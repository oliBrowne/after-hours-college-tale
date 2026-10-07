"""Battle backdrop for the club room: the fight happens on the dance floor in front of the stage.
Polished planks run toward the stage, velvet curtains frame a painted night sky, a truss of lamps
throws sweeping spotlights, string lights hang across the hall."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, shade, mix, text, text_width
from interior import (PLASTER, PANEL, FLOOR, VELVET, NIGHT, plaster, crown, wainscot, poster, curtain, valance,
                      pa_speaker)
from props import OUT, IRON, AMBER
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

INK = "#10121e"
Z_STAGE = 640.0
WALL_X = 420.0
HALL_H = 250.0


def floor_shader(X, Z):
    """Planks laid toward the stage, waxed, catching the stage light."""
    n = X.shape[0]
    plank = 15.0
    col = np.floor(X / plank)
    fx = X / plank - col
    length = 110 + 60 * hash2(col, 3)
    off = hash2(col, 5) * length
    seg = np.floor((Z + off) / length)
    fz = (Z + off) / length - seg
    tone = hash2(col, seg, 7)
    fl = pal_array(FLOOR)
    rgb = fl[2] * (1 - tone[:, None]) + fl[4] * tone[:, None]
    grain = hash2(np.floor(X / 2.0), np.floor(Z / 9.0), 11)
    rgb = rgb * (0.94 + 0.08 * grain[:, None])
    rgb[fx < 0.08] = fl[0]
    rgb[(fz < 0.012)] = fl[1]
    # The stage glow reflected on the wax: long streaks under the bright parts of the stage.
    for (lx, strength) in [(-150, 0.35), (0, 0.55), (150, 0.35)]:
        warm_light(rgb, np.hypot((X - lx) * 2.2, (Z - Z_STAGE) * 0.22), 130, colour="#f6c27a", strength=strength)
    # Spotlight pools where the fighters stand.
    warm_light(rgb, np.hypot(X + 200, (Z - 330) * 2.5), 70, colour="#fff0c4", strength=0.3)
    warm_light(rgb, np.hypot(X - 170, (Z - 330) * 2.5), 70, colour="#f2b0d0", strength=0.26)
    out = rgba_of(rgb)
    fog(out, Z, "#2a1a26", 600, 900, amount=0.5)
    return out


def wall_texture(length, height, seed=0):
    """The hall's side wall, laid out along its length (u = distance toward the stage)."""
    cv = Canvas(length, height, seed=seed)
    plaster(cv, 0, 0, length, height, seed=seed)
    wy = height - 72
    crown(cv, 0, 0, length)
    wainscot(cv, 0, wy, length, 72, seed=seed)
    rng = np.random.default_rng(seed)
    # posters and a lit sconce between them
    x = 18
    for i in range(3):
        w, h = int(rng.integers(28, 40)), int(rng.integers(40, 54))
        base = ["#c84a3c", "#425da6", "#e8b45c", "#5c897c"][int(rng.integers(4))]
        poster(cv, x, wy - h - 22, w, h, base, title=["GIG", "OPEN", "LATE"][i], seed=seed + i)
        sx = x + w + 18
        cv.rect(sx - 3, wy - 66, 7, 10, OUT); cv.rect(sx - 2, wy - 65, 5, 8, AMBER[3]); cv.rect(sx - 1, wy - 64, 3, 4, AMBER[4])
        for r, a in [(22, 0.1), (14, 0.12), (8, 0.14)]:
            cv.ellipse(sx - r, wy - 61 - r, r * 2, r * 2, C(AMBER[3], a))
        x = sx + 22
    return cv.a


