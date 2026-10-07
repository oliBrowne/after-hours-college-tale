#!/usr/bin/env python3
"""Tanner, Rush Chair of Xi Omega Xi -- procedural pixel-art sprites for "After Hours - College Tale".

Mini-boss of the Hill (H01/H02).  Drawn the way Professor Eric is drawn (tools/eric_art/draw_eric.py)
and on the same engine as Chad (newcast/chad/draw_chad.py): parts are masks shaded with material
ramps from a top-left key light, given inner 1px lines and an ink silhouette.  Everything is drawn
at its final pixel size; nothing drawn is ever resampled (only the contact sheet and the private
previews are nearest-neighbour blow-ups).

Look: a bedsheet toga knotted over his left shoulder with a gold Greek-key hem and a gold rope belt,
a royal-purple cape with gold trim (the house letters "XI OMEGA XI" -- a fictional house, drawn as
the Greek glyphs -- in gold across the back), a gold party-store laurel wreath on a curly dark mop,
salmon shorts, purple-and-gold striped crew socks in navy slides, and an airhorn.  Warm brown skin,
a big open hype grin.  Over the top, never mean.

Outputs (in ./cells next to this script; build_sheet.py packs them into ./out):
  battle-0..5.png   100x100, 84px tall body  (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  entrance.png      cell 12, 176x164: carried in on a couch by two brothers
  world-0..5.png    64x56, 52px tall overworld cells (same poses, redrawn small)
  portrait-0..3.png 64x64 portraits          (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk/tanner-0..3.png    mouth-open portraits
  idle/tanner-blink.png, tanner-pose1.png, tanner-pose2.png   world-front idle extras
  feet.json         foot point [x, y] for every body cell
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
ID = "tanner"

# --------------------------------------------------------------------------
# palette
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline (same ink as the cast)

RAMP = {
    # 0 = line/darkest, 1 = shadow, 2 = mid, 3 = light, 4 = highlight
    "skin":   [(62, 32, 22), (122, 72, 44), (164, 106, 68), (194, 138, 94), (222, 174, 128)],
    "hair":   [(24, 14, 18), (56, 34, 32), (88, 58, 46), (122, 86, 64), (160, 120, 90)],
    "toga":   [(96, 98, 124), (170, 172, 192), (214, 216, 228), (238, 238, 246), (255, 255, 255)],
    "cape":   [(34, 12, 54), (68, 26, 104), (104, 42, 150), (140, 70, 192), (184, 124, 228)],
    "lining": [(54, 14, 48), (100, 26, 82), (138, 40, 112), (170, 64, 142), (206, 110, 180)],
    "gold":   [(92, 58, 14), (170, 120, 30), (222, 172, 54), (246, 212, 100), (255, 240, 170)],
    "shorts": [(92, 34, 36), (162, 72, 66), (206, 110, 96), (232, 146, 126), (248, 186, 166)],
    "sock":   [(110, 112, 130), (182, 184, 198), (226, 226, 234), (244, 244, 250), (255, 255, 255)],
    "slide":  [(12, 14, 28), (28, 34, 62), (46, 56, 96), (72, 86, 132), (108, 122, 168)],
    "horn":   [(70, 10, 16), (150, 24, 34), (204, 48, 52), (236, 96, 90), (255, 170, 160)],
    "plastic": [(104, 100, 96), (176, 172, 164), (222, 218, 208), (244, 240, 232), (255, 255, 250)],
    "black":  [(10, 10, 16), (26, 26, 36), (44, 44, 58), (66, 66, 84), (96, 96, 118)],
    "couch":  [(40, 24, 16), (82, 50, 30), (118, 76, 44), (150, 104, 62), (184, 138, 90)],
    "plaid":  [(30, 44, 30), (52, 76, 50), (76, 104, 70), (104, 132, 92), (140, 164, 120)],
    "wood":   [(40, 22, 12), (78, 46, 24), (112, 70, 38), (146, 98, 56), (178, 132, 82)],
    # the two brothers in the entrance
    "khaki":  [(70, 58, 34), (130, 112, 70), (172, 152, 100), (202, 186, 134), (230, 216, 170)],
    "sky":    [(30, 52, 90), (60, 100, 150), (96, 142, 190), (136, 178, 220), (186, 214, 240)],
    "skinB":  [(92, 46, 32), (176, 108, 74), (218, 150, 108), (238, 184, 144), (250, 214, 182)],
    "hairB":  [(70, 36, 18), (134, 72, 34), (176, 104, 52), (210, 140, 76), (236, 182, 120)],
    "skinC":  [(48, 26, 22), (92, 54, 40), (124, 78, 56), (154, 104, 76), (184, 136, 104)],
    "hairC":  [(12, 10, 14), (28, 22, 26), (46, 36, 40), (68, 54, 58), (96, 80, 84)],
}
EYE = (30, 20, 24)
IRIS = (86, 52, 34)          # warm brown eyes
WHITE = (250, 248, 244)
SCLERA = (240, 234, 226)
MOUTH = (78, 24, 30)
LIP = (150, 82, 66)
TONGUE = (196, 92, 96)
TEETH = (252, 252, 248)
TEETH2 = (214, 214, 218)
BLUSH = (190, 98, 74)
BROW = (30, 18, 18)
SPARK = (255, 250, 210)
SPARK2 = (255, 214, 90)
SWEAT = (120, 196, 240)
SWEAT_HI = (220, 244, 255)
BLAST = [(255, 250, 220), (255, 214, 90), (255, 160, 70)]
RIM = (255, 170, 80)
# --------------------------------------------------------------------------
# tiny raster engine
# --------------------------------------------------------------------------
class Cv:
    """A canvas that composites shaded 'parts' (masks + material ramp) in order.

    Each part is shaded from its OWN full mask (so occlusion does not distort
    the form), drawn front-to-back in call order, and gets an inner 1px line
    where it borders something it should be separated from.  A final pass puts
    the ink silhouette around everything.
    """

    def __init__(self, w, h, open_bottom=False, light=(-0.55, -0.75, 0.62)):
        self.w, self.h = w, h
        self.col = np.zeros((h, w, 3), np.int32)
        self.alpha = np.zeros((h, w), bool)
        self.own = np.full((h, w), -1, np.int32)
        self.names = {}
        self.open_bottom = open_bottom
        self.Y, self.X = np.mgrid[0:h, 0:w].astype(float)
        L = np.array(light, float)
        self.L = L / np.linalg.norm(L)

    # ---- shapes (all aliased, analytic) ---------------------------------
    def empty(self):
        return np.zeros((self.h, self.w), bool)

    def ell(self, cx, cy, rx, ry, ang=0.0):
        dx, dy = self.X - cx, self.Y - cy
        if ang:
            c, s = math.cos(ang), math.sin(ang)
            dx, dy = dx * c + dy * s, -dx * s + dy * c
        return (dx / rx) ** 2 + (dy / ry) ** 2 <= 1.0

    def rect(self, x0, y0, x1, y1):
        return (self.X >= x0) & (self.X <= x1) & (self.Y >= y0) & (self.Y <= y1)

    def poly(self, pts):
        img = Image.new("L", (self.w, self.h), 0)
        ImageDraw.Draw(img).polygon([(float(x), float(y)) for x, y in pts], fill=1)
        return np.array(img) > 0

    def capsule(self, x0, y0, x1, y1, r0, r1=None):
        """Thick segment; radius can taper from r0 to r1."""
        if r1 is None:
            r1 = r0
        vx, vy = x1 - x0, y1 - y0
        L2 = vx * vx + vy * vy or 1e-9
        t = np.clip(((self.X - x0) * vx + (self.Y - y0) * vy) / L2, 0, 1)
        px, py = x0 + t * vx, y0 + t * vy
        r = r0 + (r1 - r0) * t
        return (self.X - px) ** 2 + (self.Y - py) ** 2 <= r * r

    def chain(self, pts, r):
        m = self.empty()
        for (a, b), (c, d) in zip(pts, pts[1:]):
            m |= self.capsule(a, b, c, d, r)
        return m

    def half(self, y=None, x=None, below=True, right=True):
        m = np.ones((self.h, self.w), bool)
        if y is not None:
            m &= (self.Y >= y) if below else (self.Y <= y)
        if x is not None:
            m &= (self.X >= x) if right else (self.X <= x)
        return m

    # ---- shading ---------------------------------------------------------
    def levels(self, mask, rad=None, soft=1.0, bias=0.0, cuts=(0.34, 0.56, 0.80),
               light=None, flat=False, k=1.25, ystretch=1.0):
        if flat:
            return np.where(mask, 2, 0)
        d = ndi.distance_transform_edt(np.pad(mask, 2))[2:-2, 2:-2]
        R = rad or max(2.0, float(d.max()))
        h = np.sqrt(np.clip(d / R, 0, 1))
        hs = ndi.gaussian_filter(h, soft) if soft else h
        gy, gx = np.gradient(hs)
        gy = gy * ystretch
        nx, ny, nz = -gx * R * k, -gy * R * k, np.ones_like(gx)
        n = np.sqrt(nx * nx + ny * ny + nz * nz)
        L = self.L if light is None else np.array(light) / np.linalg.norm(light)
        I = (nx * L[0] + ny * L[1] + nz * L[2]) / n + bias
        lv = np.ones(mask.shape, int)
        for c in cuts:
            lv += (I > c)
        return np.where(mask, lv, 0)

    # ---- compositing -----------------------------------------------------
    def part(self, name, mask, ramp, edge="dark", noedge=(), lv=None, tex=0.0, seed=1, **kw):
        if isinstance(ramp, str):
            ramp = RAMP[ramp]
        mask = mask.copy()
        if not mask.any():
            return mask
        if lv is None:
            lv = self.levels(mask, **kw)
        if tex:
            # sparse deterministic speckle one tone up/down -> fleece / fabric grain
            rng = np.random.default_rng(seed)
            r = rng.random(mask.shape)
            up = (r < tex / 2) & (lv < 4)
            dn = (r > 1 - tex / 2) & (lv > 1)
            # keep speckles isolated: only on pixels whose left neighbour isn't speckled
            iso = np.ones_like(up)
            iso[:, 1:] = ~(up[:, :-1] | dn[:, :-1])
            lv = lv + (up & iso) - (dn & iso)
        pid = len(self.names)
        self.names[name] = pid
        # edge pixels: inside mask, 4-neighbour outside mask and owned by a
        # part that is not in `noedge`
        no_ids = {self.names[n] for n in noedge if n in self.names}
        edgem = self.empty()
        if edge:
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                sm = np.zeros_like(mask)
                so = np.full_like(self.own, -1)
                ys = slice(max(0, dy), self.h + min(0, dy))
                yd = slice(max(0, -dy), self.h + min(0, -dy))
                xs = slice(max(0, dx), self.w + min(0, dx))
                xd = slice(max(0, -dx), self.w + min(0, -dx))
                sm[yd, xd] = mask[ys, xs]
                so[yd, xd] = self.own[ys, xs]
                if dy == 1:  # neighbour below, beyond canvas
                    sm[-1, :] = self.open_bottom
                    so[-1, :] = -2 if self.open_bottom else -1
                if dy == -1:
                    sm[0, :] = False
                if dx == 1:
                    sm[:, -1] = False
                if dx == -1:
                    sm[:, 0] = False
                out = ~sm
                bad = out & ~np.isin(so, list(no_ids)) if no_ids else out
                if self.open_bottom and dy == 1:
                    bad[-1, :] = False
                edgem |= mask & bad
        ramp_a = np.array(ramp)
        col = ramp_a[np.clip(lv, 0, 4)]
        self.col[mask] = col[mask]
        if edge:
            ec = np.array(INK if edge == "ink" else ramp[0] if edge == "dark" else edge)
            self.col[edgem] = ec
        self.alpha |= mask
        self.own[mask] = pid
        return mask

    def put(self, x, y, c):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            self.col[y, x] = c
            self.alpha[y, x] = True

    def puts(self, pts, c):
        for x, y in pts:
            self.put(x, y, c)

    def hline(self, x0, x1, y, c):
        for x in range(int(x0), int(x1) + 1):
            self.put(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(int(y0), int(y1) + 1):
            self.put(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        """Bresenham."""
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            self.put(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill(self, mask, c, only_alpha=True):
        m = mask & self.alpha if only_alpha else mask
        self.col[m] = c
        self.alpha |= m

    def get(self, x, y):
        return tuple(int(v) for v in self.col[y, x])

    def outline(self, color=INK):
        a = self.alpha
        p = np.pad(a, 1, constant_values=False)
        if self.open_bottom:
            p[-1, 1:-1] = a[-1, :]
        nb = p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
        sil = a & ~nb
        self.col[sil] = color

    def rim(self, n=1, color=RIM, own=None, mix=0.55, top_only=False):
        """Warm key-light rim just inside the silhouette on the upper-left."""
        a = self.alpha
        ys, xs = np.nonzero(a)
        res = []
        for y, x in zip(ys, xs):
            # a silhouette pixel lit from upper-left: transparent to its left or above
            if own is not None and self.own[y, x] not in own:
                continue
            left = x == 0 or not a[y, x - 1]
            up = y == 0 or not a[y - 1, x]
            if left or (up and not top_only):
                pass
            else:
                continue
            res.append((y, x))
        for y, x in res:
            # inner neighbour
            tx, ty = (x + 1, y) if (x == 0 or not a[y, x - 1]) else (x, y + 1)
            if 0 <= tx < self.w and 0 <= ty < self.h and a[ty, tx]:
                c = self.col[ty, tx]
                self.col[ty, tx] = (c * (1 - mix) + np.array(color) * mix).astype(int)

    def image(self):
        im = np.zeros((self.h, self.w, 4), np.uint8)
        im[..., :3] = np.clip(self.col, 0, 255)
        im[..., 3] = np.where(self.alpha, 255, 0)
        return Image.fromarray(im, "RGBA")


def mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))



# --------------------------------------------------------------------------
# shared bits
# --------------------------------------------------------------------------
def paint_map(cv, x0, y0, rows, pal, name="map", mirror=False):
    """Hand-placed pixels; they join the alpha so the ink pass outlines them like any part."""
    pid = len(cv.names)
    cv.names[name] = pid
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in pal:
                x, y = (x0 - i if mirror else x0 + i), y0 + j
                if 0 <= x < cv.w and 0 <= y < cv.h:
                    cv.put(x, y, pal[ch])
                    cv.own[y, x] = pid


def head_pal(skin="skin", hair="hair"):
    sk, hr, gd = RAMP[skin], RAMP[hair], RAMP["gold"]
    return {"K": INK, "0": hr[0], "1": hr[1], "2": hr[2], "3": hr[3], "4": hr[4], "s": sk[2], "l": sk[3], "h": sk[4],
            "d": sk[1], "x": sk[0], "E": EYE, "W": SCLERA, "w": WHITE, "I": IRIS, "B": BROW, "T": TEETH, "t": TEETH2,
            "M": MOUTH, "L": LIP, "r": BLUSH, "o": TONGUE, "g": gd[1], "G": gd[2], "Y": gd[3], "y": gd[4], "q": gd[0]}


def sparkle(cv, x, y, big=True, col=SPARK2):
    pts = [(x, y - 2), (x, y - 1), (x, y + 1), (x, y + 2), (x - 2, y), (x - 1, y), (x + 1, y), (x + 2, y)]
    if not big:
        pts = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
    cv.puts(pts, col)
    cv.put(x, y, WHITE)


def leaf(cv, x, y, ang, L=1.9, W=1.0, name="leaf"):
    """One gold laurel leaf centred at (x, y), long axis at ang (radians)."""
    m = cv.ell(x, y, L, W, ang)
    if not m.any():
        m = cv.rect(round(x), round(y), round(x), round(y))
    cv.part(name, m, "gold", edge="ink", rad=1.2, soft=0.4, cuts=(0.2, 0.45, 0.8), light=(-0.6, -0.8, 0.5))
    return m


def airhorn(cv, gx, gy, ang, s=1.3, name="horn", back=False):
    """An airhorn: red can gripped at (gx, gy), the white plastic trumpet pointing along ang
    (radians, 0 = right, -pi/2 = up).  s scales the drawing (1.0 battle, ~0.6 world).
    Returns the mouth centre of the trumpet."""
    ux, uy = math.cos(ang), math.sin(ang)
    vx, vy = -uy, ux
    Lc, Wc = 9.0 * s, 5.4 * s
    a0 = (gx - ux * Lc * 0.55, gy - uy * Lc * 0.55)          # can bottom
    a1 = (gx + ux * Lc * 0.45, gy + uy * Lc * 0.45)          # can top
    hw = Wc / 2
    can = cv.poly([(a0[0] + vx * hw, a0[1] + vy * hw), (a0[0] - vx * hw, a0[1] - vy * hw),
                   (a1[0] - vx * hw, a1[1] - vy * hw), (a1[0] + vx * hw, a1[1] + vy * hw)])
    cv.part(name + "can", can, "horn", edge="ink", rad=2.2 * s + 0.4, soft=0.6, cuts=(0.25, 0.5, 0.82),
            light=(-0.7, -0.6, 0.5))
    # white label band round the can
    if s >= 0.8:
        b0, b1 = (gx - ux * 1.2 * s, gy - uy * 1.2 * s), (gx + ux * 0.6 * s, gy + uy * 0.6 * s)
        band = can & cv.poly([(b0[0] + vx * 4, b0[1] + vy * 4), (b0[0] - vx * 4, b0[1] - vy * 4),
                              (b1[0] - vx * 4, b1[1] - vy * 4), (b1[0] + vx * 4, b1[1] + vy * 4)])
        band &= ndi.binary_erosion(can)
        cv.part(name + "band", band, "plastic", edge=None, noedge=(name + "can",),
                lv=np.where(band, 3, 0) - np.where(band & ((cv.X - gx) * vx + (cv.Y - gy) * vy > 0.5), 1, 0))
    # black valve cap
    c0 = a1
    c1 = (a1[0] + ux * 2.2 * s, a1[1] + uy * 2.2 * s)
    ch = 1.6 * s
    cap = cv.poly([(c0[0] + vx * ch, c0[1] + vy * ch), (c0[0] - vx * ch, c0[1] - vy * ch),
                   (c1[0] - vx * ch, c1[1] - vy * ch), (c1[0] + vx * ch, c1[1] + vy * ch)])
    cv.part(name + "cap", cap, "black", edge="ink", rad=1.2, soft=0.4)
    # the trumpet: a flared cone
    h0 = c1
    Lh = 7.5 * s
    h1 = (h0[0] + ux * Lh, h0[1] + uy * Lh)
    r0, r1 = 1.1 * s, 3.4 * s
    cone = cv.poly([(h0[0] + vx * r0, h0[1] + vy * r0), (h0[0] - vx * r0, h0[1] - vy * r0),
                    (h1[0] - vx * r1, h1[1] - vy * r1), (h1[0] + vx * r1, h1[1] + vy * r1)])
    cv.part(name + "cone", cone, "plastic", edge="ink", rad=2.0 * s, soft=0.6, cuts=(0.25, 0.5, 0.82))
    if not back and s >= 0.8:
        # the bell mouth seen a little open: a dark slot just inside the rim
        mx, my = h1[0] - ux * 1.0, h1[1] - uy * 1.0
        for k in range(-int(r1) + 1, int(r1)):
            x, y = int(round(mx + vx * k)), int(round(my + vy * k))
            if cone[y, x]:
                cv.put(x, y, RAMP["plastic"][1])
    return h1


def blast(cv, mx, my, ang, n=3, reach=10, spread=0.5):
    """Sound arcs from an airhorn mouth, drawn after the ink pass (thin and bright)."""
    for k in range(n):
        R = 3 + k * reach / n
        for j in range(-6, 7):
            a = ang + j * spread / 6
            x, y = int(round(mx + math.cos(a) * R)), int(round(my + math.sin(a) * R))
            if 0 <= x < cv.w and 0 <= y < cv.h and not cv.alpha[y, x]:
                cv.put(x, y, BLAST[k % 3])


def glyph(cv, x, y, ch, col, col2=None):
    """House letters, 5x5: X = Xi (three bars), O = Omega (a horseshoe on its feet)."""
    maps = {"X": ["#####", ".....", ".###.", ".....", "#####"],
            "O": [".###.", "#...#", "#...#", ".#.#.", "##.##"],
            "x": ["###", "...", ".#.", "...", "###"],
            "o": [".#.", "#.#", "#.#", "#.#", "#.#"]}
    for j, row in enumerate(maps[ch]):
        for i, v in enumerate(row):
            if v == "#":
                cv.put(x + i, y + j, col if (col2 is None or j < 3) else col2)


# ==========================================================================
# BATTLE  (84 px standing height: soles to the crest of his curls)
# ==========================================================================
BW, BH = 100, 100
BT = BH - 82          # body reference row; the curls rise 2px above it (height 84)


def b_hand(cv, x, y, name, rx=2.8, ry=3.0, skin="skin"):
    m = cv.ell(x, y, rx, ry)
    cv.part(name, m, skin, edge="ink", rad=2.5, soft=0.7, bias=0.05)
    return m


def b_arm(cv, name, pts, r0=3.7, r1=2.9, skin="skin"):
    """Bare arm: a tapered chain of capsules with a bicep catch-light."""
    m = cv.empty()
    n = len(pts) - 1
    for k, ((a, b), (c_, d)) in enumerate(zip(pts, pts[1:])):
        ra = r0 + (r1 - r0) * k / n
        rb = r0 + (r1 - r0) * (k + 1) / n
        m |= cv.capsule(a, b, c_, d, ra, rb)
    cv.part(name, m, skin, edge="dark", rad=3, soft=0.9, cuts=(0.26, 0.50, 0.84))
    return m


def toga_sleeve(cv, name, p0, p1, r=4.2):
    """The sheet draped over his left upper arm."""
    m = cv.capsule(p0[0], p0[1], p1[0], p1[1], r, r - 0.4)
    cv.part(name, m, "toga", edge="dark", rad=3, soft=0.9, cuts=(0.24, 0.48, 0.82))
    tg = RAMP["toga"]
    # hem of the sleeve: gold trim
    ux, uy = p1[0] - p0[0], p1[1] - p0[1]
    L = math.hypot(ux, uy) or 1
    ux, uy = ux / L, uy / L
    hem = m & ~cv.capsule(p0[0], p0[1], p1[0] - ux * 1.2, p1[1] - uy * 1.2, r + 1)
    ys, xs = np.nonzero(hem & ndi.binary_erosion(m))
    for y, x in zip(ys, xs):
        cv.put(x, y, RAMP["gold"][2] if (x + y) % 3 else RAMP["gold"][1])
    return m


def b_cape(cv, c, t, flare=(24, 24), hem=78, sway=0.0, back=False):
    """Purple cape hanging from the shoulders, flaring out; gold trim along its edges and hem.
    In front views the magenta lining shows where it turns at the outer edges."""
    fl, fr = flare
    pts = [(c - 12, t + 22), (c + 12, t + 22), (c + 16, t + 30), (c + fr * 0.8 + sway, t + 52),
           (c + fr + sway * 1.5, t + hem - 2)]
    # wavy hem from right to left
    n = 8
    for k in range(n + 1):
        x = c + fr + sway * 1.5 - (fl + fr) * k / n
        y = t + hem + (1.5 if k % 2 else -0.5)
        pts.append((x, y))
    pts += [(c - fl + sway * 1.5, t + hem - 2), (c - fl * 0.8 + sway, t + 52), (c - 16, t + 30)]
    m = cv.poly(pts)
    cv.part("cape", m, "cape", edge="dark", rad=10, soft=2.0, cuts=(0.26, 0.50, 0.84))
    cp, gd = RAMP["cape"], RAMP["gold"]
    # folds: long vertical shadows
    for fx in (-0.62, -0.3, 0.3, 0.62):
        x0 = c + fx * 14
        x1 = c + fx * (fl if fx < 0 else fr) + sway
        cv.line(x0, t + 32, x1, t + hem - 3, cp[1])
    if not back:
        # lining shows as a sliver along each outer edge
        for s, f in ((-1, fl), (1, fr)):
            for y in range(t + 34, t + hem - 1):
                u = (y - (t + 34)) / max(1, hem - 35)
                x = c + s * (16 + (f - 16) * u * 1.05) + sway * u * 1.5
                xi = int(round(x)) - s
                if m[y, xi]:
                    cv.put(xi, y, RAMP["lining"][2] if y % 7 else RAMP["lining"][3])
    # gold trim on the hem
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if y + 1 < cv.h and not m[y + 1, x] and y > t + hem - 4:
            cv.put(x, y - 1, gd[2] if (x // 2) % 2 else gd[3])
            if x % 4 == 0: cv.put(x, y - 2, gd[1])
    return m


def b_legs(cv, c, t, spread=0.0, back=False, socks=True, skin="skin", shorts="shorts", suf=""):
    """Salmon shorts, bare knees, purple-and-gold striped crew socks, navy slides."""
    sh = RAMP[shorts]
    D = lambda s_, y: s_ * spread * max(0.0, (y - t - 50)) / 30.0
    for s in (-1, 1):
        pts = [(s * 0.5, 50), (s * 11.5, 50), (s * 12, 60), (s * 2, 60), (s * 0.5, 56)]
        m = cv.poly([(c + x + D(s, t + y), t + y) for x, y in pts])
        cv.part("shorts%d%s" % (s, suf), m, shorts, rad=4, soft=1.0, cuts=(0.30, 0.56, 0.9), tex=0.02, seed=3 + s)
        # thigh-to-shin, bare
        leg = cv.poly([(c + s * 2.5 + D(s, t + 60), t + 60), (c + s * 10.5 + D(s, t + 60), t + 60),
                       (c + s * 9.6 + D(s, t + 66), t + 66), (c + s * 9.2 + D(s, t + 73), t + 73),
                       (c + s * 3.4 + D(s, t + 73), t + 73), (c + s * 3.0 + D(s, t + 66), t + 66)])
        cv.part("leg%d%s" % (s, suf), leg, skin, rad=3, soft=0.9, cuts=(0.28, 0.52, 0.86))
        # knee
        kx = c + s * 6.5 + D(s, t + 65)
        cv.put(kx - 1, t + 65, RAMP[skin][3]); cv.put(kx + 1, t + 66, RAMP[skin][1])
    cv.vline(c, t + 54, t + 59, sh[0])
    for s in (-1, 1):
        o = D(s, t + 59)
        cv.hline(c + s * 2 + o if s > 0 else c - 11 + o, c + 11 + o if s > 0 else c - 2 + o, t + 59, sh[1])
    for s in (-1, 1):
        o = int(round(D(s, t + 76)))
        sx = c + s * 6.3 + o
        sock = cv.rect(sx - 3, t + 73, sx + 3, t + 78)
        cv.part("sock%d%s" % (s, suf), sock, "sock", edge="dark", rad=2, soft=0.5, cuts=(0.3, 0.55, 0.9))
        if socks:
            cv.hline(sx - 2, sx + 2, t + 74, RAMP["cape"][2]); cv.hline(sx - 2, sx + 2, t + 75, RAMP["gold"][2])
        sl = cv.ell(sx + s * 0.4, t + 80.4, 5.4, 2.4) & cv.half(y=t + 81, below=False) & cv.half(y=t + 78)
        cv.part("shoe%d%s" % (s, suf), sl, "slide", rad=2.5, soft=0.6, cuts=(0.3, 0.55, 0.85))
        if not back:
            cv.hline(sx - 3, sx + 3, t + 79, RAMP["slide"][3])
            cv.put(sx - 1, t + 79, RAMP["gold"][3]); cv.put(sx + 1, t + 79, RAMP["gold"][2])
        cv.hline(sx - 4, sx + 4, t + 81, RAMP["slide"][0])


def b_torso(cv, c, t, back=False):
    """Bare right shoulder; the toga sheet wraps the rest, knotted on his left shoulder."""
    tg, gd, sk = RAMP["toga"], RAMP["gold"], RAMP["skin"]
    body = cv.poly([(c - 9, t + 21), (c + 9, t + 21), (c + 14, t + 24), (c + 15, t + 30), (c + 13, t + 40),
                    (c + 11, t + 46), (c + 12, t + 52), (c - 12, t + 52), (c - 11, t + 46), (c - 13, t + 40),
                    (c - 15, t + 30), (c - 14, t + 24)])
    cv.part("chest", body, "skin", rad=7, soft=1.4, cuts=(0.24, 0.48, 0.84))
    if not back:
        # pec + collarbone hints on the bare side
        cv.line(c - 10, t + 31, c - 5, t + 33, sk[1]); cv.put(c - 11, t + 30, sk[1])
        cv.line(c - 9, t + 23, c - 4, t + 24, sk[3])
        # toga: neckline runs from his left shoulder knot down across the chest to his right flank
        toga = cv.poly([(c + 2, t + 21), (c + 9, t + 21), (c + 14, t + 24), (c + 15, t + 30), (c + 13, t + 40),
                        (c + 11, t + 46), (c + 13, t + 57), (c + 6, t + 58.5), (c - 2, t + 57.5), (c - 8, t + 58.5),
                        (c - 13, t + 57), (c - 11, t + 46), (c - 13, t + 38), (c - 6, t + 34), (c - 2, t + 29)])
    else:
        toga = cv.poly([(c - 2, t + 21), (c - 9, t + 21), (c - 14, t + 24), (c - 15, t + 30), (c - 13, t + 40),
                        (c - 11, t + 46), (c - 13, t + 57), (c - 6, t + 58.5), (c + 2, t + 57.5), (c + 8, t + 58.5),
                        (c + 13, t + 57), (c + 11, t + 46), (c + 13, t + 38), (c + 6, t + 34), (c + 2, t + 29)])
    cv.part("toga", toga, "toga", rad=7, soft=1.6, cuts=(0.24, 0.48, 0.82))
    s = -1 if back else 1
    # drape folds, parallel to the neckline
    for k, col in ((0, tg[1]), (1, tg[3]), (2, tg[1]), (3, tg[1])):
        x0, y0 = c + s * (8 - k * 1), t + 26 + k * 5
        x1, y1 = c - s * (10 - k * 1), t + 40 + k * 5
        for x in range(min(x0, x1), max(x0, x1) + 1):
            u = (x - x0) / (x1 - x0)
            y = int(round(y0 + (y1 - y0) * u))
            if cv.own[y, x] == cv.names["toga"] and cv.get(x, y) != tg[0] and abs(u - 0.5) < 0.42:
                cv.put(x, y, col)
    # gold Greek-key hem
    ys, xs = np.nonzero(toga)
    for y, x in zip(ys, xs):
        if y + 1 < cv.h and not toga[y + 1, x] and cv.get(x, y) != tg[0]:
            pass
    for x in range(c - 12, c + 13):
        col = [y for y in range(t + 50, t + 60) if toga[y, x]]
        if not col:
            continue
        yb = max(col)
        cv.put(x, yb - 1, gd[2] if x % 3 else gd[3])
        cv.put(x, yb - 2, gd[1] if x % 3 == 0 else cv.get(x, yb - 2))
    # gold rope belt with a knot and tassels at his right hip
    for x in range(c - 12, c + 12):
        y = t + 45 + (1 if (x // 2) % 2 else 0) - (1 if x > c + 6 else 0) * 0
        if cv.own[y, x] in (cv.names["toga"], cv.names["chest"]):
            cv.put(x, y, gd[3] if x % 2 else gd[2]); cv.put(x, y + 1, gd[1])
    kx = c - 7 * s
    cv.puts([(kx, t + 45), (kx + 1, t + 45), (kx, t + 46), (kx + 1, t + 46)], gd[3]); cv.put(kx, t + 45, gd[4])
    cv.puts([(kx - s, t + 47), (kx - s, t + 48), (kx - s, t + 49), (kx + 1 - s, t + 47), (kx + 1 - s, t + 48)], gd[2])
    cv.put(kx - s, t + 50, gd[1])
    if not back:
        # the knot at his left shoulder: a gold medallion clasp
        mx, my = c + 8, t + 23
        med = cv.ell(mx, my, 2.4, 2.4)
        cv.part("medal", med, "gold", edge="ink", rad=2, soft=0.5, cuts=(0.2, 0.45, 0.8))
        cv.put(mx, my, gd[0]); cv.put(mx - 1, my - 1, gd[4])


def b_collar(cv, c, t, back=False, sway=0):
    """The cape's stand-up collar: two stiff pointed wings rising behind the head.  From the front we
    see the magenta lining inside a purple rim with gold piping; from the back the purple outside."""
    gd = RAMP["gold"]
    for s in (-1, 1):
        pts = [(c + s * 5, t + 21), (c + s * 6, t + 15), (c + s * 9, t + 10), (c + s * 14.5 + sway, t + 6.5),
               (c + s * 15 + sway, t + 15), (c + s * 13.5, t + 23)]
        m = cv.poly(pts)
        cv.part("collar%d" % s, m, "cape", edge="dark", rad=3, soft=0.8, cuts=(0.28, 0.52, 0.86))
        if back:
            continue
        inner = ndi.binary_erosion(m, iterations=2) & (cv.Y > t + 9)
        cv.part("lining%d" % s, inner, "lining", edge=None, rad=2, soft=0.6, cuts=(0.28, 0.52, 0.86))
        # gold piping round the rim, inside the purple edge
        rim = ndi.binary_erosion(m) & ~ndi.binary_erosion(m, iterations=2) & (cv.Y < t + 20)
        ys, xs = np.nonzero(rim)
        for y, x in zip(ys, xs):
            cv.put(x, y, gd[3] if (x + y) % 2 else gd[2])


def b_cord(cv, c, t):
    """Gold cord across the chest holding the cape on (bare shoulder side clasp)."""
    gd = RAMP["gold"]
    for x in range(c - 12, c + 7):
        u = (x - (c - 12)) / 19
        y = int(round(t + 24 + 2.2 * math.sin(math.pi * u)))
        cv.put(x, y, gd[2] if x % 2 else gd[3])
    m = cv.ell(c - 12, t + 24, 1.8, 1.8)
    cv.part("clasp", m, "gold", edge="ink", rad=1.5, cuts=(0.2, 0.45, 0.8))


def b_head_front(cv, c, t, pose):
    """Frontal head; t is the reference row (the curls crest at t-2)."""
    sk, hr = RAMP["skin"], RAMP["hair"]
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 7.6, t + 13, 1.7, 2.5), "skin", bias=0.05)
    nk = cv.rect(c - 4, t + 17, c + 4, t + 23)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 2, 0) - np.where(nk & (cv.Y <= t + 21), 1, 0))
    face = cv.ell(c, t + 12, 7.2, 8.0) | cv.poly([(c - 7, t + 13), (c + 7, t + 13), (c + 6.3, t + 18),
                                                   (c + 3, t + 21.5), (c - 3, t + 21.5), (c - 6.3, t + 18)])
    cv.part("face", face, "skin", rad=6, soft=1.4, cuts=(0.30, 0.52, 0.86))
    cv.put(c + 5, t + 18, sk[1]); cv.put(c + 4, t + 20, sk[1]); cv.put(c + 3, t + 21, sk[1])
    # ---- hair: a curly mop, each curl its own lit ball so the inner lines separate them ----
    base = cv.ell(c, t + 4.5, 8.4, 6.2) & cv.half(y=t + 7, below=False)
    cv.part("hair", base, "hair", edge=None, lv=np.where(base, 1, 0))
    for i, (bx, by, r) in enumerate(CURLS_FRONT):
        m = cv.ell(c + bx, t + by, r, r * 0.95) & cv.half(y=t - 2)
        if i >= 4:      # side and fringe curls never cover the face
            m &= ~(face & cv.half(y=t + 6.5))
        cv.part("curl%d" % i, m, "hair", edge=RAMP["hair"][1] if i < 8 else RAMP["hair"][0], rad=r, soft=0.6, cuts=(0.20, 0.50, 0.80),
                light=(-0.6, -0.8, 0.5))
        hx, hy = int(round(c + bx - r * 0.35)), int(round(t + by - r * 0.45))
        if cv.own[hy, hx] == cv.names["curl%d" % i]:
            cv.put(hx, hy, hr[4] if r > 2.8 else hr[3])
    # ---- face ----
    b_face_front(cv, c, t + 1, pose)


# curls of the battle mop: (dx, dy, r) from (c, t), drawn back to front
CURLS_FRONT = [(-6.4, 2.4, 3.0), (6.4, 2.4, 3.0), (-2.2, 1.1, 3.4), (2.4, 1.3, 3.4),
               (-8.6, 5.4, 2.5), (8.6, 5.4, 2.5), (-8.9, 9.0, 2.1), (8.9, 9.0, 2.1),
               (-5.2, 4.4, 2.4), (5.6, 4.4, 2.4), (-1.6, 4.2, 2.5), (2.2, 4.3, 2.4)]


def wreath_px(c, t, tilt=0, lost=False, n=4, step=2.2, rise=3.0, y0=5):
    """Pixel list of the gold laurel: two branches from the brow round to the temples.  Returns
    [(x, y, colour)]; drawn AFTER the ink pass so the leaves can stick out past the curls."""
    gd = RAMP["gold"]
    px = []
    for s in (-1, 1):
        for k in range(n):
            if lost and s > 0 and k >= n - 1:
                continue
            u = k / (n - 1)
            x = int(round(c + s * (1 + step * k)))
            y = int(round(t + y0 - rise * u * u + tilt * s * u))
            px.append((x, y, gd[1]))
            if k % 2 == 0:
                px += [(x + s, y - 1, gd[3]), (x + 2 * s, y - 1, gd[4] if k < 2 else gd[3])]
            else:
                px += [(x + s, y + 1, gd[2]), (x + 2 * s, y + 1, gd[3])]
    # the branch tips curl back over the temples
    for s in (-1, 1):
        if lost and s > 0:
            continue
        x = int(round(c + s * (1 + step * (n - 1)))) + 3 * s
        y = int(round(t + y0 - rise + tilt * s))
        px += [(x, y, gd[2]), (x + s, y - 1, gd[3]), (x, y - 1, gd[4])]
    px += [(int(c), int(t + y0), gd[4])]
    return px


def draw_after(cv, px, ink=True):
    """Put pixels after the ink pass; any transparent 4-neighbour of them becomes ink."""
    px = [(int(x), int(y), c_) for x, y, c_ in px]
    S = {(x, y) for x, y, _ in px}
    for x, y, col in px:
        cv.put(x, y, col)
    if ink:
        for x, y, _ in px:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                X, Y = x + dx, y + dy
                if (X, Y) not in S and 0 <= X < cv.w and 0 <= Y < cv.h and not cv.alpha[Y, X]:
                    cv.put(X, Y, INK)


def b_face_front(cv, c, t, pose):
    sk = RAMP["skin"]
    ey = t + 10
    # brows: thick, cranked high with hype
    for s in (-1, 1):
        x0 = c + s * 2
        for k in range(4):
            if pose == "tell":
                yy = ey - 2 + (1 if k == 0 else 0)
            elif pose == "hit":
                yy = ey - 3 - (1 if k == 0 else 0) + (1 if k == 3 else 0)
            else:
                yy = ey - 3 - (1 if k in (1, 2) else 0)
            cv.put(x0 + s * k, yy, BROW)
            if k in (1, 2) and pose != "hit":
                cv.put(x0 + s * k, yy + 1, mix(BROW, sk[1], 0.5))
    # eyes
    for s in (-1, 1):
        ex = c + s * 3 - (1 if s < 0 else 0)
        if pose == "tell":                       # squeezed shut: > <
            cv.put(ex + (0 if s < 0 else 1), ey, EYE); cv.put(ex + (1 if s < 0 else 0), ey + 1, EYE)
            cv.put(ex + (0 if s < 0 else 1), ey + 2, EYE)
            continue
        if pose == "hit":                        # x_x-ish dazed: small round pupils
            cv.put(ex, ey, SCLERA); cv.put(ex + 1, ey, SCLERA)
            cv.put(ex + (1 if s < 0 else 0), ey + 1, EYE); cv.put(ex + (0 if s < 0 else 1), ey + 1, SCLERA)
            cv.put(ex - 1 if s < 0 else ex + 2, ey + 1, EYE)
            continue
        cv.put(ex, ey, EYE); cv.put(ex + 1, ey, EYE)
        cv.put(ex, ey + 1, IRIS); cv.put(ex + 1, ey + 1, EYE)
        cv.put(ex, ey, WHITE)
        cv.put(ex - 1 if s < 0 else ex + 2, ey + 1, SCLERA)
        cv.hline(ex, ex + 1, ey + 2, sk[1])
    # nose
    cv.puts([(c, t + 12), (c, t + 13)], sk[3]); cv.put(c, t + 11, sk[3])
    cv.puts([(c + 1, t + 12), (c + 1, t + 13), (c + 1, t + 14)], sk[1])
    cv.puts([(c - 2, t + 14), (c - 1, t + 14), (c, t + 14), (c + 2, t + 14)], sk[1])
    cv.put(c - 5, t + 13, BLUSH); cv.put(c + 5, t + 13, mix(BLUSH, sk[1], 0.4))
    my = t + 16
    if pose == "idle":
        # big open hype grin
        cv.hline(c - 4, c + 4, my, MOUTH)
        cv.put(c - 5, my - 1, MOUTH); cv.put(c + 5, my - 1, MOUTH)
        cv.hline(c - 3, c + 3, my, TEETH); cv.put(c + 2, my, TEETH2)
        cv.hline(c - 3, c + 3, my + 1, MOUTH); cv.hline(c - 1, c + 1, my + 1, TONGUE)
        cv.hline(c - 2, c + 2, my + 2, LIP)
    elif pose == "talk":
        # LET'S GOOO: a shouting square mouth
        cv.put(c - 5, my - 1, MOUTH); cv.put(c + 5, my - 1, MOUTH)
        cv.hline(c - 4, c + 4, my, MOUTH); cv.hline(c - 3, c + 3, my, TEETH)
        for dy in (1, 2):
            cv.hline(c - 4, c + 4, my + dy, MOUTH)
        cv.hline(c - 2, c + 2, my + 2, TONGUE)
        cv.hline(c - 3, c + 3, my + 3, MOUTH)
        cv.hline(c - 2, c + 2, my + 4, LIP)
    elif pose == "tell":
        cv.hline(c - 5, c + 5, my, MOUTH)
        cv.put(c - 6, my - 1, MOUTH); cv.put(c + 6, my - 1, MOUTH)
        cv.hline(c - 4, c + 4, my, TEETH)
        cv.hline(c - 4, c + 4, my + 1, TEETH2)
        cv.put(c - 5, my + 1, MOUTH); cv.put(c + 5, my + 1, MOUTH)
        cv.hline(c - 4, c + 4, my + 2, MOUTH)
        cv.hline(c - 2, c + 2, my + 3, LIP)
    elif pose == "hit":
        for dy, w in ((0, 1), (1, 2), (2, 2), (3, 1)):
            cv.hline(c - w + 1, c + w + 1, my + dy, MOUTH)
        cv.hline(c, c + 2, my + 2, TONGUE)


def b_front(pose):
    cv = Cv(BW, BH)
    c, t = 50, BT
    sk = RAMP["skin"]
    sway = {"idle": 0, "talk": 1, "tell": -1, "hit": 3}[pose]
    b_cape(cv, c, t, flare=(25, 25) if pose != "hit" else (22, 28), sway=sway)
    b_legs(cv, c, t, spread=2 if pose in ("talk", "tell") else 0)
    b_torso(cv, c, t)
    # ---- arms ----
    horn_mouth = None
    if pose == "idle":
        # viewer-left (his right, bare): airhorn held at the hip, trumpet down and out
        b_arm(cv, "armL", [(c - 13, t + 26), (c - 17, t + 37), (c - 18, t + 47)])
        horn_mouth = airhorn(cv, c - 19, t + 51, math.radians(120))
        b_hand(cv, c - 18, t + 50, "handL")
        # viewer-right (his left, under the drape): fist on the hip, elbow out
        b_arm(cv, "armR", [(c + 13, t + 27), (c + 21, t + 36), (c + 14, t + 44)])
        toga_sleeve(cv, "sleeveR", (c + 12, t + 25), (c + 16, t + 30))
        b_hand(cv, c + 13, t + 45, "handR", rx=2.6, ry=2.6)
    elif pose == "talk":
        # airhorn lifted to the shoulder, other hand points right at you
        b_arm(cv, "armL", [(c - 13, t + 26), (c - 20, t + 34), (c - 18, t + 26)])
        horn_mouth = airhorn(cv, c - 18, t + 22, math.radians(-115))
        b_hand(cv, c - 18, t + 24, "handL")
        b_arm(cv, "armR", [(c + 13, t + 27), (c + 20, t + 33), (c + 26, t + 30)])
        toga_sleeve(cv, "sleeveR", (c + 12, t + 25), (c + 17, t + 30))
        b_hand(cv, c + 27, t + 29, "handR", rx=2.6, ry=2.4)
        fing = cv.capsule(c + 28, t + 28, c + 33, t + 26, 1.2)
        cv.part("finger", fing, "skin", edge="ink", noedge=("handR",), rad=1.2, soft=0.4, bias=0.1)
    elif pose == "tell":
        # the wind-up: airhorn hoisted overhead, braced, eyes squeezed shut
        b_arm(cv, "armL", [(c - 13, t + 26), (c - 20, t + 18), (c - 21, t + 8)])
        horn_mouth = airhorn(cv, c - 21, t + 3, math.radians(-60))
        b_hand(cv, c - 21, t + 5, "handL")
        b_arm(cv, "armR", [(c + 13, t + 27), (c + 21, t + 36), (c + 14, t + 44)])
        toga_sleeve(cv, "sleeveR", (c + 12, t + 25), (c + 16, t + 30))
        b_hand(cv, c + 13, t + 45, "handR", rx=2.6, ry=2.6)
    elif pose == "hit":
        # knocked back: airhorn fumbled out sideways, a leaf flies off the wreath
        b_arm(cv, "armL", [(c - 13, t + 26), (c - 20, t + 31), (c - 25, t + 27)])
        b_hand(cv, c - 26, t + 26, "handL")
        horn_mouth = airhorn(cv, c - 30, t + 17, math.radians(-140), name="hornfly")
        b_arm(cv, "armR", [(c + 13, t + 27), (c + 20, t + 31), (c + 23, t + 24)])
        toga_sleeve(cv, "sleeveR", (c + 12, t + 25), (c + 17, t + 29))
        b_hand(cv, c + 23, t + 22, "handR")
    b_cord(cv, c, t)
    hx = 2 if pose == "hit" else 0
    b_collar(cv, c, t, sway=1 if pose == "hit" else 0)
    b_head_front(cv, c + hx, t, pose)
    cv.outline()
    draw_after(cv, wreath_px(c + hx, t, tilt=1 if pose == "hit" else 0, lost=pose == "hit"))
    if pose == "tell" and horn_mouth:
        sparkle(cv, int(horn_mouth[0]) + 4, int(horn_mouth[1]) - 3, big=False)
    if pose == "talk" and horn_mouth:
        pass
    if pose == "hit":
        sx, sy = c - 9, t + 1
        cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx + 1, sy + 1), (sx - 1, sy + 2), (sx, sy + 2), (sx + 1, sy + 2), (sx, sy + 3)], SWEAT)
        cv.put(sx - 1, sy + 1, SWEAT_HI)
        # a leaf flying off
        lf = Cv(BW, BH)
        cv.puts([(c + 16, t - 1), (c + 17, t - 1), (c + 17, t - 2), (c + 18, t - 2)], RAMP["gold"][3])
        cv.puts([(c + 15, t - 1), (c + 16, t), (c + 17, t), (c + 18, t - 1), (c + 19, t - 2), (c + 19, t - 3), (c + 18, t - 3), (c + 17, t - 3), (c + 16, t - 2)], INK)
        cv.puts([(c + 14, t + 3), (c + 21, t + 1)], SPARK2)
    return cv


def b_side():
    """Side view facing RIGHT: we see his toga'd left side, the cape streaming behind."""
    cv = Cv(BW, BH)
    c, t = 50, BT
    sk, hr, gd, tg = RAMP["skin"], RAMP["hair"], RAMP["gold"], RAMP["toga"]
    # cape behind him, hanging off the back of the shoulders and kicking out behind
    pts = [(c - 5, t + 21), (c + 1, t + 22), (c - 2, t + 34), (c - 8, t + 52), (c - 14, t + 78), (c - 19, t + 77),
           (c - 24, t + 78), (c - 25, t + 74), (c - 18, t + 50), (c - 10, t + 30)]
    m = cv.poly(pts)
    cv.part("cape", m, "cape", edge="dark", rad=6, soft=1.6, cuts=(0.26, 0.50, 0.84))
    cv.line(c - 7, t + 30, c - 18, t + 74, RAMP["cape"][1]); cv.line(c - 4, t + 34, c - 12, t + 70, RAMP["cape"][3])
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if y + 1 < cv.h and not m[y + 1, x] and y > t + 72:
            cv.put(x, y - 1, gd[2] if x % 2 else gd[3])
    # standing collar seen edge-on behind the head
    col = cv.poly([(c - 6, t + 22), (c - 9, t + 14), (c - 10, t + 7), (c - 7, t + 8), (c - 3, t + 16), (c - 1, t + 21)])
    cv.part("collar", col, "cape", edge="dark", rad=2, soft=0.6)
    cv.line(c - 9, t + 9, c - 8, t + 15, gd[3]); cv.put(c - 9, t + 8, gd[2])
    # legs: far leg a tone darker, a short stride
    for side, dx, cuts in ((0, -3, (0.45, 0.7, 0.95)), (1, 2, (0.30, 0.56, 0.9))):
        x = c + dx
        sh = cv.poly([(x - 5, t + 50), (x + 5, t + 50), (x + 6, t + 60), (x - 5, t + 60)])
        cv.part("shorts%d" % side, sh, "shorts", rad=3, cuts=cuts)
        leg = cv.poly([(x - 3.5, t + 60), (x + 4.5, t + 60), (x + 3.5, t + 66), (x + 3, t + 73), (x - 2, t + 73), (x - 3, t + 66)])
        cv.part("leg%d" % side, leg, "skin", rad=2.5, cuts=cuts)
        sock = cv.rect(x - 2, t + 73, x + 3, t + 78)
        cv.part("sock%d" % side, sock, "sock", edge="dark", rad=2, cuts=cuts)
        cv.hline(x - 1, x + 2, t + 74, RAMP["cape"][2]); cv.hline(x - 1, x + 2, t + 75, gd[2])
        sl = cv.ell(x + 2, t + 80.4, 6.2, 2.4) & cv.half(y=t + 81, below=False) & cv.half(y=t + 78)
        cv.part("shoe%d" % side, sl, "slide", rad=2, cuts=cuts)
        cv.hline(x - 1, x + 5, t + 79, RAMP["slide"][3]); cv.put(x + 3, t + 79, gd[3])
        cv.hline(x - 3, x + 7, t + 81, RAMP["slide"][0])
    # torso in profile, wrapped in the toga
    body = cv.poly([(c - 6, t + 21), (c + 4, t + 21), (c + 9, t + 27), (c + 9, t + 37), (c + 7, t + 46), (c + 8, t + 57),
                    (c - 7, t + 58), (c - 7, t + 46), (c - 8, t + 34), (c - 8, t + 26)])
    cv.part("toga", body, "toga", rad=6, soft=1.4, cuts=(0.24, 0.48, 0.82))
    for k in range(4):
        cv.line(c + 6 - k, t + 26 + k * 6, c - 6, t + 34 + k * 6, tg[1])
    for x in range(c - 7, c + 9):
        cl = [y for y in range(t + 50, t + 60) if body[y, x]]
        if cl:
            cv.put(x, max(cl) - 1, gd[2] if x % 3 else gd[3])
    for x in range(c - 7, c + 9):
        y = t + 45 + (1 if (x // 2) % 2 else 0)
        if body[y, x]:
            cv.put(x, y, gd[3] if x % 2 else gd[2]); cv.put(x, y + 1, gd[1])
    # near arm under the drape, airhorn held forward at the hip like a holstered pistol
    b_arm(cv, "arm", [(c, t + 25), (c + 1, t + 36), (c + 5, t + 45)])
    toga_sleeve(cv, "sleeve", (c - 0.5, t + 24), (c + 0.5, t + 30))
    airhorn(cv, c + 9, t + 46, math.radians(-10))
    b_hand(cv, c + 6, t + 46, "hand")
    # ---- head in profile ----
    nk = cv.rect(c - 3, t + 15, c + 3, t + 23)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 1, 0) + np.where(nk & (cv.X > c) & (cv.Y > t + 19), 1, 0))
    face = cv.ell(c + 1.5, t + 11.5, 7.0, 8.0) | cv.poly([(c - 2, t + 14), (c + 8.2, t + 13), (c + 8, t + 18),
                                                         (c + 5.5, t + 21.4), (c + 1, t + 21), (c - 3, t + 17)])
    cv.part("face", face, "skin", rad=6, soft=1.4, cuts=(0.30, 0.52, 0.86))
    nose = cv.poly([(c + 8, t + 10.5), (c + 10.4, t + 14), (c + 8, t + 15)])
    cv.part("nose", nose, "skin", edge=None, lv=np.where(nose, 3, 0))
    curls = [(-4.6, 2.4, 3.2), (-0.6, 1.1, 3.4), (3.4, 1.8, 3.0), (-7.4, 6.4, 2.8), (-7.0, 10.6, 2.5),
             (-4.6, 14.0, 2.1), (6.4, 4.6, 2.2), (-3.0, 6.0, 2.6), (1.4, 4.6, 2.5)]
    base = cv.ell(c - 1.5, t + 6, 7.4, 6.4) & cv.half(y=t - 2) & ~(face & cv.half(x=c + 1) & cv.half(y=t + 7))
    cv.part("hair", base, "hair", edge=None, lv=np.where(base, 1, 0))
    for i, (bx, by, r) in enumerate(curls):
        mm = cv.ell(c + bx, t + by, r, r * 0.95) & cv.half(y=t - 2)
        mm &= ~(face & cv.half(y=t + 6.5) & cv.half(x=c - 1))
        cv.part("curl%d" % i, mm, "hair", edge=hr[1], rad=r, soft=0.6, cuts=(0.20, 0.50, 0.80), light=(-0.6, -0.8, 0.5))
        hx, hy = int(round(c + bx - r * 0.35)), int(round(t + by - r * 0.45))
        if cv.own[hy, hx] == cv.names["curl%d" % i]:
            cv.put(hx, hy, hr[4] if r > 2.8 else hr[3])
    cv.part("ear", cv.ell(c - 1, t + 13, 1.8, 2.5), "skin", bias=0.05)
    cv.put(c - 1, t + 13, sk[1])
    # face details (facing right)
    ey = t + 11
    cv.hline(c + 3, c + 7, ey - 3, BROW); cv.put(c + 4, ey - 4, BROW); cv.put(c + 5, ey - 4, BROW)
    cv.put(c + 5, ey, EYE); cv.put(c + 6, ey, EYE); cv.put(c + 5, ey + 1, IRIS); cv.put(c + 6, ey + 1, EYE)
    cv.put(c + 5, ey, WHITE); cv.put(c + 7, ey + 1, SCLERA); cv.hline(c + 5, c + 6, ey + 2, sk[1])
    cv.put(c + 9, t + 14, sk[1]); cv.put(c + 8, t + 15, sk[1])
    cv.put(c + 3, t + 14, BLUSH)
    my = t + 17
    cv.hline(c + 5, c + 8, my, MOUTH); cv.hline(c + 6, c + 8, my, TEETH); cv.put(c + 4, my - 1, MOUTH)
    cv.hline(c + 5, c + 7, my + 1, MOUTH); cv.put(c + 6, my + 2, LIP)
    cv.outline()
    # wreath: one branch from the brow over the ear to the back
    px = []
    for k in range(6):
        x = c + 6 - k * 2.4
        y = t + 5 - 1.2 * (k / 5) - (0 if k < 4 else 0)
        px.append((x, y, gd[1]))
        if k % 2 == 0:
            px += [(x - 1, y - 1, gd[3]), (x - 2, y - 1, gd[4] if k < 2 else gd[3])]
        else:
            px += [(x - 1, y + 1, gd[2]), (x - 2, y + 1, gd[3])]
    px += [(c - 9, t + 3, gd[2]), (c - 10, t + 2, gd[3])]
    draw_after(cv, px)
    return cv


