"""Battle backdrop for the checkout hall (N02): looking down the length of the hall toward the
stacks. The long circulation counter recedes along the left with its green lamps and returned
books; bookshelves line both walls under tall night windows; the honey stone floor with its slate
cabochons and the green runner run to the far end, where an archway opens on the dark stacks and
the regulator clock (two minutes to midnight) swings its pendulum over it. Opal pendant lamps
hang down the hall and breathe; dust drifts in their light."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON
from lib_norlin import (plaster_wall, ceiling_band, wall_shelves, arched_window, wall_sconce, regulator_clock,
                        pendulum_frames, pendant_lamp, banker_lamp, book_stack, card_catalogue, plaque, book_row,
                        OAK, OAK_DARK, BRASS, PAGE, CARPET_GREEN, GILT, NIGHT_N)
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "N02"
INK = "#10121e"
Z_END = 1000.0
WALL_X = 300.0
HALL_H = 300.0
COUNTER_X = -205.0          # front face of the circulation counter
COUNTER_BACK = -290.0
COUNTER_H = 46.0
COUNTER_Z = (360.0, 820.0)
PENDANTS = [(-110, 470), (110, 470), (-110, 700), (110, 700), (-110, 900), (110, 900)]
PENDANT_Y = 165.0
COUNTER_LAMPS = [440.0, 640.0]
FIELD = ["#5a4034", "#74543f", "#7e5c45", "#88654b", "#926e52"]
HAZE = "#1c1622"


def floor_shader(X, Z):
    size = 44.0
    fx, fz = X / size, Z / size
    i, j = np.floor(fx), np.floor(fz)
    t = hash2(i, j, 3)
    field = pal_array(FIELD)
    rgb = field[2] * (1 - t[:, None]) + field[3] * t[:, None]
    rgb[t > 0.82] = field[4]
    gx, gz = fx - i, fz - j
    joint = (gx < 0.04) | (gz < 0.04)
    rgb[joint] = np.array(C("#563c34")[:3])
    rgb[(gz > 0.04) & (gz < 0.1) & ~joint] = rgb[(gz > 0.04) & (gz < 0.1) & ~joint] * 0.85 + field[4] * 0.15
    d = (np.abs(fx - np.round(fx)) + np.abs(fz - np.round(fz)) * 0.9) * size
    rgb[d < 8] = np.array(C("#2a2430")[:3])
    rgb[d < 5.5] = np.array(C("#423a48")[:3])
    # the green runner down the middle
    g = pal_array(CARPET_GREEN)
    ax = np.abs(X)
    run = ax < 36
    rgb[run] = g[2]
    rgb[run & (ax > 30)] = g[3]
    rgb[run & (np.abs(ax - 27) < 1.6)] = g[5]
    lz = (Z % 46.0) - 23
    loz = run & (ax + np.abs(lz) * 0.7 < 11)
    rgb[loz] = g[4]
    rgb[run & (ax + np.abs(lz) * 0.7 < 3.5)] = g[6]
    # pools of lamplight
    for (px_, pz) in PENDANTS:
        warm_light(rgb, np.hypot(X - px_, (Z - pz) * 0.6), 110, strength=0.34)
    for lz_ in COUNTER_LAMPS:
        warm_light(rgb, np.hypot(X - COUNTER_X - 30, (Z - lz_) * 0.6), 80, strength=0.3)
    # moonlight from the right-hand windows laid in slanting panes
    mz = (Z + X * 0.6) % 210
    moon = (mz < 60) & (X > 40) & (X < 280)
    rgb[moon] = rgb[moon] * 0.86 + np.array(C("#b4c4f0")[:3]) * 0.14
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 700, 1400, amount=0.45)
    return out


def ceiling_shader(X, Z):
    """A painted coffered ceiling: oak beams across the hall, dark green coffers with gilt dots."""
    rgb = np.zeros((X.shape[0], 3), np.float32)
    rgb[:] = np.array(C("#2a2a2e")[:3])
    bz = (Z % 120.0) < 16
    bx = (np.abs(X) % 100.0) < 10
    coffer = ~(bz | bx)
    rgb[coffer] = np.array(C("#1e3028")[:3])
    inner = coffer & ((Z % 120.0) > 26) & ((Z % 120.0) < 110) & ((np.abs(X) % 100.0) > 20) & ((np.abs(X) % 100.0) < 90)
    rgb[inner] = np.array(C("#24382e")[:3])
    rgb[bz | bx] = pal_array(OAK)[2]
    rgb[((Z % 120.0) < 3) | ((np.abs(X) % 100.0) < 2)] = pal_array(OAK)[3]
    dot = coffer & (np.abs((Z % 120.0) - 68) < 3) & (np.abs((np.abs(X) % 100.0) - 55) < 3)
    rgb[dot] = np.array(C(GILT)[:3])
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 500, 1300, amount=0.6)
    return out


def hall_wall_texture(length, height, seed=0, catalogues=False):
    """A side wall of the hall laid flat (u along the wall toward the far end): coffered cornice,
    warm plaster with tall round-headed night windows and sconces, then books from the floor up."""
    cv = Canvas(length, height, seed=seed)
    plaster_wall(cv, 0, 0, length, height, seed=seed, shadow_top=20)
    ceiling_band(cv, 0, 0, length, 16)
    shelf_top = height - 158
    rng = np.random.default_rng(seed)
    for k, wx in enumerate(range(40, length - 60, 150)):
        arched_window(cv, wx, 52, 40, 70, seed=seed + k, view="campus" if k % 2 else "trees",
                      moon=(wx + 26, 40) if k == 2 else None)
        cv.rect(wx + 84, 30, 12, shelf_top - 34, "#7e6252"); cv.vline(wx + 84, 30, shelf_top - 34, "#9a7c66")
        wall_sconce(cv, wx + 90, 100)
    cv.rect(0, shelf_top - 8, length, 6, OAK[3]); cv.hline(0, shelf_top - 8, length, OAK[5]); cv.hline(0, shelf_top - 3, length, OAK[1])
    wall_shelves(cv, 2, shelf_top, length - 4, height - shelf_top - 10, seed=seed + 50, shelf=24, dim=0.1, frame=False)
    cv.rect(0, height - 10, length, 10, OAK[2]); cv.hline(0, height - 10, length, OAK[4])
    return cv.a


def counter_texture(length, height):
    """The front of the circulation counter laid flat: oak raised panels, a brass lip, the
    CHECKOUT plate near the start and the RETURNS slot toward the far end."""
    cv = Canvas(length, height)
    cv.rect(0, 0, length, height, OAK[3])
    cv.rect(0, 0, length, 4, BRASS[2]); cv.hline(0, 0, length, BRASS[4]); cv.hline(0, 3, length, BRASS[1])
    for px_ in range(6, length - 30, 36):
        cv.rect(px_, 9, 30, height - 18, OAK[1])
        cv.rect(px_ + 1, 10, 28, height - 20, OAK[4])
        cv.rect(px_ + 3, 12, 24, height - 24, OAK[3])
        cv.hline(px_ + 1, 10, 28, OAK[5])
    cv.rect(0, height - 6, length, 6, OAK[1]); cv.hline(0, height - 6, length, OAK[2])
    for (lab, u) in (("CHECKOUT", 30), ("RETURNS", length - 150)):
        tw = text_width(lab) + 8
        cv.rect(u - 1, 13, tw + 2, 14, OUT)
        cv.rect(u, 14, tw, 12, BRASS[3]); cv.hline(u, 14, tw, BRASS[4])
        text(cv, lab, u + 4, 14, "#3a2418")
    cv.rect(length - 146, 30, 60, 5, OUT)
    return cv.a


def far_wall(Wp, Hp):
    """The far end of the hall at its on-screen size: an archway into the dark stacks (shelves
    receding to a single lamp), STACKS over it, the regulator clock above, windows either side."""
    cv = Canvas(Wp, Hp, seed=4)
    plaster_wall(cv, 0, 0, Wp, Hp, seed=9, shadow_top=8)
    cx = Wp // 2
    # archway
    aw, ah = 44, 38
    ax0, atop = cx - aw // 2, Hp - ah
    cv.ellipse(ax0 - 5, atop - 5, aw + 10, aw + 10, "#8a6654"); cv.rect(ax0 - 5, atop + aw // 2, aw + 10, ah - aw // 2, "#8a6654")
    cv.ellipse(ax0 - 3, atop - 3, aw + 6, aw + 6, "#b48c70"); cv.rect(ax0 - 3, atop + aw // 2, aw + 6, ah - aw // 2, "#b48c70")
    cv.ellipse(ax0, atop, aw, aw, "#0c0a12"); cv.rect(ax0, atop + aw // 2, aw, ah - aw // 2, "#0c0a12")
    # the stacks beyond: shelf faces receding toward a lone lamp
    for k, (inset, dim) in enumerate([(2, 0.35), (8, 0.5), (13, 0.62), (17, 0.72)]):
        y0 = atop + aw // 2 - 4 + k * 3
        h = Hp - y0 - inset // 2
        for side in (-1, 1):
            x = ax0 + inset if side < 0 else ax0 + aw - inset - 5
            cv.rect(x, y0, 5, h, shade(OAK_DARK[3], -dim * 0.5))
            for sy in range(y0 + 3, y0 + h - 1, 5):
                book_row(cv, x, sy, 5, 4, seed=k * 10 + sy + side, dim=dim)
    cv.rect(cx - 1, atop + aw // 2 + 4, 3, 3, "#f6cf7a"); cv.px(cx, atop + aw // 2 + 3, "#fde9b6")
    cv.rect(cx - 6, Hp - 3, 12, 2, C("#f6cf7a", 0.25))
    # STACKS plaque and the clock
    tw = text_width("STACKS") + 8
    plaque(cv, cx - tw // 2, atop - 16, "STACKS")
    pivot = regulator_clock(cv, cx, atop - 48, case_h=26, w=18, hour=11, minute=58)
    # windows either side and the oak dado
    for wx in (cx - 74, cx + 50):
        arched_window(cv, wx, 22, 24, 40, seed=wx, view="trees", sill=True)
    cv.rect(0, Hp - 22, ax0 - 5, 22, OAK[2]); cv.rect(ax0 + aw + 5, Hp - 22, Wp - ax0 - aw - 5, 22, OAK[2])
    cv.hline(0, Hp - 22, ax0 - 5, OAK[4]); cv.hline(ax0 + aw + 5, Hp - 22, Wp - ax0 - aw - 5, OAK[4])
    for x0 in (4, Wp - 40):
        card_catalogue(cv, x0, Hp, w=36, h=20, seed=x0)
    cv.a[..., :3] *= 0.86
    return cv, pivot


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    v = View(horizon=98, cam=52, fill="#141223")
    v.ground(floor_shader, z_max=Z_END)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=HALL_H, z_max=Z_END)
    for side in (-1, 1):
        L = int(Z_END - 180)
        tex = hall_wall_texture(L, int(HALL_H), seed=20 + side)
        def shade_wall(u, Y, Z, tex=tex, side=side, L=L):
            o = texture_lookup(tex, u, HALL_H - Y, wrap=False)
            o[..., :3] *= 0.84
            return fog(o, Z, HAZE, 700, 1400, amount=0.45)
        v.plane((side * WALL_X, 180.0), (side * WALL_X, Z_END), shade_wall, y_max=HALL_H)
    # the counter: its front face, then the leather top seen edge-on
    Lc = int(COUNTER_Z[1] - COUNTER_Z[0])
    ctex = counter_texture(Lc, int(COUNTER_H))
    def shade_counter(u, Y, Z):
        o = texture_lookup(ctex, u, COUNTER_H - Y, wrap=False)
        for lz in COUNTER_LAMPS:
            warm_light(o[..., :3], np.abs(Z - lz) * 1.0 + np.abs(COUNTER_H - Y) * 2, 60, strength=0.25)
        return fog(o, Z, HAZE, 700, 1400, amount=0.45)
    v.plane((COUNTER_X, COUNTER_Z[0]), (COUNTER_X, COUNTER_Z[1]), shade_counter, y_max=COUNTER_H)
    def shade_end(u, Y, Z):
        o = texture_lookup(ctex, u + 200, COUNTER_H - Y, wrap=True)
        o[..., :3] *= 0.7
        return o
    v.plane((COUNTER_BACK, COUNTER_Z[0]), (COUNTER_X, COUNTER_Z[0]), shade_end, y_max=COUNTER_H)
    def counter_top(X, Z):
        rgb = np.zeros((X.shape[0], 3), np.float32)
        rgb[:] = np.array(C("#24402e")[:3])
        rgb[X > COUNTER_X - 6] = np.array(C(BRASS[3])[:3])
        a = ((X > COUNTER_BACK) & (X < COUNTER_X) & (Z > COUNTER_Z[0]) & (Z < COUNTER_Z[1])).astype(np.float32)
        return rgba_of(rgb, a)
    v.ground(counter_top, height=COUNTER_H, z_max=Z_END)
    # the far wall
    s = v.scale(Z_END)
    Wp = int(round(2 * WALL_X * s)) + 2
    Hp = int(round(HALL_H * s))
    fw, pivot = far_wall(Wp, Hp)
    fx0 = int(round(v.vx - Wp / 2))
    fy0 = int(round(v.ground_y(Z_END) - Hp))
    v.strip(fw.a, fy0, fx0)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # Crisp 1:1 pieces: counter lamps and returned books, pendant lamps on their chains.
    glows = []
    for lz in COUNTER_LAMPS + [760.0]:
        x, y = v.project(COUNTER_X - 34, COUNTER_H, lz)
        sc = v.scale(lz)
        if lz in COUNTER_LAMPS:
            banker_lamp(cv, int(round(x)), int(round(y)))
            glows.append([int(round(x)), int(round(y)) - 7, "fff0c4", 1])
        book_stack(cv, int(round(x)) + 9, int(round(y)), max(6, int(14 * sc)), n=3, seed=int(lz))
    for (px_, pz) in sorted(PENDANTS, key=lambda p: -p[1]):
        x, y = v.project(px_, PENDANT_Y, pz)
        _, ytop = v.project(px_, HALL_H, pz)
        r = max(3, int(round(7 * v.scale(pz))))
        pendant_lamp(cv, int(round(x)), int(round(y)), chain_top=max(0, int(round(ytop))), r=r)
        glows.append([int(round(x)), int(round(y)), "fde9b6", 2 if r > 4 else 1])
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))

    res = f"res://assets/art/rooms/{ROOM}/"
    px_, py_, bob_y = pivot
    layers = []
    for k, (fr, ox) in enumerate(pendulum_frames(bob_y - py_, swing=2)):
        name = f"battle-pendulum-{k}.png"
        fr.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": ["1000", "0101", "0010"][k], "rate": 2.0,
                       "texture": res + name, "x": fx0 + px_ - ox, "y": fy0 + py_})
    layers += [
        {"kind": "twinkle", "points": glows, "rate": 1.3, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [140, 20, 360, 130], "speed": [1, 3], "color": "fde9b6"},
        {"kind": "fauna", "fauna": [{"kind": "lamp_moth", "x": int(round(v.project(110, PENDANT_Y, 470)[0])),
                                     "y": int(round(v.project(110, PENDANT_Y, 470)[1])) + 6, "range": 6, "speed": 2.0, "rate": 9.0}]},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
