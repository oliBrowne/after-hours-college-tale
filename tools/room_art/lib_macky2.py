"""Macky Auditorium, the last three rooms (M05 balcony, M06 graduation stage, M07 dawn exit) and
their battle backdrops. Self-contained (it does not import lib_macky.py, which another painter is
writing at the same time) but follows the same sources: atlas cell 4 (Macky's buff sandstone,
twin crenellated towers, ivy, red tile roof), the house in macky_environment.gd, and the campus
families in props.py / interior.py / facade.py and the finished lib_norlin*.py.

Everything paints at 1:1 game pixels against a 52px character. Sections:
  palettes ........ MACKY (sandstone of cell 4), MROOF, IVY, HOUSE (lamplit plaster), GILT, SEAT,
                    CARPET_M, CARD, VAL_TEAL, GOWN, CU_GOLD, EXIT, dawn families (SKY_DAWN,
                    GRASS_DAWN, PAVE_DAWN, ALPEN, FOREST_DAWN)
  sky & land ...... dawn_sky, dawn_clouds, flatirons_dawn, campus_dawn, macky_tower,
                    garden_wall, gate_piers
  house ........... coffer_ceiling, chandelier, house_window, sconce_m, proscenium, curtain_m,
                    reserved_card, seat_row_back, seat_row_front, stalls_rows, exit_sign,
                    lightbox, theatre_door, carpet_m, oak_stage_floor
  stage set ....... grad_set (risers of reserved chairs, VAL's frame, banner), flown_chair,
                    ghost_light (prop), line_array (prop), stage_lip (prop)
  props ........... brass_rail (prop), seating_chart (prop), velvet_bench (prop), lobby_lamp (prop),
                    reserved_row (prop), dawn_bench (prop), dawn_lamp (prop), sunlit_tree (prop),
                    sun_shadow
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, LEAF, MUM, AMBER, ground_shadow, shrub

# --- palettes ---------------------------------------------------------------------------------
MACKY = ["#3a2220", "#5c3731", "#7d4e41", "#a36748", "#b26e4b", "#c17a50", "#cd8554", "#e29b56"]   # cell 4 sandstone
MROOF = ["#34171b", "#502623", "#6c2a24", "#794034", "#9f5433", "#be7144"]                          # tile roof
IVY = ["#0a171c", "#1b2723", "#1e2d26", "#2f3a29", "#46502e", "#5e6634"]
IVY_RED = ["#4a1a1c", "#7a2a26", "#a83c32", "#c8582e"]                                              # Boston ivy in October
LIMESTONE = ["#5e5450", "#857868", "#a8977e", "#c2b096", "#d8c8aa", "#ece0c4"]
HOUSE = ["#1e141c", "#2a1c24", "#3a262c", "#4c3434", "#5e423e", "#72544a", "#886658", "#a07c68"]    # lamplit plaster
GILT = ["#3e2814", "#6a4620", "#946a2c", "#c09440", "#e0bc62", "#f6dc96"]
SEAT = ["#1a0a10", "#2e0e16", "#4a1620", "#66202a", "#842c34", "#a43c40", "#c05a54"]              # red velvet
CARPET_M = ["#1a0c12", "#2a1018", "#3e1620", "#561e28", "#6e2830", "#b07a3c", "#d8a858"]          # balcony carpet
CARD = ["#8a7e70", "#c8bca4", "#ece2c8", "#fff8e6"]                                                # RESERVED cards
CARD_RED = "#9a2a2c"
VAL_TEAL = ["#0c1820", "#14283a", "#1c3a4e", "#285064", "#38687a", "#58908e"]                     # VAL's frame
GOWN = ["#24101a", "#3e1626", "#5a1e32", "#7a2a40"]
CU_GOLD = ["#5a4a2a", "#8a7444", "#b89c62", "#d6bc80", "#ecd8a4"]                                   # CU gold, black
CU_BLACK = ["#0e0c12", "#18161e", "#24222c", "#34323e"]
EXIT = ["#0e2a1c", "#1c4a34", "#2e8a5a", "#3cba7a", "#9ef0c0"]
OAKF = ["#1e1210", "#2e1c16", "#40281e", "#543426", "#68422e", "#7e5238", "#966444"]              # stage boards

# dawn families
SKY_DAWN = ["#5f7cb4", "#6c88bc", "#7c94c2", "#8e9ec8", "#a2a8cc", "#b6aecc", "#c8b2c6", "#d8b6bc",
            "#e4bab4", "#ecc2ae", "#f2ccae", "#f6d6b4"]
CLOUD_DAWN = ["#8c84a8", "#a49cbc", "#b4a8c4", "#c2aec4", "#dcb0b4", "#f4c4a4", "#fde0bc"]
ALPEN = ["#6a4458", "#8a5260", "#b06a6a", "#d08a76", "#e8a684", "#f4c098", "#fcdcb8"]               # sunlit slab faces
FOREST_DAWN = ["#2a2632", "#38323a", "#4a4240", "#5e5444", "#74644a", "#8c7650", "#a48a5a"]
HAZE_DAWN = ["#8a7c98", "#9c8ca4", "#ae9cae", "#c0acb4", "#d2bcbc"]
GRASS_DAWN = ["#202a20", "#2c3826", "#38482c", "#465832", "#566a38", "#6a7e40", "#82924a", "#a0a65a"]
SHADOW_DAWN = "#24343a"
PAVE_DAWN = ["#4e3630", "#6e4e42", "#8a6450", "#9c745c", "#ae8468", "#c29a7a", "#d8b490"]
DEW = ["#d8e8e0", "#fff6e0"]
SUN = ["#f6c47a", "#fbd896", "#fff0c8"]


def _rng(seed):
    return np.random.default_rng(abs(int(seed)))


def halo(cv, cx, cy, r, colour="#f6cf7a", strength=0.12, steps=3):
    """Stepped round glow (three crisp rings, no gradient)."""
    for i in range(steps):
        rr = int(r * (1 - i / steps))
        cv.ellipse(cx - rr, cy - rr, rr * 2 + 1, rr * 2 + 1, C(colour, strength / steps * (i + 1) * 0.8))


def band_ramp(cv, x, y, w, h, pal, seed=0, ragged=0.35, curve=1.0):
    """Stepped colour bands from top to bottom of a rect, joins ragged by a checker of the band
    above (the painted-sky join used by the other groups)."""
    rng = _rng(seed)
    n = len(pal)
    prev = None
    for yy in range(y, y + h):
        t = ((yy - y) / max(1, h - 1)) ** curve
        k = min(n - 1, int(t * n))
        cv.hline(x, yy, w, pal[k])
        if prev is not None and k != prev:
            for xx in range(x, x + w, 2):
                if rng.random() < ragged:
                    cv.px(xx + int(rng.integers(0, 2)), yy, pal[prev])
        prev = k


# ============================================================================================
# sky and land at dawn (M07 and its battle)
# ============================================================================================
def dawn_sky(cv, x, y, w, h, seed=0, pal=SKY_DAWN, curve=0.9):
    """The western sky just after sunrise: clear blue overhead easing through lavender into a
    rose-and-peach haze above the mountains (the sun is behind the viewer)."""
    band_ramp(cv, x, y, w, h, pal, seed=seed, curve=curve)


def dawn_clouds(width, height, seed=1, count=5, sizes=(60, 140), pal=CLOUD_DAWN):
    """Long flat morning clouds lit rose and gold from below, on a tileable transparent strip."""
    from clouds import cloud_strip
    return cloud_strip(width, height, count=count, seed=seed, pal=pal, sizes=sizes)


def _ridge(x0, x1, pts, rng, jag=1.0):
    """Piecewise-linear ridge through control points [(t, height)], small jagged noise."""
    xs = np.arange(x0, x1 + 1)
    ts = (xs - x0) / max(1, x1 - x0)
    tp, hp = zip(*pts)
    hgt = np.interp(ts, tp, hp)
    noise = np.cumsum(rng.normal(0, 0.6 * jag, len(xs)))
    noise -= np.linspace(noise[0], noise[-1], len(xs))
    hgt = hgt + np.clip(noise, -4, 4) + rng.integers(0, 2, len(xs)) * jag
    return xs, hgt


def _forest_fill(cv, xs, tops, base, pal, rng, lit_from_top=True, haze=None, haze_from=0.6, density=0.55):
    """Fill under a ridge with conifer stipple: a mid-tone body, little trees (lit tip, dark foot),
    darker gullies; optional haze toward the base."""
    for i, x in enumerate(xs):
        top = int(round(tops[i]))
        for yy in range(top, base):
            t = (yy - top) / max(1, base - top)
            c = pal[3] if t < 0.25 else pal[2] if t < 0.7 else pal[1]
            if haze is not None and t > haze_from:
                c = mix(c, haze, min(0.6, (t - haze_from) * 1.4))
            cv.px(int(x), yy, c)
        cv.px(int(x), top, pal[4])
    # little trees
    for i in range(0, len(xs), 2):
        x = int(xs[i])
        top = int(round(tops[i]))
        for yy in range(top + 2, base - 1, 3):
            if rng.random() > density:
                continue
            tx = x + int(rng.integers(-1, 2))
            t = (yy - top) / max(1, base - top)
            hi = pal[5] if t < 0.3 else pal[4] if t < 0.65 else pal[3]
            cv.px(tx, yy - 1, hi); cv.px(tx, yy, pal[4] if t < 0.5 else pal[3]); cv.px(tx + 1, yy, pal[1]); cv.px(tx, yy + 1, pal[0])


def flatirons_dawn(cv, x0, x1, base, seed=0, scale=1.0):
    """The Flatirons from campus just after sunrise, the light low from behind the viewer: the
    far peaks hazy rose, Green Mountain's forest warm olive with blue gullies, and the great
    tilted sandstone slabs blazing pink-orange (alpenglow), bedding ribs running down their faces,
    pines dark at their feet; the lower slopes still in cool morning haze. Returns slab apexes."""
    rng = _rng(seed)
    span = x1 - x0
    s = scale
    # 1. far peaks (Bear Peak, South Boulder Peak to the left, the Divide haze to the right)
    xs, far = _ridge(x0, x1, [(0, 52 * s), (0.08, 70 * s), (0.16, 84 * s), (0.22, 66 * s), (0.34, 60 * s), (0.5, 64 * s),
                              (0.66, 58 * s), (0.78, 50 * s), (0.9, 44 * s), (1.0, 38 * s)], rng, 0.8)
    for i, x in enumerate(xs):
        top = int(base - far[i])
        for yy in range(top, base):
            t = (yy - top) / max(1, base - top)
            cv.px(int(x), yy, HAZE_DAWN[3] if t < 0.08 else HAZE_DAWN[2] if t < 0.45 else HAZE_DAWN[1])
        cv.px(int(x), top, HAZE_DAWN[4])
    # 2. Green Mountain: forested bulk, warm on top, blue in the gullies
    xs, gm = _ridge(x0, x1, [(0, 30 * s), (0.12, 46 * s), (0.3, 62 * s), (0.44, 74 * s), (0.52, 76 * s), (0.6, 70 * s),
                             (0.74, 56 * s), (0.86, 44 * s), (1.0, 34 * s)], rng, 1.0)
    tops = base - gm
    _forest_fill(cv, xs, tops, base, FOREST_DAWN, rng, haze=HAZE_DAWN[1], haze_from=0.55)
    # spurs and gullies running down the slope (diagonal shadow strokes, lit crests)
    for k in range(int(span / 26)):
        gx = x0 + int(rng.integers(0, span))
        i = gx - x0
        if not (0 <= i < len(xs)):
            continue
        top = int(tops[i]) + 3
        L = int(rng.integers(12, 30))
        d = 1 if rng.random() < 0.5 else -1
        for j in range(L):
            px_, py_ = gx + int(d * j * 0.55), top + j
            if py_ >= base - 2:
                break
            cv.px(px_, py_, FOREST_DAWN[1]); cv.px(px_ + 1, py_, FOREST_DAWN[0] if j % 3 else FOREST_DAWN[1])
            cv.px(px_ - d, py_, FOREST_DAWN[4] if j < L * 0.5 else FOREST_DAWN[3])
    # 3. the slabs (left to right: the First, Second and Third Flatiron with smaller ones between)
    slabs = [(0.20, 0.13, 50), (0.31, 0.09, 36), (0.40, 0.15, 60), (0.53, 0.12, 52), (0.63, 0.08, 34), (0.71, 0.14, 46), (0.82, 0.08, 28)]
    apexes = []
    for k, (c, hw, hgt) in enumerate(slabs):
        hgt = int(round(hgt * s))
        cx = x0 + int(c * span)
        w = int(hw * span)
        top = base - int(gm[min(len(gm) - 1, cx - x0)] * 0.25) - hgt
        foot = base - 6
        ax = cx - w // 4
        left = cx - w // 2
        right = cx + w // 2
        pts = [(left, foot), (ax - 3, top + 6), (ax, top), (ax + 3, top + 2), (right, foot)]
        cv.poly([(p[0] - 1, p[1]) for p in pts[:3]] + [(pts[3][0] + 1, pts[3][1] - 1), (pts[4][0] + 1, pts[4][1])], ALPEN[0])
        cv.poly(pts, ALPEN[3])
        # lit face (most of the slab) and a narrow shaded north edge
        face = [(ax, top + 1), (ax + 3, top + 3), (right - 2, foot), (left + int(w * 0.28), foot)]
        cv.poly(face, ALPEN[4])
        hi = [(ax, top + 2), (ax + 2, top + 4), (ax + int(w * 0.32), foot - int(hgt * 0.4)), (ax + int(w * 0.1), foot - int(hgt * 0.3))]
        cv.poly(hi, ALPEN[5])
        cv.px(ax, top, ALPEN[6]); cv.px(ax + 1, top + 1, ALPEN[6])
        # bedding ribs down the face
        for j in range(1, 7):
            xa = ax + int(w * 0.07 * j)
            ya = top + 2 + j * 2
            xb = xa + int((right - xa) * 0.55)
            col = ALPEN[3] if j % 2 else ALPEN[6] if j < 3 else ALPEN[5]
            cv.line(xa, ya, xb, foot - 1, col)
        # cracks / ledges across
        for j in range(3):
            ly = top + int(hgt * (0.35 + 0.2 * j))
            lx = left + int((ly - top) / max(1, hgt) * (ax - left)) + 3
            cv.line(lx, ly, lx + int(w * 0.25), ly + 2, ALPEN[2])
        # the shaded left (west) edge and a dark wooded gully below it
        cv.line(left, foot, ax - 1, top + 3, ALPEN[1])
        for yy in range(top + int(hgt * 0.5), foot + 1):
            gw = int((yy - top) * 0.18)
            for xx in range(left - gw, left + 1):
                cv.px(xx, yy, FOREST_DAWN[1] if (xx + yy) % 3 else FOREST_DAWN[0])
        apexes.append((ax, top))
    # 4. pines on the lower slopes and a cool morning haze at the very bottom
    for _ in range(span * 2):
        px_ = x0 + int(rng.integers(0, span))
        py_ = base - int(abs(rng.normal(0, 6))) - 1
        c = FOREST_DAWN[1] if rng.random() < 0.6 else FOREST_DAWN[2]
        cv.px(px_, py_, c); cv.px(px_, py_ - 1, FOREST_DAWN[3] if rng.random() < 0.4 else c)
    for yy in range(base - 5, base):
        for xx in range(x0, x1, 1):
            if (xx + yy) % 2 == 0:
                cv.px(xx, yy, C(HAZE_DAWN[2], 0.35))
    return apexes


def campus_dawn(cv, x0, x1, base, seed=0, skip=(), gap=None):
    """The campus across the quad in the first sun: autumn crowns lit gold on the side facing
    the viewer, red tile hip roofs over sandstone walls, windows flashing the low sun. gap: a
    (xa, xb) span where Norlin's portico shows between the trees."""
    rng = _rng(seed)
    # back row: rooftops between trees
    x = x0
    while x < x1:
        bw, bh = int(rng.integers(44, 86)), int(rng.integers(12, 20))
        if any(a <= x <= b for a, b in skip) or rng.random() < 0.25:
            x += bw // 2
            continue
        top = base - bh - 10
        cv.rect(x, top, bw, bh + 10, MACKY[4])
        cv.vline(x, top, bh + 10, MACKY[6]); cv.vline(x + bw - 1, top, bh + 10, MACKY[2])
        for cy in range(top + 3, base, 4):
            cv.hline(x + 1, cy, bw - 2, MACKY[3])
        cv.poly([(x - 4, top), (x + 8, top - 9), (x + bw - 8, top - 9), (x + bw + 3, top)], MROOF[3])
        cv.hline(x + 8, top - 9, bw - 16, MROOF[5]); cv.hline(x - 3, top, bw + 6, MROOF[1])
        for tx in range(x - 2, x + bw + 2, 3):
            cv.vline(tx, top - 7 + (2 if tx < x + 6 or tx > x + bw - 6 else 0), 6, MROOF[4])
        for wx in range(x + 5, x + bw - 6, 8):
            cv.rect(wx, top + 4, 3, 5, "#3a2a34")
            if rng.random() < 0.35:
                cv.rect(wx, top + 4, 3, 2, SUN[1])
        x += bw + int(rng.integers(10, 40))
    if gap:
        ga, gb = gap
        norlin_far(cv, (ga + gb) // 2, base - 6, gb - ga)
    # front row: autumn tree crowns, lit on the viewer side
    pals = [["#5a2a20", "#8a3a26", "#c05a2c", "#e08a3c", "#f4b45a"],
            ["#5a4020", "#8a6224", "#c0902e", "#e0b844", "#f6d878"],
            ["#4a2a24", "#7a3428", "#a84a30", "#cc6a3a", "#e8945a"],
            ["#2a3424", "#3e4a2c", "#566234", "#74803e", "#98a050"]]
    x = x0 - 10
    while x < x1 + 10:
        if gap and gap[0] - 6 < x < gap[1] + 6:
            x += 8
            continue
        r = int(rng.integers(9, 16))
        hh = int(rng.integers(14, 26))
        pal = pals[int(rng.integers(len(pals)))]
        cx, cy = x, base - hh // 2 - 2
        cv.ellipse(cx - r, cy - hh // 2, r * 2, hh, pal[1])
        for _ in range(r * 3):
            a = rng.uniform(0, 2 * np.pi)
            d = np.sqrt(rng.uniform(0, 1))
            px_, py_ = int(cx + np.cos(a) * d * (r - 2)), int(cy + np.sin(a) * d * (hh / 2 - 2))
            lit = py_ < cy + 1
            cv.rect(px_, py_, 2, 2, pal[3] if lit else pal[2])
            if lit and rng.random() < 0.4:
                cv.px(px_, py_, pal[4])
        cv.vline(cx, cy + hh // 2 - 2, 4, "#3a2420")
        x += int(rng.integers(12, 22))
    cv.rect(x0, base - 3, x1 - x0, 3, mix(GRASS_DAWN[4], HAZE_DAWN[2], 0.3))


def norlin_far(cv, cx, base, w):
    """Norlin Library's columned west front across the quad, small with distance, lit gold."""
    h = 34
    x = cx - w // 2
    cv.rect(x - 6, base - h - 8, w + 12, h + 8, LIMESTONE[3])
    cv.poly([(x - 10, base - h - 8), (x + 4, base - h - 16), (x + w - 4, base - h - 16), (x + w + 10, base - h - 8)], MROOF[3])
    cv.hline(x + 4, base - h - 16, w - 8, MROOF[5])
    cv.rect(x - 6, base - h - 8, w + 12, 4, LIMESTONE[5]); cv.hline(x - 6, base - h - 4, w + 12, LIMESTONE[1])
    cv.rect(x, base - h, w, h, "#4a3a3c")
    for k, colx in enumerate(range(x + 2, x + w - 2, 7)):
        cv.rect(colx, base - h, 4, h, LIMESTONE[4]); cv.vline(colx, base - h, h, LIMESTONE[5]); cv.vline(colx + 3, base - h, h, LIMESTONE[2])
    for wx in range(x + 7, x + w - 6, 7):
        cv.rect(wx, base - h + 8, 2, 12, SUN[0]); cv.px(wx, base - h + 8, SUN[2])
    cv.rect(x - 8, base - 3, w + 16, 3, LIMESTONE[3]); cv.hline(x - 8, base - 3, w + 16, LIMESTONE[5])


def macky_tower(cv, x, w, top, base, seed=0, light="left", crenel=True, windows=((0.5, 0.25, 9, 24),), ivy=0.5,
                pal=MACKY, sun=True):
    """One of Macky's square sandstone towers at true scale: rough ashlar courses, quoined
    corners, tall arched slit windows, Boston ivy (red in October) climbing from the foot.
    With sun=True the face is lit gold from the low sun and the far corner falls into shadow."""
    from surfaces import ashlar_wall
    rng = _rng(seed)
    wall = [pal[1], pal[2], pal[3], pal[4], pal[5], pal[7] if sun else pal[6]]
    ashlar_wall(cv, x, top, w, base - top, wall, course=6, seed=seed, cap=False)
    # quoins and shadowed return
    for k, qy in enumerate(range(top + 2, base - 4, 8)):
        qw = 10 if k % 2 == 0 else 7
        cv.rect(x, qy, qw, 7, pal[6] if sun else pal[5]); cv.hline(x, qy, qw, pal[7]); cv.hline(x, qy + 6, qw, pal[3])
        cv.rect(x + w - qw, qy, qw, 7, pal[4]); cv.hline(x + w - qw, qy, qw, pal[6]); cv.hline(x + w - qw, qy + 6, qw, pal[2])
    if crenel and top > 0:
        for cx_ in range(x, x + w, 14):
            cv.rect(cx_, top - 9, 8, 9, pal[5]); cv.hline(cx_, top - 9, 8, pal[7]); cv.vline(cx_ + 7, top - 9, 9, pal[3])
    for (fx, fy, ww, wh) in windows:
        wx = x + int(fx * w) - ww // 2
        wy = top + int(fy * (base - top)) if fy < 1 else int(fy)
        cv.rect(wx - 3, wy - 2, ww + 6, wh + 5, LIMESTONE[2]); cv.hline(wx - 3, wy - 2, ww + 6, LIMESTONE[4])
        cv.ellipse(wx - 3, wy - ww // 2 - 4, ww + 6, ww + 6, LIMESTONE[2])
        cv.ellipse(wx - 1, wy - ww // 2 - 2, ww + 2, ww + 2, "#1e1820")
        cv.rect(wx - 1, wy, ww + 2, wh + 1, "#1e1820")
        cv.rect(wx, wy, ww, wh, "#2c2836"); cv.vline(wx + ww // 2, wy - ww // 2 + 1, wh + ww // 2 - 1, "#1e1820")
        if sun:
            cv.rect(wx + 1, wy + 2, ww // 2 - 1, wh // 2, SUN[1]); cv.px(wx + 1, wy + 2, SUN[2])
        cv.rect(wx - 4, wy + wh + 1, ww + 8, 3, LIMESTONE[3]); cv.hline(wx - 4, wy + wh + 1, ww + 8, LIMESTONE[5])
    # ivy: dense at the foot, thinning upward, green with October red
    for _ in range(int(w * (base - top) * ivy * 0.25)):
        t = rng.random() ** 0.6
        yy = int(base - 1 - t * (base - top) * 0.9)
        xx = x + int(rng.integers(0, w))
        if rng.random() > 1 - t * 0.6:
            continue
        c = IVY_RED[int(rng.integers(1, 4))] if rng.random() < 0.45 else IVY[int(rng.integers(2, 6))]
        cv.rect(xx, yy, 2, 2, c); cv.px(xx, yy + 2, IVY[1])
    cv.hline(x, base - 1, w, C("#0d0b16", 0.5))


def garden_wall(cv, x0, x1, top, base, seed=0, pal=MACKY, hedge=True, sun=True):
    """A low sandstone garden wall with a limestone coping and a clipped hedge behind it."""
    from surfaces import ashlar_wall
    rng = _rng(seed)
    if hedge:
        for x in range(x0 - 4, x1 + 4, 7):
            hh = int(rng.integers(8, 13))
            cv.ellipse(x, top - hh, int(rng.integers(10, 15)), hh * 2, "#2e3a28" if rng.random() < 0.6 else "#36442c")
        for x in range(x0, x1, 3):
            if rng.random() < 0.5:
                cv.px(x, top - int(rng.integers(6, 11)), "#5e6a38" if sun else "#3f5741")
                if sun and rng.random() < 0.4:
                    cv.px(x + 1, top - int(rng.integers(5, 10)), "#7e8444")
    wall = [pal[1], pal[2], pal[3], pal[4], pal[5], pal[7] if sun else pal[6]]
    ashlar_wall(cv, x0, top + 4, x1 - x0, base - top - 4, wall, course=5, seed=seed, cap=False)
    cv.rect(x0 - 1, top, x1 - x0 + 2, 4, LIMESTONE[4]); cv.hline(x0 - 1, top, x1 - x0 + 2, LIMESTONE[5])
    cv.hline(x0 - 1, top + 3, x1 - x0 + 2, LIMESTONE[1])
    cv.hline(x0, base - 1, x1 - x0, C("#0d0b16", 0.45))


def gate_pier(cv, cx, top, base, lamp=True, lit=0.4, pal=MACKY):
    """A square sandstone gate pier with a limestone cap and an iron lantern on top."""
    w = 16
    x = cx - w // 2
    cv.rect(x - 1, top, w + 2, base - top, OUT)
    cv.rect(x, top + 1, w, base - top - 1, pal[4]); cv.vline(x, top + 1, base - top - 1, pal[7]); cv.vline(x + 1, top + 1, base - top - 1, pal[6])
    cv.vline(x + w - 1, top + 1, base - top - 1, pal[2])
    for yy in range(top + 6, base - 2, 6):
        cv.hline(x + 1, yy, w - 2, pal[3])
    cv.rect(x - 3, top - 4, w + 6, 5, LIMESTONE[3]); cv.hline(x - 3, top - 4, w + 6, LIMESTONE[5]); cv.hline(x - 3, top, w + 6, LIMESTONE[1])
    if lamp:
        from lib_norlin import lantern_head
        glass = (mix("#e9a84a", "#c8b8b0", 1 - lit), mix("#f6cf7a", "#e0d0c8", 1 - lit), mix("#fff0c4", "#f0e8e0", 1 - lit))
        lantern_head(cv, cx, top - 23, glass=glass)
        cv.rect(cx - 1, top - 6, 2, 3, IRON[2])
    return (cx, top - 16)


def sun_shadow(cv, x, y, length, width, angle_deg=-35, colour=SHADOW_DAWN, alpha=0.45, taper=0.5, mask=None):
    """A long morning shadow cast across the ground from (x, y), pointing away from the low sun
    (angle in screen degrees, -90 = straight up). Flat, stepped edge."""
    a = np.deg2rad(angle_deg)
    dx, dy = np.cos(a), np.sin(a)
    nx, ny = -dy, dx
    pts_l, pts_r = [], []
    for k in range(0, int(length) + 1, 2):
        t = k / max(1, length)
        hw = width / 2 * (1 - taper * t)
        cx_, cy_ = x + dx * k, y + dy * k * 0.55
        pts_l.append((cx_ + nx * hw, cy_ + ny * hw * 0.55))
        pts_r.append((cx_ - nx * hw, cy_ - ny * hw * 0.55))
    poly = pts_l + pts_r[::-1]
    from PIL import Image, ImageDraw
    m = Image.new("L", (cv.w, cv.h), 0)
    ImageDraw.Draw(m).polygon([tuple(p) for p in poly], fill=255)
    m = np.array(m) > 0
    if mask is not None:
        m &= mask
    cv.fill_mask(m, C(colour, alpha))
    return m


# --- the Flatirons at sunrise, recoloured from the game's own title painting ------------------
FOREST_SUN = ["#262c3a", "#2e3642", "#384048", "#464c50", "#565a56", "#6a6a5a", "#827a60"]     # pines in shade
ALP_SUN = ["#5e3040", "#823c48", "#a44c4e", "#c45e54", "#dc745a", "#ec8e62", "#f6aa72", "#fcca92"]  # alpenglow on rock


def _ramp(pal, t):
    t = np.clip(t, 0, 0.999) * (len(pal) - 1)
    i = np.floor(t).astype(int)
    f = t - i
    P = np.array([C(p)[:3] for p in pal])
    return P[i] * (1 - f[..., None]) + P[np.minimum(i + 1, len(pal) - 1)] * f[..., None]


def title_flatirons(scale=1.6, colors=30, x0=712, x1=1262, lift=0.0):
    """The Flatirons and Green Mountain as the title painting shows them, repainted for the first
    minutes after sunrise: the east-facing slabs blaze in alpenglow (rose to peach), the pine
    slopes between them stay in cool blue shadow, lit along every crest. Returns (rgba, ridge):
    a float RGBA array whose alpha is the mountain, and the per-column y of the skyline."""
    from PIL import Image
    from scipy import ndimage
    from midlib import ART, downscale, quantize
    img = np.array(Image.open(f"{ART}/boulder-title-v2.png").convert("RGBA")).astype(np.float32) / 255.0
    crop = img[110:330, x0:x1].copy()
    small = downscale(crop, (round(crop.shape[1] / scale), round(crop.shape[0] / scale)))
    small[..., 3] = 1
    lum = small[..., :3] @ np.array([0.3, 0.55, 0.15])
    H, W = lum.shape
    ridge = np.full(W, H, int)
    for x in range(W):
        col = lum[:, x]
        for y in range(H - 4):
            if col[y] < 0.36 and (col[y + 1:y + 4] < 0.6).all():
                ridge[x] = y
                break
    ridge = ndimage.median_filter(ridge, 9)
    mask = np.arange(H)[:, None] >= ridge[None, :]
    r, b = small[..., 0], small[..., 2]
    warm = np.clip((r - b + 0.02) / 0.14, 0, 1) ** 0.8
    lo, hi = np.percentile(lum[mask], 3), np.percentile(lum[mask], 99)
    tl = (lum - lo) / (hi - lo)
    out = _ramp(FOREST_SUN, tl * 1.25 + lift) * (1 - warm[..., None]) + _ramp(ALP_SUN, tl * 1.1 + 0.05) * warm[..., None]
    res = np.concatenate([out, mask[..., None].astype(np.float32)], -1)
    q = quantize(res, colors)
    q[..., 3] = mask
    return q, ridge


def ridge_extend(src, ridge, new_ridge, height, seed=0, haze=None, haze_amt=0.0, block=(18, 40), avoid_warm=True):
    """Continue the title range sideways: each new column borrows a real column of the painting
    (in runs, so the texture stays coherent), shifted so its crest sits on new_ridge. Optional
    haze (colour, 0..1) for the far ranges. Returns float RGBA of len(new_ridge) x height."""
    rng = _rng(seed)
    H, W = src.shape[:2]
    # columns without big slabs (mostly pine) are the ones to borrow
    warmth = np.array([np.mean(src[ridge[x]:min(H, ridge[x] + 60), x, 0] - src[ridge[x]:min(H, ridge[x] + 60), x, 2])
                       for x in range(W)])
    pool = [x for x in range(4, W - 4) if (not avoid_warm or warmth[x] < np.percentile(warmth, 55)) and ridge[x] < H - 70]
    out = np.zeros((height, len(new_ridge), 4), np.float32)
    i = 0
    while i < len(new_ridge):
        run = int(rng.integers(*block))
        s0 = int(rng.choice(pool))
        for k in range(run):
            if i >= len(new_ridge):
                break
            sx = min(W - 1, s0 + k)
            top = int(new_ridge[i])
            col = src[ridge[sx]:, sx]
            n = min(len(col), height - top)
            if n > 0:
                out[top:top + n, i] = col[:n]
                if n < height - top:
                    out[top + n:, i] = col[-1]
            i += 1
    if haze is not None and haze_amt > 0:
        hz = np.array(C(haze)[:3])
        a = out[..., 3:4]
        out[..., :3] = out[..., :3] * (1 - haze_amt) + hz * haze_amt
        out[..., 3:4] = a
    return out


# --- the campus across the quad in the first sun -------------------------------------------------
AUTUMN = [["#5a2a20", "#8a3a26", "#c05a2c", "#e08a3c", "#f4b45a"],
          ["#5a4020", "#8a6224", "#c0902e", "#e0b844", "#f6d878"],
          ["#4a2a24", "#7a3428", "#a84a30", "#cc6a3a", "#e8945a"],
          ["#2a3424", "#3e4a2c", "#566234", "#74803e", "#98a050"]]
SPRUCE = ["#121c22", "#1a2a2e", "#24383a", "#2f4a44", "#3e5e4e", "#6a7a52", "#a49058"]   # blue spruce, lit tips


def spruce(cv, cx, base, h, seed=0, lit=True, pal=SPRUCE, width=0.42):
    """A Colorado blue spruce: tiers of drooping boughs on a narrow cone, dark blue-green, the
    boughs on the sun side (left) tipped with low gold light."""
    rng = _rng(seed)
    top = base - h
    for yy in range(top, base):
        t = (yy - top) / max(1, h)
        tier = (yy - top) % 5
        hw = max(1, int(h * width * 0.5 * t * (0.75 + 0.25 * tier / 4)))
        hw += int(rng.integers(0, 2))
        cv.hline(cx - hw, yy, hw * 2 + 1, pal[1] if tier < 3 else pal[2])
        cv.px(cx - hw, yy, pal[0]); cv.px(cx + hw, yy, pal[0])
        if tier == 4:
            cv.hline(cx - hw, yy, hw, pal[3])
            if lit:
                cv.hline(cx - hw - 1, yy, max(1, hw // 2), pal[5])
                cv.px(cx - hw - 1, yy, pal[6])
        if tier == 0 and t > 0.1:
            cv.hline(cx + 1, yy, hw, pal[0])
    cv.vline(cx, top - 2, 3, pal[3] if not lit else pal[5])
    cv.rect(cx - 1, base - 2, 3, 2, "#2a1c18")


def campus_morning(cv, x0, x1, base, seed=0, gate=None, tower_x=None, rows_top=24):
    """Campus across the quad, seen over the garden wall in the first sun: a far treeline, red
    tile hip roofs on buff sandstone (their east walls lit, windows flashing), Old Main's clock
    tower, blue spruces and autumn crowns. base: the row the band stands on (the wall top)."""
    rng = _rng(seed)
    solid = np.zeros((cv.h, cv.w), bool)
    before = cv.a[..., 3].copy()
    # 1. far treeline in morning haze
    for x in range(x0 - 6, x1 + 6, 5):
        r = int(rng.integers(5, 10))
        cv.ellipse(x, base - rows_top - int(rng.integers(0, 6)), r * 2, r * 2 + 10, "#7a6a6e" if rng.random() < 0.5 else "#86747a")
        cv.ellipse(x + 2, base - rows_top - int(rng.integers(-2, 4)), r, r, "#a08486")
    # 2. buildings
    x = x0 - 20
    blds = []
    while x < x1:
        bw, bh = int(rng.integers(50, 110)), int(rng.integers(12, 22))
        blds.append((x, bw, bh))
        x += bw + int(rng.integers(14, 60))
    for (bx, bw, bh) in blds:
        top = base - bh - 6
        wall = [MACKY[3], MACKY[4], MACKY[5], MACKY[6], MACKY[7]]
        cv.rect(bx, top, bw, bh + 6, wall[2])
        for cy in range(top + 3, base, 4):
            cv.hline(bx + 1, cy, bw - 2, wall[1])
            for jx in range(bx + 3 + (cy // 4 % 2) * 5, bx + bw - 2, 10):
                cv.px(jx, cy - 1, wall[1])
        cv.vline(bx, top, bh + 6, wall[4]); cv.vline(bx + bw - 1, top, bh + 6, wall[0])
        rh = int(rng.integers(8, 12))
        cv.poly([(bx - 4, top + 1), (bx + rh + 2, top - rh), (bx + bw - rh - 2, top - rh), (bx + bw + 3, top + 1)], MROOF[2])
        cv.poly([(bx - 3, top), (bx + rh + 2, top - rh + 1), (bx + bw - rh - 2, top - rh + 1), (bx + bw + 2, top)], MROOF[3])
        cv.hline(bx + rh + 2, top - rh, bw - 2 * rh - 4, MROOF[5])
        for tx in range(bx, bx + bw, 3):
            cv.vline(tx, top - rh + 3 if bx + rh < tx < bx + bw - rh else top - 3, rh - 2 if bx + rh < tx < bx + bw - rh else 3, MROOF[4])
        cv.hline(bx - 4, top + 1, bw + 8, MROOF[1])
        # dormer / chimney
        if rng.random() < 0.5:
            dx_ = bx + int(rng.integers(rh + 4, max(rh + 5, bw - rh - 10)))
            cv.rect(dx_, top - rh - 4, 4, 6, MACKY[4]); cv.hline(dx_, top - rh - 4, 4, MACKY[6])
        # two storeys of arched windows; some catch the sun
        for wy in (top + 4, top + 4 + max(6, bh // 2)):
            if wy + 5 > base - 2:
                continue
            for wx in range(bx + 4, bx + bw - 5, 7):
                cv.rect(wx, wy, 3, 5, "#3a2a3a"); cv.px(wx + 1, wy - 1, "#3a2a3a")
                if rng.random() < 0.3:
                    cv.rect(wx, wy, 3, 2, SUN[1]); cv.px(wx + 1, wy - 1, SUN[2])
    # 3. Old Main's clock tower
    if tower_x is not None:
        tw, th = 18, 44
        tx = tower_x - tw // 2
        ttop = base - th
        cv.rect(tx, ttop, tw, th, MACKY[5]); cv.vline(tx, ttop, th, MACKY[7]); cv.vline(tx + 1, ttop, th, MACKY[6])
        cv.vline(tx + tw - 1, ttop, th, MACKY[2]); cv.vline(tx + tw - 2, ttop, th, MACKY[3])
        for cy in range(ttop + 3, base, 4):
            cv.hline(tx + 2, cy, tw - 4, MACKY[4])
        cv.rect(tx - 2, ttop, tw + 4, 3, LIMESTONE[4]); cv.hline(tx - 2, ttop + 2, tw + 4, LIMESTONE[1])
        # belfry openings and the clock face
        for ox_ in (tx + 4, tx + tw - 7):
            cv.rect(ox_, ttop + 5, 3, 8, "#2a2030"); cv.px(ox_ + 1, ttop + 4, "#2a2030")
        cv.ellipse(tower_x - 4, ttop + 16, 9, 9, LIMESTONE[2]); cv.ellipse(tower_x - 3, ttop + 17, 7, 7, "#f2e6c8")
        cv.vline(tower_x, ttop + 18, 3, "#2a2030"); cv.hline(tower_x, ttop + 20, 2, "#2a2030")
        cv.poly([(tx - 3, ttop), (tower_x, ttop - 20), (tx + tw + 2, ttop)], MROOF[3])
        cv.poly([(tx - 3, ttop), (tower_x, ttop - 20), (tower_x, ttop)], MROOF[4])
        cv.line(tx - 3, ttop, tower_x, ttop - 20, MROOF[5])
        cv.vline(tower_x, ttop - 25, 5, IRON[2]); cv.px(tower_x, ttop - 26, SUN[1])
        for wx in (tx + 4, tx + tw - 7):
            cv.rect(wx, ttop + 28, 3, 6, "#3a2a3a"); cv.rect(wx, ttop + 28, 3, 2, SUN[1])
    # 4. blue spruces between the buildings
    for _ in range(int((x1 - x0) / 55)):
        sx = int(rng.integers(x0, x1))
        if gate and gate[0] - 4 < sx < gate[1] + 4:
            continue
        spruce(cv, sx, base - 2, int(rng.integers(26, 44)), seed=sx)
    # 5. autumn crowns along the front
    x = x0 - 10
    while x < x1 + 10:
        r = int(rng.integers(8, 15))
        hh = int(rng.integers(14, 24))
        pal = AUTUMN[int(rng.integers(len(AUTUMN)))]
        cx, cy = x, base - hh // 2 - 1
        cv.ellipse(cx - r, cy - hh // 2, r * 2, hh, pal[1])
        for _ in range(r * 3):
            a = rng.uniform(0, 2 * np.pi)
            d = np.sqrt(rng.uniform(0, 1))
            px_, py_ = int(cx + np.cos(a) * d * (r - 2)), int(cy + np.sin(a) * d * (hh / 2 - 2))
            lit = (px_ - cx) + (py_ - cy) * 0.6 < 2
            cv.rect(px_, py_, 2, 2, pal[3] if lit else pal[2])
            if lit and rng.random() < 0.45:
                cv.px(px_, py_, pal[4])
        x += int(rng.integers(12, 24))
    solid = cv.a[..., 3] > before
    return solid


def valley_haze(cv, x0, x1, y0, y1, colour="#c8a8b4", alpha=(0.12, 0.22, 0.32), seed=0, mask=None):
    """Morning haze lying in the valley at the mountains' feet: flat translucent bands with
    ragged tops, densest at the bottom (three steps, no gradient)."""
    rng = _rng(seed)
    n = len(alpha)
    for k in range(n):
        ya = y0 + (y1 - y0) * k // n
        m = np.zeros((cv.h, cv.w), bool)
        for x in range(x0, x1):
            top = ya + int(2 * np.sin(x / (17 + 5 * k) + k) + rng.integers(0, 2))
            m[max(0, top):y1, x] = True
        if mask is not None:
            m &= mask
        cv.fill_mask(m, C(colour, alpha[k] - (alpha[k - 1] if k else 0)))


# --- M07 props and floor pieces -------------------------------------------------------------------
STONE_SUN = ["#5a3a34", "#7a5248", "#9a6c58", "#b48468", "#c89a78", "#dcb48c", "#ecca9e"]   # sandstone in low sun
OAK_SUN = ["#3a2018", "#5a3424", "#7e4c30", "#a0663e", "#c0844e", "#dca262"]


def sunlit_tree(height=140, seed=0, tint=(1.0, 1.0, 1.0), flip=False, brightness=1.08):
    """An autumn oak (atlas cell 5) in the first sun: a touch brighter and warmer than the night
    trees, its sun side (left) rimmed with gold. Returns (Canvas, ax, ay)."""
    from midlib import sprite_from_cell
    spr = sprite_from_cell(5, height=height, colors=36, brightness=brightness, saturation=1.06)
    spr[..., :3] = np.clip(spr[..., :3] * np.array(tint), 0, 1)
    if flip:
        spr = spr[:, ::-1].copy()
    h, w = spr.shape[:2]
    m = spr[..., 3] > 0.5
    # rim light on the left edge of every leaf mass in the upper two thirds
    rim = m & ~np.roll(m, 1, axis=1)
    rim[int(h * 0.7):] = False
    lum = spr[..., :3] @ np.array([0.3, 0.55, 0.15])
    rim &= lum > 0.25
    spr[rim, :3] = np.clip(spr[rim, :3] * 1.18 + np.array([0.06, 0.04, 0.0]), 0, 1)
    cv = Canvas(w, h + 3, seed=seed)
    cv.paste(spr, 0, 0)
    return cv, w // 2, h


def dawn_bench(width=210, height=32, seed=0):
    """The long quad bench where the party sits at sunrise: sandstone pedestals, oak slats
    warm in the low light, and what they brought out of the night: a thermos of cocoa with three
    paper cups, a folded commencement programme, Pip's knit scarf over the back rail."""
    from lib_norlin import BRASS
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    seat = base - 13
    for sx in (ox + 12, ox + width // 2, ox + width - 13):
        cv.rect(sx - 1, base - height + 2, 3, height - 12, OUT); cv.vline(sx, base - height + 2, height - 13, IRON[3])
    for i, by in enumerate((base - height + 2, base - height + 8)):
        cv.rect(ox + 4, by, width - 8, 5, OUT)
        cv.rect(ox + 5, by + 1, width - 10, 3, OAK_SUN[4 if i == 0 else 3]); cv.hline(ox + 5, by + 1, width - 10, OAK_SUN[5])
        for gx in range(ox + 10, ox + width - 10, 13):
            cv.hline(gx, by + 2, 4, OAK_SUN[2])
    cv.rect(ox + width // 2 - 6, base - height + 3, 12, 3, BRASS[3]); cv.hline(ox + width // 2 - 5, base - height + 4, 10, BRASS[4])
    # the scarf over the back rail (CU gold and black stripes, a fringe hanging down)
    sx0 = ox + 40
    for k in range(14):
        c = CU_GOLD[3] if (k // 3) % 2 == 0 else CU_BLACK[2]
        cv.vline(sx0 + k, base - height + 1, 7 + (k % 3 == 0), c)
    cv.hline(sx0, base - height + 1, 14, CU_GOLD[4])
    for k in range(0, 14, 2):
        cv.vline(sx0 + k, base - height + 9, 2, CU_GOLD[2])
    cv.rect(sx0 - 1, base - height + 1, 1, 8, OUT); cv.rect(sx0 + 14, base - height + 1, 1, 8, OUT)
    # seat slats seen from above
    cv.rect(ox, seat - 6, width, 9, OUT)
    for k, sy in enumerate((seat - 5, seat - 3, seat - 1)):
        cv.rect(ox + 1, sy, width - 2, 2, OAK_SUN[4] if k != 1 else OAK_SUN[3]); cv.hline(ox + 1, sy, width - 2, OAK_SUN[5] if k == 0 else OAK_SUN[4])
    cv.rect(ox + 1, seat + 1, width - 2, 2, OAK_SUN[2]); cv.hline(ox + 1, seat + 2, width - 2, OAK_SUN[1])
    # dew still beaded on the far end of the seat
    for dx_ in range(ox + width - 34, ox + width - 6, 5):
        cv.px(dx_, seat - 4 + (dx_ // 5) % 3, DEW[1])
    for px_ in (ox + 4, ox + width // 2 - 6, ox + width - 16):
        cv.rect(px_, seat + 3, 12, base - seat - 3, OUT)
        cv.rect(px_ + 1, seat + 3, 10, base - seat - 4, STONE_SUN[4]); cv.vline(px_ + 1, seat + 3, base - seat - 4, STONE_SUN[6])
        cv.vline(px_ + 10, seat + 3, base - seat - 4, STONE_SUN[2]); cv.hline(px_ + 1, seat + 3, 10, STONE_SUN[2])
    # thermos and cups on the seat (left of centre), the programme on the right
    tx = ox + width // 2 - 30
    cv.rect(tx - 1, seat - 16, 8, 14, OUT)
    cv.rect(tx, seat - 15, 6, 12, "#a83c32"); cv.vline(tx, seat - 15, 12, "#d0584a"); cv.vline(tx + 5, seat - 15, 12, "#6a2226")
    cv.rect(tx, seat - 16, 6, 3, IRON[3]); cv.hline(tx, seat - 16, 6, IRON[4])
    cv.hline(tx, seat - 9, 6, CU_GOLD[3])
    for k, cx_ in enumerate((tx + 10, tx + 16, tx - 8)):
        cv.rect(cx_ - 1, seat - 9, 5, 6, OUT)
        cv.rect(cx_, seat - 8, 3, 5, "#f2ead6"); cv.vline(cx_ + 2, seat - 8, 5, "#c8bca4")
        cv.hline(cx_, seat - 8, 3, "#5a3424" if k < 2 else "#f2ead6")
    px_ = ox + width // 2 + 26
    cv.rect(px_ - 1, seat - 7, 18, 5, OUT)
    cv.rect(px_, seat - 6, 16, 3, "#ece2c8"); cv.hline(px_, seat - 6, 16, "#fff8e6")
    cv.rect(px_ + 1, seat - 5, 6, 1, CU_GOLD[2]); cv.hline(px_ + 9, seat - 5, 5, "#8a7e70")
    cv.vline(px_ + 8, seat - 6, 3, "#c8bca4")
    return cv, ox + width // 2, base


def dawn_lamp(height=68, glass=0.35):
    """A campus lamp post at sunrise, still lit and fading against the day: fluted iron post,
    square lantern (pale gold glass), a small sandstone footing. Lamp core ~5px below the top."""
    from lib_norlin import lantern_head
    w = 24
    cv = Canvas(w, height + 6, seed=3)
    cx, base = w // 2, height + 2
    top = base - height
    cv.rect(cx - 6, base - 6, 12, 6, OUT)
    cv.rect(cx - 5, base - 5, 10, 5, STONE_SUN[4]); cv.hline(cx - 5, base - 5, 10, STONE_SUN[6]); cv.vline(cx + 4, base - 5, 5, STONE_SUN[2])
    cv.rect(cx - 4, base - 10, 8, 5, IRON[1]); cv.hline(cx - 4, base - 10, 8, IRON[3])
    cv.rect(cx - 2, top + 18, 4, height - 28, OUT)
    cv.vline(cx - 1, top + 18, height - 28, IRON[3]); cv.vline(cx, top + 18, height - 28, IRON[2])
    cv.vline(cx - 2, top + 18, height - 28, mix(IRON[4], SUN[0], 0.4))        # sun on the left flank
    for ry in (top + 22, top + 40):
        cv.rect(cx - 3, ry, 6, 2, IRON[1]); cv.hline(cx - 3, ry, 6, IRON[4])
    cv.rect(cx - 4, top + 16, 8, 3, IRON[1]); cv.hline(cx - 4, top + 16, 8, IRON[4])
    g = (mix("#e9a84a", "#d8c8b0", 1 - glass), mix("#f6cf7a", "#ece0cc", 1 - glass), mix("#fff0c4", "#fff8ec", 1 - glass))
    lantern_head(cv, cx, top, glass=g)
    return cv, cx, base


def tree_shadow(m, x, y, length, angle_deg, crown_w, crown_h, seed=0, trunk=5, gap=0.35):
    """Mask of a long morning tree shadow on the ground: a trunk band from (x, y) running into a
    lumpy crown shadow stretched along the shadow direction (y squashed to the floor), with a
    few sun flecks through the leaves."""
    from PIL import Image, ImageDraw
    rng = _rng(seed)
    a = np.deg2rad(angle_deg)
    ux, uy = np.cos(a), np.sin(a) * 0.55
    img = Image.new("L", (m.shape[1], m.shape[0]), 0)
    d = ImageDraw.Draw(img)
    sx, sy = x + ux * length * gap, y + uy * length * gap
    d.line([(x, y), (sx + ux * 6, sy + uy * 6)], fill=255, width=trunk)
    mx_, my_ = x + ux * length * (gap + 1) / 2, y + uy * length * (gap + 1) / 2
    half = length * (1 - gap) / 2
    d.ellipse([mx_ - half * abs(ux) - crown_w * 0.28, my_ - crown_h * 0.42, mx_ + half * abs(ux) + crown_w * 0.28, my_ + crown_h * 0.42], fill=255)
    for k in range(12):        # leafy lumps around the edge
        ang = k / 12 * 2 * np.pi + rng.uniform(-0.2, 0.2)
        ex = mx_ + np.cos(ang) * (half * abs(ux) + crown_w * 0.24)
        ey = my_ + np.sin(ang) * crown_h * 0.38
        r = crown_w * rng.uniform(0.07, 0.12)
        d.ellipse([ex - r, ey - r * 0.6, ex + r, ey + r * 0.6], fill=255)
    for _ in range(5):      # sun flecks through the leaves
        t = rng.uniform(gap + 0.2, 0.9)
        cx_, cy_ = x + ux * length * t + rng.normal(0, crown_w * 0.1), y + uy * length * t + rng.normal(0, crown_h * 0.08)
        d.rectangle([cx_ - 2, cy_ - 1, cx_ + 2, cy_], fill=0)
    m |= np.array(img) > 0
    return m


def footprints(cv, pts, colour, step=9, alpha=0.5):
    """A trail of small footprints pressed into the dew along a polyline (darker grass)."""
    k = 0
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        L = max(1, int(np.hypot(x1 - x0, y1 - y0)))
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        for s in range(0, L, step):
            t = s / L
            side = 1 if k % 2 else -1
            px_ = int(round(x0 + (x1 - x0) * t + nx * 2 * side))
            py_ = int(round(y0 + (y1 - y0) * t + ny * 1 * side))
            cv.rect(px_, py_, 3, 1, C(colour, alpha)); cv.px(px_ + 1, py_ + 1, C(colour, alpha))
            k += 1


def sun_medallion(cv, cx, cy, r=36, pal=None, field=None, sy=0.4):
    """A flat brass-and-sandstone sun set into the plaza paving: rings, sixteen rays, a disc."""
    pal = pal or ["#5a3a24", "#8a6030", "#b88a40", "#dcb058", "#f4d68a"]
    field = field or STONE_SUN
    def ell(rx, c):
        cv.ellipse(cx - rx, int(cy - rx * sy), rx * 2 + 1, int(rx * 2 * sy) + 1, c)
    ell(r + 2, field[1]); ell(r, pal[2]); ell(r - 2, field[4]); ell(r - 3, field[3])
    for k in range(16):
        a = k / 16 * 2 * np.pi
        ln = r - 5 if k % 2 == 0 else r - 11
        x1, y1 = cx + np.cos(a) * ln, cy + np.sin(a) * ln * sy
        x2, y2 = cx + np.cos(a) * (r * 0.36), cy + np.sin(a) * (r * 0.36) * sy
        cv.line(int(round(x1)), int(round(y1)), int(round(x2)), int(round(y2)), pal[3] if k % 2 == 0 else pal[2])
    ell(int(r * 0.34), pal[1]); ell(int(r * 0.34) - 1, pal[3]); ell(int(r * 0.2), pal[4])
    cv.hline(cx - int(r * 0.2) + 1, int(cy - r * 0.34 * sy) + 1, int(r * 0.4) - 1, pal[4])


FAR_RANGE = ["#7c7094", "#8e7ea0", "#a28ca8", "#b89aac", "#cca8b0", "#dcb8b8"]


def _peaks(tops, win=24):
    """Local maxima of a skyline (smallest y) at least win apart: [(i, y)]."""
    out = []
    n = len(tops)
    for i in range(n):
        lo, hi = max(0, i - win), min(n, i + win + 1)
        if tops[i] <= min(tops[lo:hi]) and (not out or i - out[-1][0] >= win):
            out.append((i, tops[i]))
    return out


def far_range(cv, x0, tops, base, seed=0, pal=FAR_RANGE, facets=True, depth_steps=(18, 30)):
    """A distant range in morning haze: a pale rose-lavender silhouette, a sunlit facet hanging
    from each summit (the south-east faces the low sun reaches), a gully beside it, a lit crest,
    paler toward the valley haze (stepped)."""
    from PIL import Image, ImageDraw
    rng = _rng(seed)
    tops = np.asarray(tops, float)
    n = len(tops)
    sil = np.zeros((cv.h, cv.w), bool)
    for i in range(n):
        sil[int(round(tops[i])):base, x0 + i] = True
    img = Image.new("L", (cv.w, cv.h), 0)
    d = ImageDraw.Draw(img)
    gul = Image.new("L", (cv.w, cv.h), 0)
    dg = ImageDraw.Draw(gul)
    if facets:
        for (i, y) in _peaks(list(tops), 20):
            px_ = x0 + i
            hgt = rng.uniform(16, 30)
            wl, wr = rng.uniform(14, 26), rng.uniform(3, 8)
            d.polygon([(px_, y), (px_ - wl, y + hgt), (px_ + wr, y + hgt * 0.9)], fill=255)
            dg.line([(px_ + 1, y + 2), (px_ + wr + 3, y + hgt)], fill=255, width=2)
            for k in range(int(rng.integers(1, 3))):          # a secondary rib further down-left
                sx = px_ - wl * rng.uniform(0.5, 1.2)
                sy = y + hgt * rng.uniform(0.3, 0.6)
                d.polygon([(sx, sy), (sx - wl * 0.6, sy + hgt * 0.6), (sx + 3, sy + hgt * 0.55)], fill=255)
    lit = (np.array(img) > 0) & sil
    gully = (np.array(gul) > 0) & sil & ~lit
    ys = np.arange(cv.h)[:, None]
    top_row = np.full(cv.w, cv.h)
    top_row[x0:x0 + n] = np.round(tops).astype(int)
    depth = ys - top_row[None, :]
    k = np.where(lit, 2, np.where(gully, 0, 1))
    k = np.where(depth > depth_steps[0], np.maximum(k, 2) + 1, k)
    k = np.where(depth > depth_steps[1], np.maximum(k, 4), k)
    k = np.clip(k, 0, len(pal) - 1)
    P = np.array([C(c) for c in pal], np.float32)
    cv.a[sil] = P[k[sil]]
    for i in range(n):
        cv.px(x0 + i, int(round(tops[i])), pal[4] if pal is FAR_RANGE else pal[3])


FOREST_RIDGE = ["#262c3a", "#2e3642", "#384048", "#464c50", "#565a56", "#6a6a5a", "#827a60"]


def forest_ridge(cv, x0, tops, base, seed=0, outcrops=()):
    """A nearer forested ridge in the same colours as the repainted title Flatirons: blue pine
    shadow, lit facets on the south-east of each summit, pine stipple, a crest touched by the
    first sun, and a few small sandstone outcrops glowing (outcrops: [(x, y, w, h)])."""
    from PIL import Image, ImageDraw
    rng = _rng(seed)
    far_range(cv, x0, tops, base, seed=seed, pal=FOREST_RIDGE[:5] + [FOREST_RIDGE[2]], depth_steps=(60, 90))
    n = len(tops)
    for _ in range(n * 3):
        i = int(rng.integers(0, n))
        top = int(round(tops[i]))
        y = top + 2 + int(abs(rng.normal(0, 18)))
        if y >= base - 1:
            continue
        x = x0 + i
        c = cv.a[y, x, :3] @ np.array([0.3, 0.55, 0.15])
        cv.px(x, y, FOREST_RIDGE[5] if c > 0.27 else FOREST_RIDGE[3])
        cv.px(x, y + 1, FOREST_RIDGE[0])
    for i in range(n):
        top = int(round(tops[i]))
        cv.px(x0 + i, top, ALP_SUN[4] if (i // 2) % 3 else ALP_SUN[6])
        if rng.random() < 0.35:
            cv.px(x0 + i, top + 1, ALP_SUN[2])
    for (ox, oy, ow, oh) in outcrops:
        img = Image.new("L", (cv.w, cv.h), 0)
        ImageDraw.Draw(img).polygon([(ox, oy), (ox - ow * 0.3, oy + oh), (ox + ow * 0.7, oy + oh)], fill=255)
        m = np.array(img) > 0
        cv.fill_mask(m, ALP_SUN[3])
        img = Image.new("L", (cv.w, cv.h), 0)
        ImageDraw.Draw(img).polygon([(ox, oy + 1), (ox + 1, oy + 2), (ox + ow * 0.6, oy + oh), (ox + ow * 0.1, oy + oh)], fill=255)
        cv.fill_mask(np.array(img) > 0, ALP_SUN[5])
        cv.px(ox, oy, ALP_SUN[7])


MORNING_CLOUD = ["#8a82a8", "#a294b6", "#bca4bc", "#d4b0b6", "#e6bfb4", "#f2d0bc", "#fae2cc"]


def morning_cloud(length, thick, rng, pal=MORNING_CLOUD):
    """A small cumulus heap front-lit by the low sun behind the viewer: lit peach face, lavender
    underside, a bright rim along the top of each heap."""
    w, h = length + 8, thick * 3 + 8
    cv = Canvas(w, h)
    floor_ = h - 3
    lumps = [(4, floor_ - thick, length, thick + 1)]
    x = 6
    while x < length - 8:
        lw = int(rng.integers(12, 26)); lh = int(rng.integers(thick, thick * 2 + 3))
        lumps.append((x, floor_ - lh, lw, lh + 1))
        x += int(rng.integers(7, 15))
    for (lx, ly, lw, lh) in lumps:
        cv.ellipse(lx - 1, ly - 1, lw + 2, (lh + 1) * 2, pal[1])
    for (lx, ly, lw, lh) in lumps:
        cv.ellipse(lx, ly, lw, lh * 2, pal[3])
        cv.ellipse(lx + 1, ly, lw - 3, lh * 2 - 3, pal[4])
        cv.ellipse(lx + 2, ly + 1, lw // 2, lh, pal[5])
    for (lx, ly, lw, lh) in lumps:       # rims on top of each heap
        for xx in range(lx + 2, min(w, lx + lw - 2)):
            col = np.where(cv.a[:, xx, 3] > 0)[0]
            if len(col):
                cv.px(xx, col.min(), pal[6] if rng.random() < 0.7 else pal[5])
    cv.a[floor_ - 1:] = 0
    m = cv.a[..., 3] > 0
    for xx in range(w):
        col = np.where(m[:, xx])[0]
        if len(col):
            b = col.max()
            cv.px(xx, b, pal[0]); cv.px(xx, b - 1, pal[1]); cv.px(xx, b - 2, pal[2])
    return cv.a


def cloud_bank(width=960, height=36, count=5, seed=1, sizes=(50, 120), thick=(4, 7), pal=MORNING_CLOUD):
    """Morning cumulus on a horizontally tileable transparent strip (for drift layers)."""
    rng = _rng(seed)
    cv = Canvas(width, height)
    step = max(1, width // count)
    for i in range(count):
        cx = i * step + int(rng.integers(0, max(1, step - 40)))
        cl = morning_cloud(int(rng.integers(*sizes)), int(rng.integers(*thick)), rng, pal)
        ch = cl.shape[0]
        cy = int(rng.integers(0, max(1, height - ch)))
        for dx in (-width, 0, width):
            cv.paste(cl, cx + dx, cy)
    return cv


def cirrus(cv, x, y, length, rng, pal=("#e8c4c4", "#f6dccc", "#d4b0c0")):
    """A thin high streak of cirrus caught pink by the sun (flat, a few pixels tall)."""
    for k in range(3):
        ox = int(rng.integers(-10, 20)) + k * int(length * 0.2)
        ln = int(length * rng.uniform(0.4, 0.8))
        cv.hline(x + ox, y + k, ln, C(pal[k % 3], 0.75))
        cv.hline(x + ox + 4, y + k - 1, ln // 3, C(pal[1], 0.55))


def lenticular(cv, cx, cy, length, thick, pal=("#9a8cb0", "#c4a8bc", "#e8bcb4", "#f8d4bc", "#fde6cc"), layers=2, seed=0):
    """A Front Range wave cloud: smooth stacked lenses lying over the mountains, lit rose-gold on
    their undersides by the low sun, cooler on top (flat tones, crisp edges)."""
    rng = _rng(seed)
    for k in range(layers):
        L = int(length * (1 - 0.22 * k))
        T = max(2, thick - k)
        x0 = cx - L // 2 + int(rng.integers(-6, 7))
        y0 = cy - k * (T + 1)
        for i in range(L):
            t = i / max(1, L - 1)
            h = int(round(T * np.sin(np.pi * t) ** 0.7))
            if h <= 0:
                continue
            cv.vline(x0 + i, y0 - h, h, pal[1])
            cv.px(x0 + i, y0 - h, pal[0] if k else pal[1])
            cv.vline(x0 + i, y0 - max(1, h // 2), max(1, h // 2), pal[2])
            cv.px(x0 + i, y0 - 1, pal[3])
            if 0.15 < t < 0.85:
                cv.px(x0 + i, y0, pal[4] if (i // 3) % 4 else pal[3])


# --- backlighting (the M07 battle looks into the sunrise) ------------------------------------------
def backlit(spr, body=(0.5, 0.46, 0.58), rim="#ffd890", rim2="#f6b46a", haze=None, haze_amt=0.0, sun_dx=0.0, glow_windows=None,
            fringe=0.0, lift=(0.04, 0.04, 0.04)):
    """Grade a painted RGBA sprite as seen against the rising sun: the body falls into cool
    shadow (multiplied toward violet), every edge facing the sky gets a crisp gold rim (two
    pixels on top edges, one on the sides), optional haze toward a colour with distance."""
    out = spr.copy()
    m = out[..., 3] > 0.5
    lum = out[..., :3] @ np.array([0.3, 0.55, 0.15])
    out[..., :3] = out[..., :3] * np.array(body)[None, None, :] + np.array(lift)[None, None, :]
    if fringe > 0:
        # translucent edges (leaves) glow where the light comes through
        from scipy import ndimage
        inner = ndimage.binary_erosion(m, iterations=2)
        edge = m & ~inner
        out[edge, :3] = out[edge, :3] * (1 - fringe) + np.array(C(rim2)[:3]) * fringe
    if glow_windows is not None:
        g = glow_windows(out, lum, m)
        out[g, :3] = np.array(C("#f6c46a")[:3])
    up = m & ~np.roll(m, 1, axis=0)
    up2 = m & ~np.roll(m, 2, axis=0) & ~up
    side = m & (~np.roll(m, 1, axis=1) | ~np.roll(m, -1, axis=1)) & ~up
    out[up, :3] = np.array(C(rim)[:3])
    out[up2, :3] = out[up2, :3] * 0.4 + np.array(C(rim2)[:3]) * 0.6
    out[side, :3] = out[side, :3] * 0.5 + np.array(C(rim2)[:3]) * 0.5
    if haze is not None and haze_amt > 0:
        out[m, :3] = out[m, :3] * (1 - haze_amt) + np.array(C(haze)[:3]) * haze_amt
    return out


SUNRISE = ["#6a7cb0", "#7a86b8", "#9290bc", "#ac9ab8", "#c8a4b0", "#e2b0a6", "#f2c09c", "#f8d0a0", "#fde0ac", "#fff0c8"]
GOLD_CLOUD = ["#7a6a8e", "#9a7c96", "#c08c94", "#e0a08c", "#f4bc8c", "#fcd8a4", "#fff0cc"]


# ============================================================================================
# the house: walls, boxes, proscenium, curtain, upstage set (M06 and the M05/M06 battles)
# ============================================================================================
HOUSE_DAWN = ["#3a2a2c", "#4c3634", "#60443e", "#745448", "#886454", "#9c7662", "#b08a72", "#c8a084"]   # house lights up
VELVET = ["#1a0a10", "#2e0e16", "#4a1620", "#66202a", "#842c34", "#a43c40", "#c05a54"]
CYC_NIGHT = ["#0e1024", "#141632", "#1a1c3e", "#22244a", "#2a2c56"]
CYC_DAWN = ["#4a4450", "#5a525c", "#6a6068", "#7a6e74", "#8a7c80"]
CHAIR = ["#1e1210", "#2e1c16", "#4a2e22", "#62402c", "#7a5236", "#946844", "#b08458"]   # ceremony chairs (oak)


def sconce_m(cv, cx, y, lit=1.0):
    """A two-branch brass wall sconce with small parchment shades (house lighting)."""
    cv.rect(cx - 1, y, 3, 9, GILT[1]); cv.px(cx, y - 1, GILT[3])
    cv.ellipse(cx - 2, y + 7, 5, 4, GILT[2])
    for dx in (-6, 6):
        cv.line(cx, y + 6, cx + dx, y + 3, GILT[2])
        sh = mix("#e8c890", "#7a6a5a", 1 - lit)
        cv.poly([(cx + dx - 3, y + 3), (cx + dx - 2, y - 2), (cx + dx + 2, y - 2), (cx + dx + 3, y + 3)], sh)
        cv.hline(cx + dx - 2, y - 2, 5, mix("#fff0c8", "#8a7a6a", 1 - lit))
    if lit > 0:
        halo(cv, cx, y + 1, 16, "#f6cf7a", 0.14 * lit)


def house_window(cv, x, y, w, h, dawn=False, seed=0):
    """A tall round-headed house window: deep sandstone reveal, leaded panes; night blue or, at
    dawn, glowing with the sunrise outside."""
    cv.rect(x - 4, y - w // 2 - 2, w + 8, h + w // 2 + 6, HOUSE[1] if not dawn else HOUSE_DAWN[2])
    cv.ellipse(x - 4, y - w // 2 - 4, w + 8, w + 8, HOUSE[1] if not dawn else HOUSE_DAWN[2])
    glass = ["#141a34", "#1c2444", "#28305a"] if not dawn else ["#e8a868", "#f6c88a", "#fde6b8"]
    cv.ellipse(x, y - w // 2, w, w, glass[1])
    cv.rect(x, y, w, h, glass[1])
    for yy in range(y + 2, y + h, 3):
        cv.hline(x, yy, w, glass[0] if not dawn else glass[0])
    for k in range(1, 3):
        cv.vline(x + k * w // 3, y - w // 2 + 2, h + w // 2 - 2, "#1a1218")
    cv.hline(x, y + h // 2, w, "#1a1218")
    if dawn:
        cv.rect(x + 1, y + 1, w // 3 - 1, h - 2, glass[2])
    else:
        cv.px(x + w - 3, y + 4, "#c8d0f0")
    cv.rect(x - 5, y + h, w + 10, 3, LIMESTONE[3] if dawn else LIMESTONE[1]); cv.hline(x - 5, y + h, w + 10, LIMESTONE[4] if dawn else LIMESTONE[2])


def opera_box(cv, x, y, w, h, dawn=False, cards=True, seed=0):
    """A side box above the house floor: velvet drapes looped up with gold tassels, the dark box
    with three chair backs, a gilt balustraded parapet. Returns card points (for twinkles)."""
    pal = HOUSE_DAWN if dawn else HOUSE
    cv.rect(x, y, w, h, pal[0])
    pts = []
    # chair backs inside
    for k in range(3):
        cx = x + 8 + k * (w - 16) // 2
        cv.rect(cx - 4, y + h - 22, 9, 10, SEAT[3] if not dawn else SEAT[4]); cv.hline(cx - 4, y + h - 22, 9, SEAT[5])
        if cards:
            cv.rect(cx - 2, y + h - 19, 5, 3, CARD[3]); cv.hline(cx - 2, y + h - 17, 5, CARD[1])
            pts.append((cx, y + h - 18))
    # drapes and pelmet
    cv.rect(x - 2, y - 4, w + 4, 6, VELVET[3]); cv.hline(x - 2, y - 4, w + 4, VELVET[5])
    for sx in range(x - 2, x + w + 2, 6):
        cv.poly([(sx, y + 2), (sx + 3, y + 5), (sx + 6, y + 2)], VELVET[3])
    for side in (0, 1):
        dx = x if side == 0 else x + w - 9
        cv.poly([(dx, y), (dx + 9, y), (dx + (5 if side == 0 else 4), y + h - 18), (dx + (0 if side == 0 else 9), y + h - 12)], VELVET[2])
        cv.line(dx + (2 if side == 0 else 6), y + 1, dx + (2 if side == 0 else 6), y + h - 16, VELVET[4])
        tx = dx + (6 if side == 0 else 3)
        cv.rect(tx - 1, y + h - 20, 3, 5, GILT[3]); cv.px(tx, y + h - 15, GILT[4])
    # parapet with balusters
    py = y + h - 12
    cv.rect(x - 4, py, w + 8, 14, OUT)
    cv.rect(x - 3, py + 1, w + 6, 3, GILT[3]); cv.hline(x - 3, py + 1, w + 6, GILT[4])
    for bx in range(x - 1, x + w + 2, 5):
        cv.rect(bx, py + 4, 3, 7, pal[4]); cv.vline(bx, py + 4, 7, pal[6]); cv.px(bx + 1, py + 6, pal[2])
    cv.rect(x - 3, py + 11, w + 6, 3, GILT[2]); cv.hline(x - 3, py + 11, w + 6, GILT[3])
    cv.rect(x + w // 2 - 6, py + 4, 13, 7, GILT[2]); cv.rect(x + w // 2 - 4, py + 5, 9, 5, GILT[4])    # cartouche
    return pts


def house_wall(cv, x0, x1, top, base, dawn=False, seed=0, box=None, window=None, sconces=(), cards=True):
    """A side wall of Macky's house: warm plaster between fluted pilasters, a dark oak dado,
    a cornice; optionally an opera box, a tall window and brass sconces. Returns card points."""
    pal = HOUSE_DAWN if dawn else HOUSE
    rng = _rng(seed)
    cv.rect(x0, top, x1 - x0, base - top, pal[3])
    for yy in range(top, base, 2):           # faint plaster texture in two tones
        for xx in range(x0 + (yy // 2) % 3, x1, 7):
            if rng.random() < 0.18:
                cv.px(xx, yy, pal[2] if rng.random() < 0.6 else pal[4])
    # cornice
    cv.rect(x0, top, x1 - x0, 8, pal[1]); cv.hline(x0, top + 6, x1 - x0, GILT[2]); cv.hline(x0, top + 7, x1 - x0, pal[5])
    for xx in range(x0 + 2, x1, 6):
        cv.rect(xx, top + 2, 3, 3, pal[5])
    # pilasters
    for px_ in range(x0 + 6, x1 - 10, 58):
        cv.rect(px_, top + 8, 12, base - top - 38, pal[4]); cv.vline(px_, top + 8, base - top - 38, pal[6])
        cv.vline(px_ + 11, top + 8, base - top - 38, pal[2])
        for fx in (px_ + 3, px_ + 6, px_ + 9):
            cv.vline(fx, top + 12, base - top - 46, pal[3])
        cv.rect(px_ - 2, top + 8, 16, 4, pal[5]); cv.hline(px_ - 2, top + 8, 16, GILT[3])
    # dado
    dy = base - 30
    cv.rect(x0, dy, x1 - x0, 30, OAK_SUN[1] if dawn else OAKF[2])
    cv.hline(x0, dy, x1 - x0, GILT[2] if not dawn else GILT[3]); cv.hline(x0, dy + 1, x1 - x0, OAKF[4])
    for px_ in range(x0 + 4, x1 - 20, 30):
        cv.rect(px_, dy + 5, 24, 20, OAKF[1] if not dawn else OAK_SUN[0]); cv.rect(px_ + 1, dy + 6, 22, 18, OAKF[3] if not dawn else OAK_SUN[2])
        cv.hline(px_ + 1, dy + 6, 22, OAKF[4] if not dawn else OAK_SUN[3])
    cv.hline(x0, base - 1, x1 - x0, OUT)
    pts = []
    if window:
        house_window(cv, *window, dawn=dawn)
    if box:
        pts += opera_box(cv, *box, dawn=dawn, cards=cards)
    for (sx, sy) in sconces:
        sconce_m(cv, sx, sy, lit=1.0 if dawn else 0.6)
    return pts


def proscenium(cv, x0, x1, top, base, dawn=False):
    """Macky's proscenium: gilt-framed pilasters and a deep arch header with a lyre cartouche, the
    house curtain of red velvet gathered up in a swagged valance and tied back at the sides."""
    w = x1 - x0
    pal = HOUSE_DAWN if dawn else HOUSE
    # header
    cv.rect(x0, top, w, 24, pal[2])
    cv.rect(x0, top + 2, w, 3, GILT[3]); cv.hline(x0, top + 2, w, GILT[4])
    cv.rect(x0, top + 19, w, 3, GILT[2]); cv.hline(x0, top + 19, w, GILT[4])
    for xx in range(x0 + 6, x1 - 6, 12):
        cv.rect(xx, top + 8, 6, 8, pal[4]); cv.hline(xx, top + 8, 6, pal[6]); cv.px(xx + 2, top + 11, GILT[3])
    cx = (x0 + x1) // 2
    cv.ellipse(cx - 18, top - 2, 37, 26, OUT); cv.ellipse(cx - 17, top - 1, 35, 24, GILT[2]); cv.ellipse(cx - 14, top + 1, 29, 20, pal[1])
    # lyre in the cartouche
    cv.line(cx - 6, top + 4, cx - 4, top + 17, GILT[4]); cv.line(cx + 6, top + 4, cx + 4, top + 17, GILT[4])
    cv.hline(cx - 4, top + 17, 9, GILT[3]); cv.hline(cx - 5, top + 6, 11, GILT[3])
    for sx in (cx - 2, cx, cx + 2):
        cv.vline(sx, top + 7, 10, GILT[1])
    # pilasters
    for (px_, side) in ((x0, 0), (x1 - 20, 1)):
        cv.rect(px_, top + 22, 20, base - top - 22, pal[2])
        cv.rect(px_ + 2, top + 22, 16, base - top - 22, GILT[2]); cv.rect(px_ + 4, top + 22, 12, base - top - 22, pal[3])
        cv.vline(px_ + 2, top + 22, base - top - 22, GILT[4]); cv.vline(px_ + 17, top + 22, base - top - 22, GILT[1])
        for ry in range(top + 34, base - 10, 22):
            cv.ellipse(px_ + 6, ry, 8, 8, GILT[3]); cv.px(px_ + 9, ry + 3, GILT[4]); cv.px(px_ + 10, ry + 4, GILT[1])
    # house curtain: valance swags and gathered legs
    vx0, vx1 = x0 + 20, x1 - 20
    vy = top + 22
    cv.rect(vx0, vy, vx1 - vx0, 7, VELVET[3]); cv.hline(vx0, vy, vx1 - vx0, VELVET[2])
    nsw = max(3, (vx1 - vx0) // 64)
    sw = (vx1 - vx0) / nsw
    for k in range(nsw):
        a = vx0 + int(k * sw)
        b = vx0 + int((k + 1) * sw)
        for xx in range(a, b):
            t = (xx - a) / max(1, b - a)
            d = int(10 * np.sin(np.pi * t))
            cv.vline(xx, vy + 6, d + 2, VELVET[3])
            cv.px(xx, vy + 7 + d, VELVET[5]); cv.px(xx, vy + 8 + d, VELVET[1])
            if d > 4:
                cv.px(xx, vy + 4 + d // 2, VELVET[4])
        cv.rect(a - 1, vy + 4, 3, 10, GILT[3]); cv.px(a, vy + 14, GILT[4]); cv.px(a, vy + 15, GILT[2])
    for (lx, side) in ((vx0, 0), (vx1 - 26, 1)):
        for xx in range(lx, lx + 26):
            t = (xx - lx) / 25
            fold = int(xx * 1.0) % 5
            c = VELVET[[2, 3, 4, 3, 2][fold]]
            cv.vline(xx, vy + 7, base - vy - 7, c)
        # tie-back gathering: the leg pulled in at the waist
        ty = vy + (base - vy) * 3 // 5
        cv.rect(lx + (0 if side == 0 else 14), ty, 12, 3, GILT[3]); cv.hline(lx + (0 if side == 0 else 14), ty, 12, GILT[4])
        cv.rect(lx + (4 if side == 0 else 18), ty + 3, 3, 7, GILT[2]); cv.px(lx + (5 if side == 0 else 19), ty + 10, GILT[4])
        cv.vline(lx + (25 if side == 0 else 0), vy + 7, base - vy - 7, VELVET[1])
    return (vx0 + 26, vy + 7, vx1 - 26, base)          # the stage opening inside the curtain legs


def ceremony_chair(cv, cx, base, w=12, h=18, card=True, facing="front", pal=CHAIR, glow=False):
    """A wooden ceremony chair. facing 'front' (from the audience: back rail, slats, seat front,
    legs) or 'back' (from behind: the back panel). A RESERVED card propped on the seat/hung on
    the back. Returns the card centre or None."""
    x = cx - w // 2
    sb = base - h // 2 - 1                 # seat line
    if facing == "front":
        cv.rect(x + 1, base - h, 2, h, OUT); cv.rect(x + w - 3, base - h, 2, h, OUT)
        cv.rect(x, base - h - 1, w, 3, OUT); cv.hline(x + 1, base - h, w - 2, pal[5])
        for sx in range(x + 3, x + w - 3, 3):
            cv.vline(sx, base - h + 2, sb - (base - h + 2), pal[3])
        cv.rect(x - 1, sb, w + 2, 3, OUT); cv.hline(x, sb, w, pal[5]); cv.hline(x, sb + 1, w, pal[3])
        cv.vline(x + 1, sb + 3, base - sb - 3, pal[2]); cv.vline(x + w - 2, sb + 3, base - sb - 3, pal[1])
        if card:
            cv.rect(cx - 3, sb - 5, 7, 5, OUT); cv.rect(cx - 2, sb - 4, 5, 3, CARD[3] if not glow else "#fffaf0")
            cv.px(cx, sb - 3, CARD_RED)
            return (cx, sb - 3)
    else:
        cv.rect(x, base - h - 1, w, h // 2 + 3, OUT)
        cv.rect(x + 1, base - h, w - 2, h // 2 + 1, pal[3]); cv.hline(x + 1, base - h, w - 2, pal[5])
        cv.vline(x + 1, base - h, h // 2 + 1, pal[4])
        cv.rect(x + 1, sb + 2, 2, base - sb - 2, OUT); cv.rect(x + w - 3, sb + 2, 2, base - sb - 2, OUT)
        if card:
            cy = base - h + 3
            cv.rect(cx - 4, cy - 1, 9, 6, OUT); cv.rect(cx - 3, cy, 7, 4, CARD[3]); cv.hline(cx - 3, cy, 7, CARD[2] if not glow else "#fffaf0")
            cv.hline(cx - 2, cy + 2, 5, CARD_RED)
            return (cx, cy + 1)
    return None


def val_frame(cv, cx, top, w, h, dawn=False, seed=0):
    """The set's centrepiece, VAL's emblem at giant scale: a teal frame with brass finials and
    beading. At night its glass holds rows of mortarboards fading into the dark (everyone you
    could be); at dawn it is only a frame around plain wall."""
    rng = _rng(seed)
    x = cx - w // 2
    cv.rect(x - 1, top - 1, w + 2, h + 2, OUT)
    cv.rect(x, top, w, h, VAL_TEAL[3]); cv.rect(x + 2, top + 2, w - 4, h - 4, VAL_TEAL[4])
    cv.rect(x + 5, top + 5, w - 10, h - 10, VAL_TEAL[2])
    for bx in range(x + 3, x + w - 3, 4):            # brass beading
        cv.px(bx, top + 3, GILT[3]); cv.px(bx, top + h - 4, GILT[2])
    for by in range(top + 3, top + h - 3, 4):
        cv.px(x + 3, by, GILT[3]); cv.px(x + w - 4, by, GILT[2])
    ix, iy, iw, ih = x + 7, top + 7, w - 14, h - 14
    if not dawn:
        cv.rect(ix, iy, iw, ih, VAL_TEAL[1])
        cv.rect(ix, iy, iw, ih // 3, VAL_TEAL[0])
        # rows of mortarboards receding into the glass: bright in front, teal toward the back
        rows = 7
        for row in range(rows):
            yy = iy + ih - 7 - row * 8
            if yy < iy + 3:
                break
            f = row / (rows - 1)
            top_c = mix("#f2e2a8", VAL_TEAL[3], min(1.0, f * 1.1))
            side_c = mix("#a8905a", VAL_TEAL[2], min(1.0, f * 1.1))
            for xx in range(ix + 4 + (row % 2) * 5, ix + iw - 9, 10):
                cv.hline(xx + 1, yy, 7, top_c); cv.hline(xx, yy + 1, 9, top_c); cv.hline(xx + 1, yy + 2, 7, side_c)
                cv.rect(xx + 3, yy + 3, 3, 2, side_c)
                if row < 3:
                    cv.vline(xx + 8, yy + 1, 3 - row // 2, GILT[4] if row == 0 else GILT[3])
        cv.hline(ix, iy, iw, VAL_TEAL[5])
    else:
        cv.rect(ix, iy, iw, ih, CYC_DAWN[2])
        cv.rect(ix, iy, iw, 3, CYC_DAWN[1])
    for (fx, fy) in ((x - 3, top - 5), (x + w - 4, top - 5), (cx - 3, top - 8)):
        cv.ellipse(fx, fy, 7, 7, OUT); cv.ellipse(fx + 1, fy + 1, 5, 5, GILT[3]); cv.px(fx + 2, fy + 2, GILT[5])
    for (fx, fy) in ((x - 3, top + h - 2), (x + w - 4, top + h - 2)):
        cv.ellipse(fx, fy, 7, 6, OUT); cv.ellipse(fx + 1, fy + 1, 5, 4, GILT[2])


def flown_chair(cv, x, y, rope_top, sway=0, pal=CHAIR, lit=VAL_TEAL[5]):
    """A small wooden chair hanging from a fly line (the set's 'futures waiting to be sat in')."""
    cv.vline(x, rope_top, y - rope_top, "#6a5a4a")
    cv.px(x, y - 1, "#8a7a6a")
    sx = x + sway
    cv.rect(sx - 4, y, 9, 2, OUT); cv.hline(sx - 3, y, 7, pal[5])
    cv.rect(sx - 4, y + 2, 2, 10, OUT); cv.rect(sx + 3, y + 2, 2, 10, OUT)
    cv.vline(sx - 3, y + 2, 9, pal[3]); cv.vline(sx + 4, y + 2, 9, pal[2])
    cv.rect(sx - 5, y + 6, 11, 2, OUT); cv.hline(sx - 4, y + 6, 9, pal[4])
    cv.px(sx - 3, y + 1, lit)


def big_text(cv, s, x, y, colour, scale=2, shadow=None):
    """Lettering at 2x (each font pixel a 2x2 block) for big banners."""
    tmp = Canvas(text_width(s) + 2, 12)
    text(tmp, s, 0, 0, colour)
    a = tmp.a
    big = np.repeat(np.repeat(a, scale, 0), scale, 1)
    if shadow is not None:
        sh = big.copy()
        sh[..., :3] = np.array(C(shadow)[:3])
        cv.paste(sh, x + scale // 2 + 1, y + scale // 2 + 1)
    cv.paste(big, x, y)
    return big.shape[1], big.shape[0]


def grad_banner(cv, cx, y, label="EVERYONE YOU COULD BE", width=None):
    """The graduation banner: CU black cloth with a gold border and fringe, big gold lettering,
    hung on two cords from the batten above."""
    tw = text_width(label) * 2
    w = width or tw + 28
    x = cx - w // 2
    h = 26
    for ax in (x + 6, x + w - 7):
        cv.vline(ax, y - 14, 14, "#6a5a4a")
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, CU_BLACK[1]); cv.rect(x + 2, y + 2, w - 4, h - 4, CU_BLACK[2])
    cv.hline(x + 2, y + 2, w - 4, CU_GOLD[3]); cv.hline(x + 2, y + h - 3, w - 4, CU_GOLD[2])
    cv.vline(x + 2, y + 2, h - 4, CU_GOLD[3]); cv.vline(x + w - 3, y + 2, h - 4, CU_GOLD[2])
    for fx in range(x, x + w, 2):
        cv.vline(fx, y + h + 1, 2 + (fx // 2) % 2, CU_GOLD[2] if (fx // 2) % 2 else CU_GOLD[3])
    big_text(cv, label, cx - tw // 2, y + 7, CU_GOLD[4], shadow="#0a0810")
    return (x, y, w, h)


def ended_sign(label1="ONE GATHERING", label2="ENDED"):
    """The overlay hung over the banner at dawn: a plain cream card on the batten, hand-lettered:
    ONE GATHERING / ENDED. Returns a Canvas."""
    w = max(text_width(label1), text_width(label2)) * 2 + 30
    h = 44
    cv = Canvas(w + 2, h + 18)
    for ax in (8, w - 7):
        cv.vline(ax, 0, 16, "#6a5a4a")
    y = 15
    cv.rect(0, y, w + 2, h + 2, OUT)
    cv.rect(1, y + 1, w, h, "#e6dcc4"); cv.hline(1, y + 1, w, "#fff6e0"); cv.hline(1, y + h, w, "#b8a888")
    cv.rect(3, y + 3, w - 4, h - 4, "#efe6d0")
    big_text(cv, label1, (w + 2 - text_width(label1) * 2) // 2, y + 6, "#3a2a2a")
    big_text(cv, label2, (w + 2 - text_width(label2) * 2) // 2, y + 24, "#9a2a2c")
    for k in range(6):                     # a few torn tape corners
        pass
    cv.rect(2, y + 1, 6, 3, C("#c8b890", 0.8)); cv.rect(w - 6, y + 1, 6, 3, C("#c8b890", 0.8))
    return cv


def upstage_set(cv, x0, x1, top, base, dawn=False, seed=0, frame_dy=18, aisle=92, frame=(168, 98)):
    """Inside the proscenium: the cyclorama (night sky blue, or dull grey under work lights at
    dawn), black masking legs, VAL's teal frame, three risers of ceremony chairs with RESERVED
    cards (gone at dawn), CU bunting along the riser fronts, chairs flown on lines above (struck at
    dawn, their lines hanging empty), and the banner. Returns dict with card points, empty riser
    seat points (for chairs that appear), the banner rect."""
    rng = _rng(seed)
    w = x1 - x0
    cyc = CYC_DAWN if dawn else CYC_NIGHT
    band_ramp(cv, x0, top, w, base - top, cyc, seed=seed, ragged=0.3)
    if not dawn:
        for _ in range(w // 6):
            sx, sy = x0 + int(rng.integers(0, w)), top + int(rng.integers(0, (base - top) * 2 // 3))
            cv.px(sx, sy, "#8a90c0" if rng.random() < 0.7 else "#d8dcf0")
    # masking legs and a border
    for lx in (x0, x1 - 16):
        cv.rect(lx, top, 16, base - top, "#0c0a12")
        for fx in range(lx + 2, lx + 16, 4):
            cv.vline(fx, top, base - top, "#16121e")
    cv.rect(x0, top, w, 8, "#0c0a12")
    cx = (x0 + x1) // 2
    # VAL's frame behind the risers
    val_frame(cv, cx, top + frame_dy, frame[0], frame[1], dawn=dawn, seed=seed)
    # flown chairs on lines (night) / empty lines with hooks (dawn)
    lines = [(x0 + 40, 56), (x0 + 74, 40), (x0 + 112, 64), (x1 - 112, 50), (x1 - 76, 66), (x1 - 42, 44)]
    for (lx, ly) in lines:
        ly += top
        if dawn:
            cv.vline(lx, top + 8, ly - top - 22, "#6a5a4a"); cv.rect(lx - 1, ly - 14, 3, 2, IRON[3])
        else:
            flown_chair(cv, lx, ly, top + 8, sway=int(rng.integers(-1, 2)))
    # risers: three tiers stepping up toward the back, chairs facing the house
    out = {"cards": [], "slots": []}
    tiers = [(base - 34, 12, 16), (base - 22, 13, 17), (base - 10, 14, 18)]     # chair base y, width, height
    for t, (by, cw, chh) in enumerate(tiers):
        # riser front (deck colour) with bunting
        cv.rect(x0 + 16, by, w - 32, base - by, OAKF[2 + t % 2]); cv.hline(x0 + 16, by, w - 32, OAKF[5])
        n = (w - 60) // (cw + 3)
        sx0 = cx - (n * (cw + 3)) // 2 + (cw + 3) // 2
        for i in range(n):
            px_ = sx0 + i * (cw + 3)
            if abs(px_ - cx) < aisle:
                continue
            if (i + t) % 7 == 3 and not dawn:
                out["slots"].append((px_, by))
                continue
            c = ceremony_chair(cv, px_, by, w=cw, h=chh, card=not dawn)
            if c:
                out["cards"].append(c)
        # bunting swags (CU black and gold) along the front edge
        for sx in list(range(x0 + 18, cx - aisle - 8, 16)) + list(range(cx + aisle - 6, x1 - 18, 16)):
            for k in range(16):
                yy = by + 1 + int(3 * np.sin(np.pi * k / 16))
                cv.px(sx + k, yy, CU_GOLD[3] if t % 2 == 0 else CU_BLACK[3])
                cv.px(sx + k, yy + 1, CU_BLACK[1] if t % 2 == 0 else CU_GOLD[2])
    # the centre stair up the risers to the frame, carpeted with the procession runner
    for t, (by, cw, chh) in enumerate(tiers):
        sw = aisle - 10 + t * 6
        cv.rect(cx - sw, by, sw * 2, base - by, OAKF[3 + t % 2]); cv.hline(cx - sw, by, sw * 2, OAKF[6])
        cv.vline(cx - sw, by, base - by, OAKF[1]); cv.vline(cx + sw - 1, by, base - by, OAKF[1])
        cv.rect(cx - 22, by, 44, base - by, RUNNER_M[2] if not dawn else RUNNER_M[3])
        cv.hline(cx - 22, by, 44, RUNNER_M[4]); cv.vline(cx - 22, by, base - by, RUNNER_M[1]); cv.vline(cx + 21, by, base - by, RUNNER_M[1])
    return out


# --- M06 floor and props -------------------------------------------------------------------------
OAK_FLOOR_M = ["#1e1210", "#2c1a16", "#3a241c", "#4a2e22", "#58382a", "#664232", "#7a5240"]   # house floor (night)
RUNNER_M = ["#2a0c14", "#3e121c", "#561a26", "#6e2430", "#c09048", "#e0b860"]                   # procession runner


def plank_floor(cv, mask, pal=OAK_FLOOR_M, seed=0, row=7, grow=0.35, y0=142, seam=1, tones=(3, 6), length=(50, 120)):
    """Oak boards running across the room, seen from above at a slant: rows a little deeper
    toward the bottom, staggered joints, each board its own tone, a dark seam under every row."""
    rng = _rng(seed)
    ys, xs = np.where(mask)
    if len(ys) == 0:
        return
    ya, yb = ys.min(), ys.max() + 1
    y = ya
    r = 0
    while y < yb:
        f = 1 + grow * max(0.0, (y - y0) / 360)
        rh = max(4, int(round(row * f)))
        x = -int(rng.integers(0, 60))
        while x < cv.w:
            bl = int(rng.integers(*length))
            tone = pal[int(rng.integers(*tones))]
            sub = np.zeros((cv.h, cv.w), bool)
            sub[y:y + rh, max(0, x):max(0, x + bl)] = True
            sub &= mask
            cv.fill_mask(sub, tone)
            hi = np.zeros_like(sub); hi[y, max(0, x):max(0, x + bl)] = True
            cv.fill_mask(hi & mask, shade(tone, 0.1))
            j = np.zeros_like(sub); j[y:y + rh, max(0, min(cv.w - 1, x + bl - 1))] = True
            cv.fill_mask(j & mask, pal[seam])
            # grain streaks
            for _ in range(bl // 18):
                gx = x + int(rng.integers(2, max(3, bl - 8)))
                gy = y + int(rng.integers(1, max(2, rh - 1)))
                if 0 <= gy < cv.h and 0 <= gx < cv.w - 6 and mask[gy, gx]:
                    cv.hline(gx, gy, int(rng.integers(3, 8)), shade(tone, -0.12))
            x += bl
        seam_m = np.zeros((cv.h, cv.w), bool)
        seam_m[min(cv.h - 1, y + rh - 1), :] = True
        cv.fill_mask(seam_m & mask, pal[seam])
        y += rh
        r += 1


def runner_m(cv, mask, pal=RUNNER_M, border=3):
    """A velvet procession runner: deep red with a gold border line and a small diamond pattern."""
    from scipy import ndimage
    cv.fill_mask(mask, pal[2])
    inner = ndimage.binary_erosion(mask, iterations=border)
    edge = mask & ~inner
    cv.fill_mask(edge, pal[1])
    line = inner & ~ndimage.binary_erosion(inner, iterations=1)
    cv.fill_mask(line, pal[4])
    ys, xs = np.where(ndimage.binary_erosion(inner, iterations=3))
    pick = ((xs // 2 + ys // 2) % 8 == 0) & ((xs // 2 - ys // 2) % 8 == 0)
    for y, x in zip(ys[pick], xs[pick]):
        cv.px(x, y, pal[3])


def stage_lip(width=530, height=30, dawn=False):
    """The front of the thrust stage: an oak nosing lit along its edge, a row of hooded footlights
    (lit at night, dark at dawn), and the maroon velvet skirt in deep folds below. Returns the
    sprite (Canvas, ax, ay)."""
    cv = Canvas(width + 4, height + 4)
    ox, base = 2, height + 1
    top = base - height
    cv.rect(ox, top, width, height, OUT)
    # nosing
    cv.rect(ox + 1, top + 1, width - 2, 5, OAKF[4]); cv.hline(ox + 1, top + 1, width - 2, OAKF[6]); cv.hline(ox + 1, top + 5, width - 2, OAKF[1])
    # skirt in folds
    for xx in range(ox + 1, ox + width - 1):
        k = [2, 3, 4, 3, 2, 1][xx % 6]
        cv.vline(xx, top + 7, height - 8, VELVET[k])
    cv.hline(ox + 1, top + 6, width - 2, VELVET[0])
    cv.hline(ox + 1, base - 2, width - 2, VELVET[1])
    for xx in range(ox + 4, ox + width - 4, 6):
        cv.px(xx, base - 3, CU_GOLD[2])
    # footlights: small hooded lamps sitting on the nosing
    for fx in range(ox + 20, ox + width - 14, 34):
        cv.rect(fx - 4, top - 4, 9, 5, OUT); cv.rect(fx - 3, top - 3, 7, 3, IRON[2]); cv.hline(fx - 3, top - 3, 7, IRON[4])
        cv.rect(fx - 2, top - 1, 5, 2, "#fff0c4" if not dawn else "#7a6a5a")
        if not dawn:
            cv.px(fx, top + 1, "#f6cf7a")
    return cv, ox + width // 2, base


def pa_column(width=46, height=110, seed=0):
    """A tall PA stack beside the stage: a sub cabinet on castors, two mid-high cabinets above it on
    a short pole, black felt with steel grilles, horn mouths, a blue status LED."""
    cv = Canvas(width + 4, height + 4, seed=seed)
    ox, base = 2, height + 1
    from props import ground_shadow
    ground_shadow(cv, ox + width // 2, base, width // 2, 2, alpha=0.45)
    STEEL = ["#121218", "#1c1c26", "#2a2a36", "#3a3a48", "#525264", "#74748a"]
    def cab(y, h, kind):
        cv.rect(ox, y, width, h, OUT)
        cv.rect(ox + 1, y + 1, width - 2, h - 2, STEEL[1]); cv.hline(ox + 1, y + 1, width - 2, STEEL[3])
        cv.vline(ox + 1, y + 1, h - 2, STEEL[2])
        gx, gy, gw, gh = ox + 4, y + 4, width - 8, h - 8
        cv.rect(gx, gy, gw, gh, STEEL[2])
        for yy in range(gy, gy + gh, 2):
            cv.hline(gx, yy, gw, STEEL[0])
        if kind == "sub":
            cv.ellipse(ox + width // 2 - 14, y + h // 2 - 12, 29, 25, STEEL[0]); cv.ellipse(ox + width // 2 - 11, y + h // 2 - 9, 23, 19, STEEL[3])
            cv.ellipse(ox + width // 2 - 4, y + h // 2 - 3, 9, 7, STEEL[1])
        else:
            cv.ellipse(ox + width // 2 - 10, y + 6, 21, 17, STEEL[0]); cv.ellipse(ox + width // 2 - 8, y + 8, 17, 13, STEEL[3])
            cv.rect(ox + 8, y + h - 12, width - 16, 6, STEEL[0]); cv.hline(ox + 9, y + h - 10, width - 18, STEEL[4])
    sub_h = 40
    cab(base - sub_h - 3, sub_h, "sub")
    for cx_ in (ox + 5, ox + width - 7):
        cv.rect(cx_, base - 4, 3, 4, OUT)
    cv.rect(ox + width // 2 - 2, base - sub_h - 14, 5, 12, OUT); cv.vline(ox + width // 2, base - sub_h - 14, 12, STEEL[4])
    top_h = 32
    cab(base - sub_h - 14 - top_h * 2, top_h, "top")
    cab(base - sub_h - 14 - top_h, top_h, "top")
    cv.px(ox + width - 6, base - sub_h - 14 - 4, "#6ab0ff"); cv.px(ox + width - 6, base - 8, "#6ab0ff")
    cv.rect(ox + 4, base - sub_h + 2, 14, 3, CU_GOLD[2])         # gaffer-taped label
    return cv, ox + width // 2, base


def reserved_row(width=145, height=40, cards=True, seed=0):
    """Five ceremony chairs in a row on the house floor, seen from behind, facing the stage: a gold
    cord along their backs and a RESERVED card hung on every one (or, once VAL is settled, the
    cards gone and one programme left on a seat)."""
    from props import ground_shadow
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2, 2, alpha=0.4)
    n = 5
    cw = width // n
    for i in range(n):
        cx = ox + i * cw + cw // 2
        x = cx - 11
        # legs and seat (seen from behind, slightly above)
        cv.rect(x + 1, base - 18, 3, 18, OUT); cv.rect(x + 19, base - 18, 3, 18, OUT)
        cv.vline(x + 2, base - 17, 16, CHAIR[3]); cv.vline(x + 20, base - 17, 16, CHAIR[2])
        cv.rect(x, base - 20, 23, 5, OUT); cv.rect(x + 1, base - 19, 21, 3, CHAIR[4]); cv.hline(x + 1, base - 19, 21, CHAIR[5])
        # back
        cv.rect(x + 1, base - height + 2, 21, 20, OUT)
        cv.rect(x + 2, base - height + 3, 19, 18, CHAIR[3]); cv.hline(x + 2, base - height + 3, 19, CHAIR[6])
        cv.vline(x + 2, base - height + 3, 18, CHAIR[4]); cv.vline(x + 20, base - height + 3, 18, CHAIR[1])
        for sy in range(base - height + 8, base - 21, 4):
            cv.hline(x + 4, sy, 15, CHAIR[2])
        if cards:
            cy = base - height + 8
            cv.rect(cx - 8, cy - 1, 17, 9, OUT); cv.rect(cx - 7, cy, 15, 7, CARD[3]); cv.hline(cx - 7, cy, 15, "#fffaf0")
            cv.hline(cx - 5, cy + 3, 11, CARD_RED); cv.hline(cx - 5, cy + 5, 7, CARD[1])
    if cards:
        for i in range(n * cw):           # the gold cord along the backs
            yy = base - height + 6 + int(2 * abs(np.sin(np.pi * (i % cw) / cw)))
            cv.px(ox + i, yy, CU_GOLD[3])
    else:
        px_ = ox + 2 * cw + cw // 2
        cv.rect(px_ - 6, base - 22, 12, 4, OUT); cv.rect(px_ - 5, base - 21, 10, 2, "#ece2c8"); cv.px(px_ - 2, base - 21, CU_GOLD[2])
    return cv, ox + width // 2, base


# ============================================================================================
# M05: the house seen from the balcony (rendered in perspective into the back band)
# ============================================================================================
def house_view(width=960, height=142, dawn=False, horizon=40, F=200.0, cam=8.0, stage_z=34.0, wall_x=18.0, seed=0, ceiling=12.0):
    """The auditorium from the front of the balcony: rows of red velvet seats running down to the
    stage, aisles of carpet, side walls with two tiers of boxes and tall windows, a strip of
    coffered ceiling, the back wall with the proscenium far away. Returns (View, info) where
    info holds the screen points of seat backs (for cards), the stage opening rect, window rects."""
    from persp import View, hash2, pal_array, rgba_of, fog, warm_light
    v = View(horizon=horizon, vx=width // 2, cam=cam, F=F, W=width, H=height, fill="#0e0a12")
    house = pal_array(HOUSE_DAWN if dawn else HOUSE)
    seat = pal_array(SEAT)
    carpet = pal_array(CARPET_M)
    gilt = pal_array(GILT)
    haze = "#2a1c26" if not dawn else "#6a5450"
    ROW0, ROWD = 12.0, 0.95

    def floor_shader(X, Z):
        n = X.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        ax = np.abs(X)
        r = np.floor((Z - ROW0) / ROWD)
        f = (Z - ROW0) / ROWD - r
        col = np.floor((X + 0.27 * (r % 2)) / 0.56)
        fx = (X + 0.27 * (r % 2)) / 0.56 - col
        rgb[:] = carpet[1]
        back = f < 0.46
        top = (f >= 0.46) & (f < 0.58)
        cush = (f >= 0.58) & (f < 0.8)
        rgb[back] = seat[3]
        rgb[back & (fx < 0.12)] = seat[1]
        rgb[top] = seat[5]
        rgb[cush] = seat[2]
        lit = np.clip(1 - (stage_z - Z) / 16, 0, 1)
        rgb[back | top] = rgb[back | top] * (0.8 + 0.4 * lit[back | top, None])
        # aisles: two centre-side aisles and the outer aisles along the walls
        aisle = ((ax > 3.2) & (ax < 4.4)) | (ax > wall_x - 1.4)
        rgb[aisle] = carpet[3]
        rgb[aisle & (hash2(np.floor(X * 3), np.floor(Z * 2), 4) > 0.8)] = carpet[2]
        rgb[aisle & ((np.abs(ax - 3.2) < 0.08) | (np.abs(ax - 4.4) < 0.08))] = gilt[2]
        # the open floor before the stage and the pit rail
        front = Z > stage_z - 2.6
        rgb[front] = carpet[2]
        pit = (Z > stage_z - 1.2)
        rgb[pit] = np.array(C("#0a0608")[:3])
        rgb[(np.abs(Z - (stage_z - 1.25)) < 0.1)] = gilt[3]
        rgb[Z < ROW0] = carpet[2]
        out = rgba_of(rgb)
        if not dawn:
            warm_light(out[..., :3], np.hypot(X * 0.6, (Z - stage_z) * 1.0), 9.0, colour="#f6cf7a", strength=0.35)
        fog(out, Z, haze, 20, 60, amount=0.4)
        return out

    def wall_shader(u, Y, Z):
        n = u.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        rgb[:] = house[3]
        bay = np.floor(u / 4.2)
        bu = u / 4.2 - bay
        pil = bu < 0.12
        rgb[pil] = house[4]
        rgb[pil & (bu < 0.03)] = house[6]
        # two tiers of boxes
        for (y0, y1) in ((2.4, 4.8), (5.6, 8.2)):
            inbox = (bu > 0.18) & (bu < 0.94) & (Y > y0) & (Y < y1)
            rgb[inbox] = house[0]
            par = inbox & (Y < y0 + 0.7)
            rgb[par] = house[5]
            rgb[par & (Y > y0 + 0.55)] = gilt[3]
            rgb[par & (Y < y0 + 0.12)] = gilt[1]
            rgb[par & (Y > y0 + 0.15) & (Y < y0 + 0.5) & (np.floor(bu * 30) % 2 == 0)] = house[3]
            drape = inbox & (Y > y1 - 0.5)
            rgb[drape] = seat[3]
            rgb[drape & (Y > y1 - 0.15)] = seat[5]
            chairs = inbox & (Y > y0 + 0.9) & (Y < y0 + 1.6) & ((np.floor(bu * 9) % 2) == 0)
            rgb[chairs] = seat[2]
        # tall windows high up
        win = (bu > 0.34) & (bu < 0.76) & (Y > 9.6) & (Y < 11.8 - 1.4 * ((bu - 0.55) / 0.21) ** 2)
        if dawn:
            rgb[win] = pal_array(["#f2b878"])[0]
            rgb[win & (np.floor(Y * 2) % 3 == 0)] = pal_array(["#d8945c"])[0]
            rgb[win & (bu < 0.45)] = pal_array(["#fde2b0"])[0]
        else:
            rgb[win] = pal_array(["#1a2244"])[0]
            rgb[win & (np.floor(Y * 2) % 3 == 0)] = pal_array(["#121832"])[0]
        rgb[(np.abs(Y - 9.3) < 0.15) & ~pil] = gilt[2]                 # string course
        rgb[Y > ceiling - 0.4] = gilt[2]
        out = rgba_of(rgb)
        fog(out, Z, haze, 20, 60, amount=0.45)
        return out

    def ceiling_shader(X, Z):
        n = X.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        cx = np.floor(X / 2.6)
        cz = np.floor(Z / 2.6)
        fx = X / 2.6 - cx
        fz = Z / 2.6 - cz
        rgb[:] = house[4]
        rgb[(fx < 0.1) | (fz < 0.1)] = gilt[2]
        rgb[(fx > 0.2) & (fx < 0.8) & (fz > 0.2) & (fz < 0.8)] = house[2]
        out = rgba_of(rgb)
        fog(out, Z, haze, 20, 60, amount=0.45)
        return out

    def back_shader(X, Y):
        n = X.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        rgb[:] = house[2]
        ax = np.abs(X)
        frame = (ax < 7.4) & (Y < 9.8)
        rgb[frame] = gilt[2]
        rgb[frame & ((np.abs(ax - 7.2) < 0.12) | (np.abs(Y - 9.6) < 0.12))] = gilt[4]
        opening = (ax < 6.6) & (Y < 9.0)
        rgb[opening] = np.array(C("#0e1024" if not dawn else "#5a525c")[:3])
        out = rgba_of(rgb)
        fog(out, np.full(n, stage_z + 2.0), haze, 20, 60, amount=0.4)
        return out

    def deck_shader(X, Z):
        n = X.shape[0]
        rgb = np.zeros((n, 3), np.float32)
        rgb[:] = pal_array(OAKF)[3]
        rgb[np.floor(Z * 3) % 2 == 0] = pal_array(OAKF)[4]
        out = rgba_of(rgb)
        if not dawn:
            warm_light(out[..., :3], np.hypot(X * 0.5, Z - stage_z - 1), 5.0, colour="#58c0b8", strength=0.4)
        out[..., 3] = ((np.abs(X) < 6.6) & (Z >= stage_z) & (Z < stage_z + 2.0)).astype(np.float32)
        return out

    v.ground(floor_shader, z_max=stage_z + 4)
    v.ground(ceiling_shader, height=ceiling, z_max=stage_z + 2.0, y_from=-1.0, y_to=horizon)
    v.back(stage_z + 2.0, back_shader, region=lambda X, Y: (Y > 0.0) & (Y < ceiling) & (np.abs(X) < wall_x))
    # the stage: front face and deck inside the arch
    v.plane((-6.6, stage_z), (6.6, stage_z), lambda u, Y, Z: rgba_of(np.tile(pal_array([VELVET[2]]), (u.shape[0], 1))), y_max=1.1)
    v.ground(deck_shader, height=1.1, z_max=stage_z + 2.0, y_from=None)
    for side in (-1, 1):
        v.plane((side * wall_x, 4.0), (side * wall_x, stage_z + 2.0), wall_shader, y_max=ceiling)
    info = {}
    # screen rect of the proscenium opening (for the crisp painting of the set)
    x0, y0 = v.project(-6.6, 9.0, stage_z + 2.0)
    x1, y1 = v.project(6.6, 1.1, stage_z + 2.0)
    info["stage"] = (int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)))
    # seat-back centres (screen) for cards
    pts = []
    rng = _rng(seed)
    for r in range(int((stage_z - 2.6 - ROW0) / ROWD)):
        Z = ROW0 + r * ROWD + 0.2
        for c in range(-26, 26):
            X = (c + 0.5) * 0.56 - 0.27 * (r % 2)
            ax = abs(X)
            if (3.2 - 0.3 < ax < 4.4 + 0.3) or ax > wall_x - 1.6:
                continue
            sx, sy = v.project(X, 0.0, Z)
            pts.append((sx, sy, r, rng.random()))
    info["seats"] = pts
    info["view"] = v
    return v, info


def stage_far(cv, x0, y0, x1, y1, dawn=False):
    """The graduation stage seen small across the house (crisp, 1:1): curtain swags, legs, the
    teal frame glowing over its risers, the banner as a gold bar, footlights."""
    w, h = x1 - x0, y1 - y0
    cv.rect(x0, y0, w, h, "#0e1024" if not dawn else "#4e4850")
    if not dawn:
        for k in range(w // 3):
            cv.px(x0 + (k * 7) % w, y0 + 2 + (k * 5) % max(1, h // 2), "#6a70a8")
    cx = (x0 + x1) // 2
    fw, fh = max(8, w // 3), max(6, h // 2)
    cv.rect(cx - fw // 2 - 1, y0 + h // 4 - 1, fw + 2, fh + 2, VAL_TEAL[4] if not dawn else VAL_TEAL[2])
    cv.rect(cx - fw // 2 + 1, y0 + h // 4 + 1, fw - 2, fh - 2, VAL_TEAL[1] if not dawn else CYC_DAWN[2])
    if not dawn:
        for ry in range(y0 + h // 4 + fh - 4, y0 + h // 4 + 2, -3):
            cv.hline(cx - fw // 2 + 2, ry, fw - 4, mix("#e8d8a0", VAL_TEAL[3], (y0 + h // 4 + fh - ry) / fh))
    # risers of chairs (dots) either side
    for t in range(3):
        ry = y1 - 3 - t * 3
        for xx in range(x0 + 4, x1 - 4, 3):
            if abs(xx - cx) < fw // 2 + 2:
                continue
            cv.px(xx, ry, CHAIR[4]); cv.px(xx, ry + 1, CHAIR[2])
            if not dawn and (xx // 3 + t) % 2 == 0:
                cv.px(xx, ry - 1, CARD[3])
    # banner bar, valance swags, curtain legs
    cv.rect(cx - w // 3, y0 + 3, 2 * w // 3, 3, CU_BLACK[1] if not dawn else "#e6dcc4")
    cv.hline(cx - w // 3, y0 + 4, 2 * w // 3, CU_GOLD[3] if not dawn else "#9a2a2c")
    cv.rect(x0, y0, w, 3, VELVET[3])
    for sx in range(x0, x1, 8):
        cv.px(sx + 4, y0 + 3, VELVET[3]); cv.px(sx + 3, y0 + 3, VELVET[3]); cv.px(sx + 5, y0 + 3, VELVET[3])
    for lx in (x0, x1 - 4):
        cv.rect(lx, y0, 4, h, VELVET[2]); cv.vline(lx + 1, y0, h, VELVET[4])
    for fx in range(x0 + 4, x1 - 3, 5):
        cv.px(fx, y1, "#fff0c4" if not dawn else "#8a7a6a")


def chandelier(width=56, height=50, lit=1.0):
    """A crystal chandelier hanging in the foreground of the balcony view: chain and gilt crown,
    a ring of candle arms, then tiers of crystal drops narrowing to a pendant, catching the light."""
    cv = Canvas(width, height)
    cx = width // 2
    for y in range(0, 10):
        cv.px(cx, y, GILT[3] if y % 2 else GILT[1])
    cv.ellipse(cx - 5, 9, 11, 6, GILT[2]); cv.hline(cx - 4, 10, 9, GILT[4])
    glow = "#fff4d8" if lit else "#d8d0c4"
    # candle ring
    cv.ellipse(cx - 22, 18, 45, 9, GILT[1]); cv.ellipse(cx - 21, 18, 43, 7, GILT[3])
    for k in range(-20, 21, 5):
        yy = 20 + int(3 * (1 - (k / 20) ** 2))
        cv.vline(cx + k, yy - 6, 5, "#f2ead6"); cv.px(cx + k, yy - 7, glow)
        if lit:
            cv.px(cx + k, yy - 8, C("#fff0c8", 0.6))
    # tiers of crystal drops
    tiers = [(20, 25), (16, 30), (12, 35), (8, 40), (4, 44)]
    for i, (r, y) in enumerate(tiers):
        for k in range(-r, r + 1, 2):
            c = "#e8f0ff" if (k // 2 + i) % 3 == 0 else "#b8c8e8" if (k // 2 + i) % 3 == 1 else "#8a9ac0"
            cv.vline(cx + k, y, 3, c)
        cv.hline(cx - r, y, 2 * r + 1, GILT[2] if i < 2 else "#c8d4f0")
    cv.vline(cx, 44, 5, "#e8f0ff"); cv.px(cx, 49, "#ffffff")
    if lit:
        for (rr, a) in ((26, 0.05), (18, 0.08), (11, 0.1)):
            cv.ellipse(cx - rr, 30 - rr // 2, rr * 2, rr, C("#fff0c8", a))
    return cv


# --- M05 balcony pieces -----------------------------------------------------------------------------
CARPET_B = ["#1a0a10", "#2a1018", "#3a141e", "#4a1a26", "#5a222e", "#8a6a3a", "#b08848"]       # balcony carpet (night)
CARPET_B_DAWN = ["#2e1418", "#401c22", "#52242a", "#622c32", "#72363a", "#a08050", "#c8a060"]


def balcony_carpet(cv, mask, pal=CARPET_B, seed=0):
    """Wall-to-wall theatre carpet: a wine-red field with a dark trellis of wide diamonds (the
    floor plane foreshortened 2:1), alternate diamonds a shade apart, a small four-petal flower
    in each and a gold stud where the trellis lines cross."""
    ys, xs = np.where(mask)
    xx = xs % 32
    yy = ys % 16
    d = np.abs(xx - 16) + 2 * np.abs(yy - 8)
    rgb = np.zeros((len(xs), 3), np.float32)
    rgb[:] = C(pal[2])[:3]
    rgb[d > 16] = C(mix(pal[2], pal[3], 0.55))[:3]
    rgb[(d == 16) | (d == 15)] = C(pal[1])[:3]
    # flowers in the centre of both diamond families
    for (cx, cy, col) in ((16, 8, pal[4]), (0, 0, pal[3])):
        dx = (xx - cx + 16) % 32 - 16
        dy = (yy - cy + 8) % 16 - 8
        pet = ((np.abs(dx) <= 2) & (dy == 0)) | ((dx == 0) & (np.abs(dy) <= 1))
        rgb[pet] = C(col)[:3]
        rgb[(dx == 0) & (dy == 0)] = C(pal[5] if cx == 16 else pal[4])[:3]
    stud = ((xx == 0) & (yy == 8)) | ((xx == 16) & (yy == 0))
    rgb[stud] = C(pal[5])[:3]
    cv.a[ys, xs, :3] = rgb
    cv.a[ys, xs, 3] = 1.0


def balcony_parapet(cv, x0, x1, top, base, dawn=False):
    """The back of the balcony front seen from the balcony aisle: a brass rail on short posts over
    a velvet-padded cap, the panelled back face of the parapet below."""
    pal = HOUSE_DAWN if dawn else HOUSE
    w = x1 - x0
    # back face: oak panelling with gilt beads, a dark kick rail along the floor
    cv.rect(x0, top + 9, w, base - top - 9, OAKF[2] if not dawn else OAK_SUN[1])
    n = max(1, (w - 8) // 36)
    pw = (w - 8) / n
    for k in range(n):
        px_ = x0 + 4 + int(k * pw)
        qw = int(pw) - 6
        cv.rect(px_, top + 12, qw, base - top - 18, OAKF[1] if not dawn else OAK_SUN[0])
        cv.rect(px_ + 1, top + 13, qw - 2, base - top - 20, OAKF[3] if not dawn else OAK_SUN[2])
        cv.hline(px_ + 1, top + 13, qw - 2, GILT[2]); cv.vline(px_ + 1, top + 13, base - top - 20, GILT[1])
        cv.hline(px_ + 3, top + 15, qw - 6, OAKF[4] if not dawn else OAK_SUN[3])
    cv.rect(x0, base - 5, w, 4, OAKF[1] if not dawn else OAK_SUN[0]); cv.hline(x0, base - 5, w, GILT[2])
    cv.hline(x0, base - 1, w, OUT)
    # padded velvet cap
    cv.rect(x0, top + 3, w, 7, OUT)
    cv.rect(x0, top + 4, w, 5, VELVET[3]); cv.hline(x0, top + 4, w, VELVET[5]); cv.hline(x0, top + 8, w, VELVET[1])
    for bx in range(x0 + 6, x1, 12):
        cv.px(bx, top + 6, VELVET[1])
    # brass rail on posts
    for px_ in range(x0 + 10, x1, 40):
        cv.rect(px_ - 1, top - 3, 3, 7, OUT); cv.vline(px_, top - 3, 6, GILT[4])
    cv.rect(x0, top - 5, w, 3, OUT); cv.hline(x0, top - 4, w, GILT[4]); cv.hline(x0, top - 3, w, GILT[2])


def side_door(cv, x, top, w, h, kind="service", dawn=False, open_=False):
    """A door at the end of the balcony aisle. kind 'service': a painted steel door with a push
    bar and a small enamel sign; 'stage': a leather-padded door with brass studs and a porthole.
    open_: the door swung in, showing the stairwell/stage light beyond."""
    cv.rect(x - 4, top - 4, w + 8, h + 4, LIMESTONE[1] if not dawn else LIMESTONE[2])
    cv.hline(x - 4, top - 4, w + 8, LIMESTONE[3])
    cv.rect(x - 1, top - 1, w + 2, h + 1, OUT)
    if open_:
        if kind == "service":
            # a concrete stairwell going down: caged bulb, painted wall, steps dropping away right
            cv.rect(x, top, w, h, "#3a3844")
            cv.rect(x, top, w, 6, "#2a2832")
            for k in range(0, h - 20, 3):
                cv.hline(x + 1, top + 6 + k, w - 2, C("#8a96a8", 0.04 + 0.05 * (k < 24)))
            cv.rect(x, top + h - 34, w, 34, "#2a2832")
            for i in range(6):                                   # steps (side view) descending
                sx, sy = x + 2 + i * 9, top + h - 34 + i * 5
                cv.rect(sx, sy, w - (sx - x), 5, "#4a4856" if i % 2 == 0 else "#44424e")
                cv.hline(sx, sy, w - (sx - x), "#8a8e98")
            cv.line(x + 2, top + h - 46, x + w - 2, top + h - 16, "#c8a040")      # handrail
            cv.line(x + 2, top + h - 45, x + w - 2, top + h - 15, "#6a5020")
            cv.rect(x + w // 2 - 3, top + 8, 7, 7, "#1a1820")                     # caged bulb
            cv.rect(x + w // 2 - 2, top + 9, 5, 5, "#e8eef8"); cv.px(x + w // 2, top + 11, "#ffffff")
            cv.vline(x + w // 2 - 2, top + 9, 5, "#1a1820"); cv.vline(x + w // 2 + 2, top + 9, 5, "#1a1820")
            halo(cv, x + w // 2, top + 11, 14, "#c8d8f0", 0.12)
            cv.rect(x, top, 7, h, "#2e3a34"); cv.vline(x + 6, top, h, OUT); cv.vline(x + 1, top, h, "#465a50")
        else:
            # the wings: warm stage light, fly ropes, the edge of a flat, a work light
            for k in range(0, h, 6):
                cv.rect(x, top + k, w, 6, mix("#3a2a20", "#a87a48", min(1.0, k / h * 1.3)))
            for rx in range(x + 12, x + w - 4, 6):
                cv.vline(rx, top, h - 10, "#c8b090"); cv.vline(rx + 1, top, h - 10, "#4a3628")
            cv.rect(x + w - 18, top + 6, 16, h - 6, "#2a2228"); cv.vline(x + w - 18, top + 6, h - 6, "#6a5444")
            cv.rect(x + 14, top + 14, 6, 4, "#1a1214"); cv.hline(x + 15, top + 17, 4, "#fff0c4")
            halo(cv, x + 17, top + 18, 16, "#f6cf7a", 0.18)
            cv.rect(x, top + h - 4, w, 4, "#5a3a24"); cv.hline(x, top + h - 4, w, "#c8a060")
            cv.rect(x, top, 7, h, VELVET[2]); cv.vline(x + 6, top, h, OUT); cv.vline(x + 1, top, h, VELVET[4])
    else:
        if kind == "service":
            cv.rect(x, top, w, h, "#2e3a34"); cv.vline(x, top, h, "#465a50"); cv.vline(x + w - 1, top, h, "#1a2420")
            cv.rect(x + 4, top + h // 2 - 2, w - 8, 4, OUT); cv.hline(x + 5, top + h // 2 - 1, w - 10, "#8a8e98")
            cv.rect(x + w - 10, top + h // 2 - 8, 3, 6, "#8a8e98")
            cv.rect(x + 8, top + 8, w - 16, 14, "#22302a")
        else:
            cv.rect(x, top, w, h, VELVET[2])
            for sy in range(top + 4, top + h - 2, 8):
                for sx in range(x + 4, x + w - 2, 8):
                    cv.px(sx, sy, GILT[4]); cv.px(sx + 4, sy + 4, GILT[3])
            cv.ellipse(x + w // 2 - 6, top + 10, 13, 13, GILT[2]); cv.ellipse(x + w // 2 - 4, top + 12, 9, 9, "#f6cf7a" if not dawn else "#c8b8a0")
            cv.rect(x + w - 9, top + h // 2, 4, 8, GILT[3])
    cv.hline(x - 4, top + h, w + 8, OUT)


def lightbox_sign(cv, x, y, label, lit=True, colour="#e84a3a", bg="#1a0a0c"):
    """A small theatre lightbox sign (LAST CALL, EXIT): a dark case with glowing letters."""
    w = text_width(label) + 8
    cv.rect(x - 1, y - 1, w + 2, 13, OUT)
    cv.rect(x, y, w, 11, bg if lit else "#2a2428")
    text(cv, label, x + 4, y, colour if lit else "#5a4a4a")
    return w


def enamel_sign(cv, x, y, label, fg="#f2ead6", bg="#2a4a6a"):
    w = text_width(label) + 8
    cv.rect(x - 1, y - 1, w + 2, 13, OUT)
    cv.rect(x, y, w, 11, bg); cv.hline(x, y, w, mix(bg, "#ffffff", 0.25))
    text(cv, label, x + 4, y, fg)
    return w


def brass_rail(width=580, height=28, cards=True, seed=0):
    """The balcony's cross-aisle rail: a polished brass tube on turned brass posts with a lower
    rail, a red velvet skirt panel between each pair of posts, and (while Rook keeps the doors)
    RESERVED cards hung all along it. Returns (Canvas, ax, ay, card_points)."""
    from props import ground_shadow
    cv = Canvas(width + 6, height + 8, seed=seed)
    ox, base = 3, height + 5
    ground_shadow(cv, ox + width // 2, base, width // 2, 2, alpha=0.4)
    top = base - height
    step = 48
    posts = list(range(ox + 2, ox + width, step))
    if posts[-1] != ox + width - 3:
        posts.append(ox + width - 3)
    for i in range(len(posts) - 1):
        a, b = posts[i] + 2, posts[i + 1] - 1
        cv.rect(a, top + 6, b - a, height - 10, VELVET[2])
        for xx in range(a, b):
            k = [2, 3, 4, 3][(xx - a) % 4]
            cv.vline(xx, top + 7, height - 12, VELVET[k])
        cv.hline(a, top + height - 5, b - a, VELVET[1])
        for xx in range(a, b, 3):
            cv.px(xx, top + height - 4, GILT[3])
    for px_ in posts:
        cv.rect(px_ - 2, top - 1, 5, height, OUT)
        cv.vline(px_ - 1, top, height - 2, GILT[4]); cv.vline(px_, top, height - 2, GILT[3]); cv.vline(px_ + 1, top, height - 2, GILT[1])
        cv.ellipse(px_ - 3, top - 4, 7, 6, OUT); cv.ellipse(px_ - 2, top - 3, 5, 4, GILT[3]); cv.px(px_ - 1, top - 3, GILT[5])
        cv.rect(px_ - 3, base - 3, 7, 3, OUT); cv.hline(px_ - 2, base - 3, 5, GILT[3])
    cv.rect(ox, top + 1, width, 4, OUT); cv.hline(ox, top + 2, width, GILT[5]); cv.hline(ox, top + 3, width, GILT[2])
    pts = []
    if cards:
        for i in range(len(posts) - 1):
            for frac in (0.33, 0.67):
                cx = int(posts[i] + (posts[i + 1] - posts[i]) * frac)
                cy = top + 7
                cv.line(cx - 3, top + 4, cx - 2, cy, OUT); cv.line(cx + 3, top + 4, cx + 2, cy, OUT)
                cv.rect(cx - 6, cy, 13, 8, OUT); cv.rect(cx - 5, cy + 1, 11, 6, CARD[3]); cv.hline(cx - 5, cy + 1, 11, "#fffaf0")
                cv.hline(cx - 4, cy + 3, 9, CARD_RED); cv.hline(cx - 3, cy + 5, 6, CARD[1])
                pts.append((cx - ox - width // 2, cy + 3 - base))
    return cv, ox + width // 2, base, pts


def velvet_bench(width=160, height=32, seed=0):
    """A tufted red velvet banquette on gilt legs (the balcony lounge's bench)."""
    from props import ground_shadow
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2, 2, alpha=0.42)
    top = base - height
    # low back
    cv.rect(ox + 4, top, width - 8, 14, OUT)
    cv.rect(ox + 5, top + 1, width - 10, 12, VELVET[3]); cv.hline(ox + 5, top + 1, width - 10, VELVET[5])
    for tx in range(ox + 12, ox + width - 8, 12):
        cv.px(tx, top + 6, VELVET[1]); cv.px(tx + 6, top + 9, VELVET[1])
        cv.px(tx - 1, top + 5, VELVET[4])
    cv.hline(ox + 5, top + 12, width - 10, VELVET[1])
    # seat cushion
    cv.rect(ox, top + 13, width, 9, OUT)
    cv.rect(ox + 1, top + 14, width - 2, 7, VELVET[4]); cv.hline(ox + 1, top + 14, width - 2, VELVET[6])
    for tx in range(ox + 10, ox + width - 6, 14):
        cv.px(tx, top + 17, VELVET[2]); cv.px(tx + 1, top + 17, VELVET[3])
    cv.hline(ox + 1, top + 20, width - 2, VELVET[2])
    # gilt apron and legs
    cv.rect(ox + 2, top + 22, width - 4, 3, GILT[2]); cv.hline(ox + 2, top + 22, width - 4, GILT[4])
    for lx in (ox + 5, ox + width // 2 - 1, ox + width - 8):
        cv.rect(lx, top + 25, 4, base - top - 25, OUT); cv.vline(lx + 1, top + 25, base - top - 26, GILT[3])
    return cv, ox + width // 2, base


def seating_chart(width=120, height=58, label="ONE EXIT"):
    """An easel at the rail with the house plan: rows of seats as dots, every one marked reserved
    in red, the header ONE EXIT, and one green arrow pointing to the single door."""
    cv = Canvas(width + 4, height + 6)
    ox, base = 2, height + 3
    from props import ground_shadow
    ground_shadow(cv, ox + width // 2, base, width // 3, 2, alpha=0.4)
    bw, bh = width - 12, height - 16
    bx, by = ox + 6, base - height
    # easel legs
    cv.line(bx + 10, by + bh, bx + 4, base - 1, OUT); cv.line(bx + 11, by + bh, bx + 5, base - 1, GILT[2])
    cv.line(bx + bw - 10, by + bh, bx + bw - 4, base - 1, OUT); cv.line(bx + bw - 11, by + bh, bx + bw - 5, base - 1, GILT[2])
    cv.line(bx + bw // 2, by + bh, bx + bw // 2 + 2, base - 4, OUT)
    # board
    cv.rect(bx - 1, by - 1, bw + 2, bh + 2, OUT)
    cv.rect(bx, by, bw, bh, GILT[2]); cv.rect(bx + 2, by + 2, bw - 4, bh - 4, "#ece2c8")
    cv.rect(bx + 2, by + 2, bw - 4, 11, "#9a2a2c")
    tw = text_width(label)
    text(cv, label, bx + (bw - tw) // 2, by + 2, "#fff4e0")
    # the house plan: a stage bar and curved rows of reserved dots
    cx = bx + bw // 2
    cv.rect(cx - 16, by + 15, 32, 2, "#5a4a3a")
    for r in range(5):
        yy = by + 19 + r * 3
        half = 14 + r * 6
        for xx in range(cx - half, cx + half + 1, 3):
            if abs(xx - cx) < 3:
                continue
            cv.px(xx, yy + int(((xx - cx) / half) ** 2 * 2), "#b8323a")
    # the one exit: a green arrow at the back
    ay = by + bh - 6
    cv.rect(cx - 2, ay - 2, 5, 4, "#2e8a5a"); cv.poly([(cx - 5, ay - 2), (cx, ay - 6), (cx + 5, ay - 2)], "#3cba7a")
    cv.rect(cx + 6, ay - 2, 12, 5, "#2e8a5a"); text(cv, "", cx + 6, ay - 3, "#ffffff")
    return cv, ox + width // 2, base


def standard_lamp_m(height=68, lit=True):
    """A brass standard lamp with a pleated silk shade and a fringe (the balcony lounge lamp).
    Lamp core ~5px below the top."""
    from props import ground_shadow
    w = 30
    cv = Canvas(w, height + 6)
    cx, base = w // 2, height + 2
    top = base - height
    ground_shadow(cv, cx, base, 8, 2)
    cv.ellipse(cx - 7, base - 4, 15, 5, OUT); cv.ellipse(cx - 6, base - 4, 13, 4, GILT[2]); cv.hline(cx - 4, base - 4, 9, GILT[4])
    cv.rect(cx - 1, top + 14, 3, height - 16, OUT); cv.vline(cx, top + 14, height - 16, GILT[3])
    for ry in (top + 30, top + 48):
        cv.rect(cx - 2, ry, 5, 3, OUT); cv.hline(cx - 1, ry + 1, 3, GILT[4])
    # shade: a truncated cone, pleats, fringe; glowing from inside
    sh = ["#c88a4a", "#e8b06a", "#f6d08a", "#fff0c4"] if lit else ["#7a5a4a", "#9a7a5a", "#b09070", "#c8b090"]
    cv.poly([(cx - 7, top), (cx + 7, top), (cx + 12, top + 14), (cx - 12, top + 14)], OUT)
    cv.poly([(cx - 6, top + 1), (cx + 6, top + 1), (cx + 11, top + 13), (cx - 11, top + 13)], sh[1])
    for k in range(-9, 10, 3):
        cv.line(cx + k // 2, top + 2, cx + k, top + 12, sh[0])
    cv.poly([(cx - 5, top + 2), (cx - 1, top + 2), (cx - 4, top + 12), (cx - 9, top + 12)], sh[2])
    for fx in range(cx - 12, cx + 13, 2):
        cv.vline(fx, top + 14, 2 + (fx // 2) % 2, sh[0])
    cv.hline(cx - 10, top + 14, 21, sh[3] if lit else sh[2])
    return cv, cx, base


# --- battle helpers ---------------------------------------------------------------------------
class IdView:
    """A persp.View that also keeps, per subpixel, the id of whatever painted it last (-1 for
    anything without an id), so the screen boxes of seat cards can be read back after occlusion."""

    def __init__(self, view):
        self.v = view
        self.ids = np.full(view.a.shape[:2], -1, np.int64)

    def paint(self, call, shader, *args, ids=None, **kw):
        cap = {}

        def f(*a):
            out = shader(*a)
            cap["alpha"] = out[..., 3]
            cap["ids"] = ids(*a) if ids is not None else None
            return out
        if call == "ground":
            m = self.v.ground(f, **kw)
        elif call == "plane":
            m = self.v.plane(args[0], args[1], f, **kw)
        else:
            m = self.v.back(args[0], f, **kw)
        if m is None or not m.any() or "alpha" not in cap:
            return m
        cur = self.ids[m]
        al = cap["alpha"] > 0.5
        new = cap["ids"] if cap["ids"] is not None else np.full(cur.shape, -1, np.int64)
        cur[al] = new[al]
        self.ids[m] = cur
        return m

    def boxes(self, min_px=6, max_y=150):
        """{id: (x, y, w, h)} screen boxes (1x) of every id still visible."""
        from persp import SS
        ys, xs = np.nonzero(self.ids >= 0)
        res = {}
        if len(ys) == 0:
            return res
        vals = self.ids[ys, xs]
        order = np.argsort(vals, kind="stable")
        vals, ys, xs = vals[order], ys[order], xs[order]
        uniq, starts = np.unique(vals, return_index=True)
        ends = list(starts[1:]) + [len(vals)]
        for cid, a, b in zip(uniq, starts, ends):
            if b - a < min_px:
                continue
            x0, x1 = xs[a:b].min() / SS, (xs[a:b].max() + 1) / SS
            y0, y1 = ys[a:b].min() / SS, (ys[a:b].max() + 1) / SS
            rx, ry = int(np.floor(x0 + 0.3)), int(np.floor(y0 + 0.3))
            if ry > max_y:
                continue
            res[int(cid)] = (rx, ry, max(1, int(round(x1 - x0))), max(1, int(round(y1 - y0))))
        return res
