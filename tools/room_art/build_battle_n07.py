"""Battle backdrop for the playback room (N07): facing the big phosphor monitor across the listening
room while the source reel plays.

Pleated teal acoustic panels line both walls above an oak dado; the ceiling is a grid of acoustic
tiles with warm recessed lights; a teal listening carpet runs to the far wall, two listening
benches waiting mid-room. On the far wall the monitor fills the view under its lit PLAYBACK sign,
the recorded voice scrolling across it as a green waveform; tall walnut studio monitors stand
either side with their woofers pumping, the equipment credenza beneath with VU meters jumping. The
screen's green light spills over the carpet; dust turns in it and a moth circles the sign."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade, text, text_width
from props import OUT, IRON
from lib_norlin import oak_wainscot, ceiling_band, library_bench, OAK, OAK_DARK, BRASS, OAK_FLOOR
from lib_norlin2 import (acoustic_wall, lit_sign, waveform_screen, waveform_frame, vu_pair, loudspeaker, woofer_push, ACOUSTIC,
                         PHOSPHOR, CASE, AMBER_LIT)
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup, ROOM_TO_BATTLE

ROOM = "N07"
INK = "#10121e"
HAZE = "#121a1e"
VX = 304
Z_END = 760.0
WALL_X = 300.0
CEIL = 262.0
DADO = 44.0
LIGHTS = [(-120.0, 420.0), (120.0, 420.0), (-120.0, 600.0), (120.0, 600.0)]
TEAL_RUG = ["#0c1416", "#122024", "#1a2e34", "#223c42", "#2c4c52", "#c0884a", "#e0b26a"]
GREEN = "#7ad08a"


def floor_shader(X, Z):
    """The teal listening carpet in a diamond lattice with small gold rosettes, a parquet margin
    along the walls; warm pools under the ceiling lights, green light from the screen."""
    rug = pal_array(TEAL_RUG)
    m = 34.0
    U = (X % m) - m / 2
    V = ((Z * 1.0) % m) - m / 2
    D = np.abs(U) + np.abs(V)
    cell = (np.floor(X / m) + np.floor(Z / m)) % 2
    rgb = np.where((cell == 0)[:, None], rug[2], rug[3])
    rgb[D >= m / 2 - 2] = rug[4]
    rgb[D <= 2.2] = rug[5]
    rgb[D <= 0.9] = rug[6]
    ax = np.abs(X)
    border = (ax > WALL_X - 40)
    rgb[(ax > WALL_X - 46) & (ax <= WALL_X - 40)] = rug[1]
    rgb[(np.abs(ax - (WALL_X - 50)) < 1.2)] = rug[5]
    oak = pal_array(OAK_FLOOR)
    strip = np.floor(Z / 70.0 + hash2(np.floor(X / 12.0), 3) * 3)
    t = hash2(np.floor(X / 12.0), strip, 5)
    wood = oak[3] * (1 - t[:, None]) + oak[4] * t[:, None]
    wood[((X / 12.0) % 1) < 0.1] = oak[1]
    rgb[border] = wood[border]
    for (lx, lz) in LIGHTS:
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.8), 120, strength=0.3)
    warm_light(rgb, np.hypot(X * 0.6, (Z - Z_END) * 1.2), 200, colour=GREEN, strength=0.28)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 600, 1100, amount=0.45)
    return out


def ceiling_shader(X, Z):
    """Acoustic ceiling tiles (pin-holed, in a slim grid) with warm recessed lights."""
    rgb = np.zeros((X.shape[0], 3), np.float32)
    tile = pal_array(["#2a3438", "#344246", "#3e4e52", "#56666a"])
    rgb[:] = tile[1]
    t = hash2(np.floor(X / 40.0), np.floor(Z / 40.0), 2)
    rgb[t > 0.6] = tile[2]
    gx, gz = (X / 40.0) % 1, (Z / 40.0) % 1
    holes = (hash2(np.floor(X / 5), np.floor(Z / 5), 7) > 0.8)
    rgb[holes] *= 0.85
    rgb[(gx < 0.05) | (gz < 0.05)] = tile[0]
    for (lx, lz) in LIGHTS:
        lit = (np.abs(X - lx) < 18) & (np.abs(Z - lz) < 18)
        rgb[lit] = np.array(C("#fde9b6")[:3])
        rgb[lit & ((np.abs(X - lx) > 14) | (np.abs(Z - lz) > 14))] = np.array(C(BRASS[3])[:3])
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 0.9), 70, strength=0.25)
    warm_light(rgb, np.hypot(X * 0.6, (Z - Z_END) * 1.4), 150, colour=GREEN, strength=0.18)
    out = rgba_of(rgb)
    fog(out, Z, HAZE, 500, 1000, amount=0.5)
    return out


def wall_texture(length, seed=0):
    """A side wall laid flat (u along the wall, v down from the ceiling): ceiling edge, pleated
    acoustic panels, oak dado."""
    hh = int(CEIL)
    cv = Canvas(length, hh, seed=seed)
    ceiling_band(cv, 0, 0, length, 10)
    acoustic_wall(cv, 0, 10, length, hh - 10 - int(DADO), seed=seed, panel=34)
    oak_wainscot(cv, 0, hh - int(DADO), length, int(DADO), seed=seed, panel=34)
    return cv.a


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    v = View(horizon=98, vx=VX, cam=52, fill="#0e1014")
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=CEIL, z_max=Z_END)
    v.ground(floor_shader, z_max=Z_END)
    tex = wall_texture(int(Z_END) + 40, seed=5)
    for side in (-1, 1):
        def shade_wall(u, Y, Z, side=side):
            o = texture_lookup(tex, Z, CEIL - Y, wrap=False)
            o[..., :3] *= 0.86 if side < 0 else 0.78
            for (lx, lz) in LIGHTS:
                if lx * side > 0:
                    warm_light(o[..., :3], np.hypot((Z - lz) * 0.8, (Y - 200) * 0.9), 130, strength=0.3)
            warm_light(o[..., :3], np.hypot((Z - Z_END) * 1.0, (Y - 120) * 0.6), 140, colour=GREEN, strength=0.2)
            return fog(o, Z, HAZE, 600, 1100, amount=0.45)
        v.plane((side * WALL_X, 200.0), (side * WALL_X, Z_END), shade_wall, y_max=CEIL)
    # far wall (acoustic panels at its on-screen size; the equipment goes on crisp afterwards)
    s = v.scale(Z_END)
    Wp = int(round(2 * WALL_X * s)) + 2
    Hp = int(round(CEIL * s))
    fw = Canvas(Wp, Hp, seed=3)
    ceiling_band(fw, 0, 0, Wp, 5, stencil=False)
    acoustic_wall(fw, 0, 5, Wp, Hp - 5 - int(DADO * s), seed=8, panel=14)
    oak_wainscot(fw, 0, Hp - int(DADO * s), Wp, int(DADO * s), seed=8, panel=14)
    fx0 = int(round(v.vx - Wp / 2))
    fy0 = int(round(v.ground_y(Z_END) - Hp))
    v.strip(fw.a, fy0, fx0)
    # two listening benches mid-room
    bench = library_bench(120, 32, seed=1, cushion="#4a2a3a")[0]
    for side in (-1, 1):
        v.sprite(bench.a, side * 150.0, 560.0, scale=ROOM_TO_BATTLE)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # Crisp at 1:1 on the far wall: monitor, sign, studio monitors, credenza.
    def at(X, Y):
        x, y = v.project(X, Y, Z_END)
        return int(round(x)), int(round(y))
    ground = int(round(v.ground_y(Z_END)))
    sx0, sy0 = at(-160, 236)
    sx1, sy1 = at(160, 84)
    sw, sh = sx1 - sx0, sy1 - sy0
    for i, a in enumerate((0.06, 0.1)):
        cv.rect(sx0 - 8 + i * 4, sy0 - 6 + i * 3, sw + 16 - i * 8, sh + 12 - i * 6, C(GREEN, a))
    gx, gy, gw, gh = waveform_screen(cv, sx0, sy0, sw, sh)
    lit_sign(cv, v.vx, sy0 - 17, "PLAYBACK")
    cx0, cy0 = at(-150, 64)
    cx1, _ = at(150, 0)
    cv.rect(cx0 - 1, cy0 - 1, cx1 - cx0 + 2, ground - cy0 + 1, OUT)
    cv.rect(cx0, cy0, cx1 - cx0, ground - cy0, OAK[2]); cv.hline(cx0, cy0, cx1 - cx0, OAK[5])
    vus = []
    for k, frac in enumerate((0.16, 0.6)):
        vx_ = cx0 + int((cx1 - cx0) * frac)
        cv.rect(vx_ - 2, cy0 + 3, 44, 16, OUT); cv.rect(vx_ - 1, cy0 + 4, 42, 14, CASE[3])
        cv.paste(vu_pair(36, 12, (0.4, 0.55)), vx_ + 2, cy0 + 5)
        vus.append((vx_ + 2, cy0 + 5))
    for kx in range(cx0 + 4, cx1 - 4, 9):
        if all(not (vx_ - 4 <= kx <= vx_ + 44) for (vx_, _) in vus):
            cv.rect(kx, cy0 + 8, 4, 4, OUT); cv.rect(kx + 1, cy0 + 9, 2, 2, CASE[4])
    cv.rect(cx0 + (cx1 - cx0) // 2 - 4, cy0 + 4, 3, 2, GREEN)
    woofers = []
    for side in (-1, 1):
        lx, ltop = at(side * 232, 250)
        woofers.append(loudspeaker(cv, lx, ltop, ground, w=30))
    os.makedirs(out, exist_ok=True)
    cv.save(os.path.join(out, "battle-far.png"))
    res = f"res://assets/art/rooms/{ROOM}/"

    layers = []
    n = 12
    for k in range(n):
        name = f"battle-wave-{k}.png"
        waveform_frame(gw - 2, gh - 2, k, n, seed=11).save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(n)), "rate": 10.0,
                       "texture": res + name, "x": gx + 1, "y": gy + 1})
    angles = [(0.3, 0.42), (0.62, 0.55), (0.48, 0.7), (0.78, 0.6), (0.4, 0.35), (0.66, 0.8)]
    for k, a in enumerate(angles):
        name = f"battle-vu-{k}.png"
        vu_pair(36, 12, a).save(os.path.join(out, name))
        for j, (vx_, vy_) in enumerate(vus):
            pat = ["0"] * len(angles)
            pat[(k + j * 3) % len(angles)] = "1"
            layers.append({"kind": "blink", "pattern": "".join(pat), "rate": 6.0, "texture": res + name, "x": vx_, "y": vy_})
    wr = woofers[0][2]
    woofer_push(wr).save(os.path.join(out, "battle-woofer.png"))
    for (wx, wy, r) in woofers:
        layers.append({"kind": "blink", "pattern": "1010001011000100", "rate": 8.0, "texture": res + "battle-woofer.png",
                       "x": wx - r - 1, "y": wy - r - 1})
    glows = []
    for (lx, lz) in LIGHTS:
        x, y = v.project(lx, CEIL, lz)
        if 0 <= y < 160:
            glows.append([int(round(x)), int(round(y)), "fde9b6", 1])
    glows.append([sx0 + 10, sy0 + sh - 5, "7ad08a", 0])
    layers += [
        {"kind": "twinkle", "points": glows, "rate": 1.1, "min": 0.6},
        {"kind": "particles", "style": "dust", "count": 22, "rect": [sx0 - 20, sy0, sw + 40, 90], "speed": [1, 2], "color": "c8f0d0"},
        {"kind": "fauna", "fauna": [{"kind": "lamp_moth", "x": v.vx, "y": sy0 - 22, "range": 8, "speed": 2.0, "rate": 9.0}]},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    spec = build(paths.PROJECT)
    print(json.dumps(spec)[:300])
