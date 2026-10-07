"""Battle backdrop for the Norlin quad (N01): the fight happens up on the library's portico.

The camera stands between the last two columns with its back to the bronze doors, looking west
over the quad: the portico's limestone floor (lamplight from the doors behind, moonlight in
front) ends at the top step; below it the quad - lawn bands, the paths, the planter with its red
tree, the quiet lamps, two big oaks - and beyond the campus treeline the Flatirons stand dark
under the moon, the last of the sunset still glowing behind them. Near columns frame both edges
and the architrave runs across the top. Clouds drift behind the mountains, bats flit, pages and
leaves blow across, the lamps breathe."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from midlib import sprite_from_cell
from pixel import Canvas, C, shade
from sky import flatirons_panel
from clouds import cloud_strip
from props import OUT, IRON, AMBER, lamp_post
from lib_norlin import quiet_lamp_post, stone_planter, lantern_head, LIME, GRASS, PAVE_N, PAVE_RED, PAGE
from persp import View, hash2, fog, pal_array, rgba_of, warm_light

ROOM = "N01"
INK = "#10121e"
HAZE = "#2a2848"
NIGHT_CLOUD = ["#2c2648", "#3a3058", "#463864", "#52406c", "#6a4c76", "#8e5e80", "#b47486"]
Z_EDGE = 440.0          # the top step: the portico floor ends here
DROP = 40.0             # the quad lies this far below the portico floor
PATH_HALF = 46.0
COURT = (0.0, 1250.0, 150.0)     # oval court around the planter: X, Z, radius
LAMPS = [(-95, 1030), (95, 1030), (-95, 1520), (95, 1520)]
MOON = (196, 34)


def sky_strip(w=640, h=112):
    """Night sky looking west: stepped indigo bands warming to a plum afterglow at the horizon,
    stars, the moon with a stepped halo. Returns (rgba, star points)."""
    cv = Canvas(w, h)
    bands = ["#0f1030", "#141536", "#1a1a3e", "#212048", "#2a2552", "#352b5a", "#45325f", "#5a3c64", "#6e4466"]
    for y in range(h):
        t = y / (h - 1)
        cv.hline(0, y, w, bands[min(len(bands) - 1, int(t ** 1.4 * len(bands)))])
    rng = np.random.default_rng(11)
    stars = []
    for _ in range(150):
        sx, sy = int(rng.integers(0, w)), int(rng.integers(14, 78))
        if (sx - MOON[0]) ** 2 + (sy - MOON[1]) ** 2 < 26 ** 2:
            continue
        cv.px(sx, sy, "#c8c0e0" if rng.random() < 0.7 else "#f2d27a")
        if rng.random() < 0.12 and not (380 < sx < 640 and sy < 72):
            stars.append([sx, sy, "c8c0e0", 0])
    mx, my = MOON
    for r, a in [(24, 0.05), (17, 0.07), (12, 0.1)]:
        cv.ellipse(mx - r, my - r, r * 2 + 1, r * 2 + 1, C("#efe2b8", a))
    cv.ellipse(mx - 8, my - 8, 17, 17, "#efe2b8"); cv.ellipse(mx - 6, my - 7, 9, 7, "#fff4d2")
    for (cx, cy) in [(mx - 3, my + 2), (mx + 3, my - 3), (mx + 1, my + 4), (mx - 4, my - 2)]:
        cv.px(cx, cy, "#d8c8a0")
    return cv.a, stars


def mountains(w=640, top=40, base=104):
    """The Flatirons cut from the title painting, regraded to a moonlit night: dark blue-violet
    slopes, the slab faces catching pale moonlight. Mirrored to span the width; sky transparent."""
    panel = flatirons_panel(2.5, colors=24)
    ph, pw = panel.shape[:2]
    lum = panel[..., :3] @ np.array([0.3, 0.55, 0.15], np.float32)
    sky_row = np.median(lum[:, :4], axis=1)
    from scipy import ndimage
    dark = (lum < 0.3) & (np.arange(ph)[:, None] > ph * 0.35)
    lab, n = ndimage.label(dark)
    keep = np.unique(lab[-1][lab[-1] > 0])                 # components touching the bottom row
    body = np.isin(lab, keep)
    mask = np.zeros((ph, pw), bool)
    for x in range(pw):
        col = np.where(body[:, x])[0]
        if len(col):
            mask[col[0]:, x] = True
    mask = ndimage.binary_opening(mask, structure=np.ones((1, 3)))
    ramp = pal_array(["#12142a", "#191b36", "#212442", "#2c2e52", "#3a3a62", "#4e4c74", "#6a6488"])
    idx = np.clip(((lum - 0.08) / 0.5) * (len(ramp) - 1), 0, len(ramp) - 1).round().astype(int)
    night = np.zeros_like(panel)
    night[..., :3] = ramp[idx]
    night[..., 3] = mask
    out = np.zeros((base - top, w, 4), np.float32)
    rows = min(base - top, ph)
    src = night[ph - rows:]
    out[-rows:, :pw] = src
    out[-rows:, w - pw:] = src[:, ::-1]
    # foothills bridging the middle, lower and darker
    rng = np.random.default_rng(5)
    hcv = Canvas(w, base - top)
    y = base - top - 22
    x = pw - 30
    while x < w - pw + 30:
        sw, sh = int(rng.integers(30, 60)), int(rng.integers(8, 16))
        hcv.poly([(x, base - top), (x + sw // 2, y - sh + 14), (x + sw, base - top)], "#191b36")
        hcv.line(x + sw // 2, y - sh + 14, x + sw // 2 + sw // 5, y - sh // 2 + 14, "#2c2e52")
        x += int(rng.integers(20, 40))
    m = hcv.a[..., 3] > 0
    keep = out[..., 3] > 0
    out[m & ~keep] = hcv.a[m & ~keep]
    return out


def treeline(w=640, h=30, seed=3):
    """Campus between the quad and the mountains: dark crowns, a few roofs with lit windows."""
    rng = np.random.default_rng(seed)
    cv = Canvas(w, h)
    base = h - 1
    for x in range(-10, w + 10, 8):
        hh = int(rng.integers(8, 17))
        cv.ellipse(x, base - hh, int(rng.integers(12, 20)), hh * 2, "#1e1a34")
    for x in range(10, w, int(rng.integers(70, 90))):
        bw, bh = int(rng.integers(26, 46)), int(rng.integers(9, 15))
        cv.rect(x, base - bh, bw, bh, "#1a1630")
        cv.poly([(x - 2, base - bh), (x + bw // 2, base - bh - 5), (x + bw + 2, base - bh)], "#3a2230")
        for wx in range(x + 3, x + bw - 3, 5):
            if rng.random() < 0.35:
                cv.rect(wx, base - bh + 4, 2, 2, "#c98a46" if rng.random() < 0.7 else "#e9b45c")
    for x in range(-6, w, 5):
        hh = int(rng.integers(4, 9))
        cv.ellipse(x, base - hh + 3, int(rng.integers(8, 13)), hh * 2, "#16142a")
    cv.a[base:, :, 3] = 0
    return cv.a


def quad_shader(X, Z):
    """The quad seen from the portico: mowed lawn bands, the sandstone paths and the court."""
    n = X.shape[0]
    ax = np.abs(X)
    grass = pal_array(GRASS)
    band = (np.floor(X / 60.0) + np.floor(Z / 140.0)) % 2
    tuft = hash2(np.floor(X / 7), np.floor(Z / 14), 4)
    rgb = grass[2] * (1 - band[:, None]) + grass[3] * band[:, None]
    rgb[tuft > 0.86] = grass[4]
    rgb[tuft < 0.08] = grass[1]
    pave = pal_array(PAVE_N)
    cell = hash2(np.floor((X + 7 * np.floor(Z / 20)) / 26), np.floor(Z / 20), 9)
    stone = pave[3] * (1 - cell[:, None]) + pave[5] * cell[:, None]
    jx = ((X + 7 * np.floor(Z / 20)) / 26) % 1 < 0.08
    jz = (Z / 20) % 1 < 0.1
    stone[jx | jz] = pave[1]
    cx, cz, cr = COURT
    d = np.hypot(X - cx, (Z - cz) * 0.8)
    path = (ax < PATH_HALF) | (d < cr) | (np.abs(Z - 1700) < 26) | ((np.abs(X + Z * 0.55 - 420) < 30) & (X < -60))
    rgb[path] = stone[path]
    ring = (np.abs(d - cr + 12) < 4)
    rgb[ring] = pal_array(PAVE_RED)[3]
    kerb = ~path & ((ax < PATH_HALF + 4) | (d < cr + 4))
    rgb[kerb] = pal_array(LIME)[2]
    for (lx, lz) in LAMPS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.5), 90, strength=0.4)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 900, 3200, amount=0.8)
    return out


def portico_shader(X, Z):
    """Limestone slabs of the portico floor: warm from the lit doors behind, cool toward the edge."""
    lime = pal_array(["#4a423e", "#5e544c", "#6c6156", "#786c5e", "#857766", "#a69680"])
    row = np.floor(Z / 46.0)
    off = (row % 2) * 34
    col = np.floor((X + off) / 68.0)
    t = hash2(col, row, 3)
    rgb = lime[2] * (1 - t[:, None]) + lime[3] * t[:, None]
    fx = ((X + off) / 68.0) % 1
    fz = (Z / 46.0) % 1
    rgb[(fx < 0.03) | (fz < 0.05)] = lime[0]
    rgb[(fz > 0.93)] = rgb[(fz > 0.93)] * 0.7 + lime[4] * 0.3
    nose = Z > Z_EDGE - 10
    rgb[nose] = lime[4]
    rgb[Z > Z_EDGE - 3] = lime[5]
    # door light from behind the camera, moonlight laid on the far half
    warm_light(rgb, np.hypot(X * 0.8, (Z - 150) * 1.3), 300, colour="#f6cf7a", strength=0.42)
    cool = np.clip((Z - 380) / 140, 0, 1)
    rgb[:] = rgb * (1 - 0.18 * cool[:, None]) + np.array(C("#9aa4d8")[:3]) * 0.18 * cool[:, None]
    for side in (-1, 1):
        warm_light(rgb, np.hypot(X - side * 300, (Z - 330) * 1.6), 120, colour="#f6cf7a", strength=0.3)
    return rgba_of(rgb)


def big_column(cv, x0, x1, top, base, lit_left=True):
    """A near column at screen scale between x0 and x1: Ionic capital under the architrave,
    fluted shaft with cylinder shading, torus and plinth at the floor."""
    w = x1 - x0
    pal = ["#3e3632", "#5a5048", "#7a6e60", "#948672", "#ac9c84", "#c8b89c", "#ded2b8"]
    ramp = [5, 6, 5, 5, 4, 4, 4, 3, 3, 3, 2, 2, 1]
    if not lit_left:
        ramp = ramp[::-1]
    s_top, s_bot = top + 14, base - 14
    for i in range(w):
        c = pal[ramp[min(len(ramp) - 1, int(i / max(1, w - 1) * len(ramp)))]]
        cv.vline(x0 + i, s_top, s_bot - s_top, c)
    for i in range(3, w - 2, 5):
        cv.vline(x0 + i, s_top + 4, s_bot - s_top - 8, C("#0d0b16", 0.18))
        cv.vline(x0 + i + 1, s_top + 4, s_bot - s_top - 8, C("#ffffff", 0.05))
    for jy in range(s_bot - 40, s_top + 8, -40):
        cv.hline(x0, jy, w, C("#0d0b16", 0.16))
    cv.vline(x0 - 1, s_top, s_bot - s_top, OUT); cv.vline(x1, s_top, s_bot - s_top, OUT)
    # capital: necking, echinus, volutes, abacus
    cv.rect(x0 - 1, s_top - 3, w + 2, 3, pal[4]); cv.hline(x0 - 1, s_top - 3, w + 2, pal[6])
    cv.rect(x0 - 6, top + 5, w + 12, 6, pal[3]); cv.hline(x0 - 6, top + 5, w + 12, pal[5]); cv.hline(x0 - 6, top + 10, w + 12, pal[1])
    for vx in (x0 - 8, x1 + 1):
        cv.ellipse(vx, top + 4, 8, 9, OUT); cv.ellipse(vx + 1, top + 5, 6, 7, pal[4]); cv.ellipse(vx + 3, top + 7, 2, 3, pal[1])
    cv.rect(x0 - 9, top, w + 18, 5, pal[4]); cv.hline(x0 - 9, top, w + 18, pal[6]); cv.hline(x0 - 9, top + 4, w + 18, pal[2])
    # base
    cv.rect(x0 - 4, s_bot, w + 8, 5, pal[4]); cv.hline(x0 - 4, s_bot, w + 8, pal[6]); cv.hline(x0 - 4, s_bot + 4, w + 8, pal[1])
    cv.rect(x0 - 7, s_bot + 5, w + 14, 9, pal[3]); cv.hline(x0 - 7, s_bot + 5, w + 14, pal[5]); cv.hline(x0 - 7, base - 1, w + 14, pal[0])


def architrave(cv, y0=0, h=16):
    """The portico's architrave seen from beneath: inner fascia, dentils, the soffit's shadow."""
    pal = ["#2e2830", "#4a4040", "#5e544c", "#786c5e", "#948672", "#b0a28a"]
    cv.rect(0, y0, 640, h, pal[2])
    cv.hline(0, y0 + 3, 640, pal[3]); cv.hline(0, y0 + 6, 640, pal[1])
    cv.rect(0, y0 + 7, 640, 4, pal[3]); cv.hline(0, y0 + 7, 640, pal[4])
    for dx in range(0, 640, 6):
        cv.rect(dx, y0 + 11, 4, 3, pal[2]); cv.px(dx + 3, y0 + 13, pal[0])
    cv.hline(0, y0 + h - 2, 640, pal[1]); cv.hline(0, y0 + h - 1, 640, OUT)
    # coffers of the porch ceiling peeking above the fascia
    for cx in range(8, 640, 40):
        cv.rect(cx, y0, 24, 2, pal[1])


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    v = View(horizon=98, cam=52, fill="#141223")
    sky, stars = sky_strip()
    v.strip(sky, 0, solid=False)
    mts = mountains()
    v.strip(mts, 40)
    v.strip(treeline(), 98 - 29 + 4)
    v.ground(quad_shader, height=-DROP)

    # Quad pieces back to front: far trees, lamps, the planter, the two big oaks.
    rng = np.random.default_rng(7)
    items = []
    for (x, z, cell, hw) in [(-900, 2300, 6, 300), (980, 2200, 5, 300), (-560, 2000, 5, 260), (620, 1900, 6, 280),
                             (-470, 1320, 5, 280), (520, 1400, 5, 300)]:
        items.append((z, "tree", (x, cell, hw)))
    for (x, z) in LAMPS:
        items.append((z, "lamp", x))
    items.append((COURT[1] + 10, "maple", 0))
    glows = []
    for z, kind, data in sorted(items, key=lambda t: -t[0]):
        s = v.scale(z)
        if kind == "tree":
            x, cell, hw = data
            spr = sprite_from_cell(cell, height=int(round(hw * s)), colors=40, brightness=0.7, saturation=0.9)
            v.sprite(spr, x, z, Y=-DROP, scale=z / v.F)
        elif kind == "lamp":
            h = max(24, int(round(66 * 1.7 * s)))
            spr, ax, ay = lamp_post(h)
            sx, sy, _ = v.sprite(spr.a, data, z, Y=-DROP, anchor=(ax / spr.w, ay / spr.h), scale=z / v.F)
            glows.append([int(round(sx)), int(round(sy - ay + 11)), "fff0c4", 1])
        else:
            # the court's red maple in its low stone planter
            h = int(round(120 * 1.7 * s))
            spr = sprite_from_cell(5, height=h, colors=32, brightness=0.8)
            spr[..., :3] *= np.array([1.08, 0.82, 0.78], np.float32)
            v.sprite(spr, 0, z, Y=-DROP, scale=z / v.F)
            pw = int(round(180 * 1.7 * s)); ph = max(3, int(round(16 * 1.7 * s)))
            pl = Canvas(pw + 2, ph + 1)
            pl.rect(0, 0, pw + 2, ph + 1, OUT); pl.rect(1, 1, pw, ph - 1, LIME[2]); pl.hline(1, 1, pw, LIME[4])
            v.sprite(pl.a, 0, z + 1, Y=-DROP, scale=z / v.F)

    # The portico floor (drawn after the quad so the top step hides the ground below it).
    v.ground(portico_shader, y_from=v.ground_y(Z_EDGE) - 0.01)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # Crisp near pieces at 1:1: the architrave, the two framing columns and their lanterns.
    near_paint = Canvas(640, 360)
    architrave(near_paint, 0, 16)
    floor_y = int(round(v.ground_y(300)))
    big_column(near_paint, -4, 30, 16, floor_y + 6, lit_left=False)
    big_column(near_paint, 610, 644, 16, floor_y + 6, lit_left=True)
    lanterns = []
    for (lx, side) in [(44, 1)]:
        near_paint.rect(lx - side * 9 - 1, 62, 10, 2, IRON[1])
        lantern_head(near_paint, lx, 56)
        for r, a in [(16, 0.05), (10, 0.08)]:
            near_paint.ellipse(lx - r, 66 - r, 2 * r + 1, 2 * r + 1, C("#f6cf7a", a))
        lanterns.append([lx, 66, "fff0c4", 2])
    # paper and leaves on the near portico floor
    for _ in range(36):
        lx, ly = int(rng.integers(40, 600)), int(rng.integers(136, 200))
        c = ["#c8682e", "#a83c32", "#d9a441", "#8c4a2a"][int(rng.integers(4))]
        near_paint.px(lx, ly, c); near_paint.px(lx + 1, ly, shade(c, -0.2))
    for (px_, py_) in [(150, 172), (452, 160), (530, 188)]:
        near_paint.rect(px_, py_, 7, 4, PAGE[3]); near_paint.hline(px_ + 1, py_ + 1, 5, PAGE[0]); near_paint.hline(px_, py_ + 4, 7, C("#0d0b16", 0.4))
    m = near_paint.a[..., 3:4]
    cv.a[..., :3] = near_paint.a[..., :3] * m + cv.a[..., :3] * (1 - m)

    solid = v.solid_mask() | (near_paint.a[..., 3] > 0.5)
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = solid.astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))
    cloud_strip(640, 48, count=5, seed=8, pal=NIGHT_CLOUD, sizes=(50, 110)).save(os.path.join(out, "battle-clouds.png"))
    res = f"res://assets/art/rooms/{ROOM}/"
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "drift", "depth": "far", "texture": res + "battle-clouds.png", "y": 18, "speed": 2.0},
            {"kind": "twinkle", "depth": "far", "points": stars, "rate": 0.9, "min": 0.0},
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "night_bat", "x": 90, "y": 40, "fly": 13.0, "rate": 7.0},
                {"kind": "night_bat", "x": 400, "y": 58, "fly": 10.0, "rate": 6.0}]},
            {"kind": "twinkle", "points": glows + lanterns, "rate": 1.6, "min": 0.5},
            {"kind": "fauna", "fauna": [{"kind": "loose_page", "x": 300, "y": 120, "fly": 7.0, "rate": 3.0}]},
            {"kind": "particles", "style": "leaf", "count": 12, "rect": [-20, 20, 680, 150], "speed": [22, 12]},
        ],
    }


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
