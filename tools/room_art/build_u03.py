"""UMC atrium (U03): the building's grand hub at night. Tall arched windows between sandstone
pilasters, the club room's double doors on the left, a curtained alcove with the NEXT YEAR marquee
behind the voice booth (the booth itself is drawn by code), the service stair dropping away under an
arch on the right, a polished floor with a runner from the terrace doors and the Farrand gate."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import light_pool, flagstones, LEAVES
from props import OUT, IRON
from interior import PLASTER, PANEL, RUG, wall_clock
from lib_umc import (MARBLE, ROSE, BRASS, TRIM, SHADOW, GLOW, atrium_wall, sandstone_dado, frieze, ceiling_beam,
                     pilaster_in, atrium_window, sconce, club_doors, next_year_alcove, stair_down_arch,
                     atrium_floor, runner_rug, brass_ring, floor_reflection, cable, halo, enamel_sign, medallion,
                     STONE_IN, PLASTER as _P,
                     work_lamp, lobby_bench, welcome_desk, directory_board, potted_tree)

ROOM = "U03"
W, H = 800, 480
WALL_BASE = 118          # walk_bounds top: the back wall meets the floor here
DADO_TOP = 96
CLUB_DOOR = (90, 66)     # centre x, height of the leaves (placement 0 at y 192, painted on the wall)
STAIRS = (664, 740, 159)  # placement 2: x span and the floor line where the first tread starts
BOOTH = (382, 248)       # placement 3, drawn by code
WINDOWS = [178, 258, 506, 584]
PILASTERS = [140, 216, 290, 468, 544, 622, 754]
EAST_GATE = (730, 385)   # placement 10 threshold, the opening is in the right-hand wall
TERRACE = (360, 436)     # placement 1 threshold, the front doors (off the bottom edge)
RUNNER_X = 372           # runner centre: between the terrace doors (360) and the booth (382)
PENDANTS = [(200, 214), (560, 240), (120, 330), (470, 360), (250, 420), (640, 438)]


def paint_wall(bg):
    atrium_wall(bg, 0, 0, W, WALL_BASE, seed=1)
    ceiling_beam(bg, 0, 0, W)
    frieze(bg, 0, 6, W, inscription="UNIVERSITY MEMORIAL CENTER")
    sandstone_dado(bg, 0, DADO_TOP, W, WALL_BASE - DADO_TOP, seed=2)
    for px in PILASTERS:
        pilaster_in(bg, px - 5, 20, 10, WALL_BASE - 20)
    for i, wx in enumerate(WINDOWS):
        atrium_window(bg, wx - 18, 44, 36, 46, seed=10 + i, moon=(wx + 8, 34) if i == 3 else None)
    # sconces on the pilasters either side of the windows
    sconces = []
    for px in (216, 290, 468, 544, 622):
        sconce(bg, px, 62)
        sconces.append((px, 61))
    return sconces


def paint_club_door(bg):
    cx, h = CLUB_DOOR
    club_doors(bg, cx, WALL_BASE, w=46, h=h, plaque="CLUB ROOM")
    # a gig poster and a small sconce beside the door
    bx, by = 26, 40
    bg.rect(bx + 1, by + 1, 24, 32, C(SHADOW, 0.5))
    bg.rect(bx, by, 24, 32, "#e6d6b1"); bg.hline(bx, by, 24, "#fff3d6")
    bg.rect(bx + 2, by + 2, 20, 14, "#2a2440")
    bg.poly([(bx + 3, by + 15), (bx + 9, by + 7), (bx + 13, by + 11), (bx + 17, by + 6), (bx + 21, by + 15)], "#5a3a5a")
    bg.ellipse(bx + 15, by + 4, 4, 4, "#efe2b8")
    text(bg, "LAST", bx + 1, by + 16, "#7e3a30")
    for k in range(3):
        bg.hline(bx + 3, by + 26 + k * 2, 14 - k * 3, "#9a7c6e")
    bg.px(bx + 12, by + 1, "#c84a3c")


def paint_floor(bg):
    atrium_floor(bg, 0, WALL_BASE, W, H - WALL_BASE, seed=3)
    # skirting shadow and a dark marble border band along the wall
    bg.rect(0, WALL_BASE, W, 5, MARBLE[1]); bg.hline(0, WALL_BASE + 4, W, MARBLE[2])
    bg.rect(0, WALL_BASE, W, 2, C(SHADOW, 0.55))
    # reflections of the windows and the club doors in the polish
    for wx in WINDOWS:
        floor_reflection(bg, wx, WALL_BASE + 5, 22, 30, "#8a9ad0", 0.12)
    floor_reflection(bg, CLUB_DOOR[0], WALL_BASE + 5, 34, 24, "#f6cf7a", 0.14)
    for px in (216, 290, 468, 544, 622):
        floor_reflection(bg, px, WALL_BASE + 6, 4, 18, "#f6cf7a", 0.14)
    # runner from the terrace doors up to the booth's dais, and a short one to the club doors
    runner_rug(bg, RUNNER_X - 24, 258, 48, H - 258)
    for x in range(RUNNER_X - 24, RUNNER_X + 24, 2):
        bg.px(x, 257, RUG[5])
    runner_rug(bg, CLUB_DOOR[0] - 17, WALL_BASE + 3, 34, 84)
    for x in range(CLUB_DOOR[0] - 17, CLUB_DOOR[0] + 17, 2):
        bg.px(x, WALL_BASE + 87, RUG[5])
    # brass dais ring where the voice booth stands
    brass_ring(bg, BOOTH[0], BOOTH[1] - 8, 52, 14)
    light_pool(bg, BOOTH[0], BOOTH[1] - 6, 64, 18, strength=0.2)
    # pendant lamps hang from the ceiling out of view: their pools on the floor
    for (px, py) in PENDANTS:
        light_pool(bg, px, py, 46, 12, strength=0.17)


def wall_top(bg, x, y, w, h, inner="left"):
    """A wall cut by the camera: dark plaster top with a lit stone edge on the room side."""
    bg.rect(x, y, w, h, PLASTER[0])
    rng = np.random.default_rng(x + y)
    for _ in range(w * h // 30):
        bg.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), PLASTER[1])
    if inner == "left":
        bg.vline(x, y, h, STONE_IN[3]); bg.vline(x + 1, y, h, STONE_IN[1])
    elif inner == "right":
        bg.vline(x + w - 1, y, h, STONE_IN[3]); bg.vline(x + w - 2, y, h, STONE_IN[1])
    else:
        bg.hline(x, y, w, STONE_IN[3]); bg.hline(x, y + 1, w, STONE_IN[1])


def outside(bg, x, y, w, h, seed=0):
    """Lamplit flagstones beyond a doorway."""
    flagstones(bg, x, y, w, h, ["#4a3f45", "#5a4e52", "#7a6a62", "#86766a", "#8c7c70", "#9a8878"], seed=seed, row0=6, row1=8)
    light_pool(bg, x + w // 2, y + h // 2, w // 2 + 4, h // 2, strength=0.25)
    rng = np.random.default_rng(seed)
    for _ in range(w * h // 40):
        lx, ly = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        bg.px(lx, ly, LEAVES[int(rng.integers(len(LEAVES)))])


def paint_gates(bg):
    """The east gate to Farrand in the right-hand wall, and the terrace doors' spill at the bottom."""
    gx, gy = EAST_GATE
    # the side and front walls are seen from above as dark wall-tops; the gate and the terrace doors
    # are gaps in them showing the lamplit paving outside
    wall_top(bg, 782, WALL_BASE - 1, W - 782, H - WALL_BASE + 1, inner="left")
    wall_top(bg, 0, H - 22, W, 22, inner="top")
    wall_top(bg, 0, WALL_BASE - 1, 18, H - WALL_BASE + 1, inner="right")
    outside(bg, 782, gy - 64, W - 782, 64, seed=1)
    for yy in (gy - 66, gy):
        bg.rect(780, yy, 20, 3, STONE_IN[2]); bg.hline(780, yy, 20, STONE_IN[4])
    bg.rect(780, gy - 64, 2, 64, STONE_IN[3])
    # light from the gate spreading across the floor
    for i, (w0, a) in enumerate([(70, 0.05), (50, 0.07), (30, 0.09)]):
        bg.poly([(781, gy - 60 + i * 6), (781, gy), (781 - w0, gy + 4 - i), (781 - w0 * 0.6, gy - 40 + i * 10)], C("#f2c890", a))
    tx = TERRACE[0]
    outside(bg, tx - 34, H - 22, 68, 22, seed=2)
    for xx in (tx - 36, tx + 34):
        bg.rect(xx, H - 22, 3, 22, STONE_IN[3]); bg.vline(xx, H - 22, 22, STONE_IN[4])
    # terrace doors below the bottom edge: warm spill up the runner
    light_pool(bg, TERRACE[0], H - 14, 64, 16, strength=0.2)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=3)

    sconces = paint_wall(bg)
    paint_club_door(bg)
    bulbs = next_year_alcove(bg, BOOTH[0], 26, WALL_BASE, w=140, seed=4)
    paint_floor(bg)
    x0, x1, fy = STAIRS
    stair_down_arch(bg, x0, x1, WALL_BASE, fy, sign="REPAIR")
    paint_gates(bg)
    # autumn leaves blown in through the terrace doors and the gate, a dropped programme or two
    rng = np.random.default_rng(31)
    for (cx, cy, r, n) in [(TERRACE[0], 448, 60, 26), (760, 384, 40, 16), (300, 446, 30, 6)]:
        for _ in range(n):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
            lx, ly = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.4)
            if 20 <= lx < 780 and WALL_BASE + 4 < ly < H - 23:
                c = LEAVES[int(rng.integers(len(LEAVES)))]
                bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
    for (fx, fy, tilt) in [(262, 352, 1), (470, 300, -1), (96, 236, 1)]:
        bg.poly([(fx, fy), (fx + 9, fy - tilt), (fx + 10, fy + 5 - tilt), (fx + 1, fy + 6)], "#e6d6b1")
        bg.line(fx + 2, fy + 2, fx + 7, fy + 1, "#7e3a30"); bg.px(fx + 1, fy + 6, C(SHADOW, 0.5))
    # the work lamp's cord runs across the floor to a socket at the east wall
    cable(bg, [(619, 367), (650, 371), (700, 380), (742, 398), (781, 404)], "#16141f", hi="#6c6a88")
    bg.rect(780, 400, 3, 6, IRON[3])
    light_pool(bg, 615, 368, 56, 15, strength=0.24)
    light_pool(bg, 200, 340, 40, 9, strength=0.12)
    # dark margins outside the walkable hall
    bg.rect(18, H - 30, W - 36, 8, C(SHADOW, 0.25))
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(4, welcome_desk(102, 46, "LAST LIGHT", seed=1))
    save(5, directory_board(160, 36, "CLUB < / REPAIR >", seed=2))
    save(6, lobby_bench(94, 37, seed=3))
    save(7, work_lamp(66))
    save(8, potted_tree(50, 38, seed=5))
    save(9, potted_tree(48, 38, seed=8, pot="terracotta"))

    res = f"res://assets/art/rooms/{ROOM}/"
    chase = [{"kind": "blink", "pattern": "".join("1" if k == j else "0" for k in range(3)), "rate": 5.0,
              "rects": [[bx, by, 1, 1, "fff0c4"] for i, (bx, by) in enumerate(bulbs) if i % 3 == j]} for j in range(3)]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [0, 2],
        "fauna": [
            {"kind": "umc_moth", "x": 612, "y": 300, "range": 9, "speed": 1.4, "rate": 9.0},
        ],
        "leaves": [],
        "layers": chase + [
            {"kind": "twinkle", "points": [[x, y, "f6cf7a", 1] for (x, y) in sconces], "rate": 0.9, "min": 0.6},
        ],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
