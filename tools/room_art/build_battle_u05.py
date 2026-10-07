"""Battle backdrop for the repair landing (U05): the fight happens on the sealed concrete of the
landing, looking toward the service doorway that drops to the lanes. The camera stands a little
higher than usual so the open well in the floor reads: a slot of block wall falling away into pink
and teal neon, ringed with a safety rail. Painted block walls with a teal dado, a red sprinkler main
and conduit running down the low ceiling, caged bulbs, Mags's punch clock and key box on the left,
the humming access panel on the right with its TOMORROW fuse flickering."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from props import OUT, IRON, AMBER
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_umc import (BLOCK, DADO, CONCRETE, SAFETY, EXIT_GREEN, PAPER, SHADOW, BRASS, KRAFT,
                     block_wall, conduit_run, junction_box, punch_clock, key_cabinet, pegboard, extinguisher,
                     hazard_band, service_doorway, caged_bulb, halo, bolt)

INK = "#10121e"
HORIZON, CAM = 84, 66          # a little higher than the default so the floor and the well read
Z_NEAR = 200.0
Z_BACK = 660.0
WALL_X = 270.0
CEIL = 165.0
DADO_Y = 34.0                  # teal dado height on the walls
WELL = (-110.0, 400.0, 110.0, 570.0)   # X0, Z0, X1, Z1 of the open well
SHAFT = 300.0
DOOR_X = -40.0                 # service doorway on the back wall
PANEL_Z = (350, 400)           # access panel on the right wall (Z span)
BULBS = [(-70.0, 450.0), (120.0, 540.0), (-60.0, 620.0)]   # caged bulbs (X, Z) hanging from the ceiling


def floor_decal():
    """Markings on the landing floor, laid out in world units: column = X + WALL_X, row = Z_BACK - Z
    (row 0 is the far end, so text reads the right way up on screen)."""
    W, Hh = int(2 * WALL_X), int(Z_BACK - Z_NEAR)
    cv = Canvas(W, Hh)
    col = lambda X: int(X + WALL_X)
    row = lambda Z: int(Z_BACK - Z)
    x0, z0, x1, z1 = WELL
    # safety margin round the well: a painted yellow band with a dark inner edge
    for (ax, ay, aw, ah) in [(col(x0) - 16, row(z1) - 16, col(x1) - col(x0) + 32, 16),
                             (col(x0) - 16, row(z0), col(x1) - col(x0) + 32, 16),
                             (col(x0) - 16, row(z1), 16, row(z0) - row(z1)),
                             (col(x1), row(z1), 16, row(z0) - row(z1))]:
        cv.rect(ax, ay, aw, ah, C(SAFETY[2], 0.8))
    cv.rect(col(x0) - 4, row(z1) - 4, col(x1) - col(x0) + 8, row(z0) - row(z1) + 8, "#1e1a20")
    # aisle line along the left, dashed
    for z in range(int(Z_NEAR), int(Z_BACK), 1):
        if (z // 18) % 3 != 0:
            cv.rect(col(-205), row(z), 4, 1, C(SAFETY[2], 0.7))
    # cart bay by the left wall
    for (ax, ay, aw, ah) in [(col(-282), row(700), 70, 3), (col(-282), row(600), 70, 3), (col(-215), row(700), 3, 100)]:
        cv.rect(ax, ay, aw, ah, C(SAFETY[2], 0.6))
    # DOWN with an arrow pointing at the doorway
    cx, cz = col(DOOR_X), row(700)
    cv.rect(cx - 5, cz, 10, 30, C(SAFETY[2], 0.75))
    cv.poly([(cx - 16, cz + 2), (cx + 16, cz + 2), (cx, cz - 16)], C(SAFETY[2], 0.75))
    big = Canvas(30, 12)
    text(big, "DOWN", 3, 0, SAFETY[2])
    for yy in range(12):
        for xx in range(30):
            if big.a[yy, xx, 3] > 0.5:
                cv.rect(cx - 30 + xx * 2, cz + 34 + yy * 2, 2, 2, C(SAFETY[2], 0.75))
    # a drain, an oil stain, washers and clippings near the right wall (the bench is off to the right)
    cv.ellipse(col(180) - 14, row(470) - 7, 28, 14, CONCRETE[1]); cv.ellipse(col(180) - 12, row(470) - 5, 24, 10, "#2a262c")
    for gx in range(col(180) - 8, col(180) + 9, 4):
        cv.rect(gx, row(470) - 4, 2, 8, CONCRETE[4])
    cv.ellipse(col(210) - 30, row(540) - 10, 60, 20, C(CONCRETE[0], 0.45))
    rng = np.random.default_rng(3)
    for _ in range(40):
        cv.rect(col(150) + int(rng.integers(0, 120)), row(560) + int(rng.integers(0, 60)), 2, 1,
                ["#c84a3c", "#c0c4cc", "#e8b45c"][int(rng.integers(3))])
    return cv.a


DECAL = None


def floor_shader(X, Z):
    """Sealed concrete in 48-unit slabs with saw-cut joints, the decal of markings, pools under the
    bulbs, the lanes' neon spilling up out of the well."""
    slab = 48.0
    cx, cz = np.floor(X / slab), np.floor(Z / slab)
    fx, fz = X / slab - cx, Z / slab - cz
    c = pal_array(CONCRETE)
    tone = hash2(cx, cz, 5)
    rgb = c[4] * (1 - tone[:, None] * 0.5) + c[3] * tone[:, None] * 0.5
    mott = hash2(np.floor(X / 7), np.floor(Z / 5), 9)
    rgb = rgb * (0.95 + 0.07 * mott[:, None])
    rgb[(fx < 0.025) | (fz < 0.025)] = c[1]
    d = texture_lookup(DECAL, X + WALL_X, Z_BACK - Z, wrap=False)
    a = d[:, 3:4]
    rgb = rgb * (1 - a) + d[:, :3] * a
    for (bx, bz) in BULBS:
        warm_light(rgb, np.hypot(X - bx, (Z - bz) * 1.8), 120, colour="#f6cf7a", strength=0.3)
    x0, z0, x1, z1 = WELL
    # neon spill round the rim of the well
    dist = np.hypot(np.maximum(0, np.maximum(x0 - X, X - x1)), np.maximum(0, np.maximum(z0 - Z, Z - z1)) * 1.4)
    warm_light(rgb, dist + np.abs(X + 30) * 0.15, 70, colour="#ff7aa8", strength=0.22)
    warm_light(rgb, dist + np.abs(X - 70) * 0.25, 46, colour="#58e0d0", strength=0.16)
    # warm spill from the atrium stair behind the camera
    warm_light(rgb, np.hypot((X + 200) * 0.8, (Z - 300) * 1.5), 140, colour="#f6c27a", strength=0.18)
    out = rgba_of(rgb)
    hole = (X > x0) & (X < x1) & (Z > z0) & (Z < z1)
    out[hole | (np.abs(X) > WALL_X) | (Z > Z_BACK), 3] = 0.0
    fog(out, Z, "#1c1622", 600, 900, amount=0.4)
    return out


