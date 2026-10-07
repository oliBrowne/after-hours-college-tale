"""Tennis courts (G02, "one friendly set") and their battle backdrop: helpers and props.

The last scene of the game, late afternoon on graduation day. Golden hour: the sun hangs low over
the right-hand trees, so every shadow runs long to the left and a little toward the viewer, the
court-facing side of the windscreen is in its own shade, and anything that faces right gets a
gold rim. Everything paints at 1:1 game pixels against a 52px character.

Sections:
  palettes ........ GOLD_SKY, SLAB_GOLD, FOREST_GOLD, FAR_GOLD, COURT/SURROUND (sun and shade),
                    WINDSCREEN, FENCE, BALL, CU_GOLD / CU_BLACK (borrowed), MACKY sandstone + MROOF
  sky & land ...... golden_sky, golden_flatirons, far_hills, campus_hall, crown_row, light_tower,
                    colorado_flag (animation frames)
  fence ........... chain_link, fence_posts, windscreen, court_sign
  floor ........... court_floor (one painter for sun and shade), shadow helpers (SUN_DX/SUN_DY)
  small things .... tennis_ball, mortarboard_flat, leaf_litter
  props ........... tennis_net, ball_machine, court_bench, ball_hopper, court_light
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from PIL import Image, ImageDraw
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, shrub
from lib_macky2 import (MACKY, MROOF, LIMESTONE, AUTUMN, CU_GOLD, CU_BLACK, big_text, band_ramp,
                        spruce, _ridge, _ramp)

INK = "#171a2b"

# --- palettes ---------------------------------------------------------------------------------
GOLD_SKY = ["#6c86ba", "#7890c0", "#869ac4", "#98a2c6", "#aca8c4", "#c0aebe", "#d2b6b2", "#e0bea4",
            "#eac898", "#f2d290", "#f6dc96", "#f9e4a6"]
SUN_RINGS = ["#fbe6a8", "#fdeebe", "#fff6d6", "#fffcee"]
SLAB_GOLD = ["#5e3436", "#7c4238", "#9a5638", "#b86c3c", "#d08444", "#e29e50", "#eeb862", "#f6d080", "#fbe2a4"]
FOREST_GOLD = ["#2a2834", "#34303a", "#403a3e", "#504840", "#625644", "#786648", "#8e784e"]
FAR_GOLD = ["#8a7c9a", "#9888a2", "#a894a6", "#b8a0a8", "#c8aca8", "#d8baa8"]
HAZE_GOLD = "#e8c8a4"
CLOUD_GOLD = ["#8e86a8", "#a898b0", "#c4a8b0", "#dcb4a8", "#eec6a0", "#f8dca8", "#fff0c8"]

# hard court: blue-green playing surface, lighter sage surround; sun is warm, shade is sky blue
COURT_SUN = ["#1a4050", "#1e4a58", "#24545e", "#2a5e64", "#306868", "#38726e", "#488078"]
COURT_SHADE = ["#142a3e", "#183246", "#1c3a4e", "#204052", "#244658", "#2c4e5c", "#385864"]
SURR_SUN = ["#587a62", "#608468", "#6a8e6e", "#729672", "#7c9e76", "#8aa87e", "#a2b88a"]
SURR_SHADE = ["#2c4448", "#324c4e", "#385454", "#3e5a58", "#42605c", "#4a6862", "#567268"]
LINE_SUN = ["#c8c6b0", "#e6e0c8", "#f8f0d8"]
LINE_SHADE = ["#90a4a8", "#a8bcbc", "#bccccc"]
PATH_SUN = ["#6a5a4e", "#867262", "#9c8670", "#ae967c", "#c0a888", "#d4bc98"]
PATH_SHADE = ["#3e3e48", "#4a4a54", "#56545e", "#605e66", "#6a6870", "#76747a"]
GRASS_SUN = ["#2a3a22", "#3a4c28", "#4c602e", "#5e7234", "#74863c", "#8e9a48"]

WINDSCREEN = ["#0e1c18", "#132420", "#182c26", "#1e342c", "#243e34", "#2c483c", "#365446", "#46644e"]
WS_LIT = ["#3e5a40", "#4e6a44", "#64784a", "#7e8a52"]          # sun coming through the fabric
FENCE = ["#16181c", "#22252a", "#30343a", "#444850", "#5c6068"]  # black vinyl-coated steel
STEEL = ["#2a2e36", "#3e444e", "#585e68", "#767c86", "#969ca4", "#c0c4c4"]
BALL = ["#6a7a1a", "#9cb024", "#c8dc3a", "#e4f070", "#f6fcb8"]
TOWEL = ["#8a8a92", "#b8b8c0", "#dcdce0", "#f6f4ee"]
BLUE_SIGN = ["#14223e", "#1e3058", "#2a4274", "#3a5690"]
MACHINE = ["#14161e", "#1e222c", "#2a303c", "#38404e", "#4a5464", "#606c7e"]
ORANGE = ["#7a2e1a", "#b44a22", "#e0702e", "#f6a052"]
LEAVES = ["#c05a2c", "#e08a3c", "#a84a30", "#e0b844", "#8a3a26", "#f4b45a"]

# long golden-hour shadows: a point h px above floor point (x, y) lands on (x + SUN_DX*h, y + SUN_DY*h)
SUN_DX, SUN_DY = -1.9, 0.45


def _rng(seed):
    return np.random.default_rng(abs(int(seed)))


def P(pal):
    return np.array([C(c)[:3] for c in pal], np.float32)


def poly_mask(w, h, pts):
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).polygon([tuple(map(float, p)) for p in pts], fill=255)
    return np.array(img) > 0


def ellipse_mask(w, h, box):
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).ellipse(box, fill=255)
    return np.array(img) > 0


def cast(x, y, h):
    """Floor point where something h px above floor point (x, y) throws its shadow."""
    return (x + SUN_DX * h, y + SUN_DY * h)


# ============================================================================================
# sky and land in the late sun
# ============================================================================================
def golden_sky(cv, x, y, w, h, sun, seed=0, pal=GOLD_SKY, reach=230.0):
    """Late afternoon sky in stepped bands (blue overhead, gold toward the horizon), brighter in a
    wide stepped field around the low sun, ragged joins; then the sun disc and its rings."""
    ys, xs = np.mgrid[y:y + h, x:x + w].astype(np.float32)
    sx, sy = sun
    vert = ((ys - y) / max(1, h - 1)) ** 1.1
    r = np.hypot((xs - sx) * 0.7, ys - sy)
    radial = np.clip(1 - r / reach, 0, 1) ** 1.5
    t = np.clip(vert * 0.8 + radial * 0.5, 0, 1)
    jitter = ((((xs // 2).astype(np.int64) * 73856093) ^ (ys.astype(np.int64) * 19349663) ^ seed) % 997) / 997.0
    t = t + (jitter - 0.5) * 0.04
    n = len(pal)
    k = np.clip((t * n).astype(int), 0, n - 1)
    cv.a[y:y + h, x:x + w, :3] = P(pal)[k]
    cv.a[y:y + h, x:x + w, 3] = 1


def sun_disc(cv, cx, cy, r=9):
    """The low sun: a stepped corona (three crisp rings) round a nearly white disc."""
    for i, (rr, c) in enumerate([(r + 14, C(SUN_RINGS[0], 0.35)), (r + 8, C(SUN_RINGS[1], 0.5)), (r + 3, SUN_RINGS[1])]):
        cv.ellipse(cx - rr, cy - rr, rr * 2 + 1, rr * 2 + 1, c)
    cv.ellipse(cx - r, cy - r, r * 2 + 1, r * 2 + 1, SUN_RINGS[2])
    cv.ellipse(cx - r + 2, cy - r + 2, r * 2 - 3, r * 2 - 3, SUN_RINGS[3])


def gold_cloud(cv, x, y, length, thick, rng, pal=CLOUD_GOLD):
    """A long flat late-afternoon cloud: lavender body, its underside and right end lit gold by
    the low sun (flat tones, crisp edges)."""
    lumps = [(x, y - thick, length, thick + 1)]
    xx = x + 4
    while xx < x + length - 10:
        lw, lh = int(rng.integers(10, 22)), int(rng.integers(thick, thick + 4))
        lumps.append((xx, y - lh, lw, lh + 1))
        xx += int(rng.integers(8, 16))
    for (lx, ly, lw, lh) in lumps:
        cv.ellipse(lx, ly, lw, lh * 2, pal[1])
    for (lx, ly, lw, lh) in lumps:
        cv.ellipse(lx + 2, ly + 1, lw - 3, lh, pal[2])
    # gold underside and the sun-side ends
    cv.hline(x + 3, y, length - 6, pal[4]); cv.hline(x + length // 3, y - 1, length // 2, pal[5])
    cv.hline(x + length // 2, y, length // 2 - 4, pal[6])


def golden_flatirons(scale=1.75, colors=30, x0=712, x1=1262):
    """The Flatirons from the title painting, repainted for late afternoon: the slab faces glow
    gold-orange where the low sun catches them, the pine slopes between them stay warm violet
    in shade. Returns (rgba, ridge)."""
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
    out = _ramp(FOREST_GOLD, tl * 1.25) * (1 - warm[..., None]) + _ramp(SLAB_GOLD, tl * 1.1 + 0.08) * warm[..., None]
    # warm haze toward the foot of the range (stepped by quantising)
    depth = (np.arange(H)[:, None] - ridge[None, :]).astype(np.float32)
    hz = np.clip((depth - 40) / 60, 0, 1)[..., None] * 0.35
    out = out * (1 - hz) + np.array(C(HAZE_GOLD)[:3]) * hz
    res = np.concatenate([out, mask[..., None].astype(np.float32)], -1)
    q = quantize(res, colors)
    q[..., 3] = mask
    return q, ridge


def far_hills(cv, x0, tops, base, pal=FAR_GOLD, seed=0):
    """A distant ridge in golden haze: flat silhouette, a lit crest, the sun side of each summit a
    step lighter, paler toward the valley (three steps)."""
    rng = _rng(seed)
    n = len(tops)
    for i in range(n):
        top = int(round(tops[i]))
        x = x0 + i
        if not 0 <= x < cv.w:
            continue
        for yy in range(top, base):
            d = yy - top
            k = 1 if d < 10 else 2 if d < 22 else 3
            cv.px(x, yy, pal[k])
        # right-facing slopes (rising to the left) catch the sun
        if i + 1 < n and tops[i + 1] > tops[i] + 0.3:
            cv.vline(x, top + 1, 6, pal[3])
        cv.px(x, top, pal[5] if rng.random() < 0.7 else pal[4])


def campus_hall(cv, x0, x1, eave, base, seed=0, pavilion=None, sun_x=640):
    """A CU sandstone hall seen across the courts in the low sun: rough Lyons sandstone in
    courses, limestone sills and string course, two storeys of windows (some flashing gold in the
    sun), a red clay tile hip roof with dormers and chimneys, and a gabled centre pavilion.
    pavilion: (cx, w, rise) of the taller centre block, or None."""
    rng = _rng(seed)
    wall = MACKY
    # walls: courses 3px, blocks 5-11px, each block one tone, lit end on the right
    for cy in range(eave, base, 3):
        xx = x0 - int(rng.integers(0, 8))
        while xx < x1:
            bw = int(rng.integers(5, 12))
            t = rng.random()
            tone = wall[5] if t < 0.45 else wall[4] if t < 0.75 else wall[6] if t < 0.92 else wall[3]
            a, b = max(x0, xx), min(x1, xx + bw)
            if b > a:
                cv.rect(a, cy, b - a, 3, tone)
                cv.hline(a, cy + 2, b - a, wall[3])
                cv.px(b - 1, cy, wall[7] if tone != wall[3] else wall[5])
            xx += bw
    cv.vline(x0, eave, base - eave, wall[2]); cv.vline(x1 - 1, eave, base - eave, wall[7])
    # limestone string course and windows (sills and lintels, two storeys)
    sc = eave + 14
    cv.hline(x0, sc, x1 - x0, LIMESTONE[4]); cv.hline(x0, sc + 1, x1 - x0, LIMESTONE[2])
    cv.hline(x0, eave, x1 - x0, LIMESTONE[3]); cv.hline(x0, eave + 1, x1 - x0, wall[2])
    for wy, wh in ((eave + 4, 7), (sc + 4, 8)):
        for wx in range(x0 + 6, x1 - 6, 11):
            if pavilion and abs(wx + 2 - pavilion[0]) < pavilion[1] // 2 + 2:
                continue
            cv.rect(wx - 1, wy - 1, 6, 1, LIMESTONE[3])
            cv.rect(wx, wy, 4, wh, "#2a1e2a")
            cv.vline(wx + 2, wy, wh, "#3e2e36"); cv.hline(wx, wy + wh // 2, 4, "#3e2e36")
            if rng.random() < 0.35:                      # sun flashing on the glass
                cv.rect(wx, wy, 2, wh // 2, "#f8d890"); cv.px(wx, wy, "#fff2c8")
            elif rng.random() < 0.4:
                cv.rect(wx, wy, 2, 2, "#8a6a6a")
            cv.rect(wx - 1, wy + wh, 6, 1, LIMESTONE[4])
    # hip roof: eave overhang with its shadow, barrel tile rows
    rise = 13
    pts = [(x0 - 3, eave), (x0 + rise, eave - rise), (x1 - rise, eave - rise), (x1 + 2, eave)]
    cv.poly(pts, MROOF[3])
    for ty in range(eave - rise + 1, eave, 2):
        inset = (ty - (eave - rise))
        xa, xb = x0 + rise - inset - 2, x1 - rise + inset + 1
        for tx in range(xa, xb, 2):
            cv.px(tx, ty, MROOF[4] if (tx // 2 + ty // 2) % 2 else MROOF[2])
    # hip lines and the sunlit right hip
    cv.line(x0 - 3, eave, x0 + rise, eave - rise, MROOF[1])
    cv.line(x1 + 2, eave, x1 - rise, eave - rise, MROOF[5])
    cv.hline(x0 + rise, eave - rise, x1 - x0 - 2 * rise, MROOF[5])
    cv.poly([(x1 - rise, eave - rise), (x1 + 2, eave), (x1 - 6, eave)], MROOF[4])
    cv.hline(x0 - 3, eave, x1 - x0 + 6, MROOF[1]); cv.hline(x0 - 2, eave + 1, x1 - x0 + 4, C("#1a0e14", 0.6))
    # dormers and chimneys
    for dx in range(x0 + 24, x1 - 20, 46):
        if pavilion and abs(dx - pavilion[0]) < pavilion[1] // 2 + 10:
            continue
        cv.poly([(dx - 4, eave - 3), (dx, eave - 9), (dx + 5, eave - 3)], MROOF[4])
        cv.rect(dx - 3, eave - 3, 7, 3, wall[5]); cv.rect(dx - 1, eave - 3, 3, 3, "#2a1e2a")
        cv.line(dx, eave - 9, dx + 5, eave - 3, MROOF[5])
    for chx in (x0 + 14, x1 - 30):
        cv.rect(chx, eave - rise - 6, 5, 8, wall[4]); cv.vline(chx + 4, eave - rise - 6, 8, wall[7])
        cv.hline(chx - 1, eave - rise - 7, 7, LIMESTONE[3])
    if pavilion:
        cx, pw, prise = pavilion
        px0, px1 = cx - pw // 2, cx + pw // 2
        top = eave - prise
        for cy in range(top, base, 3):
            xx = px0 - int(rng.integers(0, 6))
            while xx < px1:
                bw = int(rng.integers(5, 10))
                a, b = max(px0, xx), min(px1, xx + bw)
                tone = wall[5] if rng.random() < 0.6 else wall[6]
                if b > a:
                    cv.rect(a, cy, b - a, 3, tone); cv.hline(a, cy + 2, b - a, wall[3]); cv.px(b - 1, cy, wall[7])
                xx += bw
        cv.vline(px0, top, base - top, wall[2]); cv.vline(px1 - 1, top, base - top, wall[7])
        # quoins on both corners
        for qy in range(top, base, 6):
            cv.rect(px0, qy, 3, 3, LIMESTONE[3]); cv.rect(px1 - 3, qy + 3, 3, 3, LIMESTONE[4])
        # tall arched windows and an oculus in the gable
        for wx in (cx - 12, cx - 2, cx + 8):
            cv.rect(wx, top + 6, 4, 14, "#2a1e2a"); cv.px(wx + 1, top + 5, "#2a1e2a"); cv.px(wx + 2, top + 5, "#2a1e2a")
            cv.rect(wx, top + 6, 2, 6, "#f4cc84" if wx > cx else "#5a4448")
            cv.hline(wx - 1, top + 20, 6, LIMESTONE[4])
        cv.poly([(px0 - 3, top), (cx, top - 14), (px1 + 2, top)], MROOF[3])
        cv.poly([(cx, top - 14), (px1 + 2, top), (cx, top)], MROOF[4])
        cv.line(px0 - 3, top, cx, top - 14, MROOF[2]); cv.line(cx, top - 14, px1 + 2, top, MROOF[5])
        cv.hline(px0 - 3, top, pw + 6, MROOF[1])
        cv.poly([(px0 + 2, top), (cx, top - 10), (px1 - 3, top)], wall[5])
        cv.ellipse(cx - 3, top - 7, 6, 6, LIMESTONE[3]); cv.ellipse(cx - 2, top - 6, 4, 4, "#3a2a30")
        cv.px(cx, top - 5, "#f6d488")


def tree_crown(cv, cx, cy, r, hh, pal, rng, lit_side=1):
    """A small autumn crown made of 2px leaf clusters: dark body, mid clusters, the sun side
    (lit_side=1 is right) bright with a few gold tips."""
    cv.ellipse(cx - r, cy - hh // 2, r * 2, hh, pal[1])
    for _ in range(r * hh // 3):
        a = rng.uniform(0, 2 * np.pi)
        d = np.sqrt(rng.uniform(0, 1))
        px_, py_ = int(cx + np.cos(a) * d * (r - 2)), int(cy + np.sin(a) * d * (hh / 2 - 2))
        lit = (px_ - cx) * lit_side - (py_ - cy) * 0.6 > -1
        cv.rect(px_, py_, 2, 2, pal[3] if lit else pal[2])
        if lit and rng.random() < 0.4:
            cv.px(px_ + (1 if lit_side > 0 else 0), py_, pal[4])
    # dark underside
    for xx in range(cx - r + 2, cx + r - 2):
        yb = cy + hh // 2 - 1 - int(abs(xx - cx) * hh / (2.6 * r))
        cv.px(xx, yb, pal[0])


def crown_row(cv, x0, x1, base, seed=0, sizes=(9, 16), heights=(16, 28), skip=()):
    """A row of autumn crowns along the back of the courts (maples, ash, a few still green)."""
    rng = _rng(seed)
    x = x0
    while x < x1:
        if not any(a <= x <= b for a, b in skip):
            r = int(rng.integers(*sizes))
            hh = int(rng.integers(*heights))
            pal = AUTUMN[int(rng.choice([0, 0, 1, 1, 2, 3]))]
            tree_crown(cv, x, base - hh // 2, r, hh, pal, rng)
        x += int(rng.integers(10, 20))


def light_tower(cv, x, top, base, heads=4, lit=0.0):
    """A court light pole for the neighbouring courts: tapered steel pole, a crossarm with a bank
    of rectangular floodlights tilted at the courts, sun catching its right edge."""
    cv.rect(x - 1, top + 6, 3, base - top - 6, STEEL[1]); cv.vline(x + 1, top + 6, base - top - 6, STEEL[4])
    cv.vline(x - 1, top + 6, base - top - 6, STEEL[0])
    for ry in range(top + 20, base, 18):          # climbing rungs
        cv.hline(x - 2, ry, 2, STEEL[2])
    w = heads * 5 + 2
    ax = x - w // 2
    cv.rect(ax, top + 4, w, 2, STEEL[1]); cv.hline(ax, top + 4, w, STEEL[4])
    for k in range(heads):
        hx = ax + 1 + k * 5
        cv.rect(hx, top - 1, 4, 5, STEEL[0]); cv.hline(hx, top - 1, 4, STEEL[3])
        glass = mix("#8a8c98", "#fff0c4", lit)
        cv.rect(hx, top + 2, 4, 2, glass); cv.px(hx + 3, top + 2, STEEL[4])


def colorado_flag(frame, w=16, h=10):
    """The Colorado flag on its halyard, three frames of a slow ripple: blue-white-blue bands,
    the red C round a gold disc. Returns RGBA (h+3, w+2) with the hoist at x 0."""
    cv = Canvas(w + 2, h + 4)
    blue, white, red, gold = ["#1e3a7a", "#2c4e96"], ["#e8e4dc", "#fff8ee"], ["#b42a26", "#d8463a"], "#f2c03a"
    for x in range(w):
        t = x / (w - 1)
        dy = int(round(np.sin(t * 3.2 + frame * 2.1) * 1.2 * t))
        sh = np.cos(t * 3.2 + frame * 2.1) * t
        b, wh = blue[1 if sh > 0 else 0], white[1 if sh > 0 else 0]
        y0 = 1 + dy
        third = h // 3
        cv.vline(x + 1, y0, third, b); cv.vline(x + 1, y0 + third, h - 2 * third, wh); cv.vline(x + 1, y0 + h - third, third, b)
    # the C and the gold disc near the hoist (drawn on the rippled cloth)
    cx = 1 + w * 0.38
    for x in range(w):
        t = x / (w - 1)
        dy = int(round(np.sin(t * 3.2 + frame * 2.1) * 1.2 * t))
        for y in range(h):
            d = np.hypot(x + 1 - cx, y - (h - 1) / 2)
            if 1.6 < d <= 3.6 and not (x + 1 > cx + 1.2 and abs(y - (h - 1) / 2) < 1.6):
                cv.px(x + 1, y + 1 + dy, red[1 if d < 2.8 else 0])
            elif d <= 1.6:
                cv.px(x + 1, y + 1 + dy, gold)
    cv.vline(0, 0, h + 4, "#c8ccd0")
    return cv.a


# ============================================================================================
# the back fence
# ============================================================================================
def chain_link(cv, x0, x1, y0, y1, pitch=6, alpha=0.55, lit=None):
    """Black vinyl-coated chain-link over whatever is behind it: a diamond lattice of 1px wires
    (one diagonal family a shade lighter where it catches the sun), knuckled twists at the top."""
    dark = C(FENCE[1], alpha)
    light = C(FENCE[3], alpha)
    for y in range(y0, y1):
        for x in range(x0, x1):
            a = (x + y) % pitch == 0
            b = (x - y) % pitch == 0
            if a and b:
                cv.px(x, y, C(FENCE[0], min(1.0, alpha + 0.25)))
            elif a:
                cv.px(x, y, dark)
            elif b:
                cv.px(x, y, light if lit is None else C(lit, alpha))
    for x in range(x0, x1, pitch):                  # twisted selvage along the top rail
        cv.px(x, y0 - 1, FENCE[0]); cv.px(x + 1, y0 - 2, FENCE[2])


def windscreen(cv, x0, x1, top, bottom, posts, seed=0, sun_x=640, vents=(), gaps=()):
    """Dark green windscreen fabric on the court side of the fence. The sun is behind it, so the
    court face sits in shade, but the open-knit fabric glows where the light comes through and
    goes dark where the trees behind shade it (big soft-edged patches in four flat steps), knit
    rows, a bound hem with grommets and white ties, soft V folds under each tie, doubled seams at
    the posts. vents: [(x, y)] U-shaped wind flaps with the sunny world showing through. gaps:
    posts where the two panels do not quite meet and a sliver of sun shows."""
    rng = _rng(seed)
    W, H = x1 - x0, bottom - top
    ws = P(WINDSCREEN)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    field = np.zeros((H, W), np.float32)
    for _ in range(int(W / 22)):
        bx, by = rng.uniform(0, W), rng.uniform(-10, H + 10)
        rx, ry = rng.uniform(16, 46), rng.uniform(12, 26)
        sign = 1.0 if rng.random() < 0.6 else -0.8
        field += np.clip(1 - ((xs - bx) / rx) ** 2 - ((ys - by) / ry) ** 2, 0, 1) ** 0.7 * sign
    field += np.clip((xs + x0 - (sun_x - 300)) / 300, 0, 1) * 1.1        # brighter toward the sun
    field -= (ys / H) * 0.5                                                # lower panel sits in the court's shade
    k = np.clip(np.floor(field * 1.5).astype(int) + 3, 1, 6)
    rgb = ws[k]
    rgb[(ys.astype(int) % 3) == 2] *= 0.92                                 # knit rows
    cv.a[top:bottom, x0:x1, :3] = rgb
    cv.a[top:bottom, x0:x1, 3] = 1
    # V folds under each tie, a shallow sag highlight between ties
    ties = list(range(x0 + 3, x1, 10))
    for tx in ties:
        for d in range(1, 6):
            cv.px(tx - d, top + 3 + d // 2, C(WINDSCREEN[0], 0.7)); cv.px(tx + d, top + 3 + d // 2, C(WINDSCREEN[0], 0.7))
        cv.px(tx, top + 3, WINDSCREEN[6])
    for i in range(len(ties) - 1):
        a, b = ties[i] + 3, ties[i + 1] - 3
        for x in range(a, b):
            t = (x - a) / max(1, b - a)
            cv.px(x, top + 6 + int(round(1.5 * np.sin(np.pi * t))), C(WINDSCREEN[7], 0.45))
    # hems: bound edges top and bottom, grommets with white zip ties to the mesh
    cv.rect(x0, top, W, 3, WINDSCREEN[1]); cv.hline(x0, top, W, WINDSCREEN[5])
    cv.rect(x0, bottom - 3, W, 3, WINDSCREEN[1]); cv.hline(x0, bottom - 3, W, WINDSCREEN[3])
    for tx in ties:
        cv.px(tx, top + 1, "#9a968a"); cv.px(tx, top - 1, "#f2f0e8"); cv.px(tx, top, "#d8d4c8")
        cv.px(tx, bottom - 2, "#6a6a60")
    # seams at the posts: doubled stitch lines
    for px_ in posts:
        cv.vline(px_ - 3, top + 3, H - 6, WINDSCREEN[0]); cv.vline(px_ + 3, top + 3, H - 6, WINDSCREEN[0])
        for y in range(top + 4, bottom - 4, 3):
            cv.px(px_ - 4, y, WINDSCREEN[4]); cv.px(px_ + 4, y, WINDSCREEN[4])
    for px_ in gaps:                       # a sliver of sun between two panels
        cv.vline(px_ + 3, top + 4, H - 8, "#b8a860"); cv.vline(px_ + 3, top + 10, H - 22, "#e0cc80")
    # wind vents: a U-shaped cut, the sunny world seen through it, the flap folded in below
    for (vx, vy) in vents:
        hole = [(0, 0, 7, "#8a8a4c"), (1, 1, 5, "#6e7442"), (2, 2, 3, "#566038")]
        for (dx, dy, w, c) in hole:
            cv.hline(vx + dx, vy + dy, w, c)
        cv.hline(vx + 1, vy, 3, "#b4a45e")
        cv.hline(vx, vy - 1, 7, WINDSCREEN[0])
        cv.px(vx - 1, vy, WINDSCREEN[0]); cv.px(vx + 7, vy, WINDSCREEN[0])
        cv.hline(vx + 1, vy + 3, 5, WS_LIT[1]); cv.hline(vx + 2, vy + 4, 3, WS_LIT[0]); cv.hline(vx + 2, vy + 5, 3, WINDSCREEN[1])


def draped_gown(cv, x, top):
    """A black graduation gown hung over the top of the windscreen to play in shirtsleeves: the
    yoke over the edge, body and one bell sleeve hanging down the court side, a CU gold stole."""
    g = ["#0c0a10", "#16141c", "#201e28", "#2c2a36", "#3c3a48"]
    cv.poly([(x, top - 3), (x + 30, top - 4), (x + 31, top + 1), (x - 1, top + 1)], g[2])
    cv.hline(x, top - 4, 30, g[4]); cv.px(x + 29, top - 4, "#d8b878")
    cv.poly([(x + 2, top + 1), (x + 28, top + 1), (x + 30, top + 26), (x + 21, top + 23), (x + 13, top + 27), (x + 4, top + 24), (x, top + 26)], g[1])
    for fx in (x + 7, x + 13, x + 19, x + 25):
        cv.line(fx, top + 3, fx + (1 if fx > x + 15 else -1), top + 24, g[0])
        cv.line(fx + 1, top + 3, fx + 2, top + 20, g[3])
    cv.poly([(x + 22, top + 2), (x + 33, top + 6), (x + 34, top + 20), (x + 28, top + 17)], g[2])     # sleeve
    cv.line(x + 33, top + 6, x + 34, top + 20, "#8a7a5a")
    cv.rect(x + 9, top - 3, 3, 26, CU_GOLD[3]); cv.vline(x + 9, top - 3, 26, CU_GOLD[4]); cv.vline(x + 11, top - 3, 26, CU_GOLD[1])
    cv.rect(x + 9, top + 23, 3, 2, CU_GOLD[2])


def court_sign(cv, cx, y, label, scale=2, fg="#f4f0e4", bg=BLUE_SIGN, pad=6):
    """An enamelled court sign zip-tied to the windscreen: blue plate, white border and lettering,
    two white ties at the top corners, the plate's own shadow below."""
    tw = text_width(label) * scale
    w = tw + pad * 2
    h = 8 * scale + 6
    x = cx - w // 2
    cv.rect(x + 1, y + h, w, 2, C("#0a1210", 0.45)); cv.rect(x + w, y + 2, 2, h - 1, C("#0a1210", 0.35))
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, bg[2]); cv.rect(x + 1, y + 1, w - 2, h - 2, bg[1])
    cv.rect(x + 2, y + 2, w - 4, h - 4, fg); cv.rect(x + 3, y + 3, w - 6, h - 6, bg[2])
    cv.hline(x + 3, y + 3, w - 6, bg[3])
    if scale == 1:
        text(cv, label, x + pad, y + 4, fg)
    else:
        big_text(cv, label, x + pad, y + 4, fg)
    for tx in (x + 3, x + w - 4):
        cv.rect(tx, y - 3, 1, 4, "#f2f0e8"); cv.px(tx, y - 3, "#c8c4b8")
    return x, y, w, h


