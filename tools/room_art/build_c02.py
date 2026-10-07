"""CU Book Store (C02), inside the UMC off the Fountain Court, open late in the first week of term.
Back wall, left to right: the TEXTBOOKS wall (black metal bays by department, rows of loud glossy
textbooks, yellow USED stickers, white price strips); the Buffs gear wall (black slatwall, caps,
face-out hoodies in black, gold, heather and white round the gold buffalo plaque, GO BUFFS, a #1
jersey, folded tees on the bottom shelf); the CHECKOUT lightbox over maple cubbies of mugs, bottles
and plush Ralphies, the store hours plaque, a clock and the STAFF ONLY door. A charcoal carpet runs
under the textbook aisles, warm porcelain tile everywhere else, pools of light under the ceiling
cans, a GO BUFFS mat inside the open front doors at the bottom edge (back out to the court).
Props: the two aisle gondolas, the tee table, a round rack of hoodies, the plush bin, the checkout
counter with its register, a sticker spinner, a SELL YOUR BOOKS chalkboard."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel import Canvas, C
from surfaces import light_pool
from lib_eng import wall_clock, outlet
from lib_umc import soft_ellipse
from lib_umc2 import lightbox
import c02_lib as L

ROOM = "C02"
W, H = 800, 480
BASE = 150                       # wall meets floor
CANS = (70, 190, 330, 470, 610, 730)
DOOR_X, DOOR_TOP = 400, 448      # the open front doors in the bottom edge (exit to C01)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=21)

    # --- back wall and ceiling
    L.store_wall(bg, 0, 12, W, BASE - 12, seed=3)
    L.store_ceiling(bg, 0, W, h=12, cans=CANS)
    # textbooks, left
    L.header_sign(bg, 130, 15, "TEXTBOOKS")
    L.textbook_wall(bg, 14, 34, 232, BASE - 34 - 4, depts=("MATH", "CHEM", "PHYS", "WRTG"), seed=5)
    # the gear wall, centre
    L.header_sign(bg, 407, 14, "BUFFS GEAR")
    L.gear_wall(bg, 262, 32, 290, 114, seed=7)
    # checkout, right: lightbox, cubbies behind the counter, hours, clock, camera, staff door
    lightbox(bg, 600, 16, 86, 16, "CHECKOUT", face="#f2e8c8", ink="#2a2430")
    L.cubby_wall(bg, 580, 46, 125, 78, cols=5, rows=3, seed=2)
    L.hours_plaque(bg, 708, 70)
    wall_clock(bg, 722, 40, r=7)
    L.dome_camera(bg, 562, 12)
    L.staff_door(bg, 762, BASE, w=34, h=68)
    outlet(bg, 258, 132); outlet(bg, 568, 132)

    # --- floor
    L.store_floor(bg, 0, BASE, W, H - BASE, seed=9)
    L.carpet_zone(bg, 12, BASE, 258, 244, seed=4)
    L.wall_shadow(bg, 0, BASE, W)
    L.entry_mat(bg, DOOR_X, 392, w=84, h=22, label="GO BUFFS")
    # light: pools under the cans, a warm wash at the counter, the gear wall's glow on the tile
    for cx, cy, rx, ry, a in [(70, 214, 70, 26, 0.18), (190, 226, 70, 26, 0.18), (330, 236, 80, 30, 0.22),
                              (470, 236, 80, 30, 0.22), (610, 232, 76, 28, 0.2), (730, 226, 66, 26, 0.18),
                              (650, 300, 100, 34, 0.16), (400, 360, 150, 50, 0.1)]:
        light_pool(bg, cx, cy, rx, ry, strength=a)
    soft_ellipse(bg, 407, 172, 150, 14, "#e6d29a", 0.05)
    # flat things on the floor: a dropped receipt, a price tag, a gold sticker, tape on the tile
    bg.rect(520, 404, 6, 9, "#f2ecdc"); bg.hline(521, 406, 4, "#a8a49c"); bg.hline(521, 408, 3, "#a8a49c")
    bg.rect(286, 238, 4, 3, L.STICKER)
    bg.rect(700, 378, 5, 3, "#f6f4ee"); bg.px(704, 379, "#3a3a4a")
    bg.rect(596, 330, 28, 2, C("#e8b45c", 0.8)); bg.rect(596, 330, 2, 10, C("#e8b45c", 0.8))      # queue tape
    bg.rect(704, 330, 28, 2, C("#e8b45c", 0.8)); bg.rect(730, 330, 2, 10, C("#e8b45c", 0.8))
    # margins: dark at the sides; the bottom edge with the open front doors
    for x0, w in [(0, 12), (W - 12, 12)]:
        bg.rect(x0, BASE, w, H - BASE, C(L.SHADOW, 0.35))
    L.storefront(bg, 460, W, DOOR_X, door_w=64)
    L.doorway_gap(bg, DOOR_X, DOOR_TOP, H, w=64)
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

    save(1, L.gondola(170, 78, rows=3, header="AISLE 1", sub="TEXTBOOKS", used=0.2, seed=1))
    save(2, L.gondola(170, 62, rows=2, header="AISLE 2", sub="USED BOOKS", used=0.75, seed=2))
    save(3, L.tee_table(104, 36, seed=3))
    save(4, L.round_rack(66, 62, seed=4))
    save(5, L.plush_bin(50, 38, seed=5))
    save(6, L.checkout_counter(164, 54, seed=6))
    save(7, L.spinner_rack(32, 62, seed=7))
    save(12, L.bargain_bin(58, 34, seed=12))
    save(8, L.chalk_aframe(50, 48, header="SELL", lines=(("YOUR", "#f2ecdc"), ("BOOKS", L.GOLD[4])), seed=8))

    # --- animated layers: the camera's red light, the cans breathing, dust in the light
    layers = [
        {"kind": "blink", "pattern": "10000000", "rate": 2.0, "rects": [[563, 15, 1, 1, "ff6a5a"]]},
        {"kind": "twinkle", "points": [[c, 11, "fff0c4", 1] for c in CANS], "rate": 0.7, "min": 0.75},
        {"kind": "particles", "style": "dust", "count": 14, "rect": [280, 20, 260, 120], "speed": [1, 3], "color": "f6e8c0"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [9, 10, 11],
        "fauna": [{"kind": "umc2_mouse", "x": 778, "y": 172, "range": 10, "speed": 0.5, "rate": 4.0}],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
