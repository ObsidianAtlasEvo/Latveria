"""The Keep of Castle Doom and the Doom Tower.

Levels (floor block y / walking y):
  dungeon   1 / 2..10     prison, Nether crypt, treasury, Doombot factory, Time Platform
  ground   11 / 12..26    throne room, kitchen, dining hall, armoury, guard room
  second   27 / 28..36    library of sorcery, laboratory, gallery, balcony
  third    37 / 38..46    Doom's chambers, war room
  roof     47 / 48        battlements, bartizans, Doom Tower (to y 100, beacon on top)
Two mirrored stairwells (x -28..-20 and 20..28, z -162..-152) link every level.
"""
import random

from core import disk_runs, ring_cells, loot, chest_items, sign, tc
from castle import (WALL, TRIM, DARK, ROOF, GLASS, doombot_stand, guard_stand, book_nbt,
                    lamp_post)
from layout import KEEP
from terrain import doom_banner

X1, X2, Z1, Z2 = KEEP          # -30, 30, -196, -150
IX1, IX2, IZ1, IZ2 = X1 + 2, X2 - 2, Z1 + 2, Z2 - 2   # interior -28..28, -194..-152
FLOORS = {"dungeon": 1, "ground": 11, "second": 27, "third": 37, "roof": 47}


def chandelier(b, x, z, ceil, drop=4, light="lantern"):
    """Chain hanging from the block at y=ceil, a ring of four hanging lanterns."""
    yb = ceil - drop
    b.fill(x, yb, z, x, ceil - 1, z, "iron_chain")
    for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        b.set(x + dx, yb, z + dz, "polished_blackstone_wall")
        b.set(x + dx, yb - 1, z + dz, "%s[hanging=true]" % light)
    b.set(x, yb - 1, z, "%s[hanging=true]" % light)


def mirror(fn):
    """Run a builder twice: west side as written, east side mirrored in x."""
    def run(b):
        fn(b, 1)
        fn(b, -1)
    return run


# --------------------------------------------------------------------------
def build_keep_shell(b):
    b.section("keep_shell", "The Keep: raising the shell")
    b.fill(X1, 0, Z1, X2, 47, Z2, WALL)
    for y in (11, 27, 37, 47):
        b.fill(X1, y, Z1, X2, y, Z2, TRIM)
    b.air(IX1, 2, IZ1, IX2, 10, IZ2)
    b.air(IX1, 12, IZ1, IX2, 26, IZ2)
    b.air(IX1, 28, IZ1, IX2, 36, IZ2)
    b.air(IX1, 38, IZ1, IX2, 46, IZ2)
    # floors
    b.fill(IX1, 1, IZ1, IX2, 1, IZ2, "polished_deepslate")
    b.fill(IX1, 11, IZ1, IX2, 11, IZ2, "polished_deepslate")
    b.fill(IX1, 27, IZ1, IX2, 27, IZ2, "dark_oak_planks")
    b.fill(IX1, 37, IZ1, IX2, 37, IZ2, "spruce_planks")
    # exterior buttresses and plinth
    b.section("keep_facade", "The Keep: facade, windows, battlements")
    bx = [-30, -22, -14, -6]
    for x in bx + [-p - 1 for p in bx]:
        for z, dz in ((Z2 + 1, 1), (Z1 - 1, -1)):
            if abs(x) <= 8 and dz > 0:
                continue
            b.fill(x, 11, z, x + 1, 44, z, DARK)
            b.fill(x, 45, z, x + 1, 45, z, "polished_deepslate_stairs[facing=%s]" % ("north" if dz > 0 else "south"))
    for z in range(Z1, Z2 + 1, 8):
        for x, dx in ((X1 - 1, -1), (X2 + 1, 1)):
            b.fill(x, 11, z, x, 44, z + 1, DARK)
            b.fill(x, 45, z, x, 45, z + 1, "polished_deepslate_stairs[facing=%s]" % ("east" if dx < 0 else "west"))
    # tall lancet windows on the upper floors, all four faces
    for y0 in (29, 39):
        wx = [-26, -18, -10]
        for x in wx + [-p - 1 for p in wx]:
            for zo, zi in ((Z2, Z2 - 1), (Z1, Z1 + 1)):
                if abs(x) <= 8 and zo == Z2 and y0 == 29:
                    continue
                b.fill(x, y0, zo, x + 1, y0 + 5, zo, GLASS)
                b.fill(x, y0, zi, x + 1, y0 + 5, zi, "air")
                b.set(x, y0 + 6, zo, "deepslate_brick_stairs[facing=east,half=top]")
                b.set(x + 1, y0 + 6, zo, "deepslate_brick_stairs[facing=west,half=top]")
        for z in range(Z1 + 4, Z2 - 1, 8):
            for xo, xi in ((X1, X1 + 1), (X2, X2 - 1)):
                b.fill(xo, y0, z, xo, y0 + 5, z + 1, GLASS)
                b.fill(xi, y0, z, xi, y0 + 5, z + 1, "air")
    # ground floor windows for the wings (side faces only)
    for z in range(Z1 + 4, Z2 - 1, 8):
        for xo, xi in ((X1, X1 + 1), (X2, X2 - 1)):
            b.fill(xo, 15, z, xo, 20, z + 1, GLASS)
            b.fill(xi, 15, z, xi, 20, z + 1, "air")
    # roof & battlements
    b.fill(IX1, 47, IZ1, IX2, 47, IZ2, "deepslate_tiles")
    b.walls(X1, 48, Z1, X2, 48, Z2, WALL)
    for x in range(X1, X2 + 1, 2):
        b.set(x, 49, Z1, WALL)
        b.set(x, 49, Z2, WALL)
    for z in range(Z1, Z2 + 1, 2):
        b.set(X1, 49, z, WALL)
        b.set(X2, 49, z, WALL)
    for x in range(X1 + 6, X2 - 5, 8):
        for z in range(Z1 + 6, Z2 - 5, 8):
            if -10 <= x <= 10 and -184 <= z <= -164:
                continue
            b.set(x, 48, z, "lantern")
    # corner bartizans with copper cones
    for cx, cz in ((X1, Z1), (X2, Z1), (X1, Z2), (X2, Z2)):
        b.ring(cx, 38, cz, 3.5, 1.0, "deepslate_tile_slab[type=top]")
        for dx, z1, z2 in disk_runs(3):
            b.fill(cx + dx, 39, cz + z1, cx + dx, 53, cz + z2, WALL)
        for dx, z1, z2 in disk_runs(1):
            b.fill(cx + dx, 48, cz + z1, cx + dx, 52, cz + z2, "air")
        for y in (50,):
            for d in ((3, 0), (-3, 0), (0, 3), (0, -3)):
                b.set(cx + d[0], y, cz + d[1], GLASS)
                b.set(cx + d[0], y + 1, cz + d[1], GLASS)
        b.cone(cx, 54, cz, 3.4, 9, ROOF)
        b.set(cx, 63, cz, "lightning_rod")
        b.set(cx, 48, cz, "lantern")