def stage_flat():
    """The stage end of the hall painted at its on-screen size (depth Z_STAGE, scale 0.5)."""
    W, H = 420, 128
    cv = Canvas(W, H, seed=8)
    deck = 106  # stage front top edge (canvas row); the floor line is the last row
    # Hall end wall around the proscenium.
    plaster(cv, 0, 0, W, H, seed=8)
    cv.rect(0, 0, W, H, C("#0d0b16", 0.35))
    # Backdrop cloth: night sky, moon, Flatirons, campus roofline.
    bx0, bx1, by0 = 74, 346, 22
    cv.dither_v(bx0, by0, bx1 - bx0, deck - by0, "#0b0f22", "#2c3a6c", steps=6)
    rng = np.random.default_rng(3)
    stars = []
    for _ in range(70):
        sx, sy = int(rng.integers(bx0 + 2, bx1 - 2)), int(rng.integers(by0 + 14, deck - 50))
        cv.px(sx, sy, "#c8d0f0" if rng.random() < 0.5 else "#8a96c8")
        if rng.random() < 0.15:
            stars.append((sx, sy))
    mx, my = 262, 46
    for r, c in [(17, C("#f6e7c4", 0.08)), (13, C("#f6e7c4", 0.12))]:
        cv.ellipse(mx - r, my - r, r * 2, r * 2, c)
    cv.ellipse(mx - 9, my - 9, 18, 18, "#f6e7c4")
    cv.ellipse(mx - 4, my - 9, 15, 16, "#2a3666")
    cv.ellipse(mx - 9, my - 9, 18, 18, C("#f6e7c4", 0.0))
    # mountains: three slab silhouettes, lit edges
    for (px, pw, ph, c) in [(120, 90, 46, "#3b3460"), (176, 70, 54, "#463c6c"), (228, 80, 40, "#3b3460")]:
        cv.poly([(px - pw // 2, deck - 18), (px, deck - 18 - ph), (px + pw // 2, deck - 18)], c)
        cv.line(px, deck - 18 - ph, px + pw // 3, deck - 18 - ph // 3, "#7a6a9c")
    cv.dither_v(bx0, deck - 30, bx1 - bx0, 12, "#1e1a38", "#141226", steps=3)
    for x in range(bx0, bx1, 7):
        h = int(rng.integers(4, 11))
        cv.rect(x, deck - 18 - h, 7, h + 2, "#141226")
        if rng.random() < 0.5:
            cv.px(x + 2, deck - 15 - h // 2, "#e9a84a")
    cv.rect(bx0, deck - 18, bx1 - bx0, 18, "#141226")
    # Curtains gathered to the sides, the valance across the top.
    curtain(cv, 50, by0 - 2, 48, deck - by0 + 2, flip=False, seed=1)
    curtain(cv, 322, by0 - 2, 48, deck - by0 + 2, flip=True, seed=2)
    for x0, x1 in [(36, 52), (368, 384)]:
        cv.rect(x0, 0, x1 - x0, deck, PANEL[2]); cv.vline(x0, 0, deck, PANEL[4]); cv.vline(x1 - 1, 0, deck, PANEL[0])
    valance(cv, 40, 8, 340)
    cv.rect(40, 0, 340, 9, VELVET[2]); cv.hline(40, 8, 340, VELVET[4])
    # Truss with four cans.
    cv.rect(44, 2, 332, 3, IRON[1]); cv.hline(44, 2, 332, IRON[3])
    cans = []
    for cx in (96, 168, 252, 324):
        cv.rect(cx - 4, 4, 9, 8, OUT); cv.rect(cx - 3, 5, 7, 5, IRON[2]); cv.rect(cx - 2, 10, 5, 2, AMBER[4])
        cans.append((cx, 12))
    # LAST LIGHT marquee hanging in front of the cloth.
    sign = "LAST LIGHT"
    sw = text_width(sign) + 18
    sx0, sy0 = 210 - sw // 2, 28
    cv.vline(sx0 + 6, 9, sy0 - 9, IRON[2]); cv.vline(sx0 + sw - 7, 9, sy0 - 9, IRON[2])
    cv.rect(sx0, sy0, sw, 17, OUT); cv.rect(sx0 + 1, sy0 + 1, sw - 2, 15, "#3a1420")
    text(cv, sign, sx0 + 9, sy0 + 3, "#f6cd78")
    bulbs = []
    for bx in range(sx0 + 2, sx0 + sw - 1, 4):
        bulbs.append((bx, sy0 + 1)); bulbs.append((bx, sy0 + 15))
    for (bx, by) in bulbs:
        cv.px(bx, by, "#7a4a24")
    # On stage: mic stand, stool, amp, a guitar on its stand, monitor wedges.
    cv.rect(0, deck - 2, W, 2, C("#0d0b16", 0.4))
    cv.vline(210, deck - 34, 32, IRON[3]); cv.vline(211, deck - 34, 32, IRON[1])
    cv.rect(207, deck - 37, 5, 4, IRON[4]); cv.rect(208, deck - 36, 3, 2, "#c0c4cc")
    cv.line(204, deck - 2, 210, deck - 6, IRON[2]); cv.line(217, deck - 2, 211, deck - 6, IRON[2])
    cv.rect(176, deck - 18, 12, 3, PANEL[4]); cv.vline(178, deck - 15, 13, IRON[2]); cv.vline(186, deck - 15, 13, IRON[2])
    cv.rect(244, deck - 16, 22, 15, OUT); cv.rect(245, deck - 15, 20, 13, "#2a2838"); cv.rect(246, deck - 14, 18, 3, "#4d4b66")
    for k in range(4):
        cv.px(248 + k * 4, deck - 13, "#e8b45c")
    cv.rect(246, deck - 10, 18, 7, "#16141f")
    gx = 292
    cv.ellipse(gx - 5, deck - 18, 11, 12, "#a83c32"); cv.ellipse(gx - 3, deck - 22, 7, 8, "#c84a3c")
    cv.ellipse(gx - 1, deck - 15, 3, 3, "#16141f"); cv.rect(gx, deck - 38, 2, 18, "#6b3f2e"); cv.rect(gx - 1, deck - 41, 4, 4, OUT)
    cv.line(gx - 4, deck - 2, gx, deck - 8, IRON[2]); cv.line(gx + 5, deck - 2, gx + 1, deck - 8, IRON[2])
    for wx in (130, 290):
        cv.poly([(wx - 12, deck - 1), (wx - 9, deck - 9), (wx + 9, deck - 9), (wx + 12, deck - 1)], OUT)
        cv.poly([(wx - 10, deck - 2), (wx - 8, deck - 8), (wx + 8, deck - 8), (wx + 10, deck - 2)], "#24222f")
    # Stage deck and front skirt with footlights.
    cv.rect(36, deck - 1, 348, 3, PANEL[4]); cv.hline(36, deck - 1, 348, PANEL[5])
    cv.rect(36, deck + 2, 348, H - deck - 2, "#1f1720")
    for sx in range(38, 382, 4):
        cv.vline(sx, deck + 3, H - deck - 4, "#2a2029")
    foot = []
    for lx in range(58, 372, 26):
        cv.rect(lx - 3, deck + 3, 7, 4, OUT); cv.rect(lx - 2, deck + 4, 5, 2, AMBER[3])
        foot.append((lx, deck + 4))
    cv.hline(36, H - 1, 348, C("#0d0b16", 0.7))
    # Side wings beyond the proscenium: dark hall wall with exit signs.
    for x0 in (0, 384):
        cv.rect(x0, deck, 36, H - deck, PANEL[1])
    for ex in (14, 402):
        cv.rect(ex - 7, 40, 14, 6, OUT); cv.rect(ex - 6, 41, 12, 4, "#3cba7a")
    return cv, cans, bulbs, foot, stars, (mx, my)


def string_lights_crisp(cv, x0, y0, x1, y1, sag, every, seed):
    rng = np.random.default_rng(seed)
    pts = []
    n = int(abs(x1 - x0))
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        cv.px(int(round(x)), int(round(y)), "#1a1418")
        if i % every == every // 2:
            c = AMBER[3] if rng.random() < 0.7 else "#f2a0a0"
            px_, py_ = int(round(x)), int(round(y))
            cv.px(px_, py_ + 1, c); cv.px(px_, py_ + 2, shade(c, 0.3))
            pts.append([px_, py_ + 2, c.lstrip("#"), 1])
    return pts


def build(project):
    out = os.path.join(project, "assets/art/rooms/U04")
    v = View(horizon=98, cam=52, fill="#120c16")
    v.ground(floor_shader)
    for side in (-1, 1):
        L = int(Z_STAGE - 300)
        tex = wall_texture(L, int(HALL_H), seed=side + 3)
        if side > 0:
            tex = tex[:, ::-1].copy()  # seen from inside, the right wall runs right-to-left
        def shade_wall(u, Y, Z, tex=tex, side=side, L=L):
            o = texture_lookup(tex, u if side < 0 else L - 1 - u, HALL_H - Y, wrap=False)
            o[..., :3] *= 0.82
            return o
        v.plane((side * WALL_X, 300.0), (side * WALL_X, Z_STAGE), shade_wall, y_max=HALL_H)
    flat, cans, bulbs, foot, stars, moon = stage_flat()
    s = v.scale(Z_STAGE)
    fx0 = int(round(v.vx - flat.w / 2))
    fy0 = int(round(v.ground_y(Z_STAGE) - flat.h))
    v.strip(flat.a, fy0, fx0)
    # PA stacks on the floor at both ends of the stage.
    for x in (-250, 250):
        spr, ax, ay = pa_speaker(int(37 * 1.7 * v.scale(560)), int(66 * 1.7 * v.scale(560)))
        v.sprite(spr.a, x, 560, anchor=(ax / spr.w, ay / spr.h), scale=560 / v.F)
    v.rows(156, 360, INK, 0.0, 0.66)
    cv = v.reduce(112)
    lights = string_lights_crisp(cv, -10, 6, 650, 4, 22, 13, seed=4)
    lights += string_lights_crisp(cv, -10, 24, 300, 30, 14, 11, seed=5)
    lights += string_lights_crisp(cv, 340, 30, 650, 22, 14, 11, seed=6)
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    res = "res://assets/art/rooms/U04/"
    to_screen = lambda p: [fx0 + p[0], fy0 + p[1]]
    can_pts = [to_screen(c) for c in cans]
    beams = [
        {"kind": "beam", "x": can_pts[0][0], "y": can_pts[0][1], "angle": 112, "sweep": 14, "period": 7.0, "phase": 0.0,
         "length": 150, "width": 62, "color": "fff0c4", "alpha": 0.3, "floor": 150},
        {"kind": "beam", "x": can_pts[3][0], "y": can_pts[3][1], "angle": 66, "sweep": 14, "period": 8.5, "phase": 1.7,
         "length": 150, "width": 62, "color": "f2b0d0", "alpha": 0.27, "floor": 150},
        {"kind": "beam", "x": can_pts[1][0], "y": can_pts[1][1], "angle": 96, "sweep": 22, "period": 5.5, "phase": 3.1,
         "length": 120, "width": 40, "color": "a8e0d8", "alpha": 0.18, "floor": 142},
    ]
    marquee = [to_screen(b) for b in bulbs]
    chase = [{"kind": "blink", "pattern": "".join("1" if (k == j) else "0" for k in range(3)), "rate": 6.0,
              "rects": [[p[0], p[1], 1, 1, "fff0c4"] for i, p in enumerate(marquee) if (i // 2) % 3 == j]} for j in range(3)]
    return {
        "far": res + "battle-far.png",
        "layers": beams + chase + [
            {"kind": "twinkle", "points": lights, "rate": 2.2, "min": 0.35},
            {"kind": "twinkle", "points": [to_screen(f) + ["f6cf7a", 1] for f in foot], "rate": 1.1, "min": 0.6},
            {"kind": "twinkle", "points": [to_screen(st) + ["c8d0f0", 1] for st in stars], "rate": 1.6, "min": 0.0},
            {"kind": "particles", "style": "dust", "count": 26, "rect": [60, 20, 520, 130], "speed": [0, 4], "color": "fff0c4"},
        ],
    }


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:200])
