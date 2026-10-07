"""Battle backdrop for the house party (H02): in the middle of the living room, looking down its
length to the fireplace with the letters over the mantel and the kitchen doorway glowing beside it.
The staircase and bay window run along the left wall, the DJ corner (bedsheet banner, TV visualiser,
neon Flatirons, speakers and the DJ table) along the right, string lights zig-zag across the
ceiling round a disco ball, and the crowd stands two deep along both walls as backlit silhouettes.
Coloured beams sweep the floor, the TV bounces, the disco ball throws sparkles everywhere."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON
from interior import crown
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_farrand import festoon
from h01_lib import CUP, HOUSE_B, SHADOW
from h02_lib import (GREEN_WALL, OAK, party_wall, oak_wainscot, led_strip, staircase, bay_window, fireplace_mantel,
                     composite_frame, kitchen_opening, wall_tv, bedsheet, pong_table, dj_table, speaker_stand,
                     leather_couch)
import build_h02 as room

INK = "#10121e"
HAZE = "#24182c"
WALL_X = 360.0
CEIL = 220.0
Z_NEAR, Z_BACK = 300.0, 860.0
Z_WALL0 = 100.0                           # side walls start behind the camera
S = ROOM_TO_BATTLE
TEX_H = int(CEIL / S) + 1                 # wall textures are painted at room scale
FLOOR = ["#2a1a18", "#3e2620", "#53342a", "#654030", "#764c38", "#86583e"]


def wall_canvas(w):
    cv = Canvas(w, TEX_H, seed=w)
    party_wall(cv, 0, 0, w, TEX_H - 30, seed=w, rail=16)
    oak_wainscot(cv, 0, TEX_H - 30, w, 30)
    crown(cv, 0, 0, w)
    return cv


def left_wall():
    """Near to far: the bay window, then the staircase climbing toward the back."""
    L = int((Z_BACK - Z_WALL0) / S) + 2
    cv = wall_canvas(L)
    bay_window(cv, 150, 22, 96, 66, seed=5)
    staircase(cv, L - 6, TEX_H, steps=10, run=11, rise=8, seed=4)
    return cv.a


def right_wall():
    """Painted as seen: far end on the left, near end on the right. The DJ corner's wall."""
    L = int((Z_BACK - Z_WALL0) / S) + 2
    cv = wall_canvas(L)
    led_strip(cv, 0, L, 6)
    room.neon_flatirons(cv, 40, 22)
    tv = wall_tv(cv, 140, 40, 60, 34)
    bedsheet(cv, 220, 14, 80, 28, seed=10)
    composite_frame(cv, 18, 66, 26, 34, seed=12)
    return cv.a, tv, L


def back_wall():
    w = int(2 * WALL_X / S) + 2
    cv = wall_canvas(w)
    cx = w // 2
    fireplace_mantel(cv, cx - 30, TEX_H, seed=7)
    composite_frame(cv, cx - 110, 26, 26, 36, seed=6)
    kitchen_opening(cv, cx + 50, TEX_H, w=76, h=92, seed=9)
    # a hallway arch on the far left with the front hall light
    cv.rect(12, TEX_H - 84, 46, 84, OAK[1]); cv.rect(16, TEX_H - 80, 38, 80, "#2a2030")
    cv.rect(18, TEX_H - 78, 34, 30, C("#f6cf7a", 0.18)); cv.rect(30, TEX_H - 86, 10, 4, "#f6cf7a")
    return cv.a, cx


