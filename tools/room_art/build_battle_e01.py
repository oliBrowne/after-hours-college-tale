"""Battle backdrop for the loading court (E01): standing in the Engineering Center's service courtyard
at night, looking up at the building the way it really looks: board-formed concrete towers rising
like grain silos over lower wings of pink-red Lyons sandstone under red tile shed roofs. The court is
closed in on both sides by wings in perspective (sandstone on the left, raw concrete on the right),
the dock block straight ahead with ENGINEERING CENTER on its canopy, the workshop's roll-up door open
and lit (welding flashes and sparks inside), DOCK 2 shut beside it, the distant office tower with its
red beacon. Yellow bay lines run toward the dock, puddles hold the door's light, clouds drift behind
the towers, a bat crosses, the lamps breathe."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
import lib_eng as E
import ec_exterior as X
import build_e01 as R

ROOM = "E01"
INK = "#10121e"
HAZE = "#28223a"
Z_FAC = 1150.0                           # depth of the facade: the tower tops just fit under the top edge
S_FAC = ROOM_TO_BATTLE * 320.0 / Z_FAC   # room pixels -> screen pixels at that depth
HALF_X = R.W / 2 * ROOM_TO_BATTLE        # the facade's half width in world units
Z_NEAR = 300.0                           # where the side wings start (outside the view)
APRON_D = 170.0                          # depth of the concrete apron in front of the dock
DOOR_X = ((R.OPEN_DOOR[0] + R.OPEN_DOOR[1] / 2) - R.W / 2) * ROOM_TO_BATTLE
PUDDLES = [(-90.0, 560.0, 80.0, 46.0), (230.0, 470.0, 52.0, 30.0), (-330.0, 700.0, 60.0, 30.0)]
LAMPS = [(-640.0, 520.0), (640.0, 640.0)]
LEFT_H, RIGHT_H = 104, 128               # wing heights in room pixels


def ground_shader(X_, Z):
    asp = pal_array(E.ASPH)
    cell = hash2(np.floor(X_ / 70), np.floor(Z / 46), 3)
    idx = np.where(cell < 0.3, 2, np.where(cell < 0.8, 3, 4))
    rgb = asp[idx].copy()
    agg = hash2(np.floor(X_ / 3), np.floor(Z / 5), 7)
    rgb[agg > 0.95] = asp[5]
    rgb[agg < 0.03] = asp[1]
    # concrete apron in slabs in front of the dock
    ap = Z > Z_FAC - APRON_D
    conc = pal_array(E.CONC)
    sl = hash2(np.floor(X_ / 68), np.floor((Z_FAC - Z) / 40), 9)
    rgb[ap] = np.where(sl[ap, None] < 0.5, conc[5], conc[6])
    jx = np.abs(((X_ + 34) % 68) - 34) < 1.2
    jz = np.abs((((Z_FAC - Z) + 20) % 40) - 20) < 1.6
    rgb[ap & (jx | jz)] = conc[3]
    rgb[np.abs(Z - (Z_FAC - APRON_D)) < 3] = conc[2]
    # a strip of sandstone pavers along the foot of each wing
    pav = pal_array(["#5a4440", "#76584e", "#86665a", "#967464"])
    side = np.abs(X_) > HALF_X - 70
    pr = np.floor(Z / 22)
    pc = np.floor((X_ + (pr % 2) * 14) / 28)
    pt = hash2(pc, pr, 4)
    prgb = pav[np.where(pt < 0.35, 1, np.where(pt < 0.8, 2, 3))]
    edge = ((((X_ + (pr % 2) * 14) % 28) + 28) % 28 < 1.5) | ((Z % 22) < 1.8)
    prgb[edge] = pav[0]
    rgb[side & ~ap] = prgb[side & ~ap]
    rgb[(np.abs(np.abs(X_) - (HALF_X - 70)) < 2) & ~ap] = pav[0] * 0.8
    # loading-bay lines toward the dock, a stop bar, a keep-clear hatch in front of DOCK 2
    yel = np.array(C(E.SAFETY[2])[:3], np.float32)
    wear = hash2(np.floor(X_ / 4), np.floor(Z / 12), 13) < 0.82
    for bx in (-360.0, -170.0, 170.0, 360.0):
        m = (np.abs(X_ - bx) < 2.5) & (Z > 380) & (Z < Z_FAC - APRON_D) & wear
        rgb[m] = rgb[m] * 0.3 + yel * 0.7
    m = (np.abs(Z - (Z_FAC - APRON_D - 14)) < 3) & (np.abs(X_) < 380) & wear
    rgb[m] = rgb[m] * 0.3 + yel * 0.7
    kx0, kx1 = (R.DOCK2[0] - R.W / 2) * ROOM_TO_BATTLE, (R.DOCK2[0] + R.DOCK2[1] - R.W / 2) * ROOM_TO_BATTLE
    box = (X_ > kx0) & (X_ < kx1) & (Z > Z_FAC - APRON_D + 20) & (Z < Z_FAC - 16)
    hatch = (np.abs(((X_ - Z * 1.0) % 40) - 20) < 3) | (np.abs(X_ - kx0) < 2.5) | (np.abs(X_ - kx1) < 2.5)
    rgb[box & hatch] = rgb[box & hatch] * 0.4 + yel * 0.6
    # the door's light on the apron, the dock lamps' and court lamps' pools
    warm_light(rgb, np.hypot((X_ - DOOR_X) * 0.9, (Z - Z_FAC) * 1.3), 260, colour="#f6cf7a", strength=0.42)
    for lx in (DOOR_X - 110, DOOR_X + 110):
        warm_light(rgb, np.hypot(X_ - lx, (Z - Z_FAC + 20) * 1.6), 90, colour="#fff0c4", strength=0.22)
    for (lx, lz) in LAMPS:
        warm_light(rgb, np.hypot(X_ - lx, (Z - lz) * 1.3), 110, colour="#f6cf7a", strength=0.3)
    # puddles: night sky in the water, the lit doorway as a warm streak
    water = pal_array(E.WATER)
    for (px, pz, rx, rz) in PUDDLES:
        d = np.hypot((X_ - px) / rx, (Z - pz) / rz) + 0.18 * (hash2(np.floor(X_ / 18), np.floor(Z / 14), 21) - 0.5)
        m = d < 1.0
        rgb[m] = water[2]
        rgb[m & (d > 0.86)] = water[1]
        streak = m & (np.abs(X_ - DOOR_X) < 26)
        rgb[streak] = np.array(C(E.WARM[2])[:3], np.float32) * 0.8
        ripple = m & (np.abs(((Z - pz) % 14) - 7) < 0.7)
        rgb[ripple] = water[3]
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 700, Z_FAC + 60, amount=0.3)
    return out


def left_wing_texture(length):
    """The left wing at room scale: Lyons sandstone on a concrete plinth, deep windows in concrete
    frames (a few lit), downpipes, a wall light, the red tile roof's edge along the top."""
    h = LEFT_H
    cv = Canvas(length, h)
    X.lyons_wall(cv, 0, 14, length, h - 26, seed=101)
    X.board_concrete(cv, 0, h - 12, length, 12, seed=102, base=6)
    X.ledge(cv, 0, h - 13, length, 2, seed=103, drip=0)
    X.shed_rake(cv, 0, 11, length, 11, thick=10, seed=104)
    rng = np.random.default_rng(105)
    for k, wx in enumerate(range(30, length - 30, 58)):
        X.deep_window(cv, wx, 34, 12, 34, lit=rng.random() < 0.4, seed=110 + k, blind=0.3 if k % 3 == 0 else 0.0,
                      figure=k % 4 == 1)
        if k % 3 == 2:
            cv.rect(wx + 30, 14, 4, h - 14, X.OUT); cv.vline(wx + 31, 14, h - 14, E.STEEL[4])
    E.wall_pack(cv, length // 2 + 14, 20)
    return cv.a


def right_wing_texture(length):
    """The right wing at room scale: raw board-formed concrete, two floors of deep-set windows,
    a projecting floor ledge streaked with rain stains, a red tile roof edge on top."""
    h = RIGHT_H
    cv = Canvas(length, h)
    X.board_concrete(cv, 0, 12, length, h - 12, seed=121, base=6)
    X.shed_rake(cv, 0, 10, length, 10, thick=9, seed=122)
    X.ledge(cv, 0, 62, length, 4, seed=123, drip=20)
    rng = np.random.default_rng(124)
    for k, wx in enumerate(range(24, length - 20, 40)):
        X.deep_window(cv, wx, 24, 10, 28, lit=rng.random() < 0.35, seed=130 + k, blind=0.4 if k % 4 == 0 else 0.0)
        if k % 2 == 0:
            X.deep_window(cv, wx, 78, 10, 30, lit=rng.random() < 0.25, seed=150 + k)
    # a concrete fin every few bays (the frame standing proud)
    for fx in range(0, length, 120):
        X.board_concrete(cv, fx, 12, 6, h - 12, seed=fx + 7, base=7)
        cv.vline(fx, 12, h - 12, X.BOARD[9]); cv.vline(fx + 5, 12, h - 12, X.BOARD[4])
    return cv.a


def wing_shader(tex, height, flip):
    def shade_(u, Y, Z):
        uu = u / ROOM_TO_BATTLE
        if flip:
            uu = tex.shape[1] - 1 - uu
        out = texture_lookup(tex, uu, (height * ROOM_TO_BATTLE - Y) / ROOM_TO_BATTLE, wrap=False)
        fog(out, Z, HAZE, 700, Z_FAC + 60, amount=0.35)
        return out
    return shade_


def sky_strip(h):
    cv = Canvas(640, h)
    stars = E.night_sky(cv, 0, 0, 640, h, seed=17, stars=130, horizon=h + 10)
    return cv, stars


def cloud_strip():
    """A horizontally tileable band of night clouds for the drift layer."""
    cv = Canvas(640, 40)
    E.night_clouds(cv, [(20, 30, 110, 3), (260, 22, 70, 2), (430, 36, 130, 3)], seed=9)
    return cv


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#141432")
    gy = v.ground_y(Z_FAC)
    sky, stars = sky_strip(int(gy) + 2)
    v.strip(sky.a, 0, 0, solid=False)
    v.ground(ground_shader)
    # the building straight ahead, with its towers' tops (the facade canvas reaches above the room)
    fc, pts = R.paint_facade()
    E.stepped_glow(fc, R.OPEN_DOOR[0] + R.OPEN_DOOR[1] // 2, R.EXTRA + R.BASE - 4, 60, 8, "#f6cf7a", 0.2, 3)
    v.sprite(fc.a, 0.0, Z_FAC, anchor=(0.5, 1.0), scale=ROOM_TO_BATTLE)
    s = S_FAC
    to_screen = lambda p: [int(round(320 + (p[0] - R.W / 2) * s)), int(round(gy - (R.BASE - p[1]) * s))]
    # the wings closing the courtyard on either side
    L = int((Z_FAC - Z_NEAR) / ROOM_TO_BATTLE) + 2
    v.plane((-HALF_X, Z_NEAR), (-HALF_X, Z_FAC), wing_shader(left_wing_texture(L), LEFT_H, False),
            y_max=LEFT_H * ROOM_TO_BATTLE)
    v.plane((HALF_X, Z_NEAR), (HALF_X, Z_FAC), wing_shader(right_wing_texture(L), RIGHT_H, True),
            y_max=RIGHT_H * ROOM_TO_BATTLE)
    # props in the court: lamps along the wings, the bike rack, the flatbed cart, cones
    lamp, lax, lay = E.court_lamp(68)
    for (x, z) in LAMPS:
        v.sprite(lamp.a, x, z, anchor=(lax / lamp.w, lay / lamp.h), scale=ROOM_TO_BATTLE)
    rack, rax, ray = E.bike_rack(180, 30, seed=3)
    v.sprite(rack.a, 560.0, 900.0, anchor=(rax / rack.w, ray / rack.h), scale=ROOM_TO_BATTLE)
    cart, cax, cay = E.flatbed_cart(110, 50, seed=2)
    v.sprite(cart.a, -470.0, 980.0, anchor=(cax / cart.w, cay / cart.h), scale=ROOM_TO_BATTLE)
    for (x, z) in [(-170.0, 760.0), (-140.0, 764.0), (170.0, 760.0)]:
        c = Canvas(12, 18)
        E.traffic_cone(c, 6, 17, 14)
        v.sprite(c.a, x, z, scale=ROOM_TO_BATTLE)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    near = Canvas(cv.w, cv.h)
    near.a = cv.a.copy()
    near.a[..., 3] = v.solid_mask().astype(np.float32)
    cv.save(os.path.join(out, "battle-far.png"))
    near.save(os.path.join(out, "battle-near.png"))
    clouds = cloud_strip()
    clouds.save(os.path.join(out, "battle-clouds.png"))

    sx, sy, sw, sh = pts["inside"]["screen"]
    a = to_screen((sx, sy))
    b = to_screen((sx + sw, sy + sh))
    fy = to_screen((sx, pts["inside"]["floor"]))[1]
    door_rect = [a[0], a[1], max(2, b[0] - a[0]), max(2, b[1] - a[1])]
    bpt = to_screen(pts["beacon"])
    lamp_pts = [to_screen(d) for d in pts["dock_lights"]]
    heads = []
    for (x, z) in LAMPS:
        hx, hy = v.project(x, (68 - 6) * ROOM_TO_BATTLE, z)
        heads.append([int(round(hx)), int(round(hy))])
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "drift", "texture": res + "battle-clouds.png", "y": 4, "speed": 3.0, "alpha": 0.9, "depth": "far"},
            {"kind": "twinkle", "points": [[x, y, c.lstrip("#"), 1] for (x, y, c) in stars], "rate": 1.3, "min": 0.1,
             "depth": "far"},
            # welding behind the screen inside the workshop, its flash on the apron, sparks
            {"kind": "blink", "pattern": "000010001100000000101000000110", "rate": 11.0,
             "rects": [door_rect + ["c8e0ff", 0.45], [door_rect[0] - 10, fy - 1, door_rect[2] + 20, 2, "c8e0ff", 0.3],
                       [door_rect[0] - 30, fy + 3, door_rect[2] + 60, 8, "a8c8ff", 0.08]]},
            {"kind": "particles", "style": "dust", "count": 6, "rect": [door_rect[0] - 3, fy - 8, door_rect[2] + 6, 8],
             "speed": [0, 10], "color": "ffc86a"},
            {"kind": "blink", "pattern": "1100000000", "rate": 2.5,
             "rects": [[bpt[0] - 1, bpt[1] - 1, 2, 2, "ff4a3a"], [bpt[0] - 3, bpt[1] - 3, 6, 6, "ff4a3a", 0.25]]},
            {"kind": "twinkle", "points": [[p[0], p[1], "fff0c4", 1] for p in lamp_pts] +
                                          [[p[0], p[1], "fff0c4", 2] for p in heads], "rate": 1.2, "min": 0.6},
            {"kind": "fauna", "fauna": [{"kind": "night_bat", "x": 200, "y": 20, "fly": 16.0, "rate": 6.0}]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
