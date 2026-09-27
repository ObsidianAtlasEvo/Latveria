# Latveria — Castle Doom & Doomstadt for Minecraft Java 26.1.2

A complete, survival-functional Latverian capital: **Castle Doom** on its crag and the walled
town of **Doomstadt** beneath it. It covers about 300 × 365 blocks, and the Doom Tower's
beacon stands about 100 blocks above the plaza. The whole thing is built by a Windows script
that types the construction commands into Minecraft's chat for you, one at a time and at a
gentle pace. You need **no server files, datapacks or mods**, only operator permission.

![South elevation](docs/preview_south.png)

| Top-down plan | East elevation |
|---|---|
| ![Plan](docs/preview_top.png) | ![East](docs/preview_east.png) |

*(These previews are rendered from the actual command list by `generator/preview.py`.)*

---

## Quick start (Windows)

1. **Back up your world.** Everything in the build area is replaced.
2. In Minecraft, pick a **flat, dry spot**. Castle Doom will rise about 70–250 blocks
   **north** (−Z) of you; the town spreads about 110 blocks south and 150 blocks east and west.
3. Stand on the block that will be the **centre of the plaza**. Press **F3** and read the
   `Block:` line (the block your feet are in), e.g. `Block: 120 68 -340`.
4. Make sure you are an **operator** (on a server) or have **cheats on** (single player).
   Creative mode is recommended.
5. Double-click **`windows/Build-Latveria.bat`**, type the three numbers, press Enter,
   then **click back into Minecraft** and leave the keyboard and mouse alone.

The script lifts you onto a glass viewing platform 80 blocks above the plaza and turns off
mob spawning and command spam for the duration. It force-loads the site, waits a minute for
chunks to generate, then builds in 56 named stages while an action-bar message shows progress.
When it finishes, it populates the town, cleans up, restores the game rules and sets you down
in front of the Colossus of Doom.

| Control | Effect |
|---|---|
| **F7** | pause / resume |
| **F10** | stop (progress is saved; run the `.bat` again to resume) |
| click away from Minecraft | pauses automatically, so it can never type into another program |

**Duration:** about 23,400 commands take roughly **75–85 minutes** at the default speed.

### Tuning

Run `Build-Latveria.bat` with parameters (or call the `.ps1` directly):

| Parameter | Default | Use |
|---|---|---|
| `-DelayMs 150` | 60 | pause after every command; raise on a slow or busy server |
| `-ChatOpenMs 150` | 80 | wait after opening chat; raise if some commands go missing |
| `-HeavyFactor 2` | 1.0 | lengthen the extra pauses after big fills |
| `-ChatKey /` | T | if you rebound the chat key |
| `-WindowMatch "Lunar"` | Minecraft | text in your game window's title (for other launchers/clients) |
| `-FromSection "Doom Tower"` | | rebuild from a named stage (list below) |
| `-DryRun` | | only write `latveria_resolved.txt` with the real coordinates, to inspect |

### Troubleshooting

* **Nothing appears or chat opens but stays empty:** raise `-ChatOpenMs`. Check that the chat
  key is T and that no menu or inventory is open.
* **Some areas are missing:** the chunks weren't generated yet when those commands ran. Re-run
  with `-FromSection "<stage name>"`. The site stays force-loaded until the final stage.
* **Kicked for spam** (some Spigot/Paper setups): make sure you are op, or raise `-DelayMs`.
* **"Too many blocks" errors:** the server lowered the `max_block_modifications` game rule.
  Set it back to 32768 or higher.
* The centre's Y must be between −52 and 189 so the dungeons and the top of the Doom Tower fit.

---

## What gets built

### Castle Doom (north, on a 12-block crag)
* **The crag**: a rugged, layered outcrop of stone, tuff and deepslate, dressed with turf, moss
  and pines.
* **Moat and drawbridge**: a 5-wide stone-lined moat with lily pads, crossed by a timber
  drawbridge with lifting chains.
* **Grand Stair of Doom**: a 15-wide ceremonial ramp from the town up the crag, lined with
  lamp pillars and Doom's banners.
* **Curtain walls**: deepslate-brick walls, 105 × 97 blocks and 17 high, with a walkable
  crenellated wall walk, hanging green banners and courtyard stairways.
* **Towers**: four great round corner towers with 20-block oxidized-copper spires, three
  square wall towers with hipped copper roofs, and two drum towers at the gate. Every tower
  has ladders, floors, beds, chests, fletching and cartography tables, and arrow loops.