def floor_shader(X, Z):
    n = X.shape[0]
    plank = 14.0
    col = np.floor(X / plank)
    fx = X / plank - col
    length = 90 + 60 * hash2(col, 3)
    off = hash2(col, 5) * length
    seg = np.floor((Z + off) / length)
    fz = (Z + off) / length - seg
    tone = hash2(col, seg, 7)
    fl = pal_array(FLOOR)
    rgb = fl[2] * (1 - tone[:, None]) + fl[4] * tone[:, None]
    grain = hash2(np.floor(X / 2.0), np.floor(Z / 8.0), 11)
    rgb = rgb * (0.93 + 0.09 * grain[:, None])
    rgb[fx < 0.08] = fl[0]
    rgb[fz < 0.015] = fl[1]
    # the oriental rug, kicked crooked on the left
    rx, rz = X + 150 + (Z - 560) * 0.08, Z - 560
    rug = (np.abs(rx) < 120) & (np.abs(rz) < 90)
    border = rug & ((np.abs(rx) > 108) | (np.abs(rz) > 80))
    motif = rug & ~border & (np.mod(np.floor(rx / 16) + np.floor(rz / 16), 2) == 0)
    rgb[rug] = np.array(C("#5a2a30")[:3])
    rgb[motif] = np.array(C("#7a3a3c")[:3])
    rgb[border] = np.array(C("#2a3a5a")[:3])
    # cups, confetti and glow sticks
    h = hash2(np.floor(X / 10.0), np.floor(Z / 16.0), 13)
    far = Z > 330
    cup = (h > 0.975) & (np.mod(X, 10) < 4) & (np.mod(Z, 16) < 5) & far
    rgb[cup] = np.array(C(CUP[2])[:3])
    conf = hash2(np.floor(X / 2.0), np.floor(Z / 3.0), 17)
    cols = pal_array(["#f06a8a", "#f6cf7a", "#7ad0c8", "#c8a0f0", "#f2f2ee"])
    clump = hash2(np.floor(X / 60.0), np.floor(Z / 70.0), 19) > 0.55        # confetti lies in drifts, not everywhere
    sel = (conf > 0.95) & clump & far
    rgb[sel] = cols[(hash2(np.floor(X / 2.0), np.floor(Z / 3.0), 18)[sel] * 4.99).astype(int)]
    # coloured light: the DJ corner's pink, a cyan pool, the kitchen green at the back, the fire
    warm_light(rgb, np.hypot((X - 230) * 0.9, (Z - 600) * 0.6), 200, colour="#ff6ab4", strength=0.32)
    warm_light(rgb, np.hypot((X + 160) * 0.9, (Z - 420) * 0.8), 150, colour="#4ae0f0", strength=0.22)
    warm_light(rgb, np.hypot((X - 90) * 1.2, (Z - Z_BACK) * 0.5), 160, colour="#6ad8a0", strength=0.22)
    warm_light(rgb, np.hypot((X + 50) * 1.4, (Z - Z_BACK) * 0.6), 120, colour="#ff9a4a", strength=0.2)
    warm_light(rgb, np.hypot(X * 1.0, (Z - 330) * 2.2), 120, colour="#c8a0f0", strength=0.2)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 600, 1000, amount=0.4)
    return out


def ceiling_shader(X, Z):
    rgb = np.tile(np.array(C("#2a2230")[:3], np.float32), (X.shape[0], 1))
    tex = hash2(np.floor(X / 6.0), np.floor(Z / 9.0), 21)
    rgb = rgb * (0.92 + 0.12 * tex[:, None])
    # crown moulding along both walls, a plaster medallion over the disco ball
    edge = np.abs(X) > WALL_X - 18
    rgb[edge] = np.array(C(OAK[3])[:3])
    rgb[(np.abs(X) > WALL_X - 6)] = np.array(C(OAK[5])[:3])
    med = np.hypot(X * 1.0, (Z - 600) * 0.9) < 34
    rgb[med] = np.array(C("#3a3040")[:3])
    rgb[np.abs(np.hypot(X, (Z - 600) * 0.9) - 30) < 2.5] = np.array(C("#4a3e52")[:3])
    warm_light(rgb, np.hypot(X - 230, Z - 640), 240, colour="#ff6ab4", strength=0.25)
    warm_light(rgb, np.hypot(X + 200, Z - 460), 200, colour="#4ae0f0", strength=0.18)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 600, 1000, amount=0.4)
    return out


