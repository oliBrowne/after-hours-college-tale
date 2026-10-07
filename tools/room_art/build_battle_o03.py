"""Battle backdrop for the empty office (O03): standing on the worn boards, looking across the big
partners' desk to the quiet window. The desk sits on its faded green rug with the open CEREMONY
DIRECTORY, the banker's lamp and the first recording on its reel-to-reel machine; behind it the
triple window with the blind half down and the moon over the Flatirons, the window seat below.
The left wall carries the chalkboard with the first purpose (GATHER ALL / DO NOT CLOSE) and the
shut service door to the cabinet room; the right wall the filing cabinet with its empty drawer,
pale squares where pictures hung, the calendar on an old month. Moonlight falls through the
window in panes across the floor.
Animated: the reels turn, the banker's lamp and the standard lamp breathe, Jules's phone pulses
on the little table, dust turns in the moonlight, a moth worries at the glass."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT
from lib_eng import micro_text, micro_width
from lib_oldmain import (plaster_om, cornice_om, panel_wainscot, sash_window, venetian_blind, chalkboard, ghost_frame, oak_frame,
                         reel_recorder, banker_lamp_om, radiator, schoolhouse_clock, OFFICE_OCHRE, OAK_IN, GILT_OM, CREAM_TRIM,
                         BOARDS, RUG_GREEN, PAPER_TINTS)
from build_o03 import partners_desk, phone_table, pleated_lamp, service_door, filing_cabinet, calendar, coat_stand
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "O03"
INK = "#10121e"
HAZE = "#1e1a1c"
T = ROOM_TO_BATTLE
Z0, Z_END = 150.0, 740.0
WALL_X = 280.0
HALL_H = 250.0
TEX_H = int(round(HALL_H / T)) + 1
DADO = 104                                  # dado cap (room px from the top of a wall texture)
DESK_Z = 600.0                              # the partners' desk (front face)
DESK_X = -34.0
LAMP = (-196.0, 430.0)                      # pleated standard lamp
WIN_HALF = 64.0                             # half-width of the window in world units
MOON_SLANT = 0.32                           # moonlight drifts left as it comes toward us


# ---------------------------------------------------------------------------- wall textures
def side_wall(length, left, seed=0):
    """A side wall laid flat (u from the camera end toward the window wall), at room scale."""
    cv = Canvas(length, TEX_H, seed=seed)
    plaster_om(cv, 0, 6, length, DADO - 6, pal=OFFICE_OCHRE, seed=seed, shadow_top=6, cracks=0, body=(5, 6))
    cornice_om(cv, 0, -3, length, ceiling=("#1a1620", "#241e28", "#2e2632"))
    cv.rect(0, 24, length, 3, OAK_IN[3]); cv.hline(0, 24, length, OAK_IN[6]); cv.hline(0, 26, length, OAK_IN[1])
    panel_wainscot(cv, 0, DADO, length, TEX_H - DADO, pal=OAK_IN, panel=34)
    if left:
        ghost_frame(cv, 20, 40, 34, 28, OFFICE_OCHRE[5], rail_y=24)
        chalkboard(cv, 70, 34, 150, 64, seed=4)
        # the service door near the window wall (moved into the wall texture: bottom at the floor)
        tmp = Canvas(length, 142)
        service_door(tmp, 250, 34, 74, ajar=False)
        sub = tmp.a[142 - 74 - 14:142, 250 - 7:250 + 34 + 7]
        y0 = TEX_H - sub.shape[0]
        reg = cv.a[y0:TEX_H, 243:243 + sub.shape[1]]
        al = sub[..., 3:4]
        reg[..., :3] = sub[..., :3] * al + reg[..., :3] * (1 - al)
    else:
        ghost_frame(cv, 30, 38, 26, 34, OFFICE_OCHRE[5], rail_y=24)
        ghost_frame(cv, 66, 46, 40, 26, OFFICE_OCHRE[5], rail_y=24)
        calendar(cv, 130, 50)
        radiator(cv, 160, TEX_H - 32, 36, 24)
        tmp = Canvas(length, 142)
        filing_cabinet(tmp, 230, 62, 44)
        coat_stand(tmp, 290)
        sub = tmp.a[:, :]
        y0 = TEX_H - 142
        reg = cv.a[max(0, y0):TEX_H, :]
        sub = sub[max(0, -y0):, :]
        al = sub[..., 3:4]
        reg[..., :3] = sub[..., :3] * al + reg[..., :3] * (1 - al)
    return cv.a


def window_wall(Wp, Hp):
    """The window wall at its on-screen size: ochre plaster, picture rail, the triple sash with
    its blind and the moon, the window seat, a stopped clock, two pale squares."""
    cv = Canvas(Wp, Hp, seed=3)
    s = T * 320.0 / Z_END                       # room px -> screen px at this depth
    dado = int(round((TEX_H - DADO) * s))
    plaster_om(cv, 0, 3, Wp, Hp - dado - 3, pal=OFFICE_OCHRE, seed=7, shadow_top=3, cracks=0, body=(5, 6), cell=18)
    cv.rect(0, 0, Wp, 3, "#241e28"); cv.hline(0, 2, Wp, CREAM_TRIM[3])
    cv.hline(0, int(24 * s), Wp, OAK_IN[5]); cv.hline(0, int(24 * s) + 1, Wp, OAK_IN[2])
    panel_wainscot(cv, 0, Hp - dado, Wp, dado, pal=OAK_IN, panel=22)
    cx = Wp // 2
    ww, wh = 84, 58
    wx, wy = cx - ww // 2 + 8, 10
    sw = (ww - 6) // 3
    for k in range(3):
        sash_window(cv, wx + k * (sw + 3), wy, sw, wh, seed=60 + k, moon=(wx + k * (sw + 3) + 12, wy + 18, 4) if k == 2 else None)
    cv.rect(wx - 7, wy - 6, ww + 14, 4, OUT); cv.rect(wx - 6, wy - 5, ww + 12, 2, CREAM_TRIM[3]); cv.hline(wx - 6, wy - 5, ww + 12, CREAM_TRIM[5])
    venetian_blind(cv, wx - 2, wy + 1, ww + 4, 15, slat=2)
    seat = wy + wh + 8
    cv.rect(wx - 10, seat, ww + 20, Hp - seat, OUT)
    cv.rect(wx - 9, seat + 1, ww + 18, 4, "#3e5a4e"); cv.hline(wx - 9, seat + 1, ww + 18, "#5a7a6a")
    panel_wainscot(cv, wx - 9, seat + 5, ww + 18, Hp - seat - 5, pal=OAK_IN, panel=16)
    ghost_frame(cv, 14, 26, 24, 20, OFFICE_OCHRE[5], rail_y=int(24 * s), hook=False)
    ghost_frame(cv, Wp - 40, 28, 20, 26, OFFICE_OCHRE[5], rail_y=int(24 * s), hook=False)
    schoolhouse_clock(cv, 62, 18, hour=4, minute=10)
    return cv, (wx, wy, ww, wh)


# ---------------------------------------------------------------------------- shaders
def floor_shader(X, Z):
    p = pal_array(BOARDS)
    row = 12.0
    j = np.floor(Z / row)
    off = hash2(j, 0, 3) * 200
    i = np.floor((X + off) / 170.0)
    t = hash2(i, j, 5)
    tone = np.where(t < 0.55, 4, np.where(t < 0.8, 3, 5))
    rgb = p[tone]
    fz = Z / row - j
    rgb[fz < 0.08] = p[2]
    rgb[(fz > 0.08) & (fz < 0.16)] = rgb[(fz > 0.08) & (fz < 0.16)] * 0.9 + p[6] * 0.1
    fx = (X + off) / 170.0 - i
    rgb[fx < 0.012] = p[1]
    grain = hash2(np.floor(X / 9), j * 7 + np.floor(fz * 3), 9) < 0.08
    rgb[grain] = rgb[grain] * 0.9
    # the faded rug under the desk
    g = pal_array(RUG_GREEN)
    RX = X - DESK_X
    rug = (np.abs(RX) < 150) & (Z > DESK_Z - 90) & (Z < DESK_Z + 110)
    rgb[rug] = g[2]
    border = rug & ((np.abs(RX) > 140) | (Z < DESK_Z - 82) | (Z > DESK_Z + 102))
    rgb[border] = g[4]
    rgb[rug & ((np.abs(np.abs(RX) - 134) < 2) | (np.abs(Z - (DESK_Z - 76)) < 2))] = g[1]
    loz = rug & (np.abs(RX) / 90 + np.abs(Z - DESK_Z + 30) / 46 < 1)
    rgb[loz] = g[3]
    rgb[rug & (np.abs(RX) / 40 + np.abs(Z - DESK_Z + 30) / 20 < 1)] = g[5]
    # moonlight through the window: panes falling forward and to the left
    mx = X + (Z_END - Z) * MOON_SLANT
    moon = (np.abs(mx) < WIN_HALF) & (Z > 330) & (Z < Z_END)
    bars = moon & ((np.abs(np.abs(mx) - WIN_HALF / 3) < 3) | (np.abs(Z - 640) < 3))
    rgb[moon] = rgb[moon] * 0.78 + np.array(C("#b4c4f0")[:3]) * 0.22
    rgb[bars] = rgb[bars] * 0.85
    warm_light(rgb, np.hypot(X - DESK_X - 70, (Z - DESK_Z) * 0.7), 120, strength=0.3)
    warm_light(rgb, np.hypot(X - LAMP[0], (Z - LAMP[1]) * 0.6), 100, strength=0.32)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 500, 1200, amount=0.4)
    return out


def ceiling_shader(X, Z):
    rgb = np.zeros((X.shape[0], 3), np.float32)
    rgb[:] = np.array(C("#3a3230")[:3])
    blot = hash2(np.floor(X / 60), np.floor(Z / 60), 2) > 0.7
    rgb[blot] = np.array(C("#423834")[:3])
    rose = np.hypot(X, (Z - 560) * 1.0)
    rgb[np.abs(rose - 26) < 3] = np.array(C("#5a4c44")[:3])
    rgb[rose < 9] = np.array(C("#5a4c44")[:3])
    rgb[np.abs(X) > WALL_X - 14] = np.array(C(CREAM_TRIM[2])[:3]) * 0.6
    warm_light(rgb, np.hypot(X - DESK_X - 70, Z - DESK_Z), 110, strength=0.12)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 400, 1200, amount=0.5)
    return out


# ---------------------------------------------------------------------------- build
def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#141223")
    v.ground(floor_shader, z_max=Z_END)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=HALL_H, z_max=Z_END)
    L = int((Z_END - Z0) / T) + 2
    for side in (-1, 1):
        tex = side_wall(L, left=(side < 0), seed=70 + side)

        def shade_wall(u, Y, Z, tex=tex, side=side):
            o = texture_lookup(tex, u / T, (HALL_H - Y) / T, wrap=False)
            o[..., :3] *= 0.82
            if side < 0:
                warm_light(o[..., :3], np.abs(Z - LAMP[1]) + np.abs(Y - 60) * 0.6, 120, strength=0.22)
            return fog(o, Z, HAZE, 500, 1200, amount=0.4)
        v.plane((side * WALL_X, Z0), (side * WALL_X, Z_END), shade_wall, y_max=HALL_H)
    s_end = v.scale(Z_END)
    Wp = int(round(2 * WALL_X * s_end)) + 2
    Hp = int(round(HALL_H * s_end))
    ww, win = window_wall(Wp, Hp)
    ww.a[..., :3] *= 0.9
    fx0 = int(round(v.vx - Wp / 2))
    fy0 = int(round(v.ground_y(Z_END) - Hp))
    v.strip(ww.a, fy0, fx0)
    # the desk (front face at DESK_Z), the lamp and the phone table, at room scale
    desk, dax, day = partners_desk(210, 52, seed=3, items=False)
    dsx, dsy, ds = v.sprite(desk.a, DESK_X, DESK_Z, anchor=(dax / desk.w, day / desk.h), scale=T)
    lamp, lax, lay = pleated_lamp(68)
    lsx, lsy, ls = v.sprite(lamp.a, LAMP[0], LAMP[1], anchor=(lax / lamp.w, lay / lamp.h), scale=T)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp things on the desk top at 1:1: the recorder (left), the ledger, the phone, the lamp (right)
    top_y = int(round(dsy - (52 - 2) * ds))
    left = int(round(dsx - 105 * ds))
    right = int(round(dsx + 105 * ds))
    rx, ry = left + 8, top_y - 18
    reel_recorder(cv, rx, ry, w=40, h=20, angle=0.0, lit=True)
    lx, ly, lw, lh = left + 60, top_y - 9, 46, 11
    cv.rect(lx - 1, ly - 1, lw + 2, lh + 3, OUT); cv.rect(lx, ly + lh - 1, lw, 3, "#5a2a22")
    for (px_, pw_) in ((lx, lw // 2), (lx + lw // 2, lw // 2)):
        cv.rect(px_, ly, pw_, lh, "#ece2c6"); cv.hline(px_, ly, pw_, "#fff6dc")
        for yy in range(ly + 3, ly + lh - 1, 2):
            cv.hline(px_ + 2, yy, pw_ - 4, C("#5a4a3a", 0.45))
    cv.vline(lx + lw // 2, ly, lh, "#a89a7c")
    micro_text(cv, "VAL", lx + 3, ly + 2, "#7a2a24")
    cv.vline(lx + lw // 2 + 5, ly + lh - 1, 5, "#b82a26")
    phx, phy = lx + lw + 12, top_y - 2
    cv.rect(phx - 1, phy - 3, 9, 5, OUT); cv.rect(phx, phy - 2, 7, 3, "#8ac0e8"); cv.hline(phx, phy - 2, 7, "#c8e4f8"); cv.px(phx + 6, phy - 2, "#e04a3a")
    banker_lamp_om(cv, right - 26, top_y + 2, lit=True)
    lamp_pt = (right - 26, top_y - 7)
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    # the reels turning: four frames of the machine's face
    for k in range(4):
        fr = Canvas(42, 22)
        reel_recorder(fr, 1, 1, w=40, h=20, angle=k * np.pi / 6, lit=True)
        name = f"battle-reels-{k}.png"
        fr.save(os.path.join(out, name))
        pat = ["0"] * 4
        pat[k] = "1"
        layers.append({"kind": "blink", "pattern": "".join(pat), "rate": 6.0, "texture": res + name, "x": rx - 1, "y": ry - 1})
    # Jules's phone lights up now and then with the unsent message
    layers.append({"kind": "blink", "pattern": "1100000000", "rate": 3.0,
                   "rects": [[phx - 4, phy - 5, 15, 9, "a8d0f0", 0.22], [phx, phy - 2, 7, 3, "e8f4fc", 0.8]]})
    wx, wy, ww_, wh = win
    layers += [
        {"kind": "twinkle", "points": [[lamp_pt[0], lamp_pt[1], "fde9b6", 1], [int(round(lsx)), int(round(lsy - 63 * ls)), "fff0c4", 2]],
         "rate": 1.4, "min": 0.5},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [fx0 + wx - 60, fy0 + wy + 10, ww_ + 60, 120], "speed": [-2, 2], "color": "c8d4f0"},
        {"kind": "fauna", "fauna": [{"kind": "lamp_moth", "x": fx0 + wx + ww_ - 10, "y": fy0 + wy + 30, "range": 6, "speed": 1.7, "rate": 8.0}]},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
