"""Battle backdrop for the Hill (H01): on the party house's front lawn, looking straight up the front
walk at the porch. The house looms over the fight with every window pulsing, string lights run from
the porch out to the two big oaks framing the lawn, the neighbours' houses stand shoulder to shoulder
either side, the lawn is littered with leaves and red cups, the plaid couch sits off to the left.
Bats cross the strip of sky, leaves come down, the open door thumps with the bass."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, shade
from props import atlas_tree, OUT
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_farrand import festoon
import build_h01 as room
from h01_lib import CUP, lawn_couch, yard_sign, SHADOW

INK = "#10121e"
HAZE = "#2a2238"
Z_HOUSE = 1000.0          # depth of the facade row
DOOR_ROOM = room.DOOR_B   # the party house's door, centred on screen
LAWN_ROOM = room.LAWN0    # room row where the lawn meets the porch skirt
GRASS = ["#141e1a", "#1a2820", "#223226", "#2b3d2e", "#354a36", "#42583e"]


def facade_row():
    """The three houses painted exactly as in the room (transparent above the side yards), plus a
    copy of the Tudor house on the left and the brick house on the right so the row fills the view."""
    t = Canvas(room.W, LAWN_ROOM + 4)
    room.side_yard(t, 0, room.HA[0], seed=3)
    room.side_yard(t, room.HA[1], room.HB[0], seed=1)
    room.side_yard(t, room.HB[1], room.HC[0], seed=2)
    room.house_a(t)
    info_b, _ = room.house_b(t)
    room.house_c(t)
    t.a[LAWN_ROOM + 2:] = 0
    pad_l, pad_r = 260, 300
    row = np.zeros((t.h, t.w + pad_l + pad_r, 4), np.float32)
    row[:, pad_l:pad_l + t.w] = t.a
    yard = t.a[:, room.HA[1]:room.HB[0]]                       # a side yard, 36 wide
    tudor = t.a[:, room.HC[0] - 16:room.HC[1] + 4]             # the Tudor and a sliver of its yard
    row[:, pad_l - tudor.shape[1]:pad_l] = tudor
    row[:, 0:pad_l - tudor.shape[1]] = yard[:, :pad_l - tudor.shape[1]]
    row[:, pad_l + t.w - 64:pad_l + t.w - 64 + yard.shape[1]] = yard   # past the hedge, another side yard
    brick = t.a[:, room.HA[0]:room.HA[0] + pad_r + 28]
    row[:, pad_l + t.w - 28:] = brick[:, :pad_r + 28]
    return row, pad_l + DOOR_ROOM, info_b


def lawn_shader(X, Z):
    """Night lawn in tufted clumps, the front walk up the middle, leaves under the oaks, cups,
    pink party light spilling from the house."""
    n = X.shape[0]
    pal = pal_array(GRASS)
    cell = hash2(np.floor(X / 6.0), np.floor(Z / 9.0), 2)
    big = hash2(np.floor(X / 40.0), np.floor(Z / 60.0), 3)
    idx = np.clip((cell * 2.2 + big * 1.6).astype(int) + 1, 1, 4)
    rgb = pal[idx].copy()
    tip = (hash2(np.floor(X / 3.0), np.floor(Z / 4.0), 5) > 0.9)
    rgb[tip] = pal[5]
    # front walk: concrete slabs from the camera up to the steps
    walk = np.abs(X) < 30
    slab = np.floor(Z / 40.0)
    tone = hash2(slab, 1, 7)
    srgb = pal_array(["#5a5560", "#6a6570", "#77727c"])
    wrgb = srgb[1] * (1 - tone[:, None]) + srgb[2] * tone[:, None]
    wrgb[(Z / 40.0 - slab) < 0.04] = srgb[0]
    rgb[walk] = wrgb[walk]
    edge = (np.abs(np.abs(X) - 30) < 1.2)
    rgb[edge] = pal[0]
    # fallen leaves under the oaks, red cups everywhere
    for ox in (-560.0, 560.0):
        d = np.hypot((X - ox) * 0.7, (Z - 600) * 0.5)
        leaf = (hash2(np.floor(X / 3.0), np.floor(Z / 5.0), 11) > 0.55 + d / 600) & ~walk
        rgb[leaf] = pal_array(["#a83c32", "#c8682e", "#d9a441"])[(hash2(np.floor(X / 3.0), np.floor(Z / 5.0), 12) * 2.99).astype(int)][leaf]
    cup = (hash2(np.floor(X / 14.0), np.floor(Z / 22.0), 13) > 0.985) & (np.mod(X, 14) < 5) & (np.mod(Z, 22) < 5)
    rgb[cup] = np.array(C(CUP[2])[:3])
    rim = (hash2(np.floor(X / 14.0), np.floor(Z / 22.0), 13) > 0.985) & (np.mod(X, 14) < 5) & (np.mod(Z, 22) >= 5) & (np.mod(Z, 22) < 7)
    rgb[rim] = np.array(C(CUP[4])[:3])
    # the house's light on the lawn: pink from the windows, warm down the walk from the open door
    warm_light(rgb, np.hypot(X * 0.6, (Z - Z_HOUSE) * 0.5), 260, colour="#f0a0c8", strength=0.3)
    warm_light(rgb, np.hypot(X * 2.2, (Z - Z_HOUSE) * 0.12), 140, colour="#ffd0dc", strength=0.3)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 700, 1400, amount=0.35)
    return out


def build(project):
    out = os.path.join(project, "assets/art/rooms/H01")
    os.makedirs(out, exist_ok=True)
    res = "res://assets/art/rooms/H01/"
    v = View(horizon=98, cam=52, fill="#141228")
    # a strip of night sky (north, away from the sunset): violet with stars, mostly hidden by the roofs
    sky = np.ones((60, 640, 4), np.float32)
    top, bot = np.array(C("#141232")[:3]), np.array(C("#3a2a56")[:3])
    for y in range(60):
        sky[y, :, :3] = top + (bot - top) * (y / 59)
    rng = np.random.default_rng(4)
    stars = []
    for _ in range(40):
        x, y = int(rng.integers(0, 640)), int(rng.integers(0, 40))
        sky[y, x, :3] = C("#c8d0f0")[:3]
        stars.append([x, y, "c8d0f0", 1])
    v.strip(sky, 0, solid=False)

    v.ground(lawn_shader)
    row, door_col, info_b = facade_row()
    rh, rw = row.shape[:2]
    s = ROOM_TO_BATTLE

    def facade(X, Y):
        u = door_col + X / s
        tv = (LAWN_ROOM + 1) - Y / s
        o = texture_lookup(row, u, tv, wrap=False)
        o[..., :3] *= 0.9
        return fog(o, np.full(X.shape, Z_HOUSE), HAZE, 700, 1400, amount=0.35)
    v.back(Z_HOUSE, facade, region=lambda X, Y: (Y >= 0) & (Y < (LAWN_ROOM + 1) * s))

    # mid-ground: the lawn couch off to the left, the yard sign, two big oaks framing the lawn
    spr, ax, ay = lawn_couch(100, 40, seed=2)
    v.sprite(spr.a, -205, 780, anchor=(ax / spr.w, ay / spr.h), scale=s)
    spr, ax, ay = yard_sign(40, 36, lines=("NO", "PARKING", "ON LAWN"))
    v.sprite(spr.a, 190, 700, anchor=(ax / spr.w, ay / spr.h), scale=s)
    trees = []
    for x, z, seed in [(-560, 600, 3), (560, 620, 5)]:
        spr, ax, ay = atlas_tree(150, cell=5, seed=seed)
        sx, sy, sc = v.sprite(spr.a, x, z, anchor=(ax / spr.w, ay / spr.h), scale=s)
        trees.append((sx, sy - spr.h * s * sc * 0.62))
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp string lights: along the party porch eave, and from the porch corners out to the oaks
    def P(rx, ry):
        X = (rx - DOOR_ROOM) * s
        Y = (LAWN_ROOM + 1 - ry) * s
        return v.project(X, Y, Z_HOUSE)
    eb = info_b["eave"] + 6
    cols = [room.HB[0] + 16, room.HB[0] + 96, room.HB[1] - 96, room.HB[1] - 16]
    bulbs = []
    for a, b in zip([room.HB[0] + 2] + cols, cols + [room.HB[1] - 2]):
        (x0, y0), (x1, y1) = P(a, eb), P(b, eb)
        bulbs += festoon(cv, int(x0), int(y0), int(x1), int(y1), sag=4, every=5, seed=int(a),
                         colours=["#f6cf7a", "#ff8ad0", "#6ad8f0", "#fff0c4"])
    (lx, ly), (rx_, ry_) = P(room.HB[0] + 2, eb), P(room.HB[1] - 2, eb)
    (tlx, tly), (trx, try_) = trees
    bulbs += festoon(cv, int(lx), int(ly), int(tlx), int(tly), sag=26, every=9, seed=31)
    bulbs += festoon(cv, int(rx_), int(ry_), int(trx), int(try_), sag=26, every=9, seed=32)
    bulbs += festoon(cv, int(lx) - 4, int(ly) + 2, -10, 30, sag=30, every=10, seed=33)
    cv.save(os.path.join(out, "battle-far.png"))

    # layers: party light pulsing in the windows, the door thumping, bulbs, bats, leaves
    win = [(room.HB[0] + 44, 18, 26, 36), (room.HB[1] - 70, 18, 26, 36), (room.HB[0] + 30, 132, 34, 44),
           (room.HB[0] + 86, 132, 26, 44), (room.HB[1] - 112, 132, 26, 44), (room.HB[1] - 64, 132, 34, 44)]
    layers = []
    for k, (x, y, w, h) in enumerate(win):
        (sx0, sy0), (sx1, sy1) = P(x, y), P(x + w, y + h)
        colour = ["ff5ab4", "5ad8ff", "a07aff"][k % 3]
        pat = ["1100", "0110", "0011", "1001"][k % 4]
        layers.append({"kind": "blink", "pattern": pat, "rate": 2.4,
                       "rects": [[int(sx0), int(sy0), max(1, int(sx1 - sx0)), max(1, int(sy1 - sy0)), colour, 0.3]]})
    (dx0, dy0), (dx1, dy1) = P(DOOR_ROOM - 17, room.FB - 72), P(DOOR_ROOM + 17, room.FB)
    layers += [
        {"kind": "blink", "pattern": "10101000", "rate": 4.0, "rects": [[int(dx0), int(dy0), int(dx1 - dx0), int(dy1 - dy0), "ffd0e8", 0.22]]},
        {"kind": "twinkle", "points": bulbs, "rate": 2.0, "min": 0.35},
        {"kind": "twinkle", "points": stars, "rate": 1.4, "min": 0.1},
        {"kind": "fauna", "fauna": [{"kind": "night_bat", "x": 120, "y": 22, "fly": 16.0, "rate": 8.0},
                                    {"kind": "night_bat", "x": 400, "y": 14, "fly": 12.0, "rate": 7.0}]},
        {"kind": "particles", "style": "leaf", "count": 10, "rect": [-20, 0, 680, 160], "speed": [10, 14]},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:200])
