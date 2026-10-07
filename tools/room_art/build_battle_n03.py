"""Battle backdrop for the reading room (N03): down the central aisle toward the great window.

Long oak reading tables run off both sides of the aisle in ranks, each with its green banker's
lamps lit; books climb the side walls to a brass gallery rail, high windows above; a beamed and
painted ceiling with green-shaded pendants; the plum runner leads to the great arched window at
the far end, where the moon stands and an owl sits on the ledge. Moonlight comes down the aisle as
a slow-swaying beam with dust turning in it; the lamps breathe."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON
from lib_norlin import (plaster_wall, ceiling_band, wall_shelves, arched_window, wall_sconce, shade_pendant,
                        banker_lamp, built_in_shelves, window_seat, book_row, OAK, OAK_DARK, OAK_FLOOR, BRASS, PAGE,
                        LAMP_GREEN, GILT, NIGHT_N, SPINES)
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "N03"
INK = "#10121e"
Z_END = 1400.0
WALL_X = 330.0
ROOM_H = 340.0
AISLE = 70.0                 # tables start this far from the centre line
TABLE_X1 = 270.0
TABLE_H = 28.0
TABLE_D = 72.0
TABLES = [460.0, 640.0, 820.0, 1000.0, 1180.0]
RUG = ["#1e1018", "#2e1622", "#45202e", "#4e2434", "#62303e", "#b07a46", "#d8a868"]
HAZE = "#181624"


def lamp_xs():
    return [AISLE + 50, TABLE_X1 - 50]


def floor_shader(X, Z):
    """Parquet in long strips, the plum runner down the aisle, lamp pools around the tables and
    the moonlight coming down the aisle in stepped bands."""
    oak = pal_array(OAK_FLOOR)
    col = np.floor(X / 12.0)
    off = hash2(col, 2) * 90
    seg = np.floor((Z + off) / 90.0)
    t = hash2(col, seg, 5)
    rgb = oak[3] * (1 - t[:, None]) + oak[4] * t[:, None]
    rgb[t < 0.15] = oak[2]
    rgb[((X / 12.0) % 1) < 0.1] = oak[1]
    rgb[(((Z + off) / 90.0) % 1) < 0.015] = oak[1]
    ax = np.abs(X)
    rug = pal_array(RUG)
    run = ax < 46
    rgb[run] = rug[2]
    rgb[run & (ax > 40)] = rug[1]
    rgb[run & (np.abs(ax - 37) < 1.4)] = rug[5]
    lz = (Z % 52.0) - 26
    rgb[run & (ax + np.abs(lz) * 0.8 < 15)] = rug[3]
    rgb[run & (ax + np.abs(lz) * 0.8 < 10)] = rug[4]
    rgb[run & (ax + np.abs(lz) * 0.8 < 3)] = rug[6]
    for z0 in TABLES:
        for side in (-1, 1):
            for lx in lamp_xs():
                warm_light(rgb, np.hypot(X - side * lx, (Z - z0 - TABLE_D / 2) * 0.7), 95, strength=0.3)
    # moonlight down the aisle, in three stepped bands widening toward the viewer
    w = 40 + (Z_END - Z) * 0.09
    for k, (f, a) in enumerate([(1.0, 0.05), (0.7, 0.05), (0.4, 0.05)]):
        m = (ax < w * f) & (Z < Z_END)
        rgb[m] = rgb[m] * (1 - a) + np.array(C("#b4c4f0")[:3]) * a
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 800, 1700, amount=0.5)
    return out


def ceiling_shader(X, Z):
    """Dark oak beams across the room with painted panels between: deep red, a gilt border."""
    rgb = np.zeros((X.shape[0], 3), np.float32)
    zz = Z % 140.0
    xx = np.abs(X) % 110.0
    rgb[:] = np.array(C("#3a1a22")[:3])
    border = (zz < 26) | (zz > 134) | (xx < 10) | (xx > 104)
    rgb[(zz > 22) & (zz < 26)] = np.array(C(GILT)[:3]) * 0.8
    inner = (zz > 40) & (zz < 120) & (xx > 24) & (xx < 90)
    rgb[inner] = np.array(C("#2a3a4a")[:3])
    rgb[inner & ((zz - 80) ** 2 / 400 + (xx - 57) ** 2 / 300 < 1)] = np.array(C("#3a4a5a")[:3])
    beam = (zz < 20) | (xx < 7)
    rgb[beam] = pal_array(OAK)[2]
    rgb[(zz < 3)] = pal_array(OAK)[3]
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 500, 1500, amount=0.6)
    return out


def side_wall_texture(length, height, seed=0):
    """A long side wall laid flat: books from floor to a brass gallery rail, then warm plaster
    with tall round-headed clerestory windows between oak pilasters, a painted cornice on top."""
    cv = Canvas(length, height, seed=seed)
    plaster_wall(cv, 0, 0, length, height, seed=seed, shadow_top=18)
    ceiling_band(cv, 0, 0, length, 18)
    rail = height - 176
    for k, wx in enumerate(range(50, length - 50, 160)):
        arched_window(cv, wx, 64, 46, rail - 86, seed=seed + k, view="trees" if k % 2 else "campus")
        cv.rect(wx + 100, 22, 14, rail - 22, "#7e6252"); cv.vline(wx + 100, 22, rail - 22, "#9a7c66"); cv.vline(wx + 113, 22, rail - 22, "#5e4640")
    wall_shelves(cv, 2, rail + 10, length - 4, height - rail - 20, seed=seed + 40, shelf=26, dim=0.12, frame=False)
    cv.rect(0, rail, length, 10, OAK[3]); cv.hline(0, rail, length, OAK[5]); cv.hline(0, rail + 9, length, OAK[1])
    cv.rect(0, rail - 6, length, 3, BRASS[2]); cv.hline(0, rail - 6, length, BRASS[4])
    for bx in range(0, length, 18):
        cv.vline(bx, rail - 4, 4, BRASS[1])
    cv.rect(0, height - 10, length, 10, OAK[2]); cv.hline(0, height - 10, length, OAK[4])
    return cv.a


def far_wall(Wp, Hp):
    """The far end at its on-screen size: the great window (moon, campus roofline), its window
    seat, shelves either side up to the rail, the painted cornice."""
    cv = Canvas(Wp, Hp, seed=5)
    plaster_wall(cv, 0, 0, Wp, Hp, seed=12, shadow_top=8)
    ceiling_band(cv, 0, 0, Wp, 6, stencil=False)
    cx = Wp // 2
    ww, wh = 56, 46
    wtop = Hp - 10 - wh
    arched_window(cv, cx - ww // 2, wtop, ww, wh, seed=33, view="campus", moon=(cx + 12, wtop - 12))
    window_seat(cv, cx - ww // 2 - 4, Hp - 10, ww + 8, 10, cushion="#4a2030")
    rail = Hp - 40
    for (x0, x1) in [(2, cx - ww // 2 - 12), (cx + ww // 2 + 12, Wp - 2)]:
        wall_shelves(cv, x0, rail, x1 - x0, Hp - rail - 3, seed=x0 + 7, shelf=12, dim=0.2, frame=False)
        cv.rect(x0, rail - 3, x1 - x0, 3, OAK[3]); cv.hline(x0, rail - 3, x1 - x0, BRASS[3])
        arched_window(cv, (x0 + x1) // 2 - 7, 18, 14, 18, seed=x0, view="trees", sill=False)
    cv.a[..., :3] *= 0.9
    return cv, (cx, wtop + wh)


def table_top(z0, side):
    """Shader for one table's top (height TABLE_H): oak with grain, lamp pools, papers and books."""
    xa, xb = (AISLE, TABLE_X1) if side > 0 else (-TABLE_X1, -AISLE)
    lx = [side * x for x in lamp_xs()]

    def sh(X, Z):
        n = X.shape[0]
        oak = pal_array(OAK)
        g = hash2(np.floor(X / 3.0), np.floor(Z / 14.0), int(z0))
        rgb = oak[3] * (1 - g[:, None] * 0.5) + oak[4] * (g[:, None] * 0.5)
        rgb[(Z - z0) < 3] = oak[5]
        for x in lx:
            warm_light(rgb, np.hypot(X - x, (Z - z0 - TABLE_D / 2) * 1.2), 40, strength=0.45)
        cell = hash2(np.floor(X / 22.0), np.floor((Z - z0) / 18.0), int(z0) + side)
        paper = (cell > 0.78) & (((X / 22.0) % 1) > 0.25) & ((((Z - z0) / 18.0) % 1) > 0.3)
        rgb[paper] = pal_array(PAGE)[3]
        book = (cell < 0.12) & (((X / 22.0) % 1) > 0.35) & ((((Z - z0) / 18.0) % 1) > 0.2)
        rgb[book] = pal_array(SPINES)[(hash2(np.floor(X / 22.0), int(z0), 9)[book] * 15).astype(int)]
        a = ((X > xa) & (X < xb) & (Z > z0) & (Z < z0 + TABLE_D)).astype(np.float32)
        out = rgba_of(rgb, a)
        fog(out, Z, HAZE, 800, 1700, amount=0.5)
        return out
    return sh


