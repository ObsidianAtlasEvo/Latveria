# Minecraft 26.1.2 integration manifest

The ordered path from what exists in this repository (a tested pure-Java core and a generated
asset tree) to a playable Fabric mod. **None of these steps has been performed.** They were
blocked in this session because `maven.fabricmc.net`, `meta.fabricmc.net`, the Mojang
piston/launcher/library hosts, GeckoLib's Maven host, Modrinth and the JDK 25 download hosts were
unreachable.

Each step says what to use from this repository, what to do, and how to know it worked. Do them in
order: every step assumes the previous one passes.

Already verified offline (from the misode/mcmeta mirror of the 26.1.2 client and data, fetched in
this session): release `26.1.2`, data version 4790, protocol 775, **resource pack format 84**,
**data pack format 101.1**; formats of `items/*.json`, `models/item` with `minecraft:item/generated`,
`block/orientable`, facing blockstates, `equipment/*.json` with `humanoid`/`humanoid_leggings`
layers, 64x32 equipment textures, `nine_slice` GUI sprite metadata, and `particles/*.json`.

---

## Part A — toolchain and an empty mod

**1. Install Java 25.** Install a JDK 25 build; `java -version` must report 25. Keep JDK 21 available:
the `core` module is written in Java 21 syntax and must keep compiling on both.
*Pass:* `./gradlew :core:test` passes on JDK 25 (167 tests, 0 failures, 0 skipped).

**2. Verify Minecraft 26.1.2 metadata.** Read `https://piston-meta.mojang.com/mc/game/version_manifest_v2.json`,
follow the 26.1.2 entry, and record: required `javaVersion.majorVersion`, client/server jar SHA-1,
and asset index id. Compare with the mcmeta values above (the mirror also lists SHA-1
`dd6fd47eec3ac2d46b4f805e003f1a421ed8a3f7`; confirm which artefact it describes).
*Pass:* a short note in this file with the recorded values; any mismatch with "resource 84 / data 101.1" is investigated first.

**3. Lock the Fabric Loader version.** Query `https://meta.fabricmc.net/v2/versions/loader/26.1.2`,
choose the newest stable loader, write it into `gradle.properties` (`loader_version`).
*Pass:* the version resolves from `maven.fabricmc.net`.

**4. Lock Fabric Loom.** Pick the Loom release that supports 26.1.2 and check its Gradle
requirement; the wrapper here is Gradle 8.14.3 (`gradle/wrapper/gradle-wrapper.properties`) — upgrade it
with `./gradlew wrapper --gradle-version <x>` if Loom needs newer.
*Pass:* `./gradlew help` configures with Loom applied.

**5. Lock Fabric API.** Choose the Fabric API build for 26.1.2 (`fabric_api_version`).
*Pass:* resolves; list the Fabric API modules actually used (networking, attachments, HUD, rendering, events, GameTest).

**6. Lock GeckoLib.** The directive names GeckoLib 5.5.2: confirm that build exists for Fabric 26.1.2
(or pick the closest supported one) and record it. Read its docs for: asset folder layout, armor renderer
bone naming, glow-mask convention, supported easing names, keyframe JSON keys.
*Pass:* a table in this file mapping each assumption in `mod/README.md` and `docs/ANIMATION_LIBRARY.md` to "confirmed" or "changed".

**7. Empty mod builds.** Create `mod/build.gradle` (Loom), add `include 'mod'` to `settings.gradle`,
depend on `project(':core')` and embed it (jar-in-jar). Fill `mod/fabric.mod.json.template` placeholders,
move it to `mod/src/main/resources/fabric.mod.json`, add an entrypoint class that only logs.
Gson is provided by Minecraft, so `core` adds no runtime library.
*Pass:* `./gradlew :mod:build` produces a jar; `./gradlew :core:test` still passes.

**8. Dev client starts.** `./gradlew :mod:runClient`.
*Pass:* title screen reached; log has no errors for `doom_sovereign:` resources (missing textures,
models, sounds, bad JSON); `/give @s doom_sovereign:doom_mask` shows the icon and the English name from `lang/en_us.json`.

