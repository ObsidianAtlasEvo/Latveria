"""Refinement v3 - Castle Doom: silhouette, eras, roofscape and interiors.

Everything is added into air or swapped for one named block (see v3core).  The castle is not
rebuilt: the keep, curtain, towers and gatehouse stay where they are.  What changes is the
story they tell - an old medieval core (rough, repaired, mossy north-west), a fortified
Renaissance front (the gate side, left formal), an industrial east (pipes, stacks, copper) and
Doom's own modern science on top (observatory, radio mast, laboratory exhausts), with one
arcane spire that does not match anything else on purpose.
"""
import math
import random

from core import disk_runs
from v3core import CRAG

ROOF = 48          # keep roof walking level (roof slab at y 47)
SPIRE = (-25, -22, -194, -191)


def disk(v, cx, y, cz, r, block, keep=True):
    for dx, z1, z2 in disk_runs(r):
        v.fill_keep(cx + dx, y, cz + z1, cx + dx, y, cz + z2, block)


def ring(v, cx, y1, y2, cz, r, block, inner):
    for dx, z1, z2 in disk_runs(r, inner):
        v.fill_keep(cx + dx, y1, cz + z1, cx + dx, y2, cz + z2, block)


# --------------------------------------------------------------------------- roofscape
def roofscape(v):
    v.section("castle_roof", "Castle Doom - the roofscape", (0, ROOF, -160))

    # the Arcane Spire (north-west corner): thin, dark, amethyst-tipped - older than the science
    with v.piece("arcane spire"):
        x1, x2, z1, z2 = SPIRE
        v.fill_keep(x1, ROOF, z1, x2, ROOF + 9, z2, "polished_blackstone_bricks")
        v.fill_keep(x1, ROOF + 10, z1, x2, ROOF + 10, z2, "chiseled_polished_blackstone")
        v.fill_keep(x1 + 1, ROOF + 11, z1 + 1, x2 - 1, ROOF + 20, z2 - 1, "blackstone")
        v.fill_keep(x1 + 1, ROOF + 21, z1 + 1, x2 - 1, ROOF + 21, z2 - 1, "crying_obsidian")
        v.fill_keep(x1 + 1, ROOF + 22, z1 + 1, x1 + 1, ROOF + 26, z1 + 1, "amethyst_block")
        v.put(x1 + 1, ROOF + 27, z1 + 1, "amethyst_cluster[facing=up]")
        for (x, z) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            v.put(x, ROOF + 11, z, "soul_lantern")
    # crying-obsidian band and purple slits in the spire shaft
    x1, x2, z1, z2 = SPIRE
    v.swap(x1, ROOF + 5, z1, x2, ROOF + 5, z2, "crying_obsidian", "polished_blackstone_bricks")
    v.swap(x1 + 1, ROOF + 14, z2 - 1, x2 - 1, ROOF + 16, z2 - 1, "purple_stained_glass", "blackstone")
    v.swap(x2 - 1, ROOF + 14, z1 + 1, x2 - 1, ROOF + 16, z2 - 1, "purple_stained_glass", "blackstone")

    # the Radio Mast (north-east corner): an iron lattice, Doom's link to his satellites
    with v.piece("radio mast"):
        x1, x2, z1, z2 = 22, 25, -194, -191
        v.fill_keep(x1, ROOF, z1, x2, ROOF + 1, z2, "polished_deepslate")
        for (x, z) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            v.fill_keep(x, ROOF + 2, z, x, ROOF + 12, z, "iron_bars")
        v.fill_keep(x1, ROOF + 13, z1, x2, ROOF + 13, z2, "polished_blackstone_slab[type=bottom]")
        for y in (ROOF + 6, ROOF + 10):
            v.fill_keep(x1 + 1, y, z1, x2 - 1, y, z1, "iron_chain[axis=x]")
            v.fill_keep(x1 + 1, y, z2, x2 - 1, y, z2, "iron_chain[axis=x]")
            v.fill_keep(x1, y, z1 + 1, x1, y, z2 - 1, "iron_chain[axis=z]")
            v.fill_keep(x2, y, z1 + 1, x2, y, z2 - 1, "iron_chain[axis=z]")
        v.fill_keep(x1 + 1, ROOF + 14, z1 + 1, x1 + 1, ROOF + 24, z1 + 1, "iron_bars")
        v.put(x1 + 1, ROOF + 25, z1 + 1, "redstone_block")
        v.put(x1 + 1, ROOF + 26, z1 + 1, "redstone_lamp[lit=true]")
        v.fill_keep(x1 + 1, ROOF + 27, z1 + 1, x1 + 1, ROOF + 31, z1 + 1, "iron_chain[axis=y]")
        v.put(x1 + 1, ROOF + 32, z1 + 1, "lightning_rod[facing=up]")
        # dish: a ring of iron trapdoors on the first platform, facing the sky
        v.put(x2, ROOF + 14, z2, "daylight_detector")
        v.put(x1, ROOF + 14, z2, "daylight_detector")

    # the Observatory (south-west): a weathered copper dome with a telescope slit
    cx, cz = -12, -162
    with v.piece("observatory"):
        ring(v, cx, ROOF, ROOF + 3, cz, 3.5, "polished_blackstone_bricks", 3.0)
        for k, (r, ri) in enumerate(((3.5, 2.0), (3.0, 1.5), (2.3, 0.8), (1.5, -1.0), (0.5, -1.0))):
            ring(v, cx, ROOF + 4 + k, ROOF + 4 + k, cz, r, "waxed_weathered_cut_copper", ri)
    # slit to the south and the telescope (lightning rods read as a brass tube)
    v.swap(cx, ROOF + 5, cz + 1, cx, ROOF + 6, cz + 3, "air", "waxed_weathered_cut_copper")
    for z in (cz + 2, cz + 3, cz + 4):
        v.put(cx, ROOF + 5, z, "lightning_rod[facing=south]")
    # doorway on the east side and the furnishings
    v.swap(cx + 4, ROOF, cz, cx + 4, ROOF + 1, cz, "air", "polished_blackstone_bricks")
    v.door(cx + 4, ROOF, cz, "dark_oak", "west")
    v.put(cx - 2, ROOF, cz, "cartography_table")
    v.put(cx + 1, ROOF, cz - 2, "chest[facing=south]")
    v.stock(cx + 1, ROOF, cz - 2, [(0, "spyglass", 1), (1, "map", 4), (2, "compass", 1), (3, "clock", 1)])
    v.lectern(cx - 1, ROOF, cz - 2, "south", "Observations", "V. von Doom", [
        "Night 212. The satellites pass over the Carpathians at the third hour. Signal clean.",
        "The old astronomers built their towers for gods. I built mine for weather, orbits and the enemy.",
        "Note for the staff: the telescope is not a toy. The dome is copper; it is supposed to be green."])
    v.put(cx, ROOF, cz, "polished_blackstone_slab[type=bottom]")

    # chimneys over the kitchen and the bedchamber fireplaces (the flues never reached the roof)
    for (z1, z2, h, name) in ((-191, -189, 7, "kitchen chimney"), (-181, -179, 5, "bedchamber chimney")):
        with v.piece(name):
            v.fill_keep(-29, ROOF, z1, -28, ROOF + h - 1, z2, "bricks")
            v.fill_keep(-29, ROOF + h, z1, -28, ROOF + h, z2, "stone_brick_slab[type=bottom]")
        v.swap(-28, ROOF + h, z1 + 1, -28, ROOF + h, z1 + 1, "campfire[lit=true,signal_fire=false]", "stone_brick_slab")

    # laboratory exhaust stacks (industrial, unequal heights)
    for (x, z, h) in ((11, -187, 8), (18, -187, 11), (13, -193, 6)):
        with v.piece("exhaust stack %d" % x):
            v.fill_keep(x, ROOF, z, x + 1, ROOF + h - 3, z + 1, "polished_blackstone_bricks")
            v.fill_keep(x, ROOF + h - 2, z, x + 1, ROOF + h - 2, z + 1, "waxed_exposed_copper")
            v.fill_keep(x, ROOF + h - 1, z, x + 1, ROOF + h - 1, z + 1, "waxed_exposed_copper_grate")
            v.put(x, ROOF + h, z, "campfire[lit=true]")
            v.put(x + 1, ROOF + h, z + 1, "lightning_rod[facing=up]")
        v.swap(x, ROOF + 2, z, x + 1, ROOF + 2, z + 1, "waxed_copper_bulb[lit=true]", "polished_blackstone_bricks")

    # the keep's rainwater tank (east): spruce staves on legs
    tx, tz = 20, -162
    with v.piece("water tank"):
        for (x, z) in ((tx - 1, tz - 1), (tx + 1, tz - 1), (tx - 1, tz + 1), (tx + 1, tz + 1)):
            v.fill_keep(x, ROOF, z, x, ROOF + 2, z, "stripped_spruce_log")
        ring(v, tx, ROOF + 3, ROOF + 6, tz, 2.0, "spruce_planks", -1.0)
        ring(v, tx, ROOF + 7, ROOF + 7, tz, 2.0, "spruce_slab[type=bottom]", -1.0)
    v.swap(tx - 2, ROOF + 4, tz - 2, tx + 2, ROOF + 4, tz + 2, "stripped_dark_oak_wood", "spruce_planks")

    # a lookout seat and the flag of Latveria on the south parapet
    with v.piece("roof flag"):
        v.fill_keep(0, ROOF, -153, 0, ROOF + 7, -153, "dark_oak_fence")
        v.put(1, ROOF + 7, -153, "green_wall_banner[facing=east]")


