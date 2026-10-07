"""Macky's animals and drifting things for the shared fauna sheet (names prefixed macky_):
macky_sparrow (a house sparrow puffed up against the cold, bobbing and pecking; the birds waiting for
morning on the procession walk), macky_ticket (a coat-check ticket tumbling through the air; use
"fly"), macky_note (a quaver drifting up out of the orchestra pit; use "fly")."""

SPARROW = [
    [
        "....kkk...",
        "...kgggk..",
        "..ykeggbk.",
        "...kwbbdbk",
        "...kwwbbdk",
        "....kwwbk.",
        ".....k.k..",
    ],
    [
        "....kkk...",
        "...kgggk..",
        "..ykeggbk.",
        "...kwbbdbk",
        "...kwwbbdk",
        "....kwwbk.",
        ".....k.k..",
    ],
    [
        "..........",
        "....kkkk..",
        "...kgggbdk",
        "..kegbbbbk",
        ".ykkwwbbdk",
        "....kwwbk.",
        ".....k.k..",
    ],
]
SPARROW_PAL = {"k": "#2a1c18", "g": "#7a6a62", "b": "#8a5a3a", "d": "#5a3a26", "w": "#d8c8a8", "e": "#0c0808", "y": "#c8a050"}

TICKET = [
    [
        "........",
        ".kkkkkk.",
        ".kpppck.",
        ".kpllck.",
        ".kkkkkk.",
        "........",
    ],
    [
        "....kk..",
        "..kkpk..",
        ".kppck..",
        ".kplck..",
        ".kkkk...",
        "........",
    ],
    [
        "........",
        "........",
        "kkkkkkkk",
        "kpllpcck",
        "kkkkkkkk",
        "........",
    ],
]
TICKET_PAL = {"k": "#6a5a50", "p": "#efe4cc", "l": "#a89a86", "c": "#c84a3c"}

NOTE = [
    [
        "...kk",
        "...kgk",
        "...k..",
        "...k..",
        ".kkk..",
        "kgkk..",
        ".kk...",
    ],
    [
        "...kk.",
        "...kk.",
        "...kgk",
        "...k..",
        ".kkk..",
        "kgkk..",
        ".kk...",
    ],
]
NOTE = [[row.ljust(6, ".") for row in frame] for frame in NOTE]
NOTE_PAL = {"k": "#e8c070", "g": "#fff0c4"}

KINDS = [
    ("macky_sparrow", SPARROW, SPARROW_PAL),
    ("macky_ticket", TICKET, TICKET_PAL),
    ("macky_note", NOTE, NOTE_PAL),
]
