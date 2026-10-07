"""E02 Shared workshop / Cal and Dev (800x480).

The Engineering Center's student workshop after hours, in the building's own raw fabric: walls of
grey board-formed concrete printed with plank grain, form-tie holes and run-off streaks, a waffle
slab and deep edge beam overhead, narrow windows set deep in the concrete onto the night, caged
lamps on conduit drops, the dust-collection duct hung under the beam, concrete piers between the
bays and a base course of rough Lyons sandstone under a cast sill. Along the back wall: the lockers (CAL, DEV), a drill press, the whiteboard where Cal's
floating arch for EVERY PLAN sits beside Dev's two spans FOR FEET, the pegboard, the electronics
bench with a live oscilloscope, a blueprint, the breaker panel and the bandsaw. The floor is sealed
concrete with a yellow walkway running between the two doors in the near wall: the loading court
(left, night outside) and the test floor (right, the lit high bay). Cal's and Dev's benches stand on
anti-fatigue mats; the keepsake spot (748, 326) is open floor.

State: Cal's study model rests on two piers once `model_revised` is set; the strapped deck planks on
Dev's bench are gone (installed) once `bridge_ready` is set. The test-floor door's lock (dev_met) is
the code-drawn label pill.
"""
import paths
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel import Canvas, C, text  # noqa: E402
from lib_umc import pegboard, extinguisher, halo, SHADOW, SAFETY  # noqa: E402
import lib_eng as E  # noqa: E402
import ec_interior as I  # noqa: E402

ROOM = "E02"
W, H = 800, 480
BASE = 142             # wall foot / top of the walkable floor
FRONT = 456            # near wall
CEIL = 22               # underside of the edge beam
DUCT_Y = 26            # dust duct hung under the beam
WIN_Y, WIN_H, WIN_W = 37, 22, 12                       # deep-set slot windows
WINDOWS = (40, 100, 176, 240, 302, 376, 446, 528, 632, 718)
PIERS = (142, 338, 600)                                # concrete piers (left x)
PIER_W = 16
DADO_Y = 112           # top of the sandstone base course (its cast sill)
PENDANTS = (210, 430, 590)
LOCKERS_X = 22
DRILL_X = 100
WHITEBOARD = (160, 72, 180, 40)
PEGBOARD = (354, 76, 96, 34)
COUNTER = (466, 140)   # x, width
BLUEPRINT_AT = (614, 72, 46, 32)
PANEL_X = 690
BANDSAW_X = 716
DOOR_L = (34, 96)
DOOR_R = (694, 756)
AISLE_TOP, AISLE_BOT = 416, 438
KEEPSAKE = (748, 326)
LAMP = (115, 344)
# sealed shop floor: warm grey with a hint of green (reads neutral under the night tint)
SHOP_FLOOR = ["#2c302e", "#3a3f3c", "#464c48", "#585e59", "#5e645e", "#656b64", "#767d75", "#868d84"]
# the bench zone is painted a darker green epoxy inside a yellow line
ZONE_FLOOR = ["#28302e", "#323c39", "#3c4844", "#46534d", "#4b5953", "#525f58", "#5d6b63", "#6b7a70"]
ZONE = (196, 230, 446, 146)
LAYOUT = (64, 178, 132, 42)   # the full-scale deck panel taped out on the floor


def paint_fabric(cv, x0, w, seed=22, windows=WINDOWS, piers=PIERS):
    """The building itself over a span of wall: waffle slab and edge beam, board-formed concrete,
    deep slot windows, concrete piers, the sandstone base course. Returns star points."""
    I.coffered_ceiling(cv, x0, w, 0, CEIL, seed=seed)
    I.board_concrete(cv, x0, CEIL, w, DADO_Y - CEIL, seed=seed + 1, foot=0)
    E.tint_rect(cv, x0, CEIL, w, 12, SHADOW, 0.22)                # the high wall in the beam's shade
    stars = []
    for k, wx in enumerate(windows):
        stars += I.deep_window(cv, wx, WIN_Y, WIN_W, WIN_H, seed=seed + 10 + k)
    I.lyons_wall(cv, x0, DADO_Y, w, BASE - DADO_Y, seed=seed + 2)
    for px in piers:                                              # piers frame the stone panels
        I.conc_pier(cv, px, CEIL, PIER_W, BASE - CEIL, seed=seed + px)
    return stars


