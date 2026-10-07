"""Moving stacks (N04): Norlin's two-tier book stacks, where the ranges run on rails.

Back wall: the painted ceiling edge; the upper stack tier behind an iron gallery rail on a deck of
glass floor tiles, carried on slim iron columns; below it the ground-tier bays: an iron spiral
stair up to the gallery, books with brass range cards, a pigeonhole rack of red-pencilled proofs,
caged work lamps hanging from the deck, and the MARKED PASSAGE board (an overlay that reads TURN
CRANK until the crank is turned, then OPEN). Right: the closed archive's sandstone wall with its
banded door, carved lintel and bookmark-shaped key plate, and a tall moonlit window.
Floor: cork tiles with two pairs of steel rails the ranges roll on, the passage marked on the
floor in yellow, a green runner in from the checkout hall (left), a grey service aisle out to the
garden (right), a short runner from the archive door, red-pencilled errata slips on the floor.
Props: four mobile ranges (two slide when `stacks_shifted`), the SHIFT AISLE crank pedestal (its
dial and lamp swap to OPEN with the flag), the ONE SENTENCE lectern and a floor lamp."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from props import OUT, IRON
from lib_norlin import (floor_inlay, plaster_wall, ceiling_band, wall_shelves, book_row, arched_window, runner_n, depth_shade,
                        standard_lamp, stone_wall, quoins, moon_patch, OAK, OAK_DARK, PAGE, BRASS, GILT, STONE_N,
                        CARPET_GREEN, CARPET_PLUM, LIME)
from lib_norlin2 import (vault_lights, stack_shelf, floor_rails, tile_floor, tread_plate, iron_column, gallery_deck, gallery_rail, iron_stair,
                         cage_lamp, passage_sign, pigeonholes, proof_sheet, correction_slip, archive_door, call_card,
                         crank_pedestal, sentence_notice, STACK, RAIL, HAZARD, RED_PENCIL)

ROOM = "N04"
W, H = 960, 540
BASE = 142
WALK = (20, 142, 920, 374)
DECK_Y = 56                     # top of the gallery deck edge (the upper tier's floor)
DECK_H = 10
RAIL_TOP = 38
GALLERY_X1 = 772                # the gallery stops at the archive's sandstone wall
COLUMNS = [150, 300, 450, 600, 750]
ARCHIVE = (830, BASE)           # door centre / threshold row; the exit mat is drawn by code at (830, 190)
WINDOW = (918, 34, 26, 70)      # tall window in the archive wall (x, top of rect, w, h)
SIGN_X = 525                    # MARKED PASSAGE board, hung from the deck in the middle bay
LAMPS = [104, 225, 375, 675]    # caged lamps hanging under the deck
ROW_A, ROW_B = 265, 375         # floor rows of the two ranks of ranges
PASSAGE = (352, 608, 268, 350)  # the marked passage in rank B (x0, x1, y0, y1)
FLOOR_LAMP = (105, 270)


def back_wall(bg):
    plaster_wall(bg, 0, 12, W, BASE - 12, seed=4, shadow_top=8)
    ceiling_band(bg, 0, 0, W, 12)
    # upper tier: books behind the gallery rail, darker with distance from the lamps
    wall_shelves(bg, 4, 15, GALLERY_X1 - 8, DECK_Y - 15, seed=61, shelf=20, dim=0.32, frame=False)
    bg.rect(0, 12, GALLERY_X1, 3, OAK_DARK[0])
    for k, x in enumerate(range(40, GALLERY_X1 - 20, 150)):
        cage_lamp(bg, x + 30, 30, 12, lit=k % 2 == 0)
    gallery_rail(bg, 0, GALLERY_X1, RAIL_TOP, DECK_Y)
    # lower tier: bays between the iron columns
    bay_top = DECK_Y + DECK_H
    wall_shelves(bg, 156, bay_top + 10, 138, BASE - bay_top - 14, seed=62, shelf=22, dim=0.08, frame=False)
    wall_shelves(bg, 456, bay_top + 10, 138, BASE - bay_top - 14, seed=63, shelf=22, dim=0.08, frame=False)
    wall_shelves(bg, 606, bay_top + 10, 138, BASE - bay_top - 14, seed=64, shelf=22, dim=0.08, frame=False)
    for x0 in (156, 456, 606):
        bg.rect(x0 - 2, BASE - 6, 142, 6, OAK[2]); bg.hline(x0 - 2, BASE - 6, 142, OAK[4])
    # bay 2: the proofing corner - pigeonholes, pinned proofs, a red pencil on a string
    bg.rect(300, bay_top, 150, BASE - bay_top, C("#0d0b16", 0.12))
    pigeonholes(bg, 312, bay_top + 14, 76, 44, seed=5)
    for i, (px_, py_) in enumerate([(398, bay_top + 12), (414, bay_top + 16), (430, bay_top + 10), (404, bay_top + 38), (424, bay_top + 40)]):
        proof_sheet(bg, px_, py_, 13, 17, seed=i)
    bg.vline(440, bay_top + 30, 10, "#8a7e72"); bg.rect(439, bay_top + 40, 3, 9, RED_PENCIL[1]); bg.px(440, bay_top + 49, "#e6c08a")
    bg.rect(306, BASE - 18, 138, 4, OAK[3]); bg.hline(306, BASE - 18, 138, OAK[5])
    bg.rect(310, BASE - 14, 4, 14, OAK[2]); bg.rect(436, BASE - 14, 4, 14, OAK[2])
    # bay 0: an iron stair climbing to the gallery, a book truck parked in its shadow
    bg.rect(0, bay_top, 150, BASE - bay_top, C("#0d0b16", 0.18))
    wall_shelves(bg, 84, bay_top + 30, 56, BASE - bay_top - 34, seed=65, shelf=20, dim=0.2, frame=False)
    iron_stair(bg, 22, BASE, 118, DECK_Y + 2)
    # range cards over the book bays
    for (cx, lab) in [(178, "PN 2"), (478, "PR 9"), (628, "PT 1")]:
        call_card(bg, cx - (text_width(lab) + 6) // 2, bay_top + 1, lab)
    # deck and columns over everything in the lower tier
    gallery_deck(bg, 0, GALLERY_X1, DECK_Y, DECK_H)
    for cx in COLUMNS:
        iron_column(bg, cx, DECK_Y + DECK_H, BASE)
        bg.rect(cx - 2, RAIL_TOP - 4, 4, DECK_Y - RAIL_TOP + 4, IRON[2]); bg.vline(cx - 2, RAIL_TOP - 4, DECK_Y - RAIL_TOP + 4, IRON[4])
    for lx in LAMPS:
        cage_lamp(bg, lx, bay_top + 16, bay_top)
    # MARKED PASSAGE board's chain hooks under the deck (the board itself is an overlay)
    for hx in (SIGN_X - 46, SIGN_X + 47):
        bg.rect(hx - 1, bay_top, 3, 2, IRON[3])
    archive_wall(bg)
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))


def archive_wall(bg):
    """The closed archive's sandstone wall at the right: the gallery butts into it."""
    x0 = GALLERY_X1
    stone_wall(bg, x0, 12, W - x0, BASE - 12, pal=[shade(c, -0.12) for c in STONE_N], seed=8, course=6)
    quoins(bg, x0, 14, BASE - 4, "left")
    bg.rect(x0 - 2, 12, 3, BASE - 12, C("#0d0b16", 0.5))
    ceiling_band(bg, x0, 0, W - x0, 12)
    archive_door(bg, ARCHIVE[0], BASE, w=44, h=72, label="ARCHIVE")
    wx, wt, ww, wh = WINDOW
    arched_window(bg, wx - ww // 2, wt, ww, wh, seed=17, view="campus", moon=(wx + 4, wt - 6))
    # a caged lamp on a bracket beside the door, an old fire bucket hook
    bg.rect(872, 74, 8, 2, IRON[2])
    cage_lamp(bg, 879, 90, 74)
    bg.rect(783, 104, 2, 8, IRON[2]); bg.rect(779, 110, 10, 12, OUT); bg.rect(780, 111, 8, 10, "#a83c32"); bg.hline(780, 111, 8, "#c8584a")
    text(bg, "F", 782, 112, "#e6d6b1")


def floor(bg):
    tile_floor(bg, 0, BASE, W, H - BASE, seed=9)
    floor_inlay(bg, 30, BASE + 8, W - 60, WALK[1] + WALK[3] - BASE - 16, t=4, colour="#3a2422", line="#a8844e")
    # pavement lights over the lower stack level, glowing faintly from below
    for (vx, vy, c, r) in [(46, 318, 12, 3), (822, 214, 10, 3), (650, 476, 12, 3), (238, 476, 10, 3)]:
        vault_lights(bg, vx, vy, c, r)
        light_pool(bg, vx + c * 7 // 2, vy + r * 5 // 2, c * 4 + 6, r * 3 + 4, color="#a8d8d0", strength=0.08)
    # steel track beds and the rails each rank of ranges runs on, clear of the walls
    tread_plate(bg, 180, ROW_A - 24, 482, 26)
    tread_plate(bg, 180, ROW_B - 24, 602, 26)
    floor_rails(bg, 186, 656, ROW_A - 17, ROW_A - 7)
    floor_rails(bg, 186, 776, ROW_B - 17, ROW_B - 7)
    # the marked passage in rank B: yellow dashes, hatched ends, PASSAGE stencilled between
    x0, x1, y0, y1 = PASSAGE
    for x in range(x0, x1, 6):
        bg.rect(x, y0, 3, 2, HAZARD[2]); bg.rect(x, y1, 3, 2, HAZARD[2])
    for (hx, d) in ((x0, 1), (x1 - 10, -1)):
        for yy in range(y0, y1 + 2):
            off = (yy - y0) % 6
            bg.rect(hx + off if d > 0 else hx + 9 - off, yy, 2, 1, C(HAZARD[1], 0.85))
    lab = "PASSAGE"
    text(bg, lab, 392 - text_width(lab) // 2 + 20, 300, C("#e8c060", 0.8))
    for k, ax in enumerate((372, 388)):
        bg.poly([(ax, 322), (ax + 8, 326), (ax, 330)], C("#e8c060", 0.75))
    # a parking line where the upper range stops when the crank is turned
    for yy in range(ROW_A - 22, ROW_A + 2, 3):
        bg.rect(398, yy, 2, 2, HAZARD[2])
    # green runner in from the checkout hall along the front aisle, warm light spilling in behind it
    runner_n(bg, 0, 414, 790, 32, pal=CARPET_GREEN, vertical=False)
    for i, a in enumerate((0.1, 0.07, 0.04)):
        bg.rect(0, 392 - i * 8, 20 + i * 12, 76 + i * 16, C("#f6cf7a", a))
    # the service aisle out to the garden: grey concrete, hazard edge, an arrow, cool light
    sx0 = 790
    bg.rect(sx0, 418, W - sx0, 36, "#4a4648")
    rng = np.random.default_rng(12)
    for _ in range(360):
        bg.px(int(rng.integers(sx0, W)), int(rng.integers(418, 454)), "#545052" if rng.random() < 0.6 else "#3e3a3e")
    for x in range(sx0, W, 8):
        bg.rect(x, 416, 4, 2, HAZARD[2]); bg.rect(x + 4, 416, 4, 2, HAZARD[0])
        bg.rect(x, 454, 4, 2, HAZARD[2]); bg.rect(x + 4, 454, 4, 2, HAZARD[0])
    bg.poly([(880, 432), (896, 432), (896, 428), (904, 436), (896, 444), (896, 440), (880, 440)], C("#e6d6b1", 0.55))
    for i, a in enumerate((0.1, 0.07, 0.04)):
        bg.rect(W - 20 - i * 12, 398 - i * 8, 20 + i * 12, 76 + i * 16, C("#a8c8e0", a))
    # a short plum runner from the archive door down to its mat
    runner_n(bg, ARCHIVE[0] - 18, BASE, 36, 54, pal=CARPET_PLUM, vertical=True)
    wx, wt, ww, wh = WINDOW
    moon_patch(bg, wx - 16, BASE + 4, 28, 50, slant=16, strength=0.2)
    # errata slips and pencil shavings on the floor
    for i, (px_, py_) in enumerate([(176, 300), (420, 392), (512, 470), (640, 404), (700, 300), (290, 470), (140, 360)]):
        correction_slip(bg, px_, py_, seed=i + 3)
    for (px_, py_) in [(436, 404), (438, 406), (441, 404)]:
        bg.px(px_, py_, "#d8a868")
    bg.line(586, 486, 594, 482, RED_PENCIL[1]); bg.px(595, 482, "#e6c08a")
    # lamplight on the floor
    light_pool(bg, FLOOR_LAMP[0], FLOOR_LAMP[1] + 3, 46, 13, strength=0.24)
    for lx in LAMPS:
        light_pool(bg, lx, BASE + 6, 34, 8, strength=0.12)
    light_pool(bg, 879, BASE + 8, 30, 8, strength=0.14)
    light_pool(bg, SIGN_X, BASE + 8, 50, 9, strength=0.1)
    depth_shade(bg, 0, 420, W, 120, steps=3, alpha=0.2)
    # margins outside the walkable stacks
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.38))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.38))
    bg.rect(0, WALK[1] + WALK[3], W, H - WALK[1] - WALK[3], C("#0d0b16", 0.42))


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    back_wall(bg)
    floor(bg)
    bg.save(os.path.join(out, "background.png"))
    res = f"res://assets/art/rooms/{ROOM}/"

    props = {}

    def save(index, made, extra=None, name=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(0, stack_shelf(150, 120, seed=31, call="PN 1-9", wheel=-1, label_pos=0.5))
    save(1, stack_shelf(150, 120, seed=32, call="PQ 2", wheel=1))
    save(2, stack_shelf(150, 100, seed=33, call="PR 4", wheel=-1))
    save(3, stack_shelf(150, 100, seed=34, call="PS 3", wheel=1))
    opened = crank_pedestal(70, 60, open_=True)
    opened[0].save(os.path.join(out, "prop-4-open.png"))
    save(4, crank_pedestal(70, 60, open_=False), {"flag": "stacks_shifted", "flag_texture": res + "prop-4-open.png"})
    save(5, sentence_notice(78, 50, "ONE SENTENCE", seed=5))
    save(6, standard_lamp(68))

    # MARKED PASSAGE board: TURN CRANK until the stacks are shifted, then OPEN.
    overlays = []
    for open_, name in ((True, "sign-open.png"), (False, "sign-crank.png")):
        sign = passage_sign(open_)
        sign.save(os.path.join(out, name))
        overlays.append({"texture": res + name, "x": SIGN_X - sign.w // 2, "y": DECK_Y + DECK_H,
                         "flag": "stacks_shifted", "when": open_})
    sw = passage_sign(False).w
    lamp_x = SIGN_X - sw // 2 + (sw // 2 - text_width("TURN CRANK") // 2 + 4) - 8
    lamp_y = DECK_Y + DECK_H + 10 + 18
    layers = [
        # the amber signal lamp blinks while the passage is closed
        {"kind": "blink", "pattern": "10", "rate": 1.6, "flag": "stacks_shifted", "when": False,
         "rects": [[lamp_x - 2, lamp_y, 4, 4, "ffb070"], [lamp_x - 1, lamp_y, 1, 1, "fff0c4"]]},
        {"kind": "twinkle", "points": [[lx, DECK_Y + DECK_H + 12, "fde9b6", 1] for lx in LAMPS] +
                                       [[x + 30, 26, "fde9b6", 1] for k, x in enumerate(range(40, GALLERY_X1 - 20, 150)) if k % 2 == 0] +
                                       [[879, 86, "fde9b6", 1], [FLOOR_LAMP[0], FLOOR_LAMP[1] - 63, "fff0c4", 2]],
         "rate": 1.2, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 16, "rect": [60, 70, 640, 70], "speed": [1, 2], "color": "fde9b6"},
    ]

    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": overlays,
        "fauna": [
            {"kind": "lamp_moth", "x": FLOOR_LAMP[0], "y": FLOOR_LAMP[1] - 66, "range": 6, "speed": 2.0, "rate": 9.0},
            {"kind": "loose_page", "x": 300, "y": 120, "fly": 5.0, "rate": 3.0},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
