"""Battle backdrop for the Farrand dorm room (D01): the fight happens in the middle of the room on
move-in day, looking down its length at the west window.

The window fills the far wall: the Flatirons with the sun going down behind the ridge, clouds
drifting past and a bird crossing. The two desks flank it; the beds run back along the side
walls, Jules's bare blue mattress on the left (box and sheets on it, the door and an empty
corkboard on the block wall behind), Jakerson's made bed on the right under his string lights,
SET POINT poster, racket and pennant. The sun lays a long gold patch across the tile toward the
fighters with the window bars printed in it, a box fan stands in the light, the braided rug lies
under the enemy. Layers: drifting clouds and a bird behind the window, a slow sun shaft, dust in
the light, twinkling string lights, the laptop cursor."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, shade, mix, text
from props import OUT
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup, ROOM_TO_BATTLE
from clouds import cloud_strip
import lib_tennis as T
import d01_lib as L

ROOM = "D01"
INK = "#10121e"
Z_BACK = 620.0
WALL_X = 340.0
HALL_H = 250.0
BED_IN = 262.0                 # beds run from the side walls in to |X| = BED_IN
BED_Z = (440.0, 620.0)
BED_TOP = 38.0
HEAD_TOP = 76.0
NEAR_Z = 300.0
FLAT_W, FLAT_H = 352, 130      # the back wall painted at its on-screen size (scale F / Z_BACK)


def in_patch(X, Z):
    """The sun's patch on the floor: thrown from the window toward the fighters, skewed left."""
    off = (600.0 - Z) * 0.42
    left, right = -64.0 - off, 86.0 - off
    inside = (Z > 380) & (Z < 612) & (X > left) & (X < right)
    u = (X - left) / (right - left)
    bars = (np.abs(u - 0.25) < 0.018) | (np.abs(u - 0.75) < 0.018) | (np.abs(Z - 500) < 3)
    return inside, bars


def floor_shader(X, Z):
    """Vinyl tile, mostly one warm beige with a few darker and lighter tiles, faint joints."""
    tile = 34.0
    cx, cz = np.floor(X / tile), np.floor(Z / tile)
    fx, fz = X / tile - cx, Z / tile - cz
    pal = pal_array(L.TILE)
    r = hash2(cx, cz, 3)
    rgb = np.where((r < 0.62)[:, None], pal[4], np.where((r < 0.9)[:, None], pal[4] * 1.03, np.where((r < 0.96)[:, None], pal[3], pal[5])))
    fleck = hash2(np.floor(X / 3), np.floor(Z / 4), 5)
    rgb = rgb * np.where(fleck[:, None] < 0.08, 0.9, 1.0)
    joint = (fx < 0.03) | (fz < 0.03)
    rgb = np.where(joint[:, None], rgb * 0.9, rgb)
    # braided rug under the enemy
    rx, rz = (X - 170) / 128, (Z - 345) / 58
    rr = np.hypot(rx, rz)
    rings = pal_array([L.NAVY[2], L.CREAM[1], L.OLIVE[3], "#8e4a34", L.NAVY[3], L.CREAM[2], L.OLIVE[2], "#a85a3c", L.NAVY[2]])
    k = np.clip((rr * len(rings)).astype(int), 0, len(rings) - 1)
    on_rug = rr < 1
    rgb = np.where(on_rug[:, None], rings[len(rings) - 1 - k] * np.where((hash2(np.floor(np.arctan2(rz, rx) * 30), k, 9) < 0.5)[:, None], 1.0, 0.86), rgb)
    rgb = np.where(((rr >= 1) & (rr < 1.06))[:, None], rgb * 0.6, rgb)
    # the sun patch, stepped, with the bar shadows
    inside, bars = in_patch(X, Z)
    sun = np.array(C("#ffd890")[:3], np.float32)
    lit = rgb * 0.55 + sun * 0.5
    rgb = np.where((inside & ~bars)[:, None], lit, rgb)
    rgb = np.where((inside & bars)[:, None], rgb * 0.92 + sun * 0.06, rgb)
    # warm bounce near the window and the lamp on Jakerson's side
    warm_light(rgb, np.hypot(X - 10, (Z - 600) * 1.4), 160, colour="#f6c27a", strength=0.25)
    warm_light(rgb, np.hypot(X - 210, (Z - 600) * 2.0), 70, colour="#f6cf7a", strength=0.2)
    out = rgba_of(rgb)
    fog(out, Z, "#3a2a2a", 560, 900, amount=0.25)
    return out