def silhouette(h=58, cup=False, seed=0, rim="#ff6ab4"):
    """A partygoer seen against the light: head, shoulders, body; a raised cup sometimes."""
    rng = np.random.default_rng(seed)
    w = 26
    cv = Canvas(w + 8, h + 14, seed=seed)
    ox, base = 4, h + 12
    sil = "#0c0a12"
    hw = 9 + int(rng.integers(0, 3))
    hx = ox + w // 2 - hw // 2 + int(rng.integers(-2, 3))
    top = base - h
    cv.ellipse(hx, top, hw, hw + 2, sil)
    if rng.random() < 0.4:                                     # a cap or a bun
        cv.rect(hx - 1, top + 1, hw + 3, 3, sil) if rng.random() < 0.5 else cv.ellipse(hx + 2, top - 3, 6, 5, sil)
    cv.ellipse(ox, top + hw, w, 16, sil)
    cv.poly([(ox + 1, top + hw + 8), (ox + w - 1, top + hw + 8), (ox + w - 4, base), (ox + 4, base)], sil)
    if cup:
        arm_x = ox + w - 2
        cv.rect(arm_x, top - 4, 3, hw + 12, sil)
        cv.rect(arm_x - 1, top - 9, 5, 6, CUP[2]); cv.hline(arm_x - 1, top - 9, 5, CUP[4])
    m = cv.a[..., 3] > 0.5
    edge = m & ~np.roll(m, 1, 1)
    cv.a[edge & (np.arange(cv.h)[:, None] < base - 6)] = C(rim)
    return cv


