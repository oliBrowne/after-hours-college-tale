# Room art generators

These Python scripts paint every room in `assets/art/rooms/<ID>/` (background, props, overlays,
animated layers and the room's own battle backdrop) and write its `manifest.json`. The game reads
the manifests through `scenes/room_art.gd` and `scenes/battle_backdrop.gd`; a room without a
manifest falls back to the old procedural drawing.

Needs Python 3.10+ with numpy and Pillow. Godot ignores this folder (`.gdignore`).

```
cd tools/room_art
python3 build_all.py            # shared animal sheet + all 36 rooms (about 4 minutes)
python3 build_all.py N04 M07    # just these rooms
python3 preview.py room U06 out.png pinpal_resolution=forceful
python3 preview.py battle M01 out.png dawn
```

The project folder is found automatically (two levels up); set `AH_PROJECT` to point elsewhere.
Rebuilding is deterministic: the scripts reproduce the committed PNGs byte for byte, so a rebuild
that changes files means a script changed. Open Godot afterwards so it imports new images.

Layout:
- `build_<id>.py` paints a room and returns its manifest; `build_battle_<id>.py` paints its battle
  backdrop and returns the manifest's `battle` section.
- `lib_<group>.py` holds helpers per building (umc, farrand, norlin, eng, oldmain, macky), and
  `fauna_extra_<group>.py` adds animals to the shared sheet `fauna.py` builds.
- Shared modules: `pixel.py`, `midlib.py`, `surfaces.py`, `props.py`, `sky.py`, `clouds.py`,
  `facade.py`, `interior.py`, `persp.py` (the one-point battle perspective).
- `PAINTING_GUIDE.md` is the full spec: style rules, manifest format, state visuals, battle layers.
  `ref/` and `rooms_now/` are the reference images it points to.
