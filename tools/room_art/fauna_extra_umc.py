"""Extra animals for the UMC interior rooms: a pale moth that circles the work lamps (atrium, repair
landing) and the shelf light in lost property, where the coats are wool."""

MOTH_PAL = {"w": "#d8ccb0", "W": "#f6eedc", "b": "#6a5040", "k": "#3a2c28"}

MOTH = [
    [
        ".......",
        "ww...ww",
        "wWwbwWw",
        ".wwbww.",
        "..wbw..",
        "...k...",
    ],
    [
        "..w.w..",
        "..wbw..",
        ".wWbWw.",
        "..wbw..",
        "...b...",
        ".......",
    ],
]

KINDS = [("umc_moth", MOTH, MOTH_PAL)]
