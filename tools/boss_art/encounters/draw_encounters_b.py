#!/usr/bin/env python3
"""Random-encounter cast, batch B (business_major, engineering_major, philosophy_major, frisbee) --
procedural pixel-art sprites for "After Hours - College Tale".

ONE script draws all four ids (run it with an id, or with no argument for all four plus the lineup).
The raster engine (class Cv) is copied verbatim from Professor Eric's draw_eric.py (via sunbeam):
parts are masks shaded with material ramps from a top-left key light, given inner 1px lines and an
ink silhouette.  Everything is drawn at its final pixel size; nothing drawn is ever resampled (only
the contact sheets and private previews are nearest-neighbour blow-ups).

These are low-key route trainers, not gym leaders: everyday clothes, one clear prop each.
  business_major     Priya-ish go-getter: burgundy blazer, sleek high ponytail, giant iced coffee
  engineering_major  stocky, deep-brown skin, short twists + chinstrap beard, thick black glasses,
                     CU-gold hoodie, carries a little tread robot he built
  philosophy_major   lanky, pale + freckled, ginger curls under a black beret, round wire glasses,
                     camel coat over a black turtleneck, a doorstop of a book
  frisbee            ultimate player: big curly puff + white sweatband, lime jersey #7, black shorts,
                     tall striped socks, hot-pink disc

Per id, outputs in /tmp/claude-0/newcast/<id>/out/ (Eric's layout, NO entrance cell):
  battle-0..5.png   battle cells (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  world-0..5.png    world cells (same poses, redrawn small)
  portrait-0..3.png 64x64 portraits (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk/<id>-0..3.png   mouth-open portraits (only mouth pixels differ)
  idle/<id>-blink.png, <id>-pose1.png, <id>-pose2.png   world-front extras
  feet.json         foot point [x, y] for every body cell
then build_sheet.py packs <id>-v1.png + <id>-atlas.json + out/world/.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

NEWCAST = "/tmp/claude-0/newcast"
IDS = ("business_major", "engineering_major", "philosophy_major", "frisbee")

# --------------------------------------------------------------------------
# palette (shared)
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline (same ink as the cast)
RAMP = {
    "metal":  [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "gold":   [(92, 62, 18), (160, 116, 36), (206, 166, 64), (236, 204, 104), (252, 236, 160)],
    "white":  [(120, 120, 140), (196, 198, 212), (226, 228, 236), (244, 244, 248), (255, 255, 255)],
    "paper":  [(120, 104, 80), (200, 186, 156), (232, 222, 196), (246, 240, 222), (255, 252, 240)],
    "coffee": [(40, 20, 10), (92, 52, 26), (132, 80, 42), (170, 116, 70), (206, 160, 112)],
    "cupclr": [(110, 130, 150), (176, 200, 216), (214, 232, 242), (236, 246, 252), (255, 255, 255)],
    "straw":  [(10, 70, 40), (30, 140, 80), (60, 190, 110), (120, 226, 150), (190, 246, 200)],
    "phone":  [(14, 14, 20), (30, 30, 40), (46, 46, 60), (70, 70, 88), (110, 110, 130)],
    "robot":  [(70, 76, 92), (140, 148, 166), (186, 194, 208), (222, 228, 236), (248, 250, 252)],
    "tread":  [(16, 16, 20), (34, 34, 42), (52, 52, 62), (76, 76, 88), (104, 104, 118)],
    "book":   [(14, 40, 30), (28, 76, 56), (44, 108, 80), (70, 140, 104), (110, 176, 140)],
    "disc":   [(100, 10, 60), (186, 30, 110), (232, 60, 150), (250, 110, 186), (255, 176, 220)],
    "lens":   [(150, 180, 200), (190, 214, 230), (214, 232, 244), (232, 244, 252), (250, 254, 255)],
}
RIM = (255, 170, 80)
EYE = (34, 22, 24)
WHITE = (250, 248, 244)
SCLERA = (240, 236, 230)
MOUTH = (98, 34, 28)
TONGUE = (214, 104, 100)
TEETH = (250, 246, 236)
SWEAT = (120, 196, 240)
SWEAT_HI = (220, 244, 255)
SPARK = (255, 240, 170)
SPARK2 = (255, 200, 80)
LEDC = (90, 236, 250)
LEDR = (255, 80, 70)
FRAME = (22, 20, 28)

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



# ==========================================================================
# CHARACTERS
# ==========================================================================
CHARS = {
    "business_major": dict(
        title="Business major", hb=76, hw=51, build=0.92, fem=True, ears=True,
        skin=[(112, 62, 50), (196, 138, 110), (228, 178, 146), (244, 206, 176), (252, 228, 204)],
        hair=[(14, 12, 18), (32, 26, 34), (52, 44, 54), (78, 68, 82), (116, 106, 124)],
        iris=(96, 56, 36), iris_d=(44, 24, 16), lip=(184, 70, 86), blush=(236, 140, 130),
        top=[(52, 14, 30), (104, 30, 58), (140, 46, 78), (176, 72, 104), (206, 110, 138)],     # burgundy blazer
        pants=[(20, 20, 28), (40, 40, 52), (58, 58, 72), (80, 80, 96), (110, 110, 126)],
        shoe=[(12, 10, 14), (30, 26, 32), (46, 40, 48), (68, 60, 72), (98, 90, 102)],
        hair_style="ponytail", top_style="blazer", legs_style="trousers", shoe_style="flats",
        facew=7.0, arm_r=2.4),
    "engineering_major": dict(
        title="Engineering major", hb=75, hw=50, build=1.18, fem=False, ears=True,
        skin=[(34, 18, 14), (78, 44, 30), (108, 64, 44), (138, 90, 62), (168, 122, 88)],
        hair=[(8, 6, 8), (20, 16, 18), (34, 28, 30), (56, 48, 50), (84, 74, 76)],
        iris=(70, 40, 24), iris_d=(20, 10, 6), lip=(92, 48, 40), blush=None,
        top=[(88, 60, 16), (164, 124, 46), (210, 174, 88), (234, 206, 128), (248, 230, 172)],   # CU-gold hoodie
        pants=[(30, 34, 22), (56, 62, 40), (78, 86, 56), (102, 110, 74), (130, 138, 98)],
        shoe=[(70, 72, 84), (140, 144, 156), (186, 190, 200), (220, 222, 230), (244, 246, 250)],
        hair_style="twists", top_style="hoodie", legs_style="cargo", shoe_style="sneakers",
        facew=7.6, arm_r=3.0),
    "philosophy_major": dict(
        title="Philosophy major", hb=78, hw=52, build=0.84, fem=False, ears=False,
        skin=[(120, 64, 56), (208, 150, 134), (238, 192, 172), (250, 216, 198), (255, 236, 222)],
        hair=[(96, 34, 14), (160, 64, 24), (206, 98, 40), (234, 136, 64), (250, 180, 110)],
        iris=(78, 140, 74), iris_d=(30, 72, 38), lip=(190, 104, 96), blush=None,
        top=[(80, 52, 26), (140, 98, 54), (180, 136, 82), (210, 170, 112), (234, 204, 152)],    # camel coat
        under=[(10, 8, 12), (24, 22, 28), (38, 36, 44), (56, 54, 64), (82, 80, 92)],          # black turtleneck
        pants=[(30, 22, 18), (56, 42, 32), (78, 60, 46), (102, 82, 64), (130, 108, 88)],
        shoe=[(40, 20, 10), (84, 46, 22), (118, 70, 36), (152, 98, 56), (188, 136, 88)],
        beret=[(10, 8, 12), (26, 22, 28), (40, 36, 44), (60, 56, 66), (88, 84, 96)],
        hair_style="beret", top_style="coat", legs_style="trousers", shoe_style="boots",
        facew=6.8, arm_r=2.6),
    "frisbee": dict(
        title="Frisbee", hb=70, hw=47, build=1.0, fem=True, ears=True,
        skin=[(64, 34, 22), (132, 80, 50), (170, 112, 72), (200, 144, 98), (224, 178, 130)],
        hair=[(18, 10, 6), (42, 26, 16), (68, 42, 26), (98, 64, 40), (132, 94, 62)],
        iris=(90, 54, 28), iris_d=(34, 18, 8), lip=(150, 76, 64), blush=(196, 104, 84),
        top=[(28, 70, 20), (64, 140, 40), (112, 192, 60), (160, 224, 96), (212, 246, 160)],      # lime jersey
        pants=[(14, 14, 18), (30, 30, 38), (44, 44, 54), (64, 64, 78), (92, 92, 108)],
        sock=[(120, 120, 140), (196, 198, 212), (226, 228, 236), (244, 244, 248), (255, 255, 255)],
        shoe=[(12, 10, 14), (30, 26, 32), (46, 40, 48), (68, 60, 72), (98, 90, 102)],
        hair_style="puff", top_style="jersey", legs_style="shorts", shoe_style="cleats",
        facew=7.0, arm_r=2.2),
}

BCW = 80            # battle canvas width (Eric is 76; props need a little more room)
WCW = 56            # world canvas width
BTOP, WTOP = 8, 4   # space above the head (hair puffs, effects)
WHK = 0.62          # world head scale (Sunbeam's 52/82)


class G:
    """Geometry for one cell.  Head features use head units (1 px in battle); the body below the
    shoulders (unit 22) is stretched so the soles (unit 81) land on the bottom row."""

    def __init__(self, ch, battle, cshift=0):
        self.battle = battle
        self.hk = 1.0 if battle else WHK
        H = ch["hb"] if battle else ch["hw"]
        self.t = BTOP if battle else WTOP
        self.CW = BCW if battle else WCW
        self.CH = self.t + H
        self.c = self.CW // 2 + cshift
        self.top_body = self.t + 22 * self.hk
        self.bk = (self.CH - 1 - self.top_body) / 59.0
        self.wk = self.hk * ch["build"]

    def X(self, dx):
        return self.c + dx * self.wk

    def Y(self, u):
        return self.t + u * self.hk if u <= 22 else self.top_body + (u - 22) * self.bk

    def Q(self, dx, u):
        return (self.X(dx), self.Y(u))

    def Hh(self, dx, dy):
        return (self.c + dx * self.hk, self.t + dy * self.hk)


def ipt(p):
    return int(round(p[0])), int(round(p[1]))


# ==========================================================================
# small parts
# ==========================================================================
def hand(cv, g, ch, x, y, name, r=2.3):
    rr = max(1.5, r * g.wk if g.battle else r * g.hk * 1.05)
    m = cv.ell(x, y, rr, rr)
    cv.part(name, m, ch["skin"], edge="ink", rad=2.5, soft=0.7, bias=0.05)
    return m


def open_hand(cv, g, ch, x, y, name):
    if g.battle:
        m = cv.ell(x, y, 2.4, 3.0) | cv.capsule(x + 1.9, y + 1.0, x + 3.4, y - 0.6, 0.95)
        cv.part(name, m, ch["skin"], edge="ink", rad=2.5, soft=0.7, bias=0.08)
        for fx in (x - 1, x + 1):
            cv.vline(int(round(fx)), int(round(y - 2.6)), int(round(y - 1)), ch["skin"][1])
    else:
        m = cv.ell(x, y, 1.6, 2.0) | cv.capsule(x + 1.2, y + 0.6, x + 2.2, y - 0.5, 0.65)
        cv.part(name, m, ch["skin"], edge="ink", lv=np.where(m, 3, 0))
    return m


def point_hand(cv, g, ch, x, y, name, dx=0.0, dy=-1.0):
    """Fist with the index finger out along (dx, dy)."""
    L = 4.2 if g.battle else 2.8
    r = 2.1 if g.battle else 1.4
    m = cv.ell(x, y, r, r) | cv.capsule(x, y, x + dx * L, y + dy * L, 0.9 if g.battle else 0.6)
    cv.part(name, m, ch["skin"], edge="ink", rad=2.0, soft=0.7, bias=0.08)
    return m


def sleeve_arm(cv, g, ch, name, pts, ramp=None, r=None):
    rr = max(1.55, (r or ch["arm_r"]) * g.wk)
    m = cv.chain(pts, rr)
    cv.part(name, m, ramp or ch["top"], edge="ink", rad=max(2, 3 * g.wk), soft=0.8,
            cuts=(0.28, 0.52, 0.86), bias=0.04)
    return m


def bare_arm(cv, g, ch, name, pts):
    """Frisbee: bare arm with the jersey's short sleeve cap."""
    k = g.wk
    r = max(1.4, ch["arm_r"] * k)
    m = cv.chain(pts, r)
    cv.part(name, m, ch["skin"], edge="dark", rad=max(2, 3 * k), soft=0.8, cuts=(0.28, 0.52, 0.86), bias=0.04)
    (x0, y0), (x1, y1) = pts[0], pts[1]
    f = 0.45
    sl = cv.capsule(x0, y0, x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, max(2.0, 3.2 * k), max(1.8, 2.9 * k))
    cv.part(name + "sl", sl, ch["top"], edge="dark", noedge=("shirt",), rad=3, soft=0.8, cuts=(0.30, 0.55, 0.88))
    return m


def arm(cv, g, ch, name, pts):
    if ch["top_style"] == "jersey":
        return bare_arm(cv, g, ch, name, pts)
    return sleeve_arm(cv, g, ch, name, pts)


def sparkle(cv, x, y, big=False):
    cv.put(x, y, WHITE)
    for d in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        cv.put(x + d[0], y + d[1], SPARK)
    if big:
        for d in ((2, 0), (-2, 0), (0, 2), (0, -2)):
            cv.put(x + d[0], y + d[1], SPARK2)


def sweat(cv, x, y, battle=True):
    if battle:
        cv.puts([(x, y), (x - 1, y + 1), (x, y + 1), (x + 1, y + 1), (x, y + 2)], SWEAT)
        cv.put(x - 1, y + 1, SWEAT_HI)
    else:
        cv.puts([(x, y), (x, y + 1), (x - 1, y + 1)], SWEAT)


# ==========================================================================
# PROPS
# ==========================================================================
def _local(cv, x, y, ang, s):
    ca, sa = math.cos(ang), math.sin(ang)
    U = ((cv.X - x) * ca + (cv.Y - y) * sa) / s
    V = (-(cv.X - x) * sa + (cv.Y - y) * ca) / s
    P = lambda u, v: (x + (u * ca - v * sa) * s, y + (u * sa + v * ca) * s)
    return U, V, P


def coffee(cv, x, y, s=1.0, ang=0.0, name="cup"):
    """Giant iced coffee: clear cup, coffee with a milky top, domed lid, green straw.
    (x, y) = where the hand grips it."""
    U, V, P = _local(cv, x, y, ang, s)
    straw = cv.capsule(*P(0.8, -7.4), *P(2.4, -12.4), max(0.6, 0.75 * s))
    cv.part(name + "straw", straw, "straw", edge="dark", lv=np.where(straw, 3, 0))
    body = cv.poly([P(-3.6, -6.2), P(3.6, -6.2), P(2.7, 5.0), P(-2.7, 5.0)])
    lv = np.where(body, 2, 0) + np.where(body & (U < -0.8), 1, 0) - np.where(body & (U > 1.8), 1, 0)
    lv = np.where(body & (V < -3.6), 4, lv)          # cream/ice band at the top
    cv.part(name, body, "coffee", edge=RAMP["cupclr"][0], lv=lv)
    if s >= 0.8:
        cr = RAMP["cupclr"]
        for (u, v) in ((-1.6, -2.0), (1.0, -1.0), (-0.6, 1.4)):          # ice cubes
            px, py = ipt(P(u, v))
            cv.put(px, py, cr[3]); cv.put(px + 1, py, cr[2])
        for v in range(-5, 4):
            px, py = ipt(P(-2.4 + v * -0.07, v))
            if cv.own[py, px] == cv.names[name]:
                cv.put(px, py, mix(cv.get(px, py), cr[4], 0.55))             # plastic glare stripe
    lid = cv.ell(*P(0, -6.6), 4.0 * s, max(1.0, 1.4 * s), ang)
    cv.part(name + "lid", lid, "cupclr", edge="dark", lv=np.where(lid, 3, 0) + np.where(lid & (V < -6.8), 1, 0))
    return body


def phone(cv, x, y, s=1.0, name="phone", glow=True):
    w, h = max(1.5, 2.2 * s), max(2.2, 3.4 * s)
    m = cv.rect(x - w, y - h, x + w, y + h)
    cv.part(name, m, "phone", edge="ink", lv=np.where(m, 2, 0))
    if glow:
        sc = cv.rect(x - w + 1, y - h + 1, x + w - 1, y + h - 1) & m
        cv.col[sc & cv.alpha] = (120, 200, 250)
        if s >= 0.8:
            cv.put(int(round(x - w + 1)), int(round(y - h + 1)), (220, 244, 255))
    return m


