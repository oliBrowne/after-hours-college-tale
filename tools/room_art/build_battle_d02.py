"""Battle backdrop for the Farrand second-floor hallway (D02): the fight happens where the hall
widens at the study lounge, looking straight across at the hall's far wall and down the long
corridor that runs off through a cased opening in it.

The far wall is painted at room scale (Z_BACK is the depth where a room-scale person is 52 px):
door 212 with its name tags, the RA's WELCOME HOME board, the drinking fountain, the 1949 class
photo and the RA's own door 210 under its fairy lights. Through the opening the corridor recedes
to a window with the moon in it: birch doors in teal frames down both sides, one standing open
on a lamp-lit room, frosted drum lights along the acoustic ceiling, oxblood border lines on the
speckled lino converging on the vanishing point. Floormates' things stand along the wall.
Layers: corridor lights breathing (one flickers), a TV flickering in the open room, the RA door's
fairy lights, a moth under the nearest corridor light, dust in the light."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_eng import painted_block, exit_sign, outlet
from lib_umc import soft_ellipse, extinguisher
from lib_oldmain import framed_photo
from facade import brick_wall
import d02_lib as L

ROOM = "D02"
INK = "#10121e"
F = 320.0
Z_BACK = 443.0                 # depth where room-scale paintings are 1:1 (72 battle px -> 52 px)
SB = F / Z_BACK
SC = 72 / 52                   # room-scale sprite -> battle world scale
WALL_X = 360.0                 # the near side walls (the lounge end of the hall)
NEAR_Z = 300.0
FW, FH = 520, 150              # the far wall flat, at its on-screen size
BASE_F = FH                    # floor line row in the flat
OPEN_HW, OPEN_H = 30, 84       # the corridor opening in the flat (half width, height)
CX = OPEN_HW / SB              # corridor half width in world units
CH = OPEN_H / SB               # corridor ceiling height in world units
Z_END = 1800.0
CORR_LIGHTS = (560.0, 800.0, 1040.0, 1280.0, 1520.0)
OPEN_DOOR = (300.0, 352.0)     # u range of the open door on the right corridor wall
TILE = 22.0


def floor_shader(X, Z):
    """Speckled asphalt tile in a quiet two-tone checker, oxblood borders along every wall, warm
    pools under the lights, the open room's glow spilling across the corridor."""
    cx, cz = np.floor(X / TILE), np.floor(Z / TILE)
    fx, fz = X / TILE - cx, Z / TILE - cz
    f, g, ox = pal_array(L.LINO_F), pal_array(L.LINO_G), pal_array(L.LINO_OX)
    r = hash2(cx, cz, 3)
    k = np.where(r < 0.94, 2, np.where(r < 0.97, 1, 3))
    rgb = np.where((((cx + cz) % 2) == 0)[:, None], f[k], g[k])
    in_corr = Z > Z_BACK - 2
    border = np.where(in_corr, np.abs(X) > CX - 9, (np.abs(X) > WALL_X - 26) | ((Z > Z_BACK - 26) & (np.abs(X) > CX - 9)))
    rgb = np.where(border[:, None], ox[2], rgb)
    inlay = np.where(in_corr, np.abs(np.abs(X) - (CX - 10)) < 0.9,
                     (np.abs(np.abs(X) - (WALL_X - 27)) < 1.2) | ((np.abs(Z - (Z_BACK - 27)) < 1.2) & (np.abs(X) > CX - 9)))
    rgb = np.where(inlay[:, None], pal_array(["#c8b49a"])[0], rgb)
    # tile edges, marbling streaks, chips
    rgb = np.where(((fx < 0.05) | (fz < 0.05))[:, None], rgb * 0.88, rgb)
    streak = (np.abs(fz - 0.3 - 0.25 * fx) < 0.04) & (hash2(cx, cz, 9) < 0.5)
    rgb = np.where(streak[:, None], rgb * 1.08, rgb)
    chip = hash2(np.floor(X / 2.5), np.floor(Z / 3.0), 5)
    rgb = np.where((chip < 0.05)[:, None], rgb * 0.86, np.where((chip > 0.97)[:, None], rgb * 1.1, rgb))
    # cart scuffs across the middle
    sc = hash2(np.floor(X / 30), np.floor(Z / 6), 13)
    rgb = np.where(((sc > 0.985) & (np.abs(X) < 300))[:, None], rgb * 0.8, rgb)
    # light: the near lounge lights, the corridor drums, the far wall's wash
    warm_light(rgb, np.hypot(X + 170, (Z - 360) * 2.0), 150, colour="#f6cf7a", strength=0.28)
    warm_light(rgb, np.hypot(X - 190, (Z - 380) * 2.0), 140, colour="#f6cf7a", strength=0.26)
    warm_light(rgb, np.hypot(X, (Z - Z_BACK) * 3.0), 300, colour="#f6c27a", strength=0.16)
    for zl in CORR_LIGHTS:
        warm_light(rgb, np.hypot(X * 1.6, Z - zl), 70, colour="#f6cf7a", strength=0.3)
    spill = in_corr & (X > 0) & (Z > OPEN_DOOR[0] + Z_BACK - 4) & (Z < OPEN_DOOR[1] + Z_BACK + 30 - X * 0.6)
    rgb = np.where(spill[:, None], rgb * 0.6 + pal_array(["#f6c27a"])[0] * 0.42, rgb)
    out = rgba_of(np.clip(rgb, 0, 1))
    fog(out, Z, "#2a2230", 900, 1900, amount=0.55)
    return out


