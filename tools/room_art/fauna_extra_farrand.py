"""Night animals for the Farrand Field festival rooms: moths around the lamps, bats over the
field, a red fox trotting along the lawn edge. Loaded by fauna.fauna_sheet()."""

_PAL = {
    "k": "#24161c",
    # moth: pale dusty wings
    "m": "#d8ccb4", "M": "#f0e6d0", "n": "#9a8c78",
    # bat
    "b": "#3a2e3e", "B": "#54445a", "e": "#e8b45c",
    # fox
    "r": "#b8582a", "R": "#d87a3a", "o": "#8a3e22", "w": "#efe2cc", "d": "#2a1a18", "E": "#0b070c",
    # raccoon
    "a": "#6a6672", "A": "#9a96a2", "z": "#2e2b34", "W": "#e2ded6",
}

MOTH = [
    [
        "k...k",
        "MmkmM",
        ".mnm.",
        "..k..",
    ],
    [
        ".....",
        ".kkk.",
        "MmnmM",
        "..k..",
    ],
]

BAT = [
    [
        "bb.....bb",
        ".bBb.bBb.",
        "..bbebb..",
        "...bbb...",
        "....b....",
    ],
    [
        ".........",
        "...b.b...",
        ".bbbebbb.",
        "bB.bbb.Bb",
        "b...b...b",
    ],
]

FOX = [
    [
        "..........kk.k..",
        ".........kRRkRk.",
        "kkk......kRRRRRk",
        "kRRk.....kRERRwk",
        ".krRk...krRRRwwd",
        "..krRkkkrRRRwwk.",
        "...krrrrrRRRRk..",
        "...kwrrrrrrRRk..",
        "..kwwkorrrrorrk.",
        "..kwk.kok.kok.k.",
        "..kk..kdk..kdk..",
    ],
    [
        "..........kk.k..",
        ".........kRRkRk.",
        ".........kRRRRRk",
        "kkk......kRERRwk",
        "kRRk....krRRRwwd",
        ".krRkkkkrRRRwwk.",
        "..krrrrrrRRRRk..",
        "...kwrrrrrrRRk..",
        "..kwwkorrrrorrk.",
        "..kwk..kokok..k.",
        "..kk...kdkdk....",
    ],
]

RACCOON = [
    [
        "............kk..kk.",
        ".....kkkkkk.kAkkAk.",
        "....kaAAAAAkkAAAAAk",
        "kk.kaaaaaaaaAWWWWWk",
        "kAzkaaaaaaaazzEzzWk",
        "kzAzaaaaaaaaaAWWWkk",
        ".kzAzaaaaaaaaaAkk..",
        "..kkzaaaazaaaaak...",
        "....kzak.kzak.kz...",
        "....kzk..kzk..kzk..",
        "....kk...kk...kk...",
    ],
    [
        "............kk..kk.",
        ".....kkkkkk.kAkkAk.",
        "....kaAAAAAkkAAAAAk",
        "kk.kaaaaaaaaAWWWWWk",
        "kAzkaaaaaaaazzEzzWk",
        "kzAzaaaaaaaaaAWWWkk",
        ".kzAzaaaaaaaaaAkk..",
        "..kkzaaaazaaaaak...",
        "....kzakkzak.kzak..",
        "...kzk..kzk...kzk..",
        "...kk...kk....kk...",
    ],
]

KINDS = [
    ("moth", MOTH, _PAL),
    ("bat", BAT, _PAL),
    ("fox", FOX, _PAL),
    ("raccoon", RACCOON, _PAL),
]
