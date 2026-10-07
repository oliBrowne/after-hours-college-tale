"""E03 Test floor / put the load somewhere real (960x540).

The structures lab's high bay, in the Engineering Center's raw fabric: grey board-formed concrete
walls printed with plank grain, form-tie holes and run-off streaks, a waffle slab and deep edge
beam overhead, narrow windows set deep in the concrete high up, a base course of rough Lyons
sandstone and a sandstone-clad pier by the stair. Across the back stands the massive board-formed
reaction wall, proud of the back wall, with its grid of steel-collared anchor holes; against it the blue load frame drives a hydraulic actuator into a steel beam
specimen, fed by the hydraulic power unit, watched by the DAQ rack and the universal testing machine
on the left. A yellow 10-ton crane spans the bay overhead with its hook hanging (animated swing),
and above the floor hangs the underside of the suspended bridge model ("the drawing looks
beautiful from the bottom"). At the back right a steel stair climbs to the model level. The strong
floor is concrete with a grid of tie-down anchors; two steel foundation pads flank the spot where
LOADBEARER stands (635, 350) and light up once the model is revised. A walkway runs from the
workshop door (left wall) along the front and up the right side to the stair.

Professor Eric's signal-integrity kit is painted against the wall, out of the walk bounds: a probe
bench in front of the reaction wall's right end (scope with a live eye diagram, a TDR box, a test
board under a probe arm, SMA and probe cables, coils on a wall hook) and a rolling scope cart
between the testing machine and the reaction wall (its trace rings out); a loose coil of SMA cable
lies flat on the floor by the bench.
"""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel import Canvas, C, text  # noqa: E402
from lib_umc import halo, SHADOW, SAFETY, hazard_band, extinguisher  # noqa: E402
import lib_eng as E  # noqa: E402
import ec_interior as I  # noqa: E402

ROOM = "E03"
W, H = 960, 540
BASE = 142
FRONT = 516
GIRDER_Y = 24
TROLLEY_X = 650
HOOK_DROP = 40
MODEL = (186, 404, 60)            # underside of the suspended model: x0, x1, deck y
WALL = (176, 776)                 # the reaction wall's extent
FRAME = (420, 580, 64)            # load frame columns x0, x1, top
HPU_X = 612
DAQ_X, UTM_X = 26, 64
STAIR = (812, 888, 100, 180)      # x0, x1, opening top, first step on the floor
BAYS = (92, 520, 872)             # high-bay lamps
PADS = ((568, 334), (702, 334))   # foundations either side of LOADBEARER
WALK = (452, 476, 880, 904)       # walkway: y top, y bottom, right leg x0, x1
DOOR_Y = (398, 448)               # opening in the left wall to the workshop
LAMP = (100, 340)
CONC_FLOOR = ["#2e2a2e", "#3c3739", "#4a4446", "#5e5755", "#625b59", "#67605d", "#756c69", "#857b76"]
WALL_TOP = 84
CEIL = 22                         # underside of the edge beam
STONE_Y = 114                     # top of the sandstone base course (its cast sill)
WINDOWS = (150, 420, 560, 680, 740, 912)   # deep slot windows high in the bay
WIN_Y, WIN_H, WIN_W = 46, 22, 12
PIER = (782, 22)                  # sandstone-clad pier by the stair: x, width
SI_BENCH = (662, 112)             # Professor Eric's probe bench: x, width
CART_X = 140                      # the rolling scope cart


def reaction_wall(cv, x0, x1, top, base, seed=44):
    """The strong wall: a thick board-formed slab standing proud of the back wall (its lit top
    face shows the thickness), a grid of steel-collared anchor holes, pour lines."""
    w = x1 - x0
    cv.rect(x1, top, 5, base - top, C(SHADOW, 0.35))                          # its shadow on the wall
    I.board_concrete(cv, x0, top, w, base - top, seed=seed, base=6, board=6, lift=24, ties=None, stains=0.18, foot=5)
    cv.rect(x0 - 3, top - 5, w + 6, 5, E.CONC[6]); cv.hline(x0 - 3, top - 5, w + 6, E.CONC[4])
    cv.hline(x0 - 3, top - 1, w + 6, E.CONC[8])
    cv.rect(x0 - 3, top, 3, base - top, E.CONC[7]); cv.rect(x1, top, 3, base - top, E.CONC[3])
    for hy in range(top + 8, base - 8, 18):
        for hx in range(x0 + 8, x1 - 6, 20):
            cv.rect(hx - 1, hy - 1, 4, 4, E.STEEL[3]); cv.px(hx - 1, hy - 1, E.STEEL[5])
            cv.rect(hx, hy, 2, 2, "#0c0b12")
            cv.px(hx, hy + 3, C(E.CONC[2], 0.6))


