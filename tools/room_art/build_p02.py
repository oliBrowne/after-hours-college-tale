"""Pearl Street startup, break room (P02): the back room of the same 1890s block. Back wall, left to
right: the doorway back into the open office (the neon's pink glow and a desk beyond), the snack
wall of gravity bins under a little GOOD VIBES neon, the kombucha kegerator with its three-tap tower
and the chalk ON TAP menu, the stainless fridge papered in stickers, the kitchenette (subway tile,
sink with its WASH IT note, a back window over the alley with the Flatirons black against the last
of the sky, open shelves of mugs, the espresso machine that wants descaling, oat milk) and four
bins, the last one labelled EQUITY. Pine floor with a round jute rug; on it the big orange beanbag
(rest and save), the high-top with two stools, empty kegs, and the office dog asleep in his bed."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from lib_eng import outlet
from lib_umc import halo, soft_ellipse
from p01_lib import (loft_ceiling, brick_wall_p, baseboard, arched_window, flatirons_view, office_glimpse, neon_text,
                     snack_wall, kegerator, chalk_menu, sticker_fridge, counter_run, subway_tile, waste_bins,
                     pine_floor, beanbag_big, high_top, dog_bed, kegs, foosball, thermostat, micro_text, micro_width,
                     NEON_MINT, SHADOW, PINE)

ROOM = "P02"
W, H = 640, 360
BASE = 152
DOOR_X = 64
SNACK = (100, 38, 136, 98)
TAP_X, FRIDGE_X = 300, 372
COUNTER = (410, 150)
WIN_X = 474
NEON_Y = 20


def jute_rug(cv, cx, cy, rx, ry):
    """A round braided jute rug: concentric bands of straw and sand, a dark edge."""
    soft_ellipse(cv, cx + 1, cy + 2, rx, ry, SHADOW, 0.3)
    for i, c in enumerate(["#6a5236", "#9a7a4e", "#b0905c", "#8e6e44", "#a88a58", "#c0a06a", "#9a7a4e", "#b49460"]):
        f = 1 - i / 8
        soft_ellipse(cv, cx, cy, int(rx * f), int(ry * f), c, 1.0)
    for a in np.linspace(0, 2 * np.pi, 60, endpoint=False):           # braid ticks on the outer band
        cv.px(int(cx + np.cos(a) * (rx - 2)), int(cy + np.sin(a) * (ry - 1)), "#544028")


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=51)

    # --- back wall
    brick_wall_p(bg, 0, 16, W, BASE - 16, seed=13)
    loft_ceiling(bg, 0, W, h=16, seed=14)
    for y0, a in [(16, 0.3), (17, 0.18), (18, 0.08)]:
        bg.hline(0, y0, W, C(SHADOW, a))
    baseboard(bg, 0, BASE, W)
    office_glimpse(bg, DOOR_X, BASE)
    bg.rect(DOOR_X + 32, 98, 5, 8, "#e6e2d6"); bg.px(DOOR_X + 34, 100, "#8a8a98")          # light switch
    # snack wall under its neon
    snack_wall(bg, *SNACK, seed=3)
    neon_text(bg, "GOOD VIBES", SNACK[0] + SNACK[2] // 2 - 31, NEON_Y, NEON_MINT, scale=1)
    # kombucha: chalk menu, kegerator and tower
    chalk_menu(bg, TAP_X - 30, 34, 60, 42)
    kegerator(bg, TAP_X, BASE)
    for k in range(4):                                                     # mason jars on top
        jx = TAP_X - 22 + k * 7
        bg.rect(jx, BASE - 46, 5, 8, "#1a1524"); bg.rect(jx + 1, BASE - 45, 3, 6, "#c8d8e0"); bg.rect(jx + 1, BASE - 43, 3, 4, ["#d8a24a", "#c83a6a", "#d8a24a", "#e8e0c8"][k])
    # the sticker fridge, cereal on top
    sticker_fridge(bg, FRIDGE_X, BASE, 42, 92, seed=5)
    for k, c in enumerate(["#e84a3a", "#f2d84a", "#3a8ad8"]):
        bx = FRIDGE_X - 17 + k * 11
        bg.rect(bx, BASE - 104, 10, 13, "#1a1524"); bg.rect(bx + 1, BASE - 103, 8, 11, c); bg.rect(bx + 2, BASE - 100, 6, 3, "#f2f2ea")
    # kitchenette: tile, window over the alley, counter, shelves, sink, espresso
    cx0, cw = COUNTER
    subway_tile(bg, cx0, 84, cw, 36)
    view = flatirons_view(40, 70, seed=6)
    arched_window(bg, WIN_X, 46, 40, 56, view, 0, seed=7)
    counter_run(bg, cx0, BASE, cw, seed=8, shelf_from=96)
    waste_bins(bg, 566, BASE)
    thermostat(bg, 252, 98)
    outlet(bg, 404, 104); outlet(bg, 250, BASE - 16)
    # --- floor
    pine_floor(bg, 0, BASE, W, H - BASE, seed=17)
    bg.rect(0, BASE, W, 2, C(SHADOW, 0.45)); bg.hline(0, BASE + 2, W, C(SHADOW, 0.2))
    jute_rug(bg, 176, 296, 86, 30)
    for cx, cy, rx, ry, c, a in [(176, 250, 110, 50, "#8ef0c8", 0.12), (330, 200, 90, 36, "#f6cf7a", 0.2),
                                 (490, 196, 110, 40, "#f6e0b0", 0.2), (DOOR_X, 176, 50, 20, "#f6cf7a", 0.18),
                                 (420, 290, 90, 36, "#f6cf7a", 0.14)]:
        light_pool(bg, cx, cy, rx, ry, color=c, strength=a)
    # small flat things: a dropped bottle cap, kombucha drips under the tap, a dog toy, a protein bar wrapper
    for k in range(3):
        bg.px(TAP_X - 4 + k * 4, BASE + 4 + (k % 2), "#c8a050")
    bg.ellipse(TAP_X - 6, BASE + 3, 12, 4, C("#a8784a", 0.25))
    bg.rect(520, 300, 8, 4, "#1a1524"); bg.rect(521, 301, 6, 2, "#e84a3a")                          # dog toy (a bone)
    bg.rect(519, 300, 2, 2, "#e84a3a"); bg.rect(527, 300, 2, 2, "#e84a3a"); bg.rect(519, 303, 2, 2, "#e84a3a"); bg.rect(527, 303, 2, 2, "#e84a3a")
    bg.poly([(262, 330), (270, 328), (271, 332), (263, 334)], "#f2d84a"); bg.hline(264, 331, 5, "#a83a2a")
    bg.ellipse(84, 236, 3, 3, "#c8962e")
    # margins
    for x0, w in [(0, 12), (W - 12, 12)]:
        bg.rect(x0, BASE, w, H - BASE, C(SHADOW, 0.35))
    bg.rect(0, H - 18, W, 18, C(SHADOW, 0.45))
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made[:3]
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(1, beanbag_big(54, 40, seed=1))
    save(2, high_top(72, 52, seed=2))
    save(3, dog_bed(44, 22, seed=3))
    save(4, kegs(40, 32, seed=4))
    save(8, foosball(70, 38, seed=5))

    # --- layers: the O in GOOD flickering, the fridge's little light, bubbles in the tap tower
    o_x = SNACK[0] + SNACK[2] // 2 - 31 + 6
    layers = [
        {"kind": "blink", "pattern": "1111111111111111111111111111110101111111111111", "rate": 9.0,
         "rects": [[o_x, NEON_Y - 1, 7, 10, "1e3a30", 0.7]]},
        {"kind": "twinkle", "points": [[TAP_X - 12 + k * 12, BASE - 66, "f2ecdc", 1] for k in range(3)], "rate": 1.8, "min": 0.6},
        {"kind": "particles", "style": "dust", "count": 6, "rect": [TAP_X - 14, BASE - 64, 28, 30], "speed": [0, -4], "color": "f6d68a"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0, 5, 6, 7],
        "fauna": [],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
