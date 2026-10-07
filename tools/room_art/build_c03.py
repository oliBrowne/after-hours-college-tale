"""Career Center (C03), off the Fountain Court, walk-in hours running late on career fair night.
Back wall, left to right: the advising corner (a tall window with the blinds half down over campus
and the Flatirons at night, a diploma, a Flatirons photo, an ADVISING plate); the navy accent wall
with raised CAREER CENTER letters under three spot cans, the JOBS board (postings with tear-off
tabs, a red HIRING card), the events screen running its slideshow, the brochure rack (one pocket
empty: WHAT NOW?), a walnut slat band; the career fair corner (a CAREER FAIR fabric banner, two
roll-up banners for the fictional recruiters PEAKLINE and FLATIRON DATA, a clock). Blue-grey carpet
tile, cool pools under the LED panels, a WELCOME mat inside the open glass doors at the bottom edge
(back out to the court).
Props: the advisor's desk and two guest chairs, the LinkedOut kiosk, the PEAKLINE fair table, the
waiting chairs (rest and save), a water cooler, a RESUME REVIEW chalkboard, two snake plants."""
import paths
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pixel import Canvas, C, text, text_width
from surfaces import light_pool
from lib_eng import wall_clock, outlet, micro_text, micro_width
from lib_umc import soft_ellipse
import c02_lib as S
import c03_lib as L

ROOM = "C03"
W, H = 800, 480
BASE = 150
ACCENT = (228, 572)              # the navy feature wall
PANELS = ((130, 40), (400, 44), (660, 40))
TV = (380, 58, 84, 46)           # the events screen (x, y, w, h)
DOOR_X, DOOR_TOP = 400, 448


