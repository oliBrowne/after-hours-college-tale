"""Winter operations on a room image: snow on lawns, caps on anything facing up, roofs under a
snow load, trampled paths, snowy mountains, warm window light on snow.

Every op takes `cv`, a float32 (H, W, 4) RGBA array in 0-255 that it edits in place, plus bool
masks, and returns the mask of pixels it turned to snow (so later ops can light them)."""
import numpy as np
from seasonlib import (hexrgb, ramp, lum, hsv, hue_in, shift, dilate, erode, distance, value_noise, fbm,
                       grid_hash, hash2)

# Snow, painted brighter than it shows (the world is tinted (0.68, 0.72, 0.84) at night): deep
# blue shadow up to a near-white sparkle.
SNOW = ramp(["#56628c", "#7684b2", "#9aa8d2", "#bcc8ea", "#d8e1f6", "#f2f6ff"])
# Snow lit by lamps and windows.
WARM = ramp(["#9c8a8e", "#c4aa9c", "#e6caa8", "#f8e4c2", "#fff4dc"])
# Packed / trodden snow and slush on paving: greyer.
PACKED = ramp(["#5a5c74", "#767a94", "#9298b2", "#b0b6cc", "#cad0e2"])
ICE = ramp(["#3c4664", "#566486", "#7a8cb2"])


def put(cv, mask, colour):
    cv[mask, :3] = colour
    cv[mask, 3] = 255


def runs_h(mask, min_len):
    """Keeps only horizontal runs of at least min_len pixels."""
    out = np.zeros_like(mask)
    h, w = mask.shape
    for y in range(h):
        row = mask[y]
        if not row.any():
            continue
        d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
        starts = np.nonzero(d == 1)[0]
        ends = np.nonzero(d == -1)[0]
        for s, e in zip(starts, ends):
            if e - s >= min_len:
                out[y, s:e] = True
    return out


def run_lengths(mask):
    """Per pixel: length of the horizontal run it belongs to, and its index within it."""
    h, w = mask.shape
    length = np.zeros((h, w), np.int32)
    index = np.zeros((h, w), np.int32)
    for y in range(h):
        row = mask[y]
        if not row.any():
            continue
        d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
        starts = np.nonzero(d == 1)[0]
        ends = np.nonzero(d == -1)[0]
        for s, e in zip(starts, ends):
            length[y, s:e] = e - s
            index[y, s:e] = np.arange(e - s)
    return length, index


# ---------------------------------------------------------------------------------------------
# lawns
# ---------------------------------------------------------------------------------------------
def grass_mask(cv, region, hue=(55, 185), smin=0.12, vmin=0.07):
    h, s, v = hsv(cv)
    return region & hue_in(h, *hue) & (s >= smin) & (v >= vmin) & (cv[..., 3] > 0)


def lawn(cv, grass, litter=None, seed=0, stripe=(3, 4), warm_shift=0.10, keep_litter=0.0):
    """Turns grass into snow cover, colour by colour: the mown stripes become two soft snow tones,
    tree shadows blue shadow, blades and clover sparkle, lamp pools warm snow."""
    if not grass.any():
        return grass
    rgb = cv[..., :3]
    L = lum(rgb)
    warmth = (rgb[..., 0] - rgb[..., 2]) / 255.0
    keys = (rgb[..., 0].astype(np.int64) << 16) | (rgb[..., 1].astype(np.int64) << 8) | rgb[..., 2].astype(np.int64)
    gk = keys[grass]
    cols, counts = np.unique(gk, return_counts=True)
    order = np.argsort(-counts)
    # the two mown-stripe colours: the most common grass colours with distinct lightness
    first = cols[order[0]]
    lum_of = {}
    for c in cols:
        r, g, b = (c >> 16) & 255, (c >> 8) & 255, c & 255
        lum_of[c] = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    second = next((cols[i] for i in order[1:] if abs(lum_of[cols[i]] - lum_of[first]) > 0.02), first)
    lo, hi = sorted([lum_of[first], lum_of[second]])
    base_warm = float(np.median(warmth[grass]))
    out = np.zeros_like(L, dtype=np.int32)
    l = L
    idx = np.where(l >= hi + 0.07, 5, np.where(l >= (lo + hi) / 2, stripe[1], np.where(l >= lo - 0.035, stripe[0],
                   np.where(l >= lo - 0.11, 2, np.where(l >= lo - 0.19, 1, 0)))))
    out = idx
    snow_rgb = SNOW[np.clip(out, 0, 5)]
    warm = (warmth - base_warm > warm_shift) & (l >= lo - 0.02)
    widx = np.clip(np.where(l >= hi + 0.12, 4, np.where(l >= hi + 0.03, 3, np.where(l >= lo, 2, 1))), 0, 4)
    snow_rgb = np.where(warm[..., None], WARM[widx], snow_rgb)
    m = grass.copy()
    cv[m, :3] = snow_rgb[m]
    if litter is not None and litter.any():
        # leaves already on the lawn sink under the snow; a few stay dark at the surface
        keep = litter & (grid_hash(*litter.shape, seed=seed + 5) < keep_litter)
        sunk = litter & ~keep
        cv[sunk, :3] = SNOW[4]
        cv[keep, :3] = hexrgb("#6e5a58")
        m |= litter
    return m


