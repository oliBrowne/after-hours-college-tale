#!/usr/bin/env python3
"""Sunbeam, jam-band frontman (rare mini-boss on the Farrand lawn) -- procedural pixel-art sprites
for "After Hours - College Tale".

Drawn the way Professor Eric is drawn (tools/eric_art/draw_eric.py, engine copied verbatim): parts
are masks shaded with material ramps from a top-left key light, given inner 1px lines and an ink
silhouette.  Everything is drawn at its final pixel size; nothing drawn is ever resampled (only the
contact sheet and the private 8x previews are nearest-neighbour blow-ups).

Look: a lanky, sun-tanned hippie with shoulder-length wavy honey-blond hair parted in the middle,
a woven orange headband with a little yellow sun on the forehead and a daisy tucked over one ear,
sky-blue mellow half-lidded eyes, a scruffy blond goatee and a sunburned nose.  His signature piece is
a LOUD rainbow spiral tie-dye tee (magenta / orange / yellow / teal / violet), plus a peace-sign
pendant, faded bell-bottoms with a flower patch, leather sandals, and a sunburst acoustic guitar on
an embroidered strap (stickers on its back).  Mellow, sunny, funny.

Outputs (in ./out next to this script):
  battle-0..5.png   82px tall battle cells   (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  entrance.png      cell 12 "sunbeam-entrance": power-strum with the sun rising behind his head
  world-0..5.png    52px tall overworld cells (same poses, redrawn small)
  portrait-0..3.png 64x64 portraits          (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk/sunbeam-0..3.png  mouth-open portraits (only mouth pixels differ)
  idle/sunbeam-blink.png, sunbeam-pose1.png (strum), sunbeam-pose2.png (peace sign)   world-front extras
  sunbeam-bus.png + sunbeam-bus.json   battle-only prop layer: the bubble-blowing camper bus behind him
  feet.json         foot point [x, y] for every body cell
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# --------------------------------------------------------------------------
# palette
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline (same ink as the cast)
INK2 = (23, 26, 43)

RAMP = {
    # 0 = line/darkest, 1 = shadow, 2 = mid, 3 = light, 4 = highlight
    "skin":    [(96, 44, 30), (176, 102, 68), (214, 142, 98), (236, 178, 132), (250, 210, 168)],
    "hair":    [(88, 56, 18), (158, 110, 40), (206, 160, 66), (236, 200, 104), (252, 232, 164)],
    "denim":   [(28, 38, 70), (58, 80, 124), (88, 116, 164), (124, 152, 196), (170, 194, 226)],
    "band":    [(110, 34, 14), (184, 64, 24), (226, 104, 36), (246, 148, 60), (255, 194, 110)],
    "leather": [(52, 28, 14), (102, 58, 28), (140, 86, 44), (176, 118, 66), (208, 156, 100)],
    "burst":   [(72, 24, 12), (150, 52, 20), (206, 106, 36), (240, 168, 64), (252, 216, 122)],
    "gback":   [(58, 26, 12), (116, 58, 26), (156, 88, 40), (194, 126, 66), (226, 168, 106)],
    "wood":    [(76, 40, 18), (138, 82, 40), (180, 120, 64), (214, 160, 98), (238, 200, 142)],
    "rosewood": [(30, 16, 12), (56, 32, 22), (78, 48, 32), (104, 68, 46), (134, 94, 66)],
    "metal":   [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "gold":    [(92, 62, 18), (160, 116, 36), (206, 166, 64), (236, 204, 104), (252, 236, 160)],
    "petal":   [(150, 150, 170), (206, 206, 218), (236, 236, 242), (250, 250, 252), (255, 255, 255)],
    "sun":     [(150, 70, 10), (230, 130, 20), (252, 186, 40), (255, 222, 90), (255, 246, 170)],
    # camper bus
    "cream":   [(110, 96, 84), (196, 184, 160), (232, 222, 196), (246, 240, 220), (255, 252, 240)],
    "teal":    [(14, 60, 66), (28, 120, 128), (48, 168, 170), (96, 204, 196), (164, 232, 220)],
    "glass":   [(20, 28, 56), (44, 62, 108), (70, 98, 150), (112, 146, 196), (176, 210, 240)],
    "tyre":    [(10, 10, 14), (26, 26, 32), (40, 40, 48), (58, 58, 68), (84, 84, 96)],
    "orange":  [(110, 40, 10), (200, 90, 30), (240, 140, 50), (252, 182, 90), (255, 220, 150)],
}
# the five dye ramps of the spiral tie-dye (index 0 unused: the shirt's own line is TIE_EDGE)
HUES = [
    [(90, 20, 60), (172, 40, 112), (222, 72, 152), (244, 122, 188), (255, 178, 220)],    # magenta
    [(110, 40, 10), (206, 92, 30), (242, 142, 50), (252, 184, 90), (255, 222, 150)],     # orange
    [(120, 90, 10), (214, 172, 30), (246, 214, 60), (255, 236, 120), (255, 250, 192)],   # yellow
    [(10, 70, 60), (28, 150, 122), (58, 196, 152), (120, 226, 184), (190, 246, 214)],    # teal
    [(40, 30, 100), (82, 70, 184), (112, 110, 228), (152, 156, 244), (202, 204, 255)],   # violet
]
TIE_EDGE = (62, 26, 70)
EYE = (34, 22, 24)
IRIS = (70, 140, 206)       # sky-blue eyes
IRIS_D = (38, 82, 140)
WHITE = (250, 248, 244)
SCLERA = (240, 236, 230)
MOUTH = (98, 34, 28)
LIP = (186, 98, 80)
TONGUE = (214, 104, 100)
TEETH = (250, 246, 236)
BLUSH = (232, 118, 92)      # sunburn on nose and cheeks
STRING = (226, 226, 214)
STRAP_DOTS = [(236, 72, 140), (250, 200, 50), (60, 190, 150), (120, 110, 230)]
PATCH = (240, 110, 150)
NOTE = (255, 228, 120)
NOTE2 = (255, 180, 70)
BUB = (176, 226, 250)
BUB2 = (236, 170, 236)
SWEAT = (120, 196, 240)
SWEAT_HI = (220, 244, 255)
SPARK = (255, 240, 170)
SPARK2 = (255, 200, 80)
RIM = (255, 170, 80)        # warm rim light (upper-left key light)

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
# shared props
# --------------------------------------------------------------------------
def tiedye(cv, name, mask, cx, cy, k=1.0, arms=5, band=2.6, phase=0.0, noedge=(), lv=None,
           rad=6, soft=1.2, cuts=(0.30, 0.56, 0.86), bias=0.0, core=True, seams=True):
    """Rainbow spiral tie-dye: hue = angle around (cx, cy) twisted by the radius; each hue keeps the
    form shading of the mask (levels 1-4).  The part's own 1px line is a dark plum."""
    if not mask.any():
        return mask
    if lv is None:
        lv = cv.levels(mask, rad=rad, soft=soft, cuts=cuts, bias=bias)
    lv = np.where(mask, np.clip(lv, 1, 4), 0)
    cv.part(name, mask, HUES[0], edge=TIE_EDGE, noedge=noedge, lv=lv)
    pid = cv.names[name]
    a = np.arctan2(cv.Y - cy, cv.X - cx)
    r = np.hypot(cv.X - cx, cv.Y - cy)
    ph = a / (2 * np.pi) * arms + r / (band * k) + phase
    hue = np.floor(ph).astype(int) % len(HUES)
    edge = np.all(cv.col == np.array(TIE_EDGE), axis=2)
    inner = (cv.own == pid) & ~edge
    for h in range(len(HUES)):
        sel = inner & (hue == h)
        cv.col[sel] = np.array(HUES[h])[lv[sel]]
    if seams:
        # crinkle seams: where one dye meets the next (following the spiral), the colour runs darker
        nxt = np.zeros_like(hue)
        nxt[:, :-1] = hue[:, 1:]
        dn = np.zeros_like(hue)
        dn[:-1, :] = hue[1:, :]
        seam = inner & (((nxt != hue) & (nxt == (hue + 1) % len(HUES))) | ((dn != hue) & (dn == (hue + 1) % len(HUES))))
        for h in range(len(HUES)):
            sel = seam & (hue == h)
            cv.col[sel] = np.array(HUES[h])[np.clip(lv[sel] - 1, 1, 4)]
    if core:
        cv.col[inner & (r < 1.0 * k + 0.25)] = HUES[2][4]
    return mask


def guitar(cv, bx, by, ang, s=1.0, name="gtr", face=True, stickers=True):
    """Sunburst acoustic.  (bx, by) = centre of the lower bout, ang = direction the neck points
    (screen radians, -pi/2 = straight up), s = scale (1 battle, ~0.63 world).
    face=False draws the plain wooden back (slung on his back) with a couple of stickers."""
    small = s < 0.8
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    P = lambda u, v: (bx + (ux * u + nx * v) * s, by + (uy * u + ny * v) * s)
    U = ((cv.X - bx) * ux + (cv.Y - by) * uy) / s
    V = ((cv.X - bx) * nx + (cv.Y - by) * ny) / s
    lit = 1 if (nx * -0.55 + ny * -0.75) > 0 else -1
    # ---- neck + headstock (behind the body) ----
    nw = 1.75 if small else 1.6
    neck = cv.capsule(*P(12, 0), *P(33, 0), nw * s)
    lvn = np.where(neck, 2, 0) + np.where(neck & (V * lit > 0.6), 1, 0)
    cv.part(name + "neck", neck, "rosewood" if face else "gback", edge="ink", lv=lvn)
    hs = cv.poly([P(32.4, -2.0), P(39.6, -2.7), P(40.6, -1.0), P(40.6, 1.0), P(39.6, 2.7), P(32.4, 2.0)])
    lvh = np.where(hs, 2, 0) + np.where(hs & (V * lit > 0.4), 1, 0)
    cv.part(name + "hs", hs, "rosewood", edge="ink", lv=lvh)
    # ---- body ----
    lower = cv.ell(*P(0, 0), 8.2 * s, 8.8 * s, ang)
    upper = cv.ell(*P(10, 0), 6.0 * s, 6.7 * s, ang)
    waist = cv.ell(*P(5, 0), 4.0 * s, 6.0 * s, ang)
    body = lower | upper | waist
    if face:
        R = np.hypot(U - 3.0, V * 1.05) / 9.4
        lv = np.where(R < 0.42, 4, np.where(R < 0.66, 3, np.where(R < 0.86, 2, 1)))
        lv = np.where(body, lv, 0)
        cv.part(name, body, "burst", edge="ink", noedge=(), lv=lv)
        pid = cv.names[name]
        if not small:
            # cream binding just inside the ink line
            inner = ndi.binary_erosion(body)
            bind = inner & ~ndi.binary_erosion(inner)
            ink = np.all(cv.col == np.array(INK), axis=2)
            cv.col[bind & (cv.own == pid) & ~ink] = RAMP["cream"][3]
        # soundhole with a rosette
        hr_ = 2.5 * s if not small else 1.4
        hole = cv.ell(*P(6.6, 0), hr_, hr_)
        if not small:
            ros = cv.ell(*P(6.6, 0), 3.5, 3.5) & ~hole & body
            cv.col[ros] = RAMP["gold"][3]
            cv.col[ros & (V * lit < -0.5)] = RAMP["gold"][2]
        cv.col[hole & body] = (36, 18, 12)
        # bridge
        br = cv.capsule(*P(-3.6, -3.4), *P(-3.6, 3.4), (0.9 if not small else 0.6) * s) & body
        cv.col[br] = (64, 32, 16)
        # strings: from the bridge to the nut, over body and fretboard
        own_ok = np.isin(cv.own, [cv.names[name], cv.names[name + "neck"]])
        ink = np.all(cv.col == np.array(INK), axis=2)
        vs = (-0.9, 0.9) if not small else (0.0,)
        for v in vs:
            x0, y0 = P(-3.6, v)
            x1, y1 = P(32.4, v * 0.6)
            n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
            for j in range(n + 1):
                px, py = int(round(x0 + (x1 - x0) * j / n)), int(round(y0 + (y1 - y0) * j / n))
                if 0 <= px < cv.w and 0 <= py < cv.h and own_ok[py, px] and not ink[py, px]:
                    if not hole[py, px]:
                        cv.col[py, px] = STRING
    else:
        lv = cv.levels(body, rad=8 * s, soft=1.2, cuts=(0.30, 0.55, 0.86))
        cv.part(name, body, "gback", edge="ink", lv=lv)
        if stickers and not small:
            # peace sticker on the lower bout, a daisy sticker on the upper bout
            px, py = P(-1.5, 1.5)
            ring = cv.ell(px, py, 2.6, 2.6) & ~cv.ell(px, py, 1.5, 1.5)
            cv.col[ring] = (250, 250, 246)
            cv.vline(round(px), round(py) - 2, round(py) + 2, (250, 250, 246))
            cv.put(round(px) - 1, round(py) + 1, (250, 250, 246)); cv.put(round(px) + 1, round(py) + 1, (250, 250, 246))
            dx, dy = P(10, -1.5)
            dx, dy = round(dx), round(dy)
            for (a_, b_) in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                cv.put(dx + a_, dy + b_, (236, 72, 140))
            cv.put(dx, dy, (250, 200, 50))
            sx, sy = P(4, -4.5)
            cv.puts([(round(sx), round(sy)), (round(sx) + 1, round(sy)), (round(sx), round(sy) + 1), (round(sx) + 1, round(sy) + 1)], (60, 190, 150))
        elif stickers:
            px, py = P(0, 0)
            cv.put(round(px), round(py), (250, 250, 246))
    return body | neck | hs