def robot(cv, x, y, s=1.0, mood="ok", name="bot"):
    """His little tread robot.  (x, y) = centre of its chassis."""
    small = s < 0.8
    tr = cv.rect(x - 6.2 * s, y + 3.0 * s, x + 6.2 * s, y + 6.4 * s) | cv.ell(x - 5.6 * s, y + 4.7 * s, 1.7 * s, 1.7 * s) \
        | cv.ell(x + 5.6 * s, y + 4.7 * s, 1.7 * s, 1.7 * s)
    cv.part(name + "tread", tr, "tread", edge="ink", lv=np.where(tr, 2, 0) + np.where(tr & (cv.Y < y + 4.0 * s), 1, 0))
    if not small:
        for i in range(-4, 5, 2):
            cv.put(int(round(x + i * s)), int(round(y + 5.0 * s)), RAMP["metal"][1])
    body = cv.rect(x - 5.0 * s, y - 3.6 * s, x + 5.0 * s, y + 3.4 * s)
    cv.part(name, body, "robot", edge="ink", lv=cv.levels(body, rad=3 * s + 1, soft=0.8, cuts=(0.28, 0.55, 0.88)))
    neck = cv.rect(x - 1.0 * s, y - 5.0 * s, x + 1.0 * s, y - 3.6 * s)
    cv.part(name + "neck", neck, "metal", edge="ink", lv=np.where(neck, 1, 0))
    ax, ay = x + (1.6 if mood == "hit" else 0.8) * s, y - 13.2 * s
    if mood == "hit":
        cv.line(int(round(x)), int(round(y - 10.4 * s)), int(round(x + 2 * s)), int(round(y - 12 * s)), RAMP["metal"][1])
        cv.line(int(round(x + 2 * s)), int(round(y - 12 * s)), int(round(x + 4.2 * s)), int(round(y - 11.4 * s)), RAMP["metal"][1])
        ax, ay = x + 4.8 * s, y - 11.4 * s
    else:
        cv.line(int(round(x)), int(round(y - 10.4 * s)), int(round(ax)), int(round(ay + 1)), RAMP["metal"][1])
    ball = cv.ell(ax, ay, max(0.9, 1.2 * s), max(0.9, 1.2 * s))
    cv.part(name + "ball", ball, [(120, 20, 20), (190, 40, 36), (240, 70, 60), (255, 120, 100), (255, 190, 170)],
            edge="dark", lv=np.where(ball, 3, 0))
    head = cv.rect(x - 4.2 * s, y - 10.6 * s, x + 4.2 * s, y - 4.8 * s)
    cv.part(name + "head", head, "robot", edge="ink", lv=cv.levels(head, rad=2.5 * s + 1, soft=0.8, cuts=(0.28, 0.55, 0.88)))
    scr = cv.rect(x - 3.2 * s, y - 9.6 * s, x + 3.2 * s, y - 5.8 * s)
    cv.part(name + "scr", scr, "phone", edge="ink", lv=np.where(scr, 1, 0))
    ec = LEDR if mood in ("angry", "hit") else LEDC
    ey = int(round(y - 7.8 * s))
    if mood == "hit":
        for sx in (-1, 1):
            ex = int(round(x + sx * 1.6 * s))
            cv.put(ex, ey, ec); cv.put(ex - 1, ey - 1, ec) if not small else None; cv.put(ex + 1, ey + 1, ec) if not small else None
    elif mood == "angry" and not small:
        for sx in (-1, 1):
            ex = int(round(x + sx * 1.6 * s))
            cv.put(ex, ey, ec); cv.put(ex + sx, ey, ec); cv.put(ex - sx, ey - 1, ec)
    else:
        for sx in (-1, 1):
            ex = int(round(x + sx * 1.6 * s))
            cv.put(ex, ey, ec)
            if not small:
                cv.put(ex + (1 if sx > 0 else -1) * 0, ey - 1, ec)
    if not small:
        # a CU-gold bolt on the chest + a little speaker grille
        cv.puts([(int(round(x - 2)), int(round(y - 1))), (int(round(x - 1)), int(round(y - 1))),
                 (int(round(x - 2)), int(round(y))), (int(round(x - 1)), int(round(y)))], (207, 184, 124))
        for i in range(3):
            cv.put(int(round(x + 1 + i)), int(round(y + 1)), RAMP["robot"][1])
    return body | head


def book(cv, x, y, s=1.0, kind="closed", ang=0.0, name="book"):
    """kind closed: a fat upright hardback, pages showing on its right edge; open: spread pages."""
    U, V, P = _local(cv, x, y, ang, s)
    if kind == "closed":
        cov = cv.poly([P(-3.6, -5.6), P(2.4, -5.6), P(2.4, 5.6), P(-3.6, 5.6)])
        cv.part(name, cov, "book", edge="ink", lv=np.where(cov, 2, 0) + np.where(cov & (U < -1.6), 1, 0))
        pg = cv.poly([P(2.4, -5.2), P(4.6, -4.8), P(4.6, 5.2), P(2.4, 5.6)])
        cv.part(name + "pg", pg, "paper", edge="ink", lv=np.where(pg, 3, 0))
        if s >= 0.8:
            for v in (-3, -1, 1, 3):
                for u in (3.0, 3.8):
                    px, py = ipt(P(u, v))
                    cv.put(px, py, RAMP["paper"][1])
            for u in np.arange(-3.0, 2.2, 1.0):              # gold title bands
                for v in (-3.4, 3.2):
                    px, py = ipt(P(u, v))
                    cv.put(px, py, RAMP["gold"][3] if v < 0 else RAMP["gold"][2])
        else:
            px, py = ipt(P(-0.6, -3.0))
            cv.put(px, py, RAMP["gold"][3])
        return cov | pg
    # open
    cov = cv.poly([P(-7.6, -4.4), P(7.6, -4.4), P(7.6, 4.8), P(-7.6, 4.8)])
    cv.part(name, cov, "book", edge="ink", lv=np.where(cov, 2, 0))
    lp = cv.poly([P(-7.0, -5.0), P(-0.4, -3.8), P(-0.4, 4.0), P(-7.0, 3.6)])
    rp = cv.poly([P(0.4, -3.8), P(7.0, -5.0), P(7.0, 3.6), P(0.4, 4.0)])
    cv.part(name + "L", lp, "paper", edge="dark", lv=np.where(lp, 4, 0) - np.where(lp & (U > -2), 1, 0))
    cv.part(name + "R", rp, "paper", edge="dark", lv=np.where(rp, 3, 0))
    if s >= 0.8:
        for v in (-2, 0, 2):
            for u in range(-6, -1):
                px, py = ipt(P(u, v - 0.1 * u))
                if cv.own[py, px] == cv.names[name + "L"]:
                    cv.put(px, py, RAMP["paper"][1])
            for u in range(2, 7):
                px, py = ipt(P(u, v + 0.1 * u - 1.0))
                if cv.own[py, px] == cv.names[name + "R"] and (u + v) % 4:
                    cv.put(px, py, RAMP["paper"][1])
    return cov


def disc(cv, x, y, s=1.0, ang=0.0, flat=1.0, name="disc"):
    rx, ry = max(2.6, 5.6 * s), max(1.2, min(5.6 * s, 2.2 * s * flat))
    m = cv.ell(x, y, rx, ry, ang)
    U, V, _ = _local(cv, x, y, ang, 1.0)
    lv = np.where(m, 2, 0) + np.where(m & (V < -0.2 * ry), 1, 0) - np.where(m & (V > 0.5 * ry), 1, 0)
    cv.part(name, m, "disc", edge="dark", lv=lv)
    if s >= 0.8:
        ring = cv.ell(x, y, rx - 2.2, max(0.6, ry - 1.0), ang) & ~cv.ell(x, y, rx - 3.2, max(0.4, ry - 1.6), ang)
        cv.col[ring & m] = RAMP["disc"][4]
    else:
        cv.put(int(round(x - rx * 0.4)), int(round(y - 0.4)), RAMP["disc"][4])
    return m


# ==========================================================================
# LEGS, TORSO
# ==========================================================================
def shoe(cv, g, ch, fx, s, name, side=False):
    small = not g.battle
    yb = g.CH - 1
    st = ch["shoe_style"]
    sr = ch["shoe"]
    hw = {"flats": 3.4, "sneakers": 4.3, "boots": 3.9, "cleats": 3.8}[st] * (0.66 if small else 1.0)
    hh = 1.6 if small else 2.5
    cx = fx + (1.7 if side else s * 0.4) * (0.66 if small else 1.0)
    if side:
        hw *= 1.15
    up = cv.ell(cx, yb - hh * 0.75, hw, hh) & (cv.Y <= yb)
    if st == "boots":
        up |= cv.rect(fx - (2.0 if small else 3.0), yb - (3.5 if small else 6.0), fx + (2.0 if small else 3.0), yb - 1)
    lv = np.where(up, 2, 0) + np.where(up & (cv.Y < yb - hh * 0.7), 1, 0)
    if st == "sneakers":
        lv = np.where(up & (cv.Y >= yb - (0 if small else 0.6)), 4, lv)
    cv.part(name, up, sr, edge="ink", lv=lv)
    if not small:
        if st == "sneakers":
            cv.hline(int(round(cx - hw + 2)), int(round(cx + hw - 2)), yb - 2, ch["top"][1])
        if st == "cleats":
            for x in range(int(round(cx - hw + 1)), int(round(cx + hw)), 2):
                cv.put(x, yb, RAMP["metal"][1])
            cv.hline(int(round(cx - 1)), int(round(cx + 1)), yb - 3, RAMP["disc"][2])
        if st == "flats":
            cv.hline(int(round(cx - 1)), int(round(cx + 1)), yb - 3, ch["skin"][2])     # instep
        if st == "boots":
            cv.put(int(round(cx - 1)), yb - 2, sr[3])


def legs_front(cv, g, ch, back=False):
    k = g.wk
    small = not g.battle
    st = ch["legs_style"]
    sk = ch["skin"]
    for s in (-1, 1):
        shoe(cv, g, ch, g.X(s * 5.2), s, "shoe%d" % s)
    for s in (-1, 1):
        x0, x1 = s * 4.6, s * 5.1
        if st == "shorts":
            leg = cv.capsule(*g.Q(x0, 52), *g.Q(x1, 77), 2.6 * k, 2.1 * k)
            cv.part("shin%d" % s, leg, sk, rad=2.5 * k + 0.4, soft=0.8, cuts=(0.28, 0.52, 0.86))
            sock = cv.capsule(*g.Q(x1, 67), *g.Q(x1, 77.5), 2.45 * k, 2.3 * k) & (cv.Y < g.CH - 2)
            cv.part("sock%d" % s, sock, ch["sock"], rad=2.4 * k, soft=0.6, cuts=(0.3, 0.55, 0.9))
            sid = cv.names["sock%d" % s]
            rows = (int(round(g.Y(68.6))), int(round(g.Y(70.4)))) if not small else (int(round(g.Y(69))),)
            for y in rows:
                for x in range(cv.w):
                    if cv.own[y, x] == sid and tuple(cv.col[y, x]) != ch["sock"][0]:
                        cv.put(x, y, RAMP["disc"][2])
        else:
            r0 = (3.7 if st == "cargo" else 3.5 if ch["fem"] else 3.2) * k
            leg = cv.capsule(*g.Q(x0, 46), *g.Q(x1, 75.5), r0, r0 * 0.88) & (cv.Y <= g.Y(77.4))
            cv.part("leg%d" % s, leg, ch["pants"], rad=r0 + 0.4, soft=0.8, cuts=(0.30, 0.55, 0.88),
                    tex=0.03 if g.battle else 0, seed=11 + s)
            if not small:
                if st == "cargo" and not back:
                    px, py = g.X(s * 7.4), g.Y(59)
                    pk = cv.rect(px - 2.2, py - 3, px + 2.2, py + 3) & leg
                    cv.part("pk%d" % s, pk, ch["pants"], edge="dark", noedge=("leg%d" % s,),
                            lv=np.where(pk, 2, 0) + np.where(pk & (cv.Y < py - 1.5), 1, 0))
                elif st == "trousers" and not back:
                    xm = int(round(g.X((x0 + x1) / 2)))
                    for y in range(int(g.Y(52)), int(g.Y(76))):
                        if cv.own[y, xm] == cv.names["leg%d" % s]:
                            cv.put(xm, y, ch["pants"][3] if s < 0 else ch["pants"][1])
    if st == "shorts":
        m = cv.poly([g.Q(-11.2, 44), g.Q(11.2, 44), g.Q(12.2, 57), g.Q(1.2, 57.5), g.Q(0, 53), g.Q(-1.2, 57.5), g.Q(-12.2, 57)])
        cv.part("shorts", m, ch["pants"], rad=4, soft=1.0, cuts=(0.30, 0.55, 0.88))
        if not small:
            for s in (-1, 1):
                x = int(round(g.X(s * 11.0)))
                for y in range(int(g.Y(47)), int(g.Y(56.5)) + 1):
                    if cv.own[y, x] == cv.names["shorts"]:
                        cv.put(x, y, ch["top"][2])


def torso_poly(g, style, back=False):
    if style == "hoodie":
        P = [(-6.5, 22), (6.5, 22), (11.5, 23.6), (13.2, 28.5), (12.6, 35), (13.6, 44), (12.6, 49.2),
             (-12.6, 49.2), (-13.6, 44), (-12.6, 35), (-13.2, 28.5), (-11.5, 23.6)]
    elif style == "blazer":
        P = [(-6, 22), (6, 22), (11, 24), (12.6, 28.5), (11, 35), (11.6, 44), (12.4, 51),
             (-12.4, 51), (-11.6, 44), (-11, 35), (-12.6, 28.5), (-11, 24)]
    elif style == "coat":
        P = [(-6, 22), (6, 22), (11, 24), (12.5, 28.5), (11.2, 35), (11.5, 47), (-11.5, 47), (-11.2, 35),
             (-12.5, 28.5), (-11, 24)]
    else:  # jersey
        P = [(-6, 22), (6, 22), (11, 24), (12.4, 28.5), (10.8, 35), (11.2, 46.5), (-11.2, 46.5), (-10.8, 35),
             (-12.4, 28.5), (-11, 24)]
    return [g.Q(x, u) for x, u in P]


GLYPH7 = ["#####", "....#", "...#.", "...#.", "..#..", "..#..", "..#.."]
GLYPH7S = ["###", "..#", ".#.", ".#."]


def glyph(cv, x, y, rows, col, shade=None):
    for j, row in enumerate(rows):
        for i, chh in enumerate(row):
            if chh == "#":
                cv.put(x + i, y + j, col)
                if shade is not None and (j + 1 >= len(rows) or rows[j + 1][i] != "#"):
                    pass


