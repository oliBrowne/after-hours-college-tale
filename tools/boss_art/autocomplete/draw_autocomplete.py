#!/usr/bin/env python3
"""AUTOCOMPLETE -- procedural pixel-art sprites for "After Hours - College Tale".

The AI boss of Norlin's closed archive (N06, replaces INDEX).  A glowing chat
window with blinking cursor eyes floats over a server rack that is stacked and
stuffed with library books (one bay is INDEX's old brass card-catalog drawer).

Everything is drawn at its final pixel size with aliased shapes and per-pixel
placement, using Professor Eric's raster engine and art contract (INK outline,
5-tone ramps, upper-left key light).  Nothing that is drawn is ever resampled;
the only scaling in this file is the nearest-neighbour blow-up of previews and
the contact sheet.

Cell layout follows Professor Eric (eric-atlas.json), not INDEX:
  battle-0..5.png   88px tall battle cells   (0 front, 1 talking, 2 tell, 3 hit, 4 side R, 5 back)
  battle-12.png     entrance pose (wider canvas, ~100px tall)
  world-0..5.png    60px tall overworld cells (same poses)
  portrait-0..3.png 64x64 portraits          (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk-0..3.png     the same portraits mid-"speech": the typing dots light up and bounce
  idle-blink.png    world front with the cursor eyes off (its "blink" is the cursor blink)
  idle-pose1.png    world front, "thinking...": eyes glance up, typing dots, LEDs busy
  idle-pose2.png    world front with a suggestion popup sliding out of the window
  feet.json         foot point [x, y] for every body cell (centre between the casters)

python3 draw_autocomplete.py            draws the cells into ./cells and ./prev (8x previews)
python3 build_sheet.py cells            packs ./out (atlas, world bakes, talk/, idle/) + sheet.png
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
CELLS = os.path.join(HERE, "cells")
PREV = os.path.join(HERE, "prev")

# --------------------------------------------------------------------------
# palette (same contract as Eric: INK silhouette, 0..4 ramps, warm upper-left rim)
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline
RIM = (255, 170, 80)        # warm key-light rim (used lightly: it is a machine)

RAMP = {
    # 0 = line/darkest, 1 = shadow, 2 = mid, 3 = light, 4 = highlight
    "rack":    [(22, 24, 36), (44, 48, 66), (64, 70, 92), (90, 98, 124), (128, 138, 164)],
    "bay":     [(10, 10, 18), (20, 22, 34), (30, 34, 48), (44, 48, 66), (62, 68, 88)],
    "unit":    [(30, 32, 46), (68, 74, 96), (96, 104, 130), (128, 138, 164), (168, 178, 202)],
    "chrome":  [(58, 52, 92), (138, 136, 184), (184, 186, 222), (218, 220, 242), (248, 248, 255)],
    "title":   [(14, 62, 70), (28, 116, 120), (44, 160, 156), (84, 202, 188), (150, 236, 218)],
    "warn":    [(90, 50, 10), (170, 100, 24), (222, 148, 40), (246, 190, 80), (255, 226, 150)],
    "err":     [(80, 16, 26), (150, 32, 44), (204, 56, 60), (236, 100, 92), (252, 160, 140)],
    "screen":  [(8, 10, 22), (14, 22, 40), (18, 36, 56), (24, 50, 68), (34, 70, 86)],
    "back":    [(20, 18, 34), (40, 38, 62), (58, 56, 88), (80, 78, 114), (108, 106, 146)],
    "maroon":  [(60, 18, 30), (110, 32, 46), (150, 48, 58), (184, 78, 76), (214, 120, 108)],
    "green":   [(18, 46, 34), (32, 82, 56), (50, 114, 76), (82, 148, 98), (128, 184, 128)],
    "navy":    [(18, 24, 58), (30, 44, 98), (46, 66, 138), (76, 98, 172), (120, 140, 206)],
    "mustard": [(78, 52, 16), (150, 108, 34), (196, 150, 52), (224, 186, 86), (242, 218, 140)],
    "pages":   [(112, 92, 66), (190, 170, 134), (222, 206, 172), (240, 230, 204), (252, 248, 234)],
    "wood":    [(46, 24, 16), (92, 52, 30), (128, 76, 42), (162, 104, 60), (194, 138, 86)],
    "brass":   [(70, 44, 16), (140, 94, 36), (196, 140, 56), (232, 184, 88), (252, 226, 150)],
    "rubber":  [(14, 14, 20), (30, 30, 40), (46, 46, 58), (66, 66, 80), (90, 90, 106)],
    "metal":   [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "popup":   [(58, 52, 92), (150, 150, 196), (204, 206, 236), (230, 232, 248), (250, 250, 255)],
}
GLOW = (110, 236, 208)      # cursor / glyph mint
GLOW_HI = (226, 255, 246)
GLOW_DK = (44, 142, 140)
GLOW_DIM = (36, 86, 98)
GHOST = (70, 88, 124)       # ghost text on the screen
GHOST2 = (98, 118, 156)
LABEL = (236, 230, 210)     # call-number stickers
LED_G = (96, 244, 128)
LED_G_DK = (30, 96, 58)
LED_A = (255, 190, 64)
LED_R = (255, 84, 84)
WHITE = (250, 248, 244)
SPARK = (200, 255, 238)
SPARK2 = (110, 236, 208)
AMBER = (255, 196, 80)
RED = (255, 92, 92)

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


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def nb(m, dy, dx):
    """Value of the neighbour at (y+dy, x+dx); False beyond the canvas."""
    h, w = m.shape
    out = np.zeros_like(m)
    ys = slice(max(0, -dy), h - max(0, dy))
    yd = slice(max(0, dy), h - max(0, -dy))
    xs = slice(max(0, -dx), w - max(0, dx))
    xd = slice(max(0, dx), w - max(0, -dx))
    out[ys, xs] = m[yd, xd]
    return out


def erode(m):
    return m & nb(m, 0, 1) & nb(m, 0, -1) & nb(m, 1, 0) & nb(m, -1, 0)


def box_lv(m, hi=3, mid=2, lo=1, top=None):
    """Bevel for a box lit from the upper left: the ring just inside the part's
    dark edge is light on the top/left and dark on the bottom/right."""
    inner = erode(m)
    lv = np.where(m, mid, 0)
    lo_m = inner & (~nb(inner, 0, 1) | ~nb(inner, 1, 0))
    hi_m = inner & (~nb(inner, 0, -1) | ~nb(inner, -1, 0))
    lv[lo_m] = lo
    lv[hi_m] = hi
    if top is not None:
        lv[inner & ~nb(inner, -1, 0)] = top
    return lv


def stamp(cv, x, y, rows, cmap, flip=False):
    for j, row in enumerate(rows):
        if flip:
            row = row[::-1]
        for i, ch in enumerate(row):
            if ch in cmap:
                cv.put(x + i, y + j, cmap[ch])


GMAP = {"W": GLOW_HI, "M": GLOW, "m": GLOW_DK, "d": GLOW_DIM, "g": GHOST, "G": GHOST2,
        "K": INK, "A": AMBER, "R": RED, "w": WHITE}


def rrect(cv, x0, y0, x1, y1, r=2):
    m = cv.rect(x0, y0, x1, y1)
    cut = {1: [(0, 0)], 2: [(0, 0), (1, 0), (0, 1)], 3: [(0, 0), (1, 0), (2, 0), (0, 1), (0, 2), (1, 1)]}[r] if r else []
    for dx, dy in cut:
        for (cx, sx), (cy, sy) in (((x0, 1), (y0, 1)), ((x1, -1), (y0, 1)), ((x0, 1), (y1, -1)), ((x1, -1), (y1, -1))):
            px, py = cx + sx * dx, cy + sy * dy
            if 0 <= px < cv.w and 0 <= py < cv.h:
                m[py, px] = False
    return m


def sparkle(cv, x, y, big=False, c=SPARK, c2=SPARK2):
    cv.put(x, y, c)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cv.put(x + dx, y + dy, c2)
    if big:
        for dx, dy in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            cv.put(x + dx, y + dy, c2)


# --------------------------------------------------------------------------
# the chat window
# --------------------------------------------------------------------------
def window(cv, x0, y0, x1, y1, tb, bez, title="title", tail=None, r=2, name="win", dots=True,
           screen_lv=None):
    """Rounded chat window: title bar of height `tb` (inside the ink), a chrome
    bezel `bez` px wide, and a dark screen.  Returns the screen box."""
    m = rrect(cv, x0, y0, x1, y1, r)
    if tail is not None:
        m |= cv.poly(tail)
    cv.part(name, m, "chrome", edge="dark", lv=box_lv(m, hi=4, mid=2, lo=1))
    # title bar
    tbm = cv.rect(x0 + 1, y0 + 1, x1 - 1, y0 + tb) & m
    lv = np.where(tbm, 3, 0)
    lv[tbm & (cv.Y == y0 + 1)] = 4
    lv[tbm & (cv.Y == y0 + tb)] = 2
    lv[tbm & (cv.X >= x1 - 2)] = np.minimum(lv[tbm & (cv.X >= x1 - 2)], 2)
    cv.part(name + "_title", tbm, title, edge=False, lv=lv)
    rp = RAMP[title]
    cv.hline(x0 + 2, x1 - 2, y0 + tb + 1, RAMP["chrome"][0])          # seam under the title bar
    if dots:
        dy = y0 + 1 + (tb - 1) // 2
        step = 3 if tb >= 4 else 2
        for i in range(3):
            cv.put(x0 + 3 + i * step, dy, WHITE if i == 0 else rp[4])
            if tb >= 5:
                cv.put(x0 + 3 + i * step, dy + 1, rp[4] if i == 0 else rp[3])
        # close "x" on the right
        if tb >= 5:
            xx = x1 - 4
            cv.puts([(xx - 1, dy - 1), (xx + 1, dy - 1), (xx, dy), (xx - 1, dy + 1), (xx + 1, dy + 1)], rp[0])
        else:
            cv.put(x1 - 3, dy, rp[0])
    # screen
    sx0, sy0, sx1, sy1 = x0 + bez, y0 + tb + 2, x1 - bez, y1 - bez
    sm = cv.rect(sx0, sy0, sx1, sy1)
    if screen_lv is None:
        cy = (sy0 + sy1) / 2.0
        cx = (sx0 + sx1) / 2.0
        d = ((cv.X - cx) / max(1, (sx1 - sx0) / 2.0)) ** 2 + ((cv.Y - cy) / max(1, (sy1 - sy0) / 2.0)) ** 2
        screen_lv = np.where(sm, np.where(d < 0.45, 3, np.where(d < 1.1, 2, 1)), 0)
    cv.part(name + "_screen", sm, "screen", edge="dark", lv=screen_lv)
    # glass glare in the top-left corner of the screen
    cv.put(sx0 + 1, sy0 + 1, RAMP["screen"][4])
    cv.put(sx0 + 2, sy0 + 1, RAMP["screen"][3])
    cv.put(sx0 + 1, sy0 + 2, RAMP["screen"][3])
    return sx0, sy0, sx1, sy1


# eye glyphs (battle scale) --------------------------------------------------
EYE_B = {
    "cursor": ["MWm"] * 10,
    "cursor_off": ["..."] * 10,
    "caret": ["..WW..", ".MWWM.", "MM..MM", "m....m"],
    "chev": ["MM...", ".MW..", "..WW.", "...WW", "..WW.", ".MW..", "MM..."],
    "x": ["WM..MW", ".WMMW.", "..WW..", ".WMMW.", "WM..MW"],
    "up": ["MWm"] * 8,
}
EYE_W = {
    "cursor": ["MW"] * 5,
    "cursor_off": [".."] * 5,
    "caret": [".W.", "MWM", "M.M"],
    "chev": ["M..", "MW.", ".WW", "MW.", "M.."],
    "x": ["W.W", ".M.", "W.W"],
    "up": ["MW"] * 4,
}


def halo(cv, box, before, color=None):
    """Soft glow: screen pixels next to newly drawn glyph pixels get a dim mint."""
    sx0, sy0, sx1, sy1 = box
    new = np.zeros((cv.h, cv.w), bool)
    sub = (cv.col[sy0:sy1 + 1, sx0:sx1 + 1] != before[sy0:sy1 + 1, sx0:sx1 + 1]).any(axis=2)
    new[sy0:sy1 + 1, sx0:sx1 + 1] = sub
    ring = (nb(new, 0, 1) | nb(new, 0, -1) | nb(new, 1, 0) | nb(new, -1, 0)) & ~new
    ring[:sy0 + 1, :] = False; ring[sy1:, :] = False; ring[:, :sx0 + 1] = False; ring[:, sx1:] = False
    c = np.array(color or GLOW_DIM)
    cv.col[ring] = (cv.col[ring] * 0.45 + c * 0.55).astype(int)


def face(cv, box, eye="cursor", mouth="flat", scale="B", look=(0, 0), glow=True):
    """Draw the face glyphs centred in the screen box."""
    before = cv.col.copy()
    _face(cv, box, eye, mouth, scale, look)
    if glow:
        halo(cv, box, before)


def _face(cv, box, eye, mouth, scale, look):
    sx0, sy0, sx1, sy1 = box
    c = (sx0 + sx1) // 2
    E = EYE_B if scale == "B" else EYE_W
    rows = E[eye]
    ew = len(rows[0])
    gap = 10 if scale == "B" else 6        # half distance between eye centres
    ey = sy0 + (4 if scale == "B" else 2) + look[1]
    if eye == "caret":
        ey += 2 if scale == "B" else 1
    if eye == "x":
        ey += 1
    for side in (-1, 1):
        ex = c + side * gap - ew // 2 + look[0] + (0 if scale == "B" or side < 0 else 1)
        stamp(cv, ex, ey, rows, GMAP, flip=(side > 0 and eye in ("chev",)))
    my = sy1 - (4 if scale == "B" else 2)
    mouth_glyph(cv, c + look[0], my, mouth, scale)


def mouth_glyph(cv, c, my, mouth, scale):
    if scale == "B":
        if mouth == "flat":
            cv.hline(c - 4, c + 4, my, GLOW_DK); cv.hline(c - 3, c + 3, my, GLOW)
        elif mouth == "smile":
            cv.hline(c - 3, c + 3, my, GLOW); cv.put(c - 4, my - 1, GLOW_DK); cv.put(c + 4, my - 1, GLOW_DK)
            cv.put(c - 5, my - 2, GLOW_DK); cv.put(c + 5, my - 2, GLOW_DK)
        elif mouth == "dots":        # typing indicator, middle dot up (mid-bounce)
            for i, dx in enumerate((-5, -1, 3)):
                yy = my - (1 if i == 1 else 0)
                cv.puts([(c + dx, yy), (c + dx + 1, yy), (c + dx, yy - 1), (c + dx + 1, yy - 1)], GLOW)
                cv.put(c + dx, yy - 1, GLOW_HI)
        elif mouth == "dots_dim":
            for dx in (-5, -1, 3):
                cv.puts([(c + dx, my), (c + dx + 1, my), (c + dx, my - 1), (c + dx + 1, my - 1)], GLOW_DIM)
        elif mouth == "zig":
            pts = [(c - 4, my), (c - 3, my - 1), (c - 2, my), (c - 1, my - 1), (c, my), (c + 1, my - 1),
                   (c + 2, my), (c + 3, my - 1), (c + 4, my)]
            cv.puts(pts, GLOW)
        elif mouth == "grin":       # tell: a wide flat grin with a cursor in it
            cv.hline(c - 6, c + 6, my, GLOW); cv.hline(c - 5, c + 5, my - 1, GLOW_DK)
            cv.put(c - 7, my - 1, GLOW); cv.put(c + 7, my - 1, GLOW)
        elif mouth == "o":
            cv.puts([(c - 1, my - 2), (c, my - 2), (c - 2, my - 1), (c + 1, my - 1), (c - 2, my), (c + 1, my),
                     (c - 1, my + 1), (c, my + 1)], GLOW)
    else:
        if mouth == "flat":
            cv.hline(c - 2, c + 3, my, GLOW_DK); cv.hline(c - 1, c + 2, my, GLOW)
        elif mouth == "smile":
            cv.hline(c - 1, c + 2, my, GLOW); cv.put(c - 2, my - 1, GLOW_DK); cv.put(c + 3, my - 1, GLOW_DK)
        elif mouth == "dots":
            for i, dx in enumerate((-3, 0, 3)):
                cv.put(c + dx + 1, my - (1 if i == 1 else 0), GLOW_HI if i == 1 else GLOW)
        elif mouth == "dots_dim":
            for dx in (-3, 0, 3):
                cv.put(c + dx + 1, my, GLOW_DIM)
        elif mouth == "zig":
            cv.puts([(c - 2, my), (c - 1, my - 1), (c, my), (c + 1, my - 1), (c + 2, my), (c + 3, my - 1)], GLOW)
        elif mouth == "grin":
            cv.hline(c - 3, c + 4, my, GLOW); cv.put(c - 4, my - 1, GLOW); cv.put(c + 5, my - 1, GLOW)


# --------------------------------------------------------------------------
# books and the rack
# --------------------------------------------------------------------------
BOOKS = ["maroon", "green", "navy", "mustard"]


def book_flat(cv, name, x0, y0, x1, y1, ramp, label=True, glow_top=False, pages=False, bands=True):
    """A book lying flat, spine towards the viewer (or the page block if `pages`)."""
    m = cv.rect(x0, y0, x1, y1)
    rp = RAMP["pages" if pages else ramp]
    lv = np.where(m, 2, 0)
    lv[m & (cv.Y == y0 + 1)] = 3
    if y1 - y0 >= 4:
        lv[m & (cv.Y == y1 - 1)] = 1
    lv[m & (cv.X == x0 + 1)] = np.maximum(lv[m & (cv.X == x0 + 1)], 3)
    cv.part(name, m, "pages" if pages else ramp, edge="dark", lv=lv)
    if pages:
        for x in range(x0 + 2, x1 - 1, 2):
            cv.vline(x, y0 + 1, y1 - 1, rp[1]) if False else None
        cv.hline(x0 + 1, x1 - 1, (y0 + y1) // 2, rp[1]) if y1 - y0 >= 4 else None
        return
    h = y1 - y0 - 1
    if bands and x1 - x0 >= 10:
        for bx in (x0 + 2, x1 - 2):
            cv.vline(bx, y0 + 1, y1 - 1, RAMP["mustard"][3] if ramp != "mustard" else RAMP["mustard"][0])
    if label and x1 - x0 >= 8:
        lx = x0 + (x1 - x0) * 3 // 5
        cv.vline(lx, y0 + 1, y1 - 1, LABEL)
        if x1 - x0 >= 16 and h >= 3:
            cv.vline(lx + 1, y0 + 1, y1 - 1, LABEL)
            cv.put(lx, y0 + 2, RAMP["navy"][1])
    if glow_top:
        for x in range(x0 + 1, x1):
            if cv.alpha[y0 + 1, x]:
                cv.col[y0 + 1, x] = np.array(mix(tuple(cv.col[y0 + 1, x]), GLOW, 0.35))


def spines(cv, name, x0, y0, x1, y1, seed=0, widths=None):
    """Books standing in a bay: vertical spines with call-number labels."""
    rng = np.random.default_rng(seed)
    x = x0
    i = 0
    widths = widths or [3, 2, 3, 3, 2, 4, 3, 2, 3]
    while x <= x1:
        w = widths[i % len(widths)]
        xe = min(x1, x + w - 1)
        top = y0 + int(rng.integers(0, 2)) if i % 3 else y0
        ramp = RAMP[BOOKS[(i + seed) % 4]]
        for xx in range(x, xe + 1):
            cv.vline(xx, top, y1, ramp[3] if xx == x else ramp[1] if xx == xe and w > 2 else ramp[2])
        cv.put(x, top, ramp[4])
        if y1 - top >= 4:
            cv.put(x + (1 if w > 2 else 0), y1 - 1, LABEL)
        x = xe + 1
        if x <= x1:
            cv.vline(x, top, y1, RAMP["bay"][0]) if False else None
        i += 1


def unit(cv, name, x0, y0, x1, y1, led=(LED_G, LED_G_DK, LED_G), drive=True, vents=True):
    """A 1U/2U server face: LEDs on the left, drive slot, vent slots."""
    m = cv.rect(x0, y0, x1, y1)
    cv.part(name, m, "unit", edge="dark", lv=box_lv(m, hi=3, mid=2, lo=1))
    my = (y0 + y1) // 2
    for i, c in enumerate(led):
        cv.put(x0 + 2 + i * 2, my, c)
    if drive and x1 - x0 >= 16:
        dx0 = x0 + 3 + len(led) * 2
        cv.hline(dx0, dx0 + 6, my, RAMP["bay"][1]); cv.hline(dx0, dx0 + 6, my + 1, RAMP["unit"][3]) if y1 - y0 >= 4 else None
    if vents:
        vx = x1 - 2
        n = 0
        while vx > x0 + (x1 - x0) * 0.55 and n < 5:
            cv.vline(vx, y0 + 1 + (1 if y1 - y0 > 4 else 0), y1 - 1 - (1 if y1 - y0 > 4 else 0), RAMP["unit"][0])
            vx -= 2
            n += 1


def drawer(cv, name, x0, y0, x1, y1):
    """INDEX's brass-pull card-catalog drawer, now a rack bay."""
    m = cv.rect(x0, y0, x1, y1)
    cv.part(name, m, "wood", edge="dark", lv=box_lv(m, hi=3, mid=2, lo=1))
    c = (x0 + x1) // 2
    my = (y0 + y1) // 2
    if y1 - y0 >= 5:
        # label card holder + pull
        cv.hline(c - 2, c + 2, y0 + 1 + (1 if y1 - y0 > 6 else 0), RAMP["brass"][2])
        cv.hline(c - 1, c + 1, y0 + 1 + (1 if y1 - y0 > 6 else 0), LABEL)
        py = y1 - 2
        cv.hline(c - 2, c + 2, py, RAMP["brass"][3]); cv.put(c - 2, py, RAMP["brass"][4])
        cv.put(c - 3, py - 1, RAMP["brass"][1]); cv.put(c + 3, py - 1, RAMP["brass"][1])
        cv.hline(c - 2, c + 2, py + 1, RAMP["brass"][1])
    else:
        cv.hline(c - 1, c + 1, my, RAMP["brass"][3]); cv.put(c - 1, my, RAMP["brass"][4])


