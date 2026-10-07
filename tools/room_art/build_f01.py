"""Farrand / cable walk (F01): the festival's service walk across Farrand Field at night.
A mat walkway runs from the UMC east gate (left) to the food court (right); cable bundles snake
beside it under yellow ramps; a branch of mats climbs to the striped volunteer tent at the back;
the main stage glows far off under the Flatirons, sweeping its beams. Rook marshals the route,
where the old EVERYONE THIS WAY sign has been crossed out in favour of one route."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import atlas_tree, ground_shadow, OUT
import lib_farrand as F

ROOM = "F01"
W, H = 800, 480
WALK_TOP = 142
FAR_EDGE = 122           # far side of the field (hedge line)
TENT_X, TENT_BASE = 230, 150


def walk_centre(x):
    """Mid line of the main mat walkway (gate on the left, food court on the right)."""
    return float(np.interp(x, [0, 300, 560, 800], [392, 384, 364, 352]))


def branch_centre(y):
    """Mid line of the mat path up to the volunteer tent."""
    return 230 - (y - 150) * 0.1


def spray_arrow(cv, x, y, direction, colour, crossed=False, seed=0):
    """A field-marking arrow sprayed on the grass, with a little overspray."""
    rng = np.random.default_rng(seed)
    c0, c1 = colour
    if direction == "up":
        cv.rect(x - 1, y - 10, 3, 10, c0); cv.vline(x, y - 10, 10, c1)
        cv.poly([(x - 5, y - 9), (x + 1, y - 15), (x + 6, y - 9)], c0); cv.hline(x - 1, y - 11, 3, c1)
        box = (x - 6, y - 16, 13, 17)
    else:
        d = 1 if direction > 0 else -1
        x0 = x if d > 0 else x - 12
        cv.rect(x0, y - 1, 12, 3, c0); cv.hline(x0, y, 12, c1)
        tip = x + d * 18
        cv.poly([(tip - d * 7, y - 5), (tip, y), (tip - d * 7, y + 5)], c0)
        cv.line(tip - d * 6, y - 3, tip - d * 2, y, c1)
        box = (min(x, tip) - 1, y - 6, 20, 13)
    for _ in range(10):
        cv.px(box[0] + int(rng.integers(0, box[2])), box[1] + int(rng.integers(0, box[3])), C(c0, 0.6))
    if crossed:
        cx_, cy_ = box[0] + box[2] // 2, box[1] + box[3] // 2
        for k in range(-6, 7):
            cv.px(cx_ + k, cy_ + k // 2 + (0 if direction != "up" else k // 2), "#d8483c")
            cv.px(cx_ + k, cy_ - k // 2 - (0 if direction != "up" else k // 2), "#d8483c")
            cv.px(cx_ + k + 1, cy_ - k // 2 - (0 if direction != "up" else k // 2), "#a83030")


def volunteer_tent_back(cv):
    """The volunteer tent at the back of the walk at character scale, its door flaps tied open
    and lit inside. Returns the peak (for the festoon)."""
    tw, eave_h, peak_h = 196, 72, 40
    tent, ax, ay = F.peaked_tent(tw, eave_h, peak_h, open_front=False, seed=4, valance_text="VOLUNTEERS",
                                 poles=[0, 64, 129, tw - 3])
    cv.paste(tent, TENT_X - ax, TENT_BASE - ay)
    # doorway: warm interior between tied-back flaps
    dw, dh = 34, 60
    dx0, dy0 = TENT_X - dw // 2, TENT_BASE - dh
    cv.rect(dx0 - 1, dy0 - 1, dw + 2, dh + 1, OUT)
    for yy in range(dh):
        t = yy / dh
        cv.hline(dx0, dy0 + yy, dw, F.BULB[3] if t < 0.12 else F.BULB[2] if t < 0.5 else F.BULB[1])
    # inside: a hanging bulb, a table with a cash box, a stack of chairs, a vest on a hook
    cv.vline(TENT_X + 2, dy0, 6, F.WIRE); cv.rect(TENT_X + 1, dy0 + 6, 3, 3, "#fffaf0")
    cv.rect(dx0 + 2, dy0 + 36, 18, 3, F.PLY[2]); cv.vline(dx0 + 4, dy0 + 39, dh - 41, F.PLY[1]); cv.vline(dx0 + 18, dy0 + 39, dh - 41, F.PLY[1])
    cv.rect(dx0 + 6, dy0 + 32, 8, 4, "#5c3a28"); cv.hline(dx0 + 6, dy0 + 32, 8, "#7a4a30")
    F.chair_stack(cv, dx0 + 22, TENT_BASE - 3, n=5, w=10)
    F.hivis_vest(cv, dx0 + 4, dy0 + 12)
    cv.rect(dx0, TENT_BASE - 4, dw, 4, F.PLY[3]); cv.hline(dx0, TENT_BASE - 4, dw, F.PLY[5])
    # flaps tied back
    for side in (-1, 1):
        fx = TENT_X + side * (dw // 2 + 1)
        pts = [(fx, dy0), (fx + side * 11, dy0 + 6), (fx + side * 7, TENT_BASE), (fx, TENT_BASE)]
        cv.poly(pts, F.CANVAS[3]); cv.line(fx, dy0, fx + side * 7, TENT_BASE - 1, F.CANVAS[5])
        cv.line(fx + side * 11, dy0 + 6, fx + side * 7, TENT_BASE - 1, F.CANVAS[2])
        cv.rect(fx + side * 9 - 1, dy0 + 28, 3, 2, F.RED[3])
    return (TENT_X, TENT_BASE - eave_h - peak_h)


def bottom_edge(cv, seed=0):
    """Below the walkable lawn: a line of hay bales, a cone or two and the end of a cable run."""
    rng = np.random.default_rng(seed)
    y = H - 22
    cv.rect(0, y, W, 22, "#1a2420")
    x = -10
    while x < W:
        bw = int(rng.integers(30, 40))
        bale, bax, bay = F.hay_bales(bw, 18, seed=int(rng.integers(1e6)))
        cv.paste(bale, x, y - 3)
        x += bw + int(rng.integers(0, 12))
    for cx_ in (180, 520, 690):
        F.traffic_cone(cv, cx_, H - 2, 11)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=11)
    twinkles = []

    # --- sky, mountains, the far edge of the field ---------------------------------------------
    sky, _ = F.farrand_sky(W, 150, panels=(0, 1, 0, 1), offset=40, scale=2.0, stars=50, seed=5)
    bg.a[:150] = sky
    F.far_hedge(bg, 0, W, FAR_EDGE, seed=2)
    # the main stage far off to the right, its delay towers, then the field-edge trees
    stage_pts = F.distant_stage(bg, 604, FAR_EDGE + 2, w=172, h=62, seed=3)
    tower_pts = F.light_tower(bg, 496, FAR_EDGE + 4, 74, seed=1) + F.light_tower(bg, 712, FAR_EDGE + 4, 70, seed=2)
    F.treeline_back(bg, -10, 820, FAR_EDGE + 6, seed=7, heights=(64, 104), gap=(46, 80), skip=[(140, 330), (500, 712)])
    # lawn from the far edge down
    F.lawn(bg, 0, FAR_EDGE, W, H - FAR_EDGE, seed=12, clover=0.03, leaves=0.12, stripes=(46, -0.35))
    # far band of the field sits in haze
    bg.rect(0, FAR_EDGE, W, WALK_TOP - FAR_EDGE, C("#2a2440", 0.35))
    bg.rect(0, FAR_EDGE, W, 6, C("#2a2440", 0.25))
    # more trees and the far festoon masts
    peak = volunteer_tent_back(bg)
    for (mx, mh) in [(392, 74), (470, 70)]:
        bg.rect(mx, FAR_EDGE + 16 - mh, 2, mh, "#2a2432"); bg.vline(mx, FAR_EDGE + 16 - mh, mh, "#3e3646")
    twinkles += F.festoon(bg, peak[0] + 2, peak[1] + 4, 392, FAR_EDGE + 16 - 74, sag=14, every=8, seed=1)
    twinkles += F.festoon(bg, 393, FAR_EDGE + 16 - 74, 470, FAR_EDGE + 16 - 70, sag=10, every=8, seed=2)
    twinkles += F.festoon(bg, 471, FAR_EDGE + 16 - 70, 496, FAR_EDGE + 4 - 74, sag=5, every=8, seed=3)
    twinkles += F.festoon(bg, 0, 96, peak[0] - 60, TENT_BASE - 54, sag=10, every=8, seed=4)
    # food court glow beyond the trees on the right
    for (r, a) in [(60, 0.08), (40, 0.1), (24, 0.12)]:
        bg.ellipse(800 - r, 100 - r // 2, r * 2, r, C(F.BULB[1], a))

    # --- the walk -------------------------------------------------------------------------------
    F.trodden_patch(bg, TENT_X, 170, 44, 16, seed=3)
    F.trodden_patch(bg, 40, 400, 50, 30, seed=4)
    F.trodden_patch(bg, 760, 352, 50, 26, seed=5)
    F.trodden_patch(bg, 560, 300, 60, 22, seed=6, strength=0.8)
    branch = F.mat_path_vertical(bg, branch_centre, TENT_BASE - 2, int(walk_centre(210)) - 20, width=34, seed=8)
    walk = F.mat_walkway(bg, walk_centre, width=44, seed=9)
    # cables: one bundle from the stage along the barrier to the tent, one across to the desk
    bundle = [(560, WALK_TOP), (548, 220), (520, 300), (470, 337), (380, 344), (260, 352), (200, 352), (160, 350),
              (120, 346), (60, 352), (0, 360)]
    F.cable_run(bg, bundle, count=3, seed=4)
    F.cable_run(bg, [(474, 338), (470, 420), (480, H)], count=2, seed=5, tape_every=50)
    F.cable_run(bg, [(160, 352), (200, 300), (214, 240), (214, 160), (206, TENT_BASE)], count=2, seed=6, tape_every=0)
    # ramps where cables cross walking routes
    F.cable_ramp_vertical(bg, 464, int(walk_centre(470)) - 23, int(walk_centre(470)) + 23)
    bx = int(branch_centre(346))
    F.cable_ramp_horizontal(bg, bx - 20, bx + 20, 343)
    # tape arrows on the mats: the one marked route (green), an old call taped over
    for x in (90, 330, 610, 740):
        F.tape_arrow(bg, x, int(walk_centre(x)) + 1, 1)
    F.tape_arrow(bg, int(branch_centre(250)), 252, "up")
    F.tape_arrow(bg, int(branch_centre(200)), 202, "up")
    F.tape_arrow(bg, 410, int(walk_centre(410)) - 10, -1, colour=["#5a5a62", "#b8b8c0", "#e6e6ea"], crossed=True)
    # sprayed field marks: one green row toward the food court, the cancelled stage route
    for i, x in enumerate((582, 616, 650)):
        spray_arrow(bg, x, 286 - i * 2, 1, ("#3e9a5c", "#7ad08e"), seed=i)
    for i, y in enumerate((292, 262)):
        spray_arrow(bg, 486 + i * 8, y, "up", ("#c8c8d0", "#f0f0f4"), crossed=True, seed=9 + i)

    # rain left in the dips, and a few things dropped on the way out
    F.puddle(bg, 96, 292, 26, 7, seed=1)
    F.puddle(bg, 662, 432, 34, 8, seed=2, reflect=("#f6cf7a", "#e8a0d0"))
    F.puddle(bg, 380, 386, 14, 4, seed=3)
    rng = np.random.default_rng(21)
    for kind, (x, y) in zip(["cup", "band", "flyer", "cup_down", "cap", "cup", "band", "flyer"],
                            [(118, 236), (276, 300), (430, 428), (612, 412), (700, 300), (60, 330), (742, 236), (402, 200)]):
        F.litter(bg, x, y, kind, seed=int(rng.integers(100)))

    # --- light ----------------------------------------------------------------------------------
    F.light_pool(bg, 152, 360, 56, 18, strength=0.26)
    F.light_pool(bg, TENT_X, 158, 46, 14, strength=0.3)
    F.light_pool(bg, 800, 352, 90, 34, strength=0.24)
    F.light_pool(bg, 340, 236, 70, 20, strength=0.12)  # bulbs in the oak
    for t in (0.3, 0.65):  # under the overhead string from the pole to the oak
        F.light_pool(bg, int(152 + 150 * t), int(360 - 120 * t), 30, 9, strength=0.1)
    F.light_pool(bg, 80, 362, 34, 9, strength=0.1)

    # --- edges ----------------------------------------------------------------------------------
    bg.rect(0, WALK_TOP, 20, H - WALK_TOP, C("#0d0b16", 0.35))
    gate_pts = F.stone_wall_side(bg, 0, WALK_TOP - 4, H - 22, gap=(366, 418), seed=1)
    F.light_pool(bg, 30, 370, 26, 9, strength=0.14); F.light_pool(bg, 30, 422, 26, 9, strength=0.14)
    bg.rect(W - 20, WALK_TOP, 20, H - WALK_TOP, C("#0d0b16", 0.3))
    bottom_edge(bg, seed=3)
    bg.rect(0, H - 24, W, 24, C("#0d0b16", 0.35))
    bg.save(os.path.join(out, "background.png"))

    # --- props ----------------------------------------------------------------------------------
    props = {}

    def save(index, sprite, ax, ay, extra=None):
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [int(ax), int(ay)]}
        entry.update(extra or {})
        props[str(index)] = entry

    # 0: the lawn oak, festoon draped through its crown
    tree, tax, tay = atlas_tree(118, cell=5, seed=2)
    rng = np.random.default_rng(3)
    for (y0, y1, sag) in [(34, 30, 14), (56, 60, 12)]:
        F.festoon(tree, 14, y0, tree.w - 14, y1, sag=sag, every=7, seed=int(rng.integers(100)), glow=True)
    save(0, tree, tax, tay)
    # 1: crowd barriers along the cable run
    save(1, *F.crowd_barrier(150, 26, seed=1))
    # 2: festoon pole (lamp)
    pole, pax, pay, _bulb = F.festoon_pole(55, seed=2)
    save(2, pole, pax, pay)
    # 3: the route notice
    sign, sax, say = F.a_frame_sign(90, 58, header="FOLLOW ONE",
                                    lines=[("EVERYONE", "#4a3a34", True), ("THIS WAY", "#4a3a34", True)], seed=3)
    by = say - 58 + 3 + 10 + 18 + 2
    for k, (c, mark) in enumerate([("#8a8a92", False), ("#2a8a4c", True), ("#8a8a92", False)]):
        ax0 = sax - 30 + k * 22
        sign.rect(ax0, by + 2, 10, 2, c); sign.poly([(ax0 + 9, by - 1), (ax0 + 14, by + 3), (ax0 + 9, by + 7)], c)
        if mark:
            sign.ellipse(ax0 - 3, by - 3, 21, 12, C("#2a8a4c", 0.0))
            for a in np.linspace(0, 2 * np.pi, 44):
                sign.px(int(round(ax0 + 6 + np.cos(a) * 10)), int(round(by + 3 + np.sin(a) * 5)), "#2a8a4c")
    save(3, sign, sax, say)
    # 4: cable trolley
    save(4, *F.cable_cart(72, 43, seed=4))

    # overhead strings from the pole to the oak and to the gate lantern, y-sorted in pieces
    ox_, oy_ = 150 - pax, 360 - pay
    top = (ox_ + pax, oy_ + _bulb[1] - 9)
    occluders = F.festoon_occluders(ROOM, out, "festoon-a", top[0] + 1, top[1], 360, 300, 194, 240, sag=18, every=9, seed=31, pieces=6)
    occluders += F.festoon_occluders(ROOM, out, "festoon-b", gate_pts[0][0] + 1, gate_pts[0][1] - 6, 366, top[0] - 1, top[1], 360, sag=12, every=9, seed=32, pieces=4)
    bulbs = [p for p in twinkles if p[1] < WALK_TOP]
    stage_lamps = [[x, y, "f6dca0", 1] for (x, y) in stage_pts]
    manifest = {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": occluders,
        "props": props,
        "label_only": [],
        "fauna": [
            {"kind": "moth", "x": 146, "y": 302, "range": 7, "speed": 2.3, "rate": 8.0},
            {"kind": "moth", "x": 156, "y": 312, "range": 5, "speed": 1.7, "rate": 7.0, "flip": True},
            {"kind": "rabbit", "x": 92, "y": 214, "range": 0, "speed": 0.0, "rate": 0.6},
            {"kind": "bat", "x": 120, "y": 40, "fly": 22.0, "rate": 7.0},
            {"kind": "bat", "x": 460, "y": 28, "fly": 17.0, "rate": 6.0},
        ],
        "leaves": [[290, 140, 100, 90]],
        "layers": [
            {"kind": "beam", "x": 560, "y": FAR_EDGE - 54, "angle": -100, "sweep": 18, "period": 9.0, "phase": 0.0,
             "length": 130, "width": 26, "color": "c8b0ff", "alpha": 0.14, "floor": -400},
            {"kind": "beam", "x": 640, "y": FAR_EDGE - 54, "angle": -80, "sweep": 18, "period": 11.0, "phase": 2.2,
             "length": 130, "width": 26, "color": "ffd0e8", "alpha": 0.13, "floor": -400},
            {"kind": "twinkle", "points": bulbs + gate_pts, "rate": 1.8, "min": 0.4},
            {"kind": "twinkle", "points": stage_lamps + [[x, y, "fff0c4", 1] for (x, y) in tower_pts], "rate": 1.2, "min": 0.5},
        ],
    }
    return manifest


if __name__ == "__main__":
    m = build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
    print(json.dumps(m)[:200])
