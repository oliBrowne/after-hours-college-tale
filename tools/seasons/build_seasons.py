"""Season variants of the outdoor rooms: winter, fall and spring from each room's painted art.

    cd tools/seasons
    python3 build_seasons.py                 # every outdoor room, every season, battles and props
    python3 build_seasons.py N01 M07         # just these rooms
    python3 build_seasons.py N01 --only winter

The game picks a variant from state.flags.season (services/season.gd); "" keeps the painted look,
which reads as early autumn. For every room in rooms.json this writes, next to the originals:

  background-<season>.png      the room's changed pixels manifest "background_<season>" (an overlay)
  prop-N-<season>.png          trees, shrubs, benches   props.N "texture_<season>"
  <occluder>-<season>.png      skylines, walls          occluders[i] "texture_<season>"
  battle-near-<season>.png     the battle scenery       battle "near_<season>" (far keeps its sky)

How it knows what is what: trace.py re-runs the room's own builder and records, per pixel, which
painting function drew it ("lawn", "norlin_portico>roof_tiles", "atlas_tree") and in what order.
rooms.json maps those names to materials (sky, mountain, lawn, paving, roof, tree, pine, shrub,
structure, ...) with regexes, plus a few hand-placed shapes where a builder painted several things
in one call. Each season then repaints material by material in the room's own pixel style:
colour by colour (so every cluster of the painting keeps its shape), snow caps on top edges that
face open sky or something further back (the paint order says what is behind), limbs grown into
the old crowns for bare winter trees. Everything is seeded, so rebuilds are byte-identical.

Run this after tools/room_art/build_all.py rebuilt a room: build_all rewrites manifest.json, and
this adds the season keys back (it only ever adds keys)."""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np
from PIL import Image
import seasonlib as L
from seasonlib import (hexrgb, ramp, lum, hsv, hue_in, shift, dilate, erode, distance, value_noise, fbm,
                       grid_hash, hash2, shape_mask, flood, components)
import snow as S
import trees as TR
from trace import load_trace

SEASONS = ("winter", "fall", "spring")
CONF = json.load(open(os.path.join(HERE, "rooms.json")))
ROOMS = [r for r in CONF if not r.startswith("_")]
MATERIALS = ("sky", "mountain", "treeline", "distant", "tree", "pine", "shrub", "lawn", "litter", "paving", "road",
             "roof", "structure", "flowerbed", "water", "lamp", "keep", "snowfree", "other")
BACK = ("sky", "mountain", "treeline", "distant")


# ---------------------------------------------------------------------------------------------
# colour helpers
# ---------------------------------------------------------------------------------------------
def hsv2rgb(h, s, v):
    h = (h % 360) / 60.0
    i = np.floor(h).astype(int) % 6
    f = h - np.floor(h)
    p = v * (1 - s)
    q = v * (1 - s * f)
    t = v * (1 - s * (1 - f))
    r = np.choose(i, [v, q, p, p, t, v])
    g = np.choose(i, [t, v, v, q, p, p])
    b = np.choose(i, [p, p, t, v, v, q])
    return np.stack([r, g, b], -1) * 255


def per_colour(cv, mask, fn):
    """Applies fn(rgb (N, 3) float) -> rgb to each distinct colour under mask, so a cluster of the
    painting stays one cluster (and the palette stays small)."""
    if not mask.any():
        return
    px = cv[mask, :3]
    cols, inv = np.unique(px.astype(np.int32), axis=0, return_inverse=True)
    new = np.clip(np.round(fn(cols.astype(np.float32))), 0, 255)
    cv[mask, :3] = new[inv.reshape(-1)]


def grade(h_to=None, h_pull=0.0, s_mul=1.0, v_mul=1.0, s_add=0.0, v_add=0.0, h_add=0.0):
    """A per-colour HSV grade: pull hue toward h_to by h_pull (0-1), scale saturation and value."""
    def fn(rgb):
        h, s, v = hsv(rgb)
        if h_to is not None:
            d = ((h_to - h + 180) % 360) - 180
            h = h + d * h_pull
        h = h + h_add
        s = np.clip(s * s_mul + s_add, 0, 1)
        v = np.clip(v * v_mul + v_add, 0, 1)
        return hsv2rgb(h, s, v)
    return fn


def rank_ramp(cv, mask, pal, lo=0.0, hi=1.0):
    """Maps each distinct colour under mask onto `pal` by its lightness rank (pixel-weighted)."""
    if not mask.any():
        return
    px = cv[mask, :3]
    cols, inv, counts = np.unique(px.astype(np.int32), axis=0, return_inverse=True, return_counts=True)
    lv = lum(cols.astype(np.float32))
    order = np.argsort(lv)
    cum = np.cumsum(counts[order]) / counts.sum()
    rank = np.empty(len(cols))
    rank[order] = cum - counts[order] / counts.sum() / 2
    rank = lo + (hi - lo) * rank
    idx = np.clip((rank * len(pal)).astype(int), 0, len(pal) - 1)
    cv[mask, :3] = pal[idx][inv.reshape(-1)]


