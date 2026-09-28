"""Refinement v3 - the districts: Doomwerk, the Southmarch, the West March, transport and defence.

Survival systems changed here (see docs/v3/REFINEMENT_V3.md for the reasoning):
  * the Villager Nursery  - a baby-only exit (one block high) drops children into a sunken
                            Children's Yard they cannot climb out of; a gate releases them.
  * the Sorting Office    - a hopper item sorter beside the Depository for the six items that
                            arrive by the stack (cobblestone, iron, bones, flesh, string, gunpowder);
                            everything else and every overflow ends in a chest, never in lava.
  * the Foundry           - audited (correct); an "output waiting" lamp on each smelter bank.
"""
import random

from core import pos
from v3core import relight, restore_named

GROUND = -1


def build(v):
    underground(v)
    nursery(v)
    sorting_office(v)
    foundry(v)
    doomwerk(v)
    harbour(v)
    southmarch(v)
    manor(v)
    transport(v)
    defence(v)
    approach(v)


def lot_free(v, x, z, w, d, m=1):
    ww = v.w
    for xx in range(x - m, x + w + m):
        for zz in range(z - m, z + d + m):
            if ww.name(xx, GROUND, zz) != "grass_block":
                return False
    return v.is_air(x - m, 0, z - m, x + w + m - 1, 6, z + d + m - 1)


def find_lot(v, x1, z1, x2, z2, w, d, step=2):
    for x in range(x1, x2 - w + 1, step):
        for z in range(z1, z2 - d + 1, step):
            if lot_free(v, x, z, w, d):
                return x, z
    return None


# ----------------------------------------------------------------------------- underground
def underground(v):
    """Way-finding in the underground network: where the Deep Cells shaft meets the escape tunnel,
    and at the great sewer crossing under the plaza."""
    v.section("underground", "Under Doomstadt - junction signs", (-40, -9, -140))
    v.sign(-40, -7, -132, "dark_oak_wall_sign[facing=west]", ["^ ladder:", "the Deep Cells", "v south:", "the sewers"], "black")
    v.section("sewer_junction", "Under Doomstadt - the sewer crossing", (0, 12))
    v.sign(-2, -8, -5, "spruce_wall_sign[facing=east]", ["CLOACA DOOMICA", "N: castle stair", "E/W: gates", "S: harbour line"], "black")


# ----------------------------------------------------------------------------- nursery
NX1, NX2, NZ1, NZ2 = -64, -44, 136, 152
BEDS = [(x, ["red", "yellow", "lime", "light_blue", "pink", "white", "orange", "cyan", "magenta"][i % 9])
        for i, x in enumerate(range(NX1 + 2, NX2 - 1, 2))]


