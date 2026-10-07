#!/usr/bin/env python3
"""Random-encounter cast, batch C (athlete, professor, advisor_mini) --
procedural pixel-art sprites for "After Hours - College Tale".

ONE script draws all three ids (run it with an id, or with no argument for all three plus the lineup
/tmp/claude-0/newcast/encounters-c-lineup.png).  The raster engine (class Cv) is copied verbatim from
Professor Eric's draw_eric.py (via sunbeam and batch B, /tmp/claude-0/newcast/business_major/draw_encounters_b.py):
parts are masks shaded with material ramps from a top-left key light, given inner 1px lines and an ink
silhouette.  Everything is drawn at its final pixel size; nothing drawn is ever resampled (only the contact
sheets are nearest-neighbour blow-ups).

These are low-key route trainers, not gym leaders: everyday clothes, one clear prop each.
  athlete       big broad lineman: golden-tan skin, black flat-top with a faded back and sides, eye black,
                black team tee with gold trim, heather-grey joggers with a gold stripe, white socks + slides,
                a football tucked under his arm
  professor     short, round, older: deep-brown skin, short silver curls, gold half-moon reading glasses on a
                bead chain, terracotta cardigan over a cream top, turquoise bead necklace, olive midi skirt,
                ankle boots, a wooden pointer
  advisor_mini  junior academic advisor (much lower-key than Advisor Bev): slight build, neat black side part
                with a cowlick, pale-blue shirt under a sage sweater vest, orange lanyard + staff badge,
                navy chinos, loafers, a clipboard of forms

Per id, outputs in /tmp/claude-0/newcast/<id>/out/ (Eric's layout, NO entrance cell):
  battle-0..5.png   battle cells (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  world-0..5.png    world cells (same poses, redrawn small)
  portrait-0..3.png 64x64 portraits (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk/<id>-0..3.png   mouth-open portraits (only mouth pixels differ)
  idle/<id>-blink.png, <id>-pose1.png, <id>-pose2.png   world-front extras
  feet.json, heights.json
then build_sheet.py (one copy per id folder) packs <id>-v1.png + <id>-atlas.json + out/world/.
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

NEWCAST = "/tmp/claude-0/newcast"
IDS = ("athlete", "professor", "advisor_mini")

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



# extra materials for batch C
RAMP.update({
    "ball":  [(48, 22, 12), (104, 50, 26), (140, 72, 38), (172, 102, 58), (204, 140, 94)],
    "wood":  [(66, 38, 18), (120, 76, 40), (160, 110, 62), (194, 146, 92), (224, 188, 136)],
    "board": [(66, 42, 22), (122, 82, 44), (158, 114, 66), (188, 148, 94), (216, 184, 134)],
    "lany":  [(118, 48, 10), (194, 90, 24), (234, 126, 40), (250, 166, 80), (255, 204, 140)],
    "bead":  [(14, 80, 84), (30, 140, 146), (60, 186, 186), (120, 220, 214), (190, 246, 238)],
})
GOLD = RAMP["gold"]
TAPE = (236, 236, 242)
EYEBLACK = (22, 18, 26)
EYEBLACK_HI = (64, 60, 72)
STICK_TIP = (34, 28, 34)
PEN = (40, 70, 160)


# ==========================================================================
# CHARACTERS
# ==========================================================================
CHARS = {
    "athlete": dict(
        title="Athlete", hb=78, hw=52, build=1.32, fem=False, ears=True,
        skin=[(86, 48, 26), (160, 104, 64), (194, 138, 92), (220, 170, 122), (238, 198, 152)],
        hair=[(8, 6, 8), (22, 18, 20), (38, 32, 34), (60, 52, 56), (90, 80, 86)],
        iris=(74, 44, 26), iris_d=(26, 14, 8), lip=(140, 76, 60), blush=None,
        top=[(20, 20, 30), (40, 42, 56), (60, 62, 80), (86, 88, 110), (120, 122, 148)],        # black team tee
        pants=[(70, 72, 82), (118, 120, 132), (152, 154, 166), (184, 186, 196), (212, 214, 222)],  # heather joggers
        sock=[(120, 120, 140), (196, 198, 212), (226, 228, 236), (244, 244, 248), (255, 255, 255)],
        shoe=[(10, 10, 14), (24, 24, 30), (38, 38, 46), (58, 58, 68), (86, 86, 98)],
        hair_style="flattop", top_style="tee", legs_style="joggers", shoe_style="slides",
        facew=7.8, arm_r=3.3, tape=False),
    "professor": dict(
        title="Professor", hb=73, hw=50, build=1.12, fem=True, ears=True,
        skin=[(36, 20, 14), (86, 50, 34), (118, 74, 52), (148, 100, 72), (176, 130, 98)],
        hair=[(96, 96, 108), (152, 152, 164), (192, 192, 204), (222, 222, 232), (246, 246, 252)],  # silver
        brow=[(60, 58, 66), (104, 102, 112), (140, 138, 148), (170, 168, 178), (200, 198, 206)],
        iris=(80, 46, 26), iris_d=(30, 16, 8), lip=(122, 52, 66), blush=None,
        top=[(84, 34, 20), (150, 64, 38), (192, 96, 58), (220, 132, 86), (240, 172, 128)],     # terracotta cardigan
        under=[(140, 126, 100), (206, 194, 166), (230, 222, 198), (244, 238, 220), (254, 250, 240)],  # cream top
        pants=[(30, 40, 22), (58, 74, 40), (80, 100, 56), (108, 128, 78), (140, 160, 106)],     # olive skirt
        tights=[(24, 18, 26), (44, 32, 44), (62, 46, 60), (84, 64, 82), (112, 90, 108)],
        shoe=[(40, 20, 10), (84, 46, 22), (118, 70, 36), (152, 98, 56), (188, 136, 88)],
        hair_style="silver", top_style="cardigan", legs_style="skirt", shoe_style="boots",
        facew=7.2, arm_r=2.6),
    "advisor_mini": dict(
        title="Junior advisor", hb=74, hw=49, build=0.86, fem=False, ears=True,
        skin=[(110, 72, 44), (194, 148, 104), (222, 184, 138), (238, 206, 164), (250, 226, 192)],
        hair=[(10, 10, 18), (26, 26, 38), (44, 44, 60), (70, 72, 92), (104, 108, 130)],
        iris=(70, 44, 26), iris_d=(24, 14, 8), lip=(170, 104, 90), blush=(230, 140, 120),
        top=[(44, 64, 46), (82, 112, 82), (112, 144, 108), (144, 172, 136), (182, 204, 170)],    # sage sweater vest
        sleeve=[(90, 120, 160), (150, 182, 214), (186, 212, 236), (212, 230, 246), (236, 246, 255)],  # pale blue shirt
        pants=[(18, 22, 40), (36, 44, 72), (52, 62, 98), (74, 86, 126), (104, 116, 156)],        # navy chinos
        shoe=[(40, 20, 10), (92, 52, 26), (128, 78, 42), (164, 110, 66), (198, 150, 100)],
        hair_style="sidepart", top_style="vest", legs_style="trousers", shoe_style="loafers",
        facew=6.8, arm_r=2.3),
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
    cv.part(name, m, ramp or ch.get("sleeve") or ch["top"], edge="ink", rad=max(2, 3 * g.wk), soft=0.8,
            cuts=(0.28, 0.52, 0.86), bias=0.04)
    return m


def bare_arm(cv, g, ch, name, pts):
    """Athlete: bare arm with the tee's short sleeve cap (gold hem) and white wrist tape."""
    k = g.wk
    r = max(1.4, ch["arm_r"] * k)
    m = cv.chain(pts, r)
    cv.part(name, m, ch["skin"], edge="dark", rad=max(2, 3 * k), soft=0.8, cuts=(0.28, 0.52, 0.86), bias=0.04)
    (x0, y0), (x1, y1) = pts[0], pts[1]
    f = 0.42
    rs0, rs1 = max(2.0, (ch["arm_r"] + 0.5) * k), max(1.8, (ch["arm_r"] + 0.3) * k)
    sl = cv.capsule(x0, y0, x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, rs0, rs1)
    cv.part(name + "sl", sl, ch["top"], edge="dark", noedge=("shirt",), rad=3, soft=0.8, cuts=(0.30, 0.55, 0.88))
    # gold hem ring at the end of the sleeve
    fa, fb = f - (0.10 if g.battle else 0.12), f
    hem = cv.capsule(x0 + (x1 - x0) * fa, y0 + (y1 - y0) * fa, x0 + (x1 - x0) * fb, y0 + (y1 - y0) * fb, rs1) & sl
    hem &= ~cv.capsule(x0, y0, x0 + (x1 - x0) * fa, y0 + (y1 - y0) * fa, rs0)
    cv.col[hem & cv.alpha] = np.array(GOLD[3] if x1 < x0 else GOLD[2])
    if ch.get("tape") and g.battle:
        (xa, ya), (xb, yb) = pts[-2], pts[-1]
        ta, tb = 0.80, 0.90
        tp = cv.capsule(xa + (xb - xa) * ta, ya + (yb - ya) * ta, xa + (xb - xa) * tb, ya + (yb - ya) * tb, r) & \
            cv.capsule(xa, ya, xb, yb, r)
        cv.part(name + "tape", tp, "white", edge="dark", lv=np.where(tp, 3, 0))
    return m


def arm(cv, g, ch, name, pts):
    if ch["top_style"] == "tee":
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


def line_pts(x0, y0, x1, y1):
    x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
    pts = []
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    while True:
        pts.append((x0, y0))
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return pts


def football(cv, x, y, s=1.0, ang=0.0, name="ball"):
    """A brown football with white end stripes and laces.  (x, y) = its centre."""
    rx, ry = max(3.4, 6.2 * s), max(2.2, 3.7 * s)
    U, V, P = _local(cv, x, y, ang, 1.0)
    m = (np.abs(U) / rx) ** 1.35 + (V / ry) ** 2 <= 1.0       # an ellipse with pointed ends
    lv = cv.levels(m, rad=ry + 0.5, soft=0.6, cuts=(0.30, 0.56, 0.88))
    cv.part(name, m, "ball", edge="ink", lv=lv)
    inner = ndi.binary_erosion(m)
    if s >= 0.8:
        for u in (-3.9 * s, 3.9 * s):
            st = inner & (np.abs(U - u) < 0.55)
            cv.col[st] = RAMP["white"][3]
        for u in range(-2, 3):
            px, py = ipt(P(u, -ry * 0.38))
            cv.put(px, py, RAMP["white"][4])
        for u in (-2, 0, 2):
            px, py = ipt(P(u, -ry * 0.38 - 1))
            if inner[py, px]:
                cv.put(px, py, RAMP["white"][2])
    else:
        for u in (-0.5, 0.5):
            px, py = ipt(P(u, -0.6))
            cv.put(px, py, RAMP["white"][3])
    return m


def stick(cv, x0, y0, x1, y1, battle=True):
    """Professor's wooden pointer.  Drawn AFTER the outline pass (it is only 1-2 px thick)."""
    wood = RAMP["wood"]
    pts = line_pts(x0, y0, x1, y1)
    steep = abs(y1 - y0) > abs(x1 - x0)
    ox, oy = (1, 0) if steep else (0, 1)
    if battle:
        for (x, y) in pts:
            cv.put(x + ox, y + oy, wood[1])
    for i, (x, y) in enumerate(pts):
        cv.put(x, y, wood[3] if battle else wood[2])
    ntip = 3 if battle else 1
    for (x, y) in pts[-ntip:]:
        cv.put(x, y, STICK_TIP)
        if battle:
            cv.put(x + ox, y + oy, STICK_TIP)


