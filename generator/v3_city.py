"""Refinement v3 - Doomstadt: government, market, park, decrees and everyday life.

The town keeps every street and house.  New pieces go only on free lots (grass at y -1 and air
above, as the model shows), and each quarter gets its own kind of detail so the city stops
repeating itself:
  north-west  the Old Town       wells, woodsheds, mossy footings, cramped yards
  north-east  the Castle Quarter formal gardens, benches, clipped hedges
  south-west  the Weavers        vegetable plots, hen houses, drying racks
  south-east  the Workshops      stacked timber, grindstones, carts, scaffolds
"""
import random

from v3core import relight

GROUND = -1


def build(v):
    government(v)
    market(v)
    park_and_decrees(v)
    yards(v)
    street_signs(v)
    road_wear(v)


# ----------------------------------------------------------------------------- helpers
def pave(v, x1, z1, x2, z2, block):
    """Replace the grass of a lot with paving (only where grass still lies)."""
    v.swap(x1, GROUND, z1, x2, GROUND, z2, block, "grass_block")


def gable(v, x1, x2, z1, z2, y0, stair, full):
    """Gable roof over x1..x2 / z1..z2 with the ridge along x, eaves overhanging by one."""
    depth = z2 - z1 + 3
    k = 0
    while z1 - 1 + k <= z2 + 1 - k:
        za, zb = z1 - 1 + k, z2 + 1 - k
        y = y0 + k
        if za == zb:
            v.fill_keep(x1 - 1, y, za, x2 + 1, y, za, full)
        elif zb - za == 1:
            v.fill_keep(x1 - 1, y, za, x2 + 1, y, za, "%s[facing=south]" % stair)
            v.fill_keep(x1 - 1, y, zb, x2 + 1, y, zb, "%s[facing=north]" % stair)
        else:
            v.fill_keep(x1 - 1, y, za, x2 + 1, y, za, "%s[facing=south]" % stair)
            v.fill_keep(x1 - 1, y, zb, x2 + 1, y, zb, "%s[facing=north]" % stair)
            # gable ends
            v.fill_keep(x1, y, za + 1, x1, y, zb - 1, full)
            v.fill_keep(x2, y, za + 1, x2, y, zb - 1, full)
        k += 1
    return y0 + k


def stall(v, x, z, facing, wool, goods, name):
    """A 3x3 market stall: corner posts, a wool awning, a counter across the open front and stock at
    the back; the stallholder stands in the middle."""
    front, back = (z + 2, z) if facing == "south" else (z, z + 2)
    with v.piece("stall " + name):
        for (dx, dz) in ((0, 0), (2, 0), (0, 2), (2, 2)):
            v.fill_keep(x + dx, 0, z + dz, x + dx, 1, z + dz, "spruce_fence")
        v.fill_keep(x, 2, z, x + 2, 2, z + 2, wool)
        v.put(x + 1, 0, front, goods[0])
        v.put(x + 1, 0, back, goods[1])


