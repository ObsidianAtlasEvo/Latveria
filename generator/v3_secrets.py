"""Refinement v3 - the secret Castle Doom, the Time Platform sequence and the new dungeon depths.

Secrets are few and each is different:
  * the throne hatch      - a sticky-piston floor block behind the throne; the lever on the small
                            pedestal beside it drops the block, opening a ladder shaft to the Time
                            Platform chamber (mechanically reasoned, requires live test);
  * the library tapestry  - a banner standing in a niche between the library and the laboratory;
                            banners have no collision, so one walks through it;
  * the oriel study       - a hidden bay built out from the keep's west face behind the royal
                            bedchamber, entered past a second standing banner;
  * the kitchen spy loft  - see v3_castle.kitchen_loft;
  * the Deep Cells        - a forgotten prison carved into the crag under the courtyard, reached
                            from the dungeon and linked by a ladder shaft to Doom's escape tunnel.
"""
from core import pos
from v3core import CRAG

DB = "deepslate_bricks"


def build(v):
    throne_hatch(v)
    time_platform(v)
    passages(v)
    deep_cells(v)
    proving_ground(v)


# --------------------------------------------------------------------------- throne hatch
def throne_hatch(v):
    v.section("secret_throne", "Castle Doom - beneath the throne", (8, 12, -184))
    H = (4, 14, -194)            # the hatch block (already polished deepslate)
    # pedestals over the piston and its head, lever first (so the piston is powered the moment it exists),
    # then the head, then the piston itself in its extended (closed) state
    v.put(5, 15, -194, "chiseled_polished_blackstone")
    v.put(6, 15, -194, "polished_blackstone")
    v.put(5, 16, -194, "soul_lantern")
    v.put(6, 16, -194, "lever[face=floor,facing=west,powered=true]")
    v.swap(5, 14, -194, 5, 14, -194, "piston_head[facing=west,type=sticky,short=false]", "polished_deepslate")
    v.swap(6, 14, -194, 6, 14, -194, "sticky_piston[facing=west,extended=true]", "polished_deepslate")
    # the shaft: through the dais and the dungeon vault, ladder on the north wall
    v.swap(4, 12, -194, 4, 13, -194, "ladder[facing=south]", "polished_deepslate")
    v.swap(4, 11, -194, 4, 11, -194, "ladder[facing=south]", "deepslate_tiles")
    v.fill_keep(4, 2, -194, 4, 10, -194, "ladder[facing=south]")
    v.mechanism("Throne hatch", "mechanically reasoned; requires live test",
                "Sticky piston (6,14,-194) facing west, placed extended; its head (5,14,-194) holds the dais block "
                "(4,14,-194) in place. The lever on the pedestal (6,16,-194) strongly powers the pedestal block "
                "(6,15,-194), which powers the piston below it. Lever OFF: the piston retracts and pulls the block one "
                "cell east - the hatch opens onto a ladder shaft down to the Time Platform chamber. Lever ON: closed.")


# --------------------------------------------------------------------------- time platform
def time_platform(v):
    """A non-destructive calibration sequence: a lever starts a repeater chain hidden in the north
    wall; each console lamp lights 0.8 s after the previous one."""
    v.section("time_platform", "Castle Doom - the Time Platform sequence", (0, 2, -186))
    Z = -195
    v.swap(-3, 2, Z, -2, 2, Z, "repeater[facing=west,delay=4]", DB)
    for x in range(0, 23, 2):
        v.swap(x, 2, Z, x, 2, Z, "repeater[facing=west,delay=4]", DB)
    v.put(-4, 2, -194, "lever[face=wall,facing=south,powered=false]")
    v.sign(-4, 3, -194, "dark_oak_wall_sign[facing=south]", ["CHRONAL", "CALIBRATION", "pull to begin"], "green", True)
    v.mechanism("Time Platform calibration", "mechanically reasoned; requires live test",
                "Lever (-4,2,-194) powers the wall block behind it; repeaters (delay 4) replace every other wall block "
                "at z=-195 from x=-3 to x=22, each powering the next wall block; the wall blocks behind the seven console "
                "lamps (x=-1..23 step 4) light them one after another (0.8 s apart). No block moves or breaks.")


