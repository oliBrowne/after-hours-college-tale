#!/usr/bin/env python3
"""Gwen the Red, seventh-year grad TA (N04 boss, replaces ERRATA) -- procedural pixel-art sprites
for "After Hours - College Tale".

Drawn the way Professor Eric is drawn (tools/eric_art/draw_eric.py, engine copied verbatim): parts
are masks shaded with material ramps from a top-left key light, given inner 1px lines and an ink
silhouette.  Everything is drawn at its final pixel size; nothing drawn is ever resampled (only the
contact sheet and the private 8x previews are nearest-neighbour blow-ups).

Look: copper-red hair scraped into a messy bun with two pencils stabbed through it, tired green eyes
with grad-school bags, freckles, dark red lipstick.  Charcoal turtleneck with a CU-gold lanyard and
TA badge, a crimson tartan skirt, plum tights and black boots with red laces.  Her signature pieces:
a CAPE OF GRADED PAPERS (sheets with blue text lines and red ink marks, fanned up into a standing
collar behind her head), a red ballpoint pen the size of a sword, and a giant to-go coffee.

Outputs (in ./out next to this script):
  battle-0..5.png   82px tall battle cells   (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  entrance.png      cell 12 "ta-entrance", the intro-card pose (wider canvas, pen raised overhead)
  world-0..5.png    52px tall overworld cells (same poses, redrawn small)
  portrait-0..3.png 64x64 portraits          (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk/ta-0..3.png  mouth-open portraits (only mouth pixels differ)
  idle/ta-blink.png, ta-pose1.png (coffee sip), ta-pose2.png (pen on shoulder)   world-front extras
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
    "skin":   [(98, 44, 46), (186, 110, 94), (226, 156, 126), (244, 190, 158), (252, 218, 192)],
    "hair":   [(78, 20, 20), (146, 40, 28), (196, 70, 36), (230, 110, 54), (250, 156, 92)],
    "knit":   [(20, 20, 30), (40, 42, 58), (60, 62, 82), (84, 88, 110), (114, 118, 142)],
    "tartan": [(66, 10, 24), (124, 20, 38), (170, 34, 50), (206, 62, 68), (234, 108, 102)],
    "tights": [(22, 14, 30), (44, 30, 56), (64, 44, 78), (88, 62, 102), (116, 88, 130)],
    "boot":   [(12, 10, 16), (28, 26, 36), (46, 44, 58), (70, 68, 84), (104, 102, 120)],
    "paper":  [(104, 98, 120), (178, 174, 190), (220, 216, 222), (242, 238, 230), (255, 252, 242)],
    "pen":    [(78, 6, 20), (150, 14, 34), (204, 30, 48), (236, 72, 76), (255, 140, 130)],
    "cup":    [(110, 100, 104), (186, 178, 176), (226, 220, 214), (244, 240, 234), (255, 253, 248)],
    "sleeve": [(70, 40, 20), (126, 80, 44), (166, 114, 66), (198, 148, 92), (224, 184, 128)],
    "metal":  [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "gold":   [(92, 62, 18), (160, 116, 36), (206, 166, 64), (236, 204, 104), (252, 236, 160)],
    "grip":   [(14, 14, 20), (30, 30, 40), (48, 48, 62), (70, 70, 88), (98, 98, 118)],
    "wood":   [(96, 56, 24), (178, 120, 60), (220, 166, 96), (240, 200, 136), (252, 228, 180)],
    "pencil": [(120, 80, 10), (196, 146, 24), (238, 192, 48), (252, 222, 96), (255, 242, 170)],
    "belt":   [(30, 18, 14), (58, 36, 26), (84, 54, 38), (112, 76, 52), (140, 102, 72)],
}
EYE = (30, 22, 30)
IRIS = (58, 124, 84)        # green eyes
WHITE = (250, 248, 244)
SCLERA = (240, 236, 230)
MOUTH = (110, 22, 36)       # dark red lipstick
LIP = (176, 44, 58)
LIP_HI = (214, 92, 96)
TONGUE = (196, 92, 96)
TEETH = (248, 244, 236)
BAG = (176, 120, 132)       # tired under-eye bags (mauve)
FRECKLE = (196, 116, 86)
BLUSH = (232, 132, 118)
REDINK = (214, 22, 40)      # grading ink
REDINK2 = (150, 12, 28)
TEXT = (146, 158, 196)      # blue-grey handwriting lines on the papers
TEXT2 = (118, 130, 170)
COFFEE = (88, 50, 30)
COFFEE_HI = (140, 92, 56)
STEAM = (196, 200, 220)
STEAM2 = (160, 166, 192)
LACE = (220, 40, 52)
STITCH = (232, 198, 76)     # yellow welt stitching on the boots
ERASER = (236, 140, 150)
GRAPHITE = (52, 50, 60)
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
GLYPHS = {
    # red-ink grading marks, in sheet-local pixels (u right, v down)
    "check": [(0, 0), (1, 1), (2, 0), (3, -1), (4, -2)],
    "x":     [(0, 0), (2, 0), (1, 1), (0, 2), (2, 2)],
    "F":     [(0, 0), (1, 0), (2, 0), (0, 1), (0, 2), (1, 2), (0, 3)],
    "circ":  [(1, 0), (2, 0), (0, 1), (3, 1), (1, 2), (2, 2)],
    "plus":  [(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)],
    "minus": [(0, 0), (1, 0), (2, 0)],
    "squig": [(0, 0), (1, 1), (2, 0), (3, 1), (4, 0)],
    "A+":    [(1, 0), (0, 1), (2, 1), (0, 2), (1, 2), (2, 2), (0, 3), (2, 3), (4, 1), (3, 2), (4, 2), (5, 2), (4, 3)],
    "C-":    [(1, 0), (2, 0), (0, 1), (0, 2), (1, 3), (2, 3), (4, 2), (5, 2)],
    "?":     [(0, 0), (1, 0), (2, 1), (1, 2), (1, 4)],
    "tick":  [(0, 0), (1, 1), (2, 0), (3, -1)],
    "dash":  [(0, 0), (1, 0)],
    "dot":   [(0, 0)],
}


def paper(cv, name, x, y, w, h, ang, mark="check", lines=True, seed=0, mark_at=None, small=False, step=2):
    """One graded sheet: a rotated rectangle of paper with blue handwriting lines and a red mark.
    (x, y) is the sheet centre, ang its rotation in radians (clockwise on screen)."""
    ca, sa = math.cos(ang), math.sin(ang)
    dx, dy = cv.X - x, cv.Y - y
    u = dx * ca + dy * sa
    v = -dx * sa + dy * ca
    m = (np.abs(u) <= w / 2) & (np.abs(v) <= h / 2)
    if not m.any():
        return m
    lv = np.where(m, 3, 0)
    lv = np.where(m & (v > h / 2 - 2.2), 2, lv)                    # lower edge curls into shade
    lv = np.where(m & (u < -w / 2 + 1.2) & (v < h / 2 - 2), 4, lv)  # lit left edge
    cv.part(name, m, "paper", edge="dark", lv=lv)
    pid = cv.names[name]
    rng = np.random.default_rng(seed)
    if lines:
        # handwriting: clean Bresenham strokes along the sheet's own rows, each split by one gap
        v0 = -h / 2 + (2 if small else 2.5)
        k = 0
        while v0 + k * step < h / 2 - 1.5:
            vv = v0 + k * step
            gap = rng.uniform(-w / 2 + 2, w / 2 - 2)
            ua, ub = -w / 2 + 1.5, w / 2 - 1.5
            for (s0, s1) in ((ua, gap - 1), (gap + 1, ub)):
                if s1 - s0 < 0.5:
                    continue
                x0_, y0_ = x + s0 * ca - vv * sa, y + s0 * sa + vv * ca
                x1_, y1_ = x + s1 * ca - vv * sa, y + s1 * sa + vv * ca
                X0, Y0, X1, Y1 = int(round(x0_)), int(round(y0_)), int(round(x1_)), int(round(y1_))
                n = max(abs(X1 - X0), abs(Y1 - Y0), 1)
                for j in range(n + 1):
                    px_ = int(round(X0 + (X1 - X0) * j / n)); py_ = int(round(Y0 + (Y1 - Y0) * j / n))
                    if 0 <= px_ < cv.w and 0 <= py_ < cv.h and cv.own[py_, px_] == pid and tuple(cv.col[py_, px_]) != RAMP["paper"][0]:
                        cv.col[py_, px_] = TEXT if k % 2 == 0 else TEXT2
            k += 1
    if mark:
        gu, gv = mark_at if mark_at else (w / 2 - 5.5, -h / 2 + 1.5)
        for (a, b) in GLYPHS[mark]:
            px = x + (gu + a) * ca - (gv + b) * sa
            py = y + (gu + a) * sa + (gv + b) * ca
            ix, iy = int(round(px)), int(round(py))
            if 0 <= ix < cv.w and 0 <= iy < cv.h and cv.own[iy, ix] == pid:
                cur = tuple(cv.col[iy, ix])
                if cur != RAMP["paper"][0]:
                    cv.col[iy, ix] = REDINK
    return m


def pen(cv, x0, y0, x1, y1, name="pen", r=2.4, small=False):
    """The giant red ballpoint, from the cap end (x0, y0) to the nib tip (x1, y1): rounded cap with a
    silver clip, gold band, red barrel with a long highlight, ribbed black grip, silver cone, red tip."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    nx, ny = -uy, ux
    P = lambda k: (x0 + ux * k, y0 + uy * k)
    s = (cv.X - x0) * ux + (cv.Y - y0) * uy           # arc position along the pen
    q = (cv.X - x0) * nx + (cv.Y - y0) * ny           # signed offset across the pen
    cone_len = 3.0 if small else 4.5
    grip_len = 4.0 if small else 8.0
    a, b = P(0), P(L - cone_len)
    body = cv.capsule(a[0], a[1], b[0], b[1], r)
    cone = cv.capsule(b[0], b[1], x1, y1, r * 0.85, 0.5) & (s >= L - cone_len - 0.5)
    m = body | cone
    # light comes from the upper left: the side of the pen facing it is lit
    lit_sign = 1 if (nx * -0.55 + ny * -0.75) > 0 else -1
    lv = np.where(m, 2, 0)
    lv = np.where(m & (q * lit_sign > r * 0.25), 3, lv)
    lv = np.where(m & (q * lit_sign > r * 0.25) & (q * lit_sign < r * 0.25 + 1.0), 4, lv)
    lv = np.where(m & (q * lit_sign < -r * 0.45), 1, lv)
    cv.part(name, m, "pen", edge="dark" if small else "ink", lv=lv)
    edgec = RAMP["pen"][0] if small else INK
    isink = (cv.col[..., 0] == edgec[0]) & (cv.col[..., 1] == edgec[1]) & (cv.col[..., 2] == edgec[2])
    inner = m & ~isink
    # cap: darker red end
    capm = inner & (s < (5 if small else 9))
    cv.col[capm] = np.array(RAMP["pen"])[np.clip(lv[capm] - 1, 0, 4)]
    # gold band where the cap meets the barrel
    band = inner & (s >= (5 if small else 9)) & (s < (6 if small else 11))
    cv.col[band] = np.array(RAMP["gold"])[np.clip(lv[band], 0, 4)]
    # ribbed grip
    gm = inner & (s >= L - cone_len - grip_len) & (s < L - cone_len)
    rib = (np.floor(s) % 2 == 0)
    cv.col[gm] = np.array(RAMP["grip"])[np.clip(lv[gm] + np.where(rib[gm], 1, 0), 0, 4)]
    # silver cone
    cm = inner & (s >= L - cone_len)
    cv.col[cm] = np.array(RAMP["metal"])[np.clip(lv[cm], 0, 4)]
    # red ink tip
    cv.put(x1, y1, REDINK)
    # silver clip along the lit side of the cap
    if not small:
        for k in range(1, 9):
            px, py = P(k)
            cv.put(px + nx * lit_sign * (r - 0.2), py + ny * lit_sign * (r - 0.2), RAMP["metal"][3 if k < 3 else 2])
        px, py = P(8.5)
        cv.put(px + nx * lit_sign * (r - 0.2), py + ny * lit_sign * (r - 0.2), RAMP["metal"][1])
    else:
        for k in range(1, 4):
            px, py = P(k)
            cv.put(px + nx * lit_sign * (r - 0.3), py + ny * lit_sign * (r - 0.3), RAMP["metal"][3])
    return m


