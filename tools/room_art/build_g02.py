"""Tennis courts (G02): one friendly set, late afternoon on graduation day.

Court 3 seen from the side, in the golden hour. The back fence runs across the top: black
chain-link over the view, a dark green windscreen (the sun is behind it) with wind flaps glowing,
the blue COURT 3 sign, two small notices and a pair of graduation balloons tied to the mesh. Beyond
the fence: the Flatirons catching the last gold, a CU sandstone hall with its red tile roof and a
Colorado flag, autumn crowns, the next courts' light towers, and the low sun over the oak on the
right. The floor is a blue-green hard court with white lines in a lighter sage surround: the
fence lays a long shadow band along the back, its posts and the net, bench, hopper, ball machine
and light post throw long shadows to the left. Flat things: tennis balls, leaves blown against
the fence, a discarded mortarboard, wear behind the baselines, skid marks, a sealed crack, and the
open exit gate at the left end of the back fence with a worn path down to the exit.
Props: the net (0), ball machine (1), bench with towel, bottle and cap (2), ball hopper (3), the
court light post (5). Threshold 4 is code.
Layers: the flag rippling (three frames), a ball dribbling out of the machine to the net post,
pollen in the sun, the machine's LED, leaves falling from the crowns, birds, a squirrel on the
fence rail."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from midlib import sprite_from_cell
from pixel import Canvas, C, mix, shade
from props import shrub
from lib_macky2 import _ridge, AUTUMN
import lib_tennis as T

ROOM = "G02"
W, H = 640, 360
FOOT = 176                     # fence foot = top of the floor
TOP_RAIL = 86                  # top rail of the back fence
WS = (124, 174)                # windscreen top / bottom
POSTS = [130 + 80 * k for k in range(7)]
GATE = (22, 72)                # the exit gate's two posts in the back fence (threshold 4 below it)
GATE_TOP = 116                 # its header bar
SUN = (606, 50)
CX = 330                       # court centre line (net centre)
DL, DR = 188, 472              # doubles sidelines (net posts stand just outside at 180 / 480)
SL, SR = 224, 436              # singles sidelines
FB, NB = 190, 334              # far / near baselines
FS, NS = 223, 301              # service lines
NET_Y = 262
CASTER_FOOT = 164             # floor line the trees and towers beyond the fence stand on              # the walk leaving at the left edge (threshold 4 at 46, 300)
BENCH, HOPPER, MACHINE, LAMP = (150, 212), (214, 214), (520, 214), (600, 186)
JAKERSON, ENTRY = (430, 320), (90, 296)
VENTS = [(96, 152), (140, 138), (252, 150), (432, 160), (512, 156), (566, 140), (624, 150)]
GAPS = [210, 450]               # posts where the windscreen panels leave a sliver of sun


# ---------------------------------------------------------------- the view beyond the fence
def paint_view(bg):
    T.golden_sky(bg, 0, 0, W, WS[0], SUN, seed=3)
    rng = T._rng(5)
    for (x, y, ln, th) in [(30, 30, 90, 3), (150, 18, 70, 2), (360, 26, 110, 3), (470, 44, 60, 2)]:
        T.gold_cloud(bg, x, y, ln, th, rng)
    T.sun_disc(bg, *SUN, r=8)
    # distant hills in the golden haze, all the way across
    xs, far = _ridge(0, W - 1, [(0, 92), (0.3, 96), (0.5, 88), (0.7, 84), (0.85, 90), (1.0, 86)], rng, 0.6)
    T.far_hills(bg, 0, far, WS[0], seed=7)
    # the Flatirons on the left, catching the last sun
    mtn, ridge = T.golden_flatirons(scale=1.75)
    bg.paste(mtn, -12, 6)
    # foothills under the hall on the right
    xs, foot = _ridge(290, W - 1, [(0, 6 + ridge[-1]), (0.25, 86), (1.0, 92)], rng, 0.5)
    T.far_hills(bg, 290, foot, WS[0], pal=["#5a4a52", "#6a5654", "#7a6458", "#8a7058", "#9a7c5c", "#b08e64"], seed=8)
    # the campus hall and its pavilion; flagpole on the pavilion
    T.campus_hall(bg, 352, 586, 88, WS[0], seed=11, pavilion=(472, 44, 10))
    bg.vline(486, 46, 32, "#c8ccd0"); bg.px(486, 45, "#f2d080")
    # light towers, trees: painted on their own layer, which also throws their shadows onto the
    # courts (their feet stand just behind the windscreen, at CASTER_FOOT)
    cast = Canvas(W, H)
    T.light_tower(cast, 150, 24, WS[0], heads=4)
    T.light_tower(cast, 424, 30, WS[0], heads=4)
    pine = sprite_from_cell(6, height=104, colors=30, brightness=0.95)
    cast.paste(pine, -26, WS[0] + 4 - pine.shape[0])
    oak = sprite_from_cell(5, height=92, colors=36, brightness=1.05, saturation=1.05)
    m = oak[..., 3] > 0.5
    rim = m & ~np.roll(m, -1, axis=1)
    oak[rim, :3] = np.clip(oak[rim, :3] * 1.25 + 0.06, 0, 1)        # sun on the right edge of each mass
    cast.paste(oak, 572, WS[0] + 6 - oak.shape[0])
    T.crown_row(cast, 20, 600, WS[0] + 6, seed=13, skip=[(470, 500)])
    T.crown_row(cast, 260, 340, WS[0] + 2, seed=14, sizes=(7, 11), heights=(12, 18))
    bg.paste(cast, 0, 0)
    return cast.a[..., 3] > 0.5


# ---------------------------------------------------------------- the back fence
def paint_fence(bg):
    T.chain_link(bg, 0, W, TOP_RAIL + 2, WS[0], alpha=0.5)
    # top rail
    bg.rect(0, TOP_RAIL, W, 2, T.FENCE[1]); bg.hline(0, TOP_RAIL, W, T.FENCE[3])
    for x in range(14, W, 40):
        bg.px(x, TOP_RAIL, "#d8b878")              # sun glinting along the rail
    T.windscreen(bg, 0, W, WS[0], WS[1], POSTS, seed=17, sun_x=SUN[0], vents=VENTS, gaps=GAPS)
    for px_ in POSTS:
        T.fence_post(bg, px_, TOP_RAIL - 1, FOOT)
    # bottom tension wire and the curb the fence stands on
    bg.rect(0, WS[1], W, 2, "#5e5a52"); bg.hline(0, WS[1], W, "#7a766a")
    paint_gate_opening(bg)
    # signs: COURT 3 in the middle, notices left and right
    T.court_sign(bg, CX, 132, "COURT 3")
    T.small_sign(bg, 170, 140, "CLOSE GATE")
    T.small_sign(bg, 476, 140, "NO GLASS", fg="#1a1e2a")
    T.flip_score(bg, 396, 134)
    # someone's gown, taken off to play, hung over the windscreen
    T.draped_gown(bg, 524, WS[0] + 1)
    # two graduation balloons (gold and black) tied to the mesh above the bench
    for (bx, by, col) in [(118, 92, T.CU_GOLD), (130, 98, T.CU_BLACK)]:
        bg.line(bx + 4, by + 12, 124, 128, "#e8e0c8")
        bg.ellipse(bx - 1, by - 1, 11, 13, T.OUT)
        bg.ellipse(bx, by, 9, 11, col[2]); bg.ellipse(bx + 3, by + 1, 5, 6, col[3])
        bg.px(bx + 6, by + 2, "#fff6dc" if col is T.CU_GOLD else "#8a8a9a"); bg.rect(bx + 3, by + 11, 3, 1, col[1])
    bg.rect(122, 127, 4, 2, "#e8e0c8")


def paint_gate_opening(bg):
    """The exit gate at the left end of the back fence, standing open: through it a sunlit lawn,
    the concrete walk curving away toward commencement, a hedge and the white peak of a
    ceremony marquee with gold pennants. Header bar, heavy gate posts, a concrete sill."""
    x0, x1 = GATE[0] + 2, GATE[1] - 1
    y0 = GATE_TOP + 3
    rng = T._rng(57)
    G, Pp = T.GRASS_SUN, T.PATH_SUN
    # sky glow low behind the hedge, then the marquee roof
    for y in range(y0, 130):
        bg.hline(x0, y, x1 - x0, mix("#e8b878", "#c89a6a", (y - y0) / 12))
    mx0, mx1, pk = x0 + 1, x0 + 31, x0 + 16                    # a white marquee: peaked roof, straight eaves
    bg.poly([(mx0, 128), (pk - 3, 121), (pk + 3, 121), (mx1, 128)], "#f4eee2")
    bg.poly([(pk + 3, 121), (mx1, 128), (pk + 6, 128)], "#d8cebe")         # the far slope in its own shade
    bg.hline(pk - 3, 121, 7, "#fffaf0"); bg.line(mx0, 128, pk - 3, 121, "#fffaf0")
    bg.vline(pk, 117, 4, "#7a6a5a"); bg.px(pk + 1, 117, T.CU_GOLD[3]); bg.px(pk + 2, 118, T.CU_GOLD[2])
    for i, x in enumerate(range(mx0, mx1 + 1, 3)):              # scalloped valance, gold and white
        c = T.CU_GOLD[3] if i % 2 else "#f4eee2"
        bg.hline(x, 129, 3, c); bg.px(x + 1, 130, c)
    bg.hline(mx0, 128, mx1 - mx0 + 1, "#b8ac9a")
    for i, x in enumerate(range(mx1 + 3, x1, 4)):                 # pennant string to the right
        bg.px(x, 124 + (i % 2), "#6a5a4a")
        bg.px(x + 1, 125 + (i % 2), T.CU_GOLD[3] if i % 2 else "#2a2830")
    # hedge, backlit: dark mass with gold rim leaves on top
    top = [132 + int(1.2 * np.sin(x * 0.7) + rng.integers(0, 2)) for x in range(x0, x1)]
    for i, x in enumerate(range(x0, x1)):
        bg.vline(x, top[i], 142 - top[i], "#3a3a24" if (x + top[i]) % 3 else "#2e3020")
        bg.px(x, top[i], "#d8a848" if i % 3 else "#b8883c")
        if i % 4 == 1:
            bg.px(x, top[i] + 3, "#4a4628")
    # lawn in full sun, mown stripes
    for y in range(142, FOOT):
        for x in range(x0, x1):
            k = 3 if ((x - (y - 142) // 2) // 7) % 2 else 4
            bg.px(x, y, G[k] if (x * 7 + y * 3) % 11 else G[k + 1])
    # the walk: leaves the sill wide, narrows and bends away to the upper left
    for y in range(140, FOOT):
        t = (y - 140) / (FOOT - 140)
        cx = x0 + 6 + t * 18
        hw = 3 + t * 15
        a, b = int(round(cx - hw)), int(round(cx + hw))
        for x in range(max(x0, a), min(x1, b + 1)):
            k = 4 if x < cx + hw * 0.3 else 3
            bg.px(x, y, Pp[k])
        if x0 <= a < x1:
            bg.px(a, y, Pp[1])
        if x0 <= b < x1:
            bg.px(b, y, G[1])
        if y % 9 == 0:                                              # expansion joints
            bg.hline(max(x0, a + 1), y, max(0, min(x1, b) - max(x0, a + 1)), Pp[2])
    # a long shadow of the gate post falling across the lawn (sun from the right, behind)
    for y in range(146, FOOT):
        sx = GATE[1] - 2 + int((y - FOOT) * 1.9 / -0.45 * 0.12)
        if x0 <= sx < x1:
            bg.px(sx, y, C("#1a1a20", 0.35))
    # header bar and the heavy gate posts
    bg.rect(GATE[0], GATE_TOP, GATE[1] - GATE[0] + 1, 3, T.FENCE[1]); bg.hline(GATE[0], GATE_TOP, GATE[1] - GATE[0] + 1, T.FENCE[3])
    bg.hline(GATE[0], GATE_TOP + 3, GATE[1] - GATE[0] + 1, C("#0a0a10", 0.5))
    for gx in GATE:
        bg.rect(gx - 2, TOP_RAIL - 3, 5, FOOT - TOP_RAIL + 3, T.FENCE[1])
        bg.vline(gx - 2, TOP_RAIL - 3, FOOT - TOP_RAIL + 3, T.FENCE[0]); bg.vline(gx + 2, TOP_RAIL - 3, FOOT - TOP_RAIL + 3, T.FENCE[4])
        bg.vline(gx + 1, TOP_RAIL - 2, FOOT - TOP_RAIL + 2, T.FENCE[2])
        bg.rect(gx - 3, TOP_RAIL - 5, 7, 2, T.FENCE[2]); bg.hline(gx - 2, TOP_RAIL - 6, 5, T.FENCE[3]); bg.px(gx + 2, TOP_RAIL - 5, "#c8a870")
    # latch keeper on the right post
    bg.rect(GATE[1] - 4, 146, 3, 4, T.STEEL[3]); bg.px(GATE[1] - 4, 146, T.STEEL[5])
    # concrete sill where the curb breaks for the gate
    bg.rect(x0 - 2, WS[1], x1 - x0 + 4, 2, Pp[3]); bg.hline(x0 - 2, WS[1], x1 - x0 + 4, Pp[5])


def paint_gate_leaf(bg, full):
    """The gate leaf, swung open into the court on its hinges: tubular frame with a mid rail and
    a diagonal brace, windscreen fabric on the lower part (catching the sun now it faces right),
    chain-link above, a drop rod at the free end."""
    hx, fy = GATE[0], FOOT                     # hinge post, floor line
    dx, dy, hh = 19, 22, FOOT - GATE_TOP - 2   # free end offset on the floor, leaf height
    ws = T.WS_LIT
    for y in range(GATE_TOP, fy + dy + 1):
        for x in range(hx, hx + dx + 1):
            u = (x - hx) / dx
            v = (fy + dy * u - y) / hh
            if not (0 <= u <= 1 and 0 <= v <= 1):
                continue
            fu = min(u * dx, (1 - u) * dx)       # px to the side frame
            fv = min(v * hh, (1 - v) * hh)       # px to the top / bottom frame
            if fu < 1.5 or fv < 1.5 or abs(v * hh - hh * 0.62) < 1:
                c = T.FENCE[4] if (u > 0.5 and fu < 1.5) or (fv < 1.5 and v > 0.5) else T.FENCE[1]
                bg.px(x, y, c)
            elif abs(v - (0.62 - 0.6 * u)) * hh < 0.8 and v < 0.62:
                bg.px(x, y, T.FENCE[2])           # diagonal brace across the fabric
            elif v < 0.62:
                wsc = T.WINDSCREEN
                k = 5 if u > 0.45 else 4           # the low sun along its face, brighter to the free end
                if int(v * hh) % 3 == 2:
                    k -= 1
                if v * hh > hh * 0.62 - 3:
                    k = 2                          # hem
                c = wsc[k] if fu > 2.5 else wsc[2]
                if u > 0.82 and fu > 1.5 and v * hh < hh * 0.62 - 3:
                    c = ws[1]                      # sun glowing through the fabric at the free end
                bg.px(x, y, c)
            else:
                a = (int(x + v * hh) % 5 == 0); b = (int(x - v * hh) % 5 == 0)
                if a or b:
                    bg.px(x, y, C(T.FENCE[3] if b else T.FENCE[1], 0.8))
    # hinges on the post, the drop rod and its scrape arc on the floor
    for v in (0.12, 0.85):
        bg.rect(hx - 1, int(fy - v * hh) - 1, 3, 3, T.FENCE[3]); bg.px(hx + 1, int(fy - v * hh) - 1, "#c8a870")
    bg.vline(hx + dx - 1, fy + dy - 6, 7, T.STEEL[2]); bg.px(hx + dx - 1, fy + dy - 6, T.STEEL[4])
    for i in range(12):
        a = np.pi / 2 * i / 11
        bg.px(int(hx + 1 + dx * np.sin(a) * 1.0), int(fy + dy * np.sin(a) + 1), C("#ece0c8", 0.35))
    # its own small shade at the foot (the sun is on its face; it shades the floor to its left)
    for i in range(dx):
        bg.px(hx + i - 1, int(fy + dy * i / dx) + 1, C("#0d0b16", 0.3))


# ---------------------------------------------------------------- floor
def court_layer(pal, seed=21):
    """The whole floor painted in one light (sun or shade). Same seeds both times so the two
    versions line up and can be joined along the shadow edges."""
    cv = Canvas(W, H, seed=seed)
    rng = T._rng(seed)
    S, Cc, L = T.P(pal["surround"]), T.P(pal["court"]), pal["line"]
    ys, xs = np.mgrid[0:H, 0:W]
    court = (xs >= DL) & (xs < DR) & (ys >= FB) & (ys < NB + 2)
    # squeegee strokes: long bands one tone apart with ragged ends (the acrylic laid in passes)
    tone = np.full((H, W), 3, int)
    y = FOOT
    while y < H:
        bh = int(rng.integers(4, 10))
        x = int(rng.integers(-120, 0))
        while x < W:
            ln = int(rng.integers(80, 220))
            if rng.random() < 0.45:
                tone[y:y + bh, max(0, x):max(0, x + ln)] = 4
            x += ln
        y += bh
    def ell(cx, cy, rx, ry):
        return ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1
    # resurfaced patches over old cracks: crisp-edged, a tone darker, the edge a hair lighter
    for (x0, y0, x1, y1, k) in [(86, 230, 182, 254, 2), (494, 318, 618, 338, 2)]:
        m = (xs >= x0) & (xs < x1) & (ys >= y0) & (ys < y1)
        tone[m] = k
        tone[m & ((ys == y0) | (xs == x0))] = k + 2
    # bird baths: low spots where rain sits, a darker pool with a dried ring
    for (cx, cy, rx, ry) in [(112, 272, 26, 6), (566, 290, 22, 5), (380, 244, 16, 4)]:
        outer = ell(cx, cy, rx, ry) | ell(cx + rx * 0.5, cy + 2, rx * 0.6, ry * 0.8)
        inner = ell(cx, cy, rx - 3, ry - 1.5) | ell(cx + rx * 0.5, cy + 2, rx * 0.6 - 3, ry * 0.8 - 1.5)
        tone[outer] = 1
        tone[inner] = 2
    # wear: paler, smoother patches where players stand (behind the baselines, at the T)
    worn = ell(CX, FB - 6, 46, 7) | ell(CX, NB + 6, 52, 8) | ell(CX, FS, 18, 4) | ell(CX, NS, 20, 4)
    worn |= ell(SL + 10, NB - 4, 22, 5) | ell(SR - 12, FB + 4, 20, 4)
    tone[worn] = np.maximum(tone[worn], 4)
    # the worn path from the open gate down to the exit (threshold 4): pale scuffed acrylic,
    # ragged edges, wider at both ends where people bunch up
    tcx = 47 + 5 * np.sin((ys - FOOT) / 124 * np.pi)
    t = np.clip((ys - FOOT) / (302 - FOOT), 0, 1)
    hw = 17 - 7 * np.sin(t * np.pi) + 3 * t
    jag = np.sin(ys * 1.7) * 1.2 + np.sin(ys * 0.53 + 1) * 1.6
    d = np.abs(xs - tcx) - (hw + jag)
    trail = (ys >= FOOT) & (ys <= 306 + np.sin(xs * 0.9) * 2)
    tone[trail & (d < 0)] = np.maximum(tone[trail & (d < 0)], 4)
    tone[trail & (d < -4) & (((xs * 3 + ys * 5) % 13) != 0)] = 5
    blot = ((xs // 3 * 7 + ys // 2 * 13) % 9 == 0)
    tone[trail & (d < -6) & ~blot] = 5
    tone[trail & (d < -8) & blot] = 6
    tone[worn & ell(CX, NB + 6, 30, 5)] = 5
    rgb = np.where(court[..., None], Cc[np.clip(tone, 0, 6)], S[np.clip(tone, 0, 6)])
    cv.a[..., :3] = rgb
    cv.a[..., 3] = 1
    cv.a[:FOOT] = 0
    # black sneaker scuffs along the gate path
    for i in range(16):
        y = int(FOOT + 8 + i * 7.4 + rng.integers(-2, 3))
        x = int(47 + 5 * np.sin((y - FOOT) / 124 * np.pi) + rng.integers(-9, 9))
        ln = int(rng.integers(2, 5))
        cv.hline(x, y, ln, S[1]); cv.px(x + ln, y + (1 if i % 2 else -1), S[2])
    # border where the court colour meets the surround (a darker painted edge)
    for (x0, y0, w, h) in [(DL - 1, FB - 1, DR - DL + 2, 1), (DL - 1, NB + 2, DR - DL + 2, 1)]:
        cv.rect(x0, y0, w, h, pal["court"][1])
    # lines: 2px, the far baseline a hair thinner in the distance
    lc, lw = L[1], L[0]
    for (x0, y0, w, h) in [(DL, FB, DR - DL, 2), (DL, NB, DR - DL, 2), (SL, FS, SR - SL, 2), (SL, NS, SR - SL, 2),
                           (DL, FB, 2, NB - FB + 2), (DR - 2, FB, 2, NB - FB + 2), (SL, FB, 2, NB - FB + 2),
                           (SR - 2, FB, 2, NB - FB + 2), (CX - 1, FS, 2, NS - FS), (CX - 1, FB + 2, 2, 3), (CX - 1, NB - 3, 2, 3)]:
        cv.rect(x0, y0, w, h, lc)
        if w > h:
            cv.hline(x0, y0 + h - 1, w, lw)
        else:
            cv.vline(x0 + w - 1, y0, h, lw)
    # worn spots in the lines (short runs, not speckle)
    for (x0, y0, w) in [(300, NB, 9), (352, NB + 1, 6), (318, FB, 7), (250, NS, 5), (CX - 1, NS - 6, 2)]:
        cv.rect(x0, y0, w, 1, mix(lc, pal["court"][4], 0.55))
    # shoe skid marks behind the baselines and along the alleys (short dark arcs)
    for (x, y, ln, d) in [(300, NB + 9, 9, 1), (318, NB + 12, 7, -1), (356, NB + 8, 10, 1), (344, FB - 8, 7, -1),
                          (312, FB - 5, 8, 1), (226, NB - 6, 6, 1), (437, FB + 8, 6, -1), (382, NB + 13, 6, -1)]:
        for i in range(ln):
            cv.px(x + i * d, y + (1 if 2 < i < ln - 2 else 0), C(pal["court"][0], 0.55))
    # ball marks: faint optic-yellow fuzz where serves and baseline rallies land
    for _ in range(26):
        x = int(rng.integers(SL + 4, SR - 6))
        y = int(rng.choice([rng.integers(FB + 4, FB + 16), rng.integers(NB - 16, NB - 3), rng.integers(FS + 3, FS + 9),
                            rng.integers(NS - 9, NS - 3)]))
        col = mix(pal["court"][3], "#c8dc3a", 0.28)
        cv.rect(x, y, 2 + int(rng.integers(0, 2)), 1, col)
    # a long sealed crack across the left surround, a hairline across the far court
    for pts in ([(26, 236), (60, 241), (92, 238), (130, 246), (168, 243), (198, 250)],
                [(262, 200), (290, 206), (318, 204), (350, 212), (384, 210), (412, 218)],
                [(500, 330), (540, 324), (570, 332), (618, 326)]):
        for (a, b) in zip(pts[:-1], pts[1:]):
            n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])))
            for i in range(n):
                t = i / n
                x = int(round(a[0] + (b[0] - a[0]) * t)); y = int(round(a[1] + (b[1] - a[1]) * t + np.sin(i * 0.9) * 0.6))
                cv.px(x, y, pal["crack"]); cv.px(x, y + 1, C(pal["crack"], 0.35))
    # side margins: grass beyond the side fences' concrete footings
    G = pal["grass"]
    for (x0, x1) in [(0, 17), (623, W)]:
        cv.rect(x0, FOOT, x1 - x0, H - FOOT, G[2])
        for yy in range(FOOT, H, 3):
            for xx in range(x0 + (yy // 3) % 3, x1, 4):
                cv.px(xx, yy, G[3]); cv.px(xx, yy + 1, G[1])
    for fx in (17, 621):
        for yy in range(FOOT, H):
            cv.rect(fx, yy, 2, 1, pal["path"][3]); cv.px(fx + 1, yy, pal["path"][1])
        for py in range(FOOT + 30, H, 60):
            cv.rect(fx - 1, py, 4, 3, "#2a2e34"); cv.hline(fx - 1, py, 4, "#5a5e66")
    # bottom: the near fence's footing and verge
    cv.rect(0, 346, W, 4, pal["path"][3]); cv.hline(0, 346, W, pal["path"][5]); cv.hline(0, 349, W, pal["path"][1])
    cv.rect(0, 350, W, H - 350, G[1])
    for xx in range(0, W, 3):
        cv.px(xx, 350 + (xx // 3) % 3, G[3]); cv.px(xx + 1, 352 + (xx // 5) % 4, G[2])
    # drain grate in the right surround
    cv.rect(560, 334, 18, 5, "#20242a")
    for gx in range(561, 577, 3):
        cv.vline(gx, 335, 3, "#4a4e56")
    return cv


SUN_PAL = {"surround": T.SURR_SUN, "court": T.COURT_SUN, "line": T.LINE_SUN, "crack": "#2a3a34", "path": T.PATH_SUN,
           "grass": T.GRASS_SUN}
SHADE_PAL = {"surround": T.SURR_SHADE, "court": T.COURT_SHADE, "line": T.LINE_SHADE, "crack": "#1a2430", "path": T.PATH_SHADE,
             "grass": ["#1a2424", "#22302c", "#2a3a32", "#324438", "#3c4e3e", "#46584a"]}


def shadow_masks(casters):
    """Long shadows on the floor: (full, half). full = solid shade; half = the net's mesh and the
    chain-link above the windscreen (a step lighter than full shade)."""
    full = np.zeros((H, W), bool)
    half = np.zeros((H, W), bool)
    ys, xs = np.mgrid[0:H, 0:W].astype(np.float32)
    # the windscreen throws a solid band; the light comes through the wind flaps
    ws_h = FOOT - WS[0]
    band_end = FOOT + T.SUN_DY * ws_h
    full |= (ys >= FOOT) & (ys < band_end)
    for (vx, vy) in VENTS:
        h0, h1 = FOOT - vy - 3, FOOT - vy + 1
        pts = [T.cast(vx, FOOT, h0), T.cast(vx + 6, FOOT, h0), T.cast(vx + 5, FOOT, h1), T.cast(vx + 1, FOOT, h1)]
        full &= ~T.poly_mask(W, H, pts)
    gh = FOOT - GATE_TOP - 3                  # light through the open gate
    g0, g1 = GATE[0] + 2, GATE[1] - 2
    full &= ~T.poly_mask(W, H, [(g0, FOOT), (g1, FOOT), T.cast(g1, FOOT, gh), T.cast(g0, FOOT, gh)])
    hy = FOOT + T.SUN_DY * (FOOT - GATE_TOP)
    full |= T.poly_mask(W, H, [(g0 + T.SUN_DX * (FOOT - GATE_TOP), hy - 1), (g1 + T.SUN_DX * (FOOT - GATE_TOP), hy - 1),
                                (g1 + T.SUN_DX * (FOOT - GATE_TOP), hy + 1), (g0 + T.SUN_DX * (FOOT - GATE_TOP), hy + 1)])
    # the open leaf: fabric part solid, mesh part half
    lh, fh = FOOT - GATE_TOP - 2, (FOOT - GATE_TOP - 2) * 0.62
    b0, b1 = (GATE[0], FOOT), (GATE[0] + 19, FOOT + 22)
    full |= T.poly_mask(W, H, [b0, b1, T.cast(b1[0], b1[1], fh), T.cast(b0[0], b0[1], fh)])
    half |= T.poly_mask(W, H, [T.cast(b0[0], b0[1], fh), T.cast(b1[0], b1[1], fh), T.cast(b1[0], b1[1], lh), T.cast(b0[0], b0[1], lh)])
    for gx in GAPS:
        a, b = T.cast(gx + 3, FOOT, 4), T.cast(gx + 3, FOOT, ws_h - 4)
        full &= ~T.poly_mask(W, H, [(a[0], a[1]), (a[0] + 2, a[1]), (b[0] + 2, b[1]), (b[0], b[1])])
    # chain-link above it: wire shadows as a lattice
    hgt = (ys - FOOT) / T.SUN_DY
    u = xs - T.SUN_DX * hgt
    vy_ = FOOT - hgt
    mesh = (ys >= band_end) & (hgt <= FOOT - TOP_RAIL)
    wire = ((np.floor(u + vy_) % 6) < 1) | ((np.floor(u - vy_) % 6) < 1)
    half |= mesh & wire
    # top rail and posts
    ry = FOOT + T.SUN_DY * (FOOT - TOP_RAIL)
    full |= (ys >= ry - 1) & (ys < ry + 1)
    for px_ in POSTS + list(GATE) + [-30, 690]:
        a, b = T.cast(px_, FOOT, ws_h), T.cast(px_, FOOT, FOOT - TOP_RAIL + 2)
        full |= T.poly_mask(W, H, [(a[0] - 1, a[1]), (a[0] + 2, a[1]), (b[0] + 2, b[1]), (b[0] - 1, b[1])])
    # trees and light towers beyond the fence: every floor pixel looks back along the sun to the
    # painted caster that would shade it; crowns get a few sun flecks
    hb = (ys - CASTER_FOOT) / T.SUN_DY
    sx = np.round(xs - T.SUN_DX * hb).astype(int)
    sy = np.round(CASTER_FOOT - hb).astype(int)
    ok = (hb > 0) & (sx >= 0) & (sx < W) & (sy >= 0) & (sy < WS[0])
    tree = np.zeros((H, W), bool)
    tree[ok] = casters[sy[ok], sx[ok]]
    rng = T._rng(41)
    fy, fx = np.where(tree & (ys > band_end + 2))
    for i in rng.choice(len(fy), size=min(len(fy), len(fy) // 90), replace=False) if len(fy) else []:
        tree[fy[i]:fy[i] + 1, fx[i]:fx[i] + 3] = False
    full |= tree
    # the net: posts and tape solid, the mesh as half shade
    nh = 24
    pl, pr = (CX - 150, NET_Y), (CX + 150, NET_Y)
    tl, tr = T.cast(pl[0] + 3, NET_Y, nh), T.cast(pr[0] - 3, NET_Y, nh)
    half |= T.poly_mask(W, H, [(pl[0] + 3, NET_Y), (pr[0] - 3, NET_Y), tr, tl])
    for p in (pl, pr):
        e = T.cast(p[0], NET_Y, nh + 1)
        full |= T.poly_mask(W, H, [(p[0] - 2, NET_Y), (p[0] + 2, NET_Y), (e[0] + 2, e[1]), (e[0] - 2, e[1])])
    for k in range(int(tl[0]), int(tr[0])):
        x_net = k - T.SUN_DX * nh
        sag = 4 * (1 - (abs(x_net - CX) / 150) ** 1.6)
        yy = int(round(tl[1] - T.SUN_DY * sag))
        full[yy:yy + 2, k] = True
    s = T.cast(CX, NET_Y, nh - 4)
    full |= T.poly_mask(W, H, [(CX - 1, NET_Y), (CX + 2, NET_Y), (s[0] + 2, s[1]), (s[0] - 1, s[1])])
    # bench: seat slab, backrest, legs
    bx, by = BENCH
    x0, x1 = bx - 54, bx + 54
    seat = [T.cast(x0, by - 8, 15), T.cast(x1, by - 8, 15), T.cast(x1, by, 15), T.cast(x0, by, 15)]
    full |= T.poly_mask(W, H, seat)
    back = [T.cast(x0, by - 8, 29), T.cast(x1, by - 8, 29), T.cast(x1, by - 8, 18), T.cast(x0, by - 8, 18)]
    full |= T.poly_mask(W, H, back)
    for lx in (x0 + 6, x1 - 8):
        e = T.cast(lx, by, 15)
        full |= T.poly_mask(W, H, [(lx, by), (lx + 3, by), (e[0] + 3, e[1]), e])
    towel = [T.cast(x0 + 18, by - 8, 29), T.cast(x0 + 38, by - 8, 29), T.cast(x0 + 38, by - 8, 14), T.cast(x0 + 18, by - 8, 14)]
    full |= T.poly_mask(W, H, towel)
    # hopper: basket and legs
    hx, hy = HOPPER
    full |= T.poly_mask(W, H, [T.cast(hx - 8, hy - 4, 20), T.cast(hx + 8, hy - 4, 20), T.cast(hx + 8, hy, 9), T.cast(hx - 8, hy, 9)])
    for lx in (hx - 9, hx + 8):
        e = T.cast(lx, hy, 9)
        full |= T.poly_mask(W, H, [(lx, hy), (lx + 1, hy), (e[0] + 1, e[1]), e])
    # ball machine: body and heaped hopper, handle
    mx, my = MACHINE
    pts = [(mx - 15, my - 6), (mx + 15, my - 6), (mx + 15, my), (mx - 15, my)]
    hull = pts + [T.cast(x, y, 34) for (x, y) in pts]
    from scipy.spatial import ConvexHull
    hp = np.array(hull)
    full |= T.poly_mask(W, H, hp[ConvexHull(hp).vertices])
    e = T.cast(mx + 15, my - 4, 40)
    full |= T.poly_mask(W, H, [(mx + 12, my - 4), (mx + 14, my - 4), (e[0] + 2, e[1]), e])
    # the light post: pole, crossarm and floods
    lx, ly = LAMP
    e = T.cast(lx, ly, 74)
    full |= T.poly_mask(W, H, [(lx - 2, ly), (lx + 2, ly), (e[0] + 2, e[1]), (e[0] - 2, e[1])])
    a, b = T.cast(lx - 9, ly, 76), T.cast(lx + 10, ly, 80)
    full |= T.poly_mask(W, H, [(a[0], a[1] - 1), (b[0], b[1] - 1), (b[0], b[1] + 2), (a[0], a[1] + 2)])
    full[:FOOT] = False
    half &= ~full
    half[:FOOT] = False
    return full, half


def paint_floor(bg, casters):
    sun = court_layer(SUN_PAL)
    shd = court_layer(SHADE_PAL)
    full, half = shadow_masks(casters)
    fl = np.zeros((H, W), bool)
    fl[FOOT:] = True
    out = sun.a.copy()
    out[full] = shd.a[full]
    out[half] = sun.a[half] * 0.45 + shd.a[half] * 0.55
    bg.a[fl] = out[fl]
    # a crisp darker edge where shade starts (on the side facing the sun)
    edge = full & ~np.roll(full, -1, axis=1) & fl
    bg.fill_mask(edge, C("#0d0b16", 0.18))
    # the low sun warms the open court toward the right, in three flat steps
    ys, xs = np.mgrid[0:H, 0:W]
    lit = fl & ~full & ~half
    for r in (620, 470, 330):
        bg.fill_mask(lit & (((xs - 700) / r) ** 2 + ((ys - 170) / (r * 0.5)) ** 2 <= 1), C("#ffd488", 0.06))
    # the foot of the windscreen: leaves blown against it, a few balls that rolled there
    rng = T._rng(31)
    T.leaf_litter(bg, 80, FOOT + 3, 70, 3, 60, rng, dim=full)
    T.leaf_litter(bg, 330, FOOT + 3, 160, 3, 50, rng, dim=full)
    T.leaf_litter(bg, 560, FOOT + 3, 70, 3, 60, rng, dim=full)
    T.leaf_litter(bg, 30, 330, 30, 14, 40, rng, dim=full)
    T.leaf_litter(bg, 610, 300, 22, 30, 40, rng, dim=full)
    T.leaf_litter(bg, 26, 250, 6, 40, 22, rng, dim=full)        # kicked to the sides of the gate path
    T.leaf_litter(bg, 72, 214, 6, 26, 16, rng, dim=full)
    for (x, y, n) in [(270, 238, 4), (380, 300, 3), (150, 300, 5), (520, 270, 4), (330, 190, 3), (470, 330, 3)]:
        T.leaf_litter(bg, x, y, 30, 14, n, rng, dim=full)
    balls = [(122, 181), (128, 183), (402, 180), (560, 182), (252, 204), (470, 248), (364, 270), (196, 222),
             (232, 220), (92, 212), (540, 300), (292, 340)]
    for (x, y) in balls:
        T.tennis_ball(bg, x, y, lit=not full[y, x + 2])
    # the discarded mortarboard on the near court, a commencement programme dropped by the bench
    T.mortarboard_flat(bg, 286, 316)
    T.programme_flat(bg, 120, 224)
    # a few curls of gold ribbon from the ceremony, walked in on someone's shoes
    for (x, y) in [(64, 292), (132, 236), (300, 324)]:
        c = "#e8c060" if not full[y, x] else "#a08848"
        bg.px(x, y, c); bg.px(x + 1, y - 1, c); bg.px(x + 2, y - 1, shade(c, -0.2)); bg.px(x + 3, y, c); bg.px(x + 4, y + 1, shade(c, 0.2))
    # outside the walkable floor: a little darker
    bg.rect(0, FOOT, 20, H - FOOT, C("#0d0b16", 0.18))
    bg.rect(620, FOOT, 20, H - FOOT, C("#0d0b16", 0.18))
    bg.rect(20, 340, 600, 20, C("#0d0b16", 0.18))
    return full


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=2)
    casters = paint_view(bg)
    paint_fence(bg)
    full = paint_floor(bg, casters)
    paint_gate_leaf(bg, full)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, name=None):
        sprite, ax, ay = made
        name = name or f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        props[str(index)] = {"texture": res + name, "anchor": [ax, ay]}

    save(0, T.tennis_net(300, 26))
    save(1, T.ball_machine(34, 40))
    save(2, T.court_bench(110, 30))
    save(3, T.ball_hopper(18, 26))
    save(5, T.court_light(80))

    # the Colorado flag on the hall's pavilion, three frames of a slow ripple
    flags = []
    for k in range(3):
        fc = Canvas(18, 14)
        fc.a = T.colorado_flag(k)
        fc.save(os.path.join(out, f"flag-{k}.png"))
        flags.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(3)), "rate": 2.2,
                      "texture": res + f"flag-{k}.png", "x": 486, "y": 46})
    mx, my = MACHINE
    layers = flags + [
        # a ball dribbles out from behind the machine and rolls to rest behind the net post
        {"kind": "movers", "from": [mx - 6, my - 3], "to": [CX + 149, NET_Y - 3], "count": 1, "period": 11.0,
         "size": [3, 3], "color": "d8ec4a", "ease": "out"},
        # the machine's power LED and the court light warming up
        {"kind": "twinkle", "points": [[mx - 19 + 2 + 22, my - 41 + 1 + 16 + 6, "3cfa6a", 1]], "rate": 1.4, "min": 0.3},
        {"kind": "twinkle", "points": [[LAMP[0] - 5, LAMP[1] - 77, "fff0c4", 1], [LAMP[0] + 6, LAMP[1] - 77, "fff0c4", 1]],
         "rate": 0.6, "min": 0.4},
        # pollen and dust drifting in the low sun
        {"kind": "particles", "style": "dust", "count": 18, "rect": [300, 120, 330, 170], "speed": [3, 4], "color": "ffe6a8"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [],
        "overlays": [],
        "fauna": [
            {"kind": "bird", "x": 60, "y": 40, "fly": 10.0, "rate": 4.0},
            {"kind": "bird", "x": 72, "y": 34, "fly": 10.0, "rate": 3.6},
            {"kind": "bird", "x": 300, "y": 22, "fly": 8.0, "rate": 3.2},
            {"kind": "squirrel", "x": 262, "y": TOP_RAIL, "range": 4, "speed": 0.25, "rate": 1.2},
            {"kind": "pigeon", "x": 586, "y": 296, "range": 6, "speed": 0.3, "rate": 2.0, "flip": True},
        ],
        "leaves": [[20, 96, 120, 80], [560, 70, 80, 106], [250, 104, 110, 72]],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
