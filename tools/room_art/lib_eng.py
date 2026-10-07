"""Shared pieces for the Engineering Center rooms (E01 loading court, E02 shared workshop, E03 test
floor, E04 suspended model, E05 control booth) and their battle backdrops.

The building reads as one place: rosy CU sandstone and board-formed concrete outside; inside, cool
concrete and steel, safety yellow, blueprint blue, the teal-and-red of LOADBEARER's machinery, and
warm amber work lights against the night. Prop painters return (Canvas, anchor_x, anchor_y) like
props.py: the anchor is the floor point of the placement.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, LEAF, ground_shadow, shrub, grass_tuft
from surfaces import light_pool
from facade import SANDSTONE, TRIM, ROOF, GLOW, DARKGLASS, FRAME, roof_tiles
from lib_umc import halo, soft_ellipse, bolt, hazard_band, SAFETY, EXIT_GREEN, PAPER, SHADOW

INK = "#171a2b"
# outside: CU sandstone (a touch cooler than the UMC's), board-formed concrete
STONE_E = ["#3e2e32", "#5c4446", "#7a5a56", "#8e6a62", "#a27c70", "#b8907e", "#cca692"]
CONC = ["#25232b", "#353239", "#46424a", "#58535a", "#6a6468", "#7c7576", "#8f8784", "#a49a94", "#b9aea4"]
ASPH = ["#201e26", "#29272f", "#312e37", "#38353e", "#403c46", "#48444e", "#55505a"]
# machinery: steel blue-grey, LOADBEARER teal, hydraulic red, crane yellow
STEEL = ["#15161f", "#22242f", "#323543", "#454a5a", "#5e6476", "#7c8294", "#a2a8b8", "#c8ccd6"]
TEALM = ["#142226", "#1c3134", "#264440", "#30574f", "#3f6e62", "#558a78", "#74a892"]
REDM = ["#2e1216", "#4a1a1e", "#6e2428", "#943432", "#b84a3e", "#d06a52"]
CRANE = ["#4a3410", "#7a5618", "#a87a1e", "#d4a030", "#ecc04c", "#f8dc84"]
BLUEPRINT = ["#121c3c", "#1a2a56", "#243a72", "#34528e", "#6a8cc4", "#b4c8ec", "#e2ecfa"]
CHALK = ["#16201c", "#1e2c26", "#273a32", "#31483e", "#9cb0a2", "#d8e2d6"]
PLY = ["#3a2a22", "#5a4232", "#7a5c42", "#987552", "#b48e64", "#cba57a", "#dcbc90"]
MAPLE = ["#4a3020", "#6e4a2e", "#946a40", "#b08550", "#c89e64", "#dcb87c", "#ecd09a"]
EPOXY = ["#22262e", "#2a3038", "#323a43", "#3a444e", "#434e58", "#4e5a64", "#5c6872"]
CARPET = ["#141824", "#1a2030", "#20283a", "#263046", "#2e3a52"]
FOAM = ["#1c1a26", "#24222f", "#2d2a3a", "#363346", "#433f55"]
GRASS_E = ["#141c1a", "#1b2622", "#22302a", "#2b3b31", "#36483a", "#425640"]
WATER = ["#0e1424", "#141c32", "#1c2844", "#283a5c", "#4a6488", "#8aa4c8"]
NIGHT_BANDS = ["#141432", "#1b1a3e", "#232149", "#2e2853", "#3b2f5c", "#4c3762", "#5e3f66"]
NIGHT_CLOUD = ["#2c2648", "#3a3058", "#463864", "#52406c", "#6a4c76", "#8e5e80", "#b47486"]
WARM = ["#7a4a24", "#c47a2c", "#e9a84a", "#f6cf7a", "#fff0c4"]
SCOPE = ["#0c1a14", "#12281e", "#1e4430", "#3e8a5a", "#7ae0a0", "#d0ffe0"]
REC = ["#3a0e12", "#7a1a1e", "#c42a2a", "#ff5a4a", "#ffb0a0"]


# ---------------------------------------------------------------------------------------------
# numpy helpers (large surfaces are painted as arrays; Canvas.px is for detail)
# ---------------------------------------------------------------------------------------------

def P(hexes):
    """Palette list -> float array (n, 3)."""
    return np.array([C(h)[:3] for h in hexes], np.float32)


def H(h):
    return np.array(C(h)[:3], np.float32)


def hashn(a, b, seed=0):
    """Deterministic integer-cell noise in 0..1 (same recipe as persp.hash2)."""
    h = (np.asarray(a).astype(np.int64) * 73856093) ^ (np.asarray(b).astype(np.int64) * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFF).astype(np.float32) / 65535.0


def put_rgb(cv, x, y, rgb, mask=None):
    """Write an (h, w, 3) array opaque into the canvas at (x, y); optional bool mask."""
    h, w = rgb.shape[:2]
    x0, y0, x1, y1 = max(0, x), max(0, y), min(cv.w, x + w), min(cv.h, y + h)
    if x0 >= x1 or y0 >= y1:
        return
    src = rgb[y0 - y:y1 - y, x0 - x:x1 - x]
    dst = cv.a[y0:y1, x0:x1]
    if mask is None:
        dst[..., :3] = src
        dst[..., 3] = 1
    else:
        m = mask[y0 - y:y1 - y, x0 - x:x1 - x]
        dst[m, :3] = src[m]
        dst[m, 3] = 1


def tint_rect(cv, x, y, w, h, colour, alpha):
    cv.rect(x, y, w, h, C(colour, alpha))


def grid(w, h):
    ys, xs = np.mgrid[0:h, 0:w]
    return xs, ys


def stepped_glow(cv, cx, cy, rx, ry, colour="#f6cf7a", strength=0.16, steps=3):
    """Elliptical glow in a few flat bands (for light spilling on walls or floors)."""
    light_pool(cv, cx, cy, rx, ry, color=colour, strength=strength, steps=steps)


def dashed(cv, x0, y0, x1, y1, colour, on=6, off=3, alpha=1.0):
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
    for i in range(n):
        if (i % (on + off)) < on:
            t = i / max(1, n - 1)
            cv.px(int(round(x0 + (x1 - x0) * t)), int(round(y0 + (y1 - y0) * t)), C(colour, alpha))


def worn_line(cv, x, y, w, h, colour, alpha=0.8, seed=0, wear=0.18):
    """A painted floor line with worn gaps (clustered, not speckle)."""
    rng = np.random.default_rng(seed)
    if w >= h:
        xx = x
        while xx < x + w:
            run = int(rng.integers(5, 18))
            if rng.random() > wear:
                cv.rect(xx, y, min(run, x + w - xx), h, C(colour, alpha))
            else:
                cv.rect(xx, y, min(run, x + w - xx), h, C(colour, alpha * 0.35))
            xx += run
    else:
        yy = y
        while yy < y + h:
            run = int(rng.integers(5, 14))
            cv.rect(x, yy, w, min(run, y + h - yy), C(colour, alpha if rng.random() > wear else alpha * 0.35))
            yy += run


def big_stencil(cv, s, x, y, colour, alpha=0.55, scale=2):
    """Floor stencil at 2x the game font, flat paint (reads as lettering on the ground)."""
    tmp = Canvas(text_width(s) + 2, 12)
    text(tmp, s, 1, 0, "#ffffff")
    m = tmp.a[..., 3] > 0.5
    ys, xs = np.where(m)
    for yy, xx in zip(ys, xs):
        cv.rect(x + xx * scale, y + yy * scale, scale, scale, C(colour, alpha))


def wire(cv, x0, y0, x1, y1, sag, colour="#14121c", hi=None):
    """A hanging cable or rope between two points (parabolic sag)."""
    n = int(max(abs(x1 - x0), abs(y1 - y0))) + 2
    prev = None
    for i in range(n + 1):
        t = i / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        p = (int(round(x)), int(round(y)))
        if prev is not None and p == prev:
            continue
        cv.px(p[0], p[1], colour)
        if hi:
            cv.px(p[0], p[1] - 1, C(hi, 0.4))
        prev = p


# ---------------------------------------------------------------------------------------------
# sky and outside
# ---------------------------------------------------------------------------------------------

def night_sky(cv, x, y, w, h, seed=3, stars=120, horizon=None):
    """Stepped indigo bands toward a plum horizon, stars (same palette as the Norlin quad)."""
    horizon = horizon or (y + h)
    for yy in range(y, y + h):
        t = (yy - y) / max(1, horizon - y - 1)
        i = min(len(NIGHT_BANDS) - 1, int(max(0, t) ** 0.9 * len(NIGHT_BANDS)))
        cv.hline(x, yy, w, NIGHT_BANDS[i])
    rng = np.random.default_rng(seed)
    pts = []
    for _ in range(stars):
        sx, sy = x + int(rng.integers(0, w)), y + int(rng.integers(0, max(1, int(h * 0.8))))
        c = "#c8c0e0" if rng.random() < 0.65 else "#f2d27a"
        cv.px(sx, sy, c)
        if rng.random() < 0.12:
            pts.append((sx, sy, c))
    return pts


def night_clouds(cv, specs, seed=4):
    from clouds import _cloud
    crng = np.random.default_rng(seed)
    for (cx, cy, length, thick) in specs:
        cl = _cloud(length, thick, crng, NIGHT_CLOUD)
        cv.paste(cl, cx, cy - cl.shape[0])


def tree_mass(cv, x0, x1, base, top, seed=0, pal=("#151a24", "#1a2230", "#202a36", "#26323e")):
    """Dark crowns of trees along a skyline (night silhouettes with a faint lit rim)."""
    rng = np.random.default_rng(seed)
    for x in range(x0 - 8, x1 + 8, 7):
        hh = int(rng.integers(max(4, (base - top) // 2), max(6, base - top)))
        ww = int(rng.integers(12, 22))
        cv.ellipse(x, base - hh, ww, hh * 2, pal[1])
        cv.ellipse(x + 2, base - hh + 2, ww - 6, max(2, hh // 2), pal[2])
        if rng.random() < 0.5:
            cv.px(x + ww // 2, base - hh + 1, pal[3])
    for x in range(x0 - 6, x1 + 6, 5):
        hh = int(rng.integers(3, 9))
        cv.ellipse(x, base - hh, int(rng.integers(8, 14)), hh * 2, pal[0])


def ecot_tower(cv, cx, top, base, w=46, seed=0):
    """The Engineering Center's office tower behind the annex: sandstone corners, slit windows,
    a few lab lights on late, an aviation beacon on the roof. Returns the beacon point."""
    rng = np.random.default_rng(seed)
    x = cx - w // 2
    cv.rect(x - 1, top, w + 2, base - top, "#191a28")
    cv.rect(x, top + 1, w, base - top, "#2a2634")
    for k, yy in enumerate(range(top + 2, base, 4)):
        cv.hline(x, yy, w, "#2e2a38" if k % 2 else "#26222e")
    for qx in (x, x + w - 5):
        cv.rect(qx, top + 1, 5, base - top, "#3a3040"); cv.vline(qx, top + 1, base - top, "#4a3c4a")
    # window grid: narrow slits, some lit
    for row, yy in enumerate(range(top + 8, base - 6, 9)):
        for col, xx in enumerate(range(x + 8, x + w - 8, 6)):
            lit = rng.random() < 0.18
            cv.rect(xx, yy, 3, 6, "#e9a84a" if lit else "#1c2032")
            if lit:
                cv.px(xx, yy, "#f6cf7a")
    cv.rect(x - 3, top - 3, w + 6, 4, "#3a3040"); cv.hline(x - 3, top - 3, w + 6, "#54465a")
    # rooftop plant and the beacon mast
    cv.rect(cx - 9, top - 9, 18, 6, "#231f2e"); cv.rect(cx + 4, top - 16, 2, 13, "#231f2e")
    return (cx + 5, top - 17)


def sandstone_wall(cv, x, y, w, h, seed=0, course=5, pal=STONE_E):
    """Rough Lyons sandstone in coursed rubble (the campus stone), with a darker foot."""
    from surfaces import ashlar_wall
    ashlar_wall(cv, x, y, w, h, pal, course=course, seed=seed, cap=False)
    cv.rect(x, y + h - 4, w, 4, C(SHADOW, 0.25))


def concrete_band(cv, x, y, w, h, seed=0):
    """Board-formed concrete: horizontal board marks, a lit top edge, tie holes."""
    rng = np.random.default_rng(seed)
    cv.rect(x, y, w, h, CONC[5])
    for yy in range(y + 2, y + h, 3):
        cv.hline(x, yy, w, CONC[4] if (yy // 3) % 2 else CONC[5])
    cv.hline(x, y, w, CONC[7]); cv.hline(x, y + 1, w, CONC[6])
    cv.hline(x, y + h - 1, w, CONC[2])
    for tx in range(x + 8 + int(rng.integers(0, 8)), x + w - 4, 24):
        cv.px(tx, y + h // 2, CONC[2])
    for _ in range(w // 30):
        sx = x + int(rng.integers(0, w - 3))
        cv.vline(sx, y + 2, int(rng.integers(2, max(3, h - 2))), C(CONC[2], 0.5))


def concrete_fin(cv, x, y, w, h):
    """A precast vertical fin between window bays (lit left face, shadowed right)."""
    cv.rect(x, y, w, h, CONC[5])
    cv.vline(x, y, h, CONC[7]); cv.vline(x + 1, y, h, CONC[6]); cv.vline(x + w - 1, y, h, CONC[3])
    for yy in range(y + 6, y + h, 12):
        cv.hline(x, yy, w, CONC[4])


def lab_window(cv, x, y, w, h, lit=True, blind=0.0, seed=0, lamp=False):
    """Tall window with a steel frame; lit labs glow amber (a blind half down, a desk lamp),
    dark ones show the night reflected."""
    rng = np.random.default_rng(seed)
    cv.rect(x - 1, y - 1, w + 2, h + 2, FRAME)
    if lit:
        for yy in range(y, y + h):
            t = (yy - y) / h
            cv.hline(x, yy, w, GLOW[3] if t < 0.3 else GLOW[2] if t < 0.75 else GLOW[1])
        # ceiling light tube inside and the far wall's shelf
        cv.hline(x, y + 2, w, GLOW[4])
        cv.rect(x, y + h - 9, w, 2, "#8a4c26")
        for bx in range(x + 1, x + w - 1, 3):
            if rng.random() < 0.6:
                cv.rect(bx, y + h - 13, 2, 4, ["#7e3a30", "#425da6", "#5c897c", "#e6d6b1"][int(rng.integers(4))])
        if lamp:
            cv.rect(x + w // 2 - 2, y + h - 18, 5, 3, "#3a2a24"); cv.vline(x + w // 2, y + h - 15, 6, "#3a2a24")
            cv.rect(x + w // 2 - 3, y + h - 19, 7, 1, GLOW[4])
    else:
        for yy in range(y, y + h):
            t = (yy - y) / h
            cv.hline(x, yy, w, DARKGLASS[1] if t < 0.5 else DARKGLASS[0])
        cv.line(x + 1, y + h - 4, x + w - 2, y + h // 3, DARKGLASS[3])
        cv.line(x + 1, y + h - 1, x + w - 2, y + h // 3 + 3, C(DARKGLASS[2], 0.8))
    if blind > 0:
        bh = int(h * blind)
        cv.rect(x, y, w, bh, "#cbb69b" if lit else "#4a4a5e")
        for yy in range(y + 1, y + bh, 2):
            cv.hline(x, yy, w, "#a8927c" if lit else "#3a3a4c")
        cv.hline(x, y + bh, w, FRAME)
    cv.vline(x + w // 2, y, h, FRAME)
    cv.hline(x, y + h * 2 // 3, w, FRAME)
    cv.rect(x - 2, y + h + 1, w + 4, 2, CONC[6]); cv.hline(x - 2, y + h + 3, w + 4, C(SHADOW, 0.5))


def wall_pack(cv, x, y, lit=True):
    """Small exterior wall light (a box with a lens on the underside)."""
    cv.rect(x - 4, y, 9, 6, OUT); cv.rect(x - 3, y + 1, 7, 3, STEEL[3]); cv.hline(x - 3, y + 1, 7, STEEL[5])
    cv.rect(x - 3, y + 4, 7, 2, WARM[3] if lit else STEEL[2])
    if lit:
        cv.hline(x - 2, y + 5, 5, WARM[4])
        for k, a in enumerate([0.16, 0.1, 0.06]):
            cv.poly([(x - 3 - k * 6, y + 6 + k * 10), (x + 3 + k * 6, y + 6 + k * 10), (x + 9 + k * 6, y + 18 + k * 10), (x - 9 - k * 6, y + 18 + k * 10)], C(WARM[3], a))


def gooseneck_dock_light(cv, x, y, arm=12, flip=False):
    """Dock light on a swing arm (a shade aimed down into the doorway)."""
    d = -1 if flip else 1
    cv.rect(x - 1, y - 2, 3, 6, OUT)
    cv.line(x, y, x + d * arm, y + 4, OUT); cv.line(x, y - 1, x + d * arm, y + 3, STEEL[4])
    hx = x + d * arm
    cv.poly([(hx - 4, y + 3), (hx + 4, y + 3), (hx + 6, y + 9), (hx - 6, y + 9)], OUT)
    cv.poly([(hx - 3, y + 4), (hx + 3, y + 4), (hx + 4, y + 8), (hx - 4, y + 8)], CRANE[3])
    cv.hline(hx - 4, y + 9, 9, WARM[4])
    return hx, y + 9


def rollup_door_closed(cv, x, y, w, h, label=None, seed=0):
    """Steel roll-up door, down: ribbed slats, a coil box above, guide rails, kick bar, bumpers."""
    cv.rect(x - 4, y - 8, w + 8, 8, OUT); cv.rect(x - 3, y - 7, w + 6, 6, STEEL[3]); cv.hline(x - 3, y - 7, w + 6, STEEL[5])
    for gx in (x - 4, x + w):
        cv.rect(gx, y, 4, h, OUT); cv.vline(gx + 1, y, h, STEEL[4]); cv.vline(gx + 2, y, h, STEEL[2])
    for k, yy in enumerate(range(y, y + h)):
        r = (yy - y) % 5
        c = [STEEL[4], STEEL[5], STEEL[4], STEEL[3], STEEL[2]][r]
        cv.hline(x, yy, w, c)
    rng = np.random.default_rng(seed)
    for _ in range(w * h // 120):
        sx, sy = x + int(rng.integers(0, w - 6)), y + int(rng.integers(0, h - 2))
        cv.hline(sx, sy, int(rng.integers(3, 8)), C(STEEL[2], 0.6))
    hazard_band(cv, x, y + h - 5, w, 5)
    cv.rect(x + w // 2 - 5, y + h - 9, 10, 3, OUT); cv.hline(x + w // 2 - 4, y + h - 8, 8, STEEL[6])
    if label:
        cv.rect(x + w // 2 - text_width(label) // 2 - 3, y + 8, text_width(label) + 6, 11, C("#141420", 0.8))
        text(cv, label, x + w // 2 - text_width(label) // 2, y + 9, SAFETY[3])
    for bx in (x - 10, x + w + 4):
        cv.rect(bx, y + h - 18, 6, 14, OUT); cv.rect(bx + 1, y + h - 17, 4, 12, "#24222a"); cv.hline(bx + 1, y + h - 17, 4, "#3a3842")


def rollup_door_open(cv, x, y, w, h, seed=0, interior=None):
    """Roll-up door open on a lit workshop: the coil box above, guide rails, the room inside
    (a welding screen, a bench, pegboard, the floor running back). Returns key points."""
    rng = np.random.default_rng(seed)
    cv.rect(x - 4, y - 10, w + 8, 10, OUT); cv.rect(x - 3, y - 9, w + 6, 8, STEEL[3]); cv.hline(x - 3, y - 9, w + 6, STEEL[5])
    cv.rect(x - 2, y - 3, w + 4, 3, STEEL[2])
    for k in range(3):   # the slat bottoms peeking out of the coil
        cv.hline(x, y + k, w, [STEEL[4], STEEL[3], STEEL[2]][k])
    cv.rect(x, y + 3, w, 3, SAFETY[2]); hazard_band(cv, x, y + 3, w, 3)
    top = y + 6
    # interior back wall (warm plaster lit by the shop lights)
    cv.rect(x, top, w, h - 6, "#c47a40")
    for yy in range(top, y + h):
        t = (yy - top) / max(1, h - 6)
        cv.hline(x, yy, w, mix("#e8a860", "#7a4426", min(1.0, t * 1.3)))
    floor_y = y + h - 18
    # pegboard and tools on the inner wall
    cv.rect(x + 4, top + 6, 24, 18, "#8a5a36")
    for gy in range(top + 8, top + 23, 3):
        for gx in range(x + 6, x + 27, 3):
            cv.px(gx, gy, "#6a4228")
    for k, tx in enumerate(range(x + 7, x + 26, 4)):
        cv.vline(tx, top + 9, 8 + (k % 3) * 2, ["#3a3a48", "#c84a3c", "#3a3a48", "#e8b45c", "#3a3a48"][k % 5])
    # a hanging shop light inside
    cv.vline(x + w // 2 + 8, top, 6, "#3a2a24")
    cv.poly([(x + w // 2 + 3, top + 6), (x + w // 2 + 13, top + 6), (x + w // 2 + 11, top + 9), (x + w // 2 + 5, top + 9)], "#2a2024")
    cv.hline(x + w // 2 + 5, top + 9, 7, "#fff0c4")
    # welding screen (red translucent curtain on a frame) on the right
    sx0 = x + w - 26
    cv.rect(sx0, top + 14, 22, floor_y - top - 12, "#7e2a26")
    for gx in range(sx0, sx0 + 22, 3):
        cv.vline(gx, top + 14, floor_y - top - 12, "#9a3a30")
    cv.rect(sx0 - 1, top + 12, 24, 2, STEEL[2]); cv.vline(sx0 - 1, top + 12, floor_y - top - 8, STEEL[2]); cv.vline(sx0 + 22, top + 12, floor_y - top - 8, STEEL[2])
    # bench silhouette on the left with a vise and a lamp
    bx0 = x + 6
    cv.rect(bx0, floor_y - 12, 30, 3, "#3a2418"); cv.hline(bx0, floor_y - 12, 30, "#6a4228")
    cv.vline(bx0 + 2, floor_y - 9, 9, "#2a1a14"); cv.vline(bx0 + 27, floor_y - 9, 9, "#2a1a14")
    cv.rect(bx0 + 20, floor_y - 16, 6, 4, "#2a2a34")
    # inner floor running back to the door line
    for yy in range(floor_y, y + h):
        t = (yy - floor_y) / 18
        cv.hline(x, yy, w, mix("#a8683c", "#5a3a2a", t))
    for yy in range(floor_y + 3, y + h, 5):
        cv.hline(x, yy, w, C("#4a2e22", 0.5))
    # door jambs
    for gx in (x - 4, x + w):
        cv.rect(gx, y, 4, h, OUT); cv.vline(gx + 1, y, h, STEEL[4]); cv.vline(gx + 2, y, h, STEEL[2])
    return {"screen": (sx0, top + 14, 22, floor_y - top - 12), "floor": floor_y}


def cylinder_cage(cv, x, y, w, h, seed=0):
    """Chain-link cage of gas cylinders against the wall (x, y = top-left; bottom on the floor line)."""
    rng = np.random.default_rng(seed)
    cols = [("#3e6a4e", "#5a8a66"), ("#6a6e7a", "#8e94a2"), ("#3e6a4e", "#5a8a66"), ("#7a3a30", "#a85a46"), ("#6a6e7a", "#8e94a2")]
    cx = x + 3
    k = 0
    while cx < x + w - 6:
        c, hi = cols[k % len(cols)]
        ch = h - 6 - int(rng.integers(0, 4))
        cv.rect(cx, y + h - ch, 7, ch, OUT); cv.rect(cx + 1, y + h - ch + 2, 5, ch - 2, c); cv.vline(cx + 1, y + h - ch + 2, ch - 2, hi)
        cv.ellipse(cx + 1, y + h - ch, 5, 4, c); cv.rect(cx + 2, y + h - ch - 3, 3, 3, STEEL[5])
        cx += 8
        k += 1
    # chain-link mesh and frame
    for yy in range(y, y + h):
        for xx in range(x, x + w):
            if (xx + yy) % 4 == 0 or (xx - yy) % 4 == 0:
                cv.px(xx, yy, C("#9aa0ac", 0.45))
    cv.rect(x, y, w, 2, STEEL[4]); cv.rect(x, y, 2, h, STEEL[4]); cv.rect(x + w - 2, y, 2, h, STEEL[3])
    cv.rect(x + w // 2 - 6, y + 6, 12, 7, "#e6d6b1"); cv.hline(x + w // 2 - 4, y + 9, 8, "#c84a3c")


def dumpster(cv, x, y, w=56, h=30, colour=("#1e3a34", "#2a4e44", "#3a6656", "#4e8070")):
    """Steel dumpster against the wall; lid half open, a sign, castors."""
    cv.rect(x, y + 6, w, h - 6, OUT)
    cv.rect(x + 1, y + 7, w - 2, h - 9, colour[1])
    for gx in range(x + 6, x + w - 4, 9):
        cv.rect(gx, y + 8, 2, h - 12, colour[2]); cv.vline(gx, y + 8, h - 12, colour[3])
    cv.rect(x - 1, y + 4, w + 2, 4, OUT); cv.rect(x, y + 5, w, 2, colour[2])
    cv.poly([(x + 2, y + 4), (x + w // 2, y + 4), (x + w // 2 - 4, y - 4), (x + 4, y - 2)], colour[0])
    cv.line(x + 4, y - 2, x + w // 2 - 4, y - 4, colour[3])
    cv.rect(x + w // 2 + 4, y + 12, 18, 8, "#e6d6b1"); cv.hline(x + w // 2 + 6, y + 15, 14, "#2a4e44"); cv.hline(x + w // 2 + 6, y + 17, 10, "#2a4e44")
    for wx in (x + 4, x + w - 9):
        cv.rect(wx, y + h - 3, 5, 3, OUT)


def wheelie_bin(cv, x, y, colour="#2c4a8a", hi="#4a6ab0", sym="#e6d6b1"):
    cv.rect(x, y + 3, 16, 24, OUT); cv.rect(x + 1, y + 4, 14, 22, colour); cv.vline(x + 1, y + 4, 22, hi)
    cv.rect(x - 1, y, 18, 4, OUT); cv.rect(x, y + 1, 16, 2, hi)
    cv.rect(x + 5, y + 10, 6, 6, sym); cv.rect(x + 6, y + 11, 4, 4, colour)
    cv.rect(x + 1, y + 26, 4, 2, OUT); cv.rect(x + 11, y + 26, 4, 2, OUT)


def materials_rack(cv, x, y, w, h, seed=0):
    """Cantilever rack against the wall with lumber, steel tube and an I-beam offcut."""
    rng = np.random.default_rng(seed)
    for px_ in (x + 2, x + w - 6):
        cv.rect(px_, y, 4, h, OUT); cv.vline(px_ + 1, y, h, STEEL[4]); cv.vline(px_ + 2, y, h, STEEL[3])
    for k, ay in enumerate(range(y + 6, y + h - 4, 10)):
        cv.rect(x, ay, w, 2, STEEL[3]); cv.hline(x, ay, w, STEEL[5])
        # stock on this arm
        sx = x + 1
        while sx < x + w - 2:
            kind = rng.random()
            if kind < 0.45:   # lumber boards
                bw = int(rng.integers(10, 22))
                for j in range(int(rng.integers(1, 3))):
                    cv.rect(sx, ay - 3 - j * 3, min(bw, x + w - sx), 3, PLY[4 - j]); cv.hline(sx, ay - 3 - j * 3, min(bw, x + w - sx), PLY[5])
                sx += bw + 1
            elif kind < 0.75:  # steel tubes (end-on circles)
                for j in range(int(rng.integers(2, 5))):
                    cv.rect(sx + j * 3, ay - 3, 3, 3, STEEL[2]); cv.px(sx + j * 3 + 1, ay - 2, STEEL[6])
                sx += 14
            else:   # an I-beam
                cv.rect(sx, ay - 5, 12, 1, CRANE[2]); cv.rect(sx + 5, ay - 5, 2, 5, CRANE[1]); cv.rect(sx, ay - 1, 12, 1, CRANE[2])
                sx += 14


def pallet_stack(cv, x, base, w=34, n=3):
    """Stacked wooden pallets at a wall foot (slats, blocks, a gap of shadow between)."""
    for k in range(n):
        y = base - (k + 1) * 6
        cv.rect(x, y, w, 6, OUT)
        cv.rect(x + 1, y + 1, w - 2, 2, PLY[4]); cv.hline(x + 1, y + 1, w - 2, PLY[5])
        for bx in (x + 1, x + w // 2 - 2, x + w - 5):
            cv.rect(bx, y + 3, 4, 2, PLY[3])
        cv.rect(x + 5, y + 3, w // 2 - 7, 2, "#14121a"); cv.rect(x + w // 2 + 2, y + 3, w // 2 - 7, 2, "#14121a")


def traffic_cone(cv, x, base, h=14):
    cv.poly([(x - 4, base - 2), (x - 1, base - h), (x + 1, base - h), (x + 4, base - 2)], OUT)
    cv.poly([(x - 3, base - 2), (x - 1, base - h + 1), (x, base - h + 1), (x + 3, base - 2)], "#e0662c")
    cv.hline(x - 2, base - h // 2, 5, "#f2f2ee"); cv.vline(x - 1, base - h + 2, h - 4, "#f2904a")
    cv.rect(x - 6, base - 2, 13, 2, OUT); cv.hline(x - 5, base - 2, 11, "#b8461e")


def fire_hydrant(cv, x, base):
    cv.rect(x - 4, base - 16, 9, 15, OUT); cv.rect(x - 3, base - 15, 7, 14, "#b0302a"); cv.vline(x - 3, base - 15, 14, "#d85a48")
    cv.rect(x - 6, base - 11, 13, 3, OUT); cv.rect(x - 5, base - 10, 11, 1, "#d85a48")
    cv.ellipse(x - 3, base - 19, 7, 5, "#b0302a"); cv.px(x, base - 19, "#e8b45c")
    cv.rect(x - 5, base - 2, 11, 2, OUT)


# ---------------------------------------------------------------------------------------------
# ground
# ---------------------------------------------------------------------------------------------

def soft_field(w, h, cell, seed=0):
    """Smooth value noise in 0..1 (bilinear over a coarse random grid, smoothstepped)."""
    rng = np.random.default_rng(seed)
    gw, gh = w // cell + 3, h // cell + 3
    g = rng.random((gh, gw)).astype(np.float32)
    ys = np.arange(h) / cell
    xs = np.arange(w) / cell
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = (ys - y0)[:, None]
    fx = (xs - x0)[None, :]
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; c = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def asphalt_np(w, h, seed=0):
    """Court asphalt as an array: soft worn patches in three tones (organic, not blocky), fine
    pale aggregate in tiny clusters, a few darker binder spots."""
    xs, ys = grid(w, h)
    pal = P(ASPH)
    f = 0.65 * soft_field(w, h, 46, seed) + 0.35 * soft_field(w, h, 14, seed + 1)
    idx = np.where(f < 0.36, 2, np.where(f < 0.62, 3, 4))
    rgb = pal[idx].copy()
    agg = hashn(xs // 2, ys // 2, seed + 7)
    fine = hashn(xs, ys, seed + 8)
    lift = (agg > 0.94) & (fine > 0.4)
    rgb[lift] = pal[np.minimum(idx[lift] + 2, len(ASPH) - 1)]
    rgb[(agg < 0.025) & (fine > 0.5)] = pal[1]
    return rgb


def tar_snake(cv, x, y, length, seed=0, vertical=False):
    """Crack sealant wandering across asphalt (glossy black line with a dull edge)."""
    rng = np.random.default_rng(seed)
    px_, py_ = x, y
    for i in range(length):
        cv.px(px_, py_, "#15131a")
        cv.px(px_ + (0 if vertical else 0), py_ + (1 if not vertical else 0), C("#15131a", 0.5))
        if i % 9 == 4:
            cv.px(px_, py_, "#3a3846")
        if vertical:
            py_ += 1; px_ += int(rng.choice([-1, 0, 0, 1]))
        else:
            px_ += 1; py_ += int(rng.choice([-1, 0, 0, 0, 1]))


def conc_slabs_np(w, h, slab=40, row=24, seed=0, pal=CONC, base=5):
    """Concrete apron slabs: each slab one tone, saw joints dark with a lit lip, a fine trowel
    pattern and a few hairline cracks."""
    xs, ys = grid(w, h)
    p = P(pal)
    cx, cy = xs // slab, ys // row
    t = hashn(cx, cy, seed)
    idx = np.where(t < 0.3, base - 1, np.where(t < 0.85, base, base + 1))
    rgb = p[np.clip(idx, 0, len(pal) - 1)].copy()
    fine = hashn(xs // 3, ys // 2, seed + 2)
    rgb[fine > 0.93] = rgb[fine > 0.93] * 0.93
    jx, jy = xs % slab, ys % row
    rgb[jy == 0] = p[max(0, base - 3)]
    rgb[jx == 0] = p[max(0, base - 3)]
    rgb[(jy == 1) & (jx != 0)] = p[min(len(pal) - 1, base + 2)]
    return rgb


def flagstone_np(w, h, seed=0, pal=None):
    """Campus sandstone pavers in running courses (warm), for the pedestrian walk."""
    pal = pal or ["#3a2c2c", "#5a4440", "#76584e", "#86665a", "#967464", "#a6826e", "#b8927a"]
    xs, ys = grid(w, h)
    p = P(pal)
    rowh = 9
    r = ys // rowh
    off = (hashn(r, 3, seed) * 30).astype(int)
    width = 14 + (hashn(r, 5, seed) * 12).astype(int)
    c = (xs + off) // width
    t = hashn(c, r, seed + 1)
    idx = np.where(t < 0.25, 3, np.where(t < 0.65, 4, np.where(t < 0.9, 5, 2)))
    rgb = p[idx].copy()
    fx = (xs + off) % width
    fy = ys % rowh
    rgb[fy == 0] = p[1]
    rgb[fx == 0] = p[1]
    rgb[(fy == 1) & (fx != 0)] = p[6] * 0.5 + rgb[(fy == 1) & (fx != 0)] * 0.5
    grain = hashn(xs // 2, ys, seed + 9)
    rgb[(grain > 0.95) & (fy > 1) & (fx > 0)] *= 0.9
    return rgb


def grass_np(w, h, seed=0):
    """Night lawn in clustered blades (dark, cool)."""
    xs, ys = grid(w, h)
    p = P(GRASS_E)
    t = hashn(xs // 3, ys // 2, seed)
    t2 = hashn(xs // 11, ys // 6, seed + 3)
    idx = np.clip((t * 2.2 + t2 * 2.6).astype(int), 1, 5)
    rgb = p[idx]
    blade = hashn(xs, ys // 3, seed + 5)
    rgb[blade > 0.9] = p[5]
    return rgb


# ---------------------------------------------------------------------------------------------
# E01 props
# ---------------------------------------------------------------------------------------------

def court_lamp(height=68):
    """A campus pole light by the walk: black pole, banner arm, lantern head (lamp head ~h-5)."""
    w = 26
    cv = Canvas(w, height + 6, seed=3)
    cx, base = w // 2, height + 2
    ground_shadow(cv, cx, base, 9, 2)
    cv.rect(cx - 5, base - 4, 10, 4, IRON[1]); cv.hline(cx - 5, base - 4, 10, IRON[3])
    cv.rect(cx - 3, base - 9, 6, 5, IRON[2]); cv.vline(cx - 3, base - 9, 5, IRON[4])
    top = 16
    cv.rect(cx - 2, top, 4, base - 9 - top, IRON[2]); cv.vline(cx - 2, top, base - 9 - top, IRON[3]); cv.vline(cx + 1, top, base - 9 - top, IRON[0])
    # CU banner on a little arm
    cv.rect(cx + 2, top + 12, 7, 1, IRON[2])
    cv.rect(cx + 3, top + 13, 6, 14, "#cfb87c"); cv.rect(cx + 3, top + 13, 6, 2, "#2a2430")
    cv.rect(cx + 4, top + 17, 4, 5, "#2a2430"); cv.px(cx + 5, top + 19, "#cfb87c")
    # lantern
    cv.rect(cx - 5, 4, 10, 2, IRON[1])
    cv.rect(cx - 4, 6, 8, 9, AMBER[2]); cv.rect(cx - 3, 7, 6, 7, AMBER[3]); cv.rect(cx - 1, 8, 2, 4, AMBER[4])
    cv.vline(cx - 4, 6, 9, IRON[1]); cv.vline(cx + 3, 6, 9, IRON[0])
    cv.rect(cx - 5, 14, 10, 2, IRON[1]); cv.hline(cx - 5, 14, 10, IRON[3])
    cv.poly([(cx - 6, 4), (cx, 0), (cx + 5, 4)], IRON[1])
    return cv, cx, base


def flatbed_cart(width=110, height=50, seed=0):
    """A steel platform truck loaded with bridge parts: deck planks, an I-beam, a coil of rope,
    a toolbox, a roll of plans; a push handle with a SHARED tag."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    deck_y = base - 12
    # castors
    for wx in (ox + 6, ox + width - 14):
        cv.rect(wx, base - 7, 8, 7, OUT); cv.rect(wx + 1, base - 6, 6, 5, STEEL[2]); cv.rect(wx + 3, base - 4, 2, 2, STEEL[5])
        cv.rect(wx + 2, deck_y + 3, 4, 3, STEEL[3])
    # platform
    cv.rect(ox, deck_y - 1, width, 6, OUT)
    cv.rect(ox + 1, deck_y, width - 2, 4, "#2c4a7a"); cv.hline(ox + 1, deck_y, width - 2, "#4a6aa8")
    cv.hline(ox + 1, deck_y + 3, width - 2, "#1e3458")
    # push handle at the left end
    cv.rect(ox, deck_y - 30, 3, 30, OUT); cv.vline(ox + 1, deck_y - 29, 28, "#4a6aa8")
    cv.rect(ox, deck_y - 31, 12, 3, OUT); cv.hline(ox + 1, deck_y - 30, 10, "#4a6aa8")
    cv.rect(ox + 3, deck_y - 25, 8, 10, PAPER[2]); cv.hline(ox + 4, deck_y - 22, 6, "#7a3a30"); cv.hline(ox + 4, deck_y - 19, 5, "#425da6")
    cv.px(ox + 6, deck_y - 26, "#c84a3c")
    # stack of deck planks (end grain visible on the right)
    px0 = ox + 8
    for j in range(4):
        y0 = deck_y - 4 - j * 4
        L = width - 30 - (j % 2) * 6
        cv.rect(px0, y0, L, 4, OUT); cv.rect(px0 + 1, y0 + 1, L - 2, 2, PLY[4 - (j % 2)]); cv.hline(px0 + 1, y0 + 1, L - 2, PLY[5])
        for gx in range(px0 + 4, px0 + L - 4, 9):
            cv.hline(gx, y0 + 2, int(rng.integers(3, 6)), PLY[3])
        cv.rect(px0 + L - 3, y0 + 1, 2, 2, PLY[6])
    # an I-beam across the planks
    by = deck_y - 21
    cv.rect(px0 + 6, by - 1, 64, 6, OUT)
    cv.rect(px0 + 7, by, 62, 1, CRANE[4]); cv.rect(px0 + 7, by + 1, 62, 2, CRANE[2]); cv.rect(px0 + 7, by + 3, 62, 1, CRANE[3])
    cv.rect(px0 + 66, by - 2, 4, 8, CRANE[1]); cv.vline(px0 + 66, by - 2, 8, CRANE[3])
    for hx in range(px0 + 12, px0 + 64, 13):
        cv.px(hx, by + 2, CRANE[1])
    # coil of rope, toolbox, rolled plans on top
    rx = ox + width - 24
    cv.ellipse(rx, deck_y - 15, 16, 11, OUT); cv.ellipse(rx + 1, deck_y - 14, 14, 9, "#c8a46a"); cv.ellipse(rx + 4, deck_y - 12, 8, 5, OUT)
    for k in range(0, 14, 3):
        cv.px(rx + 1 + k, deck_y - 10 + (k % 2), "#8a6a3a")
    tbx = px0 + 18
    cv.rect(tbx, by - 9, 20, 9, OUT); cv.rect(tbx + 1, by - 8, 18, 7, "#b8302a"); cv.hline(tbx + 1, by - 8, 18, "#d85a48")
    cv.rect(tbx + 6, by - 12, 8, 3, OUT); cv.rect(tbx + 8, by - 5, 4, 2, STEEL[6])
    cv.rect(px0 + 44, by - 4, 18, 4, OUT); cv.rect(px0 + 45, by - 3, 16, 2, BLUEPRINT[4]); cv.hline(px0 + 45, by - 3, 16, BLUEPRINT[5])
    cv.rect(px0 + 60, by - 4, 3, 4, BLUEPRINT[2])
    return cv, ox + width // 2, base


