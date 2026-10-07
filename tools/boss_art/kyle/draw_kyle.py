#!/usr/bin/env python3
"""Kyle, Pearl Street founder -- procedural pixel-art sprites for "After Hours - College Tale"
(Pearl Street internship mini-boss).

Drawn the way Professor Eric is drawn (tools/eric_art/draw_eric.py), on the same tiny raster engine as
the other new bosses (newcast/chad): parts are masks shaded with material ramps from a top-left key
light, given inner 1px lines and an ink silhouette.  Everything is drawn at its final pixel size;
nothing drawn is ever resampled (only the contact sheet and the private previews are
nearest-neighbour blow-ups).

Look: a blaze-orange high-pile fleece vest (navy binding, navy zip chest pocket, no logo) over a
charcoal mock-neck long-sleeve with the sleeves shoved up, stone slim chinos, chunky white sneakers,
a black textured quiff and a trimmed beard, a smartwatch, and a presentation clicker with a red
laser.  His signature ride is a matte-black electric kick scooter with a lime LED underglow, a
headlight and a speed readout.  In battle he rides it (84 = hair top to wheel contact; he stands 78
on the 6px deck); in the world he stands in front of it, parked.

Outputs:
  cells/battle-0..5.png   92x92 battle cells on the scooter (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  cells/entrance.png      cell 12 "kyle-entrance": a scooter manual with the clicker thrust up (wide canvas)
  cells/world-0..5.png    56x56 world cells, 52px standing in front of the parked scooter
  cells/portrait-0..3.png 64x64 portraits (0 neutral, 1 warm, 2 concern, 3 surprised)
  cells/talk/kyle-<f>.png        mouth-open portraits
  cells/idle/kyle-{blink,pose1,pose2}.png   world-front idle extras (pose1 checks his metrics on his
                                 phone, pose2 sips an iced oat latte)
  cells/kyle-deck.png + kyle-deck.json      battle-only prop: the pitch deck projected behind him
  cells/feet.json         foot point [x, y] for every body cell
build_sheet.py packs these into out/.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = os.path.join(HERE, "cells")
PREV = os.path.join(HERE, "prev")

# --------------------------------------------------------------------------
# palette (Eric's ramp convention: 0 = line/darkest, 1 shadow, 2 mid, 3 light, 4 highlight)
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline, shared with the cast

RAMP = {
    "skin":   [(74, 38, 26), (134, 80, 50), (172, 112, 72), (200, 142, 98), (224, 174, 130)],
    "hair":   [(14, 10, 16), (38, 32, 42), (62, 54, 66), (96, 86, 100), (140, 130, 146)],
    "beard":  [(24, 18, 24), (44, 34, 40), (64, 52, 56), (90, 76, 78), (120, 104, 104)],
    "vest":   [(104, 34, 12), (184, 72, 22), (230, 110, 36), (248, 152, 64), (255, 200, 128)],
    "trim":   [(12, 16, 38), (24, 32, 66), (38, 50, 98), (60, 76, 130), (94, 110, 168)],
    "tee":    [(16, 16, 24), (38, 38, 50), (58, 58, 72), (84, 84, 102), (120, 120, 140)],
    "pants":  [(66, 54, 38), (128, 110, 80), (170, 152, 116), (200, 186, 150), (228, 218, 188)],
    "shoe":   [(70, 72, 86), (160, 164, 178), (208, 212, 222), (234, 236, 242), (252, 252, 252)],
    "deck":   [(10, 10, 16), (30, 32, 42), (52, 56, 68), (80, 86, 100), (122, 130, 146)],
    "tyre":   [(8, 8, 12), (40, 40, 50), (60, 60, 72), (88, 88, 102), (122, 122, 138)],
    "metal":  [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "cup":    [(110, 112, 124), (178, 186, 196), (214, 222, 230), (236, 242, 246), (252, 254, 255)],
    "latte":  [(84, 52, 32), (150, 104, 70), (190, 148, 108), (214, 180, 142), (234, 210, 178)],
    "phone":  [(10, 10, 16), (28, 30, 40), (44, 48, 60), (70, 76, 90), (110, 118, 134)],
}
EYE = (26, 16, 20)
IRIS = (96, 58, 34)          # warm brown eyes
WHITE = (250, 248, 244)
SCLERA = (238, 232, 224)
MOUTH = (70, 24, 28)
LIP = (150, 76, 64)
TONGUE = (192, 88, 92)
TEETH = (252, 250, 244)
TEETH2 = (210, 208, 210)
BLUSH = (190, 96, 72)
BROW = (20, 14, 20)
LIME = (190, 255, 84)        # scooter LEDs / speed readout / smartwatch
LIME2 = (126, 214, 48)
LIME3 = (66, 130, 36)
LASER = (255, 46, 60)
LASER2 = (255, 150, 150)
LIGHT = (255, 252, 230)      # headlight
LIGHT2 = (255, 234, 150)
TAIL = (236, 40, 50)
SPARK = (255, 250, 210)
SPARK2 = (255, 214, 90)
SWEAT = (120, 196, 240)
SWEAT_HI = (220, 244, 255)
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
def paint_map(cv, x0, y0, rows, pal, name="map"):
    """Hand-placed pixels; they join the alpha so the ink pass outlines them like any part."""
    pid = len(cv.names)
    cv.names[name] = pid
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in pal:
                x, y = x0 + i, y0 + j
                if 0 <= x < cv.w and 0 <= y < cv.h:
                    cv.put(x, y, pal[ch])
                    cv.own[y, x] = pid


def sparkle(cv, x, y, big=True, col=SPARK2):
    pts = [(x, y - 2), (x, y - 1), (x, y + 1), (x, y + 2), (x - 2, y), (x - 1, y), (x + 1, y), (x + 2, y)]
    if not big:
        pts = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
    cv.puts(pts, col)
    cv.put(x, y, WHITE)


def shifted(a, dy, dx, fill):
    """out[y, x] = a[y + dy, x + dx] (the neighbour at offset dy, dx)."""
    h, w = a.shape
    out = np.full_like(a, fill)
    ys, yd = slice(max(0, dy), h + min(0, dy)), slice(max(0, -dy), h + min(0, -dy))
    xs, xd = slice(max(0, dx), w + min(0, dx)), slice(max(0, -dx), w + min(0, -dx))
    out[yd, xd] = a[ys, xs]
    return out


def binding(cv, part, nbrs, color, empty=False):
    """Sewn edge: recolour the pixels of `part` that touch a part in `nbrs` (or nothing, if empty)."""
    if part not in cv.names:
        return
    pid = cv.names[part]
    ids = [cv.names[n] for n in nbrs if n in cv.names]
    m = cv.own == pid
    hit = np.zeros_like(m)
    for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nb = shifted(cv.own, dy, dx, -1)
        hit |= m & np.isin(nb, ids)
        if empty:
            hit |= m & (nb == -1)
    cv.col[hit & (np.abs(cv.col - np.array(INK)).sum(axis=2) > 0)] = color


def top_edge(cv, part, color, rows=1):
    if part not in cv.names:
        return
    m = cv.own == cv.names[part]
    for x in range(cv.w):
        ys = np.nonzero(m[:, x])[0]
        for y in ys[:rows]:
            cv.put(x, y, color)


def head_pal():
    sk, hr, bd, te = RAMP["skin"], RAMP["hair"], RAMP["beard"], RAMP["tee"]
    return {"K": INK, "0": hr[0], "1": hr[1], "2": hr[2], "3": hr[3], "4": hr[4],
            "s": sk[2], "l": sk[3], "h": sk[4], "d": sk[1], "x": sk[0],
            "b": bd[2], "n": bd[1], "v": bd[3], "E": EYE, "W": SCLERA, "w": WHITE, "I": IRIS, "B": BROW,
            "T": TEETH, "t": TEETH2, "M": MOUTH, "L": LIP, "o": TONGUE, "r": BLUSH, "c": te[2], "C": te[1]}


def clicker(cv, x0, y0, x1, y1, name="clicker"):
    """Presentation clicker: a little graphite stick, red laser button at the tip end."""
    m = cv.capsule(x0, y0, x1, y1, 1.3)
    cv.part(name, m, "phone", edge="ink", rad=1.5, soft=0.4, light=(-0.7, -0.6, 0.5))
    return m


def laser(cv, x0, y0, x1, y1, dot=True):
    """The laser beam (after the ink pass so it stays a clean 1px line) ending in a bright dot."""
    n = int(max(abs(x1 - x0), abs(y1 - y0)))
    for k in range(1, n + 1):
        x = x0 + (x1 - x0) * k / n
        y = y0 + (y1 - y0) * k / n
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < cv.w and 0 <= yi < cv.h and not cv.alpha[yi, xi]:
            cv.put(xi, yi, LASER if k % 3 else LASER2)
    if dot:
        xi, yi = int(round(x1)), int(round(y1))
        cv.puts([(xi - 1, yi), (xi + 1, yi), (xi, yi - 1), (xi, yi + 1)], LASER)
        cv.put(xi, yi, WHITE)


# ==========================================================================
# BATTLE  (84 = hair top to wheel contact; 78 standing on a 6px deck)
# ==========================================================================
BW, BH = 92, 92
BATTLE_H = 84
BT = BH - BATTLE_H          # hair top row


def b_hand(cv, x, y, name, rx=2.6, ry=2.8):
    m = cv.ell(x, y, rx, ry)
    cv.part(name, m, "skin", edge="ink", rad=2.5, soft=0.7, bias=0.05)
    return m


def b_arm(cv, name, S, E, W, r0=3.3, push=0.38, watch=False, far=False, fr=2.1):
    """Charcoal long sleeve shoved up past the elbow: sleeve from the shoulder to a bunched cuff,
    then a bare forearm to the wrist.  watch=True straps the smartwatch on that wrist."""
    (sx, sy), (ex, ey), (wx, wy) = S, E, W
    kx, ky = ex + (wx - ex) * push, ey + (wy - ey) * push
    cuts = (0.45, 0.72, 0.95) if far else (0.24, 0.50, 0.84)
    fore = cv.capsule(kx, ky, wx, wy, fr, fr - 0.3)
    cv.part(name + "fore", fore, "skin", edge="dark", rad=2, soft=0.6, bias=-0.1 if far else 0.05, cuts=cuts)
    sl = cv.capsule(sx, sy, ex, ey, r0, r0 - 0.5) | cv.capsule(ex, ey, kx, ky, r0 - 0.5, r0 - 0.1)
    cv.part(name, sl, "tee", edge="dark", rad=3, soft=0.9, cuts=cuts)
    # bunched cuff: a light ridge across the sleeve end
    L = math.hypot(wx - kx, wy - ky) or 1
    ux, uy = (wx - kx) / L, (wy - ky) / L
    ridge = sl & cv.capsule(kx - ux * 1.2 - uy * 3, ky - uy * 1.2 + ux * 3, kx - ux * 1.2 + uy * 3, ky - uy * 1.2 - ux * 3, 0.6)
    ys, xs = np.nonzero(ridge)
    for y, x in zip(ys, xs):
        if cv.get(x, y) != RAMP["tee"][0]:
            cv.put(x, y, RAMP["tee"][3] if not far else RAMP["tee"][2])
    if watch:
        px, py = wx - ux * 1.0, wy - uy * 1.0
        band = cv.capsule(px - uy * 2.6, py + ux * 2.6, px + uy * 2.6, py - ux * 2.6, 0.7) & fore
        cv.fill(band, RAMP["deck"][1])
        cv.put(px - uy * 0.6, py + ux * 0.6, LIME)
    return sl


# ---- scooter, head-on (front and back views) ------------------------------
def scooter_deck_front(cv, c, t, back=False):
    """The deck strip under his soles (drawn before the legs)."""
    dk = RAMP["deck"]
    deck = cv.rect(c - 7, t + 78, c + 7, t + 81)
    lv = np.where(deck, 2, 0) + np.where(deck & (cv.Y == t + 78), 1, 0) - np.where(deck & (cv.Y >= t + 80), 1, 0)
    cv.part("deck", deck, "deck", edge="ink", lv=lv)
    for x in range(c - 6, c + 7):
        cv.put(x, t + 80, LIME2 if abs(x - c) > 3 else LIME)   # LED strip along the deck's flank


def scooter_front(cv, c, t, tilt=0.0, grips=True):
    """Front wheel + fender, the stem rising in front of him to a T-bar at hip height, a lime speed
    readout and a headlight.  tilt (px) slews the bar for the hit pose.  Returns the grip points."""
    dk, mt = RAMP["deck"], RAMP["metal"]
    wheel = cv.ell(c, t + 78.6, 3.3, 4.9)
    cv.part("wheel", wheel, "tyre", edge="ink", rad=2, soft=0.5, cuts=(0.3, 0.6, 0.95))
    cv.puts([(c - 1, t + 77), (c - 1, t + 78), (c - 1, t + 79)], RAMP["tyre"][4])
    cv.vline(c, t + 77, t + 80, RAMP["metal"][2])
    fender = cv.ell(c, t + 74.8, 4.6, 1.8) & cv.half(y=t + 75.4, below=False)
    cv.part("fender", fender, "deck", edge="ink", rad=2, soft=0.5, bias=0.1)
    top = (c + tilt * 0.5, t + 45)
    stem = cv.capsule(c, t + 73.5, top[0], top[1], 2.1)
    cv.part("stem", stem, "deck", edge="ink", rad=2.2, soft=0.6, cuts=(0.25, 0.5, 0.8), light=(-0.8, -0.3, 0.5))
    for k, y in enumerate(range(t + 57, t + 66)):
        x = int(round(c + (top[0] - c) * (t + 78 - y) / 33.0))
        cv.put(x, y, LIME2 if k % 4 else LIME)                  # reflective accent stripe
    # headlight under the bar
    hx = c + (top[0] - c) * 0.88
    lamp = cv.ell(hx, t + 49.5, 2.1, 1.6)
    cv.part("lamp", lamp, "metal", edge="ink", lv=np.where(lamp, 4, 0))
    cv.fill(lamp & ~shifted(~lamp, 0, 0, True), LIGHT)
    # T-bar with grips
    tb = tilt * 0.55
    L, R = (c - 16 + tilt, t + 44 + tb), (c + 16 + tilt, t + 44 - tb)
    bar = cv.capsule(L[0], L[1], R[0], R[1], 1.05)
    cv.part("bar", bar, "metal", edge="ink", rad=1.2, soft=0.4, bias=0.1)
    gl, gr = None, None
    if grips:
        for s, (gx, gy) in ((-1, L), (1, R)):
            g = cv.capsule(gx - s * 4.0, gy + s * tb * 0.25, gx + s * 0.5, gy - s * tb * 0.03, 1.6)
            cv.part("grip%d" % s, g, "tyre", edge="ink", rad=1.5, soft=0.4)
    # display pod on the stem head
    dx0 = int(round(top[0]))
    pod = cv.rect(dx0 - 3, t + 40, dx0 + 3, t + 43)
    cv.part("pod", pod, "deck", edge="ink", lv=np.where(pod, 2, 0))
    cv.puts([(dx0 - 2, t + 41), (dx0 - 1, t + 41), (dx0 + 1, t + 41), (dx0 - 2, t + 42), (dx0 + 1, t + 42), (dx0 + 2, t + 42)], LIME)
    cv.put(dx0 + 2, t + 41, LIME3)
    gl = (L[0] + 1.5, L[1])
    gr = (R[0] - 1.5, R[1])
    return gl, gr


def headlight_rays(cv, x, y):
    for (dx, dy) in ((-4, 0), (-3, 0), (4, 0), (3, 0), (-3, -2), (3, -2), (-3, 2), (3, 2)):
        xi, yi = int(round(x + dx)), int(round(y + dy))
        if 0 <= xi < cv.w and 0 <= yi < cv.h and not cv.alpha[yi, xi]:
            cv.put(xi, yi, LIGHT2 if abs(dx) == 3 else LIGHT)


def underglow(cv, x0, x1, y, gap=None):
    for x in range(int(x0), int(x1) + 1):
        if gap and gap[0] <= x <= gap[1]:
            continue
        if not cv.alpha[y, x]:
            cv.put(x, y, LIME3 if (x % 3) else LIME2)


# ---- body, front --------------------------------------------------------------
def b_legs(cv, c, t, back=False):
    """Slim stone chinos with a rolled hem; chunky white sneakers side by side on the deck."""
    pr, sr = RAMP["pants"], RAMP["shoe"]
    for s in (-1, 1):
        pts = [(s * 0.5, 46), (s * 10, 46), (s * 10, 52), (s * 8.5, 62), (s * 8, 72), (s * 1.5, 72), (s * 1, 62), (s * 0.5, 53)]
        leg = cv.poly([(c + x, t + y) for x, y in pts])
        cv.part("leg%d" % s, leg, "pants", rad=4, soft=1.0, cuts=(0.30, 0.56, 0.9), tex=0.02, seed=9 + s)
    cv.vline(c, t + 51, t + 54, pr[0])
    for s in (-1, 1):
        cv.line(c + s * 5, t + 57, c + s * 5, t + 69, pr[1] if s < 0 else pr[0])
        cv.hline(c + 2 if s > 0 else c - 7, c + 7 if s > 0 else c - 2, t + 71, pr[3] if s < 0 else pr[2])
        if not back:
            cv.line(c + s * 7, t + 47, c + s * 9, t + 51, pr[1])
    for s in (-1, 1):
        sx = c + s * 4.6
        sh = cv.ell(sx, t + 75.2, 4.9, 3.3) & cv.half(y=t + 77, below=False) & cv.half(y=t + 72.6)
        cv.part("shoe%d" % s, sh, "shoe", rad=2.5, soft=0.7, cuts=(0.30, 0.55, 0.85))
        ys, xs = np.nonzero(sh & (cv.Y == t + 76))
        for x in xs:
            if cv.get(x, t + 76) != sr[0]:
                cv.put(x, t + 76, sr[1])                         # chunky midsole line
        if not back:
            cv.puts([(sx - 1, t + 73), (sx + 1, t + 73)], sr[1])  # laces
        cv.put(sx + s * 3, t + 74, RAMP["vest"][2])              # orange heel tab


def b_torso(cv, c, t, back=False):
    te, vs, tr, mt = RAMP["tee"], RAMP["vest"], RAMP["trim"], RAMP["metal"]
    # mock-neck tee: the roll collar hugs the neck under the beard
    mock = cv.rect(c - 4, t + 17, c + 4, t + 23)
    cv.part("mock", mock, "tee", rad=3, soft=0.8, cuts=(0.2, 0.5, 0.85))
    cv.hline(c - 3, c + 3, t + 19, te[1])
    shirt = cv.poly([(c - 11, t + 21), (c + 11, t + 21), (c + 14, t + 25), (c + 13, t + 35), (c + 11, t + 48),
                     (c - 11, t + 48), (c - 13, t + 35), (c - 14, t + 25)])
    shirt |= cv.ell(c - 11.5, t + 25.5, 3.6, 3.4) | cv.ell(c + 11.5, t + 25.5, 3.6, 3.4)
    cv.part("shirt", shirt, "tee", rad=6, soft=1.2, cuts=(0.24, 0.50, 0.84))
    vest = cv.poly([(c - 8, t + 21), (c + 8, t + 21), (c + 10, t + 25), (c + 9.5, t + 30), (c + 11, t + 35),
                    (c + 12, t + 48), (c - 12, t + 48), (c - 11, t + 35), (c - 9.5, t + 30), (c - 10, t + 25)])
    cv.part("vest", vest, "vest", rad=8, soft=1.6, cuts=(0.26, 0.50, 0.84), tex=0.12, seed=5)
    binding(cv, "vest", ("shirt",), tr[2])                         # armhole binding
    hem = vest & cv.half(y=t + 47)
    cv.part("hem", hem, "trim", noedge=("vest",), lv=np.where(hem, 2, 0) + np.where(hem & (cv.X < c - 3), 1, 0))
    if back:
        for x in range(c - 9, c + 10):                             # yoke seam
            y = t + 27 + abs(x - c) // 5
            if cv.own[y, x] == cv.names["vest"]:
                cv.put(x, y, vs[1])
        top_edge(cv, "vest", tr[2])
        return
    # stand collar opened by the full zip, navy-bound along the top
    colm = cv.poly([(c - 7, t + 19), (c - 1, t + 21), (c - 1, t + 25), (c - 8, t + 23)]) | \
        cv.poly([(c + 7, t + 19), (c + 1, t + 21), (c + 1, t + 25), (c + 8, t + 23)])
    cv.part("collar", colm, "vest", rad=2, soft=0.6, bias=0.12, tex=0.08, seed=3)
    top_edge(cv, "collar", tr[2])
    for y in range(t + 24, t + 47):                               # zip
        cv.put(c, y, tr[1] if y % 2 else mt[1])
    cv.puts([(c, t + 25), (c, t + 26)], mt[3]); cv.put(c + 1, t + 26, mt[2])
    # navy zip chest pocket on his left chest (viewer right)
    pk = cv.rect(c + 3, t + 28, c + 7, t + 32)
    cv.part("pocket", pk, "trim", edge="dark", noedge=("vest",), lv=np.where(pk, 2, 0) + np.where(pk & (cv.Y == t + 28), 1, 0))
    cv.put(c + 7, t + 29, mt[3])
    # pile catching the key light on the left chest
    for x in range(c - 8, c - 4):
        cv.put(x, t + 27 + (c - 6 - x) // 2, vs[3])


def b_face_front(cv, c, t, pose):
    sk, bd = RAMP["skin"], RAMP["beard"]
    ey = t + 11
    # brows: thick and straight, one hiked up for the pitch
    for s in (-1, 1):
        x0 = c + s * 2
        lift = 1 if (pose == "tell" and s < 0) else 0
        for k in range(4):
            yy = ey - 2 - lift - (1 if (pose == "hit" and k == 0) else 0) + (1 if (pose == "tell" and s > 0 and k == 0) else 0)
            cv.put(x0 + s * k, yy, BROW)
    for s in (-1, 1):
        ex = c + s * 3 - (1 if s < 0 else 0)
        if pose == "hit":
            cv.puts([(ex, ey), (ex + 1, ey + 1)] if s < 0 else [(ex + 1, ey), (ex, ey + 1)], EYE)
            cv.put(ex + (1 if s < 0 else 0), ey + 1 if s < 0 else ey + 1, EYE)
            continue
        if pose == "tell" and s > 0:                               # the wink
            cv.hline(ex - 1, ex + 1, ey + 1, EYE); cv.put(ex + 2, ey, EYE)
            continue
        cv.put(ex, ey, EYE); cv.put(ex + 1, ey, EYE)
        cv.put(ex, ey + 1, IRIS); cv.put(ex + 1, ey + 1, EYE)
        cv.put(ex, ey, WHITE)
        cv.put(ex - 1 if s < 0 else ex + 2, ey + 1, SCLERA)
    # nose
    cv.puts([(c, t + 12), (c, t + 13)], sk[3])
    cv.puts([(c + 1, t + 13), (c + 1, t + 14)], sk[1])
    cv.puts([(c - 1, t + 14), (c, t + 14)], sk[1])
    # moustache
    cv.hline(c - 3, c + 3, t + 15, bd[2]); cv.puts([(c - 3, t + 15), (c - 2, t + 15)], bd[3])
    my = t + 16
    if pose == "idle":
        cv.hline(c - 3, c + 3, my, TEETH); cv.put(c + 2, my, TEETH2)
        cv.puts([(c - 4, my - 1), (c + 4, my - 1), (c - 4, my), (c + 4, my)], MOUTH)
        cv.hline(c - 2, c + 2, my + 1, MOUTH)
    elif pose == "talk":
        cv.hline(c - 3, c + 3, my, TEETH); cv.put(c + 2, my, TEETH2)
        cv.puts([(c - 4, my - 1), (c + 4, my - 1), (c - 4, my), (c + 4, my)], MOUTH)
        cv.hline(c - 3, c + 3, my + 1, MOUTH); cv.hline(c - 1, c + 1, my + 1, TONGUE)
        cv.hline(c - 2, c + 2, my + 2, MOUTH)
    elif pose == "tell":
        cv.hline(c - 2, c + 4, my, TEETH); cv.put(c + 3, my, TEETH2)
        cv.puts([(c - 3, my), (c + 5, my - 1), (c + 5, my)], MOUTH)
        cv.hline(c - 1, c + 4, my + 1, MOUTH)
    elif pose == "hit":
        cv.hline(c - 3, c + 3, my, MOUTH)
        cv.hline(c - 2, c + 2, my + 1, TEETH); cv.puts([(c - 1, my + 1), (c + 1, my + 1)], TEETH2)
        cv.puts([(c - 3, my + 1), (c + 3, my + 1)], MOUTH)
        cv.hline(c - 2, c + 2, my + 2, MOUTH)


def b_head_front(cv, c, t, pose):
    """Frontal head; t is the top of the quiff."""
    sk, hr, bd = RAMP["skin"], RAMP["hair"], RAMP["beard"]
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 7.3, t + 12, 1.7, 2.4), "skin", bias=0.05)
    face = cv.ell(c, t + 11.6, 6.8, 7.4) | cv.poly([(c - 6.5, t + 12), (c + 6.5, t + 12), (c + 5.6, t + 17),
                                                   (c + 2.6, t + 20), (c - 2.6, t + 20), (c - 5.6, t + 17)])
    cv.part("face", face, "skin", rad=6, soft=1.4, cuts=(0.30, 0.52, 0.86))
    # trimmed beard: sideburns down the jaw into the chin; the cheeks stay clear
    dx = np.abs(cv.X - c)
    beard = face & ((((dx >= 5.6) & (cv.Y >= t + 12))) | (cv.Y >= t + 18) | ((cv.Y >= t + 16) & (dx >= 4.0)))
    lvb = np.where(beard, 2, 0) + np.where(beard & (cv.X < c - 1) & (cv.Y < t + 19), 1, 0) - np.where(beard & (cv.Y >= t + 19), 1, 0)
    cv.part("beard", beard, "beard", edge=None, lv=lvb, tex=0.12, seed=21)
    for y in range(t + 12, t + 21):                                # soft stubble edge against the cheek
        for x in range(c - 6, c + 7):
            if cv.own[y, x] == cv.names["beard"]:
                for nx in (x - 1, x + 1):
                    if cv.own[y, nx] == cv.names["face"] and abs(nx - c) < 6 and (nx + y) % 2 == 0:
                        cv.put(nx, y, mix(sk[1], bd[2], 0.35))
    # ---- hair: faded sides, a tall textured quiff ----
    skull = cv.ell(c, t + 8.5, 7.6, 5.8) & cv.half(y=t + 9.5, below=False) & ((cv.Y <= t + 6.5) | (dx >= 5.2))
    skull |= cv.capsule(c - 7, t + 7, c - 7.1, t + 11, 1.2) | cv.capsule(c + 7, t + 7, c + 7.1, t + 11, 1.2)
    cv.part("hair", skull, "hair", lv=np.where(skull, 1, 0) + np.where(skull & (cv.X < c - 3), 1, 0))
    quiff = cv.poly([(c - 7.6, t + 8), (c - 7.5, t + 4.5), (c - 6, t + 2), (c - 4, t + 0.6), (c - 2.6, t + 1.6),
                     (c - 1.2, t + 0.0), (c + 1.5, t + 0.0), (c + 2.6, t + 1.4), (c + 4.4, t + 0.6), (c + 6.4, t + 2.2),
                     (c + 7.7, t + 4.6), (c + 7.8, t + 8), (c + 6.4, t + 6.4), (c + 4, t + 5.8), (c + 1.5, t + 6.4),
                     (c - 1, t + 5.8), (c - 3.5, t + 6.5), (c - 6, t + 7.6)])
    cv.part("quiff", quiff, "hair", rad=3.5, soft=1.0, cuts=(0.10, 0.34, 0.66), light=(-0.6, -0.8, 0.5), tex=0.05, seed=7, noedge=("hair",))
    cv.line(c - 4, t + 2, c - 3, t + 4, hr[4]); cv.line(c, t + 1, c + 1, t + 3, hr[4])
    cv.line(c - 2, t + 3, c - 1, t + 5, hr[0]); cv.line(c + 3, t + 2, c + 3, t + 4, hr[1])
    cv.put(c - 5, t + 3, hr[3]); cv.put(c + 5, t + 3, hr[3])
    # forehead shadow under the hairline
    for x in range(c - 6, c + 7):
        for y in range(t + 5, t + 11):
            if cv.own[y, x] == cv.names["face"] and cv.own[y - 1, x] in (cv.names["hair"], cv.names["quiff"]):
                cv.put(x, y, sk[1])
                break
    b_face_front(cv, c, t, pose)


def b_front(pose):
    cv = Cv(BW, BH)
    c, t = 46, BT
    tilt = 3 if pose == "hit" else 0
    scooter_deck_front(cv, c, t)
    b_legs(cv, c, t)
    b_torso(cv, c, t)
    gl, gr = scooter_front(cv, c, t, tilt=tilt)
    # viewer-left arm: on the grip in every pose
    b_arm(cv, "armL", (c - 12, t + 25), (c - 16, t + 35), (gl[0] + 0.5, gl[1] - 2.5))
    b_hand(cv, gl[0], gl[1], "handL")
    cv.put(gl[0] + 1, gl[1] + 1, RAMP["skin"][1])
    if pose == "idle":
        b_arm(cv, "armR", (c + 12, t + 25), (c + 16, t + 35), (gr[0] - 0.5, gr[1] - 2.5), watch=True)
        b_hand(cv, gr[0], gr[1], "handR")
        cv.put(gr[0] - 1, gr[1] + 1, RAMP["skin"][1])
    elif pose == "talk":
        # "hear me out": index finger up
        b_arm(cv, "armR", (c + 12, t + 25), (c + 19, t + 33), (c + 21, t + 26), watch=True)
        b_hand(cv, c + 21, t + 23.5, "handR", rx=2.5, ry=2.6)
        fing = cv.capsule(c + 21, t + 21, c + 21, t + 16.5, 1.05)
        cv.part("finger", fing, "skin", edge="ink", noedge=("handR",), rad=1.2, soft=0.4, bias=0.1)
    elif pose == "tell":
        # clicker thrust at the viewer, laser on
        b_arm(cv, "armR", (c + 12, t + 25), (c + 19, t + 30), (c + 23, t + 22), watch=True)
        clicker(cv, c + 23, t + 20, c + 26, t + 14)
        b_hand(cv, c + 23, t + 20.5, "handR", rx=2.6, ry=2.6)
    elif pose == "hit":
        b_arm(cv, "armR", (c + 12, t + 25), (c + 19, t + 30), (c + 22, t + 23), watch=True)
        b_hand(cv, c + 22, t + 21, "handR")
        clicker(cv, c + 33, t + 9, c + 36, t + 6, name="flyclick")
    b_head_front(cv, c + (2 if pose == "hit" else 0), t, pose)
    cv.outline()
    headlight_rays(cv, c + tilt * 0.44, t + 49.5)
    underglow(cv, c - 9, c + 9, BH - 1, gap=(c - 3, c + 3))
    if pose == "tell":
        cv.put(c + 27, t + 13, LASER)
        laser(cv, c + 27, t + 13, c + 42, t - 4)
        sparkle(cv, c - 11, t + 16)
    if pose == "hit":
        cv.puts([(c + 38, t + 4), (c + 31, t + 4), (c + 39, t + 10)], SPARK2)
        sx, sy = c - 10, t + 1
        cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx + 1, sy + 1), (sx - 1, sy + 2), (sx, sy + 2), (sx + 1, sy + 2), (sx, sy + 3)], SWEAT)
        cv.put(sx - 1, sy + 1, SWEAT_HI)
    return cv


# ---- scooter in profile (side view, entrance) ------------------------------
def scooter_side(cv, x0, g, ang=0.0, wb=38.0, R=5.0, scale=1.0):
    """Profile facing right.  x0 = rear tyre contact, g = ground row, ang tilts it nose-up about the
    rear contact.  Returns a function mapping (u, v) scooter coords to canvas, the grip and the lamp."""
    ca, sa = math.cos(ang), math.sin(ang)

    def P(u, v):
        return (x0 + u * ca - v * sa, g - (u * sa + v * ca))
    s = scale
    # deck: grip-tape top, LED flank, ink underside (between the wheels)
    deck = cv.poly([P(3.0, 2.0 * s), P(wb - 6, 2.0 * s), P(wb - 4.5, 5.6 * s), P(2.0, 5.6 * s)])
    cv.part("deck", deck, "deck", edge="ink", rad=1.5, soft=0.4, cuts=(0.2, 0.5, 0.9))
    for k in range(4, int(wb - 6)):
        x, y = P(k, 2.8 * s)
        cv.put(x, y, LIME if k % 6 == 0 else LIME2)
    # neck from the deck nose up into the stem
    neck = cv.poly([P(wb - 7, 2.2 * s), P(wb - 3.5, 3.0 * s), P(wb - 0.4, 12.0 * s), P(wb - 3.6, 12.0 * s)])
    cv.part("neck", neck, "deck", edge="ink", rad=1.5, soft=0.4)
    # wheels (in front of the deck ends)
    for name, u in (("wheelR", 0.0), ("wheelF", wb)):
        hx, hy = P(u, R - 0.5)
        m = cv.ell(hx, hy, R - 0.1, R - 0.1)
        cv.part(name, m, "tyre", edge="ink", rad=2.5, soft=0.6, cuts=(0.3, 0.6, 0.95))
        hub = cv.ell(hx, hy, R * 0.45, R * 0.45)
        cv.fill(hub & m, RAMP["deck"][3])
        cv.put(hx, hy, RAMP["metal"][3]); cv.put(hx - 1, hy - 1, RAMP["metal"][2])
    # rear fender + tail light
    fen = cv.poly([P(-R - 1.2, R + 0.6), P(-R + 0.2, R + 4.0), P(0.5, R + 5.0), P(R + 0.8, R + 3.4), P(R + 1.2, 5.6 * s),
                   P(R - 0.6, R + 2.6), P(0, R + 3.2), P(-R + 1.0, R + 2.4)])
    cv.part("fender", fen, "deck", edge="ink", rad=1.5, soft=0.4, bias=0.1)
    tx, ty = P(-R - 0.4, R + 1.4)
    cv.put(tx, ty, TAIL); cv.put(tx + 1, ty, TAIL)
    # stem from the front hub, leaning back toward the rider
    sb, st = P(wb - 3.5 * (2 * R + 1) / 39.5, 2 * R + 1), P(wb - 3.5, 39.5 * s)
    stem = cv.capsule(sb[0], sb[1], st[0], st[1], 1.9 * (0.75 + 0.25 * s))
    hb = P(wb, R)
    fork = cv.capsule(hb[0], hb[1], sb[0], sb[1], 0.9)
    cv.part("fork", fork, "metal", edge="ink", lv=np.where(fork, 2, 0))
    cv.part("stem", stem, "deck", edge="ink", rad=2, soft=0.5, cuts=(0.25, 0.5, 0.8), light=(-0.8, -0.3, 0.5))
    for k in range(int(14 * s), int(24 * s)):
        x, y = P(wb - 3.5 * k / 39.5 - 0.2, k)
        cv.put(x, y, LIME2 if k % 4 else LIME)
    cv.put(*P(wb, R), RAMP["metal"][4])
    lx, ly = P(wb - 3.5 * 31 / 39.5 + 1.6 * s, 31 * s)
    lamp = cv.ell(lx, ly, 1.4 * s + 0.3, 1.8 * s)
    cv.part("lamp", lamp, "metal", edge="ink", lv=np.where(lamp, 4, 0))
    gx, gy = P(wb - 3.8, 39.6 * s)
    grip = cv.ell(gx, gy, 1.7 * s + 0.2, 1.7 * s + 0.2)
    cv.part("grip", grip, "tyre", edge="ink", rad=1.5, soft=0.4)
    px_, py_ = P(wb - 2.4, 41.6 * s)
    pod = cv.ell(px_, py_, 2.4 * s, 1.4 * s + 0.2)
    cv.part("pod", pod, "deck", edge="ink", lv=np.where(pod, 2, 0))
    cv.put(px_ + 1, py_, LIME)
    return P, (gx, gy), (lx, ly)


def leg_side(cv, name, hip, knee, ankle, far=False, r=(4.4, 3.4, 2.8)):
    m = cv.capsule(hip[0], hip[1], knee[0], knee[1], r[0], r[1]) | cv.capsule(knee[0], knee[1], ankle[0], ankle[1], r[1], r[2])
    cv.part(name, m, "pants", rad=3, soft=0.9, cuts=(0.45, 0.72, 0.95) if far else (0.30, 0.56, 0.9), tex=0.02, seed=31)
    return m


def shoe_side(cv, name, x, sole, far=False, ang=0.0):
    """Chunky sneaker in profile, toe to the right; x = heel-to-toe centre, sole = sole row."""
    m = cv.ell(x + 0.6, sole - 2.0, 5.2, 3.2, ang) & (cv.Y <= sole + 0.4 + (cv.X - x) * math.tan(-ang)) & \
        (cv.Y >= sole - 4.4 + (cv.X - x) * math.tan(-ang))
    cv.part(name, m, "shoe", rad=2, soft=0.6, cuts=(0.45, 0.72, 0.95) if far else (0.30, 0.55, 0.85))
    ys, xs = np.nonzero(m)
    for y, xx in zip(ys, xs):
        if abs(y - (sole - 1 + (xx - x) * math.tan(-ang))) < 0.5 and cv.get(xx, y) != RAMP["shoe"][0]:
            cv.put(xx, y, RAMP["shoe"][1])
    cv.put(x - 4, sole - 2 - (-4) * math.tan(-ang) * 0, RAMP["vest"][2])
    return m


def head_side(cv, hx, t, pose="idle"):
    """Profile head facing right; hx = neck centre, t = top of the quiff."""
    sk, hr, bd = RAMP["skin"], RAMP["hair"], RAMP["beard"]
    skull = cv.ell(hx - 1.5, t + 10.6, 7.0, 7.0)
    face = cv.poly([(hx + 1, t + 5), (hx + 5, t + 6), (hx + 6.4, t + 9), (hx + 6.6, t + 11), (hx + 8.4, t + 13.6),
                    (hx + 6.8, t + 14.6), (hx + 7.2, t + 16.4), (hx + 6.6, t + 18.2), (hx + 5.6, t + 20.2),
                    (hx + 2, t + 20.8), (hx - 2.5, t + 18)])
    head = skull | face
    cv.part("face", head, "skin", rad=6, soft=1.2, cuts=(0.24, 0.48, 0.84), light=(0.25, -0.7, 0.68))
    # beard: a sideburn in front of the ear, then the jaw line down to a full chin
    beard = head & (((cv.Y >= t + 16.4 + (cv.X - hx) * 0.22) & (cv.X >= hx - 3.0)))
    lvb = np.where(beard, 2, 0) + np.where(beard & (cv.Y < t + 18) & (cv.X > hx + 2), 1, 0) - np.where(beard & (cv.Y >= t + 19), 1, 0)
    cv.part("beard", beard, "beard", edge=None, lv=lvb, tex=0.1, seed=23)
    # hair: cap over the back of the skull + the quiff swept up and forward, shaded as one mass
    cap = head & ((cv.Y < t + 6.5) | ((cv.X < hx - 0.5) & (cv.Y < t + 9.5)) | ((cv.X < hx - 3.2) & (cv.Y < t + 15.5)))
    cap &= ~beard
    quiff = cv.poly([(hx - 7.5, t + 6.5), (hx - 6.4, t + 2.6), (hx - 3.4, t + 0.6), (hx + 0.5, t + 0), (hx + 4.5, t + 0.2),
                     (hx + 7.6, t + 1.6), (hx + 9.0, t + 4.0), (hx + 7.6, t + 5.8), (hx + 5.4, t + 6.4), (hx + 2.5, t + 5.8),
                     (hx - 0.5, t + 6.8)])
    hair = cap | quiff
    cv.part("hair", hair, "hair", rad=4, soft=1.0, cuts=(0.10, 0.34, 0.66), light=(-0.6, -0.8, 0.5), tex=0.05, seed=9)
    cv.line(hx - 4, t + 2, hx + 2, t + 1, hr[4]); cv.line(hx - 3, t + 4, hx + 4, t + 3, hr[1])
    cv.line(hx + 4, t + 2, hx + 7, t + 3, hr[3]); cv.line(hx - 6, t + 8, hx - 5, t + 12, hr[1])
    # ear
    ear = cv.ell(hx - 2.0, t + 12, 1.8, 2.5)
    cv.part("ear", ear, "skin", bias=0.25, light=(0.25, -0.7, 0.68))
    cv.put(hx - 2, t + 12, sk[1]); cv.put(hx - 2, t + 11, sk[1])
    # brow, eye, nose, moustache, mouth
    cv.hline(hx + 3, hx + 6, t + 9, BROW)
    cv.put(hx + 5, t + 11, EYE); cv.put(hx + 5, t + 10, EYE); cv.put(hx + 4, t + 10, SCLERA); cv.put(hx + 4, t + 11, IRIS)
    cv.put(hx + 4, t + 12, sk[1])
    cv.put(hx + 7, t + 14, sk[1])
    cv.hline(hx + 5, hx + 7, t + 15, bd[2])
    if pose == "grin":
        cv.puts([(hx + 4, t + 16), (hx + 7, t + 16)], MOUTH); cv.hline(hx + 5, hx + 6, t + 16, TEETH)
        cv.put(hx + 3, t + 15, MOUTH)
    else:
        cv.hline(hx + 4, hx + 7, t + 16, MOUTH); cv.put(hx + 6, t + 16, TEETH)
    for x in range(int(round(hx + 1)), int(round(hx + 7))):     # forehead shadow
        for y in range(t + 4, t + 10):
            if cv.own[y, x] == cv.names["face"] and cv.own[y - 1, x] == cv.names["hair"]:
                cv.put(x, y, sk[1])
                break


def b_side_body(cv, c, t, grip, raise_arm=False, lean=0.0, feet=None):
    """Rider in profile facing right.  grip = where the far hand (and, unless raise_arm, the near
    hand) holds the bar.  feet = ((x_back, sole), (x_front, sole))."""
    te, vs, tr = RAMP["tee"], RAMP["vest"], RAMP["trim"]
    (bx, bs), (fx, fs) = feet
    L = lean
    hipB, hipF = (c - 1 + L, t + 50), (c + 1 + L, t + 50)
    # far arm to the grip (behind everything of his)
    b_arm(cv, "armB", (c + 1 + L * 0.3, t + 25), (c + 4 + L * 0.5, t + 36), (grip[0] - 2.2, grip[1] - 0.6), far=True, watch=True)
    b_hand(cv, grip[0], grip[1], "handB")
    # far leg + shoe, near leg + shoe
    leg_side(cv, "legB", hipB, (c - 3 + L * 0.6, t + 61), (bx + 0.5, bs - 5), far=True)
    shoe_side(cv, "shoeB", bx, bs, far=True)
    leg_side(cv, "legF", hipF, (c + 3.5 + L * 0.6, t + 61), (fx - 0.5, fs - 5))
    shoe_side(cv, "shoeF", fx, fs)
    pr = RAMP["pants"]
    cv.hline(fx - 4, fx + 1, fs - 5, pr[3])
    # torso: chest forward, a little forward lean onto the bar
    shirt = cv.poly([(c - 5 + L, t + 21), (c + 4 + L, t + 21), (c + 8 + L, t + 27), (c + 8 + L, t + 37), (c + 6 + L, t + 50),
                     (c - 6 + L, t + 50), (c - 7 + L, t + 36), (c - 6 + L, t + 26)])
    cv.part("shirt", shirt, "tee", rad=5, soft=1.2, cuts=(0.24, 0.50, 0.84))
    vest = cv.poly([(c - 5 + L, t + 21), (c + 4 + L, t + 20.5), (c + 8.5 + L, t + 26), (c + 9.5 + L, t + 37), (c + 8.5 + L, t + 49),
                    (c - 7.5 + L, t + 49), (c - 8 + L, t + 36), (c - 7 + L, t + 27)])
    cv.part("vest", vest, "vest", rad=7, soft=1.6, cuts=(0.26, 0.50, 0.84), tex=0.12, seed=17)
    hem = vest & cv.half(y=t + 48)
    cv.part("hem", hem, "trim", noedge=("vest",), lv=np.where(hem, 2, 0) + np.where(hem & (cv.X > c + L), 1, 0))
    cv.line(c + L, t + 29, c + 1 + L, t + 46, vs[1])                     # side seam
    colm = cv.poly([(c - 3 + L, t + 18), (c + 4 + L, t + 17.5), (c + 6 + L, t + 23), (c - 2 + L, t + 24)])
    cv.part("collar", colm, "vest", rad=2, soft=0.6, bias=0.12, tex=0.08, seed=4)
    top_edge(cv, "collar", tr[2])
    cv.vline(c + 9 + L, t + 26, t + 34, RAMP["metal"][1])                 # zip at the front edge
    # near arm
    if raise_arm:
        b_arm(cv, "armF", (c + 1 + L, t + 24), (c + 10 + L, t + 20), (c + 17 + L, t + 11), push=0.35)
        clicker(cv, c + 19 + L, t + 7, c + 22 + L, t + 1)
        b_hand(cv, c + 18.5 + L, t + 8.5, "handF", rx=2.6, ry=2.6)
        b_hand(cv, grip[0], grip[1], "handB2")                       # far hand on the bar, past his hip
    else:
        b_arm(cv, "armF", (c + 0 + L, t + 25), (c + 4 + L, t + 36), (grip[0] - 2.4, grip[1] - 0.4))
        b_hand(cv, grip[0] - 0.4, grip[1] + 0.3, "handF")
    nk = cv.rect(c - 3 + L, t + 15, c + 3 + L, t + 22)
    cv.part("mock", nk, "tee", rad=3, soft=0.8, cuts=(0.2, 0.5, 0.85))
    head_side(cv, c + 1 + L, t, pose="grin")


def b_side():
    cv = Cv(BW, BH)
    c, t = 42, BT
    g = BH - 1
    P, grip, lamp = scooter_side(cv, c - 19, g)
    sole = t + 77
    b_side_body(cv, c, t, grip, feet=((c - 4, sole), (c + 7, sole)), lean=1.0)
    cv.outline()
    lx, ly = lamp
    for k in range(2, 7):
        cv.put(lx + 2 + k, ly + (k // 3) * (1 if k % 2 else -1) * 0, LIGHT if k < 4 else LIGHT2)
    cv.put(lx + 4, ly - 2, LIGHT2); cv.put(lx + 4, ly + 2, LIGHT2)
    underglow(cv, c - 14, c + 14, g, gap=None)
    return cv


# ---- back -----------------------------------------------------------------------
def b_back():
    cv = Cv(BW, BH)
    c, t = 46, BT
    scooter_deck_front(cv, c, t, back=True)
    # rear wheel + fender with the tail light
    wheel = cv.ell(c, t + 79.0, 2.8, 4.6)
    cv.part("wheel", wheel, "tyre", edge="ink", rad=2, soft=0.5, cuts=(0.3, 0.6, 0.95))
    # the bar ends reach past his sides (the stem is hidden by his body)
    for s in (-1, 1):
        bar = cv.capsule(c + s * 9, t + 44, c + s * 16, t + 44, 1.05)
        cv.part("bar%d" % s, bar, "metal", edge="ink", rad=1.2, soft=0.4, bias=0.1)
        g = cv.capsule(c + s * 12, t + 44, c + s * 19, t + 44, 1.6)
        cv.part("grip%d" % s, g, "tyre", edge="ink", rad=1.5, soft=0.4)
    b_legs(cv, c, t, back=True)
    pr = RAMP["pants"]
    for s in (-1, 1):                                               # back pockets
        cv.hline(c + 3 if s > 0 else c - 8, c + 8 if s > 0 else c - 3, t + 51, pr[1])
    fender = cv.ell(c, t + 75.4, 3.6, 2.0) & cv.half(y=t + 76, below=False)
    cv.part("fender", fender, "deck", edge="ink", rad=2, soft=0.5, bias=0.1)
    cv.puts([(c - 1, t + 75), (c, t + 75), (c + 1, t + 75)], TAIL)
    b_torso(cv, c, t, back=True)
    for s, nm in ((-1, "armL"), (1, "armR")):
        b_arm(cv, nm, (c + s * 12, t + 25), (c + s * 16, t + 35), (c + s * 15.5, t + 41.5), watch=(s < 0))
        b_hand(cv, c + s * 14.5, t + 44, "hand%d" % s)
    # back of the head: hair all round, beard edge showing at the jaw
    hr, bd = RAMP["hair"], RAMP["beard"]
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 7.3, t + 12, 1.7, 2.4), "skin", bias=0.05)
    head = cv.ell(c, t + 10.5, 7.6, 7.0) | (cv.rect(c - 5.6, t + 10, c + 5.6, t + 17) & cv.ell(c, t + 11.5, 6.6, 7.2))
    head &= cv.half(y=t + 17.5, below=False)
    head |= cv.poly([(c - 7.4, t + 6), (c - 6, t + 2), (c - 4, t + 0.6), (c - 2.6, t + 1.6), (c - 1.2, t + 0.0), (c + 1.5, t + 0.0),
                     (c + 2.6, t + 1.4), (c + 4.4, t + 0.6), (c + 6.4, t + 2.2), (c + 7.4, t + 6), (c, t + 4)])
    cv.part("head", head, "hair", rad=5, soft=1.0, cuts=(0.10, 0.34, 0.66), light=(-0.6, -0.8, 0.5), tex=0.05, seed=8)
    for (x0, y0, x1, y1, col) in [(c - 5, t + 4, c - 4, t + 9, hr[3]), (c - 1, t + 3, c - 1, t + 8, hr[3]), (c + 3, t + 4, c + 4, t + 8, hr[1]),
                                  (c - 4, t + 11, c - 3, t + 14, hr[1]), (c + 2, t + 11, c + 3, t + 14, hr[1]), (c - 2, t + 2, c + 1, t + 2, hr[4])]:
        cv.line(x0, y0, x1, y1, col)
    for x in range(c - 4, c + 5):                                       # faded nape
        cv.put(x, t + 16, mix(RAMP["skin"][1], hr[1], 0.6 if x % 2 else 0.3))
    nk = cv.rect(c - 4, t + 17, c + 4, t + 22)
    cv.part("mock", nk, "tee", rad=3, soft=0.8, cuts=(0.2, 0.5, 0.85))
    cv.hline(c - 3, c + 3, t + 19, RAMP["tee"][1])
    cv.outline()
    underglow(cv, c - 9, c + 9, BH - 1, gap=(c - 3, c + 3))
    return cv


# ==========================================================================
# ENTRANCE  (cell 12: the intro-card pose, wider canvas)
# ==========================================================================
EW, EH = 132, 104


def entrance():
    """He rips in on a manual -- front wheel up, leaning back -- clicker thrust up at the future,
    laser on, lime underglow streaking and speed lines behind him."""
    cv = Cv(EW, EH)
    g = EH - 1
    ang = 0.26
    x0 = 30
    c = x0 + 14
    ca, sa = math.cos(ang), math.sin(ang)
    deck_top = lambda u: g - (u * sa + 5.6 * ca)
    fb, ff = x0 + 10 * ca - 5.6 * sa, x0 + 21.5 * ca - 5.6 * sa
    sb, sf = int(math.floor(deck_top(10))), int(math.floor(deck_top(21.5)))
    t = (sb + sf) // 2 - 77
    P, grip, lamp = scooter_side(cv, x0, g, ang=ang)
    b_side_body(cv, c, t, grip, raise_arm=True, lean=-1.5,
                feet=((int(round(fb)), sb), (int(round(ff)), sf)))
    cv.outline()
    lx, ly = lamp
    for k in range(2, 9):
        cv.put(lx + 2 + k, ly - k * 0.25, LIGHT if k < 5 else LIGHT2)
    # laser up and out, into the title card
    laser(cv, c + 21.5, t - 1, c + 44, max(2, t - 20), dot=True)
    # speed lines + underglow streak
    for (y, x1, ln, col) in [(t + 30, x0 - 4, 16, RAMP["vest"][3]), (t + 44, x0 - 8, 22, LIME2), (t + 58, x0 - 6, 14, RAMP["vest"][2]),
                             (t + 70, x0 - 10, 20, LIME), (g - 2, x0 - 8, 18, LIME3)]:
        for x in range(max(0, x1 - ln), x1):
            if 0 <= int(y) < EH and not cv.alpha[int(y), x]:
                cv.put(x, y, col)
    for (x, y) in [(x0 - 7, g - 1), (x0 - 9, g - 3), (x0 - 5, g - 4)]:
        cv.put(x, y, RAMP["metal"][1])                                # grit off the rear tyre
    sparkle(cv, c - 14, t + 18)
    sparkle(cv, c + 30, t + 26, big=False)
    sparkle(cv, c - 16, t + 6, big=False)
    return cv


# ==========================================================================
# PITCH DECK  (battle-only prop drawn behind him)
# ==========================================================================
FONT = {
    "V": ["1.1", "1.1", "1.1", "1.1", ".1."], "E": ["111", "1..", "11.", "1..", "111"], "S": ["111", "1..", "111", "..1", "111"],
    "T": ["111", ".1.", ".1.", ".1.", ".1."], "D": ["11.", "1.1", "1.1", "1.1", "11."], "A": [".1.", "1.1", "111", "1.1", "1.1"],
    "M": ["1.1", "111", "111", "1.1", "1.1"], "$": [".1.", "111", "11.", ".11", "111"], "9": ["111", "1.1", "111", "..1", "111"],
    "1": [".1.", "11.", ".1.", ".1.", "111"], "0": ["111", "1.1", "1.1", "1.1", "111"], "X": ["1.1", "1.1", ".1.", "1.1", "1.1"],
    " ": ["...", "...", "...", "...", "..."], "B": ["11.", "1.1", "11.", "1.1", "11."], "R": ["11.", "1.1", "11.", "1.1", "1.1"],
    "Y": ["1.1", "1.1", ".1.", ".1.", ".1."], "!": [".1.", ".1.", ".1.", "...", ".1."],
}


def text(im, x, y, s, col, k=1):
    px = im.load()
    for ch in s:
        g = FONT[ch]
        for j, row in enumerate(g):
            for i, v in enumerate(row):
                if v == "1":
                    for a in range(k):
                        for b in range(k):
                            px[x + i * k + a, y + j * k + b] = col + (255,)
        x += 4 * k


def pitch_deck():
    """A projected slide: VESTED, the hockey stick, 10X, TAM $9T.  Kyle stands in front of its left
    third (anchor = his battle foot point), so the content sits on the right."""
    W, H = 156, 100
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = 8, 2, 155, 70
    # projector spill (a hard-edged halo two tones wide) and the slide itself
    d.rectangle([x0 - 2, y0, x1, y1 + 2], fill=(62, 74, 112, 255))
    d.rectangle([x0 - 1, y0, x1, y1 + 1], fill=(104, 118, 162, 255))
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            e = min(x - x0, x1 - x, y - y0, y1 - y)
            v = 236 if e > 6 else 222 if e > 2 else 206
            im.putpixel((x, y), (v - 8, v - 4, v + 6 if v < 240 else 250, 255))
    navy, orange, grey, green, green2 = (32, 40, 84), (230, 110, 36), (150, 156, 174), (40, 160, 70), (110, 220, 90)
    # title bar
    d.rectangle([x0 + 3, y0 + 3, x1 - 3, y0 + 14], fill=navy + (255,))
    text(im, 74, y0 + 5, "VESTED", orange, 1)
    for k in range(5):
        im.putpixel((100 + k * 3, y0 + 9), orange + (255,))
    # chart axes + gridlines
    ax, ay, aw, ah = 98, 22, 50, 40
    for y in range(ay, ay + ah, 8):
        d.line([ax, y, ax + aw, y], fill=(214, 218, 230, 255))
    d.line([ax, ay, ax, ay + ah], fill=navy + (255,))
    d.line([ax, ay + ah, ax + aw, ay + ah], fill=navy + (255,))
    # the hockey stick: flat, flat, flat ... then straight up
    pts = [(ax + 2, ay + ah - 4), (ax + 14, ay + ah - 5), (ax + 26, ay + ah - 6), (ax + 34, ay + ah - 9), (ax + 40, ay + ah - 17),
           (ax + 44, ay + ah - 30), (ax + 46, ay + 4)]
    for (a, b), (c_, e) in zip(pts, pts[1:]):
        d.line([a, b + 1, c_, e + 1], fill=(20, 100, 40, 255))
        d.line([a, b, c_, e], fill=green + (255,))
        d.line([a - 1, b, c_ - 1, e], fill=green2 + (255,))
    hx, hy = pts[-1]
    for (dx, dy) in ((0, -1), (-1, 0), (1, 0), (-2, 1), (2, 1), (0, -2)):
        im.putpixel((hx + dx, hy + dy), green + (255,))
    text(im, ax + 8, ay + 4, "10X", orange, 2)
    # bullet points on the left half (mostly behind him) + the TAM line
    for k, wdt in enumerate((38, 30, 34)):
        y = 24 + k * 9
        d.rectangle([67, y, 68, y + 1], fill=orange + (255,))
        d.line([71, y, 71 + wdt - 14, y], fill=grey + (255,))
        d.line([71, y + 2, 71 + wdt - 20, y + 2], fill=(190, 194, 208, 255))
    text(im, 67, 55, "TAM $9T", navy, 1)
    return im, (44, H - 1)


# ==========================================================================
# WORLD  (52 px standing, redrawn small -- not scaled)
# ==========================================================================
WW, WH = 56, 56
WORLD_H = 52
WT = WH - WORLD_H

# front head, col 0 = c-8, row 0 = t (top of the quiff).  Rows 8-13 swap per expression.
W_HEAD = [
    "....KK.KKK.K....",
    "...K44K3443K....",
    "..K3333334332K..",
    "..K2233333322K..",
    "..K1222222221K..",
    "..K11dddddd11K..",
    "..K1dsllllsd1K..",
    ".KK1BBsllsBB1KK.",
    "KdKsWEllllEWsKdK",
    "KdKsIEsllsIEsKdK",
    ".KKbsssldsssbKK.",
    "..KbbsnnnnsbbK..",
    "..KbbMTTTTMbbK..",
    "...KbbMMMMbbK...",
    "....KKbbbbKK....",
]
W_FACE = {
    "idle": {},
    "talk": {12: "..KbMTTTTTTMbK..", 13: "...KbMooooMbK..."},
    "tell": {8: "KdKsWEllllssdKdK", 9: "KdKsIEsllEEEsKdK", 12: "..KbbMTTTTTMbK..", 13: "...KbbbMMMMbK..."},
    "hit": {7: ".KKBBsllllsBBKK.", 8: "KdKsEsllllsEsKdK", 9: "KdKssEllllEssKdK", 12: "..KbMTtTtTtMbK..", 13: "...KbMMMMMMbK..."},
    "blink": {8: "KdKssslllssssKdK", 9: "KdKsEEsllsEEsKdK"},
    "down": {8: "KdKsdsllllsdsKdK", 9: "KdKsEEsllsEEsKdK"},
    "glance": {8: "KdKsWEllllWEsKdK", 9: "KdKsWIsllsWIsKdK"},
}

# profile head facing right, col 0 = c-8, row 0 = t
W_SIDE = [
    "......KKK.K.....",
    ".....K443K4K....",
    "....K33344334K..",
    "...K2223333333K.",
    "..K122222222KK..",
    ".K112222221dsK..",
    ".K11122221dsllK.",
    ".K1111221dslBBK.",
    ".K111KK1dslWEK..",
    ".K11KsdK1sslllK.",
    ".K11KdsK1sssslK.",
    ".K1bKKKbbssssK..",
    "..KbbbbbbbbbnK..",
    "..KbbbbbbbMTMK..",
    "...KbbbbbbbbK...",
    "....KKbbbbKK....",
]

W_BACK = [
    "....KK.KKK.K....",
    "...K44K3443K....",
    "..K3333334332K..",
    "..K2333333322K..",
    "..K2233333222K..",
    "..K2222222221K..",
    "..K1222222211K..",
    ".KK1222222111KK.",
    "KdK1122221111KdK",
    "KdK1111111111KdK",
    ".KKb11111111bKK.",
    "..Kbb111111bbK..",
    "...Kbb1111bbK...",
    "....KKddddKK....",
]


def w_head(cv, c, t, face="idle", dx=0, kind="front"):
    if kind == "front":
        rows = list(W_HEAD)
        for k, r in W_FACE.get(face, {}).items():
            rows[k] = r
    elif kind == "side":
        rows = W_SIDE
    else:
        rows = W_BACK
    paint_map(cv, c - 8 + dx, t, rows, head_pal(), name="head")


def w_arm(cv, name, S, E, W, push=0.4, watch=False, far=False):
    (sx, sy), (ex, ey), (wx, wy) = S, E, W
    kx, ky = ex + (wx - ex) * push, ey + (wy - ey) * push
    fore = cv.capsule(kx, ky, wx, wy, 1.5)
    cv.part(name + "fore", fore, "skin", edge="dark", lv=np.where(fore, 2, 0) + np.where(fore & (cv.X < kx), 1, 0))
    sl = cv.capsule(sx, sy, ex, ey, 2.1, 1.8) | cv.capsule(ex, ey, kx, ky, 1.8, 2.0)
    cv.part(name, sl, "tee", edge="dark", rad=2, soft=0.7, cuts=(0.45, 0.72, 0.95) if far else (0.28, 0.52, 0.88))
    if watch:
        cv.put(wx - (wx - kx) * 0.25, wy - (wy - ky) * 0.25, LIME)
    return sl


def w_hand(cv, x, y, name, r=1.8):
    m = cv.ell(x, y, r, r)
    cv.part(name, m, "skin", edge="ink", lv=np.where(m, 3, 0) - np.where(m & (cv.X > x) & (cv.Y > y - 1), 1, 0))
    return m


def w_legs(cv, c, t, back=False):
    pr, sr = RAMP["pants"], RAMP["shoe"]
    for s in (-1, 1):
        leg = cv.poly([(c + s * 0.5, t + 31), (c + s * 7, t + 31), (c + s * 6.5, t + 40), (c + s * 6, t + 47.5),
                       (c + s * 1.8, t + 47.5), (c + s * 1.4, t + 40), (c + s * 0.5, t + 35)])
        cv.part("leg%d" % s, leg, "pants", rad=3, soft=0.8, cuts=(0.30, 0.56, 0.9))
        cv.vline(c + s * 4, t + 38, t + 45, pr[1] if s < 0 else pr[0])
        cv.hline(c + s * 2 if s > 0 else c - 6, c + 6 if s > 0 else c - 2, t + 47, pr[3] if s < 0 else pr[2])
    for s in (-1, 1):
        sh = cv.ell(c + s * 4.2, t + 50.0, 3.9, 2.4) & cv.half(y=t + 51, below=False) & cv.half(y=t + 47.8)
        cv.part("shoe%d" % s, sh, "shoe", rad=2, soft=0.5, cuts=(0.3, 0.55, 0.85))
        for x in range(c - 8, c + 9):
            if cv.own[t + 50, x] == cv.names["shoe%d" % s] and cv.get(x, t + 50) != sr[0]:
                cv.put(x, t + 50, sr[1])
        cv.put(c + s * 7, t + 49, RAMP["vest"][2])


def w_torso(cv, c, t, back=False):
    te, vs, tr = RAMP["tee"], RAMP["vest"], RAMP["trim"]
    mock = cv.rect(c - 3, t + 12, c + 2, t + 16)
    cv.part("mock", mock, "tee", edge=None, lv=np.where(mock, 2, 0) - np.where(mock & (cv.Y == t + 14), 1, 0))
    shirt = cv.poly([(c - 7, t + 15), (c + 7, t + 15), (c + 9, t + 18), (c + 8, t + 24), (c + 7, t + 32), (c - 7, t + 32),
                     (c - 8, t + 24), (c - 9, t + 18)])
    cv.part("shirt", shirt, "tee", rad=4, soft=1.0, cuts=(0.24, 0.50, 0.84))
    vest = cv.poly([(c - 5, t + 15), (c + 5, t + 15), (c + 6.5, t + 18), (c + 6, t + 21), (c + 7, t + 24), (c + 7.5, t + 32),
                    (c - 7.5, t + 32), (c - 7, t + 24), (c - 6, t + 21), (c - 6.5, t + 18)])
    cv.part("vest", vest, "vest", rad=5, soft=1.2, cuts=(0.26, 0.50, 0.84), tex=0.08, seed=55)
    binding(cv, "vest", ("shirt",), tr[2])
    hem = vest & cv.half(y=t + 31)
    cv.part("hem", hem, "trim", noedge=("vest",), lv=np.where(hem, 2, 0) + np.where(hem & (cv.X < c - 2), 1, 0))
    if back:
        top_edge(cv, "vest", tr[2])
        return
    cv.puts([(c - 3, t + 15), (c + 3, t + 15), (c - 2, t + 15), (c + 2, t + 15)], tr[2])
    cv.puts([(c - 1, t + 15), (c, t + 15), (c + 1, t + 15)], te[2])
    for y in range(t + 16, t + 31):
        cv.put(c, y, tr[1] if y % 2 else RAMP["metal"][2])
    cv.hline(c + 2, c + 4, t + 19, tr[2]); cv.hline(c + 2, c + 4, t + 20, tr[2]); cv.put(c + 4, t + 19, RAMP["metal"][3])
    cv.puts([(c - 5, t + 19), (c - 4, t + 18)], vs[3])


def w_scooter(cv, c, g, flip=False):
    """The parked scooter in profile just behind his right side (nose to the viewer's right; flip
    mirrors it for the back view), on its kickstand."""
    sgn = -1 if flip else 1
    X = lambda u: c + sgn * u
    dk = RAMP["deck"]
    R = 3.0
    deck = cv.rect(min(X(4), X(21)), g - 5, max(X(4), X(21)), g - 3)
    cv.part("deck", deck, "deck", edge="ink", lv=np.where(deck, 2, 0) + np.where(deck & (cv.Y == g - 5), 1, 0))
    for u in range(5, 21):
        cv.put(X(u), g - 4, LIME2 if u % 5 else LIME)
    neck = cv.poly([(X(20), g - 5), (X(22), g - 5), (X(24.5), g - 8), (X(22.5), g - 8)])
    cv.part("neck", neck, "deck", edge="ink", lv=np.where(neck, 2, 0))
    for name, u in (("wheelR", 3.0), ("wheelF", 24.5)):
        m = cv.ell(X(u), g - R + 0.5, R - 0.1, R - 0.1)
        cv.part(name, m, "tyre", edge="ink", lv=np.where(m, 2, 0) + np.where(m & (cv.Y < g - R), 1, 0))
        cv.put(X(u), g - R + 0.5, RAMP["metal"][3])
    fen = cv.poly([(X(-0.6), g - 3), (X(0), g - 6), (X(3), g - 7), (X(6.5), g - 5.5), (X(6.5), g - 4.5), (X(3), g - 5.6), (X(0.8), g - 4.2)])
    cv.part("fender", fen, "deck", edge="ink", lv=np.where(fen, 2, 0))
    cv.put(X(0), g - 4, TAIL)
    stem = cv.capsule(X(23.6), g - 8, X(21.4), g - 24, 1.3)
    cv.part("stem", stem, "deck", edge="ink", lv=np.where(stem, 2, 0) + np.where(stem & ((cv.X - X(22.5)) * sgn < 0), 1, 0))
    fork = cv.capsule(X(24.5), g - 2.5, X(23.6), g - 8, 0.7)
    cv.part("fork", fork, "metal", edge="ink", lv=np.where(fork, 2, 0))
    for y in range(g - 17, g - 12):
        cv.put(X(22.6 - (g - 8 - y) * 2.2 / 16), y, LIME2)
    lamp = cv.ell(X(23.6), g - 19, 1.2, 1.4)
    cv.part("lamp", lamp, "metal", edge="ink", lv=np.where(lamp, 4, 0))
    grip = cv.ell(X(21.0), g - 24.5, 1.6, 1.6)
    cv.part("grip", grip, "tyre", edge="ink", lv=np.where(grip, 2, 0))
    pod = cv.rect(min(X(22), X(24)), g - 27, max(X(22), X(24)), g - 26)
    cv.part("pod", pod, "deck", edge="ink", lv=np.where(pod, 2, 0))
    cv.put(X(23), g - 26, LIME)
    cv.line(X(9), g - 3, X(7), g, dk[1])                             # kickstand
    return (X(21.0), g - 24.5), (X(23.6), g - 19)


def w_front(pose, face=None):
    cv = Cv(WW, WH)
    c, t = 28, WT
    g = WH - 1
    grip, lamp = w_scooter(cv, c, g)
    w_legs(cv, c, t)
    w_torso(cv, c, t)
    # viewer-right arm hangs easy, smartwatch on the wrist (flung up when he flinches)
    if pose == "hit":
        w_arm(cv, "armR", (c + 8, t + 17), (c + 12, t + 20), (c + 14, t + 15), watch=True)
        w_hand(cv, c + 14, t + 13.5, "handR")
    else:
        w_arm(cv, "armR", (c + 8, t + 17), (c + 9.5, t + 24), (c + 10, t + 30), watch=True)
        w_hand(cv, c + 10, t + 31.5, "handR")
    if pose in ("idle", "blink"):
        w_arm(cv, "armL", (c - 8, t + 17), (c - 9.5, t + 24), (c - 10, t + 30))
        cv.part("clk", cv.rect(c - 11, t + 31, c - 9, t + 34), "phone", edge="ink", lv=np.where(cv.rect(c - 11, t + 31, c - 9, t + 34), 2, 0))
        w_hand(cv, c - 10, t + 31.5, "handL")
        cv.put(c - 10, t + 34, LASER)
    elif pose == "talk":
        w_arm(cv, "armL", (c - 8, t + 17), (c - 12.5, t + 22), (c - 13, t + 18))
        w_hand(cv, c - 13, t + 16.5, "handL")
        f = cv.capsule(c - 13, t + 15, c - 13, t + 12, 0.7)
        cv.part("finger", f, "skin", edge="ink", noedge=("handL",), lv=np.where(f, 3, 0))
    elif pose == "tell":
        w_arm(cv, "armL", (c - 8, t + 17), (c - 13, t + 19), (c - 15, t + 14))
        clicker(cv, c - 15.5, t + 12, c - 17.5, t + 8.5)
        w_hand(cv, c - 15, t + 12.5, "handL")
    elif pose == "hit":
        w_arm(cv, "armL", (c - 8, t + 17), (c - 12, t + 20), (c - 14, t + 15))
        w_hand(cv, c - 14, t + 13.5, "handL")
        clicker(cv, c - 20, t + 4, c - 22, t + 2, name="flyclick")
    elif pose == "phone":
        w_arm(cv, "armL", (c - 8, t + 17), (c - 9, t + 25), (c - 4, t + 24))
        ph = cv.rect(c - 5, t + 19, c - 2, t + 24)
        cv.part("phone", ph, "phone", edge="ink", lv=np.where(ph, 2, 0))
        cv.puts([(c - 4, t + 20), (c - 3, t + 20), (c - 4, t + 21), (c - 3, t + 22)], LIME2)
        cv.put(c - 3, t + 21, LIME)
        w_hand(cv, c - 4, t + 24, "handL")
    elif pose == "latte":
        w_arm(cv, "armL", (c - 8, t + 17), (c - 9.5, t + 24), (c - 5, t + 20))
        cup = cv.poly([(c - 7, t + 14), (c - 2, t + 14), (c - 2.6, t + 21), (c - 6.4, t + 21)])
        cv.part("cup", cup, "cup", edge="ink", lv=np.where(cup, 3, 0))
        lt = cup & cv.half(y=t + 16)
        cv.fill(lt & ~shifted(~lt, 0, 0, True), RAMP["latte"][2])
        cv.puts([(c - 5, t + 17), (c - 4, t + 19)], RAMP["latte"][4])     # ice
        cv.puts([(c - 6, t + 15), (c - 6, t + 16)], RAMP["cup"][4])
        cv.line(c - 3, t + 13, c - 2, t + 11, LIME2)                         # straw up to the grin
        w_hand(cv, c - 5.5, t + 19.5, "handL")
    fc = face or {"idle": "idle", "talk": "talk", "tell": "tell", "hit": "hit", "blink": "blink",
                  "phone": "down", "latte": "glance"}[pose]
    w_head(cv, c + (1 if pose == "hit" else 0), t, fc)
    cv.outline()
    underglow(cv, c + 6, c + 22, g, gap=(c - 9, c + 9))
    if pose == "tell":
        laser(cv, c - 18, t + 7, c - 25, t + 1, dot=True)
    if pose == "hit":
        cv.puts([(c - 9, t + 1), (c - 10, t + 2), (c - 9, t + 2), (c - 9, t + 3)], SWEAT)
        cv.puts([(c - 23, t + 6), (c - 18, t + 1)], SPARK2)
    return cv


def w_side():
    cv = Cv(WW, WH)
    c, t = 28, WT
    g = WH - 1
    w_scooter(cv, c, g)
    pr = RAMP["pants"]
    w_arm(cv, "armB", (c + 1, t + 17), (c + 2, t + 24), (c + 3, t + 30), far=True)
    legB = cv.poly([(c - 4, t + 31), (c + 2, t + 31), (c + 1, t + 39), (c - 1, t + 47.5), (c - 4.5, t + 47.5), (c - 3, t + 39)])
    cv.part("legB", legB, "pants", rad=2, cuts=(0.45, 0.7, 0.95))
    cv.part("shoeB", cv.ell(c - 1.5, t + 50.0, 4.4, 2.4) & cv.half(y=t + 51, below=False) & cv.half(y=t + 47.8), "shoe", rad=2, cuts=(0.45, 0.7, 0.95))
    legF = cv.poly([(c - 3, t + 31), (c + 4, t + 31), (c + 4, t + 38), (c + 3.5, t + 47.5), (c - 0.5, t + 47.5), (c - 1.5, t + 42), (c - 3, t + 37)])
    cv.part("legF", legF, "pants", rad=3, soft=0.8, cuts=(0.30, 0.56, 0.9))
    cv.vline(c + 1, t + 38, t + 45, pr[1])
    cv.hline(c - 1, c + 3, t + 47, pr[3])
    cv.part("shoeF", cv.ell(c + 3, t + 50.0, 4.6, 2.4) & cv.half(y=t + 51, below=False) & cv.half(y=t + 47.8), "shoe", rad=2, soft=0.5, cuts=(0.3, 0.55, 0.85))
    for x in range(c - 6, c + 9):
        for nm in ("shoeF", "shoeB"):
            if cv.own[t + 50, x] == cv.names[nm] and cv.get(x, t + 50) != RAMP["shoe"][0]:
                cv.put(x, t + 50, RAMP["shoe"][1])
    cv.put(c - 1, t + 49, RAMP["vest"][2])
    shirt = cv.poly([(c - 4, t + 15), (c + 3, t + 15), (c + 5, t + 18), (c + 5, t + 25), (c + 4, t + 32), (c - 4, t + 32), (c - 5, t + 24), (c - 5, t + 17)])
    cv.part("shirt", shirt, "tee", rad=3, soft=1.0)
    vest = cv.poly([(c - 4, t + 15), (c + 3, t + 14.5), (c + 5.5, t + 18), (c + 6, t + 24), (c + 5.5, t + 32), (c - 5, t + 32), (c - 5.5, t + 24), (c - 5, t + 18)])
    cv.part("vest", vest, "vest", rad=4, soft=1.2, cuts=(0.26, 0.50, 0.84), tex=0.08, seed=57)
    hem = vest & cv.half(y=t + 31)
    cv.part("hem", hem, "trim", noedge=("vest",), lv=np.where(hem, 2, 0) + np.where(hem & (cv.X > c), 1, 0))
    cv.vline(c + 5, t + 17, t + 22, RAMP["metal"][1])
    cv.puts([(c + 3, t + 14), (c + 4, t + 14), (c + 2, t + 14)], RAMP["trim"][2])
    w_arm(cv, "arm", (c - 0.5, t + 17), (c, t + 24), (c + 1.5, t + 30))
    cv.part("clk", cv.rect(c + 1, t + 31, c + 4, t + 32), "phone", edge="ink", lv=np.where(cv.rect(c + 1, t + 31, c + 4, t + 32), 2, 0))
    w_hand(cv, c + 1.5, t + 31.5, "hand")
    nk = cv.rect(c - 3, t + 12, c + 1, t + 16)
    cv.part("mock", nk, "tee", edge=None, lv=np.where(nk, 2, 0) - np.where(nk & (cv.Y == t + 14), 1, 0))
    w_head(cv, c, t, kind="side")
    cv.outline()
    underglow(cv, c + 6, c + 22, g, gap=(c - 7, c + 8))
    return cv


def w_back():
    cv = Cv(WW, WH)
    c, t = 28, WT
    g = WH - 1
    grip, lamp = w_scooter(cv, c, g, flip=True)
    w_legs(cv, c, t, back=True)
    w_torso(cv, c, t, back=True)
    w_arm(cv, "armL", (c - 8, t + 17), (c - 9.5, t + 24), (c - 10, t + 30), watch=True)
    w_hand(cv, c - 10, t + 31.5, "handL")
    w_arm(cv, "armR", (c + 8, t + 17), (c + 9.5, t + 24), (c + 10, t + 30))
    w_hand(cv, c + 10, t + 31.5, "handR")
    nk = cv.rect(c - 3, t + 12, c + 2, t + 16)
    cv.part("mock", nk, "tee", edge=None, lv=np.where(nk, 2, 0) - np.where(nk & (cv.Y == t + 14), 1, 0))
    w_head(cv, c, t, kind="back")
    cv.outline()
    underglow(cv, c - 22, c - 6, g, gap=(c - 9, c + 9))
    return cv


# ==========================================================================
# PORTRAITS  (64 x 64, head and shoulders)
# ==========================================================================
PW = PH = 64


def p_eye(cv, ex, ey, expr, side):
    """7-wide pixel-map eye; (ex, ey) is the top-left of the viewer-left eye, the right is mirrored."""
    sk = RAMP["skin"]
    maps = {
        "neutral": [".KKKKK.",
                    "KWHIIWK",
                    ".WIPIW.",
                    "..SSS.."],
        "warm":    ["..KKK..",
                    ".KKKKK.",
                    "KK...KK",
                    ".......",
                    ".SSSSS."],
        "concern": ["..KKKK.",
                    ".KHIIWK",
                    ".WIPIW.",
                    "..SSS.."],
        "surprised": ["..KKK..",
                      ".KWWWK.",
                      "KWHIIWK",
                      "KWIPIWK",
                      ".KWWWK.",
                      "..SSS.."],
        "blink":   [".......",
                    ".......",
                    "KKKKKKK",
                    ".SSSSS."],
    }
    pal = {"K": EYE, "I": IRIS, "P": EYE, "H": WHITE, "W": SCLERA, "S": sk[1]}
    rows = maps[expr]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x = ex + i if side < 0 else ex + (6 - i)
            cv.put(x, ey + j, pal[ch])
    for j, row in enumerate(rows):                 # catch-light stays upper-left in both eyes
        if "H" in row and side > 0:
            i = row.index("H")
            cv.put(ex + (6 - i), ey + j, IRIS)
            cv.put(ex + (6 - i) - 2, ey + j, WHITE)
            break


def p_mouth(cv, c, my, expr, talk=False):
    sk = RAMP["skin"]
    if expr == "neutral":
        # confident closed grin with a sliver of teeth
        cv.hline(c - 5, c + 5, my, MOUTH)
        cv.put(c - 6, my - 1, MOUTH); cv.put(c + 6, my - 1, MOUTH)
        cv.hline(c - 4, c + 4, my, TEETH); cv.put(c + 3, my, TEETH2)
        if talk:
            cv.hline(c - 4, c + 4, my + 1, MOUTH); cv.hline(c - 2, c + 2, my + 1, TONGUE)
            cv.hline(c - 3, c + 3, my + 2, MOUTH)
            cv.hline(c - 2, c + 2, my + 3, LIP)
        else:
            cv.hline(c - 4, c + 4, my + 1, MOUTH)
            cv.hline(c - 2, c + 2, my + 2, LIP)
    elif expr == "warm":
        drop = 2 if talk else 0
        cv.hline(c - 7, c + 7, my - 1, MOUTH)
        cv.put(c - 8, my - 2, MOUTH); cv.put(c + 8, my - 2, MOUTH)
        cv.hline(c - 6, c + 6, my, TEETH)
        for x in (c - 3, c, c + 3):
            cv.put(x, my, TEETH2)
        cv.put(c - 7, my, MOUTH); cv.put(c + 7, my, MOUTH)
        for k in range(1, 3 + drop):
            cv.hline(c - 6 + (k > 1), c + 6 - (k > 1), my + k, MOUTH)
        cv.hline(c - 3, c + 3, my + 2 + drop, TONGUE)
        cv.hline(c - 4, c + 4, my + 3 + drop, MOUTH)
        cv.hline(c - 3, c + 3, my + 4 + drop, LIP)
    elif expr == "concern":
        # the pitch smile, holding on through gritted teeth
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
    sk, hr, vs, te, tr, bd = RAMP["skin"], RAMP["hair"], RAMP["vest"], RAMP["tee"], RAMP["trim"], RAMP["beard"]
    # ---- shoulders: tee at the edges, the pile vest over it, mock neck, navy-bound stand collar ----
    shirt = cv.ell(c, 80, 33, 26) & cv.half(y=48)
    cv.part("shirt", shirt, "tee", rad=10, soft=1.6, cuts=(0.24, 0.50, 0.84))
    vest = cv.ell(c, 80, 27, 26) & cv.half(y=49)
    cv.part("vest", vest, "vest", rad=12, soft=2.0, cuts=(0.26, 0.50, 0.84), tex=0.14, seed=41)
    binding(cv, "vest", ("shirt",), tr[2])
    mock = cv.rect(c - 8, 40, c + 8, 58)
    cv.part("mock", mock, "tee", rad=6, soft=1.2, cuts=(0.22, 0.5, 0.85))
    for x in range(c - 7, c + 8):
        cv.put(x, 50, te[1]); cv.put(x, 51, te[3] if x < c else te[2])     # the roll of the mock neck
    colm = cv.poly([(c - 14, 50), (c - 9, 46), (c - 1, 54), (c - 1, 64), (c - 6, 64), (c - 15, 56)]) | \
        cv.poly([(c + 14, 50), (c + 9, 46), (c + 1, 54), (c + 1, 64), (c + 6, 64), (c + 15, 56)])
    cv.part("collar", colm, "vest", rad=4, soft=1.0, bias=0.10, tex=0.12, seed=43)
    top_edge(cv, "collar", tr[2], rows=2)
    for y in range(55, 64):
        cv.put(c, y, tr[1] if y % 2 else RAMP["metal"][2])
    cv.puts([(c - 1, 55), (c + 1, 55)], tr[2])
    pk = cv.rect(c + 13, 56, c + 21, 64)
    cv.part("pocket", pk, "trim", edge="dark", noedge=("vest",), lv=np.where(pk, 2, 0) + np.where(pk & (cv.X < c + 15), 1, 0))
    cv.hline(c + 13, c + 21, 57, tr[3]); cv.put(c + 20, 58, RAMP["metal"][3]); cv.put(c + 20, 59, RAMP["metal"][2])
    for x in range(c - 22, c - 15):
        y = 56 + (c - 18 - x) // 3
        if cv.own[y, x] == cv.names["vest"]:
            cv.put(x, y, vs[3])
    # ---- ears ----
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 13.6, 30, 2.6, 4.4), "skin", rad=3, bias=0.04)
        cv.puts([(c + s * 13, 29), (c + s * 13, 30), (c + s * 13, 31)], sk[1])
    # ---- face ----
    face = cv.ell(c, 27.5, 12.6, 14.0) | cv.poly([(c - 12.2, 29), (c + 12.2, 29), (c + 10.5, 39), (c + 5.5, 45),
                                                   (c - 5.5, 45), (c - 10.5, 39)])
    cv.part("face", face, "skin", rad=11, soft=2.6, cuts=(0.18, 0.46, 0.86), bias=0.04, light=(-0.45, -0.55, 0.75))
    fid = cv.names["face"]
    # beard: sideburns down the jaw, full chin, moustache; cheeks stay clear
    dx = np.abs(cv.X - c)
    beard = face & (((dx >= 10.2) & (cv.Y >= 26)) | (cv.Y >= 41) | ((cv.Y >= 36) & (dx >= 7.0)) | ((cv.Y >= 33) & (dx >= 9.0)))
    lvb = np.where(beard, 2, 0) + np.where(beard & (cv.X < c - 2) & (cv.Y < 42), 1, 0) - np.where(beard & (cv.Y >= 43), 1, 0)
    lvb -= np.where(beard & (cv.X > c + 8), 1, 0)
    cv.part("beard", beard, "beard", edge=None, lv=np.clip(lvb, 1, 3) * beard, tex=0.14, seed=45)
    bid = cv.names["beard"]
    for y in range(24, 46):                                    # stubble fringe against the cheek
        for x in range(c - 12, c + 13):
            if cv.own[y, x] == fid and ((x + y) % 2 == 0):
                if cv.own[y, x - 1] == bid or cv.own[y, x + 1] == bid or cv.own[y + 1, x] == bid:
                    cv.put(x, y, mix(cv.get(x, y), bd[2], 0.45))
    # moustache
    for x in range(c - 6, c + 7):
        cv.put(x, 36, bd[2] if abs(x - c) > 1 else bd[1]); cv.put(x, 37, bd[1] if abs(x - c) < 6 else bd[2])
    cv.puts([(c - 5, 36), (c - 4, 36), (c - 3, 36)], bd[3])
    # ---- hair: faded sides + the tall textured quiff ----
    lift = -2 if expr == "surprised" else 0
    L = lift
    skull = cv.ell(c, 19 + L, 13.8, 10.5) & cv.half(y=17 + L, below=False)
    for s in (-1, 1):
        skull |= cv.capsule(c + s * 12.4, 14 + L, c + s * 12.6, 26, 1.7)
    cv.part("hairside", skull, "hair", lv=np.where(skull, 1, 0) + np.where(skull & (cv.X < c - 6) & (cv.Y < 22), 1, 0), edge=None)
    quiff = cv.poly([(c - 13.5, 18 + L), (c - 13.8, 10 + L), (c - 11, 5 + L), (c - 7.5, 2.2 + L), (c - 5, 4 + L),
                     (c - 2, 1 + L), (c + 2.5, 0.4 + L), (c + 5, 2.6 + L), (c + 8.5, 1.4 + L), (c + 11.5, 4 + L),
                     (c + 14, 8.5 + L), (c + 14, 17 + L), (c + 11, 13.5 + L), (c + 7, 12.8 + L), (c + 3, 13.6 + L),
                     (c - 1, 12.8 + L), (c - 5, 14.2 + L), (c - 9, 15.6 + L)])
    cv.part("quiff", quiff, "hair", rad=6, soft=1.6, cuts=(0.18, 0.44, 0.78), light=(-0.6, -0.8, 0.5), tex=0.05, seed=47, noedge=("hairside",))
    for (pts_, col) in [([(c - 10, 7), (c - 7, 4)], hr[4]), ([(c - 3, 4), (c + 1, 2)], hr[4]), ([(c + 5, 5), (c + 8, 3)], hr[3]),
                        ([(c - 9, 12), (c - 6, 7), (c - 5, 5)], hr[1]), ([(c - 2, 11), (c - 1, 7), (c - 3, 4)], hr[0]),
                        ([(c + 3, 11), (c + 4, 7), (c + 3, 4)], hr[1]), ([(c + 9, 11), (c + 10, 7), (c + 9, 4)], hr[0]),
                        ([(c - 8, 9), (c - 6, 6)], hr[3]), ([(c + 6, 9), (c + 7, 6)], hr[3]), ([(c - 12, 14), (c - 11, 9)], hr[3])]:
        for (a, b), (d_, e) in zip(pts_, pts_[1:]):
            cv.line(a, b + L, d_, e + L, col)
    # forehead shadow under the hairline
    for x in range(c - 12, c + 13):
        for y in range(8, 26):
            if cv.own[y, x] == fid:
                cv.put(x, y, sk[1])
                if cv.own[y + 1, x] == fid:
                    cv.put(x, y + 1, mix(sk[1], sk[2], 0.5))
                break
    # ---- brows: thick, black, very expressive ----
    by = {"neutral": 21, "warm": 20, "concern": 20, "surprised": 18}[expr]
    for s in (-1, 1):
        for k in range(7):
            x = c + s * (3 + k)
            if expr == "concern":
                dy = -1 if k < 3 else 0 if k < 5 else 1
            elif expr == "surprised":
                dy = -1 if 1 < k < 6 else 0
            elif expr == "neutral" and s < 0:
                dy = (-1 if 1 < k < 6 else 0) - (1 if k in (3, 4) else 0)    # the hiked "hear me out" brow
            else:
                dy = -1 if 1 < k < 6 else 0
            cv.put(x, by + dy, BROW)
            cv.put(x, by + dy + 1, BROW if 0 < k < 6 else mix(BROW, sk[1], 0.5))
    ey = {"neutral": 24, "warm": 24, "concern": 24, "surprised": 23}[expr]
    for s in (-1, 1):
        p_eye(cv, c - 11 if s < 0 else c + 4, ey, "blink" if blink else expr, s)
    # ---- nose: broad, soft ----
    cv.puts([(c - 1, 28), (c - 1, 29), (c - 1, 30), (c - 1, 31)], sk[3]); cv.put(c - 1, 32, sk[4])
    cv.puts([(c + 1, 29), (c + 1, 30), (c + 2, 31), (c + 2, 32)], sk[1])
    cv.puts([(c - 4, 33), (c - 3, 34), (c + 3, 34), (c + 4, 33)], sk[1])
    cv.puts([(c - 2, 34), (c - 1, 34), (c, 34), (c + 1, 34), (c + 2, 34)], sk[1])
    cv.puts([(c - 3, 33), (c + 3, 33)], sk[0])
    for s in (-1, 1):                                         # cheek glow
        bx = c + s * 7
        for x in range(bx - 1, bx + 2):
            if cv.own[32, x] == fid:
                cv.put(x, 32, mix(cv.get(x, 32), BLUSH, 0.3))
    p_mouth(cv, c, 38, expr, talk)
    cv.outline()
    if expr == "warm":
        sparkle(cv, 57, 12)
    if expr == "concern":
        cv.puts([(c + 18, 18), (c + 17, 19), (c + 18, 19), (c + 19, 19), (c + 17, 20), (c + 18, 20), (c + 19, 20), (c + 18, 21)], SWEAT)
        cv.put(c + 17, 19, SWEAT_HI)
    if expr == "surprised":
        cv.puts([(56, 4), (56, 5), (56, 6), (56, 8), (59, 6), (60, 5), (61, 4)], SPARK2)
    return cv


# ==========================================================================
# checks, previews, output
# ==========================================================================
HEAD_PARTS = ("hair", "quiff", "face", "head", "hairside")


def body_height(cv):
    """Hair top to the bottom row (wheel contact in battle, soles in the world); props don't count."""
    body = np.zeros_like(cv.alpha)
    for n, pid in cv.names.items():
        if n in HEAD_PARTS:
            body |= cv.own == pid
    rows = np.nonzero(body.any(axis=1))[0]
    return cv.h - rows[0]


