"""E05 Control booth / the recording nobody made (800x480).

The structures lab's control booth, up beside the model level, in the Engineering Center's raw
fabric: board-formed concrete walls (plank grain, form-tie holes, run-off streaks) with wedge-foam
acoustic panels set into them in steel frames, a Lyons sandstone base course, a coffered concrete
ceiling with can lights fixed under its edge beam. A long observation window looks out at the suspended
model hanging in the dark bay. The main status screen (where the old drawing printed SOURCE
RECOVERED) plays a waveform until the source reel is found; a wall reel-to-reel turns, LED meters
dance and the REC lamp blinks while "the recording nobody made" runs. The recording console holds
the source reel (prop 0, a flag texture shows the empty spindle once `source_reel` is set); the
LAST CALL rack holds the booth log; the tape archive has one gap. In the near wall: the door back
to the model level (left) and the service lift to the loading court (right), its scissor gate
closed until `bridge_ready`.
"""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel import Canvas, C, text  # noqa: E402
from lib_umc import halo, SHADOW, SAFETY, hazard_band  # noqa: E402
from lib_norlin2 import reel_face  # noqa: E402
import lib_eng as E  # noqa: E402
import ec_interior as I  # noqa: E402

ROOM = "E05"
W, H = 800, 480
BASE = 142
FRONT = 456
WINDOW = (30, 26, 304, 78)
SCREEN = (370, 47, 172, 66)        # where the old drawing put the booth screen
DECK = (572, 26)
METER = (662, 28)
REC_AT = (698, 28)
PATCH = (662, 82)
DOOR_L = (34, 96)
LIFT = (694, 756)
LAMP = (125, 349)
CEIL = 18                          # underside of the concrete edge beam
FOAM = ((348, 26, 214, 82), (570, 24, 222, 84))   # acoustic panels set into the concrete
CANS = (60, 180, 300, 420, 540, 660, 780)


def paint_fabric(cv, x0=0, w=W, seed=71):
    """Coffered concrete ceiling with cans, the board-formed wall, foam panels set into it, the
    sandstone base course. Returns the can points."""
    I.coffered_ceiling(cv, x0, w, 0, CEIL, seed=seed, bay=40, rib=5)
    cans = I.beam_cans(cv, [c for c in CANS if x0 <= c < x0 + w], CEIL - 2)
    I.board_concrete(cv, x0, CEIL, w, 112 - CEIL, seed=seed + 1, board=6, lift=46, foot=0)
    for k, (fx, fy, fw, fh) in enumerate(FOAM):
        if x0 <= fx < x0 + w:
            I.foam_panel(cv, fx, fy, fw, fh, seed=seed + 2 + k)
    I.lyons_wall(cv, x0, 112, w, BASE - 112, seed=seed + 4)
    E.tint_rect(cv, x0, 116, w, BASE - 116, SHADOW, 0.14)          # the booth is dim down low
    return cans


def paint_back(bg):
    cans = paint_fabric(bg)
    # the observation window set deep in the concrete, its frame steel
    x, y, w, h = WINDOW
    I.deep_window(bg, x, y, w, h, seed=72, depth=9, sky=False, mullion=False)
    model_pts, beacon = E.observation_window(bg, *WINDOW, seed=72)
    I.reframe(bg, x - 3, y - 3, w + 6, h + 8, {E.WAINSCOT[1]: E.STEEL[1], E.WAINSCOT[3]: E.STEEL[3], E.WAINSCOT[4]: E.CONC[7]})
    trace = E.status_screen(bg, *SCREEN)
    E.studio_monitor(bg, 346, 52)
    E.studio_monitor(bg, 548, 52, flip=True)
    reels, rr = E.wall_tape_deck(bg, DECK[0], DECK[1], 80, 56)
    for (cx, cy) in reels:
        bg.paste(reel_face(rr, 0.3, 0.55), cx - rr - 1, cy - rr - 1)
    bars = E.led_meter(bg, METER[0], METER[1], 4, 30)
    rec = E.lightbox(bg, REC_AT[0], REC_AT[1], "REC", lit=False)
    E.wall_clock(bg, 760, 40, 7)
    E.patch_bay(bg, PATCH[0], PATCH[1], 116, 3, seed=7)
    # a quiet sign, cable trays, outlets
    bg.rect(232, 114, 64, 11, "#1a1524"); bg.rect(233, 115, 62, 9, "#2a2630"); E.micro_text(bg, "QUIET PLEASE", 236, 117, "#e8c87a")
    I.conduit(bg, 340, 796, 109, boxes=[(566, 100)])
    return cans, model_pts, beacon, trace, reels, rr, bars, rec