def clipboard(cv, x, y, s=1.0, ang=0.0, name="board", face=True):
    """Clipboard with a form on it.  (x, y) = its centre."""
    U, V, P = _local(cv, x, y, ang, 1.0)
    w, h = max(3.0, 5.0 * s), max(3.9, 6.6 * s)
    bd = cv.poly([P(-w, -h), P(w, -h), P(w, h), P(-w, h)])
    cv.part(name, bd, "board", edge="ink", lv=np.where(bd, 2, 0) + np.where(bd & (U < -w + 1.5), 1, 0))
    if face:
        if s >= 0.8:
            pw = w - 1.2
            pp = cv.poly([P(-pw, -h + 1.4), P(pw, -h + 1.4), P(pw, h - 1.2), P(-pw, h - 1.2)])
        else:
            pp = cv.poly([P(-w + 1.4, -h + 1.4), P(w - 1.4, -h + 1.4), P(w - 1.4, h - 1.4), P(-w + 1.4, h - 1.4)])
        cv.part(name + "pg", pp, "paper", edge=None, lv=np.where(pp, 4, 0) - np.where(pp & (U > 0.5 * w), 1, 0))
        if s >= 0.8:
            for j, v in enumerate((-2.0, 0.4, 2.8)):
                bx, by = ipt(P(-2.4, v))
                cv.put(bx, by, (120, 130, 160))
                if j < 2:
                    cv.put(bx, by, (60, 170, 90))
                for u in np.arange(-1.0, 3.2, 1.0):
                    px, py = ipt(P(u, v))
                    cv.put(px, py, RAMP["paper"][1])
        else:
            px, py = ipt(P(-0.5, 0.5))
            cv.put(px, py, RAMP["paper"][1])
    clip = cv.poly([P(-2.2 * s - 0.3, -h - 1.0 * s), P(2.2 * s + 0.3, -h - 1.0 * s), P(2.2 * s + 0.3, -h + 1.4 * s), P(-2.2 * s - 0.3, -h + 1.4 * s)])
    cv.part(name + "clip", clip, "metal", edge="ink", lv=np.where(clip, 3, 0))
    return bd


def paper_bit(cv, x, y):
    cv.puts([(x, y), (x + 1, y), (x + 2, y), (x, y + 1), (x + 1, y + 1), (x + 2, y + 1), (x, y + 2), (x + 1, y + 2), (x + 2, y + 2)], RAMP["paper"][3])
    cv.put(x + 2, y + 2, RAMP["paper"][1]); cv.put(x, y, RAMP["paper"][4])


def edge_stripe(cv, name, y0, y1, side, col, inset=1):
    pid = cv.names[name]
    for y in range(int(round(y0)), int(round(y1)) + 1):
        if not 0 <= y < cv.h:
            continue
        xs = np.nonzero(cv.own[y] == pid)[0]
        if len(xs) < 3:
            continue
        x = xs.min() + inset if side < 0 else xs.max() - inset
        cv.put(x, y, col)


def rib(cv, name, y0, y1, ramp):
    """Knit ribbing: every other pixel one tone down on these rows."""
    pid = cv.names[name]
    for y in range(int(round(y0)), int(round(y1)) + 1):
        for x in range(cv.w):
            if 0 <= y < cv.h and cv.own[y, x] == pid and x % 2 == 0 and tuple(cv.col[y, x]) != tuple(ramp[0]):
                cv.put(x, y, ramp[1])


# ==========================================================================
# LEGS, TORSO
# ==========================================================================
def shoe(cv, g, ch, fx, s, name, side=False):
    small = not g.battle
    yb = g.CH - 1
    st = ch["shoe_style"]
    sr = ch["shoe"]
    hw = {"slides": 4.5, "boots": 3.7, "loafers": 3.5}[st] * (0.66 if small else 1.0)
    hh = (1.6 if small else 2.5) if st != "slides" else (1.4 if small else 2.2)
    cx = fx + (1.7 if side else s * 0.4) * (0.66 if small else 1.0)
    if side:
        hw *= 1.15
    up = cv.ell(cx, yb - hh * 0.75, hw, hh) & (cv.Y <= yb)
    if st == "boots":
        up |= cv.rect(fx - (2.0 if small else 2.9), yb - (3.5 if small else 6.0), fx + (2.0 if small else 2.9), yb - 1)
    lv = np.where(up, 2, 0) + np.where(up & (cv.Y < yb - hh * 0.7), 1, 0)
    cv.part(name, up, sr, edge="ink", lv=lv)
    if st == "slides" and not small:
        # the white sock toe pokes out in front of the strap; gold stripe on the strap
        if not side:
            cv.hline(int(round(cx - 1)), int(round(cx + 1)), yb - 1, ch["sock"][3])
        else:
            cv.hline(int(round(cx + hw - 3)), int(round(cx + hw - 2)), yb - 1, ch["sock"][3])
        cv.hline(int(round(cx - hw + 2)), int(round(cx + hw - 2 - (2 if side else 0))), yb - 2, GOLD[3])
        cv.hline(int(round(cx - hw + 1)), int(round(cx + hw - 1)), yb, sr[3])
    if st == "loafers" and not small:
        cv.hline(int(round(cx - 1)), int(round(cx + 1)), yb - 2, sr[0])
        cv.put(int(round(cx - 1)), yb - 1, sr[4])
    if st == "boots" and not small:
        cv.put(int(round(cx - 1)), yb - 2, sr[3])
        cv.hline(int(round(fx - 2)), int(round(fx + 2)), yb - 5, sr[3])


def legs_front(cv, g, ch, back=False):
    k = g.wk
    small = not g.battle
    st = ch["legs_style"]
    if st == "trousers":
        for s in (-1, 1):
            shoe(cv, g, ch, g.X(s * 5.0), s, "shoe%d" % s)
        for s in (-1, 1):
            x0, x1 = s * 4.6, s * 5.0
            r0 = 3.3 * k
            leg = cv.capsule(*g.Q(x0, 46), *g.Q(x1, 75.5), r0, r0 * 0.9) & (cv.Y <= g.Y(77.4))
            cv.part("leg%d" % s, leg, ch["pants"], rad=r0 + 0.4, soft=0.8, cuts=(0.30, 0.55, 0.88),
                    tex=0.03 if g.battle else 0, seed=11 + s)
            if not small and not back:
                xm = int(round(g.X((x0 + x1) / 2)))
                for y in range(int(g.Y(52)), int(g.Y(76))):
                    if cv.own[y, xm] == cv.names["leg%d" % s]:
                        cv.put(xm, y, ch["pants"][3] if s < 0 else ch["pants"][1])
    elif st == "joggers":
        for s in (-1, 1):
            sock = cv.capsule(*g.Q(s * 5.3, 70.0), *g.Q(s * 5.3, 77.8), 2.5 * k, 2.4 * k)
            cv.part("sock%d" % s, sock, ch["sock"], rad=2.4 * k, soft=0.6, cuts=(0.3, 0.55, 0.9))
        for s in (-1, 1):
            leg = cv.capsule(*g.Q(s * 5.0, 46), *g.Q(s * 5.3, 71.0), 3.9 * k, 3.0 * k)
            cv.part("leg%d" % s, leg, ch["pants"], rad=3.6 * k, soft=0.8, cuts=(0.30, 0.55, 0.88),
                    tex=0.04 if g.battle else 0, seed=13 + s)
            pr = ch["pants"]
            pid = cv.names["leg%d" % s]
            y0 = int(round(g.Y(69.6)))
            for y in range(y0, y0 + 8):
                for x in range(cv.w):
                    if 0 <= y < cv.h and cv.own[y, x] == pid and tuple(cv.col[y, x]) != pr[0]:
                        cv.put(x, y, pr[0] if y == y0 and not small else pr[1] if x > g.c + s * 5.6 * k else pr[2])
            edge_stripe(cv, "leg%d" % s, g.Y(48), g.Y(68.6), s, GOLD[3] if s < 0 else GOLD[2], inset=1)
        for s in (-1, 1):
            shoe(cv, g, ch, g.X(s * 5.4), s, "shoe%d" % s)
    elif st == "skirt":
        for s in (-1, 1):
            leg = cv.capsule(*g.Q(s * 4.4, 58), *g.Q(s * 4.7, 75.5), 2.7 * k, 2.3 * k)
            cv.part("leg%d" % s, leg, ch["tights"], rad=2.6 * k, soft=0.7, cuts=(0.30, 0.55, 0.88))
        for s in (-1, 1):
            shoe(cv, g, ch, g.X(s * 4.7), s, "shoe%d" % s)
        m = cv.poly([g.Q(-11.6, 44), g.Q(11.6, 44), g.Q(13.6, 60), g.Q(14.4, 66.4), g.Q(-14.4, 66.4), g.Q(-13.6, 60)])
        cv.part("skirt", m, ch["pants"], rad=5 * k + 1, soft=1.2, cuts=(0.30, 0.56, 0.88), tex=0.03 if g.battle else 0, seed=17)
        if not small:
            sid = cv.names["skirt"]
            for dx in (-7.5, -2.5, 2.5, 7.5):
                for u in np.arange(52, 66.4, 0.5):
                    x, y = ipt(g.Q(dx * (1 + (u - 52) / 80.0), u))
                    if cv.own[y, x] == sid and tuple(cv.col[y, x]) != ch["pants"][0]:
                        cv.put(x, y, ch["pants"][1] if dx > 0 else ch["pants"][3] if dx < -5 else ch["pants"][1])


def torso_poly(g, style):
    if style == "tee":
        P = [(-6.4, 22), (6.4, 22), (11.4, 23.2), (13.2, 28), (11.4, 34), (9.6, 46.8), (-9.6, 46.8), (-11.4, 34),
             (-13.2, 28), (-11.4, 23.2)]
    elif style == "cardigan":
        P = [(-6, 22), (6, 22), (11, 24), (12.4, 28.5), (11.6, 35), (12.4, 46), (-12.4, 46), (-11.6, 35), (-12.4, 28.5), (-11, 24)]
    else:  # vest: the shirt underneath
        P = [(-6, 22), (6, 22), (11, 23.8), (12.4, 28.5), (11, 35), (11.2, 47), (-11.2, 47), (-11, 35), (-12.4, 28.5), (-11, 23.8)]
    return [g.Q(x, u) for x, u in P]


def necklace(cv, g, battle):
    """Professor's chunky turquoise + gold bead necklace."""
    n = 9 if battle else 5
    for i in range(n):
        a = math.pi * (0.12 + 0.76 * i / (n - 1))
        x = g.c + math.cos(a) * 4.4 * g.wk
        y = g.Y(22.6) + math.sin(a) * (6.6 if battle else 3.6)
        col = RAMP["bead"][3] if i % 2 == 0 else GOLD[3]
        cv.put(x, y, col)
        if battle:
            cv.put(x, y + 1, RAMP["bead"][1] if i % 2 == 0 else GOLD[1])


