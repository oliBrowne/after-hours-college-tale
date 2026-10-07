"""Battle backdrop for the shared workshop (E02): down the walkway between the benches toward the
back wall, where Cal's floating arch and Dev's two spans share the whiteboard. Lockers and the drill
press line the left wall, the bandsaw, blueprint and breaker panel the right; the electronics bench
in the far corner runs its oscilloscope. The room is the Engineering Center's raw board-formed
concrete: slot windows deep in the side walls, concrete piers over a Lyons sandstone base course,
a coffered concrete ceiling with caged lamps on conduit drops over yellow aisle lines; sawdust
hangs in their light."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
import lib_eng as E
import ec_interior as I
import build_e02 as R

ROOM = "E02"
INK = "#10121e"
K = ROOM_TO_BATTLE
BACK = (140, 520)                         # room-x span of the back wall shown at the end of the aisle
WALL_X = (BACK[1] - BACK[0]) * K / 2      # side walls stand at +-WALL_X
Z_BACK = 780.0
Z_NEAR = 300.0
H_WALL = R.BASE * K                       # the room's wall height in world units
L_SIDE = int(round((Z_BACK - Z_NEAR) / K))
PENDANTS = [(-120.0, 470.0), (120.0, 470.0), (-120.0, 660.0), (120.0, 660.0)]


def room_wall():
    """The E02 back wall painted at room scale, used for the end wall and both side walls."""
    cv = Canvas(R.W, R.BASE, fill="#171a2b")
    R.paint_back_wall(cv)
    elec = R.paint_wall_things(cv)
    return cv, elec


def side_texture(room, src, far_end, seed):
    """A side wall: the room's concrete fabric (slot windows, piers, sandstone base) with a slice
    of the room's back wall placed at the far end."""
    cv = Canvas(L_SIDE, R.BASE, fill="#171a2b")
    wins = tuple(range(36, L_SIDE - 20, 62))
    R.paint_fabric(cv, 0, L_SIDE, seed=seed, windows=wins, piers=tuple(range(4, L_SIDE, 124)))
    E.dust_duct(cv, 0, L_SIDE, R.DUCT_Y, 7)
    x0, x1 = src
    piece = room.a[:, x0:x1]
    if far_end == "right":
        cv.a[:, L_SIDE - (x1 - x0):] = piece
    else:
        cv.a[:, :x1 - x0] = piece
    return cv


def floor_shader(X, Z):
    fl = pal_array(R.SHOP_FLOOR)
    cell = hash2(np.floor(X / 90), np.floor(Z / 60), 5)
    rgb = np.where(cell[:, None] < 0.5, fl[4], fl[5]).astype(np.float32)
    fleck = hash2(np.floor(X * 320 / Z), np.floor(16640 / Z), 6)       # one-pixel flecks
    rgb[fleck > 0.985] = fl[6]
    rgb[(np.abs((X % 128) - 64) < 1.2) | (np.abs(((Z - 300) % 104) - 52) < 1.4)] = fl[2]
    # the work zone (darker epoxy) on both sides of the walkway
    zone = pal_array(R.ZONE_FLOOR)
    wz = np.abs(X) > 110
    rgb[wz] = np.where(cell[wz, None] < 0.5, zone[4], zone[5])
    yel = np.array(C(E.SAFETY[2])[:3], np.float32)
    wear = hash2(np.floor(X / 4), np.floor(Z / 10), 8) < 0.85
    for lx in (-110.0, 110.0):
        m = (np.abs(np.abs(X) - 110.0) < 3) & wear & (np.sign(X) == np.sign(lx))
        rgb[m] = rgb[m] * 0.25 + yel * 0.75
    # anti-fatigue mats by the benches
    for (mx, mz) in ((-200.0, 690.0), (200.0, 500.0)):
        m = (np.abs(X - mx) < 90) & (np.abs(Z - mz) < 22)
        rgb[m] = np.array(C("#34373e")[:3], np.float32)
        edge = m & ((np.abs(X - mx) > 86) | (np.abs(Z - mz) > 19))
        rgb[edge] = yel * 0.8
    # sawdust under Cal's bench, the pendant light pools
    dust = (hash2(np.floor(X / 3), np.floor(Z / 4), 9) > 0.9) & (np.hypot((X + 200) / 80, (Z - 740) / 30) < 1)
    rgb[dust] = np.array(C("#b49868")[:3], np.float32)
    for (px, pz) in PENDANTS:
        warm_light(rgb, np.hypot(X - px, (Z - pz) * 1.4), 120, colour="#f6cf7a", strength=0.3)
    warm_light(rgb, np.hypot(X, (Z - Z_BACK) * 1.2), 200, colour="#f6cf7a", strength=0.18)
    out = rgba_of(rgb)
    fog(out, Z, "#1e1c2a", 650, Z_BACK + 60, amount=0.35)
    return out


