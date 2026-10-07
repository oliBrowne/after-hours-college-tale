"""Battle backdrop for lost property (U07): the fight happens in the aisle between two towering walls
of pigeonholes, every hole holding something nobody came back for, each with its kraft tag. The
aisle runs to the claim hatch at the far end, lit warm under LOST PROPERTY, where a motorised coat
rail carries unclaimed coats slowly past the window (a drift layer seen through a hole in the near
image). Green enamel pendants hang over the aisle; the shelves fall into shadow toward the floor so
the party reads against them; NOW SERVING ticks over on the left."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from interior import PANEL
from props import OUT, IRON
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_umc import (OCHRE, KRAFT, PAPER, BRASS, SHADOW, ITEM_COLOURS, ITEM_KINDS, lost_item, claim_tag,
                     claim_hatch, now_serving, ochre_wall, halo)

INK = "#10121e"
Z_NEAR = 200.0
Z_BACK = 720.0
AISLE_X = 230.0
SHELF_H = 210.0
CEIL = 250.0
PENDANTS = [(-100.0, 420.0), (100.0, 560.0)]


def floor_shader(X, Z):
    """The room's worn linoleum: two close tans in a checker, an oxblood band along the shelves, a
    pale path walked up the middle to the hatch, pools under the pendants."""
    tile = 26.0
    cx, cz = np.floor(X / tile), np.floor(Z / tile)
    fx, fz = X / tile - cx, Z / tile - cz
    light = pal_array(["#937660"])[0]; dark = pal_array(["#866a56"])[0]
    ox = pal_array(["#74463c"])[0]; ox2 = pal_array(["#84524a"])[0]
    chk = ((cx + cz) % 2 == 0)[:, None]
    rgb = np.where(chk, light, dark).astype(np.float32)
    tone = hash2(cx, cz, 4)
    rgb = rgb * (0.96 + 0.06 * tone[:, None])
    spare = hash2(cx, cz, 9) > 0.96
    rgb[spare] = pal_array(["#9e8266"])[0]
    band = np.abs(X) > AISLE_X - 34
    rgb[band] = np.where(chk[band], ox, ox2)
    rgb[(np.abs(X) > AISLE_X - 38) & (np.abs(X) <= AISLE_X - 34)] = pal_array(["#b0957a"])[0]
    rgb[(fx < 0.04) | (fz < 0.04)] *= 0.86
    # worn path
    worn = np.abs(X + 6 * np.sin(Z / 40.0)) < 40
    rgb[worn] = rgb[worn] * 0.9 + pal_array(["#d8c0a0"])[0] * 0.1
    # a few tickets and a lost mitten on the floor
    for (tx, tz, c) in [(-60, 380, "#f6ecd2"), (40, 460, "#f6ecd2"), (110, 350, "#f6ecd2"), (-120, 520, "#c47a2c")]:
        m = (np.abs(X - tx) < 5) & (np.abs(Z - tz) < 3)
        rgb[m] = pal_array([c])[0]
    rgb *= np.array([0.86, 0.8, 0.76], np.float32)
    for (px, pz) in PENDANTS:
        warm_light(rgb, np.hypot(X - px, (Z - pz) * 1.6), 150, colour="#f6cf7a", strength=0.3)
    warm_light(rgb, np.hypot(X * 1.6, (Z - Z_BACK) * 0.5), 120, colour="#ffd890", strength=0.3)
    # shadow at the foot of the shelves
    sh = np.clip((np.abs(X) - (AISLE_X - 60)) / 60, 0, 1)
    rgb *= (1 - 0.35 * sh)[:, None]
    out = rgba_of(rgb)
    fog(out, Z, "#20161c", 560, 860, amount=0.45)
    return out


def shelf_face(left, seed=0):
    """A towering wall of pigeonholes along the aisle, laid out as seen on screen. Painted at half
    resolution and doubled, so the lost things read as chunky shapes at battle scale. Upper rows lit
    by the shelf lights, lower rows in shadow behind the party."""
    L, Hh = int(Z_BACK - Z_NEAR), int(CEIL)
    l, hh = L // 2, Hh // 2
    rng = np.random.default_rng(seed)
    cv = Canvas(l, hh, seed=seed)
    cv.rect(0, 0, l, hh, "#120c12")
    top = hh - int(SHELF_H) // 2
    cw, rh = 21, 19
    # boxes and bags piled on the shelf tops
    x = 1
    while x < l - 16:
        bw, bh = int(rng.integers(10, 18)), int(rng.integers(5, 11))
        c = KRAFT[int(rng.integers(1, 4))]
        cv.rect(x, top - bh, bw, bh, OUT); cv.rect(x + 1, top - bh + 1, bw - 2, bh - 1, c); cv.hline(x + 1, top - bh + 1, bw - 2, shade(c, 0.15))
        if rng.random() < 0.4:
            cv.rect(x + bw // 2 - 3, top - bh + 2, 6, 3, PAPER[2])
        x += bw + int(rng.integers(0, 4))
    cv.rect(0, top, l, hh - top, PANEL[1])
    nrows = (hh - top - 5) // rh
    for r in range(nrows):
        y0 = top + 3 + r * rh
        for c in range(l // cw + 1):
            x0 = c * cw + 2
            if x0 + cw - 3 > l:
                break
            cv.rect(x0, y0, cw - 3, rh - 4, mix(PANEL[1], PANEL[2], 0.5))
            cv.rect(x0, y0, cw - 3, 2, PANEL[0]); cv.vline(x0 + cw - 4, y0, rh - 4, PANEL[1])
            if rng.random() < 0.92:
                kind = ITEM_KINDS[int(rng.integers(len(ITEM_KINDS)))]
                lost_item(cv, kind, x0 + (cw - 3) // 2 + int(rng.integers(-1, 2)), y0 + rh - 4, rng)
            cv.rect(x0 - 2, y0 + rh - 4, cw, 3, PANEL[3]); cv.hline(x0 - 2, y0 + rh - 4, cw, PANEL[5])
            if rng.random() < 0.7:
                claim_tag(cv, x0 + cw - 7, y0 + rh - 2)
    for c in range(0, l, cw * 3):
        cv.rect(c, top, 2, hh - top, PANEL[2]); cv.vline(c, top, hh - top, PANEL[4])
    cv.rect(0, top - 1, l, 2, PANEL[3]); cv.hline(0, top - 1, l, PANEL[5])
    cv.rect(0, hh - 4, l, 4, PANEL[1]); cv.hline(0, hh - 4, l, PANEL[2])
    a = np.repeat(np.repeat(cv.a, 2, 0), 2, 1)
    # lighting: lit band near the top, falling into shadow toward the floor (stepped)
    rows = np.arange(a.shape[0])[:, None]
    t = np.clip((rows - top * 2) / SHELF_H, 0, 1)
    dim = np.where(t < 0.4, 1.1, np.where(t < 0.6, 0.9, np.where(t < 0.8, 0.74, 0.6)))
    a[..., :3] = np.clip(a[..., :3] * dim[..., None], 0, 1)
    return a


def back_wall():
    """The far end at its on-screen size: ochre wall over the wainscot, LOST PROPERTY across the
    top, the claim hatch with its shutter rolled up and the office lit behind, NOW SERVING to the
    left. Returns the hatch window (the hole the coats pass behind) and the digit box."""
    s = 320.0 / Z_BACK
    W = int(round(2 * AISLE_X * s)) + 2
    Hh = int(round(CEIL * s))
    cv = Canvas(W, Hh, seed=5)
    ochre_wall(cv, 0, 0, W, Hh, seed=5)
    cv.rect(0, Hh - 16, W, 16, PANEL[2]); cv.hline(0, Hh - 16, W, PANEL[4]); cv.rect(0, Hh - 3, W, 3, PANEL[1])
    cx = W // 2
    # LOST PROPERTY
    label = "LOST PROPERTY"
    sw = text_width(label) + 12
    cv.rect(cx - sw // 2 - 1, 12, sw + 2, 15, OUT); cv.rect(cx - sw // 2, 13, sw, 13, BRASS[2])
    cv.rect(cx - sw // 2 + 2, 15, sw - 4, 9, "#7e3a30")
    text(cv, label, cx - text_width(label) // 2, 14, PAPER[3])
    # the hatch, wide, shutter rolled up
    hw, hh, htop = 76, 40, 50
    claim_hatch(cv, cx, htop, hw, hh, shutter=0.12)
    win = (cx - hw // 2, htop + 6, hw, hh - 8)   # where the coat rail shows
    digits = now_serving(cv, 6, 50, "07")
    text(cv, "TAKE A", 8, 78, PAPER[2]); text(cv, "NUMBER", 8, 88, PAPER[2])
    return cv, win, digits


def coat_strip(width, height, seed=0):
    """A tileable strip of unclaimed coats on hangers from a rail (the conveyor behind the hatch)."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width, height, seed=seed)
    cv.rect(0, 2, width, 2, IRON[3]); cv.hline(0, 2, width, IRON[4])
    x = 4
    while x < width - 14:
        col = ITEM_COLOURS[int(rng.integers(len(ITEM_COLOURS)))]
        L = int(rng.integers(height - 12, height - 2))
        cv.line(x, 4, x, 7, IRON[4])
        cv.line(x - 6, 10, x, 6, IRON[3]); cv.line(x + 6, 10, x, 6, IRON[3])
        cv.poly([(x - 7, 9), (x + 7, 9), (x + 9, L), (x - 9, L)], OUT)
        cv.poly([(x - 6, 10), (x + 6, 10), (x + 8, L - 1), (x - 8, L - 1)], col)
        cv.poly([(x - 6, 10), (x - 1, 10), (x - 3, L - 1), (x - 8, L - 1)], shade(col, 0.15))
        cv.vline(x, 11, L - 12, shade(col, -0.3))
        cv.rect(x + 2, 16, 4, 6, KRAFT[4]); cv.px(x + 3, 18, "#7e3a30")
        x += int(rng.integers(14, 19))
    return cv


