"""Old Main cabinet room (O04): a finite plan.

Back wall: oxblood damask under a stencilled gilt frieze and a dark crown, a walnut frame-and-panel
dado. In the middle, bolted to the wall over its ink-pad table, Todd's stamp-audit rig: a riveted
brass gantry on iron brackets with three stamps on pistons (DENIED, AUDIT, APPROVED), a caged red
AUDIT lamp, a pressure gauge, pipes. It flanks with brass sconces; a framed founding charter and an
oval portrait at the left, a photograph of the regents and a second portrait at the right; tall
windows dressed in green velvet at both ends, the moon in the left one.
Floor: walnut herringbone parquet, a straight border along the wall, the big worn red carpet in the
middle where Todd stands behind the finite-plan desk, moonlight from the windows, lamplight, and
the two way out at the front (the notice hall bottom left, the empty office bottom right).
Props: the finite-plan desk with the consent form (two boxes: ONE GATHERING / SHARED DUTIES and a
signature line, signed once the plan is chosen), an hourglass, the inkwell and a banker's lamp;
two tall walnut card cabinets; the ASK FIRST sign; a brass standard lamp with a fringed shade.
States: while todd_resolution is unset the rig is live (the red lamp pulses, the stamps thump);
peaceful: the rig at rest under a green FINITE PLAN / APPROVED sign; forceful: the AUDIT arm
wrenched loose, the lamp cracked, a REPAIRS PENDING tag, forms scattered on the floor."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from surfaces import light_pool
from props import OUT, ground_shadow
from lib_eng import micro_text, micro_width, scribble
from lib_norlin import depth_shade
from lib_oldmain import (cornice_om, stencil_frieze, damask, panel_wainscot, draped_window, oval_portrait, stamp_rig, card_cabinet,
                         persian_rug, herringbone, oak_boards, radiator, sconce_om, framed_photo, banker_lamp_om, spill, oak_frame,
                         OXBLOOD, WALNUT, PARQUET, VELVET_G, BRASS_OM, RUG_RED, GILT_OM, PAPER_TINTS, RED_STAMP, GREEN_STAMP,
                         CREAM_TRIM)

ROOM = "O04"
W, H = 800, 480
BASE = 142
WALK = (20, 142, 760, 314)
FLOOR_BOTTOM = WALK[1] + WALK[3]
DADO_Y = 100
FRIEZE_Y = 10
DAMASK = OXBLOOD[1:] + ["#b45a50"]          # one step brighter than the deep oxblood
RIG = (440, 14)                            # stamp rig: centre x, top
REST, MID, DOWN = -6, 0, 5                 # piston travel of the stamps
WIN_L = (50, 30, 34, 62)
WIN_R = (716, 30, 34, 62)
SCONCES = ((290, 60), (586, 60))
LAMP = (135, 319)
DESK = (455, 369)
RUG = (282, 250, 344, 166)
GAPS = ((40, 110), (690, 760))             # openings in the front wall (hall, office service)


# ---------------------------------------------------------------------------- wall
def charter(cv, x, y, w, h):
    """The founding charter, framed: parchment, a heading, close lines of copperplate, two columns
    of signatures and a red wax seal on a ribbon."""
    oak_frame(cv, x, y, w, h, t=4, pal=WALNUT)
    cv.rect(x + 3, y + 3, w - 6, h - 6, GILT_OM[2]); cv.hline(x + 3, y + 3, w - 6, GILT_OM[4])
    px0, py0, pw, ph = x + 5, y + 5, w - 10, h - 10
    cv.rect(px0, py0, pw, ph, "#d8c8a0"); cv.rect(px0 + 1, py0 + 1, pw - 2, ph - 2, "#e4d6b0")
    cv.rect(px0, py0 + ph - 3, pw, 3, "#c8b68c"); cv.vline(px0 + pw - 2, py0, ph, "#ccba92")
    micro_text(cv, "CHARTER", px0 + (pw - micro_width("CHARTER")) // 2, py0 + 3, "#5a2a1e")
    cv.hline(px0 + 8, py0 + 10, pw - 16, "#9a8460")
    scribble(cv, px0 + 4, py0 + 13, pw - 8, "#7a6a50", seed=3, rows=5, gap=3)
    for k in range(2):
        scribble(cv, px0 + 5 + k * (pw // 2), py0 + ph - 10, pw // 2 - 12, "#3a2e3a", seed=7 + k, rows=2, gap=3)
    sx, sy = px0 + pw - 12, py0 + ph - 9
    cv.line(sx - 2, sy + 2, sx - 5, sy + 9, "#2a4a8a"); cv.line(sx + 2, sy + 2, sx + 4, sy + 9, "#2a4a8a")
    cv.ellipse(sx - 4, sy - 4, 9, 9, "#5a1414"); cv.ellipse(sx - 3, sy - 3, 7, 7, "#9a2420"); cv.px(sx - 1, sy - 2, "#d8584a")


def back_wall(bg, state="active", lowered=(REST, REST, REST)):
    cornice_om(bg, 0, -3, W, ceiling=("#1a1418", "#261c22", "#33262c"), trim=CREAM_TRIM)
    stencil_frieze(bg, 0, FRIEZE_Y, W, ground=OXBLOOD[1], gilt=BRASS_OM, every=14)
    damask(bg, 0, FRIEZE_Y + 9, W, DADO_Y - FRIEZE_Y - 9, pal=DAMASK, seed=4, rep=(16, 20))
    # a band of shadow under the frieze, the picture rail
    bg.rect(0, FRIEZE_Y + 9, W, 2, C("#0d0b16", 0.35))
    bg.rect(0, 24, W, 2, WALNUT[3]); bg.hline(0, 24, W, WALNUT[6])
    panel_wainscot(bg, 0, DADO_Y, W, BASE - DADO_Y, pal=WALNUT, panel=36)
    # windows at both ends, the moon in the left one; radiators under them
    draped_window(bg, *WIN_L, seed=81, moon=(WIN_L[0] + 22, WIN_L[1] + 16, 5))
    draped_window(bg, *WIN_R, seed=82)
    for (wx, wy, ww, wh) in (WIN_L, WIN_R):
        radiator(bg, wx + 1, DADO_Y + 12, ww - 2, 22)
    # portraits, the charter, the regents' photograph
    oval_portrait(bg, 130, 54, rx=11, ry=15, seed=1, bg="#2e3a36")
    oval_portrait(bg, 670, 54, rx=11, ry=15, seed=2, bg="#36303e")
    for (px_, cx_) in ((130, 130), (670, 670)):
        bg.line(cx_, 26, cx_ - 8, 37, BRASS_OM[2]); bg.line(cx_, 26, cx_ + 8, 37, BRASS_OM[2])
    charter(bg, 168, 30, 78, 58)
    framed_photo(bg, 604, 34, 40, 30, seed=5, rows=2)
    pw = micro_width("REGENTS") + 4
    bg.rect(624 - pw // 2, 66, pw, 7, BRASS_OM[2]); bg.hline(624 - pw // 2, 66, pw, BRASS_OM[4])
    micro_text(bg, "REGENTS", 624 - pw // 2 + 2, 67, "#2a1a10")
    # the stamp rig and its sconces
    glows = [sconce_om(bg, x, y) for (x, y) in SCONCES]
    pts = stamp_rig(bg, RIG[0], RIG[1], state=state, lowered=lowered)
    bg.hline(0, BASE - 1, W, C("#0d0b16", 0.6))
    return pts, glows


# ---------------------------------------------------------------------------- floor
def floor(bg):
    mask = np.zeros((H, W), bool)
    mask[BASE:, :] = True
    pq = [PARQUET[0], PARQUET[1], PARQUET[3], PARQUET[4], PARQUET[4], PARQUET[5], PARQUET[5]]
    herringbone(bg, mask, pal=pq, mortar=PARQUET[2], seed=11, a=6)
    # a border of straight boards along the wall
    oak_boards(bg, 0, BASE, W, 9, seed=3, pal=PARQUET, row=9)
    bg.hline(0, BASE + 9, W, PARQUET[0]); bg.hline(0, BASE + 10, W, PARQUET[6])
    bg.rect(0, BASE, W, 3, C("#0d0b16", 0.45)); bg.rect(0, BASE + 3, W, 2, C("#0d0b16", 0.2))
    # the carpet: Todd stands on it behind the desk
    rx, ry, rw, rh = RUG
    ground_shadow(bg, rx + rw // 2, ry + rh + 1, rw // 2 + 4, 2, alpha=0.3)
    persian_rug(bg, rx, ry, rw, rh, seed=6)
    rng = np.random.default_rng(5)
    for _ in range(60):          # worn where people stood at the desk
        tx, ty = int(rng.integers(rx + 110, rx + rw - 110)), int(rng.integers(ry + rh - 46, ry + rh - 18))
        bg.rect(tx, ty, int(rng.integers(2, 6)), 1, RUG_RED[3])
    # moonlight from both windows, sash bars in it
    for (wx, wy, ww, wh) in (WIN_L, WIN_R):
        sl = 34
        bg.poly([(wx - 2, BASE + 3), (wx + ww + 2, BASE + 3), (wx + ww + 2 + sl, 214), (wx - 2 + sl, 214)], C("#b4c4f0", 0.11))
        mx_ = wx + ww // 2
        bg.poly([(mx_ - 1, BASE + 3), (mx_ + 2, BASE + 3), (mx_ + 2 + sl, 214), (mx_ - 1 + sl, 214)], C("#0d0b16", 0.12))
        bg.poly([(wx - 2 + sl // 2, 178), (wx + ww + 2 + sl // 2, 178), (wx + ww + 2 + sl // 2 + 1, 180), (wx - 1 + sl // 2, 180)],
                C("#0d0b16", 0.12))
    # an oval rug under the standard lamp, an iron floor register by the right window
    oval_rug(bg, LAMP[0] - 4, LAMP[1] + 4, 62, 20)
    register(bg, 700, 318)
    register(bg, 236, 404)
    # lamplight: the standard lamp, the desk lamp, the sconces on the wall foot
    light_pool(bg, LAMP[0], LAMP[1] + 2, 56, 16, strength=0.26)
    light_pool(bg, DESK[0] - 56, DESK[1] + 4, 96, 18, strength=0.15)
    for (sx, sy) in SCONCES:
        light_pool(bg, sx + 4, BASE + 8, 40, 7, strength=0.12)
    light_pool(bg, RIG[0], BASE + 10, 70, 10, color="#e04a3a", strength=0.08)
    # the two ways out at the front: lamplight from the notice hall and the empty office
    for (a, b), col in zip(GAPS, ("#f6cf7a", "#f0c070")):
        spill(bg, a - 18, FLOOR_BOTTOM - 54, b - a + 36, H - FLOOR_BOTTOM + 54, col,
              steps=((1.0, 0.06), (0.6, 0.06), (0.3, 0.07)), side="bottom")
    # small things dropped: index cards by the cabinets, a pen, a paper clip
    for (fx, fy) in ((182, 236), (268, 242), (566, 233), (652, 262), (520, 438)):
        bg.rect(fx, fy, 7, 4, "#e8dcc0"); bg.hline(fx, fy, 7, "#fff6dc"); bg.hline(fx + 1, fy + 2, 5, C("#3a3a5a", 0.5))
    bg.line(230, 300, 236, 298, "#2a2a3a"); bg.px(236, 298, BRASS_OM[4])
    depth_shade(bg, 0, 420, W, H - 420, steps=3, alpha=0.16)


def oval_rug(cv, cx, cy, rx, ry):
    """A small oval rug: gold-edged navy ring, an oxblood field, a gold rosette."""
    cv.ellipse(cx - rx - 1, cy - ry - 1, 2 * rx + 3, 2 * ry + 3, C("#0d0b16", 0.4))
    cv.ellipse(cx - rx, cy - ry, 2 * rx + 1, 2 * ry + 1, RUG_RED[0])
    cv.ellipse(cx - rx + 1, cy - ry + 1, 2 * rx - 1, 2 * ry - 1, RUG_RED[6])
    cv.ellipse(cx - rx + 2, cy - ry + 2, 2 * rx - 3, 2 * ry - 3, RUG_RED[5])
    cv.ellipse(cx - rx + 6, cy - ry + 4, 2 * rx - 11, 2 * ry - 7, RUG_RED[6])
    cv.ellipse(cx - rx + 7, cy - ry + 5, 2 * rx - 13, 2 * ry - 9, RUG_RED[2])
    for k in range(0, 360, 20):
        a = np.radians(k)
        cv.px(int(cx + (rx - 4) * np.cos(a)), int(cy + (ry - 2) * np.sin(a)), RUG_RED[7])
    cv.poly([(cx, cy - 5), (cx + 12, cy), (cx, cy + 5), (cx - 12, cy)], RUG_RED[6])
    cv.poly([(cx, cy - 3), (cx + 7, cy), (cx, cy + 3), (cx - 7, cy)], RUG_RED[3])


def register(cv, x, y):
    """A cast-iron floor register: a frame and a grille of slots, flat in the parquet."""
    cv.rect(x - 1, y - 1, 24, 12, OUT)
    cv.rect(x, y, 22, 10, "#3a3a46"); cv.hline(x, y, 22, "#5a5a6a")
    for k in range(3, 20, 3):
        cv.vline(x + k, y + 2, 6, "#121218")
    cv.px(x + 1, y + 1, "#7a7a8a"); cv.px(x + 20, y + 8, "#7a7a8a")


def front_and_margins(bg):
    fy = FLOOR_BOTTOM + 8
    edges = [0] + [v for g in GAPS for v in g] + [W]
    for a, b in zip(edges[0::2], edges[1::2]):
        bg.rect(a, fy, b - a, H - fy, WALNUT[3]); bg.hline(a, fy, b - a, WALNUT[6]); bg.hline(a, fy + 1, b - a, WALNUT[4])
        bg.hline(a, fy + 4, b - a, WALNUT[2])
    for (a, b) in GAPS:
        for jx in (a - 4, b):
            bg.rect(jx, fy - 1, 4, H - fy + 1, OUT); bg.rect(jx + 1, fy, 2, H - fy, WALNUT[4]); bg.vline(jx + 1, fy, H - fy, WALNUT[6])
    for x0_, inner in ((0, 9), (W - 10, 0)):
        bg.rect(x0_, BASE, 10, FLOOR_BOTTOM - BASE, OXBLOOD[2]); bg.vline(x0_ + inner, BASE, FLOOR_BOTTOM - BASE, OXBLOOD[5])
    bg.rect(0, BASE, WALK[0], H - BASE, C("#0d0b16", 0.36))
    bg.rect(WALK[0] + WALK[2], BASE, W - WALK[0] - WALK[2], H - BASE, C("#0d0b16", 0.36))
    bg.rect(0, FLOOR_BOTTOM, W, H - FLOOR_BOTTOM, C("#0d0b16", 0.38))


def scattered_forms(cv, seed=8):
    """Forms shaken off the rig when it was wrenched: fanned across the parquet below it."""
    rng = np.random.default_rng(seed)
    for k in range(14):
        fx = int(rng.integers(RIG[0] - 100, RIG[0] + 90))
        fy = int(rng.integers(BASE + 6, BASE + 40))
        w_, h_ = int(rng.integers(8, 12)), int(rng.integers(5, 7))
        tint = PAPER_TINTS[int(rng.integers(0, 3))]
        sk = int(rng.integers(-2, 3))
        cv.poly([(fx, fy), (fx + w_, fy + sk), (fx + w_ + 1, fy + sk + h_), (fx + 1, fy + h_)], C("#0d0b16", 0.35))
        cv.poly([(fx - 1, fy - 1), (fx + w_ - 1, fy + sk - 1), (fx + w_, fy + sk + h_ - 1), (fx, fy + h_ - 1)], tint)
        cv.hline(fx + 1, fy + 1, w_ - 3, C("#5a4a3a", 0.5))
        if rng.random() < 0.4:
            cv.rect(fx + w_ - 5, fy + h_ - 4, 3, 2, C(RED_STAMP[2], 0.85))
    # the AUDIT stamp block itself, knocked off its piston
    x, y = RIG[0] + 30, BASE + 22
    cv.rect(x - 1, y - 1, 22, 9, OUT); cv.rect(x, y, 20, 3, WALNUT[3]); cv.rect(x, y + 3, 20, 4, RED_STAMP[2])
    micro_text(cv, "AUDIT", x + 1, y + 2, "#fff0e0")


# ---------------------------------------------------------------------------- props
def consent_form(cv, x, y, signed=False):
    """The consent form on its writing slope: CONSENT, two explicit boxes, a signature line."""
    w, h = 46, 26
    cv.poly([(x - 2, y + h + 1), (x + w + 1, y + h + 1), (x + w - 2, y - 1), (x + 1, y - 1)], OUT)
    cv.poly([(x - 1, y + h), (x + w, y + h), (x + w - 3, y), (x + 2, y)], WALNUT[4])
    cv.hline(x - 1, y + h, w + 1, WALNUT[2])
    px0, py0 = x + 3, y + 2
    cv.rect(px0, py0, w - 6, h - 4, "#f2e8cc"); cv.hline(px0, py0, w - 6, "#fff8e2"); cv.vline(px0 + w - 7, py0, h - 4, "#d4c8a6")
    micro_text(cv, "CONSENT", px0 + (w - 6 - micro_width("CONSENT")) // 2, py0 + 1, "#5a2a1e")
    for k in range(2):
        by = py0 + 8 + k * 5
        cv.rect(px0 + 2, by, 4, 4, "#3a2e3a"); cv.rect(px0 + 3, by + 1, 2, 2, "#f2e8cc")
        cv.hline(px0 + 8, by + 2, 22 - k * 4, "#6a5a5a")
    cv.hline(px0 + 3, py0 + h - 7, w - 14, "#3a2e3a")
    cv.px(px0 + 1, py0 + h - 8, "#3a2e3a"); cv.px(px0 + 2, py0 + h - 9, "#3a2e3a")
    if signed:
        sx = px0 + 6
        for k, dy in enumerate((0, -2, 1, -1, 0, -3, 1, 0, -1, 0, -2, 1, 0)):
            cv.px(sx + k * 2, py0 + h - 9 + dy, "#1e2a5a"); cv.px(sx + k * 2 + 1, py0 + h - 9 + dy // 2, "#1e2a5a")
        cv.rect(px0 + w - 16, py0 + 8, 8, 8, C(GREEN_STAMP[2], 0.75)); cv.rect(px0 + w - 15, py0 + 9, 6, 6, C("#f2e8cc", 0.5))
        cv.rect(px0 + w - 14, py0 + 10, 4, 4, C(GREEN_STAMP[2], 0.9))


def hourglass(cv, x, y):
    """A small brass hourglass, most of the sand still above (x, y = bottom-left)."""
    cv.rect(x - 1, y - 14, 11, 15, C("#0d0b16", 0))
    cv.rect(x, y - 2, 9, 2, OUT); cv.hline(x, y - 2, 9, BRASS_OM[4])
    cv.rect(x, y - 14, 9, 2, OUT); cv.hline(x, y - 14, 9, BRASS_OM[4])
    for px_ in (x, x + 8):
        cv.vline(px_, y - 12, 10, BRASS_OM[3])
    cv.poly([(x + 2, y - 12), (x + 6, y - 12), (x + 4, y - 7)], C("#c8d8e8", 0.55))
    cv.poly([(x + 4, y - 7), (x + 7, y - 3), (x + 1, y - 3)], C("#c8d8e8", 0.55))
    cv.poly([(x + 2, y - 11), (x + 6, y - 11), (x + 4, y - 8)], "#d8b260")
    cv.vline(x + 4, y - 7, 3, "#d8b260"); cv.hline(x + 3, y - 3, 3, "#d8b260")


def finite_plan_desk(width=180, height=44, seed=0, signed=False, items=True):
    """The finite-plan desk: a walnut pedestal desk with a green leather top and a brass FINITE PLAN
    plaque on its apron; on it the consent form on a writing slope, an inkwell and a dip pen, a
    small hourglass, a wire tray of forms and a lit banker's lamp."""
    cv = Canvas(width + 8, height + 32, seed=seed)
    ox, base = 4, height + 30
    top = base - height
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    cv.rect(ox - 2, top, width + 4, 9, OUT)
    cv.rect(ox - 1, top + 1, width + 2, 6, WALNUT[5]); cv.hline(ox - 1, top + 1, width + 2, WALNUT[6])
    cv.rect(ox + 8, top + 2, width - 16, 4, VELVET_G[3]); cv.hline(ox + 8, top + 2, width - 16, VELVET_G[5])
    cv.hline(ox + 8, top + 5, width - 16, VELVET_G[2])
    cv.hline(ox - 1, top + 7, width + 2, WALNUT[2])
    fy = top + 9
    cv.rect(ox, fy, width, base - fy, OUT)
    cv.rect(ox + 1, fy, width - 2, base - fy - 1, WALNUT[3]); cv.vline(ox + 1, fy, base - fy - 1, WALNUT[5])
    pw = 52
    for px_ in (ox + 5, ox + width - 5 - pw):
        for k in range(3):
            dy = fy + 3 + k * 9
            cv.rect(px_, dy, pw, 8, WALNUT[1]); cv.rect(px_ + 1, dy + 1, pw - 2, 6, WALNUT[4]); cv.hline(px_ + 1, dy + 1, pw - 2, WALNUT[6])
            cv.rect(px_ + pw // 2 - 4, dy + 3, 8, 2, BRASS_OM[3]); cv.px(px_ + pw // 2 - 4, dy + 3, BRASS_OM[5])
    kx0, kx1 = ox + 5 + pw + 4, ox + width - 9 - pw
    cv.rect(kx0, fy + 3, kx1 - kx0, 10, WALNUT[1]); cv.rect(kx0 + 1, fy + 4, kx1 - kx0 - 2, 8, WALNUT[4]); cv.hline(kx0 + 1, fy + 4, kx1 - kx0 - 2, WALNUT[6])
    lab = "FINITE PLAN"
    lw = micro_width(lab) + 6
    lx = kx0 + (kx1 - kx0 - lw) // 2
    cv.rect(lx - 1, fy + 4, lw + 2, 9, OUT); cv.rect(lx, fy + 5, lw, 7, BRASS_OM[3]); cv.hline(lx, fy + 5, lw, BRASS_OM[5])
    micro_text(cv, lab, lx + 3, fy + 6, "#2a1a10")
    cv.rect(kx0, fy + 15, kx1 - kx0, base - fy - 18, WALNUT[0])
    cv.rect(kx0 + 3, fy + 16, kx1 - kx0 - 6, base - fy - 21, WALNUT[1])
    cv.rect(kx0 + 3, fy + 16, kx1 - kx0 - 6, 3, "#120a08")
    cv.vline(kx0, fy + 15, base - fy - 18, WALNUT[2]); cv.vline(kx1 - 1, fy + 15, base - fy - 18, WALNUT[2])
    cv.rect(ox, base - 4, width, 4, OUT); cv.rect(ox + 1, base - 4, width - 2, 3, WALNUT[2]); cv.hline(ox + 1, base - 4, width - 2, WALNUT[4])
    if not items:
        return cv, ox + width // 2, base
    banker_lamp_om(cv, ox + 20, top + 4, lit=True)
    # wire tray of blank forms
    tx = ox + 40
    cv.rect(tx - 1, top - 5, 24, 6, OUT); cv.rect(tx, top - 4, 22, 4, "#8a8e96")
    for j in range(3):
        cv.hline(tx + 1 + j, top - 5 - j, 20, PAPER_TINTS[j])
    cv.vline(tx, top - 4, 4, "#b4bcc8"); cv.vline(tx + 21, top - 4, 4, "#b4bcc8")
    consent_form(cv, ox + width // 2 - 23, top - 26, signed=signed)
    # inkwell and dip pen, the hourglass, a hand stamp set aside on its pad
    ix = ox + width // 2 + 34
    cv.rect(ix - 1, top - 6, 9, 7, OUT); cv.rect(ix, top - 5, 7, 5, "#2a3a5a"); cv.hline(ix, top - 5, 7, "#5a6a9a")
    cv.rect(ix + 2, top - 8, 3, 3, BRASS_OM[3])
    cv.line(ix + 4, top - 7, ix + 10, top - 17, "#1e1a22"); cv.px(ix + 10, top - 17, "#e8dcc0")
    hourglass(cv, ox + width - 44, top + 1)
    sx = ox + width - 26
    cv.rect(sx - 1, top - 2, 14, 3, OUT); cv.rect(sx, top - 2, 12, 2, GREEN_STAMP[1])
    cv.rect(sx + 3, top - 9, 6, 7, OUT); cv.rect(sx + 4, top - 8, 4, 5, WALNUT[5]); cv.rect(sx + 2, top - 4, 8, 2, GREEN_STAMP[2])
    return cv, ox + width // 2, base


def ask_first_sign(width=82, height=50, seed=0):
    """A lacquered placard on a brass easel stand: ASK FIRST, and under it NO BLANK / SIGNATURE LINES,
    with a little form showing an empty line struck through."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 2
    top = base - height
    ground_shadow(cv, ox + width // 2, base, width // 2 - 8, 2)
    bh = 36
    # easel legs and the cross bar
    for (x0, x1) in ((ox + 14, ox + 8), (ox + width - 14, ox + width - 8)):
        cv.line(x0, top + bh - 2, x1, base - 1, OUT); cv.line(x0 + 1, top + bh - 2, x1 + 1, base - 1, BRASS_OM[3])
    cv.line(ox + width // 2, top + bh - 2, ox + width // 2 + 4, base - 1, OUT)
    cv.hline(ox + 12, base - 6, width - 24, BRASS_OM[2])
    # the placard
    cv.rect(ox, top, width, bh, OUT)
    cv.rect(ox + 1, top + 1, width - 2, bh - 2, BRASS_OM[3]); cv.hline(ox + 1, top + 1, width - 2, BRASS_OM[5])
    cv.rect(ox + 3, top + 3, width - 6, bh - 6, "#141018"); cv.rect(ox + 4, top + 4, width - 8, bh - 8, "#1e1820")
    cv.hline(ox + 4, top + 4, width - 8, "#2e2630")
    t = "ASK FIRST"
    text(cv, t, ox + (width - text_width(t)) // 2, top + 4, "#f2d690")
    cv.hline(ox + 12, top + 15, width - 24, BRASS_OM[2])
    for k, line in enumerate(("NO BLANK", "SIGNATURE LINES")):
        micro_text(cv, line, ox + (width - micro_width(line)) // 2, top + 18 + k * 7, "#e8dcc0")
    cv.px(ox + 6, top + 6, BRASS_OM[5]); cv.px(ox + width - 7, top + 6, BRASS_OM[5])
    cv.px(ox + 6, top + bh - 7, BRASS_OM[5]); cv.px(ox + width - 7, top + bh - 7, BRASS_OM[5])
    return cv, ox + width // 2, base


def fringe_lamp(height=68):
    """A brass standard lamp with an oxblood silk shade and a gold fringe. Bulb ~5px below the top."""
    w = 26
    cv = Canvas(w, height + 6)
    cx, base = w // 2, height + 3
    top = base - height
    ground_shadow(cv, cx, base, 8, 2)
    cv.ellipse(cx - 7, base - 5, 15, 6, OUT); cv.ellipse(cx - 6, base - 5, 13, 5, BRASS_OM[2]); cv.hline(cx - 4, base - 5, 9, BRASS_OM[4])
    cv.rect(cx - 2, top + 14, 4, base - top - 18, OUT)
    cv.vline(cx - 1, top + 14, base - top - 18, BRASS_OM[4]); cv.vline(cx, top + 14, base - top - 18, BRASS_OM[2])
    for ky in (top + 32, base - 14):
        cv.rect(cx - 3, ky, 6, 3, OUT); cv.rect(cx - 2, ky + 1, 4, 1, BRASS_OM[5])
    cv.poly([(cx - 5, top), (cx + 5, top), (cx + 10, top + 11), (cx - 10, top + 11)], OUT)
    cv.poly([(cx - 4, top + 1), (cx + 4, top + 1), (cx + 9, top + 10), (cx - 9, top + 10)], "#a8463c")
    cv.poly([(cx - 3, top + 1), (cx - 1, top + 1), (cx - 4, top + 10), (cx - 8, top + 10)], "#d0705a")
    cv.vline(cx + 4, top + 2, 8, "#7a2e2a")
    cv.hline(cx - 10, top + 11, 21, OUT)
    for fx in range(cx - 10, cx + 11):
        cv.vline(fx, top + 12, 2 + (fx % 2), BRASS_OM[4] if fx % 2 else BRASS_OM[3])
    cv.rect(cx - 2, top + 12, 5, 2, "#fff0c4")
    return cv, cx, base


# ---------------------------------------------------------------------------- build
def _crop(cv, box):
    x, y, w, h = box
    out = Canvas(w, h)
    out.a[:] = cv.a[y:y + h, x:x + w]
    return out


def wall_render(state="active", lowered=(REST, REST, REST)):
    bg = Canvas(W, H, fill="#171a2b", seed=1)
    pts, glows = back_wall(bg, state=state, lowered=lowered)
    floor(bg)
    front_and_margins(bg)
    return bg, pts, glows


def lamp_lit(bg, pts):
    """The AUDIT lamp and sign lit red, painted over a copy of the room: the frame of the pulse."""
    cv = Canvas(W, H)
    cv.a[:] = bg.a
    lx, ly = pts["lamp"]
    for rr, a in ((17, 0.05), (12, 0.07), (8, 0.1)):
        cv.ellipse(lx - rr, ly - rr, rr * 2 + 1, rr * 2 + 1, C("#ff4a3a", a))
    cv.ellipse(lx - 4, ly - 3, 9, 9, RED_STAMP[3]); cv.ellipse(lx - 3, ly - 2, 6, 5, RED_STAMP[4]); cv.px(lx - 1, ly - 1, "#ffe0d0")
    for k in (-3, 0, 3):
        cv.vline(lx + k, ly - 4, 9, "#4a4a58")
    cv.hline(lx - 5, ly, 11, "#4a4a58")
    sx, sy, sw, sh = pts["sign"]
    cv.rect(sx, sy, sw, sh, "#2a0e10")
    text(cv, "AUDIT", sx + sw // 2 - text_width("AUDIT") // 2, sy - 1, "#ff6a50")
    return _crop(cv, (lx - 24, ly - 17, 48, 40))


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg, pts, glows = wall_render("active")
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, name=None, flag=None, flag_made=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        if flag:
            fs, _, _ = flag_made
            fname = name.replace(".png", f"-{flag}.png")
            fs.save(os.path.join(out, fname))
            entry.update({"flag": flag, "flag_texture": res + fname})
        props[str(index)] = entry

    save(0, finite_plan_desk(180, 44, seed=3), flag="finite_plan", flag_made=finite_plan_desk(180, 44, seed=3, signed=True))
    save(1, card_cabinet(135, 112, seed=21, ladder=True, label="FORMS A-L"))
    save(2, card_cabinet(135, 112, seed=22, ladder=False, label="FORMS M-Z"))
    save(3, ask_first_sign(82, 50))
    save(4, fringe_lamp(68))

    # the rig's three states: live (background + layers), approved, damaged
    bx, by, bw, bh = pts["box"]
    box = (bx, by, bw, bh)
    overlays = []
    for state, equals in (("approved", "peaceful"), ("damaged", "forceful")):
        cv, _, _ = wall_render(state)
        name = f"rig-{state}.png"
        _crop(cv, box).save(os.path.join(out, name))
        overlays.append({"texture": res + name, "x": bx, "y": by, "flag": "todd_resolution", "equals": equals})
    forms = Canvas(240, 50)
    tmp = Canvas(W, H)
    scattered_forms(tmp)
    forms.a[:] = tmp.a[BASE:BASE + 50, RIG[0] - 120:RIG[0] + 120]
    forms.save(os.path.join(out, "forms-scattered.png"))
    overlays.append({"texture": res + "forms-scattered.png", "x": RIG[0] - 120, "y": BASE, "flag": "todd_resolution", "equals": "forceful"})

    layers = []
    # live rig: the red lamp pulses and the three stamps thump in turn
    lit = lamp_lit(bg, pts)
    lit.save(os.path.join(out, "rig-lamp.png"))
    lx, ly = pts["lamp"]
    layers.append({"kind": "blink", "pattern": "110000", "rate": 3.0, "texture": res + "rig-lamp.png", "x": lx - 24, "y": ly - 17,
                   "flag": "todd_resolution", "when": False})
    beam_top = pts["stamps"][0][1]
    table = pts["table"]
    n = 18
    for k, (sx, sy) in enumerate(pts["stamps"]):
        crop = (sx - 22, beam_top, 44, table + 1 - beam_top)
        for f, low in (("mid", MID), ("down", DOWN)):
            lowered = [REST, REST, REST]
            lowered[k] = low
            cv, _, _ = wall_render("active", tuple(lowered))
            name = f"stamp-{k}-{f}.png"
            _crop(cv, crop).save(os.path.join(out, name))
            pat = ["0"] * n
            start = k * 6
            if f == "mid":
                pat[start % n] = "1"; pat[(start + 2) % n] = "1"
            else:
                pat[(start + 1) % n] = "1"
            layers.append({"kind": "blink", "pattern": "".join(pat), "rate": 7.0, "texture": res + name, "x": crop[0], "y": crop[1],
                           "flag": "todd_resolution", "when": False})
    lamp_head = (LAMP[0], LAMP[1] - 56)
    layers += [
        {"kind": "twinkle", "points": [[g[0], g[1], "fde9b6", 1] for g in glows] + [[lamp_head[0], lamp_head[1], "fff0c4", 2],
                                       [DESK[0] - 70, DESK[1] - 48, "fde9b6", 1]], "rate": 1.1, "min": 0.55},
        {"kind": "particles", "style": "dust", "count": 16, "rect": [WIN_L[0] - 10, WIN_L[1] + 30, 90, 150], "speed": [-1, 2], "color": "c8d4f0"},
        {"kind": "particles", "style": "dust", "count": 10, "rect": [WIN_R[0] - 10, WIN_R[1] + 30, 70, 150], "speed": [-1, 2], "color": "c8d4f0"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": overlays,
        "fauna": [
            {"kind": "lamp_moth", "x": LAMP[0] + 4, "y": LAMP[1] - 58, "range": 7, "speed": 1.8, "rate": 8.0},
            {"kind": "umc2_mouse", "x": 720, "y": BASE + 6, "range": 22, "speed": 0.3, "rate": 4.0, "flip": True},
        ],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(paths.PROJECT)
