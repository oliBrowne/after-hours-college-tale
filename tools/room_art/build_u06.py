"""The Connection (U06): the bowling alley and arcade in the UMC basement, after closing. Seven maple
lanes run back to pin decks lit under a cosmic masking mural, THE CONNECTION in pink neon over them
and the club's ONE ROUND / ONE PROMISE banner tied across. West: the shoe-hire cubbies either side of
the steel service door up to the club room, and Chip's corner rug. Middle: the practice deck in its
wall alcove, nine pins and a chalk ring where Pin Pal used to stand, a rack of house balls. East: the
arcade under ARCADE / LAST CREDIT neon, a lounge rug, and lost property's panelled door. Navy cosmic
carpet everywhere else (the carpet lost property's doorway shows), the flight up to the repair
landing cut through the front wall. Arcade cabinets, the NEXT UP board and the ball returns are drawn
by code on their placements."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import light_pool
from props import OUT, IRON
from interior import PANEL, wainscot, wall_clock, poster
from lib_umc import (BRASS, PAPER, SAFETY, SHADOW, BLOCK, CONCRETE, halo, soft_ellipse, enamel_sign, extinguisher,
                     stair_up_flight, hazard_band, cable)
from lib_umc2 import (INDIGO, MAPLE, NEON_PINK, NEON_TEAL, NEON_GOLD, CARPET, CHROME,
                      indigo_wall, stripe_band, ceiling_soffit, shoe_cubbies, service_door, service_landing,
                      panel_door, lane_bed, gutter, capping, masking_mural, club_banner, lane_number, pit_cavity,
                      kickback, approach, pin_triangle, practice_alcove, ball_rack, neon_pin, neon_text, lightbox,
                      text_mask, cosmic_carpet, worn_path, chip_rug, lounge_rug,
                      league_pennants, floor_litter, bucket_seats, scorer_table, pin_lamp, post_sign)

ROOM = "U06"
W, H = 960, 540
WALL_BASE = 148          # walk_bounds top: the back wall meets the floor
FLOOR_END = 508          # walk_bounds bottom: the front wall-top below
STRIPE_Y = 46            # the retro stripe band round the room
WAINSCOT_TOP = 116
LANES_X0, BAY, N_LANES = 163, 60, 7      # fixed block x 163-583: seven 60 px lane bays
LANES_X1 = LANES_X0 + BAY * N_LANES
MASK = (56, 106)         # masking mural rows
PIT_TOP = 108            # pinsetter openings, down to the wall base
PIN_BACK = 153           # back row of pins (their feet)
DECK_END = 174           # pin deck to lane bed
FOUL = 304               # foul line
APPROACH_END = 347       # approaches step down to the carpet
CLUB_DOOR = (92, 191)    # placement 2: door in the wall, steps down to its floor point
LP_DOOR = (880, 211)     # placement 1: lost property door, a runner to its floor point
STAIRS = (290, 350, 435)  # placement 0: the flight up to the repair landing (x span, top tread)
PRACTICE = 627           # practice alcove and strip centre x (Pin Pal stands at 621, 335)
ARCADE = [715, 776, 837]  # code-drawn cabinets (y 292, 83 tall)
POSTERS = [712, 768, 812]  # game posters on the wall above them
LAMPS = [(72, 390), (913, 393)]
CAN_LIGHTS = list(range(60, 960, 100))
NIGHT_LIGHTS = [(110, 290), (420, 470), (640, 380), (880, 300), (230, 500)]   # ceiling lights left on


def bay_x(k):
    return LANES_X0 + BAY * k


def bed_span(k):
    """x0, x1 of lane k's bed (39 boards)."""
    return bay_x(k) + 11, bay_x(k) + 50