def torso_front(cv, g, ch, back=False):
    k = g.wk
    small = not g.battle
    st = ch["top_style"]
    sk, tp = ch["skin"], ch["top"]
    nw = 3.4 if st == "tee" else 2.6
    cv.part("neck", cv.rect(*g.Hh(-nw, 16.5), *g.Hh(nw, 23.5)), sk, rad=2, bias=-0.15)
    m = cv.poly(torso_poly(g, st))
    if st == "tee":
        cv.part("shirt", m, tp, rad=8 * k + 1, soft=1.4, cuts=(0.32, 0.6, 0.9), tex=0.02 if not small else 0, seed=5)
        if not back:
            hk = g.hk
            ring = cv.ell(g.c, g.t + 21.9 * hk, (nw + 1.7) * hk, 2.5 * hk + 0.2) & ~cv.ell(g.c, g.t + 21.4 * hk, nw * hk + 0.1, 1.5 * hk) \
                & (cv.Y >= g.t + 21.6 * hk)
            cv.part("collar", ring, GOLD, edge=None, lv=np.where(ring, 3, 0) - np.where(ring & (cv.X > g.c + 1), 1, 0))
            if not small:
                y = int(round(g.Y(33.4)))
                for s in (-1, 1):
                    xa, xb = sorted((int(round(g.X(s * 2.0))), int(round(g.X(s * 8.6)))))
                    for x in range(xa, xb + 1):
                        dy = 0 if abs(x - g.c) < 0.6 * (abs(xb - xa)) else -1
                        cv.put(x, y + dy, tp[1])
                cv.hline(int(round(g.X(-8))), int(round(g.X(8))), int(round(g.Y(46.0))), tp[1])
        else:
            cv.hline(int(round(g.X(-3.4))), int(round(g.X(3.4))), int(round(g.t + 22.6 * g.hk)), GOLD[2])
    elif st == "cardigan":
        un = ch["under"]
        cv.part("shirt", m, un, rad=8 * k + 1, soft=1.4, cuts=(0.32, 0.6, 0.9))
        if not back:
            for s in (-1, 1):
                pm = cv.poly([g.Q(s * 6.2, 22.4), g.Q(s * 11, 24), g.Q(s * 12.4, 28.5), g.Q(s * 11.6, 35), g.Q(s * 12.6, 46),
                              g.Q(s * 13.6, 60), g.Q(s * 3.4, 60), g.Q(s * 3.0, 46), g.Q(s * 3.2, 30), g.Q(s * 4.4, 23.4)])
                cv.part("card%d" % s, pm, tp, rad=6 * k + 1, soft=1.2, cuts=(0.30, 0.56, 0.88), tex=0.05 if not small else 0, seed=31 + s)
                band = cv.poly([g.Q(s * 4.4, 23.2), g.Q(s * 7.0, 23.6), g.Q(s * 5.0, 36), g.Q(s * 5.2, 60), g.Q(s * 3.4, 60),
                                g.Q(s * 3.0, 46), g.Q(s * 3.2, 30)])
                cv.part("band%d" % s, band, tp, edge="dark", noedge=(), lv=np.where(band, 3 if s < 0 else 2, 0))
                if not small:
                    px, py = g.Q(s * 8.6, 51.5)
                    pk = cv.rect(px - 2.6, py - 2.4, px + 2.6, py + 2.4)
                    cv.part("pk%d" % s, pk, tp, edge="dark", noedge=("card%d" % s,), lv=np.where(pk, 2, 0) + np.where(pk & (cv.Y < py - 1), 1, 0))
                    rib(cv, "card%d" % s, g.Y(58.4), g.Y(60), tp)
            necklace(cv, g, not small)
        else:
            pm = cv.poly([g.Q(-6.5, 22.5), g.Q(6.5, 22.5), g.Q(11, 24), g.Q(12.4, 28.5), g.Q(11.6, 35), g.Q(12.6, 46), g.Q(13.6, 60),
                          g.Q(-13.6, 60), g.Q(-12.6, 46), g.Q(-11.6, 35), g.Q(-12.4, 28.5), g.Q(-11, 24)])
            cv.part("card0", pm, tp, rad=6 * k + 1, soft=1.2, cuts=(0.30, 0.56, 0.88), tex=0.05 if not small else 0, seed=33)
            col = cv.ell(*g.Q(0, 22.8), 6.6 * k, 2.4 * g.hk + 0.6) & (cv.Y >= g.Y(22.4))
            cv.part("shawl", col, tp, edge="dark", lv=np.where(col, 3, 0))
            if not small:
                rib(cv, "card0", g.Y(58.4), g.Y(60), tp)
    else:  # vest
        sl = ch["sleeve"]
        cv.part("shirt", m, sl, rad=8 * k + 1, soft=1.4, cuts=(0.32, 0.6, 0.9))
        if not back:
            vm = cv.poly([g.Q(-9.4, 24.6), g.Q(-4.2, 23.4), g.Q(0, 33.5), g.Q(4.2, 23.4), g.Q(9.4, 24.6), g.Q(10.8, 28.6), g.Q(10.4, 35),
                          g.Q(11.0, 46.6), g.Q(-11.0, 46.6), g.Q(-10.4, 35), g.Q(-10.8, 28.6)])
            cv.part("vest", vm, tp, edge="dark", noedge=(), rad=6 * k + 1, soft=1.2, cuts=(0.30, 0.56, 0.88),
                    tex=0.05 if not small else 0, seed=37)
            if not small:
                for s in (-1, 1):
                    cv.line(*ipt(g.Q(s * 4.0, 23.6)), *ipt(g.Q(s * 0.4, 32.6)), tp[3] if s < 0 else tp[1])
                rib(cv, "vest", g.Y(44.6), g.Y(46.6), tp)
            for s in (-1, 1):
                cp = cv.poly([g.Hh(s * 0.4, 21.6), g.Hh(s * 4.6, 21.2), g.Hh(s * 3.2, 24.6)])
                cv.part("cpt%d" % s, cp, sl, edge="dark", lv=np.where(cp, 4 if s < 0 else 3, 0))
            # lanyard + badge
            bx, by = g.Q(1.4, 35.2)
            for s in (-1, 1):
                cv.line(*ipt(g.Hh(s * 2.6, 22.4)), int(round(bx + s * (0.5 if small else 1))), int(round(by)), RAMP["lany"][2] if s < 0 else RAMP["lany"][1])
            if not small:
                bd = cv.rect(bx - 2, by, bx + 2, by + 5)
                cv.part("badge", bd, "white", edge="ink", lv=np.where(bd, 3, 0))
                cv.puts([(int(round(bx - 1)), int(round(by + 1))), (int(round(bx - 1)), int(round(by + 2)))], ch["skin"][2])
                cv.hline(int(round(bx)), int(round(bx + 1)), int(round(by + 2)), (90, 120, 170))
                cv.hline(int(round(bx - 1)), int(round(bx + 1)), int(round(by + 4)), (230, 120, 40))
            else:
                cv.puts([(int(round(bx)), int(round(by))), (int(round(bx)), int(round(by + 1)))], RAMP["white"][4])
        else:
            vm = cv.poly([g.Q(-9.6, 24.2), g.Q(9.6, 24.2), g.Q(10.8, 28.6), g.Q(10.4, 35), g.Q(11.0, 46.6), g.Q(-11.0, 46.6),
                          g.Q(-10.4, 35), g.Q(-10.8, 28.6)])
            cv.part("vest", vm, tp, edge="dark", rad=6 * k + 1, soft=1.2, cuts=(0.30, 0.56, 0.88), tex=0.05 if not small else 0, seed=38)
            if not small:
                rib(cv, "vest", g.Y(44.6), g.Y(46.6), tp)
            cb = cv.rect(*g.Hh(-4.2, 20.4), *g.Hh(4.2, 23.4))
            cv.part("cband", cb, sl, edge="dark", lv=np.where(cb, 3, 0))

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


# ==========================================================================
# HEADS (battle front: pixel features; world front: its own small drawing)
# ==========================================================================
def silver_ring(cv, ch, c, t, s, ox=0.0, back=False):
    """The professor's short silver curls that stand out round the head (drawn behind the face)."""
    hr = ch["hair"]
    big = s >= 0.8
    cy = 10.6
    m = cv.ell(c + ox * s, t + (cy + 0.6) * s, (ch["facew"] + 2.0) * s, 9.4 * s)
    n = 13 if big else 9
    lo, hi = (0.86, 2.14) if not back else (0.80, 2.20)
    for i in range(n):
        a = math.pi * (lo + (hi - lo) * i / (n - 1))
        px, py = c + (ox + math.cos(a) * (ch["facew"] + 1.8)) * s, t + (cy + math.sin(a) * 9.0) * s
        m |= cv.ell(px, py, 2.4 * s + 0.3, 2.4 * s + 0.3)
    cv.part("curls", m, hr, rad=4 * s + 1, soft=1.0, cuts=(0.30, 0.56, 0.88), bias=-0.04, tex=0.10 if big else 0, seed=41)
    curl_texture(cv, "curls", hr, big)


def hair_back(cv, ch, c, t, s, view="front"):
    if ch["hair_style"] == "silver" and view == "front":
        silver_ring(cv, ch, c, t, s)


def fade_recolor(cv, name, mask, hr, sk, t_=0.42):
    pid = cv.names[name]
    ys, xs = np.nonzero((cv.own == pid) & mask)
    for y, x in zip(ys, xs):
        if tuple(cv.col[y, x]) != tuple(hr[0]):
            cv.put(x, y, mix(hr[1] if (x + y) % 2 else hr[2], sk[1], t_))