def small_sign(cv, cx, y, label, fg="#b42a26", bg=("#c8c2b0", "#eeeadc")):
    """A small white aluminium notice (red or black letters), screwed on with two rivets."""
    tw = text_width(label)
    w, h = tw + 8, 12
    x = cx - w // 2
    cv.rect(x + 1, y + h, w, 1, C("#0a1210", 0.45))
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, bg[1]); cv.hline(x, y + h - 1, w, bg[0]); cv.vline(x + w - 1, y, h, bg[0])
    text(cv, label, x + 4, y + 2, fg)
    cv.px(x + 1, y + 1, "#8a867a"); cv.px(x + w - 2, y + 1, "#8a867a")
    return x, y, w, h


def flip_score(cv, x, y, left="0", right="0"):
    """A flip scorecard zip-tied to the windscreen: green frame, two white flip cards on rings
    (love-all: nobody is keeping score, officially), a spare card hanging behind each."""
    w, h = 30, 20
    cv.rect(x + 1, y + h, w, 2, C("#0a1210", 0.45))
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, "#1e3a2c"); cv.hline(x, y, w, "#3a6248"); cv.hline(x, y + h - 1, w, "#12261c")
    for (cx_, label) in ((x + 3, left), (x + 17, right)):
        cv.rect(cx_ + 1, y + 4, 10, 13, "#a8a49a")                       # the spare cards behind
        cv.rect(cx_, y + 3, 10, 13, "#f4f0e4"); cv.hline(cx_, y + 15, 10, "#c8c4b4"); cv.vline(cx_ + 9, y + 3, 13, "#d8d4c4")
        text(cv, label, cx_ + 3, y + 5, "#1a1e2a")
        for rx in (cx_ + 2, cx_ + 7):
            cv.rect(rx, y + 1, 1, 3, "#c8ccd0"); cv.px(rx, y + 1, "#f2f4f6")
    cv.rect(x + 14, y + 8, 2, 2, "#f4f0e4")                            # the dash between
    for tx in (x + 2, x + w - 3):
        cv.rect(tx, y - 3, 1, 3, "#f2f0e8")


