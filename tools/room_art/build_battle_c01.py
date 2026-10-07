"""Battle backdrop for the Fountain Court (C01): standing in the court looking north across the
Dalton Trumbo fountain at the UMC, its pavilion doors open and lit. The fighters stand on the
sandstone flags in front of the basin; the row of jets rises between them and the building, the
water carries the windows' reflections, string lights from the truck lane cross the top left with
a food truck under them, a lamp-lit coffee cart stands at the right, and the Flatirons hold the
last of the sunset. Moving: the jets' spray and sparkle, the bulbs, clouds, birds, a few leaves."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from midlib import sprite_from_cell
from pixel import Canvas, C, shade
from sky import panorama
from props import lamp_post, shrub, MUM
from facade import TRIM, SANDSTONE
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_farrand import food_truck, string_across, TRUCK_MUSTARD
from build_battle_u02 import treeline
from c01_lib import umc_front, coffee_cart, PAVE, PAVER, COURT, WATER, JET, BRONZE

ROOM = "C01"
INK = "#10121e"
HAZE = "#4a3a52"
LEAVES = ["#c8682e", "#a83c32", "#d9a441", "#8c4a2a"]
Z_UMC = 980.0
BASIN = (-190.0, 190.0, 372.0, 520.0)      # X0, X1, Z near, Z far
RIM = 9.0                                  # coping width in world units
COURT_X, COURT_Z = 360.0, (300.0, 940.0)
JETS = [(-144, 40), (-96, 52), (-48, 62), (0, 80), (48, 62), (96, 52), (144, 40)]
Z_JETS = 446.0
LAMPS = [(-330, 560), (250, 600)]       # left lamp kept clear of the CU BOOK STORE sign
LAMP_H = 112
WINDOW_X = [-170, -120, -66, -22, 0, 22, 66, 120, 170]   # lit windows reflected in the water


def ground_shader(X, Z):
    n = X.shape[0]
    rgb = np.zeros((n, 3), np.float32)
    ax = np.abs(X)
    # campus flagstones beyond the court
    row = np.floor(Z / 26.0)
    width = 30 + 22 * hash2(row, 7)
    off = hash2(row, 11) * width
    col = np.floor((X + off) / width)
    fx = (X + off) / width - col
    fz = Z / 26.0 - row
    tone = hash2(col, row, 3)
    pave = pal_array(PAVE)
    rgb[:] = pave[3] * (1 - tone[:, None] * 0.6) + pave[5] * (tone[:, None] * 0.6)
    rgb[(fx < 2.2 / width) | (fz < 0.09)] = pave[1]
    # the court: square sandstone flags in a grid
    court = (ax < COURT_X) & (Z > COURT_Z[0]) & (Z < COURT_Z[1])
    cu, cz = X / 30.0, Z / 22.0
    ct = hash2(np.floor(cu), np.floor(cz), 5)
    cp = pal_array(COURT)
    crgb = cp[3] * (1 - ct[:, None] * 0.5) + cp[5] * (ct[:, None] * 0.5)
    joint = ((cu - np.floor(cu)) < 0.06) | ((cz - np.floor(cz)) < 0.08)
    crgb[joint] = cp[1]
    rgb[court] = crgb[court]
    # brick bands: the court's border, a frame round the basin, the runner to the UMC doors
    pp = pal_array(PAVER)
    prow = np.floor(Z / 8.0)
    pcol = np.floor((X + (prow % 2) * 6) / 12.0)
    pt = hash2(pcol, prow, 9)
    prgb = pp[2] * (1 - pt[:, None]) + pp[4] * pt[:, None]
    prgb[((X + (prow % 2) * 6) / 12.0 - pcol < 0.1) | (Z / 8.0 - prow < 0.14)] = pp[0]
    X0, X1, Zn, Zf = BASIN
    border = court & ((ax > COURT_X - 14) | (Z < COURT_Z[0] + 14) | (Z > COURT_Z[1] - 14))
    frame = (ax < X1 + 34) & (Z > Zn - 30) & (Z < Zf + 30) & ~((ax < X1 + 22) & (Z > Zn - 18) & (Z < Zf + 18))
    runner = (ax < 36) & (Z > Zf) & (Z < Z_UMC)
    axis = (np.abs(Z - (Zn + Zf) / 2) < 6) & (ax > X1 + 22) & court
    brick = border | frame | runner | axis
    rgb[brick] = prgb[brick]
    # the basin: coping round the rim, water inside with the windows' warm reflections
    inside = (X > X0) & (X < X1) & (Z > Zn) & (Z < Zf)
    water = (X > X0 + RIM) & (X < X1 - RIM) & (Z > Zn + RIM) & (Z < Zf - RIM)
    tp = pal_array(TRIM)
    rgb[inside & ~water] = tp[2]
    rgb[inside & ~water & ((Z < Zn + 2) | (Z > Zf - 2) | (np.abs(ax - X1) < 2))] = tp[3]
    wp = pal_array(WATER)
    ripple = hash2(np.floor(X / 5), np.floor(Z / 3), 13)
    wr = wp[2] * (1 - ripple[:, None] * 0.5) + wp[3] * (ripple[:, None] * 0.5)
    wr[ripple > 0.9] = wp[5]
    for wx in WINDOW_X:
        streak = (np.abs(X - wx) < (6 if wx else 11)) & (hash2(np.floor(X / 3), np.floor(Z / 4), 17) < 0.65)
        wr[streak] = wr[streak] * 0.4 + np.array(C("#f6cf7a")[:3]) * 0.6
    for (jx, _) in JETS:
        d = np.hypot((X - jx) / 1.0, (Z - Z_JETS) * 0.55)
        wr[d < 13] = wp[5]
        wr[d < 8] = wp[6]
        wr[d < 4] = wp[7]
    rgb[water] = wr[water]
    # lamp light, the doors' spill up the runner, the basin's glow
    for (lx, lz) in LAMPS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.45), 100, strength=0.42)
    warm_light(rgb, np.hypot(X * 0.9, (Z - Z_UMC) * 0.35), 120, strength=0.5)
    # leaves blown into the court's corners
    cell = hash2(np.floor(X / 6), np.floor(Z / 6), 21)
    drift = np.clip(1 - np.abs(ax - COURT_X) / 60, 0, 1) * 0.4
    leaf = (cell < drift * 0.5) & ~inside
    pick = (hash2(np.floor(X / 6), np.floor(Z / 6), 22) * 4).astype(int)
    rgb[leaf] = pal_array(LEAVES)[np.clip(pick[leaf], 0, 3)]
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 1000, 2800, amount=0.85)
    return out


def rim_texture(length, height=12):
    """The basin's near face: sandstone courses with the bronze plaque in the middle."""
    cv = Canvas(length, height)
    cv.rect(0, 0, length, height, SANDSTONE[3])
    for yy in range(3, height, 4):
        cv.hline(0, yy, length, SANDSTONE[2])
        for xx in range((yy // 4) % 2 * 9, length, 18):
            cv.vline(xx, yy - 3, 3, SANDSTONE[2])
    cv.hline(0, 0, length, SANDSTONE[5])
    cv.rect(length // 2 - 60, 2, 120, height - 4, BRONZE[2]); cv.hline(length // 2 - 60, 2, 120, BRONZE[4])
    for xx in range(length // 2 - 54, length // 2 + 54, 4):
        cv.rect(xx, height // 2 - 1, 3, 2, "#f2d690")
    return cv.a


def jet_sprite(h):
    """One jet at room scale: a white core inside a pale, wider sheath of water, a crown of drops
    arcing out and down, a splash collar at the foot."""
    cv = Canvas(23, h + 6)
    cx, ty = 11, 4
    cv.rect(cx - 3, ty + 6, 7, h - 6, C(JET[0], 0.45))
    cv.rect(cx - 2, ty + 2, 5, h - 2, C(JET[1], 0.85))
    cv.rect(cx - 1, ty, 3, h, JET[3])
    cv.vline(cx - 2, ty + 6, h - 12, JET[2])
    for side in (-1, 1):
        for k in range(1, 10):
            yy = ty + int(round(k * k * 0.3)) - 1
            cv.px(cx + side * (k + 1), yy, JET[2] if k < 4 else C(JET[1], 0.8))
            if k % 2:
                cv.px(cx + side * (k + 1), yy + 3, C(JET[1], 0.6))
    cv.rect(cx - 2, ty - 2, 5, 3, JET[3])
    cv.rect(cx - 6, ty + h - 3, 13, 3, C(JET[2], 0.8)); cv.hline(cx - 4, ty + h - 4, 9, JET[3])
    return cv.a


def umc_sprite():
    cv = Canvas(772, 222)
    umc_front(cv, 10, 762, 216, 296, 476, 146, 626, 220)
    cv.a[221:, :, 3] = 0
    return cv.a


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    v = View(horizon=98, cam=52)
    sky, _ = panorama(640, 132, scale=1.9)
    v.strip(sky, 0, solid=False)
    rowc = np.median(sky[:, :8, :3], axis=1)
    lum = lambda a: a[..., :3] @ np.array([0.3, 0.55, 0.15], np.float32)
    peaks = (lum(sky) < lum(rowc[:, None, :]) - 0.1) & (np.arange(132)[:, None] > 20)
    v.solid[:132 * 3] |= np.repeat(np.repeat(peaks, 3, 0), 3, 1)
    v.strip(treeline(seed=5), 98 - 33 + 4)
    v.ground(ground_shader)

    # back to front: far trees, the UMC, the truck lane, lamps, the basin's faces, the jets
    for i, (x, z) in enumerate([(-560, 1500), (560, 1400), (-470, 1150), (480, 1100)]):
        h = int(round(260 * v.scale(z)))
        spr = sprite_from_cell(6 if i % 2 else 5, height=h, colors=24, brightness=0.62, saturation=0.75)
        v.sprite(spr, x, z, scale=z / v.F)
    umc_at = v.sprite(umc_sprite(), 0, Z_UMC, anchor=(0.5, 216 / 222), scale=ROOM_TO_BATTLE)
    truck, tax, tay, tinfo = food_truck(width=140, height=76, pal=TRUCK_MUSTARD, name="GREEN CHILE", seed=20, facing=1)
    tsx, tsy, ts = v.sprite(truck.a, -560, 860, anchor=(tax / truck.w, tay / truck.h), scale=ROOM_TO_BATTLE)
    cart, cax, cay, cbulbs = coffee_cart(seed=3)
    csx, csy, cs = v.sprite(cart.a, 470, 640, anchor=(cax / cart.w, cay / cart.h), scale=ROOM_TO_BATTLE)
    rng = np.random.default_rng(12)
    glows = []
    X0, X1, Zn, Zf = BASIN
    for (x, z) in sorted(LAMPS, key=lambda t: -t[1]):
        if z < Zn:
            continue
        h = int(round(LAMP_H * v.scale(z)))
        spr, ax, ay = lamp_post(max(24, h))
        sx, sy, _ = v.sprite(spr.a, x, z, anchor=(ax / spr.w, ay / spr.h), scale=z / v.F)
        glows.append([int(round(sx)), int(round(sy - ay + 11)), "fff0c4", 2])
    # far inner face of the rim, then the jets, then the near face with the plaque
    tex = rim_texture(int(X1 - X0), 12)
    v.plane((X0 + RIM, Zf - RIM), (X1 - RIM, Zf - RIM), lambda u, Y, Z: texture_lookup(tex, u, (8 - Y) * 1.5, wrap=True) * np.array([0.7, 0.7, 0.8, 1], np.float32), y_max=8)
    crowns = []
    for (jx, jh) in JETS:
        js = jet_sprite(jh)
        sx, sy, s = v.sprite(js, jx, Z_JETS, anchor=(0.5, 1.0), scale=1.0)
        crowns.append((int(round(sx)), int(round(sy - (jh + 1) * s)), s))
    v.plane((X0, Zn), (X1, Zn), lambda u, Y, Z: texture_lookup(tex, u, (8 - Y) * 1.5, wrap=True), y_max=8)
    for (x, z) in LAMPS:
        if z >= Zn:
            continue
        h = int(round(LAMP_H * v.scale(z)))
        spr, ax, ay = lamp_post(max(24, h))
        sx, sy, _ = v.sprite(spr.a, x, z, anchor=(ax / spr.w, ay / spr.h), scale=z / v.F)
        glows.append([int(round(sx)), int(round(sy - ay + 11)), "fff0c4", 2])
    s = ROOM_TO_BATTLE * v.scale(Z_UMC)
    for dx in (-36, 36):
        glows.append([int(round(umc_at[0] + dx * s)), int(round(umc_at[1] - 50 * s)), "fde9b6", 1])

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    # string lights from the truck lane, strung across the top left (crisp, after the reduce)
    bulbs = string_across(cv, (-10, 22), (196, 54), sag=14, every=9, seed=4)
    bulbs += string_across(cv, (40, 6), (250, 30), sag=10, every=10, seed=5)
    # crisp leaves on the near paving
    for _ in range(140):
        lx, ly = int(rng.integers(0, 640)), int(rng.integers(152, 360))
        c = LEAVES[int(rng.integers(4))]
        dim = 1 - min(0.6, max(0.0, (ly - 156) / 204 * 0.62))
        col = tuple(np.array(C(c)[:3]) * dim)
        cv.px(lx, ly, col); cv.px(lx + 1, ly, tuple(np.array(col) * 0.8))
    solid = v.solid_mask()
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = solid.astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))
    from clouds import cloud_strip
    cloud_strip(640, 44, count=5, seed=8).save(os.path.join(out, "battle-clouds.png"))

    # spray: droplets flicking round each crown in two phases, foam sparkles on the water
    spray = []
    for j in range(2):
        rects = []
        for (cx, cy, sc) in crowns:
            for k in range(4):
                dx = int(rng.integers(2, 6)) * (1 if (k + j) % 2 else -1)
                rects.append([cx + dx, cy + int(rng.integers(0, 6)) + j * 2, 1, 1, "e6f4fc", 0.9])
        spray.append({"kind": "blink", "pattern": "10" if j == 0 else "01", "rate": 5.0, "rects": rects})
    y_near, y_far = int(v.ground_y(Zn + RIM)), int(v.ground_y(Zf - RIM))
    for j in range(3):
        rects = []
        for _ in range(24):
            yy = int(rng.integers(y_far + 1, y_near))
            zz = v.depth_at_y(yy + 0.5)
            half = (X1 - RIM) * v.F / zz
            rects.append([int(320 + rng.uniform(-half + 2, half - 4)), yy, int(rng.integers(2, 4)), 1,
                          "c8e4f4" if rng.random() < 0.6 else "f6dca0", 0.85])
        spray.append({"kind": "blink", "pattern": "".join("1" if k == j else "0" for k in range(3)), "rate": 3.0, "rects": rects})
    res = f"res://assets/art/rooms/{ROOM}/"
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "drift", "depth": "far", "texture": res + "battle-clouds.png", "y": 2, "speed": 2.5},
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "bird", "x": 80, "y": 30, "fly": 10.0, "rate": 4.0},
                {"kind": "bird", "x": 420, "y": 20, "fly": 8.0, "rate": 3.4}]
                + [{"kind": "mk2_goose", "x": 260 - 10 * k, "y": 14 + 4 * abs(k - 2), "fly": 9.0, "rate": 3.0} for k in range(5)]},
            {"kind": "twinkle", "points": glows + bulbs, "rate": 1.6, "min": 0.45},
        ] + spray + [
            {"kind": "particles", "style": "leaf", "count": 12, "rect": [-20, -10, 680, 175], "speed": [30, 14]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