def b_back():
    """From behind: the cape with the house letters in gold, the collar wings, curls and wreath."""
    cv = Cv(BW, BH)
    c, t = 50, BT
    gd, hr = RAMP["gold"], RAMP["hair"]
    b_legs(cv, c, t, back=True)
    # arms hang beside the cape: his left (viewer left) in the drape, his right (viewer right) holds the horn
    b_arm(cv, "armL", [(c - 13, t + 26), (c - 17, t + 37), (c - 18, t + 47)])
    toga_sleeve(cv, "sleeveL", (c - 12, t + 25), (c - 16, t + 30))
    b_hand(cv, c - 18, t + 50, "handL")
    b_arm(cv, "armR", [(c + 13, t + 26), (c + 17, t + 37), (c + 18, t + 47)])
    airhorn(cv, c + 19, t + 51, math.radians(60), back=True)
    b_hand(cv, c + 18, t + 50, "handR")
    # the cape, hanging straight down the back
    pts = [(c - 12, t + 21), (c + 12, t + 21), (c + 15, t + 28), (c + 16, t + 50), (c + 18, t + 70)]
    n = 8
    for k in range(n + 1):
        pts.append((c + 18 - 36 * k / n, t + 72 + (1.5 if k % 2 else -0.5)))
    pts += [(c - 18, t + 70), (c - 16, t + 50), (c - 15, t + 28)]
    m = cv.poly(pts)
    cv.part("cape", m, "cape", edge="dark", rad=10, soft=2.0, cuts=(0.26, 0.50, 0.84))
    cp = RAMP["cape"]
    for fx in (-0.66, -0.25, 0.25, 0.66):
        cv.line(c + fx * 13, t + 42, c + fx * 17, t + 70, cp[1])
    cv.line(c - 12, t + 46, c - 14, t + 68, cp[3])
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if y + 1 < cv.h and not m[y + 1, x] and y > t + 68:
            cv.put(x, y - 1, gd[2] if (x // 2) % 2 else gd[3])
            if x % 4 == 0:
                cv.put(x, y - 2, gd[1])
    # house letters: XI OMEGA XI across the shoulder blades, gold with a dark drop shadow
    gx, gy = c - 9, t + 30
    for i, ch in enumerate("XOX"):
        glyph(cv, gx + i * 6 + 1, gy + 1, ch, cp[0])
    for i, ch in enumerate("XOX"):
        glyph(cv, gx + i * 6, gy, ch, gd[3], gd[2])
    # a gold bar under the letters ("RUSH" stripe)
    cv.hline(c - 10, c + 10, t + 38, gd[2]); cv.hline(c - 9, c + 9, t + 39, gd[1])
    # head from behind
    nk = cv.rect(c - 4, t + 15, c + 4, t + 22)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 1, 0))
    for s_ in (-1, 1):
        cv.part("ear%d" % s_, cv.ell(c + s_ * 7.6, t + 13, 1.7, 2.5), "skin", bias=0.05)
    base = cv.ell(c, t + 7.5, 8.2, 8.6) & cv.half(y=t - 2) & cv.half(y=t + 16, below=False)
    cv.part("hair", base, "hair", edge=None, lv=np.where(base, 1, 0))
    curls = [(-6.4, 2.4, 3.0), (6.4, 2.4, 3.0), (-2.2, 1.1, 3.4), (2.4, 1.3, 3.4), (-7.6, 7.0, 2.8), (7.6, 7.0, 2.8),
             (-3.6, 6.2, 3.0), (3.6, 6.4, 3.0), (-6.2, 11.4, 2.6), (6.2, 11.4, 2.6), (-2.0, 11.0, 2.8), (2.4, 11.2, 2.8),
             (0.2, 14.4, 2.3)]
    for i, (bx, by, r) in enumerate(curls):
        mm = cv.ell(c + bx, t + by, r, r * 0.95) & cv.half(y=t - 2)
        cv.part("curl%d" % i, mm, "hair", edge=hr[1] if i < 8 else hr[0], rad=r, soft=0.6, cuts=(0.20, 0.50, 0.80),
                light=(-0.6, -0.8, 0.5))
        hx, hy = int(round(c + bx - r * 0.35)), int(round(t + by - r * 0.45))
        if cv.own[hy, hx] == cv.names["curl%d" % i]:
            cv.put(hx, hy, hr[4] if r > 2.8 else hr[3])
    # collar wings seen from behind: in front of the nape
    b_collar(cv, c, t, back=True)
    cv.outline()
    # wreath from behind: the two branch tips meet at the back with a gold ribbon bow
    px = []
    for s_ in (-1, 1):
        for k in range(4):
            x = c + s_ * (1.5 + 2.4 * k)
            y = t + 3 + 0.6 * k
            px.append((x, y, gd[1]))
            if k % 2 == 0:
                px += [(x + s_, y - 1, gd[3]), (x + 2 * s_, y - 1, gd[3])]
            else:
                px += [(x + s_, y + 1, gd[2]), (x + 2 * s_, y + 1, gd[3])]
    px += [(c, t + 3, gd[4]), (c, t + 4, gd[2]), (c - 1, t + 5, gd[2]), (c + 1, t + 5, gd[2]), (c - 1, t + 6, gd[1]), (c + 2, t + 6, gd[1])]
    draw_after(cv, px)
    return cv


