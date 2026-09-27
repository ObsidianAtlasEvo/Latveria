#!/usr/bin/env python3
"""Render light-level maps (before/after the lighting overhaul) of key floors.

    python lightmap.py    -> ../docs/light_*.png   (needs numpy, pillow)
"""
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sim

WIN = os.path.join(HERE, "..", "windows")
OUT = os.path.join(HERE, "..", "docs")
BASE = ["latveria_commands.txt", "latveria_expansion_commands.txt"]
FLOORS = [("keep_dungeon", 3, (-30, -196, 30, -150)), ("keep_ground", 13, (-30, -196, 30, -150)),
          ("keep_second", 29, (-30, -196, 30, -150)), ("keep_third", 39, (-30, -196, 30, -150)),
          ("cistern", -20, (-26, 28, 26, 70))]


def ramp(v):
    v = np.clip(v, 0, 15) / 15.0
    return np.stack([40 + 215 * v, 20 + 200 * v ** 1.3, 30 + 120 * v ** 3], axis=-1)


def render(files, tag):
    w = sim.World()
    for f in files:
        w.load_file(os.path.join(WIN, f))
    emit, opaque, _, _ = w._class_luts()
    imgs = []
    for name, y, (x1, z1, x2, z2) in FLOORS:
        L, sub, (ox, oy, oz) = w.block_light((x1, y, z1, x2, y, z2))
        sl = L[x1 - ox:x2 - ox + 1, y - oy, z1 - oz:z2 - oz + 1]
        op = opaque[sub][x1 - ox:x2 - ox + 1, y - oy, z1 - oz:z2 - oz + 1]
        rgb = ramp(sl.astype(float))
        rgb[op] = (70, 70, 80)
        im = Image.fromarray(rgb.astype(np.uint8).transpose(1, 0, 2)).resize(((x2 - x1 + 1) * 8, (z2 - z1 + 1) * 8), Image.NEAREST)
        imgs.append((name, im))
    return imgs


def main():
    before = render(BASE, "before")
    after = render(BASE + ["latveria_lighting_commands.txt"], "after")
    os.makedirs(OUT, exist_ok=True)
    for (name, a), (_, b) in zip(before, after):
        W_, H = a.size
        canvas = Image.new("RGB", (W_ * 2 + 24, H + 30), (20, 20, 24))
        canvas.paste(a, (0, 30))
        canvas.paste(b, (W_ + 24, 30))
        d = ImageDraw.Draw(canvas)
        d.text((6, 8), "BEFORE  (%s)" % name.replace("_", " "), fill=(230, 230, 230))
        d.text((W_ + 30, 8), "AFTER lighting overhaul", fill=(230, 230, 230))
        canvas.save(os.path.join(OUT, "light_%s.png" % name))
    print("wrote light maps to", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