def dot_texture(cv, name, hr, y0, y1, c, step=2, half=12):
    pid = cv.names[name]
    for y in range(int(y0), int(y1), step):
        for x in range(c - half, c + half + 1):
            if 0 <= y < cv.h and 0 <= x < cv.w and cv.own[y, x] == pid and tuple(cv.col[y, x]) != tuple(hr[0]) \
                    and (x + (y // step)) % 2 == 0:
                cv.put(x, y, hr[3] if x < c + 2 else hr[2])
                if y + 1 < cv.h and cv.own[y + 1, x] == pid:
                    cv.put(x, y + 1, hr[1])


def head_front_b(cv, ch, c, t, mode):
    """Battle head, front view.  mode is a dict: eyes, brows, mouth, glance."""
    sk, hr = ch["skin"], ch["hair"]
    st = ch["hair_style"]
    fw = ch["facew"]
    if ch["ears"]:
        for s in (-1, 1):
            e = cv.ell(c + s * (fw + 0.2), t + 14.6, 1.7, 2.3)
            cv.part("ear%d" % s, e, sk, edge="dark", lv=np.where(e, 2, 0) + np.where(e & (cv.X < c), 1, 0))
    jaw = fw - (0.5 if st == "flattop" else 1.0)
    face = cv.ell(c, t + 13.5, fw, 7.3) | cv.ell(c, t + 16, jaw, 6.8)
    cv.part("face", face, sk, rad=6, soft=1.4, cuts=(0.22, 0.48, 0.86), bias=0.06)
    if st == "flattop":
        yb = t + 7.0 + 0.03 * (cv.X - c) ** 2
        blk = cv.rect(c - 7.6, t - 0.6, c + 7.6, t + 6) & cv.ell(c, t + 4.6, 10.4, 6.2)
        cap = cv.ell(c, t + 10.4, fw + 0.4, 9.6) & (cv.Y < yb + 0.5)
        side = cv.ell(c, t + 12.4, fw + 0.6, 8.0) & (np.abs(cv.X - c) >= fw - 1.0) & (cv.Y < t + 13.6)
        cv.part("crown", blk | cap | side, hr, rad=5, soft=1.0, cuts=(0.24, 0.5, 0.84))
        dot_texture(cv, "crown", hr, t, t + 6, c)
        fade_recolor(cv, "crown", (cv.Y >= t + 6.5) & (np.abs(cv.X - c) >= fw - 2.2), hr, sk, 0.32)
        cv.hline(c - 4, c + 3, t, hr[3])
    elif st == "silver":
        yb = t + 7.4 + 0.045 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 10.2, fw + 1.4, 9.8) & (cv.Y < yb + 0.5)
        side = cv.ell(c, t + 12.5, fw + 1.0, 7.8) & (np.abs(cv.X - c) >= fw - 0.8) & (cv.Y < t + 15)
        cv.part("crown", crown | side, hr, noedge=("curls",), rad=5, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.10, seed=47)
        curl_texture(cv, "crown", hr, True)
    elif st == "sidepart":
        yb = t + 6.8 + 0.04 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 10.4, fw + 1.4, 10.0) & (cv.Y < yb + 0.5)
        side = cv.ell(c, t + 12.5, fw + 0.8, 8.0) & (np.abs(cv.X - c) >= fw - 1.0) & (cv.Y < t + 13.6)
        cv.part("crown", crown | side, hr, rad=5, soft=1.0, cuts=(0.24, 0.5, 0.84))
        swoop = cv.poly([(c - 3.5, t + 0.6), (c + 5, t + 1.0), (c + 8.6, t + 5.4), (c + 8.4, t + 10.6), (c + 6.6, t + 8.4),
                         (c + 3, t + 7.6), (c - 1, t + 7.4), (c - 3.6, t + 6.8)])
        cv.part("bangs", swoop, hr, noedge=("crown",), rad=3, soft=0.8, cuts=(0.30, 0.56, 0.88))
        for x in range(c - 2, c + 7):
            y = int(round(t + 2.6 + 0.07 * (x - c - 2) ** 2))
            cv.put(x, y, hr[3] if x < c + 4 else hr[2])
        cv.line(c - 1, t + 4, c + 6, t + 8, hr[1])
        cv.line(c - 3, t + 1, c - 4, t + 6, hr[0])
        cow = cv.capsule(c + 1.0, t + 0.8, c + 3.4, t - 2.2, 0.9)
        cv.part("cowlick", cow, hr, edge=None, lv=np.where(cow, 2, 0))
    features_b(cv, ch, c, t, mode)


def features_b(cv, ch, c, t, mode):
    sk, hr = ch["skin"], ch["hair"]
    st = ch["hair_style"]
    fid = cv.names["face"]
    br = ch.get("brow", hr)[1]
    ey = t + 13
    em = mode.get("eyes", "open")
    gl = mode.get("glance", 0)
    if ch.get("blush"):
        for s in (-1, 1):
            cv.put(c + s * 5, t + 16, mix(sk[2], ch["blush"], 0.35))
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
        xs = [c - 5, c - 4, c - 3] if side < 0 else [c + 5, c + 4, c + 3]
        ys = {"flat": [ey - 2] * 3, "up": [ey - 3] * 3, "angry": [ey - 3, ey - 2, ey - 1], "worried": [ey - 2, ey - 3, ey - 3],
              "hit": [ey - 3, ey - 3, ey - 2]}.get(bm, [ey - 2] * 3)
        if bm == "smug":
            ys = [ey - 3, ey - 3, ey - 2] if side > 0 else [ey - 2] * 3
        for x, y in zip(xs, ys):
            cv.put(x, y, br)
        if st == "flattop":       # heavy brows
            cv.put(xs[1], ys[1] - (0 if bm == "angry" else 0) + 0, br)
            cv.put(xs[0] + (-1 if side < 0 else 1), ys[0], br)
    # mouth
    mm = mode.get("mouth", "smile")
    my = t + 19
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
    elif mm == "o":
        cv.hline(c - 1, c + 1, my, MOUTH); cv.hline(c - 1, c + 1, my + 1, MOUTH); cv.put(c, my + 1, TONGUE)
    # per-character face pieces
    if st == "flattop":   # eye black
        for side in (-1, 1):
            x0 = c - 5 if side < 0 else c + 2
            cv.hline(x0, x0 + 3, t + 16, EYEBLACK)
    if st == "silver":    # gold half-moon reading glasses, low on the nose
        a = (mode.get("askew") and 1) or 0
        for side in (-1, 1):
            x0 = c - 5 if side < 0 else c + 2
            yy = ey + 1 + (a if side > 0 else 0)
            cv.put(x0 - 1, yy, GOLD[2]); cv.put(x0 - 1, yy + 1, GOLD[1])
            cv.put(x0 + 4, yy, GOLD[2]); cv.put(x0 + 4, yy + 1, GOLD[1])
            cv.hline(x0, x0 + 3, yy + 2, GOLD[3] if side < 0 else GOLD[2])
            cv.put(c - 7 if side < 0 else c + 7, ey + 1, GOLD[1])
        cv.put(c, ey + 2, GOLD[3])
        if mode.get("glint"):
            cv.put(c - 4, ey + 2, WHITE); cv.put(c + 3, ey + 2 + a, WHITE)


def head_front_w(cv, ch, c, t, mode):
    """World head (front), drawn small: about 14 px tall."""
    sk, hr = ch["skin"], ch["hair"]
    st = ch["hair_style"]
    fw = ch["facew"] * 0.655
    if ch["ears"]:
        for s in (-1, 1):
            e = cv.ell(c + s * (fw + 0.2), t + 9.2, 1.1, 1.5)
            cv.part("ear%d" % s, e, sk, edge="dark", lv=np.where(e, 2, 0))
    face = cv.ell(c, t + 8.6, fw, 4.7) | cv.ell(c, t + 10.2, fw - (0.3 if st == "flattop" else 0.7), 4.4)
    cv.part("face", face, sk, rad=4, soft=1.0, cuts=(0.22, 0.46, 0.88), bias=0.08)
    if st == "flattop":
        yb = t + 4.6 + 0.06 * (cv.X - c) ** 2
        blk = cv.rect(c - 4.9, t - 0.6, c + 4.9, t + 4) & cv.ell(c, t + 3.0, 6.6, 4.0)
        cap = cv.ell(c, t + 6.6, fw + 0.3, 6.2) & (cv.Y < yb + 0.5)
        side = cv.ell(c, t + 8.0, fw + 0.4, 5.2) & (np.abs(cv.X - c) >= fw - 0.6) & (cv.Y < t + 9)
        cv.part("crown", blk | cap | side, hr, rad=3, soft=0.8, cuts=(0.24, 0.5, 0.84))
        for x in range(c - 3, c + 4, 2):
            cv.put(x, t + 1, hr[3] if x < c + 2 else hr[2])
        fade_recolor(cv, "crown", (cv.Y >= t + 4.5) & (np.abs(cv.X - c) >= fw - 1.4), hr, sk, 0.32)
    elif st == "silver":
        yb = t + 4.8 + 0.07 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 6.6, fw + 0.9, 6.4) & (cv.Y < yb + 0.5)
        cv.part("crown", crown, hr, noedge=("curls",), rad=3, soft=0.8, cuts=(0.28, 0.54, 0.86))
        cv.puts([(c - 2, t + 2), (c + 1, t + 1), (c + 3, t + 3)], hr[4])
        cv.puts([(c - 4, t + 4), (c + 2, t + 3)], hr[1])
    elif st == "sidepart":
        yb = t + 4.4 + 0.07 * (cv.X - c) ** 2
        crown = cv.ell(c, t + 6.7, fw + 0.9, 6.6) & (cv.Y < yb + 0.5)
        cv.part("crown", crown, hr, rad=3, soft=0.8, cuts=(0.24, 0.5, 0.84))
        bangs = cv.poly([(c - 2.4, t + 0.6), (c + 3, t + 0.8), (c + 5.6, t + 3.8), (c + 5.4, t + 7.0), (c + 3.6, t + 5.4),
                         (c, t + 4.8), (c - 2.4, t + 4.4)])
        cv.part("bangs", bangs, hr, noedge=("crown",), rad=2, soft=0.6, cuts=(0.30, 0.56, 0.88))
        cv.puts([(c, t + 2), (c + 1, t + 2), (c + 2, t + 3)], hr[3])
        cv.put(c - 2, t + 2, hr[0])
        cv.puts([(c + 1, t - 1), (c + 2, t - 2)], hr[2])
    # features
    ey = t + 8
    em = mode.get("eyes", "open")
    gl = mode.get("glance", 0)
    if ch.get("blush"):
        cv.put(c - 3, t + 10, mix(sk[2], ch["blush"], 0.4)); cv.put(c + 3, t + 10, mix(sk[2], ch["blush"], 0.4))
    for side in (-1, 1):
        x = c - 2 if side < 0 else c + 2
        if em == "open":
            cv.put(x + gl, ey, EYE); cv.put(x + gl, ey + 1, EYE)
        elif em == "up":
            cv.put(x + gl, ey - 1, EYE); cv.put(x + gl, ey, EYE)
        elif em in ("down", "narrow"):
            cv.put(x, ey + 1, EYE); cv.put(x - side, ey + 1, EYE)
        elif em in ("closed", "blink"):
            cv.put(x, ey + 1, sk[0]); cv.put(x - side, ey + 1, sk[0])
        elif em == "happy":
            cv.put(x, ey, EYE); cv.put(x - 1, ey + 1, EYE); cv.put(x + 1, ey + 1, EYE)
        elif em == "hit":
            cv.put(x - side, ey - 1, EYE); cv.put(x, ey, EYE); cv.put(x - side, ey + 1, EYE)
        if ch["fem"] and em in ("open", "up"):
            cv.put(x + side + gl, ey - 1, EYE)
    if st == "flattop":
        cv.puts([(c - 3, ey + 2), (c - 2, ey + 2), (c + 2, ey + 2), (c + 3, ey + 2)], EYEBLACK)
    if st == "silver":
        for side in (-1, 1):
            x = c - 2 if side < 0 else c + 2
            cv.puts([(x - 1, ey + 2), (x, ey + 2), (x + 1, ey + 2)], GOLD[3] if side < 0 else GOLD[2])
        cv.put(c, ey + 1, GOLD[2])
    bm = mode.get("brows", "flat")
    brc = ch.get("brow", hr)[1]
    if bm == "angry":
        cv.put(c - 3, ey - 2, brc); cv.put(c - 2, ey - 1, brc)
        cv.put(c + 3, ey - 2, brc); cv.put(c + 2, ey - 1, brc)
    elif bm == "smug":
        cv.put(c + 2, ey - 2, brc); cv.put(c + 3, ey - 2, brc)
    mm = mode.get("mouth", "smile")
    my = t + 12
    if mm == "smile":
        cv.put(c - 1, my, MOUTH); cv.put(c, my, MOUTH)
        cv.put(c + 1, my, sk[1] if ch["fem"] else MOUTH)
    elif mm == "talk":
        cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c, my + 1, TONGUE)
    elif mm == "grin":
        cv.hline(c - 1, c + 1, my, TEETH); cv.put(c - 2, my - 1, MOUTH); cv.put(c + 2, my - 1, MOUTH)
        cv.hline(c - 1, c + 1, my + 1, MOUTH)
    elif mm == "smirk":
        cv.put(c - 1, my, MOUTH); cv.put(c, my, MOUTH); cv.put(c + 1, my - 1, MOUTH)
    elif mm == "flat":
        cv.hline(c - 1, c + 1, my, MOUTH)
    elif mm in ("ouch", "o"):
        cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c, my + 1, MOUTH)


