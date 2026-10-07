"""Farrand Hall dorm room (D01): move-in day, where the game's new intro starts.

A 1950s Farrand double seen from the middle of the room, an hour before sunset in late August.
Back wall: painted cinder block under a ceiling band, the door out to the hallway on the left (fire
plan, coat hook with a lanyard), and in the middle a wide steel casement window looking west at the
Flatirons with the low sun just right of the slabs, the green campus and red tile roofs below; a
convector under the sill. The sun throws a long gold patch across the vinyl tile toward the left,
with the window bars printed in it.
Left half (Jules, arriving today): a bare blue dorm mattress with folded sheets and a bagged pillow,
an empty hutch, a lamp still in its carton, an empty corkboard with the RA's welcome note and the
paper door star with both names, old tape marks, and moving boxes and a duffel on the floor.
Right half (Jakerson, moved in yesterday): string lights, a SET POINT tennis poster, his racket on
two hooks, a BOULDER pennant, photos on a twine line, a made bed with a racket bag on the throw, a
desk with a glowing laptop and a lamp, his hoodie on the chair, a braided rug, a pothos on the
sill, a wardrobe with a suitcase on top, a mini-fridge with a microwave.
Layers: the string lights twinkle, dust drifts in the sunbeam, the laptop cursor blinks.
"""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
import d01_lib as L

ROOM = "D01"
W, H = 640, 360
WALL = 134                       # foot of the back wall = top of the floor
WIN = (244, 26, 152, 70)         # window glass x, y, w, h
DOOR = (36, 60, 44, 74)          # door leaf x, y, w, h (bottom on the wall foot)
# placement floor points (see drafts/D01.json)
BED_J, BED_K = (122, 206), (518, 206)
DESK_J, DESK_K = (190, 160), (450, 160)
CHAIR_J, CHAIR_K = (176, 176), (466, 180)
LAMP = (428, 161)
WARDROBE = (594, 164)
BOXES, DUFFEL, FRIDGE = (238, 254), (104, 304), (592, 256)
FAN, BEANBAG, CART = (304, 200), (568, 326), (330, 334)
RUG = (494, 282, 64, 26)


