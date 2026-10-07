"""Battle backdrop for the procession walk (M01): the whole of Macky, at the end of the avenue.

The camera stands where the procession walk meets the avenue and looks straight up it. The room
only ever shows Macky's doors; here the whole east front stands at the top of a short flight of
steps on its terrace - both towers to their crenellations, belfries, the gable, MACKY AUDITORIUM
over three arched doors with the middle one open on the lit lobby, crimson ivy - with the Flatirons
behind it on the left and the campus treeline on the right. The avenue runs up to it in random
sandstone flags, taped into gold seat boxes with a tent card in each, all the way to the steps;
the lawns either side are planted with rows and rows of little RESERVED cards on stakes, a field
of seats for every possible graduate. Commencement lamps with gold banners line the avenue; two
autumn oaks frame the view. At night the hall windows burn and floodlights wash the towers; the
dawn version has a rose and gold sky, the slabs of the Flatirons lit pink, the tower tops warm
and the windows out (the lamps are still on - nobody has come to switch them off).
Layers (shared by both versions): drifting cloud, a few birds crossing behind the towers, the
lamps and door lanterns breathing, sparrows waiting on the walk, leaves blowing across."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from midlib import sprite_from_cell
from pixel import Canvas, C, shade
from clouds import cloud_strip
from props import OUT, shrub, MUM
from surfaces import LEAVES
from lib_norlin import GRASS, PAVE_N, LIME
from lib_macky import (macky_front, flatirons_cut, night_sky_m, dawn_sky_m, dawn_clouds, flatirons_m, treeline_m, procession_lamp,
                       rough_ashlar, dressed_band, DRESS, MSTONE, CU_GOLD, SHADOW)
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light

ROOM = "M01"
INK = "#10121e"
NIGHT = (0.68, 0.72, 0.84)       # the world tint the room gets at night; the battle is painted at it
DAWN = (0.90, 0.936, 0.967)      # dawn world tint divided by the battle's own dawn modulate
HAZE_N, HAZE_D = "#2a2846", "#8a7484"
AXIS = -40.0                     # world X of the avenue's centre line (Macky's middle door)
AVENUE_HALF = 100.0
WALK = (60.0, 420.0)             # the procession walk across the foreground (Z range)
PLAZA = (1000.0, 1185.0, 236.0)  # Z0, Z1, half width
STEP_Z0, STEP_N, STEP_RISE, STEP_RUN = 1185.0, 5, 7.0, 14.0
TERRACE_Z = STEP_Z0 + STEP_N * STEP_RUN       # front of the terrace wall
Z_FRONT = TERRACE_Z + 36.0                    # Macky's front wall
TERRACE_Y = STEP_N * STEP_RISE
STEP_HALF = 170.0
BOX_COLS = (AXIS - 50.0, AXIS + 50.0)
BOX_W, BOX_D = 80.0, 44.0
TAPE = (6.0, 10.0)               # tape width across and along the avenue (world units)
BOX_ROWS = [470.0 + 66.0 * k for k in range(8)]
LAMPS = [(AXIS - 150, 560), (AXIS + 150, 560), (AXIS - 150, 780), (AXIS + 150, 780), (AXIS - 150, 1000),
         (AXIS + 150, 1000), (AXIS - 260, 1170), (AXIS + 260, 1170)]
MOON = (156, 26)
NIGHT_CLOUD = ["#2a2646", "#342e54", "#3e3660", "#4a3e68", "#5a4870", "#6e5276", "#866080"]


# --- grading ----------------------------------------------------------------------------------
def emissive(rgb):
    """Lit glass, lamp globes and the open door: warm, saturated, bright pixels keep their glow."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    return (r > 0.55) & (r - b > 0.36) & (g - b > 0.2)


def grade(rgba, dawn, keep_glow=True):
    out = rgba.copy()
    mul = np.array(DAWN if dawn else NIGHT, np.float32)
    m = ~emissive(out[..., :3]) if keep_glow else np.ones(out.shape[:-1], bool)
    out[m, :3] = out[m, :3] * mul
    return out


