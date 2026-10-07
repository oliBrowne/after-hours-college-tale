"""Pearl Street startup, open office (P01): the second floor of an 1890s brick block on the
pedestrian mall, rented by a fictional startup, DISRUPTR. Back wall, left to right: the old fir
door to the stairwell (down to Pearl Street), three tall arched windows onto the mall at night
(the opposite block's cornices and lit windows, the trees wrapped in white lights) with cast-iron
radiators under them, the DISRUPTR neon over a whiteboard wall, a ceiling projector throwing Kyle's
pitch deck onto a pull-down screen, a framed MOVE FAST poster, the doorway into the break room and
a rail of identical fleece vests. A spiral duct runs under the joists; Edison pendants hang between
the windows. Heart-pine floor: four standing desks on the left (yours, a treadmill desk, a
three-monitor desk, one cleared out into a box), a rolling whiteboard, a ping-pong table down
front, a cognac sofa facing the screen on a kilim, the sales gong. The floor in front of the screen
is kept clear for Kyle and his scooter: a tape X, his charger cable to a power strip, tyre scuffs."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from lib_eng import outlet, floor_cord
from lib_umc import soft_ellipse, halo
from p01_lib import (loft_ceiling, brick_wall_p, ghost_paint, baseboard, pearl_view, arched_window, radiator,
                     pendant, neon_text, neon_bolt, whiteboard, slide, projection_screen, ceiling_projector,
                     stair_door, doorway_glimpse, vest_hooks, framed_poster, thermostat, pine_floor, kilim_rug,
                     tyre_marks, tape_x, power_strip, standing_desk, rolling_whiteboard, ping_pong_p, sofa_back,
                     gong_stand, tall_plant, road_bike_stand, swag_boxes, hot_desk_bench, micro_text, micro_width, NEON_PINK, NEON_CYAN, SHADOW, BRICK)

ROOM = "P01"
W, H = 960, 540
BASE = 176
STAIRS_X, BREAK_X = 62, 880
WINDOWS = (160, 252, 344)
WIN_W, WIN_TOP, WIN_H = 52, 42, 98
NEON_X, NEON_Y = 432, 24
BOARD = (404, 66, 152, 74)
SCREEN = (604, 28, 192, 110)
KYLE = (700, 262)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=41)

    # --- back wall: brick, the building's ghost sign, ceiling joists and the duct
    brick_wall_p(bg, 0, 16, W, BASE - 16, seed=3)
    ghost_paint(bg, 812, 24, "DRY GOODS", alpha=0.26)
    ghost_paint(bg, 836, 36, "1891", alpha=0.2)
    loft_ceiling(bg, 0, W, h=16, seed=4)
    for y0, a in [(16, 0.3), (17, 0.18), (18, 0.08)]:
        bg.hline(0, y0, W, C(SHADOW, a))

    # --- windows onto Pearl Street: one panorama shared by all three so the far block runs on
    view, lights = pearl_view(WINDOWS[-1] - WINDOWS[0] + WIN_W + 20, WIN_H + 12, seed=7)
    vx0 = WINDOWS[0] - WIN_W // 2 - 10
    win_lights = []
    for k, cx in enumerate(WINDOWS):
        sill = arched_window(bg, cx, WIN_TOP, WIN_W, WIN_H, view, cx - WIN_W // 2 - vx0, seed=k)
        radiator(bg, cx, BASE - 6, w=40, h=22)
        gx0, gx1 = cx - WIN_W // 2 + 4, cx + WIN_W // 2 - 4
        for (lx, ly) in lights:
            sx, sy = vx0 + lx, WIN_TOP - 7 + ly
            if gx0 + 1 < sx < gx1 - 1 and WIN_TOP < sy < WIN_TOP + WIN_H - 5 and abs(sx - cx) > 1 and abs(sy - (WIN_TOP + WIN_H // 2 - 4)) > 2:
                win_lights.append((sx, sy))
        # cool street light falling in on the sill and the floor below
        bg.rect(cx - WIN_W // 2 + 2, sill - 2, WIN_W - 4, 1, C("#c8d0f0", 0.15))
    # the vests, a poster, a thermostat, switches
    vest_hooks(bg, 910, 70, n=3)
    framed_poster(bg, 812, 64, 34, 46, ["MOVE", "FAST &", "BREAK", "THINGS", "(NOT", "THE TV)"])
    thermostat(bg, 383, 104)
    bg.rect(112, 110, 5, 8, "#e6e2d6"); bg.px(114, 112, "#8a8a98")                  # light switch
    outlet(bg, 768, BASE - 16); outlet(bg, 470, BASE - 16); outlet(bg, 210, BASE - 16)

    # --- the neon logo over the whiteboard wall
    neon_bolt(bg, NEON_X - 22, NEON_Y - 2, NEON_CYAN)
    neon_text(bg, "DISRUPTR", NEON_X, NEON_Y, NEON_PINK, scale=2)
    bg.line(NEON_X + 100, NEON_Y + 22, NEON_X + 106, BOARD[1] - 4, "#14121c")       # its transformer lead
    bg.rect(NEON_X + 102, BOARD[1] - 6, 8, 4, "#2a2a34")
    whiteboard(bg, *BOARD, seed=5)

    # --- projector and the pitch deck (slide 1 painted; the rest cycle as layers)
    sx, sy = projection_screen(bg, *SCREEN)
    bg.paste(slide("title"), sx, sy)
    ceiling_projector(bg, 700, (SCREEN[0] + 6, SCREEN[1], SCREEN[0] + SCREEN[2] - 6, SCREEN[1] + SCREEN[3]))
    halo(bg, 700, 84, 110, "#c8d8ff", 0.03)

    # pendants between the windows and over the ping-pong end
    bulbs = [pendant(bg, 206, 30), pendant(bg, 298, 30), pendant(bg, 580, 40)]
    baseboard(bg, 0, BASE, W)
    stair_door(bg, STAIRS_X, BASE)
    doorway_glimpse(bg, BREAK_X, BASE)

    # --- floor
    pine_floor(bg, 0, BASE, W, H - BASE, seed=9)
    bg.rect(0, BASE, W, 2, C(SHADOW, 0.45)); bg.hline(0, BASE + 2, W, C(SHADOW, 0.2))
    # light: cool window light, warm pendants, the screen's spill, the break room's warm doorway
    for cx in WINDOWS:
        bg.poly([(cx - 22, BASE), (cx + 22, BASE), (cx + 40, BASE + 46), (cx - 4, BASE + 46)], C("#b8c4f0", 0.06))
    for cx, cy, rx, ry, c, a in [(206, 300, 120, 54, "#f6cf7a", 0.22), (520, 430, 120, 46, "#f6cf7a", 0.2),
                                 (700, 236, 120, 44, "#d8e4ff", 0.16), (BREAK_X, 204, 60, 26, "#f6c27a", 0.26),
                                 (298, 220, 70, 30, "#f6cf7a", 0.14)]:
        light_pool(bg, cx, cy, rx, ry, color=c, strength=a)
    kilim_rug(bg, 594, 372, 212, 76, seed=3)
    # Kyle's spot: a tape X, his charger running to a power strip, scooter scuffs all over
    tape_x(bg, *KYLE)
    power_strip(bg, 744, 194)
    bg.line(770, BASE - 9, 770, 194, "#14121c"); bg.line(770, 194, 762, 196, "#14121c")
    floor_cord(bg, [(746, 197), (730, 206), (718, 222), (712, 240), (706, 254)], colour="#1a1a22", hi="#3a3a48")
    # a skidded donut round the X and two short skids where he braked
    ring = [(int(KYLE[0] + np.cos(a) * 46), int(KYLE[1] + 4 + np.sin(a) * 16)) for a in np.linspace(0.3, 2 * np.pi - 0.2, 40)]
    tyre_marks(bg, ring, seed=1)
    tyre_marks(bg, [(p[0] + 3, p[1] + 2) for p in ring[4:30]], seed=2)
    # small flat things: sticky notes, a paper aeroplane, a stray ping-pong ball, a lanyard
    for (x, y, c) in [(330, 300, "#f2d84a"), (348, 306, "#f28ab0"), (92, 420, "#8ad8f0")]:
        bg.rect(x + 1, y + 1, 6, 5, C(SHADOW, 0.3)); bg.rect(x, y, 6, 5, c)
    bg.poly([(612, 492), (628, 488), (618, 496)], "#f2f2ea"); bg.line(612, 492, 622, 491, "#c8c8d0")
    bg.ellipse(452, 512, 3, 3, "#f6f2e6")
    bg.line(870, 470, 884, 476, "#e84a98"); bg.rect(884, 474, 5, 6, "#f2ecdc")
    # margins
    for x0, w in [(0, 14), (W - 14, 14)]:
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

    save(2, standing_desk("intern", seed=1))
    save(3, standing_desk("treadmill", seed=2))
    save(4, standing_desk("triple", seed=3))
    save(5, standing_desk("cleared", seed=4))
    save(6, rolling_whiteboard(seed=5))
    save(7, ping_pong_p(120, 46, seed=6))
    save(8, sofa_back(124, 38, seed=7))
    save(9, gong_stand(40, 58, seed=8))
    save(10, tall_plant(34, 64, "fig", seed=9))
    save(11, tall_plant(34, 52, "snake", seed=10))
    save(16, hot_desk_bench(150, 42, seed=11))
    save(17, road_bike_stand(60, 42, seed=12))
    save(18, swag_boxes(40, 40, seed=13))

    # --- layers: the pitch deck advancing, the R in the neon buzzing, lights in the mall's trees
    layers = []
    kinds = ["traction", "tam", "hiring"]
    for k, kind in enumerate(kinds):
        name = f"slide-{kind}.png"
        slide(kind).save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if j == k + 1 else "0" for j in range(4)), "rate": 0.25,
                       "texture": res + name, "x": sx, "y": sy})
    r_x = NEON_X + 7 * 12 + 2
    layers += [
        {"kind": "blink", "pattern": "00000000000000101100000000000000000000000000001000", "rate": 10.0,
         "rects": [[r_x - 1, NEON_Y - 1, 13, 18, "3a1e24", 0.75]]},
        {"kind": "twinkle", "points": [[x, y, "fff4d0", 1] for (x, y) in win_lights], "rate": 1.4, "min": 0.3},
        {"kind": "twinkle", "points": [[bx, by, "f6cf7a", 1] for (bx, by) in bulbs], "rate": 0.7, "min": 0.75},
        {"kind": "particles", "style": "dust", "count": 12, "rect": [630, 22, 140, 110], "speed": [0, 3], "color": "e8f0ff"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0, 1, 12, 13, 14, 15],
        "fauna": [],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
