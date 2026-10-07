"""Battle backdrop for the dawn exit (M07): the reverse of the room. We turn round on the garden
walk and look east, straight into the sunrise: Macky's twin crenellated towers stand dark against
a gold sky, rimmed with fire, the sun just clearing the gable between them. Long shadows of the
towers, the oaks and the lamps run down the walk toward the fighters; between them the dewy lawn
glows. Rays sweep slowly out of the gap, the dew glints, geese cross, leaves and warm motes drift.
Painted at sunrise only (the game only reaches M07 after dawn_started)."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from midlib import sprite_from_cell
from pixel import Canvas, C, mix
from props import shrub, MUM
from persp import View, hash2, fog, pal_array, rgba_of, warm_light
from lib_macky2 import backlit, band_ramp, cloud_bank, halo, spruce, SUNRISE, GOLD_CLOUD, _rng
from lib_norlin import lantern_head
from props import IRON

ROOM = "M07"
INK = "#10121e"
SUN = (320, 27)                  # sun centre on screen (just clearing Macky's gable)
Z_MACKY = 470.0                  # Macky's front steps
MACKY_H = 132                    # on-screen height of the facade sprite
WALK = 46                        # half width of the walk
TREES = [(-250, 560, 100), (262, 600, 100), (-430, 900, 120), (450, 980, 120)]   # X, Z, height (screen px at Z=F)
LAMPS = [(-74, 360), (74, 360), (-70, 430), (70, 430)]
LAMP_H = 96
TOWERS = (-62, 62)               # tower X centres (world), for their shadows
GRASS_GLOW = ["#3e4a24", "#56622c", "#6e7a34", "#8a923e", "#a8a84c", "#c8bc62", "#e4d07c"]
GRASS_SHADE = ["#1a262c", "#203034", "#283a3a", "#304642"]
WALK_SUN = ["#5a4038", "#8a6450", "#a07660", "#b48a70", "#c8a084", "#e0bc9a"]
WALK_SHADE = ["#2e2a36", "#443e4c", "#524a58", "#5e5464", "#6a6070"]
HAZE = "#f0caa4"


def in_shadow(X, Z):
    """Long shadows lying straight toward the viewer (the sun is dead ahead, so in the picture
    they all radiate from the vanishing point)."""
    sh = np.zeros(X.shape, bool)
    # Macky's bulk right in front of it, its two towers much further
    sh |= (np.abs(X) < 118) & (Z > Z_MACKY - 70) & (Z < Z_MACKY + 40)
    for tx in TOWERS:
        sh |= (np.abs(X - tx) < 26) & (Z > Z_MACKY - 260) & (Z < Z_MACKY)
    for (tx, tz, h) in TREES:
        crown = (np.abs(X - tx) < 52) & (Z > tz - 230) & (Z < tz - 70)
        trunk = (np.abs(X - tx) < 7) & (Z > tz - 80) & (Z < tz)
        sh |= crown | trunk
    for (lx, lz) in LAMPS:
        sh |= (np.abs(X - lx) < 2.0) & (Z > lz - 120) & (Z < lz)
    return sh


def ground_shader(X, Z):
    n = X.shape[0]
    rgb = np.zeros((n, 3), np.float32)
    ax = np.abs(X)
    sh = in_shadow(X, Z)
    # lawn: mowing stripes running toward Macky, tufts, glowing where the low sun shines through
    stripe = (np.floor((X + 2000) / 90.0) % 2).astype(int)
    scr_x = X * 320.0 / Z
    scr_y = 52 * 320.0 / Z
    tuft = hash2(np.floor(scr_x / 2), np.floor(scr_y * 1.0), 3)
    glow = np.clip(1 - np.abs(X) / (Z * 0.9 + 60), 0, 1) * np.clip((Z - 350) / 500, 0, 1)   # brighter toward the sun
    k = np.clip(2 + stripe + (glow > 0.45) + (glow > 0.75) + (tuft > 0.8) * 1 - (tuft < 0.18) * 1, 0, 6)
    rgb[:] = pal_array(GRASS_GLOW)[k]
    ks = np.clip(1 + stripe + (tuft > 0.85) * 1 - (tuft < 0.18) * 1, 0, 3)
    rgb[sh] = pal_array(GRASS_SHADE)[ks[sh]]
    # the walk: sandstone flags in courses, a red sandstone band each side
    walk = ax < WALK
    row = np.floor(Z / 22.0)
    width = 26 + 20 * hash2(row, 7)
    off = hash2(row, 11) * width
    col = np.floor((X + off) / width)
    fx = (X + off) / width - col
    fz = Z / 22.0 - row
    tone = hash2(col, row, 5)
    ws = pal_array(WALK_SUN)
    wrgb = ws[2] * (1 - tone[:, None]) + ws[4] * tone[:, None]
    wrgb[(fx < 2.0 / width) | (fz < 0.1)] = ws[0]
    lip = (fz > 0.86) & ~((fx < 2.0 / width) | (fz < 0.1))
    wrgb[lip] = wrgb[lip] * 0.5 + ws[5] * 0.5
    wsh = pal_array(WALK_SHADE)
    srgb = wsh[2] * (1 - tone[:, None]) + wsh[3] * tone[:, None]
    srgb[(fx < 2.0 / width) | (fz < 0.1)] = wsh[0]
    rgb[walk] = np.where(sh[walk, None], srgb[walk], wrgb[walk])
    band = (ax >= WALK) & (ax < WALK + 6)
    rgb[band] = np.where(sh[band, None], pal_array(["#4a3440"])[0], pal_array(["#9a5a48"])[0])
    rgb[band & (ax < WALK + 1.2)] = pal_array(["#d8a888"])[0]
    # the sun's glare path down the wet walk (dew on stone), narrow and broken
    glare = walk & ~sh & (np.abs(scr_x) < 3) & (Z > 520) & (hash2(np.floor(scr_x), np.floor(scr_y * 2), 9) > 0.5)
    rgb[glare] = rgb[glare] * 0.4 + pal_array(["#fff0c8"])[0] * 0.6
    # fallen leaves along the walk edges and under the oaks
    cell = hash2(np.floor(X / 5), np.floor(Z / 5), 21)
    drift = np.clip(1 - np.abs(ax - WALK - 4) / 16, 0, 1) * 0.3
    for (tx, tz, h) in TREES:
        drift += np.clip(1 - np.hypot(X - tx, (Z - tz) * 0.8) / 110, 0, 1) * 0.5
    leaf = cell < drift * 0.4
    pick = (hash2(np.floor(X / 5), np.floor(Z / 5), 22) * 4).astype(int)
    lp = pal_array(["#c05a2c", "#e08a3c", "#a84a30", "#e0b844"])
    lrgb = lp[np.clip(pick, 0, 3)]
    lrgb[sh] *= 0.55
    rgb[leaf] = lrgb[leaf]
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 700, 2600, amount=0.7)
    return out


def sky(v):
    """Sunrise sky in stepped bands: blue overhead warming to gold at the horizon, and around the
    sun a set of concentric steps of brighter gold (no gradient: every pixel takes one of the
    palette's flat colours, joins ragged)."""
    H = 112
    cv = Canvas(640, H)
    ys, xs = np.mgrid[0:H, 0:640].astype(np.float32)
    sx, sy = SUN
    vert = (ys / (H - 1)) ** 1.15                         # 0 top .. 1 horizon
    r = np.hypot((xs - sx) * 0.8, ys - sy)
    radial = np.clip(1 - r / 230, 0, 1) ** 1.6           # 1 at the sun
    t = np.clip(vert * 0.78 + radial * 0.62, 0, 1)
    jitter = (hash2(np.floor(xs / 2), np.floor(ys), 5) - 0.5) * 0.035
    n = len(SUNRISE)
    k = np.clip(((t + jitter) * n).astype(int), 0, n - 1)
    cv.a[..., :3] = pal_array(SUNRISE)[k]
    cv.a[..., 3] = 1
    # the sun disc and a tight corona
    cv.ellipse(sx - 22, sy - 22, 45, 45, "#fcd48e")
    cv.ellipse(sx - 16, sy - 16, 33, 33, "#fee6b0")
    cv.ellipse(sx - 12, sy - 12, 25, 25, "#fff4d8")
    cv.ellipse(sx - 9, sy - 9, 19, 19, "#fffef8")
    # thin cloud bars lit gold from below, low in the east
    rng = _rng(4)
    for (x, y, ln) in [(30, 64, 120), (150, 74, 90), (430, 72, 140), (520, 58, 100), (190, 54, 60), (392, 84, 70)]:
        for k2 in range(2):
            L = ln - k2 * 30
            x0 = x + k2 * 12 + int(rng.integers(-4, 5))
            cv.hline(x0 + 6, y + k2 * 2 - 1, L // 2, GOLD_CLOUD[1])
            cv.hline(x0, y + k2 * 2, L, GOLD_CLOUD[2])
            cv.hline(x0 + 2, y + k2 * 2 + 1, L - 4, GOLD_CLOUD[5])
    v.strip(cv.a, 0, solid=False)


def far_campus():
    """Silhouettes along the horizon either side of Macky, dark against the glow, gold-rimmed."""
    rng = _rng(8)
    cv = Canvas(640, 40)
    base = 39
    for x in range(-10, 650, 8):
        h = int(rng.integers(8, 18))
        cv.ellipse(x, base - h, int(rng.integers(12, 20)), h * 2, "#6a5068")
    for x in range(0, 640, 60):
        if 180 < x < 460:
            continue
        w, h = int(rng.integers(30, 50)), int(rng.integers(10, 16))
        cv.rect(x, base - h, w, h, "#5a4258")
        cv.poly([(x - 3, base - h), (x + 6, base - h - 6), (x + w - 6, base - h - 6), (x + w + 3, base - h)], "#5a4258")
        for wx in range(x + 4, x + w - 3, 6):
            if rng.random() < 0.3:
                cv.rect(wx, base - h + 4, 2, 2, "#f6c46a")
    for x in range(-4, 644, 5):
        h = int(rng.integers(4, 10))
        cv.ellipse(x, base - h + 3, int(rng.integers(8, 13)), h * 2, "#4a3a50")
    a = cv.a
    m = a[..., 3] > 0.5
    up = m & ~np.roll(m, 1, axis=0)
    a[up, :3] = np.array(C("#f6c47a")[:3])
    a[base:, :, 3] = 0
    return a


def macky_backlit():
    spr = sprite_from_cell(4, height=MACKY_H, colors=40)

    def windows(out, lum, m):
        # the lobby lights are still on behind the door glass and the rose window
        h, w = out.shape[:2]
        ys, xs = np.mgrid[0:h, 0:w]
        warm = (out[..., 0] - out[..., 2] > 0.18) & (lum > 0.62) & m
        return warm & (ys > h * 0.35)
    return backlit(spr, body=(0.28, 0.25, 0.4), lift=(0.06, 0.04, 0.08), glow_windows=windows)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52)
    sky(v)
    v.strip(far_campus(), 98 - 39 + 3)
    v.ground(ground_shader)

    # Macky, the oaks and lamps, back to front
    items = [(Z_MACKY, "macky", None)] + [(z, "tree", (x, h)) for (x, z, h) in TREES] + [(z, "lamp", x) for (x, z) in LAMPS]
    glows = []
    rng = _rng(12)
    for z, kind, data in sorted(items, key=lambda t: -t[0]):
        if kind == "macky":
            m = macky_backlit()
            v.sprite(m, 0, Z_MACKY, anchor=(0.5, 0.97), scale=Z_MACKY / v.F)
            # low hedges of the forecourt either side of the steps
            for side in (-1, 1):
                for k in range(7):
                    x = side * (90 + k * 26)
                    w, h = int(rng.integers(26, 34)), int(rng.integers(12, 18))
                    s = shrub(0, 0, w, h, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.3 else None)
                    v.sprite(backlit(s.a, body=(0.42, 0.42, 0.52)), x, Z_MACKY - 20, scale=(Z_MACKY - 20) / v.F * 0.9)
        elif kind == "tree":
            x, hh = data
            h = int(round(hh * v.scale(z) * 1.7))
            spr = sprite_from_cell(5, height=h, colors=36, brightness=1.0, saturation=1.05)
            spr = backlit(spr, body=(0.42, 0.34, 0.4), rim="#ffcc70", rim2="#f09040", fringe=0.55)
            v.sprite(spr, x, z, scale=z / v.F)
        else:
            x = data
            h = int(round(LAMP_H * v.scale(z)))
            cv = Canvas(20, h + 4)
            cx = 10
            cv.rect(cx - 1, 14, 3, h - 14, "#2a2436"); cv.vline(cx - 1, 14, h - 14, "#f0b860")
            cv.rect(cx - 3, h - 4, 7, 4, "#2a2436"); cv.hline(cx - 3, h - 4, 7, "#f0b860")
            lantern_head(cv, cx, 1, glass=("#e9a84a", "#f6cf7a", "#fff0c4"))
            sx, sy, s = v.sprite(cv.a, x, z, anchor=(0.5, (h) / (h + 4)), scale=z / v.F)
            glows.append([int(round(sx)), int(round(sy - h * s + 10 * s)), "fff0c4", 1])

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    # crisp dew glints and leaves on the near lawn (1:1)
    for _ in range(200):
        lx, ly = int(rng.integers(0, 640)), int(rng.integers(152, 360))
        if abs(lx - 320) < (ly - 98) * WALK / 52 + 4:
            continue
        dim = 1 - min(0.6, max(0.0, (ly - 156) / 204 * 0.62))
        c = ["#c05a2c", "#e08a3c", "#a84a30", "#e0b844"][int(rng.integers(4))]
        col = tuple(np.array(C(c)[:3]) * dim)
        cv.px(lx, ly, col); cv.px(lx + 1, ly, tuple(np.array(col) * 0.8))
    solid = v.solid_mask()
    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = solid.astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))
    cloud_bank(640, 30, count=4, seed=17, sizes=(40, 90), thick=(3, 5), pal=GOLD_CLOUD).save(os.path.join(out, "battle-clouds.png"))

    # dew glints on the lawn either side of the walk, strongest toward the sun
    dew = []
    while len(dew) < 46:
        x, y = int(rng.integers(0, 640)), int(rng.integers(118, 160))
        if abs(x - 320) < (y - 98) * WALK / 52 + 8:
            continue
        if not solid[y, x]:
            continue
        dew.append([x, y, "fff6dc" if len(dew) % 3 else "ffe0a0", 1])
    sx, sy = SUN
    rays = []
    for i, (ang, w, ln, a) in enumerate([(100, 70, 300, 0.07), (122, 60, 300, 0.06), (80, 66, 300, 0.07), (58, 56, 300, 0.05),
                                          (143, 50, 260, 0.05), (36, 50, 260, 0.04)]):
        rays.append({"kind": "beam", "x": sx, "y": sy, "angle": ang, "sweep": 2.5, "period": 11 + i * 2, "phase": i * 1.3,
                     "length": ln, "width": w, "color": "ffe8b8", "alpha": a, "floor": 420})
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "drift", "depth": "far", "texture": res + "battle-clouds.png", "y": 6, "speed": 2.0, "alpha": 0.85},
            {"kind": "fauna", "depth": "far", "fauna": [{"kind": "mk2_goose", "x": 140 - 10 * k, "y": 22 + 4 * abs(k - 2), "fly": 13.0, "rate": 3.0}
                                                         for k in range(5)]},
        ] + rays + [
            {"kind": "twinkle", "points": dew, "rate": 2.2, "min": 0.0},
            {"kind": "twinkle", "points": glows, "rate": 0.9, "min": 0.5},
            {"kind": "particles", "style": "dust", "count": 26, "rect": [150, 40, 340, 110], "speed": [3, 5], "color": "ffe6b0"},
            {"kind": "particles", "style": "leaf", "count": 12, "rect": [-20, -10, 680, 170], "speed": [-30, 14]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
