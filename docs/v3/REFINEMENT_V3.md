# Latveria Refinement v3

The fourth command file. It is an **additive** layer over the finished world: it runs after the
main build, Survival Expansion v2 and the Lighting Overhaul, and it changes nothing in those
three files.

| | |
|---|---|
| Command file | `windows/latveria_refinement_v3_commands.txt` |
| Launcher | `windows/Build-Latveria-Refinement-V3.bat` (preset centre **799 70 −10090**, override with `-Centre "x y z"`) |
| Sender | `windows/Build-Latveria-Refinement-V3.ps1` (a copy of the original sender with additive-mode resume and section runs) |
| Commands | **2,581** in **59 sections** |
| Estimated run time | about **15 minutes** at the default pace, of which 5.8 minutes are chunk-loading waits after each teleport |
| Optional extra | `windows/Reset-Nursery-Beds-V3.bat` → `latveria_v3_nursery_reset_commands.txt` (38 commands) |
| Generator | `generator/build_refinement.py` + `v3core.py`, `v3_golem.py`, `v3_castle.py`, `v3_secrets.py`, `v3_city.py`, `v3_districts.py` |
| Simulator | `generator/sim.py`, extended: entities, `keep`, `execute if/unless`, guarded summons, `tp` of named entities |
| Verifier | `generator/verify3.py` |
| Renderer | `generator/render3.py` + `generator/audit3.py` (`--after` for the post-v3 set) |

Before running v3, read [AUDIT.md](AUDIT.md). The numbers are in [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md).

## How to run it

1. Make sure the first three layers have finished. Stand anywhere in the world, in **creative or
   spectator** mode, with render distance **10 chunks or more**.
2. Double-click **`windows/Build-Latveria-Refinement-V3.bat`** and confirm the centre.
3. Click into Minecraft. The sender teleports you to each district in turn (`tp @s …`), waits 6 s
   for its chunks, and then builds. F7 pauses and resumes, F10 stops, and alt-tabbing pauses.

Chat will show each command's feedback. An occasional **"No blocks were filled"** or **"Could not
set the block"** is expected and harmless. It means the spot already held something (for
example, the Golem Works troughs are filled with `replace water` and then `replace air`, so one of
the two finds nothing), or you have changed it since, so v3 left it alone. Commands the model
already knew would change nothing were removed from the file.

Options (add them after the `.bat` name, or use them with the `.ps1`):

| Option | Effect |
|---|---|
| `-ListSections` | Prints the section titles and exits. |
| `-Section "Golem"` | Runs only the sections whose title contains that text. Each one starts with its own teleport. |
| `-FromSection "Market"` | Starts at that section and continues to the end. |
| `-DryRun` | Writes `latveria_resolved.txt` with the real coordinates and types nothing. |
| `-Centre "x y z"` | Uses another centre. |

## The safety rules every command follows

There are no gamerules, no forceloads, no kills, no `clone` and no unguarded `setblock` or `fill`.
`verify3.py` checks every one of the 2,581 lines against this list:

| Form | Used for | Count |
|---|---|---|
| `setblock … keep` | every new single block (only into air) | 902 |
| `fill … keep` | every new volume (only into air cells) | 685 |
| `fill … <new> replace <old>` | swaps: the change happens only where the expected old block still stands. Carving the crag for new rooms uses `air replace <stone/dirt/andesite/…>`, after the model confirmed the volume holds nothing else. | 738 |
| `execute if block A air if block B air run setblock A … strict` (+ second half) | doors, beds and double chests, only when both cells are free | 46 |
| `execute unless entity @e[tag=lv3_<id>] run summon …` | the 8 new entities, each summoned once | 8 |
| `execute unless entity @e[type=…,name="…"] run summon …` | re-summons the Golem Works crew or the nursery adults only if one is missing | 7 |
| `execute unless items block … container.N * run item replace …` | stocks a slot only while it is empty | 44 |
| `data modify block <v3 lectern> … pages[i] set value …` | lectern pages, set by index (never appended) | 20 |
| `tp @s`, `title @s`, `tag @e[tag=lv3_…] add lv3`, `item replace entity @e[tag=lv3_…]` | harmless | 131 |

The generator adds its own checks on top:
* **Whole pieces or nothing.** A decoration that is several blocks, such as a stall or a desk, is
  checked against the model first. If any of its cells is occupied, or an animal or villager
  stands there, the whole piece is left out, so nothing is ever half-built.