# --------------------------------------------------------------------------- tapestry passages
def passages(v):
    v.section("secret_passages", "Castle Doom - passages behind the tapestries", (-10, 28, -176))
    # library <-> laboratory: a standing banner in a niche of the partition wall at x = 0
    v.swap(0, 28, -180, 0, 29, -180, "air", DB)
    v.put(0, 28, -180, 'black_banner[rotation=4]{patterns:[{pattern:"minecraft:border",color:"green"},{pattern:"minecraft:skull",color:"green"}]}')

    # the oriel study off the royal bedchamber (third floor, west wall x -30..-29)
    v.section("secret_oriel", "Castle Doom - the oriel study", (-26, 38, -168))
    x1, x2, z1, z2 = -34, -31, -170, -165       # between the keep's west buttresses
    with v.piece("oriel study"):
        # corbels
        v.fill_keep(x1 + 2, 35, z1 + 1, x2, 35, z2 - 1, "polished_deepslate")
        v.fill_keep(x1 + 1, 36, z1, x2, 36, z2, "polished_deepslate")
        v.fill_keep(x1, 37, z1, x2, 37, z2, "deepslate_tiles")
        # walls
        v.fill_keep(x1, 38, z1, x1, 42, z2, "polished_deepslate")
        v.fill_keep(x1 + 1, 38, z1, x2, 42, z1, "polished_deepslate")
        v.fill_keep(x1 + 1, 38, z2, x2, 42, z2, "polished_deepslate")
        v.fill_keep(x1, 43, z1, x2, 43, z2, "deepslate_tile_slab[type=bottom]")
        v.fill_keep(x1 - 1, 42, z1 - 1, x2 - 1, 42, z1 - 1, "deepslate_tile_stairs[facing=south,half=top]")
        v.fill_keep(x1 - 1, 42, z2 + 1, x2 - 1, 42, z2 + 1, "deepslate_tile_stairs[facing=north,half=top]")
        # furniture
        v.put(x1 + 1, 38, z1 + 1, "bookshelf")
        v.put(x1 + 1, 38, z1 + 2, "bookshelf")
        v.put(x1 + 1, 39, z1 + 1, "bookshelf")
        v.put(x1 + 1, 38, z2 - 1, "chest[facing=east]")
        v.put(x1 + 2, 38, z1 + 3, "dark_oak_stairs[facing=east]")
        v.put(x1 + 3, 38, z1 + 3, "dark_oak_slab[type=top]")
        v.put(x1 + 3, 39, z1 + 3, "candle[candles=3,lit=true]")
    # windows: green panes in the outer wall
    v.swap(x1, 39, z1 + 2, x1, 40, z2 - 2, "green_stained_glass_pane", "polished_deepslate")
    v.put(x1 + 2, 42, z1 + 3, "lantern[hanging=true]")
    v.stock(x1 + 1, 38, z2 - 1, [(0, "ender_pearl", 4), (1, "golden_apple", 2), (2, "map", 1)])
    v.lectern(x1 + 3, 38, z1 + 1, "west", "Private journal", "Victor", [
        "They think the tower is the heart of the castle. The heart of the castle is wherever I sit alone.",
        "Mother, I have not forgotten. Every stone of this study was laid by my own hand.",
        "The banner in the bedchamber hides the way. It always has."])
    # the passage through the keep wall, behind a standing banner
    v.swap(-30, 38, -166, -29, 39, -166, "air", DB)
    v.put(-29, 38, -166, 'green_banner[rotation=12]{patterns:[{pattern:"minecraft:rhombus",color:"black"},{pattern:"minecraft:border",color:"black"}]}')