def paint_floor(bg):
    fh = FRONT - BASE
    E.put_rgb(bg, 0, BASE, E.carpet_np(W, fh, seed=73))
    bg.hline(0, BASE, W, "#0e0c12"); bg.hline(0, BASE + 1, W, C(SHADOW, 0.4))
    # a round braided rug by the lamp (the save spot), a darker rug under the console, a cable cover
    for k, (rx, ry, col) in enumerate(((64, 20, "#3a2a34"), (60, 18, "#54383a"), (36, 10, "#5c4040"))):
        bg.ellipse(LAMP[0] - rx, LAMP[1] + 6 - ry, 2 * rx + 1, 2 * ry + 1, col)
    bg.rect(290, 262, 260, 104, C("#12141e", 0.55))
    bg.rect(292, 264, 256, 100, C("#3a2c4a", 0.35))
    for k in range(0, 256, 8):
        bg.px(292 + k, 264, C("#8a6a9a", 0.5)); bg.px(292 + k, 363, C("#8a6a9a", 0.5))
    pts = [(540, 300), (600, 280), (622, 238)]
    for (a, b) in zip(pts, pts[1:]):
        for d in range(-3, 4):
            bg.line(a[0], a[1] + d, b[0], b[1] + d, E.STEEL[3] if abs(d) < 3 else SAFETY[2])
    # tape scraps and a dropped leader on the carpet
    bg.line(470, 390, 486, 386, "#5a3a28"); bg.line(486, 386, 492, 392, "#5a3a28")
    bg.rect(200, 300, 8, 6, E.PAPER[3]); E.scribble(bg, 201, 302, 6, "#5a5a6a", 2, rows=1)
    # service lift approach: hazard edge and stencil
    hazard_band(bg, LIFT[0], FRONT - 6, LIFT[1] - LIFT[0], 4)
    E.big_stencil(bg, "LIFT", LIFT[0] + 7, FRONT - 34, SAFETY[2], 0.35, scale=2)