* **Protected volume.** The Doombot factory room cannot be written to; any attempt stops the build.
* **Reach.** Every write lies within 128 blocks of its section's teleport point, and every entity
  selector within 96, so its chunks and entities are loaded.
* **No new darkness.** After each section, any spawnable surface it created at block light 0
  (a roof, a stall top, a hay rick) is lit using the Lighting Overhaul's own rules. New rooms are
  lit to at least light 8.

## Resume and re-running

* The launcher saves progress **after every command** (`latveria_refinement_v3_progress.txt`).
  On resume it repeats the last command sent, which is harmless because every command is
  idempotent, and it first repeats the current section's teleport and wait, so the chunks are
  loaded again.
* **Every section is independent and safe to run again** (`-Section "…"`). Blocks already in
  place are skipped (`keep`), swaps find nothing left to swap, tagged entities are not summoned a
  second time, container slots that have items are not refilled, and lectern pages are rewritten
  with the same text. The verifier proves this by replaying the whole layer twice: **the second
  replay changes 0 blocks and adds 0 entities.**
* Entity guards only see **loaded** entities, so let each section start with its own teleport (the
  launcher always does). Do not paste single v3 commands by hand far from their district.

## What v3 changes

### Golem Works: the mandatory fix

The v2 farm had four faults (see the audit). The rework makes these changes in place:

1. **The pads are flushed and flooded.** The four channel troughs are filled flush with stone
   bricks. Then 68 water sources are laid along the inner edge of the rim at walking level
   (y 5). Water spreads 7 cells, and from every edge the shaft is 8 cells away, so every pad cell
   is flowing water pushing toward the 2×2 shaft, and the level-7 ring stops at the shaft's edge.
   The shaft stays dry, and the lava blade and hoppers are untouched. A golem's feet may be in
   water when it spawns, since the obstruction check allows fluid in the feet cell only.
2. **The pod floors are glass.** Golem spawning uses the legacy iron-golem rule: the spawn
   cell must be air or liquid, and the block below must be solid, not glass. There is no width
   check. So any attempt landing over the pod now falls through the glass to the pad beneath,
   where there are 2.7 clear blocks. The verifier simulates every attempt from every villager
   cell (±8 horizontally, from 6 above to 6 below). **All 2,204 attempts that find a spot land on
   the flooded pad.** 100 find no valid spot (the glass rim and roof), and 8 are obstructed.
   **None lands in the pod, the zombie cell, the shaft, on the rim or on a roof.**
3. **Line of sight is controlled.** The partition between the villagers and the zombie (x 255)
   is now opaque stone brick, with exactly **one window, one block high**, at the villagers' eye
   level (255, 10, −89). A villager (1.95 tall) cannot pass through it. Neither can the zombie,
   whose attack reach (about 0.83 beyond its box) cannot cross the gap of 1 block or more. This
   works whether or not glass blocks the game's line-of-sight ray: through the window the view is
   clear, and everywhere else it is solid.
4. **The night shutter.** A sticky piston replaces one roof pane above the window. An inverted
   daylight detector sits on top of it and powers it directly. At night and in rain the detector
   outputs power (inverted mode outputs the sky-darkening value, 0 in clear daylight), so the
   piston pushes a stone-brick block down into the window. The villagers stop seeing the zombie,
   stop panicking, and go to their three beds and sleep. That refreshes `LAST_SLEPT`, which golem
   spawning requires within the last 24,000 ticks. At dawn the block lifts and the zombie is
   visible again.
5. **Off switch.** A lever on the piston's east side at (256, 12, −89) holds the shutter
   closed. **Lever on = farm off.**
6. **Restores.** The three villagers named *Golem Works Hand 1–3* and the zombie *The
   Frightener* are summoned again only if they are missing.

Why it produces golems: in daylight, a villager that sees the zombie runs the panic behaviour,
which every 100 ticks calls the golem check. That check needs 3 villagers within 10 blocks who
have slept recently and have not detected a golem in the last 30 s. The spawned golem stands in
flowing water, which carries it into the shaft. It dies in the lava blade within about 12 s,
and the drops fall into the hoppers and the double chest. Expect roughly one golem per 35–45 s
of daylight, when it isn't raining. The chest is not emptied automatically: when it is full,
items wait on the hoppers and are never burnt.

