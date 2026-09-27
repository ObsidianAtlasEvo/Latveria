"""Latveria Survival Expansion v2.

Adds working infrastructure around the finished Castle Doom & Doomstadt:

  UNDERGROUND  sewers under both avenues (manholes), the Great Cistern, and
               Doom's escape tunnel from the dungeon to the sewers and out
  EAST         Doomwerk industrial quarter: depository (sorted storage),
               foundry (hopper-fed smelter banks + dripstone lava farm),
               Golem Works (iron farm), Hall of Shadows (mob XP farm),
               tree farm, open-pit quarry and a mine shaft to diamond depth
  SOUTH        Doomstadt Exchange (villager trading hall), nursery (breeder),
               sugar cane, pumpkins & melons, bamboo, ranch, harbour & docks,
               freight yard and lighthouse
  WEST         Mephisto Gate Nether hub (two portals, nether wart farm),
               the Ambassador's Manor (player residence), escape-tunnel exit
  TRANSPORT    powered minecart lines plaza <-> east quarter and plaza <-> harbour
  DEFENCE      lever-fired arrow batteries in the gate turrets
  LIGHTING     a block-light audit of the whole capital adds lanterns wherever
               a monster could spawn at night

Every piece is checked against the simulated world left by the first build, so
nothing lands on top of an existing structure.
"""
import math
import random

from core import (Builder, GenError, disk_runs, ring_cells, loot, chest_items, sign, book, tc, pos, cx, cz,
                  rot_facing, FACINGS)
from castle import lamp_post, doombot_stand, guard_stand
from terrain import doom_banner
from layout import *

RNG = random.Random(2026)
VEC = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}

EAST = (151, -130, 300, 112)
SOUTH = (-150, 113, 150, 240)
WEST = (-300, -130, -151, 112)

WORLD = None   # sim.World of the first build, set by build_expansion.py


def free(x1, y1, z1, x2, y2, z2, allowed=("air",)):
    return WORLD.box_is(min(x1, x2), min(y1, y2), min(z1, z2), max(x1, x2), max(y1, y2), max(z1, z2), allowed)


def need_free(what, *box, allowed=("air",)):
    if not free(*box, allowed=allowed):
        raise GenError("%s would overlap existing blocks %s: %s" % (
            what, box, sorted(WORLD.box_names(*[min(box[i], box[i + 3]) if i < 3 else 0 for i in range(3)],
                                              *[max(box[i], box[i + 3]) for i in range(3)]))[:8]))


# --------------------------------------------------------------------------
# generic helpers
# --------------------------------------------------------------------------
def double_chest(b, x, y, z, facing, items=None, lt=None, strict=True):
    """Double chest: the LEFT half at (x,y,z), the RIGHT half one block clockwise of facing."""
    dx, dz = VEC[rot_facing(facing, 1)]
    for (px, pz, t) in ((x, z, "left"), (x + dx, z + dz, "right")):
        nbt = ""
        if t == "left" and items:
            nbt = chest_items(items)
        elif lt:
            nbt = loot(lt)
        b.set(px, y, pz, "chest[facing=%s,type=%s]%s" % (facing, t, nbt), strict=strict)


def forceload(b, box, add=True):
    x1, z1, x2, z2 = box
    b.raw("forceload %s %s %s %s %s" % ("add" if add else "remove", cx(x1), cz(z1), cx(x2), cz(z2)))


def clear_district(b, box, name):
    x1, z1, x2, z2 = box
    b.section("clear_" + name, "Clearing the %s" % name)
    b.air(x1, 0, z1, x2, 62, z2)
    b.fill(x1, -10, z1, x2, -5, z2, "stone")
    b.fill(x1, -4, z1, x2, -2, z2, "dirt")
    b.fill(x1, -1, z1, x2, -1, z2, "grass_block")


def road(b, x1, z1, x2, z2):
    b.fill(x1, -1, z1, x2, -1, z2, "stone_bricks")
    if x2 - x1 > z2 - z1:
        b.fill(x1, -1, z1, x2, -1, z1, "polished_andesite")
        b.fill(x1, -1, z2, x2, -1, z2, "polished_andesite")
    else:
        b.fill(x1, -1, z1, x1, -1, z2, "polished_andesite")
        b.fill(x2, -1, z1, x2, -1, z2, "polished_andesite")


def shell(b, x1, z1, x2, z2, h, wall="stone_bricks", floor="polished_andesite", roof="deepslate_tiles",
          trim="polished_deepslate", windows=True):
    """A rectangular hall: floor at y=-1, walls y 0..h-1, flat roof at y=h with a parapet."""
    b.fill(x1, -1, z1, x2, -1, z2, floor)
    b.walls(x1, 0, z1, x2, h - 1, z2, wall)
    for (px, pz) in ((x1, z1), (x1, z2), (x2, z1), (x2, z2)):
        b.fill(px, 0, pz, px, h, pz, trim)
    b.fill(x1, h, z1, x2, h, z2, roof)
    b.walls(x1, h + 1, z1, x2, h + 1, z2, wall)
    if windows:
        for x in range(x1 + 3, x2 - 1, 4):
            for z in (z1, z2):
                b.fill(x, 2, z, x, h - 3, z, "glass_pane")
        for z in range(z1 + 3, z2 - 1, 4):
            for x in (x1, x2):
                b.fill(x, 2, z, x, h - 3, z, "glass_pane")
    for x in range(x1 + 3, x2 - 1, 6):
        for z in range(z1 + 3, z2 - 1, 6):
            b.set(x, h - 1, z, "lantern[hanging=true]")
            b.set(x, h + 1, z, "lantern")


def door_in(b, x, z, facing, wood="spruce", y=0):
    b.air(x, y, z, x, y + 1, z)
    b.door(x, y, z, wood, facing)


def title_sign(b, x, y, z, facing, lines, color="dark_green"):
    b.set(x, y, z, "dark_oak_wall_sign[facing=%s]" % facing + sign(lines, color, True))


def lanterns_along_x(b, x1, x2, z, step=12, y=0):
    for x in range(x1, x2 + 1, step):
        lamp_post(b, x, y, z)


def lanterns_along_z(b, z1, z2, x, step=12, y=0):
    for z in range(z1, z2 + 1, step):
        lamp_post(b, x, y, z)


# --------------------------------------------------------------------------
# UNDERGROUND
# --------------------------------------------------------------------------
def tunnel(b, x1, z1, x2, z2, y0=-9, h=3, lining="stone_bricks", channel=True):
    """Lined sewer/tunnel with walking floor at y0 (floor block y0-1)."""
    x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
    b.fill(x1 - 1, y0 - 2, z1 - 1, x2 + 1, y0 + h, z2 + 1, lining)
    b.air(x1, y0, z1, x2, y0 + h - 1, z2)
    b.fill(x1, y0 - 1, z1, x2, y0 - 1, z2, "polished_andesite")
    if channel:
        if x2 - x1 >= z2 - z1:
            zc = (z1 + z2) // 2
            b.fill(x1, y0 - 1, zc, x2, y0 - 1, zc, "water")
        else:
            xc = (x1 + x2) // 2
            b.fill(xc, y0 - 1, z1, xc, y0 - 1, z2, "water")


def build_sewers(b):
    b.section("sewers", "The sewers of Doomstadt")
    # beneath Doom Boulevard and Werner Avenue (road surface y=-1, sewer walk y=-9..-7)
    tunnel(b, -2, -60, 2, 100)
    tunnel(b, -165, -2, 140, 2)
    # re-open the crossing (each tunnel's lining cuts into the other)
    b.air(-2, -9, -3, 2, -7, 3)
    b.air(-3, -9, -2, 3, -7, 2)
    b.fill(-3, -10, -2, 3, -10, 2, "polished_andesite")
    b.fill(-2, -10, -3, 2, -10, 3, "polished_andesite")
    b.fill(0, -10, -3, 0, -10, 3, "water")
    b.fill(-3, -10, 0, 3, -10, 0, "water")
    for z in range(-56, 100, 8):
        b.set(0, -7, z, "lantern[hanging=true]")
    for x in range(-160, 140, 8):
        if abs(x) <= 3:
            continue
        b.set(x, -7, 0, "lantern[hanging=true]")
    # manholes: ladder shafts up to a trapdoor flush with the street (clear of the rail lines)
    holes = [(-2, z, "east") for z in (-52, 36, 60, 88)] + [(x, -2, "south") for x in (-130, -90, -40, 40, 90, 130)]
    for (x, z, f) in holes:
        b.air(x, -8, z, x, -2, z)
        if f == "east":
            b.fill(x - 1, -8, z, x - 1, -2, z, "stone_bricks")
        else:
            b.fill(x, -8, z - 1, x, -2, z - 1, "stone_bricks")
        b.fill(x, -9, z, x, -2, z, "ladder[facing=%s]" % f)
        b.set(x, -1, z, "spruce_trapdoor[half=top,facing=%s,open=false]" % f)
    # sign board at the crossing
    b.set(3, -8, 3, "stone_bricks")
    b.set(3, -8, 4, "dark_oak_wall_sign[facing=south]" + sign(
        ["N: Castle Doom", "S: Great Cistern", "W: Mephisto Gate", "E: Doomwerk"], "dark_green", True))


