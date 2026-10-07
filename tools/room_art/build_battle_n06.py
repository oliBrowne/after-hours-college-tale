"""Battle backdrop for the closed archive (N06): down AUTOCOMPLETE's aisle.

Behind the fighters the archive's stacks run floor to cornice, every few bays split by a server
rack forced in between the books, LEDs flickering. In the middle the wall opens into a long aisle
whose walls are the same: oak shelves of books alternating with racks. Two ladder cable trays run
along the ceiling toward the far end, data pulses racing down them, and over the aisle hangs the lit
settings toggle AUTOCOMPLETE ENABLED. At the end of the aisle, where the closed archive's grille
was, the wall of screens glows: the big chat window (SUGGESTED, > I WANT TO / BECOME A, the cursor
blinking before a ghost suggestion that keeps changing, suggestion chips) between narrow
monitors, rack units along its foot. The floor down the aisle is raised data-floor tiles lit teal
by the screens, stone flags either side, cables taped along the edges; a teal ring marks the spot
where AUTOCOMPLETE stands. Library lamps hang at the front; loose pages drift toward the screens."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON
from lib_norlin import stone_wall, shade_pendant, OAK_DARK, STONE_N
from lib_norlin2 import VAULT
from n06_lib import (stacks_texture, far_screens, toggle_sign, RACK, TEAL, SCREEN, LED, GLOW, GLOW_HI, GHOST2, CORDS, CABLE)
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "N06"
INK = "#10121e"
HAZE = "#11161e"
Z_NEAR = 430.0            # the stacks wall behind the fighters
Z_END = 860.0             # the wall of screens
GAL = 170.0               # half width of the aisle
WALL_H = 172.0            # stacks up to the cornice
CEIL = 200.0              # ceiling over the aisle
SIDE = 720.0              # how far the front stacks wall runs out sideways
AISLE = 66.0              # half width of the raised data floor
TRAYS = [-74.0, 74.0]     # cable trays along the ceiling (X)
FRONT_LAMPS = [(-250.0, 372.0), (250.0, 372.0)]
SPOT = (173.0, 352.0)     # under AUTOCOMPLETE
TEAL_LIGHT = "#54cabc"
SIDE_LAYOUT = [("shelf", 70), ("rack", 30), ("shelf", 96), ("rack", 30), ("rack", 30), ("shelf", 84), ("rack", 30), ("shelf", 120)]
FRONT_LAYOUT = [("rack", 34), ("shelf", 84), ("rack", 34), ("shelf", 120), ("rack", 34), ("shelf", 96)]


def floor_shader(X, Z):
    """Stone flags either side, raised perforated data-floor tiles down the aisle with a teal edge,
    cables along its sides, the teal ring under AUTOCOMPLETE, lamp pools and the screens' glow."""
    v = pal_array(VAULT)
    size = 40.0
    i, j = np.floor(X / size), np.floor(Z / size)
    t = hash2(i, j, 4)
    rgb = np.where(((i + j) % 2 == 0)[:, None], v[3], v[4]) * (0.95 + 0.1 * t[:, None])
    gx, gz = (X / size) % 1, (Z / size) % 1
    rgb[(gx < 0.04) | (gz < 0.05)] = v[1]
    grain = hash2(np.floor(X / 3), np.floor(Z / 4), 9) > 0.88
    rgb[grain] *= 0.94
    # the raised data floor down the aisle
    r = pal_array(RACK)
    ax = np.abs(X)
    aisle = (ax < AISLE) & (Z > Z_NEAR - 40)
    ts = 2 * AISLE / 4
    ti, tj = np.floor((X + AISLE) / ts), np.floor(Z / ts)
    perf = ((ti + tj) % 2 == 0)
    tile = np.where(perf[:, None], r[2], r[3])
    lx, lz = ((X + AISLE) / ts) % 1, (Z / ts) % 1
    tile[(lx < 0.05) | (lz < 0.06)] = r[4]
    tile[(lx > 0.95) | (lz > 0.94)] = r[1]
    holes = perf & (np.floor(X / 3) % 2 == 0) & (np.floor(Z / 3) % 2 == 0) & (lx > 0.12) & (lx < 0.88) & (lz > 0.12) & (lz < 0.88)
    tile[holes] = r[1]
    rgb[aisle] = tile[aisle]
    teal = pal_array(TEAL)
    edge = (np.abs(ax - AISLE) < 1.6) & (Z > Z_NEAR - 40)
    rgb[edge] = teal[3]
    # cable runs taped along both edges of the aisle
    for c, off in ((CABLE[1], 6.0), (CORDS[0], 10.0), (CABLE[2], 13.0)):
        rgb[(np.abs(ax - AISLE - off) < 1.3) & (Z > Z_NEAR - 40)] = np.array(C(c)[:3])
    tape = (np.abs(ax - AISLE - 9.5) < 5) & ((Z % 60.0) < 5) & (Z > Z_NEAR - 40)
    rgb[tape] = np.array(C("#3a3846")[:3])
    # the ring under AUTOCOMPLETE
    rx, rz = SPOT
    d = np.hypot(X - rx, (Z - rz) * 1.25)
    rgb[np.abs(d - 66) < 2.0] = teal[3]
    rgb[np.abs(d - 58) < 1.2] = teal[1]
    ang = np.arctan2((Z - rz) * 1.25, X - rx)
    ticks = (d > 58) & (d < 66) & (np.abs(((ang / (2 * np.pi) * 16) % 1) - 0.5) > 0.4)
    rgb[ticks] = teal[2]
    for (lx_, lz_) in FRONT_LAMPS:
        warm_light(rgb, np.hypot(X - lx_, (Z - lz_) * 0.8), 170, strength=0.3)
    warm_light(rgb, np.hypot(X * 0.8, (Z - Z_END) * 0.5), 200, colour=TEAL_LIGHT, strength=0.3)
    warm_light(rgb, np.hypot(X - rx, (Z - rz) * 1.25), 80, colour=TEAL_LIGHT, strength=0.18)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 620, 1200, amount=0.45)
    return out