def fence_post(cv, x, top, bottom):
    """A black line post with a dome cap and the sun on its right edge."""
    cv.rect(x - 1, top, 3, bottom - top, FENCE[1]); cv.vline(x - 1, top, bottom - top, FENCE[0])
    cv.vline(x + 1, top, bottom - top, FENCE[4])
    cv.rect(x - 2, top - 2, 5, 2, FENCE[2]); cv.hline(x - 1, top - 3, 3, FENCE[3]); cv.px(x + 1, top - 2, "#c8a870")
    for by in (top + 6, top + 22, bottom - 18):    # tension bands
        cv.hline(x - 2, by, 5, FENCE[3]); cv.px(x + 2, by, FENCE[4])


# ============================================================================================
# small floor things
# ============================================================================================
def tennis_ball(cv, x, y, shadow=True, lit=True):
    """A 4x3 tennis ball lying on the court: optic yellow, a curved seam, a sunlit top-right, and
    a short shadow pointing away from the sun."""
    if shadow:
        cv.hline(x - 5, y + 2, 6, C("#0e1a20", 0.35)); cv.hline(x - 3, y + 1, 3, C("#0e1a20", 0.25))
    cv.rect(x, y - 1, 4, 3, BALL[2] if lit else BALL[1]); cv.hline(x + 1, y - 2, 2, BALL[3] if lit else BALL[2])
    cv.px(x, y + 1, BALL[1] if lit else BALL[0]); cv.px(x + 3, y + 1, BALL[1] if lit else BALL[0])
    cv.px(x + 2, y - 2, BALL[4] if lit else BALL[2]); cv.px(x + 3, y - 1, BALL[3] if lit else BALL[2])
    cv.px(x + 1, y, "#f2f4dc" if lit else BALL[3])   # seam


