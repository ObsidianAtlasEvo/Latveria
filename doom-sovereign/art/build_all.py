#!/usr/bin/env python3
"""Regenerates every art/audio/UI asset and document, then runs the pipeline tests.

    python3 art/build_all.py          (from doom-sovereign/)

Order matters: audio and VFX first so the animation validator can check sound and particle ids.
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STEPS = ["build_armor.py", "build_mask.py", "build_doombot.py", "build_audio.py", "build_vfx.py", "build_ui.py",
         "build_lang.py", "build_anims.py", "build_docs.py"]

for s in STEPS:
    print("==", s)
    r = subprocess.run([sys.executable, os.path.join(HERE, s)], cwd=HERE)
    if r.returncode:
        sys.exit("%s failed" % s)
r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", os.path.join(HERE, "tests")], cwd=os.path.dirname(HERE))
sys.exit(r.returncode)
