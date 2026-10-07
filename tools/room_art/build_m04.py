"""Macky orchestra pit (M04): the score can end.

Standing in the sunken pit and looking toward the stage. Up top, the closed house curtain in
crimson velvet under a swagged pelmet, the gilt proscenium at both edges, footlight hoods along the
apron's oak nosing with a sliver of work light where the curtain halves meet. Below the lip, the pit
wall: acoustic oak slats over black felt, and in the middle the big APPLAUSE level meter (animated:
pinned in the red for as long as the score has no rests, then rising and falling with breaths and
silences once Imani picks a score that can end). Beside it the PROGRAM sheet (ENCORE over and over,
then the chosen running order), the conductor's video monitor, coiled cables, the red QUIET cue
light, the pit call board, and on the right the steel door to the music service stair.
The floor: stained boards with spike tape, gaffer-taped cables, a worn rug at the conductor's
table, dropped parts, warm pools under the stand lights and the ghost light, and the carpeted lobby
stairs at the bottom left.
Props: the orchestra riser (empty chairs in pairs, glowing stand lights, harp, bass, timpani), two
PA stacks, the conductor's score table (dense and endless, or with rests and FINE once
music_ready), the REST blackboard, the ghost light (the rest point)."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from props import OUT, IRON, WOOD
from lib_norlin import runner_n, depth_shade
from lib_macky import (stage_curtain, curtain_valance, proscenium_side, footlight, apron_lip, slat_wall,
                       applause_meter, meter_frame, setlist_paper, crt_monitor, cue_light_box, cable_coil,
                       pit_service_door, pit_floor, concert_poster, spike_mark, gaff_cable, loose_sheet, pit_riser, pa_stack,
                       score_table, rest_board, ghost_light_m, endless_scroll, BRASS, CARD, CARPET_M, SHADOW,
                       STAND_GLOW, COATS)

ROOM = "M04"
W, H = 960, 540
WALL = 142
WALK = (20, 142, 920, 374)
LIP = 50                        # top of the apron lip (stage floor edge)
DADO = 116                      # rail between the slats and the kick plate
PROS = 44                       # width of the proscenium slices at each edge
FOOTLIGHTS = list(range(76, 900, 58))
METER = (360, 70)               # top-left of the applause meter's bezel
METER_COLS, METER_SEGS = 24, 11
SETLIST = (288, 72)
MONITOR = (106, 78)
CUE = (626, 80)
CALLBOARD = (690, 72, 96, 40)
DOOR_X = 870
RISER = (490, 260)
SPEAKERS = [(720, 275), (240, 275)]
TABLE = (490, 344)
LAMP = (140, 424)
STAIRS = (30, 472, 94)          # x, top, width of the lobby stair flight
SCROLL_AT = (256, 348)


def call_board(cv, x, y, w, h):
    """Cork board with the pit call: a typed sheet headed CALL, a seating chart, a postcard."""
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT); cv.rect(x, y, w, h, WOOD[3]); cv.hline(x, y, w, WOOD[5])
    cv.rect(x + 2, y + 2, w - 4, h - 4, "#8a6440")
    rng = np.random.default_rng(31)
    for _ in range(40):
        cv.px(x + 3 + int(rng.integers(0, w - 6)), y + 3 + int(rng.integers(0, h - 6)), "#76543a")
    cv.rect(x + 5, y + 4, 34, 32, CARD[2]); cv.hline(x + 5, y + 4, 34, CARD[3])
    text(cv, "CALL", x + 10, y + 5, "#a83c32")
    for k in range(4):
        cv.hline(x + 8, y + 16 + k * 5, 26 - (k % 2) * 6, CARD[0])
    cv.px(x + 21, y + 4, "#c84a3c")
    cv.rect(x + 44, y + 6, 26, 20, "#e8e0c8"); cv.px(x + 56, y + 6, "#3a6ab0")
    for gx in range(x + 47, x + 68, 5):
        for gy in range(y + 10, y + 24, 4):
            cv.rect(gx, gy, 3, 2, "#9a8a76")
    cv.rect(x + 74, y + 10, 18, 14, "#c8784a"); cv.rect(x + 75, y + 11, 16, 6, "#e8b070"); cv.px(x + 82, y + 10, "#e8d050")
    cv.rect(x + 46, y + 29, 30, 7, "#f0e070"); cv.hline(x + 48, y + 32, 24, "#8a7a3a")


def stand_rack(cv, x, base):
    """Spare music stands folded and hung on wall hooks, black against the slats."""
    for k in range(4):
        sx = x + k * 9
        cv.rect(sx - 1, base - 50, 3, 3, IRON[3])
        cv.vline(sx, base - 48, 40, "#141018"); cv.vline(sx + 1, base - 48, 40, "#26222c")
        cv.rect(sx - 4, base - 46, 10, 7, "#141018"); cv.hline(sx - 4, base - 46, 10, "#34303c")
        cv.line(sx, base - 8, sx - 3, base - 2, "#141018"); cv.line(sx + 1, base - 8, sx + 4, base - 2, "#141018")


def kick_plate(cv, y0, y1):
    """The black kick plate along the foot of the pit wall with brass outlet boxes for the stand
    lights every so often."""
    cv.rect(0, y0, W, y1 - y0, "#1c161e"); cv.hline(0, y0, W, "#30282e")
    for ox in range(70, W - 40, 96):
        cv.rect(ox, y0 + 6, 14, 9, OUT); cv.rect(ox + 1, y0 + 7, 12, 7, BRASS[2]); cv.hline(ox + 1, y0 + 7, 12, BRASS[4])
        cv.rect(ox + 3, y0 + 9, 2, 3, "#1a1418"); cv.rect(ox + 9, y0 + 9, 2, 3, "#1a1418")


def back_wall(cv, dawn):
    lights = []
    # the stage above the lip: curtain, pelmet, proscenium slices
    stage_curtain(cv, PROS, W - PROS, 0, LIP, seed=3, glows=[(fx, 34) for fx in FOOTLIGHTS], split=W // 2)
    curtain_valance(cv, PROS, W - PROS, 0, depth=15, swag=58)
    proscenium_side(cv, 0, PROS, 0, LIP + 2, inner="right")
    proscenium_side(cv, W - PROS, W, 0, LIP + 2, inner="left")
    # the pit wall below it
    slat_wall(cv, 0, LIP + 11, W, DADO - LIP - 11, seed=4)
    cv.rect(0, DADO, W, 4, WOOD[3]); cv.hline(0, DADO, W, WOOD[5]); cv.hline(0, DADO + 3, W, WOOD[1])
    kick_plate(cv, DADO + 4, WALL)
    apron_lip(cv, 0, W, LIP, seed=5)
    for fx in FOOTLIGHTS:
        footlight(cv, fx, LIP + 1)
        lights.append((fx, LIP - 4))
    # things on the pit wall
    applause_meter(cv, METER[0], METER[1], cols=METER_COLS, segs=METER_SEGS)
    cv.paste(setlist_paper(["ENCORE", "ENCORE", "ENCORE", "!ENCORE..."], w=64), *SETLIST)
    lights.append(crt_monitor(cv, *MONITOR))
    cable_coil(cv, 176, 74, colour="#c86a2a", r=7)
    cable_coil(cv, 200, 76, colour="#2a2a36", r=6)
    cable_coil(cv, 222, 74, colour="#3a6ab0", r=6)
    concert_poster(cv, 40, 64, w=46, h=48, title="CONCERT")
    lights.append(cue_light_box(cv, *CUE, label="QUIET"))
    call_board(cv, *CALLBOARD)
    lights.append(pit_service_door(cv, DOOR_X, WALL, w=36, h=66, label="STAIR"))
    cv.rect(0, WALL - 2, W, 2, C(SHADOW, 0.4))
    return lights


def lobby_stairs(cv):
    """The carpeted flight up to the lobby at the bottom left: brass-nosed treads, oak cheek walls
    with a handrail, lit from the lobby above."""
    x, top, w = STAIRS
    cv.rect(x - 8, top - 2, w + 16, H - top + 2, OUT)
    steps = [(top + i * 11, 11) for i in range(7)]
    for i, (sy, sh) in enumerate(steps):
        lit = i / len(steps)
        tread = [CARPET_M[2], CARPET_M[3], CARPET_M[4], CARPET_M[4], "#9a3a40", "#9a3a40", "#aa4a44"][i]
        cv.rect(x, sy, w, sh, tread)
        cv.rect(x, sy, w, 3, shade(tread, -0.25))              # the riser in shadow under the nosing
        cv.hline(x, sy + 3, w, BRASS[3] if i > 1 else BRASS[2]); cv.hline(x, sy + 4, w, shade(tread, 0.12))
        cv.rect(x + 8, sy + 5, w - 16, sh - 5, shade(tread, -0.08))
        cv.vline(x + 8, sy + 5, sh - 5, CARPET_M[5] if i > 2 else CARPET_M[1])
        cv.vline(x + w - 9, sy + 5, sh - 5, CARPET_M[5] if i > 2 else CARPET_M[1])
    for sx in (x - 7, x + w + 1):
        cv.rect(sx, top - 1, 6, H - top + 1, WOOD[2]); cv.vline(sx, top - 1, H - top + 1, WOOD[4]); cv.vline(sx + 5, top - 1, H - top + 1, WOOD[0])
        cv.rect(sx + 1, top - 4, 4, 3, BRASS[3]); cv.hline(sx + 1, top - 4, 4, BRASS[4])
        cv.vline(sx + 2, top - 3, H - top + 3, BRASS[3])
    light_pool(cv, x + w // 2, H - 6, 56, 16, strength=0.16)


def floor(cv, dawn):
    pit_floor(cv, 0, WALL, W, H - WALL, seed=9)
    # the pit lift: a steel-edged seam round the platform the orchestra sits on
    lx0, ly0, lx1, ly1 = 150, 158, 832, 414
    for (ax, ay, bx, by_) in [(lx0, ly0, lx1, ly0), (lx0, ly1, lx1, ly1)]:
        cv.hline(ax, ay, bx - ax, "#141014"); cv.hline(ax, ay + 1, bx - ax, C("#8a8490", 0.35))
    for xx in (lx0, lx1):
        cv.vline(xx, ly0, ly1 - ly0 + 2, "#141014"); cv.vline(xx + 1, ly0, ly1 - ly0 + 2, C("#8a8490", 0.35))
    for (cx_, cy_) in [(lx0, ly0), (lx1, ly0), (lx0, ly1), (lx1, ly1)]:
        cv.rect(cx_ - 2, cy_ - 1, 6, 4, "#3a3440"); cv.hline(cx_ - 2, cy_ - 1, 6, "#6a6470")
    # a runner from the lobby stairs to the conductor's rug
    runner_n(cv, 50, 300, 54, STAIRS[1] - 300, pal=CARPET_M, vertical=True)
    runner_n(cv, 50, 300, 322, 40, pal=CARPET_M, vertical=False)
    cv.rect(50, 300, 54, 40, CARPET_M[3]); cv.rect(54, 304, 46, 32, CARPET_M[5]); cv.rect(56, 306, 42, 28, CARPET_M[2])
    # a cello case left lying by the wall, a trombone case
    cv.ellipse(742, 476, 30, 13, OUT); cv.ellipse(766, 478, 22, 10, OUT); cv.rect(770, 480, 26, 6, OUT)
    cv.ellipse(743, 477, 28, 11, "#2a3a5a"); cv.ellipse(767, 479, 20, 8, "#2a3a5a"); cv.rect(771, 481, 25, 4, "#2a3a5a")
    cv.hline(746, 478, 44, "#4a5a7a"); cv.rect(764, 481, 4, 2, BRASS[3])
    cv.rect(842, 380, 40, 9, OUT); cv.rect(843, 381, 38, 7, "#1e1a22"); cv.hline(843, 381, 38, "#3a3442"); cv.rect(860, 383, 4, 2, BRASS[3])
    # a worn rug where the conductor stands
    rx, ry, rw, rh = 372, 298, 236, 84
    cv.rect(rx - 1, ry - 1, rw + 2, rh + 2, C(SHADOW, 0.5))
    cv.rect(rx, ry, rw, rh, CARPET_M[3]); cv.rect(rx + 4, ry + 3, rw - 8, rh - 6, CARPET_M[5])
    cv.rect(rx + 6, ry + 5, rw - 12, rh - 10, CARPET_M[2])
    cv.rect(rx + 14, ry + 10, rw - 28, rh - 20, CARPET_M[3]); cv.rect(rx + 16, ry + 12, rw - 32, rh - 24, CARPET_M[1])
    for k in range(5):
        mx = rx + 40 + k * 39
        cv.poly([(mx, ry + rh // 2 - 8), (mx + 9, ry + rh // 2), (mx, ry + rh // 2 + 8), (mx - 9, ry + rh // 2)], CARPET_M[4])
        cv.poly([(mx, ry + rh // 2 - 4), (mx + 4, ry + rh // 2), (mx, ry + rh // 2 + 4), (mx - 4, ry + rh // 2)], CARPET_M[6])
    for fx in range(rx + 2, rx + rw - 2, 3):
        cv.vline(fx, ry - 3, 2, CARPET_M[5]); cv.vline(fx, ry + rh + 1, 2, CARPET_M[5])
    cv.rect(rx + 150, ry + 40, 40, 30, C(SHADOW, 0.15))           # worn patch where the podium stood
    # spike tape: where chairs and stands go, the podium's corners
    rng = np.random.default_rng(14)
    tapes = ["#e8d050", "#e86aa0", "#4ab0e0", "#f0f0e8", "#7ad070"]
    for (sx, sy) in [(300, 268), (352, 270), (420, 266), (548, 268), (610, 270), (668, 266), (386, 290), (588, 292),
                     (170, 300), (790, 300), (820, 236), (150, 170), (226, 160), (760, 158)]:
        spike_mark(cv, sx, sy, tapes[int(rng.integers(len(tapes)))], kind="LTX"[int(rng.integers(3))])
    # cables: PA to the wall outlets, the riser's stand lights, the score lamp
    gaff_cable(cv, [(256, 272), (262, 220), (262, 160), (262, 142)])
    gaff_cable(cv, [(704, 272), (696, 210), (694, 150), (694, 142)])
    gaff_cable(cv, [(300, 258), (280, 286), (300, 330), (372, 336)], colour="#1e1a24")
    gaff_cable(cv, [(770, 236), (820, 210), (850, 150), (838, 142)], colour="#3a2a2a")
    # parts and a pencil dropped on the floor
    for (lx, ly, t) in [(160, 228, 1), (812, 330, -1), (640, 410, 1), (330, 470, 0), (880, 420, 1)]:
        loose_sheet(cv, lx, ly, tilt=t, seed=lx)
    cv.hline(560, 440, 7, "#e8c040"); cv.px(567, 440, "#2a2026")
    cv.rect(840, 470, 6, 3, "#7a4a1a"); cv.hline(840, 470, 6, "#c8884a")          # a cake of rosin
    lobby_stairs(cv)


def light(cv, dawn):
    # stand lights spill past the riser's front edge
    for lx in range(320, 680, 44):
        light_pool(cv, lx, 266, 30, 8, strength=0.14)
    light_pool(cv, 490, 262, 200, 18, strength=0.08)
    light_pool(cv, LAMP[0], LAMP[1] + 2, 64, 20, strength=0.24)
    light_pool(cv, LAMP[0], LAMP[1] + 2, 30, 9, strength=0.14)
    light_pool(cv, 452, 336, 46, 12, strength=0.14)            # the score lamp
    light_pool(cv, DOOR_X, WALL + 8, 26, 7, strength=0.1)
    # footlights warm the lip and the slats just below it
    for fx in FOOTLIGHTS:
        cv.rect(fx - 8, LIP - 2, 17, 2, C(STAND_GLOW, 0.18))


def margins(cv):
    for (x, w) in [(0, WALK[0]), (WALK[0] + WALK[2], W - WALK[0] - WALK[2])]:
        cv.rect(x, WALL, w, H - WALL, C(SHADOW, 0.3))
    bottom = WALK[1] + WALK[3]
    depth_shade(cv, 0, bottom - 30, W, H - bottom + 30, steps=3, alpha=0.36)


def paint(dawn):
    cv = Canvas(W, H, fill="#171a2b", seed=8)
    lights = back_wall(cv, dawn)
    floor(cv, dawn)
    light(cv, dawn)
    margins(cv)
    return cv, lights


# --- the applause meter's frames --------------------------------------------------------------
def _loud_frames(n=12, seed=2):
    """Applause that never ends: every column pinned up in the amber and red, jittering."""
    rng = np.random.default_rng(seed)
    frames = []
    for f in range(n):
        lv = np.clip(9 + rng.integers(-1, 3, METER_COLS), 8, METER_SEGS)
        frames.append(meter_frame(list(lv), peaks=[METER_SEGS] * METER_COLS, segs=METER_SEGS))
    return frames


# phrase, a rest, the last phrase rising to a final chord, then it ends and is silent
ENVELOPE = [2, 4, 6, 7, 6, 7, 8, 7, 6, 7, 6, 5, 6, 5, 4, 3,
            1, 0, 0, 0, 0, 0,
            3, 5, 6, 7, 6, 7, 8, 9, 8, 9, 9, 8,
            6, 4, 2, 1, 0, 0]


def _music_frames(seed=5):
    """Music with breaths: levels follow ENVELOPE, louder in the low columns, rippling; peak-hold
    marks fall back slowly; in the rest and after the end every column goes dark."""
    rng = np.random.default_rng(seed)
    frames = []
    hist = []
    cols = np.arange(METER_COLS)
    for f, a in enumerate(ENVELOPE):
        mpos = (f * 2.3) % (METER_COLS + 6) - 3                  # the melody moving across the bands
        shape = (0.62 + 0.22 * (1 - cols / (METER_COLS - 1)) + 0.42 * np.exp(-((cols - mpos) / 3.0) ** 2)
                 + 0.12 * np.sin(cols * 0.8 + f * 1.4))
        lv = np.round(a * shape + rng.normal(0, 0.5, METER_COLS) * (a > 0))
        lv = np.clip(lv, 0, METER_SEGS).astype(int)
        hist.append(lv)
        peaks = np.max(np.array(hist[-4:]), axis=0) if a > 0 else lv
        frames.append(meter_frame(list(lv), peaks=list(peaks), segs=METER_SEGS))
    return frames


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    night, lights = paint(False)
    night.save(os.path.join(out, "background.png"))
    res = f"res://assets/art/rooms/{ROOM}/"

    # overlays: the chosen programme, and the endless score spilling over the floor
    setlist_paper(["VERSE", "  REST", "ENDING", "!FINE"], w=64).save(os.path.join(out, "setlist-honest.png"))
    setlist_paper(["MELODY", "  REST", "LAST NOTE", "!FINE"], w=64).save(os.path.join(out, "setlist-instrumental.png"))
    endless_scroll(230, 90, seed=6).save(os.path.join(out, "score-spill.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made[:3]
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(0, pit_riser(390, 84, seed=2))
    save(1, pa_stack(42, 100, seed=1, lit_side="left"))
    save(2, pa_stack(42, 100, seed=2, lit_side="right"))
    score_table(210, 48, ready=True, seed=3)[0].save(os.path.join(out, "prop-3-ready.png"))
    save(3, score_table(210, 48, ready=False, seed=3), {"flag": "music_ready", "flag_texture": res + "prop-3-ready.png"})
    save(4, rest_board(100, 56))
    save(5, ghost_light_m(68, seed=4))

    # meter frames as blink layers: one layer per frame, each lit on its own beat of the pattern
    mx, my = METER[0] + 12, METER[1] + 7
    layers = []
    loud = _loud_frames()
    for i, fr in enumerate(loud):
        name = f"meter-loud-{i:02d}.png"
        fr.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if k == i else "0" for k in range(len(loud))), "rate": 8,
                       "texture": res + name, "x": mx, "y": my, "flag": "music_ready", "when": False})
    music = _music_frames()
    for i, fr in enumerate(music):
        if ENVELOPE[i] == 0:
            continue                        # silent frames: nothing lit, no texture needed
        name = f"meter-music-{i:02d}.png"
        fr.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if k == i else "0" for k in range(len(music))), "rate": 6,
                       "texture": res + name, "x": mx, "y": my, "flag": "music_ready"})

    glow = [[int(x_), int(y_), "ffe6a8", 2] for (x_, y_) in lights[:len(FOOTLIGHTS)]]
    glow.append([int(lights[len(FOOTLIGHTS)][0]), int(lights[len(FOOTLIGHTS)][1]), "c8dcff", 3])     # monitor
    glow.append([int(lights[len(FOOTLIGHTS) + 1][0]), int(lights[len(FOOTLIGHTS) + 1][1]), "ff6040", 3])  # QUIET
    glow.append([int(lights[-1][0]), int(lights[-1][1]), "8ef08a", 2])                                 # STAIR sign
    layers += [
        {"kind": "twinkle", "points": glow, "rate": 1.1, "min": 0.55},
        # motes turning in the ghost light
        {"kind": "particles", "style": "dust", "count": 7, "rect": [LAMP[0] - 30, LAMP[1] - 90, 60, 70], "speed": [3, -3],
         "color": "f6e0b0"},
        # once the music is real, notes drift up out of the pit
        {"kind": "fauna", "flag": "music_ready", "fauna": [
            {"kind": "macky_note", "x": 300, "y": 120, "fly": 7.0, "rate": 3.0},
            {"kind": "macky_note", "x": 620, "y": 96, "fly": 6.0, "rate": 3.0},
            {"kind": "macky_note", "x": 860, "y": 140, "fly": 8.0, "rate": 4.0}]},
    ]
    sx, sy = SETLIST
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": [
            {"texture": res + "setlist-honest.png", "x": sx, "y": sy, "flag": "final_score", "equals": "honest"},
            {"texture": res + "setlist-instrumental.png", "x": sx, "y": sy, "flag": "final_score", "equals": "instrumental"},
            {"texture": res + "score-spill.png", "x": SCROLL_AT[0], "y": SCROLL_AT[1], "flag": "music_ready", "when": False},
        ],
        "fauna": [{"kind": "lamp_moth", "x": LAMP[0] + 4, "y": LAMP[1] - 66, "range": 8, "speed": 1.6, "rate": 8.0}],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
