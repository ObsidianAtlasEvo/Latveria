#!/usr/bin/env python3
"""Builds the Standard Doombot: geometry, textures (base, 2 damage states, glow masks), previews."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from doomart import doombot as DB
from doomart import render as R
from doomart.pipeline import paint_states, prepare
from build_armor import ASSETS, PREVIEW

GEO_DIR = os.path.join(ASSETS, "geckolib", "models", "entity")
TEX_DIR = os.path.join(ASSETS, "textures", "entity", "doombot")


def build():
    for d in (GEO_DIR, TEX_DIR, PREVIEW):
        os.makedirs(d, exist_ok=True)
    m = DB.build()
    fill = prepare(m)
    m.write(os.path.join(GEO_DIR, "doombot_standard.geo.json"))
    tex, files = paint_states(m, DB.DECORATIONS, TEX_DIR, "doombot_standard",
                              [("", 0), ("_damaged", 1), ("_damaged_severe", 2)], ["low", "powered"])
    b, g = tex[""]
    views = [(0, 0, "front"), (180, 0, "back"), (90, 0, "right side"), (35, 12, "3/4")]
    imgs = [R.render(m, b, g["powered"], yaw=y, pitch=p, ppu=9, size=(260, 380), center=(0, 17.5)) for y, p, _ in views]
    for suffix, label in (("_damaged", "damaged"), ("_damaged_severe", "severely damaged")):
        bb, gg = tex[suffix]
        imgs.append(R.render(m, bb, gg["powered"], yaw=35, pitch=12, ppu=9, size=(260, 380), center=(0, 17.5)))
        views.append((0, 0, label))
    imgs.append(R.render(m, b, g["low"], yaw=35, pitch=12, ppu=9, size=(260, 380), center=(0, 17.5)))
    views.append((0, 0, "low-power emissive"))
    R.sheet(imgs, 4, labels=[v[2] for v in views]).save(os.path.join(PREVIEW, "doombot_standard.png"))
    print("doombot: %d bones, %d cubes, %dx%d (%.0f%% used), %d texture files"
          % (len(m.bones), sum(1 for _ in m.cubes()), m.tex_w, m.tex_h, fill * 100, len(files)))
    return m, tex, files


if __name__ == "__main__":
    build()
