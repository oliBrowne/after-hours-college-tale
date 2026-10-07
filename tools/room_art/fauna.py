"""Hand-placed animal sprites (two or three frames each)."""
import glob
import importlib.util
import os

import numpy as np
from pixel import Canvas, C

PAL = {
    "k": "#24161c", ".": None,
    # fox squirrel
    "d": "#6e3a24", "o": "#a65e36", "l": "#d39554", "w": "#ecc993", "e": "#0b070c", "n": "#7a4a2a", "c": "#3e2a20",
    # cottontail
    "g": "#8a7466", "h": "#b29b88", "m": "#5e4c46", "u": "#efe2cc", "p": "#d08a8e",
    # pigeon
    "b": "#6d7387", "B": "#8f95aa", "v": "#4b4a62", "q": "#5c8a7c", "r": "#80608c", "y": "#e6d6b1", "f": "#c8828a", "i": "#f2d27a",
}

SQUIRREL = [
    [
        "............kkk...",
        "...........kolkk..",
        "..........kooollk.",
        "...kk.....kdooolk.",
        "..kolk.....kdoolk.",
        ".kooook....kdoolk.",
        "kooeoook...kdolk..",
        "kloooooook.kdolk..",
        ".kwwkoooookkdok...",
        "..kwnkooooooddk...",
        "..kwcnkoooooodk...",
        "...kwwoooooodk....",
        "...kwwwooooddk....",
        "....kkkdkkkdkk....",
    ],
    [
        "............kkk...",
        "...........kolkk..",
        "..........kooollk.",
        "..........kdooolk.",
        "...kk......kdoolk.",
        "..kolk.....kdoolk.",
        ".kooook....kdolk..",
        "kooeoook..kkdolk..",
        "klooooooookddok...",
        ".kwwkoooooooddk...",
        "..kwnkooooooodk...",
        "...kcwoooooodk....",
        "...kwwwooooddk....",
        "....kkkdkkkdkk....",
    ],
]

RABBIT = [
    [
        "..kk.kk.......",
        ".khk.khk......",
        ".khk.khk......",
        ".kgk.kgk......",
        ".kgkkkgk......",
        "kggggggk......",
        "kgegggggkk....",
        "pgggggggggk...",
        "kkkggggggggk..",
        "..kgghggggguk.",
        "..kghhgggguuk.",
        "..kgghhgggggk.",
        "...kmgkkkmgk..",
        "....kk...kk...",
    ],
    [
        "..kk.kk.......",
        ".khk.khk......",
        ".khk.khk......",
        ".kgk.kgk......",
        ".kgkkkgk......",
        "kggggggk......",
        "kgmgggggkk....",
        "kpggggggggk...",
        "kkkggggggggk..",
        "..kgghggggguk.",
        "..kghhgggguuk.",
        "..kgghhgggggk.",
        "...kmgkkkmgk..",
        "....kk...kk...",
    ],
]

PIGEON = [
    [
        ".......kk...",
        "......kBBk..",
        "......kBeBy.",
        "......kqrk..",
        ".kkkkkkbqk..",
        "kvbbbBBbbk..",
        "kvvbvvbbbk..",
        ".kvvbbbbk...",
        "..kk.ff.....",
    ],
    [
        "............",
        "............",
        "............",
        ".kkkkkk.....",
        "kvbbbBBkk...",
        "kvvbvvbqrk..",
        "kvvbbbbbBek.",
        ".kvvbbbbkBy.",
        "..kk.ff.....",
    ],
]

BIRD = [
    ["k...k", ".k.k.", "..k.."],
    [".....", "kkkkk", "..k.."],
]


def sprite(rows, pal=PAL):
    h, w = len(rows), len(rows[0])
    cv = Canvas(w, h)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            c = pal.get(ch)
            if c:
                cv.px(x, y, c)
    return cv


def strip(frames, pal=PAL):
    sprites = [sprite(f, pal) for f in frames]
    w, h = sprites[0].w, sprites[0].h
    out = Canvas(w * len(sprites), h)
    for i, s in enumerate(sprites):
        out.paste(s, i * w, 0)
    return out


def fauna_sheet():
    """One sheet; returns (Canvas, regions) where regions maps name -> [x, y, w, h, frames]."""
    parts = [("squirrel", SQUIRREL, PAL), ("rabbit", RABBIT, PAL), ("pigeon", PIGEON, PAL), ("bird", BIRD, PAL)]
    # More animals come from fauna_extra_*.py beside this file: KINDS = [(name, frames, palette), ...],
    # frames being lists of equal-size row strings, palette mapping characters to hex colours.
    here = os.path.dirname(os.path.abspath(__file__))
    for path in sorted(glob.glob(os.path.join(here, "fauna_extra_*.py"))):
        spec = importlib.util.spec_from_file_location(os.path.basename(path)[:-3], path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        parts += [(name, frames, {".": None, **pal}) for name, frames, pal in module.KINDS]
    strips = [(name, strip(frames, pal), len(frames)) for name, frames, pal in parts]
    W = max(s.w for _, s, _ in strips)
    H = sum(s.h + 1 for _, s, _ in strips)
    sheet = Canvas(W, H)
    regions = {}
    y = 0
    for name, s, n in strips:
        sheet.paste(s, 0, y)
        regions[name] = [0, y, s.w // n, s.h, n]
        y += s.h + 1
    return sheet, regions