# --- the sky, the mountains, the campus -------------------------------------------------------
def sky_strip(dawn, w=640, h=104):
    cv = Canvas(w, h)
    stars = []
    if dawn:
        dawn_sky_m(cv, 0, 0, w, h, seed=13)
        dawn_clouds(cv, 0, 4, w, 70, seed=14, count=9)
    else:
        pts = night_sky_m(cv, 0, 0, w, h, seed=13, stars=150, star_h=74)
        stars = [(x, y) for (x, y) in pts if not (392 <= x <= 628 and y <= 72)]
    cv.a = grade(cv.a, dawn, keep_glow=False)
    if not dawn:
        rng = np.random.default_rng(3)
        for (x, y) in pts:
            cv.px(x, y, "#c8c4e4" if rng.random() < 0.75 else "#f2d890")
        mx, my = MOON
        for r, a in [(18, 0.05), (12, 0.08), (8, 0.1)]:
            cv.ellipse(mx - r, my - r, r * 2 + 1, r * 2 + 1, C("#efe2b8", a))
        cv.ellipse(mx - 6, my - 6, 13, 13, "#efe2b8"); cv.ellipse(mx - 3, my - 7, 12, 12, cv.a[my, mx - 14])
    return cv.a, stars


def hills_strip(dawn, w=640, h=104):
    """The Flatirons on the left behind Macky, the campus treeline across the horizon."""
    cv = Canvas(w, h)
    mts = flatirons_cut(dawn)
    cv.paste(mts, 16, 101 - mts.shape[0])
    lights = treeline_m(cv, -10, 260, 101, seed=6, dawn=dawn, lit=0.3)
    lights += treeline_m(cv, 380, w + 10, 101, seed=7, dawn=dawn, lit=0.3)
    if not dawn:
        # moonlight keeps the slabs readable: a lighter grade than the rest of the night
        m = ~emissive(cv.a[..., :3])
        cv.a[m, :3] *= np.array([0.86, 0.88, 0.96], np.float32)
    else:
        cv.a = grade(cv.a, dawn)
    return cv.a, lights


# --- ground -----------------------------------------------------------------------------------
def crazy(X, Z, cell=30.0, seed=0):
    """Random sandstone flags: jittered-grid Voronoi cells. Returns (tone 0..1, joint mask)."""
    gx, gz = X / cell, Z / (cell * 0.85)
    ix, iz = np.floor(gx), np.floor(gz)
    d1 = np.full(X.shape, 9.0, np.float32); d2 = d1.copy(); best = np.zeros(X.shape, np.float32)
    for dx in (-1, 0, 1):
        for dz in (-1, 0, 1):
            cx, cz = ix + dx, iz + dz
            px = cx + 0.15 + 0.7 * hash2(cx, cz, seed)
            pz = cz + 0.15 + 0.7 * hash2(cx, cz, seed + 1)
            d = np.hypot(gx - px, gz - pz)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            best = np.where(closer, hash2(cx, cz, seed + 2), best)
            d1 = np.where(closer, d, d1)
    joint = (d2 - d1) * cell < np.maximum(2.6, Z / 320.0 * 1.4)
    return best, joint