def paint_wall(bg):
    indigo_wall(bg, 0, 8, W, WALL_BASE - 8, seed=6)
    ceiling_soffit(bg, 0, W, cans=CAN_LIGHTS)
    stripe_band(bg, 0, STRIPE_Y, W)
    wainscot(bg, 0, WAINSCOT_TOP, W, WALL_BASE - WAINSCOT_TOP, seed=2)
    bg.rect(0, WALL_BASE - 2, W, 2, PANEL[1])
    marks = {}

    # -- the lanes: masking mural, lane numbers, pinsetter openings and kickbacks
    x0, x1 = LANES_X0, LANES_X1
    bg.rect(x0 - 2, MASK[0] - 1, x1 - x0 + 4, MASK[1] - MASK[0] + 3, OUT)
    stars = masking_mural(bg, x0, MASK[0], x1 - x0, MASK[1] - MASK[0], seed=4)
    bg.rect(x0 - 2, MASK[1], x1 - x0 + 4, 2, CHROME[2]); bg.hline(x0 - 2, MASK[1], x1 - x0 + 4, CHROME[3])
    for k in range(N_LANES):
        b0 = bay_x(k)
        pit_cavity(bg, b0 + 6, b0 + 55, PIT_TOP, WALL_BASE)
        lane_number(bg, b0 + 30, MASK[1] - 11, k + 1)
    for k in range(N_LANES + 1):
        cx = bay_x(k)
        kx, kw = (cx, 6) if k == 0 else (cx - 6, 6) if k == N_LANES else (cx - 5, 11)
        kickback(bg, kx, PIT_TOP, DECK_END, w=kw)
    banner = club_banner(bg, (x0 + x1) // 2, MASK[0] + 2, rope=14)
    # THE CONNECTION in pink neon on the fascia, gold sparkles either side
    sign = neon_text(bg, "THE CONNECTION", (x0 + x1) // 2, 17, pal=NEON_PINK, scale=2)
    for sx in ((x0 + x1) // 2 - 108, (x0 + x1) // 2 + 108):
        for (dx, dy) in [(0, -3), (0, -2), (0, 2), (0, 3), (-3, 0), (-2, 0), (2, 0), (3, 0)]:
            bg.px(sx + dx, 24 + dy, NEON_GOLD[1])
        bg.px(sx, 24, NEON_GOLD[2])
        halo(bg, sx, 24, 7, colour=NEON_GOLD[3], strength=0.1)
    marks["stars"] = stars
    marks["sign"] = sign

    league_pennants(bg, 2, 156, 9, sag=8, every=10, seed=1)
    league_pennants(bg, 590, 700, 9, sag=7, every=10, seed=2)
    league_pennants(bg, 846, 958, 9, sag=7, every=10, seed=3)

    # -- west: the shoe-hire cubbies either side of the service door up to the club room
    shoe_cubbies(bg, 22, 66, 40, WALL_BASE - 68, cols=3, seed=3)
    shoe_cubbies(bg, 121, 66, 37, WALL_BASE - 68, cols=3, seed=5)
    lightbox(bg, 58, 20, 68, 15, "SHOE HIRE")
    service_door(bg, CLUB_DOOR[0], WALL_BASE, w=44, h=62, plate="CLUB")
    # a CU pennant for Chip's corner and a size chart on the end of the right case
    px, py = 4, 64
    bg.poly([(px, py), (px + 14, py + 5), (px, py + 10)], "#1a1418"); bg.poly([(px, py + 1), (px + 11, py + 5), (px, py + 9)], "#c8a058")
    bg.vline(px, py - 2, 14, BRASS[3])
    bg.rect(4, 82, 14, 18, PAPER[2]); bg.hline(4, 82, 14, PAPER[3])
    for k in range(5):
        bg.hline(6, 85 + k * 3, 10 - (k % 2) * 3, "#6a5a50")

    # -- practice deck in its alcove, a neon pin, the house-ball rack
    lightbox(bg, PRACTICE - 28, 92, 56, 13, "PRACTICE", face="#d8f4ee", ink="#1e4a4c")
    practice = practice_alcove(bg, PRACTICE, 110, WALL_BASE, w=44, missing=(9,))
    neon_pin(bg, 595, 62, h=38, pal=NEON_PINK)
    ball_rack(bg, 656, WALL_BASE, w=36, seed=2)
    wall_clock(bg, 674, 82, r=7)
    marks["practice"] = practice

    # -- arcade: ARCADE / LAST CREDIT neon, three game posters, the token changer
    neon_text(bg, "ARCADE", 776, 15, pal=NEON_TEAL, scale=2)
    neon_text(bg, "LAST CREDIT", 776, 34, pal=NEON_GOLD, scale=1)
    for i, (cx, base, title) in enumerate(zip(POSTERS, ["#3a2a6a", "#6a2a3a", "#1e4a4c"], ["ZAP", "PINS", "RALLY"])):
        game_poster(bg, cx - 12, 62, 24, 34, base, title, seed=i)
    tx, ty = 738, 96
    bg.rect(tx, ty, 16, 30, OUT); bg.rect(tx + 1, ty + 1, 14, 28, "#6a6a80"); bg.hline(tx + 1, ty + 1, 14, "#a4a4b8")
    bg.rect(tx + 3, ty + 4, 10, 6, "#14101e"); text(bg, "$", tx + 5, ty + 2, NEON_GOLD[1])
    bg.rect(tx + 4, ty + 13, 8, 3, OUT); bg.rect(tx + 3, ty + 22, 10, 5, "#24202e"); bg.hline(tx + 3, ty + 22, 10, "#4a4458")
    bg.px(tx + 6, ty + 24, BRASS[4]); bg.px(tx + 9, ty + 25, BRASS[3])
    marks["token"] = (tx + 4, ty + 6)

    # -- lost property: panelled door under an enamel sign, the extinguisher at the end wall
    panel_door(bg, LP_DOOR[0], WALL_BASE, w=44, h=64)
    label = "LOST PROPERTY"
    lw = text_width(label) + 14
    lx = LP_DOOR[0] - lw // 2
    bg.rect(lx - 1, 59, lw + 2, 15, OUT)
    bg.rect(lx, 60, lw, 13, BRASS[2]); bg.hline(lx, 60, lw, BRASS[4]); bg.hline(lx, 72, lw, BRASS[0])
    bg.rect(lx + 2, 62, lw - 4, 9, "#7e3a30"); bg.hline(lx + 2, 62, lw - 4, "#9a4a39")
    text(bg, label, LP_DOOR[0] - text_width(label) // 2, 62, PAPER[3])
    extinguisher(bg, 920, 142)
    return marks


def game_poster(bg, x, y, w, h, base, title, seed=0):
    """A framed arcade poster: a little scene and the game's name."""
    rng = np.random.default_rng(seed)
    bg.rect(x + 1, y + 1, w, h, C(SHADOW, 0.5))
    bg.rect(x - 1, y - 1, w + 2, h + 2, CHROME[1])
    bg.rect(x, y, w, h, base)
    for _ in range(10):
        bg.px(x + int(rng.integers(1, w - 1)), y + int(rng.integers(1, h // 2)), "#c8c4f0")
    if title == "ZAP":
        bg.poly([(x + 12, y + 8), (x + 18, y + 20), (x + 6, y + 20)], "#58e0d0")
        bg.rect(x + 11, y + 14, 3, 3, "#ff7aa8")
    elif title == "PINS":
        for k, dx in enumerate((7, 12, 17)):
            bg.rect(x + dx - 1, y + 9 + (k % 2) * 2, 3, 10, "#fbf4e6"); bg.hline(x + dx - 1, y + 12 + (k % 2) * 2, 3, "#d23a44")
        bg.ellipse(x + 4, y + 18, 6, 6, "#2c4aa0")
    else:
        bg.poly([(x + 3, y + 22), (x + 12, y + 8), (x + 21, y + 22)], "#2a2a3a")
        bg.rect(x + 10, y + 16, 5, 3, "#e8b45c"); bg.vline(x + 12, y + 9, 13, C("#fff0c4", 0.6))
    bg.rect(x, y + h - 10, w, 10, "#14101e")
    text(bg, title, x + w // 2 - text_width(title) // 2, y + h - 11, "#f6cf7a")


def paint_lanes(bg):
    """Lane beds, gutters and cappings from the pin decks to the foul line, pins on the decks, then
    the approaches."""
    pins = []
    for k in range(N_LANES):
        b0 = bay_x(k)
        bx0, bx1 = bed_span(k)
        lane_bed(bg, bx0, bx1, WALL_BASE, FOUL + 2, FOUL, seed=10 + k)
        # the pin deck: paler, the pin spots, a line where it meets the bed
        bg.rect(bx0, WALL_BASE, bx1 - bx0, DECK_END - WALL_BASE, C(MAPLE[5], 0.35))
        bg.hline(bx0, DECK_END, bx1 - bx0, C(MAPLE[2], 0.8))
        gutter(bg, b0 + 6, WALL_BASE, FOUL + 2)
        gutter(bg, b0 + 50, WALL_BASE, FOUL + 2)
        pins.append(pin_triangle(bg, b0 + 30, PIN_BACK, spacing=10, row_dy=5))
    for k in range(1, N_LANES):
        capping(bg, bay_x(k) - 5, DECK_END, FOUL + 2)
    capping(bg, LANES_X0, DECK_END, FOUL + 2, w=6)
    capping(bg, LANES_X1 - 6, DECK_END, FOUL + 2, w=6)
    # foul-line sensors on the cappings
    for k in range(N_LANES + 1):
        sx = min(max(bay_x(k), LANES_X0 + 2), LANES_X1 - 3)
        bg.rect(sx - 1, FOUL - 3, 3, 5, OUT); bg.px(sx, FOUL - 2, "#ff5a4a")
    gx = bay_x(5) + 50
    bg.ellipse(gx - 1, 196, 7, 7, OUT); bg.ellipse(gx, 197, 5, 5, "#5a3ab0"); bg.px(gx + 1, 198, "#9a7ae8")
    bg.hline(gx, 203, 5, C(SHADOW, 0.5))
    approach(bg, LANES_X0, LANES_X1, FOUL + 2, APPROACH_END, [(bay_x(k), bay_x(k) + 30) for k in range(N_LANES)], seed=3)
    bg.vline(LANES_X0 - 1, FOUL + 2, APPROACH_END - FOUL + 2, OUT); bg.vline(LANES_X1, FOUL + 2, APPROACH_END - FOUL + 2, OUT)
    return pins


def paint_floor(bg):
    cosmic_carpet(bg, 0, WALL_BASE, W, FLOOR_END - WALL_BASE, seed=11)
    bg.rect(0, WALL_BASE, W, 3, C(SHADOW, 0.5)); bg.hline(0, WALL_BASE + 3, W, C(SHADOW, 0.25))
    # walked-pale trails: stairs to the lanes, across to the arcade and to Chip's corner
    worn_path(bg, [(320, 420), (330, 380), (400, 362), (500, 366), (600, 370), (660, 340), (720, 330),
                   (250, 368), (160, 360), (100, 300), (110, 230), (860, 240), (880, 300)], 40, 12)
    # the service landing down from the club door
    service_landing(bg, CLUB_DOOR[0], WALL_BASE, CLUB_DOOR[1] - 1, w0=52, grow=6, n=3)
    # runner from lost property's door
    rx0, rx1 = LP_DOOR[0] - 22, LP_DOOR[0] + 22
    bg.rect(rx0 - 1, WALL_BASE, rx1 - rx0 + 2, LP_DOOR[1] - 4 - WALL_BASE, C(SHADOW, 0.5))
    bg.rect(rx0, WALL_BASE, rx1 - rx0, LP_DOOR[1] - 6 - WALL_BASE, "#74463c")
    bg.rect(rx0 + 2, WALL_BASE, rx1 - rx0 - 4, LP_DOOR[1] - 8 - WALL_BASE, BRASS[2])
    bg.rect(rx0 + 3, WALL_BASE, rx1 - rx0 - 6, LP_DOOR[1] - 9 - WALL_BASE, "#7e3a30")
    for yy in range(WALL_BASE + 4, LP_DOOR[1] - 10, 6):
        bg.hline(rx0 + 5, yy, rx1 - rx0 - 10, "#8a4a40")
    for fx in range(rx0, rx1, 2):
        bg.px(fx, LP_DOOR[1] - 5, BRASS[3])
    light_pool(bg, LP_DOOR[0], WALL_BASE + 6, 26, 6, strength=0.25)
    # the practice strip: a short maple approach to the alcove deck
    px0, px1 = PRACTICE - 20, PRACTICE + 20
    bg.rect(px0 - 2, WALL_BASE, px1 - px0 + 4, 296 - WALL_BASE, OUT)
    lane_bed(bg, px0, px1, WALL_BASE, 294, 262, seed=30)
    bg.rect(px0 - 1, WALL_BASE, 1, 294 - WALL_BASE, CHROME[1]); bg.rect(px1, WALL_BASE, 1, 294 - WALL_BASE, CHROME[1])
    bg.rect(px0, 292, px1 - px0, 2, MAPLE[1])
    light_pool(bg, PRACTICE, WALL_BASE + 8, 30, 8, strength=0.2)
    # rugs: Chip's corner at the west, the arcade lounge at the east
    chip_rug(bg, 44, 402, 192, 64)
    lounge_rug(bg, 686, 384, 222, 108, seed=4)
    # arcade screens throw colour on the carpet in front of the cabinets
    for cx, col in zip(ARCADE, ["#58a8e8", "#ff7aa8", "#58e0d0"]):
        light_pool(bg, cx, 300, 26, 7, color=col, strength=0.22)
    floor_litter(bg, [(300, 440, "card"), (226, 446, "pencil"), (752, 334, "token"), (668, 318, "token"),
                      (532, 452, "straw"), (412, 468, "wrapper"), (888, 478, "shoe"), (118, 470, "token"),
                      (690, 360, "card")])
    # the night lights left on in the ceiling, the lamps
    for (nx, ny) in NIGHT_LIGHTS:
        light_pool(bg, nx, ny, 58, 15, color="#f6e0b0", strength=0.12)
    for (lx, ly) in LAMPS:
        light_pool(bg, lx, ly, 62, 18, strength=0.3)
    # THE CONNECTION's pink on the front of the approaches, the arcade's teal on the carpet
    light_pool(bg, (LANES_X0 + LANES_X1) // 2, APPROACH_END + 6, 150, 8, color="#ff7aa8", strength=0.1)
    light_pool(bg, 776, 318, 110, 22, color="#58e0d0", strength=0.08)
    # light from the lanes' pin decks spills onto the approaches and the carpet in front of them
    light_pool(bg, (LANES_X0 + LANES_X1) // 2, APPROACH_END + 10, 230, 14, color="#ffe8c0", strength=0.12)
    # cool shade gathering toward the front wall and in the corners
    for (hh, a) in [(44, 0.08), (24, 0.08), (10, 0.1)]:
        bg.rect(0, FLOOR_END - hh, W, hh, C("#140f2a", a))
    for (ww, a) in [(50, 0.07), (26, 0.08)]:
        bg.rect(20, WALL_BASE, ww, FLOOR_END - WALL_BASE, C("#140f2a", a))
        bg.rect(940 - ww, WALL_BASE, ww, FLOOR_END - WALL_BASE, C("#140f2a", a))
    # lamp flex runs to the wall
    cable(bg, [(LAMPS[1][0] - 3, LAMPS[1][1] - 1), (926, 380), (938, 360)], "#16141f", hi="#6c6a88")
    cable(bg, [(LAMPS[0][0] + 3, LAMPS[0][1] - 1), (40, 384), (22, 372)], "#16141f", hi="#6c6a88")


def wall_top(bg, x, y, w, h, inner="top"):
    bg.rect(x, y, w, h, "#16121e")
    rng = np.random.default_rng(x * 3 + y)
    for _ in range(w * h // 28):
        bg.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), "#221c2c")
    edge = (INDIGO[4], INDIGO[2])
    if inner == "left":
        bg.vline(x, y, h, edge[0]); bg.vline(x + 1, y, h, edge[1])
    elif inner == "right":
        bg.vline(x + w - 1, y, h, edge[0]); bg.vline(x + w - 2, y, h, edge[1])
    else:
        bg.hline(x, y, w, edge[0]); bg.hline(x, y + 1, w, edge[1])


def paint_frame(bg):
    """Side and front wall-tops; the flight up to the repair landing climbs out through the front."""
    x0, x1, top = STAIRS
    stair_up_flight(bg, x0, top, x1, H, H)
    hazard_band(bg, x0, top - 3, x1 - x0, 3)
    wall_top(bg, 0, FLOOR_END, x0 - 4, H - FLOOR_END, "top")
    wall_top(bg, x1 + 4, FLOOR_END, W - x1 - 4, H - FLOOR_END, "top")
    wall_top(bg, 0, WALL_BASE - 1, 20, FLOOR_END - WALL_BASE + 1, "right")
    wall_top(bg, 940, WALL_BASE - 1, 20, FLOOR_END - WALL_BASE + 1, "left")
    bg.rect(20, FLOOR_END - 8, x0 - 24, 8, C(SHADOW, 0.25)); bg.rect(x1 + 4, FLOOR_END - 8, 940 - x1 - 4, 8, C(SHADOW, 0.25))


def layer_textures(bg, out, marks):
    """Animated bits that need textures: the second N of THE CONNECTION is painted dim in the
    background and lit by a blink texture that drops out now and then (a still shows it lit)."""
    res = f"res://assets/art/rooms/{ROOM}/"
    sx, sy, sw, sh = marks["sign"]
    m = text_mask("THE CONNECTION", 2)
    col0 = 7 * 12
    letter = m[:, col0:col0 + 12]
    lx, ly = sx + col0, sy
    lit = Canvas(13, sh + 1)
    keep = np.zeros((sh + 1, 13), bool)
    keep[:sh, :12] |= letter
    keep[1:, 1:] |= letter                    # the tube's shadow
    lit.a[keep] = bg.a[ly:ly + sh + 1, lx:lx + 13][keep]
    lit.save(os.path.join(out, "neon-n.png"))
    full = np.zeros((bg.h, bg.w), bool)
    full[ly:ly + sh, lx:lx + 12] = letter
    bg.fill_mask(full, "#4a2038")
    return [{"kind": "blink", "pattern": "11111111111111111111101011111111111111111111111111111110", "rate": 9.0,
             "texture": res + "neon-n.png", "x": lx, "y": ly}]


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=6)
    marks = paint_wall(bg)
    paint_floor(bg)
    paint_lanes(bg)
    paint_frame(bg)
    layers = layer_textures(bg, out, marks)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made[:3]
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(3, bucket_seats(98, 35, n=4, facing="front", seed=0))
    save(4, bucket_seats(108, 35, n=4, facing="back", seed=1))
    save(5, scorer_table(70, 35, label="ONE ROUND", circle=True, cards=1, seed=5))
    save(13, bucket_seats(94, 35, n=4, facing="front", seed=2))
    save(14, scorer_table(96, 35, label="SCORECARDS", circle=False, cards=2, seed=6))
    save(15, post_sign(122, 27, "LOST PROPERTY >"))
    save(16, pin_lamp(65))
    save(17, pin_lamp(65))

    res = f"res://assets/art/rooms/{ROOM}/"
    lane = lambda k: (bed_span(k)[0] + bed_span(k)[1]) // 2
    layers += [
        # rolling stars: glowing balls roll up the lanes toward pins that will not fall, while Pin
        # Pal is still sending them back
        {"kind": "movers", "from": [lane(3), FOUL - 3], "to": [lane(3), DECK_END + 6], "count": 1, "period": 4.6,
         "size": [5, 3], "color": "6ae0d0", "ease": "out", "flag": "pinpal_resolution", "when": False},
        {"kind": "movers", "from": [lane(5) + 4, FOUL - 3], "to": [lane(5) - 2, DECK_END + 6], "count": 1, "period": 7.3,
         "size": [5, 3], "color": "ff8ab8", "ease": "out", "flag": "pinpal_resolution", "when": False},
        # stars in the masking mural, the pin-deck lights and the token changer's lamp
        {"kind": "twinkle", "points": [[x, y, "fff4dc", 1] for (x, y) in marks["stars"]], "rate": 1.4, "min": 0.1},
        {"kind": "twinkle", "points": [[marks["token"][0] + 2, marks["token"][1] + 1, "f6cf7a", 1]], "rate": 2.5, "min": 0.3},
        # the arcade screens' glow on the carpet pulses with their attract modes
        {"kind": "blink", "pattern": "1100", "rate": 2.0,
         "rects": [[cx - 14, 296, 28, 6, col, 0.08] for cx, col in zip(ARCADE, ["58a8e8", "ff7aa8", "58e0d0"])]},
        {"kind": "blink", "pattern": "0110", "rate": 1.5,
         "rects": [[cx - 10, 298, 20, 4, "fff0c4", 0.06] for cx in ARCADE]},
        # dust turning in the pin-deck light
        {"kind": "particles", "style": "dust", "count": 14, "rect": [LANES_X0 + 10, PIT_TOP + 4, LANES_X1 - LANES_X0 - 20, 60],
         "speed": [0, 2], "color": "fff0c4"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0, 1, 2],
        "fauna": [
            {"kind": "umc_moth", "x": LAMPS[0][0] - 2, "y": LAMPS[0][1] - 62, "range": 8, "speed": 1.6, "rate": 9.0},
            {"kind": "umc_moth", "x": LAMPS[1][0] + 1, "y": LAMPS[1][1] - 64, "range": 7, "speed": 1.3, "rate": 8.0},
            {"kind": "umc2_mouse", "x": 44, "y": WALL_BASE + 5, "range": 14, "speed": 0.5, "rate": 5.0},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
