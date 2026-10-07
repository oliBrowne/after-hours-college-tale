"""Battle backdrop for the test floor (E03), where Professor Eric (signal integrity) fights: standing
on the strong floor of the structures bay, looking at the reaction wall, inside the Engineering
Center's raw board-formed concrete (coffered concrete ceiling, slot windows deep in the walls, a
Lyons sandstone base course and pier). A big signal-integrity display hangs from the ceiling: an
eye diagram shimmering with jitter on the left, a board layout on the right with a pulse running
down a highlighted differential pair and its return path. A rolling scope cart stands between the
party and the professor, its own trace ringing out, probe and SMA cables trailing across the floor.
Behind it all the blue load frame still drives its actuator into the beam specimen, the probe bench
and DAQ blink, the wall display plots the load as it climbs, a crane hook swings on the right, and
the two steel foundations either side of the professor's spot glow."""
import paths
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from pixel import Canvas, C
from persp import View, ROOM_TO_BATTLE, hash2, fog, pal_array, rgba_of, warm_light
from lib_umc import extinguisher, halo, SAFETY, SHADOW
import lib_eng as E
import ec_interior as I
import build_e03 as R

ROOM = "E03"
INK = "#10121e"
K = ROOM_TO_BATTLE
Z_BACK = 700.0
S_BACK = K * 320.0 / Z_BACK
HC = R.BASE + 12                                  # back canvas: the room's wall plus the stair's first treads
PADS = ((48.0, 372.0), (298.0, 372.0))            # foundations either side of the enemy
HOOK = (330.0, 420.0)                             # the near crane hook (world X, Z)
DISPLAY = (138, 46, 70, 22)                       # load display high on the wall, above the party (room px)
BIG = (112, 4, 260, 56)                           # the hanging SI display (screen px): x, y, w, h
CART = (306, 128)                                 # the scope cart in the midground (screen px): left, floor y
STAIR = (884, 956)
FOG = "#1e1c2a"


