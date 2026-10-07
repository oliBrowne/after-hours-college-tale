"""Club room (U04): back wall with stage curtains and string lights, plank floor, chairs, mixer table."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from props import shrub, MUM
from interior import (plaster, crown, wainscot, night_window, curtain, valance, string_lights, poster, corkboard,
                      wall_clock, plank_floor, rug, folding_chairs, folding_table, pa_speaker, stage_front,
                      stage_steps, floor_lamp, service_door, PANEL, FLOOR, VELVET)

ROOM = "U04"


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    W, H = 800, 480
    wall_base = 128
    bg = Canvas(W, H, fill="#171a2b", seed=6)

    # Back wall.
    plaster(bg, 0, 6, W, wall_base - 6, seed=1)
    crown(bg, 0, 0, W)
    wainscot(bg, 0, wall_base - 26, W, 26)
    night_window(bg, 26, 30, 40, 52, seed=2)
    corkboard(bg, 82, 34, 54, 40, seed=3)
    wall_clock(bg, 112, 20)
    poster(bg, 760, 34, 26, 34, "#5c897c", seed=4)
    poster(bg, 650, 30, 34, 44, "#e6d6b1", title="OPEN", seed=5)
    door, dax, day = service_door()
    bg.paste(door, 722 - dax, 177 - day)

    # Stage: curtains, valance, banner, lights, then the deck.
    stage_x0, stage_x1 = 147, 633
    # painted backdrop cloth: night sky over the Flatirons, the club's namesake last light on the ridge
    bg.dither_v(stage_x0, 6, stage_x1 - stage_x0, wall_base - 6, "#17142c", "#3a2a52", steps=5)
    srng = np.random.default_rng(12)
    for _ in range(70):
        sx = int(srng.integers(stage_x0 + 50, stage_x1 - 50)); sy = int(srng.integers(24, 90))
        bg.px(sx, sy, "#c8c0e0" if srng.random() < 0.6 else "#f2d27a")
    bg.ellipse(520, 34, 14, 14, "#efe2b8"); bg.ellipse(525, 32, 13, 13, "#1d1834")
    ridge = []
    for i, x in enumerate(range(stage_x0, stage_x1 + 1, 4)):
        ridge.append((x, 104 - 10 * np.sin(i * 0.31) - 6 * np.sin(i * 0.9) - (14 if 300 < x < 420 else 0) * np.sin((x - 300) / 120 * np.pi)))
    bg.poly(ridge + [(stage_x1, wall_base), (stage_x0, wall_base)], "#241a34")
    for k, sx in enumerate(range(318, 410, 22)):
        bg.poly([(sx, 104), (sx + 12, 80 - (k % 2) * 6), (sx + 20, 104)], "#3a2840")
        bg.line(sx + 2, 103, sx + 12, 82 - (k % 2) * 6, "#5a3a4a")
    bg.px(392, 74, "#f6cd78"); bg.rect(391, 75, 3, 2, "#e9a84a")
    for yy in range(6, wall_base, 4):
        bg.hline(stage_x0, yy, stage_x1 - stage_x0, C("#0d0b16", 0.12))
    curtain(bg, stage_x0, 6, 52, wall_base - 4, flip=False, seed=1)
    curtain(bg, stage_x1 - 52, 6, 52, wall_base - 4, flip=True, seed=2)
    valance(bg, stage_x0 - 2, 6, stage_x1 - stage_x0 + 4)
    # cloth banner with the club's name
    bx0, bx1, by = 300, 480, 40
    bg.rect(bx0, by, bx1 - bx0, 18, "#e6d6b1"); bg.hline(bx0, by, bx1 - bx0, "#fff3d6"); bg.hline(bx0, by + 17, bx1 - bx0, "#b8a888")
    for sx in range(bx0, bx1, 30):
        bg.poly([(sx, by + 18), (sx + 15, by + 22), (sx + 30, by + 18)], "#d4c4a0")
    label = "LAST LIGHT"
    text(bg, label, (bx0 + bx1) // 2 - text_width(label) // 2, by + 3, "#7e3a30")
    bg.line(bx0, by, bx0 - 10, 18, "#3a2a2a"); bg.line(bx1 - 1, by, bx1 + 9, 18, "#3a2a2a")
    string_lights(bg, stage_x0 + 50, 20, stage_x1 - 50, 20, sag=22, every=8, seed=1)
    string_lights(bg, stage_x0 + 50, 26, stage_x1 - 50, 26, sag=36, every=9, seed=2)
    # deck
    deck_top, deck_front = wall_base - 4, 188
    for yy in range(deck_top, deck_front):
        row = (yy - deck_top) // 6
        tone = PANEL[4] if row % 2 else PANEL[3]
        bg.hline(stage_x0, yy, stage_x1 - stage_x0, tone)
        if (yy - deck_top) % 6 == 5:
            bg.hline(stage_x0, yy, stage_x1 - stage_x0, PANEL[2])
    rng = np.random.default_rng(9)
    for _ in range(140):
        x = int(rng.integers(stage_x0, stage_x1)); y = int(rng.integers(deck_top, deck_front))
        bg.hline(x, y, int(rng.integers(3, 9)), PANEL[2])
    # tape marks, a mic stand and a stool on the deck
    for tx in (260, 390, 520):
        bg.rect(tx - 4, 168, 9, 2, "#e8b45c")
    bg.vline(392, 132, 34, "#16141f"); bg.rect(388, 165, 9, 2, "#16141f"); bg.rect(390, 128, 5, 5, "#4d4b66"); bg.px(391, 129, "#8a88a8")
    bg.rect(470, 150, 12, 3, "#4a2b24"); bg.vline(471, 153, 14, "#2c1a1a"); bg.vline(480, 153, 14, "#2c1a1a")
    light_pool(bg, 392, 160, 80, 22, strength=0.26)

    # Floor and rug.
    plank_floor(bg, 0, deck_front, W, H - deck_front, seed=3)
    plank_floor(bg, 0, wall_base, stage_x0, deck_front - wall_base, seed=4)
    plank_floor(bg, stage_x1, wall_base, W - stage_x1, deck_front - wall_base, seed=5)
    bg.rect(0, wall_base, stage_x0, 2, C("#0d0b16", 0.5)); bg.rect(stage_x1, wall_base, W - stage_x1, 2, C("#0d0b16", 0.5))
    bg.paste(door, 722 - dax, 177 - day)  # repaint the landing over the floor
    rug(bg, 326, 282, 244, 128)
    # a potted fig by the window and a small amp at stage left
    pot = shrub(0, 0, 22, 26, seed=31)
    bg.paste(pot, 33, wall_base - 26)
    bg.rect(36, wall_base - 4, 18, 10, "#16141f"); bg.rect(37, wall_base - 3, 16, 8, "#7e3a30"); bg.hline(37, wall_base - 3, 16, "#9a4a39")
    bg.rect(204, 150, 22, 18, "#16141f"); bg.rect(205, 151, 20, 16, "#2c2a3a"); bg.rect(207, 154, 16, 9, "#1b1824")
    for gx in range(208, 222, 2):
        bg.vline(gx, 155, 7, "#34324a")
    bg.rect(206, 151, 18, 2, "#c0884a")
    light_pool(bg, 590, 388, 50, 16, strength=0.22)
    # dark margins outside the walkable room
    for x0, w in [(0, 14), (W - 14, 14)]:
        bg.rect(x0, wall_base, w, H - wall_base, C("#0d0b16", 0.35))
    bg.rect(0, H - 18, W, 18, C("#0d0b16", 0.45))
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(2, stage_front())
    save(3, stage_steps())
    with_mixer = folding_table(112, 48, mixer=True, top_height=24, seed=1)
    with_mixer[0].save(os.path.join(out, "prop-4-mixer.png"))
    save(4, folding_table(112, 48, mixer=False, top_height=24, seed=1), {"flag": "mixer_returned", "flag_texture": f"res://assets/art/rooms/{ROOM}/prop-4-mixer.png"})
    save(5, folding_table(62, 35, items=False, top_height=25, seed=2))
    for i, index in enumerate([6, 7, 8, 9]):
        save(index, folding_chairs(seed=i))
    save(10, floor_lamp())
    save(11, pa_speaker())

    manifest = {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [1],
        "fauna": [],
        "leaves": [],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
