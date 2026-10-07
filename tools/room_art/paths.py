"""Where the Godot project is: $AH_PROJECT, else the folder two levels up (tools/room_art -> project)."""
import os

PROJECT = os.environ.get("AH_PROJECT") or os.path.abspath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
