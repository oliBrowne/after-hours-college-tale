"""Norlin steps (N01): the quad at night in front of Norlin Library's columned west front.

Top of the room: the library at character scale (tile roof edge, carved frieze, six Ionic columns,
lit windows, bronze doors), its broad steps running down onto a sandstone plaza. Left: a garden
wall with the iron gate of the UMC service passage. Right: a lamp-lit path toward Old Main, whose
tower shows over the trees. Below: the quad lawn, an oval court around the big planter with the
STOP HERE notice, the lower walk that leads out to Farrand (left) and Engineering (right), and the
garden path leaving on the right."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from midlib import sprite_from_cell
from pixel import Canvas, C, shade, mix, text, text_width
from surfaces import light_pool, LEAVES
from props import shrub, grass_tuft, atlas_tree, MUM, LEAF, OUT, IRON
from lib_norlin import (norlin_portico, stone_steps, plinth_lamp, lawn, flag_path, stone_planter, quad_bench,
                        quiet_lamp_post, notice_stand, loose_page, iron_gate, stone_wall, plaque, NIGHT_N, STONE_N,
                        paving, crazy_paving, book_medallion, kerb, tree_pit, iron_arch, book_drop, chalk, PAVE_N, PAVE_RED,
                        LIME, PAGE, GRASS)

ROOM = "N01"
NIGHT_CLOUD = ["#2c2648", "#3a3058", "#463864", "#52406c", "#6a4c76", "#8e5e80", "#b47486"]
W, H = 960, 540
BASE = 142                 # floor row of the library (top of the walkable area)
CX = 510                   # library centre line = the checkout door
INSCRIPTION = "WHO KNOWS ONLY HIS OWN GENERATION REMAINS ALWAYS A CHILD"
WALK = (20, 142, 920, 374)
LOWER_WALK = (450, 484)    # the walk along the bottom that leads to Farrand and Engineering
COURT = (410, 344, 150, 64)  # oval court around the planter: centre x, y, radius x, y
LAMP = (170, 399)          # the quiet lamp (save point)


def sky(bg):
    """Eastern night sky over the campus: stepped indigo bands, stars, a few lit clouds, the moon."""
    bands = ["#141432", "#1b1a3e", "#232149", "#2e2853", "#3b2f5c", "#4c3762", "#5e3f66"]
    for y in range(0, 128):
        t = y / 127
        i = min(len(bands) - 1, int(t ** 0.9 * len(bands)))
        bg.hline(0, y, W, bands[i])
    rng = np.random.default_rng(3)
    for _ in range(140):
        sx, sy = int(rng.integers(0, W)), int(rng.integers(0, 96))
        bg.px(sx, sy, "#c8c0e0" if rng.random() < 0.65 else "#f2d27a")
    # moon with stepped halo
    mx, my = 116, 36
    for r, a in [(22, 0.05), (16, 0.08), (11, 0.1)]:
        bg.ellipse(mx - r, my - r, r * 2 + 1, r * 2 + 1, C("#efe2b8", a))
    bg.ellipse(mx - 8, my - 8, 17, 17, "#efe2b8"); bg.ellipse(mx - 6, my - 7, 9, 7, "#fff4d2")
    for (cx, cy) in [(mx - 3, my + 2), (mx + 3, my - 3), (mx + 1, my + 4)]:
        bg.px(cx, cy, "#d8c8a0")
    # a few night clouds, their undersides still catching the sunset behind the viewer
    from clouds import _cloud
    crng = np.random.default_rng(4)
    for (cx, cy, length, thick) in [(14, 52, 96, 3), (176, 70, 70, 2), (780, 44, 120, 3), (884, 76, 70, 2), (216, 22, 50, 2)]:
        cl = _cloud(length, thick, crng, NIGHT_CLOUD)
        bg.paste(cl, cx, cy - cl.shape[0])


def far_campus(bg):
    """Distant trees and roofs along the horizon on both sides of the library; Old Main's tower."""
    rng = np.random.default_rng(5)
    # far tree crowns
    for x in range(-10, W + 10, 11):
        h = int(rng.integers(14, 30))
        bg.ellipse(x, 118 - h, int(rng.integers(16, 26)), h * 2, "#1d1b33")
    # Old Main over the trees on the right, toward the Old Main path
    om = sprite_from_cell(3, height=78, colors=28, brightness=0.62, saturation=0.8)
    bg.paste(om, 892 - om.shape[1] // 2, 124 - om.shape[0])
    # a low roofline on the left with a few lit windows (the UMC side of campus)
    for (x0, w, h) in [(0, 70, 22), (66, 58, 16), (196, 50, 18)]:
        bg.rect(x0, 118 - h, w, h, "#201c34")
        bg.poly([(x0 - 3, 118 - h), (x0 + w // 2, 112 - h), (x0 + w + 3, 118 - h)], "#201c34")
        for wx in range(x0 + 5, x0 + w - 4, 7):
            if rng.random() < 0.45:
                bg.rect(wx, 118 - h + 6, 2, 3, "#c98a46")
    # nearer crowns
    for x in list(range(-6, 270, 9)) + list(range(750, W + 6, 9)):
        h = int(rng.integers(8, 16))
        bg.ellipse(x, 126 - h, int(rng.integers(12, 18)), h * 2, "#182224")
        if rng.random() < 0.3:
            bg.px(x + 5, 126 - h + 2, "#24302e")


def service_gate(bg):
    """Left of the library: a sandstone garden wall with shrubs on top and the open iron gate of
    the UMC service passage, a path disappearing into the dark behind it."""
    wall_top = 112
    stone_wall(bg, 0, wall_top, 266, BASE - wall_top, pal=[shade(c, -0.18) for c in STONE_N], seed=8, course=5)
    bg.rect(0, wall_top - 3, 266, 4, LIME[2]); bg.hline(0, wall_top - 3, 266, LIME[4])
    rng = np.random.default_rng(9)
    for x in range(-4, 266, 15):
        if 44 < x < 112:
            continue
        w, h = int(rng.integers(18, 26)), int(rng.integers(10, 16))
        bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.2 else None), x, wall_top - h + 1)
    # the opening: path receding between dark hedges, a small lamp far away
    gx0, gx1 = 58, 104
    bg.rect(gx0, wall_top - 6, gx1 - gx0, BASE - wall_top + 6, "#141826")
    bg.poly([(gx0 + 4, BASE), (gx1 - 4, BASE), (gx1 - 16, wall_top + 2), (gx0 + 16, wall_top + 2)], "#4a3a3c")
    for k, y in enumerate(range(wall_top + 4, BASE, 5)):
        t = (y - wall_top) / (BASE - wall_top)
        half = int(8 + 15 * t)
        bg.hline(81 - half, y, half * 2, "#5a4644" if k % 2 else "#54403e")
    for side in (-1, 1):
        for y in range(wall_top - 4, BASE, 3):
            t = (y - wall_top) / (BASE - wall_top)
            x = 81 + side * int(9 + 15 * t)
            bg.rect(x if side > 0 else x - 6, y, 6, 3, "#1a2622")
    bg.vline(81, wall_top - 2, 8, IRON[2]); bg.rect(79, wall_top - 7, 5, 5, "#e9a84a"); bg.px(81, wall_top - 6, "#fff0c4")
    iron_gate(bg, gx0, BASE, gx1 - gx0, 36, open_frac=0.7)
    iron_arch(bg, (gx0 + gx1) // 2, BASE - 52, (gx1 - gx0) // 2 + 4, "SERVICE")


def oldmain_path(bg, x0):
    """Right of the library: the wall continues to the edge with a gateway (piers, iron arch and
    sign) where the path to Old Main leaves between dark hedges; Old Main's tower rises beyond."""
    wall_top = 112
    rng = np.random.default_rng(11)
    gx0, gx1 = 768, 812
    stone_wall(bg, x0, wall_top, W - x0, BASE - wall_top, pal=[shade(c, -0.18) for c in STONE_N], seed=12, course=5)
    bg.rect(x0, wall_top - 3, W - x0, 4, LIME[2]); bg.hline(x0, wall_top - 3, W - x0, LIME[4])
    for x in range(x0 - 2, W, 15):
        if gx0 - 14 < x < gx1 + 4:
            continue
        w, h = int(rng.integers(18, 26)), int(rng.integers(10, 16))
        bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.25 else None), x, wall_top - h + 1)
    # the opening: a path receding between hedges, two small lamps along it
    mid = (gx0 + gx1) // 2
    bg.rect(gx0, wall_top - 6, gx1 - gx0, BASE - wall_top + 6, "#141826")
    for k, y in enumerate(range(wall_top - 2, BASE)):
        t = (y - wall_top + 2) / (BASE - wall_top + 2)
        half = int(6 + 16 * t)
        bg.hline(mid - half, y, half * 2, "#5a4644" if (y // 4) % 2 else "#54403e")
    for side in (-1, 1):
        for y in range(wall_top - 6, BASE, 3):
            t = (y - wall_top + 6) / (BASE - wall_top + 6)
            x = mid + side * int(7 + 16 * t)
            bg.rect(x if side > 0 else x - 6, y, 6, 3, "#1a2622")
    for (lx, ly, h) in [(mid - 9, wall_top + 8, 14), (mid + 6, wall_top - 2, 9)]:
        bg.vline(lx, ly - h, h, IRON[2]); bg.rect(lx - 1, ly - h - 3, 3, 3, "#e9a84a")
    iron_gate(bg, gx0, BASE, gx1 - gx0, 36, open_frac=0.75)
    iron_arch(bg, mid, BASE - 52, (gx1 - gx0) // 2 + 4, "OLD MAIN")


def ground_masks():
    ys, xs = np.mgrid[0:H, 0:W]
    plaza = (ys >= BASE) & (ys < 250 + 6 * np.sin(xs / 70.0))
    cx, cy, rx, ry = COURT
    court = ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1
    court |= (xs >= cx - 28) & (xs < cx + 28) & (ys >= 240) & (ys < cy)
    court |= (xs >= cx - 22) & (xs < cx + 22) & (ys >= cy) & (ys < LOWER_WALK[0] + 2)
    lower = (ys >= LOWER_WALK[0] + 3 * np.sin(xs / 90.0)) & (ys < LOWER_WALK[1] + 3 * np.sin(xs / 90.0))
    # diagonal on the left: plaza to the lower walk, passing the quiet lamp on its right
    def band(a, b, half):
        (ax, ay), (bx, by) = a, b
        t = np.clip(((xs - ax) * (bx - ax) + (ys - ay) * (by - ay)) / ((bx - ax) ** 2 + (by - ay) ** 2), 0, 1)
        d = np.hypot(xs - (ax + t * (bx - ax)), ys - (ay + t * (by - ay)))
        return d <= half
    left = band((232, 246), (92, 458), 13)
    garden = band((852, 246), (880, 344), 14) | band((880, 350), (W + 10, 350), 14)
    bench_pad = (xs >= 538) & (xs < 702) & (ys >= 420) & (ys < LOWER_WALK[0] + 4)
    paths = plaza | court | lower | left | garden | bench_pad
    return paths, plaza


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    bg = Canvas(W, H, fill="#171a2b", seed=1)

    # Sky and distant campus behind everything.
    sky(bg)
    far_campus(bg)
    service_gate(bg)
    oldmain_path(bg, 754)

    # The library's west front, then plinth lamps at the head of the steps.
    info = norlin_portico(bg, CX, BASE, inscription=INSCRIPTION, seed=4)
    lamp_heads = []
    for px_ in (318, 702):
        lamp_heads.append(plinth_lamp(bg, px_, BASE + 1, plinth_w=16, plinth_h=22, post=20))

    # Ground: lawn everywhere, then the paved plaza, court and walks.
    lawn(bg, 0, BASE, W, H - BASE, seed=21)
    paths, plaza = ground_masks()
    crazy_paving(bg, paths, PAVE_N, seed=22)
    # the library's seal inlaid at the foot of the steps; a red band ringing the court
    book_medallion(bg, CX, 222, 40)
    ys, xs = np.mgrid[0:H, 0:W]
    cx_, cy_, rx_, ry_ = COURT
    ring = np.abs(np.hypot((xs - cx_) / rx_, (ys - cy_) / ry_) - 0.9) < 0.022
    bg.a[ring & paths] = C(PAVE_RED[4])
    kerb(bg, paths)
    for (tx, ty) in [(160, 262), (815, 287)]:
        tree_pit(bg, tx, ty - 2, 22, 7)
    # the broad steps down from the colonnade (painted flat: people walk on them)
    stone_steps(bg, CX, BASE, info["columns"][-1] - info["columns"][0] + 44, 8, rise=6, spread=3, seed=23)
    # a book-return drop against the library's left end wall
    book_drop(bg, 280, BASE + 1)
    # plinth lamps repainted over the top step so they stand beside it
    for px_ in (318, 702):
        plinth_lamp(bg, px_, BASE + 1, plinth_w=16, plinth_h=22, post=20)

    # Edges: hedges in the margins with gaps where the paths leave, a planted strip at the bottom.
    rng = np.random.default_rng(31)
    from surfaces import ashlar_wall
    bg.rect(0, 516, W, 24, "#1a2420")
    ashlar_wall(bg, 0, 514, W, 5, [shade(c, -0.1) for c in STONE_N[:6]], seed=33)
    for x in range(-6, W, 14):
        w, h = int(rng.integers(16, 24)), int(rng.integers(10, 15))
        bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None), x, 520 + int(rng.integers(0, 6)))
    gaps_left = [(LOWER_WALK[0] - 4, LOWER_WALK[1] + 4)]
    gaps_right = [(332, 368), (LOWER_WALK[0] - 4, LOWER_WALK[1] + 4)]
    for (x0, gaps) in ((0, gaps_left), (W - 20, gaps_right)):
        for y in range(BASE + 100, 514, 11):
            if any(a - 8 <= y <= b for a, b in gaps):
                continue
            w, h = int(rng.integers(18, 24)), int(rng.integers(12, 16))
            bg.paste(shrub(0, 0, w, h, seed=int(rng.integers(1e6))), x0 - 4 + int(rng.integers(0, 6)), y - h)

    # Leaf litter under the two trees and drifted along the steps.
    for (cx, cy, r, n) in [(160, 262, 70, 160), (815, 288, 76, 170), (300, 200, 60, 30), (720, 205, 60, 30), (470, 470, 120, 30)]:
        for _ in range(n):
            a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, r / 2))
            lx, ly = int(cx + np.cos(a) * d), int(cy + np.sin(a) * d * 0.45)
            if BASE + 2 <= ly < 514 and 0 <= lx < W - 1:
                c = LEAVES[int(rng.integers(len(LEAVES)))]
                bg.px(lx, ly, c); bg.px(lx + 1, ly, shade(c, -0.2))
                if rng.random() < 0.3:
                    bg.px(lx, ly - 1, shade(c, 0.15))
    # Chalk on the lower walk (exam week encouragement), a few flowers in the lawn.
    chalk(bg, 214, 462, "YOU GOT THIS", "#e8b4c8")
    for (sx, sy) in [(296, 466), (302, 470)]:
        bg.px(sx, sy, C("#a8d0e8", 0.8))
    for k in range(5):
        a = k / 5 * 2 * np.pi
        bg.line(300, 468, int(300 + np.cos(a) * 4), int(468 + np.sin(a) * 2), C("#a8d0e8", 0.75))
    frng = np.random.default_rng(55)
    lawn_free = ~paths
    for _ in range(26):
        fx, fy = int(frng.integers(30, 930)), int(frng.integers(262, 506))
        if not lawn_free[fy, fx]:
            continue
        for _ in range(int(frng.integers(3, 7))):
            px_, py_ = fx + int(frng.integers(-4, 5)), fy + int(frng.integers(-2, 3))
            if lawn_free[py_, px_]:
                bg.px(px_, py_, "#e6dcc0" if frng.random() < 0.7 else "#e0b440")
    # Loose pages: on the steps, the plaza, one by the notice ("the page before the door").
    for i, (px_, py_) in enumerate([(452, 168), (586, 157), (382, 214), (626, 232), (300, 392), (742, 300)]):
        loose_page(bg, px_, py_, seed=i)

    # Light on the ground: the doors, lanterns and plinth lamps, the quiet lamp.
    light_pool(bg, CX, BASE + 10, 54, 12, strength=0.24)
    for (lx, _) in info["lanterns"]:
        light_pool(bg, lx, BASE + 8, 30, 8, strength=0.16)
    for (lx, _) in lamp_heads:
        light_pool(bg, lx, BASE + 14, 36, 10, strength=0.2)
    light_pool(bg, LAMP[0], LAMP[1] + 3, 46, 13, strength=0.24)

    # Dark margins outside the walkable quad.
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.3))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.3))
    bg.rect(0, WALK[1] + WALK[3], W, H - WALK[1] - WALK[3], C("#0d0b16", 0.38))
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": f"res://assets/art/rooms/{ROOM}/{name}", "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    def stop_here_sheet(cv, x, y, w, h):
        # a page with a red ribbon bookmark laid across it where someone stopped reading
        for ly in range(y + 3, y + h - 2, 3):
            cv.hline(x + 3, ly, w - 8 - (ly % 7), PAGE[0])
        cv.rect(x + w // 2 + 4, y - 2, 4, h + 4, "#a83c32"); cv.vline(x + w // 2 + 4, y - 2, h + 4, "#c8584a")
        cv.poly([(x + w // 2 + 4, y + h + 2), (x + w // 2 + 8, y + h + 2), (x + w // 2 + 6, y + h - 1)], PAGE[3])
        cv.rect(x + 3, y + h // 2 - 1, w // 2 - 2, 2, "#425da6")

    save(0, stone_planter(180, 65, seed=41))
    save(1, quad_bench(150, 32, seed=42))
    save(2, atlas_tree(138, cell=5, seed=43))
    tree_r = atlas_tree(150, cell=5, seed=44)
    tree_r[0].a = tree_r[0].a[:, ::-1].copy()
    save(3, (tree_r[0], tree_r[0].w - 1 - tree_r[1], tree_r[2]))
    save(4, quiet_lamp_post(68))
    save(5, notice_stand(66, 48, "STOP HERE", seed=45, body=stop_here_sheet))

    head = LAMP[1] - 68 + 5
    stars = []
    srng = np.random.default_rng(7)
    for _ in range(18):
        sx, sy = int(srng.integers(0, W)), int(srng.integers(4, 90))
        if 262 < sx < 758:
            continue
        stars.append([sx, sy, "c8c0e0", 0])
    glows = [[lx, ly, "fff0c4", 1] for (lx, ly) in info["lanterns"]]
    glows += [[lx, ly, "fff0c4", 1] for (lx, ly) in lamp_heads]
    glows += [[LAMP[0], head, "fff0c4", 2], [81, 106, "fff0c4", 1], [CX, BASE - 50, "fde9b6", 1]]
    manifest = {
        "background": f"res://assets/art/rooms/{ROOM}/background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "fauna": [
            {"kind": "rabbit", "x": 112, "y": 318, "range": 0, "speed": 0.0, "rate": 0.6},
            {"kind": "rabbit", "x": 712, "y": 372, "range": 6, "speed": 0.2, "rate": 0.8, "flip": True},
            {"kind": "squirrel", "x": 236, "y": 268, "range": 4, "speed": 0.3, "rate": 1.2},
            {"kind": "barn_owl", "x": 292, "y": 16, "range": 0, "speed": 0.0, "rate": 1.5},
            {"kind": "lamp_moth", "x": LAMP[0] + 2, "y": head - 6, "range": 7, "speed": 2.3, "rate": 9.0},
            {"kind": "night_bat", "x": 120, "y": 54, "fly": 14.0, "rate": 7.0},
            {"kind": "night_bat", "x": 600, "y": 82, "fly": 11.0, "rate": 6.0},
            {"kind": "loose_page", "x": 300, "y": 300, "fly": 6.0, "rate": 3.0},
        ],
        "leaves": [[112, 170, 96, 90], [764, 190, 104, 96]],
        "layers": [
            {"kind": "twinkle", "points": glows, "rate": 1.6, "min": 0.5},
            {"kind": "twinkle", "points": stars, "rate": 0.9, "min": 0.0},
        ],
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
