"""Battle backdrop for the food court (F03): standing on the straw between two rows of food trucks
and stalls, looking down the lane to the main stage. TACOS and CURRY have their hatches lit under
striped awnings, the COCOA stall glows, NOODLES and the TOKENS kiosk are shuttered for the night.
String lights zigzag from roof to roof overhead and radiate from the timber mast in the barrel
planter; picnic tables stand on the straw, Mags' soup cart waits by the bins. Steam curls off the
taco hatch, a raccoon works the bins, the stage sweeps its beams through the dusk."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from midlib import sprite_from_cell
from pixel import Canvas, C, shade
from sky import flatirons_panel
from props import OUT
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
import lib_farrand as F

ROOM = "F03"
INK = "#10121e"
HAZE = "#3a2c48"
LANE = 205.0             # truck sides stand at X = +-LANE
STRAW_HALF = 140.0
Z_STAGE = 2700.0
MAST = (-80.0, 1120.0)
MAST_H = 150 * ROOM_TO_BATTLE


def lane_shader(X, Z):
    ax = np.abs(X)
    rgb = F.battle_grass_rgb(X, Z, stripe=100.0, seed=3)
    # straw down the middle of the lane, ragged at the edge
    edge = STRAW_HALF + 22 * (hash2(np.floor(Z / 40), 0, 2) - 0.5) + 10 * np.sin(Z / 70.0)
    straw = (ax < edge) & (Z > 250) & (Z < 1900)
    sp = pal_array(F.STRAW_BED)
    n = hash2(np.floor(X / 14), np.floor(Z / 10), 5)
    srgb = np.where((n < 0.5)[:, None], sp[2], sp[3] * 0.92 + sp[2] * 0.08)
    s1 = hash2(np.floor((X + 0.8 * Z) / 2.2), np.floor(Z / 6), 6)
    s2 = hash2(np.floor((X - 0.8 * Z) / 2.2), np.floor(Z / 6), 7)
    s3 = hash2(np.floor(X / 5), np.floor(Z / 1.6), 8)
    srgb = np.where((s1 > 0.8)[:, None], sp[4], srgb)
    srgb = np.where((s2 > 0.86)[:, None], sp[5], srgb)
    srgb = np.where((s3 > 0.93)[:, None], sp[1], srgb)
    rgb[straw] = srgb[straw]
    # wisps of straw thinning out into the grass
    wisp = (ax >= edge) & (ax < edge + 26) & (hash2(np.floor(X / 3), np.floor(Z / 2), 7) > 0.8) & (Z > 250) & (Z < 1900)
    rgb[wisp] = sp[3]
    # mat pads under the open hatches (left TACOS, left CURRY) and the cable bundles along the trucks
    for (side, z0, z1) in [(-1, 460, 600), (-1, 1110, 1250)]:
        pad = (X * side > LANE - 70) & (X * side < LANE - 8) & (Z > z0) & (Z < z1)
        mrgb = F.battle_mats_rgb(X[pad] - side * 200, Z[pad], 40.0, 30.0, seed=2)
        rgb[pad] = mrgb
    for side in (-1, 1):
        for k, off in enumerate((-2.0, 1.0)):
            line = np.abs(X - side * (LANE - 14) - off - 1.4 * np.sin(Z / (36 + 11 * k))) < 0.9
            rgb[line & (Z > 300)] = pal_array(["#1e1c24", "#4a2424"])[k]
    # shadows under the trucks
    under = (ax > LANE - 6) & (ax < LANE + 60)
    rgb[under] = rgb[under] * 0.55
    # puddles
    for (px_, pz, rx, rz) in [(120, 520, 30, 18), (-40, 900, 22, 12)]:
        d = np.hypot((X - px_) / rx, (Z - pz) / rz) + 0.25 * (hash2(np.floor(X / 6), np.floor(Z / 6), 9) - 0.5)
        water = d < 1
        rgb[water] = pal_array(["#5a4a78"])[0]
        rgb[water & (Z < pz - rz * 0.3)] = pal_array(["#8a5a84"])[0]
        rgb[water & (np.abs(X - px_) < rx * 0.2)] = pal_array(["#d89a6a"])[0]
    # light: hatches spill warm light onto the lane, the strings glow down the middle, the stage
    for (lx, lz, r, s) in [(-170, 520, 150, 0.5), (-170, 900, 130, 0.42), (-170, 1180, 120, 0.45), (0, 700, 200, 0.22),
                           (0, 1100, 180, 0.2), (MAST[0], MAST[1], 120, 0.25)]:
        warm_light(rgb, np.hypot((X - lx) * 0.9, (Z - lz) * 0.55), r, strength=s)
    warm_light(rgb, np.hypot(X * 0.45, (Z - Z_STAGE) * 0.25), 240, colour="#e8a0c0", strength=0.5)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 1300, 3600, amount=0.85)
    return out


def side_shader(tex):
    """Map a room-scale side-view sprite onto a wall plane (1 texel = ROOM_TO_BATTLE world units)."""
    h = tex.shape[0]
    base = h - 3

    def shade_(u, Y, Z):
        o = texture_lookup(tex, u / ROOM_TO_BATTLE, base - Y / ROOM_TO_BATTLE, wrap=False)
        return fog(o, Z, HAZE, 1300, 3600, amount=0.8)
    return shade_


def solid(cv):
    """Drop the soft ground shadow (it would stand up on a wall plane)."""
    a = cv.a.copy()
    a[a[..., 3] < 0.6, 3] = 0
    return a


def stage_flat():
    w, h = 140, 56
    cv = Canvas(w + 70, h + 50)
    cx, base = (w + 70) // 2, h + 46
    pts = F.distant_stage(cv, cx, base, w=w, h=h, seed=15)
    return cv, pts, cx, base


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    v = View(horizon=98, cam=52, fill="#1b1830")
    pw = flatirons_panel(scale=1.9).shape[1]
    sky, _ = F.farrand_sky(640, 132, panels=(0, 1, 0), offset=pw - (320 - pw // 2), scale=1.9, stars=34, seed=13)
    v.strip(sky, 0, solid=False)
    v.strip(F.field_treeline(640, 34, seed=7, open_span=(266, 374)), 98 - 34 + 6)
    v.ground(lane_shader)

    # far to near: light towers, the stage, field trees
    st, stage_pts, scx, sbase = stage_flat()
    sx0 = int(round(v.vx - scx))
    sy0 = int(round(v.ground_y(Z_STAGE) - sbase))
    for tx in (-540, 540):
        tz = 2400
        th = int(round(250 * v.scale(tz)))
        tw = Canvas(16, th + 8)
        F.light_tower(tw, 4, th + 6, th, seed=int(tx > 0) + 3)
        v.sprite(tw.a, tx, tz, scale=tz / v.F)
    v.strip(st.a, sy0, sx0)
    for (x, z, cell, hw) in [(-820, 2200, 6, 380), (-1150, 2000, 5, 360), (880, 2100, 5, 360), (1200, 2300, 6, 400)]:
        h = int(round(hw * v.scale(z)))
        spr = sprite_from_cell(cell, height=h, colors=28, brightness=0.55, saturation=0.75)
        v.sprite(spr, x, z, scale=z / v.F)

    # the two rows, as side-on planes (far ones first)
    bulbs_world = []   # (X, Y, Z, hex) of awning bulbs to place as twinkles
    roofs = {}         # roof corner points for the strings: name -> (X, Y, Z)

    def place_side(side, z0, sprite, info_bulbs, name, roof_h, end=None):
        tex = solid(sprite)
        L = tex.shape[1] * ROOM_TO_BATTLE
        if end is not None:
            etex = end.a
            D = etex.shape[1] * ROOM_TO_BATTLE
            ebase = etex.shape[0] - 3
            xa = -LANE - D if side < 0 else LANE
            def eshade(X, Y, etex=etex, xa=xa, ebase=ebase, z0=z0):
                o = texture_lookup(etex, (X - xa) / ROOM_TO_BATTLE, ebase - Y / ROOM_TO_BATTLE, wrap=False)
                return fog(o, np.full(X.shape, z0), HAZE, 1300, 3600, amount=0.8)
            v.back(z0 + 4, eshade, region=lambda X, Y, xa=xa, D=D: (X >= xa) & (X < xa + D) & (Y >= 0))
        if side < 0:
            A, B = (-LANE, z0), (-LANE, z0 + L)
        else:
            A, B = (LANE, z0 + L), (LANE, z0)
        v.plane(A, B, side_shader(tex), y_max=tex.shape[0] * ROOM_TO_BATTLE)
        base = tex.shape[0] - 3
        for p in info_bulbs:
            u = p[0] * ROOM_TO_BATTLE
            z = (z0 + u) if side < 0 else (z0 + L - u)
            bulbs_world.append((side * LANE, (base - p[1]) * ROOM_TO_BATTLE, z, p[2]))
        roofs[name] = [(side * LANE, roof_h * ROOM_TO_BATTLE, z0 + 20), (side * LANE, roof_h * ROOM_TO_BATTLE, z0 + L - 20)]
        return z0 + L

    # left: TACOS (open), COCOA (stall), CURRY (open)
    left = []
    t1, _, _, i1 = F.food_truck(180, 80, pal=F.TRUCK_TEAL, name="TACOS", seed=11, facing=1)
    s1, _, _, b1 = F.market_stall(118, 88, canopy=F.RED, name="COCOA", seed=13)
    t3, _, _, i3 = F.food_truck(170, 78, pal=F.TRUCK_MUSTARD, name="CURRY", seed=14, facing=1, trim=["#2c4a4c", "#e6d6b1"])
    # right: NOODLES (closed), TOKENS kiosk (closed), WAFFLES (open)
    t2, _, _, i2 = F.food_truck(168, 78, pal=F.TRUCK_PINK, name="NOODLES", open_=False, seed=12, facing=-1, trim=["#2c4a4c", "#e6d6b1"])
    k1, _, _, kb = F.kiosk(60, 66, name="TOKENS", seed=3)
    t4, _, _, i4 = F.food_truck(176, 80, pal=F.TRUCK_CREAM, name="WAFFLES", seed=16, facing=-1)
    # far to near on each side
    place_side(-1, 1060, t3, i3["bulbs"], "curry", 80, F.end_face("truck", F.TRUCK_MUSTARD, 78, trim=["#2c4a4c", "#e6d6b1"]))
    place_side(-1, 790, s1, b1, "cocoa", 86, F.end_face("stall", None, 88, depth=52))
    place_side(-1, 380, t1, i1["bulbs"], "tacos", 82, F.end_face("truck", F.TRUCK_TEAL, 80))
    place_side(1, 990, t4, i4["bulbs"], "waffles", 82, F.end_face("truck", F.TRUCK_CREAM, 80))
    place_side(1, 830, k1, kb, "tokens", 66, F.end_face("kiosk", F.TRUCK_MUSTARD, 66, depth=40))
    place_side(1, 420, t2, [], "noodles", 80, F.end_face("truck", F.TRUCK_PINK, 78, trim=["#2c4a4c", "#e6d6b1"]))

    # on the straw: the mast in its barrel, picnic tables, Mags' cart by the bins
    items = []
    for (x, z) in [(40, 1400), (70, 980), (30, 700)]:
        items.append((z, "picnic", x))
    items.append((MAST[1], "mast", MAST[0]))
    items.append((640.0, "cart", -128.0))
    items.append((900.0, "bins", 165.0))
    items.append((1300.0, "washup", -120.0))
    mast_top = None
    for z, kind, x in sorted(items, key=lambda t: -t[0]):
        s = v.scale(z)
        if kind == "picnic":
            spr, ax, ay = F.picnic_table(140, 30, seed=int(z))
            v.sprite(spr.a, x, z, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE)
        elif kind == "mast":
            spr, ax, ay, crown = F.half_barrel_planter(70, 44, seed=22, mast=150)
            sx, sy, sc = v.sprite(spr.a, x, z, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE)
            mast_top = (sx + (crown[0] - ax) * sc, sy + (crown[1] - ay) * sc)
        elif kind == "cart":
            spr, ax, ay = F.soup_cart(86, 45, seed=23)
            v.sprite(spr.a, x, z, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE)
        elif kind == "bins":
            cv_ = Canvas(64, 30)
            F.wheelie_bins(cv_, 2, 28)
            v.sprite(cv_.a, x, z, anchor=(0.5, 28 / 30), scale=ROOM_TO_BATTLE)
        elif kind == "washup":
            spr, ax, ay = F.trestle_table(150, 30, seed=20)
            v.sprite(spr.a, x, z, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE)

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp strings: zigzag roof to roof across the lane, and radiating from the mast
    twinkles = []
    zig = [roofs["tacos"][0], roofs["noodles"][1], roofs["tacos"][1], roofs["noodles"][0], roofs["cocoa"][0],
           roofs["tokens"][1], roofs["cocoa"][1], roofs["waffles"][1], roofs["curry"][0], roofs["waffles"][0], roofs["curry"][1]]
    for i in range(len(zig) - 1, 0, -1):
        a, b = zig[i - 1], zig[i]
        pa, pb = v.project(*a), v.project(*b)
        depth = (a[2] + b[2]) / 2
        twinkles += F.string_across(cv, pb, pa, sag=max(3, int(30 * v.scale(depth))), every=max(7, int(18 * v.scale(depth))), seed=i)
    if mast_top:
        for name, end in [("cocoa", 0), ("tokens", 1)]:
            p = v.project(*roofs[name][end])
            twinkles += F.string_across(cv, mast_top, p, sag=8, every=10, seed=len(twinkles))
    # awning bulbs on the truck sides
    awning = []
    for (X, Y, Z, hx) in bulbs_world:
        sx, sy = v.project(X, Y, Z)
        awning.append([int(round(sx)), int(round(sy)), hx, 1])
    # the nearest string runs in from behind the camera
    tz = v.project(*roofs["tacos"][0])
    twinkles += F.string_across(cv, (-10, 16), tz, sag=18, every=12, seed=77)
    twinkles += F.string_across(cv, tz, (650, 10), sag=34, every=13, seed=78)
    stage_lamps = [[sx0 + p[0], sy0 + p[1], "f6dca0", 1] for p in stage_pts]

    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = v.solid_mask().astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))

    res = f"res://assets/art/rooms/{ROOM}/"
    beam_y = sy0 + sbase - 56 + 2
    hatch = v.project(-LANE + 6, 50 * ROOM_TO_BATTLE, 380 + 110 * ROOM_TO_BATTLE)
    bins_xy = v.project(165, 0, 900)
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "beam", "depth": "far", "x": 300, "y": beam_y, "angle": -102, "sweep": 16, "period": 8.5, "phase": 1.0,
             "length": 110, "width": 22, "color": "c8b0ff", "alpha": 0.2, "floor": -400},
            {"kind": "beam", "depth": "far", "x": 340, "y": beam_y, "angle": -78, "sweep": 16, "period": 10.0, "phase": 3.0,
             "length": 110, "width": 22, "color": "ffc8e0", "alpha": 0.2, "floor": -400},
            {"kind": "fauna", "depth": "far", "fauna": [{"kind": "bat", "x": 140, "y": 30, "fly": 14.0, "rate": 7.0}]},
            {"kind": "fauna", "fauna": [{"kind": "raccoon", "x": int(bins_xy[0]) - 24, "y": int(bins_xy[1]) + 1, "range": 8, "speed": 0.25, "rate": 3.0}]},
            {"kind": "twinkle", "points": twinkles, "rate": 2.0, "min": 0.35},
            {"kind": "twinkle", "points": awning + stage_lamps, "rate": 1.3, "min": 0.55},
            {"kind": "particles", "style": "dust", "count": 8, "rect": [int(hatch[0]) - 10, int(hatch[1]) - 40, 50, 40],
             "speed": [3, -8], "color": "e8e4dc"},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
