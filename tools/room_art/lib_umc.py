"""Shared pieces for the UMC interior rooms painted after the club room (U04):
U03 atrium, U05 repair landing, U07 lost property, and their battle backdrops.

Everything reuses interior.py / facade.py / props.py palettes so the building reads as one: the plum
plaster and dark wainscot of the club room, the sandstone trim of the terrace facade, brass and iron
fittings. Painters that return (Canvas, anchor_x, anchor_y) follow props.py: the anchor is the floor
point of the placement.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, LEAF, MUM, ground_shadow, shrub
from interior import PLASTER, PANEL, FLOOR, VELVET, RUG, NIGHT, curtain, poster, corkboard, wall_clock
from facade import TRIM, SANDSTONE, GLOW, FRAME, DARKGLASS, TEAL

INK = "#171a2b"
# interior sandstone: the facade's trim, warmed by lamplight
STONE_IN = ["#5a4038", "#7a5a4c", "#94725e", "#ab8a70", "#c4a284", "#dcbc98"]
SHADOW = "#0d0b16"
BRASS = ["#4a2e1a", "#7a5226", "#a87a36", "#d4a656", "#f2d27a"]
# polished atrium floor: warm sandstone squares, rose squares, dark cabochon inserts
MARBLE = ["#3a2a2e", "#4e3a3a", "#6e5650", "#86685e", "#94796a", "#a88c78", "#bca08a"]
ROSE = ["#5a3c40", "#6e4a4c", "#7e5858", "#8e6664"]
# back of house: painted concrete block, sealed concrete floor, safety paint
BLOCK = ["#2e2830", "#433a3e", "#5a4e4e", "#6c5e5a", "#7e6e66", "#928070", "#a69282"]
DADO = ["#1b2a2c", "#24383a", "#2e4648", "#3c5a58", "#527470"]
CONCRETE = ["#2c282e", "#3e383c", "#514948", "#5e5552", "#6a605b", "#776b64", "#85786e"]
SAFETY = ["#6a4a18", "#a8781e", "#d9a441", "#f0c860"]
EXIT_GREEN = ["#1c4a34", "#2e8a5a", "#3cba7a", "#9ef0c0"]
# lost property: worn vinyl tiles, pegboard, kraft paper tags
VINYL = ["#3a2c2e", "#5a4642", "#6e5a52", "#7e6a5e", "#8e7a6a", "#5e3a38", "#6e4440", "#7e5048"]
KRAFT = ["#6a4a30", "#8a6440", "#a87e52", "#c49a68", "#dcb888"]
PAPER = ["#9a8e7c", "#c8bca4", "#e6d6b1", "#f6ecd2"]
ITEM_COLOURS = ["#7e3a30", "#425da6", "#5c897c", "#c47a2c", "#e6d6b1", "#8a4a6a", "#3e4a6e", "#a8604a",
                "#d9a441", "#4a6a4a", "#9e4e52", "#6b81bf"]


# ---------------------------------------------------------------------------------------------
# small shared helpers
# ---------------------------------------------------------------------------------------------

def halo(cv, cx, cy, r, colour="#f6cf7a", strength=0.12, steps=3):
    """Stepped round glow on a wall (three concentric discs, no soft gradient)."""
    for i in range(steps):
        rr = int(r * (1 - i / steps))
        if rr < 1:
            continue
        cv.ellipse(cx - rr, cy - rr, rr * 2 + 1, rr * 2 + 1, C(colour, strength * (0.7 + 0.3 * i / steps)))


def soft_ellipse(cv, cx, cy, rx, ry, colour, alpha):
    """Flat translucent ellipse (one band) for shadows and reflections."""
    for yy in range(-ry, ry + 1):
        span = int(rx * np.sqrt(max(0.0, 1 - (yy / (ry + 0.5)) ** 2)))
        cv.rect(cx - span, cy + yy, span * 2 + 1, 1, C(colour, alpha))


def bolt(cv, x, y, c="#a3a9b8"):
    cv.px(x, y, c)
    cv.px(x + 1, y + 1, shade(c, -0.45))


def caged_bulb(cv, x, y, lit=True):
    """A bare service bulb in a wire cage hanging from a short conduit drop (x, y = cage top)."""
    cv.rect(x - 2, y - 3, 5, 3, IRON[1]); cv.hline(x - 2, y - 3, 5, IRON[3])
    cv.rect(x - 3, y, 7, 8, OUT)
    cv.rect(x - 2, y + 1, 5, 6, AMBER[3] if lit else IRON[2])
    cv.rect(x - 1, y + 2, 3, 3, AMBER[4] if lit else IRON[3])
    for yy in (y + 2, y + 5):
        cv.hline(x - 3, yy, 7, C(OUT, 0.8))
    cv.vline(x, y + 1, 6, C(OUT, 0.5))
    if lit:
        halo(cv, x, y + 4, 16, strength=0.07)


def stencil(cv, s, x, y, colour, bg=None, pad=2):
    """Painted stencil lettering, optionally on a plate."""
    if bg:
        w = text_width(s) + pad * 2
        cv.rect(x - pad, y - 1, w, 11, bg)
    text(cv, s, x, y, colour)


def enamel_sign(cv, x, y, s, bg="#1f1a2a", fg="#f6cd78", frame=BRASS[2]):
    """A small framed sign with one line of the game font; (x, y) is the top-left of the frame."""
    w = text_width(s) + 8
    cv.rect(x, y, w, 13, OUT)
    cv.rect(x + 1, y + 1, w - 2, 11, frame)
    cv.rect(x + 2, y + 2, w - 4, 9, bg)
    text(cv, s, x + 4, y + 2, fg)
    cv.px(x + 1, y + 1, shade(frame, 0.3))
    return w


def cable(cv, pts, c="#16141f", hi=None):
    """A cord lying on the floor along a polyline (flat, one pixel with a faint highlight)."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        cv.line(x0, y0, x1, y1, c)
        if hi:
            cv.line(x0, y0 - 1, x1, y1 - 1, C(hi, 0.35))


# ---------------------------------------------------------------------------------------------
# U03 atrium: wall, windows, doors, the NEXT YEAR alcove, the stair down, the polished floor
# ---------------------------------------------------------------------------------------------