def build_facade_south(b):
    b.section("keep_entrance", "The Keep: grand entrance and Doom's balcony")
    # entrance portal
    b.air(-2, 12, Z2 - 1, 2, 19, Z2)
    b.fill(-3, 11, Z2 + 1, 3, 11, Z2 + 3, "polished_deepslate")
    b.fill(0, 12, Z2 - 1, 0, 13, Z2, DARK)
    b.fill(-2, 14, Z2, 2, 18, Z2, "green_stained_glass")
    b.fill(-2, 19, Z2, 2, 19, Z2, "chiseled_deepslate")
    for x in (-2, 1):
        b.door(x, 12, Z2, "dark_oak", "north", "left")
        b.door(x + 1, 12, Z2, "dark_oak", "north", "right")
    b.fill(-2, 14, Z2 - 1, 2, 19, Z2 - 1, "air")
    # portal columns and lamps
    for x in (-4, 4):
        b.fill(x, 11, Z2 + 1, x, 20, Z2 + 1, "polished_blackstone")
        b.set(x, 21, Z2 + 1, "chiseled_polished_blackstone")
        b.set(x, 22, Z2 + 1, "soul_lantern")
    b.fill(-4, 20, Z2 + 1, 4, 20, Z2 + 1, "polished_blackstone_bricks")
    b.fill(-3, 19, Z2 + 1, 3, 19, Z2 + 1, "polished_blackstone_brick_stairs[facing=south,half=top]")
    # tapestries of Latveria down the facade
    for x in (-12, -11, 11, 12):
        for y in range(44, 28, -2):
            b.set(x, y, Z2 + 1, "green_wall_banner[facing=south]" +
                  (doom_banner() if y == 44 else doom_banner("plain")))
    # balcony where Doom addresses his people
    b.fill(-7, 27, Z2 + 1, 7, 27, Z2 + 4, "polished_deepslate")
    b.fill(-7, 26, Z2 + 1, 7, 26, Z2 + 4, "deepslate_tile_slab[type=top]")
    b.fill(-7, 28, Z2 + 4, 7, 28, Z2 + 4, "polished_blackstone_wall")
    b.fill(-7, 28, Z2 + 1, -7, 28, Z2 + 3, "polished_blackstone_wall")
    b.fill(7, 28, Z2 + 1, 7, 28, Z2 + 3, "polished_blackstone_wall")
    for x in (-7, 7):
        b.set(x, 29, Z2 + 4, "soul_lantern")
    # banners hang from the balcony front
    for x in (-5, 0, 5):
        b.set(x, 25, Z2 + 1, "green_wall_banner[facing=south]" + doom_banner())
    # balcony doors from the second-floor gallery
    b.air(-1, 28, Z2 - 1, 1, 30, Z2 - 1)
    b.door(0, 28, Z2, "dark_oak", "north")
    b.fill(-1, 28, Z2, -1, 30, Z2, GLASS)
    b.fill(1, 28, Z2, 1, 30, Z2, GLASS)
    b.set(0, 30, Z2, GLASS)


# --------------------------------------------------------------------------
# stairwells (s = +1 west, -1 east: x = s * -|x|)
# --------------------------------------------------------------------------
def _stairwell(b, s):
    X = lambda x: x * s  # x given for the west side (negative numbers)
    lo = lambda a, c: (min(X(a), X(c)), max(X(a), X(c)))
    # Run A: ground -> landing (north)
    for k in range(8):
        z, y = -153 - k, 12 + k
        xa, xb = lo(-28, -27)
        if k:
            b.fill(xa, 12, z, xb, 11 + k, z, WALL)
        b.fill(xa, y, z, xb, y, z, "deepslate_brick_stairs[facing=north]")
    xa, xb = lo(-28, -24)
    b.fill(xa, 12, -162, xb, 19, -161, WALL)
    b.fill(xa, 19, -162, xb, 19, -161, "polished_deepslate")
    # Run B: landing -> second floor (south)
    for k in range(8):
        z, y = -160 + k, 20 + k
        xa, xb = lo(-25, -24)
        b.fill(xa, 12, z, xb, 19 + k, z, WALL)
        b.fill(xa, y, z, xb, y, z, "deepslate_brick_stairs[facing=south]")
    xa, xb = lo(-25, -24)
    b.air(xa, 27, -157, xb, 27, -153)
    b.set(X(-25), 20, -160, "deepslate_brick_stairs[facing=south]")
    # Run C: second -> third floor (north)
    for k in range(10):
        z, y = -152 - k, 28 + k
        xa, xb = lo(-28, -27)
        if k:
            b.fill(xa, 28, z, xb, 27 + k, z, WALL)
        b.fill(xa, y, z, xb, y, z, "spruce_stairs[facing=north]")
    xa, xb = lo(-28, -27)
    b.air(xa, 37, -160, xb, 37, -155)
    # Run D: third floor -> roof (south)
    for k in range(10):
        z, y = -161 + k, 38 + k
        xa, xb = lo(-25, -24)
        if k:
            b.fill(xa, 38, z, xb, 37 + k, z, WALL)
        b.fill(xa, y, z, xb, y, z, "spruce_stairs[facing=south]")
    xa, xb = lo(-25, -24)
    b.air(xa, 47, -157, xb, 47, -153)
    # Run E: dungeon -> ground floor (south)
    for k in range(10):
        z, y = -162 + k, 2 + k
        xa, xb = lo(-22, -21)
        if k:
            b.fill(xa, 2, z, xb, 1 + k, z, WALL)
        b.fill(xa, y, z, xb, y, z, "deepslate_brick_stairs[facing=south]")
    xa, xb = lo(-22, -21)
    b.air(xa, 11, -162, xb, 11, -154)
    # railings around the openings
    fence = "dark_oak_fence"
    b.fill(X(-23), 12, -162, X(-23), 12, -154, fence)
    b.fill(X(-20), 12, -162, X(-20), 12, -154, fence)
    b.fill(X(-26), 28, -158, X(-26), 28, -153, fence)
    b.fill(X(-23), 28, -158, X(-23), 28, -153, fence)
    xa, xb = lo(-25, -24)
    b.fill(xa, 28, -158, xb, 28, -158, fence)
    b.fill(X(-26), 38, -161, X(-26), 38, -155, fence)
    xa, xb = lo(-28, -27)
    b.fill(xa, 38, -154, xb, 38, -154, fence)
    # stair hut on the roof
    xa, xb = lo(-26, -23)
    b.fill(xa, 48, -158, xb, 52, -151, WALL)
    xa2, xb2 = lo(-25, -24)
    b.air(xa2, 48, -157, xb2, 51, -152)
    b.fill(xa, 53, -158, xb, 53, -151, "deepslate_tile_slab[type=bottom]")
    b.air(X(-23), 48, -152, X(-23), 49, -152)
    b.door(X(-23), 48, -152, "spruce", "west" if s > 0 else "east")
    b.set(X(-24), 51, -155, "lantern[hanging=true]")
    # lights in the stairwell
    b.set(X(-20), 26, -158, "lantern[hanging=true]")
    b.set(X(-20), 36, -160, "lantern[hanging=true]")
    b.set(X(-21), 46, -158, "lantern[hanging=true]")
    b.set(X(-26), 10, -156, "lantern[hanging=true]")