**9. Dedicated server starts.** `./gradlew :mod:runServer`.
*Pass:* server starts and a client joins; no client-only class is loaded on the server (`core` has no
Minecraft classes at all, so only `mod` code can break this).

## Part B — the armour

**10. Register the Royal Armor.** Items `doom_mask`, `royal_chestplate`, `royal_leggings`, `royal_boots`
with the equipment asset `doom_sovereign:royal` (`equipment/royal.json`, already present). Decide armour
values and durability (not specified anywhere yet — add them to the core as data).
*Pass:* wearing all four shows the vanilla-layout fallback texture (`textures/entity/equipment/*/royal.png`).

**11. GeckoLib geometry and textures.** Register a GeckoLib armor renderer using
`geckolib/models/armor/royal_armor.geo.json` and `textures/armor/royal_armor.png`; add the glow layer with
`royal_armor_glowmask.png`. Map GeckoLib's armor bones to the roots documented in
`docs/ROYAL_ARMOR_SKELETON.md`.
*Pass:* in-game screenshots from front, back and both sides match `art/previews/royal_armor_turnaround.png`
(same silhouette, no mirrored faces, mask on the front, cloak on the back, green eyes glowing). If faces are
mirrored or swapped, fix it once in `art/doomart/geo.py` / `render.py` conventions and rebuild — do not hand-edit JSON.

**12. Validate the animation JSON in GeckoLib.** Load `royal_armor.animation.json`; play
`animation.royal_armor.gauntlet_aim`.
*Pass:* the right arm points forward with the palm lens facing the target. If the arm swings backward or
outward, the sign convention differs: flip it in `art/doomart/anim.py` export (one place) and rebuild.
Then play every clip once (a debug command) and confirm no parse warnings, loops loop without pops, and
`hold_on_last_frame` clips hold.

**13. Doom Mode.** Attach one `core.suit.DoomSuit` per player (Fabric data attachment), tick it on the
server every tick with an `ArmorRuntimeAdapter`. On INITIALISING play `ArmorAnimationSelector.select(...)`
(`armor_initialization` first time, `mask_seal` after).
*Pass:* equip all four pieces -> 50-tick first sequence, later equips 14 ticks; removing one piece -> shutdown clip; HUD appears only in Doom Mode.

**14. Armor Energy.** Server-authoritative `ArmorEnergy`; sync stored/capacity/status to the owning client
at most every 5 ticks or on status change. Charging from the Armor Cradle uses `RechargeSource`.
*Pass:* energy survives relog (step 30) and never desyncs by more than one sync interval.

**15. Packets.** C2S: key states only (flight toggle edge, movement axes, boost, fire, ability select) —
never positions or results. S2C: suit state snapshot + `presentation.Cue` events (id + locator).
*Pass:* a modified client that sends "fire" every tick is still limited by cooldown and heat (server checks).

**16. HUD.** Draw the layer described in `docs/HUD.md` with the sprites in `textures/gui/sprites/hud/`.
*Pass:* screenshots at 1920x1080 GUI 4, 1280x720 GUI 3 and 640x480 GUI 2 match `art/previews/hud_mockup_*.png`;
the compact layout engages below 376 GUI px width.

**17. Gauntlet blast.** Server raycast/projectile from the palm locator; `DoomSuit.fireBolt / releaseCharge /
startBeam`; damage from `ShotResult`; cues `BOLT_LEFT/RIGHT`, `CHARGED_RELEASE`, `BEAM_START`.
*Pass:* the heat throttles damage then locks out (as in `DoomSuitTest.sustainedFireOverheatsAndThrottles`).

**18. Force field.** Hook incoming damage, map the damage source to `ShieldDamageContext.DamageKind` and a
bearing relative to the wearer's facing, call `ShieldModel.absorb`, apply `passedThrough`.
*Pass:* arrows from the front are absorbed and paid for in energy, from behind they are not (directional mode).