def nursery(v):
    v.section("nursery", "Southmarch - the Villager Nursery and the Children's Yard", (-40, 146))
    # the baby exit: one block high in the east wall; adults (1.95 tall) cannot pass
    gz = 145
    v.swap(NX2, 0, gz, NX2, 0, gz, "air", "bricks")
    # the Children's Yard, sunk two blocks so the children cannot jump back in
    YX1, YX2, YZ1, YZ2 = -43, -35, 141, 150
    v.carve(YX1, -2, YZ1, YX2, -1, YZ2, allow=("grass_block", "dirt"))
    v.carve(YX1, -3, YZ1, YX2, -3, YZ2, allow=("dirt",), fill_with="grass_block")
    # (a two-block drop does no harm, and two blocks is more than a child can jump back up)
    # rim: fence around the pit so nothing falls in by accident
    v.fill_keep(YX1, 0, YZ1 - 1, YX2 + 1, 0, YZ1 - 1, "spruce_fence")
    v.fill_keep(YX1, 0, YZ2 + 1, YX2 + 1, 0, YZ2 + 1, "spruce_fence")
    v.fill_keep(YX2 + 1, 0, YZ1, YX2 + 1, 0, YZ2, "spruce_fence")
    # the way out for grown-ups: stairs up the east side behind a fence gate the player opens
    v.carve(YX2 + 1, -2, YZ2 - 4, YX2 + 3, -1, YZ2 - 4, allow=("grass_block", "dirt"))
    v.put(YX2 + 1, -2, YZ2 - 4, "spruce_stairs[facing=east]")
    v.put(YX2 + 2, -1, YZ2 - 4, "spruce_stairs[facing=east]")
    v.swap(YX2 + 1, 0, YZ2 - 4, YX2 + 1, 0, YZ2 - 4, "spruce_fence_gate[facing=east]", "spruce_fence")
    v.put(YX2 + 3, -1, YZ2 - 4, "spruce_slab[type=top]")
    # shade, a water trough, lanterns
    with v.piece("yard shelter"):
        v.fill_keep(YX2 - 2, -2, YZ1, YX2 - 2, -1, YZ1, "spruce_fence")
        v.fill_keep(YX2, -2, YZ1, YX2, -1, YZ1, "spruce_fence")
    v.put(YX1 + 1, -2, YZ2, "water_cauldron[level=3]")
    for z in (YZ1 + 1, YZ2 - 1):
        v.put(YX2, -2, z, "lantern")
    v.put(YX1 + 4, -2, YZ1 + 4, "lantern")
    v.sign(YX2 + 2, 1, YZ1 - 1, "oak_sign[rotation=8]", ["CHILDREN'S", "YARD", "Grown-ups out", "by the gate"], "black")
    v.put(YX2 + 2, 0, YZ1 - 1, "oak_fence")
    v.mechanism("Nursery baby exit", "mechanically reasoned; requires live test",
                "A 1x1 opening at floor level in the nursery's east wall (%d,0,%d): baby villagers (0.98 tall) fit, "
                "adults (1.95) do not. Children who wander through drop 2 blocks into the sunken Children's Yard and "
                "cannot climb back. Open the fence gate to let grown villagers walk up the stairs into the town." % (NX2, gz))
    # adults stay: restore the three if missing
    vd = 'VillagerData:{profession:"minecraft:%s",level:1,type:"minecraft:taiga"},PersistenceRequired:1b'
    restore_named(v, "villager", "Nanny Greta", (NX1 + NX2) // 2 + 0.5, 0, NZ2 - 1.5, vd % "farmer")
    for nm in ("Petar", "Ilona"):
        restore_named(v, "villager", nm, (NX1 + NX2) // 2 + 1.5, 0, NZ2 - 1.5, vd % "none")
    relight(v, (YX1 - 1, -3, YZ1 - 1, YX2 + 3, 1, YZ2 + 1), target=1)


def nursery_reset(v):
    """Separate, optional file: re-seat every nursery bed so claims held by children who have left
    are released (a bed's claim lives in the POI record; replacing the bed makes a fresh one)."""
    v.section("nursery_reset", "Nursery - re-seating the beds (releases old claims)", (-54, 146))
    for (x, col) in BEDS:
        foot = "%s_bed[part=foot,facing=north]" % col
        head = "%s_bed[part=head,facing=north]" % col
        v.b.raw("execute if block %s %s run setblock %s air" % (pos(x, 0, NZ1 + 1), head, pos(x, 0, NZ1 + 1)))
        v.b.raw("execute if block %s %s run setblock %s air" % (pos(x, 0, NZ1 + 2), foot, pos(x, 0, NZ1 + 2)))
        v.w.apply("setblock %s air" % pos(x, 0, NZ1 + 1))
        v.w.apply("setblock %s air" % pos(x, 0, NZ1 + 2))
        v.bed(x, 0, NZ1 + 2, col, "north")


# ----------------------------------------------------------------------------- sorting office
ITEMS = [("cobblestone", "COBBLESTONE"), ("iron_ingot", "IRON INGOTS"), ("bone", "BONES"),
         ("rotten_flesh", "ROTTEN FLESH"), ("string", "STRING"), ("gunpowder", "GUNPOWDER")]


def sorting_office(v):
    v.section("sorting_office", "Doomwerk - the Sorting Office (item sorter)", (210, -113))
    X1, X2, Z1, Z2 = 202, 219, -110, -95
    ZS = -104                  # the item stream (hoppers at y 2)
    # the shell: floor, walls, roof, door on the south side, a window row
    v.swap(X1, GROUND, Z1, X2, GROUND, Z2, "polished_andesite", "grass_block")
    with v.piece("sorting office shell"):
        v.fill_keep(X1, 0, Z1, X2, 5, Z1, "stone_bricks")
        v.fill_keep(X1, 0, Z2, X2, 5, Z2, "stone_bricks")
        v.fill_keep(X1, 0, Z1 + 1, X1, 5, Z2 - 1, "stone_bricks")
        v.fill_keep(X2, 0, Z1 + 1, X2, 5, Z2 - 1, "stone_bricks")
        v.fill_keep(X1, 6, Z1, X2, 6, Z2, "deepslate_tiles")
        v.fill_keep(X1, 7, Z1, X2, 7, Z1, "deepslate_tile_slab[type=bottom]")
        v.fill_keep(X1, 7, Z2, X2, 7, Z2, "deepslate_tile_slab[type=bottom]")
    for x in range(X1 + 2, X2 - 1, 3):
        v.swap(x, 2, Z1, x, 3, Z1, "glass_pane", "stone_bricks")
    v.swap(X1 + 8, 0, Z2, X1 + 9, 1, Z2, "air", "stone_bricks")
    v.door(X1 + 8, 0, Z2, "spruce", "south", hinge="left")
    v.door(X1 + 9, 0, Z2, "spruce", "south", hinge="right")
    v.sign(X1 + 7, 2, Z2 + 1, "dark_oak_wall_sign[facing=south]", ["THE SORTING", "OFFICE", "Drop goods in", "the top chest"], "black")
    # the receiving desk: stairs up to a platform over the first stream hopper
    x_in = 204
    with v.piece("receiving platform"):
        v.fill_keep(X1 + 1, 1, ZS - 1, X1 + 2, 1, ZS + 1, "spruce_planks")
        v.put(X1 + 1, 0, ZS - 2, "spruce_stairs[facing=south]")
    # stream: input chest over the first hopper, hoppers east along z = ZS at y 2
    x_end = 216
    for x in range(x_in, x_end + 1):
        v.put(x, 2, ZS, "hopper[facing=east]")
    v.put(x_in, 3, ZS, "chest[facing=south]")
    # overflow: two hoppers down into a double chest
    v.put(x_end + 1, 2, ZS, "hopper[facing=down]")
    v.put(x_end + 1, 1, ZS, "hopper[facing=down]")
    v.pair((x_end + 1, 0, ZS), "chest[facing=north,type=right]", (x_end, 0, ZS), "chest[facing=north,type=left]")
    # filter modules at x0 = 205, 207, ... (one every second stream hopper)
    for i, (item, label) in enumerate(ITEMS):
        x0 = 205 + 2 * i
        module(v, x0, ZS, item, label)
    # spacer column between modules (under the plain stream hoppers): glass, so nothing conducts
    for i in range(len(ITEMS) - 1):
        x = 206 + 2 * i
        v.put(x, 1, ZS, "glass")
        v.put(x, 0, ZS, "glass")
    v.mechanism("Sorting Office filters", "mechanically reasoned; requires live test",
                "Per item: filter hopper F (y1) under the stream holds 18 of the item + 4 named blockers "
                "(comparator signal 1). A 19th item raises it to 2; the dust passes 2->1 into a repeater, which "
                "powers block P and turns off the torch on P; the torch's line (in the floor) stops powering the block "
                "under the lower hopper B, B unlocks, pulls one item from F into the chest and locks again. "
                "Full chest: B and F fill and the item rides the stream to OVERFLOW. No lava, no cactus: nothing is "
                "ever destroyed. At most one unlock per 8 game ticks keeps the torch below its burn-out limit.")
    relight(v, (X1, 0, Z1, X2, 6, Z2))


def module(v, x0, zs, item, label):
    """One filter module; see the mechanism note in sorting_office.  All y relative to the floor (y -1)."""
    with v.piece("filter " + item):
        # F: filter hopper under the stream, facing (south) into the comparator: it never pushes
        v.put(x0, 1, zs, "hopper[facing=south]")
        # B: the lower hopper, locked at rest, pushes north into the chest
        v.put(x0, 0, zs, "hopper[facing=north]")
    v.swap(x0, GROUND, zs, x0, GROUND, zs, "stone_bricks", "polished_andesite")             # Z, under B
    v.pair((x0, 0, zs - 1), "chest[facing=north,type=left]", (x0 + 1, 0, zs - 1), "chest[facing=north,type=right]")
    v.put(x0, 1, zs - 1, "glass")
    v.put(x0 + 1, 1, zs - 1, "glass")
    v.sign(x0, 1, zs - 2, "dark_oak_wall_sign[facing=north]", [label, "", "(sorted)"], "black")
    # comparator, two dusts, repeater, P, the wall torch
    v.put(x0, 0, zs + 1, "stone_bricks")
    v.put(x0, 1, zs + 1, "comparator[facing=north,mode=compare]")
    v.put(x0, 0, zs + 2, "stone_bricks")
    v.put(x0, 1, zs + 2, "redstone_wire[north=side,south=side,east=none,west=none]")
    v.put(x0, 0, zs + 3, "stone_bricks")
    v.put(x0, 1, zs + 3, "redstone_wire[north=side,south=side,east=none,west=none]")
    v.put(x0, 0, zs + 4, "stone_bricks")
    v.put(x0, 1, zs + 4, "repeater[facing=north,delay=1]")
    v.put(x0, 0, zs + 5, "glass")
    v.put(x0, 1, zs + 5, "stone_bricks")                                                  # P
    v.put(x0, 1, zs + 6, "redstone_wall_torch[facing=south,lit=true]")
    # the torch's line: dust under the torch, down one step, then north in the floor to Z
    v.swap(x0, GROUND, zs + 6, x0, GROUND, zs + 6, "stone_bricks", "polished_andesite")
    v.put(x0, 0, zs + 6, "redstone_wire[north=side,south=side,east=none,west=none]")
    v.swap(x0, GROUND, zs + 1, x0, GROUND, zs + 5, "redstone_wire[north=side,south=side,east=none,west=none]", "polished_andesite")
    # filter contents: 18 of the item and four named blockers (only into empty slots)
    v.stock(x0, 1, zs, [(0, item, 18)] + [(s, "stick", 1, 'custom_name="Filter"') for s in (1, 2, 3, 4)])


# ----------------------------------------------------------------------------- foundry
def foundry(v):
    v.section("foundry", "Doomwerk - the Foundry (audit and output lamps)", (182, -64))
    # each smelter bank's output chest gets a comparator and a lamp: lit = something to collect
    for (xc, z) in ((177, -54), (173, -40), (187, -40)):       # east half of each output chest
        with v.piece("output lamp %d" % xc):
            v.put(xc + 1, 0, z, "comparator[facing=west,mode=compare]")
            v.put(xc + 2, 0, z, "redstone_lamp[lit=false]")
    v.mechanism("Foundry smelter banks", "structurally verified",
                "Input chests (y4) -> hopper line (y3) -> one downward hopper per smelter (top = input); fuel chests "
                "(y3, rear) -> hopper line (y2) -> side hoppers (fuel); output hoppers (y0) -> double chest. The "
                "wiring is correct. Non-smeltable items in the input chests stop that smelter (not destructive). "
                "v3 adds a comparator + lamp beside each output chest.")


# ----------------------------------------------------------------------------- doomwerk
def doomwerk(v):
    v.section("doomwerk", "Doomwerk - chimneys, pipes and yards", (182, -64))
    # foundry roof stacks (the shell roof is at y 9)
    for (x, z, h) in ((166, -58, 7), (174, -58, 9), (196, -52, 6)):
        with v.piece("foundry stack %d" % x):
            v.fill_keep(x, 10, z, x + 1, 9 + h, z + 1, "bricks")
            v.fill_keep(x, 10 + h, z, x + 1, 10 + h, z + 1, "stone_brick_slab[type=bottom]")
        v.swap(x, 10 + h, z, x, 10 + h, z, "campfire[lit=true]", "stone_brick_slab")
    # a pipe bridge between the Foundry and the Depository (lightning rods as copper pipe)
    with v.piece("pipe bridge"):
        v.fill_keep(203, 0, -66, 203, 4, -66, "polished_deepslate")
        v.fill_keep(203, 5, -68, 203, 5, -64, "lightning_rod[facing=north]")
    # crates and a handcart in the lane
    rng = random.Random(9)
    lot = find_lot(v, 206, -60, 218, -20, 4, 3)
    if lot:
        x, z = lot
        with v.piece("crates"):
            v.fill_keep(x, 0, z, x + 1, 1, z, "barrel[facing=up]")
            v.put(x + 2, 0, z, "barrel[facing=up]")
            v.put(x, 0, z + 2, "spruce_slab[type=top]")
            v.put(x + 1, 0, z + 2, "spruce_slab[type=top]")
    relight(v, (160, 9, -62, 205, 22, -20), target=1)


# ----------------------------------------------------------------------------- harbour
def harbour(v):
    v.section("harbour", "Southmarch - the Harbour and the waterfront", (60, 150))
    LX1, LX2, LZ1, LZ2 = 34, 140, 158, 234
    rng = random.Random(1848)
    # break the rectangle: rocky shoals along the north, east and south shores
    for _ in range(46):
        side = rng.choice(["n", "n", "s", "s", "e"])
        if side == "n":
            x, z = rng.randint(LX1 + 22, LX2 - 2), LZ1 + rng.randint(0, 2)
        elif side == "s":
            x, z = rng.randint(LX1 + 22, LX2 - 2), LZ2 - rng.randint(0, 2)
        else:
            x, z = LX2 - rng.randint(0, 2), rng.randint(LZ1 + 2, LZ2 - 2)
        top = rng.choice([-2, -1, -1, 0])
        v.swap(x, -5, z, x, top, z, rng.choice(["stone", "andesite", "mossy_cobblestone", "cobblestone"]), "water", expect=0)
    # two small islets
    for (cx, cz, r) in ((104, 196, 2), (122, 214, 1)):
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r + 1:
                    top = 0 if (dx, dz) == (0, 0) else -1
                    v.swap(cx + dx, -5, cz + dz, cx + dx, top, cz + dz, "stone", "water", expect=0)
        if r >= 2:
            v.put(cx, 0, cz, "lantern")
    # bollards along the quay edge, crates, a fish market on the quay
    for z in range(LZ1 + 4, LZ2 - 3, 7):
        v.put(LX1 + 1, 0, z, "andesite_wall")
    lot = find_lot(v, 23, 160, 31, 232, 7, 5) or find_lot(v, 16, 160, 31, 232, 7, 5)
    if lot:
        x, z = lot
        with v.piece("fish market"):
            for (dx, dz) in ((0, 0), (6, 0), (0, 4), (6, 4)):
                v.fill_keep(x + dx, 0, z + dz, x + dx, 2, z + dz, "spruce_fence")
            v.fill_keep(x, 3, z, x + 6, 3, z + 4, "blue_wool")
            v.fill_keep(x + 1, 0, z + 2, x + 5, 0, z + 2, "spruce_slab[type=top]")
            v.put(x + 2, 1, z + 2, "barrel[facing=up]")
            v.put(x + 4, 1, z + 2, "dried_kelp_block")
            v.put(x + 3, 1, z + 2, "cauldron")
        v.sign(x + 3, 0, z + 5, "oak_sign[rotation=0]", ["FISH MARKET", "Catch of the", "day: whatever", "Marek says"], "black")
        relight(v, (x - 1, -1, z - 1, x + 7, 4, z + 5), target=1)
    # net racks on the piers
    for pz in range(LZ1 + 6, LZ2 - 5, 14):
        v.put(LX1 + 9, 1, pz + 2, "spruce_fence")
    v.lectern(LX1 - 4, 0, LZ1 + 30, "east", "Harbour log", "Harbour master", [
        "Wind from the Carpathians, water flat as a table. No foreign flags. Two skiffs out, two back.",
        "Reminder: the lighthouse lamp is glowstone. It does not need oil. Stop sending oil."])


# ----------------------------------------------------------------------------- southmarch
def southmarch(v):
    v.section("southmarch", "Southmarch - windmill, scarecrows and hay", (-40, 170))
    rng = random.Random(46)
    # the windmill: stone tower, cap, four sails of wool on spruce spars (facing the road)
    lot = find_lot(v, -108, 160, -62, 238, 9, 9) or find_lot(v, -150, 113, 30, 238, 9, 9)
    if lot:
        x, z = lot
        cx, cz = x + 4, z + 3
        with v.piece("windmill"):
            v.fill_keep(cx - 2, 0, cz - 2, cx + 2, 8, cz + 2, "cobblestone")
            v.fill_keep(cx - 1, 9, cz - 1, cx + 1, 11, cz + 1, "spruce_planks")
            v.fill_keep(cx - 2, 12, cz - 2, cx + 2, 12, cz + 2, "dark_oak_slab[type=bottom]")
            v.fill_keep(cx - 1, 13, cz - 1, cx + 1, 13, cz + 1, "dark_oak_slab[type=bottom]")
            v.put(cx, 10, cz + 2, "dark_oak_log[axis=z]")
            v.fill_keep(cx, 11, cz + 3, cx, 16, cz + 3, "stripped_spruce_log[axis=y]")
            v.fill_keep(cx, 4, cz + 3, cx, 9, cz + 3, "stripped_spruce_log[axis=y]")
            v.fill_keep(cx + 1, 10, cz + 3, cx + 6, 10, cz + 3, "stripped_spruce_log[axis=x]")
            v.fill_keep(cx - 6, 10, cz + 3, cx - 1, 10, cz + 3, "stripped_spruce_log[axis=x]")
            v.put(cx, 10, cz + 3, "dark_oak_log[axis=z]")
            v.fill_keep(cx + 1, 11, cz + 3, cx + 1, 16, cz + 3, "white_wool")
            v.fill_keep(cx - 1, 4, cz + 3, cx - 1, 9, cz + 3, "white_wool")
            v.fill_keep(cx + 1, 9, cz + 3, cx + 6, 9, cz + 3, "white_wool")
            v.fill_keep(cx - 6, 11, cz + 3, cx - 1, 11, cz + 3, "white_wool")
        v.swap(cx, 0, cz - 2, cx, 1, cz - 2, "air", "cobblestone")
        v.door(cx, 0, cz - 2, "spruce", "north")
        v.put(cx - 1, 0, cz - 1, "barrel[facing=up]")
        v.put(cx + 1, 0, cz - 1, "stonecutter[facing=north]")
        relight(v, (cx - 7, -1, cz - 3, cx + 7, 17, cz + 4), target=1)
    # scarecrows at the edges of the cane and melon fields (blocks only: no entities)
    placed = []
    for z in range(122, 232, 3):
        for x in (-111, -141):
            if len(placed) >= 5 or any(abs(z - p[1]) < 20 for p in placed):
                continue
            if v.w.name(x, GROUND, z) == "grass_block" and v.is_air(x, 0, z, x, 3, z):
                with v.piece("scarecrow"):
                    v.put(x, 0, z, "spruce_fence")
                    v.put(x, 1, z, "hay_block")
                    v.put(x, 2, z, "carved_pumpkin[facing=%s]" % ("east" if x > -120 else "west"))
                placed.append((x, z))
    # hay ricks at field edges
    for _ in range(8):
        lot = find_lot(v, rng.randint(-104, -60), rng.randint(160, 230), -40, 238, 3, 3, step=3)
        if lot:
            x, z = lot
            with v.piece("hay rick"):
                v.fill_keep(x, 0, z, x + 2, 0, z + 2, "hay_block")
                v.fill_keep(x + 1, 1, z, x + 1, 1, z + 2, "hay_block")


# ----------------------------------------------------------------------------- manor
def manor(v):
    """The manor already has a pond garden; v3 adds a kitchen greenhouse and a garden shed beside it."""
    v.section("manor", "West March - the Ambassador's Manor greenhouse", (-221, 58))
    lot = find_lot(v, -246, 47, -196, 66, 7, 5)
    if lot:
        x, z = lot
        with v.piece("greenhouse"):
            v.fill_keep(x, 0, z, x + 6, 0, z, "stone_bricks")
            v.fill_keep(x, 0, z + 4, x + 6, 0, z + 4, "stone_bricks")
            v.fill_keep(x, 0, z + 1, x, 0, z + 3, "stone_bricks")
            v.fill_keep(x + 6, 0, z + 1, x + 6, 0, z + 3, "stone_bricks")
            v.fill_keep(x, 1, z, x + 6, 2, z, "glass")
            v.fill_keep(x, 1, z + 4, x + 6, 2, z + 4, "glass")
            v.fill_keep(x, 1, z + 1, x, 2, z + 3, "glass")
            v.fill_keep(x + 6, 1, z + 1, x + 6, 2, z + 3, "glass")
            v.fill_keep(x, 3, z, x + 6, 3, z + 4, "glass")
        v.swap(x + 1, GROUND, z + 1, x + 5, GROUND, z + 3, "farmland[moisture=7]", "grass_block")
        v.swap(x + 3, GROUND, z + 2, x + 3, GROUND, z + 2, "water", "farmland")
        crops = ["carrots[age=7]", "potatoes[age=7]", "beetroots[age=3]", "wheat[age=7]"]
        for i, (dx, dz) in enumerate(((1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (1, 2), (2, 2), (4, 2), (5, 2),
                                      (1, 3), (2, 3), (3, 3), (4, 3), (5, 3))):
            v.put(x + dx, 0, z + dz, crops[i % 4])
        v.swap(x + 3, 0, z, x + 3, 0, z, "air", "stone_bricks")
        v.swap(x + 3, 1, z, x + 3, 1, z, "air", "glass")
        relight(v, (x - 1, -1, z - 1, x + 7, 4, z + 5), target=8)


# ----------------------------------------------------------------------------- transport
def transport(v):
    """Station shelters at the four termini of the minecart lines."""
    for (sx, sz, axis, name, anchor) in ((27, 2, "x", "PLAZA - EAST LINE", (30, 8)),
                                        (295, 2, "x", "DOOMWERK", (290, 8)),
                                        (2, 27, "z", "PLAZA - SOUTH LINE", (8, 30)),
                                        (2, 149, "z", "HARBOUR", (8, 146))):
        v.section("station_%s" % name.split()[0].lower() + str(sx), "Stations - %s" % name.title(), anchor)
        # a shelter beside the track: four posts and a slab roof, a bench under it (either side of the line)
        for side in (1, -1):
            if axis == "x":
                za, zb = sorted((sz + 2 * side, sz + 4 * side))
                cells = [(sx - 2, za), (sx + 2, za), (sx - 2, zb), (sx + 2, zb)]
                roof = (sx - 2, za, sx + 2, zb)
                bench = [(sx - 1, sz + 3 * side), (sx, sz + 3 * side), (sx + 1, sz + 3 * side)]
                bf = "south" if side > 0 else "north"
            else:
                xa, xb = sorted((sx + 2 * side, sx + 4 * side))
                cells = [(xa, sz - 2), (xa, sz + 2), (xb, sz - 2), (xb, sz + 2)]
                roof = (xa, sz - 2, xb, sz + 2)
                bench = [(sx + 3 * side, sz - 1), (sx + 3 * side, sz), (sx + 3 * side, sz + 1)]
                bf = "east" if side > 0 else "west"
            if not v.is_air(roof[0], 0, roof[1], roof[2], 3, roof[3]):
                continue
            with v.piece("shelter " + name):
                for (x, z) in cells:
                    v.fill_keep(x, 0, z, x, 2, z, "dark_oak_fence")
                v.fill_keep(roof[0], 3, roof[1], roof[2], 3, roof[3], "dark_oak_slab[type=bottom]")
                for (x, z) in bench:
                    v.put(x, 0, z, "spruce_stairs[facing=%s]" % bf)
            break
        relight(v, (roof[0] - 1, -1, roof[1] - 1, roof[2] + 1, 4, roof[3] + 1), target=1)


# ----------------------------------------------------------------------------- defence
def defence(v):
    """Castle alarm: a lever in the gatehouse passage rings two bells on the gate towers.  Manual only;
    it harms no one.  The town gate arrow batteries (v2) were audited: they fire only from their levers."""
    v.section("castle_alarm", "Castle Doom - the alarm bells", (0, 12, -106))
    # bells hang under the gate-room floor over the passage, one per side
    for x in (-2, 2):
        v.put(x, 20, -110, "bell[attachment=ceiling,facing=north]")
    v.mechanism("Town gate arrow batteries", "structurally verified",
                "Each battery's dispensers fire only when its lever is pulled (v2 design); no pressure plates or "
                "tripwires anywhere, so friendly players cannot trigger them.")


# ----------------------------------------------------------------------------- approach
def approach(v):
    """The road into Latveria from the south: boundary stones, an avenue of trees that is never quite
    regular, and a wayside shrine."""
    v.section("approach", "The approach - boundary stones, trees and a shrine", (0, 176))
    import v3_city
    rng = random.Random(1961)
    z = 116
    while z < 232:
        for x in (-9, 9):
            if rng.random() < 0.8:
                kind = rng.choice(["spruce", "spruce", "oak", "birch"])
                zz = z + rng.randint(-1, 1)
                if lot_free(v, x - 2, zz - 2, 5, 5, m=0):
                    v3_city.tree(v, x, zz, kind, rng.randint(4, 6))
        z += rng.randint(9, 14)
    for (x, z, t) in ((6, 238, ["LATVERIA", "Doomstadt", "3 km"]), (-6, 238, ["By order of", "the Throne:", "travel safely"])):
        if v.w.name(x, GROUND, z) == "grass_block" and v.is_air(x, 0, z, x, 2, z):
            with v.piece("boundary stone %d" % x):
                v.put(x, 0, z, "polished_andesite")
                v.put(x, 1, z, "stone_brick_wall")
            v.sign(x, 0, z + 1, "dark_oak_wall_sign[facing=south]", t, "black")
    lot = find_lot(v, 10, 228, 30, 244, 3, 3)
    if lot:
        x, z = lot
        with v.piece("wayside shrine"):
            v.fill_keep(x, 0, z, x + 2, 0, z + 2, "cobblestone")
            v.put(x + 1, 1, z + 1, "chiseled_stone_bricks")
            v.put(x + 1, 2, z + 1, "candle[candles=3,lit=true]")
            v.put(x, 1, z, "stone_brick_wall")
            v.put(x + 2, 1, z, "stone_brick_wall")
            v.put(x, 2, z, "stone_brick_slab[type=bottom]")
            v.put(x + 2, 2, z, "stone_brick_slab[type=bottom]")
        relight(v, (x - 1, -1, z - 1, x + 3, 3, z + 3), target=1)
