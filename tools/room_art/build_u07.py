"""Lost property (U07): a warm, cluttered claim room in the UMC's lower level, just off the
Connection. Ochre distemper over the club room's dark wainscot; a rail of unclaimed coats, a FOUND
board, a board of lost keys and the room's three verbs (SORT / RETURN / RELEASE) under a big enamel
sign; the claim hatch with its roller shutter and NOW SERVING board on the right over a counter of
labelled bins; a hung-up bicycle nobody came back for. Worn cream-and-oxblood vinyl, taped sorting
zones, and the arcade carpet of the Connection through the doorway at the bottom. Pip's table is
drawn by code; the coat rack (CLAIM) stands in front of the counter."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import light_pool
from props import OUT, IRON
from interior import PANEL, crown, wainscot, wall_clock
from lib_umc import (OCHRE, VINYL, KRAFT, PAPER, BRASS, SHADOW, SAFETY, ITEM_COLOURS,
                     ochre_wall, vinyl_floor, floor_tape_box, coat_hooks, claim_hatch, now_serving, found_board,
                     worn_mat, halo, soft_ellipse, enamel_sign, cable, gooseneck, light_cone, key_board,
                     process_placard, umbrella_stand, wall_shelf_boxes, wall_bicycle, arcade_carpet,
                     cubby_shelf, steel_shelving, low_cubbies, bin_counter, sorting_table, ticket_spool,
                     fringed_lamp, waiting_seats)

ROOM = "U07"
W, H = 800, 480
WALL_BASE = 122          # walk_bounds top
DADO_TOP = 98
FLOOR_END = 457          # walk_bounds bottom: below it the front wall-top
DOOR = (360, 436)        # placement 0 threshold (code draws the mat): the doorway to the Connection
HATCH = (672, 34, 72, 44)   # claim hatch: centre x, top, w, h (over the bin counter, placement 9)
NOW = (580, 30)          # NOW SERVING board
LAMP = (650, 371)        # placement 6
PIP = (150, 283)         # placement 4 (code)
CLAIM = (660, 212)       # the coat rack enemy (code)
KEEPSAKE = (60, 322)     # pickup spot: keep clear


def paint_wall(bg):
    ochre_wall(bg, 0, 0, W, DADO_TOP, seed=7)
    # ceiling edge and crown moulding, the club room's wainscot below
    bg.rect(0, 0, W, 5, "#1e1620"); bg.hline(0, 4, W, "#2c2028")
    crown(bg, 0, 5, W)
    wainscot(bg, 0, DADO_TOP, W, WALL_BASE - DADO_TOP, seed=3)
    bg.rect(0, WALL_BASE - 3, W, 3, PANEL[1]); bg.hline(0, WALL_BASE - 3, W, PANEL[3])
    lamps = []

    # left: a rail of unclaimed coats, bags and scarves, a COATS card
    coat_hooks(bg, 24, 192, 34, seed=4)
    bg.rect(26, 22, 34, 10, PAPER[2]); text(bg, "COATS", 27, 21, "#7e3a30")
    lamps.append(gooseneck(bg, 104, 22, reach=12))

    # FOUND board with photos of unclaimed things, and a typed list of what is kept how long
    found_board(bg, 210, 26, 78, 50, seed=5)
    lamps.append(gooseneck(bg, 244, 14, reach=10))
    bg.rect(296, 48, 16, 24, C(SHADOW, 0.4)); bg.rect(295, 47, 16, 24, PAPER[3])
    for k in range(6):
        bg.hline(297, 50 + k * 3, 12 - (k * 5) % 5, "#6a5a50")
    text(bg, "90", 296, 60, "#7e3a30")
    bg.px(302, 47, "#c84a3c")

    # centre: the big LOST PROPERTY sign, the board of keys, the three verbs
    label = "LOST PROPERTY"
    sw = text_width(label) + 22
    sx = 400 - sw // 2
    bg.rect(sx - 2, 11, sw + 4, 19, OUT)
    bg.rect(sx - 1, 12, sw + 2, 17, BRASS[2]); bg.hline(sx - 1, 12, sw + 2, BRASS[4]); bg.hline(sx - 1, 28, sw + 2, BRASS[0])
    bg.rect(sx + 1, 14, sw - 2, 13, "#7e3a30"); bg.hline(sx + 1, 14, sw - 2, "#9a4a39"); bg.hline(sx + 1, 26, sw - 2, "#5e2a26")
    text(bg, label, 400 - text_width(label) // 2 + 1, 15, "#2a1418")
    text(bg, label, 400 - text_width(label) // 2, 14, PAPER[3])
    for bx in (sx + 4, sx + sw - 5):
        bg.px(bx, 20, BRASS[4])
    lamps.append(gooseneck(bg, 334, 30, reach=10))
    lamps.append(gooseneck(bg, 452, 30, reach=-10))
    glints = key_board(bg, 322, 40, 58, 50, seed=6)
    process_placard(bg, 394, 40, 76, 42)
    wall_clock(bg, 486, 46, r=7)

    # a shelf of past terms' boxes, an umbrella stand and a hung-up bicycle nobody came back for
    wall_shelf_boxes(bg, 492, 64, 84, seed=3)
    umbrella_stand(bg, 540, WALL_BASE - 1, seed=2)
    wall_bicycle(bg, 718, 22)

    # against the wainscot: a stack of boxes waiting to be sorted, a basket of odd socks
    for (bx, bw, bh, by) in [(292, 26, 16, WALL_BASE), (296, 20, 13, WALL_BASE - 16), (322, 18, 12, WALL_BASE)]:
        bg.rect(bx, by - bh, bw, bh, OUT); bg.rect(bx + 1, by - bh + 1, bw - 2, bh - 1, KRAFT[2])
        bg.hline(bx + 1, by - bh + 1, bw - 2, KRAFT[4]); bg.vline(bx + bw - 2, by - bh + 1, bh - 1, KRAFT[1])
        bg.rect(bx + bw // 2 - 1, by - bh + 1, 3, bh - 1, C(KRAFT[0], 0.5))
    text(bg, "?", 300, WALL_BASE - 14, "#7e3a30")
    bg.rect(462, WALL_BASE - 14, 26, 14, OUT); bg.rect(463, WALL_BASE - 13, 24, 12, KRAFT[3])
    for k in range(464, 487, 3):
        bg.vline(k, WALL_BASE - 12, 10, KRAFT[1])
    for (sx, c) in [(465, "#5c897c"), (471, "#c47a2c"), (476, "#e6d6b1"), (481, "#8a4a6a")]:
        bg.rect(sx, WALL_BASE - 18, 4, 6, OUT); bg.rect(sx + 1, WALL_BASE - 17, 2, 5, c)
    bg.hline(463, WALL_BASE - 13, 24, KRAFT[4])
    # claim hatch over the bin counter, NOW SERVING beside it, an arrow to the ticket spool
    cx, top, w, h = HATCH
    claim_hatch(bg, cx, top, w, h)
    digits = now_serving(bg, NOW[0], NOW[1], "07")
    text(bg, "TAKE A", NOW[0] + 3, NOW[1] + 28, PAPER[2])
    text(bg, "NUMBER", NOW[0] + 3, NOW[1] + 38, PAPER[2])
    bg.rect(NOW[0] + 1, NOW[1] + 52, 30, 2, PAPER[2]); bg.poly([(NOW[0] + 31, NOW[1] + 49), (NOW[0] + 36, NOW[1] + 53), (NOW[0] + 31, NOW[1] + 57)], PAPER[2])

    # light: the shelf lights' wedges down the wall, the hatch's warm spill
    for (lx, ly) in lamps:
        light_cone(bg, lx, ly, 3, 22, 54, alpha=0.05)
        halo(bg, lx, ly, 9, strength=0.1)
    halo(bg, cx, top + h // 2 + 6, 44, colour="#f6cf7a", strength=0.06)
    return lamps, glints, digits


def paint_floor(bg):
    wear = [(DOOR[0], 420, 40, 22), (380, 300, 70, 20), (560, 220, 90, 20), (660, 160, 70, 14),
            (300, 200, 60, 16), (150, 230, 50, 14)]
    vinyl_floor(bg, 0, WALL_BASE, W, FLOOR_END - WALL_BASE, seed=9, tile=16, wear=wear)
    bg.rect(0, WALL_BASE, W, 3, C(SHADOW, 0.5)); bg.hline(0, WALL_BASE + 3, W, C(SHADOW, 0.25))
    # the three taped zones in front of the sorting table
    for (x, wz, lab) in [(268, 56, "SORT"), (330, 62, "RETURN"), (398, 66, "RELEASE")]:
        floor_tape_box(bg, x, 362, wz, 18, label=lab)
    # a mat under the waiting seats
    worn_mat(bg, 674, 356, 96, 34)
    # light pools: shelf lights at the wall, the hatch, out-of-view pendants, the lamp
    light_pool(bg, HATCH[0], WALL_BASE + 30, 80, 22, strength=0.24)
    for (px, py) in [(116, 150), (254, 150), (400, 152)]:
        light_pool(bg, px, py, 40, 10, strength=0.14)
    for (px, py) in [(400, 230), (140, 330), (560, 330), (300, 420)]:
        light_pool(bg, px, py, 56, 14, strength=0.12)
    light_pool(bg, LAMP[0], LAMP[1], 60, 17, strength=0.3)
    # things that fell out of pockets: a single mitten, a sock, a claim ticket, a bus pass
    for (fx, fy, kind) in [(234, 318, "mitten"), (470, 248, "sock"), (588, 300, "ticket"), (312, 168, "pass"),
                           (746, 278, "ticket"), (726, 284, "ticket")]:
        if kind == "mitten":
            bg.rect(fx, fy, 7, 5, OUT); bg.rect(fx + 1, fy + 1, 5, 3, "#c47a2c"); bg.rect(fx + 6, fy - 1, 3, 3, OUT); bg.px(fx + 7, fy, "#c47a2c")
            bg.hline(fx + 1, fy + 3, 5, PAPER[2])
        elif kind == "sock":
            bg.rect(fx, fy, 9, 3, OUT); bg.rect(fx + 1, fy + 1, 7, 1, "#5c897c"); bg.rect(fx + 7, fy + 1, 3, 4, OUT); bg.px(fx + 8, fy + 2, "#5c897c")
        elif kind == "ticket":
            bg.rect(fx, fy, 6, 3, PAPER[3]); bg.px(fx + 1, fy + 1, "#c84a3c"); bg.px(fx + 1, fy + 3, C(SHADOW, 0.4))
        else:
            bg.rect(fx, fy, 9, 6, "#2c5a8a"); bg.rect(fx + 1, fy + 1, 3, 3, PAPER[2]); bg.hline(fx + 5, fy + 2, 3, PAPER[2])
            bg.px(fx + 1, fy + 6, C(SHADOW, 0.4))
    # cool plum shade gathering in the corners and toward the front wall
    for (hh, a) in [(40, 0.08), (22, 0.08), (10, 0.1)]:
        bg.rect(0, FLOOR_END - hh, W, hh, C("#2a1a3a", a))
    for (ww, a) in [(46, 0.07), (26, 0.08)]:
        bg.rect(18, WALL_BASE, ww, FLOOR_END - WALL_BASE, C("#2a1a3a", a))
        bg.rect(782 - ww, WALL_BASE, ww, FLOOR_END - WALL_BASE, C("#2a1a3a", a))
    # the lamp's flex runs to a socket in the wainscot behind the counter's end
    cable(bg, [(LAMP[0] + 3, LAMP[1] - 1), (672, 360), (700, 338), (770, 330), (781, 322)], "#16141f", hi="#6c6a88")
    bg.rect(779, 318, 3, 6, IRON[3])


def wall_top(bg, x, y, w, h, inner="top"):
    bg.rect(x, y, w, h, "#1e1820")
    rng = np.random.default_rng(x * 3 + y)
    for _ in range(w * h // 28):
        bg.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), "#2a2228")
    if inner == "left":
        bg.vline(x, y, h, OCHRE[4]); bg.vline(x + 1, y, h, OCHRE[2])
    elif inner == "right":
        bg.vline(x + w - 1, y, h, OCHRE[4]); bg.vline(x + w - 2, y, h, OCHRE[2])
    else:
        bg.hline(x, y, w, OCHRE[4]); bg.hline(x, y + 1, w, OCHRE[2])


def paint_frame(bg):
    """Side and front wall-tops; the doorway to the Connection is a gap at the bottom showing its
    arcade carpet and the pink-and-teal glow of the lanes."""
    dx = DOOR[0]
    arcade_carpet(bg, dx - 34, FLOOR_END, 68, H - FLOOR_END, seed=3)
    wall_top(bg, 0, FLOOR_END, dx - 36, H - FLOOR_END, "top")
    wall_top(bg, dx + 36, FLOOR_END, W - dx - 36, H - FLOOR_END, "top")
    for xx in (dx - 37, dx + 34):
        bg.rect(xx, FLOOR_END, 3, H - FLOOR_END, PANEL[3]); bg.vline(xx + (2 if xx > dx else 0), FLOOR_END, H - FLOOR_END, PANEL[5])
    wall_top(bg, 0, WALL_BASE - 1, 18, FLOOR_END - WALL_BASE + 1, "right")
    wall_top(bg, 782, WALL_BASE - 1, 18, FLOOR_END - WALL_BASE + 1, "left")
    # a little of the lanes' glow spills in through the doorway
    light_pool(bg, dx, FLOOR_END - 6, 46, 12, color="#ff9ac0", strength=0.1)
    bg.rect(18, FLOOR_END - 8, dx - 54, 8, C(SHADOW, 0.25)); bg.rect(dx + 36, FLOOR_END - 8, 782 - dx - 36, 8, C(SHADOW, 0.25))


def hatch_states(out):
    """Overlays for the claim hatch after the coat rack is answered: peaceful = shutter rolled all
    the way up, a returned coat and a ticked slip on the ledge; forceful = shutter pulled down and
    padlocked with a CLOSED card."""
    cx, top, w, h = HATCH
    x0, y0 = cx - w // 2 - 6, top - 6
    for name, kw in [("peaceful", dict(shutter=0.08, state="peaceful")), ("forceful", dict(shutter=1.0))]:
        ov = Canvas(w + 12, h + 12)
        claim_hatch(ov, cx - x0, top - y0, w, h, **kw)
        ov.save(os.path.join(out, f"hatch-{name}.png"))
    return (x0, y0)


def now_texture(out, number):
    t = Canvas(34, 10)
    t.rect(0, 0, 34, 10, "#140a10")
    text(t, number, 11, 0, "#ff5a4a")
    t.save(os.path.join(out, f"now-{number}.png"))


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=7)
    lamps, glints, digits = paint_wall(bg)
    paint_floor(bg)
    paint_frame(bg)
    bg.save(os.path.join(out, "background.png"))
    hx, hy = hatch_states(out)
    now_texture(out, "08")

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made[:3]
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(1, cubby_shelf(84, 116, seed=11))
    save(2, steel_shelving(78, 111, seed=12))
    save(3, sorting_table(132, 53, seed=13))
    save(5, ticket_spool(42, 68, seed=14))
    save(6, fringed_lamp(65))
    save(7, waiting_seats(82, 34))
    save(8, low_cubbies(114, 62, seed=15))
    save(9, bin_counter(150, 48, seed=16))

    res = f"res://assets/art/rooms/{ROOM}/"
    dx, dy, dw, dh = digits
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": [
            {"texture": res + "hatch-peaceful.png", "x": hx, "y": hy, "flag": "claim_resolution", "equals": "peaceful"},
            {"texture": res + "hatch-forceful.png", "x": hx, "y": hy, "flag": "claim_resolution", "equals": "forceful"},
        ],
        "fauna": [
            {"kind": "umc_moth", "x": LAMP[0] + 1, "y": LAMP[1] - 66, "range": 8, "speed": 1.5, "rate": 9.0},
        ],
        "leaves": [],
        "layers": [
            # NOW SERVING ticks over to 08 and back while nobody comes
            {"kind": "blink", "pattern": "0000000011111111", "rate": 0.8, "texture": res + "now-08.png", "x": dx, "y": dy},
            # the lost keys catch the shelf light
            {"kind": "twinkle", "points": [[x, y, "fff0c4", 1] for (x, y) in glints], "rate": 1.7, "min": 0.15},
            # the shelf lights breathe
            {"kind": "twinkle", "points": [[x, y, "f6cf7a", 1] for (x, y) in lamps], "rate": 1.1, "min": 0.6},
            # dust turning in the hatch light
            {"kind": "particles", "style": "dust", "count": 9, "rect": [HATCH[0] - 40, 40, 80, 70], "speed": [2, -3], "color": "f6e0b0"},
        ],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
