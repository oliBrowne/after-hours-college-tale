"""Procession walk (M01): the last walk to Macky, where no one has to march.

Top of the room: Macky's east front at character scale - the gabled entrance block with its
three round-arched doors (the middle one open on the warm lobby), MACKY AUDITORIUM carved over
them, the hall windows lit, the twin sandstone towers rising out of frame under crimson autumn
ivy, the lower wings either side. Beyond: the night sky over the Flatirons (left) and the campus
(right). At dawn (background-dawn.png) the sky turns rose and gold, the Flatirons catch the first
sun, the tower tops warm and the windows go out.
The ground: lawns, and the procession route in CU's random sandstone flags - in from the Old Main
courtyard on the left, along the walk, then up the avenue to the steps - with a minor flagged path
off to the balcony service stair on the right. The avenue is stencilled RESERVED and taped into
seat boxes all the way down, the reservation eating the actual pavement; chalk on the walk says
NO ONE HAS TO MARCH.
Props: two autumn oaks, the long bench, the RESERVED easel, the commencement lamp."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from scipy import ndimage
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool, LEAVES
from props import OUT, IRON, LEAF, MUM, shrub, grass_tuft, ground_shadow
from midlib import sprite_from_cell
from lib_norlin import lawn, crazy_paving, kerb, stone_steps, flag_path, paving, GRASS, PAVE_N, LIME, STONE_N
from lib_macky import (macky_front, night_sky_m, dawn_sky_m, dawn_clouds, flatirons_m, treeline_m, procession_lamp,
                       long_bench, reserved_notice, tape_box, stencil_text, rough_ashlar, dressed_band, hexmix, DRESS,
                       MSTONE, SHADOW, CU_GOLD)

ROOM = "M01"
W, H = 960, 540
BASE = 140                 # door sill of Macky's front
CX = 511                   # centre door (the lobby threshold is at x 510)
WALK = (20, 142, 920, 374)
HORIZON = 118              # treeline foot either side of the building
STEPS = (BASE, 7, 6)       # top row, count, rise
PLAZA = (372, 176, 650, 246)
AVENUE = (452, 570, 240, 470)
PROCESSION = (0, 570, 418, 470)
BAY = (290, 378, 470, 422)
SERVICE = (568, 960, 336, 366)
LAMP = (190, 409)
TREES = [(155, 260), (815, 280)]
BIRDS = (780, 265)
GRASS_DAWN = ["#22301e", "#2c3e24", "#36492a", "#425732", "#52683c", "#647a46", "#7a8c52"]
PAVE_DAWN = ["#4a3a3c", "#6a5652", "#7c665e", "#8a7266", "#967c6e", "#a48a7a"]


def rounded_rect(xs, ys, x0, y0, x1, y1, r):
    m = (xs >= x0) & (xs < x1) & (ys >= y0) & (ys < y1)
    for (cx, cy) in [(x0 + r, y0 + r), (x1 - r, y0 + r), (x0 + r, y1 - r), (x1 - r, y1 - r)]:
        corner = (np.abs(xs - cx) <= r) & (np.abs(ys - cy) <= r) & ((xs < x0 + r) | (xs >= x1 - r)) & ((ys < y0 + r) | (ys >= y1 - r))
        m &= ~corner | ((xs - cx) ** 2 + (ys - cy) ** 2 <= r * r)
    return m


def masks():
    ys, xs = np.mgrid[0:H, 0:W]
    ground = (ys >= BASE + 2) & (ys < 516)
    plaza = rounded_rect(xs, ys, *PLAZA, 14)
    ax0, ax1, ay0, ay1 = AVENUE
    avenue = (xs >= ax0) & (xs < ax1) & (ys >= ay0 - 10) & (ys < ay1)
    px0, px1, py0, py1 = PROCESSION
    walk = (xs >= px0) & (xs < px1) & (ys >= py0) & (ys < py1)
    # round the inside corner where the walk turns up the avenue
    inner = (xs < ax0) & (xs >= ax0 - 14) & (ys < py0) & (ys >= py0 - 14) & ((xs - (ax0 - 14)) ** 2 + (ys - (py0 - 14)) ** 2 > 14 * 14)
    walk |= inner
    bay = rounded_rect(xs, ys, *BAY, 8)
    lamp_pad = ((xs - LAMP[0]) / 18.0) ** 2 + ((ys - LAMP[1] - 4) / 8.0) ** 2 <= 1
    route = ground & (plaza | avenue | walk | bay | lamp_pad)
    sx0, sx1, sy0, sy1 = SERVICE
    service = ground & (xs >= sx0) & (ys >= sy0) & (ys < sy1) & ~route
    lawns = ground & ~route & ~service
    return route, plaza, service, lawns


def back(bg, dawn):
    """Sky, mountains, campus and the back hedge either side of the building."""
    if dawn:
        # looking west at sunrise: the sun is behind us, the belt of Venus glows pink over the
        # mountains and the clouds are lit from below
        dawn_sky_m(bg, 0, 0, W, HORIZON + 4, seed=3)
        dawn_clouds(bg, 0, 6, W, 76, seed=4, count=12)
        stars = []
    else:
        stars = night_sky_m(bg, 0, 0, W, HORIZON + 4, seed=3, stars=170, star_h=70)
        # the moon going down in the west, over the mountains
        mx, my = 120, 34
        for rr, a in [(20, 0.05), (13, 0.08), (9, 0.1)]:
            bg.ellipse(mx - rr, my - rr, rr * 2 + 1, rr * 2 + 1, C("#efe2b8", a))
        bg.ellipse(mx - 6, my - 6, 13, 13, "#efe2b8"); bg.ellipse(mx - 3, my - 7, 12, 12, "#1a1c40")
    flatirons_m(bg, -16, 250, HORIZON - 2, seed=5, dawn=dawn, tall=1.05)
    lights = treeline_m(bg, -10, 240, HORIZON + 4, seed=6, dawn=dawn)
    lights += treeline_m(bg, 780, W + 10, HORIZON + 4, seed=7, dawn=dawn)
    # sandstone garden wall with a hedge, either side of Macky
    rng = np.random.default_rng(9)
    for x0, x1 in [(0, 226), (796, W)]:
        for x in range(x0 - 8, x1, 15):
            sw, sh = int(rng.integers(18, 28)), int(rng.integers(12, 18))
            bg.paste(shrub(0, 0, sw, sh, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.2 else None), x, HORIZON + 10 - sh)
        rough_ashlar(bg, x0, HORIZON + 8, x1 - x0, BASE - HORIZON - 6, seed=x0 + 1, courses=(6, 7))
        dressed_band(bg, x0, HORIZON + 6, x1 - x0, 3, seed=x0)
    return stars, lights


def uplights(bg, towers):
    """Floodlights at the foot of each tower wash the stone in stepped warm wedges (night)."""
    for (t0, t1) in towers:
        cx = (t0 + t1) // 2
        for k, (spread, top, a) in enumerate([(40, 10, 0.05), (30, 40, 0.06), (20, 80, 0.07)]):
            bg.poly([(cx - 5, BASE - 4), (cx - spread, top), (cx + spread, top), (cx + 5, BASE - 4)], C("#f6cf7a", a))
        bg.rect(cx - 4, BASE - 4, 9, 4, OUT); bg.rect(cx - 3, BASE - 4, 7, 2, "#fff0c4")


def ground(bg, dawn):
    route, plaza, service, lawns = masks()
    lawn(bg, 0, BASE + 2, W, 516 - BASE - 2, seed=11, pal=GRASS_DAWN if dawn else GRASS, mask=lawns)
    pave = PAVE_DAWN if dawn else PAVE_N
    crazy_paving(bg, route, pal=pave, seed=12, cell=(18, 10), moss=0.08, grow=0.4)
    # a dressed sandstone ring set in the plaza where processions used to form up
    for (rx, ry, col) in [(52, 14, DRESS[2]), (50, 13, DRESS[4]), (46, 12, None), (30, 8, DRESS[3]), (28, 7, None)]:
        if col:
            bg.ellipse(CX - rx, 214 - ry, rx * 2 + 1, ry * 2 + 1, col)
        else:
            sub = Canvas(rx * 2 + 1, ry * 2 + 1)
            sub.ellipse(0, 0, rx * 2 + 1, ry * 2 + 1, "#ffffff")
            m = np.zeros((H, W), bool)
            m[214 - ry:214 + ry + 1, CX - rx:CX + rx + 1] = sub.a[..., 3] > 0.5
            crazy_paving(bg, m, pal=pave, seed=rx, cell=(12, 7), moss=0.0, grow=0.0)
    for k in range(8):
        a = k * np.pi / 4
        bg.line(int(CX + np.cos(a) * 30), int(214 + np.sin(a) * 8), int(CX + np.cos(a) * 46), int(214 + np.sin(a) * 12), DRESS[3])
    flag_path(bg, service, pal=STONE_N, seed=14, row=7)
    kerb(bg, route, light=LIME[3] if not dawn else LIME[4])
    kerb(bg, service, light=LIME[2])
    # the steps up to the doors, and a dressed apron at their foot
    stone_steps(bg, CX, STEPS[0], 200, STEPS[1], rise=STEPS[2], spread=4, pal=DRESS)
    return route, plaza, service, lawns


def reservation(bg, dawn):
    """RESERVED stencilled across the avenue, seat boxes taped down the rest of it."""
    ax0, ax1, ay0, ay1 = AVENUE
    paint = "#e6dcc4"
    stencil_text(bg, "RESERVED", (ax0 + ax1) // 2 - 48, 262, paint, scale=2, alpha=0.62, worn=0.12, seed=1)
    text(bg, "EVERY FUTURE", (ax0 + ax1) // 2 - text_width("EVERY FUTURE") // 2, 284, C(paint, 0.5))
    tape = CU_GOLD[3]
    k = 0
    for row, ty in enumerate(range(304, 404, 24)):
        for tx in (ax0 + 6, ax0 + 62):
            tape_box(bg, tx, ty, 50, 18, colour=tape, seed=k, worn=0.12 + 0.05 * row)
            # a tent card in every box: a name for someone who isn't here
            cx = tx + 25
            bg.rect(cx - 4, ty + 6, 9, 5, "#2a2026"); bg.rect(cx - 4, ty + 5, 9, 4, "#f2e8d0"); bg.hline(cx - 3, ty + 7, 7, "#b8a888")
            k += 1
    # the creep: boxes taped across the walk too, one half peeled back
    for (tx, ty) in [(352, 430), (408, 444)]:
        tape_box(bg, tx, ty, 46, 16, colour=tape, seed=k, worn=0.3)
        k += 1
    # chalk, in someone's hand: no one has to march
    chalk = C("#d8dcea", 0.55)
    text(bg, "NO ONE HAS TO MARCH", 116, 450, chalk)
    bg.line(116, 460, 228, 461, C("#d8dcea", 0.35))
    for i, (hx, hy) in enumerate([(236, 451), (240, 451)]):
        bg.px(hx, hy, chalk); bg.px(hx + 1, hy + 1, chalk)
    bg.px(238, 453, chalk); bg.px(237, 452, chalk); bg.px(239, 452, chalk)


def stakes(bg, lawns):
    """Rows of little RESERVED cards on stakes pushed into the lawns, laid out like seating for
    a crowd that never comes - the reservation spreading off the paving onto the grass."""
    rng = np.random.default_rng(17)
    rows = [(176, 330, 410, 14), (206, 300, 420, 15), (238, 270, 428, 16), (272, 240, 432, 17), (308, 210, 436, 18),
            (346, 250, 436, 19)]
    for (y, x0, x1, step) in rows:
        for x in range(x0, x1, step):
            x_ = x + int(rng.integers(-1, 2))
            if not lawns[y, x_] or not lawns[y - 8, x_] or rng.random() < 0.08:
                continue
            bg.vline(x_, y - 6, 6, "#6a5a4a"); bg.px(x_ + 1, y - 1, C(SHADOW, 0.4))
            bg.rect(x_ - 2, y - 9, 5, 4, "#efe4cc"); bg.hline(x_ - 2, y - 6, 5, "#a89a86"); bg.px(x_ - 1, y - 8, "#c84a3c")
    for (y, x0, x1, step) in [(392, 610, 900, 22), (430, 640, 910, 22), (470, 600, 900, 24)]:
        for x in range(x0, x1, step):
            x_ = x + int(rng.integers(-2, 3))
            if not lawns[y, x_] or not lawns[y - 8, x_] or rng.random() < 0.35:
                continue
            bg.vline(x_, y - 6, 6, "#6a5a4a"); bg.px(x_ + 1, y - 1, C(SHADOW, 0.4))
            bg.rect(x_ - 2, y - 9, 5, 4, "#efe4cc"); bg.hline(x_ - 2, y - 6, 5, "#a89a86"); bg.px(x_ - 1, y - 8, "#c84a3c")


def litter(bg, lawns, route, dawn):
    """Leaves under the oaks and along the kerbs; confetti and a program from a procession that
    did not happen."""
    rng = np.random.default_rng(21)
    for (tx, ty) in TREES:
        for _ in range(260):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, 30))
            lx, ly = int(tx + np.cos(a) * d * 1.4), int(ty + 4 + np.sin(a) * d * 0.5)
            if 0 <= lx < W - 1 and BASE + 2 <= ly < 516:
                c = LEAVES[int(rng.integers(len(LEAVES)))]
                bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
    edge = route & ~ndimage.binary_erosion(route, iterations=3)
    ys, xs = np.where(edge)
    for i in rng.choice(len(ys), 90, replace=False):
        c = LEAVES[int(rng.integers(len(LEAVES)))]
        bg.px(xs[i], ys[i], c)
    for _ in range(40):
        x, y = int(rng.integers(300, 600)), int(rng.integers(180, 470))
        if route[y, x]:
            bg.px(x, y, [CU_GOLD[3], "#1a1418", "#e6d6b1"][int(rng.integers(3))])
    # a dropped commencement program
    bg.rect(526, 452, 10, 7, "#2a2026"); bg.rect(526, 451, 10, 7, "#efe4cc"); bg.rect(527, 452, 8, 2, CU_GOLD[3]); bg.hline(527, 455, 7, "#a89a86")


def margins(bg):
    """Hedges along the left, right and bottom edges; sandstone piers where the paths leave."""
    rng = np.random.default_rng(31)
    bg.rect(0, 516, W, H - 516, "#141a18")
    dressed_band(bg, 0, 514, W, 3, seed=2)
    for x in range(-6, W, 14):
        sw, sh = int(rng.integers(16, 26)), int(rng.integers(12, 18))
        bg.paste(shrub(0, 0, sw, sh, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None), x, 519 + int(rng.integers(0, 5)))
    for (x0, gaps) in [(0, [(PROCESSION[2] - 4, PROCESSION[3] + 4)]), (W - 18, [(SERVICE[2] - 4, SERVICE[3] + 4)])]:
        y = BASE + 4
        while y < 516:
            if any(g0 <= y + 10 and y < g1 for g0, g1 in gaps):
                y += 4
                continue
            sh = int(rng.integers(14, 22))
            bg.paste(shrub(0, 0, 20, sh, seed=int(rng.integers(1e6))), x0 - 2, y)
            y += sh - 4
        for (g0, g1) in gaps:
            for py_ in (g0 - 14, g1 - 4):
                bg.rect(x0 + 2, py_, 14, 18, OUT); bg.rect(x0 + 3, py_ + 1, 12, 16, MSTONE[5]); bg.vline(x0 + 3, py_ + 1, 16, MSTONE[7])
                bg.rect(x0 + 1, py_ - 2, 16, 4, DRESS[4]); bg.hline(x0 + 1, py_ - 2, 16, DRESS[6])


def paint(dawn):
    bg = Canvas(W, H, fill="#171a2b", seed=8)
    stars, lights = back(bg, dawn)
    route, plaza, service, lawns = ground(bg, dawn)
    before = bg.a.copy()
    flights, parts = macky_front(bg, CX, BASE, tower_top=-120, dawn=dawn, seed=4)
    lights += flights
    if dawn:
        # first sun on the upper storeys: two stepped warm bands down the stone
        built = np.any(np.abs(bg.a - before) > 0.01, axis=2)
        for (y0, y1, a) in [(0, 46, 0.34), (46, 72, 0.18)]:
            reg = bg.a[y0:y1]
            m = built[y0:y1]
            warm = reg[..., :3] * 0.6 + np.array(C("#f8b878")[:3]) * 0.4
            reg[m, :3] = reg[m, :3] * (1 - a) + warm[m] * a
    # planting along the foot of the wings, in front of the plinth
    rng = np.random.default_rng(41)
    for (w0, w1) in list(parts["wings"]) + [(parts["left_tower"][0], parts["block"][0] - 6), (parts["block"][1] + 6, parts["right_tower"][1])]:
        x = w0
        while x < w1 - 10:
            sw, sh = int(rng.integers(16, 24)), int(rng.integers(10, 15))
            bg.paste(shrub(0, 0, sw, sh, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.25 else None), x, BASE + 4 - sh)
            x += sw - 4
    if not dawn:
        uplights(bg, [parts["left_tower"], parts["right_tower"]])
    reservation(bg, dawn)
    stakes(bg, lawns)
    litter(bg, lawns, route, dawn)
    margins(bg)
    # light on the ground: the open door's spill down the steps, the lanterns, the lamp
    if not dawn:
        light_pool(bg, CX, 176, 70, 16, strength=0.26)
        for lx in (CX - 29, CX + 29):
            light_pool(bg, lx, 150, 22, 6, strength=0.14)
        light_pool(bg, LAMP[0], LAMP[1] + 2, 50, 14, strength=0.24)
    else:
        light_pool(bg, CX, 176, 56, 12, color="#f6dcae", strength=0.1)
    # dark rim outside the walkable area at the bottom
    bg.rect(0, 516, W, H - 516, C(SHADOW, 0.3))
    return bg, stars, lights


def tree(seed, flip=False, tint=None, height=132):
    spr = sprite_from_cell(5, height=height, colors=40)
    if flip:
        spr = spr[:, ::-1].copy()
    if tint is not None:
        spr = spr.copy(); spr[..., :3] = np.clip(spr[..., :3] * np.array(tint), 0, 1)
    h, w = spr.shape[:2]
    cv = Canvas(w, h + 3, seed=seed)
    ground_shadow(cv, w // 2, h, w // 3, 3)
    cv.paste(spr, 0, 0)
    return cv, w // 2, h


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    night, stars, lights = paint(False)
    night.save(os.path.join(out, "background.png"))
    day, _, _ = paint(True)
    day.save(os.path.join(out, "background-dawn.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(0, tree(1))
    save(1, tree(2, flip=True, tint=(1.04, 0.98, 0.9), height=128))
    save(2, long_bench(140, 32))
    save(3, reserved_notice(84, 60))
    procession_lamp(68, dawn=True)[0].save(os.path.join(out, "prop-4-dawn.png"))
    save(4, procession_lamp(68), {"flag": "dawn_started", "flag_texture": f"res://assets/art/rooms/{ROOM}/prop-4-dawn.png"})

    res = f"res://assets/art/rooms/{ROOM}/"
    rng = np.random.default_rng(5)
    star_pts = [[int(x), int(y), "e8e4ff", 1] for (x, y) in stars if rng.random() < 0.25]
    glow = [[int(x), int(y), "f6cf7a", 1] for (x, y) in lights]
    glow.append([LAMP[0] - 1 + 1, LAMP[1] - 63, "fff0c4", 2])
    bx, by = BIRDS
    manifest = {
        "background": res + "background.png",
        "background_dawn": res + "background-dawn.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "fauna": [
            # birds waiting for morning on the lawn by the right-hand oak
            {"kind": "macky_sparrow", "x": bx - 34, "y": by + 16, "range": 2, "speed": 0.4, "rate": 1.1},
            {"kind": "macky_sparrow", "x": bx - 22, "y": by + 21, "range": 0, "speed": 0.0, "rate": 0.8, "flip": True},
            {"kind": "macky_sparrow", "x": bx - 10, "y": by + 14, "range": 3, "speed": 0.3, "rate": 1.4},
            {"kind": "macky_sparrow", "x": bx - 46, "y": by + 22, "range": 0, "speed": 0.0, "rate": 0.6},
            {"kind": "macky_sparrow", "x": bx + 2, "y": by + 23, "range": 2, "speed": 0.5, "rate": 1.0, "flip": True},
            {"kind": "rabbit", "x": 700, "y": 470, "range": 0, "speed": 0.0, "rate": 0.6},
        ],
        "leaves": [[100, 150, 110, 110], [760, 170, 110, 110]],
        "layers": [
            {"kind": "twinkle", "points": star_pts, "rate": 1.4, "min": 0.1, "flag": "dawn_started", "when": False},
            {"kind": "twinkle", "points": glow, "rate": 1.1, "min": 0.55, "flag": "dawn_started", "when": False},
            {"kind": "fauna", "flag": "dawn_started", "when": False, "fauna": [
                {"kind": "night_bat", "x": 60, "y": 46, "fly": 13.0, "rate": 6.0},
                {"kind": "night_bat", "x": 600, "y": 30, "fly": 10.0, "rate": 5.0}]},
            {"kind": "fauna", "flag": "dawn_started", "fauna": [
                {"kind": "bird", "x": 40, "y": 40, "fly": 12.0, "rate": 4.0},
                {"kind": "bird", "x": 70, "y": 52, "fly": 11.0, "rate": 3.6},
                {"kind": "bird", "x": 500, "y": 28, "fly": 9.0, "rate": 3.2}]},
        ],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