def mortarboard_flat(cv, x, y):
    """A mortarboard someone tossed down: black square board seen from above at a tilt (a
    flattened diamond), the cap's skull showing below one edge, a gold tassel trailing on the
    court, its long shadow to the left."""
    cv.poly([(x - 18, y + 1), (x - 3, y - 3), (x + 4, y + 2), (x - 11, y + 6)], C("#0e1a20", 0.4))
    cv.poly([(x - 8, y + 2), (x + 3, y - 4), (x + 11, y), (x, y + 6)], OUT)
    cv.poly([(x - 6, y + 2), (x + 3, y - 3), (x + 9, y), (x, y + 5)], CU_BLACK[2])
    cv.line(x + 3, y - 3, x + 9, y, CU_BLACK[3]); cv.line(x - 6, y + 2, x + 3, y - 3, "#4a4a58")
    cv.line(x + 4, y - 2, x + 8, y, "#d8b880")          # sun on the far edge
    cv.rect(x - 2, y + 5, 6, 2, CU_BLACK[1]); cv.hline(x - 1, y + 7, 4, OUT)
    cv.px(x + 2, y + 1, CU_GOLD[4])                   # button
    cv.line(x + 2, y + 1, x + 9, y + 4, CU_GOLD[3])     # cord
    for k, (dx, dy) in enumerate([(9, 4), (10, 5), (11, 5), (12, 6), (13, 6)]):
        cv.px(x + dx, y + dy, CU_GOLD[4] if k % 2 else CU_GOLD[2])
    cv.px(x + 14, y + 6, CU_GOLD[1]); cv.px(x + 13, y + 7, CU_GOLD[2])
    cv.px(x + 9, y + 3, CU_GOLD[4])


