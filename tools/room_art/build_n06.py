"""Closed archive (N06), taken over by AUTOCOMPLETE: the vault behind the stacks where the machine
reads every book and finishes every sentence.

Back wall: the painted ceiling edge over sandstone. At both ends the old floor-to-cornice book
stacks, now split by server racks wedged in between them (a rolling ladder still on the left); a
ladder cable tray hung under the ceiling carries a loom of cables from the stacks to the middle,
dropping into every rack. Two tall moonlit windows stay. Where the closed archive's grille was,
a strut frame bolted to the stone holds the glowing wall of screens: the big chat window (title
SUGGESTED, "> I WANT TO / BECOME A" with the ghost of DOCTOR after the cursor, suggestion chips,
TAB TO ACCEPT, an ASK ANYTHING message field), monitors either side (chat bubbles, typing dots, ranked suggestions and the old
amber catalogue terminal, its screen overwritten in mint), a bank of rack units along the floor
below, and over it all a lit settings toggle, AUTOCOMPLETE ENABLED. A slim rack stands against the
right-hand pier.
Floor: warm grey stone flags with their brass border, a patch of raised data-floor tiles with a
teal edge where AUTOCOMPLETE parks, cable bundles taped across the flags from the cabinets to it,
index cards and printout slips, a plum runner along the front between the exits (warm stacks
light in from the left, the playback room's green glow from the right, roped off until the boss is
settled), screen glow and moonlight.
Props: a card catalogue with a rack wedged into its middle bank, a bookcase split by a rack, the
twin rack cabinets behind the boss's spot, the prompt desk with the ledger of reserved seats, and
the library floor lamp. Animated: rack LEDs flicker, data pulses run along the cable tray, the
cursor blinks, the ghost suggestion changes, typing dots bounce."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from lib_norlin import (floor_inlay, ceiling_band, stone_wall, quoins, arched_window, runner_n, depth_shade, standard_lamp,
                        built_in_shelves, shade_pendant, wall_sconce, moon_patch, LIME, STONE_N, CARPET_PLUM)
from lib_norlin2 import floor_cards, velvet_rope, tile_floor, VAULT
from n06_lib import (server_rack, cable_tray, fat_cable, cable_ties, toggle_sign, screen_wall, floor_cable, dock_pad,
                     printout_slips, catalog_rack, stacks_rack, mainframe, terminal_table,
                     TEAL, SCREEN, GLOW, GLOW_HI, GHOST2, POPUP, LED, CABLE, CORDS)

ROOM = "N06"
W, H = 800, 480
BASE = 142
WALK = (20, 142, 760, 314)
STONE = [shade(c, -0.12) for c in STONE_N]       # the archive's sandstone, as seen from the stacks
STACKS_L = [(18, 44), (102, 50)]                # book stacks at the left end: x, width
RACK_L = (68, 40, 30)                           # rack wedged between them: x, top, width
STACKS_R = [(724, 48)]
RACK_R = (690, 40, 30)
PIER_RACK = (542, 34, 28)                       # slim rack against the right-hand pier
STACK_TOP = 30
SCREENS = (400, 30)                             # wall of screens: centre x, top
SIGN_Y = 13
TRAY_Y = 20
TRAYS = [(60, 292), (508, 744)]                 # cable tray runs (x0, x1) either side of the screens
WINDOWS = [230, 630]                            # tall windows (centre x)
WIN_TOP, WIN_W, WIN_H = 40, 30, 58
PENDANTS = [282, 518]
LAMP = (95, 315)                                # floor lamp placement
BOSS_SPOT = (480, 345)
PAD = (480, 340, 78, 24)                       # raised data-floor patch: centre x, centre y, w, h
RUNNER = (400, 26)                              # front runner between the exits: top y, height
ROPE = (762, 376)                               # rope across the playback room exit (sprite top-left)


def back_wall(bg):
    """Paint the wall; return (leds, screen points)."""
    stone_wall(bg, 0, 12, W, BASE - 12, pal=STONE, seed=8, course=6)
    ceiling_band(bg, 0, 0, W, 12)
    leds = []
    # book stacks at both ends with racks forced in between, the ladder on the left
    for (x, w) in STACKS_L + STACKS_R:
        built_in_shelves(bg, x, STACK_TOP, w, BASE, seed=x, shelf=20, ladder_x=128 if x == 102 else None)
    for (x, top, w) in (RACK_L, RACK_R):
        bg.rect(x - 2, top - 1, w + 4, BASE - top + 1, C("#0d0b16", 0.5))
        leds += server_rack(bg, x, top, w, BASE, seed=x, books=0.2, drawers=0.1)
    quoins(bg, 157, 24, BASE - 4, "left", pal=LIME)
    quoins(bg, 682, 24, BASE - 4, "right", pal=LIME)
    # tall windows over the two free-standing cabinets
    for i, wx in enumerate(WINDOWS):
        arched_window(bg, wx - WIN_W // 2, WIN_TOP, WIN_W, WIN_H, seed=20 + i, view="campus",
                      moon=(wx + 6, WIN_TOP - 4) if i == 0 else None)
    # slim rack against the right pier
    px_, ptop, pw = PIER_RACK
    bg.rect(px_ - 2, ptop - 1, pw + 4, BASE - ptop + 1, C("#0d0b16", 0.45))
    leds += server_rack(bg, px_, ptop, pw, BASE, seed=77, books=0.25, drawers=0.0)
    # the wall of screens and the toggle sign over it
    cx, top = SCREENS
    bg.rect(cx - 112, top - 2, 224, BASE - top + 2, C("#0d0b16", 0.3))     # soot shadow of the frame
    scr = screen_wall(bg, cx, top, BASE, seed=4)
    leds += scr["leds"]
    toggle_sign(bg, cx, SIGN_Y, "AUTOCOMPLETE ENABLED")
    # lamps
    for p in PENDANTS:
        shade_pendant(bg, p, 62, chain_top=12, w=16)
    for sx in (WINDOWS[0] - 34, WINDOWS[1] + 34):
        wall_sconce(bg, sx, 88)
    # cable trays under the ceiling, looms dropping into the racks and the screen frame
    for (x0, x1) in TRAYS:
        cable_tray(bg, x0, x1, TRAY_Y, hang_top=12)
    rx, rt, rw = RACK_L
    p = fat_cable(bg, [(rx + 8, TRAY_Y + 4), (rx + 6, TRAY_Y + 10), (rx + 9, rt - 6), (rx + 10, rt + 1)], CABLE[1], 3)
    fat_cable(bg, [(rx + 20, TRAY_Y + 4), (rx + 23, TRAY_Y + 12), (rx + 20, rt + 1)], CORDS[0], 2)
    p = fat_cable(bg, [(286, TRAY_Y + 4), (296, TRAY_Y + 9), (300, top + 1), (302, top + 8)], CABLE[1], 3)
    fat_cable(bg, [(px_ + 10, TRAY_Y + 4), (px_ + 8, TRAY_Y + 10), (px_ + 12, ptop + 1)], CABLE[1], 3)
    fat_cable(bg, [(514, TRAY_Y + 4), (506, TRAY_Y + 9), (500, top + 1), (498, top + 8)], CORDS[1], 2)
    rx, rt, rw = RACK_R
    fat_cable(bg, [(rx + 12, TRAY_Y + 4), (rx + 9, TRAY_Y + 11), (rx + 12, rt + 1)], CABLE[1], 3)
    # cords that missed the tray and snake over the stacks' cornices
    fat_cable(bg, [(66, TRAY_Y + 4), (52, STACK_TOP - 5), (34, STACK_TOP - 9), (22, STACK_TOP - 3), (20, STACK_TOP + 18)], CORDS[2], 2)
    fat_cable(bg, [(738, TRAY_Y + 4), (746, STACK_TOP - 6), (760, STACK_TOP - 9), (770, STACK_TOP + 2), (772, STACK_TOP + 30)], CORDS[0], 2)
    fat_cable(bg, [(150, TRAY_Y + 4), (140, STACK_TOP - 6), (120, STACK_TOP - 8), (104, STACK_TOP - 5)], CORDS[1], 2)
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))
    return leds, scr


def floor(bg):
    tile_floor(bg, 0, BASE, W, H - BASE, seed=6, pal=VAULT, tw=32, th=18)
    floor_inlay(bg, 30, BASE + 10, W - 60, WALK[1] + WALK[3] - BASE - 18, t=3, colour="#3a2c2e", line="#a8844e")
    bg.rect(0, BASE, W, 3, C("#0d0b16", 0.35)); bg.rect(0, BASE + 3, W, 2, C("#0d0b16", 0.15))
    # plum runner along the front between the two exits
    ry, rh = RUNNER
    runner_n(bg, 0, ry, W, rh, pal=CARPET_PLUM, vertical=False)
    for i, a in enumerate((0.1, 0.07, 0.04)):
        bg.rect(0, ry - 18 - i * 8, 20 + i * 12, rh + 36 + i * 16, C("#f6cf7a", a))
        bg.rect(W - 20 - i * 12, ry - 18 - i * 8, 20 + i * 12, rh + 36 + i * 16, C("#9ad8b0", a))
    # screen glow, moonlight, lamplight
    light_pool(bg, SCREENS[0], BASE + 6, 120, 12, color=TEAL[3], strength=0.16)
    for wx in WINDOWS:
        moon_patch(bg, wx - 18, BASE + 6, 30, 46, slant=18, strength=0.2)
    light_pool(bg, LAMP[0], LAMP[1] + 3, 46, 13, strength=0.24)
    for p in PENDANTS:
        light_pool(bg, p, BASE + 8, 36, 9, strength=0.14)
    # the raised-floor patch where AUTOCOMPLETE parks, glowing teal
    cx, cy, pw, ph = PAD
    light_pool(bg, cx, cy, pw // 2 + 30, ph // 2 + 12, color=TEAL[3], strength=0.14)
    # cable bundles taped across the flags from the cabinets to the patch
    floor_cable(bg, [(486, 233), (492, 258), (480, 290), (484, cy - ph // 2 + 4)], CABLE[1], 3)
    floor_cable(bg, [(474, 233), (466, 262), (470, 300), (470, cy - ph // 2 + 4)], CORDS[0], 2, every=40)
    floor_cable(bg, [(288, 249), (322, 278), (384, 302), (cx - pw // 2 + 6, cy - 4)], CABLE[1], 2)
    floor_cable(bg, [(653, 249), (640, 280), (590, 312), (cx + pw // 2 - 6, cy - 6)], CABLE[1], 2)
    floor_cable(bg, [(582, 249), (584, 290), (566, 330), (cx + pw // 2 - 2, cy + 4)], CORDS[1], 2, every=40)
    floor_cable(bg, [(172, 249), (186, 270), (226, 290), (250, 302)], CORDS[0], 2, every=40)      # to the prompt desk
    dock_pad(bg, cx, cy, pw, ph)
    # index cards shaken from the catalogue, printout slips spat out by the desk and the cabinets
    floor_cards(bg, [(296, 262), (316, 270), (160, 270), (140, 300), (64, 248), (172, 258), (204, 262), (712, 262),
                     (690, 292), (746, 232), (330, 368), (240, 452), (700, 446)], seed=7)
    printout_slips(bg, [(338, 286), (412, 266), (556, 266), (602, 300), (372, 384), (520, 392), (180, 392), (612, 420),
                        (420, 438), (300, 404), (660, 360), (110, 360)], seed=9)
    depth_shade(bg, 0, 400, W, 80, steps=3, alpha=0.2)
    # margins outside the walkable floor
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.38))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.38))
    bg.rect(0, WALK[1] + WALK[3], W, H - WALK[1] - WALK[3], C("#0d0b16", 0.42))


def ghost_word(bg, crop, word, colour):
    """A texture the size of the ghost-text slot: the screen behind it plus another suggestion."""
    cv = Canvas(crop.shape[1], crop.shape[0])
    cv.a[:] = crop
    text(cv, word, 0, 0, colour)
    return cv


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    leds, scr = back_wall(bg)
    floor(bg)
    res = f"res://assets/art/rooms/{ROOM}/"
    # the ghost suggestion after the cursor: DOCTOR painted, LAWYER / CEO / accepted DOCTOR as frames
    gx, gy = scr["ghost"]
    crop = bg.a[gy:gy + 10, gx:gx + 38].copy()
    text(bg, "DOCTOR", gx, gy, GHOST2)
    for name, word, col in (("ghost-lawyer.png", "LAWYER", GHOST2), ("ghost-ceo.png", "CEO", GHOST2),
                            ("ghost-accepted.png", "DOCTOR", GLOW)):
        ghost_word(bg, crop, word, col).save(os.path.join(out, name))
    # half the LEDs burn steadily in the painting; the rest flicker in layers
    rng = np.random.default_rng(61)
    order = rng.permutation(len(leds))
    steady = [leds[int(i)] for i in order[: len(leds) // 2]]
    busy = [leds[int(i)] for i in order[len(leds) // 2:]]
    for (x, y, key) in steady:
        bg.px(x, y, LED[key])
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None, name=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(0, catalog_rack(145, 118, seed=41))
    save(1, stacks_rack(145, 118, seed=42))
    save(2, terminal_table(140, 40, seed=43))
    save(3, mainframe(110, 88, seed=44))
    save(4, standard_lamp(68))

    # the rope across the playback room's door comes down once the boss is settled
    overlays = []
    for open_, name in ((False, "rope-closed.png"), (True, "rope-open.png")):
        velvet_rope(open_).save(os.path.join(out, name))
        overlays.append({"texture": res + name, "x": ROPE[0], "y": ROPE[1], "flag": "index_resolution", "when": open_})

    layers = []
    # rack LEDs: four groups flickering at different rates
    for k, (pattern, rate) in enumerate((("1101", 3.0), ("0110", 4.5), ("1011", 2.2), ("1110010", 6.0))):
        rects = [[x, y, 1, 1, LED[key][1:]] for (x, y, key) in busy[k::4]]
        layers.append({"kind": "blink", "pattern": pattern, "rate": rate, "rects": rects})
    # the cursor after BECOME A blinks; the ghost suggestion cycles while the boss is unsettled
    layers.append({"kind": "blink", "pattern": "10", "rate": 2.0, "rects": [list(scr["cursor"]) + [GLOW_HI[1:]]]})
    for name, pattern in (("ghost-lawyer.png", "00100000"), ("ghost-ceo.png", "00001000"), ("ghost-accepted.png", "00000011")):
        layers.append({"kind": "blink", "pattern": pattern, "rate": 1.2, "texture": res + name, "x": gx, "y": gy,
                       "flag": "index_resolution", "when": False})
    # typing dots in the bubble on the upper right monitor
    for k, (dx, dy) in enumerate(scr["dots"]):
        pattern = ["0"] * 4
        pattern[k] = "1"
        layers.append({"kind": "blink", "pattern": "".join(pattern), "rate": 5.0,
                       "rects": [[dx, dy - 1, 2, 2, POPUP[4][1:]], [dx, dy + 1, 2, 1, POPUP[2][1:]]]})
    # data pulses running along the cable trays toward the screens
    (a0, a1), (b0, b1) = TRAYS
    layers += [
        {"kind": "movers", "from": [a0 + 2, TRAY_Y + 1], "to": [a1 - 2, TRAY_Y + 1], "count": 3, "period": 2.6,
         "size": [2, 2], "color": GLOW[1:], "ease": "out"},
        {"kind": "movers", "from": [b1 - 2, TRAY_Y + 1], "to": [b0 + 2, TRAY_Y + 1], "count": 2, "period": 2.2,
         "size": [2, 2], "color": GLOW[1:], "ease": "out"},
        {"kind": "twinkle", "points": [[p, 64, "fde9b6", 1] for p in PENDANTS] +
                                       [[sx, 78, "fde9b6", 1] for sx in (WINDOWS[0] - 34, WINDOWS[1] + 34)] +
                                       [[LAMP[0], LAMP[1] - 63, "fff0c4", 2], [SCREENS[0] - 64, SIGN_Y + 8, "96ecda", 1]],
         "rate": 1.1, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 18, "rect": [150, 40, 500, 90], "speed": [1, 2], "color": "c8f4e8"},
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