# ==========================================================================
# ARMS + PROPS per character (front view).  Each returns a list of "late" draws (after the head);
# thin things (the pointer) go on cv.post and are drawn after the outline.
# ==========================================================================
def arms_athlete(cv, g, ch, pose, extra):
    Q = g.Q
    b = g.battle
    s = 1.0 if b else 0.62
    late = []
    # viewer-left arm (his right): the football, tucked
    if pose == "hit":
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-16.2, 31), Q(-18.6, 25)])
        open_hand(cv, g, ch, *Q(-18.8, 22.6), "handL")
        football(cv, *g.Hh(-22, 3), s, ang=-0.9)
    elif pose == "tell":
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-14.6, 34.5), Q(-14.2, 41.6)])
        hand(cv, g, ch, *Q(-14.2, 42.4), "handL")
        football(cv, *Q(-15.0, 45.6), s * 1.12, ang=-0.55)
    elif extra == "toss":
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-15.4, 34.5), Q(-15.0, 30.0)])
        open_hand(cv, g, ch, *Q(-15.2, 28.4), "handL")
        football(cv, *Q(-15.6, 20.0), s, ang=-1.2)
    else:
        arm(cv, g, ch, "armL", [Q(-10.6, 25.5), Q(-14.6, 34.5), Q(-14.2, 41.6)])
        hand(cv, g, ch, *Q(-14.2, 42.4), "handL")
        football(cv, *Q(-15.0, 45.6), s * 1.12, ang=-0.55)
    # viewer-right arm
    if pose == "talk":
        arm(cv, g, ch, "armR", [Q(10.6, 25.5), Q(16.0, 33), Q(17.2, 27.4)])
        open_hand(cv, g, ch, *Q(17.4, 24.8), "handR")
    elif pose == "tell":     # points at you: "you're going DOWN"
        arm(cv, g, ch, "armR", [Q(10.6, 25.5), Q(16.2, 31), Q(19.0, 26.4)])
        point_hand(cv, g, ch, *Q(19.2, 25.6), "handR", 0.55, -0.85)
    elif pose == "hit":
        arm(cv, g, ch, "armR", [Q(10.6, 25.5), Q(16, 30), Q(18.6, 24.5)])
        open_hand(cv, g, ch, *Q(18.8, 22.0), "handR")
    elif extra == "flex":
        arm(cv, g, ch, "armR", [Q(10.6, 25.5), Q(17.2, 27.5), Q(15.2, 20.6)])
        hand(cv, g, ch, *Q(14.8, 19.4), "handR", r=2.4)
        if b:
            bump = cv.ell(*Q(15.6, 25.4), 3.0, 2.6)
            cv.part("bicep", bump, ch["skin"], edge="dark", noedge=("armR",), lv=np.where(bump, 3, 0))
    else:
        arm(cv, g, ch, "armR", [Q(10.6, 25.5), Q(13.8, 35.5), Q(13.4, 43.6)])
        hand(cv, g, ch, *Q(13.4, 45.0), "handR", r=2.4)
    return late


def arms_professor(cv, g, ch, pose, extra):
    Q = g.Q
    b = g.battle
    late = []
    # viewer-left arm
    if pose == "talk":
        arm(cv, g, ch, "armL", [Q(-10.4, 25.5), Q(-15.4, 34), Q(-15.8, 28.6)])
        point_hand(cv, g, ch, *Q(-15.8, 27.6), "handL", 0.0, -1.0)
    elif pose == "hit":
        arm(cv, g, ch, "armL", [Q(-10.4, 25.5), Q(-16, 31), Q(-18.4, 25.5)])
        open_hand(cv, g, ch, *Q(-18.6, 23.0), "handL")
    elif pose == "tell":
        arm(cv, g, ch, "armL", [Q(-10.4, 25.5), Q(-15.6, 34), Q(-11.0, 41.0)])
        hand(cv, g, ch, *Q(-10.8, 41.4), "handL")
    elif extra == "peer":
        late.append(lambda: (arm(cv, g, ch, "armL", [Q(-10.4, 25.5), Q(-12.8, 33), g.Hh(-6.0, 19.6)]),
                             point_hand(cv, g, ch, *g.Hh(-6.4, 17.4), "handL", 0.5, -0.8)))
    elif extra == "tap":
        arm(cv, g, ch, "armL", [Q(-10.4, 25.5), Q(-14.6, 35), Q(-12.4, 32.6)])
        open_hand(cv, g, ch, *Q(-12.4, 31.4), "handL")
    else:
        arm(cv, g, ch, "armL", [Q(-10.4, 25.5), Q(-13.4, 35), Q(-12.8, 43.4)])
        hand(cv, g, ch, *Q(-12.8, 44.8), "handL")
    # viewer-right arm: the pointer
    if pose == "tell":
        arm(cv, g, ch, "armR", [Q(10.4, 25.5), Q(16.0, 30.5), Q(18.8, 24.6)])
        hx, hy = Q(19.0, 23.6)
        hand(cv, g, ch, hx, hy, "handR")
        tx, ty = g.Hh(29, -3)
        cv.post.append(lambda: stick(cv, hx, hy, tx, ty, b))
    elif pose == "hit":
        arm(cv, g, ch, "armR", [Q(10.4, 25.5), Q(16, 30), Q(18.4, 24.5)])
        open_hand(cv, g, ch, *Q(18.6, 22.0), "handR")
        cv.post.append(lambda: stick(cv, *g.Hh(17, -4), *g.Hh(27, 3), b))
    elif extra == "tap":
        arm(cv, g, ch, "armR", [Q(10.4, 25.5), Q(13.6, 36), Q(8.4, 40.4)])
        hx, hy = Q(8.2, 40.6)
        hand(cv, g, ch, hx, hy, "handR")
        tx, ty = Q(-15.4, 30.0)
        cv.post.append(lambda: stick(cv, hx, hy, tx, ty, b))
    else:
        arm(cv, g, ch, "armR", [Q(10.4, 25.5), Q(13.2, 35), Q(13.6, 43.4)])
        hx, hy = Q(13.6, 44.8)
        hand(cv, g, ch, hx, hy, "handR")
        tx, ty = Q(19.6, 17.0)
        cv.post.append(lambda: stick(cv, hx, hy, tx, ty, b))
    return late


def arms_advisor(cv, g, ch, pose, extra):
    Q = g.Q
    b = g.battle
    s = 1.0 if b else 0.62
    late = []
    if pose == "tell":     # holds the form up for you to see
        for sd in (-1, 1):
            arm(cv, g, ch, "arm%d" % sd, [Q(sd * 10.2, 25.5), Q(sd * 13.2, 35), Q(sd * 7.2, 38.6)])
        clipboard(cv, *Q(0, 35.4), s * 1.05, 0.0)
        for sd in (-1, 1):
            hand(cv, g, ch, *Q(sd * 7.6, 39.0), "hand%d" % sd)
        return late
    # viewer-left arm: clipboard hugged to the chest
    if pose == "hit":
        arm(cv, g, ch, "armL", [Q(-10.2, 25.5), Q(-16, 31), Q(-18.6, 25.5)])
        open_hand(cv, g, ch, *Q(-18.8, 23.0), "handL")
        clipboard(cv, *g.Hh(-20, 6), s, -0.7)
    else:
        arm(cv, g, ch, "armL", [Q(-10.2, 25.5), Q(-13.4, 35), Q(-6.0, 39.4)])
        clipboard(cv, *Q(-6.4, 35.4), s, 0.12)
        hand(cv, g, ch, *Q(-9.6, 38.6), "handL")
    # viewer-right arm
    if pose == "talk":
        arm(cv, g, ch, "armR", [Q(10.2, 25.5), Q(15.4, 34), Q(15.8, 28.4)])
        point_hand(cv, g, ch, *Q(15.8, 27.4), "handR", 0.0, -1.0)
    elif pose == "hit":
        arm(cv, g, ch, "armR", [Q(10.2, 25.5), Q(16, 30), Q(18.6, 24.5)])
        open_hand(cv, g, ch, *Q(18.8, 22.0), "handR")
    elif extra == "write":
        arm(cv, g, ch, "armR", [Q(10.2, 25.5), Q(12.8, 36.5), Q(-2.4, 37.6)])
        hx, hy = Q(-3.0, 37.4)
        hand(cv, g, ch, hx, hy, "handR")
        cv.post.append(lambda: cv.line(int(round(hx - 1)), int(round(hy - 1)), int(round(hx - (3 if b else 2))), int(round(hy - (3 if b else 2))), PEN))
    elif extra == "badge":
        arm(cv, g, ch, "armR", [Q(10.2, 25.5), Q(13.6, 35), Q(4.6, 35.6)])
        hand(cv, g, ch, *Q(4.0, 35.8), "handR")
    else:
        arm(cv, g, ch, "armR", [Q(10.2, 25.5), Q(12.6, 35.5), Q(12.4, 43.6)])
        hand(cv, g, ch, *Q(12.4, 45.0), "handR")
    return late


ARMS = {"athlete": arms_athlete, "professor": arms_professor, "advisor_mini": arms_advisor}

MODES = {
    "athlete": {"tell": dict(eyes="narrow", brows="angry", mouth="grin"),
                "toss": dict(eyes="up", mouth="smile", glance=-1), "flex": dict(eyes="happy", mouth="grin")},
    "professor": {"tell": dict(eyes="up", brows="smug", mouth="smirk", glint=True),
                  "peer": dict(eyes="narrow", brows="smug", mouth="flat"), "tap": dict(eyes="closed", mouth="smile")},
    "advisor_mini": {"tell": dict(eyes="up", brows="up", mouth="grin"),
                     "write": dict(eyes="down", mouth="flat"), "badge": dict(eyes="happy", mouth="grin")},
}
EXTRAS = {"athlete": ("toss", "flex"), "professor": ("peer", "tap"), "advisor_mini": ("write", "badge")}

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


def front(cid, pose, battle=True, extra=None):
    ch = CHARS[cid]
    g = G(ch, battle)
    cv = Cv(g.CW, g.CH)
    cv.post = []
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
    for f in cv.post:
        f()
    fx_front(cv, g, ch, cid, pose, extra)
    return cv