def side_wall(side):
    """Left: block wall, the room door near the camera, the empty corkboard, tape marks.
    Right: block wall with the tennis poster, the racket, photos, the pennant and a gig poster."""
    Lw, Hh = int(Z_BACK - NEAR_Z), int(HALL_H)
    cv = Canvas(Lw, Hh, seed=side + 5)
    L.block_wall(cv, 0, 0, Lw, Hh, seed=11 + side, course=10, unit=24)
    L.ceiling_band(cv, 0, Lw, h=10)
    L.cove_base(cv, 0, Hh, Lw)
    if side < 0:
        L.dorm_door(cv, 40, Hh - 104, 54, 104)
        L.light_switch(cv, 104, Hh - 70)
        L.corkboard_welcome(cv, 168, Hh - 150, 46, 38)
        L.wall_scars(cv, [(130, 60, "tape"), (240, 70, "tape"), (280, 110, "nail"), (226, 150, "tack")])
        L.thermostat(cv, 290, Hh - 88)
    else:
        # drawn mirrored so it reads correctly on the right wall (u runs toward the camera there)
        # x is measured from the back corner (Lw - 1 - x is the distance from the camera end)
        L.band_poster(cv, 40, 70, 30, 40)
        L.pennant(cv, 110, 110, label="BOULDER")
        L.photo_strip(cv, Lw - 170, 150)
        L.wall_racket(cv, Lw - 110, 150)
        L.tennis_poster(cv, Lw - 70, 112, 40, 54)
    return cv.a


