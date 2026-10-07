"""Norlin's night animals for the shared fauna sheet (names prefixed so other groups can add their own):
library_cat (asleep on a window sill, breathing / tail flick), barn_owl (perched, blinks now and then; rate about 1.5), night_bat
(flies), lamp_moth (flutters at a lamp), loose_page (a sheet of paper tumbling through the air, for
the quad and the garden)."""

OWL = [
    [
        "..k.....k..",
        ".kok...kok.",
        ".koookoook.",
        "kowwkokwwok",
        "kowekoweook"[0:11],
        "kowwkykwwok",
        ".koooboook.",
        ".kobobobok.",
        ".koboboook.",
        "..kobobok..",
        "..kooooook."[0:11],
        "...kyk.kyk.",
    ],
    [
        "..k.....k..",
        ".kok...kok.",
        ".koookoook.",
        "kooookooook",
        "kowwkokwwok",
        "kooookyoook",
        ".koooboook.",
        ".kobobobok.",
        ".koboboook.",
        "..kobobok..",
        "..kooooook."[0:11],
        "...kyk.kyk.",
    ],
]
OWL = [OWL[0], OWL[0], OWL[0], OWL[1]]      # mostly awake: three open frames, then a blink
OWL_PAL = {"k": "#1a1418", "o": "#8a6a4e", "w": "#e6d6b1", "e": "#1a1418", "b": "#c8a884", "y": "#d9a441"}

BAT = [
    [
        "k.......k",
        "kk.....kk",
        "kkk.k.kkk",
        ".kkkkkkk.",
        "...kek...",
        "....k....",
    ],
    [
        ".........",
        ".........",
        "...k.k...",
        "kkkkkkkkk",
        "k..kek..k",
        "....k....",
    ],
    [
        ".........",
        "...k.k...",
        "..kkkkk..",
        ".kkkekkk.",
        "kk..k..kk",
        "k.......k",
    ],
]
BAT_PAL = {"k": "#1c1624", "e": "#5a4a6a"}

MOTH = [
    [
        "w...w",
        "ww.ww",
        ".wbw.",
        "..b..",
    ],
    [
        ".....",
        "w.b.w",
        "wwbww",
        ".....",
    ],
]
MOTH_PAL = {"w": "#efe2c4", "b": "#8a7a68"}

PAGE = [
    [
        "kkkkkkk.",
        "kpppppk.",
        "kplllpk.",
        "kpppppk.",
        "kpllppk.",
        "kkkkkkk.",
    ],
    [
        "........",
        ".kkkkkk.",
        "kpppppk.",
        "kplllpkk",
        "kkkkkkk.",
        "........",
    ],
    [
        "..kkkk..",
        ".kppppk.",
        ".kpllpk.",
        ".kppppk.",
        ".kpllpk.",
        "..kkkk..",
    ],
]
PAGE_PAL = {"k": "#8a7a68", "p": "#f6ecd2", "l": "#a89a86"}

CAT = [
    [
        "..........k.k...",
        ".........kgkgk..",
        ".........kgggk..",
        "....kkkkkkgegk..",
        "...kgggggggggk..",
        "..kgggwggggggk..",
        "..kggggggggwk...",
        "k.kgggggggggk...",
        "kkggggggggggk...",
        ".kkkkkkkkkkk....",
    ],
    [
        "..........k.k...",
        ".........kgkgk..",
        ".........kgggk..",
        "....kkkkkkgggk..",
        "...kgggggggggk..",
        "..kgggwggggggk..",
        "k.kggggggggwk...",
        "kkkgggggggggk...",
        ".kggggggggggk...",
        ".kkkkkkkkkkk....",
    ],
]
CAT_PAL = {"k": "#2a1810", "g": "#c47a3e", "w": "#ecc08a", "e": "#3a5a2a"}   # a ginger library cat

KINDS = [
    ("library_cat", CAT, CAT_PAL),
    ("barn_owl", OWL, OWL_PAL),
    ("night_bat", BAT, BAT_PAL),
    ("lamp_moth", MOTH, MOTH_PAL),
    ("loose_page", PAGE, PAGE_PAL),
]