**Status: mechanically reasoned and simulated, not run in Minecraft.** See the live-test list.

### Castle Doom

* **Roofscape**. The **Arcane Spire** at the north-west corner: blackstone with a
  crying-obsidian band and purple slits, rising to an amethyst needle at y 75. The **Radio Mast**
  at the north-east: an iron lattice with chain bracing, a lit red lamp and a lightning rod at
  y 80. The **Observatory** at the south-west: a weathered-copper dome with a slit, a telescope,
  a desk and a lectern journal. Two **chimneys** with lit campfires above the kitchen and
  bedchamber hearths. Three **laboratory exhaust stacks** of unequal height with copper bulbs and
  campfire smoke. A spruce **rainwater tank**. A flagpole. The silhouette is no longer mirrored:
  compare [before and after](after/before_after_castle_south.png) and the [roof](after/before_after_keep_roof.png).
* **Centuries in the stone**. The north-west, the oldest work, is rough: 90
  patches of cobbled deepslate, tuff brick and mossy cobble, and vines where the rain runs. The
  east is the industrial side: copper service pipes with lit valves, and soot-darkened parapets.
  The formal south front is left as it was.
* **The halls within**:
  * *Throne defence.* Two dispensers of arrows flank the throne, facing down the hall. Each fires
    only from the lever on its top.
  * *Kitchen spy loft.* A loft with a ladder, and a grate in the partition wall onto the throne hall.
  * *Laboratory zones.* A robotics bench with a dismantled Doombot (armour stand), a copper
    reactor core behind glass, temporal research at the central table, and a tinted-glass
    containment cell ("Specimen 4"). The alchemy corner was already there.
  * *Sorcery circle.* Purple candles in a ring in the library, with a journal.
  * *War-room map.* The green tablecloth becomes a carpet map of Latveria, **sampled from the
    build itself**: the castle is black, the harbour blue, roofs grey, roads light grey, fields yellow.
* **Beneath the throne**. The **throne hatch**. A sticky piston hidden in the dais
  holds a dais block in place (it is placed already extended). A pedestal hides the piston's
  head, and the lever sits on a second pedestal. **Lever off**: the block slides aside and
  opens a ladder shaft to the Time Platform chamber. **Lever on**: closed. The lever and its
  pedestal are placed before the piston, so the piston is powered the moment it exists.
* **The Time Platform sequence**. A lever by the console (−4, 2, −194) starts a
  hidden repeater chain inside the north wall. Every other wall block becomes a delay-4 repeater,
  and each wall block between two repeaters sits behind one of the seven console lamps. The
  lamps light one by one, 0.8 s apart. Nothing moves or breaks.
* **Tapestry passages**. A banner stands in a niche between the library and the
  laboratory; banners have no collision, so you walk through it. A second banner in the
  bedchamber hides the way into the **oriel study**, a new bay corbelled out from the keep's west
  face between two buttresses. It has shelves, a desk, a chest and Victor's journal.
* **The Deep Cells**. The empty west stairwell hall becomes an interrogation room.
  A rough-cut passage leads south through the keep wall into a new hall carved into the crag
  under the courtyard. It has eight cells behind iron bars, and the **iron cell doors open only
  from the corridor button**. One forgotten prisoner has left a tally on the wall. A ladder
  shaft drops to y −9 and meets **Doom's escape tunnel** through a door.
* **The Doombot proving ground**. The Doombot story is told outside the player's
  own factory: a new hall carved east of the keep dungeon, entered from the east stairwell hall.
  It has raw stores, a glassed lava casting pit, an assembly table with two frames under
  construction, finishing, a test lane with targets, a reject pile ("Reject 0451") and a
  quality-control journal.

### Doomstadt

* **The government quarter**, at the foot of the Grand Stair, is deliberately not a matched
  pair. To the west is the **Chancery and Ministry of Records**: older and tall, with pilasters, a
  copper gable roof and a bell turret. Inside are the records hall, clerks' desks, the register of
  citizens and the minister's office. To the east is the **Palace of Justice and Council of
  Latveria**: later and severe, with a smooth-stone block, a deepslate portico and a copper dome.
  It holds the courtroom (bench, dock and public benches) and the council chamber, where a U of
  oak surrounds an empty chair no one sits in.
