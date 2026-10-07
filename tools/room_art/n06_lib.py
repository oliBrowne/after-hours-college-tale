"""Closed archive (N06) after the AI moved in: AUTOCOMPLETE's lair. Builds on lib_norlin.py and
lib_norlin2.py (oak, books, drawers, stone) and adds the machine that took the archive over, in the
boss sprite's own palette (slate rack steel, teal chat-window chrome, mint cursor glow, green/amber
LEDs, coloured patch cords).

Everything paints at 1:1 game pixels against a 52px character.
  palettes ...... RACK, BAY, TEAL, SCREEN, POPUP, GLOW*, GHOST*, LED, CORDS
  machine ....... fat_cable (outlined spline cables), patch_cord, rack_unit, server_rack (returns LED
                  points), cable_tray, monitor, chat_window (suggestion text), toggle_sign
                  (AUTOCOMPLETE ENABLED), screen_wall (the glowing wall of screens), opac_terminal
  floor ......... floor_cable (taped flat bundles), dock_pad (the boss's raised-floor spot), printout_slips
  props ......... catalog_rack (card catalog with a rack wedged in), stacks_rack (bookcase split by a
                  rack), mainframe (twin rack cabinets stuffed with books), terminal_table (the sorting
                  table turned prompt desk, with the ledger of reserved seats)
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, ground_shadow
from lib_norlin import book_row, book_stack, open_book, OAK, OAK_DARK, PAGE, GILT, BRASS, SPINES
from lib_norlin2 import drawer_grid, SASH

# --- palettes (taken from the AUTOCOMPLETE sprite) ------------------------------------------------
RACK = ["#12141e", "#22263a", "#363c52", "#4c546e", "#68728e", "#8e98b4"]     # rack steel, dark to lit
BAY = ["#07080e", "#0e1018", "#161a26", "#1e2232", "#2a2f42"]                 # inside the rack
TEAL = ["#0e3e46", "#1c7478", "#2ca09c", "#54cabc", "#96ecda"]                # window chrome
SCREEN = ["#080a16", "#0e1628", "#122438", "#183244", "#224656"]              # screen glass, dark to lit
POPUP = ["#3a345c", "#9696c4", "#ccceec", "#e6e8f8", "#fafaff"]  # suggestion chips
GLOW = "#6eecd0"            # cursor / accepted text mint
GLOW_HI = "#e2fff6"
GLOW_DK = "#2c8e8c"
GLOW_DIM = "#245662"
GHOST = "#46587c"           # ghost (suggested, not yet accepted) text
GHOST2 = "#6a7ea6"
USER = "#ece6d2"            # what the person typed
LED = {"g": "#60f480", "a": "#ffbe40", "r": "#ff5454", "b": "#6ab4ff", "w": "#e2fff6"}
LED_OFF = {"g": "#1e603a", "a": "#6a4a1a", "r": "#5a2228", "b": "#24426a", "w": "#3a5a5a"}
CORDS = ["#2c6ab4", "#c8962e", "#c8483c", "#d8d4c4", "#3a9a5a", "#2ca09c"]      # patch cords
CABLE = ["#16141e", "#24222e", "#34323e"]                                       # black power / trunk cable


def _rng(seed):
    return np.random.default_rng(seed)


# --- cables ------------------------------------------------------------------------------------
def _spline(pts, step=0.25):
    """Points along a Catmull-Rom spline through pts (ends repeated), roughly every `step` px."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = (np.array(P[j], float) for j in (i - 1, i, i + 1, i + 2))
        n = int(max(2, np.hypot(*(p2 - p1)) / step))
        for k in range(n):
            t = k / n
            t2, t3 = t * t, t * t * t
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append(q)
    out.append(np.array(P[-2], float))
    return out


def fat_cable(cv, pts, colour=CABLE[1], width=3, outline=True, lit=True):
    """A thick cable along a smooth path: ink outline, body, a 1px lit top edge, a darker underside."""
    path = _spline(pts)
    r = width / 2.0
    if outline:
        for q in path:
            x, y = int(round(q[0] - r - 1)), int(round(q[1] - r - 1))
            cv.rect(x, y, width + 2, width + 2, OUT)
    for q in path:
        x, y = int(round(q[0] - r)), int(round(q[1] - r))
        cv.rect(x, y, width, width, colour)
    if width >= 2:
        for q in path:
            x, y = int(round(q[0] - r)), int(round(q[1] - r))
            cv.rect(x, y + width - 1, width, 1, shade(colour, -0.3))
        if lit:
            for q in path:
                x, y = int(round(q[0] - r)), int(round(q[1] - r))
                cv.px(x + width // 2, y, shade(colour, 0.28))
    return path


def patch_cord(cv, a, b, sag, colour):
    """A thin patch cord hanging between two points: 1px body with a dark pixel under it."""
    (x0, y0), (x1, y1) = a, b
    n = int(max(abs(x1 - x0), abs(y1 - y0) + sag) * 2) + 2
    last = None
    for k in range(n + 1):
        t = k / n
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)
        p = (int(round(x)), int(round(y)))
        if p != last:
            cv.px(p[0], p[1] + 1, shade(colour, -0.45))
            cv.px(p[0], p[1], colour)
            last = p


def cable_ties(cv, path, every=14, colour="#d8d4c4"):
    """Little white cable ties along a fat cable path."""
    for i in range(every * 4, len(path) - 4, every * 4):
        q = path[i]
        cv.vline(int(round(q[0])), int(round(q[1])) - 2, 4, colour)