# ----------------------------------------------------------------------------- government
def government(v):
    v.section("gov_chancery", "Doomstadt - the Chancery and the Ministry of Records", (-7, 0, -60))
    # --- the Chancery (west of the Grand Stair): old, tall, copper-roofed, with a bell turret
    x1, x2, z1, z2 = -28, -11, -68, -56
    pave(v, x1 - 1, z1 - 1, x2 + 3, z2 + 1, "polished_andesite")
    with v.piece("chancery"):
        v.fill_keep(x1, 0, z1, x2, 8, z1, "stone_bricks")
        v.fill_keep(x1, 0, z2, x2, 8, z2, "stone_bricks")
        v.fill_keep(x1, 0, z1 + 1, x1, 8, z2 - 1, "stone_bricks")
        v.fill_keep(x2, 0, z1 + 1, x2, 8, z2 - 1, "stone_bricks")
        v.fill_keep(x1 + 1, 4, z1 + 1, x2 - 1, 4, z2 - 1, "spruce_planks")
        v.fill_keep(x1, 9, z1, x2, 9, z2, "polished_deepslate")
        top = gable(v, x1, x2, z1, z2, 10, "waxed_oxidized_cut_copper_stairs", "waxed_oxidized_cut_copper")
        # the bell turret at the west end
        v.fill_keep(x1 + 1, top - 4, z1 + 5, x1 + 3, top + 2, z1 + 7, "stone_bricks")
        v.fill_keep(x1 + 1, top + 3, z1 + 5, x1 + 3, top + 3, z1 + 7, "waxed_oxidized_cut_copper")
        v.put(x1 + 2, top + 4, z1 + 6, "lightning_rod[facing=up]")
    # pilasters, windows, door (east face toward Doom Boulevard)
    for x in range(x1, x2 + 1, 3):
        v.swap(x, 0, z1, x, 8, z1, "polished_andesite", "stone_bricks")
        v.swap(x, 0, z2, x, 8, z2, "polished_andesite", "stone_bricks")
    for x in range(x1 + 2, x2, 3):
        for zz in (z1, z2):
            v.swap(x - 1, 1, zz, x, 2, zz, "glass_pane", "stone_bricks")
            v.swap(x - 1, 5, zz, x, 7, zz, "glass_pane", "stone_bricks")
    zc = (z1 + z2) // 2
    v.swap(x2, 5, zc - 2, x2, 7, zc + 2, "glass_pane", "stone_bricks")
    v.swap(x2, 0, zc - 1, x2, 1, zc, "air", "stone_bricks")
    v.door(x2, 0, zc - 1, "dark_oak", "east", hinge="left")
    v.door(x2, 0, zc, "dark_oak", "east", hinge="right")
    v.fill_keep(x2 + 1, 0, zc - 3, x2 + 1, 2, zc - 3, "polished_andesite")
    v.fill_keep(x2 + 1, 0, zc + 2, x2 + 1, 2, zc + 2, "polished_andesite")
    v.put(x2 + 1, 3, zc - 3, "lantern")
    v.put(x2 + 1, 3, zc + 2, "lantern")
    v.sign(x2 + 1, 3, zc - 1, "dark_oak_wall_sign[facing=east]", ["CHANCERY", "OF LATVERIA", "Ministry of", "Records"], "black")
    # the records hall (ground floor): shelves, archive barrels, clerks' desks
    for x in range(x1 + 2, x2 - 1, 2):
        v.fill_keep(x, 0, z1 + 1, x, 2, z1 + 1, "bookshelf")
    for x in range(x1 + 2, x2 - 1, 3):
        v.put(x, 0, z2 - 1, "barrel[facing=north]")
        v.put(x, 1, z2 - 1, "barrel[facing=north]")
    for i, x in enumerate(range(x1 + 3, x2 - 3, 4)):
        with v.piece("clerk desk %d" % i):
            v.put(x, 0, zc, "spruce_slab[type=top]")
            v.put(x + 1, 0, zc, "spruce_slab[type=top]")
            v.put(x, 0, zc + 1, "spruce_stairs[facing=north]")
            v.put(x + 1, 1, zc, "candle[candles=1,lit=true]")
    v.lectern(x1 + 1, 0, zc, "east", "Register of Citizens", "Ministry of Records", [
        "Every citizen of Latveria is written here: name, trade, street, and whether they pay their taxes.",
        "Births are recorded within three days. Deaths within one. Complaints: see the Palace of Justice."])
    # the Minister's office above (ladder in the north-west corner)
    v.swap(x1 + 1, 4, z1 + 2, x1 + 1, 4, z1 + 2, "air", "spruce_planks")
    v.fill_keep(x1 + 1, 0, z1 + 2, x1 + 1, 4, z1 + 2, "ladder[facing=east]")
    with v.piece("minister desk"):
        v.fill_keep(x2 - 5, 5, zc - 1, x2 - 3, 5, zc - 1, "dark_oak_slab[type=top]")
        v.put(x2 - 4, 5, zc, "dark_oak_stairs[facing=north]")
        v.put(x2 - 3, 6, zc - 1, "lantern")
    v.put(x1 + 6, 5, z1 + 1, "green_wall_banner[facing=south]")
    relight(v, (x1, 0, z1, x2, 9, z2))

    v.section("gov_justice", "Doomstadt - the Palace of Justice and the Council", (10, 0, -60))
    # --- the Palace of Justice (east of the stair): later, severe, columned, flat-roofed with a dome
    x1, x2, z1, z2 = 26, 42, -66, -54
    pave(v, x1 - 5, z1 - 1, x2 + 1, z2 + 1, "smooth_stone")
    with v.piece("palace of justice"):
        v.fill_keep(x1, 0, z1, x2, 7, z1, "smooth_stone")
        v.fill_keep(x1, 0, z2, x2, 7, z2, "smooth_stone")
        v.fill_keep(x1, 0, z1 + 1, x1, 7, z2 - 1, "smooth_stone")
        v.fill_keep(x2, 0, z1 + 1, x2, 7, z2 - 1, "smooth_stone")
        v.fill_keep(x1 + 1, 4, z1 + 1, x2 - 1, 4, z2 - 1, "dark_oak_planks")
        v.fill_keep(x1 - 4, 8, z1, x2, 8, z2, "polished_deepslate")
        # parapet
        v.fill_keep(x1 - 4, 9, z1, x2, 9, z1, "polished_deepslate_wall")
        v.fill_keep(x1 - 4, 9, z2, x2, 9, z2, "polished_deepslate_wall")
        v.fill_keep(x2, 9, z1 + 1, x2, 9, z2 - 1, "polished_deepslate_wall")
        v.fill_keep(x1 - 4, 9, z1 + 1, x1 - 4, 9, z2 - 1, "polished_deepslate_wall")
        # portico: six columns on the west front
        for z in range(z1 + 1, z2, 2):
            v.fill_keep(x1 - 4, 0, z, x1 - 4, 7, z, "polished_deepslate")
        # the council dome
        cx, cz = (x1 + x2) // 2 + 2, (z1 + z2) // 2
        for k, r in enumerate((3.0, 3.0, 2.5, 1.8, 0.8)):
            from core import disk_runs
            for dx, a, b_ in disk_runs(r, r - 1.2 if k < 4 else -1):
                v.fill_keep(cx + dx, 9 + k, cz + a, cx + dx, 9 + k, cz + b_, "waxed_oxidized_copper")
    zc = (z1 + z2) // 2
    for z in range(z1 + 2, z2 - 1, 3):
        v.swap(x2, 1, z, x2, 2, z, "glass_pane", "smooth_stone")
        v.swap(x2, 5, z, x2, 6, z, "glass_pane", "smooth_stone")
    for x in range(x1 + 2, x2 - 1, 3):
        for zz in (z1, z2):
            v.swap(x, 1, zz, x, 2, zz, "glass_pane", "smooth_stone")
            v.swap(x, 5, zz, x, 6, zz, "glass_pane", "smooth_stone")
    v.swap(x1, 0, zc, x1, 1, zc, "air", "smooth_stone")
    v.door(x1, 0, zc, "iron", "west")
    v.sign(x1 - 1, 2, zc, "dark_oak_wall_sign[facing=west]", ["PALACE OF", "JUSTICE", "Council of", "Latveria"], "black")
    v.put(x1 - 1, 0, zc + 1, "polished_blackstone_pressure_plate")
    v.put(x1 + 1, 0, zc + 1, "polished_blackstone_pressure_plate")
    # the courtroom (ground floor): the bench, the dock, the public benches
    with v.piece("court bench"):
        v.fill_keep(x2 - 2, 0, zc - 2, x2 - 2, 0, zc + 2, "dark_oak_planks")
        v.fill_keep(x2 - 1, 0, zc - 2, x2 - 1, 0, zc + 2, "dark_oak_planks")
        v.put(x2 - 1, 1, zc, "dark_oak_stairs[facing=west]")
        v.put(x2 - 2, 1, zc - 2, "lantern")
        v.put(x2 - 2, 1, zc + 2, "lantern")
    with v.piece("dock"):
        v.fill_keep(x1 + 6, 0, z1 + 2, x1 + 8, 1, z1 + 2, "iron_bars")
        v.fill_keep(x1 + 8, 0, z1 + 1, x1 + 8, 1, z1 + 1, "iron_bars")
    for x in range(x1 + 2, x1 + 6):
        v.fill_keep(x, 0, zc + 2, x, 0, z2 - 2, "spruce_stairs[facing=east]")
    v.fill_keep(x1 + 1, 0, z2 - 1, x1 + 1, 4, z2 - 1, "ladder[facing=north]")
    v.swap(x1 + 1, 4, z2 - 1, x1 + 1, 4, z2 - 1, "air", "dark_oak_planks")
    v.fill_keep(x1 + 1, 0, z2 - 1, x1 + 1, 4, z2 - 1, "ladder[facing=north]")
    # the council chamber (upper floor): a U of oak, eight chairs and the one no one takes
    with v.piece("council table"):
        v.fill_keep(x1 + 5, 5, zc - 3, x2 - 3, 5, zc - 3, "dark_oak_slab[type=top]")
        v.fill_keep(x1 + 5, 5, zc + 3, x2 - 3, 5, zc + 3, "dark_oak_slab[type=top]")
        v.fill_keep(x2 - 3, 5, zc - 2, x2 - 3, 5, zc + 2, "dark_oak_slab[type=top]")
        for x in range(x1 + 6, x2 - 3, 2):
            v.put(x, 5, zc - 4, "spruce_stairs[facing=south]")
            v.put(x, 5, zc + 4, "spruce_stairs[facing=north]")
        v.put(x2 - 2, 5, zc, "polished_blackstone_stairs[facing=west]")
    v.lectern(x1 + 3, 5, zc, "east", "Minutes of the Council", "Clerk of the Council", [
        "Item 1. The harvest is good. Item 2. The Master's chair remains empty; it is not to be sat in.",
        "Item 3. The Harbour asks for more lanterns. Granted. Item 4. The Golem Works is not a petting zoo."])
    relight(v, (x1 - 4, 0, z1, x2, 13, z2))


