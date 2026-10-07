"""The Farrand main stage up close and the pieces around it (rooms F04 audience lawn, F05 backstage,
F06 main stage), painted at 1:1 game pixels in the style of lib_farrand.py, which it builds on.

The stage is the one the other Farrand rooms see far off (lib_farrand.distant_stage): an arched black
truss roof hung with lamps, a back drape washed in stepped violet-to-coral light, an LED wall
showing two violet peaks, PA line arrays hanging at the front corners, scaffold wing towers, a
warm-lit deck edge over a dark slatted skirt.

Stage:       main_stage (back structure + deck surface, returns the points to animate), roof_arch,
             truss_band, stage_lamp, scaffold_tower, line_array, drape_wall, led_screen (kinds:
             mountains, again, goodnight, off), stage_banner, stage_deck, amp_stack, drum_riser,
             keys_stand, mic_stand, guitar_on_stand, deck_stairs, stage_front (the deck lip prop:
             face, wedges, mic, setlist, footlights; lamps/leds off and a dim lip for after the show)
Audience:    chair_row (wooden folding chairs seen from behind, things left on them), sub_stack
             (ground PA, its LED off with on=False), ghost_light (bare bulb in a cage on a stand),
             delay_tower (lattice mast with a PA hang and lamp bar), picnic_blanket, confetti,
             glow_stick, crew_gate (the gated gap in the side fence, returns its lamp points)
Backstage:   stage_back (the stage's scaffold-and-scrim upstage side seen from the crew road: LED
             back bay, wing opening, running lights, SHOW ON box), trackway (ribbed ground
             panels), cable_loom, road_case, gear_rack (steel shelving with cases), case_stack,
             prep_table (Imani's table and EVERYONE PERFORMS poster; chosen=True shows CHOOSES),
             cue_board (ONE SONG cue sheet; stop=True strikes AGAIN and adds STOP), work_light
             (tripod flood), portacabin, generator, scrim_fence (fence panels clad in black scrim),
             cue_light (red/green stage cue lamp), rug (the green room's rug on the grass)
Far:         campus_far (Norlin's red roof, arched lit windows and portico past the trees, returns
             the window points), sky_east (the dusk sky looking away from the Flatirons: belt of
             Venus over the earth shadow, optional rising moon)
Palettes:    WASH (back drape bands, dark top to warm bottom), DECK, TRUSS, LED, SCRIM, CASE,
             CABIN, LAMP_COLOURS, SKIRT, LIP, TRACK
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, WOOD, AMBER, ground_shadow
import lib_farrand as F

# --- palettes -------------------------------------------------------------------------------
WASH = ["#2e1c3c", "#3c2248", "#4e2852", "#62305c", "#7a3862", "#944468", "#ac506c", "#c05e6e", "#d06e6e"]
DECK = ["#1a1520", "#241d2a", "#2f2635", "#3a2f40", "#45384a", "#544555", "#685866"]
TRUSS = ["#0f0d15", "#16141e", "#211e2b", "#2e2a3a", "#3f3a4e", "#575066", "#787088"]
LED = ["#120c1c", "#22184a", "#2c2460", "#3a3070", "#4a3e88", "#6a5aa8", "#8a7ac8", "#b8a8e8"]
SCRIM = ["#0f0e15", "#16141e", "#1d1a26", "#25212f", "#2f2a3a"]
CASE = ["#121018", "#1c1a24", "#2a2832", "#3a3844", "#55525e", "#8a8894", "#c8c8d0"]
CABIN = ["#2a2a34", "#3e4048", "#5a5c62", "#7a7c7e", "#9a9a96", "#b8b6ae", "#d2cec2"]
LAMP_COLOURS = ["#fff0c4", "#ffd0e8", "#fff0c4", "#c8b0ff", "#fff0c4", "#ffb8a0"]
SKIRT = ["#140e16", "#1c121c", "#24182a", "#2e2034"]
LIP = ["#7a4a24", "#c47a2c", "#e9a84a", "#f6cf7a"]
WIRE = F.WIRE


def _rng(seed):
    return np.random.default_rng(abs(int(seed)))


# --- roof and lamps ---------------------------------------------------------------------------
def roof_arch(x0, x1, top, rise):
    """y of the roof truss's top chord at x: a shallow arch, highest (top) in the middle."""
    def y(x):
        t = (x - x0) / max(1, x1 - x0)
        return int(round(top + rise * (2 * t - 1) ** 2))
    return y