def programme_flat(cv, x, y):
    """A commencement programme dropped face up on the court: cream card, a gold seal, two
    lines of black type, one corner curling up and its little shadow."""
    cv.poly([(x - 1, y + 7), (x + 13, y + 5), (x + 14, y + 9), (x, y + 11)], C("#0e1a20", 0.35))
    cv.poly([(x, y + 1), (x + 13, y - 1), (x + 14, y + 7), (x + 1, y + 9)], "#e8e0c8")
    cv.line(x, y + 1, x + 13, y - 1, "#fff8e6"); cv.line(x + 1, y + 9, x + 14, y + 7, "#b8ae96")
    cv.px(x + 3, y + 3, CU_GOLD[3]); cv.px(x + 4, y + 3, CU_GOLD[4]); cv.px(x + 3, y + 4, CU_GOLD[2])
    cv.hline(x + 6, y + 3, 6, "#4a4650"); cv.hline(x + 5, y + 5, 7, "#7a7680"); cv.hline(x + 6, y + 7, 4, "#7a7680")
    cv.px(x + 13, y - 1, "#c8c0a8"); cv.px(x + 12, y - 2, "#fff8e6")


def leaf_litter(cv, cx, cy, rx, ry, n, rng, mask=None, dim=None):
    """Fallen leaves: 2px leaves with a lit pixel, clustered round a point."""
    for _ in range(n):
        a = rng.uniform(0, 2 * np.pi); d = abs(rng.normal(0, 0.5))
        lx, ly = int(cx + np.cos(a) * d * rx), int(cy + np.sin(a) * d * ry)
        if not (0 <= lx < cv.w - 1 and 0 <= ly < cv.h - 1):
            continue
        if mask is not None and not mask[ly, lx]:
            continue
        c = LEAVES[int(rng.integers(len(LEAVES)))]
        if dim is not None and dim[ly, lx]:
            c = shade(c, -0.3)
        cv.px(lx, ly, c); cv.px(lx + 1, ly, shade(c, -0.2))
        if rng.random() < 0.3:
            cv.px(lx, ly - 1, shade(c, 0.15))


