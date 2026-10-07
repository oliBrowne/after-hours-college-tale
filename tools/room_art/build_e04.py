"""E04 Suspended model / above the test floor (960x540).

The model level: a checker-plate mezzanine high in the structures bay of the Engineering Center,
up under the building's exposed concrete coffers and the crane runway. The back wall is raw
board-formed concrete (plank grain, form-tie holes, run-off streaks) with a row of tall openings
set deep in it looking out at the Flatirons and the lights of campus, a Lyons sandstone base course
and a sandstone-clad pier beside the control booth.
Two crane trolleys hold the suspended bridge model (drawn by code at placement 0) on wire-rope
slings; those rigs are an occluder so people behind the model pass behind the ropes. Under the
model the deck is an open bar grating with the test floor far below: the anchor grid, the load
frame from above, and the two foundation pads (they glow once the model is revised onto them).
At the back right the control booth's window glows teal; the passage to it opens in the right
wall (locked until bridge_ready by the game's pill). A stair at the front left drops back to the
test floor. Cal's drafting table holds the "perfect" arch drawing.
"""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel import Canvas, C, text  # noqa: E402
from lib_umc import halo, SHADOW, SAFETY, extinguisher, soft_ellipse  # noqa: E402
import lib_eng as E  # noqa: E402
import ec_interior as I  # noqa: E402

ROOM = "E04"
W, H = 960, 540
BASE = 142
FRONT = 516
GIRDER_Y = 44
TROLLEYS = (335, 605)
MODEL = (320, 620, 239, 369)      # code-drawn model box: x0, x1, deck top, floor y
GRATE = (262, 250, 678, 414)      # open grating panel under and around the model
WINDOW = (20, 66, 700, 38)        # band of deep-set openings onto the Flatirons
CEIL = 40                         # underside of the concrete edge beam
STONE_Y = 120                     # top of the sandstone base course
PIER = (724, 16)                  # sandstone pier between the openings and the booth
BOOTH = (744, 54, 184, 64)
STAIR = (43, 410, 107, 453)       # stair down to the test floor (label-only placement 4)
DOOR_Y = (262, 306)               # passage to the control booth in the right wall
WALK = (436, 458, 880, 904)
LAMP = (125, 350)


def paint_fabric(cv, seed=61):
    """Coffered concrete roof, the board-formed wall with its deep openings onto the Flatirons,
    the sandstone base course and pier. Returns the visible twinkle points."""
    I.coffered_ceiling(cv, 0, W, 0, CEIL, seed=seed, bay=40, rib=6)
    I.board_concrete(cv, 0, CEIL, W, STONE_Y - CEIL, seed=seed + 1, board=6, lift=40, foot=0)
    cv.rect(0, CEIL + 3, W, 14, C(SHADOW, 0.3))
    x, y, w, h = WINDOW
    lights = E.flatirons_window(cv, x, y, w, h, seed=62, bay=50)
    lights = I.slot_colonnade(cv, x, y, w, h, pitch=50, open_w=34, depth=4, seed=seed + 2, pts=lights)
    I.lyons_wall(cv, 0, STONE_Y, W, BASE - STONE_Y, seed=seed + 3)
    I.lyons_pier(cv, PIER[0], CEIL, PIER[1], BASE - CEIL, seed=seed + 4)
    return lights