def guitar_pegs(cv, bx, by, ang, s=1.0):
    """Tuning pegs: metal nubs either side of the headstock (drawn after the outline)."""
    ux, uy = math.cos(ang), math.sin(ang)
    nx, ny = -uy, ux
    P = lambda u, v: (bx + (ux * u + nx * v) * s, by + (uy * u + ny * v) * s)
    for u in ((34.5, 37.0, 39.4) if s >= 0.8 else (36.0,)):
        for v in (-3.6, 3.6):
            x, y = P(u, v)
            x, y = int(round(x)), int(round(y))
            if 0 <= x < cv.w and 0 <= y < cv.h and not cv.alpha[y, x]:
                cv.put(x, y, RAMP["metal"][3] if v * (1 if (nx * -0.55 + ny * -0.75) > 0 else -1) > 0 else RAMP["metal"][1])


def gpoint(bx, by, ang, s, u, v):
    ux, uy = math.cos(ang), math.sin(ang)
    return (bx + (ux * u - uy * v) * s, by + (uy * u + ux * v) * s)


NOTE_A = ["..##.",
          "..#.#",
          "..#..",
          "###..",
          "##..."]
NOTE_B = [".####",
          ".#..#",
          ".#..#",
          "##.##",
          "#..#."]
NOTE_S = [".#",
          ".#",
          "##"]


def note(cv, x, y, glyph=NOTE_A, col=NOTE, over=False):
    for j, row in enumerate(glyph):
        for i, ch in enumerate(row):
            if ch == "#":
                px, py = x + i, y + j
                if 0 <= px < cv.w and 0 <= py < cv.h and (over or not cv.alpha[py, px]):
                    cv.put(px, py, col)


def bubble(cv, x, y, r, over=False):
    """A soap bubble: a thin iridescent ring with a white catch-light, transparent inside."""
    pts = []
    for py in range(int(y - r - 1), int(y + r + 2)):
        for px in range(int(x - r - 1), int(x + r + 2)):
            d = math.hypot(px - x, py - y)
            if abs(d - r) < 0.5:
                pts.append((px, py))
    for px, py in pts:
        if 0 <= px < cv.w and 0 <= py < cv.h and (over or not cv.alpha[py, px]):
            ang = math.atan2(py - y, px - x)
            c = BUB2 if (0.3 < ang < 2.2) else BUB
            cv.put(px, py, c)
    if r >= 2:
        hx, hy = int(round(x - r * 0.45)), int(round(y - r * 0.45))
        if 0 <= hx < cv.w and 0 <= hy < cv.h and (over or not cv.alpha[hy, hx]):
            cv.put(hx, hy, WHITE)


def sparkle(cv, x, y, big=False):
    pts = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    if big:
        pts += [(x - 2, y), (x + 2, y), (x, y - 2), (x, y + 2)]
    cv.puts(pts, SPARK2)
    cv.put(x, y, WHITE)


def assert_feet(img, name):
    bb = img.getbbox()
    assert bb[3] == img.height, (name, "feet not on bottom row", bb)


# ==========================================================================
# BODY PARTS  (k = 1 battle, k = WORLD_H / BODY_H for the world; all offsets are in battle pixels)
# ==========================================================================
BW, BH = 96, 90
BODY_H = 82
BT = BH - BODY_H
WW, WH = 60, 56
WORLD_H = 52
WT = WH - WORLD_H
KW = WORLD_H / BODY_H


def sandals_legs(cv, c, t, k=1.0, stance=0.0, patch=True, back=False):
    """Leather sandals (sole + bare foot + a strap), then faded bell-bottoms flaring over them."""
    small = k < 0.8
    lr = RAMP["leather"]
    for s in (-1, 1):
        bx = c + s * (5.4 + stance) * k
        fx = bx + s * 0.5 * k
        sole = cv.rect(fx - 4.1 * k, t + 80.0 * k, fx + 4.1 * k, t + 81.4 * k)
        cv.part("shoe%d" % s, sole, "leather", edge="ink", lv=np.where(sole, 2, 0) + np.where(sole & (cv.Y < t + 80.6 * k), 1, 0))
        foot = cv.ell(fx, t + 79.4 * k, 3.7 * k, 1.9 * k) & ~sole
        cv.part("foot%d" % s, foot, "skin" if not back else "leather", edge="dark", noedge=("shoe%d" % s,),
                lv=np.where(foot, 3, 0) - np.where(foot & (cv.X > fx + 1), 1, 0))
        if not small and not back:
            fxi = int(round(fx))
            cv.hline(fxi - 2, fxi + 2, int(round(t + 78 * k)), lr[2])          # strap over the instep
            cv.put(fxi - 2, int(round(t + 78 * k)), lr[3])
            for x in (fxi - 2, fxi, fxi + 2):
                cv.put(x, int(round(t + 79 * k)), RAMP["skin"][1])              # toe gaps
    for s in (-1, 1):
        x0, x1 = c + s * 4.6 * k, c + s * (5.4 + stance) * k
        leg = cv.capsule(x0, t + 46 * k, x1, t + 71 * k, 3.3 * k, 2.9 * k)
        fl = cv.poly([(x1 - 2.9 * k, t + 69 * k), (x1 + 2.9 * k, t + 69 * k), (x1 + 4.7 * k, t + 77.8 * k),
                      (x1 - 4.7 * k, t + 77.8 * k)])
        cv.part("leg%d" % s, leg | fl, "denim", rad=3.2 * k + 0.4, soft=0.8, cuts=(0.30, 0.55, 0.88), tex=0.04, seed=11 + s)
        dn = RAMP["denim"]
        if not small:
            # faded knee + a centre seam down the flare
            for y in range(int(t + 58 * k), int(t + 64 * k)):
                cv.put(int(round(x0 + (x1 - x0) * 0.5)) - 1, y, dn[3])
            for y in range(int(t + 71 * k), int(t + 77 * k)):
                cv.put(int(round(x1)), y, dn[1])
    if patch and not back:
        # a pink flower patch on the viewer-left knee
        px, py = int(round(c - 5 * k)), int(round(t + 62 * k))
        if small:
            cv.put(px, py, PATCH)
        else:
            cv.puts([(px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)], PATCH)
            cv.put(px, py, SPARK2)
    # belt line under the shirt hem shows a hint of a woven belt
    return


def tc_of(c, t, k):
    return (c - 1 * k, t + 33 * k)


def torso(cv, c, t, k=1.0, back=False):
    small = k < 0.8
    cv.part("neck", cv.rect(c - 2.5 * k, t + 18 * k, c + 2.5 * k, t + 23 * k), "skin", rad=2, bias=-0.15)
    m = cv.poly([(c - 6 * k, t + 22 * k), (c + 6 * k, t + 22 * k), (c + 11 * k, t + 24 * k), (c + 12.5 * k, t + 28.5 * k),
                 (c + 11 * k, t + 34 * k), (c + 11.5 * k, t + 46.5 * k), (c - 11.5 * k, t + 46.5 * k), (c - 11 * k, t + 34 * k),
                 (c - 12.5 * k, t + 28.5 * k), (c - 11 * k, t + 24 * k)])
    cx, cy = tc_of(c, t, k)
    tiedye(cv, "shirt", m, cx + (2 * k if back else 0), cy, k=k, rad=8 * k + 1, soft=1.4, cuts=(0.34, 0.62, 0.90),
           phase=0.5 if back else 0.0)
    if not small and not back:
        # crew-neck rib
        for x in range(int(c - 4), int(c + 5)):
            y = t + 23 if abs(x - c) < 3 else t + 22
            if cv.own[y, x] == cv.names["shirt"]:
                cv.put(x, y, HUES[2][3] if x < c else HUES[2][2])


def pendant(cv, c, t):
    lr = RAMP["leather"]
    cv.line(c - 3, t + 23, c - 1, t + 28, lr[1])
    cv.line(c + 3, t + 23, c + 1, t + 28, lr[0])
    PEACE = [".###.",
             "#.#.#",
             "#.#.#",
             "##.##",
             ".###."]
    mt = RAMP["metal"]
    for j, row in enumerate(PEACE):
        for i, ch in enumerate(row):
            if ch == "#":
                cv.put(c - 2 + i, t + 28 + j, mt[4] if (i + j) < 4 else mt[3] if i < 3 else mt[1])


def arm(cv, name, pts, k=1.0, tc=None, sleeve=True):
    """Bare tanned arm with a tie-dye short sleeve over the shoulder end."""
    r = max(1.7, 2.5 * k)
    m = cv.chain(pts, r)
    cv.part(name, m, "skin", edge="dark", rad=max(2, 3 * k), soft=0.8, cuts=(0.28, 0.52, 0.86), bias=0.04)
    if sleeve:
        (x0, y0), (x1, y1) = pts[0], pts[1]
        f = 0.55
        sl = cv.capsule(x0, y0, x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, max(2.2, 3.4 * k), max(2.0, 3.1 * k))
        tiedye(cv, name + "sl", sl, tc[0], tc[1], k=k, rad=3, soft=0.8, cuts=(0.30, 0.55, 0.88), noedge=("shirt",))
    return m


def hand(cv, x, y, name, k=1.0, r=2.5):
    rr = max(1.6, r * k)
    m = cv.ell(x, y, rr, rr)
    cv.part(name, m, "skin", edge="ink", rad=2.5, soft=0.7, bias=0.05)
    if k >= 0.8:
        cv.put(x + 1, y + 1, RAMP["skin"][1])
    return m