def build_stairwells(b):
    b.section("keep_stairs", "The Keep: stairwells")
    _stairwell(b, 1)
    _stairwell(b, -1)


# --------------------------------------------------------------------------
# ground floor
# --------------------------------------------------------------------------
WINDOW_ART = [
    "..GGGGGGGGG..",
    ".GGGGGGGGGGG.",
    "GGGIIIIIIIGGG",
    "GGIIIIIIIIIGG",
    "GGIBBIIIBBIGG",
    "GGIIIIIIIIIGG",
    "GGIIIIBIIIIGG",
    "GGIIIIIIIIIGG",
    "GGIIBBBBBIIGG",
    "GGGIIIIIIIGGG",
    ".GGGIIIIIGGG.",
]
WIN = {"G": "green_stained_glass", "I": "light_gray_stained_glass", "B": "black_stained_glass"}


def build_throne_room(b):
    b.section("throne_room", "The Throne Room of Doom")
    # partitions between the hall and the wings
    for x in (-19, 19):
        b.fill(x, 12, IZ1, x, 26, IZ2, WALL)
    for x1, x2 in ((-28, -20), (20, 28)):
        b.fill(x1, 12, -177, x2, 26, -177, WALL)
        b.fill(x1, 12, -163, x2, 26, -163, WALL)
    # arches from the hall into the wings
    for x in (-19, 19):
        for zc in (-186, -170):
            b.air(x, 12, zc - 1, x, 15, zc + 1)
            b.set(x, 15, zc - 1, "deepslate_brick_stairs[facing=north,half=top]")
            b.set(x, 15, zc + 1, "deepslate_brick_stairs[facing=south,half=top]")
        b.air(x, 12, -153, x, 14, -152)
    # floor pattern
    for z in range(IZ1, IZ2 + 1, 4):
        b.fill(-18, 11, z, 18, 11, z, "deepslate_tiles")
    b.fill(-18, 11, -186, 18, 11, -186, "chiseled_deepslate")
    # ceiling beams
    for z in range(IZ1 + 2, IZ2, 6):
        b.fill(-18, 26, z, 18, 26, z, "dark_oak_log[axis=x]")
    # pillars
    pz = list(range(-188, -153, 6))
    for x in (-13, 12):
        for z in pz:
            b.fill(x, 12, z, x + 1, 26, z + 1, DARK)
            b.fill(x, 12, z, x + 1, 12, z + 1, "chiseled_deepslate")
            b.fill(x, 25, z, x + 1, 25, z + 1, "chiseled_deepslate")
    for z in pz:
        b.set(-11, 22, z, "green_wall_banner[facing=east]" + doom_banner())
        b.set(11, 22, z, "green_wall_banner[facing=west]" + doom_banner())
    # the dais
    b.fill(-10, 12, IZ1, 10, 12, -186, "polished_deepslate")
    b.fill(-10, 13, IZ1, 10, 13, -188, "polished_deepslate")
    b.fill(-10, 14, IZ1, 10, 14, -190, "polished_deepslate")
    b.fill(-10, 12, -186, 10, 12, -186, "deepslate_tile_stairs[facing=north]")
    b.fill(-10, 13, -188, 10, 13, -188, "deepslate_tile_stairs[facing=north]")
    b.fill(-10, 14, -190, 10, 14, -190, "deepslate_tile_stairs[facing=north]")
    b.fill(-3, 15, IZ1, 3, 15, -191, "green_carpet")
    # the throne
    b.fill(-1, 15, -193, 1, 18, -193, "polished_blackstone")
    b.set(0, 15, -192, "polished_blackstone_stairs[facing=north]")
    b.set(-1, 15, -192, "polished_blackstone_wall")
    b.set(1, 15, -192, "polished_blackstone_wall")
    b.set(0, 19, -193, "emerald_block")
    b.set(-1, 19, -193, "gilded_blackstone")
    b.set(1, 19, -193, "gilded_blackstone")
    b.set(0, 20, -193, "gold_block")
    b.set(0, 21, -193, "lightning_rod")
    b.set(-2, 15, -193, "polished_blackstone_stairs[facing=east]")
    b.set(2, 15, -193, "polished_blackstone_stairs[facing=west]")
    for x in (-4, 4):
        b.set(x, 15, -192, "polished_blackstone")
        b.set(x, 16, -192, "soul_campfire[lit=true]")
    doombot_stand(b, -6, 15, -191, yaw=0, name="Doombot Royal Guard", netherite=True)
    doombot_stand(b, 6, 15, -191, yaw=0, name="Doombot Royal Guard", netherite=True)
    # the great window: Doom's mask in stained glass
    for row, line in enumerate(WINDOW_ART):
        y = 26 - row
        for col, ch in enumerate(line):
            x = col - 6
            if ch in WIN:
                b.set(x, y, Z1, WIN[ch])
                b.set(x, y, Z1 + 1, "air")
    for x in range(-6, 7):
        if abs(x) > 2:
            b.set(x, 15, Z1 + 1, "sea_lantern")
    # carpet runner from the doors to the dais
    b.fill(-2, 12, -185, 2, 12, IZ2, "green_carpet")
    b.fill(-3, 12, -185, -3, 12, IZ2, "black_carpet")
    b.fill(3, 12, -185, 3, 12, IZ2, "black_carpet")
    # guards of honour lining the aisle
    for z in range(-181, -155, 6):
        doombot_stand(b, -8, 12, z, yaw=270)
        doombot_stand(b, 8, 12, z, yaw=90)
    # chandeliers
    for x in (-7, 7, 0):
        for z in range(-182, -154, 9):
            chandelier(b, x, z, 27, 5)
    for x in (-16, 16):
        for z in range(-190, -154, 8):
            b.set(x, 12, z, "lantern")
    chandelier(b, 0, -191, 27, 3, "soul_lantern")
    b.set(0, 12, IZ2 + 0, "green_carpet")