def paint_back_wall(bg):
    stars = paint_fabric(bg, 0, W)
    E.dust_duct(bg, 96, 772, DUCT_Y, 7, drops=[(DRILL_X + 14, BASE - 67)])
    # conduit under the beam feeding the caged lamps, and the riser to the breaker panel
    I.conduit(bg, 150, 700, CEIL + 13)
    bulbs = [I.cage_lamp(bg, x, CEIL + 14, 22) for x in PENDANTS]
    return stars, bulbs


def paint_wall_things(bg):
    # lockers with a hard hat and helmet on top
    E.lockers(bg, LOCKERS_X, BASE - 56, 4, 18, 56, ("CAL", "DEV", "", ""), seed=3)
    E.drill_press(bg, DRILL_X, BASE)
    E.first_aid(bg, 136, 80)
    extinguisher(bg, 140, BASE - 6)
    # whiteboard: the two designs side by side
    x, y, w, h = WHITEBOARD
    E.whiteboard_two_designs(bg, x, y, w, h)
    # stencil over the pegboard and the pegboard itself
    px, py, pw, ph = PEGBOARD
    text(bg, "WORKSHOP 1B", px + 2, py - 14, "#d8c8a8")
    pegboard(bg, px, py, pw, ph, tools=True, seed=5)
    I.jbox(bg, px - 8, DADO_Y - 12)
    # the electronics bench
    cx, cw = COUNTER
    elec = E.electronics_counter(bg, cx, DADO_Y, cw, BASE, seed=6)
    # blueprint, clock, breaker panel, bandsaw, posters
    E.blueprint_sheet(bg, *BLUEPRINT_AT, seed=7)
    E.wall_clock(bg, 676, 66, 6)
    for cx in (PANEL_X + 4, PANEL_X + 10):                       # conduits up into the beam
        bg.rect(cx, CEIL, 2, 62, E.STEEL[3]); bg.vline(cx, CEIL, 62, E.STEEL[6])
    E.breaker_panel(bg, PANEL_X, 84, 18, 26, "1B")
    E.bandsaw(bg, BANDSAW_X, BASE)
    E.safety_poster(bg, 754, 60, 22, 26, "EYES", "#2c4a8a", "goggles")
    E.safety_poster(bg, 754, 90, 22, 20, "EARS", "#2a7a4a", "ears")
    # a sprinkler riser in the corner
    bg.rect(8, CEIL, 4, BASE - CEIL, "#7e3a30"); bg.vline(8, CEIL, BASE - CEIL, "#a85a48")
    bg.rect(6, 92, 8, 4, "#5a2a22")
    return elec