def open_hand(cv, x, y, name, k=1.0):
    """Raised open palm ("hey, man"): palm, a thumb out to the side, finger lines."""
    if k >= 0.8:
        m = cv.ell(x, y, 2.6, 3.2) | cv.capsule(x + 2.0, y + 1.0, x + 3.6, y - 0.8, 1.0)
        cv.part(name, m, "skin", edge="ink", rad=2.5, soft=0.7, bias=0.08)
        sk = RAMP["skin"]
        for fx in (x - 1, x + 1):
            cv.vline(int(round(fx)), int(round(y - 3)), int(round(y - 1)), sk[1])
    else:
        m = cv.ell(x, y, 1.7, 2.2) | cv.capsule(x + 1.3, y + 0.6, x + 2.4, y - 0.6, 0.7)
        cv.part(name, m, "skin", edge="ink", lv=np.where(m, 3, 0))
    return m


def peace_hand(cv, x, y, name, k=1.0):
    """Peace sign: a small fist with two fingers up in a V."""
    if k >= 0.8:
        m = cv.ell(x, y, 2.4, 2.3)
        m |= cv.capsule(x - 0.8, y - 1.5, x - 2.4, y - 6.2, 1.2, 1.05) | cv.capsule(x + 0.8, y - 1.5, x + 2.4, y - 6.2, 1.2, 1.05)
        cv.part(name, m, "skin", edge="ink", rad=2.5, soft=0.7, bias=0.08)
    else:
        m = cv.ell(x, y, 1.6, 1.5)
        m |= cv.capsule(x - 0.5, y - 1, x - 1.6, y - 4.2, 0.75) | cv.capsule(x + 0.5, y - 1, x + 1.6, y - 4.2, 0.75)
        cv.part(name, m, "skin", edge="ink", lv=np.where(m, 3, 0))
    return m


def strap(cv, x0, y0, x1, y1, k=1.0, name="strap"):
    m = cv.capsule(x0, y0, x1, y1, max(0.8, 1.1 * k))
    cv.part(name, m, "leather", edge="dark", lv=np.where(m, 2, 0))
    if k >= 0.8:
        L = math.hypot(x1 - x0, y1 - y0)
        n = int(L // 3)
        for j in range(1, n):
            px, py = x0 + (x1 - x0) * j / n, y0 + (y1 - y0) * j / n
            ix, iy = int(round(px)), int(round(py))
            if cv.own[iy, ix] == cv.names[name] and tuple(cv.col[iy, ix]) != RAMP["leather"][0]:
                cv.put(ix, iy, STRAP_DOTS[j % len(STRAP_DOTS)])
    return m


def hair_back_front(cv, c, t, k=1.0, flare=0.0):
    fl = flare
    m = cv.ell(c, t + 12 * k, 9.8 * k, 9.4 * k)
    for s in (-1, 1):
        m |= cv.capsule(c + s * 8.5 * k, t + 12 * k, c + s * (10.6 + fl) * k, t + 31 * k, 3.2 * k, 2.4 * k)
        m |= cv.ell(c + s * (11.4 + fl) * k, t + 25 * k, 1.8 * k, 2.6 * k)
    cv.part("hairback", m, "hair", rad=5 * k + 1, soft=1.0, cuts=(0.32, 0.58, 0.88), bias=-0.06, tex=0.06 if k >= 0.8 else 0, seed=63)


# ==========================================================================
# HEADS
# ==========================================================================
def yb_front(cv, c, t):
    return t + 7.6 + 0.045 * (cv.X - c) ** 2


def head_front(cv, c, t, pose, daisy=True):
    """Battle head, front view.  t = hair top."""
    sk, hr = RAMP["skin"], RAMP["hair"]
    face = cv.ell(c, t + 13.5, 7.2, 7.3) | cv.ell(c, t + 16, 6.2, 6.8)
    cv.part("face", face, "skin", rad=6, soft=1.4, cuts=(0.22, 0.48, 0.86), bias=0.06)
    yb = yb_front(cv, c, t)
    crown = cv.ell(c, t + 10.5, 9.0, 10.56) & (cv.Y < yb + 0.5)
    cv.part("crown", crown, "hair", noedge=("hairback",), rad=5, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.06, seed=67)
    # centre parting + strands
    cv.vline(c, t + 1, t + 6, hr[1])
    cv.line(c - 1, t + 2, c - 6, t + 7, hr[1]); cv.line(c + 1, t + 2, c + 6, t + 7, hr[0])
    cv.puts([(c - 3, t + 2), (c - 4, t + 3), (c - 2, t + 2), (c - 6, t + 5)], hr[4])
    # curtains: wavy locks framing the face, down past the shoulders
    for s in (-1, 1):
        m = cv.capsule(c + s * 7.3, t + 9, c + s * 8.2, t + 20.5, 1.9, 1.7) | cv.capsule(c + s * 8.2, t + 20, c + s * 9.2, t + 25, 1.8, 1.6)
        m |= cv.capsule(c + s * 9.2, t + 25, c + s * 8.6, t + 30, 1.6, 1.2)
        cv.part("curtain%d" % s, m, "hair", noedge=("hairback", "crown"), rad=3, soft=0.8,
                cuts=(0.28, 0.54, 0.86) if s < 0 else (0.40, 0.64, 0.92), tex=0.05, seed=70 + s)
        cv.line(c + s * 8, t + 13, c + s * 9, t + 22, hr[1])
    # forehead shadow under the band
    # headband (woven, orange) with a little sun on the front
    band = cv.ell(c, t + 12, 9.8, 10.7) & (cv.Y >= yb) & (cv.Y < yb + 2.0)
    lvb = np.where(band, 2, 0) + np.where(band & (cv.Y < yb + 1.0), 1, 0)
    cv.part("band", band, "band", edge=None, lv=lvb)
    bd = RAMP["band"]
    for x in range(c - 9, c + 10, 2):
        for y in range(t + 7, t + 13):
            if cv.own[y, x] == cv.names["band"] and tuple(cv.col[y, x]) == bd[3]:
                cv.put(x, y, bd[2])
                break
    for x in range(c - 6, c + 7):
        for y in range(t + 9, t + 14):
            if cv.own[y, x] == cv.names["face"] and cv.own[y - 1, x] == cv.names["band"]:
                cv.put(x, y, sk[2] if x < c - 2 else sk[1])
                break
    su = RAMP["sun"]
    cv.puts([(c - 1, t + 8), (c, t + 7), (c + 1, t + 8), (c, t + 9)], su[3])
    cv.put(c, t + 8, su[4])
    cv.puts([(c - 1, t + 7), (c + 1, t + 7), (c - 1, t + 9), (c + 1, t + 9)], su[1])
    if daisy:
        dx, dy = c + 8, t + 9
        cv.part("daisy", cv.ell(dx, dy, 2.2, 2.2), "petal", edge=None, lv=np.where(cv.ell(dx, dy, 2.2, 2.2), 3, 0))
        cv.put(dx, dy, RAMP["sun"][2]); cv.put(dx + 1, dy + 1, RAMP["petal"][1]); cv.put(dx - 1, dy + 1, RAMP["petal"][2])
    expr_front(cv, c, t, pose)


def expr_front(cv, c, t, pose):
    sk, hr = RAMP["skin"], RAMP["hair"]
    fid = cv.names["face"]
    # stubble along the jaw
    for y in range(t + 18, t + 23):
        for x in range(c - 7, c + 8):
            if cv.own[y, x] == fid and abs(x - c) >= 4 and tuple(cv.col[y, x]) != sk[0]:
                cv.put(x, y, mix(cv.get(x, y), hr[1], 0.35))
    # sunburned nose + cheeks
    cv.put(c, t + 16, sk[3]); cv.put(c, t + 17, BLUSH); cv.put(c + 1, t + 17, sk[1]); cv.put(c - 1, t + 17, mix(sk[2], BLUSH, 0.5))
    for s in (-1, 1):
        cv.put(c + s * 4, t + 16, mix(sk[2], BLUSH, 0.55)); cv.put(c + s * 5, t + 16, mix(sk[2], BLUSH, 0.4))
    ey = t + 13
    for side in (-1, 1):
        x0 = c - 5 if side < 0 else c + 2
        if pose in ("idle", "talk"):
            cv.hline(x0, x0 + 3, ey, EYE)
            cv.put(x0 + 1, ey + 1, IRIS_D if side < 0 else IRIS); cv.put(x0 + 2, ey + 1, IRIS if side < 0 else IRIS_D)
            cv.put(x0 + (3 if side < 0 else 0), ey + 1, sk[1])
        elif pose == "tell":
            cv.puts([(x0, ey + 1), (x0 + 1, ey), (x0 + 2, ey), (x0 + 3, ey + 1)], EYE)
        elif pose == "hit":
            mp = ["K...", ".KK.", "K..."] if side < 0 else ["...K", ".KK.", "...K"]
            for j, row in enumerate(mp):
                for i, ch in enumerate(row):
                    if ch == "K":
                        cv.put(x0 + i, ey - 1 + j, EYE)
    # brows (dark gold)
    if pose == "hit":
        cv.puts([(c - 5, t + 10), (c - 4, t + 10), (c - 3, t + 11)], hr[0]); cv.puts([(c + 5, t + 10), (c + 4, t + 10), (c + 3, t + 11)], hr[0])
    elif pose == "tell":
        cv.puts([(c - 5, t + 11), (c - 4, t + 10), (c - 3, t + 10)], hr[1]); cv.puts([(c + 5, t + 11), (c + 4, t + 10), (c + 3, t + 10)], hr[1])
    else:
        cv.puts([(c - 5, t + 11), (c - 4, t + 11), (c - 3, t + 11)], hr[1]); cv.puts([(c + 5, t + 11), (c + 4, t + 11), (c + 3, t + 11)], hr[1])
    # moustache
    cv.hline(c - 3, c + 3, t + 18, hr[1]); cv.put(c - 1, t + 18, hr[2]); cv.put(c, t + 18, hr[2])
    # mouth
    y = t + 19
    if pose == "idle":
        cv.put(c - 3, y, MOUTH); cv.put(c + 3, y, MOUTH); cv.hline(c - 2, c + 2, y + 1, MOUTH)
        cv.hline(c - 1, c + 1, y + 2, LIP)
    elif pose == "talk":
        cv.put(c - 3, y, MOUTH); cv.put(c + 3, y, MOUTH); cv.hline(c - 2, c + 2, y, TEETH)
        cv.hline(c - 2, c + 2, y + 1, MOUTH); cv.put(c, y + 1, TONGUE); cv.put(c - 1, y + 1, TONGUE)
        cv.hline(c - 1, c + 1, y + 2, LIP)
    elif pose == "tell":
        cv.put(c - 4, y - 1, MOUTH); cv.put(c + 4, y - 1, MOUTH); cv.put(c - 3, y, MOUTH); cv.put(c + 3, y, MOUTH)
        cv.hline(c - 2, c + 2, y, TEETH); cv.hline(c - 2, c + 2, y + 1, MOUTH); cv.hline(c - 1, c + 1, y + 2, LIP)
    elif pose == "hit":
        cv.hline(c - 1, c + 1, y, MOUTH); cv.hline(c - 2, c + 2, y + 1, MOUTH); cv.put(c, y + 1, TONGUE)
        cv.hline(c - 1, c + 1, y + 2, MOUTH)
    # goatee
    gy = t + 22
    cv.hline(c - 2, c + 2, gy, hr[2]); cv.put(c - 2, gy, hr[1]); cv.put(c + 2, gy, hr[1])
    cv.put(c - 1, gy, hr[3])
    if pose != "hit":
        cv.put(c - 1, t + 21, hr[2]); cv.put(c + 1, t + 21, hr[1])


def yb_world(cv, c, t):
    return t + 4.8 + 0.07 * (cv.X - c) ** 2


def w_head(cv, c, t, pose, daisy=True, glance=0):
    sk, hr = RAMP["skin"], RAMP["hair"]
    face = cv.ell(c, t + 8.6, 4.7, 4.7) | cv.ell(c, t + 10.2, 4.0, 4.4)
    cv.part("face", face, "skin", rad=4, soft=1.0, cuts=(0.22, 0.46, 0.88), bias=0.08)
    yb = yb_world(cv, c, t)
    crown = cv.ell(c, t + 6.7, 5.8, 6.75) & (cv.Y < yb + 0.5)
    cv.part("crown", crown, "hair", noedge=("hairback",), rad=3, soft=0.8, cuts=(0.28, 0.54, 0.86))
    cv.vline(c, t + 1, t + 3, hr[1]); cv.put(c - 2, t + 1, hr[4]); cv.put(c - 3, t + 2, hr[4])
    for s in (-1, 1):
        m = cv.capsule(c + s * 4.7, t + 6, c + s * 5.3, t + 13, 1.25, 1.1) | cv.capsule(c + s * 5.3, t + 13, c + s * 5.7, t + 19, 1.1, 0.8)
        cv.part("curtain%d" % s, m, "hair", noedge=("hairback", "crown"), rad=2, soft=0.6,
                cuts=(0.28, 0.54, 0.86) if s < 0 else (0.40, 0.64, 0.92))
    band = cv.ell(c, t + 8, 6.4, 7.0) & (cv.Y >= yb) & (cv.Y < yb + 1.0)
    cv.part("band", band, "band", edge=None, lv=np.where(band, 3, 0) - np.where(band & (cv.X > c + 2), 1, 0))
    cv.put(c, t + 5, RAMP["sun"][4])
    if daisy:
        cv.put(c + 5, t + 6, RAMP["petal"][4]); cv.put(c + 5, t + 7, RAMP["petal"][2]); cv.put(c + 6, t + 6, RAMP["petal"][3])
    ey = t + 8
    g = glance
    for side in (-1, 1):
        x0 = c - 3 if side < 0 else c + 1
        if pose == "blink":
            cv.hline(x0, x0 + 2, ey + 1, EYE)
        elif pose == "tell":
            cv.puts([(x0, ey + 1), (x0 + 1, ey), (x0 + 2, ey + 1)], EYE)
        elif pose == "hit":
            cv.put(x0 + (0 if side < 0 else 2), ey, EYE); cv.put(x0 + 1, ey + 1, EYE); cv.put(x0 + (0 if side < 0 else 2), ey + 2, EYE)
        else:
            cv.hline(x0, x0 + 2, ey, EYE)
            cv.put(x0 + 1 + g, ey + 1, IRIS_D)
    cv.put(c, t + 10, BLUSH)
    cv.put(c - 3, t + 10, mix(sk[2], BLUSH, 0.5)); cv.put(c + 3, t + 10, mix(sk[2], BLUSH, 0.5))
    if pose == "hit":
        cv.put(c - 2, t + 6, hr[0]); cv.put(c + 2, t + 6, hr[0])
    cv.hline(c - 2, c + 2, t + 11, hr[1])
    my = t + 12
    if pose in ("talk",):
        cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c, my + 1, TONGUE)
    elif pose == "hit":
        cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c, my + 1, MOUTH)
    elif pose == "tell":
        cv.hline(c - 1, c + 1, my, TEETH); cv.put(c - 2, my, MOUTH); cv.put(c + 2, my, MOUTH)
    else:
        cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c - 2, my - 1, MOUTH) if False else None
    gy = t + 13 if pose not in ("talk", "hit") else t + 14
    cv.hline(c - 1, c + 1, gy, hr[2]); cv.put(c, gy + 1 if gy == t + 13 else gy, hr[1])