# ==========================================================================
# ENTRANCE  (cell 12: carried in on the house couch by two brothers)
# ==========================================================================
EW, EH = 176, 164


def bro(cv, c, t, skin, hair, shorts, side, suf, face="grit"):
    """One of the brothers hauling the couch: a plain toga, a purple headband, slides and socks.
    side = +1 when the couch is to his right (viewer right), -1 when it is to his left."""
    sk, hr, tg, gd = RAMP[skin], RAMP[hair], RAMP["toga"], RAMP["gold"]
    b_legs(cv, c, t + 2, spread=2, skin=skin, shorts=shorts, suf=suf, socks=False)
    body = cv.poly([(c - 9, t + 22), (c + 9, t + 22), (c + 13, t + 25), (c + 14, t + 31), (c + 12, t + 41),
                    (c + 11, t + 47), (c + 12, t + 54), (c - 12, t + 54), (c - 11, t + 47), (c - 12, t + 41),
                    (c - 14, t + 31), (c - 13, t + 25)])
    cv.part("chest" + suf, body, skin, rad=7, soft=1.4, cuts=(0.24, 0.48, 0.84))
    k = -side
    toga = cv.poly([(c + k * 2, t + 22), (c + k * 9, t + 22), (c + k * 13, t + 25), (c + k * 14, t + 31),
                    (c + k * 12, t + 41), (c + k * 11, t + 47), (c + k * 12, t + 56), (c - k * 12, t + 56),
                    (c - k * 11, t + 47), (c - k * 12, t + 39), (c - k * 6, t + 34), (c - k * 1, t + 29)]) & cv.half(y=t + 21)
    cv.part("toga" + suf, toga, "toga", rad=6, soft=1.4, cuts=(0.24, 0.48, 0.82))
    for j in range(3):
        cv.line(c + k * (7 - j), t + 28 + j * 6, c - k * (9 - j), t + 40 + j * 6, tg[1])
    # both arms reach down for the couch end in front of him (hands drawn after the couch)
    for s_ in (-1, 1):
        b_arm(cv, "arm%d%s" % (s_, suf), [(c + s_ * 12, t + 27), (c + s_ * 13, t + 38), (c + s_ * 8, t + 48)], skin=skin)
    # head
    nk = cv.rect(c - 3, t + 17, c + 3, t + 23)
    cv.part("neck" + suf, nk, skin, edge=None, lv=np.where(nk, 1, 0) + np.where(nk & (cv.Y > t + 21), 1, 0))
    for s_ in (-1, 1):
        cv.part("ear%d%s" % (s_, suf), cv.ell(c + s_ * 7.4, t + 13, 1.7, 2.4), skin, bias=0.05)
    f = cv.ell(c, t + 12, 7.0, 7.9) | cv.poly([(c - 6.8, t + 13), (c + 6.8, t + 13), (c + 6, t + 18), (c + 2.5, t + 21),
                                                (c - 2.5, t + 21), (c - 6, t + 18)])
    cv.part("face" + suf, f, skin, rad=6, soft=1.4, cuts=(0.30, 0.52, 0.86))
    if hair == "hairB":
        # shaggy ginger
        cap = cv.ell(c, t + 7, 8.2, 6.8) & cv.half(y=t + 9, below=False) & cv.half(y=t - 1)
        cap |= cv.poly([(c - 8, t + 6), (c - 3, t + 6), (c - 6, t + 10)]) | cv.poly([(c + 1, t + 6), (c + 8, t + 6), (c + 7, t + 10)])
        cv.part("hair" + suf, cap, hair, rad=4, soft=0.9, cuts=(0.26, 0.5, 0.82), light=(-0.6, -0.8, 0.5))
        for (x0, y0, x1, y1) in ((c - 5, t + 2, c - 2, t + 6), (c + 1, t + 1, c + 4, t + 6), (c - 1, t + 3, c, t + 7)):
            cv.line(x0, y0, x1, y1, hr[1])
        cv.line(c - 6, t + 2, c - 3, t + 1, hr[4])
    else:
        # tight fade
        cap = cv.ell(c, t + 7.5, 7.6, 6.6) & cv.half(y=t + 9, below=False) & cv.half(y=t + 1)
        cv.part("hair" + suf, cap, hair, rad=4, soft=0.9, cuts=(0.3, 0.55, 0.85), light=(-0.6, -0.8, 0.5))
        for x in range(c - 7, c + 8):
            for y in range(t + 7, t + 10):
                if cv.own[y, x] == cv.names["hair" + suf] and (x + y) % 2 == 0:
                    cv.put(x, y, hr[2])
    # purple headband with a gold stripe
    hb = cv.rect(c - 7.5, t + 5.6, c + 7.5, t + 7.4) & (cv.ell(c, t + 9, 8.2, 9) )
    cv.part("band" + suf, hb, "cape", edge="ink", lv=np.where(hb, 2, 0) + np.where(hb & (cv.X < c - 3), 1, 0))
    cv.hline(c - 6, c + 6, t + 6, RAMP["cape"][3])
    ey = t + 11
    for s_ in (-1, 1):
        ex = c + s_ * 3 - (1 if s_ < 0 else 0)
        if face == "grit":           # straining: eyes squeezed
            cv.hline(ex, ex + 1, ey + 1, EYE); cv.put(ex + (1 if s_ < 0 else 0), ey, EYE)
        else:
            cv.put(ex, ey, EYE); cv.put(ex + 1, ey, EYE); cv.put(ex, ey + 1, EYE); cv.put(ex + 1, ey + 1, EYE)
            cv.put(ex, ey, WHITE)
        for kk in range(3):
            cv.put(c + s_ * (2 + kk), ey - 2 - (1 if kk == 1 else 0) + (1 if face == "grit" and kk == 0 else 0), hr[0])
    cv.puts([(c, t + 13), (c, t + 14)], sk[3]); cv.puts([(c + 1, t + 13), (c + 1, t + 14), (c - 1, t + 15), (c, t + 15)], sk[1])
    my = t + 17
    if face == "grit":
        cv.hline(c - 4, c + 4, my, MOUTH); cv.hline(c - 3, c + 3, my + 1, TEETH)
        for x in range(c - 2, c + 3, 2):
            cv.put(x, my + 1, TEETH2)
        cv.hline(c - 4, c + 4, my + 2, MOUTH); cv.put(c - 5, my + 1, MOUTH); cv.put(c + 5, my + 1, MOUTH)
    else:                            # whooping
        for dy, w in ((0, 2), (1, 3), (2, 3), (3, 2)):
            cv.hline(c - w, c + w, my + dy, MOUTH)
        cv.hline(c - 2, c + 2, my, TEETH); cv.hline(c - 1, c + 1, my + 3, TONGUE)
    if hair == "hairB":
        for (x, y) in ((c - 5, t + 14), (c - 4, t + 15), (c + 4, t + 14), (c + 5, t + 15)):
            cv.put(x, y, mix(sk[2], (176, 96, 60), 0.5))