# ----------------------------------------------------------------------------- market
def market(v):
    v.section("market", "Doomstadt - the Market Square", (33, 0, -8))
    x1, x2, z1, z2 = 22, 45, -26, -11
    # cobbled square with a darker border
    pave(v, x1, z1, x2, z2, "stone_bricks")
    v.swap(x1, GROUND, z1, x2, GROUND, z1, "polished_andesite", "stone_bricks")
    v.swap(x1, GROUND, z2, x2, GROUND, z2, "polished_andesite", "stone_bricks")
    rng = random.Random(77)
    for _ in range(40):
        x, z = rng.randint(x1 + 1, x2 - 1), rng.randint(z1 + 1, z2 - 1)
        v.swap(x, GROUND, z, x, GROUND, z, rng.choice(["cobblestone", "andesite", "mossy_stone_bricks"]), "stone_bricks", expect=0)
    goods = [("barrel[facing=up]", "hay_block", "red_wool", "Grain"),
             ("composter[level=0]", "melon", "yellow_wool", "Greens"),
             ("barrel[facing=up]", "dried_kelp_block", "light_blue_wool", "Fish"),
             ("smoker[facing=south]", "barrel[facing=up]", "brown_wool", "Butcher"),
             ("loom[facing=south]", "white_wool", "purple_wool", "Cloth"),
             ("fletching_table", "barrel[facing=up]", "green_wool", "Bows"),
             ("cauldron", "barrel[facing=up]", "orange_wool", "Hides"),
             ("stonecutter[facing=south]", "chiseled_stone_bricks", "gray_wool", "Stone")]
    spots = [(x1 + 1 + 5 * i, z1 + 1) for i in range(4)] + [(x1 + 3 + 5 * i, z2 - 3) for i in range(4)]
    for (sx, sz), (a, b_, wool, name) in zip(spots, goods):
        stall(v, sx, sz, "south" if sz == z1 + 1 else "north", wool, (a, b_), name)
    # the market well with its bell
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    with v.piece("market well"):
        v.fill_keep(cx - 1, 0, cz - 1, cx + 1, 0, cz + 1, "stone_bricks")
        v.swap(cx, 0, cz, cx, 0, cz, "water", "stone_bricks")
        for (dx, dz) in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
            v.fill_keep(cx + dx, 1, cz + dz, cx + dx, 2, cz + dz, "spruce_fence")
        v.fill_keep(cx - 1, 3, cz - 1, cx + 1, 3, cz + 1, "spruce_slab[type=bottom]")
    v.put(cx, 2, cz, "bell[attachment=ceiling,facing=north]")
    # benches and a notice board
    for x in (x1 + 2, x2 - 3):
        v.fill_keep(x, 0, cz, x + 1, 0, cz, "spruce_stairs[facing=%s]" % ("east" if x < cx else "west"))
    with v.piece("market notice board"):
        v.fill_keep(x2 - 1, 0, cz - 1, x2 - 1, 2, cz + 1, "spruce_planks")
    v.sign(x2 - 2, 2, cz - 1, "spruce_wall_sign[facing=west]", ["MARKET DAY", "every day.", "Weights are", "checked."], "black")
    v.sign(x2 - 2, 1, cz, "spruce_wall_sign[facing=west]", ["Lost: one goat.", "Answers to", "'Gregor'.", "- Petra"], "black")
    v.sign(x2 - 2, 2, cz + 1, "spruce_wall_sign[facing=west]", ["Fish before", "noon, or the", "fishmonger", "will know."], "black")
    # stallholders: villagers without AI so they stay at their counters and never claim beds or jobs
    keepers = [("Magda", "farmer", 0), ("Stefan", "fisherman", 2), ("Rosa", "butcher", 3), ("Anton", "leatherworker", 6)]
    for (nm, prof, i) in keepers:
        sx, sz = spots[i]
        z = sz + 1
        v.once("mk_" + nm.lower(), "villager", sx + 1.5, 0, z + (0.5 if sz == z1 + 1 else 0.5),
               '{NoAI:1b,PersistenceRequired:1b,CustomName:"%s",VillagerData:{profession:"%s",type:"taiga"}}' % (nm, prof),
               yaw=0 if sz == z1 + 1 else 180)
    relight(v, (x1, -1, z1, x2, 4, z2), target=1)


