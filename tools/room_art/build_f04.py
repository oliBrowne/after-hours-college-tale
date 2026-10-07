"""Farrand / audience lawn (F04): the main stage itself, seen from the lawn in front of it. Under
the arched truss roof hung with lamps, the LAST LIGHT / ONE FINAL SET banner, the LED wall with
its two violet peaks, the band's gear on the black deck, PA hangs and scaffold wings; delay
towers stand out on the field either side. On the lawn, rows of wooden folding chairs face the
stage either side of the mat aisle, a festoon pole lights each side, and three columns of tape
crosses mark Chip's bounded rehearsal in front of the stage. Paths: the mat cross-walk from the
volunteer tent (left) to the backstage gate in the crew fence (right), a trodden path out to the
food court (bottom left), the aisle down toward the main stage pit (bottom)."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, WOOD, ground_shadow, shrub
import lib_farrand as F
import lib_farrand2 as G

ROOM = "F04"
W, H = 960, 540
WALK_TOP = 142
FAR_EDGE = 128                 # the far side of the field (hedge line)
STAGE_CX, DECK_W = 480, 360    # placement 0: floor point (480, 250), 360 wide
DECK_BACK, LIP, FACE = 146, 222, 28
ROOF_TOP = 14
AISLE_X = 480                  # the mat aisle down the middle to the "main stage aisle" exit
CROSS_Y = 388                  # mat cross-walk: volunteer tent (left) to backstage (right)
FOOD_Y = 465                   # trodden path out to the food court (left)
CHIP = (480, 310)              # Chip stands here (drawn by the game)
LAMPS = [(150, 370), (810, 370)]
SEATS = [(320, 360), (640, 360), (320, 430), (640, 430)]


def cross_centre(x):
    return float(np.interp(x, [0, 300, 660, 960], [390, 386, 386, 390]))


def aisle_centre(y):
    return AISLE_X + (y - 250) * 0.0


def distant_tent(cv):
    """The volunteer tent far off to the left, beyond the field, glowing inside."""
    tent, ax, ay = F.peaked_tent(112, 34, 22, open_front=False, seed=4, valance_text=None, ropes=False,
                                 poles=[0, 54, 109], windows=True)
    cv.paste(tent, 92 - ax, FAR_EDGE + 4 - ay)
    cv.rect(92 - 60, FAR_EDGE + 4 - 60, 120, 62, C("#2a2440", 0.18))      # distance haze


def backstage_back(cv):
    """Behind the crew fence on the right: a portacabin roof, a generator, a light tower."""
    for k in range(2):
        x0 = 790 + k * 74
        cv.rect(x0, FAR_EDGE - 30, 66, 34, OUT)
        cv.rect(x0 + 1, FAR_EDGE - 29, 64, 32, G.CABIN[2]); cv.hline(x0 + 1, FAR_EDGE - 29, 64, G.CABIN[4])
        for sx in range(x0 + 4, x0 + 64, 4):
            cv.vline(sx, FAR_EDGE - 27, 30, G.CABIN[1])
        cv.rect(x0 + 10, FAR_EDGE - 22, 14, 9, OUT); cv.rect(x0 + 11, FAR_EDGE - 21, 12, 7, F.BULB[2])
        cv.vline(x0 + 17, FAR_EDGE - 21, 7, OUT); cv.rect(x0 + 11, FAR_EDGE - 21, 12, 2, F.BULB[3])
        cv.rect(x0 - 1, FAR_EDGE - 33, 68, 4, OUT); cv.hline(x0, FAR_EDGE - 32, 66, G.CABIN[5])
    cv.rect(x0 + 12, FAR_EDGE - 46, 4, 14, OUT)          # flue
    return F.light_tower(cv, 930, FAR_EDGE + 2, 104, seed=8)


def scrim_fence_back(cv, x0, x1, base, label=None):
    """Crew fence across the back: mesh panels clad in black scrim on rubber feet."""
    for x in range(x0, x1):
        k = (x - x0) % 40
        top = base - 34
        if k in (0, 1):
            cv.vline(x, top - 2, 36, F.STEEL[4] if k == 0 else F.STEEL[2])
            continue
        for y in range(top, base - 4):
            cv.px(x, y, G.SCRIM[2] if (x + y) % 3 else G.SCRIM[3])
        cv.px(x, top, G.SCRIM[4])
    for x in range(x0, x1, 40):
        cv.rect(x - 4, base - 4, 10, 4, OUT); cv.hline(x - 3, base - 4, 8, "#4a4656")
    if label:
        lw = text_width(label) + 8
        lx = (x0 + x1) // 2 - lw // 2
        cv.rect(lx, base - 28, lw, 11, OUT); cv.rect(lx + 1, base - 27, lw - 2, 9, F.HAZARD[3])
        text(cv, label, lx + 4, base - 28, "#1a1720")


def rehearsal_marks(cv):
    """Chip's bounded rehearsal: three called columns of tape crosses on the lawn before the stage,
    numbered 1 2 3 on tape tabs, with a chalked stop line across the front of them."""
    cols = [418, 480, 542]
    for i, cx in enumerate(cols):
        for j, cy in enumerate((268, 288)):
            if abs(cx - CHIP[0]) < 30 and cy > 280:
                continue
            c = "#e6e2d8"
            cv.line(cx - 3, cy - 2, cx + 3, cy + 2, c); cv.line(cx - 3, cy + 2, cx + 3, cy - 2, c)
            cv.px(cx + 4, cy + 3, C("#0d0b16", 0.4))
        cv.rect(cx - 4, 254, 9, 7, "#f2cf5c"); text(cv, str(i + 1), cx - 2, 253, "#2a2630")
    for x in range(400, 562, 4):
        cv.hline(x, 300, 2, "#d8d4c8")


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=41)
    twinkles = []

    # --- sky, the far edge of the field, things beyond it --------------------------------------
    sky, _ = F.farrand_sky(W, 150, panels=(1, 0, 1, 0), offset=170, scale=2.0, stars=60, seed=21)
    bg.a[:150] = sky
    F.far_hedge(bg, 0, W, FAR_EDGE, seed=31)
    F.treeline_back(bg, -10, 980, FAR_EDGE + 6, seed=33, heights=(60, 100), gap=(44, 78), skip=[(240, 720)])
    # food court glow beyond the trees to the left
    for (r, a) in [(60, 0.08), (40, 0.1), (22, 0.12)]:
        bg.ellipse(-r // 2, 104 - r // 3, r * 2, r // 1, C(F.BULB[1], a))
    distant_tent(bg)
    lt = backstage_back(bg)
    F.lawn(bg, 0, FAR_EDGE, W, H - FAR_EDGE, seed=42, clover=0.03, leaves=0.08, stripes=(52, 0.0))
    bg.rect(0, FAR_EDGE, W, WALK_TOP - FAR_EDGE + 4, C("#2a2440", 0.3))
    scrim_fence_back(bg, 712, 960, WALK_TOP, label="CREW ONLY")

    # --- the main stage --------------------------------------------------------------------------
    stage = G.main_stage(bg, STAGE_CX, DECK_W, DECK_BACK, LIP, ROOF_TOP, rise=18, screen="mountains", seed=4, face=FACE)
    # delay towers out on the field either side of the stage, and the far festoon strings
    tower_pts = G.delay_tower(bg, 186, WALK_TOP + 2, 118, seed=1) + G.delay_tower(bg, 762, WALK_TOP + 2, 118, seed=2)
    wl, wr = stage["wings"]
    twinkles += F.festoon(bg, 192, WALK_TOP - 112, wl + 2, ROOF_TOP + 18, sag=12, every=8, seed=5)
    twinkles += F.festoon(bg, wr + 18, ROOF_TOP + 18, 768, WALK_TOP - 112, sag=12, every=8, seed=6)
    twinkles += F.festoon(bg, 0, 64, 186, WALK_TOP - 108, sag=14, every=8, seed=7)
    twinkles += F.festoon(bg, 774, WALK_TOP - 108, 960, 60, sag=14, every=8, seed=8)

    # --- the lawn ------------------------------------------------------------------------------
    for i, (px_, py_, rx, ry) in enumerate([(392, 276, 56, 14), (568, 278, 56, 14), (300, 290, 40, 10),
                                            (660, 292, 44, 10), (480, 300, 34, 9)]):
        F.trodden_patch(bg, px_, py_, rx, ry, seed=3 + i, strength=0.75)   # worn in front of the stage
    for i, x in enumerate(range(40, 440, 70)):                              # path out to the food court
        F.trodden_patch(bg, x, FOOD_Y + int(4 * np.sin(x / 50)), 40, 9, seed=20 + i, strength=0.8)
    F.trodden_patch(bg, 230, 220, 40, 12, seed=30, strength=0.6)
    F.trodden_patch(bg, 740, 230, 46, 12, seed=31, strength=0.6)
    cross = F.mat_walkway(bg, cross_centre, width=44, seed=9)
    aisle = F.mat_path_vertical(bg, aisle_centre, LIP + FACE + 2, H, width=44, seed=10)
    # cables from the stage to the mix position out the bottom, and along to the backstage gate
    F.cable_run(bg, [(560, 252), (548, 300), (520, 330), (508, 360), (506, 420), (512, 500), (520, H)], count=3, seed=11)
    F.cable_run(bg, [(660, 252), (700, 300), (760, 344), (860, 366), (960, 372)], count=2, seed=12, tape_every=50)
    F.cable_ramp_vertical(bg, 501, int(cross_centre(507)) - 23, int(cross_centre(507)) + 23)
    rehearsal_marks(bg)
    # blankets spread on the grass by people who did sit down
    G.picnic_blanket(bg, 64, 214, 62, 26, F.TEAL_C, seed=1)
    G.picnic_blanket(bg, 800, 236, 58, 24, F.RED, seed=2, skew=-6)
    G.picnic_blanket(bg, 196, 486, 54, 22, ["#2a2440", "#3a3260", "#4a4280", "#5c56a0", "#7a74c0", "#a8a0e0"], seed=3)
    F.litter(bg, 84, 222, "cup"); F.litter(bg, 104, 226, "flyer"); F.litter(bg, 820, 244, "band")
    # rain left in the dips, things dropped by the crowd
    F.puddle(bg, 120, 300, 26, 7, seed=1, reflect=("#f6cf7a", "#e8a0d0"))
    F.puddle(bg, 820, 470, 32, 8, seed=2, reflect=("#e8a0d0",))
    F.puddle(bg, 640, 488, 16, 5, seed=3)
    rng = np.random.default_rng(23)
    for kind, (x, y) in zip(["cup", "band", "flyer", "cup_down", "cap", "cup", "band", "flyer", "cup", "band"],
                            [(250, 270), (380, 320), (600, 318), (720, 456), (200, 430), (880, 300), (560, 480),
                             (90, 330), (410, 500), (840, 430)]):
        F.litter(bg, x, y, kind, seed=int(rng.integers(100)))

    # --- light ---------------------------------------------------------------------------------
    F.light_pool(bg, STAGE_CX, 262, 230, 26, color="#f0a0c8", strength=0.22)   # stage spill on the grass
    F.light_pool(bg, STAGE_CX, 258, 150, 14, strength=0.22)
    for (lx, ly) in LAMPS:
        F.light_pool(bg, lx + 6, ly + 2, 58, 18, strength=0.28)
    F.light_pool(bg, 0, FOOD_Y, 60, 20, strength=0.16)

    # --- edges ---------------------------------------------------------------------------------
    bg.rect(0, WALK_TOP, 20, H - WALK_TOP, C("#0d0b16", 0.35))
    bg.rect(W - 20, WALK_TOP, 20, H - WALK_TOP, C("#0d0b16", 0.3))
    for y in range(WALK_TOP - 4, H - 20, 14):
        if 360 < y < 414 or 438 < y < 490:
            continue                       # openings to the volunteer tent and the food court
        bg.paste(shrub(0, 0, 20, 16, seed=int(rng.integers(1e6))), -8, y)
    for y in range(WALK_TOP - 4, H - 20, 14):
        if not (356 < y < 418):
            bg.paste(shrub(0, 0, 20, 16, seed=int(rng.integers(1e6))), W - 12, y)
    gate_pts = G.crew_gate(bg, W - 16, 362, 418)
    x = -6
    while x < W:
        if AISLE_X - 40 < x + 36 and x < AISLE_X + 34:
            x = AISLE_X + 34
            continue
        bw = int(rng.integers(30, 40))
        bale, _, _ = F.hay_bales(bw, 18, seed=int(rng.integers(1e6)))
        bg.paste(bale, x, H - 25)
        x += bw + int(rng.integers(0, 12))
    for cx_ in (AISLE_X - 40, AISLE_X + 40):
        F.traffic_cone(bg, cx_, H - 6, 12)
    bg.rect(0, H - 24, W, 24, C("#0d0b16", 0.35))
    bg.save(os.path.join(out, "background.png"))

    # --- props ---------------------------------------------------------------------------------
    props = {}

    def save(index, sprite, ax, ay, extra=None):
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [int(ax), int(ay)]}
        entry.update(extra or {})
        props[str(index)] = entry

    front, fax, fay, finfo = G.stage_front(DECK_W, FACE, seed=4)
    save(0, front, fax, fay)
    for i, (sx, sy) in enumerate(SEATS):
        save(1 + i, *G.chair_row(170, 30, seed=10 + i))
    pole_bulbs = []
    for i, (lx, ly) in enumerate(LAMPS):
        pole, pax, pay, bulb = F.festoon_pole(55, seed=20 + i, flip=i == 1)
        save(5 + i, pole, pax, pay)
        pole_bulbs.append((lx - pax + bulb[0], ly - pay + bulb[1]))

    # --- animation -----------------------------------------------------------------------------
    to_room = lambda p, ax, ay, at: [at[0] - ax + p[0], at[1] - ay + p[1]]
    foot = [to_room(p, fax, fay, (STAGE_CX, 250)) + ["f6cf7a", 1] for p in finfo["lamps"]]
    wedge = [to_room(p, fax, fay, (STAGE_CX, 250)) for p in finfo["wedges"]]
    lamps = [[x, y, c, 1] for (x, y, c) in stage["lamps"]]
    sx, sy, sw, sh = stage["screen"]
    scan = [{"kind": "blink", "pattern": "".join("1" if k == j else "0" for k in range(8)), "rate": 5.0,
             "rects": [[sx, sy + j * sh // 8, sw, 2, "b8a8e8", 0.12]]} for j in range(8)]
    arch = stage["arch"]
    beams = [
        {"kind": "beam", "x": wl + 10, "y": ROOF_TOP + 4, "angle": -112, "sweep": 16, "period": 9.0, "phase": 0.0,
         "length": 150, "width": 26, "color": "c8b0ff", "alpha": 0.16, "floor": -400},
        {"kind": "beam", "x": wr + 10, "y": ROOF_TOP + 4, "angle": -68, "sweep": 16, "period": 10.5, "phase": 2.2,
         "length": 150, "width": 26, "color": "ffd0e8", "alpha": 0.15, "floor": -400},
        {"kind": "beam", "x": 400, "y": arch(400) + 22, "angle": 96, "sweep": 10, "period": 7.0, "phase": 1.0,
         "length": 150, "width": 40, "color": "fff0c4", "alpha": 0.18, "floor": 196},
        {"kind": "beam", "x": 566, "y": arch(566) + 22, "angle": 82, "sweep": 12, "period": 8.5, "phase": 3.4,
         "length": 150, "width": 40, "color": "f2b0d0", "alpha": 0.16, "floor": 190},
    ]
    return {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "fauna": [
            {"kind": "moth", "x": pole_bulbs[0][0] - 2, "y": pole_bulbs[0][1] + 4, "range": 6, "speed": 2.1, "rate": 8.0},
            {"kind": "moth", "x": pole_bulbs[1][0] + 3, "y": pole_bulbs[1][1] + 3, "range": 5, "speed": 1.7, "rate": 7.0, "flip": True},
            {"kind": "rabbit", "x": 60, "y": 236, "range": 0, "speed": 0.0, "rate": 0.6},
            {"kind": "barn_owl", "x": 192, "y": WALK_TOP + 2 - 118 - 4, "range": 0, "speed": 0.0, "rate": 0.5},
            {"kind": "bat", "x": 140, "y": 34, "fly": 20.0, "rate": 7.0},
            {"kind": "bat", "x": 700, "y": 22, "fly": 15.0, "rate": 6.0},
        ],
        "leaves": [],
        "layers": beams + scan + [
            {"kind": "twinkle", "points": twinkles + gate_pts, "rate": 1.8, "min": 0.4},
            {"kind": "twinkle", "points": lamps + [[x, y, "fff0c4", 1] for (x, y) in stage["tower_lamps"] + tower_pts + lt],
             "rate": 1.3, "min": 0.5},
            {"kind": "twinkle", "points": foot, "rate": 0.9, "min": 0.6},
            {"kind": "blink", "pattern": "1000", "rate": 1.5, "rects": [[x, y, 1, 1, "5cf08a"] for (x, y) in wedge]},
            {"kind": "particles", "style": "dust", "count": 14, "rect": [STAGE_CX - 120, 150, 240, 60], "speed": [0, -4],
             "color": "f6e0b0"},
        ],
    }


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT))[:300])
