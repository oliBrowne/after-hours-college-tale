#!/usr/bin/env python3
"""Random-encounter route trainers, batch A: cyclist, runner, hippie (hacky sack), drummer.

One shared module for all four ids (the per-id draw_<id>.py scripts are thin wrappers that call
build("<id>")).  The raster engine (Cv) is copied verbatim from Sunbeam / Professor Eric: parts are
masks shaded with material ramps from a top-left key light, given inner 1px lines and an ink
silhouette.  Everything is drawn at its final pixel size; nothing drawn is ever resampled (only the
contact sheets are nearest-neighbour blow-ups).

The bodies share one rig laid out in "Sunbeam units" (82-unit body: head 0-22, shoulders ~25,
hem ~46.5, soles 81.4).  The head zone keeps its native size, the body below it stretches to each
trainer's height, and the width scales with each trainer's build -- so one set of pose numbers gives
lanky, short and stocky people.  Faces are hand-placed pixels at each size (battle, world, portrait).

Outputs per id, in /tmp/claude-0/newcast/<id>/out/ (Eric's layout, NO entrance cell):
  battle-0..5.png   battle cells (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  world-0..5.png    the same poses redrawn at world height
  portrait-0..3.png 64x64 (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk/<id>-0..3.png  mouth-open portraits (only mouth pixels differ)
  idle/<id>-blink.png, <id>-pose1.png, <id>-pose2.png   world-front extras
  feet.json, meta.json
and /tmp/claude-0/newcast/<id>/sheet.png (3x contact sheet beside the cast).
"""
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ROOT = "/tmp/claude-0/newcast"
CAST_REF = "/tmp/claude-0/designs/cast-reference.png"