# --------------------------------------------------------------------------- curtain eras
def curtain_eras(v):
    """The oldest work is the north-west: rough, repaired and mossy.  The east is industrial."""
    v.section("castle_eras", "Castle Doom - centuries in the stone", (-40, -207))
    rng = random.Random(1214)
    # west face x = -52 (outer row) and north face z = -208: rough medieval coursing
    for _ in range(90):
        if rng.random() < 0.55:
            z = rng.randint(-206, -114)
            y = rng.randint(12, 24)
            w = rng.randint(1, 3)
            v.swap(-52, y, z, -52, y + rng.randint(0, 2), z + w, rng.choice(["cobbled_deepslate", "cobbled_deepslate", "tuff_bricks", "cracked_deepslate_bricks"]), "deepslate_bricks", expect=0)
        else:
            x = rng.randint(-50, -4)
            y = rng.randint(12, 24)
            w = rng.randint(1, 3)
            v.swap(x, y, -208, x + w, y + rng.randint(0, 2), -208, rng.choice(["cobbled_deepslate", "tuff_bricks", "cracked_deepslate_bricks", "mossy_cobblestone"]), "deepslate_bricks", expect=0)
    # green growth where the rain runs: vines on the north face, moss on the plinth
    for x in range(-49, -2, 4):
        top = 26 - rng.randint(0, 5)
        v.fill_keep(x, top - rng.randint(4, 9), -209, x, top, -209, "vine[south=true]")
    for z in range(-205, -115, 5):
        top = 25 - rng.randint(0, 5)
        v.fill_keep(-53, max(14, top - rng.randint(3, 7)), z, -53, top, z, "vine[east=true]")

    v.section("castle_east_industry", "Castle Doom - the industrial east", (40, -207))
    # copper service pipes down the east face (x = 53), each with a lit bulb as its valve
    for z in (-196, -178, -146, -128):
        with v.piece("pipe %d" % z):
            v.fill_keep(53, 14, z, 53, 24, z, "lightning_rod[facing=up]")
        v.put(53, 19, z + 1, "waxed_copper_bulb[lit=true]")
    # soot on the east parapet above the forge and the barracks kitchens
    for z in range(-200, -120, 7):
        v.swap(52, 20 + (z % 3), z, 52, 22 + (z % 3), z + 1, "polished_blackstone_bricks", "deepslate_bricks", expect=0)


