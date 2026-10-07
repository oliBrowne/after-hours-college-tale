#!/usr/bin/env python3
"""Professor Eric -- procedural pixel-art sprites for "After Hours - College Tale".

Everything is drawn at its final pixel size with aliased shapes and per-pixel
placement.  Nothing that is drawn is ever resampled; the only scaling in this
file is the nearest-neighbour blow-up of the contact sheet.

Outputs (in ./out next to this script):
  battle-0..5.png   80px tall battle cells   (0 idle, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  world-0..5.png    46px tall overworld cells (same poses)
  portrait-0..3.png 64x64 portraits          (0 neutral, 1 warm, 2 concern, 3 surprised)
  feet.json         foot point [x, y] for every body cell
  sheet.png         3x contact sheet with reference cast for scale
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
REF = os.path.join(HERE, "ref")

# --------------------------------------------------------------------------
# palette
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline
INK2 = (23, 26, 43)         # #171a2b

RAMP = {
    # 0 = line/darkest, 1 = shadow, 2 = mid, 3 = light, 4 = highlight
    "cap":    [(38, 44, 34), (66, 78, 56), (94, 110, 78), (124, 140, 100), (158, 172, 128)],
    "capdk":  [(30, 34, 28), (50, 58, 44), (70, 82, 60), (92, 106, 76), (116, 130, 94)],
    "patch":  [(70, 56, 40), (150, 128, 92), (192, 170, 124), (222, 204, 160), (240, 228, 190)],
    "skin":   [(88, 38, 40), (156, 74, 62), (200, 108, 84), (228, 146, 112), (246, 182, 146)],
    "beard":  [(70, 68, 84), (138, 136, 150), (186, 184, 192), (222, 220, 222), (248, 246, 240)],
    "hair":   [(66, 64, 80), (112, 110, 126), (150, 148, 162), (188, 186, 196), (218, 216, 222)],
    "fleece": [(20, 26, 70), (40, 56, 132), (58, 84, 176), (84, 116, 212), (126, 158, 236)],
    "tee":    [(18, 16, 24), (34, 32, 42), (50, 48, 60), (68, 66, 80), (90, 88, 102)],
    "pants":  [(62, 50, 36), (112, 94, 64), (150, 130, 90), (182, 164, 118), (208, 192, 148)],
    "shoe":   [(36, 22, 20), (78, 46, 32), (116, 72, 44), (154, 104, 62), (186, 136, 88)],
    "probe":  [(18, 18, 26), (58, 62, 80), (96, 104, 128), (140, 148, 172), (196, 204, 222)],
    "metal":  [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "cable":  [(16, 18, 28), (46, 50, 70), (76, 82, 108), (118, 126, 156), (160, 170, 198)],
}
FRAME = (34, 28, 36)        # glasses frame
FRAME_HI = (92, 80, 84)
LENS = (214, 226, 236)
LENS2 = (150, 176, 204)
BLUSH = (214, 104, 92)
BLUSH2 = (190, 84, 78)
EYE = (30, 22, 30)
WHITE = (250, 248, 244)
MOUTH = (74, 26, 34)
TONGUE = (196, 92, 96)
TEETH = (240, 236, 228)
YELLOW = (240, 196, 60)
YELLOW_DK = (176, 120, 30)
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
# shared bits
# --------------------------------------------------------------------------
def coil(cv, pts, r=1.6, pitch=3.0, name="cable", ramp="cable", stripe_phase=0.0):
    """A coiled probe cable along a polyline: a band whose colour alternates
    every `pitch` pixels of arc length, which reads as coil turns."""
    rp = RAMP[ramp]
    m = cv.chain(pts, r)
    # arc length parameter per pixel (nearest segment)
    best = np.full(m.shape, 1e9)
    sval = np.zeros(m.shape)
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        vx, vy = x1 - x0, y1 - y0
        L = math.hypot(vx, vy) or 1e-9
        t = np.clip(((cv.X - x0) * vx + (cv.Y - y0) * vy) / (L * L), 0, 1)
        d = (cv.X - x0 - t * vx) ** 2 + (cv.Y - y0 - t * vy) ** 2
        upd = d < best
        best[upd] = d[upd]
        sval[upd] = acc + t[upd] * L
        acc += L
    # stripes are diagonal across the band: add a little perpendicular term
    ph = ((sval + stripe_phase + 0.5 * (cv.X + cv.Y) * 0.0) / pitch) % 1.0
    lv = np.where(ph < 0.34, 3, np.where(ph < 0.67, 2, 1))
    lv = np.where(m, lv, 0)
    cv.part(name, m, rp, edge="ink", lv=lv)
    return m


def assert_height(img, h, name):
    bb = img.getbbox()
    top = bb[1]
    bot = bb[3] - 1
    assert bot == img.height - 1, (name, "feet not on bottom row", bb)
    return top


# ==========================================================================
# BATTLE  (80 px standing height)
# ==========================================================================
BW, BH = 76, 88
BT = BH - 80          # cap top row


def b_eyes(cv, c, t, pose):
    sk = RAMP["skin"]
    E = EYE
    for side in (-1, 1):
        ex = c + side * 7          # eye column pair is ex-1, ex
        if pose in ("idle", "talk"):
            # dark eye 2x3 with catch-light, upper lid, smile crease below
            for y in range(t + 19, t + 22):
                cv.put(ex - 1, y, E); cv.put(ex, y, E)
            cv.put(ex - 1, t + 19, WHITE)
            cv.hline(ex - 2, ex + 1, t + 19, E) if False else None
            cv.put(ex - 2, t + 19, sk[0]); cv.put(ex + 1, t + 19, sk[0])
            cv.hline(ex - 1, ex, t + 22, sk[1])
            cv.put(ex + side * 3, t + 21, sk[1])
        elif pose in ("tell",):
            pass  # hidden by the glint
        elif pose == "hit":
            m = ["KK..", "..KK", "KK.."]
            for j, row in enumerate(m):
                for i, ch in enumerate(row):
                    if ch == "K":
                        x = ex - 2 + i if side < 0 else ex + 1 - i
                        cv.put(x, t + 19 + j, E)


def b_glasses(cv, c, t, glint=False, tilt=0):
    sk = RAMP["skin"]
    y0, y1 = t + 18, t + 23
    for side in (-1, 1):
        xa, xb = (c - 12, c - 3) if side < 0 else (c + 3, c + 12)
        dy = tilt if side > 0 else 0
        for y in range(y0 + 1, y1):
            for x in range(xa + 1, xb):
                if glint:
                    cv.put(x, y + dy, LENS2 if (x - xa + y) % 6 else LENS)
                else:
                    cv.put(x, y + dy, mix(cv.get(x, y + dy), LENS, 0.16))
        cv.hline(xa, xb, y0 + dy, FRAME)
        cv.hline(xa, xb, y1 + dy, FRAME)
        cv.vline(xa, y0 + dy, y1 + dy, FRAME)
        cv.vline(xb, y0 + dy, y1 + dy, FRAME)
        cv.put(xa + 1, y0 + dy, FRAME_HI); cv.put(xa + 2, y0 + dy, FRAME_HI)
        if glint:
            cv.puts([(xa + 1, y0 + 1), (xa + 2, y0 + 1), (xa + 1, y0 + 2)], WHITE)
            cv.puts([(xa + 4, y1 - 1), (xa + 5, y1 - 2), (xa + 6, y1 - 3), (xa + 7, y1 - 4)], WHITE)
        else:
            cv.put(xa + 1, y0 + 1 + dy, LENS)
    cv.hline(c - 2, c + 2, t + 19, FRAME)
    cv.put(c - 13, t + 19, FRAME); cv.put(c + 13, t + 19 + tilt, FRAME)


def b_brows(cv, c, t, pose):
    bd = RAMP["beard"]
    # (dx from centre, dy) for the viewer-left brow; mirrored for the right
    if pose == "hit":
        top = [(-11, 18), (-10, 17), (-9, 17), (-8, 16), (-7, 16), (-6, 17), (-5, 17)]
    elif pose == "tell":
        top = [(-11, 17), (-10, 16), (-9, 16), (-8, 16), (-7, 16), (-6, 16), (-5, 17)]
    else:
        top = [(-11, 17), (-10, 16), (-9, 16), (-8, 16), (-7, 16), (-6, 17), (-5, 17)]
    for i, (dx, dy) in enumerate(top):
        cv.put(c + dx, t + dy, bd[4] if i < 4 else bd[3])
        cv.put(c - dx, t + dy, bd[3] if i < 4 else bd[2])
        if 0 < i < 6:
            cv.put(c + dx, t + dy + 1, bd[2])
            cv.put(c - dx, t + dy + 1, bd[1])


def b_mouth(cv, c, t, pose):
    y = t + 31
    if pose == "idle":
        cv.hline(c - 2, c + 2, y, MOUTH)
        cv.put(c - 3, y - 1, MOUTH); cv.put(c + 3, y - 1, MOUTH)
        cv.hline(c - 1, c + 1, y + 1, RAMP["skin"][2])
    elif pose == "tell":
        # knowing grin, one side higher
        cv.hline(c - 3, c + 3, y, MOUTH)
        cv.hline(c - 2, c + 2, y, TEETH)
        cv.put(c - 4, y - 1, MOUTH); cv.put(c + 4, y - 1, MOUTH); cv.put(c + 5, y - 2, MOUTH)
        cv.hline(c - 2, c + 2, y + 1, MOUTH)
    elif pose == "talk":
        cv.hline(c - 2, c + 2, y, TEETH)
        cv.hline(c - 3, c + 3, y + 1, MOUTH)
        cv.hline(c - 2, c + 2, y + 2, MOUTH)
        cv.hline(c - 1, c + 1, y + 2, TONGUE)
        cv.put(c - 3, y, MOUTH); cv.put(c + 3, y, MOUTH)
    elif pose == "hit":
        cv.hline(c - 3, c + 3, y, MOUTH)
        cv.hline(c - 3, c + 3, y + 1, MOUTH)
        for x in range(c - 2, c + 3):
            cv.put(x, y + ((x - c) % 2), TEETH)


def b_head(cv, cx, T, pose, hx=0, hy=0, cap_ang=0.0, cap_dx=0):
    c = cx + hx
    t = T + hy
    sk = RAMP["skin"]
    bd = RAMP["beard"]
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 14.6, t + 23, 2.6, 3.6), "skin", bias=0.05)
        cv.put(c + s * 14, t + 23, sk[1])
    face = cv.ell(c, t + 21, 14.5, 13.5)
    cv.part("face", face, "skin", rad=10, soft=1.6, cuts=(0.30, 0.52, 0.86))
    for s in (-1, 1):
        cv.part("sidehair%d" % s, cv.ell(c + s * 13.6, t + 16, 2.5, 3.6) & cv.half(y=t + 12), "hair",
                noedge=("face",), bias=0.05)
    # forehead shadow under the brim
    for x in range(c - 13, c + 14):
        for y in (t + 15, t + 16):
            if cv.own[y, x] == cv.names["face"]:
                cv.put(x, y, sk[1])
    # nose: big round ruddy
    nose = cv.ell(c, t + 25.2, 3.2, 2.9)
    cv.part("nose", nose, "skin", edge=None, rad=3, soft=0.8, bias=0.12)
    cv.puts([(c - 1, t + 24), (c - 2, t + 25), (c - 1, t + 25)], sk[4])
    cv.puts([(c + 3, t + 25), (c + 3, t + 26), (c + 2, t + 27), (c + 1, t + 28), (c, t + 28), (c - 1, t + 28), (c - 2, t + 27)], sk[0])
    cv.puts([(c + 2, t + 26), (c + 1, t + 27)], sk[1])
    # cheeks
    for s in (-1, 1):
        for x in range(c + s * 8 - 1, c + s * 8 + 2):
            if cv.own[t + 24, x] == cv.names["face"]:
                cv.put(x, t + 24, BLUSH)
    # beard
    beard = cv.ell(c, t + 29, 15.6, 11.6) & cv.half(y=t + 23)
    for s in (-1, 1):
        beard |= cv.capsule(c + s * 14, t + 18, c + s * 13.6, t + 27, 2.2)
        beard &= ~cv.ell(c + s * 7, t + 23, 6.2, 3.8)
    beard |= cv.ell(c, t + 37.5, 9.5, 3.6)
    cv.part("beard", beard, "beard", rad=9, soft=1.6, noedge=("sidehair-1", "sidehair1"),
            cuts=(0.28, 0.50, 0.82))
    st = cv.ell(c - 4, t + 28.2, 5, 2.5) | cv.ell(c + 4, t + 28.2, 5, 2.5)
    cv.part("stache", st, "beard", edge=bd[1], noedge=("beard",), rad=2.4, bias=0.08)
    cv.put(c, t + 27, bd[1])
    # strands, greyer under the mouth (as in the photo)
    for (x, y) in [(c - 1, t + 33), (c + 1, t + 34), (c, t + 35), (c - 3, t + 34), (c + 3, t + 33),
                   (c - 7, t + 35), (c + 6, t + 36), (c - 10, t + 31), (c + 10, t + 32), (c - 4, t + 37),
                   (c + 4, t + 38), (c - 12, t + 28), (c + 12, t + 29), (c + 9, t + 28), (c - 2, t + 39)]:
        if cv.own[y, x] == cv.names["beard"] and cv.get(x, y) != bd[0]:
            cv.put(x, y, bd[1] if cv.get(x, y) in (bd[2], bd[1]) else bd[2])
    b_mouth(cv, c, t, pose)
    b_glasses(cv, c, t, glint=(pose == "tell"), tilt=0)
    b_eyes(cv, c, t, pose)
    b_brows(cv, c, t, pose)
    if pose == "tell":
        sx, sy = c - 15, t + 17
        cv.puts([(sx, sy - 2), (sx, sy - 1), (sx, sy + 1), (sx, sy + 2), (sx - 2, sy), (sx - 1, sy),
                 (sx + 1, sy), (sx + 2, sy)], SPARK2)
        cv.put(sx, sy, WHITE)
    b_cap_front(cv, c + cap_dx, t, cap_ang)


def b_cap_front(cv, c, t, ang=0.0):
    ox, oy = c, t + 12

    def rot(px, py):
        ca, sa = math.cos(ang), math.sin(ang)
        return ox + (px - ox) * ca - (py - oy) * sa, oy + (px - ox) * sa + (py - oy) * ca

    def ell(px, py, rx, ry):
        x, y = rot(px, py)
        return cv.ell(x, y, rx, ry, ang)

    def hp(py, below):
        x, y = rot(c, py)
        nx, ny = -math.sin(ang), math.cos(ang)
        d = (cv.X - x) * nx + (cv.Y - y) * ny
        return d >= 0 if below else d <= 0

    cr = RAMP["cap"]
    cd = RAMP["capdk"]
    crown = ell(c, t + 13.6, 15.4, 13.65) & hp(t + 12.4, False)
    cv.part("crown", crown, "cap", rad=10, soft=1.6, cuts=(0.30, 0.52, 0.84), tex=0.05, seed=3)
    # brim: a crescent dipping toward the viewer in the middle
    brim = ell(c, t + 11.2, 14.4, 4.8) & hp(t + 11.2, True)
    lv = np.where(brim, 3, 0)
    lv = np.where(brim & (cv.X < c - 3), 4, lv)
    # top surface lit on the left, darker toward the right, darker front lip
    X, Y = cv.X, cv.Y
    lv = np.where(brim & (X > c + 4), 2, lv)
    lip = brim & ~(ell(c, t + 10.2, 14.4, 4.8))
    lv = np.where(lip, 1, lv)
    cv.part("brim", brim, "cap", lv=lv)
    # stitch rows on the brim
    for x in range(c - 8, c + 9, 2):
        yy = t + 13 + (1 if abs(x - c) < 6 else 0)
        px, py = rot(x, yy)
        px, py = int(round(px)), int(round(py))
        if cv.own[py, px] == cv.names["brim"]:
            cv.put(px, py, cr[2] if x < c + 4 else cr[1])
    for (a, b) in [((c - 1, t + 1), (c - 9, t + 11)), ((c + 1, t + 1), (c + 9, t + 11))]:
        p0 = rot(*a); p1 = rot(*b)
        cv.line(round(p0[0]), round(p0[1]), round(p1[0]), round(p1[1]), cr[1])
    # patch + embroidered mountain as rotated polygons (no holes when tilted)
    pr = RAMP["patch"]
    corners = [rot(c - 4, t + 4), rot(c + 4, t + 4), rot(c + 4, t + 9), rot(c - 4, t + 9)]
    pm = cv.poly(corners)
    cv.fill(pm, pr[2])
    if ang == 0:
        cv.hline(c - 4, c + 4, t + 4, pr[3]); cv.vline(c - 4, t + 4, t + 9, pr[3])
        cv.hline(c - 4, c + 4, t + 9, pr[1]); cv.vline(c + 4, t + 5, t + 9, pr[1])
    mnt = cv.poly([rot(c - 3, t + 8), rot(c, t + 5), rot(c + 3, t + 8)])
    cv.fill(mnt & pm, (62, 80, 58))
    px, py = rot(c, t + 5)
    cv.put(px, py, WHITE)
    px, py = rot(c, t + 1)
    cv.put(px, py, cr[4])


def b_probe(cv, x0, y0, x1, y1, name="probe", r=2.3):
    """Chunky scope probe from cable end (x0,y0) to tip (x1,y1):
    strain relief, body with a yellow channel ring, tapered nose, silver hook."""
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    P = lambda k: (x0 + ux * k, y0 + uy * k)
    a, b = P(0), P(L * 0.72)
    body = cv.capsule(a[0], a[1], b[0], b[1], r * 0.75, r)
    nose_end = P(L - 3)
    nose = cv.capsule(b[0], b[1], nose_end[0], nose_end[1], r * 0.9, r * 0.45)
    cv.part(name, body | nose, "probe", edge="ink", rad=r, soft=0.6, light=(-0.75, -0.45, 0.55),
            cuts=(0.25, 0.5, 0.8))
    # yellow channel ring at ~1/3
    ring = (body) & cv.capsule(*P(L * 0.30), *P(L * 0.36), r + 1)
    edge_px = ring & (cv.col[..., 0] == INK[0]) & (cv.col[..., 1] == INK[1])
    cv.fill(ring & ~edge_px, YELLOW)
    # darker nose cone
    nm = nose & ~body
    cv.fill(nm & ~((cv.col[..., 0] == INK[0]) & (cv.col[..., 1] == INK[1])), RAMP["probe"][1])
    # silver hook tip
    mt = RAMP["metal"]
    for k in range(int(L) - 3, int(L) + 1):
        x, y = P(k)
        cv.put(x, y, mt[3] if k < L - 1 else mt[4])
    hx, hy = P(L)
    cv.put(hx + uy * 1.2, hy - ux * 1.2, mt[2])


def b_hand(cv, x, y, name, rx=3.7, ry=3.7, fist=True):
    m = cv.ell(x, y, rx, ry)
    cv.part(name, m, "skin", edge="ink", rad=3, soft=0.8, bias=0.04)
    if fist:
        cv.put(x - 1, y, RAMP["skin"][1]); cv.put(x + 1, y, RAMP["skin"][1])
    return m


def b_arm(cv, name, pts, r=4.5):
    m = cv.chain(pts, r)
    cv.part(name, m, "fleece", edge="dark", rad=4, soft=1.0, cuts=(0.30, 0.55, 0.88), tex=0.06, seed=len(name) * 7 + int(pts[0][0]))
    # cuff
    (xa, ya), (xb, yb) = pts[-2], pts[-1]
    L = math.hypot(xb - xa, yb - ya)
    ux, uy = (xb - xa) / L, (yb - ya) / L
    cuff = m & cv.capsule(xb - ux * 1.5, yb - uy * 1.5, xb, yb, r + 0.5) & ~cv.capsule(xa, ya, xb - ux * 1.5, yb - uy * 1.5, r)
    cv.fill(cuff & (cv.col[..., 0] >= 0), RAMP["fleece"][1])
    return m


def b_front(pose):
    cv = Cv(BW, BH)
    cx, T = 38, BT
    hx = hy = 0
    cap_ang, cap_dx = 0.0, 0
    if pose == "hit":
        hx, hy = 2, 0
        cap_ang, cap_dx = 0.20, 1
    fl = RAMP["fleece"]
    # ---- cable (behind) ----
    if pose in ("idle", "talk"):
        pass  # cable is draped in front of the leg, drawn after the trousers
    elif pose == "tell":
        coil(cv, [(cx - 26, T + 34), (cx - 31, T + 42), (cx - 32, T + 51), (cx - 30, T + 61),
                  (cx - 25, T + 69), (cx - 19, T + 74)], r=1.7, pitch=3.0)
    elif pose == "hit":
        coil(cv, [(cx - 28, T + 42), (cx - 32, T + 50), (cx - 31, T + 59), (cx - 26, T + 67),
                  (cx - 18, T + 73)], r=1.7, pitch=3.0)
    # ---- legs + shoes ----
    pants = cv.poly([(cx - 13, T + 57), (cx + 13, T + 57), (cx + 12, T + 75), (cx + 2, T + 75),
                     (cx + 1, T + 66), (cx - 1, T + 66), (cx - 2, T + 75), (cx - 12, T + 75)])
    pants &= ~cv.rect(cx, T + 67, cx, T + 80)
    cv.part("pants", pants, "pants", rad=5, soft=1.0, cuts=(0.32, 0.56, 0.9), tex=0.04, seed=9)
    pr = RAMP["pants"]
    cv.vline(cx - 1, T + 62, T + 66, pr[1]); cv.vline(cx + 1, T + 63, T + 66, pr[1])
    cv.vline(cx - 7, T + 67, T + 73, pr[1]); cv.vline(cx + 7, T + 66, T + 73, pr[0])
    cv.put(cx - 8, T + 68, pr[3]); cv.put(cx - 8, T + 69, pr[3])
    for s in (-1, 1):
        sx = cx + s * 7.5
        sh = cv.ell(sx, T + 77.4, 7.4, 3.6) & cv.half(y=T + 79, below=False)
        cv.part("shoe%d" % s, sh, "shoe", rad=3, soft=0.8, cuts=(0.3, 0.55, 0.85))
        sr = RAMP["shoe"]
        cv.put(sx - 3, T + 76, sr[4]); cv.put(sx - 2, T + 75, sr[3])
    if pose in ("idle", "talk"):
        coil(cv, [(cx - 6, T + 58), (cx - 6, T + 64), (cx - 10, T + 70), (cx - 16, T + 70),
                  (cx - 20, T + 65), (cx - 20, T + 59)], r=1.7, pitch=3.0)
    # ---- torso ----
    torso = cv.ell(cx, T + 44, 19.5, 9.8) | (cv.ell(cx, T + 50, 23, 11.8) & cv.half(y=T + 60, below=False))
    cv.part("torso", torso, "fleece", rad=13, soft=2.0, cuts=(0.30, 0.52, 0.84), tex=0.07, seed=5)
    hem = torso & cv.half(y=T + 58)
    cv.part("hem", hem, "fleece", noedge=("torso",),
            lv=np.where(hem, 1, 0) + np.where(hem & (cv.X < cx - 4), 1, 0))
    for x in range(cx - 13, cx + 14, 3):
        if cv.own[T + 59, x] == cv.names["hem"]:
            cv.put(x, T + 59, fl[0])
    # belly: highlight crescent + shadow fold above the hem
    for x in range(cx - 15, cx - 8):
        cv.put(x, T + 45 + (cx - 11 - x) // 3, fl[3])
    for x in range(cx - 13, cx + 14):
        yy = T + 57 - (1 if abs(x - cx) > 9 else 0)
        if cv.own[yy, x] == cv.names["torso"]:
            cv.put(x, yy, fl[1])
    # collar + open zip showing the dark tee
    col = cv.ell(cx, T + 39.5, 11.5, 4.0)
    cv.part("collar", col, "fleece", rad=3, soft=0.8, bias=0.06)
    tee = cv.poly([(cx - 4, T + 40), (cx + 4, T + 40), (cx, T + 46)])
    cv.part("tee", tee, "tee", edge="dark", noedge=(), lv=np.where(tee, 1, 0))
    mt = RAMP["metal"]
    for y in range(T + 46, T + 55):
        cv.put(cx, y, mt[1] if y % 2 else fl[0])
    cv.puts([(cx, T + 46), (cx, T + 47)], mt[3]); cv.put(cx + 1, T + 47, mt[2]); cv.put(cx + 1, T + 48, mt[1])
    # ---- arms ----
    if pose in ("idle", "talk"):
        b_arm(cv, "armL", [(cx - 17, T + 39), (cx - 22, T + 47), (cx - 21, T + 53)])
        b_probe(cv, cx - 18, T + 54, cx - 31, T + 71)
        b_hand(cv, cx - 21, T + 57, "handL")
        cv.puts([(cx - 22, T + 58), (cx - 20, T + 58)], RAMP["skin"][1])
    elif pose == "tell":
        b_arm(cv, "armL", [(cx - 17, T + 39), (cx - 25, T + 42), (cx - 26, T + 35)])
        b_probe(cv, cx - 26, T + 36, cx - 25, T + 13)
        b_hand(cv, cx - 26, T + 31, "handL")
    elif pose == "hit":
        b_arm(cv, "armL", [(cx - 16, T + 39), (cx - 25, T + 42), (cx - 30, T + 36)])
        b_probe(cv, cx - 29, T + 39, cx - 36, T + 20)
        b_hand(cv, cx - 30, T + 35, "handL")
    if pose == "idle":
        b_arm(cv, "armR", [(cx + 17, T + 39), (cx + 22, T + 47), (cx + 21, T + 53)])
        b_hand(cv, cx + 21, T + 57, "handR")
    elif pose == "tell":
        b_arm(cv, "armR", [(cx + 17, T + 39), (cx + 23, T + 47), (cx + 16, T + 52)])
        b_hand(cv, cx + 13, T + 52, "handR", rx=3.9, ry=3.3)
    elif pose == "talk":
        b_arm(cv, "armR", [(cx + 17, T + 39), (cx + 25, T + 46), (cx + 28, T + 38)])
        b_hand(cv, cx + 28, T + 34, "handR", rx=3.6, ry=3.6, fist=False)
        fing = cv.empty()
        for k, (fx, top) in enumerate([(cx + 26, T + 27), (cx + 28, T + 26), (cx + 30, T + 27)]):
            fing |= cv.rect(fx, top, fx + 1, T + 33)
        fing |= cv.capsule(cx + 31, T + 35, cx + 33, T + 32, 1.0)
        cv.part("fingers", fing & ~cv.names.get("x", cv.empty()), "skin", edge="ink", noedge=("handR",), rad=1.5, soft=0.5, bias=0.06)
    elif pose == "hit":
        b_arm(cv, "armR", [(cx + 18, T + 40), (cx + 27, T + 41), (cx + 29, T + 33)])
        b_hand(cv, cx + 29, T + 30, "handR", rx=3.5, ry=4.2, fist=False)
    # ---- head ----
    b_head(cv, cx, T, pose, hx, hy, cap_ang, cap_dx)
    if pose == "hit":
        sx, sy = cx + 20, T + 9
        cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx + 1, sy + 1),
                 (sx - 1, sy + 2), (sx, sy + 2), (sx + 1, sy + 2), (sx, sy + 3)], SWEAT)
        cv.put(sx - 1, sy + 1, SWEAT_HI)
    cv.outline()
    return cv


def b_side():
    """Side view facing RIGHT."""
    cv = Cv(BW, BH)
    c, t = 34, BT
    sk, bd, fl = RAMP["skin"], RAMP["beard"], RAMP["fleece"]
    # back leg + shoe
    cv.part("legB", cv.poly([(c - 9, t + 57), (c + 1, t + 57), (c + 0, t + 75), (c - 9, t + 75)]), "pants",
            lv=None, rad=4, cuts=(0.4, 0.62, 0.95))
    cv.part("shoeB", cv.ell(c - 2, t + 77.4, 8.2, 3.6) & cv.half(y=t + 79, below=False), "shoe",
            rad=3, cuts=(0.4, 0.62, 0.95))
    # front leg + shoe
    leg = cv.poly([(c - 6, t + 57), (c + 6, t + 57), (c + 6, t + 75), (c - 4, t + 75)])
    cv.part("legF", leg, "pants", rad=5, soft=1.0, cuts=(0.32, 0.56, 0.9), tex=0.04, seed=11)
    pr = RAMP["pants"]
    cv.vline(c + 3, t + 64, t + 73, pr[1])
    sh = cv.ell(c + 4, t + 77.4, 8.6, 3.6) & cv.half(y=t + 79, below=False)
    cv.part("shoeF", sh, "shoe", rad=3, soft=0.8, cuts=(0.3, 0.55, 0.85))
    cv.puts([(c + 6, t + 75), (c + 8, t + 76)], RAMP["shoe"][4])
    cv.hline(c - 3, c + 11, t + 78, RAMP["shoe"][1])
    # torso: flat back, round belly forward
    torso = (cv.ell(c - 1, t + 44, 13.5, 9.8) | (cv.ell(c + 3, t + 50, 15.5, 11.8) & cv.half(y=t + 60, below=False))
             | (cv.rect(c - 13, t + 44, c, t + 60) & cv.ell(c - 1, t + 50, 13.5, 13)))
    cv.part("torso", torso, "fleece", rad=12, soft=2.0, cuts=(0.30, 0.52, 0.84), tex=0.07, seed=15)
    hem = torso & cv.half(y=t + 58)
    cv.part("hem", hem, "fleece", noedge=("torso",),
            lv=np.where(hem, 1, 0) + np.where(hem & (cv.X < c + 4), 1, 0))
    for x in range(c - 12, c + 18, 3):
        if cv.own[t + 59, x] == cv.names["hem"]:
            cv.put(x, t + 59, fl[0])
    for x in range(c + 2, c + 9):          # belly highlight
        cv.put(x, t + 45 + abs(x - c - 5) // 3, fl[3])
    for y in range(t + 50, t + 57):        # belly underside shadow
        x = c + 16 - (y - t - 50) // 2
        if cv.own[y, x] == cv.names["torso"]:
            cv.put(x, y, fl[1])
    # collar
    cv.part("collar", cv.ell(c - 1, t + 39, 9, 3.8), "fleece", rad=3, bias=0.06)
    # cable hanging behind the arm
    coil(cv, [(c + 2, t + 58), (c - 1, t + 63), (c - 6, t + 67), (c - 9, t + 72), (c - 8, t + 76)], r=1.7)
    # near arm (his left), hanging forward of the side seam
    b_arm(cv, "arm", [(c - 2, t + 40), (c - 1, t + 48), (c + 2, t + 54)])
    b_probe(cv, c + 1, t + 55, c + 16, t + 66)
    b_hand(cv, c + 3, t + 57, "hand")
    cv.put(c + 5, t + 57, sk[1]); cv.put(c + 5, t + 58, sk[1])
    # ---- head (profile) ----
    neck = cv.rect(c - 8, t + 26, c + 2, t + 38) & ~cv.ell(c - 12, t + 36, 5, 6)
    cv.part("neck", neck, "skin", rad=4, bias=-0.1)
    cv.part("collar2", cv.ell(c - 2, t + 38.5, 8.5, 3.0), "fleece", rad=3, bias=0.06)
    head = cv.ell(c, t + 20, 13.5, 12.8) | (cv.ell(c + 6, t + 20, 8.4, 10.4) & cv.half(y=t + 14))
    cv.part("head", head, "skin", rad=10, soft=1.6, cuts=(0.30, 0.52, 0.86), bias=0.12)
    # short white hair at the back of the head below the cap
    hair = cv.ell(c - 3, t + 18, 10.6, 10.4) & cv.half(x=c - 4, right=False) & cv.half(y=t + 11)
    hair |= cv.ell(c - 7, t + 24, 5.6, 4.2) & cv.half(y=t + 11)
    hair &= head | cv.ell(c - 7, t + 24, 5.6, 4.2)
    cv.part("hair", hair, "hair", noedge=("head",), rad=5, cuts=(0.32, 0.58, 0.9), tex=0.05, seed=31)
    for (x, y) in [(c - 10, t + 15), (c - 7, t + 19), (c - 11, t + 21), (c - 9, t + 24), (c - 6, t + 26)]:
        if cv.own[y, x] == cv.names["hair"]:
            cv.put(x, y, RAMP["hair"][1])
    # beard (jaw + chin, fuller forward)
    beard = (cv.ell(c + 5, t + 29, 10.5, 10.5) & cv.half(y=t + 22)) | cv.ell(c + 7, t + 36.5, 7.5, 4.2)
    beard |= cv.capsule(c + 1, t + 18, c + 1, t + 27, 2.0)
    beard &= ~cv.ell(c + 8, t + 22.5, 5, 3.4)
    cv.part("beard", beard, "beard", noedge=("hair",), rad=8, soft=1.6, cuts=(0.28, 0.5, 0.82))
    # nose: big, round, sticks out past the face
    nose = cv.ell(c + 14.6, t + 25, 2.9, 2.7)
    cv.part("nose", nose, "skin", edge="ink", noedge=("head",), rad=2.5, bias=0.12)
    cv.puts([(c + 14, t + 23), (c + 15, t + 24)], sk[4]); cv.puts([(c + 13, t + 27), (c + 14, t + 27)], sk[1])
    st = cv.ell(c + 11.5, t + 28.4, 4.6, 2.4)
    cv.part("stache", st, "beard", edge=bd[1], noedge=("beard",), rad=2.4, bias=0.08)
    # mouth
    cv.hline(c + 11, c + 13, t + 31, MOUTH)
    cv.put(c + 14, t + 30, MOUTH)
    for (x, y) in [(c + 6, t + 34), (c + 9, t + 36), (c + 4, t + 31), (c + 2, t + 36), (c + 11, t + 34), (c + 7, t + 38)]:
        if cv.own[y, x] == cv.names["beard"]:
            cv.put(x, y, bd[1] if cv.get(x, y) == bd[2] else bd[2])
    # ear (behind the sideburn)
    cv.part("ear", cv.ell(c - 3, t + 23, 2.4, 3.4), "skin", edge="dark", bias=0.05)
    cv.put(c - 3, t + 23, sk[1]); cv.put(c - 3, t + 24, sk[1])
    cv.part("sideburn", cv.capsule(c + 1, t + 17, c + 1.5, t + 25, 1.6), "beard", edge=bd[1],
            noedge=("hair", "beard"), rad=2, bias=0.04)
    # cheek blush
    cv.puts([(c + 8, t + 24), (c + 9, t + 24)], BLUSH)
    # glasses: narrow lens nearly edge-on + temple to the ear
    for x in range(c + 10, c + 13):
        for y in range(t + 19, t + 23):
            cv.put(x, y, mix(cv.get(x, y), LENS, 0.16))
    cv.hline(c + 9, c + 13, t + 18, FRAME); cv.hline(c + 9, c + 13, t + 23, FRAME)
    cv.vline(c + 9, t + 18, t + 23, FRAME); cv.vline(c + 13, t + 18, t + 23, FRAME)
    cv.hline(c - 1, c + 8, t + 19, FRAME)
    cv.put(c + 10, t + 18, FRAME_HI)
    # eye
    for y in range(t + 19, t + 22):
        cv.put(c + 11, y, EYE); cv.put(c + 12, y, EYE)
    cv.put(c + 11, t + 19, WHITE)
    cv.hline(c + 11, c + 12, t + 22, sk[1])
    cv.put(c + 10, t + 20, sk[1])
    # brow
    cv.hline(c + 8, c + 13, t + 16, bd[4]); cv.hline(c + 9, c + 12, t + 17, bd[2])
    cv.put(c + 14, t + 17, bd[3])
    # forehead shadow under brim
    for x in range(c + 2, c + 15):
        if cv.own[t + 15, x] == cv.names["head"]:
            cv.put(x, t + 15, sk[1])
    # ---- cap (profile) ----
    crown = cv.ell(c, t + 13.6, 14.4, 13.65) & cv.half(y=t + 12.4, below=False)
    cv.part("crown", crown, "cap", rad=10, soft=1.6, cuts=(0.30, 0.52, 0.84), tex=0.05, seed=3)
    cr = RAMP["cap"]
    brim = cv.poly([(c + 8, t + 10), (c + 17, t + 11), (c + 22, t + 13), (c + 21, t + 15), (c + 12, t + 15), (c + 6, t + 14)])
    lv = np.where(brim, 3, 0)
    lv = np.where(brim & (cv.Y >= t + 14), 1, lv)
    cv.part("brim", brim, "cap", lv=lv)
    cv.line(c - 1, t + 1, c + 4, t + 12, cr[1])        # seam
    cv.line(c - 9, t + 4, c - 11, t + 12, cr[1])
    pr = RAMP["patch"]
    for y in range(t + 4, t + 9):
        for x in range(c + 10, c + 13):
            cv.put(x, y, pr[2] if x < c + 12 else pr[1])
    cv.puts([(c + 10, t + 7), (c + 11, t + 6), (c + 11, t + 7), (c + 12, t + 7)], (62, 80, 58))
    cv.put(c, t + 1, cr[4])
    cv.outline()
    return cv


def b_back():
    cv = Cv(BW, BH)
    cx, T = 38, BT
    t = T
    hr, fl = RAMP["hair"], RAMP["fleece"]
    # cable + probe hang from his right hand (viewer right from behind)
    coil(cv, [(cx + 22, T + 58), (cx + 27, T + 62), (cx + 29, T + 68), (cx + 27, T + 74), (cx + 21, T + 77), (cx + 15, T + 77)], r=1.7)
    pants = cv.poly([(cx - 13, T + 57), (cx + 13, T + 57), (cx + 12, T + 75), (cx + 2, T + 75),
                     (cx + 1, T + 66), (cx - 1, T + 66), (cx - 2, T + 75), (cx - 12, T + 75)])
    pants &= ~cv.rect(cx, T + 67, cx, T + 80)
    cv.part("pants", pants, "pants", rad=5, soft=1.0, cuts=(0.32, 0.56, 0.9), tex=0.04, seed=19)
    pr = RAMP["pants"]
    cv.vline(cx, T + 58, T + 66, pr[0])
    for s in (-1, 1):   # back pockets
        cv.hline(cx + s * 4 - 3 * (s < 0), cx + s * 4 + 3 * (s > 0), T + 61, pr[1])
        cv.vline(cx + s * 10, T + 61, T + 64, pr[1])
    for s in (-1, 1):
        sx = cx + s * 7.5
        sh = cv.ell(sx, T + 77.6, 7.0, 3.4) & cv.half(y=T + 79, below=False)
        cv.part("shoe%d" % s, sh, "shoe", rad=3, soft=0.8, cuts=(0.3, 0.55, 0.85))
        cv.hline(sx - 3, sx + 3, T + 78, RAMP["shoe"][1])
    torso = cv.ell(cx, T + 44, 19.5, 9.8) | (cv.ell(cx, T + 50, 22.5, 11.8) & cv.half(y=T + 60, below=False))
    cv.part("torso", torso, "fleece", rad=13, soft=2.0, cuts=(0.30, 0.52, 0.84), tex=0.07, seed=23)
    hem = torso & cv.half(y=T + 58)
    cv.part("hem", hem, "fleece", noedge=("torso",),
            lv=np.where(hem, 1, 0) + np.where(hem & (cv.X < cx - 4), 1, 0))
    # yoke seam + spine shadow
    for x in range(cx - 15, cx + 16):
        y = T + 41 + (abs(x - cx) // 6)
        if cv.own[y, x] == cv.names["torso"]:
            cv.put(x, y, fl[1])
    for y in range(T + 46, T + 56):
        cv.put(cx, y, fl[1] if y % 3 else fl[2])
    # beard edges poke out past the jaw on both sides
    beard = cv.ell(cx, T + 30.5, 15.8, 9.2) & cv.half(y=T + 22)
    cv.part("beard", beard, "beard", rad=6, soft=1.2, cuts=(0.28, 0.5, 0.82))
    bd = RAMP["beard"]
    for (x, y) in [(cx - 13, T + 30), (cx + 13, T + 31), (cx - 11, T + 35), (cx + 11, T + 34), (cx - 14, T + 27), (cx + 14, T + 28)]:
        if cv.own[y, x] == cv.names["beard"]:
            cv.put(x, y, bd[1] if cv.get(x, y) == bd[2] else bd[2])
    neck = cv.rect(cx - 7, T + 24, cx + 7, T + 38)
    cv.part("neck", neck, "skin", rad=5, bias=-0.12)
    for x in range(cx - 6, cx + 7):          # neck crease
        if abs(x - cx) < 5:
            cv.put(x, T + 33, RAMP["skin"][1])
    cv.part("collar", cv.ell(cx, T + 38.5, 11, 3.6), "fleece", rad=3, bias=0.06)
    # arms
    b_arm(cv, "armL", [(cx - 17, T + 39), (cx - 22, T + 47), (cx - 21, T + 53)])
    b_hand(cv, cx - 21, T + 57, "handL")
    b_arm(cv, "armR", [(cx + 17, T + 39), (cx + 22, T + 47), (cx + 21, T + 53)])
    b_probe(cv, cx + 18, T + 54, cx + 31, T + 71)
    b_hand(cv, cx + 21, T + 57, "handR")
    # ears
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(cx + s * 14.6, T + 23, 2.6, 3.6), "skin", bias=0.05)
    # back of head: short white hair
    head = cv.ell(cx, T + 18, 14.2, 11.2)
    cv.part("head", head, "hair", rad=8, soft=1.4, cuts=(0.32, 0.56, 0.88), tex=0.06, seed=37)
    for (x, y) in [(cx - 6, T + 18), (cx + 4, T + 20), (cx - 9, T + 23), (cx + 9, T + 24), (cx - 2, T + 26),
                   (cx + 6, T + 27), (cx - 7, T + 27), (cx + 1, T + 22), (cx - 11, T + 19), (cx + 11, T + 21),
                   (cx - 4, T + 23), (cx + 3, T + 26)]:
        if cv.own[y, x] == cv.names["head"]:
            cv.put(x, y, hr[1])
    for x in range(cx - 13, cx + 14):
        if cv.own[T + 15, x] == cv.names["head"]:
            cv.put(x, T + 15, hr[1])
    # nape: hair thins into skin
    for x in range(cx - 5, cx + 6, 2):
        cv.put(x, T + 28, RAMP["skin"][2])
    for s_ in (-1, 1):
        cv.part("earB%d" % s_, cv.ell(cx + s_ * 14.4, T + 22, 2.6, 3.6), "skin", bias=0.05)
        cv.put(cx + s_ * 14, T + 22, RAMP["skin"][1])
    # glasses temples hooking over the ears
    cv.put(cx - 15, T + 19, FRAME); cv.put(cx + 15, T + 19, FRAME)
    # cap from behind with the strap-back opening
    cr = RAMP["cap"]
    crown = cv.ell(cx, T + 13.6, 15.4, 13.65) & cv.half(y=T + 13.4, below=False)
    cv.part("crown", crown, "cap", rad=10, soft=1.6, cuts=(0.30, 0.52, 0.84), tex=0.05, seed=29)
    opening = cv.ell(cx, T + 13.5, 4.2, 4.8) & cv.half(y=T + 9)
    cv.fill(opening, hr[2])
    cv.hline(cx - 3, cx + 3, T + 12, cr[0])
    cv.hline(cx - 2, cx + 2, T + 11, mix(cr[0], hr[2], 0.3))
    for y in range(T + 9, T + 13):
        cv.put(cx - 4 - (y > T + 10), y, cr[0]); cv.put(cx + 4 + (y > T + 10), y, cr[0])
    cv.put(cx - 4, T + 8, cr[1]); cv.put(cx + 4, T + 8, cr[1]); cv.hline(cx - 3, cx + 3, T + 8, cr[1])
    # strap + buckle
    cv.hline(cx - 6, cx + 6, T + 13, cr[1])
    cv.puts([(cx - 1, T + 13), (cx, T + 13), (cx + 1, T + 13)], RAMP["metal"][2])
    cv.line(cx - 1, T + 1, cx - 9, T + 11, cr[1])
    cv.line(cx + 1, T + 1, cx + 9, T + 11, cr[1])
    cv.put(cx, T + 1, cr[4])
    cv.outline()
    return cv


# ==========================================================================
# WORLD  (46 px standing height, redrawn small -- not scaled)
# ==========================================================================
WW, WH = 48, 50
WT = WH - 46


def w_cap_front(cv, c, t, ang=0.0):
    ox, oy = c, t + 6

    def rot(px, py):
        ca, sa = math.cos(ang), math.sin(ang)
        return ox + (px - ox) * ca - (py - oy) * sa, oy + (px - ox) * sa + (py - oy) * ca

    def ell(px, py, rx, ry):
        x, y = rot(px, py)
        return cv.ell(x, y, rx, ry, ang)

    def hp(py, below):
        x, y = rot(c, py)
        nx, ny = -math.sin(ang), math.cos(ang)
        d = (cv.X - x) * nx + (cv.Y - y) * ny
        return d >= 0 if below else d <= 0

    cr = RAMP["cap"]
    crown = ell(c, t + 7.6, 9.4, 7.65) & hp(t + 6.4, False)
    cv.part("crown", crown, "cap", rad=6, soft=1.0, cuts=(0.30, 0.52, 0.84))
    brim = ell(c, t + 5.6, 8.2, 3.0) & hp(t + 5.6, True)
    lv = np.where(brim, 3, 0)
    lv = np.where(brim & (cv.X < c - 2), 4, lv)
    lv = np.where(brim & (cv.X > c + 3), 2, lv)
    cv.part("brim", brim, "cap", lv=lv)
    pr = RAMP["patch"]
    for (x, y) in [(c - 1, t + 3), (c, t + 3), (c + 1, t + 3), (c - 1, t + 4), (c + 1, t + 4)]:
        px, py = rot(x, y)
        cv.put(px, py, pr[2])
    px, py = rot(c, t + 4)
    cv.put(px, py, (62, 80, 58))
    px, py = rot(c, t + 1)
    cv.put(px, py, cr[3])


def w_head(cv, c, t, pose, cap_ang=0.0, cap_dx=0):
    sk, bd = RAMP["skin"], RAMP["beard"]
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 8.6, t + 13, 1.6, 2.2), "skin", bias=0.05)
    face = cv.ell(c, t + 12, 8.6, 8)
    cv.part("face", face, "skin", rad=6, soft=1.2, cuts=(0.30, 0.52, 0.88))
    for s in (-1, 1):
        cv.part("sidehair%d" % s, cv.ell(c + s * 8, t + 9.5, 1.6, 2.4) & cv.half(y=t + 7), "hair", noedge=("face",))
    for x in range(c - 8, c + 9):
        if cv.own[t + 8, x] == cv.names["face"]:
            cv.put(x, t + 8, sk[1])
    # beard
    beard = cv.ell(c, t + 16, 9.2, 6.6) & cv.half(y=t + 12)
    for s in (-1, 1):
        beard |= cv.capsule(c + s * 8, t + 9, c + s * 8, t + 14, 1.2)
        beard &= ~cv.ell(c + s * 4, t + 12.2, 3.4, 1.9)
    beard |= cv.ell(c, t + 21, 5, 2.2)
    cv.part("beard", beard, "beard", rad=5, soft=1.0, noedge=("sidehair-1", "sidehair1"), cuts=(0.28, 0.5, 0.84))
    # nose + moustache
    cv.puts([(c - 1, t + 13), (c, t + 13), (c, t + 14), (c - 1, t + 14)], sk[3])
    cv.put(c - 1, t + 13, sk[4]); cv.put(c + 1, t + 14, sk[1]); cv.put(c + 1, t + 13, sk[2])
    st = cv.ell(c - 2, t + 15.6, 2.8, 1.3) | cv.ell(c + 2, t + 15.6, 2.8, 1.3)
    cv.part("stache", st, "beard", edge=None, lv=np.where(st, 4, 0))
    cv.hline(c - 3, c + 3, t + 16, bd[2])
    for (x, y) in [(c - 2, t + 19), (c + 2, t + 20), (c - 5, t + 18), (c + 5, t + 19), (c, t + 21)]:
        if cv.own[y, x] == cv.names["beard"]:
            cv.put(x, y, bd[1] if cv.get(x, y) == bd[2] else bd[2])
    # mouth
    if pose == "talk":
        cv.hline(c - 1, c + 1, t + 17, MOUTH); cv.put(c, t + 18, MOUTH)
    elif pose == "hit":
        cv.hline(c - 2, c + 2, t + 17, MOUTH); cv.put(c - 1, t + 17, TEETH); cv.put(c + 1, t + 17, TEETH)
    elif pose == "tell":
        cv.hline(c - 1, c + 2, t + 17, MOUTH); cv.put(c, t + 17, TEETH); cv.put(c + 3, t + 16, MOUTH)
    else:
        cv.hline(c - 1, c + 1, t + 17, MOUTH)
    # cheeks
    cv.put(c - 5, t + 13, BLUSH); cv.put(c + 5, t + 13, BLUSH)
    # glasses: 2 rectangles 5x4 + bridge
    for s in (-1, 1):
        xa, xb = (c - 7, c - 2) if s < 0 else (c + 2, c + 7)
        dy = 0
        for x in range(xa + 1, xb):
            for y in (t + 10, t + 11):
                cv.put(x, y + dy, LENS2 if pose == "tell" else mix(cv.get(x, y + dy), LENS, 0.15))
        cv.hline(xa, xb, t + 9 + dy, FRAME); cv.hline(xa, xb, t + 12 + dy, FRAME)
        cv.vline(xa, t + 9 + dy, t + 12 + dy, FRAME); cv.vline(xb, t + 9 + dy, t + 12 + dy, FRAME)
        ex = c + s * 4 - (1 if s < 0 else 0)
        if pose == "tell":
            cv.put(xa + 1, t + 10, WHITE); cv.put(xa + 3, t + 11, WHITE); cv.put(xa + 4, t + 10, LENS)
        elif pose == "hit":
            cv.put(ex, t + 10 + dy, EYE); cv.put(ex + 1, t + 11 + dy, EYE) if s < 0 else cv.put(ex - 1, t + 11 + dy, EYE)
            cv.put(ex - (1 if s < 0 else -1), t + 11 + dy, EYE)
        else:
            ex = c + s * 4
            cv.put(ex, t + 10, EYE); cv.put(ex, t + 11, EYE)
    cv.hline(c - 1, c + 1, t + 10, FRAME)
    # brows
    for s in (-1, 1):
        y = t + 8 - (1 if pose == "tell" else 0)
        for k in range(2, 7):
            cv.put(c + s * k, y + (1 if (pose == "hit" and k < 4) else 0), bd[4] if s < 0 else bd[3])
    w_cap_front(cv, c + cap_dx, t, cap_ang)
    if pose == "tell":
        cv.puts([(c - 9, t + 7), (c - 10, t + 8), (c - 9, t + 8), (c - 8, t + 8), (c - 9, t + 9)], SPARK2)
        cv.put(c - 9, t + 8, WHITE)


def w_probe(cv, x0, y0, x1, y1, name="probe"):
    L = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / L, (y1 - y0) / L
    P = lambda k: (x0 + ux * k, y0 + uy * k)
    e = P(L - 2)
    m = cv.capsule(x0, y0, e[0], e[1], 1.3, 0.9)
    cv.part(name, m, "probe", edge="ink", lv=np.where(m, 3, 0))
    x, y = P(L * 0.35)
    cv.put(x, y, YELLOW)
    for k in (L - 1, L):
        x, y = P(k)
        cv.put(x, y, RAMP["metal"][4])


def w_arm(cv, name, pts, r=2.7):
    m = cv.chain(pts, r)
    cv.part(name, m, "fleece", edge="dark", rad=2.5, soft=0.8, cuts=(0.30, 0.55, 0.9))
    return m


def w_hand(cv, x, y, name, r=2.1):
    m = cv.ell(x, y, r, r)
    cv.part(name, m, "skin", edge="ink", lv=np.where(m, 3, 0) - np.where(m & (cv.X > x) & (cv.Y > y - 1), 1, 0))
    return m


def w_legs(cv, c, t, back=False):
    pants = cv.poly([(c - 8, t + 33), (c + 8, t + 33), (c + 7.5, t + 42), (c + 1, t + 42), (c + 0.5, t + 38),
                     (c - 0.5, t + 38), (c - 1, t + 42), (c - 7.5, t + 42)])
    pants &= ~cv.rect(c, t + 39, c, t + 50)
    cv.part("pants", pants, "pants", rad=3, soft=0.8, cuts=(0.32, 0.56, 0.9))
    for s in (-1, 1):
        sx = c + s * 4.5
        sh = cv.ell(sx, t + 43.6, 4.6, 2.5) & cv.half(y=t + 45, below=False)
        cv.part("shoe%d" % s, sh, "shoe", rad=2, soft=0.6, cuts=(0.3, 0.55, 0.85))
        if not back:
            cv.put(sx - 2, t + 43, RAMP["shoe"][3])


def w_torso(cv, c, t, back=False):
    fl = RAMP["fleece"]
    torso = cv.ell(c, t + 25.5, 11.6, 6) | (cv.ell(c, t + 28.5, 13.6, 7) & cv.half(y=t + 34, below=False))
    cv.part("torso", torso, "fleece", rad=8, soft=1.4, cuts=(0.30, 0.52, 0.84))
    hem = torso & cv.half(y=t + 33)
    cv.part("hem", hem, "fleece", noedge=("torso",), lv=np.where(hem, 1, 0) + np.where(hem & (cv.X < c - 3), 1, 0))
    if not back:
        for x in range(c - 9, c - 5):
            cv.put(x, t + 26 + (c - 7 - x) // 2, fl[3])
        cv.part("tee", cv.poly([(c - 2, t + 22), (c + 2, t + 22), (c, t + 25)]), "tee", lv=None, flat=True)
        cv.vline(c, t + 26, t + 31, RAMP["metal"][1])
        cv.put(c, t + 26, RAMP["metal"][3])
    else:
        for x in range(c - 9, c + 10):
            y = t + 25 + abs(x - c) // 5
            if cv.own[y, x] == cv.names["torso"]:
                cv.put(x, y, fl[1])


def w_front(pose):
    cv = Cv(WW, WH)
    c, t = 24, WT
    cap_ang, cap_dx, hx = 0.0, 0, 0
    if pose == "hit":
        cap_ang, cap_dx, hx = 0.22, 1, 1
    if pose == "tell":
        coil(cv, [(c - 15, t + 21), (c - 18, t + 27), (c - 18, t + 34), (c - 14, t + 41), (c - 10, t + 44)], r=1.2, pitch=2.0)
    elif pose == "hit":
        coil(cv, [(c - 18, t + 25), (c - 20, t + 31), (c - 18, t + 38), (c - 12, t + 43)], r=1.2, pitch=2.0)
    w_legs(cv, c, t)
    if pose in ("idle", "talk"):
        coil(cv, [(c - 3, t + 34), (c - 3, t + 38), (c - 6, t + 41), (c - 10, t + 41), (c - 12, t + 37), (c - 12, t + 34)], r=1.2, pitch=2.0)
    w_torso(cv, c, t)
    if pose in ("idle", "talk"):
        w_arm(cv, "armL", [(c - 10, t + 24), (c - 13, t + 28), (c - 12.5, t + 31)])
        w_probe(cv, c - 11, t + 32, c - 19, t + 42)
        w_hand(cv, c - 12.5, t + 33, "handL")
    elif pose == "tell":
        w_arm(cv, "armL", [(c - 10, t + 24), (c - 15, t + 26), (c - 15.5, t + 21)])
        w_probe(cv, c - 15.5, t + 22, c - 15, t + 8)
        w_hand(cv, c - 15.5, t + 19.5, "handL")
    elif pose == "hit":
        w_arm(cv, "armL", [(c - 10, t + 24), (c - 15, t + 25), (c - 18, t + 21)])
        w_probe(cv, c - 18, t + 23, c - 22, t + 12)
        w_hand(cv, c - 18, t + 21, "handL")
    if pose == "idle":
        w_arm(cv, "armR", [(c + 10, t + 24), (c + 13, t + 28), (c + 12.5, t + 31)])
        w_hand(cv, c + 12.5, t + 33, "handR")
    elif pose == "talk":
        w_arm(cv, "armR", [(c + 10, t + 24), (c + 15, t + 27), (c + 17, t + 22)])
        w_hand(cv, c + 17, t + 19.5, "handR", r=2.3)
        cv.put(c + 16, t + 17, RAMP["skin"][3]); cv.put(c + 18, t + 17, RAMP["skin"][3])
        cv.put(c + 16, t + 16, INK); cv.put(c + 18, t + 16, INK); cv.put(c + 17, t + 17, INK)
    elif pose == "tell":
        w_arm(cv, "armR", [(c + 10, t + 24), (c + 13, t + 28), (c + 9, t + 31)])
        w_hand(cv, c + 7.5, t + 31, "handR")
    elif pose == "hit":
        w_arm(cv, "armR", [(c + 10, t + 24), (c + 16, t + 24), (c + 17, t + 19)])
        w_hand(cv, c + 17, t + 17, "handR", r=2.3)
    w_head(cv, c + hx, t, pose, cap_ang, cap_dx)
    if pose == "hit":
        sx, sy = c + 12, t + 3
        cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx, sy + 2)], SWEAT)
        cv.put(sx - 1, sy + 1, SWEAT_HI)
    cv.outline()
    return cv


def w_side():
    cv = Cv(WW, WH)
    c, t = 22, WT
    sk, bd, fl = RAMP["skin"], RAMP["beard"], RAMP["fleece"]
    cv.part("legB", cv.poly([(c - 6, t + 33), (c + 1, t + 33), (c + 0, t + 42), (c - 6, t + 42)]), "pants",
            rad=3, cuts=(0.4, 0.62, 0.95))
    cv.part("shoeB", cv.ell(c - 2, t + 43.6, 5, 2.5) & cv.half(y=t + 45, below=False), "shoe", rad=2, cuts=(0.4, 0.62, 0.95))
    cv.part("legF", cv.poly([(c - 4, t + 33), (c + 4, t + 33), (c + 4, t + 42), (c - 3, t + 42)]), "pants",
            rad=3, cuts=(0.32, 0.56, 0.9))
    cv.part("shoeF", cv.ell(c + 2.5, t + 43.6, 5.4, 2.5) & cv.half(y=t + 45, below=False), "shoe", rad=2,
            cuts=(0.3, 0.55, 0.85))
    cv.put(c + 4, t + 42, RAMP["shoe"][3])
    torso = (cv.ell(c - 0.5, t + 25.5, 8.5, 6) | (cv.ell(c + 2, t + 28.5, 9.6, 7) & cv.half(y=t + 34, below=False))
             | (cv.rect(c - 8, t + 26, c, t + 34) & cv.ell(c - 0.5, t + 29, 8.5, 8)))
    cv.part("torso", torso, "fleece", rad=7, soft=1.4, cuts=(0.30, 0.52, 0.84))
    hem = torso & cv.half(y=t + 33)
    cv.part("hem", hem, "fleece", noedge=("torso",), lv=np.where(hem, 1, 0) + np.where(hem & (cv.X < c + 3), 1, 0))
    for x in range(c + 2, c + 6):
        cv.put(x, t + 26 + abs(x - c - 3) // 2, fl[3])
    coil(cv, [(c + 1, t + 34), (c - 2, t + 37), (c - 5, t + 40), (c - 5, t + 44)], r=1.2, pitch=2.0)
    w_arm(cv, "arm", [(c - 1, t + 24), (c - 0.5, t + 29), (c + 1.5, t + 32)])
    w_probe(cv, c + 1, t + 33, c + 10, t + 40)
    w_hand(cv, c + 2, t + 33.5, "hand")
    # head
    cv.part("neck", cv.rect(c - 5, t + 17, c - 1, t + 22), "skin", rad=2, bias=-0.1)
    cv.part("collar", cv.ell(c - 1.5, t + 22.5, 5.5, 2.0), "fleece", rad=2, bias=0.06)
    head = cv.ell(c, t + 12, 8.2, 7.8) | (cv.ell(c + 3.5, t + 12, 5.2, 6.4) & cv.half(y=t + 8))
    cv.part("head", head, "skin", rad=6, soft=1.2, cuts=(0.30, 0.52, 0.88), bias=0.12)
    hair = cv.ell(c - 2.5, t + 11, 6, 6.2) & cv.half(x=c - 3, right=False) & cv.half(y=t + 7)
    hair &= head
    cv.part("hair", hair, "hair", noedge=("head",), rad=3, cuts=(0.32, 0.58, 0.9))
    beard = (cv.ell(c + 3, t + 17, 6.4, 6.2) & cv.half(y=t + 13)) | cv.ell(c + 4.5, t + 21.5, 4.4, 2.4)
    beard |= cv.capsule(c + 0.5, t + 10, c + 0.5, t + 15, 1.1)
    beard &= ~cv.ell(c + 5, t + 13, 3, 1.9)
    cv.part("beard", beard, "beard", noedge=("hair",), rad=5, soft=1.0, cuts=(0.28, 0.5, 0.84))
    cv.part("nose", cv.ell(c + 8.8, t + 14.5, 1.8, 1.7), "skin", edge="ink", noedge=("head",), lv=None, rad=2, bias=0.15)
    st = cv.ell(c + 7, t + 16.5, 2.8, 1.3)
    cv.part("stache", st, "beard", edge=None, lv=np.where(st, 4, 0))
    cv.put(c + 7, t + 18, MOUTH); cv.put(c + 8, t + 18, MOUTH)
    cv.part("ear", cv.ell(c - 2, t + 13, 1.5, 2.2), "skin", edge="dark", bias=0.05)
    # glasses
    cv.hline(c + 5, c + 8, t + 9, FRAME); cv.hline(c + 5, c + 8, t + 12, FRAME)
    cv.vline(c + 5, t + 9, t + 12, FRAME); cv.vline(c + 8, t + 9, t + 12, FRAME)
    cv.hline(c - 1, c + 4, t + 10, FRAME)
    for x in (c + 6, c + 7):
        for y in (t + 10, t + 11):
            cv.put(x, y, mix(cv.get(x, y), LENS, 0.15))
    cv.put(c + 7, t + 10, EYE); cv.put(c + 7, t + 11, EYE)
    cv.hline(c + 5, c + 8, t + 8, bd[4])
    cv.put(c + 5, t + 13, BLUSH)
    for x in range(c + 1, c + 9):
        if cv.own[t + 7, x] == cv.names["head"]:
            cv.put(x, t + 7, sk[1])
    # cap
    crown = cv.ell(c, t + 7.6, 8.8, 7.65) & cv.half(y=t + 6.4, below=False)
    cv.part("crown", crown, "cap", rad=6, soft=1.0, cuts=(0.30, 0.52, 0.84))
    brim = cv.poly([(c + 4, t + 5), (c + 10, t + 5.5), (c + 13, t + 7), (c + 12, t + 8), (c + 4, t + 8)])
    cv.part("brim", brim, "cap", lv=np.where(brim, 3, 0) - np.where(brim & (cv.Y >= t + 8), 2, 0))
    cv.put(c + 6, t + 3, RAMP["patch"][2]); cv.put(c + 6, t + 4, RAMP["patch"][1])
    cv.put(c, t + 1, RAMP["cap"][3])
    cv.outline()
    return cv


def w_back():
    cv = Cv(WW, WH)
    c, t = 24, WT
    hr = RAMP["hair"]
    coil(cv, [(c + 13, t + 34), (c + 17, t + 37), (c + 17, t + 41), (c + 13, t + 44), (c + 9, t + 44)], r=1.2, pitch=2.0)
    w_legs(cv, c, t, back=True)
    cv.vline(c, t + 33, t + 37, RAMP["pants"][0])
    w_torso(cv, c, t, back=True)
    beard = cv.ell(c, t + 17.5, 9.6, 5.6) & cv.half(y=t + 12)
    cv.part("beard", beard, "beard", rad=4, soft=1.0, cuts=(0.28, 0.5, 0.84))
    cv.part("neck", cv.rect(c - 4, t + 14, c + 4, t + 22), "skin", rad=3, bias=-0.12)
    cv.part("collar", cv.ell(c, t + 22.5, 6.5, 2.2), "fleece", rad=2, bias=0.06)
    w_arm(cv, "armL", [(c - 10, t + 24), (c - 13, t + 28), (c - 12.5, t + 31)])
    w_hand(cv, c - 12.5, t + 33, "handL")
    w_arm(cv, "armR", [(c + 10, t + 24), (c + 13, t + 28), (c + 12.5, t + 31)])
    w_probe(cv, c + 11, t + 32, c + 19, t + 42)
    w_hand(cv, c + 12.5, t + 33, "handR")
    head = cv.ell(c, t + 10.5, 8.4, 6.8)
    cv.part("head", head, "hair", rad=5, soft=1.0, cuts=(0.32, 0.56, 0.88))
    for (x, y) in [(c - 4, t + 11), (c + 3, t + 12), (c - 1, t + 14), (c + 5, t + 9), (c - 6, t + 9)]:
        if cv.own[y, x] == cv.names["head"]:
            cv.put(x, y, hr[1])
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 8.4, t + 12.5, 1.6, 2.2), "skin", bias=0.05)
    cr = RAMP["cap"]
    crown = cv.ell(c, t + 7.6, 9.4, 7.65) & cv.half(y=t + 7.4, below=False)
    cv.part("crown", crown, "cap", rad=6, soft=1.0, cuts=(0.30, 0.52, 0.84))
    cv.puts([(c - 1, t + 6), (c, t + 6), (c + 1, t + 6), (c - 1, t + 7), (c, t + 7), (c + 1, t + 7)], hr[2])
    cv.puts([(c - 2, t + 6), (c + 2, t + 6), (c - 2, t + 7), (c + 2, t + 7), (c - 1, t + 5), (c, t + 5), (c + 1, t + 5)], cr[0])
    cv.put(c, t + 1, cr[3])
    cv.outline()
    return cv


# ==========================================================================
# PORTRAITS  (64 x 64, head and shoulders)
# ==========================================================================
PW = PH = 64
IRIS = (44, 30, 32)
IRIS2 = (96, 62, 50)
SCLERA = (240, 236, 230)


def p_strands(cv, mask_name, pts, color):
    for (x0, y0, x1, y1) in pts:
        # only paint where the beard is
        L = max(abs(x1 - x0), abs(y1 - y0))
        for k in range(L + 1):
            x = round(x0 + (x1 - x0) * k / max(L, 1))
            y = round(y0 + (y1 - y0) * k / max(L, 1))
            if 0 <= x < cv.w and 0 <= y < cv.h and cv.own[y, x] == cv.names[mask_name]:
                if cv.get(x, y) != RAMP["beard"][0]:
                    cv.put(x, y, color)


def p_eye(cv, ex, ey, expr, side):
    """Pixel-map eyes. (ex, ey) = top-left anchor of a 7x5 cell for the
    viewer-left eye; the right eye is mirrored."""
    sk = RAMP["skin"]
    maps = {
        "neutral": ["..KKKK.",
                    ".KIHIIK",
                    ".WIIIW.",
                    "..SSS..",
                    "......."],
        "warm":    ["..KKK..",
                    ".KKKKK.",
                    "KK...KK",
                    "K.....K",
                    ".SSSSS."],
        "concern": [".KKKKK.",
                    "KIHIIW.",
                    ".WIII..",
                    "..SSS..",
                    "......."],
        "surprised": ["..KKK..",
                      ".KWWWK.",
                      "KWWIWWK",
                      "KWWIWWK",
                      ".KWWWK.",
                      "..SSS.."],
    }
    pal = {"K": EYE, "I": IRIS, "H": WHITE, "W": SCLERA, "S": sk[1], "D": IRIS2}
    rows = maps[expr]
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x = ex + i if side < 0 else ex + (6 - i)
            col = pal[ch]
            if ch == "H" and side > 0:
                # keep the highlight on the upper-left in both eyes
                x = ex + i - 1 if False else x
            cv.put(x, ey + j, col)
    hs = [(j, r.index("H")) for j, r in enumerate(rows) if "H" in r]
    if side > 0 and hs:
        # mirrored catch-light would sit on the upper-right; move it back left
        j, i = hs[0]
        xr = ex + (6 - i)
        cv.put(xr, ey + j, IRIS)
        cv.put(xr - 2, ey + j, WHITE)


def p_brows(cv, c, by, expr):
    bd = RAMP["beard"]
    # (dx, dy) from the inner end of the viewer-left brow, going outward
    if expr == "concern":
        shape = [(0, 2), (-1, 2), (-2, 1), (-3, 1), (-4, 0), (-5, 0), (-6, 0), (-7, 0), (-8, 0), (-9, 1)]
    elif expr == "surprised":
        shape = [(0, 0), (-1, -1), (-2, -1), (-3, -2), (-4, -2), (-5, -2), (-6, -2), (-7, -1), (-8, -1), (-9, 0)]
    elif expr == "warm":
        shape = [(0, 0), (-1, -1), (-2, -1), (-3, -1), (-4, -2), (-5, -2), (-6, -2), (-7, -1), (-8, -1), (-9, 0)]
    else:
        shape = [(0, 0), (-1, 0), (-2, -1), (-3, -1), (-4, -1), (-5, -1), (-6, -1), (-7, -1), (-8, 0), (-9, 1)]
    for side in (-1, 1):
        ix = c - 4 if side < 0 else c + 4
        lit = side < 0
        for i, (dx, dy) in enumerate(shape):
            x = ix + dx if side < 0 else ix - dx
            cv.put(x, by + dy, bd[4] if lit else bd[3])
            cv.put(x, by + dy + 1, bd[2] if i > 1 else bd[1])
            if 1 < i < 8:
                cv.put(x, by + dy - 1, bd[3] if lit else bd[2])
        # stray bushy hairs
        tx = ix - 10 if side < 0 else ix + 10
        cv.put(tx, by + shape[9][1], bd[3] if lit else bd[2])
        cv.put(ix + (-5 if side < 0 else 5), by + shape[5][1] - 2, bd[4] if lit else bd[3])


def p_mouth(cv, c, my, expr):
    LIP = (176, 90, 86)
    if expr == "neutral":
        cv.hline(c - 3, c + 3, my, MOUTH)
        cv.put(c - 4, my - 1, MOUTH); cv.put(c + 4, my - 1, MOUTH)
        cv.hline(c - 2, c + 2, my + 1, LIP)
    elif expr == "warm":
        cv.hline(c - 6, c + 6, my - 1, MOUTH)
        cv.put(c - 7, my - 2, MOUTH); cv.put(c + 7, my - 2, MOUTH)
        cv.hline(c - 5, c + 5, my, TEETH)
        cv.put(c - 6, my, MOUTH); cv.put(c + 6, my, MOUTH)
        for x in (c - 3, c, c + 3):
            cv.put(x, my, (214, 206, 196))
        cv.hline(c - 5, c + 5, my + 1, MOUTH)
        cv.hline(c - 4, c + 4, my + 2, MOUTH)
        cv.hline(c - 2, c + 2, my + 2, TONGUE)
        cv.hline(c - 3, c + 3, my + 3, LIP)
    elif expr == "concern":
        cv.hline(c - 3, c + 3, my, MOUTH)
        cv.put(c - 4, my + 1, MOUTH); cv.put(c + 4, my + 1, MOUTH)
        cv.hline(c - 2, c + 2, my + 1, LIP)
    elif expr == "surprised":
        for dy, w in ((0, 1), (1, 2), (2, 2), (3, 2), (4, 1)):
            cv.hline(c - w, c + w, my + dy - 1, MOUTH)
        cv.hline(c - 1, c + 1, my + 2, TONGUE)
        cv.put(c - 2, my + 4, LIP); cv.put(c - 1, my + 4, LIP); cv.put(c, my + 4, LIP); cv.put(c + 1, my + 4, LIP)


def portrait(expr):
    cv = Cv(PW, PH, open_bottom=True)
    c = 32
    sk, bd, fl, cr = RAMP["skin"], RAMP["beard"], RAMP["fleece"], RAMP["cap"]
    lift = -2 if expr == "surprised" else 0          # cap pops up when surprised
    gl = 3 if expr == "concern" else 0               # glasses slid down the nose
    # ---- shoulders + collar ----
    sh = cv.ell(c, 76, 31, 25.5) & cv.half(y=46)
    cv.part("shoulders", sh, "fleece", rad=14, soft=2.0, cuts=(0.30, 0.52, 0.84), tex=0.06, seed=41)
    cv.line(9, 57, 12, 63, fl[1]); cv.line(55, 57, 52, 63, fl[0])          # raglan seams
    col = cv.ell(c, 56.5, 17.5, 5.5)
    cv.part("collar", col, "fleece", rad=4, soft=1.0, bias=0.08)
    tee = cv.poly([(c - 6, 55), (c + 6, 55), (c + 1, 64), (c - 1, 64)])
    cv.part("tee", tee, "tee", edge="dark", lv=np.where(tee, 1, 0) + np.where(tee & (cv.X < c), 1, 0))
    mt = RAMP["metal"]
    # ---- ears ----
    for s in (-1, 1):
        cv.part("ear%d" % s, cv.ell(c + s * 18, 33, 3.2, 4.8), "skin", rad=3, bias=0.04)
        cv.puts([(c + s * 18, 32), (c + s * 18, 33), (c + s * 18, 34), (c + s * 19, 35)], sk[1])
    # ---- face ----
    face = cv.ell(c, 33, 17.5, 17)
    cv.part("face", face, "skin", rad=13, soft=2.2, cuts=(0.30, 0.50, 0.84))
    for s in (-1, 1):
        cv.part("sidehair%d" % s, cv.ell(c + s * 16.6, 24, 3.2, 5.2) & cv.half(y=18), "hair",
                noedge=("face",), rad=3, bias=0.06)
    # brim shadow on the forehead
    for x in range(c - 17, c + 18):
        for y, col_ in ((22 + lift, sk[1]), (23 + lift, sk[1]), (24 + lift, sk[2])):
            if 0 <= y < PH and cv.own[y, x] == cv.names["face"]:
                cv.put(x, y, col_)
    if expr == "surprised":
        for x in range(c - 6, c + 7, 1):
            if abs(x - c) > 1:
                cv.put(x, 21 + (abs(x - c) > 4), sk[1])
    # ---- cheeks ----
    for s in (-1, 1):
        bx = c + s * 11
        rows = (35, 36, 37) if expr != "warm" else (34, 35, 36, 37)
        for y in rows:
            for x in range(bx - 3, bx + 4):
                if cv.own[y, x] == cv.names["face"]:
                    cv.put(x, y, mix(cv.get(x, y), BLUSH, 0.5 if abs(x - bx) < 3 else 0.3))
    # ---- beard ----
    beard = cv.ell(c, 42.5, 20.6, 15.5) & cv.half(y=27)
    for s in (-1, 1):
        beard |= cv.capsule(c + s * 16.6, 22, c + s * 17.4, 36, 2.3)
    beard &= ~cv.ell(c, 31.0, 15.2, 8.6)          # cheeks + nose stay clear
    beard |= cv.ell(c, 54.0, 12.5, 4.8)            # fuller at the chin
    cv.part("beard", beard, "beard", rad=11, soft=2.0, noedge=("sidehair-1", "sidehair1"),
            cuts=(0.18, 0.40, 0.76))
    # greyer under the mouth, like the photo
    under = cv.ell(c, 51, 5.5, 3.6) & beard
    for y, x in zip(*np.nonzero(under)):
        if cv.get(x, y) != bd[0]:
            cv.put(x, y, bd[2])
    p_strands(cv, "beard", [(c - 3, 50, c - 3, 53), (c, 50, c, 54), (c + 3, 50, c + 3, 53), (c - 1, 52, c - 1, 55), (c + 2, 52, c + 2, 55)], bd[1])
    strands = []
    for (x, y) in [(15, 40), (18, 45), (21, 50), (25, 54), (17, 35), (21, 42), (24, 47), (28, 55), (14, 45), (20, 54)]:
        strands.append((x, y, x + 1, y + 3))
        strands.append((2 * c - x, y, 2 * c - x - 1, y + 3))
    p_strands(cv, "beard", strands, bd[2])
    p_strands(cv, "beard", [(16, 38, 17, 41), (19, 44, 20, 47), (23, 50, 24, 53), (27, 56, 27, 57), (16, 30, 16, 33)], bd[4])
    p_strands(cv, "beard", [(46, 40, 45, 43), (43, 46, 42, 49), (39, 52, 38, 55), (47, 33, 47, 36), (35, 56, 35, 57)], bd[1])
    # ---- moustache ----
    if expr == "warm":
        st = cv.ell(c - 5, 42.6, 7.2, 3.0, -0.22) | cv.ell(c + 5, 42.6, 7.2, 3.0, 0.22)
    else:
        st = cv.ell(c - 5, 43.4, 7.0, 3.2, -0.12) | cv.ell(c + 5, 43.4, 7.0, 3.2, 0.12)
    cv.part("stache", st, "beard", edge=bd[1], noedge=("beard",), rad=3, soft=1.0, bias=0.06, cuts=(0.2, 0.42, 0.78))
    p_strands(cv, "stache", [(c - 2, 41, c - 4, 45), (c - 6, 41, c - 8, 45), (c + 2, 41, c + 4, 45), (c + 6, 41, c + 8, 45)], bd[2])
    cv.vline(c, 41, 42, bd[1])
    # ---- nose: big, round, ruddy ----
    nose = cv.ell(c, 37.0, 4.6, 4.0)
    cv.part("nose", nose, "skin", edge="dark", noedge=("face",), rad=4, soft=1.0, bias=0.10, light=(-0.55, -0.6, 0.6))
    for y, x in zip(*np.nonzero(nose)):
        cv.put(x, y, mix(cv.get(x, y), BLUSH, 0.3))
    # separate the nose from the face: shade its lower-right rim and cast a soft
    # shadow on the cheek to its right
    nid, fid = cv.names["nose"], cv.names["face"]
    ys, xs = np.nonzero(nose)
    for y, x in zip(ys, xs):
        if (cv.own[y, x + 1] == fid or cv.own[y + 1, x] == fid) and x >= c - 1:
            cv.put(x, y, sk[1])
        elif cv.own[y, x - 1] == fid or cv.own[y - 1, x] == fid:
            cv.put(x, y, sk[3])
    for y, x in zip(ys, xs):
        if cv.own[y, x + 1] == fid and x >= c:
            cv.put(x + 1, y, mix(sk[1], sk[0], 0.3))
    cv.puts([(c - 2, 34), (c - 1, 34), (c - 3, 35), (c - 2, 35)], sk[4])
    cv.puts([(c + 3, 38), (c + 2, 39), (c + 3, 37), (c + 3, 36), (c + 2, 38)], sk[1])
    cv.puts([(c - 2, 39), (c + 2, 39)], (120, 50, 46))     # nostrils
    cv.puts([(c - 1, 30 + gl), (c - 1, 31 + gl), (c - 1, 32)], sk[3])
    # ---- mouth ----
    p_mouth(cv, c, 47 if expr != "warm" else 46, expr)
    # ---- glasses + eyes ----
    y0, y1 = 26 + gl, 33 + gl
    for side in (-1, 1):
        xa, xb = (c - 16, c - 3) if side < 0 else (c + 3, c + 16)
        for y in range(y0 + 1, y1):
            for x in range(xa + 1, xb):
                cv.put(x, y, mix(cv.get(x, y), LENS, 0.12 if not gl else 0.32))
    ey = {"neutral": 28, "warm": 28, "concern": 25, "surprised": 27}[expr]
    for side in (-1, 1):
        ex = c - 13 if side < 0 else c + 7
        p_eye(cv, ex, ey, expr, side)
    # crow's feet (outside the lenses)
    for side in (-1, 1):
        x = c + side * 17
        n = 3 if expr == "warm" else 2
        for k in range(n):
            cv.put(x + side * k, 30 + k * 2 - (1 if k == 2 else 0), sk[1])
    for side in (-1, 1):
        xa, xb = (c - 16, c - 3) if side < 0 else (c + 3, c + 16)
        cv.hline(xa, xb, y0, FRAME)
        cv.hline(xa, xb, y1, FRAME)
        cv.vline(xa, y0, y1, FRAME); cv.vline(xb, y0, y1, FRAME)
        cv.hline(xa + 1, xa + 5, y0, FRAME_HI)
        cv.put(xa, y0 + 1, FRAME_HI)
        if expr != "concern":
            cv.puts([(xa + 2, y0 + 2), (xa + 3, y0 + 2), (xa + 2, y0 + 3)], mix(LENS, (255, 255, 255), 0.5))
        else:
            cv.puts([(xa + 2, y1 - 2), (xa + 3, y1 - 2)], mix(LENS, (255, 255, 255), 0.5))
        cv.put(xb - 2, y1 - 1, mix(LENS, sk[2], 0.3))
    cv.hline(c - 2, c + 2, y0 + 1, FRAME)
    cv.hline(c - 18, c - 17, y0 + 1, FRAME); cv.hline(c + 17, c + 18, y0 + 1, FRAME)
    # ---- brows ----
    by = {"neutral": 24, "warm": 24, "concern": 22, "surprised": 22}[expr]
    p_brows(cv, c, by, expr)
    if expr == "concern":
        cv.puts([(c - 1, 23), (c + 1, 23), (c - 1, 24), (c + 1, 24), (c, 25)], sk[1])
    # ---- cap ----
    crown = cv.ell(c, 20.6 + lift, 19.4, 18.3) & cv.half(y=18.5 + lift, below=False)
    cv.part("crown", crown, "cap", rad=13, soft=2.2, cuts=(0.30, 0.52, 0.84), tex=0.05, seed=47)
    brim = cv.ell(c, 16.0 + lift, 17.6, 7.6) & cv.half(y=16.0 + lift)
    lv = np.where(brim, 3, 0)
    lv = np.where(brim & (cv.X < c - 6), 4, lv)
    lv = np.where(brim & (cv.X > c + 6), 2, lv)
    lip = brim & ~cv.ell(c, 14.8 + lift, 17.6, 7.6)
    lv = np.where(lip, 1, lv)
    cv.part("brim", brim, "cap", lv=lv)
    for x in range(c - 14, c + 15, 2):
        dy = 5.0 * math.sqrt(max(0.0, 1 - (x - c) ** 2 / 15.5 ** 2))
        y = int(round(16.0 + lift + dy))
        if cv.own[y, x] == cv.names["brim"]:
            cv.put(x, y, cr[2] if x < c + 6 else cr[1])
    cv.line(c - 1, 4 + lift, c - 12, 18 + lift, cr[1])
    cv.line(c + 1, 4 + lift, c + 12, 18 + lift, cr[1])
    cv.put(c - 1, 2 + lift, cr[4]); cv.put(c, 2 + lift, cr[3]) if 2 + lift >= 0 else None
    for (x, y) in [(c - 14, 9), (c - 15, 10), (c - 16, 11), (c - 13, 8), (c - 12, 7)]:
        cv.put(x, y + lift, cr[4])
    # embroidered patch: the Flatirons
    pr = RAMP["patch"]
    px0, py0 = c - 6, 7 + lift
    for y in range(py0, py0 + 7):
        for x in range(px0, px0 + 13):
            col_ = pr[2]
            if y == py0 or x == px0:
                col_ = pr[3]
            if y == py0 + 6 or x == px0 + 12:
                col_ = pr[1]
            cv.put(x, y, col_)
    mnt = (62, 82, 58)
    for x in range(px0 + 2, px0 + 11):
        h = max(max(0, 3 - abs(x - (px0 + 5))), max(0, 2 - abs(x - (px0 + 8))))
        for k in range(h + 1):
            cv.put(x, py0 + 5 - k, mnt)
    cv.put(px0 + 5, py0 + 2, WHITE); cv.put(px0 + 8, py0 + 3, (220, 224, 216))
    cv.outline()
    if expr == "warm":
        cv.puts([(56, 12), (57, 11), (58, 10), (57, 15), (59, 15), (60, 15)], SPARK2)
    if expr == "surprised":
        cv.puts([(55, 6), (55, 7), (55, 8), (55, 10), (58, 8), (59, 7), (60, 6)], SPARK2)
    return cv




# ==========================================================================
# output
# ==========================================================================
def foot_point(cv):
    """x = centre between the shoes on the sole row, y = sole row."""
    y = cv.h - 1
    shoe_ids = [pid for n, pid in cv.names.items() if n.startswith("shoe")]
    xs = [x for x in range(cv.w) if cv.alpha[y, x] and cv.own[y, x] in shoe_ids]
    if not xs:
        xs = [x for x in range(cv.w) if cv.alpha[y, x]]
    return [int(round((min(xs) + max(xs)) / 2)), y]


def check_height(img, want, name):
    a = np.array(img)[..., 3] > 0
    rows = np.nonzero(a.any(axis=1))[0]
    # standing height = cap top to soles; the probe may not poke above the cap
    assert rows[-1] == img.height - 1, (name, "feet not on bottom row")
    assert img.height - rows[0] == want, (name, "height", img.height - rows[0])


def build():
    os.makedirs(OUT, exist_ok=True)
    feet = {}
    cells = {}
    battle = [b_front("idle"), b_front("talk"), b_front("tell"), b_front("hit"), b_side(), b_back()]
    world = [w_front("idle"), w_front("talk"), w_front("tell"), w_front("hit"), w_side(), w_back()]
    for prefix, group, hgt in (("battle", battle, 80), ("world", world, 46)):
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            check_height(img, hgt, name)
            img.save(os.path.join(OUT, name))
            feet[name] = foot_point(cv)
            cells[name] = img
    for i, e in enumerate(("neutral", "warm", "concern", "surprised")):
        img = portrait(e).image()
        name = "portrait-%d.png" % i
        img.save(os.path.join(OUT, name))
        cells[name] = img
    with open(os.path.join(OUT, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    contact_sheet(cells, feet)
    return cells, feet


def contact_sheet(cells, feet, S=3):
    from PIL import ImageFont
    BG = (44, 44, 62, 255)
    GROUND = (70, 70, 96, 255)
    font = ImageFont.load_default()

    def ref(n):
        p = os.path.join(REF, n)
        return Image.open(p).convert("RGBA") if os.path.exists(p) else None

    def up(im):
        return im.resize((im.width * S, im.height * S), Image.NEAREST)

    rows = []
    r1 = [(cells["battle-%d.png" % i], "battle-%d" % i) for i in range(6)]
    for n in ("dev_80_idle_down.png", "jakerson_80_idle_down.png"):
        im = ref(n)
        if im:
            rows_bb = im.getbbox()
            im = im.crop((0, 0, im.width, rows_bb[3]))    # stand on the same ground line
            r1.append((im, "ref " + n.split("_")[0] + " 80"))
    r2 = [(cells["world-%d.png" % i], "world-%d" % i) for i in range(6)]
    for n in ("jules_idle_down_0_37_61.png", "imani_idle_down_0_36_55.png", "dev_52_idle_down.png"):
        im = ref(n)
        if im:
            bb = im.getbbox()
            im = im.crop((0, 0, im.width, bb[3]))
            r2.append((im, "ref " + n.split("_")[0]))
    r3 = [(cells["portrait-%d.png" % i], "portrait-%d" % i) for i in range(4)]
    for n in ("dev_portrait_0.png", "jakerson_portrait_0.png"):
        im = ref(n)
        if im:
            r3.append((im.resize((64, 64), Image.NEAREST), "ref " + n.split("_")[0]))  # 2x art back to 1x
    rows = [r1, r2, r3]
    pad = 12
    widths = [sum(im.width * S + pad for im, _ in r) + pad for r in rows]
    heights = [max(im.height * S for im, _ in r) + 26 for r in rows]
    W, H = max(widths), sum(heights) + pad * 2
    sheet = Image.new("RGBA", (W, H), BG)
    d = ImageDraw.Draw(sheet)
    y = pad
    for r, rh in zip(rows, heights):
        x = pad
        base = y + rh - 18
        if r is not r3:
            d.rectangle([0, base, W, base + 1], fill=GROUND)
        for im, label in r:
            big = up(im)
            top = base - big.height if r is not r3 else y
            sheet.alpha_composite(big, (x, top))
            d.text((x, base + 4), label, fill=(200, 200, 220, 255), font=font)
            x += big.width + pad
        y += rh
    sheet.save(os.path.join(OUT, "sheet.png"))


if __name__ == "__main__":
    cells, feet = build()
    for k, v in feet.items():
        print(k, cells[k].size, v)
