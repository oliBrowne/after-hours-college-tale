"""Battle backdrop for the UMC terrace: looking down the terrace path at the lit doors of the UMC,
the Flatirons beyond, lamps and trees receding. Rendered in one-point perspective."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from midlib import sprite_from_cell
from pixel import Canvas, C, shade
from sky import panorama
from surfaces import ashlar_wall
from facade import umc_facade, steps, TRIM
from props import lamp_post, shrub, MUM, LEAF
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

PAVE = ["#3e343b", "#4a3f45", "#5a4e52", "#665a5c", "#6c5f60", "#726465", "#7b6c6b"]
PATH = ["#4a2e2c", "#5e3a34", "#70463a", "#7d5040", "#8c5c48", "#a06e56"]
WALL = ["#3a2c31", "#5b4644", "#8a6e60", "#9a7c6b", "#b49481", "#cdb099"]
LAWN = ["#141c1c", "#1a2624", "#22302b", "#2a3a31"]
LEAVES = ["#c8682e", "#a83c32", "#d9a441", "#8c4a2a"]
HAZE = "#4a3a52"
INK = "#10121e"

Z_UMC = 760.0
PATH_HALF = 68
WALL_X = 250
LAMPS = [(-185, 470), (185, 470), (-140, 690), (140, 690)]
LAMP_H = 112


def ground_shader(X, Z):
    n = X.shape[0]
    rgb = np.zeros((n, 3), np.float32)
    ax = np.abs(X)
    # Terrace flagstones: rows 26 deep, stone widths vary per row.
    row = np.floor(Z / 26.0)
    width = 30 + 22 * hash2(row, 7)
    off = hash2(row, 11) * width
    col = np.floor((X + off) / width)
    fx = (X + off) / width - col
    fz = Z / 26.0 - row
    tone = hash2(col, row, 3)
    pave = pal_array(PAVE)
    rgb[:] = pave[3] * (1 - tone[:, None] * 0.6) + pave[5] * (tone[:, None] * 0.6)
    edge = (fx < 2.2 / width) | (fz < 0.09)
    rgb[edge] = pave[1]
    lit_edge = (fz > 0.9) & ~edge
    rgb[lit_edge] = rgb[lit_edge] * 0.8 + pave[6] * 0.2
    # Path of warm pavers in running bond, between limestone kerbs.
    path = ax < PATH_HALF
    prow = np.floor(Z / 12.0)
    pcol = np.floor((X + (prow % 2) * 9) / 18.0)
    pf = (X + (prow % 2) * 9) / 18.0 - pcol
    pz = Z / 12.0 - prow
    pt = hash2(pcol, prow, 5)
    pp = pal_array(PATH)
    prgb = pp[2] * (1 - pt[:, None]) + pp[4] * pt[:, None]
    prgb[(pf < 0.08) | (pz < 0.14)] = pp[0]
    rgb[path] = prgb[path]
    kerb = (ax >= PATH_HALF) & (ax < PATH_HALF + 7)
    rgb[kerb] = pal_array(TRIM)[2]
    rgb[kerb & (ax < PATH_HALF + 1.5)] = pal_array(TRIM)[4]
    # Lawn beyond the terrace walls.
    lawn = ax > WALL_X + 6
    lt = hash2(np.floor(X / 5), np.floor(Z / 9), 9)
    rgb[lawn] = pal_array(LAWN)[np.clip((lt[lawn] * 4).astype(int), 0, 3)]
    # Compass inlay where the fight happens.
    d = np.hypot(X, (Z - 360) * 1.0)
    ring = (np.abs(d - 50) < 4) & (Z < 600)
    rgb[ring] = pal_array(TRIM)[1]
    rgb[(np.abs(d - 50) < 1.3) & (Z < 600)] = pal_array(TRIM)[3]
    # Fallen leaves in drifts along the walls and under the oak.
    cell = hash2(np.floor(X / 6), np.floor(Z / 6), 21)
    drift = np.clip(1 - np.abs(ax - (WALL_X - 8)) / 70, 0, 1) * 0.5 + np.clip(1 - np.hypot(X + 330, Z - 600) / 260, 0, 1) * 0.35
    drift += np.clip(1 - np.abs(ax - PATH_HALF - 10) / 18, 0, 1) * 0.25
    leaf = (cell < drift * 0.55) & ~lawn & (Z > 260)
    pick = (hash2(np.floor(X / 6), np.floor(Z / 6), 22) * 4).astype(int)
    rgb[leaf] = pal_array(LEAVES)[np.clip(pick[leaf], 0, 3)]
    # Lamp light on the ground, the doors' spill on the path.
    for (lx, lz) in LAMPS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.45), 105, strength=0.45)
    warm_light(rgb, np.hypot(X * 0.9, (Z - Z_UMC) * 0.35), 120, strength=0.55)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 900, 2600, amount=0.85)
    return out


def umc_sprite():
    cv = Canvas(372, 132)
    umc_facade(cv, 16, 356, 124, 132, 240, 126)
    cv.a[127:, :, 3] = 0
    return cv.a


def wall_texture(length, height=20, seed=4):
    cv = Canvas(length, height)
    ashlar_wall(cv, 0, 0, length, height, WALL, seed=seed)
    return cv.a


def wall_shader(tex, height):
    def shade_(u, Y, Z):
        out = texture_lookup(tex, u, height - Y, wrap=True)
        return fog(out, Z, HAZE, 900, 2600, amount=0.85)
    return shade_


def treeline(width=640, seed=3):
    """Distant campus: dark tree crowns and rooftops along the horizon, a few windows lit."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width, 34)
    base = 33
    far, near = "#2b2440", "#231d36"
    for x in range(-10, width + 10, 9):
        h = int(rng.integers(9, 20))
        cv.ellipse(x, base - h, int(rng.integers(12, 20)), h * 2, far)
    for x in range(-4, width, int(rng.integers(40, 60))):
        if 200 < x < 440:
            continue
        w = int(rng.integers(24, 44)); h = int(rng.integers(10, 18))
        cv.rect(x, base - h, w, h, near)
        cv.poly([(x - 2, base - h), (x + w // 2, base - h - 6), (x + w + 2, base - h)], near)
        for wx in range(x + 3, x + w - 3, 5):
            if rng.random() < 0.35:
                cv.rect(wx, base - h + 4, 2, 2, "#c98a46" if rng.random() < 0.7 else "#e9b45c")
    for x in range(-6, width, 6):
        h = int(rng.integers(5, 11))
        cv.ellipse(x, base - h + 4, int(rng.integers(8, 14)), h * 2, "#1c1830")
    cv.a[base:, :, 3] = 0
    return cv.a


def build(project):
    out = os.path.join(project, "assets/art/rooms/U02")
    v = View(horizon=98, cam=52)
    # Sky with the Flatirons (the mountains count as solid so clouds pass behind them).
    sky, _ = panorama(640, 132, scale=1.9)
    v.strip(sky, 0, solid=False)
    rowc = np.median(sky[:, :8, :3], axis=1)
    lum = lambda a: a[..., :3] @ np.array([0.3, 0.55, 0.15], np.float32)
    peaks = (lum(sky) < lum(rowc[:, None, :]) - 0.1) & (np.arange(132)[:, None] > 20)
    v.solid[:132 * 3] |= np.repeat(np.repeat(peaks, 3, 0), 3, 1)
    v.strip(treeline(), 98 - 33 + 4)
    v.ground(ground_shader)

    # Back to front: distant trees, the UMC, the lawn trees, shrubs, walls, lamps.
    pine_far = [(-520, 1500), (520, 1400), (-380, 1150), (400, 1050)]
    for i, (x, z) in enumerate(pine_far):
        h = int(round(260 * v.scale(z)))
        spr = sprite_from_cell(6 if i % 2 else 5, height=h, colors=24, brightness=0.62, saturation=0.75)
        v.sprite(spr, x, z, scale=z / v.F)
    umc_at = v.sprite(umc_sprite(), 0, Z_UMC, anchor=(0.5, 124 / 132), scale=ROOM_TO_BATTLE)
    st = Canvas(120, 20)
    steps(st, 60, 0, 60, 4, rise=4, spread=6)
    v.sprite(st.a, 0, Z_UMC - 6, anchor=(0.5, 0.0), Y=0.0, scale=ROOM_TO_BATTLE * 0.8)

    rng = np.random.default_rng(12)
    shrubs = []
    for side in (-1, 1):
        for z in np.arange(330, Z_UMC + 40, 28):
            shrubs.append((side * (WALL_X + 18 + rng.integers(0, 14)), float(z) + rng.uniform(-6, 6)))
    big_trees = [(-420, 650, 5, 330), (430, 700, 6, 360)]
    items = [(z, "shrub", x) for (x, z) in shrubs] + [(z, "tree", (x, cell, hw)) for (x, z, cell, hw) in big_trees]
    for z, kind, data in sorted(items, key=lambda t: -t[0]):
        if kind == "shrub":
            w = int(round(46 * v.scale(z))); h = int(round(34 * v.scale(z)))
            spr = shrub(0, 0, max(6, w), max(5, h), seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None)
            v.sprite(spr.a, data, z, scale=z / v.F)
        else:
            x, cell, hw = data
            h = int(round(hw * v.scale(z)))
            spr = sprite_from_cell(cell, height=h, colors=40, brightness=0.85)
            v.sprite(spr, x, z, scale=z / v.F)

    for side in (-1, 1):
        L = int(Z_UMC - 300)
        v.plane((side * WALL_X, 300.0), (side * WALL_X, Z_UMC), wall_shader(wall_texture(L, 20, seed=side + 5), 20), y_max=20)

    glows = []
    for (x, z) in sorted(LAMPS, key=lambda t: -t[1]):
        h = int(round(LAMP_H * v.scale(z)))
        spr, ax, ay = lamp_post(max(24, h))
        sx, sy, _ = v.sprite(spr.a, x, z, anchor=(ax / spr.w, ay / spr.h), scale=z / v.F)
        glows.append([int(round(sx)), int(round(sy - ay + 11)), "fff0c4", 2])
    # door lanterns on the pavilion (canvas x 186 +- 30, y 82), scaled like the facade
    s = ROOM_TO_BATTLE * v.scale(Z_UMC)
    for dx in (-30, 30):
        glows.append([int(round(umc_at[0] + dx * s)), int(round(umc_at[1] - (124 - 86) * s)), "fde9b6", 1])

    # Darken under the battle menus so the panels sit on shadow, not on paving.
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    # Crisp leaves scattered on the near paving (world-space leaves would be blocky this close).
    for _ in range(260):
        lx, ly = int(rng.integers(0, 640)), int(rng.integers(150, 360))
        c = LEAVES[int(rng.integers(4))]
        if abs(lx - 320) < (ly - 98) * 1.3 * PATH_HALF / 52 and rng.random() < 0.7:
            continue
        dim = 1 - min(0.6, max(0.0, (ly - 156) / 204 * 0.62))
        col = tuple(np.array(C(c)[:3]) * dim)
        cv.px(lx, ly, col); cv.px(lx + 1, ly, tuple(np.array(col) * 0.8))
    solid = v.solid_mask()
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = solid.astype(np.float32)
    Canvas(640, 360).image  # noqa (keeps import use obvious)
    from PIL import Image
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))
    from clouds import cloud_strip
    cloud_strip(640, 44, count=5, seed=3).save(os.path.join(out, "battle-clouds.png"))
    res = "res://assets/art/rooms/U02/"
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "drift", "depth": "far", "texture": res + "battle-clouds.png", "y": 2, "speed": 2.5},
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "bird", "x": 40, "y": 30, "fly": 11.0, "rate": 4.0},
                {"kind": "bird", "x": 330, "y": 18, "fly": 8.0, "rate": 3.2},
                {"kind": "bird", "x": 352, "y": 24, "fly": 8.0, "rate": 3.6}]},
            {"kind": "twinkle", "points": glows, "rate": 1.7, "min": 0.45},
            {"kind": "particles", "style": "leaf", "count": 16, "rect": [-20, -10, 680, 175], "speed": [34, 16]},
            {"kind": "particles", "style": "wind", "count": 4, "rect": [-120, 20, 880, 120], "speed": [240, 0]},
        ],
    }


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