* **Gatehouse**: a pointed-arch passage with raised portcullises, murder-hole grates, a guard
  room with dispenser and beds, and an iron-and-green **Doom mask relief** over the gate.
* **Courtyard**: the Fountain of Doom (a 16-block statue), lamp-lit processional way, **royal
  stables** (six saddled, named horses), **forge** (lava hearth, anvils, blast furnaces),
  **barracks** of the Latverian Guard (two floors of bunks), a **Doombot proving ground**, and
  **Cynthia von Doom's memorial garden and mausoleum** with a book of remembrance and an
  amethyst sorcery circle.
* **The Keep** (61 × 47 blocks, four storeys and a roof):
  * **Throne Room**: 15 blocks high with pillars and banners, iron chandeliers, a Doombot
    honour guard, a three-step dais, a blackstone-and-emerald throne between soul-fire
    braziers, and a **13 × 11 stained-glass window of Doom's mask** behind it.
  * Kitchens, dining hall, armoury (iron, diamond, netherite and chainmail suits), guard room.
  * **Library of Sorcery**: bookshelf stacks, a working 15-shelf enchanting alcove, brewing
    stands, and the *Latverian Codex* and Cynthia's *Of the Dark Arts* on lecterns.
  * **Doom's laboratory**: crafter, smithing table, blast furnace, lit redstone consoles, an
    unfinished Doombot on the operating slab, an ender chest, and ancient-city loot.
  * **Gallery of Conquest**: trophies in glow item frames, and a door to **Doom's balcony**
    above the courtyard.
  * **Doom's private chambers**: canopy bed, fireplace, wardrobe of armours, his journal.
    Also the **war room**, with a great map table.
  * **Dungeons**: prison cells with iron doors, the **crypt of the Midsummer portal** (a lit
    Nether portal, since Doom descends each year to fight Mephisto for his mother's soul),
    the **treasury** (gold, emeralds, diamond blocks, end-city and bastion loot), the
    **Doombot factory**, and **Doom's Time Platform** chamber.
  * Two mirrored stairwells link every level, from the dungeon to the roof.
* **The Doom Tower**: rises from the keep roof to Y+100, with seven floors reached by ladder
  (sentinels, the enchanted *Armour of Doom*, alchemy, astronomy, the watch, a great bell).
  It is crowned by copper-tipped pinnacles and a working **Beacon of Doom** whose beam shines
  green through tinted glass.

### Doomstadt (south)
* **The Plaza of Doom**: a radial stone plaza with a fountain moat, market stalls, benches,
  lamp ring and the village bell. In the centre stands the **32-block Colossus of Victor von
  Doom**: hood, iron mask with glowing green eyes, tunic, belt, gauntlets and flowing cloak.
* **Cathedral of Doomstadt**: a cross-shaped nave with a transept, stained-glass lancets, a
  rose window, pews and an altar. It has a copper **onion dome** and a west bell tower with a
  working bell.
* **Rathaus**: the town hall, with a council chamber, archives and a **clock tower** (working
  clocks in its faces).
* About 90 timber-framed houses in six Carpathian palettes, many two-storey. Each has a bed,
  a chest of village loot, a crafting table, a job-site block, lanterns, a smoking chimney
  and a resident villager.
* Named shops: *The Iron Mask* tavern & inn, the Forge (armourer and weaponsmith), toolsmith,
  bakery, the **Werner von Doom Memorial Clinic**, library & school, stonemason, tannery,
  fishmonger.
* **Doombot garrison**: Doombot sentries in formation at the foot of the Grand Stair.
* **Farms**: five fenced fields of ripe wheat, carrots, potatoes and beetroot with irrigation,
  composters and scarecrows. Also pastures of cows, sheep, pigs, chickens and horses.
* **Werner's Camp**: four painted Romani vardo wagons around a campfire, and a memorial stone
  to Werner von Doom, the healer.
* An orchard, an apiary with beehives and a flower meadow, and a fishing pond with a jetty.
* **Town walls**: 10-block walls with a wall walk and ladders, 20 copper-capped turrets, and
  west, east and south gates with portcullises and signs.
* **Life**: over 100 villagers (every profession, with Latverian names), ten iron-golem
  "Doombots", black cats, horses, livestock and bees.

### Landmarks (offsets from your centre block)

| Place | X | Y | Z |
|---|---|---|---|
| Colossus of Doom / plaza | 0 | 0 | 0 |
| Foot of the Grand Stair | 0 | 0 | −70 |
| Castle gate | 0 | 12 | −106 |
| Throne | 0 | 15 | −190 |
| Library / laboratory | −15 / 15 | 28 | −180 |
| Doom's chambers | −14 | 38 | −183 |
| Midsummer portal (dungeon) | 0 | 2 | −157 |
| Beacon of Doom | 0 | 101 | −174 |
| Cathedral doors | 52 | 0 | −20 |
| Rathaus | −26 | 0 | −28 |
| Werner's Camp | −123 | 0 | 60 |

### Build stages
`Preparing the site`, `Clearing the land`, `Levelling the valley`, `Raising the crag`,
`Dressing the crag`, `Cutting the moat`, `The Grand Stair`, `Raising the curtain walls`,
`Wall-walk stairways`, `Corner towers`, `Wall towers`, `The Gatehouse`, `Drawbridge`,
`Courtyard`, `Royal stables`, `The castle forge`, `Barracks`, `Memorial garden`,
`Doombot proving ground`, `The Keep: raising the shell`, `The Keep: facade`,
`The Keep: grand entrance`, `The Throne Room`, `Kitchens`, `Armoury`, `Library of Sorcery`,
`Doom's laboratory`, `Gallery of Conquest`, `Doom's private chambers`, `The war room`,
`The dungeons`, `The prison`, `The crypt`, `The treasury`, `The Doombot factory`,
`Time Platform`, `The Keep: stairwells`, `The Doom Tower`, `Crown of the Doom Tower`,
`Paving the streets`, `The Plaza of Doom`, `The walls of Doomstadt`, `Cathedral`, `Rathaus`,
`Houses of the north quarter`, `Doombot garrison`, `Library and mason's quarter`,
`Houses of the upper town`, `Houses of the lower town`, `Houses of the south quarter`,
`Fields and pastures`, `Animal pens`, `Werner's Camp`, `Orchard, apiary and pond`,
`Bringing Doomstadt to life`, `Final sweep`.

---

## How it works

```
generator/          Python generator (no dependencies) + optional preview/verify tools
  build.py          -> writes windows/latveria_commands.txt
  core.py           command engine: validation, chat-length splitting, coordinate tokens
  terrain.py        clearing, crag, moat, Grand Stair
  castle.py         walls, towers, gatehouse, courtyard buildings
  keep.py           the keep, dungeons and Doom Tower
  village.py        Doomstadt
  statue.py         the voxel statue of Doom
  preview.py        renders docs/*.png from the command list      (needs numpy, pillow)
  verify.py         replays the build and checks supports/entities (needs numpy)
  mcdata/           Minecraft 26.1.2 block states and registries (from the game's data)
windows/
  Build-Latveria.bat / .ps1   the chat sender
  latveria_commands.txt       the generated build (23,415 commands)
```

* **Chat-safe:** Minecraft's chat box takes 256 characters. The generator splits anything
  longer. Chest contents go in one slot at a time with `/item replace`. Banner patterns,
  book pages and sign lines are added with `/data modify`. Armour-stand gear is equipped with
  `/item replace entity`. Every line is checked against the limit, assuming worst-case
  coordinate widths.
* **Location-independent:** coordinates are stored as offsets (`$x(12) $y(-3) $z(150)`) and
  turned into absolute numbers by the sender from the centre you type in. Moving, falling or
  teleporting during the build has no effect.
* **Checked against 26.1.2:** every block state is checked against the 26.1.2 block registry,
  and every item, entity, loot table, banner pattern and tree feature against its registry.
  Multi-block pieces (doors, beds, tall flowers) are placed with `strict` so their halves
  survive. `verify.py` replays all 1.58 million placed blocks and confirms that every ladder,
  torch, banner, sign, lantern, lever, crop, bed and door is supported, and that no mob spawns
  inside a block.
* **The sender** uses the Win32 `SendInput` API. For each command it presses the chat key,
  pastes with Ctrl+V and presses Enter, adding extra time after large fills. It only ever
  types while a window whose title contains "Minecraft" is in front.

To change the design, edit the Python files and run `python generator/build.py`. Optionally
run `python generator/verify.py` and `python generator/preview.py` too.
