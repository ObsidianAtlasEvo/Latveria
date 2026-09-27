# DOOM: SOVEREIGN — end-of-session status report

Session constraint: no network access to Fabric, Mojang, GeckoLib, Modrinth or JDK 25 hosts. Nothing in this
repository has been compiled against Fabric, run inside Minecraft, or seen in game. No launch results exist.
Every "validated" below means validated **locally, without Minecraft**, by the tool named.

## 1. Fully created and locally validated (toolchain-independent)

| Deliverable | Where | Validated by |
|---|---|---|
| Pure-Java game domain (Java 21 syntax, Gson only): armor energy, heat, arcane focus, cooldowns, force field, flight state machine, modules/frames/loadouts, research tree, Doom Analysis, Doombot command/AI, security permissions, power network, versioned persistence with v1->v2 migration, `DoomSuit` aggregate, presentation catalog + animation selector | `core/src/main/java` | 167 JUnit tests (below), compiled with `-Xlint:all -Werror` |
| Power-network stress test (100,489-node grid, split/merge/leaf churn, 20,000 networks) with recorded timings | `core/.../PowerGraphStressTest.java`, `docs/PERFORMANCE_CORE.md` | test assertions + recorded numbers (build machine: JDK 21, 4 CPUs) |
| Asset generators (geometry, box-UV packing, pixel-art painter, software renderer, rig/IK, animation authoring + validator, synthesizer, HUD/icon/particle drawing, docs) | `art/` (Python 3 + numpy + Pillow + soundfile) | 27 unittest cases incl. negative tests that the validators reject broken input |
| Every texture limited to the palette (8 spec colours + 6 documented derived shades) | `textures/**` | per-pixel check in `test_every_generated_texture_is_on_palette` |
| Geometry well-formed (unique bones, parents, UV in bounds, no UV overlaps) | 3 `.geo.json` files | `Model.validate()` + tests |
| Animation files structurally valid: names, easing names, key times, loop seams, **sampled** joint limits, linked knee bones, sound and particle ids resolve | 3 animation libraries, 58 clips | `anim.validate()` (0 problems) + Java `PresentationTest` cross-check |
| Audio measured after encoding: mono 44.1 kHz, peak <= -1 dBFS, no clipping, DC ~0, loop seams below one typical sample step | 32 OGG files | `art/audio_report.json`, `AudioTests` |
| Vanilla resource JSON in 26.1.2 formats (items, item/block models, blockstates, equipment, particles, nine-slice sprite meta) | `items/`, `models/`, `blockstates/`, `equipment/`, `particles/` | compared by hand with the 26.1.2 client assets on the misode/mcmeta mirror |
| Deterministic rebuild | whole asset tree | `python3 art/build_all.py` reproduces every file byte for byte (OGG files are kept when they decode identically) |

### Test results (exact)

`./gradlew :core:test` — **167 tests, 0 failures, 0 errors, 0 skipped**:

| Class | Tests | | Class | Tests |
|---|---|---|---|---|
| AnalysisTest | 11 | | LoadoutTest | 12 |
| DoombotBrainTest | 16 | | PersistenceTest | 13 |
| CooldownTest | 8 | | PowerGraphStressTest | 1 |
| ArmorEnergyTest | 13 | | PowerGraphTest | 12 |
| FlightControllerTest | 16 | | PresentationTest | 5 |
| ArcaneFocusTest | 6 | | ResearchTest | 11 |
| HeatModelTest | 8 | | AccessPolicyTest | 11 |
| ShieldModelTest | 11 | | DoomSuitTest | 13 |

Property/randomized tests among them: flight inputs (300 seeds x 1,500 ticks), loadout operations (500 seeds),
research play (200 seeds x 3,000 steps), bot worlds (300 seeds), delegation escalation (1,000 seeds), power
topology vs a union-find reference (200 seeds), corrupted save documents (2,000 seeds), animation-state selection
(20,000 states), energy conservation.

`python3 -m unittest discover -s art/tests` — **27 tests, 0 failures**.

Bugs the tests found and fixed this session: shield recharged while still raising; landings from powered
flight reported zero impact; GROUNDED could keep residual speed; bots could path toward an owner in another
dimension; shield capacity / spherical unlock and focus recovery stats were never applied by `DoomSuit`;
`easeInElastic` ended at 0 instead of 1; the hero-mask base texture and the mask item icon were written to the
same path (the icon silently overwrote it; now `doom_mask_hero*`, guarded by a test). The animation validator also caught 8 authored joint-limit
violations (wrist overshoot, impossible palm-up wrist, Doombot shoulders), all fixed before commit.

## 2. Authored, awaiting Minecraft / GeckoLib integration

These exist as files and pass every local check, but whether they look and behave right can only be known in game.