def foot_point(cv, world):
    """World: centre between the shoes on the sole row.  Battle: centre of the bottom row (tyre contact)."""
    y = cv.h - 1
    xs = []
    if world:
        ids = [pid for n, pid in cv.names.items() if n.startswith("shoe")]
        xs = [x for x in range(cv.w) if cv.alpha[y, x] and cv.own[y, x] in ids]
    if not xs:
        ids = [pid for n, pid in cv.names.items() if n.startswith("wheel")]
        xs = [x for x in range(cv.w) if cv.alpha[y, x] and cv.own[y, x] in ids]
    if not xs:
        xs = [x for x in range(cv.w) if cv.alpha[y, x]]
    return [int(round((min(xs) + max(xs)) / 2)), y]


def diff_box(a, b):
    d = np.any(np.array(a) != np.array(b), axis=2)
    ys, xs = np.nonzero(d)
    if len(xs) == 0:
        return None, 0
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), int(d.sum())


def preview(imgs, name, S=8, bg=(44, 44, 62)):
    os.makedirs(PREV, exist_ok=True)
    pad = 3
    W = sum(i.width + pad for i in imgs) + pad
    H = max(i.height for i in imgs) + 2 * pad
    sheet = Image.new("RGBA", (W, H), bg + (255,))
    x = pad
    for i in imgs:
        sheet.alpha_composite(i, (x, H - pad - i.height))
        x += i.width + pad
    sheet.resize((W * S, H * S), Image.NEAREST).save(os.path.join(PREV, name))


