#!/usr/bin/env python3
"""philosophy_major -- route-trainer encounter sprite.  All four batch-B encounter ids (business_major, engineering_major,
philosophy_major, frisbee) are drawn by ONE script with one engine copy:
/tmp/claude-0/newcast/business_major/draw_encounters_b.py.  This stub draws just this id into ./out
(and ./sheet.png), then packs it with ./build_sheet.py.  Run that script with no argument to redraw all
four plus /tmp/claude-0/newcast/encounters-b-lineup.png."""
import os, runpy, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "philosophy_major"]
runpy.run_path("/tmp/claude-0/newcast/business_major/draw_encounters_b.py", run_name="__main__")
subprocess.run([sys.executable, os.path.join(HERE, "build_sheet.py")], check=True)