def bike(cv, x, base, frame="#3a4f8a", hi="#5671b0", r=10, seed=0, flip=False):
    """A side-on bicycle (wheels 2r+1 across) parked at (x .. x+48, base)."""
    wheels = [(x + r + 1, base - r - 1), (x + 4 * r + 6, base - r - 1)]
    if flip:
        wheels = wheels[::-1]
    for cx, cy in wheels:
        for a in np.linspace(0, 2 * np.pi, 70):
            cv.px(int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r)), OUT)
            cv.px(int(round(cx + np.cos(a) * (r - 1))), int(round(cy + np.sin(a) * (r - 1))), "#2a2838")
        for a in np.linspace(0, np.pi, 4, endpoint=False):
            cv.line(int(cx + np.cos(a) * (r - 2)), int(cy + np.sin(a) * (r - 2)), int(cx - np.cos(a) * (r - 2)), int(cy - np.sin(a) * (r - 2)), C("#a3a9b8", 0.6))
        cv.rect(cx - 1, cy - 1, 3, 3, "#a3a9b8")
    (ax, ay), (bx, by) = wheels
    mid = (ax + bx) // 2
    crank = (mid - 2, base - r - 1)
    seat = (mid - 7 if not flip else mid + 7, base - 2 * r - 5)
    head = (bx - 5 if not flip else bx + 5, base - 2 * r - 5)
    for p, q in [((ax, ay), crank), (crank, seat), (seat, (ax, ay)), (seat, head), (crank, head), (head, (bx, by))]:
        cv.line(p[0], p[1], q[0], q[1], frame)
        cv.line(p[0], p[1] - 1, q[0], q[1] - 1, hi)
    cv.rect(seat[0] - 4, seat[1] - 3, 9, 3, OUT)
    d = 1 if not flip else -1
    cv.line(head[0], head[1], head[0] + 2 * d, head[1] - 6, OUT); cv.rect(head[0] - 3 + d * 2, head[1] - 7, 8, 2, OUT)
    cv.ellipse(crank[0] - 3, crank[1] - 3, 7, 7, "#a3a9b8"); cv.px(crank[0], crank[1], OUT)


def bike_rack(width=180, height=30, seed=0):
    """A row of black wave-hoop bike racks with three bikes locked to it (one with a basket,
    one missing its front wheel the way bikes on campus do)."""
    cv = Canvas(width + 12, height + 14, seed=seed)
    ox, base = 6, height + 10
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    # hoops
    hoops = list(range(ox + 6, ox + width - 10, 30))
    for hx in hoops:
        for a in np.linspace(np.pi, 2 * np.pi, 40):
            cv.px(int(round(hx + 10 + np.cos(a) * 10)), int(round(base - 2 + np.sin(a) * (height - 6))), OUT)
        for a in np.linspace(np.pi, 2 * np.pi, 40):
            cv.px(int(round(hx + 10 + np.cos(a) * 9)), int(round(base - 2 + np.sin(a) * (height - 7))), "#3a3a48")
        cv.vline(hx, base - 3, 3, OUT); cv.vline(hx + 20, base - 3, 3, OUT)
    cv.rect(ox, base - 2, width, 2, "#24222e")
    # bikes
    bike(cv, ox + 2, base, frame="#3a4f8a", hi="#5671b0", r=10)
    bike(cv, ox + 62, base, frame="#8a3a3a", hi="#b05656", r=10, flip=True)
    bike(cv, ox + 122, base, frame="#3a6a5a", hi="#5a8a76", r=10)
    # a basket on the green one and a U-lock on the red one
    cv.rect(ox + 162, base - 31, 10, 6, OUT); cv.rect(ox + 163, base - 30, 8, 4, "#8a6a3a")
    for k in range(0, 8, 2):
        cv.vline(ox + 163 + k, base - 30, 4, "#6a4a2a")
    cv.rect(ox + 92, base - 18, 2, 6, "#e8b45c"); cv.rect(ox + 92, base - 18, 6, 2, "#e8b45c")
    return cv, ox + width // 2, base