EXPRS = ("neutral", "warm", "concern", "surprised")
CAST_REF = "/tmp/claude-0/designs/cast-reference.png"


def build():
    for sub in ("", "talk", "idle"):
        os.makedirs(os.path.join(CELLS, sub), exist_ok=True)
    feet, cells = {}, {}
    battle = [b_front("idle"), b_front("talk"), b_front("tell"), b_front("hit"), b_side(), b_back()]
    world = [w_front("idle"), w_front("talk"), w_front("tell"), w_front("hit"), w_side(), w_back()]
    for prefix, group, want in (("battle", battle, BATTLE_H), ("world", world, WORLD_H)):
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            assert np.array(img)[-1, :, 3].any(), (name, "nothing on the bottom row")
            h = body_height(cv)
            assert h == want, (name, "height", h)
            img.save(os.path.join(CELLS, name))
            feet[name] = foot_point(cv, prefix == "world")
            cells[name] = img
    ent = entrance()
    img = ent.image()
    rows = np.nonzero((np.array(img)[..., 3] > 0).any(axis=1))[0]
    top = max(0, int(rows[0]) - 2)
    img = img.crop((0, top, img.width, img.height))
    img.save(os.path.join(CELLS, "entrance.png"))
    fx, fy = foot_point(ent, False)
    feet["entrance.png"] = [fx, fy - top]
    cells["entrance.png"] = img
    print("entrance", img.size, "body height", body_height(ent))
    for i, e in enumerate(EXPRS):
        face = portrait(e).image()
        face.save(os.path.join(CELLS, "portrait-%d.png" % i))
        cells["portrait-%d.png" % i] = face
        talk = portrait(e, talk=True).image()
        box, n = diff_box(face, talk)
        assert box and box[0] >= 20 and box[2] <= 44 and box[1] >= 34 and box[3] <= 47, ("talk diff outside the mouth", e, box)
        talk.save(os.path.join(CELLS, "talk", "kyle-%d.png" % i))
        cells["talk-%d.png" % i] = talk
        print("talk", i, "changed", n, "px in", box)
    base = cells["world-0.png"]
    blink = w_front("blink").image()
    box, n = diff_box(base, blink)
    assert box and box[1] >= WT + 8 and box[3] <= WT + 9, ("blink changes more than the eyes", box)
    extras = {"blink": blink, "pose1": w_front("phone").image(), "pose2": w_front("latte").image()}
    for k, im in extras.items():
        assert im.size == base.size and np.array_equal(np.array(im)[-16:], np.array(base)[-16:]), (k, "feet/legs moved")
        im.save(os.path.join(CELLS, "idle", "kyle-%s.png" % k))
        cells["idle-" + k] = im
        print("idle", k, diff_box(base, im))
    deck, anchor = pitch_deck()
    deck.save(os.path.join(CELLS, "kyle-deck.png"))
    cells["deck"] = deck
    with open(os.path.join(CELLS, "kyle-deck.json"), "w", newline="\r\n") as fh:
        fh.write(json.dumps({"path": "kyle-deck.png", "size": list(deck.size), "anchor": list(anchor),
                             "anchor_is": "Kyle's battle foot point (cells 0-5) in this image", "z": "behind",
                             "battle_only": True}, indent=1) + "\n")
    with open(os.path.join(CELLS, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    contact_sheet(cells, feet, anchor)
    return cells, feet


def contact_sheet(cells, feet, anchor, S=3):
    """3x sheet: battle row (+ entrance, + Kyle in front of his deck), world row (+ idle extras),
    portrait row (+ talk), each beside the cast crops from the 3x cast reference."""
    from PIL import ImageFont
    BG = (44, 44, 62, 255)
    GROUND = (70, 70, 96, 255)
    font = ImageFont.load_default()
    ref = Image.open(CAST_REF).convert("RGBA") if os.path.exists(CAST_REF) else None

    def up(im):
        return im.resize((im.width * S, im.height * S), Image.NEAREST)

    combo = cells["deck"].copy()
    lf = feet["battle-0.png"]
    combo.alpha_composite(cells["battle-0.png"], (anchor[0] - lf[0], anchor[1] - lf[1]))
    r1 = [(up(cells["battle-%d.png" % i]), "battle-%d" % i) for i in range(6)]
    r1.append((up(cells["entrance.png"]), "cell 12 kyle-entrance"))
    r1.append((up(combo), "battle-0 + kyle-deck.png"))
    if ref is not None:
        r1.append((ref.crop((1440, 40, 1848, 285)), "cast: dev 80, jakerson 80"))
    r2 = [(up(cells["world-%d.png" % i]), "world-%d" % i) for i in range(6)]
    r2 += [(up(cells["idle-%s" % k]), "idle " + k) for k in ("blink", "pose1", "pose2")]
    if ref is not None:
        r2.append((ref.crop((990, 320, 1520, 496)), "cast: jules, imani, dev (world)"))
    r3 = [(up(cells["portrait-%d.png" % i]), "portrait-%d" % i) for i in range(4)]
    r3 += [(up(cells["talk-%d.png" % i]), "talk-%d" % i) for i in range(4)]
    if ref is not None:
        r3.append((ref.crop((830, 515, 1230, 708)), "cast: dev, jakerson"))
    rows = [r1, r2, r3]
    pad = 12
    widths = [sum(im.width + pad for im, _ in r) + pad for r in rows]
    heights = [max(im.height for im, _ in r) + 26 for r in rows]
    W, H = max(widths), sum(heights) + pad * 2 + 20
    sheet = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 6), "Kyle, Pearl Street founder (kyle) -- 3x; cast crops from designs/cast-reference.png at the same 3x",
           fill=(220, 220, 236, 255), font=font)
    y = pad + 20
    for r, rh in zip(rows, heights):
        x = pad
        base = y + rh - 18
        if r is not r3:
            d.rectangle([0, base, W, base + 1], fill=GROUND)
        for im, label in r:
            tp = base - im.height if r is not r3 else y
            sheet.alpha_composite(im, (x, tp))
            d.text((x, base + 4), label, fill=(200, 200, 220, 255), font=font)
            x += im.width + pad
        y += rh
    sheet.convert("RGB").save(os.path.join(HERE, "sheet.png"))


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "build"
    if arg == "build":
        cells, feet = build()
        for k, v in sorted(feet.items()):
            print(k, cells[k].size, v)
    elif arg == "front":
        preview([b_front(p).image() for p in ("idle", "talk", "tell", "hit")], "front8.png", S=6)
    elif arg == "sb":
        preview([b_side().image(), b_back().image()], "sb8.png", S=6)
    elif arg == "ent":
        preview([entrance().image()], "ent8.png", S=5)
    elif arg == "world":
        ims = [w_front(p).image() for p in ("idle", "talk", "tell", "hit")] + [w_side().image(), w_back().image()]
        ims += [w_front(p).image() for p in ("blink", "phone", "latte")]
        preview(ims, "world8.png", S=5)
    elif arg == "port":
        ims = [portrait(e).image() for e in EXPRS] + [portrait(e, talk=True).image() for e in EXPRS]
        preview(ims, "port8.png", S=4)
    elif arg == "head":
        preview([b_front(p).image().crop((26, 4, 76, 40)) for p in ("idle", "talk", "tell", "hit")], "head10.png", S=10)