def paint_floor(bg):
    fh = FRONT - BASE
    E.put_rgb(bg, 0, BASE, E.epoxy_np(W, fh, seed=31, pal=SHOP_FLOOR))
    E.control_joints(bg, 20, BASE, W - 40, fh, SHOP_FLOOR[1], every_x=128, every_y=104, x_off=60)
    zx, zy, zw, zh = ZONE
    E.put_rgb(bg, zx, zy, E.epoxy_np(zw, zh, seed=33, pal=ZONE_FLOOR))
    for (a, b, c, d) in ((zx, zy, zw, 2), (zx, zy + zh - 2, zw, 2), (zx, zy, 2, zh), (zx + zw - 2, zy, 2, zh)):
        E.worn_line(bg, a, b, c, d, SAFETY[2], 0.7, seed=a + b)
    E.micro_text(bg, "WORK ZONE", zx + 6, zy + 5, C(SAFETY[2], 0.6))
    paint_layout(bg)
    # oil under the tool chest's usual spot, cart wheel scuffs along the walkway, offcuts by the saw
    E.soft_ellipse(bg, 226, 402, 18, 4, SHOP_FLOOR[1], 0.5)
    E.soft_ellipse(bg, 560, 250, 9, 3, SHOP_FLOOR[1], 0.4)
    for k in range(4):
        bg.line(140 + k * 130, AISLE_TOP + 6 + (k % 2), 210 + k * 130, AISLE_TOP + 5 + (k % 2), C(SHOP_FLOOR[2], 0.7))
    for (ox, oy, ow, oh, c) in ((704, 180, 12, 4, E.PLY[4]), (720, 186, 7, 3, E.PLY[5]), (692, 190, 5, 2, E.PLY[3])):
        bg.rect(ox, oy, ow, oh, c); bg.hline(ox, oy, ow, E.PLY[6]); bg.hline(ox, oy + oh, ow, C(SHADOW, 0.5))
    # the wall foot: a dark line and a lit sliver where the floor meets the cove base
    bg.hline(0, BASE, W, "#121218"); bg.hline(0, BASE + 1, W, C(SHADOW, 0.35))
    # walkway between the two doors in the near wall
    y = SAFETY[2]
    E.worn_line(bg, DOOR_L[0] - 4, AISLE_TOP, DOOR_R[1] - DOOR_L[0] + 8, 2, y, 0.75, seed=1)
    E.worn_line(bg, DOOR_L[1] + 4, AISLE_BOT, DOOR_R[0] - DOOR_L[1] - 8, 2, y, 0.75, seed=2)
    for (x, y0) in ((DOOR_L[0] - 4, AISLE_TOP), (DOOR_L[1] + 4, AISLE_BOT), (DOOR_R[0] - 6, AISLE_BOT), (DOOR_R[1] + 2, AISLE_TOP)):
        E.worn_line(bg, x, y0, 2, FRONT - y0, y, 0.75, seed=x)
    # floor arrows along the walkway
    for ax in (200, 400, 600):
        for k in range(3):
            bg.hline(ax - k, AISLE_TOP + 7 + k, 1 + 2 * k, C("#e8e2d0", 0.35))
            bg.hline(ax - k, AISLE_TOP + 14 - k, 1 + 2 * k, C("#e8e2d0", 0.0))
        bg.rect(ax - 6, AISLE_TOP + 9, 6, 2, C("#e8e2d0", 0.35))
        bg.px(ax + 1, AISLE_TOP + 10, C("#e8e2d0", 0.35))
    # keep-clear hatch in front of the breaker panel, a machine box around the bandsaw
    for k in range(0, 30, 5):
        bg.line(PANEL_X - 6 + k, BASE + 18, PANEL_X - 6 + k + 12, BASE + 4, C(SAFETY[2], 0.5))
    bg.rect(PANEL_X - 6, BASE + 3, 30, 16, C("#000000", 0.0))
    E.worn_line(bg, BANDSAW_X - 8, BASE + 30, 46, 2, SAFETY[2], 0.6, seed=9)
    E.worn_line(bg, BANDSAW_X - 8, BASE + 3, 2, 27, SAFETY[2], 0.6, seed=10)
    E.worn_line(bg, BANDSAW_X + 36, BASE + 3, 2, 27, SAFETY[2], 0.6, seed=11)
    # anti-fatigue mats where Cal and Dev stand
    E.rubber_mat(bg, 246, 296, 108, 24)
    E.rubber_mat(bg, 466, 331, 108, 24)
    # sawdust under the drill press and around Cal's bench, a cord to Dev's bench, a drain
    E.sawdust(bg, DRILL_X + 14, BASE + 8, 16, 4, seed=1)
    E.sawdust(bg, 230, 286, 22, 5, seed=2)
    E.sawdust(bg, 372, 300, 14, 4, seed=3)
    E.floor_cord(bg, [(PEGBOARD[0] + 86, BASE + 1), (PEGBOARD[0] + 88, BASE + 22), (468, 214), (492, 270), (496, 302)])
    E.floor_drain(bg, 400, 372)
    # a dropped tape measure and some screws
    bg.rect(612, 380, 6, 5, "#1a1524"); bg.rect(613, 381, 4, 3, SAFETY[3]); bg.hline(618, 383, 12, "#e6d6b1")
    for (sx, sy) in ((160, 262), (164, 265), (432, 236), (640, 404)):
        bg.px(sx, sy, "#a2a8b8")