# ----------------------------------------------------------------------------- park + decrees
def park_and_decrees(v):
    v.section("park", "Doomstadt - the Garden of the Republic and the Decree Wall", (-31, 0, 10))
    x1, x2, z1, z2 = -43, -21, 15, 30
    # gravel paths in a cross, hedges around the beds, two trees and a pool
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    v.swap(x1, GROUND, cz, x2, GROUND, cz, "dirt_path", "grass_block")
    v.swap(cx, GROUND, z1, cx, GROUND, z2, "dirt_path", "grass_block")
    for (a, b_, c, d) in ((x1 + 1, z1 + 1, cx - 2, cz - 2), (cx + 2, z1 + 1, x2 - 1, cz - 2),
                          (x1 + 1, cz + 2, cx - 2, z2 - 1), (cx + 2, cz + 2, x2 - 1, z2 - 1)):
        v.fill_keep(a, 0, b_, c, 0, b_, "oak_leaves[persistent=true]")
        v.fill_keep(a, 0, d, c, 0, d, "oak_leaves[persistent=true]")
        v.fill_keep(a, 0, b_ + 1, a, 0, d - 1, "oak_leaves[persistent=true]")
        v.fill_keep(c, 0, b_ + 1, c, 0, d - 1, "oak_leaves[persistent=true]")
    rng = random.Random(5)
    flowers = ["poppy", "cornflower", "oxeye_daisy", "allium", "red_tulip", "white_tulip", "azure_bluet", "lily_of_the_valley"]
    for (a, b_, c, d) in ((x1 + 2, z1 + 2, cx - 3, cz - 3), (cx + 3, cz + 3, x2 - 2, z2 - 2)):
        for x in range(a, c + 1):
            for z in range(b_, d + 1):
                if rng.random() < 0.55:
                    v.put(x, 0, z, rng.choice(flowers))
    for (tx, tz) in ((x1 + 5, z2 - 4), (x2 - 5, z1 + 4)):
        tree(v, tx, tz, "oak", 5)
    with v.piece("park pool"):
        v.fill_keep(cx - 1, 0, cz - 1, cx + 1, 0, cz + 1, "stone_brick_slab[type=bottom]")
    v.swap(cx, GROUND, cz, cx, GROUND, cz, "water", "dirt_path")
    for (dx, dz, f) in ((-3, 0, "east"), (3, 0, "west")):
        v.put(cx + dx, 0, cz + dz + 1, "spruce_stairs[facing=%s]" % f)
    v.put(cx + 1, 0, z1, "oak_fence")
    v.sign(cx + 1, 1, z1, "oak_sign[rotation=8]", ["GARDEN OF", "THE REPUBLIC", "Keep off", "the beds"], "green")

    # the Decree Wall: a plain stone board west of the plaza (restrained: rules, not slogans)
    x1, z1 = -37, -14
    with v.piece("decree wall"):
        v.fill_keep(x1, 0, z1, x1 + 6, 2, z1, "stone_bricks")
        v.fill_keep(x1, 3, z1, x1 + 6, 3, z1, "stone_brick_slab[type=bottom]")
        v.fill_keep(x1 - 1, 0, z1, x1 - 1, 3, z1, "polished_andesite")
        v.fill_keep(x1 + 7, 0, z1, x1 + 7, 3, z1, "polished_andesite")
    decrees = [["DECREE 1", "Lanterns stay", "lit all night.", ""],
               ["DECREE 7", "No livestock", "on the Grand", "Stair."],
               ["DECREE 12", "Report strangers", "to the Guard.", "Politely."],
               ["DECREE 19", "The fountain is", "not a bath.", ""],
               ["DECREE 23", "School is free.", "Attendance is", "not optional."],
               ["DECREE 31", "Do not feed", "the Doombots.", ""]]
    for i, lines in enumerate(decrees):
        x = x1 + i + (1 if i >= 3 else 0)
        v.sign(x, 1 + (i % 2), z1 + 1, "spruce_wall_sign[facing=south]", lines, "black")
    relight(v, (-44, -1, -15, -20, 6, 31), target=1)