def torso_front(cv, g, ch, back=False):
    k = g.wk
    small = not g.battle
    st = ch["top_style"]
    sk, tp = ch["skin"], ch["top"]
    cv.part("neck", cv.rect(*g.Hh(-2.6, 16.5), *g.Hh(2.6, 23.5)), sk, rad=2, bias=-0.15)
    m = cv.poly(torso_poly(g, st))
    if st == "hoodie":
        m |= cv.ell(*g.Q(0, 41), 12.4 * k, 8.0 * g.bk)
    body_ramp = ch["under"] if st == "coat" else tp
    cv.part("shirt", m, body_ramp, rad=8 * k + 1, soft=1.4, cuts=(0.32, 0.6, 0.9), tex=0.03 if not small and st == "hoodie" else 0, seed=5)
    sid = cv.names["shirt"]
    if st == "blazer":
        if not back:
            shell = cv.poly([g.Q(-3.8, 22.2), g.Q(3.8, 22.2), g.Q(0, 35.5)])
            cv.part("shell", shell, "white", edge=None, lv=np.where(shell, 3, 0) - np.where(shell & (cv.X > g.c + 1), 1, 0))
            for s in (-1, 1):
                lap = cv.poly([g.Q(s * 3.8, 22.4), g.Q(s * 7.6, 23.4), g.Q(s * 5.2, 28.5), g.Q(s * 0.6, 35.2)])
                cv.part("lapel%d" % s, lap, tp, edge="dark", noedge=("shell",), lv=np.where(lap, 3 if s < 0 else 2, 0))
            if not small:
                bx, by = ipt(g.Q(0, 39))
                cv.put(bx, by, RAMP["gold"][3]); cv.put(bx, by + 1, RAMP["gold"][1])
                cv.line(bx - 1, by + 2, int(round(g.X(-2.5))), int(round(g.Y(50.6))), tp[0])
                cv.line(bx + 1, by + 2, int(round(g.X(2.5))), int(round(g.Y(50.6))), tp[0])
                for s in (-1, 1):
                    y = int(round(g.Y(45)))
                    cv.hline(int(round(g.X(s * 5))) if s < 0 else int(round(g.X(4))), int(round(g.X(-4))) if s < 0 else int(round(g.X(8))), y, tp[0])
                # lanyard-free pocket square: a gold fleck on the chest pocket
                px, py = ipt(g.Q(6.5, 31))
                cv.hline(px - 1, px + 1, py + 1, tp[0]); cv.put(px, py, RAMP["gold"][3]); cv.put(px - 1, py, RAMP["gold"][2])
            else:
                bx, by = ipt(g.Q(0, 38))
                cv.put(bx, by, RAMP["gold"][3])
        elif not small:
            cv.vline(int(round(g.c)), int(round(g.Y(42))), int(round(g.Y(51))), tp[0])
    elif st == "hoodie":
        if not back:
            hood = cv.ell(*g.Q(0, 23.0), 8.0 * k, 2.9 * g.hk + 0.4) & ~cv.ell(*g.Q(0, 22.0), 4.4 * k, 2.0 * g.hk)
            cv.part("hood", hood, tp, edge="dark", noedge=(), lv=np.where(hood, 2, 0) + np.where(hood & (cv.X < g.c - 2), 1, 0))
            pk = cv.poly([g.Q(-6.6, 38), g.Q(6.6, 38), g.Q(8.6, 46), g.Q(-8.6, 46)])
            cv.part("pocket", pk, tp, edge="dark", noedge=("shirt",), lv=np.where(pk, 2, 0) + np.where(pk & (cv.Y < g.Y(39.5)), 1, 0))
            if not small:
                for s in (-1, 1):
                    x0 = int(round(g.X(s * 2.2)))
                    cv.line(x0, int(round(g.Y(24.6))), x0 + s, int(round(g.Y(31))), RAMP["white"][3])
                    cv.put(x0 + s, int(round(g.Y(31))) + 1, FRAME)
            else:
                cv.put(int(round(g.X(-1.6))), int(round(g.Y(26))), RAMP["white"][3])
                cv.put(int(round(g.X(1.6))), int(round(g.Y(26))), RAMP["white"][3])
        else:
            hood = cv.ell(*g.Q(0, 27.0), 8.2 * k, 6.0 * g.bk) & (cv.Y > g.Y(22.4))
            cv.part("hood", hood, tp, edge="dark", lv=np.where(hood, 2, 0) + np.where(hood & (cv.Y < g.Y(25)), 1, 0))
            if not small:
                cv.hline(int(round(g.X(-3))), int(round(g.X(3))), int(round(g.Y(32.0))), tp[0])
        if not small:
            y0 = int(round(g.Y(47.6)))
            for y in range(y0, int(round(g.Y(49.2))) + 1):
                for x in range(cv.w):
                    if cv.own[y, x] == sid and x % 2 == 0 and tuple(cv.col[y, x]) != tp[0]:
                        cv.put(x, y, tp[1])
    elif st == "coat":
        un = ch["under"]
        if not back:
            tn = cv.rect(*g.Hh(-3.8, 18.6), *g.Hh(3.8, 23.4))
            cv.part("tneck", tn, un, rad=2, soft=0.6, cuts=(0.25, 0.5, 0.85), bias=0.1)
            if not small:
                for dy in (19.8, 21.6):
                    cv.hline(int(round(g.c - 3)), int(round(g.c + 3)), int(round(g.t + dy)), un[3] if dy < 21 else un[2])
        for s in (-1, 1) if not back else (0,):
            if back:
                pm = cv.poly([g.Q(-6.5, 22.5), g.Q(6.5, 22.5), g.Q(11, 24), g.Q(12.5, 28.5), g.Q(11.3, 35), g.Q(12, 47),
                              g.Q(13.8, 64), g.Q(-13.8, 64), g.Q(-12, 47), g.Q(-11.3, 35), g.Q(-12.5, 28.5), g.Q(-11, 24)])
            else:
                pm = cv.poly([g.Q(s * 6.4, 22.4), g.Q(s * 11, 24), g.Q(s * 12.5, 28.5), g.Q(s * 11.3, 35), g.Q(s * 12, 47),
                              g.Q(s * 13.8, 64), g.Q(s * 4.6, 64), g.Q(s * 3.0, 46), g.Q(s * 3.2, 30), g.Q(s * 4.0, 23.6)])
            cv.part("coat%d" % s, pm, tp, rad=6 * k + 1, soft=1.2, cuts=(0.30, 0.56, 0.88), tex=0.03 if not small else 0, seed=31 + s)
            if not back:
                lap = cv.poly([g.Q(s * 4.0, 23.2), g.Q(s * 7.8, 23.6), g.Q(s * 6.6, 26.6), g.Q(s * 7.4, 27.4), g.Q(s * 3.4, 33)])
                cv.part("lapel%d" % s, lap, tp, edge="dark", noedge=(), lv=np.where(lap, 3 if s < 0 else 2, 0))
                if not small:
                    py = int(round(g.Y(53)))
                    cv.hline(int(round(g.X(s * 6))) if s < 0 else int(round(g.X(7))), int(round(g.X(-9))) if s < 0 else int(round(g.X(10))), py, tp[0])
        if not small:
            if back:
                cv.vline(int(round(g.c)), int(round(g.Y(48))), int(round(g.Y(63.5))), tp[0])
                y = int(round(g.Y(44)))
                cv.hline(int(round(g.X(-6))), int(round(g.X(6))), y, tp[1]); cv.hline(int(round(g.X(-6))), int(round(g.X(6))), y + 1, tp[0])
                cv.put(int(round(g.X(-5))), y, RAMP["metal"][2]); cv.put(int(round(g.X(5))), y, RAMP["metal"][2])
            else:
                for u in (38, 45):
                    cv.put(int(round(g.X(4.6))), int(round(g.Y(u))), tp[0]); cv.put(int(round(g.X(5.4))), int(round(g.Y(u))), tp[4])
    elif st == "jersey":
        if not back:
            vn = cv.poly([g.Q(-3.0, 21.8), g.Q(3.0, 21.8), g.Q(0, 26.6)])
            cv.part("vneck", vn, sk, edge=None, lv=np.where(vn, 2, 0))
            for s in (-1, 1):
                cv.line(*ipt(g.Q(s * 3.2, 22.2)), *ipt(g.Q(0, 27.0)), RAMP["white"][3] if s < 0 else RAMP["white"][2])
            if not small:
                glyph(cv, int(round(g.c - 2)), int(round(g.Y(30))), GLYPH7, RAMP["white"][3])
            else:
                glyph(cv, int(round(g.c - 1)), int(round(g.Y(30))), GLYPH7S, RAMP["white"][3])
        else:
            if not small:
                big = ["######", "######", "....##", "...##.", "...##.", "..##..", "..##..", "..##.."]
                glyph(cv, int(round(g.c - 3)), int(round(g.Y(29))), big, RAMP["white"][3])
            else:
                glyph(cv, int(round(g.c - 1)), int(round(g.Y(29))), GLYPH7S, RAMP["white"][3])
        if not small:
            for s in (-1, 1):
                x = int(round(g.X(s * 10.4)))
                for y in range(int(g.Y(30)), int(g.Y(46))):
                    if cv.own[y, x] == sid:
                        cv.put(x, y, RAMP["white"][2])


# ==========================================================================
# HEADS (battle front: pixel features; world front: its own small drawing)
# ==========================================================================
def hair_back(cv, ch, c, t, s, view="front"):
    """Everything of the hair that sits BEHIND the face/body.  s = head scale."""
    hr = ch["hair"]
    st = ch["hair_style"]
    H = lambda dx, dy: (c + dx * s, t + dy * s)
    big = s >= 0.8
    if st == "ponytail":
        if view == "front":
            m = cv.capsule(*H(6, 5), *H(11, 13), 2.5 * s, 2.1 * s) | cv.capsule(*H(11, 13), *H(10.2, 24), 2.1 * s, 0.9 * s)
        elif view == "side":
            m = cv.capsule(*H(-6, 4), *H(-12.5, 10), 2.6 * s, 2.2 * s) | cv.capsule(*H(-12.5, 10), *H(-12.6, 23), 2.2 * s, 0.9 * s)
        else:
            m = cv.capsule(*H(0, 3), *H(1, 12), 2.6 * s, 2.4 * s) | cv.capsule(*H(1, 12), *H(-0.5, 31), 2.4 * s, 1.0 * s)
        cv.part("tail", m, hr, rad=2.5 * s + 0.5, soft=0.8, cuts=(0.28, 0.54, 0.86))
        if big:
            for (a, b, d, e) in ([(9, 10, 11, 20)] if view == "front" else [(-11, 8, -12, 20)] if view == "side" else [(0, 8, 0, 22)]):
                cv.line(*ipt(H(a, b)), *ipt(H(d, e)), hr[3])
    elif st == "beret":
        cy = 13.5 if view != "back" else 13
        m = cv.ell(*H(0 if view == "front" else -2.5 if view == "side" else 0, cy), 10.0 * s, 8.6 * s)
        n = 11 if big else 9
        for i in range(n):
            a = math.pi * (-0.15 + 1.3 * i / (n - 1))
            ox = 0 if view == "front" else -2.5 if view == "side" else 0
            px, py = H(ox + math.cos(a) * 9.6, cy + math.sin(a) * 8.0)
            if view == "side" and math.cos(a) > 0.6:
                continue
            m |= cv.ell(px, py, 2.6 * s, 2.6 * s)
        cv.part("curls", m, hr, rad=4 * s + 1, soft=1.0, cuts=(0.30, 0.56, 0.88), bias=-0.06, tex=0.08 if big else 0, seed=41)
        curl_texture(cv, "curls", hr, big)
    elif st == "puff":
        ox = 0 if view != "side" else -3.0
        oy = 0 if view != "back" else 0.5
        m = cv.ell(*H(ox + 0.5, oy + 0.6), 7.4 * s, 5.0 * s)
        for (dx, dy, r) in ((-5.4, 0.8, 2.6), (-2.8, -2.4, 2.7), (0.6, -3.4, 2.8), (4.0, -2.6, 2.7), (6.4, -0.2, 2.5),
                            (6.8, 2.6, 2.2), (-6.4, 3.0, 2.2)):
            m |= cv.ell(*H(ox + dx, oy + dy), r * s, r * s)
        cv.part("puff", m, hr, rad=4 * s + 1, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.1 if big else 0, seed=43)
        curl_texture(cv, "puff", hr, big)


def curl_texture(cv, name, hr, big):
    if not big:
        return
    pid = cv.names[name]
    ys, xs = np.nonzero(cv.own == pid)
    for y, x in zip(ys, xs):
        if (x * 7 + y * 3) % 11 == 0 and tuple(cv.col[y, x]) != hr[0]:
            cv.put(x, y, hr[1])
            if x + 1 < cv.w and cv.own[y, x + 1] == pid:
                cv.put(x + 1, y, hr[3] if (x + y) % 2 else hr[2])


def head_front_b(cv, ch, c, t, mode):
    """Battle head, front view.  mode is a dict: eyes, brows, mouth, glance."""
    sk, hr = ch["skin"], ch["hair"]
    st = ch["hair_style"]
    fw = ch["facew"]
    if ch["ears"]:
        for s in (-1, 1):
            e = cv.ell(c + s * (fw + 0.2), t + 14.6, 1.7, 2.3)
            cv.part("ear%d" % s, e, sk, edge="dark", lv=np.where(e, 2, 0) + np.where(e & (cv.X < c), 1, 0))
    long_ = 0.6 if st == "beret" else 0.0
    face = cv.ell(c, t + 13.5, fw, 7.3) | cv.ell(c, t + 16 + long_, fw - 1.0, 6.8)
    cv.part("face", face, sk, rad=6, soft=1.4, cuts=(0.22, 0.48, 0.86), bias=0.06)
    fid = cv.names["face"]
    if st == "ponytail":
        yb = t + 7.0 + 0.06 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 10.6, 8.6, 10.4) & (cv.Y < yb + 0.5)
        for s in (-1, 1):
            crown |= cv.capsule(c + s * 7.3, t + 9, c + s * 7.7, t + 12.8, 1.2)
        cv.part("crown", crown, hr, noedge=("tail",), rad=5, soft=1.0, cuts=(0.24, 0.5, 0.84))
        bangs = cv.poly([(c - 3, t + 1.6), (c + 4, t + 2.6), (c + 8.6, t + 8), (c + 8.2, t + 12.6), (c + 6.4, t + 10.2),
                         (c + 3, t + 8.8), (c - 1, t + 8.0), (c - 3.6, t + 7.2)])
        cv.part("bangs", bangs, hr, noedge=("crown",), rad=3, soft=0.8, cuts=(0.30, 0.56, 0.88))
        for x in range(c - 6, c + 5):
            y = int(round(t + 3.6 + 0.07 * (x - c + 1) ** 2))
            if cv.own[y, x] in (cv.names["crown"], cv.names["bangs"]) and tuple(cv.col[y, x]) != hr[0]:
                cv.put(x, y, hr[4] if c - 4 <= x <= c - 1 else hr[3])
        cv.line(c - 2, t + 3, c + 6, t + 8, hr[1])
        cv.line(c, t + 5, c + 7, t + 10, hr[1])
        sc = cv.ell(c + 6.4, t + 3.0, 1.9, 1.5)
        cv.part("scrunchie", sc, ch["top"], edge="dark", lv=np.where(sc, 3, 0))
    elif st == "twists":
        yb = t + 7.6 + 0.035 * (cv.X - c) ** 2
        top = (cv.ell(c, t + 9.5, 8.6, 9.3) | (cv.rect(c - 7.6, t + 0.6, c + 7.6, t + 8) & cv.ell(c, t + 5.5, 8.9, 8.6))) & (cv.Y < yb + 0.5)
        side = cv.ell(c, t + 12.5, fw + 0.7, 8.2) & (np.abs(cv.X - c) >= fw - 1.2) & (cv.Y < t + 14.5)
        cv.part("crown", top | side, hr, rad=5, soft=1.0, cuts=(0.24, 0.5, 0.84))
        pid = cv.names["crown"]
        for y in range(t + 1, t + 8, 2):
            for x in range(c - 8, c + 9):
                if cv.own[y, x] == pid and tuple(cv.col[y, x]) != hr[0] and (x + (y - t) // 2) % 2 == 0:
                    cv.put(x, y, hr[3] if x < c + 2 else hr[2])
                    if y + 1 < cv.h and cv.own[y + 1, x] == pid:
                        cv.put(x, y + 1, hr[1])
        for y in range(t + 8, t + 15):
            for x in range(c - 9, c + 10):
                if cv.own[y, x] == pid and abs(x - c) >= fw - 1.2 and tuple(cv.col[y, x]) != hr[0]:
                    cv.put(x, y, mix(hr[2], sk[1], 0.3))
    elif st == "beret":
        yb = t + 8.4 + 0.04 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 10.6, 9.0, 9.6) & (cv.Y < yb + 0.5)
        cv.part("crown", crown, hr, noedge=("curls",), rad=5, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.08, seed=45)
        fr = cv.empty()
        for (dx, dy) in ((-6.2, 9.4), (-3.2, 9.8), (0.4, 9.2), (3.6, 9.8), (6.4, 10.6), (-7.8, 12.4), (7.8, 12.6)):
            fr |= cv.ell(c + dx, t + dy, 1.8, 1.7)
        cv.part("fringe", fr & ~cv.ell(c, t + 16, 5.5, 5.5), hr, noedge=("crown", "curls"), rad=2, soft=0.8, cuts=(0.28, 0.54, 0.86))
        curl_texture(cv, "crown", hr, True)
        br = cv.ell(c - 1.0, t + 4.6, 10.2, 4.5, -0.10) & (cv.Y < t + 8.0 - 0.10 * (cv.X - c))
        cv.part("beret", br, ch["beret"], edge="dark", rad=3, soft=1.0, cuts=(0.26, 0.5, 0.82))
        cv.put(c - 1, t, ch["beret"][2]); cv.put(c, t, ch["beret"][1])
        bid = cv.names["beret"]
        for x in range(c - 11, c + 10):
            for y in range(t + 10, t + 2, -1):
                if cv.own[y, x] == bid:
                    cv.put(x, y, ch["beret"][1])
                    break
    elif st == "puff":
        yb = t + 7.4 + 0.045 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 10.6, 8.4, 9.8) & (cv.Y < yb + 0.5)
        cv.part("crown", crown, hr, noedge=("puff",), rad=5, soft=1.0, cuts=(0.24, 0.5, 0.84))
        for dx in (-6, -3, 0, 3, 6):
            cv.line(int(round(c + dx)), int(round(t + 6.5 + 0.03 * dx * dx)), int(round(c + dx * 0.45)), t + 2, hr[1])
        cv.puts([(c - 4, t + 3), (c - 3, t + 3), (c - 5, t + 4)], hr[4])
        band = cv.ell(c, t + 12, 9.4, 10.6) & (cv.Y >= yb - 1.6) & (cv.Y < yb + 0.6)
        cv.part("band", band, "white", edge="dark", lv=np.where(band, 3, 0) - np.where(band & (cv.X > c + 3), 1, 0))
    features_b(cv, ch, c, t, mode)


