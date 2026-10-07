#!/usr/bin/env python3
"""Advisor Bev, Keeper of the Degree Audit -- procedural pixel-art sprites for
"After Hours - College Tale" (U07 boss, replaces CLAIM).

Built on Professor Eric's raster engine (tools/eric_art/draw_eric.py), copied
verbatim below, so outline, shading and palette handling match the cast.
Everything is drawn at its final pixel size with aliased shapes and per-pixel
placement.  Nothing drawn is ever resampled; the only scaling here is the
nearest-neighbour blow-up of previews and the contact sheet.

Bev never gets out of her rolling office chair: she scoots everywhere in it.
Signature pieces: teal cardigan with a mustard pussy-bow, a copper bouffant
with a pencil in it, red cat-eye glasses on a bead chain, red take-a-number
tickets swirling around her and a glowing four-year-plan scroll (one red box:
the credit you are missing).

Outputs (in ./cells next to this script, packed by build_sheet.py):
  battle-0..5.png   82px tall battle cells, 84x92 (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  world-0..5.png    50px tall world cells, 56x56 (same poses, redrawn small)
  portrait-0..3.png 64x64 portraits (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk-0..3.png     the same portraits mid-word (mouth open)
  idle-blink.png, idle-pose1.png, idle-pose2.png   world front cell variants
  entrance.png      the intro-card pose (cell 12, "advisor-entrance"), 128x104
  feet.json         foot point [x, y] for every body cell
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cells")

# --------------------------------------------------------------------------
# palette
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline (cast-wide)
INK2 = (23, 26, 43)

RAMP = {
    # 0 = line/darkest, 1 = shadow, 2 = mid, 3 = light, 4 = highlight
    "skin":   [(92, 44, 40), (168, 96, 76), (212, 138, 106), (236, 174, 138), (250, 204, 170)],
    "hair":   [(66, 24, 22), (132, 52, 32), (182, 84, 42), (220, 122, 60), (244, 164, 96)],
    "card":   [(8, 44, 54), (18, 92, 100), (28, 132, 136), (52, 172, 166), (112, 212, 198)],
    "blouse": [(96, 62, 12), (174, 122, 28), (220, 166, 50), (242, 202, 90), (252, 230, 150)],
    "slacks": [(30, 24, 42), (54, 46, 72), (76, 66, 98), (102, 92, 126), (132, 122, 156)],
    "shoe":   [(40, 14, 20), (94, 28, 40), (134, 44, 56), (168, 72, 80), (198, 110, 110)],
    "chair":  [(18, 18, 26), (38, 38, 50), (56, 56, 72), (78, 78, 96), (106, 106, 126)],
    "metal":  [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "parch":  [(110, 74, 30), (196, 158, 94), (232, 204, 144), (248, 232, 188), (255, 250, 226)],
    "ticket": [(92, 14, 24), (168, 30, 42), (218, 56, 66), (240, 108, 108), (255, 170, 160)],
    "pencil": [(110, 70, 10), (196, 140, 24), (238, 190, 52), (250, 220, 110), (255, 240, 170)],
}
EYE = (30, 22, 30)
WHITE = (250, 248, 244)
MOUTH = (74, 26, 34)
LIP = (176, 56, 78)
LIP_HI = (214, 96, 110)
TONGUE = (196, 92, 96)
TEETH = (240, 236, 228)
BLUSH = (226, 120, 112)
FRAME = (150, 28, 44)       # red cat-eye glasses
FRAME_HI = (226, 86, 96)
LENS = (214, 226, 236)
LENS2 = (150, 176, 204)
BEAD = (236, 196, 84)
BEAD_DK = (150, 108, 36)
BUTTON = (240, 200, 80)
GLOW = (255, 214, 92)
GLOW_HI = (255, 246, 200)
GLOW_DK = (226, 150, 40)
CHECK = (60, 150, 80)
SWEAT = (120, 196, 240)
SWEAT_HI = (220, 244, 255)
SPARK = (255, 240, 170)
SPARK2 = (255, 200, 80)
RIM = (255, 170, 80)
TRAIL = (255, 196, 190)     # swirl trail behind flying tickets

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
# scaled geometry: one body plan drawn at battle size (k=1) and redrawn at
# world size (k=50/82) from analytic shapes -- never by resampling pixels.
# --------------------------------------------------------------------------
class G:
    def __init__(s, cv, c, T, k=1.0):
        s.cv, s.c, s.T, s.k = cv, c, T, k

    def X(s, dx):
        return s.c + dx * s.k

    def Y(s, dy):
        return s.T + dy * s.k

    def R(s, r, lo=0.8):
        return max(r * s.k, lo)

    def rad(s, r):
        return max(2.0, r * s.k)

    def ell(s, dx, dy, rx, ry, ang=0.0):
        return s.cv.ell(s.X(dx), s.Y(dy), s.R(rx), s.R(ry), ang)

    def cap(s, x0, y0, x1, y1, r0, r1=None):
        return s.cv.capsule(s.X(x0), s.Y(y0), s.X(x1), s.Y(y1), s.R(r0), s.R(r0 if r1 is None else r1))

    def chain(s, pts, r):
        m = s.cv.empty()
        for (a, b), (c_, d) in zip(pts, pts[1:]):
            m |= s.cap(a, b, c_, d, r)
        return m

    def rect(s, x0, y0, x1, y1):
        return s.cv.rect(s.X(x0), s.Y(y0), s.X(x1), s.Y(y1))

    def poly(s, pts):
        return s.cv.poly([(s.X(x), s.Y(y)) for x, y in pts])

    def half(s, dy=None, dx=None, below=True, right=True):
        return s.cv.half(None if dy is None else s.Y(dy), None if dx is None else s.X(dx), below, right)

    def p(s, dx, dy):
        return int(round(s.X(dx))), int(round(s.Y(dy)))

    def put(s, dx, dy, col):
        s.cv.put(*s.p(dx, dy), col)


def own_is(cv, x, y, name):
    return 0 <= x < cv.w and 0 <= y < cv.h and name in cv.names and cv.own[y, x] == cv.names[name]


# --------------------------------------------------------------------------
# floating props drawn after the ink pass (like Eric's sparks)
# --------------------------------------------------------------------------
TK = {
    "h": ["dddddd.",
          "dLWWLLD",
          "dRRRRRD",
          ".DDDDDD"],
    "v": [".dd.",
          "dLLD",
          "dWLD",
          "dWRD",
          "dRRD",
          "dRRD",
          ".DD."],
    "u": ["...dd.",
          "..dLLd",
          ".dLWWD",
          "dLWRD.",
          "dRRD..",
          ".DD..."],
    "n": [".dd...",
          "dLLd..",
          "DWWLd.",
          ".DRWLd",
          "..DRRd",
          "...DD."],
    # world size
    "hs": ["dLW", "dRD"],
    "vs": ["dL", "LW", "RD"],
    "us": [".L", "LW", "D."],
}


def ticket(cv, x, y, kind):
    tr = RAMP["ticket"]
    pal = {"d": tr[1], "D": tr[0], "L": tr[3], "R": tr[2], "W": WHITE}
    for j, row in enumerate(TK[kind]):
        for i, ch in enumerate(row):
            if ch != ".":
                cv.put(x + i, y + j, pal[ch])


def trail(cv, pts):
    for k, (x, y) in enumerate(pts):
        if 0 <= x < cv.w and 0 <= y < cv.h and not cv.alpha[y, x]:
            cv.put(x, y, TRAIL if k % 2 == 0 else mix(TRAIL, RAMP["ticket"][3], 0.5))


def sparkle(cv, x, y, big=True):
    if big:
        cv.puts([(x, y - 2), (x, y - 1), (x, y + 1), (x, y + 2), (x - 2, y), (x - 1, y), (x + 1, y), (x + 2, y)], GLOW)
        cv.put(x, y, WHITE)
    else:
        cv.puts([(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)], GLOW)
        cv.put(x, y, GLOW_HI)


def glow_ring(cv, name, col=GLOW, every=1, only_empty=True):
    """1px warm halo just outside a part's ink edge (pixels that are still empty)."""
    if name not in cv.names:
        return
    m = cv.own == cv.names[name]
    ring = ndi.binary_dilation(m, iterations=2) & ~ndi.binary_dilation(m, iterations=1)
    ys, xs = np.nonzero(ring)
    for k, (y, x) in enumerate(zip(ys, xs)):
        if only_empty and cv.alpha[y, x]:
            continue
        if (x + y) % every == 0:
            cv.put(x, y, col)


# --------------------------------------------------------------------------
# chair
# --------------------------------------------------------------------------
def chair_back_front(g, name="chairback"):
    cv = g.cv
    m = (g.ell(0, 36, 23, 13) & g.half(dy=36, below=False)) | g.rect(-23, 36, 23, 52) | (g.ell(0, 52, 23, 6.4) & g.half(dy=52))
    cv.part(name, m, "chair", rad=g.rad(9), soft=1.4, cuts=(0.30, 0.56, 0.90), tex=0.04, seed=71)
    return m


def chair_base_front(g):
    cv = g.cv
    cv.part("column", g.rect(-1.8, 60, 1.8, 73), "metal", rad=g.rad(2), cuts=(0.25, 0.55, 0.85), light=(-0.9, -0.2, 0.4))
    legs = g.cap(0, 73.5, -21, 77.6, 1.7) | g.cap(0, 73.5, 21, 77.6, 1.7)
    legs |= g.cap(0, 73.5, -11, 78.6, 1.7) | g.cap(0, 73.5, 11, 78.6, 1.7) | g.ell(0, 73.8, 4.2, 2.4)
    cv.part("base", legs, "metal", rad=g.rad(2), cuts=(0.2, 0.5, 0.8), bias=0.06)
    for i, (dx, dy) in enumerate(((-21, 79.6), (21, 79.6), (-11.5, 79.8), (11.5, 79.8))):
        cv.part("caster%d" % i, g.ell(dx, dy, 2.7, 1.9), "chair", rad=2, cuts=(0.25, 0.5, 0.8))


def armrests_front(g, sides=(-1, 1)):
    cv = g.cv
    for s in sides:
        cv.part("post%d" % s, g.rect(s * 19.8 - 1.1, 52, s * 19.8 + 1.1, 59.5), "metal", rad=2, cuts=(0.3, 0.6, 0.9))
        cv.part("pad%d" % s, g.ell(s * 20, 51.4, 4.4, 1.9), "chair", rad=2, cuts=(0.2, 0.45, 0.8), bias=0.1)