def ceiling_shader(X, Z):
    """Dark ceiling panels, two ladder cable trays running toward the screens, a teal light strip
    down the middle."""
    rgb = np.zeros((X.shape[0], 3), np.float32)
    rgb[:] = np.array(C(OAK_DARK[2])[:3])
    cz = (Z / 60.0) % 1
    rgb[cz < 0.08] = np.array(C(OAK_DARK[3])[:3])
    for tx in TRAYS:
        d = np.abs(X - tx)
        tray = d < 14
        rgb[tray] = np.array(C(CABLE[1])[:3])
        rgb[tray & (d > 11.5)] = np.array(C(RACK[3])[:3])                          # rails
        rgb[tray & (d < 11.5) & ((Z % 14.0) < 2.2)] = np.array(C(RACK[2])[:3])      # rungs
        for k, (c, off) in enumerate(((CORDS[0], -6.0), (CABLE[2], -2.0), (CORDS[1], 3.0), (CABLE[0], 7.0))):
            rgb[np.abs(X - tx - off) < 1.6] = np.array(C(c)[:3])
    strip = np.abs(X) < 3.5
    rgb[strip] = np.array(C(TEAL[3])[:3])
    rgb[strip & ((Z % 40.0) < 4)] = np.array(C(TEAL[1])[:3])
    warm_light(rgb, np.hypot(X, (Z - Z_END) * 0.5), 140, colour=TEAL_LIGHT, strength=0.25)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 520, 1100, amount=0.55)
    return out