def paint_near_wall(bg):
    E.front_wall(bg, FRONT, W, H - FRONT, gaps=(DOOR_L, LIFT))
    E.door_gap(bg, DOOR_L[0], DOOR_L[1], FRONT, H - FRONT, outside="lit")
    # the lift car: steel plate floor, side rails, the gate folded open (an overlay closes it)
    x0, x1 = LIFT
    bg.rect(x0, FRONT, x1 - x0, H - FRONT, E.DECK[3])
    for yy in range(FRONT + 3, H, 5):
        for xx in range(x0 + 2 + (yy // 5 % 2) * 3, x1 - 2, 6):
            bg.hline(xx, yy, 2, E.DECK[5])
    bg.rect(x0, FRONT, x1 - x0, 3, E.STEEL[5]); bg.hline(x0, FRONT, x1 - x0, E.STEEL[7])
    gate = E.lift_gate(x1 - x0, H - FRONT - 4, closed=False)
    bg.paste(gate, x0, FRONT + 4)
    for jx, lit_side in ((x0 - 5, 0), (x1, 4)):
        bg.rect(jx, FRONT, 5, H - FRONT, E.CONC[2]); bg.vline(jx + lit_side, FRONT, H - FRONT, E.CONC[5]); bg.rect(jx, FRONT, 5, 2, E.CONC[6])
    E.tint_rect(bg, x0, FRONT, x1 - x0, H - FRONT, "#f6e0a8", 0.08)
    # side walls
    for xs in (0, W - 20):
        bg.rect(xs, BASE, 20, FRONT - BASE, "#14121a")
        for yy in range(BASE + 8, FRONT, 8):
            bg.hline(xs, yy, 20, "#1a1822")
    bg.vline(19, BASE, FRONT - BASE, E.CONC[3]); bg.vline(W - 20, BASE, FRONT - BASE, E.CONC[3])


def paint_lights(bg, cans):
    for (x, y) in cans:
        E.stepped_glow(bg, x, BASE + 8, 40, 8, "#f6cf7a", 0.07, 2)
    x, y, w, h = SCREEN
    halo(bg, x + w // 2, y + h // 2, 110, "#7ae0a0", 0.04, 3)
    E.stepped_glow(bg, x + w // 2, BASE + 12, 90, 14, "#7ae0a0", 0.06, 2)
    E.stepped_glow(bg, LAMP[0], LAMP[1] - 2, 58, 15, "#f6cf7a", 0.18, 3)
    E.stepped_glow(bg, 420, 350, 120, 22, "#f6cf7a", 0.07, 2)
    E.stepped_glow(bg, (LIFT[0] + LIFT[1]) // 2, FRONT - 6, 40, 14, "#f6e0a8", 0.08, 2)
    E.stepped_glow(bg, sum(DOOR_L) // 2, FRONT - 6, 40, 14, "#f6cf7a", 0.08, 2)


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=5)

    cans, model_pts, beacon, trace, reels, rr, bars, rec = paint_back(bg)
    paint_floor(bg)
    paint_near_wall(bg)
    paint_lights(bg, cans)
    bg.save(os.path.join(out, "background.png"))

    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    taken, _, _ = E.console_reel(220, 60, reel=False, seed=1)
    taken.save(os.path.join(out, "prop-0-taken.png"))
    save(0, E.console_reel(220, 60, reel=True, seed=1), {"flag": "source_reel", "flag_texture": res + "prop-0-taken.png"})
    save(1, E.log_rack(110, 94, "LAST CALL", seed=2))
    save(2, E.tape_archive(110, 100, seed=3))
    save(3, E.drum_floor_lamp(68))

    on = Canvas(rec[2], rec[3])
    E.lightbox(on, 0, 0, "REC", lit=True)
    on.save(os.path.join(out, "rec-on.png"))
    layers = []
    # the recording nobody made: a scrolling waveform until the source is recovered
    tx, ty, tw, th = trace
    n = 8
    for k in range(n):
        fr = E.wave_frame(tw, th, k, n, seed=5)
        fr.save(os.path.join(out, f"wave-{k}.png"))
        layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(n)), "rate": 6.0,
                       "texture": res + f"wave-{k}.png", "x": tx, "y": ty, "flag": "source_reel", "when": False})
    card = E.recovered_card(SCREEN[2], SCREEN[3] - 11)
    card.save(os.path.join(out, "source-recovered.png"))
    # the wall deck's reels turning while it plays
    m = 4
    for k in range(m):
        fr = reel_face(rr, 0.3 + k * 0.5236, 0.55)
        fr.save(os.path.join(out, f"reel-{k}.png"))
        for (cx, cy) in reels:
            layers.append({"kind": "blink", "pattern": "".join("1" if i == k else "0" for i in range(m)), "rate": 8.0,
                           "texture": res + f"reel-{k}.png", "x": cx - rr - 1, "y": cy - rr - 1,
                           "flag": "source_reel", "when": False})
    # LED meters: each bar's segments light in three bands with offset patterns
    pats = ["1111111111", "1101111011", "0100110010"]
    for b, (bx, by, bw, bh) in enumerate(bars):
        for band, (y0, y1, col) in enumerate(((by + 2 * bh // 3, by + bh, "3cba7a"), (by + bh // 3, by + 2 * bh // 3, "e8b45c"),
                                              (by, by + bh // 3, "ff5a4a"))):
            rects = [[bx, sy, 4, 2, col] for sy in range(by, by + bh, 3) if y0 <= sy < y1]
            pat = pats[band][b * 2:] + pats[band][:b * 2]
            layers.append({"kind": "blink", "pattern": pat, "rate": 7.0, "rects": rects})
    layers += [
        {"kind": "blink", "pattern": "1100", "rate": 1.2, "flag": "source_reel", "when": False,
         "texture": res + "rec-on.png", "x": rec[0], "y": rec[1]},
        {"kind": "blink", "pattern": "1100", "rate": 1.2, "flag": "source_reel", "when": False,
         "rects": [[rec[0] - 6, rec[1] - 6, rec[2] + 12, rec[3] + 12, "ff5a4a", 0.10]]},
        {"kind": "blink", "pattern": "10", "rate": 0.8, "flag": "source_reel",
         "rects": [[SCREEN[0] + SCREEN[2] - 26, SCREEN[1] + 3, 20, 5, "0c1a14"]]},
        {"kind": "twinkle", "points": [[x, y, "f6cf7a", 1] for (x, y) in model_pts], "rate": 1.1, "min": 0.4},
        {"kind": "blink", "pattern": "100000", "rate": 3.0, "rects": [[beacon[0] - 1, beacon[1], 3, 2, "ffc040"]]},
        {"kind": "twinkle", "points": [[x, y, "fff0c4", 1] for (x, y) in cans] + [[LAMP[0], LAMP[1] - 62, "fff0c4", 2]],
         "rate": 0.9, "min": 0.8},
        {"kind": "particles", "style": "dust", "count": 5, "rect": [60, 230, 140, 90], "speed": [1, -2], "color": "f6dca0"},
    ]

    gate = E.lift_gate(LIFT[1] - LIFT[0], H - FRONT - 4, closed=True)
    gate.save(os.path.join(out, "lift-gate.png"))

    manifest = {
        "background": res + "background.png",
        "width": W,
        "props": props,
        "label_only": [],
        "occluders": [],
        "overlays": [
            {"texture": res + "source-recovered.png", "x": SCREEN[0], "y": SCREEN[1] + 11, "flag": "source_reel"},
            {"texture": res + "lift-gate.png", "x": LIFT[0], "y": FRONT + 4, "flag": "bridge_ready", "when": False},
        ],
        "fauna": [
            {"kind": "lamp_moth", "x": LAMP[0] + 1, "y": LAMP[1] - 66, "range": 7, "speed": 1.8, "rate": 9.0},
        ],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