# ==========================================================================
# CELLS  (one function per view; k picks battle (1.0) or world (52/82) size)
# ==========================================================================
def canvas(k):
    if k >= 0.8:
        return Cv(BW, BH), 48, BT
    return Cv(WW, WH), 30, WT


def front(pose, k=1.0, extra=None):
    """pose: idle | talk | tell | hit.  extra (world idle variants): None | blink | strum | peace."""
    battle = k >= 0.8
    cv, c, t = canvas(k)
    Q = lambda dx, dy: (c + dx * k, t + dy * k)
    tc = tc_of(c, t, k)
    hx = (2 if battle else 1) if pose == "hit" else 0
    hair_back_front(cv, c + hx, t, k)
    sandals_legs(cv, c, t, k)
    torso(cv, c, t, k)
    if battle:
        pendant(cv, c, t)
    if pose == "hit":
        gb, ga = Q(-8, 50), -0.25
    else:
        gb, ga = Q(-6, 48), -0.52
    # strap: from the neck heel up over his left shoulder (viewer right)
    sx0, sy0 = gpoint(gb[0], gb[1], ga, k, 13, -3.0)
    strap(cv, sx0, sy0, *Q(8.5, 23.5), k)
    # fretting arm (viewer right), hand wrapped over the neck
    fu = 24 if pose == "hit" else 27
    fh = gpoint(gb[0], gb[1], ga, k, fu, 0.8)
    elbow = Q(15, 35) if pose == "hit" else Q(14.5, 36)
    arm(cv, "armR", [Q(10.5, 25.5), elbow, (fh[0] + 0.5 * k, fh[1] + 1.2 * k)], k, tc)
    guitar(cv, gb[0], gb[1], ga, s=k, face=True)
    hand(cv, fh[0], fh[1], "handR", k, r=2.4)
    # strumming arm (viewer left)
    sh0 = Q(-10.5, 25.5)
    if extra == "peace":
        arm(cv, "armL", [sh0, Q(-16, 34), Q(-17, 27)], k, tc)
        peace_hand(cv, *Q(-17, 26), "handL", k)
    elif pose == "talk":
        arm(cv, "armL", [sh0, Q(-16, 33), Q(-18, 25)], k, tc)
        open_hand(cv, *Q(-18, 22.5), "handL", k)
    elif pose == "hit":
        arm(cv, "armL", [sh0, Q(-17, 32), Q(-21, 38)], k, tc)
        open_hand(cv, *Q(-21.5, 39), "handL", k)
    else:
        if pose == "tell":
            sp = gpoint(gb[0], gb[1], ga, k, -0.5, 5.0)
            el = Q(-15, 38)
        elif extra == "strum":
            sp = gpoint(gb[0], gb[1], ga, k, 0.5, 4.0)
            el = Q(-14.5, 38)
        else:
            sp = gpoint(gb[0], gb[1], ga, k, 1.5, 0.4)
            el = Q(-14, 37)
        arm(cv, "armL", [sh0, el, sp], k, tc)
        hand(cv, sp[0], sp[1], "handL", k)
    if battle:
        head_front(cv, c + hx, t, pose, daisy=(pose != "hit"))
    else:
        hp = extra if extra == "blink" else pose
        w_head(cv, c + hx, t, hp, daisy=(pose != "hit"), glance=(-1 if extra == "peace" else 0))
    cv.outline()
    # ---- soft extras after the outline ----
    guitar_pegs(cv, gb[0], gb[1], ga, k)
    if pose == "tell":
        if battle:
            sp = gpoint(gb[0], gb[1], ga, k, -0.5, 5.0)
            for j in range(3):                                        # strum swoosh
                cv.puts([(int(sp[0]) - 5 - j, int(sp[1]) - 4 + j * 2), (int(sp[0]) - 6 - j, int(sp[1]) - 3 + j * 2)], SPARK if j else WHITE)
            note(cv, c - 30, t + 22, NOTE_A)
            note(cv, c + 22, t + 4, NOTE_B, NOTE2)
            note(cv, c - 24, t + 6, NOTE_S)
            bubble(cv, c + 30, t + 40, 3)
            bubble(cv, c - 32, t + 40, 2)
            bubble(cv, c + 26, t + 18, 2)
        else:
            note(cv, c - 19, t + 12, NOTE_S)
            note(cv, c + 14, t + 2, NOTE_S, NOTE2)
            bubble(cv, c + 20, t + 24, 2)
    if pose == "talk" and battle:
        bubble(cv, c - 26, t + 12, 2)
    if extra == "strum":
        note(cv, c - 18, t + 26, NOTE_S)
    if extra == "peace":
        sparkle(cv, int(c - 17 * k), int(t + 20 * k))
    if pose == "hit":
        # a snapped string curling off the headstock, sweat, and the daisy knocked loose
        tip = gpoint(gb[0], gb[1], ga, k, 40.6, 0)
        tx, ty = int(round(tip[0])), int(round(tip[1]))
        if battle:
            curl = [(1, -1), (2, -2), (3, -3), (4, -3), (5, -2), (5, -1), (4, 0), (3, -1), (3, -2), (4, -5), (5, -6), (6, -6)]
            sx, sy = c + 9, t + 2
            cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx + 1, sy + 1), (sx, sy + 2)], SWEAT)
            cv.put(sx - 1, sy + 1, SWEAT_HI)
            dx, dy = c + 17, t + 6
            cv.puts([(dx - 1, dy), (dx + 1, dy), (dx, dy - 1), (dx, dy + 1)], RAMP["petal"][4])
            cv.put(dx, dy, RAMP["sun"][2])
            cv.puts([(dx + 3, dy + 4), (dx + 2, dy + 6)], RAMP["petal"][3])
        else:
            curl = [(1, -1), (2, -2), (3, -2), (3, -1), (2, -3)]
            cv.puts([(c + 6, t + 1), (c + 6, t + 2), (c + 5, t + 2)], SWEAT)
            cv.put(c + 10, t + 4, RAMP["petal"][4]); cv.put(c + 11, t + 5, RAMP["sun"][2])
        for (a_, b_) in curl:
            x, y = tx + a_, ty + b_
            if 0 <= x < cv.w and 0 <= y < cv.h and not cv.alpha[y, x]:
                cv.put(x, y, STRING)
    return cv