def build_cistern(b):
    b.section("cistern", "The Great Cistern")
    x1, x2, z1, z2 = -26, 26, 28, 70
    b.fill(x1, -26, z1, x2, -12, z2, "deepslate_bricks")
    b.air(x1 + 1, -24, z1 + 1, x2 - 1, -13, z2 - 1)
    b.fill(x1 + 1, -25, z1 + 1, x2 - 1, -25, z2 - 1, "polished_deepslate")
    # walkway ring and pool
    b.fill(x1 + 1, -24, z1 + 1, x2 - 1, -22, z2 - 1, "polished_deepslate")
    b.fill(x1 + 4, -24, z1 + 4, x2 - 4, -22, z2 - 4, "water")
    for (px, pz) in ((x1 + 4, z1 + 4), (x2 - 4, z1 + 4)):
        pass
    # forest of columns
    for x in range(x1 + 5, x2 - 3, 7):
        for z in range(z1 + 5, z2 - 3, 7):
            b.fill(x, -25, z, x + 1, -13, z + 1, "polished_deepslate")
            b.fill(x, -14, z, x + 1, -14, z + 1, "chiseled_deepslate")
            b.fill(x, -21, z, x + 1, -21, z + 1, "chiseled_deepslate")
            b.set(x, -24, z - 1, "sea_lantern") if z - 1 > z1 + 4 else None
            b.set(x + 2, -13, z, "lantern[hanging=true]")
    for x in range(x1 + 3, x2 - 1, 6):
        b.set(x, -13, z1 + 2, "lantern[hanging=true]")
        b.set(x, -13, z2 - 2, "lantern[hanging=true]")
    for z in range(z1 + 3, z2 - 1, 6):
        b.set(x1 + 2, -13, z, "lantern[hanging=true]")
        b.set(x2 - 2, -13, z, "lantern[hanging=true]")
    # stair down from the sewer (west wall of the boulevard sewer at z 29..30)
    b.air(-3, -9, 29, -3, -7, 30)
    for k in range(12):
        x, y = -4 - k, -10 - k
        b.fill(x, y + 1, 29, x, y + 4, 30, "air")
        if y > -24:
            b.fill(x, -24, 29, x, y - 1, 30, "deepslate_bricks")
        b.fill(x, y, 29, x, y, 30, "deepslate_brick_stairs[facing=east]")
        b.fill(x, y + 5, 29, x, y + 5, 30, "deepslate_bricks") if y + 5 > -12 else None
    for k in range(4):
        b.fill(-4 - k, -12, 28, -4 - k, -6, 28, "deepslate_bricks")
        b.fill(-4 - k, -12, 31, -4 - k, -6, 31, "deepslate_bricks")
    b.set(-4, -7, 31, "air")


def build_escape_tunnel(b):
    b.section("escape_tunnel", "Doom's escape tunnel")
    # secret double door out of the dungeon corridor (x=-28, z -165..-164) through the keep wall
    tunnel(b, -40, -165, -31, -164, y0=2, h=3, lining="deepslate_bricks", channel=False)
    b.air(-30, 2, -165, -29, 4, -164)
    b.door(-29, 2, -165, "dark_oak", "west", "left")
    b.door(-29, 2, -164, "dark_oak", "west", "right")
    # stair down (south) from the dungeon level to the sewer level
    for k in range(12):
        z, y = -163 + k, 1 - k
        b.fill(-42, y - 2, z, -39, y + 4, z, "deepslate_bricks")
        b.air(-41, y, z, -40, y + 3, z)
        b.fill(-41, y, z, -40, y, z, "deepslate_brick_stairs[facing=north]")
    b.air(-41, 2, -164, -40, 4, -164)
    tunnel(b, -41, -151, -40, -61, y0=-9, h=3, lining="deepslate_bricks", channel=False)
    tunnel(b, -40, -61, -4, -60, y0=-9, h=3, lining="deepslate_bricks", channel=False)
    b.air(-3, -9, -61, -2, -7, -59)
    b.fill(-3, -10, -61, -2, -10, -59, "polished_andesite")
    for z in range(-148, -60, 10):
        b.set(-41, -7, z, "lantern[hanging=true]")
    for x in range(-36, -4, 10):
        b.set(x, -7, -60, "lantern[hanging=true]")
    b.set(-35, 4, -165, "lantern[hanging=true]")
    b.set(-27, 3, -166, "dark_oak_wall_sign[facing=south]" + sign(["ESCAPE", "ROUTE", "Doom's use only"], "red", True))
    b.set(-40, -9, -110, "chest[facing=east]" + chest_items(
        [("bread", 32), ("golden_apple", 2), ("torch", 32), ("ender_pearl", 4),
         ("potion", 2, 'potion_contents={potion:"minecraft:invisibility"}')]))
    # exit: from the west end of the avenue sewer up into a hermit's hut outside the west gate
    tunnel(b, -160, -8, -159, -3, y0=-9, h=3, channel=False)
    b.air(-161, -9, -3, -158, -7, -2)
    b.fill(-161, -10, -3, -158, -10, -2, "polished_andesite")
    b.fill(-161, -10, -9, -158, -1, -9, "stone_bricks")
    b.air(-160, -9, -8, -160, -2, -8)
    b.fill(-160, -9, -8, -160, -2, -8, "ladder[facing=south]")
    hx1, hx2, hz1, hz2 = -163, -156, -14, -7
    b.fill(hx1, -1, hz1, hx2, -1, hz2, "spruce_planks")
    b.walls(hx1, 0, hz1, hx2, 3, hz2, "stripped_spruce_log[axis=y]")
    b.fill(hx1 - 1, 4, hz1 - 1, hx2 + 1, 4, hz2 + 1, "spruce_slab[type=bottom]")
    b.fill(hx1, 4, hz1, hx2, 4, hz2, "spruce_planks")
    b.set(-160, -1, -8, "spruce_trapdoor[half=top,facing=south,open=false]")
    door_in(b, -159, hz2, "north")
    b.set(-161, 0, -12, "crafting_table")
    b.set(-158, 0, -12, "chest[facing=west]" + chest_items([("bread", 16), ("leather_boots", 1), ("compass", 1)]))
    b.bed(-162, 0, -11, "brown", "north")
    b.set(-159, 3, -11, "lantern[hanging=true]")
    b.fill(hx1 + 2, 1, hz2, hx1 + 2, 2, hz2, "glass_pane")


# --------------------------------------------------------------------------
# TRANSPORT
# --------------------------------------------------------------------------
def rail_line(b, a, c_, fixed, axis, name_a, name_b):
    """Straight powered minecart line. axis 'x': x from a..c_ at z=fixed; 'z': z from a..c_ at x=fixed.
    The two rails at each end stay unpowered so parked carts are not launched; a player gives
    the cart a nudge forward and the powered track takes over."""
    shape = "east_west" if axis == "x" else "north_south"
    lo, hi = sorted((a, c_))
    P = (lambda v: (v, fixed)) if axis == "x" else (lambda v: (fixed, v))
    for v in range(lo - 1, hi + 2):
        x, z = P(v)
        if WORLD.name(x, 0, z) != "air" or WORLD.name(x, -1, z) in ("air", "water"):
            raise GenError("rail blocked at %d,%d (%s over %s)" % (x, z, WORLD.name(x, 0, z), WORLD.name(x, -1, z)))
    x1, z1 = P(lo)
    x2, z2 = P(hi)
    b.fill(x1, 0, z1, x2, 0, z2, "rail[shape=%s]" % shape)
    for v in range(lo + 2, hi - 1, 5):
        x, z = P(v)
        b.set(x, -1, z, "redstone_block")
        b.set(x, 0, z, "powered_rail[shape=%s,powered=true]" % shape)
    for end, step, nm in ((lo, 1, name_a), (hi, -1, name_b)):
        x, z = P(end + step * 2)
        b.set(x, -1, z, "redstone_block")
        b.set(x, 0, z, "powered_rail[shape=%s,powered=true]" % shape)
        bx, bz = P(end - step)
        b.set(bx, 0, bz, "polished_blackstone_bricks")
        b.set(bx, 1, bz, "lantern")
        for k in (0, 1):
            px, pz = P(end + step * k)
            b.summon("minecart", px + 0.5, 0.1, pz + 0.5, '{CustomName:"%s Express"}' % nm)


def build_rails(b):
    b.section("rails", "The Doomstadt minecart lines")
    rail_line(b, 26, 296, 2, "x", "Plaza", "Doomwerk")
    rail_line(b, 26, 150, 2, "z", "Plaza South", "Harbour")
    for (x, z, f, t) in ((26, 4, "south", ["PLAZA", "STATION", "East line:", "Doomwerk"]),
                         (4, 26, "east", ["PLAZA", "STATION", "South line:", "Harbour"])):
        b.set(x, 0, z, "polished_blackstone_bricks")
        b.set(x, 1, z, "polished_blackstone_bricks")
        side = (x, 1, z + 1) if f == "south" else (x + 1, 1, z)
        b.set(*side, "dark_oak_wall_sign[facing=%s]" % f + sign(t, "dark_green", True))
        b.set(x, 2, z, "lantern")


