#!/usr/bin/env python3
"""Builds the Doom mask hero asset: geometry, 3 damage textures, glow masks, previews."""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from doomart import doom_mask as DM
from doomart import render as R
from doomart.pipeline import paint_states, prepare
from build_armor import ASSETS, PREVIEW

GEO_DIR = os.path.join(ASSETS, "geckolib", "models", "item")
TEX_DIR = os.path.join(ASSETS, "textures", "item")


def build():
    for d in (GEO_DIR, TEX_DIR, PREVIEW):
        os.makedirs(d, exist_ok=True)
    m = DM.build()
    fill = prepare(m)
    m.write(os.path.join(GEO_DIR, "doom_mask.geo.json"))
    tex, files = paint_states(m, DM.DECORATIONS, TEX_DIR, "doom_mask",
                              [("", 0), ("_damaged_moderate", 1), ("_damaged_severe", 2)], ["low", "powered", "arcane"])
    cells, labels = [], []
    for suffix, label in (("", "pristine"), ("_damaged_moderate", "moderate damage"), ("_damaged_severe", "severe damage")):
        b, g = tex[suffix]
        cells.append(R.render(m, b, g["powered"], yaw=25, pitch=8, ppu=14, size=(300, 260), center=(0, 7.5)))
        labels.append(label)
    b, g = tex[""]
    for state in ("low", "powered", "arcane"):
        cells.append(R.render(m, b, g[state], yaw=0, pitch=0, ppu=14, size=(300, 260), center=(0, 7.5)))
        labels.append(state + (" (low-power emissive)" if state == "low" else " eyes" if state == "powered" else "-enhanced"))
    R.sheet(cells, 3, labels=labels).save(os.path.join(PREVIEW, "doom_mask_states.png"))
    print("doom mask: %d bones, %d cubes, %dx%d (%.0f%% used), %d texture files"
          % (len(m.bones), sum(1 for _ in m.cubes()), m.tex_w, m.tex_h, fill * 100, len(files)))
    return m, files


if __name__ == "__main__":
    build()
