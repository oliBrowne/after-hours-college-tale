"""Reading room (N03): Norlin's great reading room after closing.

Back wall: a painted ceiling edge; floor-to-cornice built-in shelves between three tall
round-headed windows (the great window in the middle, an owl on its outside ledge), window seats
under them, two green-glass pendant lamps, an old loudspeaker high on the right (it plays Imani's
polished demo), a QUIET plaque, a sign pointing back to the checkout hall, and on the left the
glazed garden door with the margin garden lit beyond. Floor: oak parquet with a great plum carpet
under the reading tables, moonlight from the windows laid across it, runners to both exits.
Props: three long reading tables with green banker's lamps (the bookmark NEXT on one, a
reel-to-reel listening station with headphones on another), a bookcase whose open book is
written over in two inks, two cushioned benches and a floor lamp.
Keepsake spot (60, 334) is left as clear parquet."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from lib_norlin import (plaster_wall, ceiling_band, arched_window, built_in_shelves, window_seat, garden_door,
                        shade_pendant, wall_speaker, directional_sign, plaque, parquet_floor, carpet, runner_n,
                        moon_patch, depth_shade, reading_table, reel_deck, headphones, bookmark_card, open_book,
                        book_stack, marked_bookcase, library_bench, standard_lamp, OAK, PAGE, CARPET_PLUM,
                        LAMP_GREEN, GILT)

ROOM = "N03"
W, H = 800, 480
BASE = 142
WALK = (20, 142, 760, 314)
DOOR = (100, BASE)                                   # garden door, threshold mat at (100, 190)
WINDOWS = [(262, 40, 56, 72), (400, 64, 52, 76), (538, 40, 56, 72)]   # (cx, w, top of rect, h)
PENDANTS = [324, 476]
SPEAKER = (692, 42)
KEEPSAKE = (60, 334)
RUG = ["#1e1018", "#2e1622", "#45202e", "#4e2434", "#62303e", "#b07a46", "#d8a868"]   # plum, low-contrast lattice


def back_wall(bg):
    plaster_wall(bg, 0, 12, W, BASE - 12, seed=3, shadow_top=10)
    ceiling_band(bg, 0, 0, W, 14)
    # windows with seats beneath
    for i, (cx, w, top, h) in enumerate(WINDOWS):
        arched_window(bg, cx - w // 2, top, w, h, seed=30 + i, view="trees" if i != 1 else "campus",
                      moon=(cx + 14, top - 14) if i == 1 else None)
        window_seat(bg, cx - w // 2 - 4, top + h + 6, w + 8, BASE - (top + h + 6))
    # built-in shelving between the windows, floor to cornice
    built_in_shelves(bg, 148, 28, 80, BASE, seed=41, ladder_x=200)
    built_in_shelves(bg, 300, 28, 48, BASE, seed=42)
    built_in_shelves(bg, 452, 28, 48, BASE, seed=43)
    built_in_shelves(bg, 574, 28, 80, BASE, seed=44)
    built_in_shelves(bg, 676, 76, 80, BASE, seed=45)
    # the garden door and its sign
    garden_door(bg, DOOR[0], DOOR[1], w=40, h=74, seed=7, label="GARDEN")
    # QUIET over the left shelves, the loudspeaker and the way back to the checkout hall on the right
    qw = text_width("QUIET") + 8
    plaque(bg, 188 - qw // 2, 30, "QUIET")
    wall_speaker(bg, SPEAKER[0], SPEAKER[1], w=20, h=26)
    bg.line(SPEAKER[0] + 20, SPEAKER[1] + 14, SPEAKER[0] + 30, SPEAKER[1] + 14, "#1a1820")
    bg.vline(SPEAKER[0] + 30, SPEAKER[1] + 14, 18, "#1a1820")
    lab = "CHECKOUT HALL"
    w = text_width(lab + " >") + 10
    directional_sign(bg, W - 22 - w, 22, lab, arrow="right")
    for lx in PENDANTS:
        shade_pendant(bg, lx, 64, chain_top=12, w=22)
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))


def floor(bg):
    parquet_floor(bg, 0, BASE, W, H - BASE, seed=9, block=16)
    carpet(bg, 136, 168, 536, 282, pal=RUG, seed=11, motif=20)
    # moonlight from the three windows, slanting down to the right
    for (cx, w, top, h) in WINDOWS:
        big = w > 50
        moon_patch(bg, cx - w // 2 + 4, BASE + 6, w - 8, 92 if big else 60, slant=34 if big else 24, strength=0.24 if big else 0.16)
    # runners: in from the garden door, out to the checkout hall on the right
    runner_n(bg, 82, BASE, 36, 52, pal=CARPET_PLUM, vertical=True)
    runner_n(bg, 672, 391, W - 672, 18, pal=CARPET_PLUM, vertical=False)
    depth_shade(bg, 0, 384, W, 96, steps=3, alpha=0.22)
    # lamplight around the tables and the floor lamp
    for (x, y, w) in [(230, 294, 130), (480, 334, 170), (390, 225, 150)]:
        light_pool(bg, x, y - 6, w // 2 + 14, 13, strength=0.16)
    light_pool(bg, 98, 333, 24, 8, strength=0.18)
    for lx in PENDANTS:
        light_pool(bg, lx, BASE + 20, 40, 10, strength=0.1)
    # a pencil and a dropped index card on the carpet
    bg.line(330, 372, 338, 368, "#c47a2c"); bg.px(339, 368, "#2a2026")
    bg.rect(612, 300, 9, 6, PAGE[3]); bg.hline(613, 302, 6, "#a83a32"); bg.hline(613, 304, 4, PAGE[0])
    # margins outside the walkable room; warm light from the checkout hall spilling in at the right
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.38))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.38))
    bg.rect(0, WALK[1] + WALK[3], W, H - WALK[1] - WALK[3], C("#0d0b16", 0.42))
    for i, a in enumerate((0.1, 0.07, 0.04)):
        bg.rect(W - 20 - i * 10, 370 - i * 6, 20 + i * 10, 60 + i * 12, C("#f6cf7a", a))


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    back_wall(bg)
    floor(bg)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    def bookmark(cv, ox, top_y, width):
        # an open book with the bookmark NEXT (and a blank line) laid across it
        open_book(cv, ox + 70, top_y + 2, 18, 7, seed=5)
        bookmark_card(cv, ox + 84, top_y + 1, "NEXT")
        book_stack(cv, ox + 14, top_y + 10, 14, n=3, seed=6)

    def listening(cv, ox, top_y, width):
        # the listening station: reel-to-reel deck, headphones, two tapes (one hand-labelled)
        reel_deck(cv, ox + 100, top_y + 10)
        headphones(cv, ox + 74, top_y + 8, cord_to=(ox + 100, top_y + 7))
        for k, (lab_col, x0) in enumerate((("#e6d6b1", ox + 140), ("#c84a3c", ox + 152))):
            cv.rect(x0 - 1, top_y + 2, 11, 8, "#1a1418"); cv.rect(x0, top_y + 3, 9, 6, "#3a3440")
            cv.rect(x0 + 1, top_y + 4, 7, 2, lab_col)
        cv.line(ox + 141, top_y + 5, ox + 147, top_y + 5, "#2a3a6a")

    save(0, reading_table(130, 38, lamps=1, seed=21, clutter=False, extra=bookmark))
    save(1, reading_table(170, 38, lamps=1, seed=22, clutter=False, extra=listening))
    save(2, reading_table(150, 38, lamps=2, seed=23))
    save(3, marked_bookcase(100, 100, seed=24))
    save(4, library_bench(90, 30, seed=25, cushion="#4a2030"))
    save(5, library_bench(100, 30, seed=26, cushion="#4a2030"))
    save(6, standard_lamp(68))

    rng = np.random.default_rng(3)
    stars = []
    for (cx, w, top, h) in WINDOWS:
        for _ in range(3):
            stars.append([int(cx - w // 2 + 3 + rng.integers(0, w - 6)), int(top - w // 4 + rng.integers(0, h // 2)), "c8d0f0", 0])
    layers = [
        {"kind": "twinkle", "points": [[lx, 66, "fde9b6", 2] for lx in PENDANTS] + [[118, 104, "fde9b6", 1]],
         "rate": 1.2, "min": 0.6},
        {"kind": "twinkle", "points": stars, "rate": 0.8, "min": 0.0},
        {"kind": "particles", "style": "dust", "count": 14, "rect": [372, 60, 110, 170], "speed": [1.5, 2.5],
         "color": "d8dcf0"},
    ]

    manifest = {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "fauna": [
            {"kind": "barn_owl", "x": 416, "y": 127, "range": 0, "speed": 0.0, "rate": 1.5},
            {"kind": "lamp_moth", "x": 98, "y": 268, "range": 6, "speed": 2.0, "rate": 9.0},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