def side(k=1.0):
    """Facing RIGHT, walking pose: guitar slung on his back (its wooden back + stickers), hair down
    his back, headband tails streaming behind."""
    battle = k >= 0.8
    cv, c, t = canvas(k)
    c = c - 2
    Q = lambda dx, dy: (c + dx * k, t + dy * k)
    sk, hr = RAMP["skin"], RAMP["hair"]
    gb, ga = Q(-10, 43), -1.92
    guitar(cv, gb[0], gb[1], ga, s=k * 0.95, face=False)
    hb = cv.ell(*Q(-1, 11.5), 8.4 * k, 9.4 * k) | cv.capsule(*Q(-4, 12), *Q(-6.5, 30), 4.6 * k, 3.0 * k)
    hb |= cv.ell(*Q(-6.5, 29), 3.2 * k, 3.2 * k)
    cv.part("hairback", hb, "hair", rad=5 * k + 1, soft=1.0, cuts=(0.32, 0.58, 0.88), bias=-0.08,
            tex=0.06 if battle else 0, seed=65)
    # legs: back then front, each sandal under its flare
    for j, (lx, lean) in enumerate(((-2.5, -0.8), (1.5, 0.8))):
        x0 = c + lx * k
        x1 = x0 + lean * k
        sole = cv.rect(x1 - 3 * k, t + 80 * k, x1 + 5.5 * k, t + 81.4 * k)
        cv.part("shoe%d" % j, sole, "leather", edge="ink", lv=np.where(sole, 2 if j else 1, 0))
        foot = cv.ell(x1 + 1.6 * k, t + 79.4 * k, 4.3 * k, 1.9 * k) & ~sole
        cv.part("foot%d" % j, foot, "skin", edge="dark", noedge=("shoe%d" % j,),
                lv=np.where(foot, 3 if j else 2, 0))
        leg = cv.capsule(x0, t + 46 * k, x1, t + 71 * k, 3.1 * k, 2.8 * k)
        fl = cv.poly([(x1 - 2.8 * k, t + 69 * k), (x1 + 2.8 * k, t + 69 * k), (x1 + 4.4 * k, t + 77.8 * k), (x1 - 4.2 * k, t + 77.8 * k)])
        cv.part("leg%d" % j, leg | fl, "denim", rad=3 * k + 0.4, cuts=(0.30, 0.55, 0.88) if j else (0.45, 0.70, 0.95))
        if battle and j:
            fxi = int(round(x1 + 2)); cv.put(fxi, int(t + 78), RAMP["leather"][2]); cv.put(fxi + 1, int(t + 78), RAMP["leather"][2])
            cv.put(int(round(x1 + 5)), int(t + 79), sk[1])
    tor = cv.poly([Q(-5, 22), Q(3, 22), Q(7, 26), Q(8, 31), Q(6.5, 37), Q(7, 46.5), Q(-7.5, 46.5), Q(-7, 36), Q(-7, 28)])
    cv.part("neck", cv.rect(*Q(-2, 18), *Q(2, 23)), "skin", rad=2, bias=-0.15)
    tiedye(cv, "shirt", tor, *Q(0, 33), k=k, rad=7 * k + 1, soft=1.3, cuts=(0.28, 0.52, 0.84))
    strap(cv, *Q(-2, 23.5), *Q(6.5, 40), k)
    arm(cv, "arm", [Q(-0.5, 25.5), Q(0.5, 35.5), Q(2.5, 43)], k, Q(0, 33))
    hand(cv, *Q(3, 44.5), "hand", k, r=2.4)
    # ---- head (profile) ----
    head = cv.ell(*Q(1, 13.4), 7.2 * k, 7.4 * k) | cv.ell(*Q(3, 16), 5 * k, 6.6 * k) | cv.ell(*Q(4.6, 19.5), 3.4 * k, 3 * k)
    cv.part("head", head, "skin", rad=6 * k, soft=1.2, cuts=(0.22, 0.48, 0.86), bias=0.10)
    if battle:
        cv.part("nose", cv.ell(*Q(8.6, 15.6), 1.7, 1.6), "skin", edge="ink", noedge=("head",), rad=1.5, bias=0.15)
    ybs = t + (8 + 0.22 * (c + 7 * k - cv.X) / k) * k
    hair = cv.ell(*Q(-0.5, 10.5), 8.6 * k, 10.56 * k) & ((cv.X < c + 0.5 * k) | (cv.Y < ybs + 0.5))
    hair |= cv.capsule(*Q(-1.5, 13), *Q(-3, 27), 2.3 * k, 1.8 * k)
    cv.part("hair", hair, "hair", noedge=("hairback",), rad=5 * k, soft=1.0, cuts=(0.28, 0.54, 0.86),
            tex=0.06 if battle else 0, seed=69)
    band = cv.ell(*Q(-0.5, 12), 9.2 * k, 10.4 * k) & (cv.Y >= ybs) & (cv.Y < ybs + 2 * k) & (cv.X < c + 7.6 * k)
    tails = cv.capsule(*Q(-8, 11), *Q(-12.5, 17), max(0.7, 1.0 * k)) | cv.capsule(*Q(-8, 12), *Q(-10.5, 21), max(0.6, 0.9 * k))
    cv.part("band", band | tails, "band", edge="dark", lv=np.where(band | tails, 2, 0) + np.where(band & (cv.Y < ybs + k), 1, 0))
    if battle:
        cv.line(c - 3, t + 6, c + 4, t + 6, hr[1]); cv.line(c - 6, t + 13, c - 3, t + 24, hr[1])
        cv.line(c - 2, t + 1, c - 8, t + 9, hr[1]); cv.line(c + 2, t + 2, c - 4, t + 8, hr[1]); cv.line(c - 6, t + 3, c - 9, t + 12, hr[0])
        cv.puts([(c - 2, t + 3), (c - 1, t + 3), (c, t + 3), (c - 4, t + 4)], hr[4])
        # eye, brow, burn, beard
        cv.hline(c + 4, c + 6, t + 13, EYE); cv.put(c + 5, t + 14, IRIS); cv.put(c + 6, t + 14, IRIS_D)
        cv.hline(c + 4, c + 6, t + 11, hr[1])
        cv.put(c + 9, t + 16, BLUSH); cv.put(c + 5, t + 16, mix(sk[2], BLUSH, 0.5))
        hid = cv.names["head"]
        for y in range(t + 18, t + 23):
            for x in range(c - 1, c + 9):
                if cv.own[y, x] == hid and tuple(cv.col[y, x]) != sk[0]:
                    cv.put(x, y, mix(cv.get(x, y), hr[1], 0.35))
        cv.hline(c + 6, c + 8, t + 18, hr[1])
        cv.put(c + 7, t + 19, MOUTH); cv.put(c + 6, t + 19, MOUTH); cv.put(c + 8, t + 19, sk[2])
        cv.puts([(c + 5, t + 21), (c + 6, t + 21), (c + 7, t + 21), (c + 5, t + 22), (c + 6, t + 22)], hr[2])
        cv.put(c + 7, t + 22, hr[1])
        cv.part("daisy", cv.ell(c - 2, t + 9, 2.2, 2.2), "petal", edge=None, lv=np.where(cv.ell(c - 2, t + 9, 2.2, 2.2), 3, 0))
        cv.put(c - 2, t + 9, RAMP["sun"][2])
    else:
        cv.hline(c + 3, c + 4, t + 8, EYE); cv.put(c + 4, t + 9, IRIS)
        cv.put(c + 6, t + 10, BLUSH)
        cv.put(c + 4, t + 11, hr[1]); cv.put(c + 5, t + 11, hr[1])
        cv.put(c + 5, t + 12, MOUTH)
        cv.puts([(c + 3, t + 13), (c + 4, t + 13)], hr[2])
        cv.put(c - 1, t + 6, RAMP["petal"][4])
        cv.line(c, t + 1, c - 4, t + 4, hr[1])
    cv.outline()
    if not battle:
        cv.put(c + 6, t + 9, sk[2]) if False else None
    return cv


def back(k=1.0):
    """From behind: tie-dye spiral on the back, guitar slung diagonally, long hair, headband knot."""
    battle = k >= 0.8
    cv, c, t = canvas(k)
    Q = lambda dx, dy: (c + dx * k, t + dy * k)
    hr = RAMP["hair"]
    sandals_legs(cv, c, t, k, back=True)
    torso(cv, c, t, k, back=True)
    tc = (c + 2 * k, t + 33 * k)
    for s in (-1, 1):
        arm(cv, "arm%d" % s, [Q(s * 10.5, 25.5), Q(s * 12.5, 35), Q(s * 12.5, 43)], k, tc)
    gb, ga = Q(6, 46), -2.05
    guitar(cv, gb[0], gb[1], ga, s=k, face=False)
    tl = gpoint(gb[0], gb[1], ga, k, -8.4, 0)
    strap(cv, tl[0], tl[1], *Q(9.5, 23.5), k)
    for s in (-1, 1):
        hand(cv, *Q(s * 12.5, 44.5), "hand%d" % s, k)
    hb = cv.ell(*Q(0, 10.5), 9.4 * k, 10.56 * k) | cv.capsule(*Q(0, 14), *Q(0, 28), 8.6 * k, 7.0 * k)
    for dx in (-5, 0, 5):
        hb |= cv.ell(*Q(dx, 30), 2.8 * k, 2.4 * k)
    cv.part("hairback", hb, "hair", rad=7 * k + 1, soft=1.2, cuts=(0.30, 0.56, 0.86), tex=0.06 if battle else 0, seed=71)
    ybk = t + 9.0 * k + 0.035 * (cv.X - c) ** 2 / k
    band = cv.ell(*Q(0, 10.5), 9.8 * k, 10.8 * k) & (cv.Y >= ybk) & (cv.Y < ybk + 2 * k)
    knot = cv.ell(*Q(0, 10.5), 1.7 * k, 1.5 * k)
    tails = cv.capsule(*Q(-0.5, 11.5), *Q(-2.5, 22), max(0.6, 0.9 * k)) | cv.capsule(*Q(0.8, 11.5), *Q(2.2, 19.5), max(0.6, 0.9 * k))
    cv.part("band", band | knot | tails, "band", edge="dark", noedge=(), lv=np.where(band | knot | tails, 2, 0) + np.where(knot, 1, 0))
    if battle:
        for (x0, y0, x1, y1) in [(c - 3, t + 13, c - 6, t + 29), (c + 3, t + 13, c + 5, t + 28), (c - 6, t + 12, c - 8, t + 24),
                                 (c + 7, t + 12, c + 8, t + 24), (c, t + 22, c - 1, t + 30), (c - 1, t + 13, c - 3, t + 22),
                                 (c + 1, t + 14, c + 2, t + 23)]:
            cv.line(x0, y0, x1, y1, hr[1])
        for (x0, y0, x1, y1) in [(c - 5, t + 18, c - 5, t + 26), (c + 5, t + 18, c + 6, t + 25), (c + 2, t + 24, c + 2, t + 30)]:
            cv.line(x0, y0, x1, y1, hr[0])
        cv.puts([(c - 2, t + 15), (c - 2, t + 16), (c + 4, t + 16), (c - 7, t + 17)], hr[3])
        cv.puts([(c - 4, t + 3), (c - 3, t + 3), (c - 5, t + 4), (c + 2, t + 2)], hr[4])
        for (x0, y0, x1, y1, cc) in [(c, t + 1, c, t + 8, hr[1]), (c - 1, t + 2, c - 5, t + 9, hr[1]), (c + 1, t + 2, c + 5, t + 9, hr[0]),
                                     (c - 4, t + 2, c - 8, t + 9, hr[1]), (c + 4, t + 2, c + 8, t + 9, hr[0])]:
            cv.line(x0, y0, x1, y1, cc)
    else:
        cv.line(c - 2, t + 9, c - 4, t + 18, hr[1]); cv.line(c + 2, t + 9, c + 3, t + 18, hr[1])
        cv.line(c - 1, t + 1, c - 3, t + 4, hr[1]); cv.line(c + 1, t + 1, c + 3, t + 4, hr[1])
        cv.put(c + 6, t + 6, RAMP["petal"][4])
    cv.outline()
    guitar_pegs(cv, gb[0], gb[1], ga, k)
    if battle:   # the daisy peeking out over his left ear
        dx, dy = c + 9, t + 9
        cv.puts([(dx - 1, dy), (dx + 1, dy), (dx, dy - 1), (dx, dy + 1)], RAMP["petal"][3])
        cv.put(dx, dy, RAMP["sun"][2])
    return cv