def paint_background():
    bg = Canvas(W, H, fill="#171a2b", seed=4)
    # back wall
    L.block_wall(bg, 0, 8, W, WALL - 8, seed=2)
    L.ceiling_band(bg, 0, W)
    L.smoke_detector(bg, 320, 1)
    L.cove_base(bg, 0, WALL, W)
    # window, sill and the convector under it
    wx, wy, ww, wh = WIN
    sill = L.casement_window(bg, wx, wy, ww, wh, seed=3)
    L.convector(bg, wx + 4, sill + 9, ww - 8, WALL - sill - 13)
    L.sill_plants(bg, wx + ww - 44, sill + 1)
    # a stack of two library books and a phone charger on Jules's end of the sill
    bg.rect(wx - 2, sill - 4, 16, 4, "#3a5a8a"); bg.rect(wx, sill - 7, 13, 3, "#c84a3c"); bg.hline(wx, sill - 7, 13, "#e06a5a")
    # the door to the hallway, a light switch, a doormat (flat) in front of it
    dx, dy, dw, dh = DOOR
    L.dorm_door(bg, dx, dy, dw, dh)
    L.light_switch(bg, dx + dw + 8, dy + 30)
    # Jules's wall: corkboard over the bed, tape scars where last year's posters were
    L.corkboard_welcome(bg, 99, 42, 46, 38)
    L.wall_scars(bg, [(164, 22, "tape"), (196, 30, "tape"), (214, 18, "nail"), (150, 92, "tack"), (230, 112, "nail")])
    L.thermostat(bg, 222, 84)
    # Jakerson's wall: pennant, poster, racket, photos, string lights, a gig poster over the wardrobe
    L.pennant(bg, 420, 30, label="BOULDER")
    L.tennis_poster(bg, 492, 26)
    L.wall_racket(bg, 538, 56)
    L.photo_strip(bg, 494, 88)
    L.band_poster(bg, 572, 14)
    bulbs = L.string_lights(bg, 416, 14, 560, 14, sag=10, every=7, seed=5)
    bulbs += L.string_lights(bg, 560, 14, 630, 22, sag=4, every=7, seed=6)

    # floor
    L.vct_floor(bg, 0, WALL, W, H - WALL, seed=9)
    bg.rect(0, WALL, W, 2, C("#0d0b16", 0.45))
    # the sun through the window: a long gold patch thrown left across the tile, bars printed in it
    patch = [(wx + 6, WALL + 2), (wx + ww - 4, WALL + 2), (wx + ww - 96, WALL + 112), (wx - 92, WALL + 112)]
    L.light_patch(bg, patch, colour="#ffc870", alpha=0.14)
    inner = [(wx + 14, WALL + 6), (wx + ww - 12, WALL + 6), (wx + ww - 92, WALL + 104), (wx - 80, WALL + 104)]
    L.light_patch(bg, inner, colour="#ffd080", alpha=0.15)
    core = [(wx + 40, WALL + 12), (wx + ww - 40, WALL + 12), (wx + ww - 100, WALL + 90), (wx - 40, WALL + 90)]
    L.light_patch(bg, core, alpha=0.1)
    for frac in (0.25, 0.75):
        x_top = wx + 6 + int((ww - 10) * frac)
        bg.line(x_top, WALL + 3, x_top - 92, WALL + 111, C("#2a1a24", 0.35))
        bg.line(x_top + 1, WALL + 3, x_top - 91, WALL + 111, C("#2a1a24", 0.25))
    bg.line(wx - 30, WALL + 64, wx + ww - 62, WALL + 64, C("#2a1a24", 0.22))
    # the shaft through the air, very faint, so dust has something to float in
    bg.poly([(wx + 10, wy + 4), (wx + ww - 6, wy + 4), (wx + ww - 96, WALL + 100), (wx - 80, WALL + 100)], C("#ffe0a0", 0.035))

    # Jakerson's braided rug; a coir mat at the door
    L.braided_rug(bg, *RUG, seed=1)
    bg.rect(dx - 2, WALL + 4, dw + 4, 10, C("#0d0b16", 0.4)); bg.rect(dx - 1, WALL + 3, dw + 2, 9, "#8a6a42")
    for mx in range(dx, dx + dw, 2):
        bg.vline(mx, WALL + 4, 7, "#a8844e" if mx % 4 else "#6e5434")
    # flat clutter on Jules's side: a flattened box, packing paper, tape, a box cutter
    bg.poly([(150, 318), (196, 312), (204, 330), (156, 336)], L.CARD[3]); bg.line(150, 318, 196, 312, L.CARD[5])
    bg.line(160, 326, 196, 321, L.CARD[2]); bg.hline(170, 316, 10, L.TAPE[1])
    for (px, py) in [(212, 300), (220, 306), (70, 262)]:
        bg.ellipse(px, py, 9, 5, "#e6e0d0"); bg.px(px + 3, py + 1, "#b8b0a0"); bg.px(px + 5, py + 3, "#b8b0a0")
    bg.hline(276, 286, 14, C(L.TAPE[2], 0.8)); bg.hline(277, 287, 12, C(L.TAPE[0], 0.8))
    bg.rect(284, 300, 8, 2, "#e8b45c"); bg.rect(292, 300, 3, 2, "#a8a8b0")
    # a stray tennis ball and Jakerson's slides by the rug
    bg.ellipse(400, 316, 5, 5, "#d8e040"); bg.px(401, 317, "#f2f8a0"); bg.px(403, 319, "#a8b030")
    for sx in (548, 557):
        bg.rect(sx, 314, 7, 3, "#24222f"); bg.hline(sx, 314, 7, "#3a5a8e")
    # warm pool under the desk lamp
    light_pool(bg, LAMP[0] + 4, 176, 34, 10, strength=0.16)
    # dark margins outside the walkable room and the near wall's shadow
    for x0, w in [(0, 14), (W - 14, 14)]:
        bg.rect(x0, WALL, w, H - WALL, C("#0d0b16", 0.35))
    bg.rect(0, H - 12, W, 12, C("#0d0b16", 0.5))
    return bg, bulbs


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg, bulbs = paint_background()
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        props[str(index)] = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}

    save(1, L.dorm_bed(made=False, seed=1))
    save(2, L.desk_hutch("jules", seed=2))
    save(3, L.desk_chair(seed=3))
    save(4, L.desk_hutch("jakerson", seed=4))
    save(5, L.desk_chair(seed=5, hoodie=True))
    save(6, L.desk_lamp())
    save(7, L.dorm_bed(made=True, seed=7))
    save(8, L.wardrobe(seed=8))
    save(9, L.box_stack(seed=9))
    save(10, L.duffel_pile(seed=10))
    save(11, L.mini_fridge(seed=11))
    save(12, L.box_fan(seed=12))
    save(13, L.bean_bag(seed=13))
    save(14, L.movein_cart(seed=14))

    # laptop cursor: the desk sprite's anchor is (31, 99); the laptop's last text row ends at
    # sprite (30, 61), so the cursor sits just after it
    cur_x, cur_y = DESK_K[0] - 31 + 31, DESK_K[1] - 99 + 61
    manifest = {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0],
        "fauna": [],
        "leaves": [],
        "layers": [
            {"kind": "twinkle", "points": bulbs, "rate": 1.6, "min": 0.45},
            {"kind": "particles", "style": "dust", "count": 16, "rect": [170, 40, 200, 190], "speed": [-2, 3], "color": "fff0c4"},
            {"kind": "blink", "pattern": "10", "rate": 1.6, "rects": [[cur_x, cur_y, 2, 1, "f6cd78"]]},
        ],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
