"""Trees through the year: bare winter oaks grown by space colonisation inside the old crown,
snow on their limbs; foliage recoloured for deep fall or fresh spring and blossom."""
import numpy as np
from seasonlib import ramp, hexrgb, lum, hsv, hue_in, hash2, grid_hash, shift, dilate, erode, value_noise
from snow import SNOW

BARK = ramp(["#1e1620", "#2e2228", "#45343a", "#5e4a4c", "#7a6662", "#98847a"])
INK = hexrgb("#1a1524")

FALL = {
    "red": ramp(["#240c14", "#44121e", "#6e1a24", "#9c2626", "#c43c2c", "#e2683a", "#f29a52"]),
    "gold": ramp(["#30220e", "#563c16", "#866018", "#b88a1c", "#e0b430", "#f2d45a", "#fcec98"]),
    "orange": ramp(["#2e1210", "#542216", "#863414", "#b84e12", "#e0701a", "#f49a30", "#fcc464"]),
    "crimson": ramp(["#200a16", "#3e1020", "#66142c", "#921e30", "#bc3036", "#dc5a40", "#f08a5a"]),
}
SPRING = {
    "green": ramp(["#16241a", "#203a22", "#2e5428", "#44762e", "#62983a", "#86b84a", "#b2d86a"]),
    "pink": ramp(["#1c2a1e", "#2e4a2a", "#4a6a34", "#c86c94", "#e892b6", "#f6bcd4", "#fde6f0"]),
    "white": ramp(["#1c2a1e", "#2e4a2a", "#4a6a34", "#a8a6c8", "#d6d4ea", "#f0eef8", "#ffffff"]),
    "lime": ramp(["#18281a", "#26421f", "#3a6226", "#58862c", "#7cac36", "#a2cc48", "#cce878"]),
}
PINE_TIPS = hexrgb("#8ab65a")


def foliage_classes(cv, region=None):
    """Splits a tree's pixels into foliage and wood by colour: leaves are olive, gold, orange or
    green; the trunk and limbs are maroon and red-brown."""
    h, s, v = hsv(cv[..., :3])
    opaque = cv[..., 3] > 0
    leaf = opaque & ((hue_in(h, 26, 185) & (s > 0.22) & (v > 0.12)) |
                     (hue_in(h, 14, 26) & (s > 0.74) & (v > 0.44)) |
                     (hue_in(h, 26, 70) & (v > 0.5)))
    if region is not None:
        leaf &= region
    return leaf


def recolour(cv, mask, pal, quant=None, lift=0.0):
    """Maps the pixels of `mask` onto the ramp `pal` by their lightness rank, so the clusters of
    the painting survive and only the colours change."""
    if not mask.any():
        return
    L = lum(cv[..., :3])
    vals = L[mask]
    n = len(pal)
    qs = quant if quant is not None else np.linspace(0, 1, n + 1)[1:-1]
    edges = np.quantile(vals, qs)
    idx = np.searchsorted(edges, vals, side="right")
    idx = np.clip(idx + (1 if lift > 0 else 0) * (vals > np.quantile(vals, 1 - lift)), 0, n - 1)
    cv[mask, :3] = pal[idx]


def blossom(cv, mask, pal, seed=0, amount=0.5):
    """Spring blossom: the leaf clusters' lit upper halves flower (pink or white), the shaded
    parts are young leaves."""
    if not mask.any():
        return
    L = lum(cv[..., :3])
    vals = L[mask]
    q = np.quantile(vals, [0.18, 0.36, 1 - amount * 0.9, 1 - amount * 0.55, 1 - amount * 0.25, 0.97])
    idx = np.searchsorted(q, vals, side="right")
    cv[mask, :3] = pal[np.clip(idx, 0, len(pal) - 1)]


