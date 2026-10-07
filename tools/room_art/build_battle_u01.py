"""Battle backdrop for Broadway: standing on the crosswalk, looking down the street toward the
Flatirons. Storefronts recede on both sides, neon blade signs buzz, a signal hangs over the road
and car lights come and go in the distance. The asphalt is still wet from an evening shower."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, shade, mix, text
from sky import flatirons_panel
from facade import storefront, brick_wall, FRAME, TRIM, TEAL
from props import lamp_post, bus_shelter, OUT, IRON, AMBER
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

INK = "#10121e"
HAZE = "#3a2c48"
ROAD = 150.0       # half width of the roadway
FACADE = 262.0     # building line
LAMPS = [(-166, 520), (166, 520), (-166, 900), (166, 900), (-166, 1500), (166, 1500)]
SIDEWALK = ["#4f4a54", "#625d68", "#6a6570", "#77727c", "#807a84"]
NEON = [  # (side X, Z, letters, colour)
    (-FACADE + 4, 470, "JAZZ", "ff7aa8"),
    (FACADE - 4, 560, "HOTEL", "ffbf5a"),
    (-FACADE + 4, 900, None, "58e0d0"),
    (FACADE - 4, 1100, None, "ff6a5a"),
    (-FACADE + 4, 1500, None, "ffbf5a"),
]


def ground_shader(X, Z):
    n = X.shape[0]
    ax = np.abs(X)
    rgb = np.zeros((n, 3), np.float32)
    # asphalt with fine aggregate, darker and glossier toward the gutters
    agg = hash2(np.floor(X / 2.0), np.floor(Z / 6.0), 1)
    base = np.array(C("#2a2833")[:3], np.float32)
    rgb[:] = base * (0.9 + 0.2 * agg[:, None])
    road = ax < ROAD
    # lane markings: double yellow centre, dashed white lanes
    yellow = (np.abs(ax - 4) < 2.2) & road
    rgb[yellow] = np.array(C("#c8a04a")[:3])
    dash = (np.abs(ax - 76) < 2.5) & (np.mod(Z, 70) < 30) & road
    rgb[dash] = np.array(C("#b8b4c0")[:3])
    # crosswalk where the fight is
    zebra = road & (Z > 290) & (Z < 372) & (np.mod(X + 300, 36) < 20)
    rgb[zebra] = np.array(C("#a8a4b0")[:3]) * (0.92 + 0.12 * agg[zebra, None])
    stop = road & (Z > 380) & (Z < 392) & (X < -6)
    rgb[stop] = np.array(C("#a8a4b0")[:3])
    # manhole
    mh = np.hypot(X - 40, (Z - 760) * 0.6) < 16
    rgb[mh] = np.array(C("#3a3642")[:3]); rgb[mh & (np.mod(X, 5) < 1.2)] = np.array(C("#24222c")[:3])
    # kerbs and sidewalks
    kerb = (ax >= ROAD) & (ax < ROAD + 6)
    rgb[kerb] = np.array(C("#9a9aa4")[:3])
    rgb[kerb & (ax < ROAD + 1.5)] = np.array(C("#b8b8c2")[:3])
    walk = ax >= ROAD + 6
    row = np.floor(Z / 22.0)
    col = np.floor((ax - ROAD - 6) / 22.0)
    tone = hash2(col, row, 4)
    sw = pal_array(SIDEWALK)
    srgb = sw[2] * (1 - tone[:, None]) + sw[4] * tone[:, None]
    fx = (ax - ROAD - 6) / 22.0 - col
    fz = Z / 22.0 - row
    srgb[(fx < 0.06) | (fz < 0.05)] = sw[0]
    rgb[walk] = srgb[walk]
    # wet: lamps and neon reflected as long streaks running toward the viewer
    for (lx, lz) in LAMPS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.4), 90, strength=0.4)
        streak = np.hypot((X - lx * 0.92) * 3.0, np.clip(lz - Z, 0, None) * 0.25 + np.clip(Z - lz, 0, None) * 2)
        warm_light(rgb, streak, 60, colour="#f6cf7a", strength=0.28)
    for (nx, nz, _, colour) in NEON:
        streak = np.hypot((X - nx * 0.8) * 2.5, np.clip(nz - Z, 0, None) * 0.3 + np.clip(Z - nz, 0, None) * 2)
        warm_light(rgb, streak, 70, colour="#" + colour, strength=0.3)
    # shop light spilling across the sidewalks
    spill = np.clip(1 - (FACADE - ax) / 70, 0, 1) * walk
    rgb += (np.array(C("#e9a84a")[:3]) - rgb) * (spill[:, None] * 0.18 * (np.mod(Z, 230) < 150)[:, None])
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 1400, 4200, amount=0.9)
    return out


def street_side(seed, plan):
    """A row of storefronts at room scale, laid out along the street (left to right = near to far)."""
    W = sum(w for (w, *_rest) in plan) + 4
    H = 170
    cv = Canvas(W, H, seed=seed)
    base = H - 2
    x = 0
    for (w, top, wall, sign, goods, awn, uppers) in plan:
        if wall == "gap":
            cv.rect(x, top, w, base - top, "#16121e")
            for yy in range(top + 4, base, 6):
                cv.hline(x, yy, w, "#1c1724")
        else:
            storefront(cv, x + 2, w - 4, base, top, wall=wall, sign=sign, goods=goods, lit=True, awn=awn, seed=seed + x, upper_lit=uppers)
            # a third storey for the taller blocks
            if top < 40:
                for wx in range(x + 14, x + w - 20, 30):
                    cv.rect(wx - 1, top + 50, 14, 2, TRIM[2])
        x += w
    return cv.a


LEFT = [
    (150, 20, "brick", "BOOKS", "books", None, (True, False, True)),
    (130, 44, "stucco", "CAFE", "cafe", ("#2c4a4c", "#e6d6b1"), (False, True)),
    (36, 60, "gap", None, None, None, ()),
    (150, 30, "brick", "RECORDS", "records", None, (True, True, False)),
    (140, 50, "stucco", "DELI", "cafe", ("#7a3640", "#e6d6b1"), (True, False)),
    (160, 26, "brick", "THEATRE", "books", None, (False, True, True)),
    (150, 40, "stucco", "BIKES", "records", ("#2c4a4c", "#e6d6b1"), (True,)),
]
RIGHT = [
    (140, 34, "stucco", "PIZZA", "cafe", ("#9e4e52", "#e6d6b1"), (True,)),
    (160, 22, "brick", "PRINTS", "books", None, (False, True, True)),
    (40, 60, "gap", None, None, None, ()),
    (140, 46, "stucco", "TACOS", "cafe", ("#c47a2c", "#e6d6b1"), (True, False)),
    (150, 28, "brick", "GAMES", "records", None, (True, False, True)),
    (150, 44, "stucco", "BAKERY", "cafe", ("#5c897c", "#e6d6b1"), (False, True)),
]


def facade_shader(tex, flip):
    h, w = tex.shape[:2]
    def shade_(u, Y, Z):
        tu = (w - 1 - u / ROOM_TO_BATTLE) if flip else u / ROOM_TO_BATTLE
        tv = (h - 2) - Y / ROOM_TO_BATTLE
        o = texture_lookup(tex, tu, tv, wrap=False)
        return fog(o, Z, HAZE, 1400, 4200, amount=0.9)
    return shade_


def neon_blade(letters, colour, lit):
    """A projecting blade sign: dark box, letters stacked vertically in tube colour."""
    n = len(letters)
    w, h = 13, n * 8 + 6
    cv = Canvas(w + 4, h + 4)
    cv.rect(2, 2, w, h, OUT); cv.rect(3, 3, w - 2, h - 2, "#1a1424")
    tube = C("#" + colour) if lit else mix("#" + colour, "#2a2436", 0.72)
    for i, ch in enumerate(letters):
        text(cv, ch, 5, 4 + i * 8, tube)
    if lit:
        m = cv.a[..., 3] > 0
        glow = np.zeros_like(cv.a)
        glow[..., :3] = C("#" + colour)[:3]
        ys, xs = np.where((np.abs(cv.a[..., :3] - np.array(tube[:3])).sum(-1) < 0.05) & m)
        for y, x in zip(ys, xs):
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if 0 <= y + dy < cv.h and 0 <= x + dx < cv.w:
                        glow[y + dy, x + dx, 3] = max(glow[y + dy, x + dx, 3], 0.28)
        out = glow.copy()
        sel = cv.a[..., 3] > 0
        out[sel] = cv.a[sel]
        tube_px = (np.abs(cv.a[..., :3] - np.array(tube[:3])).sum(-1) < 0.05) & sel
        out[~tube_px & sel, 3] = 0  # the lit overlay only carries tubes and glow
        return out
    return cv.a


def neon_bar(colour, lit, w=5, h=12):
    cv = Canvas(w + 2, h + 2)
    cv.rect(1, 1, w, h, OUT)
    c = C("#" + colour) if lit else mix("#" + colour, "#2a2436", 0.72)
    cv.rect(2, 2, w - 2, h - 2, c)
    return cv.a


def signal_head():
    cv = Canvas(11, 27)
    cv.rect(0, 0, 11, 27, OUT); cv.rect(1, 1, 9, 25, "#2a2a1e")
    for i in range(3):
        cv.ellipse(2, 2 + i * 8, 7, 7, "#16141f")
    return cv.a


def build(project):
    out = os.path.join(project, "assets/art/rooms/U01")
    v = View(horizon=98, cam=52, fill="#1b1830")
    # Sky: per-row dusk colour, the real Flatirons slabs centred at the end of the street.
    panel = flatirons_panel(scale=1.9)
    ph, pw = panel.shape[:2]
    rowc = np.median(panel[:, :6, :3], axis=1)
    sky = np.ones((130, 640, 4), np.float32)
    top = 104 - ph
    zenith, glow = panel[0, :, :3].mean(0), np.array(C("#ee8f73")[:3], np.float32)
    for y in range(130):
        t = min(1.0, max(0.0, y / 98.0)) ** 1.6
        sky[y, :, :3] = zenith * (1 - t) + glow * t
    x0 = 320 - pw // 2
    sky[max(0, top):top + ph, x0:x0 + pw] = panel[max(0, -top):]
    v.strip(sky, 0, solid=False)
    peaks = np.zeros((130, 640), bool)
    lum = lambda a: a[..., :3] @ np.array([0.3, 0.55, 0.15], np.float32)
    ref = np.repeat(rowc[np.clip(np.arange(130) - top, 0, ph - 1)][:, None, :], 640, 1)
    peaks[:, :] = (lum(sky) < lum(ref) - 0.1)
    peaks[:, :x0] = False; peaks[:, x0 + pw:] = False
    peaks[:40] = False
    v.solid[:130 * 3] |= np.repeat(np.repeat(peaks, 3, 0), 3, 1)
    v.ground(ground_shader)

    left = street_side(1, LEFT)
    right = street_side(2, RIGHT[::-1])  # painted far-to-near so its signs read the right way round
    z0 = 160.0
    for side, tex in ((-1, left), (1, right)):
        length = tex.shape[1] * ROOM_TO_BATTLE
        v.plane((side * FACADE, z0), (side * FACADE, z0 + length), facade_shader(tex, side > 0), y_max=(tex.shape[0] - 2) * ROOM_TO_BATTLE)
    # Far end of the street: a low block closing the view under the mountains.
    v.back(4600, lambda X, Y: rgba_of(np.tile(np.array(C("#231d36")[:3], np.float32), (X.shape[0], 1))),
           region=lambda X, Y: (np.abs(X) < FACADE) & (Y < 40 + 30 * (np.abs(np.sin(X / 90.0)))) & (Y >= 0))

    # Street furniture, far to near.
    items = []
    for (x, z) in LAMPS:
        items.append((z, "lamp", x))
    items.append((640, "signal", 0))
    neon_layers = []
    sprites = []
    for (nx, nz, letters, colour) in NEON:
        items.append((nz, "neon", (nx, letters, colour)))
    glows = []
    for z, kind, data in sorted(items, key=lambda t: -t[0]):
        if kind == "lamp":
            h = int(round(118 * v.scale(z)))
            spr, ax, ay = lamp_post(max(20, h))
            sx, sy, _ = v.sprite(spr.a, data, z, anchor=(ax / spr.w, ay / spr.h), scale=z / v.F)
            glows.append([int(round(sx)), int(round(sy - ay + 11)), "fff0c4", 2 if z < 1000 else 1])
        elif kind == "shelter":
            spr, ax, ay = bus_shelter()
            v.sprite(spr.a, data, z, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE)
        elif kind == "signal":
            # span wire across the street with the signal head hanging in the middle
            Y = 168
            sxl, syl = v.project(-FACADE, Y + 6, z); sxr, syr = v.project(FACADE, Y + 6, z)
            sx, sy = v.project(0, Y, z)
            sprites.append(("wire", (sxl, syl, sx, sy - 2, sxr, syr)))
            head = signal_head()
            sprites.append(("signal", (int(round(sx - 5)), int(round(sy)), head)))
        elif kind == "neon":
            nx, letters, colour = data
            Y = 150
            sx, sy = v.project(nx, Y, z)
            sprites.append(("neon", (int(round(sx)), int(round(sy)), letters, colour, nx)))

    v.rows(156, 360, INK, 0.0, 0.64)
    cv = v.reduce(112)
    # Crisp pieces on top of the reduced image.
    for kind, data in sprites:
        if kind == "wire":
            sxl, syl, sx, sy, sxr, syr = data
            n = int(abs(sx - sxl))
            for i in range(n + 1):
                t = i / n
                cv.px(int(round(sxl + (sx - sxl) * t)), int(round(syl + (sy - syl) * t + 3 * 4 * t * (1 - t))), "#16141f")
                cv.px(int(round(sx + (sxr - sx) * t)), int(round(sy + (syr - sy) * t + 3 * 4 * t * (1 - t))), "#16141f")
        elif kind == "signal":
            x, y, head = data
            cv.paste(head, x, y)
            signal_at = (x, y)
        elif kind == "neon":
            x, y, letters, colour, nx = data
            if letters:
                unlit = neon_blade(letters, colour, False)
                lit = neon_blade(letters, colour, True)
                px_ = x - (unlit.shape[1] if nx < 0 else 0) + (6 if nx < 0 else -6)
                px_ = x - unlit.shape[1] // 2
                cv.paste(unlit, px_, y)
                name = f"battle-neon-{letters.lower()}.png"
                Image.fromarray((np.clip(lit, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, name))
                neon_layers.append({"texture": f"res://assets/art/rooms/U01/{name}", "x": px_, "y": y})
            else:
                bar = neon_bar(colour, False)
                cv.paste(bar, x - 3, y)
                lit = neon_bar(colour, True)
                name = f"battle-neon-{colour}.png"
                Image.fromarray((np.clip(lit, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, name))
                neon_layers.append({"texture": f"res://assets/art/rooms/U01/{name}", "x": x - 3, "y": y})
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = v.solid_mask().astype(np.float32)
    # the crisp pieces drawn after the reduce are solid too
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))

    res = "res://assets/art/rooms/U01/"
    buzz = ["1111111111111011111111111111110111", "1111111111111111111101011111111111", "1111111111111111111111111111111111",
            "1101111111111111111111111111111111", "1111111111111111110111111111111111"]
    layers = [{"kind": "fauna", "depth": "far", "fauna": [
        {"kind": "bird", "x": 210, "y": 26, "fly": 9.0, "rate": 4.0},
        {"kind": "bird", "x": 226, "y": 32, "fly": 9.0, "rate": 3.6}]}]
    for i, nl in enumerate(neon_layers):
        layers.append({"kind": "blink", "pattern": buzz[i % len(buzz)], "rate": 9.0, **nl})
    sx, sy = signal_at
    cycle = {"g": "000000111111111111111111", "a": "000000000000000000000000", "r": "111111000000000000000000"}
    layers += [
        {"kind": "blink", "pattern": "1" * 14 + "0" * 10, "rate": 1.0, "rects": [[sx + 3, sy + 4 + 16, 5, 5, "58e0a0"], [sx + 1, sy + 2 + 16, 9, 9, "58e0a0", 0.25]]},
        {"kind": "blink", "pattern": "0" * 14 + "111" + "0" * 7, "rate": 1.0, "rects": [[sx + 3, sy + 4 + 8, 5, 5, "ffbf5a"], [sx + 1, sy + 2 + 8, 9, 9, "ffbf5a", 0.25]]},
        {"kind": "blink", "pattern": "0" * 17 + "1" * 7, "rate": 1.0, "rects": [[sx + 3, sy + 4, 5, 5, "ff5a5a"], [sx + 1, sy + 2, 9, 9, "ff5a5a", 0.25]]},
    ]
    def P(X, Z):
        a, b = v.project(X, 4, Z)
        return [round(a, 1), round(b, 1)]
    layers += [
        {"kind": "movers", "from": P(-76, 4200), "to": P(-76, 1050), "count": 2, "period": 9.0, "size": [1, 3], "pair": 9, "color": "fff0c4", "ease": "in"},
        {"kind": "movers", "from": P(76, 1050), "to": P(76, 4200), "count": 2, "period": 11.0, "size": [3, 1], "pair": 9, "color": "ff5a5a", "ease": "out"},
        {"kind": "twinkle", "points": glows, "rate": 1.5, "min": 0.5},
        {"kind": "particles", "style": "leaf", "count": 9, "rect": [-20, 20, 680, 150], "speed": [22, 12]},
    ]
    return {"far": res + "battle-far.png", "near": res + "battle-near.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:200])
    Image.open(paths.PROJECT + "/assets/art/rooms/U01/battle-far.png").resize((1280, 720), 0).save(os.path.dirname(os.path.abspath(__file__)) + "/t_bu01.png")