# ============================================================================================
# props
# ============================================================================================
def outline(cv):
    cv.outline_outside(OUT)
    return cv


def tennis_net(width=300, height=26):
    """The net across the middle of the court: two round dark-green posts (a winder handle on
    the right one), the black square mesh (see-through, the court and anyone behind it show), the
    white headband sagging a little to the centre strap, the bottom cable. Anchor bottom-centre."""
    W, H = width + 4, height + 2
    cv = Canvas(W, H)
    base = H - 1
    pl, pr = 2, W - 3                         # post centre lines
    top_post = base - height + 1
    cx = W // 2
    sag = 4

    def tape_y(x):
        t = abs(x - cx) / (pr - cx)
        return int(round(top_post + 3 + sag * (1 - t ** 1.6)))
    # mesh: dark cords on a 3px grid, holes faintly dark (so the court shows through)
    for x in range(pl + 3, pr - 2):
        ty = tape_y(x)
        for y in range(ty + 2, base - 1):
            if (x % 3 == 0) and ((y - ty) % 3 == 0):
                cv.px(x, y, C("#0e1014", 0.95))
            elif (x % 3 == 0) or ((y - ty) % 3 == 0):
                cv.px(x, y, C("#14161c", 0.72))
            else:
                cv.px(x, y, C("#14161c", 0.1))
        # bottom: the net hangs onto the cable, a doubled dark band
        cv.px(x, base - 1, C("#1a1c22", 0.95)); cv.px(x, base - 2, C("#20242a", 0.8))
    # side bands where the net laces to the posts
    for x0 in (pl + 2, pr - 3):
        for y in range(tape_y(x0), base):
            cv.px(x0, y, "#2a2e34")
    # headband: white tape, top lit, underside shadowed
    for x in range(pl + 2, pr - 1):
        ty = tape_y(x)
        cv.px(x, ty, "#f6f2e4"); cv.px(x, ty + 1, "#d8d4c4")
        cv.px(x, ty + 2, C("#8a8a86", 0.9))
    # centre strap
    sy = tape_y(cx)
    cv.rect(cx - 1, sy, 3, base - sy, "#e6e2d4"); cv.vline(cx + 1, sy, base - sy, "#b8b4a4"); cv.vline(cx - 1, sy, base - sy, "#f6f2e4")
    cv.rect(cx - 2, base - 2, 5, 2, "#5a5e66")
    # posts: dark green round posts, sun on the right
    for p in (pl, pr):
        cv.rect(p - 2, top_post, 5, base - top_post + 1, "#1c3a2c"); cv.vline(p - 2, top_post, base - top_post + 1, "#10241c")
        cv.vline(p + 1, top_post, base - top_post + 1, "#4a6e4e"); cv.vline(p + 2, top_post, base - top_post + 1, "#2a4a38")
        cv.rect(p - 2, top_post - 1, 5, 2, "#2a4a38"); cv.hline(p - 1, top_post - 1, 3, "#6a8a62")
        cv.px(p + 1, top_post - 1, "#e8c87a")
        cv.rect(p - 3, base - 1, 7, 2, "#3a3e46")
        cv.vline(p - 3, top_post - 1, base - top_post, OUT); cv.vline(p + 3, top_post - 1, base - top_post, OUT)
        cv.hline(p - 2, top_post - 2, 5, OUT)
    # winder on the right post: a crank box and handle
    cv.rect(pr - 4, top_post + 8, 3, 5, "#2a2e36"); cv.px(pr - 4, top_post + 8, "#5a606c")
    cv.line(pr - 5, top_post + 10, pr - 7, top_post + 13, "#9ca0a8"); cv.px(pr - 7, top_post + 14, "#2a2e36")
    return cv, W // 2, base


