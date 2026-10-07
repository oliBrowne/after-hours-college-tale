"""Morning animals for the last Macky rooms (M05-M07), names prefixed mk2_ so they never collide:
mk2_robin (an American robin hopping and pecking on the dewy lawn; rate about 2), mk2_magpie (a
black-billed magpie, Boulder's long-tailed morning bird, flicking its tail; rate about 1.5),
mk2_goose (a Canada goose flying, wings up and down, for a V across the sunrise; rate about 3)."""

ROBIN = [
    [
        "...kk....",
        "..kggk...",
        ".kgegky..",
        ".kgggk...",
        "kgggrrk..",
        "kgggrrrk.",
        ".kggrrk..",
        "..kkkk...",
        "...y.y...",
    ],
    [
        ".........",
        ".........",
        "..kkk....",
        ".kgggkk..",
        "kgggggek.",
        "kgggrrkyy",
        ".kggrrk..",
        "..kkkk...",
        "...y.y...",
    ],
    [
        "...kk....",
        "..kggk...",
        ".kgegky..",
        ".kgggk...",
        "kgggrrk..",
        "kgggrrrk.",
        ".kggrrk..",
        "..kkkk...",
        "..y...y..",
    ],
]
ROBIN = [ROBIN[0], ROBIN[0], ROBIN[1], ROBIN[0], ROBIN[2], ROBIN[0]]   # stand, peck, stand, hop
ROBIN_PAL = {"k": "#1e1a20", "g": "#5a5660", "e": "#f2ead6", "r": "#d06a3a", "y": "#e8b040"}

MAGPIE = [
    [
        "........kk....",
        ".......kbbk...",
        "......kbebk...",
        "......kbbbky..",
        ".kkk.kbwwbk...",
        "kttbkkbwwwbk..",
        ".kttbbbbwwbk..",
        "...kttbbbbk...",
        ".....kkkkk....",
        "......y..y....",
    ],
    [
        "........kk....",
        ".......kbbk...",
        "......kbebk...",
        "......kbbbky..",
        "......kbwwbk..",
        "..kkkkbbwwwbk.",
        "kttttbbbbwwbk.",
        ".kkkttbbbbk...",
        ".....kkkkk....",
        "......y..y....",
    ],
]
MAGPIE_PAL = {"k": "#0e0c12", "b": "#1c1a24", "w": "#f2eee6", "e": "#5a6a8a", "t": "#2a4a5a", "y": "#2a2830"}

GOOSE = [
    [
        "...k.......",
        "..kk.......",
        "kwbbbbbk...",
        ".kkbbbbbbkk",
        "....k......",
    ],
    [
        "...........",
        "...........",
        "kwbbbbbk...",
        ".kkbbbbbbkk",
        "...kbk.....",
        "....k......",
    ][0:5],
]
GOOSE[1] = [
    "...........",
    "...........",
    "kwbbbbbbkk.",
    ".kkbbbbbbbk",
    "...kk......",
]
GOOSE_PAL = {"k": "#1a1820", "b": "#5a4a44", "w": "#e8e2d6"}

KINDS = [
    ("mk2_robin", ROBIN, ROBIN_PAL),
    ("mk2_magpie", MAGPIE, MAGPIE_PAL),
    ("mk2_goose", GOOSE, GOOSE_PAL),
]