# --------------------------------------------------------------------------
# EAST: Doomwerk industrial quarter
# --------------------------------------------------------------------------
def smelter_bank(b, x0, z0, n, block, fuel_items):
    """n smelters in a row facing south at y=1.  Input: chests on the y=4 gallery feed a
    hopper line (y=3) that one hopper per smelter (y=2) pulls down.  Fuel: chests at y=3
    behind, hopper line y=2, side hoppers into each smelter.  Output: hopper line under
    the smelters (y=0) into a double chest at the east end."""
    for i in range(n):
        x = x0 + i
        b.set(x, 0, z0, "hopper[facing=east]")
        b.set(x, 1, z0, "%s[facing=south]" % block)
        b.set(x, 2, z0, "hopper[facing=down]")
        b.set(x, 3, z0, "hopper[facing=east]")
        b.set(x, 1, z0 - 1, "hopper[facing=south]")
        b.set(x, 2, z0 - 1, "hopper[facing=east]")
    for i in range(0, n - 1, 2):
        double_chest(b, x0 + i + 1, 4, z0, "south")
        double_chest(b, x0 + i, 3, z0 - 1, "north", items=fuel_items if i == 0 else None)
    double_chest(b, x0 + n + 1, 0, z0, "south")


def build_foundry(b):
    b.section("foundry", "Doomwerk Foundry: smelter banks and lava works")
    x1, x2, z1, z2 = 160, 205, -62, -20
    shell(b, x1, z1, x2, z2, 9, wall="bricks", floor="polished_andesite", roof="deepslate_tiles", trim="polished_deepslate")
    door_in(b, (x1 + x2) // 2, z2, "north")
    door_in(b, (x1 + x2) // 2 + 1, z2, "north")
    title_sign(b, (x1 + x2) // 2 - 1, 3, z2 + 1, "south", ["DOOMWERK", "FOUNDRY", "Smelters & Lava"])
    fuel = [("coal_block", 32), ("coal_block", 32), ("charcoal", 64), ("lava_bucket", 1)]
    banks = [(164, -54, 12, "furnace", "FURNACES"), (164, -40, 8, "blast_furnace", "BLAST FURNACES"),
             (180, -40, 6, "smoker", "SMOKERS")]
    for (bx, bz, n, blk, label) in banks:
        smelter_bank(b, bx, bz, n, blk, fuel)
        # galleries: front walkway at y=3 for the input chests, rear at y=2 for fuel
        b.fill(bx - 1, 3, bz + 1, bx + n + 2, 3, bz + 2, "spruce_planks")
        b.fill(bx - 1, 4, bz + 3, bx + n + 2, 4, bz + 3, "spruce_fence")
        b.fill(bx - 1, 2, bz - 2, bx + n, 2, bz - 3, "spruce_planks")
        b.fill(bx - 1, 0, bz + 2, bx - 1, 2, bz + 2, "spruce_planks")
        b.fill(bx - 2, 0, bz + 2, bx - 2, 3, bz + 2, "ladder[facing=west]")
        b.fill(bx - 1, 0, bz - 3, bx - 1, 1, bz - 3, "spruce_planks")
        b.fill(bx - 2, 0, bz - 3, bx - 2, 2, bz - 3, "ladder[facing=west]")
        b.set(bx + n + 3, 0, bz + 1, "oak_sign[rotation=8]" + sign([label, "Top chests: ore", "Back chests: fuel",
                                                                      "Bottom right: output"], "black", False))
    # renewable lava: pointed dripstone under lava sources drips into cauldrons
    b.section("lava_works", "Doomwerk lava works")
    lx0, lz = 190, -54
    b.fill(lx0 - 1, 0, lz - 1, lx0 + 8, 5, lz + 1, "bricks")
    b.air(lx0, 0, lz, lx0 + 7, 1, lz)
    for i in range(8):
        x = lx0 + i
        b.set(x, 0, lz, "cauldron")
        b.set(x, 3, lz, "dripstone_block")
        b.set(x, 2, lz, "pointed_dripstone[vertical_direction=down,thickness=tip]")
    b.fill(lx0, 4, lz, lx0 + 7, 4, lz, "lava")
    b.fill(lx0 - 1, 5, lz - 1, lx0 + 8, 5, lz + 1, "glass")
    b.fill(lx0, 0, lz + 1, lx0 + 7, 1, lz + 1, "air")
    b.fill(lx0, 1, lz + 1, lx0 + 7, 1, lz + 1, "glass")
    b.set(lx0 + 3, 0, lz + 3, "oak_sign[rotation=8]" + sign(["LAVA WORKS", "Dripstone fills", "the cauldrons", "(renewable)"],
                                                             "black", False))
    b.set(lx0 - 2, 0, lz + 2, "chest[facing=south]" + chest_items([("bucket", 16)]))
    b.set(lx0 + 9, 0, lz, "lantern")


RACK_LABELS = ["Stone & Masonry", "Wood & Logs", "Ores & Ingots", "Gems & Treasure", "Food & Crops",
               "Redstone", "Mob Drops", "Nether", "The End", "Tools", "Weapons & Armour", "Potions",
               "Dyes & Wool", "Building Blocks", "Farming & Seeds", "Miscellaneous"]


def build_depository(b):
    b.section("depository", "The Doomstadt Depository (storage warehouse)")
    x1, x2, z1, z2 = 160, 201, -112, -70
    shell(b, x1, z1, x2, z2, 7, wall="stone_bricks", floor="polished_andesite", roof="deepslate_tiles")
    door_in(b, 180, z2, "north")
    door_in(b, 181, z2, "north")
    title_sign(b, 179, 3, z2 + 1, "south", ["THE", "DEPOSITORY", "Storage of", "Doomstadt"])
    spines = [-107, -100, -93, -86, -79]
    li = 0
    for s in spines:
        b.fill(164, 0, s, 188, 3, s, "spruce_planks")
        for side, f in ((-1, "north"), (1, "south")):
            label = RACK_LABELS[li % len(RACK_LABELS)]
            li += 1
            for i, x in enumerate(range(165, 188, 2)):
                for y in (0, 1):
                    # facing north: left half at x, right half one block east
                    if f == "north":
                        double_chest(b, x, y, s + side, f)
                    else:
                        double_chest(b, x + 1, y, s + side, f)
                b.set(x if f == "north" else x + 1, 2, s + side,
                      "spruce_wall_sign[facing=%s]" % f + sign([label, "#%d" % (i + 1)], "black", False))
    # receiving bay
    for i, x in enumerate(range(192, 199, 2)):
        double_chest(b, x, 0, -108, "south")
    for x in (193, 196):
        b.set(x, 0, -84, "crafting_table")
    b.set(195, 0, -80, "barrel[facing=up]" + chest_items([("name_tag", 4), ("oak_sign", 16), ("item_frame", 16), ("chest", 8)]))
    b.set(192, 0, -80, "cartography_table")
    b.set(198, 0, -88, "lectern[facing=west,has_book=true]" + book("Depository Rules", "Minister of Stores", [
        "Every rack is labelled. Put things back where they belong.",
        "The receiving bay (north-east) is for unsorted goods.",
        "By order of Doom: no one hoards in Latveria."]))


def ab_platform(b, cx, cz, P, pad_block="stone_bricks"):
    """Cross-channel collection floor: four dry 8x8 pads around a 2x2 hole at (cx..cx+1, cz..cz+1),
    with four recessed water channels flowing toward it (sources at the outer ends)."""
    # pads (solid floor, top at y=P)
    b.fill(cx - 8, P - 1, cz - 8, cx + 9, P, cz + 9, pad_block)
    arms = [((cx, cz - 8), (cx + 1, cz - 1), (cx, cz - 8), (cx + 1, cz - 8)),
            ((cx, cz + 2), (cx + 1, cz + 9), (cx, cz + 9), (cx + 1, cz + 9)),
            ((cx - 8, cz), (cx - 1, cz + 1), (cx - 8, cz), (cx - 8, cz + 1)),
            ((cx + 2, cz), (cx + 9, cz + 1), (cx + 9, cz), (cx + 9, cz + 1))]
    for (a1, a2, s1, s2) in arms:
        b.air(a1[0], P, a1[1], a2[0], P, a2[1])
        b.fill(s1[0], P, s1[1], s2[0], P, s2[1], "water")
    b.air(cx, P - 1, cz, cx + 1, P, cz + 1)


def build_golem_works(b):
    b.section("golem_works", "The Golem Works (iron farm)")
    cxg, czg = 252, -90
    K, P = 0, 4
    x1, x2, z1, z2 = cxg - 9, cxg + 10, czg - 9, czg + 10
    b.fill(x1, -1, z1, x2, P, z2, "stone_bricks")
    ab_platform(b, cxg, czg, P)
    # rim wall: stone with sea lanterns, glass cap (golems cannot spawn on glass)
    b.walls(x1, P + 1, z1, x2, P + 1, z2, "stone_bricks")
    b.walls(x1, P + 2, z1, x2, P + 2, z2, "glass")
    for x in range(x1 + 2, x2, 3):
        b.set(x, P + 1, z1, "sea_lantern")
        b.set(x, P + 1, z2, "sea_lantern")
    for z in range(z1 + 2, z2, 3):
        b.set(x1, P + 1, z, "sea_lantern")
        b.set(x2, P + 1, z, "sea_lantern")
    # kill shaft: hoppers at K, signs at K+1, lava blade at K+2
    b.air(cxg, K + 1, czg, cxg + 1, P, czg + 1)
    b.fill(cxg, K, czg, cxg + 1, K, czg + 1, "hopper[facing=east]")
    double_chest(b, cxg + 2, K, czg, "east")
    b.fill(cxg + 2, K + 1, czg, cxg + 2, K + 1, czg + 1, "glass")
    for x in (cxg, cxg + 1):
        b.set(x, K + 1, czg, "oak_wall_sign[facing=south]")
        b.set(x, K + 1, czg + 1, "oak_wall_sign[facing=north]")
    b.fill(cxg, K + 2, czg, cxg + 1, K + 2, czg + 1, "lava")
    # collection room and entrance
    b.air(cxg + 3, 0, czg - 2, cxg + 7, 2, czg + 3)
    b.air(cxg + 8, 0, czg, cxg + 9, 1, czg)
    door_in(b, cxg + 10, czg, "west")
    b.set(cxg + 7, 0, czg + 3, "lantern")
    b.set(cxg + 7, 0, czg - 2, "chest[facing=west]" + chest_items([("bucket", 4), ("oak_sign", 8), ("hopper", 2)]))
    b.set(cxg + 11, 2, czg + 1, "dark_oak_wall_sign[facing=east]" + sign(["GOLEM WORKS", "Iron farm:", "starts after", "first night"], "dark_green", True))
    # villager pod (glass, tinted roof) over the hole, and the zombie that frightens them
    py = P + 4
    b.fill(cxg - 2, py, czg - 1, cxg + 3, py + 4, czg + 2, "glass")
    b.fill(cxg - 2, py, czg - 1, cxg + 3, py, czg + 2, "stone_bricks")
    b.fill(cxg - 2, py + 4, czg - 1, cxg + 3, py + 4, czg + 2, "tinted_glass")
    b.air(cxg - 1, py + 1, czg, cxg + 2, py + 3, czg + 1)
    b.bed(cxg - 1, py + 1, czg, "white", "east")
    b.bed(cxg + 1, py + 1, czg, "white", "east")
    b.bed(cxg - 1, py + 1, czg + 1, "white", "east")
    b.fill(cxg + 3, py, czg, cxg + 5, py + 3, czg + 2, "glass")
    b.fill(cxg + 3, py, czg, cxg + 5, py, czg + 2, "stone_bricks")
    b.fill(cxg + 3, py + 3, czg, cxg + 5, py + 3, czg + 2, "tinted_glass")
    b.air(cxg + 4, py + 1, czg + 1, cxg + 4, py + 2, czg + 1)
    for i in range(3):
        b.summon_later("villager", cxg + 1.5, py + 1, czg + 1.5,
                       '{VillagerData:{profession:"minecraft:none",level:1,type:"minecraft:taiga"},CustomName:"Golem Works Hand %d",PersistenceRequired:1b}' % (i + 1))
    b.summon_later("zombie", cxg + 4.5, py + 1, czg + 1.5,
                   '{PersistenceRequired:1b,CanPickUpLoot:0b,CustomName:"The Frightener",equipment:{head:{id:"minecraft:carved_pumpkin",count:1}}}')
    # service ladder to the platform rim
    b.fill(x2 + 1, 0, czg + 6, x2 + 1, P + 2, czg + 6, "ladder[facing=east]")


def build_hall_of_shadows(b):
    b.section("hall_of_shadows", "The Hall of Shadows (mob XP farm)")
    xa, c = 232, -38
    Wl = 26                       # water level of the last channel segment
    Hk = Wl - 22                  # hoppers (mobs land on y=Hk+1 after a 21-block fall)
    top = Wl + 3                  # pad surface
    # dark hall block
    b.fill(xa - 1, top - 8, c - 7, xa + 32, top + 3, c + 8, "blackstone")
    b.air(xa, top + 1, c - 6, xa + 23, top + 2, c + 7)
    for k in range(4):
        sx = xa + 8 * k
        wl = Wl + 3 - k
        b.air(sx, wl, c, sx + 7, top + 2, c + 1)
        b.fill(sx, wl, c, sx, wl, c + 1, "water")
    # drop shaft beyond the channel end
    hx = xa + 32
    b.fill(hx - 1, 0, c - 1, hx + 2, top + 3, c + 2, "blackstone")
    b.air(hx, Hk + 1, c, hx + 1, Wl + 2, c + 1)
    b.air(xa + 24, Wl, c, xa + 31, top + 2, c + 1)
    b.fill(xa + 24, Wl, c, xa + 24, Wl, c + 1, "water")
    b.air(hx - 1, Wl, c, hx - 1, Wl + 2, c + 1)
    # kill chamber: hoppers into a double chest, glass above it, one head-height slot to strike through
    b.fill(hx, Hk, c, hx + 1, Hk, c + 1, "hopper[facing=east]")
    double_chest(b, hx + 2, Hk, c, "east")
    b.fill(hx + 2, Hk + 1, c, hx + 2, Hk + 1, c + 1, "glass")
    b.set(hx + 2, Hk + 2, c, "air")
    # player room with stairs up from the ground
    rx1, rx2 = hx + 3, hx + 6
    b.fill(rx1, 0, c - 2, rx2 + 1, Hk + 3, c + 3, "blackstone")
    b.air(rx1, Hk, c - 1, rx2, Hk + 2, c + 2)
    b.fill(rx1, Hk - 1, c - 1, rx2, Hk - 1, c + 2, "polished_blackstone")
    b.set(rx2, Hk, c + 2, "lantern")
    b.set(rx2, Hk, c - 1, "chest[facing=west]" + chest_items([("iron_sword", 1), ("bread", 16), ("experience_bottle", 4)]))
    door_in(b, rx2 + 1, c, "west", "dark_oak", y=Hk)
    for k in range(Hk):
        x = rx2 + 2 + k
        y = Hk - 1 - k
        b.fill(x, 0 if y > 0 else y, c, x, y, c, "blackstone")
        b.set(x, y, c, "blackstone_stairs[facing=west]")
        b.air(x, y + 1, c, x, y + 3, c)
    # light the roof so nothing spawns on top of the hall
    for x in range(xa + 2, xa + 32, 6):
        for z in (c - 5, c + 1, c + 6):
            b.set(x, top + 4, z, "lantern")
    b.set(rx2 + 1, Hk + 3, c + 1, "dark_oak_wall_sign[facing=east]" + sign(
        ["HALL OF", "SHADOWS", "Strike through", "the slot"], "dark_red", True))


def build_tree_farm(b):
    b.section("tree_farm", "The Doomwald tree plantation")
    x1, x2, z1, z2 = 156, 214, 14, 106
    species = ["oak_sapling", "birch_sapling", "spruce_sapling", "cherry_sapling", "jungle_sapling", "acacia_sapling"]
    grown = ["oak", "birch", "spruce", "cherry"]
    i = 0
    for x in range(x1 + 2, x2 - 1, 6):
        for z in range(z1 + 2, z2 - 1, 6):
            if i % 5 == 0:
                b.feature(grown[(i // 5) % len(grown)], x, 0, z)
            else:
                b.set(x, 0, z, species[i % len(species)] + "[stage=0]")
            i += 1
            b.set(x + 3, 0, z + 3, "lantern")
    # dark oak groves need 2x2 saplings
    for (x, z) in ((x2 - 4, z1 + 4), (x2 - 4, z2 - 6)):
        b.fill(x, 0, z, x + 1, 0, z + 1, "dark_oak_sapling[stage=0]")
    b.walls(x1, 0, z1, x2, 0, z2, "spruce_fence")
    b.set(x1, 0, (z1 + z2) // 2, "spruce_fence_gate[facing=east]")
    b.set(x1 + 1, 0, z1 + 1, "chest[facing=south]" + chest_items(
        [("iron_axe", 2), ("oak_sapling", 32), ("birch_sapling", 32), ("spruce_sapling", 32), ("bone_meal", 64)]))


def build_quarry(b):
    b.section("quarry", "The open-pit quarry")
    qx, qz = 262, 60
    for k in range(26):
        hx, hz = 26 - k, 24 - k
        if hx < 3:
            break
        b.air(qx - hx, -1 - k, qz - hz, qx + hx, -1 - k, qz + hz)
    b.walls(qx - 27, 0, qz - 25, qx + 27, 0, qz + 25, "spruce_fence")
    b.air(qx - 27, 0, qz - 1, qx - 27, 0, qz + 1)
    for x in range(qx - 24, qx + 25, 8):
        lamp_post(b, x, 0, qz - 27)
        lamp_post(b, x, 0, qz + 27)
    b.set(qx - 29, 0, qz + 2, "oak_sign[rotation=4]" + sign(["THE QUARRY", "26 terraces", "of honest", "Latverian stone"], "black", False))
    b.set(qx - 29, 0, qz - 3, "chest[facing=east]" + chest_items(
        [("iron_pickaxe", 2), ("iron_shovel", 1), ("torch", 64), ("bread", 16)]))


def build_mine(b):
    b.section("mine", "The Deep Mine (shaft to diamond depth)")
    mx, mz = 295, 60
    bottom = -128
    b.fill(mx - 1, bottom - 1, mz - 1, mx + 1, -1, mz + 1, "stone_bricks")
    b.air(mx, bottom, mz, mx, -1, mz)
    # pit-head house: walk in from the south and climb down
    b.fill(mx - 1, 0, mz - 1, mx + 1, 3, mz - 1, "stone_bricks")
    b.fill(mx - 1, 0, mz, mx - 1, 3, mz, "stone_bricks")
    b.fill(mx + 1, 0, mz, mx + 1, 3, mz, "stone_bricks")
    b.fill(mx - 1, 4, mz - 1, mx + 1, 4, mz + 1, "dark_oak_planks")
    b.fill(mx, bottom, mz, mx, 2, mz, "ladder[facing=south]")
    for (dx, dz) in ((-1, 1), (1, 1)):
        b.fill(mx + dx, 0, mz + dz, mx + dx, 3, mz + dz, "dark_oak_log")
    b.set(mx, 3, mz + 1, "lantern[hanging=true]")
    b.set(mx - 3, 0, mz + 2, "oak_sign[rotation=4]" + sign(["DEEP MINE", "Ladder down", "to diamond", "depth"], "black", False))
    for lvl, depth in (("Iron level", -60), ("Diamond level", bottom)):
        y = depth
        b.fill(mx - 4, y - 1, mz - 3, mx - 1, y + 3, mz + 3, "stone_bricks")
        b.air(mx - 3, y, mz - 2, mx - 1, y + 2, mz + 2)
        b.set(mx - 2, y, mz + 2, "lantern")
        b.set(mx - 3, y, mz - 2, "chest[facing=east]" + chest_items(
            [("torch", 64), ("torch", 64), ("iron_pickaxe", 1), ("bread", 16), ("water_bucket", 1), ("cobblestone", 64)]))
        b.set(mx - 3, y, mz + 2, "crafting_table")
        b.set(mx - 2, y + 1, mz - 2, "dark_oak_wall_sign[facing=south]" + sign([lvl, "Branches every", "3 blocks"], "black", False))
        # paved, lit main tunnel west (3 tall), 1x2 branches north and south
        b.fill(mx - 60, y - 1, mz, mx - 5, y - 1, mz, "stone_bricks")
        b.fill(mx - 60, y + 3, mz, mx - 5, y + 3, mz, "stone_bricks")
        b.air(mx - 60, y, mz, mx - 4, y + 2, mz)
        for x in range(mx - 8, mx - 60, -6):
            b.set(x, y + 2, mz, "lantern[hanging=true]")
        for x in range(mx - 7, mx - 58, -3):
            b.air(x, y, mz - 24, x, y + 1, mz - 1)
            b.air(x, y, mz + 1, x, y + 1, mz + 24)


# --------------------------------------------------------------------------
# SOUTH
# --------------------------------------------------------------------------
TRADERS = ["librarian", "librarian", "librarian", "librarian", "librarian", "librarian", "cleric", "cleric",
           "armorer", "armorer", "weaponsmith", "toolsmith", "toolsmith", "fletcher", "cartographer", "farmer",
           "butcher", "mason", "shepherd", "leatherworker", "fisherman", "librarian"]
JOBS = {"farmer": "composter[level=0]", "fisherman": "barrel[facing=up]", "shepherd": "loom[facing=%s]",
        "fletcher": "fletching_table", "librarian": "lectern[facing=%s]", "cartographer": "cartography_table",
        "cleric": "brewing_stand", "leatherworker": "cauldron", "mason": "stonecutter[facing=%s]",
        "butcher": "smoker[facing=%s]", "toolsmith": "smithing_table", "weaponsmith": "grindstone[face=floor,facing=%s]",
        "armorer": "blast_furnace[facing=%s]"}
TRADER_NAMES = ["Ottokar", "Jana", "Miroslav", "Vesna", "Dusan", "Ljuba", "Bratislav", "Zdenka", "Kazimir",
                "Rada", "Stanko", "Ivo", "Mila", "Branko", "Dana", "Goran", "Nevena", "Pero", "Sonja", "Teo",
                "Vuk", "Zora"]


def build_exchange(b):
    b.section("exchange", "The Doomstadt Exchange (villager trading hall)")
    x1, x2, z1, z2 = -64, -36, 116, 130
    shell(b, x1, z1, x2, z2, 6, wall="stone_bricks", floor="polished_andesite", roof="deepslate_tiles")
    cells = list(range(-62, -40, 2))
    n = 0
    for (zc, zj, face, zlo, zhi, zs) in ((118, 119, "south", 117, 119, 120), (128, 127, "north", 127, 129, 126)):
        b.fill(x1 + 1, 0, zlo, x2 - 1, 2, zhi, "stone_bricks")
        for x in cells:
            prof = TRADERS[n % len(TRADERS)]
            nm = TRADER_NAMES[n % len(TRADER_NAMES)]
            b.air(x, 0, zc, x, 1, zc)
            jb = JOBS[prof] % face if "%s" in JOBS[prof] else JOBS[prof]
            b.set(x, 0, zj, jb)
            b.set(x, 1, zj, "air")
            b.set(x, 2, zs, "spruce_wall_sign[facing=%s]" % face + sign([nm, prof.capitalize()], "black", False))
            b.summon_later("villager", x + 0.5, 0, zc + 0.5,
                           '{VillagerData:{profession:"minecraft:%s",level:1,type:"minecraft:taiga"},CustomName:"%s",PersistenceRequired:1b}'
                           % (prof, nm))
            n += 1
    door_in(b, x2, 123, "west")
    door_in(b, x2, 124, "west")
    title_sign(b, x2 + 1, 3, 123, "east", ["THE", "EXCHANGE", "Traders of", "Doomstadt"])
    b.fill(x2 + 1, -1, 122, -4, -1, 125, "stone_bricks")


def build_nursery(b):
    b.section("nursery", "The villager nursery")
    x1, x2, z1, z2 = -64, -44, 136, 152
    shell(b, x1, z1, x2, z2, 5, wall="bricks", floor="spruce_planks", roof="glass", windows=False)
    for i, x in enumerate(range(x1 + 2, x2 - 1, 2)):
        b.bed(x, 0, z1 + 2, ["red", "yellow", "lime", "light_blue", "pink", "white", "orange", "cyan", "magenta"][i % 9], "north")
    fx1, fz1 = x1 + 6, z1 + 6
    b.fill(fx1, -1, fz1, fx1 + 6, -1, fz1 + 6, "farmland[moisture=7]")
    b.set(fx1 + 3, -1, fz1 + 3, "water")
    b.fill(fx1, 0, fz1, fx1 + 6, 0, fz1 + 6, "carrots[age=7]")
    b.set(fx1 + 3, 0, fz1 + 3, "air")
    b.set(fx1 - 1, 0, fz1, "composter[level=0]")
    b.set(x2 - 2, 0, z2 - 2, "chest[facing=west]" + chest_items([("bread", 32), ("carrot", 64)]))
    # iron door with buttons, so babies cannot wander out
    dx = (x1 + x2) // 2
    b.air(dx, 0, z2, dx, 1, z2)
    b.door(dx, 0, z2, "", "north", iron=True)
    b.set(dx + 1, 1, z2 + 1, "stone_button[face=wall,facing=south]")
    b.set(dx + 1, 1, z2 - 1, "stone_button[face=wall,facing=north]")
    b.set(dx - 1, 2, z2 + 1, "dark_oak_wall_sign[facing=south]" + sign(["NURSERY", "Close the", "door behind you"], "black", False))
    for x in (x1 + 4, x2 - 4):
        b.set(x, 0, z2 - 3, "lantern")
    cxn, czn = (x1 + x2) // 2, z2 - 2
    b.summon_later("villager", cxn + 0.5, 0, czn + 0.5,
                   '{VillagerData:{profession:"minecraft:farmer",level:1,type:"minecraft:taiga"},CustomName:"Nanny Greta",PersistenceRequired:1b}')
    for nm in ("Petar", "Ilona"):
        b.summon_later("villager", cxn + 1.5, 0, czn + 0.5,
                       '{VillagerData:{profession:"minecraft:none",level:1,type:"minecraft:taiga"},CustomName:"%s",PersistenceRequired:1b}' % nm)


def build_cane_melon_bamboo(b):
    b.section("south_fields", "Sugar cane, pumpkins, melons and bamboo")
    x1, x2 = -140, -112
    # sugar cane: water channels with sand banks
    for zc in range(120, 161, 5):
        b.fill(x1, -1, zc, x2, -1, zc, "water")
        for s in (-1, 1):
            b.fill(x1, -1, zc + s, x2, -1, zc + s, "sand")
            b.fill(x1, 0, zc + s, x2, 1, zc + s, "sugar_cane")
    b.walls(x1 - 1, 0, 117, x2 + 1, 0, 164, "spruce_fence")
    b.set(x2 + 1, 0, 140, "spruce_fence_gate[facing=west]")
    # pumpkins and melons
    for i, zc in enumerate(range(172, 229, 7)):
        crop = "pumpkin" if i % 2 == 0 else "melon"
        b.fill(x1, -1, zc, x2, -1, zc, "water")
        for s in (-1, 1):
            b.fill(x1, -1, zc + s, x2, -1, zc + s, "farmland[moisture=7]")
            b.fill(x1, -1, zc + 2 * s, x2, -1, zc + 2 * s, "dirt")
            for x in range(x1, x2 + 1):
                if x % 2 == 0:
                    b.set(x, 0, zc + 2 * s, crop)
                    b.set(x, 0, zc + s, "attached_%s_stem[facing=%s]" % (crop, "north" if s < 0 else "south"))
                else:
                    b.set(x, 0, zc + s, "%s_stem[age=7]" % crop)
    b.walls(x1 - 1, 0, 168, x2 + 1, 0, 232, "spruce_fence")
    b.set(x2 + 1, 0, 200, "spruce_fence_gate[facing=west]")
    b.set(x2, 0, 169, "chest[facing=south]" + chest_items([("pumpkin_seeds", 16), ("melon_seeds", 16), ("sugar_cane", 32), ("iron_axe", 1)]))
    for z in range(120, 232, 12):
        b.set(x1 - 1, 1, z, "lantern")
        b.set(x2 + 1, 1, z, "lantern")
    # bamboo grove
    bx1, bx2, bz1, bz2 = -106, -82, 170, 230
    b.fill(bx1, -1, bz1, bx2, -1, bz2, "podzol")
    for x in range(bx1 + 1, bx2, 3):
        for z in range(bz1 + 1, bz2, 3):
            h = RNG.randint(4, 11)
            b.fill(x, 0, z, x, h - 2, z, "bamboo[age=1,leaves=none,stage=0]")
            b.set(x, h - 1, z, "bamboo[age=1,leaves=large,stage=0]")
    for z in range(bz1, bz2 + 1, 10):
        lamp_post(b, bx1 - 2, 0, z)
    b.set(bx1 - 3, 0, bz1 + 2, "oak_sign[rotation=4]" + sign(["BAMBOO GROVE", "scaffolding,", "fuel & pandas"], "black", False))


def build_ranch(b):
    b.section("ranch", "The Latverian ranch (breeding pens)")
    pens = [(-76, 176, -60, 200, ["cow"] * 6, [("wheat", 64), ("wheat", 64)], "COWS"),
            (-56, 176, -40, 200, ["sheep"] * 6, [("wheat", 64), ("shears", 1)], "SHEEP"),
            (-36, 176, -20, 200, ["pig"] * 5, [("carrot", 64), ("carrot_on_a_stick", 1)], "PIGS"),
            (-76, 206, -60, 230, ["chicken"] * 8, [("wheat_seeds", 64)], "CHICKENS"),
            (-56, 206, -40, 230, ["goat"] * 4, [("wheat", 64)], "GOATS"),
            (-36, 206, -20, 230, ["rabbit"] * 5, [("carrot", 32), ("dandelion", 16)], "RABBITS")]
    for (x1, z1, x2, z2, animals, feed, label) in pens:
        b.walls(x1, 0, z1, x2, 0, z2, "spruce_fence")
        b.set(x2, 0, (z1 + z2) // 2, "spruce_fence_gate[facing=west]")
        # shelter
        b.fill(x1 + 1, 0, z1 + 1, x1 + 1, 2, z1 + 1, "spruce_log")
        b.fill(x1 + 5, 0, z1 + 1, x1 + 5, 2, z1 + 1, "spruce_log")
        b.fill(x1 + 1, 0, z1 + 4, x1 + 1, 2, z1 + 4, "spruce_log")
        b.fill(x1 + 5, 0, z1 + 4, x1 + 5, 2, z1 + 4, "spruce_log")
        b.fill(x1 + 1, 3, z1 + 1, x1 + 5, 3, z1 + 4, "spruce_slab[type=bottom]")
        b.set(x1 + 3, 0, z1 + 2, "hay_block")
        b.set(x1 + 2, 0, z1 + 3, "water_cauldron[level=3]")
        b.set(x2 + 1, 0, (z1 + z2) // 2 + 2, "chest[facing=east]" + chest_items(feed))
        b.set(x2 + 1, 0, (z1 + z2) // 2 - 2, "oak_sign[rotation=4]" + sign([label, "Feed chest ->", "Breed me!"], "black", False))
        for (px, pz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
            b.set(px, 1, pz, "lantern")
        for i, a in enumerate(animals):
            b.summon_later(a, x1 + 4 + (i % 3) * 3, 0, z1 + 8 + (i // 3) * 4, "")


def build_harbour(b):
    b.section("harbour", "The Harbour of Doomstadt")
    lx1, lx2, lz1, lz2 = 34, 140, 158, 234
    b.fill(lx1 - 3, -1, lz1 - 3, lx2 + 3, -1, lz2 + 3, "sand")
    b.fill(lx1, -6, lz1, lx2, -6, lz2, "gravel")
    b.fill(lx1, -5, lz1, lx2, -1, lz2, "water")
    for _ in range(40):
        b.set(RNG.randint(lx1 + 10, lx2 - 2), 0, RNG.randint(lz1 + 2, lz2 - 2), "lily_pad")
    b.fill(lx1 + 20, -6, lz1 + 20, lx1 + 60, -6, lz1 + 50, "sand")
    # quay and piers
    b.fill(lx1 - 3, -1, lz1 - 3, lx1 + 1, -1, lz2 + 3, "stone_bricks")
    for pz in range(lz1 + 6, lz2 - 5, 14):
        b.fill(lx1 + 2, 0, pz, lx1 + 18, 0, pz + 2, "spruce_planks")
        b.fill(lx1 + 2, -5, pz, lx1 + 2, -1, pz, "spruce_log")
        for px in range(lx1 + 6, lx1 + 19, 6):
            b.fill(px, -5, pz, px, -1, pz, "spruce_log")
            b.fill(px, -5, pz + 2, px, -1, pz + 2, "spruce_log")
            b.set(px, 1, pz, "spruce_fence")
            b.set(px, 2, pz, "lantern")
        b.summon("oak_boat", lx1 + 10.5, -0.4, pz + 4.5, '{CustomName:"Latverian skiff"}')
        b.summon("spruce_boat", lx1 + 15.5, -0.4, pz - 1.5, '{}')
        b.set(lx1 + 17, 1, pz + 1, "barrel[facing=up]" + chest_items([("fishing_rod", 1)]))
    # fishermen's huts
    for i, hz in enumerate((lz1 + 2, lz1 + 40)):
        hx = lx1 - 12
        b.fill(hx, -1, hz, hx + 6, -1, hz + 5, "spruce_planks")
        b.walls(hx, 0, hz, hx + 6, 3, hz + 5, "spruce_planks")
        b.fill(hx - 1, 4, hz - 1, hx + 7, 4, hz + 6, "spruce_slab[type=bottom]")
        b.fill(hx, 4, hz, hx + 6, 4, hz + 5, "spruce_planks")
        door_in(b, hx + 6, hz + 2, "west")
        b.set(hx + 1, 0, hz + 1, "barrel[facing=up]")
        b.set(hx + 2, 0, hz + 1, "barrel[facing=up]" + loot("chests/village/village_fisher"))
        b.bed(hx + 1, 0, hz + 3, "blue", "south")
        b.set(hx + 4, 3, hz + 2, "lantern[hanging=true]")
        b.fill(hx + 3, 1, hz, hx + 3, 2, hz, "glass_pane")
        b.summon_later("villager", hx + 4.5, 0, hz + 3.5,
                       '{VillagerData:{profession:"minecraft:fisherman",level:1,type:"minecraft:taiga"},CustomName:"%s",PersistenceRequired:1b}' % ("Old Marek", "Salty Lida")[i])
    # freight yard by the rail terminus
    b.fill(6, -1, 138, 28, -1, 156, "polished_andesite")
    for x in range(8, 27, 4):
        for z in (140, 146):
            b.fill(x, 0, z, x + 1, 1, z + 1, "barrel[facing=up]")
    b.set(8, 0, 152, "chest[facing=east]" + chest_items([("rail", 64), ("powered_rail", 16), ("minecart", 4), ("redstone_torch", 16)]))
    b.set(9, 0, 152, "crafting_table")
    # crane
    b.fill(24, 0, 152, 24, 9, 152, "dark_oak_log")
    b.fill(25, 9, 152, 33, 9, 152, "dark_oak_planks")
    b.fill(33, 3, 152, 33, 8, 152, "iron_chain")
    b.set(33, 2, 152, "barrel[facing=down]")
    b.set(10, 0, 156, "oak_sign[rotation=0]" + sign(["FREIGHT YARD", "Harbour station", "north ->"], "black", False))
    # lighthouse
    tx, tz = lx2 + 1, lz2 + 1
    b.fill(tx - 2, -1, tz - 2, tx + 2, 24, tz + 2, "white_concrete")
    for y in range(3, 24, 6):
        b.fill(tx - 2, y, tz - 2, tx + 2, y + 2, tz + 2, "red_concrete")
    b.air(tx - 1, 0, tz - 1, tx + 1, 23, tz + 1)
    b.fill(tx - 1, 0, tz - 1, tx - 1, 24, tz - 1, "ladder[facing=south]")
    b.air(tx - 2, 0, tz, tx - 2, 1, tz)
    b.door(tx - 2, 0, tz, "spruce", "east")
    b.fill(tx - 3, 25, tz - 3, tx + 3, 25, tz + 3, "polished_deepslate")
    b.air(tx - 1, 25, tz - 1, tx - 1, 25, tz - 1)
    b.set(tx - 1, 25, tz - 1, "ladder[facing=south]")
    b.walls(tx - 3, 26, tz - 3, tx + 3, 26, tz + 3, "iron_bars")
    b.fill(tx, 26, tz, tx, 27, tz, "glowstone")
    b.fill(tx - 1, 28, tz - 1, tx + 1, 28, tz + 1, "red_concrete")
    b.set(tx, 29, tz, "lightning_rod")


# --------------------------------------------------------------------------
# WEST
# --------------------------------------------------------------------------
def portal(b, x, z, axis="x"):
    """Obsidian frame 4 wide x 5 tall in the x-y plane at z (axis x), lit with fire."""
    b.fill(x - 1, -1, z, x + 2, 3, z, "obsidian")
    b.air(x, 0, z, x + 1, 2, z)
    b.fill(x - 2, -1, z, x - 2, 5, z, "polished_blackstone_bricks")
    b.fill(x + 3, -1, z, x + 3, 5, z, "polished_blackstone_bricks")
    b.fill(x - 2, 4, z, x + 3, 4, z, "polished_blackstone_bricks")
    b.fill(x - 1, 5, z, x + 2, 5, z, "polished_blackstone_brick_slab[type=bottom]")
    b.set(x - 2, 6, z, "soul_lantern")
    b.set(x + 3, 6, z, "soul_lantern")
    b.set(x, 0, z, "fire")


def build_nether_hub(b):
    b.section("nether_hub", "Mephisto Gate: the Nether transport hub")
    x1, x2, z1, z2 = -252, -202, -46, -10
    b.fill(x1, -1, z1, x2, -1, z2, "polished_blackstone_bricks")
    b.fill(x1 + 2, -1, z1 + 2, x2 - 2, -1, z2 - 2, "polished_blackstone")
    for x in (-240, -216):
        portal(b, x, -30)
    b.set(-228, 0, -30, "polished_blackstone_bricks")
    b.set(-228, 1, -30, "polished_blackstone_bricks")
    b.set(-228, 2, -30, "lodestone")
    b.set(-228, 1, -29, "dark_oak_wall_sign[facing=south]" + sign(
        ["MEPHISTO GATE", "Nether blocks", "are 1:8 of", "the overworld"], "dark_red", True))
    for x in range(x1 + 2, x2 - 1, 8):
        for z in (z1 + 2, z2 - 2):
            b.fill(x, 0, z, x, 2, z, "polished_blackstone_wall")
            b.set(x, 3, z, "soul_lantern")
    b.set(-230, 0, -20, "chest[facing=north]" + chest_items(
        [("flint_and_steel", 1), ("gold_ingot", 8), ("golden_carrot", 16),
         ("obsidian", 10), ("compass", 1), ("map", 2)]))
    b.set(-226, 0, -20, "cartography_table")
    # nether wart farm on soul sand
    wx1, wx2, wz1, wz2 = -252, -236, -60, -50
    b.fill(wx1, -1, wz1, wx2, -1, wz2, "polished_blackstone_bricks")
    for z in range(wz1 + 1, wz2, 2):
        b.fill(wx1 + 1, -1, z, wx2 - 1, -1, z, "soul_sand")
        b.fill(wx1 + 1, 0, z, wx2 - 1, 0, z, "nether_wart[age=3]")
    b.walls(wx1, 0, wz1, wx2, 0, wz2, "nether_brick_fence")
    b.set(wx2, 0, (wz1 + wz2) // 2, "air")
    for (px, pz) in ((wx1, wz1), (wx2, wz1), (wx1, wz2), (wx2, wz2)):
        b.set(px, 1, pz, "soul_lantern")
    b.set(wx2 + 1, 0, wz1, "chest[facing=east]" + chest_items([("nether_wart", 32), ("blaze_powder", 8), ("glass_bottle", 16)]))
    b.set(wx2 + 1, 0, wz1 + 2, "brewing_stand")
    b.set(wx2 + 1, 0, wz1 + 3, "water_cauldron[level=3]")


def build_manor(b):
    b.section("manor", "The Ambassador's Manor (player residence)")
    x1, x2, z1, z2 = -236, -206, 22, 46
    mx = (x1 + x2) // 2
    b.fill(x1 - 6, -1, z2 + 1, x2 + 6, -1, z2 + 10, "grass_block")
    b.fill(x1, -1, z1, x2, -1, z2, "dark_oak_planks")
    b.walls(x1, 0, z1, x2, 5, z2, "stone_bricks")
    b.fill(x1, 6, z1, x2, 6, z2, "spruce_planks")
    b.walls(x1, 7, z1, x2, 11, z2, "calcite")
    b.fill(x1, 6, z1, x2, 6, z1, "stripped_dark_oak_log[axis=x]")
    b.fill(x1, 6, z2, x2, 6, z2, "stripped_dark_oak_log[axis=x]")
    for (px, pz) in ((x1, z1), (x1, z2), (x2, z1), (x2, z2)):
        b.fill(px, 0, pz, px, 11, pz, "dark_oak_log")
    for k in range(0, 14):
        y = 12 + k
        a1, a2, c1, c2 = x1 - 1 + k, x2 + 1 - k, z1 - 1 + k, z2 + 1 - k
        if a1 > a2 or c1 > c2:
            break
        if a1 == a2 or c1 == c2:
            b.fill(a1, y, c1, a2, y, c2, "deepslate_tiles")
            break
        b.fill(a1, y, c1, a2, y, c1, "deepslate_tile_stairs[facing=south]")
        b.fill(a1, y, c2, a2, y, c2, "deepslate_tile_stairs[facing=north]")
        b.fill(a1, y, c1 + 1, a1, y, c2 - 1, "deepslate_tile_stairs[facing=east]")
        b.fill(a2, y, c1 + 1, a2, y, c2 - 1, "deepslate_tile_stairs[facing=west]")
        if a2 - a1 > 1 and c2 - c1 > 1:
            b.fill(a1 + 1, y, c1 + 1, a2 - 1, y, c2 - 1, "deepslate_tiles")
    for x in range(x1 + 3, x2 - 1, 4):
        for z in (z1, z2):
            if z == z1 and abs(x - mx) <= 2:
                continue
            b.fill(x, 1, z, x, 3, z, "glass_pane")
            b.fill(x, 8, z, x, 10, z, "glass_pane")
    for z in range(z1 + 3, z2 - 1, 4):
        for x in (x1, x2):
            b.fill(x, 1, z, x, 3, z, "glass_pane")
            b.fill(x, 8, z, x, 10, z, "glass_pane")
    # entrance on the north side, facing the road from the Nether hub
    b.air(mx, 0, z1, mx + 1, 1, z1)
    b.door(mx, 0, z1, "dark_oak", "south", "right")
    b.door(mx + 1, 0, z1, "dark_oak", "south", "left")
    title_sign(b, mx - 1, 3, z1 - 1, "north", ["THE", "AMBASSADOR'S", "MANOR", "Guest of Doom"])
    # ground floor: great room with hearth, full workshop, storage wall
    b.fill(x1 + 1, 0, z1 + 1, x1 + 1, 4, z1 + 5, "bricks")
    b.set(x1 + 1, 0, z1 + 3, "campfire[lit=true]")
    for i, blk in enumerate(["crafting_table", "furnace[facing=east]", "smoker[facing=east]",
                             "blast_furnace[facing=east]", "smithing_table", "anvil[facing=north]",
                             "grindstone[face=floor,facing=east]", "stonecutter[facing=east]", "loom[facing=east]",
                             "cartography_table", "fletching_table"]):
        b.set(x1 + 1, 0, z1 + 8 + i, blk)
    for i in range(6):
        double_chest(b, x2 - 1, 0, z1 + 2 + 2 * i, "west")
        double_chest(b, x2 - 1, 1, z1 + 2 + 2 * i, "west")
    b.set(x2 - 1, 0, z1 + 14, "ender_chest[facing=west]")
    b.set(x2 - 1, 0, z1 + 15, "barrel[facing=up]")
    b.fill(mx - 3, 0, z1 + 8, mx + 3, 0, z1 + 12, "red_carpet")
    for x in range(x1 + 4, x2 - 2, 6):
        for z in range(z1 + 4, z2 - 2, 6):
            b.set(x, 5, z, "lantern[hanging=true]")
    # staircase along the south wall rising east, landing on the upper floor
    sz = z2 - 2
    for k in range(6):
        x = mx - 6 + k
        if k:
            b.fill(x, 0, sz, x, k - 1, sz + 1, "spruce_planks")
        b.fill(x, k, sz, x, k, sz + 1, "spruce_stairs[facing=east]")
    b.air(mx - 4, 6, sz, mx - 1, 6, sz + 1)
    b.fill(mx - 4, 7, sz - 1, mx - 1, 7, sz - 1, "spruce_fence")
    b.fill(mx - 5, 7, sz, mx - 5, 7, sz + 1, "spruce_fence")
    # upper floor: bedroom, enchanting study, brewing corner
    b.bed(x2 - 3, 7, z1 + 3, "green", "north")
    b.bed(x2 - 5, 7, z1 + 3, "green", "north")
    b.set(x2 - 1, 7, z1 + 1, "chest[facing=west]" + chest_items([("bread", 16), ("torch", 32), ("map", 1)]))
    ex, ez = x1 + 6, z1 + 8
    b.set(ex, 7, ez, "enchanting_table")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2 and not (dz == 2 and abs(dx) <= 1):
                b.fill(ex + dx, 7, ez + dz, ex + dx, 8, ez + dz, "bookshelf")
    b.set(ex + 3, 7, ez - 2, "lectern[facing=west]")
    b.set(x1 + 2, 7, z2 - 6, "brewing_stand")
    b.set(x1 + 3, 7, z2 - 6, "water_cauldron[level=3]")
    b.set(x1 + 2, 7, z2 - 8, "chest[facing=east]" + chest_items([("glass_bottle", 16), ("nether_wart", 16), ("blaze_powder", 4)]))
    for x in range(x1 + 4, x2 - 2, 6):
        for z in range(z1 + 4, z2 - 2, 6):
            b.set(x, 11, z, "lantern[hanging=true]")
    # garden behind: fountain, flowers, lamps, a horse
    gx, gz = mx - 8, z2 + 6
    for dx, zz1, zz2 in disk_runs(3):
        b.fill(gx + dx, -1, gz + zz1, gx + dx, -1, gz + zz2, "water")
    b.ring(gx, 0, gz, 4, 1.0, "stone_brick_slab[type=bottom]")
    for _ in range(40):
        x, z = RNG.randint(x1 - 5, x2 + 5), RNG.randint(z2 + 2, z2 + 9)
        if abs(x - gx) <= 5:
            continue
        b.set(x, 0, z, RNG.choice(["poppy", "cornflower", "allium", "azure_bluet", "oxeye_daisy"]))
    for x in (x1 - 4, x2 + 4):
        lamp_post(b, x, 0, z2 + 3)
    b.summon_later("horse", mx + 8.5, 0, z2 + 6.5,
                   '{Tame:1b,PersistenceRequired:1b,equipment:{saddle:{id:"minecraft:saddle",count:1}},CustomName:"Envoy"}')
    b.summon_later("cat", mx + 0.5, 0, z1 + 10.5, '{variant:"minecraft:black",PersistenceRequired:1b,CustomName:"Mephisto"}')


# --------------------------------------------------------------------------
# DEFENCE: lever-fired arrow batteries at the gates
# --------------------------------------------------------------------------
def arrow_battery(b, dispensers, levers, path, approach, sign_at=None):
    """Dispensers set into turret walls, each fired by a lever inside the turret; `path` is the
    list of turret-wall cells carved to let a person in, entered through a door at path[0]."""
    for (x, y, z, f) in dispensers:
        if WORLD.name(x, y, z) == "air":
            raise GenError("arrow battery: no wall at %d %d %d" % (x, y, z))
        b.set(x, y, z, "dispenser[facing=%s]" % f + chest_items([("arrow", 64), ("arrow", 64)]))
    for (x, y, z, f) in levers:
        if WORLD.name(x, y, z) != "air":
            raise GenError("arrow battery: lever cell %d %d %d is %s" % (x, y, z, WORLD.name(x, y, z)))
        b.set(x, y, z, "lever[face=wall,facing=%s]" % f)
    ax, az = approach
    if WORLD.name(ax, 0, az) != "air" or WORLD.name(ax, 1, az) != "air":
        raise GenError("arrow battery: approach %d %d blocked" % (ax, az))
    (dx, dz, df) = path[0]
    for (px, pz) in [p[:2] for p in path]:
        b.air(px, 0, pz, px, 1, pz)
    b.door(dx, 0, dz, "spruce", df)
    if sign_at:
        x, y, z, f = sign_at
        b.set(x, y, z, "spruce_wall_sign[facing=%s]" % f + sign(["GATE DEFENCE", "Flip a lever", "to loose", "arrows"], "red", False))


def build_gate_defences(b):
    b.section("gate_defences", "Gate defences (arrow batteries)")
    W, S = TOWN_X, TOWN_ZS
    for sgn in (-1, 1):
        fz = "south" if sgn < 0 else "north"      # dispensers shoot across the passage
        lf = "north" if sgn < 0 else "south"      # levers point away from their wall
        # west and east gates (turrets at x=+-W, z=+-7; passage z -2..2)
        for gx, inward in ((-W, 1), (W, -1)):
            arrow_battery(b,
                          [(gx, 1, 3 * sgn, fz), (gx + inward, 1, 3 * sgn, fz)],
                          [(gx, 1, 5 * sgn, lf), (gx + inward, 1, 5 * sgn, lf)],
                          [(gx + 2 * inward, 3 * sgn, "west" if inward > 0 else "east"),
                           (gx + 2 * inward, 4 * sgn, None), (gx + 2 * inward, 5 * sgn, None)],
                          (gx + 3 * inward, 3 * sgn))
        # south gate (turrets at x=+-7, z=S; passage x -2..2)
        fx = "east" if sgn < 0 else "west"
        lx = "west" if sgn < 0 else "east"
        arrow_battery(b,
                      [(3 * sgn, 1, S, fx), (3 * sgn, 1, S - 1, fx)],
                      [(5 * sgn, 1, S, lx), (5 * sgn, 1, S - 1, lx)],
                      [(3 * sgn, S - 2, "east" if sgn > 0 else "west"), (4 * sgn, S - 2, None), (5 * sgn, S - 2, None)],
                      (2 * sgn, S - 2))


# --------------------------------------------------------------------------
# roads & lighting of the new districts
# --------------------------------------------------------------------------
def build_east_roads(b):
    b.section("east_roads", "Roads of Doomwerk")
    road(b, 145, -3, 300, 3)
    road(b, 222, -128, 228, 110)
    for x in range(152, 300, 12):
        lamp_post(b, x, 0, 5)
        lamp_post(b, x, 0, -5)
    for z in range(-124, 110, 12):
        if -8 < z < 8:
            continue
        lamp_post(b, 220, 0, z)
        lamp_post(b, 230, 0, z)


def build_south_roads(b):
    b.section("south_roads", "Roads of the Southmarch")
    road(b, -3, 113, 3, 240)
    road(b, -140, 164, 150, 167)
    for z in range(116, 240, 12):
        lamp_post(b, -5, 0, z)
        lamp_post(b, 5, 0, z)


def build_west_roads(b):
    b.section("west_roads", "Roads of the West March")
    road(b, -300, -3, -145, 3)
    road(b, -232, -8, -228, 21)
    for x in range(-296, -146, 12):
        lamp_post(b, x, 0, 5)
        lamp_post(b, x, 0, -5)


# --------------------------------------------------------------------------
# lighting audit
# --------------------------------------------------------------------------
STATUE_ZONES = [(-10, 5, -6, 9, 40, 5), (-6, 15, -137, 6, 33, -129)]
AUDIT_BOXES = [(-142, -1, -68, 142, 60, 101),      # inside the town walls
               (-62, 11, -218, 62, 116, -100),     # castle island, walls, keep, towers
               (-12, 0, -96, 12, 20, -66),         # grand stair
               (-165, -26, -2, 140, -7, 100),      # sewers & cistern (column of boxes)
               (-44, -10, -166, -2, 5, -59),       # escape tunnel
               ]


def lighting_audit(b, world, boxes, exclude_boxes=(), where="the capital"):
    b.section("lighting_" + where.replace(" ", "_"), "Lighting audit of %s" % where)
    tree_cols = {(t[0] + dx, t[2] + dz) for t in world.trees for dx in range(-3, 4) for dz in range(-3, 4)}

    def excluded(x, y, z):
        if (x, z) in tree_cols:
            return True
        for (a, b_, c_, d, e, f) in exclude_boxes:
            if a <= x <= d and b_ <= y <= e and c_ <= z <= f:
                return True
        # keep doorways and ladders clear
        for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nm = world.name(x + dx, y, z + dz)
            if nm.endswith("_door") or nm == "ladder" or nm.endswith("_bed"):
                return True
        return False

    def in_statue(x, y, z):
        return any(a <= x <= d and b_ <= y <= e and c_ <= z <= f for (a, b_, c_, d, e, f) in STATUE_ZONES)

    placed = 0
    for box in boxes:
        for it in range(12):
            dark = world.dark_spawn_cells(box, exclude=excluded)
            if not dark:
                break
            taken = set()
            for (x, y, z) in sorted(dark, key=lambda p: (p[1], p[0], p[2])):
                key = (x // 7, y // 7, z // 7)
                if key in taken:
                    continue
                taken.add(key)
                blk = "light[level=15]" if in_statue(x, y, z) else "lantern"
                b.set(x, y, z, blk)
                world.apply("setblock %s %s" % (pos(x, y, z), blk))
                placed += 1
        # cells beside doors, ladders and beds get an invisible light block instead of a lantern
        def excluded2(x, y, z):
            if (x, z) in tree_cols:
                return True
            return any(a <= x <= d and b_ <= y <= e and c_ <= z <= f for (a, b_, c_, d, e, f) in exclude_boxes)
        for it in range(6):
            rest = world.dark_spawn_cells(box, exclude=excluded2)
            if not rest:
                break
            taken = set()
            for (x, y, z) in rest:
                key = (x // 7, y // 7, z // 7)
                if key in taken:
                    continue
                taken.add(key)
                b.set(x, y, z, "light[level=15]")
                world.apply("setblock %s %s" % (pos(x, y, z), "light[level=15]"))
                placed += 1
        rest = world.dark_spawn_cells(box, exclude=excluded2)
        if rest:
            print("  lighting: %d cells still dark in %s" % (len(rest), box))
    return placed