def rack(cv, x0, y0, x1, y1, bays, name="rack", rail=2, screws=True, lip=True):
    """The cabinet: body, rails with screw holes, bays from `bays`:
    list of (kind, ya, yb[, opts])."""
    m = cv.rect(x0, y0, x1, y1)
    if lip:
        m |= cv.rect(x0 - 1, y0, x1 + 1, y0 + 1)
    cv.part(name, m, "rack", edge="dark", lv=box_lv(m, hi=3, mid=2, lo=1))
    rp = RAMP["rack"]
    if lip:
        cv.hline(x0, x1, y0 + 1, rp[3]); cv.hline(x0 - 1 + 1, x1, y0 + 2, rp[0])
    # rails
    ix0, ix1 = x0 + rail + 1, x1 - rail - 1
    for x in range(x0 + 1, ix0):
        cv.vline(x, y0 + 3, y1 - 1, rp[3] if x == x0 + 1 else rp[2])
    for x in range(ix1 + 1, x1):
        cv.vline(x, y0 + 3, y1 - 1, rp[1])
    if screws:
        for y in range(y0 + 5, y1 - 1, 4):
            cv.put(x0 + rail, y, rp[0]); cv.put(x1 - rail, y, rp[0])
    # bay recess
    bm = cv.rect(ix0, y0 + 3, ix1, y1 - 2)
    cv.part(name + "_bay", bm, "bay", edge="dark", lv=np.where(bm, 1, 0))
    for k, b in enumerate(bays):
        kind, ya, yb = b[0], b[1], b[2]
        opts = b[3] if len(b) > 3 else {}
        if kind == "unit":
            unit(cv, "%s_u%d" % (name, k), ix0 + 1, ya, ix1 - 1, yb, **opts)
        elif kind == "books":
            spines(cv, "%s_b%d" % (name, k), ix0 + 1, ya, ix1 - 1, yb, **opts)
        elif kind == "drawer":
            drawer(cv, "%s_d%d" % (name, k), ix0 + 1, ya, ix1 - 1, yb)
        elif kind == "vent":
            for y in range(ya, yb + 1, 2):
                cv.hline(ix0 + 2, ix1 - 2, y, RAMP["bay"][3])
    return ix0, ix1