* **The Market Square**, north-east of the plaza: a paved square with worn setts, eight stalls
  with coloured awnings, a well with a bell, benches, and a notice board. Four named
  stallholders (Magda, Stefan, Rosa, Anton) are villagers **without AI**, so they stay at their
  counters and never claim beds or jobs.
* **The Garden of the Republic** has paths, hedged beds, flowers, trees, a pool and benches. The
  **Decree Wall** holds six dry rules rather than slogans; the propaganda is kept restrained.
* **Back yards by quarter.** 30 town blocks were scanned for free 5×5 lots, with at most four
  scenes per block and never the same scene twice in a row. Each quarter has its own menu:
  * the Old Town (north-west): wells, woodsheds, spruce trees
  * the Castle Quarter (north-east): benches, birches, flower beds, hedges, fountains
  * the Weavers (south-west): vegetable plots, hen houses, drying racks
  * the Workshops (south-east): timber stacks, workyards, carts, scaffolds
* **Street names** on signposts at the crossings: Kastellgasse, Weavers' Lane, Tanners' Row,
  Werner Avenue, Hunters' Way, Cynthia Street, Kristoff Street, Foundry Way and Doom Boulevard.
  **Worn setts** are concentrated where the traffic is.
* **Underground way-finding**: signs where the Deep Cells shaft meets the escape tunnel, and at
  the great sewer crossing.

### The districts

* **Nursery**. A **baby-only exit**, 1×1 at floor level in the east wall. Children
  (0.98 tall) fit through it; adults (1.95 tall) do not. The children drop two blocks into a
  sunken, lit **Children's Yard** they cannot climb out of. A fence gate at the top of the stairs
  releases grown villagers into the town: villagers cannot open fence gates, so only you can. The
  three adults are re-summoned only if missing.
  **Bed claims.** A child that leaves keeps its bed claim, and breeding needs a free bed.
  Run **`Reset-Nursery-Beds-V3.bat`** whenever you want the nursery to breed again. It removes
  each of the nine nursery beds (only if it is exactly the expected bed) and puts it back, which
  creates fresh, unclaimed beds. It is safe to repeat.
* **The Sorting Office**. A new building beside the Depository. You drop goods into
  the chest at the top of the receiving platform. A hopper stream carries them past six filters:
  cobblestone, iron ingots, bones, rotten flesh, string and gunpowder. These are the items the
  farms and the quarry produce by the stack. Each filter fills a labelled double chest, and
  everything else goes to the **OVERFLOW** chest. **Nothing is ever destroyed**: when a category
  chest is full, its filter fills up and the item rides on to overflow. When overflow is full,
  the stream backs up and items wait in the hoppers and the input chest.
  The Depository's 120 manual bays are untouched.
  Each filter is the standard locked-hopper design, 1 block wide:
  1. The filter hopper F under the stream holds 18 of its item plus 4 named blockers, so its
     comparator reads 1. F faces the comparator, so it never pushes.
  2. A 19th item makes the comparator read 2. The signal passes two dusts (2 → 1) into a
     repeater. The repeater powers block P and turns off the wall torch on P.
  3. The torch's line, run in the floor, stops powering the block under the lower hopper B.
     B unlocks, pulls one item from F into the chest, and F drops back to 18.
  4. At most one unlock per 8 game ticks keeps the torch below its burn-out limit (8 toggles in
     60 ticks).
  The filter slots are only filled while empty.
* **The Foundry**. Audited; the wiring is correct. A comparator and a lamp next to
  each smelter bank's output chest light while there is something to collect. **Put only
  smeltable items in the top chests**: anything else stops that smelter, though nothing is lost.
* **Doomwerk**: three brick stacks with smoke on the Foundry roof, a copper pipe
  bridge, and crates.
* **The Harbour**. 46 rocky shoals break the straight shores, and there are two
  small islets (one with a lamp). Also: bollards along the quay, a fish market with a blue
  awning, a harbour-master's log, and net racks on the piers.
* **Southmarch**: a windmill with wool sails, scarecrows (blocks only), and hay ricks.
* **The Ambassador's Manor**: a glass kitchen greenhouse with crops.
* **Stations**: shelters with benches at the Plaza (east line), Doomwerk and the
  Harbour termini. At the Plaza south-line terminus there is no free spot, so none was built.
* **Castle alarm**: two bells over the gate passage, rung by hand. They are manual
  and harm no one.