# --------------------------------------------------------------------------- interiors
def interiors(v):
    v.section("castle_interiors", "Castle Doom - the halls within", (5, 12, -170))
    throne_hall(v)
    kitchen_loft(v)
    laboratory(v)
    sorcery_circle(v)
    war_room_map(v)


def war_room_map(v):
    """A carpet map of Latveria on the war-room table, sampled from the build itself: one carpet per
    ~55 x 33 blocks - castle black, water blue, roads and plazas light grey, roofs grey, fields yellow,
    grass green."""
    import numpy as np
    X1, X2, Z1, Z2, Y = 10, 18, -185, -173, 39      # the existing green tablecloth
    w = v.w
    nx, nz = X2 - X1 + 1, Z2 - Z1 + 1
    wx1, wx2, wz1, wz2 = -300, 300, -252, 240
    names = np.array([s_.split("[", 1)[0] for s_ in w.states])
    sub = w.W[w._sl(wx1, -12, wz1, wx2, 110, wz2)]
    solid = sub != 0
    ytop = solid.shape[1] - 1 - np.argmax(solid[:, ::-1, :], axis=1)
    top = np.take_along_axis(sub, ytop[:, None, :], axis=1)[:, 0, :]
    tn = names[top]
    h = ytop - 12
    anyv = solid.any(axis=1)
    built_words = ("stairs", "slab", "tiles", "planks", "brick", "terracotta", "copper", "concrete", "wool", "glass",
                   "calcite", "log", "blackstone", "deepslate", "smooth")
    for i in range(nx):
        for j in range(nz):
            a, b_ = int(i * (wx2 - wx1 + 1) / nx), int((i + 1) * (wx2 - wx1 + 1) / nx)
            c, d = int(j * (wz2 - wz1 + 1) / nz), int((j + 1) * (wz2 - wz1 + 1) / nz)
            m = anyv[a:b_, c:d].ravel()
            cell = tn[a:b_, c:d].ravel()[m]
            hh = h[a:b_, c:d].ravel()[m]
            if cell.size == 0:
                col = "green"
            else:
                wat = np.isin(cell, ["water"]).mean()
                road = np.isin(cell, ["stone_bricks", "polished_andesite", "cobblestone", "andesite", "dirt_path"]).mean()
                crop = np.isin(cell, ["wheat", "carrots", "potatoes", "beetroots", "farmland", "sugar_cane", "melon",
                                      "pumpkin", "bamboo", "hay_block", "nether_wart"]).mean()
                built = np.array([any(k in n for k in built_words) for n in cell]) & (hh >= 1)
                leaves = np.array(["leaves" in n for n in cell]).mean()
                if (hh >= 11).mean() > 0.35:
                    col = "black"
                elif wat > 0.3:
                    col = "blue"
                elif built.mean() > 0.18:
                    col = "gray"
                elif road > 0.12:
                    col = "light_gray"
                elif crop > 0.12:
                    col = "yellow"
                elif leaves > 0.05:
                    col = "lime"
                else:
                    col = "green"
            if col != "green" and v.name(X1 + i, Y, Z1 + j) == "green_carpet":
                v.swap(X1 + i, Y, Z1 + j, X1 + i, Y, Z1 + j, "%s_carpet" % col, "green_carpet")

