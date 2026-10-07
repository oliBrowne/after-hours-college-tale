"""Macky lobby (M02): a choice of doors.

The back wall: warm ochre plaster over a dark oak dado, dressed sandstone pilasters, a stencilled
frieze under the coffered ceiling. Left, two tall round-headed windows with stained-glass borders
look west at the Flatirons (night sky with stars, or sunrise lighting the slabs pink). In the
middle, the great padded leather doors into the house under a gilt sunburst fanlight, AUDITORIUM
carved over them (they stand open, on the lit stage, once Rook has an ending). Right, an open arch
with the stone stair climbing to the BALCONY. Between them a portrait of Andrew Macky. Iron hall
lanterns and hanging signs point the two branches: CLOAKROOM left, ORCHESTRA PIT right.
The floor: rose sandstone tiles with oxblood cabochons, an inlaid border, oxblood runners crossing
import paths
from the front doors (bottom) to the auditorium and from the cloakroom to the pit.
At dawn the windows show sunrise over the Flatirons, and the front doors at our backs (east) let
the morning in: two long panels of light run up the runner, the directory's shadow stretching
toward the auditorium doors.
Props: the TWO CHOICES directory, two fern planters, two velvet benches, a parchment floor lamp."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from props import OUT, IRON
from lib_norlin import (plaster_wall, oak_wainscot, cabochon_floor, floor_inlay, runner_n, wall_sconce, standard_lamp,
                        depth_shade)
from lib_macky import (lobby_tiles, lobby_window, auditorium_doors, stair_up, hanging_lantern, hanging_sign, gilt_band,
                       directory_board, lobby_planter, lobby_bench, dressed_band, DRESS, PLASTER_M, VELVET_M, CARPET_M,
                       TILE_M, INSET_M, SHADE_PARCH, BRASS, GILT_M, SHADOW)

ROOM = "M02"
W, H = 800, 480
WALL = 142                       # foot of the back wall (top of the walk area)
DADO = 104                       # top of the oak dado
WALK = (20, 142, 760, 314)
WINDOWS = [(90, 36), (228, 36)]  # (centre x, crown y)
DOORS_X = 400
STAIR_X = 680
PILASTERS = [12, 158, 298, 502, 600, 788]
LANTERNS = [(158, 60), (600, 60)]
LAMP = (135, 389)
RUN_V = (368, 432)               # runner from the front doors up to the auditorium
RUN_H = (284, 316)               # runner from the cloakroom across to the pit
DOOR_BOX = (340, 0, 460, 200)    # region repainted by the open-doors overlay


def pilaster(cv, cx, top, base, w=12):
    """A dressed sandstone pilaster with a simple capital and plinth."""
    x = cx - w // 2
    cv.rect(x, top, w, base - top, DRESS[3]); cv.vline(x, top, base - top, DRESS[5]); cv.vline(x + w - 1, top, base - top, DRESS[1])
    cv.vline(x + 3, top + 8, base - top - 16, DRESS[2]); cv.vline(x + w - 4, top + 8, base - top - 16, DRESS[4])
    cv.rect(x - 2, top, w + 4, 5, DRESS[4]); cv.hline(x - 2, top, w + 4, DRESS[6]); cv.hline(x - 2, top + 4, w + 4, DRESS[1])
    cv.rect(x - 2, base - 7, w + 4, 7, DRESS[3]); cv.hline(x - 2, base - 7, w + 4, DRESS[5])


def frieze(cv, y):
    """The painted stencil band under the ceiling: oxblood lozenges and gilt dots on ochre."""
    cv.rect(0, y, W, 9, PLASTER_M[5])
    cv.hline(0, y, W, PLASTER_M[2]); cv.hline(0, y + 8, W, PLASTER_M[2])
    for x in range(4, W, 12):
        cv.poly([(x, y + 4), (x + 4, y + 1), (x + 8, y + 4), (x + 4, y + 7)], VELVET_M[3])
        cv.px(x + 4, y + 4, GILT_M)
        cv.px(x + 10, y + 4, "#3a5a4a")


def ceiling(cv):
    cv.rect(0, 0, W, 11, "#2a1a1c")
    cv.hline(0, 7, W, WOOD_M[3]); cv.hline(0, 8, W, WOOD_M[4]); cv.hline(0, 9, W, WOOD_M[2]); cv.hline(0, 10, W, C(SHADOW, 0.6))
    for x in range(20, W, 64):
        cv.rect(x, 0, 30, 6, "#3a2424"); cv.hline(x, 5, 30, BRASS[1])


WOOD_M = ["#2c1a1a", "#4a2b24", "#6b3f2e", "#8c573b", "#ad754d", "#c99364"]


def portrait(cv, x, y, w=40, h=50):
    """Andrew J. Macky in oils: gilt frame, dark ground, a bearded face, a brass name plate."""
    cv.rect(x - 4, y - 4, w + 8, h + 8, OUT)
    cv.rect(x - 3, y - 3, w + 6, h + 6, BRASS[2]); cv.rect(x - 3, y - 3, w + 6, 1, BRASS[4]); cv.rect(x - 2, y - 2, w + 4, h + 4, BRASS[1])
    cv.rect(x - 1, y - 1, w + 2, h + 2, BRASS[3])
    cv.rect(x, y, w, h, "#1e1a1c")
    for yy in range(y, y + h, 3):
        cv.hline(x, yy, w, "#24201e")
    cx = x + w // 2
    # coat and shoulders
    cv.poly([(x + 4, y + h), (cx - 8, y + 30), (cx + 8, y + 30), (x + w - 4, y + h)], "#16141a")
    cv.poly([(cx - 3, y + 31), (cx + 3, y + 31), (cx, y + 40)], "#d8d0c0")
    cv.rect(cx - 1, y + 33, 2, 6, "#3a1a1e")
    # head: face, receding grey hair, white beard
    cv.ellipse(cx - 7, y + 9, 14, 17, "#c89070"); cv.ellipse(cx - 5, y + 11, 6, 8, "#d8a080")
    cv.ellipse(cx - 7, y + 7, 14, 7, "#9a9088"); cv.rect(cx - 7, y + 11, 2, 6, "#9a9088"); cv.rect(cx + 5, y + 11, 2, 6, "#9a9088")
    cv.ellipse(cx - 8, y + 18, 16, 15, "#d8d4cc"); cv.ellipse(cx - 6, y + 20, 12, 11, "#ece8e0")
    cv.hline(cx - 4, y + 15, 3, "#3a2a2a"); cv.hline(cx + 2, y + 15, 3, "#3a2a2a")
    cv.hline(cx - 3, y + 20, 7, "#a89888")
    cv.rect(x + w // 2 - 14, y + h + 6, 28, 7, OUT); cv.rect(x + w // 2 - 13, y + h + 7, 26, 5, BRASS[3])
    cv.hline(x + w // 2 - 10, y + h + 9, 20, BRASS[1])


def poster_c(cv, x, y, w=30, h=44):
    """A framed commencement poster: black and CU gold, the torch, a few lines of type."""
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT); cv.rect(x - 1, y - 1, w + 2, h + 2, BRASS[2])
    cv.rect(x, y, w, h, "#1a1418")
    cv.rect(x + 2, y + 2, w - 4, 10, "#d8b45a"); cv.hline(x + 2, y + 2, w - 4, "#f0d68a")
    cx = x + w // 2
    cv.rect(cx - 1, y + 16, 3, 12, "#d8b45a"); cv.rect(cx - 3, y + 15, 7, 2, "#d8b45a")
    cv.poly([(cx - 3, y + 15), (cx, y + 8 + 6), (cx + 3, y + 15)], "#f0a040"); cv.px(cx, y + 13, "#fff0c4")
    for k in range(3):
        cv.hline(x + 5, y + 32 + k * 3, w - 10, "#a89a86" if k else "#e6d6b1")
    text(cv, "CU", cx - text_width("CU") // 2, y + 2, "#1a1418")


def back_wall(cv, dawn, doors_open=False):
    plaster_wall(cv, 0, 11, W, DADO - 11, pal=PLASTER_M, seed=3)
    frieze(cv, 11)
    ceiling(cv)
    oak_wainscot(cv, 0, DADO, W, WALL - DADO, seed=4, panel=26)
    lights = []
    for px_ in PILASTERS:
        pilaster(cv, px_, 20, WALL)
    for (wx, wy) in WINDOWS:
        lobby_window(cv, wx, wy, 40, 66, dawn=dawn, seed=wx)
    # the auditorium doors and their name
    fan = auditorium_doors(cv, DOORS_X, WALL, open_=doors_open, dawn=dawn, seed=5)
    lights.append((fan[0], fan[1], "f6cf7a", 2))
    gilt_band(cv, DOORS_X, 21, "AUDITORIUM", w=96)
    for sx in (DOORS_X - 58, DOORS_X + 58):
        wall_sconce(cv, sx, 74)
        lights.append((sx, 66, "fff0c4", 1))
    # the balcony stair
    land = stair_up(cv, STAIR_X, WALL, 66, 82, dawn=dawn, label="BALCONY")
    lights.append((land[0], land[1], "f6cf7a", 1))
    # Andrew Macky, and a commencement poster by the stair
    portrait(cv, 531, 40, 40, 48)
    poster_c(cv, 744, 38)
    # lanterns and the two signs for the branches
    for (lx, ly) in LANTERNS:
        hanging_lantern(cv, lx, ly, chain_top=11)
        lights.append((lx, ly - 15, "fff0c4", 2))
    hanging_sign(cv, 90, 16, "< CLOAKROOM", chain_top=11)
    hanging_sign(cv, 551, 18, "ORCHESTRA PIT >", chain_top=11)
    # shadow line where the wall meets the floor
    cv.rect(0, WALL - 2, W, 2, C(SHADOW, 0.35))
    return lights


def floor(cv, dawn):
    lobby_tiles(cv, 0, WALL, W, H - WALL, seed=7, size=22)
    floor_inlay(cv, 22, WALL + 6, W - 44, 318, t=5, colour="#5a2228", line="#c8a070")
    # the runners: front doors to the auditorium; cloakroom across to the pit
    runner_n(cv, RUN_V[0], WALL, RUN_V[1] - RUN_V[0], H - WALL, pal=CARPET_M, vertical=True)
    runner_n(cv, 0, RUN_H[0], W, RUN_H[1] - RUN_H[0], pal=CARPET_M, vertical=False)
    # brass stair rods where the runners cross
    cx0, cx1 = RUN_V
    cv.rect(cx0, RUN_H[0], cx1 - cx0, RUN_H[1] - RUN_H[0], CARPET_M[2])
    cv.rect(cx0 + 4, RUN_H[0] + 4, cx1 - cx0 - 8, RUN_H[1] - RUN_H[0] - 8, CARPET_M[5])
    cv.rect(cx0 + 6, RUN_H[0] + 6, cx1 - cx0 - 12, RUN_H[1] - RUN_H[0] - 12, CARPET_M[3])
    mx, my = (cx0 + cx1) // 2, (RUN_H[0] + RUN_H[1]) // 2
    cv.poly([(mx - 16, my), (mx, my - 9), (mx + 16, my), (mx, my + 9)], CARPET_M[5])
    cv.poly([(mx - 12, my), (mx, my - 6), (mx + 12, my), (mx, my + 6)], CARPET_M[2])
    cv.poly([(mx - 5, my), (mx, my - 3), (mx + 5, my), (mx, my + 3)], CARPET_M[6])


def margins(cv, dawn):
    # side margins and the bottom strip outside the walk area, darker in steps
    for (x, w) in [(0, WALK[0]), (WALK[0] + WALK[2], W - WALK[0] - WALK[2])]:
        cv.rect(x, WALL, w, H - WALL, C(SHADOW, 0.28))
    bottom = WALK[1] + WALK[3]
    depth_shade(cv, 0, bottom - 30, W, H - bottom + 30, steps=3, alpha=0.36)
    # the side openings: brighter where the runner leaves (cloakroom left, pit stairs right)
    light_pool(cv, 8, (RUN_H[0] + RUN_H[1]) // 2, 22, 22, strength=0.16)
    light_pool(cv, W - 8, (RUN_H[0] + RUN_H[1]) // 2, 22, 22, strength=0.16)


def light(cv, dawn, lights):
    for (x, y, c, s) in lights:
        pass
    for sx in (DOORS_X - 58, DOORS_X + 58):
        light_pool(cv, sx, WALL + 6, 30, 8, strength=0.12)
    light_pool(cv, DOORS_X, WALL + 8, 46, 10, strength=0.18)
    light_pool(cv, STAIR_X, WALL + 6, 34, 8, strength=0.12)
    for (lx, ly) in LANTERNS:
        light_pool(cv, lx, WALL + 46, 80, 30, strength=0.2)
    # the polished tiles mirror the lights on the wall: short broken streaks below each one
    for (x, w_, a) in [(DOORS_X, 30, 0.12)] + [(lx, 8, 0.14) for (lx, ly) in LANTERNS] + [(DOORS_X - 58, 4, 0.1), (DOORS_X + 58, 4, 0.1), (STAIR_X, 10, 0.08)]:
        for k, yy in enumerate(range(WALL + 3, WALL + 40, 3)):
            cv.rect(x - w_ // 2 + (k % 2), yy, w_, 1, C("#f6cf7a", a * (1 - k / 13)))
    light_pool(cv, LAMP[0], LAMP[1] + 2, 54, 16, strength=0.26)
    if dawn:
        # the sun comes up behind us: the front doors (below the screen) throw two long panels
        # of morning light up the runner, and the directory's shadow stretches toward the doors
        fan = Canvas(W, H)
        for (inset, a) in [(0, 0.09), (7, 0.09), (14, 0.11)]:
            for (x0, x1) in [(DOORS_X - 54, DOORS_X - 3), (DOORS_X + 3, DOORS_X + 54)]:
                fan.poly([(x0 + inset, H), (x1 - inset, H), (x1 - inset - 14, 214 + inset * 2), (x0 + inset - 10, 214 + inset * 2)],
                         C("#f8d498", a))
        lit = fan.a[..., 3]
        shadow = np.zeros((H, W), bool)
        sh = Canvas(W, H)
        sh.poly([(DOORS_X - 80, 322), (DOORS_X + 4, 322), (DOORS_X - 14, 236), (DOORS_X - 92, 236)], "#000000")
        shadow = sh.a[..., 3] > 0.5
        lit = np.clip(lit * 2.2, 0, 0.6)
        lit = np.where(shadow, lit * 0.25, lit)
        col = np.array(C("#f8d498")[:3], np.float32)
        cv.a[..., :3] = cv.a[..., :3] * (1 - lit[..., None]) + (cv.a[..., :3] * 0.45 + col * 0.55) * lit[..., None]
        # the windows glow pink on the dado below them (reflected alpenglow)
        for (wx, wy) in WINDOWS:
            cv.rect(wx - 22, DADO + 1, 44, 6, C("#f0a8a0", 0.08))
    else:
        # a little moonlight below the windows
        for (wx, wy) in WINDOWS:
            cv.poly([(wx - 14, WALL + 2), (wx + 14, WALL + 2), (wx + 40, WALL + 70), (wx + 14, WALL + 70)], C("#b4c4f0", 0.06))


def paint(dawn, doors_open=False):
    cv = Canvas(W, H, fill="#171a2b", seed=8)
    lights = back_wall(cv, dawn, doors_open)
    floor(cv, dawn)
    if doors_open:
        # the house light pours out across the floor in front of the doors
        for (rx, ry, a) in [(60, 26, 0.08), (44, 18, 0.1), (30, 12, 0.12)]:
            cv.poly([(DOORS_X - 30, WALL), (DOORS_X + 30, WALL), (DOORS_X + rx, WALL + ry * 2), (DOORS_X - rx, WALL + ry * 2)], C("#f6cf7a", a))
    light(cv, dawn, lights)
    margins(cv, dawn)
    return cv, lights


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    night, lights = paint(False)
    night.save(os.path.join(out, "background.png"))
    day, _ = paint(True)
    day.save(os.path.join(out, "background-dawn.png"))
    # Rook's ending opens the doors to the stage: the open doors and their spill as an overlay
    opened, _ = paint(False, doors_open=True)
    x0, y0, x1, y1 = DOOR_BOX
    ov = Canvas(x1 - x0, y1 - y0)
    ov.a = opened.a[y0:y1, x0:x1].copy()
    ov.save(os.path.join(out, "doors-open.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(0, directory_board(120, 74, title="THREE WAYS", rows=(("< CLOAKROOM", ""), ("ORCHESTRA PIT >", ""), ("BALCONY ^ AFTER", ""))))
    save(1, lobby_planter(82, 54, seed=1))
    save(2, lobby_planter(82, 54, seed=2))
    save(3, lobby_bench(115, 32, seed=3))
    save(4, lobby_bench(115, 32, seed=4))
    save(5, standard_lamp(68, shade_pal=SHADE_PARCH, seed=5))

    res = f"res://assets/art/rooms/{ROOM}/"
    glow = [[int(x), int(y), c, s] for (x, y, c, s) in lights]
    glow.append([LAMP[0], LAMP[1] - 63, "fff0c4", 2])
    manifest = {
        "background": res + "background.png",
        "background_dawn": res + "background-dawn.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": [{"texture": res + "doors-open.png", "x": x0, "y": y0, "flag": "rook_resolution"}],
        "fauna": [{"kind": "lamp_moth", "x": LAMP[0] + 4, "y": LAMP[1] - 58, "range": 7, "speed": 1.7, "rate": 9.0}],
        "layers": [
            {"kind": "twinkle", "points": glow, "rate": 1.1, "min": 0.55},
            {"kind": "particles", "style": "dust", "count": 16, "rect": [340, 230, 120, 230], "speed": [0, 3],
             "color": "f8e0b0", "flag": "dawn_started"},
        ],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
