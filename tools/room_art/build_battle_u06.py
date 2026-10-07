"""Battle backdrop for the Connection (U06): down the lanes from the approach, cosmic bowling after
closing. Seven maple lanes fan away from the fighters to the pin decks, lit white under the
masking, where a black-light mural of the Flatirons and bowling-ball comets runs under THE
CONNECTION in pink neon (its second N stutters, as in the room). The shoe-hire wall and the CLUB
door are on the left, a row of arcade cabinets glows down the right, black-light tubes cross the
ceiling and coloured spots sweep the lanes. Glowing balls roll up lanes 4 and 5, and at the last
moment the pins hop out of the way: the pins are refusing to be scored."""
import paths
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, mix, text, text_width
from props import OUT
from interior import PANEL
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_umc import BRASS, PAPER, SAFETY, SHADOW, halo, soft_ellipse
from lib_umc2 import (INDIGO, STRIPES, MAPLE, PIN, NEON_PINK, NEON_TEAL, NEON_GOLD, CARPET, CONFETTI, CHROME,
                      BALLS, neon_text, text_mask, stripe_band, indigo_wall, league_pennants, lightbox)

ROOM = "U06"
INK = "#10121e"
H0, CAM, VX = 56, 94, 300          # horizon, camera height, vanishing point x (feet line y 150 at Z 320)
BAY, HALF, EDGE = 76.0, 266.0, 14.0  # one lane bay (capping + gutter + 44 bed + gutter), half of seven, outer capping
Z_NEAR, Z_APP0, Z_FOUL, Z_PIN, Z_BACK = 300.0, 230.0, 360.0, 690.0, 750.0
Z_ARROW = Z_FOUL + 0.26 * (Z_PIN - Z_FOUL)
X_WEST, X_EAST, X_CAB = -420.0, 420.0, 384.0
CEIL = 170.0
TUBES = (452.0, 566.0, 680.0)      # black-light tubes across the ceiling
CABINETS = [(412, 74, 0), (452, 70, 1), (492, 76, 2), (532, 72, 3), (572, 74, 1), (612, 70, 0), (652, 74, 2)]
CAB_DEPTH = 32.0
CAB_COLOURS = [("#1e2a6a", "#58e0d0", "#3ad8c8"), ("#5a1a3a", "#ff7aa8", "#ff6aa0"),
               ("#3a2a10", "#f6cf7a", "#ffc850"), ("#2a1a5a", "#b48cff", "#9a7ae8")]
BALL_LANES = [(3, 5.6, "6ae0d0", "3ad8c8"), (4, 7.2, "ff8ab8", "ff6aa0")]   # lane index, period, colours


def P(c):
    return np.array(C(c)[:3], np.float32)


def lane_x(k):
    """World X of the centre of lane k (0..6); lane 4 (k = 3) runs straight to the vanishing point."""
    return -HALF + BAY * (k + 0.5)


def scr(X, Z, Y=0.0):
    s = 320.0 / Z
    return VX + X * s, H0 + (CAM - Y) * s


# ---------------------------------------------------------------------------------------------
# floor, ceiling
# ---------------------------------------------------------------------------------------------

def carpet_rgb(X, Z):
    """The cosmic carpet: navy weave with glowing confetti motifs (they light up under black light)."""
    rgb = np.empty(X.shape + (3,), np.float32)
    rgb[:] = P(CARPET[2])
    weave = (np.floor(Z / 9.0) % 2 == 0)
    rgb[weave] = P(mix(CARPET[2], CARPET[1], 0.5))
    cell = 24.0
    cx, cz = np.floor(X / cell + 0.5 * (np.floor(Z / cell) % 2)), np.floor(Z / cell)
    fx, fz = X / cell + 0.5 * (np.floor(Z / cell) % 2) - cx, Z / cell - cz
    h = hash2(cx, cz, 21)
    motif = (h > 0.45) & (np.abs(fx - 0.5) < 0.13) & (np.abs(fz - 0.5) < 0.1)
    idx = (hash2(cx, cz, 22) * 4).astype(int) % 4
    rgb[motif] = pal_array(CONFETTI)[idx[motif]] * 1.1
    return rgb