**19. Flight.** Each server tick build a `FlightEnvironment` from the player, call `FlightController.tick`,
rotate the local-frame velocities by yaw and apply them; override gravity when `overridesGravity()`; reset
fall distance while powered; apply `leanDegrees`/`rollDegrees` to the player render.
*Pass:* take-off, hover, cruise, boost (only with the Mk II thruster), brake, disengage, landing and fall arrest
behave as in `FlightControllerTest`; the server does not reject the movement ("moved too quickly") — if it
does, document the exact fix.

**20. Remote player rendering.** Other players see the same base clip (`ArmorAnimationSelector`) and cues.
Root-bone clips need the player model to take the pose too: add a player-animation hook (mixin or library).
*Pass:* two clients side by side see each other's walk, hover, blasts and cloak.

## Part C — Doombots

**21. Standard Doombot entity.** Register the entity with `geckolib/models/entity/doombot_standard.geo.json`,
`textures/entity/doombot/*.png`, glow layer, and `doombot.animation.json`.
*Pass:* renders matching `art/previews/doombot_standard.png`; damaged textures swap at health thresholds.

**22. Doombot AI.** Goals execute `DoombotBrain.decide` intents every 5-10 ticks from a cached
`BotWorldAdapter`; orders arrive through the control device and `issue(...)` (permissions via `AccessPolicy`);
the registry persists through `WorldDataCodec` in level SavedData.
*Pass:* follow / stay / patrol / defend / attack / return-home work; bots never attack the owner or trusted
players; PvP only when enabled; bots never path into another dimension.

**23. GameTests.** Port the pure tests' scenarios into Fabric GameTests: Doom Mode activation; energy never
negative across a flight; shield absorbs from the front only; heat lockout; fall arrest prevents fatal
fall damage; bot follow/teleport; bot refuses to attack its owner; power network split/merge when a conduit
block is broken and replaced; persistence round trip across a server restart; v1 save migrates.
*Pass:* `./gradlew :mod:runGametest` green on a dedicated server.

**24. Release JAR.** Build, check the jar contains `core` (jar-in-jar) and all generated assets
(`docs/ASSET_MANIFEST.md` lists 249 files), test in a clean 26.1.2 instance with only Fabric API and GeckoLib.
*Pass:* clean-instance play session with the checklist in step 40.

## Part D — the rest of the offline material

**25. Power network.** One `PowerGraph` per level; block entities implement `PowerNodeAdapter`; connect on
load / neighbour change, remove on unload. Tick all networks once per server tick.
*Pass:* in-game cost measured with a profiler is in line with `docs/PERFORMANCE_CORE.md` (4 ms median for
100k nodes on the build machine); the 20,000-network case is known to exceed a tick (see that doc).

**26. Machines.** Register the five blocks (`doom_forge`, `armor_cradle`, `power_core_block`,
`doombot_assembly_station`, `research_console`) with the provided blockstates/models/textures; facing property
must be named `facing` with north/east/south/west values to match the blockstates.
*Pass:* placed blocks face the player and show the front texture.

**27. Research.** Feed `ResearchEvent`s from item pickups, crafting, advancements, structure entry, boss kills,
dimension changes; the Research Console ticks `ResearchProgress.tickConsole()` while powered and attended.
*Pass:* the 22 nodes of `DoomResearch.standard()` are reachable in survival.

**28. Doom Analysis.** Scan raycast -> `AnalysisLedger.observe`; load extra profiles from datapacks at
`data/<namespace>/doom_analysis/*.json` using `ProfileRegistry.load` (defaults ship in the core jar).
*Pass:* scanning a blaze reveals vitals first, fire immunity only after watching it attack; HUD scan panel shows it.

**29. Modules and frames.** Armor Cradle UI over `Loadout.check/install/remove`, showing `LoadoutIssue` text.
*Pass:* every refusal in `LoadoutTest` has a readable UI message.

**30. Persistence.** Player data via `PlayerDataCodec` in a player attachment (JSON string or NBT wrapper);
world data via `WorldDataCodec` in SavedData.
*Pass:* relog, server restart, and loading a hand-written v1 document all restore state; corrupt fields log
warnings instead of crashing.