def ceiling_shader(X, Z):
    return I.beam_ceiling_shader(X, Z, bay_z=120.0, bay_x=240.0, z0=300.0, fog_to=Z_BACK)


def pendant_sprite(drop):
    cv = Canvas(24, drop + 14)
    I.cage_lamp(cv, 11, 0, drop, lit=True)
    return cv


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#12121c")
    room, elec = room_wall()
    v.ground(floor_shader)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=H_WALL)
    left = side_texture(room, (0, 140), "right", 81)
    right = side_texture(room, (600, 800), "left", 91)
    for side, tex in ((-1, left.a), (1, right.a)):
        def wall(u, Y, Z, tex=tex, side=side):
            uu = u / K if side < 0 else (L_SIDE - 1 - u / K)
            o = texture_lookup(tex, uu, R.BASE - Y / K, wrap=False)
            o[..., :3] *= 0.8
            fog(o, Z, "#1e1c2a", 600, Z_BACK + 60, amount=0.3)
            return o
        v.plane((side * WALL_X, Z_NEAR), (side * WALL_X, Z_BACK), wall, y_max=H_WALL)
    back = Canvas(BACK[1] - BACK[0], R.BASE)
    back.a = room.a[:, BACK[0]:BACK[1]].copy()
    v.sprite(back.a, 0.0, Z_BACK, anchor=(0.5, 1.0), scale=K)
    s_back = K * v.F / Z_BACK
    gy = v.ground_y(Z_BACK)
    to_screen = lambda p: [int(round(320 + (p[0] - (BACK[0] + BACK[1]) / 2) * s_back)), int(round(gy - (R.BASE - p[1]) * s_back))]
    # the benches: Dev's on the right nearer, Cal's on the left further back; the tool chest
    for (made, x, z) in ((E.maple_bench(170, 45, "arch", seed=1), -200.0, 720.0),
                         (E.maple_bench(170, 45, "spans", seed=2), 205.0, 530.0),
                         (E.tool_chest(70, 44, seed=4), -250.0, 560.0)):
        spr, ax, ay = made
        v.sprite(spr.a, x, z, anchor=(ax / spr.w, ay / spr.h), scale=K)
    bulbs = []
    for (px, pz) in PENDANTS:
        p = pendant_sprite(30)
        sx, sy, sc = v.sprite(p.a, px, pz, Y=H_WALL - p.h * K, anchor=(0.5, 1.0), scale=K)
        bulbs.append([int(round(sx)), int(round(sy - 4 * sc)), "fff0c4", 2])
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    cv.save(os.path.join(out, "battle-far.png"))

    # oscilloscope frames mapped onto the far wall
    sx, sy, sw, sh = elec["screen"]
    a = to_screen((sx, sy))
    b = to_screen((sx + sw, sy + sh))
    w, h = max(3, b[0] - a[0]), max(2, b[1] - a[1])
    layers = []
    n = 6
    for k in range(n):
        fr = E.scope_frame(w, h, k, n, "sine")
        fr.save(os.path.join(out, f"battle-scope-{k}.png"))
        layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(n)), "rate": 7.0,
                       "texture": res + f"battle-scope-{k}.png", "x": a[0], "y": a[1]})
    led = to_screen(elec["led"])
    layers += [
        {"kind": "blink", "pattern": "11110000", "rate": 2.0, "rects": [[led[0], led[1], 1, 1, "ff5a3a"]]},
        {"kind": "twinkle", "points": bulbs, "rate": 0.9, "min": 0.75},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [40, 30, 560, 120], "speed": [2, 3], "color": "f6dca0"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
