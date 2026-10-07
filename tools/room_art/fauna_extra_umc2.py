"""Extra animal for the Connection (U06): a small grey mouse that works the baseboard under the shoe
cubbies after closing, nose down, tail out behind."""

MOUSE_PAL = {"g": "#8a8090", "G": "#b0a8b4", "d": "#4a4250", "p": "#e0a0a8", "k": "#1a1420"}

MOUSE = [
    [
        "...........",
        "......pg...",
        "pp..ggGgg..",
        ".ppgggggGgk",
        "...gggggg..",
        "....d..d...",
    ],
    [
        "...........",
        "......pg...",
        ".pp.ggGgg..",
        "..pgggggGgk",
        "...gggggg..",
        "...d...d...",
    ],
]

KINDS = [("umc2_mouse", MOUSE, MOUSE_PAL)]
