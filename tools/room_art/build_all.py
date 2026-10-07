"""Regenerate painted rooms: python3 build_all.py [godot project] [ROOM ...].

Each painted room has build_<id>.py, whose build(project) paints assets/art/rooms/<ID>/ and returns
the room manifest, and usually build_battle_<id>.py, whose build(project) paints the battle images
and returns the manifest's "battle" section. This merges the two and writes manifest.json.
With no room ids it rebuilds the shared fauna sheet and every room that has a build script.
"""
import paths
import importlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from fauna import fauna_sheet

ROOMS = ["U01", "U02", "U03", "U04", "U05", "U06", "U07",
         "F01", "F02", "F03", "F04", "F05", "F06",
         "N01", "N02", "N03", "N04", "N05", "N06", "N07",
         "E01", "E02", "E03", "E04", "E05",
         "O01", "O02", "O03", "O04",
         "M01", "M02", "M03", "M04", "M05", "M06", "M07"]


def build_fauna(project):
    root = os.path.join(project, "assets/art/rooms")
    os.makedirs(root, exist_ok=True)
    sheet, regions = fauna_sheet()
    sheet.save(os.path.join(root, "fauna.png"))
    with open(os.path.join(root, "fauna.json"), "w") as f:
        json.dump(regions, f, indent=1)


def build_room(project, room):
    """Paint one room and its battle backdrop; returns the manifest, or None without a build script."""
    lower = room.lower()
    if not os.path.exists(os.path.join(HERE, f"build_{lower}.py")):
        return None
    manifest = importlib.import_module(f"build_{lower}").build(project)
    if os.path.exists(os.path.join(HERE, f"build_battle_{lower}.py")):
        manifest["battle"] = importlib.import_module(f"build_battle_{lower}").build(project)
    with open(os.path.join(project, f"assets/art/rooms/{room}/manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    return manifest


def main(project, rooms):
    if not rooms:
        build_fauna(project)
    for room in rooms or ROOMS:
        if build_room(project, room) is not None:
            print("built", room)


if __name__ == "__main__":
    args = sys.argv[1:]
    project = args.pop(0) if args and os.path.isdir(args[0]) else paths.PROJECT
    main(project, [a.upper() for a in args])