def atrium_wall(cv, x, y, w, h, seed=0):
    """Plum plaster (as in the club room) above a sandstone dado with a dark rail."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, PLASTER[2])
    # plaster mottle: soft clusters, a little darker toward the floor
    for _ in range(w * h // 22):
        px, py = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        t = (py - y) / max(1, h)
        c = PLASTER[1] if rng.random() < 0.35 + t * 0.4 else PLASTER[3]
        cv.px(px, py, c)
        if rng.random() < 0.3:
            cv.px(px + 1, py, c)


def sandstone_dado(cv, x, y, w, h, seed=0):
    """Low ashlar course along the wall foot, capped by a dark wood rail."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, STONE_IN[0])
    rows = [(y + 4, (h - 6) // 2), (y + 4 + (h - 6) // 2, h - 6 - (h - 6) // 2)]
    for r, (ry, rh) in enumerate(rows):
        xx = x - (int(rng.integers(6, 18)) if r else 0)
        while xx < x + w:
            sw = int(rng.integers(22, 40))
            x0, x1 = max(x, xx), min(x + w, xx + sw - 1)
            if x1 > x0:
                tone = STONE_IN[1] if rng.random() < 0.55 else mix(STONE_IN[1], STONE_IN[2], 0.5)
                cv.rect(x0, ry, x1 - x0, rh - 1, tone)
                cv.hline(x0, ry, x1 - x0, shade(tone, 0.1))
                cv.hline(x0, ry + rh - 2, x1 - x0, shade(tone, -0.1))
                for _ in range((x1 - x0) * rh // 14):
                    cv.px(x0 + int(rng.integers(0, x1 - x0)), ry + int(rng.integers(0, max(1, rh - 1))), shade(tone, float(rng.choice([-0.08, 0.06]))))
            xx += sw
    # rail on top
    cv.rect(x, y, w, 4, PANEL[3]); cv.hline(x, y, w, PANEL[5]); cv.hline(x, y + 3, w, PANEL[1])
    # skirting shadow
    cv.rect(x, y + h - 2, w, 2, PANEL[1])
    cv.hline(x, y + h - 1, w, PANEL[0])


def frieze(cv, x, y, w, inscription=None):
    """Carved sandstone band under the ceiling beam, with an inscription."""
    cv.rect(x, y, w, 14, STONE_IN[1])
    cv.hline(x, y, w, STONE_IN[3]); cv.hline(x, y + 1, w, STONE_IN[2])
    cv.hline(x, y + 12, w, STONE_IN[0]); cv.hline(x, y + 13, w, C(SHADOW, 0.5))
    for dx in range(x + 2, x + w - 2, 8):
        cv.rect(dx, y + 10, 4, 2, STONE_IN[2]); cv.px(dx + 3, y + 11, STONE_IN[0])
    if inscription:
        tw = text_width(inscription)
        tx = x + w // 2 - tw // 2
        cv.rect(tx - 6, y + 2, tw + 12, 9, STONE_IN[0])
        cv.rect(tx - 5, y + 2, tw + 10, 8, mix(STONE_IN[1], STONE_IN[0], 0.4))
        text(cv, inscription, tx, y + 1, STONE_IN[3])


def ceiling_beam(cv, x, y, w):
    cv.rect(x, y, w, 6, PANEL[1]); cv.hline(x, y + 4, w, PANEL[3]); cv.hline(x, y + 5, w, PANEL[0])
    for bx in range(x + 30, x + w, 96):
        cv.rect(bx - 3, y, 7, 6, PANEL[2]); cv.vline(bx - 3, y, 6, PANEL[3])


def pilaster_in(cv, x, y, w, h):
    """Sandstone pilaster with a simple capital and plinth (interior, slightly darker than outside)."""
    cv.rect(x, y, w, h, STONE_IN[1])
    cv.vline(x, y, h, STONE_IN[3]); cv.vline(x + 1, y, h, STONE_IN[2]); cv.vline(x + w - 1, y, h, STONE_IN[0])
    cv.vline(x + w - 2, y, h, mix(STONE_IN[0], STONE_IN[1], 0.5))
    for yy in range(y + 10, y + h - 6, 12):
        cv.hline(x + 1, yy, w - 2, STONE_IN[0]); cv.hline(x + 1, yy + 1, w - 2, mix(STONE_IN[1], STONE_IN[2], 0.5))
    # capital
    cv.rect(x - 2, y, w + 4, 4, STONE_IN[2]); cv.hline(x - 2, y, w + 4, STONE_IN[4]); cv.hline(x - 2, y + 3, w + 4, STONE_IN[0])
    cv.rect(x - 1, y + 4, w + 2, 2, STONE_IN[1]); cv.hline(x - 1, y + 5, w + 2, STONE_IN[0])
    # plinth
    cv.rect(x - 2, y + h - 6, w + 4, 6, STONE_IN[2]); cv.hline(x - 2, y + h - 6, w + 4, STONE_IN[3]); cv.hline(x - 2, y + h - 1, w + 4, STONE_IN[0])


def night_view(cv, x, y, w, h, seed=0, moon=None, ridge=True):
    """What the tall windows look at: deep night over campus, the Flatirons as dark slabs, lit windows."""
    rng = np.random.default_rng(seed)
    cv.dither_v(x, y, w, h, NIGHT[0], "#33295a", steps=5)
    for _ in range(max(3, w * h // 90)):
        sx, sy = x + int(rng.integers(0, w)), y + int(rng.integers(0, max(1, h // 2)))
        cv.px(sx, sy, "#c8d0f0" if rng.random() < 0.35 else "#7a86c0")
    if moon:
        mx, my = moon
        halo(cv, mx, my, 9, colour="#c8d0f0", strength=0.12)
        cv.ellipse(mx - 4, my - 4, 9, 9, "#efe2b8"); cv.ellipse(mx - 2, my - 5, 8, 8, NIGHT[1])
    hz = y + h
    if ridge:
        # Flatiron slabs leaning against the sky, lit faintly on their left faces
        px = x + int(rng.integers(-10, max(-9, w - 30)))
        for k in range(2):
            ph = int(rng.integers(h // 4, h // 3 + 2))
            pw = int(ph * 1.2)
            cv.poly([(px, hz - 8), (px + pw * 0.45, hz - 8 - ph), (px + pw, hz - 8)], "#2c2246")
            cv.poly([(px, hz - 8), (px + pw * 0.45, hz - 8 - ph), (px + pw * 0.3, hz - 8)], "#3a2e58")
            px += pw - 4
    # campus treeline and roofs with lit windows
    xx = x - 2
    while xx < x + w:
        bw = int(rng.integers(6, 12)); bh = int(rng.integers(5, 12))
        if rng.random() < 0.5:
            cv.ellipse(xx - 1, hz - bh - 2, bw + 3, bh * 2 + 2, "#141a26")
            cv.px(xx + bw // 2, hz - bh - 1, "#1e2634")
        else:
            cv.rect(xx, hz - bh, bw, bh, "#151626")
            cv.poly([(xx - 1, hz - bh), (xx + bw // 2, hz - bh - 3), (xx + bw, hz - bh)], "#151626")
            for wy in range(hz - bh + 3, hz - 2, 3):
                for wx in range(xx + 1, xx + bw - 1, 3):
                    if rng.random() < 0.35:
                        cv.px(wx, wy, "#e9a84a" if rng.random() < 0.7 else "#f6cd78")
        xx += bw
    cv.rect(x, hz - 2, w, 2, "#101322")


def atrium_window(cv, x, y, w, h, seed=0, moon=None, drapes=True):
    """Tall arched window seen from inside: sandstone surround, dark mullions, night beyond.
    (x, y) is the top-left of the rectangular part of the glass; the arch rises w/2 above it."""
    r = w // 2
    top = y - r
    # surround and keystone
    cv.ellipse(x - 5, top - 5, w + 10, w + 10, STONE_IN[0])
    cv.rect(x - 5, y, w + 10, h + 4, STONE_IN[0])
    cv.ellipse(x - 4, top - 4, w + 8, w + 8, STONE_IN[2])
    cv.rect(x - 4, y, w + 8, h + 3, STONE_IN[1])
    cv.vline(x - 4, y, h + 3, STONE_IN[3]); cv.vline(x + w + 3, y, h + 3, STONE_IN[0])
    for i, a in enumerate(np.linspace(np.pi, 2 * np.pi, 9)):
        if i % 2:
            for rr in range(r + 1, r + 4):
                cv.px(int(round(x + r - 0.5 + np.cos(a) * rr)), int(round(y + np.sin(a) * rr)), STONE_IN[1])
    cv.rect(x + r - 3, top - 6, 6, 6, STONE_IN[3]); cv.hline(x + r - 3, top - 6, 6, STONE_IN[4]); cv.hline(x + r - 3, top - 1, 6, STONE_IN[1])
    # glass: render the view into a scratch canvas and mask it to the arch
    view = Canvas(w, h + r)
    night_view(view, 0, 0, w, h + r, seed=seed, moon=(moon[0] - x, moon[1] - top) if moon else None)
    for yy in range(h + r):
        for xx in range(w):
            if yy < r:
                dx, dy = xx - (r - 0.5), yy - r
                if dx * dx + dy * dy > r * r:
                    continue
            cv.a[top + yy, x + xx] = view.a[yy, xx]
    # mullions: centre bar, transoms, radial bars in the fanlight
    cv.vline(x + r - 1, top, h + r, FRAME); cv.vline(x + r, top, h + r, mix(FRAME, PANEL[2], 0.5))
    for my in range(y, y + h, max(10, h // 4)):
        cv.hline(x, my, w, FRAME)
    for a in (np.pi * 1.25, np.pi * 1.75):
        cv.line(x + r, y, int(x + r + np.cos(a) * r), int(y + np.sin(a) * r), FRAME)
    # reflections on the glass
    for k in range(2):
        gx = x + 3 + k * (r + 1)
        cv.line(gx, y + h - 6, gx + r // 2, y + h - 6 - r // 2 - 4, C("#9aa8e0", 0.25))
    # sill
    cv.rect(x - 6, y + h + 2, w + 12, 3, STONE_IN[3]); cv.hline(x - 6, y + h + 2, w + 12, STONE_IN[4])
    cv.hline(x - 6, y + h + 5, w + 12, C(SHADOW, 0.5))
    if drapes:
        for side in (0, 1):
            dx = x - 7 if side == 0 else x + w + 1
            cv.rect(dx, top - 6, 6, h + r + 8, VELVET[2])
            for k in range(0, h + r + 8, 1):
                if k % 5 == 0:
                    cv.px(dx + (1 if side == 0 else 4), top - 6 + k, VELVET[4])
            cv.vline(dx + (5 if side == 0 else 0), top - 6, h + r + 8, VELVET[1])
            cv.vline(dx + 2, top - 6, h + r + 8, VELVET[3])
            ty = y + h * 2 // 3
            cv.rect(dx - 1, ty, 8, 3, BRASS[3]); cv.hline(dx - 1, ty, 8, BRASS[4]); cv.hline(dx - 1, ty + 2, 8, BRASS[1])
        cv.rect(x - 9, top - 9, w + 18, 3, BRASS[1]); cv.hline(x - 9, top - 9, w + 18, BRASS[3])
        cv.rect(x - 11, top - 10, 3, 5, BRASS[3]); cv.rect(x + w + 8, top - 10, 3, 5, BRASS[3])


def sconce(cv, x, y, glow=True):
    """Brass wall sconce with a lit tulip shade; (x, y) = shade centre."""
    if glow:
        halo(cv, x, y, 22, strength=0.06)
        halo(cv, x, y + 2, 11, strength=0.1)
    cv.rect(x - 1, y + 3, 3, 6, BRASS[1]); cv.rect(x - 3, y + 8, 7, 3, BRASS[2]); cv.hline(x - 3, y + 8, 7, BRASS[4])
    cv.poly([(x - 4, y - 4), (x + 4, y - 4), (x + 2, y + 3), (x - 2, y + 3)], OUT)
    cv.poly([(x - 3, y - 3), (x + 3, y - 3), (x + 1, y + 2), (x - 1, y + 2)], GLOW[3])
    cv.rect(x - 1, y - 3, 2, 3, GLOW[4])
    cv.hline(x - 4, y - 5, 9, BRASS[3])


def club_doors(cv, cx, bottom, w=46, h=70, plaque="CLUB ROOM"):
    """Double doors into the club room: sandstone architrave, fanlight, warm light behind glass."""
    x0, top = cx - w // 2, bottom - h
    # architrave
    cv.rect(x0 - 7, top - 16, w + 14, h + 16, STONE_IN[0])
    cv.rect(x0 - 6, top - 15, w + 12, h + 15, STONE_IN[2])
    cv.vline(x0 - 6, top - 15, h + 15, STONE_IN[3]); cv.vline(x0 + w + 5, top - 15, h + 15, STONE_IN[0])
    cv.rect(x0 - 9, top - 19, w + 18, 4, STONE_IN[3]); cv.hline(x0 - 9, top - 19, w + 18, STONE_IN[4]); cv.hline(x0 - 9, top - 16, w + 18, STONE_IN[0])
    # fanlight (warm)
    cv.rect(x0 - 1, top - 13, w + 2, 12, FRAME)
    cv.rect(x0, top - 12, w, 10, GLOW[2]); cv.rect(x0, top - 12, w, 3, GLOW[3])
    for k in range(1, 6):
        cv.vline(x0 + k * w // 6, top - 12, 10, FRAME)
    # leaves
    cv.rect(x0 - 1, top - 1, w + 2, h + 1, FRAME)
    for side in (0, 1):
        lx = x0 + side * (w // 2)
        lw = w // 2
        cv.rect(lx, top, lw, h, PANEL[3])
        cv.vline(lx, top, h, PANEL[4]); cv.vline(lx + lw - 1, top, h, PANEL[1])
        # tall glass pane: the club's light, a sliver of red curtain
        gx, gy, gw, gh = lx + 4, top + 5, lw - 8, h - 26
        cv.rect(gx - 1, gy - 1, gw + 2, gh + 2, PANEL[1])
        for yy in range(gh):
            t = yy / gh
            cv.hline(gx, gy + yy, gw, GLOW[3] if t < 0.3 else GLOW[2] if t < 0.75 else GLOW[1])
        cv.rect(gx + (gw - 3 if side == 0 else 0), gy, 3, gh, VELVET[3])
        cv.vline(gx + (gw - 3 if side == 0 else 0) + 1, gy, gh, VELVET[4])
        cv.line(gx + 1, gy + gh - 4, gx + gw - 2, gy + 6, C("#fff0c4", 0.35))
        # lower panel and push bar
        cv.rect(lx + 4, top + h - 17, lw - 8, 11, PANEL[2]); cv.rect(lx + 5, top + h - 16, lw - 10, 9, PANEL[4])
        cv.hline(lx + 5, top + h - 16, lw - 10, PANEL[5])
        px = lx + (lw - 3 if side == 0 else 1)
        cv.rect(px, top + h // 2 - 4, 2, 10, BRASS[3]); cv.vline(px, top + h // 2 - 4, 10, BRASS[4])
        cv.rect(lx + 2, top + h - 4, lw - 4, 3, BRASS[2]); cv.hline(lx + 2, top + h - 4, lw - 4, BRASS[4])
    cv.vline(cx - 1, top, h, FRAME)
    # brass plaque on the architrave
    if plaque:
        pw = text_width(plaque) + 6
        cv.rect(cx - pw // 2, top - 31, pw, 12, OUT)
        cv.rect(cx - pw // 2 + 1, top - 30, pw - 2, 10, BRASS[2]); cv.hline(cx - pw // 2 + 1, top - 30, pw - 2, BRASS[4])
        text(cv, plaque, cx - text_width(plaque) // 2, top - 31, BRASS[0])
    # stone sill
    cv.rect(x0 - 8, bottom - 1, w + 16, 3, STONE_IN[3]); cv.hline(x0 - 8, bottom - 1, w + 16, STONE_IN[4])


def next_year_alcove(cv, cx, top, base, w=140, seed=0, spot=True):
    """Curtained niche behind the voice booth with a bulb marquee; returns the marquee bulb points."""
    x0, x1 = cx - w // 2, cx + w // 2
    r = w // 2
    arch_y = top + r // 2
    # niche: darker plaster, an elliptical arch head, a backdrop cloth in deep teal
    cv.rect(x0 - 6, arch_y, w + 12, base - arch_y, STONE_IN[0])
    cv.ellipse(x0 - 6, top - 6, w + 12, r + 12, STONE_IN[0])
    cv.ellipse(x0 - 5, top - 5, w + 10, r + 10, STONE_IN[2])
    cv.rect(x0 - 5, arch_y, w + 10, base - arch_y, STONE_IN[1])
    cv.vline(x0 - 5, arch_y, base - arch_y, STONE_IN[3]); cv.vline(x1 + 4, arch_y, base - arch_y, STONE_IN[0])
    cv.ellipse(x0, top, w, r, "#18222c")
    cv.rect(x0, arch_y, w, base - arch_y, "#18222c")
    # backdrop: dark teal cloth with soft vertical folds
    for xx in range(x0 + 2, x1 - 2):
        fold = (xx * 5) % 11
        c = TEAL[1] if fold < 5 else TEAL[0] if fold < 8 else mix(TEAL[1], TEAL[2], 0.5)
        y0 = top + 2
        dx = xx - cx
        if abs(dx) < r:
            y0 = int(arch_y - np.sqrt(max(0, 1 - (dx / r) ** 2)) * (r // 2)) + 2
        cv.vline(xx, max(y0, top + 2), base - max(y0, top + 2), c)
    # spot on the cloth where the booth stands
    if spot:
        for rr, a in [(34, 0.08), (24, 0.1), (14, 0.12)]:
            cv.ellipse(cx - rr, base - 40 - rr // 2, rr * 2, rr, C("#f6cf7a", a))
    # curtains gathered at both sides
    curtain(cv, x0, arch_y - 6, 22, base - arch_y + 4, flip=False, seed=seed + 1)
    curtain(cv, x1 - 22, arch_y - 6, 22, base - arch_y + 4, flip=True, seed=seed + 2)
    for xx in range(x0, x1):
        dx = xx - cx
        yv = int(arch_y - np.sqrt(max(0, 1 - (dx / r) ** 2)) * (r // 2)) - 1
        cv.rect(xx, yv, 1, 5, VELVET[3])
        if xx % 6 == 0:
            cv.px(xx, yv + 5, "#c0884a")
    cv.hline(x0, base - 1, w, C(SHADOW, 0.5))
    # marquee: NEXT YEAR in amber on a dark board ringed with bulbs
    label = "NEXT YEAR"
    mw = text_width(label) + 22
    mx, my = cx - mw // 2, top + 10
    cv.rect(mx - 1, my - 1, mw + 2, 21, OUT)
    cv.rect(mx, my, mw, 19, "#3a1420"); cv.rect(mx + 2, my + 2, mw - 4, 15, "#24101a")
    text(cv, label, cx - text_width(label) // 2, my + 5, "#f6cd78")
    bulbs = []
    for bx in range(mx + 2, mx + mw - 1, 4):
        bulbs += [(bx, my + 1), (bx, my + 17)]
    for by in range(my + 5, my + 15, 4):
        bulbs += [(mx + 1, by), (mx + mw - 2, by)]
    for (bx, by) in bulbs:
        cv.px(bx, by, "#c47a2c")
    # chains to the ceiling
    for hx in (mx + 6, mx + mw - 7):
        for yy in range(top - 6, my, 2):
            cv.px(hx, yy, BRASS[2])
    return bulbs


def stair_down_arch(cv, x0, x1, base, floor_y, sign="REPAIR"):
    """A service stair dropping away under an arch in the back wall. The first treads start on the
    atrium floor at floor_y and recede, darker and narrower, into the opening."""
    w = x1 - x0
    cx = (x0 + x1) // 2
    r = w // 2
    top = base - 76
    # arch surround in the wall
    cv.ellipse(x0 - 7, top - 7, w + 14, w + 14, STONE_IN[0])
    cv.rect(x0 - 7, top + r, w + 14, base - top - r, STONE_IN[0])
    cv.ellipse(x0 - 6, top - 6, w + 12, w + 12, STONE_IN[2])
    cv.rect(x0 - 6, top + r, w + 12, base - top - r, STONE_IN[1])
    cv.vline(x0 - 6, top + r, base - top - r, STONE_IN[3]); cv.vline(x1 + 5, top + r, base - top - r, STONE_IN[0])
    for i, a in enumerate(np.linspace(np.pi, 2 * np.pi, 11)):
        if i % 2:
            for rr in range(r + 1, r + 6):
                cv.px(int(round(cx - 0.5 + np.cos(a) * rr)), int(round(top + r + np.sin(a) * rr)), STONE_IN[1])
    # opening: darkness
    cv.ellipse(x0, top, w, w, "#0c0a12")
    cv.rect(x0, top + r, w, base - top - r, "#0c0a12")
    # the far landing below: a caged bulb and a dim green exit sign deep inside
    cv.rect(cx - 16, top + r + 6, 32, 18, "#141019")
    cv.rect(cx - 7, top + r + 8, 14, 5, EXIT_GREEN[0]); cv.rect(cx - 6, top + r + 9, 12, 3, EXIT_GREEN[1])
    caged_bulb(cv, cx + 14, top + r - 4)
    # treads from the floor edge up into the arch: shallower and darker as they go down and away
    n = 9
    y = floor_y
    rows = []
    for i in range(n):
        th = max(3, 7 - i // 2)
        t = i / (n - 1)
        inset = int(round(2 + t * w * 0.18))
        rows.append((y - th, th, inset, t))
        y -= th
    for (ty, th, inset, t) in rows:
        tone = mix(STONE_IN[2], "#140f18", min(1.0, t * 1.15))
        cv.rect(x0 + inset, ty, w - inset * 2, th, tone)
        cv.hline(x0 + inset, ty, w - inset * 2, shade(tone, 0.18 * (1 - t)))
        cv.hline(x0 + inset, ty + th - 1, w - inset * 2, shade(tone, -0.3))
        if t < 0.5:
            cv.rect(x0 + inset + 2, ty, w - inset * 2 - 4, 1, mix(BRASS[3], tone, t * 1.6))
    # side walls of the cut, converging
    for (ty, th, inset, t) in rows:
        cv.rect(x0, ty, inset, th, mix(STONE_IN[0], "#0c0a12", t))
        cv.rect(x1 - inset, ty, inset, th, mix(STONE_IN[0], "#0c0a12", t * 0.8 + 0.2))
    # brass handrails following the descent
    (ly, _, lin, _), (fy, _, fin, _) = rows[0], rows[-1]
    for side in (0, 1):
        ax = x0 + 1 if side == 0 else x1 - 2
        bx = x0 + fin - 1 if side == 0 else x1 - fin
        cv.line(ax, floor_y - 13, bx, fy - 4, BRASS[3])
        cv.line(ax, floor_y - 12, bx, fy - 3, BRASS[1])
        cv.vline(ax, floor_y - 12, 12, BRASS[2])
    # cheek walls on the atrium floor: low sandstone kerbs with a brass cap
    for kx in (x0 - 6, x1):
        cv.rect(kx, base, 6, floor_y - base, STONE_IN[1])
        cv.vline(kx, base, floor_y - base, STONE_IN[3]); cv.vline(kx + 5, base, floor_y - base, STONE_IN[0])
        cv.hline(kx, floor_y - 1, 6, C(SHADOW, 0.6))
        cv.rect(kx + 1, base, 4, 2, BRASS[3])
    # nosing on the first step
    cv.rect(x0, floor_y - 2, w, 2, BRASS[3]); cv.hline(x0, floor_y - 2, w, BRASS[4])
    # enamel sign over the arch
    if sign:
        sw = text_width(sign) + 8
        enamel_sign(cv, cx - sw // 2, top - 22, sign, bg="#1f2a2a", fg="#f6cd78")
        cv.line(cx - 3, top - 7, cx, top - 4, BRASS[3]); cv.line(cx + 3, top - 7, cx, top - 4, BRASS[3])


def atrium_floor(cv, x, y, w, h, seed=0, tile=30, border=8):
    """Polished sandstone squares with dark cabochon inserts at the corners, rows a little deeper
    toward the viewer, a rose border band running round the hall."""
    rng = np.random.default_rng(seed)
    grout = MARBLE[2]
    cv.rect(x, y, w, h, grout)
    yy, row = y, 0
    rows = []
    while yy < y + h:
        th = int(round(13 + 7 * (yy - y) / max(1, h)))
        th = min(th, y + h - yy)
        rows.append((yy, th))
        for col, xx in enumerate(range(x - tile // 2, x + w, tile)):
            x0, x1 = max(x, xx + 1), min(x + w, xx + tile)
            if x1 <= x0:
                continue
            base = MARBLE[4] if (col * 7 + row * 3) % 5 else MARBLE[3]
            tone = shade(base, float(rng.choice([-0.05, -0.02, 0.0, 0.03])))
            cv.rect(x0, yy + 1, x1 - x0, th - 1, tone)
            cv.hline(x0, yy + 1, x1 - x0, shade(tone, 0.07))
            cv.hline(x0, yy + th - 1, x1 - x0, shade(tone, -0.05))
            # veins
            if rng.random() < 0.35:
                vx = x0 + int(rng.integers(2, max(3, x1 - x0 - 8)))
                vy = yy + 2 + int(rng.integers(0, max(1, th - 4)))
                for k in range(int(rng.integers(4, 9))):
                    cv.px(vx + k, vy - k // 3, shade(tone, -0.09))
            for _ in range((x1 - x0) * th // 20):
                cv.px(x0 + int(rng.integers(0, x1 - x0)), yy + 1 + int(rng.integers(0, max(1, th - 1))), shade(tone, float(rng.choice([-0.04, 0.035]))))
            # polish: a short lit streak on some tiles
            if rng.random() < 0.12 and th > 6:
                sx = x0 + int(rng.integers(2, max(3, x1 - x0 - 8)))
                cv.line(sx, yy + th - 3, sx + 4, yy + 2, shade(tone, 0.12))
        yy += th
        row += 1
    # cabochons on the grout crossings: small dark rose squares with a lit corner
    for (ry, th) in rows[1:]:
        for xx in range(x - tile // 2, x + w + tile, tile):
            cv.rect(xx - 1, ry - 1, 3, 3, ROSE[0]); cv.px(xx - 1, ry - 1, ROSE[2])
    # border band round the walkable hall
    bx0, bx1 = x + 20 + border, x + w - 20 - border
    by0, by1 = y + border, y + h - 24 - border
    for (ax, ay, aw, ah) in [(bx0, by0, bx1 - bx0, 4), (bx0, by1 - 4, bx1 - bx0, 4), (bx0, by0, 4, by1 - by0), (bx1 - 4, by0, 4, by1 - by0)]:
        cv.rect(ax, ay, aw, ah, ROSE[2])
    for (ax, ay, aw, ah) in [(bx0 + 1, by0 + 1, bx1 - bx0 - 2, 1), (bx0 + 1, by1 - 3, bx1 - bx0 - 2, 1), (bx0 + 1, by0 + 1, 1, by1 - by0 - 2), (bx1 - 3, by0 + 1, 1, by1 - by0 - 2)]:
        cv.rect(ax, ay, aw, ah, ROSE[3])
    cv.rect(bx0 + 6, by0 + 6, bx1 - bx0 - 12, 1, C(BRASS[2], 0.8)); cv.rect(bx0 + 6, by1 - 7, bx1 - bx0 - 12, 1, C(BRASS[2], 0.8))
    cv.rect(bx0 + 6, by0 + 6, 1, by1 - by0 - 12, C(BRASS[2], 0.8)); cv.rect(bx1 - 7, by0 + 6, 1, by1 - by0 - 12, C(BRASS[2], 0.8))


def medallion(cv, cx, cy, rx, ry):
    """A big inlaid compass rose in rose and sandstone, flat on the floor."""
    soft_ellipse(cv, cx, cy, rx, ry, ROSE[1], 1.0)
    soft_ellipse(cv, cx, cy, rx - 2, ry - 1, BRASS[2], 1.0)
    soft_ellipse(cv, cx, cy, rx - 3, ry - 1, ROSE[2], 1.0)
    soft_ellipse(cv, cx, cy, rx - 12, ry - 4, MARBLE[4], 1.0)
    soft_ellipse(cv, cx, cy, rx - 14, ry - 5, ROSE[3], 1.0)
    for k in range(8):
        a = k * np.pi / 4
        L = (rx - 8) if k % 2 == 0 else (rx - 20)
        Ly = (ry - 3) if k % 2 == 0 else (ry - 7)
        tip = (cx + np.cos(a) * L, cy + np.sin(a) * Ly)
        side = (np.cos(a + np.pi / 2) * 4, np.sin(a + np.pi / 2) * 2)
        cv.poly([(cx + side[0], cy + side[1]), tip, (cx - side[0], cy - side[1])], MARBLE[5] if k % 2 == 0 else MARBLE[3])
        cv.poly([(cx, cy), tip, (cx + side[0], cy + side[1])], shade(MARBLE[5] if k % 2 == 0 else MARBLE[3], -0.12))
    cv.ellipse(cx - 3, cy - 2, 7, 4, BRASS[3])


def runner_rug(cv, x, y, w, h, base=None, border=None):
    """A long carpet runner: deep red field, gold border, a small repeating lozenge."""
    base = base or RUG[2]
    border = border or RUG[4]
    cv.rect(x - 1, y, w + 2, h, C(SHADOW, 0.45))
    cv.rect(x, y, w, h, base)
    cv.rect(x + 2, y, 2, h, border); cv.rect(x + w - 4, y, 2, h, border)
    cv.vline(x + 1, y, h, RUG[1]); cv.vline(x + w - 2, y, h, RUG[1])
    for yy in range(y + 6, y + h - 4, 12):
        mx = x + w // 2
        cv.poly([(mx, yy - 4), (mx + 6, yy), (mx, yy + 4), (mx - 6, yy)], RUG[3])
        cv.px(mx, yy, RUG[5])
        cv.px(x + 7, yy, RUG[3]); cv.px(x + w - 8, yy, RUG[3])
    for yy in range(y, y + h):
        if yy % 3 == 0:
            cv.px(x + 5, yy, C(RUG[3], 0.6)); cv.px(x + w - 6, yy, C(RUG[3], 0.6))


def brass_ring(cv, cx, cy, rx, ry):
    """Inlaid dais under the voice booth: a brass ring, dark stone disc and a compass star."""
    soft_ellipse(cv, cx, cy, rx + 2, ry + 1, SHADOW, 0.35)
    soft_ellipse(cv, cx, cy, rx, ry, BRASS[2], 1.0)
    soft_ellipse(cv, cx, cy, rx - 2, ry - 1, BRASS[1], 1.0)
    soft_ellipse(cv, cx, cy, rx - 3, ry - 1, MARBLE[1], 1.0)
    soft_ellipse(cv, cx, cy, rx - 10, ry - 4, MARBLE[2], 1.0)
    for (dx, dy) in [(rx - 6, 0), (-(rx - 6), 0), (0, ry - 3), (0, -(ry - 3))]:
        cv.poly([(cx, cy - 1), (cx + dx, cy + dy), (cx, cy + 1)], BRASS[3])
        cv.poly([(cx - 1, cy), (cx + dx, cy + dy), (cx + 1, cy)], BRASS[3])
    cv.ellipse(cx - 3, cy - 2, 7, 4, BRASS[4])
    # highlight arc on the ring's far edge
    for xx in range(cx - rx + 6, cx + rx - 6):
        t = (xx - cx) / rx
        cv.px(xx, int(round(cy - ry * np.sqrt(max(0, 1 - t * t)))), BRASS[4] if abs(t) < 0.5 else BRASS[3])


def floor_reflection(cv, cx, y0, w, length, colour, alpha=0.1):
    """Faint stepped reflection of a bright shape on polished floor, fading downward."""
    for i, (a, f) in enumerate([(alpha, 1.0), (alpha * 0.7, 0.75), (alpha * 0.45, 0.5)]):
        ww = max(2, int(w * f))
        cv.rect(cx - ww // 2, y0 + i * length // 3, ww, length // 3, C(colour, a))


# ---------------------------------------------------------------------------------------------
# U03 props
# ---------------------------------------------------------------------------------------------

def work_lamp(height=66, cage=True, seed=0):
    """A caged work light on a tripod stand (the save lamp). The bulb sits ~5 px below the top so
    the game's point light lands on it. The cord drops down the pole."""
    w = 26
    cv = Canvas(w, height + 4, seed=seed)
    cx, base = w // 2, height + 1
    ground_shadow(cv, cx, base, 10, 2)
    # tripod legs
    for (fx, c) in [(cx - 9, IRON[2]), (cx + 9, IRON[1]), (cx + 2, IRON[3])]:
        cv.line(cx, base - 16, fx, base, OUT)
        cv.line(cx + (1 if fx > cx else 0), base - 16, fx + (1 if fx > cx else 0), base, c)
    cv.rect(cx - 2, base - 18, 5, 4, OUT); cv.rect(cx - 1, base - 17, 3, 2, IRON[3])
    # telescoping pole
    cv.rect(cx - 1, 14, 3, base - 31, OUT); cv.vline(cx, 14, base - 31, IRON[4]); cv.vline(cx - 1, 14, base - 31, IRON[2])
    cv.rect(cx - 2, (14 + base) // 2, 5, 3, IRON[2]); cv.hline(cx - 2, (14 + base) // 2, 5, IRON[4])
    cv.px(cx + 2, (14 + base) // 2 + 1, "#c84a3c")
    # cord: hangs in a loop down the pole
    for yy in range(16, base - 4):
        sag = int(round(2.5 * np.sin((yy - 16) / (base - 20) * np.pi)))
        cv.px(cx + 2 + sag, yy, "#24222f")
    # yoke and head: a round reflector facing the room, bright bulb behind a wire guard
    cv.rect(cx - 8, 6, 2, 10, IRON[1]); cv.rect(cx + 7, 6, 2, 10, IRON[1]); cv.rect(cx - 8, 14, 17, 2, IRON[2])
    cv.hline(cx - 8, 14, 17, IRON[4])
    cv.ellipse(cx - 7, -1, 15, 14, OUT)
    cv.ellipse(cx - 6, 0, 13, 12, IRON[3])
    cv.ellipse(cx - 5, 1, 11, 10, AMBER[2])
    cv.ellipse(cx - 4, 2, 9, 8, AMBER[3])
    cv.ellipse(cx - 2, 3, 5, 5, AMBER[4]); cv.px(cx, 4, "#ffffff")
    if cage:
        cv.hline(cx - 5, 6, 11, C(OUT, 0.7)); cv.vline(cx, 1, 10, C(OUT, 0.7))
        cv.px(cx - 3, 3, C(OUT, 0.5)); cv.px(cx + 3, 3, C(OUT, 0.5)); cv.px(cx - 3, 9, C(OUT, 0.5)); cv.px(cx + 3, 9, C(OUT, 0.5))
    cv.px(cx - 6, 2, IRON[4]); cv.px(cx - 5, 1, IRON[4])
    return cv, cx, base


def lobby_bench(width=94, height=37, upholstery=None, seed=0):
    """Atrium bench: dark wood frame, buttoned leather seat and back, brass feet caps."""
    up = upholstery or ["#1e2a30", "#2c4048", "#3e5a5e", "#5c7e7a"]
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2 - 2, 3)
    # back cushion
    cv.rect(ox + 3, base - height, width - 6, 18, OUT)
    cv.rect(ox + 4, base - height + 1, width - 8, 16, up[1])
    cv.hline(ox + 4, base - height + 1, width - 8, up[3]); cv.hline(ox + 4, base - height + 2, width - 8, up[2])
    for bx in range(ox + 10, ox + width - 8, 10):
        for by in (base - height + 6, base - height + 12):
            cv.px(bx + (5 if by % 2 else 0), by, up[0])
            cv.px(bx + (5 if by % 2 else 0) + 1, by - 1, up[2])
    # frame posts
    for px in (ox + 1, ox + width - 6):
        cv.rect(px, base - height - 1, 5, height - 6, OUT)
        cv.rect(px + 1, base - height, 3, height - 8, PANEL[3]); cv.vline(px + 1, base - height, height - 8, PANEL[5])
        cv.rect(px, base - height - 2, 5, 2, BRASS[3])
    # seat
    sy = base - 17
    cv.rect(ox, sy, width, 9, OUT)
    cv.rect(ox + 1, sy + 1, width - 2, 4, up[2]); cv.hline(ox + 1, sy + 1, width - 2, up[3])
    cv.rect(ox + 1, sy + 5, width - 2, 3, PANEL[3]); cv.hline(ox + 1, sy + 5, width - 2, PANEL[4]); cv.hline(ox + 1, sy + 7, width - 2, PANEL[1])
    for sx in range(ox + 16, ox + width - 8, 22):
        cv.vline(sx, sy + 1, 4, up[1])
    # legs
    for lx in (ox + 3, ox + width // 2 - 2, ox + width - 8):
        cv.rect(lx, sy + 8, 5, base - sy - 8, OUT)
        cv.rect(lx + 1, sy + 8, 3, base - sy - 9, PANEL[2]); cv.vline(lx + 1, sy + 8, base - sy - 9, PANEL[3])
        cv.rect(lx, base - 2, 5, 2, BRASS[2])
    # someone's forgotten program on the seat
    cv.rect(ox + 60, sy - 1, 9, 3, PAPER[2]); cv.hline(ox + 61, sy, 6, "#7e3a30")
    return cv, ox + width // 2, base


def welcome_desk(width=102, height=46, label="LAST LIGHT", seed=0):
    """The club's welcome desk in the atrium: panelled front with the club's name, a desk lamp,
    a guest book, a jar of pencils, a stack of programs and a little bell."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3)
    top = base - 30
    # front: vertical boards
    cv.rect(ox, top, width, 30, OUT)
    cv.wood(ox + 1, top + 4, width - 2, 25, PANEL[3], vertical=True, plank=6, seed=seed + 4)
    cv.rect(ox + 1, base - 3, width - 2, 2, PANEL[1])
    # top
    cv.rect(ox - 1, top - 3, width + 2, 7, OUT)
    cv.rect(ox, top - 2, width, 5, PANEL[4]); cv.hline(ox, top - 2, width, PANEL[5]); cv.hline(ox, top + 2, width, PANEL[2])
    # name panel: velvet with brass letters, as on the club banner
    sw = text_width(label) + 10
    sx = ox + width // 2 - sw // 2
    cv.rect(sx - 1, top + 7, sw + 2, 15, OUT)
    cv.rect(sx, top + 8, sw, 13, VELVET[2]); cv.hline(sx, top + 8, sw, VELVET[4]); cv.hline(sx, top + 20, sw, VELVET[1])
    text(cv, label, ox + width // 2 - text_width(label) // 2, top + 10, "#f6cd78")
    for k in range(sx + 2, sx + sw - 1, 4):
        cv.px(k, top + 9, BRASS[3])
    # desk lamp with a green shade (pool of light on the top)
    lx = ox + 12
    cv.rect(lx - 6, top - 3, 14, 2, C("#f6cf7a", 0.35))
    cv.rect(lx, top - 12, 2, 10, BRASS[1]); cv.rect(lx - 3, top - 3, 8, 2, BRASS[2])
    cv.poly([(lx - 5, top - 12), (lx + 6, top - 12), (lx + 4, top - 17), (lx - 3, top - 17)], OUT)
    cv.poly([(lx - 4, top - 13), (lx + 5, top - 13), (lx + 3, top - 16), (lx - 2, top - 16)], "#3e6663")
    cv.hline(lx - 3, top - 12, 8, "#f6cd78")
    # open guest book
    gx = ox + 30
    cv.rect(gx, top - 5, 20, 4, OUT); cv.rect(gx + 1, top - 5, 8, 3, PAPER[3]); cv.rect(gx + 10, top - 5, 9, 3, PAPER[2])
    cv.hline(gx + 2, top - 4, 5, "#5a4a44"); cv.hline(gx + 11, top - 4, 6, "#5a4a44")
    cv.line(gx + 14, top - 7, gx + 18, top - 4, "#c84a3c")
    # pencil jar
    jx = ox + 56
    cv.rect(jx, top - 7, 6, 6, OUT); cv.rect(jx + 1, top - 6, 4, 5, "#5c897c")
    for k, c in enumerate(["#e8b45c", "#c84a3c", "#e8b45c"]):
        cv.vline(jx + 1 + k, top - 11 + (k % 2), 4, c)
    # programs stacked
    cv.rect(ox + 66, top - 6, 14, 5, OUT); cv.rect(ox + 67, top - 6, 12, 2, PAPER[3]); cv.rect(ox + 67, top - 4, 12, 2, PAPER[2])
    cv.rect(ox + 68, top - 6, 5, 1, "#7e3a30")
    # service bell
    bx = ox + width - 14
    cv.rect(bx - 4, top - 3, 10, 2, IRON[2])
    cv.ellipse(bx - 3, top - 8, 8, 7, BRASS[3]); cv.px(bx - 1, top - 7, BRASS[4]); cv.rect(bx, top - 10, 2, 2, BRASS[2])
    cv.rect(bx - 3, top - 4, 8, 1, BRASS[1])
    return cv, ox + width // 2, base


def directory_board(width=160, height=36, label="CLUB < / REPAIR >", seed=0):
    """The UMC room directory: a brass-framed board on two posts. The label is the header line;
    below it, room listings as rows of white letter-strips, one with a pencilled question mark."""
    cv = Canvas(width + 4, height + 6, seed=seed)
    ox, base = 2, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 - 8, 2)
    board_h = 28
    bt = base - height
    # posts and feet
    for px in (ox + 14, ox + width - 18):
        cv.rect(px, bt + board_h - 2, 4, base - bt - board_h + 2, OUT); cv.vline(px + 1, bt + board_h - 2, base - bt - board_h + 1, BRASS[2])
        cv.rect(px - 3, base - 2, 10, 2, OUT); cv.rect(px - 2, base - 2, 8, 1, BRASS[2])
    # frame and felt
    cv.rect(ox, bt, width, board_h, OUT)
    cv.rect(ox + 1, bt + 1, width - 2, board_h - 2, BRASS[2]); cv.hline(ox + 1, bt + 1, width - 2, BRASS[4]); cv.hline(ox + 1, bt + board_h - 2, width - 2, BRASS[0])
    cv.rect(ox + 3, bt + 3, width - 6, board_h - 6, "#1f1a2a")
    text(cv, label, ox + width // 2 - text_width(label) // 2, bt + 3, "#f6cd78")
    cv.hline(ox + 6, bt + 13, width - 12, "#3a3248")
    # listing strips (two columns)
    rng = np.random.default_rng(seed + 9)
    for col in range(2):
        for row in range(2):
            lx = ox + 10 + col * (width // 2 - 4)
            ly = bt + 16 + row * 4
            cv.hline(lx, ly, int(rng.integers(26, 46)), "#c8c0d8")
            cv.hline(lx + 52, ly, 8, "#8a8098")
    # the pencilled question mark beside LOST PROPERTY
    qx, qy = ox + width // 2 + 64, bt + 15
    for (dx, dy) in [(0, 1), (1, 0), (2, 0), (3, 1), (3, 2), (2, 3), (1, 4), (1, 5), (1, 7)]:
        cv.px(qx + dx, qy + dy, "#e06a5a")
    return cv, ox + width // 2, base


def potted_tree(width=50, height=38, seed=0, pot="ceramic"):
    """A broad-leaved potted plant in a glazed pot (the atrium planters)."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 6, height + 8, seed=seed)
    ox, base = 3, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 - 6, 2)
    cx = ox + width // 2
    pot_w, pot_h = width - 20, 15
    px = cx - pot_w // 2
    # stems
    for k in range(5):
        tx = cx + int(rng.integers(-pot_w // 2, pot_w // 2))
        cv.line(cx + (k - 2) * 2, base - pot_h, tx, base - height + int(rng.integers(8, 18)), "#3f4a2c")
    # leaves: pointed ovals, lit on top, darker beneath, back to front
    leaves = []
    for _ in range(int(width * height / 18)):
        a = rng.uniform(np.pi * 1.02, np.pi * 1.98)
        d = np.sqrt(rng.uniform(0.05, 1.0)) * (width / 2 - 3)
        lx = cx + np.cos(a) * d
        ly = base - pot_h - 1 + np.sin(a) * (height - pot_h - 2) * (d / (width / 2)) ** 0.5 * rng.uniform(0.75, 1.0)
        leaves.append((ly, lx, a + rng.uniform(-0.5, 0.5)))
    for k in range(4):
        leaves.append((base - pot_h - 1, cx + (k - 1.5) * pot_w / 3.2, np.pi * (0.15 if k > 1 else 0.85)))
    leaves.sort()
    for (ly, lx, a) in leaves:
        L = int(rng.integers(8, 13))
        dx, dy = np.cos(a), np.sin(a) * 0.6
        nx, ny = -dy, dx * 0.6
        pts = [(lx - dx * L / 2, ly - dy * L / 2), (lx + nx * 3, ly + ny * 3), (lx + dx * L / 2, ly + dy * L / 2), (lx - nx * 3, ly - ny * 3)]
        cv.poly(pts, OUT)
        inner = [(lx - dx * (L / 2 - 1.2), ly - dy * (L / 2 - 1.2)), (lx + nx * 2, ly + ny * 2), (lx + dx * (L / 2 - 1.2), ly + dy * (L / 2 - 1.2)), (lx - nx * 2, ly - ny * 2)]
        up = ly < base - pot_h - (height - pot_h) * 0.45
        cv.poly(inner, LEAF[4] if up else LEAF[3] if ly < base - pot_h - 4 else LEAF[2])
        half = [(lx - dx * (L / 2 - 1.2), ly - dy * (L / 2 - 1.2)), (lx - nx * 2, ly - ny * 2), (lx + dx * (L / 2 - 1.2), ly + dy * (L / 2 - 1.2))]
        cv.poly(half, LEAF[5] if up else LEAF[4])
        cv.line(int(round(lx - dx * (L / 2 - 2))), int(round(ly - dy * (L / 2 - 2))), int(round(lx + dx * (L / 2 - 2))), int(round(ly + dy * (L / 2 - 2))), LEAF[2] if up else LEAF[1])
    # glazed pot
    glaze = ["#1e2f33", "#2c4a4c", "#3e6663", "#5c897c", "#86b0a0"] if pot == "ceramic" else ["#5a2c22", "#7e3a30", "#a8604a", "#c47a5a", "#d99a7a"]
    cv.poly([(px - 1, base - pot_h - 1), (px + pot_w, base - pot_h - 1), (px + pot_w - 3, base), (px + 2, base)], OUT)
    cv.poly([(px, base - pot_h), (px + pot_w - 1, base - pot_h), (px + pot_w - 4, base - 1), (px + 3, base - 1)], glaze[2])
    cv.poly([(px + pot_w - 8, base - pot_h), (px + pot_w - 1, base - pot_h), (px + pot_w - 4, base - 1), (px + pot_w - 9, base - 1)], glaze[1])
    cv.vline(px + 3, base - pot_h + 2, pot_h - 4, glaze[3]); cv.vline(px + 4, base - pot_h + 3, pot_h - 7, glaze[4])
    cv.rect(px - 2, base - pot_h - 3, pot_w + 4, 3, OUT); cv.rect(px - 1, base - pot_h - 3, pot_w + 2, 2, glaze[3]); cv.hline(px - 1, base - pot_h - 3, pot_w + 2, glaze[4])
    cv.hline(px + 2, base - pot_h + 5, pot_w - 4, glaze[1])
    cv.rect(px + 1, base - pot_h - 1, pot_w - 2, 1, "#2a1c18")
    return cv, cx, base


# ---------------------------------------------------------------------------------------------
# U05 repair landing: back-of-house block walls, conduit, the open stairwell, service stairs
# ---------------------------------------------------------------------------------------------

def block_wall(cv, x, y, w, h, dado_top=None, seed=0):
    """Painted concrete block (cream-grey, coursed 8 high, 16 long) over a dark teal painted dado
    with a safety-yellow stripe between them."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, BLOCK[2])
    for row, yy in enumerate(range(y, y + h, 8)):
        off = 0 if row % 2 else 8
        for xx in range(x - off, x + w, 16):
            x0, x1 = max(x, xx), min(x + w, xx + 15)
            if x1 <= x0:
                continue
            tone = BLOCK[4] if rng.random() < 0.7 else mix(BLOCK[4], BLOCK[5], 0.5)
            cv.rect(x0, yy, x1 - x0, min(7, y + h - yy), tone)
            cv.hline(x0, yy, x1 - x0, shade(tone, 0.08))
            for _ in range((x1 - x0) // 4):
                cv.px(x0 + int(rng.integers(0, x1 - x0)), yy + int(rng.integers(1, 7)), shade(tone, float(rng.choice([-0.06, 0.05]))))
    if dado_top is not None:
        dh = y + h - dado_top
        cv.rect(x, dado_top, w, dh, DADO[2])
        for row, yy in enumerate(range(dado_top, y + h, 8)):
            off = 0 if row % 2 else 8
            cv.hline(x, yy, w, DADO[1])
            for xx in range(x - off, x + w, 16):
                cv.vline(xx + 15, yy, min(8, y + h - yy), DADO[1])
            cv.hline(x, yy + 1, w, C(DADO[3], 0.6))
        cv.rect(x, dado_top - 3, w, 3, SAFETY[2]); cv.hline(x, dado_top - 3, w, SAFETY[3]); cv.hline(x, dado_top - 1, w, SAFETY[1])
        # scuffs where carts bump the wall
        for _ in range(w // 40):
            sx = x + int(rng.integers(0, w - 10))
            cv.hline(sx, y + h - int(rng.integers(6, 14)), int(rng.integers(4, 12)), DADO[4])
    cv.rect(x, y + h - 3, w, 3, DADO[0]); cv.hline(x, y + h - 3, w, DADO[3])


def conduit_run(cv, x0, x1, y, thick=3, colour=None, straps=24):
    """Exposed metal conduit along the wall with pipe straps."""
    c = colour or ["#3a3a48", "#6c6a88", "#9a98b0"]
    cv.rect(x0, y, x1 - x0, thick, c[0])
    cv.hline(x0, y, x1 - x0, c[2]); cv.hline(x0, y + 1, x1 - x0, c[1])
    for sx in range(x0 + 6, x1, straps):
        cv.rect(sx, y - 1, 2, thick + 2, IRON[1]); cv.px(sx, y - 1, IRON[4])


def conduit_drop(cv, x, y0, y1, thick=3):
    cv.rect(x, y0, thick, y1 - y0, "#3a3a48"); cv.vline(x, y0, y1 - y0, "#9a98b0"); cv.vline(x + 1, y0, y1 - y0, "#6c6a88")
    for sy in range(y0 + 8, y1, 20):
        cv.rect(x - 1, sy, thick + 2, 2, IRON[1])


def junction_box(cv, x, y, w=10, h=9, label=None):
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#6a6878"); cv.hline(x + 1, y + 1, w - 2, "#8e8ca0")
    bolt(cv, x + 2, y + 2); bolt(cv, x + w - 3, y + h - 3)
    if label:
        cv.rect(x + 2, y + h // 2, w - 4, 2, label)


def big_pipe(cv, x0, x1, y, colour="#7e3a30"):
    """A painted water/sprinkler main along the ceiling line with flanges."""
    cv.rect(x0, y, x1 - x0, 6, OUT)
    cv.rect(x0, y + 1, x1 - x0, 4, colour); cv.hline(x0, y + 1, x1 - x0, shade(colour, 0.25)); cv.hline(x0, y + 4, x1 - x0, shade(colour, -0.3))
    for fx in range(x0 + 40, x1, 90):
        cv.rect(fx, y - 1, 3, 8, shade(colour, -0.2)); cv.vline(fx, y - 1, 8, shade(colour, 0.2))


def punch_clock(cv, x, y):
    """Time clock with a rack of punch cards beside it (Mags: 'Clock out')."""
    cv.rect(x, y, 18, 22, OUT); cv.rect(x + 1, y + 1, 16, 20, "#8a8478"); cv.hline(x + 1, y + 1, 16, "#aaa496")
    cv.ellipse(x + 3, y + 3, 12, 12, OUT); cv.ellipse(x + 4, y + 4, 10, 10, PAPER[3])
    cv.vline(x + 9, y + 5, 4, OUT); cv.hline(x + 9, y + 9, 3, OUT)
    cv.rect(x + 4, y + 16, 10, 2, OUT); cv.rect(x + 5, y + 16, 8, 1, "#c84a3c")
    # card rack
    rx = x + 21
    cv.rect(rx, y - 2, 14, 30, OUT); cv.rect(rx + 1, y - 1, 12, 28, "#5a5462")
    for k in range(5):
        cy = y + k * 5
        cv.rect(rx + 2, cy, 10, 4, IRON[1])
        cv.rect(rx + 3, cy - 2 + (k % 2), 8, 5, PAPER[2] if k != 2 else PAPER[3])
        cv.hline(rx + 4, cy, 5, "#7e7466")
        if k == 1:
            cv.px(rx + 9, cy - 1, "#c84a3c")


def key_cabinet(cv, x, y, w=26, h=24, open_=True):
    """Wall key box (spare keys), door open, keys on hooks with coloured tags."""
    rng = np.random.default_rng(x)
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#3a4a58"); cv.rect(x + 2, y + 2, w - 4, h - 4, "#24303a")
    for row in range(3):
        for col in range(4):
            kx, ky = x + 4 + col * 5, y + 4 + row * 7
            cv.px(kx, ky, BRASS[3])
            if rng.random() < 0.8:
                cv.vline(kx, ky + 1, 3, "#c0c4cc"); cv.px(kx - 1, ky + 1, "#c0c4cc")
                cv.rect(kx, ky + 4, 2, 2, ITEM_COLOURS[int(rng.integers(0, 6))])
    if open_:
        cv.poly([(x + w, y), (x + w + 6, y + 2), (x + w + 6, y + h - 2), (x + w, y + h)], "#4a5a68")
        cv.vline(x + w + 5, y + 2, h - 4, "#5e7080")
    cv.rect(x + w // 2 - 6, y - 7, 12, 6, PAPER[2])
    cv.hline(x + w // 2 - 4, y - 5, 8, "#5a4a44"); cv.hline(x + w // 2 - 4, y - 3, 6, "#5a4a44")


def pegboard(cv, x, y, w, h, tools=True, seed=0):
    """Brown pegboard with painted tool outlines and the tools hanging in most of them."""
    rng = np.random.default_rng(seed)
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, KRAFT[1])
    for yy in range(y + 2, y + h, 4):
        for xx in range(x + 2 + (yy // 4 % 2) * 2, x + w, 4):
            cv.px(xx, yy, KRAFT[0])
    cv.hline(x, y, w, KRAFT[2])
    if not tools:
        return
    for band, (y_top, y_len) in enumerate([(y + 3, 15), (y + h // 2 + 2, h // 2 - 5)]):
        xx = x + 4 + band * 3
        while xx < x + w - 10:
            kind = int(rng.integers(0, 6))
            present = rng.random() < 0.82
            if kind == 0:   # wrench, or its painted outline
                c = IRON[4] if present else "#e6d6b1"
                cv.vline(xx + 1, y_top + 2, y_len - 2, c); cv.rect(xx, y_top, 3, 3, c)
                if present:
                    cv.px(xx + 1, y_top, KRAFT[1])
                xx += 6
            elif kind == 1:  # hammer
                if present:
                    cv.vline(xx + 3, y_top + 3, y_len - 3, WOOD[4]); cv.rect(xx, y_top, 7, 3, IRON[3]); cv.hline(xx, y_top, 7, IRON[4])
                else:
                    cv.rect(xx, y_top, 7, 1, "#e6d6b1"); cv.vline(xx + 3, y_top + 1, y_len - 1, "#e6d6b1")
                xx += 10
            elif kind == 2:  # screwdrivers
                for k in range(3):
                    c = ["#c84a3c", "#e8b45c", "#425da6"][k]
                    cv.rect(xx + k * 3, y_top, 2, 5, c); cv.vline(xx + k * 3, y_top + 5, y_len - 6, IRON[4])
                xx += 11
            elif kind == 3:  # coil of cable
                r = min(10, y_len)
                cv.ellipse(xx, y_top + 1, r, r, OUT); cv.ellipse(xx + 1, y_top + 2, r - 2, r - 2, "#c84a3c"); cv.ellipse(xx + 3, y_top + 4, r - 6, r - 6, KRAFT[1])
                xx += r + 3
            elif kind == 4:  # pliers
                cv.line(xx, y_top + y_len, xx + 3, y_top + 4, "#c84a3c"); cv.line(xx + 5, y_top + y_len, xx + 3, y_top + 4, "#c84a3c"); cv.rect(xx + 2, y_top + 1, 3, 4, IRON[3])
                xx += 8
            else:  # tape rolls on a peg
                cv.hline(xx, y_top + 1, 9, IRON[3])
                for k, c in enumerate(["#e8b45c", "#c0c4cc"]):
                    cv.ellipse(xx + k * 5, y_top + 2, 5, 5, OUT); cv.ellipse(xx + k * 5 + 1, y_top + 3, 3, 3, c)
                xx += 12


def extinguisher(cv, x, y):
    """Red fire extinguisher on a wall bracket with its sign above; (x, y) = bottom-left of the body."""
    cv.rect(x - 2, y - 30, 14, 7, "#c84a3c"); cv.rect(x - 1, y - 29, 12, 5, "#e06a5a")
    cv.px(x + 4, y - 28, PAPER[3]); cv.rect(x + 3, y - 27, 3, 2, PAPER[3])
    cv.rect(x + 1, y - 20, 8, 20, OUT); cv.rect(x + 2, y - 19, 6, 18, "#a83c32"); cv.vline(x + 3, y - 18, 16, "#e06a5a")
    cv.rect(x + 3, y - 23, 4, 3, IRON[1]); cv.line(x + 7, y - 22, x + 10, y - 16, IRON[0])
    cv.rect(x + 2, y - 12, 6, 4, PAPER[2])
    cv.rect(x, y - 8, 10, 2, IRON[2])


def concrete_floor(cv, x, y, w, h, seed=0, slab=48):
    """Sealed concrete in big slabs with saw-cut joints, trowel sheen, stains and scuffs."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, CONCRETE[3])
    for _ in range(w * h // 9):
        px, py = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        cv.px(px, py, CONCRETE[int(rng.choice([2, 4, 4]))])
    # soft trowel patches
    for _ in range(w * h // 1400):
        cx, cy = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        soft_ellipse(cv, cx, cy, int(rng.integers(12, 30)), int(rng.integers(3, 7)), CONCRETE[5], 0.25)
    # saw-cut joints
    yy, row = y, 0
    while yy < y + h:
        rh = int(round(30 + 12 * (yy - y) / max(1, h)))
        cv.hline(x, yy, w, CONCRETE[1]); cv.hline(x, yy + 1, w, CONCRETE[5])
        yy += rh
        row += 1
    for xx in range(x + slab, x + w, slab):
        cv.vline(xx, y, h, CONCRETE[1]); cv.vline(xx + 1, y, h, CONCRETE[5])
    # oil and coffee stains, rubber scuffs
    for _ in range(w * h // 5000 + 2):
        cx, cy = x + int(rng.integers(10, w - 10)), y + int(rng.integers(6, h - 6))
        soft_ellipse(cv, cx, cy, int(rng.integers(4, 9)), int(rng.integers(2, 4)), CONCRETE[0], 0.35)
    for _ in range(w * h // 1800):
        sx, sy = x + int(rng.integers(0, w - 12)), y + int(rng.integers(0, h))
        cv.line(sx, sy, sx + int(rng.integers(5, 14)), sy + int(rng.integers(-1, 2)), CONCRETE[1])


def hazard_band(cv, x, y, w, h, vertical=False):
    """Yellow and black safety stripes (diagonal), for floor edges and kick plates."""
    for yy in range(h):
        for xx in range(w):
            k = (xx + yy) if not vertical else (yy - xx)
            cv.px(x + xx, y + yy, SAFETY[2] if (k // 3) % 2 == 0 else "#1a1820")


def floor_arrow(cv, cx, cy, size=8, colour=None, down=False, label=None):
    """Worn floor-paint arrow, pointing up the screen (toward the wall) unless down."""
    c = colour or SAFETY[2]
    d = 1 if down else -1
    cv.rect(cx - 2, cy - size * d * 0 - (0 if down else size), 5, size, C(c, 0.8))
    tip = cy + d * (size + 6) if down else cy - size - 6
    base = cy + (size if down else -size)
    cv.poly([(cx - 6, base), (cx + 6, base), (cx, tip)], C(c, 0.8))
    if label:
        text(cv, label, cx - text_width(label) // 2, cy + (2 if not down else -12), C(c, 0.8))


def stairwell_void(cv, x0, y0, x1, y1, seed=0):
    """The open well in the landing floor, seen from above: the far wall dropping away, the next
    flight going down along the left wall, a mid landing, and the lanes' neon glow far below."""
    w, h = x1 - x0, y1 - y0
    cv.rect(x0, y0, w, h, "#0e0c14")
    # far wall face (lit at the top by the landing lights, falling into shadow)
    for yy in range(y0, y1):
        t = (yy - y0) / h
        cv.hline(x0, yy, w, mix(BLOCK[3], "#0e0c14", min(1.0, t * 1.6)))
    for row, yy in enumerate(range(y0, y0 + 26, 6)):
        off = 0 if row % 2 else 8
        for xx in range(x0 - off, x1, 16):
            cv.vline(xx, yy, 6, C("#0e0c14", 0.4))
        cv.hline(x0, yy, w, C("#0e0c14", 0.35))
    cv.rect(x0, y0 + 9, w, 2, C(SAFETY[2], 0.55))
    # level number stencilled on the far wall
    text(cv, "B1", x0 + w - 30, y0 + 1, C(PAPER[3], 0.7))
    # the next flight down: a diagonal of treads from the left edge toward the mid landing
    fx0, fy0 = x0 + 4, y0 + 10
    steps = 11
    for i in range(steps):
        t = i / steps
        sx = fx0 + int(i * (w * 0.55) / steps)
        sy = fy0 + int(i * (h * 0.55) / steps)
        tone = mix(CONCRETE[5], "#14121a", min(1.0, t * 1.1))
        cv.rect(sx, sy, 20, 3, tone); cv.hline(sx, sy, 20, mix(SAFETY[2], tone, 0.4 + t * 0.6))
        cv.rect(sx, sy + 3, 20, 2, shade(tone, -0.4))
    # its handrail and the stringer underneath
    cv.line(fx0 + 20, fy0 - 6, fx0 + 20 + int(w * 0.55), fy0 - 6 + int(h * 0.55), SAFETY[1])
    cv.line(fx0, fy0 + 5, fx0 + int(w * 0.55), fy0 + 5 + int(h * 0.55), "#1a1820")
    # mid landing on the right, lit by a caged bulb
    lx, ly = x0 + int(w * 0.6), y0 + int(h * 0.62)
    cv.rect(lx, ly, int(w * 0.36), 8, "#2a2630"); cv.hline(lx, ly, int(w * 0.36), SAFETY[1])
    soft_ellipse(cv, lx + int(w * 0.18), ly + 3, int(w * 0.16), 4, AMBER[3], 0.12)
    # neon glow from the lanes two floors down
    for (r, a) in [(60, 0.06), (40, 0.08), (22, 0.1)]:
        soft_ellipse(cv, x0 + int(w * 0.35), y1 - 6, r, max(3, r // 6), "#ff7aa8", a)
    for (r, a) in [(40, 0.06), (24, 0.08)]:
        soft_ellipse(cv, x0 + int(w * 0.75), y1 - 3, r, max(3, r // 6), "#58e0d0", a)


def service_doorway(cv, cx, base, floor_y, w=60, h=74, seed=0):
    """A steel-framed service doorway in the block wall with the stair to the lanes dropping away
    behind it; neon from below colours the walls. The first treads start on the landing floor."""
    x0, x1 = cx - w // 2, cx + w // 2
    top = base - h
    # steel frame
    cv.rect(x0 - 5, top - 5, w + 10, h + 5, OUT)
    cv.rect(x0 - 4, top - 4, w + 8, h + 4, "#4a5a68"); cv.hline(x0 - 4, top - 4, w + 8, "#7a8a98")
    cv.vline(x0 - 4, top - 4, h + 4, "#6a7a88")
    # opening: dark stairwell going down, walls lit pink and teal from below
    cv.rect(x0, top, w, h, "#110e18")
    for yy in range(top, base):
        t = (yy - top) / h
        cv.hline(x0, yy, 6, mix("#2a1830", "#6a2a4a", t)); cv.hline(x1 - 6, yy, 6, mix("#14262a", "#2a5a58", t))
    # far landing: a door with a lit LANES sign in neon
    cv.rect(cx - 12, top + 10, 24, 30, "#1a1422")
    cv.rect(cx - 9, top + 14, 18, 24, "#2a1a2a")
    text(cv, "LANES", cx - 15, top + 1, "#ff7aa8")
    # treads from the floor line back into the doorway, darker and narrower
    n = 10
    y = floor_y
    for i in range(n):
        th = max(3, 6 - i // 3)
        t = i / (n - 1)
        inset = int(round(1 + t * w * 0.2))
        tone = mix(CONCRETE[5], "#120e18", min(1.0, t * 1.1))
        cv.rect(x0 + inset, y - th, w - inset * 2, th, tone)
        cv.hline(x0 + inset, y - th, w - inset * 2, mix(SAFETY[2], tone, 0.3 + t * 0.7))
        cv.hline(x0 + inset, y - 1, w - inset * 2, shade(tone, -0.35))
        cv.rect(x0, y - th, inset, th, mix("#3a2440", "#110e18", t))
        cv.rect(x1 - inset, y - th, inset, th, mix("#1e3436", "#110e18", t))
        y -= th
    # handrails
    cv.line(x0 + 1, floor_y - 14, x0 + int(w * 0.2) + 1, y - 2, SAFETY[2])
    cv.line(x1 - 2, floor_y - 14, x1 - int(w * 0.2) - 2, y - 2, SAFETY[2])
    for kx in (x0 - 5, x1):
        cv.rect(kx, base, 5, floor_y - base, "#4a5a68"); cv.vline(kx, base, floor_y - base, "#7a8a98")
        cv.hline(kx, floor_y - 1, 5, C(SHADOW, 0.5))
    hazard_band(cv, x0, floor_y - 3, w, 3)


def stair_up_flight(cv, x0, y0, x1, y1, bottom, seed=0):
    """Stairs climbing toward the viewer and out through a gap in the front wall: treads get wider
    and brighter as they rise toward the atrium's warm light."""
    w = x1 - x0
    y = y0
    i = 0
    while y < bottom:
        th = 6 + i // 3
        t = min(1.0, (y - y0) / max(1, bottom - y0))
        tone = mix(CONCRETE[4], "#c8a888", t * 0.6)
        cv.rect(x0, y, w, th, shade(tone, -0.35))
        cv.rect(x0, y, w, th - 2, tone)
        cv.hline(x0, y, w, mix(SAFETY[2], tone, 0.2))
        cv.hline(x0, y + 1, w, shade(tone, 0.1))
        y += th
        i += 1
    # side walls of the flight (handrail on the open right side)
    cv.rect(x1, y0 - 2, 4, bottom - y0 + 2, BLOCK[3]); cv.vline(x1, y0 - 2, bottom - y0 + 2, BLOCK[5]); cv.vline(x1 + 3, y0 - 2, bottom - y0 + 2, BLOCK[1])
    cv.rect(x0 - 4, y0 - 2, 4, bottom - y0 + 2, BLOCK[1])
    cv.line(x1 - 2, y0 - 12, x1 - 2, bottom, SAFETY[2]); cv.line(x1 - 1, y0 - 12, x1 - 1, bottom, SAFETY[1])
    cv.rect(x1 - 3, y0 - 13, 3, 2, SAFETY[3])
    # warm light pouring down the steps from the atrium
    for (r, a) in [(w // 2 + 10, 0.08), (w // 2, 0.1), (w // 3, 0.12)]:
        cv.rect(x0 + w // 2 - r, bottom - (bottom - y0) // 2, r * 2, (bottom - y0) // 2, C(AMBER[3], a))


# ---------------------------------------------------------------------------------------------
# U05 props
# ---------------------------------------------------------------------------------------------

def well_rail(width=240, depth=58, rail_h=20, seed=0):
    """Guard rail round the open stairwell: yellow handrails on dark steel posts, a hazard-striped
    kick plate along the front edge. Transparent inside so the well painted in the room shows."""
    cv = Canvas(width + 6, depth + rail_h + 6, seed=seed)
    ox, base = 3, depth + rail_h + 3
    back = base - depth
    x0, x1 = ox, ox + width - 1

    def rail_line(y, xa, xb):
        cv.rect(xa, y, xb - xa + 1, 3, OUT)
        cv.hline(xa, y + 1, xb - xa + 1, SAFETY[2]); cv.hline(xa + 1, y, xb - xa - 1, SAFETY[3])

    def post(x, yb, h):
        cv.rect(x - 1, yb - h, 3, h, OUT); cv.vline(x, yb - h + 1, h - 1, IRON[3])

    # back rail (furthest away): posts, mid rail, handrail, a toe plate on the edge
    cv.rect(x0, back - 3, width, 3, SAFETY[1]); cv.hline(x0, back - 3, width, SAFETY[2])
    for px in range(x0 + 12, x1 - 6, 24):
        post(px, back - 2, rail_h)
    cv.hline(x0, back - rail_h // 2 - 2, width, IRON[2])
    rail_line(back - rail_h - 2, x0, x1)
    # side rails: the handrail runs straight toward the viewer, so it reads as an upright bar
    for sx in (x0, x1 - 2):
        cv.rect(sx, back - rail_h - 2, 3, depth + 2, OUT)
        cv.vline(sx + 1, back - rail_h - 1, depth, SAFETY[2])
        for py in range(back + 14, base - rail_h, 16):
            cv.rect(sx, py - 1, 3, 2, IRON[1])
    # front rail
    for px in range(x0 + 12, x1 - 6, 24):
        post(px, base - 4, rail_h - 4)
    cv.hline(x0, base - rail_h // 2 - 3, width, IRON[3]); cv.hline(x0, base - rail_h // 2 - 2, width, IRON[1])
    rail_line(base - rail_h - 1, x0, x1)
    for cx_ in (x0 + 1, x1 - 1):
        cv.rect(cx_ - 2, base - rail_h - 3, 5, 3, SAFETY[3]); cv.hline(cx_ - 2, base - rail_h - 3, 5, "#fff0c4")
    # kick plate facing the room
    cv.rect(x0, base - 5, width, 5, OUT)
    hazard_band(cv, x0 + 1, base - 4, width - 2, 3)
    ground_shadow(cv, ox + width // 2, base + 1, width // 2, 1, alpha=0.3)
    return cv, ox + width // 2, base


def repair_bench(width=86, height=46, seed=0):
    """Cal's repair bench: a steel bench with an open radio chassis (valves glowing), a meter,
    a soldering iron in its stand, a parts organiser and a red toolbox underneath."""
    cv = Canvas(width + 6, height + 8, seed=seed)
    ox, base = 3, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3)
    top = base - 24
    # legs, lower shelf, toolbox
    for lx in (ox + 2, ox + width - 6):
        cv.rect(lx, top + 2, 4, base - top - 2, OUT); cv.vline(lx + 1, top + 3, base - top - 4, IRON[3])
    cv.rect(ox + 2, base - 7, width - 4, 3, OUT); cv.hline(ox + 3, base - 6, width - 6, IRON[3])
    cv.rect(ox + 10, base - 15, 22, 9, OUT); cv.rect(ox + 11, base - 14, 20, 7, "#a83c32"); cv.hline(ox + 11, base - 14, 20, "#c84a3c")
    cv.rect(ox + 17, base - 17, 8, 3, OUT); cv.rect(ox + 19, base - 11, 4, 2, IRON[4])
    for k in range(4):  # parts organiser drawers
        cv.rect(ox + 42 + k * 9, base - 16, 8, 9, OUT); cv.rect(ox + 43 + k * 9, base - 15, 6, 7, "#5c6a78")
        cv.rect(ox + 44 + k * 9, base - 12, 4, 1, PAPER[2])
    # bench top: a thick steel-edged slab of worn plywood
    cv.rect(ox - 1, top - 1, width + 2, 7, OUT)
    cv.rect(ox, top, width, 5, KRAFT[2]); cv.hline(ox, top, width, KRAFT[3]); cv.hline(ox, top + 4, width, IRON[2])
    for k in range(6):
        cv.hline(ox + 4 + k * 13, top + 2, 6, KRAFT[1])
    # open radio chassis with valves
    rx = ox + 6
    cv.rect(rx, top - 12, 30, 12, OUT); cv.rect(rx + 1, top - 11, 28, 11, "#7a5a3a"); cv.hline(rx + 1, top - 11, 28, "#9a7a52")
    cv.rect(rx + 3, top - 9, 24, 7, "#3a3040")
    for k, vx in enumerate((rx + 6, rx + 12, rx + 18)):
        cv.rect(vx, top - 16, 4, 8, OUT); cv.rect(vx + 1, top - 15, 2, 6, AMBER[3] if k != 1 else AMBER[2]); cv.px(vx + 1, top - 15, AMBER[4])
    cv.ellipse(rx + 22, top - 9, 6, 6, "#c0c4cc"); cv.px(rx + 24, top - 7, OUT)
    cv.line(rx + 29, top - 4, rx + 36, top - 1, "#c84a3c"); cv.line(rx + 29, top - 3, rx + 38, top - 1, OUT)
    # multimeter with a needle
    mx = ox + 44
    cv.rect(mx, top - 10, 12, 10, OUT); cv.rect(mx + 1, top - 9, 10, 9, "#e8b45c")
    cv.rect(mx + 2, top - 8, 8, 4, PAPER[3]); cv.line(mx + 3, top - 5, mx + 7, top - 8, "#c84a3c")
    cv.px(mx + 4, top - 2, OUT); cv.px(mx + 7, top - 2, OUT)
    # soldering iron in its coil stand, a curl of smoke
    sx = ox + 62
    cv.rect(sx, top - 3, 10, 3, IRON[1]); cv.line(sx + 2, top - 3, sx + 9, top - 9, IRON[3]); cv.line(sx + 3, top - 3, sx + 10, top - 9, IRON[4])
    cv.line(sx + 9, top - 9, sx + 13, top - 12, "#5c897c")
    for k, (dx, dy) in enumerate([(13, -14), (12, -16), (13, -18), (14, -20)]):
        cv.px(sx + dx, top + dy, C("#c8c8d8", 0.6 - k * 0.1))
    # mug (Cal drinks tea)
    cv.rect(ox + width - 10, top - 7, 6, 7, OUT); cv.rect(ox + width - 9, top - 6, 4, 6, "#5c897c"); cv.px(ox + width - 4, top - 4, OUT)
    cv.hline(ox + width - 9, top - 6, 4, "#86b0a0")
    return cv, ox + width // 2, base


def access_panel(width=43, height=64, seed=0):
    """A humming freestanding maintenance panel: steel cabinet with its door swung open, rows of
    breakers, one amber fuse lit (TOMORROW), one slot empty (yesterday). Also returns the lit fuse
    and the empty slot relative to the anchor, for the flicker layer."""
    cv = Canvas(width + 12, height + 10, seed=seed)
    ox, base = 8, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    bw = width - 2
    bx = ox + 1
    top = base - height + 8
    # conduit stubs out of the top
    for cx_ in (bx + 7, bx + bw - 10):
        cv.rect(cx_, top - 8, 3, 8, "#3a3a48"); cv.vline(cx_, top - 8, 8, "#9a98b0")
        cv.rect(cx_ - 1, top - 2, 5, 2, IRON[2])
    # plinth
    cv.rect(bx - 1, base - 5, bw + 2, 5, OUT); cv.rect(bx, base - 4, bw, 3, IRON[1])
    # body
    cv.rect(bx - 1, top - 1, bw + 2, base - top - 3, OUT)
    cv.rect(bx, top, bw, base - top - 5, "#7a7a8a"); cv.hline(bx, top, bw, "#a4a4b4"); cv.vline(bx + bw - 1, top, base - top - 5, "#5a5a6a")
    cv.vline(bx, top, base - top - 5, "#8e8e9e")
    # header with stencil
    cv.rect(bx + 1, top + 1, bw - 2, 11, "#2a2a36")
    text(cv, "ACCESS", bx + bw // 2 - 17, top + 2, SAFETY[3])
    # interior backplate and breakers
    ix, iy, iw, ih = bx + 3, top + 14, bw - 6, base - top - 22
    cv.rect(ix - 1, iy - 1, iw + 2, ih + 2, "#4a4a5a")
    cv.rect(ix, iy, iw, ih, "#d8d2c2"); cv.rect(ix, iy, iw, 1, "#a8a292")
    lit, empty = None, None
    for row in range(5):
        for col in range(3):
            fx, fy = ix + 3 + col * 11, iy + 3 + row * 8
            if row == 2 and col == 0:
                cv.rect(fx, fy, 7, 5, "#2a2630"); bolt(cv, fx + 1, fy + 1, "#8a8478"); empty = (fx, fy)
                cv.hline(fx, fy + 6, 7, "#b8b0a0")
                continue
            cv.rect(fx, fy, 7, 5, OUT); cv.rect(fx + 1, fy + 1, 5, 3, "#3a3a48")
            if row == 2 and col == 1:
                cv.rect(fx + 1, fy + 1, 5, 3, AMBER[3]); cv.rect(fx + 2, fy + 2, 3, 1, AMBER[4]); lit = (fx, fy)
                cv.hline(fx, fy + 6, 7, "#c84a3c")
            else:
                cv.rect(fx + 2 + (row + col) % 2, fy + 1, 2, 3, IRON[4])
                cv.hline(fx, fy + 6, 7, "#8a8478")
    # the door swung open to the left with a warning sticker
    cv.poly([(bx - 1, top - 1), (ox - 7, top + 3), (ox - 7, base - 9), (bx - 1, base - 5)], OUT)
    cv.poly([(bx - 2, top + 1), (ox - 6, top + 4), (ox - 6, base - 10), (bx - 2, base - 7)], "#6a6a7a")
    cv.vline(ox - 6, top + 4, base - top - 14, "#8a8a9a")
    cv.poly([(ox - 5, top + 24), (ox - 2, top + 17), (ox, top + 25)], SAFETY[2])
    cv.px(ox - 2, top + 21, OUT)
    # vent slots at the bottom
    for vy in range(base - 9, base - 5, 2):
        cv.hline(bx + 6, vy, bw - 12, "#4a4a5a")
    ax, ay = ox + width // 2, base
    return cv, ax, ay, (lit[0] - ax, lit[1] - ay), (empty[0] - ax, empty[1] - ay)


def checklist_cart(width=49, height=40, seed=0):
    """Mags's utility cart. The checklist itself is drawn by the game on the front panel, so the
    panel is left plain (x -15..15, y -33..-9 from the anchor). On top: cups, a coffee mug, a
    spray bottle, her key ring; a push handle on the right."""
    cv = Canvas(width + 10, height + 16, seed=seed)
    ox, base = 3, height + 12
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 + 2, 3)
    blue = ["#1b2140", "#283866", "#3a4f8a", "#5671b0"]
    # wheels
    for wx in (ox + 3, ox + width - 8):
        cv.rect(wx, base - 5, 5, 5, OUT); cv.rect(wx + 1, base - 4, 3, 3, IRON[3]); cv.px(wx + 2, base - 3, IRON[1])
    # body / front panel
    cv.rect(ox, base - 38, width, 33, OUT)
    cv.rect(ox + 1, base - 37, width - 2, 31, blue[1])
    cv.hline(ox + 1, base - 37, width - 2, blue[3]); cv.vline(ox + 1, base - 37, 31, blue[2])
    cv.rect(ox + 1, base - 8, width - 2, 2, blue[0])
    cv.rect(cx - 17, base - 35, 34, 28, blue[0]); cv.rect(cx - 16, base - 34, 32, 26, blue[2])
    for k in range(4):  # tape corners where the paper goes
        tx, ty = (cx - 17 if k % 2 == 0 else cx + 14), (base - 35 if k < 2 else base - 10)
        cv.rect(tx, ty, 3, 3, C(PAPER[3], 0.6))
    # top tray lip
    cv.rect(ox - 1, base - 41, width + 2, 4, OUT); cv.rect(ox, base - 40, width, 2, blue[3]); cv.hline(ox, base - 40, width, "#7a90c8")
    # push handle on the right
    hx = ox + width + 1
    cv.rect(hx, base - 50, 3, 40, OUT); cv.vline(hx + 1, base - 49, 38, IRON[4])
    cv.rect(hx - 2, base - 51, 6, 3, OUT); cv.rect(hx - 1, base - 50, 4, 1, "#c84a3c")
    # stacked paper cups ("cups back")
    for k in range(3):
        cv.rect(ox + 4 + k * 4, base - 48 + k * 2, 4, 8 - k * 2, PAPER[3]); cv.vline(ox + 4 + k * 4, base - 48 + k * 2, 8 - k * 2, PAPER[1])
    cv.rect(ox + 3, base - 49, 6, 1, PAPER[2])
    # coffee mug
    cv.rect(cx - 3, base - 47, 7, 7, OUT); cv.rect(cx - 2, base - 46, 5, 6, "#e6d6b1"); cv.px(cx + 4, base - 44, OUT)
    cv.hline(cx - 2, base - 46, 5, "#4a2b24")
    # spray bottle
    sx = ox + width - 12
    cv.rect(sx, base - 49, 6, 9, OUT); cv.rect(sx + 1, base - 48, 4, 8, "#5c897c"); cv.rect(sx + 1, base - 52, 3, 4, OUT); cv.rect(sx + 3, base - 52, 3, 2, "#e8b45c")
    # key ring on a hook
    cv.ellipse(ox + 2, base - 32, 6, 6, BRASS[3]); cv.ellipse(ox + 3, base - 31, 4, 4, blue[1])
    cv.vline(ox + 2, base - 27, 4, "#c0c4cc"); cv.vline(ox + 5, base - 27, 3, "#c0c4cc")
    return cv, cx, base


# ---------------------------------------------------------------------------------------------
# U07 lost property: warm ochre walls over the club room's wainscot, worn vinyl, cubbies, tags
# ---------------------------------------------------------------------------------------------

OCHRE = ["#3a2a26", "#5a4234", "#6e5240", "#7e604a", "#8e6e54", "#a08060"]


def ochre_wall(cv, x, y, w, h, seed=0):
    """Distempered ochre plaster: patchy, with old picture-rail marks and pin holes."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, OCHRE[3])
    for _ in range(w * h // 260):
        cx, cy = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        soft_ellipse(cv, cx, cy, int(rng.integers(6, 18)), int(rng.integers(3, 8)), OCHRE[int(rng.choice([2, 4]))], 0.35)
    for _ in range(w * h // 90):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), OCHRE[int(rng.choice([2, 4]))])
    for _ in range(w * h // 900):
        cv.px(x + int(rng.integers(0, w)), y + int(rng.integers(0, h)), OCHRE[1])
    # stepped shade under the ceiling
    for i, (hh, a) in enumerate([(14, 0.10), (8, 0.10), (4, 0.12)]):
        cv.rect(x, y, w, hh, C("#2a1a2a", a))


def vinyl_floor(cv, x, y, w, h, seed=0, tile=16, wear=(), border=(18, 782)):
    """Worn institutional linoleum tiles: two close warm tans in a quiet checker, speckled, with an
    oxblood border band along the walls and the odd mismatched replacement tile. Rows deepen toward
    the viewer. wear: [(cx, cy, rx, ry)] paths walked pale."""
    rng = np.random.default_rng(seed)
    light, dark, ox, ox_hi = "#937660", "#866a56", "#74463c", "#84524a"
    cv.rect(x, y, w, h, dark)
    bx0, bx1 = border
    yy, row = y, 0
    while yy < y + h:
        th = int(round(10 + 4 * (yy - y) / max(1, h)))
        th = min(th, y + h - yy)
        for col, xx in enumerate(range(x, x + w, tile)):
            x1 = min(x + w, xx + tile)
            edge = row == 0 or xx < bx0 + tile or x1 > bx1 - tile
            if edge:
                tone = ox if (col + row) % 2 == 0 else ox_hi
            else:
                tone = light if (col + row) % 2 == 0 else dark
                if rng.random() < 0.04:
                    tone = ["#9e8266", "#7a5e4c", ox][int(rng.integers(3))]
            tone = shade(tone, float(rng.choice([-0.03, -0.01, 0.0, 0.015])))
            cv.rect(xx, yy, x1 - xx, th, tone)
            cv.hline(xx, yy, x1 - xx, shade(tone, 0.07))
            cv.vline(x1 - 1, yy, th, shade(tone, -0.1))
            for _ in range((x1 - xx) * th // 18):
                cv.px(xx + int(rng.integers(0, x1 - xx)), yy + int(rng.integers(0, th)), shade(tone, float(rng.choice([-0.07, 0.06]))))
        yy += th
        row += 1
    # a pale inlay line inside the border band
    cv.hline(bx0 + tile, y + int(round(10)) , bx1 - bx0 - 2 * tile, "#b0957a")
    cv.vline(bx0 + tile, y + 10, h - 10, "#b0957a"); cv.vline(bx1 - tile - 1, y + 10, h - 10, "#b0957a")
    for (cx, cy, rx, ry) in wear:
        soft_ellipse(cv, cx, cy, rx, ry, "#e0c8a8", 0.07)
        soft_ellipse(cv, cx, cy, int(rx * 0.6), int(ry * 0.6), "#e0c8a8", 0.06)
    # scuff marks from heels and trolley wheels
    for _ in range(w * h // 900):
        sx, sy = x + int(rng.integers(0, w - 10)), y + int(rng.integers(0, h))
        cv.line(sx, sy, sx + int(rng.integers(3, 9)), sy + int(rng.integers(-1, 2)), C("#3a2a26", 0.45))


def floor_tape_box(cv, x, y, w, h, label=None, colour=None):
    """A rectangle of floor tape with a stencilled word inside (the sorting zones)."""
    c = colour or SAFETY[2]
    for (ax, ay, aw, ah) in [(x, y, w, 2), (x, y + h - 2, w, 2), (x, y, 2, h), (x + w - 2, y, 2, h)]:
        cv.rect(ax, ay, aw, ah, C(c, 0.75))
    for k in range(x + 6, x + w - 6, 9):  # tape seams
        cv.px(k, y, C("#fff0c4", 0.4))
    if label:
        text(cv, label, x + w // 2 - text_width(label) // 2, y + h // 2 - 5, C(c, 0.6))


def coat_hooks(cv, x0, x1, y, seed=0, items=True):
    """A wall rail of brass hooks with lost coats, scarves, a bag and an umbrella hanging."""
    rng = np.random.default_rng(seed)
    cv.rect(x0, y, x1 - x0, 5, PANEL[2]); cv.hline(x0, y, x1 - x0, PANEL[4]); cv.hline(x0, y + 4, x1 - x0, PANEL[1])
    x = x0 + 6
    while x < x1 - 8:
        cv.rect(x, y + 1, 2, 4, BRASS[3]); cv.px(x, y + 5, BRASS[2])
        if items and rng.random() < 0.92:
            kind = int(rng.choice([0, 0, 0, 0, 0, 1, 1, 2, 2, 3]))
            col = ITEM_COLOURS[int(rng.integers(len(ITEM_COLOURS)))]
            if kind == 0:   # coat
                L = int(rng.integers(26, 36))
                cv.poly([(x - 6, y + 6), (x + 7, y + 6), (x + 10, y + L), (x - 9, y + L)], OUT)
                cv.poly([(x - 5, y + 6), (x + 6, y + 6), (x + 9, y + L - 1), (x - 8, y + L - 1)], col)
                cv.poly([(x - 5, y + 6), (x, y + 6), (x - 2, y + L - 1), (x - 8, y + L - 1)], shade(col, 0.12))
                cv.line(x, y + 8, x, y + L - 2, shade(col, -0.3))
                cv.rect(x - 2, y + 6, 5, 3, shade(col, -0.2))
                cv.px(x + 1, y + 13, PAPER[3]); cv.px(x + 1, y + 19, PAPER[3])
                cv.rect(x - 6, y + 14, 3, 6, shade(col, -0.25)); cv.rect(x + 5, y + 14, 3, 6, shade(col, -0.25))
                x += int(rng.integers(11, 15))
            elif kind == 1:  # scarf
                cv.rect(x - 2, y + 5, 5, 24, OUT); cv.rect(x - 1, y + 6, 3, 22, col)
                for k in range(y + 9, y + 27, 4):
                    cv.hline(x - 1, k, 3, shade(col, 0.25))
                cv.vline(x - 1, y + 28, 2, col); cv.vline(x + 1, y + 28, 2, col)
                x += 9
            elif kind == 2:  # tote bag
                cv.line(x - 3, y + 6, x, y + 4, OUT); cv.line(x + 3, y + 6, x, y + 4, OUT)
                cv.rect(x - 6, y + 6, 13, 14, OUT); cv.rect(x - 5, y + 7, 11, 12, col); cv.hline(x - 5, y + 7, 11, shade(col, 0.2))
                cv.rect(x - 2, y + 11, 5, 4, shade(col, -0.25))
                x += 15
            else:  # umbrella hanging by its crook
                cv.line(x, y + 5, x + 2, y + 3, IRON[3])
                cv.poly([(x - 2, y + 7), (x + 3, y + 7), (x + 2, y + 30), (x - 1, y + 30)], OUT)
                cv.poly([(x - 1, y + 8), (x + 2, y + 8), (x + 1, y + 29), (x, y + 29)], col)
                cv.vline(x, y + 30, 3, IRON[2])
                x += 9
        else:
            x += 10
        # claim tag on a string
        if rng.random() < 0.5:
            cv.rect(x - 4, y + 18, 4, 5, KRAFT[4]); cv.px(x - 3, y + 19, KRAFT[1])


def claim_hatch(cv, cx, top, w=72, h=46, shutter=0.5, state=None):
    """The claim window: a hatch in the wall with its roller shutter half up, warm office light
    behind, a counter ledge with a brass bell and a CLAIM plate over it."""
    x0 = cx - w // 2
    cv.rect(x0 - 5, top - 5, w + 10, h + 9, PANEL[1])
    cv.rect(x0 - 4, top - 4, w + 8, h + 7, PANEL[3]); cv.hline(x0 - 4, top - 4, w + 8, PANEL[5])
    # office beyond: warm, a filing cabinet and a desk lamp
    for yy in range(top, top + h):
        t = (yy - top) / h
        cv.hline(x0, yy, w, mix(GLOW[2], GLOW[1], t))
    cv.rect(x0 + 6, top + 16, 16, h - 16, "#6a5a48"); cv.hline(x0 + 6, top + 16, 16, "#8a7a62")
    for dy in (top + 21, top + 30, top + 39):
        cv.hline(x0 + 8, dy, 12, "#4a3a30"); cv.rect(x0 + 12, dy - 3, 4, 1, "#c0c4cc")
    cv.rect(x0 + w - 24, top + 30, 20, 3, PANEL[2])
    cv.rect(x0 + w - 16, top + 22, 2, 8, BRASS[1]); cv.poly([(x0 + w - 20, top + 22), (x0 + w - 10, top + 22), (x0 + w - 13, top + 17), (x0 + w - 17, top + 17)], "#3e6663")
    # roller shutter (half up by default)
    sh = max(3, int(round(h * shutter)) - 4) if shutter < 1 else h
    cv.rect(x0, top, w, sh, "#8a8a98")
    for yy in range(top, top + sh, 3):
        cv.hline(x0, yy, w, "#a8a8b6")
        if yy + 2 < top + sh:
            cv.hline(x0, yy + 2, w, "#6a6a78")
    if shutter < 1:
        cv.rect(x0, top + sh, w, 2, "#4a4a58"); cv.rect(cx - 4, top + sh, 8, 3, "#3a3a48")
    else:
        cv.rect(x0, top + h - 2, w, 2, "#3a3a48")
        # padlocked, with a CLOSED card
        cv.rect(cx - 3, top + h - 7, 7, 6, OUT); cv.rect(cx - 2, top + h - 6, 5, 4, BRASS[3]); cv.px(cx, top + h - 5, OUT)
        cv.rect(cx - 2, top + h - 10, 5, 4, OUT); cv.rect(cx - 1, top + h - 9, 3, 2, "#8a8a98")
        cv.rect(cx - 20, top + 9, 40, 12, OUT); cv.rect(cx - 19, top + 10, 38, 10, PAPER[2])
        text(cv, "CLOSED", cx - 18, top + 10, "#7e3a30")
    # counter ledge
    cv.rect(x0 - 8, top + h, w + 16, 5, OUT)
    cv.rect(x0 - 7, top + h, w + 14, 3, PANEL[4]); cv.hline(x0 - 7, top + h, w + 14, PANEL[5])
    cv.ellipse(cx + 14, top + h - 6, 8, 6, BRASS[3]); cv.px(cx + 16, top + h - 5, BRASS[4]); cv.rect(cx + 17, top + h - 8, 2, 2, BRASS[2])
    cv.rect(cx + 13, top + h - 1, 10, 1, BRASS[1])
    if state == "peaceful":
        # a returned coat folded on the ledge with a green RETURNED slip
        cv.rect(cx - 24, top + h - 6, 22, 6, OUT); cv.rect(cx - 23, top + h - 5, 20, 5, "#425da6")
        cv.hline(cx - 23, top + h - 5, 20, "#6b81bf"); cv.vline(cx - 13, top + h - 5, 5, "#3e4a6e")
        cv.rect(cx - 6, top + h - 9, 12, 9, OUT); cv.rect(cx - 5, top + h - 8, 10, 8, PAPER[3])
        cv.line(cx - 3, top + h - 4, cx - 1, top + h - 2, "#4a6a4a"); cv.line(cx - 1, top + h - 2, cx + 3, top + h - 7, "#4a6a4a")
    elif shutter < 1:
        cv.rect(cx - 20, top + h - 3, 14, 3, PAPER[2]); cv.hline(cx - 18, top + h - 2, 9, "#7e3a30")
    # CLAIM plate
    label = "CLAIM"
    pw = text_width(label) + 8
    cv.rect(cx - pw // 2, top - 18, pw, 12, OUT)
    cv.rect(cx - pw // 2 + 1, top - 17, pw - 2, 10, "#7e3a30"); cv.hline(cx - pw // 2 + 1, top - 17, pw - 2, "#9a4a39")
    text(cv, label, cx - text_width(label) // 2, top - 18, PAPER[3])


def now_serving(cv, x, y, number="07"):
    """A NOW SERVING board with red seven-segment-ish digits (game font)."""
    cv.rect(x, y, 50, 24, OUT); cv.rect(x + 1, y + 1, 48, 22, "#2a2630")
    cv.rect(x + 2, y + 2, 46, 9, "#e6d6b1")
    text(cv, "SERVING", x + 4, y + 1, "#2a2630")
    cv.rect(x + 8, y + 12, 34, 10, "#140a10")
    text(cv, number, x + 19, y + 12, "#ff5a4a")
    return (x + 8, y + 12, 34, 10)


def found_board(cv, x, y, w, h, seed=0):
    """Corkboard of FOUND notices and photos of unclaimed things."""
    rng = np.random.default_rng(seed)
    corkboard(cv, x, y, w, h, seed=seed)
    text(cv, "FOUND", x + w // 2 - 15, y + 1, "#7e3a30")
    for k in range(3):  # instant photos of items
        px, py = x + 4 + k * (w - 8) // 3, y + h - 15
        cv.rect(px + 1, py + 1, 12, 13, C(SHADOW, 0.4)); cv.rect(px, py, 12, 13, PAPER[3])
        cv.rect(px + 1, py + 1, 10, 9, ["#5c897c", "#7e3a30", "#425da6"][k])
        cv.ellipse(px + 3, py + 3, 6, 5, ["#86b0a0", "#c84a3c", "#6b81bf"][k])
        cv.px(px + 6, py, "#c84a3c")


def worn_mat(cv, x, y, w, h, label=None):
    cv.rect(x, y, w, h, "#3a2e2c"); cv.rect(x + 1, y + 1, w - 2, h - 2, "#4e3e38")
    for yy in range(y + 2, y + h - 2, 2):
        cv.hline(x + 2, yy, w - 4, "#463834")
    if label:
        text(cv, label, x + w // 2 - text_width(label) // 2, y + h // 2 - 5, "#7a6458")


# ---------------------------------------------------------------------------------------------
# U07 props: lost things and the furniture that keeps them
# ---------------------------------------------------------------------------------------------

def lost_item(cv, kind, cx, by, rng, maxw=18):
    """One small unclaimed thing standing on a shelf: bottom-centre at (cx, by)."""
    col = ITEM_COLOURS[int(rng.integers(len(ITEM_COLOURS)))]
    if kind == "sweater":
        for k in range(2):
            c = col if k == 0 else ITEM_COLOURS[int(rng.integers(len(ITEM_COLOURS)))]
            y = by - 5 * (k + 1)
            cv.rect(cx - 7, y, 14, 5, OUT); cv.rect(cx - 6, y + 1, 12, 3, c); cv.hline(cx - 6, y + 1, 12, shade(c, 0.2))
            cv.vline(cx - 2, y + 1, 3, shade(c, -0.25))
    elif kind == "helmet":
        cv.ellipse(cx - 7, by - 9, 14, 14, OUT); cv.ellipse(cx - 6, by - 8, 12, 12, col)
        cv.rect(cx - 7, by - 2, 14, 3, C("#000000", 0)); cv.a[by - 2:by + 6, cx - 8:cx + 8] = 0
        cv.rect(cx - 7, by - 2, 14, 2, OUT)
        for k in (-3, 0, 3):
            cv.vline(cx + k, by - 7, 3, shade(col, -0.35))
        cv.px(cx - 3, by - 6, shade(col, 0.4))
    elif kind == "shoes":
        for k, dx in enumerate((-6, 1)):
            cv.rect(cx + dx, by - 5, 6, 5, OUT); cv.rect(cx + dx + 1, by - 4, 4, 3, col); cv.hline(cx + dx + 1, by - 2, 5, PAPER[3])
            cv.rect(cx + dx + 1, by - 6, 3, 2, OUT)
    elif kind == "books":
        x = cx - 7
        for k in range(4):
            h = int(rng.integers(8, 13)); c = ITEM_COLOURS[int(rng.integers(len(ITEM_COLOURS)))]
            cv.rect(x, by - h, 3, h, OUT); cv.rect(x + 1, by - h + 1, 2, h - 1, c); cv.px(x + 1, by - h + 3, PAPER[3])
            x += 3
        cv.poly([(x, by), (x + 3, by - 10), (x + 6, by - 10), (x + 3, by)], OUT)
        cv.line(x + 1, by - 1, x + 4, by - 9, ITEM_COLOURS[int(rng.integers(len(ITEM_COLOURS)))])
    elif kind == "teddy":
        b = "#8a5a3a"
        cv.ellipse(cx - 5, by - 9, 10, 9, OUT); cv.ellipse(cx - 4, by - 8, 8, 8, b)
        cv.ellipse(cx - 4, by - 15, 8, 7, OUT); cv.ellipse(cx - 3, by - 14, 6, 6, b)
        cv.rect(cx - 4, by - 16, 2, 2, b); cv.rect(cx + 2, by - 16, 2, 2, b)
        cv.px(cx - 2, by - 12, OUT); cv.px(cx + 1, by - 12, OUT); cv.px(cx, by - 11, "#c8a888")
        cv.rect(cx - 2, by - 7, 4, 3, "#c8a888")
    elif kind == "lunchbox":
        cv.rect(cx - 7, by - 9, 14, 9, OUT); cv.rect(cx - 6, by - 8, 12, 7, col); cv.hline(cx - 6, by - 8, 12, shade(col, 0.25))
        cv.rect(cx - 3, by - 12, 6, 3, OUT); cv.rect(cx - 2, by - 11, 4, 1, C("#000000", 0))
        cv.a[by - 11, cx - 2:cx + 2] = 0
        cv.rect(cx - 1, by - 6, 3, 2, PAPER[3])
    elif kind == "glove":
        g = col
        cv.rect(cx - 4, by - 4, 8, 4, OUT); cv.rect(cx - 3, by - 3, 6, 2, PAPER[2])
        for k in range(4):
            cv.rect(cx - 4 + k * 2, by - 11 + (1 if k in (0, 3) else 0), 2, 7, OUT); cv.vline(cx - 3 + k * 2 - 1 + 1, by - 10 + (1 if k in (0, 3) else 0), 6, g)
        cv.rect(cx - 3, by - 6, 6, 2, g)
        cv.line(cx + 4, by - 5, cx + 6, by - 8, g)
    elif kind == "hat":
        cv.ellipse(cx - 6, by - 9, 12, 12, OUT); cv.ellipse(cx - 5, by - 8, 10, 10, col)
        cv.a[by:by + 6, cx - 7:cx + 7] = 0
        cv.rect(cx - 6, by - 3, 12, 3, OUT); cv.rect(cx - 5, by - 3, 10, 2, shade(col, 0.2))
        cv.ellipse(cx - 2, by - 12, 4, 4, PAPER[3])
    elif kind == "bottle":
        cv.rect(cx - 2, by - 12, 5, 12, OUT); cv.rect(cx - 1, by - 11, 3, 11, col); cv.vline(cx - 1, by - 10, 9, shade(col, 0.3))
        cv.rect(cx - 1, by - 14, 3, 2, IRON[3])
    elif kind == "headphones":
        for a in np.linspace(np.pi, 2 * np.pi, 14):
            cv.px(int(round(cx + np.cos(a) * 6)), int(round(by - 5 + np.sin(a) * 7)), OUT)
        cv.rect(cx - 8, by - 6, 4, 6, OUT); cv.rect(cx + 4, by - 6, 4, 6, OUT)
        cv.rect(cx - 7, by - 5, 2, 4, col); cv.rect(cx + 5, by - 5, 2, 4, col)
    elif kind == "ball":
        cv.ellipse(cx - 5, by - 10, 10, 10, OUT); cv.ellipse(cx - 4, by - 9, 8, 8, "#c47a2c")
        cv.vline(cx, by - 9, 8, OUT); cv.line(cx - 3, by - 8, cx - 3, by - 2, C(OUT, 0.6)); cv.px(cx - 2, by - 8, "#e8a45c")
    elif kind == "mug":
        cv.rect(cx - 3, by - 7, 6, 7, OUT); cv.rect(cx - 2, by - 6, 4, 6, col); cv.px(cx + 3, by - 4, OUT); cv.px(cx + 3, by - 3, OUT)
    elif kind == "box":
        cv.rect(cx - 8, by - 10, 16, 10, OUT); cv.rect(cx - 7, by - 9, 14, 9, KRAFT[2]); cv.hline(cx - 7, by - 9, 14, KRAFT[3])
        cv.vline(cx, by - 9, 3, KRAFT[1])
        q = [(0, 1), (1, 0), (2, 1), (2, 2), (1, 3), (1, 5)]
        for (dx, dy) in q:
            cv.px(cx - 4 + dx, by - 7 + dy, "#7e3a30")
    elif kind == "umbrella":
        cv.line(cx - 5, by - 1, cx + 3, by - 15, OUT); cv.line(cx - 4, by - 1, cx + 4, by - 15, col)
        cv.line(cx - 3, by - 1, cx + 4, by - 13, shade(col, -0.3))
        cv.line(cx + 3, by - 15, cx + 5, by - 17, IRON[3]); cv.px(cx + 6, by - 16, IRON[3])
    else:  # scarf folded
        cv.rect(cx - 6, by - 4, 12, 4, OUT); cv.rect(cx - 5, by - 3, 10, 2, col)
        cv.vline(cx + 4, by - 1, 3, col); cv.vline(cx + 2, by - 1, 2, col)


ITEM_KINDS = ["sweater", "helmet", "shoes", "books", "teddy", "lunchbox", "glove", "hat", "bottle",
              "headphones", "ball", "mug", "box", "umbrella", "scarf"]


def claim_tag(cv, x, y, number=None):
    """A small kraft claim tag on a string, (x, y) = string top."""
    cv.px(x, y, PAPER[2]); cv.px(x, y + 1, PAPER[2])
    cv.rect(x - 2, y + 2, 5, 4, KRAFT[4]); cv.px(x - 2, y + 2, KRAFT[2]); cv.px(x, y + 3, KRAFT[1])
    cv.px(x - 1, y + 4, "#7e3a30")


def cubby_shelf(width=84, height=116, cols=3, rows=3, bottom_open=True, seed=0):
    """A tall wooden pigeonhole unit packed with unclaimed things, a numbered tag on every hole.
    The lowest compartment (board at -22 from the anchor) is left clear: the game draws the two
    return labels there and its PASS ON / SORT LATER states on the kick plate below."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3)
    top = base - height + 12
    # things piled on top
    x = ox + 6
    while x < ox + width - 12:
        kind = ["box", "sweater", "box", "lunchbox", "hat"][int(rng.integers(0, 5))]
        lost_item(cv, kind, x + 8, top, rng)
        x += int(rng.integers(14, 22))
    # carcass
    cv.rect(ox, top, width, base - top, OUT)
    cv.rect(ox + 1, top + 1, width - 2, base - top - 2, PANEL[3])
    cv.hline(ox + 1, top + 1, width - 2, PANEL[5]); cv.vline(ox + 1, top + 1, base - top - 2, PANEL[4])
    cv.rect(ox - 1, top - 2, width + 2, 4, OUT); cv.rect(ox, top - 1, width, 2, PANEL[4]); cv.hline(ox, top - 1, width, PANEL[5])
    inner_x0, inner_x1 = ox + 4, ox + width - 4
    holes_top, holes_bot = top + 4, base - 44 if bottom_open else base - 22
    cw = (inner_x1 - inner_x0) // cols
    rh = (holes_bot - holes_top) // rows
    number = int(rng.integers(10, 60))
    for r in range(rows):
        for c in range(cols):
            hx, hy = inner_x0 + c * cw, holes_top + r * rh
            cv.rect(hx, hy, cw - 2, rh - 3, PANEL[0])
            cv.rect(hx, hy, cw - 2, 2, "#1a0e10")
            cv.vline(hx + cw - 3, hy, rh - 3, PANEL[1])
            kind = ITEM_KINDS[int(rng.integers(len(ITEM_KINDS)))]
            lost_item(cv, kind, hx + (cw - 2) // 2 + int(rng.integers(-2, 3)), hy + rh - 3, rng)
            # shelf board edge and its tag
            cv.rect(hx - 1, hy + rh - 3, cw, 3, PANEL[4]); cv.hline(hx - 1, hy + rh - 3, cw, PANEL[5])
            claim_tag(cv, hx + cw - 7, hy + rh - 2)
            number += 1
    if bottom_open:
        # the returns compartment: empty, dark, board at -22
        by = base - 22
        cv.rect(inner_x0, holes_bot, inner_x1 - inner_x0, by - holes_bot, PANEL[0])
        cv.rect(inner_x0, holes_bot, inner_x1 - inner_x0, 2, "#1a0e10")
        cv.rect(inner_x0 - 1, by, inner_x1 - inner_x0 + 2, 3, PANEL[4]); cv.hline(inner_x0 - 1, by, inner_x1 - inner_x0 + 2, PANEL[5])
        # a small paper RETURNS slip pinned at the top centre of the compartment (clear of the labels
        # the game draws at x -32..0 and 15..28)
        cx0 = ox + width // 2
        cv.rect(cx0 + 1, holes_bot + 1, 11, 4, PAPER[2]); cv.hline(cx0 + 2, holes_bot + 2, 8, "#7e3a30")
        cv.px(cx0 + 6, holes_bot + 1, "#c84a3c")
    # kick plate
    cv.rect(ox + 1, base - 19, width - 2, 17, PANEL[1]); cv.hline(ox + 1, base - 19, width - 2, PANEL[2])
    cv.rect(ox + 1, base - 3, width - 2, 2, PANEL[0])
    return cv, ox + width // 2, base


def steel_shelving(width=78, height=111, seed=0):
    """Grey steel shelving: perforated uprights, four shelves of month-labelled boxes, umbrellas
    and a racket poking out, a crate of single gloves at the bottom."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3)
    top = base - height + 8
    steel = ["#2a2a36", "#4a4a5a", "#6a6a7c", "#8e8ea0", "#b0b0c0"]
    levels = [top + 2, top + 28, top + 54, top + 80, base - 4]
    months = ["SEP", "OCT", "MAY", "JAN", "APR", "???"]
    # things on the top shelf surface first (they sit above the frame)
    lost_item(cv, "umbrella", ox + 14, top + 2, rng); lost_item(cv, "box", ox + width - 18, top + 2, rng)
    # back uprights
    for ux in (ox + 3, ox + width - 6):
        cv.rect(ux, top, 3, base - top, steel[0])
    for li, ly in enumerate(levels[1:]):
        prev = levels[li]
        # contents between prev and ly
        x = ox + 6
        while x < ox + width - 10:
            bw = int(rng.integers(18, 26))
            bw = min(bw, ox + width - 6 - x)
            if bw < 10:
                break
            bh = min(ly - prev - 6, int(rng.integers(14, 20)))
            if li == 3:
                # crate of single gloves
                cv.rect(x, ly - bh, bw, bh, OUT); cv.rect(x + 1, ly - bh + 1, bw - 2, bh - 1, "#5c4a3a")
                for k in range(x + 2, x + bw - 4, 5):
                    lost_item(cv, "glove", k + 2, ly - bh + 6, rng)
                for k in range(ly - bh + 6, ly, 3):
                    cv.hline(x + 1, k, bw - 2, "#4a3a2e")
            else:
                cv.rect(x, ly - bh, bw, bh, OUT)
                cv.rect(x + 1, ly - bh + 1, bw - 2, bh - 1, KRAFT[2]); cv.hline(x + 1, ly - bh + 1, bw - 2, KRAFT[3])
                cv.vline(x + bw - 2, ly - bh + 1, bh - 1, KRAFT[1])
                m = months[int(rng.integers(len(months)))]
                if bw >= 20:
                    cv.rect(x + bw // 2 - 10, ly - bh + 4, 20, 9, PAPER[3])
                    text(cv, m, x + bw // 2 - 9, ly - bh + 3, "#3a2a26")
                if rng.random() < 0.5:  # something poking out of the box
                    lost_item(cv, ["scarf", "umbrella", "bottle"][int(rng.integers(3))], x + bw // 2 + 3, ly - bh + 1, rng)
            x += bw + 1
        # shelf beam
        cv.rect(ox + 1, ly, width - 2, 3, OUT); cv.rect(ox + 2, ly, width - 4, 2, steel[3]); cv.hline(ox + 2, ly, width - 4, steel[4])
    cv.rect(ox + 1, levels[0], width - 2, 3, OUT); cv.rect(ox + 2, levels[0], width - 4, 2, steel[3]); cv.hline(ox + 2, levels[0], width - 4, steel[4])
    # front uprights, perforated
    for ux in (ox, ox + width - 4):
        cv.rect(ux, top - 1, 4, base - top + 1, OUT); cv.rect(ux + 1, top, 2, base - top, steel[2]); cv.vline(ux + 1, top, base - top, steel[3])
        for k in range(top + 3, base - 2, 4):
            cv.px(ux + 2, k, steel[0])
        cv.rect(ux - 1, base - 2, 6, 2, steel[1])
    # a tag hanging off the top shelf
    claim_tag(cv, ox + width - 12, levels[1] + 3)
    return cv, ox + width // 2, base


def low_cubbies(width=114, height=62, seed=0):
    """A long low pigeonhole bench of bags and shoes, folded clothes and a GLOVES box on top."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3)
    top = base - height + 14
    # on top
    lost_item(cv, "sweater", ox + 14, top, rng)
    gx = ox + 30
    cv.rect(gx, top - 12, 34, 12, OUT); cv.rect(gx + 1, top - 11, 32, 11, KRAFT[2]); cv.hline(gx + 1, top - 11, 32, KRAFT[3])
    text(cv, "GLOVES", gx + 1, top - 12, "#3a2a26")
    lost_item(cv, "glove", gx + 30, top - 10, rng)
    lost_item(cv, "teddy", ox + 76, top, rng)
    lost_item(cv, "books", ox + width - 18, top, rng)
    # carcass
    cv.rect(ox, top, width, base - top, OUT)
    cv.rect(ox + 1, top + 1, width - 2, base - top - 2, PANEL[3])
    cv.rect(ox - 1, top - 2, width + 2, 4, OUT); cv.rect(ox, top - 1, width, 2, PANEL[4]); cv.hline(ox, top - 1, width, PANEL[5])
    cols, rows = 5, 2
    ix0, ix1 = ox + 3, ox + width - 3
    cw = (ix1 - ix0) // cols
    rh = (base - 6 - top - 3) // rows
    for r in range(rows):
        for c in range(cols):
            hx, hy = ix0 + c * cw, top + 3 + r * rh
            cv.rect(hx, hy, cw - 2, rh - 3, PANEL[0]); cv.rect(hx, hy, cw - 2, 2, "#1a0e10")
            lost_item(cv, ["shoes", "lunchbox", "helmet", "bottle", "hat", "mug", "ball", "headphones"][int(rng.integers(8))], hx + (cw - 2) // 2, hy + rh - 3, rng)
            cv.rect(hx - 1, hy + rh - 3, cw, 3, PANEL[4]); cv.hline(hx - 1, hy + rh - 3, cw, PANEL[5])
            claim_tag(cv, hx + cw - 6, hy + rh - 2)
    cv.rect(ox + 1, base - 5, width - 2, 4, PANEL[1])
    return cv, ox + width // 2, base


def bin_counter(width=150, height=48, labels=("HATS", "KEYS", "BOOKS", "ODD"), seed=0):
    """A long low counter of labelled bins against the back wall; odds and ends on its top."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 2)
    top = base - height + 10
    # on top: a desk radio, a cash box, a stack of claim forms
    rx = ox + 10
    cv.rect(rx, top - 9, 18, 9, OUT); cv.rect(rx + 1, top - 8, 16, 8, "#7a5a3a"); cv.rect(rx + 2, top - 7, 8, 6, "#3a3040")
    for k in range(3):
        cv.vline(rx + 3 + k * 2, top - 6, 4, "#5a4a50")
    cv.ellipse(rx + 11, top - 6, 5, 5, BRASS[3]); cv.vline(rx + 15, top - 15, 6, IRON[3])
    cv.rect(ox + 60, top - 7, 16, 7, OUT); cv.rect(ox + 61, top - 6, 14, 6, "#2c4a4c"); cv.hline(ox + 61, top - 6, 14, "#3e6663"); cv.rect(ox + 67, top - 4, 3, 2, BRASS[3])
    for k in range(3):
        cv.rect(ox + 92 + k, top - 3 - k * 2, 18, 2, PAPER[3 - (k % 2)])
    cv.hline(ox + 94, top - 6, 10, "#7e3a30")
    lost_item(cv, "hat", ox + width - 20, top, rng)
    lost_item(cv, "mug", ox + width - 34, top, rng)
    # counter carcass
    cv.rect(ox, top, width, base - top, OUT)
    cv.rect(ox + 1, top + 1, width - 2, base - top - 2, PANEL[2])
    cv.rect(ox - 1, top - 2, width + 2, 5, OUT); cv.rect(ox, top - 1, width, 3, PANEL[4]); cv.hline(ox, top - 1, width, PANEL[5])
    n = len(labels)
    bw = (width - 8) // n
    for i, lab in enumerate(labels):
        bx = ox + 4 + i * bw
        by0, by1 = top + 4, base - 5
        # plastic tub, things poking out of it
        tub = ["#2c4a6a", "#3a5a7a", "#4a6a8a"] if i % 2 == 0 else ["#5a3a3a", "#7a4a42", "#8a5a4e"]
        for k in range(2):
            kind = {"HATS": "hat", "KEYS": "mug", "BOOKS": "books", "ODD": "box"}.get(lab, "scarf")
            if kind == "mug":
                cv.ellipse(bx + 6 + k * 10, by0 - 1, 5, 5, BRASS[3]); cv.vline(bx + 9 + k * 10, by0 + 1, 3, "#c0c4cc")
            else:
                lost_item(cv, kind, bx + 9 + k * 13, by0 + 3, rng)
        cv.rect(bx, by0, bw - 3, by1 - by0, OUT)
        cv.rect(bx + 1, by0 + 1, bw - 5, by1 - by0 - 2, tub[1]); cv.hline(bx + 1, by0 + 1, bw - 5, tub[2])
        cv.rect(bx + 1, by0 + 1, bw - 5, 2, tub[2])
        lw = text_width(lab) + 4
        cv.rect(bx + (bw - 3) // 2 - lw // 2, by0 + 8, lw, 10, PAPER[2])
        text(cv, lab, bx + (bw - 3) // 2 - text_width(lab) // 2, by0 + 8, "#3a2a26")
    cv.rect(ox + 1, base - 4, width - 2, 3, PANEL[0])
    return cv, ox + width // 2, base


def sorting_table(width=132, height=53, seed=0):
    """The sorting table: three wooden trays of half-sorted things, a heap of scarves and gloves,
    a tagging gun, a spool of numbered tickets, baskets underneath."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 6, height + 8, seed=seed)
    ox, base = 3, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3)
    top = base - 26
    # legs and baskets underneath
    for lx in (ox + 4, ox + width - 8):
        cv.rect(lx, top + 3, 4, base - top - 3, OUT); cv.vline(lx + 1, top + 4, base - top - 5, IRON[3])
    for (bx, bw) in [(ox + 16, 30), (ox + width - 50, 34)]:
        cv.rect(bx, base - 14, bw, 13, OUT); cv.rect(bx + 1, base - 13, bw - 2, 11, KRAFT[2])
        for k in range(bx + 2, bx + bw - 2, 3):
            cv.vline(k, base - 12, 9, KRAFT[1])
        cv.hline(bx + 1, base - 13, bw - 2, KRAFT[4])
        for k in range(2):
            lost_item(cv, ["scarf", "shoes", "glove", "hat"][int(rng.integers(4))], bx + 8 + k * 14, base - 13, rng)
    # table top
    cv.rect(ox - 1, top - 1, width + 2, 7, OUT)
    cv.rect(ox, top, width, 5, PANEL[4]); cv.hline(ox, top, width, PANEL[5]); cv.hline(ox, top + 4, width, PANEL[2])
    for k in range(5):
        cv.hline(ox + 8 + k * 25, top + 2, 9, PANEL[3])
    # trays with small things
    for i, tx in enumerate((ox + 6, ox + 44, ox + 82)):
        cv.rect(tx, top - 6, 34, 6, OUT); cv.rect(tx + 1, top - 5, 32, 5, PANEL[3]); cv.hline(tx + 1, top - 5, 32, PANEL[5])
        for k in range(3):
            lost_item(cv, ["mug", "bottle", "glove", "hat", "headphones", "books", "box"][int(rng.integers(7))], tx + 7 + k * 10, top - 5, rng)
        claim_tag(cv, tx + 30, top - 3)
    # a heap of scarves spilling over the right end
    hx = ox + width - 14
    for k in range(4):
        c = ITEM_COLOURS[int(rng.integers(len(ITEM_COLOURS)))]
        cv.ellipse(hx - 8 + k * 3, top - 9 + k * 2, 13, 7, OUT); cv.ellipse(hx - 7 + k * 3, top - 8 + k * 2, 11, 5, c)
        cv.hline(hx - 5 + k * 3, top - 7 + k * 2, 6, shade(c, 0.25))
    cv.rect(hx + 4, top, 3, 9, ITEM_COLOURS[2]); cv.rect(hx + 8, top, 2, 6, ITEM_COLOURS[0])
    # spool of tickets and a tagging gun at the left
    cv.ellipse(ox + 2, top - 13, 8, 8, OUT); cv.ellipse(ox + 3, top - 12, 6, 6, "#e06a5a"); cv.px(ox + 5, top - 10, OUT)
    cv.rect(ox + 6, top - 9, 6, 3, PAPER[3])
    return cv, ox + width // 2, base


def ticket_spool(width=42, height=68, seed=0):
    """A take-a-number dispenser on a pedestal: red housing with the paper spool at its axle
    (-44..-35 from the anchor, where the game draws a crack when it breaks), one ticket hanging,
    a TICKETS plate on top and a wide base where loose tickets get bundled."""
    cv = Canvas(width + 8, height + 6, seed=seed)
    ox, base = 4, height + 3
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2, 3)
    # a low wooden plinth (its top at -13..-10 is where loose tickets get bundled)
    px0, px1 = cx - 19, cx + 22
    cv.rect(px0, base - 14, px1 - px0, 14, OUT)
    cv.rect(px0 + 1, base - 13, px1 - px0 - 2, 4, PANEL[4]); cv.hline(px0 + 1, base - 13, px1 - px0 - 2, PANEL[5])
    cv.rect(px0 + 1, base - 9, px1 - px0 - 2, 8, PANEL[2]); cv.hline(px0 + 1, base - 9, px1 - px0 - 2, PANEL[1])
    for k in (px0 + 4, px1 - 6):
        cv.rect(k, base - 7, 2, 4, PANEL[3])
    cv.rect(px0 + 13, base - 7, 14, 4, PANEL[1]); cv.hline(px0 + 14, base - 6, 12, PAPER[1])
    # loose tickets left on the plinth top
    for (tx, ty) in [(px0 + 4, base - 12), (px1 - 9, base - 11)]:
        cv.rect(tx, ty, 5, 2, PAPER[3]); cv.px(tx + 1, ty, "#c84a3c")
    # pole
    cv.rect(cx - 2, base - 36, 4, 23, OUT); cv.vline(cx - 1, base - 35, 22, "#c0c4cc"); cv.vline(cx, base - 35, 22, IRON[3])
    # housing (red, rounded), axle hub where the spool turns
    hy = base - 56
    cv.rect(cx - 12, hy, 24, 22, OUT)
    cv.rect(cx - 11, hy + 1, 22, 20, "#a83c32"); cv.hline(cx - 11, hy + 1, 22, "#e06a5a"); cv.vline(cx - 11, hy + 1, 20, "#c84a3c")
    cv.vline(cx + 10, hy + 1, 20, "#7e2a26")
    cv.ellipse(cx - 7, hy + 6, 14, 14, "#7e2a26"); cv.ellipse(cx - 5, hy + 8, 10, 10, PAPER[2]); cv.ellipse(cx - 2, hy + 11, 4, 4, IRON[3])
    for a in np.linspace(0, 2 * np.pi, 9)[:-1]:
        cv.px(int(round(cx + np.cos(a) * 4)), int(round(hy + 13 + np.sin(a) * 4)), PAPER[1])
    # the one ticket it printed, hanging from the slot
    cv.rect(cx - 6, hy + 21, 12, 2, OUT)
    cv.poly([(cx - 4, hy + 22), (cx + 4, hy + 22), (cx + 5, hy + 33), (cx - 3, hy + 33)], PAPER[3])
    cv.hline(cx - 2, hy + 25, 5, "#c84a3c"); cv.hline(cx - 2, hy + 28, 4, "#5a4a44")
    # TICKETS plate on top
    label = "TICKETS"
    pw = text_width(label) + 4
    cv.rect(cx - pw // 2, hy - 12, pw, 12, OUT); cv.rect(cx - pw // 2 + 1, hy - 11, pw - 2, 10, PAPER[2])
    text(cv, label, cx - text_width(label) // 2, hy - 12, "#7e2a26")
    cv.rect(cx - 1, hy - 1, 2, 1, OUT)
    return cv, cx, base


def fringed_lamp(height=65, seed=0):
    """A mismatched floor lamp that came in as lost property itself: brass pole, a pleated
    shade with a fringe (bulb ~5 px below the top), and its own claim tag."""
    w = 26
    cv = Canvas(w, height + 4, seed=seed)
    cx, base = w // 2, height + 1
    ground_shadow(cv, cx, base, 8, 2)
    cv.ellipse(cx - 6, base - 4, 13, 5, OUT); cv.ellipse(cx - 5, base - 4, 11, 3, BRASS[2]); cv.hline(cx - 4, base - 4, 8, BRASS[4])
    cv.rect(cx - 1, 18, 3, base - 21, OUT); cv.vline(cx, 18, base - 21, BRASS[3]); cv.vline(cx + 1, 18, base - 21, BRASS[1])
    for ky in (30, 44):
        cv.rect(cx - 2, ky, 5, 2, BRASS[2]); cv.hline(cx - 2, ky, 5, BRASS[4])
    # shade
    cv.poly([(cx - 6, 1), (cx + 6, 1), (cx + 11, 15), (cx - 11, 15)], OUT)
    cv.poly([(cx - 5, 2), (cx + 5, 2), (cx + 10, 14), (cx - 10, 14)], "#e9a84a")
    cv.poly([(cx - 4, 3), (cx + 1, 3), (cx + 2, 13), (cx - 7, 13)], "#f6cd78")
    for k in range(-8, 9, 3):
        cv.line(cx + k // 2, 3, cx + k, 13, C("#c47a2c", 0.6))
    for k in range(cx - 10, cx + 11, 2):
        cv.vline(k, 15, 2 + (k % 3 == 0), "#c47a2c")
    cv.rect(cx - 2, 15, 5, 2, "#fff0c4")
    # its claim tag
    cv.line(cx + 2, 24, cx + 5, 27, PAPER[2]); cv.rect(cx + 4, 27, 5, 4, KRAFT[4]); cv.px(cx + 6, 29, "#7e3a30")
    return cv, cx, base


def waiting_seats(width=82, height=34, seed=0):
    """Three joined waiting-room seats on a steel beam; someone's umbrella left on one."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 1
    ground_shadow(cv, ox + width // 2, base, width // 2, 2)
    seats = [("#9a5a3a", "#b8784e", "#6e3a26"), ("#2c5a5a", "#3e7a74", "#1e3a3a"), ("#9a5a3a", "#b8784e", "#6e3a26")]
    sw = width // 3
    # beam and legs
    cv.rect(ox, base - 13, width, 3, OUT); cv.hline(ox + 1, base - 12, width - 2, IRON[3])
    for lx in (ox + 6, ox + width - 9):
        cv.rect(lx, base - 12, 4, 12, OUT); cv.vline(lx + 1, base - 11, 10, IRON[3])
        cv.rect(lx - 3, base - 2, 10, 2, IRON[1])
    for i, (c, hi, lo) in enumerate(seats):
        sx = ox + i * sw + 1
        # back
        cv.rect(sx + 1, base - height, sw - 4, 17, OUT)
        cv.rect(sx + 2, base - height + 1, sw - 6, 15, c); cv.hline(sx + 2, base - height + 1, sw - 6, hi)
        cv.vline(sx + 2, base - height + 1, 15, hi); cv.hline(sx + 3, base - height + 12, sw - 8, lo)
        # seat
        cv.rect(sx, base - 19, sw - 2, 7, OUT)
        cv.rect(sx + 1, base - 18, sw - 4, 4, hi); cv.hline(sx + 1, base - 15, sw - 4, c); cv.hline(sx + 1, base - 14, sw - 4, lo)
    # the forgotten umbrella on the left seat
    cv.line(ox + 6, base - 20, ox + 20, base - 26, OUT); cv.line(ox + 6, base - 21, ox + 20, base - 27, "#425da6")
    cv.line(ox + 20, base - 27, ox + 23, base - 25, IRON[3])
    return cv, ox + width // 2, base


# ---------------------------------------------------------------------------------------------
# U07 wall furniture
# ---------------------------------------------------------------------------------------------

def gooseneck(cv, x, y, reach=12, shade_col="#3e6663"):
    """A wall-mounted brass shelf light: back plate at (x, y), an arm curving out and down to a
    green enamel shade; returns the bulb point."""
    cv.rect(x - 2, y - 3, 5, 7, OUT); cv.rect(x - 1, y - 2, 3, 5, BRASS[2]); cv.px(x, y - 1, BRASS[4])
    pts = [(x + 1, y), (x + reach // 3, y - 4), (x + 2 * reach // 3, y - 5), (x + reach, y - 2)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        cv.line(ax, ay - 1, bx, by - 1, OUT); cv.line(ax, ay, bx, by, BRASS[3])
    sx, sy = x + reach, y - 1
    cv.poly([(sx - 3, sy), (sx + 3, sy), (sx + 6, sy + 6), (sx - 6, sy + 6)], OUT)
    cv.poly([(sx - 2, sy + 1), (sx + 2, sy + 1), (sx + 5, sy + 5), (sx - 5, sy + 5)], shade_col)
    cv.hline(sx - 1, sy + 1, 3, shade(shade_col, 0.3))
    cv.rect(sx - 4, sy + 6, 9, 1, "#fff0c4"); cv.rect(sx - 2, sy + 7, 5, 1, "#f6cf7a")
    return (sx, sy + 7)


def light_cone(cv, x, y, w0, w1, length, colour="#f6cf7a", alpha=0.06):
    """A faint stepped wedge of lamplight falling down the wall from a shade at (x, y)."""
    for i, f in enumerate((1.0, 0.66, 0.36)):
        a = alpha * (i + 1) / 2
        ww0, ww1 = max(1, int(w0 * f)), int(w1 * f)
        cv.poly([(x - ww0, y), (x + ww0, y), (x + ww1, y + length), (x - ww1, y + length)], C(colour, a))


def key_board(cv, x, y, w, h, seed=0):
    """A board of brass hooks with lost keys hanging in rows, kraft tags on some; returns the key
    points that catch the light."""
    rng = np.random.default_rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT); cv.rect(x - 1, y - 1, w + 2, h + 2, PANEL[4]); cv.hline(x - 1, y - 1, w + 2, PANEL[5])
    cv.rect(x, y, w, h, PANEL[2])
    for yy in range(y + 2, y + h, 3):
        cv.hline(x, yy, w, PANEL[1] if (yy // 3) % 2 else PANEL[2])
    text(cv, "KEYS", x + w // 2 - 12, y + 1, PAPER[2])
    glints = []
    for r, ry in enumerate(range(y + 14, y + h - 8, 13)):
        cv.hline(x + 2, ry - 1, w - 4, PANEL[0])
        for kx in range(x + 5 + (r % 2) * 3, x + w - 5, 7):
            cv.rect(kx, ry, 1, 2, BRASS[2])
            if rng.random() < 0.8:
                c = BRASS[3] if rng.random() < 0.6 else "#c0c4cc"
                lo = BRASS[1] if c == BRASS[3] else "#6a6a7c"
                cv.rect(kx - 1, ry + 2, 3, 3, c); cv.px(kx, ry + 3, PANEL[1])
                cv.vline(kx, ry + 5, 4, c); cv.px(kx + 1, ry + 7, lo); cv.px(kx + 1, ry + 8, c)
                if rng.random() < 0.35:
                    cv.rect(kx + 1, ry + 4, 3, 4, KRAFT[4]); cv.px(kx + 2, ry + 5, "#7e3a30")
                if rng.random() < 0.4:
                    glints.append((kx - 1, ry + 2))
    return glints


def process_placard(cv, x, y, w=78, h=44):
    """Enamel placard of the room's three verbs: 1 SORT / 2 RETURN / 3 RELEASE."""
    cv.rect(x + 1, y + 1, w, h, C(SHADOW, 0.5))
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, PAPER[2]); cv.hline(x + 1, y + 1, w - 2, PAPER[3])
    cv.rect(x + 2, y + 2, w - 4, h - 4, PAPER[2])
    for i, (word, c) in enumerate([("SORT", "#425da6"), ("RETURN", "#7e3a30"), ("RELEASE", "#4a6a4a")]):
        ly = y + 3 + i * 13
        cv.rect(x + 4, ly + 2, 9, 9, c)
        text(cv, str(i + 1), x + 6, ly + 1, PAPER[3])
        text(cv, word, x + 16, ly + 1, "#3a2a26")
        if i < 2:
            cv.hline(x + 4, ly + 12, w - 8, PAPER[1])
    for (bx, by) in [(x + 2, y + 2), (x + w - 3, y + 2), (x + 2, y + h - 3), (x + w - 3, y + h - 3)]:
        cv.px(bx, by, IRON[2])


def umbrella_stand(cv, cx, base, seed=0):
    """A tall tin stand of forgotten umbrellas against the wall (base on the wall line)."""
    rng = np.random.default_rng(seed)
    cols = ["#425da6", "#7e3a30", "#2c2a38", "#5c897c", "#d9a441", "#8a4a6a"]
    for k in range(6):
        ux = cx - 7 + k * 3 + int(rng.integers(-1, 2))
        top = base - 36 - int(rng.integers(0, 10))
        c = cols[k % len(cols)]
        cv.line(ux, base - 16, ux + (k - 3) // 2, top + 6, OUT)
        cv.poly([(ux - 2, base - 16), (ux + 2, base - 16), (ux + (k - 3) // 2 + 1, top + 6), (ux + (k - 3) // 2 - 1, top + 6)], c)
        cv.line(ux + (k - 3) // 2, top + 6, ux + (k - 3) // 2, top + 1, IRON[2])
        cv.px(ux + (k - 3) // 2 + 1, top, IRON[3]); cv.px(ux + (k - 3) // 2 + 2, top + 1, IRON[3])
    cv.rect(cx - 10, base - 18, 20, 18, OUT)
    cv.rect(cx - 9, base - 17, 18, 16, "#6a6a7c"); cv.vline(cx - 8, base - 17, 16, "#8e8ea0"); cv.vline(cx + 7, base - 17, 16, "#4a4a5a")
    for yy in (base - 14, base - 5):
        cv.hline(cx - 9, yy, 18, "#4a4a5a")
    cv.rect(cx - 4, base - 12, 8, 5, PAPER[2]); cv.px(cx - 2, base - 10, "#7e3a30"); cv.px(cx, base - 10, "#7e3a30")


def wall_bicycle(cv, x, y, seed=0):
    """An unclaimed bicycle hung on two wall hooks, front wheel up, with a big tag."""
    cv.rect(x + 2, y - 4, 3, 5, IRON[3]); cv.rect(x + 36, y - 4, 3, 5, IRON[3])
    for (wx, wy) in [(x - 6, y), (x + 26, y + 6)]:
        for a in np.linspace(0, 2 * np.pi, 48):
            cv.px(int(round(wx + 10 + np.cos(a) * 10)), int(round(wy + 10 + np.sin(a) * 10)), OUT)
            cv.px(int(round(wx + 10 + np.cos(a) * 9)), int(round(wy + 10 + np.sin(a) * 9)), "#3a3440")
        for a in np.linspace(0, np.pi, 5)[:-1]:
            cv.line(int(wx + 10 - np.cos(a) * 8), int(wy + 10 - np.sin(a) * 8), int(wx + 10 + np.cos(a) * 8), int(wy + 10 + np.sin(a) * 8), C("#8e8ea0", 0.6))
        cv.rect(wx + 9, wy + 9, 3, 3, IRON[3])
    fr = "#2c8a8a"
    for (a, b) in [((x + 4, y + 10), (x + 22, y + 22)), ((x + 22, y + 22), (x + 36, y + 16)), ((x + 4, y + 10), (x + 26, y + 8)),
                   ((x + 26, y + 8), (x + 36, y + 16)), ((x + 26, y + 8), (x + 22, y + 22))]:
        cv.line(a[0], a[1] + 1, b[0], b[1] + 1, OUT); cv.line(a[0], a[1], b[0], b[1], fr)
    cv.rect(x + 24, y + 4, 7, 3, OUT); cv.hline(x + 25, y + 5, 5, "#5a4040")
    cv.line(x + 4, y + 10, x + 2, y + 2, OUT); cv.line(x + 1, y + 2, x + 6, y + 1, IRON[3])
    cv.line(x + 30, y + 2, x + 34, y + 2, KRAFT[4]); cv.rect(x + 33, y + 1, 7, 9, KRAFT[4]); cv.rect(x + 34, y + 3, 5, 1, "#7e3a30")
    cv.rect(x + 34, y + 5, 4, 1, KRAFT[1])


def arcade_carpet(cv, x, y, w, h, seed=0):
    """The Connection's bowling-alley carpet seen through the doorway: dark navy with a faint
    neon zigzag and a few confetti flecks."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, "#1c1d38")
    for yy in range(y + 3, y + h, 8):
        for xx in range(x, x + w):
            k = (xx - x) % 8
            zy = yy + (k if k < 4 else 8 - k) // 2
            if y <= zy < y + h:
                cv.px(xx, zy, "#2c2c5a")
    for _ in range(w * h // 60):
        cx, cy = x + int(rng.integers(0, w - 2)), y + int(rng.integers(0, h - 1))
        c = ["#c45a88", "#3aa8a0", "#c8a058", "#6a5ac8"][int(rng.integers(4))]
        cv.rect(cx, cy, 2, 1, c)


def wall_shelf_boxes(cv, x, y, w, labels=("SPR", "SUM", "FAL"), seed=0):
    """A plank shelf on two brackets with archive boxes of past terms, one bulging open."""
    rng = np.random.default_rng(seed)
    bx = x + 3
    for i, lab in enumerate(labels):
        bw = int(rng.integers(22, 27)); bh = int(rng.integers(15, 19))
        if bx + bw > x + w - 2:
            break
        cv.rect(bx, y - bh, bw, bh, OUT)
        cv.rect(bx + 1, y - bh + 1, bw - 2, bh - 1, KRAFT[2]); cv.hline(bx + 1, y - bh + 1, bw - 2, KRAFT[4])
        cv.vline(bx + bw - 2, y - bh + 1, bh - 1, KRAFT[1])
        cv.rect(bx + bw // 2 - 4, y - bh + 4, 8, 3, KRAFT[0])
        cv.rect(bx + 2, y - 9, bw - 4, 8, PAPER[3])
        text(cv, lab, bx + bw // 2 - text_width(lab) // 2, y - 10, "#3a2a26")
        if i == 1:
            lost_item(cv, "scarf", bx + bw // 2, y - bh + 1, rng)
        bx += bw + 2
    cv.rect(x, y, w, 4, OUT); cv.rect(x + 1, y, w - 2, 3, PANEL[4]); cv.hline(x + 1, y, w - 2, PANEL[5])
    for k in (x + 6, x + w - 9):
        cv.rect(k, y + 4, 3, 6, IRON[2]); cv.line(k, y + 9, k + 3, y + 4, IRON[3])
