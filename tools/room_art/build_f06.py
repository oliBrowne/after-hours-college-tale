"""Farrand / main stage (F06): right up at the front of the main stage, the same stage the other
Farrand rooms see glowing across the field. The arched truss runs off the top of the picture, the
LAST LIGHT / ONE FINAL SET banner hangs under it, the LED wall is big and close (the mountains,
flipping to AGAIN AGAIN while ENCORE holds the show), the band's gear stands on the deck between
the scaffold wings and the PA hangs, ground subs stand at the corners. In front, a pit of mats
strewn with confetti where ENCORE waits, an aisle of mats back between two front rows of folding
chairs to the cross-walk (audience aisle on the left, the crew gate to the wings on the right),
the stage rest light (a ghost light) on the grass by the left exit. Beyond the stage: the crew
fence and cabins on the right and, far off past the trees, campus and Norlin's lit windows.

State: while encore_resolution is unset the show runs (lamps lit, beams sweeping, a spotlight
swaying over ENCORE, the screen flipping to AGAIN). Once it is set an overlay puts the show out:
truss lamps dark, the drape dim, the deck pools and the spill on the pit gone, the screen off (or
GOODNIGHT under a crescent when the ending was peaceful); the stage front and the subs swap to
unlit versions and the truss work lights come on."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, shrub
import lib_farrand as F
import lib_farrand2 as G

ROOM = "F06"
W, H = 800, 480
WALK_TOP = 142
FAR_EDGE = 126
STAGE_CX, DECK_W, FACE = 440, 350, 28
LIP = 217                         # top of the stage front prop (anchor y 245 minus the face)
DECK_BACK = 140
ROOF_TOP = -2                     # the truss peak just off the top of the picture
PIT = (214, 666, 247, 301)        # mats in front of the stage: x0, x1, y0, y1
AISLE = (436, 482)                # mat aisle between the front rows, back to the cross-walk
CROSS_Y = 425                     # cross-walk: audience aisle (80, 425) to the crew gate (720, 425)
ENCORE = (460, 308)               # ENCORE stands here (drawn by the game)
LAMP = (125, 380)                 # the stage rest light
SPEAKERS = [(255, 260), (635, 260)]
SEATS = [(350, 370), (565, 370)]
DIM_LIP = ["#2e2224", "#4a3428", "#5e4430", "#6e5038"]


def norlin_sign(cv, x, base):
    """A fingerpost at the back right: NORLIN pointing off past the crew fence."""
    cv.rect(x - 1, base - 40, 3, 41, OUT); cv.vline(x, base - 39, 39, F.PLY[3])
    lw = text_width("NORLIN") + 10
    cv.poly([(x - 2, base - 38), (x + lw - 6, base - 38), (x + lw, base - 32), (x + lw - 6, base - 26), (x - 2, base - 26)], OUT)
    cv.poly([(x - 1, base - 37), (x + lw - 6, base - 37), (x + lw - 1, base - 32), (x + lw - 6, base - 27), (x - 1, base - 27)], "#2a4a3a")
    cv.hline(x - 1, base - 37, lw - 5, "#3a6a50")
    text(cv, "NORLIN", x + 2, base - 38, "#e6e2c8")


def paint(show=True, screen=None):
    """The whole background. show=False paints the show over (for the encore overlay); screen
    picks what the LED wall shows (default: the mountains during the show, dark after)."""
    bg = Canvas(W, H, fill="#171a2b", seed=61)
    rng = np.random.default_rng(62)
    info = {"twinkles": []}

    # --- sky and the far side of the field --------------------------------------------------------
    sky, _ = F.farrand_sky(W, 150, panels=(0, 1, 0, 1), offset=150, scale=2.0, stars=50, seed=27)
    bg.a[:150] = sky
    F.far_hedge(bg, 0, W, FAR_EDGE, seed=41)
    F.treeline_back(bg, -10, W + 10, FAR_EDGE + 6, seed=43, heights=(56, 94), gap=(40, 74), skip=[(200, 680)])
    for (r, a) in [(50, 0.08), (32, 0.1)]:                                  # food court glow far left
        bg.ellipse(-r // 2, 100 - r // 3, r * 2, r, C(F.BULB[1], a))
    tent, tax, tay = F.peaked_tent(96, 30, 20, open_front=False, seed=4, valance_text=None, ropes=False,
                                   poles=[0, 47, 95], windows=True)
    haze = np.array(C("#2a2440")[:3], np.float32)
    tent.a[..., :3] = tent.a[..., :3] * 0.8 + haze * 0.2
    bg.paste(tent, 96 - tax, FAR_EDGE + 4 - tay)
    info["campus"] = G.campus_far(bg, 676, FAR_EDGE - 4, w=124, seed=3)
    F.lawn(bg, 0, FAR_EDGE, W, H - FAR_EDGE, seed=63, clover=0.03, leaves=0.06, stripes=(48, 0.0))
    bg.rect(0, FAR_EDGE, W, WALK_TOP - FAR_EDGE + 4, C("#2a2440", 0.3))
    # the crew fence on the right with a cabin roof behind, the fingerpost to Norlin
    for k in range(2):
        x0 = 676 + k * 64
        bg.rect(x0, WALK_TOP - 38, 58, 26, OUT)
        bg.rect(x0 + 1, WALK_TOP - 37, 56, 24, G.CABIN[2]); bg.hline(x0 + 1, WALK_TOP - 37, 56, G.CABIN[4])
        for sx in range(x0 + 4, x0 + 56, 4):
            bg.vline(sx, WALK_TOP - 35, 22, G.CABIN[1])
        bg.rect(x0 + 10, WALK_TOP - 31, 12, 8, OUT); bg.rect(x0 + 11, WALK_TOP - 30, 10, 6, F.BULB[2])
        bg.rect(x0 - 1, WALK_TOP - 41, 60, 4, OUT); bg.hline(x0, WALK_TOP - 40, 58, G.CABIN[5])
    for x in range(664, W):
        k = (x - 664) % 40
        top = WALK_TOP - 30
        if k in (0, 1):
            bg.vline(x, top - 2, 32, F.STEEL[4] if k == 0 else F.STEEL[2])
            continue
        for y in range(top, WALK_TOP - 2):
            bg.px(x, y, G.SCRIM[2] if (x + y) % 3 else G.SCRIM[3])
        bg.px(x, top, G.SCRIM[4])
    lw = text_width("CREW ONLY") + 8
    bg.rect(704, WALK_TOP - 24, lw, 11, OUT); bg.rect(705, WALK_TOP - 23, lw - 2, 9, F.HAZARD[3])
    text(bg, "CREW ONLY", 708, WALK_TOP - 24, "#1a1720")
    norlin_sign(bg, 668, WALK_TOP + 2)
    info["tower"] = F.light_tower(bg, 34, WALK_TOP - 2, 112, seed=6)

    # --- the main stage ----------------------------------------------------------------------------
    stage = G.main_stage(bg, STAGE_CX, DECK_W, DECK_BACK, LIP, ROOF_TOP, rise=18, screen=screen or ("mountains" if show else "off"),
                         lamps_on=show, dim=0.0 if show else 0.62, halo=show, seed=6, face=FACE)
    info["stage"] = stage
    wl, wr = stage["wings"]
    info["twinkles"] += F.festoon(bg, 40, WALK_TOP - 108, wl + 2, ROOF_TOP + 22, sag=14, every=8, seed=5)
    info["twinkles"] += F.festoon(bg, -4, 70, 36, WALK_TOP - 106, sag=6, every=8, seed=6)
    info["twinkles"] += F.festoon(bg, wr + 18, ROOF_TOP + 22, W + 4, 60, sag=16, every=8, seed=7)

    # --- the ground in front ---------------------------------------------------------------------
    for i, (px_, py_, rx, ry) in enumerate([(200, 300, 40, 12), (690, 300, 44, 12), (300, 330, 36, 9),
                                            (600, 334, 40, 9), (140, 440, 50, 10), (760, 390, 30, 9)]):
        F.trodden_patch(bg, px_, py_, rx, ry, seed=70 + i, strength=0.7)
    x0, x1, y0, y1 = PIT
    pit = np.zeros((H, W), bool)
    for r, yy in enumerate(range(y0, y1, 18)):
        off = 23 if r % 2 else 0
        for xx in range(x0 - off, x1, 46):
            a, b = max(x0, xx), min(x1, xx + 46)
            if b - a > 4:
                F.mat_tile(bg, a, yy, b - a, min(18, y1 - yy), seed=int(rng.integers(1e6)), lit=0.1 if show else 0.0)
    pit[y0:y1, x0:x1] = True
    bg.hline(x0, y1, x1 - x0, C("#0d0b16", 0.55)); bg.hline(x0, y1 + 1, x1 - x0, C("#0d0b16", 0.25))
    aisle = F.mat_path_vertical(bg, lambda y: (AISLE[0] + AISLE[1]) / 2, y1, CROSS_Y - 22, width=AISLE[1] - AISLE[0], seed=8)
    cross = F.mat_walkway(bg, lambda x: CROSS_Y, width=44, seed=9)
    F.cable_run(bg, [(560, 246), (556, 280), (520, 300), (500, 340), (498, 380), (500, 470), (506, H)], count=3, seed=11)
    F.cable_run(bg, [(300, 246), (290, 300), (250, 330), (180, 360), (120, 392), (0, 396)], count=2, seed=12, tape_every=54)
    F.cable_ramp_horizontal(bg, AISLE[0] - 4, AISLE[1] + 6, 336)
    F.cable_ramp_vertical(bg, 496, CROSS_Y - 23, CROSS_Y + 23)
    # what the last song left: confetti, setlists, cups, glow sticks
    lawn_mask = np.ones((H, W), bool)
    lawn_mask[:WALK_TOP + 4] = False
    G.confetti(bg, x0 - 10, y0, x1 - x0 + 20, 60, n=190, seed=3, mask=lawn_mask)
    G.confetti(bg, x0 + 40, y1, x1 - x0 - 80, 50, n=50, seed=4, mask=lawn_mask)
    G.confetti(bg, STAGE_CX - 160, LIP - 70, 320, 66, n=60, seed=5, mask=lawn_mask)
    # blankets left by people who sat on the grass at the sides
    G.picnic_blanket(bg, 64, 222, 60, 24, F.TEAL_C, seed=4)
    G.picnic_blanket(bg, 700, 330, 56, 22, F.RED, seed=5, skew=-6)
    for kind, (x, y) in zip(["flyer", "cup", "cup_down", "band", "flyer", "cup", "cup", "band"],
                            [(260, 290), (620, 286), (210, 350), (680, 360), (400, 470), (160, 330), (740, 450), (300, 455)]):
        F.litter(bg, x, y, kind, seed=int(rng.integers(100)))
    for k, (gx, gy, gc) in enumerate([(232, 316, "#7af08a"), (648, 320, "#f07ad0"), (520, 352, "#7ad0f0"), (380, 300, "#f6e07a")]):
        G.glow_stick(bg, gx, gy, gc, seed=k)
    F.puddle(bg, 690, 470, 28, 6, seed=2, reflect=("#e8a0d0",))
    F.puddle(bg, 70, 330, 20, 5, seed=3)

    # --- light -----------------------------------------------------------------------------------
    if show:
        F.light_pool(bg, STAGE_CX, 268, 240, 28, color="#f0a0c8", strength=0.22)
        F.light_pool(bg, STAGE_CX, 262, 150, 16, strength=0.22)
        F.light_pool(bg, ENCORE[0], ENCORE[1] + 2, 40, 9, color="#fff0c4", strength=0.16)
    else:                                     # the crew's work lights on after the show: cool and flat
        F.light_pool(bg, STAGE_CX, (DECK_BACK + LIP) // 2, 170, 30, color="#c8d8ff", strength=0.14)
        F.light_pool(bg, STAGE_CX, 274, 200, 22, color="#c8d8ff", strength=0.1)
    F.light_pool(bg, LAMP[0] + 2, LAMP[1] + 2, 54, 16, strength=0.3)

    # --- edges -----------------------------------------------------------------------------------
    bg.rect(0, WALK_TOP, 20, H - WALK_TOP, C("#0d0b16", 0.35))
    bg.rect(W - 20, WALK_TOP, 20, H - WALK_TOP, C("#0d0b16", 0.3))
    for y in range(WALK_TOP - 4, H - 20, 14):
        if CROSS_Y - 30 < y < CROSS_Y + 24:
            continue                                        # the aisle out to the audience lawn
        bg.paste(shrub(0, 0, 20, 16, seed=int(rng.integers(1e6))), -8, y)
    for y in range(WALK_TOP - 4, H - 20, 14):
        if not (CROSS_Y - 34 < y < CROSS_Y + 30):
            bg.paste(shrub(0, 0, 20, 16, seed=int(rng.integers(1e6))), W - 12, y)
    info["gate"] = G.crew_gate(bg, W - 16, CROSS_Y - 26, CROSS_Y + 28)
    x = -6
    while x < W:
        bw = int(rng.integers(30, 40))
        bale, _, _ = F.hay_bales(bw, 18, seed=int(rng.integers(1e6)))
        bg.paste(bale, x, H - 25)
        x += bw + int(rng.integers(0, 12))
    bg.rect(0, H - 24, W, 24, C("#0d0b16", 0.35))
    return bg, info


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg, info = paint(show=True)
    bg.save(os.path.join(out, "background.png"))

    # --- the show over: one overlay for any ending, a GOODNIGHT screen on top for a peaceful one;
    # the AGAIN screen for the blink layer. Each is the difference from a full repaint, so the gear
    # standing in front of the screen stays in front.
    def crop(a, b, name):
        diff = np.abs(a.a - b.a).sum(-1) > 1e-3
        ys, xs = np.nonzero(diff)
        x0, x1, y0, y1 = int(xs.min()), int(xs.max()) + 1, int(ys.min()), int(ys.max()) + 1
        piece = Canvas(x1 - x0, y1 - y0)
        piece.a = a.a[y0:y1, x0:x1].copy()
        piece.save(os.path.join(out, name))
        return x0, y0

    overlays = []
    over, _ = paint(show=False)
    x0, y0 = crop(over, bg, "show-over.png")
    overlays.append({"texture": res + "show-over.png", "x": x0, "y": y0, "flag": "encore_resolution"})
    night, _ = paint(show=False, screen="goodnight")
    x0, y0 = crop(night, over, "screen-goodnight.png")
    overlays.append({"texture": res + "screen-goodnight.png", "x": x0, "y": y0, "flag": "encore_resolution", "equals": "peaceful"})
    again, _ = paint(show=True, screen="again")
    again_at = crop(again, bg, "screen-again.png")
    sx, sy, sw, sh = info["stage"]["screen"]

    # --- props -----------------------------------------------------------------------------------
    props = {}

    def save(index, sprite, ax, ay, extra=None, name=None):
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [int(ax), int(ay)]}
        entry.update(extra or {})
        props[str(index)] = entry

    over_flag = lambda name: {"flag": "encore_resolution", "flag_texture": res + name}
    front, fax, fay, finfo = G.stage_front(DECK_W, FACE, seed=6)
    dark, _, _, _ = G.stage_front(DECK_W, FACE, seed=6, lamps=False, lip=DIM_LIP, leds=False)
    dark.save(os.path.join(out, "prop-0-dark.png"))
    save(0, front, fax, fay, over_flag("prop-0-dark.png"))
    for i in range(2):
        sub, sax, say = G.sub_stack(38, 68, seed=i)
        quiet, _, _ = G.sub_stack(38, 68, seed=i, on=False)
        quiet.save(os.path.join(out, f"prop-{1 + i}-quiet.png"))
        save(1 + i, sub, sax, say, over_flag(f"prop-{1 + i}-quiet.png"))
    for i in range(2):
        save(3 + i, *G.chair_row(120, 30, seed=30 + i))
    gl, gax, gay, bulb = G.ghost_light(55, seed=1)
    save(5, gl, gax, gay)
    bulb_room = (LAMP[0] - gax + bulb[0], LAMP[1] - gay + bulb[1])

    # --- animation -------------------------------------------------------------------------------
    st = info["stage"]
    arch = st["arch"]
    wl, wr = st["wings"]
    off = {"flag": "encore_resolution", "when": False}
    on_set = {"flag": "encore_resolution"}
    lamps = [[x, y, c, 1] for (x, y, c) in st["lamps"]]
    work = [[x, y, "e8f0ff", 1] for (x, y, c) in st["lamps"][2::4]]
    scan = [dict({"kind": "blink", "pattern": "".join("1" if k == j else "0" for k in range(10)), "rate": 5.0,
                  "rects": [[sx, sy + j * sh // 8, sw, 2, "b8a8e8", 0.12]]}, **off) for j in range(8)]
    sway = {"kind": "beam", "x": STAGE_CX + 6, "y": arch(STAGE_CX + 6) + 20, "angle": 86, "sweep": 9, "period": 6.0,
            "phase": 0.0, "length": 300, "width": 46, "color": "fff0c4", "alpha": 0.22, "floor": ENCORE[1] + 2}
    layers = [
        dict({"kind": "beam", "x": wl + 10, "y": max(4, arch(wl) - 4), "angle": -112, "sweep": 16, "period": 9.0, "phase": 0.0,
              "length": 140, "width": 26, "color": "c8b0ff", "alpha": 0.16, "floor": -400}, **off),
        dict({"kind": "beam", "x": wr + 10, "y": max(4, arch(wr) - 4), "angle": -68, "sweep": 16, "period": 10.5, "phase": 2.2,
              "length": 140, "width": 26, "color": "ffd0e8", "alpha": 0.15, "floor": -400}, **off),
        dict(sway, **off),
        dict({"kind": "beam", "x": 340, "y": arch(340) + 22, "angle": 100, "sweep": 10, "period": 7.0, "phase": 1.0,
              "length": 200, "width": 36, "color": "f2b0d0", "alpha": 0.15, "floor": 286}, **off),
        dict({"kind": "beam", "x": 556, "y": arch(556) + 22, "angle": 78, "sweep": 12, "period": 8.5, "phase": 3.4,
              "length": 200, "width": 36, "color": "c8b0ff", "alpha": 0.15, "floor": 290}, **off),
        dict({"kind": "blink", "pattern": "00001111", "rate": 1.2, "texture": res + "screen-again.png", "x": again_at[0], "y": again_at[1]}, **off),
    ] + scan + [
        {"kind": "twinkle", "points": info["twinkles"] + info["gate"] + info["campus"], "rate": 1.8, "min": 0.4},
        dict({"kind": "twinkle", "points": lamps + [[x, y, "fff0c4", 1] for (x, y) in st["tower_lamps"]], "rate": 1.3, "min": 0.5}, **off),
        dict({"kind": "twinkle", "points": work, "rate": 0.5, "min": 0.8}, **on_set),
        {"kind": "twinkle", "points": [[x, y, "fff0c4", 1] for (x, y) in info["tower"]] +
                                      [[int(bulb_room[0]), int(bulb_room[1]), "f6cf7a", 2]], "rate": 1.0, "min": 0.6},
        dict({"kind": "particles", "style": "dust", "count": 16, "rect": [STAGE_CX - 120, 150, 240, 70], "speed": [0, -4],
              "color": "f6e0b0"}, **off),
        dict({"kind": "particles", "style": "dust", "count": 8, "rect": [ENCORE[0] - 24, ENCORE[1] - 80, 48, 80], "speed": [0, -3],
              "color": "fff0c4"}, **off),
    ]
    return {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": overlays,
        "fauna": [
            {"kind": "moth", "x": int(bulb_room[0]) - 2, "y": int(bulb_room[1]) + 4, "range": 5, "speed": 1.8, "rate": 8.0},
            {"kind": "moth", "x": int(bulb_room[0]) + 3, "y": int(bulb_room[1]) + 2, "range": 4, "speed": 1.4, "rate": 7.0, "flip": True},
            {"kind": "rabbit", "x": 744, "y": 300, "range": 0, "speed": 0.0, "rate": 0.6},
            {"kind": "bat", "x": 120, "y": 30, "fly": 18.0, "rate": 7.0},
            {"kind": "bat", "x": 700, "y": 18, "fly": 14.0, "rate": 6.0},
        ],
        "leaves": [],
        "layers": layers,
    }


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT))[:300])