def apron_shader(length, z_near):
    """A table's apron and legs seen from the front or the aisle end; open underneath."""
    def sh(u, Y, Z):
        oak = pal_array(OAK)
        rgb = np.zeros((u.shape[0], 3), np.float32)
        rgb[:] = oak[2]
        top = Y > TABLE_H - 7
        rgb[Y > TABLE_H - 2] = oak[4]
        leg = (u < 7) | (u > length - 7)
        rgb[leg & ~top] = oak[1]
        rgb[leg & ~top & ((u < 2) | (u > length - 2))] = oak[0]
        a = (top | leg).astype(np.float32)
        out = rgba_of(rgb, a)
        fog(out, Z, HAZE, 800, 1700, amount=0.5)
        return out
    return sh


def tiny_lamp(cv, x, y, s):
    """A banker's lamp drawn at a distance scale s (full size at s >= 0.8)."""
    if s >= 0.6:
        banker_lamp(cv, x, y)
        return y - 7
    s = s * 1.4
    w = max(3, int(round(9 * s)))
    h = max(1, int(round(3 * s)))
    cv.rect(x - w // 2, y - h - max(1, int(4 * s)), w, h, LAMP_GREEN[3])
    cv.hline(x - w // 2, y - max(1, int(4 * s)) - 1, w, "#f6cd78")
    cv.vline(x, y - max(1, int(4 * s)), max(1, int(4 * s)), BRASS[2])
    for r, a in [(max(2, int(10 * s)), 0.08)]:
        cv.ellipse(x - r, y - r // 2 - 2, 2 * r + 1, r, C("#f6cf7a", a))
    return y - max(1, int(4 * s)) - 1


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    v = View(horizon=98, cam=52, fill="#141223")
    v.ground(floor_shader, z_max=Z_END)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=ROOM_H, z_max=Z_END)
    for side in (-1, 1):
        L = int(Z_END - 200)
        tex = side_wall_texture(L, int(ROOM_H), seed=60 + side)
        def shade_wall(u, Y, Z, tex=tex):
            o = texture_lookup(tex, u, ROOM_H - Y, wrap=False)
            o[..., :3] *= 0.82
            return fog(o, Z, HAZE, 800, 1700, amount=0.5)
        v.plane((side * WALL_X, 200.0), (side * WALL_X, Z_END), shade_wall, y_max=ROOM_H)
    s = v.scale(Z_END)
    Wp = int(round(2 * WALL_X * s)) + 2
    Hp = int(round(ROOM_H * s))
    fw, sill = far_wall(Wp, Hp)
    fx0 = int(round(v.vx - Wp / 2))
    fy0 = int(round(v.ground_y(Z_END) - Hp))
    v.strip(fw.a, fy0, fx0)
    # tables, far to near
    for z0 in sorted(TABLES, reverse=True):
        for side in (-1, 1):
            v.ground(table_top(z0, side), height=TABLE_H, z_max=Z_END)
            xa, xb = (AISLE, TABLE_X1) if side > 0 else (-TABLE_X1, -AISLE)
            v.plane((side * AISLE, z0 + TABLE_D), (side * AISLE, z0), apron_shader(TABLE_D, z0), y_max=TABLE_H)
            v.plane((xa, z0), (xb, z0), apron_shader(xb - xa, z0), y_max=TABLE_H)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp chair backs on the tables' far sides, lamps on the tables, pendants from the beams
    glows = []
    for z0 in sorted(TABLES, reverse=True):
        for side in (-1, 1):
            zc = z0 + TABLE_D + 6
            sc = v.scale(zc)
            for cx in np.arange(AISLE + 22, TABLE_X1 - 10, 40):
                x0, ytop = v.project(side * cx, TABLE_H + 20, zc)
                _, ybot = v.project(side * cx, TABLE_H, zc)
                cw = max(3, int(round(14 * sc)))
                xi, yt, yb = int(round(x0)) - cw // 2, int(round(ytop)), int(round(ybot))
                if yb - yt < 2:
                    continue
                cv.rect(xi - 1, yt - 1, cw + 2, yb - yt + 1, OUT)
                cv.rect(xi, yt, cw, max(1, int(round(3 * sc))), OAK[4])
                cv.rect(xi, yt + max(1, int(round(3 * sc))), cw, yb - yt - max(1, int(round(3 * sc))), OAK_DARK[2])
                cv.vline(xi, yt, yb - yt, OAK[3]); cv.vline(xi + cw - 1, yt, yb - yt, OAK[2])
                if cw >= 7:
                    cv.vline(xi + cw // 2, yt + 2, yb - yt - 2, OAK[3])
            for lx in lamp_xs():
                x, y = v.project(side * lx, TABLE_H, z0 + TABLE_D / 2)
                sc = v.scale(z0 + TABLE_D / 2)
                gy = tiny_lamp(cv, int(round(x)), int(round(y)), sc)
                glows.append([int(round(x)), int(gy), "fff0c4", 1 if sc > 0.5 else 0])
    for z in (560.0, 900.0, 1240.0):
        for side in (-1, 1):
            x, y = v.project(side * 170, 200, z)
            _, ytop = v.project(side * 170, ROOM_H, z)
            w = max(6, int(round(26 * v.scale(z))))
            shade_pendant(cv, int(round(x)), int(round(y)), chain_top=max(0, int(round(ytop))), w=w)
            glows.append([int(round(x)), int(round(y)) + 1, "fde9b6", 1])
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    res = f"res://assets/art/rooms/{ROOM}/"
    owl = [fx0 + sill[0] + 10, fy0 + sill[1]]
    return {
        "far": res + "battle-far.png",
        "layers": [
            {"kind": "beam", "x": 320, "y": fy0 + sill[1] - 30, "angle": 90, "sweep": 3, "period": 19.0, "phase": 0.0,
             "length": 120, "width": 150, "color": "c8d4ff", "alpha": 0.1, "floor": 150},
            {"kind": "twinkle", "points": glows, "rate": 1.2, "min": 0.55},
            {"kind": "particles", "style": "dust", "count": 24, "rect": [250, 40, 140, 120], "speed": [1, 3], "color": "d8dcf0"},
            {"kind": "fauna", "fauna": [{"kind": "barn_owl", "x": owl[0], "y": owl[1], "range": 0, "speed": 0.0, "rate": 1.5}]},
        ],
    }


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
