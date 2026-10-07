"""Battle backdrop for the cable walk (F01): standing on the mats, looking straight down the
walkway to the main stage glowing under the Flatirons. Crowd barriers taped in hazard yellow
recede on both sides with the cable bundles at their feet, yellow ramps cross the mats, green
tape arrows mark the one route (an old white call crossed out), festoon poles carry string lights
zigzagging overhead, the lit oak stands on the right and the volunteer tent glows on the left.
The stage sweeps searchlights through the sky; a marshal's beacon blinks on the nearest cone."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from midlib import sprite_from_cell
from pixel import Canvas, C
from sky import flatirons_panel
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
import lib_farrand as F

ROOM = "F01"
INK = "#10121e"
HAZE = "#3a2c48"
HALF = 64.0              # half width of the mat walkway
BARRIER_X = 118.0
POLES = [(-178, 400), (178, 520), (-178, 700), (178, 900), (-178, 1150), (178, 1450), (-178, 1800)]
POLE_H = 94.0            # festoon pole height in world units (55 room px x 1.7)
RAMPS = [470.0, 980.0, 1560.0]
Z_STAGE = 2600.0
ARROWS = [(-32, 340), (32, 560), (-32, 780), (32, 1060)]


def ground_shader(X, Z):
    ax = np.abs(X)
    rgb = F.battle_grass_rgb(X, Z)
    mats = ax < HALF
    rgb[mats] = F.battle_mats_rgb(X[mats], Z[mats], HALF)
    # mats sit proud of the grass: a dark lip along both edges
    rgb[(ax >= HALF) & (ax < HALF + 2.5)] = pal_array(F.MAT)[0]
    # cable bundles along the barrier feet
    for side in (-1, 1):
        d = np.abs(X - side * (BARRIER_X - 9))
        for k, off in enumerate((-2.5, 0.0, 2.5)):
            line = np.abs(X - side * (BARRIER_X - 9) - off - 1.2 * np.sin(Z / (40 + 9 * k))) < 0.9
            rgb[line] = pal_array(["#1e1c24", "#2a2832", "#4a2424"])[k]
    # cable ramps across the walkway: black bevels, yellow lid
    for zr in RAMPS:
        dz = np.abs(Z - zr)
        ramp = (dz < 8) & (ax < HALF + 14)
        rgb[ramp] = pal_array(F.HAZARD)[1]
        rgb[ramp & (dz < 3)] = pal_array(F.HAZARD)[3]
        rgb[ramp & (dz < 3) & (np.mod(X, 16) < 1.5)] = pal_array(F.HAZARD)[2]
        rgb[ramp & (Z < zr - 6)] = pal_array(F.HAZARD)[0]
    # green tape arrows pointing down the route; one white call taped over with a red X
    for (axx, az) in ARROWS:
        shaft = (np.abs(X - axx) < 3.5) & (Z > az) & (Z < az + 26)
        head = (Z >= az + 26) & (Z < az + 42) & (np.abs(X - axx) < (az + 42 - Z) * 0.55)
        rgb[shaft | head] = pal_array(F.GREEN_TAPE)[1]
        rgb[(shaft | head) & (X < axx)] = pal_array(F.GREEN_TAPE)[2]
    wx, wz = 30.0, 1280.0
    white = ((np.abs(X - wx) < 3.5) & (Z > wz) & (Z < wz + 26)) | ((Z >= wz + 26) & (Z < wz + 42) & (np.abs(X - wx) < (wz + 42 - Z) * 0.55))
    rgb[white] = pal_array(["#c8c8d0"])[0]
    cross = ((np.abs((X - wx) - (Z - wz - 20) * 0.5) < 1.6) | (np.abs((X - wx) + (Z - wz - 20) * 0.5) < 1.6)) & (np.abs(Z - wz - 20) < 20)
    rgb[cross] = pal_array(["#d8483c"])[0]
    # a puddle on the grass reflecting the sky, another on the mats
    for (px_, pz, rx, rz) in [(-250, 430, 40, 26), (22, 640, 22, 14), (230, 760, 46, 24)]:
        d = np.hypot((X - px_) / rx, (Z - pz) / rz) + 0.25 * (hash2(np.floor(X / 6), np.floor(Z / 6), 9) - 0.5)
        water = d < 1
        rgb[water] = pal_array(["#5a4a78"])[0]
        rgb[water & (Z < pz - rz * 0.3)] = pal_array(["#8a5a84"])[0]
        rgb[water & (np.abs(X - px_) < rx * 0.15)] = pal_array(["#c88a6a"])[0]
    # lamp light under the poles, the bulbs' glow along the walk, the stage spill far away
    for (lx, lz) in POLES:
        warm_light(rgb, np.hypot((X - lx * 0.8) * 1.0, (Z - lz) * 0.5), 120, strength=0.42)
    warm_light(rgb, np.hypot(X * 0.5, (Z - Z_STAGE) * 0.25), 220, colour="#e8a0c0", strength=0.5)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 1300, 3600, amount=0.85)
    return out


def barrier_shader(tex, height):
    def shade_(u, Y, Z):
        o = texture_lookup(tex, u, height - Y, wrap=True)
        return fog(o, Z, HAZE, 1300, 3600, amount=0.85)
    return shade_


def stage_flat():
    """The main stage at its on-screen size at Z_STAGE, with the lamp points on its truss."""
    w, h = 140, 56
    cv = Canvas(w + 70, h + 50)
    cx, base = (w + 70) // 2, h + 46
    pts = F.distant_stage(cv, cx, base, w=w, h=h, seed=8)
    return cv, pts, cx, base


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    v = View(horizon=98, cam=52, fill="#1b1830")
    # Sky: the Flatirons tiled across (mirrored either side of the centre panel) over the stage.
    pw = flatirons_panel(scale=1.9).shape[1]
    sky, _ = F.farrand_sky(640, 132, panels=(1, 0, 1), offset=pw - (320 - pw // 2), scale=1.9, stars=36, seed=4)
    v.strip(sky, 0, solid=False)
    v.strip(F.field_treeline(640, 34, seed=3, open_span=(262, 378)), 98 - 34 + 6)
    v.ground(ground_shader)

    # Far to near: light towers, the stage, field trees, the tent, the oak, barrier runs, poles, cones.
    st, stage_pts, scx, sbase = stage_flat()
    sx0 = int(round(v.vx - scx))
    sy0 = int(round(v.ground_y(Z_STAGE) - sbase))
    for tx in (-560, 560):
        tz = 2300
        th = int(round(250 * v.scale(tz)))
        tw = Canvas(16, th + 8)
        F.light_tower(tw, 4, th + 6, th, seed=int(tx > 0))
        v.sprite(tw.a, tx, tz, scale=tz / v.F)
    v.strip(st.a, sy0, sx0)
    for (x, z, cell, hw) in [(-760, 2100, 5, 360), (-1100, 1900, 6, 400), (820, 2000, 6, 380), (1150, 2200, 5, 360)]:
        h = int(round(hw * v.scale(z)))
        spr = sprite_from_cell(cell, height=h, colors=28, brightness=0.55, saturation=0.75)
        v.sprite(spr, x, z, scale=z / v.F)
    tent, tax, tay = F.peaked_tent(196, 72, 40, open_front=False, seed=4, valance_text="VOLUNTEERS",
                                   poles=[0, 64, 129, 193])
    tent_z = 1400.0
    v.sprite(tent.a, -560, tent_z, anchor=(tax / tent.w, tay / tent.h), scale=ROOM_TO_BATTLE)
    from props import atlas_tree
    oak_z = 560.0
    oak_h = int(round(118 * ROOM_TO_BATTLE * v.scale(oak_z)))
    oak, oax, oay = atlas_tree(oak_h, cell=5, seed=2)
    oak_bulbs = []
    for (y0, y1, sag) in [(int(oak_h * 0.3), int(oak_h * 0.26), 16), (int(oak_h * 0.5), int(oak_h * 0.54), 14)]:
        oak_bulbs += F.festoon(oak, 18, y0, oak.w - 18, y1, sag=sag, every=9, seed=y0)
    oak_at = v.sprite(oak.a, 430, oak_z, anchor=(oax / oak.w, oay / oak.h), scale=oak_z / v.F)

    for side in (-1, 1):
        L = 1900
        tex = F.barrier_texture(L, 44, seed=side + 2)
        v.plane((side * BARRIER_X, 330.0), (side * BARRIER_X, 330.0 + L), barrier_shader(tex, 44), y_max=44)

    pole_tops = []
    for (x, z) in sorted(POLES, key=lambda p: -p[1]):
        h = int(round(POLE_H * v.scale(z)))
        pole, pax, pay, bulb = F.festoon_pole(max(16, h), arm=max(4, h // 6), seed=z, flip=x > 0)
        sx, sy, _ = v.sprite(pole.a, x, z, anchor=(pax / pole.w, pay / pole.h), scale=z / v.F)
        pole_tops.append(((x, z), (sx, sy - h + 2), (sx - pax + bulb[0], sy - pay + bulb[1])))
    cones = [(-HALF - 10, 380), (HALF + 10, 450), (-HALF - 10, 620), (HALF + 10, 760), (-HALF - 10, 1000), (HALF + 10, 1300)]
    for (x, z) in sorted(cones, key=lambda p: -p[1]):
        h = max(5, int(round(24 * v.scale(z))))
        v.sprite(F.cone_sprite(h), x, z, anchor=(0.5, (h + 1) / (h + 3)), scale=z / v.F)

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # Crisp string lights: zigzag between pole tops, nearest last.
    twinkles = []
    tops = sorted(pole_tops, key=lambda p: -p[0][1])
    for i in range(len(tops) - 1):
        a, b = tops[i][1], tops[i + 1][1]
        depth = (tops[i][0][1] + tops[i + 1][0][1]) / 2
        twinkles += F.string_across(cv, b, a, sag=max(3, int(26 * v.scale(depth))), every=max(5, int(13 * v.scale(depth))), seed=i)
    # the nearest span runs off the left edge to a pole behind the camera
    near_top = [t for t in pole_tops if t[0][1] == 400][0][1]
    twinkles += F.string_across(cv, (-12, 30), near_top, sag=14, every=12, seed=21)
    twinkles += F.string_across(cv, near_top, (652, 18), sag=30, every=13, seed=22)
    lamp_glows = [[int(round(t[2][0])), int(round(t[2][1])), "fff0c4", 2 if t[0][1] < 800 else 1] for t in pole_tops]
    # oak bulbs to screen
    s_oak = oak_z / v.F * v.scale(oak_z)
    ox0 = oak_at[0] - oax * s_oak
    oy0 = oak_at[1] - oay * s_oak
    oak_pts = [[int(round(ox0 + p[0] * s_oak)), int(round(oy0 + p[1] * s_oak)), p[2], 1] for p in oak_bulbs]
    stage_lamps = [[sx0 + p[0], sy0 + p[1], "f6dca0", 1] for p in stage_pts]

    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = v.solid_mask().astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))

    res = f"res://assets/art/rooms/{ROOM}/"
    beam_y = sy0 + sbase - 56 + 2
    nearest_cone = v.project(-HALF - 10, 24, 380)
    beacon = [int(round(nearest_cone[0])) - 1, int(round(nearest_cone[1])) - 3]
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "beam", "depth": "far", "x": 300, "y": beam_y, "angle": -104, "sweep": 16, "period": 8.0, "phase": 0.0,
             "length": 110, "width": 22, "color": "c8b0ff", "alpha": 0.2, "floor": -400},
            {"kind": "beam", "depth": "far", "x": 340, "y": beam_y, "angle": -76, "sweep": 16, "period": 9.5, "phase": 2.0,
             "length": 110, "width": 22, "color": "ffc8e0", "alpha": 0.2, "floor": -400},
            {"kind": "beam", "depth": "far", "x": 320, "y": beam_y, "angle": -90, "sweep": 28, "period": 6.5, "phase": 4.0,
             "length": 100, "width": 16, "color": "fff0c4", "alpha": 0.14, "floor": -400},
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "bat", "x": 80, "y": 34, "fly": 16.0, "rate": 7.0},
                {"kind": "bat", "x": 420, "y": 22, "fly": 12.0, "rate": 6.0}]},
            {"kind": "twinkle", "points": twinkles + oak_pts, "rate": 2.0, "min": 0.35},
            {"kind": "twinkle", "points": lamp_glows + stage_lamps, "rate": 1.3, "min": 0.55},
            {"kind": "blink", "pattern": "1100000000", "rate": 5.0,
             "rects": [[beacon[0], beacon[1], 3, 2, "ffb030"], [beacon[0] - 2, beacon[1] - 2, 7, 6, "ffb030", 0.3]]},
            {"kind": "particles", "style": "dust", "count": 10, "rect": [int(lamp_glows[-1][0]) - 30, int(lamp_glows[-1][1]) - 10, 60, 50],
             "speed": [0, 6], "color": "f6e0b0"},
            {"kind": "particles", "style": "leaf", "count": 8, "rect": [400, 20, 260, 150], "speed": [-18, 12]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