def fx_front(cv, g, ch, cid, pose, extra):
    b = g.battle
    c, t = g.c, g.t
    if pose == "hit":
        sweat(cv, c + (9 if b else 6), t + (3 if b else 2), b)
        if cid == "athlete":
            x, y = ipt(g.Hh(-22, 3))
            if b:
                cv.puts([(x - 4, y - 7), (x - 2, y - 8), (x, y - 8), (x + 2, y - 7)], WHITE)
                cv.puts([(x + 6, y + 6), (x + 8, y + 5)], SPARK)
                sparkle(cv, x - 9, y + 6)
            else:
                cv.puts([(x - 2, y - 5), (x, y - 5)], WHITE)
        if cid == "professor":
            pts = ((-24, 30), (-21, 34), (22, 32)) if b else ((-15, 19), (14, 20))
            for (dx, dy) in pts:
                x, y = c + dx, t + dy
                cv.puts([(x, y), (x + 1, y), (x, y + 1)], RAMP["white"][3])
                cv.put(x + 1, y + 1, RAMP["white"][1])
        if cid == "advisor_mini":
            if b:
                for (dx, dy) in ((-27, 30), (20, 34), (-8, -4)):
                    paper_bit(cv, c + dx, t + dy)
            else:
                cv.puts([(c - 16, t + 18), (c - 15, t + 18), (c + 13, t + 21), (c + 14, t + 21)], RAMP["paper"][3])
    if pose == "tell":
        if cid == "athlete" and b:
            x, y = ipt(g.Q(19.2, 25.6))
            for j in range(3):
                cv.put(x + 6 + j, y - 6 - j, SPARK if j else WHITE)
            cv.puts([(x + 4, y - 9), (x + 9, y - 3)], SPARK2)
        if cid == "professor":
            x, y = ipt(g.Hh(29, -3))
            if b:
                cv.puts([(x + 2, y - 2), (x + 3, y - 3), (x + 3, y), (x + 4, y), (x, y - 3), (x, y - 4)], SPARK)
            else:
                cv.puts([(x + 2, y - 1), (x + 1, y - 2)], SPARK)
        if cid == "advisor_mini" and b:
            x, y = ipt(g.Q(0, 35.4))
            sparkle(cv, x + 9, y - 9)
            cv.puts([(x - 9, y - 10), (x - 10, y - 12)], SPARK2)
    if extra == "toss":
        x, y = ipt(g.Q(-15.6, 20.0))
        cv.puts([(x - 5, y + 1), (x + 5, y - 1)], WHITE)


# ==========================================================================
# SIDE (facing right) and BACK
# ==========================================================================
def legs_side(cv, g, ch):
    k = g.wk
    st = ch["legs_style"]
    for j, (lx, lean) in enumerate(((-2.4, -0.9), (1.6, 0.9))):
        x0, x1 = lx, lx + lean
        cuts = (0.30, 0.55, 0.88) if j else (0.45, 0.70, 0.95)
        if st == "joggers":
            sock = cv.capsule(*g.Q(x1, 70.0), *g.Q(x1, 77.8), 2.4 * k, 2.3 * k)
            cv.part("sock%d" % j, sock, ch["sock"], rad=2.4 * k, cuts=(0.3, 0.55, 0.9) if j else (0.45, 0.7, 0.95))
            leg = cv.capsule(*g.Q(x0, 46), *g.Q(x1, 71.0), 3.7 * k, 2.9 * k)
            cv.part("leg%d" % j, leg, ch["pants"], rad=3.6 * k, cuts=cuts)
            pr = ch["pants"]
            pid = cv.names["leg%d" % j]
            y0 = int(round(g.Y(69.6)))
            for y in range(y0, y0 + 8):
                for x in range(cv.w):
                    if 0 <= y < cv.h and cv.own[y, x] == pid and tuple(cv.col[y, x]) != pr[0]:
                        cv.put(x, y, pr[0] if y == y0 and g.battle else pr[1] if j == 0 else pr[2])
            if j:
                for u in np.arange(48, 68.6, 0.5):
                    x, y = ipt(g.Q(x0 + (x1 - x0) * (u - 46) / 25.0 - 0.4, u))
                    if cv.own[y, x] == pid:
                        cv.put(x, y, GOLD[3])
            shoe(cv, g, ch, g.X(x1), 1, "shoe%d" % j, side=True)
        elif st == "skirt":
            leg = cv.capsule(*g.Q(x0 * 0.8, 58), *g.Q(x1, 75.5), 2.6 * k, 2.2 * k)
            cv.part("leg%d" % j, leg, ch["tights"], rad=2.6 * k, cuts=cuts)
            shoe(cv, g, ch, g.X(x1), 1, "shoe%d" % j, side=True)
        else:
            shoe(cv, g, ch, g.X(x1), 1, "shoe%d" % j, side=True)
            r0 = 3.1 * k
            leg = cv.capsule(*g.Q(x0, 46), *g.Q(x1, 75.5), r0, r0 * 0.92) & (cv.Y <= g.Y(77.4))
            cv.part("leg%d" % j, leg, ch["pants"], rad=r0 + 0.4, cuts=cuts)
    if st == "skirt":
        m = cv.poly([g.Q(-8.0, 44), g.Q(6.6, 44), g.Q(8.8, 60), g.Q(9.6, 66.4), g.Q(-10.8, 66.4), g.Q(-9.6, 60)])
        cv.part("skirt", m, ch["pants"], rad=4, cuts=(0.30, 0.55, 0.88))
        if g.battle:
            sid = cv.names["skirt"]
            for dx in (-4.0, 2.0):
                for u in np.arange(50, 66.4, 0.5):
                    x, y = ipt(g.Q(dx * (1 + (u - 50) / 60.0), u))
                    if cv.own[y, x] == sid:
                        cv.put(x, y, ch["pants"][1])


def side(cid, battle=True):
    ch = CHARS[cid]
    g = G(ch, battle, cshift=-2)
    cv = Cv(g.CW, g.CH)
    cv.post = []
    c, t = g.c, g.t
    k, s = g.wk, g.hk
    b = battle
    sk, hr, tp = ch["skin"], ch["hair"], ch["top"]
    st = ch["top_style"]
    hs = ch["hair_style"]
    H = lambda dx, dy: (c + dx * s, t + dy * s)
    if hs == "silver":
        # curls behind the head
        m = cv.empty()
        n = 11 if b else 8
        for i in range(n):
            a = math.pi * (0.70 + 1.15 * i / (n - 1))
            m |= cv.ell(*H(-0.8 + math.cos(a) * 9.0, 10.6 + math.sin(a) * 9.0), 2.4 * s + 0.3, 2.4 * s + 0.3)
        m |= cv.ell(*H(-1.2, 11.2), 9.0 * s, 9.2 * s)
        cv.part("curls", m, hr, rad=4 * s + 1, soft=1.0, cuts=(0.30, 0.56, 0.88), tex=0.10 if b else 0, seed=42)
        curl_texture(cv, "curls", hr, b)
    legs_side(cv, g, ch)
    cv.part("neck", cv.rect(*H(-2.2 if st != "tee" else -3.0, 17), *H(2, 23.5)), sk, rad=2, bias=-0.15)
    if st == "tee":
        tor = cv.poly([g.Q(-5.4, 22), g.Q(3.6, 22), g.Q(7.6, 25.4), g.Q(8.8, 31), g.Q(7.2, 38), g.Q(6.8, 46.8), g.Q(-7.4, 46.8),
                       g.Q(-7.8, 36), g.Q(-7.8, 27)])
        cv.part("shirt", tor, tp, rad=7 * k + 1, soft=1.3, cuts=(0.28, 0.52, 0.84))
        cv.line(*ipt(H(1.6, 22.4)), *ipt(H(3.6, 24.0)), GOLD[3])
        cv.line(*ipt(H(-3.0, 22.0)), *ipt(H(1.4, 22.6)), GOLD[2])
        if b:
            cv.hline(int(round(g.X(1))), int(round(g.X(7))), int(round(g.Y(33.4))), tp[1])
    elif st == "cardigan":
        tor = cv.poly([g.Q(-5, 22), g.Q(3, 22), g.Q(7, 26), g.Q(7.8, 31), g.Q(7.2, 38), g.Q(7.0, 46), g.Q(-7.2, 46), g.Q(-7, 36), g.Q(-7, 28)])
        cv.part("shirt", tor, ch["under"], rad=7 * k + 1, soft=1.3, cuts=(0.28, 0.52, 0.84))
        cd = cv.poly([g.Q(-5.6, 22.2), g.Q(1.2, 22.2), g.Q(4.4, 30), g.Q(5.0, 46), g.Q(7.2, 60), g.Q(-9.6, 60), g.Q(-7.8, 46),
                      g.Q(-7.4, 36), g.Q(-7.2, 28)])
        cv.part("card0", cd, tp, rad=6 * k + 1, soft=1.2, cuts=(0.28, 0.52, 0.84), tex=0.05 if b else 0, seed=34)
        if b:
            rib(cv, "card0", g.Y(58.4), g.Y(60), tp)
            cv.line(*ipt(g.Q(1.2, 22.4)), *ipt(g.Q(4.4, 30)), tp[3])
            for i, u in enumerate((24.5, 26.0, 27.5, 29.0)):
                x, y = ipt(g.Q(4.6 + i * 0.5, u))
                cv.put(x, y, RAMP["bead"][3] if i % 2 == 0 else GOLD[3])
        else:
            x, y = ipt(g.Q(5.4, 26.5))
            cv.put(x, y, RAMP["bead"][3])
    else:  # vest
        tor = cv.poly([g.Q(-5, 22), g.Q(3, 22), g.Q(7, 26), g.Q(8, 31), g.Q(6.5, 37), g.Q(7.2, 47), g.Q(-7.6, 47), g.Q(-7, 36), g.Q(-7, 28)])
        cv.part("shirt", tor, ch["sleeve"], rad=7 * k + 1, soft=1.3, cuts=(0.28, 0.52, 0.84))
        vm = cv.poly([g.Q(-5.6, 23.6), g.Q(0.6, 23.6), g.Q(5.8, 30), g.Q(6.8, 37), g.Q(7.4, 46.6), g.Q(-7.8, 46.6), g.Q(-7.4, 36), g.Q(-7.2, 28)])
        cv.part("vest", vm, tp, edge="dark", rad=6 * k + 1, soft=1.2, cuts=(0.28, 0.52, 0.84), tex=0.05 if b else 0, seed=39)
        if b:
            rib(cv, "vest", g.Y(44.6), g.Y(46.6), tp)
        cp = cv.poly([H(0.4, 21.4), H(3.6, 21.6), H(3.0, 24.4)])
        cv.part("cpt", cp, ch["sleeve"], edge="dark", lv=np.where(cp, 4, 0))
        bx, by = g.Q(6.8, 34.6)
        cv.line(*ipt(H(1.6, 22.6)), int(round(bx)), int(round(by)), RAMP["lany"][2])
        if b:
            bd = cv.rect(bx - 1, by, bx + 1, by + 4)
            cv.part("badge", bd, "white", edge="ink", lv=np.where(bd, 3, 0))
        else:
            cv.put(int(round(bx)), int(round(by + 1)), RAMP["white"][4])
    # arm + prop (near side)
    if cid == "athlete":
        arm(cv, g, ch, "arm", [g.Q(-0.5, 25.5), g.Q(0.6, 35), g.Q(2.6, 41.6)])
        hand(cv, g, ch, *g.Q(2.8, 42.6), "hand")
        football(cv, *g.Q(4.2, 46.0), 1.12 if b else 0.7, ang=0.55)
    elif cid == "professor":
        arm(cv, g, ch, "arm", [g.Q(-0.5, 25.5), g.Q(0.4, 35), g.Q(2.6, 43.4)])
        hx, hy = g.Q(3.0, 44.6)
        hand(cv, g, ch, hx, hy, "hand")
        tx, ty = g.Q(9.6, 17.0)
        cv.post.append(lambda: stick(cv, hx, hy, tx, ty, b))
    else:
        arm(cv, g, ch, "arm", [g.Q(-0.5, 25.5), g.Q(0.4, 35), g.Q(2.4, 42.4)])
        clipboard(cv, *g.Q(3.8, 48.4), 0.95 if b else 0.6, 0.08)
        hand(cv, g, ch, *g.Q(2.6, 43.0), "hand")
    # head (profile)
    head = cv.ell(*H(1, 13.4), 7.2 * s, 7.4 * s) | cv.ell(*H(3, 16), 5 * s, 6.6 * s) | cv.ell(*H(4.6, 19.5), 3.4 * s, 3 * s)
    if hs == "flattop":
        head |= cv.ell(*H(3.4, 18.6), 4.4 * s, 4.0 * s)
    cv.part("head", head, sk, rad=6 * s, soft=1.2, cuts=(0.22, 0.48, 0.86), bias=0.10)
    if b:
        cv.part("nose", cv.ell(*H(8.6, 15.6), 1.6, 1.5), sk, edge="ink", noedge=("head",), rad=1.5, bias=0.15)
    ybs = t + (8 + 0.22 * (c + 7 * s - cv.X) / s) * s
    if hs == "flattop":
        blk = cv.rect(*H(-7.8, -0.6), *H(6.2, 6)) & cv.ell(*H(-0.6, 4.6), 10.4 * s, 6.2 * s)
        cap = cv.ell(*H(-0.6, 10.4), 8.4 * s, 9.6 * s) & ((cv.X < c - 1 * s) | (cv.Y < ybs - 0.5 * s)) & (cv.Y < t + 16.5 * s)
        cv.part("hair", blk | cap, hr, rad=5 * s, soft=1.0, cuts=(0.24, 0.5, 0.84))
        if b:
            dot_texture(cv, "hair", hr, t, t + 6, c - 1)
        fade_recolor(cv, "hair", cv.Y >= t + 6.2 * s, hr, sk, 0.32)
    elif hs == "silver":
        hair = cv.ell(*H(-0.8, 10.4), 9.0 * s, 9.6 * s) & ((cv.X < c + 0.5 * s) | (cv.Y < ybs + 0.5 * s)) & (cv.Y < t + 17 * s)
        cv.part("hair", hair, hr, noedge=("curls",), rad=5 * s, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.10 if b else 0, seed=46)
        curl_texture(cv, "hair", hr, b)
    else:
        hair = cv.ell(*H(-0.5, 10.6), 8.6 * s, 10.3 * s) & ((cv.X < c - 1 * s) | (cv.Y < ybs - 0.5 * s)) & (cv.Y < t + 16.5 * s)
        cv.part("hair", hair, hr, rad=5 * s, soft=1.0, cuts=(0.24, 0.5, 0.84))
        fl = cv.ell(*H(4.6, 5.6), 4.6 * s, 2.4 * s + 0.2, 0.30)
        cv.part("bangs", fl, hr, noedge=("hair",), rad=2, soft=0.8, cuts=(0.30, 0.56, 0.88))
        cow = cv.capsule(*H(-1.0, 0.6), *H(-3.4, -2.2), 0.9 if b else 0.7)
        cv.part("cowlick", cow, hr, edge=None, lv=np.where(cow, 2, 0))
        if b:
            cv.line(c + 6, t + 4, c - 4, t + 3, hr[3]); cv.line(c + 4, t + 6, c - 6, t + 6, hr[1])
    if ch["ears"]:
        e = cv.ell(*H(-1.2, 14.6), 1.6 * s + 0.2, 2.2 * s + 0.2)
        cv.part("ear", e, sk, edge="dark", lv=np.where(e, 2, 0))
    # face details
    if b:
        ey = t + 13
        cv.hline(c + 4, c + 6, ey, EYE); cv.put(c + 5, ey + 1, ch["iris"]); cv.put(c + 6, ey + 1, ch["iris_d"])
        if ch["fem"]:
            cv.put(c + 7, ey - 1, EYE)
        cv.hline(c + 4, c + 6, ey - 2, ch.get("brow", hr)[1])
        cv.put(c + 6, t + 19, MOUTH); cv.put(c + 7, t + 19, MOUTH)
        if hs == "flattop":
            cv.hline(c + 4, c + 6, ey + 3, EYEBLACK)
            cv.hline(c + 3, c + 6, ey - 2, ch["hair"][1])
        if hs == "silver":
            cv.hline(c + 4, c + 7, ey + 3, GOLD[2]); cv.put(c + 8, ey + 2, GOLD[2])
            cv.hline(c - 1, c + 3, ey + 1, GOLD[1])
            cv.put(c - 1, t + 17, GOLD[3]); cv.put(c - 1, t + 18, RAMP["bead"][3])
        if ch.get("blush"):
            cv.put(c + 5, t + 16, mix(sk[2], ch["blush"], 0.4))
    else:
        ey = t + 8
        cv.put(c + 3, ey, EYE); cv.put(c + 3, ey + 1, EYE)
        cv.put(c + 4, t + 12, MOUTH)
        if hs == "flattop":
            cv.puts([(c + 3, ey + 2), (c + 4, ey + 2)], EYEBLACK)
        if hs == "silver":
            cv.puts([(c + 3, ey + 2), (c + 4, ey + 2)], GOLD[2]); cv.put(c + 1, ey + 1, GOLD[1])
    cv.outline()
    for f in cv.post:
        f()
    return cv


