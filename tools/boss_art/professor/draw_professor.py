#!/usr/bin/env python3
"""professor -- route-trainer encounter sprite.  All three batch-C encounter ids (athlete, professor,
advisor_mini) are drawn by ONE script with one engine copy:
/tmp/claude-0/newcast/athlete/draw_encounters_c.py.  This stub draws just this id into ./out
(and ./sheet.png), then packs it with ./build_sheet.py.  Run that script with no argument to redraw all
three plus /tmp/claude-0/newcast/encounters-c-lineup.png."""
import os, runpy, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.argv = [sys.argv[0], "professor"]
runpy.run_path("/tmp/claude-0/newcast/athlete/draw_encounters_c.py", run_name="__main__")
subprocess.run([sys.executable, os.path.join(HERE, "build_sheet.py")], check=True)
