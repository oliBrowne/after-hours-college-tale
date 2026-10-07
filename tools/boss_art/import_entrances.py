#!/usr/bin/env python3
"""Copy loose entrance poses (from a newcast/entrances* folder) into tools/boss_art/entrances/ under the
game's boss ids, merging entrances.json, then bake them. Usage: import_entrances.py SRC_DIR [old=new ...]"""
import json, os, shutil, subprocess, sys
here = os.path.dirname(__file__); dst = os.path.join(here, "entrances"); os.makedirs(dst, exist_ok=True)
src = sys.argv[1]; rename = dict(a.split("=") for a in sys.argv[2:])
meta_path = os.path.join(dst, "entrances.json")
meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
for old, m in json.load(open(os.path.join(src, "entrances.json"))).items():
    new = rename.get(old, old)
    shutil.copy(os.path.join(src, old + "-entrance.png"), os.path.join(dst, new + "-entrance.png"))
    meta[new] = m
json.dump(meta, open(meta_path, "w"), indent=1)
subprocess.check_call([sys.executable, os.path.join(here, "bake_entrance.py")] + list(rename.values()) + [k for k in meta if k not in rename.values()])
