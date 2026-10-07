"""Norlin Library, the inner rooms (N04-N07) and their battle backdrops. Builds on lib_norlin.py
(palettes, books, lamps, walls) so all seven Norlin rooms read as one building.

Everything paints at 1:1 game pixels against a 52px character. Sections:
  moving stacks (N04) . STACK, CORK, RAIL, HAZARD, RED_PENCIL; call_card, handwheel, stack_shelf (prop on
                        rails), floor_rails, vault_lights, iron_column, gallery_deck, gallery_rail,
                        iron_stair, tile_floor, tread_plate, cage_lamp, passage_sign (OPEN / TURN CRANK),
                        pigeonholes, proof_sheet, correction_slip, archive_door, crank_pedestal (prop),
                        sentence_notice (prop)
  closed archive (N06)  BOXES, SLATE, SASH, VAULT; drawer_grid, index_wall (+ index_wall_slots, drawer_out
                        for the sliding-drawer blinks), index_cabinet (prop), archive_shelf (prop),
                        sorting_table (prop), reserved_chairs, chair_stack, two_line_plaque, index_rose,
                        floor_cards, archive_cage, card_chute, velvet_rope (exit barrier overlay),
                        chair_row_back (battle)
  playback room (N07) . ACOUSTIC, PHOSPHOR, AMBER_LIT, CASE, TAPE_BOXES; acoustic_wall, lit_sign,
                        waveform_screen + waveform_frame (scrolling envelope frames), vu_pair, loudspeaker,
                        woofer_push, reel_face, tape_machine, playback_console (prop), tape_shelf (prop),
                        listening_desk (prop)
  roof garden (N05) ... GRAVEL, SLEEPER, NIGHT_CLOUD, MOUNTAIN, LAVENDER; night_sky, moon, flatirons_night,
                        campus_roofs, auditorium, balustrade, stone_urn, festoon, tub_tree (prop), lavender,
                        raised_bed (prop), fountain_grass_small, feeder_bed (prop)
Painters that return sprites give (Canvas, anchor_x, anchor_y) like props.py.
"""
import numpy as np
from pixel import Canvas, C, mix, shade, text, text_width
from props import OUT, IRON, LEAF, MUM, AMBER, ground_shadow, shrub
from lib_norlin import (book_row, book_stack, open_book, banker_lamp, headphones, OAK, OAK_DARK, SPINES, PAGE, GILT, BRASS,
                        LAMP_GREEN, STONE_N, LIME, PLASTER_N, NIGHT_N, GRASS)

# --- palettes ---------------------------------------------------------------------------------
STACK = ["#121c18", "#1c2c26", "#27403a", "#335248", "#44685a", "#5e8470"]      # bottle-green enamelled steel
CORK = ["#2a1e1c", "#3e2c26", "#4a362c", "#543e32", "#5e4638", "#6a5040"]       # cork-tile stack floor
RAIL = ["#141220", "#2c2a38", "#4a4858", "#7a7890", "#a8a6bc"]                  # steel rails, dark to shine
HAZARD = ["#2a2018", "#c8962e", "#e8b84a"]
RED_PENCIL = ["#7a2420", "#b0382e", "#d8584a"]
INK_BLUE = "#2c3a6a"


def _rng(seed):
    return np.random.default_rng(seed)


# --- moving stacks ----------------------------------------------------------------------------
def call_card(cv, x, y, label, w=None):
    """A small brass range-finder frame with a cream card and a call number."""
    w = w or text_width(label) + 6
    cv.rect(x - 1, y - 1, w + 2, 12, OUT)
    cv.rect(x, y, w, 10, BRASS[2]); cv.hline(x, y, w, BRASS[4])
    cv.rect(x + 1, y + 1, w - 2, 8, PAGE[3])
    text(cv, label, x + 3, y, "#2a2030")
    return w


def handwheel(cv, cx, cy, r, spokes=3, rim=IRON, hub=BRASS, angle=0.0, knob=True):
    """A cast-iron hand crank wheel seen face-on: rim, spokes, brass hub, a turned knob on the rim."""
    cv.ellipse(cx - r - 1, cy - r - 1, 2 * r + 3, 2 * r + 3, OUT)
    cv.ellipse(cx - r, cy - r, 2 * r + 1, 2 * r + 1, rim[3])
    cv.ellipse(cx - r + 2, cy - r + 2, 2 * r - 3, 2 * r - 3, rim[1])
    cv.ellipse(cx - r + 3, cy - r + 3, 2 * r - 5, 2 * r - 5, C("#000000", 0.0))
    # inner hole (show what is behind as dark)
    inner = Canvas(cv.w, cv.h)
    for k in range(spokes):
        a = angle + k * 2 * np.pi / spokes
        x1, y1 = cx + np.cos(a) * (r - 1), cy + np.sin(a) * (r - 1)
        cv.line(cx, cy, int(round(x1)), int(round(y1)), rim[3])
        cv.line(cx + 1, cy, int(round(x1)) + 1, int(round(y1)), rim[2])
    # rim highlight (upper left)
    for a in np.linspace(np.pi * 1.05, np.pi * 1.6, 8):
        cv.px(int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r)), rim[4])
    cv.rect(cx - 2, cy - 2, 5, 5, OUT); cv.rect(cx - 1, cy - 1, 3, 3, hub[3]); cv.px(cx - 1, cy - 1, hub[4])
    if knob:
        a = angle + np.pi / spokes
        kx, ky = int(round(cx + np.cos(a) * r)), int(round(cy + np.sin(a) * r))
        cv.rect(kx - 2, ky - 2, 5, 5, OUT); cv.rect(kx - 1, ky - 1, 3, 3, OAK[4]); cv.px(kx - 1, ky - 1, OAK[5])