def couch(cv, x0, x1, yb):
    """The house couch: a saggy green plaid three-seater with rolled arms, wooden stub feet and a
    duct-tape patch.  yb = bottom of the skirt."""
    pl, wd = RAMP["plaid"], RAMP["wood"]
    for x in (x0 + 5, x1 - 5, (x0 + x1) // 2):
        m = cv.rect(x - 1.5, yb, x + 1.5, yb + 3)
        cv.part("foot%d" % x, m, "wood", edge="ink", lv=np.where(m, 2, 0) + np.where(m & (cv.X < x), 1, 0))
    back = cv.rect(x0 + 6, yb - 36, x1 - 6, yb - 18) & (cv.ell((x0 + x1) / 2, yb - 18, (x1 - x0) / 2 - 4, 22) | cv.half(y=yb - 24))
    cv.part("couchback", back, "plaid", rad=8, soft=1.6, cuts=(0.26, 0.5, 0.84))
    skirt = cv.rect(x0 + 2, yb - 14, x1 - 2, yb)
    cv.part("skirt", skirt, "plaid", rad=6, soft=1.4, cuts=(0.24, 0.48, 0.84))
    cush = cv.empty()
    n = 3
    w = (x1 - x0 - 20) / n
    for i in range(n):
        a = x0 + 10 + i * w
        m = cv.rect(a + 0.5, yb - 22, a + w - 0.5, yb - 13) & cv.ell(a + w / 2, yb - 17.5, w / 2 + 1.5, 7)
        cv.part("cush%d" % i, m, "plaid", rad=5, soft=1.0, cuts=(0.22, 0.46, 0.80))
        cush |= m
    for side, xa in ((-1, x0), (1, x1)):
        arm = cv.rect(min(xa, xa - side * 11), yb - 26, max(xa, xa - side * 11), yb) | cv.ell(xa - side * 5.5, yb - 26, 6.5, 4.5)
        cv.part("arm%d" % side, arm, "plaid", rad=6, soft=1.2, cuts=(0.24, 0.48, 0.84))
        cv.part("roll%d" % side, cv.ell(xa - side * 5.5, yb - 26, 4.5, 3.4), "plaid", edge="dark", rad=3, soft=0.8,
                cuts=(0.2, 0.45, 0.8))
    # plaid: a gold-ish check over the green, every 6px each way, only on lit/mid tones
    for y in range(cv.h):
        for x in range(cv.w):
            o = cv.own[y, x]
            nm = [k for k, v in cv.names.items() if v == o]
            if not nm or not (nm[0].startswith(("couch", "skirt", "cush", "arm-", "arm1", "roll"))):
                continue
            col = cv.get(x, y)
            if col == pl[0]:
                continue
            if x % 6 == 0 or y % 6 == 0:
                cv.put(x, y, mix(col, (200, 150, 70), 0.35))
            if x % 6 == 0 and y % 6 == 0:
                cv.put(x, y, mix(col, (120, 40, 40), 0.4))
    # duct tape patch on the skirt
    tx, ty = x0 + 20, yb - 9
    m = cv.poly([(tx, ty), (tx + 8, ty - 2), (tx + 9, ty + 3), (tx + 1, ty + 5)])
    cv.part("tape", m, "metal" if "metal" in RAMP else "plastic", edge="dark", rad=2, soft=0.5)
    cv.line(tx + 2, ty + 1, tx + 7, ty, RAMP["plastic"][4])


def entrance():
    """Carried in on the house couch: two brothers haul it (one straining, one whooping) while
    Tanner stands on the cushions, cape streaming, airhorn hoisted and blasting, pointing at you."""
    cv = Cv(EW, EH)
    g = EH - 1
    tb = EH - 80                        # the brothers (78px)
    x0, x1 = 34, 142
    bB, bC = x0 + 6, x1 - 6
    bro(cv, bB, tb, "skinB", "hairB", "khaki", 1, "B", face="grit")
    bro(cv, bC, tb, "skinC", "hairC", "sky", -1, "C", face="whoop")
    yb = tb + 50
    couch(cv, x0, x1, yb)
    # their hands hook under the couch arms (drawn over the couch)
    for s_ in (-1, 1):
        b_hand(cv, bB + s_ * 7.5, yb - 1, "gripB%d" % s_, rx=2.6, ry=2.6, skin="skinB")
        b_hand(cv, bC + s_ * 7.5, yb - 1, "gripC%d" % s_, rx=2.6, ry=2.6, skin="skinC")
    # ---- Tanner on the cushions ----
    c = 88
    ys = yb - 21                        # soles on the cushion tops
    t = ys - 82
    b_cape(cv, c, t, flare=(22, 34), hem=74, sway=5)
    b_legs(cv, c, t, spread=4)
    b_torso(cv, c, t)
    b_arm(cv, "armL", [(c - 13, t + 26), (c - 21, t + 16), (c - 24, t + 6)])
    mouth = airhorn(cv, c - 25, t + 0, math.radians(-75))
    b_hand(cv, c - 24, t + 2, "handL")
    b_arm(cv, "armR", [(c + 13, t + 27), (c + 21, t + 31), (c + 28, t + 27)])
    toga_sleeve(cv, "sleeveR", (c + 12, t + 25), (c + 17, t + 30))
    b_hand(cv, c + 29, t + 26, "handR", rx=2.6, ry=2.4)
    fing = cv.capsule(c + 30, t + 25, c + 35, t + 23, 1.2)
    cv.part("finger", fing, "skin", edge="ink", noedge=("handR",), rad=1.2, soft=0.4, bias=0.1)
    b_cord(cv, c, t)
    b_collar(cv, c, t, sway=1)
    b_head_front(cv, c, t, "talk")
    cv.outline()
    draw_after(cv, wreath_px(c, t))
    blast(cv, mouth[0], mouth[1], math.radians(-75), n=3, reach=12, spread=0.7)
    # confetti in house colours
    rng = np.random.default_rng(7)
    cols = [RAMP["gold"][3], RAMP["cape"][3], RAMP["gold"][2], RAMP["lining"][3], WHITE]
    for k in range(26):
        x, y = int(rng.integers(4, EW - 4)), int(rng.integers(2, yb - 30))
        if cv.alpha[max(0, y - 1):y + 2, max(0, x - 1):x + 2].any():
            continue
        cv.put(x, y, cols[k % len(cols)])
        if k % 3 == 0:
            cv.put(x + 1, y + (1 if k % 2 else -1), cols[k % len(cols)])
    sparkle(cv, c - 6, t + 17, big=False)
    sparkle(cv, c + 40, t + 14)
    return cv, ys


# ==========================================================================
# WORLD  (52 px standing height, redrawn small -- not scaled)
# ==========================================================================
WW, WH = 64, 56
WT = WH - 52


def mirror_rows(half):
    return [h + h[::-1] for h in half]


# front head, col 0 = c-8, row 0 = t (crest of the curls).  Built from left halves, mirrored.
W_HEAD = mirror_rows([
    "..KKK.KK",
    ".K343K43",
    "K2332123",
    "KYg1YgGy",
    "K1G2112Y",
    "K11ddsl1",
    "K1dsBBll",
    "KdKsWEll",
    "KdKsdEsl",
    "..Krsssl",
    "..KsMTTT",
    "..KdsMoo",
    "...KdssL",
    "....KKdd",
])
W_FACE = {
    "idle": {},
    "talk": {10: "..KMTTTTTTTTMK..", 11: "..KdMMooooMMdK..", 12: "...KdMMMMMMdK..."},
    "tell": {6: "K1dsslllllllsd1K", 7: "KdKsEEllllEEsKdK", 8: "KdKsssslldsssKdK",
             10: "..KMTTTTTTTTMK..", 11: "..KdMttttttMdK..", 12: "...KdsMMMMsdK..."},
    "hit":  {6: "K1dBBsllllsBBd1K", 7: "KdKsWWllllWWsKdK", 8: "KdKsEdslldsdEKdK",
             10: "..KssssMMssssK..", 11: "..KdsssMMsssdK..", 12: "...KdssLLssdK..."},
    "blink": {7: "KdKsssllllsssKdK", 8: "KdKsEEslldEEsKdK"},
    "glance": {7: "KdKsWEllllWEsKdK", 8: "KdKsdEslldsdEKdK"},
    "up":    {7: "KdKsEWllllEWsKdK", 8: "KdKsddslldsdsKdK"},
}
W_BACK = mirror_rows([
    "..KKK.KK",
    ".K343K43",
    "K2332123",
    "KYg1YgYG",
    "K1G21212",
    "Kd121221",
    "Kd212112",
    "KdK12121",
    "KdK21212",
    "..K12121",
    "..K21212",
    "..KK1212",
    "...Kdddd",
])
# profile facing right, col 0 = c-8, row 0 = t
W_SIDE = [
    "...KKK.KKKK.....",
    "..K343K43343K...",
    ".K23321233212K..",
    "K2Yg1YgYgGyYgYK.",
    "K12G2112YG21ddK.",
    "K1121221dlsssK..",
    "K21122121dslllK.",
    "K1212211dsllBBK.",
    "K121KKdsllllWEK.",
    "K12KsddsllllsssK",
    "K21KdxdssssssslK",
    ".K1KKddssssssdK.",
    "..KKddsssssMTTK.",
    "...KddssssssMoK.",
    "....KddsssssLK..",
    ".....KKddddKK...",
]


def w_hand(cv, x, y, name, r=1.8, skin="skin"):
    m = cv.ell(x, y, r, r)
    cv.part(name, m, skin, edge="ink", lv=np.where(m, 3, 0) - np.where(m & (cv.X > x) & (cv.Y > y - 1), 1, 0))
    return m


def w_arm(cv, name, pts, r0=2.3, r1=1.9, skin="skin"):
    m = cv.empty()
    n = len(pts) - 1
    for k, ((a, b), (c_, d)) in enumerate(zip(pts, pts[1:])):
        m |= cv.capsule(a, b, c_, d, r0 + (r1 - r0) * k / n, r0 + (r1 - r0) * (k + 1) / n)
    cv.part(name, m, skin, edge="dark", rad=2, soft=0.7, cuts=(0.28, 0.52, 0.88))
    return m


def w_sleeve(cv, name, p0, p1, r=2.7):
    m = cv.capsule(p0[0], p0[1], p1[0], p1[1], r, r - 0.3)
    cv.part(name, m, "toga", edge="dark", rad=2, soft=0.6, cuts=(0.24, 0.48, 0.82))
    return m


def w_cape(cv, c, t, flare=(15, 15), sway=0, hem=48, back=False):
    fl, fr = flare
    pts = [(c - 7, t + 14), (c + 7, t + 14), (c + 10, t + 19), (c + fr * 0.8 + sway, t + 32), (c + fr + sway * 1.5, t + hem - 1)]
    n = 6
    for k in range(n + 1):
        pts.append((c + fr + sway * 1.5 - (fl + fr) * k / n, t + hem + (1 if k % 2 else 0)))
    pts += [(c - fl + sway * 1.5, t + hem - 1), (c - fl * 0.8 + sway, t + 32), (c - 10, t + 19)]
    m = cv.poly(pts)
    cv.part("cape", m, "cape", edge="dark", rad=6, soft=1.4, cuts=(0.26, 0.50, 0.84))
    cp, gd = RAMP["cape"], RAMP["gold"]
    for fx in (-0.6, 0.6):
        cv.line(c + fx * 9, t + 22, c + fx * (fl if fx < 0 else fr) + sway, t + hem - 2, cp[1])
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if y + 1 < cv.h and not m[y + 1, x] and y > t + hem - 3:
            cv.put(x, y - 1, gd[2] if x % 2 else gd[3])
    if not back:
        for s_, f in ((-1, fl), (1, fr)):
            for y in range(t + 22, t + hem - 1):
                u = (y - (t + 22)) / max(1, hem - 23)
                x = int(round(c + s_ * (10 + (f - 10) * u) + sway * u * 1.5)) - s_
                if m[y, x]:
                    cv.put(x, y, RAMP["lining"][2])
    return m


def w_collar(cv, c, t, back=False, sway=0):
    gd = RAMP["gold"]
    for s_ in (-1, 1):
        m = cv.poly([(c + s_ * 3, t + 14), (c + s_ * 4, t + 9), (c + s_ * 6, t + 6), (c + s_ * 9.5 + sway, t + 4),
                     (c + s_ * 10 + sway, t + 10), (c + s_ * 8.5, t + 15)])
        cv.part("collar%d" % s_, m, "cape", edge="dark", rad=2, soft=0.6, cuts=(0.28, 0.52, 0.86))
        if back:
            continue
        inner = ndi.binary_erosion(m) & (cv.Y > t + 5)
        cv.part("lining%d" % s_, inner, "lining", edge=None, rad=2, soft=0.5, cuts=(0.28, 0.52, 0.86))
        top = [(x, min(y for y in range(cv.h) if inner[y, x])) for x in range(cv.w) if inner[:, x].any()]
        for x, y in top:
            cv.put(x, y, gd[3] if x % 2 else gd[2])


def w_legs(cv, c, t, back=False, spread=0):
    gd = RAMP["gold"]
    for s_ in (-1, 1):
        o = s_ * spread
        sh = cv.poly([(c + s_ * 0.5, t + 31), (c + s_ * 7.5, t + 31), (c + s_ * 7.8 + o * 0.3, t + 37), (c + s_ * 1.4, t + 37)])
        cv.part("shorts%d" % s_, sh, "shorts", rad=3, soft=0.8, cuts=(0.30, 0.56, 0.9))
        leg = cv.poly([(c + s_ * 1.8 + o * 0.3, t + 37), (c + s_ * 6.8 + o * 0.3, t + 37), (c + s_ * 6.2 + o, t + 45),
                       (c + s_ * 2.4 + o, t + 45)])
        cv.part("leg%d" % s_, leg, "skin", rad=2, soft=0.7, cuts=(0.28, 0.52, 0.86))
        sx = c + s_ * 4.2 + o
        sock = cv.rect(sx - 2, t + 45, sx + 2, t + 48)
        cv.part("sock%d" % s_, sock, "sock", edge="dark", lv=np.where(sock, 3, 0) - np.where(sock & (cv.X > sx), 1, 0))
        cv.hline(sx - 1, sx + 1, t + 46, RAMP["cape"][2])
        sl = cv.ell(sx + s_ * 0.3, t + 50.3, 3.7, 1.8) & cv.half(y=t + 51, below=False) & cv.half(y=t + 49)
        cv.part("shoe%d" % s_, sl, "slide", rad=2, soft=0.5, cuts=(0.3, 0.55, 0.85))
        if not back:
            cv.put(sx, t + 49, gd[3])
    cv.vline(c, t + 33, t + 36, RAMP["shorts"][0])


def w_torso(cv, c, t, back=False):
    tg, gd, sk = RAMP["toga"], RAMP["gold"], RAMP["skin"]
    body = cv.poly([(c - 5, t + 13), (c + 5, t + 13), (c + 8.5, t + 15), (c + 9, t + 19), (c + 8, t + 25), (c + 7, t + 29),
                    (c + 7.5, t + 33), (c - 7.5, t + 33), (c - 7, t + 29), (c - 8, t + 25), (c - 9, t + 19), (c - 8.5, t + 15)])
    cv.part("chest", body, "skin", rad=4, soft=1.0, cuts=(0.24, 0.48, 0.84))
    k = -1 if back else 1
    toga = cv.poly([(c + k * 1, t + 13), (c + k * 5, t + 13), (c + k * 8.5, t + 15), (c + k * 9, t + 19), (c + k * 8, t + 25),
                    (c + k * 7, t + 29), (c + k * 8, t + 36), (c - k * 8, t + 36), (c - k * 7, t + 29), (c - k * 8, t + 24),
                    (c - k * 4, t + 21), (c - k * 1, t + 18)])
    cv.part("toga", toga, "toga", rad=4, soft=1.2, cuts=(0.24, 0.48, 0.82))
    cv.line(c + k * 5, t + 17, c - k * 6, t + 25, tg[1]); cv.line(c + k * 6, t + 22, c - k * 5, t + 30, tg[1])
    for x in range(c - 8, c + 9):
        cl = [y for y in range(t + 30, t + 38) if toga[y, x]]
        if cl:
            cv.put(x, max(cl) - 1, gd[2] if x % 3 else gd[3])
    for x in range(c - 7, c + 8):
        y = t + 28
        if cv.own[y, x] in (cv.names["toga"], cv.names["chest"]):
            cv.put(x, y, gd[3] if x % 2 else gd[2])
    cv.put(c - 4 * k, t + 29, gd[2]); cv.put(c - 4 * k, t + 30, gd[1])
    if not back:
        cv.line(c - 7, t + 19, c - 4, t + 20, sk[1])
        cv.put(c + 5, t + 14, gd[3]); cv.put(c + 5, t + 15, gd[2]); cv.put(c + 4, t + 14, gd[4])
        # cape cord across the chest
        for x in range(c - 7, c + 5):
            u = (x - (c - 7)) / 12
            cv.put(x, int(round(t + 15 + 1.3 * math.sin(math.pi * u))), gd[2] if x % 2 else gd[3])


def w_head(cv, c, t, rows, dx=0):
    nk = cv.rect(c - 3, t + 11, c + 2, t + 15)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 2, 0) - np.where(nk & (cv.Y <= t + 13), 1, 0))
    paint_map(cv, c - 8 + dx, t, rows, head_pal(), name="head")


