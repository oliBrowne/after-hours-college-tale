"""Battle backdrop for backstage (F05): standing on the crew road, looking along it to the stage.
On the left the site cabins run away in a row (GREEN ROOM with its door open on a warm room, the
generator with the cat asleep on it, PRODUCTION), on the right the stage's side towers up in
black scrim and scaffold with the show's light leaking through the seams. At the end of the road
the flight-case stairs climb into the wings, washed pink and violet, the cue light beside them;
over the cabins the volunteer tent's striped roof and the dusk. Kit waits along the stage wall:
the gear rack, the backline cases, the ONE SONG cue board. Festoons hang across the road."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from pixel import Canvas, C, text, text_width
from props import OUT
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
import lib_farrand as F
import lib_farrand2 as G

ROOM = "F05"
INK = "#10121e"
HAZE = "#2e2438"
ROAD_HALF = 96.0           # the trackway road, 192 units wide
CABIN_X = -190.0           # face of the cabin row (left wall)
CABIN_Z = (300.0, 1020.0)
STAGE_X = 176.0            # face of the stage's side scaffold (right wall)
Z_END = 900.0              # the stage's back wall across the end of the road
WING_X = (-50.0, 50.0)     # the opening into the wings in the end wall
STAGE_TOP = 520.0          # the side wall climbs off the top of the screen
CABIN_TEX_H = 100          # cabin row texture height in room px (1.7 world units each)
FENCE_H = 99.0             # the scrim fence before the cabins (58 room px)


def ground_shader(X, Z):
    rgb = F.battle_grass_rgb(X, Z, stripe=1e6, seed=7)
    dirt = pal_array(F.DIRT)
    tone = hash2(np.floor(X / 9), np.floor(Z / 9), 4)
    worn = (np.abs(X) < ROAD_HALF + 30) | (X > STAGE_X - 40)
    rgb[worn] = rgb[worn] * 0.6 + (dirt[2] * 0.6 + dirt[3] * 0.4 * tone[worn, None]) * 0.4
    # aluminium trackway: panels 110 long, ribs across the travel, hinge joints, mud
    road = np.abs(X) < ROAD_HALF
    t = pal_array(G.TRACK)
    col = np.floor((X + ROAD_HALF) / (ROAD_HALF / 2))
    seg = np.floor((Z + (col % 2) * 55) / 110)
    pt = hash2(col, seg, 6)
    trk = t[3] * (1 - pt[:, None] * 0.5) + t[4] * (pt[:, None] * 0.5)
    rib = np.mod(Z, 6.0) < 1.6
    trk[rib] = trk[rib] * 0.7 + t[5] * 0.3
    trk[(np.mod(Z, 6.0) >= 1.6) & (np.mod(Z, 6.0) < 2.6)] *= 0.88
    fz = (Z + (col % 2) * 55) / 110 - seg
    fx = (X + ROAD_HALF) / (ROAD_HALF / 2) - col
    trk[(fz < 0.025) | (fx < 0.03)] = t[0]
    knuckle = (fz < 0.04) & (np.mod(X, 16) < 4)
    trk[knuckle] = t[5]
    mud = hash2(np.floor(X / 10), np.floor(Z / 22), 9) > 0.93
    trk[mud] = trk[mud] * 0.75 + dirt[2] * 0.25
    rgb[road] = trk[road]
    rgb[road & (np.abs(X) > ROAD_HALF - 2)] = t[0]
    # cable looms along the foot of the stage wall and across the road under a ramp
    for k, off in enumerate((-30, -26, -22, -18)):
        line = np.abs(X - (STAGE_X + off + 1.5 * np.sin(Z / (31 + 5 * k)))) < 1.1
        rgb[line] = pal_array(["#1e1c24", "#2a2832", "#7a3a2a", "#3a3a52"])[k]
    zr = 610.0
    dz = np.abs(Z - zr)
    ramp = (dz < 9) & (np.abs(X) < ROAD_HALF + 10)
    hz = pal_array(F.HAZARD)
    rgb[ramp] = hz[1]
    rgb[ramp & (dz < 3.5)] = hz[3]
    rgb[ramp & (dz < 3.5) & (np.mod(X, 18) < 2)] = hz[2]
    rgb[ramp & (Z < zr - 7)] = hz[0]
    for (cx, cz) in [(40, 430), (-60, 760)]:                            # gaffer tape arrows to the wings
        shaft = (np.abs(X - cx) < 3) & (Z > cz) & (Z < cz + 30)
        head = (Z >= cz + 30) & (Z < cz + 46) & (np.abs(X - cx) < (cz + 46 - Z) * 0.6)
        rgb[shaft | head] = pal_array(["#e8e4d8"])[0]
    # puddle catching the wing light
    d = np.hypot((X - 60) / 34, (Z - 520) / 26) + 0.25 * (hash2(np.floor(X / 6), np.floor(Z / 6), 2) - 0.5)
    water = d < 1
    rgb[water] = pal_array(["#4a3a68"])[0]
    rgb[water & (np.abs(X - 60 - (Z - 520) * 0.2) < 6)] = pal_array(["#d08ab8"])[0]
    # light: the wings' wash pouring out along the road, cabin doors, the work light
    warm_light(rgb, np.hypot(X * 0.9, (Z - Z_END) * 0.45), 300, colour="#f0a0c8", strength=0.42)
    warm_light(rgb, np.hypot(X * 1.4, (Z - Z_END) * 0.9), 120, colour="#c8a0f0", strength=0.3)
    for (lx, lz, r) in [(CABIN_X + 30, 452, 80), (CABIN_X + 30, 790, 60)]:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.6), r, strength=0.36)
    warm_light(rgb, np.hypot(X + 20, (Z - 690) * 0.7), 80, colour="#fff0c4", strength=0.3)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 900, 2600, amount=0.7)
    return out


def cabin_row():
    """The cabin row as a texture at room scale, u along the row from the camera's end."""
    L = int((CABIN_Z[1] - CABIN_Z[0]) / ROOM_TO_BATTLE)
    cv = Canvas(L, CABIN_TEX_H, seed=8)
    base = CABIN_TEX_H - 1
    info = {}
    info["green"] = G.portacabin(cv, 8, base, 168, 76, "GREEN ROOM", seed=1, door_x=18, door_open=True,
                                 windows=[(110, 24), (138, 24)], notices=1)
    info["gen"] = G.generator(cv, 182, base, w=60, h=30, label="GEN3")
    info["prod"] = G.portacabin(cv, 248, base, 150, 76, "PROD", seed=2, door_x=8, ac=True, notices=2)
    cv.a[:, :, 3] = np.where(cv.a[:, :, 3] > 0.5, 1.0, 0.0)
    return cv, info