def ground_shader(dawn):
    grass = pal_array(GRASS)
    pave = pal_array(PAVE_N)
    lime = pal_array(LIME)
    gold = np.array(C(CU_GOLD[4])[:3], np.float32)
    dress = pal_array(DRESS)

    def shader(X, Z):
        n = X.shape[0]
        ax = np.abs(X - AXIS)
        # lawn in mowing bands, tufts
        band = (np.floor((X - AXIS) / 70.0) + np.floor(Z / 150.0)) % 2
        tuft = hash2(np.floor(X / 6), np.floor(Z / 12), 4)
        rgb = grass[3] * (1 - band[:, None]) + grass[4] * band[:, None]
        rgb[tuft > 0.88] = grass[5]
        rgb[tuft < 0.08] = grass[2]
        # paving: the walk across, the avenue, the plaza at the foot of the steps
        z0, z1, ph = PLAZA
        walk = (Z > WALK[0]) & (Z < WALK[1])
        avenue = (ax < AVENUE_HALF) & (Z >= WALK[1] - 2) & (Z < z0 + 2)
        plaza = (ax < ph) & (Z >= z0) & (Z < z1 + 30)
        paved = walk | avenue | plaza
        tone, joint = crazy(X, Z, 30.0, seed=12)
        idx = np.clip((tone * 4.99).astype(int) + 1, 1, 5)
        stone = pave[idx]
        stone[joint] = pave[0]
        rgb[paved] = stone[paved]
        # lime kerbs round the paving
        kerb = ~paved & (((Z > WALK[0] - 6) & (Z < WALK[1] + 6) & ~((ax < AVENUE_HALF + 6) & (Z > WALK[1])))
                         | ((ax < AVENUE_HALF + 6) & (Z > WALK[1]) & (Z < z0))
                         | ((ax < ph + 6) & (Z >= z0 - 6) & (Z < z1 + 30)))
        rgb[kerb] = lime[2]
        rgb[kerb & (hash2(np.floor(X / 14), np.floor(Z / 14), 2) > 0.7)] = lime[3]
        # the dressed ring set in the plaza
        d = np.hypot((X - AXIS) / 1.0, (Z - 1095) * 1.6)
        ring = (np.abs(d - 120) < 7) | (np.abs(d - 70) < 4)
        rgb[ring & plaza] = dress[3]
        rgb[(np.abs(d - 120) < 2) & plaza] = dress[5]
        # gold tape seat boxes all the way up the avenue
        for bz in BOX_ROWS:
            for bx in BOX_COLS:
                inside = (np.abs(X - bx) < BOX_W / 2) & (np.abs(Z - bz) < BOX_D / 2)
                edge = inside & ((np.abs(X - bx) > BOX_W / 2 - TAPE[0]) | (np.abs(Z - bz) > BOX_D / 2 - TAPE[1]))
                worn = hash2(np.floor(X / 5), np.floor(Z / 5), int(bz)) < 0.1
                rgb[edge & ~worn] = gold
        out = rgba_of(rgb)
        out = grade(out, dawn, keep_glow=False)
        if dawn:
            fog(out, Z, HAZE_D, 700, 2600, amount=0.5)
            warm_light(out[..., :3], np.hypot(X - AXIS, (Z - 1180) * 0.5), 160, colour="#f6dcae", strength=0.12)
        else:
            fog(out, Z, HAZE_N, 700, 2600, amount=0.6)
            for (lx, lz) in LAMPS:
                warm_light(out[..., :3], np.hypot(X - lx, (Z - lz) * 0.55), 80, strength=0.34)
            warm_light(out[..., :3], np.hypot(X - AXIS, (Z - 1180) * 0.6), 150, strength=0.3)
            warm_light(out[..., :3], np.hypot(X - AXIS, (Z - 300) * 0.5), 260, colour="#c8d0f0", strength=0.08)
        if dawn:
            for (lx, lz) in LAMPS:
                warm_light(out[..., :3], np.hypot(X - lx, (Z - lz) * 0.55), 60, strength=0.14)
        return out
    return shader


def step_shaders(dawn):
    dress = pal_array(DRESS)
    mul = np.array(DAWN if dawn else NIGHT, np.float32)

    def tread(X, Z):
        rgb = np.repeat(dress[4][None], X.shape[0], 0)
        slab = hash2(np.floor((X - AXIS) / 46), np.floor(Z / STEP_RUN), 3)
        rgb[slab > 0.6] = dress[3]
        rgb[((X - AXIS) / 46) % 1 < 0.05] = dress[2]
        nose = ((Z - STEP_Z0) % STEP_RUN) < 2.5
        rgb[nose] = dress[5]
        rgb *= mul
        out = rgba_of(rgb)
        if not dawn:
            warm_light(out[..., :3], np.hypot(X - AXIS, (Z - 1260) * 0.8), 120, strength=0.34)
        return out

    def riser(u, Y, Z):
        rgb = np.repeat(dress[2][None], u.shape[0], 0)
        rgb[(Y % STEP_RISE) > STEP_RISE - 1.5] = dress[1]
        rgb *= mul
        out = rgba_of(rgb)
        if not dawn:
            warm_light(out[..., :3], np.abs(u - STEP_HALF), 140, strength=0.26)
        return out
    return tread, riser