| Item | Open question to settle in game |
|---|---|
| Royal Armor model (56 bones, 75 cubes, 128x128) + 3 damage textures + glow masks (low / powered / arcane) | box-UV orientation and x-mirroring as GeckoLib applies them (previews use our emulation) |
| Doom mask hero asset (7 bones, 64x64, pristine / moderate / severe + low / powered / arcane glow) | display transforms for item, cradle and cut-in |
| Standard Doombot (26-bone reusable skeleton, 64x64, base / damaged / severe + 2 glow masks) | scale and hitbox |
| 39 Royal Armor clips (all 38 requested moves + cloak secondary motion baked into every clip), 16 Doombot clips, 3 mask clips | rotation sign conventions; GeckoLib easing semantics; root-bone clips need a player-animation hook |
| 28 sound events | in-game mix and categories |
| 55 HUD sprites + layout | drawing through the Fabric HUD API at every GUI scale |
| 10 particle types (31 sprites) | registration and emitters |
| 15 item icons, 5 blocks (14 face textures), vanilla-layout fallback armour texture | appearance in inventory and world |
| `presentation.Cue` / `ArmorAnimationSelector` | wiring to real events and renderers |

## 3. Specification or placeholder only

- `docs/VFX.md` + `vfx/effects.json`: emitter behaviour (counts, lifetimes, budgets, reduced-particle rules) — data only.
- `docs/HUD.md`: behaviour of each HUD element (blink rules, fades, compact layout) — spec only.
- `docs/MINECRAFT_26_1_2_INTEGRATION_MANIFEST.md`: 40 ordered steps — plan only.
- `mod/src/main/java/com/doomsovereign/mod/PACKAGES.md`: reserved package layout — no Java code.
- `mod/fabric.mod.json.template`: **unverified scaffolding** with unresolved `${...}` placeholders.
- Not designed yet: armour protection/durability values, the Time Platform, teleport safety rules, Doombot variants beyond Standard.

## 4. Blocked by unavailable dependencies

Java 25; Minecraft 26.1.2 client/server jars and metadata from Mojang; Fabric Loader, Loom and Fabric API
versions; GeckoLib 5.x for 26.1.2; therefore: any Fabric/GeckoLib code, `fabric.mod.json` values, dev client
and dedicated server launches, GameTests, in-game screenshots, the release JAR.

## Counts

### Source added this session (`doom-sovereign/`)

| Kind | Files | Lines |
|---|---|---|
| Java, main (`core/src/main/java`) | 89 | 4,987 |
| Java, tests (`core/src/test/java`) | 18 | 3,177 |
| Python generators + tests (`art/`) | 29 | 6,250 |
| Core data (`analysis/vanilla.json`, 16 creature profiles) | 1 | 624 |

### Shipped assets (`mod/src/main/resources`, 249 files, 2.9 MB)

| Type | Files |
|---|---|
| geometry (geo.json) | 3 |
| animation libraries (58 clips, 12,809 keyframes) | 3 |
| textures: armor | 12 |
| textures: entity (Doombot 9 + fallback equipment 2) | 11 |
| textures: item (15 icons + 12 hero-mask textures) | 27 |
| textures: block | 14 |
| textures: HUD sprites | 55 |
| textures: particle | 31 |
| mod icon | 1 |
| sounds (ogg) | 32 |
| sounds.json | 1 |
| item definitions | 20 |
| model JSON (15 item + 5 block) | 20 |
| blockstates | 5 |
| equipment asset | 1 |
| particle definitions | 10 |
| sprite metadata | 1 |
| VFX spec (json) | 1 |
| language | 1 |

Plus 20 preview images in `art/previews/` (not shipped) and 13 files in `docs/` (12 documents + `asset_counts.json`).

## Reference manifest

| Document | Content |
|---|---|
| `docs/MINECRAFT_26_1_2_INTEGRATION_MANIFEST.md` | ordered integration steps 1-40 |
| `docs/ROYAL_ARMOR_SKELETON.md` | the armour bone hierarchy: pivots, rest rotations, DOF limits, linked bones |
| `docs/DOOMBOT_SKELETON.md` | reusable Doombot skeleton |
| `docs/DOOM_MASK_RIG.md` | hero mask rig |
| `docs/ANIMATION_LIBRARY.md` | every clip with length, loop mode, keyframes, sounds, particles, cues |
| `docs/AUDIO.md` | every sound with design notes and measured loudness |
| `docs/HUD.md` | HUD layout at three GUI sizes and element behaviour |
| `docs/VFX.md` | 19 effects: colour, lifetime, count, size curve, motion, opacity, emission, budget, reduced mode |
| `docs/ART_DIRECTION.md` | palette (spec + derived) and pixel-art rules |
| `docs/ASSET_MANIFEST.md` | every shipped file with type, size, sha1 prefix |
| `docs/PERFORMANCE_CORE.md` | power-network timings |
| `mod/README.md` | what the mod module contains and how it was checked |
| `art/audio_report.json` | machine-readable audio measurements |

## Known limitations (honest list)

- The cloak's secondary motion is **baked** into each clip; there is no runtime cloth simulation.
- The eye-glow bone only scales the flare planes; fully dimming the eyes needs the renderer's glow-mask swap.
- Clips that move root bones need the player model to be posed too (a player-animation hook) — otherwise only child bones move.
- The 20,000-separate-networks power case takes ~186 ms per tick on the build machine (over budget); normal play is far smaller, but round-robin ticking is not implemented.
- The weakest icons are `royal_boots` and `latverian_alloy` (legible, not polished).
- Preview renders use our emulation of GeckoLib's transforms; parity is unverified.