def wall_shader(tex, flip=False, length=None):
    def shade_(u, Y, Z):
        uu = (length - u) if flip else u
        o = texture_lookup(tex, uu / ROOM_TO_BATTLE, (CABIN_TEX_H * ROOM_TO_BATTLE - Y) / ROOM_TO_BATTLE, wrap=False)
        return fog(o, Z, HAZE, 900, 2600, amount=0.7)
    return shade_


def fence_shader(u, Y, Z):
    """The crew fence in front of the cabins: black scrim on heras panels, posts on rubber feet."""
    sc = pal_array(G.SCRIM)
    st = pal_array(F.STEEL)
    rgb = np.where(((np.floor(u / 2.4) + np.floor(Y / 2.4)) % 3 == 0)[:, None], sc[3], sc[2])
    post = np.mod(u, 156.0) < 6
    rgb[post] = st[4]
    rgb[post & (np.mod(u, 156.0) > 3.5)] = st[2]
    rgb[(Y > FENCE_H - 5)] = st[4]
    rgb[(Y < 8) & (np.mod(u + 10, 156.0) < 26)] = pal_array(["#3a3644"])[0]
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 900, 2600, amount=0.7)
    return out


def stage_side_shader(u, Y, Z):
    """Black scrim on the scaffold, standards and ledgers, pink leaking through the seams."""
    n = u.shape[0]
    sc = pal_array(G.SCRIM)
    tr = pal_array(G.TRUSS)
    rgb = np.where(((np.floor(u / 2.4) + np.floor(Y / 2.4)) % 3 == 0)[:, None], sc[4], sc[3])
    std = np.mod(u, 96.0)
    rgb[std < 4] = tr[5]
    rgb[(std >= 4) & (std < 5.5)] = tr[1]
    leak = (std >= 5.5) & (std < 7.5) & (Y < 380)
    t = np.clip(Y / 380, 0, 1)
    pink = pal_array(["#f0a0c8"])[0]
    rgb[leak] = rgb[leak] * (0.45 + 0.3 * t[leak, None]) + pink * (0.55 - 0.3 * t[leak, None])
    led = np.mod(Y, 70.0)
    rgb[(led < 3) & (std >= 4)] = tr[4]
    brace = np.abs(np.mod(u + Y * 1.0, 192.0) - 96) < 1.6
    rgb[brace & (std >= 4)] = tr[3]
    # the deck's skirt along the bottom, its lit lip
    rgb[Y < 66] = np.where(((np.floor(u / 8)) % 2 == 0)[Y < 66, None], pal_array(G.SKIRT)[1], pal_array(G.SKIRT)[2])
    rgb[(Y >= 64) & (Y < 68)] = pal_array(G.LIP)[2]
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 900, 2600, amount=0.7)
    return out