def ceiling_shader(X, Z):
    """The low slab ceiling: board-marked concrete, the red sprinkler main and a run of conduits,
    a cable tray, everything converging on the doorway."""
    c = pal_array(BLOCK)
    tone = hash2(np.floor(X / 60), np.floor(Z / 22), 2)
    rgb = c[1] * (1 - tone[:, None] * 0.4) + c[2] * tone[:, None] * 0.4
    rgb[(np.abs((X % 60)) < 1.5)] = c[0]
    for (px, w, col, hi) in [(-215.0, 9.0, "#8a3a32", "#b8584a"), (150.0, 4.0, "#3a3a48", "#9a98b0"),
                             (160.0, 4.0, "#5a6a78", "#8a9aa8"), (170.0, 4.0, "#3a3a48", "#9a98b0")]:
        m = np.abs(X - px) < w / 2
        rgb[m] = pal_array([col])[0]
        rgb[m & (X < px - w / 2 + 1.5)] = pal_array([hi])[0]
        strap = m & ((Z % 70) < 3)
        rgb[strap] = pal_array([IRON[1]])[0]
    tray = (X > -40) & (X < 10)
    rgb[tray] = pal_array(["#2a2a36"])[0]
    rgb[tray & ((Z % 24) < 2)] = pal_array(["#5a5a6a"])[0]
    rgb[tray & ((X < -37) | (X > 7))] = pal_array(["#6a6a7c"])[0]
    for (bx, bz) in BULBS:
        warm_light(rgb, np.hypot(X - bx, (Z - bz) * 1.5), 90, colour="#f6cf7a", strength=0.22)
    out = rgba_of(rgb * 0.8)
    fog(out, Z, "#1c1622", 600, 900, amount=0.5)
    return out


