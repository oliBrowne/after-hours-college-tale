"""Farrand / backstage (F05): the crew yard behind the main stage at dusk. Along the back, the black
scrim fence with the gate through to the volunteer tent (its striped roof showing over the fence),
the GREEN ROOM cabin with its door open on a warm room, the generator (a cat asleep on its warm
roof), the PRODUCTION cabin with the night's run order on a whiteboard, and, filling the back
right, the stage itself from behind: the arched truss climbing off the top, a bay of scrim rolled
up on the back of the LED wall with the show's light leaking round it, the load-in ramp. Down the
right edge the stage's side scaffold opens on the wings, washed pink. On the yard: aluminium
trackway (the crew road from the lawn to the wings, a path to the tent gate, an apron along the
cabins, a path from the stage ramp), cable looms with ramps, mud. Props: a steel gear rack, a
stack of backline cases, the prep table with the EVERYONE PERFORMS poster, the ONE SONG cue
board, a tripod work light."""
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

ROOM = "F05"
W, H = 800, 480
WALK_TOP = 142
WALK_BOTTOM = 456
BACK = WALK_TOP + 2               # base line of everything along the back
GATE = (72, 128)                  # gap in the fence: the volunteer shortcut (100, 170)
THRU = (362, 418)                 # the crew road: audience lawn (60, 390) to the wings (710, 390)
GATE_PATH = (76, 124)
APRON = (124, 548, 196)           # trackway along the cabins: x0, x1, bottom y
STAGE_X0 = 548                    # the stage fills the back from here
STAGE_PATH = (556, 644)           # trackway from the load-in ramp down to the crew road
WING = (352, 426)                 # the opening in the stage's side scaffold (right edge)
GREEN = (162, 168)                # GREEN ROOM cabin x, width
GEN_X = 334
PROD = (398, 150)                 # PRODUCTION cabin x, width
BOARD = (432, 92, 90, 42)         # run order whiteboard on the production cabin
LAMP = (100, 300)
RUG = (322, 298, 166, 60)         # the artists' rug under the prep table
KEEPSAKE = (748, 294)             # keep clear


def tent_beyond(cv):
    """The volunteer tent beyond the fence, its striped roof over the scrim, lit inside."""
    tent, ax, ay = F.peaked_tent(156, 44, 30, open_front=False, seed=4, valance_text=None, ropes=False,
                                 poles=[0, 52, 103, 155], windows=True)
    haze = np.array(C("#2a2440")[:3], np.float32)
    tent.a[..., :3] = tent.a[..., :3] * 0.84 + haze * 0.16          # a little distance haze
    cv.paste(tent, 96 - ax, 122 - ay)


def run_board_line(cv, x, y, s):
    """One line of the run order (the whiteboard's second line can change with Imani's choice)."""
    cv.rect(x, y, 80, 9, "#f2f0e8")
    text(cv, s, x, y - 2, "#1e2a5a" if not s.startswith("2 IMANI") else "#a02a24")


