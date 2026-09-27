# Reserved package layout (no code yet)

No Java source exists under `com.doomsovereign.mod`: it would have to be written against Minecraft,
Fabric API and GeckoLib classes that could not be resolved in this session. The layout below is the
plan the integration manifest follows; each package only adapts `com.doomsovereign.core` (the tested
pure-Java domain) to the game.

| Package | Side | Responsibility | Core types it adapts |
|---|---|---|---|
| `mod` | common | entrypoint, registries (items, blocks, block entities, entities, sounds, particles, data components) | — |
| `mod.armor` | common | Royal Armor items, equipment assets, Doom Mode detection, per-player `DoomSuit` attachment | `suit.DoomSuit`, `api.ArmorRuntimeAdapter` |
| `mod.flight` | common | server flight tick, velocity application, fall-damage suppression | `flight.FlightController`, `api.FlightEnvironment` |
| `mod.combat` | common | gauntlet projectiles/beam raycast, force-field damage hook, melee | `shield.ShieldModel`, `heat.HeatModel`, `api.ShieldDamageContext` |
| `mod.analysis` | common | scan raycast, observation events, datapack profile loader (`data/<ns>/doom_analysis/*.json`) | `analysis.*` |
| `mod.research` | common | event listeners feeding `ResearchEvent`s, Research Console block entity | `research.*` |
| `mod.bot` | common | Doombot entity, goals that execute `BotIntent`s, control device | `bot.DoombotBrain`, `api.BotWorldAdapter` |
| `mod.power` | common | power block entities registered into one `PowerGraph` per level | `power.PowerGraph`, `api.PowerNodeAdapter` |
| `mod.security` | common | secured blocks, permission UI server side | `security.*` |
| `mod.persist` | common | player attachment + SavedData using the JSON codecs | `persist.*` |
| `mod.net` | common | payloads: input (client -> server), suit state and cues (server -> client) | `presentation.Cue` |
| `client.render` | client | GeckoLib armor/entity renderers, glow layers, flight lean/roll | `presentation.ArmorAnimationSelector` |
| `client.hud` | client | HUD layer using `textures/gui/sprites/hud/*` and docs/HUD.md layout | — |
| `client.fx` | client | particle providers and emitters reading `vfx/effects.json` | — |
| `gametest` | test | GameTests listed in the integration manifest | — |