def corridor_wall(side):
    """One side of the corridor in world units (u along its length, v down from the ceiling):
    cream block over a brick wainscot, birch doors in teal frames with paper name tags."""
    Lw, Hh = int(Z_END - Z_BACK), int(round(CH))
    cv = Canvas(Lw, Hh, seed=40 + side)
    painted_block(cv, 0, 0, Lw, Hh, seed=41 + side, pal=L.FH_BLOCK, course=10, length=22)
    rail = Hh - 60
    cv.rect(0, rail, Lw, 6, L.FH_SAND[3]); cv.hline(0, rail, Lw, L.FH_SAND[5]); cv.hline(0, rail + 5, Lw, L.FH_SAND[1])
    brick_wall(cv, 0, rail + 6, Lw, Hh - rail - 10, pal=L.FH_BRICK, seed=43 + side)
    cv.rect(0, Hh - 4, Lw, 4, "#2a2226")
    rng = np.random.default_rng(44 + side)
    start = 60 if side < 0 else 150
    for k, u in enumerate(range(start, Lw - 60, 210)):
        dw, dh = 50, 98
        top = Hh - 4 - dh
        cv.rect(u - 4, top - 4, dw + 8, dh + 4, L.STEEL_T[3]); cv.rect(u - 4, top - 4, dw + 8, 2, L.STEEL_T[5])
        if side > 0 and OPEN_DOOR[0] <= u <= OPEN_DOOR[1]:
            # standing open: the lamp-lit room inside
            cv.rect(u, top, dw, dh, "#b07c50"); cv.rect(u, top + dh - 20, dw, 20, "#6a4630")
            cv.rect(u + 10, top + 20, 22, 26, "#1e2240"); cv.rect(u + 14, top + 26, 12, 10, "#e9a84a")
            cv.rect(u, top, 8, dh, L.BIRCH[3])
            continue
        cv.rect(u, top, dw, dh, L.BIRCH[3])
        for gx in range(u + 3, u + dw - 2, 6):
            cv.vline(gx, top + 2, dh - 4, L.BIRCH[4] if (gx // 6) % 2 else L.BIRCH[2])
        cv.rect(u, top + dh - 12, dw, 10, L.CHROME[2])                   # kick plate
        cv.rect(u + dw - 10, top + 48, 7, 4, L.CHROME[4])                # lever
        for t in range(int(rng.integers(1, 3))):                         # paper name tags
            c = L.CPAPER[int(rng.integers(0, 6))]
            cv.rect(u + 8 + t * 4, top + 22 + t * 16, 30, 12, OUT); cv.rect(u + 9 + t * 4, top + 23 + t * 16, 28, 10, c)
            cv.rect(u + 13 + t * 4, top + 27 + t * 16, 18, 2, "#2a2030")
        cv.rect(u + dw + 10, top + 26, 14, 8, OUT); cv.rect(u + dw + 11, top + 27, 12, 6, "#e8e2d0")   # number plate
    return cv.a


def ceiling_shader(X, Z):
    """The corridor's acoustic-tile ceiling in a T-bar grid, frosted drum lights down the middle."""
    inside = (np.abs(X) < CX) & (Z > Z_BACK) & (Z < Z_END)
    a = pal_array(L.ACOUSTIC)
    gx, gz = X / 25.0, Z / 25.0
    rgb = np.repeat(a[3][None, :], X.shape[0], 0)
    pit = hash2(np.floor(X / 2.0), np.floor(Z / 3.0), 21) > 0.85
    rgb = np.where(pit[:, None], a[2], rgb)
    tbar = (np.abs(gx - np.round(gx)) < 0.06) | (np.abs(gz - np.round(gz)) < 0.04)
    rgb = np.where(tbar[:, None], a[1], rgb)
    for zl in CORR_LIGHTS:
        d = np.hypot(X / 15.0, (Z - zl) / 12.0)
        rgb = np.where((d < 1.25)[:, None], pal_array([L.CHROME[1]])[0], rgb)
        rgb = np.where((d < 1.0)[:, None], pal_array(["#f2dfb4"])[0], rgb)
        rgb = np.where((d < 0.55)[:, None], pal_array(["#fffaee"])[0], rgb)
        warm_light(rgb, d * 15, 40, colour="#f6cf7a", strength=0.25)
    out = rgba_of(rgb)
    out[..., :3] *= 0.85
    fog(out, Z, "#2a2230", 900, 1900, amount=0.55)
    out[~inside, 3] = 0
    return out


def end_wall_shader(X, Y):
    """The corridor's end: a steel casement window with the moon, a radiator under it."""
    blk = pal_array(L.FH_BLOCK)
    rgb = np.repeat(blk[5][None, :], X.shape[0], 0)
    rgb = np.where(((np.floor(Y / 8) % 2 == 0) & (np.abs(Y % 8) < 1))[:, None], blk[3], rgb)
    rgb = np.where((Y < 64)[:, None], pal_array([L.FH_BRICK[3]])[0], rgb)
    win = (np.abs(X) < 26) & (Y > 40) & (Y < 106)
    sky = pal_array(["#141a3a", "#1e2a5a", "#2c3a6c"])
    t = np.clip(((Y - 40) / 66 * 3).astype(int), 0, 2)
    rgb = np.where(win[:, None], sky[t], rgb)
    star = win & (hash2(np.floor(X / 2), np.floor(Y / 2), 31) > 0.93)
    rgb = np.where(star[:, None], pal_array(["#c8d0f0"])[0], rgb)
    moon = np.hypot(X - 8, Y - 88) < 5
    rgb = np.where(moon[:, None], pal_array(["#f6e7c4"])[0], rgb)
    frame = win & ((np.abs(X) < 1.6) | (np.abs(Y - 74) < 1.6))
    rgb = np.where(frame[:, None], pal_array(["#2a2e3e"])[0], rgb)
    rgb = np.where(((np.abs(X) < 30) & (Y > 34) & (Y <= 40))[:, None], pal_array([L.FH_SAND[4]])[0], rgb)
    rad = (np.abs(X) < 18) & (Y > 8) & (Y < 32)
    rgb = np.where(rad[:, None], np.where((np.floor(X / 3) % 2 == 0)[:, None], pal_array(["#8a8478"])[0], pal_array(["#5a564e"])[0]), rgb)
    out = rgba_of(rgb)
    out[..., :3] *= 0.8
    fog(out, np.full(X.shape, Z_END), "#2a2230", 900, 1900, amount=0.55)
    return out


def side_wall(side):
    """The near walls of the lounge end: block over brick; the lounge's stair door on the left,
    the extinguisher and a sign-up sheet on the right."""
    Lw, Hh = int(Z_BACK - NEAR_Z), 230
    cv = Canvas(Lw, Hh, seed=50 + side)
    L.hall_wall(cv, 0, Lw, Hh, top=0, seed=51 + side, rail=60)
    if side < 0:
        L.stair_door(cv, 70, Hh, label="STAIRS")
        exit_sign(cv, 61, Hh - 96)
    else:
        extinguisher(cv, 40, Hh - 70)
        cv.rect(80, Hh - 150, 26, 34, OUT); cv.rect(81, Hh - 149, 24, 32, "#f2ecdc")
        for yy in range(Hh - 144, Hh - 120, 4):
            cv.hline(84, yy, 18, "#5a5a6a")
    return cv.a


def far_wall():
    """The hall's far wall at room scale, with the corridor opening cut out (transparent)."""
    cv = Canvas(FW, FH, seed=60)
    L.hall_wall(cv, 0, FW, BASE_F, top=0, seed=61)
    for wx in (110, 400):                             # washes from the drum lights just above the frame
        for (rx, ry, a) in ((90, 70, 0.07), (60, 46, 0.07), (34, 26, 0.08)):
            soft_ellipse(cv, wx, 0, rx, ry, "#f6cf7a", a)
    mid = FW // 2
    # door 212, the RA board, the light switch
    L.dorm_door(cv, 40, BASE_F, "212", [("NOOR", L.CPAPER[3], "star", "#e8c24a"), ("BEX", L.CPAPER[2], "heart", "#c84a3c")],
                ("whiteboard",), seed=11)
    L.ra_board(cv, 80, 18, 132, 62, seed=3, ra="MIKA", room="210")
    L.light_switch(cv, 70, BASE_F - 58)
    # the cased opening into the corridor, the directional sign over it, the EXIT sign beyond
    ox0, ox1, otop = mid - OPEN_HW, mid + OPEN_HW, BASE_F - OPEN_H
    cv.rect(ox0 - 6, otop - 6, ox1 - ox0 + 12, OPEN_H + 6, OUT)
    cv.rect(ox0 - 5, otop - 5, ox1 - ox0 + 10, OPEN_H + 5, L.STEEL_T[3]); cv.hline(ox0 - 5, otop - 5, ox1 - ox0 + 10, L.STEEL_T[5])
    cv.vline(ox0 - 5, otop - 5, OPEN_H + 5, L.STEEL_T[4]); cv.vline(ox1 + 4, otop - 5, OPEN_H + 5, L.STEEL_T[1])
    cv.a[otop:BASE_F, ox0:ox1, 3] = 0
    L.room_sign(cv, mid - 33, otop - 32, lines=("201-214",))
    # the fountain, the class photo, the thermostat, the RA's door 210 with its lights and calendar
    L.drinking_fountain(cv, 318, BASE_F)
    framed_photo(cv, 346, 30, 42, 30, seed=5, rows=3, caption="FARRAND 1949")
    L.thermostat(cv, 404, 70)
    r_door = 452
    L.dorm_door(cv, r_door, BASE_F, "210", [("RA MIKA", L.CPAPER[4], "star", "#e8c24a")], ("calendar", "lights"), seed=12)
    L.pull_station(cv, 500, 66)
    for ox in (20, 150, 296, 420):
        outlet(cv, ox, BASE_F - 16)
    L.wall_shadow(cv, 0, BASE_F - 1, FW, depth=1)
    lights = [(r_door - 21 + i * 4, BASE_F - 72 - 19) for i in range(11)] + \
             [(r_door - 22, BASE_F - 72 - 19 + i * 5) for i in range(1, 17)] + \
             [(r_door + 21, BASE_F - 72 - 19 + i * 5) for i in range(1, 17)]
    return cv, lights


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#1a1420")
    v.ground(floor_shader)
    # the corridor, far to near: its end wall, ceiling, walls
    v.back(Z_END, end_wall_shader, region=lambda X, Y: (np.abs(X) < CX) & (Y < CH) & (Y >= 0))
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=CH)
    for side in (-1, 1):
        tex = corridor_wall(side)

        def shade_corr(u, Y, Z, tex=tex, side=side):
            o = texture_lookup(tex, u, CH - Y, wrap=False)
            o[..., :3] *= 0.84 if side < 0 else 0.74
            fog(o, Z, "#2a2230", 900, 1900, amount=0.55)
            return o
        v.plane((side * CX, Z_BACK), (side * CX, Z_END), shade_corr, y_max=CH)
    # the far wall flat over it
    flat, fairy = far_wall()
    fx0 = int(round(v.vx - FW / 2))
    fy0 = int(round(v.ground_y(Z_BACK) - FH))
    v.strip(flat.a, fy0, fx0)
    # the near side walls
    for side in (-1, 1):
        tex = side_wall(side)
        Lw = tex.shape[1]

        def shade_side(u, Y, Z, tex=tex, side=side, Lw=Lw):
            uu = Lw - 1 - u if side < 0 else u
            o = texture_lookup(tex, uu, 230 - Y, wrap=False)
            o[..., :3] *= 0.8
            return o
        v.plane((side * WALL_X, Z_BACK), (side * WALL_X, NEAR_Z), shade_side, y_max=230)
    # floormates' things along the wall (room-scale sprites)
    for (made, X, Z) in [(L.box_stack(40, 44, labels=("JAKERSON", "TENNIS"), seed=2), -96, 432),
                         (L.mini_fridge(26, 36, seed=3), 150, 434),
                         (L.leaning_bike(54, 34, seed=6), 318, 436),
                         (L.laundry_pile(36, 24, seed=5), 326, 372),
                         (L.guitar_case(18, 50, seed=4), -330, 400)]:
        s_, ax_, ay_ = made
        v.sprite(s_.a, X, Z, anchor=(ax_ / s_.w, ay_ / s_.h), scale=SC)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp: the drum lights' hot spots (a moth circles the nearest)
    ex, ey = v.project(0, CH, CORR_LIGHTS[0])
    pts = []
    for zl in CORR_LIGHTS:
        sx, sy = v.project(0, CH, zl)
        pts.append([int(round(sx)), int(round(sy)) + 1, "fff0c4", 1])
    cv.save(os.path.join(out, "battle-far.png"))

    fairy_pts = [[fx0 + x, fy0 + y, ["f6cf7a", "f2a0a0", "a0d8f0", "b0f0a0"][k % 4], 1] for k, (x, y) in enumerate(fairy)]
    # the open door's TV light on the corridor floor
    a = v.project(CX - 2, 0, Z_BACK + OPEN_DOOR[0] + 6)
    b = v.project(CX - 2, 0, Z_BACK + OPEN_DOOR[1])
    tvx0, tvx1 = int(round(min(a[0], b[0]))) - 3, int(round(max(a[0], b[0])))
    tvy = int(round(b[1]))
    tv = [tvx0, tvy - 3, max(3, tvx1 - tvx0), 4]
    flick = pts[1]
    return {
        "far": res + "battle-far.png",
        "layers": [
            {"kind": "twinkle", "points": pts, "rate": 0.9, "min": 0.65},
            {"kind": "blink", "pattern": "11111111111101111111111111110101", "rate": 6.0,
             "rects": [[flick[0] - 3, flick[1] - 2, 7, 3, "141223", 0.6]]},
            {"kind": "blink", "pattern": "1101001110", "rate": 5.0, "rects": [tv + ["a8c4f0", 0.35]]},
            {"kind": "blink", "pattern": "0010110001", "rate": 5.0, "rects": [tv + ["e07a5a", 0.25]]},
            {"kind": "twinkle", "points": fairy_pts, "rate": 1.4, "min": 0.3},
            {"kind": "fauna", "fauna": [{"kind": "lamp_moth", "x": int(round(ex)) + 6, "y": int(round(ey)) + 12,
                                         "range": 8, "speed": 1.4, "rate": 9.0}]},
            {"kind": "particles", "style": "dust", "count": 18, "rect": [90, 10, 460, 120], "speed": [1, 3], "color": "fff0c4"},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
