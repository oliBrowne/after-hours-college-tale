"""Battle backdrop for the margin garden (N05): out on the lawn of Norlin's roof garden, facing the
balustrade and the whole night beyond it.

The mown lawn runs out to a strip of pea gravel at the foot of the sandstone balustrade, its
mowing stripes converging on the view; urns on the piers, a festoon of warm bulbs swagged from
urn to urn, and a longer one slung overhead between the two tub trees that frame the picture.
Beyond the coping: the Flatirons and the dark bulk of Green Mountain under the moon on the left,
the campus roofs with a few lit windows and Macky's towers on the right. In the middle of the
lawn the little lantern stands by a line of stepping stones; under the enemy a circle of raked
gravel has been left empty on purpose, ringed with kerb stones. The bird feeder stands at the
right with pigeons pecking below it. Clouds drift behind the mountains, birds cross the sky,
the bulbs and the lantern breathe, leaves blow across."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, shade
from props import OUT, IRON, LEAF, MUM, shrub
from clouds import cloud_strip
from lib_norlin import quiet_lamp_post, STONE_N, LIME, GRASS
from lib_norlin2 import (night_sky, moon, flatirons_night, campus_roofs, auditorium, balustrade, stone_urn, festoon,
                         tub_tree, feeder_bed, GRAVEL, NIGHT_CLOUD)
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, ROOM_TO_BATTLE

ROOM = "N05"
INK = "#10121e"
HAZE = "#2a2444"
Z_BAL = 620.0                 # the balustrade's foot
GRAVEL_Z = 572.0              # pea gravel from here to the balustrade
SKY_BASE = 108                # screen row the distant view stands on (hidden behind the coping)
BAL_TOP = 103                 # screen rows of the balustrade coping and plinth foot
PIERS = [22, 168, 314, 460, 606]
STRIPE = 46.0                 # mowing stripe width (world units)
CIRCLE = (173.0, 347.0, 64.0)  # the raked empty circle under the enemy: X, Z, radius
LANTERN = (48.0, 480.0)
STONES = [(30.0, 300.0), (16.0, 336.0), (34.0, 372.0), (20.0, 408.0), (40.0, 444.0)]
TREES = [(-420.0, 470.0, 1, None), (500.0, 500.0, 2, (1.08, 0.82, 0.78))]
FEEDER = (470.0, 590.0)
BAT_X = 168


def ground_shader(X, Z):
    """Mown lawn with stripes running out to the view, the gravel strip at the balustrade foot,
    stepping stones to the lantern, the raked empty circle, fallen leaves, lamp pools."""
    g = pal_array(GRASS)
    gr = pal_array(GRAVEL)
    stripe = (np.floor(X / STRIPE) % 2 == 0)
    t = hash2(np.floor(X / 3), np.floor(Z / 4), 3)
    rgb = np.where(stripe[:, None], g[3], g[2]).copy()
    rgb[t > 0.86] = g[4]
    rgb[t < 0.08] = g[1]
    blades = (hash2(np.floor(X / 2), np.floor(Z / 2), 5) > 0.93) & stripe
    rgb[blades] = g[5]
    # a darker hollow here and there
    hol = hash2(np.floor(X / 40), np.floor(Z / 26), 7) > 0.8
    rgb[hol] *= 0.9
    # the gravel strip along the balustrade
    grav = Z > GRAVEL_Z
    gt = hash2(np.floor(X / 2.5), np.floor(Z / 3), 11)
    rgb[grav] = gr[3]
    rgb[grav & (gt > 0.7)] = gr[5]
    rgb[grav & (gt < 0.2)] = gr[1]
    rgb[np.abs(Z - GRAVEL_Z) < 2.0] = pal_array(LIME)[1]
    # stepping stones out to the lantern
    for (sx, sz) in STONES + [(LANTERN[0] - 8, LANTERN[1] - 22)]:
        d = np.hypot((X - sx) / 13.0, (Z - sz) / 9.0)
        st = d < 1
        rgb[st] = pal_array(STONE_N)[3]
        rgb[st & (Z > sz + 3)] = pal_array(STONE_N)[5]
        rgb[(d >= 1) & (d < 1.18) & (Z < sz)] = g[0]
    # the empty circle: raked pale gravel in rings, a kerb of stones
    cx, cz, r = CIRCLE
    d = np.hypot(X - cx, (Z - cz) * 1.0)
    inside = d < r
    rings = (np.floor(d / 6.0) % 2 == 0)
    rgb[inside] = pal_array(["#7c6a62"])[0]
    rgb[inside & rings] = pal_array(["#8e7c70"])[0]
    rgb[inside & (np.abs((d % 6.0) - 0.0) < 0.9)] = pal_array(["#5e504c"])[0]
    kerb = (d >= r) & (d < r + 5)
    rgb[kerb] = pal_array(LIME)[3]
    rgb[kerb & (np.floor(np.arctan2(Z - cz, X - cx) * 9) % 2 == 0)] = pal_array(LIME)[2]
    rgb[kerb & (Z > cz) & (d > r + 3)] = pal_array(LIME)[1]
    # fallen leaves under the trees and blown across the lawn
    lv = pal_array(["#c8682e", "#a83c32", "#d9a441", "#8c4a2a"])
    for (tx, tz, _, _) in TREES:
        near = np.hypot((X - tx) / 160.0, (Z - tz) / 90.0) < 1
        h = hash2(np.floor(X / 3), np.floor(Z / 3), 21)
        pick = near & (h > 0.9) & ~grav
        rgb[pick] = lv[(np.floor(h[pick] * 40) % 4).astype(int)]
    h = hash2(np.floor(X / 3), np.floor(Z / 3), 23)
    pick = (h > 0.985) & ~inside & ~grav
    rgb[pick] = lv[(np.floor(h[pick] * 400) % 4).astype(int)]
    # light: the lantern's pool, the bulbs along the balustrade, the moon
    warm_light(rgb, np.hypot(X - LANTERN[0], (Z - LANTERN[1]) * 1.6), 120, strength=0.38)
    warm_light(rgb, np.abs(Z - Z_BAL) * 2.4, 90, strength=0.22)
    warm_light(rgb, np.hypot(X - cx, (Z - cz) * 1.2), 110, colour="#c8c0e0", strength=0.12, bands=2)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 460, 900, amount=0.4)
    return out


def view_strip():
    """Everything beyond the coping, painted 1:1: the Flatirons and Green Mountain, the campus
    roofs and Macky's towers, tree crowns down where the quad lies."""
    cv = Canvas(640, 360)
    flatirons_night(cv, -30, 400, SKY_BASE, seed=5, tall=1.3)
    lights = campus_roofs(cv, 330, 664, SKY_BASE, seed=6, lit=0.5)
    auditorium(cv, 362, SKY_BASE)
    rng = np.random.default_rng(7)
    for x in range(-6, 650, 9):
        h = int(rng.integers(5, 11))
        cv.ellipse(x, SKY_BASE - 2 - h, int(rng.integers(12, 18)), h * 2, "#182224")
    lights += [(362 - 15, SKY_BASE - 32), (362 + 13, SKY_BASE - 32)]
    return cv, lights