def floor_shader(X, Z):
    """Approach boards, the lanes (cappings with a glowing strip, gutters, maple beds with the pin
    lights and the neon reflected in the oil), the white-lit pin decks, carpet either side."""
    rgb = carpet_rgb(X, Z)
    xa = np.abs(X)
    wood = xa < HALF + EDGE
    bx = X + HALF
    bay = np.floor(bx / BAY)
    lu = bx - bay * BAY
    near_b = np.round(bx / BAY)                 # nearest bay boundary
    dcap = np.abs(bx - near_b * BAY)            # distance to it
    board = np.floor(X / 3.0)
    tone = hash2(board, np.floor(Z / 140.0), 3)

    # approach: one wide maple floor, boards running toward the pins, seams at each lane's edge
    app = wood & (Z >= Z_APP0) & (Z < Z_FOUL)
    a = (P(MAPLE[3]) * 0.35 + P(MAPLE[4]) * 0.65)[None, :] * (0.91 + 0.12 * tone[:, None])
    a[dcap < 0.9] = P(MAPLE[2])
    a[(Z < Z_APP0 + 6)] = P(MAPLE[5])
    a[(Z < Z_APP0 + 2)] = P(MAPLE[1])
    # lit from the lanes' end: stepping darker toward the camera
    fall = np.clip((Z_FOUL - Z) / (Z_FOUL - Z_APP0), 0, 1)
    a *= (1.0 - 0.1 * np.ceil(fall * 3))[:, None]
    rgb[app] = a[app]

    # lanes
    lane = wood & (Z >= Z_FOUL) & (Z < Z_BACK + 4)
    t = np.clip((Z - Z_FOUL) / (Z_PIN - Z_FOUL), 0, 1)
    cap = (dcap < 6) | (xa > HALF)
    gut = ~cap & (dcap < 16)
    bed = ~cap & ~gut
    deck = Z >= Z_PIN - 16
    # bed: boards in two close tones, a stepped brightening toward the lit decks
    b = (P(MAPLE[3]) * 0.55 + P(MAPLE[4]) * 0.45)[None, :] * (0.93 + 0.1 * tone[:, None])
    # (steps measured on screen, so each band gets its share of the picture)
    ys = 320.0 * CAM / Z
    u = np.clip((320.0 * CAM / Z_FOUL - ys) / (320.0 * CAM / Z_FOUL - 320.0 * CAM / Z_PIN), 0, 1)
    step = np.where(u < 0.3, 0.8, np.where(u < 0.55, 0.86, np.where(u < 0.8, 0.93, 1.0)))
    b *= step[:, None]
    # the oil: the deck lights run down the middle of every lane in stepped bands
    dl = np.abs(lu - BAY / 2)
    refl = np.where(u < 0.2, 0.04, np.where(u < 0.45, 0.1, np.where(u < 0.7, 0.18, 0.28)))
    streak = np.where(dl < 3.5, 1.0, np.where(dl < 9, 0.55, np.where(dl < 15, 0.25, 0.0)))
    k = (refl * streak)[:, None]
    b = b * (1 - k) + P("#fff2d8")[None, :] * k
    # THE CONNECTION reflected pink in the boards straight under the sign
    sx = VX + X * 320.0 / Z
    pink = (np.abs(sx - VX) < 80) & (u > 0.3)
    kp = np.where(u > 0.65, 0.2, 0.12)
    b[pink] = b[pink] * (1 - kp[pink, None]) + P("#ff7aa8")[None, :] * kp[pink, None]
    # deck: pale and brightly lit
    d = P("#ecd2a4")[None, :] * (0.96 + 0.05 * tone[:, None])
    b = np.where(deck[:, None], d, b)
    # gutters: dark troughs with a lit lip on the lane side
    g = np.empty_like(b)
    g[:] = P("#1c1726")
    g[(np.abs(dcap - 15.0) < 1.0)] = P("#4a4058")
    g[(np.abs(dcap - 10.5) < 1.2)] = P("#120e1a")
    g[deck] = P("#2a2234")
    # cappings: charcoal, a lit top edge, a glowing strip (teal and pink by turns) down the middle
    cp = np.empty_like(b)
    cp[:] = P("#221e2c")
    cp[np.abs(dcap - 5.0) < 1.0] = P("#4a4458")
    glow = np.where((near_b.astype(int) % 2) == 0, 0, 1)
    strip = (dcap < 1.3) & (xa <= HALF + 1)
    gc = pal_array(["#3ad8c8", "#ff6aa0"])[glow]
    cp[strip] = cp[strip] * 0.35 + gc[strip] * 0.65
    cp[deck] = P("#16121e")
    lrgb = np.where(bed[:, None], b, np.where(gut[:, None], g, cp))
    rgb[lane] = lrgb[lane]

    # light: the approach under the pink sign glow and the arcade's teal, darker at the edges
    warm_light(rgb, np.hypot(X * 0.9, (Z - Z_FOUL + 30) * 2.2), 260, colour="#ff9ac0", strength=0.14)
    warm_light(rgb, np.hypot(X - 360, (Z - 470) * 1.2), 150, colour="#58e0d0", strength=0.2)
    edge = np.clip((xa - 150) / 260, 0, 1)
    rgb *= (1 - 0.35 * np.ceil(edge * 3) / 3)[:, None]
    out = rgba_of(rgb)
    off = ~(wood & (Z >= Z_APP0))
    t2 = np.clip((Z - 480) / 320, 0, 1)[:, None] * 0.45 * off[:, None]
    out[..., :3] = out[..., :3] * (1 - t2) + P("#191630")[None, :] * t2
    return out