def stack_shelf(width=150, height=120, seed=0, call="PN 6", wheel=1, dim=0.0, label_pos=0.5):
    """A mobile stack range on rails, seen from the front: enamelled steel end frames with a
    brass-framed range card on the top cap, two bays of books on steel shelves, a riveted carriage
    on small wheels and a three-spoke crank wheel on one end (wheel = -1 left, 1 right, 0 none).
    Prop, anchor bottom-centre."""
    rng = _rng(seed)
    cv = Canvas(width + 12, height + 22, seed=seed)
    ox, base = 6, height + 18
    ground_shadow(cv, ox + width // 2, base, width // 2 + 3, 3, alpha=0.48)
    top = base - height
    carriage = 10
    # body outline, top cap seen from above
    cv.rect(ox, top, width, height - carriage + 1, OUT)
    cv.rect(ox + 1, top + 1, width - 2, 4, STACK[4]); cv.hline(ox + 1, top + 1, width - 2, STACK[5])
    cv.hline(ox + 1, top + 5, width - 2, STACK[1])
    cv.rect(ox - 1, top + 6, width + 2, 3, OUT); cv.rect(ox, top + 7, width, 1, STACK[3])
    inner_top = top + 9
    side = 7
    floor_y = base - carriage
    # end frames: a recessed panel, rivets, a lit left edge
    for (x0, lit) in ((ox + 1, True), (ox + width - 1 - side, False)):
        cv.rect(x0, inner_top, side, floor_y - inner_top, STACK[3] if lit else STACK[2])
        cv.vline(x0, inner_top, floor_y - inner_top, STACK[5] if lit else STACK[3])
        cv.rect(x0 + 2, inner_top + 4, side - 4, floor_y - inner_top - 8, STACK[2] if lit else STACK[1])
        for ry in range(inner_top + 2, floor_y - 1, 9):
            cv.px(x0 + side // 2, ry, STACK[5] if lit else STACK[4])
    bx0, bx1 = ox + 1 + side, ox + width - 1 - side
    cv.rect(bx0, inner_top, bx1 - bx0, floor_y - inner_top, OAK_DARK[1])
    mid = ox + width // 2
    cv.rect(mid - 1, inner_top, 3, floor_y - inner_top, STACK[3]); cv.vline(mid - 1, inner_top, floor_y - inner_top, STACK[4])
    bays = [(bx0, mid - 1), (mid + 2, bx1)]
    usable = floor_y - inner_top
    n = max(2, round(usable / 21))
    step = usable / n
    for k in range(n):
        y0 = inner_top + int(round(k * step))
        y1 = inner_top + int(round((k + 1) * step))
        for b, (a0, a1) in enumerate(bays):
            cv.hline(a0, y0, a1 - a0, OAK_DARK[0])
            book_row(cv, a0 + 1, y1 - 2, a1 - a0 - 2, y1 - y0 - 5, seed=seed * 97 + k * 7 + b, dim=dim,
                     gaps=0.06, stacks=0.06)
            # a red-flagged correction slip poking out of a book here and there
            if rng.random() < 0.5:
                sx = a0 + 4 + int(rng.integers(0, max(1, a1 - a0 - 10)))
                cv.rect(sx, y0 + 3, 2, 4, PAGE[3]); cv.px(sx, y0 + 3, RED_PENCIL[2])
        # steel shelf edge with a lit lip
        cv.rect(bx0, y1 - 2, bx1 - bx0, 2, STACK[3]); cv.hline(bx0, y1 - 2, bx1 - bx0, STACK[5])
    # carriage with rivets and wheels sitting on the rail
    cv.rect(ox - 1, floor_y, width + 2, carriage - 2, OUT)
    cv.rect(ox, floor_y + 1, width, carriage - 4, IRON[2]); cv.hline(ox, floor_y + 1, width, IRON[4])
    cv.hline(ox, floor_y + carriage - 4, width, IRON[1])
    for rx in range(ox + 4, ox + width - 2, 8):
        cv.px(rx, floor_y + 3, IRON[4])
    for wx in (ox + 10, ox + width // 2 - 12, ox + width // 2 + 12, ox + width - 11):
        cv.ellipse(wx - 3, base - 6, 7, 6, OUT); cv.ellipse(wx - 2, base - 5, 5, 4, IRON[1]); cv.px(wx, base - 4, IRON[4])
    # range card on the top cap
    if call:
        cw = text_width(call) + 6
        cx = ox + int(width * label_pos) - cw // 2
        cv.rect(cx + 3, top - 2, 2, 3, IRON[2]); cv.rect(cx + cw - 5, top - 2, 2, 3, IRON[2])
        call_card(cv, cx, top - 11, call, cw)
    # crank wheel on one end
    if wheel:
        wx = ox + (width - 4 if wheel > 0 else 3)
        wy = top + height // 2 - 4
        cv.rect(wx - 4 if wheel > 0 else wx - 1, wy - 1, 6, 3, IRON[1])
        handwheel(cv, wx + (3 if wheel > 0 else -3), wy, 8, spokes=3, angle=float(rng.uniform(0, 2)))
    return cv, ox + width // 2, base


def floor_rails(cv, x0, x1, y_back, y_front, stops=True):
    """Two steel rails let into the floor in a dark channel, for the moving stacks to run on."""
    for y in (y_back, y_front):
        cv.rect(x0, y - 1, x1 - x0, 4, C(RAIL[0], 0.85))
        cv.hline(x0, y, x1 - x0, RAIL[3]); cv.hline(x0, y + 1, x1 - x0, RAIL[2])
        cv.hline(x0, y + 2, x1 - x0, RAIL[1])
        for bx in range(x0 + 6, x1 - 2, 24):
            cv.px(bx, y + 1, RAIL[4])
    # sleepers between the rails, every so often
    for sx in range(x0 + 10, x1 - 6, 36):
        cv.rect(sx, y_back + 3, 3, y_front - y_back - 4, C(RAIL[1], 0.7))
    if stops:
        for x in (x0, x1 - 6):
            cv.rect(x - 1, y_back - 3, 8, y_front - y_back + 7, OUT)
            for k, yy in enumerate(range(y_back - 2, y_front + 4, 2)):
                cv.rect(x, yy, 6, 2, HAZARD[2] if k % 2 == 0 else HAZARD[0])


def vault_lights(cv, x, y, cols, rows, pitch=(7, 5)):
    """A cast-iron pavement light let into the floor: a frame holding rows of small round glass
    prisms that glow faintly with the lamps on the level below. (x, y) top-left."""
    pw, ph = pitch
    w, h = cols * pw + 3, rows * ph + 3
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, IRON[2]); cv.hline(x, y, w, IRON[4]); cv.vline(x, y, h, IRON[3])
    for r in range(rows):
        for c in range(cols):
            lx, ly = x + 2 + c * pw, y + 2 + r * ph
            cv.rect(lx, ly, pw - 2, ph - 2, "#1e2a2c")
            cv.rect(lx + 1, ly, pw - 4, ph - 2, "#7aa8a0")
            cv.px(lx + 1, ly, "#c8ece0")
            cv.hline(lx + 1, ly + ph - 3, pw - 4, "#4e7a74")


def iron_column(cv, cx, top, base, w=6):
    """A slim cast-iron stack column: a flared capital under the deck, a round shaft, a base."""
    cv.rect(cx - w // 2, top, w, base - top, IRON[2])
    cv.vline(cx - w // 2, top, base - top, IRON[4]); cv.vline(cx - w // 2 + 1, top, base - top, IRON[3])
    cv.vline(cx + w // 2 - 1, top, base - top, IRON[1])
    cv.rect(cx - w // 2 - 3, top, w + 6, 3, IRON[3]); cv.hline(cx - w // 2 - 3, top, w + 6, IRON[4])
    cv.rect(cx - w // 2 - 2, top + 3, w + 4, 2, IRON[2])
    cv.rect(cx - w // 2 - 2, base - 5, w + 4, 5, IRON[2]); cv.hline(cx - w // 2 - 2, base - 5, w + 4, IRON[4])
    cv.hline(cx - w // 2 - 2, base - 1, w + 4, IRON[0])


def gallery_deck(cv, x0, x1, y, h=10):
    """The edge of the upper stack tier's floor: a riveted iron beam carrying a strip of glass
    deck tiles that glow faintly with the lamps above."""
    cv.rect(x0, y, x1 - x0, h, IRON[1])
    cv.rect(x0, y, x1 - x0, 3, "#9ab8a8"); cv.hline(x0, y, x1 - x0, "#c8e0cc")
    for gx in range(x0, x1, 7):
        cv.vline(gx, y, 3, IRON[2])
    cv.hline(x0, y + 3, x1 - x0, IRON[3])
    cv.rect(x0, y + 4, x1 - x0, h - 5, IRON[2])
    for rx in range(x0 + 3, x1 - 1, 6):
        cv.px(rx, y + 6, IRON[4])
    cv.hline(x0, y + h - 1, x1 - x0, OUT)
    cv.rect(x0, y + h, x1 - x0, 3, C("#0d0b16", 0.45))


def gallery_rail(cv, x0, x1, top, bottom, every=6):
    """An iron gallery railing in front of the upper stacks: brass-capped handrail, balusters,
    a mid rail, posts with ball finials at intervals."""
    cv.rect(x0, top, x1 - x0, 3, OUT); cv.hline(x0, top, x1 - x0, BRASS[3]); cv.hline(x0, top + 1, x1 - x0, BRASS[1])
    for bx in range(x0 + 2, x1, every):
        cv.vline(bx, top + 3, bottom - top - 3, IRON[1])
    mid = (top + bottom) // 2 + 2
    cv.hline(x0, mid, x1 - x0, IRON[2])
    cv.hline(x0, bottom - 2, x1 - x0, IRON[2])
    for px_ in range(x0, x1 + 1, every * 8):
        cv.rect(px_ - 1, top - 2, 3, bottom - top + 2, IRON[2]); cv.vline(px_ - 1, top - 2, bottom - top + 2, IRON[4])
        cv.rect(px_ - 1, top - 4, 3, 2, BRASS[3])


def iron_stair(cv, x0, base, x1, top, w=0, seed=0):
    """A steep iron stair up to the gallery, painted against the back wall: two riveted stringers
    climbing from (x0, base) to (x1, top), open treads with lit nosings, posts and a brass handrail."""
    n = max(4, (base - top) // 7)
    pts = [(x0 + (x1 - x0) * i / n, base - (base - top) * i / n) for i in range(n + 1)]
    # back stringer (in shadow) then treads, then the front stringer
    cv.line(x0 + 10, base - 1, x1 + 10, top + 4, IRON[1])
    for i in range(1, n + 1):
        tx, ty = pts[i]
        tx, ty = int(round(tx)), int(round(ty))
        cv.rect(tx - 2, ty, 16, 3, OUT)
        cv.hline(tx - 1, ty, 14, IRON[4]); cv.hline(tx - 1, ty + 1, 14, IRON[2])
    for k in (0, 1):
        cv.line(x0 + k, base - 1, x1 + k, top + 3, IRON[3] if k == 0 else IRON[1])
    cv.line(x0 - 1, base - 1, x1 - 1, top + 3, OUT)
    for i in range(0, n + 1, 3):
        tx, ty = pts[i]
        cv.vline(int(round(tx)) + 1, int(round(ty)) - 18, 18, IRON[2])
    cv.line(int(pts[0][0]) + 1, int(pts[0][1]) - 19, int(pts[-1][0]) + 1, int(pts[-1][1]) - 19, BRASS[3])
    cv.line(int(pts[0][0]) + 1, int(pts[0][1]) - 18, int(pts[-1][0]) + 1, int(pts[-1][1]) - 18, BRASS[1])
    cv.rect(x0 - 3, base - 3, 8, 3, IRON[1]); cv.hline(x0 - 3, base - 3, 8, IRON[3])


def tile_floor(cv, x, y, w, h, seed=0, pal=CORK, tw=20, th=14):
    """Square cork tiles laid in a grid, checkered in two close tones, each with a granular
    texture, a lit top edge and a dark joint; a few scuffed paler tiles."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, pal[1])
    for row, ty in enumerate(range(y, y + h, th)):
        for col, tx in enumerate(range(x, x + w, tw)):
            x0, x1 = tx + 1, min(x + w, tx + tw)
            y1 = min(y + h, ty + th)
            tone = pal[3] if (row + col) % 2 == 0 else pal[4]
            if rng.random() < 0.08:
                tone = pal[5] if (row + col) % 2 else pal[2]
            cv.rect(x0, ty + 1, x1 - x0, y1 - ty - 1, tone)
            cv.hline(x0, ty + 1, x1 - x0, shade(tone, 0.07))
            for _ in range((x1 - x0) * (y1 - ty) // 10):
                cv.px(x0 + int(rng.integers(0, max(1, x1 - x0))), ty + 2 + int(rng.integers(0, max(1, y1 - ty - 2))),
                      shade(tone, float(rng.choice([-0.06, -0.03, 0.04]))))


def tread_plate(cv, x, y, w, h, base="#3c3844"):
    """A steel track bed of diamond tread plate let into the floor (lit top lip, dark lower lip)."""
    cv.rect(x, y, w, h, base)
    for yy in range(y + 2, y + h - 1, 4):
        for xx in range(x + ((yy - y) // 4 % 2) * 4 + 1, x + w - 2, 8):
            cv.hline(xx, yy, 2, shade(base, 0.22)); cv.px(xx + 1, yy + 1, shade(base, -0.25))
    cv.hline(x, y, w, shade(base, 0.3)); cv.hline(x, y + 1, w, shade(base, 0.12))
    cv.hline(x, y + h - 1, w, OUT)
    cv.vline(x, y, h, shade(base, 0.2)); cv.vline(x + w - 1, y, h, OUT)


def cage_lamp(cv, x, y, chain_top, lit=True):
    """A caged work lamp hanging on a short chain: brass cap, wire cage over a warm bulb.
    (x, y) is the bottom of the cage."""
    cv.vline(x, chain_top, y - 9 - chain_top, IRON[2])
    for cy in range(chain_top + 1, y - 9, 2):
        cv.px(x, cy, IRON[3])
    if lit:
        for r, a in [(14, 0.05), (9, 0.08)]:
            cv.ellipse(x - r, y - 4 - r, 2 * r + 1, 2 * r + 1, C("#f6cf7a", a))
    cv.rect(x - 3, y - 10, 7, 3, BRASS[2]); cv.hline(x - 3, y - 10, 7, BRASS[4])
    cv.rect(x - 3, y - 7, 7, 7, OUT)
    cv.rect(x - 2, y - 7, 5, 6, "#f6cd78" if lit else "#4e4860"); cv.rect(x - 1, y - 6, 3, 3, "#fff0c4" if lit else "#6a6480")
    cv.vline(x, y - 7, 7, IRON[2]); cv.hline(x - 2, y - 4, 5, IRON[2])
    cv.px(x, y, IRON[2])


def passage_sign(open_):
    """The stacks' MARKED PASSAGE board, hung on two chains: gilt letters on dark oak, the state
    in green (OPEN) or amber (TURN CRANK) with a matching signal lamp. Returns the Canvas."""
    top_line = "MARKED PASSAGE"
    state = "OPEN" if open_ else "TURN CRANK"
    w = text_width(top_line) + 20
    h = 28
    cv = Canvas(w + 2, h + 12)
    # chains from the deck
    for hx in (8, w - 7):
        for cy in range(0, 10, 2):
            cv.px(hx, cy, IRON[3]); cv.px(hx, cy + 1, IRON[1])
    y0 = 10
    cv.rect(0, y0, w + 2, h + 2, OUT)
    cv.rect(1, y0 + 1, w, h, OAK[2]); cv.hline(1, y0 + 1, w, OAK[4]); cv.hline(1, y0 + h, w, OAK[1])
    cv.rect(3, y0 + 3, w - 4, h - 4, "#1c1418")
    text(cv, top_line, 11, y0 + 3, GILT)
    cv.hline(6, y0 + 13, w - 10, BRASS[1])
    colour = "#7ad08a" if open_ else "#f0a848"
    sw = text_width(state)
    sx = (w + 2) // 2 - sw // 2 + 4
    text(cv, state, sx, y0 + 15, colour)
    # signal lamp left of the state word
    lx = sx - 8
    cv.rect(lx - 3, y0 + 17, 6, 6, OUT)
    cv.rect(lx - 2, y0 + 18, 4, 4, "#3cba6a" if open_ else "#c8582e")
    cv.px(lx - 1, y0 + 18, "#c8f0c8" if open_ else "#ffd0a0")
    if not open_:
        # a little crank glyph after the words
        gx = sx + sw + 4
        cv.ellipse(gx, y0 + 16, 7, 7, IRON[3]); cv.px(gx + 3, y0 + 19, BRASS[3]); cv.line(gx + 3, y0 + 19, gx + 6, y0 + 16, IRON[4])
    return cv


def pigeonholes(cv, x, y, w, h, seed=0, cell=(10, 8)):
    """An oak pigeonhole rack on the wall: little cells with folded slips and red-marked proofs."""
    rng = _rng(seed)
    cv.rect(x - 2, y - 2, w + 4, h + 4, OUT)
    cv.rect(x - 1, y - 1, w + 2, h + 2, OAK[3]); cv.hline(x - 1, y - 1, w + 2, OAK[5])
    cw, ch = cell
    for yy in range(y, y + h - ch + 1, ch + 1):
        for xx in range(x, x + w - cw + 1, cw + 1):
            cv.rect(xx, yy, cw, ch, OAK_DARK[1]); cv.hline(xx, yy + ch - 1, cw, OAK[2])
            k = rng.random()
            if k < 0.55:
                pw = int(rng.integers(4, cw - 1))
                ph = int(rng.integers(3, ch - 1))
                px_ = xx + int(rng.integers(1, cw - pw + 1))
                cv.rect(px_, yy + ch - 1 - ph, pw, ph, PAGE[2] if rng.random() < 0.7 else PAGE[3])
                cv.hline(px_, yy + ch - 1 - ph, pw, PAGE[3])
                if rng.random() < 0.4:
                    cv.px(px_ + 1, yy + ch - ph, RED_PENCIL[1])
            elif k < 0.7:
                cv.rect(xx + 1, yy + ch - 3, cw - 2, 2, SPINES[int(rng.integers(len(SPINES)))])


def proof_sheet(cv, x, y, w=14, h=18, seed=0, pin="#c84a3c"):
    """A typeset proof pinned to the wall: grey text lines, red pencil strikes and carets."""
    rng = _rng(seed)
    cv.rect(x + 1, y + 1, w, h, C("#0d0b16", 0.35))
    cv.rect(x, y, w, h, PAGE[3]); cv.hline(x, y, w, "#fff8e6")
    for ly in range(y + 3, y + h - 2, 2):
        n = int(rng.integers(w // 2, w - 3))
        cv.hline(x + 2, ly, n, "#8a7e72")
        if rng.random() < 0.35:
            sx = x + 2 + int(rng.integers(0, max(1, n - 3)))
            cv.hline(sx, ly, int(rng.integers(2, 5)), RED_PENCIL[1])
            cv.px(x + w - 2, ly - 1, RED_PENCIL[2])
    cv.px(x + w // 2, y + 1, pin)


def correction_slip(cv, x, y, seed=0):
    """An errata slip dropped on the floor: a small cream strip with a red pencil mark."""
    rng = _rng(seed)
    w, h = int(rng.integers(6, 9)), int(rng.integers(3, 5))
    cv.rect(x + 1, y + 1, w, h, C("#0d0b16", 0.35))
    cv.rect(x, y, w, h, PAGE[3]); cv.hline(x, y, w, "#fff8e6")
    cv.hline(x + 1, y + h // 2, w - 3, "#8a7e72")
    cv.line(x + 1, y + h - 1, x + w - 2, y + 1, RED_PENCIL[1])


def archive_door(cv, cx, bottom, w=44, h=72, label="ARCHIVE", pal=STONE_N):
    """The closed archive's door: a deep sandstone surround with a carved lintel and label,
    a heavy oak door banded with iron, a small grilled window, and a brass plate with a
    bookmark-shaped key slot. (cx, bottom) is the threshold."""
    x, top = cx - w // 2, bottom - h
    # surround and reveal
    cv.rect(x - 8, top - 4, w + 16, h + 4, pal[2])
    cv.vline(x - 8, top - 4, h + 4, pal[4]); cv.vline(x + w + 7, top - 4, h + 4, pal[1])
    for k, qy in enumerate(range(top + 2, bottom - 2, 8)):
        qw = 6 if k % 2 == 0 else 4
        cv.rect(x - 8, qy, qw, 7, pal[3]); cv.hline(x - 8, qy, qw, pal[5])
        cv.rect(x + w + 8 - qw, qy, qw, 7, pal[2]); cv.hline(x + w + 8 - qw, qy, qw, pal[4])
    cv.rect(x - 3, top - 1, w + 6, h + 1, pal[1]); cv.rect(x - 3, top - 1, 3, h + 1, pal[3])
    # lintel with the carved word
    lw = max(w + 20, text_width(label) + 12)
    ly = top - 16
    cv.rect(cx - lw // 2, ly, lw, 12, pal[3]); cv.hline(cx - lw // 2, ly, lw, pal[5]); cv.hline(cx - lw // 2, ly + 11, lw, pal[1])
    tw = text_width(label)
    text(cv, label, cx - tw // 2, ly + 2, pal[4])
    text(cv, label, cx - tw // 2, ly + 1, pal[0])
    cv.rect(cx - lw // 2 - 3, ly - 3, lw + 6, 3, LIME[3]); cv.hline(cx - lw // 2 - 3, ly - 3, lw + 6, LIME[5])
    # the door: vertical oak boards, iron straps with rivets
    cv.rect(x, top, w, h, OUT)
    for bx in range(x + 1, x + w - 1, 6):
        tone = OAK[2] if (bx // 6) % 2 else OAK[3]
        cv.rect(bx, top + 1, min(6, x + w - 1 - bx), h - 1, tone)
        cv.vline(bx, top + 1, h - 1, OAK[1])
    for sy in (top + 12, top + h // 2 + 4, bottom - 12):
        cv.rect(x + 1, sy, w - 2, 3, IRON[2]); cv.hline(x + 1, sy, w - 2, IRON[3])
        for rx in range(x + 4, x + w - 2, 7):
            cv.px(rx, sy + 1, IRON[4])
    # grilled window
    gx, gy = cx - 7, top + 20
    cv.rect(gx - 1, gy - 1, 16, 12, OUT); cv.rect(gx, gy, 14, 10, "#120e16")
    cv.rect(gx + 2, gy + 6, 10, 3, C("#e9a84a", 0.35))
    for k in range(gx + 2, gx + 14, 3):
        cv.vline(k, gy, 10, IRON[3])
    cv.hline(gx, gy + 4, 14, IRON[3])
    # brass plate with a bookmark-shaped slot, and a ring pull
    px_, py_ = cx + 8, top + h // 2 + 12
    cv.rect(px_ - 1, py_ - 1, 9, 15, OUT); cv.rect(px_, py_, 7, 13, BRASS[2]); cv.hline(px_, py_, 7, BRASS[4])
    cv.rect(px_ + 2, py_ + 2, 3, 7, "#120c10"); cv.px(px_ + 2, py_ + 9, "#120c10"); cv.px(px_ + 4, py_ + 9, "#120c10")
    cv.ellipse(cx - 12, top + h // 2 + 12, 7, 7, OUT); cv.ellipse(cx - 11, top + h // 2 + 13, 5, 5, BRASS[2]); cv.px(cx - 9, top + h // 2 + 15, OUT)
    # worn stone sill
    cv.rect(x - 9, bottom - 2, w + 18, 2, pal[5]); cv.hline(x - 9, bottom - 2, w + 18, pal[6])


def crank_pedestal(width=70, height=60, open_=False, label="SHIFT AISLE"):
    """The stacks' shifting crank on a cast-iron pedestal: a gilt header plate with the label,
    a geared housing in the stacks' green enamel, a big crank wheel with a wooden handle, and a
    position dial (needle on TURN or OPEN, lamp amber or green). Prop, anchor bottom-centre."""
    cv = Canvas(width + 8, height + 6)
    ox, base = 4, height + 2
    cx = ox + width // 2
    ground_shadow(cv, cx, base, width // 2 - 4, 3, alpha=0.45)
    top = base - height
    # header plate
    tw = text_width(label)
    pw = tw + 8
    cv.rect(cx - pw // 2 - 1, top, pw + 2, 13, OUT)
    cv.rect(cx - pw // 2, top + 1, pw, 11, BRASS[2]); cv.hline(cx - pw // 2, top + 1, pw, BRASS[4])
    cv.rect(cx - pw // 2 + 1, top + 2, pw - 2, 9, "#1c1418")
    text(cv, label, cx - tw // 2, top + 2, GILT)
    for hx in (cx - 14, cx + 13):
        cv.rect(hx, top + 13, 2, 4, IRON[2])
    # housing
    hx0, hx1 = cx - 22, cx + 22
    hy0 = top + 17
    cv.rect(hx0 - 1, hy0 - 1, hx1 - hx0 + 2, base - 7 - hy0 + 2, OUT)
    cv.rect(hx0, hy0, hx1 - hx0, base - 7 - hy0, STACK[3]); cv.hline(hx0, hy0, hx1 - hx0, STACK[5])
    cv.vline(hx0, hy0, base - 7 - hy0, STACK[4]); cv.vline(hx1 - 1, hy0, base - 7 - hy0, STACK[1])
    cv.rect(hx0 + 3, hy0 + 3, hx1 - hx0 - 6, base - 13 - hy0, STACK[2])
    for rx in (hx0 + 2, hx1 - 3):
        for ry in (hy0 + 2, base - 10):
            cv.px(rx, ry, BRASS[3])
    # position dial with the needle and lamp
    dx, dy = cx + 11, hy0 + 10
    cv.ellipse(dx - 6, dy - 6, 13, 13, OUT); cv.ellipse(dx - 5, dy - 5, 11, 11, PAGE[3])
    cv.px(dx - 4, dy, RED_PENCIL[1]); cv.px(dx + 4, dy, "#3cba6a")
    end = (dx + 4, dy - 2) if open_ else (dx - 4, dy - 2)
    cv.line(dx, dy + 1, end[0], end[1], "#1a1424")
    cv.rect(dx - 2, dy + 7, 5, 4, OUT); cv.rect(dx - 1, dy + 8, 3, 2, "#3cba6a" if open_ else "#e08a3a")
    # crank wheel on the left of the housing
    handwheel(cv, cx - 9, hy0 + 15, 11, spokes=4, angle=0.35 if open_ else 0.0)
    # plinth
    cv.rect(cx - 26, base - 7, 52, 7, OUT)
    cv.rect(cx - 25, base - 6, 50, 5, IRON[2]); cv.hline(cx - 25, base - 6, 50, IRON[4]); cv.hline(cx - 25, base - 2, 50, IRON[1])
    return cv, cx, base


def sentence_notice(width=78, height=52, label="ONE SENTENCE", seed=0):
    """An oak notice lectern holding one typed sentence under red pencil: SAID struck through,
    MUST pencilled above it with a caret, other lines marked up. Prop, anchor bottom-centre."""
    rng = _rng(seed)
    cv = Canvas(width + 6, height + 6, seed=seed)
    ox, base = 3, height + 3
    ground_shadow(cv, ox + width // 2, base, width // 2 - 4, 2)
    for px_ in (ox + 8, ox + width - 12):
        cv.rect(px_, base - 12, 4, 12, OUT); cv.vline(px_ + 1, base - 12, 11, OAK[3]); cv.vline(px_ + 2, base - 12, 11, OAK[2])
        cv.rect(px_ - 3, base - 2, 10, 2, OUT); cv.hline(px_ - 2, base - 2, 8, OAK[3])
    top = base - height
    cv.rect(ox, top, width, height - 10, OUT)
    cv.rect(ox + 1, top + 1, width - 2, height - 12, OAK[3]); cv.hline(ox + 1, top + 1, width - 2, OAK[5])
    cv.vline(ox + 1, top + 1, height - 12, OAK[4]); cv.vline(ox + width - 2, top + 1, height - 12, OAK[1])
    tw = text_width(label)
    cv.rect(ox + 2, top + 2, width - 4, 11, "#1f1a2a"); cv.hline(ox + 2, top + 2, width - 4, BRASS[3]); cv.hline(ox + 2, top + 12, width - 4, BRASS[1])
    text(cv, label, ox + width // 2 - tw // 2, top + 3, GILT)
    sx, sy, sw, sh = ox + 4, top + 15, width - 8, height - 29
    cv.rect(sx + 1, sy + 1, sw, sh, C("#0d0b16", 0.4))
    cv.rect(sx, sy, sw, sh, PAGE[3]); cv.hline(sx, sy, sw, "#fff8e6")
    # MUST pencilled above, SAID typed below and struck out, a caret between
    wx = sx + sw // 2 - 12
    text(cv, "MUST", wx + 2, sy, RED_PENCIL[1])
    text(cv, "SAID", wx, sy + 11, INK_BLUE)
    cv.hline(wx - 1, sy + 15, 26, RED_PENCIL[1])
    cv.line(wx + 10, sy + 10, wx + 12, sy + 8, RED_PENCIL[2]); cv.line(wx + 12, sy + 8, wx + 14, sy + 10, RED_PENCIL[2])
    # the rest of the sentence, typed, with a red mark or two
    for ly in (sy + 17,):
        cv.hline(sx + 2, ly, wx - sx - 4, "#6a6070"); cv.hline(wx + 26, ly, sx + sw - wx - 28, "#6a6070")
    cv.hline(sx + 2, sy + 5, wx - sx - 4, "#8a7e72"); cv.hline(wx + 28, sy + 5, sx + sw - wx - 30, "#8a7e72")
    cv.hline(sx + 4, sy + 5, 5, RED_PENCIL[1])
    cv.px(sx + sw - 3, sy + 2, RED_PENCIL[2])
    return cv, ox + width // 2, base


# --- closed archive ---------------------------------------------------------------------------
BOXES = ["#5a5048", "#6e6458", "#8a7e6c", "#4a5058", "#5e6670", "#7a6a5a"]        # archive boxes, buff and grey
SLATE = ["#2a2428", "#3e3438", "#4a3e40", "#544648", "#5e5050", "#6a5a58"]          # worn warm-grey stone flags
SASH = ["#5a1a20", "#8a2a2e", "#b03a3a"]
VAULT = ["#1e171c", "#2e2428", "#463a3a", "#6a5852", "#58484a", "#7a665c"]           # chequered archive flags


def drawer_grid(cv, x, y, w, h, seed=0, dw=9, dh=6, pal=OAK, open_rate=0.04, label=True):
    """A wall of small card-index drawers: oak faces with a lit top edge, a cream label in a brass
    frame and a brass pull on each; a few drawers left pulled out with cards standing up."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, OAK_DARK[1])
    opened = []
    for yy in range(y + 1, y + h - dh + 1, dh + 1):
        for xx in range(x + 1, x + w - dw + 1, dw + 1):
            tone = pal[3] if rng.random() < 0.7 else pal[4]
            cv.rect(xx, yy, dw, dh, tone)
            cv.hline(xx, yy, dw, shade(tone, 0.12))
            if label:
                cv.rect(xx + dw // 2 - 2, yy + 1, 4, 2, PAGE[2] if rng.random() < 0.85 else PAGE[3])
            cv.hline(xx + dw // 2 - 1, yy + dh - 2, 2, BRASS[3])
            if rng.random() < open_rate:
                opened.append((xx, yy))
    for (xx, yy) in opened:
        cv.rect(xx - 1, yy + 1, dw + 2, dh + 2, OUT)
        cv.rect(xx, yy + 2, dw, dh, pal[4]); cv.hline(xx, yy + 2, dw, pal[5])
        for k in range(dw // 2):
            cv.vline(xx + 1 + k * 2, yy - 1, 3, PAGE[3] if k % 2 else PAGE[2])
        cv.hline(xx + dw // 2 - 1, yy + dh, 2, BRASS[4])
    return opened


def index_wall(cv, x, top, w, base, seed=0, dw=9, dh=6, open_rate=0.03):
    """Floor-to-cornice card-index drawers built into a wall: carved cornice, banks of drawers
    between oak stiles, a plinth at the floor."""
    cv.rect(x - 4, top - 7, w + 8, 7, OUT)
    cv.rect(x - 3, top - 6, w + 6, 5, OAK[3]); cv.hline(x - 3, top - 6, w + 6, OAK[5]); cv.hline(x - 3, top - 3, w + 6, OAK[2])
    cv.rect(x - 3, top, w + 6, base - top, OAK[2])
    plinth = 7
    bank = 4 * (dw + 1) + 1
    opened = []
    bx = x
    while bx + bank <= x + w:
        opened += drawer_grid(cv, bx, top + 2, bank, base - plinth - top - 3, seed=seed + bx, dw=dw, dh=dh, open_rate=open_rate)
        bx += bank + 3
    cv.rect(x - 3, base - plinth, w + 6, plinth, OAK[2]); cv.hline(x - 3, base - plinth, w + 6, OAK[4])
    cv.hline(x - 3, base - 2, w + 6, OAK[1])
    return opened


def index_cabinet(width=145, height=118, seed=0, boxes=True):
    """A tall freestanding card-index cabinet (INDEX's kin): banks of small drawers with cream
    labels and brass pulls, some pulled out bristling with cards, card trays and archive boxes
    stacked on top, a moulded base on turned feet. Prop, anchor bottom-centre."""
    rng = _rng(seed)
    cv = Canvas(width + 10, height + 10, seed=seed)
    ox, base = 5, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.48)
    top = base - height
    top_load = 22 if boxes else 0
    body_top = top + top_load
    cv.rect(ox, body_top, width, height - top_load, OUT)
    # top surface (seen a little from above) and cornice
    cv.rect(ox - 2, body_top - 5, width + 4, 6, OUT)
    cv.rect(ox - 1, body_top - 4, width + 2, 4, OAK[4]); cv.hline(ox - 1, body_top - 4, width + 2, OAK[5])
    cv.rect(ox - 2, body_top, width + 4, 6, OUT)
    cv.rect(ox - 1, body_top + 1, width + 2, 4, OAK[3]); cv.hline(ox - 1, body_top + 1, width + 2, OAK[5]); cv.hline(ox - 1, body_top + 4, width + 2, OAK[1])
    inner_top = body_top + 6
    feet = 8
    cv.rect(ox + 1, inner_top, width - 2, base - feet - inner_top, OAK[2])
    cv.vline(ox + 1, inner_top, base - feet - inner_top, OAK[4]); cv.vline(ox + width - 2, inner_top, base - feet - inner_top, OAK[1])
    # banks of drawers
    dw, dh = 9, 7
    bank = 4 * (dw + 1) + 1
    nb = max(1, (width - 8 + 3) // (bank + 3))
    span = nb * bank + (nb - 1) * 3
    bx = ox + (width - span) // 2
    for b in range(nb):
        drawer_grid(cv, bx, inner_top + 3, bank, base - feet - inner_top - 8, seed=seed * 7 + b, dw=dw, dh=dh, open_rate=0.07)
        bx += bank + 3
    # base and feet
    cv.rect(ox - 1, base - feet - 4, width + 2, 4, OAK[3]); cv.hline(ox - 1, base - feet - 4, width + 2, OAK[5])
    for fx in (ox + 3, ox + width // 2 - 3, ox + width - 9):
        cv.rect(fx, base - feet, 6, feet, OUT); cv.rect(fx + 1, base - feet, 4, feet - 1, OAK[2]); cv.vline(fx + 1, base - feet, feet - 1, OAK[4])
    # on top: archive boxes, card trays, a ledger
    if boxes:
        x = ox + 3
        while x < ox + width - 16:
            k = rng.random()
            if k < 0.55:
                bw, bh = int(rng.integers(16, 24)), int(rng.integers(12, 19))
                c = BOXES[int(rng.integers(len(BOXES)))]
                bt = body_top - 2
                cv.rect(x - 1, bt - bh - 1, bw + 2, bh + 1, OUT)
                cv.rect(x, bt - bh, bw, bh, c); cv.hline(x, bt - bh, bw, shade(c, 0.25))
                cv.vline(x + bw - 1, bt - bh, bh, shade(c, -0.2))
                cv.rect(x + bw // 2 - 4, bt - bh + 3, 8, 4, PAGE[3]); cv.hline(x + bw // 2 - 3, bt - bh + 4, 6, "#6a6070")
                cv.rect(x + bw // 2 - 2, bt - 5, 4, 2, shade(c, -0.4))
                x += bw + 1
            elif k < 0.8:
                tw = int(rng.integers(14, 20))
                bt = body_top - 2
                cv.rect(x - 1, bt - 8, tw + 2, 8, OUT); cv.rect(x, bt - 7, tw, 7, OAK[3]); cv.hline(x, bt - 7, tw, OAK[5])
                for cx in range(x + 1, x + tw - 1, 2):
                    cv.vline(cx, bt - 10, 4, PAGE[3] if (cx // 2) % 2 else PAGE[2])
                x += tw + 2
            else:
                book_stack(cv, x, body_top - 2, 15, n=int(rng.integers(2, 4)), seed=seed + x)
                x += 17
    return cv, ox + width // 2, base


def archive_shelf(width=110, height=88, seed=0):
    """Steel archive shelving with buff and grey document boxes end-on (label holders, finger
    holes), a row of tall ledgers and a few loose folders. Prop, anchor bottom-centre."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.45)
    top = base - height
    post = ["#24222c", "#3a3846", "#545262", "#74728a"]
    cv.rect(ox, top, width, height, OUT)
    cv.rect(ox + 1, top + 1, width - 2, height - 2, "#16141c")
    rows = 3
    sh = (height - 8) // rows
    for r in range(rows):
        y1 = top + 4 + (r + 1) * sh
        y0 = y1 - sh
        x = ox + 5
        kind = r % 3
        while x < ox + width - 8:
            if kind == 1 and rng.random() < 0.8:
                # tall ledgers, spines out
                bw = int(rng.integers(5, 8))
                c = ["#5a2a26", "#2a3a5a", "#3a4a3a", "#6a4a2a"][int(rng.integers(4))]
                cv.rect(x, y0 + 4, bw, sh - 6, c); cv.vline(x, y0 + 4, sh - 6, shade(c, 0.2))
                cv.hline(x, y0 + 7, bw, GILT); cv.hline(x, y1 - 6, bw, GILT)
                cv.rect(x + 1, y0 + 10, bw - 2, 4, PAGE[2])
                x += bw
            else:
                bw = int(rng.integers(16, 22))
                c = BOXES[int(rng.integers(len(BOXES)))]
                bh = sh - 4 - int(rng.integers(0, 4))
                if x + bw > ox + width - 6:
                    break
                cv.rect(x, y1 - 2 - bh, bw, bh, c); cv.hline(x, y1 - 2 - bh, bw, shade(c, 0.22)); cv.vline(x + bw - 1, y1 - 2 - bh, bh, shade(c, -0.25))
                cv.rect(x + 3, y1 - bh + 1, bw - 6, 5, OUT); cv.rect(x + 4, y1 - bh + 2, bw - 8, 3, PAGE[3])
                cv.hline(x + 5, y1 - bh + 3, bw - 10, "#6a6070")
                cv.rect(x + bw // 2 - 2, y1 - 8, 4, 2, shade(c, -0.45))
                x += bw + 1
        cv.rect(ox + 1, y1 - 2, width - 2, 3, post[2]); cv.hline(ox + 1, y1 - 2, width - 2, post[3])
    for px_ in (ox + 1, ox + width - 4):
        cv.rect(px_, top + 1, 3, height - 2, post[2]); cv.vline(px_, top + 1, height - 2, post[3])
    cv.rect(ox + 1, top + 1, width - 2, 3, post[2]); cv.hline(ox + 1, top + 1, width - 2, post[3])
    return cv, ox + width // 2, base


def sorting_table(width=140, height=40, seed=0):
    """The archive's long sorting table: an oak top seen from above crowded with index-card trays,
    an open ledger of reserved seats (rows of little boxes, most marked), RESERVED tent cards,
    a date stamp and pad, card stacks; front apron and turned legs. Prop, anchor bottom-centre."""
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
    # the ledger of reserved seats, open in the middle
    lx, ly, lw, lh = ox + width // 2 - 22, top_y + 2, 44, 12
    cv.rect(lx - 2, ly - 1, lw + 4, lh + 2, OUT); cv.rect(lx - 1, ly, lw + 2, lh, "#5a2a26")
    cv.rect(lx, ly, lw, lh - 1, PAGE[3]); cv.vline(lx + lw // 2, ly, lh - 1, PAGE[0]); cv.vline(lx + lw // 2 - 1, ly, lh - 1, PAGE[2])
    for r in range(3):
        for c in range(9):
            sx = lx + 2 + c * 2 + (c // 4.5 > 0) * 0
            for side in (0, 1):
                px_ = lx + 2 + side * (lw // 2 + 1) + (c % 5) * 4
                if c >= 5:
                    continue
                py_ = ly + 2 + r * 3
                cv.rect(px_, py_, 3, 2, "#8a7e72")
                if rng.random() < 0.8:
                    cv.px(px_ + 1, py_, SASH[2])
    cv.vline(lx + lw // 2 + 6, ly + lh - 1, 6, SASH[1])
    # trays of index cards
    for tx in (ox + 6, ox + width - 30):
        cv.rect(tx - 1, top_y + 3, 24, 9, OUT); cv.rect(tx, top_y + 4, 22, 7, OAK[2]); cv.hline(tx, top_y + 4, 22, OAK[3])
        for cx in range(tx + 1, tx + 21, 2):
            cv.vline(cx, top_y + 1, 6, PAGE[3] if (cx // 2) % 3 else PAGE[2])
        cv.px(tx + 6, top_y + 1, SASH[2])
    # RESERVED tent cards
    for (tx, ty) in ((ox + 34, front - 3), (ox + width - 50, front - 2)):
        cv.poly([(tx, ty), (tx + 4, ty - 7), (tx + 16, ty - 7), (tx + 20, ty)], OUT)
        cv.poly([(tx + 1, ty - 1), (tx + 5, ty - 6), (tx + 15, ty - 6), (tx + 19, ty - 1)], PAGE[3])
        cv.hline(tx + 5, ty - 4, 10, SASH[1])
    # stamp and pad, loose cards
    cv.rect(ox + width - 22, top_y + 4, 10, 5, OUT); cv.rect(ox + width - 21, top_y + 5, 8, 3, "#2a3a6a")
    cv.rect(ox + width - 10, top_y - 1, 3, 6, OUT); cv.rect(ox + width - 9, top_y, 1, 4, OAK[2]); cv.rect(ox + width - 11, top_y + 4, 5, 2, IRON[2])
    for (cx, cy) in ((ox + 38, top_y + 6), (ox + 92, top_y + 8), (ox + 100, top_y + 4)):
        cv.rect(cx, cy, 7, 4, PAGE[3]); cv.hline(cx + 1, cy + 1, 5, "#8a7e72"); cv.px(cx + 5, cy + 2, SASH[2])
    return cv, ox + width // 2, base


def reserved_chairs(cv, x, base, n=5, cw=18, seed=0, label="RESERVED"):
    """A row of oak ceremony chairs set against a wall, a red sash looped across their backs and
    a RESERVED card hung on it in the middle. (x, base) is the left foot of the row."""
    for i in range(n):
        cx = x + i * cw
        # back legs/posts and the top rail
        cv.rect(cx + 2, base - 30, 3, 30, OUT); cv.rect(cx + cw - 6, base - 30, 3, 30, OUT)
        cv.vline(cx + 3, base - 29, 28, OAK[3]); cv.vline(cx + cw - 5, base - 29, 28, OAK[2])
        cv.rect(cx + 1, base - 32, cw - 3, 4, OUT); cv.rect(cx + 2, base - 31, cw - 5, 2, OAK[4]); cv.hline(cx + 2, base - 31, cw - 5, OAK[5])
        cv.rect(cx + 6, base - 28, cw - 11, 9, OAK_DARK[2]); cv.vline(cx + cw // 2 - 1, base - 28, 9, OAK[3])
        # seat seen from the front, front legs
        cv.rect(cx, base - 16, cw - 1, 4, OUT); cv.rect(cx + 1, base - 15, cw - 3, 2, "#4a2030"); cv.hline(cx + 1, base - 15, cw - 3, "#6a3040")
        cv.rect(cx + 1, base - 12, 2, 12, OAK[2]); cv.rect(cx + cw - 4, base - 12, 2, 12, OAK[1])
    # the sash in loops between the chair backs
    pts = []
    for i in range(n + 1):
        pts.append((x + i * cw + 2, base - 27))
    for i in range(n):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        for k in range(bx - ax + 1):
            t = k / max(1, bx - ax)
            yy = int(round(ay + 4 * np.sin(t * np.pi)))
            cv.px(ax + k, yy, SASH[1]); cv.px(ax + k, yy + 1, SASH[0])
    for i in range(n):
        cv.rect(x + i * cw + 5, base - 15, 6, 2, PAGE[3]); cv.px(x + i * cw + 7, base - 15, SASH[2])
    tw = text_width(label) + 6
    mx = x + n * cw // 2 - tw // 2
    ex = x + n * cw // 2
    cv.line(ex - 6, base, ex - 2, base - 12, OUT); cv.line(ex + 6, base, ex + 2, base - 12, OUT)
    cv.line(ex - 5, base, ex - 1, base - 12, OAK[4]); cv.line(ex + 5, base, ex + 1, base - 12, OAK[3])
    cy = base - 12
    cv.rect(mx - 1, cy - 1, tw + 2, 12, OUT); cv.rect(mx, cy, tw, 10, PAGE[3]); cv.hline(mx, cy, tw, "#fff8e6")
    cv.hline(mx, cy + 9, tw, PAGE[1])
    text(cv, label, mx + 3, cy - 1, SASH[1])


def chair_stack(cv, x, base, n=4):
    """Folding chairs folded flat and leaned against a wall one in front of another, ready for a
    ceremony: slatted backs, the folded seat as a bar, long legs. (x, base) is the left foot."""
    for i in range(n):
        cx = x + i * 4
        top = base - 38 + i
        lean = 3
        for (lx, c) in ((cx + 1, OAK[2]), (cx + 12, OAK[3])):
            cv.line(lx + lean, top + 2, lx, base - 1, OUT); cv.line(lx + lean + 1, top + 2, lx + 1, base - 1, c)
        cv.rect(cx + lean - 1, top, 16, 12, OUT)
        cv.rect(cx + lean, top + 1, 14, 10, OAK[4] if i % 2 else OAK[3]); cv.hline(cx + lean, top + 1, 14, OAK[5])
        cv.hline(cx + lean + 1, top + 5, 12, OAK[2]); cv.hline(cx + lean + 1, top + 8, 12, OAK[2])
        cv.rect(cx, base - 18, 15, 4, OUT); cv.rect(cx + 1, base - 17, 13, 2, "#4a2030"); cv.hline(cx + 1, base - 17, 13, "#6a3040")


def two_line_plaque(cv, cx, y, lines, fg=GILT, bg="#1c1622", frame=BRASS, chains=0):
    """An enamelled plaque with two centred lines of the game font, brass framed, optionally hung
    on chains from `chains` px above. Returns (x, y, w, h)."""
    w = max(text_width(s) for s in lines) + 16
    h = 12 * len(lines) + 6
    x = cx - w // 2
    if chains:
        for hx in (x + 8, x + w - 9):
            for yy in range(y - chains, y, 2):
                cv.px(hx, yy, IRON[3]); cv.px(hx, yy + 1, IRON[1])
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, frame[2]); cv.hline(x, y, w, frame[4]); cv.hline(x, y + h - 1, w, frame[0])
    cv.rect(x + 2, y + 2, w - 4, h - 4, bg)
    for i, s in enumerate(lines):
        text(cv, s, cx - text_width(s) // 2, y + 3 + i * 12, fg if i == 0 else shade(fg, -0.15))
    if len(lines) > 1:
        cv.hline(x + 6, y + 14, w - 12, frame[1])
    return x, y, w, h


def drawer_slots(x, y, w, h, dw=9, dh=6):
    """The (x, y) of every drawer drawer_grid paints in a bank, row by row (for animating them)."""
    return [(xx, yy) for yy in range(y + 1, y + h - dh + 1, dh + 1) for xx in range(x + 1, x + w - dw + 1, dw + 1)]


def index_wall_slots(x, top, w, base, dw=9, dh=6):
    """Drawer positions of every bank index_wall builds with the same arguments."""
    plinth = 7
    bank = 4 * (dw + 1) + 1
    out = []
    bx = x
    while bx + bank <= x + w:
        out += drawer_slots(bx, top + 2, bank, base - plinth - top - 3, dw, dh)
        bx += bank + 3
    return out


def drawer_out(dw=9, dh=6, pal=OAK, cards=True):
    """One drawer pulled half out of its bank, cards bristling (a blink frame for restless drawers).
    Paste or draw it at (slot_x - 1, slot_y - 2)."""
    cv = Canvas(dw + 2, dh + 5)
    cv.rect(0, 3, dw + 2, dh + 2, OUT)
    cv.rect(1, 4, dw, dh, pal[4]); cv.hline(1, 4, dw, pal[5])
    cv.rect(1 + dw // 2 - 2, 5, 4, 2, PAGE[3])
    cv.hline(1 + dw // 2 - 1, 4 + dh - 2, 2, BRASS[4])
    if cards:
        for k in range(dw // 2):
            cv.vline(2 + k * 2, 1, 3, PAGE[3] if k % 2 else PAGE[2])
    return cv


def ring(cv, cx, cy, rx, ry, color, t=1):
    """A flat elliptical ring (floor inlay): the pixels inside (rx, ry) but outside (rx-t, ry-t)."""
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    outer = ((xs - cx) / max(rx, 0.5)) ** 2 + ((ys - cy) / max(ry, 0.5)) ** 2 <= 1.0
    inner = ((xs - cx) / max(rx - t, 0.5)) ** 2 + ((ys - cy) / max(ry - t, 0.5)) ** 2 <= 1.0
    cv.fill_mask(outer & ~inner, color)


def index_rose(cv, cx, cy, rx=46, ry=15, line=BRASS[2], light=BRASS[4]):
    """A brass catalogue rose let into the floor: a double ring, tick marks like drawer pulls round
    it, four lozenges at the quarters and a small card at the centre."""
    ring(cv, cx, cy, rx, ry, C(line, 0.9))
    ring(cv, cx, cy, rx - 4, ry - 2, C(line, 0.7))
    for k in range(24):
        a = k / 24 * 2 * np.pi
        x0, y0 = cx + np.cos(a) * (rx - 1), cy + np.sin(a) * (ry - 1)
        x1, y1 = cx + np.cos(a) * (rx - 4), cy + np.sin(a) * (ry - 2)
        cv.line(int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1)), C(line, 0.8))
    for (dx, dy) in ((rx, 0), (-rx, 0), (0, ry), (0, -ry)):
        x, y = cx + dx, cy + dy
        cv.poly([(x - 4, y), (x, y - 2), (x + 4, y), (x, y + 2)], C(light, 0.9))
    cv.rect(cx - 6, cy - 2, 12, 5, C(PAGE[2], 0.55)); cv.hline(cx - 5, cy, 10, C(SASH[1], 0.6))


def floor_cards(cv, spots, seed=0):
    """Index cards fallen on a floor: cream rectangles with a red rule, a shadow pixel under each."""
    rng = _rng(seed)
    for (x, y) in spots:
        w = int(rng.integers(5, 8)); h = 3 if rng.random() < 0.7 else 4
        cv.hline(x + 1, y + h, w, C("#0d0b16", 0.35))
        cv.rect(x, y, w, h, PAGE[3] if rng.random() < 0.7 else PAGE[2])
        cv.hline(x, y, w, "#fff8e6")
        cv.hline(x + 1, y + 1, w - 2, SASH[2] if rng.random() < 0.6 else "#6a7aa8")


def archive_cage(cv, x, top, w, base, seed=0):
    """The closed archive itself, seen through a locked lattice grille set in the wall: a stone
    surround with keystone, darkness inside with tiers of boxed files receding to a single caged
    bulb, the gate's two leaves chained and padlocked in the middle."""
    rng = _rng(seed)
    h = base - top
    # stone surround and the deep reveal
    cv.rect(x - 8, top - 8, w + 16, h + 8, LIME[1])
    cv.rect(x - 7, top - 7, w + 14, h + 7, LIME[3]); cv.hline(x - 7, top - 7, w + 14, LIME[4])
    for k, vy in enumerate(range(top - 4, base - 4, 9)):
        cv.hline(x - 7, vy, 6, LIME[1]); cv.hline(x + w + 1, vy, 6, LIME[1])
    cv.rect(x + w // 2 - 6, top - 10, 13, 10, OUT); cv.rect(x + w // 2 - 5, top - 9, 11, 8, LIME[4]); cv.hline(x + w // 2 - 5, top - 9, 11, "#efe2c2")
    # the dark inside: far wall, tiers of shelving with boxes fading into the dark
    cv.rect(x, top, w, h, "#0f0c16")
    lamp_x = x + w // 3
    for tier in range(4):
        ty = top + 12 + tier * 24
        if ty + 18 > base:
            break
        xx = x + 2
        while xx < x + w - 6:
            bw = int(rng.integers(9, 15))
            bh = int(rng.integers(10, 16))
            d = min(1.0, abs((xx + bw / 2) - lamp_x) / (w * 0.8))
            c = shade(BOXES[int(rng.integers(len(BOXES)))], -0.45 - 0.35 * d)
            cv.rect(xx, ty + 18 - bh, bw, bh, c); cv.hline(xx, ty + 18 - bh, bw, shade(c, 0.18))
            if d < 0.5:
                cv.rect(xx + bw // 2 - 2, ty + 18 - bh + 3, 4, 2, shade(PAGE[3], -0.35 - d))
            xx += bw + 1
        cv.rect(x, ty + 18, w, 2, shade(IRON[2], -0.3)); cv.hline(x, ty + 18, w, shade(IRON[3], -0.35))
    for i, a in enumerate((0.1, 0.07, 0.05)):
        r = 14 + i * 12
        cv.ellipse(lamp_x - r, top + 8 - r // 2, r * 2, r, C("#f6cf7a", a))
    cv.vline(lamp_x, top, 6, IRON[2]); cv.rect(lamp_x - 2, top + 6, 5, 5, IRON[1]); cv.rect(lamp_x - 1, top + 7, 3, 3, "#fde9b6")
    cv.rect(x, top, w, 3, C("#0d0b16", 0.5))
    # lattice grille: diagonal bars both ways, riveted where they cross
    pitch = 10
    for k in range(-h, w + h, pitch):
        for yy in range(top, base):
            for (xx, col) in ((x + k + (yy - top), IRON[3]), (x + k + h - (yy - top), IRON[2])):
                if x <= xx < x + w:
                    cv.px(xx, yy, col)
    for yy in range(top + pitch // 2, base, pitch // 2):
        for xx in range(x, x + w):
            if (xx - x + yy - top) % pitch == 0 and (xx - x - (yy - top)) % pitch == 0:
                cv.px(xx, yy, IRON[4])
    # frame and the two leaves of the gate
    for (fx, fw) in ((x, 4), (x + w - 4, 4), (x + w // 2 - 2, 4)):
        cv.rect(fx, top, fw, h, OUT); cv.vline(fx + 1, top, h, IRON[3]); cv.vline(fx + 2, top, h, IRON[2])
    for fy in (top, top + h // 2, base - 4):
        cv.rect(x, fy, w, 4, OUT); cv.hline(x, fy + 1, w, IRON[3]); cv.hline(x, fy + 2, w, IRON[2])
    for fy in (top + 10, base - 14):
        for hx in (x - 2, x + w - 2):
            cv.rect(hx, fy, 4, 6, IRON[1]); cv.px(hx + 1, fy + 1, IRON[4])
    # chain looped through both leaves, a padlock hanging from it
    mx, my = x + w // 2, top + h // 2 - 4
    for k in range(-9, 10):
        yy = my - 4 + int(round(3 * np.cos(k / 9 * np.pi / 2)))
        cv.px(mx + k, yy, IRON[4] if k % 2 else IRON[2])
    cv.rect(mx - 4, my + 1, 9, 8, OUT); cv.rect(mx - 3, my + 2, 7, 6, BRASS[2]); cv.hline(mx - 3, my + 2, 7, BRASS[4])
    cv.rect(mx - 2, my - 3, 5, 4, OUT); cv.rect(mx - 1, my - 2, 3, 3, C("#0f0c16")); cv.px(mx, my + 4, OUT); cv.px(mx, my + 5, OUT)


def card_chute(cv, x, top, base, label="INTAKE"):
    """INDEX's intake: a glass pneumatic tube with brass collars dropping from the ceiling into a
    wire hopper heaped with index cards, a few spilling over the rim. x is the tube's centre.
    Returns the glass span (y0, y1) for card blink frames."""
    hop_top = base - 30
    tube_bot = hop_top - 10
    # glass tube: dark glass, a lit edge, brass collars
    cv.rect(x - 4, top, 9, tube_bot - top, OUT)
    cv.rect(x - 3, top, 7, tube_bot - top, "#3a4860"); cv.vline(x - 2, top, tube_bot - top, "#9ab0c8"); cv.vline(x - 1, top, tube_bot - top, "#4e6078")
    cv.vline(x + 2, top, tube_bot - top, "#262e40"); cv.vline(x + 3, top, tube_bot - top, "#1c2232")
    for cy in list(range(top + 6, tube_bot - 4, 22)) + [tube_bot - 4]:
        cv.rect(x - 5, cy, 11, 4, OUT); cv.rect(x - 4, cy + 1, 9, 2, BRASS[2]); cv.hline(x - 4, cy + 1, 9, BRASS[4])
    # flared mouth
    cv.poly([(x - 5, tube_bot - 1), (x + 5, tube_bot - 1), (x + 9, tube_bot + 6), (x - 9, tube_bot + 6)], OUT)
    cv.poly([(x - 4, tube_bot), (x + 4, tube_bot), (x + 7, tube_bot + 5), (x - 7, tube_bot + 5)], BRASS[3])
    cv.hline(x - 7, tube_bot + 5, 15, BRASS[1])
    # wire hopper on legs, heaped with cards
    hw = 30
    hx = x - hw // 2
    for lx in (hx + 2, hx + hw - 4):
        cv.rect(lx, hop_top + 16, 2, base - hop_top - 16, IRON[2]); cv.px(lx, base - 1, IRON[4])
    cv.poly([(hx, hop_top), (hx + hw, hop_top), (hx + hw - 4, hop_top + 17), (hx + 4, hop_top + 17)], OUT)
    cv.poly([(hx + 1, hop_top + 1), (hx + hw - 1, hop_top + 1), (hx + hw - 5, hop_top + 16), (hx + 5, hop_top + 16)], "#1c1824")
    rng = _rng(len(label) + x)
    for _ in range(46):
        cx = hx + 3 + int(rng.integers(0, hw - 8)); cy = hop_top - 4 + int(rng.integers(0, 16))
        cv.rect(cx, cy, int(rng.integers(3, 6)), 2, PAGE[3] if rng.random() < 0.6 else PAGE[2])
    for yy in range(hop_top + 3, hop_top + 17, 4):
        t = (yy - hop_top) / 17
        cv.hline(hx + 1 + int(4 * t), yy, hw - 2 - int(8 * t), C(IRON[3], 0.8))
    for xx in range(hx + 4, hx + hw - 2, 5):
        cv.line(xx, hop_top + 1, xx + (2 if xx < x else -2), hop_top + 16, C(IRON[3], 0.7))
    cv.hline(hx, hop_top, hw, IRON[4])
    cv.rect(hx + hw // 2 - 8, hop_top + 8, 17, 9, OUT)
    cv.rect(hx + hw // 2 - 7, hop_top + 9, 15, 7, BRASS[2]); cv.hline(hx + hw // 2 - 7, hop_top + 9, 15, BRASS[4])
    cv.rect(x - 4, hop_top + 10, 9, 5, PAGE[3]); cv.hline(x - 3, hop_top + 12, 7, SASH[1])
    return top + 2, tube_bot - 2


def velvet_rope(open_=False, rope=None, post=None):
    """Two brass stanchions with a red rope: hooked across with a little card (closed) or unhooked
    and hanging from the near post (open). Anchor: the sprite's top-left; the far post is left.
    rope/post palettes turn it into iron bollards with a chain for outdoors."""
    SASH_ = rope or SASH
    BRASS_ = post or BRASS
    cv = Canvas(34, 50)
    posts = [(5, 26), (27, 46)]
    for (px_, by) in posts:
        cv.ellipse(px_ - 5, by - 3, 11, 5, OUT); cv.ellipse(px_ - 4, by - 3, 9, 4, BRASS_[2]); cv.hline(px_ - 3, by - 3, 7, BRASS_[4])
        cv.rect(px_ - 2, by - 24, 4, 22, OUT); cv.vline(px_ - 1, by - 24, 22, BRASS_[4]); cv.vline(px_, by - 24, 22, BRASS_[2])
        cv.rect(px_ - 3, by - 27, 6, 5, OUT); cv.rect(px_ - 2, by - 26, 4, 3, BRASS_[3]); cv.hline(px_ - 2, by - 26, 4, BRASS_[4])
    (ax, ay), (bx, by) = (posts[0][0] + 2, posts[0][1] - 21), (posts[1][0] - 2, posts[1][1] - 21)
    if not open_:
        n = bx - ax
        pts = [(ax + n * t, ay + (by - ay) * t + 7 * np.sin(t * np.pi)) for t in np.linspace(0, 1, 10)]
        for (dy, c) in ((-1, OUT), (2, OUT), (1, SASH_[1]), (0, SASH_[2])):
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                cv.line(int(round(x0)), int(round(y0)) + dy, int(round(x1)), int(round(y1)) + dy, c)
        mx = ax + n // 2
        my = int(round(ay + (by - ay) * 0.5 + 7)) + 3
        cv.rect(mx - 6, my, 13, 9, OUT); cv.rect(mx - 5, my + 1, 11, 7, PAGE[3]); cv.hline(mx - 5, my + 1, 11, "#fff8e6")
        cv.hline(mx - 3, my + 4, 7, SASH_[1])
    else:
        for k in range(18):
            xx = bx + (1 if 6 < k < 13 else 0)
            cv.px(xx - 1, by + k, OUT); cv.px(xx, by + k, SASH_[2]); cv.px(xx + 1, by + k, SASH_[1]); cv.px(xx + 2, by + k, OUT)
        cv.rect(bx - 1, by + 18, 4, 2, BRASS_[3])
    return cv


def chair_row_back(n=3, cw=18, seed=0):
    """A row of oak ceremony chairs seen from behind (for the battle hall): turned back posts, a
    top rail and splat, the seat's back edge, a red sash looped from post to post and a small
    RESERVED card tied to each back. Returns a Canvas, feet on its bottom row."""
    rng = _rng(seed)
    cv = Canvas(n * cw + 2, 36)
    base = 35
    for i in range(n):
        cx = 1 + i * cw
        for (lx, c) in ((cx + 1, OAK[3]), (cx + cw - 4, OAK[2])):
            cv.rect(lx, base - 32, 3, 32, OUT); cv.vline(lx + 1, base - 31, 30, c)
        cv.rect(cx + 2, base - 15, cw - 4, 4, OUT); cv.rect(cx + 3, base - 14, cw - 6, 2, "#4a2030"); cv.hline(cx + 3, base - 14, cw - 6, "#6a3040")
        cv.rect(cx, base - 33, cw - 1, 5, OUT); cv.rect(cx + 1, base - 32, cw - 3, 3, OAK[4]); cv.hline(cx + 1, base - 32, cw - 3, OAK[5])
        cv.rect(cx + 6, base - 28, cw - 11, 12, OUT); cv.rect(cx + 7, base - 28, cw - 13, 11, OAK[3]); cv.vline(cx + 7, base - 28, 11, OAK[4])
        cv.rect(cx + cw // 2 - 4, base - 25, 7, 5, OUT); cv.rect(cx + cw // 2 - 3, base - 24, 5, 3, PAGE[3]); cv.hline(cx + cw // 2 - 2, base - 23, 3, SASH[1])
    for i in range(n):
        ax, bx = 2 + i * cw, 2 + (i + 1) * cw
        for k in range(bx - ax + 1):
            t = k / max(1, bx - ax)
            yy = int(round(base - 29 + 4 * np.sin(t * np.pi)))
            cv.px(ax + k, yy, SASH[2]); cv.px(ax + k, yy + 1, SASH[0])
    return cv


# --- playback room ----------------------------------------------------------------------------
ACOUSTIC = ["#0c161a", "#122026", "#1a2c34", "#223a42", "#2c4a52", "#3c5e64"]     # teal fabric panels
PHOSPHOR = ["#08140e", "#0e2418", "#1c4a2c", "#3a8a50", "#7ad08a", "#d0ffd8"]     # screen glass to trace
AMBER_LIT = ["#3a2410", "#7a4a1a", "#c8862e", "#f0b850", "#ffe0a0"]
CASE = ["#24222a", "#34313c", "#4a4652", "#6a6470", "#8a8494", "#b8b0a8"]         # equipment cases, grey
TAPE_BOXES = ["#c8b48a", "#d8d0c0", "#a83a32", "#3a4a7a", "#2a2830", "#8a6a3a", "#5c897c"]


def acoustic_wall(cv, x, y, w, h, seed=0, panel=26):
    """Acoustic panelling: pleated teal fabric panels between oak battens, a slim oak cap rail."""
    rng = _rng(seed)
    cv.rect(x, y, w, h, OAK_DARK[2])
    px_ = x + 2
    while px_ < x + w - 6:
        pw = min(panel, x + w - 2 - px_)
        cv.rect(px_, y + 3, pw, h - 6, ACOUSTIC[3])
        for k in range(px_ + 1, px_ + pw - 1, 3):
            cv.vline(k, y + 4, h - 8, ACOUSTIC[2]); cv.vline(k + 1, y + 4, h - 8, ACOUSTIC[4])
        cv.hline(px_, y + 3, pw, ACOUSTIC[5]); cv.hline(px_, y + h - 4, pw, ACOUSTIC[1])
        for _ in range(pw * h // 60):
            cv.px(px_ + int(rng.integers(0, pw)), y + 4 + int(rng.integers(0, h - 8)), ACOUSTIC[int(rng.choice([2, 4]))])
        bx = px_ + pw
        cv.rect(bx, y, 4, h, OAK[3]); cv.vline(bx, y, h, OAK[5]); cv.vline(bx + 3, y, h, OAK[1])
        cv.px(bx + 1, y + h // 3, BRASS[3]); cv.px(bx + 1, y + 2 * h // 3, BRASS[3])
        px_ = bx + 4
    cv.rect(x, y, w, 3, OAK[3]); cv.hline(x, y, w, OAK[5]); cv.hline(x, y + 2, w, OAK[1])
    cv.rect(x, y + h - 3, w, 3, OAK[2]); cv.hline(x, y + h - 3, w, OAK[4])


def lit_sign(cv, cx, y, label, glow=AMBER_LIT):
    """An illuminated sign box: dark face, letters lit amber, a stepped glow on the wall around it.
    Returns (x, y, w, h)."""
    w = text_width(label) + 12
    h = 14
    x = cx - w // 2
    for i, a in enumerate((0.06, 0.1)):
        cv.rect(x - 8 + i * 4, y - 5 + i * 2, w + 16 - i * 8, h + 10 - i * 4, C(glow[3], a))
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, CASE[2]); cv.hline(x, y, w, CASE[4])
    cv.rect(x + 2, y + 2, w - 4, h - 4, glow[0])
    text(cv, label, x + 6, y + 2, glow[4])
    return x, y, w, h


def waveform_screen(cv, x, y, w, h):
    """A big phosphor monitor set in the wall: grey case with a lit top edge, dark green glass with
    rounded corners, a dotted graticule, a playhead down the middle, a glint, two knobs below.
    Returns the glass rect (gx, gy, gw, gh) for waveform frames."""
    cv.rect(x - 1, y - 1, w + 2, h + 2, OUT)
    cv.rect(x, y, w, h, CASE[2]); cv.hline(x, y, w, CASE[4]); cv.hline(x, y + h - 1, w, CASE[0])
    cv.vline(x, y, h, CASE[3])
    gx, gy, gw, gh = x + 6, y + 5, w - 12, h - 14
    cv.rect(gx - 1, gy - 1, gw + 2, gh + 2, OUT)
    cv.rect(gx, gy, gw, gh, PHOSPHOR[0])
    for (cx_, cy_) in ((gx, gy), (gx + gw - 1, gy), (gx, gy + gh - 1), (gx + gw - 1, gy + gh - 1)):
        cv.px(cx_, cy_, OUT)
    for k in range(gx + 10, gx + gw - 2, 10):
        for yy in range(gy + 2, gy + gh - 1, 2):
            cv.px(k, yy, PHOSPHOR[1])
    for k in range(gy + 6, gy + gh - 2, 8):
        for xx in range(gx + 2, gx + gw - 1, 2):
            cv.px(xx, k, PHOSPHOR[1])
    for xx in range(gx + 1, gx + gw - 1):
        cv.px(xx, gy + gh // 2, PHOSPHOR[2] if xx % 2 else PHOSPHOR[1])
    for yy in range(gy + 1, gy + gh - 1):
        cv.px(gx + gw // 2, yy, PHOSPHOR[3] if yy % 3 else PHOSPHOR[2])
    cv.line(gx + 3, gy + 8, gx + 9, gy + 2, C("#c8e8d0", 0.18))
    for kx in (x + w - 22, x + w - 12):
        cv.rect(kx - 1, y + h - 8, 6, 6, OUT); cv.rect(kx, y + h - 7, 4, 4, CASE[4]); cv.px(kx + 1, y + h - 7, CASE[5])
    cv.rect(x + 8, y + h - 6, 4, 2, "#7ad08a")
    return gx, gy, gw, gh


def waveform_frame(gw, gh, k, n=8, seed=0):
    """One frame of a recorded voice scrolling across the glass: symmetric amplitude bars under a
    syllable envelope, a bright core, a dim halo. Frames 0..n-1 loop seamlessly."""
    rng = _rng(seed)
    cv = Canvas(gw, gh)
    mid = gh // 2
    bumps = [(rng.uniform(0, gw), rng.uniform(4, 12), rng.uniform(0.35, 1.0)) for _ in range(9)]
    shift = k * gw / n
    for x in range(1, gw - 1):
        u = (x + shift) % gw
        env = 0.06
        for (c, s, a) in bumps:
            d = min(abs(u - c), gw - abs(u - c))
            env = max(env, a * np.exp(-(d / s) ** 2))
        wob = 0.6 + 0.4 * abs(np.sin(u * 1.7 + 0.6 * np.sin(u * 0.43)))
        amp = int(round(env * wob * (mid - 2)))
        if amp <= 0:
            cv.px(x, mid, PHOSPHOR[3])
            continue
        cv.vline(x, mid - amp - 1, 2 * amp + 3, C(PHOSPHOR[3], 0.55))
        cv.vline(x, mid - amp, 2 * amp + 1, PHOSPHOR[4])
        cv.vline(x, mid - max(0, amp // 3), 2 * max(0, amp // 3) + 1, PHOSPHOR[5])
    return cv


def vu_pair(w=48, h=16, angles=(0.3, 0.5)):
    """Two amber VU meters side by side in a black bezel, needles at the given angles (0 left,
    1 right, red zone past 0.75). A Canvas (also used as animation frames)."""
    cv = Canvas(w, h)
    cv.rect(0, 0, w, h, OUT)
    mw = (w - 3) // 2
    for i, a in enumerate(angles):
        mx = 1 + i * (mw + 1)
        cv.rect(mx, 1, mw, h - 2, AMBER_LIT[3]); cv.hline(mx, 1, mw, AMBER_LIT[4])
        px_, py_ = mx + mw // 2, h - 3
        r = h - 6
        for t in np.linspace(0, 1, 9):
            ang = np.pi * (0.85 - 0.7 * t)
            cv.px(int(round(px_ + np.cos(ang) * r)), int(round(py_ - np.sin(ang) * r * 0.8)), "#b0382e" if t > 0.74 else AMBER_LIT[1])
        ang = np.pi * (0.85 - 0.7 * a)
        cv.line(px_, py_, int(round(px_ + np.cos(ang) * (r - 1))), int(round(py_ - np.sin(ang) * (r - 1) * 0.8)), "#2a1a10")
        cv.px(px_, py_, OUT)
    return cv


def loudspeaker(cv, cx, top, base, w=36):
    """A tall studio monitor standing against the wall: walnut cabinet, a black baffle with a big
    woofer, a mid cone and a dome tweeter, a brass badge, a short plinth. Returns the woofer (x, y, r)."""
    x = cx - w // 2
    cv.rect(x - 1, top - 1, w + 2, base - top + 1, OUT)
    cv.rect(x, top, w, base - top - 4, OAK[2]); cv.vline(x, top, base - top - 4, OAK[4]); cv.hline(x, top, w, OAK[5])
    cv.rect(x + 3, top + 3, w - 6, base - top - 12, "#1a181e")
    cv.rect(x + 2, base - 5, w - 4, 5, OAK_DARK[3]); cv.hline(x + 2, base - 5, w - 4, OAK[3])
    wr = (w - 10) // 2
    wy = base - 12 - wr - 2
    tw_y = top + 9
    mid_y = tw_y + 12
    for (yy, r, cone) in ((wy, wr, "#2c2a32"), (mid_y, max(4, wr // 2), "#2c2a32")):
        cv.ellipse(cx - r - 1, yy - r - 1, 2 * r + 3, 2 * r + 3, OUT)
        cv.ellipse(cx - r, yy - r, 2 * r + 1, 2 * r + 1, "#46424e")
        cv.ellipse(cx - r + 2, yy - r + 2, 2 * r - 3, 2 * r - 3, cone)
        cv.ellipse(cx - r // 3, yy - r // 3, 2 * (r // 3) + 1, 2 * (r // 3) + 1, "#5a5662")
        cv.px(cx - r // 3, yy - r // 3, "#8a8494")
        cv.line(cx - r + 2, yy - 2, cx - 2, yy - r + 2, C("#8a8494", 0.4))
    cv.ellipse(cx - 3, tw_y - 3, 7, 7, OUT); cv.ellipse(cx - 2, tw_y - 2, 5, 5, CASE[4]); cv.px(cx - 1, tw_y - 1, CASE[5])
    cv.rect(cx - 4, base - 11, 9, 3, BRASS[2]); cv.hline(cx - 4, base - 11, 9, BRASS[4])
    return cx, wy, wr


def woofer_push(r):
    """A woofer cone pushed out (a pulse frame): a lit rim and a brighter, bigger dust cap."""
    cv = Canvas(2 * r + 3, 2 * r + 3)
    c = r + 1
    cv.ellipse(1, 1, 2 * r + 1, 2 * r + 1, "#5a5662")
    cv.ellipse(3, 3, 2 * r - 3, 2 * r - 3, "#36343e")
    q = r // 3 + 1
    cv.ellipse(c - q, c - q, 2 * q + 1, 2 * q + 1, "#7a7686")
    cv.px(c - q + 1, c - q + 1, "#b8b0c0")
    cv.line(3, c - 2, c - 2, 3, C("#b8b0c0", 0.5))
    return cv


def reel_face(r, angle=0.0, tape=0.6):
    """A tape reel seen face on: aluminium flange with three windows, the brown tape pack showing
    through, a hub. Rotate with `angle` for animation frames."""
    cv = Canvas(2 * r + 3, 2 * r + 3)
    c = r + 1
    cv.ellipse(0, 0, 2 * r + 3, 2 * r + 3, OUT)
    cv.ellipse(1, 1, 2 * r + 1, 2 * r + 1, CASE[5])
    tr = int(r * tape)
    ys, xs = np.mgrid[0:cv.h, 0:cv.w]
    d = np.hypot(xs - c, ys - c)
    a = (np.arctan2(ys - c, xs - c) - angle) % (2 * np.pi / 3)
    win = (d > 4) & (d < r - 2) & (a > 0.35) & (a < 1.65)
    cv.fill_mask(win & (d <= tr), "#5a3a28")
    cv.fill_mask(win & (d > tr), "#14121a")
    cv.fill_mask(win & (np.abs(d - tr) < 0.6), "#7a5236")
    cv.ellipse(c - 3, c - 3, 7, 7, CASE[3]); cv.ellipse(c - 1, c - 1, 3, 3, OUT)
    cv.px(c - r + 3, c - r // 2, "#e8e4ee")
    return cv


def tape_machine(cv, x, top, w=96, base=142, seed=0):
    """A floor-standing archive tape machine against the wall: grey cabinet, a top deck plate with
    two big reels and the tape running round the heads, a counter, transport keys, a VU pair and a
    vented base. Returns the reel centres and radius for animation frames."""
    cv.rect(x - 1, top - 1, w + 2, base - top + 1, OUT)
    cv.rect(x, top, w, base - top, CASE[3]); cv.hline(x, top, w, CASE[4]); cv.vline(x, top, base - top, CASE[4])
    cv.vline(x + w - 1, top, base - top, CASE[1])
    deck_h = 56
    cv.rect(x + 3, top + 3, w - 6, deck_h, CASE[2]); cv.hline(x + 3, top + 3, w - 6, CASE[1])
    r = 15
    reels = [(x + 3 + r + 4, top + 3 + r + 4), (x + w - 3 - r - 5, top + 3 + r + 4)]
    for (rx, ry) in reels:
        cv.paste(reel_face(r, 0.3, tape=0.75 if rx < x + w // 2 else 0.45), rx - r - 1, ry - r - 1)
    hy = top + deck_h - 6
    cv.rect(x + w // 2 - 12, hy - 4, 24, 7, CASE[1]); cv.rect(x + w // 2 - 10, hy - 3, 20, 5, CASE[4])
    for gx in (x + w // 2 - 6, x + w // 2, x + w // 2 + 6):
        cv.rect(gx - 1, hy - 2, 3, 3, CASE[5])
    (lx, ly), (rx, ry) = reels
    cv.line(lx - 2, ly + r - 4, x + w // 2 - 12, hy, "#5a3a28")
    cv.line(rx + 2, ry + r - 4, x + w // 2 + 12, hy, "#5a3a28")
    cv.hline(x + w // 2 - 12, hy - 4, 24, "#5a3a28")
    for gx in (x + 10, x + w - 11):
        cv.ellipse(gx - 2, hy - 2, 5, 5, CASE[5]); cv.px(gx, hy, OUT)
    # control strip: counter, VU pair, keys
    sy = top + deck_h + 6
    cv.rect(x + 6, sy, 22, 8, OUT); cv.rect(x + 7, sy + 1, 20, 6, "#141218")
    for k in range(4):
        cv.rect(x + 8 + k * 5, sy + 2, 3, 4, "#e8e4ee" if k != 3 else AMBER_LIT[3])
    cv.paste(vu_pair(36, 14, (0.45, 0.6)), x + w - 42, sy - 2)
    for k in range(6):
        c = "#c84a3c" if k == 4 else ("#7ad08a" if k == 2 else CASE[5])
        cv.rect(x + 8 + k * 9, sy + 14, 7, 5, OUT); cv.rect(x + 9 + k * 9, sy + 15, 5, 3, c); cv.hline(x + 9 + k * 9, sy + 15, 5, shade(c, 0.3))
    for vy in range(sy + 26, base - 4, 3):
        cv.hline(x + 8, vy, w - 16, CASE[1])
    cv.rect(x, base - 4, w, 4, CASE[1])
    return reels, r


def playback_console(width=180, height=48, seed=0):
    """The playback console where the source reel is threaded: an oak desk on two drawer
    pedestals; on its top a mixer of faders and coloured knobs, a reel-to-reel deck standing up at
    the back with the source reel (green leader) on the left spindle, a VU pair, headphones and a
    log sheet. Prop, anchor bottom-centre."""
    rng = _rng(seed)
    pad_top = 30
    cv = Canvas(width + 8, height + pad_top + 6, seed=seed)
    ox, base = 4, height + pad_top + 2
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.45)
    front = base - 24
    top_y = front - 16
    cx = ox + width // 2
    # pedestals and knee space
    cv.rect(ox, front, width, base - front, OUT)
    cv.rect(ox + 1, front, width - 2, base - front - 1, OAK_DARK[1])
    for (px_, pw) in ((ox + 1, 40), (ox + width - 41, 40)):
        cv.rect(px_, front, pw, base - front - 1, OAK[3]); cv.vline(px_, front, base - front - 1, OAK[4])
        for k in range(2):
            dy = front + 4 + k * 9
            cv.rect(px_ + 3, dy, pw - 6, 7, OAK[2]); cv.hline(px_ + 3, dy, pw - 6, OAK[4])
            cv.rect(px_ + pw // 2 - 3, dy + 3, 6, 2, BRASS[3])
        cv.rect(px_, base - 4, pw, 3, OAK_DARK[3])
    cv.rect(ox + 41, front + 2, width - 82, 6, OAK[2]); cv.hline(ox + 41, front + 2, width - 82, OAK[4])
    # top surface
    cv.rect(ox - 1, top_y - 1, width + 2, front - top_y + 3, OUT)
    cv.rect(ox, top_y, width, front - top_y, OAK[4]); cv.hline(ox, top_y, width, OAK[5])
    cv.rect(ox, front - 2, width, 3, OAK[3]); cv.hline(ox, front - 2, width, OAK[5])
    # mixer on the left
    mx, my = ox + 6, top_y + 2
    cv.rect(mx - 1, my - 1, 52, 13, OUT); cv.rect(mx, my, 50, 11, CASE[2]); cv.hline(mx, my, 50, CASE[4])
    for k in range(8):
        fx = mx + 3 + k * 6
        cv.vline(fx + 1, my + 4, 6, OUT)
        cv.rect(fx, my + 4 + int(rng.integers(0, 4)), 3, 2, CASE[5] if k % 4 else "#c84a3c")
        cv.px(fx + 1, my + 2, ["#c84a3c", "#e9a84a", "#7ad08a", "#6a8ac8"][k % 4])
    # VU pair and headphones on the right, a log sheet
    cv.paste(vu_pair(30, 12, (0.55, 0.42)), ox + width - 36, top_y - 4)
    headphones(cv, ox + width - 58, top_y + 9, band="#2a2830", cup="#4a4652")
    cv.rect(ox + 60, top_y + 4, 11, 9, PAGE[3]); cv.hline(ox + 61, top_y + 6, 8, PAGE[0]); cv.hline(ox + 61, top_y + 8, 7, PAGE[0])
    cv.hline(ox + 61, top_y + 10, 6, PAGE[0])
    # upright deck at the back, the source reel on the left spindle
    dw, dh = 64, 30
    dx, dy = cx - dw // 2, top_y - dh + 8
    cv.rect(dx - 1, dy - 1, dw + 2, dh + 2, OUT)
    cv.rect(dx, dy, dw, dh, CASE[3]); cv.hline(dx, dy, dw, CASE[5]); cv.vline(dx, dy, dh, CASE[4])
    r = 10
    for i, rx in enumerate((dx + 15, dx + dw - 15)):
        cv.paste(reel_face(r, 0.2 + i, tape=0.8 if i == 0 else 0.4), rx - r - 1, dy + 2)
    cv.rect(dx + 15 - 2, dy + 2 + 2, 4, 3, "#5ec27a")
    hy = dy + dh - 6
    cv.rect(cx - 8, hy - 2, 16, 5, CASE[1]); cv.rect(cx - 6, hy - 1, 12, 3, CASE[5])
    cv.line(dx + 9, dy + 2 + 2 * r - 2, cx - 8, hy, "#5a3a28"); cv.line(dx + dw - 9, dy + 2 + 2 * r - 2, cx + 8, hy, "#5a3a28")
    for k in range(5):
        c = "#c84a3c" if k == 1 else ("#7ad08a" if k == 2 else CASE[5])
        cv.rect(cx - 13 + k * 6, top_y + 4, 5, 3, OUT); cv.rect(cx - 12 + k * 6, top_y + 4, 3, 2, c)
    return cv, cx, base


def tape_shelf(width=100, height=94, seed=0):
    """Open oak shelving of the tape archive: boxed reels standing spine-out (buff, white, red,
    blue), a few lying in stacks, round reel cans, and on top a pile of cans. Prop, bottom-centre."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 8, seed=seed)
    ox, base = 4, height + 4
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.45)
    top = base - height + 10
    cv.rect(ox, top, width, base - top, OUT)
    cv.rect(ox + 1, top + 1, width - 2, base - top - 2, OAK_DARK[2])
    rows = 4
    sh = (base - top - 10) // rows
    for r_ in range(rows):
        y1 = top + 4 + (r_ + 1) * sh
        x = ox + 5
        while x < ox + width - 8:
            k = rng.random()
            if k < 0.68:
                bw = int(rng.integers(3, 5)); bh = sh - 4 - int(rng.integers(0, 2))
                c = TAPE_BOXES[int(rng.choice([0, 0, 1, 1, 1, 2, 3, 4, 5, 6]))]
                cv.rect(x, y1 - 2 - bh, bw, bh, c); cv.vline(x, y1 - 2 - bh, bh, shade(c, 0.2))
                cv.vline(x + bw - 1, y1 - 2 - bh, bh, shade(c, -0.25))
                cv.rect(x, y1 - bh + 2, bw, 3, PAGE[3] if c not in (TAPE_BOXES[1],) else "#c84a3c")
                x += bw
            elif k < 0.85:
                n = int(rng.integers(2, 4)); bw = int(rng.integers(12, 16))
                for j in range(n):
                    c = TAPE_BOXES[int(rng.integers(len(TAPE_BOXES)))]
                    cv.rect(x, y1 - 2 - (j + 1) * 3, bw, 3, c); cv.hline(x, y1 - 2 - (j + 1) * 3, bw, shade(c, 0.2))
                x += bw + 1
            else:
                rr = min(7, (sh - 5) // 2)
                if x + 2 * rr + 3 > ox + width - 6:
                    break
                cv.paste(reel_face(rr, float(rng.uniform(0, 2)), tape=float(rng.uniform(0.4, 0.8))), x, y1 - 2 - (2 * rr + 3))
                x += 2 * rr + 4
            if x > ox + width - 8:
                break
        cv.rect(ox + 1, y1 - 2, width - 2, 3, OAK[3]); cv.hline(ox + 1, y1 - 2, width - 2, OAK[5])
    for px_ in (ox + 1, ox + width - 4):
        cv.rect(px_, top + 1, 3, base - top - 2, OAK[3]); cv.vline(px_, top + 1, base - top - 2, OAK[4])
    cv.rect(ox - 1, top - 2, width + 2, 4, OUT); cv.rect(ox, top - 1, width, 2, OAK[4]); cv.hline(ox, top - 1, width, OAK[5])
    # reel cans piled on top
    for j, (cx_, w_) in enumerate(((ox + 20, 22), (ox + 22, 18), (ox + 64, 24))):
        yy = top - 3 - (j % 2) * 4 if cx_ < ox + 40 else top - 3
        cv.ellipse(cx_ - w_ // 2 - 1, yy - 4, w_ + 2, 7, OUT); cv.ellipse(cx_ - w_ // 2, yy - 3, w_, 5, CASE[4])
        cv.ellipse(cx_ - w_ // 2 + 3, yy - 2, w_ - 6, 3, CASE[5])
    cv.rect(ox + width - 26, top - 10, 14, 8, OUT); cv.rect(ox + width - 25, top - 9, 12, 6, TAPE_BOXES[0]); cv.hline(ox + width - 25, top - 9, 12, PAGE[3])
    return cv, ox + width // 2, base


def listening_desk(width=100, height=36, seed=0):
    """A small listening desk: oak top with a headphone amplifier (jacks and green lights), the
    spare pair of headphones lying out, another pair hung on a little stand, cue cards and a pencil;
    a chair back behind. Prop, anchor bottom-centre."""
    from lib_norlin import reading_table

    def extra(cv, ox, top_y, w):
        cv.rect(ox + 8, top_y + 2, 26, 8, OUT); cv.rect(ox + 9, top_y + 3, 24, 6, CASE[3]); cv.hline(ox + 9, top_y + 3, 24, CASE[5])
        for k in range(4):
            cv.px(ox + 11 + k * 6, top_y + 6, OUT); cv.px(ox + 12 + k * 6, top_y + 5, "#7ad08a")
        headphones(cv, ox + 44, top_y + 8, band="#3a2a20", cup="#6a4a3a", cord_to=(ox + 30, top_y + 9))
        sx = ox + w - 16
        cv.rect(sx, top_y - 8, 2, 14, IRON[2]); cv.rect(sx - 3, top_y + 5, 8, 2, IRON[1])
        for k in range(9):
            a = np.pi + np.pi * k / 8
            cv.px(int(round(sx + 1 + np.cos(a) * 5)), int(round(top_y - 8 + np.sin(a) * 3)), "#2a2830")
        cv.rect(sx - 6, top_y - 6, 4, 6, OUT); cv.rect(sx + 4, top_y - 6, 4, 6, OUT)
        cv.rect(sx - 5, top_y - 5, 2, 4, "#4a4652"); cv.rect(sx + 5, top_y - 5, 2, 4, "#4a4652")
        cv.rect(ox + 64, top_y + 3, 9, 6, PAGE[3]); cv.hline(ox + 65, top_y + 5, 6, PAGE[0])
        cv.line(ox + 62, top_y + 9, ox + 70, top_y + 7, "#c47a2c")

    return reading_table(width, height, lamps=0, seed=seed, chairs=True, clutter=False, top_depth=11, extra=extra)


# --- roof garden ------------------------------------------------------------------------------
GRAVEL = ["#3a3234", "#4a4040", "#564a48", "#625450", "#6e5e58", "#7c6a62"]
SLEEPER = ["#1e1412", "#2e201a", "#3e2c22", "#52392a", "#664834"]                   # weathered timber
NIGHT_CLOUD = ["#2c2648", "#3a3058", "#463864", "#52406c", "#6a4c76", "#8e5e80", "#b47486"]
MOUNTAIN = ["#17152a", "#1f1c36", "#2a2644", "#36304f", "#433a5c", "#56486c"]
LAVENDER = ["#4a3a6a", "#6a54a0", "#8a72c0", "#b49ad8"]


def night_sky(cv, x, y, w, h, seed=0, stars=120, star_h=None):
    """Stepped indigo bands (the Norlin night), stars scattered in the upper part."""
    bands = ["#141432", "#1b1a3e", "#232149", "#2e2853", "#3b2f5c", "#4c3762", "#5e3f66"]
    for yy in range(y, y + h):
        t = (yy - y) / max(1, h - 1)
        cv.hline(x, yy, w, bands[min(len(bands) - 1, int(t ** 0.9 * len(bands)))])
    rng = _rng(seed)
    pts = []
    for _ in range(stars):
        sx, sy = x + int(rng.integers(0, w)), y + int(rng.integers(0, star_h or int(h * 0.75)))
        cv.px(sx, sy, "#c8c0e0" if rng.random() < 0.65 else "#f2d27a")
        pts.append((sx, sy))
    return pts


def moon(cv, mx, my, r=8):
    """The Norlin moon: a stepped halo, a pale disc with a lit cap and a few maria."""
    for rr, a in [(r * 3, 0.05), (r * 2, 0.08), (int(r * 1.4), 0.1)]:
        cv.ellipse(mx - rr, my - rr, rr * 2 + 1, rr * 2 + 1, C("#efe2b8", a))
    cv.ellipse(mx - r, my - r, 2 * r + 1, 2 * r + 1, "#efe2b8"); cv.ellipse(mx - r + 2, my - r + 1, r + 1, r - 1, "#fff4d2")
    for (cx, cy) in [(mx - 3, my + 2), (mx + 3, my - 3), (mx + 1, my + 4)]:
        cv.px(cx, cy, "#d8c8a0")


def flatirons_night(cv, x0, x1, base, seed=0, tall=1.0):
    """The Flatirons at night on the western horizon: the dark forested bulk of Green Mountain
    behind, and in front of it three great sandstone slabs tilted up toward the east - a steep west
    edge, a rounded crest and a long ribbed east face catching a little moonlight - separated by
    dark wooded gullies, pines thick on the lower slopes."""
    rng = _rng(seed)
    span = x1 - x0
    # Green Mountain: a broad dark mass with a ragged ridge
    ridge = []
    for x in range(x0, x1 + 1):
        t = (x - x0) / span
        hgt = (52 + 14 * np.sin(t * np.pi * 0.9 + 0.3) - 8 * t) * tall
        hgt *= min(1.0, (1 - t) / 0.22) ** 0.8 if t > 0.78 else 1.0
        ridge.append(int(base - hgt + rng.integers(0, 2)))
    for i, x in enumerate(range(x0, x1 + 1)):
        cv.vline(x, ridge[i], base - ridge[i] + 1, MOUNTAIN[1])
        if i % 3 == 0:
            cv.px(x, ridge[i], MOUNTAIN[2])
    # the slabs, back to front
    slabs = [(0.04, 0.42, 58), (0.36, 0.70, 50), (0.64, 0.94, 40)]
    for k, (a, b, hgt) in enumerate(slabs):
        hgt = int(round(hgt * tall))
        sx0, sx1 = x0 + int(a * span), x0 + int(b * span)
        w = sx1 - sx0
        top = base - hgt
        crest = sx0 + int(w * 0.2)
        pts = [(sx0, base), (sx0 + int(w * 0.08), top + int(hgt * 0.35)), (crest - 3, top + 3), (crest, top),
               (crest + 4, top + 1), (crest + int(w * 0.18), top + int(hgt * 0.16)), (sx1, base)]
        cv.poly(pts, MOUNTAIN[2])
        face = [(crest, top + 1), (crest + 4, top + 2), (crest + int(w * 0.18), top + int(hgt * 0.17)), (sx1, base), (crest + int(w * 0.1), base)]
        cv.poly(face, MOUNTAIN[3])
        # ribs of bedding down the east face
        for j in range(1, 6):
            t = j / 6
            xa = crest + int(w * 0.04 * j)
            cv.line(xa, top + 2 + j, xa + int((sx1 - xa) * 0.85), base - 1, MOUNTAIN[4] if j % 2 else MOUNTAIN[2])
        cv.line(crest, top, crest + int(w * 0.18), top + int(hgt * 0.16), MOUNTAIN[5])
        cv.line(crest + int(w * 0.18), top + int(hgt * 0.16), sx1, base, MOUNTAIN[4])
        # a dark wooded gully at the foot of the west edge
        for yy in range(top + int(hgt * 0.45), base):
            gw = int((yy - top) * 0.25)
            cv.hline(sx0 - gw // 2, yy, gw, MOUNTAIN[0])
    for _ in range(span * 3):
        px_ = x0 + int(rng.integers(0, span))
        py_ = base - int(abs(rng.normal(0, 7)))
        cv.px(px_, py_, MOUNTAIN[0] if rng.random() < 0.7 else "#1c2224")


def campus_roofs(cv, x0, x1, base, seed=0, lit=0.4):
    """Campus below the terrace, beyond the parapet: tree crowns and the red tile hip roofs of
    sandstone halls with a few lit windows, a twin-towered auditorium. Returns lit window points."""
    rng = _rng(seed)
    lights = []
    for x in range(x0 - 8, x1 + 8, 10):
        hh = int(rng.integers(8, 18))
        cv.ellipse(x, base - hh, int(rng.integers(14, 22)), hh * 2, "#1a1c30")
    x = x0
    while x < x1 - 30:
        bw = int(rng.integers(40, 80)); bh = int(rng.integers(10, 18))
        if rng.random() < 0.35:
            x += bw // 2
            continue
        roof = "#4a2a2e" if rng.random() < 0.7 else "#3e2630"
        wall = "#2a2238"
        cv.rect(x, base - bh, bw, bh, wall)
        cv.poly([(x - 3, base - bh), (x + 6, base - bh - 7), (x + bw - 6, base - bh - 7), (x + bw + 3, base - bh)], roof)
        cv.hline(x + 6, base - bh - 7, bw - 12, "#6a3a36")
        for wx in range(x + 4, x + bw - 4, 6):
            if rng.random() < lit:
                cv.rect(wx, base - bh + 4, 2, 3, "#c98a46")
                lights.append((wx, base - bh + 4))
        x += bw + int(rng.integers(6, 30))
    return lights


def auditorium(cv, cx, base):
    """Macky's two square towers with pyramid caps, dark against the sky, one lit window each."""
    for dx in (-14, 14):
        tx = cx + dx
        cv.rect(tx - 5, base - 40, 11, 40, "#262036")
        cv.poly([(tx - 6, base - 40), (tx, base - 50), (tx + 6, base - 40)], "#4a2a2e")
        cv.rect(tx - 1, base - 32, 2, 4, "#c98a46")
    cv.rect(cx - 10, base - 22, 21, 22, "#262036")
    cv.poly([(cx - 12, base - 22), (cx, base - 30), (cx + 12, base - 22)], "#4a2a2e")


def balustrade(cv, x0, x1, top, base, piers=(), seed=0):
    """A sandstone balustrade (the roof parapet): limestone coping with a lit lip, a row of vase
    balusters with dark gaps showing the night between them, a plinth, square piers."""
    rng = _rng(seed)
    cope = 6
    plinth = 7
    cv.rect(x0, top + cope, x1 - x0, base - top - cope - plinth, "#1c1a30")
    for bx in range(x0 + 2, x1 - 4, 7):
        by0, by1 = top + cope, base - plinth
        hh = by1 - by0
        for yy in range(by0, by1):
            t = (yy - by0) / max(1, hh)
            wdt = 2 + int(round(2.2 * np.sin(np.pi * min(1.0, t * 1.15)) ** 0.8)) if t > 0.12 else 3
            cv.hline(bx + 2 - wdt // 2, yy, wdt + 1, STONE_N[3])
            cv.px(bx + 2 - wdt // 2, yy, STONE_N[4])
            cv.px(bx + 2 + wdt // 2, yy, STONE_N[1])
    cv.rect(x0, base - plinth, x1 - x0, plinth, STONE_N[2]); cv.hline(x0, base - plinth, x1 - x0, STONE_N[4])
    cv.hline(x0, base - 1, x1 - x0, STONE_N[1])
    cv.rect(x0, top, x1 - x0, cope, LIME[2]); cv.hline(x0, top, x1 - x0, LIME[5]); cv.hline(x0, top + 1, x1 - x0, LIME[4])
    cv.hline(x0, top + cope - 1, x1 - x0, LIME[0])
    for px_ in piers:
        cv.rect(px_ - 7, top - 4, 15, base - top + 4, OUT)
        cv.rect(px_ - 6, top - 3, 13, base - top + 3, STONE_N[3]); cv.vline(px_ - 6, top - 3, base - top + 3, STONE_N[4])
        cv.vline(px_ + 6, top - 3, base - top + 3, STONE_N[1])
        cv.rect(px_ - 8, top - 7, 17, 4, LIME[3]); cv.hline(px_ - 8, top - 7, 17, LIME[5])
        for k in range(top + 2, base - 2, 6):
            cv.hline(px_ - 6, k, 13, STONE_N[2])


def stone_urn(cv, cx, base, seed=0):
    """A sandstone urn on a pier top, trailing ivy and a few late flowers."""
    rng = _rng(seed)
    cv.rect(cx - 3, base - 4, 7, 4, OUT); cv.rect(cx - 2, base - 4, 5, 3, STONE_N[3])
    cv.ellipse(cx - 7, base - 14, 15, 11, OUT); cv.ellipse(cx - 6, base - 13, 13, 9, STONE_N[3])
    cv.ellipse(cx - 5, base - 13, 6, 7, STONE_N[4])
    cv.rect(cx - 8, base - 15, 17, 3, LIME[3]); cv.hline(cx - 8, base - 15, 17, LIME[5])
    spr = shrub(0, 0, 18, 12, seed=seed, flowers=MUM if rng.random() < 0.6 else None)
    cv.paste(spr, cx - 9, base - 26)
    for k in range(3):
        sx = cx - 7 + k * 6
        for j in range(int(rng.integers(4, 9))):
            cv.px(sx + (j % 2), base - 13 + j, LEAF[2] if j % 3 else LEAF[3])


def festoon(cv, x0, y0, x1, y1, sag=12, every=9, seed=0):
    """A festoon of warm bulbs on a dark cord between two points. Returns the bulb points."""
    rng = _rng(seed)
    n = max(2, abs(x1 - x0))
    pts = []
    for i in range(n + 1):
        t = i / n
        x = int(round(x0 + (x1 - x0) * t)); y = int(round(y0 + (y1 - y0) * t + sag * 4 * t * (1 - t)))
        cv.px(x, y, "#1a1418")
        if i % every == 0 and 0 < i < n:
            c = "#f6cf7a" if rng.random() < 0.8 else "#f2a0a0"
            cv.rect(x - 2, y + 1, 5, 4, C(c, 0.14))
            cv.px(x, y + 1, OUT); cv.px(x, y + 2, c); cv.px(x, y + 3, shade(c, 0.4))
            pts.append((x, y + 2))
    return pts


def tub_tree(height=110, seed=0, cell=5, tint=None):
    """A small tree in a square sandstone tub (roof-garden planting): the atlas tree trimmed to the
    tub, a limestone rim, a skirt of fallen leaves. Prop, anchor bottom-centre."""
    from midlib import sprite_from_cell
    tub_h, tub_w = 20, 40
    spr = sprite_from_cell(cell, height=height - tub_h + 8, colors=36)
    if tint is not None:
        spr = spr.copy(); spr[..., :3] = np.clip(spr[..., :3] * np.array(tint), 0, 1)
    sh, sw = spr.shape[:2]
    w = max(sw, tub_w + 8)
    cv = Canvas(w, height + 4, seed=seed)
    cx, base = w // 2, height + 1
    ground_shadow(cv, cx, base, tub_w // 2 + 4, 3, alpha=0.45)
    cv.paste(spr, cx - sw // 2, base - tub_h - sh + 8)
    ty = base - tub_h
    cv.rect(cx - tub_w // 2 - 1, ty - 1, tub_w + 2, tub_h + 1, OUT)
    cv.rect(cx - tub_w // 2, ty + 3, tub_w, tub_h - 3, STONE_N[3]); cv.vline(cx - tub_w // 2, ty + 3, tub_h - 3, STONE_N[4])
    cv.vline(cx + tub_w // 2 - 1, ty + 3, tub_h - 3, STONE_N[1])
    for k in range(ty + 7, base - 2, 5):
        cv.hline(cx - tub_w // 2 + 1, k, tub_w - 2, STONE_N[2])
    cv.rect(cx - tub_w // 2 - 2, ty, tub_w + 4, 4, LIME[3]); cv.hline(cx - tub_w // 2 - 2, ty, tub_w + 4, LIME[5])
    cv.hline(cx - tub_w // 2 - 2, ty + 3, tub_w + 4, LIME[1])
    cv.rect(cx - 2, ty - 4, 5, 4, "#3a2418")
    rng = _rng(seed)
    from surfaces import LEAVES
    for _ in range(18):
        lx = cx + int(rng.normal(0, tub_w * 0.5)); ly = base - int(rng.integers(-1, 3))
        cv.px(lx, ly, LEAVES[int(rng.integers(len(LEAVES)))])
    return cv, cx, base


def _sleeper_box(cv, x0, x1, top, base, rng):
    """Front face of a timber raised bed: stacked weathered sleepers with bolt heads, a rim."""
    cv.rect(x0 - 1, top - 1, x1 - x0 + 2, base - top + 1, OUT)
    yy = top + 3
    k = 0
    while yy < base:
        hh = min(6, base - yy)
        c = SLEEPER[3] if k % 2 == 0 else SLEEPER[2]
        cv.rect(x0, yy, x1 - x0, hh, c); cv.hline(x0, yy, x1 - x0, shade(c, 0.12)); cv.hline(x0, yy + hh - 1, x1 - x0, SLEEPER[1])
        for _ in range((x1 - x0) // 6):
            cv.hline(x0 + int(rng.integers(0, x1 - x0 - 4)), yy + 2 + int(rng.integers(0, max(1, hh - 3))), int(rng.integers(3, 8)), shade(c, -0.1))
        for bx in (x0 + 3, x1 - 5):
            cv.px(bx, yy + hh // 2, IRON[3])
        yy += hh
        k += 1
    cv.rect(x0 - 1, top, x1 - x0 + 2, 3, SLEEPER[4]); cv.hline(x0 - 1, top, x1 - x0 + 2, shade(SLEEPER[4], 0.15))


def lavender(cv, cx, base, w=14, h=14, seed=0):
    """A lavender clump: grey-green mound with purple spikes standing out of it."""
    rng = _rng(seed)
    cv.paste(shrub(0, 0, w, max(6, h // 2), seed=seed, palette=["#1a2620", "#26362c", "#34483a", "#4a5e4c", "#64785e"]), cx - w // 2, base - h // 2 - 1)
    for _ in range(w // 2 + 3):
        sx = cx + int(rng.integers(-w // 2 + 1, w // 2))
        top = base - h + int(rng.integers(0, 4))
        cv.vline(sx, top + 3, base - h // 2 - top - 2, "#4a5e4c")
        cv.vline(sx, top, 3, LAVENDER[int(rng.integers(1, 4))]); cv.px(sx, top, LAVENDER[3])


def raised_bed(width=190, height=65, seed=0, step=30):
    """The long raised bed of the margin garden: weathered sleepers, lavender, sage and autumn mums,
    grasses at the ends, and one bare patch of raked soil left on purpose with a little slate
    marker - room for an empty space. Its left end is a low stone step to sit on. Prop."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 10, seed=seed)
    ox, base = 4, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.42)
    # low stone step at the left end
    sx0, sx1 = ox, ox + step
    cv.rect(sx0 - 1, base - 13, step + 2, 13, OUT)
    cv.rect(sx0, base - 9, step, 9, STONE_N[3]); cv.hline(sx0, base - 9, step, STONE_N[4]); cv.hline(sx0, base - 1, step, STONE_N[1])
    cv.rect(sx0 - 1, base - 13, step + 2, 4, LIME[3]); cv.hline(sx0 - 1, base - 13, step + 2, LIME[5])
    # the bed
    bx0, bx1 = ox + step + 2, ox + width
    face_top = base - 21
    soil_top = face_top - 9
    cv.rect(bx0, soil_top, bx1 - bx0, face_top - soil_top + 2, "#2a1c18")
    for _ in range(bx1 - bx0):
        cv.px(bx0 + int(rng.integers(0, bx1 - bx0)), soil_top + int(rng.integers(0, face_top - soil_top)), "#3e2a20" if rng.random() < 0.6 else "#1e1412")
    cv.rect(bx0 - 1, soil_top - 3, bx1 - bx0 + 2, 3, SLEEPER[4]); cv.hline(bx0 - 1, soil_top - 3, bx1 - bx0 + 2, shade(SLEEPER[4], 0.15))
    gap0 = bx0 + int((bx1 - bx0) * 0.52)
    gap1 = gap0 + 26
    # raked soil in the gap, a slate marker on a stake
    for gx in range(gap0 + 2, gap1 - 2, 3):
        cv.vline(gx, soil_top + 1, face_top - soil_top - 1, "#4a3428")
    mx = (gap0 + gap1) // 2
    cv.vline(mx, face_top - 12, 10, SLEEPER[3])
    cv.rect(mx - 5, face_top - 18, 11, 7, OUT); cv.rect(mx - 4, face_top - 17, 9, 5, "#3a3a44"); cv.hline(mx - 4, face_top - 17, 9, "#5a5a66")
    cv.hline(mx - 2, face_top - 15, 5, "#c8c0b4")
    # plants, back to front, skipping the gap
    x = bx0 + 2
    while x < bx1 - 8:
        if gap0 - 6 < x < gap1:
            x = gap1 + 1
            continue
        k = rng.random()
        if k < 0.4:
            lavender(cv, x + 7, face_top + 1, w=16, h=int(rng.integers(18, 25)), seed=seed + x)
            x += 12
        elif k < 0.7:
            sw, sh = int(rng.integers(16, 22)), int(rng.integers(14, 20))
            cv.paste(shrub(0, 0, sw, sh, seed=seed + x, flowers=[MUM[int(rng.integers(3))], MUM[3], MUM[(int(rng.integers(3)))]], density=1.2), x - 2, face_top - sh + 3)
            x += sw - 4
        else:
            sw, sh = int(rng.integers(18, 24)), int(rng.integers(16, 24))
            cv.paste(shrub(0, 0, sw, sh, seed=seed + x), x - 2, face_top - sh + 3)
            x += sw - 5
    for gx in (bx0 + 8, bx1 - 9):
        fountain_grass_small(cv, gx, face_top + 1, seed=seed + gx)
    _sleeper_box(cv, bx0, bx1, face_top, base - 1, rng)
    return cv, ox + width // 2, base


def fountain_grass_small(cv, cx, base, seed=0):
    from lib_norlin import fountain_grass
    fountain_grass(cv, cx, base, w=18, h=26, seed=seed)


def feeder_bed(width=80, height=55, seed=0):
    """A small square raised bed with low sedums and thyme, and a bird feeder on a post in the
    middle: a little roofed seed house with a tray, seed spilt on the rim. Prop, bottom-centre."""
    rng = _rng(seed)
    cv = Canvas(width + 8, height + 10, seed=seed)
    ox, base = 4, height + 6
    ground_shadow(cv, ox + width // 2, base, width // 2 + 2, 3, alpha=0.42)
    face_top = base - 15
    soil_top = face_top - 8
    x0, x1 = ox, ox + width
    cx = ox + width // 2
    cv.rect(x0, soil_top, width, face_top - soil_top + 2, "#2a1c18")
    cv.rect(x0 - 1, soil_top - 3, width + 2, 3, SLEEPER[4]); cv.hline(x0 - 1, soil_top - 3, width + 2, shade(SLEEPER[4], 0.15))
    # feeder post and house
    top = base - height + 2
    cv.rect(cx - 1, top + 12, 3, face_top - top - 12, OUT); cv.vline(cx, top + 12, face_top - top - 12, SLEEPER[4])
    cv.rect(cx - 9, top + 12, 19, 3, OUT); cv.rect(cx - 8, top + 12, 17, 2, SLEEPER[4])
    for (sx, c) in ((cx - 7, "#c8a868"), (cx - 4, "#a88850"), (cx + 3, "#c8a868"), (cx + 6, "#e0c080")):
        cv.px(sx, top + 11, c)
    cv.rect(cx - 6, top + 4, 13, 8, OUT); cv.rect(cx - 5, top + 5, 11, 7, "#5a3a2a")
    cv.rect(cx - 3, top + 6, 7, 5, "#c8a868"); cv.hline(cx - 3, top + 6, 7, "#e0c080")
    cv.poly([(cx - 9, top + 5), (cx, top - 2), (cx + 9, top + 5)], OUT)
    cv.poly([(cx - 7, top + 4), (cx, top - 1), (cx + 7, top + 4)], "#6a2e2a")
    cv.line(cx, top - 1, cx + 7, top + 4, "#8a4a3a")
    # a sparrow on the tray
    for (px_, py_, c) in ((cx + 6, top + 9, "#6a4a32"), (cx + 7, top + 9, "#8a6a48"), (cx + 6, top + 10, "#5a3e2a"), (cx + 7, top + 10, "#c8b08a"),
                          (cx + 8, top + 9, "#8a6a48"), (cx + 8, top + 8, "#6a4a32"), (cx + 9, top + 8, "#2a1e18"), (cx + 5, top + 10, "#5a3e2a"),
                          (cx + 4, top + 9, "#4a3222")):
        cv.px(px_, py_, c)
    # low planting
    x = x0 + 2
    while x < x1 - 8:
        if abs(x + 6 - cx) < 5:
            x += 4
            continue
        sw, sh = int(rng.integers(10, 15)), int(rng.integers(6, 10))
        pal = ["#1a2620", "#2a3a2a", "#3e5236", "#5a6e44", "#7a8a52"] if rng.random() < 0.5 else None
        fl = ["#c06a7a", "#d88a9a", "#e8b0b8", "#f0d0d0"] if rng.random() < 0.4 else None
        cv.paste(shrub(0, 0, sw, sh, seed=seed + x, palette=pal or LEAF, flowers=fl), x - 2, face_top - sh + 3)
        x += sw - 3
    _sleeper_box(cv, x0, x1, face_top, base - 1, rng)
    for _ in range(6):
        cv.px(x0 + int(rng.integers(2, width - 2)), soil_top - 2, "#e0c080")
    return cv, cx, base