# --------------------------------------------------------------------------
# shared palette
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline (same ink as the cast)
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
NOTE = (255, 228, 120)
RAMP = {
    "metal": [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "tyre": [(10, 10, 14), (26, 26, 32), (40, 40, 50), (62, 62, 74), (92, 92, 106)],
    "white": [(90, 90, 104), (176, 178, 190), (222, 222, 230), (242, 242, 246), (255, 255, 255)],
    "wood": [(96, 60, 24), (170, 120, 60), (214, 170, 100), (236, 206, 146), (250, 232, 190)],
}


# --------------------------------------------------------------------------
# tiny raster engine (verbatim from draw_sunbeam.py / draw_eric.py)
# --------------------------------------------------------------------------
class Cv:
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

    def part(self, name, mask, ramp, edge="dark", noedge=(), lv=None, tex=0.0, seed=1, **kw):
        if isinstance(ramp, str):
            ramp = RAMP[ramp]
        mask = mask.copy()
        if not mask.any():
            return mask
        if lv is None:
            lv = self.levels(mask, **kw)
        if tex:
            rng = np.random.default_rng(seed)
            r = rng.random(mask.shape)
            up = (r < tex / 2) & (lv < 4)
            dn = (r > 1 - tex / 2) & (lv > 1)
            iso = np.ones_like(up)
            iso[:, 1:] = ~(up[:, :-1] | dn[:, :-1])
            lv = lv + (up & iso) - (dn & iso)
        pid = len(self.names)
        self.names[name] = pid
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
                if dy == 1:
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

    def line(self, x0, y0, x1, y1, c, only_empty=False, only_own=None):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        dx, dy = abs(x1 - x0), -abs(y1 - y0)
        sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
        err = dx + dy
        while True:
            ok = 0 <= x0 < self.w and 0 <= y0 < self.h
            if ok and only_empty and self.alpha[y0, x0]:
                ok = False
            if ok and only_own is not None and self.own[y0, x0] not in only_own:
                ok = False
            if ok:
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

    def image(self):
        im = np.zeros((self.h, self.w, 4), np.uint8)
        im[..., :3] = np.clip(self.col, 0, 255)
        im[..., 3] = np.where(self.alpha, 255, 0)
        return Image.fromarray(im, "RGBA")


def mix(a, b, t):
    return tuple(int(round(a[i] * (1 - t) + b[i] * t)) for i in range(3))


def recolor(cv, name, sel, src, dst):
    """Repaint the pixels of part `name` inside `sel` from ramp src to ramp dst, tone for tone."""
    if name not in cv.names:
        return
    m = (cv.own == cv.names[name]) & sel
    for i in range(5):
        hit = m & np.all(cv.col == np.array(src[i]), axis=2)
        cv.col[hit] = dst[i]


def ids(cv, *names):
    return [cv.names[n] for n in names if n in cv.names]


def own_mask(cv, *names):
    ids = [cv.names[n] for n in names if n in cv.names]
    return np.isin(cv.own, ids)


# --------------------------------------------------------------------------
# rig
# --------------------------------------------------------------------------
KW = 52 / 82          # world head scale (same head size as the 52px cast)


class Rig:
    """Body coordinates in Sunbeam units: Y(u) keeps the head (u <= 22) at native size and
    stretches the body below it to this trainer's height; X(dx) scales by build."""

    def __init__(self, c, t, kh, sx, sy, battle):
        self.c, self.t, self.kh, self.sx, self.sy, self.battle = c, t, kh, sx, sy, battle
        self.k = (kh + sy) / 2.0

    def X(self, dx):
        return self.c + dx * self.sx

    def Y(self, u):
        return self.t + u * self.kh if u <= 22 else self.t + 22 * self.kh + (u - 22) * self.sy

    def Q(self, dx, u):
        return (self.X(dx), self.Y(u))

    def r(self, v, lo=1.0):
        return max(lo, v * self.k)


class HF:
    """Head frame: (x, t) = head centre line and hair top, s = scale (1 battle, KW world, 1.83 portrait)."""

    def __init__(self, x, t, s):
        self.x, self.t, self.s = x, t, s

    def P(self, dx, u):
        return (self.x + dx * self.s, self.t + u * self.s)

    @property
    def big(self):
        return self.s >= 0.8


def fist(cv, x, y, name, R, skin, r=2.4):
    rr = R.r(r, 1.6)
    m = cv.ell(x, y, rr, rr)
    cv.part(name, m, skin, edge="ink", rad=2.5, soft=0.7, bias=0.05)
    if R.battle:
        cv.put(x + 1, y + 1, skin[1])
    return m


def open_hand(cv, x, y, name, R, skin, flip=1):
    if R.battle:
        m = cv.ell(x, y, 2.5, 3.1) | cv.capsule(x - 2.0 * flip, y + 1.0, x - 3.5 * flip, y - 0.8, 1.0)
        cv.part(name, m, skin, edge="ink", rad=2.5, soft=0.7, bias=0.08)
        for fx in (x - 1, x + 1):
            cv.vline(int(round(fx)), int(round(y - 3)), int(round(y - 1)), skin[1])
    else:
        m = cv.ell(x, y, 1.7, 2.1) | cv.capsule(x - 1.3 * flip, y + 0.6, x - 2.3 * flip, y - 0.6, 0.7)
        cv.part(name, m, skin, edge="ink", lv=np.where(m, 3, 0))
    return m


def arm(cv, R, name, pts, skin, cloth=None, sleeve="long", tex=0.0, seed=5):
    """pts in pixels.  sleeve: long (cloth to the wrist), elbow (cloth to the elbow, pushed up),
    short (cap sleeve), none (bare)."""
    r = R.r(2.4, 1.7)
    if sleeve == "long":
        m = cv.chain(pts, R.r(2.75, 1.8))
        cv.part(name, m, cloth, rad=max(2, 3 * R.k), soft=0.8, cuts=(0.28, 0.52, 0.86), tex=tex, seed=seed)
        return m
    m = cv.chain(pts, r)
    cv.part(name, m, skin, rad=max(2, 3 * R.k), soft=0.8, cuts=(0.28, 0.52, 0.86), bias=0.04)
    if sleeve == "elbow":
        (x0, y0), (x1, y1) = pts[0], pts[1]
        sl = cv.capsule(x0, y0, x1, y1, R.r(3.0, 2.0), R.r(3.0, 1.9))
        cv.part(name + "sl", sl, cloth, noedge=("torso",), rad=3, soft=0.8, cuts=(0.28, 0.52, 0.86), tex=tex, seed=seed)
    elif sleeve == "short":
        (x0, y0), (x1, y1) = pts[0], pts[1]
        f = 0.5
        sl = cv.capsule(x0, y0, x0 + (x1 - x0) * f, y0 + (y1 - y0) * f, R.r(3.2, 2.1), R.r(3.0, 2.0))
        cv.part(name + "sl", sl, cloth, noedge=("torso",), rad=3, soft=0.8, cuts=(0.30, 0.55, 0.88))
    return m


def sneaker(cv, R, name, fx, up, sole, lift=0.0, side=False, high=False):
    """Front (or side-profile) sneaker standing on the ground row (raised by `lift` px)."""
    yb = R.Y(81.4) - lift
    hs = 1.2 if R.battle else 0.6
    k = R.k
    if side:
        s_m = cv.rect(fx - 3.2 * k, yb - hs, fx + 5.4 * k, yb)
        u_m = (cv.ell(fx + 1.0 * k, yb - hs - 0.2, 4.4 * k, 3.4 * k) & (cv.Y < yb - hs + 0.5)) | \
              cv.rect(fx - 3.2 * k, yb - hs - (3.2 if high else 1.6) * k, fx + 1.0 * k, yb - hs)
    else:
        s_m = cv.rect(fx - 4.1 * k, yb - hs, fx + 4.1 * k, yb)
        u_m = (cv.ell(fx, yb - hs - 0.2, 3.9 * k, 3.6 * k) & (cv.Y < yb - hs + 0.5))
        if high:
            u_m |= cv.rect(fx - 3.0 * k, yb - hs - 4.2 * k, fx + 3.0 * k, yb - hs)
    u_m &= ~s_m
    cv.part(name + "U", u_m, up, edge="ink", rad=2.5 * k + 0.5, soft=0.6, cuts=(0.25, 0.5, 0.85), bias=0.05)
    cv.part(name + "S", s_m, sole, edge="ink", lv=np.where(s_m, 3, 0) - np.where(s_m & (cv.X > fx + 1), 1, 0))
    return u_m | s_m


def note(cv, x, y, glyph, col=NOTE, over=False):
    for j, row in enumerate(glyph):
        for i, ch in enumerate(row):
            if ch == "#":
                px, py = x + i, y + j
                if 0 <= px < cv.w and 0 <= py < cv.h and (over or not cv.alpha[py, px]):
                    cv.put(px, py, col)


NOTE_A = ["..##.", "..#.#", "..#..", "###..", "##..."]
NOTE_S = [".#", ".#", "##"]


def sparkle(cv, x, y, big=False, col=SPARK2):
    pts = [(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)]
    if big:
        pts += [(x - 2, y), (x + 2, y), (x, y - 2), (x, y + 2)]
    for p in pts:
        if 0 <= p[0] < cv.w and 0 <= p[1] < cv.h and not cv.alpha[p[1], p[0]]:
            cv.put(p[0], p[1], col)
    cv.put(x, y, WHITE)


def sweat(cv, x, y, battle):
    if battle:
        cv.puts([(x, y), (x - 1, y + 1), (x, y + 1), (x + 1, y + 1), (x, y + 2)], SWEAT)
        cv.put(x - 1, y + 1, SWEAT_HI)
    else:
        cv.puts([(x, y), (x, y + 1)], SWEAT)


def empty_put(cv, x, y, c):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < cv.w and 0 <= y < cv.h and not cv.alpha[y, x]:
        cv.put(x, y, c)


def arc_marks(cv, cx, cy, r, a0, a1, col, n=None):
    """A short motion arc (only on empty pixels)."""
    n = n or max(3, int(abs(a1 - a0) * r))
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        empty_put(cv, cx + math.cos(a) * r, cy + math.sin(a) * r, col)


# ==========================================================================
# base character
# ==========================================================================
EXPRS = ("neutral", "warm", "concern", "surprised")


class Char:
    id = "?"
    title = "?"
    H, WH = 76, 51          # battle / world body height
    build = 1.0             # width scale
    hipw = 1.0              # leg spread
    face_w = 1.0
    top = 0.0               # units the hair/hat reaches above u=0
    BW, BHc = 84, 90        # battle canvas
    WWc, WHc = 56, 58       # world canvas
    lashes = False
    hit_dx = 2
    skin = hair = None
    iris = (70, 44, 30)
    iris_d = (40, 24, 18)
    brow = None
    lip = None

    # ---------------- rig ----------------
    def rig(self, battle, cdx=0):
        if battle:
            Hc, W, Hb, kh, sx = self.BHc, self.BW, self.H, 1.0, self.build
        else:
            Hc, W, Hb, kh, sx = self.WHc, self.WWc, self.WH, KW, KW * self.build
        t = Hc - Hb + self.top * kh
        sy = (Hc - 0.6 - t - 22 * kh) / 59.4
        return Cv(W, Hc), Rig(W // 2 + cdx, t, kh, sx, sy, battle)

    def hf(self, R, dx=0.0):
        return HF(R.c + dx, R.t, R.kh)

    # ---------------- generic pieces ----------------
    def standing_legs(self, cv, R, raise_leg=None, stance=0.0):
        """raise_leg: None or (s, knee(dx,u), ankle(dx,u), lift_px) for one bent leg."""
        legs = {}
        for s in (-1, 1):
            hip = R.Q(s * 4.6 * self.hipw, 47)
            if raise_leg and raise_leg[0] == s:
                knee, ank = R.Q(*raise_leg[1]), R.Q(*raise_leg[2])
                lift = R.Y(81.4) - ank[1] - 3.4 * R.k
            else:
                knee = R.Q(s * (4.9 * self.hipw + stance * 0.5), 62)
                ank = R.Q(s * (5.2 * self.hipw + stance), 75.0)
                lift = 0.0
            legs[s] = (hip, knee, ank, lift)
        # raised leg last so it sits in front of the standing one
        order = (-1, 1) if not raise_leg else (-raise_leg[0], raise_leg[0])
        for s in order:
            hip, knee, ank, lift = legs[s]
            self.leg(cv, R, "leg%d" % s, [hip, knee, ank], s)
            self.shoe(cv, R, "shoe%d" % s, ank[0] + s * 0.4 * R.k, lift, s)
        self.hips(cv, R, legs)
        return legs

    def hips(self, cv, R, legs):
        pass

    def torso_mask(self, cv, R, back=False, sw=1.0, belly=0.0, ww=1.0, hw=1.0):
        Q = R.Q
        m = cv.poly([Q(-6, 22.5), Q(6, 22.5), Q(10.5 * sw, 23.6), Q(12 * sw, 27.5), Q(11.2 * ww, 36), Q(11.5 * hw, 47),
                     Q(-11.5 * hw, 47), Q(-11.2 * ww, 36), Q(-12 * sw, 27.5), Q(-10.5 * sw, 23.6)])
        if belly:
            m |= cv.ell(*Q(0, 40), 12.5 * R.sx * belly, 7.2 * R.sy) & cv.half(y=R.Y(31))
        return m

    def neck(self, cv, R, dx=0.0):
        cv.part("neck", cv.rect(R.X(-2.5) + dx, R.Y(18), R.X(2.5) + dx, R.Y(23.5)), self.skin, rad=2, bias=-0.15)

    # ---------------- head ----------------
    def face_mask(self, cv, hf, view="front"):
        s, fw = hf.s, self.face_w
        if view == "side":
            m = cv.ell(*hf.P(1, 13.4), 7.2 * s * fw, 7.4 * s) | cv.ell(*hf.P(3, 16), 5 * s * fw, 6.6 * s) | \
                cv.ell(*hf.P(4.6, 19.5), 3.4 * s, 3 * s)
            return m
        m = cv.ell(*hf.P(0, 13.5), 7.2 * s * fw, 7.3 * s) | cv.ell(*hf.P(0, 16), 6.2 * s * fw, 6.8 * s)
        if s > 1.5:
            m |= cv.ell(*hf.P(0, 18.9), 6.3 * s * fw, 4.5 * s)
        return m

    def ears(self, cv, hf):
        s = hf.s
        m = cv.empty()
        for sd in (-1, 1):
            m |= cv.ell(*hf.P(sd * 7.3 * self.face_w, 14.5), max(1.0, 1.5 * s), max(1.3, 2.2 * s))
        cv.part("ears", m, self.skin, edge="dark", rad=2, bias=-0.1)

    def head(self, cv, hf, view, pose, extra=None):
        if view == "front":
            self.ears(cv, hf)
            cv.part("face", self.face_mask(cv, hf), self.skin, rad=6 * hf.s, soft=1.4 if hf.big else 1.0,
                    cuts=(0.22, 0.48, 0.86), bias=0.06)
            self.hair_front(cv, hf, pose, extra)
            if hf.big:
                self.feats_b(cv, hf, pose, extra)
            else:
                self.feats_w(cv, hf, pose, extra)
            self.face_extra(cv, hf, "front", pose, extra)
        elif view == "side":
            self.hair_side_back(cv, hf)
            cv.part("face", self.face_mask(cv, hf, "side"), self.skin, rad=6 * hf.s, soft=1.2, cuts=(0.22, 0.48, 0.86), bias=0.10)
            if hf.big:
                cv.part("nose", cv.ell(*hf.P(8.4, 15.6), 1.6, 1.5), self.skin, edge="ink", noedge=("face",), rad=1.5, bias=0.15)
            self.hair_side(cv, hf)
            self.feats_side(cv, hf)
            self.face_extra(cv, hf, "side", pose, extra)
        else:
            self.hair_back_view(cv, hf)

    # face features: battle front ------------------------------------------------
    def feats_b(self, cv, hf, pose, extra):
        c, t = int(round(hf.x)), int(round(hf.t))
        sk = self.skin
        ey = t + 13
        g = -1 if extra == "glance" else (1 if extra == "glanceR" else 0)
        up = extra == "lookup"
        for side in (-1, 1):
            x0 = c - 5 if side < 0 else c + 2
            if pose == "blink" or extra == "blink":
                cv.hline(x0, x0 + 3, ey + 1, EYE)
                if self.lashes:
                    cv.put(x0 - 1 if side < 0 else x0 + 4, ey + 1, EYE)
            elif pose in ("idle", "talk"):
                cv.hline(x0, x0 + 3, ey, EYE)
                ix = x0 + 1 + g
                yy = ey + 1 - (1 if up else 0)
                cv.put(x0, ey + 1, SCLERA); cv.put(x0 + 3, ey + 1, SCLERA)
                cv.put(ix, yy, WHITE if side < 0 else self.iris); cv.put(ix + 1, yy, self.iris_d if side < 0 else WHITE)
                if not up:
                    cv.put(ix, yy + 1, self.iris); cv.put(ix + 1, yy + 1, self.iris_d)
                else:
                    cv.hline(x0, x0 + 3, ey - 1, EYE)
                    cv.put(ix, ey, self.iris); cv.put(ix + 1, ey, self.iris_d)
                    cv.put(x0, ey, SCLERA); cv.put(x0 + 3, ey, SCLERA)
                if self.lashes:
                    cv.put(x0 - 1 if side < 0 else x0 + 4, ey - 1 if not up else ey - 2, EYE)
            elif pose == "tell":
                cv.puts([(x0, ey + 1), (x0 + 1, ey), (x0 + 2, ey), (x0 + 3, ey + 1)], EYE)
                if self.lashes:
                    cv.put(x0 - 1 if side < 0 else x0 + 4, ey, EYE)
            elif pose == "hit":
                mp = ["K...", ".KK.", "K..."] if side < 0 else ["...K", ".KK.", "...K"]
                for j, row in enumerate(mp):
                    for i, ch in enumerate(row):
                        if ch == "K":
                            cv.put(x0 + i, ey - 1 + j + 1, EYE)
        b = self.brow
        if pose == "hit":
            cv.puts([(c - 5, t + 10), (c - 4, t + 10), (c - 3, t + 11)], b); cv.puts([(c + 5, t + 10), (c + 4, t + 10), (c + 3, t + 11)], b)
        elif pose == "tell":
            cv.puts([(c - 5, t + 10), (c - 4, t + 10), (c - 3, t + 11)], b); cv.puts([(c + 5, t + 10), (c + 4, t + 10), (c + 3, t + 11)], b)
        else:
            dy = -1 if up or pose == "talk" else 0
            cv.puts([(c - 5, t + 11 + dy), (c - 4, t + 10 + dy), (c - 3, t + 10 + dy)], b)
            cv.puts([(c + 5, t + 11 + dy), (c + 4, t + 10 + dy), (c + 3, t + 10 + dy)], b)
        # nose
        cv.put(c, t + 16, sk[3]); cv.put(c + 1, t + 17, sk[1]); cv.put(c, t + 17, mix(sk[1], sk[2], 0.5))
        self.mouth_b(cv, c, t + 19, pose)

    def mouth_b(self, cv, c, y, pose):
        L = self.lip or self.skin[1]
        if pose in ("idle", "blink"):
            cv.put(c - 2, y, MOUTH); cv.put(c + 2, y, MOUTH); cv.hline(c - 1, c + 1, y + 1, MOUTH)
            cv.put(c, y + 2, L)
        elif pose == "talk":
            cv.put(c - 3, y, MOUTH); cv.put(c + 3, y, MOUTH); cv.hline(c - 2, c + 2, y, TEETH)
            cv.hline(c - 2, c + 2, y + 1, MOUTH); cv.put(c, y + 1, TONGUE); cv.put(c - 1, y + 1, TONGUE)
            cv.hline(c - 1, c + 1, y + 2, L)
        elif pose == "tell":
            cv.put(c - 4, y - 1, MOUTH); cv.put(c + 4, y - 1, MOUTH); cv.put(c - 3, y, MOUTH); cv.put(c + 3, y, MOUTH)
            cv.hline(c - 2, c + 2, y, TEETH); cv.hline(c - 2, c + 2, y + 1, MOUTH); cv.hline(c - 1, c + 1, y + 2, L)
        elif pose == "hit":
            cv.hline(c - 1, c + 1, y, MOUTH); cv.hline(c - 2, c + 2, y + 1, MOUTH); cv.put(c, y + 1, TONGUE)
            cv.hline(c - 1, c + 1, y + 2, MOUTH)
        elif pose == "drink":
            cv.hline(c - 1, c + 1, y + 1, MOUTH)

    # world front --------------------------------------------------------------
    def feats_w(self, cv, hf, pose, extra):
        c, t = int(round(hf.x)), int(round(hf.t))
        ey = t + 8
        g = -1 if extra == "glance" else (1 if extra == "glanceR" else 0)
        up = 1 if extra == "lookup" else 0
        for side in (-1, 1):
            ex = c - 2 if side < 0 else c + 2
            if pose == "blink" or extra == "blink":
                cv.put(ex, ey + 1, EYE); cv.put(ex + (-1 if side < 0 else 1), ey + 1, EYE)
            elif pose in ("idle", "talk"):
                # 2x2: lid row + (pupil, white) so the eye reads on every skin tone
                xo = ex + (-1 if side < 0 else 1)
                cv.put(ex, ey - up, EYE); cv.put(xo, ey - up, EYE)
                px = ex if g == 0 else (min(ex, xo) if g < 0 else max(ex, xo))
                cv.put(ex + xo - px, ey + 1 - up, SCLERA)
                cv.put(px, ey + 1 - up, EYE)
                if self.lashes:
                    cv.put(xo + (-1 if side < 0 else 1), ey - 1 - up, EYE)
            elif pose == "tell":
                cv.put(ex - 1, ey + 1, EYE); cv.put(ex, ey, EYE); cv.put(ex + 1, ey + 1, EYE)
            elif pose == "hit":
                o = 0 if side < 0 else 0
                cv.put(ex - side, ey, EYE); cv.put(ex, ey + 1, EYE); cv.put(ex - side, ey + 2, EYE)
        if pose == "hit":
            cv.put(c - 3, ey - 2, self.brow); cv.put(c + 3, ey - 2, self.brow)
        my = t + 12
        sk = self.skin
        cv.put(c + 1, t + 10, sk[1])
        if pose == "talk":
            cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c, my + 1, TONGUE)
        elif pose == "hit":
            cv.put(c, my, MOUTH); cv.put(c, my + 1, MOUTH)
        elif pose == "tell":
            cv.hline(c - 1, c + 1, my, TEETH); cv.put(c - 2, my - 1, MOUTH); cv.put(c + 2, my - 1, MOUTH)
        elif pose == "drink":
            cv.put(c, my, MOUTH)
        else:
            cv.hline(c - 1, c + 1, my, MOUTH); cv.put(c - 2, my - 1, MOUTH) if False else None

    # side profile ---------------------------------------------------------------
    def feats_side(self, cv, hf):
        c, t = int(round(hf.x)), int(round(hf.t))
        if hf.big:
            cv.hline(c + 4, c + 6, t + 13, EYE); cv.put(c + 5, t + 14, self.iris); cv.put(c + 6, t + 14, self.iris_d)
            if self.lashes:
                cv.put(c + 3, t + 12, EYE)
            cv.puts([(c + 4, t + 11), (c + 5, t + 10), (c + 6, t + 10)], self.brow)
            cv.put(c + 7, t + 19, MOUTH); cv.put(c + 6, t + 19, MOUTH); cv.put(c + 8, t + 19, self.skin[2])
            cv.put(c + 7, t + 20, self.lip or self.skin[1])
        else:
            cv.put(c + 3, t + 8, EYE); cv.put(c + 3, t + 9, self.iris_d)
            cv.put(c + 5, t + 12, MOUTH)

    # hooks -----------------------------------------------------------------------
    def face_extra(self, cv, hf, view, pose, extra):
        pass

    def hair_front(self, cv, hf, pose, extra):
        pass

    def hair_side_back(self, cv, hf):
        pass

    def hair_side(self, cv, hf):
        pass

    def hair_back_view(self, cv, hf):
        pass

    def behind_front(self, cv, R, pose, extra):
        pass

    # ---------------- cells ----------------
    def front(self, pose, battle=True, extra=None):
        cv, R = self.rig(battle)
        hx = (self.hit_dx if battle else 1) if pose == "hit" else 0
        hf = self.hf(R, hx)
        self.st = {}
        self.behind_front(cv, R, pose, extra)
        self.legs_front(cv, R, pose, extra)
        self.neck(cv, R, hx)
        self.torso_front(cv, R, pose, extra)
        self.arms_front(cv, R, pose, extra)
        hp = "blink" if extra == "blink" else pose
        self.head(cv, hf, "front", hp, extra)
        self.over_head(cv, R, hf, pose, extra)
        cv.outline()
        self.after_front(cv, R, hf, pose, extra)
        return cv, R

    def over_head(self, cv, R, hf, pose, extra):
        pass

    def after_front(self, cv, R, hf, pose, extra):
        pass

    def legs_front(self, cv, R, pose, extra):
        self.standing_legs(cv, R)

    def side(self, battle=True):
        cv, R = self.rig(battle, cdx=-2 if battle else -1)
        hf = self.hf(R)
        self.st = {}
        self.side_behind(cv, R)
        for j, (lx, lean) in enumerate(self.side_stride):
            x0 = R.X(lx * self.hipw)
            x1 = x0 + lean * R.k
            self.leg(cv, R, "leg%d" % j, [(x0, R.Y(47)), ((x0 + x1) / 2, R.Y(62)), (x1, R.Y(75.0))], 0, far=(j == 0))
            self.shoe(cv, R, "shoe%d" % j, x1, 0.0, 0, side=True, far=(j == 0))
        self.neck(cv, R)
        self.torso_side(cv, R)
        self.arm_side(cv, R)
        self.head(cv, hf, "side", "idle")
        cv.outline()
        self.after_side(cv, R, hf)
        return cv, R

    side_stride = ((-2.5, -0.8), (1.5, 0.8))

    def side_behind(self, cv, R):
        pass

    def after_side(self, cv, R, hf):
        pass

    def back(self, battle=True):
        cv, R = self.rig(battle)
        hf = self.hf(R)
        self.st = {}
        self.back_behind(cv, R)
        self.standing_legs(cv, R)
        self.neck(cv, R)
        self.torso_back(cv, R)
        self.arms_back(cv, R)
        self.head(cv, hf, "back", "idle")
        self.back_over(cv, R, hf)
        cv.outline()
        self.after_back(cv, R, hf)
        return cv, R

    def back_behind(self, cv, R):
        pass

    def back_over(self, cv, R, hf):
        pass

    def after_back(self, cv, R, hf):
        pass

    # ---------------- portrait ----------------
    def portrait(self, expr, talk=False):
        cv = Cv(64, 64, open_bottom=True)
        c = 32
        lift = -1 if expr == "surprised" else 0
        hf = HF(c, self.p_top + lift, 1.75)
        self.p_behind(cv, hf, expr)
        self.p_shoulders(cv, c, expr)
        cv.part("neck", cv.rect(c - 5, 40, c + 5, 52), self.skin, rad=4, bias=-0.18)
        self.p_collar(cv, c, expr)
        for sd in (-1, 1):
            m = cv.ell(c + sd * 13.6 * self.face_w, 30 + lift, 2.6, 3.8)
            cv.part("ear%d" % sd, m, self.skin, edge="dark", rad=2, bias=-0.1)
        face = cv.ell(c, 28 + lift * 0, 13.2 * self.face_w, 13.6) | cv.ell(c, 33, 11.2 * self.face_w, 12.4) | \
            cv.ell(c, 38, 11.6 * self.face_w, 8.2)
        cv.part("face", face, self.skin, rad=11, soft=2.2, cuts=(0.16, 0.42, 0.86), bias=0.06)
        self.p_face_marks(cv, c, expr)
        self.p_mouth(cv, c, 41, expr, talk)
        ey = {"neutral": 25, "warm": 25, "concern": 24, "surprised": 23}[expr]
        self.p_eye(cv, c - 11, ey, expr, -1)
        self.p_eye(cv, c + 4, ey, expr, 1)
        by = {"neutral": 22, "warm": 22, "concern": 22, "surprised": 20}[expr]
        self.p_brows(cv, c, by, expr)
        self.p_hair(cv, hf, expr)
        cv.outline()
        self.p_after(cv, c, expr)
        return cv

    p_top = -0.5

    def p_behind(self, cv, hf, expr):
        pass

    def p_collar(self, cv, c, expr):
        pass

    def p_after(self, cv, c, expr):
        if expr == "surprised":
            cv.puts([(5, 14), (5, 15), (5, 16), (5, 18), (2, 16), (1, 15), (0, 14)], SPARK2)
        if expr == "concern":
            cv.puts([(13, 17), (12, 18), (13, 18), (14, 18), (13, 19)], SWEAT); cv.put(12, 18, SWEAT_HI)

    def p_face_marks(self, cv, c, expr):
        sk = self.skin
        fid = cv.names["face"]
        for s in (-1, 1):
            bx = c + s * 8
            for y in (34, 35):
                for x in range(bx - 2, bx + 3):
                    if cv.own[y, x] == fid:
                        cv.put(x, y, mix(cv.get(x, y), self.blush, 0.32 if abs(x - bx) < 2 else 0.16))
        cv.puts([(c - 1, 28), (c - 1, 29), (c - 1, 30), (c - 1, 31)], sk[3])
        cv.puts([(c + 1, 31), (c + 1, 32), (c + 2, 33)], sk[1]); cv.puts([(c - 1, 34), (c, 34), (c + 1, 34)], sk[1])
        cv.put(c - 2, 33, sk[1])

    blush = (232, 120, 110)

    def p_eye(self, cv, ex, ey, expr, side):
        maps = {
            "neutral": [".KKKKK.", "KWHDIWK", ".WIIIW.", "..SSS.."],
            "warm": [".......", "..KKK..", ".K...K.", "K.....K", ".SSSSS."],
            "concern": [".KKKKK.", "KWHDIWK", ".WIIIW.", "..WWW..", "..SSS.."],
            "surprised": ["..KKK..", ".KWWWK.", "KWHDIWK", "KWIDIWK", ".KWIWK.", "..SSS.."],
        }
        pal = {"K": EYE, "I": self.iris, "D": self.iris_d, "H": WHITE, "W": SCLERA, "S": self.skin[1]}
        rows = maps[expr]
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == ".":
                    continue
                x = ex + i if side < 0 else ex + (6 - i)
                col = pal[ch]
                if ch == "H" and side > 0:
                    col = self.iris
                cv.put(x, ey + j, col)
        if side > 0:
            for j, row in enumerate(rows):
                if "H" in row:
                    i = row.index("H")
                    cv.put(ex + (6 - i) - 2, ey + j, WHITE)
        if self.lashes:
            r0 = next(j for j, row in enumerate(rows) if "K" in row)
            xo = ex - 1 if side < 0 else ex + 7
            cv.put(xo, ey + r0, EYE)
            cv.put(xo + (-1 if side < 0 else 1), ey + r0 - 1, EYE)

    def p_brows(self, cv, c, by, expr):
        if expr == "concern":
            left = [(-11, 0), (-10, 0), (-9, -1), (-8, -1), (-7, -2), (-6, -2), (-5, -3)]
        elif expr == "surprised":
            left = [(-12, 0), (-11, -1), (-10, -2), (-9, -2), (-8, -2), (-7, -2), (-6, -1)]
        elif expr == "warm":
            left = [(-12, 1), (-11, 0), (-10, -1), (-9, -1), (-8, -1), (-7, -1), (-6, 0)]
        else:
            left = [(-12, 1), (-11, 0), (-10, 0), (-9, 0), (-8, 0), (-7, 0), (-6, 0)]
        thick = self.brow_thick
        for side in (-1, 1):
            for i, (dx, dy) in enumerate(left):
                x = c + dx if side < 0 else c - dx
                cv.put(x, by + dy, self.brow)
                if thick and 0 < i < 6:
                    cv.put(x, by + dy - 1, self.brow2)

    brow_thick = True

    def p_mouth(self, cv, c, my, expr, talk=False):
        LIP = self.lip or self.skin[1]
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


# ==========================================================================
# CYCLIST -- bike commuter: mint helmet, purple rain shell, carries her front wheel
#            (Boulder rule: lock the frame, take the wheel)
# ==========================================================================
class Cyclist(Char):
    id = "cyclist"
    title = "Cyclist (bike commuter, carries her front wheel)"
    H, WH = 75, 50
    build = 0.95
    hipw = 0.95
    top = -1.0
    lashes = True
    skin = [(112, 60, 44), (204, 144, 108), (236, 186, 146), (248, 210, 176), (253, 230, 204)]
    hair = [(12, 12, 22), (28, 28, 44), (46, 46, 66), (70, 72, 96), (104, 108, 136)]
    helmet = [(16, 72, 66), (38, 140, 124), (72, 194, 170), (128, 228, 202), (196, 250, 232)]
    jacket = [(46, 22, 78), (94, 50, 148), (130, 84, 194), (168, 128, 224), (210, 182, 246)]
    pants = [(22, 34, 44), (44, 62, 76), (64, 86, 100), (90, 114, 128), (126, 150, 162)]
    gum = [(80, 50, 24), (150, 100, 50), (190, 140, 80), (214, 170, 110), (236, 204, 150)]
    iris = (84, 52, 34)
    iris_d = (40, 24, 18)
    brow = (28, 28, 44)
    brow2 = (46, 46, 66)
    lip = (198, 110, 100)
    blush = (240, 130, 120)
    ORANGE = (240, 120, 40)

    # legs: slim dark jeans, rolled cuffs, an orange reflective band on one ankle
    def shoe(self, cv, R, name, fx, lift, s, side=False, far=False):
        sneaker(cv, R, name, fx, RAMP["white"], self.gum, lift, side=side)

    def leg(self, cv, R, name, pts, s, far=False):
        m = cv.chain(pts, R.r(3.0, 1.7))
        m |= cv.capsule(*pts[0], *pts[1], R.r(3.3, 1.9), R.r(3.0, 1.7))
        cv.part(name, m, self.pants, rad=3.2 * R.k + 0.4, soft=0.8, cuts=(0.30, 0.55, 0.88) if not far else (0.45, 0.70, 0.95),
                tex=0.04, seed=11 + s)
        ax, ay = pts[-1]
        cuff = cv.capsule(ax, ay - R.r(2.2, 1.2), ax, ay, R.r(3.3, 1.9)) & cv.half(y=ay - R.r(2.2, 1.2))
        cv.part(name + "cuff", cuff, self.pants, edge="dark", lv=np.where(cuff, 3, 0))
        if s == -1 or (s == 0 and not far):
            band = cuff & (cv.Y >= ay - (0.6 if R.battle else 0.2)) & (cv.Y <= ay + 0.6)
            band = cv.capsule(ax, ay + R.r(1.6, 0.9) - 0.5, ax, ay + R.r(1.6, 0.9) - 0.5, R.r(3.0, 1.8)) & ~own_mask(cv, "shoe%dU" % s, "shoe%dS" % s) if False else band
            cv.part(name + "band", band, [(120, 50, 10), (210, 96, 30), self.ORANGE, (252, 170, 80), (255, 214, 150)], edge=None,
                    lv=np.where(band, 2, 0) + np.where(band & (cv.X < ax), 1, 0))

    def torso_front(self, cv, R, pose, extra, back=False):
        m = self.torso_mask(cv, R, sw=0.88, ww=0.8, hw=0.88)
        cv.part("torso", m, self.jacket, rad=8 * R.k + 1, soft=1.4, cuts=(0.34, 0.60, 0.90))
        Q = R.Q
        # reflective chest stripe
        st = (cv.Y >= R.Y(31.2)) & (cv.Y <= R.Y(31.2) + (1.0 if R.battle else 0.3))
        recolor(cv, "torso", st, self.jacket, RAMP["metal"])
        if not back:
            # zip + high collar
            if R.battle:
                cv.line(R.c, R.Y(23.5), R.c, R.Y(46), self.jacket[1], only_own=ids(cv, "torso"))
                cv.put(R.c + 1, R.Y(24.5), RAMP["metal"][3])
            col = cv.ell(*Q(0, 22.4), 5.6 * R.sx, 2.4 * R.k) & ~cv.ell(*Q(0, 21.2), 3.4 * R.sx, 1.6 * R.k)
            cv.part("collar", col, self.jacket, noedge=("torso",), lv=np.where(col, 3, 0) - np.where(col & (cv.X > R.c + 1), 1, 0))
        # hem band
        hem = (cv.Y >= R.Y(45.6)) & own_mask(cv, "torso")
        recolor(cv, "torso", hem, self.jacket, [self.jacket[0], self.jacket[0], self.jacket[1], self.jacket[2], self.jacket[3]])

    def sleeve_stripe(self, cv, R, name, a, b):
        """A reflective band round the forearm (a->b = elbow->wrist)."""
        x = a[0] + (b[0] - a[0]) * 0.55
        y = a[1] + (b[1] - a[1]) * 0.55
        band = cv.ell(x, y, R.r(3.0, 1.8), R.r(3.0, 1.8)) & own_mask(cv, name)
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy) or 1
        along = ((cv.X - x) * dx + (cv.Y - y) * dy) / L
        band &= np.abs(along) <= (0.8 if R.battle else 0.4)
        recolor(cv, name, band, self.jacket, RAMP["metal"])

    def an_arm(self, cv, R, name, pts):
        arm(cv, R, name, pts, self.skin, self.jacket, "long")
        self.sleeve_stripe(cv, R, name, pts[1], pts[2])

    def wheel_at(self, cv, R, cx, cy, asp=1.0, ang=0.0, name="wheel"):
        r = 14.0 * R.k
        tt = 2.2 if R.battle else 1.6
        outer = cv.ell(cx, cy, r * asp, r, ang)
        tin = cv.ell(cx, cy, (r - tt) * asp, r - tt, ang)
        rin = cv.ell(cx, cy, (r - tt - 1.2) * asp, r - tt - 1.2, ang)
        tyre = outer & ~tin
        lv = np.where(tyre, 2, 0) + np.where(tyre & ((cv.X - cx) + (cv.Y - cy) < -r * 0.6), 1, 0)
        cv.part(name + "T", tyre, "tyre", edge="ink", lv=lv)
        rim = tin & ~rin
        lvr = np.where(rim, 3, 0) - np.where(rim & ((cv.X - cx) + (cv.Y - cy) > r * 0.3), 1, 0)
        cv.part(name + "R", rim, "metal", edge=None, lv=lvr)
        self.st[name] = (cx, cy, r, asp, ang)

    def wheel_after(self, cv, R, name="wheel", spin=False):
        if name not in self.st:
            return
        cx, cy, r, asp, ang = self.st[name]
        mt = RAMP["metal"]
        # the outline pass inked the rim's inner edge: give it back as a darker silver line
        ink = np.all(cv.col == np.array(INK), axis=2)
        rim = own_mask(cv, name + "R") & ink
        cv.col[rim] = mt[1]
        # spokes + hub through the empty middle
        n = 10 if R.battle else 6
        ri = r - (2.2 if R.battle else 1.6) - 1.2
        ca, sa = math.cos(ang), math.sin(ang)
        for i in range(n):
            a = i * 2 * math.pi / n + (0.26 if spin else 0.0)
            ux, uy = math.cos(a) * asp, math.sin(a)
            ux, uy = ux * ca - uy * sa, ux * sa + uy * ca
            if spin and R.battle and i % 2:
                continue
            cv.line(cx + ux * 1.2, cy + uy * 1.2, cx + ux * (ri - 0.2), cy + uy * (ri - 0.2),
                    mt[3] if i % 2 == 0 else mt[2], only_empty=True)
        hub = cv.ell(cx, cy, max(0.9, 1.6 * R.k * asp), max(0.9, 1.6 * R.k))
        for y, x in zip(*np.nonzero(hub & ~cv.alpha)):
            cv.put(x, y, mt[3])
        empty_put(cv, cx, cy, mt[1])
        if spin:
            for j, rr in enumerate((r + 2.2 * R.k, r + 3.8 * R.k)):
                arc_marks(cv, cx, cy, rr, -2.6 + j * 0.3, -1.4 + j * 0.3, SPARK if j else WHITE)
                arc_marks(cv, cx, cy, rr, 0.6 + j * 0.3, 1.8 + j * 0.3, SPARK if j else WHITE)

    def behind_front(self, cv, R, pose, extra):
        Q = R.Q
        if pose == "tell":
            hand = Q(-21, 19)
            self.wheel_at(cv, R, hand[0] - 3.0 * R.k, hand[1] - 12.6 * R.k)
        elif pose == "hit":
            hand = Q(-17, 46)
            self.wheel_at(cv, R, hand[0] - 4.0 * R.k, hand[1] + 11.5 * R.k, asp=0.6, ang=0.35)
        else:
            hand = Q(-17, 45)
            self.wheel_at(cv, R, hand[0] - 1.0 * R.k, hand[1] + 12.8 * R.k)
        self.st["whand"] = hand
        # ponytail tip peeking out behind the neck
        cv.part("tailpeek", cv.capsule(*Q(4.5, 18), *Q(7.0, 24.5), R.r(2.0, 1.2), R.r(1.4, 0.9)), self.hair, rad=2, cuts=(0.4, 0.66, 0.92))

    def legs_front(self, cv, R, pose, extra):
        self.standing_legs(cv, R, stance=0.6 if pose == "tell" else 0.0)

    def arms_front(self, cv, R, pose, extra):
        Q = R.Q
        hand = self.st["whand"]
        # her right arm (viewer left) holds the wheel
        if pose == "tell":
            self.an_arm(cv, R, "armR", [Q(-10.5, 25.5), Q(-17.5, 25), hand])
        elif pose == "hit":
            self.an_arm(cv, R, "armR", [Q(-10.5, 25.5), Q(-15.5, 36), hand])
        else:
            self.an_arm(cv, R, "armR", [Q(-10.5, 25.5), Q(-15, 35.5), hand])
        fist(cv, hand[0], hand[1], "handR", R, self.skin)
        # free arm
        if extra == "strap":
            self.an_arm(cv, R, "armL", [Q(10.5, 25.5), Q(13, 34), Q(4.5, 23.5)])
            fist(cv, *Q(3.5, 22.8), "handL", R, self.skin)
        elif extra == "pocket":
            self.an_arm(cv, R, "armL", [Q(10.5, 25.5), Q(12.5, 35), Q(10.5, 42.5)])
        elif pose == "talk":
            self.an_arm(cv, R, "armL", [Q(10.5, 25.5), Q(17, 31), Q(18.5, 22)])
            open_hand(cv, *Q(18.8, 19.5), "handL", R, self.skin, flip=-1)
        elif pose == "hit":
            self.an_arm(cv, R, "armL", [Q(10.5, 25.5), Q(17, 25), Q(20.5, 17)])
            open_hand(cv, *Q(21, 14.5), "handL", R, self.skin, flip=-1)
        else:
            self.an_arm(cv, R, "armL", [Q(10.5, 25.5), Q(16.5, 34.5), Q(11.8, 43)])
            fist(cv, *Q(11.5, 43.5), "handL", R, self.skin)

    # head: helmet + bangs + ponytail
    def helmet_front(self, cv, hf, pose):
        s = hf.s
        dome = cv.ell(*hf.P(0, 9.6), 9.9 * s, 9.2 * s) & (cv.Y < hf.t + (10.6 + 0.0) * s + 0.02 * (cv.X - hf.x) ** 2 / max(s, 0.5))
        cv.part("helmet", dome, self.helmet, edge="dark", rad=6 * s, soft=1.0 if s < 1.5 else 1.6, cuts=(0.28, 0.54, 0.86))
        hel = self.helmet
        visor = cv.ell(*hf.P(0, 10.4), 8.2 * s, 1.5 * s) & cv.half(y=hf.t + 9.6 * s)
        cv.part("visor", visor, hel, edge="dark", noedge=("helmet",), lv=np.where(visor, 1, 0) + np.where(visor & (cv.X < hf.x), 1, 0))
        if s >= 0.8:
            # vents
            for dx in (-4, 0, 4):
                x0, y0 = hf.P(dx, 2.6)
                x1, y1 = hf.P(dx * 1.25, 6.2)
                cv.line(x0, y0, x1, y1, hel[0], only_own=ids(cv, "helmet"))
            cv.puts([hf.P(-5, 3.6), hf.P(-6, 4.6)], hel[4])
            if s > 1.5:
                for dx in (-2, 2, 6, -6):
                    x0, y0 = hf.P(dx, 2.2); x1, y1 = hf.P(dx * 1.25, 6.4)
                    cv.line(x0 + 1, y0, x1 + 1, y1, hel[0], only_own=ids(cv, "helmet"))
        else:
            cv.put(*hf.P(0, 2.5), hel[1]); cv.put(*hf.P(-3.2, 3.2), hel[4])

    def hair_front(self, cv, hf, pose, extra):
        s = hf.s
        # side hair over the ears + swept bangs under the helmet rim
        m = cv.empty()
        for sd in (-1, 1):
            m |= cv.capsule(*hf.P(sd * 7.0, 9.5), *hf.P(sd * 7.5, 14.0), 1.7 * s, 1.2 * s)
        m |= cv.poly([hf.P(-7.6, 9.4), hf.P(6.8, 9.4), hf.P(4.5, 11.6), hf.P(0.5, 12.2), hf.P(-2.5, 11.4), hf.P(-6.2, 13.4)])
        cv.part("hair", m, self.hair, noedge=("face",), rad=3 * s, soft=0.8, cuts=(0.3, 0.56, 0.88))
        if s >= 0.8 and s < 1.5:
            cv.line(*hf.P(-1, 11), *hf.P(-5, 13), self.hair[3], only_own=ids(cv, "hair"))
        self.helmet_front(cv, hf, pose)
        # chin strap: only the buckle ends show under the helmet (a full strap reads as a beard or tears)
        if False:
            for sd in (-1, 1):
                a = hf.P(sd * 7.4, 11.2)
                b = hf.P(sd * 5.6, 19.2 if s < 1.5 else 18.6)
                cv.line(*a, *b, (40, 46, 58), only_own=ids(cv, "face", "ears", "hair"))

    def hair_side_back(self, cv, hf):
        s = hf.s
        tail = cv.capsule(*hf.P(-6, 11), *hf.P(-10.5, 18), 2.6 * s, 2.0 * s) | cv.capsule(*hf.P(-10.5, 18), *hf.P(-10.0, 25), 2.0 * s, 1.2 * s)
        cv.part("tail", tail, self.hair, rad=3 * s, cuts=(0.3, 0.56, 0.88), tex=0.05 if s >= 0.8 else 0, seed=4)

    def hair_side(self, cv, hf):
        s = hf.s
        m = cv.ell(*hf.P(-0.5, 12.5), 7.6 * s, 5.0 * s) & (cv.X < hf.x + 4.2 * s) & (cv.Y > hf.t + 9 * s)
        m &= ~cv.ell(*hf.P(3.5, 15.5), 3.0 * s, 4.0 * s)
        cv.part("hair", m, self.hair, rad=3 * s, cuts=(0.3, 0.56, 0.88))
        dome = cv.ell(*hf.P(0, 9.6), 9.9 * s, 9.2 * s) & (cv.Y < hf.t + 10.8 * s - 0.08 * (cv.X - hf.x - 2 * s))
        cv.part("helmet", dome, self.helmet, edge="dark", rad=6 * s, soft=1.0, cuts=(0.28, 0.54, 0.86))
        visor = cv.ell(*hf.P(8.4, 9.8), 3.4 * s, 1.4 * s)
        cv.part("visor", visor, self.helmet, edge="dark", noedge=("helmet",), lv=np.where(visor, 2, 0))
        if s >= 0.8:
            for dx in (-5, -1, 3):
                cv.line(*hf.P(dx, 2.0 + abs(dx) * 0.2), *hf.P(dx - 1.5, 5.6), self.helmet[0], only_own=ids(cv, "helmet"))
            cv.line(*hf.P(3.5, 11.0), *hf.P(4.5, 19.4), (40, 46, 58), only_own=ids(cv, "face", "hair"))

    def hair_back_view(self, cv, hf):
        s = hf.s
        for sd in (-1, 1):
            e = cv.ell(*hf.P(sd * 7.8, 14.5), max(1.0, 1.4 * s), max(1.3, 2.1 * s))
            cv.part("ear%d" % sd, e, self.skin, edge="dark", rad=2, bias=-0.1)
        m = cv.ell(*hf.P(0, 12.0), 8.4 * s, 6.6 * s) & (cv.Y > hf.t + 7 * s)
        tail = cv.capsule(*hf.P(0, 14), *hf.P(0.5, 22), 2.6 * s, 2.0 * s) | cv.capsule(*hf.P(0.5, 22), *hf.P(-0.5, 27), 2.0 * s, 1.1 * s)
        cv.part("hair", m | tail, self.hair, rad=4 * s, soft=1.0, cuts=(0.24, 0.5, 0.84), tex=0.05 if s >= 0.8 else 0, seed=6)
        if s >= 0.8:
            for (a, b) in (((-3, 12), (-1, 17)), ((3, 12), (1, 17)), ((0, 18), (0.5, 25))):
                cv.line(*hf.P(*a), *hf.P(*b), self.hair[3], only_own=ids(cv, "hair"))
        dome = cv.ell(*hf.P(0, 9.6), 9.9 * s, 9.2 * s) & (cv.Y < hf.t + 11.2 * s - 0.02 * (cv.X - hf.x) ** 2 / max(s, 0.5))
        cv.part("helmet", dome, self.helmet, edge="dark", rad=6 * s, soft=1.0, cuts=(0.28, 0.54, 0.86))
        if s >= 0.8:
            for dx in (-4, 0, 4):
                cv.line(*hf.P(dx, 2.6), *hf.P(dx * 1.25, 8.0), self.helmet[0], only_own=ids(cv, "helmet"))
            # a little red rear light on the helmet
            cv.puts([hf.P(-0.5, 9.4), hf.P(0.5, 9.4)], (230, 50, 50)); cv.put(*hf.P(-0.5, 9.4), (255, 140, 120))
        else:
            cv.put(*hf.P(0, 6.8), (230, 50, 50))

    def after_front(self, cv, R, hf, pose, extra):
        self.wheel_after(cv, R, spin=(pose == "tell"))
        if pose == "tell":
            sparkle(cv, int(R.X(-6)), int(R.Y(-3)), big=R.battle)
        if pose == "hit":
            sweat(cv, int(hf.x + 9 * hf.s), int(hf.t + 3 * hf.s), R.battle)

    # side: walking right, wheel in her near hand
    side_stride = ((-2.0, -1.4), (1.5, 1.4))

    def side_behind(self, cv, R):
        Q = R.Q
        self.arm_far = [Q(-1, 25.5), Q(-3.5, 35), Q(-4.5, 43)]
        self.an_arm(cv, R, "armF", self.arm_far)
        fist(cv, *Q(-4.6, 44), "handF", R, self.skin)

    def torso_side(self, cv, R):
        Q = R.Q
        tor = cv.poly([Q(-5, 22.5), Q(3, 22.5), Q(7, 26), Q(8, 31), Q(6.5, 37), Q(7, 47), Q(-7.5, 47), Q(-7.5, 36), Q(-7, 28)])
        cv.part("torso", tor, self.jacket, rad=7 * R.k + 1, soft=1.3, cuts=(0.28, 0.52, 0.84))
        st = (cv.Y >= R.Y(31.2)) & (cv.Y <= R.Y(31.2) + (1.0 if R.battle else 0.3))
        recolor(cv, "torso", st, self.jacket, RAMP["metal"])
        col = cv.ell(*Q(0.5, 22.6), 4.2 * R.sx, 2.0 * R.k)
        cv.part("collar", col, self.jacket, noedge=("torso",), lv=np.where(col, 3, 0))

    def arm_side(self, cv, R):
        Q = R.Q
        hand = Q(4.5, 45)
        self.wheel_at(cv, R, hand[0] + 1.5 * R.k, hand[1] + 12.8 * R.k, asp=1.0)
        self.an_arm(cv, R, "arm", [Q(-0.5, 25.5), Q(1.5, 35.5), hand])
        fist(cv, *hand, "hand", R, self.skin)

    def after_side(self, cv, R, hf):
        self.wheel_after(cv, R)

    def back_behind(self, cv, R):
        Q = R.Q
        hand = Q(17, 45)
        self.wheel_at(cv, R, hand[0] + 1.0 * R.k, hand[1] + 12.8 * R.k)
        self.st["whand"] = hand

    def torso_back(self, cv, R):
        self.torso_front(cv, R, "idle", None, back=True)
        # hood-ish collar seen from behind
        Q = R.Q
        col = cv.ell(*Q(0, 22.8), 5.8 * R.sx, 2.2 * R.k)
        cv.part("collar", col, self.jacket, noedge=("torso",), lv=np.where(col, 2, 0))

    def arms_back(self, cv, R):
        Q = R.Q
        hand = self.st["whand"]
        self.an_arm(cv, R, "armR", [Q(10.5, 25.5), Q(15, 35.5), hand])
        fist(cv, *hand, "handR", R, self.skin)
        self.an_arm(cv, R, "armL", [Q(-10.5, 25.5), Q(-12.5, 35), Q(-12.5, 43)])
        fist(cv, *Q(-12.5, 44.5), "handL", R, self.skin)

    def after_back(self, cv, R, hf):
        self.wheel_after(cv, R)

    # portrait
    def p_behind(self, cv, hf, expr):
        tail = cv.capsule(*hf.P(-4, 14), *hf.P(-12.5, 25), 3.2 * hf.s * 0.7, 2.2 * hf.s * 0.7) | \
            cv.capsule(*hf.P(-12.5, 25), *hf.P(-14, 33), 2.2 * hf.s * 0.7, 1.4 * hf.s * 0.7)
        cv.part("tail", tail, self.hair, rad=4, cuts=(0.3, 0.56, 0.88), tex=0.05, seed=4)

    def p_shoulders(self, cv, c, expr):
        sh = cv.ell(c, 75, 31, 25) & cv.half(y=48)
        cv.part("shoulders", sh, self.jacket, rad=14, soft=2.0, cuts=(0.34, 0.60, 0.90))
        st = (cv.Y >= 58) & (cv.Y <= 59)
        recolor(cv, "shoulders", st, self.jacket, RAMP["metal"])
        cv.line(c, 52, c, 63, self.jacket[1], only_own=ids(cv, "shoulders"))

    def p_collar(self, cv, c, expr):
        col = cv.poly([(c - 9, 47), (c - 6, 52), (c, 54), (c + 6, 52), (c + 9, 47), (c + 9, 53), (c, 57), (c - 9, 53)])
        cv.part("collar", col, self.jacket, noedge=("shoulders",), lv=np.where(col, 3, 0) - np.where(col & (cv.X > c + 1), 1, 0))
        cv.vline(c, 54, 63, RAMP["metal"][2]); cv.put(c, 55, RAMP["metal"][4])

    def p_hair(self, cv, hf, expr):
        self.hair_front(cv, hf, "idle", None)

    def p_after(self, cv, c, expr):
        Char.p_after(self, cv, c, expr)
        if expr == "warm":
            sparkle(cv, 6, 8, big=True)