# ---------------------------------------------------------------------------------------------
# caps: snow lying on top of whatever faces the sky
# ---------------------------------------------------------------------------------------------
def caps(cv, solid, open_above, region, depth=2, min_run=3, pile=True, seed=0, tones=(5, 4, 3), shade_below=0.22):
    """Snow on every pixel of `solid` (inside region) whose upper neighbour is `open_above`
    (sky or transparent). Runs of `min_run`+ get a cap `depth` px thick; a pile rises one pixel
    into the open space above wide runs, rounded at the ends; the pixel under the cap darkens."""
    top = solid & shift(open_above, 0, 1, fill=True) & region
    top &= runs_h(top, min_run) | (runs_h(top, 1) & shift(top, 1, 0) & shift(top, -1, 0))
    length, index = run_lengths(top)
    snow = np.zeros_like(top)
    painted = np.zeros(top.shape, np.int8) - 1
    ys, xs = np.nonzero(top)
    H, W = top.shape
    for y, x in zip(ys, xs):
        n, i = length[y, x], index[y, x]
        edge = min(i, n - 1 - i)
        d = depth if edge >= 1 else max(1, depth - 1)
        if n < 5:
            d = min(d, 1 + (edge >= 1))
        # body of the cap (replaces the top rows of the object)
        for k in range(d):
            yy = y + k
            if yy < H and solid[yy, x]:
                painted[yy, x] = tones[min(k + 1, len(tones) - 1)] if k else tones[1]
        # the pile rising above the edge
        if pile and n >= 6 and edge >= 2 and y - 1 >= 0 and open_above[y - 1, x]:
            painted[y - 1, x] = tones[0]
            if n >= 14 and edge >= 4 and y - 2 >= 0 and open_above[y - 2, x] and hash2(x // 5, y, seed) < 0.35:
                painted[y - 2, x] = tones[0]
                painted[y - 1, x] = tones[1]
    snow = painted >= 0
    cv[snow, :3] = SNOW[painted[snow]]
    cv[snow, 3] = 255
    # thin shadow line under the cap where the object continues
    under = shift(snow, 0, 1) & ~snow & solid
    cv[under, :3] *= (1 - shade_below)
    return snow


def ledge_lines(cv, lines, seed=0):
    """Explicit snow ledges from the hints: [x0, x1, y, depth] puts a cap whose bottom row is y."""
    H, W = cv.shape[:2]
    snow = np.zeros((H, W), bool)
    for ln in lines:
        x0, x1, y = int(ln[0]), int(ln[1]), int(ln[2])
        d = int(ln[3]) if len(ln) > 3 else 2
        for x in range(max(0, x0), min(W, x1 + 1)):
            edge = min(x - x0, x1 - x)
            dd = d if edge >= 1 else max(1, d - 1)
            if edge >= 3 and d >= 2 and hash2(x // 4, y, seed) < 0.3:
                dd += 1
            for k in range(dd):
                yy = y - k
                if 0 <= yy < H:
                    t = 5 if k == dd - 1 else (4 if k == dd - 2 else 3)
                    cv[yy, x, :3] = SNOW[t]
                    cv[yy, x, 3] = 255
                    snow[yy, x] = True
            if y + 1 < H:
                cv[y + 1, x, :3] *= 0.8
    return snow


def ledge_auto(cv, region, min_run=6, rise=0.05, drop=0.03, skip=None):
    """Finds the lit top faces of sills, cornices and copings (a light row with darker wall above
    it and its own shadow below) and lays a one-pixel snow line on them, one more on wide runs."""
    L = lum(cv[..., :3])
    above = shift(L, 0, 1)
    below = shift(L, 0, -1)
    cand = region & (L - above > rise) & (L - below > drop)
    if skip is not None:
        cand &= ~skip
    cand = runs_h(cand, min_run)
    length, index = run_lengths(cand)
    snow = cand.copy()
    cv[cand, :3] = SNOW[4]
    up = shift(cand & (length >= 10) & (index >= 1) & (index <= length - 2), 0, -1)
    up &= region
    cv[up, :3] = SNOW[5]
    snow |= up
    return snow


# ---------------------------------------------------------------------------------------------
# roofs
# ---------------------------------------------------------------------------------------------
def roof(cv, mask, eave=3, seed=0, min_cover=1, sky=None, dim=0.0):
    """A pitched tile roof under snow: from the ridge down, snow follows the tile rows (their light
    and dark rows become a soft ripple in the snow) and ends in a scalloped lip a few rows above the
    eave, so the red tile still shows along the bottom; a thin blue shadow under the lip."""
    H, W = mask.shape
    L = lum(cv[..., :3])
    snow = np.zeros((H, W), bool)
    tone = np.zeros((H, W), np.int32)
    wob = value_noise(1, W, 7, seed)[0]
    for x in range(W):
        col = np.nonzero(mask[:, x])[0]
        if len(col) == 0:
            continue
        # contiguous vertical spans
        splits = np.nonzero(np.diff(col) > 1)[0]
        for seg in np.split(col, splits + 1):
            top, bot = seg[0], seg[-1]
            n = bot - top + 1
            e = eave if n > eave + 2 else max(0, n - min_cover - 1)
            lip = bot - e + int(round((wob[x] - 0.5) * 2.4))
            lip = max(top + min(min_cover, n) - 1, min(bot, lip))
            for y in range(top, lip + 1):
                snow[y, x] = True
    if not snow.any():
        return snow
    # tone from the tile pattern underneath: light rows -> brighter snow
    med = np.median(L[snow])
    tone[snow] = np.where(L[snow] > med + 0.04, 5, np.where(L[snow] > med - 0.05, 4, 3))
    firsts = snow & ~shift(snow, 0, 1)
    tone[firsts] = 5
    lips = snow & ~shift(snow, 0, -1)
    tone[lips] = 3
    col = SNOW[tone]
    if dim:
        col = col * (1 - dim) + cv[..., :3] * dim
    cv[snow, :3] = col[snow]
    under = shift(snow, 0, 1) & mask & ~snow
    cv[under, :3] = cv[under, :3] * 0.62 + SNOW[0] * 0.38 * 0.6
    # the ridge pile against the sky
    if sky is not None:
        pile = shift(firsts, 0, -1) & sky
        pl, pi = run_lengths(pile)
        pile &= (pl >= 6) & (pi >= 1) & (pi <= pl - 2)
        cv[pile, :3] = SNOW[5] if not dim else SNOW[5] * (1 - dim) + cv[pile, :3] * dim
        cv[pile, 3] = 255
        snow |= pile
    return snow


# ---------------------------------------------------------------------------------------------
# paths and paving
# ---------------------------------------------------------------------------------------------
def trample(cv, mask, coverage=0.45, seed=0, cell=11, edge=3, joints=True, keep=None, banks=None, packed=False,
            cool=0.18):
    """Shovelled / trodden paving: crisp-edged snow patches (thicker near the path edges and in
    `banks`), snow packed into the dark joints between stones, and the stone that shows turned a
    little colder and darker (wet). `keep` marks where feet have cleared it (fewer patches)."""
    H, W = mask.shape
    rgb = cv[..., :3]
    L = lum(rgb)
    n = fbm(H, W, cell, seed=seed, octaves=3)
    dist = distance(~mask, maxd=edge + 2)
    bias = np.clip((edge + 1 - dist) / (edge + 1), 0, 1) * 0.55
    if banks is not None:
        bias = np.maximum(bias, banks.astype(np.float32) * 0.5)
    if keep is not None:
        bias -= keep.astype(np.float32) * 0.75
    field = n + bias
    thr = np.quantile(field[mask], 1 - coverage) if mask.any() else 1
    cover = mask & (field > thr)
    # tidy: no single pixels or one-pixel slivers
    cover = erode(dilate(cover, 1), 1) & mask
    cover &= dilate(erode(cover, 1), 1) | (dist <= 1)
    snow = cover.copy()
    sr = PACKED if packed else SNOW
    t = np.full((H, W), 3, np.int32)
    t[cover & ~shift(cover, 0, 1)] = 4
    t[cover & ~shift(cover, 0, -1)] = 2
    hi = cover & (n > thr + 0.12) & shift(cover, 0, 1) & shift(cover, 0, -1)
    t[hi] = 4
    cv[cover, :3] = sr[t[cover]]
    bare = mask & ~cover
    # stone between the patches: colder, wet
    grey = rgb[bare].mean(-1, keepdims=True)
    cv[bare, :3] = (rgb[bare] * (1 - cool) + (grey * np.array([0.92, 0.96, 1.12])) * cool) * 0.9
    if joints:
        box = (L + shift(L, 1, 0) + shift(L, -1, 0) + shift(L, 0, 1) + shift(L, 0, -1)) / 5
        j = bare & (L < box - 0.035)
        jn = value_noise(H, W, 5, seed + 9)
        j &= jn > 0.35
        cv[j, :3] = sr[2]
        snow |= j
    # the bare stone right under a patch gets its shadow
    sh = shift(cover, 0, 1) & bare
    cv[sh, :3] *= 0.85
    return snow


# ---------------------------------------------------------------------------------------------
# mountains
# ---------------------------------------------------------------------------------------------
def mountain(cv, mask, sky, seed=0, line=3, slope=0.5, dim=0.0, top_y=None, bottom_y=None, rock_keep=0.75,
             streak=(4, 14), thr=0.62):
    """Snow on the range: a bright crest wherever rock meets sky, snowfields on the shadowed and
    forested slopes thicker toward the summits, streaks of snow on the ledges of the lit rock."""
    H, W = mask.shape
    rgb = cv[..., :3]
    L = lum(rgb)
    h, s, v = hsv(rgb)
    ys = np.arange(H)[:, None].repeat(W, 1).astype(np.float32)
    if top_y is None:
        rows = np.nonzero(mask.any(1))[0]
        top_y, bottom_y = (rows[0], rows[-1]) if len(rows) else (0, H)
    height = np.clip(1 - (ys - top_y) / max(1, bottom_y - top_y), 0, 1)
    d_sky = distance(sky, maxd=line + 2)
    crest = mask & (d_sky <= line) & (d_sky >= 1)
    lit = mask & (s > 0.32) & hue_in(h, 345, 45) & (v > 0.45)
    shade = mask & ~lit
    n = fbm(H, W, (6, 9), seed=seed, octaves=3)
    n2 = fbm(H, W, streak, seed=seed + 3, octaves=2)
    field_shade = n * 0.6 + height * 0.9 * slope + 0.15
    snowfield = shade & (field_shade > thr)
    snowfield = erode(dilate(snowfield, 1), 1) & shade
    rockstreak = lit & (n2 + height * 0.35 > 0.62 + (1 - rock_keep) * -0.2) & (L < np.quantile(L[lit], 0.6) if lit.any() else False)
    snow = crest | snowfield | rockstreak
    t = np.where(L > 0.55, 5, np.where(L > 0.38, 4, np.where(L > 0.22, 3, 2)))
    t = np.where(crest, np.maximum(t, 4), t)
    t = np.where(rockstreak, np.maximum(t - 1, 3), t)
    col = SNOW[t]
    if dim:
        col = col * (1 - dim) + rgb * dim
    cv[snow, :3] = col[snow]
    # the snow on the lit side picks up the sunset
    if lit.any():
        warm = snow & lit
        cv[warm, :3] = cv[warm, :3] * 0.7 + rgb[warm] * 0.3 + np.array([18, 6, -6]) * 0.6
    return snow


# ---------------------------------------------------------------------------------------------
# evergreens and shrubs under a snow load
# ---------------------------------------------------------------------------------------------
def load_foliage(cv, mask, open_above, seed=0, rise=0.05, heavy=0.5, depth=2, tones=(5, 4)):
    """Snow on each bough: where the pixel above is open (sky, transparent, not this plant) and on
    the lit upper edge of every tier inside the crown (a pixel brighter than the one above it)."""
    H, W = mask.shape
    L = lum(cv[..., :3])
    above_open = shift(open_above | ~mask, 0, 1, fill=True)
    lit_edge = (L - shift(L, 0, 1) > rise) & (L > np.quantile(L[mask], 0.35) if mask.any() else False)
    top = mask & (above_open | lit_edge)
    n = value_noise(H, W, 4, seed)
    top &= (n < 0.5 + heavy) | above_open
    snow = top.copy()
    cv[top, :3] = SNOW[tones[0]]
    if depth >= 2:
        sec = shift(top, 0, 1) & mask & ~top & (n < heavy + 0.25)
        cv[sec, :3] = SNOW[tones[1]]
        snow |= sec
    return snow


def warm_light(cv, snow, light, reach=4):
    """Snow next to lit windows and lamp heads takes their amber."""
    d = distance(light, maxd=reach + 1)
    near = snow & (d <= reach)
    L = lum(cv[..., :3])
    t = np.clip(np.round((L - 0.45) * 8), 0, 4).astype(int)
    k = np.clip((reach + 1 - d) / (reach + 1), 0, 1)[..., None]
    cv[near, :3] = (cv[..., :3] * (1 - k * 0.75) + WARM[t] * k * 0.75)[near]
    return near


def lit_mask(cv, region=None, vmin=0.72, smin=0.35):
    h, s, v = hsv(cv[..., :3])
    m = hue_in(h, 25, 58) & (s >= smin) & (v >= vmin)
    if region is not None:
        m &= region
    return m


def shovel(cv, mask, lane, seed=0, packed_patches=0.12, joints=0.65, cool=0.2, bank=True, holes=None):
    """A shovelled path through snow-covered paving: inside `lane` (jittered 1-2px in from its
    outline) the stone shows, cold and wet, with snow packed into its joints and a few trodden
    packed patches; everywhere else on `mask` lies an even blanket whose tone follows the stones
    under it (a soft ripple), with a bright lip along the cut and a blue shadow on the stone below."""
    H, W = mask.shape
    rgb = cv[..., :3].copy()
    L = lum(rgb)
    lane = lane & mask
    din = distance(~(lane | holes) if holes is not None else ~lane, maxd=6)
    jit = value_noise(H, W, (9, 5), seed) * 0.7 + value_noise(H, W, (3, 2), seed + 3) * 0.3
    cleared = lane & (din > 1 + (jit * 4.0).astype(int))
    cleared = erode(dilate(cleared, 1), 1) & lane
    cover = mask & ~cleared
    # blanket: tone from the stone pattern under it
    box = (L + shift(L, 1, 0) + shift(L, -1, 0) + shift(L, 0, 1) + shift(L, 0, -1)) / 5
    t = np.full((H, W), 4, np.int32)
    t[L < box - 0.03] = 3
    t[(L > box + 0.03)] = 4
    edge_top = cover & shift(cleared, 0, -1)          # snow whose lower neighbour is cleared stone
    t[edge_top] = 5
    t[cover & ~shift(mask, 0, 1)] = np.minimum(t[cover & ~shift(mask, 0, 1)], 4)
    cv[cover, :3] = SNOW[t[cover]]
    # cleared stone: colder and darker
    grey = rgb[cleared].mean(-1, keepdims=True)
    cv[cleared, :3] = (rgb[cleared] * (1 - cool) + (grey * np.array([0.92, 0.96, 1.12])) * cool) * 0.88
    snow = cover.copy()
    if joints > 0:
        j = cleared & (L < box - 0.035) & (value_noise(H, W, 5, seed + 9) < joints)
        cv[j, :3] = PACKED[3]
        snow |= j
    if packed_patches > 0:
        pn = fbm(H, W, 7, seed + 4, octaves=2)
        p = cleared & (pn > 1 - packed_patches)
        p = erode(dilate(p, 1), 1) & cleared
        cv[p, :3] = PACKED[np.where(shift(p, 0, 1)[p], 3, 4)]
        snow |= p
    if bank:
        sh = cleared & shift(cover, 0, 1)
        cv[sh, :3] = cv[sh, :3] * 0.7 + SNOW[0] * 0.3 * 0.7
    return snow