def build(project):
    out = os.path.join(project, f"assets/art/rooms/{ROOM}")
    os.makedirs(out, exist_ok=True)
    res = f"res://assets/art/rooms/{ROOM}/"
    bg = Canvas(W, H, fill="#171a2b", seed=31)

    # --- back wall
    L.office_wall(bg, 0, 12, W, BASE - 12, seed=4)
    L.accent_wall(bg, ACCENT[0], 12, ACCENT[1] - ACCENT[0], BASE - 12, seed=5)
    L.office_ceiling(bg, 0, W, h=12, panels=PANELS)
    # advising corner
    L.blinds_window(bg, 40, 36, 70, 72, seed=6, raised=0.35)
    s = "ADVISING"
    bg.rect(130, 24, micro_width(s) + 8, 10, L.NAVY[2]); micro_text(bg, s, 134, 27, "#f2ecdc")
    L.diploma(bg, 130, 46, 26, 20)
    L.diploma(bg, 162, 46, 26, 20)
    L.framed_photo(bg, 144, 74, 24, 16)
    outlet(bg, 30, 132); outlet(bg, 214, 132)
    # the accent wall: letters, jobs board, screen, brochures
    L.raised_letters(bg, "CAREER CENTER", 400, 24)
    L.job_board(bg, 252, 54, 104, 64, seed=7)
    L.wall_tv(bg, *TV)
    L.brochure_rack(bg, 488, 50, cols=3, rows=3, seed=8)
    # career fair corner
    L.fabric_banner(bg, 598, 722, 20, "CAREER FAIR")
    L.popup_banner(bg, 604, BASE, 42, 102, "PEAKLINE", lines=(("WE'RE", L.PEAK[1]), ("HIRING", L.PEAK[2])), pal=L.PEAK)
    L.popup_banner(bg, 716, BASE, 42, 102, "FLATIRON", lines=(("DATA", L.NAVY[3]), ("INTERNS", L.NAVY[2]), ("WANTED", L.NAVY[2])),
                   pal=[L.NAVY[1], L.NAVY[2], L.NAVY[4], "#8ac0f4", "#c8d8f0"])
    wall_clock(bg, 660, 52, r=7)
    outlet(bg, 580, 132); outlet(bg, 770, 132)

    # --- floor
    L.office_carpet(bg, 0, BASE, W, H - BASE, seed=9)
    S.wall_shadow(bg, 0, BASE, W)
    S.entry_mat(bg, DOOR_X, 392, w=84, h=22, label="WELCOME")
    for cx, cy, rx, ry, c, a in [(130, 214, 90, 30, "#e8eeff", 0.16), (400, 236, 100, 34, "#e8eeff", 0.13),
                                 (660, 228, 90, 30, "#e8eeff", 0.16), (400, 360, 160, 50, "#f6cf7a", 0.08),
                                 (640, 420, 80, 24, "#f6cf7a", 0.12)]:
        light_pool(bg, cx, cy, rx, ry, color=c, strength=a)
    soft_ellipse(bg, 420, 160, 60, 8, "#8ac0f4", 0.05)                      # the screen's glow on the carpet
    # flat things on the floor: a dropped lanyard, a business card, a paper cone cup
    bg.line(520, 330, 532, 334, S.GOLD[3]); bg.line(532, 334, 538, 330, S.GOLD[3]); bg.rect(537, 330, 4, 5, "#f2ecdc")
    bg.rect(300, 372, 7, 4, "#f2f6f6"); bg.hline(301, 373, 4, L.PEAK[2])
    bg.rect(318, 214, 3, 2, "#f2f6f6")
    # the FREE HEADSHOTS corner: a tape X on the carpet in front of the ring light
    for k in range(-4, 5):
        bg.px(132 + k, 404 + k, C("#e8b45c", 0.9)); bg.px(132 + k, 404 - k, C("#e8b45c", 0.9))
    s_ = "FREE HEADSHOTS"
    micro_text(bg, s_, 132 - micro_width(s_) // 2, 414, C("#e8b45c", 0.85))
    # margins and the glass front with its open doors
    for x0, w in [(0, 12), (W - 12, 12)]:
        bg.rect(x0, BASE, w, H - BASE, C(S.SHADOW, 0.35))
    S.storefront(bg, 460, W, DOOR_X, door_w=64)
    S.doorway_gap(bg, DOOR_X, DOOR_TOP, H, w=64)
    bg.save(os.path.join(out, "background.png"))

    # --- props
    props = {}

    def save(index, made, extra=None):
        sprite, ax, ay = made[:3]
        name = f"prop-{index}.png"
        sprite.save(os.path.join(out, name))
        entry = {"texture": res + name, "anchor": [ax, ay]}
        entry.update(extra or {})
        props[str(index)] = entry

    save(1, L.advisor_desk(132, 52, seed=1))
    save(2, L.guest_chair(28, 34, seed=2))
    save(3, L.guest_chair(28, 34, seed=3))
    save(4, L.linkedout_kiosk(42, 78, seed=4))
    save(5, L.fair_table(154, 46, seed=5))
    save(6, L.beam_seats(98, 36, seed=6))
    save(7, L.snake_plant(36, 58, seed=7))
    save(8, L.water_cooler(22, 50, seed=8))
    save(9, S.chalk_aframe(50, 48, header="RESUME", lines=(("REVIEW", "#f2ecdc"), ("WALK-INS", "#8ac0f4")), arrow=False,
                           board="#1a2034", head_bg=L.NAVY[3], head_ink="#f2ecdc", seed=9))
    save(10, L.snake_plant(36, 58, seed=10))
    save(14, L.ring_light(30, 64, seed=14))
    save(15, L.cocktail_table(34, 52, seed=15))

    # --- animated layers: the events screen's slideshow, the clock's second hand, dust in the light
    layers = []
    x, y, w, h = TV
    for k, slide in enumerate(L.tv_slides(w, h)):
        name = f"slide-{k}.png"
        slide.save(os.path.join(out, name))
        layers.append({"kind": "blink", "pattern": "".join("1" if j == k else "0" for j in range(3)), "rate": 0.4,
                       "texture": res + name, "x": x, "y": y})
    layers += [
        {"kind": "blink", "pattern": "10", "rate": 1.0, "rects": [[660, 46, 1, 6, "c03a32", 0.9]]},
        {"kind": "particles", "style": "dust", "count": 10, "rect": [300, 20, 200, 120], "speed": [1, 3], "color": "e8eeff"},
    ]
    manifest = {
        "background": res + "background.png",
        "width": W,
        "occluders": [],
        "props": props,
        "label_only": [11, 12, 13],
        "fauna": [],
        "leaves": [],
        "layers": layers,
    }
    with open(os.path.join(out, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else paths.PROJECT)
