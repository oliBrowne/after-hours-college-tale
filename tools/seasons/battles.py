"""Season layers for the battle backdrops (battle-near.png, or battle-far.png when a room has no
near layer).

The battle scenery is rendered in perspective by tools/room_art/build_battle_<id>.py with whole
arrays, so the material trace has nothing to say about it; this works from colour and geometry:
the near layer's transparent pixels are the sky, rows below the camera's horizon whose colours
belong to the floor's own palette are the floor (green ones lawn, the rest paving), green
foliage above the floor is evergreen or hedge, and every top edge under open sky is a ledge.

  winter  lawn under snow, paving under a blanket with a shovelled path to the vanishing point,
          snow on boughs and on every top edge against the sky, warm snow by lit windows
  fall    green foliage turned gold, orange and red; lawns olive with leaf litter
  spring  lawns and foliage fresh and saturated, blossom on some of the green trees

Autumn-coloured crowns are left as painted: by colour alone they cannot be told from brick.

Writes overlays: only the changed pixels (NativeSeason.overlay, scenes/battle_backdrop.gd)."""
import numpy as np
import seasonlib as L
from seasonlib import lum, hsv, hue_in, shift, dilate, erode, value_noise, grid_hash, components, ramp
import snow as S
import trees as TR


def classify(img, sky, horizon):
    H, W = img.shape[:2]
    rgb = img[..., :3].astype(np.int64) >> 3
    key = (rgb[..., 0] << 10) | (rgb[..., 1] << 5) | rgb[..., 2]
    rows = np.arange(H)[:, None]
    # the floor's palette: colours of the bottom band (nearly all floor)
    band = slice(min(H - 40, horizon + 30), H)
    mid = slice(int(W * 0.2), int(W * 0.8))
    sample = key[band, mid][~sky[band, mid]]
    cols, counts = np.unique(sample, return_counts=True)
    floor_cols = cols[counts >= 4]
    floor = (rows >= horizon) & np.isin(key, floor_cols) & ~sky
    # close little holes (stones' specks) so the floor reads whole
    floor |= erode(dilate(floor, 1), 1) & (rows >= horizon) & ~sky
    h, s, v = hsv(img)
    lawn = floor & hue_in(h, 55, 185) & (s > 0.12)
    paving = floor & ~lawn
    above = ~sky & ~floor
    green = above & hue_in(h, 65, 190) & (s > 0.12) & (v > 0.06)
    autumn = above & hue_in(h, 0, 55) & (s > 0.5) & (v > 0.22)
    return floor, lawn, paving, above, green, autumn


def far_mountains(far, open_, rows, seed=0, lmax=0.42, dim=0.25):
    """Snow on the range painted into the far image: pixels in `rows` that show through the near
    layer (open_) and are darker than the sky (lum below lmax, scanned top-down per column)."""
    cv = far.astype(np.float32)
    H, W = open_.shape
    y0, y1 = rows
    band = np.zeros((H, W), bool)
    band[y0:y1] = True
    # the ridge: scanning down each column, the first pixel whose colour departs from the sky
    # above it and stays different for three rows (stars are single pixels)
    c = far[..., :3].astype(np.float32)
    body = lum(far[min(y1, H) - 1])           # the range's own tone at the bottom of the band
    ref = np.zeros((H, W, 3), np.float32)
    ref[y0] = c[y0]
    hit = np.zeros((H, W), bool)
    for y in range(y0 + 1, min(y1, H - 3)):
        d = [np.abs(c[y + k] - ref[y - 1]).sum(-1) for k in range(3)]
        hit[y] = (d[0] > 30) & (d[1] > 30) & (d[2] > 30) & (lum(far[y]) <= np.minimum(lmax, body + 0.08))
        ref[y] = np.where(hit[y][:, None], ref[y - 1], c[y])
    # a ridge is continuous: each column's ridge row is the median of its neighbours' (±4)
    ridge = np.where(hit.any(0), hit.argmax(0), y1).astype(np.float32)
    pad = np.pad(ridge, 4, mode="edge")
    med = np.median(np.stack([pad[k:k + W] for k in range(9)]), 0)
    ridge = np.where(np.abs(ridge - med) > 3, med, ridge)
    mtn = (np.arange(H)[:, None] >= ridge[None, :]) & band & open_
    sky = band & ~mtn | (np.arange(H)[:, None] < y0)
    S.mountain(cv, mtn, sky, seed=seed, line=2, slope=0.45, dim=dim, thr=0.7)
    return cv