def paint_fabric(cv, seed=41, windows=WINDOWS):
    """The bay's walls and overhead: waffle slab, board-formed concrete, deep slot windows, the
    sandstone base course and pier. Returns star points."""
    I.coffered_ceiling(cv, 0, W, 0, CEIL, seed=seed)
    I.board_concrete(cv, 0, CEIL, W, STONE_Y - CEIL, seed=seed + 1, board=6, lift=40, foot=0)
    cv.rect(0, CEIL + 3, W, 30, C(SHADOW, 0.38)); cv.rect(0, CEIL + 33, W, 22, C(SHADOW, 0.18))   # dim upper reaches
    stars = []
    for k, wx in enumerate(windows):
        stars += I.deep_window(cv, wx, WIN_Y, WIN_W, WIN_H, seed=seed + 10 + k)
    I.lyons_wall(cv, 0, STONE_Y, W, BASE - STONE_Y, seed=seed + 2)
    I.lyons_pier(cv, PIER[0], CEIL, PIER[1], BASE - CEIL, seed=seed + 3)
    return stars


def paint_back(bg):
    stars = paint_fabric(bg)
    # the reaction wall rises in front of the back wall behind the frame
    reaction_wall(bg, WALL[0], WALL[1], WALL_TOP, BASE)
    E.micro_text(bg, "REACTION WALL - MAX 500 KN PER ANCHOR", WALL[0] + 10, 98, "#d0c4b4")
    for k, ch in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"):
        cx = WALL[0] + 8 + k * 20
        if cx < WALL[1] - 8:
            E.micro_text(bg, ch, cx - 1, 136, "#9c9086")
    # crane bridge with its trolley, and the model hanging from it
    rope = E.crane_girder(bg, 0, W, GIRDER_Y, 16, "10 TON", TROLLEY_X)
    # caged high-bay lamps under the crane runway
    bulbs = [I.cage_lamp(bg, x, GIRDER_Y + 16, 8) for x in BAYS]
    model_pts = E.suspended_underside(bg, MODEL[0], MODEL[1], MODEL[2], GIRDER_Y + 16)
    # its underside lights wash the wall below it
    E.stepped_glow(bg, (MODEL[0] + MODEL[1]) // 2, MODEL[2] + 12, (MODEL[1] - MODEL[0]) // 2, 12, "#f6cf7a", 0.10, 3)
    return bulbs, rope, model_pts, stars


def paint_wall_kit(bg):
    leds = E.daq_rack(bg, DAQ_X, BASE - 72, 30, 72)
    E.micro_text(bg, "DAQ", DAQ_X + 9, BASE - 79, "#d8c8a8")
    utm_screen = E.utm(bg, UTM_X + 12, BASE)
    box = E.lightbox(bg, 446, 46, "LOAD TEST", lit=True)
    halo(bg, box[0] + box[2] // 2, box[1] + 7, 40, "#ff5a4a", 0.07, 3)
    tip, spec = E.test_frame(bg, FRAME[0], FRAME[1], FRAME[2], BASE, seed=5)
    E.hpu(bg, HPU_X, BASE)
    # cable tray along the reaction wall carrying gauge leads back to the DAQ
    bg.rect(WALL[0], 108, FRAME[0] - WALL[0], 3, E.STEEL[3]); bg.hline(WALL[0], 108, FRAME[0] - WALL[0], E.STEEL[5])
    bg.rect(DAQ_X + 30, 108, WALL[0] - DAQ_X - 30, 3, E.STEEL[3]); bg.hline(DAQ_X + 30, 108, WALL[0] - DAQ_X - 30, E.STEEL[5])
    # conduit riser by the DAQ, Professor Eric's probe bench and scope cart
    I.conduit(bg, DAQ_X + 6, DAQ_X + 8, CEIL + 4, drops=[(DAQ_X + 6, BASE - 92)])
    si = I.si_bench(bg, SI_BENCH[0], BASE, SI_BENCH[1], seed=7)
    cart = I.scope_cart(bg, CART_X, BASE, 34, seed=8)
    for rect, kind in ((si["screen"], "eye"), (cart, "ring")):
        bg.paste(I.si_screen_frame(rect[2], rect[3], 0, 6, kind), rect[0], rect[1])
    # right side: hose cabinet, extinguisher
    bg.rect(902, 82, 26, 32, "#1a1524"); bg.rect(903, 83, 24, 30, "#a8322c"); bg.hline(903, 83, 24, "#c84a3c")
    bg.rect(906, 88, 18, 14, "#e8e2d0"); E.micro_text(bg, "HOSE", 907, 92, "#a8322c")
    extinguisher(bg, 910, BASE - 6)
    # a beacon on the frame's left column, a warning light on the trolley
    beacon = (FRAME[0] + 5, FRAME[2] - 4)
    bg.rect(beacon[0] - 2, beacon[1] - 2, 5, 4, "#1a1524"); bg.rect(beacon[0] - 1, beacon[1] - 1, 3, 2, "#a86a1a")
    return leds, utm_screen, tip, spec, beacon, si, cart


def paint_floor(bg):
    fh = FRONT - BASE
    E.put_rgb(bg, 0, BASE, E.epoxy_np(W, fh, seed=51, pal=CONC_FLOOR))
    # the test zone behind the barrier is sealed darker
    E.put_rgb(bg, 290, BASE, E.epoxy_np(340, 112, seed=52, pal=E.CONC[:2] + CONC_FLOOR[1:]))
    E.control_joints(bg, 20, BASE, W - 40, fh, CONC_FLOOR[1], every_x=192, every_y=124, x_off=96)
    E.anchor_floor(bg, 20, BASE, W - 40, fh, pitch=(48, 30), x_off=28, y_off=16)
    bg.hline(0, BASE, W, "#121218"); bg.hline(0, BASE + 1, W, C(SHADOW, 0.35))
    # hazard edge along the front of the test zone (under the barrier) and a stencil
    hazard_band(bg, 290, 262, 340, 4)
    E.big_stencil(bg, "LOAD", 610, 384, SAFETY[2], 0.32, scale=2)
    # gauge leads along the wall foot from the frame to the DAQ
    E.floor_cord(bg, [(DAQ_X + 15, BASE + 1), (DAQ_X + 20, BASE + 6), (FRAME[0] + 30, BASE + 6), (FRAME[0] + 40, BASE + 1)],
                 colour="#2a2a34", hi="#4a4a56")
    # hydraulic fluid weeping by the HPU, tyre marks from the forklift
    E.soft_ellipse(bg, HPU_X + 24, BASE + 8, 22, 4, CONC_FLOOR[1], 0.6)
    E.soft_ellipse(bg, HPU_X + 30, BASE + 9, 8, 2, "#2a2440", 0.5)
    for k in range(2):
        bg.line(140, 236 + k * 6, 300, 226 + k * 6, C(CONC_FLOOR[2], 0.6))
    # the two foundations: steel bearing plates bolted into the strong floor, painted rings
    for k, (px, py) in enumerate(PADS):
        E.soft_ellipse(bg, px, py, 30, 10, SAFETY[1], 0.25)
        bg.ellipse(px - 26, py - 9, 53, 19, C(SAFETY[2], 0.55))
        bg.ellipse(px - 23, py - 7, 47, 15, CONC_FLOOR[4])
        bg.rect(px - 16, py - 5, 33, 11, "#1a1524"); bg.rect(px - 15, py - 4, 31, 9, E.STEEL[4]); bg.hline(px - 15, py - 4, 31, E.STEEL[6])
        for (bx, by) in ((-12, -2), (12, -2), (-12, 3), (12, 3)):
            bg.rect(px + bx, py + by, 2, 2, E.STEEL[2])
        bg.rect(px - 4, py - 2, 9, 5, E.STEEL[3])
        E.micro_text(bg, "AB"[k], px - 1, py + 12, C(SAFETY[2], 0.8))
    # walkway from the workshop door along the front and up the right side to the stair
    yt, yb, rx0, rx1 = WALK
    E.worn_line(bg, 20, yt, rx0 - 20, 2, SAFETY[2], 0.75, seed=1)
    E.worn_line(bg, 20, yb, rx1 - 20, 2, SAFETY[2], 0.75, seed=2)
    E.worn_line(bg, rx0, STAIR[3] + 8, 2, yt - STAIR[3] - 8, SAFETY[2], 0.75, seed=3)
    E.worn_line(bg, rx1, STAIR[3] + 8, 2, yb - STAIR[3] - 6, SAFETY[2], 0.75, seed=4)
    for ax in (180, 400, 640):
        E.micro_text(bg, ">", ax, yt + 10, C("#e8e2d0", 0.4))
    for ay in (300, 400):                                           # chevrons pointing to the stair
        bg.line(rx0 + 8, ay, rx0 + 12, ay - 4, C("#e8e2d0", 0.4)); bg.line(rx0 + 12, ay - 4, rx0 + 16, ay, C("#e8e2d0", 0.4))
    # a loose coil of SMA cable on the floor by the probe bench, its lead back to the bench
    I.ring_coil(bg, 722, BASE + 14, 7, I.CABLE["sma"][0], I.CABLE["sma"][1])
    E.floor_cord(bg, [(729, BASE + 13), (742, BASE + 5), (744, BASE + 1)], colour=I.CABLE["sma"][0], hi=I.CABLE["sma"][1])
    # a taped line where the cylinder cart parks
    E.dashed(bg, 126, 286, 214, 286, SAFETY[2], 5, 3, 0.5)
    # chalk footprints of earlier tests, with their notes
    chalk = "#d8d4c8"
    for (cx, cy, cw, ch, note) in ((700, 196, 120, 40, "TEST 14 - 2 SPANS"), (80, 168, 76, 34, "PIER B"), (340, 470, 160, 30, "")):
        E.dashed(bg, cx, cy, cx + cw, cy, chalk, 4, 3, 0.35); E.dashed(bg, cx, cy + ch, cx + cw, cy + ch, chalk, 4, 3, 0.35)
        E.dashed(bg, cx, cy, cx, cy + ch, chalk, 4, 3, 0.35); E.dashed(bg, cx + cw, cy, cx + cw, cy + ch, chalk, 4, 3, 0.35)
        if note:
            E.micro_text(bg, note, cx + 4, cy + 4, C(chalk, 0.4))
    # anchor grid references painted along the floor's left edge
    for k, ay in enumerate(range(BASE + 16, FRONT - 4, 30)):
        E.micro_text(bg, str(k + 1), 22, ay - 2, C("#e8e2d0", 0.35))


def paint_edges(bg):
    # near wall
    bg.rect(0, FRONT, W, H - FRONT, "#0e0d14")
    bg.hline(0, FRONT, W, E.CONC[5]); bg.hline(0, FRONT + 1, W, E.CONC[3]); bg.rect(0, FRONT + 2, W, 2, E.CONC[1])
    # side walls, the left one opening to the workshop
    for x0 in (0, W - 20):
        bg.rect(x0, BASE, 20, FRONT - BASE, "#14161e")
        for yy in range(BASE + 8, FRONT, 8):
            bg.hline(x0, yy, 20, "#1a1d26")
    bg.vline(19, BASE, FRONT - BASE, E.CONC[4]); bg.vline(W - 20, BASE, FRONT - BASE, E.CONC[4])
    y0, y1 = DOOR_Y
    bg.rect(0, y0, 20, y1 - y0, E.EPOXY[3])
    for k in range(0, y1 - y0, 4):
        bg.hline(0, y0 + k, 20, E.EPOXY[4])
    E.tint_rect(bg, 0, y0, 20, y1 - y0, "#f6cf7a", 0.18)
    bg.rect(14, y0, 6, y1 - y0, E.STEEL[4]); bg.vline(19, y0, y1 - y0, E.STEEL[6])
    bg.rect(0, y0 - 4, 20, 4, E.CONC[5]); bg.rect(0, y1, 20, 3, E.CONC[2])
    E.stepped_glow(bg, 24, (y0 + y1) // 2, 46, 22, "#f6cf7a", 0.12, 3)


def paint_lights(bg):
    for x in BAYS:
        E.stepped_glow(bg, x, 300, 170, 46, "#f6e0a8", 0.08, 3)
        halo(bg, x, GIRDER_Y + 30, 40, "#f6e0a8", 0.05, 3)
    E.stepped_glow(bg, 500, BASE + 30, 160, 26, "#f6cf7a", 0.08, 2)
    # the tripod flood washing the bench
    E.stepped_glow(bg, 200, 352, 110, 26, "#f6cf7a", 0.14, 3)
    E.stepped_glow(bg, (STAIR[0] + STAIR[1]) // 2, STAIR[3] + 8, 50, 10, "#f6cf7a", 0.08, 2)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=3)

    bulbs, rope, model_pts, stars = paint_back(bg)
    leds, utm_screen, tip, spec, beacon, si, cart = paint_wall_kit(bg)
    paint_floor(bg)
    x0, x1, top, fy = STAIR
    E.stair_up_opening(bg, x0, x1, top, BASE, fy, "MODEL LEVEL", steps_out=5)
    paint_edges(bg)
    paint_lights(bg)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        props[str(index)] = {"texture": res + name, "anchor": [ax, ay]}

    save(0, E.pipe_barrier(320, 25, "TEST AREA"))
    save(1, E.steel_bench_chart(170, 42, seed=2))
    save(2, E.cylinder_cart(80, 50, seed=3))
    save(4, E.flood_tripod(68))
    save(5, E.chain_barrier(120, 26, "KEEP CLEAR"))

    # the crane hook swinging gently on its ropes
    layers = []
    # Professor Eric's screens: the bench scope's eye diagram shimmering, the cart scope ringing
    for name, rect, kind, n, rate in (("si-eye", si["screen"], "eye", 6, 5.0), ("si-ring", cart, "ring", 6, 4.0)):
        sx, sy, sw, sh = rect
        for k in range(n):
            fr = I.si_screen_frame(sw, sh, k, n, kind)
            fr.save(os.path.join(out, f"{name}-{k}.png"))
            layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(n)), "rate": rate,
                           "texture": res + f"{name}-{k}.png", "x": sx, "y": sy})
    vx, vy, vw, vh = si["vna"]
    layers.append({"kind": "blink", "pattern": "1110", "rate": 2.0,
                   "rects": [[vx + 2, vy + vh // 2 - 1, vw - 4, 1, "4ab8d8"], [vx + vw // 2, vy + 1, 1, vh - 2, "2a6e8a"]]})
    offsets = [-2, -1, 0, 1, 2]
    seq = [0, 1, 2, 3, 4, 4, 3, 2, 1, 0]
    for k, dx in enumerate(offsets):
        fr = E.hook_frame(HOOK_DROP, dx, 24)
        fr.save(os.path.join(out, f"hook-{k}.png"))
        layers.append({"kind": "blink", "pattern": "".join("1" if s == k else "0" for s in seq), "rate": 3.0,
                       "texture": res + f"hook-{k}.png", "x": rope[0] - 12, "y": rope[1]})
    # DAQ module LEDs in three offset groups (a slow chase), the UTM screen ticking
    groups = [leds[0::3], leds[1::3], leds[2::3]]
    for g, pat in zip(groups, ("100", "010", "001")):
        layers.append({"kind": "blink", "pattern": pat, "rate": 2.5, "rects": [[x, y, 1, 1, c.lstrip("#")] for (x, y, c) in g]})
    layers += [
        {"kind": "blink", "pattern": "10", "rate": 1.0, "rects": [[utm_screen[0] + 1, utm_screen[1] + 2, 6, 1, "7ae0a0"]]},
        # amber beacon on the frame column: the test is live
        {"kind": "blink", "pattern": "1000", "rate": 3.0, "rects": [[beacon[0] - 1, beacon[1] - 1, 3, 2, "ffc040"],
                                                                     [beacon[0] - 6, beacon[1] - 6, 13, 12, "ffc040", 0.18]]},
        {"kind": "blink", "pattern": "10", "rate": 1.2, "rects": [[TROLLEY_X - 1, GIRDER_Y + 18, 3, 2, "ff4a3a"]]},
        # the model's underside lights and the bay lamps breathing
        {"kind": "twinkle", "points": [[x, y, "f6cf7a", 1] for (x, y) in model_pts], "rate": 1.1, "min": 0.4},
        {"kind": "twinkle", "points": [[x, y, "fff0c4", 2] for (x, y) in bulbs] + [[LAMP[0], LAMP[1] - 62, "fff0c4", 2]],
         "rate": 0.8, "min": 0.8},
        {"kind": "particles", "style": "dust", "count": 9, "rect": [60, 60, 840, 160], "speed": [3, 2], "color": "f6e0a8"},
        {"kind": "twinkle", "points": [[x, y, c.lstrip("#"), 1] for (x, y, c) in stars], "rate": 1.3, "min": 0.15},
    ]
    # the two foundations light up once the model has been revised onto them
    glow = E.glow_sprite(40, 15, "#f6cf7a", (0.07, 0.14, 0.26, 0.42))
    glow.save(os.path.join(out, "pad-glow.png"))
    for (px, py) in PADS:
        layers.append({"kind": "blink", "pattern": "1111111000", "rate": 2.0, "flag": "model_revised",
                       "texture": res + "pad-glow.png", "x": px - 40, "y": py - 15})

    manifest = {
        "background": res + "background.png",
        "width": W,
        "props": props,
        "label_only": [3],
        "occluders": [],
        "overlays": [],
        "fauna": [
            {"kind": "pigeon", "x": 300, "y": GIRDER_Y, "range": 18, "speed": 0.3, "rate": 2.0},
            {"kind": "lamp_moth", "x": LAMP[0] + 1, "y": LAMP[1] - 66, "range": 7, "speed": 1.8, "rate": 9.0},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