def ishift(a, dx, dy, fill):
    out = np.full_like(a, fill)
    h, w = a.shape[:2]
    ys0, ys1 = max(0, dy), min(h, h + dy)
    xs0, xs1 = max(0, dx), min(w, w + dx)
    out[ys0:ys1, xs0:xs1] = a[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out


# ---------------------------------------------------------------------------------------------
# a traced image and its materials
# ---------------------------------------------------------------------------------------------
class Scene:
    def __init__(self, room, name, rgba, lab, order, names, conf, sprite=False, tint=None):
        self.room, self.name, self.sprite = room, name, sprite
        self.names, self.tint = names, tint
        self.src = rgba
        self.cv = rgba.astype(np.float32)
        self.lab, self.order = lab, order
        self.H, self.W = lab.shape
        self.opaque = rgba[..., 3] > 0
        depth = conf.get("group_depth", 1)
        groups = [">".join(re.split(r"[>|]", n)[:depth]) for n in names]
        gid = {g: i for i, g in enumerate(sorted(set(groups)))}
        self.group = np.array([gid[g] for g in groups] + [0], np.int32)[np.minimum(lab, len(names))]
        # materials from label regexes, first match wins
        table = np.full(len(names) + 1, MATERIALS.index("other"), np.int32)
        rules = [(m, re.compile(rx)) for m, rx in conf.get("materials", [])]
        for i, n in enumerate(names):
            for m, rx in rules:
                if rx.search(n):
                    table[i] = MATERIALS.index(m)
                    break
        self.mat = table[np.minimum(lab, len(names))]
        self.mat[~self.opaque] = MATERIALS.index("sky") if not sprite else MATERIALS.index("other")
        self.tint_lab = None
        for reg in conf.get("regions", []):
            m = shape_mask([reg], self.H, self.W) if any(k in reg for k in ("rect", "poly", "ellipse")) \
                else np.ones((self.H, self.W), bool)
            if "label" in reg:
                rx = re.compile(reg["label"])
                hit = np.array([bool(rx.search(n)) for n in names] + [False])
                m &= hit[np.minimum(lab, len(names))]
            if "from" in reg:
                m &= np.isin(self.mat, [MATERIALS.index(f) for f in reg["from"]])
            if "hue" in reg:
                h, s, v = hsv(self.src)
                m &= hue_in(h, *reg["hue"]) & (s >= reg.get("smin", 0)) & (v >= reg.get("vmin", 0))
            if "lmax" in reg:
                m &= lum(self.src) <= reg["lmax"]
            if "lmin" in reg:
                m &= lum(self.src) >= reg["lmin"]
            if "skyline" in reg:
                # columns scanned top-down: everything from the first pixel that is not sky-like
                # (darker than skyline lmax, or of a hue outside the sky's) down to the region's end
                sk = reg["skyline"]
                h, s, v = hsv(self.src)
                L_ = lum(self.src)
                skyish = (L_ > sk.get("lmax", 0.45)) | (hue_in(h, *sk["sky_hue"]) if "sky_hue" in sk else False)
                below = np.maximum.accumulate(m & ~skyish, axis=0)
                m &= ~below if reg.get("invert") else below
            self.mat[m] = MATERIALS.index(reg["mat"])
        # small unlabelled bits (leaf specks, pages scattered by array writes) take the material
        # of what they lie on
        unl = np.array([n == "" for n in names] + [False])[np.minimum(lab, len(names))] & self.opaque
        if unl.any() and not sprite:
            cl, cn = components(unl)
            sizes = np.bincount(cl.ravel(), minlength=cn + 1)
            small = unl & (sizes[cl] <= conf.get("speck_max", 14))
            mat = self.mat.copy()
            for _ in range(4):
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nb = ishift(mat, dx, dy, -1)
                    nbs = ishift(small, dx, dy, True)
                    take = small & ~nbs & (nb >= 0)
                    mat[take] = nb[take]
                    small = small & ~take
            self.mat = mat
        self.mat[~self.opaque] = MATERIALS.index("sky") if not sprite else -1
        self.snow = np.zeros((self.H, self.W), bool)

    def labelled(self, pattern, tint=False):
        rx = re.compile(pattern)
        hit = np.array([bool(rx.search(n)) for n in self.names] + [False])
        arr = self.tint if tint else self.lab
        if arr is None:
            return np.zeros((self.H, self.W), bool)
        return hit[np.minimum(arr, len(self.names))]

    def M(self, *names):
        return np.isin(self.mat, [MATERIALS.index(n) for n in names])

    def open_above(self):
        """Pixels whose upper neighbour is open: transparent, sky or far scenery, or something that
        was painted earlier by a different painter (so it lies behind)."""
        back = ~self.opaque | self.M(*BACK)
        up_back = shift(back, 0, 1, fill=self.sprite)
        up_order = ishift(self.order, 0, 1, 1 << 30)
        up_group = ishift(self.group, 0, 1, -1)
        behind = (up_order < self.order) & (up_group != self.group)
        # snow also lies on a ledge in front of plants (a planter's coping under its shrubs)
        veg = self.M("shrub", "tree", "pine", "treeline")
        up_veg = shift(veg, 0, 1) & ~veg & ~self.M("lawn")
        return up_back | behind | up_veg

    def result(self):
        out = np.clip(np.round(self.cv), 0, 255).astype(np.uint8)
        out[..., 3] = np.where(self.cv[..., 3] > 0, out[..., 3], 0)
        return out


# ---------------------------------------------------------------------------------------------
# shared repaints
# ---------------------------------------------------------------------------------------------
def fill_behind(sc, region, prefer=("sky",)):
    """Paints what lies behind `region` by carrying each row's nearest outside colour into it
    (sky first): the sky's bands are rows, so a cleared crown shows the right band behind it."""
    cv = sc.cv
    H, W = region.shape
    pref = sc.M(*prefer) & ~region & sc.opaque
    ok = ~region & sc.opaque
    for y in np.nonzero(region.any(1))[0]:
        row = region[y]
        xs = np.nonzero(row)[0]
        good_p = np.nonzero(pref[y])[0]
        good = np.nonzero(ok[y])[0]
        src = good_p if len(good_p) else good
        if len(src) == 0:
            continue
        j = np.searchsorted(src, xs)
        left = src[np.clip(j - 1, 0, len(src) - 1)]
        right = src[np.clip(j, 0, len(src) - 1)]
        pick = np.where(np.abs(xs - left) <= np.abs(right - xs), left, right)
        if len(good_p) and len(good):
            # a near non-sky neighbour beats a far sky one (walls and roofs behind a tree)
            j2 = np.searchsorted(good, xs)
            l2 = good[np.clip(j2 - 1, 0, len(good) - 1)]
            r2 = good[np.clip(j2, 0, len(good) - 1)]
            near = np.where(np.abs(xs - l2) <= np.abs(r2 - xs), l2, r2)
            far = np.abs(pick - xs) > np.abs(near - xs) + 14
            pick = np.where(far, near, pick)
        cv[y, xs, :3] = cv[y, pick, :3]
        cv[y, xs, 3] = 255
        sc.mat[y, xs] = sc.mat[y, pick]


def caps_on(sc, top, solid, depth=2, pile=True, seed=0, min_run=2):
    """Snow along `top` (top-edge pixels of `solid`): `depth` px thick into the object, a 1px
    pile rising above runs of 6+, rounded ends, a shadow line under it."""
    cv = sc.cv
    open_ = ~solid
    t = top & (S.runs_h(top, min_run) | (top & shift(top, 1, 0) & shift(top, -1, 0)))
    length, index = S.run_lengths(t)
    painted = np.full(t.shape, -1, np.int8)
    ys, xs = np.nonzero(t)
    H, W = t.shape
    for y, x in zip(ys, xs):
        n, i = length[y, x], index[y, x]
        edge = min(i, n - 1 - i)
        d = depth if edge >= 1 else max(1, depth - 1)
        if n < 4:
            d = 1
        for k in range(d):
            yy = y + k
            if yy < H and solid[yy, x]:
                painted[yy, x] = 5 if k == 0 else (4 if k == 1 else 3)
        if pile and n >= 6 and edge >= 2 and y >= 1 and open_[y - 1, x]:
            painted[y - 1, x] = 5
            painted[y, x] = 4 if painted[y, x] >= 0 else painted[y, x]
            if n >= 14 and edge >= 4 and y >= 2 and open_[y - 2, x] and hash2(x // 5, y, seed) < 0.3:
                painted[y - 2, x] = 5
                painted[y - 1, x] = 4
    m = painted >= 0
    cv[m, :3] = S.SNOW[painted[m]]
    cv[m, 3] = 255
    under = shift(m, 0, 1) & ~m & solid
    cv[under, :3] *= 0.78
    sc.snow |= m
    return m


def light_sources(sc):
    """Lit windows, lamp heads and bulbs: warm, bright, saturated."""
    h, s, v = hsv(sc.src)
    return sc.opaque & hue_in(h, 22, 60) & (s > 0.3) & (v > 0.78) & ~sc.M("lawn", "tree", "treeline", "shrub")


# ---------------------------------------------------------------------------------------------
# winter
# ---------------------------------------------------------------------------------------------
def bare_limbs(sc, crown, keep, seed, conf):
    """Grows bare limbs out of the kept painted trunk into the old crown (TR.oak_limbs) and paints
    them in the trunk's own bark colours, snow along their upper sides. Returns the new wood."""
    cv = sc.cv
    ys, xs = np.nonzero(keep)
    if len(ys) == 0:
        return np.zeros_like(crown)
    rows = np.nonzero(crown.any(1))[0]
    base_y = ys.max()
    base_x = np.median(xs[ys >= base_y - 3])
    # roots: the highest points of the kept wood, spread across its width, each aimed from
    # the foot of the trunk through that point
    # the painted trunk is kept up to where it forks; the limbs fan out from its top
    top_c, bot_c = rows[0], rows[-1]
    fork_y = int(bot_c - (bot_c - top_c) * conf.get("fork", 0.36))
    keep = keep & (np.arange(sc.H)[:, None] >= fork_y)
    from seasonlib import components as _comp
    kl, kn = _comp(keep)
    if kn > 1:
        sizes = np.bincount(kl.ravel())
        sizes[0] = 0
        keep = kl == int(np.argmax(sizes))
    ys, xs = np.nonzero(keep)
    if len(ys) == 0:
        return np.zeros_like(crown)
    trow = xs[ys <= ys.min() + 1]
    tx0, tx1 = trow.min(), trow.max()
    roots = []
    n_roots = conf.get("roots", 5)
    fan = conf.get("fan", 1.05)
    for k in range(n_roots):
        f = (k + 0.5) / n_roots * 2 - 1                      # -1 (left) .. 1 (right)
        ang = -np.pi / 2 + f * fan + (hash2(k, 5, seed) - 0.5) * 0.25
        x = tx0 + (tx1 - tx0) * (f + 1) / 2
        wthis = conf.get("limb", 4.2) * (1.0 - 0.3 * abs(f))
        roots.append((float(x), float(ys.min() + 1), ang, wthis))
    space = dilate(crown, 1)
    if conf.get("method", "oak") == "grow":
        # space colonisation from the top of the painted trunk: limbs that fill the old crown,
        # thick where many twigs feed them (pipe model), drawn in the trunk's own bark
        top_y = ys.min()
        starts = [(float(x), float(top_y + 1)) for x in np.unique(xs[ys <= top_y + 2])[::2]]
        tcol = np.unique(xs)
        for y in range(int(top_y), int(base_y - (base_y - top_y) * 0.4)):
            row = xs[ys == y]
            if len(row):
                starts.append((float(np.median(row)), float(y)))
        nodes, parent = TR.grow(space, starts, seed=seed, density=conf.get("density", 0.035),
                                radius=conf.get("radius", 18.0), up=conf.get("up", 0.3), kill=3.0)
        width = TR.thickness(parent, base=conf.get("limb", 3.6), tip=1.0, power=0.6)
        wmap, twig = TR.raster((sc.H, sc.W), nodes, parent, width, seed=seed, crown=space)
        wood_cols = sc.src[keep][:, :3].astype(np.float32)
        lv = lum(wood_cols)
        qs = np.quantile(lv, [0.05, 0.25, 0.45, 0.65, 0.82, 0.95])
        bark = np.array([wood_cols[np.argmin(np.abs(lv - q))] for q in qs], np.float32)
        wmap[keep] = 0
        twig &= ~keep
        snow = TR.paint_bare(cv, wmap, twig, bark=bark, snow=True, seed=seed, outline=False,
                             snow_twigs=conf.get("snow_twigs", 0.12))
        sc.snow |= snow
        new = (wmap > 0) | twig
        wood_now = keep | new
        tops_ = keep & ~shift(wood_now, 0, 1)
        if sc.sprite:
            clear_ = cv[..., 3] == 0
            tops_ &= shift(clear_, 0, 1, fill=True) & shift(clear_, 0, 2, fill=True)
        tops_ &= S.runs_h(tops_, 3)
        cv[tops_, :3] = S.SNOW[4]
        sc.snow |= tops_
        return new
    segs = TR.oak_limbs(space, roots, seed=seed, depth=conf.get("depth", 6), spread=conf.get("spread", 0.46),
                        fill=conf.get("fill", 0.8), shrink=conf.get("shrink", 0.72),
                        wshrink=conf.get("wshrink", 0.72), first=conf.get("first", 0.5), rise=conf.get("rise", 0.03),
                        curl=conf.get("curl", 0.14), fringe=conf.get("fringe", 2))
    wmap, amap = TR.draw_limbs((sc.H, sc.W), segs)
    # twig lace: short 1px twigs sprouting off the limbs, pointing away from the trunk, so the
    # old crown's outline still reads as a fine dark haze
    lace = conf.get("lace", 0.05)
    if lace > 0:
        ly, lx = np.nonzero(wmap > 0)
        pick = hash2(lx, ly, seed + 31) < lace
        cy = base_y - (base_y - ys.min()) * 0.5
        for k, (x0, y0) in enumerate(zip(lx[pick], ly[pick])):
            side = 1 if hash2(k, 4, seed) < 0.5 else -1
            a = amap[y0, x0] + side * (0.45 + 0.6 * hash2(k, 1, seed))
            a += ((-np.pi / 2 - a + np.pi) % (2 * np.pi) - np.pi) * 0.25
            ln = 3 + int(hash2(k, 2, seed) * 7)
            x, y = float(x0), float(y0)
            for _ in range(ln):
                x += np.cos(a); y += np.sin(a)
                xi, yi = int(round(x)), int(round(y))
                if not (0 <= yi < sc.H and 0 <= xi < sc.W and space[yi, xi]):
                    break
                if wmap[yi, xi] == 0:
                    wmap[yi, xi] = 0.65
                    amap[yi, xi] = a
                a += (hash2(xi, yi, seed + 3) - 0.5) * 0.6
    wmap[keep] = 0
    # bark colours from the painted trunk, dark to light (at most 5)
    wood_cols = sc.src[keep][:, :3].astype(np.float32)
    lv = lum(wood_cols)
    qs = np.quantile(lv, [0.08, 0.3, 0.55, 0.78, 0.95])
    pal = np.array([wood_cols[np.argmin(np.abs(lv - q))] for q in qs], np.float32)
    snow = TR.paint_limbs(cv, wmap, amap, pal, seed=seed, snow_ramp=S.SNOW, perch=conf.get("perch", 0.55))
    sc.snow |= snow
    new = wmap > 0
    # snow along the upper faces of the painted trunk and limbs
    wood_now = keep | new
    tops_ = keep & ~shift(wood_now, 0, 1)
    if sc.sprite:
        clear_ = cv[..., 3] == 0
        tops_ &= shift(clear_, 0, 1, fill=True) & shift(clear_, 0, 2, fill=True) & shift(clear_, 0, 3, fill=True)
    tops_ &= S.runs_h(tops_, 4)
    cv[tops_, :3] = S.SNOW[4]
    sc.snow |= tops_
    return new


def winter_trees_sprite(sc, crown, seed, conf):
    """A deciduous tree sprite goes bare: leaves cleared, the painted trunk and the limbs joined
    to it kept, new limbs grown from them into the old crown, snow on every limb, a drift at its
    foot where the fallen leaves were."""
    cv = sc.cv
    wood = TR.wood_mask(sc.src, crown)
    keep = TR.trunk_part(wood, crown, frac=conf.get("trunk_frac", 0.35), reach=conf.get("reach", 0.55))
    keep = erode(dilate(keep, 1), 1) & wood | (keep & ~erode(keep, 1))
    rows = np.nonzero(crown.any(1))[0]
    top, bot = rows[0], rows[-1]
    foot_row = int(bot - max(3, (bot - top) * conf.get("foot", 0.1)))
    foot = crown & ~keep & (np.arange(sc.H)[:, None] >= foot_row) & sc.opaque
    clear = crown & ~keep & ~foot
    cv[clear, 3] = 0
    cv[clear, :3] = 0
    if foot.any():
        # a soft mound: brighter on top, blue in the shade of the trunk
        fl = foot.copy()
        topd = fl & ~shift(fl, 0, 1)
        cv[fl, :3] = S.SNOW[3]
        cv[topd, :3] = S.SNOW[5]
        cv[shift(topd, 0, 1) & fl, :3] = S.SNOW[4]
        sc.snow |= fl
    bare_limbs(sc, crown & ~foot, keep, seed, conf)


def winter_tree_background(sc, crown, seed, conf):
    """A deciduous tree painted into the background: what is behind the crown shows through a
    lattice of bare limbs."""
    wood = TR.wood_mask(sc.src, crown)
    keep = TR.trunk_part(wood, crown, frac=conf.get("trunk_frac", 0.35))
    clear = crown & ~keep
    fill_behind(sc, clear, prefer=tuple(conf.get("behind", ["sky"])))
    new = bare_limbs(sc, crown, keep, seed, conf)
    sc.mat[clear] = MATERIALS.index("structure")
    sc.mat[new | keep] = MATERIALS.index("tree")


def winter_treeline(sc, mask, seed):
    """Distant deciduous woods in winter: a mauve-brown haze of bare twigs, lacy along the top,
    dusted with snow where the crowns face up; evergreens among them stay dark green."""
    if not mask.any():
        return
    cv = sc.cv
    h, s, v = hsv(sc.src)
    green = mask & hue_in(h, 95, 200) & (s > 0.15)
    decid = mask & ~green
    TWIG = ramp(["#1c1622", "#2a2030", "#3a2c3c", "#4c3a48", "#5e4a54", "#74606a"])
    rank_ramp(cv, decid, TWIG, 0.0, 0.92)
    # lacy top edge: some of the outermost twig pixels show what is behind
    edge = decid & sc.open_above()
    lace = edge & (grid_hash(sc.H, sc.W, seed) < 0.45)
    lace |= shift(lace, 0, -1) & decid & (grid_hash(sc.H, sc.W, seed + 1) < 0.3)
    fill_behind(sc, lace, prefer=("sky",))
    # snow on crown tops and a sprinkle through the woods
    tops = (decid & ~lace) & shift(~(decid & ~lace), 0, 1)
    n = grid_hash(sc.H, sc.W, seed + 2)
    dust = tops & (n < 0.55)
    inner = decid & ~lace & (n < 0.05) & (lum(cv[..., :3]) > 0.16)
    cv[dust, :3] = S.SNOW[3]
    cv[inner, :3] = S.SNOW[2]
    sc.snow |= dust | inner
    # evergreens: darker, snow on their tiers
    rank_ramp(cv, green, ramp(["#0e1a1c", "#142426", "#1c3030", "#263c38", "#32483e"]), 0, 1)
    gt = green & shift(~green, 0, 1)
    cv[gt, :3] = S.SNOW[4]
    sc.snow |= gt


def winter_pines(sc, mask, seed, heavy=0.45):
    if not mask.any():
        return
    cv = sc.cv
    h, s, v = hsv(sc.src)
    needles = mask & hue_in(h, 70, 220) & (s > 0.08)
    per_colour(cv, needles, grade(h_to=170, h_pull=0.25, s_mul=0.85, v_mul=0.9))
    open_ = sc.open_above() | ~needles
    snow = S.load_foliage(cv, needles, open_ & ~needles, seed=seed, heavy=heavy, rise=0.04)
    sc.snow |= snow


def winter_shrubs(sc, mask, seed, heavy=0.35):
    if not mask.any():
        return
    cv = sc.cv
    h, s, v = hsv(sc.src)
    leaves = mask & sc.opaque & (hue_in(h, 40, 200) | (s < 0.25))
    flowers = mask & sc.opaque & ~leaves
    # flowers and autumn colour die back to dry brown, the greens darken under the cold
    per_colour(cv, flowers, grade(h_to=20, h_pull=0.8, s_mul=0.45, v_mul=0.7))
    per_colour(cv, leaves, grade(h_to=165, h_pull=0.3, s_mul=0.75, v_mul=0.85))
    open_ = (sc.open_above() | ~mask) & ~mask
    snow = S.load_foliage(cv, mask & sc.opaque, open_, seed=seed, heavy=heavy, rise=0.05)
    sc.snow |= snow


def winter_lawn(sc, mask, seed):
    if not mask.any():
        return
    cv = sc.cv
    h, s, v = hsv(sc.src)
    grass = mask & hue_in(h, 50, 190) & (s > 0.08)
    litter = mask & ~grass
    m = S.lawn(cv, grass, litter=litter, seed=seed, keep_litter=0.06)
    sc.snow |= m


def winter_paving(sc, mask, seed, coverage, packed=False, cell=11, edge=3, joints=True, banks=None, keep=None,
                  lane=None):
    if not mask.any() or coverage <= 0:
        return
    if lane is not None and not packed:
        sc.snow |= S.shovel(sc.cv, mask, lane, seed=seed)
        return
    m = S.trample(sc.cv, mask, coverage=coverage, seed=seed, cell=cell, edge=edge, joints=joints, packed=packed,
                  banks=banks, keep=keep)
    sc.snow |= m


def winter_roofs(sc, mask, seed, eave=3):
    if not mask.any():
        return
    m = S.roof(sc.cv, mask, eave=eave, seed=seed, sky=sc.M(*BACK) | ~sc.opaque)
    sc.snow |= m


def winter_caps(sc, region, seed, depth=2, min_run=2):
    """Snow on every top edge of solid things in `region` that faces open sky or lies in front
    of whatever is above it."""
    solid = region & sc.opaque & ~sc.M(*BACK)
    top = solid & sc.open_above() & ~sc.snow
    return caps_on(sc, top, solid | sc.snow, depth=depth, seed=seed, min_run=min_run)


def winter_ledges(sc, region, seed):
    m = S.ledge_auto(sc.cv, region & ~sc.snow, min_run=5, rise=0.06, drop=0.03)
    sc.snow |= m


def winter_mountains(sc, mask, seed, conf):
    if not mask.any():
        return
    sky = sc.M("sky") | ~sc.opaque
    m = S.mountain(sc.cv, mask, sky, seed=seed, line=conf.get("line", 2), slope=conf.get("slope", 0.55),
                   rock_keep=conf.get("rock_keep", 0.75), dim=conf.get("dim", 0.0), thr=conf.get("thr", 0.62))
    sc.snow |= m


def winter_flowerbeds(sc, mask, seed):
    """Beds under a mounded blanket: brighter crowns where plants were, shadow between."""
    if not mask.any():
        return
    cv = sc.cv
    L_ = lum(sc.src)
    med = np.median(L_[mask])
    t = np.where(L_ > med + 0.08, 5, np.where(L_ > med - 0.02, 4, np.where(L_ > med - 0.12, 3, 2)))
    cv[mask, :3] = S.SNOW[t[mask]]
    sc.snow |= mask


def winter_water(sc, mask, seed):
    if not mask.any():
        return
    cv = sc.cv
    per_colour(cv, mask, grade(h_to=225, h_pull=0.4, s_mul=0.7, v_mul=0.85))
    # shelf ice along both banks
    d = distance(~mask, maxd=5)
    n = value_noise(sc.H, sc.W, (3, 9), seed)
    ice = mask & (d <= 1 + (n * 4).astype(int))
    cv[ice, :3] = S.ICE[np.clip((lum(sc.src)[ice] * 6).astype(int), 0, 2)]
    rim = ice & (d <= 1)
    cv[rim, :3] = S.SNOW[3]
    sc.snow |= rim


def warm_glow(sc, reach=4):
    """Snow near lit windows, lamp heads and light pools takes their amber; lit windows read
    a touch warmer against the cold."""
    cv = sc.cv
    lit = light_sources(sc)
    S.warm_light(cv, sc.snow, lit, reach=reach)
    pool = sc.labelled(r"light_pool|lamp_glow|glow_pool", tint=True) & sc.snow
    if pool.any():
        L_ = lum(cv[..., :3])
        t = np.clip(np.round((L_ - 0.5) * 9), 0, 4).astype(int)
        k = 0.3
        cv[pool, :3] = cv[pool, :3] * (1 - k) + S.WARM[t[pool]] * k
    per_colour(cv, lit & ~sc.snow, grade(h_to=38, h_pull=0.15, s_mul=1.05, v_mul=1.04))


def winter(sc, rc, seed):
    w = rc.get("winter", {})
    if sc.M("mountain").any():
        winter_mountains(sc, sc.M("mountain"), seed + 1, w.get("mountain", {}))
    winter_treeline(sc, sc.M("treeline"), seed + 2)
    trees(sc, rc, seed + 3, "winter")
    winter_pines(sc, sc.M("pine"), seed + 4, w.get("pine_heavy", 0.45))
    winter_shrubs(sc, sc.M("shrub"), seed + 5, w.get("shrub_heavy", 0.35))
    winter_roofs(sc, sc.M("roof"), seed + 6, w.get("eave", 3))
    winter_lawn(sc, sc.M("lawn", "litter"), seed + 7)
    keep = shape_mask(w.get("trodden", []), sc.H, sc.W) if w.get("trodden") else None
    banks = shape_mask(w.get("banks", []), sc.H, sc.W) if w.get("banks") else None
    lane = shape_mask(w.get("lanes", []), sc.H, sc.W) if w.get("lanes") else None
    if w.get("lane_label"):
        ll = sc.labelled(w["lane_label"])
        lane = ll if lane is None else lane | ll
    winter_paving(sc, sc.M("paving"), seed + 8, w.get("paving", 0.45), keep=keep, banks=banks,
                  cell=w.get("cell", 11), edge=w.get("edge", 3), lane=lane)
    road = sc.M("road")
    if road.any() and w.get("plowed", True):
        # a plowed road: wet asphalt between banks of snow along the kerbs, a few packed tracks
        area = road | sc.M("keep", "water")
        sc.snow |= S.shovel(sc.cv, road, erode(area, w.get("bank", 5)) & road, seed=seed + 9, joints=0,
                            holes=sc.M("keep", "water") & erode(area, w.get("bank", 5)),
                            packed_patches=w.get("road_packed", 0.08))
    else:
        winter_paving(sc, road, seed + 9, w.get("road", 0.25), packed=True, cell=w.get("cell", 11), edge=4,
                      joints=False, keep=keep, banks=banks)
    winter_flowerbeds(sc, sc.M("flowerbed"), seed + 10)
    winter_water(sc, sc.M("water"), seed + 11)
    struct = sc.M("structure", "lamp", "other", "distant")
    winter_caps(sc, struct | sc.M("distant"), seed + 12, depth=w.get("cap_depth", 2))
    if w.get("ledges", not sc.sprite):
        winter_ledges(sc, sc.M("structure") & ~light_sources(sc), seed + 13)
    for ln in w.get("ledge_lines", []):
        sc.snow |= S.ledge_lines(sc.cv, [ln], seed + 14)
    warm_glow(sc, w.get("glow", 4))


# ---------------------------------------------------------------------------------------------
# fall and spring
# ---------------------------------------------------------------------------------------------
FALL_RAMPS = [TR.FALL["orange"], TR.FALL["red"], TR.FALL["gold"], TR.FALL["crimson"]]
LITTER = ramp(["#5a1e18", "#8e2c1e", "#b8501c", "#d07a24", "#e0a83a", "#a83a2a"])
PETALS = ramp(["#f6bcd4", "#fde6f0", "#ffffff", "#e892b6"])
SPRING_FLOWERS = [ramp(["#d8324a", "#f05a6a"]), ramp(["#f2c22e", "#fbe26a"]), ramp(["#f07ab0", "#fbb4d4"]),
                  ramp(["#f4f0f8", "#ffffff"]), ramp(["#9a6ad8", "#c49af0"])]


def fall_foliage(sc, mask, seed, mix_cell=7):
    """Deep fall: each tree in two of the fall ramps, mixed in leaf-cluster-sized blobs."""
    if not mask.any():
        return
    cv = sc.cv
    leaf = TR.foliage_classes(sc.src, mask)
    lab_, n = components(dilate(leaf, 2) & mask) if leaf.sum() < 60000 else (leaf.astype(np.int32), 1)
    blob = value_noise(sc.H, sc.W, mix_cell, seed)
    for i in range(1, n + 1):
        part = leaf & (lab_ == i)
        if part.sum() < 4:
            continue
        a = FALL_RAMPS[int(hash2(i, 1, seed) * 4)]
        b = FALL_RAMPS[int(hash2(i, 2, seed) * 4)]
        pa = part & (blob < 0.62)
        rank_ramp(cv, pa, a, 0.0, 1.0)
        rank_ramp(cv, part & ~pa, b, 0.0, 1.0)


def spring_foliage(sc, mask, seed, blossom=None):
    if not mask.any():
        return
    cv = sc.cv
    leaf = TR.foliage_classes(sc.src, mask)
    lab_, n = components(dilate(leaf, 2) & mask) if leaf.sum() < 60000 else (leaf.astype(np.int32), 1)
    for i in range(1, n + 1):
        part = leaf & (lab_ == i)
        if part.sum() < 4:
            continue
        kind = blossom if blossom else None
        if kind is None:
            r = hash2(i, 3, seed)
            kind = "pink" if r < 0.3 else "white" if r < 0.45 else "green" if r < 0.8 else "lime"
        if kind in ("pink", "white"):
            TR.blossom(cv, part, TR.SPRING[kind], seed=seed + i, amount=0.5)
        else:
            rank_ramp(cv, part, TR.SPRING[kind], 0.0, 1.0)


def trees(sc, rc, seed, season):
    """Deciduous trees painted into the image (material 'tree')."""
    mask = sc.M("tree")
    if not mask.any():
        return
    tc = rc.get("trees", {})
    if season == "winter":
        lab_, n = components(mask)
        for i in range(1, n + 1):
            part = lab_ == i
            if part.sum() < 30:
                continue
            if sc.sprite:
                winter_trees_sprite(sc, part, seed + i, tc)
            else:
                winter_tree_background(sc, part, seed + i, tc)
    elif season == "fall":
        fall_foliage(sc, mask, seed)
    else:
        spring_foliage(sc, mask, seed, tc.get("blossom"))


def scatter(sc, mask, density, pal, seed, size2=0.4):
    """Little 1-2px things scattered over mask (leaves, petals, flowers)."""
    cv = sc.cv
    n = grid_hash(sc.H, sc.W, seed)
    pts = mask & (n < density)
    pts &= ~shift(pts, 1, 0) & ~shift(pts, 0, 1)
    idx = (grid_hash(sc.H, sc.W, seed + 1) * len(pal)).astype(int) % len(pal)
    cv[pts, :3] = pal[idx[pts]]
    two = shift(pts & (grid_hash(sc.H, sc.W, seed + 2) < size2), 1, 0) & mask
    idx2 = shift(idx, 1, 0)
    cv[two, :3] = pal[idx2[two]]
    return pts | two


def near_trees(sc, rc, reach=40):
    """0..1 closeness to tree trunks (for leaf litter): from the room's tree spots."""
    spots = rc.get("tree_spots", [])
    if not spots:
        return np.zeros((sc.H, sc.W), np.float32)
    ys, xs = np.mgrid[0:sc.H, 0:sc.W]
    best = np.zeros((sc.H, sc.W), np.float32)
    for (x, y, r) in spots:
        d = np.hypot((xs - x) / r, (ys - y) / (r * 0.45))
        best = np.maximum(best, np.clip(1 - d, 0, 1))
    return best


def fall(sc, rc, seed):
    f = rc.get("fall", {})
    cv = sc.cv
    trees(sc, rc, seed + 3, "fall")
    fall_foliage(sc, sc.M("treeline"), seed + 2, mix_cell=5)
    h, s, v = hsv(sc.src)
    # shrubs: a burning red or gold here and there
    sh = sc.M("shrub") & sc.opaque
    if sh.any():
        green = sh & hue_in(h, 40, 200)
        blob = value_noise(sc.H, sc.W, 9, seed + 5)
        per_colour(cv, green & (blob >= 0.62), grade(h_to=95, h_pull=0.35, s_mul=0.9, v_mul=0.95))
        hot = green & (blob < f.get("shrub_red", 0.3))
        rank_ramp(cv, hot, TR.FALL["crimson"], 0.15, 0.95)
        warm = green & (blob >= f.get("shrub_red", 0.3)) & (blob < 0.62)
        rank_ramp(cv, warm, TR.FALL["gold"], 0.05, 0.85)
        flowers = sh & ~green
        per_colour(cv, flowers, grade(h_to=30, h_pull=0.6, s_mul=1.0))
    # lawn: the green goes olive-gold
    lawn = sc.M("lawn", "litter")
    grass = lawn & hue_in(h, 50, 190)
    per_colour(cv, grass, grade(h_to=68, h_pull=0.42, s_mul=0.88, v_mul=0.98))
    near = near_trees(sc, rc)
    n = fbm(sc.H, sc.W, 14, seed + 6, octaves=2)
    dens = f.get("litter", 0.05) * (0.35 + 1.3 * n) + near * f.get("litter_near", 0.35)
    piles = np.zeros((sc.H, sc.W), bool)
    hit = grid_hash(sc.H, sc.W, seed + 7) < dens
    piles = lawn & hit
    scatter(sc, piles, 1.0, LITTER, seed + 8)
    # paving: leaves blown into the edges and joints
    pave = sc.M("paving", "road")
    if pave.any():
        d = distance(~pave, maxd=6)
        pd = f.get("pave_litter", 0.03) * (0.4 + n) + np.where(d <= 2, f.get("pave_edge", 0.10), 0) + near * 0.25
        hit = pave & (grid_hash(sc.H, sc.W, seed + 9) < pd)
        scatter(sc, hit, 1.0, LITTER, seed + 10)
    # flower beds: mums
    beds = sc.M("flowerbed")
    if beds.any():
        bh = beds & ~hue_in(h, 60, 190)
        rank_ramp(cv, bh, ramp(["#4a1a14", "#8a2a1a", "#c4501c", "#e08a2a", "#f2c04a"]), 0.1, 1.0)
    # pines a shade warmer; mountains keep their look


def spring(sc, rc, seed):
    p = rc.get("spring", {})
    cv = sc.cv
    trees(sc, rc, seed + 3, "spring")
    h, s, v = hsv(sc.src)
    tl = sc.M("treeline")
    if tl.any():
        tleaf = TR.foliage_classes(sc.src, tl)
        blob = value_noise(sc.H, sc.W, 6, seed + 2)
        rank_ramp(cv, tleaf & (blob >= 0.25), TR.SPRING["green"], 0.0, 0.95)
        rank_ramp(cv, tleaf & (blob < 0.25) & (blob >= 0.12), TR.SPRING["lime"], 0.0, 0.95)
        bl = tleaf & (blob < 0.12)
        TR.blossom(cv, bl, TR.SPRING["pink"], seed=seed, amount=0.55)
    sh = sc.M("shrub") & sc.opaque
    if sh.any():
        green = sh & (hue_in(h, 40, 200) | (s < 0.2))
        per_colour(cv, green, grade(h_to=105, h_pull=0.3, s_mul=1.25, v_mul=1.06))
        flow = sh & ~green
        per_colour(cv, flow, grade(h_to=320, h_pull=0.5, s_mul=1.1, v_mul=1.05))
        # some bushes in flower
        blob = value_noise(sc.H, sc.W, 8, seed + 4)
        top = green & shift(~green, 0, 1)
        for k, pal in enumerate(SPRING_FLOWERS[2:]):
            zone = green & (blob > 0.55 + 0.1 * k) & (blob < 0.65 + 0.1 * k)
            scatter(sc, zone, p.get("shrub_flowers", 0.18), pal, seed + 20 + k, size2=0.2)
    pines = sc.M("pine")
    if pines.any():
        L0 = lum(sc.src)
        tips = pines & (L0 - shift(L0, 0, 1) > 0.05) & hue_in(h, 70, 200)
        tips &= grid_hash(sc.H, sc.W, seed + 5) < 0.35
        cv[tips, :3] = TR.PINE_TIPS
    lawn = sc.M("lawn", "litter")
    grass = lawn & hue_in(h, 50, 190)
    per_colour(cv, grass, grade(h_to=104, h_pull=0.4, s_mul=1.35, v_mul=1.08))
    # old leaves raked away: litter on the lawn becomes grass
    lit = lawn & ~grass
    if lit.any():
        g = dilate(grass, 1)
        cv[lit, :3] = S.SNOW[0] * 0 + np.median(cv[grass, :3], axis=0)
    dens = p.get("lawn_flowers", 0.006)
    scatter(sc, grass, dens, ramp(["#f4e04a", "#ffffff", "#f8f4e8"]), seed + 6, size2=0.0)
    for bed in p.get("beds", []):
        tulip_bed(sc, bed, seed + 7)
    beds = sc.M("flowerbed")
    if beds.any():
        bh = beds & ~hue_in(h, 60, 190)
        n = (grid_hash(sc.H, sc.W, seed + 8) * 4).astype(int)
        for k, pal in enumerate(SPRING_FLOWERS[:4]):
            rank_ramp(cv, bh & (n == k), pal, 0, 1)
    pave = sc.M("paving")
    if pave.any() and p.get("petals_near_trees"):
        near = near_trees(sc, rc)
        hit = pave & (grid_hash(sc.H, sc.W, seed + 9) < near * 0.12)
        scatter(sc, hit, 1.0, PETALS, seed + 10, size2=0.0)


def tulip_bed(sc, bed, seed):
    """A small bed of tulips on a lawn: dark soil oval, rows of 2px blooms on stems."""
    cx, cy, rx, ry = bed[:4]
    pal = SPRING_FLOWERS[int(bed[4]) % len(SPRING_FLOWERS)] if len(bed) > 4 else SPRING_FLOWERS[0]
    cv = sc.cv
    ys, xs = np.mgrid[0:sc.H, 0:sc.W]
    e = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2
    soil = e <= 1
    rim = soil & (e > 0.72)
    cv[soil, :3] = hexrgb("#3a2826")
    cv[rim, :3] = hexrgb("#5a4a3c")
    lit = soil & (ys < cy - ry * 0.3) & ~rim
    cv[lit, :3] = hexrgb("#4a3430")
    for y in range(cy - ry + 2, cy + ry - 1, 3):
        for x in range(cx - rx + 3, cx + rx - 2, 3):
            xx = x + (1 if (y // 3) % 2 else 0)
            if ((xx - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 > 0.62:
                continue
            k = int(hash2(xx, y, seed) * 2)
            if 0 <= y - 2 < sc.H:
                cv[y, xx, :3] = hexrgb("#3e7a34")
                cv[y - 1, xx, :3] = pal[k]
                cv[y - 2, xx, :3] = pal[1]
                if xx + 1 < sc.W:
                    cv[y - 1, xx + 1, :3] = pal[0]


SEASON_FN = {"winter": winter, "fall": fall, "spring": spring}


# ---------------------------------------------------------------------------------------------
# rooms
# ---------------------------------------------------------------------------------------------
def res(room, name):
    return f"res://assets/art/rooms/{room}/{name}"


def variant_name(name, season):
    base, ext = os.path.splitext(name)
    return f"{base}-{season}{ext}"


def seed_of(room, name):
    return int(sum(ord(c) * (i + 1) for i, c in enumerate(room + name))) % 9973


def process(room, name, caps, names, conf, season, sprite=False):
    rgba, lab, tint, order = caps[name]
    sc = Scene(room, name, rgba, lab, order, names, conf, sprite=sprite, tint=tint)
    SEASON_FN[season](sc, conf, seed_of(room, name))
    hook = conf.get("hook")
    if hook:
        import room_hooks
        fn = getattr(room_hooks, f"{hook}_{season}", None)
        if fn:
            fn(sc)
    return sc.result()


def merged(conf, key):
    """A sub-config (props, battle) inherits the room's season settings unless it sets its own."""
    sub = dict(conf)
    sub.update(conf.get(key, {}))
    return sub


def _strip_keys(d, season):
    """Removes every "<key>_<season>" entry (and dawn ones) from a manifest, recursively."""
    if isinstance(d, dict):
        for k in [k for k in d if isinstance(k, str) and k.endswith("_" + season)]:
            del d[k]
        for v in d.values():
            _strip_keys(v, season)
    elif isinstance(d, list):
        for v in d:
            _strip_keys(v, season)


def build_room(room, seasons=SEASONS, verbose=True):
    rc = CONF[room]
    caps, names = load_trace(room)
    folder = os.path.join(L.ROOMS_DIR, room)
    mpath = os.path.join(folder, "manifest.json")
    manifest = json.load(open(mpath))
    written = []
    for season in seasons:
        # start clean: this season's files and keys are rewritten below
        for f in os.listdir(folder):
            if f.endswith(f"-{season}.png"):
                os.remove(os.path.join(folder, f))
        _strip_keys(manifest, season)
        if season in rc.get("skip", []):
            continue
        bg_out = None
        # the room itself (and its dawn look when it has one)
        for bg_key, file in (("background", "background.png"), ("background_dawn", "background-dawn.png")):
            if bg_key not in manifest or file not in caps:
                continue
            if bg_key == "background_dawn" and season not in rc.get("dawn_seasons", []):
                continue
            out = process(room, file, caps, names, rc, season)
            if bg_key == "background":
                bg_out = out
            vn = variant_name(file, season)
            # stored as an overlay: only the pixels the season changed (NativeSeason.overlay)
            base = caps[file][0]
            layer = out.copy()
            layer[np.all(out == base, axis=-1)] = 0
            L.save(layer, res(room, vn))
            manifest[f"{bg_key}_{season}" if bg_key == "background" else f"background_dawn_{season}"] = res(room, vn)
            written.append(vn)
        # props
        for key, spec in manifest.get("props", {}).items():
            pc = rc.get("props", {}).get(key)
            if pc is None or not isinstance(pc, dict) or season in pc.get("skip", []):
                continue
            for tkey in ("texture", "flag_texture"):
                if tkey not in spec:
                    continue
                file = os.path.basename(spec[tkey])
                if file not in caps:
                    continue
                conf = merged(rc, "props")
                conf.update(pc)
                out = process(room, file, caps, names, conf, season, sprite=True)
                if np.array_equal(out, caps[file][0]):
                    continue            # nothing seasonal about it
                vn = variant_name(file, season)
                L.save(out, res(room, vn))
                spec[f"{tkey}_{season}"] = res(room, vn)
                written.append(vn)
        # occluders
        for i, occ in enumerate(manifest.get("occluders", [])):
            file = os.path.basename(occ["texture"])
            oc = rc.get("occluders", {}).get(file)
            if oc is None or season in oc.get("skip", []):
                continue
            if oc.get("crop"):
                # a piece cut from the background: cut it from the season's background instead
                src = np.array(Image.open(L.res_path(occ["texture"])).convert("RGBA"))
                h_, w_ = src.shape[:2]
                x_, y_ = int(occ["x"]), int(occ["y"])
                out = bg_out[y_:y_ + h_, x_:x_ + w_].copy()
                out[..., 3] = src[..., 3]
                out[src[..., 3] == 0] = 0
                if np.array_equal(out, src):
                    continue
                vn = variant_name(file, season)
                L.save(out, res(room, vn))
                occ[f"texture_{season}"] = res(room, vn)
                written.append(vn)
                continue
            if file not in caps:
                continue
            conf = merged(rc, "props")
            conf.update(oc)
            out = process(room, file, caps, names, conf, season, sprite=True)
            if np.array_equal(out, caps[file][0]):
                continue
            vn = variant_name(file, season)
            L.save(out, res(room, vn))
            occ[f"texture_{season}"] = res(room, vn)
            written.append(vn)
        # battle: an overlay over the near layer (or the far image when there is none), made from
        # colour and geometry (battles.py); dawn battles keep their plain dawn look
        bc = rc.get("battle")
        battle = manifest.get("battle", {})
        if bc is not None and battle and season not in bc.get("skip", []):
            import battles
            key = "near" if "near" in battle else "far"
            base = np.array(Image.open(L.res_path(battle[key])).convert("RGBA"))
            sky = base[..., 3] == 0 if key == "near" else np.zeros(base.shape[:2], bool)
            kw = {}
            if season == "winter":
                kw = {k: bc[k] for k in ("lane", "dim") if k in bc}
            lay = battles.layer(base, season, bc.get("horizon", 98), seed=seed_of(room, "battle"), sky=sky, **kw)
            if season == "winter" and key == "near" and bc.get("mountains"):
                y0, y1, lmax = bc["mountains"]
                far = np.array(Image.open(L.res_path(battle["far"])).convert("RGBA"))
                cvf = battles.far_mountains(far, sky, (y0, y1), seed=seed_of(room, "far"), lmax=lmax,
                                            dim=bc.get("mountain_dim", 0.3))
                outf = np.clip(np.round(cvf), 0, 255).astype(np.uint8)
                outf[..., 3] = far[..., 3]
                outf[np.all(outf == far, axis=-1)] = 0
                vf = variant_name("battle-far.png", season)
                L.save(outf, res(room, vf))
                battle[f"far_{season}"] = res(room, vf)
                written.append(vf)
            vn = variant_name(f"battle-{key}.png", season)
            L.save(lay, res(room, vn))
            battle[f"{key}_{season}"] = res(room, vn)
            if key == "far" or not (season == "winter" and bc.get("mountains")):
                for stale in ("near", "far"):
                    if stale != key:
                        battle.pop(f"{stale}_{season}", None)
            written.append(vn)
    with open(mpath, "w") as f:
        json.dump(manifest, f, indent=1)
    if verbose:
        size = sum(os.path.getsize(os.path.join(folder, w)) for w in set(written))
        print(f"{room}: {len(set(written))} images, {size / 1024:.0f} KB", flush=True)
    return written


def main(args):
    only = None
    if "--only" in args:
        i = args.index("--only")
        only = args[i + 1].split(",")
        args = args[:i] + args[i + 2:]
    rooms = [a.upper() for a in args] or ROOMS
    for room in rooms:
        build_room(room, seasons=only or SEASONS)


if __name__ == "__main__":
    main(sys.argv[1:])
