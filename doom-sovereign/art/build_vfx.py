#!/usr/bin/env python3
"""Particle sprites (vanilla particles/<id>.json + textures/particle) and the VFX specification.

The specification (EFFECTS) is data: it drives docs/VFX.md and is written to
assets/doom_sovereign/vfx/effects.json so the future client code can read the same numbers
instead of re-typing them. The particle *types* need client registration code (not written: no
Fabric toolchain here); the textures and JSON follow the verified vanilla 26.1.2 format.
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from doomart.pixel import Canvas
from doomart.paint import palette_violations
from doomart import render as R
from build_armor import ASSETS, PREVIEW

ROOT = os.path.normpath(os.path.join(HERE, ".."))


def frames_flare():
    out = []
    for k in range(4):
        c = Canvas(8, 8)
        r = 1.2 + k * 0.9
        c.disc(3.5, 3.5, r, ("arcane_core", "arcane", "arcane", "arcane_dim")[k])
        if k < 3:
            c.disc(3.5, 3.5, max(0.6, r - 1.2), "arcane_core" if k < 2 else "arcane")
        out.append(c)
    return out


def frames_spark():
    out = []
    for k in range(4):
        c = Canvas(8, 8)
        col = ("arcane_core", "arcane", "arcane", "arcane_dim")[k]
        L = 3 - k // 2
        if k < 2:
            c.hline(3 - L, 4 + L, 3, col).vline(3, 3 - L, 4 + L, col)
        else:
            c.px(3, 3, col).px(4, 4, col)
        out.append(c)
    return out


def frames_mote():
    out = []
    for k in range(4):
        c = Canvas(8, 8)
        s = (1, 2, 2, 1)[k]
        for d in range(-s, s + 1):
            c.px(3 + d, 3, "green_hi").px(3, 3 + d, "green_hi")
        c.px(3, 3, "arcane_core" if k in (1, 2) else "arcane")
        out.append(c)
    return out


def frames_sigil():
    glyphs = [[(1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (5, 1), (1, 5), (3, 1), (3, 5)],
              [(3, 0), (3, 6), (0, 3), (6, 3), (1, 1), (5, 5), (5, 1), (1, 5), (3, 3)],
              [(1, 0), (2, 1), (3, 2), (4, 3), (5, 4), (6, 5), (1, 3), (2, 4), (4, 1), (5, 2)]]
    out = []
    for g in glyphs:
        c = Canvas(8, 8)
        for (x, y) in g:
            c.px(x, y, "arcane")
        c.px(3, 3, "arcane_core")
        out.append(c)
    return out


def frames_ring():
    out = []
    for k in range(4):
        c = Canvas(16, 16)
        c.ring(7.5, 7.5, 2.5 + k * 1.7, ("steel_hi", "steel_hi", "steel_mid", "steel")[k])
        out.append(c)
    return out


def frames_hex():
    out = []
    for col in ("arcane_dim", "steel_hi"):
        c = Canvas(8, 8)
        for (x, y) in ((2, 0), (3, 0), (4, 0), (5, 0), (1, 1), (6, 1), (0, 2), (7, 2), (0, 3), (7, 3), (0, 4), (7, 4),
                       (1, 5), (6, 5), (2, 6), (3, 6), (4, 6), (5, 6)):
            c.px(x, y, col)
        out.append(c)
    return out


def frames_scan():
    c = Canvas(8, 8)
    c.hline(0, 7, 3, "arcane_dim").hline(2, 5, 3, "arcane")
    return [c]


def frames_ember():
    out = []
    for k in range(3):
        c = Canvas(8, 8)
        c.px(3, 3, ("brass_hi", "brass", "brass_lo")[k])
        if k == 0:
            c.px(4, 3, "brass").px(3, 4, "brass")
        out.append(c)
    return out


def frames_weld():
    out = []
    for k in range(2):
        c = Canvas(8, 8)
        c.px(3, 3, "arcane_core").px(4, 3, "brass_hi" if k == 0 else "brass").px(3, 2, "brass_hi" if k == 0 else None)
        out.append(c)
    return out


def frames_smoke():
    out = []
    for k in range(4):
        c = Canvas(8, 8)
        c.disc(3.5, 3.5, 1.5 + k * 0.6, ("steel_mid", "steel_mid", "steel", "steel")[k])
        if k < 2:
            c.px(2, 2, "steel_hi")
        out.append(c)
    return out


PARTICLES = {
    "repulsor_flare": frames_flare, "energy_spark": frames_spark, "arcane_mote": frames_mote, "sigil_glyph": frames_sigil,
    "shock_ring": frames_ring, "field_hex": frames_hex, "scan_line": frames_scan, "ember": frames_ember,
    "weld_spark": frames_weld, "smoke_puff": frames_smoke,
}

# ---- the specification ----------------------------------------------------------------------------
# lifetime in ticks (20/s); size in blocks (curve: start -> peak -> end); budget = max live particles per
# emitter; reduced = behaviour under the vanilla "Particles: Decreased" / "Minimal" settings.
EFFECTS = [
    dict(id="repulsor_idle", family="tech", types=["repulsor_flare"], color="arcane #65E86B core #D2FFD4",
         lifetime=(6, 10), count="2 per second per emitter (palms, boots)", size=(0.06, 0.12, 0.02),
         motion="downward 0.12 b/t + inherited velocity, drag 0.85", opacity="1.0 -> 0 (ease-out)",
         emission="point at palm_emitter / boot locator", budget=8, reduced="Decreased: 1/s; Minimal: none (the emissive lens still glows)"),
    dict(id="repulsor_burst", family="tech", types=["repulsor_flare", "smoke_puff"], color="arcane core, steel smoke",
         lifetime=(8, 14), count="12 flares + 6 smoke, once", size=(0.1, 0.25, 0.05), motion="radial in the ground plane 0.25 b/t, drag 0.8",
         opacity="1.0 -> 0", emission="disc r=0.4 under each boot", budget=18, reduced="Decreased: 6 + 3; Minimal: 2 flares"),
    dict(id="repulsor_trail", family="tech", types=["repulsor_flare"], color="arcane", lifetime=(5, 8),
         count="1 per tick per emitter while cruising", size=(0.08, 0.1, 0.02), motion="opposite to flight direction 0.2 b/t, no gravity",
         opacity="0.8 -> 0", emission="palm and boot locators", budget=40, reduced="Decreased: every 3rd tick; Minimal: none"),
    dict(id="repulsor_trail_boost", family="tech", types=["repulsor_flare", "energy_spark"], color="arcane core, white-green sparks",
         lifetime=(6, 10), count="2 flares + 1 spark per tick per boot", size=(0.12, 0.18, 0.03), motion="trail + random 0.05 jitter",
         opacity="1.0 -> 0", emission="boot locators", budget=80, reduced="Decreased: half; Minimal: 1 flare every 4 ticks"),
    dict(id="gauntlet_charge", family="tech", types=["energy_spark"], color="arcane", lifetime=(4, 8),
         count="rises 1 -> 6 per tick with charge", size=(0.04, 0.08, 0.02), motion="converges on the palm from r=0.8",
         opacity="0.4 -> 1.0 -> 0", emission="sphere shell r=0.8 around palm_emitter", budget=48, reduced="Decreased: 1/3; Minimal: none (lens scale pulse remains)"),
    dict(id="gauntlet_muzzle", family="tech", types=["repulsor_flare", "energy_spark"], color="arcane core", lifetime=(3, 5),
         count="1 flare + 6 sparks, once", size=(0.2, 0.35, 0.0), motion="sparks cone 25 deg along the shot, 0.35 b/t",
         opacity="1.0 -> 0 fast", emission="palm_emitter", budget=7, reduced="Decreased: flare + 2; Minimal: flare only"),
    dict(id="gauntlet_heavy_muzzle", family="tech", types=["repulsor_flare", "energy_spark", "shock_ring"], color="arcane core, steel ring",
         lifetime=(4, 10), count="1 flare + 16 sparks + 1 ring", size=(0.4, 0.8, 0.0), motion="sparks cone 40 deg 0.5 b/t; ring expands to 1.5 b",
         opacity="1.0 -> 0", emission="palm_emitter", budget=18, reduced="Decreased: 6 sparks; Minimal: ring only"),
    dict(id="beam", family="tech", types=["energy_spark"], color="arcane + arcane_core line", lifetime=(2, 4),
         count="beam is a textured quad strip (not particles); 2 sparks per tick at the impact point", size=(0.05, 0.08, 0.0),
         motion="impact sparks reflect off the surface normal 0.2 b/t", opacity="1.0 -> 0", emission="hit point",
         budget=16, reduced="Decreased: 1 spark per 2 ticks; Minimal: none (quad strip stays)"),
    dict(id="landing_shockwave", family="tech", types=["shock_ring", "smoke_puff"], color="steel ring, steel dust", lifetime=(8, 16),
         count="1 flat ring + 10 dust (scaled by impact 0..1)", size=(0.5, 3.0, 3.0), motion="ring expands in the ground plane; dust radial 0.15 b/t",
         opacity="0.9 -> 0", emission="feet position, ground plane", budget=11, reduced="Decreased: ring + 4 dust; Minimal: ring"),
    dict(id="field_raise", family="tech", types=["field_hex"], color="arcane_dim hex cells", lifetime=(10, 14),
         count="24 hex cells, once", size=(0.25, 0.3, 0.25), motion="spawn on the shield surface, drift outward 0.02 b/t",
         opacity="0 -> 0.8 -> 0", emission="shield arc (directional 120 deg) or sphere", budget=24, reduced="Decreased: 10; Minimal: 4"),
    dict(id="field_impact", family="tech", types=["field_hex", "energy_spark"], color="steel_hi flash, arcane sparks",
         lifetime=(6, 10), count="6 hexes + 4 sparks at the hit bearing (x ripple 0..1)", size=(0.3, 0.4, 0.3),
         motion="hexes stay on the surface; sparks bounce outward 0.15 b/t", opacity="1.0 -> 0", emission="hit point on the field",
         budget=10, reduced="Decreased: 3 + 2; Minimal: 1 hex"),
    dict(id="field_collapse", family="tech", types=["field_hex", "energy_spark"], color="steel_hi shards", lifetime=(10, 20),
         count="30 hex shards + 12 sparks", size=(0.3, 0.3, 0.1), motion="outward 0.2 b/t with gravity 0.02", opacity="1.0 -> 0",
         emission="whole field surface", budget=42, reduced="Decreased: 12 + 4; Minimal: 6"),
    dict(id="scan_sweep", family="tech", types=["scan_line"], color="arcane_dim", lifetime=(10, 10),
         count="1 line every 2 ticks along a 40 deg cone", size=(0.4, 0.4, 0.4), motion="advances 0.8 b/t to sensor range",
         opacity="0.7 -> 0", emission="palm_emitter, cone", budget=20, reduced="Decreased: every 4 ticks; Minimal: none (HUD result still shows)"),
    dict(id="sparks", family="tech", types=["ember", "energy_spark"], color="brass embers, arcane sparks", lifetime=(6, 14),
         count="4-8 per burst", size=(0.05, 0.05, 0.02), motion="random hemisphere 0.2 b/t, gravity 0.04", opacity="1.0 -> 0",
         emission="spark locators on damaged bots / armour", budget=16, reduced="Decreased: half; Minimal: 1"),
    dict(id="repair_weld", family="tech", types=["weld_spark", "ember"], color="arcane core, brass", lifetime=(3, 8),
         count="3 per 2 ticks while repairing", size=(0.04, 0.05, 0.02), motion="small arcs 0.1 b/t, gravity 0.05",
         opacity="1.0 -> 0", emission="hand locator", budget=12, reduced="Decreased: half; Minimal: none"),
    dict(id="arcane_sigil", family="sorcery", types=["sigil_glyph", "arcane_mote"], color="arcane glyphs, green-white motes",
         lifetime=(16, 24), count="3 glyphs drawn along the hand path + 8 motes", size=(0.15, 0.3, 0.0),
         motion="glyphs hang, then rotate slowly and fade; motes rise 0.02 b/t", opacity="0 -> 1 -> 0 (slow)",
         emission="palm path during the cast", budget=11, reduced="Decreased: 2 + 3; Minimal: 1 glyph"),
    dict(id="ritual_motes", family="sorcery", types=["arcane_mote", "sigil_glyph"], color="green_hi motes, arcane glyph ring",
         lifetime=(30, 60), count="4 per second rising from the circle; 8 glyphs orbiting", size=(0.06, 0.12, 0.04),
         motion="rise 0.03 b/t with a slow spiral; glyphs orbit r=2 at 0.02 rad/t", opacity="0 -> 0.8 -> 0",
         emission="ritual circle perimeter", budget=40, reduced="Decreased: 2/s + 4 glyphs; Minimal: glyph ring only"),
    dict(id="teleport_flash", family="sorcery", types=["arcane_mote", "sigil_glyph"], color="arcane_core flash, green motes",
         lifetime=(8, 20), count="20 motes implode at the origin, 20 explode at the destination", size=(0.08, 0.12, 0.02),
         motion="origin: inward 0.3 b/t; destination: outward 0.25 b/t", opacity="1.0 -> 0",
         emission="body volume at both ends", budget=40, reduced="Decreased: 8 + 8; Minimal: 3 + 3"),
    dict(id="time_platform_charge", family="tech", types=["energy_spark", "shock_ring"], color="arcane sparks, steel rings",
         lifetime=(10, 20), count="sparks 1 -> 10 per tick over the charge; a ring every second", size=(0.05, 0.1, 0.0),
         motion="sparks spiral up the platform; rings rise 0.05 b/t", opacity="0.5 -> 1 -> 0", emission="platform disc r=2",
         budget=120, reduced="Decreased: 1/3; Minimal: rings only"),
]


def build():
    pdir = os.path.join(ASSETS, "particles")
    tdir = os.path.join(ASSETS, "textures", "particle")
    os.makedirs(pdir, exist_ok=True)
    os.makedirs(tdir, exist_ok=True)
    sheet, labels, bad, ntex = [], [], 0, 0
    for name, fn in PARTICLES.items():
        frames = fn()
        texs = []
        for k, c in enumerate(frames):
            a = c.array()
            bad += palette_violations(a)
            fname = "%s_%d" % (name, k) if len(frames) > 1 else name
            c.save(os.path.join(tdir, fname + ".png"))
            texs.append("doom_sovereign:" + fname)
            sheet.append(R.upscale(a, 8 if a.shape[0] == 8 else 4))
            labels.append(fname)
            ntex += 1
        with open(os.path.join(pdir, name + ".json"), "w") as f:
            json.dump({"textures": texs}, f, indent=2)
            f.write("\n")
    for e in EFFECTS:
        for t in e["types"]:
            assert t in PARTICLES, (e["id"], t)
    vdir = os.path.join(ASSETS, "vfx")
    os.makedirs(vdir, exist_ok=True)
    with open(os.path.join(vdir, "effects.json"), "w") as f:
        json.dump({"schema": 1, "effects": EFFECTS}, f, indent=1)
        f.write("\n")
    R.sheet(sheet, 8, labels=labels).save(os.path.join(PREVIEW, "particles.png"))
    write_doc()
    print("vfx: %d particle types, %d particle textures, %d effects specified, palette violations %d"
          % (len(PARTICLES), ntex, len(EFFECTS), bad))
    return len(PARTICLES), ntex, len(EFFECTS)


def write_doc():
    lines = ["# DOOM: SOVEREIGN - VFX specification", "",
             "Status: **specification + particle sprites only.** No particle has been spawned in Minecraft. The particle",
             "types need client registration code (a Fabric step, not written here). Numbers below are the same data as",
             "`assets/doom_sovereign/vfx/effects.json`, generated by `art/build_vfx.py`.", "",
             "Conventions: lifetime in ticks (20 per second); size in blocks as start -> peak -> end; `budget` is the most",
             "live particles one emitter may own (the emitter stops spawning at the budget); `reduced` follows vanilla's",
             "Particles setting (All / Decreased / Minimal). Technology effects use hard flares, sparks, rings and hex",
             "cells; sorcery effects use slow glyphs and drifting motes, so the two read differently even in green.", "",
             "Global rules:", "",
             "- Per-player cap: 250 live DOOM: SOVEREIGN particles; beyond it, new emitters spawn at 1/4 rate.",
             "- Distance culling: emitters farther than 48 blocks from the camera spawn nothing; 24-48 blocks spawn half.",
             "- First-person: the wearer's own palm/boot trails are suppressed within 1.5 blocks of the camera (no screen spam).",
             "- Every effect has a non-particle fallback (emissive textures, HUD, sound) so Minimal loses no information.", "",
             "| Effect | Family | Particle types | Colour | Lifetime (t) | Count | Size (b) | Motion | Opacity | Emission | Budget | Reduced |",
             "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for e in EFFECTS:
        lines.append("| `%s` | %s | %s | %s | %d-%d | %s | %s -> %s -> %s | %s | %s | %s | %d | %s |" % (
            e["id"], e["family"], ", ".join(e["types"]), e["color"], e["lifetime"][0], e["lifetime"][1], e["count"],
            e["size"][0], e["size"][1], e["size"][2], e["motion"], e["opacity"], e["emission"], e["budget"], e["reduced"]))
    lines += ["", "## Particle sprites", "", "| Type | Frames | Notes |", "|---|---|---|"]
    for name, fn in PARTICLES.items():
        lines.append("| `%s` | %d | %s |" % (name, len(fn()), "16x16" if name == "shock_ring" else "8x8"))
    lines += ["", "Preview: `art/previews/particles.png`.", ""]
    with open(os.path.join(ROOT, "docs", "VFX.md"), "w") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    build()