def truss_band(cv, x0, x1, arch, depth=11, lit="#4a3448"):
    """The roof's front truss along the arch: top and bottom chords, zigzag lacing with the dark
    roof underside showing through, the membrane edge above, a lit underside line below."""
    for x in range(x0, x1):
        y = arch(x)
        cv.vline(x, y - 3, 3, TRUSS[0])                     # roof membrane edge
        cv.px(x, y - 3, TRUSS[2])
        cv.vline(x, y, depth, TRUSS[1])                     # underside seen through the lacing
        cv.px(x, y, TRUSS[5]); cv.px(x, y + 1, TRUSS[3])    # top chord
        cv.px(x, y + depth - 2, TRUSS[4]); cv.px(x, y + depth - 1, TRUSS[2])   # bottom chord
        cv.px(x, y + depth, lit)                            # stage light catching the underside
    # lacing: diagonals between the chords, every 8 px
    for x in range(x0 + 2, x1 - 6, 8):
        ya, yb = arch(x), arch(x + 4)
        for k in range(depth - 4):
            cv.px(x + k * 4 // (depth - 4), ya + 2 + k, TRUSS[3])
            cv.px(x + 4 + k * 4 // (depth - 4), yb + depth - 3 - k, TRUSS[3])
        cv.vline(x, ya + 2, depth - 4, TRUSS[2])


def stage_lamp(cv, x, y, colour="#fff0c4", kind="par", on=True):
    """A lamp hung under the truss at (x, y) (top of its clamp): a par can or a moving head.
    Returns the lens point (centre of the lit face)."""
    cv.rect(x - 1, y, 3, 2, TRUSS[0])                       # clamp
    if kind == "head":
        cv.rect(x - 4, y + 2, 9, 2, OUT); cv.hline(x - 3, y + 2, 7, TRUSS[4])     # yoke
        cv.rect(x - 4, y + 4, 2, 4, OUT); cv.rect(x + 3, y + 4, 2, 4, OUT)
        cv.rect(x - 2, y + 4, 5, 6, OUT); cv.rect(x - 1, y + 5, 3, 3, TRUSS[3])
        lens = (x, y + 9)
        cv.rect(x - 1, y + 8, 3, 2, colour if on else TRUSS[3])
        if on:
            cv.px(x, y + 8, "#ffffff")
    else:
        cv.rect(x - 2, y + 2, 5, 7, OUT); cv.vline(x - 1, y + 3, 5, TRUSS[4]); cv.vline(x + 1, y + 3, 5, TRUSS[2])
        cv.rect(x - 2, y + 9, 5, 2, colour if on else TRUSS[3])
        if on:
            cv.px(x, y + 9, "#ffffff")
        lens = (x, y + 10)
    if on:
        cv.rect(x - 3, y + 8, 7, 5, C(colour, 0.14))
    return lens


# --- structure --------------------------------------------------------------------------------
def scaffold_tower(cv, x, top, base, w=20, seed=0, scrim_from=None, lamps=2):
    """A scaffold wing tower: two standards with lit edges, ledgers every 14 px, alternating
    braces, base plates on timber sole boards, black scrim tied on below scrim_from, a lamp bar
    on top. Returns the lamp points."""
    rng = _rng(seed)
    for yy in range(top + 6, base - 2, 14):                 # ledgers
        cv.rect(x, yy, w, 2, TRUSS[3]); cv.hline(x, yy, w, TRUSS[5])
    k = 0
    for yy in range(top + 6, base - 14, 14):                # braces
        if k % 2:
            cv.line(x + 2, yy + 2, x + w - 3, yy + 13, TRUSS[4])
        else:
            cv.line(x + w - 3, yy + 2, x + 2, yy + 13, TRUSS[4])
        k += 1
    for sx in (x, x + w - 3):                               # standards
        cv.rect(sx, top, 3, base - top, OUT)
        cv.vline(sx + 1, top, base - top, TRUSS[5]); cv.vline(sx + 2, top, base - top, TRUSS[3])
        for yy in range(top + 6, base - 2, 14):
            cv.rect(sx - 1, yy - 1, 5, 4, TRUSS[2]); cv.px(sx, yy - 1, TRUSS[5])     # couplers
    if scrim_from is not None:
        for yy in range(scrim_from, base - 3):
            for xx in range(x + 3, x + w - 3):
                if (xx + yy) % 2 == 0 or (yy - scrim_from) % 6 == 0:
                    cv.px(xx, yy, SCRIM[1] if (xx // 3) % 2 else SCRIM[2])
        for yy in range(scrim_from + 2, base - 4, 8):       # cable ties
            cv.px(x + 3, yy, "#c8c8d0"); cv.px(x + w - 4, yy + 4, "#c8c8d0")
    cv.rect(x - 4, base - 3, w + 8, 3, OUT); cv.hline(x - 3, base - 3, w + 6, WOOD[3])  # sole board
    cv.rect(x - 4, top - 5, w + 8, 4, OUT); cv.hline(x - 3, top - 4, w + 6, TRUSS[4])  # lamp bar
    pts = []
    for i in range(lamps):
        lx = x + 1 + i * (w - 3) // max(1, lamps - 1)
        cv.rect(lx - 1, top - 8, 4, 3, OUT); cv.rect(lx, top - 7, 2, 2, "#fff0c4")
        pts.append([lx, top - 7])
    return pts


def line_array(cv, x, top, n=8, w=22, box=8, chain=6, lit=True):
    """A PA line array hanging from a bumper: n black boxes curving slightly in (a J), grilles
    with horizontal slots, lit top edges, a status LED on the bottom box. Returns its bottom y."""
    bx = x + 3
    cv.rect(bx - 1, top, w + 2, 3, OUT); cv.hline(bx, top + 1, w, TRUSS[4])            # bumper
    for cx_ in (bx + 3, bx + w - 4):                                                    # chains
        for yy in range(top - chain, top):
            cv.px(cx_, yy, TRUSS[4] if yy % 2 else TRUSS[2])
    y = top + 3
    for i in range(n):
        inset = max(0, i - n + 3)                           # the J: bottom boxes tuck in
        x0 = bx + inset // 2
        ww = w - inset
        cv.rect(x0 - 1, y, ww + 2, box, OUT)
        cv.rect(x0, y, ww, box - 1, TRUSS[1])
        cv.hline(x0, y, ww, TRUSS[4] if lit else TRUSS[3])
        for gy in range(y + 2, y + box - 1, 2):
            cv.hline(x0 + 2, gy, ww - 4, TRUSS[2])
        cv.vline(x0, y + 1, box - 2, TRUSS[3])
        y += box
    cv.px(bx + w // 2, y - 3, "#5cf08a")
    return y


def drape_wall(cv, x0, x1, top_fn, base, pal=WASH, pleat=7, dim=0.0):
    """The stage's back drape washed by the lights: stepped bands from dark violet at the top to
    warm coral at the deck, vertical pleats (a lit fold, a shadow fold), a darker hem."""
    for x in range(x0, x1):
        top = top_fn(x)
        k = (x - x0) % pleat
        lift = 0.06 if k in (1, 2) else -0.12 if k == pleat - 1 else 0.0
        for y in range(top, base):
            t = (y - top) / max(1, base - top)
            c = pal[min(len(pal) - 1, int(t * len(pal)))]
            if lift:
                c = shade(c, lift)
            if dim:
                c = mix(c, "#141223", dim)
            cv.px(x, y, c)
    cv.rect(x0, base - 3, x1 - x0, 3, C("#0d0b16", 0.35))


def led_screen(cv, x, y, w, h, kind="mountains", seed=0):
    """The LED wall: black frame, panel seams every 12 px, a faint pixel grid. kind: 'mountains'
    (two violet peaks under a dusk sky with a moon, as seen from across the field), 'again' (AGAIN
    repeated in red), 'goodnight' (quiet: a crescent and GOODNIGHT), 'off' (dark glass)."""
    rng = _rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT); cv.rect(x - 1, y - 1, w + 2, h + 2, TRUSS[0])
    if kind == "mountains":
        bands = [LED[1], LED[2], LED[3], LED[4]]
        for yy in range(h):
            cv.hline(x, y + yy, w, bands[min(3, yy * 4 // h)])
        for _ in range(w * h // 140):
            cv.px(x + int(rng.integers(1, w - 1)), y + int(rng.integers(1, h // 2)), "#d8d0f0")
        mx, my = x + w * 4 // 5, y + h // 5 + 2
        cv.ellipse(mx - 4, my - 4, 9, 9, "#efe2b8"); cv.ellipse(mx - 1, my - 5, 9, 9, LED[1])
        # two peaks like the distant stage shows: lit west faces, shadowed east faces, snow
        gy = y + h - 6
        for (px_, pw, ph) in [(x + w * 3 // 10, w // 2, h * 13 // 20), (x + w * 13 // 20, w * 2 // 5, h // 2)]:
            cv.poly([(px_ - pw // 2 - 1, gy), (px_, gy - ph - 1), (px_ + pw // 2 + 1, gy)], LED[1])
            cv.poly([(px_ - pw // 2, gy), (px_, gy - ph), (px_ + pw // 2, gy)], LED[5])
            cv.poly([(px_, gy - ph), (px_ + pw // 2, gy), (px_ + pw // 8, gy)], shade(LED[5], -0.22))
            cv.line(px_, gy - ph, px_ - pw // 2 + 1, gy - 1, LED[6])
            for k in range(3):     # strata on the lit face
                cv.line(px_ - 2 - k * 4, gy - ph + 8 + k * 6, px_ - pw // 4 - k * 3, gy - ph // 3 + k * 4, shade(LED[5], 0.12))
            cv.poly([(px_ - 5, gy - ph + 7), (px_, gy - ph), (px_ + 4, gy - ph + 6), (px_ + 1, gy - ph + 4), (px_ - 2, gy - ph + 6)], LED[7])
        cv.rect(x, gy, w, h - (gy - y), LED[2])
        cv.hline(x, gy, w, LED[1])
        for xx in range(x + 2, x + w - 2, 5):
            cv.px(xx, gy + 3, "#e9a84a" if rng.random() < 0.5 else LED[4])
    elif kind == "again":
        cv.rect(x, y, w, h, "#2a0c18")
        rows = max(1, (h - 4) // 11)
        for r in range(rows):
            s = "AGAIN " * 8
            off = (r * 13) % 36
            yy = y + 3 + r * 11
            for i, ch in enumerate(s):
                gx = x + 2 - off + i * 6
                if x <= gx and gx + 6 <= x + w:
                    text(cv, ch, gx, yy, "#f05a5a" if r % 2 == 0 else "#f6a86a")
    elif kind == "goodnight":
        cv.rect(x, y, w, h, LED[1])
        for _ in range(w * h // 90):
            cv.px(x + int(rng.integers(1, w - 1)), y + int(rng.integers(1, h - 12)), "#a8a0d0")
        mx, my = x + w // 2, y + h // 3
        cv.ellipse(mx - 6, my - 6, 13, 13, "#efe2b8"); cv.ellipse(mx - 2, my - 8, 13, 13, LED[1])
        s = "GOODNIGHT"
        text(cv, s, x + w // 2 - text_width(s) // 2, y + h // 2 + 2, "#e6d6b1")
    else:
        cv.rect(x, y, w, h, "#100c16")
        cv.line(x + w // 5, y + h - 2, x + w // 5 + h // 2, y + 1, "#1c1826")
        cv.line(x + w // 5 + 6, y + h - 2, x + w // 5 + 6 + h // 2, y + 1, "#18141f")
    # panel seams and pixel grid
    for xx in range(x + 12, x + w, 12):
        cv.vline(xx, y, h, C("#0a0810", 0.3))
    for yy in range(y + 12, y + h, 12):
        cv.hline(x, yy, w, C("#0a0810", 0.3))
    for xx in range(x + 1, x + w, 3):
        cv.vline(xx, y, h, C("#0a0810", 0.12))


def stage_banner(cv, cx, y, label="LAST LIGHT / ONE FINAL SET", tie_to=None):
    """The cloth banner hung under the truss: cream with a darker hem, red-brown lettering, a
    ragged scalloped bottom edge, ties up to the truss. Returns its rect."""
    w = text_width(label) + 16
    x = cx - w // 2
    h = 13
    if tie_to:
        for (ax, ay), bx in zip(tie_to, (x + 3, x + w - 4)):
            cv.line(ax, ay, bx, y, "#3a2a2a")
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, "#e6d6b1"); cv.hline(x, y, w, "#fff3d6"); cv.hline(x, y + h - 1, w, "#b8a888")
    for sx in range(x, x + w - 1, 12):                      # scallops
        cv.poly([(sx, y + h), (sx + 6, y + h + 3), (sx + 12, y + h)], "#d4c4a0")
        cv.px(sx + 6, y + h + 2, "#b8a888")
    for k in range(3):                                      # cloth creases
        fx = x + 20 + k * (w - 40) // 2
        cv.vline(fx, y + 1, h - 2, C("#b8a888", 0.45))
    cv.px(x + 2, y + 2, "#8a7a6a"); cv.px(x + w - 3, y + 2, "#8a7a6a")   # grommets
    text(cv, label, cx - text_width(label) // 2, y + 2, "#7e3a30")
    return (x, y, w, h)


def stage_deck(cv, x0, x1, y0, y1, seed=0, pools=True, runs=()):
    """The stage floor from the back drape (y0) to the front lip (y1): black-painted deck panels
    with seams and scuffs, spike tape marks, gaffer-taped cable runs (runs: polylines), towels and
    set lists taped down, warm and pink pools of stage light. Flat, so characters can walk on it."""
    rng = _rng(seed)
    cv.rect(x0, y0, x1 - x0, y1 - y0, DECK[3])
    rows, yy = [], y0
    while yy < y1:                                          # panel rows deepen toward the front
        rh = int(round(11 + 8 * (yy - y0) / max(1, y1 - y0)))
        rows.append((yy, min(rh, y1 - yy)))
        yy += rh
    for r, (yy, rh) in enumerate(rows):
        off = 0 if r % 2 == 0 else 32
        for xx in range(x0 - off, x1, 64):
            a, b = max(x0, xx), min(x1, xx + 64)
            if b - a < 2:
                continue
            tone = DECK[3] if rng.random() < 0.55 else DECK[4]
            cv.rect(a, yy, b - a, rh, tone)
            cv.hline(a, yy, b - a, shade(tone, 0.07))
            for _ in range((b - a) * rh // 45):            # scuffs and boot marks
                sx, sy = a + int(rng.integers(0, max(1, b - a - 6))), yy + 1 + int(rng.integers(0, max(1, rh - 2)))
                cv.hline(sx, sy, int(rng.integers(2, 7)), DECK[5] if rng.random() < 0.45 else DECK[2])
            cv.vline(b - 1, yy, rh, DECK[1])
            cv.px(a + 2, yy + 2, DECK[6]); cv.px(b - 3, yy + 2, DECK[6])                # panel bolts
        cv.hline(x0, yy + rh - 1, x1 - x0, DECK[1])
    if pools:
        mid = (x0 + x1) // 2
        F.light_pool(cv, mid, (y0 + y1) // 2 + 6, (x1 - x0) // 5, (y1 - y0) * 2 // 5, "#f6cf7a", 0.36)
        F.light_pool(cv, x0 + (x1 - x0) // 5, (y0 + y1) // 2, (x1 - x0) // 9, (y1 - y0) // 4, "#e88ab8", 0.26)
        F.light_pool(cv, x1 - (x1 - x0) // 5, (y0 + y1) // 2, (x1 - x0) // 9, (y1 - y0) // 4, "#a890f0", 0.26)
    # cable runs taped flat to the deck
    for pts in runs:
        F.cable_run(cv, pts, count=2, seed=seed + len(pts), colours=("#121016", "#1e1a24", "#3a1c22"),
                    tape_every=34, spread=1)
    # spike marks (where each player stands) and a line of tape along the downstage edge
    for i in range(8):
        sx = x0 + 30 + int(rng.integers(0, x1 - x0 - 60))
        sy = y0 + 10 + int(rng.integers(0, max(1, y1 - y0 - 18)))
        c = ["#f05a8a", "#62c47c", "#f2cf5c", "#7ab8f0"][i % 4]
        cv.hline(sx - 2, sy, 5, c); cv.vline(sx, sy - 1, 3, c); cv.px(sx + 2, sy + 1, shade(c, -0.4))
    for xx in range(x0 + 4, x1 - 4, 14):
        cv.hline(xx, y1 - 4, 7, "#d8d4c8"); cv.px(xx + 6, y1 - 3, "#8a8690")
    # a towel dropped by the drum riser, pedalboards by the amps
    tx = (x0 + x1) // 2 - 58
    cv.poly([(tx, y0 + 12), (tx + 14, y0 + 10), (tx + 16, y0 + 16), (tx + 2, y0 + 18)], "#e6e2d8")
    cv.line(tx + 2, y0 + 15, tx + 14, y0 + 13, "#c8c4b8")
    for (px_, py_) in [(x0 + (x1 - x0) // 4 - 14, y0 + 8), (x1 - (x1 - x0) // 4 - 14, y0 + 10)]:
        cv.rect(px_, py_, 26, 6, OUT); cv.rect(px_ + 1, py_ + 1, 24, 3, CASE[2])
        for k in range(4):
            c = ["#c84a3c", "#e0b23a", "#3a62a0", "#4a8a4c"][k]
            cv.rect(px_ + 2 + k * 6, py_ + 1, 4, 3, c); cv.px(px_ + 3 + k * 6, py_ + 1, "#f2f2ee")
        cv.hline(px_, py_ + 6, 26, C("#0d0b16", 0.5))


def stage_front(width=360, face=28, seed=0, wedges=None, mic=True, setlist=True, lamps=True,
                cables=True, lip=LIP, leds=True):
    """The front of the stage deck as a prop: the warm-lit lip (stage light catching the edge),
    the dark slatted skirt with a few footlights, wedge monitors along the edge, a vocal mic on
    its stand at centre front with the set list taped by it. Anchor: bottom centre of the skirt.
    Returns (Canvas, anchor_x, anchor_y, info) with info['lamps'] (footlight points),
    info['mic'] (mic head) and info['wedges'] (status LEDs) in canvas pixels."""
    rng = _rng(seed)
    gear_h = 48
    W, H = width + 8, face + gear_h + 4
    cv = Canvas(W, H, seed=seed)
    ox, base = 4, H - 2
    top = base - face
    info = {"lamps": [], "mic": None, "wedges": []}
    # skirt: dark slats, a shadow band under the lip, scuffs at the foot
    cv.rect(ox - 1, top, width + 2, face, OUT)
    cv.rect(ox, top + 3, width, face - 3, SKIRT[1])
    for sx in range(ox + 2, ox + width - 1, 5):
        cv.vline(sx, top + 4, face - 6, SKIRT[2])
        cv.px(sx, top + 4, SKIRT[3])
    cv.rect(ox, top + 3, width, 2, SKIRT[0])
    cv.hline(ox, base - 2, width, SKIRT[0])
    # the lip: warm light on the edge, darker under-nosing
    cv.hline(ox, top, width, lip[3]); cv.hline(ox, top + 1, width, lip[2]); cv.hline(ox, top + 2, width, lip[0])
    for xx in range(ox + 6, ox + width - 6, 23):
        cv.px(xx, top + 1, lip[3])
    # footlights let into the skirt
    if lamps:
        for lx in range(ox + 30, ox + width - 20, 60):
            cv.rect(lx - 3, top + 8, 7, 5, OUT); cv.rect(lx - 2, top + 9, 5, 3, AMBER[3]); cv.px(lx, top + 9, "#fffaf0")
            cv.rect(lx - 6, top + 6, 13, 9, C(AMBER[3], 0.1))
            info["lamps"].append([lx, top + 10])
    # wedge monitors on the edge (canvas x of their centres)
    wedges = wedges if wedges is not None else [width * k // 8 for k in (1, 3, 5, 7)]
    for i, wx in enumerate(wedges):
        cx_ = ox + wx
        wb = top + 1
        cv.poly([(cx_ - 12, wb), (cx_ - 9, wb - 9), (cx_ + 9, wb - 9), (cx_ + 12, wb)], OUT)
        cv.poly([(cx_ - 10, wb - 1), (cx_ - 8, wb - 8), (cx_ + 8, wb - 8), (cx_ + 10, wb - 1)], CASE[2])
        cv.hline(cx_ - 8, wb - 8, 17, CASE[4])
        for gy in range(wb - 6, wb - 1, 2):
            cv.hline(cx_ - 7, gy, 15, CASE[1])
        cv.px(cx_ + 7, wb - 3, "#5cf08a" if leds else "#2a3a30")
        info["wedges"].append([cx_ + 7, wb - 3])
        if cables:   # cable from the wedge draped back over the deck
            cv.line(cx_ + 10, wb - 2, cx_ + 14, wb - 6, WIRE)
    # vocal mic stand at centre front, the set list taped beside it
    if mic:
        mx = ox + width // 2 + 4
        mb = top - 2
        cv.line(mx - 5, mb, mx, mb - 4, OUT); cv.line(mx + 5, mb, mx, mb - 4, OUT); cv.line(mx, mb, mx, mb - 4, OUT)
        cv.vline(mx, mb - 38, 34, IRON[3]); cv.vline(mx + 1, mb - 38, 34, IRON[1])
        cv.line(mx, mb - 38, mx - 6, mb - 42, IRON[3])                                 # boom
        cv.rect(mx - 9, mb - 44, 4, 4, OUT); cv.rect(mx - 8, mb - 43, 2, 2, "#c0c4cc")  # mic head
        cv.line(mx + 1, mb - 30, mx + 4, mb - 10, WIRE); cv.line(mx + 4, mb - 10, mx + 2, mb - 1, WIRE)
        info["mic"] = [mx - 7, mb - 42]
    if setlist:
        sx = ox + width // 2 - 22
        cv.rect(sx, top - 4, 12, 4, "#f2ead6"); cv.hline(sx + 2, top - 3, 7, "#6a6a7a"); cv.hline(sx + 2, top - 2, 5, "#c8382c")
        cv.rect(sx - 1, top - 4, 2, 1, "#8c8e98"); cv.rect(sx + 11, top - 4, 2, 1, "#8c8e98")
    # a strip of shadow where the skirt meets the ground
    cv.hline(ox - 2, base, width + 4, C("#0d0b16", 0.6)); cv.hline(ox - 2, base + 1, width + 4, C("#0d0b16", 0.3))
    return cv, ox + width // 2, base, info



# --- gear on the deck -------------------------------------------------------------------------
def amp_stack(cv, x, base, w=24, h=30, head=True, seed=0):
    """A guitar cab (black tolex, grey grille cloth with a weave, gold piping) with its head on top."""
    cab_h = h - (9 if head else 0)
    cv.rect(x, base - cab_h, w, cab_h, OUT)
    cv.rect(x + 1, base - cab_h + 1, w - 2, cab_h - 2, CASE[1]); cv.hline(x + 1, base - cab_h + 1, w - 2, CASE[3])
    gx0, gy0, gw, gh = x + 3, base - cab_h + 3, w - 6, cab_h - 6
    cv.rect(gx0, gy0, gw, gh, "#4a4652")
    for yy in range(gy0, gy0 + gh):
        for xx in range(gx0 + (yy % 2), gx0 + gw, 2):
            cv.px(xx, yy, "#3a3642")
    cv.rect(gx0 - 1, gy0 - 1, gw + 2, 1, "#a8884a"); cv.rect(gx0 - 1, gy0 + gh, gw + 2, 1, "#a8884a")
    if head:
        hy = base - h
        cv.rect(x, hy, w, 9, OUT); cv.rect(x + 1, hy + 1, w - 2, 7, CASE[1]); cv.hline(x + 1, hy + 1, w - 2, CASE[3])
        cv.rect(x + 2, hy + 4, w - 4, 3, "#c8b07a")
        for k in range(x + 4, x + w - 4, 3):
            cv.px(k, hy + 5, OUT)
        cv.px(x + w - 4, hy + 2, "#f05a4a")
    cv.hline(x - 1, base, w + 2, C("#0d0b16", 0.5))


def drum_riser(cv, cx, base, w=86, seed=0):
    """Drum riser: carpeted platform with a slatted front, the kit on it (bass drum with a lit
    front head, toms, snare, brass cymbals on stands, the throne behind)."""
    rh = 10
    x0 = cx - w // 2
    top = base - rh
    cv.rect(x0 - 1, top - 4, w + 2, rh + 4, OUT)
    cv.rect(x0, top - 3, w, 4, "#3a2a3a"); cv.hline(x0, top - 3, w, "#5a4458")            # carpet
    cv.rect(x0, top + 1, w, rh - 1, SKIRT[1])
    for sx in range(x0 + 2, x0 + w, 4):
        cv.vline(sx, top + 2, rh - 3, SKIRT[2])
    ky = top - 3                                            # the kit stands here
    # cymbals on stands (behind)
    for (dx, dy, cw) in [(-30, 26, 14), (26, 30, 16), (-12, 33, 12)]:
        sx = cx + dx
        cv.vline(sx, ky - dy, dy, IRON[3])
        cv.poly([(sx - cw // 2, ky - dy + 1), (sx, ky - dy - 2), (sx + cw // 2, ky - dy + 1)], "#a8803a")
        cv.hline(sx - cw // 2 + 2, ky - dy - 1, cw - 4, "#e0b860"); cv.px(sx, ky - dy - 2, "#f6dca0")
    # throne behind
    cv.rect(cx - 4, ky - 12, 9, 3, OUT); cv.rect(cx - 3, ky - 11, 7, 1, "#3a3644")
    # toms
    for (dx, r) in [(-9, 5), (8, 5)]:
        tx = cx + dx
        cv.ellipse(tx - r, ky - 24, 2 * r + 1, 9, OUT); cv.ellipse(tx - r + 1, ky - 23, 2 * r - 1, 7, "#8a2c3a")
        cv.hline(tx - r + 2, ky - 23, 2 * r - 3, "#e6e2d8")
    # bass drum: front head facing us, lit, a ring and the festival's initials
    r = 12
    cv.ellipse(cx - r - 1, ky - 2 * r - 1, 2 * r + 3, 2 * r + 2, OUT)
    cv.ellipse(cx - r, ky - 2 * r, 2 * r + 1, 2 * r, "#8a2c3a")
    cv.ellipse(cx - r + 2, ky - 2 * r + 2, 2 * r - 3, 2 * r - 4, "#e6dcc4")
    cv.ellipse(cx - r + 4, ky - 2 * r + 4, 2 * r - 7, 2 * r - 8, "#f2ead6")
    text(cv, "LL", cx - 6, ky - r - 4, "#7e3a30")
    # snare and floor tom at the sides
    cv.rect(cx - 26, ky - 10, 11, 6, OUT); cv.rect(cx - 25, ky - 9, 9, 4, "#c8c8d0"); cv.hline(cx - 25, ky - 9, 9, "#ffffff")
    cv.vline(cx - 21, ky - 4, 4, IRON[3])
    cv.rect(cx + 15, ky - 14, 12, 14, OUT); cv.rect(cx + 16, ky - 13, 10, 12, "#8a2c3a"); cv.hline(cx + 16, ky - 13, 10, "#e6e2d8")
    cv.vline(cx + 17, ky - 12, 11, "#a83c4a")


def keys_stand(cv, x, base, w=34):
    """A keyboard on an X stand: black body, a row of white keys with black ones, a lit screen."""
    ky = base - 18
    cv.line(x + 3, base, x + w - 5, ky + 3, IRON[3]); cv.line(x + w - 4, base, x + 4, ky + 3, IRON[2])
    cv.rect(x, ky - 4, w, 6, OUT); cv.rect(x + 1, ky - 3, w - 2, 4, CASE[1])
    cv.hline(x + 2, ky - 1, w - 4, "#e6e2d8")
    for k in range(x + 3, x + w - 3, 3):
        cv.px(k, ky - 1, OUT)
    cv.rect(x + w // 2 - 3, ky - 3, 6, 1, "#7ab8f0")


def mic_stand(cv, x, base, h=34, boom=-1):
    cv.line(x - 4, base, x, base - 3, OUT); cv.line(x + 4, base, x, base - 3, OUT)
    cv.vline(x, base - h, h - 2, IRON[3])
    cv.line(x, base - h, x + boom * 6, base - h - 4, IRON[3])
    cv.rect(x + boom * 6 - 1, base - h - 6, 3, 3, "#c0c4cc")


def guitar_on_stand(cv, x, base, body="#c84a3c"):
    """An electric guitar resting upright on an A-frame stand: lower and upper bouts with a waist,
    pickguard, long neck, headstock."""
    cv.line(x - 5, base, x - 1, base - 9, IRON[2]); cv.line(x + 5, base, x + 1, base - 9, IRON[2])
    bot = base - 4
    cv.ellipse(x - 7, bot - 12, 15, 12, OUT); cv.ellipse(x - 6, bot - 18, 12, 10, OUT)
    cv.ellipse(x - 6, bot - 11, 13, 10, body); cv.ellipse(x - 5, bot - 17, 10, 8, body)
    cv.px(x - 6, bot - 11, OUT); cv.px(x + 6, bot - 11, OUT)                       # waist
    cv.ellipse(x - 5, bot - 10, 6, 6, shade(body, 0.25))
    cv.rect(x - 1, bot - 9, 6, 5, "#e6e2d8"); cv.hline(x - 3, bot - 6, 7, OUT)   # pickguard, bridge
    cv.rect(x - 1, bot - 40, 3, 24, OUT); cv.vline(x, bot - 40, 24, "#8c573b")   # neck
    cv.rect(x - 2, bot - 45, 5, 6, OUT); cv.rect(x - 1, bot - 44, 3, 4, "#2a1a1a")
    cv.px(x - 2, bot - 43, "#c8c8d0"); cv.px(x + 2, bot - 42, "#c8c8d0")


def deck_stairs(cv, x, lip_y, face, side=-1, steps=3, run=10):
    """Flight-case stairs against the side of the deck going down to the ground: aluminium-edged
    black cases stepping down, lit diamond-plate treads, a handrail on the outer side. side -1 =
    left of the deck (x is the deck's left edge), +1 = right."""
    rise = face // steps
    for i in range(steps):
        h = face - i * rise                      # step i (0 = the top step against the deck)
        sx = x + (i * run if side > 0 else -(i + 1) * run)
        top = lip_y + face - h
        cv.rect(sx, top - 6, run, 6, CASE[4]); cv.hline(sx, top - 6, run, CASE[6])          # tread
        for k in range(sx + 1, sx + run - 1, 2):
            cv.px(k, top - 4 + (k % 4) // 2, CASE[5])
        cv.rect(sx - (1 if side < 0 else 0), top, run + 1, h, OUT)                          # case face
        cv.rect(sx, top + 1, run - 1 + (1 if side < 0 else 0), h - 2, CASE[2])
        cv.hline(sx, top + 1, run - 1, CASE[5]); cv.vline(sx + (run - 2 if side > 0 else 0), top + 1, h - 2, CASE[4])
        cv.rect(sx + run // 2 - 2, top + 4, 4, 2, CASE[5])                                     # latch
    far = x + side * steps * run
    rail_x = far - (1 if side > 0 else -1) * 2
    cv.vline(rail_x, lip_y + face - rise - 20, 20, IRON[3])
    cv.line(rail_x, lip_y + face - rise - 20, x + side * 2, lip_y - 22, IRON[4])
    cv.vline(x + side * 2, lip_y - 22, 16, IRON[3])
    cv.hline(min(x, far) - 2, lip_y + face, abs(far - x) + 4, C("#0d0b16", 0.5))


def picnic_blanket(cv, x, y, w, h, pal=None, seed=0, skew=8):
    """A plaid blanket spread on the grass (flat): skewed, a fold along one edge, fringe, a few
    things left on it."""
    rng = _rng(seed)
    pal = pal or F.RED
    pts = [(x + skew, y), (x + w + skew // 2, y + 2), (x + w, y + h), (x, y + h - 2)]
    cv.poly([(p[0], p[1] + 2) for p in pts], C("#0d0b16", 0.35))
    cv.poly(pts, pal[3])
    for k in range(0, w + skew, 7):                     # plaid: diagonal-ish verticals, horizontals
        cv.line(x + skew + k - (skew if k > w else 0), y + 1, x + k, y + h - 2, pal[2])
    for k in range(3, h - 2, 5):
        t = k / h
        cv.line(int(x + skew * (1 - t)) + 1, y + k, int(x + w + skew // 2 * (1 - t)) - 1, y + k + 1, pal[4])
    cv.line(x + skew, y, x + w + skew // 2, y + 2, pal[5])
    for k in range(x + 2, x + w - 1, 3):                # fringe on the near edge
        cv.px(k, y + h - 1 + (k % 2), pal[4])
    return [(x + w // 3, y + h // 2), (x + 2 * w // 3, y + h // 3)]


# --- the whole stage --------------------------------------------------------------------------
def main_stage(cv, cx, deck_w, back_y, lip_y, roof_top, rise=18, screen="mountains", lamps_on=True,
               dim=0.0, seed=0, gear=True, deck=True, banner="LAST LIGHT / ONE FINAL SET", halo=True,
               screen_h=None, face=28, stairs=True):
    """Paint the main stage into a room background. The deck spans cx +- deck_w/2 from the back
    drape (back_y) to the front lip (lip_y, where the stage_front prop takes over); the roof's
    arched truss peaks at roof_top. Returns info: 'lamps' [[x, y, hex]], 'tower_lamps', 'screen'
    (x, y, w, h), 'banner' (x, y, w, h), 'arch' (x -> truss top y), 'wings' (left x, right x),
    'pa' [(x, bottom)]."""
    rng = _rng(seed)
    x0, x1 = cx - deck_w // 2, cx + deck_w // 2
    rx0, rx1 = x0 - 42, x1 + 42
    arch = roof_arch(rx0, rx1, roof_top, rise)
    depth = 11
    info = {"lamps": [], "tower_lamps": [], "arch": arch, "pa": []}
    if halo and not dim:
        for (r, a) in [(deck_w // 2 + 70, 0.05), (deck_w // 2 + 40, 0.06), (deck_w // 2 + 14, 0.07)]:
            cv.ellipse(cx - r, roof_top - r // 5, r * 2, r // 2 + (back_y - roof_top), C("#c88ab0", a))
    # scaffold wings outside the roof ends
    wing_top = roof_top + rise - 14
    wl, wr = rx0 + 2, rx1 - 22
    info["wings"] = (wl, wr)
    for k, wx in enumerate((wl, wr)):
        info["tower_lamps"] += scaffold_tower(cv, wx, wing_top, back_y, 20, seed=seed + k, scrim_from=wing_top + 40)
    # back drape and the masking legs at the sides
    bwx0, bwx1 = x0 + 16, x1 - 16
    drape_wall(cv, bwx0, bwx1, lambda x: arch(x) + depth + 1, back_y, dim=dim)
    for (a, b) in ((wl + 20, bwx0), (bwx1, wr)):
        for x in range(a, b):
            k = (x - a) % 5
            col = SCRIM[2] if k in (1, 2) else SCRIM[1] if k == 3 else SCRIM[3]
            cv.vline(x, arch(x) + depth + 1, back_y - arch(x) - depth - 1, col)
        cv.vline(a if a > cx else b - 1, arch(a) + depth, back_y - arch(a) - depth, SCRIM[0])
    # LED wall
    if screen_h is None:
        screen_h = int((back_y - arch(cx)) * 0.5)
    sw = int(deck_w * 0.42) // 12 * 12
    sx = cx - sw // 2
    sy = arch(cx) + depth + 26
    info["screen"] = (sx, sy, sw, screen_h)
    led_screen(cv, sx, sy, sw, screen_h, kind=screen, seed=seed)
    # shafts of light from the truss down the drape (not over the screen)
    if lamps_on:
        for i, lx in enumerate(range(bwx0 + 18, bwx1 - 10, (bwx1 - bwx0) // 6)):
            col = ["#fff0c4", "#f0a0d0", "#a8c8ff"][i % 3]
            ty = arch(lx) + depth + 2
            for yy in range(ty, back_y - 2):
                spread = (yy - ty) // 5 + 1
                lean = (i % 2 * 2 - 1) * (yy - ty) // 7
                for xx in range(lx - spread + lean, lx + spread + lean + 1):
                    if sx - 2 <= xx < sx + sw + 2 and sy - 2 <= yy < sy + screen_h + 2:
                        continue
                    inner = abs(xx - lx - lean) < spread // 2 + 1
                    cv.px(xx, yy, C(col, 0.09 if inner else 0.05))
    # gear at the back of the deck
    if gear:
        drum_riser(cv, cx, back_y, w=min(96, deck_w // 4), seed=seed)
        amp_stack(cv, cx - deck_w // 4 - 20, back_y, 24, 30)
        amp_stack(cv, cx - deck_w // 4 + 6, back_y, 24, 21, head=False)
        amp_stack(cv, cx + deck_w // 4 - 4, back_y, 30, 34)
        keys_stand(cv, x0 + 22, back_y)
        guitar_on_stand(cv, cx + deck_w // 4 + 36, back_y)
        guitar_on_stand(cv, cx - deck_w // 4 - 30, back_y, body="#e0b23a")
        for mx in (cx - deck_w // 6, cx + deck_w // 6 + 10):
            mic_stand(cv, mx, back_y, 30, -1 if mx < cx else 1)
    # roof truss and its lamps (over everything behind)
    for x in range(rx0, rx1):
        cv.vline(x, arch(x) - 6, 3, C(TRUSS[0], 0.6))
    truss_band(cv, rx0, rx1, arch, depth)
    kinds = ["par", "head", "par", "par", "head"]
    for i, lx in enumerate(range(rx0 + 16, rx1 - 12, 22)):
        col = LAMP_COLOURS[i % len(LAMP_COLOURS)]
        lens = stage_lamp(cv, lx, arch(lx) + depth, col, kinds[i % len(kinds)], on=lamps_on)
        info["lamps"].append([lens[0], lens[1], col.lstrip("#")])
    # PA line arrays hanging at the front corners
    for px_ in (x0 - 18, x1 - 8):
        top = arch(px_ + 12) + depth + 8
        bottom = line_array(cv, px_, top, n=8, w=24, box=8, chain=7, lit=lamps_on)
        info["pa"].append((px_ + 15, bottom))
    # banner under the truss
    if banner:
        by = arch(cx) + depth + 5
        bw = text_width(banner) + 16
        ties = [(cx - bw // 2 + 3, arch(cx - bw // 2) + depth), (cx + bw // 2 - 4, arch(cx + bw // 2) + depth)]
        info["banner"] = stage_banner(cv, cx, by, banner, tie_to=ties)
    if deck:
        d = lip_y - back_y
        runs = [[(cx - deck_w // 4 - 8, back_y + 2), (cx - deck_w // 4 - 10, back_y + d // 2), (x0 + deck_w // 8 + 10, lip_y - 3)],
                [(cx + deck_w // 4 + 10, back_y + 2), (cx + deck_w // 4 + 14, back_y + d // 2), (x1 - deck_w // 8 + 10, lip_y - 3)],
                [(cx + 6, back_y + 2), (cx + 14, back_y + d * 2 // 3), (cx + 10, lip_y - 3)],
                [(x0 + 30, back_y + 2), (x0 + 36, back_y + d // 2), (x0 + deck_w * 3 // 8 + 10, lip_y - 3)]]
        stage_deck(cv, x0, x1, back_y, lip_y, seed=seed, pools=lamps_on, runs=runs)
    if stairs:
        deck_stairs(cv, x0, lip_y, face, side=-1)
        deck_stairs(cv, x1, lip_y, face, side=1)
    return info


# --- audience ---------------------------------------------------------------------------------
def chair_row(width=170, height=30, n=None, seed=0, things=True, frame=None, slats=None):
    """A row of wooden folding chairs seen from behind, facing the stage: slatted backs on steel
    frames, the seat's edge and legs below, joined by a strap. Things left on some chairs: a
    plaid blanket over a back, a programme, a jacket, a cup. Anchor bottom centre."""
    rng = _rng(seed)
    frame = frame or F.STEEL
    slats = slats or F.PLY
    n = n or max(2, int(round(width / 21)))
    CW, CH = width + 8, height + 8
    cv = Canvas(CW, CH, seed=seed)
    ox, base = 4, CH - 3
    ground_shadow(cv, ox + width // 2, base, width // 2, 2, alpha=0.4)
    pitch = width / n
    cw = int(pitch) - 4
    top = base - height
    for i in range(n):
        x = int(round(ox + i * pitch + (pitch - cw) / 2))
        # legs: rear pair splayed back, the front pair seen between them
        for lx in (x + 1, x + cw - 2):
            cv.rect(lx, top + 14, 2, base - top - 14, OUT); cv.vline(lx, top + 15, base - top - 16, frame[3])
        for lx in (x + 3, x + cw - 4):
            cv.vline(lx, top + 19, base - top - 20, frame[1])
        cv.hline(x + 2, base - 6, cw - 4, frame[2])                                  # cross bar
        # seat edge under the back
        cv.rect(x - 1, top + 13, cw + 2, 4, OUT); cv.hline(x, top + 14, cw, slats[4]); cv.hline(x, top + 15, cw, slats[2])
        # back: frame and three slats
        cv.rect(x - 1, top, cw + 2, 14, OUT)
        cv.vline(x, top + 1, 12, frame[4]); cv.vline(x + cw - 1, top + 1, 12, frame[2])
        for k, sy in enumerate((top + 1, top + 5, top + 9)):
            cv.rect(x + 1, sy, cw - 2, 3, slats[3]); cv.hline(x + 1, sy, cw - 2, slats[5] if k == 0 else slats[4])
            cv.px(x + 1 + int(rng.integers(0, max(1, cw - 3))), sy + 1, slats[2])
        cv.hline(x + 1, top + 12, cw - 2, slats[1])
        if not things:
            continue
        r = rng.random()
        if r < 0.16:     # plaid blanket over the back, hanging down behind
            pal = F.RED if rng.random() < 0.5 else F.TEAL_C
            cv.rect(x - 1, top - 1, cw + 2, 18, OUT)
            cv.rect(x, top, cw, 16, pal[3])
            for k in range(1, cw, 4):
                cv.vline(x + k, top, 16, pal[2])
            for k in range(2, 16, 4):
                cv.hline(x, top + k, cw, pal[4])
            cv.hline(x, top, cw, pal[5])
            cv.poly([(x + 2, top + 16), (x + cw - 2, top + 16), (x + cw // 2, top + 20)], pal[2])
        elif r < 0.28:   # a programme left on the seat, its corner over the edge
            cv.rect(x + cw // 2 - 3, top + 12, 7, 3, "#f2ead6"); cv.px(x + cw // 2 - 2, top + 13, "#c8382c")
        elif r < 0.38:   # a jacket over the back
            cv.rect(x - 1, top - 1, cw + 2, 9, OUT); cv.rect(x, top, cw, 7, "#2c3a5a"); cv.hline(x, top, cw, "#425a86")
            cv.vline(x + 2, top + 7, 9, OUT); cv.vline(x + 3, top + 7, 8, "#2c3a5a")
        elif r < 0.46:   # a paper cup on the seat
            cv.rect(x + cw - 6, top + 9, 4, 5, "#e6e2d8"); cv.hline(x + cw - 6, top + 10, 4, "#c84a3c")
    return cv, ox + width // 2, base


def sub_stack(width=38, height=68, seed=0, label=None, on=True):
    """Ground-stacked PA at a stage corner: two sub-bass boxes with big ported fronts and a
    mid-high box on top angled at the crowd, black with worn corners, a strap round the stack."""
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.45)
    sub_h = 24
    for k in range(2):
        y = base - sub_h * (k + 1)
        cv.rect(ox, y, width, sub_h, OUT)
        cv.rect(ox + 1, y + 1, width - 2, sub_h - 2, CASE[1]); cv.hline(ox + 1, y + 1, width - 2, CASE[3])
        cv.ellipse(ox + 5, y + 4, width - 10, sub_h - 8, "#0d0b14")                 # driver
        cv.ellipse(ox + 8, y + 7, width - 16, sub_h - 14, CASE[2])
        cv.ellipse(ox + width // 2 - 3, y + sub_h // 2 - 3, 7, 6, CASE[3])
        cv.rect(ox + 2, y + sub_h - 5, 6, 3, "#0d0b14"); cv.rect(ox + width - 8, y + sub_h - 5, 6, 3, "#0d0b14")  # ports
        for (cx_, cy_) in [(ox + 1, y + 1), (ox + width - 3, y + 1), (ox + 1, y + sub_h - 3), (ox + width - 3, y + sub_h - 3)]:
            cv.rect(cx_, cy_, 2, 2, CASE[5])
    top_h = height - 2 * sub_h
    y = base - height
    cv.poly([(ox + 2, y + top_h), (ox + 4, y), (ox + width - 4, y + 2), (ox + width - 2, y + top_h)], OUT)
    cv.poly([(ox + 3, y + top_h - 1), (ox + 5, y + 1), (ox + width - 5, y + 3), (ox + width - 3, y + top_h - 1)], CASE[2])
    for gy in range(y + 4, y + top_h - 1, 2):
        cv.hline(ox + 5, gy, width - 10, CASE[1])
    cv.hline(ox + 5, y + 1, width - 10, CASE[4])
    cv.px(ox + width - 7, y + top_h - 3, "#5cf08a" if on else "#2a3a30")
    cv.vline(ox + width // 2 - 8, base - 2 * sub_h, 2 * sub_h, "#c8a03a")             # ratchet strap
    cv.rect(ox + width // 2 - 9, base - sub_h - 2, 3, 4, F.STEEL[4])
    if label:
        lw = text_width(label) + 4
        cv.rect(ox + width // 2 - lw // 2, base - 10, lw, 9, "#e6d6b1")
        text(cv, label, ox + width // 2 - lw // 2 + 2, base - 11, "#2c2a34")
    return cv, ox + width // 2, base


def ghost_light(height=55, seed=0, on=True):
    """The stage rest light (ghost light): a bare bulb in a wire cage on a tall pole, three-footed
    base on castors, the cable coiled at its foot. The bulb's centre sits height - 5 above the
    anchor, where the game puts its point light. Returns (Canvas, ax, ay, (bulb_x, bulb_y))."""
    w = 26
    H = height + 10
    cv = Canvas(w, H, seed=seed)
    cx, base = w // 2, H - 3
    by = base - (height - 5)
    ground_shadow(cv, cx, base, 9, 2)
    # tripod base and castors
    cv.line(cx, base - 6, cx - 8, base - 1, OUT); cv.line(cx, base - 6, cx + 8, base - 1, OUT)
    cv.line(cx, base - 6, cx + 2, base - 1, OUT)
    for fx in (cx - 9, cx + 7, cx + 1):
        cv.rect(fx, base - 2, 3, 3, OUT); cv.px(fx + 1, base - 1, IRON[3])
    # pole
    cv.rect(cx - 1, by + 6, 3, base - 6 - by - 6, OUT); cv.vline(cx, by + 6, base - by - 12, IRON[4])
    cv.rect(cx - 2, by + 24, 5, 3, OUT); cv.hline(cx - 1, by + 25, 3, IRON[3])         # clamp
    # cable down the pole and coiled at the foot
    for yy in range(by + 8, base - 4):
        cv.px(cx + 2, yy, WIRE)
    cv.ellipse(cx + 2, base - 5, 9, 4, WIRE); cv.ellipse(cx + 4, base - 4, 5, 2, C("#000000", 0))
    # socket, bulb, cage
    cv.rect(cx - 2, by + 3, 5, 4, OUT); cv.rect(cx - 1, by + 4, 3, 2, IRON[3])
    if on:
        cv.ellipse(cx - 7, by - 9, 15, 15, C(AMBER[3], 0.16))
        cv.ellipse(cx - 5, by - 7, 11, 11, C(AMBER[3], 0.2))
    cv.ellipse(cx - 3, by - 4, 7, 8, AMBER[3] if on else "#c8c4b8")
    cv.ellipse(cx - 2, by - 3, 4, 5, AMBER[4] if on else "#e6e2d8")
    if on:
        cv.px(cx - 1, by - 2, "#ffffff")
    for k in (-4, 0, 4):                                    # cage wires
        cv.line(cx + k, by - 6 + abs(k) // 2, cx + k, by + 3, IRON[2])
    cv.hline(cx - 4, by - 6, 9, IRON[2]); cv.hline(cx - 4, by - 1, 9, IRON[1])
    cv.px(cx, by - 7, IRON[2])
    return cv, cx, base, (cx, by)


def delay_tower(cv, x, base, height, seed=0, pa=True, owl_perch=False):
    """A delay tower out in the audience field: a triangular lattice mast (seen as two chords with
    zigzag lacing), a small PA box hung near the top facing the crowd, a lamp bar on top with two
    spots, guy wires pegged out, water ballast tanks at the foot. Returns lamp points."""
    rng = _rng(seed)
    w = 12
    top = base - height
    for yy in range(top, base, 8):                          # lacing
        cv.line(x + 1, yy, x + w - 2, yy + 4, TRUSS[3]); cv.line(x + w - 2, yy + 4, x + 1, yy + 8, TRUSS[3])
    for sx in (x, x + w - 2):
        cv.rect(sx, top, 2, height, OUT); cv.px(sx, top, TRUSS[5])
        cv.vline(sx + (1 if sx == x else 0), top, height, TRUSS[4])
    # guy wires
    for (gx, gy) in [(x - 40, base - 2), (x + w + 40, base - 2)]:
        cv.line(x + w // 2, top + 14, gx, gy, C("#8a8698", 0.55))
        cv.rect(gx - 1, gy - 1, 3, 3, OUT)
    # ballast: two water tanks in a cage
    for k in (-1, 1):
        tx = x + w // 2 + k * 9 - 6
        cv.rect(tx, base - 11, 12, 11, OUT); cv.rect(tx + 1, base - 10, 10, 9, "#d8d8d0")
        cv.hline(tx + 1, base - 10, 10, "#f2f2ee")
        for gx in range(tx + 3, tx + 11, 3):
            cv.vline(gx, base - 10, 9, F.STEEL[3])
        cv.hline(tx + 1, base - 5, 10, F.STEEL[3])
    pts = []
    if pa:
        py = top + 18
        cv.rect(x - 4, py, w + 8, 16, OUT); cv.rect(x - 3, py + 1, w + 6, 14, CASE[1]); cv.hline(x - 3, py + 1, w + 6, CASE[3])
        for gy in range(py + 3, py + 14, 2):
            cv.hline(x - 1, gy, w + 2, CASE[2])
        cv.px(x + w + 1, py + 13, "#5cf08a")
    cv.rect(x - 6, top - 4, w + 12, 4, OUT); cv.hline(x - 5, top - 3, w + 10, TRUSS[4])
    for lx in (x - 5, x + w + 1):
        cv.rect(lx, top - 8, 5, 4, OUT); cv.rect(lx + 1, top - 7, 3, 2, "#fff0c4"); cv.px(lx + 2, top - 7, "#ffffff")
        pts.append([lx + 2, top - 6])
    return pts


# --- backstage --------------------------------------------------------------------------------
TRACK = ["#202028", "#32323a", "#46464e", "#5a5a62", "#6e6e76", "#8e8e94", "#b8b8bc"]


def trackway(cv, x, y, w, h, panel=(58, 22), along="x", seed=0, mud=5, pal=TRACK):
    """Aluminium trackway laid on the grass as the crew's roadway: chequer-plate panels (raised
    bars alternating direction), dark joints with bright hinge knuckles, a lit leading edge, mud
    carried in on boots. along='x' runs left-right (rows staggered), 'y' runs away from the viewer
    (panels stacked). Returns a canvas-sized mask."""
    rng = _rng(seed)
    pw, ph = panel
    cv.rect(x, y, w, h, pal[1])
    panels = []
    if along == "x":
        for r, yy in enumerate(range(y, y + h, ph)):
            off = (pw // 2) if r % 2 else 0
            for xx in range(x - off, x + w, pw):
                panels.append((max(x, xx), yy, min(x + w, xx + pw), min(y + h, yy + ph)))
    else:
        cols = max(1, int(round(w / pw)))
        cw = w // cols
        for c in range(cols):
            for yy in range(y - (ph // 2 if c % 2 else 0), y + h, ph):
                panels.append((x + c * cw, max(y, yy), x + (c + 1) * cw if c < cols - 1 else x + w, min(y + h, yy + ph)))
    for (x0, y0, x1, y1) in panels:
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue
        tone = mix(pal[3], pal[4], float(rng.random()) * 0.55)
        hi, lo = shade(tone, 0.14), shade(tone, -0.1)
        cv.rect(x0, y0, x1 - x0 - 1, y1 - y0 - 1, tone)
        if along == "x":                                            # extruded ribs across the travel
            for xx in range(x0 + 2, x1 - 2, 3):
                cv.vline(xx, y0 + 1, y1 - y0 - 3, hi); cv.vline(xx + 1, y0 + 2, y1 - y0 - 4, lo)
        else:
            for yy in range(y0 + 2, y1 - 2, 3):
                cv.hline(x0 + 1, yy, x1 - x0 - 3, hi); cv.hline(x0 + 2, yy + 1, x1 - x0 - 4, lo)
        for _ in range((x1 - x0) * (y1 - y0) // 400):                # scuffs catching the light
            gx, gy = x0 + int(rng.integers(2, max(3, x1 - x0 - 6))), y0 + int(rng.integers(2, max(3, y1 - y0 - 3)))
            cv.hline(gx, gy, int(rng.integers(2, 5)), shade(tone, 0.28))
        cv.hline(x0, y0, x1 - x0 - 1, shade(tone, 0.2))
        cv.vline(x0, y0, y1 - y0 - 1, shade(tone, 0.08))
        cv.hline(x0, y1 - 2, x1 - x0 - 1, lo)
        cv.vline(x1 - 1, y0, y1 - y0, pal[0]); cv.hline(x0, y1 - 1, x1 - x0, pal[0])
        if along == "x":
            for ky in range(y0 + 4, y1 - 3, 8):                    # hinge knuckles on the joint
                cv.rect(x1 - 2, ky, 3, 2, pal[5]); cv.px(x1 - 1, ky + 1, pal[2])
        else:
            for kx in range(x0 + 5, x1 - 4, 10):
                cv.rect(kx, y1 - 2, 3, 2, pal[5]); cv.px(kx + 1, y1 - 1, pal[2])
    for _ in range(mud):                                            # mud and boot prints
        fx, fy = x + int(rng.integers(4, max(5, w - 20))), y + int(rng.integers(2, max(3, h - 6)))
        if rng.random() < 0.5:
            cv.rect(fx, fy, int(rng.integers(6, 16)), 2, C(F.DIRT[2], 0.55))
            cv.hline(fx + 2, fy + 2, int(rng.integers(3, 8)), C(F.DIRT[1], 0.45))
        else:
            for k in range(3):
                px_, py_ = (fx + k * 7, fy + (k % 2) * 3) if along == "x" else (fx + (k % 2) * 4, fy - k * 6)
                cv.rect(px_, py_, 3, 2, C(F.DIRT[1], 0.55)); cv.px(px_ + 1, py_ + 2, C(F.DIRT[1], 0.4))
    cv.hline(x, y - 1, w, C("#0d0b16", 0.3))
    cv.hline(x, y + h, w, C("#0d0b16", 0.55)); cv.hline(x, y + h + 1, w, C("#0d0b16", 0.25))
    cv.vline(x + w, y, h, C("#0d0b16", 0.4))
    mask = np.zeros((cv.h, cv.w), bool)
    mask[max(0, y):y + h, max(0, x):x + w] = True
    return mask


def cable_loom(cv, points, seed=0, count=5):
    """A fat loom of stage cables lying on the ground (power, multicore, DMX), taped together."""
    F.cable_run(cv, points, count=count, seed=seed, spread=3, tape_every=46,
                colours=("#1e1c24", "#2a2832", "#7a3a2a", "#1e1c24", "#3a3a52"))


def road_case(cv, x, base, w, h, top=5, pal=CASE, label=None, label_col="#e6e2d8", tape=None,
              wheels=False, latches=True, lid=0.32):
    """A flight case seen from the front and a little above: plywood skin, aluminium edge
    extrusions, ball corners, butterfly latches on the lid line, a stencilled label, optionally a
    strip of gaffer tape with a marker label, castors under it. Returns its top-left."""
    if wheels:
        for wx in (x + 3, x + w - 8):
            cv.rect(wx, base - 4, 5, 4, OUT); cv.rect(wx + 1, base - 3, 3, 2, F.STEEL[2]); cv.px(wx + 2, base - 3, F.STEEL[4])
        base -= 4
    y = base - h
    cv.rect(x - 1, y - top - 1, w + 2, h + top + 2, OUT)
    cv.rect(x, y - top, w, top, pal[3]); cv.hline(x, y - top, w, pal[4])            # lid seen from above
    cv.rect(x, y, w, h, pal[2])
    cv.vline(x + 1, y, h, shade(pal[2], 0.06))
    cv.hline(x, y, w, pal[5]); cv.hline(x, y + 1, w, pal[1])                       # top-front extrusion
    cv.vline(x, y - top, h + top, pal[4]); cv.vline(x + w - 1, y - top, h + top, pal[1])
    cv.hline(x, base - 1, w, pal[1])
    ly = y + max(3, int(h * lid))
    cv.hline(x, ly, w, pal[0]); cv.hline(x, ly + 1, w, pal[4])                      # lid line
    for (cx_, cy_) in [(x, y - 1), (x + w - 3, y - 1), (x, base - 3), (x + w - 3, base - 3)]:
        cv.rect(cx_, cy_, 3, 3, pal[5]); cv.px(cx_ + 1, cy_ + 1, pal[6])            # ball corners
    if latches:
        for lx in ([x + w // 4, x + w * 3 // 4 - 3] if w > 30 else [x + w // 2 - 2]):
            cv.rect(lx, ly - 1, 4, 3, OUT); cv.rect(lx + 1, ly, 2, 1, pal[6])
    if label:
        tw = text_width(label)
        text(cv, label, x + (w - tw) // 2, ly + 3, label_col)
    if tape:
        tw = text_width(tape) + 4
        tx = x + (w - tw) // 2
        ty = base - 10 if not label else y + 2
        cv.rect(tx, ty, tw, 8, "#e8e4d8"); cv.hline(tx, ty, tw, "#f6f4ee"); cv.px(tx + tw - 1, ty + 7, "#c8c4b8")
        text(cv, tape, tx + 2, ty - 1, "#2a2a36")
    return x, y - top


def gear_rack(width=100, height=90, seed=0):
    """Steel shelving behind the stage: four levels of kit. Flight cases on the bottom shelf,
    coiled cables and a tower of gaffer-tape rolls, a radio charger with handsets, hard hats and a
    folded drape on top, a hi-vis vest on the end. Anchor bottom centre."""
    rng = _rng(seed)
    W, H = width + 10, height + 8
    cv = Canvas(W, H, seed=seed)
    ox, base = 4, H - 3
    x0, x1 = ox, ox + width - 1
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.45)
    depth = 5                                                     # the back uprights, up and right
    levels = [base - 4, base - 32, base - 56, base - 78]          # shelf tops (front edge y)
    top = base - height
    st = F.STEEL
    # back uprights and the back of each shelf (seen through)
    for bx in (x0 + depth, x1 + depth - 1):
        cv.rect(bx - 1, top - depth, 3, height - 2, OUT); cv.vline(bx, top - depth + 1, height - 4, st[2])
    def shelf(yy):
        cv.poly([(x0, yy), (x0 + depth, yy - depth), (x1 + depth, yy - depth), (x1, yy)], st[3])
        cv.hline(x0 + depth, yy - depth, width, st[2])
        cv.rect(x0 - 1, yy, width + 2, 4, OUT); cv.hline(x0, yy + 1, width, st[5]); cv.hline(x0, yy + 2, width, st[3])
        for hx in range(x0 + 6, x1 - 4, 12):
            cv.px(hx, yy + 2, st[1])
    # bottom shelf: two flight cases
    shelf(levels[0])
    road_case(cv, x0 + 3, levels[0], 44, 20, top=3, label="DI")
    road_case(cv, x0 + 51, levels[0], 44, 23, top=3, label="MICS", pal=["#121018", "#24161c", "#3a2028", "#4e2a32", "#6a3a42", "#8a8894", "#c8c8d0"])
    # second shelf: coiled cables, a gaffer tape tower, a crate of clamps
    shelf(levels[1])
    y = levels[1]
    for k, (cx_, col) in enumerate([(x0 + 12, "#1e1c24"), (x0 + 26, "#2a2832"), (x0 + 40, "#c45a2a")]):
        cv.ellipse(cx_ - 8, y - 18, 17, 18, OUT)
        cv.ellipse(cx_ - 7, y - 17, 15, 16, col)
        cv.ellipse(cx_ - 4, y - 14, 9, 10, OUT)
        cv.ellipse(cx_ - 3, y - 13, 7, 8, st[3] if k != 2 else "#2a2832")
        for a in range(0, 360, 40):
            r = 6.5
            px_, py_ = cx_ + int(round(r * np.cos(np.radians(a)))), y - 9 + int(round(r * np.sin(np.radians(a))))
            cv.px(px_, py_, shade(col, 0.35))
    gx = x0 + 56
    for k, col in enumerate(["#22202a", "#e8e4d8", "#e0b23a", "#e86aa8", "#2a2a36", "#5ab0e8"]):
        ty = y - 4 - k * 4
        cv.rect(gx - 1, ty - 1, 12, 5, OUT); cv.rect(gx, ty, 10, 3, col); cv.hline(gx, ty, 10, shade(col, 0.2))
        cv.rect(gx + 3, ty, 4, 1, shade(col, -0.35))
    cv.rect(x0 + 72, y - 14, 24, 14, OUT); cv.rect(x0 + 73, y - 13, 22, 12, "#3a5a8a"); cv.hline(x0 + 73, y - 13, 22, "#5a7aaa")
    for k in range(4):
        cv.rect(x0 + 75 + k * 5, y - 17, 3, 4, st[4]); cv.px(x0 + 76 + k * 5, y - 17, st[5])
    cv.hline(x0 + 73, y - 7, 22, "#2a4468")
    # third shelf: radio charger with handsets (green and red LEDs), first-aid box, a torch
    shelf(levels[2])
    y = levels[2]
    cv.rect(x0 + 4, y - 7, 40, 7, OUT); cv.rect(x0 + 5, y - 6, 38, 5, "#24222c"); cv.hline(x0 + 5, y - 6, 38, "#3a3844")
    for k in range(6):
        rx = x0 + 6 + k * 6
        cv.rect(rx, y - 17, 5, 11, OUT); cv.rect(rx + 1, y - 16, 3, 9, "#2e2c36"); cv.px(rx + 1, y - 16, "#4a4856")
        cv.vline(rx + 3, y - 21, 4, OUT)
        cv.px(rx + 2, y - 3, "#5cf08a" if k != 4 else "#f05c5c")
    cv.rect(x0 + 52, y - 15, 22, 15, OUT); cv.rect(x0 + 53, y - 14, 20, 13, "#2e8a5a"); cv.hline(x0 + 53, y - 14, 20, "#4aaa7a")
    cv.rect(x0 + 61, y - 12, 4, 9, "#f2f2ee"); cv.rect(x0 + 58, y - 9, 10, 3, "#f2f2ee")
    cv.rect(x0 + 80, y - 6, 14, 6, OUT); cv.rect(x0 + 81, y - 5, 12, 4, "#e0b23a"); cv.rect(x0 + 92, y - 5, 2, 4, "#fff0c4")
    # top shelf: hard hats and a folded black drape
    shelf(levels[3])
    y = levels[3]
    cv.rect(x0 + 4, y - 9, 40, 9, OUT); cv.rect(x0 + 5, y - 8, 38, 7, SCRIM[3])
    for fy in (y - 6, y - 3):
        cv.hline(x0 + 5, fy, 38, SCRIM[1])
    cv.hline(x0 + 5, y - 8, 38, SCRIM[4])
    for k, (hx, col) in enumerate([(x0 + 54, "#f2f2ee"), (x0 + 72, "#e0b23a")]):
        cv.ellipse(hx - 1, y - 11, 16, 12, OUT); cv.ellipse(hx, y - 10, 14, 11, col)
        cv.rect(hx - 2, y - 3, 18, 3, OUT); cv.hline(hx - 1, y - 2, 16, shade(col, -0.15))
        cv.vline(hx + 7, y - 10, 7, shade(col, 0.15)); cv.px(hx + 4, y - 8, shade(col, 0.3))
    # front uprights over everything, with feet; a hi-vis vest hung on the right end
    for fx in (x0, x1 - 2):
        cv.rect(fx - 1, top, 4, height + 1, OUT); cv.vline(fx, top + 1, height - 1, st[4]); cv.vline(fx + 1, top + 1, height - 1, st[3])
        for hy in range(top + 4, base - 2, 6):
            cv.px(fx + 1, hy, st[1])
        cv.rect(fx - 2, base - 1, 6, 2, OUT)
    F.hivis_vest(cv, x1 - 6, levels[2] + 4)
    # a strip of tape on the top shelf: which side of the stage this lives on
    cv.rect(x0 + 34, levels[3] + 1, 32, 3, "#e8e4d8")
    for k in range(6):
        cv.hline(x0 + 36 + k * 5, levels[3] + 2, 3, "#2a2a36")
    return cv, ox + width // 2, base


def case_stack(width=100, height=85, seed=0):
    """Backline flight cases stacked by the stage door: a long wheeled case stencilled with the
    band's name, a drum case and a keys case on it, a guitar case lying on top beside a small case
    with a coffee cup left on it. Anchor bottom centre."""
    W, H = width + 8, height + 8
    cv = Canvas(W, H, seed=seed)
    ox, base = 4, H - 3
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.45)
    x0 = ox
    _, t1 = road_case(cv, x0, base, width, 28, top=5, label="LAST LIGHT", label_col="#e6d6b1", wheels=True, lid=0.25)
    red = ["#120c10", "#2a1218", "#4a1e24", "#6a2a30", "#8a3a3e", "#9a9aa4", "#d0d0d8"]
    navy = ["#0e0e18", "#161a2a", "#222a40", "#2e3854", "#40506e", "#9a9aa4", "#d0d0d8"]
    _, t2 = road_case(cv, x0 + 3, t1 + 1, 52, 22, top=4, pal=red, tape="DRUMS")
    _, t3 = road_case(cv, x0 + 58, t1 + 1, 40, 25, top=4, pal=navy, tape="KEYS")
    # guitar case lying on the drum case: a dark tolex body with the guitar's outline
    gy = t2 + 1
    gx = x0 + 4
    pts = [(gx, gy - 4), (gx + 4, gy - 11), (gx + 18, gy - 12), (gx + 24, gy - 9), (gx + 30, gy - 10),
           (gx + 38, gy - 9), (gx + 54, gy - 8), (gx + 54, gy - 3), (gx + 38, gy - 2), (gx + 30, gy - 1),
           (gx + 24, gy - 2), (gx + 18, gy), (gx + 4, gy)]
    cv.poly([(px_ - 1, py_ - 1 if i < 7 else py_ + 1) for i, (px_, py_) in enumerate(pts)], OUT)
    cv.poly(pts, "#2a2430")
    cv.line(gx + 4, gy - 10, gx + 17, gy - 11, "#4a4252"); cv.line(gx + 30, gy - 9, gx + 53, gy - 7, "#4a4252")
    for lx in (gx + 10, gx + 26, gx + 44):
        cv.rect(lx, gy - 2, 3, 2, "#c8c8d0")
    cv.rect(gx + 22, gy - 12, 6, 2, OUT)                                              # handle
    # small case on the keys case with a paper cup on it
    _, t4 = road_case(cv, x0 + 66, t3 + 1, 26, 15, top=3, latches=True)
    cv.rect(x0 + 75, t4 - 6, 6, 7, OUT); cv.rect(x0 + 76, t4 - 5, 4, 5, "#e6e2d8"); cv.hline(x0 + 76, t4 - 3, 4, "#c84a3c")
    cv.hline(x0 + 75, t4 - 6, 6, "#f6f4ee")
    # a set list taped to the big case
    sx = x0 + 6
    cv.rect(sx, base - 19, 10, 12, "#f2ead6"); cv.hline(sx + 2, base - 16, 6, "#6a6a7a")
    cv.hline(sx + 2, base - 13, 5, "#6a6a7a"); cv.hline(sx + 2, base - 10, 6, "#c8382c")
    cv.rect(sx - 1, base - 20, 3, 2, "#b8b4a8"); cv.rect(sx + 8, base - 20, 3, 2, "#b8b4a8")
    return cv, ox + width // 2, base


def _big_text(cv, s, x, y, colour, k=2):
    """Text at k times the font size (block letters a marker would make)."""
    tmp = Canvas(text_width(s) + 2, 10)
    text(tmp, s, 1, 0, colour)
    a = np.repeat(np.repeat(tmp.a, k, 0), k, 1)
    cv.paste(a, x - k, y)


def prep_table(width=140, height=30, seed=0, chosen=False):
    """The prep table in the backstage yard: a trestle with a black cloth, the printed vinyl
    poster zip-tied to its front (EVERYONE PERFORMS, the names already printed under it, IMANI
    among them), lyric sheets and a set list, a mic in its clip, water bottles, a battery lamp, an
    acoustic guitar leaning on the end. chosen: a strip of white tape over PERFORMS reads CHOOSES
    in marker, and Imani's sheet has one verse circled. Anchor bottom centre."""
    rng = _rng(seed)
    W, H = width + 18, height + 30
    cv = Canvas(W, H, seed=seed)
    ox, base = 6, H - 3
    x0, x1 = ox, ox + width
    ground_shadow(cv, ox + width // 2, base, width // 2 + 3, 3, alpha=0.45)
    ttop = base - height                                            # back edge of the table top
    front = ttop + 7                                                # front edge
    cloth = ["#141218", "#1c1a22", "#26232e", "#322e3a"]
    cv.rect(x0 - 1, ttop - 1, width + 2, height + 1, OUT)
    cv.rect(x0, ttop, width, 7, "#3a3640"); cv.hline(x0, ttop, width, "#4a4652")
    cv.rect(x0, front, width, base - front - 1, cloth[1])
    for fx in range(x0 + 3, x1 - 2, 7):                            # cloth folds
        cv.vline(fx, front + 2, base - front - 4, cloth[2])
    cv.hline(x0, front, width, cloth[3]); cv.hline(x0, base - 2, width, cloth[0])
    # the vinyl poster on the front
    pw = text_width("EVERYONE PERFORMS") + 10
    px0 = ox + (width - pw) // 2
    py0 = front + 3
    ph = 19
    cv.rect(px0 - 1, py0 - 1, pw + 2, ph + 2, OUT)
    cv.rect(px0, py0, pw, ph, "#ece2c8"); cv.hline(px0, py0, pw, "#fbf3dc"); cv.hline(px0, py0 + ph - 1, pw, "#c8bc9e")
    cv.rect(px0, py0, pw, 2, "#c8382c")
    text(cv, "EVERYONE PERFORMS", px0 + 5, py0 + 1, "#a02a24")
    # the printed line-up under it: names as grey blocks, IMANI spelled out
    ny = py0 + 11
    nx = px0 + 5
    for k, nw in enumerate([14, 10, None, 16, 12]):
        if nw is None:
            text(cv, "IMANI", nx, ny - 2, "#2a2a36")
            nx += text_width("IMANI") + 4
            continue
        cv.hline(nx, ny + 2, nw, "#8a8478"); cv.hline(nx, ny + 3, nw, "#a49c8c")
        nx += nw + 4
    for (zx, zy) in [(px0 - 2, py0 + 2), (px0 + pw, py0 + 2)]:     # zip ties
        cv.rect(zx, zy, 2, 2, "#e8e4d8")
    if chosen:
        tx = px0 + 5 + text_width("EVERYONE ") - 2
        tw = text_width("PERFORMS") + 4
        cv.rect(tx, py0 + 1, tw, 9, "#f6f4ee"); cv.hline(tx, py0 + 9, tw, "#c8c4b8")
        cv.px(tx - 1, py0 + 2, "#f6f4ee"); cv.px(tx + tw, py0 + 7, "#f6f4ee")
        text(cv, "CHOOSES", tx + 3, py0 + 1, "#1e2a5a")
    # things on the table top (back to front)
    # lyric sheets fanned out
    for k, (sx, rot) in enumerate([(x0 + 10, 0), (x0 + 22, 1), (x0 + 34, -1)]):
        cv.poly([(sx, ttop + 5), (sx + 2 + rot, ttop + 1), (sx + 14 + rot, ttop + 1), (sx + 12, ttop + 5)], "#f2ead6")
        cv.hline(sx + 4 + rot, ttop + 2, 7, "#8a8478"); cv.hline(sx + 3, ttop + 3, 8, "#8a8478")
    if chosen:                                                    # one verse circled in red
        for (px_, py_) in [(x0 + 25, ttop + 2), (x0 + 25, ttop + 3), (x0 + 36, ttop + 2), (x0 + 36, ttop + 3)]:
            cv.px(px_, py_, "#c8382c")
        cv.hline(x0 + 26, ttop + 1, 10, "#c8382c"); cv.hline(x0 + 26, ttop + 4, 10, "#c8382c")
    # mic on a short desk stand, its cable over the edge
    mx = x0 + 56
    cv.rect(mx - 4, ttop + 3, 9, 2, OUT); cv.vline(mx, ttop - 7, 10, IRON[3])
    cv.rect(mx - 2, ttop - 13, 5, 7, OUT); cv.rect(mx - 1, ttop - 12, 3, 5, "#c0c4cc"); cv.hline(mx - 1, ttop - 10, 3, "#8a8e98")
    cv.line(mx + 1, ttop + 4, mx + 6, front + 2, WIRE); cv.line(mx + 6, front + 2, mx + 5, front + 8, WIRE)
    # water bottles
    for k, bx in enumerate((x0 + 72, x0 + 77, x0 + 82)):
        by = ttop + 4 - (k % 2)
        cv.rect(bx - 1, by - 10, 4, 10, OUT); cv.rect(bx, by - 9, 2, 8, "#9ac8e0"); cv.px(bx, by - 8, "#e6f4fa")
        cv.rect(bx, by - 11, 2, 2, "#3a6ac8")
    # set list and a marker
    cv.rect(x0 + 92, ttop + 1, 12, 5, "#f2ead6"); cv.hline(x0 + 94, ttop + 2, 7, "#2a2a36"); cv.hline(x0 + 94, ttop + 4, 5, "#c8382c")
    cv.line(x0 + 106, ttop + 5, x0 + 112, ttop + 3, "#2a2a36"); cv.px(x0 + 112, ttop + 3, "#c8382c")
    # battery lantern
    lx = x0 + 120
    cv.rect(lx - 1, ttop - 8, 8, 12, OUT); cv.rect(lx, ttop - 7, 6, 10, "#3a3844")
    cv.rect(lx + 1, ttop - 5, 4, 5, "#fff0c4"); cv.px(lx + 2, ttop - 4, "#ffffff"); cv.hline(lx + 1, ttop - 9, 4, OUT)
    cv.ellipse(lx - 5, ttop - 10, 16, 14, C(AMBER[3], 0.12))
    # acoustic guitar leaning on the right end of the table
    gx, gb = x1 + 4, base - 1
    body = [(gx - 6, gb), (gx - 9, gb - 6), (gx - 8, gb - 12), (gx - 5, gb - 15), (gx - 6, gb - 19),
            (gx - 4, gb - 23), (gx + 1, gb - 24), (gx + 4, gb - 21), (gx + 3, gb - 16), (gx + 5, gb - 12),
            (gx + 5, gb - 5), (gx + 2, gb)]
    cv.poly([(px_ + (1 if px_ > gx else -1), py_) for (px_, py_) in body], OUT)
    cv.poly(body, "#c88a4a")
    cv.poly([(gx - 5, gb - 2), (gx - 7, gb - 7), (gx - 6, gb - 12), (gx - 3, gb - 14), (gx - 4, gb - 19), (gx - 2, gb - 22), (gx - 1, gb - 6)], "#e0a860")
    cv.ellipse(gx - 4, gb - 14, 5, 5, "#2a1a14")
    cv.line(gx - 1, gb - 24, gx + 3, gb - 44, OUT); cv.line(gx, gb - 24, gx + 4, gb - 44, "#5a3a24")
    cv.rect(gx + 2, gb - 49, 4, 6, OUT); cv.rect(gx + 3, gb - 48, 2, 4, "#3a2418")
    cv.hline(gx - 6, gb - 5, 7, "#3a2418")
    return cv, ox + width // 2, base


def cue_board(width=70, height=42, seed=0, stop=False):
    """The stage manager's cue board on a tripod stand: a white board in a black frame headed ONE
    SONG, the cue lines in marker, the last cue AGAIN in red. stop: AGAIN is struck through and
    STOP is written big under it, readable from the back row. Anchor bottom centre."""
    W, H = width + 8, height + 6
    cv = Canvas(W, H, seed=seed)
    ox, base = 4, H - 3
    cx = ox + width // 2
    ground_shadow(cv, cx, base, 14, 2, alpha=0.45)
    bh = height - 6
    by = base - height
    # tripod
    cv.line(cx, by + bh, cx - 10, base, OUT); cv.line(cx, by + bh, cx + 10, base, OUT); cv.line(cx, by + bh, cx + 1, base - 1, OUT)
    cv.line(cx + 1, by + bh, cx - 9, base, IRON[2]); cv.line(cx - 1, by + bh, cx + 9, base, IRON[3])
    # board
    cv.rect(ox, by, width, bh, OUT)
    cv.rect(ox + 1, by + 1, width - 2, bh - 2, "#3a3844")
    cv.rect(ox + 3, by + 2, width - 6, bh - 5, "#f2f0e8"); cv.hline(ox + 3, by + 2, width - 6, "#ffffff")
    cv.hline(ox + 3, by + bh - 4, width - 6, "#c8c4b8")
    cv.rect(ox + 2, by + bh - 3, width - 4, 2, "#2a2832")                           # pen tray
    cv.rect(ox + 8, by + bh - 4, 8, 1, "#c8382c"); cv.rect(ox + 18, by + bh - 4, 7, 1, "#2a3a8a")
    text(cv, "ONE SONG", ox + (width - text_width("ONE SONG")) // 2, by + (2 if not stop else 0), "#1e2a5a")
    if not stop:
        cv.hline(ox + 6, by + 10, width - 12, "#1e2a5a")
        for k, (lw, col) in enumerate([(36, "#3a3a52"), (28, "#3a3a52")]):
            cv.hline(ox + 6, by + 13 + k * 3, 4, "#3a3a52"); cv.hline(ox + 12, by + 13 + k * 3, lw, col)
        text(cv, "AGAIN", ox + 6, by + 18, "#c8382c")
        cv.hline(ox + 6, by + 26, text_width("AGAIN") + 1, "#c8382c")
        cv.px(ox + width - 18, by + 20, "#c8382c"); cv.vline(ox + width - 18, by + 18, 5, "#c8382c")
        cv.vline(ox + width - 15, by + 18, 5, "#c8382c"); cv.px(ox + width - 15, by + 24, "#c8382c"); cv.px(ox + width - 18, by + 24, "#c8382c")
    else:
        text(cv, "AGAIN", ox + (width - text_width("AGAIN")) // 2, by + 8, "#a8a0a0")
        cv.line(ox + (width - text_width("AGAIN")) // 2 - 2, by + 15, ox + (width + text_width("AGAIN")) // 2 + 1, by + 13, "#c8382c")
        _big_text(cv, "STOP", cx - text_width("STOP") + 1, by + 13, "#c8382c")
    return cv, cx, base


def work_light(height=55, seed=0):
    """A tripod work light: splayed legs, a telescopic mast with a clamp, a halogen flood head
    in a yellow housing with its guard, the cable dropping to the ground. The lens centre sits
    height - 5 above the anchor (the game's point light). Returns (Canvas, ax, ay, (hx, hy))."""
    w = 30
    H = height + 10
    cv = Canvas(w, H, seed=seed)
    cx, base = w // 2, H - 3
    hy = base - (height - 5)
    ground_shadow(cv, cx, base, 11, 2)
    knee = base - 14
    for (fx, c) in [(cx - 11, IRON[2]), (cx + 11, IRON[3]), (cx + 2, IRON[1])]:
        cv.line(cx, knee, fx, base, OUT); cv.line(cx, knee - 1, fx, base - 1, c)
        cv.rect(fx - 1, base - 1, 3, 2, OUT)
    cv.rect(cx - 1, hy + 6, 3, knee - hy - 6, OUT); cv.vline(cx, hy + 6, knee - hy - 6, IRON[4])
    cv.rect(cx - 2, hy + 20, 5, 3, OUT); cv.hline(cx - 1, hy + 21, 3, "#e0b23a")           # clamp knob
    cv.rect(cx - 2, knee - 2, 5, 3, OUT)
    # yoke and head (tilted down a little toward the yard)
    cv.line(cx - 7, hy + 2, cx, hy + 7, OUT); cv.line(cx + 7, hy + 2, cx, hy + 7, OUT)
    cv.rect(cx - 8, hy - 6, 17, 12, OUT)
    cv.rect(cx - 7, hy - 5, 15, 10, "#e0b23a"); cv.hline(cx - 7, hy - 5, 15, "#f2cf5c"); cv.hline(cx - 7, hy + 4, 15, "#b88a2a")
    cv.rect(cx - 5, hy - 3, 11, 7, "#fff4d0"); cv.rect(cx - 4, hy - 2, 9, 4, "#ffffff")
    for gx in range(cx - 4, cx + 6, 3):
        cv.vline(gx, hy - 3, 7, C("#3a3644", 0.6))
    for k in range(1, 5):
        cv.hline(cx - 7, hy - 6 - k * 0, 15, OUT)
    cv.rect(cx - 6, hy - 9, 13, 3, OUT); cv.hline(cx - 5, hy - 8, 11, "#3a3644")             # handle
    cv.ellipse(cx - 13, hy - 10, 27, 20, C("#fff0c4", 0.1))
    # cable
    for yy in range(hy + 7, knee):
        cv.px(cx + 2, yy, WIRE)
    cv.line(cx + 2, knee, cx + 9, base + 1, WIRE)
    return cv, cx, base, (cx, hy)


def portacabin(cv, x, base, w, h, label, seed=0, door_x=None, door_open=False, windows=(), ac=False,
               notices=0, lift=6):
    """A site cabin standing on sleepers at the back of the yard: ribbed steel siding, the roof's
    lit edge, windows with half-drawn blinds glowing warm, a steel door (open: the lit room inside),
    a cream name plate, a bulkhead lamp over the door, alu steps, an AC box, taped notices.
    windows: [(dx, width)] from x. Returns {'lamp': (x, y), 'door': (x, y, w, h), 'windows': [...]}."""
    rng = _rng(seed)
    sb = base - lift                                    # bottom of the cabin body
    top = base - h
    info = {"windows": []}
    # sleepers and the dark gap under it
    cv.rect(x + 2, sb, w - 4, lift, "#14121a")
    for bx in range(x + 6, x + w - 8, max(20, w // 5)):
        cv.rect(bx, sb + 1, 8, lift - 1, "#3a3036"); cv.hline(bx, sb + 1, 8, "#4e4248")
    # body: ribbed siding
    cv.rect(x - 1, top - 1, w + 2, sb - top + 2, OUT)
    cv.rect(x, top, w, sb - top, CABIN[3])
    for xx in range(x + 2, x + w - 2, 4):
        cv.vline(xx, top + 4, sb - top - 5, CABIN[4]); cv.vline(xx + 1, top + 4, sb - top - 5, CABIN[2])
    for k in range(5):                                   # grime rising from the ground
        cv.hline(x, sb - 1 - k, w, C(F.DIRT[1], 0.32 - k * 0.06))
    # corner posts and roof edge
    for cx_ in (x, x + w - 4):
        cv.rect(cx_, top, 4, sb - top, CABIN[2]); cv.vline(cx_ + (0 if cx_ == x else 3), top, sb - top, CABIN[4] if cx_ == x else CABIN[1])
    cv.rect(x - 2, top - 4, w + 4, 5, OUT)
    cv.hline(x - 1, top - 3, w + 2, CABIN[6]); cv.hline(x - 1, top - 2, w + 2, CABIN[5]); cv.hline(x - 1, top - 1, w + 2, CABIN[2])
    cv.hline(x, top, w, CABIN[1])
    # windows
    for (dx, ww) in windows:
        wx, wy, wh = x + dx, top + 10, 16
        cv.rect(wx - 2, wy - 2, ww + 4, wh + 4, OUT); cv.rect(wx - 1, wy - 1, ww + 2, wh + 2, CABIN[1])
        cv.rect(wx, wy, ww, wh, F.BULB[2]); cv.rect(wx, wy + wh // 2, ww, wh // 2, F.BULB[1])
        cv.rect(wx, wy, ww, 7, "#d8cdb0")                                     # blind half down
        for by in range(wy + 1, wy + 7, 2):
            cv.hline(wx, by, ww, "#b8ac90")
        cv.hline(wx, wy + 7, ww, "#8a7c62")
        cv.vline(wx + ww // 2, wy + 8, wh - 8, CABIN[1])
        cv.rect(wx - 2, wy + wh + 1, ww + 4, 2, CABIN[5])                     # sill
        cv.ellipse(wx - 6, wy + wh, ww + 12, 8, C(F.BULB[2], 0.08))
        info["windows"].append((wx, wy, ww, wh))
    # door, steps, lamp
    if door_x is not None:
        dx0, dw, dh = x + door_x, 17, sb - top - 8
        dy0 = sb - dh
        cv.rect(dx0 - 2, dy0 - 2, dw + 4, dh + 2, OUT)
        if door_open:
            cv.rect(dx0, dy0, dw, dh, F.BULB[2]); cv.rect(dx0, dy0, dw, 6, F.BULB[3])
            cv.rect(dx0 + 2, dy0 + 8, 5, dh - 8, "#c8a070")                   # the room inside: a coat rack
            cv.vline(dx0 + 12, dy0 + 4, dh - 4, "#8a6a4a"); cv.hline(dx0 + 10, dy0 + 6, 5, "#8a6a4a")
            cv.rect(dx0 + 9, dy0 + 7, 3, 9, "#5a3a52"); cv.rect(dx0 + 13, dy0 + 7, 3, 7, "#3a5a6a")
            cv.poly([(dx0 - 1, dy0 - 1), (dx0 - 7, dy0 + 3), (dx0 - 7, sb + 1), (dx0 - 1, sb)], OUT)   # leaf swung out
            cv.poly([(dx0 - 2, dy0), (dx0 - 6, dy0 + 4), (dx0 - 6, sb), (dx0 - 2, sb - 1)], "#3a4a5e")
            cv.vline(dx0 - 3, dy0 + 3, dh - 4, "#4e6078")
            cv.poly([(dx0, sb + 1), (dx0 + dw, sb + 1), (dx0 + dw + 8, sb + lift + 6), (dx0 - 8, sb + lift + 6)], C(F.BULB[2], 0.16))
        else:
            cv.rect(dx0, dy0, dw, dh, "#3a4a5e"); cv.vline(dx0, dy0, dh, "#4e6078")
            cv.rect(dx0 + 4, dy0 + 4, 9, 7, OUT); cv.rect(dx0 + 5, dy0 + 5, 7, 5, F.BULB[2])
            cv.rect(dx0 + 12, dy0 + dh // 2, 3, 2, "#c8c8d0")
        # name plate beside the door
        pw = text_width(label) + 6
        px_ = dx0 + dw + 6 if dx0 + dw + 6 + pw < x + w - 4 else dx0 - pw - 6
        cv.rect(px_ - 1, top + 8, pw + 2, 11, OUT); cv.rect(px_, top + 9, pw, 9, "#e6d6b1"); cv.hline(px_, top + 9, pw, "#fff3d6")
        text(cv, label, px_ + 3, top + 8, "#2a2a36")
        # bulkhead lamp over the door
        lx, ly = dx0 + dw // 2, dy0 - 6
        cv.rect(lx - 4, ly - 2, 9, 5, OUT); cv.rect(lx - 3, ly - 1, 7, 3, "#fff0c4"); cv.px(lx, ly, "#ffffff")
        cv.ellipse(lx - 10, ly - 5, 21, 12, C("#fff0c4", 0.12))
        info["lamp"] = (lx, ly)
        info["door"] = (dx0, dy0, dw, dh)
        # alu steps with a handrail
        sx0 = dx0 - 4
        for k in range(2):
            sy = sb + k * 4
            cv.rect(sx0 - k * 2 - 1, sy - 1, dw + 8 + k * 4 + 2, 5, OUT)
            cv.rect(sx0 - k * 2, sy, dw + 8 + k * 4, 3, TRACK[4]); cv.hline(sx0 - k * 2, sy, dw + 8 + k * 4, TRACK[6])
            for rx in range(sx0 - k * 2 + 1, sx0 + dw + 8 + k * 2, 3):
                cv.px(rx, sy + 2, TRACK[2])
        rx = dx0 + dw + 5
        cv.vline(rx, dy0 + 10, sb + 8 - dy0 - 10, OUT); cv.vline(rx + 1, dy0 + 10, sb + 8 - dy0 - 10, TRACK[5])
        cv.line(rx, dy0 + 10, rx + 4, dy0 + 14, TRACK[5])
    if ac:
        ax_ = x + w - 26
        cv.rect(ax_ - 1, top + 5, 18, 13, OUT); cv.rect(ax_, top + 6, 16, 11, "#d2d0c8"); cv.hline(ax_, top + 6, 16, "#ecebe4")
        cv.ellipse(ax_ + 2, top + 7, 9, 9, "#8a8a90"); cv.ellipse(ax_ + 3, top + 8, 7, 7, "#5a5a62")
        cv.line(ax_ + 4, top + 9, ax_ + 8, top + 13, "#a8a8ae"); cv.line(ax_ + 8, top + 9, ax_ + 4, top + 13, "#a8a8ae")
        for gy in range(top + 8, top + 16, 2):
            cv.hline(ax_ + 12, gy, 3, "#8a8a90")
        cv.vline(ax_ + 8, top + 18, sb - top - 18, "#6a6a72")                 # drain pipe
    for k in range(notices):
        nx = x + 8 + int(rng.integers(0, max(1, w - 30)))
        ny = top + 30 + int(rng.integers(0, 8))
        cv.rect(nx, ny, 9, 11, "#f2ead6"); cv.hline(nx + 1, ny + 2, 7, "#6a6a7a"); cv.hline(nx + 1, ny + 4, 5, "#6a6a7a")
        cv.hline(nx + 1, ny + 6, 6, "#c8382c" if k % 2 else "#6a6a7a")
        cv.rect(nx + 3, ny - 1, 3, 2, C("#e8e4d8", 0.8))
    return info


def generator(cv, x, base, w=48, h=30, label="GEN3", seed=0):
    """A silenced diesel generator on its skids: green steel canopy with louvres, the control
    door with a small lit display, the exhaust stack blackened at the top, outlet sockets with
    cables plugged in. Returns {'led': (x, y), 'exhaust': (x, y)}."""
    g = ["#18241e", "#22342a", "#304836", "#3e5c44", "#4e7254", "#6a8e6a", "#8aac84"]
    y = base - h
    cv.rect(x - 2, base - 3, w + 4, 3, OUT); cv.hline(x - 1, base - 2, w + 2, "#3a3644")     # skids
    cv.rect(x - 1, y - 4, w + 2, h + 2, OUT)
    cv.rect(x, y - 3, w, 4, g[5]); cv.hline(x, y - 3, w, g[6])                               # roof
    cv.rect(x, y + 1, w, h - 4, g[3]); cv.vline(x, y + 1, h - 4, g[4]); cv.vline(x + w - 1, y + 1, h - 4, g[2])
    for ly in range(y + 4, base - 15, 3):                                                     # louvres
        cv.hline(x + 3, ly, 14, g[1]); cv.hline(x + 3, ly + 1, 14, g[4])
    cv.rect(x + 21, y + 4, 14, h - 10, OUT); cv.rect(x + 22, y + 5, 12, h - 12, g[2])           # control door
    cv.rect(x + 24, y + 7, 8, 4, "#0e1a14"); cv.hline(x + 25, y + 8, 5, "#5cf08a")
    cv.px(x + 25, y + 13, "#f05c5c"); cv.px(x + 28, y + 13, "#5cf08a")
    text(cv, label, x + 1, base - 15, "#e6e2d0")
    for k, col in enumerate(["#e0b23a", "#3a6ac8", "#c8382c"]):                             # outlets
        sx = x + 37 + (k % 2) * 5
        sy = y + 16 + (k // 2) * 5
        cv.rect(sx, sy, 4, 4, OUT); cv.rect(sx + 1, sy + 1, 2, 2, col)
    ex = x + 8
    cv.rect(ex - 1, y - 14, 5, 11, OUT); cv.rect(ex, y - 13, 3, 10, "#5a5a62"); cv.rect(ex, y - 13, 3, 3, "#1a1820")
    cv.vline(ex + 2, y - 10, 7, "#7a7a82")
    return {"led": (x + 28, y + 8), "exhaust": (ex + 1, y - 14)}


def scrim_fence(cv, x0, x1, base, height=58, panel=100, gaps=(), seed=0, signs=()):
    """Heras fence panels along the back of the yard, clad in black scrim: round posts on rubber
    feet with couplers at the top, the scrim cable-tied to the top rail with a little sag between
    ties. gaps: [(xa, xb)] gate openings with a caged lamp on each post. signs: [(x, text)].
    Returns lamp points."""
    rng = _rng(seed)
    top = base - height
    pts = []
    def in_gap(xx):
        return any(a <= xx < b for (a, b) in gaps)
    for xx in range(x0, x1):
        if in_gap(xx):
            continue
        k = (xx - x0) % panel
        sag = int(round(1.5 * np.sin(np.pi * ((xx - x0) % 16) / 16)))
        for yy in range(top + 3 + sag, base - 5):
            cv.px(xx, yy, SCRIM[2] if (xx + yy) % 3 else SCRIM[3])
        cv.px(xx, top + 3 + sag, SCRIM[4])
        if (xx - x0) % 16 == 0:
            cv.px(xx, top + 2, "#c8c8d0")
        if k % 23 == 7:
            cv.vline(xx, top + 6 + sag, height - 12, SCRIM[1])                 # folds
        cv.hline(xx, top + 1, 1, F.STEEL[4]); cv.px(xx, top + 2, F.STEEL[2])
        cv.px(xx, base - 5, SCRIM[0])
    posts = [p for p in range(x0, x1 + 1, panel) if not in_gap(p)] + [b for g in gaps for b in (g[0] - 2, g[1])]
    for px_ in posts:
        cv.rect(px_ - 2, top - 2, 5, height - 2, OUT); cv.vline(px_ - 1, top - 1, height - 4, F.STEEL[5]); cv.vline(px_, top - 1, height - 4, F.STEEL[3])
        cv.rect(px_ - 7, base - 6, 15, 6, OUT); cv.rect(px_ - 6, base - 5, 13, 4, "#3a3644"); cv.hline(px_ - 6, base - 5, 13, "#5a5666")
        cv.rect(px_ - 3, top + 4, 7, 4, OUT); cv.hline(px_ - 2, top + 5, 5, F.STEEL[4])
    for (a, b) in gaps:
        for gx in (a - 2, b):
            cv.rect(gx - 3, top - 10, 7, 8, OUT); cv.rect(gx - 2, top - 9, 5, 6, F.BULB[2]); cv.px(gx, top - 8, F.BULB[3])
            cv.vline(gx - 2, top - 9, 6, C(OUT, 0.5)); cv.vline(gx + 2, top - 9, 6, C(OUT, 0.5))
            pts.append([gx, top - 7, "f6cf7a", 1])
    for (sx, s) in signs:
        sw = text_width(s) + 8
        cv.rect(sx - 1, top + 14, sw + 2, 13, OUT); cv.rect(sx, top + 15, sw, 11, "#e6e2d8"); cv.hline(sx, top + 15, sw, "#f6f4ee")
        cv.rect(sx, top + 15, sw, 2, "#c8382c")
        text(cv, s, sx + 4, top + 15, "#2a2a36")
        for (zx, zy) in [(sx + 1, top + 16), (sx + sw - 3, top + 16)]:
            cv.rect(zx, zy, 2, 2, "#8a8a92")
    return pts


def cue_light(cv, x, y):
    """A cue-light box screwed to a scaffold upright: red standby and green go lamps (unlit
    here; the room animates them). Returns (red point, green point)."""
    cv.rect(x - 1, y - 1, 8, 15, OUT); cv.rect(x, y, 6, 13, "#2a2832"); cv.hline(x, y, 6, "#3a3844")
    cv.rect(x + 1, y + 2, 4, 4, "#5a1a1a"); cv.rect(x + 1, y + 7, 4, 4, "#1a4a2a")
    return (x + 1, y + 2), (x + 1, y + 7)


def stage_back(cv, x0, x1, base, seed=0, show=True):
    """The main stage seen from behind its upstage corner, filling the back of the yard: the arched
    roof truss climbing off the top, the wing tower, scaffold clad in black scrim with one bay
    rolled up on the back of the LED wall (grey cabinets, data looms, status LEDs) with the show's
    light leaking round it, the upstage deck with a load-in ramp and waiting cases, a SHOW IN
    PROGRESS box. show=False: the show is over, the leaks and halo are dark, the box unlit.
    Returns {'leds': [...], 'lamps': [...], 'show_box': (x, y, w, h), 'truss': [(x, y)...]}."""
    rng = _rng(seed)
    info = {"leds": [], "lamps": [], "truss": []}
    w = x1 - x0
    deck_y = base - 40
    # halo of the show over the roof
    if show:
        for (r, a) in [(200, 0.06), (150, 0.07), (100, 0.09)]:
            cv.ellipse(x1 - r + 40, -r // 2, 2 * r, r, C("#d08ab8", a))
    def arch(x):                                   # the roof truss climbs to the right, off the top
        t = (x - x0) / max(1, w)
        return int(round(30 - 52 * t + 8 * t * t))
    # scaffold wall behind (standards and ledgers), then scrim over it
    wall_top = lambda x: arch(x) + 12
    for x in range(x0 + 20, x1):
        for y in range(max(0, wall_top(x)), deck_y):
            cv.px(x, y, SCRIM[3] if (x + y) % 3 else SCRIM[4])
    # the scaffold over the scrim: standards, ledgers, a brace in some bays
    for sx in range(x0 + 44, x1, 34):
        if show:                                                       # the show leaking through the seams
            for y in range(max(0, wall_top(sx) + 2), deck_y - 2):
                t = (y - wall_top(sx)) / max(1, deck_y - wall_top(sx))
                cv.px(sx + 3, y, C("#f0a0c8" if t < 0.6 else "#f6c27a", 0.35 + 0.25 * (1 - t)))
    for ly in range(40, deck_y - 4, 22):
        for x in range(x0 + 20, x1):
            if ly > wall_top(x) + 2:
                cv.px(x, ly, TRUSS[4]); cv.px(x, ly + 1, TRUSS[1])
    for i, sx in enumerate(range(x0 + 44, x1, 34)):
        top_ = max(0, wall_top(sx))
        if i % 2 == 0 and sx + 34 < x1:
            cv.line(sx + 2, deck_y - 2, sx + 32, max(0, wall_top(sx + 32) + 4), TRUSS[3])
        cv.rect(sx - 1, top_, 2, deck_y - top_, TRUSS[5]); cv.vline(sx + 1, top_, deck_y - top_, TRUSS[1])
        for cy in range(44, deck_y - 4, 22):
            if cy > top_:
                cv.rect(sx - 2, cy - 1, 4, 4, TRUSS[2]); cv.px(sx - 1, cy, TRUSS[6])
    # the gap under the roof: the lit inside of the stage seen over the top of the scrim
    for x in range(x0 + 20, x1):
        for k, (col, a) in enumerate([("#d07aa8", 1.0), ("#f0a0c8", 0.8), ("#f6c0d8", 0.4)] if show else
                                     [("#1c1620", 1.0), ("#1a1420", 0.8), ("#18121c", 0.4)]):
            cv.px(x, arch(x) + 11 + k, C(col, a))
    for ly in range(46, deck_y, 26):
        for x in range(x0 + 20, x1):
            if ly > wall_top(x) + 2 and (x // 3) % 2 == 0:
                cv.px(x, ly, SCRIM[4])
    # the rolled-up bay: the back of the LED wall, light leaking round it
    bx0, bx1 = x0 + 92, x0 + 170
    by0, by1 = wall_top(bx1) + 14, deck_y - 6
    cv.rect(bx0 - 2, by0 - 6, bx1 - bx0 + 4, 7, OUT)                                         # rolled scrim
    for x in range(bx0 - 1, bx1 + 1):
        cv.vline(x, by0 - 5, 5, SCRIM[3] if x % 4 else SCRIM[1]); cv.px(x, by0 - 5, SCRIM[4])
    cv.rect(bx0, by0, bx1 - bx0, by1 - by0, "#2a1830" if show else "#141018")
    if show:
        for k, (col, a) in enumerate([("#f2a0c8", 0.5), ("#c8a0f0", 0.4), ("#fff0c4", 0.35)]):
            cv.rect(bx0 + k, by0 + k, bx1 - bx0 - 2 * k, 2, C(col, a))
            cv.rect(bx0 + k, by0, 2, by1 - by0, C(col, a * 0.6)); cv.rect(bx1 - 2 - k, by0, 2, by1 - by0, C(col, a * 0.6))
    lx0, lx1 = bx0 + 6, bx1 - 6
    for cy in range(by0 + 5, by1 - 2, 12):                                                   # LED cabinets
        for cx in range(lx0, lx1 - 10, 12):
            cv.rect(cx, cy, 11, 11, "#3a3a44"); cv.hline(cx, cy, 11, "#55525e"); cv.vline(cx + 10, cy, 11, "#24222c")
            cv.rect(cx + 3, cy + 3, 5, 4, "#2a2a32")
            led = (cx + 8, cy + 8)
            cv.px(led[0], led[1], "#5cf08a" if show else "#2a4a3a")
            info["leds"].append([led[0], led[1], "5cf08a" if (cx // 12 + cy // 12) % 3 else "6ab0ff", 1])
        cv.hline(lx0, cy + 11, lx1 - lx0 - 6, "#1a1820")
    for k, lx in enumerate(range(lx0 + 4, lx1 - 8, 12)):                                     # data looms
        cv.line(lx, by0 + 2, lx + 3, by1, "#2a4a8a" if k % 2 else "#1e1c24")
    # the wing tower at the left end, under the truss
    info["lamps"] += scaffold_tower(cv, x0, arch(x0) + 6, deck_y + 2, 20, seed=seed, scrim_from=arch(x0) + 40, lamps=2)
    # roof truss with the backs of its lamps, light falling from them inside the wall's top
    for x in range(x0 - 4, x1):
        cv.vline(x, arch(x) - 6, 3, C(TRUSS[0], 0.6))
    truss_band(cv, x0 - 4, x1, arch, 11)
    for i, lx in enumerate(range(x0 + 30, x1 - 6, 24)):
        ty = arch(lx) + 11
        cv.rect(lx - 3, ty, 7, 8, OUT); cv.rect(lx - 2, ty + 1, 5, 6, TRUSS[3]); cv.px(lx - 1, ty + 1, TRUSS[5])
        cv.vline(lx, ty - 2, 2, TRUSS[4])
        info["truss"].append((lx, ty + 8))
        if show:
            col = LAMP_COLOURS[i % len(LAMP_COLOURS)]
            cv.rect(lx - 2, ty + 7, 5, 1, C(col, 0.8))
            info["lamps"].append([lx, ty + 7, col.lstrip("#")])
    # upstage deck: black skirt, a lip of light, cases waiting, the ramp down to the yard
    cv.rect(x0 + 18, deck_y, w - 18, base - deck_y, SKIRT[1])
    for sx in range(x0 + 20, x1, 5):
        cv.vline(sx, deck_y + 3, base - deck_y - 4, SKIRT[2])
    cv.hline(x0 + 18, deck_y, w - 18, LIP[2] if show else SKIRT[3]); cv.hline(x0 + 18, deck_y + 1, w - 18, LIP[0] if show else SKIRT[2])
    cv.rect(x0 + 18, deck_y + 2, w - 18, 2, SKIRT[0])
    for (cx, cw, ch, pal) in [(x0 + 190, 34, 18, CASE), (x0 + 226, 24, 12, CASE)]:
        if cx + cw < x1:
            road_case(cv, cx, deck_y - 1, cw, ch, top=3, pal=pal)
    # ramp: from the yard up to the deck, hazard edges, rubber treads
    rx0, rx1 = x0 + 26, x0 + 92
    for x in range(rx0, rx1):
        t = (x - rx0) / (rx1 - rx0)
        yy = int(round(base - 2 - t * (base - 2 - deck_y)))
        cv.vline(x, yy, base - yy, PLY[2] if False else "#4a4038")
        cv.px(x, yy, F.HAZARD[3] if (x // 4) % 2 else F.HAZARD[1]); cv.px(x, yy + 1, F.HAZARD[3] if (x // 4) % 2 else F.HAZARD[1])
        if x % 5 == 0:
            cv.vline(x, yy + 3, max(0, base - yy - 4), "#3a322c")
    cv.line(rx0, base - 1, rx1, deck_y, OUT)
    info["blues"] = []
    for bx in range(x0 + 104, x1 - 4, 38):                               # blue running lights on the deck edge
        cv.rect(bx - 1, deck_y - 3, 4, 3, OUT); cv.rect(bx, deck_y - 2, 2, 1, "#6a8aff")
        cv.ellipse(bx - 5, deck_y - 6, 12, 8, C("#6a8aff", 0.14))
        info["blues"].append([bx, deck_y - 2, "8aa8ff", 1])
    # the SHOW IN PROGRESS box on the scrim beside the ramp
    sx, sy = x0 + 186, deck_y - 30
    sw = text_width("SHOW ON") + 8
    cv.rect(sx - 1, sy - 1, sw + 2, 13, OUT); cv.rect(sx, sy, sw, 11, "#3a1418" if not show else "#c8382c")
    cv.hline(sx, sy, sw, "#5a2028" if not show else "#f06a5a")
    text(cv, "SHOW ON", sx + 4, sy, "#5a3a3a" if not show else "#ffe8d8")
    info["show_box"] = (sx, sy, sw, 11)
    # STAGE LEFT stencil on the scrim
    text(cv, "STAGE LEFT", x0 + 26, deck_y - 22, C("#c8c8d0", 0.5))
    return info


def rug(cv, x, y, w, h, seed=0, field=("#5a1a24", "#7a2430", "#9a3038"), border=("#1e2a4a", "#e6d6b1", "#c88a3a")):
    """An old patterned rug laid on the grass for the artists: a red field with a stepped
    medallion, a navy border with a cream running pattern, tassels at both ends."""
    rng = _rng(seed)
    cv.rect(x - 1, y - 1, w + 2, h + 2, C("#0d0b16", 0.5))
    cv.rect(x, y, w, h, border[0])
    b = 6
    cv.rect(x + b, y + b // 2 + 1, w - 2 * b, h - b - 2, field[1])
    for xx in range(x + 2, x + w - 2, 4):                               # running pattern in the border
        cv.px(xx, y + 2, border[1]); cv.px(xx + 1, y + 3, border[2])
        cv.px(xx, y + h - 3, border[1]); cv.px(xx + 1, y + h - 4, border[2])
    for yy in range(y + 3, y + h - 3, 3):
        cv.px(x + 2, yy, border[1]); cv.px(x + w - 3, yy, border[1])
        cv.px(x + 3, yy + 1, border[2]); cv.px(x + w - 4, yy + 1, border[2])
    cx, cy = x + w // 2, y + h // 2
    for k, col in enumerate([field[0], border[2], field[2], border[1], field[0]]):   # medallion
        rx, ry = (w // 4) - k * 6, (h // 2 - 5) - k * 3
        if rx < 2 or ry < 1:
            break
        cv.poly([(cx - rx, cy), (cx, cy - ry), (cx + rx, cy), (cx, cy + ry)], col)
    for (ex, ey) in [(x + b + 4, y + b), (x + w - b - 10, y + b), (x + b + 4, y + h - b - 4), (x + w - b - 10, y + h - b - 4)]:
        cv.poly([(ex, ey + 2), (ex + 3, ey), (ex + 6, ey + 2), (ex + 3, ey + 4)], border[2])
    for _ in range(w * h // 300):                                        # wear and mud
        wx, wy = x + int(rng.integers(2, w - 6)), y + int(rng.integers(2, h - 2))
        cv.hline(wx, wy, int(rng.integers(2, 6)), C(F.DIRT[2], 0.4))
    for xx in (x - 3, x + w):                                            # tassels
        for yy in range(y + 1, y + h - 1, 2):
            cv.hline(xx, yy, 3, "#d8ccb0" if (yy // 2) % 2 else "#b8ac90")


def crew_gate(cv, x, ya, yb):
    """A crew gate in a hedge or fence line at a room's right edge: two scaffold posts on rubber
    feet with a caged work lamp on each, the hazard-striped drop bar swung up against the near
    post, a CREW tag on the far post. Returns twinkle points for the lamps."""
    pts = []
    for gy in (ya, yb):
        cv.rect(x - 3, gy - 46, 6, 48, OUT); cv.vline(x - 2, gy - 45, 46, F.STEEL[5]); cv.vline(x - 1, gy - 45, 46, F.STEEL[4])
        cv.vline(x, gy - 45, 46, F.STEEL[3]); cv.vline(x + 1, gy - 45, 46, F.STEEL[2])
        for yy in range(gy - 40, gy - 4, 12):
            cv.rect(x - 4, yy, 8, 3, OUT); cv.hline(x - 3, yy + 1, 6, F.STEEL[3])          # couplers
        cv.rect(x - 7, gy, 15, 5, OUT); cv.rect(x - 6, gy + 1, 13, 3, "#3a3644"); cv.hline(x - 6, gy + 1, 13, "#5a5666")
        cv.rect(x - 8, gy - 56, 17, 15, C(F.BULB[2], 0.1))
        cv.rect(x - 4, gy - 53, 9, 9, OUT); cv.rect(x - 3, gy - 52, 7, 7, F.BULB[2]); cv.rect(x - 2, gy - 51, 4, 4, F.BULB[3])
        cv.vline(x, gy - 52, 7, IRON[1]); cv.hline(x - 3, gy - 49, 7, IRON[1])
        pts.append([x, gy - 49, "f6cf7a", 2])
    for k in range(34):
        c = F.HAZARD[3] if (k // 4) % 2 == 0 else "#e6e2d8"
        px_, py_ = x - 4 - k // 4, yb - 8 - k
        cv.px(px_, py_, c); cv.px(px_ - 1, py_, shade(c, -0.3))
    label = "CREW"
    lw = text_width(label) + 6
    cv.rect(x - lw - 4, ya - 34, lw, 11, OUT); cv.rect(x - lw - 3, ya - 33, lw - 2, 9, F.HAZARD[3])
    text(cv, label, x - lw - 1, ya - 34, "#1a1720")
    cv.hline(x - 4, ya - 30, 2, OUT)
    return pts


def confetti(cv, x, y, w, h, n=200, seed=0, mask=None):
    """Confetti from the last song scattered flat on the ground: 2x1 and 1x2 flecks."""
    rng = _rng(seed)
    cols = ["#f06a8a", "#f6cf7a", "#7ad0c8", "#c8a0f0", "#f2f2ee", "#f0904a"]
    for _ in range(n):
        px_, py_ = x + int(rng.integers(0, w)), y + int(rng.integers(0, h))
        if mask is not None and not (0 <= py_ < mask.shape[0] and 0 <= px_ < mask.shape[1] and mask[py_, px_]):
            continue
        c = cols[int(rng.integers(len(cols)))]
        if rng.random() < 0.6:
            cv.hline(px_, py_, 2, c)
        else:
            cv.vline(px_, py_, 2, c)
        cv.px(px_, py_ + (1 if rng.random() < 0.6 else 2), C("#0d0b16", 0.25))


def glow_stick(cv, x, y, c="#7af08a", seed=0):
    """A spent glow stick lying on the grass, still faintly lit."""
    rng = _rng(seed)
    d = int(rng.integers(-1, 2))
    cv.line(x, y, x + 5, y + d, c); cv.line(x, y + 1, x + 5, y + d + 1, C(c, 0.4))
    cv.ellipse(x - 3, y - 3, 12, 7, C(c, 0.12))


def campus_far(cv, x, base, w=150, seed=0):
    """Campus buildings far off past the field: sandstone walls under red tile roofs, rows of lit
    windows, the library's tall arched windows and portico at the centre (Norlin), lamps on the
    walk that climbs to its steps. Returns twinkle points (windows, lamps)."""
    rng = _rng(seed)
    pts = []
    stone = ["#4a3a3a", "#5e4a44", "#76604e", "#8a7258"]
    roof = ["#4a2424", "#6a3028", "#8a4030"]
    cx = x + w // 2
    for (bx, bw, bh) in [(x, w // 4, 22), (x + w * 3 // 4, w // 4, 20)]:          # wings either side
        cv.rect(bx, base - bh, bw, bh, stone[1]); cv.hline(bx, base - bh, bw, stone[2])
        cv.poly([(bx - 2, base - bh), (bx + 4, base - bh - 7), (bx + bw - 4, base - bh - 7), (bx + bw + 2, base - bh)], roof[1])
        cv.hline(bx + 4, base - bh - 7, bw - 8, roof[2])
        for wx in range(bx + 4, bx + bw - 4, 6):
            for wy in (base - bh + 5, base - bh + 12):
                lit = rng.random() < 0.55
                cv.rect(wx, wy, 2, 3, F.BULB[2] if lit else stone[0])
                if lit and rng.random() < 0.3:
                    pts.append([wx, wy + 1, "f6dca0", 1])
    lw = w // 2 + 4
    lx = cx - lw // 2
    cv.rect(lx, base - 34, lw, 34, stone[2]); cv.hline(lx, base - 34, lw, stone[3])
    cv.poly([(lx - 3, base - 34), (lx + 8, base - 46), (lx + lw - 8, base - 46), (lx + lw + 3, base - 34)], roof[1])
    cv.hline(lx + 8, base - 46, lw - 16, roof[2]); cv.hline(lx - 3, base - 34, lw + 6, roof[0])
    for k, wx in enumerate(range(lx + 6, lx + lw - 6, 9)):                         # tall arched windows
        cv.rect(wx, base - 28, 4, 14, F.BULB[2]); cv.px(wx, base - 28, stone[2]); cv.px(wx + 3, base - 28, stone[2])
        cv.hline(wx, base - 22, 4, F.BULB[1])
        if k % 2 == 0:
            pts.append([wx + 2, base - 24, "f6dca0", 1])
    cv.rect(cx - 10, base - 12, 20, 12, stone[1])                                   # portico and steps
    for k in range(5):
        cv.vline(cx - 9 + k * 4, base - 11, 9, stone[3])
    for k in range(3):
        cv.hline(cx - 12 - k * 2, base - 2 + k, 24 + k * 4, stone[3] if k % 2 == 0 else stone[2])
    return pts


def sky_east(width, height, seed=0, stars=50, horizon=None, moon=None):
    """The sky looking away from the Flatirons at dusk: stepped bands from deep violet overhead to
    the pink belt of Venus above a blue-grey earth-shadow band at the horizon (y = horizon, default
    the strip's bottom), a few long cloud streaks lit pink underneath, early stars, and optionally
    the full moon rising in the belt (moon = (x, y, r)). Returns an RGBA array (height, width, 4)."""
    rng = _rng(seed)
    hz = height if horizon is None else horizon
    cv = Canvas(width, height, seed=seed)
    bands = [("#1a1632", 0.0), ("#211c3e", 0.14), ("#2a2248", 0.27), ("#352852", 0.39), ("#452e5a", 0.5),
             ("#5a3662", 0.59), ("#743e68", 0.67), ("#8e4a6e", 0.74), ("#a65a74", 0.8), ("#b86a78", 0.85),
             ("#8a6480", 0.9), ("#5e5a80", 0.95), ("#4c5078", 1.0)]
    for k, (col, t0) in enumerate(bands):
        t1 = bands[k + 1][1] if k + 1 < len(bands) else height / max(1, hz) + 1
        y0, y1 = int(t0 * hz), int(t1 * hz)
        cv.rect(0, y0, width, max(0, min(height, y1) - y0), col)
        if k:   # a ragged join between bands, as in the painted skies
            prev = bands[k - 1][0]
            for x in range(0, width, 2):
                if rng.random() < 0.35:
                    cv.px(x, y0, prev)
    for _ in range(stars):
        sx, sy = int(rng.integers(0, width)), int(rng.integers(0, int(hz * 0.5)))
        cv.px(sx, sy, "#e8e0f0" if rng.random() < 0.6 else "#f6dca0")
    if moon:
        mx, my, r = moon
        cv.ellipse(mx - r - 2, my - r - 2, 2 * r + 5, 2 * r + 5, C("#f6dcc8", 0.16))      # one crisp halo step
        cv.ellipse(mx - r, my - r, 2 * r + 1, 2 * r + 1, "#f2d6c0")
        cv.ellipse(mx - r + 1, my - r, 2 * r - 1, 2 * r - 1, "#fbe8d4")
        for (dx, dy, s) in ((-3, -2, 3), (2, 1, 2), (-1, 3, 2), (3, -3, 1)):
            cv.ellipse(mx + dx - s // 2, my + dy - s // 2, s, s, "#e2c2b0")
    for _ in range(9):                                       # cloud streaks, some across the moon
        cx, cy = int(rng.integers(-40, width)), int(rng.integers(int(hz * 0.2), int(hz * 0.8)))
        L = int(rng.integers(40, 120))
        for k in range(3):
            xx = cx + k * 9 + int(rng.integers(0, 6))
            ll = L - k * 22
            if ll < 8:
                break
            cv.hline(xx, cy + k, ll, "#4a3a62" if cy < hz * 0.5 else "#6a4a6e")
            cv.hline(xx + 3, cy + k + 1, max(2, ll - 8), "#b06a80" if cy > hz * 0.35 else "#7a5078")
    out = cv.a.copy()
    out[..., 3] = 1
    return out