def run_board(cv):
    """The night's run order on a whiteboard screwed to the production cabin."""
    x, y, w, h = BOARD
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT); cv.rect(x, y, w, h, "#55525e")
    cv.rect(x + 2, y + 2, w - 4, h - 4, "#f2f0e8"); cv.hline(x + 2, y + 2, w - 4, "#ffffff")
    text(cv, "RUN ORDER", x + (w - text_width("RUN ORDER")) // 2, y + 1, "#c8382c")
    cv.hline(x + 6, y + 10, w - 12, "#c8382c")
    for k, s in enumerate(["1 CHIP", "2 EVERYONE", "3 AGAIN"]):
        run_board_line(cv, x + 5, y + 13 + k * 9, s)
    cv.rect(x + 2, y + h - 3, w - 4, 2, "#3a3844"); cv.hline(x + 10, y + h - 4, 7, "#2a3a8a")


def stage_side(cv, show=True):
    """The stage's side scaffold down the right edge, clad in scrim, open on the wings."""
    x0 = W - 18
    for x in range(x0, W):
        for y in range(BACK - 2, WALK_BOTTOM + 2):
            if WING[0] <= y < WING[1]:
                continue
            cv.px(x, y, G.SCRIM[2] if (x + y) % 3 else G.SCRIM[3])
    for sx in (x0, W - 6):
        cv.rect(sx - 1, BACK - 4, 4, WALK_BOTTOM - BACK + 8, OUT); cv.vline(sx, BACK - 3, WALK_BOTTOM - BACK + 6, G.TRUSS[5])
        cv.vline(sx + 1, BACK - 3, WALK_BOTTOM - BACK + 6, G.TRUSS[3])
    for ly in range(BACK + 20, WALK_BOTTOM, 46):
        if not (WING[0] - 4 <= ly < WING[1] + 4):
            cv.rect(x0, ly, 18, 3, OUT); cv.hline(x0, ly + 1, 18, G.TRUSS[4])
    # the wings: a slice of the stage's wash, a flight-case step up, a lit edge
    wy0, wy1 = WING
    bands = G.WASH[3:] if show else ["#1a1420", "#1e1824", "#221a28", "#261e2c", "#2a2030", "#2e2234"]
    for i, y in enumerate(range(wy0, wy1)):
        t = (y - wy0) / (wy1 - wy0)
        cv.hline(x0, y, 18, bands[min(len(bands) - 1, int(t * len(bands)))])
    for k in range(3):
        sy = wy1 - 10 - k * 8
        cv.rect(x0 + 2 + k * 5, sy, 18, 8, OUT); cv.rect(x0 + 3 + k * 5, sy + 1, 16, 6, G.CASE[2]); cv.hline(x0 + 3 + k * 5, sy + 1, 16, G.CASE[5])
    cv.rect(x0 - 2, wy0 - 3, 20, 3, OUT); cv.rect(x0 - 2, wy1, 20, 3, OUT)
    red, green = G.cue_light(cv, x0 - 1, wy0 - 30)
    return red, green


def build_background(show=True):
    """Paint the whole background; show=False paints the stage with the show over (for the
    encore_resolution overlay). Returns (Canvas, info)."""
    bg = Canvas(W, H, fill="#171a2b", seed=51)
    info = {"twinkles": []}
    rng = np.random.default_rng(52)

    # --- sky, trees, the tent beyond the fence ---------------------------------------------------
    sky, _ = F.farrand_sky(W, 150, panels=(0, 1, 0, 1), offset=40, scale=2.0, stars=50, seed=23)
    bg.a[:150] = sky
    F.treeline_back(bg, -10, STAGE_X0 + 10, BACK - 30, seed=35, heights=(58, 96), gap=(40, 70))
    F.far_hedge(bg, 0, STAGE_X0, BACK - 34, seed=36)
    tent_beyond(bg)
    F.lawn(bg, 0, BACK - 30, W, H - BACK + 30, seed=53, clover=0.02, leaves=0.05)

    # --- along the back: fence and gate, cabins, generator, the stage ----------------------------
    info["gate"] = G.scrim_fence(bg, -20, GREEN[0] + 4, BACK, height=58, panel=92, gaps=[GATE], seed=5,
                                 signs=[(10, "CREW")])
    green = G.portacabin(bg, GREEN[0], BACK, GREEN[1], 76, "GREEN ROOM", seed=1, door_x=18, door_open=True,
                         windows=[(110, 24), (138, 24)], ac=False, notices=1)
    gen = G.generator(bg, GEN_X, BACK, w=60, h=30, label="GEN3")
    prod = G.portacabin(bg, PROD[0], BACK, PROD[1], 76, "PROD", seed=2, door_x=8,
                        windows=[], ac=True, notices=1)
    run_board(bg)
    info["stage"] = G.stage_back(bg, STAGE_X0, W, BACK + 2, seed=4, show=show)
    info["green"], info["prod"], info["gen"] = green, prod, gen
    # festoon from the gate post to the green room and on to the production cabin
    info["twinkles"] += F.festoon(bg, GATE[1], BACK - 66, GREEN[0] + 10, BACK - 74, sag=8, every=8, seed=7)
    info["twinkles"] += F.festoon(bg, GREEN[0] + GREEN[1] - 6, BACK - 78, PROD[0] + 8, BACK - 78, sag=12, every=8, seed=8)

    # --- the yard ------------------------------------------------------------------------------
    for i, (px_, py_, rx, ry) in enumerate([(250, 214, 50, 12), (520, 230, 40, 10), (190, 300, 36, 10),
                                            (700, 250, 50, 14), (420, 440, 90, 8), (690, 444, 60, 8), (300, 340, 40, 10)]):
        F.trodden_patch(bg, px_, py_, rx, ry, seed=60 + i, strength=0.6)
    # tyre ruts from the load-in vans across the right of the yard
    for k, dy in enumerate((0, 22)):
        for x in range(640, 782):
            y = 300 + dy + int(round(10 * np.sin((x - 640) / 60)))
            bg.hline(x, y, 1, C(F.DIRT[1], 0.45)); bg.px(x, y + 1, C(F.DIRT[2], 0.35))
            if x % 7 == 0:
                bg.px(x, y, C(F.DIRT[0], 0.5))
    G.rug(bg, RUG[0], RUG[1], RUG[2], RUG[3], seed=3)
    G.trackway(bg, GATE_PATH[0], BACK, GATE_PATH[1] - GATE_PATH[0], THRU[0] - BACK, panel=(24, 30), along="y", seed=2)
    G.trackway(bg, APRON[0], BACK, APRON[1] - APRON[0], APRON[2] - BACK, panel=(58, 26), along="x", seed=3)
    G.trackway(bg, STAGE_PATH[0], BACK, STAGE_PATH[1] - STAGE_PATH[0], THRU[0] - BACK, panel=(44, 30), along="y", seed=4)
    G.trackway(bg, 0, THRU[0], W - 18, THRU[1] - THRU[0], panel=(58, 28), along="x", seed=1)
    # cable looms: generator to the stage (over a ramp on the stage path), the FOH multicore out to
    # the lawn, the production feed to the cue board, a run across the crew road under a ramp
    G.cable_loom(bg, [(GEN_X + 44, BACK - 2), (GEN_X + 52, 206), (470, 214), (548, 210), (650, 214), (720, 226), (W - 18, 236)], seed=1)
    G.cable_loom(bg, [(W - 18, 432), (600, 436), (400, 440), (200, 436), (0, 440)], seed=2, count=6)
    F.cable_run(bg, [(PROD[0] + 70, BACK - 2), (480, 182), (466, 214)], count=2, seed=3, tape_every=0)
    F.cable_run(bg, [(262, 246), (258, 300), (262, 362), (262, 418), (250, 436)], count=3, seed=4)
    F.cable_ramp_horizontal(bg, STAGE_PATH[0] - 4, STAGE_PATH[1] + 4, 207)
    F.cable_ramp_vertical(bg, 256, THRU[0], THRU[1])
    F.cable_run(bg, [(LAMP[0] + 6, LAMP[1]), (130, 318), (150, 344), (160, 362)], count=1, seed=5, tape_every=0)
    # tape on the crew road: an arrow and a marker label pointing to the wings, one up to the tent
    F.tape_arrow(bg, 668, 390, direction=1, colour=["#c8c4b8", "#e8e4d8", "#f6f4ee"], length=18)
    lw = text_width("STAGE") + 4
    bg.rect(612, 384, lw, 9, "#e8e4d8"); bg.hline(612, 384, lw, "#f6f4ee")
    text(bg, "STAGE", 614, 383, "#2a2a36")
    F.tape_arrow(bg, 100, 240, direction="up", colour=["#c8c4b8", "#e8e4d8", "#f6f4ee"], length=16)
    # puddles and dropped things
    F.puddle(bg, 190, 444, 26, 6, seed=4, reflect=("#f6cf7a",))
    F.puddle(bg, 712, 196, 22, 6, seed=5, reflect=("#e8a0d0",))
    F.puddle(bg, 360, 340, 14, 4, seed=6)
    for kind, (x, y) in zip(["cup", "flyer", "band", "cup_down", "flyer", "cup", "band"],
                            [(220, 330), (520, 260), (300, 210), (680, 330), (150, 210), (590, 440), (40, 330)]):
        F.litter(bg, x, y, kind, seed=int(rng.integers(100)))

    # --- light ---------------------------------------------------------------------------------
    F.light_pool(bg, LAMP[0] + 18, LAMP[1] + 4, 70, 22, color="#fff0c4", strength=0.26)
    F.light_pool(bg, LAMP[0] + 30, LAMP[1] + 2, 36, 10, color="#fff0c4", strength=0.2)
    lx, ly = green["lamp"]
    F.light_pool(bg, lx, BACK + 10, 40, 10, strength=0.24)
    lx, ly = prod["lamp"]
    F.light_pool(bg, lx, BACK + 8, 30, 8, strength=0.2)
    if show:
        F.light_pool(bg, W - 40, (WING[0] + WING[1]) // 2, 120, 30, color="#f0a0c8", strength=0.24)
        F.light_pool(bg, W - 20, (WING[0] + WING[1]) // 2, 50, 18, color="#c8a0f0", strength=0.2)
        F.light_pool(bg, 600, BACK + 6, 60, 10, color="#f0a0c8", strength=0.14)

    # --- edges ---------------------------------------------------------------------------------
    info["wing_cue"] = stage_side(bg, show)
    bg.rect(0, WALK_TOP, 20, H - WALK_TOP, C("#0d0b16", 0.35))
    for y in range(WALK_TOP - 2, H - 20, 14):
        if THRU[0] - 8 < y < THRU[1] - 4:
            continue                                    # the crew road out to the audience lawn
        bg.paste(shrub(0, 0, 20, 16, seed=int(rng.integers(1e6))), -8, y)
    # the perimeter fence along the bottom, seen from inside: scrim and the top rail with clamps
    fy = WALK_BOTTOM + 3
    for x in range(0, W):
        for y in range(fy + 3, H):
            bg.px(x, y, G.SCRIM[1] if (x + y) % 3 else G.SCRIM[2])
        bg.px(x, fy + 3, G.SCRIM[3])
    bg.rect(0, fy, W, 3, OUT); bg.hline(0, fy + 1, W, F.STEEL[4])
    for px_ in range(30, W, 92):
        bg.rect(px_ - 3, fy - 1, 7, 6, OUT); bg.rect(px_ - 2, fy, 5, 4, F.STEEL[3]); bg.hline(px_ - 2, fy, 5, F.STEEL[5])
    bg.rect(0, H - 24, W, 24, C("#0d0b16", 0.3))
    return bg, info


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg, info = build_background(show=True)
    bg.save(os.path.join(out, "background.png"))
    res = f"res://assets/art/rooms/{ROOM}/"

    # --- overlays: the show over (encore resolved), Imani's line on the run order -------------
    overlays = []
    dark, _ = build_background(show=False)
    diff = np.abs(dark.a - bg.a).sum(-1) > 1e-3
    ys, xs = np.nonzero(diff)
    if len(xs):
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        piece = Canvas(int(x1 - x0), int(y1 - y0))
        piece.a = dark.a[y0:y1, x0:x1].copy()
        piece.save(os.path.join(out, "show-over.png"))
        overlays.append({"texture": res + "show-over.png", "x": int(x0), "y": int(y0), "flag": "encore_resolution"})
    bx, by, bw, bh = BOARD
    for value, line in (("honest", "2 IMANI VERSE"), ("instrumental", "2 IMANI INSTR")):
        piece = Canvas(82, 10)
        run_board_line(piece, 1, 1, line)
        piece.save(os.path.join(out, f"run-{value}.png"))
        overlays.append({"texture": res + f"run-{value}.png", "x": bx + 4, "y": by + 13 + 9 - 1,
                         "flag": "imani_performance", "equals": value})
    piece = Canvas(82, 10)
    run_board_line(piece, 1, 1, "3 GOODNIGHT")
    piece.save(os.path.join(out, "run-goodnight.png"))
    overlays.append({"texture": res + "run-goodnight.png", "x": bx + 4, "y": by + 13 + 18 - 1, "flag": "encore_resolution"})

    # --- props ---------------------------------------------------------------------------------
    props = {}

    def save(index, sprite, ax, ay, extra=None, name=None):
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [int(ax), int(ay)]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(0, *G.gear_rack(100, 90, seed=1))
    save(1, *G.case_stack(100, 85, seed=2))
    chosen, cax, cay = G.prep_table(140, 30, seed=3, chosen=True)
    chosen.save(os.path.join(out, "prop-2-chosen.png"))
    save(2, *G.prep_table(140, 30, seed=3), extra={"flag": "imani_performance", "flag_texture": res + "prop-2-chosen.png"})
    stop, sax, say = G.cue_board(70, 42, stop=True)
    stop.save(os.path.join(out, "prop-3-stop.png"))
    save(3, *G.cue_board(70, 42), extra={"flag": "imani_performance", "flag_texture": res + "prop-3-stop.png"})
    light, lax, lay, head = G.work_light(55)
    save(4, light, lax, lay)
    head_room = (LAMP[0] - lax + head[0], LAMP[1] - lay + head[1])

    # --- animation -----------------------------------------------------------------------------
    st = info["stage"]
    red, green = info["wing_cue"]
    gen = info["gen"]
    show_off = {"flag": "encore_resolution", "when": False}
    wy0, wy1 = WING
    layers = [
        dict({"kind": "beam", "x": 700, "y": 14, "angle": -104, "sweep": 14, "period": 9.5, "phase": 0.5,
              "length": 120, "width": 24, "color": "ffd0e8", "alpha": 0.15, "floor": -400}, **show_off),
        dict({"kind": "beam", "x": 770, "y": 8, "angle": -80, "sweep": 16, "period": 8.0, "phase": 2.6,
              "length": 120, "width": 24, "color": "c8b0ff", "alpha": 0.15, "floor": -400}, **show_off),
        # the wash in the wings breathing with the music
        dict({"kind": "blink", "pattern": "1100", "rate": 2.0, "rects": [[W - 18, wy0, 18, wy1 - wy0, "f0a0c8", 0.18]]}, **show_off),
        dict({"kind": "blink", "pattern": "0011", "rate": 2.0, "rects": [[W - 18, wy0, 18, wy1 - wy0, "a890f0", 0.16]]}, **show_off),
        # cue light: red standby, then a green go now and then
        dict({"kind": "blink", "pattern": "1111111000", "rate": 2.0, "rects": [[red[0], red[1], 4, 4, "ff4a3a"], [red[0] - 2, red[1] - 2, 8, 8, "ff4a3a", 0.25]]}, **show_off),
        dict({"kind": "blink", "pattern": "0000000110", "rate": 2.0, "rects": [[green[0], green[1], 4, 4, "5cf08a"], [green[0] - 2, green[1] - 2, 8, 8, "5cf08a", 0.25]]}, **show_off),
        # the green room telly flickering behind the blind
        {"kind": "blink", "pattern": "10110100", "rate": 3.0, "rects": [[info["green"]["windows"][0][0], info["green"]["windows"][0][1] + 8, 30, 8, "a8c8ff", 0.18]]},
        {"kind": "blink", "pattern": "10", "rate": 0.8, "rects": [[gen["led"][0], gen["led"][1], 1, 1, "5cf08a"]]},
        {"kind": "twinkle", "points": info["twinkles"] + info["gate"], "rate": 1.8, "min": 0.4},
        dict({"kind": "twinkle", "points": st["lamps"] and [[p[0], p[1], p[2] if len(p) > 2 else "fff0c4", 1] for p in st["lamps"]],
              "rate": 1.3, "min": 0.5}, **show_off),
        {"kind": "twinkle", "points": st["leds"], "rate": 0.7, "min": 0.3},
        {"kind": "twinkle", "points": st["blues"], "rate": 0.6, "min": 0.6},
        {"kind": "twinkle", "points": [[info["green"]["lamp"][0], info["green"]["lamp"][1], "fff0c4", 1],
                                       [info["prod"]["lamp"][0], info["prod"]["lamp"][1], "fff0c4", 1]], "rate": 1.0, "min": 0.7},
        {"kind": "particles", "style": "dust", "count": 10, "rect": [head_room[0] - 10, head_room[1] - 6, 70, 40],
         "speed": [2, 3], "color": "fff0c4"},
        {"kind": "particles", "style": "dust", "count": 6, "rect": [gen["exhaust"][0] - 4, gen["exhaust"][1] - 24, 14, 22],
         "speed": [3, -8], "color": "8a8496"},
    ]
    return {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": overlays,
        "fauna": [
            {"kind": "library_cat", "x": GEN_X + 30, "y": BACK - 34, "range": 0, "speed": 0.0, "rate": 0.5},
            {"kind": "moth", "x": head_room[0] - 3, "y": head_room[1] + 4, "range": 6, "speed": 2.0, "rate": 8.0},
            {"kind": "moth", "x": info["green"]["lamp"][0] + 3, "y": info["green"]["lamp"][1] + 5, "range": 4, "speed": 1.6, "rate": 7.0, "flip": True},
            {"kind": "bat", "x": 300, "y": 30, "fly": 16.0, "rate": 7.0},
        ],
        "leaves": [],
        "layers": layers,
    }


if __name__ == "__main__":
    print(json.dumps(build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT))[:300])