def caster(cv, name, cx, y1, big=True):
    if big:
        br = cv.rect(cx - 2, y1 - 4, cx + 2, y1 - 3)
        cv.part(name + "_br", br, "metal", edge="dark", lv=np.where(br, 2, 0))
        wh = cv.ell(cx, y1 - 1.0, 2.6, 1.9)
        cv.part(name, wh, "rubber", edge="dark", lv=np.where(wh, 2, 0))
        cv.put(cx, y1 - 1, RAMP["metal"][2]); cv.put(cx - 1, y1 - 2, RAMP["rubber"][4])
    else:
        br = cv.rect(cx - 1, y1 - 3, cx + 1, y1 - 2)
        cv.part(name + "_br", br, "metal", edge=False, lv=np.where(br, 2, 0))
        wh = cv.rect(cx - 2, y1 - 1, cx + 2, y1)
        cv.part(name, wh, "rubber", edge="dark", lv=np.where(wh, 2, 0))
        cv.put(cx, y1 - 1, RAMP["rubber"][3]) if False else None


def dropdown(cv, x0, y0, x1, rows, rh, name="pop", sel=0, scale="B"):
    """An autocomplete suggestion list: `rows` entries of height `rh`, entry `sel` highlighted."""
    y1 = y0 + rows * rh + 1
    m = rrect(cv, x0, y0, x1, y1, 1)
    cv.part(name, m, "popup", edge="dark", lv=box_lv(m, hi=4, mid=3, lo=2))
    for i in range(rows):
        ya = y0 + 1 + i * rh
        if i == sel:
            hm = cv.rect(x0 + 1, ya, x1 - 1, ya + rh - 1)
            cv.part(name + "_sel", hm, "title", edge=False, lv=np.where(hm, 3, 0))
            cv.hline(x0 + 1, x1 - 1, ya, RAMP["title"][4])
        ty = ya + rh // 2
        ln = (x1 - x0) - 4 - (i * 5) % 9
        col = WHITE if i == sel else RAMP["popup"][1]
        if scale == "B":
            cv.hline(x0 + 3, x0 + 3 + ln // 2, ty, col)
            cv.hline(x0 + 5 + ln // 2, x0 + ln - 1, ty, col if i == sel else RAMP["popup"][2])
            if i < rows - 1 and i != sel and i + 1 != sel:
                cv.hline(x0 + 2, x1 - 2, ya + rh - 1, RAMP["popup"][2])
        else:
            cv.hline(x0 + 2, x0 + 1 + ln // 2, ty, col)
            if ln > 10:
                cv.hline(x0 + 3 + ln // 2, x0 + ln - 2, ty, col if i == sel else RAMP["popup"][2])
    return y1


def glitch(cv, rows, dx, x0=0, x1=None):
    """Shift a band of rows sideways (a torn-signal slice)."""
    x1 = cv.w - 1 if x1 is None else x1
    for y in rows:
        for arr in (cv.col, cv.alpha, cv.own):
            seg = arr[y, x0:x1 + 1].copy()
            arr[y, x0:x1 + 1] = np.roll(seg, dx, axis=0)
            fillv = -1 if arr is cv.own else 0
            if dx > 0:
                arr[y, x0:x0 + dx] = fillv
            else:
                arr[y, x1 + 1 + dx:x1 + 1] = fillv


# ==========================================================================
# BODIES -- one drawing per pose, laid out from hand-picked native geometry
# (battle 88 px tall, world 60 px tall; nothing is scaled)
# ==========================================================================
G = {
    "B": dict(W=88, H=96, t=8, win=(30, 29), wh=36, tb=6, bez=3, tail=(21, 12, 24, 6),
              rack=(20, 19), ry0=49, rbot=5, cast=(15, 14), big=True, rail=2,
              bays=[("unit", 4, 9), ("books", 11, 17), ("unit2", 19, 22), ("drawer", 24, 30), ("vent", 32, 32)],
              stack=[("maroon", -15, 13, 4), ("green", -12, 16, 3), ("navy", -17, 10, 3)],
              slide=9, lev=(0, 1, 2), pop=(17, 12, 43, 3, 6), side_win=(22, 25), side_rack=(15, 15, 7),
              side_cast=(11, 11), look=5, glitch=((9, 12, 3), (24, 26, -3))),
    "W": dict(W=64, H=64, t=4, win=(21, 20), wh=22, tb=4, bez=2, tail=(14, 8, 16, 4),
              rack=(14, 13), ry0=32, rbot=5, cast=(10, 9), big=False, rail=1,
              bays=[("unit", 3, 6), ("books", 8, 12), ("unit2", 14, 16), ("drawer", 18, 21)],
              stack=[("maroon", -11, 9, 3), ("green", -8, 11, 3), ("navy", -12, 7, 2)],
              slide=6, lev=(0, 1, 1), pop=(12, 9, 30, 3, 4), side_win=(15, 17), side_rack=(10, 10, 5),
              side_cast=(7, 7), look=3, glitch=((6, 8, 2), (15, 16, -2))),
}


def stack_rows(g, c, ry0, pose=None):
    ys = []
    yb = ry0 - 1
    for k, (rpn, xa, xb, th) in enumerate(g["stack"]):
        ya = yb - th
        lift = g["lev"][k] if pose == "tell" else 0
        dx = g["slide"] if (pose == "hit" and k == 2) else 0
        ys.append((rpn, c + xa + dx, c + xb + dx, ya - lift, yb - lift))
        yb = ya
    return ys


def front(pose, sc="B"):
    g = G[sc]
    cv = Cv(g["W"], g["H"])
    c, t, H = g["W"] // 2, g["t"], g["H"]
    title = {"tell": "warn", "hit": "err"}.get(pose, "title")
    for i, dx in enumerate((-g["cast"][0], g["cast"][1])):
        caster(cv, "shoe%d" % i, c + dx, H - 1, big=g["big"])
    rx0, rx1, ry0, ry1 = c - g["rack"][0], c + g["rack"][1], t + g["ry0"], H - g["rbot"]
    leds = {"idle": (LED_G, LED_G_DK, LED_G), "talk": (LED_G, LED_G, LED_G_DK), "tell": (LED_A, LED_A, LED_A),
            "hit": (LED_R, LED_G_DK, LED_R), "think": (LED_A, LED_G, LED_A)}.get(pose, (LED_G, LED_G_DK, LED_G))
    leds2 = {"idle": (LED_G_DK, LED_G, LED_A), "talk": (LED_G, LED_A, LED_G), "tell": (LED_A, LED_R, LED_A),
             "hit": (LED_G_DK, LED_R, LED_G_DK), "think": (LED_G, LED_A, LED_G)}.get(pose, (LED_G_DK, LED_G, LED_A))
    if sc == "W":
        leds, leds2 = leds[:2], leds2[:2]
    bays = []
    for k, (kind, a, b) in enumerate(g["bays"]):
        if kind == "unit":
            bays.append(("unit", ry0 + a, ry0 + b, {"led": leds, "drive": sc == "B"}))
        elif kind == "unit2":
            bays.append(("unit", ry0 + a, ry0 + b, {"led": leds2, "drive": False}))
        elif kind == "books":
            bays.append(("books", ry0 + a, ry0 + b, {"seed": 1}))
        else:
            bays.append((kind, ry0 + a, ry0 + b))
    rack(cv, rx0, ry0, rx1, ry1, bays, rail=g["rail"], screws=sc == "B")
    ys = stack_rows(g, c, ry0, pose)
    for k, (rpn, xa, xb, ya, yb_) in enumerate(reversed(ys)):
        book_flat(cv, "book%d" % k, xa, ya, xb, yb_, rpn, glow_top=(k == 0))
    wy0, wy1 = t, t + g["wh"]
    wx0, wx1 = c - g["win"][0], c + g["win"][1]
    ta, tb_, tc, td = g["tail"]
    tail = [(c - ta, wy1 - 1), (c - tb_, wy1 - 1), (c - tc, wy1 + td)]
    box = window(cv, wx0, wy0, wx1, wy1, g["tb"], g["bez"], title=title, tail=tail)
    eye = {"idle": "cursor", "talk": "caret", "tell": "chev", "hit": "x", "think": "up", "off": "cursor_off",
           "suggest": "cursor"}[pose]
    mouth = {"idle": "flat", "talk": "dots", "tell": "grin", "hit": "zig", "think": "dots", "off": "flat",
             "suggest": "smile"}[pose]
    look = {"think": (g["look"] // 2, -1), "suggest": (1, 0)}.get(pose, (0, 0))
    face(cv, box, eye, mouth, sc, look=look)
    if pose == "suggest":                    # a ghost suggestion offered from the window's corner
        if sc == "W":
            dropdown(cv, c + 9, wy1 - 7, c + 29, 2, 4, sel=0, scale=sc)
        else:
            dropdown(cv, c + 14, wy1 - 10, c + 43, 2, 6, sel=0, scale=sc)
    if pose == "tell":
        a, b, e, n, rh = g["pop"]
        dropdown(cv, c + a, wy1 - b, c + e, n, rh, sel=0, scale=sc)
    cv.outline()
    if pose == "hit":
        for a, b, d in g["glitch"]:
            glitch(cv, range(t + a, t + b), d, wx0 - 1 - max(0, -d), wx1 + 1 + max(0, d))
    big = sc == "B"
    if pose in ("idle", "talk", "off", "think", "suggest"):
        sparkle(cv, wx1 + (4 if big else 3), t + 3, )
        cv.put(wx0 - 3, t + (12 if big else 8), SPARK2)
        if big:
            cv.put(wx1 + 3, t + 22, SPARK2)
    if pose == "talk":
        sparkle(cv, wx1 + (5 if big else 3), t + (13 if big else 10), c=GLOW_HI)
    if pose == "tell":
        for k in (1, 2):
            rpn, xa, xb, ya, yb_ = ys[k]
            cv.put(xa - 2, yb_ + 1, SPARK2)
        sparkle(cv, wx0 - 3, t + 4, c=AMBER, c2=(246, 150, 40))
    if pose == "hit":
        cv.puts([(wx0 - 4, t + 6), (wx0 - 5, t + 9), (wx1 + 4, t + 21 if not big else t + 31)], RED)
    return cv


def side(sc="B"):
    """Facing right: the rack's side panel, the window turned to the right."""
    g = G[sc]
    big = sc == "B"
    cv = Cv(g["W"], g["H"])
    c, t, H = g["W"] // 2, g["t"], g["H"]
    for i, dx in enumerate((-g["side_cast"][0], g["side_cast"][1])):
        caster(cv, "shoe%d" % i, c + dx, H - 1, big=g["big"])
    hw, hw2, fw = g["side_rack"]
    rx0, rx1, ry0, ry1 = c - hw, c + hw2, t + g["ry0"], H - g["rbot"]
    m = cv.rect(rx0, ry0, rx1 - fw, ry1) | cv.rect(rx0 - 1, ry0, rx1 - fw + 1, ry0 + 1)
    cv.part("rack", m, "rack", edge="dark", lv=box_lv(m, hi=3, mid=2, lo=1))
    rp = RAMP["rack"]
    for y in range(ry0 + (6 if big else 4), ry1 - (4 if big else 2), 3):
        cv.hline(rx0 + 3, rx1 - fw - 3, y, rp[0]); cv.hline(rx0 + 3, rx1 - fw - 3, y + 1, rp[3])
    if big:
        cv.put(rx0 + 2, ry0 + 4, rp[0]); cv.put(rx0 + 2, ry1 - 3, rp[0])
    f = cv.rect(rx1 - fw + 1, ry0, rx1, ry1) | cv.rect(rx1 - fw + 1, ry0, rx1 + 1, ry0 + 1)
    cv.part("rackfront", f, "rack", edge="dark", lv=np.where(f, 3, 0))
    fx0, fx1 = rx1 - fw + 3, rx1 - 1
    bm = cv.rect(fx0, ry0 + 3, fx1, ry1 - 2)
    cv.part("rackfront_bay", bm, "bay", edge=False, lv=np.where(bm, 1, 0))
    for kind, a, b in g["bays"]:
        ya, yb = ry0 + a, ry0 + b
        if kind in ("unit", "unit2"):
            for y in range(ya, yb + 1):
                cv.hline(fx0, fx1, y, RAMP["unit"][3] if y == ya else RAMP["unit"][2])
            cv.put(fx1, (ya + yb) // 2, LED_G)
        elif kind == "books":
            for y in range(ya, yb + 1):
                cv.hline(fx0, fx1, y, RAMP["pages"][3 if (y - ya) % 3 else 1])
        elif kind == "drawer":
            for y in range(ya, yb + 1):
                cv.hline(fx0, fx1 + 1, y, RAMP["wood"][3] if y == ya else RAMP["wood"][2])
            cv.put(fx1 + 1, yb - 1, RAMP["brass"][3]); cv.put(fx1 + 2, yb - 1, RAMP["brass"][2])
    for k, (rpn, xa, xb, ya, yb_) in enumerate(reversed(stack_rows(g, c, ry0))):
        book_flat(cv, "book%d" % k, xa + 1, ya, xb - 1, yb_, rpn, pages=True, glow_top=(k == 0))
        cv.vline(xb - 2, ya + 1, yb_ - 1, RAMP[rpn][2]); cv.vline(xb - 3, ya + 1, yb_ - 1, RAMP[rpn][1])
    wy0, wy1 = t, t + g["wh"]
    wx0, wx1 = c - g["side_win"][0], c + g["side_win"][1]
    d = 4 if big else 3
    slab = cv.poly([(wx0 - d, wy0 + d - 1), (wx0 + 1, wy0), (wx0 + 1, wy1), (wx0 - d, wy1 - d + 1)])
    cv.part("slab", slab, "back", edge="dark", lv=np.where(slab, 2, 0) + np.where(slab & (cv.Y < wy0 + 8), 1, 0))
    ta, tb_, tc, td = g["tail"]
    sh = g["win"][0] - g["side_win"][0]
    tail = [(c - ta + sh, wy1 - 1), (c - tb_ + sh, wy1 - 1), (c - tc + sh, wy1 + td)]
    box = window(cv, wx0, wy0, wx1, wy1, g["tb"], g["bez"], tail=tail)
    face(cv, box, "cursor", "flat", sc, look=(g["look"], 0))
    cv.outline()
    sparkle(cv, wx1 + (5 if big else 3), t + 4)
    return cv


def back(sc="B"):
    """From behind: the window's back panel (glow leaking at the seams) and the
    rack's mesh door with a cable waterfall; the books show their fore-edges."""
    g = G[sc]
    big = sc == "B"
    cv = Cv(g["W"], g["H"])
    c, t, H = g["W"] // 2, g["t"], g["H"]
    rx0, rx1, ry0, ry1 = c - g["rack"][0], c + g["rack"][1], t + g["ry0"], H - g["rbot"]
    m = cv.rect(rx0, ry0, rx1, ry1) | cv.rect(rx0 - 1, ry0, rx1 + 1, ry0 + 1)
    cv.part("rack", m, "rack", edge="dark", lv=box_lv(m, hi=3, mid=2, lo=1))
    rp = RAMP["rack"]
    ins = 3 if big else 2
    mesh = cv.rect(rx0 + ins, ry0 + ins + 1, rx1 - ins, ry1 - ins)
    cv.part("mesh", mesh, "bay", edge="dark", lv=np.where(mesh, 2, 0))
    for y in range(ry0 + ins + 2, ry1 - ins):
        for x in range(rx0 + ins + 1, rx1 - ins):
            if (x + y) % 2 == 0:
                cv.put(x, y, RAMP["bay"][4] if (x + y) % 4 == 0 else RAMP["bay"][3])
    hy = ry0 + (14 if big else 9)
    cv.vline(rx1 - ins - 2, hy, hy + (6 if big else 4), rp[3])
    cols = [(46, 120, 196), (230, 196, 70), (220, 80, 90), (90, 200, 120)]
    step = 3 if big else 2
    for i, col in enumerate(cols):
        x = rx0 + (8 if big else 5) + i * step
        fy = H - 2 - (3 - i) if big else H - 1 - (3 - i)
        pts = [(x, ry0 + ins + 3), (x, fy - 1), (x - 1, fy), (rx0 - 2 - i, fy)]
        cm = cv.chain(pts, 0.5)
        ramp = [mix(col, INK, 0.6), mix(col, INK, 0.3), col, mix(col, WHITE, 0.25), mix(col, WHITE, 0.5)]
        cv.part("cable%d" % i, cm, ramp, edge=False, lv=np.where(cm, 2, 0))
    for i, dx in enumerate((-g["cast"][0], g["cast"][1])):      # casters in front of the cable pool
        caster(cv, "shoe%d" % i, c + dx, H - 1, big=g["big"])
    for k, (rpn, xa, xb, ya, yb_) in enumerate(reversed(stack_rows(g, c, ry0))):
        xa, xb = 2 * c - xb, 2 * c - xa                      # mirrored: we are behind it
        book_flat(cv, "book%d" % k, xa, ya, xb, yb_, rpn, pages=True)
        cv.hline(xa + 1, xb - 1, ya + 1, RAMP[rpn][2])
    wy0, wy1 = t, t + g["wh"]
    wx0, wx1 = c - g["win"][1], c + g["win"][0]
    ta, tb_, tc, td = g["tail"]
    tail = [(c + ta, wy1 - 1), (c + tb_, wy1 - 1), (c + tc, wy1 + td)]
    w = rrect(cv, wx0, wy0, wx1, wy1, 2) | cv.poly(tail)
    cv.part("win", w, "back", edge="dark", lv=box_lv(w, hi=3, mid=2, lo=1))
    tbm = cv.rect(wx0 + 1, wy0 + 1, wx1 - 1, wy0 + g["tb"]) & w
    cv.part("win_title", tbm, "title", edge=False, lv=np.where(tbm, 1, 0) + np.where(tbm & (cv.Y == wy0 + 1), 1, 0))
    cv.hline(wx0 + 2, wx1 - 2, wy0 + g["tb"] + 1, RAMP["back"][0])
    if big:
        pl = cv.rect(c - 6, wy0 + 13, c + 5, wy0 + 26)
    else:
        pl = cv.rect(c - 4, wy0 + 9, c + 3, wy0 + 17)
    cv.part("plate", pl, "back", edge="dark", lv=box_lv(pl, hi=4, mid=3, lo=1))
    if big:
        for x, y in ((c - 4, wy0 + 15), (c + 3, wy0 + 15), (c - 4, wy0 + 24), (c + 3, wy0 + 24)):
            cv.put(x, y, RAMP["back"][0])
        st = cv.rect(wx0 + 6, wy1 - 9, wx0 + 14, wy1 - 5)
        cv.part("sticker", st, "pages", edge="dark", lv=np.where(st, 3, 0))
        cv.hline(wx0 + 8, wx0 + 12, wy1 - 7, RAMP["maroon"][2])
    else:
        st = cv.rect(wx0 + 4, wy1 - 6, wx0 + 9, wy1 - 3)
        cv.part("sticker", st, "pages", edge="dark", lv=np.where(st, 3, 0))
        cv.hline(wx0 + 6, wx0 + 7, wy1 - 5, RAMP["maroon"][2])
    cv.outline()
    for x in range(wx0 + 3, wx1 - 2, 3):
        cv.put(x, wy1, GLOW_DK)
    for y in range(wy0 + g["tb"] + 4, wy1 - 2, 3):
        cv.put(wx0, y, GLOW_DK); cv.put(wx1, y, GLOW_DK)
    return cv


# ==========================================================================
# PORTRAITS 64x64 -- the window fills the frame, the book stack and the top
# of the rack show below.  `talk` lights the typing dots in place of the mouth.
# ==========================================================================
PW = PH = 64
BLUSH = (255, 132, 170)
BLUSH2 = (190, 80, 128)
EYE_P = {
    "cursor": ["MWWm"] * 14,
    "short": ["MWWm"] * 10,
    "caret": ["...WW...", "..MWWM..", ".MM..MM.", "MM....MM", "m......m"],
    "o": ["..MMMM..", ".MWWWWM.", "MW....WM", "MW....WM", "MW....WM", "MW....WM", "MW....WM",
          ".MWWWWM.", "..MMMM.."],
}


def p_mouth(cv, c, my, expr, talk):
    if talk:
        # typing indicator: three 3x3 dots, bounced to suit the mood
        offs = {"neutral": (0, -2, 0), "warm": (-1, 1, -1), "concern": (-1, 0, 1), "surprised": (0, -2, 0)}[expr]
        for dx, oy in zip((-6, 0, 6), offs):
            big = expr == "surprised" and dx == 0
            r = 2 if big else 1
            for yy in range(-r, r + 1):
                for xx in range(-r, r + 1):
                    if big and abs(xx) == 2 and abs(yy) == 2:
                        continue
                    cv.put(c + dx + xx, my + oy + yy, GLOW)
            cv.put(c + dx - 1, my + oy - 1, GLOW_HI); cv.put(c + dx, my + oy - 1, GLOW_HI); cv.put(c + dx - 1, my + oy, GLOW_HI)
        return
    if expr == "neutral":
        cv.hline(c - 5, c + 5, my, GLOW); cv.hline(c - 4, c + 4, my + 1, GLOW_DK)
        cv.put(c - 5, my, GLOW_DK); cv.put(c + 5, my, GLOW_DK)
    elif expr == "warm":
        cv.hline(c - 4, c + 4, my + 1, GLOW); cv.hline(c - 3, c + 3, my + 2, GLOW_DK)
        cv.puts([(c - 5, my), (c - 6, my), (c + 5, my), (c + 6, my)], GLOW)
        cv.puts([(c - 7, my - 1), (c + 7, my - 1)], GLOW_DK)
    elif expr == "concern":
        for i, x in enumerate(range(c - 6, c + 7)):
            y = my + (0 if (i // 2) % 2 == 0 else 1)
            cv.put(x, y, GLOW if i % 2 == 0 else GLOW_DK if False else GLOW)
    elif expr == "surprised":
        cv.puts([(c - 1, my - 2), (c, my - 2), (c - 2, my - 1), (c + 1, my - 1), (c - 2, my), (c + 1, my),
                 (c - 1, my + 1), (c, my + 1)], GLOW)
        cv.puts([(c - 1, my - 1), (c, my - 1), (c - 1, my), (c, my)], RAMP["screen"][0])


def portrait(expr, talk=False):
    cv = Cv(PW, PH, open_bottom=True)
    c = 32
    # ---- rack top and the book stack (cut by the frame) ----
    rk = cv.rect(7, 58, 56, 63)
    cv.part("rack", rk, "rack", edge="dark", lv=np.where(rk, 2, 0))
    rp = RAMP["rack"]
    cv.hline(8, 55, 59, rp[3]); cv.hline(8, 55, 60, rp[0])
    um = cv.rect(12, 62, 51, 63)
    cv.part("unit", um, "unit", edge=False, lv=np.where(um, 3, 0))
    cv.hline(12, 51, 61, RAMP["bay"][1])
    lit = {"neutral": (LED_G, LED_G_DK, LED_G), "warm": (LED_G, LED_G, LED_G), "concern": (LED_A, LED_G_DK, LED_A),
           "surprised": (LED_R, LED_A, LED_G)}[expr]
    for i, col in enumerate(lit):
        cv.put(14 + i * 2, 63, col)
    for x in range(42, 50, 2):
        cv.put(x, 63, RAMP["unit"][0])
    stack = [("maroon", 11, 52, 54, 58), ("green", 15, 55, 50, 54), ("navy", 15, 50, 46, 50)]
    for k, (rpn, xa, xb, ya, yb) in enumerate(reversed(stack)):
        book_flat(cv, "book%d" % k, xa, ya, xb, yb, rpn, glow_top=(k == 0))
    # ---- window ----
    title = {"concern": "warn"}.get(expr, "title")
    tail = [(13, 46), (21, 46), (9, 52)]
    box = window(cv, 3, 3, 60, 46, 7, 3, title=title, tail=tail, r=3)
    # window title text in the bar
    cv.hline(14, 24, 6, RAMP[title][4]); cv.hline(26, 30, 6, RAMP[title][4])
    sx0, sy0, sx1, sy1 = box
    before = cv.col.copy()
    ey = sy0 + 5
    for side in (-1, 1):
        if expr == "neutral":
            stamp(cv, c + side * 11 - 2, ey, EYE_P["cursor"], GMAP)
        elif expr == "warm":
            stamp(cv, c + side * 11 - 4, ey + 4, EYE_P["caret"], GMAP)
        elif expr == "concern":
            stamp(cv, c + side * 11 - 2, ey + 4, EYE_P["short"], GMAP)
            brow = ["....MM", "..MM..", "MM...."]
            stamp(cv, c + side * 11 - 3, ey, brow, GMAP, flip=side > 0)
        elif expr == "surprised":
            stamp(cv, c + side * 11 - 4, ey + 2, EYE_P["o"], GMAP)
    if expr == "warm":                      # a bashful pixel blush
        for side in (-1, 1):
            bx = c + side * 11 - 2
            cv.puts([(bx, ey + 12), (bx + 2, ey + 12)], BLUSH)
            cv.puts([(bx + 1, ey + 11), (bx + 3, ey + 11)], BLUSH2)
    p_mouth(cv, c, sy1 - 6, expr, talk)
    halo(cv, box, before)
    cv.outline()
    if expr == "surprised":                 # a notification badge pops on the corner
        bm = cv.ell(57.5, 5.5, 4.6, 4.6)
        cv.fill(bm, RAMP["err"][0], only_alpha=False)
        cv.fill(cv.ell(57.5, 5.5, 3.6, 3.6), RAMP["err"][2], only_alpha=False)
        cv.puts([(56, 4), (56, 3)], RAMP["err"][4])
        cv.vline(58, 3, 6, WHITE); cv.put(57, 4, WHITE); cv.hline(57, 59, 8, WHITE) if False else cv.put(58, 8, WHITE)
        cv.puts([(48, 0), (49, 1), (62, 13), (63, 12)], SPARK)
    if expr == "warm":
        sparkle(cv, 61, 52) if False else cv.puts([(1, 50), (2, 49), (62, 50)], SPARK2)
    return cv


# ==========================================================================
# ENTRANCE (cell 12) -- the intro-card pose: the window rises out of the rack
# on beams of light, the book stack bursts into an orbit of open books, the
# old card-catalog drawer flies open and spits index cards, and two
# suggestion lists fan out like wings.
# ==========================================================================
EW, EH = 136, 112


def open_book(cv, name, x, y, ramp, flip=False):
    """A book flapping open, seen from the front: cover wings under two page fans."""
    cover = cv.poly([(x - 9, y - 3), (x, y + 1), (x + 9, y - 3), (x + 9, y + 1), (x, y + 5), (x - 9, y + 1)])
    cv.part(name, cover, ramp, edge="dark", lv=np.where(cover, 2, 0) + np.where(cover & (cv.X < x), 1, 0))
    pages = cv.poly([(x - 8, y - 6), (x, y - 2), (x + 8, y - 6), (x + 8, y - 2), (x, y + 2), (x - 8, y - 2)])
    lv = np.where(pages, 3, 0)
    lv[pages & (cv.X > x)] = 2
    lv[pages & (cv.X == x)] = 1
    cv.part(name + "_pg", pages, "pages", edge="dark", lv=lv)
    for k in (-5, -3, 3, 5):                                  # page lines
        xx = x + k
        yy = y - 4 + abs(k) // 2 - (abs(k) - 1) // 1 + 3 if False else y - 2 - (abs(k) // 2) + 1
        cv.put(xx, yy, RAMP["pages"][1])


def card(cv, name, x, y, tilt=0):
    m = cv.rect(x, y, x + 5, y + 3)
    cv.part(name, m, "pages", edge="dark", lv=np.where(m, 4, 0))
    cv.hline(x + 1, x + 3, y + 1, RAMP["maroon"][3])


def entrance():
    cv = Cv(EW, EH)
    c, H = EW // 2, EH
    t = H - 104
    for i, dx in enumerate((-15, 14)):
        caster(cv, "shoe%d" % i, c + dx, H - 1)
    rx0, rx1, ry0, ry1 = c - 20, c + 19, H - 41, H - 5
    lit = (LED_G, LED_G, LED_G)
    rack(cv, rx0, ry0, rx1, ry1, [
        ("unit", ry0 + 4, ry0 + 9, {"led": lit}),
        ("books", ry0 + 11, ry0 + 17, {"seed": 1}),
        ("unit", ry0 + 19, ry0 + 22, {"led": (LED_A, LED_G, LED_A), "drive": False}),
        ("vent", ry0 + 32, ry0 + 32),
    ])
    # the card-catalog drawer pulled out towards us (a deeper box, lower)
    dm = cv.rect(rx0 + 2, ry0 + 24, rx1 - 2, ry0 + 31)
    cv.part("drawer_box", dm, "wood", edge="dark", lv=box_lv(dm, hi=3, mid=2, lo=1))
    ins = cv.rect(rx0 + 4, ry0 + 24, rx1 - 4, ry0 + 26)
    cv.part("drawer_cards", ins, "pages", edge="dark", lv=np.where(ins, 3, 0))
    for x in range(rx0 + 6, rx1 - 4, 3):
        cv.vline(x, ry0 + 24, ry0 + 25, RAMP["pages"][4])
    cv.hline(c - 3, c + 2, ry0 + 29, RAMP["brass"][3]); cv.put(c - 3, ry0 + 29, RAMP["brass"][4])
    cv.hline(c - 3, c + 2, ry0 + 30, RAMP["brass"][1])
    # index cards fluttering up out of it
    for k, (x, y, tl) in enumerate(((c - 30, ry0 + 12, 1), (c + 25, ry0 + 6, -1), (c - 27, ry0 - 2, 0), (c + 28, ry0 + 18, 1))):
        card(cv, "card%d" % k, x, y, tl)
    # one book is still on the rack; the rest orbit
    book_flat(cv, "book_base", c - 15, ry0 - 5, c + 13, ry0 - 1, "maroon", glow_top=True)
    orbit = [("green", c - 50, t + 52, False), ("navy", c + 50, t + 50, True), ("mustard", c - 36, t + 64, False),
             ("maroon", c + 37, t + 62, True)]
    for k, (rpn, x, y, fl) in enumerate(orbit):
        open_book(cv, "ob%d" % k, x, y, rpn, fl)
    # the window, risen
    wy0, wy1 = t, t + 40
    wx0, wx1 = c - 36, c + 35
    tail = [(c - 26, wy1 - 1), (c - 16, wy1 - 1), (c - 30, wy1 + 7)]
    box = window(cv, wx0, wy0, wx1, wy1, 7, 3, tail=tail, r=3)
    cv.hline(wx0 + 14, wx0 + 26, wy0 + 3, RAMP["title"][4]); cv.hline(wx0 + 28, wx0 + 33, wy0 + 3, RAMP["title"][4])
    sx0, sy0, sx1, sy1 = box
    before = cv.col.copy()
    for side in (-1, 1):
        stamp(cv, c + side * 12 - 2, sy0 + 4, EYE_P["short"], GMAP)
    my = sy1 - 6
    cv.hline(c - 9, c + 9, my, GLOW); cv.hline(c - 8, c + 8, my + 1, GLOW_DK)
    cv.puts([(c - 10, my - 1), (c - 11, my - 2), (c + 10, my - 1), (c + 11, my - 2)], GLOW)
    cv.vline(c + 5, my - 4, my + 1, GLOW_HI)                 # a cursor blinking inside the grin
    halo(cv, box, before)
    # suggestion lists fanned out like wings
    dropdown(cv, 3, wy0 + 18, 30, 3, 6, name="popL", sel=1)
    dropdown(cv, EW - 31, wy0 + 12, EW - 4, 3, 6, name="popR", sel=0)
    cv.outline()
    # light beams between the rack and the window (after the outline: pure light)
    for x, y0_, y1_ in ((c - 8, wy1 + 2, ry0 - 7), (c - 2, wy1 + 4, ry0 - 7), (c + 4, wy1 + 2, ry0 - 7), (c + 10, wy1 + 5, ry0 - 7)):
        for y in range(y0_, y1_ + 1):
            if not cv.alpha[y, x]:
                cv.put(x, y, GLOW if (y + x) % 3 else GLOW_DK)
    for x, y in ((c - 44, t + 6), (c + 46, t + 2), (c - 56, t + 40), (c + 58, t + 36), (c - 20, ry0 + 2), (c + 24, ry0 - 4)):
        sparkle(cv, x, y, big=(x % 2 == 0))
    return cv


# ==========================================================================
# output
# ==========================================================================
BODY_H = {"battle": 88, "world": 60, "entrance": 104}


def foot_point(cv):
    """x = centre between the casters on the bottom row, y = bottom row."""
    y = cv.h - 1
    ids = [pid for n, pid in cv.names.items() if n.startswith("shoe") and not n.endswith("_br")]
    xs = [x for x in range(cv.w) if cv.alpha[y, x] and cv.own[y, x] in ids]
    if not xs:
        xs = [x for x in range(cv.w) if cv.alpha[y, x]]
    return [int(round((min(xs) + max(xs)) / 2)), y]


def check_height(img, want, name):
    a = np.array(img)[..., 3] > 0
    rows = np.nonzero(a.any(axis=1))[0]
    assert rows[-1] == img.height - 1, (name, "casters not on bottom row")
    assert img.height - rows[0] == want, (name, "height", img.height - rows[0])


def preview(img, path, S=8):
    bg = Image.new("RGBA", img.size, (44, 44, 62, 255))
    bg.alpha_composite(img)
    bg.resize((img.width * S, img.height * S), Image.NEAREST).save(path)


def build():
    os.makedirs(CELLS, exist_ok=True)
    os.makedirs(PREV, exist_ok=True)
    feet, cells = {}, {}
    poses = ("idle", "talk", "tell", "hit")
    groups = (("battle", [front(p, "B") for p in poses] + [side("B"), back("B")], 88),
              ("world", [front(p, "W") for p in poses] + [side("W"), back("W")], 60))
    for prefix, group, hgt in groups:
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            check_height(img, hgt, name)
            img.save(os.path.join(CELLS, name))
            feet[name] = foot_point(cv)
            cells[name] = img
    ent = entrance()
    img = ent.image()
    check_height(img, BODY_H["entrance"], "battle-12.png")
    img.save(os.path.join(CELLS, "battle-12.png"))
    feet["battle-12.png"] = foot_point(ent)
    cells["battle-12.png"] = img
    for i, e in enumerate(("neutral", "warm", "concern", "surprised")):
        for talk in (False, True):
            img = portrait(e, talk).image()
            name = ("talk-%d.png" if talk else "portrait-%d.png") % i
            img.save(os.path.join(CELLS, name))
            cells[name] = img
    base = cells["world-0.png"]
    for key, pose in (("blink", "off"), ("pose1", "think"), ("pose2", "suggest")):
        cv = front(pose, "W")
        img = cv.image()
        assert img.size == base.size and foot_point(cv) == feet["world-0.png"], key
        img.save(os.path.join(CELLS, "idle-%s.png" % key))
        cells["idle-%s.png" % key] = img
    with open(os.path.join(CELLS, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    for name, img in cells.items():
        preview(img, os.path.join(PREV, name.replace(".png", "-8x.png")))
    return cells, feet


if __name__ == "__main__":
    cells, feet = build()
    for k in sorted(cells):
        print(k, cells[k].size, feet.get(k, ""))