# --------------------------------------------------------------------------
# Bev, front view
# --------------------------------------------------------------------------
def legs_front(g, legs_seed=81):
    cv = g.cv
    cv.part("seat", g.ell(0, 60, 19.2, 4.2), "chair", rad=g.rad(3), cuts=(0.25, 0.5, 0.85), bias=0.05)
    shin = g.cap(-6.4, 61, -6.8, 76, 4.3, 3.9) | g.cap(6.4, 61, 6.8, 76, 4.3, 3.9)
    cv.part("shins", shin, "slacks", rad=g.rad(3), soft=0.8, cuts=(0.30, 0.56, 0.9))
    for s in (-1, 1):
        sh = g.ell(s * 7.4, 79.2, 5.4, 2.8)
        cv.part("shoe%d" % s, sh, "shoe", rad=g.rad(3), cuts=(0.3, 0.55, 0.85))
        g.put(s * 7.2 - 2, 78, RAMP["shoe"][4])
    lap = g.ell(-6.6, 57.6, 7.4, 4.8) | g.ell(6.6, 57.6, 7.4, 4.8) | g.rect(-13.4, 53, 13.4, 57.5)
    cv.part("lap", lap, "slacks", rad=g.rad(5), soft=1.0, cuts=(0.30, 0.55, 0.88), tex=0.03, seed=legs_seed)
    if g.k == 1:
        cv.vline(g.c, int(g.Y(57)), int(g.Y(61)), RAMP["slacks"][0])


def torso_front(g, seed=5):
    cv = g.cv
    cd = RAMP["card"]
    tor = g.ell(0, 46.5, 16.6, 10.4) | g.poly([(-15.6, 46.5), (15.6, 46.5), (13.9, 56.3), (-13.9, 56.3)])
    cv.part("torso", tor, "card", rad=g.rad(12), soft=1.8, cuts=(0.30, 0.52, 0.86), tex=0.06 if g.k == 1 else 0.0, seed=seed)
    # ribbed hem
    hem = tor & g.half(dy=54.2)
    cv.part("hem", hem, "card", noedge=("torso",), lv=np.where(hem, 1, 0) + np.where(hem & (cv.X < g.c - 3), 1, 0))
    if g.k == 1:
        for x in range(int(g.X(-13)), int(g.X(14)), 2):
            for y in (int(g.Y(55)), int(g.Y(56))):
                if own_is(cv, x, y, "hem"):
                    cv.put(x, y, cd[0])
    # blouse V + bow
    v = g.poly([(-4.4, 37.2), (4.4, 37.2), (1.2, 54.2), (-1.2, 54.2)])
    cv.part("blouse", v, "blouse", rad=g.rad(3), cuts=(0.2, 0.5, 0.9), bias=0.08)
    # cardigan buttons down the viewer-left placket
    if g.k == 1:
        for dy in (44, 48, 52):
            hw = 4.4 - (dy - 37.2) / 17.0 * 3.2
            x, y = g.p(-hw - 1.6, dy)
            cv.put(x, y, BUTTON); cv.put(x, y + 1, YELLOW_DK)
    else:
        for dy in (45, 51):
            hw = 4.4 - (dy - 37.2) / 17.0 * 3.2
            g.put(-hw - 1.7, dy, BUTTON)


def bow(g):
    cv = g.cv
    loops = g.ell(-3.0, 38.4, 2.8, 1.9, -0.15) | g.ell(3.0, 38.4, 2.8, 1.9, 0.15)
    cv.part("bowloops", loops, "blouse", edge="dark", rad=2, cuts=(0.2, 0.45, 0.8), bias=0.1)
    tails = g.cap(-0.7, 40, -2.4, 43.6, 1.0, 0.8) | g.cap(0.7, 40, 2.0, 43.6, 1.0, 0.8)
    cv.part("bowtails", tails, "blouse", edge="dark", noedge=("blouse",), rad=2, cuts=(0.25, 0.5, 0.8), bias=0.05)
    cv.part("knot", g.ell(0, 38.6, 1.2, 1.4), "blouse", edge="dark", rad=2, bias=0.2)


def arm(g, name, pts, r=4.1, seed=0):
    cv = g.cv
    m = g.chain(pts, r)
    cv.part(name, m, "card", edge="dark", rad=g.rad(4), soft=1.0, cuts=(0.30, 0.55, 0.88),
            tex=0.05 if g.k == 1 else 0.0, seed=seed or (len(name) * 7 + int(pts[0][0]) + 50))
    # ribbed cuff
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    L = math.hypot(xb - xa, yb - ya) or 1
    ux, uy = (xb - xa) / L, (yb - ya) / L
    cuff = m & g.cap(xb - ux * 2.2, yb - uy * 2.2, xb, yb, r + 0.5) & ~g.cap(xa, ya, xb - ux * 2.2, yb - uy * 2.2, r + 0.6)
    edgepx = (cv.col[..., 0] == RAMP["card"][0][0]) & (cv.col[..., 1] == RAMP["card"][0][1])
    cv.fill(cuff & ~edgepx, RAMP["card"][1])
    return m


def hand(g, name, dx, dy, rx=2.9, ry=2.7):
    m = g.ell(dx, dy, rx, ry) if g.k == 1 else g.cv.ell(g.X(dx), g.Y(dy), max(rx * g.k, 2.0), max(ry * g.k, 2.0))
    g.cv.part(name, m, "skin", edge="ink", rad=2.5, soft=0.8, bias=0.06)
    return m


def finger(g, name, x0, y0, x1, y1, r=1.0, after=()):
    m = g.cap(x0, y0, x1, y1, r)
    g.cv.part(name, m, "skin", edge="ink", noedge=after, rad=1.5, soft=0.5, bias=0.08)
    return m


def scroll_rolled(g, x0, x1, y, r=2.6, name="scroll"):
    """The four-year plan rolled up: glowing parchment tube with gold knobs."""
    cv = g.cv
    tube = g.cap(x0, y, x1, y, r)
    cv.part(name, tube, "parch", edge="dark", rad=g.rad(2.5), cuts=(0.15, 0.40, 0.70), light=(-0.2, -0.9, 0.5), bias=0.1)
    # gold seam where the sheet ends on the roll
    if g.k == 1:
        for x in range(int(g.X(x0 + 2)), int(g.X(x1 - 1))):
            if own_is(cv, x, int(round(g.Y(y + 1))), name):
                cv.put(x, int(round(g.Y(y + 1))), GLOW_DK)
    for i, dx in enumerate((x0 - 1.4, x1 + 1.4)):
        cv.part("%sknob%d" % (name, i), g.ell(dx, y, 1.5, r + 0.7), "pencil", edge="dark", rad=2, cuts=(0.2, 0.45, 0.75), bias=0.1)


def hair_back_front(g, flick=0):
    cv = g.cv
    hb = g.ell(0, 17, 19, 17) | g.ell(-14.8, 29.2, 5.6, 5.8) | g.ell(14.8 + flick, 29.2, 5.6, 5.8)
    cv.part("hairback", hb, "hair", rad=g.rad(13), soft=1.6, cuts=(0.28, 0.52, 0.84), tex=0.05 if g.k == 1 else 0.0, seed=17)
    return hb


def face_front(g):
    cv = g.cv
    cv.part("neck", g.rect(-3, 31, 3, 37.5), "skin", rad=g.rad(3), bias=-0.15)
    face = g.ell(0, 22, 12.6, 13.2)
    cv.part("face", face, "skin", rad=g.rad(10), soft=1.6, cuts=(0.28, 0.50, 0.86))
    return face


def bangs_front(g, hb):
    """Big side-swept fringe: low over the viewer-left brow, lifting to the right."""
    cv = g.cv
    dx = (cv.X - g.c) / g.k
    edge = 14.6 - 0.21 * (dx + 12) - 0.010 * dx * dx
    m = g.ell(0, 17, 19, 17) & (cv.Y <= g.T + edge * g.k)
    # a soft curl that rolls up at the right temple
    m |= g.ell(11.2, 10.2, 5.2, 3.6) & g.ell(0, 17, 19, 17)
    cv.part("bangs", m, "hair", noedge=("hairback",), rad=g.rad(9), soft=1.4, cuts=(0.26, 0.50, 0.82),
            tex=0.05 if g.k == 1 else 0.0, seed=19, light=(-0.55, -0.85, 0.55))
    hr = RAMP["hair"]
    if g.k == 1:
        # sweep strands
        for (x0, y0, x1, y1) in [(-14, 6, -4, 12), (-10, 3, 2, 10), (-4, 1, 8, 7), (-16, 11, -9, 14), (2, 3, 13, 6)]:
            L = max(abs(x1 - x0), abs(y1 - y0))
            for t in range(L + 1):
                x, y = g.p(x0 + (x1 - x0) * t / L, y0 + (y1 - y0) * t / L)
                if own_is(cv, x, y, "bangs") and cv.get(x, y) != hr[0]:
                    cv.put(x, y, hr[1] if cv.get(x, y) in (hr[2], hr[1]) else hr[2])
        for (x, y) in [(-12, 21), (-15, 25), (13, 22), (16, 26), (-17, 28), (17, 31), (-13, 31)]:
            px, py = g.p(x, y)
            if own_is(cv, px, py, "hairback"):
                cv.put(px, py, hr[1])
    return m


def pencil(g, x0, y0, x1, y1, name="pencil"):
    """Pencil tucked in the bouffant: (x0,y0) is the point end, (x1,y1) the eraser."""
    cv = g.cv
    body = g.cap(x0, y0, x1, y1, 1.35) if g.k == 1 else g.cap(x0, y0, x1, y1, 2.7)
    cv.part(name, body, "pencil", edge="dark" if g.k == 1 else None, rad=2, cuts=(0.2, 0.5, 0.85), light=(-0.3, -0.9, 0.4))
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    er = g.cap(x1 - ux * 2.4, y1 - uy * 2.4, x1, y1, 1.35) & body
    cv.fill(er, RAMP["ticket"][3])
    band = g.cap(x1 - ux * 3.6, y1 - uy * 3.6, x1 - ux * 2.6, y1 - uy * 2.6, 1.5) & body
    cv.fill(band, RAMP["metal"][2])