def tree(v, x, z, kind, h):
    with v.piece("tree %d,%d" % (x, z)):
        v.fill_keep(x - 2, h - 2, z - 2, x + 2, h - 1, z + 2, "%s_leaves[persistent=true]" % kind)
        v.fill_keep(x - 1, h, z - 1, x + 1, h, z + 1, "%s_leaves[persistent=true]" % kind)
        v.put(x, h + 1, z, "%s_leaves[persistent=true]" % kind)
        v.fill_keep(x, 0, z, x, h - 1, z, "%s_log[axis=y]" % kind)


# ----------------------------------------------------------------------------- yards
XB = [(-141, -103), (-97, -51), (-45, -5), (5, 45), (51, 97), (103, 141)]
ZB = [(-66, -43), (-37, -6), (6, 41), (47, 73), (79, 101)]


def quarter(x, z):
    if z < 0:
        return "old" if x < 0 else "castle"
    return "weavers" if x < 0 else "workshops"


def lot_free(v, x, z, n=5, m=1):
    """True if the n x n lot at (x, z) plus an m-cell margin is grass with air above (y 0..5)."""
    w = v.w
    for xx in range(x - m, x + n + m):
        for zz in range(z - m, z + n + m):
            if w.name(xx, GROUND, zz) != "grass_block":
                return False
    return v.is_air(x - m, 0, z - m, x + n + m - 1, 5, z + n + m - 1)