def back_wall():
    """The test bay's back wall at room scale, laid out for this view."""
    cv = Canvas(R.W, HC)
    cv.rect(0, 0, R.W, R.BASE, "#171a2b")
    stars = R.paint_fabric(cv, windows=tuple(x for x in R.WINDOWS if x != 150))
    R.reaction_wall(cv, R.WALL[0], R.WALL[1], R.WALL_TOP, R.BASE)
    E.crane_girder(cv, 0, R.W, R.GIRDER_Y, 16, "10 TON", None)
    bulbs = [I.cage_lamp(cv, x, R.GIRDER_Y + 16, 8) for x in (92, 640, 872)]
    leds = E.daq_rack(cv, 74, R.BASE - 72, 30, 72)
    E.micro_text(cv, "DAQ", 83, R.BASE - 79, "#d8c8a8")
    utm_screen = E.utm(cv, 112, R.BASE)
    box = E.lightbox(cv, 446, 46, "LOAD TEST", lit=True)
    halo(cv, box[0] + box[2] // 2, box[1] + 7, 40, "#ff5a4a", 0.07, 3)
    tip, spec = E.test_frame(cv, R.FRAME[0], R.FRAME[1], R.FRAME[2], R.BASE, seed=5)
    E.hpu(cv, R.HPU_X, R.BASE)
    cv.rect(R.WALL[0], 108, R.FRAME[0] - R.WALL[0], 3, E.STEEL[3]); cv.hline(R.WALL[0], 108, R.FRAME[0] - R.WALL[0], E.STEEL[5])
    cv.rect(104, 108, R.WALL[0] - 104, 3, E.STEEL[3]); cv.hline(104, 108, R.WALL[0] - 104, E.STEEL[5])
    si = I.si_bench(cv, R.SI_BENCH[0], R.BASE, R.SI_BENCH[1], seed=7)
    cv.paste(I.si_screen_frame(si["screen"][2], si["screen"][3], 0, 6, "eye"), si["screen"][0], si["screen"][1])
    # the load display's wall bracket (its screen is painted crisp after the reduce)
    dx, dy, dw, dh = DISPLAY
    cv.rect(dx - 3, dy - 3, dw + 6, dh + 6, "#1a1524"); cv.rect(dx - 2, dy - 2, dw + 4, dh + 4, "#2a2a34")
    cv.rect(dx + dw // 2 - 3, dy + dh + 3, 6, 4, "#2a2a34")
    # the stair up to the model level, extinguisher
    E.stair_up_opening(cv, STAIR[0], STAIR[1], 100, R.BASE, R.BASE + 10, "UP", steps_out=2)
    extinguisher(cv, 828, R.BASE - 6)
    beacon = (R.FRAME[0] + 5, R.FRAME[2] - 4)
    cv.rect(beacon[0] - 2, beacon[1] - 2, 5, 4, "#1a1524"); cv.rect(beacon[0] - 1, beacon[1] - 1, 3, 2, "#a86a1a")
    # light on the wall from the bay lamps and the test
    E.stepped_glow(cv, 500, R.BASE - 30, 150, 30, "#f6cf7a", 0.08, 3)
    return cv, bulbs, leds, utm_screen, spec, beacon, si, stars


def floor_shader(X, Z):
    fl = pal_array(R.CONC_FLOOR)
    cell = hash2(np.floor(X / 120), np.floor(Z / 80), 5)
    rgb = np.where(cell[:, None] < 0.5, fl[4], fl[5]).astype(np.float32)
    fleck = hash2(np.floor(X * 320 / Z), np.floor(16640 / Z), 6)       # aggregate: one-pixel flecks
    rgb[fleck > 0.985] = fl[6]
    rgb[fleck < 0.012] = fl[2]
    # the sealed test zone in front of the reaction wall, edged with a hazard band
    zone = (Z > 600) & (np.abs(X - 40) < 460)
    rgb[zone] = rgb[zone] * 0.82
    band = (Z > 594) & (Z < 604) & (np.abs(X - 40) < 466)
    stripe = (np.floor((X - (Z - 594) * 1.2) / 16) % 2) == 0
    rgb[band] = np.where(stripe[band, None], np.array(C(SAFETY[2])[:3], np.float32), np.array(C("#1a1524")[:3], np.float32))
    # control joints and the grid of tie-down anchors
    jx = np.abs(((X + 65) % 330) - 165) < 1.6
    jz = np.abs(((Z - 40) % 210) - 105) < 1.6
    rgb[(jx | jz) & ~band] = fl[2]
    ax = ((X + 41) % 82) - 41
    az = ((Z - 10) % 60) - 30
    collar = (np.abs(ax) < 7) & (np.abs(az) < 3.2) & (Z < 690) & ~band
    st = pal_array(E.STEEL)
    rgb[collar] = st[4]
    rgb[collar & (az < -1.6)] = st[6]
    rgb[collar & (np.abs(ax) < 3) & (np.abs(az) < 1.4)] = np.array(C("#0c0b12")[:3], np.float32)
    # chalk outlines of earlier tests
    chalk = np.array(C("#d8d4c8")[:3], np.float32)
    for (x0, x1, z0, z1) in ((-640.0, -430.0, 440.0, 520.0), (330.0, 620.0, 470.0, 540.0)):
        dash = (np.floor((X + Z) / 14) % 2) == 0
        edge = (((np.abs(X - x0) < 2) | (np.abs(X - x1) < 2)) & (Z > z0) & (Z < z1)) | \
               (((np.abs(Z - z0) < 2.4) | (np.abs(Z - z1) < 2.4)) & (X > x0) & (X < x1))
        m = edge & dash
        rgb[m] = rgb[m] * 0.6 + chalk * 0.4
    # walkway to the stair on the right and gauge leads along the wall foot
    yel = np.array(C(SAFETY[2])[:3], np.float32)
    wear = hash2(np.floor(X / 4), np.floor(Z / 10), 8) < 0.85
    for lx in (560.0, 700.0):
        m = (np.abs(X - lx) < 3) & (Z < 690) & wear
        rgb[m] = rgb[m] * 0.25 + yel * 0.75
    lead = (np.abs(Z - 686) < 2.2) & (X > -650) & (X < -60)
    rgb[lead] = np.array(C("#2a2a34")[:3], np.float32)
    # the two foundations: painted rings, bolted bearing plates
    for (px, pz) in PADS:
        d = np.hypot((X - px) / 52, (Z - pz) / 30)
        rgb[(d < 1.0) & (d > 0.82)] = rgb[(d < 1.0) & (d > 0.82)] * 0.3 + yel * 0.7
        rgb[d <= 0.82] = fl[6]
        plate = (np.abs(X - px) < 30) & (np.abs(Z - pz) < 12)
        rgb[plate] = st[4]
        rgb[plate & (Z > pz + 8)] = st[6]
        rgb[plate & ((np.abs(X - px) > 27) | (np.abs(Z - pz) > 10))] = st[2]
        bolt = plate & (np.abs(np.abs(X - px) - 21) < 2.5) & (np.abs(np.abs(Z - pz) - 6) < 2)
        rgb[bolt] = st[2]
        core = (np.abs(X - px) < 8) & (np.abs(Z - pz) < 4)
        rgb[core] = st[3]
    # light: bay lamps, the lit foundations, the frame
    for (lx, lz, r, s) in ((-420.0, 560.0, 240.0, 0.16), (330.0, 640.0, 220.0, 0.14), (20.0, 690.0, 200.0, 0.18)):
        warm_light(rgb, np.hypot(X - lx, (Z - lz) * 1.4), r, colour="#f6e0a8", strength=s)
    for (px, pz) in PADS:
        warm_light(rgb, np.hypot(X - px, (Z - pz) * 1.6), 120, colour="#f6cf7a", strength=0.36)
    out = rgba_of(rgb)
    fog(out, Z, FOG, 520, Z_BACK + 60, amount=0.38)
    return out


def ceiling_shader(X, Z):
    return I.beam_ceiling_shader(X, Z, bay_z=140.0, bay_x=220.0, z0=300.0, fog_to=Z_BACK)


def layout_panel(w, h):
    """The board-layout half of the big display: a dark green board, gold traces in pairs with
    vias, one differential pair highlighted cyan with its return path dashed beneath it.
    Returns the canvas and the highlighted trace's polyline (panel px)."""
    cv = Canvas(w, h, fill=I.PCB[0])
    for gx in range(0, w, 6):
        for gy in range(0, h, 6):
            cv.px(gx, gy, I.PCB[1])
    # background nets
    for k, yy in enumerate(range(4, h - 2, 6)):
        if abs(yy - h // 2) < 5:
            continue
        x0 = 2 + (k * 7) % 11
        jog = x0 + 20 + (k * 13) % 30
        cv.hline(x0, yy, jog - x0, I.GOLD[1]); cv.line(jog, yy, jog + 3, yy + (2 if k % 2 else -2), I.GOLD[1])
        cv.hline(jog + 3, yy + (2 if k % 2 else -2), w - jog - 6, I.GOLD[1])
        cv.px(x0, yy, I.GOLD[3]); cv.px(w - 4, yy + (2 if k % 2 else -2), I.GOLD[3])
    for (cx, cy) in ((w // 3, 8), (2 * w // 3, h - 9)):
        cv.rect(cx - 6, cy - 4, 12, 8, "#14141a"); cv.hline(cx - 6, cy - 4, 12, "#30303a")
        for k in range(-5, 6, 2):
            cv.px(cx + k, cy - 5, I.GOLD[2]); cv.px(cx + k, cy + 4, I.GOLD[2])
    # the highlighted pair: SMA launch on the left, a via transition, out to the right edge
    mid = h // 2
    pts = [(3, mid - 1), (w // 2 - 6, mid - 1), (w // 2 - 2, mid - 5), (w // 2 + 10, mid - 5), (w // 2 + 14, mid - 1), (w - 4, mid - 1)]
    for off, col in ((0, I.TRACE_CY[3]), (3, I.TRACE_CY[3])):
        for a, b in zip(pts, pts[1:]):
            cv.line(a[0], a[1] + off, b[0], b[1] + off, col)
    for a, b in zip(pts, pts[1:]):                                    # return path, dashed below
        E.dashed(cv, a[0], a[1] + 7, b[0], b[1] + 7, I.TRACE_YE[2], 2, 2)
    for (vx, vy) in ((w // 2 - 2, mid - 5), (w // 2 + 10, mid - 5)):
        cv.rect(vx - 1, vy - 1, 3, 3, I.GOLD[3]); cv.px(vx, vy, I.PCB[0])
    cv.rect(0, mid - 3, 4, 8, I.GOLD[2])
    micro = "NET D+/D-"
    E.micro_text(cv, micro, 3, h - 7, I.TRACE_CY[2])
    return cv, pts


def big_display(cv):
    """The hanging SI display, painted 1:1: drop rods to the ceiling, bezel, a header bar, the eye
    diagram panel and the layout panel. Returns the eye area and the layout trace (screen px)."""
    x, y, w, h = BIG
    for rx in (x + 30, x + w - 30):
        cv.rect(rx, 0, 2, y, E.STEEL[3]); cv.vline(rx, 0, y, E.STEEL[5])
    cv.rect(x - 3, y - 2, w + 6, h + 5, E.OUT); cv.rect(x - 2, y - 1, w + 4, h + 3, "#2a2c36"); cv.hline(x - 2, y - 1, w + 4, "#4a4c58")
    cv.rect(x, y + 1, w, h - 1, I.SCREEN_BG)
    cv.rect(x, y + 1, w, 8, "#0e2230")
    E.micro_text(cv, "EYE  2.5 GB/S", x + 4, y + 2, I.TRACE_CY[3])
    E.micro_text(cv, "LAYOUT", x + 162, y + 2, I.TRACE_YE[3])
    ew = 152
    eye = (x + 2, y + 10, ew, h - 12)
    cv.paste(I.si_screen_frame(eye[2], eye[3], 0, 8, "eye"), eye[0], eye[1])
    cv.vline(x + ew + 4, y + 9, h - 9, "#2a2c36")
    lp, pts = layout_panel(w - ew - 8, h - 12)
    lx, ly = x + ew + 6, y + 10
    cv.paste(lp, lx, ly)
    cv.rect(x + w - 10, y + h + 3, 6, 2, "#3cba7a")
    return eye, [(lx + px, ly + py) for (px, py) in pts]


def cart_sprite():
    """The midground scope cart, painted at screen scale; returns (canvas, screen rect in it)."""
    sp = Canvas(50, 72)
    scr = I.scope_cart(sp, 6, 71, 40, seed=12)
    return sp, scr


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    v = View(horizon=98, cam=52, fill="#12121c")
    v.ground(floor_shader)
    v.ground(ceiling_shader, y_from=0, y_to=v.h0, height=R.BASE * K)
    wall, bulbs, leds, utm_screen, spec, beacon, si, stars = back_wall()
    v.sprite(wall.a, 0.0, Z_BACK, anchor=(0.5, R.BASE / HC), scale=K)
    gy = v.ground_y(Z_BACK)
    to_screen = lambda p: [int(round(320 + (p[0] - R.W / 2) * S_BACK)), int(round(gy - (R.BASE - p[1]) * S_BACK))]
    v.rows(156, 360, INK, 0.0, 0.62)
    cv = v.reduce(112)

    # crisp: the load display's screen at 1:1 (its frames animate on top)
    dx, dy, dw, dh = DISPLAY
    a = to_screen((dx, dy))
    b = to_screen((dx + dw, dy + dh))
    sw, sh = b[0] - a[0], b[1] - a[1]
    n = 10
    first = E.load_curve_frame(sw, sh, n - 1, n)
    cv.a[a[1]:a[1] + sh, a[0]:a[0] + sw] = first.a
    # the hanging SI display, and its glow on the ceiling and floor
    bx, by, bw, bh = BIG
    halo(cv, bx + bw // 2, by + bh // 2, 150, "#4ab8d8", 0.05, 3)
    eye, trace = big_display(cv)
    # the scope cart between the party and the professor, cables trailing over the floor
    cart, scr = cart_sprite()
    cx0, cfloor = CART
    cy0 = cfloor - cart.h
    E.stepped_glow(cv, cx0 + 25, cfloor, 30, 4, "#0a0910", 0.4, 2)
    cv.paste(cart, cx0, cy0)
    cscr = (cx0 + scr[0], cy0 + scr[1], scr[2], scr[3])
    cv.paste(I.si_screen_frame(cscr[2], cscr[3], 0, 6, "ring"), cscr[0], cscr[1])
    for (pts, kind) in (([(cx0 + 12, cfloor - 2), (cx0 - 10, cfloor + 8), (cx0 - 46, cfloor + 12), (cx0 - 70, cfloor + 26)], "probe"),
                        ([(cx0 + 40, cfloor - 2), (cx0 + 58, cfloor + 10), (cx0 + 70, cfloor + 30), (cx0 + 96, cfloor + 38)], "sma"),
                        ([(cx0 + 30, cfloor - 1), (cx0 + 38, cfloor + 16), (cx0 + 30, cfloor + 34)], "blue")):
        col, hi = I.CABLE[kind]
        E.floor_cord(cv, pts, colour=col, hi=hi)
    I.ring_coil(cv, cx0 + 74, cfloor + 20, 7, I.CABLE["sma"][0], I.CABLE["sma"][1])
    cv.save(os.path.join(out, "battle-far.png"))

    layers = []
    seq = list(range(n)) + [n - 1] * 4
    for k in range(n):
        fr = E.load_curve_frame(sw, sh, k, n)
        fr.save(os.path.join(out, f"battle-load-{k}.png"))
        layers.append({"kind": "blink", "pattern": "".join("1" if s == k else "0" for s in seq), "rate": 3.0,
                       "texture": res + f"battle-load-{k}.png", "x": a[0], "y": a[1]})
    # the eye diagram shimmering, the cart scope ringing, the bench scope's eye
    bench = si["screen"]
    bs0, bs1 = to_screen((bench[0], bench[1])), to_screen((bench[0] + bench[2], bench[1] + bench[3]))
    for name, rect, kind, m, rate in (("battle-eye", eye, "eye", 8, 5.0), ("battle-ring", cscr, "ring", 6, 4.0),
                                      ("battle-bench", (bs0[0], bs0[1], bs1[0] - bs0[0], bs1[1] - bs0[1]), "eye", 4, 3.0)):
        rx, ry, rw, rh = rect
        for k in range(m):
            fr = I.si_screen_frame(rw, rh, k, m, kind, grid=rw > 30)
            fr.save(os.path.join(out, f"{name}-{k}.png"))
            layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(m)), "rate": rate,
                           "texture": res + f"{name}-{k}.png", "x": rx, "y": ry})
    # a pulse running down the highlighted pair, a dimmer echo on its return path
    segs = list(zip(trace, trace[1:]))
    steps = []
    for (p0, p1) in segs:
        L = max(abs(p1[0] - p0[0]), abs(p1[1] - p0[1]))
        for j in range(0, L, 4):
            t = j / max(1, L)
            steps.append((int(round(p0[0] + (p1[0] - p0[0]) * t)), int(round(p0[1] + (p1[1] - p0[1]) * t))))
    m = len(steps)
    for k, (px_, py_) in enumerate(steps):
        layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(m + 4)), "rate": 9.0,
                       "rects": [[px_ - 1, py_ - 1, 3, 5, "e4fcff"], [px_ - 3, py_ - 2, 7, 7, "4ab8d8", 0.3],
                                 [px_ - 1, py_ + 7, 3, 1, "fff4b0", 0.7]]})
    # the near crane hook swinging gently on its falls
    hs = v.scale(HOOK[1])
    hx = int(round(320 + HOOK[0] * hs))
    drop = 84
    offsets = [-3, -2, -1, 0, 1, 2, 3]
    hseq = [0, 1, 2, 3, 4, 5, 6, 6, 5, 4, 3, 2, 1, 0]
    for k, d in enumerate(offsets):
        fr = E.big_hook_frame(drop, d)
        fr.save(os.path.join(out, f"battle-hook-{k}.png"))
        layers.append({"kind": "blink", "pattern": "".join("1" if s == k else "0" for s in hseq), "rate": 4.0,
                       "texture": res + f"battle-hook-{k}.png", "x": hx - fr.w // 2, "y": 0})
    # the lit foundations breathing, with a faint column of light over each
    glow = E.glow_sprite(48, 9, "#f6cf7a", (0.08, 0.16, 0.28, 0.42))
    glow.save(os.path.join(out, "battle-pad-glow.png"))
    for i, (px, pz) in enumerate(PADS):
        s = v.scale(pz)
        sx, sy = int(round(320 + px * s)), int(round(v.ground_y(pz)))
        pat = "1111111000" if i == 0 else "1110001111"
        layers.append({"kind": "blink", "pattern": pat, "rate": 2.4, "texture": res + "battle-pad-glow.png",
                       "x": sx - 48, "y": sy - 9})
        layers.append({"kind": "blink", "pattern": pat, "rate": 2.4,
                       "rects": [[sx - 14, sy - 70, 29, 68, "f6cf7a", 0.05], [sx - 7, sy - 70, 15, 68, "f6cf7a", 0.06]]})
    # DAQ LEDs in a slow chase, the testing machine's screen, the frame beacon
    groups = [leds[0::3], leds[1::3], leds[2::3]]
    for g, pat in zip(groups, ("100", "010", "001")):
        pts = []
        for (x, y, c) in g:
            p = to_screen((x, y))
            pts.append([p[0], p[1], 1, 1, c.lstrip("#")])
        layers.append({"kind": "blink", "pattern": pat, "rate": 2.5, "rects": pts})
    us = to_screen((utm_screen[0] + 1, utm_screen[1] + 2))
    bp = to_screen(beacon)
    sp = to_screen(spec)
    bulb_pts = []
    for (x, y) in bulbs:
        p = to_screen((x, y))
        bulb_pts.append([p[0], p[1], "fff0c4", 2])
    star_pts = []
    for (x, y, c) in stars:
        p = to_screen((x, y))
        star_pts.append([p[0], p[1], c.lstrip("#"), 1])
    layers += [
        {"kind": "blink", "pattern": "10", "rate": 1.0, "rects": [[us[0], us[1], 5, 1, "7ae0a0"]]},
        {"kind": "blink", "pattern": "1000", "rate": 3.0, "rects": [[bp[0] - 1, bp[1] - 1, 3, 2, "ffc040"],
                                                                     [bp[0] - 6, bp[1] - 6, 13, 12, "ffc040", 0.18]]},
        {"kind": "twinkle", "points": bulb_pts, "rate": 0.8, "min": 0.75},
        {"kind": "twinkle", "points": star_pts, "rate": 1.3, "min": 0.2},
        # the display's power LED, concrete grit trickling off the loaded specimen, dust in the lamp light
        {"kind": "blink", "pattern": "1110", "rate": 1.0, "rects": [[bx + bw - 10, by + bh + 3, 6, 2, "7ae0a0"]]},
        {"kind": "particles", "style": "dust", "count": 5, "rect": [sp[0] - 18, sp[1], 36, gy - sp[1]], "speed": [0, -7],
         "color": "c8beb0"},
        {"kind": "particles", "style": "dust", "count": 18, "rect": [40, 48, 560, 100], "speed": [2, 3], "color": "f6e0a8"},
    ]
    return {"far": res + "battle-far.png", "layers": layers}


if __name__ == "__main__":
    import json
    print(json.dumps(build(paths.PROJECT))[:300])