def features_b(cv, ch, c, t, mode):
    sk, hr = ch["skin"], ch["hair"]
    st = ch["hair_style"]
    fid = cv.names["face"]
    br = hr[0] if st in ("beret",) else hr[1]
    if st == "beret":
        br = hr[1]
    ey = t + 13
    em = mode.get("eyes", "open")
    gl = mode.get("glance", 0)
    # cheeks / freckles / beard first (features go over them)
    if ch.get("blush"):
        for s in (-1, 1):
            cv.put(c + s * 5, t + 16, mix(sk[2], ch["blush"], 0.5)); cv.put(c + s * 4, t + 16, mix(sk[2], ch["blush"], 0.35))
    if st == "beret":
        FR = (196, 110, 76)
        for (x, y) in ((c - 5, t + 16), (c - 3, t + 17), (c + 3, t + 16), (c + 5, t + 17)):
            cv.put(x, y, mix(cv.get(x, y), FR, 0.45))
        for y in range(t + 18, t + 24):
            for x in range(c - 7, c + 8):
                if cv.own[y, x] == fid and tuple(cv.col[y, x]) != sk[0] and (abs(x - c) >= 4 or y >= t + 22):
                    cv.put(x, y, mix(cv.get(x, y), hr[1], 0.2))
        cv.hline(c - 1, c + 1, t + 23, hr[2])
    if st == "twists":
        fm = cv.own == fid
        er = ndi.binary_erosion(fm, iterations=2)
        band = fm & ~er & (cv.Y >= t + 14)
        ys, xs = np.nonzero(band)
        for y, x in zip(ys, xs):
            if tuple(cv.col[y, x]) != sk[0]:
                cv.put(x, y, hr[2] if x < c else hr[1])
        cv.hline(c - 2, c + 2, t + 18, hr[1])
    # nose
    cv.put(c, t + 15, sk[3]); cv.put(c, t + 16, sk[2]); cv.put(c + 1, t + 16, sk[1]); cv.put(c - 1, t + 17, sk[1])
    # eyes
    for side in (-1, 1):
        x0 = c - 5 if side < 0 else c + 2
        outer = x0 - 1 if side < 0 else x0 + 4
        if em in ("open", "up", "down", "narrow"):
            ly = ey + (1 if em in ("down", "narrow") else 0)
            cv.hline(x0, x0 + 3, ly, EYE)
            if em == "down":
                cv.put(x0 + 1, ly + 1, ch["iris_d"]); cv.put(x0 + 2, ly + 1, ch["iris"])
            else:
                ix = x0 + 1 + gl
                cv.put(x0, ly + 1, SCLERA); cv.put(x0 + 3, ly + 1, SCLERA)
                cv.put(ix, ly + 1, ch["iris_d"] if side < 0 else ch["iris"])
                cv.put(ix + 1, ly + 1, ch["iris"] if side < 0 else ch["iris_d"])
                if em == "up":
                    cv.put(ix, ly + 2, SCLERA); cv.put(ix + 1, ly + 2, SCLERA)
                    cv.hline(x0, x0 + 3, ly + 3, sk[1])
            if ch["fem"]:
                cv.put(outer, ly - 1 if em != "down" else ly, EYE)
        elif em == "happy":
            cv.puts([(x0, ey + 1), (x0 + 1, ey), (x0 + 2, ey), (x0 + 3, ey + 1)], EYE)
            if ch["fem"]:
                cv.put(outer, ey, EYE)
        elif em == "closed":
            cv.hline(x0, x0 + 3, ey + 1, EYE)
            if ch["fem"]:
                cv.put(outer, ey + 1, EYE)
        elif em == "hit":
            mp = ["K...", ".KK.", "K..."] if side < 0 else ["...K", ".KK.", "...K"]
            for j, row in enumerate(mp):
                for i, chh in enumerate(row):
                    if chh == "K":
                        cv.put(x0 + i, ey - 1 + j, EYE)
    # brows
    bm = mode.get("brows", "flat")
    for side in (-1, 1):
        xs = [c - 5, c - 4, c - 3] if side < 0 else [c + 5, c + 4, c + 3]   # outer -> inner
        if bm == "flat":
            ys = [ey - 2, ey - 2, ey - 2]
        elif bm == "up":
            ys = [ey - 3, ey - 3, ey - 3]
        elif bm == "angry":
            ys = [ey - 3, ey - 2, ey - 1]
        elif bm == "worried":
            ys = [ey - 2, ey - 3, ey - 3]
        elif bm == "smug":
            ys = [ey - 3, ey - 3, ey - 2] if side > 0 else [ey - 2, ey - 2, ey - 2]
        else:
            ys = [ey - 2] * 3
        if bm == "up" or bm == "hit":
            ys = [ey - 3, ey - 3, ey - 3] if bm == "up" else [ey - 3, ey - 3, ey - 2]
        for x, y in zip(xs, ys):
            cv.put(x, y, br)
    # mouth
    mm = mode.get("mouth", "smile")
    my = t + 19 + (1 if st == "beret" else 0)
    lip = ch["lip"]
    if mm == "smile":
        cv.put(c - 2, my, MOUTH); cv.put(c + 2, my, MOUTH); cv.hline(c - 1, c + 1, my + 1, MOUTH)
        if ch["fem"]:
            cv.put(c, my + 2, mix(sk[2], lip, 0.45))
    elif mm == "talk":
        cv.put(c - 2, my, MOUTH); cv.put(c + 2, my, MOUTH); cv.hline(c - 1, c + 1, my, TEETH)
        cv.hline(c - 1, c + 1, my + 1, MOUTH); cv.put(c, my + 1, TONGUE)
        cv.hline(c - 1, c + 1, my + 2, mix(sk[2], lip, 0.6) if ch["fem"] else sk[1])
    elif mm == "grin":
        cv.put(c - 3, my - 1, MOUTH); cv.put(c + 3, my - 1, MOUTH)
        cv.hline(c - 2, c + 2, my, TEETH); cv.put(c - 3, my, MOUTH); cv.put(c + 3, my, MOUTH)
        cv.hline(c - 2, c + 2, my + 1, MOUTH)
    elif mm == "smirk":
        cv.put(c + 3, my - 1, MOUTH); cv.put(c + 2, my, MOUTH); cv.hline(c - 2, c + 1, my + 1, MOUTH)
        if ch["fem"]:
            cv.hline(c - 1, c + 1, my + 2, mix(sk[2], lip, 0.6))
    elif mm == "flat":
        cv.hline(c - 2, c + 1, my + 1, MOUTH); cv.put(c + 2, my, MOUTH)
    elif mm == "ouch":
        cv.hline(c - 1, c + 1, my, MOUTH); cv.hline(c - 2, c + 2, my + 1, MOUTH); cv.put(c, my + 1, TONGUE)
        cv.hline(c - 1, c + 1, my + 2, MOUTH)
    elif mm == "sip":
        cv.puts([(c - 1, my), (c, my), (c - 1, my + 1), (c, my + 1)], MOUTH)
    # glasses
    if st == "twists":
        for side in (-1, 1):
            x0 = c - 5 if side < 0 else c + 2
            for x in range(x0 - 1, x0 + 5):
                for y in range(ey - 1, ey + 3):
                    edge = x in (x0 - 1, x0 + 4) or y in (ey - 1, ey + 2)
                    if edge:
                        cv.put(x, y, FRAME)
                    elif cv.own[y, x] == fid and tuple(cv.col[y, x]) not in (EYE, ch["iris"], ch["iris_d"], SCLERA):
                        cv.put(x, y, mix(cv.get(x, y), RAMP["lens"][3], 0.22))
            cv.put(c - 7 if side < 0 else c + 7, ey, FRAME)
            cv.put(c - 7 if side < 0 else c + 7, ey - 1, FRAME)
        cv.put(c, ey, FRAME)
        if mode.get("glint"):
            for (x, y) in ((c - 5, ey + 1), (c - 4, ey), (c + 3, ey + 1), (c + 4, ey)):
                cv.put(x, y, WHITE)
    if st == "beret":
        gd = RAMP["gold"]
        for side in (-1, 1):
            ex = c - 3.5 if side < 0 else c + 3.5
            ring = cv.ell(ex, ey + 0.6, 2.7, 2.3) & ~cv.ell(ex, ey + 0.6, 1.7, 1.3)
            ys, xs = np.nonzero(ring)
            for y, x in zip(ys, xs):
                cv.put(x, y, gd[3] if (y < ey and x < ex) else gd[2] if y < ey + 1 else gd[1])
        cv.put(c, ey, gd[2])
        if mode.get("askew"):
            cv.put(c - 7, ey - 2, gd[2])


def head_front_w(cv, ch, c, t, mode):
    """World head (front), drawn small: about 14 px tall."""
    sk, hr = ch["skin"], ch["hair"]
    st = ch["hair_style"]
    fw = ch["facew"] * 0.655
    if ch["ears"]:
        for s in (-1, 1):
            e = cv.ell(c + s * (fw + 0.2), t + 9.2, 1.1, 1.5)
            cv.part("ear%d" % s, e, sk, edge="dark", lv=np.where(e, 2, 0))
    face = cv.ell(c, t + 8.6, fw, 4.7) | cv.ell(c, t + 10.2 + (0.4 if st == "beret" else 0), fw - 0.7, 4.4)
    cv.part("face", face, sk, rad=4, soft=1.0, cuts=(0.22, 0.46, 0.88), bias=0.08)
    fid = cv.names["face"]
    if st == "ponytail":
        yb = t + 4.6 + 0.09 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 6.7, 5.6, 6.6) & (cv.Y < yb + 0.5)
        cv.part("crown", crown, hr, noedge=("tail",), rad=3, soft=0.8, cuts=(0.24, 0.5, 0.84))
        bangs = cv.poly([(c - 2, t + 1), (c + 3, t + 1.6), (c + 5.6, t + 5), (c + 5.4, t + 8), (c + 3.6, t + 6.2), (c, t + 5.2), (c - 2.4, t + 4.6)])
        cv.part("bangs", bangs, hr, noedge=("crown",), rad=2, soft=0.6, cuts=(0.30, 0.56, 0.88))
        cv.puts([(c - 3, t + 2), (c - 2, t + 2)], hr[4])
        cv.put(c + 4, t + 1, ch["top"][3])
    elif st == "twists":
        yb = t + 4.9 + 0.05 * (cv.X - c) ** 2
        top = (cv.ell(c, t + 6.2, 5.6, 6.2) | (cv.rect(c - 5, t + 0.5, c + 5, t + 5) & cv.ell(c, t + 4, 5.8, 5.6))) & (cv.Y < yb + 0.5)
        side = cv.ell(c, t + 8.2, fw + 0.5, 5.4) & (np.abs(cv.X - c) >= fw - 0.6) & (cv.Y < t + 9.6)
        cv.part("crown", top | side, hr, rad=3, soft=0.8, cuts=(0.24, 0.5, 0.84))
        for x in range(c - 4, c + 5, 2):
            cv.put(x, t + 2, hr[3] if x < c + 2 else hr[2])
        for x in range(c - 3, c + 4, 2):
            cv.put(x, t + 4, hr[3] if x < c + 2 else hr[2])
    elif st == "beret":
        yb = t + 5.4 + 0.06 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 6.8, 5.8, 6.2) & (cv.Y < yb + 0.5)
        cv.part("crown", crown, hr, noedge=("curls",), rad=3, soft=0.8, cuts=(0.28, 0.54, 0.86))
        fr = cv.empty()
        for (dx, dy) in ((-4, 6), (-1.5, 6.3), (1.5, 6.0), (4, 6.6)):
            fr |= cv.ell(c + dx, t + dy, 1.2, 1.1)
        cv.part("fringe", fr, hr, noedge=("crown", "curls"), lv=np.where(fr, 3, 0) - np.where(fr & (cv.X > c + 2), 1, 0))
        brt = cv.ell(c - 0.6, t + 2.9, 6.6, 2.9, -0.1) & (cv.Y < t + 5.2 - 0.1 * (cv.X - c))
        cv.part("beret", brt, ch["beret"], edge="dark", rad=2, soft=0.8, cuts=(0.26, 0.5, 0.82))
        cv.put(c - 1, t, ch["beret"][2])
    elif st == "puff":
        yb = t + 4.8 + 0.07 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 6.8, 5.4, 6.3) & (cv.Y < yb + 0.5)
        cv.part("crown", crown, hr, noedge=("puff",), rad=3, soft=0.8, cuts=(0.24, 0.5, 0.84))
        band = cv.ell(c, t + 7.6, 6.0, 6.8) & (cv.Y >= yb - 1.0) & (cv.Y < yb + 0.2)
        cv.part("band", band, "white", edge=None, lv=np.where(band, 3, 0) - np.where(band & (cv.X > c + 2), 1, 0))
    # features
    ey = t + 8
    em = mode.get("eyes", "open")
    gl = mode.get("glance", 0)
    if st == "twists":
        for y in range(t + 10, t + 15):
            for x in range(c - 6, c + 7):
                if cv.own[y, x] == fid and tuple(cv.col[y, x]) != sk[0] and abs(x - c) >= 3:
                    cv.put(x, y, hr[1] if y < t + 13 or abs(x - c) >= 2 else hr[2])
        cv.put(c, t + 14, hr[1])
    if st == "beret":
        cv.put(c - 3, t + 10, mix(sk[2], (200, 120, 90), 0.5)); cv.put(c + 3, t + 10, mix(sk[2], (200, 120, 90), 0.5))
        cv.put(c, t + 14, hr[2])
    if ch.get("blush") and st != "beret":
        cv.put(c - 3, t + 10, mix(sk[2], ch["blush"], 0.5)); cv.put(c + 3, t + 10, mix(sk[2], ch["blush"], 0.5))
    for side in (-1, 1):
        x = c - 2 if side < 0 else c + 2
        if em == "open":
            cv.put(x + gl, ey, EYE); cv.put(x + gl, ey + 1, EYE)
        elif em == "up":
            cv.put(x + gl, ey - 1 if st != "twists" else ey, EYE); cv.put(x + gl, ey, EYE)
        elif em == "down":
            cv.put(x, ey + 1, EYE); cv.put(x - side, ey + 1, EYE)
        elif em == "narrow":
            cv.put(x, ey + 1, EYE); cv.put(x - side, ey + 1, EYE)
        elif em in ("closed", "blink"):
            cv.put(x, ey + 1, sk[0]); cv.put(x - side, ey + 1, sk[0])
        elif em == "happy":
            cv.put(x, ey, EYE); cv.put(x - 1, ey + 1, EYE); cv.put(x + 1, ey + 1, EYE)
        elif em == "hit":
            cv.put(x - side, ey - 1, EYE); cv.put(x, ey, EYE); cv.put(x - side, ey + 1, EYE)
        if ch["fem"] and em in ("open", "up"):
            cv.put(x + side + gl, ey - 1 if em == "open" else ey - 1, EYE)
    if st == "twists":
        LN = mix(sk[3], RAMP["lens"][3], 0.55)
        for side in (-1, 1):
            x = c - 2 if side < 0 else c + 2
            cv.puts([(x - 1, ey - 1), (x, ey - 1), (x + 1, ey - 1)], FRAME)
            if em in ("open", "up"):
                cv.put(x - 1 if side < 0 else x + 1, ey, LN)
                cv.put(x + gl, ey, LN); cv.put(x + gl, ey + 1, EYE)
            cv.put(x - 1 if side < 0 else x + 1, ey + 1, FRAME) if False else None
        cv.put(c, ey, FRAME)
        cv.put(c - 4, ey, FRAME); cv.put(c + 4, ey, FRAME)
        if mode.get("glint"):
            cv.put(c - 3, ey, WHITE); cv.put(c + 1, ey, WHITE)
    if st == "beret":
        gd = RAMP["gold"]
        for side in (-1, 1):
            x = c - 2 if side < 0 else c + 2
            cv.puts([(x - 1, ey), (x + 1, ey + 1)], gd[3])
            cv.puts([(x - 1, ey + 1), (x + 1, ey)], gd[2])
        cv.put(c, ey, gd[2])
    # brows (only when they say something)
    bm = mode.get("brows", "flat")
    brc = hr[1]
    if bm == "angry":
        cv.put(c - 3, ey - 2, brc); cv.put(c - 2, ey - 1, brc) if st != "twists" else None
        cv.put(c + 3, ey - 2, brc); cv.put(c + 2, ey - 1, brc) if st != "twists" else None
    elif bm == "smug":
        cv.put(c + 2, ey - 3 if st != "puff" else ey - 2, brc); cv.put(c + 3, ey - 3 if st != "puff" else ey - 2, brc)
    # mouth
    mm = mode.get("mouth", "smile")
    my = t + 12 + (1 if st == "beret" else 0)
    if mm == "smile":
        cv.put(c - 1, my - 1 if False else my, MOUTH); cv.put(c, my, MOUTH)
        cv.put(c + 1, my, sk[1] if ch["fem"] else MOUTH)
        if ch["fem"]:
            cv.put(c - 2, my - 1, mix(sk[2], MOUTH, 0.6)) if False else None
    elif mm == "talk":
        cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c, my + 1, TONGUE)
    elif mm == "grin":
        cv.hline(c - 1, c + 1, my, TEETH); cv.put(c - 2, my - 1, MOUTH); cv.put(c + 2, my - 1, MOUTH)
        cv.hline(c - 1, c + 1, my + 1, MOUTH)
    elif mm == "smirk":
        cv.put(c - 1, my, MOUTH); cv.put(c, my, MOUTH); cv.put(c + 1, my - 1, MOUTH)
    elif mm == "flat":
        cv.hline(c - 1, c + 1, my, MOUTH)
    elif mm == "ouch":
        cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c, my + 1, MOUTH)
    elif mm == "sip":
        cv.put(c, my, MOUTH)


