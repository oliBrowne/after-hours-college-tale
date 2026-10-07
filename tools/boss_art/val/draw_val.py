#!/usr/bin/env python3
"""Val, VP of Talent Acquisition -- final boss of "After Hours - College Tale".

Procedural pixel art in Professor Eric's contract (tools/eric_art/draw_eric.py):
everything is drawn at its final pixel size with aliased shapes and per-pixel
placement.  Nothing drawn is ever resampled; the only scaling is the
nearest-neighbour blow-up of the contact sheet and the 8x previews.

Val is the grown-up version of little val_small (graduation cap, maroon robe):
the same chocolate bob with a fringe, the same big dark oval eyes, and the blue
clasp from the robe is now a brooch on the lapel.  Signature piece: a raspberry
power suit with sharp padded shoulders, an earhook headset with a live red LED,
and a glowing tablet that shows the candidate she is evaluating (you).

Outputs (in ./out next to this script):
  battle-0..5.png    84px tall battle cells   (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  entrance.png       intro-card pose: rising on the Macky stage lift through dry ice
  screens.png        optional battle prop: the wall of candidate screens behind her
  world-0..5.png     54px tall overworld cells (same poses)
  portrait-0..3.png  64x64 portraits          (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk/val-0..3.png  the portraits with the mouth open mid-word
  idle/val-{blink,pose1,pose2}.png  world front idle extras (same canvas + foot)
  feet.json          foot point [x, y] for every body cell
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
PREV = os.path.join(HERE, "prev")
CAST_REF = "/tmp/claude-0/designs/cast-reference.png"

# --------------------------------------------------------------------------
# palette (outline + lighting identical to Eric's; materials are Val's)
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline, same as the whole cast

RAMP = {
    # 0 = line/darkest, 1 = shadow, 2 = mid, 3 = light, 4 = highlight
    "suit":   [(62, 10, 40), (124, 20, 68), (178, 32, 94), (220, 62, 122), (246, 124, 164)],
    "suitdk": [(48, 8, 32), (98, 16, 56), (142, 26, 78), (178, 40, 98), (206, 74, 124)],
    "blouse": [(112, 98, 96), (196, 186, 176), (230, 224, 214), (246, 242, 234), (255, 253, 246)],
    "skin":   [(120, 62, 54), (204, 134, 106), (234, 174, 136), (248, 202, 164), (255, 226, 194)],
    "hair":   [(30, 18, 20), (60, 34, 30), (92, 54, 40), (128, 80, 54), (166, 112, 76)],
    "gold":   [(96, 58, 16), (168, 108, 30), (218, 160, 50), (244, 200, 92), (255, 236, 164)],
    "black":  [(14, 12, 20), (32, 30, 42), (52, 50, 66), (84, 82, 100), (132, 130, 150)],
    "screen": [(18, 58, 92), (36, 118, 168), (76, 186, 228), (148, 228, 250), (232, 252, 255)],
    "metal":  [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "fog":    [(122, 116, 150), (172, 168, 196), (206, 204, 224), (228, 228, 240), (246, 246, 252)],
    "lift":   [(28, 26, 38), (52, 50, 66), (80, 78, 98), (112, 110, 130), (150, 148, 168)],
}
BLUSH = (238, 132, 128)
EYE = (34, 20, 26)
IRIS = (78, 44, 36)
WHITE = (252, 250, 246)
MOUTH = (82, 22, 38)
LIP = (196, 54, 98)
LIP_DK = (150, 34, 74)
TONGUE = (214, 98, 110)
TEETH = (250, 246, 240)
GEM = (70, 120, 220)
GEM_HI = (170, 210, 255)
LED = (255, 64, 72)
LED_HI = (255, 196, 190)
CHECK = (90, 220, 130)
SWEAT = (120, 196, 240)
SWEAT_HI = (220, 244, 255)
SPARK = (255, 240, 170)
SPARK2 = (255, 200, 80)
GLITCH = (255, 70, 110)
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


class G:
    """Body geometry in 'battle units' (Val is 84 units tall, t = top of hair),
    scaled by k so the same shapes are re-rasterised natively at world height."""

    def __init__(self, cv, c, t, k=1.0):
        self.cv, self.c, self.t, self.k = cv, c, t, k

    def x(self, dx):
        return self.c + dx * self.k

    def y(self, dy):
        return self.t + dy * self.k

    def p(self, dx, dy):
        return (self.x(dx), self.y(dy))

    def r(self, v, lo=0.6):
        return max(lo, v * self.k)

    def ell(self, dx, dy, rx, ry, ang=0.0):
        return self.cv.ell(self.x(dx), self.y(dy), self.r(rx), self.r(ry), ang)

    def poly(self, pts):
        return self.cv.poly([self.p(a, b) for a, b in pts])

    def rect(self, a, b, c, d):
        return self.cv.rect(self.x(a), self.y(b), self.x(c), self.y(d))

    def chain(self, pts, r):
        return self.cv.chain([self.p(a, b) for a, b in pts], self.r(r))

    def capsule(self, a, b, c, d, r0, r1=None):
        return self.cv.capsule(self.x(a), self.y(b), self.x(c), self.y(d), self.r(r0), None if r1 is None else self.r(r1))


def gold_piping(cv, part_names, against="jacket", lo=None):
    """Gold trim on lapel edges that meet the jacket (echoes val_small's gold-trimmed robe)."""
    gd = RAMP["gold"]
    if against not in cv.names:
        return
    jid = cv.names[against]
    for nm in part_names:
        if nm not in cv.names:
            continue
        pid = cv.names[nm]
        ys, xs = np.nonzero(cv.own == pid)
        for y, x in zip(ys, xs):
            nb = [(y, x + 1), (y, x - 1), (y + 1, x), (y - 1, x)]
            if any(0 <= a < cv.h and 0 <= b < cv.w and cv.own[a, b] == jid for a, b in nb):
                cv.col[y, x] = gd[3] if x < cv.w // 2 else gd[2]


def own(cv, name):
    return cv.own == cv.names[name] if name in cv.names else cv.empty()


def is_ink(cv):
    return (cv.col[..., 0] == INK[0]) & (cv.col[..., 1] == INK[1]) & (cv.col[..., 2] == INK[2])


# --------------------------------------------------------------------------
# props
# --------------------------------------------------------------------------
SCREEN_BIG = [        # 7 x 10, the candidate card on her tablet (battle size)
    "4444444",
    "1111111",
    "1hh1333",
    "1ss1111",
    "1bb1333",
    "1111111",
    "1333331",
    "1331111",
    "1111111",
    "1ggg1c1",
]
SCREEN_SMALL = [      # 4 x 6 (world size)
    "4444",
    "1s13",
    "1b11",
    "1331",
    "1111",
    "1gc1",
]
SCREEN_GLITCH_BIG = [
    "4444444",
    "1x11111",
    "1hhx333",
    "x1s1x11",
    "1bbx3x3",
    "11x1111",
    "x333x31",
    "13x1111",
    "1111x11",
    "xxx1x1x",
]


def screen_pal():
    s, h, sk, g = RAMP["screen"], RAMP["hair"], RAMP["skin"], RAMP["gold"]
    return {"1": s[1], "2": s[2], "3": s[3], "4": s[4], "h": h[1], "s": sk[3], "b": s[0],
            "g": g[3], "c": CHECK, "x": GLITCH, "w": WHITE}


def tablet(cv, x0, y0, bitmap, name="tablet", flare=False):
    """Axis-aligned tablet: ink outline, 1px black bezel, screen bitmap inside.
    (x0, y0) is the top-left outline pixel."""
    sw, sh = len(bitmap[0]), len(bitmap)
    w, h = sw + 4, sh + 4
    m = cv.rect(x0, y0, x0 + w - 1, y0 + h - 1)
    bk = RAMP["black"]
    cv.part(name, m, "black", edge="ink", lv=np.where(m, 1, 0))
    cv.put(x0 + 1, y0 + 1, bk[3])
    pal = screen_pal()
    for j, row in enumerate(bitmap):
        for i, ch in enumerate(row):
            col = pal[ch]
            if flare and ch in "13":
                col = mix(col, RAMP["screen"][4], 0.45)
            cv.put(x0 + 2 + i, y0 + 2 + j, col)
    return m


def brooch(cv, x, y):
    g = RAMP["gold"]
    cv.puts([(x, y - 1), (x - 1, y), (x + 1, y), (x, y + 1)], g[2])
    cv.put(x - 1, y - 1, g[4]); cv.put(x + 1, y + 1, g[1])
    cv.put(x + 1, y - 1, g[3]); cv.put(x - 1, y + 1, g[2])
    cv.put(x, y, GEM)


def sparkle(cv, x, y, big=True):
    if big:
        cv.puts([(x, y - 2), (x, y - 1), (x, y + 1), (x, y + 2), (x - 2, y), (x - 1, y), (x + 1, y), (x + 2, y)], SPARK2)
    else:
        cv.puts([(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)], SPARK2)
    cv.put(x, y, WHITE)


def sweat(cv, x, y, big=True):
    if big:
        cv.puts([(x, y), (x - 1, y + 1), (x, y + 1), (x + 1, y + 1), (x - 1, y + 2), (x, y + 2), (x + 1, y + 2), (x, y + 3)], SWEAT)
        cv.put(x - 1, y + 1, SWEAT_HI)
    else:
        cv.puts([(x, y), (x - 1, y + 1), (x, y + 1), (x, y + 2)], SWEAT)
        cv.put(x - 1, y + 1, SWEAT_HI)


# --------------------------------------------------------------------------
# body parts shared by battle (k=1) and world (k=54/84)
# --------------------------------------------------------------------------
def legs_front(g):
    cv = g.cv
    pants = g.poly([(-10.6, 54), (10.6, 54), (9.4, 77.4), (1.8, 77.4), (0.5, 62), (-0.5, 62), (-1.8, 77.4), (-9.4, 77.4)])
    pants &= ~cv.rect(g.c, g.y(63), g.c, cv.h)
    cv.part("pants", pants, "suitdk", rad=g.r(4), soft=1.0, cuts=(0.30, 0.55, 0.9))
    sd = RAMP["suitdk"]
    if g.k > 0.8:
        for s in (-1, 1):       # pressed creases
            x = round(g.x(s * 5.6))
            for y in range(round(g.y(64)), round(g.y(77))):
                if cv.own[y, x] == cv.names["pants"]:
                    cv.put(x, y, sd[3] if s < 0 else sd[1])
    bottom = cv.h - 1
    for s in (-1, 1):
        ank = g.rect(s * 5.6 - 1.6, 76.6, s * 5.6 + 1.6, 80.5)
        cv.part("ankle%d" % s, ank, "skin", lv=np.where(ank, 2, 0) + np.where(ank & (cv.X < g.x(s * 5.6)), 1, 0), noedge=("pants",))
        toe = (g.ell(s * 5.8, 81.4, 3.4, 2.4) | g.capsule(s * 5.8, 82.0, s * 9.0, 82.8, 1.6, 0.6))
        toe &= cv.half(y=bottom, below=False)
        cv.part("shoe%d" % s, toe, "black", rad=2, soft=0.6, cuts=(0.25, 0.5, 0.85))
        hx = round(g.x(s * 5.8 - 1.4))
        cv.put(hx, round(g.y(80.6)), RAMP["black"][4])


def jacket_front(g, hit=False):
    cv = g.cv
    sh = 1 if hit else 0
    body = g.poly([(-4.6, 27.4), (4.6, 27.4), (12, 28.0), (18.0, 29.0 + sh), (17.2, 33.5), (13, 37.5),
                   (9.4, 43.0), (12.8, 56.4), (4.0, 57.2), (0, 53.6), (-4.0, 57.2), (-12.8, 56.4),
                   (-9.4, 43.0), (-13, 37.5), (-17.2, 33.5), (-18.0, 29.0 - sh), (-12, 28.0)])
    cv.part("jacket", body, "suit", rad=g.r(11), soft=1.6, cuts=(0.26, 0.48, 0.84))
    su = RAMP["suit"]
    # blouse V + gold chain
    bl = g.poly([(-3.4, 28.0), (3.4, 28.0), (0.6, 39.5), (-0.6, 39.5)])
    cv.part("blouse", bl, "blouse", rad=g.r(3), soft=0.8, bias=0.1, noedge=("neck",))
    # peak lapels (satin, a tone lighter)
    for s in (-1, 1):
        lap = g.poly([(s * 4.7, 27.2), (s * 12.4, 29.6), (s * 10.0, 33.6), (s * 0.6, 42.6), (s * 0.4, 40.5)])
        lv = np.where(lap, 3 if s < 0 else 2, 0)
        cv.part("lapel%d" % s, lap, "suit", lv=lv, edge=su[0], noedge=())
    gold_piping(cv, ["lapel-1", "lapel1"])
    # double-breasted gold buttons
    gd = RAMP["gold"]
    for by_ in (43.4, 48.8):
        for s_ in (-1, 1):
            bx, by = round(g.x(s_ * 2.8)), round(g.y(by_))
            if g.k > 0.8:
                cv.put(bx, by, gd[3]); cv.put(bx + 1 if s_ > 0 else bx - 1, by, gd[2]) if False else None
                cv.put(bx, by + 1, gd[1])
            else:
                cv.put(bx, by, gd[3])
    # waist cinch shadow
    if g.k > 0.8:
        for s_ in (-1, 1):
            x0, y0 = round(g.x(s_ * 9.2)), round(g.y(44.0))
            cv.put(x0, y0, su[1]); cv.put(x0, y0 + 1, su[1]); cv.put(x0 + s_, y0 + 2, su[1])
    return body


def neck_front(g):
    cv = g.cv
    n = g.rect(-2.6, 21, 2.6, 29)
    cv.part("neck", n, "skin", lv=np.where(n, 2, 0))
    sk = RAMP["skin"]
    for x in range(round(g.x(-2.6)), round(g.x(2.6)) + 1):
        cv.put(x, round(g.y(25.6)), sk[1])
        if g.k > 0.8:
            cv.put(x, round(g.y(26.6)), sk[1])


def arm(g, name, pts, r=3.3, cuff=True):
    cv = g.cv
    m = g.chain(pts, r)
    cv.part(name, m, "suit", rad=g.r(3.5), soft=1.0, cuts=(0.30, 0.55, 0.88))
    if cuff:
        (xa, ya), (xb, yb) = g.p(*pts[-2]), g.p(*pts[-1])
        L = math.hypot(xb - xa, yb - ya)
        ux, uy = (xb - xa) / L, (yb - ya) / L
        w = max(1.0, 1.4 * g.k)
        band = m & cv.capsule(xb - ux * w, yb - uy * w, xb, yb, g.r(r) + 0.6) & ~cv.capsule(xa, ya, xb - ux * w, yb - uy * w, g.r(r) + 0.6)
        cv.fill(band & ~is_ink(cv) & (own(cv, name)), RAMP["blouse"][2])
    return m


def hand(g, name, dx, dy, rx=2.5, ry=2.5):
    cv = g.cv
    m = g.ell(dx, dy, rx, ry)
    cv.part(name, m, "skin", edge="ink", rad=g.r(2.4), soft=0.6, bias=0.06)
    return m


def palm(g, name, dx, dy, tilt=0.0, thumb=1):
    """Open hand, fingers up: a mitten block with finger splits drawn inside,
    so the outline cannot swallow single-pixel fingers."""
    cv = g.cv
    big = g.k > 0.8
    w, h = (3.0, 4.2) if big else (2.0, 2.6)
    m = cv.ell(g.x(dx), g.y(dy), w, h, tilt)
    m |= cv.ell(g.x(dx), g.y(dy) + h * 0.5, w + 0.3, h * 0.6, tilt)
    tx = g.x(dx) + thumb * (w + (0.9 if big else 0.4))
    m |= cv.capsule(g.x(dx) + thumb * w * 0.4, g.y(dy) + h * 0.5, tx, g.y(dy) - (0.6 if big else 0.2), 1.1 if big else 0.7)
    lv = np.where(m, 3, 0) - np.where(m & (cv.X * thumb > (g.x(dx) + 0.5) * thumb), 1, 0)
    cv.part(name, m, "skin", edge="ink", lv=lv)
    if big:
        sk = RAMP["skin"]
        x0, y0 = round(g.x(dx)), round(g.y(dy) - h)
        for fx in (x0 - 1, x0 + 1):
            for y in (y0 + 1, y0 + 2):
                if cv.own[y, fx] == cv.names[name]:
                    cv.put(fx, y, sk[1])
    return m


def finger(g, name, pts, r=0.9):
    cv = g.cv
    m = cv.chain([g.p(a, b) for a, b in pts], max(0.55, r * g.k))
    cv.part(name, m, "skin", edge=None, lv=np.where(m, 3, 0))
    return m


# --------------------------------------------------------------------------
# head (front) -- big = battle, else world
# --------------------------------------------------------------------------
def hair_back(g, dx=0, dy=0):
    cv = g.cv
    hb = g.ell(dx, dy + 12.5, 12.8, 12.5) | g.rect(dx - 12.6, dy + 12.5, dx + 12.6, dy + 23.6)
    hb &= ~g.rect(dx + 11.8, dy + 22.8, dx + 20, dy + 30) & ~g.rect(dx - 20, dy + 22.8, dx - 11.8, dy + 30)
    cv.part("hairback", hb, "hair", rad=g.r(9), soft=1.4, cuts=(0.30, 0.55, 0.86))
    return hb


def head_front(g, pose, big, dx=0, dy=0, mic_up=False, loose=False):
    cv = g.cv
    sk, hr = RAMP["skin"], RAMP["hair"]
    face = g.ell(dx, dy + 15, 8.6, 10.0)
    lv = np.where(face, 3, 0)
    lv = np.where(face & ~g.ell(dx - 0.8, dy + 14.4, 8.0, 9.6), 2, lv)          # rim shade, right + chin
    lv = np.where(face & (cv.X < g.x(dx - 0.5)) & ~g.ell(dx + 0.4, dy + 15.4, 8.6, 10.2), 3, lv)
    lv = np.where(face & g.ell(dx - 3.6, dy + 12.4, 2.6, 2.2), 4, lv)          # forehead/cheek light
    lv = np.where(face & (cv.Y >= g.y(dy + 23.6)) & (cv.X > g.x(dx - 3)), 2, lv)
    cv.part("face", face, "skin", lv=lv)
    part_x = dx + 3.0

    def fb(xu):  # fringe bottom (units) for a column (units)
        return 7.6 + (part_x - xu) * 0.30 if xu < part_x else 7.0 + (xu - part_x) * 0.48

    xu = (cv.X - g.c) / g.k
    fbm = np.vectorize(fb)(xu) if False else np.where(xu < part_x, 7.6 + (part_x - xu) * 0.30, 7.0 + (xu - part_x) * 0.48)
    yu = (cv.Y - g.t) / g.k
    front = face & ((yu < fbm + dy) | (np.abs(xu - dx) > 6.9) & (yu > dy + 6))
    front |= g.ell(dx, dy + 12.5, 12.8, 12.5) & ~face & cv.half(y=g.y(dy + 6.5), below=False)
    cv.part("fringe", front, "hair", noedge=("hairback",), rad=g.r(8), soft=1.2, cuts=(0.28, 0.52, 0.84))
    # glossy shine band on the crown (polished!)
    shine = (g.ell(dx - 1.5, dy + 9.5, 9.6, 8.2) & ~g.ell(dx - 1.5, dy + 10.4, 8.4, 7.4)) & cv.half(y=g.y(dy + 6.5), below=False)
    shine &= (own(cv, "fringe") | own(cv, "hairback")) & ~is_ink(cv)
    shine &= cv.X < g.x(dx + 6)
    for y, x in zip(*np.nonzero(shine)):
        cv.put(x, y, hr[4] if x < g.x(dx - 2) else hr[3])
    # side part
    if big:
        cv.line(g.x(part_x), g.y(dy + 1.5), g.x(part_x) + 1, g.y(dy + 5), hr[0])
    c, t = round(g.x(dx)), round(g.y(dy))
    if big:
        face_big(cv, c, t, pose)
    else:
        face_small(cv, c, t, pose)
    if loose:
        # a strand knocked loose
        if big:
            cv.puts([(c - 2, t + 8), (c - 2, t + 9), (c - 1, t + 10), (c - 1, t + 11)], hr[1])
        else:
            cv.put(c - 1, t + 6, hr[1])
    headset_front(g, dx, dy, big, mic_up)


def headset_front(g, dx, dy, big, mic_up=False):
    cv = g.cv
    bk = RAMP["black"]
    # band across the crown, just inside the hair edge
    band = (g.ell(dx, dy + 12.6, 11.4, 11.2) & ~g.ell(dx, dy + 12.6, 11.4 - 1.05 / g.k, 11.2 - 1.05 / g.k)) & cv.half(y=g.y(dy + 11), below=False)
    band &= cv.X > g.x(dx - 11.0)
    if not big:
        band &= False
    for y, x in zip(*np.nonzero(band)):
        cv.put(x, y, bk[3] if x < g.x(dx - 4) else bk[2])
    pad = g.ell(dx + 12.0, dy + 16.5, 2.0, 3.0)
    cv.part("earpad", pad, "black", edge="ink", rad=2, bias=0.1)
    c, t = round(g.x(dx)), round(g.y(dy))
    if big:
        if mic_up:
            cv.line(c + 12, t + 14, c + 15, t + 9, bk[2]); cv.put(c + 15, t + 8, bk[1]); cv.put(c + 16, t + 8, bk[1])
            cv.put(c + 16, t + 7, LED)
        else:
            cv.line(c + 11, t + 19, c + 8, t + 22, bk[2])
            cv.puts([(c + 6, t + 22), (c + 7, t + 22), (c + 6, t + 23), (c + 7, t + 23)], bk[1])
            cv.put(c + 6, t + 22, bk[3])
        cv.put(c + 12, t + 15, LED); cv.put(c + 12, t + 16, mix(LED, bk[1], 0.5))
    else:
        if mic_up:
            cv.line(c + 8, t + 9, c + 10, t + 6, bk[2]); cv.put(c + 10, t + 5, LED)
        else:
            cv.line(c + 7, t + 12, c + 5, t + 14, bk[2])
            cv.put(c + 4, t + 14, bk[1])
        cv.put(c + 8, t + 10, LED)


def face_big(cv, c, t, pose):
    sk = RAMP["skin"]
    hr = RAMP["hair"]
    # eyes: val_small's tall dark ovals, grown up with lashes
    for s in (-1, 1):
        a, b = (c - 5, c - 4) if s < 0 else (c + 4, c + 5)
        outer = a - 1 if s < 0 else b + 1
        if pose in ("idle", "talk", "tell"):
            for y in range(t + 14, t + 18):
                cv.put(a, y, EYE); cv.put(b, y, EYE)
            cv.put(a, t + 15, IRIS); cv.put(b, t + 16, IRIS); cv.put(a, t + 16, IRIS); cv.put(b, t + 15, IRIS)
            cv.put(a, t + 14 + 1, WHITE) if pose != "tell" else None
            cv.put(outer, t + 14, EYE); cv.put(outer + (-1 if s < 0 else 1), t + 13, EYE)
            cv.hline(a, b, t + 18, sk[1])
            if pose == "tell":
                cv.put(a, t + 15, SPARK); cv.put(b, t + 16, WHITE)
        elif pose == "hit":
            # squeezed shut: > <
            if s < 0:
                cv.puts([(a - 1, t + 14), (a, t + 15), (b, t + 16), (a, t + 17), (a - 1, t + 18)], EYE)
            else:
                cv.puts([(b + 1, t + 14), (b, t + 15), (a, t + 16), (b, t + 17), (b + 1, t + 18)], EYE)
        elif pose == "down":
            for y in range(t + 16, t + 18):
                cv.put(a, y, EYE); cv.put(b, y, EYE)
            cv.hline(a - (1 if s < 0 else 0), b + (1 if s > 0 else 0), t + 15, EYE)
            cv.hline(a, b, t + 18, sk[1])
        elif pose == "blink":
            cv.hline(a - (1 if s < 0 else 0), b + (1 if s > 0 else 0), t + 17, EYE)
            cv.put(outer + (-1 if s < 0 else 1), t + 16, EYE)
    # brows: thin, groomed arches
    for s in (-1, 1):
        ix = c - 3 if s < 0 else c + 3
        lift = -1 if pose == "tell" and s > 0 else 0
        if pose == "hit":
            pts = [(ix, t + 11), (ix + s, t + 11), (ix + 2 * s, t + 12), (ix + 3 * s, t + 12)]
        else:
            pts = [(ix, t + 12 + lift), (ix + s, t + 11 + lift), (ix + 2 * s, t + 11 + lift), (ix + 3 * s, t + 12 + lift)]
        for x, y in pts:
            if cv.own[y, x] == cv.names["face"]:
                cv.put(x, y, hr[1])
    # nose
    cv.put(c - 1, t + 18, sk[3]); cv.put(c + 1, t + 19, sk[1]); cv.put(c, t + 19, sk[2])
    # blush
    for s in (-1, 1):
        for x in (c + s * 6, c + s * 7):
            if cv.own[t + 18, x] == cv.names["face"]:
                cv.put(x, t + 18, mix(cv.get(x, t + 18), BLUSH, 0.55))
    # mouth: always the bright interview smile
    y = t + 21
    if pose in ("idle", "blink", "down"):
        cv.hline(c - 3, c + 3, y, MOUTH)
        cv.hline(c - 2, c + 2, y, TEETH)
        cv.put(c - 4, y - 1, LIP_DK); cv.put(c + 4, y - 1, LIP_DK)
        cv.hline(c - 2, c + 2, y + 1, LIP)
    elif pose == "talk":
        cv.hline(c - 3, c + 3, y, LIP_DK)
        cv.hline(c - 2, c + 2, y, TEETH)
        cv.hline(c - 3, c + 3, y + 1, MOUTH)
        cv.hline(c - 1, c + 1, y + 2, TONGUE); cv.put(c - 2, y + 2, MOUTH); cv.put(c + 2, y + 2, MOUTH)
        cv.put(c - 4, y - 1, LIP_DK); cv.put(c + 4, y - 1, LIP_DK)
        cv.hline(c - 1, c + 1, y + 3, LIP)
    elif pose == "tell":
        cv.hline(c - 4, c + 4, y, MOUTH)
        cv.hline(c - 3, c + 3, y, TEETH)
        cv.put(c - 5, y - 1, LIP_DK); cv.put(c + 5, y - 1, LIP_DK); cv.put(c + 5, y - 2, LIP_DK)
        cv.hline(c - 3, c + 3, y + 1, MOUTH)
        cv.hline(c - 2, c + 2, y + 2, LIP)
    elif pose == "hit":       # gritted, but still smiling
        cv.hline(c - 3, c + 3, y - 1, MOUTH)
        cv.hline(c - 3, c + 3, y, TEETH); cv.hline(c - 3, c + 3, y + 1, TEETH)
        cv.put(c - 4, y, MOUTH); cv.put(c + 4, y, MOUTH); cv.put(c - 4, y + 1, MOUTH); cv.put(c + 4, y + 1, MOUTH)
        cv.put(c - 1, y + 1, MOUTH); cv.put(c + 1, y + 1, MOUTH)
        cv.hline(c - 3, c + 3, y + 2, MOUTH)
        cv.put(c - 5, y - 1, LIP_DK); cv.put(c + 5, y - 1, LIP_DK)


def face_small(cv, c, t, pose):
    sk, hr = RAMP["skin"], RAMP["hair"]
    for s in (-1, 1):
        a_, b_ = (c - 3, c - 2) if s < 0 else (c + 2, c + 3)
        outer = a_ if s < 0 else b_
        if pose in ("idle", "talk", "tell"):
            for x in (a_, b_):
                cv.put(x, t + 10, EYE); cv.put(x, t + 11, EYE)
            cv.put(a_, t + 10, WHITE if pose != "tell" else SPARK)
            cv.put(outer, t + 9, EYE)
        elif pose == "hit":
            cv.put(outer, t + 9, EYE); cv.put(a_ if s > 0 else b_, t + 10, EYE); cv.put(outer, t + 11, EYE)
        elif pose == "blink":
            cv.hline(a_, b_, t + 11, EYE); cv.put(outer, t + 10, EYE)
        elif pose == "down":
            cv.hline(a_, b_, t + 11, EYE); cv.put(outer, t + 10, EYE); cv.put(a_ if s < 0 else b_, t + 11, IRIS)
    # brows
    for s in (-1, 1):
        ex = c - 2 if s < 0 else c + 2
        yb = t + 8 if pose != "hit" else t + 8
        for x in (ex, ex + s):
            if cv.own[yb, x] == cv.names["face"]:
                cv.put(x, yb, hr[2] if x == ex else hr[1])
    cv.put(c + 1, t + 12, sk[1])
    for s in (-1, 1):
        x = c + s * 4
        if cv.own[t + 12, x] == cv.names["face"]:
            cv.put(x, t + 12, mix(cv.get(x, t + 12), BLUSH, 0.6))
    y = t + 14
    if pose in ("idle", "blink", "down"):
        cv.hline(c - 2, c + 2, y, MOUTH); cv.hline(c - 1, c + 1, y, TEETH)
        cv.put(c - 2, y - 1, LIP_DK) if False else None
        cv.hline(c - 1, c + 1, y + 1, LIP)
    elif pose == "talk":
        cv.hline(c - 1, c + 1, y, TEETH); cv.put(c - 2, y, LIP_DK); cv.put(c + 2, y, LIP_DK)
        cv.hline(c - 1, c + 1, y + 1, MOUTH)
    elif pose == "tell":
        cv.hline(c - 2, c + 2, y, MOUTH); cv.hline(c - 1, c + 2, y, TEETH); cv.put(c + 3, y - 1, LIP_DK)
        cv.hline(c - 1, c + 1, y + 1, LIP)
    elif pose == "hit":
        cv.hline(c - 2, c + 2, y, MOUTH); cv.put(c - 1, y, TEETH); cv.put(c + 1, y, TEETH)


# ==========================================================================
# FRONT (battle 84 px, world 54 px)
# ==========================================================================
BW, BH = 84, 92
WW, WH = 52, 58
WK = 54 / 84


def canvas(world):
    if world:
        cv = Cv(WW, WH)
        return cv, G(cv, WW // 2, WH - 54, WK)
    cv = Cv(BW, BH)
    return cv, G(cv, 42, BH - 84, 1.0)


def front(pose, world=False):
    """pose: idle, talk, tell, hit (cells 0-3); world extras: blink, phone, call."""
    cv, g = canvas(world)
    big = not world
    hx, hy = ((2 if big else 1 / WK), 0) if pose == "hit" else (0, 0)
    face_pose = {"phone": "down", "call": "idle"}.get(pose, pose)
    hair_back(g, hx, hy)
    legs_front(g)
    neck_front(g)
    jacket_front(g, hit=(pose == "hit"))
    bx, by = g.p(-6.6, 34.4)
    brooch(cv, round(bx), round(by)) if big else cv.put(round(bx), round(by), GEM)
    scr = SCREEN_BIG if big else SCREEN_SMALL
    tw, th = len(scr[0]) + 4, len(scr) + 4

    def tab_at(ux, uy, bitmap=None, flare=False, anchor="tl"):
        x0, y0 = g.p(ux, uy)
        x0, y0 = round(x0), round(y0)
        if anchor == "c":
            x0 -= tw // 2; y0 -= th // 2
        tablet(cv, x0, y0, bitmap or scr, flare=flare)
        return x0, y0

    # ---- viewer-left arm (her right) ----
    if pose in ("idle", "tell_unused", "blink"):
        arm(g, "armL", [(-14.4, 31.2), (-19.6, 39.4), (-13.6, 45.4)])
        hand(g, "handL", -12.4, 45.6, 2.6, 2.4)
    elif pose == "talk":
        arm(g, "armL", [(-14.4, 31.2), (-20.6, 37.6), (-21.6, 30.0)])
        palm(g, "handL", -21.6, 26.4, thumb=1)
    elif pose == "tell":
        arm(g, "armL", [(-14.4, 31.2), (-20.6, 35.0), (-26.4, 33.0)])
        hand(g, "handL", -27.6, 32.6, 2.4, 2.3)
        if big:
            finger(g, "point", [(-28.4, 32.0), (-32.4, 32.0)], 1.45)
        else:
            finger(g, "point", [(-29.0, 32.0), (-32.2, 31.6)], 0.7)
    elif pose == "hit":
        arm(g, "armL", [(-14.4, 31.6), (-21.4, 30.4), (-24.4, 23.6)])
        palm(g, "handL", -24.8, 20.0, tilt=-0.2, thumb=1)
    elif pose == "phone":
        arm(g, "armL", [(-14.4, 31.2), (-17.4, 39.6), (-6.0, 41.6)])
    elif pose == "call":
        arm(g, "armL", [(-14.4, 31.2), (-16.8, 39.8), (-15.6, 45.6)])

    # ---- viewer-right arm (her left) + tablet ----
    if pose in ("idle", "talk", "blink"):
        arm(g, "armR", [(14.4, 31.2), (17.0, 39.4), (16.6, 44.6)])
        tab_at(11.4, 44.0)
        hand(g, "handR", 16.4, 45.6, 2.5, 2.3)
    elif pose == "tell":
        arm(g, "armR", [(14.4, 31.2), (21.0, 29.0), (21.6, 23.0)])
        x0, y0 = tab_at(15.6, 5.4, flare=True)
        hand(g, "handR", 21.4, 20.6, 2.5, 2.4)
        sparkle(cv, x0 + tw - 1, y0, big)
        sparkle(cv, x0 - 1 if big else x0, y0 + th // 2, False)
    elif pose == "hit":
        arm(g, "armR", [(14.4, 31.6), (17.4, 39.4), (8.6, 41.0)])
        tab_at(1.0, 33.0, SCREEN_GLITCH_BIG if big else ["4444", "x1s3", "1bx1", "x331", "11x1", "x1cx"])
        hand(g, "handR", 8.4, 41.2, 2.5, 2.4)
    elif pose == "phone":
        arm(g, "armR", [(14.4, 31.2), (16.8, 39.6), (10.4, 42.0)])
        tab_at(-2.0, 33.6)
        hand(g, "handR", 9.8, 42.2, 2.4, 2.3)
        hand(g, "handL", -5.0, 40.6, 2.3, 2.2)
        finger(g, "tap", [(-4.0, 39.0), (-2.6, 37.4)], 0.7)
    elif pose == "call":
        arm(g, "armR", [(14.4, 31.2), (19.6, 32.6), (15.4, 21.6)])
        hand(g, "handR", 14.8, 18.8, 2.4, 2.8)
    if pose == "call":
        tab_at(-20.4, 39.0)
        hand(g, "handL", -15.4, 46.4, 2.4, 2.2)

    head_front(g, face_pose, big, hx, hy, mic_up=(pose == "hit"), loose=(pose == "hit"))
    if pose == "call":
        hand(g, "handR2", 14.8, 18.8, 2.4, 2.8)
    if pose == "hit":
        c, t = round(g.x(hx)), round(g.y(hy))
        if big:
            sweat(cv, c + 17, t + 4)
        else:
            sweat(cv, c + 11, t + 2, False)
    cv.outline()
    return cv


def preview(cvs, name, S=8, bg=(44, 44, 62)):
    ims = [c.image() if hasattr(c, "image") else c for c in cvs]
    W = sum(i.width for i in ims) + 2 * (len(ims) + 1)
    H = max(i.height for i in ims) + 4
    sheet = Image.new("RGBA", (W, H), bg + (255,))
    x = 2
    for i in ims:
        sheet.alpha_composite(i, (x, H - 2 - i.height))
        x += i.width + 2
    os.makedirs(PREV, exist_ok=True)
    sheet.resize((W * S, H * S), Image.NEAREST).save(os.path.join(PREV, name))


if __name__ == "__main__" and "--try" in sys.argv:
    preview([front(p) for p in ("idle", "talk", "tell", "hit")], "front.png", 5)
    preview([front(p, True) for p in ("idle", "talk", "tell", "hit", "blink", "phone", "call")], "wfront.png", 6)


# ==========================================================================
# SIDE (facing right) and BACK
# ==========================================================================
def side(world=False):
    cv, g = canvas(world)
    g.c -= round(2 * g.k)
    big = not world
    sk, hr, su, bk = RAMP["skin"], RAMP["hair"], RAMP["suit"], RAMP["black"]
    bottom = cv.h - 1
    hcx = round(-3.0 * g.k) / g.k      # crown centre on a whole pixel so the top row exists
    # back hair mass
    hb = g.ell(hcx, 12.5, 11.8, 12.5) | g.rect(-13.6, 12.5, 1.6, 23.4)
    hb &= ~g.rect(-30, 22.6, -12.6, 40)
    cv.part("hairback", hb, "hair", rad=g.r(9), soft=1.4, cuts=(0.30, 0.55, 0.86))
    # legs: back leg, then front leg, both in pumps
    for name, ox in (("B", -4.4), ("F", 1.8)):
        leg = g.poly([(ox - 4.4, 54), (ox + 4.6, 54), (ox + 3.6, 77.4), (ox - 3.0, 77.4)])
        lv = None if name == "F" else np.where(leg, 1, 0) + np.where(leg & (cv.X < g.x(ox)), 1, 0)
        cv.part("leg" + name, leg, "suitdk", lv=lv, rad=g.r(4), soft=1.0, cuts=(0.30, 0.55, 0.9))
        ank = g.rect(ox - 1.4, 76.8, ox + 1.6, 80.0)
        cv.part("ankle" + name, ank, "skin", lv=np.where(ank, 2 if name == "F" else 1, 0))
        shoe = g.poly([(ox - 2.2, 79.2), (ox + 2.6, 79.6), (ox + 9.6, 82.6), (ox + 9.6, 83.6), (ox + 2.4, 83.6),
                       (ox + 0.6, 81.6), (ox - 1.0, 81.8), (ox - 1.0, 83.6), (ox - 2.2, 83.6)])
        shoe &= cv.half(y=bottom, below=False)
        cv.part("shoe" + name, shoe, "black", lv=np.where(shoe, 2, 0) + np.where(shoe & (cv.Y <= g.y(80.4)), 1, 0))
        if big:
            cv.put(round(g.x(ox + 5.0)), round(g.y(80.8)), bk[4])
    if big:
        cv.vline(round(g.x(4.0)), round(g.y(64)), round(g.y(76)), RAMP["suitdk"][3])
    neck = g.rect(-1.4, 20, 3.4, 29)
    cv.part("neck", neck, "skin", lv=np.where(neck, 2, 0) + np.where(neck & (cv.X > g.x(1.6)), 1, 0))
    # jacket (profile)
    body = g.poly([(-5.0, 27.6), (5.6, 27.6), (8.6, 31.6), (8.8, 36.0), (6.0, 43.0), (8.2, 56.4),
                   (-8.6, 56.4), (-6.4, 43.0), (-7.8, 36.0), (-7.4, 30.4)])
    body |= g.ell(-0.6, 29.6, 7.2, 2.8)
    cv.part("jacket", body, "suit", rad=g.r(10), soft=1.6, cuts=(0.26, 0.48, 0.84))
    bl = g.poly([(4.0, 27.6), (6.6, 28.6), (6.0, 32.0)])
    cv.part("blouse", bl, "blouse", lv=np.where(bl, 3, 0), noedge=("neck",))
    lap = g.poly([(3.6, 27.4), (8.0, 31.0), (8.4, 34.0), (5.6, 42.6), (4.4, 42.6), (6.0, 33.0)])
    cv.part("lapel", lap, "suit", lv=np.where(lap, 3, 0), edge=su[0])
    gold_piping(cv, ["lapel"])
    if big:
        cv.put(round(g.x(6.6)), round(g.y(44.0)), RAMP["gold"][3])
        cv.put(round(g.x(6.6)), round(g.y(49.4)), RAMP["gold"][3])
        for y in range(round(g.y(46)), round(g.y(56))):   # back vent / side seam
            x = round(g.x(-3.0))
            if cv.own[y, x] == cv.names["jacket"]:
                cv.put(x, y, su[1])
    # tablet held at the hip, screen facing forward (a sliver of glow)
    tx0, ty0 = round(g.x(5.0)), round(g.y(42.0))
    tw, th = (4, 15) if big else (3, 10)
    tm = cv.rect(tx0, ty0, tx0 + tw - 1, ty0 + th - 1)
    cv.part("tablet", tm, "black", edge="ink", lv=np.where(tm, 1, 0))
    sc = RAMP["screen"]
    for y in range(ty0 + 1, ty0 + th - 1):
        cv.put(tx0 + tw - 2, y, sc[3] if (y - ty0) % 4 else sc[4])
    # near arm, hand gripping the tablet
    arm(g, "arm", [(-0.6, 31.0), (-0.2, 40.0), (3.4, 46.0)], r=3.2)
    hand(g, "hand", 4.4, 47.0, 2.4, 2.4)
    # head (profile)
    face = g.ell(3.4, 14.6, 7.2, 9.8) | g.ell(5.6, 19.4, 4.4, 5.4)
    lv = np.where(face, 3, 0)
    lv = np.where(face & (cv.Y > g.y(22.6)), 2, lv)
    lv = np.where(face & g.ell(5.0, 12.6, 2.4, 2.0), 4, lv)
    cv.part("face", face, "skin", lv=lv)
    nose = g.ell(10.0, 17.6, 1.4, 1.6) | g.poly([(8.8, 15.2), (10.4, 18.6), (8.6, 18.8)])
    cv.part("nose", nose, "skin", lv=np.where(nose, 3, 0), noedge=("face",))
    # front hair: crown + fringe swept toward the face, bob to the jaw
    front = (g.ell(hcx, 12.5, 11.8, 12.5) | g.rect(-13.6, 12.5, 0.6, 23.4)) & ~g.rect(-30, 22.6, -12.6, 40)
    front &= ~(face & (cv.X > g.x(0.8)) & (cv.Y > g.y(7.0)))
    front |= face & (cv.Y < g.y(7.0) + (cv.X - g.x(1.0)) * 0.42) & (cv.X < g.x(9.6))
    front &= ~(cv.Y > g.y(23.6))
    cv.part("hair", front, "hair", noedge=("hairback",), rad=g.r(9), soft=1.4, cuts=(0.28, 0.52, 0.84))
    shine = (g.ell(-2.0, 10.0, 9.0, 7.6) & ~g.ell(-2.0, 10.8, 7.8, 6.8)) & cv.half(y=g.y(9.0), below=False)
    shine &= own(cv, "hair") & ~is_ink(cv) & (cv.X < g.x(4))
    for y, x in zip(*np.nonzero(shine)):
        cv.put(x, y, hr[4] if x < g.x(-4) else hr[3])
    c, t = round(g.x(0)), round(g.y(0))
    if big:
        for y in range(t + 14, t + 18):
            cv.put(c + 6, y, EYE); cv.put(c + 7, y, EYE)
        cv.put(c + 7, t + 15, WHITE); cv.put(c + 6, t + 16, IRIS)
        cv.put(c + 5, t + 14, EYE); cv.put(c + 4, t + 13, EYE)
        cv.hline(c + 6, c + 7, t + 18, sk[1])
        cv.hline(c + 5, c + 8, t + 11, hr[1]); cv.put(c + 9, t + 12, hr[1])
        cv.put(c + 5, t + 18, mix(sk[3], BLUSH, 0.55)); cv.put(c + 4, t + 18, mix(sk[3], BLUSH, 0.55))
        cv.hline(c + 6, c + 9, t + 21, MOUTH); cv.hline(c + 7, c + 9, t + 21, TEETH)
        cv.put(c + 5, t + 20, LIP_DK); cv.hline(c + 7, c + 8, t + 22, LIP)
        cv.put(c + 9, t + 18, sk[1])
    else:
        cv.put(c + 4, t + 9, EYE); cv.put(c + 4, t + 10, EYE); cv.put(c + 3, t + 9, EYE)
        cv.put(c + 5, t + 11, mix(sk[3], BLUSH, 0.5)) if False else None
        cv.hline(c + 4, c + 6, t + 14, MOUTH); cv.put(c + 5, t + 14, TEETH)
        cv.hline(c + 3, c + 5, t + 7, hr[1])
    # headset: band over the crown, pad on the (left) ear, boom to the mouth
    if big:
        for y, x in zip(*np.nonzero((g.ell(-1, 12.5, 10.6, 11.4) & ~g.ell(-1, 12.5, 9.6, 10.4)) & cv.half(y=g.y(16), below=False) & (cv.X > g.x(-2.6)) & (cv.X < g.x(0.6)))):
            cv.put(x, y, bk[2])
    pad = g.ell(0.2, 16.4, 2.0, 3.0)
    cv.part("earpad", pad, "black", edge="ink", rad=2, bias=0.1)
    if big:
        cv.line(c + 1, t + 19, c + 4, t + 22, bk[2]); cv.put(c + 5, t + 23, bk[1]); cv.put(c + 4, t + 23, bk[1])
        cv.put(c, t + 15, LED)
    else:
        cv.line(c + 1, t + 12, c + 3, t + 14, bk[2]); cv.put(c, t + 10, LED)
    cv.outline()
    return cv


def back(world=False):
    cv, g = canvas(world)
    big = not world
    su, hr, bk = RAMP["suit"], RAMP["hair"], RAMP["black"]
    bottom = cv.h - 1
    pants = g.poly([(-10.6, 54), (10.6, 54), (9.4, 77.4), (1.8, 77.4), (0.5, 62), (-0.5, 62), (-1.8, 77.4), (-9.4, 77.4)])
    pants &= ~cv.rect(g.c, g.y(63), g.c, cv.h)
    cv.part("pants", pants, "suitdk", rad=g.r(4), soft=1.0, cuts=(0.30, 0.55, 0.9))
    for s in (-1, 1):
        ank = g.rect(s * 5.6 - 1.6, 76.6, s * 5.6 + 1.6, 80.5)
        cv.part("ankle%d" % s, ank, "skin", lv=np.where(ank, 2, 0), noedge=("pants",))
        heel = g.ell(s * 5.6, 81.2, 2.8, 2.2) & cv.half(y=g.y(80.0))
        heel |= g.rect(s * 5.6 - 0.6, 81.0, s * 5.6 + 0.6, 84.0)
        heel &= cv.half(y=bottom, below=False)
        cv.part("shoe%d" % s, heel, "black", lv=np.where(heel, 2, 0))
    neck = g.rect(-2.6, 21, 2.6, 29)
    cv.part("neck", neck, "skin", lv=np.where(neck, 2, 0))
    body = g.poly([(-4.6, 27.4), (4.6, 27.4), (12, 28.0), (18.0, 29.0), (17.2, 33.5), (13, 37.5),
                   (9.4, 43.0), (12.8, 56.4), (-12.8, 56.4), (-9.4, 43.0), (-13, 37.5), (-17.2, 33.5), (-18.0, 29.0), (-12, 28.0)])
    cv.part("jacket", body, "suit", rad=g.r(11), soft=1.6, cuts=(0.26, 0.48, 0.84))
    coll = g.poly([(-5.2, 27.0), (5.2, 27.0), (4.0, 30.0), (-4.0, 30.0)])
    cv.part("collar", coll, "suit", lv=np.where(coll, 3, 0), edge=su[0])
    x = round(g.x(0))
    for y in range(round(g.y(31)), round(g.y(56))):
        if cv.own[y, x] == cv.names["jacket"]:
            cv.put(x, y, su[1])
    if big:
        for s in (-1, 1):
            for y in range(round(g.y(38)), round(g.y(47))):
                xx = round(g.x(s * 6.5))
                cv.put(xx, y, su[1])
        cv.put(x - 1, round(g.y(50)), su[0]); cv.put(x + 1, round(g.y(50)), su[0])
    arm(g, "armL", [(-14.4, 31.2), (-16.8, 39.6), (-16.0, 45.0)])
    arm(g, "armR", [(14.4, 31.2), (16.8, 39.6), (16.0, 45.0)])
    # tablet back (her left hand is on the viewer's left from behind)
    tx0, ty0 = round(g.x(-21.6)), round(g.y(43.0))
    tw, th = (11, 14) if big else (7, 9)
    tm = cv.rect(tx0, ty0, tx0 + tw - 1, ty0 + th - 1)
    cv.part("tablet", tm, "black", edge="ink", lv=np.where(tm, 2, 0))
    cv.put(tx0 + tw // 2, ty0 + th // 2 - 1, bk[4])
    cv.put(tx0 + 1, ty0 + 1, bk[3])
    hand(g, "handL", -16.0, 46.4, 2.4, 2.4)
    hand(g, "handR", 16.0, 46.6, 2.4, 2.4)
    hb = g.ell(0, 12.5, 12.8, 12.5) | g.rect(-12.6, 12.5, 12.6, 23.6)
    hb &= ~g.rect(11.8, 22.8, 20, 30) & ~g.rect(-20, 22.8, -11.8, 30)
    cv.part("hair", hb, "hair", rad=g.r(9), soft=1.4, cuts=(0.30, 0.55, 0.86))
    shine = (g.ell(-1.5, 9.5, 9.6, 8.2) & ~g.ell(-1.5, 10.4, 8.4, 7.4)) & own(cv, "hair") & ~is_ink(cv) & (cv.X < g.x(6))
    for y, xx in zip(*np.nonzero(shine)):
        cv.put(xx, y, hr[4] if xx < g.x(-2) else hr[3])
    if big:   # a few strand lines in the bob
        for (a, b, c2, d) in [(-6, 14, -7, 22), (-1, 13, -1, 23), (5, 14, 6, 22), (9, 15, 10, 21)]:
            cv.line(g.x(a), g.y(b), g.x(c2), g.y(d), hr[1])
    band = (g.ell(0, 12.6, 11.4, 11.2) & ~g.ell(0, 12.6, 10.35, 10.15)) & cv.half(y=g.y(11), below=False) if big else cv.empty()
    for y, xx in zip(*np.nonzero(band & (cv.X < g.x(11)))):
        cv.put(xx, y, bk[2])
    pad = g.ell(-12.0, 16.5, 2.0, 3.0)
    cv.part("earpad", pad, "black", edge="ink", rad=2, bias=0.1)
    c, t = round(g.x(0)), round(g.y(0))
    cv.put(c - 12 if big else round(g.x(-12)), t + (15 if big else 10), LED)
    cv.outline()
    return cv


if __name__ == "__main__" and "--try2" in sys.argv:
    preview([front("idle"), side(), back(), front("idle", True), side(True), back(True)], "sideback.png", 6)


# ==========================================================================
# PORTRAITS (64 x 64, head and shoulders)
# ==========================================================================
PW = PH = 64

EYE_MAPS = {
    # viewer-left eye, outer corner on the left; mirrored for the right eye
    "neutral": ["L.....",
                "KKKKK.",
                "KHIIK.",
                ".KIIIK",
                ".KIDIK",
                ".KIIK.",
                "..SS.."],
    "concern": ["......",
                ".KKKK.",
                "KIIHK.",
                ".KIIIK",
                ".KDIIK",
                "..KK..",
                "..SS.."],
    "surprised": [".KKKK.",
                  "KWWWWK",
                  "KWIIWK",
                  "KWIHWK",
                  "KWWWWK",
                  ".KKKK.",
                  "..SS.."],
    "warm": ["......",
             "......",
             "..KK..",
             ".K..K.",
             "K....K",
             "......",
             "......"],
}


def p_eye(cv, ex, ey, expr, side):
    sk = RAMP["skin"]
    pal = {"K": EYE, "I": IRIS, "H": WHITE, "W": WHITE, "D": (130, 84, 60), "S": sk[2], "L": EYE}
    rows = EYE_MAPS[expr]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x = ex + i if side < 0 else ex + (5 - i)
            cv.put(x, ey + j, pal[ch])
    if side > 0:
        # keep the catch-light on the upper-left in both eyes
        for j, row in enumerate(rows):
            if "H" in row and expr != "surprised":
                i = row.index("H")
                xr = ex + (5 - i)
                cv.put(xr, ey + j, IRIS)
                cv.put(xr - 1, ey + j, WHITE)
                break


def p_brows(cv, c, by, expr):
    hr = RAMP["hair"]
    shapes = {
        "neutral": [(0, 1), (-1, 0), (-2, 0), (-3, -1), (-4, -1), (-5, -1), (-6, 0), (-7, 0)],
        "warm": [(0, 0), (-1, -1), (-2, -1), (-3, -2), (-4, -2), (-5, -2), (-6, -1), (-7, 0)],
        "concern": [(0, -2), (-1, -2), (-2, -1), (-3, -1), (-4, 0), (-5, 0), (-6, 0), (-7, 1)],
        "surprised": [(0, -1), (-1, -2), (-2, -3), (-3, -3), (-4, -3), (-5, -3), (-6, -2), (-7, -1)],
    }[expr]
    for side in (-1, 1):
        ix = c - 4 if side < 0 else c + 4
        for i, (dx, dy) in enumerate(shapes):
            x = ix + dx if side < 0 else ix - dx
            if cv.own[by + dy, x] == cv.names["face"]:
                cv.put(x, by + dy, hr[0] if 0 < i < 6 else hr[1])
            if 0 < i < 6 and cv.own[by + dy + 1, x] == cv.names["face"]:
                cv.put(x, by + dy + 1, mix(hr[2], RAMP["skin"][2], 0.5))


def p_mouth(cv, c, my, expr, talk=False):
    if not talk:
        if expr == "neutral":           # the polished interview smile
            cv.hline(c - 4, c + 4, my, MOUTH)
            cv.hline(c - 3, c + 3, my, TEETH)
            cv.put(c - 5, my - 1, LIP_DK); cv.put(c + 5, my - 1, LIP_DK)
            cv.hline(c - 3, c + 3, my + 1, LIP)
            cv.hline(c - 2, c + 2, my - 1, LIP)
        elif expr == "warm":             # beaming
            cv.hline(c - 6, c + 6, my - 1, LIP_DK)
            cv.put(c - 7, my - 2, LIP_DK); cv.put(c + 7, my - 2, LIP_DK)
            cv.hline(c - 5, c + 5, my, TEETH); cv.put(c - 6, my, MOUTH); cv.put(c + 6, my, MOUTH)
            cv.hline(c - 5, c + 5, my + 1, MOUTH)
            cv.hline(c - 4, c + 4, my + 2, MOUTH); cv.hline(c - 2, c + 2, my + 2, TONGUE)
            cv.hline(c - 3, c + 3, my + 3, LIP)
        elif expr == "concern":          # the smile, slipping on one side
            cv.hline(c - 4, c + 3, my, MOUTH)
            cv.hline(c - 3, c + 1, my, TEETH)
            cv.put(c - 5, my - 1, LIP_DK); cv.put(c + 4, my + 1, LIP_DK)
            cv.hline(c - 3, c + 2, my + 1, LIP)
        elif expr == "surprised":
            cv.hline(c - 1, c + 1, my - 1, MOUTH)
            cv.hline(c - 2, c + 2, my, MOUTH); cv.hline(c - 2, c + 2, my + 1, MOUTH)
            cv.hline(c - 1, c + 1, my + 1, TONGUE)
            cv.hline(c - 1, c + 1, my + 2, MOUTH)
            cv.put(c - 3, my, LIP); cv.put(c + 3, my, LIP); cv.put(c - 3, my + 1, LIP); cv.put(c + 3, my + 1, LIP)
            cv.hline(c - 1, c + 1, my + 3, LIP)
        return
    # mouth open mid-word
    if expr == "neutral":
        cv.hline(c - 4, c + 4, my - 1, LIP)
        cv.hline(c - 3, c + 3, my, TEETH); cv.put(c - 4, my, MOUTH); cv.put(c + 4, my, MOUTH)
        cv.put(c - 5, my - 1, LIP_DK); cv.put(c + 5, my - 1, LIP_DK)
        cv.hline(c - 3, c + 3, my + 1, MOUTH); cv.hline(c - 1, c + 1, my + 1, TONGUE)
        cv.hline(c - 2, c + 2, my + 2, LIP)
    elif expr == "warm":
        cv.hline(c - 6, c + 6, my - 1, LIP_DK)
        cv.put(c - 7, my - 2, LIP_DK); cv.put(c + 7, my - 2, LIP_DK)
        cv.hline(c - 5, c + 5, my, TEETH); cv.put(c - 6, my, MOUTH); cv.put(c + 6, my, MOUTH)
        cv.hline(c - 5, c + 5, my + 1, MOUTH)
        cv.hline(c - 5, c + 5, my + 2, MOUTH); cv.hline(c - 3, c + 3, my + 2, TONGUE)
        cv.hline(c - 4, c + 4, my + 3, MOUTH); cv.hline(c - 2, c + 2, my + 3, TONGUE)
        cv.hline(c - 3, c + 3, my + 4, LIP)
    elif expr == "concern":
        cv.hline(c - 4, c + 3, my, MOUTH)
        cv.hline(c - 3, c + 1, my, TEETH)
        cv.put(c - 5, my - 1, LIP_DK); cv.put(c + 4, my + 1, LIP_DK)
        cv.hline(c - 3, c + 2, my + 1, MOUTH); cv.hline(c - 1, c, my + 1, TONGUE)
        cv.hline(c - 2, c + 1, my + 2, LIP)
    elif expr == "surprised":
        cv.hline(c - 1, c + 1, my - 2, MOUTH)
        cv.hline(c - 2, c + 2, my - 1, MOUTH)
        for yy in (my, my + 1, my + 2):
            cv.hline(c - 2, c + 2, yy, MOUTH)
        cv.hline(c - 1, c + 1, my + 2, TONGUE)
        cv.hline(c - 1, c + 1, my + 3, MOUTH)
        for yy in (my - 1, my, my + 1, my + 2):
            cv.put(c - 3, yy, LIP); cv.put(c + 3, yy, LIP)
        cv.hline(c - 1, c + 1, my + 4, LIP)


def portrait(expr, talk=False, blink=False):
    cv = Cv(PW, PH, open_bottom=True)
    c = 32
    sk, hr, su, bk = RAMP["skin"], RAMP["hair"], RAMP["suit"], RAMP["black"]
    # ---- hair (back of the bob) ----
    hb = cv.ell(c, 28, 21.6, 22) | cv.rect(c - 21.4, 28, c + 21.4, 51.4)
    hb &= ~cv.rect(c + 19.6, 49.6, 70, 70) & ~cv.rect(-6, 49.6, c - 19.6, 70)
    cv.part("hairback", hb, "hair", rad=14, soft=2.0, cuts=(0.30, 0.55, 0.86))
    # ---- shoulders: power suit ----
    neck = cv.rect(c - 5, 44, c + 5, 58)
    cv.part("neck", neck, "skin", lv=np.where(neck, 2, 0))
    for x in range(c - 5, c + 6):
        cv.put(x, 49, sk[1]); cv.put(x, 50, sk[1])
    sh = cv.poly([(c - 9, 52), (c + 9, 52), (c + 26, 54), (c + 33, 57), (c + 33, 64), (c - 33, 64), (c - 33, 57), (c - 26, 54)])
    cv.part("jacket", sh, "suit", rad=12, soft=2.0, cuts=(0.26, 0.48, 0.84))
    bl = cv.poly([(c - 6, 52), (c + 6, 52), (c + 1.5, 64), (c - 1.5, 64)])
    cv.part("blouse", bl, "blouse", rad=4, soft=1.0, bias=0.1, noedge=("neck",))
    gd = RAMP["gold"]
    cv.puts([(c - 3, 55), (c - 2, 56), (c - 1, 57), (c + 1, 57), (c + 2, 56), (c + 3, 55)], gd[3])
    cv.put(c, 58, gd[2]); cv.put(c, 59, gd[1])
    for s in (-1, 1):
        lap = cv.poly([(c + s * 6.5, 51.6), (c + s * 21, 55.6), (c + s * 17.4, 59.4), (c + s * 4.0, 64.5), (c + s * 2.0, 64.5)])
        cv.part("lapel%d" % s, lap, "suit", lv=np.where(lap, 3 if s < 0 else 2, 0), edge=su[0])
    gold_piping(cv, ["lapel-1", "lapel1"])
    brooch(cv, c - 13, 58)
    # ---- face ----
    face = cv.ell(c, 31.5, 14.6, 16.0) | cv.ell(c, 37.5, 12.4, 10.6)
    lv = np.where(face, 3, 0)
    lv = np.where(face & ~cv.ell(c - 1.2, 31.0, 13.6, 15.4) & ~cv.ell(c - 1.0, 37.0, 11.6, 10.2), 2, lv)
    lv = np.where(face & cv.ell(c - 6.5, 28.0, 4.4, 3.4), 4, lv)
    lv = np.where(face & (cv.Y >= 46), 2, lv)
    cv.part("face", face, "skin", lv=lv)
    for s in (-1, 1):                     # blush
        for y in (38, 39):
            for x in range(c + s * 10 - 2, c + s * 10 + 3):
                if cv.own[y, x] == cv.names["face"]:
                    cv.put(x, y, mix(cv.get(x, y), BLUSH, 0.45 if abs(x - c - s * 10) < 2 else 0.25))
    # nose
    cv.puts([(c - 1, 36), (c - 1, 37)], sk[4]); cv.puts([(c + 1, 38), (c, 39), (c + 1, 39)], sk[1])
    # ---- eyes / brows / mouth ----
    e = "warm" if expr == "warm" else expr
    ey = {"neutral": 29, "warm": 29, "concern": 29, "surprised": 28}[expr]
    for side in (-1, 1):
        ex = c - 11 if side < 0 else c + 6
        if blink and expr != "warm":
            cv.hline(ex + 1, ex + 4, ey + 4, EYE) if side < 0 else cv.hline(ex + 1, ex + 4, ey + 4, EYE)
            cv.put(ex if side < 0 else ex + 5, ey + 3, EYE)
        else:
            p_eye(cv, ex, ey, e, side)
    p_brows(cv, c, 25, expr)
    p_mouth(cv, c, 43, expr, talk)
    # ---- front hair: side-swept fringe + curtains ----
    part_x = c + 5
    X, Y = cv.X, cv.Y
    fbm = np.where(X < part_x, 20.5 + (part_x - X) * 0.26, 19.6 + (X - part_x) * 0.55)
    front = face & ((Y < fbm) | ((np.abs(X - c) > 11.8) & (Y > 16)))
    front |= cv.ell(c, 28, 21.6, 22) & ~face & (Y < 17)
    cv.part("fringe", front, "hair", noedge=("hairback",), rad=12, soft=1.8, cuts=(0.28, 0.52, 0.84))
    shine = (cv.ell(c - 3, 22, 15.6, 13.6) & ~cv.ell(c - 3, 23.4, 13.8, 12.0)) & (Y < 21) & (X < c + 8)
    shine &= (own(cv, "fringe") | own(cv, "hairback")) & ~is_ink(cv)
    for y, x in zip(*np.nonzero(shine)):
        cv.put(x, y, hr[4] if x < c - 4 else hr[3])
    cv.line(part_x, 7, part_x + 1, 13, hr[0])
    for (a, b, c2, d) in [(c - 17, 30, c - 18, 46), (c + 17, 30, c + 18, 46), (c - 14, 22, c - 16, 30), (c + 9, 20, c + 13, 27)]:
        cv.line(a, b, c2, d, hr[1])
    # ---- headset ----
    band = (cv.ell(c, 28, 20.0, 20.4) & ~cv.ell(c, 28, 18.8, 19.2)) & (Y < 26) & (X > c - 19)
    for y, x in zip(*np.nonzero(band)):
        cv.put(x, y, bk[3] if x < c - 6 else bk[2])
    pad = cv.ell(c + 20, 34, 3.2, 4.6)
    cv.part("earpad", pad, "black", edge="ink", rad=3, bias=0.1)
    cv.put(c + 19, 31, bk[4])
    boom = [(c + 19, 38), (c + 18, 39), (c + 17, 40), (c + 16, 41), (c + 15, 42), (c + 14, 43)]
    for x, y in boom:
        cv.put(x, y, bk[2]); cv.put(x, y + 1, bk[1])
    mic = cv.ell(c + 12, 44.0, 2.0, 1.6)
    cv.part("mic", mic, "black", edge="ink", lv=np.where(mic, 2, 0))
    cv.put(c + 11, 43, bk[4])
    cv.put(c + 21, 32, LED); cv.put(c + 21, 33, mix(LED, bk[2], 0.4))
    cv.outline()
    cv.put(c + 22, 31, LED_HI) if False else None
    if expr == "warm":
        cv.puts([(56, 12), (57, 11), (58, 10), (57, 15), (59, 15), (60, 15)], SPARK2)
    if expr == "surprised":
        cv.puts([(55, 6), (55, 7), (55, 8), (55, 10), (58, 8), (59, 7), (60, 6)], SPARK2)
    if expr == "concern":
        sweat(cv, 12, 18)
    return cv


if __name__ == "__main__" and "--try3" in sys.argv:
    ex = ("neutral", "warm", "concern", "surprised")
    preview([portrait(e) for e in ex] + [portrait(e, talk=True) for e in ex], "ports.png", 6)


# ==========================================================================
# ENTRANCE (intro card): rising on the Macky stage lift through dry ice
# ==========================================================================
EW, EH = 128, 120


def fog_puffs(cv, puffs, name):
    m = cv.empty()
    for (x, y, rx, ry) in puffs:
        m |= cv.ell(x, y, rx, ry)
    m &= cv.half(y=cv.h - 1, below=False)
    cv.part(name, m, "fog", edge=RAMP["fog"][1], rad=6, soft=1.2, cuts=(0.18, 0.42, 0.74), light=(-0.3, -0.9, 0.5))
    return m


def entrance():
    cv = Cv(EW, EH)
    g = G(cv, EW // 2, 16, 1.0)
    c = g.c
    feet = g.t + 83
    lf = RAMP["lift"]
    # back fog (behind the lift)
    fog_puffs(cv, [(c - 38, feet - 2, 10, 6), (c + 39, feet - 3, 11, 6.5), (c - 52, feet + 4, 9, 6), (c + 53, feet + 3, 9, 6),
                   (c - 27, feet - 1, 6, 4), (c + 28, feet - 1, 6, 4)], "fogB")
    # lift column + platform
    col = cv.rect(c - 11, feet + 6, c + 11, EH)
    cv.part("column", col, "lift", rad=6, light=(-0.9, 0.0, 0.4), cuts=(0.3, 0.55, 0.85))
    for y in range(feet + 8, EH, 3):
        cv.hline(c - 10, c + 10, y, lf[1])
    top = cv.ell(c, feet + 1.5, 30, 3.5)
    face_ = cv.rect(c - 30, feet + 1.5, c + 30, feet + 7) & (cv.ell(c, feet + 5.5, 30.4, 3.6) | cv.rect(c - 30, feet, c + 30, feet + 5.5))
    cv.part("platform", face_, "lift", lv=np.where(face_, 1, 0))
    cv.part("deck", top, "lift", lv=np.where(top, 3, 0) + np.where(top & (cv.X < c - 12), 1, 0))
    gd = RAMP["gold"]
    for x in range(c - 28, c + 29):          # hazard stripe + footlights on the front face
        y = feet + 4
        if cv.own[y, x] == cv.names["platform"]:
            cv.put(x, y, gd[3] if ((x - c) // 2) % 2 == 0 else lf[0])
    for x in range(c - 24, c + 25, 8):
        cv.put(x, feet + 6, SPARK); cv.put(x, feet + 5, SPARK2) if cv.own[feet + 5, x] == cv.names["platform"] else None
    # Val, arms flung up: the tablet held high like a trophy
    hair_back(g)
    legs_front(g)
    neck_front(g)
    jacket_front(g)
    brooch(cv, round(g.x(-6.6)), round(g.y(34.4)))
    arm(g, "armL", [(-14.4, 31.2), (-22.0, 25.0), (-27.0, 16.0)])
    palm(g, "handL", -27.6, 11.6, tilt=-0.25, thumb=1)
    arm(g, "armR", [(14.4, 31.2), (21.0, 22.0), (22.6, 12.0)])
    tw, th = 11, 14
    x0, y0 = round(g.x(17.4)), round(g.y(-6.2))
    tablet(cv, x0, y0, SCREEN_BIG, flare=True)
    hand(g, "handR", 22.6, 8.8, 2.5, 2.6)
    head_front(g, "tell", True)
    # front fog rolling over the platform edge and her shoes
    fog_puffs(cv, [(c - 34, feet + 7, 9, 5), (c - 46, feet + 11, 10, 6), (c + 35, feet + 7, 9, 5), (c + 48, feet + 11, 10, 6),
                   (c - 22, feet + 15, 12, 6), (c + 22, feet + 15, 12, 6), (c, feet + 19, 17, 5.5),
                   (c - 59, feet + 17, 7, 6), (c + 59, feet + 17, 7, 6), (c - 14, feet + 1.5, 4.6, 2.4), (c + 13, feet + 1.0, 5.2, 2.6),
                   (c - 4, feet + 2.6, 3.4, 1.8)], "fogF")
    cv.outline()
    # dry ice keeps a soft lavender edge instead of the ink line
    fogm = own(cv, "fogF") | own(cv, "fogB")
    cv.col[fogm & is_ink(cv)] = RAMP["fog"][0]
    # light rays fanning from the tablet
    for ang in (-2.6, -2.1, -1.35, -0.75, -0.3):
        for r in range(11, 18):
            px, py = x0 + tw / 2 + math.cos(ang) * r, y0 + th / 2 + math.sin(ang) * r
            if 0 <= px < EW and 0 <= py < EH and not cv.alpha[int(py), int(px)]:
                cv.put(px, py, SPARK if r < 14 else SPARK2)
    # sparkles after the outline so they stay crisp
    sparkle(cv, x0 + tw + 2, y0 - 1)
    sparkle(cv, x0 - 4, y0 + 3, False)
    sparkle(cv, round(g.x(-33)), round(g.y(6)), False)
    sparkle(cv, round(g.x(28)), round(g.y(28)), False)
    sparkle(cv, round(g.x(-24)), round(g.y(-2)))
    return cv


# ==========================================================================
# SCREENS prop (optional battle layer): the wall of candidate screens
# ==========================================================================
def screens():
    cols, rows, mw, mh, gap = 6, 3, 30, 22, 3
    W = cols * mw + (cols - 1) * gap + 4
    H = rows * mh + (rows - 1) * gap + 10
    cv = Cv(W, H)
    sc, bk, sk, hr = RAMP["screen"], RAMP["black"], RAMP["skin"], RAMP["hair"]
    rng = np.random.default_rng(7)
    hairs = [hr[1], (40, 30, 30), (200, 150, 70), (90, 60, 40), (30, 30, 40), (150, 80, 50)]
    skins = [sk[3], (196, 140, 100), (140, 90, 60), (236, 190, 150), (110, 70, 50), (220, 160, 120)]
    for j in range(rows):
        for i in range(cols):
            x0 = 2 + i * (mw + gap)
            y0 = 2 + j * (mh + gap)
            m = cv.rect(x0, y0, x0 + mw - 1, y0 + mh - 1)
            cv.part("mon%d_%d" % (i, j), m, "black", edge="ink", lv=np.where(m, 1, 0))
            k = (i * 5 + j * 3) % 6
            for y in range(y0 + 2, y0 + mh - 2):
                for x in range(x0 + 2, x0 + mw - 2):
                    cv.put(x, y, sc[1] if (y - y0) > 3 else sc[2])
            cv.hline(x0 + 2, x0 + mw - 3, y0 + 2, sc[3])
            # candidate: head + shoulders silhouette
            hx, hy = x0 + 9, y0 + 9
            for y in range(hy - 4, hy + 4):
                for x in range(hx - 4, hx + 5):
                    if (x - hx) ** 2 / 14.0 + (y - hy) ** 2 / 12.0 <= 1:
                        cv.put(x, y, skins[k])
            for y in range(hy - 5, hy + 3):
                for x in range(hx - 5, hx + 6):
                    inside = (x - hx) ** 2 / 16.0 + (y - hy + 0.5) ** 2 / 16.0 <= 1
                    if inside and (y < hy - 1 or (abs(x - hx) >= 4 and y < hy + 2 + (k % 2))):
                        cv.put(x, y, hairs[k])
            cv.put(hx - 2, hy + 1, EYE); cv.put(hx + 2, hy + 1, EYE)
            for y in range(hy + 4, y0 + mh - 2):
                for x in range(hx - 6, hx + 7):
                    if abs(x - hx) <= 3 + (y - hy - 4):
                        cv.put(x, y, sc[0])
            # name + stat lines
            cv.hline(x0 + 17, x0 + 26, y0 + 6, sc[3])
            cv.hline(x0 + 17, x0 + 23, y0 + 9, sc[3])
            cv.hline(x0 + 17, x0 + 25, y0 + 12, sc[2])
            stars = int(rng.integers(1, 6))
            for s in range(5):
                cv.put(x0 + 17 + s * 2, y0 + 16, RAMP["gold"][3] if s < stars else sc[0])
            verdict = (i + j * 2) % 4
            if verdict == 0:
                cv.puts([(x0 + 24, y0 + 17), (x0 + 25, y0 + 18), (x0 + 26, y0 + 17), (x0 + 27, y0 + 16)], CHECK)
            elif verdict == 2:
                cv.puts([(x0 + 24, y0 + 16), (x0 + 26, y0 + 18), (x0 + 25, y0 + 17), (x0 + 24, y0 + 18), (x0 + 26, y0 + 16)], GLITCH)
            cv.put(x0 + 1, y0 + 1, bk[3])
    # mounting bar
    bar = cv.rect(2, H - 6, W - 3, H - 3)
    cv.part("bar", bar, "lift", lv=np.where(bar, 2, 0))
    cv.outline()
    return cv


if __name__ == "__main__" and "--try4" in sys.argv:
    preview([entrance()], "entrance.png", 6)
    preview([screens()], "screens.png", 5)


# ==========================================================================
# output
# ==========================================================================
def foot_point(cv):
    """x = centre between the shoes on the sole row, y = sole row (Eric's rule)."""
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


def changed_box(a, b):
    d = np.any(np.array(a) != np.array(b), axis=2)
    ys, xs = np.nonzero(d)
    return None if not len(ys) else (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def build():
    cells_dir = os.path.join(OUT, "cells")
    for d in (cells_dir, os.path.join(OUT, "talk"), os.path.join(OUT, "idle")):
        os.makedirs(d, exist_ok=True)
    feet, imgs = {}, {}
    battle = [front("idle"), front("talk"), front("tell"), front("hit"), side(), back()]
    world = [front("idle", True), front("talk", True), front("tell", True), front("hit", True), side(True), back(True)]
    for prefix, group, hgt in (("battle", battle, 84), ("world", world, 54)):
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            check_height(img, hgt, name)
            img.save(os.path.join(cells_dir, name))
            feet[name] = foot_point(cv)
            imgs[name] = img
    ent = entrance()
    img = ent.image()
    img.save(os.path.join(cells_dir, "entrance.png"))
    rows = np.nonzero(np.array(img)[..., 3].any(axis=1))[0]
    feet["entrance.png"] = [EW // 2, EH - 1]
    feet["entrance-height"] = int(EH - rows[0])
    imgs["entrance.png"] = img
    scr = screens().image()
    scr.save(os.path.join(cells_dir, "screens.png"))
    imgs["screens.png"] = scr
    for i, e in enumerate(("neutral", "warm", "concern", "surprised")):
        p = portrait(e).image()
        t = portrait(e, talk=True).image()
        p.save(os.path.join(cells_dir, "portrait-%d.png" % i))
        t.save(os.path.join(OUT, "talk", "val-%d.png" % i))
        imgs["portrait-%d.png" % i] = p
        imgs["talk-%d.png" % i] = t
        print("talk", i, "changed box", changed_box(p, t))
    # idle extras for the world front cell: same canvas, same foot
    base = imgs["world-0.png"]
    for name, pose in (("blink", "blink"), ("pose1", "phone"), ("pose2", "call")):
        cv = front(pose, True)
        im = cv.image()
        assert im.size == base.size and foot_point(cv) == feet["world-0.png"], name
        hip = round((WH - 54) + 60 * WK)
        assert np.array_equal(np.array(im)[hip:], np.array(base)[hip:]), (name, "lower body changed")
        im.save(os.path.join(OUT, "idle", "val-%s.png" % name))
        imgs["idle-" + name] = im
        print("idle", name, "changed box", changed_box(base, im))
    with open(os.path.join(cells_dir, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    contact_sheet(imgs, feet)
    previews(imgs)
    return imgs, feet


def _ref_crops():
    """Cut the existing cast out of the shared cast reference (already 3x)."""
    if not os.path.exists(CAST_REF):
        return [], [], []
    im = Image.open(CAST_REF).convert("RGBA")
    a = np.array(im)
    bg = a[5, 5, :3].astype(int)

    def cut(x0, x1, y0, y1, label):
        sub = a[y0:y1, x0:x1].copy()
        mask = np.abs(sub[..., :3].astype(int) - bg).sum(2) <= 3
        sub[mask, 3] = 0
        out = Image.fromarray(sub, "RGBA")
        bb = out.getbbox()
        out = out.crop((bb[0], bb[1] if y1 not in (284, 496) else bb[1], bb[2], (y1 - y0) if y1 in (284, 496) else bb[3]))
        return out, label

    r1 = [cut(33, 207, 20, 284, "eric 80"), cut(1476, 1617, 20, 284, "dev 80"), cut(1695, 1809, 20, 284, "jakerson 80")]
    r2 = [cut(27, 132, 300, 496, "eric world"), cut(1011, 1104, 300, 496, "jules"), cut(1245, 1326, 300, 496, "imani"), cut(1416, 1509, 300, 496, "dev")]
    r3 = [cut(834, 993, 514, 710, "dev"), cut(1035, 1224, 514, 710, "jakerson")]
    return r1, r2, r3


def contact_sheet(imgs, feet, S=3):
    from PIL import ImageFont
    BG = (44, 44, 62, 255)
    GROUND = (70, 70, 96, 255)
    font = ImageFont.load_default()
    up = lambda im: im.resize((im.width * S, im.height * S), Image.NEAREST)
    ref1, ref2, ref3 = _ref_crops()
    r1 = [(up(imgs["battle-%d.png" % i]), "battle-%d" % i) for i in range(6)] + [(up(imgs["entrance.png"]), "entrance (cell 12)")]
    r1 += [(im, "ref " + l) for im, l in ref1]
    r2 = [(up(imgs["world-%d.png" % i]), "world-%d" % i) for i in range(6)]
    r2 += [(up(imgs["idle-" + n]), "idle " + n) for n in ("blink", "pose1", "pose2")]
    r2 += [(im, "ref " + l) for im, l in ref2]
    r3 = [(up(imgs["portrait-%d.png" % i]), "portrait-%d" % i) for i in range(4)]
    r3 += [(up(imgs["talk-%d.png" % i]), "talk-%d" % i) for i in range(4)]
    r3 += [(im, "ref " + l) for im, l in ref3]
    r4 = [(up(imgs["screens.png"]), "screens prop (optional battle layer)")]
    rows = [r1, r2, r3, r4]
    pad = 12
    widths = [sum(im.width + pad for im, _ in r) + pad for r in rows]
    heights = [max(im.height for im, _ in r) + 26 for r in rows]
    W, H = max(widths), sum(heights) + pad * 2
    sheet = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    y = pad
    for ri, (r, rh) in enumerate(zip(rows, heights)):
        x = pad
        base = y + rh - 18
        grounded = ri < 2
        if grounded:
            d.rectangle([0, base, W, base + 1], fill=GROUND)
        for im, label in r:
            top = base - im.height if grounded else y
            sheet.alpha_composite(im, (x, top))
            d.text((x, base + 4), label, fill=(200, 200, 220, 255), font=font)
            x += im.width + pad
        y += rh
    sheet.save(os.path.join(HERE, "sheet.png"))


def previews(imgs, S=8):
    """8x previews of every cell, for review."""
    os.makedirs(PREV, exist_ok=True)
    for k, im in imgs.items():
        im.resize((im.width * S, im.height * S), Image.NEAREST).save(os.path.join(PREV, "x8-" + k.replace(".png", "") + ".png"))


if __name__ == "__main__" and not any(a.startswith("--try") for a in sys.argv):
    imgs, feet = build()
    for k, v in feet.items():
        print(k, imgs[k].size if k in imgs else "", v)