def ghost_frame(crop, word, colour):
    cv = Canvas(crop.shape[1], crop.shape[0])
    cv.a[:] = crop
    text(cv, word, 0, 0, colour)
    return cv


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#0e0c12")
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=CEIL, z_max=Z_END)
    v.ground(floor_shader, z_max=Z_END)
    # far wall: dark stone first (the screens go on crisp after the reduction)
    s = v.scale(Z_END)
    Wp = int(round(2 * GAL * s)) + 2
    Hp = int(round(CEIL * s))
    fw = Canvas(Wp, Hp, seed=3)
    stone_wall(fw, 0, 0, Wp, Hp, pal=[shade(c, -0.36) for c in STONE_N], seed=12, course=4)
    far_x, far_y = int(round(v.vx - Wp / 2)), int(round(v.ground_y(Z_END) - Hp))
    v.strip(fw.a, far_y, far_x)
    # aisle walls: stacks and racks to the cornice, stone above
    side_tex, side_leds = stacks_texture(int(Z_END - Z_NEAR) + 20, int(WALL_H) + 12, seed=21, layout=SIDE_LAYOUT)
    for (u, vv, key) in side_leds:                     # LEDs fat enough to survive the distance
        side_tex.rect(u, vv, 2, 1, LED[key])
    stone = Canvas(400, 80, seed=4)
    stone_wall(stone, 0, 0, 400, 80, pal=[shade(c, -0.25) for c in STONE_N], seed=14, course=6)
    for side in (-1, 1):
        def shade_side(u, Y, Z, side=side):
            o = texture_lookup(side_tex.a, u, WALL_H + 12 - Y, wrap=False)
            up = Y > WALL_H + 10
            if up.any():
                o[up] = texture_lookup(stone.a, u[up], CEIL - Y[up], wrap=True)
            o[..., 3] = 1
            o[..., :3] *= 0.84 if side < 0 else 0.76
            warm_light(o[..., :3], np.hypot((Z - Z_END) * 0.6, (Y - 60) * 0.8), 220, colour=TEAL_LIGHT, strength=0.22)
            return fog(o, Z, HAZE, 600, 1200, amount=0.5)
        v.plane((side * GAL, Z_NEAR), (side * GAL, Z_END), shade_side, y_max=CEIL)
    # the front stacks wall behind the fighters, either side of the aisle mouth
    front_tex, front_leds = stacks_texture(int(SIDE), int(WALL_H) + 12, seed=31, layout=FRONT_LAYOUT)
    upper = Canvas(1440, 140, seed=5)
    stone_wall(upper, 0, 0, 1440, 140, pal=[shade(c, -0.12) for c in STONE_N], seed=16, course=6)

    def front(X, Y):
        o = np.zeros(X.shape + (4,), np.float32)
        low = Y <= WALL_H + 12
        u = np.abs(X) - GAL
        o[low] = texture_lookup(front_tex.a, u[low], WALL_H + 12 - Y[low], wrap=False)
        o[~low] = texture_lookup(upper.a, X[~low] + 720, 400 - Y[~low], wrap=True)
        o[..., 3] = 1
        for (lx, lz) in FRONT_LAMPS:
            warm_light(o[..., :3], np.hypot(X - lx, (Y - 150) * 1.1), 200, strength=0.26)
        o[..., :3] *= 0.9
        return o
    v.back(Z_NEAR, front, region=lambda X, Y: (np.abs(X) > GAL) & (Y >= 0))
    v.back(Z_NEAR, lambda X, Y: texture_lookup(upper.a, X + 720, 400 - Y, wrap=True),
           region=lambda X, Y: (np.abs(X) <= GAL) & (Y > CEIL - 4))
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # Crisp pieces at 1:1: the screens at the end of the aisle, the mouth's frame, the hung sign,
    # the front lamps.
    scr, pts = far_screens(Wp - 2, Hp - 2, seed=7)
    cv.paste(scr, far_x + 1, far_y + 1)
    glows = []
    for side in (-1, 1):
        x, _ = v.project(side * GAL, 0, Z_NEAR)
        x = int(round(x))
        _, yb = v.project(0, 0, Z_NEAR)
        cv.rect(x - 3 if side > 0 else x - 2, 0, 5, int(round(yb)), OUT)
        cv.rect(x - 2 if side > 0 else x - 1, 0, 3, int(round(yb)), RACK[3])
        cv.vline(x - 1 if side < 0 else x - 2, 0, int(round(yb)), RACK[5])
        for yy in range(2, int(round(yb)), 5):
            cv.px(x - 1 if side < 0 else x - 1, yy, RACK[1])
    # the toggle sign hung over the aisle on chains from the ceiling
    bz = 600.0
    bx, by = v.project(0, 178, bz)
    _, btop = v.project(0, CEIL, bz)
    board = Canvas(160, 22)
    x0, y0, w, h = toggle_sign(board, 80, 2, "AUTOCOMPLETE ENABLED", compact=True, halo=False)
    px_, py_ = int(round(bx - 80)), int(round(by))
    for hx in (x0 + 8, x0 + w - 9):
        for yy in range(max(0, int(round(btop))), py_ + 2, 2):
            cv.px(px_ + hx, yy, IRON[3]); cv.px(px_ + hx, yy + 1, IRON[1])
    cv.paste(board, px_, py_)
    glows.append([px_ + x0 + 12, py_ + y0 + 8, "96ecda", 1])
    for (lx, lz) in FRONT_LAMPS:
        x, y = v.project(lx, 150, lz)
        shade_pendant(cv, int(round(x)), int(round(y)), chain_top=0, w=18)
        glows.append([int(round(x)), int(round(y)) + 1, "fde9b6", 1])

    # the ghost suggestion after the cursor: DOCTOR painted, the others as frames
    gx, gy = pts["ghost"]
    gx, gy = gx + far_x + 1, gy + far_y + 1
    crop = cv.a[gy:gy + 10, gx:gx + 38].copy()
    text(cv, "DOCTOR", gx, gy, GHOST2)
    for name, word, col in (("battle-ghost-lawyer.png", "LAWYER", GHOST2), ("battle-ghost-ceo.png", "CEO", GHOST2),
                            ("battle-ghost-accepted.png", "DOCTOR", GLOW)):
        ghost_frame(crop, word, col).save(os.path.join(out, name))
    # front-wall LEDs: half lit in the painting, the rest flicker in layers
    s0 = v.scale(Z_NEAR)
    screen_leds = []
    for (u, vv, key) in front_leds:
        for side in (-1, 1):
            X = side * (GAL + u + 0.5)
            Y = WALL_H + 12 - (vv + 0.5)
            sx, sy = v.project(X, Y, Z_NEAR)
            sx, sy = int(round(sx)), int(round(sy))
            if 0 <= sx < 640 and 0 <= sy < 136 and not (392 <= sx <= 628 and sy <= 70) and not (sx <= 66 and sy <= 26):
                screen_leds.append((sx, sy, key))
    for (sx, sy, key) in pts["leds"]:
        screen_leds.append((sx + far_x + 1, sy + far_y + 1, key))
    rng = np.random.default_rng(12)
    order = rng.permutation(len(screen_leds))
    steady = [screen_leds[int(i)] for i in order[: len(order) // 2]]
    busy = [screen_leds[int(i)] for i in order[len(order) // 2:]]
    for (sx, sy, key) in steady:
        cv.px(sx, sy, LED[key])
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    for k, (pattern, rate) in enumerate((("1101", 3.0), ("0110", 4.4), ("1011", 2.3), ("1110010", 6.0))):
        layers.append({"kind": "blink", "pattern": pattern, "rate": rate,
                       "rects": [[x, y, 1, 1, LED[key][1:]] for (x, y, key) in busy[k::4]]})
    cx_, cy_, cw_, ch_ = pts["cursor"]
    layers.append({"kind": "blink", "pattern": "10", "rate": 2.0,
                   "rects": [[cx_ + far_x + 1, cy_ + far_y + 1, cw_, ch_, GLOW_HI[1:]]]})
    for name, pattern in (("battle-ghost-lawyer.png", "00100000"), ("battle-ghost-ceo.png", "00001000"),
                          ("battle-ghost-accepted.png", "00000011")):
        layers.append({"kind": "blink", "pattern": pattern, "rate": 1.2, "texture": res + name, "x": gx, "y": gy})
    # data pulses racing down the ceiling trays toward the screens
    for tx in TRAYS:
        a = v.project(tx, CEIL, 520.0)
        b = v.project(tx, CEIL, Z_END - 10)
        layers.append({"kind": "movers", "from": [round(a[0]), round(a[1])], "to": [round(b[0]), round(b[1])],
                       "count": 3, "period": 1.8, "size": [3, 1], "color": GLOW[1:], "ease": "out"})
    glows.append([int(v.vx), int(round(v.project(0, CEIL * 0.55, Z_END)[1])), "96ecda", 0])
    layers += [
        {"kind": "twinkle", "points": glows, "rate": 1.2, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 20, "rect": [180, 30, 280, 110], "speed": [1, 2], "color": "c8f4e8"},
        {"kind": "fauna", "fauna": [{"kind": "loose_page", "x": 160, "y": 40, "fly": 7.0, "rate": 3.0},
                                    {"kind": "loose_page", "x": 420, "y": 92, "fly": 5.0, "rate": 2.6},
                                    {"kind": "loose_page", "x": 300, "y": 20, "fly": 9.0, "rate": 3.4}]},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