def sorcery_circle(v):
    """The library's sorcery corner: a ring of purple candles round a soul lantern on the floor."""
    cx, cz, y = -21, -168, 28
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            d = (dx * dx + dz * dz) ** 0.5
            if 1.6 < d < 2.5:
                v.put(cx + dx, y, cz + dz, "purple_candle[candles=%d,lit=true]" % (1 + (dx + dz) % 3 if (dx + dz) % 3 >= 0 else 1))
    v.put(cx, y, cz, "soul_lantern")
    v.lectern(cx - 4, y, cz, "east", "On the Veil", "anonymous", [
        "Science explains the world. Sorcery negotiates with it. My son will need both.",
        "The circle is for focus only. Nothing has come through it. Nothing is supposed to."])


def throne_hall(v):
    # concealed throne defence: two dispensers flank the throne, each fired only by the lever on it
    for x in (-3, 3):
        v.swap(x, 15, -193, x, 15, -193, "dispenser[facing=south,triggered=false]", "green_carpet")
        v.stock(x, 15, -193, [(0, "arrow", 64), (1, "arrow", 64)])
        v.put(x, 16, -193, "lever[face=floor,facing=south,powered=false]")
    v.mechanism("Throne defence", "mechanically reasoned; requires live test",
                "Two dispensers of arrows at the throne's sides, facing down the hall. Each fires once per flip of the "
                "lever on its top. Manual only: arrows harm players, so nothing fires by itself.")