# ---------------------------------------------------------------------------------------------
# bare trees
# ---------------------------------------------------------------------------------------------
def grow(crown, starts, seed=0, density=0.05, radius=17.0, kill=3.5, step=2.0, up=0.25, iters=260):
    """Space colonisation: limbs grow from `starts` toward attraction points scattered in the
    crown until the crown is filled. Returns nodes (N, 2) as (x, y) and parent indices."""
    H, W = crown.shape
    ys, xs = np.nonzero(crown)
    keep = hash2(xs, ys, seed) < density
    attr = np.stack([xs[keep], ys[keep]], 1).astype(np.float32)
    nodes = [np.array(p, np.float32) for p in starts]
    parent = [-1] + list(range(len(starts) - 1))
    if len(attr) == 0:
        return np.array(nodes), np.array(parent)
    for it in range(iters):
        N = np.array(nodes)
        d = np.linalg.norm(attr[:, None, :] - N[None, :, :], axis=2)
        near = d.argmin(1)
        nd = d[np.arange(len(attr)), near]
        live = nd < radius
        if not live.any():
            break
        grew = False
        for ni in np.unique(near[live]):
            pts = attr[live & (near == ni)]
            v = pts - N[ni]
            v = v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-3)
            dvec = v.sum(0)
            dvec = dvec / max(np.linalg.norm(dvec), 1e-3) + np.array([0, -up], np.float32)
            dvec = dvec / max(np.linalg.norm(dvec), 1e-3)
            new = N[ni] + dvec * step
            if np.min(np.linalg.norm(N - new, axis=1)) < step * 0.5:
                continue
            nodes.append(new)
            parent.append(ni)
            grew = True
        N = np.array(nodes)
        d = np.linalg.norm(attr[:, None, :] - N[None, :, :], axis=2)
        attr = attr[d.min(1) > kill]
        if not grew or len(attr) == 0:
            break
    return np.array(nodes), np.array(parent)


def thickness(parent, base=4.0, tip=1.0, power=0.5):
    n = len(parent)
    tips = np.ones(n)
    child_count = np.zeros(n, int)
    for i in range(n):
        if parent[i] >= 0:
            child_count[parent[i]] += 1
    for i in range(n - 1, -1, -1):
        if parent[i] >= 0:
            tips[parent[i]] += tips[i] if child_count[i] else 1
    t = tips / tips.max()
    return tip + (base - tip) * t ** power


def line_pts(x0, y0, x1, y1):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    xs = np.round(np.linspace(x0, x1, n)).astype(int)
    ys = np.round(np.linspace(y0, y1, n)).astype(int)
    return xs, ys


