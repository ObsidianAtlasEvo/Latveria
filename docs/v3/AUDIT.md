# Audit of the executed world (main build + Survival Expansion v2 + Lighting Overhaul)

Done before any v3 command was written. The three executed command files were replayed in order
into a voxel model (`generator/sim.py`, now also tracking entities and `keep`/`execute` forms), and
every v3 decision below was checked against that model. Renders of the audited state are in
[`audit/`](audit/). The same renders after v3 are in [`after/`](after/).

All coordinates are offsets from the centre block **799 70 −10090** (plaza centre, feet level).

## What the three layers left

| | |
|---|---|
| Non-air blocks | 2,724,270 |
| Built bounds (relative) | x −300..300, y −129..115, z −252..240 |
| Block states in use | 460 |
| Entities | 293: 137 villagers, 46 armour stands, 12 horses, 11 chickens, 10 cows, 10 sheep, 10 iron golems (the Doombot golems), 9 glow item frames, 8 minecarts, 7 pigs, 5 bees, 5 cats, 10 boats, 5 rabbits, 4 goats, 1 donkey, 1 cod, 1 salmon, 1 zombie (The Frightener) |
| Trees from `place feature` | 82. Their exact shape isn't known to the model, so v3 keeps away from them. |
| Global state | Each layer switched `send_command_feedback`, `log_admin_commands` (and, for the first two, `spawn_mobs`) off and back on at its end. **If an earlier run was ever stopped before its last section, check `/gamerule spawn_mobs` is `true`**. v3 never touches gamerules. |

Maps: [full map](audit/map_full.png), [entities](audit/map_entities.png),
[underground](audit/map_underground.png), [castle elevations](audit/castle_elevations.png),
[keep floor plans](audit/castle_keep_plans.png), [courtyard](audit/castle_courtyard_plan.png),
[wall walk](audit/castle_wallwalk_plan.png), and the plans of [Doomstadt](audit/plan_doomstadt.png),
[Doomwerk](audit/plan_doomwerk.png), [Southmarch](audit/plan_southmarch.png) and
[West March](audit/plan_west_march.png).

## Castle Doom as found

* **Keep** (x −30..30, z −196..−150). Floors are at y 1, 11, 27, 37 and 47.
  * **Dungeon** (walk y 2): the player's own Doombot factory at x −28..−6 / z −194..−168. It is
    protected: v3 writes nothing inside x −29..−5, y 0..11, z −195..−167, and the verifier checks
    it is unchanged cell for cell. Also on this level: the Time Platform chamber (x −4..28) with a
    console of observers, daylight detectors and seven **unwired** lamps along the north wall; the
    corridor (z −166..−163) with the secret door to the escape tunnel; the prison, crypt and treasury;
    and two stairwell halls (x −28..−23 and 23..28, z −161..−152) that were **empty**.
  * **Ground** (walk y 12): the throne hall (dais z −194..−186, throne at x −1..1, z −193), kitchen,
    dining room, armoury and guard room.
  * **Second** (walk y 28): the library (x −28..−1) and the laboratory (x 1..28). The laboratory is
    one 28×31 room with a single workstation row and a central table, **mostly empty**.
  * **Third** (walk y 38): the royal bedchamber (west), with a fireplace whose flue ends under the
    ceiling, and the war room (east), with a large table under a green cloth.
  * **Roof** (walk y 48): a **flat, empty 57×43 plane** with a lantern grid, two stair huts and
    the Doom Tower (x −8..8, z −182..−166, to y 100).
* **Curtain and towers.** The walls are one material, deepslate bricks, with cracked patches.
  There are four round corner towers (cone roofs to y 66), three square wall towers, and a
  gatehouse with twin drum towers, murder-hole trapdoors and raised portcullis grilles.
* **Silhouette.** Seen from any side the castle is **mirror-symmetric**: the tower to y 100 sits
  dead centre, with matching corners, matching wall towers and a matching keep roofline. It reads
  as a single building campaign, not centuries of work.

## Doomstadt and the districts as found

* **Town** (x ±144, z −70..104). A rigid grid of 30 blocks: houses face the streets, and the
  backyards are empty. **43% of the town's ground is bare grass.** There is no market, no
  government building and no street name. Every quarter looks the same.
* **Doomwerk**: the Depository, with 120 manual chest bays and **no sorting**; the Foundry;
  the lava works; the Golem Works; the Hall of Shadows; the tree farm, quarry and mine.
  Everything stands on open grass.
* **Southmarch**: the Exchange, the nursery, the fields, the ranch, and the harbour, which is a
  **flat, rectangular pool** with straight shores.
* **West March**: Mephisto Gate (two portals, the wart farm) and the manor, which has a pond garden.

## Faults and weak points found

| # | System | Finding | v3 response |
|---|---|---|---|
| 1 | **Golem Works** | The pads were **dry**, so a golem could stand on them for minutes. While a golem lives within 16 blocks, every villager keeps `GOLEM_DETECTED_RECENTLY` and the farm stalls. | The pads are flooded from 68 rim sources, and the channels are filled flush. |
| 2 | Golem Works | The villager pod floor was **stone**. Golem spawning checks the three cells above the spot, not the golem's width, so spawn attempts could land *inside* the pod on its two free cells. | The pod floors are now glass, which golems cannot spawn on. |
| 3 | Golem Works | The zombie was behind **glass** on every side. If glass passes line of sight, the villagers panic all night and never sleep, so the farm stops after one day. If glass blocks line of sight, they never panic at all. Either way it fails. | An opaque partition with one 1-block window, shut at night by a piston. |
| 4 | Golem Works | No off switch. | A lever on the shutter piston. |
| 5 | Golem Works | The nearest other iron golems (the Doombots) are ≥ 100 blocks away, so they suppress nothing. | No change needed. |
| 6 | **Nursery** | Children stay inside and claim beds. With 3 adults and 9 beds, breeding stops after 6 births. A child that leaves keeps its bed claim (the claim lives in the POI record). | A baby-only exit, a sunken Children's Yard, and an optional bed-reset file. |
| 7 | **Depository** | Manual only. | A separate Sorting Office for the six high-volume items. Manual storage is untouched. |
| 8 | **Foundry** | The wiring is correct: input from the top, fuel from the side, output from below into the end chest. The lava works are correct: lava over dripstone over a gap over a cauldron. Non-smeltable items in the top chests jam one smelter. | A lamp beside each output chest. The jam is documented. |
| 9 | **Hall of Shadows** | 25,854 cells at block light 0, as designed. | v3 adds no light there, and the verifier checks it. |
| 10 | **Gate batteries** | They fire only from their levers: no pressure plates, no tripwires. Safe for friendly players. | No change. |
| 11 | **Nether hub** | Portals at x −240 and −216 (absolute x 559 and 583, z −10120) map to Nether x 69.9 and 72.9, z −1265, which is 3 blocks apart. So **both link to the same Nether portal**, and the way back always arrives at the western portal. | Documented in REFINEMENT_V3.md with a manual fix. v3 does not build in the Nether, because its terrain there is unknown. |
| 12 | Castle | Symmetric silhouette, a flat empty roof, sparse rooms, an unused Time Platform console, empty stairwell halls, and one secret (the escape tunnel). | Roofscape, eras, interiors, secrets and the Deep Cells. |
| 13 | Town / districts | Empty yards, grid monotony, no civic centre, a rectangular harbour. | Government quarter, market, park, yards by quarter, street names, harbour shoals, windmill. |
