#!/usr/bin/env python3
"""Builds, validates and previews the animation libraries.

    python3 build_anims.py            (after build_armor.py)

The validator runs on the JSON as written to disk, not on the authoring objects.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from doomart import anim as A, anim_armor, anim_doombot, anim_mask, royal_armor as RA, doombot as DB, doom_mask as DM, render as R
from doomart.paint import Painter
from doomart.rig import ROOTS
from build_armor import ASSETS, PREVIEW

ANIM_DIR = os.path.join(ASSETS, "geckolib", "animations", "armor")


def known_particles():
    p = os.path.join(ASSETS, "vfx", "effects.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return {"doom_sovereign:" + e["id"] for e in json.load(f)["effects"]}


def known_sounds():
    p = os.path.join(ASSETS, "sounds.json")
    if not os.path.exists(p):
        return None
    with open(p) as f:
        return {"doom_sovereign:" + k for k in json.load(f)}


def armor():
    os.makedirs(ANIM_DIR, exist_ok=True)
    m = RA.build()
    m.pack()
    anims = anim_armor.build(m)
    path = os.path.join(ANIM_DIR, "royal_armor.animation.json")
    A.write_library(path, anim_armor.PREFIX, anims)
    with open(path) as f:
        doc = json.load(f)
    problems = A.validate(doc, m, linked=RA.LINKED, known_sounds=known_sounds(), known_particles=known_particles(), root_motion=ROOTS)
    keys = sum(len(k) for a in doc["animations"].values() for ch in a["bones"].values() for k in ch.values())
    print("royal armor animations: %d clips, %d keyframes, %d problems" % (len(doc["animations"]), keys, len(problems)))
    for p in problems[:40]:
        print("  " + p)
    return m, anims, doc, problems


def contact_sheets(m, anims, out_dir, frames=6):
    base, glow = Painter(m, RA.DECORATIONS, glow="powered").paint()
    os.makedirs(out_dir, exist_ok=True)
    by_cat = {}
    for a in anims:
        by_cat.setdefault(a.category, []).append(a)
    for cat, group in by_cat.items():
        cells, labels = [], []
        for a in group:
            for i in range(frames):
                t = a.length * i / (frames - 1)
                img = R.render(m, base, glow, pose=a.pose_at(t), yaw=40, pitch=10, ppu=4.2, size=(150, 190),
                               center=(0, 14), lean=a.lean)
                cells.append(img)
                labels.append("%s %.2fs" % (a.name, t) if i == 0 else "%.2fs" % t)
        R.sheet(cells, frames, gap=4, labels=labels).save(os.path.join(out_dir, "armor_%s.png" % cat))


def library(model, module, sub, fname, root_motion=()):
    d = os.path.join(ASSETS, "geckolib", "animations", sub)
    os.makedirs(d, exist_ok=True)
    model.pack()
    anims = module.build()
    path = os.path.join(d, fname)
    A.write_library(path, module.PREFIX, anims)
    with open(path) as f:
        doc = json.load(f)
    problems = A.validate(doc, model, known_sounds=known_sounds(), known_particles=known_particles(), root_motion=root_motion)
    keys = sum(len(k) for a in doc["animations"].values() for ch in a["bones"].values() for k in ch.values())
    print("%s: %d clips, %d keyframes, %d problems" % (fname, len(doc["animations"]), keys, len(problems)))
    for p in problems[:40]:
        print("  " + p)
    return anims, doc, problems


def bot_sheet(m, anims, out, frames=6):
    from doomart.paint import Painter
    base, glow = Painter(m, DB.DECORATIONS, glow="powered").paint()
    cells, labels = [], []
    for a in anims:
        for i in range(frames):
            t = a.length * i / (frames - 1)
            cells.append(R.render(m, base, glow, pose=a.pose_at(t), yaw=40, pitch=10, ppu=4.0, size=(150, 190), center=(0, 15)))
            labels.append("%s %.2fs" % (a.name, t) if i == 0 else "%.2fs" % t)
    R.sheet(cells, frames, gap=4, labels=labels).save(out)


if __name__ == "__main__":
    m, anims, doc, problems = armor()
    bm = DB.build()
    banims, bdoc, bprob = library(bm, anim_doombot, "entity", "doombot.animation.json", root_motion=("root", "pelvis"))
    mm = DM.build()
    manims, mdoc, mprob = library(mm, anim_mask, "item", "doom_mask.animation.json")
    if "--no-preview" not in sys.argv:
        contact_sheets(m, anims, os.path.join(PREVIEW, "anim"))
        bot_sheet(bm, banims, os.path.join(PREVIEW, "anim", "doombot.png"))
    sys.exit(1 if (problems or bprob or mprob) else 0)