def terrace_wall(dawn, w=1240, h=None):
    """The terrace Macky stands on: rough sandstone wall with a dressed coping (room scale)."""
    h = h or int(TERRACE_Y / ROOM_TO_BATTLE) + 4
    cv = Canvas(w, h)
    rough_ashlar(cv, 0, 3, w, h - 3, seed=21, courses=(6, 7))
    dressed_band(cv, 0, 0, w, 3, seed=22)
    rng = np.random.default_rng(23)
    top = Canvas(w, 18)
    x = 0
    while x < w:
        sw, sh = int(rng.integers(18, 28)), int(rng.integers(10, 16))
        top.paste(shrub(0, 0, sw, sh, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.25 else None), x, 18 - sh)
        x += sw - 5
    out = Canvas(w, h + 16)
    out.paste(top.a, 0, 0)
    out.paste(cv.a, 0, 16)
    out.a = grade(out.a, dawn, keep_glow=False)
    return out.a


# --- Macky --------------------------------------------------------------------------------------
def macky_sprite(dawn):
    """The whole east front at room scale, towers to their battlements; floodlights at night."""
    W_, base = 612, 252
    cv = Canvas(W_, base + 2)
    cx = W_ // 2
    lights, parts = macky_front(cv, cx, base, tower_top=base - 230, dawn=dawn, seed=4)
    if dawn:
        # first sun on the tower tops and the gable: stepped warm bands
        for (y0, y1, a) in [(0, 60, 0.32), (60, 100, 0.16)]:
            reg = cv.a[y0:y1]
            m = reg[..., 3] > 0.5
            warm = reg[..., :3] * 0.6 + np.array(C("#f8b878")[:3]) * 0.4
            reg[m, :3] = reg[m, :3] * (1 - a) + warm[m] * a
    else:
        for (t0, t1) in (parts["left_tower"], parts["right_tower"]):
            tcx = (t0 + t1) // 2
            for (spread, top, a) in [(44, 20, 0.05), (34, 70, 0.06), (24, 130, 0.07)]:
                cv.poly([(tcx - 5, base - 4), (tcx - spread, top), (tcx + spread, top), (tcx + 5, base - 4)], C("#f6cf7a", a))
    # planting along the plinth either side of the doors
    rng = np.random.default_rng(41)
    for (w0, w1) in list(parts["wings"]) + [(parts["left_tower"][0], parts["block"][0] - 6), (parts["block"][1] + 6, parts["right_tower"][1])]:
        x = w0
        while x < w1 - 10:
            sw, sh = int(rng.integers(16, 24)), int(rng.integers(10, 15))
            cv.paste(shrub(0, 0, sw, sh, seed=int(rng.integers(1e6)), flowers=MUM if rng.random() < 0.25 else None), x, base + 2 - sh)
            x += sw - 4
    a = grade(cv.a, dawn)
    return a, cx, base, lights


def oak(height, flip=False, tint=(1.0, 1.0, 1.0), dawn=False):
    spr = sprite_from_cell(5, height=height, colors=40)
    if flip:
        spr = spr[:, ::-1].copy()
    spr = spr.copy()
    spr[..., :3] = np.clip(spr[..., :3] * np.array(tint, np.float32), 0, 1)
    return grade(spr, dawn, keep_glow=False)


def far_tree(height, cell, dawn):
    spr = sprite_from_cell(cell, height=height, colors=32, brightness=0.75, saturation=0.85)
    return grade(spr, dawn, keep_glow=False)