def end_wall():
    """The stage's back wall across the end of the road, at room scale: scrim on scaffold, the
    opening into the wings with flight-case stairs climbing into the pink wash, the cue light, the
    SHOW ON box, the roof truss crossing at the top. Returns (Canvas, info) with anchor at
    bottom-left = world X -60 at Z_END."""
    w = int((STAGE_X - (-60)) / ROOM_TO_BATTLE) + 2
    h = int(STAGE_TOP / ROOM_TO_BATTLE)
    cv = Canvas(w, h, seed=9)
    base = h - 1
    for x in range(w):
        for y in range(0, base - 38):
            cv.px(x, y, G.SCRIM[3] if (x + y) % 3 else G.SCRIM[4])
    for sx in range(4, w, 34):
        cv.rect(sx - 1, 0, 2, base - 38, G.TRUSS[5]); cv.vline(sx + 1, 0, base - 38, G.TRUSS[1])
        for yy in range(0, base - 38):
            cv.px(sx + 3, yy, C("#f0a0c8", 0.35))
    for ly in range(base - 60, 0, -24):
        cv.hline(0, ly, w, G.TRUSS[4]); cv.hline(0, ly + 1, w, G.TRUSS[1])
    # a bay of scrim rolled up on the back of the LED wall above the wings
    ox0 = int((WING_X[0] + 60) / ROOM_TO_BATTLE)
    ox1 = int((WING_X[1] + 60) / ROOM_TO_BATTLE)
    lx0, lx1, ly0, ly1 = ox0 - 6, ox1 + 34, base - 38 - 46 - 92, base - 38 - 46 - 14
    cv.rect(lx0 - 2, ly0 - 6, lx1 - lx0 + 4, 7, OUT)
    for x in range(lx0 - 1, lx1 + 1):
        cv.vline(x, ly0 - 5, 5, G.SCRIM[3] if x % 4 else G.SCRIM[1])
    cv.rect(lx0, ly0, lx1 - lx0, ly1 - ly0, "#2a1830")
    for k, (col, a) in enumerate([("#f2a0c8", 0.55), ("#c8a0f0", 0.45), ("#fff0c4", 0.35)]):
        cv.rect(lx0 + k, ly0 + k, lx1 - lx0 - 2 * k, 2, C(col, a))
        cv.rect(lx0 + k, ly0, 2, ly1 - ly0, C(col, a * 0.6)); cv.rect(lx1 - 2 - k, ly0, 2, ly1 - ly0, C(col, a * 0.6))
    leds = []
    for cy in range(ly0 + 5, ly1 - 10, 12):
        for cx in range(lx0 + 5, lx1 - 14, 12):
            cv.rect(cx, cy, 11, 11, "#3a3a44"); cv.hline(cx, cy, 11, "#55525e"); cv.vline(cx + 10, cy, 11, "#24222c")
            cv.rect(cx + 3, cy + 3, 5, 4, "#2a2a32"); cv.px(cx + 8, cy + 8, "#5cf08a")
            leds.append((cx + 8, cy + 8))
    for k, lx in enumerate(range(lx0 + 9, lx1 - 14, 12)):
        cv.line(lx, ly0 + 2, lx + 3, ly1, "#2a4a8a" if k % 2 else "#1e1c24")
    # deck skirt and lip
    cv.rect(0, base - 38, w, 39, G.SKIRT[1])
    for sx in range(1, w, 5):
        cv.vline(sx, base - 35, 34, G.SKIRT[2])
    cv.hline(0, base - 38, w, G.LIP[2]); cv.hline(0, base - 37, w, G.LIP[0])
    # the wings opening, washed pink and violet
    ox0 = int((WING_X[0] + 60) / ROOM_TO_BATTLE)
    ox1 = int((WING_X[1] + 60) / ROOM_TO_BATTLE)
    oy0 = base - 38 - 46
    cv.rect(ox0 - 2, oy0 - 2, ox1 - ox0 + 4, base - oy0 + 2, OUT)
    bands = G.WASH[2:]
    for y in range(oy0, base - 38):
        t = (y - oy0) / max(1, base - 38 - oy0)
        cv.hline(ox0, y, ox1 - ox0, bands[min(len(bands) - 1, int(t * len(bands)))])
    for k in range(3):                                           # a lamp and a mic stand inside
        cv.vline(ox0 + 10 + k * 18, oy0 + 6, 3, G.TRUSS[2])
    cv.vline(ox1 - 14, oy0 + 16, base - 38 - oy0 - 16, G.TRUSS[1]); cv.line(ox1 - 14, oy0 + 16, ox1 - 20, oy0 + 12, G.TRUSS[1])
    # flight-case stairs up from the road into the wings
    steps = 4
    for k in range(steps):
        sy = base - (k + 1) * 9
        sx0 = ox0 + 2 + k * 2
        sw = ox1 - ox0 - 4 - k * 4
        cv.rect(sx0 - 1, sy - 1, sw + 2, 10, OUT); cv.rect(sx0, sy, sw, 9, G.CASE[2]); cv.hline(sx0, sy, sw, G.CASE[5])
        cv.hline(sx0, sy + 1, sw, G.CASE[4])
        for (bx, by) in [(sx0, sy + 6), (sx0 + sw - 3, sy + 6)]:
            cv.rect(bx, by, 3, 3, G.CASE[5])
        cv.hline(sx0 + 4, sy + 1, sw - 8, F.HAZARD[3])
    for hx in (ox0 - 1, ox1):                                    # handrails
        cv.line(hx, base - 4, hx, base - 4 * 9 - 20, G.TRUSS[5])
    red, green = G.cue_light(cv, ox1 + 6, oy0 + 4)
    sw_ = text_width("SHOW ON") + 8
    cv.rect(ox1 + 18, oy0 - 2, sw_ + 2, 13, OUT); cv.rect(ox1 + 19, oy0 - 1, sw_, 11, "#c8382c")
    cv.hline(ox1 + 19, oy0 - 1, sw_, "#f06a5a"); text(cv, "SHOW ON", ox1 + 23, oy0 - 1, "#ffe8d8")
    # roof truss crossing the top
    arch = lambda x: 6 + int(10 * (x / w))
    G.truss_band(cv, 0, w, arch, 11)
    lamps = []
    for i, lx in enumerate(range(10, w - 6, 22)):
        lens = G.stage_lamp(cv, lx, arch(lx) + 11, G.LAMP_COLOURS[i % len(G.LAMP_COLOURS)], "par", on=True)
        lamps.append((lens[0], lens[1], G.LAMP_COLOURS[i % len(G.LAMP_COLOURS)].lstrip("#")))
    return cv, {"red": red, "green": green, "lamps": lamps, "base": base, "wing": (ox0, oy0, ox1, base - 38), "leds": leds}


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    v = View(horizon=98, cam=52, fill="#1b1830")
    sky, _ = F.farrand_sky(640, 132, panels=(0, 1, 0, 1), offset=120, scale=1.9, stars=34, seed=12)
    v.strip(sky, 0, solid=False)
    v.strip(F.field_treeline(640, 34, seed=8, open_span=(700, 800)), 98 - 34 + 4)
    v.ground(ground_shader)

    # beyond the cabins: the perimeter fence and the volunteer tent's roof
    tent, tax, tay = F.peaked_tent(196, 72, 40, open_front=False, seed=4, valance_text=None, ropes=False,
                                   poles=[0, 64, 129, 193])
    v.sprite(tent.a, -120, 1500, anchor=(tax / tent.w, tay / tent.h), scale=ROOM_TO_BATTLE)
    fence = Canvas(300, 64)
    G.scrim_fence(fence, 0, 300, 63, height=58, panel=92, seed=3, signs=[(120, "CREW")])
    v.sprite(fence.a, -200, 1150, anchor=(0.5, 1.0), scale=ROOM_TO_BATTLE)

    # the stage's back wall across the end of the road, then its side wall on the right
    ew, einfo = end_wall()
    ex, ey, es = v.sprite(ew.a, -60, Z_END, anchor=(0.0, 1.0), scale=ROOM_TO_BATTLE)
    emap = lambda p: (ex + p[0] * es, ey - (ew.h - p[1]) * es)
    v.plane((STAGE_X, 100.0), (STAGE_X, Z_END), stage_side_shader, y_max=STAGE_TOP)
    v.plane((CABIN_X, 140.0), (CABIN_X, CABIN_Z[0] + 2), fence_shader, y_max=FENCE_H)

    # the cabin row on the left
    row, rinfo = cabin_row()
    L = CABIN_Z[1] - CABIN_Z[0]
    v.plane((CABIN_X, CABIN_Z[0]), (CABIN_X, CABIN_Z[1]), wall_shader(row.a), y_max=CABIN_TEX_H * ROOM_TO_BATTLE)
    rmap = lambda p: v.project(CABIN_X, (CABIN_TEX_H - p[1]) * ROOM_TO_BATTLE, CABIN_Z[0] + p[0] * ROOM_TO_BATTLE)

    # kit along the stage wall and by the stairs, the work light by the cabins
    for (x, z, w, h, pal, tape) in [(STAGE_X - 34, 520, 40, 22, G.CASE, "DI"), (STAGE_X - 30, 600, 52, 26, None, "DRUMS"),
                                     (STAGE_X - 36, 600, 30, 16, G.CASE, None)]:
        case = Canvas(w + 4, h + 12)
        G.road_case(case, 2, h + 10, w, h, top=4, pal=pal or ["#120c10", "#2a1218", "#4a1e24", "#6a2a30", "#8a3a3e", "#9a9aa4", "#d0d0d8"],
                    tape=tape)
        y_lift = 0 if tape != None or w > 40 else 26 * ROOM_TO_BATTLE
        v.sprite(case.a, x, z, Y=y_lift, anchor=(0.5, (h + 10) / (h + 12)), scale=ROOM_TO_BATTLE)
    cb, cbx, cby = G.cue_board(70, 42)
    v.sprite(cb.a, -120, 820, anchor=(cbx / cb.w, cby / cb.h), scale=ROOM_TO_BATTLE)
    wl, wlx, wly, head = G.work_light(55)
    wl_at = v.sprite(wl.a, -40, 680, anchor=(wlx / wl.w, wly / wl.h), scale=ROOM_TO_BATTLE)
    head_s = (wl_at[0] + (head[0] - wlx) * wl_at[2], wl_at[1] + (head[1] - wly) * wl_at[2])

    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp festoons from the cabin roofs across to the stage scaffold
    twinkles = []
    spans = [(CABIN_Z[0] + 60, 380.0), (CABIN_Z[0] + 360, 640.0), (CABIN_Z[0] + 560, 860.0)]
    for i, (zl, zr) in enumerate(spans):
        a = v.project(CABIN_X, CABIN_TEX_H * ROOM_TO_BATTLE + 2, zl)
        b = v.project(STAGE_X, 230.0, zr)
        sag = max(4, int(30 * v.scale((zl + zr) / 2)))
        twinkles += F.string_across(cv, a, b, sag=sag, every=max(5, int(14 * v.scale((zl + zr) / 2))), seed=i)

    pts = lambda m, lst, col, size=1: [[int(round(m(p)[0])), int(round(m(p)[1])), col, size] for p in lst]
    lamps = [[int(round(emap(p)[0])), int(round(emap(p)[1])), p[2], 1] for p in einfo["lamps"]]
    leds = [[int(round(emap(p)[0])), int(round(emap(p)[1])), "5cf08a", 1] for p in einfo["leds"]]
    win = pts(rmap, [rinfo["green"]["lamp"], rinfo["prod"]["lamp"]], "fff0c4")
    red, green = emap(einfo["red"]), emap(einfo["green"])
    ox0, oy0, ox1, oy1 = einfo["wing"]
    (wx0, wy0), (wx1, wy1) = emap((ox0, oy0)), emap((ox1, oy1))
    gen_led = rmap(rinfo["gen"]["led"])
    gen_top = rmap((182 + 30, CABIN_TEX_H - 1 - 34))
    exhaust = rmap(rinfo["gen"]["exhaust"])

    cv.save(os.path.join(out, "battle-far.png"))
    near = cv.a.copy()
    near[..., 3] = v.solid_mask().astype(np.float32)
    Image.fromarray((np.clip(near, 0, 1) * 255).round().astype(np.uint8), "RGBA").save(os.path.join(out, "battle-near.png"))
    res = f"res://assets/art/rooms/{ROOM}/"
    r = lambda x: int(round(x))
    return {
        "far": res + "battle-far.png",
        "near": res + "battle-near.png",
        "layers": [
            {"kind": "beam", "depth": "far", "x": r(emap((60, 20))[0]), "y": r(emap((60, 20))[1]), "angle": -100, "sweep": 14,
             "period": 9.0, "phase": 0.3, "length": 110, "width": 22, "color": "ffd0e8", "alpha": 0.16, "floor": -400},
            {"kind": "beam", "depth": "far", "x": r(emap((120, 24))[0]), "y": r(emap((120, 24))[1]), "angle": -76, "sweep": 16,
             "period": 7.5, "phase": 2.4, "length": 110, "width": 22, "color": "c8b0ff", "alpha": 0.16, "floor": -400},
            {"kind": "fauna", "depth": "far", "fauna": [
                {"kind": "bat", "x": 120, "y": 26, "fly": 14.0, "rate": 7.0}]},
            {"kind": "fauna", "fauna": [
                {"kind": "library_cat", "x": r(gen_top[0]), "y": r(gen_top[1]), "range": 0, "speed": 0.0, "rate": 0.5}]},
            {"kind": "blink", "pattern": "1100", "rate": 2.0, "rects": [[r(wx0), r(wy0), r(wx1 - wx0), r(wy1 - wy0), "f0a0c8", 0.16]]},
            {"kind": "blink", "pattern": "0011", "rate": 2.0, "rects": [[r(wx0), r(wy0), r(wx1 - wx0), r(wy1 - wy0), "a890f0", 0.14]]},
            {"kind": "blink", "pattern": "1111111000", "rate": 2.0, "rects": [[r(red[0]), r(red[1]), 3, 3, "ff4a3a"], [r(red[0]) - 2, r(red[1]) - 2, 7, 7, "ff4a3a", 0.25]]},
            {"kind": "blink", "pattern": "0000000110", "rate": 2.0, "rects": [[r(green[0]), r(green[1]), 3, 3, "5cf08a"], [r(green[0]) - 2, r(green[1]) - 2, 7, 7, "5cf08a", 0.25]]},
            {"kind": "blink", "pattern": "10", "rate": 0.8, "rects": [[r(gen_led[0]), r(gen_led[1]), 1, 1, "5cf08a"]]},
            {"kind": "twinkle", "points": twinkles, "rate": 1.8, "min": 0.4},
            {"kind": "twinkle", "points": lamps + win, "rate": 1.3, "min": 0.55},
            {"kind": "twinkle", "points": leds, "rate": 0.7, "min": 0.3},
            {"kind": "particles", "style": "dust", "count": 10, "rect": [r(head_s[0]) - 6, r(head_s[1]) - 4, 60, 34],
             "speed": [3, 3], "color": "fff0c4"},
            {"kind": "particles", "style": "dust", "count": 5, "rect": [r(exhaust[0]) - 3, r(exhaust[1]) - 18, 10, 16],
             "speed": [2, -7], "color": "8a8496"},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:400])
