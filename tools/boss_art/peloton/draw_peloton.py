#!/usr/bin/env python3
"""Captain Lance and the Flatirons Peloton -- procedural pixel-art sprites for
"After Hours - College Tale" (F01 boss, replaces the cone committee).

Same contract as Professor Eric (tools/eric_art/draw_eric.py): everything is
drawn at its final pixel size with aliased analytic shapes and per-pixel
placement, and nothing drawn is ever resampled.  The only scaling in this file
is the nearest-neighbour blow-up of the previews and the contact sheet.

Look: a Boulder road-club captain in matching neon-chartreuse lycra with a hot
pink Flatirons-peaks chevron, an aero time-trial helmet with an iridescent
flip-up visor, white socks and shoes, on a hot-pink race bike.  In battle he
stands on the pedals; in the world he stands in front of the bike.

Outputs (in ./out next to this script):
  battle-0..5.png    84px battle cells on the bike, 88x88 canvas (0 front, 1 talk, 2 tell, 3 hit, 4 side R, 5 back)
  entrance.png       cell 12 "peloton-entrance": a wheelie with a fist pump (wide canvas)
  peloton-riders.png battle-only prop layer: the five Flatirons riders in an echelon behind him
  peloton-riders.json  its anchor (Lance's battle foot point inside it) and draw order (behind)
  world-0..5.png     54px world cells (56x57) (same poses, standing in front of the bike)
  portrait-0..3.png  64x64 portraits (0 neutral, 1 warm, 2 concern, 3 surprised)
  talk/peloton-<f>.png      mouth-open portraits
  idle/peloton-{blink,pose1,pose2}.png  idle extras for world cell 0
  feet.json          foot point [x, y] for every body cell
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
PREV = os.path.join(HERE, "prev")

# --------------------------------------------------------------------------
# palette (Eric's ramp convention: 0 = line/darkest, 1 shadow, 2 mid, 3 light, 4 highlight)
# --------------------------------------------------------------------------
INK = (26, 21, 36)          # #1a1524 outer outline, shared with the cast

RAMP = {
    "skin":   [(84, 40, 30), (150, 86, 56), (194, 124, 82), (222, 160, 112), (242, 196, 150)],
    "hair":   [(64, 38, 18), (116, 74, 32), (164, 118, 54), (204, 164, 86), (236, 206, 132)],
    "neon":   [(58, 86, 12), (124, 170, 20), (182, 226, 34), (220, 250, 76), (246, 255, 176)],
    "pink":   [(98, 12, 64), (172, 26, 108), (228, 54, 146), (255, 110, 188), (255, 178, 224)],
    "lycra":  [(14, 12, 22), (30, 28, 42), (46, 44, 62), (66, 64, 88), (96, 94, 122)],
    "sock":   [(96, 98, 118), (172, 174, 192), (214, 216, 228), (238, 240, 246), (255, 255, 255)],
    "tire":   [(12, 10, 18), (26, 24, 34), (40, 38, 50), (60, 58, 72), (88, 86, 104)],
    "metal":  [(60, 62, 74), (128, 132, 146), (176, 180, 192), (214, 218, 226), (246, 248, 250)],
    "visor":  [(34, 26, 84), (70, 54, 160), (70, 140, 214), (110, 226, 226), (236, 255, 250)],
    "glove":  [(14, 12, 22), (30, 28, 42), (48, 46, 64), (70, 68, 90), (100, 98, 124)],
    "bottle": [(30, 70, 90), (90, 170, 196), (160, 220, 236), (210, 244, 250), (250, 255, 255)],
}
NEON, PINK, LYC, SKIN = RAMP["neon"], RAMP["pink"], RAMP["lycra"], RAMP["skin"]
EYE = (30, 22, 30)
WHITE = (250, 248, 244)
MOUTH = (74, 26, 34)
TONGUE = (196, 92, 96)
TEETH = (246, 244, 236)
BLUSH = (206, 104, 80)
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
# hand-placed pixel grids (heads are too small for analytic shapes to read)
# --------------------------------------------------------------------------
LEGEND = {
    "K": INK,
    "a": RAMP["neon"][0], "b": RAMP["neon"][1], "c": RAMP["neon"][2], "d": RAMP["neon"][3], "e": RAMP["neon"][4],
    "R": RAMP["pink"][1], "P": RAMP["pink"][2], "Q": RAMP["pink"][3], "S": RAMP["pink"][0],
    "m": RAMP["lycra"][1], "l": RAMP["lycra"][2], "n": RAMP["lycra"][3],
    "1": RAMP["skin"][0], "2": RAMP["skin"][1], "3": RAMP["skin"][2], "4": RAMP["skin"][3], "5": RAMP["skin"][4],
    "H": RAMP["hair"][1], "h": RAMP["hair"][2], "j": RAMP["hair"][3], "G": RAMP["hair"][0],
    "u": RAMP["visor"][0], "v": RAMP["visor"][1], "w": RAMP["visor"][2], "x": RAMP["visor"][3], "y": RAMP["visor"][4],
    "W": WHITE, "E": EYE, "O": MOUTH, "T": TEETH, "B": BLUSH, "t": TONGUE,
    "s": RAMP["sock"][2], "z": RAMP["sock"][3], "Z": RAMP["sock"][1],
}


def stamp(cv, rows, x0, y0, name, flip=False):
    """Paint a grid of legend letters ('.' = leave as is) as its own part."""
    m = cv.empty()
    w = max(len(r) for r in rows)
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch == ".":
                continue
            x = x0 + (w - 1 - i if flip else i)
            y = y0 + j
            if 0 <= x < cv.w and 0 <= y < cv.h:
                cv.col[y, x] = LEGEND[ch]
                cv.alpha[y, x] = True
                m[y, x] = True
    pid = len(cv.names)
    cv.names[name] = pid
    cv.own[m] = pid
    return m


def grid_sub(rows, edits):
    """Copy of a grid with {(col,row): char} replaced."""
    g = [list(r) for r in rows]
    for (i, j), ch in edits.items():
        while len(g[j]) <= i:
            g[j].append(".")
        g[j][i] = ch
    return ["".join(r) for r in g]


# battle head, profile facing right (26 x 24).  Neck base is at grid (15, 23).
HEAD_SIDE = [
    "...........KKKKKKK........",
    "........KKKPPPPPPPKK......",
    "......KKPPPdddeeeddKK.....",
    ".....KPPddddddeeeddcK.....",
    "....KPdddddddddddcccdK....",
    "...KPdddddddddddcccccdK...",
    "..KPdddccccccccccccccccK..",
    ".KPddcccccccccccbbbbbbbK..",
    "KPdccccbbbbbbbbbbbbbbbbbK.",
    "KPccbbbbbbbbbbmmmmmmmmmmK.",
    "KbcbbbbbbbaKbbK345555HHHK.",
    ".KabbbbbbaK.KbbK3454E4W4K.",
    "..KabbbbaK..KblK34444E445K",
    "...KaabaK...KKK2344444455K",
    "....KKKK.....K23444444444K",
    ".............K2m44B4444KK.",
    ".............K2m444OOOOK..",
    ".............K23m4444444K.",
    "..............K23m44444K..",
    "..............K122m333K...",
    "..............K122KKKK....",
    ".............K1223K.......",
    "............K11223K.......",
    "...........K112233K.......",
]
VISOR_UP_SIDE = {(19, 1): "K", (20, 1): "K", (21, 1): "K", (18, 2): "K", (19, 2): "v", (20, 2): "w", (21, 2): "x", (22, 2): "K",
                 (18, 3): "K", (19, 3): "v", (20, 3): "w", (21, 3): "x", (22, 3): "y", (23, 3): "K",
                 (19, 4): "K", (20, 4): "w", (21, 4): "x", (22, 4): "y", (23, 4): "K", (20, 5): "K", (21, 5): "K", (22, 5): "K"}
VISOR_DOWN_SIDE = {(17, 9): "K", (18, 9): "K", (19, 9): "K", (20, 9): "K", (21, 9): "K", (22, 9): "K", (23, 9): "K", (24, 9): "K",
                   (16, 10): "K", (17, 10): "v", (18, 10): "v", (19, 10): "w", (20, 10): "W", (21, 10): "x", (22, 10): "x", (23, 10): "y", (24, 10): "K",
                   (16, 11): "K", (17, 11): "u", (18, 11): "v", (19, 11): "W", (20, 11): "w", (21, 11): "x", (22, 11): "y", (23, 11): "y", (24, 11): "K",
                   (17, 12): "K", (18, 12): "K", (19, 12): "v", (20, 12): "w", (21, 12): "x", (22, 12): "x", (23, 12): "K", (24, 12): "4",
                   (19, 13): "K", (20, 13): "K", (21, 13): "K", (22, 13): "K"}


def head_side_grid(t, neck, pose="idle", visor_down=False, flip=False):
    """Stamp the profile head so its neck base lands on design point `neck`."""
    X, Y = t.p(*neck)
    g = HEAD_SIDE
    ed = {}
    if pose == "talk":
        ed.update({(19, 16): "O", (20, 16): "T", (21, 16): "T", (22, 16): "T", (23, 16): "K",
                   (19, 17): "O", (20, 17): "O", (21, 17): "t", (22, 17): "O", (23, 17): "K",
                   (20, 18): "4", (21, 18): "4", (22, 18): "4", (23, 18): "K"})
    elif pose == "grin":
        ed.update({(19, 16): "O", (20, 16): "T", (21, 16): "T", (22, 16): "T", (23, 16): "K", (18, 15): "O"})
    elif pose == "hit":
        ed.update({(20, 11): "4", (22, 11): "4", (21, 12): "4", (20, 12): "E", (21, 11): "E", (22, 12): "E",
                   (21, 10): "H", (22, 10): "4", (20, 10): "H", (19, 16): "4", (20, 16): "O", (21, 16): "O", (22, 16): "O"})
    if visor_down:
        ed.update(VISOR_DOWN_SIDE)
    else:
        ed.update(VISOR_UP_SIDE)
    g = grid_sub(g, ed)
    w = len(g[0])
    x0 = int(round(X)) - (w - 1 - 15 if flip else 15)
    return stamp(t.cv, g, x0, int(round(Y)) - 23, "head", flip=flip)


def _rows3(trip):
    out = []
    for l, m, r in trip:
        assert len(l) == 11 and len(m) == 3 and len(r) == 11, (l, m, r)
        out.append(l + m + r)
    return out


# battle head, facing the camera (25 x 25, centre column 12).  Neck base at grid (12, 24).
HEAD_FRONT = _rows3([
    ("........KKK", "KKK", "KKK........"),
    ("......KKeed", "PPP", "dccKK......"),
    (".....Keeddd", "PPP", "dccbbK....."),
    ("....Keddddd", "PPP", "dcccbbK...."),
    ("...Kedddddd", "PPP", "dccccbbK..."),
    ("...Keddddcc", "PPP", "cccccbbK..."),
    ("..Keddddccc", "PPP", "cccccbbbK.."),
    ("..Kdddccccc", "PPP", "cccccbbbK.."),
    (".Kddccccccc", "RRR", "ccccbbbbbK."),
    (".Kcbmmmmmmm", "mmm", "mmmmmmmbbK."),
    (".Kbm4555555", "555", "5555554mbK."),
    (".Kbm45HHHH5", "555", "5HHHH54mbK."),
    (".Kbm455WE55", "555", "55WE554mbK."),
    (".Kbm445EE55", "554", "55EE544mbK."),
    (".Kbm4445555", "553", "5555443mbK."),
    ("..Km4BH5555", "543", "5555HB3mK.."),
    ("..Km444Hhhh", "HGH", "hhH4443mK.."),
    ("..Km444555O", "OOO", "O555443mK.."),
    ("...Km444555", "555", "555443mK..."),
    ("....Km34444", "444", "44443mK...."),
    (".....Km3344", "343", "4333mK....."),
    (".......KK33", "333", "33KK......."),
    (".........K2", "122", "2K........."),
    (".........K3", "322", "2K........."),
    ("........K33", "322", "22K........"),
])
HEAD_FRONT = [r.replace("0", "O") for r in HEAD_FRONT]


def _overlay(rows):
    """{(col,row): ch} from a list of (row, col0, string)."""
    ed = {}
    for j, i0, s in rows:
        for k, ch in enumerate(s):
            if ch != ".":
                ed[(i0 + k, j)] = ch
    return ed


VISOR_UP_FRONT = _overlay([
    (3, 6, "KKKKKKKKKKKKK"),
    (4, 5, "KvwwxyyWyyxwwvK"),
    (5, 4, "KuvwwxxyyyxxwwvuK"),
    (6, 4, "KKKKKKKKKKKKKKKKK"),
])
VISOR_DOWN_FRONT = _overlay([
    (10, 3, "KKKKKKKKKKKKKKKKKKK"),
    (11, 3, "KuvvwwxWyyyxxwwvvuK"),
    (12, 3, "KuvvwWxxyyyxxwwvvuK"),
    (13, 3, "KuvvWwwxxyxxwwwvvuK"),
    (14, 4, "KvvwwxxK4KxxwwvvK"),
    (15, 5, "KKKKKK...KKKKKK"),
])
# eyes / mouths for the front head (grid coords)
FACE_FRONT = {
    "smile": {},
    "grin": _overlay([(17, 9, "OTTTTTO"), (18, 11, "OOO")]),
    "talk": _overlay([(17, 9, "OTTTTTO"), (18, 10, "OOtOO"), (19, 11, "OOO")]),
    "shout": _overlay([(17, 9, "OTTTTTO"), (18, 9, "OOtttOO"), (19, 10, "OOOOO")]),
    "hit": _overlay([(11, 6, "HH"), (11, 17, "HH"), (12, 7, "EE5"), (13, 7, "5EE"), (12, 15, "5EE"), (13, 15, "EE5"),
                     (17, 10, "OTTTO"), (18, 11, "OOO")]),
}


def head_front_grid(t, neck, pose="grin", visor="up", flip=False, extra=None):
    X, Y = t.p(*neck)
    ed = {}
    ed.update(FACE_FRONT.get(pose, {}))
    if visor == "up":
        ed.update(VISOR_UP_FRONT)
    elif visor == "down":
        ed.update(VISOR_DOWN_FRONT)
    if extra:
        ed.update(extra)
    g = grid_sub(HEAD_FRONT, ed)
    return stamp(t.cv, g, int(round(X)) - 12, int(round(Y)) - 24, "head", flip=flip)


# --------------------------------------------------------------------------
# a design-space frame: draw the same analytic shapes scaled / rotated / mirrored
# (shapes are rasterised directly at the target size -- no image resampling)
# --------------------------------------------------------------------------
class Tf:
    def __init__(self, cv, ox=0.0, oy=0.0, s=1.0, ax=0.0, ay=0.0, ang=0.0, flip=False):
        self.cv, self.ox, self.oy, self.s, self.ax, self.ay, self.ang, self.flip = cv, ox, oy, s, ax, ay, ang, flip

    def p(self, x, y):
        dx, dy = (x - self.ax), (y - self.ay)
        if self.flip:
            dx = -dx
        c, s = math.cos(self.ang), math.sin(self.ang)
        rx, ry = dx * c - dy * s, dx * s + dy * c
        return self.ox + self.s * rx, self.oy + self.s * ry

    def r(self, r, mn=0.55):
        return max(mn, r * self.s)

    def ell(self, x, y, rx, ry, ang=0.0):
        X, Y = self.p(x, y)
        a = (-ang if self.flip else ang) + self.ang
        return self.cv.ell(X, Y, self.r(rx), self.r(ry), a)

    def cap(self, x0, y0, x1, y1, r0, r1=None):
        a, b = self.p(x0, y0)
        c, d = self.p(x1, y1)
        return self.cv.capsule(a, b, c, d, self.r(r0), self.r(r1 if r1 is not None else r0))

    def chain(self, pts, r):
        m = self.cv.empty()
        for (a, b), (c, d) in zip(pts, pts[1:]):
            m |= self.cap(a, b, c, d, r)
        return m

    def poly(self, pts):
        return self.cv.poly([self.p(x, y) for x, y in pts])

    def rect(self, x0, y0, x1, y1):
        if self.ang == 0 and not self.flip:
            a, b = self.p(x0, y0)
            c, d = self.p(x1, y1)
            return self.cv.rect(min(a, c), min(b, d), max(a, c), max(b, d))
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def put(self, x, y, col):
        X, Y = self.p(x, y)
        self.cv.put(X, Y, col)

    def line(self, x0, y0, x1, y1, col):
        a, b = self.p(x0, y0)
        c, d = self.p(x1, y1)
        self.cv.line(round(a), round(b), round(c), round(d), col)


def ik(h, f, l1, l2, bend=1):
    """Knee/elbow position for a two-bone limb from h to f; bend picks the side."""
    dx, dy = f[0] - h[0], f[1] - h[1]
    d = math.hypot(dx, dy)
    d = min(d, l1 + l2 - 0.01)
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    hh = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / (math.hypot(dx, dy) or 1), dy / (math.hypot(dx, dy) or 1)
    mx, my = h[0] + ux * a, h[1] + uy * a
    return (mx - bend * uy * hh, my + bend * ux * hh)


def is_ink(cv):
    return (cv.col[..., 0] == INK[0]) & (cv.col[..., 1] == INK[1]) & (cv.col[..., 2] == INK[2])


# ==========================================================================
# the bike, side view (design space: ground y=87, rear hub (20,73), front hub (56,73))
# ==========================================================================
RH, FH, BB = (20.0, 73.0), (56.0, 73.0), (36.0, 75.0)
WR = 14.0                  # wheel radius
SEAT = (31.0, 51.0)        # saddle nose
HT_TOP, HT_BOT = (51.5, 53.0), (53.0, 60.0)
HOOD = (60.0, 51.5)


def wheel_side(t, hub, name, spokes=True, phase=0.0):
    cv = t.cv
    s = t.s
    hx, hy = hub
    tire = t.ell(hx, hy, WR, WR) & ~t.ell(hx, hy, WR - 2.2, WR - 2.2)
    cv.part(name + "tire", tire, "tire", edge="ink", rad=2, soft=0.5, cuts=(0.25, 0.55, 0.85))
    rim = t.ell(hx, hy, WR - 2.2, WR - 2.2) & ~t.ell(hx, hy, WR - 5.6, WR - 5.6)
    cv.part(name + "rim", rim, "lycra", edge=RAMP["lycra"][0], noedge=(name + "tire",), rad=3, soft=0.6,
            cuts=(0.2, 0.5, 0.8))
    # neon rim decal on the upper-right and lower-left arcs
    for a0 in (-1.15, 1.95):
        for k in range(7 if s > 0.8 else 4):
            a = a0 + k * (0.11 / max(s, 0.5))
            x, y = hx + (WR - 3.9) * math.cos(a), hy + (WR - 3.9) * math.sin(a)
            X, Y = t.p(x, y)
            xi, yi = int(round(X)), int(round(Y))
            if 0 <= yi < cv.h and 0 <= xi < cv.w and cv.own[yi, xi] == cv.names[name + "rim"]:
                cv.put(xi, yi, NEON[3] if k < 4 else NEON[2])
    # tire highlight on the upper-left (key light)
    for k in range(9 if s > 0.8 else 5):
        a = math.pi * 1.08 + k * 0.12 / max(s, 0.5)
        x, y = hx + (WR - 0.9) * math.cos(a), hy + (WR - 0.9) * math.sin(a)
        X, Y = t.p(x, y)
        xi, yi = int(round(X)), int(round(Y))
        if 0 <= yi < cv.h and 0 <= xi < cv.w and cv.own[yi, xi] == cv.names[name + "tire"] and not is_ink(cv)[yi, xi]:
            cv.put(xi, yi, RAMP["tire"][3])
    if spokes:
        n = 8 if s > 0.8 else 4
        for k in range(n):
            a = phase + k * 2 * math.pi / n
            t.line(hx + 1.2 * math.cos(a), hy + 1.2 * math.sin(a), hx + (WR - 5.8) * math.cos(a),
                   hy + (WR - 5.8) * math.sin(a), RAMP["metal"][1] if k % 2 else RAMP["metal"][0])
    hubm = t.ell(hx, hy, 1.7, 1.7)
    cv.part(name + "hub", hubm, "metal", edge="ink", rad=1.5, soft=0.3, bias=0.1)


def bike_side(t, pedal_ang=0.35, crank=True, drive=True, bottle=True):
    """Frame, wheels, cockpit.  pedal_ang: crank angle of the NEAR pedal (0 = forward, +ve down)."""
    cv = t.cv
    wheel_side(t, RH, "rw", phase=0.2)
    wheel_side(t, FH, "fw", phase=0.6)
    r = 1.75
    seat_cl = (32.5, 57.0)
    rear = t.cap(*BB, *RH, 1.2) | t.cap(*seat_cl, *RH, 1.1)
    cv.part("stays", rear, "pink", edge="dark", rad=1.5, soft=0.4, cuts=(0.25, 0.55, 0.85))
    main = (t.cap(*BB, *seat_cl, r) | t.cap(*seat_cl, *HT_TOP, r * 0.95) | t.cap(*HT_BOT, *BB, r * 1.15)
            | t.cap(*HT_TOP, *HT_BOT, r * 1.1))
    fork = t.cap(*HT_BOT, 55.4, 66.5, 1.5) | t.cap(55.4, 66.5, *FH, 1.4, 1.0)
    cv.part("frame", main | fork, "pink", edge="ink", rad=2, soft=0.5, cuts=(0.22, 0.52, 0.86))
    # neon "FLATIRONS" decal: a bright dash run along the down tube
    for k in range(6 if t.s > 0.8 else 3):
        f = 0.28 + k * 0.07 / max(t.s, 0.6)
        x, y = HT_BOT[0] + (BB[0] - HT_BOT[0]) * f, HT_BOT[1] + (BB[1] - HT_BOT[1]) * f
        t.put(x, y - 0.3, NEON[3])
    if bottle:
        b = t.cap(42.0, 67.5, 46.5, 63.2, 1.6)
        cv.part("bottle", b, "bottle", edge="dark", rad=1.5, soft=0.4, bias=0.05)
    # seatpost + saddle
    cv.part("post", t.cap(*seat_cl, 30.5, 52.5, 0.9), "metal", edge="ink", rad=1, soft=0.3)
    sad = t.poly([(24.5, 50.0), (33.5, 50.4), (34.5, 51.6), (26.0, 53.0), (24.0, 52.0)])
    cv.part("saddle", sad, "lycra", edge="ink", rad=1.5, soft=0.4, bias=0.1)
    # stem + drop bars (black tape) + pink hoods
    stem = t.cap(*HT_TOP, 57.0, 51.2, 1.0)
    bars = t.chain([(57.0, 51.2), (60.0, 51.0), (62.4, 53.0), (62.6, 56.6), (60.2, 58.4), (58.6, 57.8)], 0.95)
    cv.part("bars", stem | bars, "tire", edge="ink", rad=1, soft=0.3, cuts=(0.2, 0.5, 0.8))
    hood = t.ell(60.2, 50.6, 1.6, 1.4)
    cv.part("hood", hood, "lycra", edge="ink", rad=1, soft=0.3, bias=0.1)
    if crank:
        # chainring + crank
        ring = t.ell(*BB, 4.3, 4.3) & ~t.ell(*BB, 2.4, 2.4)
        cv.part("ring", ring, "metal", edge="ink", rad=1.3, soft=0.3, cuts=(0.2, 0.5, 0.82))
        # chain to the rear cog (upper + lower run)
        t.line(BB[0], BB[1] - 4.4, RH[0], RH[1] - 2.2, RAMP["metal"][0])
        t.line(BB[0] - 1, BB[1] + 4.2, RH[0] + 1, RH[1] + 2.0, RAMP["metal"][0])


def crank_arm(t, ang, name, near=True):
    cv = t.cv
    px, py = BB[0] + 7.0 * math.cos(ang), BB[1] + 7.0 * math.sin(ang)
    arm = t.cap(*BB, px, py, 1.25, 1.0)
    cv.part(name, arm, "metal" if near else "tire", edge="ink", rad=1, soft=0.3, cuts=(0.2, 0.45, 0.8))
    pd = t.cap(px - 2.0, py + 0.2, px + 2.0, py + 0.2, 0.8)
    cv.part(name + "pedal", pd, "tire", edge="ink", rad=1, soft=0.3)
    return (px, py)


# ==========================================================================
# rider parts (design space, battle scale; Tf scales them for world / paceline)
# ==========================================================================
def shoe_side(t, foot, name, far=False, toe=1):
    """Cycling shoe clipped to a pedal at `foot`; toe points +x (toe=1) or -x."""
    cv = t.cv
    fx, fy = foot
    m = t.ell(fx + 1.2 * toe, fy - 1.3, 4.4, 2.0, -0.12 * toe) | t.ell(fx - 1.6 * toe, fy - 2.4, 2.3, 2.1)
    cv.part(name, m, "sock", edge="ink", rad=2, soft=0.4, bias=-0.15 if far else 0.0, cuts=(0.25, 0.5, 0.82))
    # neon BOA strap
    t.line(fx - 0.6 * toe, fy - 3.4, fx + 1.2 * toe, fy - 2.4, NEON[2] if not far else NEON[1])
    t.put(fx + 4.6 * toe, fy - 1.0, RAMP["sock"][1])


def leg(t, hip, knee, foot, name, far=False, sock_dir=(0, -1), short=0.55):
    """Lycra short to mid-thigh, tanned calf with a bulge, white sock."""
    cv = t.cv
    b = -0.18 if far else 0.0
    kx, ky = knee
    fx, fy = foot
    ax, ay = fx + (kx - fx) * 0.18, fy + (ky - fy) * 0.18 - 1.6     # ankle just above the shoe
    hx, hy = hip
    mx, my = hx + (kx - hx) * short, hy + (ky - hy) * short           # shorts hem
    shin = t.cap(kx, ky, ax, ay, 2.3, 1.5)
    # calf bulge behind the shin, nearer the knee
    cxp, cyp = kx + (ax - kx) * 0.33, ky + (ay - ky) * 0.33
    vx, vy = ax - kx, ay - ky
    L = math.hypot(vx, vy) or 1
    nx, ny = -vy / L, vx / L
    side = 1 if (nx * (hx - kx) + ny * (hy - ky)) < 0 else -1
    shin |= t.ell(cxp + side * nx * 0.9, cyp + side * ny * 0.9, 2.6, 3.4, math.atan2(vy, vx) - math.pi / 2)
    thigh_skin = t.cap(mx, my, kx, ky, 3.0, 2.5)
    cv.part(name + "skin", thigh_skin | shin, "skin", edge="dark", rad=2.6, soft=0.7, bias=b,
            cuts=(0.28, 0.52, 0.86))
    sock = t.cap(ax, ay, fx + (ax - fx) * 0.2, fy + (ay - fy) * 0.2 - 0.6, 1.7)
    sock &= ~t.cap(kx, ky, ax + (kx - ax) * 0.14, ay + (ky - ay) * 0.14, 3.0) | t.cap(ax, ay, ax, ay, 1.7)
    cv.part(name + "sock", sock, "sock", edge="dark", noedge=(name + "skin",), rad=1.5, soft=0.4, bias=b)
    thigh = t.cap(hx, hy, mx, my, 4.1, 3.4)
    cv.part(name + "short", thigh, "lycra", edge="ink", rad=3, soft=0.8, bias=b, cuts=(0.22, 0.5, 0.82))
    # neon hem gripper band
    hem = thigh & ~t.cap(hx, hy, mx + (hx - mx) * 0.16, my + (hy - my) * 0.16, 4.2) & ~is_ink(cv)
    cv.fill(hem, NEON[1] if far else NEON[2])


def arm(t, sh, el, hand, name, far=False, sleeve=0.5, glove=True, fist=True, hand_r=2.2):
    cv = t.cv
    b = -0.18 if far else 0.0
    ex, ey = el
    sx, sy = sh
    mx, my = sx + (ex - sx) * sleeve, sy + (ey - sy) * sleeve
    skin = t.cap(mx, my, ex, ey, 2.2, 2.1) | t.cap(ex, ey, hand[0], hand[1], 2.1, 1.7)
    cv.part(name + "skin", skin, "skin", edge="dark", rad=2.2, soft=0.6, bias=b, cuts=(0.28, 0.52, 0.86))
    slv = t.cap(sx, sy, mx, my, 3.3, 2.9)
    cv.part(name + "sleeve", slv, "neon", edge="dark", rad=3, soft=0.7, bias=b, cuts=(0.25, 0.5, 0.84))
    # pink sleeve cuff
    cuff = slv & t.cap(mx, my, mx + (sx - mx) * 0.2, my + (sy - my) * 0.2, 3.3) & ~is_ink(cv)
    cv.fill(cuff, PINK[2] if not far else PINK[1])
    hm = t.ell(hand[0], hand[1], hand_r, hand_r)
    cv.part(name + "hand", hm, "glove" if glove else "skin", edge="ink", rad=2, soft=0.4, bias=b + 0.05)
    if glove:
        # fingers peek out of the fingerless glove
        X, Y = t.p(hand[0], hand[1] + hand_r * 0.6)
        cv.put(X, Y, SKIN[2] if not far else SKIN[1])
        cv.put(X + 1, Y, SKIN[1])
    return hm


def torso_side(t, hip, sh, name="torso", r_ch=6.4, r_hip=5.2):
    cv = t.cv
    m = t.cap(hip[0], hip[1], sh[0], sh[1], r_hip, r_ch)
    m |= t.ell(sh[0] - 1.0, sh[1] + 2.5, r_ch + 0.4, r_ch - 0.6, math.atan2(sh[1] - hip[1], sh[0] - hip[0]))
    cv.part(name, m, "neon", rad=6, soft=1.2, cuts=(0.28, 0.52, 0.84))
    # lower third of the jersey is hot pink under a Flatirons zig-zag (the club crest)
    zig_panel(t, m, hip, sh, name)
    return m


def head_side(t, c, pose="idle", visor_down=False, cap_name="helmet"):
    """Profile facing right; c = (x, y) of the face centre.  Battle scale only."""
    cv = t.cv
    x, y = c
    sk = SKIN
    # neck
    neck = t.cap(x - 1.0, y + 6, x - 4.0, y + 12, 2.8)
    cv.part("neck", neck, "skin", edge="dark", lv=np.where(neck, 2, 0))
    face = t.ell(x + 0.4, y + 0.6, 7.6, 8.2) | t.poly([(x - 4, y + 2), (x + 7.4, y + 1.6), (x + 7.0, y + 6.6), (x + 5.2, y + 8.8), (x + 1.0, y + 9.2), (x - 3, y + 7.0)])
    cv.part("face", face, "skin", rad=6, soft=1.2, cuts=(0.3, 0.52, 0.86), light=(0.1, -0.8, 0.6), bias=0.08)
    nose = t.poly([(x + 7.0, y - 1.4), (x + 9.6, y + 2.8), (x + 9.0, y + 3.4), (x + 7.0, y + 3.4)])
    cv.part("nose", nose, "skin", edge="dark", noedge=("face",), rad=2, soft=0.4, bias=0.1)
    ear = t.ell(x - 1.6, y + 1.6, 1.6, 2.2)
    cv.part("ear", ear, "skin", edge="dark", noedge=(), lv=np.where(ear, 2, 0))
    t.put(x - 1.6, y + 1.6, sk[1])
    sb = t.poly([(x - 0.4, y - 3.0), (x + 1.2, y - 3.0), (x + 1.0, y + 0.6), (x - 0.4, y + 0.6)])
    cv.part("sideburn", sb, "hair", edge="dark", noedge=("face",), rad=1, soft=0.3)
    # chin strap: from in front of the ear down under the jaw
    t.line(x - 0.5, y + 3.0, x + 2.0, y + 9.0, LYC[1])
    # eye / brow / mouth / cheek
    ex, ey = x + 5, y - 0.5
    if not visor_down:
        if pose == "hit":
            t.line(ex - 1, ey - 1, ex + 1, ey + 0, EYE); t.put(ex - 1, ey + 1, EYE)
        else:
            t.put(ex, ey, EYE); t.put(ex, ey + 1, EYE); t.put(ex + 1, ey + 1, EYE)
            t.put(ex + 1, ey, WHITE if pose != "tell" else EYE)
            t.put(ex - 1, ey + 2, sk[1])
        t.line(ex - 1.5, ey - 2.4, ex + 2, ey - 2.4 - (1 if pose == "hit" else 0), RAMP["hair"][0])
    t.put(x + 3.0, y + 3.0, BLUSH); t.put(x + 4.0, y + 3.0, BLUSH)
    my = y + 5.6
    if pose in ("idle", "tell"):
        # confident grin: upturned line, teeth flash
        t.line(x + 4, my, x + 7, my, MOUTH); t.put(x + 3, my - 1, MOUTH)
        t.put(x + 5, my + 1, TEETH if pose == "tell" else SKIN[1]); t.put(x + 6, my + 1, SKIN[1])
    elif pose == "hit":
        t.line(x + 4, my + 0.5, x + 7, my, MOUTH)
    else:  # shout
        m = t.poly([(x + 3.6, my - 0.8), (x + 7.6, my - 1.0), (x + 7.4, my + 2.4), (x + 4.6, my + 2.2)])
        cv.fill(m, MOUTH, only_alpha=False)
        t.line(x + 4.4, my - 0.8, x + 7.2, my - 0.8, TEETH)
    # aero helmet: a teardrop -- dome over the head, tail tapering back and down
    dome = t.ell(x - 0.4, y - 3.6, 9.2, 8.2) & ~(t.poly([(x + 1, y - 2.6), (x + 12, y - 3.4), (x + 12, y + 12), (x + 1, y + 12)]))
    tail = t.cap(x - 3.0, y - 4.2, x - 15.0, y + 1.6, 6.6, 1.2)
    sidecut = t.poly([(x - 9.5, y - 3.0), (x - 2.0, y - 3.4), (x - 1.5, y + 0.0), (x - 6.0, y + 1.6)])
    hm = (dome | tail | sidecut) & ~t.poly([(x - 20, y + 0.6), (x - 3.5, y + 1.0), (x - 3.5, y + 12), (x - 20, y + 12)])
    cv.part(cap_name, hm, "neon", edge="ink", rad=6, soft=1.2, cuts=(0.25, 0.48, 0.80))
    # black lower shell + pink racing stripe over the crown
    hid = cv.names[cap_name]
    below = np.zeros_like(hm)
    below[:-1] = hm[:-1] & ~hm[1:]                       # lowest helmet row in each column
    shell = (np.roll(below, -1, axis=0) | below) & hm & ~is_ink(cv)
    cv.fill(shell & (cv.own == hid), LYC[2])
    stripe = hm & (t.cap(x + 7.0, y - 7.6, x - 1.0, y - 11.2, 0.8) | t.cap(x - 1.0, y - 11.2, x - 14.5, y - 0.2, 0.8))
    cv.fill(stripe & ~is_ink(cv), PINK[2])
    # visor
    if visor_down:
        v = t.poly([(x + 1.0, y - 3.8), (x + 8.6, y - 4.4), (x + 8.8, y + 1.4), (x + 5.0, y + 1.8), (x + 1.0, y + 0.8)])
        visor_part(t, v)
    else:
        v = t.poly([(x + 2.0, y - 9.6), (x + 7.2, y - 7.4), (x + 8.8, y - 4.2), (x + 2.8, y - 4.4)])
        visor_part(t, v)


def visor_part(t, v, gleam=True):
    cv = t.cv
    ys, xs = np.nonzero(v)
    if not len(xs):
        return
    x0, x1 = xs.min(), xs.max()
    lv = np.zeros(v.shape, int)
    for y_, x_ in zip(ys, xs):
        f = (x_ - x0) / max(1, (x1 - x0))
        lv[y_, x_] = 1 + int(f * 3.2)
    lv = np.clip(lv, 1, 4)
    cv.part("visor", v, "visor", edge="ink", lv=lv)
    if gleam:
        yy = sorted(set(ys))
        if len(yy) >= 3:
            ym = yy[len(yy) // 2 - 1]
            row = sorted(xs[ys == ym])
            if len(row) > 3:
                cv.put(row[1], ym, WHITE)
                cv.put(row[2], ym - 1 if ym - 1 in yy else ym, WHITE)


def zig_panel(t, m, hip, sh, name, frac=0.36, teeth=3, amp=2.2):
    """Colour the hip-side `frac` of a torso mask pink under a zig-zag edge (peaks point up the torso)."""
    cv = t.cv
    vx, vy = sh[0] - hip[0], sh[1] - hip[1]
    L = math.hypot(vx, vy)
    ux, uy = vx / L, vy / L
    # project every pixel onto the hip->shoulder axis (in canvas space)
    H0 = t.p(*hip)
    S0 = t.p(*sh)
    cx_, cy_ = S0[0] - H0[0], S0[1] - H0[1]
    CL = math.hypot(cx_, cy_) or 1
    ax_, ay_ = cx_ / CL, cy_ / CL
    along = (cv.X - H0[0]) * ax_ + (cv.Y - H0[1]) * ay_
    across = -(cv.X - H0[0]) * ay_ + (cv.Y - H0[1]) * ax_
    per = max(3.0, 9.0 * t.s / teeth * 3 / 3)
    tri = np.abs(((across / per) % 1.0) - 0.5) * 2          # 0 at a peak, 1 in a valley
    edge = CL * frac + amp * t.s * (1 - tri) - amp * t.s * 0.5
    own = (cv.own == cv.names[name]) & ~is_ink(cv)
    pink = own & (along < edge)
    cv.fill(pink, PINK[2])
    rim = own & (along < edge) & (along >= edge - 1.0)
    cv.fill(rim, PINK[3])
    deep = own & (along < edge - 1.0) & (along < CL * 0.12)
    cv.fill(deep, PINK[1])


# ==========================================================================
# BATTLE  (84 px: helmet top to the tyre contact)
# ==========================================================================
BW, BH = 80, 88
BATTLE_H = 84


ENT_FIST, ENT_BEND = (24.5, -5.0), 1


def rider_side(cv, t, pose="idle"):
    """Side view facing right, standing on the pedals (battle cell 4 and the entrance)."""
    near_ang = 0.30 if pose != "wheelie" else 0.05
    far_ang = near_ang + math.pi
    hip = (37.5, 50.0)
    sh = (46.5, 29.0)
    hc = None
    if pose == "wheelie":
        hip, sh, hc = (35.5, 52.0), (43.0, 34.5), (47.0, 17.5)
    # far side first: arm, crank, leg
    farP = (BB[0] + 7 * math.cos(far_ang), BB[1] + 7 * math.sin(far_ang))
    if True:
        arm(t, (sh[0] - 1, sh[1] + 1), ik((sh[0] - 1, sh[1] + 1), (HOOD[0] - 1, HOOD[1] + 0.4), 11.6, 11.6, -1),
            (HOOD[0] - 1, HOOD[1] + 0.4), "armF", far=True)
    crank_arm(t, far_ang, "crankF", near=False)
    fk = ik(hip, (farP[0], farP[1] - 2.5), 15.0, 14.6, -1)
    leg(t, hip, fk, (farP[0], farP[1] - 1.2), "legF", far=True)
    shoe_side(t, (farP[0], farP[1] - 0.4), "shoeF", far=True)
    bike_side(t)
    nearP = crank_arm(t, near_ang, "crankN")
    nk = ik(hip, (nearP[0], nearP[1] - 2.5), 15.0, 14.6, -1)
    shoe_side(t, (nearP[0], nearP[1] - 0.4), "shoeN")
    torso_side(t, hip, sh)
    cv.part("hips", t.ell(hip[0] - 0.5, hip[1] + 0.5, 5.4, 4.6), "lycra", edge="ink", rad=4, soft=0.8, cuts=(0.22, 0.5, 0.82))
    leg(t, hip, nk, (nearP[0], nearP[1] - 1.2), "legN")
    head_side_grid(t, (sh[0] + 0.5, sh[1] - (1.5 if pose == "wheelie" else 2.0)), pose="grin" if pose == "wheelie" else "idle", visor_down=(pose == "wheelie"))
    if pose == "wheelie":
        # near arm punched up in a victory salute, far hand on the bars
        # fist up and back over the helmet tail (screen space, undoing the wheelie rotation)
        fist = (sh[0] + ENT_FIST[0], sh[1] + ENT_FIST[1])
        arm(t, (sh[0] + 0.5, sh[1] + 0.5), ik((sh[0] + 0.5, sh[1] + 0.5), fist, 14.2, 14.2, ENT_BEND), fist, "armN",
            hand_r=3.0, sleeve=0.4)
    else:
        arm(t, (sh[0] + 0.5, sh[1] + 0.5), ik((sh[0] + 0.5, sh[1] + 0.5), HOOD, 11.6, 11.6, -1), HOOD, "armN")


def b_side():
    cv = Cv(BW, BH)
    t = Tf(cv, ox=2.0, oy=0.0)
    rider_side(cv, t)
    cv.outline()
    return cv


def crop_prev(cv, box, name, S=14):
    img = cv.image().crop(box)
    preview(img, name, S)


# --------------------------------------------------------------------------
# battle front: standing on the pedals, bike head-on
# --------------------------------------------------------------------------
def shoe_front(t, foot, name, far=False):
    cv = t.cv
    fx, fy = foot
    m = t.ell(fx, fy - 1.8, 3.4, 2.4) | t.ell(fx, fy - 3.4, 2.4, 1.8)
    cv.part(name, m, "sock", edge="ink", rad=2, soft=0.4, bias=-0.15 if far else 0.0, cuts=(0.25, 0.5, 0.82))
    t.line(fx - 1.5, fy - 3.0, fx + 1.5, fy - 3.0, NEON[2])


def leg_front(t, hip, knee, foot, name, far=False):
    """Front-on leg: shorts to mid-thigh, knee, calf, white sock, shoe."""
    cv = t.cv
    b = -0.15 if far else 0.0
    hx, hy = hip
    kx, ky = knee
    fx, fy = foot
    ax, ay = fx, fy - 4.0
    mx, my = hx + (kx - hx) * 0.55, hy + (ky - hy) * 0.55
    skin = t.cap(mx, my, kx, ky, 3.7, 3.0) | t.cap(kx, ky, ax, ay, 3.0, 1.8)
    # calf: the muscle bulges outward, a third of the way down the shin
    side = -1 if kx < 40 else 1
    skin |= t.ell(kx + (ax - kx) * 0.3 + side * 0.8, ky + (ay - ky) * 0.3, 3.0, 4.0)
    cv.part(name + "skin", skin, "skin", edge="dark", rad=2.6, soft=0.7, bias=b, cuts=(0.28, 0.52, 0.86))
    sock = t.cap(ax, ay - 1.0, fx, fy - 2.6, 1.8)
    cv.part(name + "sock", sock, "sock", edge="dark", noedge=(name + "skin",), rad=1.5, soft=0.4, bias=b)
    thigh = t.cap(hx, hy, mx, my, 4.8, 4.2)
    cv.part(name + "short", thigh, "lycra", edge="ink", rad=3, soft=0.8, bias=b, cuts=(0.22, 0.5, 0.82))
    hem = thigh & ~t.cap(hx, hy, mx + (hx - mx) * 0.2, my + (hy - my) * 0.2, 4.3) & ~is_ink(cv)
    cv.fill(hem, NEON[2] if not far else NEON[1])
    # kneecap highlight
    t.put(kx - 1, ky - 0.5, SKIN[4])
    shoe_front(t, foot, name + "shoe", far)


def torso_front(t, cx, top, name="torso", w=14.0, waist=9.0, h=18.0, zig=True, zip_=True):
    cv = t.cv
    m = t.ell(cx, top + 6.5, w, 7.0) | t.poly([(cx - w + 1.5, top + 6), (cx + w - 1.5, top + 6),
                                               (cx + waist, top + h), (cx - waist, top + h)])
    m |= t.ell(cx, top + h - 0.5, waist + 0.5, 2.5)
    cv.part(name, m, "neon", rad=8, soft=1.4, cuts=(0.30, 0.54, 0.86))
    if zig:
        zig_front(t, m, cx, top + h - 4.5, name)
    # collar + zip
    col = t.ell(cx, top + 1.6, 5.0, 2.2)
    cv.part(name + "col", col, "neon", edge="dark", rad=2, soft=0.5, bias=0.1)
    X0, Y0 = t.p(cx, top + 2.5)
    X1, Y1 = t.p(cx, top + h)
    for y in (range(int(round(Y0)), int(round(Y1))) if zip_ else ()):
        if cv.own[y, int(round(X0))] in (cv.names[name], cv.names[name + "col"]) and not is_ink(cv)[y, int(round(X0))]:
            cv.put(X0, y, NEON[1] if cv.get(int(round(X0)), y) not in (PINK[2], PINK[1], PINK[3]) else PINK[0])
    if zip_:
        t.put(cx, top + 3.4, RAMP["metal"][3])
    return m


def zig_front(t, m, cx, y_edge, name, per=5.0, amp=2.0):
    """Pink lower panel under a row of slanted Flatirons peaks."""
    cv = t.cv
    X0, Y0 = t.p(cx, y_edge)
    P = per * t.s
    A = amp * t.s
    f = ((cv.X - X0) / P) % 1.0
    tooth = np.where(f < 0.62, f / 0.62, (1 - f) / 0.38)     # slanted slab: long rise, short drop
    edge = Y0 - A * tooth
    own = (cv.own == cv.names[name]) & ~is_ink(cv)
    pink = own & (cv.Y >= edge)
    lv = cv.col.copy()
    cv.fill(pink, PINK[2])
    cv.fill(own & (cv.Y >= edge) & (cv.Y < edge + 1), PINK[3])
    # keep the torso's shading on the pink: darker on the right flank
    rx = own & pink & (cv.X > X0 + 5 * t.s)
    cv.fill(rx & (cv.Y >= edge + 1), PINK[1])


def arm_front(t, sh, el, hand, name, far=False, sleeve=0.45, hand_r=2.4, thumb=None):
    hm = arm(t, sh, el, hand, name, far=far, sleeve=sleeve, hand_r=hand_r)
    if thumb:
        tx, ty = thumb
        th = t.cap(hand[0], hand[1], tx, ty, 1.1)
        t.cv.part(name + "thumb", th & ~hm, "skin", edge="ink", rad=1, soft=0.3, bias=0.1)
    return hm


def bike_front(t, wobble=0):
    cv = t.cv
    c = 40 + wobble
    # tyre + deep rim seen head-on
    tire = t.ell(c, 73.5, 3.3, 13.5)
    cv.part("ftire", tire, "tire", edge="ink", rad=2, soft=0.4, cuts=(0.25, 0.55, 0.85))
    for y in range(62, 86, 1):
        if (y // 3) % 2 == 0:
            t.put(c - 1, y, RAMP["tire"][3])
    # hub axle + fork blades
    cv.part("axle", t.cap(c - 4.6, 73.0, c + 4.6, 73.0, 0.9), "metal", edge="ink", rad=1, soft=0.3)
    fork = t.cap(c - 3.6, 57.5, c - 4.0, 72.5, 1.2) | t.cap(c + 3.6, 57.5, c + 4.0, 72.5, 1.2)
    fork |= t.ell(c, 57.0, 4.6, 1.8)
    cv.part("fork", fork, "pink", edge="ink", rad=1.5, soft=0.4, cuts=(0.22, 0.52, 0.86))
    ht = t.cap(c, 51.5, c, 56.0, 2.0)
    cv.part("headtube", ht, "pink", edge="ink", rad=2, soft=0.5, cuts=(0.22, 0.52, 0.86))
    # neon decal on the head tube
    t.put(c - 1, 53, NEON[3]); t.put(c, 53, NEON[3]); t.put(c - 1, 54, NEON[2])


def bars_front(t, wobble=0, hood=True):
    cv = t.cv
    c = 40 + wobble
    bars = t.cap(c - 13.5, 50.6, c + 13.5, 50.6, 1.1)
    bars |= t.chain([(c - 13.5, 50.6), (c - 15.2, 53.2), (c - 15.0, 56.4), (c - 13.4, 57.6)], 1.0)
    bars |= t.chain([(c + 13.5, 50.6), (c + 15.2, 53.2), (c + 15.0, 56.4), (c + 13.4, 57.6)], 1.0)
    bars |= t.cap(c, 50.0, c, 52.0, 1.8)          # stem cap
    cv.part("bars", bars, "tire", edge="ink", rad=1, soft=0.3, cuts=(0.2, 0.5, 0.8))
    # bike computer on the stem: tiny glowing screen
    comp = t.rect(c - 2, 47.5, c + 2, 49.5)
    cv.part("computer", comp, "tire", edge="ink", lv=np.where(comp, 2, 0))
    t.put(c - 1, 48.5, NEON[3]); t.put(c, 48.5, NEON[3]); t.put(c + 1, 48.5, NEON[2])
    if hood:
        for s in (-1, 1):
            h = t.ell(c + s * 12.4, 49.4, 1.7, 1.9)
            cv.part("hood%d" % s, h, "lycra", edge="ink", rad=1, soft=0.3, bias=0.1)


def crank_front(t, foot, name):
    cv = t.cv
    fx, fy = foot
    arm_ = t.cap(40, 75.0, fx, fy - 0.5, 1.0)
    cv.part(name, arm_, "metal", edge="ink", rad=1, soft=0.3, cuts=(0.2, 0.45, 0.8))


def b_front(pose):
    cv = Cv(BW, BH)
    t = Tf(cv)
    rider_front(cv, t, pose)
    cv.outline()
    if pose == "tell":
        # visor gleam sparks + speed ticks
        for (x, y) in [(18, 13), (61, 15)]:
            cv.puts([(x, y - 2), (x, y - 1), (x, y + 1), (x, y + 2), (x - 2, y), (x - 1, y), (x + 1, y), (x + 2, y)], SPARK2)
            cv.put(x, y, WHITE)
    if pose == "hit":
        sx, sy = 58, 6
        cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx + 1, sy + 1), (sx - 1, sy + 2), (sx, sy + 2),
                 (sx + 1, sy + 2), (sx, sy + 3)], SWEAT)
        cv.put(sx - 1, sy + 1, SWEAT_HI)
    return cv


def rider_front(cv, t, pose, visor=None, face=None, s_head=True):
    """The whole front-on rider + bike in design space (centre x 40, ground 87)."""
    wob = 0
    hipL, hipR = (35.5, 50.0), (44.5, 50.0)
    footL, footR = (31.5, 81.0), (48.5, 70.0)
    kneeL, kneeR = (31.0, 64.5), (50.5, 58.5)
    shL, shR = (27.5, 32.0), (52.5, 32.0)
    handL, handR = (27.6, 50.6), (52.4, 50.6)
    elL, elR = (21.5, 42.0), (58.5, 42.0)
    neck = (40, 28)
    hx = 0
    if pose == "tell":                  # aero tuck: elbows in, hands on the tops, head down
        elL, elR = (25.5, 43.0), (54.5, 43.0)
        handL, handR = (31.5, 50.6), (48.5, 50.6)
    if pose == "hit":
        footL, kneeL = (22.0, 76.0), (27.0, 63.0)      # right foot unclipped, flailing out
        elL, handL = (20.0, 38.0), (17.5, 30.0)
        hx = 2
        neck = (41, 28)
    # hips + legs (behind the bars and the wheel)
    cv.part("hips", t.ell(40, 50.5, 8.5, 4.6), "lycra", edge="ink", rad=4, soft=0.8, cuts=(0.22, 0.5, 0.82))
    crank_front(t, footR, "crankR")
    leg_front(t, hipR, kneeR, footR, "legR", far=False)
    if pose != "hit":
        crank_front(t, footL, "crankL")
    leg_front(t, hipL, kneeL, footL, "legL")
    torso_front(t, 40, 29.0)
    bike_front(t, wob)
    bars_front(t, wob)
    # arms
    arm_front(t, shL, elL, handL, "armL", hand_r=2.5)
    if pose == "talk":
        elR2, handR2 = (60.5, 37.0), (60.0, 26.5)
        arm_front(t, shR, elR2, handR2, "armR", hand_r=2.6, thumb=(60.0, 21.8))
    else:
        arm_front(t, shR, elR, handR, "armR", hand_r=2.5)
    vis = visor or ("down" if pose == "tell" else "up")
    fc = face or {"idle": "grin", "talk": "talk", "tell": "grin", "hit": "hit"}[pose]
    head_front_grid(t, (neck[0], neck[1]), fc, vis)


HEAD_BACK = _rows3([
    ("........KKK", "KKK", "KKK........"),
    ("......KKeed", "PPP", "dccKK......"),
    (".....Keeddd", "PPP", "dccbbK....."),
    ("....Keddddd", "PPP", "dcccbbK...."),
    ("...Kedddddd", "PPP", "dccccbbK..."),
    ("...Keddddcc", "PPP", "cccccbbK..."),
    ("..Keddddccc", "PPP", "cccccbbbK.."),
    ("..Kdddccccc", "PPP", "cccccbbbK.."),
    (".Kddccccccc", "PPP", "ccccbbbbbK."),
    (".Kdcccccccc", "PPP", "cccbbbbbbK."),
    (".Kccccccccc", "PPP", "ccbbbbbbbK."),
    (".Kbcccccccc", "PPP", "cbbbbbbbaK."),
    ("..Kbbcccccc", "PPP", "bbbbbbbaK.."),
    ("..Kmmbbbccc", "PPP", "bbbbbmmmK.."),
    ("..K2Kmmbbcc", "RPR", "ccbbmmK2K.."),
    ("..K23KKmbbb", "RRR", "bbbmKK32K.."),
    ("...K2hHKKmb", "bRb", "bmKKHh2K..."),
    ("....KhHHHKK", "KbK", "KKHHHhK...."),
    (".....KHhH33", "333", "33HhHK....."),
    ("......KH333", "333", "333HK......"),
    (".......K233", "333", "332K......."),
    (".......K233", "333", "332K......."),
    ("........K23", "333", "32K........"),
    ("........K23", "322", "32K........"),
    ("........K23", "322", "22K........"),
])


def head_back_grid(t, neck):
    X, Y = t.p(*neck)
    return stamp(t.cv, HEAD_BACK, int(round(X)) - 12, int(round(Y)) - 24, "head")


DIGIT_1 = [".K.", "KK.", ".K.", ".K.", "KKK"]


def bib(cv, x0, y0, w=8, h=7):
    """White race number pinned to the jersey: #1, of course."""
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            edge = y in (y0, y0 + h - 1) or x in (x0, x0 + w - 1)
            cv.put(x, y, RAMP["sock"][1] if edge else RAMP["sock"][3])
    for j, row in enumerate(DIGIT_1):
        for i, ch in enumerate(row):
            if ch == "K":
                cv.put(x0 + w // 2 - 1 + i, y0 + 1 + j, INK)
    cv.put(x0 + 1, y0 + 1, PINK[2]); cv.put(x0 + w - 2, y0 + 1, PINK[2])     # safety pins


def b_back():
    cv = Cv(BW, BH)
    t = Tf(cv)
    c = 40
    # cockpit (far): bar ends peek out past the elbows
    bars_front(t, hood=True)
    shL, shR = (27.5, 32.0), (52.5, 32.0)
    arm(t, shL, (21.5, 42.0), (27.6, 50.6), "armL", hand_r=2.5)
    arm(t, shR, (58.5, 42.0), (52.4, 50.6), "armR", hand_r=2.5)
    sad = t.poly([(c - 3, 52.5), (c + 3, 52.5), (c + 2, 57), (c - 2, 57)])
    cv.part("saddle", sad, "lycra", edge="ink", rad=1.5, soft=0.4, bias=0.1)
    cv.part("hips", t.ell(40, 50.0, 9.0, 5.0), "lycra", edge="ink", rad=4, soft=0.8, cuts=(0.22, 0.5, 0.82))
    m = torso_front(t, 40, 29.0, zip_=False)
    # back pockets (three seams) + the #1 bib
    for x in (34, 40, 46):
        for y in range(43, 47):
            t.put(x, y, PINK[0])
    bib(cv, 36, 34)
    # legs: his right (viewer's right) pushes down, the left pedal is up
    crank_front(t, (48.5, 81.0), "crankR")
    leg_front(t, (44.5, 50.0), (49.0, 64.5), (48.5, 81.0), "legR")
    crank_front(t, (31.5, 70.0), "crankL")
    leg_front(t, (35.5, 50.0), (29.5, 58.5), (31.5, 70.0), "legL")
    # rear wheel, nearest to us
    tire = t.ell(c, 73.5, 3.3, 13.5)
    cv.part("rtire", tire, "tire", edge="ink", rad=2, soft=0.4, cuts=(0.25, 0.55, 0.85))
    for y in range(62, 86):
        if (y // 3) % 2 == 0:
            t.put(c - 1, y, RAMP["tire"][3])
    st = t.cap(c - 3.8, 60.0, c - 4.2, 72.5, 1.0) | t.cap(c + 3.8, 60.0, c + 4.2, 72.5, 1.0)
    cv.part("stays", st, "pink", edge="ink", rad=1.5, soft=0.4)
    cv.part("axle", t.cap(c - 4.8, 73.0, c + 4.8, 73.0, 0.9), "metal", edge="ink", rad=1, soft=0.3)
    # red tail light on the seatpost
    tl = t.rect(c - 1, 58, c + 1, 59)
    cv.part("taillight", tl, "pink", edge="ink", lv=np.where(tl, 3, 0))
    head_back_grid(t, (40, 28))
    cv.outline()
    return cv


# ==========================================================================
# WORLD  (54 px: helmet top to soles; he stands in front of the bike)
# ==========================================================================
WW, WH = 56, 57
WORLD_H = 54
WT = WH - WORLD_H          # helmet top row
WCX = 28

W_HEAD_FRONT = [
    "....KKKKKKK....",
    "..KKeedPdccKK..",
    ".KeedddPdcccbK.",
    ".KKKKKKKKKKKKK.",
    "KKvwxxyWyxxwvKK",
    "KdKKKKKKKKKKKbK",
    "KcmmmmmmmmmmmbK",
    "Kbm455555554mbK",
    "Kbm4HH555HH4mbK",
    "Kbm45E555E54mbK",
    ".Km4B45554B4mK.",
    ".Km4HhhGhhH4mK.",
    "..Km44OOO44mK..",
    "...Km34443mK...",
    "....KK333KK....",
    ".....K232K.....",
]
W_FACE = {
    "smile": {},
    "grin": _overlay([(12, 4, "4TTT4")]),
    "talk": _overlay([(12, 4, "OTTTO"), (13, 5, "3OtO3")]),
    "hit": _overlay([(9, 3, "4EE555EE4"), (8, 4, "H"), (8, 10, "H"), (12, 4, "OTTTO")]),
    "blink": _overlay([(9, 5, "2"), (9, 9, "2"), (8, 5, "H"), (8, 9, "H")]),
    "look": _overlay([(9, 5, "5E"), (9, 9, "5E")]),
}
W_VISOR_DOWN = _overlay([(3, 1, "KeddddPdcccbK"), (4, 0, "KeddddcPccccbbK"), (5, 0, "KdcccccPcccbbbK"),
                         (8, 2, "KvwWxyyxxwvK"), (9, 2, "KuvwxyWxwvuK"), (10, 3, "KKKK555KKKK")])
W_HEAD_SIDE = [
    "........KKKKK.....",
    "......KKPPPPPK....",
    "....KKPPddddedK...",
    "...KPPddddddddcK..",
    "..KPdddcccccccccK.",
    ".KPdcccccbbbbbbbK.",
    "KPcbbbbbbbmmmmmmK.",
    "KabbaKKbK345HH4K..",
    ".KaaK.KbK3445E44K.",
    "..KK...KK23444445K",
    "........K2HhhhH4K.",
    "........K23OTT4K..",
    "........K23344K...",
    ".........K233K....",
    "........K122K.....",
    ".......K1122K.....",
]
W_SIDE_VISOR_UP = _overlay([(1, 12, "KKKK"), (2, 12, "KvwxK"), (3, 13, "KxyK"), (4, 14, "KK")])
W_HEAD_BACK = [
    "....KKKKKKK....",
    "..KKeedPdccKK..",
    ".KeedddPdcccbK.",
    ".KeddddPccccbK.",
    "KeddcccPccccbbK",
    "KdcccccPcccbbbK",
    "KcccccbPbbbbbaK",
    "KbbbbbbPbbbbaaK",
    "KmbbbbbRbbbbamK",
    "K2mmbbbRbbbmm2K",
    ".K2KmmbbbmmK2K.",
    "..KhHKKaKKHhK..",
    "...KHH333HHK...",
    "....K23332K....",
    ".....K232K.....",
    ".....K232K.....",
]


def w_head(cv, x, y, kind="front", face="smile", visor="up", extra=None):
    """Stamp a world head with its neck base at (x, y)."""
    if kind == "front":
        ed = dict(W_FACE.get(face, {}))
        if visor == "down":
            ed.update(W_VISOR_DOWN)
        if extra:
            ed.update(extra)
        return stamp(cv, grid_sub(W_HEAD_FRONT, ed), x - 7, y - 15, "head")
    if kind == "side":
        ed = dict(W_SIDE_VISOR_UP)
        return stamp(cv, grid_sub(W_HEAD_SIDE, ed), x - 10, y - 15, "head")
    return stamp(cv, W_HEAD_BACK, x - 7, y - 15, "head")


def w_bike(cv, flip=False):
    """The bike parked side-on behind him, drawn small (wheel radius ~8.7)."""
    t = Tf(cv, ox=WCX, oy=WH - 1, s=0.62, ax=38.0, ay=87.0, flip=flip)
    bike_side(t, crank=True, bottle=True)
    crank_arm(t, 1.9, "wcrank")
    return t


def w_leg(cv, hip, foot, name, far=False, side=False):
    b = -0.15 if far else 0.0
    hx, hy = hip
    fx, fy = foot
    mx, my = hx + (fx - hx) * 0.34, hy + (fy - hy) * 0.34
    kx, ky = hx + (fx - hx) * 0.50, hy + (fy - hy) * 0.50
    ax, ay = fx, fy - 3.0
    skin = cv.capsule(mx, my, kx, ky, 2.5, 2.2) | cv.capsule(kx, ky, ax, ay, 2.1, 1.4)
    skin |= cv.ell(kx + (ax - kx) * 0.35 + (0.6 if side else 0), ky + (ay - ky) * 0.35, 2.3, 2.8)
    cv.part(name + "skin", skin, "skin", edge="dark", rad=2, soft=0.5, bias=b, cuts=(0.28, 0.52, 0.86))
    sock = cv.capsule(ax, ay - 0.5, ax, ay + 1.0, 1.5)
    cv.part(name + "sock", sock, "sock", edge="dark", noedge=(name + "skin",), lv=np.where(sock, 3, 0))
    thigh = cv.capsule(hx, hy, mx, my, 3.0, 2.6)
    cv.part(name + "short", thigh, "lycra", edge="ink", rad=2.5, soft=0.6, bias=b, cuts=(0.22, 0.5, 0.82))
    X, Y = int(round(mx)), int(round(my))
    for dx in (-2, -1, 0, 1, 2):
        if cv.own[Y, X + dx] == cv.names[name + "short"] and not is_ink(cv)[Y, X + dx]:
            cv.put(X + dx, Y, NEON[2])
    if side:
        sh = cv.ell(fx + 1.2, fy - 1.2, 3.4, 1.7) | cv.ell(fx - 0.6, fy - 2.0, 1.9, 1.6)
    else:
        sh = cv.ell(fx, fy - 1.3, 2.4, 1.8) | cv.ell(fx, fy - 2.6, 1.8, 1.3)
    sh &= cv.half(y=WH - 1, below=False)
    cv.part(name + "shoe", sh, "sock", edge="ink", rad=1.5, soft=0.3, bias=b, cuts=(0.25, 0.5, 0.82))
    cv.put(fx, fy - 2.6, NEON[2])


def w_arm(cv, sh, el, hand, name, far=False, thumb=None, up=False):
    b = -0.15 if far else 0.0
    sx, sy = sh
    ex, ey = el
    mx, my = sx + (ex - sx) * 0.55, sy + (ey - sy) * 0.55
    skin = cv.capsule(mx, my, ex, ey, 1.6) | cv.capsule(ex, ey, hand[0], hand[1], 1.6, 1.3)
    cv.part(name + "skin", skin, "skin", edge="dark", rad=1.5, soft=0.4, bias=b, cuts=(0.28, 0.52, 0.86))
    slv = cv.capsule(sx, sy, mx, my, 2.4, 2.1)
    cv.part(name + "sleeve", slv, "pink", edge="dark", rad=2, soft=0.5, bias=b, cuts=(0.25, 0.5, 0.84))
    hm = cv.ell(hand[0], hand[1], 1.8, 1.8)
    cv.part(name + "hand", hm, "glove", edge="ink", rad=1.5, soft=0.3, bias=b + 0.05)
    cv.put(hand[0], hand[1] + (-1 if up else 1), SKIN[2])
    if thumb:
        th = cv.capsule(hand[0], hand[1], thumb[0], thumb[1], 0.8)
        cv.part(name + "thumb", th & ~hm, "skin", edge="ink", rad=1, soft=0.3, bias=0.1)


def w_torso(cv, cx, top, name="torso", back=False):
    m = cv.ell(cx, top + 4.0, 8.4, 4.4) | cv.poly([(cx - 7.6, top + 4), (cx + 7.6, top + 4), (cx + 5.6, top + 13.5),
                                                  (cx - 5.6, top + 13.5)])
    cv.part(name, m, "neon", rad=6, soft=1.2, cuts=(0.30, 0.54, 0.86))
    t = Tf(cv)
    zig_front(t, m, cx, top + 11.0, name, per=4.0, amp=1.6)
    if not back:
        cv.vline(cx, top + 2, top + 10, NEON[1])
        cv.put(cx, top + 2, RAMP["metal"][3])
        cv.hline(cx - 2, cx + 2, top, NEON[1])
    else:
        for y in range(top + 3, top + 8):
            for x in range(cx - 3, cx + 3):
                edge = y in (top + 3, top + 7) or x in (cx - 3, cx + 2)
                cv.put(x, y, RAMP["sock"][1] if edge else RAMP["sock"][3])
        cv.vline(cx, top + 4, top + 6, INK); cv.put(cx - 1, top + 4, INK)
    return m


def w_front(pose, face=None, arm_pose=None):
    cv = Cv(WW, WH)
    w_bike(cv)
    c, T = WCX, WT
    neck = (c, T + 15)
    hipL, hipR = (c - 3.5, T + 31.5), (c + 3.5, T + 31.5)
    footL, footR = (c - 4.0, WH - 1), (c + 4.0, WH - 1)
    cv.part("hips", cv.ell(c, T + 31, 6.6, 3.2), "lycra", edge="ink", rad=3, soft=0.6, cuts=(0.22, 0.5, 0.82))
    w_leg(cv, hipL, footL, "legL")
    w_leg(cv, hipR, footR, "legR")
    w_torso(cv, c, T + 16)
    shL, shR = (c - 7.5, T + 19.5), (c + 7.5, T + 19.5)
    ap = arm_pose or pose
    # viewer-right hand rests on the bar hood of the parked bike
    hoodR = (c + 13.5, T + 31.0)
    if ap == "hit":
        w_arm(cv, shR, (c + 11.5, T + 22.0), (c + 12.0, T + 16.5), "armR", up=True)
    else:
        w_arm(cv, shR, (c + 11.5, T + 25.0), hoodR, "armR")
    if ap == "idle":
        w_arm(cv, shL, (c - 11.0, T + 24.5), (c - 7.5, T + 29.5), "armL")          # hand on hip
    elif ap == "talk":
        w_arm(cv, shL, (c - 12.5, T + 21.5), (c - 12.0, T + 15.5), "armL", thumb=(c - 12.0, T + 12.5), up=True)
    elif ap == "tell":
        w_arm(cv, shL, (c - 12.5, T + 17.5), (c - 11.5, T + 11.0), "armL", up=True)   # fist pump
    elif ap == "hit":
        w_arm(cv, shL, (c - 11.5, T + 22.0), (c - 12.0, T + 16.5), "armL", up=True)
    elif ap == "watch":      # idle pose 1: checks the bike computer on his wrist
        w_arm(cv, shL, (c - 10.5, T + 26.0), (c - 4.0, T + 24.0), "armL")
        cv.puts([(c - 5, T + 23), (c - 4, T + 23)], NEON[3])
    elif ap == "bottle":     # idle pose 2: a squirt from the bidon
        w_arm(cv, shL, (c - 11.0, T + 21.0), (c - 6.0, T + 14.5), "armL", up=True)
        b = cv.capsule(c - 5.0, T + 13.0, c - 3.0, T + 9.0, 1.3)
        cv.part("bottle", b, "bottle", edge="dark", rad=1.2, soft=0.3)
        cv.puts([(c - 2, T + 7), (c - 1, T + 6)], SWEAT)
    fc = face or {"idle": "smile", "talk": "talk", "tell": "grin", "hit": "hit"}.get(pose, "smile")
    w_head(cv, neck[0], neck[1], "front", fc, "down" if pose == "tell" else "up",
           extra=_overlay([(12, 4, "4OOO4")]) if ap == "bottle" else None)
    cv.outline()
    if pose == "hit":
        cv.puts([(c + 9, T + 1), (c + 8, T + 2), (c + 9, T + 2), (c + 10, T + 2), (c + 9, T + 3)], SWEAT)
    if pose == "tell":
        x, y = c - 10, T + 6
        cv.puts([(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)], SPARK2); cv.put(x, y, WHITE)
    return cv


def w_side():
    cv = Cv(WW, WH)
    w_bike(cv)
    c, T = WCX - 2, WT
    hip = (c, T + 31.0)
    w_arm(cv, (c + 1, T + 19.5), (c + 3.0, T + 25.0), (c + 1.5, T + 29.5), "armF", far=True)
    w_leg(cv, (hip[0] - 0.5, hip[1]), (c - 1.5, WH - 1), "legF", far=True, side=True)
    w_leg(cv, (hip[0] + 0.5, hip[1]), (c + 2.5, WH - 1), "legN", side=True)
    m = cv.capsule(c, T + 29, c + 1, T + 20, 4.4, 4.8) | cv.ell(c + 0.5, T + 21.5, 5.0, 3.8)
    cv.part("torso", m, "neon", rad=5, soft=1.0, cuts=(0.30, 0.54, 0.86))
    t = Tf(cv)
    zig_front(t, m, c, T + 26.5, "torso", per=4.0, amp=1.6)
    cv.part("hips", cv.ell(c + 0.3, T + 30.5, 4.6, 2.8), "lycra", edge="ink", rad=3, soft=0.6, cuts=(0.22, 0.5, 0.82))
    w_arm(cv, (c + 1, T + 19.5), (c + 6.0, T + 25.0), (WCX + 13.5, T + 31.0), "armN")
    w_head(cv, c + 1, T + 15, "side")
    cv.outline()
    return cv


def w_back():
    cv = Cv(WW, WH)
    w_bike(cv)
    c, T = WCX, WT
    cv.part("hips", cv.ell(c, T + 31, 6.6, 3.2), "lycra", edge="ink", rad=3, soft=0.6, cuts=(0.22, 0.5, 0.82))
    w_leg(cv, (c - 3.5, T + 31.5), (c - 4.0, WH - 1), "legL")
    w_leg(cv, (c + 3.5, T + 31.5), (c + 4.0, WH - 1), "legR")
    w_torso(cv, c, T + 16, back=True)
    # his left hand (viewer's left now) on the bars, right hand on the hip
    w_arm(cv, (c - 7.5, T + 19.5), (c - 11.5, T + 25.0), (c - 13.5, T + 31.0), "armL")
    w_arm(cv, (c + 7.5, T + 19.5), (c + 11.0, T + 24.5), (c + 7.5, T + 29.5), "armR")
    w_head(cv, c, T + 15, "back")
    cv.outline()
    return cv


# ==========================================================================
# ENTRANCE (cell 12): a wheelie with a victory fist, visor snapped down
# ==========================================================================
EW, EH = 112, 104


def entrance():
    cv = Cv(EW, EH)
    # rotate the whole side-view rider+bike about the rear tyre contact (20, 87)
    t = Tf(cv, ox=46.0, oy=EH - 1, s=1.0, ax=20.0, ay=87.0, ang=-0.36)
    rider_side(cv, t, pose="wheelie")
    cv.outline()
    # speed streaks behind him (after the outline pass so they stay coloured)
    for k, (y, x0, x1, col) in enumerate([(30, 4, 24, PINK[2]), (44, 0, 18, NEON[2]), (58, 6, 26, PINK[3]),
                                         (72, 0, 16, NEON[3]), (86, 8, 24, PINK[2])]):
        for x in range(x0, x1 + 1):
            if not cv.alpha[y, x]:
                cv.put(x, y, col)
    # visor glint
    ys, xs = np.nonzero(cv.own == cv.names["head"])
    gx, gy = int(xs.max()) + 2, int(ys.min()) + 12
    cv.puts([(gx, gy - 2), (gx, gy - 1), (gx, gy + 1), (gx, gy + 2), (gx - 2, gy), (gx - 1, gy), (gx + 1, gy), (gx + 2, gy)], SPARK2)
    cv.put(gx, gy, WHITE)
    # dust puff under the rear tyre + sparkle on the visor
    for (x, y) in [(36, 101), (38, 100), (40, 102), (33, 102), (42, 101), (31, 100), (29, 102)]:
        cv.put(x, y, (176, 168, 150))
    cv.puts([(35, 99), (41, 99), (30, 99)], (220, 212, 192))
    return cv


# ==========================================================================
# PACELINE prop (battle only): five Flatirons riders in an echelon behind him
# ==========================================================================
SKIN_ALT = [
    [(70, 34, 24), (112, 64, 40), (150, 92, 58), (180, 122, 80), (206, 156, 110)],
    [(92, 46, 36), (176, 104, 76), (222, 150, 116), (240, 184, 150), (252, 214, 186)],
    [(56, 28, 20), (88, 50, 32), (120, 72, 46), (150, 98, 64), (182, 130, 92)],
    [(84, 40, 30), (150, 86, 56), (194, 124, 82), (222, 160, 112), (242, 196, 150)],
    [(92, 46, 36), (170, 98, 70), (214, 140, 106), (236, 178, 142), (250, 208, 178)],
]
PW_, PH_ = 172, 124
PACE = [(19, -7), (37, -14), (55, -21), (73, -28), (91, -35)]


def paceline():
    """Riders are the same drawing as Lance (visors down, no moustache), darkened with distance.
    Paste it so its foot point sits on Lance's battle foot point; draw it BEHIND his cell."""
    out = Image.new("RGBA", (PW_, PH_), (0, 0, 0, 0))
    bg = np.array((30, 30, 46), float)
    for k in reversed(range(len(PACE))):
        dx, dy = PACE[k]
        cv = Cv(BW, BH)
        t = Tf(cv)
        global LEGEND
        saved = dict(LEGEND)
        sk = SKIN_ALT[k]
        for i, ch in enumerate("12345"):
            LEGEND[ch] = sk[i]
        LEGEND["H"] = sk[1]; LEGEND["h"] = sk[2]; LEGEND["G"] = sk[1]
        RAMP["skin"], keep = sk, RAMP["skin"]
        try:
            rider_front(cv, t, "idle" if k % 2 else "tell", visor="down", face="smile")
        finally:
            LEGEND.clear(); LEGEND.update(saved)
            RAMP["skin"] = keep
        cv.outline()
        img = np.array(cv.image()).astype(float)
        f = 0.22 + 0.09 * k
        img[..., :3] = img[..., :3] * (1 - f) + bg * f
        im = Image.fromarray(img.clip(0, 255).astype(np.uint8), "RGBA")
        out.alpha_composite(im, (dx, PH_ - BH + dy))
    return out


# ==========================================================================
# PORTRAITS 64x64 (0 neutral, 1 warm, 2 concern, 3 surprised) + talking mouths
# ==========================================================================
PW = PH = 64
IRIS = (60, 96, 70)          # hazel-green eyes
SCLERA = (244, 240, 232)


def p_eye(cv, ex, ey, expr, side, blink=False):
    """ex = left column of a 4x4 eye box."""
    sk = SKIN
    if blink or expr == "warm":
        # happy closed arcs
        cv.puts([(ex, ey + 2), (ex + 1, ey + 1), (ex + 2, ey + 1), (ex + 3, ey + 2)], EYE)
        if not blink:
            cv.puts([(ex - 1, ey + 3), (ex + 4, ey + 3)], sk[1])
        return
    h = 5 if expr == "surprised" else 4
    y0 = ey - (1 if expr == "surprised" else 0)
    for y in range(y0, y0 + h):
        for x in range(ex, ex + 4):
            cv.put(x, y, SCLERA)
    look = -1 if expr == "concern" else 0
    ix = ex + 1 + look * side * 0 + (1 if (side > 0 and expr != "concern") else 0)
    if expr == "concern":
        ix = ex + (0 if side < 0 else 0)
    if expr == "surprised":
        for y in range(y0, y0 + h):
            for x in range(ex, ex + 4):
                cv.put(x, y, SCLERA)
        cv.put(ex + 1, y0 + 2, EYE); cv.put(ex + 2, y0 + 2, EYE); cv.put(ex + 1, y0 + 3, EYE); cv.put(ex + 2, y0 + 3, IRIS)
        cv.hline(ex - 1, ex + 4, y0 - 1, EYE)
        cv.put(ex - 1, y0, EYE); cv.put(ex + 4, y0, EYE); cv.hline(ex, ex + 3, y0 + h, sk[1])
        return
    for y in range(y0 + 1, y0 + h):
        cv.put(ix, y, IRIS); cv.put(ix + 1, y, EYE if y > y0 + 1 else IRIS)
    cv.put(ix, y0 + 1, WHITE)
    cv.hline(ex - 1, ex + 4, y0 - 1, EYE)                      # upper lid
    if expr != "surprised":
        cv.hline(ex, ex + 3, y0 + h, sk[1])
    cv.put(ex - 1, y0, EYE); cv.put(ex + 4, y0, sk[0])


def p_brows(cv, by, expr):
    hr = RAMP["hair"]
    for side in (-1, 1):
        base = 32 + side * 8
        pts = []
        for k in range(-4, 4):
            x = base + k * side * -1 if side < 0 else base + k
            # inner end is k toward centre
            inner = (x - 32) * side < 8
            dy = 0
            if expr == "concern":
                dy = -1 if inner else 1
                dy = -(4 - abs(x - 32) // 3) // 2 if inner else 0
            elif expr == "surprised":
                dy = -2
            elif expr == "warm":
                dy = -1 if abs(x - base) < 2 else 0
            pts.append((x, by + dy))
        for (x, y) in pts:
            cv.put(x, y, hr[1]); cv.put(x, y + 1, hr[0])
        cv.put(base - 4 * side * -1 if False else base + 4 * side, by + (1 if expr != "surprised" else -1), hr[1])


def p_mouth(cv, my, expr, talk=False):
    sk = SKIN
    c = 32
    if expr == "warm":
        if talk:
            cv.hline(c - 6, c + 6, my, MOUTH)
            for y in range(my + 1, my + 5):
                w = 6 - max(0, y - my - 2) * 2
                cv.hline(c - w, c + w, y, MOUTH)
            cv.hline(c - 5, c + 5, my + 1, TEETH)
            cv.hline(c - 2, c + 2, my + 4, TONGUE); cv.hline(c - 3, c + 3, my + 3, TONGUE)
        else:
            cv.hline(c - 6, c + 6, my, MOUTH)
            cv.hline(c - 5, c + 5, my + 1, TEETH)
            cv.hline(c - 4, c + 4, my + 2, TEETH)
            cv.hline(c - 3, c + 3, my + 3, MOUTH)
            cv.put(c - 6, my + 1, MOUTH); cv.put(c + 6, my + 1, MOUTH)
            cv.put(c - 5, my + 2, MOUTH); cv.put(c + 5, my + 2, MOUTH); cv.put(c - 4, my + 3, MOUTH); cv.put(c + 4, my + 3, MOUTH)
        cv.hline(c - 3, c + 3, my + 5 + (1 if talk else 0), sk[1])
    elif expr == "neutral":
        if talk:
            cv.hline(c - 4, c + 4, my, MOUTH)
            cv.hline(c - 3, c + 3, my + 1, TEETH)
            cv.hline(c - 3, c + 3, my + 2, MOUTH)
            cv.hline(c - 2, c + 2, my + 3, MOUTH); cv.hline(c - 1, c + 1, my + 3, TONGUE)
            cv.put(c - 5, my - 1, MOUTH); cv.put(c + 5, my - 1, MOUTH)
        else:
            # confident closed smile, one corner higher
            cv.hline(c - 4, c + 4, my, MOUTH)
            cv.put(c - 5, my - 1, MOUTH); cv.put(c + 5, my - 1, MOUTH); cv.put(c + 6, my - 2, MOUTH)
            cv.hline(c - 2, c + 2, my + 1, TEETH)
        cv.hline(c - 2, c + 2, my + 4, sk[1])
    elif expr == "concern":
        if talk:
            cv.hline(c - 3, c + 3, my, MOUTH)
            cv.hline(c - 3, c + 3, my + 1, MOUTH); cv.hline(c - 2, c + 2, my + 1, TEETH)
            cv.hline(c - 2, c + 2, my + 2, MOUTH)
        else:
            cv.hline(c - 3, c + 3, my + 1, MOUTH)
            cv.put(c - 4, my + 2, MOUTH); cv.put(c + 4, my + 2, MOUTH); cv.hline(c - 2, c + 2, my, MOUTH)
        cv.hline(c - 1, c + 1, my + 4, sk[1])
    elif expr == "surprised":
        h = 5 if talk else 4
        for y in range(my, my + h):
            w = 2 if y in (my, my + h - 1) else 3
            cv.hline(c - w, c + w, y, MOUTH)
        cv.hline(c - 1, c + 1, my + h - 2, TONGUE)
        cv.hline(c - 2, c + 2, my, TEETH) if talk else None


def portrait(expr, talk=False, blink=False):
    cv = Cv(PW, PH, open_bottom=True)
    c = 32
    sk, hr = SKIN, RAMP["hair"]
    lift = -2 if expr == "surprised" else 0
    # ---- shoulders: neon jersey, pink raglan sleeves, zip ----
    sh = cv.ell(c, 77, 35, 25) & cv.half(y=47)
    cv.part("shoulders", sh, "neon", rad=14, soft=2.0, cuts=(0.30, 0.52, 0.84))
    for s in (-1, 1):
        sl = sh & cv.ell(c + s * 31, 66, 10, 14)
        cv.fill(sl & ~is_ink(cv), PINK[2] if s < 0 else PINK[1])
        cv.line(c + s * 17, 55, c + s * 21, 63, NEON[1])
    # club crest on the chest: three slanted pink Flatirons slabs
    for k, x0 in enumerate((40, 45, 50)):
        for j in range(5):
            cv.hline(x0 + j // 2, x0 + 3 - (j == 0), 63 - j, PINK[2] if j else PINK[3]) if 63 - j < PH else None
    neck = cv.rect(c - 7, 44, c + 7, 57)
    cv.part("neck", neck, "skin", edge="dark", lv=np.where(neck, 2, 0) + (neck & (cv.X > c + 3)) * -1 + (neck & (cv.Y < 49)) * -1)
    col = cv.ell(c, 56.5, 13.0, 4.6) & ~cv.ell(c, 54.0, 9.0, 3.8)
    cv.part("collar", col, "neon", edge="dark", rad=3, soft=0.8, bias=0.08)
    mt = RAMP["metal"]
    cv.vline(c, 58, 63, NEON[0]); cv.put(c, 58, mt[3]); cv.put(c, 59, mt[2]); cv.put(c + 1, 59, mt[1])
    # ---- face: square jaw ----
    face = cv.ell(c, 33, 15.0, 14.0) | cv.poly([(17, 33), (47, 33), (45.5, 44), (39, 50.5), (25, 50.5), (18.5, 44)])
    d = ndi.distance_transform_edt(np.pad(face, 2))[2:-2, 2:-2]
    lv = np.where(face, 2, 0)
    lv = np.where(face & (cv.X < c + 1) & (cv.Y < 45) & (d > 2.5), 3, lv)
    lv = np.where(face & (cv.X < c - 4) & (cv.Y > 27) & (cv.Y < 38) & (d > 3.5), 4, lv)
    lv = np.where(face & (((d <= 2.6) & (cv.X > c + 3)) | (cv.Y >= 48) | ((d <= 1.5) & (cv.Y > 40))), 1, lv)
    cv.part("face", face, "skin", lv=lv)
    # cheeks
    for s in (-1, 1):
        bx = c + s * 10
        for y in (39, 40):
            for x in range(bx - 2, bx + 3):
                if cv.own[y, x] == cv.names["face"]:
                    cv.put(x, y, mix(cv.get(x, y), BLUSH, 0.45 if expr != "warm" else 0.6))
    # chin cleft + jaw shading
    cv.put(c, 49, sk[1]); cv.put(c, 48, sk[2])
    # ---- nose ----
    cv.vline(c - 1, 33, 38, sk[3])
    cv.puts([(c + 1, 36), (c + 1, 37), (c + 2, 38), (c + 2, 39), (c + 1, 40), (c, 40), (c - 1, 40), (c - 2, 39)], sk[1])
    cv.puts([(c - 2, 40), (c + 1, 41)], (120, 62, 44))
    # ---- mouth + handlebar moustache ----
    my = 46 if expr != "warm" else 45
    p_mouth(cv, my, expr, talk)
    st = cv.ell(c - 5, 43.0, 6.4, 2.1, -0.18) | cv.ell(c + 5, 43.0, 6.4, 2.1, 0.18)
    st |= cv.capsule(c - 10.5, 42.5, c - 12.5, 39.0, 1.1) | cv.capsule(c + 10.5, 42.5, c + 12.5, 39.0, 1.1)
    if expr == "warm":
        st = cv.ell(c - 5, 42.4, 6.4, 2.1, -0.25) | cv.ell(c + 5, 42.4, 6.4, 2.1, 0.25)
        st |= cv.capsule(c - 10.5, 41.5, c - 12.0, 38.0, 1.1) | cv.capsule(c + 10.5, 41.5, c + 12.0, 38.0, 1.1)
    cv.part("stache", st, "hair", edge=hr[0], noedge=("face",), rad=2, soft=0.6, bias=0.08, cuts=(0.25, 0.48, 0.8))
    cv.put(c, 42, hr[0])
    # ---- eyes + brows ----
    ey = 31
    for side in (-1, 1):
        ex = c - 10 if side < 0 else c + 6
        p_eye(cv, ex, ey, expr, side, blink=blink)
    if expr != "warm":
        for side in (-1, 1):            # crow's feet: he's a sun-worn 40-something
            x = c + side * 15
            cv.put(x, 32, sk[1]); cv.put(x + side, 33, sk[1])
    by = {"neutral": 27, "warm": 27, "concern": 26, "surprised": 25}[expr]
    p_brows(cv, by, expr)
    if expr == "concern":
        cv.puts([(c - 1, 28), (c + 1, 28), (c, 29)], sk[1])
    # ---- helmet: dome, black brow shell, ear flaps, chin strap ----
    dome = cv.ell(c, 22 + lift, 20.5, 18.0) & cv.half(y=24.5 + lift, below=False)
    flaps = cv.empty()
    for s in (-1, 1):
        flaps |= cv.poly([(c + s * 20.5, 18 + lift), (c + s * 13.5, 22 + lift), (c + s * 14.5, 36), (c + s * 17.5, 39), (c + s * 20.0, 34)])
    cv.part("helmet", dome | flaps, "neon", rad=14, soft=2.0, cuts=(0.28, 0.50, 0.82))
    hid = cv.names["helmet"]
    shell = (dome | flaps) & ~cv.ell(c, 21 + lift, 20.0, 18.0)
    shell |= (dome & cv.half(y=22.5 + lift))
    cv.fill(shell & (cv.own == hid) & ~is_ink(cv), LYC[2])
    cv.fill(shell & (cv.own == hid) & ~is_ink(cv) & cv.half(y=23.5 + lift, below=False) & cv.half(y=22.5 + lift), LYC[3])
    stripe = (dome | flaps) & cv.rect(c - 2, 0, c + 2, 21 + lift) & ~shell
    cv.fill(stripe & ~is_ink(cv), PINK[2])
    cv.fill(stripe & ~is_ink(cv) & cv.rect(c - 2, 0, c - 1, 30), PINK[3])
    for s in (-1, 1):                    # vent slots
        for k in range(3):
            cv.put(c + s * (7 + k), 9 + lift + k, NEON[1])
    # chin straps
    for s in (-1, 1):
        cv.line(c + s * 16, 38, c + s * 9, 49, LYC[1])
        cv.line(c + s * 17, 38, c + s * 10, 49, LYC[2])
    # ---- visor flipped up across the helmet front ----
    vy = 12 + lift
    v = cv.ell(c, vy + 9, 17.5, 7.5) & ~cv.ell(c, vy + 13, 17.0, 7.5) & cv.half(y=vy, below=True)
    ys, xs = np.nonzero(v)
    lv = np.zeros(v.shape, int)
    for y_, x_ in zip(ys, xs):
        f = (x_ - xs.min()) / max(1, xs.max() - xs.min())
        lv[y_, x_] = [1, 2, 3, 4, 3, 2, 2, 1][min(7, int(f * 8))]
    cv.part("visor", v, "visor", edge="ink", lv=lv)
    for k in range(4):
        cv.put(c - 9 + k, vy + 4 - (k // 2), WHITE)
    cv.outline()
    if expr == "warm":
        cv.puts([(56, 12), (57, 11), (58, 10), (57, 15), (59, 15), (60, 15)], SPARK2)
    if expr == "surprised":
        cv.puts([(55, 6), (55, 7), (55, 8), (55, 10), (58, 8), (59, 7), (60, 6)], SPARK2)
    if expr == "concern":
        sx, sy = 52, 22
        cv.puts([(sx, sy), (sx - 1, sy + 1), (sx, sy + 1), (sx + 1, sy + 1), (sx - 1, sy + 2), (sx, sy + 2),
                 (sx + 1, sy + 2), (sx, sy + 3)], SWEAT)
        cv.put(sx - 1, sy + 1, SWEAT_HI)
    return cv


def preview(cv_or_img, name, S=8, bg=(44, 44, 62)):
    img = cv_or_img.image() if hasattr(cv_or_img, "image") else cv_or_img
    os.makedirs(PREV, exist_ok=True)
    b = Image.new("RGBA", img.size, bg + (255,))
    b.alpha_composite(img)
    b.resize((img.width * S, img.height * S), Image.NEAREST).save(os.path.join(PREV, name))


# ==========================================================================
# output
# ==========================================================================
EXPRS = ("neutral", "warm", "concern", "surprised")
CAST_REF = "/tmp/claude-0/designs/cast-reference.png"   # 3x contact sheet of the approved cast
BPAD = 4    # empty columns added each side of the 80px battle drawing -> 88px cells


def foot_point(cv, world):
    """World: centre between the shoes on the sole row.  Battle: centre of the tyre contact(s)."""
    y = cv.h - 1
    xs = []
    if world:
        ids = [pid for n, pid in cv.names.items() if n.endswith("shoe")]
        xs = [x for x in range(cv.w) if cv.alpha[y, x] and cv.own[y, x] in ids]
    if not xs:
        xs = [x for x in range(cv.w) if cv.alpha[y, x]]
    return [int(round((min(xs) + max(xs)) / 2)), y]


def check_height(img, want, name):
    a = np.array(img)[..., 3] > 0
    rows = np.nonzero(a.any(axis=1))[0]
    assert rows[-1] == img.height - 1, (name, "not on the bottom row")
    assert img.height - rows[0] == want, (name, "height", img.height - rows[0])


def diff_box(a, b):
    d = np.any(np.array(a) != np.array(b), axis=2)
    ys, xs = np.nonzero(d)
    if len(xs) == 0:
        return None, 0
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())), int(d.sum())


def build():
    for sub in ("", "talk", "idle"):
        os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    feet, cells = {}, {}
    battle = [b_front("idle"), b_front("talk"), b_front("tell"), b_front("hit"), b_side(), b_back()]
    world = [w_front("idle"), w_front("talk"), w_front("tell"), w_front("hit"), w_side(), w_back()]
    for prefix, group, hgt in (("battle", battle, BATTLE_H), ("world", world, WORLD_H)):
        for i, cv in enumerate(group):
            img = cv.image()
            name = "%s-%d.png" % (prefix, i)
            check_height(img, hgt, name)
            fp = foot_point(cv, prefix == "world")
            if prefix == "battle":
                # widen the battle cell so its shrink to world height (x 54/84) is at least as wide as the
                # 56px world cell with the parked bike -- otherwise the native-clean bake clips the wheels
                wide = Image.new("RGBA", (img.width + 2 * BPAD, img.height), (0, 0, 0, 0))
                wide.paste(img, (BPAD, 0))
                img, fp = wide, [fp[0] + BPAD, fp[1]]
            img.save(os.path.join(OUT, name))
            feet[name] = fp
            cells[name] = img
    ent = entrance()
    img = ent.image()
    rows = np.nonzero((np.array(img)[..., 3] > 0).any(axis=1))[0]
    top = max(0, int(rows[0]) - 2)                   # trim the empty sky above the fist / helmet
    img = img.crop((0, top, img.width, img.height))
    assert np.array(img)[-1, :, 3].any(), "entrance tyre"
    img.save(os.path.join(OUT, "entrance.png"))
    fx, fy = foot_point(ent, False)
    # the wheelie only has the rear tyre down: its contact is the foot point
    feet["entrance.png"] = [fx, fy - top]
    cells["entrance.png"] = img
    for i, e in enumerate(EXPRS):
        img = portrait(e).image()
        img.save(os.path.join(OUT, "portrait-%d.png" % i))
        cells["portrait-%d.png" % i] = img
        t_img = portrait(e, talk=True).image()
        box, n = diff_box(img, t_img)
        assert box and box[1] >= 36 and box[3] <= 53, ("talk diff outside the mouth", e, box)
        t_img.save(os.path.join(OUT, "talk", "peloton-%d.png" % i))
        cells["talk-%d.png" % i] = t_img
        print("talk", i, "changed", n, "px in", box)
    base = cells["world-0.png"]
    for key, kw in (("blink", dict(face="blink")), ("pose1", dict(arm_pose="watch", face="look")),
                    ("pose2", dict(arm_pose="bottle"))):
        img = w_front("idle", **kw).image()
        assert img.size == base.size
        box, n = diff_box(base, img)
        print("idle", key, "changed", n, "px in", box)
        img.save(os.path.join(OUT, "idle", "peloton-%s.png" % key))
        cells["idle-%s.png" % key] = img
    # battle-only prop layer: the five riders of the paceline, drawn behind Lance
    pace = paceline()
    pace.save(os.path.join(OUT, "peloton-riders.png"))
    cells["riders"] = pace
    lf = feet["battle-0.png"]
    anchor = [lf[0] - BPAD, PH_ - BH + lf[1]]
    with open(os.path.join(OUT, "peloton-riders.json"), "w", newline="\r\n") as fh:
        fh.write(json.dumps({"path": "peloton-riders.png", "size": list(pace.size), "anchor": anchor,
                             "anchor_is": "Lance's battle foot point (cells 0-5) in this image", "z": "behind",
                             "battle_only": True}, indent=1) + "\n")
    with open(os.path.join(OUT, "feet.json"), "w") as f:
        json.dump(feet, f, indent=2)
    contact_sheet(cells, feet, anchor)
    return cells, feet


def contact_sheet(cells, feet, anchor, S=3):
    """3x sheet: battle row (+ entrance, + Lance in front of his paceline), world row (+ idle extras),
    portrait row (+ talk), each beside the cast crops from the 3x cast reference."""
    from PIL import ImageFont
    BG = (44, 44, 62, 255)
    GROUND = (70, 70, 96, 255)
    font = ImageFont.load_default()
    ref = Image.open(CAST_REF).convert("RGBA") if os.path.exists(CAST_REF) else None

    def up(im):
        return im.resize((im.width * S, im.height * S), Image.NEAREST)

    combo = cells["riders"].copy()
    lf = feet["battle-0.png"]
    combo.alpha_composite(cells["battle-0.png"], (anchor[0] - lf[0], anchor[1] - lf[1]))
    r1 = [(up(cells["battle-%d.png" % i]), "battle-%d" % i) for i in range(6)]
    r1.append((up(cells["entrance.png"]), "cell 12 peloton-entrance"))
    r1.append((up(combo), "battle-0 + peloton-riders.png"))
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
    d.text((pad, 6), "Captain Lance and the Flatirons Peloton (peloton) -- 3x; cast crops from designs/cast-reference.png at the same 3x",
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