def sawhorse_table(width=180, height=40, seed=0):
    """Outdoor work table: two sawhorses, a plywood top with deck boards being cut, a circular
    saw, clamps, a tape measure, a work light clamped on, a cord running off."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 8, height + 14, seed=seed)
    ox, base = 4, height + 10
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    top = base - 22
    # sawhorses (splayed legs)
    for sx in (ox + 18, ox + width - 30):
        for lx, d in ((sx, -1), (sx + 12, 1)):
            cv.line(lx, top + 3, lx + d * 4, base - 1, OUT); cv.line(lx + 1, top + 3, lx + 1 + d * 4, base - 1, PLY[3])
        cv.rect(sx - 2, top + 1, 18, 3, OUT); cv.hline(sx - 1, top + 2, 16, PLY[4])
        cv.line(sx, base - 8, sx + 12, base - 8, PLY[2])
    # plywood sheet
    cv.rect(ox, top - 4, width, 6, OUT)
    cv.rect(ox + 1, top - 3, width - 2, 3, PLY[5]); cv.hline(ox + 1, top - 3, width - 2, PLY[6])
    cv.hline(ox + 1, top, width - 2, PLY[2])
    for gx in range(ox + 6, ox + width - 6, 11):
        cv.hline(gx, top - 2, int(rng.integers(3, 8)), PLY[4])
    # deck boards on top, pencil marks, offcuts
    for j, (bx, L) in enumerate([(ox + 10, 74), (ox + 14, 70), (ox + 92, 40)]):
        y0 = top - 7 - (j % 2) * 3
        cv.rect(bx, y0, L, 4, OUT); cv.rect(bx + 1, y0 + 1, L - 2, 2, PLY[4]); cv.hline(bx + 1, y0 + 1, L - 2, PLY[6])
        for mx in range(bx + 10, bx + L - 4, 16):
            cv.vline(mx, y0 + 1, 2, "#3a3a48")
    for k in range(3):
        cv.rect(ox + 140 + k * 6, top - 5, 4, 2, PLY[5])
    # circular saw
    sx0 = ox + 100
    cv.rect(sx0, top - 13, 18, 6, OUT); cv.rect(sx0 + 1, top - 12, 16, 4, "#2a6a9a"); cv.hline(sx0 + 1, top - 12, 16, "#4a8aba")
    cv.ellipse(sx0 + 2, top - 15, 10, 8, STEEL[5]); cv.ellipse(sx0 + 4, top - 13, 6, 4, STEEL[3])
    cv.rect(sx0 + 12, top - 17, 6, 4, OUT); cv.rect(sx0 + 13, top - 16, 4, 2, "#2a2a34")
    # bar clamps
    for cx_ in (ox + 30, ox + 66):
        cv.rect(cx_, top - 12, 2, 12, STEEL[5]); cv.rect(cx_ - 2, top - 12, 6, 2, "#c84a3c"); cv.rect(cx_ - 2, top + 1, 6, 2, "#c84a3c")
    # tape measure and pencil
    cv.rect(ox + 132, top - 9, 7, 6, OUT); cv.rect(ox + 133, top - 8, 5, 4, "#e8b45c"); cv.hline(ox + 139, top - 5, 10, "#e8d070")
    cv.line(ox + 150, top - 4, ox + 158, top - 6, "#e8b45c")
    # clamp-on work light at the right end
    lx = ox + width - 12
    cv.rect(lx, top - 8, 3, 8, OUT); cv.line(lx + 1, top - 8, lx - 4, top - 20, STEEL[4])
    cv.poly([(lx - 10, top - 24), (lx - 1, top - 24), (lx + 1, top - 18), (lx - 12, top - 18)], OUT)
    cv.poly([(lx - 9, top - 23), (lx - 2, top - 23), (lx, top - 19), (lx - 11, top - 19)], CRANE[3])
    cv.hline(lx - 11, top - 18, 12, WARM[4])
    # orange extension cord down the leg and off along the ground
    cv.line(ox + width - 6, top + 1, ox + width - 2, base - 2, "#d86a2a")
    cv.line(ox + width - 2, base - 2, ox + width + 3, base - 1, "#d86a2a")
    return cv, ox + width // 2, base


def notice_stand(width=90, height=48, label="ASK FIRST"):
    """A steel notice board on two posts: header ASK FIRST, the printed rule ASK BEFORE LIFTING,
    and a second line added below in marker (Cal's handwriting: ASK FOR HELP)."""
    cv = Canvas(width + 6, height + 8, seed=17)
    ox, base = 3, height + 5
    ground_shadow(cv, ox + width // 2, base, width // 2 - 8, 2)
    for px_ in (ox + 10, ox + width - 14):
        cv.rect(px_, base - 16, 4, 16, OUT); cv.vline(px_ + 1, base - 15, 14, STEEL[4]); cv.vline(px_ + 2, base - 15, 14, STEEL[2])
    bt = base - height
    cv.rect(ox, bt, width, height - 14, OUT)
    cv.rect(ox + 1, bt + 1, width - 2, height - 16, STEEL[3]); cv.hline(ox + 1, bt + 1, width - 2, STEEL[5])
    # header band
    cv.rect(ox + 3, bt + 3, width - 6, 11, SAFETY[2]); cv.hline(ox + 3, bt + 3, width - 6, SAFETY[3])
    text(cv, label, ox + width // 2 - text_width(label) // 2, bt + 3, "#1a1420")
    # printed sheet
    py = bt + 16
    cv.rect(ox + 4, py, width - 8, height - 33, PAPER[2]); cv.hline(ox + 4, py, width - 8, PAPER[3])
    for k, L in enumerate([60, 52, 44]):
        cv.hline(ox + 8, py + 3 + k * 3, L, "#5a4a44")
    # marker line, slanted and blue
    for k in range(0, 46):
        cv.px(ox + 14 + k, py + 13 - (k // 15), "#2a4a9a")
        if k % 5 == 0:
            cv.px(ox + 14 + k, py + 12 - (k // 15), "#2a4a9a")
    cv.px(ox + width // 2, bt + 15, "#c84a3c")
    return cv, ox + width // 2, base


def concrete_planter(width=88, height=44, seed=0):
    """Board-formed concrete planter with ornamental grasses, a low juniper and asters."""
    rng = np.random.default_rng(seed)
    cv = Canvas(width + 6, height + 12, seed=seed)
    ox, base = 3, height + 8
    ground_shadow(cv, ox + width // 2, base, width // 2, 3)
    face_top = base - 22
    # plants first
    bush = shrub(0, 0, 34, 20, seed=seed + 1, palette=LEAF)
    cv.paste(bush, ox + 4, face_top - 18)
    bush2 = shrub(0, 0, 22, 14, seed=seed + 2, palette=LEAF, flowers=["#a88ad8", "#c8a8e8"])
    cv.paste(bush2, ox + width - 28, face_top - 12)
    for gx in range(ox + 36, ox + width - 26, 3):
        hh = int(rng.integers(12, 22))
        lean = int(rng.integers(-3, 4))
        cv.line(gx, face_top + 1, gx + lean, face_top - hh, "#8a845a")
        cv.line(gx + 1, face_top + 1, gx + 1 + lean, face_top - hh + 3, "#b0a670")
        cv.px(gx + lean, face_top - hh, "#d8cc94")
    # concrete box
    cv.rect(ox, face_top - 2, width, 22, OUT)
    cv.rect(ox + 1, face_top + 2, width - 2, 17, CONC[5])
    for yy in range(face_top + 4, face_top + 19, 3):
        cv.hline(ox + 1, yy, width - 2, CONC[4])
    for tx in range(ox + 8, ox + width - 4, 16):
        cv.px(tx, face_top + 10, CONC[2])
    cv.rect(ox - 1, face_top - 3, width + 2, 5, OUT)
    cv.rect(ox, face_top - 2, width, 3, CONC[7]); cv.hline(ox, face_top - 2, width, CONC[8])
    cv.rect(ox + 1, face_top + 1, width - 2, 1, CONC[3])
    cv.hline(ox + 1, base - 3, width - 2, CONC[3])
    return cv, ox + width // 2, base


def eng_deer():
    """Mule deer frames (grazing, head up) for the shared fauna sheet."""
    graze = [
        "..........................",
        "..........................",
        "..........................",
        "..........................",
        "..........................",
        "..........................",
        "........kkkkkkkkkkkk......",
        ".......khhhhhhhhhhhhkk....",
        "......khhbbbbbbbbbhhhhk...",
        ".....khbbbbbbbbbbbbbbhk...",
        "....kkbbbbbbbbbbbbbbbbk...",
        "...kwkbbbbbbbbbbbbbbbbk...",
        "...kwkbbbbbbbbbbbbbbbk....",
        "....kkbbbbdddddbbbbbbk....",
        ".....kbbkkk...kkbbkbbk....",
        ".....kbk........kbkkbk....",
        "...kkkbk........kbk.kbk...",
        "..kddkbk........kbk..kbk..",
        ".kdddkbk........kbk..kbk..",
        "kedddkbk........kbk..kbk..",
        "kkddk.kk........kk...kk...",
        ".kkk.....................",
    ]
    up = [
        "...k.k....................",
        "..kdkdk...................",
        "..kdddk...................",
        ".kkdddk...................",
        "kndddkk...................",
        "kkdedk....................",
        "..kddkkkkkkkkkkkkk........",
        "..kdkhhhhhhhhhhhhhkk......",
        "...kkhbbbbbbbbbbhhhhk.....",
        "....khbbbbbbbbbbbbbhk.....",
        "....kbbbbbbbbbbbbbbbbk....",
        "...kkbbbbbbbbbbbbbbbbk....",
        "...kwkbbbbbbbbbbbbbbk.....",
        "....kkbbbbdddddbbbbbk.....",
        ".....kbbkkk...kkbbkbk.....",
        ".....kbk........kbkkbk....",
        ".....kbk........kbk.kbk...",
        ".....kbk........kbk..kbk..",
        ".....kbk........kbk..kbk..",
        ".....kbk........kbk..kbk..",
        ".....kk.........kk...kk...",
        "..........................",
    ]
    w = max(len(r) for r in graze + up)
    fix = lambda rows: [r.ljust(w, ".") for r in rows]
    pal = {"k": "#1a1418", "b": "#7a5a44", "h": "#94704e", "d": "#5e4232", "w": "#e6d6c0", "e": "#0b070c", "n": "#2a1a14"}
    return [fix(graze), fix(up)], pal


# =============================================================================================
# interiors (E02 workshop, E03 test floor, E04 model level, E05 control booth)
# =============================================================================================

# warm buff painted block above a dark blue-grey painted dado
BLOCK_E = ["#3a3432", "#544a44", "#6a5e54", "#7e7062", "#8c7e6e", "#9c8e7c", "#ae9f8c", "#c2b29c"]
DADO_E = ["#141820", "#1c222c", "#262e3a", "#2f3946", "#384454", "#445264", "#55647a", "#687a92"]
MACHINE = ["#1a2622", "#26362f", "#33483e", "#42594c", "#55705f", "#6e8a76", "#8ea692"]
LOCKER = ["#1a2230", "#243042", "#2f3e54", "#3c4e68", "#4c6280", "#62789a", "#8096b4"]
BOARD = ["#9aa2aa", "#b4bcc2", "#c8ced2", "#dadee0", "#e8eaea"]
MARKER = {"blue": "#2c4a9a", "red": "#c03a32", "black": "#262830", "green": "#2a7a4a"}

# a 3x5 pixel font (variable width for M N W) for tags, labels and log sheets
MICRO = {
    "A": [".#.", "#.#", "###", "#.#", "#.#"], "B": ["##.", "#.#", "##.", "#.#", "##."],
    "C": [".##", "#..", "#..", "#..", ".##"], "D": ["##.", "#.#", "#.#", "#.#", "##."],
    "E": ["###", "#..", "##.", "#..", "###"], "F": ["###", "#..", "##.", "#..", "#.."],
    "G": [".##", "#..", "#.#", "#.#", ".##"], "H": ["#.#", "#.#", "###", "#.#", "#.#"],
    "I": ["###", ".#.", ".#.", ".#.", "###"], "J": ["..#", "..#", "..#", "#.#", ".#."],
    "K": ["#.#", "#.#", "##.", "#.#", "#.#"], "L": ["#..", "#..", "#..", "#..", "###"],
    "M": ["#...#", "##.##", "#.#.#", "#...#", "#...#"], "N": ["#..#", "##.#", "#.##", "#..#", "#..#"],
    "O": ["###", "#.#", "#.#", "#.#", "###"], "P": ["##.", "#.#", "##.", "#..", "#.."],
    "Q": [".#.", "#.#", "#.#", "##.", ".##"], "R": ["##.", "#.#", "##.", "#.#", "#.#"],
    "S": [".##", "#..", ".#.", "..#", "##."], "T": ["###", ".#.", ".#.", ".#.", ".#."],
    "U": ["#.#", "#.#", "#.#", "#.#", "###"], "V": ["#.#", "#.#", "#.#", "#.#", ".#."],
    "W": ["#...#", "#...#", "#.#.#", "##.##", "#...#"], "X": ["#.#", "#.#", ".#.", "#.#", "#.#"],
    "Y": ["#.#", "#.#", ".#.", ".#.", ".#."], "Z": ["###", "..#", ".#.", "#..", "###"],
    "0": [".#.", "#.#", "#.#", "#.#", ".#."], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["##.", "..#", ".#.", "#..", "###"], "3": ["##.", "..#", ".#.", "..#", "##."],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "##.", "..#", "##."],
    "6": [".##", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "##."],
    "-": ["...", "...", "###", "...", "..."], ".": [".", ".", ".", ".", "#"],
    ":": [".", "#", ".", "#", "."], "/": ["..#", "..#", ".#.", "#..", "#.."],
    "?": ["##.", "..#", ".#.", "...", ".#."], "!": ["#", "#", "#", ".", "#"],
    "'": ["#", "#", ".", ".", "."], "+": ["...", ".#.", "###", ".#.", "..."],
    "&": [".#.", "#.#", ".#.", "#.#", ".##"], "%": ["#.#", "..#", ".#.", "#..", "#.#"],
    "<": ["..#", ".#.", "#..", ".#.", "..#"], ">": ["#..", ".#.", "..#", ".#.", "#.."],
    "=": ["...", "###", "...", "###", "..."], "#": ["#.#", "###", "#.#", "###", "#.#"],
}


def micro_width(s):
    w = 0
    for ch in s.upper():
        g = MICRO.get(ch)
        w += (len(g[0]) if g else 2) + 1
    return max(0, w - 1)


def micro_text(cv, s, x, y, colour):
    """Tiny 3x5 lettering (tags, rack labels, log lines). Returns the width drawn."""
    cx = x
    for ch in s.upper():
        g = MICRO.get(ch)
        if g is None:
            cx += 3
            continue
        for r, row in enumerate(g):
            for k, c in enumerate(row):
                if c == "#":
                    cv.px(cx + k, y + r, colour)
        cx += len(g[0]) + 1
    return cx - x - 1


def scribble(cv, x, y, w, colour, seed=0, rows=1, gap=3):
    """Handwritten lines too small to read: short dashes with tiny ascenders."""
    rng = np.random.default_rng(seed)
    for r in range(rows):
        xx, yy = x, y + r * gap
        end = x + w - int(rng.integers(0, max(1, w // 3))) if r == rows - 1 else x + w
        while xx < end:
            run = int(rng.integers(2, 6))
            cv.hline(xx, yy, min(run, end - xx), colour)
            if rng.random() < 0.3:
                cv.px(xx + int(rng.integers(0, run)), yy - 1, colour)
            xx += run + 1


# --------------------------------------------------------------------------------- surfaces

def painted_block(cv, x, y, w, h, seed=0, pal=BLOCK_E, course=8, length=16):
    """Painted concrete block in running bond: a lit top edge on every block, a few blocks a tone
    off, recessed mortar a tone darker. pal needs 7+ tones (mortar 2, body 4/5, odd 3, lit 6)."""
    xs, ys = grid(w, h)
    row = (ys + y) // course
    off = (row % 2) * (length // 2)
    col = (xs + x + off) // length
    ix = (xs + x + off) % length
    iy = (ys + y) % course
    pal_ = P(pal)
    v = hashn(col, row, seed)
    idx = np.where(v < 0.6, 4, np.where(v < 0.86, 5, 3))
    top = iy == 0
    idx = np.where(top, np.minimum(idx + 2, len(pal) - 1), idx)
    idx = np.where((iy == course - 2) & (v < 0.6), 3, idx)
    fine = hashn(xs + x, ys + y, seed + 3)
    idx = np.where((fine > 0.985) & ~top, idx - 1, idx)
    mort = (iy == course - 1) | (ix == length - 1)
    idx = np.where(mort, 2, idx)
    put_rgb(cv, x, y, P(pal)[idx])


def dado(cv, x, y, w, h, seed=0, stripe=True):
    """Dark painted block dado with a safety-yellow stripe on top and a rubber cove base."""
    painted_block(cv, x, y, w, h, seed, pal=DADO_E)
    if stripe:
        cv.rect(x, y - 3, w, 3, SAFETY[2]); cv.hline(x, y - 3, w, SAFETY[3]); cv.hline(x, y - 1, w, SAFETY[1])
    cv.rect(x, y + h - 3, w, 3, "#121218"); cv.hline(x, y + h - 3, w, "#2a2a34")


def steel_ceiling(cv, x, w, y=0, h=22, seed=0):
    """Corrugated roof deck over a steel girder along the wall line, with the girder's shadow."""
    cv.rect(x, y, w, h, STEEL[1])
    for xx in range(x, x + w):
        k = (xx - x) % 8
        c = STEEL[2] if k < 4 else STEEL[1]
        if k == 0:
            c = STEEL[3]
        cv.vline(xx, y, 9, c)
    cv.hline(x, y + 9, w, STEEL[0])
    # girder: top flange, web, bottom flange catching light from below
    cv.rect(x, y + 10, w, 2, STEEL[3]); cv.hline(x, y + 10, w, STEEL[4])
    cv.rect(x, y + 12, w, 5, STEEL[2])
    cv.rect(x, y + 17, w, 2, STEEL[4]); cv.hline(x, y + 18, w, STEEL[5])
    for sx in range(x + 30, x + w, 96):
        cv.rect(sx, y + 11, 8, 7, STEEL[3])
        for by in (12, 15):
            cv.px(sx + 2, y + by, STEEL[6]); cv.px(sx + 5, y + by, STEEL[6])
    cv.rect(x, y + 19, w, h - 19, C(SHADOW, 0.55))


def clerestory(cv, x, y, w, h, seed=0, bay=40, win=30):
    """A band of high windows onto the night: flat sky bands, a few stars, steel mullions.
    Returns star points for a twinkle layer."""
    rng = np.random.default_rng(seed)
    pts = []
    cv.rect(x, y, w, h, CONC[2]); cv.hline(x, y, w, CONC[1]); cv.hline(x, y + h - 1, w, CONC[4])
    for wx in range(x + (bay - win) // 2, x + w - win + 1, bay):
        cv.rect(wx - 1, y + 2, win + 2, h - 4, STEEL[0])
        gy0, gh = y + 3, h - 6
        bands = NIGHT_BANDS[:4]
        for k in range(gh):
            cv.hline(wx, gy0 + k, win, bands[min(3, k * 4 // gh)])
        for _ in range(2):
            sx, sy = wx + int(rng.integers(2, win - 2)), gy0 + int(rng.integers(1, gh - 3))
            cv.px(sx, sy, "#c8ccec")
            pts.append((sx, sy, "#e8ecff"))
        # mullions and a diagonal reflection
        cv.vline(wx + win // 2, gy0, gh, STEEL[2])
        cv.hline(wx, gy0 + gh // 2, win, STEEL[2])
        cv.line(wx + 3, gy0 + gh - 2, wx + 9, gy0 + 1, C("#8a90c0", 0.35))
        cv.hline(wx - 1, y + h - 3, win + 2, CONC[5])
    return pts


def dome_pendant(cv, x, y_top, drop, lit=True, shade_col=None):
    """Industrial dome pendant on a cord; returns the bulb point."""
    sc = shade_col or ["#1e2a26", "#2e4038", "#40584c", "#56725f"]
    cv.vline(x, y_top, drop, "#141218")
    y = y_top + drop
    cv.rect(x - 1, y - 3, 3, 4, STEEL[3])
    cv.poly([(x - 3, y), (x + 3, y), (x + 10, y + 7), (x - 10, y + 7)], OUT)
    cv.poly([(x - 2, y + 1), (x + 2, y + 1), (x + 8, y + 6), (x - 8, y + 6)], sc[2])
    cv.line(x - 2, y + 1, x - 8, y + 6, sc[3]); cv.line(x - 1, y + 1, x - 6, y + 5, sc[3])
    cv.hline(x - 10, y + 7, 21, sc[1]); cv.hline(x - 9, y + 7, 4, sc[3])
    if lit:
        cv.rect(x - 6, y + 8, 13, 1, WARM[3]); cv.rect(x - 3, y + 8, 7, 2, WARM[4])
        halo(cv, x, y + 10, 18, "#f6cf7a", 0.07, 3)
    return (x, y + 9)


def dust_duct(cv, x0, x1, y, d=7, drops=()):
    """Galvanised dust-collection duct along the wall with riveted seams and drops to machines
    (each drop: (x, y_end)) with a yellow blast gate."""
    cv.rect(x0, y, x1 - x0, d, STEEL[3])
    cv.hline(x0, y, x1 - x0, STEEL[5]); cv.hline(x0, y + 1, x1 - x0, STEEL[6]); cv.hline(x0, y + 2, x1 - x0, STEEL[5])
    cv.hline(x0, y + d - 1, x1 - x0, STEEL[2])
    for sx in range(x0 + 10, x1, 26):
        cv.vline(sx, y, d, STEEL[2]); cv.vline(sx + 1, y, d, STEEL[6])
    for sx in range(x0 + 40, x1, 120):
        cv.rect(sx, y - 3, 2, 3, STEEL[1])          # hanger strap
    for (dx, ye) in drops:
        cv.rect(dx - 2, y + d, 5, ye - y - d, STEEL[3]); cv.vline(dx - 1, y + d, ye - y - d, STEEL[6]); cv.vline(dx + 2, y + d, ye - y - d, STEEL[2])
        gy = y + d + 6
        cv.rect(dx - 3, gy, 7, 3, SAFETY[2]); cv.hline(dx - 3, gy, 7, SAFETY[3]); cv.rect(dx + 4, gy + 1, 3, 1, SAFETY[1])


def epoxy_np(w, h, seed=0, pal=EPOXY):
    """Sealed workshop floor as an array: soft trowelled patches in three tones, sparse colour
    flecks, never noisy."""
    xs, ys = grid(w, h)
    p = P(pal)
    f = 0.7 * soft_field(w, h, 70, seed) + 0.3 * soft_field(w, h, 23, seed + 1)
    idx = np.where(f < 0.22, 3, np.where(f < 0.72, 4, 5))
    fine = hashn(xs, ys, seed + 5)
    idx = np.where(fine > 0.993, np.minimum(idx + 2, len(pal) - 1), idx)
    idx = np.where(fine < 0.006, idx - 2, idx)
    return p[idx]


def control_joints(cv, x, y, w, h, colour, every_x=128, every_y=86, x_off=0):
    """Saw-cut control joints (a dark line with a lit lip)."""
    for jx in range(x + x_off, x + w, every_x):
        cv.vline(jx, y, h, C(colour, 0.55)); cv.vline(jx + 1, y, h, C("#ffffff", 0.05))
    for jy in range(y + every_y, y + h, every_y):
        cv.hline(x, jy, w, C(colour, 0.55)); cv.hline(x, jy + 1, w, C("#ffffff", 0.05))


def rubber_mat(cv, x, y, w, h, edge=None):
    """Anti-fatigue mat: black rubber with a grid of drain holes and a bevelled yellow edge."""
    cv.rect(x, y, w, h, "#34373e")
    for yy in range(y + 3, y + h - 2, 4):
        for xx in range(x + 3 + (yy // 4 % 2) * 2, x + w - 2, 4):
            cv.px(xx, yy, "#1c1d23"); cv.px(xx, yy - 1, "#3a3d44")
    e = edge or SAFETY[2]
    cv.rect(x, y, w, 2, e); cv.rect(x, y + h - 2, w, 2, e)
    cv.rect(x, y, 2, h, e); cv.rect(x + w - 2, y, 2, h, e)
    cv.hline(x, y, w, SAFETY[3]); cv.hline(x, y + h - 1, w, SAFETY[1])
    cv.rect(x + 2, y + h - 2, w - 4, 2, C(SHADOW, 0.0))


def sawdust(cv, cx, cy, rx, ry, seed=0, col=None):
    """Flat drifts of sawdust and a few curls of shaving."""
    rng = np.random.default_rng(seed)
    c = col or ["#a88a60", "#c4a674", "#dcc08c"]
    for _ in range(rx * ry // 3):
        a, r = rng.random() * 6.283, rng.random() ** 0.7
        x, y = int(cx + np.cos(a) * rx * r), int(cy + np.sin(a) * ry * r)
        cv.px(x, y, C(c[int(rng.integers(0, 3))], 0.85))
    for _ in range(3):
        x, y = cx + int(rng.integers(-rx, rx)), cy + int(rng.integers(-ry, ry))
        cv.hline(x, y, 3, c[2]); cv.px(x + 3, y - 1, c[1]); cv.px(x - 1, y + 1, c[1])


def floor_cord(cv, pts, colour="#d46a24", hi="#f09a48"):
    """An extension cord lying flat on the floor along a polyline."""
    for (a, b) in zip(pts, pts[1:]):
        cv.line(a[0], a[1] + 1, b[0], b[1] + 1, C(SHADOW, 0.5))
        cv.line(a[0], a[1], b[0], b[1], colour)
    for (a, b) in zip(pts, pts[1:]):
        if abs(b[0] - a[0]) > abs(b[1] - a[1]):
            cv.px((a[0] + b[0]) // 2, (a[1] + b[1]) // 2 - 0, hi)


def floor_drain(cv, cx, cy, w=14, h=6):
    cv.rect(cx - w // 2 - 1, cy - h // 2 - 1, w + 2, h + 2, CONC[1])
    cv.rect(cx - w // 2, cy - h // 2, w, h, "#0e0e14")
    for xx in range(cx - w // 2 + 1, cx + w // 2, 2):
        cv.vline(xx, cy - h // 2, h, STEEL[3])
    cv.hline(cx - w // 2 - 1, cy - h // 2 - 1, w + 2, CONC[5])


def front_wall(cv, y, w, h, gaps=(), cap=CONC[5]):
    """The near wall seen from above: a lit capping line, then the dark wall face below it,
    interrupted by doorway gaps [(x0, x1)]."""
    cv.rect(0, y, w, h, "#0e0d14")
    cv.hline(0, y, w, cap); cv.hline(0, y + 1, w, CONC[3]); cv.rect(0, y + 2, w, 2, CONC[1])
    for (x0, x1) in gaps:
        cv.rect(x0, y, x1 - x0, h, "#0e0d14")


def door_gap(cv, x0, x1, y, h, outside="night"):
    """A doorway through the near wall (seen from above): lit jamb caps, the floor running on
    under a steel threshold, then the next space: the night court (asphalt, a painted line, cool
    light) or the warm-lit test floor (concrete and a hazard edge)."""
    w = x1 - x0
    cv.rect(x0, y, w, h, EPOXY[3])
    cv.rect(x0, y + 4, w, 3, STEEL[4]); cv.hline(x0, y + 4, w, STEEL[6]); cv.hline(x0, y + 6, w, STEEL[2])
    oy = y + 7
    if outside == "night":
        cv.rect(x0, oy, w, h - 7, ASPH[3])
        for k in range(0, h - 7, 4):
            cv.hline(x0, oy + k, w, ASPH[2])
        cv.rect(x0 + w // 2 - 1, oy + 3, 3, h - 10, C(SAFETY[2], 0.5))
        tint_rect(cv, x0, oy, w, h - 7, "#7088d0", 0.16)
    else:
        cv.rect(x0, oy, w, h - 7, CONC[5])
        for k in range(0, h - 7, 6):
            cv.hline(x0, oy + k, w, CONC[4])
        hazard_band(cv, x0, oy + 2, w, 4)
        tint_rect(cv, x0, oy, w, h - 7, "#f6cf7a", 0.12)
    # jambs: the cut ends of the near wall, lit on top
    for jx, lit_side in ((x0 - 5, 0), (x1, 4)):
        cv.rect(jx, y, 5, h, CONC[2]); cv.vline(jx + lit_side, y, h, CONC[5])
        cv.rect(jx, y, 5, 2, CONC[6])


# --------------------------------------------------------------------------- wall fixtures

def drill_press(cv, x, base):
    """Floor drill press against the wall (machine green), ~28 wide, 58 tall. x = left edge."""
    m = MACHINE
    cv.rect(x + 1, base - 5, 24, 5, OUT); cv.rect(x + 2, base - 4, 22, 3, m[3]); cv.hline(x + 2, base - 4, 22, m[5])
    cv.rect(x + 15, base - 50, 4, 46, OUT); cv.vline(x + 16, base - 49, 44, STEEL[6]); cv.vline(x + 17, base - 49, 44, STEEL[4])
    # table on its collar
    cv.rect(x + 13, base - 24, 8, 5, m[2])
    cv.rect(x + 3, base - 26, 18, 4, OUT); cv.rect(x + 4, base - 25, 16, 2, STEEL[5]); cv.hline(x + 4, base - 25, 16, STEEL[6])
    cv.rect(x + 8, base - 28, 6, 2, PLY[4])                       # a scrap block in the vice
    # head, belt cover and motor
    cv.rect(x + 5, base - 56, 22, 18, OUT)
    cv.rect(x + 6, base - 55, 20, 16, m[4]); cv.hline(x + 6, base - 55, 20, m[6]); cv.vline(x + 25, base - 55, 16, m[2])
    cv.rect(x + 6, base - 59, 16, 4, OUT); cv.rect(x + 7, base - 58, 14, 3, m[5]); cv.hline(x + 7, base - 58, 14, m[6])
    cv.rect(x + 22, base - 53, 6, 10, m[2]); cv.vline(x + 27, base - 53, 10, OUT)
    cv.rect(x + 8, base - 50, 7, 3, SAFETY[3]); cv.hline(x + 9, base - 49, 5, SAFETY[1])
    # quill, chuck, bit
    cv.rect(x + 10, base - 39, 3, 5, STEEL[5]); cv.rect(x + 9, base - 34, 5, 3, STEEL[4]); cv.vline(x + 11, base - 31, 3, STEEL[6])
    # feed handles with black knobs
    hx, hy = x + 23, base - 44
    for (ex, ey) in ((x + 30, base - 48), (x + 29, base - 38), (x + 25, base - 36)):
        cv.line(hx, hy, ex, ey, STEEL[5]); cv.rect(ex - 1, ey - 1, 2, 2, OUT)
    cv.rect(hx - 1, hy - 1, 3, 3, STEEL[3])
    cv.rect(x + 2, base - 1, 24, 1, C(SHADOW, 0.5))


def bandsaw(cv, x, base):
    """Vertical bandsaw: stand, two wheel housings, table, blade guard. ~30 wide, 68 tall."""
    m = MACHINE
    cv.rect(x + 3, base - 24, 22, 24, OUT); cv.rect(x + 4, base - 23, 20, 22, m[2]); cv.hline(x + 4, base - 23, 20, m[4])
    cv.rect(x + 7, base - 18, 14, 8, m[1]); cv.hline(x + 7, base - 18, 14, m[3])
    for (yy, hh) in ((base - 42, 19), (base - 68, 20)):
        cv.rect(x + 1, yy, 26, hh, OUT)
        cv.rect(x + 2, yy + 1, 24, hh - 2, m[4]); cv.hline(x + 3, yy + 1, 22, m[6]); cv.vline(x + 2, yy + 2, hh - 4, m[5])
        cv.vline(x + 25, yy + 2, hh - 4, m[2]); cv.hline(x + 3, yy + hh - 2, 22, m[2])
        bolt(cv, x + 14, yy + hh // 2, STEEL[6])
    cv.rect(x + 20, base - 50, 6, 10, OUT); cv.rect(x + 21, base - 49, 4, 8, m[3])
    cv.rect(x - 4, base - 46, 36, 4, OUT); cv.rect(x - 3, base - 45, 34, 2, STEEL[5]); cv.hline(x - 3, base - 45, 34, STEEL[7])
    cv.vline(x + 9, base - 50, 5, SAFETY[3]); cv.vline(x + 10, base - 50, 5, SAFETY[2]); cv.vline(x + 9, base - 45, 2, STEEL[7])
    cv.rect(x + 5, base - 64, 18, 7, "#e6d6b1"); micro_text(cv, "SAW", x + 9, base - 63, "#262830")
    cv.rect(x + 3, base - 1, 22, 1, C(SHADOW, 0.5))


def lockers(cv, x, y, n=4, lw=18, h=60, names=("CAL", "DEV", "", ""), seed=0):
    """A bank of steel lockers with vents, latches and paper name tags."""
    rng = np.random.default_rng(seed)
    L = LOCKER
    for i in range(n):
        lx = x + i * lw
        cv.rect(lx, y, lw, h, OUT)
        tone = L[3] if i % 2 == 0 else mix(L[3], L[4], 0.3)
        cv.rect(lx + 1, y + 1, lw - 2, h - 2, tone)
        cv.hline(lx + 1, y + 1, lw - 2, L[5]); cv.vline(lx + 1, y + 1, h - 2, L[4]); cv.vline(lx + lw - 2, y + 1, h - 2, L[2])
        for vy in (y + 4, y + 6, y + 8, y + h - 10, y + h - 8):
            cv.hline(lx + 4, vy, lw - 8, L[1])
        cv.rect(lx + lw - 6, y + h // 2 - 4, 2, 9, STEEL[6]); cv.px(lx + lw - 6, y + h // 2 + 4, STEEL[2])
        cv.rect(lx + 3, y + 13, lw - 6, 7, PAPER[3]); cv.hline(lx + 3, y + 19, lw - 6, PAPER[1])
        name = names[i] if i < len(names) else ""
        if name:
            micro_text(cv, name, lx + (lw - micro_width(name)) // 2, y + 14, MARKER["black"] if i else MARKER["red"])
        else:
            cv.hline(lx + 5, y + 16, lw - 10, PAPER[1])
        cv.hline(lx + 4, y + h - 2, lw - 8, C(SHADOW, 0.3))
    # a sticker on Dev's locker and a hard hat and a bike helmet on top
    if n > 1:
        sx = x + lw + 4
        cv.rect(sx, y + 26, 9, 5, "#e6d6b1"); cv.hline(sx + 1, y + 29, 7, MARKER["green"]); cv.px(sx + 2, y + 28, MARKER["green"]); cv.px(sx + 6, y + 28, MARKER["green"])
    cv.ellipse(x + 3, y - 6, 12, 8, OUT); cv.ellipse(x + 4, y - 5, 10, 7, SAFETY[3]); cv.hline(x + 1, y - 1, 16, SAFETY[1]); cv.px(x + 6, y - 4, "#fff0c4")
    cv.ellipse(x + lw * 2 + 3, y - 6, 12, 8, OUT); cv.ellipse(x + lw * 2 + 4, y - 5, 10, 7, "#2c4a8a"); cv.px(x + lw * 2 + 7, y - 4, "#5671b0")


def scope_frame(w, h, k, n, kind="sine"):
    """One animation frame of an oscilloscope screen (graticule plus a phosphor trace)."""
    cv = Canvas(w, h, fill=SCOPE[0])
    for gx in range(2, w, 4):
        for gy in range(2, h, 4):
            cv.px(gx, gy, SCOPE[1])
    cv.hline(0, h // 2, w, SCOPE[1]); cv.vline(w // 2, 0, h, SCOPE[1])
    ph = 6.2832 * k / n
    rng = np.random.default_rng(31 + k)
    prev = None
    for xx in range(w):
        t = xx / w
        if kind == "square":
            f = 1.0 if np.sin(6.2832 * t * 2 + ph) >= 0 else -1.0
        elif kind == "voice":
            env = 0.35 + 0.65 * abs(np.sin(6.2832 * t * 1.3 + ph * 0.5))
            f = env * np.sin(6.2832 * t * 7 + ph * 3) * (0.6 + 0.4 * rng.random())
        else:
            f = np.sin(6.2832 * t * 2 + ph)
        yy = int(round(h / 2 - 1 - f * (h / 2 - 3)))
        if prev is not None and abs(yy - prev) > 1:
            lo, hi = sorted((prev, yy))
            cv.vline(xx, lo, hi - lo + 1, SCOPE[3])
        cv.px(xx, yy, SCOPE[4])
        cv.px(xx, yy - 1, SCOPE[3])
        prev = yy
    return cv


def bench_supply(cv, x, y):
    """Bench power supply: two digit windows, knobs, red/black posts. Returns the digit rects."""
    cv.rect(x, y, 24, 14, OUT); cv.rect(x + 1, y + 1, 22, 12, "#c8c4b8"); cv.hline(x + 1, y + 1, 22, "#e6e2d6")
    rects = []
    for k, (dx, col) in enumerate(((3, "#ff6a4a"), (13, "#7ae0a0"))):
        cv.rect(x + dx, y + 3, 8, 5, "#14100c")
        for d in range(3):
            cv.rect(x + dx + 1 + d * 2 + (d > 0), y + 4, 1, 3, col)
        rects.append((x + dx, y + 3, 8, 5, col))
    for kx in (6, 16):
        cv.rect(x + kx, y + 10, 3, 2, OUT)
    cv.px(x + 21, y + 10, "#c42a2a"); cv.px(x + 21, y + 12, "#1a1418")
    return rects


def electronics_counter(cv, x, top, w, base, seed=0):
    """The electronics bench against the wall: ESD mat top, drawers below, an oscilloscope, a bench
    supply, a soldering station, a magnifier lamp, parts drawers and wire spools on the wall above.
    Returns positions for the animated layers."""
    rng = np.random.default_rng(seed)
    # parts-drawer cabinet and spool rod on the wall above
    px0, py0 = x + 6, top - 52
    cv.rect(px0, py0, 34, 26, OUT); cv.rect(px0 + 1, py0 + 1, 32, 24, "#3a4252")
    for r in range(4):
        for c in range(4):
            dx, dy = px0 + 2 + c * 8, py0 + 2 + r * 6
            cv.rect(dx, dy, 7, 5, "#8a96a8"); cv.hline(dx, dy, 7, "#b4c0d0"); cv.px(dx + 3, dy + 3, OUT)
            if rng.random() < 0.5:
                cv.px(dx + 1, dy + 1, ["#c84a3c", "#e8b45c", "#7ae0a0", "#5671b0"][int(rng.integers(0, 4))])
    rx0 = x + 48
    cv.hline(rx0, top - 40, 50, STEEL[4]); cv.rect(rx0, top - 42, 2, 4, STEEL[2]); cv.rect(rx0 + 48, top - 42, 2, 4, STEEL[2])
    for k, col in enumerate(("#c84a3c", "#2c4a9a", "#e8b45c", "#262830", "#2a7a4a")):
        sx = rx0 + 4 + k * 9
        cv.rect(sx, top - 46, 7, 11, OUT); cv.rect(sx + 1, top - 45, 5, 9, col); cv.vline(sx + 2, top - 45, 9, shade(col, 0.3))
        cv.rect(sx, top - 41, 7, 1, STEEL[5])
    # counter body
    cv.rect(x, top, w, base - top, OUT)
    cv.rect(x + 1, top + 1, w - 2, 4, "#3a5a78"); cv.hline(x + 1, top + 1, w - 2, "#5a7e9c")
    cv.rect(x + 1, top + 5, w - 2, 2, STEEL[5]); cv.hline(x + 1, top + 5, w - 2, STEEL[6])
    cv.rect(x + 1, top + 7, w - 2, base - top - 8, STEEL[2])
    for dx in range(x + 4, x + w - 20, 24):
        for k in range(3):
            dy = top + 9 + k * 7
            if dy + 6 > base - 2:
                break
            cv.rect(dx, dy, 20, 6, STEEL[3]); cv.hline(dx, dy, 20, STEEL[4]); cv.rect(dx + 7, dy + 2, 6, 1, STEEL[6])
    cv.rect(x + w - 18, top + 9, 14, base - top - 12, STEEL[1])        # knee space
    # oscilloscope
    ox, oy = x + 8, top - 22
    cv.rect(ox, oy, 38, 23, OUT); cv.rect(ox + 1, oy + 1, 36, 21, "#5a6272"); cv.hline(ox + 1, oy + 1, 36, "#7c8494")
    cv.rect(ox + 3, oy + 3, 24, 16, "#0a120e")
    screen = (ox + 4, oy + 4, 22, 14)
    for ky in range(4):
        cv.rect(ox + 30, oy + 4 + ky * 4, 3, 2, OUT); cv.px(ox + 34, oy + 4 + ky * 4, ["#c84a3c", "#e8b45c", "#3cba7a", "#5671b0"][ky])
    cv.line(ox + 32, oy + 22, ox + 40, top + 3, "#e8b45c"); cv.line(ox + 34, oy + 22, ox + 46, top + 3, "#5671b0")
    # bench supply
    sx, sy = x + 50, top - 14
    digits = bench_supply(cv, sx, sy)
    cv.line(sx + 20, sy + 13, sx + 30, top + 2, "#c42a2a"); cv.line(sx + 22, sy + 13, sx + 34, top + 3, OUT)
    # a small breadboard with LEDs on the mat
    bx = sx + 26
    cv.rect(bx, top + 1, 16, 3, "#e6e2d6"); cv.px(bx + 3, top + 1, "#c42a2a"); cv.px(bx + 8, top + 2, "#3cba7a"); cv.px(bx + 12, top + 1, "#e8b45c")
    # soldering station with the iron in its holder, the LED
    tx = x + w - 30
    cv.rect(tx, top - 8, 14, 9, OUT); cv.rect(tx + 1, top - 7, 12, 7, "#2a2a34"); cv.hline(tx + 1, top - 7, 12, "#44444f")
    led = (tx + 3, top - 5)
    cv.rect(tx + 6, top - 5, 5, 2, "#c84a3c")
    cv.line(tx + 14, top - 4, tx + 22, top - 14, STEEL[5]); cv.rect(tx + 20, top - 16, 3, 3, "#c84a3c")
    cv.ellipse(tx + 17, top - 2, 8, 3, "#c8a050")                         # brass tip cleaner
    return {"screen": screen, "digits": digits, "led": led}


def whiteboard_two_designs(cv, x, y, w, h):
    """Rolling-free wall whiteboard: Cal's floating arch for EVERY PLAN (no supports, red question
    marks at the ends) beside Dev's two spans on three piers FOR FEET, with a little walker."""
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT)
    cv.rect(x - 1, y - 1, w + 2, h + 2, STEEL[6]); cv.hline(x - 1, y - 1, w + 2, STEEL[7])
    cv.rect(x, y, w, h, BOARD[3])
    rng = np.random.default_rng(7)
    for _ in range(9):                                            # ghosts of old erased marker
        gx, gy = x + int(rng.integers(4, w - 30)), y + int(rng.integers(4, h - 8))
        cv.line(gx, gy, gx + int(rng.integers(10, 26)), gy + int(rng.integers(-3, 4)), BOARD[2])
    mid = x + w // 2
    for yy in range(y + 3, y + h - 3, 4):
        cv.vline(mid, yy, 2, MARKER["black"])
    B, R, K, G = MARKER["blue"], MARKER["red"], MARKER["black"], MARKER["green"]
    # --- Cal: the suspended arch
    lx0, lx1 = x + 10, mid - 10
    deck = y + h - 14
    micro_text(cv, "EVERY PLAN", x + 6, y + 4, B)
    cv.hline(x + 6, y + 10, micro_width("EVERY PLAN"), B)
    top_y = y + 13
    pts = []
    for xx in range(lx0, lx1 + 1):
        t = (xx - lx0) / (lx1 - lx0)
        yy = int(round(deck - 4 - (deck - 4 - top_y) * 4 * t * (1 - t)))
        pts.append((xx, yy))
        cv.px(xx, yy, B); cv.px(xx, yy + 1, B)
    for k in range(1, 10):
        hx, hy = pts[k * len(pts) // 10]
        cv.vline(hx, hy + 2, deck - hy - 2, B)
    cv.hline(lx0 - 3, deck, lx1 - lx0 + 7, B); cv.hline(lx0 - 3, deck + 1, lx1 - lx0 + 7, B)
    for ex in (lx0 - 4, lx1 + 4):
        cv.ellipse(ex - 4, deck - 4, 9, 9, R); cv.ellipse(ex - 3, deck - 3, 7, 7, BOARD[3])
        micro_text(cv, "?", ex - 1, deck + 5, R)
    micro_text(cv, "NO WAY DOWN", lx0 + 10, deck + 5, R)
    # --- Dev: two spans on three piers, ground hatch, a walker
    rx0, rx1 = mid + 10, x + w - 10
    micro_text(cv, "FOR FEET", mid + 6, y + 4, G)
    cv.hline(mid + 6, y + 10, micro_width("FOR FEET"), G)
    ground = y + h - 9
    cv.hline(rx0 - 4, ground, rx1 - rx0 + 8, K)
    for hx in range(rx0 - 3, rx1 + 4, 4):
        cv.line(hx, ground + 1, hx - 2, ground + 3, K)
    d2 = y + h - 20
    cv.hline(rx0, d2, rx1 - rx0, K); cv.hline(rx0, d2 + 1, rx1 - rx0, K)
    for px_ in (rx0, (rx0 + rx1) // 2, rx1 - 1):
        cv.rect(px_ - 2, d2 + 2, 4, ground - d2 - 2, C(K, 0.0)); cv.vline(px_ - 2, d2 + 2, ground - d2 - 2, K); cv.vline(px_ + 1, d2 + 2, ground - d2 - 2, K)
        cv.hline(px_ - 4, ground - 1, 8, G)
    # a stick figure halfway across
    fx = rx0 + (rx1 - rx0) // 3
    cv.rect(fx, d2 - 8, 2, 2, K); cv.vline(fx, d2 - 7, 4, K); cv.line(fx, d2 - 3, fx - 2, d2 - 1, K); cv.line(fx, d2 - 3, fx + 2, d2 - 1, K)
    cv.line(fx - 2, d2 - 6, fx + 2, d2 - 5, K)
    cv.line(rx1 - 6, y + 4, rx1 - 4, y + 7, G); cv.line(rx1 - 4, y + 7, rx1 + 1, y + 1, G)   # a tick
    # sticky note, magnet, marker tray
    cv.rect(x + w - 15, y + h - 13, 10, 9, "#e8d070"); scribble(cv, x + w - 14, y + h - 11, 7, "#8a7428", 1, rows=2)
    cv.rect(x + 3, y + h + 2, w - 6, 3, OUT); cv.rect(x + 4, y + h + 2, w - 8, 2, STEEL[5])
    for k, col in enumerate((B, R, G, K)):
        cv.rect(x + 12 + k * 9, y + h + 1, 7, 2, col)
    cv.rect(x + w - 30, y + h, 12, 3, "#2a2a34"); cv.hline(x + w - 30, y + h, 12, "#5a5a6a")


def blueprint_sheet(cv, x, y, w, h, seed=0):
    """A pinned blueprint: grid, a truss elevation in white lines, a title block."""
    BP = BLUEPRINT
    cv.rect(x, y, w, h, BP[2])
    for gx in range(x + 3, x + w, 5):
        cv.vline(gx, y + 1, h - 2, C(BP[3], 0.8))
    for gy in range(y + 3, y + h, 5):
        cv.hline(x + 1, gy, w - 2, C(BP[3], 0.8))
    by = y + h * 3 // 5
    cv.hline(x + 4, by, w - 8, BP[5]); cv.hline(x + 4, by - 8, w - 8, BP[5])
    for k, tx in enumerate(range(x + 4, x + w - 4, 6)):
        cv.line(tx, by, tx + 6, by - 8, BP[5]) if k % 2 == 0 else cv.line(tx, by - 8, tx + 6, by, BP[5])
    cv.vline(x + 4, by - 8, 8, BP[5]); cv.vline(x + w - 5, by - 8, 8, BP[5])
    cv.rect(x + w - 16, y + h - 8, 13, 6, C(BP[6], 0.0)); cv.hline(x + w - 16, y + h - 8, 13, BP[5]); cv.vline(x + w - 16, y + h - 8, 6, BP[5])
    scribble(cv, x + w - 14, y + h - 6, 10, BP[5], seed, rows=2, gap=2)
    micro_text(cv, "SPAN A", x + 4, y + 3, BP[6])
    cv.hline(x, y, w, BP[4]); cv.vline(x + w - 1, y, h, BP[1]); cv.hline(x, y + h - 1, w, BP[1])
    for (tx, ty) in ((x - 1, y - 1), (x + w - 4, y - 1)):
        cv.rect(tx, ty, 5, 3, C("#d8d4c0", 0.8))
    cv.poly([(x + w - 1, y + h - 7), (x + w - 1, y + h - 1), (x + w - 7, y + h - 1)], BP[4])


def safety_poster(cv, x, y, w, h, title, colour, icon="goggles"):
    """A small safety poster: coloured header with a title, a pictogram, lines of text."""
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#d8d2c4")
    cv.rect(x + 1, y + 1, w - 2, 7, colour)
    micro_text(cv, title, x + 1 + (w - 2 - micro_width(title)) // 2, y + 2, "#f4f0e6")
    cx, cy = x + w // 2, y + 8 + (h - 16) // 2
    if icon == "goggles":
        cv.rect(cx - 7, cy - 2, 6, 5, OUT); cv.rect(cx + 1, cy - 2, 6, 5, OUT)
        cv.rect(cx - 6, cy - 1, 4, 3, "#7ab4d4"); cv.rect(cx + 2, cy - 1, 4, 3, "#7ab4d4"); cv.hline(cx - 1, cy, 2, OUT)
        cv.hline(cx - 9, cy, 2, OUT); cv.hline(cx + 7, cy, 2, OUT)
    elif icon == "ears":
        cv.line(cx - 5, cy + 2, cx - 4, cy - 4, OUT); cv.line(cx - 4, cy - 4, cx + 4, cy - 4, OUT); cv.line(cx + 4, cy - 4, cx + 5, cy + 2, OUT)
        cv.rect(cx - 7, cy, 4, 5, colour); cv.rect(cx + 4, cy, 4, 5, colour)
    elif icon == "hand":
        cv.rect(cx - 3, cy - 1, 7, 6, "#c89878")
        for k in range(4):
            cv.vline(cx - 3 + k * 2, cy - 4, 3, "#c89878")
        cv.line(cx + 4, cy + 1, cx + 6, cy - 2, "#c89878")
        cv.line(cx - 6, cy - 5, cx + 6, cy + 6, "#c03a32")
    else:
        cv.poly([(cx, cy - 5), (cx + 6, cy + 4), (cx - 6, cy + 4)], SAFETY[3]); cv.vline(cx, cy - 2, 3, OUT); cv.px(cx, cy + 2, OUT)
    scribble(cv, x + 3, y + h - 6, w - 6, "#7a7468", rows=2, gap=2)


def wall_clock(cv, cx, cy, r=6):
    """Round wall clock reading ten to midnight."""
    cv.ellipse(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, OUT)
    cv.ellipse(cx - r, cy - r, 2 * r + 1, 2 * r + 1, "#e6e0d0")
    for a in range(12):
        ang = a * 0.5236
        cv.px(int(round(cx + np.sin(ang) * (r - 1))), int(round(cy - np.cos(ang) * (r - 1))), "#5a5448")
    cv.line(cx, cy, cx, cy - r + 2, OUT)
    cv.line(cx, cy, cx - 2, cy - r + 3, OUT)
    cv.px(cx, cy, "#c03a32")


def exit_sign(cv, x, y):
    cv.rect(x, y, 19, 9, OUT); cv.rect(x + 1, y + 1, 17, 7, EXIT_GREEN[1]); cv.hline(x + 1, y + 1, 17, EXIT_GREEN[2])
    micro_text(cv, "EXIT", x + 3, y + 2, EXIT_GREEN[3])
    halo(cv, x + 9, y + 4, 12, EXIT_GREEN[2], 0.05, 2)


def outlet(cv, x, y, colour="#d8d2c4"):
    cv.rect(x, y, 5, 7, OUT); cv.rect(x + 1, y + 1, 3, 5, colour); cv.px(x + 2, y + 2, OUT); cv.px(x + 2, y + 4, OUT)


def first_aid(cv, x, y):
    cv.rect(x, y, 14, 12, OUT); cv.rect(x + 1, y + 1, 12, 10, "#e6e2d8"); cv.hline(x + 1, y + 1, 12, "#fffaf0")
    cv.rect(x + 6, y + 3, 2, 6, "#c03a32"); cv.rect(x + 4, y + 5, 6, 2, "#c03a32")


def eyewash(cv, x, y):
    """Eyewash station: green sign and a yellow bowl on a bracket."""
    cv.rect(x, y, 16, 8, OUT); cv.rect(x + 1, y + 1, 14, 6, EXIT_GREEN[1]); micro_text(cv, "EYE", x + 3, y + 2, "#e6f6ea")
    cv.rect(x + 3, y + 12, 10, 4, OUT); cv.rect(x + 4, y + 12, 8, 3, SAFETY[3]); cv.hline(x + 4, y + 12, 8, SAFETY[3])
    cv.vline(x + 8, y + 16, 8, STEEL[4])


def breaker_panel(cv, x, y, w=18, h=26, label="1B"):
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#7c8290"); cv.hline(x + 1, y + 1, w - 2, "#9aa0ac")
    cv.vline(x + w - 4, y + h // 2 - 2, 4, OUT)
    cv.rect(x + 3, y + 3, w - 8, 6, "#e6e2d8"); micro_text(cv, label, x + 4, y + 4, "#262830")
    cv.rect(x + 3, y + h - 6, 6, 3, "#c03a32")


# ------------------------------------------------------------------------------ E02 props

def _bench_body(cv, x0, x1, base, top, seed=0, vise=True):
    """Heavy maple-topped workbench on steel legs with a lower shelf; top seen from above."""
    w = x1 - x0
    ground_shadow(cv, (x0 + x1) // 2, base - 1, w // 2 + 2, 3)
    # legs and lower shelf
    for lx in (x0 + 4, x1 - 8):
        cv.rect(lx, top + 10, 4, base - top - 10, OUT); cv.vline(lx + 1, top + 10, base - top - 11, STEEL[5]); cv.vline(lx + 2, top + 10, base - top - 11, STEEL[3])
        cv.rect(lx - 1, base - 2, 6, 2, OUT)
    sy = base - 10
    cv.rect(x0 + 3, sy, w - 6, 4, OUT); cv.rect(x0 + 4, sy, w - 8, 2, PLY[3]); cv.hline(x0 + 4, sy, w - 8, PLY[5])
    # top: butcher-block strips seen from above, then the front edge
    cv.rect(x0, top, w, 13, OUT)
    for r in range(4):
        cv.rect(x0 + 1, top + 1 + r * 2, w - 2, 2, MAPLE[5] if r % 2 == 0 else MAPLE[4])
    rng = np.random.default_rng(seed)
    for _ in range(w // 9):
        gx, gy = x0 + 2 + int(rng.integers(0, w - 10)), top + 1 + int(rng.integers(0, 8))
        cv.hline(gx, gy, int(rng.integers(3, 8)), MAPLE[3])
    cv.hline(x0 + 1, top + 1, w - 2, MAPLE[6])
    cv.rect(x0 + 1, top + 9, w - 2, 3, MAPLE[3]); cv.hline(x0 + 1, top + 9, w - 2, MAPLE[4]); cv.hline(x0 + 1, top + 11, w - 2, MAPLE[2])
    for jx in range(x0 + 6, x1 - 4, 9):
        cv.vline(jx, top + 9, 3, MAPLE[2])
    if vise:
        vx = x0 + 8
        cv.rect(vx, top + 10, 14, 7, OUT); cv.rect(vx + 1, top + 11, 12, 5, STEEL[4]); cv.hline(vx + 1, top + 11, 12, STEEL[6])
        cv.hline(vx - 3, top + 15, 20, STEEL[5]); cv.rect(vx - 4, top + 14, 2, 3, OUT); cv.rect(vx + 18, top + 14, 2, 3, OUT)


def maple_bench(width=170, height=45, model="arch", seed=0):
    """Cal's or Dev's workbench. model: 'arch' (Cal's study model of the suspended arch, held up on
    wire stands), 'arch_revised' (the same arch resting on two piers), 'spans' (Dev's two spans on
    three piers, laptop, calipers, mug, bridge planks waiting), 'spans_done' (the planks installed)."""
    W, Hc = width + 8, height + 6
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 3
    x0, x1 = 4, W - 4
    top = base - 31
    _bench_body(cv, x0, x1, base, top, seed, vise=model.startswith("arch"))
    ty = top + 6                                                # where things sit on the top
    if model.startswith("arch"):
        # base board and the balsa arch with thread hangers
        bx0, bx1 = x0 + 34, x0 + 100
        cv.rect(bx0, ty - 2, bx1 - bx0, 3, PLY[4]); cv.hline(bx0, ty - 2, bx1 - bx0, PLY[6]); cv.hline(bx0, ty, bx1 - bx0, PLY[2])
        ax0, ax1, deck = bx0 + 4, bx1 - 4, ty - 9
        apex = ty - 26
        prev = None
        for xx in range(ax0, ax1 + 1):
            t = (xx - ax0) / (ax1 - ax0)
            yy = int(round(deck - (deck - apex) * 4 * t * (1 - t)))
            cv.px(xx, yy, OUT); cv.px(xx, yy + 1, MAPLE[6]); cv.px(xx, yy + 2, MAPLE[4])
            if prev is not None and abs(yy - prev) > 1:
                lo, hi = sorted((prev, yy))
                cv.vline(xx, lo, hi - lo, MAPLE[6])
            if (xx - ax0) % 6 == 3 and 0.08 < t < 0.92:
                cv.vline(xx, yy + 3, deck - yy - 3, "#5a4a3a")
            prev = yy
        cv.rect(ax0 - 2, deck, ax1 - ax0 + 5, 2, OUT); cv.hline(ax0 - 1, deck, ax1 - ax0 + 3, MAPLE[6])
        cv.rect(ax0 + (ax1 - ax0) // 2, apex - 6, 1, 6, OUT)
        if model == "arch":
            cv.rect(ax0 + (ax1 - ax0) // 2 + 1, apex - 6, 4, 3, MARKER["red"])
            for sx in (ax0 + 1, ax1 - 1):                         # wire stands holding the loose ends
                cv.vline(sx, deck + 2, ty - 2 - deck - 2, STEEL[6]); cv.rect(sx - 2, ty - 3, 5, 1, STEEL[3])
        else:
            cv.rect(ax0 + (ax1 - ax0) // 2 + 1, apex - 6, 4, 3, MARKER["green"])
            for sx in (ax0 + (ax1 - ax0) // 3, ax0 + 2 * (ax1 - ax0) // 3):
                cv.rect(sx - 2, deck + 2, 5, ty - 2 - deck - 2, OUT); cv.rect(sx - 1, deck + 2, 3, ty - deck - 5, CONC[7]); cv.vline(sx - 1, deck + 2, ty - deck - 5, CONC[8])
        # cutting mat, balsa strips, knife, glue, a sketchbook
        mx = x0 + 108
        cv.rect(mx, ty - 3, 34, 7, "#2a6a4a"); cv.hline(mx, ty - 3, 34, "#3e8a62")
        for gx in range(mx + 3, mx + 34, 5):
            cv.vline(gx, ty - 3, 7, "#3a7e58")
        for k in range(3):
            cv.hline(mx + 3, ty - 2 + k * 2, 22 - k * 4, MAPLE[6])
        cv.line(mx + 26, ty + 2, mx + 32, ty - 1, STEEL[6]); cv.px(mx + 25, ty + 2, "#e8b45c")
        cv.rect(x0 + 146, ty - 8, 4, 9, "#e6e2d6"); cv.rect(x0 + 146, ty - 10, 4, 2, "#d46a24")
        cv.rect(x0 + 12, ty - 3, 18, 7, PAPER[3]); cv.vline(x0 + 21, ty - 3, 7, PAPER[1])
        scribble(cv, x0 + 13, ty - 1, 7, "#5a5a6a", 1, rows=2, gap=2); cv.line(x0 + 23, ty, x0 + 28, ty - 2, MARKER["blue"])
        cv.line(x0 + 26, ty + 3, x0 + 31, ty + 1, "#e8b45c")
        # bins on the lower shelf
        for k, c in enumerate(("#2c4a8a", "#2c4a8a", "#c84a3c")):
            bx = x0 + 30 + k * 34
            cv.rect(bx, base - 17, 26, 8, OUT); cv.rect(bx + 1, base - 16, 24, 6, c); cv.hline(bx + 1, base - 16, 24, shade(c, 0.3))
    else:
        # Dev's model: two spans on three piers, a tiny walker
        bx0, bx1 = x0 + 20, x0 + 92
        cv.rect(bx0, ty - 2, bx1 - bx0, 3, PLY[4]); cv.hline(bx0, ty - 2, bx1 - bx0, PLY[6]); cv.hline(bx0, ty, bx1 - bx0, PLY[2])
        deck = ty - 13
        cv.rect(bx0 + 3, deck, bx1 - bx0 - 6, 3, OUT); cv.hline(bx0 + 4, deck, bx1 - bx0 - 8, MAPLE[6]); cv.hline(bx0 + 4, deck + 1, bx1 - bx0 - 8, MAPLE[4])
        for px_ in (bx0 + 6, (bx0 + bx1) // 2, bx1 - 7):
            cv.rect(px_ - 2, deck + 3, 5, ty - 2 - deck - 3, OUT); cv.rect(px_ - 1, deck + 3, 3, ty - deck - 6, CONC[7]); cv.vline(px_ - 1, deck + 3, ty - deck - 6, CONC[8])
        for hx in range(bx0 + 4, bx1 - 4, 3):                    # handrail posts
            cv.px(hx, deck - 1, MAPLE[5])
        cv.hline(bx0 + 4, deck - 3, bx1 - bx0 - 8, MAPLE[5])
        fx = bx0 + 30
        cv.rect(fx, deck - 6, 2, 2, "#f0c8a0"); cv.rect(fx, deck - 4, 2, 3, MARKER["red"])
        # laptop with CAD on the screen
        lx = x0 + 100
        cv.poly([(lx, ty + 3), (lx + 22, ty + 3), (lx + 20, ty - 1), (lx + 2, ty - 1)], STEEL[4])
        cv.rect(lx + 2, ty - 15, 18, 14, OUT); cv.rect(lx + 3, ty - 14, 16, 12, "#1c2c4a")
        cv.hline(lx + 4, ty - 7, 14, "#8ac4ff"); cv.line(lx + 5, ty - 7, lx + 10, ty - 12, "#8ac4ff"); cv.line(lx + 10, ty - 12, lx + 16, ty - 7, "#8ac4ff")
        cv.vline(lx + 7, ty - 7, 4, "#6a9ad8"); cv.vline(lx + 14, ty - 7, 4, "#6a9ad8")
        # calipers, mug, pencil
        cv.hline(x0 + 8, ty, 14, STEEL[6]); cv.vline(x0 + 9, ty - 3, 3, STEEL[6]); cv.vline(x0 + 13, ty - 3, 3, STEEL[6])
        cv.rect(x0 + 126, ty - 7, 6, 8, OUT); cv.rect(x0 + 127, ty - 6, 4, 6, "#cfb87c"); cv.hline(x0 + 127, ty - 4, 4, "#2a2430"); cv.px(x0 + 132, ty - 4, OUT); cv.px(x0 + 132, ty - 3, OUT)
        if model == "spans":
            # deck planks for the court bridge, strapped and tagged, waiting to be installed
            px0 = x0 + 136
            for k in range(4):
                cv.rect(px0 - k, ty - 2 - k * 2, 26, 3, OUT); cv.rect(px0 - k + 1, ty - 2 - k * 2, 24, 2, PLY[5] if k % 2 else PLY[4]); cv.hline(px0 - k + 1, ty - 2 - k * 2, 24, PLY[6])
            cv.vline(px0 + 10, ty - 9, 10, "#d46a24")
            cv.rect(px0 + 16, ty - 13, 6, 5, PAPER[3]); cv.px(px0 + 17, ty - 12, MARKER["red"]); cv.px(px0 + 19, ty - 12, MARKER["blue"])
        else:
            cv.rect(x0 + 140, ty - 3, 14, 6, PAPER[3]); scribble(cv, x0 + 141, ty - 1, 9, "#5a5a6a", 2, rows=2, gap=2)
            cv.line(x0 + 150, ty - 1, x0 + 151, ty, MARKER["green"]); cv.line(x0 + 151, ty, x0 + 154, ty - 3, MARKER["green"])
            cv.ellipse(x0 + 158, ty - 2, 6, 4, "#d46a24"); cv.ellipse(x0 + 160, ty - 1, 2, 2, MAPLE[4])
        # parts bins and a toolbox below
        cv.rect(x0 + 22, base - 18, 34, 9, OUT); cv.rect(x0 + 23, base - 17, 32, 7, "#c84a3c"); cv.hline(x0 + 23, base - 17, 32, "#e06a5a"); cv.rect(x0 + 35, base - 19, 8, 2, OUT)
        for k in range(2):
            bx = x0 + 90 + k * 30
            cv.rect(bx, base - 17, 24, 8, OUT); cv.rect(bx + 1, base - 16, 22, 6, "#2c4a8a"); cv.hline(bx + 1, base - 16, 22, "#4a6ab0")
    return cv, W // 2, base


def tool_shelf_tags(width=95, height=96, seed=0):
    """Free-standing steel shelving of shared tools, every tool tagged with a red mark (Cal) and a
    blue mark (Dev), under a SHARED TOOLS plate."""
    W, Hc = width + 6, height + 4
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 3, W - 3
    rng = np.random.default_rng(seed)
    ground_shadow(cv, W // 2, base - 1, width // 2 + 2, 3)
    shelves = [base - 4, base - 28, base - 52, base - 76]
    top = base - height + 13
    # back panel (pegboard-brown hardboard) so the shelf reads as a unit
    cv.rect(x0 + 2, top, x1 - x0 - 4, base - top - 2, "#3a2c26")
    for yy in range(top + 2, base - 4, 4):
        for xx in range(x0 + 4 + (yy // 4 % 2) * 2, x1 - 4, 4):
            cv.px(xx, yy, "#2a201c")
    # contents per level
    # level 3 (top): drill cases red and blue, a level
    ly = shelves[3]
    for k, (col, wdt) in enumerate((("#c84a3c", 20), ("#2c4a8a", 20), ("#c84a3c", 16), ("#2c4a8a", 18))):
        bx = x0 + 4 + sum((20, 20, 16, 18)[:k]) + k * 2
        cv.rect(bx, ly - 12, wdt, 12, OUT); cv.rect(bx + 1, ly - 11, wdt - 2, 10, col); cv.hline(bx + 1, ly - 11, wdt - 2, shade(col, 0.3))
        cv.rect(bx + wdt // 2 - 3, ly - 14, 6, 2, OUT); cv.rect(bx + 3, ly - 6, wdt - 6, 1, shade(col, -0.3))
    # level 2: bar clamps hanging, a long yellow level, hammers
    ly = shelves[2]
    for k in range(5):
        cx_ = x0 + 6 + k * 6
        cv.rect(cx_, ly - 20, 2, 20, STEEL[5]); cv.rect(cx_ - 1, ly - 20, 4, 4, "#d46a24"); cv.rect(cx_ - 1, ly - 7, 4, 4, "#d46a24")
    cv.rect(x0 + 40, ly - 5, 44, 5, OUT); cv.rect(x0 + 41, ly - 4, 42, 3, SAFETY[3]); cv.rect(x0 + 60, ly - 4, 4, 2, "#7ae0a0")
    for k in range(2):
        hx = x0 + 46 + k * 16
        cv.rect(hx, ly - 15, 10, 4, IRON[3]); cv.hline(hx, ly - 15, 10, IRON[4]); cv.rect(hx + 4, ly - 11, 2, 6, WOOD[4])
    # level 1: circular saw, sander, a coffee can of pencils, a jar of screws
    ly = shelves[1]
    cv.ellipse(x0 + 5, ly - 18, 22, 18, OUT); cv.ellipse(x0 + 6, ly - 17, 20, 16, STEEL[5]); cv.ellipse(x0 + 10, ly - 13, 12, 9, STEEL[3])
    cv.rect(x0 + 14, ly - 22, 12, 7, "#e8b45c"); cv.hline(x0 + 14, ly - 22, 12, "#f6d48a")
    cv.rect(x0 + 32, ly - 12, 20, 12, OUT); cv.rect(x0 + 33, ly - 11, 18, 10, "#2a7a4a"); cv.rect(x0 + 33, ly - 4, 18, 3, OUT)
    cv.rect(x0 + 58, ly - 11, 9, 11, OUT); cv.rect(x0 + 59, ly - 10, 7, 9, STEEL[4]); cv.vline(x0 + 60, ly - 15, 5, "#e8b45c"); cv.vline(x0 + 63, ly - 14, 4, MARKER["blue"])
    cv.rect(x0 + 72, ly - 10, 10, 10, OUT); cv.rect(x0 + 73, ly - 9, 8, 8, "#9ab0c0"); cv.rect(x0 + 73, ly - 11, 8, 2, "#c84a3c")
    for _ in range(6):
        cv.px(x0 + 74 + int(rng.integers(0, 6)), ly - 6 + int(rng.integers(0, 4)), STEEL[2])
    # level 0 (floor): shop vac and bins
    ly = shelves[0]
    cv.ellipse(x0 + 4, ly - 20, 26, 22, OUT); cv.ellipse(x0 + 5, ly - 19, 24, 20, SAFETY[2]); cv.vline(x0 + 9, ly - 16, 13, SAFETY[3])
    cv.rect(x0 + 6, ly - 22, 22, 5, IRON[2]); cv.hline(x0 + 6, ly - 22, 22, IRON[4])
    for k in range(2):
        bx = x0 + 36 + k * 26
        cv.rect(bx, ly - 14, 22, 14, OUT); cv.rect(bx + 1, ly - 13, 20, 12, "#3c5a7a"); cv.hline(bx + 1, ly - 13, 20, "#5a7e9c")
        cv.rect(bx + 6, ly - 10, 10, 5, PAPER[3]); cv.hline(bx + 7, ly - 8, 8, "#5a5a6a")
    # uprights and shelf lips
    for ux in (x0, x1 - 3):
        cv.rect(ux, top - 2, 3, base - top + 2, OUT); cv.vline(ux + 1, top - 1, base - top, STEEL[5])
        for hy in range(top + 2, base - 2, 4):
            cv.px(ux + 1, hy, STEEL[1])
    for sy in shelves:
        cv.rect(x0, sy, x1 - x0, 4, OUT); cv.rect(x0 + 1, sy + 1, x1 - x0 - 2, 2, STEEL[4]); cv.hline(x0 + 1, sy + 1, x1 - x0 - 2, STEEL[6])
    # tags: little cards on strings from each shelf lip, each with a red AND a blue mark
    for sy in shelves[1:]:
        for tx in range(x0 + 9 + (sy % 3) * 3, x1 - 8, 17):
            cv.vline(tx + 2, sy + 3, 2, "#e6d6b1")
            cv.rect(tx, sy + 5, 6, 5, PAPER[3]); cv.hline(tx, sy + 9, 6, PAPER[1])
            cv.px(tx + 1, sy + 6, MARKER["red"]); cv.px(tx + 1, sy + 7, MARKER["red"])
            cv.px(tx + 4, sy + 6, MARKER["blue"]); cv.px(tx + 4, sy + 7, MARKER["blue"])
    # SHARED TOOLS enamel plate on top
    pw = text_width("SHARED TOOLS") + 6
    px0 = (W - pw) // 2
    cv.rect(px0, 0, pw, 12, OUT); cv.rect(px0 + 1, 1, pw - 2, 10, SAFETY[2]); cv.hline(px0 + 1, 1, pw - 2, SAFETY[3])
    text(cv, "SHARED TOOLS", px0 + 4, 1, "#1a1524")
    cv.vline(px0 + 6, 12, top - 13, STEEL[3]); cv.vline(px0 + pw - 7, 12, top - 13, STEEL[3])
    return cv, W // 2, base


def tool_chest(width=70, height=44, seed=0):
    """Red rolling tool chest: chrome drawer pulls, side handle, casters, a radio and tape on top."""
    W, Hc = width + 6, height + 5
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 6, W - 8
    ground_shadow(cv, W // 2, base - 1, width // 2, 3)
    top = base - 36
    R = ["#4a1418", "#7a2222", "#a8322c", "#c84a3c", "#e06a5a", "#f29a84"]
    cv.rect(x0, top, x1 - x0, base - 5 - top, OUT)
    cv.rect(x0 + 1, top + 1, x1 - x0 - 2, base - 7 - top, R[3])
    cv.rect(x0 + 1, top + 1, x1 - x0 - 2, 3, R[4]); cv.hline(x0 + 1, top + 1, x1 - x0 - 2, R[5])
    dy = top + 5
    for k, dh in enumerate((4, 4, 5, 5, 8)):
        cv.hline(x0 + 2, dy + dh, x1 - x0 - 4, R[1])
        cv.rect(x0 + 6, dy + 1, x1 - x0 - 12, 1, STEEL[6]); cv.hline(x0 + 6, dy + 2, x1 - x0 - 12, STEEL[4])
        dy += dh + 1
    cv.vline(x1 - 2, top + 1, base - 8 - top, R[1])
    cv.rect(x1, top + 6, 2, 16, STEEL[5]); cv.rect(x1 + 2, top + 5, 2, 18, OUT); cv.vline(x1 + 1, top + 6, 16, STEEL[7])
    cv.rect(x0 + 4, top + 6, 13, 7, "#e6d6b1"); micro_text(cv, "C+D", x0 + 5, top + 7, "#1a1524")
    for cx_ in (x0 + 4, x1 - 6):
        cv.rect(cx_, base - 5, 4, 2, STEEL[3]); cv.ellipse(cx_ - 1, base - 4, 6, 5, OUT); cv.px(cx_ + 1, base - 2, STEEL[5])
    # radio, tape roll, a rag on top
    cv.rect(x0 + 4, top - 8, 20, 8, OUT); cv.rect(x0 + 5, top - 7, 18, 6, "#3a3a46")
    for gx in range(x0 + 6, x0 + 13, 2):
        cv.vline(gx, top - 6, 4, "#262630")
    cv.rect(x0 + 15, top - 6, 6, 2, "#e8b45c"); cv.vline(x0 + 22, top - 14, 6, STEEL[5])
    cv.ellipse(x0 + 30, top - 6, 8, 6, OUT); cv.ellipse(x0 + 31, top - 5, 6, 4, "#c0c4cc"); cv.ellipse(x0 + 33, top - 4, 2, 2, OUT)
    cv.poly([(x0 + 42, top), (x0 + 56, top), (x0 + 54, top - 3), (x0 + 44, top - 4)], "#5a7e9c"); cv.hline(x0 + 44, top - 3, 9, "#7c9cb8")
    return cv, W // 2, base


def shop_floor_lamp(height=68, seed=0):
    """Weighted floor lamp with a jointed arm and a red enamel shade; the bulb sits ~h-5 up, directly
    above the anchor."""
    W, Hc = 34, height + 6
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    cx = 12
    ground_shadow(cv, cx + 4, base - 1, 11, 2)
    px_ = cx + 9
    cv.ellipse(px_ - 7, base - 4, 15, 5, OUT); cv.ellipse(px_ - 6, base - 4, 13, 3, IRON[2]); cv.hline(px_ - 5, base - 4, 10, IRON[4])
    cv.rect(px_ - 1, base - 44, 3, 41, OUT); cv.vline(px_, base - 44, 40, STEEL[5])
    cv.rect(px_ - 2, base - 46, 5, 4, IRON[3])
    # arm up and over to the shade
    cv.line(px_, base - 45, px_ - 4, base - 60, STEEL[5]); cv.line(px_ + 1, base - 45, px_ - 3, base - 60, OUT)
    cv.line(px_ - 4, base - 60, cx, base - 66, STEEL[5])
    cv.rect(px_ - 5, base - 61, 3, 3, IRON[3])
    cv.line(px_ + 2, base - 50, px_ - 2, base - 58, "#8a8a96")                # spring
    # shade: red enamel cone pointing down
    sy = base - 70
    cv.poly([(cx - 2, sy), (cx + 3, sy), (cx + 9, sy + 7), (cx - 8, sy + 7)], OUT)
    cv.poly([(cx - 1, sy + 1), (cx + 2, sy + 1), (cx + 7, sy + 6), (cx - 6, sy + 6)], "#b8382e")
    cv.line(cx - 1, sy + 1, cx - 5, sy + 5, "#e0705a")
    cv.hline(cx - 7, sy + 7, 16, "#7a1e1a")
    cv.rect(cx - 3, sy + 8, 7, 1, WARM[3]); cv.rect(cx - 1, sy + 8, 3, 2, WARM[4])
    # a hook on the pole with a rag
    cv.rect(px_ + 2, base - 30, 4, 7, "#5a7e9c"); cv.vline(px_ + 2, base - 30, 7, "#7c9cb8")
    return cv, cx, base


# ------------------------------------------------------------------- E03 test floor pieces

FRAME_BLUE = ["#141c34", "#1e2c50", "#2a3e6e", "#34528e", "#4a6ab0", "#6a8ad0"]
HOSE_R, HOSE_B = "#b8382e", "#2c4a9a"


def strong_wall(cv, x, y, w, h, seed=0, pitch=(20, 18)):
    """Board-formed concrete reaction wall: horizontal board marks, pour lines, and a grid of
    steel-collared anchor holes."""
    xs, ys = grid(w, h)
    p = P(CONC)
    f = soft_field(w, h, 40, seed)
    board = ((ys + y) // 6) % 2
    idx = np.where(board == 0, 5, 6) - (f < 0.3).astype(int)
    idx = np.where(((ys + y) % 6) == 5, 4, idx)
    fine = hashn(xs + x, ys + y, seed)
    idx = np.where(fine > 0.985, idx - 1, idx)
    # board butt joints, staggered per board course
    bj = ((xs + x + ((ys + y) // 6) * 37) % 48) == 0
    idx = np.where(bj, 4, idx)
    put_rgb(cv, x, y, p[idx])
    for py in range(y + 10, y + h - 6, 48):                    # pour lines
        cv.hline(x, py, w, CONC[3]); cv.hline(x, py + 1, w, CONC[7])
    px_, py_ = pitch
    for hy in range(y + 8, y + h - 8, py_):
        for hx in range(x + 8, x + w - 6, px_):
            cv.rect(hx - 1, hy - 1, 4, 4, STEEL[3]); cv.px(hx - 1, hy - 1, STEEL[5])
            cv.rect(hx, hy, 2, 2, "#0c0b12")


def anchor_floor(cv, x, y, w, h, pitch=(48, 30), x_off=24, y_off=14):
    """Tie-down anchors set in the strong floor (flat steel collars with a dark bore)."""
    for ay in range(y + y_off, y + h - 4, pitch[1]):
        for ax in range(x + x_off, x + w - 4, pitch[0]):
            cv.rect(ax - 2, ay - 1, 5, 3, STEEL[4]); cv.hline(ax - 2, ay - 1, 5, STEEL[6])
            cv.rect(ax - 1, ay, 3, 1, "#0c0b12")


def crane_girder(cv, x0, x1, y, h=16, label="10 TON", trolley_x=None):
    """Yellow overhead crane bridge across the bay with its trolley; returns the rope point."""
    Y = CRANE
    cv.rect(x0, y, x1 - x0, h, OUT)
    cv.rect(x0, y + 1, x1 - x0, h - 2, Y[3])
    cv.hline(x0, y + 1, x1 - x0, Y[5]); cv.hline(x0, y + 2, x1 - x0, Y[4])
    cv.hline(x0, y + h - 3, x1 - x0, Y[2]); cv.hline(x0, y + h - 2, x1 - x0, Y[1])
    for sx in range(x0 + 12, x1, 24):                           # stiffener plates
        cv.vline(sx, y + 3, h - 6, Y[2]); cv.vline(sx + 1, y + 3, h - 6, Y[4])
    lw = text_width(label)
    for lx in range(x0 + 120, x1 - lw, 360):
        cv.rect(lx - 3, y + 3, lw + 6, h - 6, OUT)
        text(cv, label, lx, y + 3, Y[4])
    ropes = []
    for tx in ([] if trolley_x is None else (trolley_x if isinstance(trolley_x, (list, tuple)) else [trolley_x])):
        cv.rect(tx - 20, y - 6, 40, 6, OUT); cv.rect(tx - 19, y - 5, 38, 4, Y[2]); cv.hline(tx - 19, y - 5, 38, Y[4])
        for wx in (tx - 15, tx + 9):
            cv.ellipse(wx, y - 9, 7, 5, OUT); cv.ellipse(wx + 1, y - 8, 5, 3, STEEL[4])
        cv.rect(tx - 14, y + h, 28, 7, OUT); cv.rect(tx - 13, y + h, 26, 6, Y[2]); cv.hline(tx - 13, y + h, 26, Y[3])
        cv.rect(tx - 9, y + h + 1, 18, 4, STEEL[3])                 # rope drum
        for k in range(0, 18, 2):
            cv.vline(tx - 9 + k, y + h + 1, 4, STEEL[5])
        ropes.append((tx, y + h + 6))
    if isinstance(trolley_x, (list, tuple)):
        return ropes
    return ropes[0] if ropes else None


def hook_frame(drop, dx, w=24):
    """One swing frame of the crane hook block: two ropes from the drum to a sheave block, the
    hook below. Canvas is w wide; the ropes start at the top centre."""
    cv = Canvas(w, drop + 22)
    cx = w // 2
    bx = cx + dx
    for k in (-2, 2):
        cv.line(cx + k, 0, bx + k, drop, STEEL[2]); cv.line(cx + k + 1, 0, bx + k + 1, drop, STEEL[5])
    cv.rect(bx - 5, drop, 11, 9, OUT); cv.rect(bx - 4, drop + 1, 9, 7, CRANE[3]); cv.hline(bx - 4, drop + 1, 9, CRANE[5])
    cv.rect(bx - 2, drop + 3, 5, 3, CRANE[1])
    cv.rect(bx, drop + 9, 2, 3, STEEL[4])
    # the hook: a J with a safety latch
    hy = drop + 12
    cv.vline(bx, hy, 5, OUT); cv.vline(bx + 1, hy, 5, STEEL[5])
    cv.line(bx + 1, hy + 5, bx - 1, hy + 8, OUT); cv.line(bx - 1, hy + 8, bx - 4, hy + 7, OUT); cv.line(bx - 4, hy + 7, bx - 4, hy + 4, OUT)
    cv.px(bx, hy + 6, STEEL[6]); cv.px(bx - 2, hy + 7, STEEL[5])
    cv.line(bx - 4, hy + 4, bx, hy + 2, CRANE[4])
    return cv


def test_frame(cv, x0, x1, top, base, seed=0):
    """Blue steel reaction frame against the strong wall: two columns, a crosshead, a hydraulic
    actuator pressing a steel beam specimen on roller supports, strain-gauge wires. Returns the
    actuator tip and specimen midpoint."""
    F = FRAME_BLUE
    cw = 10
    for cx in (x0, x1 - cw):
        cv.rect(cx, top, cw, base - top, OUT)
        cv.rect(cx + 1, top + 1, cw - 2, base - top - 2, F[3]); cv.vline(cx + 1, top + 1, base - top - 2, F[5])
        cv.vline(cx + 3, top + 1, base - top - 2, F[4]); cv.vline(cx + cw - 2, top + 1, base - top - 2, F[1])
        cv.rect(cx - 3, base - 4, cw + 6, 4, OUT); cv.rect(cx - 2, base - 3, cw + 4, 2, STEEL[4])
        for by in range(top + 16, base - 8, 14):
            cv.px(cx + 5, by, F[5])
    # crosshead
    cv.rect(x0 - 6, top, x1 - x0 + 12, 13, OUT)
    cv.rect(x0 - 5, top + 1, x1 - x0 + 10, 11, F[3]); cv.hline(x0 - 5, top + 1, x1 - x0 + 10, F[5]); cv.hline(x0 - 5, top + 10, x1 - x0 + 10, F[1])
    for bx in range(x0, x1, 14):
        cv.px(bx, top + 4, F[5]); cv.px(bx, top + 8, F[5])
    # actuator: cylinder, rod, load cell
    mid = (x0 + x1) // 2
    cv.rect(mid - 7, top + 13, 14, 30, OUT)
    cv.rect(mid - 6, top + 13, 12, 29, STEEL[4]); cv.vline(mid - 4, top + 13, 29, STEEL[6]); cv.vline(mid + 4, top + 13, 29, STEEL[2])
    cv.rect(mid - 7, top + 20, 14, 2, STEEL[2]); cv.rect(mid - 7, top + 36, 14, 2, STEEL[2])
    cv.rect(mid - 2, top + 43, 5, 10, STEEL[6]); cv.vline(mid - 1, top + 43, 10, "#e8ecf4")
    cv.rect(mid - 5, top + 53, 11, 5, OUT); cv.rect(mid - 4, top + 54, 9, 3, "#c8a050")
    tip = (mid, top + 58)
    # hoses looping out to the right
    cv.line(mid + 6, top + 17, x1 + 12, top + 26, HOSE_R); cv.line(x1 + 12, top + 26, x1 + 24, base - 18, HOSE_R)
    cv.line(mid + 6, top + 33, x1 + 8, top + 40, HOSE_B); cv.line(x1 + 8, top + 40, x1 + 18, base - 16, HOSE_B)
    # beam specimen on roller supports
    sy = top + 60
    sx0, sx1 = x0 + 16, x1 - 16
    for px_ in (sx0 + 10, sx1 - 14):
        cv.rect(px_ - 4, sy + 9, 12, base - sy - 13, OUT); cv.rect(px_ - 3, sy + 10, 10, base - sy - 15, STEEL[3]); cv.hline(px_ - 3, sy + 10, 10, STEEL[5])
        cv.poly([(px_ - 2, sy + 9), (px_ + 6, sy + 9), (px_ + 2, sy + 5)], STEEL[5])
    cv.rect(sx0, sy - 1, sx1 - sx0, 7, OUT)
    cv.rect(sx0 + 1, sy, sx1 - sx0 - 2, 5, "#7c7a80"); cv.hline(sx0 + 1, sy, sx1 - sx0 - 2, "#a8a6ac"); cv.hline(sx0 + 1, sy + 4, sx1 - sx0 - 2, "#4e4c52")
    cv.rect(sx0 + 1, sy + 2, sx1 - sx0 - 2, 1, "#5e5c62")
    rng = np.random.default_rng(seed)
    for k in range(5):                                          # strain gauges and their wires
        gx = sx0 + 14 + k * (sx1 - sx0 - 28) // 4
        cv.rect(gx, sy + 2, 3, 2, "#e8b45c")
        cv.line(gx + 1, sy + 5, gx - 6 + int(rng.integers(0, 4)), base - 2, "#2a2a34")
    for k in range(0, sx1 - sx0 - 4, 12):
        cv.vline(sx0 + 3 + k, sy + 1, 3, MARKER["red"])
    return tip, (mid, sy)


def utm(cv, x, base):
    """Universal testing machine: twin screw columns, moving crosshead, a concrete cylinder
    between the platens, and its control tower."""
    cv.rect(x, base - 10, 44, 10, OUT); cv.rect(x + 1, base - 9, 42, 8, "#3a4252"); cv.hline(x + 1, base - 9, 42, "#5a6272")
    for cx in (x + 4, x + 36):
        cv.rect(cx, base - 76, 4, 66, OUT); cv.vline(cx + 1, base - 75, 64, STEEL[6]); cv.vline(cx + 2, base - 75, 64, STEEL[4])
        for k in range(base - 74, base - 12, 3):
            cv.px(cx + 2, k, STEEL[2])
    cv.rect(x, base - 82, 44, 8, OUT); cv.rect(x + 1, base - 81, 42, 6, "#3a4252"); cv.hline(x + 1, base - 81, 42, "#6a7282")
    cv.rect(x + 2, base - 46, 40, 7, OUT); cv.rect(x + 3, base - 45, 38, 5, "#4a5262"); cv.hline(x + 3, base - 45, 38, "#7a8292")
    cv.rect(x + 16, base - 39, 12, 3, STEEL[5])
    cv.rect(x + 17, base - 36, 10, 22, OUT); cv.rect(x + 18, base - 35, 8, 20, CONC[7]); cv.vline(x + 18, base - 35, 20, CONC[8])
    cv.line(x + 19, base - 30, x + 24, base - 22, CONC[4])                          # a crack
    cv.rect(x + 16, base - 14, 12, 4, STEEL[5])
    cv.rect(x + 46, base - 52, 16, 52, OUT); cv.rect(x + 47, base - 51, 14, 50, "#3a4252"); cv.hline(x + 47, base - 51, 14, "#5a6272")
    cv.rect(x + 49, base - 48, 10, 7, "#0a120e"); cv.hline(x + 50, base - 45, 8, SCOPE[4])
    cv.rect(x + 51, base - 36, 6, 6, "#c03a32"); cv.rect(x + 52, base - 35, 4, 4, "#e85a4a")                # e-stop
    return (x + 50, base - 46)


def daq_rack(cv, x, y, w=30, h=72):
    """Instrument rack for the data acquisition: modules with LED rows; returns LED points."""
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#1e2028")
    leds = []
    yy = y + 3
    k = 0
    while yy < y + h - 8:
        mh = 7 if k % 3 else 10
        cv.rect(x + 2, yy, w - 4, mh, "#3a3e4a"); cv.hline(x + 2, yy, w - 4, "#5a5e6a")
        cv.px(x + 3, yy + 2, STEEL[6]); cv.px(x + w - 4, yy + 2, STEEL[6])
        for j in range(4):
            lx = x + 7 + j * 4
            col = ("#3cba7a", "#3cba7a", "#e8b45c", "#c84a3c")[(j + k) % 4]
            cv.px(lx, yy + 3, shade(col, -0.4))
            leds.append((lx, yy + 3, col))
        if mh == 10:
            cv.rect(x + 6, yy + 5, w - 12, 3, "#0a120e"); cv.hline(x + 7, yy + 6, w - 14, SCOPE[3])
        yy += mh + 1
        k += 1
    cv.rect(x + 4, y + h - 6, w - 8, 4, "#26282e")
    return leds


def hpu(cv, x, base):
    """Hydraulic power unit: blue tank, motor, pressure gauge, hoses out."""
    cv.rect(x, base - 24, 46, 24, OUT); cv.rect(x + 1, base - 23, 44, 22, FRAME_BLUE[2]); cv.hline(x + 1, base - 23, 44, FRAME_BLUE[4])
    cv.rect(x + 4, base - 34, 18, 11, OUT); cv.rect(x + 5, base - 33, 16, 9, STEEL[3]); cv.hline(x + 5, base - 33, 16, STEEL[5])
    for k in range(5, 20, 3):
        cv.vline(x + k, base - 32, 7, STEEL[2])
    cv.ellipse(x + 28, base - 36, 10, 10, OUT); cv.ellipse(x + 29, base - 35, 8, 8, "#e6e0d0"); cv.line(x + 33, base - 31, x + 35, base - 34, "#c03a32")
    cv.vline(x + 33, base - 27, 4, STEEL[5])
    cv.rect(x + 6, base - 16, 18, 6, "#e6d6b1"); micro_text(cv, "HPU 1", x + 7, base - 15, "#262830")
    cv.rect(x + 1, base - 3, 44, 2, C(SHADOW, 0.5))


def lightbox(cv, x, y, label, lit=False, colour="#c03a32"):
    """A wall lightbox sign (dark when off, glowing red when lit). Returns its rect."""
    w = text_width(label) + 10
    cv.rect(x, y, w, 14, OUT)
    cv.rect(x + 1, y + 1, w - 2, 12, "#2a1418" if not lit else colour)
    text(cv, label, x + 5, y + 2, "#5a2a2a" if not lit else "#ffe0d0")
    return (x, y, w, 14)


def suspended_underside(cv, x0, x1, y, hang_top):
    """The suspended bridge model seen from the test floor: a blue deck with amber edge lights on
    its underside, an arch rising above it, hangers, and cables up to the crane."""
    w = x1 - x0
    for cx in (x0 + w // 5, x1 - w // 5):
        cv.line(cx, hang_top, cx, y - 2, "#14121c"); cv.line(cx + 1, hang_top, cx + 1, y - 2, STEEL[4])
    apex = y - 18
    prev = None
    for xx in range(x0 + 4, x1 - 3):
        t = (xx - x0 - 4) / (w - 8)
        yy = int(round(y - 2 - (y - 2 - apex) * 4 * t * (1 - t)))
        cv.px(xx, yy, BLUEPRINT[4]); cv.px(xx, yy + 1, BLUEPRINT[2])
        if prev is not None and abs(yy - prev) > 1:
            lo, hi = sorted((prev, yy))
            cv.vline(xx, lo, hi - lo, BLUEPRINT[4])
        if (xx - x0) % 10 == 0 and 0.05 < t < 0.95:
            cv.vline(xx, yy + 2, y - yy - 2, BLUEPRINT[3])
        prev = yy
    cv.rect(x0, y, w, 6, OUT)
    cv.rect(x0 + 1, y + 1, w - 2, 4, BLUEPRINT[2]); cv.hline(x0 + 1, y + 1, w - 2, BLUEPRINT[4])
    cv.hline(x0 + 1, y + 4, w - 2, BLUEPRINT[1])
    pts = []
    cv.hline(x0 + 2, y + 5, w - 4, WARM[1])
    for lx in range(x0 + 6, x1 - 4, 12):
        cv.rect(lx - 1, y + 5, 3, 1, WARM[3]); cv.px(lx, y + 5, WARM[4]); pts.append((lx, y + 5))
    return pts


def stair_up_opening(cv, x0, x1, top, wall_base, floor_y, sign="MODEL LEVEL", steps_out=5):
    """A steel stair rising from the floor into an opening in the back wall (up to the model
    level): treads with yellow nosings climbing into the dark, rails on both sides, a sign above."""
    w = x1 - x0
    cv.rect(x0 - 4, top - 4, w + 8, wall_base - top + 4, CONC[2])
    cv.rect(x0 - 4, top - 4, w + 8, 3, CONC[5])
    cv.rect(x0, top, w, wall_base - top, "#0c0b12")
    # inside flight: treads getting smaller and darker as they climb
    n_in = 8
    for k in range(n_in):
        ty = wall_base - 4 - k * (wall_base - top - 8) // n_in
        inset = 4 + k
        tone = mix(STEEL[3], "#0c0b12", k / n_in)
        cv.rect(x0 + inset, ty, w - 2 * inset, 3, tone)
        cv.hline(x0 + inset, ty, w - 2 * inset, mix(SAFETY[2], "#0c0b12", k / n_in))
    # landing light at the top
    cv.rect(x0 + 12, top + 2, w - 24, 2, C(WARM[3], 0.6))
    # flight projecting onto the floor
    step_h = (floor_y - wall_base) // steps_out
    for k in range(steps_out):
        ty = floor_y - (k + 1) * step_h
        cv.rect(x0 + 2, ty, w - 4, step_h, STEEL[2])
        cv.rect(x0 + 2, ty, w - 4, 2, SAFETY[2]); cv.hline(x0 + 2, ty, w - 4, SAFETY[3])
        for gx in range(x0 + 5, x1 - 4, 3):
            cv.vline(gx, ty + 2, step_h - 2, STEEL[1])
    # stringers and rails
    for sx in (x0, x1 - 3):
        cv.rect(sx, wall_base, 3, floor_y - wall_base, STEEL[4]); cv.vline(sx, wall_base, floor_y - wall_base, STEEL[6])
        cv.line(sx + 1, floor_y - 30, sx + 1, top + 10, SAFETY[3])
        cv.vline(sx + 1, floor_y - 30, 30, SAFETY[2])
    cv.rect(x0 - 2, floor_y, w + 4, 2, C(SHADOW, 0.5))
    sw = text_width(sign) + 8
    sx = x0 + (w - sw) // 2
    cv.rect(sx, top - 22, sw, 13, OUT); cv.rect(sx + 1, top - 21, sw - 2, 11, SAFETY[2]); cv.hline(sx + 1, top - 21, sw - 2, SAFETY[3])
    text(cv, sign, sx + 4, top - 21, "#1a1524")


# ------------------------------------------------------------------------------ E03 props

def pipe_barrier(width=320, height=25, label="TEST AREA", seed=0):
    """Yellow steel pipe barrier on bolted posts, black-banded, with a hanging sign."""
    W, Hc = width + 6, height + 12
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 3, W - 3
    ground_shadow(cv, W // 2, base - 1, width // 2, 2)
    posts = list(range(x0, x1 - 3, 40)) + [x1 - 4]
    top = base - height + 2
    for px_ in posts:
        cv.rect(px_ - 1, base - 2, 7, 2, OUT); cv.rect(px_, base - 2, 5, 1, STEEL[4])
        cv.rect(px_, top, 4, base - top - 2, OUT); cv.vline(px_ + 1, top + 1, base - top - 3, SAFETY[3]); cv.vline(px_ + 2, top + 1, base - top - 3, SAFETY[2])
        for by in (top + 6, top + 14):
            cv.rect(px_ + 1, by, 2, 3, "#1a1524")
    for ry, th in ((top, 4), (top + 10, 3)):
        cv.rect(x0, ry, x1 - x0, th, OUT)
        cv.hline(x0 + 1, ry + 1, x1 - x0 - 2, SAFETY[3])
        if th > 3:
            cv.hline(x0 + 1, ry + 2, x1 - x0 - 2, SAFETY[2])
    sw = text_width(label) + 8
    sx = (W - sw) // 2
    cv.rect(sx, top + 3, sw, 13, OUT); cv.rect(sx + 1, top + 4, sw - 2, 11, "#e8e2d0")
    cv.rect(sx + 1, top + 4, 3, 11, "#c03a32"); cv.rect(sx + sw - 4, top + 4, 3, 11, "#c03a32")
    text(cv, label, sx + 4, top + 4, "#c03a32")
    return cv, W // 2, base


def steel_bench_chart(width=170, height=42, seed=0):
    """Steel workbench of the test floor: a data logger, a laptop, and the LOAD CHART board on a
    stand: two foundations lit, an arrow showing where the weight lands."""
    W, Hc = width + 8, height + 26
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 4, W - 4
    ground_shadow(cv, W // 2, base - 1, width // 2 + 2, 3)
    top = base - 28
    for lx in (x0 + 4, x1 - 8):
        cv.rect(lx, top + 6, 4, base - top - 6, OUT); cv.vline(lx + 1, top + 6, base - top - 7, STEEL[5])
    cv.rect(x0 + 3, base - 10, x1 - x0 - 6, 3, OUT); cv.hline(x0 + 4, base - 10, x1 - x0 - 8, STEEL[4])
    cv.rect(x0, top, x1 - x0, 8, OUT); cv.rect(x0 + 1, top + 1, x1 - x0 - 2, 4, STEEL[5]); cv.hline(x0 + 1, top + 1, x1 - x0 - 2, STEEL[6])
    cv.rect(x0 + 1, top + 5, x1 - x0 - 2, 2, STEEL[3])
    # things on the lower shelf: a coil of cable and a case
    cv.ellipse(x0 + 20, base - 18, 14, 8, OUT); cv.ellipse(x0 + 21, base - 17, 12, 6, "#2a2a34"); cv.ellipse(x0 + 24, base - 15, 6, 2, STEEL[2])
    cv.rect(x0 + 110, base - 19, 36, 9, OUT); cv.rect(x0 + 111, base - 18, 34, 7, "#c84a3c"); cv.hline(x0 + 111, base - 18, 34, "#e06a5a")
    # data logger with a ribbon of wires off the back
    ty = top + 2
    cv.rect(x0 + 10, ty - 9, 30, 9, OUT); cv.rect(x0 + 11, ty - 8, 28, 7, "#3a4252"); cv.hline(x0 + 11, ty - 8, 28, "#5a6272")
    cv.rect(x0 + 13, ty - 6, 12, 3, "#0a120e"); cv.hline(x0 + 14, ty - 5, 10, SCOPE[4])
    for k in range(4):
        cv.px(x0 + 28 + k * 2, ty - 5, ("#3cba7a", "#e8b45c", "#3cba7a", "#c84a3c")[k])
    # laptop
    lx = x0 + 128
    cv.poly([(lx, ty + 1), (lx + 22, ty + 1), (lx + 20, ty - 2), (lx + 2, ty - 2)], STEEL[4])
    cv.rect(lx + 2, ty - 15, 18, 13, OUT); cv.rect(lx + 3, ty - 14, 16, 11, "#1c2c4a")
    for k in range(6):
        cv.vline(lx + 4 + k * 2, ty - 5 - [2, 4, 7, 9, 8, 9][k], [2, 4, 7, 9, 8, 9][k], "#7ae0a0")
    # the LOAD CHART board on its stand
    bx, bw, bh = x0 + 52, 66, 30
    by = ty - bh - 4
    cv.vline(bx + 10, by + bh, 5, STEEL[4]); cv.vline(bx + bw - 11, by + bh, 5, STEEL[4])
    cv.rect(bx, by, bw, bh, OUT); cv.rect(bx + 1, by + 1, bw - 2, bh - 2, "#e8e4d8")
    cv.rect(bx + 1, by + 1, bw - 2, 8, "#2c4a8a")
    text(cv, "LOAD CHART", bx + 3, by, "#f0ece0")
    gy = by + bh - 6
    cv.hline(bx + 6, gy, bw - 12, "#262830")
    for k, fx in enumerate((bx + 16, bx + bw - 18)):            # two foundations, lit
        cv.rect(fx - 4, gy + 1, 9, 3, SAFETY[3]); cv.hline(fx - 4, gy + 1, 9, SAFETY[2])
        cv.vline(fx, gy - 7, 7, "#262830")
    cv.hline(bx + 10, gy - 8, bw - 20, "#262830"); cv.hline(bx + 10, gy - 9, bw - 20, "#262830")
    ax = bx + bw // 2
    cv.vline(ax, by + 11, 6, "#c03a32"); cv.line(ax - 2, by + 15, ax, by + 17, "#c03a32"); cv.line(ax + 2, by + 15, ax, by + 17, "#c03a32")
    return cv, W // 2, base


def cylinder_cart(width=80, height=50, seed=0):
    """Two-tier steel cart carrying concrete test cylinders and weight plates."""
    W, Hc = width + 6, height + 4
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 4, W - 4
    ground_shadow(cv, W // 2, base - 1, width // 2, 3)
    top = base - 34
    for lx in (x0 + 1, x1 - 4):
        cv.rect(lx, top, 3, base - top - 4, OUT); cv.vline(lx + 1, top, base - top - 5, STEEL[5])
    for sy in (top, base - 14):
        cv.rect(x0, sy, x1 - x0, 5, OUT); cv.rect(x0 + 1, sy + 1, x1 - x0 - 2, 3, STEEL[4]); cv.hline(x0 + 1, sy + 1, x1 - x0 - 2, STEEL[6])
    cv.rect(x1 - 2, top - 10, 2, 12, STEEL[5]); cv.rect(x1 - 2, top - 11, 6, 2, OUT)              # push handle
    for cx_ in (x0 + 4, x1 - 9):
        cv.ellipse(cx_, base - 5, 6, 6, OUT); cv.px(cx_ + 2, base - 3, STEEL[5])
    # cylinders on top, plates below
    for k in range(5):
        cx_ = x0 + 5 + k * 12
        hh = 16 if k != 3 else 10
        cv.rect(cx_, top - hh, 9, hh, OUT); cv.rect(cx_ + 1, top - hh + 1, 7, hh - 1, CONC[7]); cv.vline(cx_ + 1, top - hh + 1, hh - 1, CONC[8])
        cv.ellipse(cx_ + 1, top - hh, 7, 3, CONC[8])
        if k == 1:
            cv.line(cx_ + 2, top - 12, cx_ + 6, top - 4, CONC[4])
        cv.rect(cx_ + 2, top - hh + 4, 5, 3, "#e8e4d8"); cv.px(cx_ + 3, top - hh + 5, "#5a5a6a")
    for k in range(3):
        py = base - 16 - k * 3
        cv.rect(x0 + 8 + k, py - 3, 30 - 2 * k, 3, OUT); cv.rect(x0 + 9 + k, py - 3, 28 - 2 * k, 2, IRON[3]); cv.hline(x0 + 9 + k, py - 3, 28 - 2 * k, IRON[4])
    cv.rect(x0 + 46, base - 24, 18, 10, OUT); cv.rect(x0 + 47, base - 23, 16, 8, SAFETY[2]); cv.hline(x0 + 47, base - 23, 16, SAFETY[3])
    return cv, W // 2, base


def flood_tripod(height=68, seed=0):
    """LED flood panel on a tripod; the panel's face sits ~h-5 above the floor."""
    W, Hc = 34, height + 6
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    cx = W // 2
    ground_shadow(cv, cx, base - 1, 13, 2)
    for ex in (cx - 12, cx + 12, cx + 2):
        cv.line(cx, base - 24, ex, base - 1, IRON[2]); cv.line(cx + 1, base - 24, ex + 1, base - 1, IRON[4])
    cv.rect(cx - 1, base - 58, 3, 35, OUT); cv.vline(cx, base - 58, 34, STEEL[5])
    cv.rect(cx - 2, base - 26, 5, 4, IRON[3])
    hy = base - 68
    cv.rect(cx - 11, hy, 22, 12, OUT); cv.rect(cx - 10, hy + 1, 20, 10, SAFETY[2]); cv.hline(cx - 10, hy + 1, 20, SAFETY[3])
    cv.rect(cx - 8, hy + 3, 16, 6, WARM[3]); cv.rect(cx - 6, hy + 4, 12, 4, WARM[4])
    cv.rect(cx - 2, hy + 12, 5, 3, IRON[3])
    cv.line(cx + 1, base - 50, cx + 10, base - 30, "#2a2a34"); cv.line(cx + 10, base - 30, cx + 15, base - 2, "#2a2a34")
    return cv, cx, base


def chain_barrier(width=120, height=26, label="KEEP CLEAR", seed=0):
    """Two weighted stanchions with a yellow-black chain and a hanging sign."""
    W, Hc = width + 6, height + 6
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 6, W - 7
    ground_shadow(cv, W // 2, base - 1, width // 2, 2)
    top = base - height
    for sx in (x0, x1):
        cv.ellipse(sx - 5, base - 3, 11, 4, OUT); cv.ellipse(sx - 4, base - 3, 9, 2, "#1a1524")
        cv.rect(sx - 1, top + 2, 4, base - top - 4, OUT)
        for k in range(top + 3, base - 3, 4):
            cv.rect(sx, k, 2, 2, SAFETY[3] if (k // 4) % 2 else "#1a1524")
        cv.rect(sx - 2, top, 6, 3, SAFETY[2])
    n = x1 - x0
    for i in range(n + 1):
        t = i / n
        yy = int(round(top + 4 + 10 * 4 * t * (1 - t)))
        cv.px(x0 + i, yy, SAFETY[3] if (i // 4) % 2 else "#1a1524")
        cv.px(x0 + i, yy + 1, OUT)
    sw = text_width(label) + 6
    sx = (W - sw) // 2
    sy = top + 12
    cv.rect(sx, sy, sw, 12, OUT); cv.rect(sx + 1, sy + 1, sw - 2, 10, SAFETY[2])
    text(cv, label, sx + 3, sy, "#1a1524")
    return cv, W // 2, base


def glow_sprite(rx, ry, colour="#f6cf7a", alphas=(0.08, 0.16, 0.3), core=None):
    """A transparent sprite of nested flat ellipses (for blinking/pulsing light layers)."""
    cv = Canvas(2 * rx + 1, 2 * ry + 1)
    n = len(alphas)
    for k, a in enumerate(alphas):
        sx, sy = rx * (n - k) // n, ry * (n - k) // n
        m = np.zeros((cv.h, cv.w), bool)
        ys, xs = np.mgrid[0:cv.h, 0:cv.w]
        m = ((xs - rx) / max(1, sx)) ** 2 + ((ys - ry) / max(1, sy)) ** 2 <= 1.0
        col = np.array(C(colour)[:3], np.float32)
        cv.a[m, :3] = col
        cv.a[m, 3] = np.maximum(cv.a[m, 3], a)
    if core:
        x, y, w, h, c = core
        cv.rect(rx + x, ry + y, w, h, c)
    return cv


# ------------------------------------------------------------------ E04 model level pieces

DECK = ["#24262e", "#30333c", "#3c4049", "#474b55", "#51565f", "#5c616a", "#6a6f78", "#7c818a"]


def checker_plate_np(w, h, seed=0, pal=DECK):
    """Diamond (checker) plate floor as an array: rows of short raised lugs alternating in
    direction, each with a lit edge and a shadow, over gently worn plate."""
    xs, ys = grid(w, h)
    p = P(pal)
    idx = np.full((h, w), 4, int)
    cx, cy = xs % 8, ys % 6
    flip = ((xs // 8 + ys // 6) % 2) == 0
    lug = np.where(flip, (cx - 2) == (cy * 2 // 3), (5 - cx) == (cy * 2 // 3)) & (cy < 3) & (cx >= 2) & (cx <= 5)
    lug_sh = np.roll(lug, 1, axis=0) & ~lug
    idx = np.where(lug, np.minimum(idx + 2, len(pal) - 1), idx)
    idx = np.where(lug_sh, idx - 1, idx)
    return p[idx]


def roof_truss(cv, x0, x1, y_top, y_bot, bay=40, colour=None):
    """Pratt roof trusses seen against the roof deck: top and bottom chords, verticals, diagonals."""
    c = colour or [STEEL[0], STEEL[2], STEEL[3]]
    cv.rect(x0, y_top, x1 - x0, 3, c[1]); cv.hline(x0, y_top + 2, x1 - x0, c[2])
    cv.rect(x0, y_bot, x1 - x0, 3, c[1]); cv.hline(x0, y_bot, x1 - x0, c[2])
    for k, bx in enumerate(range(x0, x1, bay)):
        cv.rect(bx, y_top, 2, y_bot - y_top, c[1])
        if k % 2 == 0:
            cv.line(bx + 2, y_top + 3, bx + bay, y_bot, c[1])
        else:
            cv.line(bx + 2, y_bot, bx + bay, y_top + 3, c[1])
        cv.px(bx, y_bot + 1, c[2]); cv.px(bx + 1, y_top + 1, c[2])


def flatirons_window(cv, x, y, w, h, seed=0, bay=48):
    """Tall clerestory onto the night: sky bands, stars, the Flatirons' slabs in silhouette, a
    scatter of campus windows and street lights below them. Returns twinkle points."""
    rng = np.random.default_rng(seed)
    pts = []
    sky = Canvas(w, h)
    for k in range(h):
        sky.hline(0, k, w, NIGHT_BANDS[min(len(NIGHT_BANDS) - 1, k * len(NIGHT_BANDS) // h)])
    for _ in range(w // 9):
        sx, sy = int(rng.integers(0, w)), int(rng.integers(0, h // 2))
        sky.px(sx, sy, "#c8ccec"); pts.append((x + sx, y + sy, "#e8ecff"))
    # the Flatirons: tilted slabs against the sky
    ridge = h * 3 // 5
    for k, sx in enumerate(range(-20, w, 70)):
        hgt = int(rng.integers(h // 3, h // 2))
        base_y = ridge + 10
        sky.poly([(sx, base_y), (sx + 22, base_y - hgt), (sx + 34, base_y - hgt + 6), (sx + 60, base_y)], "#1c1830")
        sky.line(sx + 22, base_y - hgt, sx + 34, base_y - hgt + 6, "#2c2644")
        sky.line(sx + 22, base_y - hgt, sx + 6, base_y - 4, "#26203a")
    sky.rect(0, ridge + 6, w, h - ridge - 6, "#141428")
    for _ in range(w // 14):                                   # campus windows and lamps
        lx, ly = int(rng.integers(0, w)), int(rng.integers(ridge + 9, h - 2))
        col = ("#f6cf7a", "#e9a84a", "#c8d0f0")[int(rng.integers(0, 3))]
        sky.px(lx, ly, col); pts.append((x + lx, y + ly, col))
    cv.rect(x - 2, y - 2, w + 4, h + 4, STEEL[0])
    cv.paste(sky, x, y)
    for mx in range(x + bay, x + w, bay):
        cv.rect(mx - 1, y, 3, h, STEEL[1]); cv.vline(mx - 1, y, h, STEEL[3])
    cv.rect(x, y + h // 2, w, 2, STEEL[1])
    for k in range(3):
        rx = x + 12 + k * bay * 2
        if rx < x + w - 12:
            cv.line(rx, y + h - 4, rx + 10, y + 4, C("#8a90c0", 0.25))
    cv.rect(x - 2, y + h, w + 4, 3, CONC[5]); cv.hline(x - 2, y + h, w + 4, CONC[7])
    return pts


def booth_window(cv, x, y, w, h, label="CONTROL"):
    """The control booth seen from the model level: a box on steel legs with a slanted window,
    screens glowing teal inside, a red REC lamp. Returns screen rects and the lamp point."""
    cv.rect(x, y, w, h, OUT)
    cv.rect(x + 1, y + 1, w - 2, h - 2, CONC[3]); cv.hline(x + 1, y + 1, w - 2, CONC[6])
    wx, wy, ww, wh = x + 6, y + 14, w - 12, h - 24
    cv.rect(wx, wy, ww, wh, "#0c1a1c")
    screens = []
    for k in range(3):
        sx = wx + 6 + k * (ww - 12) // 3
        sw = (ww - 12) // 3 - 6
        cv.rect(sx, wy + wh - 14, sw, 9, "#1e4448"); cv.hline(sx + 1, wy + wh - 11, sw - 2, "#4ac0b0")
        screens.append((sx, wy + wh - 14, sw, 9))
    cv.rect(wx, wy + wh - 4, ww, 4, "#1a1418")                  # console edge
    tint_rect(cv, wx, wy, ww, wh, "#4ac0b0", 0.12)
    cv.line(wx + 4, wy + wh - 2, wx + 16, wy + 2, C("#c8f0f0", 0.25)); cv.line(wx + 8, wy + wh - 2, wx + 20, wy + 2, C("#c8f0f0", 0.15))
    cv.rect(wx - 1, wy - 1, ww + 2, 2, STEEL[4])
    lw = text_width(label) + 8
    cv.rect(x + (w - lw) // 2, y + 2, lw, 11, OUT)
    text(cv, label, x + (w - lw) // 2 + 4, y + 1, "#e8e2d0")
    lamp = (x + (w + lw) // 2 + 6, y + 6)
    cv.rect(lamp[0] - 2, lamp[1] - 2, 5, 5, OUT); cv.rect(lamp[0] - 1, lamp[1] - 1, 3, 3, REC[1])
    for lx in (x + 8, x + w - 11):
        cv.rect(lx, y + h, 3, 10, STEEL[3]); cv.vline(lx, y + h, 10, STEEL[5])
    return screens, lamp


def pendant_control(cv, x, y_top, y_box):
    """The crane's hanging push-button pendant on its cable."""
    cv.vline(x, y_top, y_box - y_top, "#14121c")
    cv.rect(x - 4, y_box, 9, 18, OUT); cv.rect(x - 3, y_box + 1, 7, 16, CRANE[3]); cv.hline(x - 3, y_box + 1, 7, CRANE[5])
    for k, col in enumerate(("#3cba7a", "#1a1524", "#1a1524", "#c03a32")):
        cv.rect(x - 1, y_box + 3 + k * 3, 3, 2, col)


def grating_view(cv, x0, y0, x1, y1, seed=0):
    """A bar-grating panel in the deck with the test floor far below seen through it: dim strong
    floor with its anchor grid, the load frame from above, the walkway lines, the two foundation
    pads; steel bearing bars over all. Returns the pad centres (below)."""
    w, h = x1 - x0, y1 - y0
    xs, ys = grid(w, h)
    p = P(["#1a181f", "#221f27", "#2a2730", "#322e37", "#3a363f"])
    f = soft_field(w, h, 50, seed)
    idx = np.where(f < 0.3, 2, 3)
    put_rgb(cv, x0, y0, p[idx])
    # far floor: anchor grid, a walkway line, the frame from above
    for ay in range(y0 + 8, y1 - 2, 12):
        for ax in range(x0 + 6, x1 - 2, 18):
            cv.px(ax, ay, "#4a4a58")
    for (lx, ly, rx_, ry_) in ((x0 + w // 4, y0 + h // 2, w // 4, h // 3), (x0 + 3 * w // 4, y0 + h // 2, w // 4, h // 3)):
        soft_ellipse(cv, lx, ly, rx_, ry_, "#f6e0a8", 0.07)
        soft_ellipse(cv, lx, ly, rx_ * 2 // 3, ry_ * 2 // 3, "#f6e0a8", 0.06)
    cv.hline(x0, y1 - 22, w, C(SAFETY[1], 0.6)); cv.hline(x0, y1 - 14, w, C(SAFETY[1], 0.6))
    cv.rect(x0 + 40, y0 + 6, 120, 6, FRAME_BLUE[1]); cv.hline(x0 + 40, y0 + 6, 120, FRAME_BLUE[2])
    cv.rect(x0 + 44, y0 + 4, 8, 10, FRAME_BLUE[1]); cv.rect(x0 + 148, y0 + 4, 8, 10, FRAME_BLUE[1])
    cv.rect(x0 + 52, y0 + 12, 96, 3, "#2a2a30")
    pads = []
    for px_ in (x0 + w // 2 - 100, x0 + w // 2 + 100):
        py = y1 - 40
        cv.ellipse(px_ - 18, py - 6, 37, 13, C(SAFETY[1], 0.7))
        cv.ellipse(px_ - 15, py - 4, 31, 9, "#24222a")
        cv.rect(px_ - 10, py - 2, 21, 5, "#3a3d46")
        pads.append((px_, py))
    soft_ellipse(cv, x0 + w // 2, y0 + h // 2, w // 2 - 20, h // 2 - 20, "#f6cf7a", 0.05)
    # bearing bars and cross bars, frame edge
    for bx in range(x0, x1, 3):
        cv.vline(bx, y0, h, C(STEEL[3], 0.7))
    for by in range(y0 + 12, y1, 16):
        cv.hline(x0, by, w, C(STEEL[4], 0.85))
    cv.rect(x0 - 3, y0 - 3, w + 6, 3, STEEL[4]); cv.hline(x0 - 3, y0 - 3, w + 6, STEEL[6])
    cv.rect(x0 - 3, y1, w + 6, 3, STEEL[3]); cv.hline(x0 - 3, y1, w + 6, STEEL[5])
    cv.rect(x0 - 3, y0, 3, h, STEEL[3]); cv.rect(x1, y0, 3, h, STEEL[3])
    return pads


def stair_down_well(cv, x0, y0, x1, y1, seed=0):
    """A stair opening in the deck going down toward the viewer: treads darkening as they drop,
    yellow nosings, side rails seen from above, warm light rising from the test floor."""
    w, h = x1 - x0, y1 - y0
    cv.rect(x0 - 3, y0 - 3, w + 6, h + 6, STEEL[4]); cv.hline(x0 - 3, y0 - 3, w + 6, STEEL[6])
    cv.rect(x0, y0, w, h, "#0e0c14")
    n = 7
    for k in range(n):
        ty = y0 + 2 + k * (h - 4) // n
        t = k / n
        tone = mix(DECK[5], "#0e0c14", t * 0.9)
        cv.rect(x0 + 4, ty, w - 8, (h - 4) // n - 1, tone)
        cv.hline(x0 + 4, ty, w - 8, mix(SAFETY[2], "#0e0c14", t * 0.8))
    soft_ellipse(cv, x0 + w // 2, y1 - 4, w // 2, 6, "#f6cf7a", 0.12)
    for sx in (x0, x1 - 3):
        cv.rect(sx, y0 - 6, 3, h + 6, SAFETY[2]); cv.vline(sx, y0 - 6, h + 6, SAFETY[3])
    cv.rect(x0, y0 - 6, w, 2, SAFETY[2]); cv.hline(x0, y0 - 6, w, SAFETY[3])


# ------------------------------------------------------------------------------ E04 props

def guardrail(width=390, height=24, label="NO STANDING UNDER LOAD", seed=0):
    """Mezzanine guardrail: yellow top and mid rails on square posts, a toe board, a sign."""
    W, Hc = width + 6, height + 8
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 3, W - 3
    top = base - height + 2
    cv.rect(x0, base - 5, x1 - x0, 5, OUT); cv.rect(x0 + 1, base - 4, x1 - x0 - 2, 3, STEEL[3]); cv.hline(x0 + 1, base - 4, x1 - x0 - 2, STEEL[5])
    for k, px_ in enumerate(list(range(x0, x1 - 3, 48)) + [x1 - 4]):
        cv.rect(px_, top, 4, base - top - 4, OUT); cv.vline(px_ + 1, top + 1, base - top - 5, SAFETY[3]); cv.vline(px_ + 2, top + 1, base - top - 5, SAFETY[1])
    for ry, th in ((top, 4), (top + 9, 3)):
        cv.rect(x0, ry, x1 - x0, th, OUT); cv.hline(x0 + 1, ry + 1, x1 - x0 - 2, SAFETY[3])
        if th > 3:
            cv.hline(x0 + 1, ry + 2, x1 - x0 - 2, SAFETY[2])
    sw = text_width(label) + 8
    sx = (W - sw) // 2
    cv.rect(sx, top + 3, sw, 12, OUT); cv.rect(sx + 1, top + 4, sw - 2, 10, "#2c4a8a")
    text(cv, label, sx + 4, top + 3, "#f0ece0")
    return cv, W // 2, base


def drafting_table(width=120, height=42, seed=0):
    """Drafting table with the 'perfect arch' drawing pinned to its tilted board, a parallel rule,
    a lamp clamped to the edge, a stool tucked beside."""
    W, Hc = width + 8, height + 10
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 6, W - 22
    ground_shadow(cv, W // 2, base - 1, width // 2, 3)
    # legs (a steel H frame)
    for lx in (x0 + 6, x1 - 8):
        cv.rect(lx, base - 22, 3, 22, OUT); cv.vline(lx + 1, base - 22, 21, STEEL[5])
        cv.rect(lx - 3, base - 2, 9, 2, OUT)
    cv.rect(x0 + 6, base - 10, x1 - x0 - 12, 2, STEEL[4])
    # tilted board
    bt, bb = base - height + 4, base - 20
    cv.poly([(x0, bb), (x1, bb), (x1 - 4, bt), (x0 + 4, bt)], OUT)
    cv.poly([(x0 + 2, bb - 1), (x1 - 2, bb - 1), (x1 - 5, bt + 1), (x0 + 5, bt + 1)], "#d8d0bc")
    cv.rect(x0 + 1, bb, x1 - x0 - 2, 3, MAPLE[3]); cv.hline(x0 + 1, bb, x1 - x0 - 2, MAPLE[5])
    # the drawing: a grand arch with fine hangers, dimension lines, and nowhere to stand
    dx0, dx1 = x0 + 12, x1 - 12
    dy = bb - 5
    apex = bt + 4
    for xx in range(dx0, dx1 + 1):
        t = (xx - dx0) / (dx1 - dx0)
        yy = int(round(dy - (dy - apex) * 4 * t * (1 - t)))
        cv.px(xx, yy, BLUEPRINT[2])
        if (xx - dx0) % 4 == 2 and 0.06 < t < 0.94:
            cv.vline(xx, yy + 1, dy - yy - 1, C(BLUEPRINT[3], 0.6))
    cv.hline(dx0, dy, dx1 - dx0, BLUEPRINT[2])
    cv.hline(dx0, dy + 3, dx1 - dx0, C("#5a5a6a", 0.6)); cv.vline(dx0, dy + 2, 3, "#5a5a6a"); cv.vline(dx1, dy + 2, 3, "#5a5a6a")
    micro_text(cv, "PERFECT", x0 + 7, bt + 2, "#7a2a2a")
    cv.rect(x0 + 2, bb - 4, x1 - x0 - 4, 1, STEEL[6])                  # parallel rule
    # clamp lamp
    lx = x1 - 2
    cv.line(lx, bb, lx + 6, bt - 2, STEEL[4]); cv.line(lx + 6, bt - 2, lx - 2, bt - 8, STEEL[4])
    cv.poly([(lx - 6, bt - 10), (lx + 1, bt - 10), (lx + 2, bt - 5), (lx - 7, bt - 5)], "#2c4a8a")
    cv.hline(lx - 6, bt - 5, 8, WARM[3])
    # stool
    sx = x1 + 6
    cv.ellipse(sx, base - 20, 14, 5, OUT); cv.ellipse(sx + 1, base - 20, 12, 3, "#3a3a46")
    cv.line(sx + 3, base - 16, sx + 1, base - 1, STEEL[4]); cv.line(sx + 11, base - 16, sx + 13, base - 1, STEEL[4])
    cv.hline(sx + 2, base - 7, 11, STEEL[3])
    return cv, (x0 + x1) // 2 + 4, base


def cage_pole_lamp(height=68, seed=0):
    """Caged bulb on a steel pole with a weighted base, cord looped round a hook; bulb at h-5."""
    W, Hc = 24, height + 6
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    cx = W // 2
    ground_shadow(cv, cx, base - 1, 9, 2)
    cv.rect(cx - 6, base - 4, 13, 4, OUT); cv.rect(cx - 5, base - 3, 11, 2, IRON[3]); cv.hline(cx - 5, base - 3, 11, IRON[4])
    cv.rect(cx - 1, base - 58, 3, 55, OUT); cv.vline(cx, base - 58, 54, STEEL[5])
    cv.rect(cx - 4, base - 60, 9, 3, IRON[2])
    by = base - 63
    cv.ellipse(cx - 4, by - 5, 9, 11, OUT)
    cv.ellipse(cx - 3, by - 4, 7, 9, WARM[2]); cv.ellipse(cx - 2, by - 3, 5, 6, WARM[3]); cv.rect(cx - 1, by - 2, 2, 3, WARM[4])
    cv.vline(cx, by - 5, 11, C(OUT, 0.8)); cv.hline(cx - 3, by, 7, C(OUT, 0.8))
    for yy in range(base - 50, base - 6):
        cv.px(cx + 2 + int(round(2 * np.sin((yy - base + 50) / 44 * np.pi))), yy, "#24222f")
    cv.rect(cx + 2, base - 40, 3, 2, IRON[3])
    return cv, cx, base


# ------------------------------------------------------------------- E05 control booth

FOAM_E = ["#16141e", "#1e1b28", "#262232", "#2f2a3c", "#3a3448", "#463e56"]
WAINSCOT = ["#2a1c1a", "#3e2a24", "#563a2e", "#6e4c3a", "#8a6248"]


def acoustic_foam(cv, x, y, w, h, seed=0, tile=16, trim=64):
    """Wedge acoustic foam in tiles of alternating ridge direction, framed by thin wood battens."""
    xs, ys = grid(w, h)
    p = P(FOAM_E)
    tx, ty = (xs + x) // tile, (ys + y) // tile
    u, v = (xs + x) % tile, (ys + y) % tile
    vert = ((tx + ty) % 2) == 0
    ridge = np.where(vert, u % 4, v % 4)
    idx = np.choose(ridge, [2, 4, 3, 1])
    edge = (u == 0) | (v == 0)
    idx = np.where(edge, 1, idx)
    put_rgb(cv, x, y, p[idx])
    for bx in range(x, x + w, trim):
        cv.rect(bx, y, 3, h, WAINSCOT[2]); cv.vline(bx, y, h, WAINSCOT[3])
    cv.rect(x, y, w, 3, WAINSCOT[2]); cv.hline(x, y, w, WAINSCOT[4]); cv.rect(x, y + h - 3, w, 3, WAINSCOT[1])


def wainscot(cv, x, y, w, h):
    """Dark wood wainscot with vertical boards and a lit cap rail."""
    cv.rect(x, y, w, h, WAINSCOT[2])
    for bx in range(x, x + w, 12):
        cv.vline(bx, y, h, WAINSCOT[1]); cv.vline(bx + 1, y, h, WAINSCOT[3])
    cv.rect(x, y, w, 3, WAINSCOT[3]); cv.hline(x, y, w, WAINSCOT[4]); cv.hline(x, y + 3, w, WAINSCOT[0])
    cv.rect(x, y + h - 3, w, 3, "#141016")


def booth_ceiling(cv, w, h=16):
    """Dark acoustic ceiling tiles with two rows of recessed can lights; returns the lights."""
    cv.rect(0, 0, w, h, "#18161f")
    for xx in range(0, w, 24):
        cv.vline(xx, 0, h, "#24212d")
    cv.hline(0, h // 2, w, "#24212d")
    pts = []
    for xx in range(60, w, 120):
        cv.rect(xx - 4, h - 4, 9, 3, "#2e2a38"); cv.rect(xx - 2, h - 3, 5, 2, WARM[3])
        pts.append((xx, h - 2))
    cv.hline(0, h - 1, w, "#0e0c14")
    return pts


def observation_window(cv, x, y, w, h, seed=0):
    """The booth's window onto the high bay: the crane girder, the suspended model with its amber
    lights hanging in the dark, the far clerestory and the glow of the test floor below.
    Returns light points (model lights) and the crane beacon point."""
    rng = np.random.default_rng(seed)
    view = Canvas(w, h, fill="#12101a")
    for k in range(h):
        if k > h * 2 // 3:
            view.hline(0, k, w, mix("#12101a", "#3a2c24", (k - h * 2 / 3) / (h / 3) * 0.8))
    # far clerestory band
    view.rect(0, 10, w, 12, "#1c1a34")
    for wx in range(4, w, 30):
        view.rect(wx, 11, 24, 10, NIGHT_BANDS[2]); view.px(wx + int(rng.integers(2, 20)), 13, "#c8ccec")
    view.rect(0, 3, w, 5, CRANE[2]); view.hline(0, 3, w, CRANE[4])
    # the model, hanging
    mx0, mx1, deck = w // 6, w * 5 // 6, h // 2 + 10
    for cx in (mx0 + 12, mx1 - 12):
        view.vline(cx, 8, deck - 8, STEEL[4])
    prev = None
    for xx in range(mx0, mx1):
        t = (xx - mx0) / (mx1 - mx0)
        yy = int(round(deck - 2 - 20 * 4 * t * (1 - t)))
        view.px(xx, yy, BLUEPRINT[4])
        if (xx - mx0) % 8 == 0 and 0.05 < t < 0.95:
            view.vline(xx, yy + 1, deck - yy - 1, BLUEPRINT[2])
    view.rect(mx0 - 2, deck, mx1 - mx0 + 4, 4, BLUEPRINT[3]); view.hline(mx0 - 2, deck, mx1 - mx0 + 4, BLUEPRINT[5])
    pts = []
    for lx in range(mx0 + 4, mx1, 10):
        view.px(lx, deck + 4, WARM[3]); pts.append((x + lx, y + deck + 4))
    soft_ellipse(view, w // 2, h - 6, w // 2, 10, "#f6cf7a", 0.12)
    cv.rect(x - 3, y - 3, w + 6, h + 6, WAINSCOT[1])
    cv.paste(view, x, y)
    for mx in range(x + w // 3, x + w, w // 3):
        cv.rect(mx - 1, y, 3, h, WAINSCOT[1]); cv.vline(mx - 1, y, h, WAINSCOT[3])
    for k in range(3):
        rx = x + 20 + k * w // 3
        cv.line(rx, y + h - 3, rx + 18, y + 3, C("#c8d0f0", 0.12)); cv.line(rx + 5, y + h - 3, rx + 23, y + 3, C("#c8d0f0", 0.08))
    cv.rect(x - 3, y + h, w + 6, 4, WAINSCOT[3]); cv.hline(x - 3, y + h, w + 6, WAINSCOT[4])
    beacon = (x + w - 18, y + 5)
    return pts, beacon


def status_screen(cv, x, y, w, h):
    """The booth's main status screen (bezel, graticule, header). Returns the trace area."""
    cv.rect(x - 4, y - 4, w + 8, h + 8, OUT); cv.rect(x - 3, y - 3, w + 6, h + 6, "#2a2a34"); cv.hline(x - 3, y - 3, w + 6, "#44444f")
    cv.rect(x, y, w, h, SCOPE[0])
    for gx in range(x + 4, x + w, 8):
        for gy in range(y + 14, y + h - 2, 6):
            cv.px(gx, gy, SCOPE[1])
    cv.rect(x, y, w, 11, SCOPE[1])
    micro_text(cv, "CH1  SOURCE", x + 4, y + 3, SCOPE[4])
    micro_text(cv, "--:--", x + w - 26, y + 3, SCOPE[3])
    cv.rect(x + w // 2 - 6, y + h + 4, 12, 4, "#2a2a34")
    return (x + 4, y + 16, w - 8, h - 22)


def wave_frame(w, h, k, n, seed=0):
    """One frame of the scrolling playback waveform (bars, voice-like)."""
    cv = Canvas(w, h)
    rng = np.random.default_rng(seed)
    amps = 0.25 + 0.75 * np.abs(np.sin(np.arange(w + n * 4) * 0.21)) * rng.random(w + n * 4) ** 0.5
    mid = h // 2
    for xx in range(0, w, 2):
        a = amps[xx + k * 4]
        hh = max(1, int(a * (h // 2 - 1)))
        cv.vline(xx, mid - hh, 2 * hh, SCOPE[3])
        cv.px(xx, mid - hh, SCOPE[4]); cv.px(xx, mid + hh - 1, SCOPE[4])
    cv.vline(w * 2 // 3, 0, h, C(SCOPE[5], 0.6))
    return cv


def recovered_card(w, h):
    """'SOURCE RECOVERED' card for the status screen once the reel is found: a still, full
    waveform and the words in amber."""
    cv = Canvas(w, h, fill=SCOPE[0])
    for xx in range(2, w - 2, 2):
        a = 0.3 + 0.7 * abs(np.sin(xx * 0.17)) * (0.6 + 0.4 * abs(np.sin(xx * 0.05)))
        hh = max(1, int(a * 10))
        cv.vline(xx, h - 14 - hh, 2 * hh, SCOPE[2])
    tw = text_width("SOURCE RECOVERED")
    cv.rect((w - tw) // 2 - 3, 8, tw + 6, 12, "#2a1c0c")
    text(cv, "SOURCE RECOVERED", (w - tw) // 2, 8, "#f6cf7a")
    cv.rect(0, 0, w, 1, SCOPE[1])
    return cv


def wall_tape_deck(cv, x, y, w=80, h=56):
    """A wall-mounted reel-to-reel deck above the meters: two reels (their faces are animated by
    layers), heads, transport buttons. Returns reel centres and radius."""
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#5a5664"); cv.hline(x + 1, y + 1, w - 2, "#7a7684")
    r = 15
    centres = [(x + 4 + r + 1, y + 4 + r + 1), (x + w - 5 - r - 1, y + 4 + r + 1)]
    for (cx, cy) in centres:
        cv.ellipse(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, "#2a2832")
    hx = x + w // 2
    cv.rect(hx - 8, y + h - 18, 16, 8, "#2a2832"); cv.rect(hx - 6, y + h - 16, 4, 4, STEEL[6]); cv.rect(hx + 2, y + h - 16, 4, 4, STEEL[6])
    cv.line(centres[0][0], centres[0][1] + r, hx - 6, y + h - 14, "#5a3a28"); cv.line(hx + 6, y + h - 14, centres[1][0], centres[1][1] + r, "#5a3a28")
    for k, col in enumerate(("#3a3a46", "#3a3a46", "#3a3a46", "#c03a32")):
        cv.rect(x + 8 + k * 9, y + h - 7, 7, 4, OUT); cv.rect(x + 9 + k * 9, y + h - 6, 5, 2, col)
    return centres, r


def led_meter(cv, x, y, n=4, hgt=30):
    """A wall LED level meter: n bars of segments (dim); returns bar rects for animation."""
    cv.rect(x, y, n * 6 + 4, hgt + 8, OUT); cv.rect(x + 1, y + 1, n * 6 + 2, hgt + 6, "#14121a")
    bars = []
    for k in range(n):
        bx = x + 3 + k * 6
        for s in range(0, hgt, 3):
            sy = y + 3 + s
            t = s / hgt
            col = "#c03a32" if t < 0.2 else ("#e8b45c" if t < 0.4 else "#2a7a4a")
            cv.rect(bx, sy, 4, 2, shade(col, -0.55))
        bars.append((bx, y + 3, 4, hgt))
    micro_text(cv, "VU", x + 2, y + hgt + 9, "#c8c0b0")
    return bars


def studio_monitor(cv, x, y, flip=False):
    """A studio monitor speaker on a wall bracket."""
    cv.rect(x, y, 16, 22, OUT); cv.rect(x + 1, y + 1, 14, 20, "#24222c"); cv.hline(x + 1, y + 1, 14, "#3a3844")
    cv.ellipse(x + 3, y + 3, 10, 10, OUT); cv.ellipse(x + 4, y + 4, 8, 8, "#3a3844"); cv.ellipse(x + 6, y + 6, 4, 4, "#14121a")
    cv.ellipse(x + 5, y + 14, 6, 6, OUT); cv.px(x + 7, y + 16, "#5a5866")
    bx = x + (17 if not flip else -4)
    cv.rect(bx, y + 8, 3, 6, STEEL[3])


def patch_bay(cv, x, y, w=60, rows=3, seed=0):
    """A patch bay with rows of jacks and a few looping patch cables."""
    rng = np.random.default_rng(seed)
    h = rows * 6 + 4
    cv.rect(x, y, w, h, OUT); cv.rect(x + 1, y + 1, w - 2, h - 2, "#2a2832")
    jacks = []
    for r in range(rows):
        for jx in range(x + 3, x + w - 2, 4):
            cv.px(jx, y + 3 + r * 6, "#0c0a10"); cv.px(jx, y + 4 + r * 6, STEEL[5])
            jacks.append((jx, y + 3 + r * 6))
    for k in range(5):
        a, b = jacks[int(rng.integers(0, len(jacks)))], jacks[int(rng.integers(0, len(jacks)))]
        col = ("#c03a32", "#2c4a9a", "#e8b45c", "#2a7a4a", "#d8d4c8")[k]
        wire(cv, a[0], a[1], b[0], b[1], 6 + k * 2, col)
    return h


def carpet_np(w, h, seed=0, tile=24):
    """Quarter-turned carpet tiles: fine ribs alternating direction, a whisper of tone change."""
    xs, ys = grid(w, h)
    p = P(CARPET)
    tx, ty = xs // tile, ys // tile
    vert = ((tx + ty) % 2) == 0
    rib = np.where(vert, xs % 3 == 0, ys % 3 == 0)
    idx = 3 - rib.astype(int)
    seam = ((xs % tile) == 0) | ((ys % tile) == 0)
    idx = np.where(seam, 2, idx)
    fine = hashn(xs, ys, seed + 2)
    idx = np.where(fine > 0.992, 4, idx)
    return p[np.clip(idx, 0, len(CARPET) - 1)]


def lift_gate(w, h, closed=True):
    """The service lift's scissor gate in the near-wall opening (closed lattice, or folded open)
    with its status lamp."""
    cv = Canvas(w, h)
    if closed:
        for k in range(0, w, 8):
            cv.line(k, 0, k + 8, h - 1, STEEL[5]); cv.line(k + 8, 0, k, h - 1, STEEL[5])
        cv.hline(0, 0, w, STEEL[6]); cv.hline(0, h - 1, w, STEEL[3])
        cv.rect(w // 2 - 6, h // 2 - 3, 12, 7, "#c03a32"); micro_text(cv, "NO", w // 2 - 4, h // 2 - 2, "#ffe0d0")
    else:
        for k in range(0, 8, 2):
            cv.vline(k, 0, h, STEEL[5]); cv.vline(w - 1 - k, 0, h, STEEL[5])
    return cv


# ------------------------------------------------------------------------------ E05 props

def console_reel(width=220, height=60, reel=True, seed=0):
    """The booth's recording console: fader bed, meter bridge, a talkback mic, a small monitor, and
    an upright reel-to-reel deck holding the source reel (reel=False: the reel has been taken, an
    empty spindle and a note left behind)."""
    from lib_norlin2 import reel_face
    W, Hc = width + 8, height + 22
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 4, W - 4
    rng = np.random.default_rng(seed)
    ground_shadow(cv, W // 2, base - 1, width // 2 + 2, 3)
    # body
    cv.rect(x0, base - 30, x1 - x0, 30, OUT)
    cv.rect(x0 + 1, base - 29, x1 - x0 - 2, 28, "#2a2630"); cv.hline(x0 + 1, base - 29, x1 - x0 - 2, "#3e3a46")
    for px_ in range(x0 + 10, x1 - 10, 40):
        cv.rect(px_, base - 24, 30, 18, "#24202a"); cv.hline(px_, base - 24, 30, "#36323e")
    cv.rect(x0 + 1, base - 3, x1 - x0 - 2, 2, "#141118")
    # fader bed seen from above, with the padded arm rest in front
    by0 = base - 44
    cv.rect(x0, by0, x1 - x0, 15, OUT); cv.rect(x0 + 1, by0 + 1, x1 - x0 - 2, 13, "#4a4652")
    for ch in range(x0 + 6, x1 - 8, 7):
        cv.vline(ch + 2, by0 + 6, 7, "#1a1820")
        fy = by0 + 7 + int(rng.integers(0, 5))
        cv.rect(ch + 1, fy, 3, 2, ("#d8d4c8", "#d8d4c8", "#c03a32", "#e8b45c", "#2c4a9a")[int(rng.integers(0, 5))])
        for ky in (by0 + 2, by0 + 4):
            cv.px(ch + 2, ky, ("#c03a32", "#e8b45c", "#2a7a4a", "#8a8696")[int(rng.integers(0, 4))])
    cv.rect(x0, base - 30, x1 - x0, 3, "#1a1418"); cv.hline(x0, base - 30, x1 - x0, "#3a2c2c")
    # meter bridge
    mx0 = x0 + 92
    cv.rect(mx0, by0 - 9, 100, 9, OUT); cv.rect(mx0 + 1, by0 - 8, 98, 7, "#2a2630")
    for k in range(6):
        vx = mx0 + 4 + k * 16
        cv.rect(vx, by0 - 7, 12, 5, "#e8c87a"); cv.line(vx + 3, by0 - 3, vx + 7 + (k % 3), by0 - 6, "#1a1418")
    # talkback mic and a small monitor on an arm
    cv.line(x1 - 18, by0, x1 - 26, by0 - 12, STEEL[4]); cv.rect(x1 - 29, by0 - 15, 5, 4, "#1a1418")
    cv.rect(x1 - 20, by0 - 26, 18, 13, OUT); cv.rect(x1 - 19, by0 - 25, 16, 11, "#1e4448"); cv.hline(x1 - 18, by0 - 20, 14, "#4ac0b0")
    cv.vline(x1 - 11, by0 - 13, 13, STEEL[3])
    # the reel-to-reel deck standing on the console's left end
    dx0, dw, dh = x0 + 8, 78, 30
    dy0 = by0 - dh + 4
    cv.rect(dx0, dy0, dw, dh, OUT); cv.rect(dx0 + 1, dy0 + 1, dw - 2, dh - 2, "#6a6674"); cv.hline(dx0 + 1, dy0 + 1, dw - 2, "#8a8694")
    r = 11
    left = (dx0 + 4, dy0 - 6)
    right = (dx0 + dw - 4 - (2 * r + 3), dy0 - 6)
    if reel:
        cv.paste(reel_face(r, 0.4, 0.7), *left)
    else:
        cv.ellipse(left[0] + r - 2, left[1] + r - 2, 7, 7, OUT); cv.ellipse(left[0] + r - 1, left[1] + r - 1, 5, 5, STEEL[5])
        cv.rect(left[0] + 1, left[1] + r + 5, 24, 9, PAPER[3]); micro_text(cv, "TAKEN", left[0] + 3, left[1] + r + 7, "#c03a32")
    cv.paste(reel_face(r, 1.1, 0.35), *right)
    hx = dx0 + dw // 2
    cv.rect(hx - 6, dy0 + dh - 12, 12, 6, "#2a2832"); cv.rect(hx - 4, dy0 + dh - 10, 3, 3, STEEL[6]); cv.rect(hx + 1, dy0 + dh - 10, 3, 3, STEEL[6])
    for k, col in enumerate(("#3a3a46", "#3a3a46", "#3a3a46", "#c03a32")):
        cv.rect(dx0 + 6 + k * 8, dy0 + dh - 5, 6, 3, col)
    micro_text(cv, "SOURCE", dx0 + dw - 30, dy0 + dh - 12, "#e8e2d0")
    return cv, W // 2, base


def log_rack(width=110, height=94, label="LAST CALL", seed=0):
    """Equipment rack beside a pin board with the booth log on a clipboard (signed by a night
    marshal), under a red LAST CALL lightbox."""
    W, Hc = width + 6, height + 4
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 3, W - 3
    rng = np.random.default_rng(seed)
    ground_shadow(cv, W // 2, base - 1, width // 2, 3)
    top = base - height + 16
    # rack (left)
    rw = 44
    cv.rect(x0, top, rw, base - top, OUT); cv.rect(x0 + 1, top + 1, rw - 2, base - top - 2, "#1e1c26")
    yy = top + 3
    k = 0
    while yy < base - 8:
        uh = (6, 9, 6, 12, 6)[k % 5]
        cv.rect(x0 + 3, yy, rw - 6, uh, "#3a3846"); cv.hline(x0 + 3, yy, rw - 6, "#5a5866")
        for j in range(3):
            cv.px(x0 + 6 + j * 3, yy + 2, ("#3cba7a", "#e8b45c", "#c03a32")[(j + k) % 3])
        if uh == 12:
            cv.ellipse(x0 + 18, yy + 2, 8, 8, "#2a2832"); cv.ellipse(x0 + 29, yy + 2, 8, 8, "#2a2832")
        elif uh == 9:
            cv.rect(x0 + 16, yy + 3, 20, 3, "#0a120e"); cv.hline(x0 + 17, yy + 4, 18, SCOPE[3])
        yy += uh + 1
        k += 1
    # pin board (right) with the log clipboard and notes
    bx = x0 + rw + 3
    bw = x1 - bx
    cv.rect(bx, top + 4, bw, base - top - 20, OUT); cv.rect(bx + 1, top + 5, bw - 2, base - top - 22, KRAFT_E[2])
    for _ in range(40):
        cv.px(bx + 2 + int(rng.integers(0, bw - 4)), top + 6 + int(rng.integers(0, base - top - 24)), KRAFT_E[1])
    cx_, cy_ = bx + 8, top + 10
    cv.rect(cx_, cy_, 30, 40, OUT); cv.rect(cx_ + 1, cy_ + 1, 28, 38, "#7a5a3a")
    cv.rect(cx_ + 3, cy_ + 5, 24, 32, PAPER[3]); cv.rect(cx_ + 10, cy_ - 1, 10, 5, STEEL[5]); cv.hline(cx_ + 10, cy_ - 1, 10, STEEL[7])
    micro_text(cv, "LOG", cx_ + 10, cy_ + 7, "#262830")
    for r in range(5):
        scribble(cv, cx_ + 5, cy_ + 15 + r * 4, 18, "#5a5a6a", seed=r)
    cv.line(cx_ + 6, cy_ + 34, cx_ + 12, cy_ + 31, MARKER["blue"]); cv.line(cx_ + 12, cy_ + 31, cx_ + 18, cy_ + 35, MARKER["blue"])
    cv.line(cx_ + 18, cy_ + 35, cx_ + 24, cy_ + 32, MARKER["blue"])                     # the marshal's signature
    cv.rect(bx + bw - 18, top + 12, 14, 12, "#e8d070"); scribble(cv, bx + bw - 17, top + 15, 11, "#8a7428", 3, rows=2)
    cv.rect(bx + bw - 20, top + 30, 16, 14, PAPER[2]); scribble(cv, bx + bw - 19, top + 33, 13, "#5a5a6a", 4, rows=3)
    cv.px(bx + bw - 12, top + 30, "#c03a32")
    # a low cabinet under the board
    cv.rect(bx, base - 16, bw, 16, OUT); cv.rect(bx + 1, base - 15, bw - 2, 14, WAINSCOT[2]); cv.hline(bx + 1, base - 15, bw - 2, WAINSCOT[4])
    cv.vline(bx + bw // 2, base - 14, 12, WAINSCOT[0]); cv.rect(bx + bw // 2 - 4, base - 9, 2, 3, BRASS_E); cv.rect(bx + bw // 2 + 3, base - 9, 2, 3, BRASS_E)
    # the LAST CALL lightbox on top
    lw = text_width(label) + 10
    lx = (W - lw) // 2
    cv.rect(lx, 0, lw, 14, OUT); cv.rect(lx + 1, 1, lw - 2, 12, "#a8322c"); cv.hline(lx + 1, 1, lw - 2, "#e06a5a")
    text(cv, label, lx + 5, 1, "#ffe8d8")
    cv.vline(lx + 6, 14, top - 14, STEEL[3]); cv.vline(lx + lw - 7, 14, top - 14, STEEL[3])
    return cv, W // 2, base


KRAFT_E = ["#6a4a30", "#8a6440", "#a87e52", "#c49a68", "#dcb888"]
BRASS_E = "#d4a656"


def tape_archive(width=110, height=100, seed=0):
    """Walnut shelving of tape boxes: square boxes with dated spines, some lying flat, one gap
    where the earliest reel was kept, an ARCHIVE plate on top."""
    W, Hc = width + 6, height + 4
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    x0, x1 = 3, W - 3
    rng = np.random.default_rng(seed)
    ground_shadow(cv, W // 2, base - 1, width // 2, 3)
    top = base - height + 12
    cv.rect(x0, top, x1 - x0, base - top, OUT); cv.rect(x0 + 1, top + 1, x1 - x0 - 2, base - top - 2, WAINSCOT[1])
    rows = 4
    rh = (base - top - 6) // rows
    for r in range(rows):
        sy = top + 3 + (r + 1) * rh
        xx = x0 + 4
        while xx < x1 - 12:
            if r == 1 and 40 < xx < 56:
                cv.rect(xx, sy - 12, 12, 12, "#120e12"); micro_text(cv, "?", xx + 5, sy - 9, "#5a4a44")
                xx += 13
                continue
            if rng.random() < 0.12:
                for k in range(3):                      # a short stack lying flat
                    cv.rect(xx, sy - 3 - k * 3, 16, 3, OUT); cv.rect(xx + 1, sy - 3 - k * 3, 14, 2, ("#c8bca4", "#9aa8c0", "#c8a07a")[k])
                xx += 18
                continue
            bw = int(rng.integers(5, 8))
            bh = rh - 4 - int(rng.integers(0, 3))
            col = ("#c8bca4", "#e6d6b1", "#9aa8c0", "#c8a07a", "#a8322c", "#2c4a8a")[int(rng.integers(0, 6))]
            cv.rect(xx, sy - bh, bw, bh, OUT); cv.rect(xx + 1, sy - bh + 1, bw - 2, bh - 1, col)
            cv.hline(xx + 1, sy - bh + 4, bw - 2, shade(col, -0.35)); cv.hline(xx + 1, sy - bh + 6, bw - 2, shade(col, -0.35))
            xx += bw
        cv.rect(x0 + 1, sy, x1 - x0 - 2, 3, WAINSCOT[3]); cv.hline(x0 + 1, sy, x1 - x0 - 2, WAINSCOT[4])
    lw = text_width("ARCHIVE") + 8
    lx = (W - lw) // 2
    cv.rect(lx, 0, lw, 12, OUT); cv.rect(lx + 1, 1, lw - 2, 10, BRASS_E); text(cv, "ARCHIVE", lx + 4, 0, "#2a1c14")
    return cv, W // 2, base


def drum_floor_lamp(height=68, seed=0):
    """Brass floor lamp with a cream drum shade; the bulb glows at the shade's foot ~h-5 up."""
    W, Hc = 30, height + 6
    cv = Canvas(W, Hc, seed=seed)
    base = Hc - 2
    cx = W // 2
    ground_shadow(cv, cx, base - 1, 10, 2)
    cv.ellipse(cx - 7, base - 4, 15, 5, OUT); cv.ellipse(cx - 6, base - 4, 13, 3, "#a87a36"); cv.hline(cx - 4, base - 4, 8, "#e8c070")
    cv.rect(cx - 1, base - 60, 3, 57, OUT); cv.vline(cx, base - 60, 56, "#d4a656")
    sy = base - 74
    cv.rect(cx - 10, sy, 21, 13, OUT)
    cv.rect(cx - 9, sy + 1, 19, 11, "#e6d6b1"); cv.vline(cx - 9, sy + 1, 11, "#f6ecd2"); cv.vline(cx + 8, sy + 1, 11, "#c8b48c")
    cv.rect(cx - 9, sy + 10, 19, 2, "#f6cf7a")
    cv.rect(cx - 3, sy + 12, 7, 1, WARM[4])
    return cv, cx, base


# ------------------------------------------------------------------ battle-scale pieces (1:1)

def big_hook_frame(drop, dx, w=44):
    """A crane hook drawn at battle scale: two rope falls from the top centre to a yellow sheave
    block offset by dx (one swing frame), the swivel and a big J hook with its latch."""
    cv = Canvas(w, drop + 46)
    cx = w // 2
    bx = cx + dx
    for k in (-4, 3):
        cv.line(cx + k, 0, bx + k, drop, STEEL[2]); cv.line(cx + k + 1, 0, bx + k + 1, drop, STEEL[5])
    cv.rect(bx - 10, drop, 21, 19, OUT)
    cv.rect(bx - 9, drop + 1, 19, 17, CRANE[3]); cv.hline(bx - 9, drop + 1, 19, CRANE[5])
    cv.vline(bx - 9, drop + 1, 17, CRANE[4]); cv.vline(bx + 9, drop + 1, 17, CRANE[1])
    cv.ellipse(bx - 6, drop + 2, 13, 9, CRANE[1]); cv.ellipse(bx - 5, drop + 3, 11, 7, CRANE[2])
    cv.rect(bx - 1, drop + 5, 3, 3, STEEL[4]); cv.px(bx, drop + 6, STEEL[6])
    cv.rect(bx - 9, drop + 12, 19, 6, "#1a1524")                  # hazard stripes on the cheek plate
    for k in range(-9, 10, 4):
        cv.line(bx + k, drop + 17, bx + k + 3, drop + 12, CRANE[4])
        cv.line(bx + k + 1, drop + 17, bx + k + 4, drop + 12, CRANE[4])
    cv.rect(bx - 3, drop + 19, 7, 5, OUT); cv.rect(bx - 2, drop + 19, 5, 4, STEEL[4]); cv.hline(bx - 2, drop + 19, 5, STEEL[6])
    hy = drop + 24
    path = [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5), (0, 6), (0, 7), (-1, 8), (-1, 9), (-2, 10), (-3, 11),
            (-4, 11), (-5, 11), (-6, 10), (-7, 9), (-8, 8), (-8, 7), (-8, 6), (-8, 5), (-7, 4)]
    for (px_, py_) in path:
        cv.rect(bx + px_ - 1, hy + py_ - 1, 4, 3, OUT)
    for (px_, py_) in path:
        cv.px(bx + px_, hy + py_, STEEL[5]); cv.px(bx + px_ + 1, hy + py_, STEEL[4])
    cv.px(bx + 1, hy + 1, STEEL[7]); cv.px(bx + 1, hy + 2, STEEL[7]); cv.px(bx - 4, hy + 11, STEEL[3])
    cv.line(bx - 7, hy + 3, bx - 1, hy, CRANE[4]); cv.line(bx - 7, hy + 4, bx - 1, hy + 1, CRANE[2])
    return cv


def load_curve_frame(w, h, k, n, peak=184):
    """One frame of a load-displacement plot being drawn: axes, the curve rising and softening up to
    step k of n, a bright cursor at its tip, and the load readout."""
    cv = Canvas(w, h, fill=SCOPE[0])
    for gx in range(6, w, 6):
        for gy in range(8, h - 2, 4):
            cv.px(gx, gy, SCOPE[1])
    cv.vline(3, 7, h - 9, SCOPE[2]); cv.hline(3, h - 3, w - 5, SCOPE[2])
    f = (k + 1) / n
    xs = list(range(4, 4 + int((w - 8) * f)))
    prev = None
    for xx in xs:
        t = (xx - 4) / (w - 8)
        load = 1 - (1 - min(1.0, t / 0.75)) ** 2 if t < 0.75 else 1 - 0.08 * (t - 0.75) / 0.25
        yy = int(round(h - 4 - load * (h - 13)))
        if prev is not None and abs(yy - prev) > 1:
            lo, hi = sorted((prev, yy))
            cv.vline(xx, lo, hi - lo + 1, SCOPE[3])
        cv.px(xx, yy, SCOPE[4])
        prev = yy
    if xs:
        cv.rect(xs[-1] - 1, prev - 1, 3, 3, SCOPE[5])
    micro_text(cv, f"{int(round(peak * f))} KN", 5, 1, SCOPE[4])
    return cv