* **The approach**: boundary stones on the south road, an avenue of trees spaced a
  little irregularly, and a candle-lit wayside shrine.

### Colour language and the night hierarchy

* Colour: **green** is the state (Doom banners, the government signage, Decree Wall text).
  **Copper**, weathered to green, is science: the observatory, the reactor, the lab stacks and the
  pipes. **Purple and amethyst** are sorcery, and appear only on the Arcane Spire and in the
  library circle. **Black** is the castle.
* Night: the hierarchy is kept, with the castle brightest, then the plaza and avenues, then the
  streets and yards. v3 never removes light. It adds light only where it created a new
  spawnable surface, or in its own new rooms (at least 8). The Hall of Shadows stays at 0.

## What v3 leaves untouched

* The player's Doombot factory room, cell for cell (verified).
* Every building's position, every street and wall, every tower, the Grand Stair and the Plaza.
* All v1/v2/lighting entities: none is moved or killed.
* The Hall of Shadows, the Exchange villagers, the ranch, the quarry and mine, the tree farm,
  the rails, the Nether hub portals, and the manor house itself.
* Global state: no gamerule, no forceload, no difficulty, time or weather change.

## Entity additions

8 new entities, each tagged `lv3_<id>` and `lv3`:
* 4 armour stands: the lab Doombot, two Doombot frames and Reject 0451
* 4 villagers without AI: the market stallholders

Up to 7 restores (the Golem Works crew and the nursery adults) are summoned only if missing.
The total goes from 293 to **301**.

## Live Minecraft test requirements (not done: nothing here has run in Minecraft)

| System | What to check | Status |
|---|---|---|
| Golem Works | Golems appear on the pad by day and ride the water into the shaft. The shutter closes at dusk and in rain. Villagers sleep at night (watch for 2 in-game days). The lever stops the farm. The iron reaches the chest. | mechanically reasoned + spawn simulation; **requires live test** |
| Throne hatch | Lever off opens the hatch and lever on closes it; you can climb out of the shaft at the top. | mechanically reasoned; **requires live test** |
| Time Platform | The seven lamps light in sequence and go dark in sequence. | mechanically reasoned; **requires live test** |
| Sorting Office | Each filter sorts at full hopper speed with no torch burn-out, and overflow fills correctly. | mechanically reasoned; **requires live test** |
| Nursery | Children go through the exit and adults don't. Breeding resumes after the bed reset. | mechanically reasoned; **requires live test** |
| Throne dispensers | Each lever flip fires one arrow down the hall. | mechanically reasoned |
| Lecterns | The pages show text: they are set as plain strings, which the game should read as text components. | requires live check |
| Market stallholders | They offer trades (villagers without AI normally still trade) and stay at their stalls. | requires live check |
| Everything else | Structural placement. The verifier checks supports and replays the layer. | structurally verified |

## Rollback limitations

There is no automatic undo. Honestly:
* **Placements into air** can be removed by hand, or with `fill … air replace <that block>` over
  a known volume. The build report lists every section and its commands.
* **Swaps** (`replace <old>`) cannot be undone blindly: turning the new block back into the old one
  in the same volume would also convert any matching block you have placed since.
* **Carved rooms** (the Deep Cells, the proving ground, the Children's Yard) replaced natural crag
  and ground. Refilling them with stone is possible but loses the original stone and dirt pattern.
* The **bed reset** file is repeatable. Its effect on claims can't be reversed, but reversing it
  is never needed.
* A **world backup** before any large edit is still the only true undo.

## The Nether link (not changed by v3)

The hub's two portals map to Nether (69.9, −1265) and (72.9, −1265), less than the 16-block
search radius apart. So both lead to **the same Nether portal**, and returning always arrives at
the **western** portal. v3 does not build in the Nether, because its terrain there is unknown and
a guess could break the link you already use. If you want two separate links, go through the **eastern** portal. In the Nether, press F3 and
note the x of the portal you arrive at.
* If it is at **x 70 or less**, build a second portal by hand at about **x 73–74, z −1265**. The
  eastern overworld portal (target x 72.9) will then find the new portal nearer, and the western
  one (target x 69.9) keeps the old one. Coming back through the new portal leads to overworld
  x ≈ 584, which is the eastern portal.
* If it is at **x 71 or more**, both targets are nearer the old portal, and two separate links
  are not possible without moving an overworld portal. v3 will not do that.
