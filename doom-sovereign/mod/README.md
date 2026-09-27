# DOOM: SOVEREIGN — mod module (resources only)

**Status: resource tree real, Java code absent, build not wired.**

This directory is where the Fabric mod for Minecraft 26.1.2 will live. In this session the Fabric
toolchain (Loom, Loader, Fabric API), GeckoLib, the Minecraft client/server jars and Java 25 could
not be downloaded, so nothing here has been compiled, launched or seen in game.

What is here:

| Path | What it is | Validated how |
|---|---|---|
| `src/main/resources/assets/doom_sovereign/geckolib/models/` | Royal Armor, hero mask and Standard Doombot geometry (Bedrock 1.12.0 geometry JSON, the format GeckoLib's Blockbench plugin writes) | `art/` validators: bone graph, UV bounds and overlap, re-rendered with the preview renderer |
| `src/main/resources/assets/doom_sovereign/geckolib/animations/` | 58 animation clips (Bedrock animation JSON 1.8.0) | `art/doomart/anim.py` validator + `core` Java cross-check test |
| `src/main/resources/assets/doom_sovereign/textures/` | armor, mask, Doombot, glow masks, items, blocks, HUD sprites, particles, fallback equipment texture | palette check on every pixel, preview sheets in `art/previews/` |
| `src/main/resources/assets/doom_sovereign/sounds/`, `sounds.json` | 32 original OGG files for 28 sound events | decoded and measured (`art/audio_report.json`) |
| `src/main/resources/assets/doom_sovereign/{items,models,blockstates,equipment,particles}` | vanilla-format resource JSON | formats compared with the 26.1.2 client assets (misode/mcmeta `26.1.2-assets`) |
| `src/main/resources/assets/doom_sovereign/lang/en_us.json` | names, subtitles, HUD and key strings | generated from the same tables as the assets |
| `src/main/resources/assets/doom_sovereign/vfx/effects.json` | the VFX specification as data | referenced ids checked against animations |
| `fabric.mod.json.template` | **unverified scaffolding** with `${...}` placeholders | not validated: requires Fabric metadata |

GeckoLib asset folder: GeckoLib 4 used `assets/<ns>/geo/` and `assets/<ns>/animations/`; this tree uses
`assets/<ns>/geckolib/models/` and `assets/<ns>/geckolib/animations/`, which is our understanding of
GeckoLib 5. Confirm against the GeckoLib 5.x build actually used (integration step 12) and move the two
folders if needed — no other file references those paths.

Every file under `src/main/resources/assets` is generated: edit the generators in `art/`, then run
`python3 art/build_all.py`. Planned Java packages are listed in `src/main/java/com/doomsovereign/mod/PACKAGES.md`.