def paint_back(bg):
    lights = paint_fabric(bg)
    ropes = E.crane_girder(bg, 0, W, GIRDER_Y, 14, "10 TON", list(TROLLEYS))
    # control booth window high on the right, set in the concrete
    bx, by, bw, bh = BOOTH
    bg.rect(bx - 4, by - 4, bw + 8, bh + 4, E.CONC[2]); bg.hline(bx - 4, by - 4, bw + 8, E.CONC[1])
    screens, rec = E.booth_window(bg, bx, by, bw, bh, "CONTROL")
    halo(bg, bx + bw // 2, by + bh - 10, 70, "#4ac0b0", 0.05, 3)
    # left wall: crane pendant control, signs, a rack of balsa and spools, extinguisher
    E.pendant_control(bg, 214, GIRDER_Y + 14, 104)
    bg.rect(30, 108, 70, 12, "#1a1524"); bg.rect(31, 109, 68, 10, SAFETY[2]); text(bg, "LEVEL 3", 40, 108, "#1a1524")
    bg.rect(29, 121, 58, 9, "#1a1524"); bg.rect(30, 122, 56, 7, "#3a3d46")
    E.micro_text(bg, "MAX 4 PERSONS", 32, 123, "#e8e2d0")
    extinguisher(bg, 116, BASE - 6)
    rx = 140
    bg.rect(rx, 110, 50, 32, "#1a1524"); bg.rect(rx + 1, 111, 48, 30, "#2a2a34")
    for k in range(8):
        bg.rect(rx + 3 + k * 5, 113, 4, 26, (E.MAPLE[5], E.MAPLE[4], E.MAPLE[6])[k % 3])
        bg.hline(rx + 3 + k * 5, 113, 4, E.MAPLE[6])
    # conduit along the wall under the openings, dropping to two boxes
    I.conduit(bg, 240, 700, 108, drops=[(300, 110), (620, 110)])
    return ropes, lights, screens, rec


def rig_occluder(ropes):
    """Wire-rope slings from the two trolleys to the ends of the model's deck, as one occluder."""
    x0, x1, deck, floor = MODEL
    oy = ropes[0][1]
    cv = Canvas(W, deck - oy + 2)
    hooks = []
    for (tx, ty), (ea, eb) in zip(ropes, ((x0 + 2, x0 + 30), (x1 - 30, x1 - 2))):
        by = deck - 44 - oy
        for k in (-2, 2):
            cv.vline(tx + k, 0, by, E.STEEL[2]); cv.vline(tx + k + 1, 0, by, E.STEEL[5])
        cv.rect(tx - 6, by, 13, 10, E.OUT); cv.rect(tx - 5, by + 1, 11, 8, E.CRANE[3]); cv.hline(tx - 5, by + 1, 11, E.CRANE[5])
        cv.rect(tx - 2, by + 3, 5, 3, E.CRANE[1])
        hy = by + 13
        cv.vline(tx, by + 10, 4, E.STEEL[5])
        cv.line(tx + 1, hy + 2, tx - 1, hy + 5, E.OUT); cv.line(tx - 1, hy + 5, tx - 4, hy + 4, E.OUT)
        # two-leg sling down to the deck, with a red tag
        for ex in (ea, eb):
            cv.line(tx, hy + 3, ex, deck - oy - 1, E.STEEL[3])
            cv.line(tx + 1, hy + 3, ex + 1, deck - oy - 1, E.STEEL[6])
        cv.rect(tx + 3, hy + 8, 4, 5, "#c03a32")
        hooks.append((tx, by + oy))
    return cv, 0, oy, hooks


def paint_floor(bg):
    fh = FRONT - BASE
    E.put_rgb(bg, 0, BASE, E.checker_plate_np(W, fh, seed=64))
    bg.hline(0, BASE, W, "#121218"); bg.hline(0, BASE + 1, W, C(SHADOW, 0.35))
    # plate seams
    for sx in range(96, W, 192):
        bg.vline(sx, BASE, fh, E.DECK[1]); bg.vline(sx + 1, BASE, fh, E.DECK[6])
    for sy in range(BASE + 94, FRONT, 94):
        bg.hline(0, sy, W, E.DECK[1]); bg.hline(0, sy + 1, W, E.DECK[6])
    # the open grating with the test floor far below
    gx0, gy0, gx1, gy1 = GRATE
    pads = E.grating_view(bg, gx0, gy0, gx1, gy1, seed=65)
    # walkway from the stair along the front and up the right side to the booth passage
    yt, yb, rx0, rx1 = WALK
    E.worn_line(bg, STAIR[2] + 6, yt, rx0 - STAIR[2] - 6, 2, SAFETY[2], 0.75, seed=1)
    E.worn_line(bg, STAIR[2] + 6, yb, rx1 - STAIR[2] - 6, 2, SAFETY[2], 0.75, seed=2)
    E.worn_line(bg, rx0, DOOR_Y[1] + 4, 2, yt - DOOR_Y[1] - 4, SAFETY[2], 0.75, seed=3)
    E.worn_line(bg, rx1, DOOR_Y[1] + 4, 2, yb - DOOR_Y[1] - 2, SAFETY[2], 0.75, seed=4)
    E.worn_line(bg, rx0, DOOR_Y[1] + 4, W - 20 - rx0, 2, SAFETY[2], 0.75, seed=5)
    E.worn_line(bg, rx0, DOOR_Y[0] - 2, W - 20 - rx0, 2, SAFETY[2], 0.75, seed=6)
    E.micro_text(bg, "CONTROL >", 884, DOOR_Y[0] + 18, C("#e8e2d0", 0.5))
    # edge of the deck at the back: a toe-board strip
    bg.rect(0, BASE + 2, W, 2, C(SAFETY[1], 0.5))
    # stair down to the test floor
    E.stair_down_well(bg, *STAIR)
    # scattered model parts: balsa offcuts, a coil of wire rope, chalk notes by the grating
    for (ox, oy, ow, c) in ((150, 230, 10, E.MAPLE[5]), (162, 234, 6, E.MAPLE[6]), (720, 330, 9, E.MAPLE[5]), (210, 470, 7, E.MAPLE[4])):
        bg.rect(ox, oy, ow, 2, c); bg.hline(ox, oy + 2, ow, C(SHADOW, 0.6))
    bg.ellipse(196, 300, 16, 7, E.STEEL[3]); bg.ellipse(199, 302, 10, 3, E.DECK[3])
    paint_template(bg, 52, 168, 150, 56)
    paint_tarp(bg, 712, 168, 150, 60)
    E.micro_text(bg, "GRATING - NO DROPPED TOOLS", gx0, gy1 + 6, C(SAFETY[2], 0.6))
    return pads


def paint_template(bg, x, y, w, h):
    """Kraft paper taped to the deck with a full-size marker drawing of one span and its pier,
    Dev's 'FOR FEET' revision pencilled over Cal's arch."""
    bg.rect(x, y, w, h, "#a88456"); bg.hline(x, y, w, "#c49a68"); bg.hline(x, y + h - 1, w, "#7e6040")
    for (tx, ty) in ((x - 2, y - 1), (x + w - 6, y - 1), (x - 2, y + h - 3), (x + w - 6, y + h - 3)):
        bg.rect(tx, ty, 8, 4, C("#e8dcc0", 0.8))
    ink = "#2a2430"
    base_y = y + h - 12
    for xx in range(x + 8, x + w - 8):
        t = (xx - x - 8) / (w - 16)
        yy = int(round(base_y - 30 * 4 * t * (1 - t)))
        bg.px(xx, yy, C(ink, 0.6))
    bg.hline(x + 8, base_y, w - 16, ink); bg.hline(x + 8, base_y + 1, w - 16, ink)
    for px_ in (x + w // 3, x + 2 * w // 3):
        bg.rect(px_ - 3, base_y + 2, 6, 8, C("#2a7a4a", 0.0)); bg.vline(px_ - 3, base_y + 2, 8, "#2a7a4a"); bg.vline(px_ + 2, base_y + 2, 8, "#2a7a4a")
    E.micro_text(bg, "FOR FEET", x + w - 42, y + 4, "#2a7a4a")
    E.micro_text(bg, "1:1", x + 4, y + 4, ink)


def paint_tarp(bg, x, y, w, h):
    """A blue tarp with spare model parts laid out in rows: deck strips, hangers, two piers."""
    bg.rect(x, y, w, h, "#2c4a7a"); bg.hline(x, y, w, "#4a6aa0"); bg.hline(x, y + h - 1, w, "#1e3458")
    for gx in (x + 2, x + w - 4):
        bg.rect(gx, y + 2, 2, 2, E.STEEL[6]); bg.rect(gx, y + h - 4, 2, 2, E.STEEL[6])
    for r in range(3):
        for k in range(6):
            bg.rect(x + 8 + k * 22, y + 8 + r * 7, 18, 2, (E.MAPLE[5], E.MAPLE[6])[k % 2])
            bg.hline(x + 8 + k * 22, y + 10 + r * 7, 18, C(SHADOW, 0.5))
    for k in range(14):
        bg.vline(x + 10 + k * 9, y + 32, 8, E.STEEL[6])
    for px_ in (x + 30, x + 110):
        bg.rect(px_, y + 44, 14, 9, E.CONC[7]); bg.hline(px_, y + 44, 14, E.CONC[8]); bg.hline(px_, y + 53, 14, C(SHADOW, 0.5))
    E.micro_text(bg, "SPARES", x + 56, y + h - 9, "#c8d8f0")


def paint_edges(bg):
    bg.rect(0, FRONT, W, H - FRONT, "#0e0d14")
    bg.hline(0, FRONT, W, E.DECK[6]); bg.hline(0, FRONT + 1, W, E.DECK[3]); bg.rect(0, FRONT + 2, W, 2, E.DECK[1])
    # mezzanine edge rail along the front (seen from above: a yellow top rail line)
    bg.rect(0, FRONT - 3, W, 2, SAFETY[2]); bg.hline(0, FRONT - 3, W, SAFETY[3])
    for x0 in (0, W - 20):
        bg.rect(x0, BASE, 20, FRONT - BASE, "#14161e")
        for yy in range(BASE + 8, FRONT, 8):
            bg.hline(x0, yy, 20, "#1a1d26")
    bg.vline(19, BASE, FRONT - BASE, E.CONC[4]); bg.vline(W - 20, BASE, FRONT - BASE, E.CONC[4])
    # the booth passage in the right wall
    y0, y1 = DOOR_Y
    bg.rect(W - 20, y0, 20, y1 - y0, E.CARPET[3])
    for k in range(0, y1 - y0, 4):
        bg.hline(W - 20, y0 + k, 20, E.CARPET[4])
    E.tint_rect(bg, W - 20, y0, 20, y1 - y0, "#4ac0b0", 0.16)
    bg.rect(W - 20, y0, 4, y1 - y0, E.STEEL[4]); bg.vline(W - 20, y0, y1 - y0, E.STEEL[6])
    bg.rect(W - 20, y0 - 4, 20, 4, E.CONC[5]); bg.rect(W - 20, y1, 20, 3, E.CONC[2])
    E.stepped_glow(bg, W - 24, (y0 + y1) // 2, 50, 20, "#4ac0b0", 0.10, 3)


def paint_lights(bg):
    gx0, gy0, gx1, gy1 = GRATE
    # warm light rising through the grating from the test floor
    E.stepped_glow(bg, (gx0 + gx1) // 2, (gy0 + gy1) // 2, (gx1 - gx0) // 2 + 30, (gy1 - gy0) // 2 + 14, "#f6cf7a", 0.07, 3)
    E.stepped_glow(bg, LAMP[0], LAMP[1] - 2, 60, 16, "#f6cf7a", 0.16, 3)
    E.stepped_glow(bg, 735, 420, 70, 16, "#f6cf7a", 0.10, 2)
    E.stepped_glow(bg, BOOTH[0] + BOOTH[2] // 2, BASE + 10, 110, 16, "#4ac0b0", 0.07, 2)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=4)

    ropes, lights, screens, rec = paint_back(bg)
    pads = paint_floor(bg)
    paint_edges(bg)
    paint_lights(bg)
    bg.save(os.path.join(out, "background.png"))

    rig, rx, ry, hooks = rig_occluder(ropes)
    rig.save(os.path.join(out, "rig.png"))

    props = {}

    def save(index, made):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        props[str(index)] = {"texture": res + name, "anchor": [ax, ay]}

    save(1, E.guardrail(390, 24, "NO STANDING UNDER LOAD"))
    save(2, E.drafting_table(120, 42, seed=2))
    save(3, E.cage_pole_lamp(68))

    glow = E.glow_sprite(30, 11, "#f6cf7a", (0.08, 0.16, 0.28, 0.45))
    glow.save(os.path.join(out, "pad-glow.png"))
    layers = []
    for (px, py) in pads:
        layers.append({"kind": "blink", "pattern": "1111111000", "rate": 2.0, "flag": "model_revised",
                       "texture": res + "pad-glow.png", "x": px - 30, "y": py - 11})
    flick = [[sx + 1, sy + 3, sw - 2, 1, "8af0e0"] for (sx, sy, sw, sh) in screens]
    layers += [
        # booth screens scanning, and its REC lamp: the recording nobody made
        {"kind": "blink", "pattern": "1011101", "rate": 4.0, "rects": flick},
        {"kind": "blink", "pattern": "1100", "rate": 1.5, "flag": "source_reel", "when": False,
         "rects": [[rec[0] - 1, rec[1] - 1, 3, 3, "ff5a4a"], [rec[0] - 4, rec[1] - 4, 9, 9, "ff5a4a", 0.25]]},
        # amber warning lights on the two trolleys while the model hangs
        {"kind": "blink", "pattern": "100000", "rate": 3.0,
         "rects": [[tx - 1, GIRDER_Y + 16, 3, 2, "ffc040"] for tx in TROLLEYS] + [[tx - 5, GIRDER_Y + 12, 11, 9, "ffc040", 0.2] for tx in TROLLEYS]},
        {"kind": "twinkle", "points": [[x, y, c.lstrip("#"), 1] for (x, y, c) in lights], "rate": 1.2, "min": 0.2},
        {"kind": "twinkle", "points": [[LAMP[0], LAMP[1] - 63, "fff0c4", 2]], "rate": 0.9, "min": 0.8},
        # dust drifting up through the warm light over the grating
        {"kind": "particles", "style": "dust", "count": 10, "rect": [GRATE[0], 160, GRATE[2] - GRATE[0], 200],
         "speed": [2, -6], "color": "f6dca0"},
    ]

    manifest = {
        "background": res + "background.png",
        "width": W,
        "props": props,
        "label_only": [4],
        "occluders": [{"texture": res + "rig.png", "x": rx, "y": ry, "base": MODEL[3] - 1}],
        "overlays": [],
        "fauna": [
            {"kind": "pigeon", "x": 760, "y": 36, "range": 14, "speed": 0.3, "rate": 2.0},
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