def back(cid, battle=True):
    ch = CHARS[cid]
    g = G(ch, battle)
    cv = Cv(g.CW, g.CH)
    cv.post = []
    c, t = g.c, g.t
    k, s = g.wk, g.hk
    b = battle
    sk, hr, tp = ch["skin"], ch["hair"], ch["top"]
    H = lambda dx, dy: (c + dx * s, t + dy * s)
    sc = 1.0 if b else 0.62
    if cid == "advisor_mini":      # clipboard hugged to the chest: only its corner shows past his side
        clipboard(cv, *g.Q(7.4, 35.4), sc, -0.12, face=False)
    legs_front(cv, g, ch, back=True)
    torso_front(cv, g, ch, back=True)
    if cid == "athlete":
        arm(cv, g, ch, "armL", [g.Q(-10.6, 25.5), g.Q(-13.8, 35.5), g.Q(-13.4, 43.6)])
        hand(cv, g, ch, *g.Q(-13.4, 45.0), "handL", r=2.4)
        arm(cv, g, ch, "armR", [g.Q(10.6, 25.5), g.Q(14.6, 34.5), g.Q(14.2, 41.6)])
        football(cv, *g.Q(15.6, 44.6), sc * 1.12, ang=0.62)
    elif cid == "professor":
        arm(cv, g, ch, "armR", [g.Q(10.4, 25.5), g.Q(13.4, 35), g.Q(12.8, 43.4)])
        hand(cv, g, ch, *g.Q(12.8, 44.8), "handR")
        arm(cv, g, ch, "armL", [g.Q(-10.4, 25.5), g.Q(-13.2, 35), g.Q(-13.6, 43.4)])
        hx, hy = g.Q(-13.6, 44.8)
        hand(cv, g, ch, hx, hy, "handL")
        tx, ty = g.Q(-19.6, 17.0)
        cv.post.append(lambda: stick(cv, hx, hy, tx, ty, b))
    else:
        arm(cv, g, ch, "armL", [g.Q(-10.2, 25.5), g.Q(-12.6, 35.5), g.Q(-12.4, 43.6)])
        hand(cv, g, ch, *g.Q(-12.4, 45.0), "handL")
        arm(cv, g, ch, "armR", [g.Q(10.2, 25.5), g.Q(13.4, 35), g.Q(9.6, 39.6)])
    # head from behind
    hs = ch["hair_style"]
    if ch["ears"]:
        for sd in (-1, 1):
            e = cv.ell(*H(sd * (ch["facew"] + 0.2), 14.6), 1.7 * s, 2.3 * s)
            cv.part("ear%d" % sd, e, sk, edge="dark", lv=np.where(e, 2, 0))
    nape = cv.ell(*H(0, 15), (ch["facew"] - (0 if hs != "flattop" else -0.4)) * s, 7 * s)
    cv.part("nape", nape, sk, rad=4, cuts=(0.3, 0.55, 0.9), bias=-0.1)
    if hs == "flattop":
        blk = cv.rect(*H(-7.6, -0.6), *H(7.6, 6)) & cv.ell(*H(0, 4.6), 10.4 * s, 6.2 * s)
        cap = cv.ell(*H(0, 10.6), (ch["facew"] + 0.4) * s, 9.4 * s) & (cv.Y < t + 16.6 * s)
        cv.part("hairback", blk | cap, hr, rad=5 * s, soft=1.0, cuts=(0.24, 0.5, 0.84))
        if b:
            dot_texture(cv, "hairback", hr, t, t + 6, c)
        fade_recolor(cv, "hairback", cv.Y >= t + 6.2 * s, hr, sk, 0.32)
        if b:
            cv.hline(c - 3, c + 3, t + 22, GOLD[2])
    elif hs == "silver":
        silver_ring(cv, ch, c, t, s, back=True)
        hb = cv.ell(*H(0, 11), (ch["facew"] + 1.6) * s, 9.8 * s) & (cv.Y < t + 17.4 * s)
        cv.part("hairback", hb, hr, noedge=("curls",), rad=5 * s, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.10 if b else 0, seed=48)
        curl_texture(cv, "hairback", hr, b)
    else:
        hb = cv.ell(*H(0, 10.6), (ch["facew"] + 1.4) * s, 10.2 * s) & (cv.Y < t + 16.6 * s)
        cv.part("hairback", hb, hr, rad=5 * s, soft=1.0, cuts=(0.24, 0.5, 0.84))
        cow = cv.capsule(*H(1.0, 0.8), *H(3.2, -2.2), 0.9 if b else 0.7)
        cv.part("cowlick", cow, hr, edge=None, lv=np.where(cow, 2, 0))
        if b:
            for x0 in (-6, -3, 3, 6):
                cv.line(int(round(c + x0)), t + 14, c + (1 if x0 > 0 else -1), t + 4, hr[1])
            cv.puts([(c - 3, t + 3), (c - 2, t + 2)], hr[3])
    cv.outline()
    for f in cv.post:
        f()
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
    hr = ch.get("brow", ch["hair"])
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
    if st == "tee":
        sh = cv.ell(c, 78, 38, 28) & cv.half(y=47)
        cv.part("shoulders", sh, tp, rad=14, soft=2.0, cuts=(0.34, 0.6, 0.9), tex=0.02, seed=3)
        cv.part("neck", cv.rect(c - 8, 38, c + 8, 52), sk, rad=5, bias=-0.18)
        ring = cv.ell(c, 50, 11.4, 5.6) & ~cv.ell(c, 49, 9.0, 3.9) & cv.half(y=47)
        cv.part("collar", ring, GOLD, edge="dark", lv=np.where(ring, 3, 0) - np.where(ring & (cv.X > c + 4), 1, 0))
        for s in (-1, 1):                      # trapezius / chest shading
            cv.line(c + s * 12, 60, c + s * 4, 63, tp[1])
    elif st == "cardigan":
        sh = cv.ell(c, 77, 32, 26) & cv.half(y=48)
        cv.part("shoulders", sh, tp, rad=14, soft=2.0, cuts=(0.34, 0.6, 0.9), tex=0.05, seed=3)
        cv.part("neck", cv.rect(c - 5, 38, c + 5, 52), sk, rad=4, bias=-0.18)
        top = cv.poly([(c - 11, 48), (c + 11, 48), (c + 7, 64), (c - 7, 64)]) & ~cv.ell(c, 45.5, 6.0, 5.0)
        cv.part("under", top, ch["under"], edge="dark", rad=6, soft=1.0, cuts=(0.25, 0.5, 0.85), bias=0.06)
        for s in (-1, 1):
            band = cv.poly([(c + s * 10.5, 48), (c + s * 14.5, 48.5), (c + s * 10.5, 64), (c + s * 6.5, 64)])
            cv.part("band%d" % s, band, tp, edge="dark", lv=np.where(band, 3 if s < 0 else 2, 0))
        # bead necklace
        n = 13
        for i in range(n):
            a = math.pi * (0.10 + 0.80 * i / (n - 1))
            x = int(round(c + math.cos(a) * 9.4))
            y = int(round(47.6 + math.sin(a) * 9.0))
            if i % 2 == 0:
                cv.puts([(x, y), (x + 1, y), (x, y + 1), (x + 1, y + 1)], RAMP["bead"][2])
                cv.put(x, y, RAMP["bead"][4]); cv.put(x + 1, y + 1, RAMP["bead"][0])
            else:
                cv.put(x, y, GOLD[3]); cv.put(x + 1, y, GOLD[2]); cv.put(x, y + 1, GOLD[1])
    else:  # vest over a pale blue shirt + lanyard
        sl = ch["sleeve"]
        sh = cv.ell(c, 77, 30, 26) & cv.half(y=48)
        cv.part("shoulders", sh, sl, rad=14, soft=2.0, cuts=(0.34, 0.6, 0.9), seed=3)
        cv.part("neck", cv.rect(c - 5, 38, c + 5, 52), sk, rad=4, bias=-0.18)
        vest = cv.ell(c, 80, 23, 30) & cv.half(y=50) & ~cv.poly([(c - 9, 48), (c + 9, 48), (c, 64)])
        cv.part("vest", vest, tp, edge="dark", rad=10, soft=1.6, cuts=(0.30, 0.56, 0.88), tex=0.06, seed=9)
        for s in (-1, 1):
            cv.line(c + s * 9, 50, c + s, 63, tp[3] if s < 0 else tp[1])
        for s in (-1, 1):
            cp = cv.poly([(c + s * 0.5, 50), (c + s * 6.5, 45.5), (c + s * 9.5, 52), (c + s * 4, 54)])
            cv.part("cpt%d" % s, cp, sl, edge="dark", lv=np.where(cp, 4 if s < 0 else 3, 0))
        ly = RAMP["lany"]
        for s in (-1, 1):
            cv.line(c + s * 8, 46, c + s * 2, 64, ly[2] if s < 0 else ly[1])
            cv.line(c + s * 9, 46, c + s * 3, 64, ly[1] if s < 0 else ly[0])