def side_wall(left):
    """A side wall as it appears on screen (left: near to far, right: far to near). Block with a
    teal dado; the lower part stays quiet behind the fighters; detail sits high up."""
    L, Hh = int(Z_BACK - Z_NEAR), int(CEIL)
    cv = Canvas(L, Hh, seed=2 if left else 3)
    block_wall(cv, 0, 0, L, Hh, dado_top=int(Hh - DADO_Y), seed=4 if left else 5)
    col = lambda z: int(z - Z_NEAR) if left else int(Z_BACK - z)
    conduit_run(cv, 0, L, 10)
    conduit_run(cv, 0, L, 16, colour=["#3a3a48", "#5a6a78", "#8a9aa8"])
    marks = []
    if left:
        # Mags's corner: punch clock and card rack, the key box, her jacket on its hook
        punch_clock(cv, col(430), 34)
        key_cabinet(cv, col(476), 42)
        jx = col(522)
        cv.rect(jx + 4, 34, 3, 3, IRON[3])
        cv.poly([(jx, 37), (jx + 10, 37), (jx + 14, 68), (jx - 4, 68)], "#3e5a5e")
        cv.poly([(jx, 37), (jx + 5, 37), (jx + 3, 68), (jx - 4, 68)], "#2c4048")
        cv.rect(jx - 3, 64, 17, 4, "#2c4048"); cv.px(jx + 8, 50, "#e8b45c")
        for (nx, ny, c) in [(col(560), 40, PAPER[2]), (col(576), 46, "#f2d27a")]:
            cv.rect(nx + 1, ny + 1, 12, 15, C(SHADOW, 0.5)); cv.rect(nx, ny, 12, 15, c)
            for k in range(4):
                cv.hline(nx + 2, ny + 3 + k * 3, 8 - (k % 2) * 2, "#6a5a50")
            cv.px(nx + 6, ny + 1, "#c84a3c")
        text(cv, "B1", col(615), 30, SAFETY[2])
    else:
        # the access panel set into the wall, door open, the TOMORROW fuse lit
        p0, p1 = col(PANEL_Z[1]), col(PANEL_Z[0])
        top, bot = Hh - 112, Hh - 38
        cv.rect(p0 - 2, top - 2, p1 - p0 + 4, bot - top + 4, OUT)
        cv.rect(p0, top, p1 - p0, bot - top, "#7a7a8a"); cv.hline(p0, top, p1 - p0, "#a4a4b4")
        cv.rect(p0 + 2, top + 2, p1 - p0 - 4, 10, "#2a2a36"); text(cv, "ACCESS", p0 + (p1 - p0) // 2 - 17, top + 2, SAFETY[3])
        ix, iy = p0 + 4, top + 15
        cv.rect(ix, iy, p1 - p0 - 8, bot - top - 20, "#4a4a5a")
        for r in range(6):
            for c_ in range(3):
                fx, fy = ix + 3 + c_ * 13, iy + 4 + r * 9
                if fx + 8 > p1 - 4:
                    continue
                cv.rect(fx, fy, 8, 6, OUT); cv.rect(fx + 1, fy + 1, 6, 4, "#3a3a48")
                if r == 2 and c_ == 1:
                    cv.rect(fx - 1, fy - 1, 10, 8, C("#f6cf7a", 0.35))
                    cv.rect(fx + 1, fy + 1, 6, 4, "#ffd27a"); cv.rect(fx + 2, fy + 2, 4, 2, "#fff0c4")
                    marks.append(("fuse", fx + 1, fy + 1))
                elif r == 2 and c_ == 0:
                    cv.rect(fx, fy, 8, 6, "#2a2630"); bolt(cv, fx + 2, fy + 2, "#8a8478")
                else:
                    cv.rect(fx + 3, fy + 1, 2, 4, IRON[4])
        cv.poly([(p1, top), (p1 + 18, top + 6), (p1 + 18, bot - 4), (p1, bot)], "#6a6a7a")
        cv.vline(p1 + 18, top + 6, bot - top - 10, "#8a8a9a")
        cv.poly([(p1 + 6, top + 30), (p1 + 10, top + 22), (p1 + 13, top + 31)], SAFETY[2])
        # conduit dropping into it, a junction box, hazard tape on the floor edge
        cv.rect(p0 + 8, 19, 4, top - 19, "#3a3a48"); cv.vline(p0 + 8, 19, top - 19, "#9a98b0")
        junction_box(cv, p0 + 4, 40, 12, 10, label=SAFETY[2])
        # Cal's pegboard further along, and the extinguisher by the doorway end
        pegboard(cv, col(520), 40, 86, 46, seed=3)
        extinguisher(cv, col(640), Hh - 36)
    return cv.a, marks


def back_wall():
    """The far end at its on-screen size: block wall and dado, the service doorway down to the lanes
    with LANES in neon, an EXIT sign, the pipes arriving from the ceiling."""
    s = 320.0 / Z_BACK
    W = int(round(2 * WALL_X * s)) + 2
    Hh = int(round(CEIL * s))
    cv = Canvas(W, Hh, seed=4)
    block_wall(cv, 0, 0, W, Hh, dado_top=Hh - 14, seed=6)
    cv.rect(0, 0, W, Hh, C(SHADOW, 0.18))
    cv.rect(0, 0, W, 4, "#24202a")
    cv.rect(0, 4, W, 4, "#8a3a32"); cv.hline(0, 4, W, "#b8584a")
    cx = W // 2 + int(round(DOOR_X * s))
    service_doorway(cv, cx, Hh, Hh, w=46, h=60, seed=1)
    neon = (cx - 15, Hh - 60 + 1)
    halo(cv, cx, Hh - 54, 18, colour="#ff7aa8", strength=0.14)
    text(cv, "LANES", cx - 15, Hh - 60 + 1, "#ff8ab4")
    halo(cv, cx, Hh - 42, 22, colour="#ff7aa8", strength=0.08)
    cv.rect(cx - 13, Hh - 78, 26, 10, OUT); cv.rect(cx - 12, Hh - 77, 24, 8, EXIT_GREEN[1])
    text(cv, "EXIT", cx - 12, Hh - 78, EXIT_GREEN[3])
    halo(cv, cx, Hh - 73, 14, colour="#3cba7a", strength=0.06)
    # stencil and a notice on the right
    text(cv, "B1", W - 60, 14, SAFETY[2])
    cv.rect(W - 40, 18, 10, 13, PAPER[2])
    for k in range(3):
        cv.hline(W - 38, 21 + k * 3, 6, "#6a5a50")
    return cv, neon, (cx, Hh - 73)


def well_rails():
    """Rail texture for the well's sides: posts every 40 units, top and mid rails in worn safety
    paint, a hazard kick plate; transparent between."""
    L, Hh = 280, 44
    cv = Canvas(L, Hh)
    post, hi, lo = "#a8781e", "#d9a441", "#6a4a18"
    for x in range(0, L, 40):
        cv.rect(x, 2, 3, Hh - 2, post); cv.vline(x, 2, Hh - 2, hi); cv.vline(x + 2, 2, Hh - 2, lo)
    cv.rect(0, 2, L, 3, post); cv.hline(0, 2, L, hi); cv.hline(0, 4, L, lo)
    cv.rect(0, 22, L, 2, post); cv.hline(0, 22, L, hi)
    hazard_band(cv, 0, Hh - 6, L, 6)
    return cv.a


def shaft_wall(length):
    """Inside of the well: block falling away from the landing lights into the dark, then lit pink
    and teal from the lanes below; the top of the next flight's yellow handrail on the far wall."""
    Hh = int(SHAFT)
    cv = Canvas(length, Hh)
    block_wall(cv, 0, 0, length, Hh, seed=8)
    for (y0, y1, a) in [(0, 4, 0.3), (4, 8, 0.5), (8, 12, 0.7), (12, Hh, 0.86)]:
        cv.rect(0, y0, length, y1 - y0, C("#0e0c14", a))
    cv.rect(0, 3, length, 1, C(SAFETY[2], 0.5))
    # neon rising from the lanes: pink to the left, teal to the right, stepped bands
    for (y0, a) in [(13, 0.14), (17, 0.24), (21, 0.36), (25, 0.5)]:
        for xx in range(length):
            t = xx / max(1, length - 1)
            c = "#ff7aa8" if t < 0.62 else "#58e0d0"
            cv.px(xx, y0, C(c, a * 0.6))
        cv.rect(0, y0 + 1, int(length * 0.62), 4, C("#ff7aa8", a))
        cv.rect(int(length * 0.62), y0 + 1, length - int(length * 0.62), 4, C("#58e0d0", a * 0.8))
    cv.line(10, 5, length - 20, 30, SAFETY[1]); cv.line(10, 6, length - 20, 31, SAFETY[0])
    return cv.a


def build(project):
    global DECAL
    DECAL = floor_decal()
    out = os.path.join(project, "assets/art/rooms/U05")
    v = View(horizon=HORIZON, cam=CAM, fill="#100c14")
    # ceiling first, then walls, the far wall, the inside of the well, the floor over all of it
    v.ground(ceiling_shader, y_from=0.0, y_to=HORIZON - 0.01, height=CEIL)
    L = int(Z_BACK - Z_NEAR)
    marks = []
    for side in (-1, 1):
        tex, m = side_wall(side < 0)
        if side > 0:
            marks = m

        def shade_wall(u, Y, Z, tex=tex, side=side):
            o = texture_lookup(tex, u if side < 0 else L - 1 - u, CEIL - Y, wrap=False)
            o[..., :3] *= 0.76
            fog(o, Z, "#1c1622", 600, 900, amount=0.4)
            return o
        v.plane((side * WALL_X, Z_NEAR), (side * WALL_X, Z_BACK), shade_wall, y_max=CEIL)
    flat, neon, exit_pt = back_wall()
    s = v.scale(Z_BACK)
    fx0 = int(round(v.vx - flat.w / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - flat.h))
    v.strip(flat.a, fy0, fx0)
    x0, z0, x1, z1 = WELL
    sh = shaft_wall(int(x1 - x0))
    v.plane((x0, z1), (x1, z1), lambda u, Y, Z: texture_lookup(sh, u, -Y, wrap=False), y_max=0.0, y_min=-SHAFT)
    sh2 = shaft_wall(int(z1 - z0))

    def side_shaft(u, Y, Z):
        o = texture_lookup(sh2, u, -Y, wrap=False)
        o[..., :3] *= 0.7
        return o
    for X in (x0, x1):
        v.plane((X, z0), (X, z1), side_shaft, y_max=0.0, y_min=-SHAFT)
    v.ground(floor_shader)
    rails = well_rails()

    def rail_shader(u, Y, Z):
        return texture_lookup(rails, u, 44 - Y, wrap=True)
    v.plane((x0, z1), (x1, z1), rail_shader, y_max=44)
    v.plane((x0, z0), (x0, z1), rail_shader, y_max=44)
    v.plane((x1, z0), (x1, z1), rail_shader, y_max=44)
    v.plane((x0, z0), (x1, z0), rail_shader, y_max=44)
    # caged bulbs on drops from the ceiling
    bulbs = []
    for (bx, bz) in BULBS:
        spr = Canvas(9, 60)
        spr.rect(4, 0, 1, 48, "#3a3a48")
        caged_bulb(spr, 4, 51)
        spr.a[:, :, :][spr.a[..., 3] < 0.2] = 0
        sx, sy, sc = v.sprite(spr.a, bx, bz, Y=CEIL, anchor=(0.5, 0.0), scale=1.2)
        bulbs.append((int(round(sx)), int(round(sy + 55 * sc))))
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    # crisp neon over the doorway (too few pixels to survive the palette reduction)
    nx, ny = fx0 + neon[0], fy0 + neon[1]
    text(cv, "LANES", nx + 1, ny + 1, "#5a1a3a")
    text(cv, "LANES", nx, ny, "#ff8ab4")
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    res = "res://assets/art/rooms/U05/"

    def wall_pt(z, row):
        """Screen point of a right-wall texel (column for depth z, row from the ceiling)."""
        X, Y = WALL_X, CEIL - row
        sx, sy = v.project(X, Y, z)
        return int(round(sx)), int(round(sy))
    layers = []
    for (_, tx, ty) in marks:
        z = Z_BACK - tx
        ax, ay = wall_pt(z, ty)
        bx_, by_ = wall_pt(z - 6, ty + 4)
        layers.append({"kind": "blink", "pattern": "1111011111101111", "rate": 9.0,
                       "rects": [[min(ax, bx_), ay, max(2, abs(bx_ - ax)), max(2, by_ - ay), "fff0c4"],
                                 [min(ax, bx_) - 3, ay - 3, abs(bx_ - ax) + 6, by_ - ay + 6, "f6cf7a", 0.2]]})
    nx, ny = fx0 + neon[0], fy0 + neon[1]
    layers += [
        {"kind": "blink", "pattern": "11111111011111111110", "rate": 7.0, "rects": [[nx, ny + 2, 30, 7, "ff7aa8", 0.25]]},
        # the lanes' glow breathing up the well
        {"kind": "blink", "pattern": "1100", "rate": 0.8, "rects": [[int(v.project(-60, 0, z1)[0]), int(v.project(0, 0, z1)[1]),
                                                                       int(150 * v.scale(z1)), 8, "ff7aa8", 0.12]]},
        {"kind": "blink", "pattern": "0011", "rate": 0.8, "rects": [[int(v.project(10, 0, z1)[0]), int(v.project(0, 0, z1)[1]) + 2,
                                                                       int(100 * v.scale(z1)), 6, "58e0d0", 0.12]]},
        {"kind": "twinkle", "points": [[x, y, "f6cf7a", 2] for (x, y) in bulbs], "rate": 1.3, "min": 0.65},
        {"kind": "particles", "style": "dust", "count": 16, "rect": [200, 20, 260, 110], "speed": [0, 2], "color": "f6e0b0"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:400])