def entrance():
    """Intro-card pose: the sun rises behind his head, peace sign thrown high, guitar raked up,
    eyes closed mid-song, hair flying, bubbles and notes everywhere."""
    W, H = 132, 124
    cv = Cv(W, H)
    c, t = 64, H - BODY_H
    k = 1.0
    Q = lambda dx, dy: (c + dx, t + dy)
    tc = tc_of(c, t, k)
    # the sun
    sx, sy = c + 1, t + 12
    for i in range(12):
        a = math.radians(i * 30 + 15)
        da = 0.15
        r0, r1 = 14.5, 24.0 if i % 2 == 0 else 20.5
        pts = [(sx + math.cos(a - da) * r0, sy + math.sin(a - da) * r0), (sx + math.cos(a) * r1, sy + math.sin(a) * r1),
               (sx + math.cos(a + da) * r0, sy + math.sin(a + da) * r0)]
        m = cv.poly(pts)
        cv.part("ray%d" % i, m, "sun", edge="dark", lv=np.where(m, 3 if i % 2 == 0 else 2, 0))
    disk = cv.ell(sx, sy, 14.5, 14.5)
    R = np.hypot(cv.X - sx + 3, cv.Y - sy + 3) / 15
    lv = np.where(disk, np.where(R < 0.45, 4, np.where(R < 0.8, 3, 2)), 0)
    cv.part("sun", disk, "sun", edge="dark", lv=lv)
    hair_back_front(cv, c, t, k, flare=2.0)
    for s in (-1, 1):   # flying locks
        m = cv.capsule(c + s * 10, t + 16, c + s * 16, t + 28, 2.6, 1.4) | cv.capsule(c + s * 10, t + 22, c + s * 15, t + 33, 2.2, 1.0)
        cv.part("fly%d" % s, m, "hair", noedge=("hairback",), rad=3, cuts=(0.30, 0.56, 0.88), tex=0.05, seed=80 + s)
    sandals_legs(cv, c, t, k, stance=3.0)
    torso(cv, c, t, k)
    pendant(cv, c, t)
    gb, ga = Q(-8, 50), -0.85
    s0 = gpoint(gb[0], gb[1], ga, k, 13, -3.0)
    strap(cv, s0[0], s0[1], *Q(8.5, 23.5), k)
    fh = gpoint(gb[0], gb[1], ga, k, 27, 0.8)
    arm(cv, "armR", [Q(10.5, 25.5), Q(18, 33), (fh[0] + 0.8, fh[1] + 1.0)], k, tc)
    guitar(cv, gb[0], gb[1], ga, s=k, face=True)
    hand(cv, fh[0], fh[1], "handR", k, r=2.4)
    arm(cv, "armL", [Q(-10.5, 25.5), Q(-18, 17), Q(-21, 9)], k, tc)
    peace_hand(cv, *Q(-21.5, 8), "handL", k)
    head_front(cv, c, t, "tell")
    # singing: open the grin into a big song
    y = t + 19
    cv.put(c - 4, y - 1, MOUTH); cv.put(c + 4, y - 1, MOUTH)
    cv.hline(c - 3, c + 3, y, TEETH); cv.put(c - 3, y, MOUTH); cv.put(c + 3, y, MOUTH)
    cv.hline(c - 3, c + 3, y + 1, MOUTH); cv.hline(c - 1, c + 1, y + 1, TONGUE)
    cv.hline(c - 2, c + 2, y + 2, MOUTH); cv.put(c, y + 2, TONGUE)
    cv.outline()
    guitar_pegs(cv, gb[0], gb[1], ga, k)
    note(cv, c - 44, t + 30, NOTE_B, NOTE2)
    note(cv, c + 36, t + 2, NOTE_A)
    note(cv, c + 42, t + 34, NOTE_S, NOTE2)
    note(cv, c - 36, t - 4, NOTE_A)
    for (x, y, r) in ((c - 40, t + 50, 4), (c + 44, t + 56, 3), (c - 50, t + 12, 2), (c + 50, t + 16, 3),
                      (c - 30, t - 20, 3), (c + 30, t - 26, 2), (c + 22, t + 70, 2), (c - 46, t + 70, 2)):
        bubble(cv, x, y, r)
    sparkle(cv, c - 25, t + 1, big=True)
    return cv


# ==========================================================================
# PORTRAITS  (64 x 64, head and shoulders)
# ==========================================================================
PW = PH = 64
EXPRS = ("neutral", "warm", "concern", "surprised")


def p_eye(cv, ex, ey, expr, side):
    """Pixel-map eyes; (ex, ey) = top-left of a 7-wide cell for the viewer-left eye, mirrored on the right.
    K lid/lash, W white, I blue iris, D pupil, H catch-light, S lower-lid shadow."""
    maps = {
        "neutral":   ["KKKKKKK",
                      ".KWHDIK",
                      "..WIIW.",
                      "..SSS.."],
        "warm":      [".......",
                      "..KKK..",
                      ".K...K.",
                      "K.....K",
                      ".SSSSS."],
        "concern":   [".KKKKK.",
                      "KWHDIWK",
                      ".WIIIW.",
                      "..WWW..",
                      "..SSS.."],
        "surprised": ["..KKK..",
                      ".KWWWK.",
                      "KWHDIWK",
                      "KWIDIWK",
                      ".KWIWK.",
                      "..SSS.."],
    }
    pal = {"K": EYE, "I": IRIS, "D": IRIS_D, "H": WHITE, "W": SCLERA, "S": RAMP["skin"][1]}
    for j, row in enumerate(maps[expr]):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x = ex + i if side < 0 else ex + (6 - i)
            col = pal[ch]
            if ch == "H" and side > 0:
                col = IRIS
            cv.put(x, ey + j, col)
    if side > 0:
        for j, row in enumerate(maps[expr]):
            if "H" in row:
                i = row.index("H")
                cv.put(ex + (6 - i) - 2, ey + j, WHITE)


def p_brows(cv, c, by, expr):
    hr = RAMP["hair"]
    if expr == "concern":
        left = [(-11, 0), (-10, 0), (-9, -1), (-8, -1), (-7, -2), (-6, -2), (-5, -3)]
    elif expr == "surprised":
        left = [(-12, 0), (-11, -1), (-10, -2), (-9, -2), (-8, -2), (-7, -2), (-6, -1)]
    elif expr == "warm":
        left = [(-12, 1), (-11, 0), (-10, -1), (-9, -1), (-8, -1), (-7, -1), (-6, 0)]
    else:   # mellow: soft, slightly lifted at the outer end
        left = [(-12, 1), (-11, 0), (-10, 0), (-9, 0), (-8, 0), (-7, 0), (-6, 0)]
    for side in (-1, 1):
        for i, (dx, dy) in enumerate(left):
            x = c + dx if side < 0 else c - dx
            cv.put(x, by + dy, hr[1] if side < 0 else hr[0])
            if 0 < i < 6:
                cv.put(x, by + dy - 1, hr[2] if side < 0 else hr[1])


def p_mouth(cv, c, my, expr, talk=False):
    if expr == "neutral":
        cv.put(c - 4, my - 1, MOUTH); cv.put(c + 4, my - 1, MOUTH)
        if not talk:
            cv.hline(c - 3, c + 3, my, MOUTH)
            cv.hline(c - 2, c + 2, my + 1, LIP)
        else:
            cv.hline(c - 3, c + 3, my, MOUTH); cv.hline(c - 2, c + 2, my, TEETH)
            cv.hline(c - 3, c + 3, my + 1, MOUTH); cv.hline(c - 1, c + 1, my + 1, TONGUE)
            cv.hline(c - 2, c + 2, my + 2, LIP)
    elif expr == "warm":
        cv.put(c - 7, my - 2, MOUTH); cv.put(c + 7, my - 2, MOUTH)
        cv.hline(c - 6, c + 6, my - 1, MOUTH)
        cv.hline(c - 5, c + 5, my, TEETH); cv.put(c - 6, my, MOUTH); cv.put(c + 6, my, MOUTH)
        if not talk:
            cv.hline(c - 5, c + 5, my + 1, MOUTH); cv.hline(c - 2, c + 2, my + 1, TONGUE)
            cv.hline(c - 3, c + 3, my + 2, LIP)
        else:
            cv.hline(c - 5, c + 5, my + 1, MOUTH); cv.hline(c - 4, c + 4, my + 2, MOUTH)
            cv.hline(c - 2, c + 2, my + 2, TONGUE); cv.hline(c - 1, c + 1, my + 1, TONGUE)
            cv.hline(c - 3, c + 3, my + 3, LIP)
    elif expr == "concern":
        cv.hline(c - 3, c + 3, my, MOUTH)
        cv.put(c - 4, my + 1, MOUTH); cv.put(c + 4, my + 1, MOUTH)
        if not talk:
            cv.hline(c - 2, c + 2, my + 1, LIP)
        else:
            cv.hline(c - 3, c + 3, my + 1, MOUTH); cv.hline(c - 1, c + 1, my + 1, TONGUE)
            cv.hline(c - 2, c + 2, my + 2, LIP)
    elif expr == "surprised":
        rows = ((0, 1), (1, 2), (2, 2), (3, 1)) if not talk else ((0, 1), (1, 2), (2, 2), (3, 2), (4, 1))
        for dy, w in rows:
            cv.hline(c - w, c + w, my + dy - 1, MOUTH)
        cv.hline(c - 1, c + 1, my + len(rows) - 2, TONGUE)
        cv.hline(c - 1, c + 1, my + len(rows) - 1, LIP)