def build_west_wing(b):
    b.section("kitchen", "Kitchens and dining hall")
    # kitchen x -28..-20, z -194..-178
    for z in range(-193, -187):
        b.set(-28, 12, z, "smoker[facing=east]" if z % 2 else "furnace[facing=east]")
    b.fill(-28, 13, -193, -28, 13, -188, "bricks")
    b.fill(-28, 14, -193, -28, 26, -188, "bricks")
    b.set(-28, 12, -186, "water_cauldron[level=3]")
    b.set(-28, 12, -185, "crafting_table")
    b.set(-28, 12, -184, "barrel[facing=east]" + loot("chests/village/village_plains_house"))
    b.set(-28, 12, -183, "barrel[facing=east]" + chest_items(
        [("bread", 64), ("baked_potato", 64), ("pumpkin_pie", 16), ("cake", 1), ("cookie", 32),
         ("wheat", 64), ("sugar", 32), ("egg", 16), ("milk_bucket", 1)]))
    b.set(-28, 12, -182, "barrel[facing=east]" + chest_items(
        [("cooked_beef", 32), ("cooked_porkchop", 32), ("cooked_chicken", 32), ("cooked_salmon", 16),
         ("beetroot_soup", 1), ("mushroom_stew", 1), ("honey_bottle", 8)]))
    b.set(-28, 12, -181, "composter[level=3]")
    b.fill(-24, 12, -192, -22, 12, -181, "spruce_planks")
    b.fill(-24, 13, -192, -22, 13, -181, "spruce_slab[type=bottom]")
    b.set(-23, 13, -186, "spruce_planks")
    b.set(-23, 14, -186, "cake")
    b.set(-21, 12, -193, "hay_block")
    b.set(-20, 12, -193, "hay_block")
    b.set(-21, 13, -193, "hay_block")
    for z in (-190, -183):
        b.set(-24, 26, z, "lantern[hanging=true]")
    b.set(-20, 12, -180, "chest[facing=west]" + loot("chests/village/village_butcher"))
    # dining hall x -28..-20, z -176..-164
    b.fill(-25, 12, -174, -23, 12, -166, "dark_oak_planks")
    for z in range(-174, -165, 2):
        b.set(-26, 12, z, "dark_oak_stairs[facing=east]")
        b.set(-22, 12, z, "dark_oak_stairs[facing=west]")
    b.set(-24, 13, -170, "cake")
    b.set(-24, 13, -173, "candle[candles=3,lit=true]")
    b.set(-24, 13, -167, "candle[candles=3,lit=true]")
    b.set(-24, 12, -175, "dark_oak_stairs[facing=south]")
    chandelier(b, -24, -170, 27, 4)
    b.set(-28, 16, -170, "green_wall_banner[facing=east]" + doom_banner("latveria"))


def build_east_wing(b):
    b.section("armoury", "Armoury and guard room")
    # armoury x 20..28, z -194..-178
    names = ["Armour of the Latverian Guard", "Mark I Battle Suit", "Coronation Armour", "Hunting Armour"]
    kinds = ["iron", "diamond", "netherite", "chainmail"]
    for i, z in enumerate((-192, -188, -184, -180)):
        m = kinds[i]
        head = m + "_helmet"
        b.armor_stand(27, 12, z, 90, names[i], {
            "head": (m + "_helmet", None), "chest": (m + "_chestplate", None),
            "legs": (m + "_leggings", None), "feet": (m + "_boots", None),
            "mainhand": (("iron" if m == "chainmail" else m) + "_sword", None)})
    for z in (-193, -190, -186, -182):
        b.set(21, 12, z, "chest[facing=east]" + loot("chests/village/village_weaponsmith"))
    b.set(21, 12, -179, "chest[facing=east]" + chest_items(
        [("iron_sword", 1), ("iron_axe", 1), ("crossbow", 1), ("bow", 1), ("arrow", 64), ("shield", 1),
         ("iron_helmet", 1), ("iron_chestplate", 1), ("iron_leggings", 1), ("iron_boots", 1),
         ("mace", 1), ("wind_charge", 16), ("trident", 1)]))
    b.set(24, 12, -193, "smithing_table")
    b.set(25, 12, -193, "grindstone[face=floor,facing=south]")
    b.set(23, 12, -193, "anvil[facing=east]")
    b.set(24, 26, -186, "lantern[hanging=true]")
    b.set(24, 26, -181, "lantern[hanging=true]")
    b.set(28, 17, -186, "green_wall_banner[facing=west]" + doom_banner())
    # guard room x 20..28, z -176..-164
    b.fill(23, 12, -172, 25, 12, -168, "spruce_planks")
    b.set(24, 13, -170, "lantern")
    for z in (-172, -168):
        b.set(22, 12, z, "spruce_stairs[facing=east]")
        b.set(26, 12, z, "spruce_stairs[facing=west]")
    b.bed(27, 12, -175, "green", "east")
    b.bed(27, 12, -165, "green", "east")
    b.set(21, 12, -175, "chest[facing=east]" + loot("chests/village/village_taiga_house"))
    b.set(28, 12, -170, "barrel[facing=west]" + chest_items([("bread", 32), ("cooked_mutton", 16)]))
    b.set(21, 12, -165, "bell[attachment=floor,facing=east]")
    chandelier(b, 24, -170, 27, 4)
    guard_stand(b, 21, 12, -168, yaw=90)