def w_front(pose):
    cv = Cv(WW, WH)
    c, t = 32, WT
    sway = {"hit": 2, "talk": 1}.get(pose, 0)
    w_cape(cv, c, t, sway=sway)
    w_legs(cv, c, t, spread=1 if pose in ("talk", "tell") else 0)
    w_torso(cv, c, t)
    mouth = None
    # viewer-left arm (bare) with the airhorn
    if pose in ("idle", "blink", "glance", "flex", "crown"):
        w_arm(cv, "armL", [(c - 8, t + 16), (c - 10.5, t + 23), (c - 11, t + 29)])
        airhorn(cv, c - 12, t + 32, math.radians(115), s=0.8)
        w_hand(cv, c - 11, t + 31, "handL")
    elif pose == "talk":
        w_arm(cv, "armL", [(c - 8, t + 16), (c - 12.5, t + 21), (c - 11.5, t + 16)])
        mouth = airhorn(cv, c - 11.5, t + 13, math.radians(-110), s=0.8)
        w_hand(cv, c - 11.5, t + 14.5, "handL")
    elif pose == "tell":
        w_arm(cv, "armL", [(c - 8, t + 16), (c - 13, t + 13), (c - 15.5, t + 9)])
        mouth = airhorn(cv, c - 17, t + 8, math.radians(-150), s=0.8)
        w_hand(cv, c - 15.5, t + 8.5, "handL")
    elif pose == "hit":
        w_arm(cv, "armL", [(c - 8, t + 16), (c - 12, t + 19), (c - 15, t + 17)])
        w_hand(cv, c - 16, t + 16.5, "handL")
        airhorn(cv, c - 18, t + 10, math.radians(-140), s=0.8, name="hornfly")
    # viewer-right arm under the drape
    if pose in ("idle", "blink", "glance", "tell"):
        w_arm(cv, "armR", [(c + 8, t + 16), (c + 13, t + 22), (c + 8.5, t + 27)])
        w_sleeve(cv, "sleeveR", (c + 7.5, t + 15), (c + 10, t + 18.5))
        w_hand(cv, c + 8, t + 27.5, "handR")
    elif pose == "talk":
        w_arm(cv, "armR", [(c + 8, t + 16), (c + 12.5, t + 20), (c + 16, t + 18)])
        w_sleeve(cv, "sleeveR", (c + 7.5, t + 15), (c + 10.5, t + 18.5))
        w_hand(cv, c + 16.5, t + 17.5, "handR")
        fing = cv.capsule(c + 17.5, t + 17, c + 20, t + 16, 0.8)
        cv.part("finger", fing, "skin", edge="ink", noedge=("handR",), lv=np.where(fing, 3, 0))
    elif pose == "hit":
        w_arm(cv, "armR", [(c + 8, t + 16), (c + 12, t + 19), (c + 14, t + 14)])
        w_sleeve(cv, "sleeveR", (c + 7.5, t + 15), (c + 10.5, t + 18))
        w_hand(cv, c + 14, t + 12.5, "handR")
    elif pose == "flex":
        # pose2: a big flex of the toga'd arm, fist up by the collar
        w_arm(cv, "armR", [(c + 8, t + 16), (c + 14.5, t + 16.5), (c + 14, t + 10)], r0=2.7, r1=2.0)
        w_sleeve(cv, "sleeveR", (c + 7.5, t + 15), (c + 11, t + 16))
        w_hand(cv, c + 13.5, t + 8.5, "handR", r=2.0)
    elif pose == "crown":
        # pose1: straightens his laurel wreath
        w_arm(cv, "armR", [(c + 8, t + 16), (c + 13.5, t + 12), (c + 10.5, t + 5)])
        w_sleeve(cv, "sleeveR", (c + 7.5, t + 15), (c + 11, t + 14))
    w_collar(cv, c, t, sway=1 if pose == "hit" else 0)
    face = {"idle": "idle", "talk": "talk", "tell": "tell", "hit": "hit", "blink": "blink", "glance": "glance",
            "crown": "glance", "flex": "up"}[pose]
    rows = list(W_HEAD)
    for k, r in W_FACE.get(face, {}).items():
        rows[k] = r
    if pose == "hit":       # wreath knocked askew: right half one row lower
        rows[3] = rows[3][:8] + rows[2][8:]
        rows[4] = rows[4][:8] + "Y2g1YgYK"
    w_head(cv, c + (1 if pose == "hit" else 0), t, rows)
    if pose == "crown":
        w_hand(cv, c + 9.5, t + 3.5, "handR")
    cv.outline()
    if pose == "tell" and mouth:
        sparkle(cv, int(mouth[0]) + 3, int(mouth[1]) - 2, big=False)
    if pose == "hit":
        cv.puts([(c - 7, t + 1), (c - 8, t + 2), (c - 7, t + 2), (c - 7, t + 3)], SWEAT)
        cv.puts([(c + 11, t - 0), (c + 12, t + 1)], RAMP["gold"][3])
    return cv