def paint_layout(bg):
    """Blue painter's tape on the floor: a full-scale outline of the court bridge's deck panel,
    with braces, tick marks and a dimension line (flat, walkable)."""
    x, y, w, h = LAYOUT
    tape, ink = "#4a7ac8", "#2c4a9a"
    for (a, b, c, d) in ((x, y, w, 2), (x, y + h - 2, w, 2), (x, y, 2, h), (x + w - 2, y, 2, h)):
        bg.rect(a, b, c, d, C(tape, 0.8))
    for k in range(1, 3):
        bx = x + k * w // 3
        bg.rect(bx, y, 2, h, C(tape, 0.8))
    for k in range(3):
        x0 = x + k * w // 3
        bg.line(x0 + 2, y + 2, x0 + w // 3 - 1, y + h - 3, C(tape, 0.7))
    for tx in range(x, x + w + 1, 11):
        bg.vline(tx, y - 4, 2, C(tape, 0.7))
    bg.hline(x, y - 7, w, C(ink, 0.7)); bg.vline(x, y - 9, 5, C(ink, 0.7)); bg.vline(x + w - 1, y - 9, 5, C(ink, 0.7))
    E.micro_text(bg, "DECK PANEL 1:1", x + 4, y + h + 3, "#5a8ad8")
    # the roll of tape left on the line
    bg.ellipse(x + w + 4, y + h - 6, 7, 5, "#1a1524"); bg.ellipse(x + w + 5, y + h - 5, 5, 3, tape); bg.px(x + w + 7, y + h - 4, "#1a1524")


def paint_near_wall(bg):
    E.front_wall(bg, FRONT, W, H - FRONT, gaps=(DOOR_L, DOOR_R))
    E.door_gap(bg, DOOR_L[0], DOOR_L[1], FRONT, H - FRONT, outside="night")
    E.door_gap(bg, DOOR_R[0], DOOR_R[1], FRONT, H - FRONT, outside="lit")
    # side walls outside the walk bounds
    for x0 in (0, W - 20):
        bg.rect(x0, BASE, 20, FRONT - BASE, "#14161e")
        for yy in range(BASE + 8, FRONT, 8):
            bg.hline(x0, yy, 20, "#1a1d26")
    bg.vline(19, BASE, FRONT - BASE, E.CONC[4]); bg.vline(W - 20, BASE, FRONT - BASE, E.CONC[4])


def paint_lights(bg):
    for x in PENDANTS:
        E.stepped_glow(bg, x, BASE + 14, 70, 16, "#f6cf7a", 0.12, 3)
        halo(bg, x, CEIL + 44, 40, "#f6cf7a", 0.06, 3)
        E.stepped_glow(bg, x + 1, CEIL + 50, 34, 26, "#f6cf7a", 0.07, 2)     # lamp wash on the concrete
    # overhead light on the two benches
    E.stepped_glow(bg, 300, 282, 130, 34, "#f6cf7a", 0.15, 3)
    E.stepped_glow(bg, 520, 318, 130, 34, "#f6cf7a", 0.15, 3)
    # the save lamp
    E.stepped_glow(bg, LAMP[0], LAMP[1] - 2, 40, 11, "#f6cf7a", 0.16, 3)
    # cool night through the court door, warm high-bay light through the test-floor door
    E.stepped_glow(bg, sum(DOOR_L) // 2, FRONT - 4, 40, 18, "#8aa4e8", 0.10, 2)
    E.stepped_glow(bg, sum(DOOR_R) // 2, FRONT - 4, 40, 18, "#f6cf7a", 0.10, 2)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=2)

    stars, bulbs = paint_back_wall(bg)
    elec = paint_wall_things(bg)
    paint_floor(bg)
    paint_near_wall(bg)
    paint_lights(bg)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None, name=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    # Cal's bench (the study model gains two piers once the model is revised)
    alt, _, _ = E.maple_bench(170, 45, "arch_revised", seed=1)
    alt.save(os.path.join(out, "prop-0-revised.png"))
    save(0, E.maple_bench(170, 45, "arch", seed=1), {"flag": "model_revised", "flag_texture": res + "prop-0-revised.png"})
    # Dev's bench (the court-bridge planks leave once the bridge is installed)
    alt, _, _ = E.maple_bench(170, 45, "spans_done", seed=2)
    alt.save(os.path.join(out, "prop-1-installed.png"))
    save(1, E.maple_bench(170, 45, "spans", seed=2), {"flag": "bridge_ready", "flag_texture": res + "prop-1-installed.png"})
    save(2, E.tool_shelf_tags(95, 96, seed=3))
    save(3, E.tool_chest(70, 44, seed=4))
    save(4, E.shop_floor_lamp(68))

    # oscilloscope frames
    sx, sy, sw, sh = elec["screen"]
    n = 6
    layers = []
    for k in range(n):
        fr = E.scope_frame(sw, sh, k, n, "sine")
        fr.save(os.path.join(out, f"scope-{k}.png"))
        layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(n)), "rate": 7.0,
                       "texture": res + f"scope-{k}.png", "x": sx, "y": sy})
    d0, d1 = elec["digits"]
    lx, ly = elec["led"]
    layers += [
        # soldering station heater LED cycling, the supply's readout flickering in its last digit
        {"kind": "blink", "pattern": "11110000", "rate": 2.0, "rects": [[lx, ly, 2, 2, "ff5a3a"], [lx - 1, ly - 1, 4, 4, "ff5a3a", 0.25]]},
        {"kind": "blink", "pattern": "10", "rate": 1.5, "rects": [[d0[0] + 6, d0[1] + 1, 1, 3, "1a100c"], [d1[0] + 6, d1[1] + 1, 1, 3, "1a100c"]]},
        {"kind": "twinkle", "points": [[x, y, c.lstrip("#"), 1] for (x, y, c) in stars], "rate": 1.3, "min": 0.15},
        {"kind": "twinkle", "points": [[bx, by, "fff0c4", 2] for (bx, by) in bulbs] + [[LAMP[0], LAMP[1] - 62, "fff0c4", 2]],
         "rate": 0.9, "min": 0.8},
        # dust hanging in the pendant light and over Cal's bench
        {"kind": "particles", "style": "dust", "count": 7, "rect": [150, 40, 500, 90], "speed": [2, 3], "color": "f6dca0"},
        {"kind": "particles", "style": "dust", "count": 5, "rect": [220, 200, 160, 70], "speed": [1, 2], "color": "f6dca0"},
    ]

    manifest = {
        "background": res + "background.png",
        "width": W,
        "props": props,
        "label_only": [],
        "occluders": [],
        "overlays": [],
        "fauna": [
            {"kind": "umc2_mouse", "x": 448, "y": BASE + 4, "range": 16, "speed": 0.5, "rate": 5.0},
            {"kind": "lamp_moth", "x": LAMP[0] + 1, "y": LAMP[1] - 66, "range": 7, "speed": 1.8, "rate": 9.0},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