def build(project):
    out = os.path.join(project, "assets/art/rooms/H02")
    os.makedirs(out, exist_ok=True)
    res = "res://assets/art/rooms/H02/"
    v = View(horizon=98, cam=52, fill="#120c16")
    v.ground(floor_shader)
    v.ground(ceiling_shader, height=CEIL)
    lw = left_wall()
    rwall, tv, L = right_wall()
    for side, tex in ((-1, lw), (1, rwall)):
        def shade_wall(u, Y, Z, tex=tex, side=side):
            tu = u / S if side < 0 else (L - 1) - u / S
            o = texture_lookup(tex, tu, (TEX_H - 1) - Y / S, wrap=False)
            o[..., :3] *= 0.85
            return fog(o, Z, HAZE, 600, 1000, amount=0.4)
        v.plane((side * WALL_X, Z_WALL0), (side * WALL_X, Z_BACK), shade_wall, y_max=CEIL)
    bw, bcx = back_wall()

    def shade_back(X, Y):
        o = texture_lookup(bw, bcx + X / S, (TEX_H - 1) - Y / S, wrap=False)
        return fog(o, np.full(X.shape, Z_BACK), HAZE, 600, 1000, amount=0.4)
    v.back(Z_BACK, shade_back, region=lambda X, Y: (np.abs(X) <= WALL_X) & (Y >= 0) & (Y <= CEIL))

    # furniture and the crowd, far to near
    items = []
    for k, (x, z) in enumerate([(-300, 830), (-262, 810), (300, 830), (262, 790), (-330, 760), (322, 720),
                                (330, 600), (300, 520), (346, 470), (-110, 840), (150, 845), (60, 850)]):
        items.append((z, "sil", (x, k)))
    items += [(640, "dj", (250,)), (660, "spk", (196,)), (650, "spk", (322,)), (700, "pong", (-40,)),
              (780, "couch", (-230,))]
    for z, kind, data in sorted(items, key=lambda t: -t[0]):
        if kind == "sil":
            x, k = data
            spr = silhouette(52 + (k * 7) % 12, cup=(k % 3 == 0), seed=k, rim="#ff6ab4" if x > 0 else "#4ae0f0")
            v.sprite(spr.a, x, z, anchor=(0.5, 1.0), scale=S)
        else:
            maker = {"dj": lambda: dj_table(110, 50, seed=4), "spk": lambda: speaker_stand(30, 66, seed=5),
                     "pong": lambda: pong_table(124, 44, seed=3), "couch": lambda: leather_couch(124, 46, seed=2)}[kind]
            spr, ax, ay = maker()
            v.sprite(spr.a, data[0], z, anchor=(ax / spr.w, ay / spr.h), scale=S)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp: string lights zig-zagging across the ceiling, the disco ball on its chain
    bulbs = []
    for k, (za, zb) in enumerate([(380, 470), (470, 560), (560, 650), (650, 740)]):
        a = v.project(-WALL_X + 10, CEIL - 4, za)
        b = v.project(WALL_X - 10, CEIL - 4, zb)
        if k % 2:
            a, b = (v.project(-WALL_X + 10, CEIL - 4, zb), v.project(WALL_X - 10, CEIL - 4, za))
        bulbs += festoon(cv, int(a[0]), int(a[1]), int(b[0]), int(b[1]), sag=10, every=8, seed=40 + k,
                         colours=["#f6cf7a", "#ff8ad0", "#6ad8f0", "#fff0c4"])
    bx, by = v.project(0, CEIL - 34, 600)
    cx_, cy_ = int(round(bx)), int(round(by))
    top_y = int(v.project(0, CEIL, 600)[1])
    cv.vline(cx_, top_y, cy_ - 6 - top_y, "#3a3848")
    r = 6
    cv.ellipse(cx_ - r - 1, cy_ - r - 1, r * 2 + 3, r * 2 + 3, OUT)
    cv.ellipse(cx_ - r, cy_ - r, r * 2 + 1, r * 2 + 1, "#8a8ea8")
    for yy in range(cy_ - r, cy_ + r + 1, 2):
        for xx in range(cx_ - r, cx_ + r + 1, 2):
            if (xx - cx_) ** 2 + (yy - cy_) ** 2 <= r * r:
                cv.px(xx, yy, "#e6e8f4" if (xx + yy) % 4 == 0 else "#5a5e78" if xx > cx_ else "#b8bcd0")
    sparkle_ball = [[cx_ - 2, cy_ - 3, "ffffff", 1], [cx_ + 2, cy_ - 1, "ffffff", 1], [cx_ - 3, cy_ + 2, "ffffff", 1]]
    rng = np.random.default_rng(9)
    sparkles = []
    for _ in range(70):
        x, y = int(rng.integers(0, 640)), int(rng.integers(0, 160))
        sparkles.append([x, y, ["ffd0ec", "c8f4ff", "fff0c4"][int(rng.integers(3))], 2])
    cv.save(os.path.join(out, "battle-far.png"))

    # the TV on the right wall: project its screen to a quad's bounding box for the bouncing bars
    tx, ty, tw, th = tv

    def wall_pt(u_tex, v_tex):
        u = (L - 1 - u_tex) * S
        return v.project(WALL_X, (TEX_H - 1 - v_tex) * S, Z_WALL0 + u)
    p0, p1 = wall_pt(tx, ty), wall_pt(tx + tw, ty + th)
    sx0, sx1 = int(min(p0[0], p1[0])), int(max(p0[0], p1[0]))
    sy0, sy1 = int(min(p0[1], p1[1])), int(max(p0[1], p1[1]))
    bars = []
    nb = max(3, (sx1 - sx0) // 4)
    for f in range(4):
        rects = []
        for k in range(nb):
            bh = int(3 + (sy1 - sy0 - 5) * abs(np.sin(f * 1.3 + k * 0.9)))
            rects.append([sx0 + 1 + k * 4, sy1 - 2 - bh, 3, bh, ["ff6ab4", "a07aff", "4ae0f0"][k % 3], 1.0])
        bars.append({"kind": "blink", "pattern": "".join("1" if j == f else "0" for j in range(4)), "rate": 5.0, "rects": rects})
    layers = bars + [
        {"kind": "beam", "x": cx_, "y": cy_, "angle": 118, "sweep": 26, "period": 6.0, "phase": 0.0,
         "length": 140, "width": 54, "color": "ff6ab4", "alpha": 0.2, "floor": 150},
        {"kind": "beam", "x": cx_, "y": cy_, "angle": 62, "sweep": 26, "period": 7.5, "phase": 2.0,
         "length": 140, "width": 54, "color": "4ae0f0", "alpha": 0.18, "floor": 150},
        {"kind": "beam", "x": cx_, "y": cy_, "angle": 90, "sweep": 40, "period": 4.5, "phase": 1.0,
         "length": 110, "width": 36, "color": "a07aff", "alpha": 0.14, "floor": 140},
        {"kind": "twinkle", "points": bulbs, "rate": 2.2, "min": 0.35},
        {"kind": "twinkle", "points": sparkle_ball, "rate": 5.0, "min": 0.0},
        {"kind": "twinkle", "points": sparkles, "rate": 2.6, "min": 0.0},
        {"kind": "particles", "style": "dust", "count": 30, "rect": [20, 10, 600, 150], "speed": [0, 5], "color": "ffd0ec"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:200])