# ---- face details, battle size --------------------------------------------
def b_glasses(cv, c, t, glint=False, tilt=0):
    y0, y1 = t + 18, t + 24
    for side in (-1, 1):
        xa, xb = (c - 11, c - 2) if side < 0 else (c + 2, c + 11)
        dy = tilt if side > 0 else 0
        for y in range(y0 + 1, y1):
            for x in range(xa + 1, xb):
                if glint:
                    cv.put(x, y + dy, LENS2 if (x - xa + y) % 6 else LENS)
                else:
                    cv.put(x, y + dy, mix(cv.get(x, y + dy), LENS, 0.16))
        cv.hline(xa, xb, y0 + dy, FRAME)
        cv.hline(xa + 1, xb - 1, y1 + dy, FRAME)
        cv.vline(xa, y0 + dy, y1 - 1 + dy, FRAME)
        cv.vline(xb, y0 + dy, y1 - 1 + dy, FRAME)
        # cat-eye: heavier outer top and an upswept wing
        o, i_ = (xa, xb) if side < 0 else (xb, xa)
        cv.put(o - side * 0, y0 - 1 + dy, FRAME)
        cv.put(o + side * 1, y0 - 1 + dy, FRAME)
        cv.put(o + side * 2, y0 - 2 + dy, FRAME)
        cv.put(o + side * 1, y0 - 2 + dy, FRAME_HI if side < 0 else FRAME)
        cv.put(o - side * 1, y0 - 1 + dy, FRAME)
        cv.put(xa + 2, y0 + dy, FRAME_HI) if side < 0 else None
        cv.put(xa + 3, y0 + dy, FRAME_HI) if side < 0 else None
        if glint:
            cv.puts([(xa + 1, y0 + 1 + dy), (xa + 2, y0 + 1 + dy), (xa + 1, y0 + 2 + dy)], WHITE)
            cv.puts([(xa + 4, y1 - 1 + dy), (xa + 5, y1 - 2 + dy), (xa + 6, y1 - 3 + dy), (xa + 7, y1 - 4 + dy)], WHITE)
        else:
            cv.put(xa + 1, y0 + 1 + dy, LENS)
    cv.hline(c - 1, c + 1, t + 20, FRAME)


def b_eyes(cv, c, t, pose, blink=False):
    sk = RAMP["skin"]
    for side in (-1, 1):
        a, b = (c - 7, c - 6) if side < 0 else (c + 6, c + 7)
        outer = a - 1 if side < 0 else b + 1
        if blink or pose == "tell_closed":
            cv.hline(a - 1 if side < 0 else a, b if side < 0 else b + 1, t + 21, EYE)
            cv.put(outer + side, t + 20, EYE)
            continue
        if pose == "hit":
            m = ["KK..", "..KK", "KK.."]
            for j, row in enumerate(m):
                for i, ch in enumerate(row):
                    if ch == "K":
                        x = a - 1 + i if side < 0 else b + 1 - i
                        cv.put(x, t + 20 + j + (1 if side > 0 else 0), EYE)
            continue
        if pose == "tell":
            continue        # hidden by the glint
        for y in range(t + 20, t + 23):
            cv.put(a, y, EYE); cv.put(b, y, EYE)
        cv.put(a, t + 20, WHITE)
        cv.hline(a - (side < 0), b + (side > 0), t + 19, EYE)   # upper lid
        cv.put(outer + side, t + 19, EYE)                        # lash flick
        cv.put(outer, t + 22, sk[1])


def b_brows(cv, c, t, pose):
    hr = RAMP["hair"]
    if pose == "hit":
        top = [(-10, 15), (-9, 15), (-8, 14), (-7, 14), (-6, 13), (-5, 13)]      # worried
    elif pose == "tell":
        top = [(-10, 16), (-9, 15), (-8, 15), (-7, 15), (-6, 15), (-5, 16)]
    else:
        top = [(-10, 16), (-9, 15), (-8, 14), (-7, 14), (-6, 14), (-5, 15)]
    for i, (dx, dy) in enumerate(top):
        cv.put(c + dx, t + dy, hr[1])
        rdy = dy - (1 if pose == "tell" and i > 0 else 0)
        cv.put(c - dx, t + rdy, hr[1])


def b_mouth(cv, c, t, pose):
    y = t + 30
    if pose == "idle":
        cv.hline(c - 2, c + 2, y, MOUTH)
        cv.put(c - 3, y - 1, MOUTH); cv.put(c + 3, y - 1, MOUTH)
        cv.hline(c - 2, c + 2, y + 1, LIP)
        cv.put(c - 1, y - 1, LIP); cv.put(c + 1, y - 1, LIP)
    elif pose == "talk":
        cv.hline(c - 2, c + 2, y - 1, LIP)
        cv.hline(c - 2, c + 2, y, TEETH)
        cv.put(c - 3, y, MOUTH); cv.put(c + 3, y, MOUTH)
        cv.hline(c - 3, c + 3, y + 1, MOUTH)
        cv.hline(c - 1, c + 1, y + 1, TONGUE)
        cv.hline(c - 2, c + 2, y + 2, LIP)
    elif pose == "tell":
        # knowing grin, one side higher
        cv.hline(c - 3, c + 3, y, MOUTH)
        cv.hline(c - 2, c + 2, y, TEETH)
        cv.put(c - 4, y - 1, MOUTH); cv.put(c + 4, y - 1, MOUTH); cv.put(c + 5, y - 2, MOUTH)
        cv.hline(c - 2, c + 2, y + 1, LIP)
    elif pose == "grin":
        cv.hline(c - 4, c + 4, y - 1, MOUTH)
        cv.hline(c - 3, c + 3, y, TEETH)
        cv.put(c - 4, y, MOUTH); cv.put(c + 4, y, MOUTH)
        cv.put(c - 5, y - 2, MOUTH); cv.put(c + 5, y - 2, MOUTH)
        cv.hline(c - 3, c + 3, y + 1, MOUTH)
        cv.hline(c - 1, c + 1, y + 1, TONGUE)
        cv.hline(c - 2, c + 2, y + 2, LIP)
    elif pose == "hit":
        cv.hline(c - 3, c + 3, y, MOUTH)
        cv.hline(c - 3, c + 3, y + 1, MOUTH)
        for x in range(c - 2, c + 3):
            cv.put(x, y + ((x - c) % 2), TEETH)


def b_face(g, pose, blink=False, glint=None):
    cv = g.cv
    c, t = int(round(g.c)), int(round(g.T))
    sk = RAMP["skin"]
    for s in (-1, 1):
        for x in range(c + s * 8 - 1, c + s * 8 + 2):
            if own_is(cv, x, t + 26, "face"):
                cv.put(x, t + 26, BLUSH)
    cv.put(c - 1, t + 25, sk[3])
    cv.puts([(c + 1, t + 26), (c, t + 27), (c - 1, t + 27)], sk[1])
    b_mouth(cv, c, t, "talk" if pose == "talk" else pose if pose in ("tell", "hit", "grin") else "idle")
    gl = (pose in ("tell", "grin")) if glint is None else glint
    b_glasses(cv, c, t, glint=gl, tilt=1 if pose == "hit" else 0)
    b_eyes(cv, c, t, "tell" if gl else pose, blink=blink)
    b_brows(cv, c, t, pose)
    # pearl earrings under the flip
    for s in (-1, 1):
        cv.put(c + s * 12, t + 29, WHITE); cv.put(c + s * 12, t + 30, LENS2)


def bead_chain(g, sides=(-1, 1), drop=0):
    """Glasses chain: from each temple down past the jaw, looping on the chest."""
    cv = g.cv
    for s in sides:
        pts = [(13.2, 20), (14.4, 25), (14.0, 30), (11.5, 35), (8, 39.5), (4, 42 + drop), (0, 43 + drop)]
        pts = [(s * x, y) for x, y in pts]
        n = 0
        step = 1.9 if g.k == 1 else 1.0
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            L = math.hypot(x1 - x0, y1 - y0) * g.k
            k = 0.0
            while k < L:
                x, y = g.p(x0 + (x1 - x0) * k / L, y0 + (y1 - y0) * k / L)
                if g.k == 1:
                    cv.put(x, y, BEAD if n % 2 == 0 else BEAD_DK)
                elif n % 2 == 0:
                    cv.put(x, y, BEAD)
                n += 1
                k += step