def w_side():
    cv = Cv(WW, WH)
    c, t = 30, WT
    gd, tg = RAMP["gold"], RAMP["toga"]
    m = cv.poly([(c - 3, t + 13), (c + 1, t + 14), (c - 1, t + 21), (c - 5, t + 32), (c - 8, t + 48), (c - 12, t + 47.5),
                 (c - 15, t + 48), (c - 16, t + 45), (c - 11, t + 31), (c - 6, t + 19)])
    cv.part("cape", m, "cape", edge="dark", rad=4, soft=1.2, cuts=(0.26, 0.50, 0.84))
    cv.line(c - 4, t + 19, c - 11, t + 45, RAMP["cape"][1])
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if y + 1 < cv.h and not m[y + 1, x] and y > t + 44:
            cv.put(x, y - 1, gd[2] if x % 2 else gd[3])
    col = cv.poly([(c - 3, t + 14), (c - 6, t + 8), (c - 6.5, t + 4), (c - 4, t + 5), (c - 1, t + 13)])
    cv.part("collar", col, "cape", edge="dark", rad=2, soft=0.5)
    for side, dx, cuts in ((0, -2, (0.45, 0.7, 0.95)), (1, 1, (0.30, 0.56, 0.9))):
        x = c + dx
        sh = cv.poly([(x - 3.5, t + 31), (x + 3.5, t + 31), (x + 4, t + 37), (x - 3.5, t + 37)])
        cv.part("shorts%d" % side, sh, "shorts", rad=2, cuts=cuts)
        leg = cv.poly([(x - 2.5, t + 37), (x + 3, t + 37), (x + 2.2, t + 45), (x - 1.6, t + 45)])
        cv.part("leg%d" % side, leg, "skin", rad=2, cuts=cuts)
        sock = cv.rect(x - 1.5, t + 45, x + 2, t + 48)
        cv.part("sock%d" % side, sock, "sock", edge="dark", lv=np.where(sock, 3 - (side == 0), 0))
        cv.hline(x - 1, x + 1, t + 46, RAMP["cape"][2])
        sl = cv.ell(x + 1.5, t + 50.3, 4.0, 1.8) & cv.half(y=t + 51, below=False) & cv.half(y=t + 49)
        cv.part("shoe%d" % side, sl, "slide", rad=2, cuts=cuts)
    body = cv.poly([(c - 4, t + 13), (c + 2, t + 13), (c + 5.5, t + 17), (c + 5.5, t + 23), (c + 4.5, t + 28), (c + 5, t + 36),
                    (c - 4.5, t + 36.5), (c - 4.5, t + 28), (c - 5, t + 21), (c - 5, t + 16)])
    cv.part("toga", body, "toga", rad=4, soft=1.2, cuts=(0.24, 0.48, 0.82))
    cv.line(c + 3, t + 18, c - 4, t + 22, tg[1]); cv.line(c + 3, t + 24, c - 4, t + 28, tg[1])
    for x in range(c - 4, c + 6):
        cl = [y for y in range(t + 30, t + 38) if body[y, x]]
        if cl:
            cv.put(x, max(cl) - 1, gd[2] if x % 3 else gd[3])
        if body[t + 28, x]:
            cv.put(x, t + 28, gd[3] if x % 2 else gd[2])
    w_arm(cv, "arm", [(c, t + 16), (c + 0.5, t + 23), (c + 3, t + 28)])
    w_sleeve(cv, "sleeve", (c - 0.5, t + 15), (c, t + 18.5))
    airhorn(cv, c + 6, t + 28.5, math.radians(-10), s=0.8)
    w_hand(cv, c + 3.5, t + 29, "hand")
    nk = cv.rect(c - 2, t + 11, c + 1, t + 15)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 1, 0))
    paint_map(cv, c - 8, t, W_SIDE, head_pal(), name="head")
    cv.outline()
    return cv


