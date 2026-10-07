"""Battle backdrop for the CU Book Store (C02): the fight happens in the textbook aisle, looking down
it to the Buffs gear wall at the far end.

Black gondolas of glossy textbooks run back on both sides (department headers, white price strips,
yellow USED stickers, overstock cartons on top); above them the putty side walls carry TEXTBOOKS
fascias and buyback posters. The far wall is the gear wall painted at room scale: caps, face-out
hoodies in black, gold, heather and white round the gold buffalo plaque, GO BUFFS, the #1 jersey,
folded tees. Charcoal carpet tile with a gold edge strip, warm pools under the ceiling cans.
In the aisle: the bargain bin, a shopping basket, a dropped textbook.
Layers: AISLE 1 and AISLE 2 signs swinging on their chains, the cans breathing, dust in the light."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_eng import micro_text, micro_width
import c02_lib as L

ROOM = "C02"
INK = "#10121e"
F = 320.0
SC = 72 / 52                    # room-scale sprite -> battle world units
SHELF_X = 230.0                 # gondola faces either side of the aisle
WALL_X = 340.0                  # side walls behind the gondolas
Z_NEAR, Z_BACK = 190.0, 443.0   # gondolas run from here to the far (gear) wall; at Z_BACK 1 room px = 1 screen px
SHELF_H = 100.0
CEIL = 176.0
CANS = [(-100.0, z) for z in (250, 330, 410)] + [(100.0, z) for z in (250, 330, 410)]
FW = int(round(2 * WALL_X * F / Z_BACK))
FH = int(round(CEIL * F / Z_BACK))
FOG = "#2a2430"


def floor_shader(X, Z):
    """Charcoal carpet tile, quarter-turned ribs, a gold edge strip at the gondola bases, warm
    pools under the cans and a long glow from the lit gear wall."""
    tile = 26.0
    cx, cz = np.floor(X / tile), np.floor(Z / tile)
    fx, fz = X / tile - cx, Z / tile - cz
    p = pal_array(L.CARPET_S)
    vert = ((cx + cz) % 2) == 0
    rib = np.where(vert, np.mod(X, 3.0) < 1.0, np.mod(Z, 4.0) < 1.3)
    rgb = np.where(rib[:, None], p[1], p[2])
    rgb = np.where((hash2(cx, cz, 3) > 0.8)[:, None], rgb * 1.08, rgb)
    rgb = np.where(((fx < 0.03) | (fz < 0.02))[:, None], p[3], rgb)
    edge = (np.abs(X) > SHELF_X - 10) & (np.abs(X) < SHELF_X - 6)
    rgb = np.where(edge[:, None], pal_array([L.GOLD[2]])[0], rgb)
    for (cx_, cz_) in CANS:
        warm_light(rgb, np.hypot((X - cx_) * 1.0, (Z - cz_) * 1.2), 70, colour="#f6cf7a", strength=0.22)
    warm_light(rgb, np.hypot(X * 0.7, (Z - Z_BACK) * 1.1), 160, colour="#e6d29a", strength=0.2)
    out = rgba_of(np.clip(rgb, 0, 1))
    fog(out, Z, FOG, 380, 700, amount=0.35)
    return out


def ceiling_shader(X, Z):
    """Black ceiling with a faint panel grid and two rows of recessed cans."""
    b = pal_array(L.BLACK)
    rgb = np.repeat(b[2][None, :], X.shape[0], 0)
    grid = (np.abs(np.mod(X, 60.0) - 30) > 29.2) | (np.abs(np.mod(Z, 60.0) - 30) > 29.4)
    rgb = np.where(grid[:, None], b[1], rgb)
    for (cx_, cz_) in CANS:
        d = np.hypot(X - cx_, (Z - cz_) * 0.9)
        rgb = np.where((d < 9)[:, None], b[0], rgb)
        rgb = np.where((d < 6.5)[:, None], pal_array(["#fff0c4"])[0], rgb)
        warm_light(rgb, d, 34, colour="#f6cf7a", strength=0.2)
    out = rgba_of(rgb)
    fog(out, Z, FOG, 380, 700, amount=0.3)
    out[(Z > Z_BACK) | (np.abs(X) > WALL_X), 3] = 0
    return out


def side_wall_tex():
    """The putty side walls seen above the gondolas: a TEXTBOOKS fascia and buyback posters."""
    Lw, Hh = int(Z_BACK - 150), int(CEIL)
    cv = Canvas(Lw, Hh, seed=40)
    L.store_wall(cv, 0, 0, Lw, Hh, seed=41)
    y0 = Hh - int(SHELF_H) - 70
    for k, (u, title, col) in enumerate([(30, "BUYBACK", "#c8382c"), (150, "RENT", "#2a5aa8")]):
        cv.rect(u - 1, y0 - 1, 52, 40, OUT); cv.rect(u, y0, 50, 38, "#f2ecdc")
        cv.rect(u, y0, 50, 12, col)
        text(cv, title, u + 25 - text_width(title) // 2, y0 + 1, "#f6f4ee")
        for j in range(3):
            cv.hline(u + 6, y0 + 18 + j * 5, 38 - j * 8, "#7a7a8a")
    L.header_sign(cv, 245, y0 + 8, "TEXTBOOKS", rods=False)
    return cv.a


def back_wall():
    """The far wall at 1:1 room scale: the putty wall, the gear wall, an end bay of textbooks each side."""
    cv = Canvas(FW, FH, seed=50)
    L.store_wall(cv, 0, 0, FW, FH, seed=51)
    cx = FW // 2
    gw, gh = 300, 114
    L.gear_wall(cv, cx - gw // 2, FH - gh - 4, gw, gh, seed=7)
    for k in (-1, 1):                                           # end bays of textbooks beside it
        x0 = cx + k * (gw // 2 + 8) - (0 if k > 0 else 70)
        L.textbook_wall(cv, x0, FH - 96, 70, 92, depts=("MATH",) if k < 0 else ("ECON",), seed=60 + k)
    cv.rect(0, FH - 2, FW, 2, C(L.SHADOW, 0.5))
    return cv


def aisle_sign(label, chain=26, small=False):
    """A hanging black-and-gold aisle sign on two thin chains, crisp at screen size; the far one
    (small) is lettered in the tiny face."""
    w = (micro_width(label) + 10) if small else (text_width(label) + 16)
    h = 10 if small else 15
    cv = Canvas(w + 2, chain + h + 1, seed=3)
    for rx in (5, w - 4):
        for yy in range(0, chain, 3):
            cv.px(rx, yy, IRON[3]); cv.px(rx, yy + 1, IRON[1])
    cv.rect(0, chain, w + 2, h, OUT)
    cv.rect(1, chain + 1, w, h - 2, L.GOLD[2]); cv.rect(2, chain + 2, w - 2, h - 4, L.BLACK[1])
    cv.hline(2, chain + 2, w - 2, L.BLACK[4])
    if small:
        micro_text(cv, label, 1 + w // 2 - micro_width(label) // 2, chain + 3, L.GOLD[4])
    else:
        text(cv, label, 1 + w // 2 - text_width(label) // 2, chain + 3, L.GOLD[4])
    return cv


def basket(width=26, height=16):
    """A red store shopping basket on the carpet, handles folded down, two books inside."""
    cv = Canvas(width + 4, height + 6, seed=9)
    ox, base = 2, height + 3
    cv.rect(ox + 3, base - 2, width - 4, 2, C(L.SHADOW, 0.4))
    cv.rect(ox + 4, base - height + 2, 7, 5, L.TEXTBOOK[1]); cv.rect(ox + 12, base - height + 1, 6, 6, L.TEXTBOOK[3])
    cv.poly([(ox, base - height + 5), (ox + width, base - height + 5), (ox + width - 3, base), (ox + 3, base)], OUT)
    cv.poly([(ox + 1, base - height + 6), (ox + width - 1, base - height + 6), (ox + width - 4, base - 1), (ox + 4, base - 1)], "#c8382c")
    for gx in range(ox + 4, ox + width - 3, 3):
        cv.vline(gx, base - height + 8, height - 10, "#8a2424")
    cv.hline(ox + 1, base - height + 6, width - 2, "#e86a5a")
    cv.rect(ox + 2, base - height + 3, width - 4, 2, IRON[2])
    return cv, ox + width // 2, base


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#1a1420")
    v.ground(floor_shader)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=CEIL)
    flat = back_wall()
    fx0 = int(round(v.vx - FW / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - FH))
    v.strip(flat.a, fy0, fx0)
    # side walls above the gondolas
    wall = side_wall_tex()
    Lw = wall.shape[1]
    for side in (-1, 1):
        def shade_side(u, Y, Z, side=side):
            o = texture_lookup(wall, (Lw - 1 - u) if side < 0 else u, CEIL - Y, wrap=False)
            o[..., :3] *= 0.8 if side < 0 else 0.72
            fog(o, Z, FOG, 380, 700, amount=0.3)
            return o
        v.plane((side * WALL_X, Z_BACK), (side * WALL_X, 150.0), shade_side, y_max=CEIL)
    # the gondola fronts, overstock cartons along their tops
    Ls = int(Z_BACK - Z_NEAR)
    for side in (-1, 1):
        tex = L.shelf_tex(Ls, int(SHELF_H) + 22, seed=5 + side)
        def shade_shelf(u, Y, Z, tex=tex, side=side):
            uu = u if side < 0 else Ls - 1 - u
            o = texture_lookup(tex, uu, SHELF_H + 22 - Y, wrap=False)
            o[..., :3] *= 0.95 if side < 0 else 0.84
            fog(o, Z, FOG, 380, 700, amount=0.3)
            return o
        v.plane((side * SHELF_X, Z_NEAR), (side * SHELF_X, Z_BACK), shade_shelf, y_max=SHELF_H + 22)
    # things in the aisle (room-scale sprites)
    for (made, X, Z) in [(L.bargain_bin(58, 34, seed=12), -120, 420),
                         (basket(26, 16), 30, 372),
                         (L.plush_bin(50, 38, seed=5), 150, 430)]:
        s_, ax_, ay_ = made[:3]
        v.sprite(s_.a, X, Z, anchor=(ax_ / s_.w, ay_ / s_.h), scale=SC)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    # a dropped textbook on the carpet, crisp
    bx, by = v.project(-40, 0, 300)
    bx, by = int(round(bx)), int(round(by))
    cv.rect(bx - 1, by - 4, 16, 6, OUT); cv.rect(bx, by - 3, 14, 4, L.TEXTBOOK[0]); cv.hline(bx, by - 3, 14, shade(L.TEXTBOOK[0], 0.3))
    cv.rect(bx + 11, by - 3, 3, 4, "#e6d6b1")
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    # the hanging aisle signs, painted crisp at screen size, swinging a pixel either way
    for (label, cx, chain, phase, small) in [("AISLE 2", 268, 36, "2101", True), ("AISLE 1", 190, 20, "0121", False)]:
        sign = aisle_sign(label, chain=chain, small=small)
        for k, dx in enumerate((-1, 0, 1)):
            name = f"battle-sign-{label[-1]}-{k}.png"
            sign.save(os.path.join(out, name))
            layers.append({"kind": "blink", "pattern": "".join("1" if int(c) == k else "0" for c in phase), "rate": 1.6,
                           "texture": res + name, "x": cx - sign.w // 2 + dx, "y": 0})
    pts = []
    for (cx_, cz_) in CANS:
        px_, py_ = v.project(cx_, CEIL, cz_)
        pts.append([int(round(px_)), int(round(py_)), "fff0c4", 1])
    layers += [
        {"kind": "twinkle", "points": pts, "rate": 0.8, "min": 0.7},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [140, 20, 360, 120], "speed": [1, 3], "color": "f6e8c0"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