# ---- the whole front figure -------------------------------------------------
def front(pose, g=None, k=1.0, blink=False, entrance=False):
    """pose: idle, talk, tell, hit, grin (entrance), pose1 (pushing glasses), pose2 (holding up a ticket)."""
    if g is None:
        if k == 1:
            cv = Cv(BW, BH)
            g = G(cv, 42, BT, 1.0)
        else:
            cv = Cv(WW, WH)
            g = G(cv, WC, WT, k)
    cv = g.cv
    big = g.k == 1
    hx = 2 if pose == "hit" else 0
    chair_back_front(g)
    chair_base_front(g)
    armrests_front(g, sides=(-1, 1))
    legs_front(g)
    torso_front(g)
    bow(g)
    # ---- arms (the ones that stay low) ----
    lap_scroll = pose in ("idle", "pose1", "pose2", "talk")
    if pose in ("idle", "pose2"):
        arm(g, "armL", [(-15, 39), (-19.2, 48.5), (-10, 55.6)])
    elif pose in ("talk", "pose1"):
        arm(g, "armL", [(-15, 39), (-19.2, 48.5), (-10, 55.6)])
    elif pose == "tell":
        arm(g, "armL", [(-15, 39), (-21.5, 47), (-26.5, 41.5)])
    elif pose == "grin":
        arm(g, "armL", [(-15, 39), (-23, 45.5), (-30, 43.5)])
    elif pose == "hit":
        arm(g, "armL", [(-15, 39), (-24, 37), (-27.5, 28)])
    if pose in ("idle", "talk"):
        arm(g, "armR", [(15, 39), (19.2, 48.5), (10, 55.6)])
    elif pose == "pose2":
        arm(g, "armR", [(15, 39), (19.2, 48.5), (10, 55.6)])
    elif pose == "pose1":
        arm(g, "armR", [(15, 39), (19.2, 48.5), (10, 55.6)])
    if lap_scroll:
        if pose in ("idle", "pose1"):
            scroll_rolled(g, -14.5, 12.5, 57.4)
        else:
            scroll_rolled(g, -15.5, 8.5, 57.4)
        hand(g, "handL", -10, 56.4)
        if pose in ("idle", "pose1"):
            hand(g, "handR", 10, 56.4)
        elif pose == "pose2":
            hand(g, "handR", 10, 56.4)
    if pose == "hit":
        # the plan slips off her lap and unrolls over her knees
        sheet = g.poly([(-11, 56), (7, 56), (8, 69), (-10, 69)])
        g.cv.part("sheet", sheet, "parch", edge="dark", lv=np.where(sheet, 4, 0))
        if big:
            for yy in range(59, 68, 3):
                cv.hline(g.X(-8), g.X(5), g.Y(yy), GLOW_DK)
            cv.puts([(g.c - 6, g.T + 64), (g.c - 5, g.T + 65)], CHECK)
        scroll_rolled(g, -11, 7, 70, r=2.2, name="scroll")
    # ---- head ----
    gh = G(cv, g.c + hx * g.k, g.T, g.k)
    hb = hair_back_front(gh)
    face_front(gh)
    bangs_front(gh, hb)
    if big:
        b_face(gh, pose if pose in ("idle", "talk", "tell", "hit", "grin") else "idle", blink=blink)
    else:
        w_face(gh, pose, blink=blink)
    bead_chain(gh)
    if pose != "hit":
        pencil(gh, 8, 6, 20.5, 1.2)
    # ---- arms that are raised in front of the hair ----
    if pose == "talk":
        arm(g, "armR", [(15, 39), (22.5, 47.5), (25.5, 38.5)])
        hand(g, "handR", 25.8, 35.2, rx=2.8, ry=3.0)
        finger(g, "finger", 26.0, 33, 26.4, 27.0, r=1.35, after=("handR",))
        g.put(24.6, 35.4, RAMP["skin"][1])
    elif pose == "tell":
        open_plan(g, 22, 19, 38, 67)
        arm(g, "armR", [(15, 39), (24.5, 35), (27.5, 24.5)])
    elif pose == "grin":
        arm(g, "armR", [(15, 39), (24, 31), (27.4, 9)], r=3.9)
    elif pose == "hit":
        arm(g, "armR", [(15, 39), (24, 37), (28.5, 28)])
        hand(g, "handR", 28.8, 25.6, rx=2.8, ry=3.2)
        hand(g, "handL", -27.8, 25.6, rx=2.8, ry=3.2)
    elif pose == "pose1":
        # pushing her glasses up the nose with one finger
        # adjusting her glasses by the frame
        arm(g, "armR", [(15, 39), (21, 44), (15, 27)], r=3.9)
        hand(g, "handR", 13.4, 23.4, rx=2.7, ry=3.0)
    elif pose == "pose2":
        # holding a fresh take-a-number ticket up by her face
        arm(g, "armL2", [(-15, 39), (-20, 44), (-21.5, 34)])
    if pose == "tell":
        hand(g, "handR", 27.6, 21.6, rx=2.8, ry=3.0)
        hand(g, "handL", -27, 40.4, rx=3.0, ry=2.4)
        finger(g, "thumbL", -24.6, 39.2, -23.6, 37.6, r=0.9, after=("handL",))
    if pose == "grin":
        hand(g, "handL", -30.4, 43.2, rx=2.8, ry=2.6)
        finger(g, "point", -32.5, 42.4, -38.2, 41.6, r=1.35, after=("handL",))
    if pose == "pose2":
        hand(g, "handL2", -21.6, 32.6, rx=2.6, ry=2.6)
    if pose == "hit" and big:
        pencil(gh, 21, -1, 29, 5, name="pencil")          # knocked loose
    cv.outline()
    # ---- after the ink: tickets, glow, sweat ----
    c, T = g.c, g.T
    if big:
        if pose in ("idle", "talk"):
            ticket(cv, c - 33, T + 12, "u"); trail(cv, [(c - 27, T + 10), (c - 25, T + 9), (c - 23, T + 9)])
            ticket(cv, c + 30, T + 30, "n"); trail(cv, [(c + 31, T + 36), (c + 30, T + 38), (c + 28, T + 39)])
            ticket(cv, c - 36, T + 46, "h"); trail(cv, [(c - 30, T + 48), (c - 28, T + 49)])
            sparkle(cv, c + 17, T + 61, big=False)
            sparkle(cv, c - 19, T + 54, big=False)
        elif pose == "tell":
            ticket(cv, c - 31, T + 30, "v"); trail(cv, [(c - 29, T + 37), (c - 28, T + 38)])
            ticket(cv, c - 36, T + 16, "u"); trail(cv, [(c - 31, T + 14), (c - 29, T + 13), (c - 27, T + 13)])
            ticket(cv, c - 37, T + 54, "h")
            ticket(cv, c - 20, T + 4, "n"); trail(cv, [(c - 15, T + 5), (c - 13, T + 6)])
            glow_ring(cv, "plan", GLOW, every=1)
            sparkle(cv, c + 19, T + 15); sparkle(cv, c + 39, T + 44, big=False); sparkle(cv, c + 20, T + 72, big=False)
        elif pose == "hit":
            ticket(cv, c - 38, T + 8, "u"); ticket(cv, c - 34, T + 40, "v"); ticket(cv, c + 31, T + 40, "h")
            ticket(cv, c + 33, T + 52, "n"); ticket(cv, c - 37, T + 60, "h")
            sx, sy = c - 19, T + 12
            cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx + 1, sy + 1),
                     (sx - 1, sy + 2), (sx, sy + 2), (sx + 1, sy + 2), (sx, sy + 3)], SWEAT)
            cv.put(sx - 1, sy + 1, SWEAT_HI)
    else:
        if pose in ("idle", "talk", "pose1", "pose2"):
            ticket(cv, c - 22, T + 9, "us")
            ticket(cv, c + 18, T + 21, "vs")
            ticket(cv, c - 23, T + 28, "hs")
        elif pose == "tell":
            ticket(cv, c - 22, T + 8, "us"); ticket(cv, c - 23, T + 30, "hs")
            glow_ring(cv, "plan", GLOW, every=2)
        elif pose == "hit":
            ticket(cv, c - 23, T + 5, "us"); ticket(cv, c + 18, T + 25, "hs"); ticket(cv, c - 22, T + 32, "vs")
        if pose == "pose2":
            pass
    if pose == "pose2":
        x, y = g.p(-23, 26.5)
        if big:
            ticket(cv, x, y, "v")
        else:
            tr = RAMP["ticket"]
            cv.puts([(x, y), (x + 1, y)], tr[3]); cv.puts([(x, y + 1), (x + 1, y + 1)], tr[2])
            cv.put(x + 1, y, WHITE); cv.puts([(x, y + 2), (x + 1, y + 2)], tr[0])
    return cv