def back_wall():
    """The far wall at its on-screen size: block, the window with the Flatirons, convector, desks."""
    cv = Canvas(FLAT_W, FLAT_H, seed=21)
    L.block_wall(cv, 0, 0, FLAT_W, FLAT_H, seed=22, course=6, unit=14)
    L.ceiling_band(cv, 0, FLAT_W, h=10)
    L.smoke_detector(cv, FLAT_W // 2, 2)
    L.cove_base(cv, 0, FLAT_H, FLAT_W)
    wx, wy, ww, wh = 102, 22, 148, 70
    sill, sky = L.casement_window(cv, wx, wy, ww, wh, seed=3, with_mask=True)
    L.convector(cv, wx + 4, sill + 9, ww - 8, FLAT_H - sill - 13)
    L.sill_plants(cv, wx + ww - 44, sill + 1)
    cv.rect(wx - 2, sill - 4, 16, 4, "#3a5a8a"); cv.rect(wx, sill - 7, 13, 3, "#c84a3c")
    desks = []
    for kind, cx in (("jules", 68), ("jakerson", FLAT_W - 68)):
        spr, ax, ay = L.desk_hutch(kind, width=48, seed=2 if kind == "jules" else 4)
        cv.paste(spr, cx - ax, FLAT_H - 1 - ay)
        desks.append((cx - ax, FLAT_H - 1 - ay))
    lamp, lx, ly = L.desk_lamp()
    cv.paste(lamp, FLAT_W - 80 - lx, FLAT_H - ly)
    full_sky = np.zeros((FLAT_H, FLAT_W), bool)
    full_sky[wy:wy + wh, wx:wx + ww] = sky
    return cv, full_sky, desks


def bed_top_shader(made):
    def shader(X, Z):
        n = X.shape[0]
        side = np.sign(X)
        inside = (np.abs(X) > BED_IN) & (np.abs(X) < WALL_X - 2) & (Z > BED_Z[0]) & (Z < BED_Z[1] - 2)
        u = (np.abs(X) - BED_IN) / (WALL_X - BED_IN)          # 0 at the inner edge
        v = (Z - BED_Z[0]) / (BED_Z[1] - BED_Z[0])           # 0 at the foot
        if made:
            pal = pal_array(L.NAVY)
            plaid = (np.floor(u * 6) + np.floor(v * 9)) % 2
            rgb = np.where((plaid > 0)[:, None], pal[2], pal[3])
            stripe = (np.abs(u * 6 - np.round(u * 6)) < 0.08) | (np.abs(v * 9 - np.round(v * 9)) < 0.1)
            rgb = np.where(stripe[:, None], pal_array([L.CREAM[1]])[0] * 0.8, rgb)
            rgb = np.where(((v > 0.78) & (v < 0.84))[:, None], pal_array([L.CREAM[3]])[0], rgb)     # sheet fold
            pil = (v > 0.86) & ((u < 0.47) | (u > 0.53))
            rgb = np.where(pil[:, None], pal_array([L.CREAM[2]])[0], rgb)
            rgb = np.where(((v > 0.05) & (v < 0.2))[:, None], pal_array([L.OLIVE[3]])[0], rgb)     # throw
        else:
            pal = pal_array(L.VINYL)
            rgb = np.repeat(pal[3][None, :], n, 0)
            rgb = np.where((np.abs(v * 6 - np.round(v * 6)) < 0.05)[:, None], pal[4], rgb)       # seams
            sheets = (v > 0.66) & (v < 0.86) & (u > 0.12) & (u < 0.5)
            rgb = np.where(sheets[:, None], np.where((np.floor(v * 40) % 2 == 0)[:, None], pal_array([L.CREAM[2]])[0], pal_array(["#9ac0d8"])[0]), rgb)
            pillow = (v > 0.66) & (v < 0.84) & (u > 0.56) & (u < 0.92)
            rgb = np.where(pillow[:, None], pal_array(["#d8e4ec"])[0], rgb)
        edge = (u < 0.04) | (v < 0.02)
        rgb = np.where(edge[:, None], rgb * 1.12, rgb)
        out = rgba_of(np.clip(rgb, 0, 1))
        out[~inside, 3] = 0
        return out
    return shader


def bed_side_shader(made, front=False):
    pal = pal_array(L.NAVY if made else L.VINYL)
    oak = pal_array(L.OAK)

    def shader(u, Y, Z):
        n = u.shape[0]
        rgb = np.repeat(oak[1][None, :], n, 0) * 0.6          # dark gap under the frame
        frame = (Y > 14) & (Y < 22)
        rgb = np.where(frame[:, None], oak[5], rgb)
        rgb = np.where(((Y >= 21) & (Y < 22.5))[:, None], oak[6], rgb)
        mat = Y >= 22
        rgb = np.where(mat[:, None], pal[2], rgb)
        rgb = np.where(((Y > BED_TOP - 3) & mat)[:, None], pal[3], rgb)
        legs = (u < 6) | (u > (90 if front else 176))
        rgb = np.where((legs & (Y < 15))[:, None], oak[3], rgb)
        out = rgba_of(rgb)
        if not front:
            out[..., :3] *= 0.85
        return out
    return shader


def head_shader(u, Y, Z):
    oak = pal_array(L.OAK)
    rgb = np.repeat(oak[3][None, :], u.shape[0], 0)
    rgb = np.where(((np.floor(u / 10) % 2 == 0) & (Y > 46) & (Y < HEAD_TOP - 6))[:, None], oak[2], rgb)
    rgb = np.where((Y > HEAD_TOP - 4)[:, None], oak[5], rgb)
    return rgba_of(rgb * 0.92)


def string_points(v):
    """String lights along the right wall, pinned in swags; returns screen points."""
    pts = []
    zs = np.linspace(330, 616, 160)
    for i, z in enumerate(zs):
        t = (i % 32) / 32
        y = 104 - 10 * 4 * t * (1 - t)
        sx, sy = v.project(WALL_X - 2, y, z)
        pts.append((sx, sy))
    # and on across the back wall's right half
    for x in np.linspace(WALL_X - 4, BED_IN, 40):
        t = (x - BED_IN) / (WALL_X - 4 - BED_IN)
        sx, sy = v.project(x, HEAD_TOP + 14 - 8 * 4 * t * (1 - t), Z_BACK - 4)
        pts.append((sx, sy))
    return pts


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#1a1420")
    v.ground(floor_shader)
    for side in (-1, 1):
        tex = side_wall(side)
        Lw = tex.shape[1]

        def shade_wall(u, Y, Z, tex=tex, side=side, Lw=Lw):
            uu = u if side < 0 else Lw - 1 - u
            o = texture_lookup(tex, uu, HALL_H - Y, wrap=False)
            o[..., :3] *= 0.86 if side < 0 else 0.8
            return o
        v.plane((side * WALL_X, NEAR_Z), (side * WALL_X, Z_BACK), shade_wall, y_max=HALL_H)
    flat, sky, desks = back_wall()
    fx0 = int(round(v.vx - FLAT_W / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - FLAT_H))
    v.strip(flat.a, fy0, fx0)
    # the window's open sky is not solid, so clouds and a bird can pass behind the frames
    sky_big = np.zeros((v.H, v.W), bool)
    ys, xs = np.where(sky)
    sky_big[np.clip(ys + fy0, 0, v.H - 1), np.clip(xs + fx0, 0, v.W - 1)] = True
    v.solid &= ~np.repeat(np.repeat(sky_big, 3, 0), 3, 1)
    # the beds: headboard, inner side, top, foot end (painter's order, far to near)
    for side, made in ((-1, False), (1, True)):
        xin, xw = side * BED_IN, side * (WALL_X - 1)
        v.plane((xw, BED_Z[1] - 2), (xin, BED_Z[1] - 2), head_shader, y_max=HEAD_TOP)
        v.plane((xin, BED_Z[0]), (xin, BED_Z[1]), bed_side_shader(made), y_max=BED_TOP)
        v.ground(bed_top_shader(made), height=BED_TOP)
        v.plane((xw, BED_Z[0]), (xin, BED_Z[0]), bed_side_shader(made, front=True), y_max=BED_TOP)
    # things on the beds and the floor (room-scale sprites)
    for (painter, X, Z, sc) in [(L.box_fan(seed=12), 6, 590, 1.0), (L.box_stack(seed=9), -200, 590, 1.0),
                                (L.mini_fridge(seed=11), 305, 430, 0.9),
                                (L.bean_bag(seed=13), 236, 338, 0.75), (L.duffel_pile(seed=10), -250, 380, 0.85)]:
        s_, ax_, ay_ = painter
        v.sprite(s_.a, X, Z, anchor=(ax_ / s_.w, ay_ / s_.h), scale=ROOM_TO_BATTLE * sc)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp string lights and the laptop cursor at 1:1
    bulbs = []
    pts = string_points(v)
    for i, (sx, sy) in enumerate(pts):
        x, y = int(round(sx)), int(round(sy))
        cv.px(x, y, "#2a2028")
        if i % 6 == 3:
            c = L.GOLD[2] if (i // 6) % 5 else "#f2a0a0"
            cv.px(x, y + 1, c); cv.px(x, y + 2, shade(c, 0.35))
            bulbs.append([x, y + 1, c.lstrip("#"), 1])
    dxk, dyk = desks[1]
    cursor = [fx0 + dxk + 31, fy0 + dyk + 61]
    cv.save(os.path.join(out, "battle-far.png"))
    solid = v.solid_mask()
    near = cv.a.copy()
    near[..., 3] = solid.astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))
    cloud_strip(640, 18, count=4, seed=7, pal=T.CLOUD_GOLD, sizes=(40, 80)).save(os.path.join(out, "battle-clouds.png"))
    win_x = fx0 + 102 + 74
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "drift", "depth": "far", "texture": res + "battle-clouds.png", "y": fy0 + 24, "speed": 2.0, "alpha": 0.9},
            {"kind": "fauna", "depth": "far", "fauna": [{"kind": "bird", "x": 200, "y": fy0 + 44, "fly": 7.0, "rate": 4.0}]},
            {"kind": "beam", "x": win_x + 30, "y": fy0 + 40, "angle": 116, "sweep": 1.5, "period": 11.0, "phase": 0.0,
             "length": 120, "width": 90, "color": "ffd890", "alpha": 0.14, "floor": 140},
            {"kind": "particles", "style": "dust", "count": 22, "rect": [210, 40, 200, 110], "speed": [-2, 3], "color": "fff0c4"},
            {"kind": "twinkle", "points": bulbs, "rate": 1.6, "min": 0.45},
            {"kind": "blink", "pattern": "10", "rate": 1.6, "rects": [[cursor[0], cursor[1], 2, 1, "f6cd78"]]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
