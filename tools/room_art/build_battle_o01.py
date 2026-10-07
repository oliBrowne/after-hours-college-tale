"""Battle backdrop for the Old Main courtyard: standing on the herringbone forecourt in front of
Old Main at night. The red-brick front fills the middle distance, its steps climbing to the open,
lamp-lit door; the bell tower rises out of the top of the frame with the bell swinging in the
belfry. Gas lamps line the sandstone-framed forecourt, the Old Main medallion lies between the
fighters, the oak and the blue spruce frame the scene on their lawns, garden walls and the dark
campus treeline run off to the sides under the moon. The bell swings, bats circle the tower, night
clouds drift behind it, the last open office glows, a paper crane drifts by, oak leaves fall."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from midlib import sprite_from_cell
from pixel import Canvas, C, shade, mix
from props import shrub, MUM
from lib_norlin import stone_wall, STONE_N, LIME
from lib_oldmain import (old_main, night_sky, gas_lamp, bell, HERRING, GRASS_OM, TRIM_OM, NIGHT_CLOUD, OM_HALF,
                         TOWER_HALF)
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from surfaces import LEAVES

ROOM = "O01"
INK = "#10121e"
HAZE = "#2a2442"
HORIZON, CAM = 112, 38         # a low camera looking up at the tower (feet line y 150 at Z 320)
Z_OM = 1300.0                 # the facade plane
STEP_N, STEP_D, STEP_R = 4, 14.0, 7.0     # treads, tread depth, rise (world units)
STEP_HALF = 150.0
Z_STEPS = Z_OM - STEP_N * STEP_D            # front edge of the lowest tread
FRAME_X = 262.0               # sandstone bands framing the forecourt
BAND = 9.0
Z_CROSS = Z_STEPS - 26.0      # band along the foot of the steps
LAWN_X = (318.0, 900.0)
LAWN_Z = (380.0, Z_CROSS - 30)
WALL_X = 940.0                # garden walls on both sides
MEDAL = (0.0, 540.0)
LAMPS = [(-FRAME_X - 26, 560.0), (FRAME_X + 26, 560.0), (-FRAME_X - 26, 800.0), (FRAME_X + 26, 800.0)]
LAMP_H = 68 * ROOM_TO_BATTLE
OAK = (-640.0, 690.0, 340.0)  # x, z, height in world units
SPRUCE = (660.0, 760.0, 380.0)
FACADE_W, FACADE_H, FACADE_BASE = 620, 300, 290


def ground_shader(X, Z):
    n = X.shape[0]
    a = 6.0
    # herringbone brick (same zig-zag as the room's courtyard, in world units)
    cu, cw = np.floor(X / a), np.floor(-Z / a)
    fx, fy = X / a - cu, -Z / a - cw
    d = cu - cw
    r = np.mod(d, 4)
    b = -(d - r) / 4
    k = np.where(r == 0, cu + 2 * b, np.where(r == 1, cu + 2 * b - 1, cu - 2 + 2 * b))
    horiz = r < 2
    t = hash2(k * 2 + horiz, b, 11)
    p = pal_array(HERRING)
    idx = np.select([t < 0.08, t < 0.3, t < 0.66, t < 0.9], [2, 3, 4, 5], 6)
    rgb = p[idx]
    jt = 0.16
    joint = np.where(horiz, (fy > 1 - jt) | ((r == 1) & (fx > 1 - jt)), (fx > 1 - jt) | ((r == 2) & (fy > 1 - jt)))
    rgb[joint] = p[1]
    ax = np.abs(X)
    # lawn panels either side of the forecourt
    lawn = (ax > LAWN_X[0]) & (ax < LAWN_X[1]) & (Z > LAWN_Z[0]) & (Z < LAWN_Z[1])
    g = pal_array(GRASS_OM)
    stripe = (np.floor((Z + 8 * np.sin(X / 40.0)) / 46.0) % 2).astype(int)
    tuft = hash2(np.floor(X / 3), np.floor(Z / 5), 9)
    gr = np.where(stripe[:, None] == 0, g[3], g[2]) * (0.94 + 0.12 * tuft[:, None])
    rgb[lawn] = gr[lawn]
    edge = lawn & ((np.abs(ax - LAWN_X[0]) < 3) | (np.abs(Z - LAWN_Z[0]) < 4) | (np.abs(Z - LAWN_Z[1]) < 4))
    rgb[edge] = g[5]
    # sandstone bands: the forecourt frame and the band along the foot of the steps
    tr = pal_array(TRIM_OM)
    band = ((np.abs(ax - FRAME_X) < BAND / 2) & (Z > 330) & (Z < Z_CROSS)) | ((np.abs(Z - Z_CROSS) < BAND / 2) & (ax < WALL_X))
    rgb[band] = tr[2]
    rgb[band & (hash2(np.floor(X / 30), np.floor(Z / 30), 4) < 0.4)] = tr[3]
    # the Old Main medallion: rings, rays, a bronze plate
    mx, mz = MEDAL
    dd = np.hypot(X - mx, (Z - mz) * 1.0)
    ring = (np.abs(dd - 96) < 4) | (np.abs(dd - 70) < 3)
    rgb[ring] = tr[3]
    ang = np.arctan2(Z - mz, X - mx)
    rays = (dd > 72) & (dd < 93) & (np.abs(((ang / (2 * np.pi) * 24) % 1) - 0.5) > 0.36)
    rgb[rays] = p[5]
    rgb[(dd > 72) & (dd < 93) & ~rays] = p[2]
    plate = (np.abs(X - mx) < 34) & (np.abs(Z - mz) < 16)
    rgb[plate] = np.array(C("#a8843e")[:3])
    rgb[plate & ((np.abs(X - mx) > 30) | (np.abs(Z - mz) > 13))] = np.array(C("#6a4e2a")[:3])
    # leaves: drifts under the oak and along the bands
    cell = hash2(np.floor(X / 6), np.floor(Z / 6), 21)
    drift = np.clip(1 - np.hypot(X - OAK[0], (Z - OAK[1]) * 0.8) / 380, 0, 1) * 0.6
    drift += np.clip(1 - np.abs(ax - FRAME_X) / 40, 0, 1) * 0.25
    leaf = cell < drift * 0.5
    pick = (hash2(np.floor(X / 6), np.floor(Z / 6), 22) * 4).astype(int)
    rgb[leaf] = pal_array(LEAVES)[np.clip(pick[leaf], 0, 3)]
    # warm light: the open door down the forecourt, the lamps, the lanterns
    warm_light(rgb, np.hypot(X * 0.8, (Z - Z_OM) * 0.35), 190, strength=0.42)
    for (lx, lz) in LAMPS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.5), 120, strength=0.42)
    # cool moonlight sheen across the middle of the court
    rgb *= 1.0
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 900, 2800, amount=0.8)
    return out


def steps_tread(height, z0, z1):
    def shade_(X, Z):
        tr = pal_array(TRIM_OM)
        inside = (np.abs(X) < STEP_HALF + (z1 - Z) * 0.0) & (Z >= z0) & (Z < z1)
        rgb = np.zeros((X.shape[0], 3), np.float32) + tr[3]
        rgb[Z > z1 - 2.5] = tr[4]
        joint = np.abs(((X + 13 * (height / STEP_R)) % 46) - 23) > 22
        rgb[joint] = tr[2]
        warm_light(rgb, np.hypot(X * 0.8, (Z - Z_OM) * 0.35), 190, strength=0.5)
        out = rgba_of(rgb)
        out[~inside, 3] = 0
        return fog(out, Z, HAZE, 900, 2800, amount=0.8)
    return shade_


def wall_texture(length, height=34, seed=0):
    cv = Canvas(length, height + 4)
    stone_wall(cv, 0, 4, length, height, pal=[shade(c, -0.3) for c in STONE_N], seed=seed, course=5)
    cv.rect(0, 0, length, 5, shade(LIME[2], -0.2)); cv.hline(0, 0, length, shade(LIME[4], -0.2))
    return cv.a


def treeline(width=640, seed=3):
    rng = np.random.default_rng(seed)
    cv = Canvas(width, 40)
    base = 39
    for x in range(-10, width + 10, 9):
        h = int(rng.integers(10, 24))
        cv.ellipse(x, base - h, int(rng.integers(12, 20)), h * 2, "#231f3a")
    for (x0, w, h) in [(10, 50, 14), (560, 60, 16), (610, 40, 12)]:
        cv.rect(x0, base - h, w, h, "#1e1a32")
        cv.poly([(x0 - 2, base - h), (x0 + w // 2, base - h - 6), (x0 + w + 2, base - h)], "#1e1a32")
        for wx in range(x0 + 3, x0 + w - 3, 6):
            if rng.random() < 0.4:
                cv.rect(wx, base - h + 4, 2, 2, "#c98a46")
    for x in range(-6, width, 6):
        h = int(rng.integers(5, 11))
        cv.ellipse(x, base - h + 4, int(rng.integers(8, 14)), h * 2, "#1a1730")
    cv.a[base:, :, 3] = 0
    return cv.a


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=HORIZON, cam=CAM, fill="#141223")
    # sky (not solid: clouds drift behind everything), the far treeline
    sky = Canvas(640, 134)
    stars = night_sky(sky, 640, 134, seed=7, stars=170, moon=(116, 36), clouds=[(20, 70, 80, 2)])
    v.strip(sky.a, 0, solid=False)
    v.strip(treeline(), HORIZON - 39 + 6)
    v.ground(ground_shader)

    # garden walls along the facade line and down both sides of the courtyard
    for side in (-1, 1):
        L = int(Z_OM - 300)
        tex = wall_texture(L + 40, 34, seed=side + 5)
        def wall(u, Y, Z, tex=tex):
            o = texture_lookup(tex, u, 38 - Y, wrap=True)
            return fog(o, Z, HAZE, 900, 2800, amount=0.8)
        v.plane((side * WALL_X, 300.0), (side * WALL_X, Z_OM), wall, y_max=38)
    back = wall_texture(1400, 34, seed=9)
    v.back(Z_OM + 4, lambda X, Y: fog(texture_lookup(back, X + 700, 38 - Y, wrap=True), np.full(X.shape, Z_OM), HAZE, 900, 2800, 0.8),
           region=lambda X, Y: (np.abs(X) > OM_HALF * ROOM_TO_BATTLE - 10) & (np.abs(X) < WALL_X) & (Y >= 0) & (Y <= 38))
    rng = np.random.default_rng(12)
    for x in np.arange(-WALL_X + 10, WALL_X, 34.0):
        if abs(x) < OM_HALF * ROOM_TO_BATTLE:
            continue
        s_ = v.scale(Z_OM + 6)
        spr = shrub(0, 0, max(6, int(48 * s_)), max(5, int(30 * s_)), seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None)
        v.sprite(spr.a, float(x), Z_OM + 6, Y=36.0, scale=(Z_OM + 6) / v.F)
    for side in (-1, 1):
        for z in np.arange(340.0, Z_OM, 30.0):
            s_ = v.scale(z)
            spr = shrub(0, 0, max(6, int(50 * s_)), max(5, int(32 * s_)), seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None)
            v.sprite(spr.a, side * (WALL_X + 6), float(z), Y=36.0, scale=z / v.F)

    # Old Main: the whole front (the tower runs out of the top of the frame), steps, then the court
    fac = Canvas(FACADE_W, FACADE_H)
    info = old_main(fac, FACADE_W // 2, FACADE_BASE, seed=4,
                    lit={"g4": "dim", "g5": "dim", "u3": "dim", "g7": "dim", "u9": "dim"}, office="u6")
    om_at = v.sprite(fac.a, 0.0, Z_OM, anchor=(0.5, FACADE_BASE / FACADE_H), scale=ROOM_TO_BATTLE)
    s_fac = om_at[2]
    def fac_to_screen(px, py):
        return (om_at[0] + (px - FACADE_W / 2) * s_fac, om_at[1] + (py - FACADE_BASE) * s_fac)
    # steps: risers and treads in front of the door
    for i in range(STEP_N):
        z_back = Z_OM - i * STEP_D
        h = (STEP_N - i) * STEP_R
        tr = pal_array(TRIM_OM)
        def riser(X, Y, h=h):
            o = np.zeros(X.shape + (4,), np.float32)
            o[..., :3] = shade(TRIM_OM[1], -0.25) if False else tr[1] * 0.78
            o[Y > h - 2.2, :3] = tr[4]
            o[(Y > h - 3.4) & (Y <= h - 2.2), :3] = tr[2]
            o[np.abs(((X + 7 * h) % 52) - 26) > 25, :3] = tr[0]
            o[..., 3] = 1
            warm_light(o[..., :3], np.abs(X) * 0.8, 190, strength=0.3)
            return o
        v.back(z_back - STEP_D, riser, region=lambda X, Y, h=h: (np.abs(X) < STEP_HALF) & (Y >= h - STEP_R) & (Y <= h))
        v.ground(steps_tread(h, z_back - STEP_D, z_back), height=h, z_max=z_back + 1)

    # trees, lamps (far to near)
    items = [(OAK[1], "tree", OAK, 5), (SPRUCE[1], "tree", SPRUCE, 6)] + [(z, "lamp", (x, z), 0) for (x, z) in LAMPS]
    glows = []
    for z, kind, data, cell in sorted(items, key=lambda t: -t[0]):
        if kind == "tree":
            x, z_, hw = data
            h = int(round(hw * v.scale(z_)))
            spr = sprite_from_cell(cell, height=h, colors=40, brightness=0.82)
            if cell == 6:
                spr = spr[:, ::-1].copy()
            v.sprite(spr, x, z_, scale=z_ / v.F)
        else:
            x, z_ = data
            h = int(round(LAMP_H * v.scale(z_)))
            spr, ax, ay = gas_lamp(max(24, h))
            sx, sy, _ = v.sprite(spr.a, x, z_, anchor=(ax / spr.w, ay / spr.h), scale=z_ / v.F)
            glows.append([int(round(sx)), int(round(sy - ay + 11 * h / 68)), "fff0c4", 2 if z_ < 700 else 1])

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp leaves on the near brick, the bell's yoke
    for _ in range(220):
        lx, ly = int(rng.integers(0, 640)), int(rng.integers(150, 360))
        if rng.random() < 0.5 and lx > 320:
            continue
        c = LEAVES[int(rng.integers(4))]
        dim = 1 - min(0.6, max(0.0, (ly - 156) / 204 * 0.62))
        col = tuple(np.array(C(c)[:3]) * dim)
        cv.px(lx, ly, col); cv.px(lx + 1, ly, tuple(np.array(col) * 0.8))
    bx, by = fac_to_screen(*info["bell"])
    bx, by = int(round(bx)), int(round(by))
    ox, oy, ow, oh = info["belfry"]
    cv.hline(bx - 5, by - 3, 11, "#4a2e22"); cv.hline(bx - 5, by - 4, 11, "#6e4430")
    solid = v.solid_mask()
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = solid.astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))
    from clouds import cloud_strip
    cloud_strip(640, 40, count=4, seed=5, pal=NIGHT_CLOUD, sizes=(50, 110)).save(os.path.join(out, "battle-clouds.png"))

    # the bell swings: four frames played 0-1-2-3-2-1
    angles = [-0.42, -0.16, 0.16, 0.42]
    pats = ["100000", "010001", "001010", "000100"]
    layers = []
    for i, ang in enumerate(angles):
        b = Canvas(20, 16)
        bell(b, 10, 3, size=4, angle=ang, yoke=False)
        name = f"battle-bell-{i}.png"
        b.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": pats[i], "rate": 3.0, "texture": res + name, "x": bx - 10, "y": by - 3})
    # lights: lanterns at the door, the office window, lamps; stars
    for (lx, ly) in info["lanterns"]:
        sx, sy = fac_to_screen(lx, ly)
        glows.append([int(round(sx)), int(round(sy)), "fde9b6", 1])
    wx, wy, ww, wh = info["windows"]["u6"]
    sx, sy = fac_to_screen(wx + ww / 2, wy + wh / 2)
    glows.append([int(round(sx)), int(round(sy)), "fff0c4", 1])
    star_pts = [[sx_, sy_, "c8c0e0", 0] for (sx_, sy_, c) in stars[::5] if sy_ < 70 and not (392 <= sx_ <= 628 and sy_ <= 70)]
    layers += [
        {"kind": "drift", "depth": "far", "texture": res + "battle-clouds.png", "y": 8, "speed": 2.0, "alpha": 0.85},
        {"kind": "fauna", "depth": "far", "fauna": [
            {"kind": "night_bat", "x": 260, "y": 20, "fly": 12.0, "rate": 7.0},
            {"kind": "night_bat", "x": 360, "y": 34, "fly": 9.0, "rate": 6.0},
            {"kind": "night_bat", "x": 60, "y": 48, "fly": 14.0, "rate": 7.5}]},
        {"kind": "twinkle", "points": glows, "rate": 1.6, "min": 0.45},
        {"kind": "twinkle", "points": star_pts, "rate": 0.9, "min": 0.0, "depth": "far"},
        {"kind": "particles", "style": "leaf", "count": 14, "rect": [-20, 0, 300, 165], "speed": [26, 18]},
        {"kind": "particles", "style": "leaf", "count": 6, "rect": [440, 30, 220, 135], "speed": [-14, 16]},
        {"kind": "fauna", "fauna": [{"kind": "om_crane", "x": 120, "y": 96, "fly": 6.0, "rate": 3.0}]},
    ]
    return {"far": res + "battle-far.png", "near": res + "battle-near.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
