"""Farrand Hall lobby and laundry room (D03), the ground floor on move-in night.
Left, the lobby: the stair door up to the second floor, a bank of brass mailboxes, the glass front
doors under FARRAND HALL in brass letters, a sandstone fireplace with the fire going, the front
desk with parcels in its cubbies and WELCOME bunting. Terrazzo with brass strips, a medallion
inside the doors, a rug and a teal couch round the fire, the brass floor lamp (rest and save).
Right, past a sandstone pier, the laundry room: mint glazed tile, a row of washers and stacked
dryers set into the wall (one still tumbling), the soap machine, the LOST SOCKS board, a long
folding table under the fluorescent tubes. Down front: the ping-pong table, the lobby's
upright piano, a row of plastic chairs and a WET FLOOR sign by a soapy puddle."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from lib_eng import micro_text, micro_width, exit_sign, outlet, wall_clock
from lib_umc import soft_ellipse, halo
from lib_farrand import a_frame_sign
from interior import potted_plant
from d02_lib import (acoustic_soffit, hall_wall, drum_light, stair_door, painted_block, wall_shadow, lino_floor,
                     terrazzo_floor, floor_medallion, tile_wainscot, fluorescent, mailboxes, front_entrance, fireplace,
                     fire_frames, desk_wall, bunting, lost_socks, front_desk, couch_back, armchair, coffee_table,
                     floor_lamp_fh, washer, dryer_stack, tumble_frames, vending_soap, folding_table_fh, wire_cart,
                     move_in_cart, laundry_pile, doormat, sneakers, light_switch, thermostat, pull_station,
                     ping_pong, upright_piano, plastic_chairs, wet_floor_sign, puddle,
                     FH_BLOCK, FH_SAND, MINT, BRASS_FH, CPAPER, SHADOW, OUT, CHROME)

ROOM = "D03"
W, H = 960, 540
BASE = 158
SPLIT = 628                      # lobby | laundry
STAIRS_X, DOORS_X, FIRE_X = 56, 262, 392
WASHERS = (666, 710, 754)
DRYERS = (808, 858)
SOAP_X = 908


def rug(cv, x, y, w, h):
    """A mid-century wool rug: rust field, cream border, a row of mustard and teal diamonds."""
    cv.rect(x + 1, y + 1, w, h, C(SHADOW, 0.4))
    cv.rect(x, y, w, h, "#7a3a2e")
    cv.rect(x + 3, y + 2, w - 6, h - 4, "#e6d6b1"); cv.rect(x + 5, y + 4, w - 10, h - 8, "#8a4434")
    for yy in range(y + 6, y + h - 6, 2):
        cv.hline(x + 5, yy, w - 10, "#80402f")
    for k, xx in enumerate(range(x + 16, x + w - 12, 18)):
        cy = y + h // 2
        c = "#c89838" if k % 2 else "#3e6e68"
        cv.poly([(xx, cy - 7), (xx + 7, cy), (xx, cy + 7), (xx - 7, cy)], c)
        cv.poly([(xx, cy - 3), (xx + 3, cy), (xx, cy + 3), (xx - 3, cy)], "#e6d6b1")
    for fx in range(x, x + w, 2):
        cv.px(fx, y - 1, "#e6d6b1"); cv.px(fx, y + h, "#e6d6b1")


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=31)

    # --- lobby wall
    hall_wall(bg, 0, SPLIT, BASE, top=12, seed=14)
    # --- laundry wall: cream block over mint glazed tile
    painted_block(bg, SPLIT, 12, W - SPLIT, BASE - 12, seed=15, pal=FH_BLOCK)
    bg.rect(SPLIT, 12, W - SPLIT, 2, C(SHADOW, 0.22))
    tile_wainscot(bg, SPLIT, BASE - 64, W - SPLIT, 61)
    bg.rect(SPLIT, BASE - 3, W - SPLIT, 3, "#2a2226"); bg.hline(SPLIT, BASE - 3, W - SPLIT, "#433a3c")
    acoustic_soffit(bg, 0, W, y=0, h=12, seed=16)
    # the sandstone pier between the two rooms
    bg.rect(SPLIT - 8, 12, 16, BASE - 12, OUT)
    bg.rect(SPLIT - 7, 12, 14, BASE - 12, FH_SAND[3]); bg.vline(SPLIT - 7, 12, BASE - 12, FH_SAND[5]); bg.vline(SPLIT + 6, 12, BASE - 12, FH_SAND[1])
    for yy in range(18, BASE, 9):
        bg.hline(SPLIT - 7, yy, 14, FH_SAND[2])
    bg.rect(SPLIT - 9, 12, 18, 4, FH_SAND[4]); bg.rect(SPLIT - 9, BASE - 8, 18, 8, FH_SAND[2])

    # --- lobby: stairs, mailboxes, front doors, fireplace, the front desk wall
    stair_door(bg, STAIRS_X, BASE, label="STAIRS")
    exit_sign(bg, STAIRS_X - 44, BASE - 80)              # beside the frame, clear of the label pill
    mailboxes(bg, 100, 74, cols=9, rows=6, seed=4)
    front_entrance(bg, DOORS_X, BASE, seed=5)
    fb = fireplace(bg, FIRE_X, BASE, seed=6)
    desk_wall(bg, 452, 66, 160, seed=7)
    bunting(bg, 450, 20, 614, 20, sag=12, letters="WELCOME")
    light_switch(bg, 88, 104); pull_station(bg, 330, 104); thermostat(bg, 440, 110)
    for cx in (160, 540):
        drum_light(bg, cx, 12)
    for ox in (204, 600):
        outlet(bg, ox, 142)

    # --- laundry: machines set into the wall, the board, sign, clock, tubes
    lost_socks(bg, 664, 60, 56, 34, seed=8)
    wall_clock(bg, 744, 70, r=6)
    s = "LAUNDRY"
    sw = text_width(s) + 10
    bg.rect(833 - sw // 2, 30, sw, 13, OUT); bg.rect(834 - sw // 2, 31, sw - 2, 11, "#2a2a36")
    text(bg, s, 833 - sw // 2 + 5, 31, "#e8d8a8")
    card = "CARD ONLY"
    bg.rect(726, 100, micro_width(card) + 6, 9, "#f2ecdc"); micro_text(bg, card, 729, 102, "#3a5aa8")
    for cx in (700, 870):
        fluorescent(bg, cx, 12)
    wins = []
    for k, cx in enumerate(WASHERS):
        spr, ax, ay = washer(40, 46, seed=k, lid_open=(k == 1))
        bg.paste(spr, cx - ax, BASE - ay + 1)
    for k, cx in enumerate(DRYERS):
        spr, ax, ay, w2 = dryer_stack(46, 94, seed=k)
        bg.paste(spr, cx - ax, BASE - ay + 1)
        wins.append([(cx - ax + wx, BASE - ay + 1 + wy, r) for (wx, wy, r) in w2])
    spr, ax, ay = vending_soap(30, 72, seed=3)
    bg.paste(spr, SOAP_X - ax, BASE - ay + 1)
    halo(bg, SOAP_X, BASE - 40, 30, colour="#8ab0f0", strength=0.08, steps=2)

    # --- floors
    terrazzo_floor(bg, 0, BASE, SPLIT, H - BASE, seed=9)
    lino_floor(bg, SPLIT, BASE, W - SPLIT, H - BASE - 20, seed=10, bottom_border=False)
    bg.rect(SPLIT - 1, BASE, 3, H - BASE, BRASS_FH[2]); bg.vline(SPLIT - 1, BASE, H - BASE, BRASS_FH[3])   # threshold strip
    wall_shadow(bg, 0, BASE, W)
    # the hearth (flush sandstone slab), the medallion and walk-off mat inside the doors, the rug
    bg.rect(FIRE_X - 44, BASE, 88, 14, FH_SAND[3]); bg.hline(FIRE_X - 44, BASE, 88, FH_SAND[5])
    for jx in (FIRE_X - 22, FIRE_X, FIRE_X + 22):
        bg.vline(jx, BASE + 1, 13, FH_SAND[2])
    bg.hline(FIRE_X - 44, BASE + 13, 88, FH_SAND[1])
    doormat(bg, DOORS_X, BASE + 2, w=60, h=18, colour="#4a3e36", word="FARRAND")
    floor_medallion(bg, DOORS_X, 222)
    rug(bg, 314, 238, 156, 70)
    # light: pools under the drums and the floor lamp, the fire's glow, the cool tubes over the laundry
    for cx, cy, rx, ry, c, a in [(160, 236, 100, 40, "#f6cf7a", 0.26), (540, 300, 96, 40, "#f6cf7a", 0.22),
                                 (FIRE_X, 200, 110, 44, "#f6a050", 0.3), (458, 318, 64, 26, "#f6cf7a", 0.3),
                                 (760, 262, 150, 50, "#e8f0ff", 0.16)]:
        light_pool(bg, cx, cy, rx, ry, color=c, strength=a)
    soft_ellipse(bg, 390, 380, 300, 40, "#e0c8a8", 0.04)
    # flat things on the floor
    sneakers(bg, 76, 186, colour="#e6e2d6", accent="#3a8a5a")
    bg.rect(700, 214, 16, 6, "#e6e2d6"); bg.rect(702, 216, 12, 2, "#c8c4b8")                        # a dropped towel
    for k in range(5):                                                                          # a trail of socks
        bg.rect(848 + k * 9, 246 + (k % 2) * 3, 5, 3, ["#c84a3c", "#e6e2d6", "#3a5aa8", "#e8c24a", "#5c897c"][k])
    puddle(bg, 876, 412, w=34, h=8, seed=4)                                                     # the overflowed washer
    for k in range(4):                                                                          # ping-pong balls that got away
        bg.ellipse(96 + k * 37 + (k % 2) * 9, 470 + (k * 13) % 22, 3, 3, "#f6f2e6")
    # margins: dark at the sides and the bottom edge of the room
    for x0, w in [(0, 12), (W - 12, 12)]:
        bg.rect(x0, BASE, w, H - BASE, C(SHADOW, 0.35))
    bg.rect(0, H - 20, W, 20, C(SHADOW, 0.5))
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

    save(2, front_desk(140, 52, seed=1))
    save(3, couch_back(112, 36, seed=2))
    save(4, armchair(40, 40, seed=3, facing=-1))
    save(5, armchair(40, 40, seed=4, facing=1))
    save(6, coffee_table(60, 20, seed=5))
    save(7, floor_lamp_fh(64))
    save(8, move_in_cart(64, 58, seed=9))
    save(9, a_frame_sign(70, 50, lines=[("CHECK", "#2a2030", False), ("IN >", "#c84a3c", False)], header="MOVE-IN", seed=6))
    save(10, potted_plant(40, 52, seed=7))
    save(11, folding_table_fh(120, 34, seed=8))
    save(12, wire_cart(34, 38, seed=10))
    save(13, laundry_pile(36, 24, seed=11))
    save(18, ping_pong(112, 40, seed=12))
    save(19, upright_piano(56, 46, seed=13))
    save(20, plastic_chairs(84, 36, count=3, seed=14))
    save(21, wet_floor_sign(18, 26))

    # --- animated layers: the fire, one dryer tumbling, the flickering tube, the soap machine glow
    layers = []
    frames = fire_frames(4, fb[2], fb[3], seed=3)
    for k, f in enumerate(frames):
        name = f"fire-{k}.png"
        f.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if j == k else "0" for j in range(4)), "rate": 7.0,
                       "texture": res + name, "x": fb[0], "y": fb[1]})
    (dx, dy, r) = wins[0][0]
    for k, f in enumerate(tumble_frames(r, 4, seed=2)):
        name = f"tumble-{k}.png"
        f.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if j == k else "0" for j in range(4)), "rate": 3.0,
                       "texture": res + name, "x": dx - r, "y": dy - r})
    layers += [
        {"kind": "blink", "pattern": "1111111111111111110101111111111111111111", "rate": 8.0,
         "rects": [[870 - 23, 13, 46, 6, "141223", 0.45]]},
        {"kind": "twinkle", "points": [[FIRE_X - 30, BASE - 61, "f6cd78", 1], [FIRE_X + 28, BASE - 61, "f6cd78", 1]], "rate": 2.6, "min": 0.4},
        {"kind": "particles", "style": "dust", "count": 10, "rect": [FIRE_X - 40, 60, 80, 90], "speed": [0, -6], "color": "ffb070"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0, 1, 14, 15, 16, 17],
        "fauna": [{"kind": "lamp_moth", "x": 462, "y": 262, "range": 8, "speed": 1.3, "rate": 9.0},
                  {"kind": "umc2_mouse", "x": 934, "y": 196, "range": 14, "speed": 0.5, "rate": 4.0}],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