# ==========================================================================
# ARMS + PROPS per character (front view).  Each returns a list of "late" draws (after the head).
# ==========================================================================
def arms_business(cv, g, ch, pose, extra):
    Q = g.Q
    b = g.battle
    s = 1.0 if b else 0.62
    late = []
    # viewer-right arm (her left): free hand
    if pose == "talk":
        arm(cv, g, ch, "armR", [Q(10.3, 25.5), Q(15.6, 34), Q(17.2, 29)])
        open_hand(cv, g, ch, *Q(17.4, 26.4), "handR")
    elif pose == "tell" or extra == "phone":
        arm(cv, g, ch, "armR", [Q(10.3, 25.5), Q(13.6, 37), Q(7.8, 37)])
        phone(cv, *Q(6.4, 33.4), s)
        hand(cv, g, ch, *Q(7.6, 36.4), "handR")
    elif pose == "hit":
        arm(cv, g, ch, "armR", [Q(10.3, 25.5), Q(16, 30), Q(19.6, 24)])
        open_hand(cv, g, ch, *Q(20, 21.4), "handR")
    else:
        arm(cv, g, ch, "armR", [Q(10.6, 25.5), Q(14.0, 35.5), Q(14.0, 43.6)])
        hand(cv, g, ch, *Q(14.0, 45.0), "handR")
    # viewer-left arm: the iced coffee
    if pose == "hit":
        arm(cv, g, ch, "armL", [Q(-10.3, 25.5), Q(-16.5, 33), Q(-20, 29)])
        coffee(cv, *Q(-20.5, 28.4), s, ang=-0.85)
        hand(cv, g, ch, *Q(-20.2, 28.6), "handL")
    elif extra == "sip":
        arm(cv, g, ch, "armL", [Q(-10.3, 25.5), Q(-12.6, 35), Q(-4.0, 31.5)])
        coffee(cv, *g.Hh(-2.6, 29.2), s, ang=0.22)
        hand(cv, g, ch, *g.Hh(-2.8, 29.4), "handL")
    else:
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-14.6, 35), Q(-12.6, 40.5)])
        coffee(cv, *Q(-13.0, 40.4), s)
        hand(cv, g, ch, *Q(-12.6, 40.6), "handL")
    return late


def arms_engineering(cv, g, ch, pose, extra):
    Q = g.Q
    b = g.battle
    s = 0.92 if b else 0.6
    late = []
    # viewer-left arm: free
    if pose == "talk":
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-15.6, 34), Q(-16.0, 28.5)])
        point_hand(cv, g, ch, *Q(-16.0, 27.4), "handL", 0.0, -1.0)
    elif pose == "hit":
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-16, 31), Q(-19, 26)])
        open_hand(cv, g, ch, *Q(-19.2, 23.8), "handL")
    elif pose == "tell":
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-13.6, 35), Q(-7.0, 40)])
    elif extra == "glasses":
        late.append(lambda: (arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-12.6, 33), g.Hh(-2.2, 17.6)]),
                             point_hand(cv, g, ch, *g.Hh(-1.4, 15.2), "handL", 0.3, -1.0)))
    elif extra == "scratch":
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-16.5, 22), g.Hh(-9.4, 6.0)])
        late.append(lambda: hand(cv, g, ch, *g.Hh(-7.6, 5.2), "handL"))
    else:
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-13.4, 35.5), Q(-12.8, 44)])
        hand(cv, g, ch, *Q(-12.8, 45.2), "handL", r=2.5)
    # viewer-right arm + robot
    if pose == "tell":
        robot(cv, *Q(0, 37.5), s, mood="angry")
        arm(cv, g, ch, "armR", [Q(10.6, 25.5), Q(13.6, 35), Q(7.0, 40)])
        hand(cv, g, ch, *Q(6.4, 40.5), "handR", r=2.5)
        hand(cv, g, ch, *Q(-6.4, 40.5), "handL", r=2.5)
    else:
        mood = "hit" if pose == "hit" else "ok"
        arm(cv, g, ch, "armR", [Q(10.6, 25.5), Q(15.4, 34.5), Q(15.6, 42.6)])
        robot(cv, *Q(16.4, 36.8), s, mood=mood)
        hand(cv, g, ch, *Q(15.8, 43.8), "handR", r=2.5)
    return late


def arms_philosophy(cv, g, ch, pose, extra):
    Q = g.Q
    b = g.battle
    s = 1.0 if b else 0.62
    late = []
    reading = pose == "tell" or extra == "read"
    if reading:
        arm(cv, g, ch, "armL", [Q(-10.4, 25.5), Q(-13.2, 36), Q(-7.6, 39)])
        arm(cv, g, ch, "armR", [Q(10.4, 25.5), Q(13.2, 36), Q(7.6, 39)])
        book(cv, *Q(0, 36.6), s, kind="open")
        hand(cv, g, ch, *Q(-8.4, 39.0), "handL")
        hand(cv, g, ch, *Q(8.4, 39.0), "handR")
        return late
    # viewer-left: the book
    if pose == "hit":
        arm(cv, g, ch, "armL", [Q(-10.4, 25.5), Q(-16.5, 32), Q(-18.5, 26)])
        open_hand(cv, g, ch, *Q(-18.8, 23.6), "handL")
        book(cv, *Q(-15, 49), s, kind="open", ang=0.5)
    else:
        arm(cv, g, ch, "armL", [Q(-10.4, 25.5), Q(-14.2, 34.5), Q(-12.2, 41)])
        book(cv, *Q(-12.6, 41.6), s, kind="closed")
        hand(cv, g, ch, *Q(-11.6, 41.4), "handL")
    # viewer-right
    if pose == "talk":
        arm(cv, g, ch, "armR", [Q(10.4, 25.5), Q(15.4, 35), Q(15.8, 29.6)])
        point_hand(cv, g, ch, *Q(15.8, 28.6), "handR", 0.0, -1.0)
    elif pose == "hit":
        arm(cv, g, ch, "armR", [Q(10.4, 25.5), Q(15.6, 33), Q(18.4, 39)])
        open_hand(cv, g, ch, *Q(18.8, 40.4), "handR")
    elif extra == "chin":
        late.append(lambda: (arm(cv, g, ch, "armR", [Q(10.4, 25.5), Q(12.2, 35), g.Hh(3.6, 23.8)]),
                             hand(cv, g, ch, *g.Hh(2.6, 22.2), "handR")))
    else:   # hand in the coat pocket
        arm(cv, g, ch, "armR", [Q(10.4, 25.5), Q(12.8, 36), Q(9.8, 46.5)])
    return late


def arms_frisbee(cv, g, ch, pose, extra):
    Q = g.Q
    b = g.battle
    s = 1.0 if b else 0.62
    late = []
    # viewer-left arm
    if pose == "talk":
        arm(cv, g, ch, "armL", [Q(-10.3, 25.5), Q(-16.5, 23), Q(-17.6, 15.5)])
        open_hand(cv, g, ch, *Q(-17.8, 13.0), "handL")
    elif pose == "hit":
        late.append(lambda: (arm(cv, g, ch, "armL", [Q(-10.3, 25.5), Q(-15.6, 30), g.Hh(-14.6, 9.0), g.Hh(-8.6, 6.4)]),
                             open_hand(cv, g, ch, *g.Hh(-6.4, 5.4), "handL")))
    elif extra == "stretch":
        arm(cv, g, ch, "armL", [Q(-10.3, 25.5), Q(-12.8, 12), g.Hh(-3.0, -1.6)])
        hand(cv, g, ch, *g.Hh(-1.6, -2.6), "handL")
    else:   # hand on hip
        arm(cv, g, ch, "armL", [Q(-10.3, 25.5), Q(-16.6, 34.5), Q(-11.6, 43)])
        hand(cv, g, ch, *Q(-11.4, 43.2), "handL")
    # viewer-right arm + disc
    if pose == "tell":
        arm(cv, g, ch, "armR", [Q(10.3, 25.5), Q(9.0, 36), Q(-6.6, 38.5)])
        disc(cv, *Q(-11.6, 38.6), s, ang=-0.25)
        hand(cv, g, ch, *Q(-7.0, 38.4), "handR")
    elif pose == "hit":
        arm(cv, g, ch, "armR", [Q(10.3, 25.5), Q(16, 30), Q(18.4, 24.5)])
        open_hand(cv, g, ch, *Q(18.6, 22.0), "handR")
        disc(cv, *g.Hh(13, -2), s, ang=0.5)
    elif extra == "spin":
        arm(cv, g, ch, "armR", [Q(10.3, 25.5), Q(15.4, 34), Q(14.6, 28.2)])
        point_hand(cv, g, ch, *Q(14.6, 27.4), "handR", 0.0, -1.0)
        disc(cv, *Q(14.6, 21.5), s, flat=0.75)
    else:
        arm(cv, g, ch, "armR", [Q(10.3, 25.5), Q(13.6, 35), Q(13.2, 43.4)])
        disc(cv, *Q(15.2, 44.6), s, ang=0.0, flat=2.3)
        hand(cv, g, ch, *Q(13.4, 43.4), "handR")
    return late


ARMS = {"business_major": arms_business, "engineering_major": arms_engineering,
        "philosophy_major": arms_philosophy, "frisbee": arms_frisbee}

# face per pose (idle/talk/tell/hit) and per world idle extra
MODES = {
    "business_major": {"tell": dict(eyes="down", brows="smug", mouth="smirk"),
                       "sip": dict(eyes="closed", mouth="sip"), "phone": dict(eyes="down", mouth="smirk")},
    "engineering_major": {"tell": dict(eyes="narrow", brows="angry", mouth="grin", glint=True),
                          "glasses": dict(glint=True, mouth="smile"), "scratch": dict(eyes="up", mouth="flat", glance=-1)},
    "philosophy_major": {"tell": dict(eyes="down", brows="up", mouth="flat"),
                         "read": dict(eyes="down", mouth="flat"), "chin": dict(eyes="up", brows="up", mouth="flat")},
    "frisbee": {"tell": dict(eyes="narrow", brows="angry", mouth="grin"),
                "spin": dict(eyes="up", mouth="grin"), "stretch": dict(eyes="closed", mouth="smile")},
}


def face_mode(cid, pose, extra):
    if extra == "blink":
        return dict(eyes="closed" if True else "blink")
    if extra:
        return MODES[cid][extra]
    if pose == "talk":
        return dict(mouth="talk", brows="up")
    if pose == "hit":
        return dict(eyes="hit", mouth="ouch", brows="hit", askew=True)
    if pose == "tell":
        return MODES[cid]["tell"]
    return {}


EXTRAS = {"business_major": ("sip", "phone"), "engineering_major": ("glasses", "scratch"),
          "philosophy_major": ("read", "chin"), "frisbee": ("spin", "stretch")}


def front(cid, pose, battle=True, extra=None):
    ch = CHARS[cid]
    g = G(ch, battle)
    cv = Cv(g.CW, g.CH)
    c, t = g.c, g.t
    hx = 1 if pose == "hit" else 0
    hair_back(cv, ch, c + hx, t, g.hk, "front")
    legs_front(cv, g, ch)
    torso_front(cv, g, ch)
    late = ARMS[cid](cv, g, ch, pose, extra)
    mode = face_mode(cid, pose, extra)
    if battle:
        head_front_b(cv, ch, c + hx, t, mode)
    else:
        head_front_w(cv, ch, c + hx, t, mode)
    for f in late:
        f()
    cv.outline()
    fx_front(cv, g, ch, cid, pose, extra)
    return cv


def fx_front(cv, g, ch, cid, pose, extra):
    b = g.battle
    c, t = g.c, g.t
    if pose == "hit":
        sweat(cv, c + (9 if b else 6), t + (3 if b else 2), b)
        if cid == "business_major":
            for (dx, dy) in ((-24, 18), (-26, 22), (-22, 14), (-27, 15)) if b else ((-15, 12), (-16, 15)):
                cv.put(c + dx, t + dy, RAMP["coffee"][2])
            if b:
                cv.put(c - 25, t + 19, RAMP["coffee"][4])
        if cid == "engineering_major":
            x, y = ipt(g.Q(16.4, 36.8))
            for (dx, dy) in ((5, -15), (7, -13), (8, -16), (4, -18)) if b else ((3, -9), (5, -8)):
                cv.put(x + dx, y + dy, SPARK2 if dx % 2 else SPARK)
        if cid == "philosophy_major" and b:
            for (x, y) in ((c - 26, t + 30), (c + 22, t + 36)):
                cv.puts([(x, y), (x + 1, y), (x + 2, y), (x, y + 1), (x + 1, y + 1), (x + 2, y + 1), (x, y + 2), (x + 1, y + 2), (x + 2, y + 2)], RAMP["paper"][3])
                cv.put(x + 2, y + 2, RAMP["paper"][1]); cv.put(x, y, RAMP["paper"][4])
        if cid == "frisbee":
            x, y = ipt(g.Hh(13, -2))
            for i in range(3 if b else 2):
                cv.put(x - 8 - i * 2, y + 3 + i, WHITE if i == 0 else SPARK)
            if b:
                cv.puts([(c - 3, t - 3), (c - 1, t - 5), (c + 2, t - 4)], SPARK2)
    if pose == "tell":
        if cid == "engineering_major" and b:
            sparkle(cv, c - 9, t + 9, big=False)
        if cid == "frisbee" and b:
            for j in range(3):
                cv.put(c - 26 + j, t + 26 + j * 2, WHITE if j == 0 else SPARK)
        if cid == "philosophy_major" and b:
            cv.puts([(c + 15, t + 2), (c + 16, t + 1), (c + 17, t + 2), (c + 17, t + 3), (c + 16, t + 4), (c + 16, t + 6)], SPARK)
        if cid == "business_major" and b:
            # a tiny green stock tick above the phone
            x, y = ipt(g.Q(6.4, 33.4))
            cv.puts([(x - 3, y - 7), (x - 2, y - 8), (x - 1, y - 7), (x, y - 9), (x + 1, y - 10), (x + 2, y - 11)], (90, 220, 120))
            cv.puts([(x + 1, y - 11), (x + 2, y - 10)], (90, 220, 120))
    if pose == "talk" and b and cid == "philosophy_major":
        x, y = ipt(g.Q(15.8, 24.0))
        cv.put(x + 3, y - 2, SPARK)
    if extra == "spin":
        x, y = ipt(g.Q(14.6, 21.5))
        cv.puts([(x - 5, y - 2), (x + 5, y + 2)], WHITE)
    if extra == "sip" and not b:
        pass


# ==========================================================================
# SIDE (facing right) and BACK
# ==========================================================================
def legs_side(cv, g, ch):
    k = g.wk
    st = ch["legs_style"]
    for j, (lx, lean) in enumerate(((-2.4, -0.9), (1.6, 0.9))):
        x0 = lx
        x1 = lx + lean
        shoe(cv, g, ch, g.X(x1), 1, "shoe%d" % j, side=True)
        if st == "shorts":
            leg = cv.capsule(*g.Q(x0, 52), *g.Q(x1, 77), 2.6 * k, 2.1 * k)
            cv.part("shin%d" % j, leg, ch["skin"], rad=2.5 * k + 0.4, cuts=(0.28, 0.52, 0.86) if j else (0.45, 0.7, 0.95))
            sock = cv.capsule(*g.Q(x1, 67), *g.Q(x1, 77.5), 2.45 * k, 2.3 * k) & (cv.Y < g.CH - 2)
            cv.part("sock%d" % j, sock, ch["sock"], rad=2.4 * k, cuts=(0.3, 0.55, 0.9))
            sid = cv.names["sock%d" % j]
            for y in ((int(round(g.Y(68.6))), int(round(g.Y(70.4)))) if g.battle else (int(round(g.Y(69))),)):
                for x in range(cv.w):
                    if cv.own[y, x] == sid and tuple(cv.col[y, x]) != ch["sock"][0]:
                        cv.put(x, y, RAMP["disc"][2])
        else:
            r0 = (3.6 if st == "cargo" else 3.1) * k
            leg = cv.capsule(*g.Q(x0, 46), *g.Q(x1, 75.5), r0, r0 * 0.92) & (cv.Y <= g.Y(77.4))
            cv.part("leg%d" % j, leg, ch["pants"], rad=r0 + 0.4, cuts=(0.30, 0.55, 0.88) if j else (0.45, 0.70, 0.95))
            if st == "cargo" and j and g.battle:
                px, py = g.X(x0 + 0.5), g.Y(59)
                pk = cv.rect(px - 2.2, py - 3, px + 2.2, py + 3) & leg
                cv.part("pk%d" % j, pk, ch["pants"], edge="dark", noedge=("leg%d" % j,), lv=np.where(pk, 2, 0) + np.where(pk & (cv.Y < py - 1.5), 1, 0))
    if st == "shorts":
        m = cv.poly([g.Q(-6.8, 44), g.Q(6.0, 44), g.Q(6.8, 57), g.Q(-7.6, 57)])
        cv.part("shorts", m, ch["pants"], rad=4, cuts=(0.30, 0.55, 0.88))
        if g.battle:
            x = int(round(g.X(-0.4)))
            for y in range(int(g.Y(46)), int(g.Y(56.5)) + 1):
                if cv.own[y, x] == cv.names["shorts"]:
                    cv.put(x, y, ch["top"][2])