# --------------------------------------------------------------------------
# second floor
# --------------------------------------------------------------------------
def build_second_floor(b):
    b.section("library", "Library of Sorcery")
    y = 28
    # partitions: z=-163 (rooms | gallery), x=0 (library | laboratory)
    b.fill(-19, y, -163, 19, 36, -163, WALL)
    b.fill(-28, y, -163, -20, 36, -163, WALL)
    b.fill(20, y, -163, 28, 36, -163, WALL)
    b.fill(0, y, IZ1, 0, 36, -164, WALL)
    for xd in (-10, 10):
        b.air(xd - 1, y, -163, xd, y + 2, -163)
    # ---- library (x -28..-1, z -194..-164) ----
    for z in range(-194, -163):
        if z in (-181, -180, -179):
            continue
        b.fill(-28, y, z, -28, y + 3, z, "bookshelf")
    for x in range(-27, -1):
        b.fill(x, y, -194, x, y + 3, -194, "bookshelf")
    b.fill(-28, y + 4, -194, -2, y + 4, -194, "dark_oak_planks")
    for xr in (-24, -19, -14):
        b.fill(xr, y, -191, xr, y + 2, -176, "bookshelf")
        b.fill(xr, y, -183, xr, y + 2, -183, "air")
        b.fill(xr, y + 3, -191, xr, y + 3, -176, "dark_oak_slab[type=bottom]")
    b.set(-28, y, -180, "chiseled_bookshelf[facing=east]")
    b.set(-28, y + 1, -180, "chiseled_bookshelf[facing=east]")
    # enchanting alcove: table with 15 bookshelves one block away
    ex, ez = -7, -178
    b.set(ex, y, ez, "enchanting_table")
    for dx in range(-2, 3):
        for dz in range(-2, 3):
            if max(abs(dx), abs(dz)) == 2 and not (dz == 2 and abs(dx) <= 1):
                b.fill(ex + dx, y, ez + dz, ex + dx, y + 1, ez + dz, "bookshelf")
    b.set(ex, y + 8, ez, "iron_chain")
    b.set(ex, y + 7, ez, "soul_lantern[hanging=true]")
    b.set(ex, y + 7, ez, "iron_chain")
    b.set(ex, y + 6, ez, "soul_lantern[hanging=true]")
    # sorcery corner: brewing, cauldrons, lecterns with tomes
    b.set(-26, y, -171, "brewing_stand")
    b.set(-25, y, -171, "brewing_stand")
    b.set(-27, y, -171, "water_cauldron[level=3]")
    b.set(-27, y, -168, "cauldron")
    b.set(-26, y, -165, "chest[facing=south]" + chest_items(
        [("blaze_powder", 16), ("nether_wart", 32), ("glass_bottle", 16), ("redstone", 32),
         ("glowstone_dust", 32), ("gunpowder", 16), ("fermented_spider_eye", 8), ("ghast_tear", 4),
         ("phantom_membrane", 4), ("dragon_breath", 2), ("lapis_lazuli", 64), ("experience_bottle", 32)]))
    b.set(-25, y, -165, "chest[facing=south]" + loot("chests/stronghold_library"))
    b.set(-24, y, -165, "chest[facing=south]" + loot("chests/stronghold_library"))
    b.set(-12, y, -168, "lectern[facing=south,has_book=true]" + book_nbt(
        "Of the Dark Arts", "Cynthia von Doom", [
            "The arts my mother practised were not evil. They were a tool, as a hammer is a tool. The Ancient One taught me that power is only as noble as the hand that wields it.",
            "Remember: every pact exacts a price. Read the terms. Then rewrite them.",
        ]))
    b.set(-4, y, -186, "lectern[facing=east,has_book=true]" + book_nbt(
        "Latverian Codex", "Victor von Doom", [
            "LATVERIA\nA sovereign monarchy in the Carpathian highlands. Capital: Doomstadt.\nRuler: Victor von Doom.",
            "I. There is no crime in Latveria, for Doom provides.\nII. No citizen shall want for bread, shelter, or medicine.\nIII. Doom's word is law.",
            "Victor was born to the Romani of Latveria. His father Werner was a healer; his mother Cynthia a sorceress. Both were taken from him by the cruelty of the old Baron.",
            "He studied at Empire State University, then journeyed to the Himalayas where he forged the mask he has worn ever since.",
            "He returned, overthrew the tyrant, and took the throne. Castle Doom has stood over Doomstadt ever since.",
        ]))
    for x in (-24, -14, -6):
        for z in (-188, -172):
            chandelier(b, x, z, 37, 3)
    b.fill(-27, y - 1, -192, -2, y - 1, -165, "dark_oak_planks")
    b.fill(-13, y, -175, -9, y, -171, "green_carpet")
    # ---- laboratory (x 1..28, z -194..-164) ----
    b.section("laboratory", "Doom's laboratory")
    b.fill(1, y - 1, IZ1, 28, y - 1, -164, "polished_deepslate")
    for z in range(IZ1, -163, 4):
        b.fill(1, y - 1, z, 28, y - 1, z, "smooth_stone")
    for x in range(3, 28, 5):
        for z in range(-192, -165, 6):
            b.set(x, 36, z, "waxed_copper_bulb[lit=true]")
    # workbenches around the walls
    bench = [("crafting_table", None), ("crafter[orientation=north_up]", None), ("smithing_table", None),
             ("blast_furnace[facing=south]", None), ("anvil[facing=east]", None),
             ("stonecutter[facing=south]", None), ("loom[facing=south]", None),
             ("cartography_table", None), ("fletching_table", None), ("grindstone[face=floor,facing=south]", None)]
    for i, (blk, _) in enumerate(bench):
        b.set(2 + i * 2, y, -194, blk)
    b.set(28, y, -192, "chest[facing=west]" + chest_items(
        [("redstone", 64), ("redstone_block", 16), ("repeater", 16), ("comparator", 16), ("observer", 16),
         ("piston", 16), ("sticky_piston", 16), ("iron_ingot", 64), ("copper_ingot", 64), ("quartz", 64),
         ("diamond", 16), ("netherite_ingot", 2), ("ender_pearl", 16), ("amethyst_shard", 32),
         ("echo_shard", 4), ("heart_of_the_sea", 1), ("nether_star", 1)]))
    b.set(28, y, -190, "chest[facing=west]" + loot("chests/ancient_city"))
    b.set(28, y, -188, "ender_chest[facing=west]")
    # central Doombot on the operating slab, under repair
    b.fill(12, y, -182, 16, y, -178, "polished_blackstone")
    b.fill(12, y + 1, -182, 16, y + 1, -178, "polished_blackstone_slab[type=bottom]")
    doombot_stand(b, 14, y + 1.5, -180, yaw=180, name="Doombot Mk. XIII (unfinished)")
    b.set(11, y, -183, "lightning_rod")
    b.set(17, y, -177, "lightning_rod")
    # consoles of redstone lamps and observers
    for z in range(-176, -165, 2):
        b.set(27, y, z, "observer[facing=west]")
        b.set(27, y + 1, z, "redstone_lamp")
        b.set(28, y + 1, z, "redstone_block")
        b.set(27, y + 2, z, "target")
    for x in (4, 8):
        b.set(x, y, -170, "brewing_stand")
        b.set(x, y, -172, "water_cauldron[level=3]")
    b.set(6, y, -168, "lodestone")
    b.set(6, y + 1, -168, "end_rod[facing=up]")
    b.set(20, y, -167, "jukebox")
    b.set(21, y, -167, "note_block")
    b.set(20, 36, -180, "lantern[hanging=true]")
    b.set(8, 36, -180, "lantern[hanging=true]")
    # ---- gallery (z -162..-152) ----
    b.section("gallery", "Gallery of Conquest")
    b.fill(-19, y - 1, -162, 19, y - 1, IZ2, "dark_oak_planks")
    b.fill(-18, y, -158, 18, y, -156, "green_carpet")
    for x in range(-16, 17, 8):
        b.set(x, 36, -157, "lantern[hanging=true]")
    for x in (-16, -12, -6, 6, 12, 16):
        b.fill(x, y, -162, x, y + 3, -162, "polished_deepslate")
        b.set(x, y + 4, -162, "lantern")
    trophies = [("netherite_sword", "The Blade of the Baron"), ("trident", "Trident of Namor (a gift)"),
                ("shield", "Shield of the Latverian Guard"), ("heart_of_the_sea", "Captured cosmic energy"),
                ("nether_star", "Fragment of the Power Cosmic"), ("totem_of_undying", "Relic of the Romani")]
    xs = [-16, -12, -6, 6, 12, 16]
    for (it, nm), x in zip(trophies, xs):
        b.summon("glow_item_frame", x, y + 2, -162 + 1,
                 '{Facing:3b,Fixed:1b,Invulnerable:1b,Item:{id:"minecraft:%s",count:1,components:{"minecraft:custom_name":%s}}}'
                 % (it, tc(nm, "gold")))