def p_hair_back(cv, ch, c, lift):
    hr = ch["hair"]
    st = ch["hair_style"]
    if st == "silver":
        m = cv.ell(c, 25 + lift, 19.4, 15)
        n = 15
        for i in range(n):
            a = math.pi * (0.88 + 1.24 * i / (n - 1))
            m |= cv.ell(c + math.cos(a) * 18.2, 23 + lift + math.sin(a) * 16.4, 4.4, 4.4)
        cv.part("curls", m, hr, rad=8, soft=1.4, cuts=(0.30, 0.56, 0.88), bias=-0.04, tex=0.10, seed=41)
        curl_texture(cv, "curls", hr, True)


def p_hair_front(cv, ch, c, lift):
    hr, sk = ch["hair"], ch["skin"]
    st = ch["hair_style"]
    if st == "flattop":
        yb = 13.6 + lift + 0.026 * (cv.X - c) ** 2
        blk = cv.rect(c - 15.0, 4 + lift, c + 15.0, 15) & cv.ell(c, 13 + lift, 20.0, 11.4)
        cap = cv.ell(c, 20 + lift, 17.6, 17.6) & (cv.Y < yb + 1)
        side = cv.ell(c, 26, 16.2, 15) & (np.abs(cv.X - c) >= 12.6) & (cv.Y < 29) & (cv.Y > 10)
        cv.part("crown", blk | cap | side, hr, rad=8, soft=1.2, cuts=(0.24, 0.5, 0.84))
        dot_texture(cv, "crown", hr, 5 + lift, 14 + lift, c, step=2, half=16)
        fade_recolor(cv, "crown", (cv.Y >= 14 + lift) & (np.abs(cv.X - c) >= 11.0), hr, sk, 0.32)
        cv.hline(c - 9, c + 6, 5 + lift, hr[3]); cv.hline(c - 7, c + 1, 6 + lift, hr[4])
    elif st == "silver":
        yb = 13.2 + lift + 0.032 * (cv.X - c) ** 2
        crown = cv.ell(c, 19 + lift, 17.6, 16.8) & (cv.Y < yb + 1)
        for dx in (-12, -8, -4, 0, 4, 8, 12):
            crown |= cv.ell(c + dx, 13.4 + lift + 0.032 * dx * dx, 2.4, 2.0)
        cv.part("crown", crown, hr, noedge=("curls",), rad=8, soft=1.4, cuts=(0.28, 0.54, 0.86), tex=0.10, seed=47)
        curl_texture(cv, "crown", hr, True)
    elif st == "sidepart":
        yb = 12.6 + lift + 0.03 * (cv.X - c) ** 2
        crown = cv.ell(c, 19.5 + lift, 17.2, 17.6) & (cv.Y < yb + 1)
        side = cv.ell(c, 26, 16.0, 15) & (np.abs(cv.X - c) >= 12.6) & (cv.Y < 28)
        cv.part("crown", crown | side, hr, rad=8, soft=1.2, cuts=(0.24, 0.5, 0.84))
        swoop = cv.poly([(c - 6, 2 + lift), (c + 8, 2.5 + lift), (c + 16, 10 + lift), (c + 16.6, 23), (c + 13.4, 19 + lift),
                         (c + 8, 15.4 + lift), (c + 1, 14 + lift), (c - 6, 13 + lift)])
        cv.part("bangs", swoop, hr, noedge=("crown",), rad=5, soft=1.0, cuts=(0.30, 0.56, 0.88))
        for x in range(c - 4, c + 12):
            y = int(round(6 + lift + 0.04 * (x - c - 3) ** 2))
            cv.put(x, y, hr[3] if x < c + 6 else hr[2])
            if x < c + 4:
                cv.put(x, y + 1, hr[4] if c - 2 <= x <= c + 1 else hr[3])
        for (x0, y0, x1, y1) in ((c - 3, 9, c + 13, 16), (c + 1, 6, c + 15, 12), (c - 5, 11, c + 6, 14)):
            cv.line(x0, y0 + lift, x1, y1 + lift, hr[1])
        cv.line(c - 6, 3 + lift, c - 7, 12 + lift, hr[0])
        cow = cv.capsule(c + 2, 3.5 + lift, c + 6, 0.5 + lift, 1.3)
        cv.part("cowlick", cow, hr, edge=None, lv=np.where(cow, 2, 0))


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
    jawk = 1.04 if st == "flattop" else (0.92 if ch["fem"] else 1.0)
    face = cv.ell(c, 28, 13.2 * f, 13.6) | cv.ell(c, 33, 11.2 * f, 12.4) | cv.ell(c, 38, 11.6 * f * jawk, 8.2)
    cv.part("face", face, sk, rad=11, soft=2.2, cuts=(0.16, 0.42, 0.86), bias=0.06)
    fid = cv.names["face"]
    p_hair_front(cv, ch, c, lift)
    if ch.get("blush"):
        for s in (-1, 1):
            bx = c + s * 8
            for y in (34, 35):
                for x in range(bx - 2, bx + 3):
                    if cv.own[y, x] == fid:
                        cv.put(x, y, mix(cv.get(x, y), ch["blush"], 0.22 if abs(x - bx) < 2 else 0.12))
    if st == "silver":          # smile lines
        for s in (-1, 1):
            cv.puts([(c + s * 7, 36), (c + s * 8, 37), (c + s * 8, 38)], sk[1])
    # nose
    cv.puts([(c - 1, 28), (c - 1, 29), (c - 1, 30), (c - 1, 31)], sk[3])
    cv.puts([(c + 1, 31), (c + 1, 32), (c + 2, 33)], sk[1]); cv.puts([(c - 1, 34), (c, 34), (c + 1, 34)], sk[1])
    cv.put(c - 2, 33, sk[1])
    my = 41
    p_mouth(cv, ch, c, my, expr, talk)
    ey = {"neutral": 25, "warm": 25, "concern": 24, "surprised": 23}[expr]
    p_eye(cv, ch, c - 11, ey, expr, -1)
    p_eye(cv, ch, c + 4, ey, expr, 1)
    by = {"neutral": 22, "warm": 22, "concern": 22, "surprised": 20}[expr]
    p_brows(cv, ch, c, by, expr)
    if expr == "concern":
        cv.puts([(c - 1, 22), (c + 1, 22), (c, 23)], sk[1])
    if st == "flattop":         # eye black
        for s in (-1, 1):
            xa, xb = (c - 11, c - 5) if s < 0 else (c + 4, c + 10)
            for y in (31, 32):
                for x in range(xa, xb + 1):
                    if (y == 32 and (x == xa or x == xb)):
                        continue
                    cv.put(x, y, EYEBLACK)
            cv.put(xa + 1, 31, EYEBLACK_HI); cv.put(xa + 2, 31, EYEBLACK_HI)
    if st == "silver":          # gold half-moon reading glasses + bead chain
        for s in (-1, 1):
            ex = c - 11 if s < 0 else c + 4
            x0, x1 = ex - 1, ex + 7
            top = 29
            cv.hline(x0, x1, top, GOLD[2])
            for y in (30, 31):
                cv.put(x0, y, GOLD[1]); cv.put(x1, y, GOLD[1])
                for x in range(x0 + 1, x1):
                    if cv.own[y, x] == fid:
                        cv.put(x, y, mix(cv.get(x, y), RAMP["lens"][3], 0.20))
            cv.hline(x0 + 1, x1 - 1, 32, GOLD[3] if s < 0 else GOLD[2])
            tx = x0 - 1 if s < 0 else x1 + 1
            cv.put(tx, top, GOLD[1]); cv.put(tx + s, top, GOLD[1])
            for i, y in enumerate(range(31, 50, 2)):
                x = int(round(c + s * (14.6 + 0.08 * (y - 31))))
                cv.put(x, y, RAMP["bead"][3] if i % 2 == 0 else GOLD[3])
        cv.hline(c - 2, c + 2, 29, GOLD[2])
        cv.puts([(c - 9, 30), (c + 6, 30)], WHITE)
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
    _rows_sheet([r1, r2, r3], "Encounter cast C -- athlete, professor, advisor_mini -- 3x, next to the cast",
                os.path.join(NEWCAST, "encounters-c-lineup.png"))


def main(argv):
    ids = [a for a in argv if a in IDS] or list(IDS)
    all_cells = {}
    for cid in ids:
        all_cells[cid] = build(cid)
    if len(ids) == len(IDS):
        lineup(all_cells)


if __name__ == "__main__":
    main(sys.argv[1:])