**31. Security.** Secured blocks store an `AccessPolicy`; turrets and doors use `EngagementRules` and
`AccessPolicy.can`; admin override only when the server config enables it.

**32. Sorcery.** Spells over `ArcaneFocus` (instant and channelled with interruption), cues `SPELL_CAST`,
`RITUAL`, `TELEPORT`; teleport safety checks (solid floor, no suffocation) are Minecraft-side work still to design.

**33. Audio.** Register the 28 sound events from `sounds.json`; set categories as listed in `docs/AUDIO.md`;
loops (`flight.loop`, `gauntlet.beam_loop`, `field.hum`, `sorcery.ritual_resonance`) as moving/looping sound
instances. *Pass:* listen test: no clipping, loops seamless, subtitles show.

**34. VFX.** Register the 10 particle types (`particles/*.json`), then emitters that read
`vfx/effects.json` (counts, lifetimes, budgets, reduced-particle rules). *Pass:* frame time with all effects
on screen; Minimal particle setting keeps every effect's non-particle fallback.

**35. Hero mask.** Item display and Armor Cradle close-up using `geckolib/models/item/doom_mask.geo.json`,
`textures/item/doom_mask_hero*.png` and `doom_mask.animation.json` (`lock`, `display_idle`, `power_down`).

**36. Damage and glow states in the renderer.** Choose `royal_armor`, `_damaged_moderate` or
`_damaged_severe` by armour durability; choose the glow mask `_low` / default / `_arcane` / none by energy
status, Doom Mode and active sorcery.

**37. Time Platform.** Not designed beyond research node `temporal_mechanics`, two sounds and one VFX
entry. Needs a design document before code.

**38. Configuration.** Server config: PvP for bots, admin override, flight speed multipliers, particle caps;
client config: HUD scale offset, reduced flashing (disables the 2 Hz blink, keeps shapes), mask vignette (off).

**39. Latveria centre.** `/doom latveria setcenter` stores `WorldDoomData.latveriaCenter` (optional, never
hard-coded). Integration with the existing Latveria build scripts (`windows/`) is non-destructive: the mod
never edits blocks it did not place.

**40. Release checklist.** Two-client multiplayer session (flight, blasts, field, bots, sorcery); relog;
restart; low-end machine frame time; all four GUI scales; subtitles on; reduced particles; English strings
complete; license and credits (all art and audio original, generated by `art/`).

---

## Offline material -> step

| Material | Where | Step(s) |
|---|---|---|
| Pure-Java domain + 167 tests | `core/` | 1, 7, 13-19, 22, 25, 27-32 |
| Presentation catalog + animation selector | `core/.../presentation` | 13, 15, 17, 20 |
| Royal Armor geometry, textures, glow masks | `mod/.../geckolib/models/armor`, `textures/armor` | 11, 36 |
| Royal Armor clips (39) | `geckolib/animations/armor` | 12, 13, 20 |
| Hero mask (6 states, 3 clips) | `geckolib/models/item`, `textures/item/doom_mask_hero*` | 35, 36 |
| Standard Doombot (model, 9 textures, 16 clips) | `geckolib/models/entity`, `textures/entity/doombot` | 21, 22 |
| Sounds (32 files / 28 events) | `sounds/`, `sounds.json` | 33 |
| HUD sprites (55) + layout | `textures/gui/sprites/hud`, `docs/HUD.md` | 16 |
| Item icons, block textures, JSON | `textures/item`, `textures/block`, `items`, `models`, `blockstates` | 8, 10, 26 |
| Particles (10 types) + VFX spec | `particles`, `textures/particle`, `vfx/effects.json`, `docs/VFX.md` | 34 |
| Fallback equipment texture | `equipment/royal.json`, `textures/entity/equipment` | 10 |
| Language file | `lang/en_us.json` | 8 |
| Unverified `fabric.mod.json` template | `mod/fabric.mod.json.template` | 7 |
