"""Farrand Hall second floor (D02): the long hallway on move-in day, scrolling two screens wide.
Red brick wainscot under a sandstone chair rail, cream block, acoustic ceiling with frosted drum
lights, speckled linoleum with an oxblood border. Left to right: the hall window over a radiator,
room 214 (Jules and Jakerson, tags already up, Jakerson's boxes outside), the drinking fountain,
212, the RA's WELCOME HOME board, the RA's own door 210, the class photo and a bench, 208 standing
open on a lamp-lit room, the study lounge with its TV, 206, 204 and the fire door to the stairs.
Floormates' things everywhere: a move-in cart, a FREE mini fridge, a guitar case, laundry, a bike."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from lib_eng import micro_text, exit_sign, outlet
from lib_umc import extinguisher, soft_ellipse, halo
from lib_oldmain import radiator, framed_photo
from d02_lib import (acoustic_soffit, hall_wall, drum_light, dorm_door, stair_door, hall_window, lounge_opening,
                     drinking_fountain, pull_station, thermostat, light_switch, wall_shadow, ra_board, lino_floor,
                     doormat, sneakers, pizza_box, skateboard, dropped_tag, move_in_cart, mini_fridge, box_stack,
                     guitar_case, laundry_pile, leaning_bike, hall_bench, hall_poster, room_sign, packing_peanuts, CPAPER, FH_BLOCK, SHADOW, OUT)

ROOM = "D02"
W, H = 1280, 360
BASE = 158                       # foot of the back wall (top of the walk bounds)
NEAR = 318                       # top of the near wall's cut edge
LAMPS = (100, 360, 620, 880, 1140)
LAMP_Y = 242                     # floor point under each drum light (the game puts a real light here)

# doors along the back wall: (centre x, number, tags, deco, ajar)
DOORS = [
    (150, "214", [("JULES", CPAPER[6], "mountain", "#8aa8e0"), ("JAKERSON", CPAPER[0], "ball", None)], ("pennant",), False),
    (322, "212", [("NOOR", CPAPER[3], "star", "#e8c24a"), ("BEX", CPAPER[2], "heart", "#c84a3c")], ("whiteboard",), False),
    (606, "210", [("RA MIKA", CPAPER[4], "star", "#e8c24a")], ("calendar", "lights"), False),
    (760, "208", [], (), True),
    (1000, "206", [("LENA", CPAPER[5], "sun", "#e8c24a"), ("ROSIE", CPAPER[1], "note", "#2a2030")], ("hanger", "whiteboard"), False),
    (1100, "204", [("OWEN", CPAPER[2], "buff", None), ("MARCO", CPAPER[3], "mountain", "#9ccf6a")], ("poster",), False),
]
STAIRS_X = 1210
LOUNGE_X = 880


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=21)

    # --- back wall
    hall_wall(bg, 0, W, BASE, top=12, seed=4)
    acoustic_soffit(bg, 0, W, y=0, h=12, seed=5)
    hall_window(bg, 30, 34, 36, 70, seed=7, moon=(56, 44, 3))
    radiator(bg, 31, 122, 34, 28)
    tv = lounge_opening(bg, LOUNGE_X, BASE, seed=8)
    for k, (cx, num, tags, deco, ajar) in enumerate(DOORS):
        dorm_door(bg, cx, BASE, num, tags, deco, seed=10 + k, ajar=ajar)
    stair_door(bg, STAIRS_X, BASE, label="STAIRS")
    exit_sign(bg, STAIRS_X + 24, BASE - 80)              # beside the frame, clear of the label pill
    notes = ra_board(bg, 392, 30, 150, 66, seed=3, ra="MIKA", room="210")
    drinking_fountain(bg, 236, BASE)
    framed_photo(bg, 652, 44, 42, 30, seed=5, rows=3, caption="FARRAND 1949")
    pull_station(bg, 1168, 86); light_switch(bg, 186, 100); light_switch(bg, 978, 100); thermostat(bg, 556, 104)
    hall_poster(bg, 920, 58, seed=2)
    room_sign(bg, 1132, 30)
    extinguisher(bg, 1048, 134)
    for ox in (260, 470, 700, 940, 1170):
        outlet(bg, ox, 142)
    for cx in LAMPS:
        drum_light(bg, cx, 12)

    # --- floor
    lino_floor(bg, 0, BASE, W, NEAR - BASE, seed=6, stripe=(226, 240))
    wall_shadow(bg, 0, BASE, W)
    # the near wall's cut edge, then darkness below it
    bg.rect(0, NEAR, W, 2, FH_BLOCK[6]); bg.hline(0, NEAR + 2, W, FH_BLOCK[3])
    bg.rect(0, NEAR + 3, W, H - NEAR - 3, "#1c1824")
    for xx in range(0, W, 16):
        bg.vline(xx + (8 if (xx // 16) % 2 else 0), NEAR + 3, 7, "#221d2c")
    bg.hline(0, NEAR + 10, W, "#221d2c")
    # warm pools under the drum lights, a pale wear path down the middle
    for cx in LAMPS:
        light_pool(bg, cx, LAMP_Y, 112, 46, strength=0.3)
    soft_ellipse(bg, W // 2, 246, 600, 26, "#e0c8a8", 0.05)
    # spill from the open door of 208 and the lounge TV
    bg.poly([(742, BASE), (778, BASE), (800, BASE + 46), (722, BASE + 46)], C("#f6cf7a", 0.13))
    bg.poly([(748, BASE), (772, BASE), (786, BASE + 26), (736, BASE + 26)], C("#f6cf7a", 0.10))
    bg.poly([(LOUNGE_X - 24, BASE), (LOUNGE_X + 24, BASE), (LOUNGE_X + 38, BASE + 30), (LOUNGE_X - 38, BASE + 30)], C("#8ab0f0", 0.07))
    # doormats and flat clutter (nothing on the floor stands up)
    for cx, word, col in [(150, "HI", "#5c4a3a"), (322, None, "#3a4a5a"), (606, "RA", "#6a3a3a"), (1000, None, "#4a5a3a"),
                          (1100, None, "#5a4a5a")]:
        doormat(bg, cx, BASE + 2, w=32, h=9, colour=col, word=word)
    sneakers(bg, 966, BASE + 6, colour="#e6e2d6", accent="#c84a3c")
    sneakers(bg, 336, BASE + 13, colour="#2a2a36", accent="#e8c24a")
    pizza_box(bg, 846, 270)
    skateboard(bg, 1052, 290)
    dropped_tag(bg, 512, 290, "TY", CPAPER[5])
    packing_peanuts(bg, 226, 258, seed=3)
    # dark margins at the ends of the hall and along the bottom
    for x0, w in [(0, 12), (W - 12, 12)]:
        bg.rect(x0, BASE, w, NEAR - BASE, C(SHADOW, 0.35))
    bg.rect(0, NEAR - 10, W, 10, C(SHADOW, 0.18))
    bg.save(os.path.join(out, "background.png"))

    # --- props (placement index -> sprite)
    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(2, move_in_cart(64, 58, seed=1))
    save(3, box_stack(40, 44, labels=("JAKERSON", "TENNIS"), seed=2))
    save(4, mini_fridge(26, 36, seed=3))
    save(5, guitar_case(18, 50, seed=4))
    save(6, laundry_pile(36, 24, seed=5))
    save(7, leaning_bike(54, 34, seed=6))
    save(8, hall_bench(72, 30, seed=7))

    # --- animated layers: the lounge TV flickers, RA door lights twinkle, one drum light hums
    tx, ty, tw, th = tv
    layers = [
        {"kind": "blink", "pattern": "1101001110", "rate": 5.0, "rects": [[tx, ty, tw, th, "a8c4f0", 0.5]]},
        {"kind": "blink", "pattern": "0010110001", "rate": 5.0, "rects": [[tx, ty, tw, th, "e07a5a", 0.35]]},
        {"kind": "twinkle", "points": [[606 - 21 + i * 4, BASE - 72 - 19, "f6cf7a", 1] for i in range(11)], "rate": 1.4, "min": 0.3},
        {"kind": "blink", "pattern": "11111111111101111111111111110101", "rate": 6.0,
         "rects": [[LAMPS[3] - 14, 13, 29, 9, "141223", 0.35]]},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0, 1] + list(range(9, 9 + len(LAMPS))),
        "fauna": [{"kind": "lamp_moth", "x": LAMPS[1] + 4, "y": 34, "range": 10, "speed": 1.4, "rate": 9.0}],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