def stake_sprite(s):
    """A RESERVED card on a stake, pre-sized for screen scale s (crisp 1:1)."""
    cw = max(2, int(round(8 * s)))
    ch = max(2, int(round(6 * s)))
    sh = max(2, int(round(10 * s)))
    cv = Canvas(cw, ch + sh)
    cv.vline(cw // 2, ch, sh, "#5a4a3c")
    cv.rect(0, 0, cw, ch, "#efe4cc")
    if ch >= 3:
        cv.hline(0, ch - 1, cw, "#a89a86")
    if cw >= 4 and ch >= 3:
        cv.px(1, 1, "#c84a3c")
    return cv.a


def tent_card(s):
    """The folded name card standing in each seat box."""
    cw = max(2, int(round(9 * s)))
    ch = max(2, int(round(6 * s)))
    cv = Canvas(cw, ch)
    cv.rect(0, 0, cw, ch, "#f2e8d0")
    cv.hline(0, ch - 1, cw, "#8a7c6a")
    if ch >= 4 and cw >= 6:
        cv.hline(1, ch // 2 - 1, cw - 2, "#b8a888")
    return cv.a


def render(dawn):
    v = View(horizon=98, cam=52, fill="#141223")
    sky, stars = sky_strip(dawn)
    v.strip(sky, 0, solid=False)
    hills, hill_lights = hills_strip(dawn)
    v.strip(hills, 0)
    v.ground(ground_shader(dawn))

    # everything standing, far to near
    items = []
    for (x, z, cell, hh) in [(1010, 2200, 5, 300), (820, 1650, 6, 300)]:
        items.append((z, "far_tree", (x, cell, hh)))
    items.append((Z_FRONT, "macky", None))
    items.append((TERRACE_Z, "terrace", None))
    for (x, z) in LAMPS:
        items.append((z, "lamp", x))
    items.append((640, "oak", (-640, 150, False, (1.0, 1.0, 1.0))))
    items.append((720, "oak", (700, 146, True, (1.04, 0.96, 0.88))))
    rng = np.random.default_rng(7)
    for z in np.arange(450, 1160, 54):
        for side in (-1, 1):
            x = AXIS + side * (AVENUE_HALF + 40)
            while abs(x - AXIS) < 1100:
                if rng.random() > 0.08:
                    items.append((z + rng.uniform(-3, 3), "stake", x + rng.uniform(-4, 4)))
                x += side * 48
    for bz in BOX_ROWS:
        for bx in BOX_COLS:
            items.append((bz + 4, "card", bx))
    items.sort(key=lambda t: -t[0])

    glows = []
    macky_at = None
    tread, riser = step_shaders(dawn)
    for z, kind, data in items:
        s = v.scale(z)
        if kind == "far_tree":
            x, cell, hh = data
            spr = far_tree(int(round(hh * s)), cell, dawn)
            v.sprite(spr, x, z, scale=z / v.F)
        elif kind == "macky":
            spr, mcx, mbase, lights = macky_sprite(dawn)
            sx, sy, sc = v.sprite(spr, AXIS, z, Y=TERRACE_Y, anchor=(mcx / spr.shape[1], mbase / spr.shape[0]),
                                  scale=ROOM_TO_BATTLE)
            k = sc * ROOM_TO_BATTLE
            macky_at = (sx, sy, k)
            for (lx, ly) in lights:
                glows.append([int(round(sx + (lx - mcx) * k)), int(round(sy + (ly - mbase) * k)), "f6cf7a", 1])
        elif kind == "terrace":
            # the terrace wall, then the steps cut into it, far tread first
            wall = terrace_wall(dawn)
            v.sprite(wall, AXIS, z, anchor=(0.5, 1.0), scale=ROOM_TO_BATTLE)
            for i in range(STEP_N - 1, -1, -1):
                za = STEP_Z0 + i * STEP_RUN
                yt = (i + 1) * STEP_RISE
                v.ground(lambda X, Z, za=za: _clip(tread(X, Z), X, Z, za, za + STEP_RUN), height=yt,
                         y_from=v.project(0, yt, za + STEP_RUN)[1] - 0.5, y_to=v.project(0, yt, za)[1] + 0.5)
                v.plane((AXIS - STEP_HALF, za), (AXIS + STEP_HALF, za), riser, y_max=yt, y_min=yt - STEP_RISE)
            # the cheek walls either side of the flight
            for side in (-1, 1):
                xx = AXIS + side * (STEP_HALF + 6)
                v.plane((xx, STEP_Z0 - 2), (xx, TERRACE_Z), _cheek(dawn), y_max=TERRACE_Y + 4)
        elif kind == "lamp":
            spr, ax, ay = procession_lamp(68)
            a = grade(spr.a, dawn)
            if data > AXIS:
                a = a[:, ::-1].copy()
                ax = spr.w - 1 - ax
            sx, sy, sc = v.sprite(a, data, z, anchor=(ax / spr.w, ay / spr.h), scale=ROOM_TO_BATTLE)
            k = sc * ROOM_TO_BATTLE
            glows.append([int(round(sx)), int(round(sy - (ay - 9) * k)), "fff0c4", 2 if z < 900 else 1])
        elif kind == "oak":
            x, hh, flip, tint = data
            spr = oak(int(round(hh * ROOM_TO_BATTLE * s)), flip, tint, dawn)
            v.sprite(spr, x, z, scale=z / v.F)
        elif kind == "stake":
            spr = stake_sprite(ROOM_TO_BATTLE * s * 0.62)
            sx, sy = v.project(data, 0, z)
            if 0 <= sx < 640:
                v.strip(grade(spr, dawn, keep_glow=False), int(round(sy)) - spr.shape[0] + 1, int(round(sx)) - spr.shape[1] // 2)
        elif kind == "card":
            spr = tent_card(ROOM_TO_BATTLE * s * 0.62)
            sx, sy = v.project(data, 0, z)
            v.strip(grade(spr, dawn, keep_glow=False), int(round(sy)) - spr.shape[0] + 1, int(round(sx)) - spr.shape[1] // 2)

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp extras on the near walk: leaves, confetti, a dropped programme
    for _ in range(70):
        lx, ly = int(rng.integers(0, 640)), int(rng.integers(140, 200))
        c = LEAVES[int(rng.integers(len(LEAVES)))]
        c = shade(c, -0.25) if not dawn else c
        cv.px(lx, ly, c); cv.px(lx + 1, ly, shade(c, -0.2))
    for _ in range(30):
        lx, ly = int(rng.integers(160, 470)), int(rng.integers(134, 170))
        cv.px(lx, ly, [CU_GOLD[2], "#1a1418", "#c8bca0"][int(rng.integers(3))])
    cv.rect(346, 170, 9, 5, "#1a1418"); cv.rect(346, 169, 9, 5, "#bdb29a"); cv.rect(347, 170, 7, 2, CU_GOLD[2])
    return v, cv, stars, glows


def _clip(rgba, X, Z, z0, z1):
    out = rgba
    out[(Z < z0) | (Z >= z1) | (np.abs(X - AXIS) > STEP_HALF), 3] = 0
    return out


def _cheek(dawn):
    dress = pal_array(DRESS)
    mul = np.array(DAWN if dawn else NIGHT, np.float32)

    def sh(u, Y, Z):
        rgb = np.repeat(dress[3][None], u.shape[0], 0)
        rgb[Y > TERRACE_Y + 1] = dress[5]
        rgb[(u % 20) < 1.2] = dress[1]
        return rgba_of(rgb * mul)
    return sh


def save_pair(v, cv, out, suffix):
    cv.save(os.path.join(out, f"battle-far{suffix}.png"))
    near = cv.a.copy()
    near[..., 3] = v.solid_mask().astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, f"battle-near{suffix}.png"))


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    v, cv, stars, glows = render(False)
    save_pair(v, cv, out, "")
    vd, cvd, _, _ = render(True)
    save_pair(vd, cvd, out, "-dawn")
    cloud_strip(640, 40, count=5, seed=8, pal=NIGHT_CLOUD, sizes=(50, 110)).save(os.path.join(out, "battle-clouds.png"))
    res = f"res://assets/art/rooms/{ROOM}/"
    lamp_pts = [g for g in glows if g[2] == "fff0c4"]
    door_pts = [g for g in glows if g[2] != "fff0c4"][-6:]
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "far_dawn": res + "battle-far-dawn.png",
        "near_dawn": res + "battle-near-dawn.png",
        "layers": [
            {"kind": "drift", "depth": "far", "texture": res + "battle-clouds.png", "y": 14, "speed": 2.0, "alpha": 0.55},
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "bird", "x": 60, "y": 36, "fly": 11.0, "rate": 3.6},
                {"kind": "bird", "x": 90, "y": 46, "fly": 10.0, "rate": 3.2},
                {"kind": "bird", "x": 420, "y": 30, "fly": 9.0, "rate": 3.0}]},
            {"kind": "twinkle", "points": lamp_pts, "rate": 1.3, "min": 0.55},
            {"kind": "fauna", "fauna": [
                {"kind": "macky_sparrow", "x": 318, "y": 158, "range": 3, "speed": 0.4, "rate": 1.2},
                {"kind": "macky_sparrow", "x": 334, "y": 162, "range": 0, "speed": 0.0, "rate": 0.8, "flip": True},
                {"kind": "macky_sparrow", "x": 372, "y": 156, "range": 2, "speed": 0.3, "rate": 1.5}]},
            {"kind": "particles", "style": "leaf", "count": 12, "rect": [-20, 20, 680, 150], "speed": [20, 12]},
        ],
    }


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
