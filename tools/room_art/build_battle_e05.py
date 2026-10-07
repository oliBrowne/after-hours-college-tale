"""Battle backdrop for the control booth (E05): inside the booth facing the long observation window,
the recording console in front of it running "the recording nobody made". Through the window the
suspended model hangs in the dark bay with its amber lights; the hanging status screen plays the
waveform, the reels on the console deck turn, the meter bridge's LED bars jump, the REC lamp over the
window blinks. The booth is the Engineering Center's raw board-formed concrete: wedge-foam panels
set into the concrete walls in steel frames, a Lyons sandstone base course, the observation window
deep in a thick concrete frame, can lights under the coffered concrete ceiling, the carpet receding
to a rug under the console."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C, shade
from persp import View, hash2, fog, pal_array, rgba_of, warm_light, texture_lookup
from lib_umc import halo
from lib_norlin2 import reel_face
import lib_eng as E
import ec_interior as I
from lib_umc import SHADOW

ROOM = "E05"
INK = "#10121e"
Z_BACK = 640.0
Z_NEAR = 280.0
X_WALL = 400.0
H_CEIL = 180.0
Z_CONSOLE = 520.0
CANS = [(-200.0, 400.0), (200.0, 400.0), (-200.0, 570.0), (200.0, 570.0), (0.0, 480.0)]
FOG = "#16141e"


def bay_view(w, h, seed=0):
    """The high bay through the window: crane girder, far clerestory with stars, the suspended model
    on its slings with amber lights, the test floor's glow below. Returns view, lights, beacon, stars."""
    rng = np.random.default_rng(seed)
    view = Canvas(w, h, fill="#12101a")
    for k in range(h * 2 // 3, h):
        view.hline(0, k, w, E.mix("#12101a", "#3a2c24", (k - h * 2 / 3) / (h / 3) * 0.8))
    view.rect(0, 9, w, 13, "#1c1a34")
    stars = []
    for wx in range(4, w, 30):
        view.rect(wx, 10, 24, 11, E.NIGHT_BANDS[2]); view.rect(wx, 17, 24, 4, "#1c1830")
        sx, sy = wx + int(rng.integers(2, 22)), 11 + int(rng.integers(0, 4))
        view.px(sx, sy, "#c8ccec"); stars.append((sx, sy))
    view.rect(0, 2, w, 5, E.CRANE[2]); view.hline(0, 2, w, E.CRANE[4]); view.hline(0, 6, w, E.CRANE[1])
    m0, m1, deck, apex = 70, 270, 30, 12
    BL = ["#1a2a56", "#2c437e", "#425da6", "#5c7cc4", "#8aa6dc"]
    for (hx, legs) in ((m0 + 30, (m0 + 6, m0 + 50)), (m1 - 30, (m1 - 50, m1 - 6))):
        view.rect(hx - 6, 6, 13, 3, E.CRANE[3])
        view.vline(hx, 9, 4, E.STEEL[5])
        view.rect(hx - 2, 13, 5, 4, E.CRANE[3])
        for lx in legs:
            view.line(hx, 17, lx, deck - 1, E.STEEL[4])
    for xx in range(m0 + 4, m1 - 3):
        t = (xx - m0 - 4) / (m1 - m0 - 7)
        yy = int(round(deck - 1 - (deck - 1 - apex) * 4 * t * (1 - t)))
        view.px(xx, yy, BL[4]); view.px(xx, yy + 1, BL[2])
        if (xx - m0) % 7 == 0 and 0.05 < t < 0.95:
            view.vline(xx, yy + 2, deck - yy - 2, BL[2])
    view.rect(m0, deck, m1 - m0, 4, BL[2]); view.hline(m0, deck, m1 - m0, BL[4]); view.hline(m0, deck + 3, m1 - m0, BL[1])
    lights = []
    for lx in range(m0 + 4, m1, 10):
        view.px(lx, deck + 4, E.WARM[3]); lights.append((lx, deck + 4))
    E.soft_ellipse(view, w // 2, h - 4, w // 2, 10, "#f6cf7a", 0.14)
    return view, lights, (w - 18, 4), stars


def back_wall():
    """The window wall at 1:1 screen pixels: foam, walnut wainscot, the observation window onto
    the bay, monitors either side, the REC lightbox (dark; the layer lights it)."""
    w, h = 400, 90
    cv = Canvas(w, h, fill="#171a2b")
    I.board_concrete(cv, 0, 0, w, 72, seed=81, board=5, lift=36, ties=(20, 15), stains=0.25, foot=0)
    I.lyons_wall(cv, 0, 72, w, h - 72, seed=83, course=(4, 5, 6), length=(8, 24))
    E.tint_rect(cv, 0, 76, w, h - 76, SHADOW, 0.14)
    x, y, vw, vh = 30, 14, 340, 56
    view, model_pts, beacon, stars = bay_view(vw, vh, seed=82)
    I.deep_window(cv, x, y, vw, vh, seed=84, depth=6, sky=False, mullion=False)
    cv.rect(x - 2, y - 2, vw + 4, vh + 4, E.STEEL[1])
    cv.paste(view, x, y)
    for mx in (x + vw // 3, x + 2 * vw // 3):
        cv.rect(mx - 1, y, 3, vh, E.STEEL[1]); cv.vline(mx - 1, y, vh, E.STEEL[3])
    for k in range(3):
        rx = x + 20 + k * vw // 3
        cv.line(rx, y + vh - 3, rx + 18, y + 3, C("#c8d0f0", 0.12)); cv.line(rx + 5, y + vh - 3, rx + 23, y + 3, C("#c8d0f0", 0.08))
    model_pts = [(x + px, y + py) for (px, py) in model_pts]
    beacon = (x + beacon[0], y + beacon[1])
    E.studio_monitor(cv, 6, 24)
    E.studio_monitor(cv, 378, 24, flip=True)
    rec = E.lightbox(cv, 186, 0, "REC", lit=False)
    return cv, model_pts, beacon, rec


def console():
    """The recording console at 1:1: the tape deck rising at the centre, the meter bridge with LED
    bars, the sloped fader panel, the padded armrest, the walnut front."""
    w, h = 410, 70
    cv = Canvas(w, h)
    # tape deck at the centre
    dx0, dx1, dt = 170, 240, 6
    cv.rect(dx0, dt, dx1 - dx0, 28 - dt, E.OUT); cv.rect(dx0 + 1, dt + 1, dx1 - dx0 - 2, 27 - dt, "#5a5664"); cv.hline(dx0 + 1, dt + 1, dx1 - dx0 - 2, "#7a7684")
    r = 9
    reels = [(dx0 + 3 + r + 1, dt + 2 + r), (dx1 - 4 - r - 1, dt + 2 + r)]
    for (cx, cy) in reels:
        cv.ellipse(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, "#2a2832")
    hx = (dx0 + dx1) // 2
    cv.rect(hx - 7, 19, 14, 6, "#2a2832"); cv.rect(hx - 5, 20, 3, 3, E.STEEL[6]); cv.rect(hx + 2, 20, 3, 3, E.STEEL[6])
    cv.line(reels[0][0], reels[0][1] + r, hx - 5, 22, "#5a3a28"); cv.line(hx + 5, 22, reels[1][0], reels[1][1] + r, "#5a3a28")
    for k, col in enumerate(("#3a3a46", "#3a3a46", "#c03a32")):
        cv.rect(dx0 + 6 + k * 7, 24, 5, 3, col)
    # meter bridge
    cv.rect(0, 26, w, 11, E.OUT); cv.rect(1, 27, w - 2, 9, "#1e1c26"); cv.hline(1, 27, w - 2, "#34303e")
    bars = []
    for bx in list(range(10, 150, 5)) + list(range(262, 400, 5)):
        for s in range(0, 7, 2):
            col = "#c03a32" if s == 0 else ("#e8b45c" if s == 2 else "#2a7a4a")
            cv.rect(bx, 28 + s, 3, 1, shade(col, -0.55))
        bars.append((bx, 28, 3, 7))
    for vx in (152, 252):                                       # two amber needle meters by the deck
        cv.rect(vx, 28, 8, 6, "#3a2a14"); cv.rect(vx + 1, 29, 6, 4, "#e8b45c"); cv.line(vx + 2, 32, vx + 5, 29, E.OUT)
    # sloped fader panel
    cv.rect(0, 37, w, 11, E.OUT); cv.rect(1, 38, w - 2, 9, "#3a3e4c"); cv.hline(1, 38, w - 2, "#545a6c")
    leds = []
    for k, sx in enumerate(range(6, w - 4, 8)):
        cv.px(sx, 39, ("#c8c4d0", "#e8b45c", "#7ab0e0", "#c84a3c")[k % 4])
        cv.px(sx + 3, 39, "#8a8696")
        cv.vline(sx + 1, 41, 5, "#14121a")
        cap = 41 + (k * 7) % 4
        cap_col = "#e8e2d0" if k % 9 else "#c03a32"
        cv.rect(sx, cap, 3, 2, cap_col)
        if k % 5 == 2:
            leds.append((sx + 3, 40))
    # armrest and the walnut front
    cv.rect(0, 48, w, 4, "#14121a"); cv.hline(0, 48, w, "#3a3440"); cv.hline(0, 49, w, "#24202a")
    cv.rect(0, 52, w, h - 52, E.WAINSCOT[1])
    for px in range(0, w, 41):
        cv.rect(px + 2, 54, 37, h - 58, E.WAINSCOT[2]); cv.hline(px + 2, 54, 37, E.WAINSCOT[3])
    cv.rect(0, h - 3, w, 3, "#0e0c12")
    return cv, reels, r, bars, leds


def floor_shader(X, Z):
    cp = pal_array(E.CARPET)
    rgb = np.empty(X.shape + (3,), np.float32)
    rgb[:] = cp[3]
    fleck = hash2(np.floor(X * 320 / Z), np.floor(16640 / Z), 3)
    rgb[fleck > 0.9] = cp[4]
    rgb[fleck < 0.06] = cp[2]
    seam = (np.abs((X % 48) - 24) > 23.2) | (np.abs((Z % 48) - 24) > 23.2)
    rgb[seam] = cp[2]
    # the rug under the console with its dotted border
    rug = (np.abs(X) < 360) & (Z > 450) & (Z < Z_CONSOLE + 4)
    rgb[rug] = np.array(C("#2a2238")[:3], np.float32)
    border = rug & ((np.abs(X) > 352) | (Z < 456)) & ((np.floor((X + Z) / 8) % 2) == 0)
    rgb[border] = np.array(C("#6a4e7a")[:3], np.float32)
    for (cx, cz) in CANS:
        warm_light(rgb, np.hypot(X - cx, (Z - cz) * 1.5), 90, colour="#f6cf7a", strength=0.18)
    warm_light(rgb, np.hypot(X + 130, (Z - 430) * 1.3), 160, colour="#7ae0a0", strength=0.1)
    out = rgba_of(rgb)
    fog(out, Z, FOG, 480, Z_BACK + 40, amount=0.3)
    return out


def ceiling_shader(X, Z):
    out = I.beam_ceiling_shader(X, Z, bay_z=85.0, bay_x=200.0, z0=360.0, fog_to=Z_BACK, fog_col="#100e16")
    rgb = out[..., :3]
    for (cx, cz) in CANS:
        d = np.hypot(X - cx, Z - cz)
        rgb[d < 11] = np.array(C(E.STEEL[3])[:3], np.float32)
        rgb[d < 7] = np.array(C(E.WARM[3])[:3], np.float32)
        rgb[d < 3.5] = np.array(C(E.WARM[4])[:3], np.float32)
    out[Z > Z_BACK, 3] = 0
    return out


SIDE_L = int(Z_BACK - Z_NEAR)


def side_texture(seed):
    """A side wall in world units (1 texel each): board-formed concrete, wedge-foam panels set
    into it between concrete piers, the sandstone base course below."""
    cv = Canvas(SIDE_L + 1, int(H_CEIL) + 1, fill="#171a2b")
    hc = int(H_CEIL)
    I.board_concrete(cv, 0, 0, SIDE_L + 1, hc + 1, seed=seed, board=8, lift=60, ties=(28, 24), tie=3, stains=0.25, foot=0)
    for k, px in enumerate(range(14, SIDE_L - 60, 96)):
        I.foam_panel(cv, px, 34, 76, hc - 34 - 52, seed=seed + k, tile=20)
    I.lyons_wall(cv, 0, hc - 40, SIDE_L + 1, 41, seed=seed + 9, course=(7, 8, 9, 10, 12), length=(16, 44))
    return cv


def wall_shader(side):
    tex = side_texture(91 if side < 0 else 97).a

    def shade(u, Y, Z):
        out = texture_lookup(tex, u, H_CEIL - Y, wrap=True)
        rgb = out[..., :3]
        # light scallops under the can lights
        for (cx, cz) in CANS:
            if np.sign(cx) == side or cx == 0:
                warm_light(rgb, np.hypot((Z - cz) * 1.0, (Y - 120) * 2.2), 70, colour="#f6cf7a", strength=0.12)
        out[..., :3] *= 0.85
        fog(out, Z, FOG, 400, Z_BACK, amount=0.3)
        return out
    return shade


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#12121c")
    v.ground(floor_shader)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=H_CEIL)
    for side in (-1, 1):
        v.plane((side * X_WALL, Z_NEAR), (side * X_WALL, Z_BACK), wall_shader(side), y_max=H_CEIL)
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp: the window wall, the console, the hanging status screen
    wall, model_pts, beacon, rec = back_wall()
    bx, by = 320 - wall.w // 2, int(round(v.ground_y(Z_BACK))) - wall.h
    cv.paste(wall, bx, by)
    cons, reels, rr, bars, leds = console()
    cx0, cy0 = 320 - cons.w // 2, int(round(v.ground_y(Z_CONSOLE))) - cons.h
    E.stepped_glow(cv, 320, cy0 + cons.h, 230, 8, "#0a0910", 0.35, 2)
    cv.paste(cons, cx0, cy0)
    sx, sy, sw, sh = 98, 22, 150, 34
    for rx in (sx + 16, sx + sw - 16):
        cv.rect(rx, 0, 2, sy - 4, E.STEEL[3]); cv.vline(rx, 0, sy - 4, E.STEEL[5])
    trace = E.status_screen(cv, sx, sy, sw, sh)
    halo(cv, sx + sw // 2, sy + sh // 2, 90, "#7ae0a0", 0.05, 3)
    for (rcx, rcy) in reels:
        cv.paste(reel_face(rr, 0.3, 0.55), cx0 + rcx - rr - 1, cy0 + rcy - rr - 1)
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    # the recording nobody made: the waveform scrolling on the hanging screen
    tx, ty, tw, th = trace
    n = 8
    for k in range(n):
        fr = E.wave_frame(tw, th, k, n, seed=5)
        fr.save(os.path.join(out, f"battle-wave-{k}.png"))
        layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(n)), "rate": 6.0,
                       "texture": res + f"battle-wave-{k}.png", "x": tx, "y": ty})
    # the console deck's reels turning
    m = 4
    for k in range(m):
        fr = reel_face(rr, 0.3 + k * 0.5236, 0.55)
        fr.save(os.path.join(out, f"battle-reel-{k}.png"))
        for (rcx, rcy) in reels:
            layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(m)), "rate": 8.0,
                           "texture": res + f"battle-reel-{k}.png", "x": cx0 + rcx - rr - 1, "y": cy0 + rcy - rr - 1})
    # meter bridge LED bars: three bands with offset patterns per bar
    pats = ["1111111111", "1101111011", "0100110010"]
    groups = {}
    for b, (lx, ly, lw, lh) in enumerate(bars):
        for band, (segs, col) in enumerate((((4, 6), "3cba7a"), ((2,), "e8b45c"), ((0,), "ff5a4a"))):
            rot = (b * 3) % 10
            groups.setdefault((band, rot), []).extend([[cx0 + lx, cy0 + ly + ss, 3, 1, col] for ss in segs])
    for (band, rot), rects in sorted(groups.items()):
        layers.append({"kind": "blink", "pattern": pats[band][rot:] + pats[band][:rot], "rate": 7.0, "rects": rects})
    # REC over the window, lit and breathing
    on = Canvas(rec[2], rec[3])
    E.lightbox(on, 0, 0, "REC", lit=True)
    on.save(os.path.join(out, "battle-rec-on.png"))
    layers += [
        {"kind": "blink", "pattern": "1100", "rate": 1.2, "texture": res + "battle-rec-on.png", "x": bx + rec[0], "y": by + rec[1]},
        {"kind": "blink", "pattern": "1100", "rate": 1.2,
         "rects": [[bx + rec[0] - 6, by + rec[1] - 5, rec[2] + 12, rec[3] + 10, "ff5a4a", 0.10]]},
        {"kind": "blink", "pattern": "100110", "rate": 3.0, "rects": [[cx0 + x, cy0 + y, 1, 1, "7ae0a0"] for (x, y) in leds]},
        {"kind": "twinkle", "points": [[bx + x, by + y, "f6cf7a", 1] for (x, y) in model_pts], "rate": 1.1, "min": 0.4},
        {"kind": "blink", "pattern": "100000", "rate": 3.0, "rects": [[bx + beacon[0] - 1, by + beacon[1], 3, 2, "ffc040"]]},
    ]
    cans = []
    for (cx, cz) in CANS:
        px, py = v.project(cx, H_CEIL, cz)
        if 0 <= px < 640 and 0 <= py < 166:
            cans.append([int(round(px)), int(round(py)), "fff0c4", 1])
    layers += [
        {"kind": "twinkle", "points": cans, "rate": 0.9, "min": 0.8},
        {"kind": "particles", "style": "dust", "count": 14, "rect": [60, 30, 520, 90], "speed": [1, 2], "color": "f6dca0"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