def build_third_floor(b):
    b.section("chambers", "Doom's private chambers")
    y = 38
    b.fill(-19, y, -163, 19, 46, -163, WALL)
    b.fill(-28, y, -163, -20, 46, -163, WALL)
    b.fill(20, y, -163, 28, 46, -163, WALL)
    b.fill(0, y, IZ1, 0, 46, -164, WALL)
    for xd in (-10, 10):
        b.air(xd - 1, y, -163, xd, y + 2, -163)
    b.fill(-19, y - 1, -162, 19, y - 1, IZ2, "dark_oak_planks")
    for x in range(-16, 17, 8):
        b.set(x, 46, -157, "lantern[hanging=true]")
    # ---- bedchamber (west) ----
    b.fill(-27, y - 1, IZ1, -1, y - 1, -164, "dark_oak_planks")
    b.fill(-20, y, -191, -8, y, -175, "green_carpet")
    b.fill(-20, y, -191, -20, y, -175, "black_carpet")
    b.fill(-8, y, -191, -8, y, -175, "black_carpet")
    # canopy bed
    b.bed(-15, y, -191, "green", "north")
    b.bed(-14, y, -191, "green", "north")
    for px in (-16, -13):
        for pz in (-193, -190):
            b.fill(px, y, pz, px, y + 3, pz, "dark_oak_fence")
    b.fill(-16, y + 4, -193, -13, y + 4, -190, "green_wool")
    b.set(-17, y, -193, "chest[facing=east]" + chest_items(
        [("diamond", 32), ("emerald", 64), ("gold_ingot", 64), ("enchanted_golden_apple", 2),
         ("netherite_helmet", 1), ("elytra", 1), ("totem_of_undying", 1), ("ender_pearl", 16)]))
    b.set(-12, y, -193, "chest[facing=west]" + loot("chests/woodland_mansion"))
    b.set(-18, y, -193, "lantern")
    b.set(-11, y, -193, "lantern")
    # the wardrobe: Doom's spare armour
    doombot_stand(b, -26, y, -192, yaw=90, name="Doom's Armour (ceremonial)", netherite=True)
    doombot_stand(b, -26, y, -188, yaw=90, name="Doom's Armour (battle)")
    # fireplace
    b.fill(-28, y, -182, -28, 46, -178, "bricks")
    b.set(-28, y, -180, "campfire[lit=true]")
    b.fill(-27, y + 3, -182, -27, y + 3, -178, "brick_slab[type=top]")
    b.set(-27, y + 4, -180, "potted_wither_rose")
    # reading corner and desk
    b.fill(-6, y, -176, -3, y, -175, "dark_oak_planks")
    b.set(-5, y + 1, -176, "lantern")
    b.set(-4, y + 1, -175, "potted_red_tulip")
    b.set(-5, y, -174, "dark_oak_stairs[facing=north]")
    b.fill(-2, y, -192, -2, y + 3, -184, "bookshelf")
    b.set(-3, y, -168, "lectern[facing=west,has_book=true]" + book_nbt(
        "Journal", "V. von Doom", [
            "Day 1,204 of my reign. The Richards family remains a thorn. Reed will never admit that my calculations were correct.",
            "Midsummer's Eve approaches. Again I will descend. Again I will face Mephisto. And one day, Mother, I will bring you home.",
            "Note: the portal in the crypt must be kept lit. The guard is forbidden to enter.",
        ]))
    chandelier(b, -14, -183, 47, 3)
    chandelier(b, -14, -170, 47, 3)
    b.set(-26, y, -166, "potted_blue_orchid")
    # ---- war room (east) ----
    b.section("war_room", "The war room")
    b.fill(1, y - 1, IZ1, 27, y - 1, -164, "spruce_planks")
    b.fill(9, y, -186, 19, y, -172, "dark_oak_planks")
    b.fill(9, y, -186, 19, y, -172, "dark_oak_planks")
    b.fill(10, y + 1, -185, 18, y + 1, -173, "green_carpet")
    for x in range(9, 20, 2):
        b.set(x, y, -187, "dark_oak_stairs[facing=south]")
        b.set(x, y, -171, "dark_oak_stairs[facing=north]")
    b.set(14, y + 1, -179, "lantern")
    b.set(10, y + 1, -175, "candle[candles=2,lit=true]")
    b.set(18, y + 1, -183, "candle[candles=2,lit=true]")
    b.set(27, y, -192, "cartography_table")
    b.set(27, y, -190, "chest[facing=west]" + chest_items(
        [("map", 16), ("compass", 2), ("recovery_compass", 1), ("spyglass", 2), ("paper", 64),
         ("writable_book", 4), ("ink_sac", 16), ("feather", 16), ("clock", 1)]))
    b.set(27, y, -188, "lectern[facing=west,has_book=true]" + book_nbt(
        "State of the Realm", "Minister of Doomstadt", [
            "Harvests: bountiful. Crime: none. Unemployment: none. Doombots on patrol: 400.",
            "Border with Symkaria: quiet. Wakanda: watchful. The Baxter Building: insufferable.",
        ]))
    for z in (-190, -184, -178, -172):
        b.set(1, y + 2, z, "green_wall_banner[facing=east]" + doom_banner("latveria"))
    chandelier(b, 14, -179, 47, 3)
    chandelier(b, 22, -170, 47, 3)
    b.set(22, y, -190, "lantern")
    b.set(6, y, -166, "lantern")