def portrait(expr, talk=False):
    cv = Cv(PW, PH, open_bottom=True)
    c = 32
    sk, hr = RAMP["skin"], RAMP["hair"]
    lift = -1 if expr == "surprised" else 0
    # ---- long hair behind the shoulders ----
    back = cv.ell(c, 26 + lift, 18.6, 18)
    for s in (-1, 1):
        back |= cv.capsule(c + s * 15, 24, c + s * 19.5, 60, 5.4, 4.0) | cv.ell(c + s * 20.5, 50, 3.0, 4.2)
    cv.part("hairback", back, "hair", rad=9, soft=1.6, cuts=(0.32, 0.58, 0.88), bias=-0.06, tex=0.05, seed=63)
    # ---- tie-dye shoulders ----
    sh = cv.ell(c, 75, 31, 25) & cv.half(y=48)
    tiedye(cv, "shoulders", sh, c - 3, 68, k=1.6, rad=14, soft=2.0, cuts=(0.34, 0.60, 0.90))
    strap(cv, c + 17, 49, c + 22, 66, k=1.8, name="pstrap")
    cv.part("neck", cv.rect(c - 5, 40, c + 5, 52), "skin", rad=4, bias=-0.18)
    col = cv.ell(c, 51.5, 8.6, 3.0) & ~cv.ell(c, 49.9, 6.6, 2.4) & cv.half(y=49)
    cv.part("collar", col, "sun", edge=TIE_EDGE, lv=np.where(col, 3, 0) - np.where(col & (cv.X > c + 2), 1, 0))
    # pendant cord + the top of the peace sign
    lr = RAMP["leather"]
    cv.line(c - 5, 52, c - 2, 56, lr[1]); cv.line(c + 5, 52, c + 2, 56, lr[0])
    ring = cv.ell(c, 59.5, 3.6, 3.6) & ~cv.ell(c, 59.5, 2.4, 2.4)
    spokes = cv.rect(c - 0.4, 56, c + 0.4, 63) | cv.capsule(c, 59.5, c - 2.2, 61.7, 0.45) | cv.capsule(c, 59.5, c + 2.2, 61.7, 0.45)
    pm = ring | (spokes & cv.ell(c, 59.5, 3.0, 3.0))
    cv.part("peace", pm, "metal", edge=None, lv=np.where(pm, 3, 0) + np.where(pm & (cv.X < c) & (cv.Y < 59.5), 1, 0) - np.where(pm & (cv.X > c), 1, 0))
    # ---- face ----
    face = cv.ell(c, 28, 13.2, 13.6) | cv.ell(c, 33, 11.2, 12.4) | cv.ell(c, 38, 11.6, 8.2)
    cv.part("face", face, "skin", rad=11, soft=2.2, cuts=(0.16, 0.42, 0.86), bias=0.06)
    fid = cv.names["face"]
    ybp = 13.0 + lift + 0.024 * (cv.X - c) ** 2
    crown = cv.ell(c, 20 + lift, 17.4, 18.6) & (cv.Y < ybp + 1)
    cv.part("crown", crown, "hair", noedge=("hairback",), rad=8, soft=1.4, cuts=(0.28, 0.54, 0.86), tex=0.05, seed=67)
    cv.vline(c, 2 + lift, 12 + lift, hr[1])
    for (x0, y0, x1, y1) in [(c - 2, 3, c - 10, 12), (c - 4, 6, c - 13, 14), (c + 2, 3, c + 10, 12), (c + 5, 6, c + 13, 15)]:
        cv.line(x0, y0 + lift, x1, y1 + lift, hr[1] if x0 < c else hr[0])
    cv.puts([(c - 5, 4 + lift), (c - 6, 4 + lift), (c - 7, 5 + lift), (c - 4, 3 + lift), (c - 9, 7 + lift)], hr[4])
    for s in (-1, 1):
        m = cv.capsule(c + s * 13, 15, c + s * 15, 38, 3.3, 3.0) | cv.capsule(c + s * 15, 37, c + s * 17.5, 56, 3.1, 2.4)
        cv.part("curtain%d" % s, m, "hair", noedge=("hairback", "crown"), rad=5, soft=1.0,
                cuts=(0.28, 0.54, 0.86) if s < 0 else (0.40, 0.64, 0.92), tex=0.05, seed=90 + s)
        cv.line(c + s * 14, 20, c + s * 16, 38, hr[1]); cv.line(c + s * 16, 40, c + s * 17, 54, hr[1])
        cv.line(c + s * 12, 24, c + s * 13, 36, hr[0] if s > 0 else hr[1])
    if True:
        cv.puts([(c - 14, 22), (c - 14, 23), (c - 15, 41), (c - 16, 42)], hr[4])
    # headband
    band = cv.ell(c, 24, 19.5, 21) & (cv.Y >= ybp) & (cv.Y < ybp + 3.5)
    lvb = np.where(band, 2, 0) + np.where(band & (cv.Y < ybp + 1.2), 1, 0)
    cv.part("band", band, "band", edge="dark", lv=lvb)
    bd = RAMP["band"]
    for x in range(c - 18, c + 19):
        for y in range(8, 22):
            if cv.own[y, x] == cv.names["band"] and tuple(cv.col[y, x]) not in (bd[0],):
                if (x + y) % 3 == 0:
                    cv.put(x, y, bd[1] if tuple(cv.col[y, x]) == bd[2] else bd[2])
                break
    for x in range(c - 12, c + 13):
        for y in range(12, 26):
            if cv.own[y, x] == fid and cv.own[y - 1, x] == cv.names["band"]:
                cv.put(x, y, sk[1]); cv.put(x, y + 1, sk[2])
                break
    # the little sun on the band
    su = RAMP["sun"]
    sy = 14 + lift
    disk = cv.ell(c, sy, 2.4, 2.4)
    cv.part("sunemb", disk, "sun", edge=su[1], lv=np.where(disk, 3, 0) + np.where(disk & (cv.X < c) & (cv.Y < sy), 1, 0))
    for (dx, dy) in ((0, -4), (0, 4), (-4, 0), (4, 0), (-3, -3), (3, -3), (-3, 3), (3, 3)):
        cv.put(c + dx, sy + dy, su[2])
    # daisy over his left ear
    dx_, dy_ = c + 16, 16 + lift
    for i in range(8):
        a = i * math.pi / 4
        pm = cv.ell(dx_ + math.cos(a) * 2.6, dy_ + math.sin(a) * 2.6, 1.6, 1.6)
        cv.part("petal%d" % i, pm, "petal", edge=None, lv=np.where(pm, 3 if i in (3, 4, 5, 6) else 2, 0))
    ctr = cv.ell(dx_, dy_, 1.5, 1.5)
    cv.part("dcentre", ctr, "sun", edge=None, lv=np.where(ctr, 3, 0))
    # ---- cheeks, sunburn, nose ----
    for s in (-1, 1):
        bx = c + s * 8
        for y in (34, 35):
            for x in range(bx - 2, bx + 3):
                if cv.own[y, x] == fid:
                    cv.put(x, y, mix(cv.get(x, y), BLUSH, 0.4 if abs(x - bx) < 2 else 0.22))
    cv.puts([(c - 1, 28), (c - 1, 29), (c - 1, 30), (c - 1, 31)], sk[3])
    cv.puts([(c + 1, 31), (c + 1, 32), (c + 2, 33)], sk[1]); cv.puts([(c - 1, 34), (c, 34), (c + 1, 34)], sk[1])
    cv.put(c - 2, 33, sk[1]); cv.put(c, 33, mix(sk[2], BLUSH, 0.7)); cv.put(c - 1, 33, mix(sk[3], BLUSH, 0.5))
    # ---- beard: stubble on the jaw, moustache, goatee ----
    for y in range(36, 47):
        for x in range(c - 12, c + 13):
            if cv.own[y, x] == fid and tuple(cv.col[y, x]) != sk[0] and (abs(x - c) >= 7 or y >= 44):
                cv.put(x, y, mix(cv.get(x, y), hr[1], 0.42))
    goat = (cv.ell(c, 45.6, 5.6, 3.4) | cv.rect(c - 2.5, 42, c + 2.5, 44)) & face
    cv.part("goatee", goat, "hair", edge="dark", noedge=("face",), rad=3, soft=0.8, cuts=(0.28, 0.54, 0.86), bias=-0.05)
    cv.hline(c - 4, c + 4, 36, hr[2]); cv.hline(c - 6, c + 6, 37, hr[1]); cv.hline(c - 6, c + 6, 38, hr[1])
    cv.put(c - 7, 38, hr[1]); cv.put(c + 7, 38, hr[0]); cv.put(c - 7, 39, hr[1]); cv.put(c + 7, 39, hr[0])
    cv.put(c, 37, hr[0])
    cv.puts([(c - 4, 37), (c - 3, 37)], hr[3])
    p_mouth(cv, c, 41, expr, talk)
    ey = {"neutral": 25, "warm": 25, "concern": 24, "surprised": 23}[expr]
    p_eye(cv, c - 11, ey, expr, -1)
    p_eye(cv, c + 4, ey, expr, 1)
    by = {"neutral": 22, "warm": 22, "concern": 22, "surprised": 20}[expr]
    p_brows(cv, c, by, expr)
    if expr == "concern":
        cv.puts([(c - 1, 22), (c + 1, 22), (c, 23)], sk[1])
    cv.outline()
    cv.puts([(c + 2, 1 + lift), (c + 3, 0 + lift) if lift == 0 else (c + 3, 1)], hr[1])
    if expr == "warm":
        note(cv, 3, 4, NOTE_A)
    if expr == "surprised":
        cv.puts([(5, 14), (5, 15), (5, 16), (5, 18), (2, 16), (1, 15), (0, 14)], SPARK2)
    if expr == "concern":
        cv.puts([(13, 17), (12, 18), (13, 18), (14, 18), (13, 19)], SWEAT); cv.put(12, 18, SWEAT_HI)
    return cv


# ==========================================================================
# BUS  (battle-only prop layer: the camper bus behind him, blowing bubbles)
# ==========================================================================
BUSW, BUSH = 204, 124
BUS_ANCHOR = (96, BUSH - 1)       # his battle foot point inside this image


def rrect(cv, x0, y0, x1, y1, rtl, rtr, rbr, rbl):
    m = cv.rect(x0, y0, x1, y1)
    for (cx, cy, r, sx, sy) in ((x0 + rtl, y0 + rtl, rtl, -1, -1), (x1 - rtr, y0 + rtr, rtr, 1, -1),
                                (x1 - rbr, y1 - rbr, rbr, 1, 1), (x0 + rbl, y1 - rbl, rbl, -1, 1)):
        if r <= 0:
            continue
        corner = ((cv.X - cx) * sx > 0) & ((cv.Y - cy) * sy > 0)
        m &= ~corner | cv.ell(cx, cy, r, r)
    return m


