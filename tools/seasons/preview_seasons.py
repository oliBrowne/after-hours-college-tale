"""Preview sheets for the season pass (no Godot needed).

    python3 preview_seasons.py sheet <ROOM> <out.png>            the room in all four looks, dusk tint
    python3 preview_seasons.py room <ROOM> <season> <out.png> [scale] [x y w h]
    python3 preview_seasons.py battle <ROOM> <season> <out.png>
    python3 preview_seasons.py overview <out.png> ROOM ROOM ...  rooms in winter, 2 columns
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "room_art"))
import numpy as np
from PIL import Image, ImageDraw
import preview

LOOKS = ["", "fall", "winter", "spring"]


def room(r, season, dawn=False):
    img = preview.compose(r, flags={"season": season, "dawn_started": dawn}, markers=False)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)[..., :3]


def label(img, text):
    im = Image.fromarray(img)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 8 * len(text) + 8, 14], fill=(16, 16, 28))
    d.text((4, 2), text, fill=(240, 230, 200))
    return np.array(im)


def sheet(r):
    tiles = [label(room(r, s), f"{r} {s or 'as painted (early autumn)'}") for s in LOOKS]
    h, w = tiles[0].shape[:2]
    out = np.zeros((h * 2 + 4, w * 2 + 4, 3), np.uint8)
    for i, t in enumerate(tiles):
        y, x = (i // 2) * (h + 4), (i % 2) * (w + 4)
        out[y:y + h, x:x + w] = t
    return out


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "sheet":
        Image.fromarray(sheet(sys.argv[2])).save(sys.argv[3])
    elif mode == "room":
        img = room(sys.argv[2], "" if sys.argv[3] == "-" else sys.argv[3])
        scale = int(sys.argv[5]) if len(sys.argv) > 5 else 1
        if len(sys.argv) > 9:
            x, y, w, h = map(int, sys.argv[6:10])
            img = img[y:y + h, x:x + w]
        Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), 0).save(sys.argv[4])
    elif mode == "battle":
        img = preview.battle(sys.argv[2], season="" if sys.argv[3] == "-" else sys.argv[3])
        Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)[..., :3]).save(sys.argv[4])
    elif mode == "overview":
        rooms = sys.argv[3:]
        tiles = []
        for r in rooms:
            img = room(r, "winter")
            # one 640x360 view per room, centred horizontally, from the top
            h, w = img.shape[:2]
            x0 = max(0, (w - 640) // 2)
            tiles.append(label(np.ascontiguousarray(img[0:360, x0:x0 + 640]), f"{r} winter"))
        cols = 2
        rows = (len(tiles) + cols - 1) // cols
        out = np.zeros((rows * 364, cols * 644, 3), np.uint8)
        for i, t in enumerate(tiles):
            y, x = (i // cols) * 364, (i % cols) * 644
            out[y:y + t.shape[0], x:x + t.shape[1]] = t
        Image.fromarray(out).save(sys.argv[2])
