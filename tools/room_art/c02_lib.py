"""The CU Book Store (C02) inside the UMC, open late, and its battle backdrop. Some pieces (the store
ceiling, the bottom doorway, the chalkboard a-frame) are shared with the Career Center (C03).

The store wears the Buffs' black and gold (CU gold is #cfb87c) against warm putty walls, the same
black-and-gold awning and gold-lettered fascia the shop shows on the Fountain Court (C01). Sections:
  palettes ............ GOLD, BLACK, HEATHER, PUTTY, TILE_S, CARPET_S, TEXTBOOK
  walls ............... store_wall, store_ceiling, header_sign, wall_shadow
  textbooks ........... textbook_row, price_strip, textbook_wall (built in), shelf_tex (battle)
  gear ................ slatwall, hoodie, cap, folded_stack, buffalo_plaque, gear_wall, cubby_wall
  back of house ....... staff_door, hours_plaque, dome_camera, store_clock
  floors .............. store_floor, carpet_zone, entry_mat, doorway_gap
  props ............... gondola, tee_table, round_rack, plush_bin, checkout_counter, spinner_rack, chalk_aframe
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, ground_shadow
from surfaces import light_pool
from lib_eng import micro_text, micro_width
from lib_umc import halo, soft_ellipse
from lib_umc2 import buffalo, CHROME

# --- palettes ---------------------------------------------------------------------------------
GOLD = ["#4a3614", "#7a5c24", "#a8843a", "#cfb87c", "#e6d29a", "#f6e8c0"]       # CU gold, shadow to lit
BLACK = ["#0c0b10", "#16141c", "#211e28", "#2c2834", "#3a3644", "#4a4656"]      # Buffs black, night-lifted
HEATHER = ["#3e3e48", "#5a5a64", "#76767e", "#93939a", "#b0b0b6"]
WHITE_T = ["#8a8a90", "#b8b6b4", "#dcdad4", "#f2f0ea"]
PUTTY = ["#3a3034", "#54464a", "#6a5a5a", "#7a6866", "#887672", "#98867e", "#a89488"]   # warm store wall
MAPLE = ["#5a3a24", "#7e5634", "#a07444", "#ba8c56", "#d0a46a", "#e2bc84"]      # fixture wood
TILE_S = ["#3a3236", "#5a4e4e", "#6c605c", "#7a6c66", "#86786e", "#968676"]     # porcelain floor
CARPET_S = ["#1c1b27", "#252332", "#2e2b3e", "#37344a", "#423f58"]             # charcoal carpet tile
TEXTBOOK = ["#c8382c", "#2a5aa8", "#3a8a5a", "#e8a03a", "#7a3a8a", "#2a8a96", "#d85a2a", "#5a6a7a",
            "#a82a4a", "#1e3a6e", "#6a8a2a", "#e0c040", "#3a3a4a", "#b85a7a"]
STICKER = "#f2d23a"                                                              # yellow USED sticker
SHADOW = "#0d0b16"


def _rng(seed):
    return np.random.default_rng(seed)


# --- walls ------------------------------------------------------------------------------------
def store_wall(cv, x, y, w, h, seed=0, pal=PUTTY):
    """Painted drywall: an even putty field with soft 2-3 px roller marks, a stepped shade under
    the ceiling and a dark rubber base at the floor."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[4])
    for _ in range(w * h // 70):
        px_, py_ = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        c = pal[3] if rng.random() < 0.55 else pal[5]
        cv.hline(px_, py_, int(rng.integers(2, 4)), c)
    for (hh, a) in [(10, 0.14), (5, 0.12), (2, 0.14)]:
        cv.rect(x, y, w, hh, C(SHADOW, a))
    cv.rect(x, y + h - 5, w, 5, BLACK[2]); cv.hline(x, y + h - 5, w, BLACK[4])


def store_ceiling(cv, x, w, h=12, cans=(), lit=True, pal=BLACK):
    """A dark ceiling band with a lip, recessed downlights and their stepped glow on the wall."""
    cv.rect(x, 0, w, h, pal[1])
    cv.hline(x, h - 3, w, pal[3]); cv.hline(x, h - 2, w, pal[4]); cv.hline(x, h - 1, w, pal[2])
    cv.hline(x, h, w, C(SHADOW, 0.55))
    for cx in cans:
        cv.rect(cx - 4, h - 3, 9, 3, pal[0]); cv.rect(cx - 3, h - 2, 7, 2, "#fff0c4" if lit else pal[4])
        if lit:
            halo(cv, cx, h + 6, 16, colour="#f6cf7a", strength=0.08, steps=3)


def wall_shadow(cv, x, y, w):
    """Contact shadow where the floor meets the wall."""
    cv.rect(x, y, w, 2, C(SHADOW, 0.45)); cv.rect(x, y + 2, w, 2, C(SHADOW, 0.2))


def header_sign(cv, cx, y, label, fg=GOLD[4], bg=BLACK[1], frame=GOLD[2], rods=True, pad=8):
    """A black fascia panel with a gold keyline and gold lettering, hung on two rods from the ceiling."""
    w = text_width(label) + pad * 2
    x = cx - w // 2
    if rods:
        for rx in (x + 6, x + w - 7):
            cv.vline(rx, 10, y - 10, IRON[3]); cv.vline(rx + 1, 10, y - 10, IRON[1])
    cv.rect(x - 1, y - 1, w + 2, 15, OUT)
    cv.rect(x, y, w, 13, bg)
    cv.rect(x + 1, y + 1, w - 2, 11, frame); cv.rect(x + 2, y + 2, w - 4, 9, bg)
    cv.hline(x, y, w, shade(bg, 0.2))
    text(cv, label, cx - text_width(label) // 2, y + 2, fg)
    return x, w


# --- textbooks --------------------------------------------------------------------------------
def textbook_row(cv, x, base, w, max_h, seed=0, dim=0.0, used=0.25, faceout=0.08):
    """New and used textbooks standing on a shelf from x to x+w, bottoms on row base-1. Textbooks are
    thick, glossy and loud: wide spines in saturated colours, a pale title band near the top, a
    publisher block at the foot, yellow USED stickers on some, the odd one turned face-out."""
    rng = _rng(seed)
    bx, end = x, x + w
    while bx < end - 2:
        r = rng.random()
        if r < faceout and end - bx > 16:
            # a face-out cover leaning back: a coloured board with a simple cover graphic
            cw = int(rng.integers(12, 15))
            ch = min(max_h, int(rng.integers(max_h - 3, max_h + 1)))
            c = shade(TEXTBOOK[int(rng.integers(len(TEXTBOOK)))], -dim)
            top = base - ch
            cv.rect(bx, top, cw, ch, OUT); cv.rect(bx + 1, top + 1, cw - 2, ch - 1, c)
            cv.hline(bx + 1, top + 1, cw - 2, shade(c, 0.3))
            cv.rect(bx + 2, top + 3, cw - 4, 2, shade(WHITE_T[3], -dim))          # title bar
            g = int(rng.integers(3))
            mx, my = bx + cw // 2, top + ch // 2 + 2
            if g == 0:      # a sine wave (calculus)
                for k in range(cw - 4):
                    cv.px(bx + 2 + k, my + int(round(np.sin(k * 0.9) * 2)), shade(WHITE_T[2], -dim))
            elif g == 1:    # a molecule (chemistry)
                for (dx, dy) in [(-3, -1), (2, -2), (0, 2)]:
                    cv.line(mx, my, mx + dx, my + dy, shade(WHITE_T[1], -dim))
                    cv.rect(mx + dx - 1, my + dy - 1, 2, 2, shade(GOLD[4], -dim))
            else:           # a triangle (a mountain, a pyramid, a supply curve)
                cv.poly([(mx - 4, my + 3), (mx, my - 3), (mx + 4, my + 3)], shade(c, -0.35))
                cv.line(mx, my - 3, mx + 4, my + 3, shade(WHITE_T[2], -dim - 0.2))
            if rng.random() < 0.5:
                cv.rect(bx + cw - 5, top + ch - 6, 3, 3, shade(STICKER, -dim))
            bx += cw + 1
            continue
        bw = int(rng.choice([4, 5, 5, 6, 6, 7]))
        bh = int(rng.integers(max(6, int(max_h * 0.72)), max_h + 1))
        if bx + bw > end:
            bw = end - bx
            if bw < 3:
                break
        c = shade(TEXTBOOK[int(rng.integers(len(TEXTBOOK)))], -dim + float(rng.uniform(-0.05, 0.05)))
        top = base - bh
        cv.rect(bx, top, bw, bh, c)
        cv.vline(bx, top, bh, shade(c, 0.28))
        cv.vline(bx + bw - 1, top, bh, shade(c, -0.3))
        cv.hline(bx, top, bw, shade(c, 0.36))
        if bh > 9:
            cv.rect(bx + 1, top + 2, bw - 2, 2, shade(WHITE_T[3], -dim - 0.05))                  # title band
            cv.px(bx + 1 + int(rng.integers(0, max(1, bw - 2))), top + 3, shade(c, -0.2))
            cv.rect(bx + 1, base - 4, bw - 2, 2, shade(c, -0.45))                                 # publisher block
            cv.px(bx + bw // 2, base - 4, shade(WHITE_T[2], -dim))
        if rng.random() < used and bh > 11:
            cv.rect(bx + 1, top + bh // 2, bw - 2, 3, shade(STICKER, -dim))
            cv.hline(bx + 1, top + bh // 2 + 1, bw - 2, shade(STICKER, -dim - 0.25))
        elif rng.random() < 0.3:
            cv.px(bx + 1, top + 5 + int(rng.integers(0, max(1, bh - 9))), shade("#ffffff", -dim - 0.1))   # shrink-wrap glint
        bx += bw


def price_strip(cv, x, y, w, seed=0, dim=0.0):
    """The shelf-edge label channel: white strip, small price tags, the odd yellow USED tag."""
    rng = _rng(seed)
    cv.rect(x, y, w, 3, shade(WHITE_T[2], -dim)); cv.hline(x, y, w, shade(WHITE_T[3], -dim))
    cv.hline(x, y + 3, w, C(SHADOW, 0.6))
    xx = x + int(rng.integers(2, 8))
    while xx < x + w - 6:
        c = STICKER if rng.random() < 0.3 else "#f6f4ee"
        cv.rect(xx, y, 5, 3, shade(c, -dim)); cv.hline(xx + 1, y + 1, 3, shade("#3a3a4a", -dim))
        xx += int(rng.integers(12, 22))


def textbook_wall(cv, x, y, w, h, depts=("MATH", "CHEM", "PHYS", "WRTG"), seed=0, shelf=24):
    """Built-in black metal shelving, one bay per department: a gold-lettered black bay header,
    rows of textbooks, white price strips on every shelf edge, uprights between bays."""
    rng = _rng(seed)
    cv.rect(x - 3, y - 3, w + 6, h + 3, OUT)
    cv.rect(x - 2, y - 2, w + 4, h + 2, BLACK[3]); cv.hline(x - 2, y - 2, w + 4, BLACK[5])
    cv.rect(x, y, w, h, BLACK[1])
    n = len(depts)
    bay = w / n
    for k, dept in enumerate(depts):
        bx0, bx1 = x + int(round(k * bay)), x + int(round((k + 1) * bay))
        # bay header
        cv.rect(bx0 + 1, y + 1, bx1 - bx0 - 2, 9, BLACK[0]); cv.hline(bx0 + 1, y + 9, bx1 - bx0 - 2, GOLD[2])
        micro_text(cv, dept, (bx0 + bx1) // 2 - micro_width(dept) // 2, y + 3, GOLD[4])
        n = max(1, round((h - 17) / shelf))
        step = (h - 17) / n
        for r in range(n):
            sy = y + 11 + int(round(r * step))
            sh = int(round((r + 1) * step)) - int(round(r * step))
            cv.rect(bx0 + 1, sy, bx1 - bx0 - 2, sh - 4, BLACK[1])
            cv.hline(bx0 + 1, sy, bx1 - bx0 - 2, BLACK[0])
            textbook_row(cv, bx0 + 2, sy + sh - 4, bx1 - bx0 - 4, sh - 7, seed=seed * 53 + k * 11 + r, dim=0.05 * r)
            price_strip(cv, bx0 + 1, sy + sh - 4, bx1 - bx0 - 2, seed=seed + k * 7 + r, dim=0.03 * r)
        # a dangling course tag on the top shelf of each bay
        tx = bx0 + 6 + int(rng.integers(0, max(1, int(bay) - 22)))
        cv.rect(tx, y + 11 + shelf - 1, 10, 7, "#f6f4ee"); cv.hline(tx, y + 11 + shelf - 1, 10, "#ffffff")
        cv.hline(tx + 2, y + 13 + shelf, 6, "#3a3a4a")
        cv.hline(tx + 2, y + 15 + shelf, 4, "#7a7a8a")
        # upright
        if k:
            cv.rect(bx0 - 1, y, 3, h, BLACK[3]); cv.vline(bx0 - 1, y, h, BLACK[5])
            for py_ in range(y + 14, y + h - 4, 6):
                cv.px(bx0, py_, BLACK[0])
    cv.rect(x, y + h - 6, w, 6, BLACK[2]); cv.hline(x, y + h - 6, w, BLACK[4])   # kick plate


def shelf_tex(length, height, seed=0, shelf=26, bay=64, depts=("MATH", "CHEM", "PHYS", "CSCI", "ECON", "WRTG", "ASTR", "PSYC")):
    """A run of gondola shelving laid out flat for a perspective plane (battle): bays of textbooks,
    price strips, department headers, overstock boxes on top."""
    rng = _rng(seed)
    cv = Canvas(length, height, seed=seed)
    top_band = 22
    cv.rect(0, 0, length, top_band, (0, 0, 0, 0))
    # overstock cartons and a few shrink-wrapped bundles along the top
    xx = int(rng.integers(0, 10))
    while xx < length - 20:
        bw, bh = int(rng.integers(16, 30)), int(rng.integers(9, 18))
        if rng.random() < 0.75:
            k = ["#b08a5a", "#9a7448", "#c49c68"][int(rng.integers(3))]
            cv.rect(xx, top_band - bh, bw, bh, OUT); cv.rect(xx + 1, top_band - bh + 1, bw - 2, bh - 1, k)
            cv.hline(xx + 1, top_band - bh + 1, bw - 2, shade(k, 0.25)); cv.vline(xx + bw // 2, top_band - bh + 1, 3, "#d8c8a0")
            if rng.random() < 0.5:
                cv.rect(xx + 3, top_band - bh + 5, 8, 4, "#f2ecdc")
        xx += bw + int(rng.integers(4, 26))
    body = height - top_band
    cv.rect(0, top_band, length, body, BLACK[1])
    cv.rect(0, top_band, length, 3, BLACK[4]); cv.hline(0, top_band, length, BLACK[5])
    for k, bx0 in enumerate(range(0, length, bay)):
        bx1 = min(length, bx0 + bay)
        dept = depts[k % len(depts)]
        cv.rect(bx0 + 2, top_band + 4, bx1 - bx0 - 4, 9, BLACK[0]); cv.hline(bx0 + 2, top_band + 12, bx1 - bx0 - 4, GOLD[2])
        micro_text(cv, dept, (bx0 + bx1) // 2 - micro_width(dept) // 2, top_band + 6, GOLD[4])
        sy = top_band + 14
        r = 0
        while sy + shelf <= height - 10:
            textbook_row(cv, bx0 + 3, sy + shelf - 4, bx1 - bx0 - 6, shelf - 7, seed=seed * 31 + k * 5 + r, dim=0.0)
            price_strip(cv, bx0 + 1, sy + shelf - 4, bx1 - bx0 - 2, seed=seed + k + r)
            sy += shelf
            r += 1
        cv.rect(bx0, top_band, 3, body, BLACK[3]); cv.vline(bx0, top_band, body, BLACK[5])
    cv.rect(0, height - 10, length, 10, BLACK[2]); cv.hline(0, height - 10, length, BLACK[4])
    return cv.a


# --- gear -------------------------------------------------------------------------------------
def slatwall(cv, x, y, w, h, pal=BLACK, slat=6):
    """Black slatwall panel: horizontal slats with a lit lip and a dark groove."""
    cv.rect(x, y, w, h, pal[2])
    for sy in range(y, y + h, slat):
        cv.hline(x, sy, w, pal[3]); cv.hline(x, sy + slat - 2, w, pal[0]); cv.hline(x, sy + slat - 1, w, pal[1])


def hoodie(cv, cx, top, body, trim, letters="CU", ink=None, seed=0, hook=True):
    """A hoodie hung face-out on a waterfall hook, about 24 x 28: hood, shoulders, sleeves hanging
    straight, ribbed cuffs and hem, kangaroo pocket, drawstrings and the chest lettering."""
    rng = _rng(seed)
    ink = ink or trim
    if hook:
        cv.hline(cx - 5, top - 3, 11, CHROME[2]); cv.px(cx, top - 4, CHROME[3]); cv.vline(cx, top - 2, 2, CHROME[1])
    lo, hi, dk = shade(body, 0.16), shade(body, 0.3), shade(body, -0.3)
    # body and sleeves (silhouette first, ink outline)
    cv.rect(cx - 10, top + 3, 21, 25, OUT)
    cv.rect(cx - 12, top + 4, 4, 22, OUT); cv.rect(cx + 9, top + 4, 4, 22, OUT)
    cv.rect(cx - 9, top + 4, 19, 23, body)
    cv.rect(cx - 11, top + 5, 3, 20, shade(body, -0.12)); cv.rect(cx + 9, top + 5, 3, 20, shade(body, -0.2))
    cv.rect(cx - 11, top + 23, 3, 2, trim); cv.rect(cx + 9, top + 23, 3, 2, trim)          # cuffs
    cv.hline(cx - 9, top + 4, 19, lo); cv.vline(cx - 9, top + 4, 22, lo)
    cv.vline(cx + 9, top + 4, 22, dk)
    cv.rect(cx - 9, top + 25, 19, 2, trim); cv.hline(cx - 9, top + 25, 19, shade(trim, 0.2))  # hem rib
    for (sx, d) in [(cx - 12, 1), (cx + 12, -1)]:                                         # sloped shoulders
        cv.px(sx, top + 4, (0, 0, 0, 0)); cv.px(sx + d, top + 3, (0, 0, 0, 0))
        cv.px(sx + d, top + 4, OUT); cv.px(sx + 2 * d, top + 3, OUT)
    cv.vline(cx - 8, top + 7, 17, shade(body, -0.25)); cv.vline(cx + 8, top + 7, 17, shade(body, -0.35))  # sleeve seams
    # hood: a rounded cowl behind the neck with its lit rim
    cv.ellipse(cx - 6, top - 1, 13, 9, OUT)
    cv.ellipse(cx - 5, top, 11, 7, shade(body, -0.08)); cv.hline(cx - 3, top, 7, hi)
    cv.ellipse(cx - 3, top + 2, 7, 4, shade(body, -0.45))
    cv.vline(cx - 2, top + 5, 3, trim); cv.vline(cx + 2, top + 5, 2, trim)                  # drawstrings
    # kangaroo pocket
    cv.hline(cx - 6, top + 19, 13, dk); cv.vline(cx - 6, top + 19, 5, dk); cv.vline(cx + 6, top + 19, 5, dk)
    # chest lettering
    if letters == "CU":
        text(cv, "CU", cx - 6, top + 8, ink)
    elif letters:
        micro_text(cv, letters, cx - micro_width(letters) // 2, top + 11, ink)
    if rng.random() < 0.4:
        cv.rect(cx + 6, top + 6, 2, 4, "#f6f4ee")                                           # swing tag


def cap(cv, cx, y, crown, brim, logo=GOLD[3]):
    """A ball cap seen from the front on a peg (~11 x 8): dome, button, brim, a logo patch."""
    cv.ellipse(cx - 6, y, 13, 10, OUT)
    cv.ellipse(cx - 5, y + 1, 11, 8, crown)
    cv.hline(cx - 3, y + 1, 7, shade(crown, 0.25)); cv.px(cx, y, shade(crown, 0.3))
    cv.rect(cx - 7, y + 6, 15, 3, OUT); cv.rect(cx - 6, y + 6, 13, 2, brim); cv.hline(cx - 6, y + 6, 13, shade(brim, 0.25))
    cv.rect(cx - 1, y + 3, 3, 2, logo)


def folded_stack(cv, x, base, w, n, colours, seed=0, logo=True):
    """Folded tees stacked flat, seen from the front: 3 px folds with a lit crease and a shadowed
    underside, slightly misaligned; the top shirt shows a printed chest mark."""
    rng = _rng(seed)
    yy = base
    for k in range(n):
        c = colours[k % len(colours)]
        off = int(rng.integers(-1, 2))
        cv.rect(x + off - 1, yy - 4, w + 2, 5, OUT)
        cv.rect(x + off, yy - 3, w, 3, c)
        cv.hline(x + off, yy - 3, w, shade(c, 0.3)); cv.hline(x + off, yy - 1, w, shade(c, -0.3))
        cv.vline(x + off + w // 3, yy - 3, 2, shade(c, -0.15))
        yy -= 3
    if logo:
        top = colours[(n - 1) % len(colours)]
        ink = GOLD[3] if sum(C(top)[:3]) < 1.2 else BLACK[1]
        cv.rect(x + w // 2 - 2, yy, 5, 1, ink)
    return yy


def buffalo_plaque(cv, cx, cy, r=26):
    """A black disc with a double gold ring and a charging gold buffalo (Ralphie) across it."""
    cv.ellipse(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, OUT)
    cv.ellipse(cx - r, cy - r, 2 * r + 1, 2 * r + 1, GOLD[2])
    cv.ellipse(cx - r + 2, cy - r + 2, 2 * r - 3, 2 * r - 3, BLACK[1])
    cv.ellipse(cx - r + 4, cy - r + 4, 2 * r - 7, 2 * r - 7, GOLD[1])
    cv.ellipse(cx - r + 5, cy - r + 5, 2 * r - 9, 2 * r - 9, BLACK[1])
    for a in np.linspace(np.pi * 1.1, np.pi * 1.5, 9):
        cv.px(int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r)), GOLD[5])
    buffalo(cv, cx + 2, cy + 11, gold=GOLD[3], dark=GOLD[1], hi=GOLD[5])


def gear_wall(cv, x, y, w, h, seed=0):
    """The Buffs gear wall: black slatwall; a row of caps on pegs; two rows of face-out hoodies
    either side of the buffalo plaque; a shelf of folded tees along the bottom."""
    rng = _rng(seed)
    cv.rect(x - 3, y - 3, w + 6, h + 3, OUT)
    cv.rect(x - 2, y - 2, w + 4, h + 2, GOLD[2]); cv.hline(x - 2, y - 2, w + 4, GOLD[4])
    slatwall(cv, x, y, w, h)
    cx = x + w // 2
    styles = [(BLACK[2], GOLD[3], "CU", GOLD[4]), (GOLD[3], BLACK[2], "BUFFS", BLACK[1]), (HEATHER[3], BLACK[2], "CU", BLACK[1]),
              (BLACK[3], GOLD[3], "BUFFS", GOLD[4]), (WHITE_T[2], GOLD[2], "CU", BLACK[1]), (BLACK[2], WHITE_T[2], "SKO", WHITE_T[3])]
    # caps along the top
    for k, px_ in enumerate(range(x + 12, x + w - 8, 17)):
        if abs(px_ - cx) < 36:
            continue
        crown, brim = [(BLACK[2], BLACK[3]), (GOLD[3], GOLD[2]), (HEATHER[2], BLACK[2]), (WHITE_T[2], GOLD[3])][k % 4]
        cv.hline(px_ - 2, y + 5, 5, CHROME[2])
        cap(cv, px_, y + 6, crown, brim, logo=GOLD[3] if crown != GOLD[3] else BLACK[1])
    # two rows of hoodies
    k = 0
    for row_y in (y + 26, y + 62):
        for hx in range(x + 18, x + w - 12, 30):
            if abs(hx - cx) < 40:
                continue
            body, trim, letters, ink = styles[(k + (row_y > y + 40)) % len(styles)]
            hoodie(cv, hx, row_y, body, trim, letters, ink, seed=seed * 13 + k)
            k += 1
    buffalo_plaque(cv, cx, y + 38, r=27)
    s = "GO BUFFS"
    cv.rect(cx - text_width(s) // 2 - 4, y + 70, text_width(s) + 8, 12, BLACK[0])
    text(cv, s, cx - text_width(s) // 2, y + 71, GOLD[4])
    # a jersey under the plaque: #1 in gold numerals
    jx, jy = cx, y + 86
    cv.rect(jx - 11, jy, 23, 4, OUT); cv.rect(jx - 9, jy + 3, 19, 18, OUT)
    cv.rect(jx - 10, jy + 1, 21, 3, BLACK[2]); cv.rect(jx - 8, jy + 3, 17, 17, BLACK[2])
    cv.hline(jx - 10, jy + 1, 21, BLACK[4]); cv.rect(jx - 3, jy + 1, 7, 2, BLACK[0])
    cv.rect(jx - 10, jy + 3, 3, 2, GOLD[3]); cv.rect(jx + 8, jy + 3, 3, 2, GOLD[3])
    text(cv, "1", jx - 3, jy + 7, GOLD[4])
    # the bottom shelf with folded tees
    sy = y + h - 12
    cv.rect(x, sy, w, 3, MAPLE[3]); cv.hline(x, sy, w, MAPLE[5]); cv.hline(x, sy + 3, w, C(SHADOW, 0.6))
    tee_cols = [[BLACK[2], BLACK[3]], [GOLD[3], GOLD[4]], [HEATHER[3], HEATHER[2]], [WHITE_T[2], WHITE_T[3]]]
    for j, tx in enumerate(range(x + 6, x + w - 18, 22)):
        folded_stack(cv, tx, sy, 16, int(rng.integers(3, 6)), tee_cols[j % 4], seed=seed + j)


def cubby_wall(cv, x, y, w, h, cols=5, rows=3, seed=0):
    """Maple cubbies behind the counter: mugs, water bottles, plush buffaloes, mascot bobbleheads,
    gift boxes; one cubby holds the spare receipt rolls."""
    rng = _rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT)
    cv.rect(x - 1, y - 1, w + 2, h + 2, MAPLE[3]); cv.hline(x - 1, y - 1, w + 2, MAPLE[5])
    cw, ch = w // cols, h // rows
    kinds = ["mugs", "bottles", "plush", "boxes", "mugs", "rolls", "plush", "bottles", "boxes", "mugs", "plush", "bottles", "boxes", "mugs", "plush"]
    for r in range(rows):
        for c in range(cols):
            hx, hy = x + c * cw + 1, y + r * ch + 1
            iw, ih = cw - 2, ch - 3
            cv.rect(hx, hy, iw, ih, MAPLE[1]); cv.rect(hx, hy, iw, 3, MAPLE[0]); cv.vline(hx, hy, ih, MAPLE[0])
            cv.rect(hx - 1, hy + ih, iw + 2, 2, MAPLE[3]); cv.hline(hx - 1, hy + ih, iw + 2, MAPLE[4])
            base = hy + ih
            kind = kinds[(r * cols + c + seed) % len(kinds)]
            if kind == "mugs":
                for k in range(3):
                    mx = hx + 2 + k * (iw // 3)
                    col = [BLACK[3], GOLD[3], WHITE_T[2]][(k + r) % 3]
                    cv.rect(mx, base - 7, 6, 7, OUT); cv.rect(mx + 1, base - 6, 4, 6, col); cv.hline(mx + 1, base - 6, 4, shade(col, 0.3))
                    cv.rect(mx + 5, base - 5, 2, 3, OUT); cv.px(mx + 2, base - 4, GOLD[3] if col != GOLD[3] else BLACK[1])
            elif kind == "bottles":
                for k in range(4):
                    bx = hx + 2 + k * (iw // 4)
                    col = [GOLD[3], BLACK[3], HEATHER[3], "#3a6aa8"][(k + c) % 4]
                    cv.rect(bx, base - 10, 4, 10, OUT); cv.rect(bx + 1, base - 9, 2, 9, col); cv.px(bx + 1, base - 9, shade(col, 0.4))
                    cv.rect(bx + 1, base - 12, 2, 2, OUT)
            elif kind == "plush":
                for k in range(2):
                    px_ = hx + 4 + k * (iw // 2)
                    plush_buffalo(cv, px_ + 4, base, upside=False)
            elif kind == "boxes":
                yy = base
                for k in range(int(rng.integers(2, 4))):
                    bw = iw - 4 - int(rng.integers(0, 4))
                    col = [GOLD[3], BLACK[3], "#f2ecdc"][k % 3]
                    cv.rect(hx + 2, yy - 4, bw, 4, OUT); cv.rect(hx + 3, yy - 3, bw - 2, 3, col); cv.hline(hx + 3, yy - 3, bw - 2, shade(col, 0.3))
                    yy -= 4
            else:
                for k in range(3):
                    rx = hx + 3 + k * 5
                    cv.ellipse(rx, base - 6, 5, 6, "#f2ecdc"); cv.px(rx + 2, base - 3, "#a8a49c")


def plush_buffalo(cv, cx, base, upside=False, scarf=GOLD[3]):
    """A small plush buffalo (Ralphie), about 10 x 8, sitting; upside-down if asked."""
    fur, dark, hi = "#6a4430", "#4a2c20", "#8a5c40"
    if not upside:
        cv.ellipse(cx - 5, base - 8, 11, 8, OUT); cv.ellipse(cx - 4, base - 7, 9, 6, fur)
        cv.ellipse(cx - 4, base - 10, 7, 6, OUT); cv.ellipse(cx - 3, base - 9, 5, 4, dark)      # shaggy head
        cv.px(cx - 4, base - 10, "#e6d6b1"); cv.px(cx + 2, base - 10, "#e6d6b1")                # horns
        cv.px(cx - 2, base - 7, "#1a1418"); cv.px(cx + 1, base - 7, "#1a1418")
        cv.hline(cx - 3, base - 5, 7, scarf)
        cv.hline(cx - 3, base - 8, 2, hi)
    else:
        cv.ellipse(cx - 5, base - 7, 11, 7, OUT); cv.ellipse(cx - 4, base - 6, 9, 5, fur)
        cv.rect(cx - 4, base - 9, 2, 3, OUT); cv.rect(cx + 2, base - 9, 2, 3, OUT)             # legs in the air
        cv.px(cx - 4, base - 9, dark); cv.px(cx + 2, base - 9, dark)
        cv.hline(cx - 3, base - 3, 7, scarf)


# --- back of house ----------------------------------------------------------------------------
def staff_door(cv, cx, base, w=34, h=66):
    """A flat staff door in a steel frame: kick plate, push plate, a STAFF ONLY plaque."""
    x = cx - w // 2
    cv.rect(x - 3, base - h - 3, w + 6, h + 3, OUT)
    cv.rect(x - 2, base - h - 2, w + 4, h + 2, HEATHER[2]); cv.hline(x - 2, base - h - 2, w + 4, HEATHER[4])
    cv.rect(x, base - h, w, h, "#5a4e5a"); cv.vline(x, base - h, h, "#6e6270"); cv.vline(x + w - 1, base - h, h, "#3e3440")
    cv.rect(x + 2, base - 12, w - 4, 10, CHROME[1]); cv.hline(x + 2, base - 12, w - 4, CHROME[2])
    cv.rect(x + w - 8, base - h // 2 - 8, 4, 14, CHROME[2]); cv.vline(x + w - 8, base - h // 2 - 8, 14, CHROME[3])
    s = "STAFF"
    cv.rect(cx - 10, base - h + 12, 21, 13, BLACK[1]); cv.rect(cx - 9, base - h + 13, 19, 11, BLACK[0])
    micro_text(cv, s, cx - micro_width(s) // 2, base - h + 14, "#f2ecdc")
    micro_text(cv, "ONLY", cx - micro_width("ONLY") // 2, base - h + 20, "#e86a5a")


def hours_plaque(cv, x, y):
    """A small black plaque: STORE HOURS, OPEN LATE, and a sad face added in pen."""
    cv.rect(x, y, 30, 22, OUT); cv.rect(x + 1, y + 1, 28, 20, BLACK[1]); cv.hline(x + 1, y + 1, 28, BLACK[4])
    micro_text(cv, "HOURS", x + 15 - micro_width("HOURS") // 2, y + 3, GOLD[4])
    cv.hline(x + 4, y + 9, 22, GOLD[1])
    micro_text(cv, "OPEN", x + 15 - micro_width("OPEN") // 2, y + 11, "#f2ecdc")
    micro_text(cv, "LATE", x + 15 - micro_width("LATE") // 2 - 3, y + 16, "#f2ecdc")
    cv.px(x + 24, y + 16, "#8ab4e8"); cv.px(x + 26, y + 16, "#8ab4e8"); cv.hline(x + 24, y + 19, 3, "#8ab4e8"); cv.px(x + 23, y + 20, "#8ab4e8"); cv.px(x + 27, y + 20, "#8ab4e8")


def dome_camera(cv, x, y):
    cv.rect(x - 4, y, 9, 2, HEATHER[3]); cv.ellipse(x - 4, y + 1, 9, 6, OUT); cv.ellipse(x - 3, y + 1, 7, 5, "#2a2a36")
    cv.px(x - 1, y + 2, "#6a6a80"); cv.px(x + 1, y + 3, "#e84a3a")


# --- floors -----------------------------------------------------------------------------------
def store_floor(cv, x, y, w, h, seed=0, tile=40, pal=TILE_S):
    """Large warm-grey porcelain tiles laid straight, rows deepening toward the viewer, thin grout,
    a quiet tone shift per tile and a few long sheen streaks."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[1])
    yy, row = y, 0
    while yy < y + h:
        th = int(round(20 + 8 * (yy - y) / max(1, h)))
        th = min(th, y + h - yy)
        for col, xx in enumerate(range(x, x + w, tile)):
            x0, x1 = max(x, xx + 1), min(x + w, xx + tile)
            if x1 - x0 < 2:
                continue
            tone = pal[4] if (col + row) % 2 == 0 else pal[3]
            tone = shade(tone, float(rng.choice([-0.025, 0.0, 0.0, 0.02])))
            cv.rect(x0, yy + 1, x1 - x0, th - 1, tone)
            cv.hline(x0, yy + 1, x1 - x0, shade(tone, 0.08))
            for _ in range((x1 - x0) * th // 40):
                cv.px(x0 + int(rng.integers(0, x1 - x0)), yy + 1 + int(rng.integers(0, max(1, th - 1))), shade(tone, float(rng.choice([-0.05, 0.04]))))
            if rng.random() < 0.18:
                sx = x0 + int(rng.integers(2, max(3, x1 - x0 - 8)))
                cv.line(sx, yy + th - 2, sx + 5, yy + 2, shade(tone, 0.12))
        yy += th
        row += 1


def carpet_zone(cv, x, y, w, h, seed=0, pal=CARPET_S, tile=20, border=GOLD[1]):
    """Charcoal carpet tiles, quarter-turned ribs, with a thin gold edge strip where it meets tile."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[2])
    for ty in range(y, y + h, tile):
        for tx in range(x, x + w, tile):
            vert = ((tx - x) // tile + (ty - y) // tile) % 2 == 0
            tw, th = min(tile, x + w - tx), min(tile, y + h - ty)
            base = pal[2] if rng.random() < 0.8 else pal[3]
            cv.rect(tx, ty, tw, th, base)
            if vert:
                for k in range(tx + 1, tx + tw, 3):
                    cv.vline(k, ty + 1, th - 2, pal[1])
            else:
                for k in range(ty + 1, ty + th, 3):
                    cv.hline(tx + 1, k, tw - 2, pal[1])
            cv.hline(tx, ty, tw, pal[3]); cv.vline(tx, ty, th, pal[3])
    cv.rect(x, y + h, w, 2, border); cv.hline(x, y + h, w, GOLD[3])
    cv.rect(x + w, y, 2, h + 2, border); cv.vline(x + w, y, h + 2, GOLD[2])


def entry_mat(cv, cx, y, w=72, h=22, label="GO BUFFS"):
    """A black rubber walk-off mat with a gold border and gold lettering."""
    x = cx - w // 2
    cv.rect(x - 1, y - 1, w + 2, h + 2, C(SHADOW, 0.5))
    cv.rect(x, y, w, h, BLACK[2])
    for k in range(y + 2, y + h - 1, 2):
        cv.hline(x + 2, k, w - 4, BLACK[1])
    cv.rect(x + 2, y + 2, w - 4, 1, GOLD[2]); cv.rect(x + 2, y + h - 3, w - 4, 1, GOLD[2])
    cv.rect(x + 2, y + 2, 1, h - 4, GOLD[2]); cv.rect(x + w - 3, y + 2, 1, h - 4, GOLD[2])
    text(cv, label, cx - text_width(label) // 2, y + h // 2 - 5, GOLD[3])


def storefront(cv, y, W, door_x, door_w=64, posts=96, frame=CHROME):
    """The shop's glass front along the bottom edge, seen from inside at the very foot of the view:
    a dark sill, aluminium mullions, night glass with a few diagonal reflections. Leaves the door gap."""
    cv.rect(0, y, W, 2, frame[1]); cv.hline(0, y, W, frame[2])
    cv.rect(0, y + 2, W, 480, "#141826")
    for gx in range(-20, W, 37):
        cv.line(gx, y + 20, gx + 14, y + 3, C("#6a7aa8", 0.18))
    for px_ in range(posts // 2, W, posts):
        if abs(px_ - door_x) < door_w // 2 + 8:
            continue
        cv.rect(px_ - 2, y, 4, 40, OUT); cv.vline(px_ - 1, y, 40, frame[2]); cv.vline(px_, y, 40, frame[1])


def doorway_gap(cv, cx, top, H, w=64, frame=CHROME):
    """The shop's front doors, open, at the bottom edge of the room: brushed aluminium jambs and a
    threshold strip, and beyond them a glimpse of the Fountain Court's paving in cool night light."""
    x = cx - w // 2
    cv.rect(x, top, w, H - top, "#4a4658")
    for yy in range(top + 2, H, 5):                                   # court paving under the lamps
        off = 0 if ((yy - top) // 5) % 2 else 7
        cv.hline(x, yy, w, "#3a3648")
        for xx in range(x + off, x + w, 14):
            cv.vline(xx, yy - 4, 4, "#3a3648")
    cv.rect(x, top + 2, w, 6, C("#f6cf7a", 0.12))                    # the store's light spilling out
    cv.rect(x, top, w, 2, "#6a6e86"); cv.hline(x, top, w, "#8a90a8")    # aluminium threshold
    for jx in (x - 4, x + w):
        cv.rect(jx, top - 4, 4, H - top + 4, OUT); cv.rect(jx + 1, top - 4, 2, H - top + 4, frame[2]); cv.vline(jx + 1, top - 4, H - top + 4, frame[3])


# --- props ------------------------------------------------------------------------------------
def gondola(width=170, height=78, rows=3, header="AISLE 1", sub="TEXTBOOKS", used=0.25, seed=0, header_h=19):
    """A freestanding black gondola of textbooks seen from the front: end uprights, shelves of books
    with price strips, a kick plate, and a black-and-gold aisle header on two posts above."""
    W, Hc = width + 8, height + 8
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.45)
    top = base - height + header_h
    # header on posts
    hw = max(text_width(header), micro_width(sub)) + 14
    hx = ox + width // 2 - hw // 2
    for px_ in (hx + 5, hx + hw - 6):
        cv.rect(px_, top - 6, 2, 6, IRON[3])
    cv.rect(hx, base - height, hw, header_h - 5, OUT)
    cv.rect(hx + 1, base - height + 1, hw - 2, header_h - 7, BLACK[1]); cv.hline(hx + 1, base - height + 1, hw - 2, BLACK[4])
    cv.hline(hx + 2, base - height + header_h - 8, hw - 4, GOLD[2])
    text(cv, header, ox + width // 2 - text_width(header) // 2, base - height + 2, GOLD[4])
    # cabinet
    cv.rect(ox, top, width, base - top, OUT)
    cv.rect(ox + 1, top + 1, width - 2, 3, BLACK[4]); cv.hline(ox + 1, top + 1, width - 2, BLACK[5])
    inner_top, kick = top + 5, 8
    cv.rect(ox + 1, inner_top, 4, base - inner_top - 1, BLACK[3]); cv.vline(ox + 1, inner_top, base - inner_top - 1, BLACK[5])
    cv.rect(ox + width - 5, inner_top, 4, base - inner_top - 1, BLACK[2])
    bx0, bx1 = ox + 5, ox + width - 5
    usable = base - kick - inner_top
    step = usable / rows
    mid = ox + width // 2
    for k in range(rows):
        y0 = inner_top + int(round(k * step)); y1 = inner_top + int(round((k + 1) * step))
        cv.rect(bx0, y0, bx1 - bx0, y1 - y0, BLACK[1]); cv.hline(bx0, y0, bx1 - bx0, BLACK[0])
        for b, (a0, a1) in enumerate([(bx0, mid - 1), (mid + 2, bx1)]):
            textbook_row(cv, a0 + 1, y1 - 3, a1 - a0 - 2, y1 - y0 - 6, seed=seed * 41 + k * 3 + b, used=used, dim=0.03 * k)
        price_strip(cv, bx0, y1 - 3, bx1 - bx0, seed=seed + k)
    cv.rect(mid - 1, inner_top, 3, usable, BLACK[3]); cv.vline(mid - 1, inner_top, usable, BLACK[5])
    cv.rect(ox + 1, base - kick, width - 2, kick - 1, BLACK[2]); cv.hline(ox + 1, base - kick, width - 2, BLACK[4])
    micro_text(cv, sub, ox + width // 2 - micro_width(sub) // 2, base - kick + 2, GOLD[3])
    return cv, ox + width // 2, base


def tee_table(width=104, height=36, seed=0):
    """A maple display table piled with folded tees in stacks, a cap pyramid and a small NEW card."""
    W, Hc = width + 6, height + 10
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 3, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - 20
    for lx in (ox + 4, ox + width - 8):
        cv.rect(lx, top + 4, 4, base - top - 4, OUT); cv.rect(lx + 1, top + 4, 2, base - top - 5, MAPLE[2]); cv.vline(lx + 1, top + 4, base - top - 5, MAPLE[4])
    cv.rect(ox + 4, base - 7, width - 8, 3, OUT); cv.hline(ox + 5, base - 6, width - 10, MAPLE[2])      # stretcher
    cv.rect(ox, top - 4, width, 9, OUT)
    cv.rect(ox + 1, top - 3, width - 2, 4, MAPLE[4]); cv.hline(ox + 1, top - 3, width - 2, MAPLE[5])
    cv.rect(ox + 1, top + 1, width - 2, 3, MAPLE[2]); cv.hline(ox + 1, top + 3, width - 2, MAPLE[1])
    cols = [[GOLD[3], GOLD[4]], [BLACK[3], BLACK[4]], [WHITE_T[2], WHITE_T[3]], [HEATHER[3], HEATHER[4]], [GOLD[4], GOLD[3]]]
    rng = _rng(seed)
    for j, tx in enumerate(range(ox + 4, ox + width - 14, 19)):
        folded_stack(cv, tx, top - 2, 16, int(rng.integers(5, 8)), cols[j % len(cols)], seed=seed + j)
    s = "NEW"
    cv.rect(ox + width // 2 - 8, top + 4, 17, 9, OUT); cv.rect(ox + width // 2 - 7, top + 5, 15, 7, "#f6f4ee")
    micro_text(cv, s, ox + width // 2 - micro_width(s) // 2, top + 6, "#c8382c")
    return cv, ox + width // 2, base


def round_rack(width=66, height=62, seed=0):
    """A chrome round rack of hoodies: the far half of the ring above, the near half's garments
    hanging toward us, a centre pole with a size topper, a weighted base."""
    W, Hc = width + 6, height + 6
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 3, height + 3
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2, 3)
    ring_y = base - 40
    cols = [(BLACK[2], GOLD[3]), (GOLD[3], BLACK[2]), (HEATHER[3], BLACK[2]), (BLACK[3], WHITE_T[2])]
    # far garments (darker, peeking above the ring)
    for k, gx in enumerate(range(ox + 6, ox + width - 8, 8)):
        c, t = cols[(k + 1) % 4]
        cv.rect(gx - 1, ring_y - 6, 10, 9, OUT); cv.rect(gx, ring_y - 5, 8, 8, shade(c, -0.35))
        cv.hline(gx + 2, ring_y - 6, 4, CHROME[1])
    # pole and topper
    cv.rect(cx - 1, base - height + 8, 3, height - 10, OUT); cv.vline(cx, base - height + 8, height - 10, CHROME[3])
    cv.rect(cx - 9, base - height, 19, 9, OUT); cv.rect(cx - 8, base - height + 1, 17, 7, "#f6f4ee")
    micro_text(cv, "S-XL", cx - micro_width("S-XL") // 2 + 1, base - height + 2, BLACK[2])
    # ring
    cv.ellipse(ox + 2, ring_y - 4, width - 4, 9, OUT); cv.ellipse(ox + 3, ring_y - 3, width - 6, 7, CHROME[2])
    cv.ellipse(ox + 5, ring_y - 2, width - 10, 5, (0, 0, 0, 0))
    cv.ellipse(ox + 4, ring_y - 2, width - 8, 5, C(BLACK[1], 1.0))
    # near garments: hoodies hanging off the front of the ring, overlapping
    for k, gx in enumerate(range(ox + 4, ox + width - 10, 9)):
        c, t = cols[k % 4]
        gy = ring_y + 2 - (1 if k % 2 else 0)
        cv.rect(gx - 1, gy - 1, 14, 28, OUT)
        cv.rect(gx, gy, 12, 26, c); cv.vline(gx, gy, 26, shade(c, 0.18)); cv.vline(gx + 11, gy, 26, shade(c, -0.3))
        cv.rect(gx, gy + 23, 12, 3, t)
        cv.hline(gx + 2, gy + 16, 8, shade(c, -0.3))
        cv.hline(gx + 3, gy - 2, 6, CHROME[3])
        if k % 2 == 0:
            cv.rect(gx + 4, gy + 6, 4, 2, t)
    # base
    cv.rect(cx - 12, base - 4, 25, 4, OUT); cv.rect(cx - 11, base - 3, 23, 2, CHROME[1]); cv.hline(cx - 11, base - 3, 23, CHROME[3])
    for lx in (cx - 9, cx + 9):
        cv.rect(lx - 1, base - 13, 3, 10, OUT); cv.vline(lx, base - 13, 10, CHROME[2])
    return cv, cx, base


def plush_bin(width=50, height=38, seed=0):
    """A chrome wire bin heaped with plush buffaloes in gold scarves, one upside down, a RALPHIE card."""
    rng = _rng(seed)
    W, Hc = width + 6, height + 8
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 3, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - 22
    # the heap first, so the wire front overlaps it
    spots = [(ox + 8, top + 2), (ox + 18, top + 1), (ox + 29, top + 2), (ox + 40, top + 3), (ox + 13, top - 4), (ox + 25, top - 5), (ox + 36, top - 3)]
    for k, (px_, py_) in enumerate(spots):
        plush_buffalo(cv, px_, py_ + 6, upside=(k == 5), scarf=GOLD[3] if k % 3 else BLACK[3])
    # wire basket
    cv.rect(ox, top, width, base - top - 3, C(BLACK[1], 0.6))
    for gx in range(ox, ox + width, 5):
        cv.vline(gx, top, base - top - 3, CHROME[2])
    for gy in range(top, base - 3, 5):
        cv.hline(ox, gy, width, CHROME[2])
    cv.rect(ox - 1, top - 1, width + 2, 2, CHROME[3]); cv.hline(ox - 1, top - 1, width + 2, "#ffffff")
    cv.rect(ox, base - 4, width, 2, CHROME[1])
    for lx in (ox + 1, ox + width - 3):
        cv.rect(lx, base - 4, 2, 4, OUT)
    # gold card on a clip
    s = "RALPHIE"
    cw = micro_width(s) + 6
    cv.rect(ox + width // 2 - cw // 2, top - 16, cw, 9, OUT); cv.rect(ox + width // 2 - cw // 2 + 1, top - 15, cw - 2, 7, GOLD[3])
    micro_text(cv, s, ox + width // 2 - micro_width(s) // 2, top - 14, BLACK[1])
    cv.vline(ox + width // 2, top - 7, 6, CHROME[2])
    return cv, ox + width // 2, base


def checkout_counter(width=164, height=54, seed=0):
    """The checkout counter seen from the customer side: black laminate front with a gold band and
    the store's buffalo badge, a maple top, the register's customer screen, a card reader, the receipt
    printer, a rail of lanyards, a candy box, paper bags and a desk bell."""
    W, Hc = width + 8, height + 10
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 4, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    top = base - 30
    # front
    cv.rect(ox, top, width, base - top, OUT)
    cv.rect(ox + 1, top + 4, width - 2, base - top - 5, BLACK[2])
    for px_ in range(ox + 4, ox + width - 3, 4):
        cv.vline(px_, top + 10, base - top - 13, BLACK[1])                   # reeded panel
    cv.rect(ox + 1, top + 6, width - 2, 3, GOLD[3]); cv.hline(ox + 1, top + 6, width - 2, GOLD[4])
    cv.rect(ox + 1, base - 4, width - 2, 3, BLACK[0])
    bx = ox + width // 2
    cv.ellipse(bx - 9, top + 10, 19, 15, OUT); cv.ellipse(bx - 8, top + 11, 17, 13, GOLD[2]); cv.ellipse(bx - 7, top + 12, 15, 11, BLACK[1])
    text(cv, "CU", bx - 6, top + 13, GOLD[4])
    # top
    cv.rect(ox - 1, top - 2, width + 2, 7, OUT)
    cv.rect(ox, top - 1, width, 4, MAPLE[4]); cv.hline(ox, top - 1, width, MAPLE[5]); cv.hline(ox, top + 3, width, MAPLE[1])
    # register: the customer display on a pole, the POS behind it (its back), cash drawer edge
    rx = ox + 42
    cv.rect(rx - 14, top - 12, 26, 11, OUT); cv.rect(rx - 13, top - 11, 24, 9, IRON[2]); cv.hline(rx - 13, top - 11, 24, IRON[4])
    cv.rect(rx - 1, top - 20, 3, 9, OUT); cv.vline(rx, top - 20, 9, IRON[3])
    cv.rect(rx - 13, top - 33, 28, 14, OUT); cv.rect(rx - 12, top - 32, 26, 12, "#0f2a26")
    micro_text(cv, "0.00", rx - 8, top - 30, "#7ae0a0")
    micro_text(cv, "GO CU", rx - 10, top - 24, "#e6d29a")
    # card reader on its stand
    kx = ox + 70
    cv.rect(kx, top - 13, 9, 13, OUT); cv.rect(kx + 1, top - 12, 7, 11, IRON[2]); cv.rect(kx + 2, top - 11, 5, 4, "#2a4a5a"); cv.px(kx + 3, top - 10, "#8ad8e8")
    for k in range(3):
        cv.hline(kx + 2, top - 6 + k * 2, 5, IRON[4])
    # receipt printer with a curl of paper
    px_ = ox + 16
    cv.rect(px_, top - 8, 14, 8, OUT); cv.rect(px_ + 1, top - 7, 12, 6, WHITE_T[1]); cv.hline(px_ + 1, top - 7, 12, WHITE_T[3])
    cv.rect(px_ + 3, top - 13, 8, 6, "#f6f4ee"); cv.hline(px_ + 4, top - 11, 5, "#a8a49c"); cv.hline(px_ + 4, top - 9, 4, "#a8a49c")
    # lanyard rail: black and gold straps hanging over the front edge
    lx0 = ox + 92
    cv.rect(lx0, top - 16, 30, 2, CHROME[2]); cv.vline(lx0, top - 16, 16, CHROME[1]); cv.vline(lx0 + 29, top - 16, 16, CHROME[1])
    for k in range(6):
        c = [BLACK[3], GOLD[3]][k % 2]
        cv.rect(lx0 + 3 + k * 4, top - 15, 2, 20, c); cv.px(lx0 + 3 + k * 4, top + 4, CHROME[3])
    # candy box and paper bags at the far end, desk bell
    cbx = ox + width - 34
    cv.rect(cbx, top - 9, 16, 9, OUT); cv.rect(cbx + 1, top - 8, 14, 8, "#c8382c"); cv.hline(cbx + 1, top - 8, 14, "#e86a5a")
    for k in range(4):
        cv.rect(cbx + 2 + k * 3, top - 10, 2, 3, ["#f2d23a", "#3a8a5a", "#2a5aa8", "#f2ecdc"][k])
    bgx = ox + width - 15
    for k in range(3):
        cv.rect(bgx - k, top - 14 + k * 2, 12, 14 - k * 2, OUT); cv.rect(bgx - k + 1, top - 13 + k * 2, 10, 13 - k * 2, "#c8a878")
    cv.hline(bgx - 1, top - 7, 10, "#a88858"); cv.rect(bgx + 3, top - 5, 3, 2, BLACK[2])
    cv.ellipse(ox + 128, top - 5, 7, 5, OUT); cv.ellipse(ox + 129, top - 4, 5, 4, GOLD[3]); cv.px(ox + 131, top - 6, GOLD[5])
    return cv, ox + width // 2, base


def spinner_rack(width=32, height=62, seed=0):
    """A wire spinner of postcards and stickers on three tiers, with a STICKERS topper."""
    rng = _rng(seed)
    W, Hc = width + 6, height + 6
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 3, height + 3
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 - 2, 2)
    cv.rect(cx - 1, base - height + 10, 3, height - 12, OUT); cv.vline(cx, base - height + 10, height - 12, CHROME[3])
    cv.rect(cx - 9, base - 3, 19, 3, OUT); cv.hline(cx - 8, base - 2, 17, CHROME[2])
    s = "STICKERS"
    tw = micro_width(s) + 4
    cv.rect(cx - tw // 2, base - height, tw, 9, OUT); cv.rect(cx - tw // 2 + 1, base - height + 1, tw - 2, 7, GOLD[3])
    micro_text(cv, s, cx - micro_width(s) // 2, base - height + 2, BLACK[1])
    cards = ["#f2ecdc", "#8ab4e8", "#e8a03a", "#c8382c", "#3a8a5a", GOLD[3], "#e6d6b1", "#7a3a8a"]
    for t in range(3):
        ty = base - height + 12 + t * 15
        cv.hline(ox + 2, ty + 12, width - 4, CHROME[2])
        for k in range(4):
            px_ = ox + 2 + k * (width - 4) // 4
            pw = (width - 4) // 4 - 1
            c = cards[int(rng.integers(len(cards)))]
            cv.rect(px_, ty, pw, 12, OUT); cv.rect(px_ + 1, ty + 1, pw - 2, 10, c); cv.hline(px_ + 1, ty + 1, pw - 2, shade(c, 0.3))
            if rng.random() < 0.6:
                cv.rect(px_ + 2, ty + 4, pw - 4, 3, shade(c, -0.35))
            else:
                cv.poly([(px_ + 1, ty + 10), (px_ + pw // 2, ty + 4), (px_ + pw - 2, ty + 10)], shade(c, -0.35))
    return cv, cx, base


def chalk_aframe(width=50, height=48, header="SELL", lines=(("YOUR", "#f2ecdc"), ("BOOKS", GOLD[4])), arrow=True, seed=0,
                 frame=MAPLE, board="#1e2a26", head_bg=GOLD[3], head_ink=BLACK[1]):
    """A chalkboard sandwich board in a maple frame: a gold header strip, chalk lines, an arrow."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 - 4, 2)
    top = base - height
    leg = 10
    for lx in (ox + 5, ox + width - 8):
        cv.line(lx, base - leg - 2, lx - 2, base, OUT); cv.line(lx + 3, base - leg - 2, lx + 5, base, OUT)
        cv.line(lx + 1, base - leg - 2, lx - 1, base - 1, frame[2]); cv.line(lx + 2, base - leg - 2, lx + 4, base - 1, frame[3])
    bh = height - leg
    cv.rect(ox, top, width, bh, OUT)
    cv.rect(ox + 1, top + 1, width - 2, bh - 2, frame[3]); cv.hline(ox + 1, top + 1, width - 2, frame[5])
    cv.rect(ox + 3, top + 3, width - 6, bh - 6, board)
    rng = _rng(seed)
    for _ in range(width * bh // 30):                                  # chalk dust smudges
        cv.px(ox + 3 + int(rng.integers(0, width - 6)), top + 3 + int(rng.integers(0, bh - 6)), shade(board, 0.12))
    cv.rect(ox + 3, top + 3, width - 6, 10, head_bg)
    text(cv, header, ox + width // 2 - text_width(header) // 2, top + 3, head_ink)
    y = top + 15
    for (s, col) in lines:
        if micro_width(s) > width - 8 or len(s) <= 6:
            text(cv, s, ox + width // 2 - text_width(s) // 2, y - 1, col)
            y += 9
        else:
            micro_text(cv, s, ox + width // 2 - micro_width(s) // 2, y, col)
            y += 7
    if arrow and y < top + bh - 6:
        ay = top + bh - 7
        cv.hline(ox + width // 2 - 6, ay, 11, "#f2ecdc"); cv.px(ox + width // 2 + 3, ay - 1, "#f2ecdc"); cv.px(ox + width // 2 + 3, ay + 1, "#f2ecdc")
    return cv, ox + width // 2, base


def bargain_bin(width=58, height=34, seed=0):
    """A low maple bin of bargain books tumbled every which way, and a hand-lettered $1 card."""
    rng = _rng(seed)
    W, Hc = width + 6, height + 12
    cv = Canvas(W, Hc, seed=seed)
    ox, base = 3, height + 8
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - 20
    # the heap: little piles of books lying flat above the rim, a couple leaning on them
    for k, px_ in enumerate(range(ox + 3, ox + width - 12, 13)):
        yy = top + 2
        for j in range(int(rng.integers(2, 5))):
            bw = int(rng.integers(9, 13)); th = int(rng.integers(3, 5))
            bx = px_ + int(rng.integers(-1, 3))
            c = TEXTBOOK[int(rng.integers(len(TEXTBOOK)))]
            cv.rect(bx - 1, yy - th - 1, bw + 2, th + 2, OUT)
            cv.rect(bx, yy - th, bw, th, c); cv.hline(bx, yy - th, bw, shade(c, 0.3))
            cv.rect(bx + bw - 3, yy - th, 2, th, "#e6d6b1"); cv.vline(bx + bw - 2, yy - th, th, "#b8a888")
            yy -= th + 1
    for lx in (ox + 14, ox + 38):
        c = TEXTBOOK[int(rng.integers(len(TEXTBOOK)))]
        cv.poly([(lx, top + 1), (lx + 4, top + 1), (lx + 9, top - 12), (lx + 5, top - 13)], OUT)
        cv.poly([(lx + 1, top), (lx + 3, top), (lx + 8, top - 11), (lx + 6, top - 12)], c)
    # the bin: maple box with a dark rim
    cv.rect(ox, top, width, base - top - 2, OUT)
    cv.rect(ox + 1, top + 1, width - 2, base - top - 4, MAPLE[3])
    for yy in range(top + 4, base - 3, 4):
        cv.hline(ox + 1, yy, width - 2, MAPLE[2])
    cv.rect(ox, top, width, 3, MAPLE[5]); cv.hline(ox, top + 2, width, MAPLE[1])
    cv.rect(ox + 2, base - 3, 4, 3, OUT); cv.rect(ox + width - 6, base - 3, 4, 3, OUT)
    # the card
    cx = ox + width - 12
    cv.rect(cx - 8, top - 14, 18, 12, OUT); cv.rect(cx - 7, top - 13, 16, 10, "#f6f4ee")
    text(cv, "$1", cx - 5, top - 13, "#c8382c")
    cv.vline(cx, top - 3, 3, CHROME[2])
    return cv, ox + width // 2, base