def winter(img, sky, horizon, seed=0, lane=True, dim=0.85):
    cv = img.astype(np.float32)
    H, W = sky.shape
    floor, lawn, paving, above, green, autumn = classify(img, sky, horizon)
    snow = np.zeros((H, W), bool)
    snow |= S.lawn(cv, lawn, seed=seed)
    if paving.any():
        ys, xs = np.mgrid[0:H, 0:W]
        path = (np.abs(xs - W / 2) < 10 + (ys - horizon) * 0.55) & (ys >= horizon) if lane else np.zeros_like(paving)
        snow |= S.shovel(cv, paving, path & paving, seed=seed + 1)
    open_ = sky | ~above
    snow |= S.load_foliage(cv, green, open_ & ~green, seed=seed + 2, heavy=0.4)
    # caps on every top edge against the sky
    solid = above & ~snow
    top = solid & shift(sky, 0, 1, fill=True)
    t = top & (S.runs_h(top, 2) | (shift(top, 1, 0) & shift(top, -1, 0)))
    cap = t | (shift(t, 0, -1) & solid)
    cv[t, :3] = S.SNOW[5]
    second = shift(t, 0, -1) & solid
    cv[second, :3] = S.SNOW[4]
    under = shift(cap, 0, -1) & solid & ~cap
    cv[under, :3] *= 0.8
    snow |= cap
    # lit windows warm the snow beside them
    h, s, v = hsv(img)
    lit = ~sky & hue_in(h, 22, 60) & (s > 0.3) & (v > 0.78)
    S.warm_light(cv, snow, lit, reach=4)
    if dim < 1:
        # night: the snow takes the dark, a little bluer
        cv[snow, :3] = cv[snow, :3] * dim * np.array([0.96, 0.98, 1.04])
    return cv


def fall(img, sky, horizon, seed=0):
    cv = img.astype(np.float32)
    H, W = sky.shape
    floor, lawn, paving, above, green, autumn = classify(img, sky, horizon)
    ramps = [TR.FALL["orange"], TR.FALL["red"], TR.FALL["gold"], TR.FALL["crimson"]]
    lab, n = components(dilate(green, 1) & green)
    blob = value_noise(H, W, 7, seed)
    for i in range(1, n + 1):
        part = lab == i
        if part.sum() < 6:
            continue
        a = ramps[int(L.hash2(i, 1, seed) * 4)]
        b = ramps[int(L.hash2(i, 2, seed) * 4)]
        pa = part & (blob < 0.6)
        _rank(cv, pa, a)
        _rank(cv, part & ~pa, b)
    _grade(cv, lawn, 68, 0.42, 0.88, 0.98)
    lit = lawn | paving
    pts = lit & (grid_hash(H, W, seed + 7) < 0.02)
    pal = ramp(["#5a1e18", "#8e2c1e", "#b8501c", "#d07a24", "#e0a83a"])
    cv[pts, :3] = pal[(grid_hash(H, W, seed + 8) * len(pal)).astype(int)[pts] % len(pal)]
    return cv


def spring(img, sky, horizon, seed=0):
    cv = img.astype(np.float32)
    H, W = sky.shape
    floor, lawn, paving, above, green, autumn = classify(img, sky, horizon)
    _grade(cv, lawn, 104, 0.35, 1.22, 1.05)
    _grade(cv, green, 108, 0.3, 1.2, 1.05)
    # blossom on some of the green crowns (autumn-coloured ones are left alone: by colour alone
    # they cannot be told from brick and sandstone)
    lab, n = components(dilate(green, 1) & green)
    for i in range(1, n + 1):
        part = lab == i
        if part.sum() < 40 or L.hash2(i, 3, seed) > 0.35:
            continue
        TR.blossom(cv, part, TR.SPRING["pink" if L.hash2(i, 4, seed) < 0.6 else "white"], seed=seed + i, amount=0.4)
    pts = lawn & (grid_hash(H, W, seed + 6) < 0.006)
    cv[pts, :3] = L.hexrgb("#f4e04a")
    return cv


def _rank(cv, mask, pal):
    if not mask.any():
        return
    px = cv[mask, :3]
    cols, inv, counts = np.unique(px.astype(np.int32), axis=0, return_inverse=True, return_counts=True)
    lv = lum(cols.astype(np.float32))
    order = np.argsort(lv)
    cum = np.cumsum(counts[order]) / counts.sum()
    rank = np.empty(len(cols))
    rank[order] = cum - counts[order] / counts.sum() / 2
    idx = np.clip((rank * len(pal)).astype(int), 0, len(pal) - 1)
    cv[mask, :3] = pal[idx][inv.reshape(-1)]


def _grade(cv, mask, h_to, pull, s_mul, v_mul):
    if not mask.any():
        return
    from build_seasons import per_colour, grade
    per_colour(cv, mask, grade(h_to=h_to, h_pull=pull, s_mul=s_mul, v_mul=v_mul))


FN = {"winter": winter, "fall": fall, "spring": spring}


def layer(base, season, horizon, seed=0, sky=None, **kw):
    """The season's overlay for a battle image `base` (RGBA uint8): changed pixels only."""
    if sky is None:
        sky = base[..., 3] == 0
    out = np.clip(np.round(FN[season](base, sky, horizon, seed=seed, **kw)), 0, 255).astype(np.uint8)
    out[..., 3] = base[..., 3]
    lay = out.copy()
    lay[np.all(out == base, axis=-1) | (base[..., 3] == 0)] = 0
    return lay