def balustrade_strip():
    """The balustrade 1:1 across the frame with urns on alternate piers and shrubs at its foot."""
    cv = Canvas(640, 360)
    base = int(round(98 + 52 * 320 / Z_BAL))
    balustrade(cv, -4, 644, BAL_TOP, base, piers=PIERS, seed=2)
    urns = []
    for k, px_ in enumerate(PIERS):
        stone_urn(cv, px_, BAL_TOP - 7, seed=k + 3)
        urns.append((px_, BAL_TOP - 20))
    rng = np.random.default_rng(17)
    x = -6
    while x < 640:
        if any(abs(x + 8 - p) < 12 for p in PIERS) or 300 < x < 336:
            x += 6
            continue
        sw, sh = int(rng.integers(14, 22)), int(rng.integers(8, 13))
        fl = MUM if rng.random() < 0.3 else None
        cv.paste(shrub(0, 0, sw, sh, seed=int(rng.integers(1e6)), flowers=fl), x, base - sh + 2)
        x += sw + int(rng.integers(4, 22))
    return cv, base, urns


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    v = View(horizon=98, cam=52, fill="#141432")

    # the sky (open: clouds and birds pass in it), then the view and the balustrade as scenery
    sky = Canvas(640, 360)
    stars = night_sky(sky, 0, 0, 640, SKY_BASE, seed=3, stars=150, star_h=86)
    moon(sky, 286, 28, r=9)
    v.strip(sky.a, 0, solid=False)
    vs, lights = view_strip()
    v.strip(vs.a, 0)
    v.ground(ground_shader, z_max=Z_BAL)
    bal, bal_base, urns = balustrade_strip()
    v.strip(bal.a, 0)

    # far to near: feeder, lantern, the tub trees
    fd, fax, fay = feeder_bed(80, 55, seed=4)
    v.sprite(fd.a, FEEDER[0], FEEDER[1], anchor=(fax / fd.w, fay / fd.h), scale=ROOM_TO_BATTLE)
    lp, lax, lay = quiet_lamp_post(68)
    lsx, lsy, ls = v.sprite(lp.a, LANTERN[0], LANTERN[1], anchor=(lax / lp.w, lay / lp.h), scale=ROOM_TO_BATTLE)
    lamp_core = (int(round(lsx)), int(round(lsy - 57 * ls)))     # the lantern sits 57px above the post's foot
    tree_tops = []
    for (tx, tz, seed, tint) in sorted(TREES, key=lambda t: -t[1]):
        tr, tax, tay = tub_tree(110, seed=seed, tint=tint)
        sx, sy, s = v.sprite(tr.a, tx, tz, anchor=(tax / tr.w, tay / tr.h), scale=ROOM_TO_BATTLE)
        tree_tops.append((int(round(sx)), int(round(sy - 92 * s))))

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp: festoons swagged urn to urn along the balustrade, a long one overhead tree to tree
    before = cv.a.copy()
    bulbs = []
    for (a, b) in zip(urns, urns[1:]):
        bulbs += festoon(cv, a[0], a[1], b[0], b[1], sag=7, every=9, seed=a[0])
    (lx, ly), (rx, ry) = sorted(tree_tops)
    over = festoon(cv, lx + 14, ly + 6, rx - 10, ry + 8, sag=40, every=15, seed=99)
    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    strung = np.abs(cv.a - before).sum(axis=2) > 0.2           # cords and bulbs hang in front of the clouds
    near[..., 3] = (v.solid_mask() | strung).astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))

    clouds = cloud_strip(width=640, height=44, count=4, seed=8, pal=NIGHT_CLOUD, sizes=(50, 110))
    clouds.save(os.path.join(out, "battle-clouds.png"))

    res = f"res://assets/art/rooms/{ROOM}/"
    rng = np.random.default_rng(12)
    star_pts = [[int(x), int(y), "f2e6c0" if rng.random() < 0.3 else "c8c0e0", 1] for (x, y) in stars
                if rng.random() < 0.45 and not (392 <= x <= 628 and y <= 70)]
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "drift", "depth": "far", "texture": res + "battle-clouds.png", "y": 14, "speed": 3.0, "alpha": 0.8},
            {"kind": "twinkle", "depth": "far", "points": star_pts, "rate": 0.9, "min": 0.2},
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "bird", "x": 90, "y": 36, "fly": 12.0, "rate": 4.0},
                {"kind": "bird", "x": 106, "y": 44, "fly": 12.0, "rate": 3.6},
                {"kind": "bird", "x": 120, "y": 38, "fly": 12.0, "rate": 4.4},
                {"kind": "night_bat", "x": BAT_X, "y": 64, "fly": 14.0, "rate": 6.0}]},
            {"kind": "twinkle", "points": [[x, y, "f6cf7a", 1] for (x, y) in bulbs + over], "rate": 1.8, "min": 0.35},
            {"kind": "twinkle", "points": [[x, y, "e0a050", 1] for (x, y) in lights] +
                                          [[lamp_core[0], lamp_core[1], "fff0c4", 2]], "rate": 1.1, "min": 0.55},
            {"kind": "fauna", "fauna": [
                {"kind": "pigeon", "x": 556, "y": 131, "range": 8, "speed": 0.3, "rate": 2.0},
                {"kind": "pigeon", "x": 600, "y": 133, "range": 6, "speed": 0.25, "rate": 1.6, "flip": True},
                {"kind": "lamp_moth", "x": lamp_core[0], "y": lamp_core[1] - 2, "range": 6, "speed": 2.0, "rate": 9.0}]},
            {"kind": "particles", "style": "leaf", "count": 10, "rect": [0, 20, 640, 140], "speed": [-14, 10]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