def ceiling_shader(X, Z):
    """Black acoustic tiles with three black-light tubes across, each throwing a violet band."""
    rgb = np.empty(X.shape + (3,), np.float32)
    rgb[:] = P("#14111f")
    tile = 30.0
    fx, fz = X / tile - np.floor(X / tile), Z / tile - np.floor(Z / tile)
    rgb[(fx < 0.06) | (fz < 0.08)] = P("#0b0914")
    for zt in TUBES:
        dz = np.abs(Z - zt)
        span = np.abs(X) < 330
        for (r, a) in [(26, 0.1), (14, 0.12), (7, 0.16)]:
            m = span & (dz < r)
            rgb[m] = rgb[m] * (1 - a) + P("#7a5ae0") * a
        rgb[span & (dz < 4)] = P("#241e3a")
        rgb[span & (dz < 1.8)] = P("#c8b4ff")
    out = rgba_of(rgb)
    fog(out, Z, "#100d1c", 600, 900, amount=0.4)
    return out


# ---------------------------------------------------------------------------------------------
# side walls and cabinets (textures in world units, painted at half resolution and doubled)
# ---------------------------------------------------------------------------------------------

def doubled(cv):
    return np.repeat(np.repeat(cv.a, 2, 0), 2, 1)


def mini_cubbies(cv, x, y, w, h, cols, seed=0, sole="#cfc6b4"):
    """Shoe-hire cubbies at battle scale: a wooden case of holes, each with a two-tone pair."""
    rng = np.random.default_rng(seed)
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, PANEL[3]); cv.hline(x, y, w, PANEL[5])
    cw = (w - 1) // cols
    rows = (h - 1) // 7
    shoes = [("#b8403c", "#e6d6b1"), ("#3a5ab8", "#c49a68"), ("#2a8a86", "#1e1a2a"), ("#d8c8a8", "#b8403c"),
             ("#c8642a", "#2a2436")]
    for r in range(rows):
        for c in range(cols):
            hx, hy = x + 1 + c * cw, y + 1 + r * 7
            cv.rect(hx, hy, cw - 1, 6, "#1a1016")
            if rng.random() < 0.8:
                body, trim = shoes[int(rng.integers(len(shoes)))]
                cv.rect(hx + 1, hy + 2, cw - 3, 2, body); cv.px(hx + 1, hy + 2, trim)
                cv.hline(hx + 1, hy + 4, cw - 3, sole)
            cv.px(hx + cw // 2 - 1, hy + 5, BRASS[3])


def west_wall_tex():
    """The shoe-hire wall: indigo plaster, pennants, the SHOE HIRE lightbox over the stripe band,
    a long run of shoe cubbies and the dark wainscot, all falling into shadow toward the floor."""
    L, Hh = int(Z_BACK - Z_NEAR) // 2, int(CEIL) // 2
    cv = Canvas(L, Hh, seed=31)
    indigo_wall(cv, 0, 0, L, Hh, seed=31)
    league_pennants(cv, 0, L - 1, 4, sag=3, every=11, seed=4)
    cv.rect(146, 16, 3, 9, CHROME[1]); cv.rect(146, 16, 3, 1, CHROME[3])     # the projecting sign's bracket
    stripe_band(cv, 0, 31, L)
    mini_cubbies(cv, 52, 45, 120, 22, cols=12, seed=3, sole="#a8a094")
    cv.rect(0, 70, L, Hh - 70, PANEL[2]); cv.rect(0, 70, L, 2, PANEL[4]); cv.hline(0, 70, L, PANEL[5])
    for px in range(3, L - 8, 14):
        cv.rect(px, 74, 11, Hh - 78, PANEL[1]); cv.rect(px + 1, 75, 9, Hh - 80, PANEL[3])
    a = doubled(cv)
    rows = np.arange(a.shape[0])[:, None]
    dim = np.where(rows < 60, 0.95, np.where(rows < 90, 0.85, np.where(rows < 130, 0.7, 0.56)))
    a[..., :3] *= dim[..., None]
    return a


def east_wall_tex():
    """The arcade side: the same indigo and stripe band, teal light washing up from the cabinets."""
    L, Hh = int(Z_BACK - Z_NEAR) // 2, int(CEIL) // 2
    cv = Canvas(L, Hh, seed=32)
    indigo_wall(cv, 0, 0, L, Hh, seed=32)
    league_pennants(cv, 0, L - 1, 4, sag=3, every=11, seed=5)
    stripe_band(cv, 0, 31, L)
    for (r, a) in [(30, 0.08), (22, 0.1), (14, 0.12)]:
        cv.rect(0, Hh - r - 20, L, r + 20, C("#58e0d0", a))
    cv.rect(0, 70, L, Hh - 70, PANEL[2]); cv.rect(0, 70, L, 2, PANEL[4])
    return doubled(cv)


def cabinet_front(height, kind):
    """One arcade cabinet's front, in world units (u along the row, v down from the top): lit
    marquee, the screen glowing with a game, control panel, coin door."""
    body, glow, bright = CAB_COLOURS[kind]
    w, h = int(CAB_DEPTH), int(height)
    cv = Canvas(w, h)
    cv.rect(0, 0, w, h, "#120f1a")
    cv.rect(1, 0, w - 2, h, body)
    # marquee
    cv.rect(2, 2, w - 4, 10, bright); cv.rect(3, 3, w - 6, 8, shade(glow, 0.5))
    for k in range(5, w - 6, 4):
        cv.rect(k, 5, 2, 4, body)
    # screen bezel and screen
    sy = 15
    cv.rect(2, sy, w - 4, 24, "#0a0812")
    cv.rect(4, sy + 2, w - 8, 20, mix(glow, "#0a0812", 0.55))
    for yy in range(sy + 3, sy + 22, 3):
        cv.hline(5, yy, w - 10, C(glow, 0.55))
    cv.rect(w // 2 - 4, sy + 9, 8, 6, bright); cv.rect(w // 2 - 2, sy + 10, 4, 3, "#ffffff")
    # control panel
    cv.rect(0, sy + 26, w, 8, "#2a2638"); cv.hline(0, sy + 26, w, CHROME[2])
    for bxp in (8, 14, 20, 24):
        cv.rect(bxp, sy + 29, 2, 2, CONFETTI[bxp % 4])
    # coin door, lit coin slots
    cv.rect(w // 2 - 6, h - 22, 12, 14, "#1a1622"); cv.rect(w // 2 - 3, h - 19, 2, 3, "#ff8a3a"); cv.rect(w // 2 + 1, h - 19, 2, 3, "#ff8a3a")
    cv.rect(0, h - 4, w, 4, "#0a0812")
    return cv.a


def cabinet_side(height, kind):
    """The side panel seen end-on: black laminate, a sweep of side art, a bright T-moulding edge."""
    body, glow, bright = CAB_COLOURS[kind]
    w, h = int(X_EAST - X_CAB), int(height)
    cv = Canvas(w, h)
    cv.rect(0, 0, w, h, "#16121e")
    cv.poly([(0, h * 0.45), (w, h * 0.25), (w, h * 0.38), (0, h * 0.6)], body)
    cv.poly([(0, h * 0.62), (w, h * 0.4), (w, h * 0.45), (0, h * 0.68)], glow)
    cv.rect(0, 0, 3, h, bright); cv.vline(1, 0, h, "#ffffff")
    cv.rect(0, 0, w, 2, bright)
    cv.rect(0, h - 4, w, 4, "#0a0812")
    return cv.a


# ---------------------------------------------------------------------------------------------
# the far wall, painted at its on-screen size
# ---------------------------------------------------------------------------------------------

def mini_mural(cv, x, y, w, h, seed=0):
    """The masking mural at battle scale: violet night, stars, a ringed planet and a crescent moon,
    bowling-ball comets, the Flatirons and the lit campus roofline along the bottom."""
    rng = np.random.default_rng(seed)
    bands = ["#1a1640", "#211a4c", "#2a1f58", "#352462", "#43296a"]
    bh = h / len(bands)
    for i, c in enumerate(bands):
        cv.rect(x, y + int(i * bh), w, int(bh) + 1, c)
        if i:
            for xx in range(x, x + w, 2):
                cv.px(xx + (i % 2), y + int(i * bh), bands[i - 1])
    for _ in range(w * h // 70):
        cv.px(x + int(rng.integers(1, w - 1)), y + int(rng.integers(1, h - 8)), "#8a86c8" if rng.random() < 0.6 else "#c8c4f0")
    stars = []
    for _ in range(9):
        sx, sy = x + int(rng.integers(4, w - 4)), y + int(rng.integers(2, h - 10))
        cv.px(sx, sy, "#fff4dc")
        stars.append((sx, sy))
    # ringed planet
    px, py = x + 30, y + 7
    cv.ellipse(px - 4, py - 4, 9, 9, "#3a7aa8"); cv.ellipse(px - 3, py - 3, 6, 6, "#58a0c8"); cv.px(px - 1, py - 2, "#8ad0e8")
    for kx in range(-8, 9):
        if abs(kx) > 4 or kx > 0:
            cv.px(px + kx, py + int(round(kx * 0.25)) + 1, "#e8c070")
    # crescent moon
    mx, my = x + w - 30, y + 6
    cv.ellipse(mx - 4, my - 4, 9, 9, "#f6e7c4"); cv.ellipse(mx - 2, my - 5, 9, 9, bands[0])
    # bowling-ball comets
    for (bx, by, tail, col, tc) in [(x + 84, y + 6, 18, "#c4407a", "#ff8ab8"), (x + 150, y + 11, 14, "#2a8a86", "#6ae0d0"),
                                    (x + w - 64, y + 4, 12, "#5a3ab0", "#9a7ae8")]:
        for i, (ln, a) in enumerate([(tail, 0.3), (tail * 2 // 3, 0.45), (tail // 3, 0.65)]):
            cv.rect(bx - ln, by - 1 + (1 if i == 2 else 0), ln, 3 - (1 if i == 2 else 0), C(tc, a))
        cv.ellipse(bx - 2, by - 2, 5, 5, col); cv.px(bx - 1, by - 1, tc); cv.px(bx + 1, by, OUT)
    # Flatirons, pines and the roofline
    base = y + h
    ridge = [(xx, base - 7 - 2 * math.sin(i * 0.5) - 1.5 * math.sin(i * 1.3)) for i, xx in enumerate(range(x, x + w + 1, 3))]
    cv.poly(ridge + [(x + w, base), (x, base)], "#241a3c")
    cv.rect(x, base - 3, w, 3, "#18142a")
    for xx in range(x, x + w, 5):
        cv.px(xx + int(rng.integers(0, 3)), base - 4, "#18142a")
    return stars


def far_wall():
    """Returns the far wall Canvas, its screen origin and the points other layers need."""
    s = 320.0 / Z_BACK
    fx0 = int(round(VX + X_WEST * s)) - 1
    W = int(round((X_EAST - X_WEST) * s)) + 3
    Hh = int(round(CEIL * s))
    fy0 = int(round(H0 + CAM * s)) - Hh

    def lx(X):
        return int(round(VX + X * s)) - fx0

    cv = Canvas(W, Hh, seed=8)
    indigo_wall(cv, 0, 0, W, Hh, seed=8)
    # ceiling edge and the fascia that carries the neon (lettered later at 1:1)
    cv.rect(0, 0, W, 3, "#0c0a16"); cv.hline(0, 3, W, "#2a2438")
    cv.rect(0, 4, W, 17, mix(INDIGO[1], INDIGO[2], 0.5))
    stripe_band(cv, 0, 22, W)
    # west part: CLUB service door between two runs of cubbies, the wainscot under them
    wx1 = lx(-HALF - EDGE) - 1
    cv.rect(0, 62, wx1, Hh - 62, PANEL[2]); cv.hline(0, 62, wx1, PANEL[4])
    mini_cubbies(cv, 3, 36, 20, 22, cols=3, seed=5)
    mini_cubbies(cv, wx1 - 20, 36, 18, 22, cols=3, seed=6)
    dx = (wx1 + 23) // 2
    cv.rect(dx - 10, 35, 20, Hh - 35, OUT)
    cv.rect(dx - 9, 36, 18, Hh - 36, "#4a5a68"); cv.rect(dx - 7, 38, 14, Hh - 38, "#3a4a5a")
    cv.rect(dx - 4, 41, 8, 9, "#e9a84a"); cv.rect(dx - 4, 41, 8, 4, "#f6cd78")
    cv.rect(dx - 6, 54, 12, 2, "#c0c4cc")
    cv.rect(dx - 4, 58, 8, 4, PAPER[2])
    cv.rect(dx - 3, 31, 6, 2, "#5cc28a"); halo(cv, dx, 32, 6, colour="#5cc28a", strength=0.1)
    # east part: the practice alcove with its nine pins and the rack of house balls
    ex0 = lx(HALF + EDGE) + 1
    cv.rect(ex0, 62, W - ex0, Hh - 62, PANEL[2]); cv.hline(ex0, 62, W - ex0, PANEL[4])
    pcx = ex0 + 14
    cv.rect(pcx - 11, 44, 22, Hh - 44, OUT); cv.rect(pcx - 10, 45, 20, Hh - 45, CHROME[1])
    cv.rect(pcx - 9, 46, 18, Hh - 46, "#0c0a14"); cv.rect(pcx - 9, 46, 18, 1, "#fff0c8")
    for i, a in enumerate([0.06, 0.08, 0.1]):
        cv.rect(pcx - 9, 50 + i * 7, 18, Hh - 50 - i * 7, C("#ffe8c0", a))
    rx = ex0 + 30
    for tier, ty in enumerate((52, 66)):
        cv.rect(rx, ty, 22, 2, CHROME[2])
        for k in range(4):
            col, hi = BALLS[(k + tier * 2) % len(BALLS)]
            cv.ellipse(rx + 1 + k * 5, ty - 5, 5, 5, col); cv.px(rx + 2 + k * 5, ty - 4, hi)
    # the masking mural across the lanes, lane numbers, the pit openings and kickbacks
    mx0, mx1 = lx(-HALF - EDGE), lx(HALF + EDGE)
    stars = mini_mural(cv, mx0, 31, mx1 - mx0, 22, seed=9)
    stars = [(fx0 + sx, fy0 + sy) for (sx, sy) in stars]
    cv.rect(mx0 - 1, 31, 1, 22, CHROME[1]); cv.rect(mx1, 31, 1, 22, CHROME[1])
    cv.rect(mx0, 53, mx1 - mx0, 1, CHROME[2]); cv.rect(mx0, 54, mx1 - mx0, 1, "#0a0810")
    pits = []
    for k in range(7):
        xa, xb = lx(-HALF + BAY * k + 6), lx(-HALF + BAY * k + 70)
        pits.append((xa, xb))
        cv.rect(xa, 55, xb - xa, Hh - 55, "#0c0a14")
        cv.rect(xa + 1, 57, xb - xa - 2, 4, "#16121e"); cv.ellipse((xa + xb) // 2 - 6, 57, 12, 6, "#1e1828")
        cv.rect(xa, 55, xb - xa, 1, "#fff0c8"); cv.hline(xa, 56, xb - xa, "#a8946a")
        cv.rect(xa, 62, xb - xa, 2, "#2a2432"); cv.hline(xa, 63, xb - xa, SAFETY[1])
        for i, a in enumerate([0.06, 0.08, 0.11]):
            yy = 64 + i * 3
            cv.rect(xa, yy, xb - xa, Hh - yy, C("#ffe8c0", a))
        # lane number on the masking
        n = str(k + 1)
        cxn = (xa + xb) // 2
        cv.rect(cxn - 4, 43, 9, 10, OUT); cv.rect(cxn - 3, 44, 7, 8, "#14101e")
        text(cv, n, cxn - 2, 44, "#f6cf7a")
    for k in range(8):
        xa, xb = lx(-HALF + BAY * k - 6), lx(-HALF + BAY * k + 6)
        cv.rect(xa, 55, xb - xa, Hh - 55, "#16121e")
        cv.vline(xa, 55, Hh - 55, CHROME[1]); cv.vline(xb - 1, 55, Hh - 55, "#0a0810")
    cv.hline(0, Hh - 1, W, "#0a0810")
    return cv, fx0, fy0, stars, pits


# ---------------------------------------------------------------------------------------------
# crisp pieces at 1:1 on the reduced frame
# ---------------------------------------------------------------------------------------------

PIN_SPRITE = [".W.", ".Ws", ".r.", ".W.", "WWs", "WWs", ".s."]
PIN_SPOTS = [(-18, 33), (-6, 33), (6, 33), (18, 33), (-12, 22), (0, 22), (12, 22), (-6, 11), (6, 11), (0, 0)]


def draw_pin(cv, x, base, lean=0):
    pal = {"W": "#fbf4ff", "s": "#c8c0dc", "r": PIN[3]}
    rows = PIN_SPRITE
    for yy, row in enumerate(rows):
        off = 0
        if lean and yy < 3:
            off = lean
        for xx, ch in enumerate(row):
            if ch != ".":
                cv.px(x - 1 + xx + off, base - len(rows) + yy, pal[ch])


def pin_positions(k, spread=0.0, hop=0):
    """Screen positions (x, base, lean) of lane k's ten pins, back row first. spread pushes them
    toward the kickbacks (pixels at the head pin's depth), hop lifts them."""
    Xc = lane_x(k)
    out = []
    for i, (dx, dz) in enumerate(PIN_SPOTS):
        Z = Z_PIN + dz
        x, y = scr(Xc + dx, Z)
        row = {33: 0, 22: 1, 11: 2, 0: 3}[dz]
        base = int(round(y)) + row // 2
        side = np.sign(dx) if dx else (1 if i % 2 else -1)
        if spread:
            x += side * spread * (0.5 + abs(dx) / 24.0)
        out.append((int(round(x)), base - hop * (1 if dz else 2), int(side) if spread else 0))
    return out


def draw_pins(cv, k, spread=0.0, hop=0):
    for (x, base, lean) in pin_positions(k, spread, hop):
        cv.hline(x - 1, base, 3, C("#2a2232", 0.5))
        draw_pin(cv, x, base, lean)


def lane_marks(cv):
    """Foul line, the two rows of approach dots, the targeting arrows."""
    yf = int(round(scr(0, Z_FOUL)[1]))
    xa, _ = scr(-HALF - EDGE, Z_FOUL)
    xb, _ = scr(HALF + EDGE, Z_FOUL)
    cv.hline(int(round(xa)), yf, int(round(xb - xa)), "#1a1220")
    for k in range(7):
        Xc = lane_x(k)
        for Zd in (Z_FOUL - 18, Z_FOUL - 52):
            for d in (-12, -6, 0, 6, 12):
                x, y = scr(Xc + d, Zd)
                cv.px(int(round(x)), int(round(y)), C(MAPLE[1], 0.85))
        for j in range(-3, 4):
            x, y = scr(Xc + j * 5.5, Z_ARROW + (3 - abs(j)) * 8)
            cv.px(int(round(x)), int(round(y)), C(MAPLE[0], 0.9))
            if abs(j) < 3:
                cv.px(int(round(x)), int(round(y)) - 1, C(MAPLE[1], 0.6))


def ceiling_stars(rng, n=26):
    """Fibre-optic stars in the ceiling tiles (screen points between the tubes)."""
    pts = []
    while len(pts) < n:
        x, y = int(rng.integers(20, 620)), int(rng.integers(2, 28))
        if 392 <= x <= 628 and y <= 70:
            continue
        if x < 70 and y < 28:
            continue
        pts.append((x, y))
    return pts


# ---------------------------------------------------------------------------------------------

def mover_phase(t_period, length, rate):
    """Which blink frames see the ball arrive: movers put lane balls at p = frac(t / period + c0),
    with c0 from the engine's per-layer hash; returns the pattern indices for p in a window."""
    c0 = 0.3 * ((math.sin(9 * 78.233) * 43758.5453) % 1.0)
    idx = lambda p: int(math.floor(length * (p - c0))) % length
    return idx


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    res = f"res://assets/art/rooms/{ROOM}/"
    os.makedirs(out, exist_ok=True)
    v = View(horizon=H0, vx=VX, cam=CAM, fill="#0c0a14")
    v.ground(ceiling_shader, y_from=0, y_to=H0 - 0.01, height=CEIL)
    v.ground(floor_shader)
    L = int(Z_BACK - Z_NEAR)
    for X, tex in ((X_WEST, west_wall_tex()), (X_EAST, east_wall_tex())):
        def shade_wall(u, Y, Z, tex=tex):
            o = texture_lookup(tex, u, CEIL - Y, wrap=False)
            fog(o, Z, "#100d1c", 600, 900, amount=0.35)
            return o
        v.plane((X, Z_NEAR), (X, Z_BACK), shade_wall, y_max=CEIL)
    flat, fx0, fy0, mural_stars, pits = far_wall()
    v.strip(flat.a, fy0, fx0)
    # arcade cabinets along the east wall, far to near
    for (z0, hgt, kind) in sorted(CABINETS, reverse=True):
        front, side = cabinet_front(hgt, kind), cabinet_side(hgt, kind)

        def shade_front(u, Y, Z, tex=front, h=hgt):
            o = texture_lookup(tex, u, h - Y, wrap=False)
            fog(o, Z, "#100d1c", 600, 900, amount=0.3)
            return o

        def shade_side(u, Y, Z, tex=side, h=hgt):
            return texture_lookup(tex, u, h - Y, wrap=False)
        v.plane((X_CAB, z0), (X_CAB, z0 + CAB_DEPTH), shade_front, y_max=hgt)
        v.plane((X_CAB, z0), (X_EAST, z0), shade_side, y_max=hgt)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp: the neon over the pins, its stuttering N
    sign = neon_text(cv, "THE CONNECTION", VX, fy0 + 6, NEON_PINK, scale=2)
    for gx in (sign[0] - 12, sign[0] + sign[2] + 11):
        cv.px(gx, fy0 + 12, NEON_GOLD[2]); cv.px(gx - 1, fy0 + 12, NEON_GOLD[1]); cv.px(gx + 1, fy0 + 12, NEON_GOLD[1])
        cv.px(gx, fy0 + 11, NEON_GOLD[1]); cv.px(gx, fy0 + 13, NEON_GOLD[1])
    lane_marks(cv)
    # SHOE HIRE on a lightbox projecting from the west wall, square to the camera
    hx, hy = scr(X_WEST + 2, 592.0, 140.0)
    hx, hy = int(round(hx)), int(round(hy))
    cv.rect(hx - 2, hy - 4, 26, 2, CHROME[1]); cv.hline(hx - 2, hy - 4, 26, CHROME[2])
    for rx in (hx + 4, hx + 20):
        cv.vline(rx, hy - 3, 3, CHROME[1])
    lightbox(cv, hx, hy, 60, 13, "SHOE HIRE")
    rng = np.random.default_rng(14)
    stars = ceiling_stars(rng)
    for (x, y) in stars:
        cv.px(x, y, CONFETTI[(x + y) % 4] if (x + y) % 3 else "#fff4dc")
    base = Canvas(cv.w, cv.h)
    base.a = cv.a.copy()                       # the frame without pins, for the dodge frames
    for k in range(7):
        draw_pins(cv, k)
    # the practice alcove's nine pins
    pcx = fx0 + int(round(VX + (HALF + EDGE) * 320.0 / Z_BACK)) - fx0 + 15
    for i, dx in enumerate((-6, -2, 2, 6, -4, 0, 4)):
        draw_pin(cv, pcx + dx, fy0 + 71 + (1 if i >= 4 else 0))

    # stuttering N: dim in the frame, lit by a blink texture
    sx, sy, sw, sh = sign
    m = text_mask("THE CONNECTION", 2)
    col0 = 7 * 12
    letter = m[:, col0:col0 + 12]
    lxn, lyn = sx + col0, sy
    lit = Canvas(13, sh + 1)
    keep = np.zeros((sh + 1, 13), bool)
    keep[:sh, :12] |= letter
    keep[1:, 1:] |= letter
    lit.a[keep] = cv.a[lyn:lyn + sh + 1, lxn:lxn + 13][keep]
    lit.save(os.path.join(out, "battle-neon-n.png"))
    full = np.zeros((cv.h, cv.w), bool)
    full[lyn:lyn + sh, lxn:lxn + 12] = letter
    cv.fill_mask(full, "#4a2038")

    layers = [{"kind": "blink", "pattern": "11111111111111111111101011111111111111111111111111111110", "rate": 9.0,
               "texture": res + "battle-neon-n.png", "x": lxn, "y": lyn}]

    # balls rolling up lanes 4 and 5; the pins hop aside as each one arrives
    rate = 5.0
    balls = []
    for (k, period, core, glow) in BALL_LANES:
        Xc = lane_x(k)
        x0, y0 = scr(Xc, Z_FOUL + 6)
        x1, y1 = scr(Xc, Z_PIN - 4)
        frm, to = [round(x0, 1), round(y0 - 2, 1)], [round(x1, 1), round(y1 - 1, 1)]
        balls.append({"kind": "movers", "from": frm, "to": to, "count": 1, "period": period, "size": [13, 6],
                      "color": glow + "60", "ease": "out"})
        balls.append({"kind": "movers", "from": frm, "to": to, "count": 1, "period": period, "size": [7, 3],
                      "color": core, "ease": "out"})
        # dodge frames: a crop of the lane's deck with the pins parting (A) and fully apart (B)
        xs = [p[0] for p in pin_positions(k, 7, 2)]
        bx0, bx1 = min(xs) - 4, max(xs) + 5
        by1 = int(round(scr(Xc, Z_PIN)[1])) + 3
        by0 = by1 - 14
        for tag, spread, hop in (("a", 3, 1), ("b", 6, 2)):
            fr = Canvas(cv.w, cv.h)
            fr.a = base.a.copy()
            draw_pins(fr, k, spread, hop)
            crop = Canvas(bx1 - bx0, by1 - by0)
            crop.a = fr.a[by0:by1, bx0:bx1].copy()
            crop.save(os.path.join(out, f"battle-dodge-{k + 1}{tag}.png"))
        length = int(round(period * rate))
        idx = mover_phase(period, length, rate)
        pa, pb = ["0"] * length, ["0"] * length
        i0, i1 = idx(0.80), idx(1.04)
        span = [(i0 + j) % length for j in range((i1 - i0) % length + 1)]
        for j, s in enumerate(span):
            if j == 0 or j == len(span) - 1:
                pa[s] = "1"
            else:
                pb[s] = "1"
        for tag, pat in (("a", pa), ("b", pb)):
            layers.append({"kind": "blink", "pattern": "".join(pat), "rate": rate,
                           "texture": res + f"battle-dodge-{k + 1}{tag}.png", "x": bx0, "y": by0})
    layers += balls                            # drawn over the dodge frames

    cv.save(os.path.join(out, "battle-far.png"))
    layers += [
        {"kind": "twinkle", "points": [[x, y, "fff4dc", 1] for (x, y) in mural_stars] +
                                      [[x, y, "c8b4ff", 1] for (x, y) in stars[::2]], "rate": 1.3, "min": 0.15},
        {"kind": "beam", "x": 190, "y": 10, "angle": 98, "sweep": 20, "period": 7.0, "phase": 0.0, "length": 132,
         "width": 46, "color": "b48cff", "alpha": 0.22, "floor": 136},
        {"kind": "beam", "x": 360, "y": 8, "angle": 84, "sweep": 22, "period": 9.0, "phase": 2.2, "length": 128,
         "width": 42, "color": "ff7aa8", "alpha": 0.18, "floor": 132},
        {"kind": "beam", "x": 560, "y": 40, "angle": 112, "sweep": 14, "period": 8.0, "phase": 4.0, "length": 100,
         "width": 40, "color": "58e0d0", "alpha": 0.16, "floor": 134},
        {"kind": "particles", "style": "dust", "count": 18, "rect": [150, 40, 320, 100], "speed": [0, 3], "color": "c8b4ff"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:400])
