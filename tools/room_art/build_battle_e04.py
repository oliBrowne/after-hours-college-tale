"""Battle backdrop for the model level (E04): out on the checker-plate mezzanine at the guardrail,
high in the structures bay. Across the drop the suspended bridge model hangs from the crane on its
slings, swaying a pixel either way; beyond it the far side of the bay climbs from the lit test floor
(reaction wall, the blue load frame, the bay lamps) past the far catwalk and the control booth's teal
window up to the deep-set openings onto the Flatirons and the crane runway. It is all the Engineering
Center's raw board-formed concrete: coffered concrete overhead, concrete columns rising out of the
drop, a Lyons sandstone base course along the test floor and a sandstone pier by the booth. Through the open grating behind
the party the test floor glows far below. The camera is set higher than usual (horizon 60) so the
drop reads; the feet line stays at y 150."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, text
from persp import View, ROOM_TO_BATTLE as K_ROOM, hash2, fog, pal_array, rgba_of, warm_light
from lib_umc import SAFETY, SHADOW
import lib_eng as E
import ec_interior as I
import build_e03 as R3

ROOM = "E04"
INK = "#10121e"
H0, CAM = 40, 110                 # a higher camera than usual: the feet line is still y 150 at Z 320
Z_EDGE = 420.0                    # the mezzanine's edge and guardrail
GRATE = (346.0, 414.0)            # open bar grating behind the party (depth)
Z_FAR = 2200.0                    # the far side of the bay
DROP = 200.0                      # the test floor below the mezzanine
STRIP_Y = 6                       # top row of the painted far wall strip
K_LOW = (CAM + DROP) / CAM        # how much deeper the test floor is than the deck, along a ray
LOW_PADS = ((-356.0, 1500.0), (94.0, 1500.0))
FOG = "#1c1a2a"


def far_y(Y):
    """Screen row of world height Y on the far wall."""
    return H0 + (CAM - Y) * 320.0 / Z_FAR


def mini_clerestory(cv, x, y, w, h, seed=0, bay=40):
    """A small, far clerestory onto the night and the Flatirons. Returns star/light points."""
    rng = np.random.default_rng(seed)
    pts = []
    for k in range(h):
        cv.hline(x, y + k, w, E.NIGHT_BANDS[min(len(E.NIGHT_BANDS) - 1, k * len(E.NIGHT_BANDS) // h)])
    for _ in range(w // 10):
        sx, sy = int(rng.integers(0, w)), int(rng.integers(0, h // 2))
        cv.px(x + sx, y + sy, "#c8ccec"); pts.append((x + sx, y + sy, "#e8ecff"))
    base = y + h - 5
    for sx in range(x - 10, x + w, 46):
        hg = int(rng.integers(5, 9))
        cv.poly([(sx, base), (sx + 12, base - hg), (sx + 19, base - hg + 3), (sx + 32, base)], "#1c1830")
        cv.line(sx + 12, base - hg, sx + 19, base - hg + 3, "#2c2644")
    cv.rect(x, base, w, y + h - base, "#141428")
    for _ in range(w // 12):
        lx, ly = int(rng.integers(0, w)), int(rng.integers(base + 1 - y, h - 1))
        col = ("#f6cf7a", "#e9a84a", "#c8d0f0")[int(rng.integers(0, 3))]
        cv.px(x + lx, y + ly, col); pts.append((x + lx, y + ly, col))
    for mx in range(x + bay, x + w, bay):
        cv.rect(mx - 1, y, 2, h, E.STEEL[1]); cv.vline(mx - 1, y, h, E.STEEL[3])
    cv.hline(x, y + h // 2, w, E.STEEL[1])
    cv.rect(x - 1, y - 1, w + 2, 1, E.STEEL[0]); cv.rect(x - 1, y + h, w + 2, 2, E.CONC[5])
    return pts


def far_wall():
    """The far side of the bay painted 1:1 in screen pixels (rows from STRIP_Y)."""
    cy = lambda Y: int(round(far_y(Y))) - STRIP_Y
    w, h = 640, cy(-DROP) + 1
    cv = Canvas(w, h, fill="#15161f")
    top, deck = cy(262), cy(0)
    I.coffered_ceiling(cv, 0, w, 0, top + 1, seed=70, bay=16, rib=3)
    I.board_concrete(cv, 0, top, w, deck - top, seed=71, board=3, lift=18, ties=(9, 9), tie=1, stains=0.3, foot=0)
    cv.rect(0, top, w, 2, C(SHADOW, 0.4))
    ry = cy(256)                                                # crane runway along the far wall
    cv.rect(0, ry, w, 3, E.OUT); cv.hline(0, ry + 1, w, E.CRANE[3]); cv.hline(0, ry, w, E.CRANE[4])
    sx_, sy_, sw_, sh_ = 4, cy(236), w - 8, cy(102) - cy(236)
    stars = mini_clerestory(cv, sx_, sy_, sw_, sh_, seed=72)
    stars = I.slot_colonnade(cv, sx_, sy_, sw_, sh_, pitch=22, open_w=14, depth=2, seed=74, pts=stars)
    stars = [(x, y + STRIP_Y, c) for (x, y, c) in stars]
    # the far catwalk at our level, the control booth on it (left)
    bx0, bx1, by0 = 70, 190, cy(94)
    I.lyons_wall(cv, bx1 + 6, cy(236) - 2, 8, deck - cy(236) + 2, seed=79, course=(2, 3), length=(3, 8), cap=False)
    cv.rect(bx0, by0, bx1 - bx0, deck - by0, E.OUT)
    cv.rect(bx0 + 1, by0 + 1, bx1 - bx0 - 2, deck - by0 - 1, E.CONC[3]); cv.hline(bx0 + 1, by0 + 1, bx1 - bx0 - 2, E.CONC[6])
    wx0, wx1, wy0, wy1 = bx0 + 4, bx1 - 4, by0 + 3, deck - 2
    cv.rect(wx0, wy0, wx1 - wx0, wy1 - wy0, "#0c1a1c")
    screens = []
    for k in range(4):
        sx = wx0 + 4 + k * 28
        cv.rect(sx, wy1 - 4, 22, 3, "#1e4448"); cv.hline(sx + 1, wy1 - 3, 20, "#4ac0b0")
        screens.append((sx, wy1 - 4 + STRIP_Y, 22, 3))
    E.tint_rect(cv, wx0, wy0, wx1 - wx0, wy1 - wy0, "#4ac0b0", 0.16)
    cv.line(wx0 + 6, wy1 - 1, wx0 + 11, wy0 + 1, C("#c8f0f0", 0.25))
    cv.rect(bx0 + 40, by0 - 5, 40, 6, E.OUT); E.micro_text(cv, "CONTROL", bx0 + 46, by0 - 5, "#e8e2d0")
    E.stepped_glow(cv, (bx0 + bx1) // 2, deck + 3, 80, 6, "#4ac0b0", 0.10, 3)
    cv.rect(0, deck, w, 2, E.STEEL[4]); cv.hline(0, deck, w, E.STEEL[6]); cv.rect(0, deck + 2, w, 1, E.STEEL[1])
    rt_ = cy(34)
    cv.hline(0, rt_, bx0 - 1, SAFETY[1]); cv.hline(bx1 + 1, rt_, w - bx1 - 1, SAFETY[1])
    for px in range(4, w, 24):
        if not bx0 - 2 <= px <= bx1 + 1:
            cv.vline(px, rt_, deck - rt_, SAFETY[1])
    # the test floor's wall below: block, the reaction wall, the blue frame, lamps, lit from below
    low_top, low_bot = deck + 3, h
    I.board_concrete(cv, 0, low_top, w, low_bot - low_top, seed=73, board=3, lift=18, ties=(9, 9), tie=1, stains=0.3, foot=0)
    I.lyons_wall(cv, 0, low_bot - 7, w, 7, seed=78, course=(2, 3), length=(4, 10), cap=False)
    E.tint_rect(cv, 0, low_top, w, low_bot - low_top, "#0e0d16", 0.4)
    cv.rect(0, low_top, w, 2, C("#0a0910", 0.6))
    rw0, rw1 = 150, 470
    rt = cy(-104)
    cv.rect(rw0, rt, rw1 - rw0, low_bot - rt, E.CONC[5])
    for yy in range(rt + 1, low_bot, 2):
        cv.hline(rw0, yy, rw1 - rw0, E.CONC[6])
    cv.hline(rw0, rt, rw1 - rw0, E.CONC[7])
    for ay in range(rt + 2, low_bot - 1, 4):
        for ax in range(rw0 + 3, rw1 - 2, 5):
            cv.px(ax, ay, E.STEEL[2])
    fx0, fx1, ft = 268, 312, cy(-76)
    for fx in (fx0, fx1 - 3):
        cv.rect(fx, ft, 3, low_bot - ft, E.FRAME_BLUE[3]); cv.vline(fx, ft, low_bot - ft, E.FRAME_BLUE[5])
    cv.rect(fx0 - 2, ft, fx1 - fx0 + 4, 3, E.FRAME_BLUE[3]); cv.hline(fx0 - 2, ft, fx1 - fx0 + 4, E.FRAME_BLUE[5])
    mid = (fx0 + fx1) // 2
    cv.rect(mid - 2, ft + 3, 4, 6, E.STEEL[4]); cv.vline(mid, ft + 9, 3, E.STEEL[6])
    cv.rect(fx0 + 4, low_bot - 6, fx1 - fx0 - 8, 2, "#8a8890")
    cv.rect(mid - 8, ft - 5, 17, 4, "#c03a32"); cv.hline(mid - 8, ft - 5, 17, "#e85a4a")
    cv.rect(330, low_bot - 5, 10, 5, E.FRAME_BLUE[2]); cv.hline(330, low_bot - 5, 10, E.FRAME_BLUE[4])
    cv.rect(176, low_bot - 13, 7, 13, "#1e2028")
    leds = []
    for k in range(4):
        for j in range(2):
            leds.append((178 + j * 3, low_bot - 11 + k * 3 + STRIP_Y, ("#3cba7a", "#e8b45c", "#c84a3c")[(k + j) % 3]))
    lamps = []
    for lx in (96, 300, 520):
        cv.rect(lx - 3, low_top, 7, 2, "#3a3a46"); cv.px(lx, low_top + 2, E.WARM[4])
        lamps.append((lx, low_top + 2 + STRIP_Y))
        E.stepped_glow(cv, lx, low_bot - 1, 70, 10, "#f6cf7a", 0.10, 3)
    E.tint_rect(cv, 0, low_bot - 8, w, 8, "#f6cf7a", 0.10)
    E.tint_rect(cv, 0, low_top, w, low_bot - low_top, "#f6cf7a", 0.05)
    return cv, stars, screens, leds, lamps


def low_floor(X, Z):
    """The test floor seen far below (world coordinates on that floor)."""
    fl = pal_array(R3.CONC_FLOOR)
    cell = hash2(np.floor(X / 120), np.floor(Z / 80), 15)
    rgb = np.where(cell[:, None] < 0.5, fl[3], fl[4]).astype(np.float32)
    ax = ((X + 41) % 82) - 41
    az = ((Z - 10) % 60) - 30
    rgb[(np.abs(ax) < 6) & (np.abs(az) < 3)] = pal_array(E.STEEL)[4]
    yel = np.array(C(SAFETY[2])[:3], np.float32)
    for (px, pz) in LOW_PADS:
        d = np.hypot((X - px) / 60, (Z - pz) / 40)
        ring = (d < 1.0) & (d > 0.78)
        rgb[ring] = yel
        rgb[(np.abs(X - px) < 30) & (np.abs(Z - pz) < 14)] = pal_array(E.STEEL)[5]
        warm_light(rgb, np.hypot(X - px, (Z - pz) * 1.2), 160, colour="#f6cf7a", strength=0.45)
    for lx in (-700.0, 0.0, 700.0):
        warm_light(rgb, np.hypot(X - lx, Z - 1750), 460, colour="#f6e0a8", strength=0.3)
    yel2 = (np.abs(np.abs(X) - 900) < 4) & (Z < Z_FAR - 60)
    rgb[yel2] = rgb[yel2] * 0.3 + yel * 0.7
    shade_ = (Z < 1330) & (Z > 1000)                          # the mezzanine's own shadow below its edge
    rgb[shade_] *= 0.72
    out = rgba_of(rgb)
    out[Z > Z_FAR, 3] = 0
    fog(out, Z, "#2a2232", 1100, Z_FAR, amount=0.3)
    return out


def deck_shader(X, Z):
    d = pal_array(E.DECK)
    rgb = np.empty(X.shape + (3,), np.float32)
    rgb[:] = d[4]
    # checker plate: raised lugs alternating direction cell by cell
    i, j = np.floor(X / 12), np.floor(Z / 12)
    u, v = X - i * 12, Z - j * 12
    odd = ((i + j) % 2) == 1
    lug = np.where(odd, np.abs(u - v) < 1.6, np.abs(u + v - 12) < 1.6) & (u > 2.5) & (u < 9.5)
    rgb[lug] = d[6]
    rgb[lug & (np.where(odd, u > v, u + v > 12))] = d[2]
    seam = (np.abs((X % 240) - 120) < 1.4) | (np.abs(((Z - 40) % 160) - 80) < 1.6)
    rgb[seam] = d[1]
    # hazard band along the grating's near edge
    yel = np.array(C(SAFETY[2])[:3], np.float32)
    band = (Z > GRATE[0] - 9) & (Z < GRATE[0] - 2)
    stripe = (np.floor((X - Z * 1.3) / 14) % 2) == 0
    rgb[band] = np.where(stripe[band, None], yel, np.array(C("#1a1524")[:3], np.float32))
    # the open grating: the test floor far below between the bearing bars
    g = (Z > GRATE[0]) & (Z < GRATE[1])
    if g.any():
        low = low_floor(X[g] * K_LOW, Z[g] * K_LOW)[..., :3]
        low = low * 0.85
        bars = (np.abs((X[g] % 9) - 4.5) > 3.0) | (np.abs(((Z[g] - GRATE[0]) % 34) - 17) > 15.5)
        st = pal_array(E.STEEL)
        sub = np.where(bars[:, None], st[3], low)
        sub[bars & (np.abs((X[g] % 9) - 4.5) > 3.8)] = st[5]
        rgb[g] = sub
    frame = ((np.abs(Z - GRATE[0]) < 2.5) | (np.abs(Z - GRATE[1]) < 2.5))
    rgb[frame] = d[6]
    # the toe board foot and the lit deck around the party
    for (lx, lz) in ((-200.0, 330.0), (230.0, 360.0)):
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 1.6), 200, colour="#f6e0a8", strength=0.16)
    warm_light(rgb, np.hypot((X - 60) * 0.5, Z - GRATE[1]), 90, colour="#f6cf7a", strength=0.18)
    out = rgba_of(rgb)
    out[Z > Z_EDGE, 3] = 0
    fog(out, Z, FOG, 380, Z_EDGE + 40, amount=0.2)
    return out


def roof_shader(X, Z):
    out = I.beam_ceiling_shader(X, Z, bay_z=200.0, bay_x=260.0, z0=300.0, fog_to=Z_FAR, fog_col="#15161f")
    out[Z > Z_FAR, 3] = 0
    return out


def rail_shader(kind):
    def shade(u, Y, Z):
        cr = pal_array(E.CRANE)
        rgb = np.empty(Y.shape + (3,), np.float32)
        if kind == "toe":
            stripe = (np.floor(u / 22) % 2) == 0
            rgb[:] = np.where(stripe[:, None], np.array(C(SAFETY[2])[:3], np.float32), np.array(C("#1a1524")[:3], np.float32))
            rgb[Y > 7] = cr[4]
        else:
            rgb[:] = cr[2]
            top = Y > (Y.max() if Y.size else 0) - 1.2
            rgb[top] = cr[4]
        out = rgba_of(rgb)
        fog(out, Z, FOG, 400, 700, amount=0.15)
        return out
    return shade


HOOKS = ((232, (204, 248)), (352, (336, 380)))   # trolley x and the deck points each sling holds
MODEL_X = (196, 388)
DECK_Y, APEX_Y, BLOCK_Y = 62, 30, 11


def model_frame(dx, lights_out=None):
    """The suspended model at 1:1, nudged dx px: crane ropes, hook blocks, two-leg slings, the blue
    deck with its amber underside strip, Cal's arch with hangers. Canvas covers x 160..440, y 0..80."""
    ox = 160
    cv = Canvas(280, 80)
    d0, d1, dy = MODEL_X[0] - ox + dx, MODEL_X[1] - ox + dx, DECK_Y
    BL = ["#1a2a56", "#2c437e", "#425da6", "#5c7cc4", "#8aa6dc"]
    for (hx, legs) in HOOKS:
        hx -= ox
        for k in (-1, 1):
            cv.line(hx + k, 4, hx + dx + k, BLOCK_Y, E.STEEL[2]); cv.line(hx + k + 1, 4, hx + dx + k + 1, BLOCK_Y, E.STEEL[5])
        b = hx + dx
        cv.rect(b - 5, BLOCK_Y, 11, 8, E.OUT); cv.rect(b - 4, BLOCK_Y + 1, 9, 6, E.CRANE[3]); cv.hline(b - 4, BLOCK_Y + 1, 9, E.CRANE[5])
        cv.rect(b - 1, BLOCK_Y + 8, 3, 3, E.STEEL[4])
        for lx in legs:
            lx = lx - ox + dx
            cv.line(b, BLOCK_Y + 11, lx, dy - 1, E.STEEL[3]); cv.line(b + 1, BLOCK_Y + 11, lx + 1, dy - 1, E.STEEL[6])
        cv.rect(b + 3, BLOCK_Y + 15, 3, 4, "#c03a32")

    def arch_y(xx):
        t = (xx - d0 - 6) / (d1 - d0 - 11)
        return t, int(round(dy - 1 - (dy - 1 - APEX_Y) * 4 * t * (1 - t)))
    for xx in range(d0 + 6, d1 - 5):                           # far rib and hangers
        t, yy = arch_y(xx)
        cv.px(xx, yy - 2, BL[1])
        if (xx - d0) % 8 == 0 and 0.04 < t < 0.96:
            cv.vline(xx, yy + 1, dy - yy - 1, BL[1])
    for xx in range(d0 + 6, d1 - 5):
        cv.rect(xx, arch_y(xx)[1] - 1, 1, 3, E.OUT)
    for xx in range(d0 + 6, d1 - 5):                           # near rib
        yy = arch_y(xx)[1]
        cv.px(xx, yy, BL[4]); cv.px(xx, yy + 1, BL[2])
    # deck: blue box girder, pale top edge, amber underside strip with lamps
    cv.rect(d0, dy, d1 - d0, 7, E.OUT)
    cv.rect(d0 + 1, dy + 1, d1 - d0 - 2, 5, BL[2]); cv.hline(d0 + 1, dy + 1, d1 - d0 - 2, BL[4]); cv.hline(d0 + 1, dy + 4, d1 - d0 - 2, BL[1])
    for sx in range(d0 + 8, d1 - 4, 16):
        cv.vline(sx, dy + 2, 2, BL[3])
    cv.hline(d0 + 2, dy + 6, d1 - d0 - 4, E.WARM[1])
    pts = []
    for lx in range(d0 + 6, d1 - 4, 12):
        cv.rect(lx - 1, dy + 6, 3, 1, E.WARM[3]); cv.px(lx, dy + 6, E.WARM[4])
        pts.append((lx + ox, dy + 6))
    for ex in (d0, d1 - 6):                                     # end blocks
        cv.rect(ex, dy - 3, 6, 4, E.OUT); cv.rect(ex + 1, dy - 2, 4, 2, E.CONC[7])
    if lights_out is not None:
        lights_out.extend(pts)
    return cv, ox


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=H0, cam=CAM, fill="#12121c")
    wall, stars, screens, leds, lamps = far_wall()
    v.strip(wall.a, STRIP_Y, 0)
    v.ground(roof_shader, y_from=0, y_to=H0, height=CAM + 220)
    v.ground(low_floor, height=-DROP)
    # kit standing on the test floor far below
    for (made, X, Z) in ((E.steel_bench_chart(170, 42, seed=2), -700.0, 1560.0),
                         (E.pipe_barrier(320, 25, "TEST AREA"), -150.0, 1950.0),
                         (E.cylinder_cart(80, 50, seed=3), 640.0, 1700.0)):
        spr, ax, ay = made
        v.sprite(spr.a, X, Z, Y=-DROP, anchor=(ax / spr.w, ay / spr.h), scale=K_ROOM)
    # steel columns of the bay rising out of the drop at both sides, and the model's tag lines
    st = pal_array(E.CONC)

    def column(xc):
        def shade(X, Y):
            # a board-formed concrete column: lit left face, plank marks, tie holes, a dark right arris
            u = X - xc
            rgb = np.empty(X.shape + (3,), np.float32)
            rgb[:] = st[5]
            rgb[(np.floor(Y / 7) % 2) == 0] = st[4] * 0.5 + st[5] * 0.5
            rgb[np.abs(Y % 7) < 0.9] = st[4]
            rgb[u < -13] = st[6]
            rgb[u > 14] = st[3]
            rgb[u > 18] = st[2]
            tie = (np.abs(np.abs(u) - 7) < 1.2) & (np.abs(((Y + 20) % 36) - 18) < 1.2)
            rgb[tie] = st[1]
            plate = np.abs(((Y + 40) % 140) - 70) < 3
            rgb[plate] = st[7]
            out = rgba_of(rgb)
            low = Y < 0
            out[low, :3] = out[low, :3] * 0.8 + np.array(C("#f6cf7a")[:3], np.float32) * 0.2 * np.clip(-Y[low] / 200, 0, 1)[:, None]
            fog(out, np.full(X.shape, 640.0), FOG, 400, 900, amount=0.2)
            return out
        return shade
    for xc in (-600.0, 600.0):
        v.back(640.0, column(xc), region=lambda X, Y, xc=xc: (np.abs(X - xc) < 21) & (Y > -DROP) & (Y < 400))
    rope = np.array(C("#d46a24"), np.float32)
    for xl in (-310.0, 250.0):
        v.back(900.0, lambda X, Y: np.broadcast_to(rope, X.shape + (4,)).copy(),
               region=lambda X, Y, xl=xl: (np.abs(X - xl + 0.04 * (Y - 48)) < 1.6) & (Y > -DROP) & (Y < 48))
    v.ground(deck_shader)
    # guardrail along the mezzanine edge: toe board, mid and top rails, posts
    A, B = (-3000.0, Z_EDGE), (3000.0, Z_EDGE)
    v.plane(A, B, rail_shader("toe"), y_min=0, y_max=9)
    v.plane(A, B, rail_shader("rail"), y_min=17, y_max=20)
    v.plane(A, B, rail_shader("rail"), y_min=33, y_max=37)
    cr = pal_array(E.CRANE)

    def posts(X, Y):
        o = np.zeros(X.shape + (4,), np.float32)
        loc = np.abs(((X + 80) % 160) - 80)
        o[:, :3] = cr[2]
        o[loc < 1.2, :3] = cr[4]
        o[:, 3] = 1
        return o
    v.back(Z_EDGE - 1, posts, region=lambda X, Y: (Y > 0) & (Y < 37) & (np.abs(((X + 80) % 160) - 80) < 3.2))
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)
    # the crane bridge carrying the model, crossing high overhead (crisp)
    cv.rect(0, 0, 640, 5, E.OUT); cv.rect(0, 0, 640, 4, E.CRANE[3]); cv.hline(0, 3, 640, E.CRANE[1])
    for (tx, _) in HOOKS:
        cv.rect(tx - 9, 3, 19, 4, E.OUT); cv.rect(tx - 8, 3, 17, 3, E.CRANE[2]); cv.rect(tx - 5, 4, 11, 1, E.STEEL[3])
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    # the model swaying a pixel either way on its slings
    model_lights = []
    offsets = [-1, 0, 1]
    seq = [1, 1, 2, 2, 2, 1, 1, 0, 0, 0]
    for k, d in enumerate(offsets):
        fr, ox = model_frame(d, model_lights if d == 0 else None)
        fr.save(os.path.join(out, f"battle-model-{k}.png"))
        layers.append({"kind": "blink", "pattern": "".join("1" if s == k else "0" for s in seq), "rate": 2.5,
                       "texture": res + f"battle-model-{k}.png", "x": ox, "y": 0})
    flick = [[sx + 1, sy + 1, sw - 2, 1, "8af0e0"] for (sx, sy, sw, sh) in screens]
    layers += [
        {"kind": "twinkle", "points": [[x, y, c.lstrip("#"), 1] for (x, y, c) in stars], "rate": 1.2, "min": 0.2},
        {"kind": "twinkle", "points": [[x, y, "f6cf7a", 1] for (x, y) in model_lights], "rate": 1.1, "min": 0.45},
        {"kind": "twinkle", "points": [[x, y, "fff0c4", 1] for (x, y) in lamps], "rate": 0.8, "min": 0.7},
        {"kind": "blink", "pattern": "1011101", "rate": 4.0, "rects": flick},
        {"kind": "blink", "pattern": "100000", "rate": 3.0,
         "rects": [[tx - 1, 7, 3, 1, "ffc040"] for (tx, _) in HOOKS] + [[tx - 5, 4, 11, 6, "ffc040", 0.2] for (tx, _) in HOOKS]},
    ]
    groups = [leds[0::2], leds[1::2]]
    for g, pat in zip(groups, ("10", "01")):
        layers.append({"kind": "blink", "pattern": pat, "rate": 2.0, "rects": [[x, y, 1, 1, c.lstrip("#")] for (x, y, c) in g]})
    # the two lit foundations far below, breathing
    glow = E.glow_sprite(18, 4, "#f6cf7a", (0.10, 0.2, 0.34))
    glow.save(os.path.join(out, "battle-pad-glow.png"))
    for i, (px, pz) in enumerate(LOW_PADS):
        sx = int(round(320 + px * 320 / pz))
        sy = int(round(H0 + (CAM + DROP) * 320 / pz))
        layers.append({"kind": "blink", "pattern": "1111111000" if i == 0 else "1110001111", "rate": 2.0,
                       "texture": res + "battle-pad-glow.png", "x": sx - 18, "y": sy - 4})
    layers += [
        # dust rising out of the bay through the lamp light
        {"kind": "particles", "style": "dust", "count": 20, "rect": [20, 50, 600, 70], "speed": [1, 5], "color": "f6dca0"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
