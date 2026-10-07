"""Battle backdrop for the moving stacks (N04): standing on the green runner in the front aisle,
looking straight down the main aisle between the mobile ranges.

The first range on each side shows its whole book face; beyond, the aisle is walled by the
ranges' enamelled end panels, each with its range card and crank wheel, steel rails crossing the
floor under every range. Halfway down on the left the marked passage stands open, a lamp lit
inside it. Overhead the glass deck of the upper tier glows in its iron grid; caged lamps hang
import paths
from it, and the MARKED PASSAGE board hangs over the aisle with its signal lamp blinking. At the
far end the closed archive's banded door waits under its carved lintel. Correction slips drift
through the air, dust turns in the lamplight, a lamp swings on its chain, the near crank turns."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON
from lib_norlin import (plaster_wall, ceiling_band, book_row, stone_wall, quoins, OAK, OAK_DARK, BRASS, PAGE,
                        CARPET_GREEN, GILT, STONE_N, LIME)
from lib_norlin2 import (handwheel, cage_lamp, archive_door, passage_sign, gallery_rail, STACK, CORK, RAIL, HAZARD,
                         RED_PENCIL)
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "N04"
INK = "#10121e"
HAZE = "#161a1e"
Z_NEAR = 470.0            # front faces of the first ranges
Z_END = 1240.0            # the archive wall at the end of the aisle
AISLE = 104.0             # half width of the main aisle
RANGE_D = 72.0            # depth of one range (end panel width)
RANGE_H = 150.0
DECK_H = 176.0            # underside of the glass deck overhead
SIDE_L = 520.0            # how far the ranges run out sideways
PASSAGE = (830.0, 902.0)  # the open marked passage on the left (z range)
RUNNER = (318.0, 382.0)   # green runner across the front aisle (z range)
LAMPS = [(0, 560), (0, 760), (0, 1000), (-210, 400), (210, 400)]
LAMP_Y = 150.0


def ranges(side):
    """z starts of the ranges on one side of the aisle (the left side skips the open passage)."""
    zs = []
    z = Z_NEAR
    while z < Z_END - 20:
        if not (side < 0 and PASSAGE[0] - 1 <= z < PASSAGE[1] - 1):
            zs.append(z)
        z += RANGE_D
    return zs


def floor_shader(X, Z):
    """Cork tiles, the green runner across the front aisle, tread plate and rails under each
    range (rails cross the main aisle), the passage marked in yellow, lamp pools."""
    cork = pal_array(CORK)
    size = 30.0
    i, j = np.floor(X / size), np.floor(Z / (size * 0.9))
    t = hash2(i, j, 4)
    rgb = np.where(((i + j) % 2 == 0)[:, None], cork[3], cork[4]) * (0.96 + 0.08 * t[:, None])
    gx, gz = (X / size) % 1, (Z / (size * 0.9)) % 1
    rgb[(gx < 0.05) | (gz < 0.06)] = cork[1]
    grain = hash2(np.floor(X / 3), np.floor(Z / 4), 9) > 0.86
    rgb[grain] *= 0.93
    # under each range: steel tread plate with two rails, rails continuing across the aisle
    plate = pal_array(["#3c3844", "#4c4856", "#2a2830"])
    rl = pal_array(RAIL)
    for side in (-1, 1):
        for z0 in ranges(side):
            under = (side * X > AISLE - 6) & (Z >= z0 + 4) & (Z < z0 + RANGE_D - 4)
            rgb[under] = plate[0]
            dots = under & (hash2(np.floor(X / 6), np.floor(Z / 4), 3) > 0.7)
            rgb[dots] = plate[1]
    for z0 in sorted(set(ranges(-1)) | set(ranges(1))):
        for zr in (z0 + 16, z0 + RANGE_D - 18):
            band = np.abs(Z - zr)
            rgb[band < 3.5] = rl[0]
            rgb[band < 1.8] = rl[2]
            rgb[(Z - zr > -1.8) & (Z - zr < -0.4)] = rl[3]
    # the marked passage: yellow dashes along its mouth, hatching on the floor inside it
    mz0, mz1 = PASSAGE
    mouth = (X < -AISLE + 30) & (X > -SIDE_L) & (Z > mz0) & (Z < mz1)
    rgb[mouth] = cork[3] * 0.95
    hatch = mouth & ((((X + Z) / 14.0) % 1) < 0.3) & ((X > -AISLE - 30) | (X < -SIDE_L + 40))
    rgb[hatch] = np.array(C(HAZARD[1])[:3])
    for zz in (mz0 + 3, mz1 - 3):
        edge = (np.abs(Z - zz) < 2.5) & (X < -AISLE + 30) & (((X / 16.0) % 1) < 0.55)
        rgb[edge] = np.array(C(HAZARD[2])[:3])
    # the green runner across the front aisle
    g = pal_array(CARPET_GREEN)
    run = (Z > RUNNER[0]) & (Z < RUNNER[1])
    rgb[run] = g[2]
    rgb[run & ((Z - RUNNER[0] < 7) | (RUNNER[1] - Z < 7))] = g[3]
    rgb[run & ((np.abs(Z - RUNNER[0] - 5) < 1.4) | (np.abs(RUNNER[1] - Z - 5) < 1.4))] = g[5]
    lx = (X % 52.0) - 26
    zc = (RUNNER[0] + RUNNER[1]) / 2
    loz = run & (np.abs(lx) * 0.7 + np.abs(Z - zc) < 14)
    rgb[loz] = g[4]
    rgb[run & (np.abs(lx) * 0.7 + np.abs(Z - zc) < 4)] = g[6]
    for (lx_, lz) in LAMPS:
        warm_light(rgb, np.hypot(X - lx_, (Z - lz) * 0.7), 120, strength=0.34)
    warm_light(rgb, np.hypot(X + AISLE + 120, (Z - (mz0 + mz1) / 2) * 0.8), 150, strength=0.4)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 700, 1500, amount=0.55)
    return out


def deck_shader(X, Z):
    """The underside of the upper tier's glass deck: iron joists and a grid of glass tiles glowing
    with the lamps above (brighter over the aisle)."""
    rgb = np.zeros((X.shape[0], 3), np.float32)
    rgb[:] = np.array(C(IRON[1])[:3])
    cx, cz = (X / 22.0) % 1, (Z / 22.0) % 1
    glass = (cx > 0.14) & (cz > 0.14)
    t = hash2(np.floor(X / 22.0), np.floor(Z / 22.0), 6)
    gcol = pal_array(["#2e3e3a", "#405650", "#506a60", "#8aa894"])
    rgb[glass] = gcol[1] * (1 - t[glass, None] * 0.6) + gcol[2] * (t[glass, None] * 0.6)
    rgb[glass & (cx < 0.24) & (cz < 0.24)] = gcol[3]
    for (lx, lz) in LAMPS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.8), 90, colour="#f6cf7a", strength=0.35)
    joist = (np.abs(Z % 132.0) < 10)
    rgb[joist] = np.array(C(IRON[2])[:3])
    rgb[joist & (np.abs(Z % 132.0) < 2)] = np.array(C(IRON[3])[:3])
    over_aisle = np.abs(X) < AISLE + 20
    rgb[~over_aisle & glass] *= 0.7
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 500, 1400, amount=0.7)
    return out


def end_panel_texture(n):
    """The aisle-facing end panels of n ranges in a row, laid flat along the wall (u = depth):
    each one green enamel with a recessed field, a range card, a three-spoke crank wheel, rivets,
    and the riveted carriage at the floor; a dark seam between neighbours."""
    D, Hh = int(RANGE_D), int(RANGE_H)
    cv = Canvas(D * n, Hh)
    rng = np.random.default_rng(4)
    for k in range(n):
        x0 = k * D
        cv.rect(x0, 0, D, Hh, STACK[3])
        cv.rect(x0, 0, D, 7, STACK[4]); cv.hline(x0, 0, D, STACK[5])
        cv.rect(x0 + 6, 14, D - 12, Hh - 34, STACK[2]); cv.hline(x0 + 6, 14, D - 12, STACK[1]); cv.vline(x0 + 6, 14, Hh - 34, STACK[1])
        cv.hline(x0 + 6, Hh - 21, D - 12, STACK[4])
        # range card
        cv.rect(x0 + D // 2 - 15, 20, 30, 14, OUT); cv.rect(x0 + D // 2 - 14, 21, 28, 12, BRASS[2]); cv.rect(x0 + D // 2 - 12, 23, 24, 8, PAGE[3])
        cv.hline(x0 + D // 2 - 9, 26, 18, "#3a3040"); cv.hline(x0 + D // 2 - 9, 28, 10 + int(rng.integers(0, 8)), "#3a3040")
        # crank wheel
        handwheel(cv, x0 + D // 2, 74, 15, spokes=3, angle=float(rng.uniform(0, 2)))
        for ry in range(10, Hh - 16, 12):
            cv.px(x0 + 3, ry, STACK[5]); cv.px(x0 + D - 4, ry, STACK[4])
        # carriage
        cv.rect(x0, Hh - 14, D, 14, IRON[2]); cv.hline(x0, Hh - 14, D, IRON[4])
        for rx in range(x0 + 4, x0 + D - 2, 8):
            cv.px(rx, Hh - 11, IRON[4])
        for wx in (x0 + 14, x0 + D - 14):
            cv.ellipse(wx - 5, Hh - 9, 11, 9, OUT); cv.ellipse(wx - 4, Hh - 8, 9, 7, IRON[1])
        cv.rect(x0 + D - 3, 0, 3, Hh, "#0c0e10")
    return cv.a


def range_face_texture(length, seed=0, dim=0.0):
    """A range's long book face laid flat (u = distance out from the aisle): green steel uprights
    every bay, steel shelves of books, a top cap with range cards, the carriage at the floor."""
    Hh = int(RANGE_H)
    cv = Canvas(length, Hh, seed=seed)
    cv.rect(0, 0, length, Hh, OAK_DARK[1])
    cv.rect(0, 0, length, 8, STACK[4]); cv.hline(0, 0, length, STACK[5]); cv.hline(0, 7, length, STACK[1])
    carriage = 16
    shelf = 26
    n = max(1, (Hh - carriage - 8) // shelf)
    shelf = (Hh - carriage - 8) / n
    rows = [int(round(8 + shelf * (k + 1))) for k in range(n)]
    shelf = int(shelf)
    bay = 62
    for bx in range(0, length, bay):
        b1 = min(length, bx + bay - 5)
        for k, sy in enumerate(rows):
            book_row(cv, bx + 1, sy - 3, b1 - bx - 2, shelf - 6, seed=seed * 131 + bx * 3 + k, dim=dim)
        cv.rect(b1, 8, 5, Hh - 8 - carriage, STACK[3]); cv.vline(b1, 8, Hh - 8 - carriage, STACK[5]); cv.vline(b1 + 4, 8, Hh - 8 - carriage, STACK[1])
    for sy in rows:
        cv.rect(0, sy - 3, length, 3, STACK[3]); cv.hline(0, sy - 3, length, STACK[5])
    cv.rect(0, Hh - carriage, length, carriage, IRON[2]); cv.hline(0, Hh - carriage, length, IRON[4])
    for rx in range(4, length, 9):
        cv.px(rx, Hh - carriage + 3, IRON[4])
    # the inner end stile, facing the aisle
    cv.rect(0, 0, 9, Hh - carriage, STACK[4]); cv.vline(0, 0, Hh - carriage, STACK[5]); cv.vline(8, 0, Hh - carriage, STACK[1])
    return cv.a


def far_wall(Wp, Hp):
    """The end of the aisle at its on-screen size: the archive's sandstone wall, the banded door
    under the carved lintel, a caged lamp, the gallery rail crossing above."""
    cv = Canvas(Wp, Hp, seed=3)
    stone_wall(cv, 0, 0, Wp, Hp, pal=[shade(c, -0.25) for c in STONE_N], seed=12, course=4)
    archive_door(cv, Wp // 2, Hp, w=22, h=36, label="ARCHIVE")
    cv.rect(Wp // 2 + 18, Hp - 34, 4, 1, IRON[2])
    cv.a[..., :3] *= 0.9
    return cv


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    v = View(horizon=98, cam=52, fill="#0e0f14")
    v.ground(deck_shader, y_from=0, y_to=v.h0, height=DECK_H, z_max=Z_END)
    v.ground(floor_shader, z_max=Z_END)
    # far wall at the end of the aisle
    s = v.scale(Z_END)
    Wp = int(round(2 * (AISLE + 40) * s)) + 2
    Hp = int(round(DECK_H * s))
    fw = far_wall(Wp, Hp)
    fx0 = int(round(v.vx - Wp / 2))
    fy0 = int(round(v.ground_y(Z_END) - Hp))
    v.strip(fw.a, fy0, fx0)
    # inside the marked passage: the next range's book face, lit
    face_tex = range_face_texture(int(SIDE_L), seed=7, dim=0.0)
    def passage_face(X, Y):
        o = texture_lookup(face_tex, -X - AISLE, RANGE_H - Y, wrap=False)
        warm_light(o[..., :3], np.hypot(X + AISLE + 120, (Y - 70) * 1.2), 160, strength=0.3)
        return fog(o, np.full(X.shape, PASSAGE[1]), HAZE, 700, 1500, amount=0.55)
    v.back(PASSAGE[1], passage_face, region=lambda X, Y: (X < -AISLE) & (X > -SIDE_L) & (Y >= 0) & (Y <= RANGE_H))
    # the end panels walling the aisle, both sides
    for side in (-1, 1):
        zs = ranges(side)
        tex = end_panel_texture(len(zs) + 1)
        def shade_panels(u, Y, Z, tex=tex, zs=zs, side=side):
            k = np.searchsorted(np.array(zs), Z, side="right") - 1
            k = np.clip(k, 0, len(zs) - 1)
            local = Z - np.array(zs)[k]
            inside = (local >= 0) & (local < RANGE_D)
            uu = k * RANGE_D + (local if side < 0 else RANGE_D - 1 - local)
            o = texture_lookup(tex, uu, RANGE_H - Y, wrap=False)
            o[~inside, 3] = 0
            o[..., :3] *= 0.86 if side < 0 else 0.78
            for (lx, lz) in LAMPS[:3]:
                warm_light(o[..., :3], np.hypot((Z - lz) * 0.9, (Y - 120) * 0.8), 110, strength=0.3)
            return fog(o, Z, HAZE, 700, 1500, amount=0.55)
        v.plane((side * AISLE, Z_NEAR), (side * AISLE, Z_END), shade_panels, y_max=RANGE_H)
    # the first ranges' book faces, full width, framing the fighters
    for side in (-1, 1):
        tex = range_face_texture(int(SIDE_L), seed=11 + side, dim=0.12)
        def near_face(X, Y, tex=tex, side=side):
            o = texture_lookup(tex, side * X - AISLE, RANGE_H - Y, wrap=False)
            for (lx, lz) in LAMPS[-2:]:
                warm_light(o[..., :3], np.hypot(X - lx, (Y - 100) * 1.3), 170, strength=0.22)
            o[..., :3] *= 0.9
            return o
        v.back(Z_NEAR, near_face, region=lambda X, Y, side=side: (side * X > AISLE) & (side * X < AISLE + SIDE_L) & (Y >= 0) & (Y <= RANGE_H))
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # Crisp pieces at 1:1: the gallery rail edge over the near ranges, caged lamps on their chains,
    # the MARKED PASSAGE board over the aisle, crank wheels on the near ranges' aisle ends.
    glows = []
    _, deck_y = v.project(0, DECK_H, Z_NEAR - 10)
    for (lx, lz) in sorted(LAMPS, key=lambda p: -p[1]):
        x, y = v.project(lx, LAMP_Y, lz)
        _, ytop = v.project(lx, DECK_H, lz)
        cage_lamp(cv, int(round(x)), int(round(y)), max(0, int(round(ytop))))
        glows.append([int(round(x)), int(round(y)) - 4, "fde9b6", 1])
    # a small signal lamp on top of every end panel (green; one amber far down the right side)
    for side in (-1, 1):
        for z0 in ranges(side):
            ix, iy = v.project(side * AISLE, RANGE_H - 4, z0 + RANGE_D / 2)
            col = "7ad08a" if not (side > 0 and 900 < z0 < 1000) else "f0a848"
            cv.px(int(round(ix)), int(round(iy)), "#" + col)
            if z0 < 760:
                glows.append([int(round(ix)), int(round(iy)), col, 0])
    sign = passage_sign(False)
    sx, sy = v.project(0, 168, 690)
    sign_x, sign_y = int(round(sx - sign.w / 2)), int(round(sy)) - 10
    _, top_y = v.project(0, DECK_H, 690)
    sub = Canvas(sign.w, sign.h)
    sub.a = sign.a.copy()
    sub.a[:10] = 0
    cv.paste(sub, sign_x, sign_y)
    for hx in (8, sign.w - 7):
        cv.vline(sign_x + hx, int(round(top_y)), sign_y + 10 - int(round(top_y)), IRON[3])
    glows = [g for g in glows if not (sign_x - 2 <= g[0] <= sign_x + sign.w + 2 and sign_y + 8 <= g[1] <= sign_y + sign.h + 2)]
    lamp_x = sign_x + sign.w // 2 - text_width("TURN CRANK") // 2 + 4 - 8
    lamp_y = sign_y + 10 + 18
    wheels = []
    for side in (-1, 1):
        wx, wy = v.project(side * (AISLE + 22), 76, Z_NEAR)
        wheels.append((int(round(wx)), int(round(wy))))
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    res = f"res://assets/art/rooms/{ROOM}/"
    # three frames of the near crank wheels turning
    layers = []
    for k in range(3):
        fr = Canvas(640, 360)
        for (wx, wy) in wheels:
            handwheel(fr, wx, wy, 11, spokes=3, rim=["#16141f", "#3a2c1c", "#7a5428", "#a87c38", "#f0d48a"], angle=k * 2 * np.pi / 9)
        ys, xs = np.where(fr.a[..., 3] > 0)
        x0, y0, x1, y1 = xs.min(), ys.min(), xs.max() + 1, ys.max() + 1
        crop = Canvas(x1 - x0, y1 - y0)
        crop.a = fr.a[y0:y1, x0:x1].copy()
        name = f"battle-wheel-{k}.png"
        crop.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(3)), "rate": 3.0,
                       "texture": res + name, "x": int(x0), "y": int(y0)})
    sway_x, sway_y = v.project(0, LAMP_Y, 560)
    layers += [
        {"kind": "beam", "x": int(round(sway_x)), "y": int(round(sway_y)), "angle": 90, "sweep": 7, "period": 6.5, "phase": 0.0,
         "length": 70, "width": 70, "color": "fde9b6", "alpha": 0.14, "floor": int(round(v.ground_y(560)))},
        {"kind": "blink", "pattern": "10", "rate": 1.6, "rects": [[lamp_x - 2, lamp_y, 4, 4, "ffb070"], [lamp_x - 1, lamp_y, 1, 1, "fff0c4"]]},
        {"kind": "twinkle", "points": glows, "rate": 1.3, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [200, 30, 240, 120], "speed": [1, 3], "color": "fde9b6"},
        {"kind": "fauna", "fauna": [{"kind": "loose_page", "x": 120, "y": 60, "fly": 8.0, "rate": 3.0},
                                    {"kind": "loose_page", "x": 470, "y": 34, "fly": 6.0, "rate": 2.5}]},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