# ==========================================================================
# RUNNER -- lanky distance runner: coral singlet with a race bib, split shorts,
#           lime shoes, sport sunglasses pushed up, a handheld water bottle
# ==========================================================================
class Runner(Char):
    id = "runner"
    title = "Runner (singlet, race bib, handheld bottle)"
    H, WH = 78, 52
    build = 0.9
    hipw = 0.85
    skin = [(36, 18, 12), (78, 42, 28), (110, 64, 42), (140, 88, 58), (172, 120, 84)]
    hair = [(10, 8, 8), (26, 20, 20), (42, 32, 30), (62, 48, 44), (88, 70, 62)]
    singlet = [(112, 26, 36), (202, 58, 66), (240, 98, 94), (252, 146, 132), (255, 198, 182)]
    shorts = [(14, 18, 40), (30, 38, 72), (46, 58, 100), (70, 84, 130), (104, 118, 164)]
    lime = [(36, 74, 10), (96, 164, 20), (146, 210, 40), (196, 238, 96), (232, 255, 176)]
    lens = [(20, 24, 60), (50, 60, 150), (70, 130, 210), (120, 210, 230), (230, 250, 255)]
    bottle_r = [(30, 70, 110), (70, 140, 190), (120, 190, 230), (180, 226, 248), (230, 248, 255)]
    iris = (66, 38, 24)
    iris_d = (30, 16, 10)
    brow = (16, 10, 10)
    brow2 = (30, 22, 20)
    lip = (88, 46, 40)
    blush = (150, 70, 60)

    def shoe(self, cv, R, name, fx, lift, s, side=False, far=False):
        sneaker(cv, R, name, fx, self.lime, RAMP["white"], lift, side=side)

    def leg(self, cv, R, name, pts, s, far=False):
        m = cv.chain(pts, R.r(2.6, 1.5))
        m |= cv.capsule(*pts[0], *pts[1], R.r(3.3, 1.9), R.r(2.6, 1.5))
        cv.part(name, m, self.skin, rad=3 * R.k, soft=0.8, cuts=(0.28, 0.52, 0.86) if not far else (0.42, 0.66, 0.92), bias=0.04)
        # white ankle sock
        ax, ay = pts[-1]
        sock = cv.capsule(ax, ay - R.r(1.6, 0.6), ax, ay + 0.5, R.r(2.5, 1.5)) & cv.half(y=ay - R.r(1.6, 0.6))
        cv.part(name + "sock", sock, RAMP["white"], edge="dark", lv=np.where(sock, 3, 0))

    def hips(self, cv, R, legs):
        Q = R.Q
        m = cv.poly([Q(-9.4, 45.5), Q(9.4, 45.5), Q(10.4, 55), Q(1.2, 55.5), Q(0, 51.5), Q(-1.2, 55.5), Q(-10.4, 55)])
        for s in (-1, 1):
            hip, knee, ank, lift = legs[s]
            if lift:
                # raised thigh: the shorts follow it
                m |= cv.capsule(*hip, hip[0] + (knee[0] - hip[0]) * 0.45, hip[1] + (knee[1] - hip[1]) * 0.45, R.r(3.8, 2.2))
        cv.part("shorts", m, self.shorts, rad=4 * R.k, soft=0.8, cuts=(0.30, 0.56, 0.88))
        if R.battle:
            # split-hem notch + a reflective dot
            for s in (-1, 1):
                x = R.X(s * 9.4)
                cv.line(x, R.Y(55), x - s * 0.5, R.Y(52.5), self.shorts[0], only_own=ids(cv, "shorts"))
            cv.put(R.X(-7.5), R.Y(48), RAMP["metal"][3])

    def torso_front(self, cv, R, pose, extra, back=False):
        Q = R.Q
        sk = cv.poly([Q(-6, 22.5), Q(6, 22.5), Q(9.8, 23.8), Q(11, 28), Q(9.6, 33), Q(-9.6, 33), Q(-11, 28), Q(-9.8, 23.8)])
        cv.part("chest", sk, self.skin, rad=6 * R.k, soft=1.2, cuts=(0.26, 0.5, 0.86))
        if back:
            sing = cv.poly([Q(-8, 23), Q(-4.5, 22.6), Q(0, 24.5), Q(4.5, 22.6), Q(8, 23), Q(9.0, 31), Q(9.0, 38), Q(9.8, 47),
                            Q(-9.8, 47), Q(-9.0, 38), Q(-9.0, 31)])
        else:
            sing = cv.poly([Q(-8, 23), Q(-4.5, 22.6), Q(0, 27.5), Q(4.5, 22.6), Q(8, 23), Q(9.0, 31), Q(9.0, 38), Q(9.8, 47),
                            Q(-9.8, 47), Q(-9.0, 38), Q(-9.0, 31)])
        cv.part("torso", sing, self.singlet, noedge=("chest",), rad=8 * R.k + 1, soft=1.4, cuts=(0.32, 0.58, 0.90))
        cv.part("tline", cv.poly([Q(-8, 23), Q(-4.5, 22.6), Q(-5, 24), Q(-8.5, 25)]) | cv.poly([Q(8, 23), Q(4.5, 22.6), Q(5, 24), Q(8.5, 25)]),
                self.singlet, edge=None, lv=None, rad=2, cuts=(0.3, 0.55, 0.88)) if False else None
        if not back:
            # race bib: white with a "303" and four pins
            x0, y0 = R.X(-5.2), R.Y(33.5)
            x1, y1 = R.X(5.2), R.Y(41.5)
            bib = cv.rect(x0, y0, x1, y1)
            cv.part("bib", bib, RAMP["white"], edge="dark", lv=np.where(bib, 3, 0) - np.where(bib & (cv.X > x1 - 2), 1, 0))
            ix0, iy0 = int(math.ceil(x0)), int(math.ceil(y0))
            if R.battle:
                D = {"3": ["##.", "..#", ".#.", "..#", "##."], "0": [".#.", "#.#", "#.#", "#.#", ".#."]}
                x = ix0 + 2
                for ch in "303":
                    for j, row in enumerate(D[ch]):
                        for i, p in enumerate(row):
                            if p == "#":
                                cv.put(x + i, iy0 + 2 + j, (30, 30, 44))
                    x += 3
                cv.hline(ix0 + 1, int(x1) - 1, iy0 + 1, (220, 60, 60))
            else:
                cv.hline(ix0 + 1, int(x1) - 1, iy0 + 1, (40, 40, 56))
                cv.put(ix0 + 1, iy0, (220, 60, 60))

    def bottle_at(self, cv, R, x, y, ang=0.0, name="bottle"):
        """Handheld bottle centred on the hand (x, y); ang tilts it (0 = upright)."""
        L = 5.5 * R.k
        ux, uy = math.sin(ang), -math.cos(ang)
        b = cv.capsule(x - ux * L, y - uy * L, x + ux * L * 0.9, y + uy * L * 0.9, R.r(2.3, 1.4))
        cv.part(name, b, self.bottle_r, edge="ink", rad=2, soft=0.6, cuts=(0.25, 0.5, 0.8))
        cap = cv.ell(x + ux * (L + 1.6 * R.k), y + uy * (L + 1.6 * R.k), R.r(1.5, 0.9), R.r(1.5, 0.9))
        cv.part(name + "cap", cap, self.lime, edge="ink", lv=np.where(cap, 3, 0))
        if R.battle:
            # water level line
            cv.put(x - ux * 2 - 1, y - uy * 2 + 2, self.bottle_r[1])
        self.st["cap"] = (x + ux * (L + 1.6 * R.k), y + uy * (L + 1.6 * R.k), ux, uy)

    def watch(self, cv, R, x, y):
        m = cv.ell(x, y, R.r(1.8, 1.0), R.r(1.4, 0.8))
        cv.part("watch", m, [(10, 10, 14), (20, 20, 26), (34, 34, 42), (54, 54, 64), (80, 80, 96)], edge="ink", lv=np.where(m, 2, 0))
        cv.put(x, y, self.lime[3] if R.battle else self.lime[2])

    def arms_front(self, cv, R, pose, extra):
        Q = R.Q
        sk = self.skin
        if extra == "drink":
            pts = [Q(-9.5, 25.5), Q(-14, 31.5), Q(-5.5, 22)]
            arm(cv, R, "armR", pts, sk, sleeve="none")
            self.bottle_at(cv, R, *Q(-6.5, 20.5), ang=1.1)
            fist(cv, *Q(-6.5, 21.5), "handR", R, sk)
        elif pose == "tell":
            arm(cv, R, "armR", [Q(-9.5, 25.5), Q(-13.5, 34), Q(-16.5, 40)], sk, sleeve="none")
            self.bottle_at(cv, R, *Q(-16.8, 40.5), ang=-0.4)
            fist(cv, *Q(-16.8, 41), "handR", R, sk)
        elif pose == "hit":
            arm(cv, R, "armR", [Q(-9.5, 25.5), Q(-16, 22.5), Q(-18.5, 15)], sk, sleeve="none")
            self.bottle_at(cv, R, *Q(-18.8, 13.5), ang=-2.3)
            fist(cv, *Q(-18.8, 14), "handR", R, sk)
        else:
            arm(cv, R, "armR", [Q(-9.5, 25.5), Q(-12.5, 35.5), Q(-13, 44)], sk, sleeve="none")
            self.bottle_at(cv, R, *Q(-13.2, 45.5))
            fist(cv, *Q(-13.2, 45.5), "handR", R, sk)
        # left arm: watch arm
        if pose == "talk":
            pts = [Q(9.5, 25.5), Q(15.5, 35), Q(16.5, 26.5)]
            arm(cv, R, "armL", pts, sk, sleeve="none")
            self.watch(cv, R, *Q(16.4, 28.4))
            fist(cv, *Q(16.6, 25.2), "handL", R, sk)
        elif extra == "watch":
            pts = [Q(9.5, 25.5), Q(14, 35), Q(6.5, 32)]
            arm(cv, R, "armL", pts, sk, sleeve="none")
            self.watch(cv, R, *Q(8.6, 32.6))
            fist(cv, *Q(5.6, 31.6), "handL", R, sk)
        elif pose == "tell":
            arm(cv, R, "armL", [Q(9.5, 25.5), Q(13.5, 33), Q(9.5, 28.5)], sk, sleeve="none")
            self.watch(cv, R, *Q(11, 30.2))
            fist(cv, *Q(8.8, 27.8), "handL", R, sk)
        elif pose == "hit":
            arm(cv, R, "armL", [Q(9.5, 25.5), Q(16, 30), Q(20, 26)], sk, sleeve="none")
            self.watch(cv, R, *Q(18.6, 27))
            open_hand(cv, *Q(20.6, 24), "handL", R, sk, flip=-1)
        else:
            arm(cv, R, "armL", [Q(9.5, 25.5), Q(15.5, 34.5), Q(10.5, 43)], sk, sleeve="none")
            self.watch(cv, R, *Q(11.8, 41))
            fist(cv, *Q(10.2, 43.5), "handL", R, sk)

    def legs_front(self, cv, R, pose, extra):
        if pose == "tell":
            self.standing_legs(cv, R, raise_leg=(1, (7.5, 56), (6.5, 66.5), 9.5))
        else:
            self.standing_legs(cv, R)

    def hair_front(self, cv, hf, pose, extra):
        s = hf.s
        yl = hf.t + 8.6 * s + 0.035 * (cv.X - hf.x) ** 2 / max(s, 0.5)
        crown = cv.ell(*hf.P(0, 9.4), (8.7 if s < 1.5 else 7.9) * s, 9.0 * s) & (cv.Y < yl)
        crown |= cv.ell(*hf.P(0, 5.4), (7.8 if s < 1.5 else 7.2) * s, 5.6 * s)
        cv.part("hair", crown, self.hair, noedge=("face",), rad=4 * s, soft=1.0, cuts=(0.30, 0.56, 0.88),
                tex=0.18 if s >= 0.8 else 0.0, seed=21)
        self.shades(cv, hf, "front")

    def shades(self, cv, hf, view):
        s = hf.s
        fr = (24, 24, 32)
        if view == "front":
            # one wraparound shield lens pushed up on the hair
            m = cv.ell(*hf.P(0, 6.6), 7.4 * s, 1.5 * s + 0.35) | cv.ell(*hf.P(0, 5.9), 7.0 * s, 1.2 * s + 0.2)
            lv = np.where(m, 1, 0) + np.where(m & (cv.X < hf.x + 2 * s), 1, 0) + np.where(m & (cv.X < hf.x - 2.5 * s), 1, 0) + \
                np.where(m & (cv.X < hf.x - 4.5 * s) & (cv.Y < hf.t + 6.4 * s), 1, 0)
            cv.part("shades", m, self.lens, edge="ink", lv=lv)
            for sd in (-1, 1):
                cv.line(*hf.P(sd * 6.6, 5.8), *hf.P(sd * 8.2, 7.0), fr, only_own=ids(cv, "hair"))
        elif view == "side":
            m = cv.ell(*hf.P(4.5, 5.2), 3.4 * s, 1.4 * s + 0.2)
            cv.part("shades", m, self.lens, edge="ink", lv=np.where(m, 3, 0))
            cv.line(*hf.P(1.5, 5.4), *hf.P(-5, 7.8), fr)

    def hair_side(self, cv, hf):
        s = hf.s
        yl = hf.t + (8.4 + 0.1 * (hf.x - cv.X) / s) * s
        m = cv.ell(*hf.P(0, 9.2), 8.6 * s, 9.0 * s) & ((cv.X < hf.x + 0.5 * s) | (cv.Y < yl))
        m &= (cv.Y < hf.t + 16 * s) | (cv.X < hf.x - 4 * s)
        m &= ~(cv.ell(*hf.P(-0.5, 14.5), 2.2 * s, 2.6 * s))
        cv.part("hair", m, self.hair, rad=4 * s, cuts=(0.30, 0.56, 0.88), tex=0.18 if s >= 0.8 else 0, seed=22)
        ear = cv.ell(*hf.P(-0.5, 14.5), max(1.0, 1.6 * s), max(1.3, 2.2 * s))
        cv.part("ear", ear, self.skin, edge="dark", rad=2, bias=-0.1)
        self.shades(cv, hf, "side")

    def hair_back_view(self, cv, hf):
        s = hf.s
        m = cv.ell(*hf.P(0, 9.6), 8.8 * s, 9.6 * s) & (cv.Y < hf.t + 18.5 * s)
        cv.part("hair", m, self.hair, rad=4 * s, soft=1.0, cuts=(0.30, 0.56, 0.88), tex=0.18 if s >= 0.8 else 0, seed=23)
        for sd in (-1, 1):
            e = cv.ell(*hf.P(sd * 8.0, 14.5), max(1.0, 1.4 * s), max(1.3, 2.2 * s))
            cv.part("ear%d" % sd, e, self.skin, edge="dark", rad=2, bias=-0.1)
        # sunglasses strap round the back of the head
        cv.line(*hf.P(-8.4, 7.4), *hf.P(8.4, 7.4), (24, 24, 32), only_own=ids(cv, "hair"))
        # fade at the nape
        nape = (cv.Y >= hf.t + 16.5 * s) & own_mask(cv, "hair")
        recolor(cv, "hair", nape, self.hair, [mix(c, self.skin[1], 0.45) for c in self.hair])

    def after_front(self, cv, R, hf, pose, extra):
        if pose == "tell":
            # motion ticks by the raised knee and a pumping arm
            kx, ky = R.Q(12, 56)
            for j in range(3):
                empty_put(cv, kx + j, ky - 2 + j * 2, SPARK)
            sweat(cv, int(hf.x - 10 * hf.s), int(hf.t + 6 * hf.s), R.battle)
        if pose == "hit":
            # water sloshing out of the flipped bottle
            cx, cy, ux, uy = self.st["cap"]
            for j, (dx, dy) in enumerate(((1, -1), (2, -3), (4, -4), (6, -4), (7, -2), (3, -6), (8, 0))):
                if R.battle or j < 3:
                    empty_put(cv, cx + dx * R.k, cy + dy * R.k, SWEAT_HI if j % 2 else SWEAT)
            sweat(cv, int(hf.x + 9 * hf.s), int(hf.t + 3 * hf.s), R.battle)
        if extra == "watch" and not R.battle:
            pass

    # side: mid-stride jog
    side_stride = ((-3.0, -2.6), (2.0, 2.6))

    def side_behind(self, cv, R):
        Q = R.Q
        arm(cv, R, "armF", [Q(-1, 25.5), Q(-5, 33), Q(-1.5, 38)], self.skin, sleeve="none")
        fist(cv, *Q(-1, 38.5), "handF", R, self.skin)

    def torso_side(self, cv, R):
        Q = R.Q
        tor = cv.poly([Q(-5, 22.5), Q(3, 22.5), Q(7, 26), Q(7.5, 31), Q(6, 37), Q(6.5, 47), Q(-7, 47), Q(-7, 36), Q(-6.5, 28)])
        cv.part("chest", tor, self.skin, rad=6 * R.k, cuts=(0.26, 0.5, 0.86))
        sing = cv.poly([Q(-6, 24), Q(-3, 22.8), Q(3.5, 24.5), Q(6.5, 27), Q(7.5, 31), Q(6, 37), Q(6.5, 47), Q(-7, 47), Q(-7, 36), Q(-5.5, 30)])
        sing &= ~cv.ell(*Q(0.5, 27.5), 3.6 * R.sx, 3.6 * R.sy)
        cv.part("torso", sing, self.singlet, noedge=("chest",), rad=7 * R.k + 1, soft=1.3, cuts=(0.28, 0.52, 0.84))
        m = cv.poly([Q(-7.5, 45.5), Q(6.8, 45.5), Q(8.2, 55), Q(-8.0, 55)])
        cv.part("shorts", m, self.shorts, rad=4 * R.k, cuts=(0.30, 0.56, 0.88))

    def arm_side(self, cv, R):
        Q = R.Q
        arm(cv, R, "arm", [Q(-0.5, 25.5), Q(-3.5, 35), Q(4, 38)], self.skin, sleeve="none")
        self.bottle_at(cv, R, *Q(4.8, 38.5), ang=0.2)
        fist(cv, *Q(4.8, 38.5), "hand", R, self.skin)
        self.watch(cv, R, *Q(1.8, 38))

    def after_side(self, cv, R, hf):
        for j in range(3):
            empty_put(cv, R.X(-12) - j * 2 * R.k, R.Y(56 + j * 6), SPARK)

    def torso_back(self, cv, R):
        self.torso_front(cv, R, "idle", None, back=True)
        legs = {s: (R.Q(s * 4.6 * self.hipw, 47), None, None, 0) for s in (-1, 1)}
        self.hips(cv, R, legs)

    def arms_back(self, cv, R):
        Q = R.Q
        sk = self.skin
        arm(cv, R, "armR", [Q(9.5, 25.5), Q(12.5, 35.5), Q(13, 44)], sk, sleeve="none")
        self.bottle_at(cv, R, *Q(13.2, 45.5))
        fist(cv, *Q(13.2, 45.5), "handR", R, sk)
        arm(cv, R, "armL", [Q(-9.5, 25.5), Q(-12, 35), Q(-12, 43)], sk, sleeve="none")
        self.watch(cv, R, *Q(-12, 41.5))
        fist(cv, *Q(-12, 44), "handL", R, sk)

    # portrait
    def p_shoulders(self, cv, c, expr):
        sh = cv.ell(c, 75, 31, 25) & cv.half(y=48)
        cv.part("bare", sh, self.skin, rad=14, soft=2.0, cuts=(0.30, 0.56, 0.90))
        sing = cv.poly([(c - 15, 49), (c - 10, 48), (c, 60), (c + 10, 48), (c + 15, 49), (c + 19, 64), (c - 19, 64)])
        sing &= sh
        cv.part("shoulders", sing, self.singlet, noedge=("bare",), rad=10, soft=1.6, cuts=(0.32, 0.58, 0.90))

    def p_hair(self, cv, hf, expr):
        self.hair_front(cv, hf, "idle", None)

    def p_face_marks(self, cv, c, expr):
        Char.p_face_marks(self, cv, c, expr)
        # cheek shine (key light) + a tiny chin beard
        cv.puts([(c - 9, 30), (c - 8, 30)], self.skin[4])
        cv.hline(c - 2, c + 2, 47, self.hair[1]); cv.hline(c - 1, c + 1, 48, self.hair[1])

    def p_after(self, cv, c, expr):
        Char.p_after(self, cv, c, expr)
        if expr == "warm":
            cv.puts([(56, 8), (57, 7), (58, 8), (57, 9)], SPARK2); cv.put(57, 8, WHITE)


