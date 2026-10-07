"""Graduation stage (M06): VAL's ceremony, "everyone you could be".

Back band: Macky's gilt proscenium with the red house curtain swagged up, and on the stage behind
it VAL's graduation set: three risers of ceremony chairs facing the house, a RESERVED card on every
seat, CU black-and-gold bunting, chairs flown on lines above, VAL's emblem (a teal frame with brass
finials) at giant scale holding rows of mortarboards that fade into the dark, the night-blue
cyclorama behind. Over the proscenium hangs the banner EVERYONE YOU COULD BE. The house side walls
flank it: an opera box with reserved chairs on the left, a tall window on the right, brass sconces.
Floor: the thrust stage (oak deck, spike marks) in front of the arch, its front lip a prop with
footlights; the house floor in oak boards with a red procession runner from the lobby aisle to the
stage and a cross aisle to both side exits, gold tape marks for seats that are not there, a cold
spotlight pool where VAL stands.
Dawn (background_dawn, after VAL): house lights up, the cards gone, the flown chairs struck,
the frame just a frame, the window full of sunrise throwing a shaft across the floor, the dawn
exit (bottom right) spilling morning light, and the sign ONE GATHERING / ENDED over the banner
(overlay on dawn_started).
Props: stage front (footlights off at dawn), the reserved row (cards gone with val_resolution),
two PA columns, the ghost light."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, mix, shade
from surfaces import light_pool
from lib_farrand2 import ghost_light
from lib_macky2 import (HOUSE, HOUSE_DAWN, OAKF, OAK_FLOOR_M, CU_GOLD, CU_BLACK, CARD, VAL_TEAL, _rng, halo,
                        house_wall, proscenium, upstage_set, grad_banner, ended_sign, plank_floor, runner_m,
                        stage_lip, pa_column, reserved_row, ceremony_chair)

ROOM = "M06"
W, H = 960, 540
BASE = 142
WALK = (20, 142, 920, 374)
PROS = (176, 794, 4)                      # proscenium outer x0, x1, top
DECK = (220, 750, 226)                    # thrust stage deck: x0, x1, front y (lip prop below)
BOX_L = (40, 46, 104, 50)                 # opera box on the left wall
WINDOW_R = (858, 40, 34, 64)              # tall window on the right wall
SCONCES = [(22, 100), (160, 100), (812, 96), (942, 96)]
VAL_SPOT = (485, 330)
RUNNER_X = (457, 513)                     # centre aisle
CROSS_Y = (446, 480)                      # cross aisle to the side exits
LOBBY_X = (372, 428)                      # runner from the cross aisle down to the lobby return
LAMP = (190, 429)
SEATS = (725, 344)
BANNER_Y = 8
OAK_FLOOR_DAWN = ["#2e1e18", "#3e2a20", "#523626", "#62422e", "#704c34", "#7e583c", "#946a4a"]
DECK_NIGHT = ["#16100e", "#221814", "#30221c", "#3c2a22", "#48342a", "#544032", "#66503e"]
DECK_DAWN = ["#2a1e1a", "#3a2a22", "#4a362a", "#584032", "#664a3a", "#745644", "#866650"]


def back_band(bg, dawn):
    """House walls, the set inside the arch, the proscenium and the banner. Returns set info."""
    x0, x1, top = PROS
    cards = house_wall(bg, 0, x0, 0, BASE, dawn=dawn, seed=3, box=BOX_L, sconces=SCONCES[:2], cards=not dawn)
    house_wall(bg, x1, W, 0, BASE, dawn=dawn, seed=4, window=WINDOW_R, sconces=SCONCES[2:])
    info = upstage_set(bg, x0 + 20, x1 - 20, top + 22, BASE, dawn=dawn, seed=5, frame_dy=20)
    proscenium(bg, x0, x1, top, BASE, dawn=dawn)
    if not dawn:
        info["banner"] = grad_banner(bg, (x0 + x1) // 2, BANNER_Y)
    else:
        # at dawn the banner is furled to its batten (the overlay sign hangs in front of it)
        bx = (x0 + x1) // 2 - 140
        bg.rect(bx, BANNER_Y, 280, 6, CU_BLACK[1]); bg.hline(bx, BANNER_Y, 280, CU_GOLD[3])
        for k in range(0, 280, 40):
            bg.rect(bx + k + 18, BANNER_Y - 1, 3, 8, "#6a5a4a")
    info["cards"] += cards
    return info


def floor(bg, dawn):
    fl = np.zeros((H, W), bool)
    fl[BASE:, :] = True
    deck = np.zeros_like(fl)
    deck[BASE:DECK[2], DECK[0]:DECK[1]] = True
    house = fl & ~deck
    plank_floor(bg, house, pal=OAK_FLOOR_DAWN if dawn else OAK_FLOOR_M, seed=11, row=10, seam=2, tones=(3, 5), length=(90, 200))
    # the deck: darker stage boards running across, a lit edge under the arch
    plank_floor(bg, deck, pal=DECK_DAWN if dawn else DECK_NIGHT, seed=12, row=7, grow=0.2, seam=2, tones=(3, 5), length=(80, 180))
    bg.hline(DECK[0], BASE, DECK[1] - DECK[0], "#0a0608")
    # deck sides (the stage's side faces seen at the ends)
    for (sx, d) in ((DECK[0] - 4, 1), (DECK[1], -1)):
        bg.rect(sx, BASE, 4, DECK[2] - BASE + 24, OUT_SIDE)
    # spike marks and glow tape on the deck
    rng = _rng(13)
    for _ in range(14):
        tx, ty = int(rng.integers(DECK[0] + 20, DECK[1] - 20)), int(rng.integers(BASE + 8, DECK[2] - 8))
        c = ["#e0c040", "#d04040", "#40a0d0", "#e8e8e0"][int(rng.integers(4))]
        bg.hline(tx, ty, 4, C(c, 0.8)); bg.vline(tx, ty - 1, 3, C(c, 0.8))
    for (gx, gy) in [(DECK[0] + 14, DECK[2] - 6), (DECK[1] - 16, DECK[2] - 6), ((DECK[0] + DECK[1]) // 2, BASE + 6)]:
        bg.rect(gx, gy, 3, 2, "#9ef0c0" if not dawn else "#6a9a80")
    # procession runner and cross aisle
    run = np.zeros_like(fl)
    run[DECK[2] + 26:CROSS_Y[1], RUNNER_X[0]:RUNNER_X[1]] = True
    run[CROSS_Y[0]:H - 24, LOBBY_X[0]:LOBBY_X[1]] = True          # down to the lobby doors (threshold 6)
    run[BASE:DECK[2], RUNNER_X[0] + 6:RUNNER_X[1] - 6] = True
    run[CROSS_Y[0]:CROSS_Y[1], 0:W] = True
    runner_m(bg, run)
    # gold tape marks where rows of seats would be (every future gets a place)
    for yy in range(280, 430, 36):
        for xx in list(range(56, 400, 44)) + list(range(586, 930, 44)):
            if abs(xx - SEATS[0]) < 90 and abs(yy - SEATS[1]) < 26:
                continue
            if abs(xx - LAMP[0]) < 16 and abs(yy - LAMP[1]) < 14:
                continue
            c = C("#c8a040", 0.75) if not dawn else C("#a08850", 0.55)
            bg.hline(xx, yy, 5, c); bg.vline(xx, yy - 3, 3, c)
    # VAL's mark: its frame taped out on the floor in teal glow tape, brass corners
    fx0, fy0, fx1, fy1 = VAL_SPOT[0] - 78, VAL_SPOT[1] - 30, VAL_SPOT[0] + 78, VAL_SPOT[1] + 14
    tc = C("#58c0b8", 0.8) if not dawn else C("#4a7a74", 0.6)
    for (xa, ya, w_, h_) in ((fx0, fy0, fx1 - fx0, 2), (fx0, fy1, fx1 - fx0, 2), (fx0, fy0, 2, fy1 - fy0), (fx1 - 2, fy0, 2, fy1 - fy0 + 2)):
        bg.rect(xa, ya, w_, h_, tc)
    for (cx_, cy_) in ((fx0, fy0), (fx1 - 2, fy0), (fx0, fy1), (fx1 - 2, fy1)):
        bg.rect(cx_ - 2, cy_ - 1, 6, 4, CU_GOLD[3])
    # programmes dropped on the floor, a scatter of gold and black confetti
    for k in range(9):
        px_, py_ = int(rng.integers(40, 920)), int(rng.integers(262, 500))
        bg.rect(px_ + 1, py_ + 1, 8, 5, C("#0d0b16", 0.35)); bg.rect(px_, py_, 8, 5, "#e6dcc4"); bg.hline(px_, py_, 8, "#fff6e0")
        bg.rect(px_ + 1, py_ + 1, 3, 1, CU_GOLD[2])
    for _ in range(260):
        px_, py_ = int(rng.integers(24, 936)), int(rng.integers(150, 512))
        bg.px(px_, py_, [CU_GOLD[3], CU_GOLD[4], CU_BLACK[3], "#e8e2d0"][int(rng.integers(4))])
    # light
    if not dawn:
        # footlight glow along the deck front, the cold spot where VAL stands
        for yy in range(DECK[2] - 16, DECK[2]):
            bg.hline(DECK[0], yy, DECK[1] - DECK[0], C("#f6cf7a", 0.03 * (yy - DECK[2] + 17) / 4))
        light_pool(bg, VAL_SPOT[0], VAL_SPOT[1] - 2, 86, 30, color="#c8d8ff", strength=0.2)
        light_pool(bg, (DECK[0] + DECK[1]) // 2, BASE + 30, 170, 34, color="#58a0a8", strength=0.2)
        light_pool(bg, LAMP[0], LAMP[1] + 2, 40, 12, color="#f6cf7a", strength=0.18)
    else:
        # morning through the window (a slanting shaft across the right floor) and the open exit
        shaft = np.zeros_like(fl)
        ys, xs = np.mgrid[0:H, 0:W]
        shaft |= (xs > 780 - (ys - BASE) * 1.1) & (xs < 846 - (ys - BASE) * 1.1) & (ys > BASE + 4) & (ys < 410)
        shaft |= (xs > 860 - (ys - BASE) * 1.1) & (xs < 892 - (ys - BASE) * 1.1) & (ys > BASE + 4) & (ys < 410)
        shaft &= fl
        bg.fill_mask(shaft, C("#f6d496", 0.14))
        spill = (xs > 760 + (516 - ys) * 1.2) & (ys > 400) & (ys < 516)
        bg.fill_mask(spill & fl, C("#f8d8a0", 0.16))
        spill2 = (xs > 840 + (516 - ys) * 1.2) & (ys > 420) & (ys < 516)
        bg.fill_mask(spill2 & fl, C("#fff0c8", 0.14))
        light_pool(bg, LAMP[0], LAMP[1] + 2, 36, 10, color="#f6cf7a", strength=0.1)
    # exits: the balcony stair (left) and the dawn exit (right) at the ends of the cross aisle
    for (ex, d) in ((0, 1), (W - 20, -1)):
        bg.rect(ex, CROSS_Y[0] - 10, 20, CROSS_Y[1] - CROSS_Y[0] + 20, "#0e0a10")
    if dawn:
        bg.rect(W - 20, CROSS_Y[0] - 10, 20, CROSS_Y[1] - CROSS_Y[0] + 20, "#f6d8a0")
        bg.rect(W - 20, CROSS_Y[0] - 10, 6, CROSS_Y[1] - CROSS_Y[0] + 20, "#fff0c8")
    # dark margins
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.35))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.35))
    bg.rect(0, WALK[1] + WALK[3], W, H - WALK[1] - WALK[3], C("#0d0b16", 0.45))


OUT_SIDE = "#1a1214"


def paint(dawn):
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    info = back_band(bg, dawn)
    floor(bg, dawn)
    return bg, info


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg, info = paint(False)
    bg.save(os.path.join(out, "background.png"))
    bgd, _ = paint(True)
    bgd.save(os.path.join(out, "background-dawn.png"))

    props = {}

    def save(index, made, name=None, flag=None, flag_made=None, flag_name=None):
        sprite, ax, ay = made[:3]
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        if flag:
            fs = flag_made[0]
            fs.save(os.path.join(out, flag_name))
            entry.update({"flag": flag, "flag_texture": res + flag_name})
        props[str(index)] = entry

    save(0, stage_lip(530, 30), flag="dawn_started", flag_made=stage_lip(530, 30, dawn=True), flag_name="prop-0-dawn.png")
    save(1, reserved_row(145, 40, cards=True, seed=21), flag="val_resolution", flag_made=reserved_row(145, 40, cards=False, seed=21),
         flag_name="prop-1-open.png")
    save(2, pa_column(46, 110, seed=22))
    save(3, pa_column(46, 110, seed=23))
    gl = ghost_light(68, seed=24)
    save(4, gl)

    # overlay: ONE GATHERING / ENDED over the banner once dawn has started
    sign = ended_sign()
    sign.save(os.path.join(out, "sign-ended.png"))
    sx = (PROS[0] + PROS[1]) // 2 - sign.w // 2
    overlays = [{"texture": res + "sign-ended.png", "x": sx, "y": BANNER_Y - 12, "flag": "dawn_started"}]

    # chairs appearing in the risers' gaps while VAL is at large (a slow chase of extra futures)
    ghost = Canvas(16, 22)
    ceremony_chair(ghost, 8, 21, w=13, h=17, card=True, glow=True)
    ghost.a[..., :3] = ghost.a[..., :3] * 0.7 + np.array(C(VAL_TEAL[5])[:3]) * 0.3
    ghost.save(os.path.join(out, "ghost-chair.png"))
    layers = []
    slots = info["slots"]
    for k, (gx, gy) in enumerate(slots):
        pat = ["0"] * (len(slots) + 3)
        for j in range(3):
            pat[(k + j) % len(pat)] = "1"
        layers.append({"kind": "blink", "pattern": "".join(pat), "rate": 1.4, "flag": "dawn_started", "when": False,
                       "texture": res + "ghost-chair.png", "x": gx - 8, "y": gy - 21})
    cards = [[int(x), int(y), "fff8e6", 1] for (x, y) in info["cards"]]
    rng = _rng(31)
    pick = rng.choice(len(cards), min(40, len(cards)), replace=False)
    layers += [
        {"kind": "twinkle", "points": [cards[int(i)] for i in pick] + [[SEATS[0] - 58 + k * 29, SEATS[1] - 29, "fff8e6", 2] for k in range(5)],
         "rate": 1.2, "min": 0.3, "flag": "dawn_started", "when": False},
        {"kind": "beam", "x": 300, "y": 0, "angle": 62, "sweep": 4, "period": 9, "phase": 0.0, "length": 380, "width": 90,
         "color": "c8d8ff", "alpha": 0.16, "floor": VAL_SPOT[1], "flag": "dawn_started", "when": False},
        {"kind": "beam", "x": 680, "y": 0, "angle": 112, "sweep": 5, "period": 11, "phase": 2.0, "length": 380, "width": 80,
         "color": "f6e0b0", "alpha": 0.12, "floor": VAL_SPOT[1] + 6, "flag": "dawn_started", "when": False},
        {"kind": "twinkle", "points": [[x, y + 1, "fde9b6", 1] for (x, y) in SCONCES] + [[LAMP[0], LAMP[1] - 63, "fff0c4", 2]],
         "rate": 1.0, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 20, "rect": [330, 120, 300, 220], "speed": [1, 2], "color": "c8d8ff",
         "flag": "dawn_started", "when": False},
        {"kind": "particles", "style": "dust", "count": 26, "rect": [520, 160, 380, 250], "speed": [-2, -1], "color": "f6d896",
         "flag": "dawn_started"},
    ]
    manifest = {
        "background": res + "background.png",
        "background_dawn": res + "background-dawn.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": overlays,
        "fauna": [
            {"kind": "lamp_moth", "x": LAMP[0], "y": LAMP[1] - 66, "range": 6, "speed": 2.0, "rate": 9.0},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
