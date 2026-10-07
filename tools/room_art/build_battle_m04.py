"""Battle backdrop for the orchestra pit (M04): from the stage, over the pit, into the house.

The room shows the pit looking up at the closed curtain; here the curtain is open and the camera
stands on the stage apron facing out, the fighters on the black stage boards. The house curtain's
gathered legs and gold-fringed border frame the view. At the stage edge a row of footlights glows;
past it the pit drops away: music stand lights, the harp's gilt head and the bass scroll peek over
the edge in front of the pit rail. Beyond, the empty house: rows of crimson seats rising toward
the back under the balcony, brass aisle lights, warm sconces and green EXIT signs on the side
walls, the gilded balcony front sweeping round in a horseshoe with its rail of bulbs, the balcony
rows above it, and at the back the projection booth where two follow spots wait.
Layers: the follow spots sweep the stage, the balcony bulbs chase, a red APPLAUSE sign hanging from
the balcony flashes on and off (the score that wants applause forever), lamps breathe, dust turns
in the beams, quavers drift up out of the pit."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON, WOOD
from lib_macky import (CURTAIN, BRASS, CHAIR, STAND_GLOW, PLASTER_M, CARPET_M, DRESS, SHADOW, _stand, _harp,
                       _double_bass)
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup

ROOM = "M04"
INK = "#10121e"
HOUSE = 700.0                     # side walls at X = -HOUSE and +HOUSE
EDGE = 420.0                      # the apron edge (stage floor ends here)
PIT_Z, PIT_Y = 560.0, -40.0       # the pit's far wall (audience side) and its floor height
RAIL_Y = 30.0                     # top of the pit rail
STALLS = [(640.0 + 52 * k, -24.0 + 10 * k) for k in range(15)]          # (Z, floor Y) of each stalls row
BAL_Z, BAL_LO, BAL_HI = 1100.0, 168.0, 214.0                              # balcony front (centre) and its face
BALCONY = [(1150.0 + 50 * k, BAL_HI + 18 * k) for k in range(9)]        # balcony rows
BACK_Z, SOFFIT_Z = 1600.0, 1400.0
CEIL = 500.0
LENSES = [(-380.0, 440.0), (370.0, 440.0)]    # follow spots in the booth (X, Y) on the back wall
NIGHT = (0.68, 0.72, 0.84)
HAZE = "#140e18"


def emissive(rgb):
    """Pixels that keep their full brightness at night: warm lamps, green EXIT, red lightbox."""
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    warm = (r > 0.55) & (r - b > 0.36) & (g - b > 0.2)
    green = (g > 0.6) & (g - r > 0.3)
    red = (r > 0.85) & (g < 0.45) & (b < 0.4)
    return warm | green | red


def grade(rgba, keep_glow=True):
    out = rgba.copy()
    m = ~emissive(out[..., :3]) if keep_glow else np.ones(out.shape[:-1], bool)
    out[m, :3] = out[m, :3] * np.array(NIGHT, np.float32)
    return out


def darken(rgba, k):
    out = rgba.copy()
    m = ~emissive(out[..., :3])
    out[m, :3] *= k
    return out


# --- painted pieces (world-unit scale unless noted) ---------------------------------------------
SEAT = ["#3a0e16", "#5a1620", "#7a1e28", "#982a30", "#b43c3a"]


def seat_row(width=int(2 * HOUSE), seat_w=46, back_h=40, aisles=(-250, 250), seed=0, step=10):
    """One row of theatre seats seen from the stage: upholstered crimson backs with a lit top roll,
    the seats folded up, oak armrests, cast end standards with an aisle light at each aisle, and the
    row's carpeted step below."""
    rng = np.random.default_rng(seed)
    H_ = back_h + step
    cv = Canvas(width, H_, seed=seed)
    base = back_h
    cv.rect(0, base, width, step, CARPET_M[2]); cv.hline(0, base, width, CARPET_M[1])
    cv.hline(0, H_ - 1, width, CARPET_M[0])
    half = width // 2
    gaps = [(half + a - 28, half + a + 28) for a in aisles]
    x = int(rng.integers(0, seat_w // 2))
    while x < width - seat_w // 2:
        if any(g0 - seat_w + 6 < x < g1 for (g0, g1) in gaps):
            x += 6
            continue
        sx = x
        cv.rect(sx + 3, 4, seat_w - 6, base - 6, SEAT[2])
        cv.rect(sx + 5, 2, seat_w - 10, 4, SEAT[4]); cv.hline(sx + 7, 1, seat_w - 14, SEAT[3])
        cv.vline(sx + 3, 4, base - 8, SEAT[3]); cv.vline(sx + seat_w - 4, 4, base - 8, SEAT[1])
        for k in range(sx + 10, sx + seat_w - 8, 9):
            cv.vline(k, 8, base - 20, SEAT[1])                          # channel stitching
        cv.rect(sx + 5, base - 12, seat_w - 10, 8, SEAT[0]); cv.hline(sx + 5, base - 12, seat_w - 10, SEAT[3])   # folded seat
        cv.rect(sx - 1, base - 16, 4, 16, "#1c1014"); cv.rect(sx - 2, base - 17, 6, 3, WOOD[3])               # armrest
        x += seat_w
    for (g0, g1) in gaps:
        cv.a[0:base, max(0, g0):g1] = 0
        cv.rect(g0, base, g1 - g0, step, CARPET_M[3]); cv.hline(g0, base, g1 - g0, BRASS[2])
        for sx in (g0 - 6, g1):
            cv.rect(sx, base - 26, 6, 26, "#2a2228"); cv.hline(sx, base - 26, 6, BRASS[3]); cv.px(sx + 2, base - 18, BRASS[3])
            cv.rect(sx + 1, base - 5, 4, 3, "#ffd88a")                    # aisle light
    return cv.a


def balcony_front_tex(length, h=int(BAL_HI - BAL_LO), seed=0):
    """The balcony front laid out flat: cream plaster with gilt mouldings top and bottom, a band of
    gilt lozenges, the rail of small bulbs along the top (unlit here; the chase layer lights them)."""
    cv = Canvas(length, h)
    cv.rect(0, 0, length, h, "#8a6e58")
    cv.rect(0, 0, length, 6, BRASS[3]); cv.hline(0, 0, length, BRASS[4]); cv.hline(0, 5, length, BRASS[1])
    cv.rect(0, h - 6, length, 6, BRASS[2]); cv.hline(0, h - 6, length, BRASS[4]); cv.hline(0, h - 1, length, BRASS[0])
    for x in range(0, length, 40):
        cv.poly([(x + 20, 12), (x + 34, h // 2 + 1), (x + 20, h - 12), (x + 6, h // 2 + 1)], BRASS[2])
        cv.poly([(x + 20, 16), (x + 29, h // 2 + 1), (x + 20, h - 16), (x + 11, h // 2 + 1)], "#7a2a2e")
        cv.vline(x, 8, h - 16, "#6a5040")
    return cv.a


def side_wall_tex(length, height, seed=0):
    """The house side wall laid out flat (u along the wall from the stage, rows from the top):
    rose plaster above an oak dado, tall round-headed arches with dark recesses, a warm sconce on
    every pier, EXIT doors with green signs, the balcony's side gallery front."""
    cv = Canvas(length, height, seed=seed)
    rng = np.random.default_rng(seed)
    cv.rect(0, 0, length, height, PLASTER_M[3])
    for _ in range(length * height // 900):
        px_, py_ = int(rng.integers(0, length)), int(rng.integers(0, height))
        cv.rect(px_, py_, int(rng.integers(10, 30)), int(rng.integers(4, 10)), PLASTER_M[int(rng.choice([2, 4]))])
    dado = height - 60
    cv.rect(0, dado, length, 60, WOOD[2]); cv.rect(0, dado, length, 6, WOOD[4]); cv.hline(0, dado, length, WOOD[5])
    for x in range(20, length, 60):
        cv.rect(x, dado + 12, 44, 40, WOOD[1]); cv.hline(x, dado + 12, 44, WOOD[0])
    lamps = []
    for k, x in enumerate(range(80, length - 60, 210)):
        aw, ah = 110, 200
        top = dado - ah
        cv.rect(x - 8, top - 10, aw + 16, ah + 10, DRESS[3])
        cv.ellipse(x - 8, top - 10 - aw // 2, aw + 16, aw + 16, DRESS[3])
        cv.rect(x, top, aw, ah, "#2a1a20"); cv.ellipse(x, top - aw // 2, aw, aw, "#2a1a20")
        cv.rect(x + 6, top + 10, aw - 12, ah - 10, "#3a2228")
        if k % 2 == 1:
            # an exit door in the arch with its green sign
            cv.rect(x + 25, dado - 120, 60, 120 + 60, "#4a2a26"); cv.vline(x + 55, dado - 120, 180, "#2a1814")
            cv.rect(x + 34, dado - 152, 42, 20, "#103018"); cv.rect(x + 36, dado - 150, 38, 16, "#40e070")
            lamps.append((x + 55, dado - 142, "6aff9a"))
        # sconce on the pier
        px_ = x + aw + 60
        if px_ < length - 20:
            cv.rect(px_ - 3, dado - 150, 7, 30, BRASS[2]); cv.ellipse(px_ - 12, dado - 172, 25, 24, "#f6cf7a")
            cv.ellipse(px_ - 7, dado - 166, 15, 14, "#fff0c4")
            lamps.append((px_, dado - 160, "ffe6a8"))
    return cv.a, lamps


def pit_piece(kind, seed=0):
    """Room-scale cut-outs for the pit seen over the stage edge: a stand pair (two chair backs and
    a lit stand), the harp, the bass."""
    if kind == "stand":
        cv = Canvas(40, 40, seed=seed)
        for dx in (-8, 8):
            cx = 20 + dx
            cv.rect(cx - 6, 16, 13, 9, CHAIR[0]); cv.rect(cx - 5, 17, 11, 7, CHAIR[2]); cv.hline(cx - 5, 17, 11, "#8a6a58")
        _stand(cv, 20, 39, lit=True, h=24)
        return cv.a
    if kind == "harp":
        cv = Canvas(46, 90)
        _harp(cv, 4, 88, h=78)
        return cv.a
    cv = Canvas(26, 70)
    _double_bass(cv, 2, 68, h=60)
    return cv.a


# --- shaders ------------------------------------------------------------------------------------
def stage_shader():
    """Black stage boards running out toward the house, worn grey where feet go, coloured spike
    tape, the white downstage safety line just before the footlights."""
    def shader(X, Z):
        board = 18.0
        col = np.floor(X / board)
        fx = X / board - col
        length = 240 + 120 * hash2(col, 3)
        off = hash2(col, 5) * length
        seg = np.floor((Z + off) / length)
        fz = (Z + off) / length - seg
        t = hash2(col, seg, 7)
        base = pal_array(["#2a2228", "#342a30", "#3c3036"])
        rgb = base[np.clip((t * 3).astype(int), 0, 2)]
        grain = hash2(np.floor(X / 3.0), np.floor(Z / 14.0), 11)
        rgb = rgb * (0.94 + 0.1 * grain[:, None])
        worn = hash2(np.floor(X / 30), np.floor(Z / 30), 13) > 0.72
        rgb[worn] = rgb[worn] * 1.12
        rgb[fx < 0.07] = pal_array(["#18121a"])[0]
        rgb[fz < 0.012] = pal_array(["#1c161c"])[0]
        # spike tape marks
        for (sx, sz, colr) in [(-180, 330, "#e8d050"), (60, 300, "#e86aa0"), (240, 360, "#4ab0e0"), (-40, 380, "#f0f0e8"),
                               (380, 300, "#e8d050"), (-360, 250, "#7ad070")]:
            m = (np.abs(X - sx) < 9) & (np.abs(Z - sz) < 3) | (np.abs(X - sx) < 2.5) & (np.abs(Z - sz) < 10)
            rgb[m] = pal_array([colr])[0]
        line = (Z > EDGE - 16) & (Z < EDGE - 11)
        rgb[line] = pal_array(["#d8d4c8"])[0]
        rgb = rgb * np.array(NIGHT, np.float32)
        out = rgba_of(rgb)
        # footlight spill on the downstage boards, warm pools where the follow spots rest
        warm_light(out[..., :3], np.abs(Z - EDGE) * 3.0, 160, colour="#f6cf7a", strength=0.3)
        warm_light(out[..., :3], np.hypot((X + 150) * 0.5, Z - 330), 140, colour="#fff0c4", strength=0.16)
        return out
    return shader


def ceiling_shader():
    def shader(X, Z):
        cof = (((X / 90.0) % 1) < 0.12) | (((Z / 90.0) % 1) < 0.12)
        rgb = np.repeat(pal_array(["#3a2430"]), X.shape[0], 0)
        rgb[cof] = pal_array([BRASS[1]])[0]
        rgb = rgb * np.array(NIGHT, np.float32)
        out = rgba_of(rgb)
        fog(out, Z, HAZE, 900, 2200, amount=0.5)
        return out
    return shader


def soffit_shader():
    def shader(X, Z):
        rgb = np.repeat(pal_array(["#2a1a22"]), X.shape[0], 0)
        lamp = (np.abs(((X + 45) / 180.0) % 1 - 0.5) < 0.05) & (np.abs(((Z - SOFFIT_Z) / 100.0) % 1 - 0.5) < 0.1)
        rgb = rgb * np.array(NIGHT, np.float32)
        rgb[lamp] = pal_array(["#ffe6a8"])[0]
        out = rgba_of(rgb)
        inside = (np.abs(X) < HOUSE) & (Z > BAL_Z - 300 * (X / HOUSE) ** 2) & (Z < SOFFIT_Z)
        out[~inside, 3] = 0
        return out
    return shader


def plane_shader(tex, flip=False, haze=True):
    th, tw = tex.shape[:2]

    def shader(u, Y, Z):
        uu = (tw - 1 - u) if flip else u
        out = texture_lookup(tex, uu, th - 1 - Y)
        out[..., 3] = 1
        if haze:
            glow = emissive(out[..., :3])
            f = out.copy()
            fog(f, Z, HAZE, 900, 2200, amount=0.5)
            out[~glow] = f[~glow]
        return out
    return shader


def back_shader(y_lo, y_hi, colour="#3a2430"):
    """The back wall of the balcony with the projection booth's row of little windows; two hold the
    follow spots' lenses."""
    def shader(X, Y):
        rgb = np.repeat(pal_array([colour]), X.shape[0], 0)
        win = (np.abs(((X + 30) / 120.0) % 1 - 0.5) < 0.16) & (Y > 424) & (Y < 456)
        rgb[win] = pal_array(["#140c14"])[0]
        rgb = rgb * np.array(NIGHT, np.float32)
        for (sx, sy) in LENSES:
            lens = np.hypot(X - sx, (Y - sy) * 1.2) < 13
            rgb[lens] = pal_array(["#fff6dc"])[0]
        out = rgba_of(rgb)
        fog(out, np.full(X.shape, BACK_Z), HAZE, 900, 2200, amount=0.5)
        return out
    return shader


# --- render -------------------------------------------------------------------------------------
def render():
    v = View(horizon=98, cam=52, fill="#120c14")
    glows = []
    # ceiling, back wall of the balcony with the booth
    v.ground(ceiling_shader(), height=CEIL, y_from=0, y_to=v.h0)
    v.back(BACK_Z, back_shader(0, CEIL), region=lambda X, Y: (Y > BALCONY[-1][1]) & (Y < CEIL) & (np.abs(X) < HOUSE))
    # side walls
    for side, flip in ((-1, False), (1, True)):
        tex, lamps = side_wall_tex(int(BACK_Z - EDGE), int(CEIL), seed=7 + side)
        tex = grade(tex)
        A, B = (side * HOUSE, EDGE), (side * HOUSE, BACK_Z)
        v.plane(A, B, plane_shader(tex), y_max=CEIL)
        for (u, row, colr) in lamps:
            Z = EDGE + u
            Y = CEIL - row
            sx, sy = v.project(side * HOUSE, Y, Z)
            if 0 <= sx < 640 and 0 <= sy < 160:
                glows.append([int(round(sx)), int(round(sy)), colr, 2 if Z < 1000 else 1])
    # balcony rows, back to front
    for k, (z, y) in reversed(list(enumerate(BALCONY))):
        row = darken(grade(seat_row(seed=40 + k)), 0.8 - 0.03 * k)
        v.sprite(row, 0, z, Y=y, anchor=(0.5, 1.0 - 10 / row.shape[0]), scale=1.0)
    # under the balcony: its soffit with downlights, the rear wall
    v.back(SOFFIT_Z, back_shader(0, BAL_LO, colour="#24161c"), region=lambda X, Y: (Y < BAL_LO) & (np.abs(X) < HOUSE))
    v.ground(soffit_shader(), height=BAL_LO, y_from=0, y_to=v.h0)
    # stalls rows, back to front
    for k, (z, y) in reversed(list(enumerate(STALLS))):
        shade_k = 0.62 if z > BAL_Z else 0.85 + 0.01 * (14 - k)
        row = darken(grade(seat_row(seed=10 + k)), min(1.0, shade_k))
        v.sprite(row, 0, z, Y=y, anchor=(0.5, 1.0 - 10 / row.shape[0]), scale=1.0)
    # the balcony front: a horseshoe of flat segments, centre first then the wings coming forward
    ftex = grade(balcony_front_tex(3000))
    xs = np.linspace(-HOUSE, HOUSE, 29)
    zs = BAL_Z - 300 * (xs / HOUSE) ** 2
    u0 = 0.0
    segs = list(zip(zip(xs[:-1], zs[:-1]), zip(xs[1:], zs[1:])))
    order = sorted(range(len(segs)), key=lambda i: -(zs[i] + zs[i + 1]))
    starts = np.concatenate([[0], np.cumsum([np.hypot(b[0] - a[0], b[1] - a[1]) for a, b in segs])])
    bulbs = []
    for i in order:
        a, b = segs[i]
        off = starts[i]
        tex = ftex

        def sh(u, Y, Z, off=off):
            return plane_shader(tex)(u + off, Y - BAL_LO, Z)
        v.plane(a, b, sh, y_max=BAL_HI, y_min=BAL_LO)
    for t in np.linspace(0, 1, 46):
        xx = -HOUSE + 2 * HOUSE * t
        zz = BAL_Z - 300 * (xx / HOUSE) ** 2
        sx, sy = v.project(xx, BAL_HI - 1, zz)
        if 2 <= sx < 638:
            bulbs.append((int(round(sx)), int(round(sy))))
    # the soffit edge shadow under the balcony front
    # the pit: its far wall and rail, then what stands in it
    v.back(PIT_Z, lambda X, Y: rgba_of(np.repeat(pal_array(["#1e1418"]), X.shape[0], 0) * np.array(NIGHT, np.float32)),
           region=lambda X, Y: (Y < RAIL_Y) & (Y > PIT_Y))
    rail = v.back(PIT_Z - 2, lambda X, Y: rgba_of(np.where((Y > RAIL_Y - 3)[:, None], pal_array([BRASS[3]])[0], pal_array([WOOD[3]])[0])
                                                    * np.array(NIGHT, np.float32)),
                  region=lambda X, Y: (Y < RAIL_Y + 2) & (Y > RAIL_Y - 10))
    rng = np.random.default_rng(3)
    pit_glows = []
    harp = grade(pit_piece("harp"))
    v.sprite(harp, -470, 520, Y=PIT_Y, scale=ROOM_TO_BATTLE)
    bass = grade(pit_piece("bass"))
    v.sprite(bass, 380, 530, Y=PIT_Y, scale=ROOM_TO_BATTLE)
    for z in (535.0, 495.0, 455.0):
        for x in np.arange(-320, 340, 110) + (z % 3) * 18:
            if abs(x - 380) < 40:
                continue
            st = grade(pit_piece("stand", seed=abs(int(x))))
            sx, sy, s = v.sprite(st, float(x + rng.integers(-12, 12)), z, Y=PIT_Y, scale=ROOM_TO_BATTLE)
            k = s * ROOM_TO_BATTLE
            pit_glows.append([int(round(sx)), int(round(sy - (24 + 1) * k)), "ffe2a0", 1])
    # the stage floor up to its edge, the apron nosing
    ey = v.ground_y(EDGE)
    v.ground(stage_shader(), y_from=ey)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    # crisp work on the 1x canvas: the apron's nosing and footlights
    ey = int(round(ey))
    cv.rect(0, ey, 640, 2, "#3a2a24"); cv.hline(0, ey, 640, "#6a5040")
    foot = []
    for X in np.arange(-640, 660, 64):
        fx, fy = v.project(X, 0, EDGE)
        if 4 <= fx < 636:
            fx = int(round(fx))
            cv.rect(fx - 4, ey - 3, 9, 4, "#141016"); cv.hline(fx - 3, ey - 3, 7, "#2a2228")
            cv.rect(fx - 3, ey - 1, 7, 2, "#ffe6a8"); cv.px(fx, ey - 1, "#ffffff")
            foot.append([fx, ey, "ffe6a8", 2])
    # unlit balcony bulbs (the chase layers light them)
    for (bx, by) in bulbs:
        cv.px(bx, by, "#6a5a40")
    frame_proscenium(cv)
    return cv, glows + pit_glows + foot, bulbs


def frame_proscenium(cv):
    """The opened house curtain gathered at both sides and its fringed border across the top,
    painted 1:1 over the edges of the view."""
    for (x0, w, flip) in ((0, 22, False), (640 - 22, 22, True)):
        for x in range(w):
            xx = (w - 1 - x) if flip else x
            ph = (xx * 0.9) % 6
            tone = CURTAIN[[1, 2, 3, 4, 3, 2][int(ph)]] if xx < w - 4 else CURTAIN[1]
            cv.vline(x0 + x, 0, 168, tone)
        edge = x0 + (w - 1 if not flip else 0)
        cv.vline(edge, 0, 168, CURTAIN[0])
        cv.rect(x0, 150, w, 18, C(SHADOW, 0.3))
    for x in range(0, 640):
        dip = int(3 * abs(np.sin(x / 40.0 * np.pi)))
        cv.vline(x, 0, 8 + dip, CURTAIN[[2, 3, 4, 3][(x // 3) % 4]])
        cv.vline(x, 8 + dip, 3, BRASS[3] if x % 2 else BRASS[2])
    cv.hline(0, 0, 640, CURTAIN[1])


def applause_sign(lit):
    """The red APPLAUSE lightbox hung from the balcony front (lit, or dark)."""
    label = "APPLAUSE"
    w = text_width(label) + 8
    cv = Canvas(w + 2, 14)
    cv.rect(0, 0, w + 2, 14, OUT)
    cv.rect(1, 1, w, 12, "#ff4a3a" if lit else "#4a1a1e")
    cv.rect(2, 2, w - 2, 10, "#ff5a44" if lit else "#3a1418")
    text(cv, label, 5, 3, "#fff0e0" if lit else "#6a2a2a")
    return cv


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    cv, glows, bulbs = render()
    # the APPLAUSE sign hangs at the centre of the balcony front
    on, off = applause_sign(True), applause_sign(False)
    v = View(horizon=98, cam=52)
    _, by = v.project(0, BAL_LO, BAL_Z)
    sx, sy = 320 - on.w // 2, int(round(by)) + 3
    spots = [[int(round(c)) for c in v.project(lx, ly, BACK_Z)] for (lx, ly) in LENSES]
    cv.vline(sx + 6, sy - 3, 3, IRON[2]); cv.vline(sx + on.w - 7, sy - 3, 3, IRON[2])
    cv.paste(off, sx, sy)
    cv.save(os.path.join(out, "battle-far.png"))
    on.save(os.path.join(out, "battle-applause.png"))
    res = f"res://assets/art/rooms/{ROOM}/"
    chase = []
    for k in range(3):
        rects = [[bx, by_, 1, 1, "ffe6a8"] for i, (bx, by_) in enumerate(bulbs) if i % 3 == k]
        chase.append({"kind": "blink", "pattern": "".join("1" if j == k else "0" for j in range(3)), "rate": 5, "rects": rects})
    return {
        "far": res + "battle-far.png",
        "layers": chase + [
            {"kind": "blink", "pattern": "1010", "rate": 2, "texture": res + "battle-applause.png", "x": sx, "y": sy},
            {"kind": "twinkle", "points": glows, "rate": 1.2, "min": 0.55},
            {"kind": "beam", "x": spots[0][0], "y": spots[0][1], "angle": 118, "sweep": 9, "period": 7.0, "phase": 0.0, "length": 150, "width": 70,
             "color": "fff6dc", "alpha": 0.2, "floor": 152},
            {"kind": "beam", "x": spots[1][0], "y": spots[1][1], "angle": 66, "sweep": 16, "period": 9.0, "phase": 1.7, "length": 150, "width": 66,
             "color": "fff0c4", "alpha": 0.18, "floor": 150},
            {"kind": "particles", "style": "dust", "count": 16, "rect": [150, 40, 320, 110], "speed": [2, -4], "color": "fff0d0"},
            {"kind": "fauna", "fauna": [
                {"kind": "macky_note", "x": 120, "y": 118, "fly": 9.0, "rate": 3.0},
                {"kind": "macky_note", "x": 360, "y": 96, "fly": 7.0, "rate": 3.0},
                {"kind": "macky_note", "x": 560, "y": 128, "fly": 11.0, "rate": 4.0}]},
        ],
    }


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