# --------------------------------------------------------------------------- deep cells
def deep_cells(v):
    v.section("deep_cells", "Castle Doom - the Deep Cells", (-25, 2, -156))
    # the interrogation room: the empty west stairwell hall (x -28..-23, z -161..-152)
    with v.piece("interrogation"):
        v.put(-26, 2, -157, "dark_oak_fence")
        v.put(-26, 3, -157, "spruce_pressure_plate")
        v.put(-25, 2, -157, "dark_oak_fence")
        v.put(-25, 3, -157, "spruce_pressure_plate")
        v.put(-27, 2, -157, "dark_oak_stairs[facing=east]")
        v.put(-24, 2, -157, "dark_oak_stairs[facing=west]")
        v.put(-28, 2, -160, "barrel[facing=up]")
        v.put(-28, 2, -159, "barrel[facing=up]")
        v.fill_keep(-28, 8, -155, -28, 10, -155, "iron_chain[axis=y]")
        v.fill_keep(-23, 8, -155, -23, 10, -155, "iron_chain[axis=y]")
    v.lectern(-28, 2, -154, "east", "Interrogation record", "Captain of the Guard", [
        "Subject 31 claims to be a journalist. Confiscated: one camera, three notebooks, a sandwich.",
        "Subject 31 moved to the Deep Cells. His notebooks go to the Ministry of Information."])
    # the way down: through the keep's south wall and a rough-cut passage
    v.swap(-26, 2, -151, -25, 3, -150, "air", DB)
    v.carve(-26, 2, -149, -25, 4, -138)
    v.carve(-26, 1, -149, -25, 1, -138, fill_with="cobbled_deepslate")
    # the hall of cells (x -36..-16, z -137..-125, y 2..5)
    X1, X2, Z1, Z2 = -36, -16, -137, -125
    v.carve(X1, 2, Z1, X2, 5, Z2)
    v.carve(X1, 1, Z1, X2, 1, Z2, fill_with="cobbled_deepslate")
    v.carve(X1, 6, Z1, X2, 6, Z2, fill_with="deepslate_tiles")
    # cell walls and fronts
    for x in (-31, -26, -21):
        v.fill_keep(x, 2, Z1, x, 5, -133, DB)
        v.fill_keep(x, 2, -129, x, 5, Z2, DB)
    cells = [(-36, -32), (-30, -27), (-25, -22), (-20, -16)]
    for (a, b_) in cells:
        for zf in (-133, -129):
            v.fill_keep(a, 2, zf, b_, 5, zf, "iron_bars")
    # front rows are iron bars; one cell door per cell (a gap closed by an iron door with a button outside)
    for i, (a, b_) in enumerate(cells):
        for zf, facing, inside in ((-133, "south", -134), (-129, "north", -128)):
            dx = a + 1
            v.swap(dx, 2, zf, dx, 3, zf, "air", "iron_bars")
            v.door(dx, 2, zf, "iron", facing)
            outside = zf + (1 if zf == -133 else -1)
            v.swap(dx + 1, 3, zf, dx + 1, 3, zf, DB, "iron_bars")
            v.put(dx + 1, 3, outside, "stone_button[face=wall,facing=%s]" % facing)
            # straw bed, bucket, chains
            v.put(b_, 2, inside + (-2 if zf == -133 else 2), "hay_block")
            v.put(a, 2, inside + (-3 if zf == -133 else 3), "cauldron")
    # one lantern in every cell, soul lanterns along the corridor (no dark floor anywhere)
    for (a, b_) in cells:
        for zc in (-135, -127):
            v.put((a + b_) // 2, 5, zc, "lantern[hanging=true]")
    # the corridor lights (soul lanterns under the tile ceiling)
    for x in range(-34, -16, 5):
        v.put(x, 5, -131, "soul_lantern[hanging=true]")
    # a forgotten prisoner and his tally
    v.put(-18, 2, -136, "skeleton_skull[rotation=6]")
    v.sign(-16, 3, -136, "spruce_wall_sign[facing=west]", ["IIII IIII IIII", "IIII IIII IIII", "IIII IIII II", "they forgot me"], "black")
    v.put(-35, 4, -137, "cobweb")
    v.put(-20, 5, -125, "cobweb")
    # link to the escape tunnel: passage west and a ladder shaft down to y -9
    v.carve(-38, 2, -131, -37, 3, -131)
    v.carve(-38, -9, -131, -38, 1, -131)
    v.fill_keep(-38, -9, -131, -38, 2, -131, "ladder[facing=north]")
    v.swap(-39, -9, -131, -39, -8, -131, "air", DB)
    v.door(-39, -9, -131, "dark_oak", "west")
    v.mechanism("Deep Cells doors", "structurally verified",
                "Iron cell doors open only with the stone button on the corridor side; prisoners cannot open them.")


# --------------------------------------------------------------------------- doombot proving ground
def proving_ground(v):
    """A Doombot annex carved east of the keep dungeon (the player's own factory is untouched)."""
    v.section("doombot_annex", "Castle Doom - the Doombot proving ground", (25, 2, -156))
    X1, X2, Z1, Z2 = 32, 47, -170, -152
    # door from the jailers' hall (x 23..28) through the keep's east wall
    v.swap(29, 2, -157, 30, 3, -156, "air", DB)
    v.carve(31, 2, -157, 31, 3, -156)
    v.carve(X1, 2, Z1, X2, 6, Z2)
    v.carve(X1, 1, Z1, X2, 1, Z2, fill_with="polished_deepslate")
    v.carve(X1, 7, Z1, X2, 7, Z2, fill_with="deepslate_tiles")
    # stations along the hall (north to south): stores, casting, assembly, finishing, testing, rejects
    with v.piece("raw stores"):
        for z in (-169, -168, -167):
            v.put(32, 2, z, "barrel[facing=east]")
            v.put(32, 3, z, "barrel[facing=east]")
    v.stock(32, 2, -169, [(0, "iron_ingot", 32), (1, "redstone", 32)])
    with v.piece("casting"):
        v.fill_keep(35, 2, -169, 37, 2, -167, "polished_blackstone_bricks")
        v.fill_keep(35, 3, -169, 37, 3, -167, "glass")
        v.fill_keep(35, 4, -169, 37, 4, -167, "polished_blackstone_bricks")
    v.swap(36, 3, -168, 36, 3, -168, "lava", "glass")
    with v.piece("assembly"):
        v.fill_keep(40, 2, -163, 44, 2, -162, "iron_block")
        v.fill_keep(42, 5, -163, 42, 6, -163, "iron_chain[axis=y]")
        v.put(39, 2, -163, "anvil[facing=east]")
        v.put(45, 2, -163, "smithing_table")
        v.put(45, 2, -162, "crafter[orientation=up_north]")
    for i, x in enumerate((41.5, 43.5)):
        tag = v.once("annex_bot_%d" % i, "armor_stand", x, 3, -162.5,
                     '{ShowArms:1b,NoBasePlate:1b,CustomName:"Doombot frame %d"}' % (i + 1), yaw=180)
        v.equip(tag, "armor.chest", "iron_chestplate")
        if i == 0:
            v.equip(tag, "armor.head", "iron_helmet")
    with v.piece("finishing"):
        v.put(33, 2, -160, "cauldron")
        v.put(33, 2, -159, "green_glazed_terracotta")
        v.put(33, 3, -159, "green_candle[candles=2,lit=false]")
    # testing lane: targets at the south end, a firing line at the north
    with v.piece("test lane"):
        v.fill_keep(47, 2, -158, 47, 4, -153, "polished_deepslate")
    v.swap(47, 3, -157, 47, 3, -154, "target", "polished_deepslate")
    v.fill_keep(38, 2, -158, 38, 2, -153, "polished_blackstone_wall")
    # rejects
    with v.piece("rejects"):
        v.put(34, 2, -153, "iron_block")
        v.put(35, 2, -153, "iron_trapdoor[half=bottom,facing=north,open=false]")
        v.put(34, 3, -153, "skeleton_skull[rotation=10]")
        v.put(36, 2, -152, "iron_bars")
    v.once("annex_reject", "armor_stand", 34.5, 2, -155.5,
           '{NoBasePlate:1b,Small:1b,CustomName:"Reject 0451",Pose:{Head:[40f,0f,25f]}}', yaw=45)
    for x in range(34, 47, 6):
        for z in (-166, -155):
            v.put(x, 6, z, "lantern[hanging=true]")
    v.lectern(44, 2, -168, "west", "Quality control", "Doombot Works", [
        "Unit 0451 walked into the lava during casting. Unit 0452 saluted the wrong flag. Scrap both.",
        "Reminder: the Master's own workshop next door is OFF LIMITS. His units are not our units."])
