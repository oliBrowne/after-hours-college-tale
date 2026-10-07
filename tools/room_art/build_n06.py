"""Closed archive (N06): the vault behind the stacks where INDEX files every possible future.

Back wall: the painted ceiling edge over sandstone; floor-to-cornice card-index walls at both ends
(a rolling ladder on the left), two tall moonlit windows, and in the middle the closed archive
itself - a locked lattice grille in a limestone surround, boxed files fading into the dark behind
it, chained and padlocked, under the enamelled plaque POSSIBLE LIVES / CLOSED ARCHIVE. A row of
oak ceremony chairs waits in front of the grille, roped with a red sash and a RESERVED card; a
stack of spare folding chairs leans by the pier. INDEX's intake - a glass pneumatic tube with
brass collars dropping cards into a heaped wire hopper - stands at the right-hand pier.
Floor: warm grey stone flags, a brass catalogue rose let into the floor where INDEX stands,
fallen index cards trailing from the cabinets, a plum runner along the front between the exits
(warm stacks light in from the left, the playback room's green glow from the right, roped off
until INDEX is settled), moonlight from the windows.
Props: two tall index cabinets, the sorting table with the ledger of reserved seats, a steel
archive shelf of boxed files and a floor lamp."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from props import OUT, IRON
from lib_norlin import (floor_inlay, ceiling_band, stone_wall, quoins, arched_window, runner_n, depth_shade, standard_lamp, library_ladder,
                        shade_pendant, wall_sconce, moon_patch, OAK, PAGE, BRASS, GILT, STONE_N, LIME, CARPET_PLUM)
from lib_norlin2 import (index_wall, index_wall_slots, drawer_out, index_cabinet, archive_shelf, sorting_table, reserved_chairs,
                         chair_stack, two_line_plaque, archive_cage, card_chute, index_rose, floor_cards, velvet_rope,
                         tile_floor, VAULT, SASH)

ROOM = "N06"
W, H = 800, 480
BASE = 142
WALK = (20, 142, 760, 314)
STONE = [shade(c, -0.12) for c in STONE_N]       # the archive's sandstone, as seen from the stacks
INDEX_L = (24, 30, 129)                         # index wall: x, top, width (3 banks)
INDEX_R = (686, 30, 85)                         # (2 banks)
CAGE = (312, 56, 176)                           # closed archive grille: x, top, width
WINDOWS = [230, 630]                            # tall windows (centre x)
WIN_TOP, WIN_W, WIN_H = 40, 30, 58
CHUTE_X = 556                                   # INDEX's intake tube
PENDANTS = [282, 518]
LAMP = (95, 315)                                # floor lamp placement
INDEX_SPOT = (480, 345)
RUNNER = (400, 26)                              # front runner between the exits: top y, height
ROPE = (762, 376)                               # rope across the playback room exit (sprite top-left)


def back_wall(bg):
    stone_wall(bg, 0, 12, W, BASE - 12, pal=STONE, seed=8, course=6)
    ceiling_band(bg, 0, 0, W, 12)
    # card-index walls at both ends, a rolling ladder on the left one
    for (x, top, w) in (INDEX_L, INDEX_R):
        index_wall(bg, x, top, w, BASE, seed=x, open_rate=0.035)
    library_ladder(bg, 128, INDEX_L[1] - 2, BASE)
    quoins(bg, INDEX_L[0] + INDEX_L[2] + 4, 24, BASE - 4, "left", pal=LIME)
    quoins(bg, INDEX_R[0] - 4, 24, BASE - 4, "right", pal=LIME)
    # tall windows over the two free-standing cabinets
    for i, wx in enumerate(WINDOWS):
        arched_window(bg, wx - WIN_W // 2, WIN_TOP, WIN_W, WIN_H, seed=20 + i, view="campus",
                      moon=(wx + 6, WIN_TOP - 4) if i == 0 else None)
    # the closed archive and its plaque
    cx, ctop, cw = CAGE
    archive_cage(bg, cx, ctop, cw, BASE, seed=3)
    two_line_plaque(bg, cx + cw // 2, 15, ["POSSIBLE LIVES", "CLOSED ARCHIVE"], fg=GILT, bg="#1c1622", frame=BRASS)
    # the ceremony: reserved chairs waiting in front of the grille, spare chairs stacked by the pier
    reserved_chairs(bg, 355, BASE, n=5, cw=18, seed=2)
    chair_stack(bg, 280, BASE, n=4)
    # INDEX's intake tube and hopper at the right pier, a few cards fallen at its feet
    card_chute(bg, CHUTE_X, 12, BASE, label="INTAKE")
    # lamps
    for px_ in PENDANTS:
        shade_pendant(bg, px_, 62, chain_top=12, w=16)
    for sx in (WINDOWS[0] - 34, WINDOWS[1] + 34):
        wall_sconce(bg, sx, 88)
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))


def floor(bg):
    tile_floor(bg, 0, BASE, W, H - BASE, seed=6, pal=VAULT, tw=32, th=18)
    floor_inlay(bg, 30, BASE + 10, W - 60, WALK[1] + WALK[3] - BASE - 18, t=3, colour="#3a2c2e", line="#a8844e")
    # a shadow line where the flags meet the wall
    bg.rect(0, BASE, W, 3, C("#0d0b16", 0.35)); bg.rect(0, BASE + 3, W, 2, C("#0d0b16", 0.15))
    # the brass catalogue rose where INDEX keeps its station
    index_rose(bg, INDEX_SPOT[0], INDEX_SPOT[1] - 6, rx=52, ry=17)
    # plum runner along the front between the two exits
    ry, rh = RUNNER
    runner_n(bg, 0, ry, W, rh, pal=CARPET_PLUM, vertical=False)
    for i, a in enumerate((0.1, 0.07, 0.04)):
        bg.rect(0, ry - 18 - i * 8, 20 + i * 12, rh + 36 + i * 16, C("#f6cf7a", a))
        bg.rect(W - 20 - i * 12, ry - 18 - i * 8, 20 + i * 12, rh + 36 + i * 16, C("#9ad8b0", a))
    # moonlight from the windows, lamplight
    for wx in WINDOWS:
        moon_patch(bg, wx - 18, BASE + 6, 30, 46, slant=18, strength=0.2)
    light_pool(bg, LAMP[0], LAMP[1] + 3, 46, 13, strength=0.24)
    for px_ in PENDANTS:
        light_pool(bg, px_, BASE + 8, 36, 9, strength=0.14)
    light_pool(bg, 400, BASE + 6, 70, 10, strength=0.08)
    # index cards fallen from the cabinets and the intake, trailing toward INDEX's rose
    spots = [(296, 256), (312, 268), (340, 280), (366, 292), (392, 306), (418, 318), (436, 330), (526, 304), (548, 290),
             (578, 276), (604, 262), (712, 262), (690, 292), (160, 270), (140, 300), (330, 368), (398, 380), (548, 148),
             (564, 150), (542, 153), (64, 248), (746, 232), (512, 444), (240, 452), (700, 446), (180, 380)]
    floor_cards(bg, spots, seed=7)
    depth_shade(bg, 0, 400, W, 80, steps=3, alpha=0.2)
    # margins outside the walkable floor
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

    save(0, index_cabinet(145, 118, seed=41))
    save(1, index_cabinet(145, 118, seed=42))
    save(2, sorting_table(140, 40, seed=43))
    save(3, archive_shelf(110, 88, seed=44))
    save(4, standard_lamp(68))

    # the rope across the playback room's door comes down once INDEX is settled
    overlays = []
    for open_, name in ((False, "rope-closed.png"), (True, "rope-open.png")):
        velvet_rope(open_).save(os.path.join(out, name))
        overlays.append({"texture": res + name, "x": ROPE[0], "y": ROPE[1], "flag": "index_resolution", "when": open_})

    # INDEX has not finished: drawers in the index walls slide out and back, cards drop down the tube
    drawer_out().save(os.path.join(out, "drawer-out.png"))
    slots = index_wall_slots(INDEX_L[0], INDEX_L[1], INDEX_L[2], BASE) + index_wall_slots(INDEX_R[0], INDEX_R[1], INDEX_R[2], BASE)
    rng = np.random.default_rng(66)
    picks = rng.choice(len(slots), 10, replace=False)
    layers = []
    for k, i in enumerate(picks):
        sx, sy = slots[int(i)]
        pattern = ["0"] * 10
        pattern[k] = "1"
        layers.append({"kind": "blink", "pattern": "".join(pattern), "rate": 1.3, "flag": "index_resolution", "when": False,
                       "texture": res + "drawer-out.png", "x": sx - 1, "y": sy - 2})
    tube_y0, tube_y1 = 14, BASE - 40
    steps = 6
    for k in range(steps):
        y = tube_y0 + 4 + (tube_y1 - tube_y0 - 8) * k // (steps - 1)
        pattern = ["0"] * (steps + 2)
        pattern[k] = "1"
        layers.append({"kind": "blink", "pattern": "".join(pattern), "rate": 5.0, "flag": "index_resolution", "when": False,
                       "rects": [[CHUTE_X - 2, y, 4, 3, "f6ecd2"], [CHUTE_X - 2, y, 4, 1, "fff8e6"], [CHUTE_X - 1, y + 1, 2, 1, "b0382e"]]})
    layers += [
        {"kind": "twinkle", "points": [[px_, 64, "fde9b6", 1] for px_ in PENDANTS] +
                                       [[sx, 78, "fde9b6", 1] for sx in (WINDOWS[0] - 34, WINDOWS[1] + 34)] +
                                       [[CAGE[0] + CAGE[2] // 3, CAGE[1] + 9, "fde9b6", 1], [LAMP[0], LAMP[1] - 63, "fff0c4", 2]],
         "rate": 1.1, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 18, "rect": [150, 40, 500, 90], "speed": [1, 2], "color": "fde9b6"},
    ]

    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": overlays,
        "fauna": [
            {"kind": "lamp_moth", "x": LAMP[0], "y": LAMP[1] - 66, "range": 6, "speed": 2.0, "rate": 9.0},
            {"kind": "library_cat", "x": WINDOWS[1] + 2, "y": WIN_TOP + WIN_H + 2, "range": 0, "speed": 0.0, "rate": 0.5, "flip": True},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
