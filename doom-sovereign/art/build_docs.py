#!/usr/bin/env python3
"""Generates the reference documents from the same data the assets are built from:

  docs/ROYAL_ARMOR_SKELETON.md, docs/DOOMBOT_SKELETON.md, docs/ANIMATION_LIBRARY.md,
  docs/AUDIO.md, docs/HUD.md, docs/ASSET_MANIFEST.md, docs/asset_counts.json
and the mod icon (assets/doom_sovereign/icon.png).
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from doomart import royal_armor as RA, doombot as DB, doom_mask as DM, hud, render as R
from doomart.paint import Painter
from doomart.palette import SPEC, DERIVED
from build_armor import ASSETS, PREVIEW

ROOT = os.path.normpath(os.path.join(HERE, ".."))
DOCS = os.path.join(ROOT, "docs")


def fmt(v):
    return ("%g" % v)


def dof(b):
    if not b.dof:
        return "fixed (driven only through its parent)"
    return ", ".join("%s %s..%s" % (ax, fmt(lo), fmt(hi)) if ax in b.dof else "%s fixed" % ax
                     for ax, (lo, hi) in ((a, b.dof.get(a, (0, 0))) for a in "xyz"))


def skeleton_doc(model, title, intro, path, linked=None):
    lines = ["# " + title, "", intro, "",
             "Coordinates: Bedrock geometry space, 1 unit = 1 model pixel (16 per block), +y up, the model's front faces -z,",
             "the model's right side is -x. Pivots are absolute. Rotations are degrees; limits below are the ranges the",
             "animation validator enforces for rest rotation + animated rotation. Sign conventions (from the transform",
             "emulation in `art/doomart/render.py`, awaiting in-game confirmation): limb x negative = swing forward, right",
             "limb z positive = outward, elbow x negative = flex, knee x positive = flex, head/body x positive = pitch down.", "",
             "| Bone | Parent | Pivot | Rest rotation | Rotation limits (DOF) | Cubes | Purpose |",
             "|---|---|---|---|---|---|---|"]
    for b in model.bones:
        lines.append("| `%s` | %s | %s | %s | %s | %d | %s |" % (
            b.name, "`%s`" % b.parent if b.parent else "(root)", "(%s)" % ", ".join(fmt(p) for p in b.pivot),
            "(%s)" % ", ".join(fmt(r) for r in b.rotation) if any(b.rotation) else "-", dof(b), len(b.cubes), b.desc))
    lines += ["", "Hierarchy:", "", "```"]

    def walk(name, depth):
        lines.append("  " * depth + name)
        for c in model.children(name):
            walk(c.name, depth + 1)
    for b in model.bones:
        if b.parent is None:
            walk(b.name, 0)
    lines += ["```", ""]
    if linked:
        lines += ["Linked bones (must be animated identically; the validator checks every sampled frame):", ""]
        lines += ["- `%s` = `%s`" % (a, b) for a, b in linked.items()]
        lines.append("")
    lines += ["Texture: %dx%d, box UV, %d cubes. Geometry identifier `%s`." % (
        model.tex_w, model.tex_h, sum(1 for _ in model.cubes()), model.identifier), ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def animation_doc(path):
    lines = ["# Animation library", "",
             "Status: **authored, awaiting runtime validation.** Every clip passes `art/doomart/anim.py`'s validator",
             "(structure, bone names, easing names, key times, loop seams, sampled joint limits, linked knee bones, sound and",
             "particle ids) and the Java `PresentationTest`, but none has been played by GeckoLib.", "",
             "Integration note: vanilla drives the armour root bones (`armorHead`, `armorBody`, limbs). Clips that move the",
             "roots (walk, flight poses, landings) need the player model itself to take the same pose - a player-animation",
             "hook on the Fabric side - otherwise only the child bones (elbows, knees, cloak, mask, plates) will move.",
             "Full-body lean and roll in flight are applied by the renderer from `FlightOutput`, not by the clips.",
             "The eye-glow bone scales only the flare planes; dimming the face-plate glow needs the glow-mask texture swap",
             "(`_glowmask_low` / none) chosen by the renderer.", ""]
    for rel, title in (("armor/royal_armor.animation.json", "Royal Armor"), ("entity/doombot.animation.json", "Standard Doombot"),
                       ("item/doom_mask.animation.json", "Doom mask (hero asset)")):
        with open(os.path.join(ASSETS, "geckolib", "animations", rel)) as f:
            doc = json.load(f)
        lines += ["## %s (`%s`)" % (title, rel), "", "| Clip | Length (s) | Loop | Keyframes | Sounds | Particles | Gameplay cues |", "|---|---|---|---|---|---|---|"]
        for name, a in doc["animations"].items():
            keys = sum(len(k) for ch in a["bones"].values() for k in ch.values())
            snd = ", ".join("%s@%s" % (e["effect"].split(":")[1], t) for t, e in a.get("sound_effects", {}).items())
            par = ", ".join("%s@%s" % (e["effect"].split(":")[1], t) for t, e in a.get("particle_effects", {}).items())
            cues = ", ".join("%s@%s" % (c, t) for t, c in a.get("timeline", {}).items())
            loop = {True: "loop", False: "once", "hold_on_last_frame": "hold"}[a["loop"]]
            lines.append("| `%s` | %g | %s | %d | %s | %s | %s |" % (name, a["animation_length"], loop, keys, snd or "-", par or "-", cues or "-"))
        lines.append("")
    lines += ["Descriptions and authoring notes live next to each clip in `art/doomart/anim_armor.py`,",
              "`anim_doombot.py` and `anim_mask.py`. Contact sheets: `art/previews/anim/`.", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def audio_doc(path):
    with open(os.path.join(HERE, "audio_report.json")) as f:
        rep = json.load(f)
    lines = ["# Audio", "",
             "Status: **created and measured; not heard in game.** Every sound is synthesized by `art/build_audio.py` from",
             "oscillators, filtered noise and envelopes (`art/doomart/synth.py`). No samples, recordings, voices, ripped or",
             "third-party audio, and no imitation of any actor or existing game/film sound. Mono 44.1 kHz OGG Vorbis",
             "(mono so Minecraft can position it).", "",
             "Two families: **technology** (filtered noise, FM metal, gliding servo whines, hard transients, mains-like",
             "hum) and **sorcery** (just-intonation sine stacks, inharmonic bells, reversed swells, long airy tails).",
             "Spectrograms: `art/previews/audio_spectrograms.png`.", "",
             "Loudness rules: peak <= -1 dBFS after encoding (2 dB pre-encode headroom); RMS targets -14 (impacts),",
             "-16 (one-shots), -19 (UI), -22 (loops) dBFS; transient sounds sit below their target because the peak limit",
             "wins. Loops are cross-faded and rotated to a quiet seam; `seam` is the seam step divided by the loop's",
             "99th-percentile sample step (< 1 means inaudible).", "",
             "| Event | File | Family | Kind | Length (s) | Peak dBFS | RMS dBFS | Seam | Design |", "|---|---|---|---|---|---|---|---|---|"]
    for r in rep:
        lines.append("| `%s` | `%s` | %s | %s | %.2f | %.2f | %.2f | %s | %s |" % (
            r["event"], r["file"], r["family"], r["kind"], r["duration_s"], r["peak_dbfs"], r["rms_dbfs"],
            r.get("loop_seam_ratio", "-"), r["description"]))
    lines += ["", "In-game categories (set in code when played): armour, flight and weapons -> `players`; Doombots -> `hostile`",
              "when hostile to the listener else `neutral`; machines and Time Platform -> `blocks`; sorcery -> `players`.", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def hud_doc(path):
    lines = ["# HUD specification", "",
             "Status: **sprites created, layout specified and mocked up; not drawn by the game.** Sprites are in",
             "`assets/doom_sovereign/textures/gui/sprites/hud/` (sprite ids `doom_sovereign:hud/<name>`), authored at 1x GUI",
             "pixels; the game scales them by the integer GUI scale. Mock-ups: `art/previews/hud_mockup_*.png`.", "",
             "Principles: restrained (nothing over the centre of the screen except the target bracket), anchored to the",
             "corners, readable at every GUI scale, and never colour-only: warnings differ in shape and critical ones blink",
             "at 2 Hz; bars have tick marks every 20 %; the heat bar marks the throttle (70 %) and warning (50 %) points.", "",
             "## Anchoring (GUI pixels)", "",
             "| Element | Anchor | Rectangle at 480x270 (1920x1080, scale 4) | at 426x240 (1280x720, scale 3) | at 320x240 (640x480, scale 2) |",
             "|---|---|---|---|---|"]
    ls = [hud.layout(480, 270), hud.layout(426, 240), hud.layout(320, 240)]
    for key in ("focus", "shield", "heat", "energy", "warnings", "abilities", "scan_panel", "hotbar (vanilla)"):
        anchor = {"abilities": "bottom-right", "scan_panel": "top-right", "hotbar (vanilla)": "bottom-centre"}.get(key, "bottom-left")
        cells = ["x %d, y %d, %dx%d" % l[key][:4] for l in ls]
        lines.append("| %s | %s | %s |" % (key, anchor, " | ".join(cells)))
    lines += ["", "Compact rule: when the GUI is narrower than %d px (the status cluster would touch the hotbar), the cluster" % hud.MIN_SIDE_W,
              "and the ability bar move up above the vanilla health/food rows (see the 640x480 mock-up).", "",
              "## Elements", "",
              "- **Energy** (82x5): fill = stored / capacity; the leftmost 10 % shows the reserve band (`energy_bar_reserve`);",
              "  at `LOW` status the fill switches to `energy_bar_fill_low` (brass, striped) and blinks at `RESERVE`.",
              "- **Heat** (82x3): brass fill, brighter past the throttle marker; `heat_bar_fill_locked` (hatched) while locked out.",
              "- **Force field** (82x3): segmented steel fill = field charge / capacity; hidden while the field is OFF.",
              "- **Arcane focus** (82x5): pale fill with sigil dots (sorcery look); reserved focus for a channel shows as the",
              "  unfilled part blinking slowly.",
              "- **Warnings** (9x9, up to 4, left to right by severity): low energy (triangle + bolt), overheat (square + flame),",
              "  shield down (broken hexagon), low focus (open ring), armour damaged (cracked plate), lock-on (four ticks).",
              "- **Abilities**: 4 slots (20x20), selected slot framed in brass; icon 16x16; cooldown = `cooldown_00..15` radial",
              "  wipe (frame = floor(progress x 16)); a charge counter digit draws bottom-right when an ability has charges.",
              "- **Scan result**: nine-slice panel (`scan_panel`, border 4) 124 px wide; lines: subject name, knowledge % +",
              "  `knowledge_bar`, up to 4 revealed traits, newly unlocked countermeasure; fades 6 s after the last scan.",
              "- **Target bracket**: four `target_bracket` corners (mirrored at draw time) around the projected bounding box",
              "  of the current target; `target_bracket_locked` when a charged shot or bot order is locked on.",
              "- Vanilla hotbar, health, food and crosshair are untouched.", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def manifest():
    rows, counts = [], {}
    base = os.path.join(ROOT, "mod", "src", "main", "resources")
    for root, _, files in os.walk(base):
        for fn in sorted(files):
            p = os.path.join(root, fn)
            rel = os.path.relpath(p, base)
            kind = kind_of(rel)
            counts[kind] = counts.get(kind, 0) + 1
            with open(p, "rb") as f:
                h = hashlib.sha1(f.read()).hexdigest()[:10]
            rows.append((rel, kind, os.path.getsize(p), h))
    prev = []
    for root, _, files in os.walk(PREVIEW):
        for fn in sorted(files):
            prev.append(os.path.relpath(os.path.join(root, fn), ROOT))
    rows.sort()
    lines = ["# Asset manifest", "", "Every file under `mod/src/main/resources`, generated by `art/build_all.py` (sha1 prefix lets a",
             "reviewer confirm a rebuild is identical).", "", "## Counts by type", "", "| Type | Files |", "|---|---|"]
    for k in sorted(counts):
        lines.append("| %s | %d |" % (k, counts[k]))
    lines += ["| **total** | **%d** |" % sum(counts.values()), "", "Preview images (not shipped): %d files in `art/previews/`." % len(prev), "",
              "## Files", "", "| Path | Type | Bytes | sha1 |", "|---|---|---|---|"]
    for rel, kind, size, h in rows:
        lines.append("| `%s` | %s | %d | `%s` |" % (rel, kind, size, h))
    with open(os.path.join(DOCS, "ASSET_MANIFEST.md"), "w") as f:
        f.write("\n".join(lines) + "\n")
    with open(os.path.join(DOCS, "asset_counts.json"), "w") as f:
        json.dump({"by_type": counts, "total": sum(counts.values()), "previews": len(prev)}, f, indent=1)
        f.write("\n")
    return counts


def kind_of(rel):
    r = rel.replace("\\", "/")
    if r.endswith(".ogg"):
        return "sound (ogg)"
    if "/geckolib/models/" in r:
        return "geometry (geo.json)"
    if "/geckolib/animations/" in r:
        return "animation library (json)"
    if r.endswith(".png"):
        for key, name in (("/textures/armor/", "texture: armor"), ("/textures/item/", "texture: item"),
                          ("/textures/entity/", "texture: entity"), ("/textures/block/", "texture: block"),
                          ("/textures/gui/", "texture: HUD sprite"), ("/textures/particle/", "texture: particle")):
            if key in r:
                return name
        return "texture: other (icon)"
    if r.endswith(".mcmeta"):
        return "sprite metadata"
    if "/lang/" in r:
        return "language"
    if r.endswith("sounds.json"):
        return "sounds.json"
    for key, name in (("/items/", "item definition"), ("/models/", "model json"), ("/blockstates/", "blockstate"),
                      ("/equipment/", "equipment asset"), ("/particles/", "particle definition"), ("/vfx/", "vfx spec (json)")):
        if key in r:
            return name
    return "other"


def mod_icon():
    m = DM.build()
    m.pack()
    base, glow = Painter(m, DM.DECORATIONS, glow="powered").paint()
    img = R.render(m, base, glow, yaw=18, pitch=6, ppu=7, size=(128, 128), center=(0, 7.5), background=(20, 45, 36, 255))
    from PIL import Image
    Image.fromarray(img, "RGBA").save(os.path.join(ASSETS, "icon.png"))


def palette_doc(path):
    lines = ["# Art direction and palette", "",
             "All textures are generated by `art/` and limited to these colours (every pixel is checked by",
             "`art/tests/test_pipeline.py`). Spec colours come from the art direction; derived colours are the minimum",
             "extra steps for shading, each with its derivation.", "", "| Name | Hex | Source |", "|---|---|---|"]
    for k, v in SPEC.items():
        lines.append("| %s | `%s` | spec |" % (k, v))
    for k, (v, why) in DERIVED.items():
        lines.append("| %s | `%s` | derived: %s |" % (k, v, why))
    lines += ["", "Pixel-art discipline:", "",
              "- One texel per model unit on worn armour and the Doombot (vanilla density); the hero mask is 2x.",
              "- Flat material colour, one-pixel light on the top/left edges and recess on the bottom/right, no gradients",
              "  or noise; wear marks are sparse single pixels placed with fixed seeds.",
              "- Decoration is hand-placed per face (mask slits, stern lines, grille, rivets, buckle, trims).",
              "- Emissive parts are separate `_glowmask` textures (GeckoLib's glow-layer convention - to be confirmed for",
              "  the GeckoLib version used): off / low / powered / arcane; damage variants keep identical UV layout.",
              "- Technology glows solid green; sorcery adds sigils, runes and green-white cores.", ""]
    with open(path, "w") as f:
        f.write("\n".join(lines))


def build():
    os.makedirs(DOCS, exist_ok=True)
    a = RA.build()
    a.pack()
    skeleton_doc(a, "Royal Armor skeleton", "The one bone hierarchy every Royal Armor clip targets (`geckolib/models/armor/royal_armor.geo.json`). "
                 "Root bone names follow GeckoLib's armour-renderer convention.", os.path.join(DOCS, "ROYAL_ARMOR_SKELETON.md"), RA.LINKED)
    b = DB.build()
    b.pack()
    skeleton_doc(b, "Doombot skeleton (reusable)", "Shared by every Doombot variant: variants change cubes and textures, never bone "
                 "names or pivots, so all Doombot clips apply to all variants.", os.path.join(DOCS, "DOOMBOT_SKELETON.md"))
    mk = DM.build()
    mk.pack()
    skeleton_doc(mk, "Doom mask hero asset", "Stand-alone mask for item display, the Armor Cradle and the equip cut-in; the lock sequence "
                 "moves brow, cheeks, jaw and eye glow.", os.path.join(DOCS, "DOOM_MASK_RIG.md"))
    animation_doc(os.path.join(DOCS, "ANIMATION_LIBRARY.md"))
    audio_doc(os.path.join(DOCS, "AUDIO.md"))
    hud_doc(os.path.join(DOCS, "HUD.md"))
    palette_doc(os.path.join(DOCS, "ART_DIRECTION.md"))
    mod_icon()
    counts = manifest()
    print("docs: 8 documents; assets by type:", counts)


if __name__ == "__main__":
    build()