def open_plan(g, x0, y0, x1, y1):
    """The four-year plan unrolled: two columns x four years of course boxes,
    every box ticked except one (the missing credit, in red)."""
    cv = g.cv
    sheet = g.rect(x0 + 1, y0 + 1, x1 - 1, y1 - 1)
    lv = np.where(sheet, 4, 0)
    cv.part("plan", sheet, "parch", edge="dark", lv=lv)
    big = g.k == 1
    X0, Y0 = g.p(x0 + 1, y0 + 1)
    X1, Y1 = g.p(x1 - 1, y1 - 1)
    for y in range(Y0, Y1 + 1):
        for x in range(X0, X1 + 1):
            cv.put(x, y, GLOW_HI if (x + y) % 7 else (255, 238, 170))
    if big:
        # title band
        cv.hline(X0 + 2, X1 - 2, Y0 + 2, GLOW_DK)
        for x in range(X0 + 3, X1 - 2, 2):
            cv.put(x, Y0 + 3, (196, 140, 60))
        bw = (X1 - X0 - 3) // 2
        top = Y0 + 6
        bh, gap = 8, 2
        for row in range(4):
            for col in range(2):
                bx = X0 + 1 + col * (bw + 1)
                by = top + row * (bh + gap)
                if by + bh > Y1:
                    continue
                missing = (row == 3 and col == 1)
                edge = (210, 40, 52) if missing else GLOW_DK
                cv.hline(bx, bx + bw - 1, by, edge); cv.hline(bx, bx + bw - 1, by + bh - 1, edge)
                cv.vline(bx, by, by + bh - 1, edge); cv.vline(bx + bw - 1, by, by + bh - 1, edge)
                for yy in range(by + 1, by + bh - 1):
                    for xx in range(bx + 1, bx + bw - 1):
                        cv.put(xx, yy, (255, 230, 150) if not missing else (255, 214, 206))
                if missing:
                    for d in range(bh - 4):
                        cv.put(bx + 2 + d * (bw - 4) // max(1, bh - 5), by + 2 + d, (210, 40, 52))
                        cv.put(bx + bw - 3 - d * (bw - 4) // max(1, bh - 5), by + 2 + d, (210, 40, 52))
                else:
                    cv.puts([(bx + 2, by + 4), (bx + 3, by + 5), (bx + 4, by + 4), (bx + 5, by + 3)], CHECK)
                    cv.hline(bx + 2, bx + bw - 3, by + 2, (214, 170, 90)) if bw > 6 else None
    else:
        for row in range(4):
            yy = Y0 + 2 + row * ((Y1 - Y0 - 2) // 4)
            cv.hline(X0 + 1, X1 - 1, yy, GLOW_DK)
        cv.put(X1 - 2, Y1 - 3, (210, 40, 52))
    # rolls at both ends
    for i, yy in enumerate((y0, y1)):
        cv.part("planroll%d" % i, g.cap(x0 - 0.5, yy, x1 + 0.5, yy, 2.1), "parch", edge="dark",
                rad=2, cuts=(0.15, 0.4, 0.7), light=(-0.2, -0.9, 0.5), bias=0.1)
        cv.part("planknobL%d" % i, g.ell(x0 - 1.8, yy, 1.3, 2.6), "pencil", edge="dark", rad=2, bias=0.1)
        cv.part("planknobR%d" % i, g.ell(x1 + 1.8, yy, 1.3, 2.6), "pencil", edge="dark", rad=2, bias=0.1)


# --------------------------------------------------------------------------
# side view, facing RIGHT
# --------------------------------------------------------------------------
def side(g=None, k=1.0):
    if g is None:
        if k == 1:
            g = G(Cv(BW, BH), 40, BT, 1.0)
        else:
            g = G(Cv(WW, WH), WC - 2, WT, k)
    cv = g.cv
    big = g.k == 1
    sk = RAMP["skin"]
    # chair: base + column
    cv.part("column", g.rect(-1.6, 60, 1.8, 73), "metal", rad=2, cuts=(0.25, 0.55, 0.85), light=(-0.9, -0.2, 0.4))
    legs = g.cap(0, 73.8, -18, 77.6, 1.7) | g.cap(0, 73.8, 18, 77.6, 1.7) | g.ell(0, 74, 4, 2.3)
    cv.part("base", legs, "metal", rad=2, cuts=(0.2, 0.5, 0.8), bias=0.06)
    for i, dx in enumerate((-18.4, 18.4)):
        cv.part("caster%d" % i, g.ell(dx, 79.6, 2.7, 1.9), "chair", rad=2, cuts=(0.25, 0.5, 0.8))
    cv.part("casterM", g.ell(-4, 79.8, 2.6, 1.9), "chair", rad=2, cuts=(0.25, 0.5, 0.8))
    # chair back (behind her) + seat
    back = g.cap(-15.5, 29, -13.4, 55, 3.6) | g.cap(-13.4, 55, -10, 58.5, 2.6)
    cv.part("chairback", back, "chair", rad=g.rad(3), cuts=(0.3, 0.56, 0.9), light=(0.4, -0.7, 0.6))
    cv.part("seat", g.ell(-2, 60, 13.5, 2.9), "chair", rad=2, cuts=(0.25, 0.5, 0.85), bias=0.05)
    # far leg (slightly darker, behind)
    cv.part("thighF", g.cap(-6, 56.5, 7.6, 56.2, 4.0), "slacks", rad=3, bias=-0.15)
    cv.part("shinF", g.cap(6.8, 57, 8.6, 75.5, 3.3), "slacks", rad=3, bias=-0.15)
    cv.part("shoeF", g.ell(11.2, 79.2, 5.2, 2.6), "shoe", rad=3, bias=-0.1)
    # near leg
    cv.part("thigh", g.cap(-6, 55.6, 9, 56, 4.1), "slacks", rad=g.rad(4), soft=0.8, cuts=(0.3, 0.56, 0.88))
    cv.part("shin", g.cap(9.4, 57, 11, 75.5, 3.4), "slacks", rad=g.rad(3), soft=0.8, cuts=(0.3, 0.56, 0.88))
    sh = g.ell(13.6, 79.2, 5.6, 2.7)
    cv.part("shoe", sh, "shoe", rad=3, cuts=(0.3, 0.55, 0.85))
    g.put(16, 78, RAMP["shoe"][4])
    # torso
    tor = g.ell(-3, 46.5, 10.6, 10.4) | g.poly([(-12.8, 46.5), (6.2, 46.5), (5.0, 56.2), (-11.6, 56.2)])
    cv.part("torso", tor, "card", rad=g.rad(9), soft=1.6, cuts=(0.30, 0.52, 0.86), tex=0.05 if big else 0.0, seed=15)
    hem = tor & g.half(dy=54.2)
    cv.part("hem", hem, "card", noedge=("torso",), lv=np.where(hem, 1, 0) + np.where(hem & (cv.X < g.X(-2)), 1, 0))
    # blouse peeking at the front + bow from the side
    cv.part("blouse", g.poly([(3.6, 38.2), (7.0, 38.6), (6.0, 50), (4.4, 50)]), "blouse", rad=2, bias=0.1)
    cv.part("bowloops", g.ell(6.6, 39.2, 2.6, 2.4), "blouse", edge="dark", rad=2, bias=0.12)
    cv.part("bowtails", g.cap(7.2, 41, 8.2, 45.5, 1.1, 0.9), "blouse", edge="dark", rad=2, bias=0.05)
    # armrest under the elbow
    cv.part("post", g.rect(-3.4, 52, -1.4, 59.2), "metal", rad=2, cuts=(0.3, 0.6, 0.9))
    cv.part("pad", g.ell(-2.6, 51.4, 7.2, 1.9), "chair", rad=2, cuts=(0.2, 0.45, 0.8), bias=0.1)
    # scroll in the lap, seen end-on
    cv.part("scrollknob", g.ell(10.6, 52.4, 2.6, 2.8), "pencil", edge="dark", rad=2, bias=0.15)
    if big:
        cv.put(*g.p(10.6, 52.4), GLOW_HI)
    # arm
    arm(g, "arm", [(-4, 40), (-2.6, 49), (8.4, 52.8)], r=3.9)
    hand(g, "hand", 9.4, 53.6, rx=2.7, ry=2.6)
    # neck + head
    cv.part("neck", g.rect(-3.6, 31, 2.4, 38), "skin", rad=3, bias=-0.15)
    hb = g.ell(-3.4, 17, 17.2, 16.6) | g.ell(-13.8, 29.4, 5.4, 5.6)
    cv.part("hairback", hb, "hair", rad=g.rad(12), soft=1.6, cuts=(0.28, 0.52, 0.84), tex=0.05 if big else 0.0, seed=23)
    face = g.ell(2.6, 22, 10.4, 12.6) | g.ell(5.6, 30.4, 5.4, 4.6)
    cv.part("face", face, "skin", rad=g.rad(8), soft=1.4, cuts=(0.28, 0.50, 0.86), bias=0.08)
    side_hair = g.ell(-6.4, 18.6, 10.6, 13.6) | g.ell(-13.8, 29.4, 5.4, 5.6)
    side_hair |= g.ell(-1.6, 27.4, 3.4, 4.6)
    cv.part("sidehair", side_hair, "hair", noedge=("hairback",), rad=g.rad(9), soft=1.4, cuts=(0.28, 0.52, 0.84),
            tex=0.05 if big else 0.0, seed=27)
    nose = g.ell(12.6, 25.0, 1.7, 2.0)
    cv.part("nose", nose, "skin", edge="ink", noedge=("face",), rad=2, bias=0.14)
    dx = (cv.X - g.c) / g.k
    bang_edge = 13.8 - 0.20 * (dx + 4)
    bangs = (g.ell(-1, 13, 15.6, 12.8) & (cv.Y <= g.T + bang_edge * g.k)) | (g.ell(6.6, 9.8, 6.2, 4.2) & g.ell(-1, 13, 15.6, 12.8))
    cv.part("bangs", bangs, "hair", noedge=("hairback", "sidehair"), rad=g.rad(8), soft=1.4, cuts=(0.26, 0.50, 0.82),
            tex=0.05 if big else 0.0, seed=29, light=(-0.55, -0.85, 0.55))
    if big:
        c, t = g.c, g.T
        hr = RAMP["hair"]
        for (x0, y0, x1, y1) in [(-14, 8, -4, 4), (-12, 14, 0, 7), (-16, 20, -8, 16), (-6, 2, 6, 3)]:
            L = max(abs(x1 - x0), abs(y1 - y0))
            for s_ in range(L + 1):
                x, y = g.p(x0 + (x1 - x0) * s_ / L, y0 + (y1 - y0) * s_ / L)
                if (own_is(cv, x, y, "hairback") or own_is(cv, x, y, "bangs")) and cv.get(x, y) != hr[0]:
                    cv.put(x, y, hr[1])
        # eye, lash, brow
        for y in range(t + 20, t + 23):
            cv.put(c + 9, y, EYE)
        cv.put(c + 10, t + 20, EYE); cv.put(c + 10, t + 21, EYE); cv.put(c + 9, t + 20, WHITE)
        cv.hline(c + 8, c + 10, t + 19, EYE); cv.put(c + 7, t + 18, EYE)
        cv.hline(c + 7, c + 11, t + 15, hr[1]); cv.put(c + 12, t + 16, hr[1])
        # cat-eye lens edge-on + temple
        cv.vline(c + 11, t + 18, t + 23, FRAME); cv.vline(c + 12, t + 19, t + 23, FRAME)
        cv.put(c + 12, t + 18, FRAME); cv.put(c + 11, t + 17, FRAME); cv.put(c + 10, t + 16, FRAME_HI)
        cv.hline(c + 1, c + 10, t + 19, FRAME)
        # nose, blush, lips, earring
        cv.puts([(c + 13, t + 24), (c + 12, t + 23)], sk[3]); cv.puts([(c + 12, t + 27), (c + 13, t + 27)], sk[1])
        cv.puts([(c + 6, t + 25), (c + 7, t + 25), (c + 8, t + 26)], BLUSH)
        cv.puts([(c + 10, t + 29), (c + 11, t + 29)], LIP); cv.put(c + 9, t + 30, MOUTH); cv.puts([(c + 10, t + 30), (c + 11, t + 31)], MOUTH)
        cv.put(c + 10, t + 31, LIP)
        cv.put(c + 1, t + 31, WHITE); cv.put(c + 1, t + 32, LENS2)
        # bead chain from the temple, down behind the jaw
        for i, (x, y) in enumerate([(c + 1, t + 20), (c + 1, t + 22), (c + 1, t + 24), (c + 1, t + 26), (c + 2, t + 28),
                                    (c + 2, t + 30), (c + 3, t + 33), (c + 4, t + 35), (c + 5, t + 37)]):
            cv.put(x, y, BEAD if i % 2 == 0 else BEAD_DK)
    else:
        w_side_face(g)
    pencil(g, -2, 6, -9, -1.2)
    cv.outline()
    c, T = g.c, g.T
    if big:
        ticket(cv, c + 22, T + 14, "n"); trail(cv, [(c + 20, T + 12), (c + 18, T + 11)])
        ticket(cv, c - 36, T + 38, "u"); trail(cv, [(c - 30, T + 42), (c - 28, T + 43)])
        sparkle(cv, c + 15, T + 48, big=False)
    else:
        ticket(cv, c + 14, T + 9, "us"); ticket(cv, c - 22, T + 24, "hs")
    return cv


# --------------------------------------------------------------------------
# back view: mostly chair, with the bouffant on top
# --------------------------------------------------------------------------
def back(g=None, k=1.0):
    if g is None:
        if k == 1:
            g = G(Cv(BW, BH), 42, BT, 1.0)
        else:
            g = G(Cv(WW, WH), WC, WT, k)
    cv = g.cv
    big = g.k == 1
    # shoes (on the floor in front of the chair) + base
    for s in (-1, 1):
        cv.part("shoe%d" % s, g.ell(s * 7.2, 79.4, 4.4, 2.4) & g.half(dy=78.2), "shoe", rad=2, bias=-0.15)
    chair_base_front(g)
    # her elbows on the armrests poke out past the chair back
    for s in (-1, 1):
        cv.part("post%d" % s, g.rect(s * 19.8 - 1.1, 52, s * 19.8 + 1.1, 59.5), "metal", rad=2, cuts=(0.3, 0.6, 0.9))
        arm(g, "arm%d" % s, [(s * 15, 39), (s * 19.6, 48.6)], r=4.1)
        cv.part("pad%d" % s, g.ell(s * 20, 51.4, 4.4, 1.9), "chair", rad=2, cuts=(0.2, 0.45, 0.8), bias=0.1)
    # hair (back of the bouffant)
    hb = g.ell(0, 17, 19, 17) | g.ell(-14.8, 29.2, 5.6, 5.8) | g.ell(14.8, 29.2, 5.6, 5.8)
    cv.part("hairback", hb, "hair", rad=g.rad(13), soft=1.6, cuts=(0.28, 0.52, 0.84), tex=0.05 if big else 0.0, seed=37)
    hr = RAMP["hair"]
    if big:
        # backcombed swirl
        for (x0, y0, x1, y1) in [(-12, 6, -2, 14), (-14, 14, -6, 24), (2, 4, 12, 10), (6, 12, 15, 20), (-4, 20, 4, 24), (-8, 2, 6, 2)]:
            L = max(abs(x1 - x0), abs(y1 - y0))
            for s_ in range(L + 1):
                x, y = g.p(x0 + (x1 - x0) * s_ / L, y0 + (y1 - y0) * s_ / L)
                if own_is(cv, x, y, "hairback") and cv.get(x, y) != hr[0]:
                    cv.put(x, y, hr[1])
    pencil(g, -8, 6, -20.5, 1.2)
    # chair back, seen from behind
    cb = chair_back_front(g, "chairback")
    ch = RAMP["chair"]
    if big:
        c, T = g.c, g.T
        # plastic shell seam + lumbar ridge
        for x in range(c - 17, c + 18):
            y = T + 46 + int(round(((x - c) / 17.0) ** 2 * 3))
            if own_is(cv, x, y, "chairback"):
                cv.put(x, y, ch[1])
            if own_is(cv, x, y + 1, "chairback"):
                cv.put(x, y + 1, ch[3])
        # a ticket taped to the back: NOW SERVING
        tr = RAMP["ticket"]
        for y in range(T + 32, T + 38):
            for x in range(c - 4, c + 5):
                cv.put(x, y, tr[2] if y > T + 32 else tr[3])
        cv.hline(c - 4, c + 4, T + 38, tr[0]); cv.vline(c + 5, T + 32, T + 38, tr[0])
        cv.hline(c - 2, c + 2, T + 34, WHITE); cv.hline(c - 1, c + 1, T + 36, WHITE)
        cv.puts([(c - 5, T + 31), (c - 4, T + 31), (c + 4, T + 31), (c + 5, T + 31)], (226, 222, 200))  # tape
        # adjustment lever under the seat
        cv.part("lever", g.cap(10, 59.6, 17, 61.4, 0.9), "metal", rad=1)
    else:
        tr = RAMP["ticket"]
        x, y = g.p(-1.5, 33)
        cv.puts([(x, y), (x + 1, y), (x + 2, y)], tr[3]); cv.puts([(x, y + 1), (x + 2, y + 1)], tr[2]); cv.put(x + 1, y + 1, WHITE)
    cv.outline()
    c, T = g.c, g.T
    if big:
        ticket(cv, c - 34, T + 16, "u"); trail(cv, [(c - 28, T + 14), (c - 26, T + 13)])
        ticket(cv, c + 30, T + 34, "n")
    else:
        ticket(cv, c - 22, T + 9, "us"); ticket(cv, c + 18, T + 21, "vs")
    return cv


# ==========================================================================
# WORLD (50 px standing height, redrawn small -- not scaled)
# ==========================================================================
def w_face(g, pose, blink=False):
    cv = g.cv
    sk, hr = RAMP["skin"], RAMP["hair"]
    c, t = int(round(g.c)), g.T
    # face centre row is t + 22*k ~ t+13; eyes at t+12
    ey = int(round(g.Y(21)))
    ly, my = int(round(g.Y(17))), int(round(g.Y(30)))
    # blush
    cv.put(c - 5, ey + 3, BLUSH); cv.put(c + 5, ey + 3, BLUSH)
    # glasses: two 5x4 red frames with wings
    tilt = 1 if pose == "hit" else 0
    glint = pose in ("tell", "grin")
    for side in (-1, 1):
        xa, xb = (c - 6, c - 2) if side < 0 else (c + 2, c + 6)
        dy = tilt if side > 0 else 0
        for y in range(ey, ey + 2):
            for x in range(xa + 1, xb):
                cv.put(x, y + dy, LENS if glint else mix(cv.get(x, y + dy), LENS, 0.18))
        cv.hline(xa, xb, ey - 1 + dy, FRAME)
        cv.hline(xa + 1, xb - 1, ey + 2 + dy, FRAME)
        cv.vline(xa, ey - 1 + dy, ey + 1 + dy, FRAME); cv.vline(xb, ey - 1 + dy, ey + 1 + dy, FRAME)
        o = xa if side < 0 else xb
        cv.put(o + side, ey - 2 + dy, FRAME)
    cv.put(c, ey, FRAME); cv.put(c - 1, ey, FRAME); cv.put(c + 1, ey, FRAME)
    # eyes
    for side in (-1, 1):
        x = c - 4 if side < 0 else c + 4
        dy = tilt if side > 0 else 0
        if glint:
            cv.put(c - 5 if side < 0 else c + 3, ey + dy, WHITE)
            continue
        if blink:
            cv.put(x, ey + 1 + dy, EYE); cv.put(x + (-1 if side < 0 else 1), ey + 1 + dy, EYE)
        elif pose == "hit":
            cv.put(x, ey + dy, EYE); cv.put(x - side, ey + 1 + dy, EYE)
        else:
            cv.put(x, ey + dy, EYE); cv.put(x, ey + 1 + dy, EYE)
            cv.put(x - side * 0 + (-1 if side < 0 else 1), ey + dy, EYE)
    # brows
    for side in (-1, 1):
        x0 = c - 5 if side < 0 else c + 3
        yb = ey - 3 if pose != "hit" else ey - 3
        cv.hline(x0, x0 + 2, yb, hr[1])
    # mouth
    if pose in ("talk", "grin"):
        cv.hline(c - 1, c + 1, my - 1, MOUTH); cv.put(c, my, TONGUE); cv.put(c - 1, my, MOUTH); cv.put(c + 1, my, MOUTH)
    elif pose == "hit":
        cv.hline(c - 2, c + 2, my - 1, MOUTH); cv.put(c - 1, my - 1, TEETH); cv.put(c + 1, my - 1, TEETH)
    else:
        cv.hline(c - 1, c + 1, my - 1, LIP); cv.put(c - 2, my - 2, MOUTH); cv.put(c + 2, my - 2, MOUTH)
    cv.put(c, ey + 3, sk[1])


def w_side_face(g):
    cv = g.cv
    sk, hr = RAMP["skin"], RAMP["hair"]
    c, t = int(round(g.c)), g.T
    ey = int(round(g.Y(21)))
    cv.put(c + 5, ey, EYE); cv.put(c + 5, ey + 1, EYE); cv.put(c + 4, ey - 1, EYE)
    cv.vline(c + 7, ey - 1, ey + 1, FRAME); cv.put(c + 6, ey - 2, FRAME)
    cv.hline(c - 1, c + 6, ey - 1, FRAME)
    cv.hline(c + 4, c + 6, ey - 3, hr[1])
    cv.put(c + 4, ey + 2, BLUSH)
    my = int(round(g.Y(29.5)))
    cv.put(c + 6, my, LIP); cv.put(c + 5, my, MOUTH)


# ==========================================================================
# PORTRAITS (64 x 64, head and shoulders, chair back behind)
# ==========================================================================
PW = PH = 64
IRIS = (60, 40, 34)
IRIS2 = (118, 76, 48)
SCLERA = (240, 236, 230)


def p_eye(cv, ex, ey, expr, side):
    """Pixel-map eyes. (ex, ey) = top-left of a 7-wide cell for the viewer-left
    eye; the right eye is mirrored.  Column 0 is the outer corner."""
    sk = RAMP["skin"]
    maps = {
        "neutral": ["K......",
                    ".KKKKK.",
                    ".KIHIIK",
                    "..IIDI.",
                    "...SS..."],
        "warm":    ["K......",
                    ".KKKK..",
                    "K....K.",
                    ".S..S..",
                    "......."],
        "concern": [".......",
                    "KKKKKK.",
                    ".KIHIK.",
                    "..IDI..",
                    "...SS.."],
        "surprised": ["K..KK..",
                      ".KKWWK.",
                      ".KWIHWK",
                      ".KWIIWK",
                      "..KWWK.",
                      "...SS.."],
        "closed":  ["K......",
                    ".......",
                    ".KKKKK.",
                    "..SSS..",
                    "......."],
    }
    pal = {"K": EYE, "I": IRIS, "H": WHITE, "W": SCLERA, "S": sk[1], "D": IRIS2}
    rows = maps[expr]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "." or i > 6:
                continue
            x = ex + i if side < 0 else ex + (6 - i)
            cv.put(x, ey + j, pal[ch])
    hs = [(j, r.index("H")) for j, r in enumerate(rows) if "H" in r]
    if side > 0 and hs:
        j, i = hs[0]
        xr = ex + (6 - i)
        cv.put(xr, ey + j, IRIS)
        cv.put(xr - 1, ey + j, WHITE)


def p_brows(cv, c, by, expr):
    hr = RAMP["hair"]
    if expr == "concern":
        # one brow up, one down: the over-the-glasses look
        left = [(0, -1), (-1, -1), (-2, 0), (-3, 0), (-4, 0), (-5, 0), (-6, 1), (-7, 1)]
        right = [(0, 1), (-1, 0), (-2, 0), (-3, -1), (-4, -1), (-5, -1), (-6, -1), (-7, 0)]
    elif expr == "surprised":
        left = right = [(0, -1), (-1, -2), (-2, -2), (-3, -3), (-4, -3), (-5, -3), (-6, -2), (-7, -1)]
    elif expr == "warm":
        left = right = [(0, 0), (-1, -1), (-2, -1), (-3, -2), (-4, -2), (-5, -2), (-6, -1), (-7, 0)]
    else:
        left = right = [(0, 0), (-1, 0), (-2, -1), (-3, -1), (-4, -1), (-5, -1), (-6, 0), (-7, 1)]
    for side, shape in ((-1, left), (1, right)):
        ix = c - 4 if side < 0 else c + 4
        for i, (dx, dy) in enumerate(shape):
            x = ix + dx if side < 0 else ix - dx
            cv.put(x, by + dy, hr[0] if 1 < i < 6 else hr[1])
            if 1 < i < 5:
                cv.put(x, by + dy + 1, hr[1])


def p_mouth(cv, c, my, expr, talk=False):
    sk = RAMP["skin"]
    if expr == "neutral":
        if not talk:
            cv.hline(c - 3, c + 3, my, MOUTH)
            cv.put(c - 4, my - 1, MOUTH); cv.put(c + 4, my - 1, MOUTH)
            cv.hline(c - 2, c + 2, my - 1, LIP); cv.put(c, my - 1, MOUTH)
            cv.hline(c - 2, c + 2, my + 1, LIP); cv.hline(c - 1, c + 0, my + 1, LIP_HI)
        else:
            cv.hline(c - 2, c + 2, my - 1, LIP); cv.put(c, my - 1, MOUTH)
            cv.put(c - 4, my - 1, MOUTH); cv.put(c + 4, my - 1, MOUTH)
            cv.hline(c - 3, c + 3, my, MOUTH); cv.hline(c - 2, c + 2, my, TEETH)
            cv.hline(c - 2, c + 2, my + 1, MOUTH); cv.hline(c - 1, c + 1, my + 1, TONGUE)
            cv.hline(c - 2, c + 2, my + 2, LIP); cv.hline(c - 1, c, my + 2, LIP_HI)
    elif expr == "warm":
        o = 1 if talk else 0
        cv.hline(c - 5, c + 5, my - 1, MOUTH)
        cv.put(c - 6, my - 2, MOUTH); cv.put(c + 6, my - 2, MOUTH)
        cv.hline(c - 4, c + 4, my, TEETH)
        cv.put(c - 5, my, MOUTH); cv.put(c + 5, my, MOUTH)
        for k in range(o + 1):
            cv.hline(c - 4, c + 4, my + 1 + k, MOUTH)
        cv.hline(c - 2, c + 2, my + 1 + o, TONGUE)
        cv.hline(c - 3, c + 3, my + 2 + o, LIP); cv.hline(c - 1, c + 1, my + 2 + o, LIP_HI)
        cv.put(c - 4, my + 1 + o, LIP) if o else None
        cv.put(c + 4, my + 1 + o, LIP) if o else None
    elif expr == "concern":
        if not talk:
            cv.hline(c - 2, c + 3, my, MOUTH)
            cv.put(c - 3, my + 1, MOUTH); cv.put(c + 4, my - 1, MOUTH)
            cv.hline(c - 1, c + 2, my + 1, LIP)
        else:
            cv.hline(c - 1, c + 2, my - 1, LIP)
            cv.put(c - 2, my, MOUTH); cv.put(c + 4, my - 1, MOUTH)
            cv.hline(c - 1, c + 3, my, MOUTH)
            cv.hline(c - 1, c + 2, my + 1, MOUTH); cv.hline(c, c + 1, my + 1, TONGUE)
            cv.hline(c - 1, c + 2, my + 2, LIP)
    elif expr == "surprised":
        h = 5 if talk else 4
        widths = (1, 2, 2, 2, 1) if not talk else (1, 2, 2, 2, 2, 1)
        for dy, w in enumerate(widths):
            cv.hline(c - w, c + w, my + dy - 1, MOUTH)
        cv.hline(c - 1, c + 1, my + len(widths) - 3, TONGUE)
        cv.hline(c - 1, c + 1, my - 2, LIP)
        cv.hline(c - 1, c + 1, my + len(widths) - 1, LIP)


def portrait(expr, talk=False):
    cv = Cv(PW, PH, open_bottom=True)
    c = 32
    sk, hr, cd = RAMP["skin"], RAMP["hair"], RAMP["card"]
    lift = -1 if expr == "surprised" else 0
    gl = 3 if expr == "concern" else 0        # glasses slid down: she looks over them
    # ---- chair back behind the shoulders ----
    cb = (cv.ell(c, 50, 30, 12) & cv.half(y=50, below=False)) | cv.rect(2, 50, 61, 64)
    cv.part("chairback", cb, "chair", rad=10, soft=1.6, cuts=(0.30, 0.56, 0.9), tex=0.04, seed=73)
    # ---- shoulders ----
    sh = cv.ell(c, 66, 34, 14) & cv.half(y=50)
    cv.part("shoulders", sh, "card", rad=13, soft=2.0, cuts=(0.30, 0.52, 0.84), tex=0.06, seed=41)
    vee = cv.poly([(c - 8, 53), (c + 8, 53), (c + 2, 64), (c - 2, 64)])
    cv.part("blouse", vee, "blouse", rad=4, cuts=(0.2, 0.5, 0.9), bias=0.08)
    cv.put(c - 9, 58, BUTTON); cv.put(c - 9, 59, YELLOW_DK); cv.put(c - 7, 63, BUTTON)
    cv.part("neck", cv.rect(c - 6, 44, c + 6, 54), "skin", rad=5, bias=-0.18)
    cv.part("bowloops", cv.ell(c - 4.6, 55.4, 4.2, 2.7, -0.15) | cv.ell(c + 4.6, 55.4, 4.2, 2.7, 0.15), "blouse",
            edge="dark", rad=3, cuts=(0.2, 0.45, 0.8), bias=0.1)
    cv.part("bowtails", cv.capsule(c - 1.2, 58, c - 3.4, 63, 1.4, 1.1) | cv.capsule(c + 1.2, 58, c + 2.8, 63, 1.4, 1.1),
            "blouse", edge="dark", noedge=("blouse",), rad=2, bias=0.05)
    cv.part("knot", cv.ell(c, 55.6, 1.8, 2.0), "blouse", edge="dark", rad=2, bias=0.2)
    # ---- hair (back volume + flips) ----
    hb = cv.ell(c, 25 + lift, 26.5, 24) | cv.ell(8.6, 42 + lift, 6.4, 6.6) | cv.ell(55.4, 42 + lift, 6.4, 6.6)
    cv.part("hairback", hb, "hair", rad=16, soft=2.0, cuts=(0.28, 0.52, 0.84), tex=0.05, seed=43)
    # ---- face ----
    face = cv.ell(c, 32.6, 15.4, 16.6)
    cv.part("face", face, "skin", rad=13, soft=2.2, cuts=(0.28, 0.50, 0.84), bias=0.07)
    # jaw shadow onto the neck
    for x in range(c - 6, c + 7):
        if cv.own[50, x] == cv.names["neck"]:
            cv.put(x, 50, sk[1])
    # ---- bangs ----
    dx = cv.X - c
    edge = 22.0 + lift - 0.28 * (dx + 16) - 0.008 * dx * dx
    bang = cv.ell(c, 25 + lift, 26.5, 24) & (cv.Y <= edge)
    bang |= cv.ell(c + 15, 15 + lift, 7, 5) & cv.ell(c, 25 + lift, 26.5, 24)
    cv.part("bangs", bang, "hair", noedge=("hairback",), rad=12, soft=1.8, cuts=(0.26, 0.50, 0.82), tex=0.05, seed=47,
            light=(-0.55, -0.85, 0.55))
    for (x0, y0, x1, y1) in [(8, 14, 22, 22), (12, 8, 30, 17), (20, 4, 40, 12), (34, 4, 50, 9), (6, 22, 13, 26),
                             (44, 12, 54, 16), (26, 2, 44, 5)]:
        L = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(L + 1):
            x = round(x0 + (x1 - x0) * k / L); y = round(y0 + (y1 - y0) * k / L) + lift
            if 0 <= y < PH and cv.own[y, x] == cv.names["bangs"] and cv.get(x, y) != hr[0]:
                cv.put(x, y, hr[1] if cv.get(x, y) in (hr[2], hr[1]) else hr[2])
    for (x0, y0, x1, y1) in [(5, 30, 7, 38), (58, 30, 56, 38), (9, 36, 12, 44), (55, 36, 52, 44), (4, 42, 6, 46), (60, 42, 58, 46)]:
        L = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(L + 1):
            x = round(x0 + (x1 - x0) * k / L); y = round(y0 + (y1 - y0) * k / L) + lift
            if 0 <= y < PH and cv.own[y, x] == cv.names["hairback"] and cv.get(x, y) != hr[0]:
                cv.put(x, y, hr[1])
    # ---- cheeks ----
    for s in (-1, 1):
        bx = c + s * 10
        rows = (37, 38, 39) if expr != "warm" else (36, 37, 38, 39)
        for y in rows:
            for x in range(bx - 3, bx + 4):
                if cv.own[y, x] == cv.names["face"]:
                    cv.put(x, y, mix(cv.get(x, y), BLUSH, 0.5 if abs(x - bx) < 3 else 0.3))
    # ---- nose ----
    cv.puts([(c - 1, 35), (c - 1, 36)], sk[3])
    cv.puts([(c + 1, 37), (c + 1, 38), (c, 39)], sk[1])
    cv.puts([(c - 2, 39), (c + 2, 39)], mix(sk[1], sk[0], 0.4))
    cv.put(c - 1, 39, sk[2])
    # ---- mouth ----
    p_mouth(cv, c, 43 if expr != "warm" else 42, expr, talk)
    # ---- glasses + eyes ----
    y0, y1 = 27 + gl, 34 + gl
    for side in (-1, 1):
        xa, xb = (c - 15, c - 3) if side < 0 else (c + 3, c + 15)
        for y in range(y0 + 1, y1):
            for x in range(xa + 1, xb):
                cv.put(x, y, mix(cv.get(x, y), LENS, 0.12 if not gl else 0.30))
    ey = {"neutral": 28, "warm": 29, "concern": 24, "surprised": 27}[expr]
    for side in (-1, 1):
        ex = c - 12 if side < 0 else c + 6
        p_eye(cv, ex, ey, "closed" if expr == "blink" else expr, side)
    for side in (-1, 1):
        xa, xb = (c - 15, c - 3) if side < 0 else (c + 3, c + 15)
        o = xa if side < 0 else xb
        cv.hline(xa, xb, y0, FRAME); cv.hline(xa + 1, xb - 1, y0 - 1 + 0, FRAME) if False else None
        cv.hline(xa + 1, xb - 1, y1, FRAME)
        cv.vline(xa, y0, y1 - 1, FRAME); cv.vline(xb, y0, y1 - 1, FRAME)
        # cat-eye wing: heavier top toward the outside, flicking up
        for k in range(5):
            cv.put(o - side * k, y0 - 1, FRAME)
        cv.put(o + side * 1, y0 - 1, FRAME); cv.put(o + side * 1, y0 - 2, FRAME); cv.put(o + side * 2, y0 - 3, FRAME)
        cv.put(o + side * 2, y0 - 2, FRAME_HI if side < 0 else FRAME)
        cv.hline(xa + 1, xa + 4, y0, FRAME_HI) if side < 0 else cv.hline(xa + 1, xa + 3, y0, FRAME_HI)
        if expr != "concern":
            cv.puts([(xa + 2, y0 + 2), (xa + 3, y0 + 2), (xa + 2, y0 + 3)], mix(LENS, (255, 255, 255), 0.5))
        else:
            cv.puts([(xa + 2, y1 - 2), (xa + 3, y1 - 2)], mix(LENS, (255, 255, 255), 0.5))
    cv.hline(c - 2, c + 2, y0 + 2, FRAME)
    # ---- brows ----
    by = {"neutral": 24, "warm": 24, "concern": 21, "surprised": 22}[expr]
    p_brows(cv, c, by, expr)
    # ---- bead chain: temples -> along the jaw -> loop at the collar ----
    for side in (-1, 1):
        pts = [(17.6, 29 + gl), (19.2, 34), (18.6, 40), (16, 46), (11, 51), (6, 53.6)]
        n = 0
        for (xa_, ya), (xb_, yb) in zip(pts, pts[1:]):
            L = math.hypot(xb_ - xa_, yb - ya)
            kk = 0.0
            while kk < L:
                x = c + side * (xa_ + (xb_ - xa_) * kk / L); y = ya + (yb - ya) * kk / L
                cv.put(round(x), round(y), BEAD if n % 2 == 0 else BEAD_DK)
                n += 1
                kk += 1.8
    # pearl earrings
    for s in (-1, 1):
        x = c + s * 17
        cv.puts([(x, 43), (x + 1, 43)], WHITE); cv.puts([(x, 44), (x + 1, 44)], LENS2)
    # ---- pencil in the bouffant ----
    pc = RAMP["pencil"]
    pen = cv.capsule(44, 9 + lift, 62, 2 + lift, 1.7)
    cv.part("pencil", pen, "pencil", edge="dark", rad=2, cuts=(0.2, 0.5, 0.85), light=(-0.3, -0.9, 0.4))
    er = cv.capsule(59, 3.2 + lift, 62.5, 1.8 + lift, 1.7) & pen
    cv.fill(er, RAMP["ticket"][3])
    cv.fill(cv.capsule(57.5, 3.8 + lift, 58.4, 3.4 + lift, 1.9) & pen, RAMP["metal"][2])
    cv.outline()
    if expr == "warm":
        ticket(cv, 2, 4, "u"); ticket(cv, 56, 22, "v")
    if expr == "surprised":
        ticket(cv, 1, 6, "n"); ticket(cv, 57, 20, "u")
        cv.puts([(54, 14), (54, 15), (54, 16), (54, 18)], SPARK2)
    if expr == "concern":
        cv.puts([(5, 14), (6, 13), (7, 14)], SPARK2) if False else None
    return cv


# ==========================================================================
# ENTRANCE (intro card): she spins in on the chair, the plan unfurls overhead
# like a banner, tickets everywhere, pointing at you: "NEXT!"
# ==========================================================================
EW, EH = 128, 104


def banner(cv, pts, w=10.0, name="banner"):
    """A glowing ribbon of course boxes along a polyline."""
    best = np.full((cv.h, cv.w), 1e9)
    sval = np.zeros((cv.h, cv.w))
    off = np.zeros((cv.h, cv.w))
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        vx, vy = x1 - x0, y1 - y0
        L = math.hypot(vx, vy) or 1e-9
        t = np.clip(((cv.X - x0) * vx + (cv.Y - y0) * vy) / (L * L), 0, 1)
        px, py = x0 + t * vx, y0 + t * vy
        d = (cv.X - px) ** 2 + (cv.Y - py) ** 2
        upd = d < best
        best[upd] = d[upd]
        sval[upd] = acc + t[upd] * L
        off[upd] = (((cv.X - px) * (-vy) + (cv.Y - py) * vx) / L)[upd]
        acc += L
    band = best <= (w / 2) ** 2
    cv.part(name, band, "parch", edge="dark", lv=np.where(band, 4, 0))
    ink_edge = band & (cv.col[..., 0] == RAMP["parch"][0][0]) & (cv.col[..., 1] == RAMP["parch"][0][1])
    inner = band & ~ink_edge
    cv.fill(inner, GLOW_HI)
    box = 7.0
    cell = np.floor(sval / box).astype(int)
    divider = inner & (((sval % box) < 1.0) | (np.abs(off) < 0.5))
    cv.fill(divider, GLOW_DK)
    nboxes = int(acc // box)
    ys, xs = np.nonzero(inner & ~divider)
    for y, x in zip(ys, xs):
        k = cell[y, x]
        sub = sval[y, x] % box
        row = off[y, x] > 0
        idx = 2 * k + int(row)
        if idx == 2 * (nboxes - 3) + 1:            # the one missing credit
            cv.put(x, y, (210, 40, 52) if not (3.0 < sub < 4.2 and 1.6 < abs(off[y, x]) < 2.8) else WHITE)
        elif 3.0 < sub < 4.4 and 1.6 < abs(off[y, x]) < 2.9 and (k + int(row)) % 3:
            cv.put(x, y, CHECK)
    return band, acc


def entrance_full():
    """Draw the figure, then the banner behind/above, then props after the ink."""
    cv = Cv(EW, EH)
    T = EH - 82
    c = 60
    g = G(cv, c, T, 1.0)
    # banner first so the figure overlaps its low end; it streams from her raised
    # right hand, arcs over her head and falls away to the left
    pts = [(c + 28, T + 1), (c + 30, T - 10), (c + 22, T - 17), (c + 6, T - 19), (c - 12, T - 16),
           (c - 28, T - 9), (c - 40, T + 2), (c - 47, T + 16), (c - 49, T + 30)]
    band, L = banner(cv, pts, w=11.0)
    # end roll at the far end
    cv.part("bannerroll", cv.capsule(c - 55, T + 31, c - 43, T + 31, 2.4), "parch", edge="dark", rad=2,
            cuts=(0.15, 0.4, 0.7), light=(-0.2, -0.9, 0.5), bias=0.1)
    cv.part("bannerknobL", cv.ell(c - 57, T + 31, 1.4, 2.9), "pencil", edge="dark", rad=2, bias=0.1)
    cv.part("bannerknobR", cv.ell(c - 41, T + 31, 1.4, 2.9), "pencil", edge="dark", rad=2, bias=0.1)
    front("grin", g=g)      # ends with the ink pass for everything so far
    # the roll in her hand (drawn over the outline, then re-inked locally)
    sub = Cv(EW, EH)
    sub.part("roll", sub.capsule(c + 21, T + 2, c + 35, T + 2, 2.4), "parch", edge="dark", rad=2,
             cuts=(0.15, 0.4, 0.7), light=(-0.2, -0.9, 0.5), bias=0.1)
    sub.part("knobL", sub.ell(c + 19, T + 2, 1.4, 2.9), "pencil", edge="dark", rad=2, bias=0.1)
    sub.part("knobR", sub.ell(c + 37, T + 2, 1.4, 2.9), "pencil", edge="dark", rad=2, bias=0.1)
    sub.part("handR", sub.ell(c + 27.6, T + 4.4, 2.9, 3.0), "skin", edge="ink", rad=2.5, soft=0.8, bias=0.06)
    sub.outline()
    m = sub.alpha
    cv.col[m] = sub.col[m]; cv.alpha |= m
    # glow halo around the banner + sparkles
    glow_ring(cv, "banner", GLOW, every=1)
    for (x, y, b) in [(c + 38, T - 14, True), (c - 4, T - 25, False), (c - 50, T - 2, True), (c - 56, T + 22, False),
                      (c + 14, T - 25, False), (c - 30, T - 20, False)]:
        if 2 <= y < EH - 2:
            sparkle(cv, x, y, big=b)
    # speed lines from the right (she just spun in)
    for (x0, x1, y) in [(c + 34, c + 56, T + 52), (c + 38, c + 64, T + 59), (c + 33, c + 52, T + 66), (c + 40, c + 66, T + 73)]:
        for x in range(x0, x1 + 1):
            if (x - x0) % 8 < 6 and not cv.alpha[y, x]:
                cv.put(x, y, (176, 188, 224) if (x - x0) % 8 < 4 else WHITE)
    # spin arc around the base + skid dust
    for i in range(60):
        a = math.pi * (0.02 + 0.96 * i / 59)
        x = int(round(c + 31 * math.cos(a))); y = int(round(T + 78 - 5 * math.sin(a)))
        if 0 <= y < EH and not cv.alpha[y, x] and i % 6 != 5:
            cv.put(x, y, WHITE if i % 3 else (176, 188, 224))
    for (x, y) in [(c + 28, T + 81), (c + 31, T + 80), (c + 33, T + 81), (c + 35, T + 81), (c - 28, T + 81), (c - 31, T + 81)]:
        cv.put(x, y, (200, 196, 210))
    # tickets in a swirl around her
    for (x, y, k) in [(c - 40, T + 32, "u"), (c - 44, T + 58, "h"), (c - 30, T + 70, "n"), (c + 36, T + 26, "v"),
                      (c + 44, T + 40, "u"), (c + 50, T + 12, "h"), (c - 26, T + 30, "v"), (c + 12, T - 4, "n"),
                      (c - 18, T - 2, "u")]:
        ticket(cv, x, y, k)
    trail(cv, [(c - 34, T + 31), (c - 32, T + 30), (c - 30, T + 30)])
    trail(cv, [(c - 40, T + 56), (c - 41, T + 54), (c - 41, T + 52)])
    trail(cv, [(c + 42, T + 46), (c + 40, T + 48), (c + 38, T + 49)])
    trail(cv, [(c + 48, T + 16), (c + 46, T + 18), (c + 44, T + 19)])
    return cv


# ==========================================================================
# output
# ==========================================================================
BW, BH = 84, 92
BT = BH - 82
WW, WH = 56, 56
WK = 50 / 82
WT = WH - 50 - 0.4
WC = 28


def foot_of(cv):
    y = cv.h - 1
    xs = [x for x in range(cv.w) if cv.alpha[y, x]]
    return [int(round((min(xs) + max(xs)) / 2)), y]


def body_height(img):
    a = np.array(img)[..., 3] > 0
    rows = np.nonzero(a.any(axis=1))[0]
    assert rows[-1] == img.height - 1, "feet not on bottom row"
    return img.height - rows[0]


def build():
    os.makedirs(OUT, exist_ok=True)
    feet, cells = {}, {}
    battle = [front("idle"), front("talk"), front("tell"), front("hit"), side(), back()]
    world = [front("idle", k=WK), front("talk", k=WK), front("tell", k=WK), front("hit", k=WK), side(k=WK), back(k=WK)]
    # foot pivot = the chair's column centre on the floor row
    for prefix, group, c in (("battle", battle, None), ("world", world, None)):
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            img.save(os.path.join(OUT, name))
            cells[name] = img
            centre = 40 if (prefix == "battle" and i == 4) else 42 if prefix == "battle" else (WC - 2 if i == 4 else WC)
            feet[name] = [centre, img.height - 1]
            print(name, img.size, "height", body_height(img), "foot", feet[name])
    for name, cv in (("idle-blink.png", front("idle", k=WK, blink=True)), ("idle-pose1.png", front("pose1", k=WK)),
                     ("idle-pose2.png", front("pose2", k=WK))):
        img = cv.image(); img.save(os.path.join(OUT, name)); cells[name] = img
    for i, e in enumerate(("neutral", "warm", "concern", "surprised")):
        for talk, pre in ((False, "portrait"), (True, "talk")):
            img = portrait(e, talk).image()
            name = "%s-%d.png" % (pre, i)
            img.save(os.path.join(OUT, name)); cells[name] = img
    ent = entrance_full().image()
    ent.save(os.path.join(OUT, "entrance.png")); cells["entrance.png"] = ent
    feet["entrance.png"] = [60, EH - 1]
    print("entrance", ent.size, "height", body_height(ent))
    with open(os.path.join(OUT, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    return cells, feet


YELLOW_DK = (176, 120, 30)

if __name__ == "__main__":
    build()