def yards(v):
    """Scan every town block for free 5x5 back-yard lots and give each a small, quarter-specific
    scene.  At most four scenes per block, and never two identical scenes side by side."""
    rng = random.Random(1509)
    menu = {"old": [yard_well, yard_woodshed, yard_garden, yard_bench, yard_woodshed, yard_tree_spruce],
            "castle": [yard_bench, yard_tree_birch, yard_flowerbed, yard_bench, yard_fountainlet, yard_hedge],
            "weavers": [yard_garden, yard_coop, yard_garden, yard_drying, yard_well, yard_tree_oak],
            "workshops": [yard_timber, yard_grind, yard_cart, yard_timber, yard_scaffold, yard_garden]}
    k = 0
    for (xa, xb) in XB:
        for (za, zb) in ZB:
            cx, cz = (xa + xb) // 2, (za + zb) // 2
            q = quarter(cx, cz)
            k += 1
            v.section("yards_%d" % k, "Doomstadt - back yards, block %d (%s)" % (k, q), (cx, cz))
            used = []
            last = None
            for x in range(xa + 1, xb - 5, 6):
                for z in range(za + 1, zb - 5, 6):
                    if len(used) >= 4:
                        break
                    if not lot_free(v, x, z):
                        continue
                    choices = [f for f in menu[q] if f is not last]
                    f = rng.choice(choices)
                    f(v, x, z, rng)
                    used.append((x, z))
                    last = f
            if used:
                relight(v, (xa, -1, za, xb, 6, zb), target=1)


def yard_well(v, x, z, rng):
    with v.piece("well"):
        v.fill_keep(x + 1, 0, z + 1, x + 3, 0, z + 3, "mossy_cobblestone")
        v.fill_keep(x + 1, 1, z + 1, x + 1, 2, z + 1, "spruce_fence")
        v.fill_keep(x + 3, 1, z + 3, x + 3, 2, z + 3, "spruce_fence")
        v.fill_keep(x + 1, 3, z + 1, x + 3, 3, z + 3, "spruce_slab[type=bottom]")
    v.swap(x + 2, 0, z + 2, x + 2, 0, z + 2, "water", "mossy_cobblestone")
    v.put(x + 2, 2, z + 2, "iron_chain[axis=y]")


def yard_woodshed(v, x, z, rng):
    wood = rng.choice(["spruce", "dark_oak", "oak"])
    with v.piece("woodshed"):
        v.fill_keep(x + 1, 0, z + 1, x + 3, 1, z + 1, "stripped_%s_log[axis=x]" % wood)
        v.fill_keep(x + 1, 0, z + 2, x + 3, 0, z + 2, "stripped_%s_log[axis=x]" % wood)
        v.fill_keep(x, 0, z + 3, x, 1, z + 3, "%s_fence" % wood)
        v.fill_keep(x + 4, 0, z + 3, x + 4, 1, z + 3, "%s_fence" % wood)
        v.fill_keep(x, 2, z, x + 4, 2, z + 3, "%s_slab[type=bottom]" % wood)
        v.fill_keep(x, 0, z, x, 1, z, "%s_fence" % wood)
        v.fill_keep(x + 4, 0, z, x + 4, 1, z, "%s_fence" % wood)


def yard_garden(v, x, z, rng):
    crops = ["wheat[age=%d]", "carrots[age=%d]", "potatoes[age=%d]", "beetroots[age=%d]"]
    with v.piece("vegetable plot"):
        v.fill_keep(x, 0, z, x + 4, 0, z, "oak_fence")
        v.fill_keep(x, 0, z + 4, x + 4, 0, z + 4, "oak_fence")
        v.fill_keep(x, 0, z + 1, x, 0, z + 3, "oak_fence")
        v.fill_keep(x + 4, 0, z + 1, x + 4, 0, z + 2, "oak_fence")
    v.swap(x + 1, GROUND, z + 1, x + 3, GROUND, z + 3, "farmland[moisture=7]", "grass_block")
    v.swap(x + 2, GROUND, z + 2, x + 2, GROUND, z + 2, "water", "farmland")
    c = rng.choice(crops)
    for (dx, dz) in ((1, 1), (2, 1), (3, 1), (1, 2), (3, 2), (1, 3), (2, 3), (3, 3)):
        crop = c if rng.random() < 0.7 else rng.choice(crops)
        age = 3 if crop.startswith("beetroots") else 7
        v.put(x + dx, 0, z + dz, crop % rng.randint(age - 3, age))
    v.put(x + 4, 0, z + 3, "oak_fence_gate[facing=east]")


