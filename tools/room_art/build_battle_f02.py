"""Battle backdrop for the volunteer tent (F02): inside the crew marquee, looking out through its
open front. The red-and-cream canvas ceiling converges overhead with string lights along it, the
lit canvas walls have dark PVC windows, the crew's gear stands along them (vest rack, chair
stacks, water, the radio that keeps calling), and the plywood floor runs out to the festival:
wet lawn, the main stage glowing under the Flatirons, its beams sweeping the sky."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, shade, mix, text, text_width
from sky import flatirons_panel
from props import OUT
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
import lib_farrand as F

ROOM = "F02"
INK = "#10121e"
HAZE = "#3a2c48"
WALL_X = 300.0
EAVE = 143.0             # wall/ceiling height (84 room px x 1.7)
Z_FRONT = 760.0          # the open front of the tent
Z_STAGE = 3000.0
BULB_ROWS = [-120.0, 120.0]


def floor_shader(X, Z):
    n = X.shape[0]
    inside = Z < Z_FRONT + 120
    rgb = F.battle_grass_rgb(X, Z, stripe=110.0, seed=2)
    # plywood inside the tent and on the apron beyond its front
    sw, sl = 120.0, 60.0
    col = np.floor(X / sw)
    row = np.floor(Z / sl)
    off = (row % 2) * sw / 2
    col2 = np.floor((X + off) / sw)
    fx = (X + off) / sw - col2
    fz = Z / sl - row
    ply = pal_array(["#3e3026", "#5a4636", "#7a6048", "#947a5a", "#ab926c", "#c4ab82"])
    tone = hash2(col2, row, 3)
    prgb = ply[3] * (1 - tone[:, None] * 0.6) + ply[4] * (tone[:, None] * 0.6)
    grain = hash2(np.floor(X / 9.0), np.floor(Z / 3.0), 4)
    prgb = prgb * (0.95 + 0.07 * grain[:, None])
    prgb[(fx < 0.012) | (fz < 0.03)] = ply[2]
    screw = ((fx * sw) % 14 < 1.4) & (fz > 0.05) & (fz < 0.09)
    prgb[screw] = ply[1]
    rgb[inside] = prgb[inside]
    # muddy footprints and wet patches blown in at the front
    fp = (hash2(np.floor(X / 7), np.floor(Z / 9), 8) > 0.93) & inside
    rgb[fp] = rgb[fp] * 0.75 + pal_array([F.DIRT[1]])[0] * 0.25
    wet = (np.hypot((X + 60) / 120, (Z - Z_FRONT + 40) / 60) + 0.3 * hash2(np.floor(X / 10), np.floor(Z / 10), 5) < 1)
    rgb[wet] = rgb[wet] * 0.7 + pal_array(["#5a4a78"])[0] * 0.3
    # the warm bulbs overhead pool on the boards; the stage tints the lawn far away
    for bx in BULB_ROWS:
        for bz in (380, 560, 740):
            warm_light(rgb, np.hypot((X - bx) * 0.8, (Z - bz) * 0.6), 120, strength=0.36)
    warm_light(rgb, np.hypot(X * 0.4, (Z - Z_STAGE) * 0.25), 260, colour="#e8a0c0", strength=0.5)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 1200, 3800, amount=0.85)
    return out


def ceiling_shader(X, Z):
    """Underside of the striped canvas: bands running toward the front, frame purlins, ridge."""
    band = (np.floor((X + 25) / 50) % 2).astype(int)
    red, cream = pal_array(F.RED), pal_array(F.CANVAS)
    rgb = np.where(band[:, None] == 0, red[2], cream[3]).astype(np.float32)
    # lit from the bulbs strung below it: warm near the strings, dimmer toward the walls and
    # overhead where the camera stands
    edge = np.clip(np.abs(X) / WALL_X, 0, 1)
    near = np.clip((Z - 120) / 360, 0, 1)
    rgb = rgb * (0.62 + 0.36 * near[:, None] - 0.30 * edge[:, None])
    glow = np.exp(-((np.abs(X) - 120) / 70) ** 2)
    rgb = rgb + (pal_array([F.BULB[1]])[0] - rgb) * (0.18 * glow * near)[:, None]
    seam = np.abs(((X + 25) % 50) - 0) < 1.5
    rgb[seam] = rgb[seam] * 0.72
    # the canvas sags a little between purlins: a soft shadow just behind each bar
    zz = np.mod(Z, 180)
    rgb[(zz > 5) & (zz < 22)] *= 0.9
    purlin = zz < 5
    rgb[purlin] = pal_array(F.STEEL)[3] * 0.8
    ridge = np.abs(X) < 4
    rgb[ridge] = pal_array(F.STEEL)[3]
    out = rgba_of(rgb)
    out[(Z > Z_FRONT) | (np.abs(X) > WALL_X), 3] = 0
    return out


def wall_texture(length, height, seed=0, right=False):
    """The canvas side wall laid out from the camera toward the front (u = depth)."""
    cv = Canvas(length, height, seed=seed)
    pal = F.CANVAS
    F.canvas_wall(cv, 0, 0, length, height, pal=[shade(c, -0.08) for c in pal], seed=seed, panel=60)
    # warm light from the bulbs on the upper wall
    cv.rect(0, 0, length, 30, C(F.BULB[2], 0.12))
    for wx in range(60, length - 40, 150):
        F.pvc_window(cv, wx, 30, 40, 64, lit=False)
    cv.rect(0, height - 18, length, 18, C("#3a2a30", 0.4))   # damp hem
    return cv.a


def wall_shader(tex, flip):
    h, w = tex.shape[:2]
    def shade_(u, Y, Z):
        o = texture_lookup(tex, u if not flip else u, EAVE - Y, wrap=False)
        return fog(o, Z, HAZE, 1200, 3800, amount=0.5)
    return shade_


def valance_texture(width=600, height=20):
    cv = Canvas(width, height + 6)
    F.scallop_valance(cv, 0, 0, width, depth=height - 4, pal_a=F.RED, pal_b=F.CANVAS, stripe=16)
    return cv.a


def stage_flat():
    w, h = 150, 56
    cv = Canvas(w + 70, h + 50)
    cx, base = (w + 70) // 2, h + 46
    pts = F.distant_stage(cv, cx, base, w=w, h=h, seed=9)
    return cv, pts, cx, base


def vest_rack(h_px):
    """The vest rack with three hi-vis vests on hangers, at its on-screen size."""
    s = h_px / 44.0
    cv = Canvas(int(60 * s) + 6, h_px + 4)
    base = h_px + 2
    w = cv.w - 6
    top = base - h_px
    cv.rect(2, top, w + 2, 3, OUT); cv.hline(3, top + 1, w, F.STEEL[4])
    for sx in (2, w):
        cv.rect(sx, top, 3, h_px, OUT); cv.vline(sx + 1, top + 1, h_px - 2, F.STEEL[3])
        cv.rect(sx - 4, base - 2, 11, 3, OUT); cv.hline(sx - 3, base - 1, 9, F.STEEL[2])
    cols = [("#d8e040", "#a8b02a", "#eef27a"), ("#f0a030", "#c07020", "#f8c870"), ("#d8e040", "#a8b02a", "#eef27a")]
    for k in range(3):
        vw, vh = max(9, int(14 * s)), max(12, int(20 * s))
        vx = 6 + int((4 + k * 16) * s)
        vy = top + 4
        mid, dark, lite = cols[k]
        cx = vx + vw // 2
        cv.vline(cx, top + 1, 3, OUT)                                   # hanger hook
        cv.hline(cx - vw // 3, vy, 2 * (vw // 3) + 1, OUT)              # hanger bar
        # vest body: shoulders, armholes cut in, V neck, straight hem
        pts = [(vx + 1, vy + 1), (cx - 2, vy + 1), (cx, vy + vh // 3), (cx + 2, vy + 1), (vx + vw - 1, vy + 1),
               (vx + vw - 1, vy + 3), (vx + vw - 3, vy + vh // 3 + 1), (vx + vw - 2, vy + vh), (vx + 1, vy + vh),
               (vx + 2, vy + vh // 3 + 1), (vx + 1, vy + 3)]
        cv.poly([(x + dx, y + dy) for (x, y) in pts for dx, dy in [(0, 0)]], OUT)
        inner = [(vx + 2, vy + 2), (cx - 2, vy + 2), (cx, vy + vh // 3 + 1), (cx + 2, vy + 2), (vx + vw - 2, vy + 2),
                 (vx + vw - 4, vy + vh // 3 + 1), (vx + vw - 3, vy + vh - 1), (vx + 2, vy + vh - 1), (vx + 3, vy + vh // 3 + 1)]
        cv.poly(inner, mid)
        cv.vline(vx + 2, vy + vh // 3 + 2, vh - vh // 3 - 3, lite)
        cv.vline(vx + vw - 3, vy + vh // 3 + 2, vh - vh // 3 - 3, dark)
        cv.vline(cx, vy + vh // 3 + 1, vh - vh // 3 - 2, dark)          # the zip
        for yy in (vy + vh // 2 + 1, vy + vh - 4):
            cv.hline(vx + 2, yy, vw - 4, F.REFLECT[2])
            cv.hline(vx + 2, yy + 1, vw - 4, F.REFLECT[1])
    return cv.a


def crew_table(h_px):
    """The crew table end-on: urn, mugs, a row of radios charging (one LED red), first-aid box."""
    s = h_px / 40.0
    W_ = int(110 * s)
    cv = Canvas(W_ + 6, h_px + 4)
    base = h_px + 2
    top = base - int(22 * s)
    cv.rect(2, top, W_, max(3, int(4 * s)), OUT); cv.hline(3, top + 1, W_ - 2, F.PLY[4])
    cv.rect(3, top + int(4 * s), W_ - 2, int(10 * s), C("#120e18", 0.6))
    for lx in (4, W_ - 2):
        cv.rect(lx, top, max(2, int(3 * s)), base - top, OUT)
    ux = 6
    cv.rect(ux, top - int(16 * s), int(10 * s), int(16 * s), OUT); cv.rect(ux + 1, top - int(15 * s), int(8 * s), int(14 * s), F.STEEL[4])
    radios = []
    for k in range(4):
        rx = int((30 + k * 9) * s)
        rw, rh = max(3, int(6 * s)), max(5, int(9 * s))
        cv.rect(rx, top - rh, rw, rh, OUT); cv.rect(rx + 1, top - rh + 1, rw - 2, rh - 2, "#2a2832")
        cv.vline(rx + rw - 2, top - rh - int(5 * s), int(5 * s), OUT)
        led = (rx + 1, top - rh + 2)
        cv.px(led[0], led[1], "#5cf08a" if k != 1 else "#7a2a24")
        radios.append(led)
    fx = int(72 * s)
    cv.rect(fx, top - int(9 * s), int(14 * s), int(9 * s), OUT); cv.rect(fx + 1, top - int(8 * s), int(12 * s), int(7 * s), "#e6e2d8")
    cv.rect(fx + int(6 * s), top - int(7 * s), 2, int(5 * s), "#c84a3c"); cv.rect(fx + int(4 * s), top - int(5 * s), int(6 * s), 2, "#c84a3c")
    for k, c in enumerate(["#c84a3c", "#e6d6b1", "#425da6"]):
        mx = int((92 + k * 6) * s)
        cv.rect(mx, top - int(5 * s), max(3, int(5 * s)), max(3, int(5 * s)), OUT); cv.rect(mx + 1, top - int(5 * s) + 1, max(1, int(5 * s) - 2), max(1, int(5 * s) - 2), c)
    return cv.a, radios[1]


def canvas_heap(cv, x, base, w, h):
    """A heap of wet striped canvas dragged in out of the rain: lumpy folds, red bands, a dark
    damp underside and a puddle spreading out from under it."""
    def el(cx, cy, rx, ry, c):
        cv.ellipse(cx - rx, cy - ry, 2 * rx + 1, 2 * ry + 1, c)
    el(x + w // 2, base - 1, w // 2 + 2, 3, C("#3a3458", 0.8))
    lumps = [(0.2, 0.55, 0.22), (0.45, 1.0, 0.26), (0.72, 0.7, 0.24), (0.9, 0.35, 0.14)]
    for fx, fh, fr in lumps:
        cx, cy = x + int(w * fx), base - int(h * fh * 0.5)
        rx, ry = max(3, int(w * fr)), max(2, int(h * fh * 0.55))
        el(cx, cy, rx + 1, ry + 1, OUT)
    for i, (fx, fh, fr) in enumerate(lumps):
        cx, cy = x + int(w * fx), base - int(h * fh * 0.5)
        rx, ry = max(3, int(w * fr)), max(2, int(h * fh * 0.55))
        pal = F.CANVAS if i % 2 == 0 else F.RED
        el(cx, cy, rx, ry, pal[2])
        el(cx - rx // 4, cy - ry // 3, max(1, rx * 2 // 3), max(1, ry // 2), pal[3])
        cv.hline(cx - rx // 2, cy - ry + 1, max(1, rx // 2), pal[4])
        cv.line(cx - rx + 2, cy + ry // 2, cx + rx // 2, cy - ry // 3, pal[1])   # a fold
    cv.rect(x + 1, base - 2, w, 2, shade(F.CANVAS[1], -0.2))


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    v = View(horizon=98, cam=52, fill="#1b1830")
    pw = flatirons_panel(scale=2.4).shape[1]
    sky, _ = F.farrand_sky(640, 132, panels=(1, 0, 1), offset=pw - (320 - pw // 2), scale=2.4, stars=30, seed=8)
    v.strip(sky, 0, solid=False)
    v.strip(F.field_treeline(640, 34, seed=5, open_span=(270, 370)), 98 - 34 + 7)
    v.ground(floor_shader)

    # outside, far to near: the stage, its towers
    st, stage_pts, scx, sbase = stage_flat()
    sx0 = int(round(v.vx - scx))
    sy0 = int(round(v.ground_y(Z_STAGE) - sbase))
    for tx in (-640, 640):
        th = int(round(250 * v.scale(2600)))
        tw = Canvas(16, th + 8)
        F.light_tower(tw, 4, th + 6, th, seed=int(tx > 0))
        v.sprite(tw.a, tx, 2600, scale=2600 / v.F)
    v.strip(st.a, sy0, sx0)

    # other tents across the field, lit inside, and a string of lights between them
    def stall_inside(cv_, x, y, w, h):
        cv_.rect(x, y, w, h, "#3a2a2a")
        F.light_pool(cv_, x + w // 2, y + h // 2, w // 2, h // 2, F.BULB[1], 0.45)
        cv_.rect(x + 4, y + h - 14, w - 8, 3, OUT); cv_.rect(x + 4, y + h - 13, w - 8, 1, F.PLY[4])
        cv_.rect(x + 4, y + h - 11, w - 8, 11, F.PLY[1])
        for k in range(3):
            cv_.rect(x + 10 + k * (w - 20) // 3, y + h - 20, 7, 6, ["#c84a3c", "#e6d6b1", "#425da6"][k])
    for (tx, tz, tw_, sd) in ((-520.0, 1500.0, 130, 21), (540.0, 1750.0, 150, 22)):
        tent, tax, tay = F.peaked_tent(tw_, 52, 30, open_front=True, seed=sd, interior=stall_inside,
                                       stripe=F.TEAL_C if sd == 22 else F.RED)
        v.sprite(tent.a, tx, tz, anchor=(tax / tent.w, tay / tent.h), scale=ROOM_TO_BATTLE)
    outside = Canvas(640, 360)
    o_pts = []
    for (a, b) in (((-760.0, 1300.0), (0.0, 1300.0)), ((0.0, 1300.0), (760.0, 1300.0))):
        p0 = v.project(a[0], 118, a[1]); p1 = v.project(b[0], 118, b[1])
        o_pts += F.string_across(outside, p0, p1, sag=7, every=6, seed=int(a[0] + 900))
    v.strip(outside.a, 0, 0)

    # the tent: walls, ceiling, valance and front poles
    L = int(Z_FRONT - 120)
    for side in (-1, 1):
        tex = wall_texture(L, int(EAVE), seed=side + 4)
        v.plane((side * WALL_X, 120.0), (side * WALL_X, Z_FRONT), wall_shader(tex, side > 0), y_max=EAVE)
    v.ground(ceiling_shader, y_from=-1, y_to=v.h0 - 0.01, height=EAVE)
    val = valance_texture(int(2 * WALL_X), 20)
    vh = val.shape[0]
    v.back(Z_FRONT, lambda X, Y: texture_lookup(val, X + WALL_X, (EAVE - Y), wrap=False),
           region=lambda X, Y: (np.abs(X) < WALL_X) & (Y > EAVE - vh) & (Y <= EAVE))
    for px_ in (-WALL_X, -WALL_X / 3, WALL_X / 3, WALL_X):
        h = int(round((EAVE - 8) * v.scale(Z_FRONT)))
        pole = Canvas(4, h + 2)
        pole.rect(0, 0, 4, h + 2, OUT); pole.vline(1, 0, h + 1, F.STEEL[4]); pole.vline(2, 0, h + 1, F.STEEL[3])
        v.sprite(pole.a, px_, Z_FRONT, scale=Z_FRONT / v.F)

    # gear along the walls, far to near
    items = []
    radio_led = None
    table_z = 560.0
    th = int(round(40 * ROOM_TO_BATTLE * v.scale(table_z)))
    table, led = crew_table(th)
    items.append((table_z, "table", (WALL_X - 70, table, led)))
    items.append((640.0, "rack", -WALL_X + 60))
    items.append((470.0, "chairs", WALL_X - 50))
    items.append((700.0, "chairs", WALL_X - 40))
    items.append((420.0, "water", -WALL_X + 50))
    items.append((520.0, "heap", -WALL_X + 110))
    for z, kind, data in sorted(items, key=lambda t: -t[0]):
        s = v.scale(z)
        if kind == "table":
            x, spr, led = data
            sx, sy, _ = v.sprite(spr, x, z, anchor=(0.5, 1.0), scale=z / v.F)
            radio_led = (int(round(sx - spr.shape[1] / 2 + led[0])), int(round(sy - spr.shape[0] + led[1])))
        elif kind == "rack":
            spr = vest_rack(int(round(44 * ROOM_TO_BATTLE * s)))
            v.sprite(spr, data, z, scale=z / v.F)
        elif kind == "chairs":
            hh = int(round(38 * ROOM_TO_BATTLE * s))
            cv_ = Canvas(int(hh * 0.8) + 8, hh + 4)
            F.chair_stack(cv_, 2, hh + 2, n=7, w=max(8, int(hh * 0.5)))
            F.chair_stack(cv_, 4 + int(hh * 0.25), hh + 2, n=5, w=max(8, int(hh * 0.5)))
            v.sprite(cv_.a, data, z, scale=z / v.F)
        elif kind == "water":
            hh = int(round(30 * ROOM_TO_BATTLE * s))
            cv_ = Canvas(hh * 2, hh + 4)
            for k in range(3):
                F.crate(cv_, 2 + (k % 2) * 3, hh + 2 - k * max(6, hh // 3), max(12, hh), max(6, hh // 3), F.TEAL_C)
            F.cooler(cv_, max(14, hh) + 6, hh + 2, max(12, hh // 1), max(8, hh // 2))
            v.sprite(cv_.a, data, z, scale=z / v.F)
        elif kind == "heap":
            hh = int(round(14 * ROOM_TO_BATTLE * s)); ww = int(round(50 * ROOM_TO_BATTLE * s))
            cv_ = Canvas(ww + 6, hh + 6)
            canvas_heap(cv_, 2, hh + 4, ww, hh)
            v.sprite(cv_.a, data, z, scale=z / v.F)

    v.rows(156, 360, INK, 0.0, 0.6)
    cv = v.reduce(112)

    # crisp string lights along the ceiling, from overhead to the front
    twinkles = []
    for bx in BULB_ROWS:
        zs = [180, 300, 420, 540, 660, Z_FRONT - 10]
        for i in range(len(zs) - 1):
            p0 = v.project(bx, EAVE - 2, zs[i])
            p1 = v.project(bx, EAVE - 2, zs[i + 1])
            depth = (zs[i] + zs[i + 1]) / 2
            twinkles += F.string_across(cv, p0, p1, sag=max(2, int(9 * v.scale(depth))), every=max(4, int(16 * v.scale(depth))), seed=int(bx) + i)
    # a work lamp hanging from the ridge over the fight
    lx, ly = v.project(0, EAVE - 30, 520)
    lx, ly = int(round(lx)), int(round(ly))
    top_y = int(round(v.project(0, EAVE, 520)[1]))
    cv.vline(lx, top_y, ly - top_y, F.WIRE)
    cv.rect(lx - 3, ly, 7, 3, OUT); cv.rect(lx - 2, ly + 3, 5, 2, F.BULB[3]); cv.rect(lx - 5, ly + 2, 11, 6, C(F.BULB[2], 0.15))
    lamp = [[lx, ly + 4, "fff0c4", 2]]
    # only the outside bulbs that are actually seen through the opening
    def seen(pt):
        x, y = int(pt[0]), int(pt[1])
        if not (0 <= x < cv.w and 0 <= y < cv.h):
            return False
        want = np.array([int(pt[2][i:i + 2], 16) / 255 for i in (0, 2, 4)])
        return float(np.abs(cv.a[y, x, :3] - want).max()) < 0.14
    twinkles += [p for p in o_pts if seen(p)]
    stage_lamps = [[sx0 + p[0], sy0 + p[1], "f6dca0", 1] for p in stage_pts]

    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = v.solid_mask().astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))

    res = f"res://assets/art/rooms/{ROOM}/"
    beam_y = sy0 + sbase - 56 + 2
    layers = [
        {"kind": "beam", "depth": "far", "x": 304, "y": beam_y, "angle": -102, "sweep": 16, "period": 8.5, "phase": 0.5,
         "length": 90, "width": 18, "color": "c8b0ff", "alpha": 0.22, "floor": -400},
        {"kind": "beam", "depth": "far", "x": 336, "y": beam_y, "angle": -78, "sweep": 16, "period": 10.0, "phase": 2.5,
         "length": 90, "width": 18, "color": "ffc8e0", "alpha": 0.22, "floor": -400},
        {"kind": "fauna", "depth": "far", "fauna": [{"kind": "bat", "x": 260, "y": 68, "fly": 9.0, "rate": 7.0}]},
        {"kind": "twinkle", "points": twinkles, "rate": 2.0, "min": 0.4},
        {"kind": "twinkle", "points": lamp + stage_lamps, "rate": 1.1, "min": 0.6},
        {"kind": "particles", "style": "dust", "count": 14, "rect": [lx - 40, ly - 4, 80, 60], "speed": [0, 5], "color": "f6e0b0"},
        {"kind": "particles", "style": "wind", "count": 3, "rect": [200, 70, 240, 50], "speed": [200, 0]},
    ]
    if radio_led:
        layers.append({"kind": "blink", "pattern": "10100000", "rate": 6.0,
                       "rects": [[radio_led[0], radio_led[1], 1, 1, "ff5a4a"], [radio_led[0] - 1, radio_led[1] - 1, 3, 3, "ff5a4a", 0.35]]})
    return {"far": res + "battle-far.png", "near": res + "battle-near.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
