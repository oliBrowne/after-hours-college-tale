"""Playback room (N07): Norlin's sound archive, where the source reel is heard.

Back wall: the painted ceiling edge over pleated teal acoustic panels between oak battens, an oak
dado below. In the middle a big phosphor monitor shows the recording as a green waveform that
scrolls past a playhead (animated), under an amber lit PLAYBACK sign, on a low equipment
credenza whose VU meters jump with the voice; tall walnut studio monitors stand either side, their
woofers pulsing. Left: a floor-standing archive tape machine with its reels turning, a framed
CLASS OF programme with a blank year; right: an old public-address loudspeaker on a bracket (the
voice that wants every possible graduate seated) and a STAIRS TO QUAD sign.
Floor: oak parquet with a teal listening carpet under the console and benches, cables snaking to
the monitors, green screen-light at the wall foot, warm archive light in from the left; at the
right edge the foot of the return stairs climbs off toward the quad in cool moonlight, roped off
until the source has been heard.
Props: the playback console (source reel threaded on its deck), two listening benches, the tape
shelf, the listening desk with the spare headphones and the save lamp."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from props import OUT, IRON
from lib_norlin import (ceiling_band, oak_wainscot, parquet_floor, carpet, runner_n, depth_shade, standard_lamp, library_bench,
                        wall_speaker, wall_clock_big, directional_sign, OAK, OAK_DARK, PAGE, BRASS, GILT, LIME, CARPET_PLUM, STONE_N)
from lib_norlin2 import (acoustic_wall, lit_sign, waveform_screen, waveform_frame, vu_pair, loudspeaker, woofer_push, reel_face,
                         tape_machine, playback_console, tape_shelf, listening_desk, velvet_rope, ACOUSTIC, PHOSPHOR, CASE,
                         AMBER_LIT, SASH)

ROOM = "N07"
W, H = 800, 480
BASE = 142
WALK = (20, 142, 760, 314)
DADO = 26
SCREEN = (304, 36, 192, 70)          # monitor case x, y, w, h
SPEAKERS = [262, 538]                # studio monitors (centre x)
MACHINE = (40, 42, 96)               # tape machine x, top, width
CREDENZA = (300, 110, 200)           # x, top, width
VU_AT = [(322, 118), (432, 118)]
LAMP = (135, 389)
CARPET_RECT = (44, 166, 712, 226)
STAIR = (764, 386, 448)              # stair foot: first riser x, tread band top and bottom y
ROPE = (744, 376)
TEAL_RUG = ["#0c1416", "#122024", "#1a2e34", "#223c42", "#2c4c52", "#c0884a", "#e0b26a"]


def programme(bg, x, y):
    """A framed ceremony programme: mortarboard, CLASS OF and a blank year, ruled names."""
    w, h = 56, 52
    bg.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    bg.rect(x, y, w, h, OAK[3]); bg.hline(x, y, w, OAK[5])
    bg.rect(x + 3, y + 3, w - 6, h - 6, PAGE[3]); bg.hline(x + 3, y + 3, w - 6, "#fff8e6")
    cx = x + w // 2
    bg.poly([(cx - 9, y + 10), (cx, y + 6), (cx + 9, y + 10), (cx, y + 14)], "#2a2830")
    bg.rect(cx - 5, y + 12, 11, 4, "#2a2830"); bg.vline(cx + 8, y + 10, 6, GILT); bg.px(cx + 8, y + 16, GILT)
    text(bg, "CLASS OF", cx - text_width("CLASS OF") // 2, y + 17, "#3a2a40")
    bg.hline(cx - 10, y + 30, 20, "#8a7a68")
    for k in range(4):
        bg.hline(x + 9, y + 35 + k * 3, w - 18 - (k % 2) * 8, PAGE[1])


def credenza(bg):
    """The low equipment cabinet under the monitor: oak top, grey amplifier faces with knobs and
    pilot lights, two VU pairs (animated), a patch bay."""
    x, top, w = CREDENZA
    bg.rect(x - 1, top - 1, w + 2, BASE - top + 1, OUT)
    bg.rect(x, top, w, BASE - top, OAK[2]); bg.rect(x - 2, top - 1, w + 4, 4, OAK[4]); bg.hline(x - 2, top - 1, w + 4, OAK[5])
    for k, (fx, fw) in enumerate(((x + 4, 64), (x + 72, 56), (x + 132, 64))):
        bg.rect(fx, top + 5, fw, 22, OUT); bg.rect(fx + 1, top + 6, fw - 2, 20, CASE[3]); bg.hline(fx + 1, top + 6, fw - 2, CASE[5])
        for j in range(fw // 10):
            kx = fx + 6 + j * 10
            bg.rect(kx - 1, top + 19, 5, 5, OUT); bg.rect(kx, top + 20, 3, 3, CASE[4]); bg.px(kx, top + 20, CASE[5])
        bg.rect(fx + fw - 6, top + 8, 3, 2, "#7ad08a" if k != 1 else "#e9a84a")
    # patch bay in the middle unit: rows of jacks with a few cords
    px_ = x + 78
    for j in range(8):
        for r in range(2):
            bg.px(px_ + j * 5, top + 9 + r * 4, OUT); bg.px(px_ + 1 + j * 5, top + 9 + r * 4, CASE[1])
    for (a, b, c) in ((px_ + 1, px_ + 21, "#c84a3c"), (px_ + 11, px_ + 36, "#e9a84a"), (px_ + 6, px_ + 26, "#5a7ac8")):
        for k in range(b - a + 1):
            t = k / max(1, b - a)
            bg.px(a + k, top + 10 + int(round(5 * np.sin(t * np.pi))), c)
    for (vx, vy) in VU_AT:
        bg.paste(vu_pair(44, 16, (0.35, 0.5)), vx, vy)
    bg.rect(x, BASE - 4, w, 4, OAK_DARK[3])


def back_wall(bg):
    acoustic_wall(bg, 0, 12, W, BASE - 12 - DADO, seed=3)
    oak_wainscot(bg, 0, BASE - DADO, W, DADO, seed=4)
    ceiling_band(bg, 0, 0, W, 12)
    # signs to the two exits
    directional_sign(bg, 26, 20, "ARCHIVE", arrow="left")
    sw = text_width("STAIRS TO QUAD >") + 10
    directional_sign(bg, W - 24 - sw, 20, "STAIRS TO QUAD", arrow="right")
    # the archive tape machine and the ceremony programme
    mx, mtop, mw = MACHINE
    tape_machine(bg, mx, mtop, mw, BASE, seed=2)
    programme(bg, 162, 46)
    # the monitor, its sign and the credenza under it, the studio monitors either side
    sx, sy, sw_, sh = SCREEN
    credenza(bg)
    for i, a in enumerate((0.05, 0.08, 0.1)):
        bg.rect(sx - 10 + i * 4, sy - 6 + i * 3, sw_ + 20 - i * 8, sh + 12 - i * 6, C("#7ad08a", a))
    waveform_screen(bg, sx, sy, sw_, sh)
    lit_sign(bg, sx + sw_ // 2, 17, "PLAYBACK")
    for cx in SPEAKERS:
        loudspeaker(bg, cx, 48, BASE, w=36)
    # the public-address loudspeaker that keeps asking for more chairs
    wall_speaker(bg, 612, 44, w=20, h=24)
    bg.line(622, 38, 622, 30, IRON[2]); bg.hline(612, 30, 10, IRON[1])
    # the clock that has said four minutes to midnight all night
    wall_clock_big(bg, 706, 74, r=13, hour=11, minute=56)
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))


def stair_foot(bg):
    """The foot of the return stairs at the right edge: oak treads climbing off toward the quad,
    the stringer's stepped face, a brass handrail on posts, moonlight from the landing above."""
    x0, y0, y1 = STAIR
    tread, rise = 8, 6
    n = (W - x0) // tread + 1
    for i in range(n):
        x = x0 + i * tread
        top, bot = y0 - i * rise, y1 - i * rise
        bg.rect(x, top, tread, bot - top, OAK[4]); bg.hline(x, top, tread, OAK[5])
        bg.vline(x, top, bot - top, OAK[2])
        bg.rect(x, bot, tread, rise * i + 4, OAK[2]); bg.hline(x, bot, tread, OAK[3])
        bg.rect(x + 1, top + 4, tread - 2, bot - top - 8, CARPET_PLUM[3])
        bg.hline(x + 1, top + 4, tread - 2, CARPET_PLUM[4])
    bg.rect(x0, y1 + 4, W - x0, H - y1 - 4, C("#0d0b16", 0.5))
    # handrail on the open (front) side
    for i in range(0, n, 2):
        px_ = x0 + 3 + i * tread
        bg.rect(px_, y1 - i * rise - 16, 2, 16, BRASS[2]); bg.vline(px_, y1 - i * rise - 16, 16, BRASS[4])
    bg.line(x0 + 2, y1 - 18, W, y1 - 18 - (W - x0 - 2) * rise // tread, OUT)
    bg.line(x0 + 2, y1 - 17, W, y1 - 17 - (W - x0 - 2) * rise // tread, BRASS[3])
    for i, a in enumerate((0.1, 0.07, 0.04)):
        bg.rect(W - 26 - i * 12, y0 - 40 - i * 8, 26 + i * 12, (y1 - y0) + 60 + i * 16, C("#a8c8e0", a))


def floor(bg):
    parquet_floor(bg, 0, BASE, W, H - BASE, seed=7)
    rx, ry, rw, rh = CARPET_RECT
    carpet(bg, rx, ry, rw, rh, pal=TEAL_RUG, seed=3, motif=16)
    # a plum runner from the archive door (left) along the front to the stairs (right)
    runner_n(bg, 0, 402, STAIR[0], 26, pal=CARPET_PLUM, vertical=False)
    for i, a in enumerate((0.1, 0.07, 0.04)):
        bg.rect(0, 384 - i * 8, 20 + i * 12, 62 + i * 16, C("#f6cf7a", a))
    stair_foot(bg)
    # cables from the console to the monitors and the credenza
    for (ax, ay, bx, by) in ((362, 300, SPEAKERS[0], BASE + 2), (438, 300, SPEAKERS[1], BASE + 2), (400, 296, 400, BASE + 2)):
        pts = [(ax + (bx - ax) * t + 10 * np.sin(t * np.pi * 2), ay + (by - ay) * t) for t in np.linspace(0, 1, 14)]
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            bg.line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)), "#16141c")
            bg.line(int(round(x0)), int(round(y0)) - 1, int(round(x1)), int(round(y1)) - 1, C("#4a4652", 0.6))
    # screen light at the wall foot, lamplight, a speaker's glow
    light_pool(bg, 400, BASE + 10, 120, 16, color="#7ad08a", strength=0.12)
    light_pool(bg, LAMP[0], LAMP[1] + 3, 46, 13, strength=0.26)
    light_pool(bg, 400, 330, 110, 26, strength=0.1)
    depth_shade(bg, 0, 420, W, 60, steps=3, alpha=0.18)
    # margins outside the walkable floor (the stairs stay lit)
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.38))
    bg.rect(WALK[0] + WALK[2], BASE, STAIR[0] - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.3))
    bg.rect(0, WALK[1] + WALK[3], STAIR[0], H - WALK[1] - WALK[3], C("#0d0b16", 0.42))


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

    save(0, playback_console(180, 48, seed=5))
    save(1, library_bench(120, 32, seed=1, cushion="#4a2a3a"))
    save(2, library_bench(120, 32, seed=2, cushion="#4a2a3a"))
    save(3, tape_shelf(100, 94, seed=6))
    save(4, listening_desk(100, 36, seed=7))
    save(5, standard_lamp(68))

    # the stairs to the quad stay roped off until the source has been heard
    overlays = []
    for open_, name in ((False, "rope-closed.png"), (True, "rope-open.png")):
        velvet_rope(open_).save(os.path.join(out, name))
        overlays.append({"texture": res + name, "x": ROPE[0], "y": ROPE[1], "flag": "playback_heard", "when": open_})

    layers = []
    # the waveform scrolling past the playhead: twelve frames in turn
    sx, sy, sw_, sh = SCREEN
    gx, gy, gw, gh = sx + 6, sy + 5, sw_ - 12, sh - 14
    n = 12
    for k in range(n):
        fr = waveform_frame(gw - 2, gh - 2, k, n, seed=11)
        name = f"wave-{k}.png"
        fr.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(n)), "rate": 10.0,
                       "texture": res + name, "x": gx + 1, "y": gy + 1})
    # VU needles jumping with the voice
    angles = [(0.3, 0.42), (0.62, 0.55), (0.48, 0.7), (0.78, 0.6), (0.4, 0.35), (0.66, 0.8)]
    for k, a in enumerate(angles):
        name = f"vu-{k}.png"
        vu_pair(44, 16, a).save(os.path.join(out, name))
        for j, (vx, vy) in enumerate(VU_AT):
            pat = ["0"] * len(angles)
            pat[(k + j * 2) % len(angles)] = "1"
            layers.append({"kind": "blink", "pattern": "".join(pat), "rate": 6.0, "texture": res + name, "x": vx, "y": vy})
    # the tape machine's reels turning (three-spoke reels: three frames make a full turn)
    mx, mtop, mw = MACHINE
    r = 15
    reels = [(mx + 3 + r + 4, mtop + 3 + r + 4, 0.75), (mx + mw - 3 - r - 5, mtop + 3 + r + 4, 0.45)]
    for j, (rx, ry, tape) in enumerate(reels):
        for k in range(3):
            name = f"reel-{j}-{k}.png"
            reel_face(r, 0.3 + k * 2 * np.pi / 9, tape=tape).save(os.path.join(out, name))
            layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(3)), "rate": 5.0,
                           "texture": res + name, "x": rx - r - 1, "y": ry - r - 1})
    # the monitors' woofers pushing with the syllables
    woofers = []
    for cx in SPEAKERS:
        w_ = 36
        wr = (w_ - 10) // 2
        wy = BASE - 12 - wr - 2
        woofers.append((cx, wy, wr))
    push = woofer_push(woofers[0][2])
    push.save(os.path.join(out, "woofer-push.png"))
    for (cx, wy, wr) in woofers:
        layers.append({"kind": "blink", "pattern": "1010001011000100", "rate": 8.0, "texture": res + "woofer-push.png",
                       "x": cx - wr - 1, "y": wy - wr - 1})
    layers += [
        {"kind": "twinkle", "points": [[LAMP[0], LAMP[1] - 63, "fff0c4", 2], [sx + 10, sy + sh - 5, "7ad08a", 0],
                                       [CREDENZA[0] + 64, CREDENZA[1] + 9, "7ad08a", 0], [CREDENZA[0] + 190, CREDENZA[1] + 9, "7ad08a", 0]],
         "rate": 1.2, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 14, "rect": [300, 40, 200, 90], "speed": [1, 2], "color": "c8f0d0"},
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
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
