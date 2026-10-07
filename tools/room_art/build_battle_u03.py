"""Battle backdrop for the UMC atrium (U03): the fight happens on the polished floor in the middle of
the hall, looking north along the runner to the NEXT YEAR alcove. Sandstone pilasters and tall
arched windows run down both side walls (the club room's doors glow warm on the left, the REPAIR
stair drops away under an arch on the right), brass pendants hang from the coffered ceiling, moonlight
import paths
from the east windows lies across the floor, and the marquee bulbs chase round NEXT YEAR."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from interior import PANEL, RUG, NIGHT
from props import OUT, IRON
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_umc import (MARBLE, ROSE, BRASS, STONE_IN, SHADOW, GLOW, PLASTER, VELVET, EXIT_GREEN,
                     atrium_wall, sandstone_dado, frieze, ceiling_beam, pilaster_in, atrium_window, sconce,
                     club_doors, next_year_alcove, enamel_sign, caged_bulb, halo)

INK = "#10121e"
Z_NEAR = 300.0
Z_BACK = 700.0
WALL_X = 420.0
HALL_H = 260.0
DADO_H = 90          # quiet sandstone below the windows (behind the fighters' heads)
EAST_WINDOWS = [440.0, 640.0]   # right-wall window centres (Z) that throw moonlight on the floor


def floor_shader(X, Z):
    """Polished sandstone squares with rose cabochons at the corners, a rose border band along the
    walls, the runner down the middle to a brass ring before the alcove."""
    tile = 30.0
    cx, cz = np.floor(X / tile), np.floor(Z / tile)
    fx, fz = X / tile - cx, Z / tile - cz
    m = pal_array(MARBLE)
    tone = hash2(cx, cz, 3)
    light = ((cx + cz) % 2 == 0)
    rgb = np.where(light[:, None], m[5] * (1 - tone[:, None] * 0.25) + m[4] * tone[:, None] * 0.25,
                   m[4] * (1 - tone[:, None] * 0.3) + m[3] * tone[:, None] * 0.3)
    grout = (fx < 0.05) | (fz < 0.05)
    rgb[grout] = m[2]
    # cabochons: small rose diamonds where four squares meet
    dx, dz = np.minimum(fx, 1 - fx), np.minimum(fz, 1 - fz)
    cab = (dx + dz) < 0.16
    r = pal_array(ROSE)
    rgb[cab] = r[1]
    rgb[(dx + dz < 0.08)] = r[3]
    # border band along the walls, a brass line inside it
    ax = np.abs(X)
    band = ax > WALL_X - 52
    bt = hash2(np.floor(Z / 26), np.floor(ax / 26), 4) > 0.5
    rgb[band] = np.where(bt[band][:, None], r[2], r[1])
    rgb[(ax > WALL_X - 56) & (ax <= WALL_X - 52)] = pal_array(BRASS)[2]
    # the runner: deep red with a gold border and a diamond pattern
    rr = pal_array(RUG)
    run = (ax < 34) & (Z < Z_BACK - 70)
    rgb[run] = rr[2]
    dia = (np.abs(((Z / 22.0) % 1.0) - 0.5) * 22 + ax * 0.9) < 6
    rgb[run & dia] = rr[3]
    rgb[run & (ax > 27)] = rr[4]
    rgb[run & (ax > 30)] = rr[1]
    # brass ring where the booth usually stands
    ring = np.hypot(X / 1.0, (Z - (Z_BACK - 40)) * 1.6)
    rgb[(ring > 64) & (ring < 70)] = pal_array(BRASS)[3]
    # night grade: warmer and a little darker than the room's lamplit stone
    rgb *= np.array([0.9, 0.8, 0.74], np.float32)
    # polish: long reflections of the alcove glow and the windows (the wool runner only glows softly)
    keep = rgb[run].copy()
    warm_light(rgb, np.hypot(X * 2.4, (Z - Z_BACK) * 0.18), 120, colour="#f6c27a", strength=0.4)
    rgb[run] = keep * 0.75 + rgb[run] * 0.25
    for zc in (480.0, 600.0):
        for side in (-1, 1):
            warm_light(rgb, np.hypot((X - side * (WALL_X - 30)) * 0.5, (Z - zc) * 0.9), 40, colour="#f6cf7a", strength=0.18)
    # moonlight laid across the floor from the east windows (slanting toward the west)
    for zc in EAST_WINDOWS:
        zz = Z - (zc - (WALL_X - X) * 0.42)
        reach = WALL_X - X
        patch = (np.abs(zz) < 24) & (reach > 40) & (reach < 230)
        rgb[patch] = rgb[patch] * 0.72 + pal_array(["#a8b4e8"])[0] * 0.28
        # the window's mullion and transoms laid across the patch
        bars = patch & ((np.abs(zz) < 1.6) | (np.abs(((reach - 40) % 64) - 32) > 30.5))
        rgb[bars] = rgb[bars] * 0.82
    # pools under the pendants where the party stands
    warm_light(rgb, np.hypot((X + 150) * 1.0, (Z - 470) * 1.6), 110, colour="#f6cf7a", strength=0.26)
    warm_light(rgb, np.hypot((X - 150) * 1.0, (Z - 470) * 1.6), 110, colour="#f6cf7a", strength=0.22)
    warm_light(rgb, np.hypot((X + 95) * 1.0, (Z - 610) * 1.6), 70, colour="#f6cf7a", strength=0.2)
    warm_light(rgb, np.hypot((X - 95) * 1.0, (Z - 610) * 1.6), 70, colour="#f6cf7a", strength=0.2)
    out = rgba_of(rgb)
    fog(out, Z, "#241a2a", 560, 820, amount=0.45)
    return out


def side_wall(left):
    """A side wall laid out as it appears on screen: the left wall runs near (u=0) to far, the right
    wall far to near. Pilasters and tall arched windows above a sandstone dado; the club room's
    doors on the left, the arch of the service stair on the right."""
    L, Hh = int(Z_BACK - Z_NEAR), int(HALL_H)
    cv = Canvas(L, Hh, seed=4 if left else 5)
    atrium_wall(cv, 0, 0, L, Hh, seed=6 if left else 7)
    cv.rect(0, 0, L, 18, C(SHADOW, 0.35))
    frieze(cv, 0, 22, L)
    sandstone_dado(cv, 0, Hh - DADO_H, L, DADO_H, seed=3)
    col = lambda z: int(z - Z_NEAR) if left else int(Z_BACK - z)
    pil = [430, 520, 600, 690] if left else [440, 520, 610, 690]
    for z in pil:
        pilaster_in(cv, col(z) - 8, 38, 16, Hh - 38)
    glints = []
    if left:
        for (z, seed) in [(470, 1), (650, 2)]:
            atrium_window(cv, col(z) - 26, 92, 52, 72, seed=seed)
            sconce(cv, col(z) - 42, 150)
        club_doors(cv, col(560), Hh - 2, w=64, h=104, plaque="CLUB ROOM")
    else:
        for (z, seed) in [(EAST_WINDOWS[0], 3), (EAST_WINDOWS[1], 4)]:
            atrium_window(cv, col(z) - 26, 92, 52, 72, seed=seed, moon=(col(z) + 10, 70) if z > 600 else None)
        # the service stair's arch: darkness, a rail dropping away, a dim exit sign far below
        ax, aw, atop = col(565), 74, Hh - 128
        r = aw // 2
        cv.ellipse(ax - r - 7, atop - 7, aw + 14, aw + 14, STONE_IN[0])
        cv.rect(ax - r - 7, atop + r, aw + 14, Hh - atop - r, STONE_IN[0])
        cv.ellipse(ax - r - 6, atop - 6, aw + 12, aw + 12, STONE_IN[2])
        cv.rect(ax - r - 6, atop + r, aw + 12, Hh - atop - r, STONE_IN[1])
        cv.ellipse(ax - r, atop, aw, aw, "#0c0a12")
        cv.rect(ax - r, atop + r, aw, Hh - atop - r, "#0c0a12")
        cv.rect(ax - 9, atop + r + 18, 18, 6, EXIT_GREEN[0]); cv.rect(ax - 8, atop + r + 19, 16, 4, EXIT_GREEN[1])
        caged_bulb(cv, ax + 18, atop + r + 2)
        for k in range(6):
            yy = Hh - 4 - k * 9
            cv.rect(ax - r + 4 + k * 2, yy, aw - 8 - k * 4, 3, mix(STONE_IN[2], "#0c0a12", k / 6))
        cv.line(ax - r + 2, Hh - 30, ax - 10, atop + r + 30, BRASS[3])
        sw = text_width("REPAIR") + 8
        enamel_sign(cv, ax - sw // 2, atop - 26, "REPAIR", bg="#1f2a2a", fg="#f6cd78")
        for z in (450, 690):
            sconce(cv, col(z), 150)
    return cv.a


def back_wall():
    """The hall's north end painted at its on-screen size (depth Z_BACK): frieze and coffered beam,
    two arched windows each side of the NEXT YEAR alcove, sconces on the pilasters."""
    s = 320.0 / Z_BACK
    W = int(round(2 * WALL_X * s))
    Hh = int(round(HALL_H * s))
    cv = Canvas(W, Hh, seed=9)
    atrium_wall(cv, 0, 0, W, Hh, seed=9)
    ceiling_beam(cv, 0, 0, W)
    frieze(cv, 0, 6, W, inscription="UNIVERSITY MEMORIAL CENTER")
    base = Hh
    sandstone_dado(cv, 0, base - 20, W, 20, seed=5)
    cx = W // 2
    for px in (10, 62, 112, W - 113, W - 63, W - 11):
        pilaster_in(cv, px - 4, 21, 8, base - 21)
    for i, wx in enumerate((36, 87, W - 88, W - 37)):
        atrium_window(cv, wx - 13, 48, 26, 36, seed=20 + i, moon=(wx + 6, 40) if i == 3 else None)
    bulbs = next_year_alcove(cv, cx, 26, base - 1, w=118, seed=3, spot=False)
    # the booth is out on the floor tonight: only its old microphone stands in the alcove's spot
    for (ry, rx, a) in [(4, 20, 0.12), (3, 13, 0.14), (2, 7, 0.16)]:
        cv.ellipse(cx - rx, base - 3 - ry, rx * 2, ry * 2, C("#f6cf7a", a))
    cv.vline(cx, base - 30, 27, IRON[3]); cv.vline(cx + 1, base - 30, 27, IRON[1])
    cv.line(cx - 6, base - 2, cx, base - 6, IRON[2]); cv.line(cx + 7, base - 2, cx + 1, base - 6, IRON[2])
    cv.rect(cx - 2, base - 37, 6, 8, OUT); cv.rect(cx - 1, base - 36, 4, 6, "#c0c4cc")
    for yy in range(base - 35, base - 30, 2):
        cv.hline(cx - 1, yy, 4, IRON[2])
    cv.px(cx, base - 36, "#fff0c4")
    cv.line(cx + 1, base - 29, cx + 9, base - 22, OUT); cv.line(cx + 9, base - 22, cx + 14, base - 2, OUT)
    lamps = []
    for px in (62, 112, W - 113, W - 63):
        sconce(cv, px, 62, glow=False)
        halo(cv, px, 62, 7, strength=0.1)
        lamps.append((px, 61))
    return cv, bulbs, lamps


def pendant(size=1.0):
    """A brass bell pendant on a chain (sprite at world scale)."""
    w, h = 26, 120
    cv = Canvas(w, h)
    cx = w // 2
    for yy in range(0, h - 18, 3):
        cv.px(cx, yy, BRASS[2]); cv.px(cx, yy + 1, BRASS[1])
    cv.rect(cx - 2, h - 20, 5, 3, BRASS[3])
    cv.poly([(cx - 4, h - 17), (cx + 4, h - 17), (cx + 11, h - 6), (cx - 11, h - 6)], OUT)
    cv.poly([(cx - 3, h - 16), (cx + 3, h - 16), (cx + 10, h - 7), (cx - 10, h - 7)], BRASS[2])
    cv.poly([(cx - 3, h - 16), (cx, h - 16), (cx - 3, h - 7), (cx - 10, h - 7)], BRASS[3])
    cv.rect(cx - 11, h - 6, 23, 2, BRASS[1])
    cv.rect(cx - 6, h - 4, 13, 3, "#fff0c4"); cv.rect(cx - 4, h - 2, 9, 2, "#f6cf7a")
    return cv


def build(project):
    out = os.path.join(project, "assets/art/rooms/U03")
    v = View(horizon=98, cam=52, fill="#120c16")
    v.ground(floor_shader)
    L = int(Z_BACK - Z_NEAR)
    for side in (-1, 1):
        tex = side_wall(side < 0)

        def shade_wall(u, Y, Z, tex=tex, side=side):
            o = texture_lookup(tex, u if side < 0 else L - 1 - u, HALL_H - Y, wrap=False)
            o[..., :3] *= 0.86
            fog(o, Z, "#241a2a", 560, 820, amount=0.35)
            return o
        v.plane((side * WALL_X, Z_NEAR), (side * WALL_X, Z_BACK), shade_wall, y_max=HALL_H)
    flat, bulbs, lamps = back_wall()
    fx0 = int(round(v.vx - flat.w / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - flat.h))
    v.strip(flat.a, fy0, fx0)
    # pendants hanging from the ceiling between viewer and alcove
    pend = []
    for (X, Z, Y) in [(-150, 470, 168), (150, 470, 168), (-95, 610, 186), (95, 610, 186)]:
        spr = pendant()
        sx, sy, s = v.sprite(spr.a, X, Z, Y=Y, anchor=(0.5, 1.0), scale=1.0)
        pend.append((sx, sy - 2 * s))
    v.rows(0, 8, "#0c0a12", 0.5, 0.0)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    # crisp details: chains above the pendants up off the frame
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    res = "res://assets/art/rooms/U03/"
    to_screen = lambda p: [fx0 + p[0], fy0 + p[1]]
    marquee = [to_screen(b) for b in bulbs]
    chase = [{"kind": "blink", "pattern": "".join("1" if k == j else "0" for k in range(3)), "rate": 6.0,
              "rects": [[p[0], p[1], 1, 1, "fff0c4"] for i, p in enumerate(marquee) if i % 3 == j]} for j in range(3)]
    return {
        "far": res + "battle-far.png",
        "layers": chase + [
            {"kind": "twinkle", "points": [to_screen(l) + ["f6cf7a", 1] for l in lamps], "rate": 0.9, "min": 0.6},
            {"kind": "twinkle", "points": [[int(round(x)), int(round(y)), "fff0c4", 2] for (x, y) in pend], "rate": 1.2, "min": 0.7},
            {"kind": "particles", "style": "dust", "count": 18, "rect": [fx0 + flat.w // 2 - 70, 40, 140, 80], "speed": [0, 3], "color": "f6e0b0"},
        ],
    }


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