def w_back():
    cv = Cv(WW, WH)
    c, t = 32, WT
    gd, cp = RAMP["gold"], RAMP["cape"]
    w_legs(cv, c, t, back=True)
    w_arm(cv, "armL", [(c - 8, t + 16), (c - 10.5, t + 23), (c - 11, t + 29)])
    w_sleeve(cv, "sleeveL", (c - 7.5, t + 15), (c - 10, t + 18.5))
    w_hand(cv, c - 11, t + 31, "handL")
    w_arm(cv, "armR", [(c + 8, t + 16), (c + 10.5, t + 23), (c + 11, t + 29)])
    airhorn(cv, c + 12, t + 32, math.radians(65), s=0.8, back=True)
    w_hand(cv, c + 11, t + 31, "handR")
    pts = [(c - 7, t + 13), (c + 7, t + 13), (c + 9, t + 18), (c + 10, t + 31), (c + 11, t + 43)]
    n = 6
    for k in range(n + 1):
        pts.append((c + 11 - 22 * k / n, t + 44 + (1 if k % 2 else 0)))
    pts += [(c - 11, t + 43), (c - 10, t + 31), (c - 9, t + 18)]
    m = cv.poly(pts)
    cv.part("cape", m, "cape", edge="dark", rad=6, soft=1.4, cuts=(0.26, 0.50, 0.84))
    for fx in (-0.6, 0.0, 0.6):
        cv.line(c + fx * 8, t + 26, c + fx * 10, t + 42, cp[1])
    ys, xs = np.nonzero(m)
    for y, x in zip(ys, xs):
        if y + 1 < cv.h and not m[y + 1, x] and y > t + 41:
            cv.put(x, y - 1, gd[2] if x % 2 else gd[3])
    # house letters, 3x5 glyphs
    for i, ch in enumerate("xox"):
        glyph(cv, c - 6 + i * 4 + 1, t + 19 + 1, ch, cp[0])
    for i, ch in enumerate("xox"):
        glyph(cv, c - 6 + i * 4, t + 19, ch, gd[3], gd[2])
    w_collar(cv, c, t, back=True)
    nk = cv.rect(c - 3, t + 10, c + 2, t + 14)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 1, 0))
    paint_map(cv, c - 8, t, W_BACK, head_pal(), name="head")
    # collar wings sit in front of the nape from behind
    for s_ in (-1, 1):
        mm = cv.poly([(c + s_ * 3, t + 14), (c + s_ * 4, t + 9), (c + s_ * 6, t + 6), (c + s_ * 9.5, t + 4),
                      (c + s_ * 10, t + 10), (c + s_ * 8.5, t + 15)]) & ~cv.rect(c - 2, t, c + 1, t + 12)
        cv.part("collarB%d" % s_, mm, "cape", edge="dark", rad=2, soft=0.5)
    cv.outline()
    return cv


# ==========================================================================
# PORTRAITS  (64 x 64, head and shoulders)
# ==========================================================================
PW = PH = 64


def p_eye(cv, ex, ey, expr, side):
    """7x5 pixel-map eye; (ex, ey) is the top-left of the viewer-left eye, the right is mirrored."""
    sk = RAMP["skin"]
    maps = {
        "neutral": [".KKKKK.",
                    "KWHIIWK",
                    ".WIPIW.",
                    "..SSS..",
                    "......."],
        "warm":    ["..KKK..",
                    ".KKKKK.",
                    "KK...KK",
                    ".......",
                    ".SSSSS."],
        "concern": ["..KKKK.",
                    ".KHIIWK",
                    ".WIPIW.",
                    "..SSS..",
                    "......."],
        "surprised": ["..KKK..",
                      ".KWWWK.",
                      "KWHIIWK",
                      "KWIPIWK",
                      ".KWWWK.",
                      "..SSS.."],
        "blink":   ["......",
                    ".......",
                    "KKKKKKK",
                    ".SSSSS.",
                    "......."],
    }
    pal = {"K": EYE, "I": IRIS, "P": EYE, "H": WHITE, "W": SCLERA, "S": sk[1]}
    rows = maps[expr]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x = ex + i if side < 0 else ex + (6 - i)
            cv.put(x, ey + j, pal[ch])
    # keep the catch-light on the upper-left in both eyes
    for j, row in enumerate(rows):
        if "H" in row and side > 0:
            i = row.index("H")
            cv.put(ex + (6 - i), ey + j, IRIS)
            cv.put(ex + (6 - i) - 2, ey + j, WHITE)
            break


def p_mouth(cv, c, my, expr, talk=False):
    sk = RAMP["skin"]
    if expr == "neutral":
        if not talk:
            # the closed-lip-but-still-teeth power smile
            cv.hline(c - 5, c + 5, my, MOUTH)
            cv.put(c - 6, my - 1, MOUTH); cv.put(c + 6, my - 1, MOUTH); cv.put(c + 7, my - 2, MOUTH)
            cv.hline(c - 4, c + 4, my, TEETH); cv.put(c + 3, my, TEETH2)
            cv.hline(c - 4, c + 4, my + 1, MOUTH)
            cv.hline(c - 2, c + 2, my + 2, LIP)
        else:
            cv.hline(c - 5, c + 5, my, MOUTH)
            cv.put(c - 6, my - 1, MOUTH); cv.put(c + 6, my - 1, MOUTH); cv.put(c + 7, my - 2, MOUTH)
            cv.hline(c - 4, c + 4, my, TEETH); cv.put(c + 3, my, TEETH2)
            cv.hline(c - 4, c + 4, my + 1, MOUTH)
            cv.hline(c - 3, c + 3, my + 2, MOUTH); cv.hline(c - 1, c + 2, my + 2, TONGUE)
            cv.hline(c - 2, c + 2, my + 3, LIP)
    elif expr == "warm":
        drop = 2 if talk else 0
        cv.hline(c - 7, c + 7, my - 1, MOUTH)
        cv.put(c - 8, my - 2, MOUTH); cv.put(c + 8, my - 2, MOUTH); cv.put(c - 9, my - 3, sk[1]); cv.put(c + 9, my - 3, sk[1])
        cv.hline(c - 6, c + 6, my, TEETH)
        for x in (c - 3, c, c + 3):
            cv.put(x, my, TEETH2)
        cv.put(c - 7, my, MOUTH); cv.put(c + 7, my, MOUTH)
        for k in range(1, 2 + drop):
            cv.hline(c - 6 + (k > 1), c + 6 - (k > 1), my + k, MOUTH)
        cv.hline(c - 3, c + 3, my + 1 + drop, TONGUE)
        cv.hline(c - 5, c + 5, my + 2 + drop, TEETH); cv.put(c - 6, my + 2 + drop, MOUTH); cv.put(c + 6, my + 2 + drop, MOUTH)
        cv.hline(c - 4, c + 4, my + 3 + drop, MOUTH)
        cv.hline(c - 3, c + 3, my + 4 + drop, LIP)
    elif expr == "concern":
        # the grin holds, but it is clenched now
        cv.hline(c - 5, c + 5, my, MOUTH)
        cv.put(c - 6, my + 1, MOUTH); cv.put(c + 6, my - 1, MOUTH)
        cv.hline(c - 4, c + 4, my + 1, TEETH)
        for x in range(c - 3, c + 4, 2):
            cv.put(x, my + 1, TEETH2)
        if talk:
            cv.hline(c - 4, c + 4, my + 2, MOUTH); cv.hline(c - 2, c + 2, my + 2, TONGUE)
            cv.hline(c - 3, c + 3, my + 3, MOUTH)
            cv.hline(c - 2, c + 2, my + 4, LIP)
        else:
            cv.hline(c - 4, c + 4, my + 2, MOUTH)
            cv.hline(c - 2, c + 2, my + 3, LIP)
        cv.put(c + 5, my + 1, MOUTH)
    elif expr == "surprised":
        sizes = ((0, 2), (1, 3), (2, 3), (3, 3), (4, 2)) if not talk else ((0, 2), (1, 3), (2, 4), (3, 4), (4, 4), (5, 3))
        for dy, w in sizes:
            cv.hline(c - w, c + w, my + dy - 1, MOUTH)
        cv.hline(c - 1, c + 1, my - 1, TEETH)
        last = sizes[-1][0]
        cv.hline(c - 2, c + 2, my + last - 2, TONGUE)
        cv.hline(c - 2, c + 2, my + last, LIP)



