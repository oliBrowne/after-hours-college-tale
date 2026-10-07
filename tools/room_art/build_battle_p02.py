"""Battle backdrop for the Pearl Street break room (P02): the fight happens on the pine floor between
the beanbag and the high-top, looking at the kitchenette. On the far wall: the kombucha kegerator
under its chalk ON TAP menu, the subway-tiled counter with the sink and espresso machine, the back
window over the alley with the Flatirons black against the last of the sky, shelves of mugs, and
the sticker fridge. Down the left wall the snack wall of gravity bins under the GOOD VIBES neon;
down the right wall the doorway back to the office (pink neon glow), the four bins and a
letterboard. Joists and the duct overhead. Layers: the neon O flickering, bubbles in the tap
tower, stars over the mesa, crumbs of dust in the counter light."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_umc import halo, soft_ellipse
import p01_lib as L

ROOM = "P02"
INK = "#10121e"
F = 320.0
SC = 72 / 52
WALL_X = 230.0
Z_NEAR, Z_BACK = 180.0, 470.0
CEIL = 170.0
FW = int(round(2 * WALL_X * F / Z_BACK))
FH = int(round(CEIL * F / Z_BACK))


def floor_shader(X, Z):
    """Pine boards toward the counter, a round jute rug under the beanbag, warm pools from the counter
    lights and the mint of the neon on the left."""
    plank = 11.0
    col = np.floor(X / plank)
    fx = X / plank - col
    length = 90 + 70 * hash2(col, 13)
    off = hash2(col, 15) * length
    seg = np.floor((Z + off) / length)
    fz = (Z + off) / length - seg
    tone = hash2(col, seg, 17)
    pine = pal_array(L.PINE)
    k = np.clip((3 + tone * 3.99).astype(int), 3, 6)
    rgb = pine[k] * 0.92
    grain = hash2(np.floor(X / 2.0), np.floor(Z / 7.0), 19)
    rgb = rgb * (0.93 + 0.09 * grain[:, None])
    rgb[fx < 0.09] = pine[1]
    rgb[fz < 0.012] = pine[1]
    # jute rug: concentric braided bands
    r = np.hypot((X + 150) / 110.0, (Z - 330) / 60.0)
    jute = pal_array(["#6a5236", "#9a7a4e", "#b0905c", "#8e6e44", "#a88a58", "#c0a06a"])
    band = np.clip((r * 6).astype(int), 0, 5)
    rgb = np.where((r < 1.0)[:, None], jute[5 - band] * 0.95, rgb)
    rgb = np.where((np.abs(r - 1.0) < 0.03)[:, None], jute[0] * 0.8, rgb)
    warm_light(rgb, np.hypot(X * 0.9, (Z - Z_BACK) * 1.8), 200, colour="#f6e0b0", strength=0.3)
    warm_light(rgb, np.hypot((X + WALL_X) * 1.2, (Z - 380) * 1.2), 120, colour="#8ef0c8", strength=0.16)
    out = rgba_of(rgb)
    fog(out, Z, "#2a1e26", 420, 700, amount=0.35)
    return out


def ceiling_shader(X, Z):
    t = pal_array(L.TIMBER)
    d = pal_array(L.DUCT)
    jz = np.mod(Z, 44.0)
    rgb = np.where((jz < 8)[:, None], t[3], t[1])
    rgb = np.where(((jz >= 8) & (jz < 9))[:, None], t[0], rgb)
    rgb = np.where((np.mod(X, 13.0) < 1.0)[:, None] & (jz >= 9)[:, None], t[0], rgb)
    duct = np.abs(X - 60) < 13
    seam = np.mod(Z + (X - 60) * 0.4, 8.0) < 1.2
    dt = np.where((np.abs(X - 60) < 4)[:, None], d[4], np.where((np.abs(X - 60) < 9)[:, None], d[3], d[2]))
    rgb = np.where(duct[:, None], np.where(seam[:, None], d[1], dt), rgb)
    out = rgba_of(rgb)
    fog(out, Z, "#1a1418", 380, 650, amount=0.45)
    return out


def left_wall_tex():
    """Snack wall under the GOOD VIBES neon, along the left (u = depth from Z_NEAR)."""
    Lw, Hh = int(Z_BACK - Z_NEAR), int(CEIL)
    cv = Canvas(Lw, Hh, seed=61)
    L.brick_wall_p(cv, 0, 0, Lw, Hh, seed=62)
    L.baseboard(cv, 0, Hh, Lw)
    L.snack_wall(cv, 100, Hh - 116, 150, 98, seed=63)
    L.neon_text(cv, "GOOD VIBES", 142, Hh - 150, L.NEON_MINT, scale=1)
    L.thermostat(cv, 266, Hh - 80)
    L.thermostat(cv, 40, Hh - 84)
    return cv.a


def right_wall_tex():
    """The doorway back to the office, the bins, a letterboard, along the right."""
    Lw, Hh = int(Z_BACK - Z_NEAR), int(CEIL)
    cv = Canvas(Lw, Hh, seed=71)
    L.brick_wall_p(cv, 0, 0, Lw, Hh, seed=72)
    L.baseboard(cv, 0, Hh, Lw)
    L.letterboard(cv, 110, Hh - 120, ["EVERY DAY", "IS FRIDAY", "(IT IS", "TUESDAY)"], w=56)
    L.waste_bins(cv, 112, Hh)
    L.office_glimpse(cv, 226, Hh, w=46, h=74)
    return cv.a


def back_wall():
    """The kitchenette wall at its on-screen size."""
    cv = Canvas(FW, FH, seed=81)
    L.brick_wall_p(cv, 0, 0, FW, FH, seed=82)
    cv.hline(0, 0, FW, C(L.SHADOW, 0.35))
    L.baseboard(cv, 0, FH, FW)
    cx0, cw = 92, 136
    L.subway_tile(cv, cx0, FH - 70, cw, 36)
    view = L.flatirons_view(40, 70, seed=6)
    L.arched_window(cv, cx0 + 64, FH - 106, 40, 56, view, 0, seed=7)
    L.counter_run(cv, cx0, FH, cw, seed=8, shelf_from=86)
    L.chalk_menu(cv, 20, FH - 108, 56, 40)
    L.kegerator(cv, 48, FH, w=48, h=56)
    L.sticker_fridge(cv, FW - 44, FH, 42, 92, seed=5)
    stars = [(cx0 + 64 - 14 + k * 7, FH - 108 + (k * 5) % 11) for k in range(5)]
    return cv, (cx0 + 64, FH - 106), stars


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#1a1420")
    v.ground(floor_shader)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=CEIL)
    flat, win, stars = back_wall()
    fx0 = int(round(v.vx - FW / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - FH))
    v.strip(flat.a, fy0, fx0)
    ltex, rtex = left_wall_tex(), right_wall_tex()
    Lw = ltex.shape[1]

    def shade_left(u, Y, Z):
        o = texture_lookup(ltex, u, CEIL - Y, wrap=False)
        o[..., :3] *= 0.84
        fog(o, Z, "#2a1e26", 420, 700, amount=0.3)
        return o

    def shade_right(u, Y, Z):
        o = texture_lookup(rtex, Lw - 1 - u, CEIL - Y, wrap=False)
        o[..., :3] *= 0.74
        fog(o, Z, "#2a1e26", 420, 700, amount=0.3)
        return o
    v.plane((-WALL_X, Z_NEAR), (-WALL_X, Z_BACK), shade_left, y_max=CEIL)
    v.plane((WALL_X, Z_NEAR), (WALL_X, Z_BACK), shade_right, y_max=CEIL)
    for (made, X, Z) in sorted([(L.high_top(72, 52, seed=2), 150, 440), (L.dog_bed(44, 22, seed=3), 196, 455),
                                (L.beanbag_big(54, 40, seed=1), -175, 455), (L.kegs(40, 32, seed=4), -60, 460)],
                               key=lambda t: -t[2]):
        s_, ax_, ay_ = made[:3]
        v.sprite(s_.a, X, Z, anchor=(ax_ / s_.w, ay_ / s_.h), scale=SC)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    cv.save(os.path.join(out, "battle-far.png"))

    # the neon O on the left wall: project the letter's texel box
    ox_, oy_ = v.project(-WALL_X, CEIL - (CEIL - 150) - 1, Z_NEAR + 149)
    ox2, oy2 = v.project(-WALL_X, CEIL - (CEIL - 150) - 9, Z_NEAR + 155)
    tap = [fx0 + 48 - 12 + k * 12 for k in range(3)]
    layers = [
        {"kind": "blink", "pattern": "1111111111111111111111111111110101111111111111", "rate": 9.0,
         "rects": [[int(min(ox_, ox2)), int(min(oy_, oy2)), max(2, int(abs(ox2 - ox_)) + 1), max(2, int(abs(oy2 - oy_)) + 1), "1e3a30", 0.7]]},
        {"kind": "twinkle", "points": [[fx0 + x, fy0 + y, "c8c8e8", 1] for (x, y) in stars], "rate": 1.5, "min": 0.0},
        {"kind": "twinkle", "points": [[x, fy0 + FH - 66, "f2ecdc", 1] for x in tap], "rate": 1.8, "min": 0.6},
        {"kind": "particles", "style": "dust", "count": 8, "rect": [fx0 + 34, fy0 + FH - 64, 28, 26], "speed": [0, -4], "color": "f6d68a"},
        {"kind": "particles", "style": "dust", "count": 14, "rect": [200, 40, 240, 100], "speed": [1, 2], "color": "fff0c4"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