def side(cid, battle=True):
    ch = CHARS[cid]
    g = G(ch, battle, cshift=-2)
    cv = Cv(g.CW, g.CH)
    c, t = g.c, g.t
    k, s = g.wk, g.hk
    b = battle
    sk, hr, tp = ch["skin"], ch["hair"], ch["top"]
    st = ch["top_style"]
    H = lambda dx, dy: (c + dx * s, t + dy * s)
    hair_back(cv, ch, c, t, s, "side")
    # things carried on the far side / behind
    legs_side(cv, g, ch)
    # torso profile
    if st == "hoodie":
        tor = cv.poly([g.Q(-5, 22), g.Q(3.5, 22), g.Q(7.5, 26), g.Q(8.5, 32), g.Q(9.5, 40), g.Q(8.5, 49.2), g.Q(-7.5, 49.2), g.Q(-8, 36), g.Q(-7.6, 27)])
    elif st == "coat":
        tor = cv.poly([g.Q(-5, 22), g.Q(3, 22), g.Q(7, 26), g.Q(7.6, 31), g.Q(6.8, 38), g.Q(7.6, 47), g.Q(8.6, 64), g.Q(-9.6, 64), g.Q(-7.4, 46), g.Q(-7.2, 36), g.Q(-7, 28)])
    elif st == "blazer":
        tor = cv.poly([g.Q(-5, 22), g.Q(3, 22), g.Q(7, 26), g.Q(8, 31), g.Q(6.5, 37), g.Q(7.6, 51), g.Q(-7.8, 51), g.Q(-7, 36), g.Q(-7, 28)])
    else:
        tor = cv.poly([g.Q(-5, 22), g.Q(3, 22), g.Q(7, 26), g.Q(8, 31), g.Q(6.5, 37), g.Q(7, 46.5), g.Q(-7.5, 46.5), g.Q(-7, 36), g.Q(-7, 28)])
    cv.part("neck", cv.rect(*H(-2, 17), *H(2, 23.5)), sk, rad=2, bias=-0.15)
    cv.part("shirt", tor, tp, rad=7 * k + 1, soft=1.3, cuts=(0.28, 0.52, 0.84), tex=0.03 if b and st in ("hoodie", "coat") else 0, seed=7)
    sid = cv.names["shirt"]
    if st == "hoodie":
        hood = cv.ell(*g.Q(-4.5, 25), 4.6 * k, 4.4 * g.bk) & (cv.Y > g.Y(21.6))
        cv.part("hood", hood, tp, edge="dark", lv=np.where(hood, 2, 0) + np.where(hood & (cv.Y < g.Y(24)), 1, 0))
        if b:
            y = int(round(g.Y(47.8)))
            for yy in range(y, int(round(g.Y(49.2))) + 1):
                for x in range(cv.w):
                    if cv.own[yy, x] == sid and x % 2 == 0 and tuple(cv.col[yy, x]) != tp[0]:
                        cv.put(x, yy, tp[1])
    if st == "coat":
        tn = cv.rect(*H(-2.6, 18.4), *H(2.8, 23.4))
        cv.part("tneck", tn, ch["under"], rad=2, cuts=(0.25, 0.5, 0.85), bias=0.1)
        if b:
            cv.hline(int(round(g.X(2))), int(round(g.X(6.5))), int(round(g.Y(53))), tp[0])
            cv.line(*ipt(g.Q(3.2, 23.4)), *ipt(g.Q(5.4, 30)), tp[0])
            y = int(round(g.Y(44)))
            cv.hline(int(round(g.X(-7))), int(round(g.X(-3))), y, tp[0])
    if st == "blazer":
        if b:
            cv.line(*ipt(g.Q(2.6, 22.6)), *ipt(g.Q(6.2, 33)), tp[0])
            cv.put(*ipt(g.Q(3.4, 23.4)), RAMP["white"][3]); cv.put(*ipt(g.Q(4.0, 24.6)), RAMP["white"][2])
    if st == "jersey" and b:
        cv.line(*ipt(g.Q(1.0, 22.4)), *ipt(g.Q(3.0, 25.0)), RAMP["white"][3])
        x = int(round(g.X(0)))
        for y in range(int(g.Y(28)), int(g.Y(46))):
            if cv.own[y, x] == sid:
                cv.put(x, y, RAMP["white"][2])
    # arm + prop
    ap = [g.Q(-0.5, 25.5), g.Q(0.6, 35.5), g.Q(2.4, 43)]
    hp = g.Q(3.0, 44.6)
    if cid == "business_major":
        arm(cv, g, ch, "arm", [g.Q(-0.5, 25.5), g.Q(0.4, 35.5), g.Q(5.0, 39.5)])
        coffee(cv, *g.Q(6.6, 39.4), 1.0 if b else 0.62)
        hand(cv, g, ch, *g.Q(6.0, 39.6), "hand")
    elif cid == "engineering_major":
        robot(cv, *g.Q(4.6, 41.5), 0.92 if b else 0.6)
        arm(cv, g, ch, "arm", [g.Q(-0.5, 25.5), g.Q(-1.0, 34), g.Q(3.2, 42)])
        hand(cv, g, ch, *g.Q(3.6, 42.4), "hand", r=2.5)
    elif cid == "philosophy_major":
        arm(cv, g, ch, "arm", [g.Q(-0.5, 25.5), g.Q(0.2, 35), g.Q(1.8, 40.5)])
        book(cv, *g.Q(1.6, 39.6), 1.0 if b else 0.62, kind="closed", ang=0.0)
        hand(cv, g, ch, *g.Q(2.6, 41.4), "hand")
    else:
        arm(cv, g, ch, "arm", ap)
        disc(cv, *g.Q(4.2, 46.0), 1.0 if b else 0.62, ang=1.25, flat=1.0)
        hand(cv, g, ch, *hp, "hand")
    # head (profile)
    if ch["ears"]:
        pass
    head = cv.ell(*H(1, 13.4), 7.2 * s, 7.4 * s) | cv.ell(*H(3, 16), 5 * s, 6.6 * s) | cv.ell(*H(4.6, 19.5), 3.4 * s, 3 * s)
    cv.part("head", head, sk, rad=6 * s, soft=1.2, cuts=(0.22, 0.48, 0.86), bias=0.10)
    if b:
        cv.part("nose", cv.ell(*H(8.6, 15.6), 1.6, 1.5), sk, edge="ink", noedge=("head",), rad=1.5, bias=0.15)
    hs = ch["hair_style"]
    ybs = t + (8 + 0.22 * (c + 7 * s - cv.X) / s) * s
    if hs == "ponytail":
        hair = cv.ell(*H(-0.5, 10.6), 8.6 * s, 10.3 * s) & ((cv.X < c - 1 * s) | (cv.Y < ybs - 0.5 * s))
        cv.part("hair", hair, hr, noedge=("tail",), rad=5 * s, soft=1.0, cuts=(0.24, 0.5, 0.84))
        if b:
            cv.line(c + 6, t + 5, c - 4, t + 4, hr[3]); cv.line(c + 4, t + 7, c - 6, t + 6, hr[1])
        sc = cv.ell(*H(-6.4, 4.2), 1.7 * s + 0.2, 2.0 * s + 0.2)
        cv.part("scrunchie", sc, ch["top"], edge="dark", lv=np.where(sc, 3, 0))
    elif hs == "twists":
        hair = (cv.ell(*H(-0.5, 9.5), 8.6 * s, 9.3 * s) | (cv.rect(*H(-8, 0.6), *H(7, 8)) & cv.ell(*H(-0.5, 5.5), 8.9 * s, 8.6 * s)))
        hair &= (cv.X < c - 0.5 * s) | (cv.Y < ybs - 0.5 * s)
        hair &= ~cv.ell(*H(5.5, 15), 4.5 * s, 5 * s)
        cv.part("hair", hair, hr, rad=5 * s, soft=1.0, cuts=(0.24, 0.5, 0.84))
        if b:
            pid = cv.names["hair"]
            for y in range(t + 1, t + 9, 2):
                for x in range(c - 9, c + 8):
                    if cv.own[y, x] == pid and (x + (y - t) // 2) % 2 == 0 and tuple(cv.col[y, x]) != hr[0]:
                        cv.put(x, y, hr[3])
    elif hs == "beret":
        hair = cv.ell(*H(-0.5, 10.5), 8.8 * s, 9.6 * s) & ((cv.X < c + 0.5 * s) | (cv.Y < ybs + 0.5 * s))
        cv.part("hair", hair, hr, noedge=("curls",), rad=5 * s, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.08 if b else 0, seed=46)
        curl_texture(cv, "hair", hr, b)
        brt = cv.ell(*H(0.6, 4.4), 10.4 * s, 4.2 * s, -0.12) & (cv.Y < t + 8 * s - 0.12 * (cv.X - c))
        cv.part("beret", brt, ch["beret"], edge="dark", rad=3 * s, soft=1.0, cuts=(0.26, 0.5, 0.82))
        cv.put(int(round(c)), t, ch["beret"][2])
    elif hs == "puff":
        hair = cv.ell(*H(-0.5, 10.6), 8.4 * s, 9.8 * s) & ((cv.X < c - 1 * s) | (cv.Y < ybs - 0.5 * s))
        cv.part("hair", hair, hr, noedge=("puff",), rad=5 * s, soft=1.0, cuts=(0.24, 0.5, 0.84))
        band = cv.ell(*H(-0.5, 11.6), 9.0 * s, 10.4 * s) & (cv.Y >= ybs - 1.6 * s) & (cv.Y < ybs + 0.4 * s) & (cv.X < c + 7.6 * s)
        cv.part("band", band, "white", edge="dark", lv=np.where(band, 3, 0))
    if ch["ears"]:
        e = cv.ell(*H(-1.2, 14.6), 1.6 * s + 0.2, 2.2 * s + 0.2)
        cv.part("ear", e, sk, edge="dark", lv=np.where(e, 2, 0))
    # face details
    if b:
        ey = t + 13
        cv.hline(c + 4, c + 6, ey, EYE); cv.put(c + 5, ey + 1, ch["iris"]); cv.put(c + 6, ey + 1, ch["iris_d"])
        if ch["fem"]:
            cv.put(c + 7, ey - 1, EYE)
        cv.hline(c + 4, c + 6, ey - 2, hr[1])
        cv.put(c + 6, t + 19 + (1 if hs == "beret" else 0), MOUTH); cv.put(c + 7, t + 19 + (1 if hs == "beret" else 0), MOUTH)
        if hs == "twists":
            hid = cv.names["head"]
            for y in range(t + 15, t + 24):
                for x in range(c - 2, c + 9):
                    if cv.own[y, x] == hid and tuple(cv.col[y, x]) != sk[0] and (x < c + 3 or y >= t + 21):
                        cv.put(x, y, hr[1])
            cv.hline(c + 6, c + 8, t + 18, hr[1])
            for x in range(c + 3, c + 9):
                cv.put(x, ey - 1, FRAME); cv.put(x, ey + 2, FRAME)
            cv.vline(c + 3, ey - 1, ey + 2, FRAME); cv.vline(c + 8, ey - 1, ey + 2, FRAME)
            cv.hline(c - 1, c + 2, ey, FRAME)
        if hs == "beret":
            hid = cv.names["head"]
            for y in range(t + 18, t + 24):
                for x in range(c - 1, c + 9):
                    if cv.own[y, x] == hid and tuple(cv.col[y, x]) != sk[0]:
                        cv.put(x, y, mix(cv.get(x, y), hr[1], 0.38))
            ring = cv.ell(c + 5.6, ey + 0.6, 2.2, 2.4) & ~cv.ell(c + 5.6, ey + 0.6, 1.2, 1.4)
            cv.col[ring] = RAMP["gold"][2]
            cv.hline(c - 1, c + 3, ey, RAMP["gold"][1])
            cv.puts([(c + 6, t + 16), (c + 4, t + 17), (c + 7, t + 17)], (200, 120, 90))
        if hs == "ponytail" or hs == "puff":
            cv.put(c - 1, t + 17, RAMP["gold"][3])
        if ch.get("blush") and hs != "beret":
            cv.put(c + 5, t + 16, mix(sk[2], ch["blush"], 0.5))
    else:
        ey = t + 8
        cv.put(c + 3, ey, EYE); cv.put(c + 3, ey + 1, EYE)
        cv.put(c + 4, t + 12 + (1 if hs == "beret" else 0), MOUTH)
        if hs == "twists":
            cv.puts([(c + 2, ey - 1), (c + 3, ey - 1), (c + 4, ey - 1), (c + 1, ey), (c, ey)], FRAME)
            for (x, y) in ((c + 1, t + 11), (c + 2, t + 12), (c + 1, t + 12), (c + 3, t + 13), (c + 2, t + 13)):
                if cv.alpha[y, x]:
                    cv.put(x, y, hr[1])
        if hs == "beret":
            cv.puts([(c + 2, ey - 1), (c + 4, ey - 1), (c + 2, ey + 2), (c + 4, ey + 2), (c + 1, ey)], RAMP["gold"][2])
            cv.puts([(c + 3, t + 14), (c + 2, t + 14)], hr[2])
    cv.outline()
    return cv


def back(cid, battle=True):
    ch = CHARS[cid]
    g = G(ch, battle)
    cv = Cv(g.CW, g.CH)
    c, t = g.c, g.t
    k, s = g.wk, g.hk
    b = battle
    sk, hr, tp = ch["skin"], ch["hair"], ch["top"]
    H = lambda dx, dy: (c + dx * s, t + dy * s)
    legs_front(cv, g, ch, back=True)
    torso_front(cv, g, ch, back=True)
    # props peeking out at the sides (her right = viewer right from behind)
    if cid == "business_major":
        arm(cv, g, ch, "armL", [g.Q(-10.3, 25.5), g.Q(-12.8, 36), g.Q(-12.4, 44)])
        hand(cv, g, ch, *g.Q(-12.4, 45.2), "handL")
        coffee(cv, *g.Q(11.2, 40.4), 1.0 if b else 0.62)
        arm(cv, g, ch, "armR", [g.Q(10.3, 25.5), g.Q(13.8, 35), g.Q(11.0, 40.5)])
        hand(cv, g, ch, *g.Q(11.2, 40.6), "handR")
    elif cid == "engineering_major":
        arm(cv, g, ch, "armL", [g.Q(-10.6, 25.5), g.Q(-15.4, 34.5), g.Q(-15.6, 42.6)])
        robot(cv, *g.Q(-16.4, 36.8), 0.92 if b else 0.6)
        hand(cv, g, ch, *g.Q(-15.8, 43.8), "handL", r=2.5)
        arm(cv, g, ch, "armR", [g.Q(10.6, 25.5), g.Q(13.4, 35.5), g.Q(12.8, 44)])
        hand(cv, g, ch, *g.Q(12.8, 45.2), "handR", r=2.5)
    elif cid == "philosophy_major":
        arm(cv, g, ch, "armL", [g.Q(-10.4, 25.5), g.Q(-12.8, 36), g.Q(-9.8, 46.5)])
        arm(cv, g, ch, "armR", [g.Q(10.4, 25.5), g.Q(14.2, 34.5), g.Q(12.2, 41)])
        book(cv, *g.Q(12.6, 41.6), 1.0 if b else 0.62, kind="closed")
        hand(cv, g, ch, *g.Q(11.8, 41.4), "handR")
    else:
        arm(cv, g, ch, "armR", [g.Q(10.3, 25.5), g.Q(16.6, 34.5), g.Q(11.6, 43)])
        hand(cv, g, ch, *g.Q(11.4, 43.2), "handR")
        arm(cv, g, ch, "armL", [g.Q(-10.3, 25.5), g.Q(-13.6, 35), g.Q(-13.2, 43.4)])
        disc(cv, *g.Q(-15.2, 44.6), 1.0 if b else 0.62, ang=0.0, flat=2.3)
        hand(cv, g, ch, *g.Q(-13.4, 43.4), "handL")
    # head from behind
    hs = ch["hair_style"]
    if ch["ears"]:
        for sd in (-1, 1):
            e = cv.ell(*H(sd * (ch["facew"] + 0.2), 14.6), 1.7 * s, 2.3 * s)
            cv.part("ear%d" % sd, e, sk, edge="dark", lv=np.where(e, 2, 0))
    nape = cv.ell(*H(0, 15), ch["facew"] * s, 7 * s)
    cv.part("nape", nape, sk, rad=4, cuts=(0.3, 0.55, 0.9), bias=-0.1)
    if hs == "ponytail":
        hb = cv.ell(*H(0, 10.6), 8.6 * s, 10.4 * s) & (cv.Y < t + 17 * s)
        cv.part("hairback", hb, hr, rad=6 * s + 1, soft=1.0, cuts=(0.26, 0.52, 0.86))
        hair_back(cv, ch, c, t, s, "back")
        sc = cv.ell(*H(0, 3.6), 2.2 * s + 0.2, 1.6 * s + 0.2)
        cv.part("scrunchie", sc, ch["top"], edge="dark", lv=np.where(sc, 3, 0))
        if b:
            for x0 in (-6, -3, 3, 6):
                cv.line(int(round(c + x0)), t + 14, c + (1 if x0 > 0 else -1), t + 5, hr[1])
    elif hs == "twists":
        hb = (cv.ell(*H(0, 9.5), 8.6 * s, 9.3 * s) | (cv.rect(*H(-7.6, 0.6), *H(7.6, 8)) & cv.ell(*H(0, 5.5), 8.9 * s, 8.6 * s)))
        hb |= cv.ell(*H(0, 13), (ch["facew"] + 0.4) * s, 6 * s) & (cv.Y < t + 17 * s)
        cv.part("hairback", hb, hr, rad=5 * s, soft=1.0, cuts=(0.24, 0.5, 0.84))
        pid = cv.names["hairback"]
        rows = range(t + 1, t + 16, 2) if b else range(t + 1, t + 10, 2)
        for y in rows:
            for x in range(c - 9, c + 10):
                if cv.own[y, x] == pid and tuple(cv.col[y, x]) != hr[0] and (x + (y - t) // 2) % 2 == 0:
                    cv.put(x, y, hr[3] if x < c else hr[2])
        hood = cv.ell(*g.Q(0, 24.5), 6.6 * k, 3.0 * g.bk)
        cv.part("hoodtop", hood, tp, edge="dark", lv=np.where(hood, 3, 0))
    elif hs == "beret":
        hair_back(cv, ch, c, t, s, "back")
        brt = cv.ell(*H(1.0, 4.6), 10.2 * s, 4.5 * s, 0.10) & (cv.Y < t + 8.0 * s + 0.10 * (cv.X - c))
        cv.part("beret", brt, ch["beret"], edge="dark", rad=3 * s, soft=1.0, cuts=(0.26, 0.5, 0.82))
        cv.put(int(round(c + 1)), t, ch["beret"][2])
        tn = cv.rect(*H(-3.8, 19.5), *H(3.8, 23.4))
        cv.part("tneck", tn, ch["under"], rad=2, cuts=(0.25, 0.5, 0.85))
    elif hs == "puff":
        hb = cv.ell(*H(0, 10.6), 8.4 * s, 9.8 * s) & (cv.Y < t + 17 * s)
        cv.part("hairback", hb, hr, rad=5 * s, soft=1.0, cuts=(0.24, 0.5, 0.84))
        hair_back(cv, ch, c, t, s, "back")
        band = cv.ell(*H(0, 12), 9.2 * s, 10.4 * s) & (cv.Y >= t + 9.0 * s) & (cv.Y < t + 10.8 * s)
        cv.part("band", band, "white", edge="dark", lv=np.where(band, 3, 0))
        if b:
            for x0 in (-6, -3, 0, 3, 6):
                cv.line(int(round(c + x0)), t + 15, c + int(x0 * 0.4), t + 6, hr[1])
    cv.outline()
    return cv


# ==========================================================================
# PORTRAITS 64x64
# ==========================================================================
PW = PH = 64
EXPRS = ("neutral", "warm", "concern", "surprised")


def p_eye(cv, ch, ex, ey, expr, side):
    maps = {
        "neutral":   ["..KKKK.",
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
    pal = {"K": EYE, "I": ch["iris"], "D": ch["iris_d"], "H": WHITE, "W": SCLERA, "S": ch["skin"][1]}
    rows = maps[expr]
    for j, row in enumerate(rows):
        for i, chh in enumerate(row):
            if chh == ".":
                continue
            x = ex + i if side < 0 else ex + (6 - i)
            col = pal[chh]
            if chh == "H" and side > 0:
                col = ch["iris"]
            cv.put(x, ey + j, col)
    if side > 0:
        for j, row in enumerate(rows):
            if "H" in row:
                i = row.index("H")
                cv.put(ex + (6 - i) - 2, ey + j, WHITE)
    if ch["fem"]:
        # lashes flick out at the outer corner
        top = 0 if expr != "warm" else 2
        if expr == "warm":
            ox = ex - 1 if side < 0 else ex + 7
            cv.put(ox, ey + 3, EYE)
        else:
            ox = ex if side < 0 else ex + 6
            ox2 = ex - 1 if side < 0 else ex + 7
            cv.put(ox, ey + top, EYE); cv.put(ox2, ey + top - 1, EYE)


def p_brows(cv, ch, c, by, expr):
    hr = ch["hair"]
    if expr == "concern":
        left = [(-11, 0), (-10, 0), (-9, -1), (-8, -1), (-7, -2), (-6, -2), (-5, -3)]
    elif expr == "surprised":
        left = [(-12, 0), (-11, -1), (-10, -2), (-9, -2), (-8, -2), (-7, -2), (-6, -1)]
    elif expr == "warm":
        left = [(-12, 1), (-11, 0), (-10, -1), (-9, -1), (-8, -1), (-7, -1), (-6, 0)]
    else:
        left = [(-12, 1), (-11, 0), (-10, 0), (-9, 0), (-8, 0), (-7, 0), (-6, 1)]
    thick = not ch["fem"]
    c0, c1 = (hr[1], hr[0]) if ch["hair_style"] != "beret" else (hr[1], hr[0])
    for side in (-1, 1):
        for i, (dx, dy) in enumerate(left):
            x = c + dx if side < 0 else c - dx
            cv.put(x, by + dy, c0 if side < 0 else c1)
            if 0 < i < 6 and (thick or i < 4):
                cv.put(x, by + dy - 1, hr[2] if side < 0 else hr[1])


def p_mouth(cv, ch, c, my, expr, talk=False):
    sk = ch["skin"]
    lip = mix(sk[2], ch["lip"], 0.65) if ch["fem"] else sk[1]
    if expr == "neutral":
        cv.put(c - 4, my - 1, MOUTH); cv.put(c + 4, my - 1, MOUTH)
        if not talk:
            cv.hline(c - 3, c + 3, my, MOUTH)
            cv.hline(c - 2, c + 2, my + 1, lip)
        else:
            cv.hline(c - 3, c + 3, my, MOUTH); cv.hline(c - 2, c + 2, my, TEETH)
            cv.hline(c - 3, c + 3, my + 1, MOUTH); cv.hline(c - 1, c + 1, my + 1, TONGUE)
            cv.hline(c - 2, c + 2, my + 2, lip)
    elif expr == "warm":
        cv.put(c - 7, my - 2, MOUTH); cv.put(c + 7, my - 2, MOUTH)
        cv.hline(c - 6, c + 6, my - 1, MOUTH)
        cv.hline(c - 5, c + 5, my, TEETH); cv.put(c - 6, my, MOUTH); cv.put(c + 6, my, MOUTH)
        if not talk:
            cv.hline(c - 5, c + 5, my + 1, MOUTH); cv.hline(c - 2, c + 2, my + 1, TONGUE)
            cv.hline(c - 3, c + 3, my + 2, lip)
        else:
            cv.hline(c - 5, c + 5, my + 1, MOUTH); cv.hline(c - 4, c + 4, my + 2, MOUTH)
            cv.hline(c - 2, c + 2, my + 2, TONGUE); cv.hline(c - 1, c + 1, my + 1, TONGUE)
            cv.hline(c - 3, c + 3, my + 3, lip)
    elif expr == "concern":
        cv.hline(c - 3, c + 3, my, MOUTH)
        cv.put(c - 4, my + 1, MOUTH); cv.put(c + 4, my + 1, MOUTH)
        if not talk:
            cv.hline(c - 2, c + 2, my + 1, lip)
        else:
            cv.hline(c - 3, c + 3, my + 1, MOUTH); cv.hline(c - 1, c + 1, my + 1, TONGUE)
            cv.hline(c - 2, c + 2, my + 2, lip)
    elif expr == "surprised":
        rows = ((0, 1), (1, 2), (2, 2), (3, 1)) if not talk else ((0, 1), (1, 2), (2, 2), (3, 2), (4, 1))
        for dy, w in rows:
            cv.hline(c - w, c + w, my + dy - 1, MOUTH)
        cv.hline(c - 1, c + 1, my + len(rows) - 2, TONGUE)
        cv.hline(c - 1, c + 1, my + len(rows) - 1, lip)


def p_clothes(cv, ch, c):
    sk, tp = ch["skin"], ch["top"]
    st = ch["top_style"]
    if st == "hoodie":
        hood = cv.ell(c, 50, 19, 7.5) & cv.half(y=44)
        cv.part("hoodback", hood, tp, edge="dark", lv=np.where(hood, 1, 0) + np.where(hood & (cv.Y < 47), 1, 0))
    sh = cv.ell(c, 76, 33 if st == "hoodie" else 31, 26) & cv.half(y=48)
    if st == "coat":
        cv.part("shoulders", sh, tp, rad=14, soft=2.0, cuts=(0.34, 0.6, 0.9), tex=0.03, seed=3)
    else:
        cv.part("shoulders", sh, tp, rad=14, soft=2.0, cuts=(0.34, 0.6, 0.9), tex=0.04 if st == "hoodie" else 0, seed=3)
    cv.part("neck", cv.rect(c - 5, 38, c + 5, 52), sk, rad=4, bias=-0.18)
    if st == "blazer":
        shell = cv.poly([(c - 8, 48), (c + 8, 48), (c + 2, 64), (c - 2, 64)]) & ~cv.ell(c, 46, 5.4, 4.4)
        cv.part("shell", shell, "white", edge="dark", lv=np.where(shell, 3, 0) - np.where(shell & (cv.X > c + 2), 1, 0))
        for s in (-1, 1):
            lap = cv.poly([(c + s * 8, 47.5), (c + s * 14, 50), (c + s * 10, 56), (c + s * 12, 58), (c + s * 3, 64), (c + s * 2, 64)])
            cv.part("lapel%d" % s, lap, tp, edge="dark", lv=np.where(lap, 3 if s < 0 else 2, 0))
        cv.puts([(c - 1, 56), (c, 57)], RAMP["gold"][3])                  # tiny gold pendant
        cv.put(c, 56, RAMP["gold"][2])
    elif st == "hoodie":
        ring = cv.ell(c, 50.5, 12.5, 5.2) & ~cv.ell(c, 49.5, 7.6, 3.6)
        cv.part("hoodring", ring, tp, edge="dark", lv=np.where(ring, 2, 0) + np.where(ring & (cv.X < c - 3), 1, 0))
        for s in (-1, 1):
            x = c + s * 5
            cv.vline(x, 54, 62, RAMP["white"][3]); cv.vline(x + s, 54, 62, RAMP["white"][1])
            cv.put(x, 63, FRAME); cv.put(x + s, 63, FRAME)
    elif st == "coat":
        un = ch["under"]
        tn = cv.ell(c, 47, 9.4, 9) & cv.half(y=39)
        tn |= cv.rect(c - 7, 52, c + 7, 64)
        cv.part("tneck", tn, un, rad=5, soft=1.0, cuts=(0.25, 0.5, 0.85), bias=0.08)
        for y in (42, 45, 48):
            cv.hline(c - 7, c + 7, y, un[3] if y < 46 else un[2])
        for s in (-1, 1):
            lap = cv.poly([(c + s * 8, 54), (c + s * 16, 52), (c + s * 13, 58), (c + s * 15, 60), (c + s * 8, 64)])
            cv.part("lapel%d" % s, lap, tp, edge="dark", lv=np.where(lap, 3 if s < 0 else 2, 0))
    elif st == "jersey":
        vn = cv.poly([(c - 7, 48), (c + 7, 48), (c, 59)])
        cv.part("vneck", vn, sk, edge=None, rad=4, bias=-0.1)
        for s in (-1, 1):
            cv.line(c + s * 7, 48, c, 59, RAMP["white"][3] if s < 0 else RAMP["white"][2])
            cv.line(c + s * 8, 48, c + s, 60, RAMP["white"][2] if s < 0 else RAMP["white"][1])
        for s in (-1, 1):
            cv.line(c + s * 20, 52, c + s * 26, 64, RAMP["white"][2])


def p_hair_back(cv, ch, c, lift):
    hr = ch["hair"]
    st = ch["hair_style"]
    if st == "ponytail":
        m = cv.capsule(c + 13, 12 + lift, c + 21, 26, 5.2, 4.0) | cv.capsule(c + 21, 26, c + 22, 50, 4.0, 2.0)
        cv.part("tail", m, hr, rad=5, soft=1.0, cuts=(0.28, 0.54, 0.86))
        cv.line(c + 16, 16, c + 21, 40, hr[3]); cv.line(c + 19, 18, c + 23, 34, hr[1])
    elif st == "beret":
        m = cv.ell(c, 30 + lift, 20, 16)
        for i in range(14):
            a = math.pi * (-0.1 + 1.2 * i / 13)
            m |= cv.ell(c + math.cos(a) * 19, 30 + lift + math.sin(a) * 14, 4.6, 4.6)
        cv.part("curls", m, hr, rad=8, soft=1.4, cuts=(0.30, 0.56, 0.88), bias=-0.06, tex=0.08, seed=41)
        curl_texture(cv, "curls", hr, True)
    elif st == "puff":
        m = cv.ell(c + 1, 7 + lift, 14, 6.6)
        for (dx, dy, r) in ((-11, 7, 4.4), (-6, 3.6, 4.4), (0, 2.6, 4.6), (6, 3.2, 4.4), (11.5, 6, 4.2), (14, 10, 3.6), (-13, 11, 3.6)):
            m |= cv.ell(c + dx, dy + lift, r, r)
        cv.part("puff", m, hr, rad=8, soft=1.4, cuts=(0.28, 0.54, 0.86), tex=0.1, seed=43)
        curl_texture(cv, "puff", hr, True)


def p_hair_front(cv, ch, c, lift):
    hr, sk = ch["hair"], ch["skin"]
    st = ch["hair_style"]
    fid = cv.names["face"]
    if st == "ponytail":
        yb = 15.0 + lift + 0.03 * (cv.X - c) ** 2
        crown = cv.ell(c, 20 + lift, 16.6, 17.8) & (cv.Y < yb + 1)
        for s in (-1, 1):
            crown |= cv.capsule(c + s * 14, 16, c + s * 14.6, 25, 2.2)
        cv.part("crown", crown, hr, noedge=("tail",), rad=8, soft=1.4, cuts=(0.24, 0.5, 0.84))
        bangs = cv.poly([(c - 7, 3 + lift), (c + 6, 4 + lift), (c + 15, 13 + lift), (c + 16, 25), (c + 12, 21 + lift),
                         (c + 6, 18 + lift), (c - 1, 16.5 + lift), (c - 7, 15 + lift)])
        lock = cv.capsule(c - 9, 13 + lift, c - 13.5, 24, 2.0, 1.4)
        cv.part("lock", lock, hr, noedge=("crown",), rad=2, soft=0.8, cuts=(0.30, 0.56, 0.88))
        cv.part("bangs", bangs, hr, noedge=("crown",), rad=5, soft=1.0, cuts=(0.30, 0.56, 0.88))
        for x in range(c - 13, c + 8):
            y = int(round(7.5 + lift + 0.035 * (x - c + 3) ** 2))
            if cv.own[y, x] in (cv.names["crown"], cv.names["bangs"]):
                cv.put(x, y, hr[4] if c - 9 <= x <= c - 3 else hr[3])
                cv.put(x, y + 1, hr[3] if c - 9 <= x <= c - 3 else hr[2])
        for (x0, y0, x1, y1) in ((c - 6, 5, c + 12, 15), (c - 2, 7, c + 13, 19), (c - 4, 9, c + 6, 15)):
            cv.line(x0, y0 + lift, x1, y1 + lift, hr[1])
        sc = cv.ell(c + 13, 9 + lift, 3.2, 2.6)
        cv.part("scrunchie", sc, ch["top"], edge="dark", lv=np.where(sc, 3, 0) - np.where(sc & (cv.X > c + 14), 1, 0))
    elif st == "twists":
        yb = 12.5 + lift + 0.022 * (cv.X - c) ** 2
        top = (cv.ell(c, 18 + lift, 16.5, 16) | (cv.rect(c - 14.5, 1 + lift, c + 14.5, 14) & cv.ell(c, 12 + lift, 17.2, 16.6))) & (cv.Y < yb + 1)
        side = cv.ell(c, 26, 15.4, 16) & (np.abs(cv.X - c) >= 12) & (cv.Y < 30)
        cv.part("crown", top | side, hr, rad=8, soft=1.2, cuts=(0.24, 0.5, 0.84))
        pid = cv.names["crown"]
        for y in range(2 + lift, 13 + lift, 3):
            for x in range(c - 15, c + 16):
                if cv.own[y, x] == pid and ((x + (y // 3) * 2) % 4 == 0):
                    cv.put(x, y, hr[3] if x < c + 4 else hr[2]); cv.put(x, y + 1, hr[3] if x < c else hr[2])
                    if cv.own[y + 2, x] == pid:
                        cv.put(x, y + 2, hr[1])
        for y in range(14, 30):
            for x in range(c - 17, c + 18):
                if cv.own[y, x] == pid and abs(x - c) >= 12:
                    cv.put(x, y, mix(cv.get(x, y), sk[1], 0.25))
    elif st == "beret":
        yb = 16.0 + lift + 0.03 * (cv.X - c) ** 2
        crown = cv.ell(c, 20 + lift, 17.6, 17.6) & (cv.Y < yb + 1)
        cv.part("crown", crown, hr, noedge=("curls",), rad=8, soft=1.4, cuts=(0.28, 0.54, 0.86), tex=0.08, seed=45)
        fr = cv.empty()
        for (dx, dy) in ((-12, 16), (-7, 17), (-2, 16), (3, 17), (8, 16), (13, 18), (-15, 21), (15, 22)):
            fr |= cv.ell(c + dx, dy + lift, 3.0, 2.8)
        cv.part("fringe", fr & ~cv.ell(c, 34, 10, 12), hr, noedge=("crown", "curls"), rad=3, soft=0.8, cuts=(0.28, 0.54, 0.86))
        curl_texture(cv, "crown", hr, True)
        curl_texture(cv, "fringe", hr, True)
        br = cv.ell(c - 2, 8 + lift, 20, 8.4, -0.10) & (cv.Y < 14.5 + lift - 0.10 * (cv.X - c))
        cv.part("beret", br, ch["beret"], edge="dark", rad=5, soft=1.2, cuts=(0.26, 0.5, 0.82))
        bid = cv.names["beret"]
        cv.puts([(c - 3, 0 + lift), (c - 2, 0 + lift), (c - 3, 1 + lift)], ch["beret"][2]) if lift == 0 else cv.puts([(c - 3, 0), (c - 2, 0)], ch["beret"][2])
        for x in range(c - 22, c + 20):
            for y in range(20, 2, -1):
                if 0 <= x < cv.w and cv.own[y, x] == bid:
                    cv.put(x, y, ch["beret"][1]); cv.put(x, y - 1, ch["beret"][2])
                    break
    elif st == "puff":
        yb = 15.6 + lift + 0.022 * (cv.X - c) ** 2
        crown = cv.ell(c, 20 + lift, 16.4, 17.6) & (cv.Y < yb + 1)
        cv.part("crown", crown, hr, noedge=("puff",), rad=8, soft=1.4, cuts=(0.24, 0.5, 0.84))
        for dx in (-12, -7, -2, 3, 8, 12):
            cv.line(c + dx, int(round(12 + lift + 0.02 * dx * dx)), c + int(dx * 0.4), 4 + lift, hr[1])
        cv.puts([(c - 8, 7 + lift), (c - 7, 6 + lift), (c - 6, 6 + lift), (c - 9, 8 + lift)], hr[4])
        yb2 = 15.0 + lift + 0.012 * (cv.X - c) ** 2
        band = cv.ell(c, 24 + lift, 18.0, 20) & (cv.Y >= yb2 - 3.4) & (cv.Y < yb2 + 0.4)
        cv.part("band", band, "white", edge="dark", lv=np.where(band, 3, 0) + np.where(band & (cv.Y < yb - 2), 1, 0) - np.where(band & (cv.X > c + 8), 1, 0))
        bid = cv.names["band"]
        for x in range(c - 18, c + 19):
            col = [y for y in range(0, 30) if cv.own[y, x] == bid]
            if len(col) >= 3:
                cv.put(x, col[len(col) // 2], RAMP["disc"][2])


def portrait(cid, expr, talk=False):
    ch = CHARS[cid]
    cv = Cv(PW, PH, open_bottom=True)
    c = 32
    sk, hr = ch["skin"], ch["hair"]
    st = ch["hair_style"]
    lift = -1 if expr == "surprised" else 0
    p_hair_back(cv, ch, c, lift)
    p_clothes(cv, ch, c)
    f = ch["facew"] / 7.2
    if ch["ears"]:
        for s in (-1, 1):
            e = cv.ell(c + s * 13.2 * f, 30, 2.8, 4.0)
            cv.part("ear%d" % s, e, sk, edge="dark", lv=np.where(e, 2, 0) + np.where(e & (cv.X < c), 1, 0))
    longer = 1.2 if st == "beret" else 0
    face = cv.ell(c, 28, 13.2 * f, 13.6) | cv.ell(c, 33, 11.2 * f, 12.4 + longer) | cv.ell(c, 38 + longer, 11.6 * f * (0.92 if ch["fem"] else 1.0), 8.2)
    cv.part("face", face, sk, rad=11, soft=2.2, cuts=(0.16, 0.42, 0.86), bias=0.06)
    fid = cv.names["face"]
    p_hair_front(cv, ch, c, lift)
    # cheeks / freckles / beard
    if ch.get("blush"):
        for s in (-1, 1):
            bx = c + s * 8
            for y in (34, 35):
                for x in range(bx - 2, bx + 3):
                    if cv.own[y, x] == fid:
                        cv.put(x, y, mix(cv.get(x, y), ch["blush"], 0.35 if abs(x - bx) < 2 else 0.18))
    if st == "beret":
        FR = (196, 110, 76)
        for (x, y) in ((c - 9, 31), (c - 7, 32), (c - 10, 33), (c - 6, 34), (c - 8, 35), (c + 7, 31), (c + 9, 32), (c + 6, 33),
                       (c + 8, 34), (c + 10, 34), (c - 2, 31), (c + 2, 30), (c - 4, 33), (c + 4, 32)):
            cv.put(x, y, mix(cv.get(x, y), FR, 0.6))
        for y in range(37, 50):
            for x in range(c - 12, c + 13):
                if cv.own[y, x] == fid and tuple(cv.col[y, x]) != sk[0] and (abs(x - c) >= 6 or y >= 45):
                    cv.put(x, y, mix(cv.get(x, y), hr[1], 0.36))
        goat = cv.ell(c, 47.2, 3.4, 2.4) & face
        cv.part("goatee", goat, hr, edge="dark", noedge=("face",), rad=2, soft=0.8, cuts=(0.28, 0.54, 0.86))
    if st == "twists":
        fm = cv.own == fid
        er = ndi.binary_erosion(fm, iterations=3)
        band = fm & ~er & (cv.Y >= 30)
        ys, xs = np.nonzero(band)
        for y, x in zip(ys, xs):
            if tuple(cv.col[y, x]) != sk[0]:
                cv.put(x, y, hr[2] if x < c else hr[1])
        for y in range(44, 49):
            for x in range(c - 3, c + 4):
                if cv.own[y, x] == fid and tuple(cv.col[y, x]) != sk[0]:
                    cv.put(x, y, hr[2] if x < c else hr[1])
        cv.hline(c - 5, c + 5, 38, hr[1]); cv.hline(c - 4, c + 4, 37, hr[2])
    # nose
    cv.puts([(c - 1, 28), (c - 1, 29), (c - 1, 30), (c - 1, 31)], sk[3])
    cv.puts([(c + 1, 31), (c + 1, 32), (c + 2, 33)], sk[1]); cv.puts([(c - 1, 34), (c, 34), (c + 1, 34)], sk[1])
    cv.put(c - 2, 33, sk[1])
    my = 41 if st != "beret" else 42
    if st == "twists":
        my = 41
    p_mouth(cv, ch, c, my, expr, talk)
    ey = {"neutral": 25, "warm": 25, "concern": 24, "surprised": 23}[expr]
    p_eye(cv, ch, c - 11, ey, expr, -1)
    p_eye(cv, ch, c + 4, ey, expr, 1)
    by = {"neutral": 22, "warm": 22, "concern": 22, "surprised": 20}[expr]
    p_brows(cv, ch, c, by, expr)
    if expr == "concern":
        cv.puts([(c - 1, 22), (c + 1, 22), (c, 23)], sk[1])
    # glasses
    if st == "twists":
        for side in (-1, 1):
            x0 = c - 13 if side < 0 else c + 3
            x1 = x0 + 10
            for x in range(x0, x1 + 1):
                for y in range(22, 31):
                    edge = x in (x0, x1) or y in (22, 30)
                    if edge:
                        cv.put(x, y, FRAME)
                        if y == 22 and x not in (x0, x1):
                            cv.put(x, y + 1, FRAME)
                    elif cv.own[y, x] == fid and tuple(cv.col[y, x]) not in (EYE, ch["iris"], ch["iris_d"], SCLERA, WHITE, hr[0], hr[1], hr[2]):
                        cv.put(x, y, mix(cv.get(x, y), RAMP["lens"][3], 0.2))
            xo = x0 - 1 if side < 0 else x1 + 1
            cv.put(xo, 24, FRAME); cv.put(xo + side, 24, FRAME)
        cv.hline(c - 2, c + 2, 24, FRAME)
        cv.puts([(c - 11, 27), (c - 10, 26), (c + 5, 27), (c + 6, 26)], WHITE)
    if st == "beret":
        gd = RAMP["gold"]
        for side in (-1, 1):
            ex = c - 7.5 if side < 0 else c + 7.5
            ring = cv.ell(ex, 26.5, 6.2, 5.6) & ~cv.ell(ex, 26.5, 5.0, 4.4)
            ys, xs = np.nonzero(ring)
            for y, x in zip(ys, xs):
                cv.put(x, y, gd[3] if (y < 25 and x < ex) else gd[2] if y < 28 else gd[1])
        cv.hline(c - 2, c + 2, 25, gd[2])
        cv.put(c - 14, 25, gd[1]); cv.put(c + 14, 25, gd[1])
    if ch["ears"] and ch["fem"]:
        for s in (-1, 1):
            x = int(round(c + s * 13.6 * f))
            cv.put(x, 34, RAMP["gold"][3]); cv.put(x, 35, RAMP["gold"][1])
    cv.outline()
    if expr == "warm":
        sparkle(cv, 6, 8)
    if expr == "surprised":
        cv.puts([(5, 14), (5, 15), (5, 16), (5, 18), (2, 16), (1, 15), (0, 14)], SPARK2)
    if expr == "concern":
        cv.puts([(13, 17), (12, 18), (13, 18), (14, 18), (13, 19)], SWEAT); cv.put(12, 18, SWEAT_HI)
    return cv


# ==========================================================================
# output
# ==========================================================================
CAST_REF = "/tmp/claude-0/designs/cast-reference.png"


def foot_point(cv):
    y = cv.h - 1
    shoe_ids = [pid for n, pid in cv.names.items() if n.startswith("shoe")]
    xs = [x for x in range(cv.w) if cv.alpha[y, x] and cv.own[y, x] in shoe_ids]
    if not xs:
        xs = [x for x in range(cv.w) if cv.alpha[y, x]]
    return [int(round((min(xs) + max(xs)) / 2)), y]


def body_height(img):
    a = np.array(img)[..., 3] > 0
    rows = np.nonzero(a.any(axis=1))[0]
    assert rows[-1] == img.height - 1, "feet not on bottom row"
    return int(img.height - rows[0])


def diff_box(a, b):
    d = np.any(np.array(a) != np.array(b), axis=2)
    ys, xs = np.nonzero(d)
    if len(xs) == 0:
        return None, 0
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), int(d.sum())


def build(cid):
    here = os.path.join(NEWCAST, cid)
    out = os.path.join(here, "out")
    for d in (out, os.path.join(out, "talk"), os.path.join(out, "idle")):
        os.makedirs(d, exist_ok=True)
    feet, cells, heights = {}, {}, {}
    battle = [front(cid, "idle"), front(cid, "talk"), front(cid, "tell"), front(cid, "hit"), side(cid), back(cid)]
    world = [front(cid, "idle", False), front(cid, "talk", False), front(cid, "tell", False), front(cid, "hit", False),
             side(cid, False), back(cid, False)]
    for prefix, group in (("battle", battle), ("world", world)):
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            heights[name] = body_height(img)
            img.save(os.path.join(out, name))
            feet[name] = foot_point(cv)
            cells[name] = img
    for i, e in enumerate(EXPRS):
        img = portrait(cid, e).image()
        img.save(os.path.join(out, "portrait-%d.png" % i))
        cells["portrait-%d.png" % i] = img
        t_img = portrait(cid, e, talk=True).image()
        box, n = diff_box(img, t_img)
        assert box and box[1] >= 36 and box[3] <= 48, ("talk diff outside the mouth", e, box)
        t_img.save(os.path.join(out, "talk", "%s-%d.png" % (cid, i)))
        cells["talk-%d.png" % i] = t_img
    base = cells["world-0.png"]
    for key, extra in zip(("blink", "pose1", "pose2"), ("blink",) + EXTRAS[cid]):
        img = front(cid, "idle", False, extra).image()
        assert img.size == base.size
        a0, a1 = np.array(base), np.array(img)
        assert (a0[-6:] == a1[-6:]).all(), (cid, key, "feet moved")
        box, n = diff_box(base, img)
        print(cid, "idle", key, extra, "changed", n, "px in", box)
        img.save(os.path.join(out, "idle", "%s-%s.png" % (cid, key)))
        cells["idle-%s.png" % key] = img
    meta = {"battle_height": heights["battle-0.png"], "world_height": heights["world-0.png"], "heights": heights}
    with open(os.path.join(out, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    with open(os.path.join(out, "heights.json"), "w") as f:
        json.dump(meta, f, indent=2)
    contact_sheet(cid, cells)
    print(cid, "heights", heights)
    return cells


def _font():
    from PIL import ImageFont
    return ImageFont.load_default()


def _up(im, S=3):
    return im.resize((im.width * S, im.height * S), Image.NEAREST)


def _rows_sheet(rows, title, path, ground_rows=(0, 1)):
    BG = (44, 44, 62, 255)
    GROUND = (70, 70, 96, 255)
    font = _font()
    pad = 12
    widths = [sum(im.width + pad for im, _ in r) + pad for r in rows]
    heights = [max(im.height for im, _ in r) + 26 for r in rows]
    W, H = max(widths), sum(heights) + pad * 2 + 20
    sheet = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    d.text((pad, 6), title, fill=(220, 220, 236, 255), font=font)
    y = pad + 20
    for ri, (r, rh) in enumerate(zip(rows, heights)):
        x = pad
        base = y + rh - 18
        if ri in ground_rows:
            d.rectangle([0, base, W, base + 1], fill=GROUND)
        for im, label in r:
            tp = base - im.height if ri in ground_rows else y
            sheet.alpha_composite(im, (x, tp))
            d.text((x, base + 4), label, fill=(200, 200, 220, 255), font=font)
            x += im.width + pad
        y += rh
    sheet.convert("RGB").save(path)


def contact_sheet(cid, cells, S=3):
    ref = Image.open(CAST_REF).convert("RGBA") if os.path.exists(CAST_REF) else None
    r1 = [(_up(cells["battle-%d.png" % i]), "battle-%d" % i) for i in range(6)]
    r2 = [(_up(cells["world-%d.png" % i]), "world-%d" % i) for i in range(6)]
    r2 += [(_up(cells["idle-%s.png" % k]), "idle " + k) for k in ("blink", "pose1", "pose2")]
    r3 = [(_up(cells["portrait-%d.png" % i]), "portrait-%d" % i) for i in range(4)]
    r3 += [(_up(cells["talk-%d.png" % i]), "talk-%d" % i) for i in range(4)]
    if ref is not None:
        r1.append((ref.crop((1440, 40, 1848, 285)), "cast: dev 80, jakerson 80"))
        r2.append((ref.crop((990, 320, 1520, 496)), "cast: jules, imani, dev (world)"))
        r3.append((ref.crop((830, 515, 1230, 708)), "cast: dev, jakerson"))
    _rows_sheet([r1, r2, r3], "%s (%s) -- 3x; route-trainer encounter, no entrance cell; cast crops from designs/cast-reference.png at the same 3x"
                % (CHARS[cid]["title"], cid), os.path.join(NEWCAST, cid, "sheet.png"))


def lineup(all_cells):
    ref = Image.open(CAST_REF).convert("RGBA") if os.path.exists(CAST_REF) else None
    r1, r2, r3 = [], [], []
    for cid in IDS:
        cells = all_cells[cid]
        r1.append((_up(cells["battle-0.png"]), cid + " battle"))
        r2.append((_up(cells["world-0.png"]), cid + " world"))
        r3.append((_up(cells["portrait-0.png"]), cid))
    if ref is not None:
        r1.append((ref.crop((0, 40, 240, 285)), "cast: eric 80"))
        r1.append((ref.crop((1440, 40, 1848, 285)), "cast: dev 80, jakerson 80"))
        r2.append((ref.crop((0, 320, 160, 496)), "eric (world)"))
        r2.append((ref.crop((990, 320, 1520, 496)), "cast: jules, imani, dev (world)"))
        r3.append((ref.crop((830, 515, 1230, 708)), "cast: dev, jakerson"))
    _rows_sheet([r1, r2, r3], "Encounter cast B -- business_major, engineering_major, philosophy_major, frisbee -- 3x, next to the cast",
                os.path.join(NEWCAST, "encounters-b-lineup.png"))


def main(argv):
    ids = [a for a in argv if a in IDS] or list(IDS)
    all_cells = {}
    for cid in ids:
        all_cells[cid] = build(cid)
    if len(ids) == len(IDS):
        lineup(all_cells)


if __name__ == "__main__":
    main(sys.argv[1:])