def ball_machine(width=34, height=40):
    """Ball machine on its two wheels: a charcoal body with an orange stripe, a wide open hopper
    heaped with balls, the launch throat facing the court, a pull handle, a power LED, and the
    control panel whose dial reads LOB / TOPSPIN / MERCY (MERCY taped over with silver tape)."""
    W, H = width + 4, height + 3
    cv = Canvas(W, H)
    base = H - 2
    x0 = 2
    # handle (behind, right)
    cv.line(x0 + 28, base - 18, x0 + 33, base - 34, MACHINE[3]); cv.line(x0 + 29, base - 18, x0 + 34, base - 34, MACHINE[1])
    cv.rect(x0 + 31, base - 37, 4, 3, "#2a2a2a"); cv.px(x0 + 34, base - 37, "#6a6a6a")
    # body
    bt = base - 22
    cv.rect(x0 + 2, bt, 26, 17, MACHINE[2]); cv.vline(x0 + 2, bt, 17, MACHINE[1]); cv.vline(x0 + 27, bt, 17, MACHINE[4])
    cv.hline(x0 + 2, bt, 26, MACHINE[4]); cv.hline(x0 + 2, bt + 16, 26, MACHINE[0])
    cv.rect(x0 + 2, bt + 11, 26, 2, ORANGE[2]); cv.hline(x0 + 2, bt + 11, 26, ORANGE[3]); cv.px(x0 + 27, bt + 11, "#ffd090")
    # control panel with the dial: three ticks (green LOB, amber TOPSPIN, red MERCY under tape)
    cv.rect(x0 + 14, bt + 2, 11, 8, "#c8c4b4"); cv.hline(x0 + 14, bt + 2, 11, "#e8e4d4"); cv.vline(x0 + 24, bt + 2, 8, "#9a9686")
    cv.rect(x0 + 15, bt + 4, 5, 5, "#2a2e36"); cv.rect(x0 + 16, bt + 5, 3, 3, "#5a606c"); cv.px(x0 + 17, bt + 6, "#e8e4d4")
    cv.px(x0 + 16, bt + 3, "#3cba5a"); cv.px(x0 + 18, bt + 3, "#e8a034")
    # silver tape across MERCY (the right of the dial), a little crooked
    cv.rect(x0 + 19, bt + 2, 5, 3, "#d8dce0"); cv.px(x0 + 23, bt + 2, "#a8acb4"); cv.hline(x0 + 19, bt + 4, 5, "#a8acb4")
    cv.px(x0 + 20, bt + 3, "#c84a3a")                  # a red corner still peeking out
    cv.rect(x0 + 21, bt + 6, 3, 2, "#2a2e36"); cv.px(x0 + 22, bt + 6, "#3cfa6a")   # power LED
    # launch throat on the left face (aimed at the court)
    cv.ellipse(x0 + 3, bt + 3, 9, 8, MACHINE[0]); cv.ellipse(x0 + 4, bt + 4, 7, 6, "#08080c")
    cv.px(x0 + 9, bt + 4, MACHINE[5]); cv.px(x0 + 5, bt + 5, BALL[1])
    # hopper: open wire basket wider than the body, heaped with balls
    ht = bt - 14
    cv.poly([(x0, ht + 4), (x0 + 30, ht + 4), (x0 + 27, bt), (x0 + 3, bt)], C(MACHINE[1], 1.0))
    for hx in range(x0 + 2, x0 + 29, 3):
        cv.line(hx, ht + 5, hx + (1 if hx < x0 + 15 else -1), bt - 1, MACHINE[3])
    cv.hline(x0, ht + 4, 31, STEEL[4]); cv.hline(x0 + 3, bt - 1, 25, MACHINE[3])
    rng = _rng(5)
    balls = []
    for row, (y, n, off) in enumerate([(ht + 1, 6, 3), (ht + 4, 7, 1), (ht - 2, 4, 7)]):
        for k in range(n):
            balls.append((x0 + off + k * 4 + int(rng.integers(0, 2)), y + int(rng.integers(0, 2))))
    for bx, by in sorted(balls, key=lambda b: b[1]):
        cv.rect(bx, by, 4, 3, BALL[2]); cv.hline(bx + 1, by - 1, 2, BALL[3])
        cv.px(bx, by + 2, BALL[1]); cv.px(bx + 3, by + 2, BALL[1]); cv.px(bx + 2, by - 1, BALL[4])
        cv.px(bx + 1, by + 1, "#f2f4dc")
    for bx, by in [(x0 + 4, ht + 7), (x0 + 12, ht + 8), (x0 + 21, ht + 7)]:    # balls seen through the wire
        cv.rect(bx, by, 3, 2, BALL[1])
    # wheels and the front foot
    for wx in (x0 + 8, x0 + 22):
        cv.ellipse(wx - 4, base - 8, 9, 9, "#16161a"); cv.ellipse(wx - 2, base - 6, 5, 5, "#4a4e58")
        cv.px(wx, base - 4, "#9ca0a8"); cv.px(wx + 2, base - 7, "#5a5e66")
    cv.rect(x0 + 13, base - 4, 4, 4, MACHINE[1]); cv.hline(x0 + 13, base - 1, 4, "#0e0e12")
    outline(cv)
    return cv, W // 2, base


