"""Broadway (U01): storefronts across the street, the bus lane, the shelter and Mara's mural."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade
from sky import panorama
from surfaces import sidewalk, asphalt, light_pool, LEAVES
from facade import storefront, TRIM, FRAME, brick_wall
from props import (lamp_post, park_bench, planter_box, bus_shelter, timetable, mural_board, bicycle, bollard_lamp,
                   atlas_tree, shrub, MUM)

ROOM = "U01"


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    W, H = 640, 360
    base = 148
    bg = Canvas(W, H, fill="#171a2b", seed=8)
    sky, _ = panorama(W, 150, scale=2.2)
    bg.a[:150] = sky

    # Street running off toward the mountains on the left, the bus lane.
    asphalt(bg, 0, 120, 68, H - 120, seed=1)
    for y in range(124, H, 18):
        bg.rect(33, y, 2, 9, "#c8a04a")
    bg.rect(66, 120, 4, H - 120, "#9a9aa4"); bg.vline(66, 120, H - 120, "#b8b8c2"); bg.vline(69, 120, H - 120, "#4f4a54")
    bg.rect(0, 118, 70, 3, C("#0d0b16", 0.5))

    # Storefronts across Broadway.
    storefront(bg, 72, 128, base, 30, wall="brick", sign="BOOKS", goods="books", lit=True, seed=1, upper_lit=(True, False, True))
    storefront(bg, 204, 136, base, 46, wall="stucco", sign="CAFE", goods="cafe", lit=True, awn=("#2c4a4c", "#e6d6b1"), seed=2, upper_lit=(False, True))
    # alley between buildings
    bg.rect(340, 70, 32, base - 70, "#1c1724")
    for y in range(74, base, 6):
        bg.hline(340, y, 32, "#221c2a")
    bg.rect(344, base - 22, 20, 18, "#2c4a4c"); bg.hline(344, base - 22, 20, "#3e6663"); bg.rect(346, base - 4, 3, 4, FRAME); bg.rect(359, base - 4, 3, 4, FRAME)
    storefront(bg, 372, 150, base, 24, wall="brick", sign="RECORDS", goods="records", lit=False, seed=3, upper_lit=(True, True, False))
    storefront(bg, 524, 116, base, 40, wall="stucco", sign="PIZZA", goods="cafe", lit=True, awn=("#9e4e52", "#e6d6b1"), seed=4, upper_lit=(True,))
    bg.rect(70, base, W - 70, 2, C("#0d0b16", 0.5))

    # Sidewalk.
    sidewalk(bg, 70, base + 2, W - 70, H - base - 2, seed=5)
    rng = np.random.default_rng(6)
    for (cx, cy, r, n) in [(590, 200, 60, 90), (300, 320, 80, 30), (120, 300, 50, 20)]:
        for _ in range(n):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
            lx, ly = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.5)
            if 70 <= lx < W and base < ly < H:
                c = LEAVES[int(rng.integers(len(LEAVES)))]
                bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
    # tree pit for the street tree
    bg.rect(570, 166, 40, 10, "#2a2026"); bg.rect(571, 167, 38, 8, "#3a2a26")
    for lx in (150, 184):
        light_pool(bg, lx, 252 if lx == 150 else 271, 46, 13, strength=0.22)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        props[str(index)] = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}

    save(0, bus_shelter())
    save(1, timetable())
    save(2, planter_box(112, 36, seed=11))
    save(3, mural_board())
    save(4, bicycle())
    save(5, park_bench(92, 34))
    save(7, lamp_post(66))
    save(8, atlas_tree(110, cell=5))
    save(9, bollard_lamp(32))

    manifest = {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "fauna": [
            {"kind": "pigeon", "x": 120, "y": 304, "range": 15, "speed": 0.35, "rate": 2.0},
            {"kind": "pigeon", "x": 156, "y": 318, "range": 10, "speed": 0.29, "rate": 1.5, "flip": True},
            {"kind": "squirrel", "x": 540, "y": 336, "range": 18, "speed": 0.22, "rate": 1.4},
            {"kind": "bird", "x": 100, "y": 22, "fly": 8.0, "rate": 4.0},
        ],
        "leaves": [[560, 70, 60, 100]],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