# --------------------------------------------------------------------------
# dungeon
# --------------------------------------------------------------------------
def build_dungeon(b):
    b.section("dungeon_walls", "The dungeons beneath the keep")
    y = 2
    # corridor z -166..-163, north wall z=-167, south wall z=-162
    b.fill(IX1, y, -167, IX2, 10, -167, WALL)
    b.fill(-19, y, -162, 19, 10, -162, WALL)
    for x in (-19, -5, 5, 19):
        b.fill(x, y, -161, x, 10, IZ2, WALL)
    b.fill(-5, y, IZ1, -5, 10, -168, WALL)
    # doorways
    for x, w in ((-17, 2), (10, 3)):
        b.air(x, y, -167, x + w - 1, y + 2, -167)
    b.air(-13, y, -162, -12, y + 2, -162)
    b.air(-1, y, -162, 1, y + 3, -162)
    b.fill(13, y, -162, 13, y + 1, -162, "air")
    b.door(13, y, -162, "", "south", iron=True)
    b.set(14, y + 1, -163, "lever[face=wall,facing=north]")
    b.set(12, y + 1, -161, "lever[face=wall,facing=south]")
    # corridor lighting
    for x in range(-26, 27, 6):
        b.set(x, 10, -165, "lantern[hanging=true]")
    b.fill(IX1, 1, -166, IX2, 1, -163, "deepslate_tiles")
    # ---- prison (x -18..-6, z -161..-152) ----
    b.section("prison", "The prison")
    for xw in (-15, -11, -7):
        b.fill(xw, y, -157, xw, 10, IZ2, WALL)
    b.fill(-18, y, -158, -6, 10, -158, WALL)
    for cx in (-17, -13, -9):
        b.fill(cx - 1, y, -158, cx + 1, y + 2, -158, "iron_bars")
        b.door(cx, y, -158, "", "north", iron=True)
        bx = cx + 2
        b.set(bx, y + 1, -159, "stone_button[face=wall,facing=north]")
        b.bed(cx - 1, y, -155, "gray", "south")
        b.set(cx + 1, y, -153, "cauldron")
        b.set(cx + 1, y, -156, "cobweb")
        b.set(cx, y, -153, "soul_lantern")
    b.set(-9, y, -155, "skeleton_skull[rotation=6]")
    b.set(-6, y, -160, "chest[facing=west]" + chest_items([("bread", 16), ("iron_ingot", 3), ("name_tag", 1)]))
    b.set(-12, 10, -160, "lantern[hanging=true]")
    b.set(-18, y, -161, "barrel[facing=up]" + loot("chests/simple_dungeon"))
    # ---- crypt with Doom's portal to Mephisto's realm (x -4..4, z -161..-152) ----
    b.section("crypt", "The crypt of the Midsummer portal")
    b.fill(-4, 1, -161, 4, 1, IZ2, "soul_soil")
    b.fill(-2, 1, -161, 2, 1, IZ2, "polished_blackstone_bricks")
    b.fill(-3, y, IZ2, 2, y + 5, IZ2, "crying_obsidian")
    b.fill(-2, y, IZ2, 1, y + 4, IZ2, "obsidian")
    b.fill(-1, y + 1, IZ2, 0, y + 3, IZ2, "air")
    b.set(-1, y + 1, IZ2, "fire")
    for x in (-4, 4):
        b.set(x, y, -160, "soul_lantern")
        b.set(x, y, -154, "soul_lantern")
        b.fill(x, y, -157, x, y + 2, -157, "chiseled_polished_blackstone")
        b.set(x, y + 3, -157, "soul_campfire[lit=true]")
    b.set(3, y, IZ2 + 0, "lectern[facing=north,has_book=true]" + book_nbt(
        "Pact of Midsummer", "Victor von Doom", [
            "Once each year, on Midsummer's Eve, Doom is permitted to challenge Mephisto for his mother's soul.",
            "This portal opens upon the burning realms. Enter prepared. Leave victorious.",
        ]))
    b.set(2, y + 2, -153, "dark_oak_wall_sign[facing=north]" + sign(
        ["MIDSUMMER", "PORTAL", "Enter at your", "own peril"], "red", True))
    b.set(0, 10, -157, "soul_lantern[hanging=true]")
    # ---- treasury (x 6..18, z -161..-152) ----
    b.section("treasury", "The treasury of Latveria")
    b.fill(6, 1, -161, 18, 1, IZ2, "polished_blackstone_bricks")
    b.fill(7, y, IZ2, 17, y, IZ2, "gold_block")
    b.fill(8, y + 1, IZ2, 16, y + 1, IZ2, "gold_block")
    b.fill(10, y + 2, IZ2, 14, y + 2, IZ2, "gold_block")
    b.set(12, y + 3, IZ2, "emerald_block")
    b.fill(18, y, -158, 18, y + 1, -154, "emerald_block")
    b.fill(6, y, -158, 6, y, -154, "diamond_block")
    b.set(6, y, -156, "raw_gold_block")
    for z, t in ((-160, "chests/end_city_treasure"), (-158, "chests/bastion_treasure"),
                 (-156, "chests/buried_treasure"), (-154, "chests/ancient_city")):
        b.set(16, y, z, "chest[facing=west]" + loot(t))
    b.set(8, y, -160, "chest[facing=east]" + chest_items(
        [("gold_block", 32), ("emerald_block", 16), ("diamond_block", 4), ("netherite_ingot", 4),
         ("enchanted_golden_apple", 3), ("gold_ingot", 64), ("emerald", 64)]))
    b.set(12, 10, -157, "lantern[hanging=true]")
    b.set(8, 10, -154, "lantern[hanging=true]")
    b.set(16, 10, -154, "lantern[hanging=true]")
    # ---- Doombot factory (x -28..-6, z -194..-168) ----
    b.section("factory", "The Doombot factory")
    b.fill(IX1, 1, IZ1, -6, 1, -168, "polished_deepslate")
    b.fill(-24, 1, IZ1, -22, 1, -170, "black_concrete")
    b.fill(-12, 1, IZ1, -10, 1, -170, "black_concrete")
    for x in (-23, -11):
        for i, z in enumerate(range(-191, -170, 4)):
            doombot_stand(b, x, 2, z, yaw=90, name="Doombot Unit %d%02d" % (4 if x < -15 else 7, i + 1))
    for z in range(-193, -169, 4):
        b.set(-28, y, z, "blast_furnace[facing=east]")
        b.set(-28, y, z + 1, "smithing_table")
        b.set(-7, y, z, "anvil[facing=north]")
        b.set(-7, y, z + 1, "crafter[orientation=west_up]")
    b.fill(-20, y, IZ1, -14, y, IZ1, "iron_block")
    b.fill(-19, y + 1, IZ1, -15, y + 1, IZ1, "iron_block")
    b.set(-17, y + 2, IZ1, "copper_block")
    b.set(-26, y, -169, "chest[facing=south]" + chest_items(
        [("iron_block", 32), ("iron_ingot", 64), ("redstone", 64), ("copper_block", 16), ("gold_ingot", 32),
         ("iron_helmet", 4), ("iron_leggings", 4), ("iron_boots", 4), ("armor_stand", 8)]))
    for x in range(-26, -6, 5):
        for z in (-190, -180, -172):
            b.set(x, 10, z, "waxed_copper_bulb[lit=true]")
    # ---- Time Platform chamber (x -4..28, z -194..-168) ----
    b.section("time_platform", "Doom's Time Platform")
    cx, cz = 12, -181
    b.fill(-4, 1, IZ1, IX2, 1, -168, "polished_blackstone_bricks")
    for dx, z1, z2 in disk_runs(8):
        b.fill(cx + dx, 1, cz + z1, cx + dx, 1, cz + z2, "smooth_quartz")
    for dx, z1, z2 in disk_runs(6):
        b.fill(cx + dx, 2, cz + z1, cx + dx, 2, cz + z2, "polished_blackstone")
    b.ring(cx, 2, cz, 6, 1.0, "chiseled_polished_blackstone")
    for dx, dz in ring_cells(6, 1.0)[::2]:
        b.set(cx + dx, 3, cz + dz, "end_rod[facing=up]")
    for dx, z1, z2 in disk_runs(2):
        b.fill(cx + dx, 2, cz + z1, cx + dx, 2, cz + z2, "crying_obsidian")
    b.set(cx, 3, cz, "lodestone")
    b.set(cx, 4, cz, "end_rod[facing=up]")
    b.set(cx, 10, cz, "end_rod[facing=down]")
    b.set(cx, 9, cz, "end_rod[facing=down]")
    # pylons around the platform
    for dx, dz in ((9, 0), (-9, 0), (0, 9), (0, -9), (6, 6), (-6, 6), (6, -6), (-6, -6)):
        b.fill(cx + dx, 2, cz + dz, cx + dx, 8, cz + dz, "iron_chain")
        b.set(cx + dx, 9, cz + dz, "waxed_copper_bulb[lit=true]")
        b.set(cx + dx, 2, cz + dz, "iron_block")
    # control consoles
    for x in range(-3, 28, 2):
        if x > 26:
            break
        b.set(x, y, IZ1, "observer[facing=south]" if x % 4 == 1 else "redstone_lamp[lit=false]")
        b.set(x, y + 1, IZ1, "daylight_detector" if x % 4 == 1 else "target")
    b.set(0, y, -185, "lectern[facing=east,has_book=true]" + book_nbt(
        "Time Platform Log", "V. von Doom", [
            "Destinations: Camelot (Morgan le Fay). Ancient Egypt (Rama-Tut). The far future.",
            "WARNING: the platform must never be activated without my express command. The guard will be dismantled.",
        ]))
    b.set(0, y, -170, "ender_chest[facing=east]")
    b.set(1, y, -170, "chest[facing=north]" + loot("chests/end_city_treasure"))
    b.set(24, y, -170, "calibrated_sculk_sensor[facing=north]")
    b.set(22, y, -170, "sculk_sensor")


# --------------------------------------------------------------------------
# Doom Tower
# --------------------------------------------------------------------------
TX1, TX2, TZ1, TZ2 = -8, 8, -182, -166
TOP = 100