def court_bench(width=110, height=30):
    """Courtside bench, green-painted steel slats on black frame ends: a white towel with a CU
    gold stripe over the backrest, a steel water bottle, a can of balls, and a graduation cap
    someone already took off (gold tassel hanging over the front edge)."""
    W, H = width + 4, height + 4
    cv = Canvas(W, H)
    base = H - 2
    x0, x1 = 2, W - 2
    green = ["#12261c", "#1a3424", "#22442e", "#2c5438", "#3a6644", "#527a54", "#c8b070"]
    # frame ends (behind) and the backrest slats
    bk_top = base - height + 1
    for fx in (x0 + 6, x1 - 8):
        cv.rect(fx, bk_top, 3, height - 1, FENCE[1]); cv.vline(fx + 2, bk_top, height - 1, FENCE[4])
    for k, sy in enumerate((bk_top + 2, bk_top + 6)):
        cv.rect(x0 + 2, sy, x1 - x0 - 4, 3, green[3]); cv.hline(x0 + 2, sy, x1 - x0 - 4, green[5])
        cv.hline(x0 + 2, sy + 2, x1 - x0 - 4, green[1])
        cv.px(x1 - 3, sy, green[6]); cv.px(x1 - 3, sy + 1, green[5])       # sun at the right end
    # seat: three slats seen from above, front lip
    seat = base - 12
    for k, sy in enumerate((seat - 5, seat - 3, seat - 1)):
        cv.rect(x0, sy, x1 - x0, 2, green[3] if k != 1 else green[4]); cv.hline(x0, sy, x1 - x0, green[5] if k == 0 else green[4])
    cv.rect(x0, seat + 1, x1 - x0, 2, green[2]); cv.hline(x0, seat + 2, x1 - x0, green[1])
    cv.px(x1 - 1, seat - 5, green[6]); cv.px(x1 - 1, seat - 3, green[6])
    # legs: black steel, splayed feet
    for fx in (x0 + 6, x1 - 8):
        cv.rect(fx, seat + 3, 3, base - seat - 3, FENCE[1]); cv.vline(fx + 2, seat + 3, base - seat - 3, FENCE[4])
        cv.rect(fx - 2, base - 1, 7, 2, FENCE[0])
    # the towel over the backrest: a fold over the top rail, the front hanging down unevenly with
    # soft vertical folds, a CU gold stripe near the hem, the sun on its right edge
    tx = x0 + 16
    tw = 22
    cv.rect(tx - 1, bk_top - 1, tw + 2, 4, OUT)
    cv.rect(tx, bk_top, tw, 3, TOWEL[3]); cv.hline(tx, bk_top + 2, tw, TOWEL[2])
    hem = [seat - 4 - (1 if (i // 5) % 2 else 0) - (2 if i > tw - 7 else 0) for i in range(tw)]
    for i in range(tw):
        x = tx + i
        cv.vline(x, bk_top + 3, hem[i] - bk_top - 3, TOWEL[2])
        cv.px(x, hem[i], OUT)
    for fx in (tx + 5, tx + 11, tx + 16):            # folds: a shadow line with a lit line beside it
        cv.vline(fx, bk_top + 3, hem[fx - tx] - bk_top - 4, TOWEL[1]); cv.vline(fx + 1, bk_top + 4, hem[fx - tx] - bk_top - 6, TOWEL[3])
    cv.vline(tx + tw - 1, bk_top, hem[-1] - bk_top, "#fff8e0")
    cv.vline(tx, bk_top, hem[0] - bk_top, TOWEL[0])
    for i in range(tw):
        cv.px(tx + i, hem[i] - 3, CU_GOLD[3]); cv.px(tx + i, hem[i] - 2, CU_GOLD[2])
    # steel water bottle standing on the seat
    bx = x0 + 52
    cv.rect(bx, seat - 15, 5, 12, STEEL[3]); cv.vline(bx, seat - 15, 12, STEEL[1]); cv.vline(bx + 4, seat - 15, 12, STEEL[5])
    cv.rect(bx + 1, seat - 17, 3, 2, "#2a5a8a"); cv.px(bx + 3, seat - 17, "#5a8ac0")
    cv.rect(bx, seat - 10, 5, 3, "#2a5a8a"); cv.px(bx + 4, seat - 10, "#5a8ac0")
    # a can of balls lying on its side
    cx_ = x0 + 62
    cv.rect(cx_, seat - 6, 9, 4, "#c8ccd0"); cv.hline(cx_, seat - 6, 9, "#eef0f0"); cv.rect(cx_, seat - 6, 2, 4, "#e0702e")
    cv.rect(cx_ + 3, seat - 5, 4, 2, BALL[2])
    # the graduation cap on the seat: board seen at an angle, skull cap, gold tassel over the edge
    gx = x0 + 80
    cv.rect(gx + 2, seat - 6, 10, 4, CU_BLACK[1]); cv.hline(gx + 2, seat - 3, 10, OUT)
    cv.poly([(gx - 2, seat - 7), (gx + 7, seat - 11), (gx + 17, seat - 8), (gx + 8, seat - 4)], CU_BLACK[2])
    cv.line(gx + 7, seat - 11, gx + 17, seat - 8, "#d8b880"); cv.line(gx - 2, seat - 7, gx + 7, seat - 11, CU_BLACK[3])
    cv.px(gx + 7, seat - 8, CU_GOLD[4])
    cv.line(gx + 7, seat - 8, gx + 14, seat - 5, CU_GOLD[3])
    cv.vline(gx + 14, seat - 5, 7, CU_GOLD[3]); cv.vline(gx + 15, seat - 4, 6, CU_GOLD[2]); cv.px(gx + 14, seat + 2, CU_GOLD[4])
    outline(cv)
    return cv, W // 2, base


def ball_hopper(width=18, height=26):
    """A wire ball hopper standing on its fold-down handles: chrome wire basket, balls heaped
    over the top and showing between the wires, the handle legs splayed to the floor."""
    W, H = width + 4, height + 3
    cv = Canvas(W, H)
    base = H - 2
    x0 = 2
    bt, bb = base - height + 6, base - 9           # basket top and bottom
    # legs (the handles folded down), behind the basket
    for (a, b) in [((x0 + 2, bb), (x0, base)), ((x0 + width - 3, bb), (x0 + width - 1, base))]:
        cv.line(a[0], a[1], b[0], b[1], STEEL[4]); cv.line(a[0] + 1, a[1], b[0] + 1, b[1], STEEL[2])
    cv.hline(x0 - 1, base, 3, STEEL[1]); cv.hline(x0 + width - 2, base, 3, STEEL[1])
    # inside: balls behind the wires
    cv.rect(x0 + 1, bt, width - 2, bb - bt, "#2a2e22")
    rng = _rng(7)
    for by in range(bt + 1, bb - 1, 3):
        for bx in range(x0 + 1 + (by // 3) % 2, x0 + width - 3, 4):
            cv.rect(bx, by, 3, 2, BALL[1 + int(rng.integers(0, 2))]); cv.px(bx + 1, by, BALL[3])
    # wires: verticals and three rings, sun on the right
    for wx in range(x0 + 1, x0 + width, 3):
        cv.vline(wx, bt, bb - bt, STEEL[3] if wx < x0 + width - 4 else STEEL[5])
    for ry in (bt, bt + (bb - bt) // 2, bb):
        cv.hline(x0, ry, width, STEEL[4]); cv.px(x0 + width - 1, ry, STEEL[5])
    # heap on top
    for k, (bx, by) in enumerate([(x0 + 1, bt - 3), (x0 + 5, bt - 4), (x0 + 9, bt - 3), (x0 + 13, bt - 3), (x0 + 3, bt - 6), (x0 + 8, bt - 7), (x0 + 11, bt - 6)]):
        cv.rect(bx, by, 4, 3, BALL[2]); cv.hline(bx + 1, by - 1, 2, BALL[3]); cv.px(bx + 2, by - 1, BALL[4])
        cv.px(bx, by + 2, BALL[1]); cv.px(bx + 3, by + 2, BALL[1]); cv.px(bx + 1 + k % 2, by + 1, "#f2f4dc")
    outline(cv)
    return cv, W // 2, base


def court_light(height=80, lit=0.45):
    """The court's own light post at the right: galvanised pole on a concrete footing with an
    access hatch and a conduit box, a crossarm carrying two flat LED floods tilted down at the
    court, their glass just warming up. The lamp core sits ~5px below the top."""
    W = 28
    cv = Canvas(W, height + 4)
    cx, base = W // 2, height + 2
    top = base - height
    # footing and the pole (sun on its right)
    cv.rect(cx - 6, base - 5, 12, 5, "#8a8478"); cv.hline(cx - 6, base - 5, 12, "#b4ac9c"); cv.vline(cx + 5, base - 5, 5, "#5e5a52")
    cv.rect(cx - 2, top + 10, 5, base - top - 15, STEEL[2])
    cv.vline(cx - 2, top + 10, base - top - 15, STEEL[1]); cv.vline(cx + 1, top + 10, base - top - 15, STEEL[4])
    cv.vline(cx + 2, top + 10, base - top - 15, STEEL[5])
    cv.rect(cx - 1, base - 24, 3, 7, STEEL[3]); cv.rect(cx, base - 23, 1, 5, STEEL[0])          # access hatch
    cv.rect(cx + 3, base - 34, 5, 7, "#4a4e58"); cv.hline(cx + 3, base - 34, 5, "#8a909a"); cv.vline(cx + 7, base - 34, 7, "#6a707a")
    cv.vline(cx + 5, base - 27, 21, "#3a3e46")                                                   # conduit
    for by in (top + 26, top + 48):                                                              # pole bands
        cv.hline(cx - 2, by, 5, STEEL[3]); cv.px(cx + 2, by, STEEL[5])
    # crossarm and two floods tilted at the court: dark housings, warm glass on their undersides
    cv.rect(cx - 12, top + 7, 25, 2, STEEL[1]); cv.hline(cx - 12, top + 7, 25, STEEL[4])
    cv.rect(cx - 1, top + 3, 3, 5, STEEL[2])
    glass = (mix("#7a7c88", "#e9a84a", lit), mix("#9a9ca8", "#f6cf7a", lit), mix("#b8bac4", "#fff0c4", lit))
    for hx in (cx - 13, cx + 2):
        cv.poly([(hx, top + 1), (hx + 10, top), (hx + 11, top + 4), (hx + 1, top + 6)], STEEL[0])
        cv.line(hx, top + 1, hx + 10, top, STEEL[4]); cv.px(hx + 10, top, "#e8c87a")
        cv.poly([(hx + 1, top + 4), (hx + 10, top + 3), (hx + 10, top + 5), (hx + 1, top + 7)], glass[0])
        cv.hline(hx + 3, top + 5, 6, glass[1]); cv.hline(hx + 5, top + 5, 2, glass[2])
        for fx in range(hx + 2, hx + 10, 2):                                                      # cooling fins
            cv.px(fx, top + 1, STEEL[2])
    outline(cv)
    return cv, cx, base
