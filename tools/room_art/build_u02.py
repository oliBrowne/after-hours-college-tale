"""UMC terrace (U02): painted backdrop, depth occluders, props and animal placements."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from midlib import sprite_from_cell
from pixel import Canvas, C, shade
from sky import panorama
from surfaces import flagstones, light_pool, ashlar_wall
from facade import umc_facade, steps
from props import (lamp_post, park_bench, planter_box, custodian_cart, bike_workbench, shrub, grass_tuft,
                   MUM, LEAF, SAND)

PAVE = ["#4a3f45", "#5a4e52", "#665a5c", "#6c5f60", "#726465", "#7b6c6b"]
WALL = ["#3a2c31", "#5b4644", "#8a6e60", "#9a7c6b", "#b49481", "#cdb099"]


def tint(sprite, mul):
    out = sprite.copy()
    out[..., :3] *= np.array(mul)
    return out


def build(project):
    out = os.path.join(project, "assets/art/rooms/U02")
    os.makedirs(out, exist_ok=True)
    W, H = 640, 360
    bg = Canvas(W, H, fill="#171a2b", seed=2)
    sky, _ = panorama(W, 150, scale=2.2)
    bg.a[:150] = sky

    # Shrubs behind the low wall, then the wall itself.
    rng = np.random.default_rng(4)
    for x in list(range(-6, 160, 17)) + list(range(480, 650, 17)):
        w = int(rng.integers(20, 30)); h = int(rng.integers(13, 19))
        bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.25 else None), x, 108 - h + int(rng.integers(0, 4)))
    for x0, x1 in [(0, 152), (488, 640)]:
        ashlar_wall(bg, x0, 106, x1 - x0, 16, WALL, seed=x0)

    # Paving first so trees and the building sit on it.
    flagstones(bg, 0, 122, W, H - 122, PAVE, seed=21, row0=9, row1=16, leaves=0.0, moss=0.10,
               leaf_clusters=[(20, 140, 70, 160), (610, 135, 60, 120), (150, 300, 60, 40), (520, 250, 50, 30), (330, 200, 90, 30)])
    bg.rect(0, 122, W, 2, C("#0d0b16", 0.45))
    # Inlaid compass ring in front of the steps.
    for (rx, ry, col) in [(44, 13, "#8a7a74"), (42, 12, PAVE[2]), (30, 8, "#8a7a74"), (28, 7, PAVE[4])]:
        bg.ellipse(320 - rx, 190 - ry, rx * 2, ry * 2, col)
    for (dx, dy) in [(0, -7), (0, 7), (-27, 0), (27, 0)]:
        bg.poly([(320, 190), (320 + dx + (2 if dy else 0), 190 + dy + (1 if dx else 0)), (320 + dx * 1.0, 190 + dy * 1.0), (320 + dx - (2 if dy else 0), 190 + dy - (1 if dx else 0))], "#b39a82")
    bg.ellipse(316, 188, 8, 4, "#c9b093")
    # Planting strip along the bottom edge.
    bg.rect(0, 330, W, 30, "#22302b")
    bg.rect(0, 328, W, 3, WALL[4]); bg.hline(0, 328, W, WALL[5]); bg.hline(0, 331, W, WALL[1])
    for x in range(-4, W, 13):
        w = int(rng.integers(14, 24)); h = int(rng.integers(10, 16))
        bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.4 else None), x, 333 + int(rng.integers(0, 6)))
    for x in range(6, W, 37):
        grass_tuft(bg, x, 333, 6, seed=x)

    # The UMC at character scale: wings, a taller entrance pavilion, the doors open.
    umc_facade(bg, 150, 490, 124, 266, 374, 142)
    steps(bg, 320, 142, 52, 4, rise=4, spread=5)
    occluders = []

    # Trees framing the terrace.
    oak = sprite_from_cell(5, height=126, colors=40)
    pine = sprite_from_cell(6, height=136, colors=32)
    bg.paste(pine, W - pine.shape[1] + 34, 125 - pine.shape[0])
    bg.paste(oak, -58, 125 - oak.shape[0])

    # Warm light on the paving: two lamps and the open doors.
    for lx in (266, 376):
        light_pool(bg, lx, 184, 44, 13, strength=0.22)
    light_pool(bg, 320, 162, 46, 10, strength=0.2)

    bg.save(os.path.join(out, "background.png"))

    props = {}
    painters = {2: planter_box, 3: custodian_cart, 4: bike_workbench, 5: park_bench, 6: lamp_post, 7: lamp_post}
    for index, painter in painters.items():
        sprite, ax, ay = painter()
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        props[str(index)] = {"texture": f"res://assets/art/rooms/U02/{name}", "anchor": [ax, ay]}

    manifest = {
        "background": "res://assets/art/rooms/U02/background.png",
        "occluders": occluders,
        "props": props,
        "label_only": [0],
        "fauna": [
            {"kind": "squirrel", "x": 180, "y": 273, "range": 3, "speed": 0.25, "rate": 1.2},
            {"kind": "pigeon", "x": 252, "y": 266, "range": 14, "speed": 0.32, "rate": 2.0},
            {"kind": "pigeon", "x": 284, "y": 279, "range": 10, "speed": 0.27, "rate": 1.6, "flip": True},
            {"kind": "rabbit", "x": 458, "y": 133, "range": 0, "speed": 0.0, "rate": 0.7},
            {"kind": "bird", "x": 60, "y": 38, "fly": 9.0, "rate": 4.0},
            {"kind": "bird", "x": 220, "y": 52, "fly": 7.0, "rate": 3.5},
        ],
        "leaves": [[40, 30, 90, 70], [560, 20, 80, 80]],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