def portrait(expr, talk=False, blink=False):
    cv = Cv(PW, PH, open_bottom=True)
    c = 32
    sk, hr, tg, gd, cp = RAMP["skin"], RAMP["hair"], RAMP["toga"], RAMP["gold"], RAMP["cape"]
    # ---- collar wings rising behind the head ----
    for s in (-1, 1):
        m = cv.poly([(c + s * 12, 54), (c + s * 14, 40), (c + s * 18, 31), (c + s * 27, 22), (c + s * 28, 42), (c + s * 25, 56)])
        cv.part("collar%d" % s, m, "cape", edge="dark", rad=5, soft=1.2, cuts=(0.28, 0.52, 0.86))
        inner = ndi.binary_erosion(m, iterations=3) & (cv.Y > 24)
        cv.part("lining%d" % s, inner, "lining", edge=None, rad=4, soft=1.0, cuts=(0.28, 0.52, 0.86))
        rim = ndi.binary_erosion(m, iterations=2) & ~ndi.binary_erosion(m, iterations=3) & (cv.Y < 52)
        ys, xs = np.nonzero(rim)
        for y, x in zip(ys, xs):
            cv.put(x, y, gd[3] if (x + y) % 3 else gd[2])
    # ---- shoulders: cape at the edges, bare right shoulder, toga over the left ----
    cape = cv.ell(c, 79, 35, 28) & cv.half(y=47)
    cv.part("cape", cape, "cape", rad=10, soft=1.6, cuts=(0.26, 0.50, 0.84))
    body = cv.ell(c, 79, 29, 27) & cv.half(y=47)
    cv.part("chest", body, "skin", rad=12, soft=2.0, cuts=(0.24, 0.48, 0.84))
    nk = cv.rect(c - 7, 38, c + 7, 56)
    cv.part("neck", nk, "skin", rad=6, bias=-0.15, cuts=(0.3, 0.6, 0.95))
    for x in range(c - 6, c + 7):
        cv.put(x, 46, sk[0] if abs(x - c) > 4 else sk[1]); cv.put(x, 47, sk[1])
    toga = cv.poly([(c + 6, 50), (c + 18, 52), (c + 30, 60), (c + 32, 64), (c - 14, 64), (c - 6, 60), (c + 2, 55)]) & body
    toga |= cv.ell(c + 20, 60, 10, 9) & body
    cv.part("toga", toga, "toga", rad=8, soft=1.6, cuts=(0.24, 0.48, 0.82))
    for k in range(3):
        cv.line(c + 16 - k * 2, 54 + k * 3, c - 2 - k * 3, 63, tg[1])
    cv.line(c + 22, 56, c + 10, 63, tg[3])
    # collarbone + pec on the bare side
    cv.line(c - 20, 53, c - 9, 55, sk[3]); cv.line(c - 20, 54, c - 9, 56, sk[1])
    cv.line(c - 22, 61, c - 13, 63, sk[1])
    # knot medallion on his left shoulder, gold cord across the chest to the right-shoulder clasp
    for x in range(c - 24, c + 16):
        u = (x - (c - 24)) / 40
        y = int(round(52 + 3.5 * math.sin(math.pi * u)))
        if cv.alpha[y, x]:
            cv.put(x, y, gd[3] if x % 2 else gd[2]); cv.put(x, y + 1, gd[1])
    med = cv.ell(c + 17, 52, 3.4, 3.4)
    cv.part("medal", med, "gold", edge="ink", rad=3, soft=0.6, cuts=(0.2, 0.45, 0.8))
    cv.put(c + 17, 52, gd[0]); cv.put(c + 16, 51, gd[4])
    cl = cv.ell(c - 24, 52, 2.6, 2.6)
    cv.part("clasp", cl, "gold", edge="ink", rad=2, soft=0.5, cuts=(0.2, 0.45, 0.8))
    # ---- ears ----
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 13.6, 30, 2.6, 4.4), "skin", rad=3, bias=0.04)
        cv.puts([(c + s * 13, 29), (c + s * 13, 30), (c + s * 13, 31)], sk[1])
    # ---- face: broad jaw, round chin ----
    face = cv.ell(c, 27.5, 12.6, 14.0) | cv.poly([(c - 12.2, 29), (c + 12.2, 29), (c + 10.8, 39), (c + 6, 45),
                                                   (c - 6, 45), (c - 10.8, 39)])
    cv.part("face", face, "skin", rad=11, soft=2.6, cuts=(0.18, 0.46, 0.86), bias=0.04, light=(-0.45, -0.55, 0.75))
    for (x, y) in [(c + 10, 38), (c + 9, 40), (c + 8, 42), (c + 7, 43)]:
        cv.put(x, y, sk[1])
    cv.puts([(c - 2, 43), (c - 3, 44)], sk[3])
    # ---- hair: big curls, each its own lit ball ----
    lift = -1 if expr == "surprised" else 0
    base = cv.ell(c, 13 + lift, 14.5, 10) & cv.half(y=19, below=False)
    cv.part("hair", base, "hair", edge=None, lv=np.where(base, 1, 0))
    curls = [(-10, 7, 5.0), (10, 7, 5.0), (-3.5, 4, 5.4), (4, 4, 5.4), (-14.5, 13, 4.2), (14.5, 13, 4.2),
             (-15, 20, 3.4), (15, 20, 3.4), (-9, 13, 4.2), (9.5, 13, 4.2), (-2.5, 12.5, 4.2), (3.5, 12.5, 4.0),
             (-6, 16, 3.2), (6.4, 16, 3.0), (0.5, 16.4, 3.0)]
    for i, (bx, by, r) in enumerate(curls):
        m = cv.ell(c + bx, by + lift, r, r * 0.92) & cv.half(y=1)
        if i >= 6:
            m &= ~(face & cv.half(y=17.5 + lift))
        cv.part("curl%d" % i, m, "hair", edge=hr[1] if i < 6 else hr[0], rad=r, soft=0.8, cuts=(0.20, 0.50, 0.80),
                light=(-0.6, -0.8, 0.5))
        # c-shaped curl highlight
        hx, hy = c + bx - r * 0.45, by + lift - r * 0.45
        for dx_, dy_ in ((0, 0), (1, -1), (2, -1)) if r > 3.5 else ((0, 0), (1, -1)):
            x, y = int(round(hx + dx_)), int(round(hy + dy_))
            if cv.own[y, x] == cv.names["curl%d" % i]:
                cv.put(x, y, hr[4] if dy_ else hr[3])
    # forehead shadow under the fringe
    fid = cv.names["face"]
    for x in range(c - 12, c + 13):
        for y in range(10, 26):
            if cv.own[y, x] == fid:
                cv.put(x, y, sk[1])
                if cv.own[y + 1, x] == fid:
                    cv.put(x, y + 1, mix(sk[1], sk[2], 0.5))
                break
    # ---- brows: thick, high ----
    by = {"neutral": 21, "warm": 20, "concern": 21, "surprised": 19}[expr]
    for s in (-1, 1):
        for k in range(7):
            x = c + s * (3 + k)
            if expr == "concern":
                dy = -1 if k < 3 else 0 if k < 5 else 1
            elif expr == "surprised":
                dy = -1 if 1 < k < 6 else 0
            else:
                dy = -1 if 1 < k < 6 else 0
                dy -= 1 if k in (3, 4) and expr == "neutral" else 0
            cv.put(x, by + dy, BROW)
            cv.put(x, by + dy + 1, BROW if 0 < k < 6 else mix(BROW, sk[1], 0.5))
    ey = {"neutral": 24, "warm": 24, "concern": 24, "surprised": 23}[expr]
    for s in (-1, 1):
        p_eye(cv, c - 11 if s < 0 else c + 4, ey, "blink" if blink else expr, s)
    # ---- nose: broad ----
    cv.puts([(c - 1, 28), (c - 1, 29), (c - 1, 30), (c - 1, 31)], sk[3]); cv.put(c - 1, 32, sk[4])
    cv.puts([(c + 1, 29), (c + 1, 30), (c + 2, 31), (c + 2, 32), (c + 3, 33)], sk[1])
    cv.puts([(c - 4, 34), (c - 3, 35), (c + 3, 35), (c + 4, 34)], sk[1])
    cv.puts([(c - 2, 35), (c - 1, 35), (c, 35), (c + 1, 35), (c + 2, 35)], sk[1])
    cv.puts([(c - 3, 34), (c + 3, 34)], sk[0])
    for s in (-1, 1):
        bx = c + s * 9
        for y in (33, 34):
            for x in range(bx - 2, bx + 3):
                if cv.own[y, x] == fid:
                    cv.put(x, y, mix(cv.get(x, y), BLUSH, 0.3 if abs(x - bx) < 2 else 0.15))
        cv.put(c + s * 7, 36 if expr == "warm" else 37, sk[1])
    p_mouth(cv, c, 38, expr, talk)
    cv.outline()
    # ---- the laurel, over the curls (after the ink so the leaves can break the silhouette) ----
    px = []
    for s in (-1, 1):
        for k in range(6):
            u = k / 5
            x = int(round(c + s * (2 + k * 2.6)))
            y = int(round(15 - 7 * u * u + lift))
            px.append((x, y, gd[1]))
            if k % 2 == 0:
                px += [(x + s, y - 1, gd[3]), (x + 2 * s, y - 1, gd[3]), (x + 2 * s, y - 2, gd[4]), (x + s, y - 2, gd[2])]
            else:
                px += [(x + s, y + 1, gd[2]), (x + 2 * s, y + 1, gd[3]), (x + 3 * s, y, gd[3])]
        x = c + s * 17
        px += [(x, 7 + lift, gd[2]), (x + s, 6 + lift, gd[3]), (x + s * 2, 5 + lift, gd[4]), (x + s, 5 + lift, gd[3])]
    px += [(c, 15 + lift, gd[4]), (c, 16 + lift, gd[2]), (c - 1, 16 + lift, gd[1]), (c + 1, 16 + lift, gd[1])]
    draw_after(cv, px)
    if expr == "warm":
        sparkle(cv, 57, 30)
        sparkle(cv, 7, 33, big=False)
    if expr == "concern":
        cv.puts([(c + 18, 22), (c + 17, 23), (c + 18, 23), (c + 19, 23), (c + 17, 24), (c + 18, 24), (c + 19, 24), (c + 18, 25)], SWEAT)
        cv.put(c + 17, 23, SWEAT_HI)
    if expr == "surprised":
        cv.puts([(4, 20), (4, 21), (4, 22), (4, 24), (7, 22), (8, 21), (9, 20)], SPARK2)
    return cv


def preview(imgs, path, S=8, bg=(52, 52, 72, 255)):
    pad = 4
    W = sum(i.width + pad for i in imgs) + pad
    H = max(i.height for i in imgs) + 2 * pad
    sheet = Image.new("RGBA", (W, H), bg)
    x = pad
    for i in imgs:
        sheet.alpha_composite(i, (x, H - pad - i.height))
        x += i.width + pad
    sheet.resize((W * S, H * S), Image.NEAREST).save(path)



def foot_point(cv):
    """x = centre between the shoes on the sole row, y = sole row (as Eric's)."""
    y = cv.h - 1
    shoe_ids = [pid for n, pid in cv.names.items() if n.startswith("shoe")]
    xs = [x for x in range(cv.w) if cv.alpha[y, x] and cv.own[y, x] in shoe_ids]
    if not xs:
        xs = [x for x in range(cv.w) if cv.alpha[y, x]]
    return [int(round((min(xs) + max(xs)) / 2)), y]


def body_height(cv):
    """Standing height: soles to the top of the hair (props such as the raised ring do not count)."""
    body = np.zeros_like(cv.alpha)
    for n, pid in cv.names.items():
        if n in ("hair", "head", "face") or n.startswith("curl"):
            body |= cv.own == pid
    rows = np.nonzero(body.any(axis=1))[0]
    return cv.h - rows[0]


def same_except(a, b, box):
    """True when images a and b differ only inside box (x0, y0, x1, y1), inclusive."""
    A, B = np.array(a).astype(int), np.array(b).astype(int)
    diff = np.abs(A - B).sum(axis=2) > 0
    ys, xs = np.nonzero(diff)
    if not len(ys):
        return True, None
    bb = (xs.min(), ys.min(), xs.max(), ys.max())
    return (bb[0] >= box[0] and bb[1] >= box[1] and bb[2] <= box[2] and bb[3] <= box[3]), bb


def build():
    cells_dir = os.path.join(HERE, "cells")
    for sub in ("", "talk", "idle"):
        os.makedirs(os.path.join(cells_dir, sub), exist_ok=True)
    feet, cells = {}, {}
    battle = [b_front("idle"), b_front("talk"), b_front("tell"), b_front("hit"), b_side(), b_back()]
    world = [w_front("idle"), w_front("talk"), w_front("tell"), w_front("hit"), w_side(), w_back()]
    for prefix, group, want in (("battle", battle, 84), ("world", world, 52)):
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            assert img.getbbox()[3] == img.height, (name, "feet not on the bottom row")
            h = body_height(cv)
            assert h == want, (name, "height", h)
            img.save(os.path.join(cells_dir, name))
            feet[name] = foot_point(cv)
            cells[name] = img
    ent, soles = entrance()
    img = ent.image()
    tan = np.zeros_like(ent.alpha)
    for n, pid in ent.names.items():
        if n.startswith("curl") or n in ("hair", "face"):
            tan |= ent.own == pid
    top = np.nonzero(tan.any(axis=1))[0][0]
    assert img.getbbox()[3] == img.height and soles - top == 84, ("entrance height", soles - top)
    img.save(os.path.join(cells_dir, "entrance.png"))
    feet["entrance.png"] = foot_point(ent)
    cells["entrance.png"] = img
    exprs = ("neutral", "warm", "concern", "surprised")
    for i, e in enumerate(exprs):
        face = portrait(e).image()
        face.save(os.path.join(cells_dir, "portrait-%d.png" % i))
        cells["portrait-%d.png" % i] = face
        talk = portrait(e, talk=True).image()
        ok, bb = same_except(face, talk, (20, 34, 44, 46))
        assert ok, ("talk portrait changes more than the mouth", e, bb)
        talk.save(os.path.join(cells_dir, "talk", "tanner-%d.png" % i))
        cells["talk-%d.png" % i] = talk
    # idle extras for the world front cell (same canvas, same feet)
    base = cells["world-0.png"]
    blink = w_front("blink").image()
    ok, bb = same_except(base, blink, (20, 8, 44, 16))
    assert ok, ("blink changes more than the eyes", bb)
    extras = {"blink": blink, "pose1": w_front("crown").image(), "pose2": w_front("flex").image()}
    for k, im in extras.items():
        assert im.size == base.size and np.array_equal(np.array(im)[-6:], np.array(base)[-6:]), (k, "feet moved")
        im.save(os.path.join(cells_dir, "idle", "tanner-%s.png" % k))
        cells["idle-" + k] = im
    with open(os.path.join(cells_dir, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    contact_sheet(cells)
    return cells, feet


def contact_sheet(cells, S=3):
    """3x sheet: Tanner next to the approved cast (cropped straight from the 3x cast reference)."""
    from PIL import ImageFont
    BG = (44, 44, 62, 255)
    GROUND = (70, 70, 96, 255)
    font = ImageFont.load_default()
    ref = Image.open("/tmp/claude-0/designs/cast-reference.png").convert("RGBA")
    rbg = np.array(ref)[2, 2]

    def rcrop(x0, y0, x1, y1):
        c = ref.crop((x0, y0, x1, y1))
        a = np.abs(np.array(c).astype(int) - rbg.astype(int)).sum(axis=2) > 30
        ys, xs = np.nonzero(a)
        c = c.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
        arr = np.array(c)
        bgm = np.abs(arr.astype(int) - rbg.astype(int)).sum(axis=2) <= 30
        arr[bgm, 3] = 0
        return Image.fromarray(arr)

    def up(im):
        return im.resize((im.width * S, im.height * S), Image.NEAREST)

    r1 = [(up(cells["battle-%d.png" % i]), "battle-%d" % i) for i in range(6)]
    r1 += [(up(cells["entrance.png"]), "entrance (cell 12)")]
    r1 += [(rcrop(30, 30, 215, 286), "ref eric 80"), (rcrop(1450, 30, 1640, 286), "ref dev 80"),
           (rcrop(1680, 30, 1830, 286), "ref jakerson 80")]
    r2 = [(up(cells["world-%d.png" % i]), "world-%d" % i) for i in range(6)]
    r2 += [(up(cells["idle-" + k]), "idle " + k) for k in ("blink", "pose1", "pose2")]
    r2 += [(rcrop(25, 330, 140, 498), "ref eric w"), (rcrop(1000, 320, 1110, 498), "ref jules"),
           (rcrop(1235, 320, 1335, 498), "ref imani"), (rcrop(1410, 320, 1510, 498), "ref dev")]
    r3 = [(up(cells["portrait-%d.png" % i]), "portrait-%d" % i) for i in range(4)]
    r3 += [(up(cells["talk-%d.png" % i]), "talk-%d" % i) for i in range(4)]
    r3 += [(rcrop(25, 512, 200, 708), "ref eric"), (rcrop(1030, 512, 1230, 708), "ref jakerson")]
    rows = [r1, r2, r3]
    pad = 12
    widths = [sum(im.width + pad for im, _ in r) + pad for r in rows]
    heights = [max(im.height for im, _ in r) + 30 for r in rows]
    W, H = max(widths), sum(heights) + pad * 2
    sheet = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    y = pad
    for r, rh in zip(rows, heights):
        x = pad
        base = y + rh - 22
        if r is not r3:
            d.rectangle([0, base, W, base + 1], fill=GROUND)
        for im, label in r:
            top = base - im.height if r is not r3 else y
            sheet.alpha_composite(im, (x, top))
            d.text((x, base + 6), label, fill=(200, 200, 220, 255), font=font)
            x += im.width + pad
        y += rh
    sheet.save(os.path.join(HERE, "sheet.png"))


if __name__ == "__main__":
    import sys
    P = os.path.join(HERE, "prev")
    os.makedirs(P, exist_ok=True)
    arg = sys.argv[1] if len(sys.argv) > 1 else "build"
    if arg == "build":
        cells, feet = build()
        for k, v in sorted(feet.items()):
            print(k, cells[k].size, v)
    if arg == "front":
        ims = [b_front(p).image() for p in ("idle", "talk", "tell", "hit")]
        preview(ims, os.path.join(P, "front.png"), S=5)
    if arg == "sb":
        preview([b_side().image(), b_back().image()], os.path.join(P, "sb.png"), S=8)
    if arg == "ent":
        preview([entrance()[0].image()], os.path.join(P, "ent.png"), S=5)
    if arg == "world":
        ims = [w_front(p).image() for p in ("idle", "talk", "tell", "hit")] + [w_side().image(), w_back().image()]
        ims += [w_front(p).image() for p in ("blink", "crown", "flex")]
        preview(ims, os.path.join(P, "world.png"), S=5)
    if arg == "port":
        ims = [portrait(e).image() for e in ("neutral", "warm", "concern", "surprised")]
        ims += [portrait(e, talk=True).image() for e in ("neutral", "warm", "concern", "surprised")]
        preview(ims, os.path.join(P, "port.png"), S=4)
    if arg == "head":
        ims = [b_front(p).image().crop((28, 6, 74, 44)) for p in ("idle", "talk", "tell", "hit")]
        preview(ims, os.path.join(P, "head.png"), S=10)