def build_doom_tower(b):
    b.section("doom_tower", "The Doom Tower")
    b.fill(TX1, 47, TZ1, TX2, TOP, TZ2, WALL)
    for yb in range(56, TOP, 9):
        b.fill(TX1, yb, TZ1, TX2, yb, TZ2, TRIM)
    for (px, pz) in ((TX1, TZ1), (TX1, TZ2), (TX2, TZ1), (TX2, TZ2)):
        b.fill(px, 48, pz, px, TOP, pz, DARK)
    b.air(TX1 + 2, 48, TZ1 + 2, TX2 - 2, TOP - 1, TZ2 - 2)
    levels = list(range(56, TOP, 9))
    for fy in levels:
        b.fill(TX1 + 2, fy, TZ1 + 2, TX2 - 2, fy, TZ2 - 2, "dark_oak_planks")
    b.fill(TX1 + 2, TOP, TZ1 + 2, TX2 - 2, TOP, TZ2 - 2, "polished_deepslate")
    # tall slit windows on the east, west and south faces
    for fy in [47] + levels:
        for x in (-4, 4):
            b.fill(x, fy + 3, TZ2, x, fy + 6, TZ2, GLASS)
            b.fill(x, fy + 3, TZ2 - 1, x, fy + 6, TZ2 - 1, "air")
        for z in (-178, -170):
            b.fill(TX1, fy + 3, z, TX1, fy + 6, z, GLASS)
            b.fill(TX1 + 1, fy + 3, z, TX1 + 1, fy + 6, z, "air")
            b.fill(TX2, fy + 3, z, TX2, fy + 6, z, GLASS)
            b.fill(TX2 - 1, fy + 3, z, TX2 - 1, fy + 6, z, "air")
    # ladder on the north wall all the way to the top
    b.fill(0, 48, TZ1 + 2, 0, TOP, TZ1 + 2, "ladder[facing=south]")
    # entrance from the roof
    b.air(0, 48, TZ2 - 1, 0, 49, TZ2 - 1)
    b.door(0, 48, TZ2, "dark_oak", "north")
    b.fill(-1, 50, TZ2 + 1, 1, 50, TZ2 + 1, "deepslate_brick_slab[type=top]")
    for x in (-2, 2):
        b.set(x, 50, TZ2 + 1, "green_wall_banner[facing=south]" + doom_banner())
    # the Doom sigil on the tower's south face
    from castle import mask_relief
    mask_relief(b, -3, 92, TZ2 + 1)
    # per-level contents
    for i, fy in enumerate([47] + levels):
        yy = fy + 1
        b.set(-5, yy, -169, "lantern")
        b.set(5, yy, -169, "lantern")
        b.set(-5, yy, -179, "lantern")
        b.set(5, yy, -179, "lantern")
    doombot_stand(b, -4, 48, -176, yaw=90, name="Tower Sentinel")
    doombot_stand(b, 4, 48, -176, yaw=270, name="Tower Sentinel")
    # level 57: armoury of Doom
    ench = "enchantments={protection:4,unbreaking:3}"
    b.armor_stand(0, 57, -174, 0, "The Armour of Doom", {
        "head": ("netherite_helmet", ench), "chest": ("netherite_chestplate", ench),
        "legs": ("netherite_leggings", ench),
        "feet": ("netherite_boots", "enchantments={protection:4,feather_falling:4}"),
        "mainhand": ("netherite_sword", "enchantments={sharpness:5,unbreaking:3}")})
    b.set(-5, 57, -174, "smithing_table")
    b.set(5, 57, -174, "grindstone[face=floor,facing=south]")
    # level 66: alchemy
    b.set(-5, 66, -174, "brewing_stand")
    b.set(-4, 66, -174, "water_cauldron[level=3]")
    b.set(5, 66, -174, "chest[facing=west]" + chest_items(
        [("nether_wart", 32), ("blaze_rod", 8), ("magma_cream", 8), ("golden_carrot", 8),
         ("glistering_melon_slice", 8), ("rabbit_foot", 4), ("turtle_scute", 4), ("breeze_rod", 4)]))
    # level 75: astronomy
    b.set(0, 75, -174, "lectern[facing=south,has_book=true]" + book_nbt(
        "Star Charts", "V. von Doom", ["Galactus approaches from the direction of Sagittarius. The Silver Surfer's board must be studied."]))
    b.set(-5, 75, -174, "cartography_table")
    b.set(5, 75, -174, "barrel[facing=up]" + chest_items([("spyglass", 1), ("firework_rocket", 32), ("map", 8)]))
    # level 84: sleeping quarters of the watch
    b.bed(-5, 84, -176, "green", "south")
    b.bed(5, 84, -176, "green", "south")
    b.set(0, 84, -170, "chest[facing=north]" + loot("chests/village/village_taiga_house"))
    # level 93: the bell
    b.set(0, 99, -174, "bell[attachment=ceiling,facing=north]")
    b.set(-5, 93, -174, "barrel[facing=up]" + chest_items([("elytra", 1), ("firework_rocket", 64)]))
    # crown: parapet, pinnacles, beacon
    b.section("doom_tower_crown", "Crown of the Doom Tower and the Beacon of Doom")
    b.walls(TX1, TOP + 1, TZ1, TX2, TOP + 1, TZ2, WALL)
    for x in range(TX1, TX2 + 1, 2):
        b.set(x, TOP + 2, TZ1, WALL)
        b.set(x, TOP + 2, TZ2, WALL)
    for z in range(TZ1, TZ2 + 1, 2):
        b.set(TX1, TOP + 2, z, WALL)
        b.set(TX2, TOP + 2, z, WALL)
    for (px, pz) in ((TX1, TZ1), (TX1, TZ2 - 2), (TX2 - 2, TZ1), (TX2 - 2, TZ2 - 2)):
        b.fill(px, TOP + 1, pz, px + 2, TOP + 9, pz + 2, DARK)
        b.fill(px, TOP + 10, pz, px + 2, TOP + 10, pz + 2, "deepslate_tile_slab[type=bottom]")
        cxp, czp = px + 1, pz + 1
        b.fill(cxp, TOP + 10, czp, cxp, TOP + 14, czp, ROOF)
        b.set(cxp, TOP + 15, czp, "lightning_rod")
    b.fill(-1, TOP, -175, 1, TOP, -173, "iron_block")
    b.set(0, TOP + 1, -174, "beacon")
    b.set(0, TOP + 2, -174, "lime_stained_glass")
    b.set(0, TOP + 3, -174, "green_stained_glass")
    b.air(0, TOP, TZ1 + 2, 0, TOP, TZ1 + 2)
    b.set(0, TOP, TZ1 + 2, "ladder[facing=south]")
    for (x, z) in ((-5, -179), (5, -179), (-5, -169), (5, -169)):
        b.set(x, TOP + 1, z, "lantern")


def build_keep(b):
    build_keep_shell(b)
    build_facade_south(b)
    build_throne_room(b)
    build_west_wing(b)
    build_east_wing(b)
    build_second_floor(b)
    build_third_floor(b)
    build_dungeon(b)
    build_stairwells(b)   # after the rooms so the openings are carved last
    build_doom_tower(b)