def raster(shape, nodes, parent, width, seed=0, twigs=True, crown=None):
    """Width map of the limbs (0 = none) plus a twig mask for the fine outer growth."""
    H, W = shape
    wmap = np.zeros((H, W), np.float32)
    for i in range(len(nodes)):
        p = parent[i]
        if p < 0:
            continue
        w = width[i]
        xs, ys = line_pts(nodes[p][0], nodes[p][1], nodes[i][0], nodes[i][1])
        r = int(np.floor((w - 1) / 2 + 0.25))
        for x, y in zip(xs, ys):
            for dy in range(-r, r + 1):
                for dx in range(-r, r + 1 + (1 if w - 1 - 2 * r >= 0.75 else 0)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < H and 0 <= xx < W:
                        wmap[yy, xx] = max(wmap[yy, xx], w)
    twig = np.zeros((H, W), bool)
    if twigs:
        child = np.zeros(len(nodes), int)
        for i in range(len(nodes)):
            if parent[i] >= 0:
                child[parent[i]] += 1
        for i in np.nonzero(child == 0)[0]:
            x, y = nodes[i]
            p = parent[i]
            base_ang = np.arctan2(y - nodes[p][1], x - nodes[p][0]) if p >= 0 else -np.pi / 2
            for k in range(2):
                a = base_ang + (hash2(i, k, seed) - 0.5) * 1.9
                ln = 2 + int(hash2(i, k + 7, seed) * 3)
                xs, ys = line_pts(x, y, x + np.cos(a) * ln, y + np.sin(a) * ln)
                for xx, yy in zip(xs, ys):
                    if 0 <= yy < H and 0 <= xx < W and (crown is None or crown[yy, xx]):
                        twig[yy, xx] = True
        twig &= wmap == 0
    return wmap, twig


def paint_bare(cv, wmap, twig, bark=BARK, snow=True, seed=0, outline=True, snow_twigs=0.25, dim=0.0):
    """Shades the limbs (light from the upper left), outlines the big ones in ink and lays snow
    along the tops of every limb that is not too steep."""
    wood = wmap > 0
    W_ = wmap
    left_open = ~shift(wood, 1, 0)
    right_open = ~shift(wood, -1, 0)
    top_open = ~shift(wood, 0, 1)
    col = np.zeros(wood.shape + (3,), np.float32)
    t = np.full(wood.shape, 2, int)
    t[W_ >= 3] = 3
    t[(W_ >= 2) & left_open] = 4
    t[(W_ >= 4) & left_open] = 5
    t[(W_ >= 2) & right_open] = 1
    t[(W_ < 2)] = 1
    t[(W_ < 1.5)] = 1
    col = bark[t]
    cv[wood, :3] = col[wood]
    cv[wood, 3] = 255
    cv[twig, :3] = bark[0] if dim == 0 else bark[0] * (1 - dim) + cv[twig, :3] * dim
    cv[twig, 3] = 255
    if outline:
        big = W_ >= 3
        ring = dilate(big, 1) & ~wood & ~twig
        cv[ring, :3] = INK
        cv[ring, 3] = 255
    snowm = np.zeros(wood.shape, bool)
    if snow:
        # limbs: the top pixel of each limb that has room above it
        flatish = wood & top_open & (W_ >= 1.5)
        # a steep limb has wood right below-left or below-right only: keep flat runs
        run = flatish & (shift(flatish, 1, 0) | shift(flatish, -1, 0))
        snowm = run
        cv[snowm, :3] = SNOW[4]
        # a line of snow perched on the finer branches too (one pixel above them)
        fine = (wood & (W_ < 1.5)) | twig
        perch = shift(fine & shift(fine, 1, 0), 0, -1) & ~wood & ~twig
        pick = grid_hash(*wood.shape, seed=seed + 3) < snow_twigs
        perch &= pick | shift(pick, 1, 0)
        cv[perch, :3] = SNOW[3]
        cv[perch, 3] = 255
        snowm |= perch
        # the forks hold more
        fork = wood & top_open & (W_ >= 3) & ~shift(wood, 0, 2)
        up = shift(fork, 0, -1) & ~wood
        cv[up, :3] = SNOW[5]
        cv[up, 3] = 255
        snowm |= up
    return snowm


def bare_tree(cv, crown, trunk_top, trunk_width, seed=0, bark=BARK, snow=True, trunk_len=None, density=0.05,
              radius=17.0, outline=True, dim=0.0, starts=None, snow_twigs=0.25, up=0.25):
    """Grows and paints a bare tree into `cv` (crown pixels must already be cleared)."""
    H, W = crown.shape
    tx, ty = trunk_top
    if starts is None:
        rows = np.nonzero(crown.any(1))[0]
        if len(rows) == 0:
            return np.zeros_like(crown)
        top, bot = rows[0], rows[-1]
        rise = trunk_len if trunk_len is not None else max(6, int((ty - top) * 0.35))
        starts = [(tx, ty - k) for k in range(0, rise, 2)]
    nodes, parent = grow(crown, starts, seed=seed, density=density, radius=radius, up=up)
    width = thickness(parent, base=trunk_width, tip=1.0, power=0.55)
    wmap, twig = raster((H, W), nodes, parent, width, seed=seed, crown=dilate(crown, 2))
    return paint_bare(cv, wmap, twig, bark=bark, snow=snow, seed=seed, outline=outline, dim=dim, snow_twigs=snow_twigs)


# ---------------------------------------------------------------------------------------------
# bare trees grown out of the painted trunk and limbs
# ---------------------------------------------------------------------------------------------
def wood_mask(cv, crown):
    """Bark: maroon / red-brown / dark violet pixels (leaves are olive, gold, green)."""
    h, s, v = hsv(cv[..., :3])
    return crown & (cv[..., 3] > 0) & ((hue_in(h, 285, 16) & (v <= 0.42)) | (hue_in(h, 16, 22) & (v <= 0.33)) | (v < 0.11))


def trunk_part(wood, crown, frac=0.3, min_size=12, reach=0.55):
    """The wood connected to the trunk: components touching the bottom `frac` of the crown,
    taken no higher than `reach` of the crown's height (above that, leaf shadow and limb mix)."""
    from seasonlib import components
    rows = np.nonzero(crown.any(1))[0]
    if len(rows) == 0:
        return wood & False
    cut = rows[-1] - int((rows[-1] - rows[0]) * frac)
    ceiling = rows[-1] - int((rows[-1] - rows[0]) * reach)
    wood = wood.copy()
    wood[:ceiling] = False
    lab, n = components(wood)
    keep = np.zeros_like(wood)
    for i in range(1, n + 1):
        part = lab == i
        if part[cut:].any() and part.sum() >= min_size:
            keep |= part
    return keep


def colonise(crown, roots, seed=0, density=0.012, radius=20.0, kill=4.0, step=2.0, up=0.3, iters=200):
    """Space colonisation from many roots (each its own node, no parent): limbs grow from the
    nearest painted wood toward attraction points scattered through the old crown."""
    ys, xs = np.nonzero(crown)
    pick = hash2(xs, ys, seed) < density
    attr = np.stack([xs[pick], ys[pick]], 1).astype(np.float32)
    nodes = [np.array(p, np.float32) for p in roots]
    parent = [-1] * len(nodes)
    is_root = [True] * len(nodes)
    for _ in range(iters):
        if len(attr) == 0:
            break
        N = np.array(nodes)
        d = np.linalg.norm(attr[:, None, :] - N[None, :, :], axis=2)
        near = d.argmin(1)
        nd = d[np.arange(len(attr)), near]
        live = nd < radius
        if not live.any():
            break
        grew = False
        for ni in np.unique(near[live]):
            pts = attr[live & (near == ni)]
            v = pts - N[ni]
            v = v / np.maximum(np.linalg.norm(v, axis=1, keepdims=True), 1e-3)
            dvec = v.sum(0)
            dvec = dvec / max(np.linalg.norm(dvec), 1e-3) + np.array([0, -up], np.float32)
            dvec = dvec / max(np.linalg.norm(dvec), 1e-3)
            new = N[ni] + dvec * step
            if np.min(np.linalg.norm(N - new, axis=1)) < step * 0.6:
                continue
            nodes.append(new)
            parent.append(int(ni))
            is_root.append(False)
            grew = True
        N = np.array(nodes)
        d = np.linalg.norm(attr[:, None, :] - N[None, :, :], axis=2)
        attr = attr[d.min(1) > kill]
        if not grew:
            break
    return np.array(nodes), np.array(parent), np.array(is_root)


def limb_widths(parent, is_root, base=2.6, tip=1.0, power=0.55):
    n = len(parent)
    tips = np.ones(n)
    for i in range(n - 1, -1, -1):
        if parent[i] >= 0:
            tips[parent[i]] += tips[i]
    grown = ~is_root
    if not grown.any():
        return tips
    mx = tips[grown].max()
    return tip + (base - tip) * (tips / mx) ** power


def _inside(crown, x, y):
    xi, yi = int(round(x)), int(round(y))
    return 0 <= yi < crown.shape[0] and 0 <= xi < crown.shape[1] and crown[yi, xi]


def ray_length(crown, x, y, ang, maxlen=200):
    """How far a straight line from (x, y) at `ang` stays inside the crown."""
    for k in range(1, maxlen):
        if not _inside(crown, x + np.cos(ang) * k, y + np.sin(ang) * k):
            return k - 1
    return maxlen


def oak_limbs(crown, roots, seed=0, depth=5, spread=0.5, shrink=0.7, fill=0.62, curl=0.18, rise=0.06,
              base_width=3.0, wshrink=0.68, first=0.42, fringe=0):
    """Recursive limbs for a bare broad-crowned tree: each root (x, y, angle, width) grows a
    curving limb that forks in two (sometimes three) until the twigs reach the old crown's edge.
    Returns segments [(x0, y0, x1, y1, width, angle)]."""
    segs = []
    counter = [0]

    def h():
        counter[0] += 1
        return float(hash2(counter[0], 7, seed))

    def grow(x, y, ang, length, width, d):
        steps = max(1, int(length / 3))
        step = length / steps
        for _ in range(steps):
            ang += (h() - 0.5) * curl * 2
            # limbs bend a little toward the light
            up = -np.pi / 2
            ang += ((up - ang + np.pi) % (2 * np.pi) - np.pi) * rise
            nx, ny = x + np.cos(ang) * step, y + np.sin(ang) * step
            if not _inside(crown, nx, ny):
                break
            segs.append((x, y, nx, ny, width, ang))
            x, y = nx, ny
        if d >= depth or width < 0.6:
            # a fringe of short 1px twigs at the tip: the fine lace of a bare crown
            for k in range(fringe):
                a = ang + (h() - 0.5) * 1.8
                ln = 3.0 + h() * 5.0
                tx, ty = x, y
                for _ in range(int(ln)):
                    nx, ny = tx + np.cos(a), ty + np.sin(a)
                    if not _inside(crown, nx, ny):
                        break
                    segs.append((tx, ty, nx, ny, 0.65, a))
                    tx, ty = nx, ny
                    a += (h() - 0.5) * 0.5
            return
        kids = 3 if h() < 0.25 and d < depth - 1 else 2
        for k in range(kids):
            off = (k - (kids - 1) / 2) * spread * (0.7 + 0.6 * h()) * (2 if kids == 2 else 1)
            a = ang + off
            room = ray_length(crown, x, y, a)
            ln = min(length * shrink * (0.8 + 0.4 * h()), room * fill + 2)
            if ln < 2.5:
                continue
            grow(x, y, a, ln, max(0.7, width * wshrink), d + 1)

    for (x, y, ang, w) in roots:
        room = ray_length(crown, x, y, ang)
        grow(x, y, ang, max(4.0, room * first), w if w else base_width, 0)
    return segs


def draw_limbs(shape, segs):
    """Width map (max width per pixel) and angle map of the limbs."""
    H, W = shape
    wmap = np.zeros((H, W), np.float32)
    amap = np.zeros((H, W), np.float32)
    for (x0, y0, x1, y1, w, a) in segs:
        n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        r = max(0.0, (w - 1) / 2)
        for t in np.linspace(0, 1, n):
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            for dy in range(-int(np.ceil(r)), int(np.ceil(r)) + 1):
                for dx in range(-int(np.ceil(r)), int(np.ceil(r)) + 1):
                    if dx * dx + dy * dy > (r + 0.35) ** 2:
                        continue
                    xx, yy = int(round(cx + dx)), int(round(cy + dy))
                    if 0 <= yy < H and 0 <= xx < W and w >= wmap[yy, xx]:
                        wmap[yy, xx] = w
                        amap[yy, xx] = a
    return wmap, amap


def paint_limbs(cv, wmap, amap, pal, seed=0, snow=True, snow_ramp=None, perch=0.55):
    """Shades the limbs (lit from the upper left; pal dark->light) and lays snow along the upper
    side of every limb that is not too steep: a continuous line on the big ones, clumps on twigs."""
    from seasonlib import value_noise
    wood = wmap > 0
    H, W = wood.shape
    n = len(pal)
    t = np.full(wood.shape, n // 2, int)
    above_open = ~shift(wood, 0, 1)
    below_open = ~shift(wood, 0, -1)
    left_open = ~shift(wood, 1, 0)
    right_open = ~shift(wood, -1, 0)
    t[wood & (wmap < 1.6)] = 1
    t[wood & (wmap >= 1.6) & (below_open | right_open)] = 0
    t[wood & (wmap >= 1.6) & (above_open | left_open)] = min(n - 1, n // 2 + 1)
    t[wood & (wmap >= 2.6) & above_open & left_open] = n - 1
    cv[wood, :3] = pal[t[wood]]
    cv[wood, 3] = 255
    snowm = np.zeros(wood.shape, bool)
    if not snow:
        return snowm
    sr = snow_ramp
    flat = np.abs(np.sin(amap)) < 0.8
    clump = value_noise(H, W, (4, 2), seed) < perch
    # snow sits on top: the pixel above a lit upper edge
    top = wood & above_open & flat
    big = top & (wmap >= 1.6)
    small = top & (wmap < 1.6) & clump & (np.abs(np.sin(amap)) < 0.35)
    lay = shift(big | small, 0, -1) & ~wood
    cv[lay, :3] = sr[5]
    cv[lay, 3] = 255
    # the limb's own top row whitens a little where the load is thick
    thick = big & clump
    cv[thick, :3] = sr[3]
    snowm = lay | thick
    return snowm