def yard_bench(v, x, z, rng):
    with v.piece("bench"):
        v.put(x + 1, 0, z + 2, "spruce_stairs[facing=east]")
        v.put(x + 1, 0, z + 3, "spruce_stairs[facing=east]")
        v.put(x + 3, 0, z + 2, "flowering_azalea")
        v.put(x + 3, 0, z + 3, "lantern")
    for dx in range(0, 5):
        if rng.random() < 0.5:
            v.put(x + dx, 0, z, rng.choice(["poppy", "dandelion", "cornflower"]))


def yard_flowerbed(v, x, z, rng):
    for dx in range(5):
        for dz in range(5):
            if (dx in (0, 4) or dz in (0, 4)):
                v.put(x + dx, 0, z + dz, "stone_brick_slab[type=bottom]") if (dx + dz) % 2 == 0 else \
                    v.put(x + dx, 0, z + dz, "mossy_stone_brick_slab[type=bottom]")
            elif rng.random() < 0.8:
                v.put(x + dx, 0, z + dz, rng.choice(["red_tulip", "white_tulip", "pink_tulip", "allium", "oxeye_daisy"]))


def yard_hedge(v, x, z, rng):
    with v.piece("hedge"):
        v.fill_keep(x, 0, z + 1, x + 4, 1, z + 1, "spruce_leaves[persistent=true]")
        v.fill_keep(x, 0, z + 3, x + 4, 0, z + 3, "spruce_leaves[persistent=true]")
    v.put(x + 2, 0, z + 2, "decorated_pot[facing=south]")


def yard_fountainlet(v, x, z, rng):
    with v.piece("fountainlet"):
        v.fill_keep(x + 1, 0, z + 1, x + 3, 0, z + 3, "polished_andesite")
        v.put(x + 2, 1, z + 2, "andesite_wall")
        v.put(x + 2, 2, z + 2, "lantern")
    v.swap(x + 2, 0, z + 2, x + 2, 0, z + 2, "water", "polished_andesite")


def yard_tree_spruce(v, x, z, rng):
    tree(v, x + 2, z + 2, "spruce", rng.randint(5, 7))


def yard_tree_birch(v, x, z, rng):
    tree(v, x + 2, z + 2, "birch", rng.randint(4, 6))


def yard_tree_oak(v, x, z, rng):
    tree(v, x + 2, z + 2, "oak", rng.randint(4, 5))


def yard_coop(v, x, z, rng):
    with v.piece("hen house"):
        v.fill_keep(x + 1, 0, z + 1, x + 3, 1, z + 2, "spruce_planks")
        v.fill_keep(x, 2, z, x + 4, 2, z + 3, "spruce_slab[type=bottom]")
        v.fill_keep(x, 0, z + 4, x + 4, 0, z + 4, "spruce_fence")
    v.swap(x + 2, 0, z + 2, x + 2, 0, z + 2, "hay_block", "spruce_planks")
    v.swap(x + 2, 1, z + 2, x + 2, 1, z + 2, "spruce_trapdoor[half=bottom,facing=south,open=true]", "spruce_planks")


def yard_drying(v, x, z, rng):
    with v.piece("drying rack"):
        v.fill_keep(x, 0, z + 2, x, 2, z + 2, "spruce_fence")
        v.fill_keep(x + 4, 0, z + 2, x + 4, 2, z + 2, "spruce_fence")
        v.fill_keep(x + 1, 2, z + 2, x + 3, 2, z + 2, "iron_chain[axis=x]")
        v.put(x + 2, 0, z + 1, "hay_block[axis=x]")
        v.put(x + 2, 0, z + 3, "barrel[facing=up]")


def yard_timber(v, x, z, rng):
    wood = rng.choice(["spruce", "dark_oak", "birch", "oak"])
    with v.piece("timber stack"):
        v.fill_keep(x, 0, z + 1, x + 4, 0, z + 3, "%s_log[axis=x]" % wood)
        v.fill_keep(x + 1, 1, z + 1, x + 3, 1, z + 3, "%s_log[axis=x]" % wood)
        v.fill_keep(x + 2, 2, z + 2, x + 2, 2, z + 2, "%s_log[axis=x]" % wood)


