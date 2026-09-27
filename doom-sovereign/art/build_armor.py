#!/usr/bin/env python3
"""Builds the Royal Armor art package.

    python3 build_armor.py

Writes the geometry and textures into the mod resource tree and preview renders into
art/previews/. Deterministic: running it twice produces identical files.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from doomart import royal_armor as RA
from doomart.paint import Painter, to_image, palette_violations
from doomart import render as R

ROOT = os.path.normpath(os.path.join(HERE, ".."))
ASSETS = os.path.join(ROOT, "mod", "src", "main", "resources", "assets", "doom_sovereign")
GEO_DIR = os.path.join(ASSETS, "geckolib", "models", "armor")
TEX_DIR = os.path.join(ASSETS, "textures", "armor")
PREVIEW = os.path.join(HERE, "previews")

VARIANTS = [
    # file suffix, damage, glow state written alongside
    ("", 0),
    ("_damaged_moderate", 1),
    ("_damaged_severe", 2),
]
GLOWS = ["low", "powered", "arcane"]


def build():
    for d in (GEO_DIR, TEX_DIR, PREVIEW):
        os.makedirs(d, exist_ok=True)
    m = RA.build()
    fill = m.pack()
    problems = m.validate()
    if problems:
        raise SystemExit("model problems:\n  " + "\n  ".join(problems))
    m.write(os.path.join(GEO_DIR, "royal_armor.geo.json"))
    textures = {}
    for suffix, dmg in VARIANTS:
        textures[suffix] = [None, {}]
        for glow in GLOWS:
            base, gl = Painter(m, RA.DECORATIONS, damage=dmg, glow=glow).paint()
            if glow == "powered":
                to_image(base).save(os.path.join(TEX_DIR, "royal_armor%s.png" % suffix))
                textures[suffix][0] = base
            name = "royal_armor%s_glowmask%s.png" % (suffix, "" if glow == "powered" else "_" + glow)
            to_image(gl).save(os.path.join(TEX_DIR, name))
            textures[suffix][1][glow] = gl
    bad = sum(palette_violations(b) for b, _ in textures.values())
    if bad:
        raise SystemExit("palette violations: %d" % bad)
    previews(m, textures)
    print("royal armor: %d bones, %d cubes, texture %dx%d (%.0f%% used), %d texture files"
          % (len(m.bones), sum(1 for _ in m.cubes()), m.tex_w, m.tex_h, fill * 100, 3 + 3 * len(GLOWS)))
    return m


def previews(m, textures):
    base, glows = textures[""]
    views = [(0, 0, "front"), (180, 0, "back"), (90, 0, "right side"), (-90, 0, "left side"),
             (35, 15, "3/4 front-right"), (-145, 15, "3/4 back-left")]
    imgs = [R.render(m, base, glows["powered"], yaw=y, pitch=p, ppu=10, size=(280, 400), center=(0, 16)) for y, p, _ in views]
    R.sheet(imgs, 3, labels=[v[2] for v in views]).save(os.path.join(PREVIEW, "royal_armor_turnaround.png"))
    # damage and glow states, face close-ups
    cells, labels = [], []
    for suffix, label in (("", "pristine"), ("_damaged_moderate", "moderate damage"), ("_damaged_severe", "severe damage")):
        b, g = textures[suffix]
        cells.append(R.render(m, b, g["powered"], yaw=20, pitch=5, ppu=22, size=(300, 300), center=(0, 27.5),
                              hide=_body_bones(m)))
        labels.append(label)
    for glow in ("low", "powered", "arcane"):
        cells.append(R.render(m, base, glows[glow], yaw=0, pitch=0, ppu=22, size=(300, 300), center=(0, 27.5),
                              hide=_body_bones(m)))
        labels.append("glow: " + glow)
    R.sheet(cells, 3, labels=labels).save(os.path.join(PREVIEW, "royal_armor_mask_states.png"))
    # the texture atlas itself, enlarged 4x on a checker so transparent pixels are visible
    atlas = R.upscale(base, 4)
    R.sheet([_checker(atlas), _checker(R.upscale(glows["arcane"], 4))], 2,
            labels=["royal_armor.png (x4)", "royal_armor_glowmask_arcane.png (x4)"]).save(
        os.path.join(PREVIEW, "royal_armor_atlas.png"))


def _body_bones(m):
    keep = set()
    todo = ["armorHead"]
    while todo:
        n = todo.pop()
        keep.add(n)
        todo += [b.name for b in m.children(n)]
    return tuple(b.name for b in m.bones if b.name not in keep)


def _checker(img):
    import numpy as np
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    bg = np.where(((xx // 8 + yy // 8) % 2)[..., None] == 0, 40, 56).astype(np.uint8)
    out = np.zeros_like(img)
    out[..., :3] = bg
    out[..., 3] = 255
    a = img[..., 3:4] / 255.0
    out[..., :3] = (img[..., :3] * a + out[..., :3] * (1 - a)).astype(np.uint8)
    return out


if __name__ == "__main__":
    build()