# --- rack hardware -------------------------------------------------------------------------------
def rack_unit(cv, x, y, w, h, kind, rng, leds):
    """One unit inside a rack, face-on, w x h at (x, y). Appends its LEDs (x, y, key) to `leds`.
    kinds: drives, vent, switch, screen, blank, books, drawer."""
    if kind == "books":
        cv.rect(x, y, w, h, BAY[1])
        book_row(cv, x + 1, y + h, w - 2, h - 1, seed=int(rng.integers(1 << 20)), lean=0.1, gaps=0.02, stacks=0.08)
        cv.hline(x, y + h - 1, w, RACK[3])
        return
    if kind == "drawer":
        # a card-catalogue drawer crammed into the rack, oak face, label and brass pull, cards up
        cv.rect(x, y, w, h, OAK[3]); cv.hline(x, y, w, OAK[5]); cv.hline(x, y + h - 1, w, OAK[1])
        cv.rect(x + w // 2 - 4, y + 2, 8, 3, BRASS[3]); cv.rect(x + w // 2 - 3, y + 3, 6, 1, PAGE[3])
        cv.hline(x + w // 2 - 2, y + h - 3, 4, BRASS[4])
        for cx in range(x + 2, x + w - 2, 2):
            cv.vline(cx, y - 2, 2, PAGE[3] if (cx // 2) % 2 else PAGE[2])
        return
    face = RACK[2] if kind != "blank" else RACK[1]
    cv.rect(x, y, w, h, face)
    cv.hline(x, y, w, shade(face, 0.18)); cv.hline(x, y + h - 1, w, RACK[0])
    # ears with screws
    cv.px(x + 1, y + h // 2, RACK[5]); cv.px(x + w - 2, y + h // 2, RACK[5])
    if kind == "drives":
        dx = x + 3
        while dx + 5 <= x + w - 3:
            cv.rect(dx, y + 1, 4, h - 2, RACK[1]); cv.hline(dx, y + 1, 4, RACK[3])
            cv.vline(dx + 3, y + 2, h - 4, RACK[0])
            key = "g" if rng.random() < 0.75 else ("a" if rng.random() < 0.7 else "b")
            cv.px(dx + 1, y + h - 2, LED_OFF[key])
            leds.append((dx + 1, y + h - 2, key))
            dx += 5
    elif kind == "vent":
        for vy in range(y + 2, y + h - 1, 2):
            cv.hline(x + 4, vy, w - 16, RACK[0])
        cv.rect(x + w - 10, y + 2, 6, min(3, h - 3), "#d8d4c4")                  # asset sticker
        cv.px(x + w - 6, y + h - 2, LED_OFF["g"]); leds.append((x + w - 6, y + h - 2, "g"))
    elif kind == "switch":
        ports = []
        px_ = x + 4
        while px_ + 3 <= x + w - 8:
            cv.rect(px_, y + 1, 2, 2, BAY[0]); cv.px(px_, y + 1, LED_OFF["a"] if rng.random() < 0.3 else LED_OFF["g"])
            ports.append(px_)
            if h >= 6:
                cv.rect(px_, y + 4, 2, 2, BAY[0])
            px_ += 3
        cv.px(x + w - 5, y + 2, LED_OFF["g"]); leds.append((x + w - 5, y + 2, "g"))
        for p in ports[::2]:
            leds.append((p, y + 1, "g" if rng.random() < 0.7 else "a"))
        # patch cords out of a few ports, hanging over the units below and off to the side
        for p in ports:
            if rng.random() < 0.55:
                col = CORDS[int(rng.integers(len(CORDS)))]
                side = x - 1 if p < x + w // 2 else x + w
                patch_cord(cv, (p + 1, y + 3), (side, y + h + int(rng.integers(2, 9))), int(rng.integers(3, 8)), col)
    elif kind == "screen":
        cv.rect(x + 3, y + 1, w - 14, h - 2, SCREEN[1])
        for k in range(x + 5, x + w - 14, 3):
            if rng.random() < 0.7:
                cv.hline(k, y + h // 2, 2, GLOW_DK)
        cv.px(x + 5, y + h // 2, GLOW)
        cv.px(x + w - 7, y + 2, LED_OFF["b"]); leds.append((x + w - 7, y + 2, "b"))
        cv.px(x + w - 5, y + 2, LED_OFF["g"]); leds.append((x + w - 5, y + 2, "g"))
    else:  # blank
        cv.px(x + 3, y + h // 2, RACK[3]); cv.px(x + w - 4, y + h // 2, RACK[3])


def server_rack(cv, x, top, w, base, seed=0, books=0.22, drawers=0.0, feet=True, cap=True, kinds=None):
    """A free-standing 19-inch rack, face-on: outlined steel frame, perforated posts, a stack of units
    of mixed heights (drive caddies, vents, switches with patch cords, little status screens, blank
    panels, bays stuffed with library books, now and then a card-catalogue drawer), a vented top cap
    and levelling feet. Returns the LED points [(x, y, key)] (dim in the painting; layers light them)."""
    rng = _rng(seed)
    leds = []
    plinth = 5 if feet else 2
    cv.rect(x - 1, top - 1, w + 2, base - top + 1, OUT)
    cv.rect(x, top, w, base - top, RACK[2])
    cv.vline(x, top, base - top, RACK[4]); cv.vline(x + w - 1, top, base - top, RACK[1])
    y = top + 1
    if cap:
        cv.rect(x + 1, top + 1, w - 2, 4, RACK[3]); cv.hline(x + 1, top + 1, w - 2, RACK[5])
        for vx in range(x + 4, x + w - 4, 3):
            cv.vline(vx, top + 2, 2, RACK[1])
        y = top + 6
    # posts
    inner0, inner1 = x + 3, x + w - 3
    cv.rect(x + 1, y, 2, base - plinth - y, RACK[3]); cv.rect(x + w - 3, y, 2, base - plinth - y, RACK[2])
    for py_ in range(y + 1, base - plinth, 3):
        cv.px(x + 1, py_, RACK[0]); cv.px(x + w - 2, py_, RACK[0])
    cv.rect(inner0, y, inner1 - inner0, base - plinth - y, BAY[1])
    # units
    choices = kinds or ["drives", "vent", "switch", "drives", "screen", "blank", "vent", "switch"]
    y += 1
    while y < base - plinth - 4:
        r = rng.random()
        if r < books:
            kind, h = "books", int(rng.integers(9, 14))
        elif r < books + drawers:
            kind, h = "drawer", 8
        else:
            kind = choices[int(rng.integers(len(choices)))]
            h = {"drives": 7, "vent": 5, "switch": 4, "screen": 6, "blank": 3}[kind]
            if kind == "drives" and rng.random() < 0.4:
                h = 10
            if kind == "switch" and rng.random() < 0.5:
                h = 7
        h = min(h, base - plinth - y - 1)
        if h < 3:
            break
        if (kind == "books" and h < 8) or (kind == "drawer" and h < 6):
            kind = "blank"
        if rng.random() < 0.08 and kind not in ("books", "drawer"):
            y += 2                                                   # an empty slot, dark
            continue
        rack_unit(cv, inner0, y, inner1 - inner0, h, kind, rng, leds)
        y += h + 1
    # plinth / feet
    cv.rect(x + 1, base - plinth, w - 2, plinth, RACK[1]); cv.hline(x + 1, base - plinth, w - 2, RACK[3])
    if feet:
        for fx in (x + 2, x + w - 6):
            cv.rect(fx, base - 2, 4, 2, RACK[0])
        for vx in range(x + 6, x + w - 6, 3):
            cv.vline(vx, base - plinth + 2, 1, RACK[0])
    return leds


def cable_tray(cv, x0, x1, y, hang_top=0, every=40):
    """A ladder cable tray hung under the ceiling on threaded rods, a loom of cables lying in it."""
    for hx in range(x0 + 6, x1 - 2, every):
        cv.vline(hx, hang_top, y - hang_top, IRON[3])
        cv.px(hx, hang_top, IRON[4])
    cv.rect(x0, y - 1, x1 - x0, 6, OUT)
    cv.rect(x0, y, x1 - x0, 4, CABLE[1])
    for k, col in enumerate((CABLE[2], "#2a3a5a", CABLE[0], "#3a2a3a")):
        cv.hline(x0, y + k, x1 - x0, col)
    cv.hline(x0, y + 3, x1 - x0, RACK[3])                          # the tray's lip
    for rx in range(x0 + 2, x1 - 1, 6):
        cv.vline(rx, y + 2, 2, RACK[4])


def monitor(cv, x, y, w, h, stand=None, bezel=RACK):
    """A flat screen in a dark bezel with a lit top edge and a power LED. stand: 'arm' (wall bracket
    above), 'foot' (desk foot below) or None. Returns the glass rect (x, y, w, h)."""
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, bezel[1]); cv.hline(x, y, w, bezel[3]); cv.hline(x, y + h - 1, w, bezel[0])
    gx, gy, gw, gh = x + 2, y + 2, w - 4, h - 5
    cv.rect(gx, gy, gw, gh, SCREEN[1])
    cv.hline(gx, gy, gw, SCREEN[3])
    cv.px(x + w - 3, y + h - 2, LED["g"])
    if stand == "foot":
        cv.rect(x + w // 2 - 2, y + h + 1, 4, 3, OUT); cv.rect(x + w // 2 - 1, y + h + 1, 2, 2, bezel[2])
        cv.rect(x + w // 2 - 6, y + h + 3, 12, 2, OUT); cv.hline(x + w // 2 - 5, y + h + 3, 10, bezel[3])
    elif stand == "arm":
        cv.rect(x + w // 2 - 1, y - 6, 3, 5, OUT); cv.vline(x + w // 2, y - 6, 5, bezel[3])
    return gx, gy, gw, gh


def chip(cv, x, y, label, fill=POPUP[2], ink="#2a2648"):
    """A suggestion chip: a lavender pill with dark text. Returns its width."""
    w = text_width(label) + 6
    cv.rect(x + 1, y - 1, w - 2, 11, OUT); cv.rect(x - 1 + 1, y, w, 9, OUT)
    cv.rect(x + 1, y, w - 2, 9, fill); cv.hline(x + 1, y, w - 2, POPUP[4]); cv.hline(x + 1, y + 8, w - 2, POPUP[1])
    text(cv, label, x + 3, y - 1, ink)
    return w


def chat_window(cv, x, y, w, h, title="SUGGESTED", seed=0):
    """The big chat window: teal title bar (traffic dots, title, close box), dark glass, a typed
    prompt, the accepted part of the completion in mint, the ghost of the rest, a row of suggestion
    chips and a hint line. Returns dict of points: cursor rect, typing slots for layers."""
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT)
    cv.rect(x - 1, y - 1, w + 2, h + 2, RACK[2]); cv.hline(x - 1, y - 1, w + 2, RACK[4])
    # title bar
    cv.rect(x, y, w, 11, TEAL[3]); cv.hline(x, y, w, TEAL[4]); cv.hline(x, y + 10, w, TEAL[1])
    for k, col in enumerate((TEAL[1], TEAL[1], TEAL[1])):
        cv.rect(x + 3 + k * 4, y + 4, 2, 2, col)
    text(cv, title, x + w // 2 - text_width(title) // 2, y + 1, TEAL[0])
    cv.rect(x + w - 9, y + 2, 7, 7, TEAL[1]); cv.line(x + w - 8, y + 3, x + w - 4, y + 7, TEAL[4]); cv.line(x + w - 4, y + 3, x + w - 8, y + 7, TEAL[4])
    # glass
    gx, gy, gw, gh = x, y + 11, w, h - 11
    cv.rect(gx, gy, gw, gh, SCREEN[1])
    cv.rect(gx, gy, gw, 2, SCREEN[3])
    for yy in range(gy + 3, gy + gh, 3):                       # faint scanlines
        cv.hline(gx, yy, gw, SCREEN[2])
    tx = gx + 5
    text(cv, "> I WANT TO", tx, gy + 2, USER)
    text(cv, "BECOME A", tx, gy + 13, GLOW)
    cur = (tx + text_width("BECOME A") + 1, gy + 14, 2, 9)
    cy = gy + 28
    cx = tx
    for lab in ("LAWYER", "CEO", "NURSE"):
        cx += chip(cv, cx, cy, lab) + 3
    text(cv, "TAB TO ACCEPT", tx, gy + 38, GHOST)
    # the message field along the bottom: placeholder text and a send arrow
    fy = gy + gh - 14
    cv.rect(gx + 3, fy, gw - 6, 12, SCREEN[3]); cv.rect(gx + 4, fy + 1, gw - 8, 10, SCREEN[0]); cv.hline(gx + 4, fy + 1, gw - 8, SCREEN[2])
    text(cv, "ASK ANYTHING", gx + 7, fy + 1, GHOST)
    ax = gx + gw - 14
    cv.rect(ax, fy + 2, 9, 8, TEAL[2]); cv.hline(ax, fy + 2, 9, TEAL[4])
    cv.hline(ax + 2, fy + 6, 5, TEAL[0])
    for (dx, dy) in ((4, -2), (5, -1), (5, 1), (4, 2)):
        cv.px(ax + dx, fy + 6 + dy, TEAL[0])
    cv.hline(gx, gy + gh - 1, gw, SCREEN[0])
    return {"cursor": cur, "glass": (gx, gy, gw, gh), "ghost": (tx + text_width("BECOME A ") + 3, gy + 13)}


def toggle_sign(cv, cx, y, label="AUTOCOMPLETE ENABLED", compact=False, halo=True):
    """A settings toggle blown up into a wall sign: dark glass panel in a teal frame, a lit pill
    switch at the left, the words in mint. Returns (x, y, w, h)."""
    pill = 12 if compact else 16
    w = text_width(label) + pill + (10 if compact else 14)
    h = 16
    x = cx - w // 2
    if halo:
        cv.rect(x - 2, y - 2, w + 4, h + 4, C(TEAL[2], 0.22))           # glow halo on the stone
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, TEAL[1]); cv.hline(x, y, w, TEAL[3]); cv.hline(x, y + h - 1, w, TEAL[0])
    cv.rect(x + 2, y + 2, w - 4, h - 4, SCREEN[0])
    # pill switch, on
    px_ = x + (3 if compact else 5)
    cv.rect(px_, y + 4, pill, 8, OUT); cv.rect(px_ + 1, y + 5, pill - 2, 6, GLOW_DK); cv.hline(px_ + 1, y + 5, pill - 2, GLOW)
    cv.rect(px_ + pill - 7, y + 4, 7, 8, OUT); cv.rect(px_ + pill - 6, y + 5, 5, 6, GLOW_HI)
    text(cv, label, px_ + pill + (3 if compact else 4), y + 3, GLOW)
    return x, y, w, h


def opac_terminal(cv, x, y, w=30, h=24):
    """The library's old amber catalogue terminal (OPAC), its screen overwritten by mint text."""
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, "#8a8270"); cv.hline(x, y, w, "#aaa28c"); cv.vline(x + w - 1, y, h, "#5e5848")
    sx, sy, sw, sh = x + 3, y + 3, w - 6, h - 9
    cv.rect(sx, sy, sw, sh, "#1a1208")
    cv.hline(sx + 2, sy + 2, 10, "#c8862e"); cv.hline(sx + 2, sy + 5, 6, "#c8862e")
    cv.hline(sx + 2, sy + 8, sw - 6, GLOW_DK); cv.px(sx + sw - 4, sy + 8, GLOW)
    cv.rect(x + 3, y + h - 5, w - 6, 3, "#6a6454")
    for k in range(x + 4, x + w - 4, 2):
        cv.px(k, y + h - 4, "#4a4638")
    return (sx + sw - 4, sy + 8)


def screen_wall(cv, cx, top, base, seed=0):
    """The glowing wall of screens that replaced the closed archive's grille: a strut frame bolted to
    the stone holds the big chat window in the middle and a column of monitors either side (chat
    bubbles, a progress bar, typing dots, ranked suggestions, the old amber catalogue terminal);
    a low bank of rack units runs along the floor beneath them, cords drooping between.
    Returns points for layers: {'cursor', 'dots', 'leds', 'glows', 'ghost'}."""
    rng = _rng(seed)
    out = {"leds": [], "glows": [], "dots": []}
    # strut frame
    fx0, fx1 = cx - 104, cx + 104
    for sy in (top + 4, base - 32):
        cv.rect(fx0, sy, fx1 - fx0, 4, OUT); cv.rect(fx0 + 1, sy + 1, fx1 - fx0 - 2, 2, RACK[3]); cv.hline(fx0 + 1, sy + 1, fx1 - fx0 - 2, RACK[5])
        for bx in range(fx0 + 4, fx1 - 2, 9):
            cv.px(bx, sy + 2, RACK[1])
    for sx in (fx0 + 2, cx - 72, cx + 69, fx1 - 6):
        cv.rect(sx, top + 4, 4, base - 32 - top, OUT); cv.rect(sx + 1, top + 4, 2, base - 32 - top, RACK[3])
        for by in range(top + 9, base - 32, 6):
            cv.px(sx + 1, by, RACK[1])
    # the big chat window
    ww, wh = 136, 74
    pts = chat_window(cv, cx - ww // 2, top + 10, ww, wh, seed=seed)
    out["cursor"] = pts["cursor"]
    out["ghost"] = pts["ghost"]
    # left column: chat bubbles
    lx = cx - 102
    g = monitor(cv, lx, top + 12, 30, 26)
    gx, gy, gw, gh = g
    cv.rect(gx + 2, gy + 2, 16, 6, POPUP[2]); cv.px(gx + 2, gy + 8, POPUP[2]); cv.hline(gx + 4, gy + 4, 11, POPUP[0])
    cv.rect(gx + gw - 18, gy + 11, 16, 6, TEAL[2]); cv.px(gx + gw - 3, gy + 17, TEAL[2]); cv.hline(gx + gw - 16, gy + 13, 9, TEAL[0])
    # below it the library's old amber catalogue terminal, its screen overwritten in mint
    out["glows"].append(opac_terminal(cv, lx, top + 44, 30, 24))
    # right column: typing dots bubble, then ranked suggestions
    rx = cx + 72
    g = monitor(cv, rx, top + 12, 30, 26)
    gx, gy, gw, gh = g
    cv.rect(gx + 3, gy + 5, 18, 9, POPUP[2]); cv.px(gx + 3, gy + 14, POPUP[2]); cv.px(gx + 4, gy + 15, POPUP[2])
    for k in range(3):
        cv.rect(gx + 6 + k * 5, gy + 9, 2, 2, POPUP[1])
        out["dots"].append((gx + 6 + k * 5, gy + 9))
    g = monitor(cv, rx, top + 44, 30, 24)
    gx, gy, gw, gh = g
    for k, (wd, col) in enumerate(((18, GLOW), (13, GHOST2), (16, GHOST2), (9, GHOST))):
        cv.px(gx + 2, gy + 2 + k * 4, col); cv.hline(gx + 4, gy + 2 + k * 4, wd, col)
    # bank of low rack units on the floor under the screens
    by0 = base - 24
    cv.rect(fx0 - 2, by0 - 1, fx1 - fx0 + 4, base - by0 + 1, OUT)
    x = fx0 - 1
    k = 0
    while x < fx1:
        uw = int(rng.integers(30, 44))
        uw = min(uw, fx1 + 1 - x)
        if uw < 12:
            break
        out["leds"] += server_rack(cv, x, by0, uw, base, seed=seed * 10 + k, books=0.3 if k % 2 else 0.12, feet=False, cap=False)
        x += uw + 1
        k += 1
    # cords drooping from the screens into the bank
    for (ax, ay, bx, sag, col) in ((cx - 87, top + 69, cx - 60, 14, CABLE[1]), (cx + 87, top + 69, cx + 58, 12, CABLE[1]),
                                    (cx - 30, top + 85, cx - 46, 10, CORDS[0]), (cx + 26, top + 85, cx + 44, 9, CORDS[1]),
                                    (cx + 4, top + 85, cx - 4, 8, CABLE[2])):
        patch_cord(cv, (ax, ay), (bx, by0 - 1), sag, col)
        patch_cord(cv, (ax + 1, ay), (bx + 1, by0 - 1), sag, shade(col, -0.1))
    return out


# --- floor ---------------------------------------------------------------------------------------
def floor_cable(cv, pts, colour=CABLE[1], width=3, tape="#3a3846", every=34):
    """A cable bundle lying flat on the floor, gaffer-taped down at intervals, a shadow under it."""
    path = _spline(pts)
    for q in path:
        cv.rect(int(round(q[0] - 1)), int(round(q[1] + 1)), width, 2, C("#0d0b16", 0.35))
    fat_cable(cv, pts, colour, width)
    for i in range(every * 4, len(path) - every * 2, every * 4):
        q = path[i]
        x, y = int(round(q[0])), int(round(q[1]))
        cv.rect(x - 2, y - 3, 5, 7, OUT); cv.rect(x - 1, y - 2, 3, 5, tape); cv.hline(x - 1, y - 2, 3, shade(tape, 0.25))
    return path


def dock_pad(cv, cx, cy, w=104, h=30):
    """The boss's spot: a patch of raised data-floor tiles (perforated steel) let into the flags,
    a teal glow strip round the edge, a cable grommet at the centre."""
    x0, y0 = cx - w // 2, cy - h // 2
    cv.rect(x0 - 3, y0 - 2, w + 6, h + 4, C(TEAL[2], 0.16))
    cv.rect(x0 - 1, y0 - 1, w + 2, h + 2, RACK[0])
    tw, th = (w + 2) // 3, (h + 1) // 2
    for ty in range(y0, y0 + h, th):
        for tx in range(x0, x0 + w, tw):
            ww, hh = min(tw, x0 + w - tx), min(th, y0 + h - ty)
            perf = ((tx - x0) // tw + (ty - y0) // th) % 2 == 0
            cv.rect(tx, ty, ww, hh, RACK[2] if perf else RACK[3])
            cv.hline(tx, ty, ww, RACK[4]); cv.vline(tx, ty, hh, RACK[3])
            cv.hline(tx, ty + hh - 1, ww, RACK[1]); cv.vline(tx + ww - 1, ty, hh, RACK[1])
            if perf:
                for py_ in range(ty + 3, ty + hh - 2, 2):
                    for px_ in range(tx + 3 + (py_ // 2) % 2, tx + ww - 2, 2):
                        cv.px(px_, py_, RACK[0])
    # teal glow strip round the patch
    cv.hline(x0 - 1, y0 - 2, w + 2, TEAL[3]); cv.hline(x0 - 1, y0 + h + 1, w + 2, TEAL[2])
    cv.vline(x0 - 2, y0 - 1, h + 2, TEAL[2]); cv.vline(x0 + w + 1, y0 - 1, h + 2, TEAL[2])
    for (ax, ay) in ((x0 - 2, y0 - 2), (x0 + w + 1, y0 - 2), (x0 - 2, y0 + h + 1), (x0 + w + 1, y0 + h + 1)):
        cv.px(ax, ay, TEAL[4])
    # grommet
    cv.rect(cx - 9, cy - 3, 18, 7, OUT); cv.rect(cx - 8, cy - 2, 16, 5, BAY[0]); cv.hline(cx - 8, cy + 2, 16, RACK[2])
    for k, col in enumerate((CORDS[0], CABLE[2], CORDS[1], CABLE[2], CORDS[4])):
        cv.vline(cx - 6 + k * 3, cy - 2, 3, col)
    return (x0, y0, w, h)


def printout_slips(cv, spots, seed=0):
    """Strips of printout spat from the machine: white paper, grey lines of text, a mint word."""
    rng = _rng(seed)
    for (x, y) in spots:
        w = int(rng.integers(8, 13)); h = int(rng.integers(4, 6))
        cv.hline(x + 1, y + h, w, C("#0d0b16", 0.35))
        cv.rect(x, y, w, h, "#e8e6dc"); cv.hline(x, y, w, "#fafaf4")
        for ly in range(y + 1, y + h - 1, 2):
            cv.hline(x + 1, ly, int(rng.integers(3, w - 2)), "#8a8a9a")
        if rng.random() < 0.5:
            cv.hline(x + w - 4, y + 1, 3, GLOW_DK)


# --- props ---------------------------------------------------------------------------------------
def _top_monitor(cv, x, base, w=34, h=24, seed=0):
    """A screen on a desk foot standing on top of a cabinet, a suggestion half-typed on it."""
    g = monitor(cv, x, base - h - 5, w, h, stand="foot")
    gx, gy, gw, gh = g
    cv.hline(gx + 2, gy + 3, gw - 10, USER); cv.hline(gx + 2, gy + 7, gw - 14, GLOW); cv.hline(gx + gw - 11, gy + 7, 7, GHOST2)
    cv.vline(gx + gw - 12, gy + 6, 3, GLOW_HI)
    cv.rect(gx + 2, gy + 11, 10, 4, POPUP[2]); cv.rect(gx + 14, gy + 11, 8, 4, POPUP[2])
    return g


def catalog_rack(width=145, height=118, seed=0):
    """A tall card-catalogue cabinet the machine has moved into: the middle bank of drawers torn out
    and a rack of servers wedged in their place, the drawers that are left gaping with cards, a fat
    cable loom snaking over the cornice and down the face, a monitor and book stacks on top.
    Prop, anchor bottom-centre."""
    rng = _rng(seed)
    cv = Canvas(width + 12, height + 10, seed=seed)
    ox, base = 6, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.48)
    top = base - height
    body_top = top + 26
    cv.rect(ox, body_top, width, height - 26, OUT)
    cv.rect(ox - 2, body_top - 5, width + 4, 6, OUT)
    cv.rect(ox - 1, body_top - 4, width + 2, 4, OAK[4]); cv.hline(ox - 1, body_top - 4, width + 2, OAK[5])
    cv.rect(ox - 2, body_top, width + 4, 6, OUT)
    cv.rect(ox - 1, body_top + 1, width + 2, 4, OAK[3]); cv.hline(ox - 1, body_top + 1, width + 2, OAK[5]); cv.hline(ox - 1, body_top + 4, width + 2, OAK[1])
    inner_top = body_top + 6
    feet = 8
    cv.rect(ox + 1, inner_top, width - 2, base - feet - inner_top, OAK[2])
    cv.vline(ox + 1, inner_top, base - feet - inner_top, OAK[4]); cv.vline(ox + width - 2, inner_top, base - feet - inner_top, OAK[1])
    dw, dh = 9, 7
    bank = 4 * (dw + 1) + 1
    span = 3 * bank + 6
    bx = ox + (width - span) // 2
    gh = base - feet - inner_top - 8
    drawer_grid(cv, bx, inner_top + 3, bank, gh, seed=seed * 7, dw=dw, dh=dh, open_rate=0.12)
    drawer_grid(cv, bx + 2 * (bank + 3), inner_top + 3, bank, gh, seed=seed * 7 + 2, dw=dw, dh=dh, open_rate=0.12)
    # the middle bank: a rack wedged in, its steel frame proud of the oak, a splintered edge
    mx = bx + bank + 3
    cv.rect(mx - 1, inner_top + 1, bank + 2, gh + 4, OAK_DARK[0])
    server_rack(cv, mx, inner_top + 2, bank, inner_top + gh + 4, seed=seed + 5, books=0.25, drawers=0.12, feet=False)
    for (sx, sy) in ((mx - 2, inner_top + 8), (mx + bank + 1, inner_top + 20), (mx - 2, inner_top + 50)):
        cv.px(sx, sy, OAK[5]); cv.px(sx, sy + 1, OAK[4])
    # base and feet
    cv.rect(ox - 1, base - feet - 4, width + 2, 4, OAK[3]); cv.hline(ox - 1, base - feet - 4, width + 2, OAK[5])
    for fx in (ox + 3, ox + width // 2 - 3, ox + width - 9):
        cv.rect(fx, base - feet, 6, feet, OUT); cv.rect(fx + 1, base - feet, 4, feet - 1, OAK[2]); cv.vline(fx + 1, base - feet, feet - 1, OAK[4])
    # on top: a monitor, a heap of books, an index-card tray
    bt = body_top - 3
    _top_monitor(cv, ox + width // 2 - 17, bt + 1, seed=seed)
    book_stack(cv, ox + 8, bt + 1, 22, n=4, seed=seed + 1)
    book_stack(cv, ox + width - 34, bt + 1, 18, n=3, seed=seed + 2)
    tx = ox + width - 14
    cv.rect(tx - 1, bt - 7, 12, 8, OUT); cv.rect(tx, bt - 6, 10, 6, OAK[3]); cv.hline(tx, bt - 6, 10, OAK[5])
    for k in range(tx + 1, tx + 9, 2):
        cv.vline(k, bt - 9, 4, PAGE[3] if (k // 2) % 2 else PAGE[2])
    # the cable loom: out of the rack top, over the cornice, down the right-hand drawers
    mid = mx + bank // 2
    p = fat_cable(cv, [(mid - 4, inner_top + 3), (mid - 2, body_top - 6), (mid + 22, body_top - 9), (mid + 40, body_top - 4),
                       (mid + 46, body_top + 12), (mid + 40, inner_top + 40), (mid + 52, base - feet - 10), (mid + 58, base - 1)],
                  CABLE[1], 3)
    cable_ties(cv, p, every=12)
    fat_cable(cv, [(mid + 6, inner_top + 3), (mid + 8, body_top - 4), (mid - 26, body_top - 8), (mid - 44, body_top - 2),
                   (mid - 50, inner_top + 24), (mid - 56, base - feet - 6), (mid - 58, base - 1)], CORDS[0], 2)
    return cv, ox + width // 2, base


def stacks_rack(width=145, height=118, seed=0):
    """A library bookcase split down the middle by a server rack forced in between its two halves;
    the books are squeezed to the outer bays, patch cords drape over the crown, and a small screen
    and a pile of books sit on top. Prop, anchor bottom-centre."""
    rng = _rng(seed)
    cv = Canvas(width + 12, height + 10, seed=seed)
    ox, base = 6, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.48)
    top = base - height
    case_top = top + 22
    rw = 34
    rx = ox + width // 2 - rw // 2
    plinth = 7
    for (x0, x1, s) in ((ox, rx - 1, 0), (rx + rw + 1, ox + width, 1)):
        w = x1 - x0
        cv.rect(x0, case_top, w, base - case_top, OUT)
        cv.rect(x0 + 1, case_top + 1, w - 2, 3, OAK[4]); cv.hline(x0 + 1, case_top + 1, w - 2, OAK[5])
        cv.rect(x0 - 1 if s == 0 else x0, case_top + 4, w + 1, 5, OUT)
        cv.rect(x0 if s == 0 else x0 + 1, case_top + 5, w - 1, 3, OAK[3]); cv.hline(x0 if s == 0 else x0 + 1, case_top + 5, w - 1, OAK[5])
        it = case_top + 10
        cv.rect(x0 + 1, it, 3, base - it - 1, OAK[3]); cv.vline(x0 + 1, it, base - it - 1, OAK[4])
        cv.rect(x1 - 4, it, 3, base - it - 1, OAK[2]); cv.vline(x1 - 2, it, base - it - 1, OAK[1])
        b0, b1 = x0 + 4, x1 - 4
        cv.rect(b0, it, b1 - b0, base - plinth - it, OAK_DARK[1])
        n = 4
        step = (base - plinth - it) / n
        for k in range(n):
            y0 = it + int(round(k * step)); y1 = it + int(round((k + 1) * step))
            cv.hline(b0, y0, b1 - b0, OAK_DARK[0])
            book_row(cv, b0 + 1, y1 - 2, b1 - b0 - 2, y1 - y0 - 5, seed=seed * 31 + k * 5 + s)
            # books shoved hard against the rack lean outward
            cv.rect(b0, y1 - 2, b1 - b0, 2, OAK[3]); cv.hline(b0, y1 - 2, b1 - b0, OAK[5])
        cv.rect(x0 + 1, base - plinth, w - 2, plinth - 1, OAK[2]); cv.hline(x0 + 1, base - plinth, w - 2, OAK[4])
        cv.hline(x0 + 1, base - 2, w - 2, OAK[1])
    # the rack, a touch taller than the cases
    leds = server_rack(cv, rx, case_top - 4, rw, base, seed=seed + 3, books=0.18, drawers=0.0)
    # on top of the cases: a screen on the left, books and a card tray on the right
    _top_monitor(cv, ox + 12, case_top + 1, w=30, h=20, seed=seed)
    book_stack(cv, ox + width - 40, case_top + 1, 20, n=4, seed=seed + 4)
    book_stack(cv, ox + width - 18, case_top + 1, 14, n=2, seed=seed + 6)
    # cords from the rack top, over both crowns
    for (pts, col, wd) in (([(rx + 8, case_top - 3), (rx + 2, case_top - 10), (rx - 14, case_top - 6), (rx - 22, case_top + 4), (rx - 20, case_top + 30), (rx - 28, case_top + 60), (rx - 31, base - 1)], CORDS[1], 2),
                           ([(rx + rw - 9, case_top - 3), (rx + rw - 2, case_top - 11), (rx + rw + 12, case_top - 2), (rx + rw + 6, case_top + 14), (rx + rw + 3, case_top + 50), (rx + rw + 5, base - 1)], CABLE[1], 3),
                           ([(rx + rw - 14, case_top - 3), (rx + rw + 4, case_top - 6), (rx + rw + 10, case_top + 2)], CORDS[0], 2)):
        fat_cable(cv, pts, col, wd)
    return cv, ox + width // 2, base


def mainframe(width=110, height=88, seed=0):
    """AUTOCOMPLETE's own cabinets behind its spot: two rack cabinets bolted together, the left with a
    perforated door glowing teal from inside, the right open on its units and its bays of books;
    reference books and a keyboard piled on top. Prop, anchor bottom-centre."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.5)
    top = base - height
    ct = top + 12
    half = width // 2
    # left cabinet: door
    x = ox
    cv.rect(x - 1, ct - 1, half + 1, base - ct + 1, OUT)
    cv.rect(x, ct, half - 1, base - ct, RACK[2]); cv.hline(x, ct, half - 1, RACK[4]); cv.vline(x, ct, base - ct, RACK[4])
    dx0, dy0, dx1, dy1 = x + 4, ct + 6, x + half - 6, base - 8
    cv.rect(dx0 - 1, dy0 - 1, dx1 - dx0 + 2, dy1 - dy0 + 2, RACK[0])
    cv.rect(dx0, dy0, dx1 - dx0, dy1 - dy0, BAY[1])
    for yy in range(dy0 + 1, dy1, 2):                       # LEDs and units seen through the mesh
        for xx in range(dx0 + 1 + (yy // 2) % 2, dx1, 2):
            cv.px(xx, yy, RACK[1])
    for k, yy in enumerate(range(dy0 + 4, dy1 - 3, 7)):
        cv.hline(dx0 + 2, yy, dx1 - dx0 - 4, C(TEAL[2], 0.45))
        cv.px(dx0 + 3 + (k * 5) % (dx1 - dx0 - 6), yy - 1, LED["g"]); cv.px(dx0 + 3 + (k * 11) % (dx1 - dx0 - 6), yy + 1, LED["a"] if k % 3 == 0 else LED["g"])
    cv.rect(x + half - 5, ct + (base - ct) // 2 - 6, 2, 12, RACK[5])            # handle
    cv.rect(x + 6, ct + 2, 18, 3, "#e8e6dc"); cv.hline(x + 7, ct + 3, 12, "#5a5a6a")  # label strip
    cv.rect(x + 1, base - 5, half - 3, 5, RACK[1]); cv.hline(x + 1, base - 5, half - 3, RACK[3])
    # right cabinet: open
    server_rack(cv, ox + half, ct, width - half, base, seed=seed + 9, books=0.32, drawers=0.0, cap=True)
    # top: books piled, a keyboard, a coil of patch cord
    book_stack(cv, ox + 4, ct, 26, n=4, seed=seed + 2)
    book_stack(cv, ox + 34, ct, 18, n=2, seed=seed + 3)
    kx = ox + 58
    cv.rect(kx - 1, ct - 5, 34, 5, OUT); cv.rect(kx, ct - 4, 32, 3, RACK[3]); cv.hline(kx, ct - 4, 32, RACK[5])
    for k in range(kx + 1, kx + 31, 2):
        cv.px(k, ct - 3, RACK[1])
    book_stack(cv, ox + width - 16, ct, 14, n=3, seed=seed + 4)
    patch_cord(cv, (ox + half - 6, ct - 1), (ox + half + 6, ct - 1), 3, CORDS[5])
    return cv, ox + width // 2, base


def terminal_table(width=140, height=40, seed=0):
    """The archive's sorting table turned prompt desk: an oak top with a keyboard and a screen
    asking for a name, the old ledger of reserved seats open beside it (its boxes now ticked in
    mint), a printer feeding a long tongue of fan-fold suggestions over the front edge, a mug and
    loose cards. Prop, anchor bottom-centre (same frame as the old sorting table)."""
    rng = _rng(seed)
    pad_top = 12
    cv = Canvas(width + 8, height + pad_top + 6, seed=seed)
    ox, base = 4, height + pad_top + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 1, 3, alpha=0.42)
    front = base - 20
    top_y = front - 16
    for lx in (ox + 5, ox + width - 10):
        cv.rect(lx, front + 3, 5, base - front - 3, OUT)
        cv.rect(lx + 1, front + 3, 3, base - front - 4, OAK[2]); cv.vline(lx + 1, front + 3, base - front - 4, OAK[3])
        cv.rect(lx, front + 9, 5, 2, OAK[4])
    cv.rect(ox + 9, base - 6, width - 18, 2, OAK[1])
    cv.rect(ox, top_y - 1, width, front - top_y + 6, OUT)
    cv.rect(ox + 1, top_y, width - 2, front - top_y, OAK[4])
    for gy in range(top_y + 2, front, 3):
        for _ in range(width // 16):
            gx = ox + 2 + int(rng.integers(0, width - 12))
            cv.hline(gx, gy, int(rng.integers(4, 10)), OAK[3])
    cv.hline(ox + 1, top_y, width - 2, OAK[5])
    cv.rect(ox + 1, front, width - 2, 4, OAK[3]); cv.hline(ox + 1, front, width - 2, OAK[5]); cv.hline(ox + 1, front + 3, width - 2, OAK[1])
    # the screen, on its foot, asking
    mx = ox + 44
    g = monitor(cv, mx, top_y - 13, 30, 17, stand="foot")
    gx, gy, gw, gh = g
    cv.hline(gx + 2, gy + 2, 12, USER); cv.vline(gx + 15, gy + 1, 3, GLOW_HI)
    cv.rect(gx + 2, gy + 6, 8, 3, POPUP[2]); cv.rect(gx + 12, gy + 6, 8, 3, POPUP[2])
    # keyboard
    kx, ky = ox + 40, front - 6
    cv.rect(kx - 1, ky - 1, 36, 6, OUT); cv.rect(kx, ky, 34, 4, RACK[3]); cv.hline(kx, ky, 34, RACK[5])
    for r in range(2):
        for k in range(kx + 1 + r, kx + 33, 2):
            cv.px(k, ky + 1 + r * 2, RACK[1])
    # the ledger of reserved seats
    lx, ly, lw, lh = ox + 84, top_y + 2, 36, 12
    cv.rect(lx - 2, ly - 1, lw + 4, lh + 2, OUT); cv.rect(lx - 1, ly, lw + 2, lh, "#5a2a26")
    cv.rect(lx, ly, lw, lh - 1, PAGE[3]); cv.vline(lx + lw // 2, ly, lh - 1, PAGE[0]); cv.vline(lx + lw // 2 - 1, ly, lh - 1, PAGE[2])
    for r in range(3):
        for c in range(4):
            for side in (0, 1):
                px_ = lx + 2 + side * (lw // 2 + 1) + c * 4
                py_ = ly + 2 + r * 3
                cv.rect(px_, py_, 3, 2, "#8a7e72")
                if rng.random() < 0.8:
                    cv.px(px_ + 1, py_, GLOW_DK)
    cv.vline(lx + lw // 2 + 6, ly + lh - 1, 6, SASH[1])
    # printer at the left feeding fan-fold paper over the front edge
    px0 = ox + 6
    cv.rect(px0 - 1, top_y - 5, 30, 14, OUT); cv.rect(px0, top_y - 4, 28, 12, "#c8c4b4"); cv.hline(px0, top_y - 4, 28, "#e8e4d8")
    cv.rect(px0 + 3, top_y - 2, 22, 2, "#4a4a56"); cv.px(px0 + 24, top_y + 4, LED["g"])
    paper = "#eceae0"
    cv.rect(px0 + 4, top_y - 9, 20, 7, OUT); cv.rect(px0 + 5, top_y - 8, 18, 6, paper)
    for ly_ in range(top_y - 7, top_y - 2, 2):
        cv.hline(px0 + 7, ly_, int(rng.integers(6, 14)), "#8a8a9a")
    # the tongue of printout over the edge and down to the floor
    tx = px0 + 6
    cv.rect(tx - 1, top_y + 8, 18, front - top_y - 7, OUT); cv.rect(tx, top_y + 8, 16, front - top_y - 8, paper)
    cv.rect(tx - 1, front, 18, 6, OUT); cv.rect(tx, front, 16, 5, paper)
    cv.rect(tx - 1, front + 5, 18, base - front - 6, OUT); cv.rect(tx, front + 5, 16, base - front - 7, "#d8d6cc")
    for yy in range(top_y + 10, base - 3, 3):
        cv.hline(tx + 2, yy, int(rng.integers(5, 12)), "#7a7a8a")
        if rng.random() < 0.35:
            cv.hline(tx + 11, yy, 3, GLOW_DK)
    for yy in range(front + 6, base - 2, 6):
        cv.hline(tx, yy, 16, "#b8b6ac")
    cv.rect(tx + 2, base - 4, 22, 4, OUT); cv.rect(tx + 3, base - 3, 20, 2, paper)       # fold lying on the floor
    # mug, loose cards
    cv.rect(ox + width - 18, top_y + 3, 7, 7, OUT); cv.rect(ox + width - 17, top_y + 4, 5, 5, TEAL[2]); cv.hline(ox + width - 17, top_y + 4, 5, "#2a1a14")
    cv.px(ox + width - 11, top_y + 6, OUT)
    for (cx, cy) in ((ox + 78, top_y + 8), (ox + 124, top_y + 3)):
        cv.rect(cx, cy, 7, 4, PAGE[3]); cv.hline(cx + 1, cy + 1, 5, "#8a7e72"); cv.px(cx + 5, cy + 2, SASH[2])
    return cv, ox + width // 2, base


# --- battle pieces -------------------------------------------------------------------------------
def stacks_texture(length, height, seed=0, layout=None):
    """A wall of library stacks with server racks forced in between, laid flat for the battle
    perspective: oak shelf bays of books and steel racks alternating along `length`, a plinth.
    layout: list of ('shelf'|'rack', width). Returns (Canvas, leds [(u, v, key)])."""
    rng = _rng(seed)
    cv = Canvas(length, height, seed=seed)
    cv.rect(0, 0, length, height, OAK[2])
    leds = []
    x = 0
    k = 0
    layout = layout or []
    while x < length:
        kind, w = layout[k % len(layout)] if layout else (("shelf", 90) if k % 2 == 0 else ("rack", 34))
        w = min(w, length - x)
        if kind == "shelf":
            if w > 12:
                wall_shelves_n(cv, x + 4, 6, w - 8, height - 14, seed=seed * 13 + k, shelf=22)
        else:
            cv.rect(x, 0, w, height, OAK_DARK[0])
            leds += server_rack(cv, x + 2, 4, w - 4, height - 1, seed=seed * 7 + k, books=0.22, drawers=0.06)
        x += w
        k += 1
    cv.rect(0, height - 8, length, 8, OAK[2]); cv.hline(0, height - 8, length, OAK[4]); cv.hline(0, height - 2, length, OAK[1])
    return cv, leds


def wall_shelves_n(cv, x, y, w, h, seed=0, shelf=22):
    """Oak shelf bay full of books (lib_norlin.wall_shelves without uprights bleeding into racks)."""
    cv.rect(x - 3, y - 4, w + 6, h + 4, OAK[1])
    cv.rect(x - 2, y - 3, w + 4, h + 3, OAK[3])
    cv.hline(x - 3, y - 4, w + 6, OAK[4]); cv.hline(x - 2, y - 3, w + 4, OAK[5])
    cv.rect(x, y, w, h, OAK_DARK[1])
    prev = y
    for k, sy in enumerate(range(y + shelf, y + h + 1, shelf)):
        cv.hline(x, prev, w, OAK_DARK[0])
        book_row(cv, x + 1, sy - 2, w - 2, shelf - 5, seed=seed * 31 + k)
        cv.rect(x, sy - 2, w, 2, OAK[3]); cv.hline(x, sy - 2, w, OAK[5])
        cv.hline(x, sy, w, C("#0d0b16", 0.5))
        prev = sy


def far_screens(w, h, seed=0):
    """The end wall of the battle aisle at its on-screen size: a strut frame over dark stone holding
    the big chat window (SUGGESTED; > I WANT TO / BECOME A, cursor, ghost DOCTOR; chips) with narrow monitors either side and rack units along the floor. Returns (Canvas, points)
    with 'cursor' and 'ghost' for the layers."""
    rng = _rng(seed)
    cv = Canvas(w, h, seed=seed)
    pts = {"leds": []}
    # frame
    for sy in (3, h - 18):
        cv.rect(0, sy, w, 3, OUT); cv.hline(1, sy + 1, w - 2, RACK[3])
    # rack units along the floor
    x = 1
    k = 0
    while x < w - 8:
        uw = min(int(rng.integers(20, 30)), w - 1 - x)
        pts["leds"] += server_rack(cv, x, h - 15, uw, h, seed=seed + k, books=0.3, feet=False, cap=False)
        x += uw + 1
        k += 1
    # the window
    ww, wh = 104, 49
    x0, y0 = (w - ww) // 2, 7
    cv.rect(x0 - 2, y0 - 2, ww + 4, wh + 4, OUT)
    cv.rect(x0 - 1, y0 - 1, ww + 2, wh + 2, RACK[2])
    cv.rect(x0, y0, ww, 11, TEAL[3]); cv.hline(x0, y0, ww, TEAL[4]); cv.hline(x0, y0 + 10, ww, TEAL[1])
    for j in range(3):
        cv.rect(x0 + 3 + j * 4, y0 + 4, 2, 2, TEAL[1])
    text(cv, "SUGGESTED", x0 + ww // 2 - text_width("SUGGESTED") // 2, y0 + 1, TEAL[0])
    cv.rect(x0 + ww - 9, y0 + 2, 7, 7, TEAL[1]); cv.line(x0 + ww - 8, y0 + 3, x0 + ww - 4, y0 + 7, TEAL[4]); cv.line(x0 + ww - 4, y0 + 3, x0 + ww - 8, y0 + 7, TEAL[4])
    gx, gy, gw, gh = x0, y0 + 11, ww, wh - 11
    cv.rect(gx, gy, gw, gh, SCREEN[1]); cv.rect(gx, gy, gw, 2, SCREEN[3])
    for yy in range(gy + 3, gy + gh, 3):
        cv.hline(gx, yy, gw, SCREEN[2])
    tx = gx + 3
    text(cv, "> I WANT TO", tx, gy + 1, USER)
    text(cv, "BECOME A", tx, gy + 12, GLOW)
    pts["cursor"] = (tx + text_width("BECOME A") + 1, gy + 13, 2, 9)
    pts["ghost"] = (tx + text_width("BECOME A ") + 2, gy + 12)
    cx = tx
    for lab in ("CEO", "NURSE", "LAWYER"):
        if cx + text_width(lab) + 6 > gx + gw - 2:
            break
        cx += chip(cv, cx, gy + 26, lab) + 3
    # narrow monitors either side
    for mx in (2, w - 12):
        g = monitor(cv, mx, 10, 10, 22)
        cv.hline(g[0] + 1, g[1] + 3, 4, GLOW_DK); cv.hline(g[0] + 1, g[1] + 7, 3, POPUP[2]); cv.hline(g[0] + 1, g[1] + 11, 5, GHOST2)
        g = monitor(cv, mx, 36, 10, 18)
        cv.rect(g[0] + 1, g[1] + 2, 4, 3, POPUP[2]); cv.hline(g[0] + 1, g[1] + 8, 5, GLOW_DK)
    for (ax_, bx_, col) in ((7, 20, CABLE[2]), (w - 7, w - 22, CORDS[1]), (x0 + 20, x0 + 12, CORDS[0])):
        patch_cord(cv, (ax_, 56 if ax_ < 20 or ax_ > w - 20 else y0 + wh + 1), (bx_, h - 16), 3, col)
    return cv, pts