def yard_grind(v, x, z, rng):
    with v.piece("workyard"):
        v.put(x + 1, 0, z + 1, "grindstone[face=floor,facing=east]")
        v.put(x + 3, 0, z + 1, rng.choice(["anvil[facing=north]", "chipped_anvil[facing=east]", "damaged_anvil[facing=south]"]))
        v.put(x + 1, 0, z + 3, "barrel[facing=up]")
        v.put(x + 2, 0, z + 3, "barrel[facing=up]")
        v.put(x + 1, 1, z + 3, "barrel[facing=up]")
        v.put(x + 3, 0, z + 3, "stonecutter[facing=north]")


def yard_cart(v, x, z, rng):
    with v.piece("cart"):
        v.fill_keep(x + 1, 0, z + 2, x + 3, 0, z + 2, "spruce_slab[type=top]")
        v.put(x + 1, 0, z + 1, "spruce_trapdoor[half=bottom,facing=south,open=true]")
        v.put(x + 3, 0, z + 1, "spruce_trapdoor[half=bottom,facing=south,open=true]")
        v.put(x + 1, 0, z + 3, "spruce_trapdoor[half=bottom,facing=north,open=true]")
        v.put(x + 3, 0, z + 3, "spruce_trapdoor[half=bottom,facing=north,open=true]")
        v.put(x + 2, 1, z + 2, "hay_block")
        v.put(x, 0, z + 2, "spruce_fence")


def yard_scaffold(v, x, z, rng):
    with v.piece("scaffold"):
        v.fill_keep(x + 1, 0, z + 1, x + 1, 3, z + 1, "scaffolding[distance=0,bottom=false]")
        v.fill_keep(x + 2, 0, z + 1, x + 2, 2, z + 1, "scaffolding[distance=1,bottom=false]")
        v.put(x + 3, 0, z + 2, "stone_bricks")
        v.put(x + 3, 0, z + 3, "stone_brick_stairs[facing=west]")
        v.put(x + 2, 0, z + 3, "cobblestone")


# ----------------------------------------------------------------------------- street signs
STREETS_Z = {-40: "Kastellgasse", 44: "Weavers' Lane", 76: "Tanners' Row", 0: "Werner Avenue"}
STREETS_X = {-100: "Hunters' Way", -48: "Cynthia Street", 48: "Kristoff Street", 100: "Foundry Way", 0: "Doom Boulevard"}


def street_signs(v):
    """A signpost at the north-east corner of each crossing, naming both streets."""
    for zs, zn in STREETS_Z.items():
        v.section("street_signs_%d" % zs, "Doomstadt - street names along %s" % zn, (0, zs + 8))
        for xs, xn in STREETS_X.items():
            if xs == 0 and zs == 0:
                continue                      # the plaza
            placed = False
            for (dx, dz) in ((5, -5), (5, 5), (-5, 5), (-5, -5), (6, -6), (6, 6), (-6, 6), (-6, -6), (8, -5), (5, -8)):
                x, z = xs + dx, zs + dz
                if v.w.name(x, GROUND, z) in ("grass_block",) and v.is_air(x, 0, z, x, 2, z) and v.is_air(x - 1, 0, z - 1, x + 1, 1, z + 1):
                    with v.piece("signpost %s/%s" % (xn, zn)):
                        v.put(x, 0, z, "dark_oak_fence")
                        v.put(x, 1, z, "dark_oak_fence")
                    v.sign(x, 2, z, "dark_oak_sign[rotation=%d]" % (0 if dz < 0 else 8), [xn, "x", zn, ""], "black")
                    placed = True
                    break


# ----------------------------------------------------------------------------- road wear
def road_wear(v):
    """Worn setts where the traffic is: most at the gates and the market, least in quiet lanes."""
    rng = random.Random(1410)
    for (ax, title) in ((-90, "west"), (0, "centre"), (90, "east")):
        v.section("road_wear_%s" % title, "Doomstadt - worn streets (%s)" % title, (ax, 8))
        for _ in range(70):
            if title == "centre":
                x, z = rng.randint(-2, 1), rng.choice([rng.randint(30, 100), rng.randint(-66, -26), rng.randint(85, 101)])
            else:
                x = rng.randint(ax - 50, ax + 49)
                z = rng.randint(-2, 1)
            v.swap(x, GROUND, z, x + rng.randint(0, 1), GROUND, z + rng.randint(0, 1),
                   rng.choice(["cobblestone", "cracked_stone_bricks", "mossy_stone_bricks", "andesite"]), "stone_bricks", expect=0)
