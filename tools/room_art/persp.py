"""One-point perspective battle backdrops.

The view is rendered 3x supersampled, box-reduced to game pixels and quantised without dithering, so
receding surfaces come out as clean mid-resolution pixel clusters. Fronto-parallel pieces (facades,
trees, lamps) are hand-painted sprites scaled by distance. Crisp details go on afterwards at 1:1.

World units: X right, Y up, Z depth. A point at depth Z = F is drawn at 1:1 game pixels, and the
ground there is screen y = horizon + cam, which is where the fighters stand (feet at y 150).
Room paintings are at room scale; ROOM_TO_BATTLE scales them to the 72px battle sprites.
"""
import numpy as np
from PIL import Image
from midlib import quantize
from pixel import C, Canvas

SS = 3
ROOM_TO_BATTLE = 1.7


class View:
    def __init__(self, horizon=98, vx=320, cam=52, F=320.0, W=640, H=360, fill="#141223"):
        self.h0, self.vx, self.cam, self.F, self.W, self.H = horizon, vx, cam, F, W, H
        self.a = np.zeros((H * SS, W * SS, 4), np.float32)
        self.a[:] = C(fill)
        self.solid = np.zeros((H * SS, W * SS), bool)  # False where only sky has been painted
        ys, xs = np.mgrid[0:H * SS, 0:W * SS].astype(np.float32)
        self.sx = (xs + 0.5) / SS
        self.sy = (ys + 0.5) / SS

    # --- projection -------------------------------------------------------
    def project(self, X, Y, Z):
        s = self.F / Z
        return self.vx + X * s, self.h0 + (self.cam - Y) * s

    def scale(self, Z):
        return self.F / Z

    def ground_y(self, Z):
        return self.h0 + self.cam * self.F / Z

    def depth_at_y(self, sy):
        return self.cam * self.F / (sy - self.h0)

    # --- compositing ------------------------------------------------------
    def _blend(self, mask, rgba):
        d = self.a[mask]
        al = rgba[..., 3:4]
        d[..., :3] = rgba[..., :3] * al + d[..., :3] * (1 - al)
        self.a[mask] = d
        sol = self.solid[mask]
        sol |= al[..., 0] > 0.5
        self.solid[mask] = sol

    def fill(self, mask, colour):
        c = np.array(C(colour), np.float32)
        self.a[mask, :3] = c[:3] * c[3] + self.a[mask, :3] * (1 - c[3])

    def strip(self, rgba, y=0, x=0, solid=True):
        """Paste a 1x painted strip (nearest-upscaled) at screen (x, y). solid=False marks it as sky."""
        big = np.repeat(np.repeat(rgba, SS, 0), SS, 1)
        self._paste(big, x * SS, y * SS, solid)

    def sprite(self, rgba, X, Z, Y=0.0, anchor=(0.5, 1.0), scale=1.0):
        """Place a 1x painted sprite standing at world (X, Y, Z); it shrinks with distance."""
        h, w = rgba.shape[:2]
        s = scale * self.F / Z
        tw, th = max(1, int(round(w * s * SS))), max(1, int(round(h * s * SS)))
        img = Image.fromarray((np.clip(rgba, 0, 1) * 255).round().astype(np.uint8), "RGBA").resize((tw, th), Image.NEAREST)
        big = np.array(img).astype(np.float32) / 255
        sx, sy = self.project(X, Y, Z)
        x0 = int(round((sx - anchor[0] * w * s) * SS))
        y0 = int(round((sy - anchor[1] * h * s) * SS))
        self._paste(big, x0, y0)
        return sx, sy, s

    def _paste(self, src, x, y, solid=True):
        h, w = src.shape[:2]
        H, W = self.a.shape[:2]
        x0, y0, x1, y1 = max(0, x), max(0, y), min(W, x + w), min(H, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        s = src[y0 - y:y1 - y, x0 - x:x1 - x]
        d = self.a[y0:y1, x0:x1]
        al = s[..., 3:4]
        d[..., :3] = s[..., :3] * al + d[..., :3] * (1 - al)
        if solid:
            self.solid[y0:y1, x0:x1] |= al[..., 0] > 0.5

    # --- planes -----------------------------------------------------------
    def ground(self, shader, y_from=None, y_to=None, z_max=1e5, height=0.0):
        """Horizontal plane at world height `height` (0 = ground). shader(X, Z) -> RGBA per pixel."""
        drop = self.cam - height
        y_from = self.h0 + 0.01 if y_from is None else y_from
        y_to = self.H if y_to is None else y_to
        mask = (self.sy > y_from) & (self.sy < y_to) & ((self.sy - self.h0) * drop > 0)
        sy, sx = self.sy[mask], self.sx[mask]
        Z = np.minimum(drop * self.F / (sy - self.h0), z_max)
        X = (sx - self.vx) * Z / self.F
        self._blend(mask, shader(X, Z))
        return mask

    def plane(self, A, B, shader, y_max=1e5, y_min=0.0, clip=None):
        """Vertical plane between ground points A=(X, Z) and B=(X, Z). shader(u, Y, Z) -> RGBA,
        with u the distance from A along the wall in world units."""
        ax, az = A
        dx, dz = B[0] - ax, B[1] - az
        length = float(np.hypot(dx, dz))
        k = (self.sx - self.vx) / self.F
        with np.errstate(divide="ignore", invalid="ignore"):
            t_u = (az * k - ax) / (dx - dz * k)
        Z = az + t_u * dz
        Y = self.cam - (self.sy - self.h0) * Z / self.F
        mask = (t_u >= 0) & (t_u <= 1) & (Z > 1) & (Y >= y_min) & (Y <= y_max)
        if clip is not None:
            mask &= clip
        if not mask.any():
            return mask
        self._blend(mask, shader(t_u[mask] * length, Y[mask], Z[mask]))
        return mask

    def back(self, Z, shader, region=None):
        """Fronto-parallel plane at depth Z. shader(X, Y) -> RGBA."""
        X = (self.sx - self.vx) * Z / self.F
        Y = self.cam - (self.sy - self.h0) * Z / self.F
        mask = np.ones_like(X, bool) if region is None else region(X, Y)
        self._blend(mask, shader(X[mask], Y[mask]))
        return mask

    def rows(self, y0, y1, colour, alpha0, alpha1):
        """Vertical ramp of a tint over screen rows y0..y1 (darkening under the battle menus)."""
        c = np.array(C(colour)[:3], np.float32)
        for yy in range(int(y0 * SS), min(self.H * SS, int(y1 * SS))):
            t = (yy / SS - y0) / max(1e-3, y1 - y0)
            al = alpha0 + (alpha1 - alpha0) * t
            self.a[yy, :, :3] = c * al + self.a[yy, :, :3] * (1 - al)

    # --- output -----------------------------------------------------------
    def reduce(self, colors=64, **grade):
        img = Image.fromarray((np.clip(self.a, 0, 1) * 255).round().astype(np.uint8), "RGBA")
        small = np.array(img.resize((self.W, self.H), Image.BOX)).astype(np.float32) / 255
        small[..., 3] = 1
        out = quantize(small, colors, **grade) if colors else small
        cv = Canvas(self.W, self.H)
        cv.a = out
        return cv

    def solid_mask(self):
        """1x mask of pixels covered by anything but sky (majority of the 3x3 samples)."""
        m = self.solid.reshape(self.H, SS, self.W, SS).mean(axis=(1, 3))
        return m >= 0.5

    def mark_sky(self, y0, y1):
        """Treat screen rows y0..y1 as open sky again (for a strip painted as solid by mistake)."""
        self.solid[int(y0 * SS):int(y1 * SS)] = False


def texture_lookup(tex, u, v, wrap=True):
    """Nearest sample of a float RGBA texture at float texel coords (u right, v down)."""
    h, w = tex.shape[:2]
    ui = np.floor(u).astype(int)
    vi = np.floor(v).astype(int)
    if wrap:
        ui %= w
        inside = (vi >= 0) & (vi < h)
    else:
        inside = (ui >= 0) & (ui < w) & (vi >= 0) & (vi < h)
    out = tex[np.clip(vi, 0, h - 1), np.clip(ui, 0, w - 1)].copy()
    out[~inside, 3] = 0
    return out


def hash2(a, b, seed=0):
    """Deterministic per-cell noise in 0..1 for integer arrays a, b."""
    h = (np.asarray(a).astype(np.int64) * 73856093) ^ (np.asarray(b).astype(np.int64) * 19349663) ^ (seed * 83492791)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return (h & 0xFFFF).astype(np.float32) / 65535.0


def fog(rgba, Z, colour, start, end, amount=1.0):
    """Blend toward a haze colour with distance (also keeps far texture from aliasing)."""
    t = np.clip((Z - start) / max(1e-3, end - start), 0, 1)[..., None] * amount
    c = np.array(C(colour)[:3], np.float32)
    rgba[..., :3] = rgba[..., :3] * (1 - t) + c * t
    return rgba


def pal_array(pal):
    return np.array([C(p)[:3] for p in pal], np.float32)


def rgba_of(rgb, alpha=1.0):
    out = np.ones(rgb.shape[:-1] + (4,), np.float32)
    out[..., :3] = rgb
    out[..., 3] = alpha
    return out


def warm_light(rgb, dist, radius, colour="#f6cf7a", strength=0.35, bands=3):
    """Stepped pool of light (concentric bands, not a soft gradient), added in place."""
    c = np.array(C(colour)[:3], np.float32)
    t = np.clip(1 - dist / radius, 0, 1)
    t = np.ceil(t * bands) / bands * strength
    rgb[...] = rgb * (1 - t[..., None]) + (rgb * 0.4 + c * 0.6) * t[..., None]
    return rgb