def bus():
    cv = Cv(BUSW, BUSH)
    x0, x1, top, bot = 20, 184, 36, 103
    belt = 72
    body = rrect(cv, x0, top, x1, bot, 13, 20, 9, 7)
    # two-tone: cream up top, teal below, the cream dipping into a V at the nose
    vline = belt + np.clip((cv.X - 158) * 0.55, 0, 99)
    upper = body & (cv.Y < vline)
    lower = body & ~upper
    lvu = np.where(upper, 3, 0) + np.where(upper & (cv.Y < top + 4), 1, 0) - np.where(upper & (cv.X > x1 - 6), 1, 0)
    cv.part("upper", upper, "cream", edge="dark", lv=lvu)
    lvl = np.where(lower, 2, 0) + np.where(lower & (cv.Y < belt + 4), 1, 0) - np.where(lower & (cv.Y > bot - 6), 1, 0)
    cv.part("lower", lower, "teal", edge="dark", noedge=("upper",), lv=lvl)
    # chrome belt trim along the colour split
    for x in range(x0 + 2, x1 - 1):
        y = int(round(belt + max(0, (x - 158) * 0.55)))
        if cv.own[y, x] in (cv.names["upper"], cv.names["lower"]):
            cv.put(x, y, RAMP["metal"][3])
    # skylights (a row of little roof windows) and side windows
    gl = RAMP["glass"]
    tc = RAMP["teal"]

    def window(name, wx0, wy0, wx1, wy1, r=2, curtain=False, seed=0):
        m = rrect(cv, wx0, wy0, wx1, wy1, r, r, r, r)
        lv = np.where(m, 2, 0) + np.where(m & (cv.Y < wy0 + (wy1 - wy0) * 0.4), 1, 0)
        # diagonal glare streak
        lv = np.where(m & (np.abs((cv.X - wx0) - (cv.Y - wy0) * 0.9 - (wx1 - wx0) * 0.35) < 1.2), 4, lv)
        cv.part(name, m, "glass", edge="ink", lv=lv)
        if curtain:
            cm = m & ((cv.X < wx0 + 3.5) | (cv.X > wx1 - 3.5)) & ~cv.rect(wx0, wy0, wx1, wy0)
            tiedye(cv, name + "c", cm, (wx0 + wx1) / 2, wy0 - 4, k=0.8, rad=2, soft=0.6, noedge=(name,), core=False)
    for i, sx in enumerate(range(36, 150, 14)):
        window("sky%d" % i, sx, top + 3, sx + 8, top + 6, r=1)
    for i, (wx0, wx1, cur) in enumerate(((32, 54, True), (58, 80, False), (84, 106, True), (110, 132, False), (136, 156, True))):
        window("win%d" % i, wx0, 46, wx1, 62, r=3, curtain=cur, seed=i)
    ws = cv.poly([(162, 45), (178, 45), (182, 63), (162, 63)]) & body
    cv.part("windshield", ws, "glass", edge="ink", lv=np.where(ws, 3, 0) + np.where(ws & (cv.X > 172), -1, 0))
    for y in range(46, 63):
        x = int(166 + (y - 46) * 0.3)
        if cv.own[y, x] == cv.names["windshield"]:
            cv.put(x, y, gl[4])
    # door seams + handle
    for x in (82, 108):
        for y in range(45, bot - 3):
            if cv.own[y, x] in (cv.names["upper"], cv.names["lower"]):
                cv.put(x, y, RAMP["cream"][1] if y < belt else tc[0])
    cv.hline(102, 105, belt + 4, RAMP["metal"][4]); cv.hline(102, 105, belt + 5, RAMP["metal"][1])
    # bumpers + headlight + tail light
    fb = rrect(cv, 172, 94, 190, 99, 2, 2, 2, 2)
    cv.part("fbump", fb, "metal", edge="ink", lv=np.where(fb, 3, 0) - np.where(fb & (cv.Y > 97), 1, 0))
    rb = rrect(cv, 14, 94, 28, 99, 2, 2, 2, 2)
    cv.part("rbump", rb, "metal", edge="ink", lv=np.where(rb, 3, 0) - np.where(rb & (cv.Y > 97), 1, 0))
    hl = cv.ell(183, 78, 2.6, 4.0)
    cv.part("headlight", hl, "cream", edge="ink", lv=np.where(hl, 4, 0) - np.where(hl & (cv.Y > 79), 1, 0))
    tl = cv.rect(20, 76, 22, 82)
    cv.part("tail", tl, "orange", edge="ink", lv=np.where(tl, 3, 0))
    # wheel arches, tyres, cream hubcaps
    for i, wx in enumerate((50, 148)):
        arch = cv.ell(wx, 103, 14.5, 14.5) & body
        cv.part("arch%d" % i, arch, "tyre", edge="ink", noedge=("lower",), lv=np.where(arch, 1, 0))
        tyre = cv.ell(wx, 102.5, 11.5, 11.5)
        cv.part("tyre%d" % i, tyre, "tyre", edge="ink", lv=cv.levels(tyre, rad=6, soft=1.0, cuts=(0.4, 0.7, 0.95)))
        hub = cv.ell(wx, 102.5, 6, 6)
        cv.part("hub%d" % i, hub, "cream", edge="dark", lv=cv.levels(hub, rad=4, soft=0.8, cuts=(0.3, 0.55, 0.85)))
        cv.part("cap%d" % i, cv.ell(wx, 102.5, 2.2, 2.2), "metal", edge="dark", lv=np.where(cv.ell(wx, 102.5, 2.2, 2.2), 3, 0))
    # painted daisies on the lower panel + a big peace sign on the nose
    for (fx, fy, r) in ((70, 86, 5.0), (96, 90, 3.6), (124, 85, 5.4), (35, 88, 3.4)):
        for i in range(8):
            a = i * math.pi / 4 + 0.2
            pm = cv.ell(fx + math.cos(a) * r * 0.75, fy + math.sin(a) * r * 0.75, r * 0.42, r * 0.42) & body
            cv.part("dp%d_%d" % (fx, i), pm, "petal", edge=None, lv=np.where(pm, 3, 0))
        ctr = cv.ell(fx, fy, r * 0.38, r * 0.38)
        cv.part("dc%d" % fx, ctr, "sun", edge=None, lv=np.where(ctr, 3, 0))
    px, py = 168, 85
    ring = cv.ell(px, py, 6.2, 6.2) & ~cv.ell(px, py, 4.6, 4.6)
    legs = cv.capsule(px, py - 5.5, px, py + 5.5, 0.7) | cv.capsule(px, py, px - 4.2, py + 4.2, 0.7) | cv.capsule(px, py, px + 4.2, py + 4.2, 0.7)
    pm = (ring | (legs & cv.ell(px, py, 5.4, 5.4))) & body
    cv.part("peace", pm, "petal", edge=None, lv=np.where(pm, 4, 0))
    # roof rack + the bubble machine
    rack = cv.rect(40, 31, 150, 32) | cv.rect(44, 31, 45, 35) | cv.rect(96, 31, 97, 35) | cv.rect(146, 31, 147, 35)
    cv.part("rack", rack, "metal", edge=None, lv=np.where(rack, 2, 0) + np.where(rack & (cv.Y == 31), 1, 0))
    box = rrect(cv, 112, 20, 132, 31, 2, 2, 0, 0)
    cv.part("machine", box, "orange", edge="ink", lv=np.where(box, 3, 0) - np.where(box & (cv.X > 126), 1, 0) + np.where(box & (cv.Y < 22), 1, 0))
    fan = cv.ell(118, 25.5, 3.2, 3.2)
    cv.part("fan", fan, "metal", edge="ink", lv=np.where(fan, 2, 0) + np.where(fan & (cv.X < 118) & (cv.Y < 25.5), 1, 0))
    wand = cv.capsule(110, 25, 104, 22, 0.8) | cv.ell(102, 21, 2.4, 2.4) & ~cv.ell(102, 21, 1.2, 1.2)
    cv.part("wand", wand, "sun", edge="dark", lv=np.where(wand, 3, 0))
    # flower-power lettering stripe: a rainbow pinstripe along the upper body
    for j, hue in enumerate(HUES):
        y = 66 + j
        for x in range(30, 156):
            if cv.own[y, x] == cv.names["upper"]:
                cv.put(x, y, hue[2] if (x // 2) % 6 else hue[3])
    cv.outline()
    # bubbles: out of the machine, drifting up and back over the roof, and out of a window
    rng = np.random.default_rng(7)
    for (bx, by, r) in ((96, 16, 4), (86, 9, 3), (74, 14, 5), (60, 6, 3), (48, 16, 2), (40, 7, 4), (26, 18, 3),
                        (14, 10, 2), (108, 8, 2), (66, 24, 2), (30, 28, 2), (126, 10, 3), (140, 18, 2), (152, 6, 4),
                        (168, 22, 3), (184, 12, 2), (8, 30, 3), (194, 34, 2), (6, 52, 2), (192, 56, 3)):
        bubble(cv, bx, by, r)
    return cv


# ==========================================================================
# output
# ==========================================================================
CAST_REF = "/tmp/claude-0/designs/cast-reference.png"   # 3x contact sheet of the approved cast


def foot_point(cv):
    """x = centre between the sandals on the sole row, y = sole row."""
    y = cv.h - 1
    shoe_ids = [pid for n, pid in cv.names.items() if n.startswith("shoe")]
    xs = [x for x in range(cv.w) if cv.alpha[y, x] and cv.own[y, x] in shoe_ids]
    if not xs:
        xs = [x for x in range(cv.w) if cv.alpha[y, x]]
    return [int(round((min(xs) + max(xs)) / 2)), y]


def check_height(img, want, name):
    a = np.array(img)[..., 3] > 0
    rows = np.nonzero(a.any(axis=1))[0]
    assert rows[-1] == img.height - 1, (name, "feet not on bottom row")
    assert img.height - rows[0] == want, (name, "height", img.height - rows[0])


def diff_box(a, b):
    d = np.any(np.array(a) != np.array(b), axis=2)
    ys, xs = np.nonzero(d)
    if len(xs) == 0:
        return None, 0
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), int(d.sum())


def build():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(os.path.join(OUT, "talk"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "idle"), exist_ok=True)
    feet, cells = {}, {}
    battle = [front("idle"), front("talk"), front("tell"), front("hit"), side(), back()]
    world = [front("idle", KW), front("talk", KW), front("tell", KW), front("hit", KW), side(KW), back(KW)]
    for prefix, group, hgt in (("battle", battle, BODY_H), ("world", world, WORLD_H)):
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            check_height(img, hgt, name)
            img.save(os.path.join(OUT, name))
            feet[name] = foot_point(cv)
            cells[name] = img
    ent = entrance()
    img = ent.image()
    assert np.array(img)[-1, :, 3].any(), "entrance feet"
    img.save(os.path.join(OUT, "entrance.png"))
    feet["entrance.png"] = foot_point(ent)
    cells["entrance.png"] = img
    for i, e in enumerate(EXPRS):
        img = portrait(e).image()
        img.save(os.path.join(OUT, "portrait-%d.png" % i))
        cells["portrait-%d.png" % i] = img
        t_img = portrait(e, talk=True).image()
        box, n = diff_box(img, t_img)
        assert box and box[1] >= 36 and box[3] <= 48, ("talk diff outside the mouth", e, box)
        t_img.save(os.path.join(OUT, "talk", "sunbeam-%d.png" % i))
        cells["talk-%d.png" % i] = t_img
        print("talk", i, "changed", n, "px in", box)
    base = cells["world-0.png"]
    for key, extra in (("blink", "blink"), ("pose1", "strum"), ("pose2", "peace")):
        img = front("idle", KW, extra).image()
        assert img.size == base.size
        box, n = diff_box(base, img)
        print("idle", key, "changed", n, "px in", box)
        img.save(os.path.join(OUT, "idle", "sunbeam-%s.png" % key))
        cells["idle-%s.png" % key] = img
    # battle-only prop layer: the bus behind him
    b = bus().image()
    b.save(os.path.join(OUT, "sunbeam-bus.png"))
    cells["bus"] = b
    with open(os.path.join(OUT, "sunbeam-bus.json"), "w", newline="\r\n") as fh:
        fh.write(json.dumps({"path": "sunbeam-bus.png", "size": list(b.size), "anchor": list(BUS_ANCHOR),
                             "anchor_is": "Sunbeam's battle foot point (cells 0-5) in this image", "z": "behind",
                             "battle_only": True}, indent=1) + "\n")
    with open(os.path.join(OUT, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    contact_sheet(cells, feet)
    return cells, feet


def contact_sheet(cells, feet, S=3):
    """3x sheet: battle row (+ entrance, + Sunbeam in front of his bus), world row (+ idle extras),
    portrait row (+ talk), each beside the cast crops from the 3x cast reference."""
    from PIL import ImageFont
    BG = (44, 44, 62, 255)
    GROUND = (70, 70, 96, 255)
    font = ImageFont.load_default()
    ref = Image.open(CAST_REF).convert("RGBA") if os.path.exists(CAST_REF) else None

    def up(im):
        return im.resize((im.width * S, im.height * S), Image.NEAREST)

    combo = cells["bus"].copy()
    lf = feet["battle-0.png"]
    combo.alpha_composite(cells["battle-0.png"], (BUS_ANCHOR[0] - lf[0], BUS_ANCHOR[1] - lf[1]))
    r1 = [(up(cells["battle-%d.png" % i]), "battle-%d" % i) for i in range(6)]
    r1.append((up(cells["entrance.png"]), "cell 12 sunbeam-entrance"))
    r1.append((up(combo), "battle-0 + sunbeam-bus.png"))
    if ref is not None:
        r1.append((ref.crop((1440, 40, 1848, 285)), "cast: dev 80, jakerson 80"))
    r2 = [(up(cells["world-%d.png" % i]), "world-%d" % i) for i in range(6)]
    r2 += [(up(cells["idle-%s.png" % k]), "idle " + k) for k in ("blink", "pose1", "pose2")]
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
    d.text((pad, 6), "Sunbeam, jam-band frontman (sunbeam) -- 3x; cast crops from designs/cast-reference.png at the same 3x",
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
    cells, feet = build()
    for k, v in feet.items():
        print(k, cells[k].size, v)
