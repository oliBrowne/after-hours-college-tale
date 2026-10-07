"""Battle backdrop for the closed archive (N06): INDEX's hall of possible lives.

Behind the fighters a wall of card-index drawers runs floor to cornice, a few drawers pulled out
and bristling with cards. In the middle it opens into a long gallery, its walls drawers too, where
rows of oak ceremony chairs - roped with a red sash, a RESERVED card on every back - wait on both
sides of a crimson aisle for a ceremony that never starts. At the far end the closed archive's
lattice grille glows faintly, chained shut; the enamelled board POSSIBLE LIVES / CLOSED ARCHIVE
hangs over the aisle on chains from a coffered ceiling, green-shaded pendants above the chairs.
A brass catalogue rose is let into the floor where INDEX stands. Drawers slide out and back,
index cards drift down through the lamplight, the lamps breathe."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON
from lib_norlin import stone_wall, shade_pendant, ceiling_band, OAK, OAK_DARK, BRASS, PAGE, GILT, STONE_N, LIME, LAMP_GREEN
from lib_norlin2 import (index_wall, index_wall_slots, drawer_out, archive_cage, two_line_plaque, chair_row_back,
                         VAULT, SASH)
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup, ROOM_TO_BATTLE

ROOM = "N06"
INK = "#10121e"
HAZE = "#17131a"
Z_NEAR = 430.0            # the drawer wall behind the fighters
Z_END = 860.0             # the closed archive's grille wall
GAL = 150.0               # half width of the gallery
WALL_H = 172.0            # drawers up to the cornice
CEIL = 246.0              # coffered ceiling over the gallery
SIDE = 720.0              # how far the front drawer wall runs out sideways
CHAIR_ROWS = [500.0, 570.0, 640.0, 710.0, 780.0]
PENDANTS = [(-92.0, 520.0), (92.0, 520.0), (-92.0, 700.0), (92.0, 700.0)]
FRONT_LAMPS = [(-250.0, 372.0), (250.0, 372.0)]
ROSE = (173.0, 352.0)     # under INDEX
DW, DH = 12, 8            # drawer size in world units (about 9 x 6 px on the near wall)


def floor_shader(X, Z):
    """Chequered stone flags, the crimson aisle between the chair rows, the brass rose under INDEX,
    lamp pools."""
    v = pal_array(VAULT)
    size = 40.0
    i, j = np.floor(X / size), np.floor(Z / size)
    t = hash2(i, j, 4)
    rgb = np.where(((i + j) % 2 == 0)[:, None], v[3], v[4]) * (0.95 + 0.1 * t[:, None])
    gx, gz = (X / size) % 1, (Z / size) % 1
    rgb[(gx < 0.04) | (gz < 0.05)] = v[1]
    grain = hash2(np.floor(X / 3), np.floor(Z / 4), 9) > 0.88
    rgb[grain] *= 0.94
    # the aisle runner
    red = pal_array(["#1e0e12", "#3a141a", "#5a1a22", "#7a2a2e", "#c0884a", "#e0b26a"])
    ax = np.abs(X)
    run = (ax < 34) & (Z > Z_NEAR - 30) & (Z < Z_END)
    rgb[run] = red[2]
    rgb[run & (ax > 29)] = red[1]
    rgb[run & (np.abs(ax - 26) < 1.3)] = red[4]
    lz = (Z % 46.0) - 23
    rgb[run & (ax + np.abs(lz) * 0.8 < 12)] = red[3]
    rgb[run & (ax + np.abs(lz) * 0.8 < 3)] = red[5]
    # brass catalogue rose under INDEX
    rx, rz = ROSE
    d = np.hypot((X - rx) / 1.0, (Z - rz) * 1.25)
    brass = pal_array(BRASS)
    rgb[np.abs(d - 70) < 2.2] = brass[2]
    rgb[np.abs(d - 60) < 1.4] = brass[1]
    ang = np.arctan2((Z - rz) * 1.25, X - rx)
    ticks = (d > 60) & (d < 70) & (np.abs(((ang / (2 * np.pi) * 24) % 1) - 0.5) > 0.42)
    rgb[ticks] = brass[2]
    for (lx, lz_) in PENDANTS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz_) * 0.7), 150, strength=0.3)
    for (lx, lz_) in FRONT_LAMPS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz_) * 0.8), 170, strength=0.3)
    warm_light(rgb, np.hypot(X, (Z - Z_END) * 0.6), 110, strength=0.22)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 600, 1200, amount=0.5)
    return out


def ceiling_shader(X, Z):
    """Coffered oak ceiling over the gallery: deep beams across and along, dark panels."""
    rgb = np.zeros((X.shape[0], 3), np.float32)
    rgb[:] = np.array(C(OAK_DARK[2])[:3])
    cx, cz = (X / 50.0 + 0.5) % 1, (Z / 70.0) % 1
    panel = (cx > 0.16) & (cz > 0.16)
    rgb[panel] = np.array(C(OAK_DARK[1])[:3])
    rgb[panel & (cx < 0.24)] = np.array(C(OAK_DARK[3])[:3])
    rgb[~panel & ((cx < 0.06) | (cz < 0.06))] = np.array(C(OAK[3])[:3])
    rgb[(cz > 0.16) & (cz < 0.2) & panel] = np.array(C("#7a3646")[:3])
    for (lx, lz) in PENDANTS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.8), 90, strength=0.3)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 500, 1100, amount=0.6)
    return out


def drawer_texture(length, height, seed=0, dim=0.0):
    """A card-index wall laid flat: cornice, banks of drawers between oak stiles, a plinth."""
    cv = Canvas(length, height + 12, seed=seed)
    cv.rect(0, 0, length, height + 12, OAK[2])
    index_wall(cv, 4, 10, length - 8, height + 12, seed=seed, dw=DW, dh=DH, open_rate=0.025)
    if dim:
        cv.a[..., :3] *= (1 - dim)
    return cv.a


def far_wall(Wp, Hp):
    """The grille wall at the end of the gallery, at its on-screen size: dark sandstone, the
    closed archive's lattice and stone surround, chained shut."""
    cv = Canvas(Wp, Hp, seed=3)
    stone_wall(cv, 0, 0, Wp, Hp, pal=[shade(c, -0.3) for c in STONE_N], seed=12, course=4)
    gw = int(Wp * 0.62)
    archive_cage(cv, Wp // 2 - gw // 2, int(Hp * 0.3), gw, Hp, seed=5)
    cv.a[..., :3] *= 0.92
    return cv


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    v = View(horizon=98, cam=52, fill="#0e0c12")
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=CEIL, z_max=Z_END)
    v.ground(floor_shader, z_max=Z_END)
    # far wall
    s = v.scale(Z_END)
    Wp = int(round(2 * GAL * s)) + 2
    Hp = int(round(CEIL * s))
    fw = far_wall(Wp, Hp)
    v.strip(fw.a, int(round(v.ground_y(Z_END) - Hp)), int(round(v.vx - Wp / 2)))
    # gallery side walls: drawers to the cornice, stone above
    side_tex = drawer_texture(int(Z_END - Z_NEAR) + 20, int(WALL_H), seed=21)
    stone = Canvas(400, 80, seed=4)
    stone_wall(stone, 0, 0, 400, 80, pal=[shade(c, -0.2) for c in STONE_N], seed=14, course=6)
    for side in (-1, 1):
        def shade_side(u, Y, Z, side=side):
            o = texture_lookup(side_tex, u, WALL_H + 12 - Y, wrap=False)
            up = Y > WALL_H + 10
            if up.any():
                o[up] = texture_lookup(stone.a, u[up], CEIL - Y[up], wrap=True)
            o[..., :3] *= 0.84 if side < 0 else 0.76
            for (lx, lz) in PENDANTS:
                warm_light(o[..., :3], np.hypot((Z - lz) * 0.9, (Y - 140) * 0.9), 120, strength=0.32)
            return fog(o, Z, HAZE, 600, 1200, amount=0.5)
        v.plane((side * GAL, Z_NEAR), (side * GAL, Z_END), shade_side, y_max=CEIL)
    # the chair rows, far to near, either side of the aisle
    row = chair_row_back(3, 18, seed=2)
    for z in sorted(CHAIR_ROWS, reverse=True):
        for side in (-1, 1):
            v.sprite(row.a, side * (40 + row.w * ROOM_TO_BATTLE / 2), z, scale=ROOM_TO_BATTLE)
    # the front drawer wall behind the fighters, either side of the gallery mouth
    front_tex = drawer_texture(int(SIDE), int(WALL_H), seed=31, dim=0.12)
    upper = Canvas(1440, 140, seed=5)
    stone_wall(upper, 0, 0, 1440, 140, pal=[shade(c, -0.1) for c in STONE_N], seed=16, course=6)
    def front(X, Y):
        o = np.zeros(X.shape + (4,), np.float32)
        low = Y <= WALL_H + 12
        u = np.abs(X) - GAL
        o[low] = texture_lookup(front_tex, u[low] if True else u[low], WALL_H + 12 - Y[low], wrap=False)
        o[~low] = texture_lookup(upper.a, X[~low] + 720, 400 - Y[~low], wrap=True)
        o[..., 3] = 1
        for (lx, lz) in FRONT_LAMPS:
            warm_light(o[..., :3], np.hypot(X - lx, (Y - 150) * 1.1), 200, strength=0.26)
        o[..., :3] *= 0.92
        return o
    v.back(Z_NEAR, front, region=lambda X, Y: (np.abs(X) > GAL) & (Y >= 0))
    # the lintel over the gallery mouth
    v.back(Z_NEAR, lambda X, Y: texture_lookup(upper.a, X + 720, 400 - Y, wrap=True),
           region=lambda X, Y: (np.abs(X) <= GAL) & (Y > CEIL - 4))
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # Crisp pieces at 1:1: the gallery mouth's oak frame, pendants, the hung board, front lamps.
    glows = []
    for side in (-1, 1):
        x, _ = v.project(side * GAL, 0, Z_NEAR)
        x = int(round(x))
        _, yb = v.project(0, 0, Z_NEAR)
        cv.rect(x - 3 if side > 0 else x - 2, 0, 5, int(round(yb)), OUT)
        cv.rect(x - 2 if side > 0 else x - 1, 0, 3, int(round(yb)), OAK[3]); cv.vline(x - 1 if side < 0 else x - 2, 0, int(round(yb)), OAK[5])
    for (lx, lz) in sorted(PENDANTS, key=lambda p: -p[1]):
        x, y = v.project(lx, 176, lz)
        _, yt = v.project(lx, CEIL, lz)
        shade_pendant(cv, int(round(x)), int(round(y)), chain_top=max(0, int(round(yt))), w=12 if lz < 600 else 10)
        glows.append([int(round(x)), int(round(y)) + 1, "fde9b6", 1])
    # the board, hung on chains from the coffers over the aisle
    bz = 600.0
    bx, by = v.project(0, 214, bz)
    _, btop = v.project(0, CEIL, bz)
    board = Canvas(120, 40)
    x0, y0, w, h = two_line_plaque(board, 60, 2, ["POSSIBLE LIVES", "CLOSED ARCHIVE"], fg=GILT, bg="#1c1622", frame=BRASS)
    px_, py_ = int(round(bx - 60)), int(round(by))
    for hx in (x0 + 8, x0 + w - 9):
        for yy in range(int(round(btop)), py_ + 2, 2):
            cv.px(px_ + hx, yy, IRON[3]); cv.px(px_ + hx, yy + 1, IRON[1])
    cv.paste(board, px_, py_)
    for (lx, lz) in FRONT_LAMPS:
        x, y = v.project(lx, 150, lz)
        shade_pendant(cv, int(round(x)), int(round(y)), chain_top=0, w=18)
        glows.append([int(round(x)), int(round(y)) + 1, "fde9b6", 1])
    # the glow of the single bulb inside the closed archive
    gx, gy = v.project(-GAL * 0.2, CEIL * 0.62, Z_END - 2)
    glows.append([int(round(gx)), int(round(gy)), "f6cf7a", 0])
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    res = f"res://assets/art/rooms/{ROOM}/"

    # restless drawers on the front wall: each slides out in turn
    d = drawer_out(9, 6)
    d.save(os.path.join(out, "battle-drawer.png"))
    slots = index_wall_slots(4, 10, int(SIDE) - 8, int(WALL_H) + 12, dw=DW, dh=DH)
    s0 = v.scale(Z_NEAR)
    rng = np.random.default_rng(9)
    layers = []
    picks = []
    for (u, vv) in slots:
        for side in (-1, 1):
            X = side * (GAL + u + DW / 2)
            Y = WALL_H + 12 - (vv + DH / 2)
            sx, sy = v.project(X, Y, Z_NEAR)
            if (12 <= sx <= 628) and 30 <= sy <= 128 and not (380 <= sx <= 640 and sy <= 74) and not (sx <= 70 and sy <= 30):
                picks.append((int(round(sx - 5)), int(round(sy - 6))))
    idx = rng.choice(len(picks), 8, replace=False)
    for k, i in enumerate(idx):
        pattern = ["0"] * 9
        pattern[k] = "1"
        layers.append({"kind": "blink", "pattern": "".join(pattern), "rate": 1.4, "texture": res + "battle-drawer.png",
                       "x": picks[int(i)][0], "y": picks[int(i)][1]})
    layers += [
        {"kind": "twinkle", "points": glows, "rate": 1.2, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 20, "rect": [180, 30, 280, 110], "speed": [1, 2], "color": "fde9b6"},
        {"kind": "fauna", "fauna": [{"kind": "loose_page", "x": 160, "y": 40, "fly": 7.0, "rate": 3.0},
                                    {"kind": "loose_page", "x": 420, "y": 92, "fly": 5.0, "rate": 2.6},
                                    {"kind": "loose_page", "x": 300, "y": 20, "fly": 9.0, "rate": 3.4}]},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
