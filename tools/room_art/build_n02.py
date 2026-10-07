"""Checkout hall (N02): Norlin's circulation hall at closing time.

Back wall: a painted ceiling edge, warm plaster, four tall round-headed windows onto the night
campus (a library cat asleep on one sill), a regulator clock at two minutes to midnight over a
CIRCULATION board, card catalogues and the returns chute in the oak dado, gilt signs pointing
to the reading room (left) and the stacks (right). Floor: buff and rose marble with a green
runner from the front doors up to the desk and out to both wings, moonlight laid across the
stone under the windows. Props: the checkout desk, two tall bookcases (one with a rolling
ladder), the DUE BACK notice with FOREVER crossed out, a fern in a teal urn, a floor lamp."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from lib_norlin import (plaster_wall, ceiling_band, oak_wainscot, arched_window, wall_sconce, directional_sign,
                        regulator_clock, pendulum_frames, card_catalogue, plaque, marble_floor, runner_n, carpet,
                        moon_patch, checkout_desk, cabochon_floor, floor_inlay, depth_shade, pendant_lamp, bookcase, notice_stand, urn_plant, standard_lamp, wall_shelves,
                        PAGE, OAK, BRASS, CARPET_GREEN, GILT)

ROOM = "N02"
W, H = 800, 480
BASE = 142                          # wall base / top of the walkable floor
WALK = (20, 142, 760, 314)
WINDOWS = [170, 290, 520, 640]      # centre x of the four tall windows
WIN_W, WIN_TOP, WIN_H = 38, 36, 58  # rectangular part; the arch rises WIN_W/2 above WIN_TOP
DADO = 102                          # top of the oak dado
CLOCK_X, CLOCK_TOP = 405, 22
DESK = (405, 315)
PENDANTS = [230, 580]


def back_wall(bg):
    plaster_wall(bg, 0, 10, W, DADO - 10, seed=2)
    ceiling_band(bg, 0, 0, W, 12)
    # pilasters between the window bays
    for px_ in [110, 230, 350, 460, 580, 700]:
        bg.rect(px_ - 5, 12, 10, DADO - 12, "#7e6252"); bg.vline(px_ - 5, 12, DADO - 12, "#9a7c66"); bg.vline(px_ + 4, 12, DADO - 12, "#5e4640")
        bg.rect(px_ - 7, 12, 14, 4, "#8e705c"); bg.hline(px_ - 7, 12, 14, "#a88a72")
    for i, wx in enumerate(WINDOWS):
        arched_window(bg, wx - WIN_W // 2, WIN_TOP, WIN_W, WIN_H, seed=10 + i, view="campus" if i % 2 else "trees",
                      moon=(wx + 6, WIN_TOP - 4) if i == 3 else None)
    for sx in [110, 700]:
        wall_sconce(bg, sx, 66)
    oak_wainscot(bg, 0, DADO, W, BASE - DADO, panel=26)
    # regulator clock over the circulation board, the returns chute beneath
    pivot = regulator_clock(bg, CLOCK_X, CLOCK_TOP, case_h=46, w=26, hour=11, minute=58)
    w = plaque(bg, CLOCK_X - (text_width("CIRCULATION") + 8) // 2, 78, "CIRCULATION")
    for (cx, side) in [(CLOCK_X - 62, -1), (CLOCK_X + 62, 1)]:
        card_catalogue(bg, cx - 22, BASE, w=44, h=36, seed=cx)
    bg.rect(CLOCK_X - 16, 108, 32, 22, OAK[1]); bg.rect(CLOCK_X - 15, 109, 30, 20, BRASS[2]); bg.hline(CLOCK_X - 15, 109, 30, BRASS[4])
    bg.rect(CLOCK_X - 11, 118, 22, 4, "#120c10")
    text(bg, "BOOKS", CLOCK_X - 14, 109, "#3a2418")
    bg.rect(CLOCK_X - 18, 130, 36, 12, OAK[2]); bg.hline(CLOCK_X - 18, 130, 36, OAK[4])
    # low built-in shelves in the dado under the outer windows
    for wx in (WINDOWS[0], WINDOWS[3]):
        wall_shelves(bg, wx - 34, 112, 68, 26, seed=wx, shelf=13, dim=0.15, frame=True)
    # directional signs at both ends
    directional_sign(bg, 26, 30, "READING ROOM", arrow="left")
    w = text_width("STACKS >") + 10
    directional_sign(bg, W - 26 - w, 30, "STACKS", arrow="right")
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))
    # pendant lanterns hanging in front of the pilasters either side of the clock bay
    for lx in PENDANTS:
        pendant_lamp(bg, lx, 58, chain_top=0, r=6)
    return pivot


def floor(bg):
    cabochon_floor(bg, 0, BASE, W, H - BASE, seed=5, size=36, border=(6, "#3e2a2a"))
    floor_inlay(bg, 44, 166, W - 88, 270, t=5)
    # moonlight from the four windows, slanting across the stone
    for wx in WINDOWS:
        moon_patch(bg, wx - 18, BASE + 4, 36, 40, slant=18)
    # green runners: front doors to the desk, and out to both wings; a rug under the desk
    carpet(bg, 286, 252, 238, 76, pal=CARPET_GREEN, seed=8, motif=14)
    runner_n(bg, 380, 328, 40, H - 328, vertical=True)
    runner_n(bg, 0, 291, 286, 18, vertical=False)
    runner_n(bg, 524, 291, W - 524, 18, vertical=False)
    # the hall darkens toward the front doors and the corners, away from the lamps
    depth_shade(bg, 0, 360, W, 120, steps=3, alpha=0.24)
    # warm pools: desk lamp, floor lamp, the pendants and sconces
    light_pool(bg, DESK[0] - 70, DESK[1] + 4, 60, 14, strength=0.2)
    light_pool(bg, 120, 393, 46, 13, strength=0.24)
    for sx in [110, 700]:
        light_pool(bg, sx, BASE + 6, 30, 7, strength=0.12)
    for lx in PENDANTS:
        light_pool(bg, lx, BASE + 30, 50, 14, strength=0.16)
    # a dropped return slip and a pencil by the desk
    bg.rect(318, 340, 9, 6, PAGE[3]); bg.hline(319, 342, 6, PAGE[0]); bg.hline(319, 344, 4, PAGE[0])
    bg.line(470, 345, 478, 341, "#c47a2c"); bg.px(479, 341, "#2a2026")
    # margins outside the walkable hall, and light from the two wings spilling in at the sides
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.38))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.38))
    bg.rect(0, WALK[1] + WALK[3], W, H - WALK[1] - WALK[3], C("#0d0b16", 0.42))
    for x0 in (0, W - 20):
        for i, a in enumerate((0.1, 0.07, 0.04)):
            bg.rect(x0 if x0 == 0 else x0 - i * 10, 270 - i * 6, 20 + i * 10, 60 + i * 12, C("#f6cf7a", a))


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    pivot = back_wall(bg)
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

    def return_slip(cv, x, y, w, h):
        # DUE BACK: WHEN YOU ARE DONE, with FOREVER struck through by another hand
        cv.hline(x + 3, y + 3, w - 8, PAGE[0])
        text(cv, "FOREVER", x + (w - text_width("FOREVER")) // 2, y + 5, "#7a6a5a")
        cv.hline(x + (w - text_width("FOREVER")) // 2 - 1, y + 9, text_width("FOREVER"), "#c84a3c")
        cv.line(x + 4, y + 12, x + w - 6, y + 11, "#3a4a7a")

    save(0, checkout_desk(180, 52, seed=3))
    save(1, bookcase(130, 112, seed=11, ladder=True))
    save(2, bookcase(130, 112, seed=12))
    save(3, urn_plant(56, 44, seed=13))
    save(4, notice_stand(64, 48, "DUE BACK", seed=14, body=return_slip))
    save(5, standard_lamp(68))

    # Pendulum frames for the regulator clock: left, middle, right, middle.
    px_, py_, bob_y = pivot
    layers = []
    patterns = ["1000", "0101", "0010"]
    for k, (fr, ox) in enumerate(pendulum_frames(bob_y - py_, swing=3)):
        name = f"pendulum-{k}.png"
        fr.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": patterns[k], "rate": 2.0,
                       "texture": f"res://assets/art/rooms/{ROOM}/{name}", "x": px_ - ox, "y": py_})
    glows = [[sx, 58, "fde9b6", 1] for sx in [110, 700]] + [[lx, 58, "fff0c4", 2] for lx in PENDANTS]
    glows += [[DESK[0] - 68, DESK[1] - 40, "fff0c4", 1], [120, 390 - 63, "fff0c4", 1]]
    layers.append({"kind": "twinkle", "points": glows, "rate": 1.3, "min": 0.55})

    manifest = {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "fauna": [
            {"kind": "library_cat", "x": WINDOWS[1] + 4, "y": WIN_TOP + WIN_H + 1, "range": 0, "speed": 0.0, "rate": 0.5},
        ],
        "leaves": [[wx - WIN_W // 2 + 2, WIN_TOP - 10, WIN_W - 4, WIN_H] for wx in (WINDOWS[0], WINDOWS[2])],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