# ==========================================================================
# HIPPIE -- hacky-sack girl: ginger messy bun, freckles, striped baja hoodie,
#           baggy olive patch pants, wool socks + clogs, a crocheted footbag
# ==========================================================================
class Hippie(Char):
    id = "hippie"
    title = "Hippie (hacky sack, baja hoodie)"
    H, WH = 73, 50
    build = 1.05
    hipw = 1.12
    face_w = 1.02
    top = 4.2
    lashes = True
    skin = [(124, 64, 50), (216, 152, 126), (244, 196, 170), (252, 220, 198), (255, 238, 222)]
    hair = [(92, 30, 12), (158, 62, 24), (204, 98, 42), (232, 138, 68), (248, 180, 112)]
    cream = [(110, 96, 76), (196, 182, 156), (226, 214, 190), (242, 234, 214), (252, 248, 236)]
    teal = [(14, 60, 70), (30, 110, 120), (46, 146, 150), (90, 186, 184), (150, 220, 214)]
    rust = [(90, 30, 16), (160, 62, 30), (196, 94, 48), (222, 130, 80), (240, 172, 124)]
    navy = [(20, 24, 50), (40, 48, 90), (62, 72, 124), (92, 104, 156), (130, 142, 190)]
    olive = [(38, 44, 20), (72, 82, 40), (100, 112, 58), (130, 142, 82), (166, 176, 116)]
    clog = [(52, 28, 14), (102, 58, 28), (140, 86, 44), (176, 118, 66), (208, 156, 100)]
    iris = (80, 150, 90)
    iris_d = (36, 86, 50)
    brow = (150, 60, 26)
    brow2 = (190, 90, 40)
    lip = (214, 120, 110)
    blush = (238, 130, 110)
    SACK = [(214, 60, 50), (240, 200, 60), (80, 170, 80)]

    def shoe(self, cv, R, name, fx, lift, s, side=False, far=False):
        sneaker(cv, R, name, fx, self.clog, [(40, 24, 12), (70, 44, 24), (96, 64, 36), (120, 86, 52), (150, 112, 74)], lift, side=side)

    def leg(self, cv, R, name, pts, s, far=False):
        ax, ay = pts[-1]
        sock = cv.capsule(ax, ay - R.r(2.0, 0.8), ax, ay + 0.6, R.r(2.6, 1.5)) & cv.half(y=ay - R.r(2.0, 0.8))
        cv.part(name + "sock", sock, self.rust, edge="dark", lv=np.where(sock, 3, 0) - np.where(sock & (cv.X > ax), 1, 0))
        top = (pts[-1][0], pts[-1][1] - R.r(2.0, 0.8))
        p2 = [pts[0], pts[1], top]
        m = cv.capsule(*p2[0], *p2[1], R.r(4.4, 2.6), R.r(3.9, 2.3)) | cv.capsule(*p2[1], *p2[2], R.r(3.9, 2.3), R.r(3.6, 2.1))
        cv.part(name, m, self.olive, rad=3.6 * R.k + 0.4, soft=0.8, cuts=(0.30, 0.55, 0.88) if not far else (0.45, 0.70, 0.95),
                tex=0.05, seed=31 + s)
        if R.battle:
            # fold lines + a rust patch on the viewer-left knee
            kx, ky = p2[1]
            cv.line(kx - 2, ky + 3, kx + 1, ky + 5, self.olive[1], only_own=[cv.names[name]])
            if s == -1:
                pm = cv.rect(kx - 2, ky - 2, kx + 1, ky + 1)
                cv.part(name + "patch", pm, self.rust, edge="dark", lv=np.where(pm, 3, 0))
                cv.put(kx - 1, ky - 1, self.rust[4])
            # gathered hem
            cv.line(top[0] - R.r(3.4, 2), top[1], top[0] + R.r(3.4, 2), top[1], self.olive[1], only_own=[cv.names[name]])

    def baja(self, cv, name, R, dense=False, vertical=True):
        """Vertical baja stripes (teal / rust / navy on cream), recoloured tone for tone."""
        if name not in cv.names:
            return
        m = own_mask(cv, name)
        step = 3 if (R is None or R.battle) else 3
        xs = (cv.X.astype(int))
        cols = [self.teal, self.rust, self.navy]
        if R is not None and not R.battle:
            sel = (xs % 3 == 0)
            recolor(cv, name, m & sel, self.cream, self.teal)
            return
        for i, rmp in enumerate(cols):
            sel = (xs % 6 == (i * 2) % 6) & ((xs // 6) % 1 == 0)
            if i == 2:
                sel = (xs % 12 == 4)
            elif i == 0:
                sel = (xs % 6 == 0)
            else:
                sel = (xs % 12 == 2) | (xs % 12 == 9) if False else (xs % 12 == 10)
            recolor(cv, name, m & sel, self.cream, rmp)

    def torso_front(self, cv, R, pose, extra, back=False):
        m = self.torso_mask(cv, R, sw=0.98)
        m |= cv.poly([R.Q(-11.5, 40), R.Q(11.5, 40), R.Q(12.8, 47.5), R.Q(-12.8, 47.5)])
        cv.part("torso", m, self.cream, rad=8 * R.k + 1, soft=1.4, cuts=(0.34, 0.60, 0.90), tex=0.04, seed=41)
        self.baja(cv, "torso", R)
        hem = (cv.Y >= R.Y(45.8)) & own_mask(cv, "torso")
        recolor(cv, "torso", hem, self.cream, self.rust)
        recolor(cv, "torso", hem, self.teal, self.rust)
        recolor(cv, "torso", hem, self.navy, self.rust)
        if back:
            return
        Q = R.Q
        # kangaroo pocket
        pk = cv.poly([Q(-6.5, 37.5), Q(6.5, 37.5), Q(8.5, 44.5), Q(-8.5, 44.5)])
        cv.part("pocket", pk, self.cream, edge="dark", noedge=(), lv=np.where(pk, 2, 0) + np.where(pk & (cv.Y < R.Y(38.6)), 1, 0))
        self.baja(cv, "pocket", R)
        # drawstrings
        if R.battle:
            for sd in (-1, 1):
                cv.line(R.X(sd * 2), R.Y(23.5), R.X(sd * 2.4), R.Y(30.5), self.rust[1])
                cv.put(R.X(sd * 2.4), R.Y(31.3), self.rust[3])
        else:
            cv.put(R.X(-1.5), R.Y(26), self.rust[1]); cv.put(R.X(1.5), R.Y(26), self.rust[1])

    def behind_front(self, cv, R, pose, extra):
        Q = R.Q
        hood = cv.ell(*Q(0, 22.6), 9.4 * R.sx, 3.4 * R.k)
        cv.part("hood", hood, self.cream, rad=3, cuts=(0.4, 0.66, 0.92))
        self.baja(cv, "hood", R)

    def sack(self, cv, R, x, y, name="sack"):
        r = R.r(2.9, 1.6)
        m = cv.ell(x, y, r, r)
        cv.part(name, m, [INK, self.SACK[0], self.SACK[0], self.SACK[0], self.SACK[0]], edge="ink", lv=np.where(m, 2, 0))
        pid = cv.names[name]
        ink = np.all(cv.col == np.array(INK), axis=2)
        inner = (cv.own == pid) & ~ink
        a = np.arctan2(cv.Y - y, cv.X - x)
        seg = ((a + math.pi) / (2 * math.pi) * 3).astype(int) % 3
        for i in range(3):
            cv.col[inner & (seg == i)] = self.SACK[i]
        if R.battle:
            cv.put(x - 1, y - 1, WHITE)
        self.st["sack"] = (x, y)

    def legs_front(self, cv, R, pose, extra):
        if pose == "tell":
            self.standing_legs(cv, R, raise_leg=(1, (11.5, 55.5), (9.5, 64.5), 12.5))
        else:
            self.standing_legs(cv, R)

    def arms_front(self, cv, R, pose, extra):
        Q = R.Q
        sk, cr = self.skin, self.cream

        def a(name, pts):
            arm(cv, R, name, pts, sk, cr, "long", tex=0.04, seed=43)
            self.baja(cv, name, R)
            # rust cuff
            x, y = pts[-1]
            px, py = pts[-2]
            L = math.hypot(x - px, y - py) or 1
            cuff = cv.ell(x - (x - px) / L * 1.2 * R.k, y - (y - py) / L * 1.2 * R.k, R.r(2.9, 1.9), R.r(2.9, 1.9)) & own_mask(cv, name)
            recolor(cv, name, cuff, cr, self.rust); recolor(cv, name, cuff, self.teal, self.rust); recolor(cv, name, cuff, self.navy, self.rust)

        pocket_hands = []
        # viewer-left arm (her right) holds the sack
        if extra == "toss":
            a("armR", [Q(-11, 25.5), Q(-16, 34), Q(-14.5, 38.5)])
            open_hand(cv, *Q(-14.5, 39.5), "handR", R, sk)
            self.sack(cv, R, *Q(-14.5, 28))
        elif extra == "lookup":
            a("armR", [Q(-11, 25.5), Q(-12.5, 35), Q(-6, 41)])
            pocket_hands.append("armR")
        elif pose == "tell":
            a("armR", [Q(-11, 25.5), Q(-17.5, 31), Q(-22, 29.5)])
            open_hand(cv, *Q(-23.5, 28.5), "handR", R, sk)
        elif pose == "hit":
            a("armR", [Q(-11, 25.5), Q(-17, 24), Q(-20, 16)])
            open_hand(cv, *Q(-20.5, 13.5), "handR", R, sk)
        else:
            a("armR", [Q(-11, 25.5), Q(-15, 35), Q(-14.5, 42.5)])
            open_hand(cv, *Q(-14.8, 43.2), "handR", R, sk)
            self.sack(cv, R, *Q(-14.8, 40.2))
        # viewer-right arm (her left)
        if pose == "talk":
            a("armL", [Q(11, 25.5), Q(17.5, 31), Q(19, 22.5)])
            open_hand(cv, *Q(19.2, 20), "handL", R, sk, flip=-1)
        elif pose == "tell":
            a("armL", [Q(11, 25.5), Q(17.5, 30), Q(22, 26.5)])
            open_hand(cv, *Q(23.5, 25.5), "handL", R, sk, flip=-1)
        elif pose == "hit":
            a("armL", [Q(11, 25.5), Q(17, 24.5), Q(19.5, 17)])
            open_hand(cv, *Q(20, 14.5), "handL", R, sk, flip=-1)
        else:
            a("armL", [Q(11, 25.5), Q(12.5, 35), Q(6, 41)])
            pocket_hands.append("armL")
        if pocket_hands:
            # the pocket goes back over the wrists
            pk = cv.poly([Q(-6.5, 37.5), Q(6.5, 37.5), Q(8.5, 44.5), Q(-8.5, 44.5)])
            cv.part("pocket2", pk, cr, edge="dark", lv=np.where(pk, 2, 0) + np.where(pk & (cv.Y < R.Y(38.6)), 1, 0))
            self.baja(cv, "pocket2", R)
        if pose == "tell":
            self.sack(cv, R, *Q(15.5, 47.5))
        if pose == "hit":
            self.sack(cv, R, *Q(5.5, -1.5))

    def hair_front(self, cv, hf, pose, extra):
        s = hf.s
        hr = self.hair
        if s > 1.5:
            bun = cv.ell(*hf.P(2.5, 0.8), 4.2 * s, 3.2 * s)
        else:
            bun = cv.ell(*hf.P(0.8, -1.2), 5.4 * s, 4.4 * s) | cv.ell(*hf.P(-2.4, 0.4), 3.0 * s, 2.6 * s)
        cv.part("bun", bun, hr, rad=3 * s, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.10 if s >= 0.8 else 0, seed=51)
        tie = cv.ell(*hf.P(0.4, 3.0), 3.4 * s, 1.0 * s + 0.3)
        cv.part("scrunchie", tie, self.teal, edge="dark", lv=np.where(tie, 3, 0))
        yl = hf.t + 9.4 * s + 0.05 * (cv.X - hf.x - 1.5 * s) ** 2 / max(s, 0.5)
        crown = cv.ell(*hf.P(0, 10.4), 9.3 * s, 9.8 * s) & (cv.Y < yl)
        # swept fringe: a side part, one loose lock over the brow
        crown |= cv.capsule(*hf.P(-1, 6.5), *hf.P(-6.4, 11.8), 2.2 * s, 1.4 * s)
        for sd in (-1, 1):
            crown |= cv.capsule(*hf.P(sd * 7.6, 9.5), *hf.P(sd * 8.3, 15.0), 1.7 * s, 1.2 * s)
            crown |= cv.ell(*hf.P(sd * 8.6, 15.8), 1.2 * s, 1.3 * s)
        cv.part("hair", crown, hr, noedge=("face", "bun"), rad=4 * s, soft=1.0, cuts=(0.28, 0.54, 0.86),
                tex=0.10 if s >= 0.8 else 0, seed=52)
        if s >= 0.8:
            hid = [cv.names["hair"]]
            k = s
            for (a, b) in (((1, 2), (-4, 7)), ((3, 2.5), (6, 7.5)), ((-2, 3), (-6.5, 8))):
                cv.line(*hf.P(*a), *hf.P(*b), hr[1], only_own=hid)
            cv.puts([hf.P(-3, 3.8), hf.P(-4, 4.6), hf.P(-1, 3.0)], hr[4])

    def face_extra(self, cv, hf, view, pose, extra):
        # freckles across the nose + cheeks
        c, t = int(round(hf.x)), int(round(hf.t))
        fr = mix(self.skin[1], self.hair[1], 0.35)
        if view == "front" and hf.big:
            cv.puts([(c - 4, t + 16), (c - 3, t + 17), (c - 5, t + 17), (c + 3, t + 16), (c + 4, t + 17), (c + 5, t + 16)], fr)
        elif view == "front":
            cv.put(c - 3, t + 10, fr); cv.put(c + 3, t + 10, fr)

    def hair_side(self, cv, hf):
        s = hf.s
        hr = self.hair
        bun = cv.ell(*hf.P(-2.5, -0.5), 5.0 * s, 4.4 * s)
        cv.part("bun", bun, hr, rad=3 * s, cuts=(0.28, 0.54, 0.86), tex=0.10 if s >= 0.8 else 0, seed=53)
        yl = hf.t + (9.0 + 0.12 * (hf.x - cv.X) / s) * s
        m = cv.ell(*hf.P(-0.5, 10.2), 8.6 * s, 9.6 * s) & ((cv.X < hf.x + 0.5 * s) | (cv.Y < yl)) & (cv.Y < hf.t + 17 * s)
        m &= ~cv.ell(*hf.P(-0.5, 14.5), 2.0 * s, 2.4 * s)
        m |= cv.capsule(*hf.P(5, 7.5), *hf.P(7.5, 11.5), 1.6 * s, 1.1 * s)
        m |= cv.capsule(*hf.P(1.5, 12), *hf.P(2.5, 19), 1.4 * s, 1.0 * s)
        cv.part("hair", m, hr, noedge=("bun",), rad=4 * s, cuts=(0.28, 0.54, 0.86), tex=0.10 if s >= 0.8 else 0, seed=54)
        tie = cv.ell(*hf.P(-1.5, 3.2), 2.4 * s, 1.0 * s + 0.3, 0.6)
        cv.part("scrunchie", tie, self.teal, edge="dark", lv=np.where(tie, 3, 0))
        ear = cv.ell(*hf.P(-0.5, 14.5), max(1.0, 1.5 * s), max(1.3, 2.1 * s))
        cv.part("ear", ear, self.skin, edge="dark", rad=2, bias=-0.1)
        if s >= 0.8:
            c, t = int(round(hf.x)), int(round(hf.t))
            fr = mix(self.skin[1], self.hair[1], 0.35)
            cv.puts([(c + 6, t + 16), (c + 7, t + 17)], fr)

    def hair_back_view(self, cv, hf):
        s = hf.s
        hr = self.hair
        m = cv.ell(*hf.P(0, 10.4), 9.3 * s, 9.8 * s) & (cv.Y < hf.t + 18.5 * s)
        for sd in (-1, 1):
            m |= cv.capsule(*hf.P(sd * 6, 14), *hf.P(sd * 7.5, 20), 1.6 * s, 1.0 * s)
        cv.part("hair", m, hr, rad=4 * s, cuts=(0.28, 0.54, 0.86), tex=0.10 if s >= 0.8 else 0, seed=55)
        bun = cv.ell(*hf.P(-0.4, -0.6), 5.4 * s, 4.4 * s) | cv.ell(*hf.P(2.4, 0.8), 3.0 * s, 2.6 * s)
        cv.part("bun", bun, hr, rad=3 * s, cuts=(0.28, 0.54, 0.86), tex=0.10 if s >= 0.8 else 0, seed=56)
        tie = cv.ell(*hf.P(-0.2, 3.4), 3.4 * s, 1.0 * s + 0.3)
        cv.part("scrunchie", tie, self.teal, edge="dark", lv=np.where(tie, 3, 0))
        if s >= 0.8:
            for (a, b) in (((-1, 5), (-5, 16)), ((2, 5), (5, 16)), ((0, 9), (0, 17)), ((-4, 3), (-7, 10))):
                cv.line(*hf.P(*a), *hf.P(*b), hr[1], only_own=ids(cv, "hair"))

    def after_front(self, cv, R, hf, pose, extra):
        if pose == "tell":
            x, y = self.st["sack"]
            arc_marks(cv, x + 1, y + 6 * R.k, 5 * R.k, -2.3, -0.9, SPARK)
            sparkle(cv, int(x + 6 * R.k), int(y - 5 * R.k), big=R.battle)
        if pose == "hit":
            x, y = self.st["sack"]
            for (dx, dy) in ((-4, -2), (4, -2), (0, -5), (-3, 2), (4, 2)):
                if R.battle or abs(dx) < 4:
                    empty_put(cv, x + dx * R.k, y + dy * R.k, SPARK2)
            sweat(cv, int(hf.x - 10 * hf.s), int(hf.t + 8 * hf.s), R.battle)
        if extra == "toss":
            x, y = self.st["sack"]
            empty_put(cv, x, y + 3.5 * R.k, SPARK); empty_put(cv, x, y + 5 * R.k, SPARK)

    side_stride = ((-2.5, -1.2), (2.0, 1.2))

    def side_behind(self, cv, R):
        Q = R.Q
        hood = cv.ell(*Q(-5.5, 25), 4.0 * R.sx, 4.4 * R.k)
        cv.part("hood", hood, self.cream, rad=3, cuts=(0.4, 0.66, 0.92))
        self.baja(cv, "hood", R)
        arm(cv, R, "armF", [Q(-1, 25.5), Q(-3.5, 35), Q(-3, 42.5)], self.skin, self.cream, "long")
        self.baja(cv, "armF", R)
        fist(cv, *Q(-3, 43.5), "handF", R, self.skin)

    def torso_side(self, cv, R):
        Q = R.Q
        tor = cv.poly([Q(-6, 22.5), Q(3, 22.5), Q(7.5, 26), Q(8.5, 31), Q(8, 37), Q(9, 47.5), Q(-8.5, 47.5), Q(-8, 36), Q(-7.5, 28)])
        cv.part("torso", tor, self.cream, rad=7 * R.k + 1, soft=1.3, cuts=(0.28, 0.52, 0.84), tex=0.04, seed=41)
        self.baja(cv, "torso", R)
        hem = (cv.Y >= R.Y(45.8)) & own_mask(cv, "torso")
        for src in (self.cream, self.teal, self.navy):
            recolor(cv, "torso", hem, src, self.rust)
        pk = cv.poly([Q(2, 37.5), Q(8.2, 37.5), Q(8.8, 44.5), Q(2.5, 44.5)])
        cv.part("pocket", pk, self.cream, edge="dark", lv=np.where(pk, 2, 0))

    def arm_side(self, cv, R):
        Q = R.Q
        arm(cv, R, "arm", [Q(-0.5, 25.5), Q(1.5, 35), Q(6.5, 39.5)], self.skin, self.cream, "long")
        self.baja(cv, "arm", R)
        open_hand(cv, *Q(7.5, 40.5), "hand", R, self.skin, flip=-1)
        self.sack(cv, R, *Q(8, 37.6))

    def back_behind(self, cv, R):
        pass

    def torso_back(self, cv, R):
        self.torso_front(cv, R, "idle", None, back=True)
        Q = R.Q
        hood = cv.ell(*Q(0, 28), 7.4 * R.sx, 6.4 * R.k) | cv.ell(*Q(0, 24), 8.6 * R.sx, 2.6 * R.k)
        cv.part("hood", hood, self.cream, edge="dark", rad=4, cuts=(0.32, 0.6, 0.9))
        self.baja(cv, "hood", R)

    def arms_back(self, cv, R):
        Q = R.Q
        for sd, nm in ((1, "armR"), (-1, "armL")):
            arm(cv, R, nm, [Q(sd * 11, 25.5), Q(sd * 13.5, 35), Q(sd * 13, 42.5)], self.skin, self.cream, "long")
            self.baja(cv, nm, R)
            fist(cv, *Q(sd * 13, 43.8), "hand" + nm, R, self.skin)

    def back_over(self, cv, R, hf):
        pass

    # portrait
    p_top = 2.0

    def p_behind(self, cv, hf, expr):
        m = cv.ell(*hf.P(0, 12.5), 9.4 * hf.s, 8.6 * hf.s)
        cv.part("hairbk", m, self.hair, rad=8, cuts=(0.36, 0.62, 0.9), tex=0.06, seed=57)

    def p_shoulders(self, cv, c, expr):
        hood = cv.ell(c, 50, 20, 6) & cv.half(y=44)
        cv.part("hood", hood, self.cream, rad=6, cuts=(0.4, 0.66, 0.92))
        self.baja(cv, "hood", None)
        sh = cv.ell(c, 75, 31, 25) & cv.half(y=48)
        cv.part("shoulders", sh, self.cream, rad=14, soft=2.0, cuts=(0.34, 0.60, 0.90), tex=0.03, seed=41)
        self.baja(cv, "shoulders", None)

    def p_collar(self, cv, c, expr):
        for sd in (-1, 1):
            cv.line(c + sd * 3, 53, c + sd * 4, 63, self.rust[1])
            cv.line(c + sd * 4, 53, c + sd * 5, 63, self.rust[2])

    def p_face_marks(self, cv, c, expr):
        Char.p_face_marks(self, cv, c, expr)
        fr = mix(self.skin[1], self.hair[1], 0.3)
        for (x, y) in ((-7, 32), (-5, 33), (-8, 34), (-4, 31), (5, 32), (7, 33), (4, 31), (8, 31), (-2, 32), (2, 32)):
            cv.put(c + x, y, fr)

    def p_hair(self, cv, hf, expr):
        self.hair_front(cv, hf, "idle", None)
        # bigger curly wisps at portrait size
        hr = self.hair
        cv.puts([(hf.x - 15, 30), (hf.x - 16, 31), (hf.x - 16, 33), (hf.x + 15, 31), (hf.x + 16, 33)], hr[1])

    def p_after(self, cv, c, expr):
        Char.p_after(self, cv, c, expr)
        if expr == "warm":
            note(cv, 4, 4, NOTE_A)


# ==========================================================================
# DRUMMER -- campus bucket drummer: big guy, backwards black cap, short beard,
#            CU-gold hoodie with pushed-up sleeves, an orange 5-gallon bucket on a strap
# ==========================================================================
class Drummer(Char):
    id = "drummer"
    title = "Drummer (bucket busker)"
    H, WH = 76, 51
    build = 1.2
    hipw = 1.3
    face_w = 1.08
    top = 1.6
    hit_dx = 2
    skin = [(78, 40, 24), (148, 90, 56), (184, 122, 80), (208, 150, 104), (228, 182, 138)]
    hair = [(14, 10, 10), (30, 22, 20), (48, 36, 32), (68, 52, 46), (94, 74, 64)]
    cap = [(14, 14, 20), (30, 30, 40), (46, 46, 60), (66, 66, 84), (96, 96, 118)]
    gold = [(98, 76, 32), (164, 134, 72), (204, 176, 110), (228, 206, 148), (246, 232, 192)]
    jog = [(18, 18, 24), (38, 38, 50), (58, 58, 74), (82, 82, 100), (116, 116, 136)]
    red = [(90, 16, 20), (170, 34, 40), (214, 60, 60), (238, 104, 96), (252, 160, 148)]
    bucket = [(110, 40, 6), (206, 92, 18), (244, 138, 30), (252, 176, 70), (255, 214, 140)]
    iris = (60, 36, 22)
    iris_d = (28, 16, 10)
    brow = (20, 14, 12)
    brow2 = (34, 26, 22)
    lip = (150, 84, 64)
    blush = (214, 120, 90)

    def shoe(self, cv, R, name, fx, lift, s, side=False, far=False):
        sneaker(cv, R, name, fx, self.red, RAMP["white"], lift, side=side, high=True)

    def leg(self, cv, R, name, pts, s, far=False):
        m = cv.capsule(*pts[0], *pts[1], R.r(4.6, 2.6), R.r(4.0, 2.3)) | cv.capsule(*pts[1], *pts[2], R.r(4.0, 2.3), R.r(3.0, 1.8))
        cv.part(name, m, self.jog, rad=3.8 * R.k + 0.4, soft=0.8, cuts=(0.30, 0.55, 0.88) if not far else (0.45, 0.70, 0.95),
                tex=0.04, seed=61 + s)
        ax, ay = pts[-1]
        cuff = cv.capsule(ax, ay - R.r(1.8, 0.8), ax, ay, R.r(3.2, 1.9)) & cv.half(y=ay - R.r(1.8, 0.8)) & own_mask(cv, name)
        recolor(cv, name, cuff, self.jog, [self.jog[0], self.jog[0], self.jog[1], self.jog[1], self.jog[2]])
        if s != 0 and R.battle:
            # gold side stripe down the outer seam
            hx, hy = pts[0]
            kx, ky = pts[1]
            off = s * R.r(3.2, 1.8)
            cv.line(hx + off * 1.15, hy + 2, kx + off * 1.0, ky, self.gold[2], only_own=[cv.names[name]])
            cv.line(kx + off * 1.0, ky, ax + off * 0.8, ay - 2, self.gold[1], only_own=[cv.names[name]])

    def torso_front(self, cv, R, pose, extra, back=False):
        m = self.torso_mask(cv, R, sw=0.92, belly=0.92, ww=0.98, hw=0.95)
        cv.part("torso", m, self.gold, rad=9 * R.k + 1, soft=1.6, cuts=(0.34, 0.60, 0.90), tex=0.03, seed=71)
        hem = (cv.Y >= R.Y(45.4)) & own_mask(cv, "torso")
        recolor(cv, "torso", hem, self.gold, [self.gold[0], self.gold[0], self.gold[1], self.gold[1], self.gold[2]])
        Q = R.Q
        if back:
            hood = cv.ell(*Q(0, 26.5), 7.6 * R.sx, 4.8 * R.k)
            cv.part("hood", hood, self.gold, edge="dark", rad=4, cuts=(0.32, 0.6, 0.9))
            return
        hood = cv.ell(*Q(0, 22.8), 7.2 * R.sx, 2.8 * R.k) & ~cv.ell(*Q(0, 21.6), 4.0 * R.sx, 2.0 * R.k)
        cv.part("hoodrim", hood, self.gold, noedge=("torso",), lv=np.where(hood, 3, 0) - np.where(hood & (cv.X > R.c + 2), 1, 0))
        if R.battle:
            for sd in (-1, 1):
                cv.line(R.X(sd * 2.2), R.Y(24), R.X(sd * 2.6), R.Y(31), (30, 26, 30))

    def strap(self, cv, R, a, b, name="strap"):
        m = cv.capsule(*a, *b, R.r(1.2, 0.7))
        cv.part(name, m, self.cap, edge="dark", lv=np.where(m, 3, 0))

    def bucket_front(self, cv, R):
        Q = R.Q
        top, bot = 44.0, 58.5
        body = cv.poly([Q(-6.6, top), Q(6.6, top), Q(8.0, bot), Q(-8.0, bot)]) | cv.ell(*Q(0, bot), 8.0 * R.sx, R.r(1.6, 0.8))
        # cylinder shading: lit band left of centre, dark right edge
        xr = (cv.X - R.c) / (8.0 * R.sx)
        lv = np.where(body, np.where(xr < -0.75, 2, np.where(xr < -0.1, 4, np.where(xr < 0.45, 3, np.where(xr < 0.8, 2, 1)))), 0)
        cv.part("bucket", body, self.bucket, edge="ink", lv=lv)
        lid = cv.ell(*Q(0, top), 6.6 * R.sx, R.r(2.4, 1.2))
        cv.part("bhead", lid, self.bucket, edge="ink", lv=np.where(lid, 3, 0) + np.where(lid & (cv.X < R.c - 1) & (cv.Y < R.Y(top)), 1, 0))
        bk = self.bucket
        bid = [cv.names["bucket"]]
        for u in ((49.0, 52.5) if R.battle else (51.0,)):
            y = R.Y(u)
            cv.line(R.X(-8.2), y, R.X(8.2), y, bk[1], only_own=bid)
        lip = (cv.Y >= R.Y(bot) - (1.4 if R.battle else 0.6)) & own_mask(cv, "bucket")
        recolor(cv, "bucket", lip, bk, [bk[0], bk[1], bk[1], bk[2], bk[3]])
        if R.battle:
            # stick scuffs on the drum head
            cv.puts([(R.X(-2), R.Y(top) - 0.4), (R.X(2.5), R.Y(top) + 0.6)], bk[2])
        self.strap(cv, R, Q(7.2, 46), Q(-10.2, 24.8))

    def stick(self, cv, R, a, b, name):
        """Drumsticks are 1-2px wide, so they are painted after the outline pass (an ink pass would
        swallow them): a light core with a dark-brown shadow line, passing behind the fists."""
        self.st.setdefault("sticks", []).append((a, b))

    def draw_sticks(self, cv, R):
        wd = RAMP["wood"]
        hands = ids(cv, *[n for n in cv.names if n.startswith("hand")])
        for a, b in self.st.get("sticks", []):
            dx, dy = b[0] - a[0], b[1] - a[1]
            # shadow on the side away from the key light
            ox, oy = (0, 1) if abs(dx) >= abs(dy) else (1, 0)
            for (x0, y0, x1, y1, col) in ((a[0] + ox, a[1] + oy, b[0] + ox, b[1] + oy, wd[0]), (a[0], a[1], b[0], b[1], wd[3])):
                if not R.battle and col == wd[0]:
                    col = wd[1]
                n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
                for j in range(n + 1):
                    x, y = int(round(x0 + (x1 - x0) * j / n)), int(round(y0 + (y1 - y0) * j / n))
                    if 0 <= x < cv.w and 0 <= y < cv.h and cv.own[y, x] not in hands:
                        cv.put(x, y, col)
            bx, by = int(round(b[0])), int(round(b[1]))
            cv.put(bx, by, wd[4])

    def stick_from(self, cv, R, hand, ang, length, back=3.0, name="stk"):
        ux, uy = math.cos(ang), math.sin(ang)
        a = (hand[0] - ux * back * R.k, hand[1] - uy * back * R.k)
        b = (hand[0] + ux * length * R.k, hand[1] + uy * length * R.k)
        self.stick(cv, R, a, b, name)
        return b

    def arms_front(self, cv, R, pose, extra):
        Q = R.Q
        sk, gd = self.skin, self.gold
        self.bucket_front(cv, R)

        def a(name, pts):
            arm(cv, R, name, pts, sk, gd, "elbow", tex=0.03, seed=72)

        H = {}
        if pose == "tell":
            a("armR", [Q(-12, 25.5), Q(-18.5, 19), Q(-13.5, 9.5)])
            a("armL", [Q(12, 25.5), Q(18.5, 19), Q(13.5, 9.5)])
            H["R"], H["L"] = Q(-13.2, 9.0), Q(13.2, 9.0)
            self.stick_from(cv, R, H["R"], -0.85, 13, name="stkR")
            self.stick_from(cv, R, H["L"], math.pi + 0.85, 13, name="stkL")
        elif pose == "hit":
            a("armR", [Q(-12, 25.5), Q(-18, 33), Q(-20, 26)])
            a("armL", [Q(12, 25.5), Q(18, 31), Q(21, 23.5)])
            H["R"], H["L"] = Q(-20.2, 24.8), Q(21.2, 22.2)
            self.stick_from(cv, R, H["R"], -2.0, 9, name="stkR")
        else:
            a("armR", [Q(-12, 25.5), Q(-17, 35), Q(-9.5, 41.5)])
            H["R"] = Q(-9.3, 41.5)
            self.stick_from(cv, R, H["R"], 0.55, 8, name="stkR")
            if extra == "twirl":
                a("armL", [Q(12, 25.5), Q(17.5, 34), Q(15, 30)])
                H["L"] = Q(15.2, 29.5)
                self.stick_from(cv, R, H["L"], -0.15, 8, back=6, name="stkL")
            elif extra == "tap":
                a("armL", [Q(12, 25.5), Q(17, 35), Q(10, 39)])
                H["L"] = Q(9.8, 38.8)
                self.stick_from(cv, R, H["L"], math.pi - 0.2, 8, name="stkL")
            elif pose == "talk":
                a("armL", [Q(12, 25.5), Q(18, 31), Q(18.5, 22.5)])
                H["L"] = Q(18.6, 22.0)
                self.stick_from(cv, R, H["L"], -1.35, 11, name="stkL")
            else:
                a("armL", [Q(12, 25.5), Q(17, 35), Q(9.5, 41.5)])
                H["L"] = Q(9.3, 41.5)
                self.stick_from(cv, R, H["L"], math.pi - 0.55, 8, name="stkL")
        for k_, h in H.items():
            fist(cv, h[0], h[1], "hand" + k_, R, sk, r=2.6)
        if extra == "tap":
            # the right stick lifted a touch too
            pass

    def hair_front(self, cv, hf, pose, extra):
        s = hf.s
        # sideburns into the beard
        m = cv.empty()
        for sd in (-1, 1):
            m |= cv.capsule(*hf.P(sd * 7.2 * self.face_w, 9.5), *hf.P(sd * 7.2 * self.face_w, 15.5), 1.4 * s, 1.3 * s)
        cv.part("hair", m, self.hair, noedge=("face",), rad=2 * s, cuts=(0.36, 0.6, 0.9))
        self.beard(cv, hf, pose)
        self.cap_front(cv, hf)

    def beard(self, cv, hf, pose):
        s = hf.s
        fw = self.face_w
        face = own_mask(cv, "face")
        jaw = (cv.ell(*hf.P(0, 16.8), 7.6 * s * fw, 6.6 * s) & (cv.Y > hf.t + 16.2 * s)) | \
              (cv.ell(*hf.P(0, 14), 7.5 * s * fw, 7.4 * s) & (np.abs(cv.X - hf.x) > 5.4 * s * fw) & (cv.Y > hf.t + 13 * s))
        m = jaw & face
        m &= ~cv.ell(*hf.P(0, 18.6), 3.0 * s, 1.4 * s + 0.2) if s >= 0.8 else ~cv.ell(*hf.P(0, 18.9), 1.6 * s, 0.9)
        cv.part("beard", m, self.hair, edge="dark", noedge=("face",), rad=2.5 * s, soft=0.8, cuts=(0.32, 0.6, 0.9),
                tex=0.08 if s >= 0.8 else 0, seed=73)
        # moustache
        if s >= 0.8:
            mo = cv.ell(*hf.P(0, 17.9), 3.4 * s, 0.9 * s + 0.2)
            cv.part("stache", mo, self.hair, edge=None, lv=np.where(mo, 2, 0))

    def cap_front(self, cv, hf, view="front"):
        self.beanie(cv, hf, view)

    def beanie(self, cv, hf, view="front"):
        """Black slouch beanie with a ribbed cuff and one CU-gold stripe."""
        s, fw = hf.s, self.face_w
        sx = 1 if view != "side" else 0
        cx = 0 if view != "side" else -0.5
        curve = 0.02 * (cv.X - hf.x) ** 2 / max(s, 0.5) * sx
        yb = hf.t + 10.2 * s + curve
        if view == "side":
            yb = hf.t + (10.4 - 0.12 * (cv.X - hf.x) / s) * s
        dome = cv.ell(*hf.P(cx, 8.4), 9.6 * s * fw, 9.4 * s) & (cv.Y < yb)
        dome |= cv.ell(*hf.P(cx - 1.4, 0.4), 6.2 * s, 2.8 * s)
        cv.part("cap", dome, self.cap, edge="dark", rad=6 * s, soft=1.0, cuts=(0.28, 0.54, 0.86), tex=0.05 if s >= 0.8 else 0, seed=77)
        ct = hf.t + 6.6 * s + curve if view != "side" else yb - 3.6 * s
        cuff = cv.ell(*hf.P(cx, 8.4), 10.1 * s * fw, 9.9 * s) & (cv.Y < yb + 0.4) & (cv.Y >= ct)
        if view == "side":
            cuff &= cv.X < hf.x + 7.6 * s
        cv.part("cuff", cuff, self.cap, edge="dark", noedge=("cap",), lv=np.where(cuff, 2, 0) + np.where(cuff & (cv.X < hf.x - 2 * s), 1, 0))
        # gold stripe through the cuff
        mid = (cv.Y >= ct + 1.4 * s - 0.5) & (cv.Y < ct + 1.4 * s + (0.5 if s < 1.5 else 1.3))
        recolor(cv, "cuff", mid & own_mask(cv, "cuff"), self.cap, [self.gold[0], self.gold[1], self.gold[2], self.gold[3], self.gold[4]])
        if s >= 0.8:
            cid = cv.names["cuff"]
            for x in range(int(hf.x - 11 * s), int(hf.x + 11 * s), 2 if s < 1.5 else 3):
                for y in range(int(hf.t + 3 * s), int(hf.t + 12 * s) + 2):
                    if 0 <= x < cv.w and 0 <= y < cv.h and cv.own[y, x] == cid and not mid[y, x] and tuple(cv.col[y, x]) in (self.cap[2], self.cap[3]):
                        cv.put(x, y, self.cap[1])
            cv.puts([hf.P(cx - 5, 3.0), hf.P(cx - 6, 4.0)], self.cap[4])

    def face_extra(self, cv, hf, view, pose, extra):
        pass

    def mouth_b(self, cv, c, y, pose):
        Char.mouth_b(self, cv, c, y, pose)

    def after_front(self, cv, R, hf, pose, extra):
        self.draw_sticks(cv, R)
        if pose == "tell":
            sparkle(cv, int(R.X(0)), int(R.Y(-11)), big=R.battle)
            for sd in (-1, 1):
                arc_marks(cv, R.X(sd * 13), R.Y(-1), 6 * R.k, -math.pi / 2 - sd * 0.9, -math.pi / 2 - sd * 0.2, SPARK)
        if pose == "hit":
            # the left stick flies off, spinning
            x, y = R.Q(23, 6)
            L = 5 * R.k
            self.st["sticks"] = [((x - L, y + L * 0.4), (x + L, y - L * 0.4))]
            self.draw_sticks(cv, R)
            arc_marks(cv, x, y, 7 * R.k, -2.8, -1.8, SPARK)
            arc_marks(cv, x, y, 7 * R.k, 0.3, 1.3, SPARK)
            sweat(cv, int(hf.x - 10 * hf.s), int(hf.t + 5 * hf.s), R.battle)
        if pose == "talk" and R.battle:
            note(cv, int(R.X(24)), int(R.Y(4)), NOTE_S)
        if extra == "twirl":
            x, y = R.Q(15.2, 29.5)
            arc_marks(cv, x, y, 7 * R.k, -2.2, -0.6, SPARK)
        if extra == "tap":
            note(cv, int(R.X(-18)), int(R.Y(24)), NOTE_S)

    side_stride = ((-3.0, -1.0), (2.6, 1.0))

    def after_side(self, cv, R, hf):
        self.draw_sticks(cv, R)

    def after_back(self, cv, R, hf):
        self.draw_sticks(cv, R)

    def side_behind(self, cv, R):
        Q = R.Q
        arm(cv, R, "armF", [Q(-1, 25.5), Q(-4, 34), Q(-1, 40)], self.skin, self.gold, "elbow")
        fist(cv, *Q(-0.5, 40.5), "handF", R, self.skin)

    def torso_side(self, cv, R):
        Q = R.Q
        tor = cv.poly([Q(-6, 22.5), Q(3, 22.5), Q(8, 26), Q(9.5, 31), Q(9, 37), Q(9.5, 47), Q(-8.5, 47), Q(-8.5, 36), Q(-8, 28)])
        tor |= cv.ell(*Q(5, 40), 7.5 * R.sx, 7 * R.sy)
        cv.part("torso", tor, self.gold, rad=8 * R.k + 1, soft=1.4, cuts=(0.28, 0.52, 0.84), tex=0.03, seed=71)
        hood = cv.ell(*Q(-5, 25.5), 4.4 * R.sx, 4.0 * R.k)
        cv.part("hood", hood, self.gold, edge="dark", noedge=("torso",), rad=3, cuts=(0.36, 0.62, 0.9))
        # bucket in front of the belly, side-on
        b = cv.poly([Q(8.0, 45.5), Q(13.5, 45.5), Q(14.6, 60.5), Q(6.8, 60.5)])
        cv.part("bucket", b, self.bucket, edge="ink", rad=4 * R.k, cuts=(0.28, 0.52, 0.86))
        lid = cv.ell(*Q(10.8, 45.5), 2.8 * R.sx, R.r(1.0, 0.6))
        cv.part("bhead", lid, self.bucket, edge="ink", lv=np.where(lid, 4, 0))
        for u in ((50.0, 54.5) if R.battle else (52.0,)):
            cv.line(R.X(7.4), R.Y(u), R.X(14), R.Y(u), self.bucket[1], only_own=ids(cv, "bucket"))
        self.strap(cv, R, Q(9, 47), Q(1.5, 24))

    def arm_side(self, cv, R):
        Q = R.Q
        arm(cv, R, "arm", [Q(-0.5, 25.5), Q(1.5, 35), Q(8.5, 41)], self.skin, self.gold, "elbow")
        h = Q(9, 41.5)
        self.stick_from(cv, R, h, 0.35, 8, name="stk")
        fist(cv, *h, "hand", R, self.skin, r=2.6)

    def hair_side(self, cv, hf):
        s = hf.s
        ear = cv.ell(*hf.P(-0.5, 14.5), max(1.0, 1.6 * s), max(1.3, 2.2 * s))
        cv.part("ear", ear, self.skin, edge="dark", rad=2, bias=-0.1)
        m = cv.ell(*hf.P(0, 12.5), 7.6 * s, 4.0 * s) & (cv.X < hf.x + 1.0 * s) & ~ear
        m |= cv.capsule(*hf.P(1.4, 10), *hf.P(1.6, 15.5), 1.3 * s)
        cv.part("hair", m, self.hair, rad=2 * s, cuts=(0.36, 0.6, 0.9))
        face = own_mask(cv, "face")
        beard = face & (((cv.Y > hf.t + 16.0 * s) & (cv.X < hf.x + 8.2 * s)) | ((cv.X < hf.x + 2.6 * s) & (cv.Y > hf.t + 13 * s)))
        beard &= ~(cv.ell(*hf.P(7.0, 18.8), 1.8 * s, 1.0 * s + 0.2))
        cv.part("beard", beard, self.hair, edge="dark", noedge=("face",), rad=2.5 * s, cuts=(0.32, 0.6, 0.9),
                tex=0.08 if s >= 0.8 else 0, seed=74)
        self.beanie(cv, hf, "side")

    def hair_back_view(self, cv, hf):
        s = hf.s
        for sd in (-1, 1):
            e = cv.ell(*hf.P(sd * 8.4, 14.5), max(1.0, 1.5 * s), max(1.3, 2.2 * s))
            cv.part("ear%d" % sd, e, self.skin, edge="dark", rad=2, bias=-0.1)
        m = cv.ell(*hf.P(0, 12), 8.6 * s, 7.6 * s) & (cv.Y < hf.t + 18.5 * s)
        cv.part("hair", m, self.hair, rad=3 * s, cuts=(0.32, 0.58, 0.88), tex=0.06 if s >= 0.8 else 0, seed=75)
        self.beanie(cv, hf, "back")

    def back_behind(self, cv, R):
        Q = R.Q
        # the bucket is hidden in front of him; only its strap shows on his back
        pass

    def torso_back(self, cv, R):
        self.torso_front(cv, R, "idle", None, back=True)
        Q = R.Q
        self.strap(cv, R, Q(-10, 45.5), Q(10.2, 24.8))

    def arms_back(self, cv, R):
        Q = R.Q
        for sd, nm in ((1, "armR"), (-1, "armL")):
            arm(cv, R, nm, [Q(sd * 12, 25.5), Q(sd * 16, 35), Q(sd * 14.5, 42.5)], self.skin, self.gold, "elbow")
            h = Q(sd * 14.6, 43.6)
            self.stick_from(cv, R, h, math.pi / 2 + sd * 0.25, 7, name="stk" + nm)
            fist(cv, *h, "hand" + nm, R, self.skin, r=2.6)

    # portrait
    def p_shoulders(self, cv, c, expr):
        sh = cv.ell(c, 75, 33, 25) & cv.half(y=47)
        cv.part("shoulders", sh, self.gold, rad=14, soft=2.0, cuts=(0.34, 0.60, 0.90), tex=0.03, seed=71)
        m = cv.capsule(c - 21, 50, c + 13, 64, 2.2)
        cv.part("strap", m, self.cap, edge="dark", lv=np.where(m, 3, 0))

    def p_collar(self, cv, c, expr):
        hood = cv.ell(c, 51, 12, 4.2) & ~cv.ell(c, 49.5, 7.5, 3.0) & cv.half(y=48)
        cv.part("hoodrim", hood, self.gold, noedge=("shoulders",), lv=np.where(hood, 3, 0) - np.where(hood & (cv.X > c + 3), 1, 0))
        for sd in (-1, 1):
            cv.line(c + sd * 4, 54, c + sd * 5, 63, (30, 26, 30))

    def p_hair(self, cv, hf, expr):
        c = 32
        s = hf.s
        m = cv.empty()
        for sd in (-1, 1):
            m |= cv.capsule(c + sd * 12.9 * self.face_w, 21, c + sd * 12.6 * self.face_w, 31, 1.8)
        cv.part("hair", m, self.hair, noedge=("face",), rad=3, cuts=(0.36, 0.6, 0.9))
        face = own_mask(cv, "face")
        jaw = face & (((cv.Y > 38.5) & ~cv.ell(c, 41.2, 6.0, 2.6)) | ((np.abs(cv.X - c) > 9.0) & (cv.Y > 31)) |
                      ((np.abs(cv.X - c) > 7.5) & (cv.Y > 35)))
        cv.part("beard", jaw, self.hair, edge="dark", noedge=("face",), rad=4, soft=1.2, cuts=(0.32, 0.6, 0.9), tex=0.10, seed=76)
        mo = (cv.ell(c, 38.6, 6.6, 1.6) & cv.half(y=37.6)) & ~cv.rect(c - 0.5, 36, c + 0.5, 37.6)
        cv.part("stache", mo, self.hair, edge="dark", lv=np.where(mo, 2, 0))
        # mouth back on top of the beard
        self.p_mouth(cv, c, 41, expr, getattr(self, "_talk", False))
        self.cap_front(cv, hf)

    def portrait(self, expr, talk=False):
        self._talk = talk
        return Char.portrait(self, expr, talk)

    def p_after(self, cv, c, expr):
        Char.p_after(self, cv, c, expr)
        if expr == "warm":
            note(cv, 4, 6, NOTE_A)


CHARS = {c.id: c for c in (Cyclist(), Runner(), Hippie(), Drummer())}

# per-id world idle extras (pose1, pose2) and what they are
IDLE = {
    "cyclist": (("strap", "adjusts her helmet strap"), ("pocket", "free hand in jacket pocket, glancing aside")),
    "runner": (("watch", "checks his GPS watch"), ("drink", "sips from his bottle")),
    "hippie": (("toss", "tosses the hacky sack up"), ("lookup", "hands in the pocket, gazing at the sky")),
    "drummer": (("twirl", "twirls a drumstick"), ("tap", "taps out a beat")),
}


# ==========================================================================
# output
# ==========================================================================
def foot_x(cv, R, view):
    return int(round(R.c))


def body_height(img):
    a = np.array(img)[..., 3] > 0
    rows = np.nonzero(a.any(axis=1))[0]
    return img.height - rows[0], rows[-1] == img.height - 1


def diff_box(a, b):
    d = np.any(np.array(a) != np.array(b), axis=2)
    ys, xs = np.nonzero(d)
    if len(xs) == 0:
        return None, 0
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), int(d.sum())


def build(cid):
    ch = CHARS[cid]
    here = os.path.join(ROOT, cid)
    out = os.path.join(here, "out")
    for d in (out, os.path.join(out, "talk"), os.path.join(out, "idle")):
        os.makedirs(d, exist_ok=True)
    feet, cells, heights = {}, {}, {}
    for battle, prefix in ((True, "battle"), (False, "world")):
        views = [ch.front("idle", battle), ch.front("talk", battle), ch.front("tell", battle), ch.front("hit", battle),
                 ch.side(battle), ch.back(battle)]
        for i, (cv, R) in enumerate(views):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            h, grounded = body_height(img)
            assert grounded, (cid, name, "feet not on the bottom row")
            heights[name] = int(h)
            img.save(os.path.join(out, name))
            feet[name] = [foot_x(cv, R, i), img.height - 1]
            cells[name] = img
    for i, e in enumerate(EXPRS):
        img = ch.portrait(e).image()
        img.save(os.path.join(out, "portrait-%d.png" % i))
        cells["portrait-%d.png" % i] = img
        t_img = ch.portrait(e, talk=True).image()
        box, n = diff_box(img, t_img)
        assert box and box[1] >= 36 and box[3] <= 48, ("talk diff outside the mouth", cid, e, box)
        t_img.save(os.path.join(out, "talk", "%s-%d.png" % (cid, i)))
        cells["talk-%d.png" % i] = t_img
    base = cells["world-0.png"]
    idle_log = {}
    for key, extra in (("blink", "blink"), ("pose1", IDLE[cid][0][0]), ("pose2", IDLE[cid][1][0])):
        img = ch.front("idle", False, extra)[0].image()
        assert img.size == base.size
        box, n = diff_box(base, img)
        h, grounded = body_height(img)
        assert grounded
        # feet untouched: the bottom 12 rows must be identical (upper body only)
        assert box is None or np.array_equal(np.array(base)[-10:], np.array(img)[-10:]), (cid, key, "legs changed")
        idle_log[key] = (n, box)
        img.save(os.path.join(out, "idle", "%s-%s.png" % (cid, key)))
        cells["idle-%s.png" % key] = img
    with open(os.path.join(out, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    meta = {"id": cid, "title": ch.title, "battle_height": heights["battle-0.png"], "world_height": heights["world-0.png"],
            "measured": heights, "idle": {k: IDLE[cid][j][1] for j, k in enumerate(("pose1", "pose2"))}}
    with open(os.path.join(out, "meta.json"), "w") as f:
        json.dump(meta, f, indent=1)
    contact_sheet(cid, cells, os.path.join(here, "sheet.png"))
    return cells, feet, meta, idle_log


# --------------------------------------------------------------------------
# contact sheets
# --------------------------------------------------------------------------
BG = (44, 44, 62, 255)
GROUND = (70, 70, 96, 255)


def up(im, S=3):
    return im.resize((im.width * S, im.height * S), Image.NEAREST)


def render_rows(rows, title, path, ground_rows=None):
    font = ImageFont.load_default()
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
        grounded = ground_rows is None or ri in ground_rows
        if grounded:
            d.rectangle([0, base, W, base + 1], fill=GROUND)
        for im, label in r:
            tp = base - im.height if grounded else y
            sheet.alpha_composite(im, (x, tp))
            d.text((x, base + 4), label, fill=(200, 200, 220, 255), font=font)
            x += im.width + pad
        y += rh
    sheet.convert("RGB").save(path)


def contact_sheet(cid, cells, path, S=3):
    ref = Image.open(CAST_REF).convert("RGBA") if os.path.exists(CAST_REF) else None
    r1 = [(up(cells["battle-%d.png" % i]), "battle-%d" % i) for i in range(6)]
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
    render_rows([r1, r2, r3], "%s (%s) -- 3x; cast crops from designs/cast-reference.png at the same 3x" % (CHARS[cid].title, cid),
                path, ground_rows=(0, 1))


def lineup(path=os.path.join(ROOT, "encounters-a-lineup.png"), S=3):
    ref = Image.open(CAST_REF).convert("RGBA") if os.path.exists(CAST_REF) else None
    r1, r2, r3 = [], [], []
    for cid in CHARS:
        o = os.path.join(ROOT, cid, "out")
        r1.append((up(Image.open(os.path.join(o, "battle-0.png"))), "%s battle-0" % cid))
        r2.append((up(Image.open(os.path.join(o, "world-0.png"))), "%s world-0" % cid))
        r3.append((up(Image.open(os.path.join(o, "portrait-0.png"))), "%s portrait-0" % cid))
    for extra in ("sunbeam", "chad"):
        p = os.path.join(ROOT, extra, "out", "battle-0.png")
        if os.path.exists(p):
            r1.append((up(Image.open(p)), "%s (boss) battle-0" % extra))
    if ref is not None:
        r1.append((ref.crop((0, 40, 240, 285)), "cast: eric 80"))
        r1.append((ref.crop((1440, 40, 1848, 285)), "cast: dev 80, jakerson 80"))
        r2.append((ref.crop((990, 320, 1520, 496)), "cast: jules, imani, dev (world)"))
        r3.append((ref.crop((830, 515, 1230, 708)), "cast: dev, jakerson"))
    render_rows([r1, r2, r3], "Encounter cast A: cyclist, runner, hippie, drummer -- 3x, beside the existing cast", path,
                ground_rows=(0, 1))


if __name__ == "__main__":
    todo = sys.argv[1:] or list(CHARS)
    for cid in todo:
        cells, feet, meta, idle_log = build(cid)
        print(cid, "battle", meta["battle_height"], "world", meta["world_height"], meta["measured"])
        for k, v in idle_log.items():
            print("  idle", k, "changed", v[0], "px in", v[1])
    if not sys.argv[1:]:
        lineup()