def cup(cv, x, y, name="cup", small=False, tilt=0.0, splash=False):
    """Giant to-go coffee. (x, y) is the centre of the top of the lid."""
    if small:
        wt, wb, hgt = 3.0, 2.4, 8
    else:
        wt, wb, hgt = 4.2, 3.2, 13
    ca, sa = math.cos(tilt), math.sin(tilt)
    def R(px, py):
        return (x + px * ca - py * sa, y + px * sa + py * ca)
    body = cv.poly([R(-wt, 1.5), R(wt, 1.5), R(wb, hgt), R(-wb, hgt)])
    lvb = cv.levels(body, rad=2.5, soft=0.6, cuts=(0.2, 0.45, 0.85))
    cv.part(name, body, "cup", edge="dark", lv=lvb)
    # kraft sleeve around the middle
    sl0, sl1 = (3, 6) if small else (5, 10)
    sleeve = cv.poly([R(-wt - 0.3, sl0), R(wt + 0.3, sl0), R(wb + 0.6, sl1), R(-wb - 0.6, sl1)]) & body
    cv.part(name + "sleeve", sleeve, "sleeve", edge="dark", noedge=(name,), lv=cv.levels(sleeve, rad=2, soft=0.5))
    if not small:
        # a tiny red heart stamped on the sleeve
        hx, hy = R(0, (sl0 + sl1) / 2)
        cv.puts([(hx - 1, hy - 1), (hx + 1, hy - 1), (hx - 1, hy), (hx, hy), (hx + 1, hy), (hx, hy + 1)], REDINK)
    # lid: wider, with a sip-hole bump
    lid = cv.poly([R(-wt - 1, 0), R(wt + 1, 0), R(wt + 1, 2), R(-wt - 1, 2)])
    lid |= cv.poly([R(-wt + 0.5, -1.5), R(wt - 0.5, -1.5), R(wt, 0), R(-wt, 0)])
    lvl = np.where(lid, 3, 0)
    cv.part(name + "lid", lid, "cup", edge="ink", lv=lvl)
    px, py = R(-wt + 1.5, -1)
    cv.put(px, py, RAMP["cup"][4])
    px, py = R(wt - 1.5, -1)
    cv.put(px, py, RAMP["cup"][1])
    if splash:
        pass
    return body | lid


def steam(cv, x, y, n=2, small=False):
    """Two thin wisps rising from the lid (drawn after the outline so they stay soft)."""
    if small:
        pts = [(x - 1, y - 1), (x, y - 2), (x - 1, y - 3), (x + 2, y - 2), (x + 2, y - 4)]
        for p in pts:
            cv.put(p[0], p[1], STEAM2)
        return
    w1 = [(x - 1, y - 2), (x - 2, y - 3), (x - 2, y - 4), (x - 1, y - 5), (x - 1, y - 6), (x - 2, y - 7)]
    w2 = [(x + 2, y - 2), (x + 3, y - 3), (x + 3, y - 4), (x + 2, y - 5), (x + 2, y - 6)]
    for i, p in enumerate(w1):
        cv.put(p[0], p[1], STEAM if i < 4 else STEAM2)
    if n > 1:
        for i, p in enumerate(w2):
            cv.put(p[0], p[1], STEAM2 if i < 3 else STEAM)


