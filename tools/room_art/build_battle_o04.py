"""Battle backdrop for the cabinet room (O04): standing on the long red carpet, looking down the
room at Todd's stamp-audit rig on the end wall. Tall walnut card cabinets line both walls under
the oxblood damask, with velvet-draped windows (moonlight laid across the herringbone parquet) on
the left, portraits, the charter and brass sconces; a coffered walnut ceiling.
Animated: the three stamps thump in turn, the caged AUDIT lamp pulses and throws a slow red sweep
across the room, the sconces breathe, forms fly loose through the air, dust turns in the moonlight."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, text, text_width
from props import OUT
from lib_eng import micro_text, micro_width
from lib_oldmain import (cornice_om, stencil_frieze, damask, panel_wainscot, draped_window, oval_portrait, stamp_rig, card_cabinet,
                         sconce_om, framed_photo, OXBLOOD, WALNUT, PARQUET, BRASS_OM, RUG_RED, RED_STAMP, CREAM_TRIM)
from build_o04 import charter, DAMASK, REST, MID, DOWN
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "O04"
INK = "#10121e"
HAZE = "#24141a"
T = ROOM_TO_BATTLE
VX = 290
Z0, Z_END = 150.0, 700.0
WALL_X = 300.0
HALL_H = 250.0
TEX_H = int(round(HALL_H / T)) + 1
DADO = 104                                  # dado cap (room px from the top of a wall texture)
L_WINDOWS = (176, 304)                      # left wall: window glass u (room px), 30 wide
L_CABINETS = (96, 226)
R_CABINETS = (70, 170, 290)
L_SCONCES = (162, 288)
R_SCONCES = (148, 252)
RUNNER = 92.0                               # half width of the carpet down the middle


# ---------------------------------------------------------------------------- wall textures
def _paste(cv, sprite, x, bottom):
    """Composite a prop sprite into a wall texture with its base on `bottom`."""
    spr, ax, ay = sprite
    a = spr.a[:ay + 1]
    h, w = a.shape[:2]
    y0 = bottom - h + 1
    x0 = x
    ys0, xs0 = max(0, -y0), max(0, -x0)
    ys1, xs1 = min(h, cv.h - y0), min(w, cv.w - x0)
    if ys1 <= ys0 or xs1 <= xs0:
        return
    src = a[ys0:ys1, xs0:xs1]
    reg = cv.a[y0 + ys0:y0 + ys1, x0 + xs0:x0 + xs1]
    al = src[..., 3:4]
    reg[..., :3] = src[..., :3] * al + reg[..., :3] * (1 - al)


def wall_base(length, seed):
    cv = Canvas(length, TEX_H, seed=seed)
    damask(cv, 0, 22, length, DADO - 22, pal=DAMASK, seed=seed, rep=(16, 20))
    cornice_om(cv, 0, 0, length, ceiling=("#1a1418", "#261c22", "#33262c"), trim=CREAM_TRIM)
    stencil_frieze(cv, 0, 13, length, ground=OXBLOOD[1], gilt=BRASS_OM, every=14)
    cv.rect(0, 30, length, 2, WALNUT[3]); cv.hline(0, 30, length, WALNUT[6])
    panel_wainscot(cv, 0, DADO, length, TEX_H - DADO, pal=WALNUT, panel=34)
    return cv


def left_wall(length):
    cv = wall_base(length, 31)
    for k, u in enumerate(L_WINDOWS):
        draped_window(cv, u, 36, 30, 60, seed=90 + k, moon=(u + 20, 50, 4) if k == 0 else None)
    for k, u in enumerate(L_CABINETS):
        _paste(cv, card_cabinet(64, 96, seed=40 + k, ladder=(k == 0), label=("A-F", "G-L")[k]), u - 5, TEX_H - 1)
        oval_portrait(cv, u + 32, 30, rx=8, ry=10, seed=k, bg=("#2e3a36", "#36303e")[k])
    for u in L_SCONCES:
        sconce_om(cv, u, 70)
    return cv.a


def right_wall(length):
    cv = wall_base(length, 47)
    for k, u in enumerate(R_CABINETS):
        _paste(cv, card_cabinet(64, 96, seed=50 + k, ladder=(k == 1), label=("M-R", "S-V", "W-Z")[k]), u - 5, TEX_H - 1)
    oval_portrait(cv, 102, 30, rx=8, ry=10, seed=3, bg="#36303e")
    charter(cv, 236, 40, 46, 40)
    framed_photo(cv, 186, 26, 34, 24, seed=7, rows=2)
    for u in R_SCONCES:
        sconce_om(cv, u, 70)
    return cv.a


def end_wall(Wp, Hp):
    """The end wall at its on-screen size, before the rig is bolted on: cornice, frieze, damask,
    a walnut dado, a sconce at each side."""
    cv = Canvas(Wp, Hp, seed=5)
    s = T * 320.0 / Z_END
    dado = int(round((TEX_H - DADO) * s))
    damask(cv, 0, 12, Wp, Hp - dado - 12, pal=DAMASK, seed=9, rep=(12, 16))
    cv.rect(0, 0, Wp, 4, "#261c22"); cv.hline(0, 4, Wp, CREAM_TRIM[4]); cv.hline(0, 5, Wp, CREAM_TRIM[2])
    stencil_frieze(cv, 0, 6, Wp, ground=OXBLOOD[1], gilt=BRASS_OM, every=12)
    panel_wainscot(cv, 0, Hp - dado, Wp, dado, pal=WALNUT, panel=24)
    glows = [sconce_om(cv, 14, 56), sconce_om(cv, Wp - 22, 56)]
    return cv, glows


# ---------------------------------------------------------------------------- shaders
def herring(X, Z, A=10.0, seed=3):
    """90-degree herringbone parquet in world units: tone index per block and a joint mask."""
    cu, cw = np.floor(X / A).astype(np.int64), np.floor(Z / A).astype(np.int64)
    fx, fz = X / A - cu, Z / A - cw
    d = cu - cw
    r = d % 4
    b = -(d - r) // 4
    k = np.where(r == 0, cu + 2 * b, np.where(r == 1, cu + 2 * b - 1, cu - 2 + 2 * b))
    horiz = r < 2
    t = hash2(k * 2 + horiz, b, seed)
    tone = np.select([t < 0.3, t < 0.75], [3, 4], 5)
    joint = np.where(horiz, (fz > 0.86) | ((r == 1) & (fx > 0.86)), (fx > 0.86) | ((r == 2) & (fz > 0.86)))
    return tone, joint


def floor_shader(X, Z):
    p = pal_array(PARQUET)
    tone, joint = herring(X, Z)
    rgb = p[tone]
    rgb[joint] = p[2]
    # moonlight from the left windows: panes laid across the boards, slanting toward us
    for u in L_WINDOWS:
        z0, z1 = Z0 + u * T, Z0 + (u + 30) * T
        mx = X + WALL_X
        zz = Z + 0.6 * mx
        moon = (mx > 0) & (mx < 150) & (zz > z0) & (zz < z1)
        bar = moon & ((np.abs(zz - (z0 + z1) / 2) < 3) | (np.abs(mx - 75) < 3))
        rgb[moon] = rgb[moon] * 0.76 + np.array(C("#b4c4f0")[:3]) * 0.24
        rgb[bar] = rgb[bar] * 0.85
    # the long carpet down the middle
    r = pal_array(RUG_RED)
    ax = np.abs(X)
    run = (ax < RUNNER) & (Z < Z_END - 40)
    rgb[run] = r[2]
    border = run & (ax > RUNNER - 18)
    rgb[border] = r[4]
    rgb[run & (np.abs(ax - (RUNNER - 18)) < 2)] = r[6]
    rgb[run & (ax > RUNNER - 3)] = r[6]
    dots = border & (np.abs(ax - (RUNNER - 9)) < 3) & ((Z % 22) < 6)
    rgb[dots] = r[6]
    field = run & (ax < RUNNER - 20)
    lzx, lzz = (X + 16) % 32 - 16, (Z + (np.floor((X + 16) / 32) % 2) * 16) % 32 - 16
    lz = field & ((np.abs(lzx) / 5 + np.abs(lzz) / 8) < 1)
    rgb[lz] = r[3]
    rgb[field & (np.abs(lzx) < 1.2) & (np.abs(lzz) < 1.6)] = r[6]
    fringe = (ax < RUNNER) & (Z >= Z_END - 40) & (Z < Z_END - 32)
    rgb[fringe] = np.array(C("#c8b892")[:3])
    # lamplight and the red of the AUDIT lamp at the far end
    for z in (Z0 + L_SCONCES[0] * T, Z0 + L_SCONCES[1] * T):
        warm_light(rgb, np.hypot(X + WALL_X, (Z - z) * 0.8), 120, strength=0.22)
    for z in (Z0 + R_SCONCES[0] * T, Z0 + R_SCONCES[1] * T):
        warm_light(rgb, np.hypot(X - WALL_X, (Z - z) * 0.8), 120, strength=0.22)
    warm_light(rgb, np.hypot(X, (Z - Z_END) * 0.8), 160, colour="#e04a3a", strength=0.12)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 420, 1100, amount=0.45)
    return out


def ceiling_shader(X, Z):
    rgb = np.zeros((X.shape[0], 3), np.float32)
    rgb[:] = np.array(C("#2a1a1c")[:3])
    coffer = 90.0
    fx, fz = (X + 45) % coffer, Z % coffer
    beam = (fx < 10) | (fz < 10)
    rgb[beam] = np.array(C(WALNUT[3])[:3])
    rgb[beam & ((fx < 2) | (fz < 2))] = np.array(C(WALNUT[5])[:3])
    inner = ~beam & (fx > 16) & (fz > 16) & (fx < coffer - 6) & (fz < coffer - 6)
    rgb[inner] = np.array(C("#3a2226")[:3])
    rose = ~beam & (np.hypot(fx - 50, fz - 50) < 6)
    rgb[rose] = np.array(C(BRASS_OM[2])[:3])
    rgb[np.abs(X) > WALL_X - 14] = np.array(C(CREAM_TRIM[2])[:3]) * 0.6
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 400, 1100, amount=0.5)
    return out


# ---------------------------------------------------------------------------- build
def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, vx=VX, cam=52, fill="#141223")
    v.ground(floor_shader, z_max=Z_END)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=HALL_H, z_max=Z_END)
    L = int((Z_END - Z0) / T) + 2
    sconces = []
    for side in (-1, 1):
        tex = left_wall(L) if side < 0 else right_wall(L)
        for u in (L_SCONCES if side < 0 else R_SCONCES):
            sconces.append((side, u))

        def shade_wall(u, Y, Z, tex=tex, side=side):
            o = texture_lookup(tex, u / T, (HALL_H - Y) / T, wrap=False)
            o[..., :3] *= 0.84
            for (sd, su) in sconces:
                if sd == side:
                    warm_light(o[..., :3], np.hypot(Z - (Z0 + su * T), (Y - (HALL_H - 64 * T)) * 0.8), 90, strength=0.2)
            return fog(o, Z, HAZE, 420, 1100, amount=0.45)
        v.plane((side * WALL_X, Z0), (side * WALL_X, Z_END), shade_wall, y_max=HALL_H)
    s_end = v.scale(Z_END)
    Wp = int(round(2 * WALL_X * s_end)) + 2
    Hp = int(round(HALL_H * s_end))
    ew, end_glows = end_wall(Wp, Hp)
    ew.a[..., :3] *= 0.9
    fx0 = int(round(v.vx - Wp / 2))
    fy0 = int(round(v.ground_y(Z_END) - Hp))
    v.strip(ew.a, fy0, fx0)
    v.rows(156, 360, INK, 0.0, 0.62)
    base = v.reduce(112)

    # the rig, crisp at 1:1 on the end wall
    cx, top = int(round(v.vx)), fy0 + 4

    def rig(lowered):
        cv = Canvas(base.w, base.h)
        cv.a[:] = base.a
        pts = stamp_rig(cv, cx, top, state="active", lowered=lowered, pipe_to=fy0 + Hp - 1)
        return cv, pts

    cv, pts = rig((REST, REST, REST))
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    # the AUDIT lamp pulses red
    lit = Canvas(base.w, base.h)
    lit.a[:] = cv.a
    lx, ly = pts["lamp"]
    for rr, a in ((14, 0.06), (9, 0.1)):
        lit.ellipse(lx - rr, ly - rr, rr * 2 + 1, rr * 2 + 1, C("#ff4a3a", a))
    lit.ellipse(lx - 4, ly - 3, 9, 9, RED_STAMP[3]); lit.ellipse(lx - 3, ly - 2, 6, 5, RED_STAMP[4]); lit.px(lx - 1, ly - 1, "#ffe0d0")
    for k in (-3, 0, 3):
        lit.vline(lx + k, ly - 4, 9, "#4a4a58")
    lit.hline(lx - 5, ly, 11, "#4a4a58")
    sx, sy, sw, sh = pts["sign"]
    lit.rect(sx, sy, sw, sh, "#2a0e10")
    text(lit, "AUDIT", sx + sw // 2 - text_width("AUDIT") // 2, sy - 1, "#ff6a50")
    bx, by = lx - 20, max(0, ly - 14)
    crop = Canvas(40, 30)
    crop.a[:] = lit.a[by:by + 30, bx:bx + 40]
    crop.save(os.path.join(out, "battle-lamp.png"))
    layers.append({"kind": "blink", "pattern": "110000", "rate": 3.0, "texture": res + "battle-lamp.png", "x": bx, "y": by})
    # the three stamps thump in turn
    beam_top = pts["stamps"][0][1]
    table = pts["table"]
    n = 18
    for k, (scx, scy) in enumerate(pts["stamps"]):
        box = (scx - 22, beam_top, 44, table + 1 - beam_top)
        for f, low in (("mid", MID), ("down", DOWN)):
            lowered = [REST, REST, REST]
            lowered[k] = low
            fr, _ = rig(tuple(lowered))
            c2 = Canvas(box[2], box[3])
            c2.a[:] = fr.a[box[1]:box[1] + box[3], box[0]:box[0] + box[2]]
            name = f"battle-stamp-{k}-{f}.png"
            c2.save(os.path.join(out, name))
            pat = ["0"] * n
            start = k * 6
            if f == "mid":
                pat[start % n] = "1"; pat[(start + 2) % n] = "1"
            else:
                pat[(start + 1) % n] = "1"
            layers.append({"kind": "blink", "pattern": "".join(pat), "rate": 7.0, "texture": res + name, "x": box[0], "y": box[1]})
    # sconce glows (walls and end wall)
    pts_tw = []
    for (side, u) in sconces:
        X, Z, Y = side * WALL_X, Z0 + (u + 4) * T, HALL_H - 60 * T
        px_, py_ = v.project(X, Y, Z)
        if 0 <= px_ < 640 and 0 <= py_ < 160 and not (392 <= px_ <= 628 and py_ <= 72):
            pts_tw.append([int(round(px_)), int(round(py_)), "fde9b6", 1])
    for (gx, gy) in end_glows:
        pts_tw.append([fx0 + gx, fy0 + gy, "fde9b6", 1])
    layers += [
        {"kind": "beam", "x": lx, "y": ly + 2, "angle": 90, "sweep": 38, "period": 7.0, "length": 150 - ly, "width": 80,
         "alpha": 0.12, "color": "ff5a40", "floor": 150},
        {"kind": "twinkle", "points": pts_tw, "rate": 1.3, "min": 0.5},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [0, 40, 170, 110], "speed": [-2, 3], "color": "c8d4f0"},
        {"kind": "fauna", "fauna": [{"kind": "loose_page", "x": 120, "y": 70, "fly": 14.0, "rate": 6.0},
                                    {"kind": "loose_page", "x": 420, "y": 112, "fly": 10.0, "rate": 5.0}]},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
