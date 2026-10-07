"""Inside the party (H02): the living room of the XI OMEGA LAMBDA house (fictional) on a Friday.

Back wall, left to right: the staircase taped off at the bottom (NO PARTY UPSTAIRS) with coats
spilling out of the closet under it, the bay window onto College Ave, a house composite, the brick
fireplace with the letters over the mantel and cups in the firebox, another composite, the kitchen
doorway packed with silhouettes, then the DJ corner: FALL BASH bedsheet, the TV running a
visualiser, a neon Flatirons sign, LED tape along the crown, a disco ball. Worn oak floor with
cups, confetti, glow sticks and coloured light. The middle of the floor, from the front door at the
bottom edge up to the fireplace, is left clear for Tanner's couch entrance and the crowd."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from interior import crown, plank_floor
from props import OUT, IRON, AMBER
from lib_farrand2 import confetti, glow_stick
from d02_lib import doormat, pizza_box, sneakers
from h01_lib import CUP, SHADOW, HOUSE_B, cup_flat
from h02_lib import (party_rug, shoe_pile, GREEN_WALL, OAK, party_wall, oak_wainscot, led_strip, staircase, bay_window, fireplace_mantel,
                     composite_frame, kitchen_opening, wall_tv, bedsheet, leather_couch, pong_table, dj_table,
                     speaker_stand, recliner, bean_bag, cup_tower_bin, snack_table, floor_lamp_h)

ROOM = "H02"
W, H = 800, 480
BASE = 152
WAIN = 34
STAIR_X = 176
WINDOW = (196, 30, 120, 84)
FIRE_X = 410
KITCHEN_X = 506
DISCO = (596, 46)


def neon_flatirons(cv, x, y, colour="#ff6ab4"):
    """A neon sign on the DJ wall: three Flatiron slabs in pink tube on a black backer.
    Returns the tube pixels for the buzzing layer."""
    cv.rect(x - 3, y - 3, 66, 36, OUT); cv.rect(x - 2, y - 2, 64, 34, "#100e16")
    tubes = []
    for (px, pw, ph) in [(4, 18, 22), (18, 22, 28), (36, 20, 20)]:
        a, b, c = (x + px, y + 28), (x + px + pw // 2, y + 28 - ph), (x + px + pw, y + 28)
        for p, q in [(a, b), (b, c)]:
            n = max(abs(q[0] - p[0]), abs(q[1] - p[1]))
            for i in range(n + 1):
                xx = round(p[0] + (q[0] - p[0]) * i / n); yy = round(p[1] + (q[1] - p[1]) * i / n)
                tubes.append((xx, yy))
    for (xx, yy) in tubes:
        cv.rect(xx - 1, yy - 1, 3, 3, C(colour, 0.18))
    for (xx, yy) in tubes:
        cv.px(xx, yy, colour)
    cv.hline(x + 2, y + 29, 56, "#4ae0f0")
    return tubes


def disco_ball(cv, cx, cy, r=7):
    cv.vline(cx, 0, cy - r, "#3a3848")
    cv.ellipse(cx - r - 1, cy - r - 1, r * 2 + 3, r * 2 + 3, OUT)
    cv.ellipse(cx - r, cy - r, r * 2 + 1, r * 2 + 1, "#8a8ea8")
    for yy in range(cy - r, cy + r + 1, 2):
        for xx in range(cx - r, cx + r + 1, 2):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                c = "#e6e8f4" if (xx + yy) % 4 == 0 else "#5a5e78" if xx > cx else "#b8bcd0"
                cv.px(xx, yy, c)
    cv.px(cx - 3, cy - 3, "#ffffff")
    return [(cx - 3, cy - 3), (cx + 2, cy - 4), (cx - 4, cy + 2), (cx + 1, cy + 1), (cx + 4, cy - 1)]


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=29)
    rng = np.random.default_rng(29)

    # --- back wall
    party_wall(bg, 0, 6, W, BASE - WAIN - 6, seed=3, rail=20)
    crown(bg, 0, 0, W)
    oak_wainscot(bg, 0, BASE - WAIN, W, WAIN)
    newel_top, landing = staircase(bg, STAIR_X, BASE, steps=12, run=12, rise=8, seed=4)
    bay_window(bg, *WINDOW, seed=5)
    composite_frame(bg, 326, 36, 28, 40, seed=6)
    fireplace_mantel(bg, FIRE_X, BASE, seed=7)
    composite_frame(bg, 468, 36, 28, 40, seed=8)
    kitchen_opening(bg, KITCHEN_X, BASE, w=76, h=92, seed=9)
    # DJ corner
    led_strip(bg, 592, W, 6)
    bedsheet(bg, 604, 18, 96, 30, seed=10)
    tv = wall_tv(bg, 650, 62, 64, 36)
    tubes = neon_flatirons(bg, 726, 26)
    # light switch, an outlet with too many plugs, a thermostat set to 85 out of spite
    bg.rect(186, 96, 5, 8, "#e6e0d2"); bg.rect(187, 99, 3, 2, "#a8a090")
    bg.rect(590, 128, 8, 10, "#e6e0d2"); bg.rect(591, 131, 2, 2, OUT); bg.rect(595, 131, 2, 2, OUT)
    for k in range(3):
        bg.line(592 + k * 2, 138, 600 + k * 9, BASE + 4, "#0e0c14")
    bg.rect(480, 92, 10, 12, "#e6e0d2"); bg.rect(482, 95, 6, 4, "#3a5a3a")
    ball = disco_ball(bg, *DISCO)
    # string lights along the banister and across the head of the bay window
    from lib_farrand import festoon
    twinkles = festoon(bg, newel_top[0], newel_top[1] + 2, landing[0] + 4, landing[1] - 40, sag=10, every=7, seed=5,
                       colours=["#f6cf7a", "#ff8ad0", "#f6cf7a", "#6ad8f0"])
    twinkles += festoon(bg, WINDOW[0] - 6, WINDOW[1] - 8, WINDOW[0] + WINDOW[2] + 6, WINDOW[1] - 8, sag=12, every=8, seed=6)

    # --- floor
    plank_floor(bg, 0, BASE, W, H - BASE, seed=11)
    bg.rect(0, BASE, W, 3, C(SHADOW, 0.45))
    # a dance-worn patch in the middle (scuffed finish), a rolled rug against the wainscot
    for _ in range(260):
        x = int(rng.normal(400, 70)); y = int(rng.normal(372, 34))
        if BASE < y < H - 20:
            bg.hline(x, y, int(rng.integers(2, 6)), C("#c8a07a", 0.18))
    bg.rect(318, BASE - 12, 4, 12, OUT)
    party_rug(bg, 136, 288, 270, 112, seed=14)
    shoe_pile(bg, 300, 440, seed=15); shoe_pile(bg, 446, 446, seed=16)
    # coloured light: pink from the DJ corner, cyan from the window, amber under the lamp, the kitchen green
    for (cx, cy, rx, ry, c, a) in [(680, 300, 170, 60, "#ff6ab4", 0.16), (256, 230, 120, 30, "#6ad8f0", 0.1),
                                   (168, 222, 60, 20, "#ffb0d0", 0.2), (544, 176, 60, 18, "#6ad8a0", 0.16),
                                   (FIRE_X, 168, 50, 12, "#ff9a4a", 0.14), (400, 380, 120, 46, "#a07aff", 0.1)]:
        light_pool(bg, cx, cy, rx, ry, color=c, strength=a)
    # disco dots across the walls and floor
    dots = []
    for _ in range(60):
        x = int(rng.integers(10, W - 10)); y = int(rng.integers(12, H - 30))
        c = ["#ffd0ec", "#c8f4ff", "#fff0c4"][int(rng.integers(3))]
        bg.rect(x, y, 2, 2, C(c, 0.35))
        dots.append([x, y, c.lstrip("#"), 2])
    # flat party debris on the floor (kept off the props' feet)
    confetti(bg, 300, 300, 220, 140, n=160, seed=12)
    confetti(bg, 560, 250, 200, 140, n=90, seed=13)
    for k, (x, y) in enumerate([(310, 248), (452, 262), (366, 298), (520, 248), (612, 290), (700, 330), (98, 360),
                                (180, 400), (468, 410), (300, 444), (640, 420), (742, 380), (40, 250), (540, 446)]):
        cup_flat(bg, x, y, tipped=(k % 3 != 0), seed=k)
    for k, (x, y) in enumerate([(150, 260), (430, 344), (700, 410)]):
        bg.ellipse(x, y, 3, 3, "#f6f2e6")                                   # ping-pong balls that got away
    glow_stick(bg, 470, 330, "#7af08a", seed=1); glow_stick(bg, 342, 412, "#ff7ad0", seed=2); glow_stick(bg, 620, 380, "#7ad8ff", seed=3)
    pizza_box(bg, 52, 400)
    sneakers(bg, 210, 156, colour="#e6e2d6", accent="#3a6ac8")
    for (x, y, rx, ry) in [(380, 314, 9, 3), (512, 404, 12, 3), (140, 312, 8, 2)]:
        bg.ellipse(x, y, rx * 2, ry * 2, C("#3a1a14", 0.35)); bg.hline(x + 3, y + 1, rx, C("#c87a5a", 0.3))   # sticky spills
    # the front door's threshold at the bottom edge: the inside of the front wall, the mat, light from the porch
    bg.rect(0, H - 20, W, 20, C(SHADOW, 0.55))
    bg.rect(400 - 34, H - 22, 68, 22, C("#f0a0c8", 0.12))
    doormat(bg, 400, H - 24, w=56, h=12, colour="#4a3a30")
    from h01_lib import greek_small
    greek_small(bg, HOUSE_B, 400 - 14, H - 23, "#8a7462", gap=2)
    for x0, w in [(0, 10), (W - 10, 10)]:
        bg.rect(x0, BASE, w, H - BASE, C(SHADOW, 0.35))
    bg.save(os.path.join(out, "background.png"))

    # --- props
    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made[:3]
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(2, leather_couch(124, 46, seed=2))
    save(3, pong_table(124, 44, seed=3))
    save(4, dj_table(110, 50, seed=4))
    save(5, speaker_stand(30, 66, seed=5))
    save(6, speaker_stand(30, 66, seed=6))
    save(7, floor_lamp_h(64))
    save(8, cup_tower_bin(26, 36, seed=8))
    save(9, recliner(46, 42, seed=9))
    save(10, snack_table(84, 36, seed=10))
    save(11, bean_bag(42, 26, seed=11))
    from interior import folding_chairs, potted_plant
    save(12, folding_chairs(56, 38, count=2, seed=3))
    save(13, potted_plant(40, 52, seed=13))

    # --- animated layers
    tx, ty, tw, th = tv
    bars = []
    for f in range(4):
        rects = [[tx, ty, tw, th, "10121e", 1.0]]
        for k in range(9):
            bh = int(6 + 24 * abs(np.sin(f * 1.3 + k * 0.9)))
            c = ["ff6ab4", "a07aff", "4ae0f0"][k % 3]
            rects.append([tx + 3 + k * 7, ty + th - 3 - bh, 5, bh, c, 1.0])
        bars.append({"kind": "blink", "pattern": "".join("1" if j == f else "0" for j in range(4)), "rate": 5.0, "rects": rects})
    buzz = {"kind": "blink", "pattern": "1111111111110111111111111111101111", "rate": 9.0,
            "rects": [[x, y, 1, 1, "100e16", 0.7] for (x, y) in tubes[::2]]}
    led = [{"kind": "blink", "pattern": p, "rate": 2.0, "rects": [[592 + k * 69, 6, 69, 1, c, 1.0]]}
           for k, (p, c) in enumerate([("100", "ff6ab4"), ("010", "a07aff"), ("001", "4ae0f0")])]
    beams = [
        {"kind": "beam", "x": 640, "y": 160, "angle": 160, "sweep": 22, "period": 6.5, "phase": 0.0,
         "length": 330, "width": 70, "color": "ff6ab4", "alpha": 0.16, "floor": 380},
        {"kind": "beam", "x": 720, "y": 160, "angle": 150, "sweep": 26, "period": 8.0, "phase": 2.1,
         "length": 380, "width": 70, "color": "4ae0f0", "alpha": 0.14, "floor": 400},
    ]
    layers = bars + [buzz] + led + beams + [
        {"kind": "twinkle", "points": [[x, y, "ffffff", 1] for (x, y) in ball], "rate": 4.0, "min": 0.0},
        {"kind": "twinkle", "points": dots, "rate": 1.6, "min": 0.0},
        {"kind": "twinkle", "points": twinkles, "rate": 1.8, "min": 0.4},
        {"kind": "twinkle", "points": [[newel_top[0], newel_top[1], "ffb0d0", 1]], "rate": 1.0, "min": 0.6},
        # the crowd in the kitchen bobbing: a rim of light that flickers on and off their shoulders
        {"kind": "blink", "pattern": "1010110", "rate": 3.0, "rects": [[KITCHEN_X, BASE - 40, 76, 2, "6ad8a0", 0.5]]},
        {"kind": "particles", "style": "dust", "count": 16, "rect": [520, 20, 260, 200], "speed": [0, 3], "color": "ffd0ec"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [1],
        "fauna": [],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
