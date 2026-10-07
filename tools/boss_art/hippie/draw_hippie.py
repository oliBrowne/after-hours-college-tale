#!/usr/bin/env python3
"""Draw the 'hippie' random-encounter trainer for "After Hours - College Tale".

All four batch-A encounter ids (cyclist, runner, hippie, drummer) share ONE drawing module,
/tmp/claude-0/newcast/cyclist/encounters_a.py (engine copied once from Sunbeam / Professor Eric,
one rig, one class per trainer).  This wrapper builds just this id into ./out and ./sheet.png;
run encounters_a.py with no arguments to rebuild all four plus the lineup sheet.
"""
import os
import sys

sys.path.insert(0, "/tmp/claude-0/newcast/cyclist")
import encounters_a  # noqa: E402

if __name__ == "__main__":
    cells, feet, meta, idle = encounters_a.build("hippie")
    print("hippie", "battle", meta["battle_height"], "world", meta["world_height"])