def pencil(cv, x0, y0, x1, y1, name, r=1.2):
    """Yellow pencil from the eraser end (x0, y0) to the sharpened tip (x1, y1)."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    s = (cv.X - x0) * ux + (cv.Y - y0) * uy
    m = cv.capsule(x0, y0, x1 - ux * 2, y1 - uy * 2, r) | (cv.capsule(x1 - ux * 2.5, y1 - uy * 2.5, x1, y1, r, 0.4))
    lv = np.where(m, 3, 0)
    cv.part(name, m, "pencil", edge="dark", lv=lv)
    e0 = RAMP["pencil"][0]
    isink = (cv.col[..., 0] == e0[0]) & (cv.col[..., 1] == e0[1]) & (cv.col[..., 2] == e0[2])
    inner = m & ~isink
    cv.col[inner & (s < 1.6)] = ERASER
    cv.col[inner & (s >= 1.6) & (s < 2.6)] = RAMP["metal"][2]
    cv.col[inner & (s >= L - 3)] = RAMP["wood"][2]
    cv.put(x1, y1, GRAPHITE)


def w_pencil(cv, x0, y0, x1, y1):
    """World-size pencil: a 1px yellow line with a pink eraser and a graphite point, no outline."""
    L = max(abs(x1 - x0), abs(y1 - y0))
    for k in range(L + 1):
        x = round(x0 + (x1 - x0) * k / L)
        y = round(y0 + (y1 - y0) * k / L)
        cv.put(x, y, ERASER if k == 0 else GRAPHITE if k == L else RAMP["wood"][2] if k == L - 1 else RAMP["pencil"][2 if k % 3 else 3])


def mark_dots(cv, pts, c):
    for p in pts:
        cv.put(p[0], p[1], c)


def assert_feet(img, name):
    bb = img.getbbox()
    assert bb[3] == img.height, (name, "feet not on bottom row", bb)


# ==========================================================================
# BATTLE  (82 px standing height, bun top to boot soles)
# ==========================================================================
BW, BH = 96, 90
BODY_H = 82
BT = BH - BODY_H


def b_cape_collar(cv, c, t, spread=1.0, seed=0):
    """Standing collar of graded papers fanned out behind the head and shoulders."""
    px, py = c, t + 25
    specs = [  # (angle from vertical in degrees, radius, w, h, mark)
        (40, 13.0, 7, 10, None), (64, 13.5, 7, 10, "check"), (88, 12.5, 7, 9, None),
    ]
    k = 0
    for s in (-1, 1):
        for (deg, rad, w, h, mk) in specs:
            a = math.radians(deg * spread) * s
            cx_, cy_ = px + math.sin(a) * rad, py - math.cos(a) * rad
            paper(cv, "col%d%d" % (s, k), cx_, cy_, w, h, a, mark=mk if s < 0 or mk is None else "x",
                  seed=seed + k, small=True, mark_at=(-1.5, -h / 2 + 2))
            k += 1


CAPE_MARKS = ["check", None, "F", None, "circ", "A+", None, "x", "C-", None]


def b_cape_back(cv, c, t, flare=0.0, seed=10, drop=0):
    """The cape: a crimson cloak flaring from the shoulders, shingled with graded sheets."""
    fl = flare * 4
    cloak = cv.poly([(c - 10, t + 24), (c + 10, t + 24), (c + 16, t + 34), (c + 22 + fl, t + 64 + drop),
                     (c + 16 + fl, t + 68 + drop), (c, t + 66 + drop), (c - 16 - fl, t + 68 + drop),
                     (c - 22 - fl, t + 64 + drop), (c - 16, t + 34)])
    cv.part("cloak", cloak, "pen", rad=6, soft=1.2, cuts=(0.45, 0.75, 0.95), bias=-0.25)
    k = 0
    for row in range(5):
        y = t + 31 + row * 7.6 + drop
        for s in (-1, 1):
            x = c + s * (14.5 + row * (1.6 + flare * 1.2))
            ang = s * (0.06 + 0.035 * row + flare * 0.10) + (0.05 if (row + (s > 0)) % 2 else -0.04)
            paper(cv, "cape%d" % k, x, y, 9, 11, ang, mark=CAPE_MARKS[k % len(CAPE_MARKS)], seed=seed + k,
                  mark_at=(s * 0.5 - 0.5, -2.5))
            k += 1


def b_legs(cv, c, t, stance=0):
    """Tights + chunky black boots with red laces and yellow welt stitching."""
    for s in (-1, 1):
        x_top, x_bot = c + s * 4.5, c + s * (5.5 + stance)
        leg = cv.capsule(x_top, t + 55, x_bot, t + 72, 2.9, 2.4)
        cv.part("leg%d" % s, leg, "tights", rad=3, soft=0.8, cuts=(0.30, 0.55, 0.88))
    tr = RAMP["tights"]
    cv.vline(c - 4, t + 60, t + 70, tr[3])
    for s in (-1, 1):
        bx = c + s * (5.5 + stance)
        shaft = cv.rect(bx - 3.5, t + 70, bx + 3.5, t + 78)
        toe = cv.ell(bx + s * 0.8, t + 78.6, 4.9, 3.2) & cv.half(y=t + 81, below=False)
        cv.part("shoe%d" % s, shaft | toe, "boot", rad=3, soft=0.8, cuts=(0.32, 0.58, 0.9))
        br = RAMP["boot"]
        cv.hline(bx - 3, bx + 3, t + 70, br[3])                     # collar of the boot
        for y in (t + 72, t + 74, t + 76):                            # red laces
            cv.put(bx - 1, y, LACE); cv.put(bx + 1, y, LACE)
            cv.put(bx, y + 1, REDINK2)
        cv.hline(bx - 4 + (s > 0), bx + 4 + (s > 0) * 0, t + 80, STITCH)
        for x in range(int(bx - 4), int(bx + 5)):
            if cv.own[t + 80, x] == cv.names["shoe%d" % s] and x % 2:
                cv.put(x, t + 80, br[1])
        cv.put(bx - 3 + s * 0.8, t + 77, br[4])


def b_skirt(cv, c, t, swing=0):
    sk = cv.poly([(c - 9, t + 42), (c + 9, t + 42), (c + 14 + swing, t + 56), (c + 7, t + 57),
                  (c, t + 56.5), (c - 7, t + 57), (c - 14 + swing, t + 56)])
    cv.part("skirt", sk, "tartan", rad=5, soft=1.0, cuts=(0.30, 0.55, 0.86))
    tr = RAMP["tartan"]
    pid = cv.names["skirt"]
    GREEN, GREEN2 = (30, 52, 44), (22, 36, 32)
    YEL = (214, 172, 70)

    def on(x, y):
        return 0 <= y < cv.h and 0 <= x < cv.w and cv.own[y, x] == pid and cv.get(x, y) != tr[0]
    # horizontal tartan bands
    for y in (t + 47, t + 52):
        for x in range(c - 15, c + 16):
            if on(x, y):
                cv.put(x, y, GREEN)
    for x in range(c - 15, c + 16):
        if on(x, t + 50) and cv.get(x, t + 50) != tr[0]:
            cv.put(x, t + 50, tr[3] if x < c else tr[2])
    # vertical bands fanning out with the pleats
    for k in (-2, -1, 0, 1, 2):
        for y in range(t + 43, t + 57):
            f = (y - (t + 42)) / 14.0
            x = int(round(c + k * (3.6 + 1.6 * f) + swing * f * 0.5))
            if on(x, y):
                cv.put(x, y, GREEN2 if y in (t + 47, t + 52) else GREEN)
    # pleat shadows
    for k in (-1.5, -0.5, 0.5, 1.5):
        for y in range(t + 49, t + 57):
            f = (y - (t + 42)) / 14.0
            x = int(round(c + k * (3.6 + 1.6 * f) + swing * f * 0.5))
            if on(x, y) and cv.get(x, y) not in (GREEN, GREEN2, YEL):
                cv.put(x, y, tr[1])
    # belt with a gold buckle
    belt = cv.rect(c - 9, t + 42, c + 9, t + 43) & cv.poly([(c - 10, t + 41), (c + 10, t + 41), (c + 10, t + 44), (c - 10, t + 44)])
    cv.part("belt", belt, "belt", edge=None, lv=np.where(belt, 2, 0) + np.where(belt & (cv.X < c - 3), 1, 0))
    gd = RAMP["gold"]
    cv.puts([(c - 1, t + 42), (c + 1, t + 42), (c - 1, t + 43), (c + 1, t + 43)], gd[2])
    cv.put(c - 1, t + 42, gd[4]); cv.put(c, t + 42, gd[1]); cv.put(c, t + 43, gd[1])


def b_torso(cv, c, t, lean=0):
    kn = RAMP["knit"]
    torso = cv.poly([(c - 6, t + 23), (c + 6, t + 23), (c + 11, t + 26), (c + 12, t + 30), (c + 9.5, t + 37),
                     (c + 8.5, t + 42), (c - 8.5, t + 42), (c - 9.5, t + 37), (c - 12, t + 30), (c - 11, t + 26)])
    cv.part("torso", torso, "knit", rad=8, soft=1.6, cuts=(0.30, 0.52, 0.84), tex=0.05, seed=5)
    # soft bust / ribbing folds
    for x in range(c - 7, c - 2):
        cv.put(x, t + 33 + (x == c - 7), kn[1])
    for x in range(c + 3, c + 8):
        cv.put(x, t + 33 + (x == c + 7), kn[1])
    for x in range(c - 8, c - 4):
        cv.put(x, t + 30, kn[3])
    # waist rib
    for x in range(c - 8, c + 9, 2):
        cv.put(x, t + 40, kn[1])
    # rolled turtleneck collar
    col = cv.ell(c, t + 22.5, 5.2, 2.8) | cv.rect(c - 4, t + 20, c + 4, t + 22)
    cv.part("collar", col, "knit", rad=3, soft=0.8, bias=0.08)
    cv.hline(c - 3, c + 3, t + 22, kn[1])
    cv.put(c - 3, t + 21, kn[3]); cv.put(c - 2, t + 21, kn[3])


def b_lanyard(cv, c, t):
    gd = RAMP["gold"]
    cv.line(c - 4, t + 24, c - 1, t + 31, gd[2])
    cv.line(c + 4, t + 24, c + 1, t + 31, gd[1])
    # badge
    cv.part("badge", cv.rect(c - 2, t + 32, c + 2, t + 37), "paper", edge="ink", lv=np.where(cv.rect(c - 2, t + 32, c + 2, t + 37), 3, 0))
    cv.hline(c - 1, c + 1, t + 33, REDINK)            # red header strip
    cv.put(c - 1, t + 35, (120, 84, 70)); cv.put(c, t + 35, TEXT); cv.put(c + 1, t + 35, TEXT)
    cv.put(c, t + 31, RAMP["metal"][2])


def b_arm(cv, name, pts, r=2.7):
    m = cv.chain(pts, r)
    cv.part(name, m, "knit", edge="dark", rad=3, soft=0.9, cuts=(0.30, 0.55, 0.88), tex=0.05,
            seed=len(name) * 7 + int(pts[0][0]))
    return m


def b_hand(cv, x, y, name, rx=2.6, ry=2.6, fist=True):
    m = cv.ell(x, y, rx, ry)
    cv.part(name, m, "skin", edge="ink", rad=2.5, soft=0.7, bias=0.05)
    if fist:
        cv.put(x + 1, y + 1, RAMP["skin"][1])
    return m


def b_face(cv, c, t, pose):
    """Face, hair, bun and pencils (front view). t = bun top."""
    sk, hr = RAMP["skin"], RAMP["hair"]
    # pencils stabbed through the bun (behind it)
    pencil(cv, c - 9, t + 2, c + 10, t + 7, "pencilA")
    pencil(cv, c + 8, t + 1, c - 4, t + 8, "pencilB")
    bun = cv.ell(c + 1, t + 4.2, 5.4, 4.2)
    cv.part("bun", bun, "hair", rad=4, soft=0.8, cuts=(0.28, 0.52, 0.84), tex=0.08, seed=61)
    cv.line(c - 2, t + 3, c + 3, t + 6, hr[1]); cv.line(c, t + 2, c + 4, t + 4, hr[1])
    # back hair mass + face-framing locks behind the face
    back = cv.ell(c, t + 13.5, 9.6, 8.8) | cv.capsule(c - 8, t + 13, c - 8.6, t + 22, 2.3) | cv.capsule(c + 8, t + 13, c + 8.8, t + 22, 2.3)
    cv.part("hairback", back, "hair", rad=5, soft=1.0, cuts=(0.30, 0.56, 0.86), tex=0.06, seed=63)
    # neck (mostly hidden by the turtleneck)
    cv.part("neck", cv.rect(c - 2.5, t + 19, c + 2.5, t + 23), "skin", rad=2, bias=-0.15)
    face = cv.ell(c, t + 13.2, 7.4, 7.2) | cv.ell(c, t + 16, 6.2, 6.9)
    cv.part("face", face, "skin", rad=6, soft=1.4, cuts=(0.22, 0.48, 0.86), bias=0.06)
    # front hair: side-swept fringe from her right (viewer left) across the brow
    fr = cv.ell(c, t + 12.4, 8.6, 7.8)
    line = t + 9.0 + 0.30 * (cv.X - c) + np.where(((cv.X - c) % 4) == 1, 1.2, 0) + np.where(cv.X > c + 3, 0.8, 0)
    fringe = fr & (cv.Y < line)
    fringe |= cv.capsule(c - 7.6, t + 9, c - 8.0, t + 20, 1.6) | cv.capsule(c + 7.4, t + 10, c + 8.0, t + 21, 1.5)
    cv.part("fringe", fringe, "hair", noedge=("hairback", "bun"), rad=4, soft=0.9, cuts=(0.28, 0.54, 0.86), tex=0.05, seed=67)
    for (x0, y0, x1, y1) in [(c - 5, t + 7, c - 2, t + 11), (c + 1, t + 7, c + 4, t + 12), (c - 7, t + 11, c - 7, t + 16)]:
        cv.line(x0, y0, x1, y1, hr[1])
    cv.puts([(c - 4, t + 6), (c - 3, t + 6), (c - 5, t + 7)], hr[4])
    # forehead shadow under the fringe
    for x in range(c - 6, c + 7):
        for y in range(t + 8, t + 16):
            if cv.own[y, x] == cv.names["face"] and cv.own[y - 1, x] == cv.names["fringe"]:
                cv.put(x, y, sk[1] if x > c - 3 else sk[2])
                break
    # flyaway strands (messy seventh-year bun)
    cv.puts([(c - 8, t + 4), (c - 9, t + 3), (c + 9, t + 5), (c + 10, t + 4)], hr[1])
    b_expr(cv, c, t, pose)


def b_expr(cv, c, t, pose):
    sk = RAMP["skin"]
    hr = RAMP["hair"]
    ey = t + 13
    # freckles
    for (x, y) in [(c - 5, t + 17), (c - 4, t + 18), (c - 6, t + 18), (c + 5, t + 17), (c + 4, t + 18), (c + 6, t + 18)]:
        cv.put(x, y, FRECKLE)
    cv.put(c - 5, t + 18, BLUSH); cv.put(c + 5, t + 18, BLUSH)
    # nose
    cv.put(c, t + 17, sk[1]); cv.put(c - 1, t + 16, sk[3]); cv.put(c + 1, t + 17, sk[1])
    for side in (-1, 1):
        x0 = c - 5 if side < 0 else c + 2       # left pixel of the 4-wide eye cell
        if pose in ("idle", "talk"):
            # heavy half-lid, 2x2 eye with green iris + catch-light, mauve bags
            cv.hline(x0, x0 + 3, ey, EYE)
            cv.put(x0 if side < 0 else x0 + 3, ey + 1, EYE)
            cv.put(x0 + 1, ey + 1, EYE); cv.put(x0 + 2, ey + 1, IRIS)
            cv.put(x0 + 1, ey + 2, EYE); cv.put(x0 + 2, ey + 2, EYE)
            cv.put(x0 + 1, ey + 1, WHITE if side < 0 else EYE)
            if side > 0:
                cv.put(x0 + 1, ey + 1, WHITE)
            cv.hline(x0 + 1, x0 + 2, ey + 3, BAG)
        elif pose == "tell":
            # narrowed, scheming
            cv.hline(x0, x0 + 3, ey + 1, EYE)
            cv.put(x0 + 1, ey + 2, IRIS); cv.put(x0 + 2, ey + 2, EYE)
            cv.hline(x0 + 1, x0 + 2, ey + 3, BAG)
        elif pose == "hit":
            m = ["K...", ".KK.", "K..."] if side < 0 else ["...K", ".KK.", "...K"]
            for j, row in enumerate(m):
                for i, ch in enumerate(row):
                    if ch == "K":
                        cv.put(x0 + i, ey + j, EYE)
    # brows: thin copper; the viewer-right one cocked up (skeptical grader)
    if pose == "hit":
        cv.puts([(c - 5, t + 11), (c - 4, t + 10), (c - 3, t + 10), (c - 2, t + 11)], hr[1])
        cv.puts([(c + 5, t + 11), (c + 4, t + 10), (c + 3, t + 10), (c + 2, t + 11)], hr[1])
    elif pose == "tell":
        cv.puts([(c - 5, t + 11), (c - 4, t + 11), (c - 3, t + 12), (c - 2, t + 12)], hr[0])
        cv.puts([(c + 5, t + 11), (c + 4, t + 11), (c + 3, t + 12), (c + 2, t + 12)], hr[0])
    else:
        cv.puts([(c - 5, t + 11), (c - 4, t + 11), (c - 3, t + 11), (c - 2, t + 12)], hr[1])
        cv.puts([(c + 2, t + 11), (c + 3, t + 10), (c + 4, t + 10), (c + 5, t + 11)], hr[1])
    # mouth (dark red lipstick)
    y = t + 20
    if pose == "idle":
        cv.hline(c - 2, c + 1, y, MOUTH); cv.put(c + 2, y - 1, MOUTH)
        cv.hline(c - 1, c, y + 1, LIP)
    elif pose == "talk":
        cv.hline(c - 2, c + 2, y - 1, MOUTH)
        cv.hline(c - 1, c + 1, y, MOUTH); cv.put(c, y, TONGUE)
        cv.hline(c - 1, c + 1, y + 1, LIP)
    elif pose == "tell":
        cv.hline(c - 2, c + 2, y, MOUTH); cv.put(c + 3, y - 1, MOUTH); cv.put(c - 3, y - 1, MOUTH)
        cv.hline(c - 1, c + 1, y, TEETH)
        cv.hline(c - 1, c + 1, y + 1, LIP)
    elif pose == "hit":
        cv.hline(c - 2, c + 2, y - 1, MOUTH); cv.hline(c - 2, c + 2, y, MOUTH)
        cv.put(c - 1, y - 1, TEETH); cv.put(c + 1, y - 1, TEETH)
        cv.hline(c - 1, c + 1, y + 1, LIP)


def b_front(pose):
    cv = Cv(BW, BH)
    c, t = 48, BT
    hx = 2 if pose == "hit" else 0
    # ---- cape (behind everything) ----
    b_cape_collar(cv, c + hx // 2, t, spread=1.08 if pose == "hit" else 1.0, seed=3)
    b_cape_back(cv, c, t, flare=0.4 if pose in ("tell", "hit") else 0.0)
    # ---- pen behind the body in the tell pose ----
    # ---- legs, skirt, torso ----
    b_legs(cv, c, t)
    b_skirt(cv, c, t)
    b_torso(cv, c, t)
    b_lanyard(cv, c, t)
    # ---- viewer-left arm: the pen ----
    if pose in ("idle", "talk"):
        b_arm(cv, "armL", [(c - 10, t + 26), (c - 13, t + 32), (c - 15, t + 37)])
        pen(cv, c - 16, t + 34, c - 20, t + 81)
        b_hand(cv, c - 16, t + 39, "handL")
    elif pose == "tell":
        pen(cv, c - 11, t + 40, c - 34, t + 4)
        b_arm(cv, "armL", [(c - 10, t + 26), (c - 16, t + 30), (c - 17, t + 25)])
        b_hand(cv, c - 16.5, t + 26, "handL")
    elif pose == "hit":
        b_arm(cv, "armL", [(c - 10, t + 26), (c - 16, t + 30), (c - 20, t + 27)])
        pen(cv, c - 13, t + 40, c - 30, t + 8)
        b_hand(cv, c - 20, t + 27, "handL")
    # ---- viewer-right arm: the coffee ----
    if pose in ("idle", "tell"):
        b_arm(cv, "armR", [(c + 10, t + 26), (c + 13, t + 32), (c + 14, t + 37)])
        cup(cv, c + 15, t + 29)
        b_hand(cv, c + 14, t + 38, "handR", rx=2.4)
    elif pose == "talk":
        b_arm(cv, "armR", [(c + 10, t + 26), (c + 16, t + 30), (c + 18, t + 24)])
        cup(cv, c + 19, t + 14)
        b_hand(cv, c + 18.5, t + 23, "handR", rx=2.4)
    elif pose == "hit":
        b_arm(cv, "armR", [(c + 10, t + 26), (c + 16, t + 29), (c + 21, t + 26)])
        cup(cv, c + 24, t + 15, tilt=0.55)
        b_hand(cv, c + 21.5, t + 25, "handR", rx=2.4)
    # ---- head ----
    b_face(cv, c + hx, t, pose)
    if pose == "hit":
        # sheets knocked loose from the cape
        paper(cv, "loose0", c + 30, t + 40, 7, 9, 0.7, mark="F", seed=91, small=True, mark_at=(-1.5, -2.5))
        paper(cv, "loose1", c - 29, t + 50, 7, 9, -0.5, mark="x", seed=92, small=True, mark_at=(-1.5, -2.5))
    cv.outline()
    # soft extras after the outline
    if pose in ("idle", "tell"):
        steam(cv, c + 15, t + 27)
    elif pose == "talk":
        steam(cv, c + 19, t + 12)
    if pose == "hit":
        # coffee sloshing out of the tipped cup
        cv.puts([(c + 28, t + 12), (c + 29, t + 11), (c + 30, t + 13), (c + 31, t + 15), (c + 29, t + 15)], COFFEE)
        cv.put(c + 29, t + 11, COFFEE_HI)
        sx, sy = c + 10, t + 3
        cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx + 1, sy + 1), (sx, sy + 2)], SWEAT)
        cv.put(sx - 1, sy + 1, SWEAT_HI)
    if pose == "tell":
        # glint on the nib + a drop of red ink
        sx, sy = c - 34, t + 4
        cv.puts([(sx - 2, sy), (sx + 2, sy), (sx, sy - 2), (sx, sy + 2), (sx - 1, sy), (sx + 1, sy), (sx, sy - 1), (sx, sy + 1)], SPARK2)
        cv.put(sx, sy, WHITE)
        cv.puts([(c - 36, t + 9), (c - 36, t + 10)], REDINK)
    return cv


def b_side():
    """Side view facing RIGHT: cape trailing behind, pen slung across her back, coffee in front."""
    cv = Cv(BW, BH)
    c, t = 46, BT
    sk, hr, kn = RAMP["skin"], RAMP["hair"], RAMP["knit"]
    # ---- collar sheets fanned behind the head (back side only) ----
    px, py = c - 2, t + 25
    for k, (deg, rad, mk) in enumerate(((-28, 13.0, None), (-52, 13.5, "check"), (-76, 13.0, None), (-100, 12.0, "x"))):
        a = math.radians(deg)
        paper(cv, "col%d" % k, px + math.sin(a) * rad, py - math.cos(a) * rad, 7, 10, a, mark=mk, seed=40 + k,
              small=True, mark_at=(-1.5, -3))
    # ---- cloak trailing back ----
    cloak = cv.poly([(c - 6, t + 24), (c + 1, t + 25), (c - 1, t + 40), (c - 4, t + 66), (c - 14, t + 68),
                     (c - 22, t + 64), (c - 14, t + 34)])
    cv.part("cloak", cloak, "pen", rad=6, soft=1.2, cuts=(0.45, 0.75, 0.95), bias=-0.25)
    for k, (x, y, ang, mk) in enumerate(((c - 11, t + 31, -0.12, None), (c - 13, t + 39, -0.18, "F"),
                                         (c - 15, t + 47, -0.12, None), (c - 17, t + 55, -0.22, "A+"),
                                         (c - 18, t + 62, -0.16, "circ"), (c - 8, t + 60, 0.08, None))):
        paper(cv, "cape%d" % k, x, y, 9, 11, ang, mark=mk, seed=50 + k, mark_at=(-1, -2.5))
    # ---- pen slung diagonally across the back ----
    pen(cv, c - 13, t + 18, c - 1, t + 70)
    # ---- legs + boots (back leg first) ----
    for k, (lx, name) in enumerate(((c - 3, "legB"), (c + 1, "legF"))):
        cv.part(name, cv.capsule(lx, t + 55, lx + (1 if k else -1), t + 72, 2.9, 2.4), "tights", rad=3,
                cuts=(0.30, 0.55, 0.88) if k else (0.45, 0.7, 0.95))
        bx = lx + (1 if k else -1)
        boot = cv.rect(bx - 3, t + 70, bx + 3, t + 78) | (cv.ell(bx + 2.5, t + 78.6, 5.6, 3.2) & cv.half(y=t + 81, below=False))
        cv.part("shoe" + name[-1], boot, "boot", rad=3, soft=0.8, cuts=(0.32, 0.58, 0.9) if k else (0.45, 0.7, 0.95))
        br = RAMP["boot"]
        cv.hline(bx - 2, bx + 7, t + 80, STITCH)
        for x in range(int(bx - 3), int(bx + 8)):
            if x % 2:
                cv.put(x, t + 80, br[1])
        if k:
            for y in (t + 72, t + 74, t + 76):
                cv.put(bx + 2, y, LACE)
            cv.put(bx + 5, t + 77, br[4]); cv.hline(bx - 2, bx + 2, t + 70, br[3])
    # ---- skirt ----
    skm = cv.poly([(c - 7, t + 42), (c + 6, t + 42), (c + 10, t + 56), (c + 3, t + 57), (c - 5, t + 56.5), (c - 12, t + 56)])
    cv.part("skirt", skm, "tartan", rad=5, soft=1.0, cuts=(0.30, 0.55, 0.86))
    tr = RAMP["tartan"]
    pid = cv.names["skirt"]
    for y in (t + 47, t + 52):
        for x in range(c - 13, c + 11):
            if cv.own[y, x] == pid and cv.get(x, y) != tr[0]:
                cv.put(x, y, (30, 52, 44))
    for k in (-2, -1, 0, 1):
        for y in range(t + 43, t + 57):
            f = (y - (t + 42)) / 14.0
            x = int(round(c - 1 + k * (3.4 + 1.4 * f)))
            if cv.own[y, x] == pid and cv.get(x, y) != tr[0]:
                cv.put(x, y, (22, 36, 32) if y in (t + 47, t + 52) else (30, 52, 44))
    belt = cv.rect(c - 7, t + 42, c + 6, t + 43)
    cv.part("belt", belt, "belt", edge=None, lv=np.where(belt, 2, 0))
    # ---- torso (profile) ----
    torso = cv.poly([(c - 5, t + 23), (c + 3, t + 23), (c + 6, t + 27), (c + 7, t + 31), (c + 5, t + 37),
                     (c + 5, t + 42), (c - 7, t + 42), (c - 6, t + 36), (c - 7, t + 29)])
    cv.part("torso", torso, "knit", rad=7, soft=1.4, cuts=(0.30, 0.52, 0.84), tex=0.05, seed=15)
    for y in range(t + 31, t + 35):
        cv.put(c + 5, y, kn[1])
    gd = RAMP["gold"]
    cv.line(c + 2, t + 24, c + 5, t + 31, gd[2])
    cv.part("badge", cv.rect(c + 5, t + 31, c + 7, t + 35), "paper", edge="ink", lv=np.where(cv.rect(c + 5, t + 31, c + 7, t + 35), 3, 0))
    cv.put(c + 6, t + 32, REDINK)
    col = cv.ell(c - 0.5, t + 22.5, 4.6, 2.8) | cv.rect(c - 3, t + 20, c + 3, t + 22)
    cv.part("collar", col, "knit", rad=3, bias=0.08)
    # ---- near arm with the coffee ----
    b_arm(cv, "arm", [(c - 1, t + 26), (c + 0, t + 33), (c + 6, t + 36)])
    cup(cv, c + 9, t + 28)
    b_hand(cv, c + 7.5, t + 36, "hand", rx=2.4)
    # ---- head (profile) ----
    pencil(cv, c - 13, t + 1, c + 2, t + 8, "pencilA")
    pencil(cv, c - 1, t + 1, c - 11, t + 9, "pencilB")
    bun = cv.ell(c - 6, t + 5, 5.0, 4.4)
    cv.part("bun", bun, "hair", rad=4, soft=0.8, cuts=(0.28, 0.52, 0.84), tex=0.08, seed=61)
    cv.line(c - 9, t + 4, c - 4, t + 7, hr[1])
    cv.part("neck", cv.rect(c - 2, t + 18, c + 2, t + 23), "skin", rad=2, bias=-0.15)
    head = cv.ell(c + 1, t + 13.4, 7.2, 7.4) | cv.ell(c + 3, t + 16, 5.0, 6.6) | cv.ell(c + 4.6, t + 19.5, 3.4, 3.0)
    cv.part("head", head, "skin", rad=6, soft=1.4, cuts=(0.22, 0.48, 0.86), bias=0.10)
    cv.part("nose", cv.ell(c + 9.0, t + 15.8, 1.7, 1.6), "skin", edge="ink", noedge=("head",), lv=None, rad=1.5, bias=0.15)
    hair = cv.ell(c, t + 12.3, 8.2, 7.8)
    hair &= (cv.X < c + 1) | (cv.Y < t + 8.5 + 0.35 * (cv.X - c))
    hair |= cv.capsule(c - 6.5, t + 11, c - 6.0, t + 20, 2.0)
    cv.part("hair", hair, "hair", noedge=("bun",), rad=5, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.06, seed=69)
    cv.line(c - 4, t + 7, c + 3, t + 9, hr[1]); cv.line(c - 6, t + 10, c - 3, t + 17, hr[1])
    cv.puts([(c - 1, t + 6), (c, t + 6), (c + 1, t + 6)], hr[4])
    # ear tucked under the side lock
    cv.part("ear", cv.ell(c + 0.5, t + 15, 1.4, 2.0), "skin", edge="dark", bias=0.05)
    # eye, brow, bag, freckles, lips
    cv.hline(c + 4, c + 6, t + 13, EYE)
    cv.put(c + 5, t + 14, EYE); cv.put(c + 6, t + 14, IRIS); cv.put(c + 5, t + 15, EYE)
    cv.put(c + 5, t + 16, BAG)
    cv.hline(c + 4, c + 6, t + 11, hr[1])
    cv.puts([(c + 4, t + 17), (c + 6, t + 18)], FRECKLE)
    cv.put(c + 7, t + 20, MOUTH); cv.put(c + 6, t + 20, MOUTH); cv.put(c + 7, t + 19, LIP); cv.put(c + 7, t + 21, LIP)
    cv.put(c + 4, t + 22, RAMP["skin"][1]); cv.put(c + 5, t + 22, RAMP["skin"][1])
    cv.outline()
    cv.puts([(c - 12, t + 3), (c - 13, t + 2)], hr[1])
    steam(cv, c + 9, t + 26)
    return cv


def b_back():
    """From behind: the full cape of graded papers is the showpiece."""
    cv = Cv(BW, BH)
    c, t = 48, BT
    hr = RAMP["hair"]
    b_legs(cv, c, t)
    # no laces from behind: paint the boot heels plain
    br = RAMP["boot"]
    for s in (-1, 1):
        bx = c + s * 5.5
        for y in range(t + 72, t + 78):
            for x in (bx - 1, bx, bx + 1):
                cv.put(x, y, br[2] if x < bx + 1 else br[1])
        cv.vline(bx, t + 71, t + 77, br[1])
    b_skirt(cv, c, t)
    b_torso(cv, c, t)
    # head from behind: nape, hair, bun with pencils
    cv.part("neck", cv.rect(c - 2.5, t + 18, c + 2.5, t + 23), "skin", rad=2, bias=-0.15)
    head = cv.ell(c, t + 13, 8.6, 8.4)
    cv.part("head", head, "hair", rad=6, soft=1.2, cuts=(0.30, 0.56, 0.86), tex=0.06, seed=71)
    for (x0, y0, x1, y1) in [(c - 1, t + 6, c - 5, t + 19), (c + 1, t + 6, c + 4, t + 19), (c - 4, t + 7, c - 7, t + 16), (c + 4, t + 7, c + 7, t + 16)]:
        cv.line(x0, y0, x1, y1, hr[1])
    cv.puts([(c - 2, t + 20), (c, t + 21), (c + 2, t + 20)], hr[2])
    pencil(cv, c - 9, t + 2, c + 10, t + 7, "pencilA")
    pencil(cv, c + 8, t + 1, c - 4, t + 8, "pencilB")
    bun = cv.ell(c, t + 4.6, 5.6, 4.6)
    cv.part("bun", bun, "hair", noedge=("head",), rad=4, soft=0.8, cuts=(0.28, 0.52, 0.84), tex=0.08, seed=73)
    cv.line(c - 3, t + 2, c + 3, t + 7, hr[1]); cv.line(c - 4, t + 5, c - 1, t + 7, hr[1])
    # pencil ends poke out of the far side of the bun too
    # ---- the cape over her back ----
    cloak = cv.poly([(c - 8, t + 23), (c + 8, t + 23), (c + 12, t + 30), (c + 18, t + 66), (c + 11, t + 69),
                     (c, t + 67), (c - 11, t + 69), (c - 18, t + 66), (c - 12, t + 30)])
    cv.part("cloak", cloak, "pen", rad=7, soft=1.2, cuts=(0.45, 0.75, 0.95), bias=-0.25)
    pr = RAMP["pen"]
    for k in (-1, 1):                                   # cloak folds
        cv.line(c + k * 6, t + 58, c + k * 9, t + 67, pr[1])
    marks = ["A+", None, "F", "check", "C-", None, "circ", "x", "?", "check", None, "A+"]
    k = 0
    for row in range(4):
        y = t + 30 + row * 8.0
        for j in (-1, 0, 1):
            x = c + j * (7.6 + row * 0.9) + (1 if row % 2 else -1) * 0.6
            ang = j * (0.06 + row * 0.03) + (0.05 if (row + j) % 2 else -0.05)
            paper(cv, "cape%d" % k, x, y, 10, 12, ang, mark=marks[k % len(marks)], seed=80 + k, mark_at=(-1.5, -3))
            k += 1
    # standing collar seen from behind: paper backs at the shoulders
    px, py = c, t + 25
    for s_ in (-1, 1):
        for deg, rad in ((66, 12.5), (90, 12.0)):
            a = math.radians(deg) * s_
            paper(cv, "colb%d%d" % (s_, deg), px + math.sin(a) * rad, py - math.cos(a) * rad, 7, 9, a,
                  mark=None, lines=True, seed=deg, small=True)
    # arms at the sides (coffee viewer-left, pen viewer-right: mirrored hands from behind)
    b_arm(cv, "armL", [(c - 10, t + 26), (c - 13, t + 32), (c - 14, t + 37)])
    cup(cv, c - 15, t + 29)
    b_hand(cv, c - 14, t + 38, "handL", rx=2.4)
    b_arm(cv, "armR", [(c + 10, t + 26), (c + 13, t + 32), (c + 15, t + 37)])
    pen(cv, c + 16, t + 34, c + 20, t + 81)
    b_hand(cv, c + 16, t + 39, "handR")
    cv.outline()
    steam(cv, c - 15, t + 27)
    return cv


def b_entrance():
    """Intro-card pose: pen raised overhead in a red-ink slash, cape thrown wide, papers flying,
    coffee held out like a trophy."""
    W, H = 132, 124
    cv = Cv(W, H)
    c, t = 64, H - BODY_H
    b_cape_collar(cv, c, t, spread=1.12, seed=7)
    b_cape_back(cv, c, t, flare=1.6, seed=30)
    b_legs(cv, c, t, stance=1)
    b_skirt(cv, c, t, swing=0)
    b_torso(cv, c, t)
    b_lanyard(cv, c, t)
    # coffee arm thrust out to the side
    b_arm(cv, "armR", [(c + 10, t + 26), (c + 18, t + 28), (c + 25, t + 25)])
    cup(cv, c + 29, t + 13)
    b_hand(cv, c + 27, t + 24, "handR", rx=2.5)
    # pen arm raised overhead; the pen sweeps up and over her head
    b_arm(cv, "armL", [(c - 10, t + 26), (c - 17, t + 18), (c - 14, t + 8)])
    pen(cv, c - 18, t + 14, c + 20, t - 34, r=2.6)
    b_hand(cv, c - 14, t + 7, "handL", rx=2.8, ry=2.8)
    b_face(cv, c, t, "tell")
    # a wink: the viewer-right eye closes into a happy arc
    for x in range(c + 2, c + 6):
        for y in range(t + 12, t + 17):
            if cv.own[y, x] == cv.names["face"]:
                cv.put(x, y, cv.get(x - 7 if x - 7 >= c - 5 else x, y) if False else RAMP["skin"][2 if y < t + 15 else 2])
    cv.puts([(c + 2, t + 14), (c + 3, t + 13), (c + 4, t + 13), (c + 5, t + 14)], EYE)
    cv.put(c + 3, t + 16, BAG); cv.put(c + 4, t + 16, BAG)
    cv.puts([(c + 5, t + 17), (c + 4, t + 18), (c + 6, t + 18)], FRECKLE)
    cv.puts([(c + 2, t + 11), (c + 3, t + 10), (c + 4, t + 10), (c + 5, t + 11)], RAMP["hair"][1])
    # loose sheets flying off the cape
    for k, (x, y, ang, mk) in enumerate(((c - 40, t + 30, -0.6, "F"), (c + 40, t + 40, 0.5, "A+"),
                                         (c - 44, t + 56, 0.3, "check"), (c + 44, t + 62, -0.4, "x"),
                                         (c - 30, t + 8, 0.9, "C-"), (c + 36, t - 4, -0.3, "circ"))):
        paper(cv, "fly%d" % k, x, y, 8, 10, ang, mark=mk, seed=110 + k, mark_at=(-2, -3))
    cv.outline()
    # red-ink slash trail arcing from the nib
    for k in range(0, 64):
        a = math.radians(-60 + k * 1.0)
        for rr, col in ((47.0, REDINK), (48.0, REDINK), (46.0, REDINK2)):
            x = c - 6 + math.cos(a) * rr
            y = t + 12 + math.sin(a) * rr
            ix, iy = int(round(x)), int(round(y))
            if 0 <= ix < W and 0 <= iy < H and not cv.alpha[iy, ix]:
                if k > 14 or rr == 47.0:
                    cv.put(ix, iy, col)
    # glint on the nib and steam
    sx, sy = c + 20, t - 34
    cv.puts([(sx - 3, sy), (sx + 3, sy), (sx, sy - 3), (sx, sy + 3), (sx - 2, sy), (sx + 2, sy), (sx, sy - 2), (sx, sy + 2), (sx - 1, sy), (sx + 1, sy), (sx, sy - 1), (sx, sy + 1)], SPARK2)
    cv.put(sx, sy, WHITE)
    steam(cv, c + 29, t + 11)
    return cv


# ==========================================================================
# WORLD  (52 px standing height, redrawn small -- not scaled)
# ==========================================================================
WW, WH = 60, 56
WORLD_H = 52
WT = WH - WORLD_H


def w_paper(cv, name, x, y, ang, mark=None, seed=0, w=6, h=7, lines=True):
    return paper(cv, name, x, y, w, h, ang, mark=mark, seed=seed, small=True, mark_at=(-1, -2), lines=lines)


def w_cape(cv, c, t, flare=0.0, back=False):
    fl = flare * 2
    cloak = cv.poly([(c - 6, t + 15), (c + 6, t + 15), (c + 10, t + 21), (c + 14 + fl, t + 40), (c + 10 + fl, t + 43),
                     (c, t + 42), (c - 10 - fl, t + 43), (c - 14 - fl, t + 40), (c - 10, t + 21)])
    cv.part("cloak", cloak, "pen", rad=4, soft=1.0, cuts=(0.45, 0.75, 0.95), bias=-0.25)
    if back:
        return
    marks = ["tick", None, "dash", None, "tick", "dot", None, "dash"]
    k = 0
    for row in range(4):
        y = t + 20 + row * 5.6
        for s in (-1, 1):
            x = c + s * (9.5 + row * (1.1 + flare * 0.8))
            ang = s * (0.06 + 0.04 * row + flare * 0.1) + (0.05 if (row + (s > 0)) % 2 else -0.04)
            w_paper(cv, "cape%d" % k, x, y, ang, mark=marks[k % len(marks)], seed=20 + k)
            k += 1


def w_collar(cv, c, t, spread=1.0, back=False):
    px, py = c, t + 16
    k = 0
    for s in (-1, 1):
        for deg, rad in ((44, 8.5), (70, 9.0), (94, 8.0)):
            a = math.radians(deg * spread) * s
            w_paper(cv, "col%d" % k, px + math.sin(a) * rad, py - math.cos(a) * rad, a, w=5, h=7,
                    mark=("tick" if (k == 1 and not back) else None), seed=k, lines=True)
            k += 1


def w_legs(cv, c, t, back=False):
    for s in (-1, 1):
        cv.part("leg%d" % s, cv.capsule(c + s * 3, t + 35, c + s * 3.5, t + 45, 1.9, 1.6), "tights", rad=2,
                cuts=(0.30, 0.55, 0.88))
    br = RAMP["boot"]
    for s in (-1, 1):
        bx = c + s * 3.5
        boot = cv.rect(bx - 2.3, t + 44, bx + 2.3, t + 49) | (cv.ell(bx + s * 0.5, t + 49.6, 3.2, 2.2) & cv.half(y=t + 51, below=False))
        cv.part("shoe%d" % s, boot, "boot", rad=2, soft=0.6, cuts=(0.32, 0.58, 0.9))
        cv.hline(bx - 2, bx + 2, t + 44, br[3])
        if not back:
            cv.put(bx, t + 46, LACE)
        for x in range(int(bx - 3), int(bx + 4)):
            if cv.own[t + 51, x] == cv.names["shoe%d" % s]:
                cv.put(x, t + 51, STITCH if x % 2 == 0 else br[0])


def w_skirt(cv, c, t):
    sk = cv.poly([(c - 6, t + 27), (c + 6, t + 27), (c + 9, t + 36), (c + 4, t + 36.5), (c, t + 36), (c - 4, t + 36.5), (c - 9, t + 36)])
    cv.part("skirt", sk, "tartan", rad=3, soft=0.8, cuts=(0.30, 0.55, 0.86))
    pid = cv.names["skirt"]
    tr = RAMP["tartan"]
    for y in (t + 30, t + 33):
        for x in range(c - 9, c + 10):
            if cv.own[y, x] == pid and cv.get(x, y) != tr[0]:
                cv.put(x, y, (30, 52, 44))
    for k in (-1, 0, 1):
        for y in range(t + 28, t + 36):
            f = (y - (t + 27)) / 9.0
            x = int(round(c + k * (3.4 + 1.6 * f)))
            if cv.own[y, x] == pid and cv.get(x, y) != tr[0]:
                cv.put(x, y, (22, 36, 32) if y in (t + 30, t + 33) else (30, 52, 44))
    belt = cv.rect(c - 6, t + 27, c + 6, t + 27)
    cv.part("belt", belt, "belt", edge=None, lv=np.where(belt, 2, 0))
    cv.put(c, t + 27, RAMP["gold"][3])


def w_torso(cv, c, t, back=False):
    kn = RAMP["knit"]
    torso = cv.poly([(c - 4, t + 14.5), (c + 4, t + 14.5), (c + 7, t + 16.5), (c + 7.5, t + 19.5), (c + 6, t + 23.5),
                     (c + 5.5, t + 27), (c - 5.5, t + 27), (c - 6, t + 23.5), (c - 7.5, t + 19.5), (c - 7, t + 16.5)])
    cv.part("torso", torso, "knit", rad=5, soft=1.2, cuts=(0.30, 0.52, 0.84))
    col = cv.ell(c, t + 14.5, 3.4, 1.8) | cv.rect(c - 2.5, t + 13, c + 2.5, t + 14)
    cv.part("collar", col, "knit", rad=2, bias=0.08)
    if not back:
        gd = RAMP["gold"]
        cv.line(c - 2, t + 16, c - 1, t + 20, gd[2]); cv.line(c + 2, t + 16, c + 1, t + 20, gd[1])
        cv.put(c, t + 21, RAMP["paper"][3]); cv.put(c, t + 22, RAMP["paper"][2]); cv.put(c - 1, t + 21, REDINK)
        cv.put(c + 1, t + 21, RAMP["paper"][3]); cv.put(c + 1, t + 22, RAMP["paper"][2]); cv.put(c - 1, t + 22, RAMP["paper"][2])
        cv.put(c - 4, t + 18, kn[3]); cv.put(c - 3, t + 18, kn[3])


def w_arm(cv, name, pts, r=1.8):
    m = cv.chain(pts, r)
    cv.part(name, m, "knit", edge="dark", rad=2, soft=0.7, cuts=(0.30, 0.55, 0.9))
    return m


def w_hand(cv, x, y, name, r=1.7):
    m = cv.ell(x, y, r, r)
    cv.part(name, m, "skin", edge="ink", lv=np.where(m, 3, 0) - np.where(m & (cv.X > x) & (cv.Y > y - 1), 1, 0))
    return m


def w_head(cv, c, t, pose, glance=0):
    sk, hr = RAMP["skin"], RAMP["hair"]
    bun = cv.ell(c + 0.5, t + 2.7, 3.6, 2.8)
    cv.part("bun", bun, "hair", rad=3, soft=0.6, cuts=(0.28, 0.52, 0.84))
    cv.put(c - 1, t + 2, hr[1]); cv.put(c + 1, t + 3, hr[1])
    w_pencil(cv, c - 6, t + 1, c + 6, t + 4)
    back = cv.ell(c, t + 8.6, 6.4, 5.8) | cv.capsule(c - 5.5, t + 8, c - 5.8, t + 14, 1.5) | cv.capsule(c + 5.5, t + 8, c + 5.8, t + 14, 1.5)
    cv.part("hairback", back, "hair", rad=3, soft=0.8, cuts=(0.30, 0.56, 0.86))
    cv.part("neck", cv.rect(c - 1.5, t + 12, c + 1.5, t + 14), "skin", rad=1, bias=-0.15)
    face = cv.ell(c, t + 8.6, 4.9, 4.8) | cv.ell(c, t + 10.4, 4.1, 4.4)
    cv.part("face", face, "skin", rad=4, soft=1.0, cuts=(0.22, 0.46, 0.88), bias=0.08)
    fr = cv.ell(c, t + 8.0, 5.8, 5.2)
    line = t + 5.6 + 0.30 * (cv.X - c) + np.where(((cv.X - c) % 3) == 1, 0.9, 0)
    fringe = (fr & (cv.Y < line)) | cv.capsule(c - 5, t + 6, c - 5.2, t + 12.5, 1.1) | cv.capsule(c + 4.9, t + 6.5, c + 5.3, t + 13, 1.0)
    cv.part("fringe", fringe, "hair", noedge=("hairback", "bun"), rad=3, soft=0.7, cuts=(0.28, 0.54, 0.86))
    cv.put(c - 3, t + 4, hr[4]); cv.put(c - 2, t + 4, hr[4])
    cv.line(c - 2, t + 5, c, t + 7, hr[1])
    g = glance
    ey = t + 8
    for side in (-1, 1):
        x0 = c - 3 if side < 0 else c + 1      # 3-wide eye cell
        if pose == "blink" or pose == "sip":
            cv.hline(x0, x0 + 2, ey, EYE)                       # closed: just the lid line
            cv.put(x0 + 1, ey + 2, BAG)
        elif pose == "hit":
            cv.put(x0 + (0 if side < 0 else 2), ey, EYE); cv.put(x0 + 1, ey + 1, EYE); cv.put(x0 + (0 if side < 0 else 2), ey + 2, EYE)
        elif pose == "tell":
            cv.hline(x0, x0 + 2, ey + 1, EYE); cv.put(x0 + 1 + g, ey + 2, IRIS)
        else:
            cv.hline(x0, x0 + 2, ey, EYE)                       # heavy lid
            px_ = x0 + 1 + g
            cv.put(px_, ey + 1, EYE)
            cv.put(px_ + (1 if side < 0 else -1), ey + 1, IRIS)  # green iris toward the nose
            cv.put(x0 + 1, ey + 2, BAG)
    # brows
    if pose != "hit":
        cv.put(c - 3, t + 6 + (pose == "tell"), hr[1]); cv.put(c - 2, t + 6 + (pose == "tell"), hr[1])
        cv.put(c + 2, t + 6 - (pose not in ("tell",)) + (pose == "tell"), hr[1]); cv.put(c + 3, t + 6, hr[1])
    cv.put(c - 4, t + 11, FRECKLE); cv.put(c + 4, t + 11, FRECKLE)
    cv.put(c, t + 10, sk[1])
    my = t + 12
    if pose == "talk":
        cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c, my + 1, LIP)
    elif pose == "hit":
        cv.hline(c - 1, c + 1, my, MOUTH); cv.hline(c - 1, c + 1, my + 1, MOUTH)
    elif pose == "tell":
        cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c + 2, my - 1, MOUTH); cv.put(c - 2, my - 1, MOUTH)
    else:
        cv.hline(c - 1, c, my, MOUTH); cv.put(c + 1, my - 1, MOUTH); cv.put(c - 1, my + 1, LIP) if False else None


def w_front(pose, extra=None):
    """extra: None | 'blink' | 'sip' | 'shoulder' (idle variants share the idle lower body)."""
    cv = Cv(WW, WH)
    c, t = 30, WT
    hx = 1 if pose == "hit" else 0
    w_collar(cv, c, t, spread=1.08 if pose == "hit" else 1.0)
    w_cape(cv, c, t, flare=0.5 if pose in ("tell", "hit") else 0.0)
    w_legs(cv, c, t)
    w_skirt(cv, c, t)
    w_torso(cv, c, t)
    # pen arm (viewer left)
    if extra == "shoulder":
        # pen hoisted upright like a staff
        w_arm(cv, "armL", [(c - 6.5, t + 17), (c - 9.5, t + 21), (c - 11, t + 19)])
        pen(cv, c - 12, t + 29, c - 13, t + 0, small=True, r=1.6)
        w_hand(cv, c - 11.5, t + 19, "handL")
    elif pose in ("idle", "talk"):
        w_arm(cv, "armL", [(c - 6.5, t + 17), (c - 8.5, t + 21), (c - 9.5, t + 24)])
        pen(cv, c - 10, t + 21, c - 13, t + 51, small=True, r=1.6)
        w_hand(cv, c - 10, t + 25, "handL")
    elif pose == "tell":
        pen(cv, c - 7, t + 26, c - 21, t + 3, small=True, r=1.6)
        w_arm(cv, "armL", [(c - 6.5, t + 17), (c - 10, t + 19), (c - 10.5, t + 16)])
        w_hand(cv, c - 10.5, t + 16.5, "handL")
    elif pose == "hit":
        w_arm(cv, "armL", [(c - 6.5, t + 17), (c - 10, t + 19.5), (c - 12.5, t + 17)])
        pen(cv, c - 8, t + 26, c - 19, t + 5, small=True, r=1.6)
        w_hand(cv, c - 12.5, t + 17, "handL")
    # coffee arm (viewer right)
    if extra == "sip":
        w_arm(cv, "armR", [(c + 6.5, t + 17), (c + 9.5, t + 20), (c + 9.5, t + 15.5)])
        cup(cv, c + 9.5, t + 8, small=True)
        w_hand(cv, c + 9.5, t + 15.5, "handR", r=1.6)
    elif pose in ("idle", "tell"):
        w_arm(cv, "armR", [(c + 6.5, t + 17), (c + 8.5, t + 21), (c + 9, t + 24)])
        cup(cv, c + 9.5, t + 18, small=True)
        w_hand(cv, c + 9, t + 25, "handR", r=1.6)
    elif pose == "talk":
        w_arm(cv, "armR", [(c + 6.5, t + 17), (c + 10, t + 19), (c + 11.5, t + 15)])
        cup(cv, c + 12, t + 7, small=True)
        w_hand(cv, c + 11.5, t + 15, "handR", r=1.6)
    elif pose == "hit":
        w_arm(cv, "armR", [(c + 6.5, t + 17), (c + 10, t + 18.5), (c + 13, t + 16)])
        cup(cv, c + 15, t + 8, small=True, tilt=0.55)
        w_hand(cv, c + 13, t + 16, "handR", r=1.6)
    hpose = extra if extra in ("blink", "sip") else pose
    w_head(cv, c + hx, t, hpose, glance=(-1 if extra == "shoulder" else 0))
    cv.outline()
    if pose in ("idle", "tell") and extra != "sip":
        steam(cv, c + 9, t + 17, small=True)
    elif pose == "talk":
        steam(cv, c + 12, t + 6, small=True)
    if extra == "sip":
        steam(cv, c + 9, t + 7, small=True)
    if pose == "hit":
        cv.puts([(c + 18, t + 6), (c + 19, t + 8), (c + 18, t + 9)], COFFEE)
        cv.puts([(c + 7, t + 1), (c + 6, t + 2), (c + 7, t + 2), (c + 7, t + 3)], SWEAT)
    if pose == "tell":
        sx, sy = c - 21, t + 3
        cv.puts([(sx - 1, sy), (sx + 1, sy), (sx, sy - 1), (sx, sy + 1)], SPARK2)
        cv.put(sx, sy, WHITE)
    return cv


def w_side():
    cv = Cv(WW, WH)
    c, t = 29, WT
    hr, kn = RAMP["hair"], RAMP["knit"]
    px, py = c - 1, t + 16
    for k, (deg, mk) in enumerate(((-36, None), (-62, "tick"), (-90, None))):
        a = math.radians(deg)
        w_paper(cv, "col%d" % k, px + math.sin(a) * 8.5, py - math.cos(a) * 8.5, a, w=5, h=7, mark=mk, seed=k)
    cloak = cv.poly([(c - 4, t + 15), (c + 1, t + 16), (c - 1, t + 26), (c - 3, t + 42), (c - 9, t + 43),
                     (c - 14, t + 40), (c - 9, t + 22)])
    cv.part("cloak", cloak, "pen", rad=4, soft=1.0, cuts=(0.45, 0.75, 0.95), bias=-0.25)
    for k, (x, y, ang, mk) in enumerate(((c - 7, t + 20, -0.12, None), (c - 9, t + 26, -0.18, "tick"),
                                         (c - 10, t + 32, -0.12, None), (c - 11, t + 38, -0.22, "dash"))):
        w_paper(cv, "cape%d" % k, x, y, ang, mark=mk, seed=30 + k)
    pen(cv, c - 8, t + 11, c - 1, t + 45, small=True, r=1.6)
    for k, lx in enumerate((c - 2, c + 1)):
        name = "B" if k == 0 else "F"
        cv.part("leg" + name, cv.capsule(lx, t + 35, lx + (1 if k else -1) * 0.5, t + 45, 1.9, 1.6), "tights", rad=2,
                cuts=(0.30, 0.55, 0.88) if k else (0.45, 0.7, 0.95))
        bx = lx + (0.5 if k else -0.5)
        boot = cv.rect(bx - 2, t + 44, bx + 2, t + 49) | (cv.ell(bx + 1.6, t + 49.6, 3.6, 2.2) & cv.half(y=t + 51, below=False))
        cv.part("shoe" + name, boot, "boot", rad=2, cuts=(0.32, 0.58, 0.9) if k else (0.45, 0.7, 0.95))
        for x in range(int(bx - 2), int(bx + 6)):
            if cv.own[t + 51, x] == cv.names["shoe" + name]:
                cv.put(x, t + 51, STITCH if x % 2 == 0 else RAMP["boot"][0])
        if k:
            cv.put(bx + 1, t + 46, LACE)
    skm = cv.poly([(c - 5, t + 27), (c + 4, t + 27), (c + 7, t + 36), (c, t + 36.5), (c - 8, t + 36)])
    cv.part("skirt", skm, "tartan", rad=3, cuts=(0.30, 0.55, 0.86))
    pid = cv.names["skirt"]
    for y in (t + 30, t + 33):
        for x in range(c - 9, c + 8):
            if cv.own[y, x] == pid and cv.get(x, y) != RAMP["tartan"][0]:
                cv.put(x, y, (30, 52, 44))
    for y in range(t + 28, t + 36):
        if cv.own[y, c - 1] == pid:
            cv.put(c - 1, y, (30, 52, 44))
    cv.part("belt", cv.rect(c - 5, t + 27, c + 4, t + 27), "belt", edge=None, lv=np.where(cv.rect(c - 5, t + 27, c + 4, t + 27), 2, 0))
    torso = cv.poly([(c - 3.5, t + 14.5), (c + 2, t + 14.5), (c + 4, t + 17), (c + 4.5, t + 20), (c + 3.5, t + 24),
                     (c + 3.5, t + 27), (c - 4.5, t + 27), (c - 4, t + 23), (c - 4.5, t + 18)])
    cv.part("torso", torso, "knit", rad=4, soft=1.0, cuts=(0.30, 0.52, 0.84))
    cv.part("collar", cv.ell(c - 0.5, t + 14.5, 3, 1.8) | cv.rect(c - 2, t + 13, c + 2, t + 14), "knit", rad=2, bias=0.08)
    cv.line(c + 1, t + 16, c + 3, t + 20, RAMP["gold"][2]); cv.put(c + 3, t + 21, RAMP["paper"][3]); cv.put(c + 4, t + 21, REDINK)
    w_arm(cv, "arm", [(c - 0.5, t + 17), (c, t + 21.5), (c + 4, t + 23.5)])
    cup(cv, c + 6, t + 17, small=True)
    w_hand(cv, c + 5, t + 24, "hand", r=1.6)
    bun = cv.ell(c - 4, t + 2.8, 3.4, 2.9)
    cv.part("bun", bun, "hair", rad=3, cuts=(0.28, 0.52, 0.84))
    w_pencil(cv, c - 9, t + 1, c, t + 5)
    cv.part("neck", cv.rect(c - 1, t + 11.5, c + 1.5, t + 14), "skin", rad=1, bias=-0.15)
    head = cv.ell(c + 0.8, t + 8.6, 4.7, 4.8) | cv.ell(c + 2, t + 10.4, 3.4, 4.2)
    cv.part("head", head, "skin", rad=4, soft=1.0, cuts=(0.30, 0.52, 0.88), bias=0.10)
    cv.part("nose", cv.ell(c + 5.6, t + 10, 0.9, 1.0), "skin", edge="ink", noedge=("head",), lv=None, rad=1, bias=0.15)
    hair = cv.ell(c, t + 7.9, 5.4, 5.1)
    hair &= (cv.X < c + 0.5) | (cv.Y < t + 5.4 + 0.35 * (cv.X - c))
    hair |= cv.capsule(c - 4, t + 7, c - 3.8, t + 12.5, 1.3)
    cv.part("hair", hair, "hair", noedge=("bun",), rad=3, soft=0.8, cuts=(0.28, 0.54, 0.86))
    cv.put(c, t + 4, hr[4]); cv.put(c - 1, t + 4, hr[4])
    cv.hline(c + 2, c + 4, t + 8, EYE); cv.put(c + 3, t + 9, EYE); cv.put(c + 4, t + 9, IRIS)
    cv.put(c + 3, t + 10, BAG)
    cv.put(c + 3, t + 6, hr[1]); cv.put(c + 4, t + 6, hr[1])
    cv.put(c + 4, t + 13, MOUTH); cv.put(c + 3, t + 11, FRECKLE)
    cv.outline()
    steam(cv, c + 6, t + 16, small=True)
    return cv


def w_back():
    cv = Cv(WW, WH)
    c, t = 30, WT
    hr = RAMP["hair"]
    w_legs(cv, c, t, back=True)
    w_skirt(cv, c, t)
    w_torso(cv, c, t, back=True)
    cv.part("neck", cv.rect(c - 1.5, t + 11, c + 1.5, t + 14), "skin", rad=1, bias=-0.15)
    head = cv.ell(c, t + 8.3, 5.6, 5.5)
    cv.part("head", head, "hair", rad=4, soft=0.9, cuts=(0.30, 0.56, 0.86))
    cv.line(c - 1, t + 5, c - 3, t + 12, hr[1]); cv.line(c + 1, t + 5, c + 3, t + 12, hr[1])
    bun = cv.ell(c, t + 3, 3.7, 3.0)
    cv.part("bun", bun, "hair", noedge=("head",), rad=3, cuts=(0.28, 0.52, 0.84))
    w_pencil(cv, c - 6, t + 1, c + 6, t + 4)
    cv.put(c - 1, t + 2, hr[1]); cv.put(c + 1, t + 4, hr[1])
    w_cape(cv, c, t, back=True)
    k = 0
    marks = ["tick", "dash", None, None, "tick", "dot", "dash", None, "tick"]
    for row in range(3):
        for j in (-1, 0, 1):
            x = c + j * (5.2 + row * 0.6)
            ang = j * (0.06 + row * 0.03) + (0.05 if (row + j) % 2 else -0.05)
            w_paper(cv, "capeb%d" % k, x, t + 20 + row * 6.2, ang, mark=marks[k], seed=60 + k, w=7, h=8)
            k += 1
    px, py = c, t + 16
    for s_ in (-1, 1):
        for deg in (68, 92):
            a = math.radians(deg) * s_
            w_paper(cv, "colb%d%d" % (s_, deg), px + math.sin(a) * 8.0, py - math.cos(a) * 8.0, a, w=5, h=6, seed=deg)
    w_arm(cv, "armL", [(c - 6.5, t + 17), (c - 8.5, t + 21), (c - 9, t + 24)])
    cup(cv, c - 9.5, t + 18, small=True)
    w_hand(cv, c - 9, t + 25, "handL", r=1.6)
    w_arm(cv, "armR", [(c + 6.5, t + 17), (c + 8.5, t + 21), (c + 9.5, t + 24)])
    pen(cv, c + 10, t + 21, c + 13, t + 51, small=True, r=1.6)
    w_hand(cv, c + 10, t + 25, "handR")
    cv.outline()
    steam(cv, c - 9, t + 17, small=True)
    return cv


# ==========================================================================
# PORTRAITS  (64 x 64, head and shoulders)
# ==========================================================================
PW = PH = 64
EXPRS = ("neutral", "warm", "concern", "surprised")


def p_eye(cv, ex, ey, expr, side):
    """Pixel-map eyes; (ex, ey) = top-left of a 7-wide cell for the viewer-left eye, mirrored on the right.
    K lid/lash, W white, I green iris, D pupil, H catch-light, B tired bag."""
    maps = {
        "neutral":   ["KKKKKK.",
                      ".KIDDHK",
                      ".WIIIW.",
                      "..BBB.."],
        "warm":      [".......",
                      "..KKK..",
                      ".K...K.",
                      "K.....K",
                      ".BBBBB."],
        "concern":   [".KKKKK.",
                      "KWHDIWK",
                      ".WIIIW.",
                      "..WWW..",
                      "..BBB.."],
        "surprised": ["..KKK..",
                      ".KWWWK.",
                      "KWHDIWK",
                      "KWIDIWK",
                      ".KWIWK.",
                      "..BBB.."],
    }
    pal = {"K": EYE, "I": IRIS, "D": (24, 52, 36), "H": WHITE, "W": SCLERA, "B": BAG}
    for j, row in enumerate(maps[expr]):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x = ex + i if side < 0 else ex + (6 - i)
            col = pal[ch]
            if ch == "H" and side > 0:
                col = IRIS                       # catch-lights both sit on the upper left
            cv.put(x, ey + j, col)
    if side > 0:
        rows = maps[expr]
        for j, row in enumerate(rows):
            if "H" in row:
                i = row.index("H")
                cv.put(ex + (6 - i) - 2, ey + j, WHITE)


def p_brows(cv, c, by, expr):
    hr = RAMP["hair"]
    if expr == "concern":
        left = [(-10, 1), (-9, 1), (-8, 0), (-7, 0), (-6, -1), (-5, -1), (-4, -2)]
        right = [(10, 1), (9, 1), (8, 0), (7, 0), (6, -1), (5, -1), (4, -2)]
    elif expr == "surprised":
        left = [(-11, 0), (-10, -1), (-9, -2), (-8, -2), (-7, -2), (-6, -2), (-5, -1)]
        right = [(11, 0), (10, -1), (9, -2), (8, -2), (7, -2), (6, -2), (5, -1)]
    elif expr == "warm":
        left = [(-11, 1), (-10, 0), (-9, -1), (-8, -1), (-7, -1), (-6, -1), (-5, 0)]
        right = [(11, 1), (10, 0), (9, -1), (8, -1), (7, -1), (6, -1), (5, 0)]
    else:   # neutral: flat, the viewer-right brow cocked up (skeptical grader)
        left = [(-11, 0), (-10, 0), (-9, 0), (-8, 0), (-7, 0), (-6, 0), (-5, 1)]
        right = [(11, -1), (10, -2), (9, -3), (8, -3), (7, -3), (6, -2), (5, -1)]
    for pts, lit in ((left, True), (right, False)):
        for i, (dx, dy) in enumerate(pts):
            cv.put(c + dx, by + dy, hr[1] if lit else hr[0])
            if 0 < i < 6:
                cv.put(c + dx, by + dy - 1, hr[2] if lit else hr[1])


def p_mouth(cv, c, my, expr, talk=False):
    if expr == "neutral":
        if not talk:
            cv.hline(c - 3, c + 2, my, MOUTH); cv.put(c + 3, my - 1, MOUTH); cv.put(c + 4, my - 1, MOUTH)
            cv.hline(c - 2, c + 1, my + 1, LIP); cv.put(c - 1, my + 1, LIP_HI)
            cv.hline(c - 2, c + 2, my - 1, LIP)
        else:
            cv.hline(c - 2, c + 2, my - 1, LIP)
            cv.hline(c - 3, c + 2, my, MOUTH); cv.put(c + 3, my - 1, MOUTH)
            cv.hline(c - 2, c + 1, my + 1, MOUTH); cv.hline(c - 1, c, my + 1, TONGUE)
            cv.hline(c - 2, c + 1, my + 2, LIP); cv.put(c - 1, my + 2, LIP_HI)
    elif expr == "warm":
        cv.hline(c - 5, c + 5, my - 1, MOUTH)
        cv.put(c - 6, my - 2, MOUTH); cv.put(c + 6, my - 2, MOUTH)
        cv.hline(c - 4, c + 4, my, TEETH)
        cv.put(c - 5, my, MOUTH); cv.put(c + 5, my, MOUTH)
        if not talk:
            cv.hline(c - 4, c + 4, my + 1, MOUTH)
            cv.hline(c - 2, c + 2, my + 1, TONGUE)
            cv.hline(c - 3, c + 3, my + 2, LIP); cv.put(c - 2, my + 2, LIP_HI)
        else:
            cv.hline(c - 4, c + 4, my + 1, MOUTH)
            cv.hline(c - 4, c + 4, my + 2, MOUTH)
            cv.hline(c - 2, c + 2, my + 2, TONGUE); cv.hline(c - 1, c + 1, my + 1, TONGUE)
            cv.hline(c - 3, c + 3, my + 3, LIP); cv.put(c - 2, my + 3, LIP_HI)
    elif expr == "concern":
        if not talk:
            cv.hline(c - 2, c + 2, my, MOUTH)
            cv.put(c - 3, my + 1, MOUTH); cv.put(c + 3, my + 1, MOUTH)
            cv.hline(c - 1, c + 1, my + 1, LIP)
        else:
            cv.hline(c - 2, c + 2, my, MOUTH)
            cv.put(c - 3, my + 1, MOUTH); cv.put(c + 3, my + 1, MOUTH)
            cv.hline(c - 2, c + 2, my + 1, MOUTH); cv.put(c, my + 1, TONGUE)
            cv.hline(c - 1, c + 1, my + 2, LIP)
    elif expr == "surprised":
        rows = ((0, 1), (1, 2), (2, 2), (3, 1)) if not talk else ((0, 1), (1, 2), (2, 2), (3, 2), (4, 1))
        for dy, w in rows:
            cv.hline(c - w, c + w, my + dy - 1, MOUTH)
        cv.hline(c - 1, c + 1, my + len(rows) - 2, TONGUE)
        cv.hline(c - 1, c + 1, my + len(rows) - 1, LIP)
        cv.put(c - 2, my - 2, LIP); cv.put(c + 2, my - 2, LIP)


def portrait(expr, talk=False):
    cv = Cv(PW, PH, open_bottom=True)
    c = 32
    sk, hr, kn = RAMP["skin"], RAMP["hair"], RAMP["knit"]
    lift = -1 if expr == "surprised" else 0
    # ---- standing collar of graded papers behind the shoulders ----
    marks = ["check", "F", None, "A+", "x", "C-"]
    k = 0
    for s in (-1, 1):
        for deg, rad in ((34, 25), (58, 26), (84, 25)):
            a = math.radians(deg) * s
            paper(cv, "col%d" % k, c + math.sin(a) * rad, 60 - math.cos(a) * rad, 12, 16, a,
                  mark=marks[k], seed=200 + k, mark_at=(-3, -5), step=3)
            k += 1
    # ---- the pen slung behind her right shoulder (viewer left), cap end up ----
    pen(cv, 9, 12, 2, 70, r=3.0)
    # ---- shoulders + turtleneck ----
    sh = cv.ell(c, 78, 28, 24) & cv.half(y=49)
    cv.part("shoulders", sh, "knit", rad=14, soft=2.0, cuts=(0.30, 0.52, 0.84), tex=0.05, seed=41)
    cv.line(10, 58, 13, 63, kn[1]); cv.line(54, 58, 51, 63, kn[0])
    gd = RAMP["gold"]
    cv.line(c - 7, 54, c - 3, 63, gd[2]); cv.line(c + 7, 54, c + 3, 63, gd[1])
    cv.put(c - 5, 58, gd[3])
    # ---- hair behind the face ----
    pencil(cv, c - 15, 3, c + 16, 10, "pencilA", r=2.0)
    pencil(cv, c + 13, 1, c - 6, 11, "pencilB", r=2.0)
    bun = cv.ell(c + 2, 7 + lift, 8.5, 6.2)
    cv.part("bun", bun, "hair", rad=6, soft=1.0, cuts=(0.28, 0.52, 0.84), tex=0.07, seed=61)
    for (x0, y0, x1, y1) in [(c - 4, 5, c + 4, 10), (c - 1, 3, c + 6, 6), (c - 5, 9, c, 11)]:
        cv.line(x0, y0 + lift, x1, y1 + lift, hr[1])
    back = cv.ell(c, 27 + lift, 17.6, 17) | cv.capsule(c - 15, 26, c - 16, 45, 3.4) | cv.capsule(c + 15, 26, c + 16, 45, 3.4)
    cv.part("hairback", back, "hair", rad=9, soft=1.6, cuts=(0.30, 0.56, 0.86), tex=0.05, seed=63)
    cv.part("neck", cv.rect(c - 4, 40, c + 4, 51), "skin", rad=4, bias=-0.18)
    col = cv.ell(c, 51.5, 9.0, 3.8) | cv.rect(c - 6.5, 47, c + 6.5, 51)
    cv.part("collar", col, "knit", rad=4, soft=1.0, bias=0.08)
    cv.hline(c - 6, c + 6, 50, kn[1]); cv.hline(c - 5, c - 2, 48, kn[3])
    # ---- face ----
    face = cv.ell(c, 28, 13.4, 13.6) | cv.ell(c, 33, 11.2, 12.6)
    cv.part("face", face, "skin", rad=11, soft=2.2, cuts=(0.16, 0.42, 0.86), bias=0.06)
    # front fringe swept from viewer-left across the brow + face-framing locks
    fr = cv.ell(c, 24 + lift, 15.8, 14.6)
    line = 17.5 + lift + 0.32 * (cv.X - c) + np.where(((cv.X - c) % 5) == 2, 1.6, 0) + np.where(cv.X > c + 6, 1.4, 0)
    fringe = (fr & (cv.Y < line))
    fringe |= cv.capsule(c - 13.5, 18, c - 14.0, 40, 2.3) | cv.capsule(c + 13.0, 20, c + 14.0, 41, 2.2)
    cv.part("fringe", fringe, "hair", noedge=("hairback", "bun"), rad=7, soft=1.2, cuts=(0.28, 0.54, 0.86), tex=0.05, seed=67)
    for (x0, y0, x1, y1) in [(c - 9, 13, c - 4, 20), (c - 2, 12, c + 4, 21), (c + 5, 13, c + 9, 22),
                             (c - 14, 24, c - 14, 36), (c + 13, 25, c + 14, 37)]:
        cv.line(x0, y0 + lift, x1, y1 + lift, hr[1])
    cv.puts([(c - 8, 12 + lift), (c - 7, 12 + lift), (c - 6, 13 + lift), (c - 10, 13 + lift), (c - 15, 26), (c - 15, 27)], hr[4])
    # shadow cast by the fringe
    fid, frid = cv.names["face"], cv.names["fringe"]
    for x in range(c - 12, c + 13):
        for y in range(10, 30):
            if cv.own[y, x] == fid and cv.own[y - 1, x] == frid:
                cv.put(x, y, sk[1]); cv.put(x, y + 1, sk[2])
                break
    # ---- cheeks, freckles, nose ----
    for s in (-1, 1):
        bx = c + s * 8
        for y in (36, 37):
            for x in range(bx - 2, bx + 3):
                if cv.own[y, x] == fid:
                    cv.put(x, y, mix(cv.get(x, y), BLUSH, 0.45 if abs(x - bx) < 2 else 0.25))
    for (x, y) in [(c - 9, 34), (c - 7, 35), (c - 10, 36), (c + 9, 34), (c + 7, 35), (c + 10, 36), (c - 3, 32), (c + 3, 32)]:
        cv.put(x, y, mix(cv.get(x, y), FRECKLE, 0.75))
    cv.puts([(c - 1, 29), (c - 1, 30), (c - 1, 31), (c - 1, 32)], sk[3])
    cv.puts([(c + 1, 32), (c + 1, 33), (c + 2, 34)], sk[1]); cv.puts([(c - 1, 35), (c, 35), (c + 1, 35)], sk[1])
    cv.put(c - 2, 34, sk[1]); cv.put(c - 1, 34, sk[4])
    # ---- mouth ----
    p_mouth(cv, c, 40, expr, talk)
    # ---- eyes + brows ----
    ey = {"neutral": 27, "warm": 26, "concern": 26, "surprised": 25}[expr]
    p_eye(cv, c - 11, ey, expr, -1)
    p_eye(cv, c + 4, ey, expr, 1)
    by = {"neutral": 24, "warm": 23, "concern": 23, "surprised": 22}[expr] + lift
    p_brows(cv, c, by, expr)
    if expr == "concern":
        cv.puts([(c - 1, 24), (c + 1, 24), (c, 25)], sk[1])
    cv.outline()
    # flyaway strands
    cv.puts([(c - 14, 6 + lift), (c - 15, 5 + lift), (c + 12, 13), (c + 13, 12)], hr[1])
    if expr == "warm":
        cv.puts([(56, 22), (57, 21), (58, 20), (57, 25), (59, 25), (60, 25)], SPARK2)
    if expr == "surprised":
        cv.puts([(56, 14), (56, 15), (56, 16), (56, 18), (59, 16), (60, 15), (61, 14)], SPARK2)
    if expr == "concern":
        cv.puts([(50, 20), (49, 21), (50, 21), (51, 21), (50, 22)], SWEAT); cv.put(49, 21, SWEAT_HI)
    return cv


# ==========================================================================
# output
# ==========================================================================
CAST_REF = "/tmp/claude-0/designs/cast-reference.png"   # 3x contact sheet of the approved cast


def foot_point(cv):
    """x = centre between the boots on the sole row, y = sole row."""
    y = cv.h - 1
    shoe_ids = [pid for n, pid in cv.names.items() if n.startswith("shoe")]
    xs = [x for x in range(cv.w) if cv.alpha[y, x] and cv.own[y, x] in shoe_ids]
    if not xs:
        xs = [x for x in range(cv.w) if cv.alpha[y, x]]
    return [int(round((min(xs) + max(xs)) / 2)), y]


def check_height(img, want, name):
    a = np.array(img)[..., 3] > 0
    rows = np.nonzero(a.any(axis=1))[0]
    # standing height = bun top to soles; nothing in cells 0-5 may poke above the bun
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
    battle = [b_front("idle"), b_front("talk"), b_front("tell"), b_front("hit"), b_side(), b_back()]
    world = [w_front("idle"), w_front("talk"), w_front("tell"), w_front("hit"), w_side(), w_back()]
    for prefix, group, hgt in (("battle", battle, BODY_H), ("world", world, WORLD_H)):
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            check_height(img, hgt, name)
            img.save(os.path.join(OUT, name))
            feet[name] = foot_point(cv)
            cells[name] = img
    ent = b_entrance()
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
        assert box and box[1] >= 36 and box[3] <= 46, ("talk diff outside the mouth", e, box)
        t_img.save(os.path.join(OUT, "talk", "ta-%d.png" % i))
        cells["talk-%d.png" % i] = t_img
        print("talk", i, "changed", n, "px in", box)
    base = cells["world-0.png"]
    for key, extra in (("blink", "blink"), ("pose1", "sip"), ("pose2", "shoulder")):
        img = w_front("idle", extra).image()
        assert img.size == base.size
        box, n = diff_box(base, img)
        print("idle", key, "changed", n, "px in", box)
        img.save(os.path.join(OUT, "idle", "ta-%s.png" % key))
        cells["idle-%s.png" % key] = img
    with open(os.path.join(OUT, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    contact_sheet(cells, feet)
    return cells, feet


def contact_sheet(cells, feet, S=3):
    """3x sheet: battle row, world row (+ idle extras), portrait row (+ talk), each beside the cast."""
    from PIL import ImageFont
    BG = (44, 44, 62, 255)
    GROUND = (70, 70, 96, 255)
    font = ImageFont.load_default()
    ref = Image.open(CAST_REF).convert("RGBA") if os.path.exists(CAST_REF) else None

    def up(im):
        return im.resize((im.width * S, im.height * S), Image.NEAREST)

    def cast(box):
        # the cast reference is already a 3x sheet; crop it 1:1 so the scale matches
        return (ref.crop(box), True) if ref is not None else None

    r1 = [(up(cells["battle-%d.png" % i]), "battle-%d" % i) for i in range(6)]
    r1.append((up(cells["entrance.png"]), "cell 12 ta-entrance"))
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
    d.text((pad, 6), "Gwen the Red, seventh-year grad TA (ta) -- 3x; cast crops from designs/cast-reference.png at the same 3x",
           fill=(220, 220, 236, 255), font=font)
    y = pad + 20
    for r, rh in zip(rows, heights):
        x = pad
        base = y + rh - 18
        if r is not r3:
            d.rectangle([0, base, W, base + 1], fill=GROUND)
        for im, label in r:
            top = base - im.height if r is not r3 else y
            sheet.alpha_composite(im, (x, top))
            d.text((x, base + 4), label, fill=(200, 200, 220, 255), font=font)
            x += im.width + pad
        y += rh
    sheet.convert("RGB").save(os.path.join(HERE, "sheet.png"))


if __name__ == "__main__":
    cells, feet = build()
    for k, v in feet.items():
        print(k, cells[k].size, v)
