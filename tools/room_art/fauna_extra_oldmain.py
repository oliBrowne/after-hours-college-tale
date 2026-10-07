"""Old Main animals: a folded paper crane drifting over the courtyard (Rook's folded-paper kin)
and a sleeping pigeon tucked on a window ledge."""

CRANE = [
    [
        "..........",
        "k........k",
        "wk......kw",
        "pwk....kwp",
        ".pwkkkkwp.",
        "..kwwwwk.k",
        "...kpppkkw",
        "....kk....",
    ],
    [
        "..........",
        "..........",
        "..........",
        "kk......kk",
        "wwkkkkkkww",
        ".ppwwwwk.k",
        "...kpppkkw",
        "....kk....",
    ],
    [
        "..........",
        "..........",
        "..........",
        "..........",
        "..kkkkkk..",
        ".kpwwwwkkk",
        "kwppppkkkw",
        "wp..kk....",
    ],
]
CRANE_PAL = {"k": "#3a3448", "w": "#f2ead6", "p": "#c8bca4"}

ROOST = [
    [
        "...kkkk...",
        "..kBBBBk..",
        ".kBeBBBBk.",
        "kyBBbbbBBk",
        ".kBbvvbbBk",
        "..kvvvvvk.",
        "...kkkkk..",
    ],
    [
        "...kkkk...",
        "..kBBBBk..",
        ".kBkBBBBk.",
        "kyBBbbbBBk",
        ".kBbvvbbBk",
        "..kvvvvvk.",
        "...kkkkk..",
    ],
]
ROOST_PAL = {"k": "#24161c", "B": "#8f95aa", "b": "#6d7387", "v": "#4b4a62", "e": "#0b070c", "y": "#e6d6b1"}

KINDS = [
    ("om_crane", CRANE, CRANE_PAL),
    ("om_roost", ROOST, ROOST_PAL),
]