def pendant():
    w, h = 24, 120
    cv = Canvas(w, h)
    cx = w // 2
    cv.vline(cx, 0, h - 12, "#2a2630")
    cv.poly([(cx - 3, h - 13), (cx + 3, h - 13), (cx + 10, h - 4), (cx - 10, h - 4)], OUT)
    cv.poly([(cx - 2, h - 12), (cx + 2, h - 12), (cx + 9, h - 5), (cx - 9, h - 5)], "#3e6663")
    cv.poly([(cx - 2, h - 12), (cx, h - 12), (cx - 3, h - 5), (cx - 9, h - 5)], "#5a8a84")
    cv.rect(cx - 10, h - 4, 21, 1, "#2c4a4c")
    cv.rect(cx - 5, h - 3, 11, 3, "#fff0c4")
    return cv


def build(project):
    out = os.path.join(project, "assets/art/rooms/U07")
    v = View(horizon=98, cam=52, fill="#0e0a10")
    v.ground(floor_shader)
    L = int(Z_BACK - Z_NEAR)
    for side in (-1, 1):
        tex = shelf_face(side < 0, seed=11 if side < 0 else 12)

        def shade_wall(u, Y, Z, tex=tex, side=side):
            o = texture_lookup(tex, u if side < 0 else L - 1 - u, CEIL - Y, wrap=False)
            fog(o, Z, "#20161c", 560, 860, amount=0.3)
            return o
        v.plane((side * AISLE_X, Z_NEAR), (side * AISLE_X, Z_BACK), shade_wall, y_max=CEIL)
    flat, win, digits = back_wall()
    fx0 = int(round(v.vx - flat.w / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - flat.h))
    v.strip(flat.a, fy0, fx0)
    pend = []
    for (X, Z) in PENDANTS:
        spr = pendant()
        sx, sy, sc = v.sprite(spr.a, X, Z, Y=CEIL, anchor=(0.5, 0.0), scale=1.0)
        pend.append((int(round(sx)), int(round(sy + 118 * sc))))
    v.rows(0, 10, "#0a080c", 0.6, 0.0)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    # the near image is the same frame with the hatch window cut out, so the coat rail drifts
    # past behind the counter
    wx, wy, ww, wh = fx0 + win[0], fy0 + win[1], win[2], win[3]
    near = Canvas(cv.w, cv.h)
    near.a = cv.a.copy()
    near.a[wy:wy + wh, wx:wx + ww, 3] = 0
    near.save(os.path.join(out, "battle-near.png"))
    strip = coat_strip(160, wh + 2, seed=3)
    strip.save(os.path.join(out, "battle-coats.png"))
    t08 = Canvas(digits[2], digits[3])
    t08.rect(0, 0, digits[2], digits[3], "#140a10")
    text(t08, "08", 11, 0, "#ff5a4a")
    t08.save(os.path.join(out, "battle-now-08.png"))
    res = "res://assets/art/rooms/U07/"
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "drift", "texture": res + "battle-coats.png", "y": wy - 1, "speed": 7, "alpha": 1.0, "depth": "far"},
            {"kind": "blink", "pattern": "0000000011111111", "rate": 0.8, "texture": res + "battle-now-08.png",
             "x": fx0 + digits[0], "y": fy0 + digits[1]},
            {"kind": "twinkle", "points": [[x, y, "fff0c4", 2] for (x, y) in pend], "rate": 1.1, "min": 0.7},
            {"kind": "particles", "style": "dust", "count": 22, "rect": [220, 30, 200, 110], "speed": [0, 3], "color": "f6e0b0"},
        ],
    }


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
