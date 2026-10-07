"""Repair landing (U05): the back-of-house stair landing under the atrium. Painted block walls with
a teal dado, a red sprinkler main and conduit along the ceiling line, caged bulbs, Mags's punch clock
and key box, Cal's pegboard. The open stairwell in the middle drops toward the lanes (their neon
glows up from below), the service doorway at the back right continues down to the Connection, and
the flight at the bottom left climbs back to the atrium's warm light."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import light_pool
from props import OUT, IRON, AMBER
from interior import PLASTER
from lib_umc import (BLOCK, DADO, CONCRETE, SAFETY, EXIT_GREEN, PAPER, KRAFT, BRASS, SHADOW, STONE_IN,
                     block_wall, conduit_run, conduit_drop, junction_box, big_pipe, punch_clock, key_cabinet,
                     pegboard, extinguisher, concrete_floor, hazard_band, stairwell_void, service_doorway,
                     stair_up_flight, caged_bulb, cable, halo, enamel_sign, soft_ellipse,
                     well_rail, repair_bench, access_panel, checklist_cart, work_lamp)

ROOM = "U05"
W, H = 640, 360
WALL_BASE = 128          # walk_bounds top
DADO_TOP = 98
FLOOR_END = 336          # below this the front wall-top band
UP_STAIRS = (42, 94, 249)        # placement 0: x span, top of the flight (it climbs toward the viewer)
DOWN_DOOR = (570, 171)           # placement 1: doorway centre x and the floor line of its first tread
WELL = (144, 158, 384, 216)      # placement 2: the open well (collision box of the rail)
PANEL = (429, 209)               # placement 4
BENCH = (470, 228)               # placement 3
LAMP = (542, 287)                # placement 6
BULBS = [(92, 26), (300, 26), (478, 26)]
KEEPSAKE = (580, 264)            # pickup spot: keep clear


def paint_wall(bg):
    block_wall(bg, 0, 6, W, WALL_BASE - 6, dado_top=DADO_TOP, seed=2)
    # ceiling slab edge
    bg.rect(0, 0, W, 6, "#24202a"); bg.hline(0, 5, W, "#3a3440"); bg.hline(0, 6, W, C(SHADOW, 0.5))
    big_pipe(bg, 0, W, 8, colour="#8a3a32")
    conduit_run(bg, 0, W, 17)
    conduit_run(bg, 0, W, 22, colour=["#3a3a48", "#5a6a78", "#8a9aa8"])
    # high wired-glass windows at ground level outside: a lamp-lit night strip
    for wx in (176, 316):
        bg.rect(wx - 2, 34, 44, 22, OUT); bg.rect(wx - 1, 35, 42, 20, "#4a5a68")
        bg.dither_v(wx + 1, 37, 38, 16, "#1a2038", "#3a3a5a", steps=3)
        for k in range(0, 38, 3):
            bg.vline(wx + 1 + k, 49 - (k * 7 % 5), 4 + (k * 7 % 5), "#22302b")
        bg.rect(wx + 1, 52, 38, 1, "#2a3a2e")
        for gx in range(wx + 1, wx + 39, 5):
            for gy in range(37, 53, 5):
                bg.px(gx, gy, C("#8a9ab0", 0.5))
        bg.vline(wx + 20, 37, 16, "#4a5a68")
        bg.rect(wx - 3, 56, 46, 2, BLOCK[5])
    # stencilled level marker and arrow between the windows
    for (s, x, y, c) in [("B1", 262, 36, SAFETY[2]), ("REPAIR", 252, 50, PAPER[2])]:
        text(bg, s, x, y, c)
    bg.rect(268, 66, 4, 10, SAFETY[2]); bg.poly([(263, 75), (276, 75), (269, 82)], SAFETY[2])
    # Mags's corner: punch clock and card rack, the spare-key box, her jacket on a hook
    punch_clock(bg, 26, 44)
    key_cabinet(bg, 74, 52)
    bg.rect(120, 44, 3, 3, IRON[3])
    bg.poly([(116, 47), (126, 47), (130, 78), (112, 78)], "#3e5a5e"); bg.poly([(116, 47), (121, 47), (119, 78), (112, 78)], "#2c4048")
    bg.line(121, 47, 121, 77, "#24383a"); bg.rect(113, 74, 17, 4, "#2c4048"); bg.px(124, 60, "#e8b45c")
    # notices
    for (nx, ny, c, lines) in [(144, 64, PAPER[2], 4), (158, 70, "#f2d27a", 3)]:
        bg.rect(nx + 1, ny + 1, 12, 15, C(SHADOW, 0.5)); bg.rect(nx, ny, 12, 15, c)
        for k in range(lines):
            bg.hline(nx + 2, ny + 3 + k * 3, 8 - (k % 2) * 2, "#6a5a50")
        bg.px(nx + 6, ny + 1, "#c84a3c")
    # Cal's pegboard behind the bench and a schematic pinned up
    pegboard(bg, 448, 38, 76, 40, seed=3)
    bg.rect(530, 44, 22, 28, "#2a4a7a"); bg.rect(531, 45, 20, 26, "#3a62a0")
    for k in range(5):
        bg.hline(533, 48 + k * 5, 16, C("#c8d8f0", 0.7))
    bg.vline(540, 47, 22, C("#c8d8f0", 0.7)); bg.rect(538, 56, 5, 5, C("#c8d8f0", 0.7))
    # conduit drops: one feeds the access panel through a floor channel, one the doorway light
    conduit_drop(bg, 424, 25, WALL_BASE)
    junction_box(bg, 420, 84, 11, 10, label=SAFETY[2])
    conduit_drop(bg, 140, 25, 50)
    junction_box(bg, 136, 48, 10, 9)
    # an EXIT sign above the service doorway (the doorway is painted after the floor)
    cx, fy = DOWN_DOOR
    bg.rect(cx - 12, 36, 24, 10, OUT); bg.rect(cx - 11, 37, 22, 8, EXIT_GREEN[1])
    text(bg, "EXIT", cx - 12, 36, EXIT_GREEN[3])
    halo(bg, cx, 41, 16, colour="#3cba7a", strength=0.06)
    extinguisher(bg, 614, 110)
    # caged bulbs on drops from the conduit
    for (bx, by) in BULBS:
        bg.vline(bx, 25, by - 25 + 2, "#3a3a48")
        caged_bulb(bg, bx, by + 4)


def paint_floor(bg):
    concrete_floor(bg, 0, WALL_BASE, W, FLOOR_END - WALL_BASE, seed=4)
    bg.rect(0, WALL_BASE, W, 2, C(SHADOW, 0.5))
    # the open well and a painted safety margin round it
    x0, y0, x1, y1 = WELL
    stairwell_void(bg, x0 + 2, y0, x1 - 2, y1 - 1, seed=1)
    for (ax, ay, aw, ah) in [(x0 - 6, y0 - 5, x1 - x0 + 12, 2), (x0 - 6, y1 + 3, x1 - x0 + 12, 2),
                             (x0 - 6, y0 - 5, 2, y1 - y0 + 10), (x1 + 4, y0 - 5, 2, y1 - y0 + 10)]:
        bg.rect(ax, ay, aw, ah, C(SAFETY[2], 0.75))
    # cable channel from the panel back to the wall (flat, yellow-and-black cover)
    px, py = PANEL
    bg.rect(px - 6, WALL_BASE, 8, py - WALL_BASE - 4, "#1a1820")
    hazard_band(bg, px - 5, WALL_BASE + 1, 6, py - WALL_BASE - 6, vertical=True)
    # light pools: bulbs at the wall, the lamp, warm spill from the atrium flight
    for (bx, by) in BULBS:
        light_pool(bg, bx, WALL_BASE + 16, 54, 12, strength=0.22)
    light_pool(bg, LAMP[0], LAMP[1], 60, 16, strength=0.3)
    # the atrium's warm light spilling down the flight at the bottom left
    light_pool(bg, (UP_STAIRS[0] + UP_STAIRS[1]) // 2 + 10, FLOOR_END - 30, 70, 26, color="#f6c27a", strength=0.22)
    light_pool(bg, DOWN_DOOR[0], DOWN_DOOR[1] + 6, 40, 8, color="#ff9ac0", strength=0.12)
    # oil drip under the bench, wire clippings and a dropped washer
    bx, by = BENCH
    soft_ellipse(bg, bx + 10, by + 4, 12, 3, CONCRETE[0], 0.4)
    rng = np.random.default_rng(7)
    for _ in range(14):
        cx, cy = bx + int(rng.integers(-40, 40)), by + int(rng.integers(2, 14))
        bg.px(cx, cy, ["#c84a3c", "#c0c4cc", "#e8b45c"][int(rng.integers(3))])
    # aisle lines from the atrium stairs to the doorway, the cart's parking bay, a drain,
    # and a rubber mat where Cal stands at the bench
    for xx in range(112, 600, 1):
        if (xx // 6) % 7 != 0:
            bg.px(xx, 300, C(SAFETY[2], 0.55)); bg.px(xx, 301, C(SAFETY[1], 0.4))
    for (ax, ay, aw, ah) in [(66, 178, 68, 1), (66, 240, 68, 1), (66, 178, 1, 62), (133, 178, 1, 62)]:
        for k in range(max(aw, ah)):
            if (k // 4) % 2 == 0:
                bg.px(ax + (k if aw > 1 else 0), ay + (k if ah > 1 else 0), C(SAFETY[2], 0.6))
    text(bg, "CART", 88, 242, C(SAFETY[2], 0.5))
    bg.ellipse(292, 262, 16, 8, CONCRETE[1]); bg.ellipse(293, 263, 14, 6, "#2a262c")
    for gx in range(295, 306, 3):
        bg.vline(gx, 263, 6, CONCRETE[4])
    mx0, my0, mw, mh = 424, 238, 96, 22
    bg.rect(mx0, my0, mw, mh, "#2a3430"); bg.rect(mx0 + 1, my0 + 1, mw - 2, mh - 2, "#3a4842")
    for gx in range(mx0 + 3, mx0 + mw - 2, 3):
        bg.vline(gx, my0 + 2, mh - 4, "#33403a")
    bg.hline(mx0 + 1, my0 + 1, mw - 2, "#4e5e56"); bg.hline(mx0, my0 + mh - 1, mw, "#1e2420")
    # floor stencils: DOWN with an arrow pointing at the doorway (down is a direction)
    cx, fy = DOWN_DOOR
    text(bg, "DOWN", cx - 12, fy + 14, C(SAFETY[2], 0.7))
    bg.rect(cx - 1, fy + 4, 3, 8, C(SAFETY[2], 0.7)); bg.poly([(cx - 5, fy + 5), (cx + 6, fy + 5), (cx, fy - 1)], C(SAFETY[2], 0.7))
    # the service doorway down to the lanes: its first treads start on the landing floor
    service_doorway(bg, cx, WALL_BASE, fy, w=60, h=74, seed=1)
    # the work lamp's cord to the wall by the doorway
    cable(bg, [(LAMP[0] + 3, LAMP[1] - 1), (566, 296), (604, 300), (621, 296)], "#16141f", hi="#6c6a88")
    bg.rect(619, 292, 3, 6, IRON[3])


def paint_frame(bg):
    """Wall-tops of the side and front walls, the stair up to the atrium cut through the front."""
    def wall_top(x, y, w, h, edge):
        bg.rect(x, y, w, h, "#1e1a24")
        rng = np.random.default_rng(x * 7 + y)
        for _ in range(w * h // 26):
            bg.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), "#2a2430")
        if edge == "left":
            bg.vline(x, y, h, BLOCK[4]); bg.vline(x + 1, y, h, BLOCK[2])
        elif edge == "right":
            bg.vline(x + w - 1, y, h, BLOCK[4]); bg.vline(x + w - 2, y, h, BLOCK[2])
        else:
            bg.hline(x, y, w, BLOCK[4]); bg.hline(x, y + 1, w, BLOCK[2])
    x0, x1, top = UP_STAIRS
    stair_up_flight(bg, x0, top, x1, H, H)
    wall_top(0, FLOOR_END, x0 - 4, H - FLOOR_END, "top")
    wall_top(x1 + 4, FLOOR_END, W - x1 - 4, H - FLOOR_END, "top")
    wall_top(0, WALL_BASE - 1, 18, FLOOR_END - WALL_BASE + 1, "right")
    wall_top(622, WALL_BASE - 1, 18, FLOOR_END - WALL_BASE + 1, "left")
    bg.rect(18, FLOOR_END - 8, x0 - 22, 8, C(SHADOW, 0.25)); bg.rect(x1 + 4, FLOOR_END - 8, 622 - x1 - 4, 8, C(SHADOW, 0.25))


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=5)
    paint_wall(bg)
    paint_floor(bg)
    paint_frame(bg)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made[:3]
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(2, well_rail(240, WELL[3] - WELL[1], 20))
    save(3, repair_bench(86, 46))
    panel = access_panel(43, 64)
    save(4, panel)
    save(5, checklist_cart(49, 40))
    save(6, work_lamp(59))

    (lx, ly), (ex, ey) = panel[3], panel[4]
    fx, fy = PANEL[0] + lx, PANEL[1] + ly
    res = f"res://assets/art/rooms/{ROOM}/"
    cx, _ = DOWN_DOOR
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0, 1],
        "fauna": [
            {"kind": "umc_moth", "x": LAMP[0] - 2, "y": LAMP[1] - 60, "range": 8, "speed": 1.6, "rate": 9.0},
        ],
        "leaves": [],
        "layers": [
            # the TOMORROW fuse hums: a flicker and a faint glow over the open panel
            {"kind": "blink", "pattern": "1111011111101111", "rate": 9.0,
             "rects": [[fx + 1, fy + 1, 5, 3, "fff0c4"], [fx - 2, fy - 2, 11, 9, "f6cf7a", 0.18]]},
            # LANES neon down the stairwell buzzes
            {"kind": "blink", "pattern": "11111111011111111110", "rate": 7.0,
             "rects": [[cx - 15, WALL_BASE - 73, 30, 9, "ff7aa8", 0.2]]},
            # the lanes' glow breathing up the open well
            {"kind": "blink", "pattern": "1100", "rate": 0.8,
             "rects": [[WELL[0] + 60, WELL[3] - 12, 90, 8, "ff7aa8", 0.08]]},
            {"kind": "blink", "pattern": "0011", "rate": 0.8,
             "rects": [[WELL[0] + 150, WELL[3] - 10, 70, 7, "58e0d0", 0.08]]},
            {"kind": "twinkle", "points": [[x, y + 8, "f6cf7a", 1] for (x, y) in BULBS], "rate": 1.3, "min": 0.65},
        ],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