def kitchen_loft(v):
    """A spy loft over the kitchen with a grate onto the throne hall."""
    with v.piece("kitchen spy loft"):
        v.fill_keep(-23, 19, -184, -20, 19, -180, "dark_oak_slab[type=top]")
        v.fill_keep(-20, 12, -179, -20, 20, -179, "ladder[facing=west]")
        v.put(-23, 20, -184, "barrel[facing=up]")
        v.put(-23, 20, -183, "barrel[facing=up]")
    v.swap(-19, 21, -182, -19, 21, -182, "iron_bars", "deepslate_bricks")
    v.stock(-23, 20, -184, [(0, "bread", 3)])
    v.lectern(-22, 20, -184, "east", "Kitchen ledger", "Head cook", [
        "Whoever keeps the loft: the grate over the throne hall is for the Master's ears, not yours.",
        "Anyone caught listening will be moved to the Deep Cells. Signed, the cook."])


def laboratory(v):
    """Doom's laboratory (second floor east, x 1..28, z -194..-164, walk y 28): zones."""
    Y = 28
    # robotics bay (north-east): an operating table with a Doombot under repair
    with v.piece("robotics bench"):
        v.fill_keep(20, Y, -186, 24, Y, -185, "iron_block")
        v.put(19, Y, -186, "anvil[facing=north]")
        v.put(25, Y, -186, "smithing_table")
        v.fill_keep(22, Y + 5, -186, 22, Y + 8, -186, "iron_chain[axis=y]")
    v.once("lab_doombot", "armor_stand", 22.5, Y + 1, -185.5,
           '{ShowArms:1b,NoBasePlate:1b,Pose:{Head:[20f,0f,0f]},CustomName:"Doombot Mk VII"}', yaw=180)
    v.equip("lv3_lab_doombot", "armor.head", "iron_helmet")
    v.equip("lv3_lab_doombot", "armor.chest", "iron_chestplate", 'trim={pattern:"minecraft:silence",material:"minecraft:emerald"}')
    # energy research (east wall): a copper reactor core behind glass
    with v.piece("reactor core"):
        v.fill_keep(24, Y, -180, 26, Y, -178, "waxed_oxidized_copper")
        v.fill_keep(24, Y + 1, -180, 26, Y + 3, -178, "glass")
        v.fill_keep(24, Y + 4, -180, 26, Y + 4, -178, "waxed_oxidized_copper")
    v.swap(25, Y + 1, -179, 25, Y + 3, -179, "end_rod[facing=up]", "glass")
    v.swap(24, Y + 2, -180, 26, Y + 2, -178, "waxed_copper_bulb[lit=true]", "glass")
    # temporal research: clocks and a compass rose around the existing central table
    for (x, z) in ((17, -183), (11, -177)):
        v.put(x, Y, z, "lightning_rod[facing=up]") if (x, z) != (11, -183) else None
    # containment cell (south-west): tinted glass box around a specimen
    with v.piece("containment"):
        v.fill_keep(3, Y, -168, 5, Y + 3, -166, "tinted_glass")
    v.swap(4, Y + 1, -167, 4, Y + 2, -167, "air", "tinted_glass")
    v.put(4, Y + 1, -167, "wither_skeleton_skull[rotation=8]")
    v.sign(6, Y + 1, -166, "dark_oak_wall_sign[facing=east]", ["SPECIMEN 4", "Do not tap", "the glass"], "black")


def build(v):
    roofscape(v)
    curtain_eras(v)
    interiors(v)
