#!/usr/bin/env python3
"""Chad, Networking Legend -- procedural pixel-art sprites for "After Hours - College Tale".

Drawn the way Professor Eric is drawn (tools/eric_art/draw_eric.py): parts are masks shaded with
material ramps from a top-left key light, given inner 1px lines and an ink silhouette.  Everything
is drawn at its final pixel size; nothing drawn is ever resampled (only the contact sheet and the
private 8x previews are nearest-neighbour blow-ups).

Look: teal quarter-zip fleece vest over a crisp light-blue oxford, navy slim chinos cropped over
bare ankles and cognac loafers, a golden hair swoop, a spray tan, perfect teeth and AirPods.  His
signature props are a handheld ring light with his phone clipped in the middle (always "live") and
a hand of glowing LED business cards.

Outputs (in ./out next to this script):
  battle-0..5.png   82px tall battle cells   (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  entrance.png      cell 12, the intro-card pose (wider canvas)
  world-0..5.png    52px tall overworld cells (same poses, redrawn small)
  portrait-0..3.png 64x64 portraits          (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk/chad-0..3.png    mouth-open portraits
  idle/chad-blink.png, chad-pose1.png, chad-pose2.png   world-front idle extras
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
    "skin":   [(92, 42, 30), (166, 92, 58), (212, 134, 88), (236, 170, 120), (250, 204, 160)],
    "hair":   [(78, 46, 22), (146, 96, 40), (196, 142, 58), (230, 188, 96), (250, 226, 150)],
    "vest":   [(8, 44, 54), (16, 92, 104), (26, 136, 144), (58, 182, 178), (134, 224, 212)],
    "shirt":  [(54, 70, 112), (122, 152, 200), (168, 196, 232), (204, 224, 248), (238, 246, 255)],
    "pants":  [(16, 18, 38), (34, 40, 72), (52, 60, 102), (74, 86, 134), (102, 116, 164)],
    "shoe":   [(46, 20, 12), (100, 48, 24), (146, 78, 38), (188, 114, 60), (222, 156, 94)],
    "metal":  [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "house":  [(20, 20, 30), (44, 46, 60), (70, 74, 92), (104, 108, 128), (150, 154, 172)],
    "card":   [(12, 12, 20), (26, 28, 42), (40, 44, 62), (58, 62, 84), (84, 88, 112)],
    "gold":   [(92, 58, 14), (170, 120, 30), (222, 172, 54), (246, 212, 100), (255, 240, 170)],
}
EYE = (30, 22, 30)
IRIS = (52, 86, 120)        # blue-grey eyes
WHITE = (250, 248, 244)
SCLERA = (240, 236, 230)
MOUTH = (84, 30, 34)
LIP = (186, 98, 82)
TONGUE = (196, 92, 96)
TEETH = (252, 252, 248)
TEETH2 = (214, 216, 220)
BLUSH = (222, 120, 94)
BROW = (110, 66, 30)
POD = (250, 250, 252)       # AirPods
POD2 = (196, 200, 210)
LED = (250, 252, 255)       # ring light LEDs
LED2 = (206, 236, 255)
LED3 = (150, 206, 240)
SCREEN = (70, 140, 220)
SCREEN2 = (130, 196, 250)
REC = (240, 60, 70)
CARD_GLOW = [(70, 236, 255), (255, 90, 200), (150, 255, 110), (255, 214, 80)]
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
def pmap(cv, x0, y0, rows, pal, mirror=False):
    """Paint a little character map; '.' is skipped.  mirror flips it left-right about x0."""
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == "." or ch == " ":
                continue
            x = x0 - i if mirror else x0 + i
            cv.put(x, y0 + j, pal[ch])


def ring_light(cv, cx, cy, R=9.0, squash=1.0, ang=0.0, name="ring", phone=True, back=False, band=3.0):
    """A handheld ring light seen from the front: dark housing, a bright LED band, the phone clipped
    in the middle on a cross bar.  squash < 1 turns it away (ellipse), back=True shows the housing."""
    ry = R * squash
    outer = cv.ell(cx, cy, R, ry, ang)
    inner = cv.ell(cx, cy, R - band - 1.2, max(0.6, (R - band - 1.2) * squash), ang)
    ringm = outer & ~inner
    cv.part(name, ringm, "house", edge="ink", rad=2, soft=0.6, cuts=(0.3, 0.55, 0.85))
    if not back:
        led = cv.ell(cx, cy, R - 1.0, max(0.6, (R - 1.0) * squash), ang) & ~cv.ell(cx, cy, R - band, max(0.5, (R - band) * squash), ang)
        led &= ringm
        ys, xs = np.nonzero(led)
        for y, x in zip(ys, xs):
            # top-left of the band burns white, the far side cools to pale blue
            u = ((x - cx) + (y - cy)) / (R * 1.4)
            cv.put(x, y, LED if u < 0.15 else LED2 if u < 0.75 else LED3)
    else:
        ys, xs = np.nonzero(ringm)
        for y, x in zip(ys, xs):
            if (x + y) % 5 == 0 and cv.get(x, y) != INK:
                cv.put(x, y, RAMP["house"][1])
    if phone:
        # cross bar + phone holder
        hw = max(1, int(round((R - band - 1) * 0.95)))
        for x in range(int(round(cx - hw)), int(round(cx + hw)) + 1):
            if inner[int(round(cy)), x]:
                cv.put(x, int(round(cy)), RAMP["metal"][1])
        px, py = int(round(cx)), int(round(cy))
        if R >= 8:
            m = cv.rect(px - 2, py - 3, px + 2, py + 3)
            cv.part(name + "phone", m, "house", edge="ink", lv=np.where(m, 1, 0))
            if not back:
                for y in range(py - 2, py + 3):
                    for x in range(px - 1, px + 2):
                        cv.put(x, y, SCREEN2 if (x - px + y - py) < -1 else SCREEN)
                cv.put(px + 1, py - 2, REC)
            else:
                cv.put(px - 1, py - 2, RAMP["house"][3])
        else:
            cv.put(px, py, (34, 34, 44)); cv.put(px, py - 1, SCREEN if not back else (34, 34, 44))
    return ringm


def handle(cv, x0, y0, x1, y1, r=1.3, name="handle"):
    m = cv.capsule(x0, y0, x1, y1, r)
    cv.part(name, m, "house", edge="ink", rad=1.5, soft=0.5, light=(-0.75, -0.45, 0.55))
    return m


def card(cv, px, py, ang, L=8.0, W=5.0, glow=0, name="card"):
    """One LED business card, pivot (px, py) at its bottom edge centre, rotated by ang (radians,
    0 = upright).  Matte black card whose LED trim glows just inside the ink edge, with a bright
    name line and a logo dot on the face."""
    ux, uy = math.sin(ang), -math.cos(ang)          # up the card
    vx, vy = math.cos(ang), math.sin(ang)           # across the card
    hw = W / 2.0
    pts = [(px - vx * hw, py - vy * hw), (px + vx * hw, py + vy * hw),
           (px + vx * hw + ux * L, py + vy * hw + uy * L), (px - vx * hw + ux * L, py - vy * hw + uy * L)]
    m = cv.poly(pts)
    cv.part(name, m, "card", edge="ink", lv=np.where(m, 1, 0))
    g = CARD_GLOW[glow % len(CARD_GLOW)]
    gd = mix(g, RAMP["card"][1], 0.45)
    inner = ndi.binary_erosion(m)
    trim = inner & ~ndi.binary_erosion(inner)
    ys, xs = np.nonzero(trim)
    for y, x in zip(ys, xs):
        # brighter on the top edge of the card, dimmer down the sides
        d = (x - px) * ux + (y - py) * uy
        cv.put(x, y, g if d > L * 0.55 else gd)
    if L >= 9:
        lx, ly = px + ux * (L * 0.45), py + uy * (L * 0.45)
        cv.put(int(round(lx - vx)), int(round(ly - vy)), WHITE)
        cv.put(int(round(lx + vx)), int(round(ly + vy)), mix(g, WHITE, 0.5))
    else:
        lx, ly = px + ux * (L * 0.45), py + uy * (L * 0.45)
        if inner[int(round(ly)), int(round(lx))]:
            cv.put(int(round(lx)), int(round(ly)), WHITE)
    return m


def fan(cv, px, py, base=0.0, spread=0.32, n=4, L=10.0, W=7.0, name="fan"):
    """A hand of n cards fanned about a pivot in the fingers."""
    for i in range(n):
        a = base + (i - (n - 1) / 2) * spread
        card(cv, px, py, a, L, W, glow=i, name="%s%d" % (name, i))


def sparkle(cv, x, y, big=True):
    pts = [(x, y - 2), (x, y - 1), (x, y + 1), (x, y + 2), (x - 2, y), (x - 1, y), (x + 1, y), (x + 2, y)]
    if not big:
        pts = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
    cv.puts(pts, SPARK2)
    cv.put(x, y, WHITE)


def head_pal():
    sk, hr = RAMP["skin"], RAMP["hair"]
    return {"K": INK, "0": hr[0], "1": hr[1], "2": hr[2], "3": hr[3], "4": hr[4], "s": sk[2], "l": sk[3], "h": sk[4],
            "d": sk[1], "x": sk[0], "E": EYE, "W": SCLERA, "w": WHITE, "I": IRIS, "B": BROW, "T": TEETH, "t": TEETH2,
            "M": MOUTH, "L": LIP, "P": POD, "p": POD2, "r": BLUSH, "o": TONGUE}


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


SIDE_HEAD = [
 "..........KKKKK........",  # -2
 "........KK444443KK.....",  # -1
 "......KK44444443333K...",  # 0
 ".....K33444443333222K..",  # 1
 "....K2333333333322222K.",  # 2
 "...K2222333322211112K..",  # 3
 "..K12222222221KKKK12K..",  # 4
 "..K1122222221dsssssK...",  # 5
 ".K11122222221dsssssK...",  # 6
 ".K111122221ddlsssssK...",  # 7
 ".K11111221dslllssssK...",  # 8
 ".K1111111ddsllllBBBBK..",  # 9
 ".K1111KKKdsllllWWEsK...",  # 10
 ".K111KlsddssllllWEEsK..",  # 11
 ".K111KlsPPdssssssdssssK",  # 12
 ".K111KsdsPdsssssssslsdK",  # 13
 "..K11KsddPdsssssrssddK.",  # 14
 "..K111KKdpdssssssssdK..",  # 15
 "...K1KKddsssssssMTTTK..",  # 16
 "...KKKddssssssssdMMMK..",  # 17
 ".....KddssssssssssLK...",  # 18
 ".....KdddssssssssslK...",  # 19
 "......KdddddsssssslK...",  # 20
 ".......KKddddddddKK....",  # 21
]


def check_height(img, want, name):
    a = np.array(img)[..., 3] > 0
    assert a[-1].any(), (name, "feet not on bottom row")


# ==========================================================================
# BATTLE  (82 px standing height)
# ==========================================================================
BW, BH = 92, 96
HB = 84
BT = BH - 82          # body reference row; the swoop crest rises 2px above it (height 84)


def b_hand(cv, x, y, name, rx=2.6, ry=3.0):
    m = cv.ell(x, y, rx, ry)
    cv.part(name, m, "skin", edge="ink", rad=2.5, soft=0.7, bias=0.05)
    return m


def b_arm(cv, name, pts, r0=3.3, r1=2.8, cuff=True):
    """Oxford sleeve: a tapered chain, crisp crease highlights, a white cuff at the wrist."""
    m = cv.empty()
    n = len(pts) - 1
    for k, ((a, b), (c_, d)) in enumerate(zip(pts, pts[1:])):
        ra = r0 + (r1 - r0) * k / n
        rb = r0 + (r1 - r0) * (k + 1) / n
        m |= cv.capsule(a, b, c_, d, ra, rb)
    cv.part(name, m, "shirt", edge="dark", rad=3, soft=0.9, cuts=(0.28, 0.52, 0.86))
    if cuff:
        (xa, ya), (xb, yb) = pts[-2], pts[-1]
        L = math.hypot(xb - xa, yb - ya) or 1
        ux, uy = (xb - xa) / L, (yb - ya) / L
        cm = m & cv.capsule(xb - ux * 1.6, yb - uy * 1.6, xb, yb, r1 + 0.6)
        sh = RAMP["shirt"]
        ys, xs = np.nonzero(cm)
        for y, x in zip(ys, xs):
            if cv.get(x, y) != sh[0]:
                cv.put(x, y, sh[4] if (x - xb) * -1 + (y - yb) * -1 > -0.5 else sh[3])
    return m


def b_legs(cv, c, t, back=False, spread=0.0):
    """Slim chinos cropped over bare ankles, cognac penny loafers.  spread pushes the feet apart
    (a power stance) by that many pixels at the ankle."""
    pr = RAMP["pants"]
    D = lambda s_, y: s_ * spread * max(0.0, (y - t - 49)) / 28.0
    for s in (-1, 1):
        pts = [(s * 0.5, 49), (s * 11, 49), (s * 11, 56), (s * 9.5, 67), (s * 9, 76), (s * 3, 76), (s * 2, 67), (s * 0.5, 57)]
        leg = cv.poly([(c + x + D(s, t + y), t + y) for x, y in pts])
        cv.part("leg%d" % s, leg, "pants", rad=4, soft=1.0, cuts=(0.30, 0.56, 0.9), tex=0.03, seed=9 + s)
    # crotch + inseam + crease
    cv.vline(c, t + 54, t + 57, pr[0])
    for s in (-1, 1):
        cv.line(c + s * 6 + D(s, t + 58), t + 58, c + s * 6 + D(s, t + 74), t + 74, pr[1] if s < 0 else pr[0])
        if s < 0:
            cv.put(c - 7 + D(s, t + 60), t + 60, pr[3])
        o = D(s, t + 75)
        cv.hline(c + 3 + o if s > 0 else c - 9 + o, c + 9 + o if s > 0 else c - 3 + o, t + 75, pr[1])
    for s in (-1, 1):                          # slant pockets
        cv.line(c + s * 7, t + 50, c + s * 10, t + 55, pr[1])
    # bare ankles (no-show socks) + loafers
    sr = RAMP["shoe"]
    for s in (-1, 1):
        o = int(round(s * spread))
        ax = c + s * 6 + o
        ank = cv.rect(ax - 2, t + 77, ax + 2, t + 78)
        cv.part("ankle%d" % s, ank, "skin", edge="dark", lv=np.where(ank, 2, 0) + np.where(ank & (cv.X < ax), 1, 0))
        sx = c + s * 6.6 + o
        sh = cv.ell(sx, t + 80.2, 5.6, 2.6) & cv.half(y=t + 81, below=False) & cv.half(y=t + 77.6)
        cv.part("shoe%d" % s, sh, "shoe", rad=2.5, soft=0.7, cuts=(0.30, 0.55, 0.85))
        if not back:
            cv.hline(sx - 2, sx + 2, t + 79, sr[1])              # vamp strap
            cv.put(sx - 1, t + 79, RAMP["gold"][3])             # penny-bit glint
            cv.put(sx - 3, t + 79, sr[4])
        else:
            cv.hline(sx - 2, sx + 2, t + 79, sr[1])
        cv.hline(sx - 4, sx + 4, t + 81, sr[0])                 # sole


def b_torso(cv, c, t, back=False, logo=True):
    sh, vs = RAMP["shirt"], RAMP["vest"]
    # shirt underneath: shoulders show past the vest's armholes
    shirt = cv.poly([(c - 11, t + 22), (c + 11, t + 22), (c + 14, t + 26), (c + 13, t + 36), (c + 11, t + 50),
                     (c - 11, t + 50), (c - 13, t + 36), (c - 14, t + 26)])
    shirt |= cv.ell(c - 11.5, t + 26.5, 3.6, 3.4) | cv.ell(c + 11.5, t + 26.5, 3.6, 3.4)
    cv.part("shirt", shirt, "shirt", rad=6, soft=1.2, cuts=(0.28, 0.52, 0.86))
    vest = cv.poly([(c - 8, t + 22), (c + 8, t + 22), (c + 10, t + 26), (c + 9.5, t + 31), (c + 11, t + 37),
                    (c + 12, t + 51), (c - 12, t + 51), (c - 11, t + 37), (c - 9.5, t + 31), (c - 10, t + 26)])
    cv.part("vest", vest, "vest", noedge=(), rad=8, soft=1.6, cuts=(0.26, 0.50, 0.84), tex=0.05, seed=5)
    # hem band
    hem = vest & cv.half(y=t + 49)
    cv.part("hem", hem, "vest", noedge=("vest",), lv=np.where(hem, 1, 0) + np.where(hem & (cv.X < c - 3), 1, 0))
    # side panel seams
    for s in (-1, 1):
        cv.line(c + s * 9, t + 33, c + s * 10, t + 48, vs[1])
    if back:
        for x in range(c - 9, c + 10):          # yoke
            y = t + 28 + abs(x - c) // 5
            if cv.own[y, x] == cv.names["vest"]:
                cv.put(x, y, vs[1])
        return
    # mock-neck collar opened by the quarter zip; shirt collar points inside
    colm = cv.poly([(c - 6, t + 19), (c - 1, t + 21), (c - 1, t + 26), (c - 7, t + 24)]) | \
        cv.poly([(c + 6, t + 19), (c + 1, t + 21), (c + 1, t + 26), (c + 7, t + 24)])
    cv.part("collar", colm, "vest", rad=2, soft=0.6, bias=0.12)
    pts = cv.poly([(c - 1, t + 21), (c - 4, t + 21), (c - 1, t + 25)]) | cv.poly([(c + 1, t + 21), (c + 4, t + 21), (c + 1, t + 25)])
    cv.part("shirtcol", pts, "shirt", edge="dark", lv=np.where(pts, 4, 0))
    cv.vline(c, t + 21, t + 26, sh[1])
    # zip line down to mid chest + pull
    mt = RAMP["metal"]
    for y in range(t + 26, t + 33):
        cv.put(c, y, vs[0] if y % 2 else mt[1])
    cv.puts([(c, t + 33), (c, t + 34)], mt[3]); cv.put(c + 1, t + 34, mt[2])
    # chest logo patch (his left = viewer right)
    if logo:
        cv.hline(c + 4, c + 7, t + 28, (236, 236, 228)); cv.hline(c + 4, c + 7, t + 29, (190, 200, 196))
        cv.put(c + 5, t + 28, (240, 120, 70))
    # light on the vest's left chest, fold under the arm
    for x in range(c - 8, c - 4):
        cv.put(x, t + 27 + (c - 6 - x) // 2, vs[3])


def b_head_front(cv, c, t, pose, tilt=0):
    """Frontal head; t is the top of the swoop."""
    sk, hr = RAMP["skin"], RAMP["hair"]
    # ears + AirPods
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 7.4, t + 13, 1.7, 2.4), "skin", bias=0.05)
    nk = cv.rect(c - 3, t + 17, c + 3, t + 23)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 2, 0) - np.where(nk & (cv.Y <= t + 21), 1, 0))
    face = cv.ell(c, t + 12, 6.9, 7.9) | cv.poly([(c - 6.6, t + 13), (c + 6.6, t + 13), (c + 5.5, t + 18),
                                                   (c + 2.5, t + 21), (c - 2.5, t + 21), (c - 5.5, t + 18)])
    cv.part("face", face, "skin", rad=6, soft=1.4, cuts=(0.30, 0.52, 0.86))
    cv.put(c + 5, t + 17, sk[1]); cv.put(c + 4, t + 19, sk[1]); cv.put(c + 3, t + 20, sk[1])
    for y in range(t + 18, t + 21):                 # clean, lit chin (no stubble read)
        for x in range(c - 4, c + 4):
            if cv.own[y, x] == cv.names["face"] and cv.get(x, y) != sk[0]:
                cv.put(x, y, sk[2])
    cv.put(c - 1, t + 20, sk[3]); cv.put(c, t + 20, sk[3]); cv.put(c + 3, t + 19, sk[1])
    for s in (-1, 1):
        cv.put(c + s * 8, t + 13, POD); cv.put(c + s * 8, t + 14, POD if s < 0 else POD2)
        cv.put(c + s * 8, t + 15, POD2)
    # ---- hair: faded sides, then the swoop rising off the forehead and sweeping to his left ----
    skull = cv.ell(c, t + 9, 7.7, 5.8) & cv.half(y=t + 10, below=False)
    skull |= cv.capsule(c - 7, t + 7, c - 7.2, t + 11, 1.3) | cv.capsule(c + 7, t + 7, c + 7.2, t + 11, 1.3)
    skull |= cv.ell(c + 6.8, t + 6.2, 2.6, 2.2)      # fills under the curl so no notch shows
    sl = np.where(skull, 1, 0) + np.where(skull & (cv.X < c - 3) & (cv.Y < t + 8), 1, 0)
    cv.part("hair", skull, "hair", lv=sl)          # short faded sides, a tone darker
    swoop = cv.poly([(c - 6.5, t + 5.5), (c - 6, t + 1.5), (c - 3.5, t - 1.0), (c + 0.5, t - 2.0), (c + 5, t - 1.8),
                     (c + 8.6, t + 0.0), (c + 10.6, t + 3), (c + 11, t + 6.5), (c + 9.6, t + 8.6), (c + 8.2, t + 6.6),
                     (c + 6, t + 4.6), (c + 3, t + 5.2), (c, t + 6.2), (c - 3, t + 7.6), (c - 5.5, t + 8.6)])
    cv.part("swoop", swoop, "hair", rad=3.5, soft=1.0, cuts=(0.22, 0.46, 0.78), light=(-0.6, -0.8, 0.5))
    # strands follow the sweep; the tip curls under
    cv.line(c - 4, t + 0, c + 2, t - 1, hr[4]); cv.put(c + 3, t - 1, hr[3]); cv.put(c - 5, t + 1, hr[4])
    cv.line(c - 4, t + 3, c + 4, t + 1, hr[1])                 # groove between strand locks
    cv.line(c - 3, t + 4, c + 5, t + 2, hr[3])
    cv.line(c - 4, t + 6, c - 1, t + 5, hr[3])
    cv.line(c + 6, t + 1, c + 9, t + 4, hr[3])
    # forehead shadow under the swoop
    for x in range(c - 6, c + 7):
        for y in range(t + 5, t + 11):
            if cv.own[y, x] == cv.names["face"] and cv.own[y - 1, x] in (cv.names["hair"], cv.names["swoop"]):
                cv.put(x, y, sk[1])
                break
    # ---- face ----
    b_face_front(cv, c, t + 1, pose)


def b_face_front(cv, c, t, pose):
    sk = RAMP["skin"]
    ey = t + 10
    # brows: thick, confident
    for s in (-1, 1):
        x0 = c + s * 2
        lift = 1 if pose in ("hit",) and s > 0 else 0
        for k in range(4):
            yy = ey - 2 - (1 if k in (1, 2) else 0) - lift + (1 if pose == "tell" and k == 0 else 0)
            cv.put(x0 + s * k, yy, BROW)
    # eyes
    for s in (-1, 1):
        ex = c + s * 3 - (1 if s < 0 else 0)          # left pixel of the 2-wide eye
        if pose == "hit":
            cv.puts([(ex, ey), (ex + 1, ey + 1)] if s < 0 else [(ex + 1, ey), (ex, ey + 1)], EYE)
            cv.put(ex + (1 if s < 0 else 0), ey, EYE)
            continue
        if pose == "tell":                             # a wink to the crowd (his left eye)
            if s > 0:
                cv.hline(ex - 1, ex + 1, ey + 1, EYE); cv.put(ex + 2, ey, EYE)
                continue
        cv.put(ex, ey, EYE); cv.put(ex + 1, ey, EYE)
        cv.put(ex, ey + 1, IRIS); cv.put(ex + 1, ey + 1, EYE)
        cv.put(ex if s < 0 else ex, ey, WHITE)            # catch-light (ring shaped in the portrait)
        cv.put(ex - 1 if s < 0 else ex + 2, ey + 1, SCLERA)
        cv.hline(ex, ex + 1, ey + 2, sk[1])
    # nose
    cv.puts([(c, t + 12), (c, t + 13)], sk[3]); cv.put(c, t + 11, sk[3])
    cv.puts([(c + 1, t + 12), (c + 1, t + 13), (c + 1, t + 14)], sk[1])
    cv.puts([(c - 1, t + 14), (c, t + 14)], sk[1])
    # cheeks
    cv.put(c - 5, t + 13, BLUSH); cv.put(c + 5, t + 13, mix(BLUSH, sk[1], 0.4))
    # mouth: the famous grin
    my = t + 16
    if pose == "idle":
        cv.hline(c - 3, c + 3, my, TEETH); cv.put(c + 2, my, TEETH2)
        cv.put(c - 4, my - 1, MOUTH); cv.put(c + 4, my - 1, MOUTH)
        cv.put(c - 4, my, MOUTH); cv.put(c + 4, my, MOUTH)
        cv.hline(c - 3, c + 3, my + 1, MOUTH)
        cv.hline(c - 1, c + 1, my + 2, LIP)
    elif pose == "talk":
        cv.hline(c - 3, c + 3, my, TEETH); cv.put(c + 2, my, TEETH2)
        cv.put(c - 4, my - 1, MOUTH); cv.put(c + 4, my - 1, MOUTH)
        cv.put(c - 4, my, MOUTH); cv.put(c + 4, my, MOUTH)
        cv.hline(c - 3, c + 3, my + 1, MOUTH)
        cv.hline(c - 2, c + 2, my + 2, MOUTH); cv.hline(c - 1, c + 1, my + 2, TONGUE)
        cv.hline(c - 1, c + 1, my + 3, LIP)
    elif pose == "tell":
        cv.hline(c - 4, c + 4, my, TEETH); cv.put(c + 3, my, TEETH2)
        cv.put(c - 5, my - 1, MOUTH); cv.put(c + 5, my - 2, MOUTH); cv.put(c + 5, my - 1, MOUTH)
        cv.put(c - 5, my, MOUTH)
        cv.hline(c - 4, c + 4, my + 1, MOUTH)
        cv.hline(c - 2, c + 2, my + 2, LIP)
    elif pose == "hit":
        cv.hline(c - 3, c + 3, my, MOUTH)
        cv.hline(c - 2, c + 2, my + 1, TEETH)
        cv.put(c - 3, my + 1, MOUTH); cv.put(c + 3, my + 1, MOUTH)
        cv.hline(c - 2, c + 2, my + 2, MOUTH)


def b_front(pose):
    cv = Cv(BW, BH)
    c, t = 46, BT
    # ---- props behind the body ----
    if pose == "tell":
        handle(cv, c - 20, t + 26, c - 24, t + 16)
        ring_light(cv, c - 26, t + 5, R=10.5)
    b_legs(cv, c, t)
    b_torso(cv, c, t)
    # ---- arms ----
    if pose in ("idle", "talk"):
        # viewer-left: ring light held low by his hip
        handle(cv, c - 17, t + 52, c - 22, t + 43)
        ring_light(cv, c - 27, t + 34, R=10.5)
        b_arm(cv, "armL", [(c - 12, t + 26), (c - 15, t + 37), (c - 16, t + 48)])
        b_hand(cv, c - 16, t + 51, "handL")
        cv.put(c - 17, t + 52, RAMP["skin"][1])
    elif pose == "tell":
        b_arm(cv, "armL", [(c - 12, t + 26), (c - 19, t + 33), (c - 20, t + 27)])
        b_hand(cv, c - 20, t + 25, "handL")
    elif pose == "hit":
        # ring light knocked sideways, arm flung out
        handle(cv, c - 20, t + 32, c - 26, t + 38)
        ring_light(cv, c - 31, t + 42, R=9.0, squash=0.55, ang=0.5)
        b_arm(cv, "armL", [(c - 12, t + 26), (c - 18, t + 31), (c - 21, t + 30)])
        b_hand(cv, c - 21, t + 31, "handL")
    if pose == "idle":
        b_arm(cv, "armR", [(c + 12, t + 26), (c + 15, t + 37), (c + 16, t + 47)])
        fan(cv, c + 17, t + 50, base=0.30, spread=0.30)
        b_hand(cv, c + 16, t + 50, "handR")
    elif pose == "talk":
        # finger guns at the viewer
        b_arm(cv, "armR", [(c + 12, t + 26), (c + 18, t + 35), (c + 22, t + 31)])
        b_hand(cv, c + 23, t + 30, "handR", rx=2.6, ry=2.4)
        fing = cv.capsule(c + 24, t + 29, c + 29, t + 26, 1.2) | cv.capsule(c + 22, t + 28, c + 22, t + 25, 1.1)
        cv.part("fingers", fing, "skin", edge="ink", noedge=("handR",), rad=1.2, soft=0.4, bias=0.1)
        # two cards peek from the vest pocket
        cv.puts([(c + 5, t + 38), (c + 6, t + 37), (c + 7, t + 37)], INK)
        cv.puts([(c + 6, t + 38), (c + 7, t + 38)], CARD_GLOW[0])
    elif pose == "tell":
        # the hand of cards held up at the viewer like a winning poker hand
        b_arm(cv, "armR", [(c + 12, t + 26), (c + 17, t + 36), (c + 10, t + 38)])
        fan(cv, c + 8, t + 38, base=-0.05, spread=0.36, n=5, L=11, W=7)
        b_hand(cv, c + 8, t + 38, "handR")
    elif pose == "hit":
        b_arm(cv, "armR", [(c + 12, t + 26), (c + 19, t + 30), (c + 22, t + 24)])
        b_hand(cv, c + 22, t + 22, "handR")
        # cards fly out of his hand
        card(cv, c + 33, t + 22, 0.35, L=9, W=6, glow=0, name="fly0")
        card(cv, c + 31, t + 6, -0.3, L=9, W=6, glow=1, name="fly1")
        card(cv, c + 40, t + 37, 1.57, L=9, W=6, glow=2, name="fly2")
    # ---- head ----
    hx = 2 if pose == "hit" else 0
    b_head_front(cv, c + hx, t, pose)
    cv.outline()
    if pose == "tell":
        sparkle(cv, c - 12, t + 16)
    if pose == "hit":
        # an AirPod pops out
        cv.puts([(c + 14, t + 4), (c + 15, t + 4), (c + 14, t + 5), (c + 15, t + 5), (c + 15, t + 6), (c + 15, t + 7)], POD)
        cv.puts([(c + 15, t + 5), (c + 15, t + 7)], POD2)
        cv.puts([(c + 12, t + 3), (c + 17, t + 2), (c + 17, t + 8)], SPARK2)
        sx, sy = c - 10, t + 1
        cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx + 1, sy + 1), (sx - 1, sy + 2), (sx, sy + 2), (sx + 1, sy + 2), (sx, sy + 3)], SWEAT)
        cv.put(sx - 1, sy + 1, SWEAT_HI)
    return cv


def b_side():
    """Side view facing RIGHT (we see his left side and the ring light held at his hip)."""
    cv = Cv(BW, BH)
    c, t = 44, BT
    sk, hr, pr, sr, vs, sh = RAMP["skin"], RAMP["hair"], RAMP["pants"], RAMP["shoe"], RAMP["vest"], RAMP["shirt"]
    # far arm (just the hand of cards peeking behind the back)
    fan(cv, c - 9, t + 49, base=-0.9, spread=0.28, n=3, L=10, W=7, name="fanB")
    b_hand(cv, c - 8, t + 49, "handB")
    # legs: far leg a tone darker, a short stride
    legB = cv.poly([(c - 6, t + 49), (c + 3, t + 49), (c + 2, t + 60), (c - 2, t + 76), (c - 7, t + 76), (c - 5, t + 60)])
    cv.part("legB", legB, "pants", rad=3, cuts=(0.45, 0.7, 0.95))
    cv.part("ankleB", cv.rect(c - 6, t + 77, c - 3, t + 78), "skin", edge="dark", lv=np.where(cv.rect(c - 6, t + 77, c - 3, t + 78), 1, 0))
    shB = cv.ell(c - 3, t + 80.2, 6.0, 2.6) & cv.half(y=t + 81, below=False) & cv.half(y=t + 77.6)
    cv.part("shoeB", shB, "shoe", rad=2, cuts=(0.45, 0.7, 0.95))
    legF = cv.poly([(c - 5, t + 49), (c + 6, t + 49), (c + 6, t + 58), (c + 5, t + 67), (c + 5, t + 76), (c - 1, t + 76),
                    (c - 2, t + 67), (c - 5, t + 58)])
    cv.part("legF", legF, "pants", rad=4, soft=1.0, cuts=(0.30, 0.56, 0.9), tex=0.03, seed=13)
    cv.line(c + 2, t + 58, c + 2, t + 74, pr[1])
    cv.hline(c - 1, c + 5, t + 75, pr[1])
    ank = cv.rect(c, t + 77, c + 4, t + 78)
    cv.part("ankleF", ank, "skin", edge="dark", lv=np.where(ank, 2, 0))
    shF = cv.ell(c + 4, t + 80.2, 6.4, 2.6) & cv.half(y=t + 81, below=False) & cv.half(y=t + 77.6)
    cv.part("shoeF", shF, "shoe", rad=2.5, soft=0.7, cuts=(0.30, 0.55, 0.85))
    cv.hline(c + 3, c + 7, t + 79, sr[1]); cv.put(c + 5, t + 79, RAMP["gold"][3]); cv.put(c + 8, t + 79, sr[4])
    cv.hline(c - 2, c + 10, t + 81, sr[0])
    # torso in profile: chest forward, flat back
    shirt = cv.poly([(c - 6, t + 22), (c + 4, t + 22), (c + 8, t + 28), (c + 8, t + 38), (c + 6, t + 50), (c - 6, t + 50),
                     (c - 7, t + 36), (c - 7, t + 26)])
    cv.part("shirt", shirt, "shirt", rad=5, soft=1.2, cuts=(0.28, 0.52, 0.86))
    vest = cv.poly([(c - 6, t + 22), (c + 4, t + 21), (c + 8, t + 27), (c + 9, t + 37), (c + 8, t + 51), (c - 7, t + 51),
                    (c - 8, t + 36), (c - 7, t + 27)])
    cv.part("vest", vest, "vest", rad=7, soft=1.6, cuts=(0.26, 0.50, 0.84), tex=0.05, seed=17)
    hem = vest & cv.half(y=t + 49)
    cv.part("hem", hem, "vest", noedge=("vest",), lv=np.where(hem, 1, 0) + np.where(hem & (cv.X > c), 1, 0))
    cv.line(c + 1, t + 30, c + 2, t + 48, vs[1])                 # side seam
    # stand collar + zip at the front
    colm = cv.poly([(c - 3, t + 19), (c + 4, t + 18), (c + 6, t + 23), (c - 2, t + 24)])
    cv.part("collar", colm, "vest", rad=2, soft=0.6, bias=0.12)
    cv.puts([(c + 5, t + 19), (c + 6, t + 20)], sh[4])
    cv.vline(c + 8, t + 26, t + 32, RAMP["metal"][1]); cv.put(c + 9, t + 33, RAMP["metal"][3])
    cv.hline(c + 5, c + 7, t + 28, (236, 236, 228))
    # near arm hangs by the side holding the ring light, which faces forward (edge-on to us)
    b_arm(cv, "arm", [(c - 1, t + 25), (c + 0, t + 37), (c + 2, t + 47)])
    handle(cv, c + 3, t + 50, c + 9, t + 45)
    rx0, ry0 = c + 13, t + 37
    ringm = cv.ell(rx0, ry0, 4.4, 10.5) & ~cv.ell(rx0, ry0, 1.5, 7.2)
    cv.part("ring", ringm, "house", edge="ink", rad=2, soft=0.6)
    ys, xs = np.nonzero(ringm)
    for y, x in zip(ys, xs):
        # the LED face points forward (right): its rim shows as a bright crescent on the right
        if x >= rx0 + 1 and cv.get(x, y) != INK:
            cv.put(x, y, LED if y < ry0 else LED2)
    cv.vline(rx0, ry0 - 2, ry0 + 2, RAMP["house"][1])          # the phone, edge-on
    b_hand(cv, c + 3, t + 50, "hand")
    cv.put(c + 4, t + 51, sk[1])
    # ---- head in profile: hand-placed pixels (col 0 = c-11, row 0 = t-2) ----
    nk = cv.rect(c - 4, t + 16, c + 2, t + 23)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 2, 0) - np.where(nk & ((cv.X > c - 1) | (cv.Y < t + 20)), 1, 0))
    paint_map(cv, c - 11, t - 2, SIDE_HEAD, head_pal(), name="head")
    cv.outline()
    return cv


def b_back():
    cv = Cv(BW, BH)
    c, t = 46, BT
    hr, vs = RAMP["hair"], RAMP["vest"]
    b_legs(cv, c, t, back=True)
    pr = RAMP["pants"]
    for s in (-1, 1):                          # back pockets
        cv.hline(c + s * 3 if s > 0 else c - 8, c + 8 if s > 0 else c - 3, t + 52, pr[1])
    b_torso(cv, c, t, back=True)
    # arms: ring light in his right hand (viewer right from behind), cards in his left
    b_arm(cv, "armL", [(c - 12, t + 26), (c - 15, t + 37), (c - 16, t + 47)])
    fan(cv, c - 17, t + 50, base=-0.30, spread=0.30, name="fanL")
    b_hand(cv, c - 16, t + 50, "handL")
    handle(cv, c + 17, t + 52, c + 22, t + 43)
    ring_light(cv, c + 27, t + 34, R=10.5, back=True)
    b_arm(cv, "armR", [(c + 12, t + 26), (c + 15, t + 37), (c + 16, t + 48)])
    b_hand(cv, c + 16, t + 51, "handR")
    # neck, ears + AirPod stems, back of the head
    nk = cv.rect(c - 3, t + 15, c + 3, t + 23)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 2, 0) - np.where(nk & (cv.Y >= t + 19), 1, 0))
    cv.part("collar", cv.ell(c, t + 21.5, 6.5, 2.4), "vest", rad=2, bias=0.1)
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 7.4, t + 13, 1.7, 2.4), "skin", bias=0.05)
    head = cv.ell(c, t + 9, 7.8, 7.2) | (cv.rect(c - 6.6, t + 9, c + 6.6, t + 17) & cv.ell(c, t + 11, 7.4, 7.4))
    head &= cv.half(y=t + 17, below=False)
    lvh = np.where(head, 2, 0) + np.where(head & (cv.X < c - 1) & (cv.Y < t + 9), 1, 0) - np.where(head & (cv.Y > t + 12), 1, 0)
    lvh = lvh - np.where(head & (cv.X > c + 3) & (cv.Y > t + 6), 1, 0)
    cv.part("head", head, "hair", lv=np.clip(lvh, 1, 4) * head)
    for (x0, y0, x1, y1, col) in [(c - 5, t + 6, c - 3, t + 10, hr[2]), (c - 1, t + 5, c, t + 10, hr[2]),
                                  (c + 3, t + 6, c + 4, t + 10, hr[1]), (c - 3, t + 12, c - 2, t + 15, hr[2]),
                                  (c + 2, t + 12, c + 2, t + 15, hr[0])]:
        cv.line(x0, y0, x1, y1, col)
    swoop = cv.poly([(c - 6, t + 3), (c - 3.5, t - 1.0), (c + 0.5, t - 2.0), (c + 5, t - 1.8), (c + 8.6, t + 0.5),
                     (c + 8, t + 3.5), (c + 2, t + 2.2), (c - 3, t + 3.5)])
    cv.part("swoop", swoop, "hair", rad=2.5, soft=0.8, cuts=(0.22, 0.46, 0.78), light=(-0.6, -0.8, 0.5))
    cv.line(c - 3, t + 0, c + 3, t - 1, hr[4])
    for x in range(c - 2, c + 3, 2):
        cv.put(x, t + 17, RAMP["skin"][2])
    for s in (-1, 1):
        cv.puts([(c + s * 8, t + 12), (c + s * 8, t + 13), (c + s * 8, t + 14), (c + s * 8, t + 15)], POD)
        cv.put(c + s * 8, t + 15, POD2)
    cv.outline()
    return cv


# ==========================================================================
# ENTRANCE  (cell 12: the intro-card pose, wider canvas)
# ==========================================================================
EW, EH = 128, 108


def entrance():
    """Power stance under his own spotlight: the ring light hoisted overhead like a trophy, the hand
    of LED cards thrown open at the viewer, a wink and a sparkle off the teeth."""
    cv = Cv(EW, EH)
    c, t = 60, EH - 82
    rx, ry, R = c - 24, t - 9, 11.5
    b_legs(cv, c, t, spread=5)
    b_torso(cv, c, t)
    # ring arm up
    b_arm(cv, "armL", [(c - 12, t + 26), (c - 20, t + 18), (c - 22, t + 8)])
    handle(cv, c - 22, t + 6, rx + 1, ry + R - 1, r=1.5)
    ring_light(cv, rx, ry, R=R, band=3.5)
    b_hand(cv, c - 22, t + 6, "handL", rx=2.8, ry=3.0)
    # cards thrown open
    b_arm(cv, "armR", [(c + 12, t + 26), (c + 21, t + 31), (c + 29, t + 27)])
    fan(cv, c + 31, t + 26, base=0.12, spread=0.36, n=5, L=12, W=8, name="fanE")
    b_hand(cv, c + 30, t + 27, "handR", rx=2.8, ry=2.8)
    b_head_front(cv, c, t, "tell")
    cv.outline()
    # light rays off the ring (drawn after the ink pass so they stay thin and bright)
    for k in range(10):
        a = -math.pi * 0.95 + k * (math.pi * 1.15 / 9)
        for d_ in range(int(R + 3), int(R + 3 + (5 if k % 2 else 8))):
            x, y = int(round(rx + math.cos(a) * d_)), int(round(ry + math.sin(a) * d_))
            if 0 <= x < EW and 0 <= y < EH and not cv.alpha[y, x]:
                cv.put(x, y, LED2 if d_ < R + 6 else LED3)
    sparkle(cv, c - 11, t + 17)
    sparkle(cv, c + 46, t + 12, big=False)
    sparkle(cv, c + 22, t + 2, big=False)
    sparkle(cv, rx + 14, ry - 10, big=True)
    return cv


# ==========================================================================
# WORLD  (52 px standing height, redrawn small -- not scaled)
# ==========================================================================
WW, WH = 60, 56
WT = WH - 52

# front head, col 0 = c-8, row 0 = t (crest).  Rows 7-13 are swapped per expression.
W_HEAD = [
    "......KKKKK.....",
    "....KK444443K...",
    "...K33444433332K",
    "..K223333332222K",
    "..K1222222221K2K",
    "..K11dddddd11KK.",
    ".KK1dslllllsd1K.",
    ".KdsBBlllsBBsdK.",
    "KdKsWEllllEWsKdK",
    "KPKsdEsldsEdsKPK",
    ".pKrsssldsssrKp.",
    "..KsMTTTTTTMsK..",
    "..KdsMMMMMMsdK..",
    "...KdssLLssdK...",
    "....KKddddKK....",
]
W_FACE = {
    "idle": {},
    "talk": {12: "..KdsMooooMsdK..", 13: "...KdsMMMMsdK..."},
    "tell": {8: "KdKsWElllsssdKdK", 9: "KPKsdEsldEEEsKPK",
             11: "..KsMTTTTTTTMK..", 10: ".pKrsssldsssMKp."},
    "hit":  {7: ".KdBBslllllBBdK.", 8: "KdKsEsllllsEsKdK", 9: "KPKssEsldsEssKPK",
             11: "..KssMTTTTMssK..", 12: "..KdsdMMMMdsdK.."},
    "blink": {8: "KdKsssllllsssKdK", 9: "KPKsEEsldsEEsKPK"},
    "glance": {8: "KdKsEWllllEWsKdK", 9: "KPKsEdsldsEdsKPK"},
    "glance2": {8: "KdKsWEllllWEsKdK", 9: "KPKsdEsldsdEsKPK"},
}

# profile head facing right, col 0 = c-8, row 0 = t
W_SIDE = [
    "......KKKK......",
    "....KK44443K....",
    "...K334443332K..",
    "..K22333322222K.",
    ".K1222222211K2K.",
    ".K112222221dssK.",
    "K11122221dsllsK.",
    "K1112211dsllBBK.",
    "K111KKdslllWEK..",
    "K11KsPdsllllssK.",
    "K11KdpdssssssslK",
    ".K1KKddssssssdK.",
    "..KKddsssssMTTK.",
    "...KddssssssMMK.",
    "....KddsssssLK..",
    ".....KKddddKK...",
]


def w_head_front(cv, c, t, face="idle", dx=0):
    rows = list(W_HEAD)
    for k, r in W_FACE.get(face, {}).items():
        rows[k] = r
    nk = cv.rect(c - 2, t + 13, c + 1, t + 17)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 2, 0) - np.where(nk & (cv.Y <= t + 14), 1, 0))
    paint_map(cv, c - 8 + dx, t, rows, head_pal(), name="head")


def w_arm(cv, name, pts, r0=2.1, r1=1.8):
    m = cv.empty()
    n = len(pts) - 1
    for k, ((a, b), (c_, d)) in enumerate(zip(pts, pts[1:])):
        m |= cv.capsule(a, b, c_, d, r0 + (r1 - r0) * k / n, r0 + (r1 - r0) * (k + 1) / n)
    cv.part(name, m, "shirt", edge="dark", rad=2, soft=0.7, cuts=(0.28, 0.52, 0.88))
    return m


def w_hand(cv, x, y, name, r=1.8):
    m = cv.ell(x, y, r, r)
    cv.part(name, m, "skin", edge="ink", lv=np.where(m, 3, 0) - np.where(m & (cv.X > x) & (cv.Y > y - 1), 1, 0))
    return m


def w_legs(cv, c, t, back=False):
    pr, sr = RAMP["pants"], RAMP["shoe"]
    for s in (-1, 1):
        leg = cv.poly([(c + s * 0.5, t + 32), (c + s * 7, t + 32), (c + s * 6.5, t + 40), (c + s * 6, t + 47.5),
                       (c + s * 1.8, t + 47.5), (c + s * 1.4, t + 40), (c + s * 0.5, t + 36)])
        cv.part("leg%d" % s, leg, "pants", rad=3, soft=0.8, cuts=(0.30, 0.56, 0.9))
        cv.vline(c + s * 4, t + 38, t + 46, pr[1] if s < 0 else pr[0])
    for s in (-1, 1):
        ax = c + s * 4
        ank = cv.rect(ax - 1, t + 48, ax + 1, t + 48)
        cv.part("ankle%d" % s, ank, "skin", edge=None, lv=np.where(ank, 2, 0))
        sh = cv.ell(c + s * 4.3, t + 50.4, 3.7, 1.9) & cv.half(y=t + 51, below=False) & cv.half(y=t + 48.6)
        cv.part("shoe%d" % s, sh, "shoe", rad=2, soft=0.5, cuts=(0.3, 0.55, 0.85))
        if not back:
            cv.put(c + s * 4.3 - 1, t + 49, RAMP["gold"][3])


def w_torso(cv, c, t, back=False):
    sh, vs = RAMP["shirt"], RAMP["vest"]
    shirt = cv.poly([(c - 7, t + 15), (c + 7, t + 15), (c + 9, t + 18), (c + 8, t + 24), (c + 7, t + 32), (c - 7, t + 32),
                     (c - 8, t + 24), (c - 9, t + 18)])
    cv.part("shirt", shirt, "shirt", rad=4, soft=1.0, cuts=(0.28, 0.52, 0.86))
    vest = cv.poly([(c - 5, t + 15), (c + 5, t + 15), (c + 6.5, t + 18), (c + 6, t + 21), (c + 7, t + 24), (c + 7.5, t + 33),
                    (c - 7.5, t + 33), (c - 7, t + 24), (c - 6, t + 21), (c - 6.5, t + 18)])
    cv.part("vest", vest, "vest", rad=5, soft=1.2, cuts=(0.26, 0.50, 0.84))
    hem = vest & cv.half(y=t + 32)
    cv.part("hem", hem, "vest", noedge=("vest",), lv=np.where(hem, 1, 0) + np.where(hem & (cv.X < c - 2), 1, 0))
    if back:
        return
    cv.puts([(c - 2, t + 15), (c - 1, t + 16), (c + 2, t + 15), (c + 1, t + 16)], sh[4])
    cv.put(c, t + 15, sh[1]); cv.put(c, t + 16, sh[1])
    cv.puts([(c - 3, t + 15), (c + 3, t + 15)], vs[3])
    for y in range(t + 17, t + 21):
        cv.put(c, y, vs[0] if y % 2 else RAMP["metal"][1])
    cv.put(c, t + 21, RAMP["metal"][3])
    cv.hline(c + 2, c + 4, t + 18, (236, 236, 228)); cv.put(c + 3, t + 18, (240, 120, 70))
    cv.puts([(c - 5, t + 19), (c - 4, t + 18)], vs[3])


def w_front(pose):
    cv = Cv(WW, WH)
    c, t = 30, WT
    sk = RAMP["skin"]
    if pose == "tell":
        handle(cv, c - 12, t + 15, c - 15, t + 9, r=1.0)
        ring_light(cv, c - 17, t + 3, R=6.6, band=2.2)
    w_legs(cv, c, t)
    w_torso(cv, c, t)
    if pose in ("idle", "talk", "blink", "glance", "cards"):
        handle(cv, c - 10, t + 33, c - 13, t + 28, r=1.0)
        ring_light(cv, c - 16, t + 22, R=6.6, band=2.2)
        w_arm(cv, "armL", [(c - 8, t + 17), (c - 9.5, t + 24), (c - 10, t + 30)])
        w_hand(cv, c - 10, t + 32, "handL")
    elif pose == "selfie":
        # lifts the ring light to check his look in the phone
        handle(cv, c - 13, t + 15, c - 15, t + 11, r=1.0)
        ring_light(cv, c - 16, t + 6, R=6.6, band=2.2)
        w_arm(cv, "armL", [(c - 8, t + 17), (c - 12.5, t + 22), (c - 13, t + 17.5)])
        w_hand(cv, c - 13, t + 15.5, "handL")
    elif pose == "tell":
        w_arm(cv, "armL", [(c - 8, t + 17), (c - 12, t + 21), (c - 12.5, t + 17)])
        w_hand(cv, c - 12.5, t + 15.5, "handL")
    elif pose == "hit":
        handle(cv, c - 12, t + 21, c - 16, t + 25, r=1.0)
        ring_light(cv, c - 20, t + 28, R=6.4, squash=0.55, ang=0.5, band=2.2)
        w_arm(cv, "armL", [(c - 8, t + 17), (c - 11, t + 20), (c - 13, t + 19)])
        w_hand(cv, c - 13, t + 20, "handL")
    if pose in ("idle", "blink", "glance"):
        w_arm(cv, "armR", [(c + 8, t + 17), (c + 9.5, t + 24), (c + 10, t + 30)])
        fan(cv, c + 11, t + 31, base=0.30, spread=0.36, n=3, L=6.5, W=4.6, name="fan")
        w_hand(cv, c + 10, t + 32, "handR")
    elif pose == "talk":
        w_arm(cv, "armR", [(c + 8, t + 17), (c + 12, t + 23), (c + 14, t + 20)])
        w_hand(cv, c + 14.5, t + 19, "handR")
        fing = cv.capsule(c + 15.5, t + 18.5, c + 18, t + 17, 0.8)
        cv.part("fingers", fing, "skin", edge="ink", noedge=("handR",), lv=np.where(fing, 3, 0))
    elif pose == "tell":
        w_arm(cv, "armR", [(c + 8, t + 17), (c + 11, t + 23), (c + 6, t + 25)])
        fan(cv, c + 5, t + 24, base=0.0, spread=0.40, n=4, L=7, W=5, name="fan")
        w_hand(cv, c + 5, t + 25, "handR")
    elif pose == "hit":
        w_arm(cv, "armR", [(c + 8, t + 17), (c + 12, t + 20), (c + 14, t + 15)])
        w_hand(cv, c + 14, t + 13.5, "handR")
        card(cv, c + 21, t + 14, 0.4, L=6, W=4.5, glow=0, name="fly0")
        card(cv, c + 20, t + 4, -0.3, L=6, W=4.5, glow=1, name="fly1")
    elif pose == "selfie":
        w_arm(cv, "armR", [(c + 8, t + 17), (c + 9.5, t + 24), (c + 10, t + 30)])
        fan(cv, c + 11, t + 31, base=0.30, spread=0.36, n=3, L=6.5, W=4.6, name="fan")
        w_hand(cv, c + 10, t + 32, "handR")
    elif pose == "cards":
        # fans the hand of cards open at chest height, admiring them
        w_arm(cv, "armR", [(c + 8, t + 17), (c + 11.5, t + 23), (c + 7, t + 25)])
        fan(cv, c + 6, t + 24, base=-0.05, spread=0.42, n=3, L=6.5, W=4.6, name="fan")
        w_hand(cv, c + 6, t + 25, "handR")
    face = {"idle": "idle", "talk": "talk", "tell": "tell", "hit": "hit", "blink": "blink", "glance": "glance",
            "selfie": "glance", "cards": "glance2"}[pose]
    w_head_front(cv, c + (1 if pose == "hit" else 0), t, face)
    cv.outline()
    if pose == "tell":
        sparkle(cv, c - 10, t + 11, big=False)
    if pose == "hit":
        cv.puts([(c + 9, t + 2), (c + 9, t + 3), (c + 10, t + 3)], POD)
        cv.puts([(c - 8, t + 1), (c - 9, t + 2), (c - 8, t + 2), (c - 8, t + 3)], SWEAT)
    return cv


def w_side():
    cv = Cv(WW, WH)
    c, t = 28, WT
    pr, sr, vs = RAMP["pants"], RAMP["shoe"], RAMP["vest"]
    fan(cv, c - 6, t + 31, base=-0.9, spread=0.32, n=2, L=6.5, W=4.6, name="fanB")
    w_hand(cv, c - 5, t + 31, "handB")
    legB = cv.poly([(c - 4, t + 32), (c + 2, t + 32), (c + 1, t + 39), (c - 1, t + 47.5), (c - 4.5, t + 47.5), (c - 3, t + 39)])
    cv.part("legB", legB, "pants", rad=2, cuts=(0.45, 0.7, 0.95))
    cv.part("shoeB", cv.ell(c - 2, t + 50.4, 4.0, 1.9) & cv.half(y=t + 51, below=False) & cv.half(y=t + 48.6), "shoe", rad=2, cuts=(0.45, 0.7, 0.95))
    legF = cv.poly([(c - 3, t + 32), (c + 4, t + 32), (c + 4, t + 38), (c + 3.5, t + 47.5), (c - 0.5, t + 47.5), (c - 1.5, t + 42), (c - 3, t + 37)])
    cv.part("legF", legF, "pants", rad=3, soft=0.8, cuts=(0.30, 0.56, 0.9))
    cv.vline(c + 1, t + 38, t + 46, pr[1])
    cv.part("ankleF", cv.rect(c, t + 48, c + 3, t + 48), "skin", edge=None, lv=np.where(cv.rect(c, t + 48, c + 3, t + 48), 2, 0))
    cv.part("shoeF", cv.ell(c + 3, t + 50.4, 4.2, 1.9) & cv.half(y=t + 51, below=False) & cv.half(y=t + 48.6), "shoe", rad=2, soft=0.5, cuts=(0.3, 0.55, 0.85))
    cv.put(c + 4, t + 49, RAMP["gold"][3])
    shirt = cv.poly([(c - 4, t + 15), (c + 3, t + 15), (c + 5, t + 18), (c + 5, t + 25), (c + 4, t + 32), (c - 4, t + 32), (c - 5, t + 24), (c - 5, t + 17)])
    cv.part("shirt", shirt, "shirt", rad=3, soft=1.0)
    vest = cv.poly([(c - 4, t + 15), (c + 3, t + 14.5), (c + 5.5, t + 18), (c + 6, t + 24), (c + 5.5, t + 33), (c - 5, t + 33), (c - 5.5, t + 24), (c - 5, t + 18)])
    cv.part("vest", vest, "vest", rad=4, soft=1.2, cuts=(0.26, 0.50, 0.84))
    hem = vest & cv.half(y=t + 32)
    cv.part("hem", hem, "vest", noedge=("vest",), lv=np.where(hem, 1, 0) + np.where(hem & (cv.X > c), 1, 0))
    cv.vline(c + 5, t + 17, t + 21, RAMP["metal"][1])
    cv.hline(c + 3, c + 4, t + 18, (236, 236, 228))
    w_arm(cv, "arm", [(c - 0.5, t + 17), (c, t + 24), (c + 1.5, t + 30)])
    handle(cv, c + 2, t + 32, c + 6, t + 28, r=1.0)
    rx0, ry0 = c + 8, t + 23
    ringm = cv.ell(rx0, ry0, 2.8, 6.8) & ~cv.ell(rx0, ry0, 0.9, 4.4)
    cv.part("ring", ringm, "house", edge="ink", rad=2, soft=0.6)
    ys, xs = np.nonzero(ringm)
    for y, x in zip(ys, xs):
        if x >= rx0 + 1:
            cv.put(x, y, LED if y < ry0 else LED2)
    w_hand(cv, c + 2, t + 32, "hand")
    nk = cv.rect(c - 3, t + 12, c + 1, t + 16)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 1, 0))
    paint_map(cv, c - 8, t, W_SIDE, head_pal(), name="head")
    cv.outline()
    return cv


def w_back():
    cv = Cv(WW, WH)
    c, t = 30, WT
    hr = RAMP["hair"]
    w_legs(cv, c, t, back=True)
    w_torso(cv, c, t, back=True)
    w_arm(cv, "armL", [(c - 8, t + 17), (c - 9.5, t + 24), (c - 10, t + 30)])
    fan(cv, c - 11, t + 31, base=-0.30, spread=0.36, n=3, L=6.5, W=4.6, name="fanL")
    w_hand(cv, c - 10, t + 32, "handL")
    handle(cv, c + 10, t + 33, c + 13, t + 28, r=1.0)
    ring_light(cv, c + 16, t + 22, R=6.6, band=2.2, back=True)
    w_arm(cv, "armR", [(c + 8, t + 17), (c + 9.5, t + 24), (c + 10, t + 30)])
    w_hand(cv, c + 10, t + 32, "handR")
    nk = cv.rect(c - 2, t + 11, c + 1, t + 16)
    cv.part("neck", nk, "skin", edge=None, lv=np.where(nk, 1, 0))
    cv.part("collar", cv.ell(c, t + 15, 4.5, 1.6), "vest", rad=2, bias=0.1)
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 5.6, t + 9, 1.2, 1.7), "skin", bias=0.05)
    head = cv.ell(c, t + 6.5, 5.6, 5.4) | (cv.rect(c - 4.6, t + 6, c + 4.6, t + 12) & cv.ell(c, t + 7.5, 5.3, 5.4))
    lvh = np.where(head, 2, 0) + np.where(head & (cv.X < c - 1) & (cv.Y < t + 6), 1, 0) - np.where(head & (cv.Y > t + 9), 1, 0)
    cv.part("head", head, "hair", lv=np.clip(lvh, 1, 4) * head)
    cv.line(c - 3, t + 4, c - 2, t + 7, hr[2]); cv.line(c + 2, t + 4, c + 3, t + 7, hr[1])
    swoop = cv.poly([(c - 4, t + 2), (c - 2, t + 0.2), (c + 2, t + 0.2), (c + 6, t + 1.5), (c + 5, t + 3), (c, t + 2), (c - 3, t + 3)])
    cv.part("swoop", swoop, "hair", rad=2, soft=0.6, cuts=(0.22, 0.46, 0.78))
    for s in (-1, 1):
        cv.puts([(c + s * 6, t + 8), (c + s * 6, t + 9), (c + s * 6, t + 10)], POD)
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
    sk, hr, vs, sh = RAMP["skin"], RAMP["hair"], RAMP["vest"], RAMP["shirt"]
    lift = -2 if expr == "surprised" else 0            # the swoop pops when he's surprised
    # ---- shoulders: shirt at the edges, vest over it, mock-neck collar opened by the zip ----
    shirt = cv.ell(c, 80, 33, 26) & cv.half(y=48)
    cv.part("shirt", shirt, "shirt", rad=10, soft=1.6, cuts=(0.28, 0.52, 0.86))
    vest = cv.ell(c, 80, 27, 26) & cv.half(y=49)
    cv.part("vest", vest, "vest", noedge=(), rad=12, soft=2.0, cuts=(0.26, 0.50, 0.84), tex=0.05, seed=41)
    nk = cv.rect(c - 7, 38, c + 7, 56)
    cv.part("neck", nk, "skin", rad=6, bias=-0.15, cuts=(0.3, 0.6, 0.95))
    for x in range(c - 6, c + 7):
        cv.put(x, 46, sk[0] if abs(x - c) > 4 else sk[1]); cv.put(x, 47, sk[1])
    colm = cv.poly([(c - 13, 50), (c - 7, 47), (c - 1, 52), (c - 1, 64), (c - 6, 64), (c - 14, 56)]) | \
        cv.poly([(c + 13, 50), (c + 7, 47), (c + 1, 52), (c + 1, 64), (c + 6, 64), (c + 14, 56)])
    cv.part("collar", colm, "vest", rad=4, soft=1.0, bias=0.10)
    pts = cv.poly([(c - 8, 49), (c - 1, 53), (c - 1, 60), (c - 6, 56)]) | cv.poly([(c + 8, 49), (c + 1, 53), (c + 1, 60), (c + 6, 56)])
    cv.part("shirtcol", pts, "shirt", edge="dark", lv=np.where(pts, 4, 0) - np.where(pts & (cv.X > c + 3), 1, 0))
    cv.vline(c, 52, 63, sh[1])
    mt = RAMP["metal"]
    cv.puts([(c, 61), (c, 62)], mt[3]); cv.put(c + 1, 62, mt[2]); cv.put(c, 63, mt[1])
    cv.hline(c + 15, c + 20, 58, (236, 236, 228)); cv.hline(c + 15, c + 20, 59, (190, 200, 196))
    cv.put(c + 16, 58, (240, 120, 70)); cv.put(c + 17, 58, (240, 120, 70))
    for x in range(c - 22, c - 15):
        y = 56 + (c - 18 - x) // 3
        if cv.own[y, x] == cv.names["vest"]:
            cv.put(x, y, vs[3])
    # ---- ears + AirPods ----
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 13.6, 30, 2.6, 4.4), "skin", rad=3, bias=0.04)
        cv.puts([(c + s * 13, 29), (c + s * 13, 30), (c + s * 13, 31)], sk[1])
    # ---- face: square jaw, strong chin ----
    face = cv.ell(c, 27.5, 12.6, 14.0) | cv.poly([(c - 12.2, 29), (c + 12.2, 29), (c + 10.5, 39), (c + 5.5, 45),
                                                   (c - 5.5, 45), (c - 10.5, 39)])
    cv.part("face", face, "skin", rad=11, soft=2.6, cuts=(0.18, 0.46, 0.86), bias=0.04, light=(-0.45, -0.55, 0.75))
    # jaw line shading + chin cleft
    for (x, y) in [(c + 10, 38), (c + 9, 40), (c + 8, 42), (c + 7, 43)]:
        cv.put(x, y, sk[1])
    cv.puts([(c, 43)], sk[1]); cv.puts([(c - 2, 43), (c - 3, 44)], sk[3])
    # AirPods: a bud in each ear and the stem hanging below
    for s in (-1, 1):
        x0 = c + s * 14
        cv.puts([(x0, 30), (x0 + s, 30), (x0, 31), (x0 + s, 31)], POD)
        cv.puts([(x0 + s, 32), (x0 + s, 33), (x0 + s, 34), (x0 + s, 35)], POD)
        cv.put(x0 + s, 35, POD2); cv.put(x0, 31, POD2)
    # ---- hair: short faded sides, then the swoop ----
    skull = cv.ell(c, 19 + lift, 13.8, 10.5) & cv.half(y=15 + lift, below=False)
    for s in (-1, 1):
        skull |= cv.capsule(c + s * 12.4, 14 + lift, c + s * 12.8, 25, 1.7)
    skull |= cv.ell(c + 10.8, 15.5 + lift, 3.6, 4.6) & ~cv.ell(c, 27.5, 12.6, 14.0)   # under the curl, no gap
    sl = np.where(skull, 1, 0) + np.where(skull & (cv.X < c - 6) & (cv.Y < 22), 1, 0)
    cv.part("hairside", skull, "hair", lv=sl, edge=None)
    L = lift
    swoop = cv.poly([(c - 13, 18 + L), (c - 12.5, 10 + L), (c - 8, 4 + L), (c - 1, 1 + L), (c + 7, 1 + L), (c + 13, 3.5 + L),
                     (c + 17.5, 8 + L), (c + 19, 13 + L), (c + 17.5, 17 + L), (c + 15.5, 14 + L), (c + 12.5, 12 + L),
                     (c + 7, 12.5 + L), (c + 1, 14 + L), (c - 5, 16.5 + L), (c - 10, 19.5 + L)])
    cv.part("swoop", swoop, "hair", rad=6, soft=1.6, cuts=(0.22, 0.46, 0.80), light=(-0.6, -0.8, 0.5), tex=0.03, seed=47)
    # locks of the sweep: highlight arcs + dark grooves, all running to his left
    for (pts_, col) in [([(c - 9, 6), (c - 3, 3), (c + 4, 3), (c + 9, 4)], hr[4]),
                        ([(c - 10, 10), (c - 4, 7), (c + 3, 6), (c + 10, 7), (c + 14, 9)], hr[1]),
                        ([(c - 9, 12), (c - 3, 9), (c + 4, 9), (c + 11, 10)], hr[3]),
                        ([(c - 10, 16), (c - 5, 13), (c + 1, 11)], hr[1]),
                        ([(c + 13, 6), (c + 16, 9), (c + 17, 13)], hr[3]),
                        ([(c + 14, 11), (c + 16, 14)], hr[1])]:
        for (a, b), (d_, e) in zip(pts_, pts_[1:]):
            cv.line(a, b + L, d_, e + L, col)
    cv.puts([(c - 6, 4 + L), (c - 5, 4 + L), (c - 1, 2 + L)], hr[4])
    # forehead shadow under the swoop
    fid = cv.names["face"]
    for x in range(c - 12, c + 13):
        for y in range(8, 26):
            if cv.own[y, x] == fid:
                cv.put(x, y, sk[1])
                if cv.own[y + 1, x] == fid:
                    cv.put(x, y + 1, mix(sk[1], sk[2], 0.5))
                break
    # ---- brows ----
    by = {"neutral": 21, "warm": 20, "concern": 20, "surprised": 18}[expr]
    for s in (-1, 1):
        for k in range(7):
            x = c + s * (3 + k)
            if expr == "concern":
                dy = -1 if k < 3 else 0 if k < 5 else 1
            elif expr == "surprised":
                dy = -1 if 1 < k < 6 else 0
            elif expr == "neutral" and s > 0:
                dy = -1 if 1 < k < 6 else 0          # one cocked brow
                dy -= 1 if k in (3, 4) else 0
            else:
                dy = -1 if 1 < k < 6 else 0
            cv.put(x, by + dy, BROW)
            cv.put(x, by + dy + 1, BROW if 0 < k < 6 else mix(BROW, sk[1], 0.5))
    # ---- eyes ----
    ey = {"neutral": 24, "warm": 24, "concern": 24, "surprised": 23}[expr]
    for s in (-1, 1):
        p_eye(cv, c - 11 if s < 0 else c + 4, ey, "blink" if blink else expr, s)
    # ---- nose: straight, a little upturned ----
    cv.puts([(c - 1, 28), (c - 1, 29), (c - 1, 30), (c - 1, 31)], sk[3]); cv.put(c - 1, 32, sk[4])
    cv.puts([(c + 1, 29), (c + 1, 30), (c + 2, 31), (c + 2, 32), (c + 2, 33)], sk[1])
    cv.puts([(c - 3, 34), (c - 2, 35), (c + 2, 35), (c + 3, 34)], sk[1])
    cv.puts([(c - 1, 35), (c, 35), (c + 1, 35)], sk[1])
    cv.puts([(c - 2, 34), (c + 2, 34)], (128, 60, 44))
    # ---- cheeks (a touch of spray tan glow) ----
    for s in (-1, 1):
        bx = c + s * 9
        for y in (33, 34):
            for x in range(bx - 2, bx + 3):
                if cv.own[y, x] == fid:
                    cv.put(x, y, mix(cv.get(x, y), BLUSH, 0.35 if abs(x - bx) < 2 else 0.2))
        cv.put(c + s * 7, 36 if expr == "warm" else 37, sk[1])          # smile lines
    # ---- mouth ----
    p_mouth(cv, c, 38, expr, talk)
    cv.outline()
    if expr == "warm":
        sparkle(cv, c - 4, 38) if False else None
        cv.puts([(c + 4, 37), (c + 5, 38), (c + 4, 39), (c + 3, 38)], SPARK)
        cv.put(c + 4, 38, WHITE)
        sparkle(cv, 57, 12)
    if expr == "concern":
        cv.puts([(c + 18, 18), (c + 17, 19), (c + 18, 19), (c + 19, 19), (c + 17, 20), (c + 18, 20), (c + 19, 20), (c + 18, 21)], SWEAT)
        cv.put(c + 17, 19, SWEAT_HI)
    if expr == "surprised":
        cv.puts([(56, 4), (56, 5), (56, 6), (56, 8), (59, 6), (60, 5), (61, 4)], SPARK2)
    return cv


# ==========================================================================
# previews
# ==========================================================================
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
        if n in ("swoop", "hair", "head", "face"):
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
    ent = entrance()
    img = ent.image()
    assert img.getbbox()[3] == img.height and body_height(ent) == 84
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
        talk.save(os.path.join(cells_dir, "talk", "chad-%d.png" % i))
        cells["talk-%d.png" % i] = talk
    # idle extras for the world front cell (same canvas, same feet)
    base = cells["world-0.png"]
    blink = w_front("blink").image()
    ok, bb = same_except(base, blink, (20, 10, 40, 16))
    assert ok, ("blink changes more than the eyes", bb)
    extras = {"blink": blink, "pose1": w_front("selfie").image(), "pose2": w_front("cards").image()}
    for k, im in extras.items():
        assert im.size == base.size and np.array_equal(np.array(im)[-6:], np.array(base)[-6:]), (k, "feet moved")
        im.save(os.path.join(cells_dir, "idle", "chad-%s.png" % k))
        cells["idle-" + k] = im
    with open(os.path.join(cells_dir, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    contact_sheet(cells)
    return cells, feet


def contact_sheet(cells, S=3):
    """3x sheet: Chad next to the approved cast (cropped straight from the 3x cast reference)."""
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
    os.makedirs(os.path.join(HERE, "prev"), exist_ok=True)
    if len(sys.argv) == 1:
        cells, feet = build()
        for k, v in sorted(feet.items()):
            print(k, cells[k].size, v)
    if len(sys.argv) > 1 and sys.argv[1] == "front":
        ims = [b_front(p).image() for p in ("idle", "talk", "tell", "hit")] + [b_side().image(), b_back().image()]
        preview(ims, os.path.join(HERE, "prev", "front8.png"), S=5)
    if len(sys.argv) > 1 and sys.argv[1] == "head":
        ims = [b_front(p).image().crop((26, 8, 80, 50)) for p in ("idle", "talk", "tell", "hit")]
        preview(ims, os.path.join(HERE, "prev", "head10.png"), S=10)
    if len(sys.argv) > 1 and sys.argv[1] == "sb":
        preview([b_side().image(), b_back().image()], os.path.join(HERE, "prev", "sb8.png"), S=8)
    if len(sys.argv) > 1 and sys.argv[1] == "ent":
        preview([entrance().image()], os.path.join(HERE, "prev", "ent8.png"), S=6)
    if len(sys.argv) > 1 and sys.argv[1] == "world":
        ims = [w_front(p).image() for p in ("idle", "talk", "tell", "hit")] + [w_side().image(), w_back().image()]
        ims += [w_front(p).image() for p in ("blink", "selfie", "cards")]
        preview(ims, os.path.join(HERE, "prev", "world8.png"), S=6)
    if len(sys.argv) > 1 and sys.argv[1] == "port":
        ims = [portrait(e).image() for e in ("neutral", "warm", "concern", "surprised")]
        ims += [portrait(e, talk=True).image() for e in ("neutral", "warm", "concern", "surprised")]
        preview(ims, os.path.join(HERE, "prev", "port8.png"), S=4)
