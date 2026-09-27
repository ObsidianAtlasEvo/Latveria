"""Doomstadt: the capital of Latveria, spread beneath Castle Doom.

Streets
  Doom Boulevard     x -3..3   (north-south, from the Grand Stair to the south gate)
  Werner Avenue      z -3..3   (east-west, west gate to east gate)
  lanes              z = -40, 44, 76  and  x = +-48, +-100   (5 wide)
"""
import math
import random

from core import disk_runs, ring_cells, loot, chest_items, sign, book, tc
from layout import *
from statue import build_statue
from terrain import doom_banner
from castle import lamp_post, doombot_stand

RNG = random.Random(1964)

NAMES = ["Anja", "Boris", "Dragan", "Elena", "Filip", "Greta", "Hanna", "Ivan", "Jelena", "Karl",
         "Lenka", "Milos", "Nadia", "Oskar", "Petra", "Radu", "Sanda", "Tomas", "Ursula", "Vlad",
         "Wanda", "Zoran", "Mira", "Stefan", "Irina", "Bogdan", "Katya", "Luka", "Marta", "Nikolai",
         "Olga", "Pavel", "Rosa", "Sergei", "Tatiana", "Viktor", "Yana", "Emil", "Dora", "Anton",
         "Klara", "Josef", "Ilse", "Gregor", "Magda", "Fritz", "Zelda", "Hugo"]

JOB = {"farmer": "composter[level=0]", "fisherman": "barrel[facing=up]", "shepherd": "loom[facing=south]",
       "fletcher": "fletching_table", "librarian": "lectern[facing=south]", "cartographer": "cartography_table",
       "cleric": "brewing_stand", "leatherworker": "cauldron", "mason": "stonecutter[facing=south]",
       "butcher": "smoker[facing=south]", "toolsmith": "smithing_table", "weaponsmith": "grindstone[face=floor,facing=south]",
       "armorer": "blast_furnace[facing=south]"}
HOUSE_LOOT = ["chests/village/village_taiga_house", "chests/village/village_plains_house",
              "chests/village/village_snowy_house"]

PALETTES = [
    # base, wall, frame(log), beam(log stripped), roof stairs, roof block, planks, wood (door)
    dict(base="cobblestone", wall="calcite", frame="dark_oak_log", beam="stripped_dark_oak_log",
         roof="deepslate_tile_stairs", roofb="deepslate_tiles", planks="spruce_planks", wood="dark_oak"),
    dict(base="stone_bricks", wall="white_terracotta", frame="spruce_log", beam="stripped_spruce_log",
         roof="brick_stairs", roofb="bricks", planks="spruce_planks", wood="spruce"),
    dict(base="cobblestone", wall="yellow_terracotta", frame="dark_oak_log", beam="stripped_dark_oak_log",
         roof="spruce_stairs", roofb="spruce_planks", planks="oak_planks", wood="spruce"),
    dict(base="polished_andesite", wall="smooth_sandstone", frame="stripped_dark_oak_log", beam="dark_oak_log",
         roof="mangrove_stairs", roofb="mangrove_planks", planks="spruce_planks", wood="mangrove"),
    dict(base="mossy_cobblestone", wall="mud_bricks", frame="oak_log", beam="stripped_oak_log",
         roof="dark_oak_stairs", roofb="dark_oak_planks", planks="oak_planks", wood="oak"),
    dict(base="stone_bricks", wall="light_gray_terracotta", frame="spruce_log", beam="stripped_spruce_log",
         roof="deepslate_tile_stairs", roofb="deepslate_tiles", planks="dark_oak_planks", wood="spruce"),
]

_name_i = [0]


def villager(b, x, y, z, prof, vtype="taiga"):
    name = NAMES[_name_i[0] % len(NAMES)]
    _name_i[0] += 1
    b.summon_later("villager", x + 0.5, y, z + 0.5,
                   '{VillagerData:{profession:"minecraft:%s",level:1,type:"minecraft:%s"},CustomName:"%s"}'
                   % (prof or "none", vtype, name))


# --------------------------------------------------------------------------
# a house, built in a local frame with the door on its south side
# --------------------------------------------------------------------------
def house(b, xmin, zmin, w, d, facing, stories=1, pal=None, prof=None, kind=None, title=None):
    pal = pal or RNG.choice(PALETTES)
    r = {"south": 0, "west": 1, "north": 2, "east": 3}[facing]
    ox, oz = {0: (xmin, zmin), 1: (xmin + d - 1, zmin), 2: (xmin + w - 1, zmin + d - 1),
              3: (xmin, zmin + w - 1)}[r]
    with b.frame(ox, 0, oz, r):
        _house_local(b, w, d, stories, pal, prof, kind, title)


def _house_local(b, w, d, stories, pal, prof, kind, title):
    top = 5 * stories - 1              # ceiling / roof base
    # foundation and floor
    b.fill(0, -2, 0, w - 1, -1, d - 1, pal["base"])
    b.fill(1, -1, 1, w - 2, -1, d - 2, pal["planks"])
    # walls
    for s in range(stories):
        y0 = 5 * s
        b.walls(0, y0, 0, w - 1, y0 + 3, d - 1, pal["wall"])
        if s == 0:
            b.walls(0, 0, 0, w - 1, 0, d - 1, pal["base"])
        # floor/ceiling and timber band
        b.fill(0, y0 + 4, 0, w - 1, y0 + 4, d - 1, pal["planks"])
        b.fill(0, y0 + 4, 0, w - 1, y0 + 4, 0, pal["beam"] + "[axis=x]")
        b.fill(0, y0 + 4, d - 1, w - 1, y0 + 4, d - 1, pal["beam"] + "[axis=x]")
        b.fill(0, y0 + 4, 1, 0, y0 + 4, d - 2, pal["beam"] + "[axis=z]")
        b.fill(w - 1, y0 + 4, 1, w - 1, y0 + 4, d - 2, pal["beam"] + "[axis=z]")
        # windows front/back and sides, with shutters
        for x in range(2, w - 2, 3):
            if s == 0 and abs(x - w // 2) <= 1:
                continue
            for z, sh in ((0, "north"), (d - 1, "south")):
                b.fill(x, y0 + 1, z, x, y0 + 2, z, "glass_pane")
        for z in range(2, d - 2, 3):
            for x in (0, w - 1):
                b.fill(x, y0 + 1, z, x, y0 + 2, z, "glass_pane")
    # corner posts
    for (px, pz) in ((0, 0), (w - 1, 0), (0, d - 1), (w - 1, d - 1)):
        b.fill(px, 0, pz, px, top, pz, pal["frame"])
    b.fill(0, 0, 0, 0, 0, 0, pal["frame"])
    # gable roof, ridge along x
    i = 0
    while True:
        za, zb = -1 + i, d - i
        y = top + i
        if za > zb:
            break
        if za == zb:
            b.fill(-1, y, za, w, y, za, pal["roofb"])
            b.fill(-1, y + 1, za, w, y + 1, za, pal["roof"].replace("_stairs", "_slab") + "[type=bottom]")
            break
        b.fill(-1, y, za, w, y, za, pal["roof"] + "[facing=south]")
        b.fill(-1, y, zb, w, y, zb, pal["roof"] + "[facing=north]")
        if i >= 1 and zb - za > 1:
            b.fill(0, y, za + 1, 0, y, zb - 1, pal["wall"])
            b.fill(w - 1, y, za + 1, w - 1, y, zb - 1, pal["wall"])
        i += 1
    roof_top = top + i + 1
    # chimney with a smoking campfire
    b.fill(1, 0, 1, 1, roof_top, 1, "cobblestone")
    b.set(1, roof_top + 1, 1, "campfire[lit=true]")
    # door, step and porch light
    dx = w // 2
    b.air(dx, 0, d - 1, dx, 1, d - 1)
    b.door(dx, 0, d - 1, pal["wood"], "north")
    b.set(dx, -1, d, "stone_bricks")
    b.set(dx - 1, 2, d, "wall_torch[facing=south]")
    if title:
        b.set(dx + 1, 2, d, "spruce_wall_sign[facing=south]" + sign(title, "black", True))
    # interior
    b.set(dx, 3, d // 2, "lantern[hanging=true]")
    b.set(2, 0, 1, "chest[facing=south]" + loot(RNG.choice(HOUSE_LOOT)))
    b.set(3, 0, 1, "crafting_table")
    if prof in JOB:
        b.set(1, 0, d - 2, JOB[prof])
    elif kind is None:
        b.set(1, 0, d - 2, "potted_red_tulip")
    if w >= 8:
        b.set(w - 2, 0, d - 2, "furnace[facing=west]")
    if stories == 1:
        b.bed(w - 2, 0, 2, RNG.choice(["red", "green", "blue", "yellow", "white", "brown"]), "north")
    else:
        b.fill(w - 2, 0, 1, w - 2, 4, 1, "ladder[facing=south]")
        b.bed(2, 5, 2, RNG.choice(["red", "green", "blue", "yellow"]), "north")
        if w >= 8:
            b.bed(4, 5, 2, RNG.choice(["red", "green", "white", "brown"]), "north")
        b.set(w - 3, 5, d - 2, "chest[facing=north]" + loot(RNG.choice(HOUSE_LOOT)))
        b.set(dx, 8, d // 2, "lantern[hanging=true]")
        b.set(2, 5, d - 2, "bookshelf")
    if kind:
        KIND[kind](b, w, d, stories)
    villager(b, dx, 0, d // 2, prof)


# special interiors for named houses ---------------------------------------
def _tavern(b, w, d, s):
    b.fill(2, 0, 3, w - 3, 0, 3, "barrel[facing=up]")
    b.set(3, 0, 3, "barrel[facing=up]" + chest_items([("honey_bottle", 16), ("milk_bucket", 1), ("bread", 32)]))
    b.set(2, 1, 3, "brewing_stand")
    b.set(w - 3, 1, 3, "lantern")
    for x in range(2, w - 2, 3):
        b.set(x, 0, d - 3, "spruce_fence")
        b.set(x, 1, d - 3, "spruce_pressure_plate")
        b.set(x - 1, 0, d - 3, "spruce_stairs[facing=east]") if x - 1 >= 1 else None
    b.set(w - 2, 0, 3, "cauldron")


def _smithy(b, w, d, s):
    b.set(2, 0, 2, "blast_furnace[facing=south]")
    b.set(4, 0, 2, "anvil[facing=east]")
    b.set(w - 3, 0, 2, "smithing_table")
    b.set(w - 4, 0, 2, "grindstone[face=floor,facing=south]")
    b.set(2, 0, 3, "water_cauldron[level=3]")
    b.set(w - 3, 0, d - 3, "chest[facing=west]" + loot("chests/village/village_weaponsmith"))


def _bakery(b, w, d, s):
    b.set(2, 0, 2, "smoker[facing=south]")
    b.set(4, 0, 2, "furnace[facing=south]")
    b.set(5, 0, 2, "barrel[facing=up]" + chest_items([("bread", 64), ("cake", 1), ("pumpkin_pie", 16),
                                                        ("cookie", 64), ("wheat", 64)]))
    b.set(w - 3, 0, 3, "hay_block")
    b.set(w - 3, 1, 3, "cake")


def _clinic(b, w, d, s):
    for x in range(2, w - 2, 2):
        b.bed(x, 0, d - 3, "white", "north")
    b.set(2, 0, 2, "brewing_stand")
    b.set(4, 0, 2, "water_cauldron[level=3]")
    b.set(5, 0, 2, "chest[facing=south]" + chest_items(
        [("golden_apple", 4), ("glistering_melon_slice", 8), ("honey_bottle", 16), ("milk_bucket", 1),
         ("glass_bottle", 16), ("nether_wart", 16)]))


def _library(b, w, d, s):
    for x in range(2, w - 2):
        b.fill(x, 0, 1, x, 2, 1, "bookshelf")
    b.set(w // 2, 0, d // 2 - 1, "lectern[facing=south,has_book=true]" + book(
        "History of Latveria", "Doomstadt School", [
            "Latveria is a small nation in the Carpathians, bordering Symkaria and Transia.",
            "For centuries it was ruled by the cruel Barons of the Haasen family, until Victor von Doom returned and overthrew them.",
            "Under Doom, no Latverian goes hungry. The Doombots keep the peace. The castle watches over us.",
        ]))
    b.set(2, 0, d - 3, "chest[facing=north]" + loot("chests/stronghold_library"))


def _tannery(b, w, d, s):
    for x in range(3, w - 2, 2):
        b.set(x, 0, 3, "water_cauldron[level=3]")
    b.set(2, 0, 3, "chest[facing=east]" + loot("chests/village/village_tannery"))


def _mason(b, w, d, s):
    b.set(3, 0, 3, "stonecutter[facing=south]")
    b.fill(w - 3, 0, 2, w - 3, 1, 3, "stone_bricks")
    b.set(4, 0, 3, "chest[facing=south]" + loot("chests/village/village_mason"))


def _fisher(b, w, d, s):
    b.set(2, 0, 3, "barrel[facing=up]" + loot("chests/village/village_fisher"))
    b.set(4, 0, 3, "barrel[facing=up]" + chest_items([("fishing_rod", 2), ("cod", 16), ("salmon", 16)]))


KIND = {"tavern": _tavern, "smithy": _smithy, "bakery": _bakery, "clinic": _clinic, "library": _library,
        "tannery": _tannery, "mason": _mason, "fisher": _fisher}


# --------------------------------------------------------------------------
# streets and plaza
# --------------------------------------------------------------------------
LANES_Z = (-40, 44, 76)
LANES_X = (-100, -48, 48, 100)
TX, TZS, TZN = TOWN_X - 2, TOWN_ZS - 2, TOWN_ZN   # inner faces of the town wall


def build_streets(b):
    b.section("streets", "Paving the streets of Doomstadt")
    # Doom Boulevard and Werner Avenue
    b.fill(-3, -1, TZN, 3, -1, TZS, "stone_bricks")
    b.fill(-TX, -1, -3, TX, -1, 3, "stone_bricks")
    for e in (-3, 3):
        b.fill(e, -1, TZN, e, -1, TZS, "polished_andesite")
        b.fill(-TX, -1, e, TX, -1, e, "polished_andesite")
    # lanes
    for zc in LANES_Z:
        b.fill(-TX, -1, zc - 2, TX, -1, zc + 2, "cobblestone")
    for xc in LANES_X:
        b.fill(xc - 2, -1, TZN + 4, xc + 2, -1, TZS, "cobblestone")
    # wear and patches
    for _ in range(500):
        x, z = RNG.randint(-TX, TX), RNG.randint(TZN, TZS)
        blk = RNG.choice(["cracked_stone_bricks", "mossy_stone_bricks", "andesite"])
        b.fill(x, -1, z, x + 1, -1, z, blk, "replace stone_bricks")
        b.fill(x, -1, z, x, -1, z + 1, RNG.choice(["mossy_cobblestone", "gravel", "andesite"]), "replace cobblestone")
    # street lamps
    for z in range(TZN + 6, TZS, 12):
        if abs(z) < PLAZA_R + 3:
            continue
        lamp_post(b, -5, 0, z)
        lamp_post(b, 5, 0, z)
    for x in range(-TX + 6, TX, 12):
        if abs(x) < PLAZA_R + 3:
            continue
        lamp_post(b, x, 0, -5)
        lamp_post(b, x, 0, 5)
    for zc in LANES_Z:
        for i, x in enumerate(range(-TX + 10, TX, 16)):
            lamp_post(b, x, 0, zc - 2 if i % 2 else zc + 2)
    for xc in LANES_X:
        for i, z in enumerate(range(TZN + 12, TZS, 16)):
            lamp_post(b, xc + 2 if i % 2 else xc - 2, 0, z)


def build_plaza(b):
    b.section("plaza", "The Plaza of Doom")
    for dx, z1, z2 in disk_runs(PLAZA_R):
        b.fill(dx, -1, z1, dx, -1, z2, "polished_andesite")
    for rr in (PLAZA_R, 17, 10):
        b.ring(0, -1, 0, rr, 1.0, "deepslate_tiles" if rr != 17 else "polished_deepslate")
    for ang in range(0, 360, 30):
        a = math.radians(ang)
        for rr in range(11, PLAZA_R):
            b.set(round(math.cos(a) * rr), -1, round(math.sin(a) * rr), "stone_bricks")
    # fountain moat around the plinth
    for dx, z1, z2 in disk_runs(15):
        b.fill(dx, -2, z1, dx, -2, z2, "polished_deepslate")
    for dx, z1, z2 in disk_runs(14):
        b.fill(dx, -1, z1, dx, -1, z2, "water")
    b.ring(0, 0, 0, 15, 1.0, "polished_deepslate_slab[type=bottom]")
    for dx, dz in ring_cells(15, 1.0)[::6]:
        b.set(dx, -2, dz, "sea_lantern")
    # plinth
    b.fill(-12, -1, -9, 12, 0, 9, "polished_deepslate")
    b.fill(-11, 1, -8, 11, 3, 8, "polished_deepslate")
    b.fill(-11, 4, -8, 11, 4, 8, "deepslate_tiles")
    b.fill(-12, 1, -9, 12, 1, 9, "polished_deepslate_slab[type=bottom]")
    b.fill(-11, 1, -8, 11, 3, 8, "polished_deepslate")
    for x in (-11, 11):
        for z in (-8, 8):
            b.fill(x, 4, z, x, 6, z, "chiseled_deepslate")
            b.set(x, 7, z, "soul_lantern")
    # inscription
    b.set(-2, 2, 9, "dark_oak_wall_sign[facing=south]" + sign(["VICTOR", "VON DOOM"], "dark_green", True))
    b.set(0, 2, 9, "dark_oak_wall_sign[facing=south]" + sign(["Sovereign", "of", "Latveria"], "dark_green", True))
    b.set(2, 2, 9, "dark_oak_wall_sign[facing=south]" + sign(["Doom", "provides."], "dark_green", True))
    for x in (-5, 5):
        b.set(x, 3, 9, "green_wall_banner[facing=south]" + doom_banner())
    # the colossus
    build_statue(b, 0, 5, 0, 1.0, rot=0)
    # village bell (the meeting point of Doomstadt)
    b.set(0, 0, 19, "stone_bricks")
    b.set(0, 1, 19, "bell[attachment=floor,facing=east]")
    # lamps and benches ring
    for ang in range(15, 360, 30):
        a = math.radians(ang)
        x, z = round(math.cos(a) * 21), round(math.sin(a) * 21)
        lamp_post(b, x, 0, z)
    # market stalls
    stalls = [(-17, -15, "red"), (13, -15, "yellow"), (-17, 12, "blue"), (13, 12, "lime")]
    goods = [("farmer", [("wheat", 32), ("carrot", 32), ("potato", 32)]),
             ("fisherman", [("cod", 16), ("salmon", 16)]),
             ("butcher", [("cooked_beef", 16), ("cooked_porkchop", 16)]),
             ("shepherd", [("white_wool", 32), ("green_wool", 16)])]
    for (x, z, col), (prof, items) in zip(stalls, goods):
        b.fill(x, 0, z, x + 4, 0, z + 2, "air")
        for (px, pz) in ((x, z), (x + 4, z), (x, z + 2), (x + 4, z + 2)):
            b.fill(px, 0, pz, px, 2, pz, "spruce_fence")
        b.fill(x, 3, z, x + 4, 3, z + 2, "%s_wool" % col)
        b.fill(x + 1, 3, z + 1, x + 3, 3, z + 1, "white_wool")
        b.set(x + 1, 0, z + 1, "barrel[facing=up]" + chest_items(items))
        b.set(x + 2, 0, z + 1, JOB[prof])
        b.set(x + 3, 0, z + 1, "barrel[facing=up]" + loot("chests/village/village_plains_house"))
        b.set(x + 2, 2, z + 1, "lantern[hanging=true]")
        villager(b, x + 2, 0, z, prof)
    # benches
    for (x, z, f) in ((-8, 20, "north"), (8, 20, "north"), (-8, -20, "south"), (8, -20, "south"),
                      (20, 8, "west"), (20, -8, "west"), (-20, 8, "east"), (-20, -8, "east")):
        b.set(x, 0, z, "spruce_stairs[facing=%s]" % f)
    # Doombot sentinels at the plaza
    for (x, z, yaw) in ((0, -22, 180), (22, 0, 90), (-22, 0, 270), (0, 22, 0)):
        pass


# --------------------------------------------------------------------------
# town walls
# --------------------------------------------------------------------------
def round_turret(b, cx, cz, r=4, top=15):
    for dx, z1, z2 in disk_runs(r):
        b.fill(cx + dx, -1, cz + z1, cx + dx, top, cz + z2, "stone_bricks")
    for dx, z1, z2 in disk_runs(r - 2):
        b.fill(cx + dx, 0, cz + z1, cx + dx, top - 1, cz + z2, "air")
    for dx, z1, z2 in disk_runs(r - 2):
        b.fill(cx + dx, 9, cz + z1, cx + dx, 9, cz + z2, "spruce_planks")
    b.cone(cx, top + 1, cz, r + 0.6, r * 2 + 2, "oxidized_cut_copper", "lightning_rod")
    b.set(cx, 0, cz, "lantern")
    b.set(cx, 10, cz, "lantern")


def build_town_walls(b):
    b.section("town_walls", "The walls of Doomstadt")
    W = TOWN_X
    S = TOWN_ZS
    N = TOWN_ZN - 2
    segs = [(-W, -W + 1, N, S), (W - 1, W, N, S), (-W, W, S - 1, S),
            (-W, -64, N, N + 1), (64, W, N, N + 1)]
    for (x1, x2, z1, z2) in segs:
        b.fill(x1, -3, z1, x2, 8, z2, "stone_bricks")
        b.fill(x1, 0, z1, x2, 0, z2, "mossy_stone_bricks")
    # merlons on the outer edge
    for z in range(N, S + 1, 2):
        b.set(-W, 9, z, "stone_bricks")
        b.set(W, 9, z, "stone_bricks")
    for x in range(-W, W + 1, 2):
        b.set(x, 9, S, "stone_bricks")
    for x in list(range(-W, -63, 2)) + list(range(64, W + 1, 2)):
        b.set(x, 9, N, "stone_bricks")
    # gates
    b.air(-W, 0, -3, -W + 1, 5, 3)
    b.air(W - 1, 0, -3, W, 5, 3)
    b.air(-3, 0, S - 1, 3, 5, S)
    for (x1, x2, z1, z2) in ((-W, -W + 1, -3, 3), (W - 1, W, -3, 3), (-3, 3, S - 1, S)):
        b.fill(x1, -1, z1, x2, -1, z2, "stone_bricks")
    for (gx, gz) in ((-W, 0), (W, 0)):
        b.fill(gx, 5, -3, gx, 5, 3, "iron_bars")
        round_turret(b, gx, -7)
        round_turret(b, gx, 7)
    b.fill(-3, 5, S, 3, 5, S, "iron_bars")
    round_turret(b, -7, S)
    round_turret(b, 7, S)
    # corner and interval towers
    for (tx, tz) in ((-W, S), (W, S), (-W, N), (W, N), (-W, -40), (W, -40), (-W, 50), (W, 50),
                     (-60, S), (60, S), (-110, S), (110, S), (-104, N), (104, N)):
        round_turret(b, tx, tz, 4, 16)
    # ladders up to the wall walk
    for z in (-55, -20, 25, 70, 95):
        b.fill(-W + 2, 0, z, -W + 2, 8, z, "ladder[facing=east]")
        b.fill(W - 2, 0, z, W - 2, 8, z, "ladder[facing=west]")
    for x in (-90, -30, 30, 90):
        b.fill(x, 0, S - 2, x, 8, S - 2, "ladder[facing=north]")
    # gate signs and banners
    b.set(0, 6, S + 1, "dark_oak_wall_sign[facing=south]" + sign(["DOOMSTADT", "Capital of", "Latveria"], "dark_green", True))
    for x in (-2, 2):
        b.set(x, 8, S + 1, "green_wall_banner[facing=south]" + doom_banner("latveria"))
    b.set(-W - 1, 6, 0, "dark_oak_wall_sign[facing=west]" + sign(["DOOMSTADT", "West Gate"], "dark_green", True))
    b.set(W + 1, 6, 0, "dark_oak_wall_sign[facing=east]" + sign(["DOOMSTADT", "East Gate"], "dark_green", True))
    # the road leading out of the south gate
    b.fill(-3, -1, S + 1, 3, -1, Z_MAX, "stone_bricks")


# --------------------------------------------------------------------------
# landmark buildings
# --------------------------------------------------------------------------
def build_cathedral(b):
    b.section("cathedral", "Cathedral of Doomstadt")
    # nave along x (entrance west), transept along z, dome over the crossing, west bell tower
    X1, X2 = 60, 94
    Zc = -20
    NZ1, NZ2 = Zc - 7, Zc + 7
    H = 16
    TX1, TX2 = 78, 86
    b.fill(X1 - 1, -1, NZ1 - 1, X2 + 1, -1, NZ2 + 1, "stone_bricks")
    # nave shell
    b.fill(X1, -1, NZ1, X2, H, NZ2, "stone_bricks")
    b.air(X1 + 1, 0, NZ1 + 1, X2 - 1, H - 1, NZ2 - 1)
    # transept shell
    b.fill(TX1, -1, Zc - 15, TX2, H, Zc + 15, "stone_bricks")
    b.air(TX1 + 1, 0, Zc - 14, TX2 - 1, H - 1, Zc + 14)
    b.air(TX1 + 1, 0, NZ1 + 1, TX2 - 1, H - 1, NZ2 - 1)
    b.air(X1 + 1, 0, NZ1 + 1, X2 - 1, H - 1, NZ2 - 1)
    b.fill(X1 + 1, -1, NZ1 + 1, X2 - 1, -1, NZ2 - 1, "polished_andesite")
    b.fill(TX1 + 1, -1, Zc - 14, TX2 - 1, -1, Zc + 14, "polished_andesite")
    b.fill(X1 + 1, 0, Zc - 1, X2 - 6, 0, Zc + 1, "red_carpet")
    # buttresses
    for x in range(X1, X2 + 1, 6):
        for z in (NZ1 - 1, NZ2 + 1):
            b.fill(x, -1, z, x, H - 2, z, "polished_andesite")
    # stained glass lancets
    cols = ["purple", "blue", "red", "yellow", "green", "cyan"]
    for i, x in enumerate(range(X1 + 3, X2 - 1, 6)):
        if TX1 <= x <= TX2:
            continue
        for z in (NZ1, NZ2):
            b.fill(x, 3, z, x + 1, 11, z, "%s_stained_glass_pane" % cols[i % 6])
            b.fill(x, 12, z, x + 1, 12, z, "stone_brick_stairs[facing=%s,half=top]" % ("north" if z == NZ1 else "south"))
    for z in (Zc - 15, Zc + 15):
        b.fill(TX1 + 3, 3, z, TX2 - 3, 12, z, "light_blue_stained_glass_pane")
    # rose window over the east apse
    for dz in range(-3, 4):
        for dy in range(-3, 4):
            if dz * dz + dy * dy <= 10:
                b.set(X2, 10 + dy, Zc + dz, "red_stained_glass" if dz * dz + dy * dy <= 2 else "yellow_stained_glass")
    # gabled roofs of deepslate tiles
    for i in range(0, 9):
        y = H + i
        za, zb = NZ1 - 1 + i, NZ2 + 1 - i
        if za >= zb:
            b.fill(X1 - 1, y, za, X2 + 1, y, za, "deepslate_tiles")
            break
        b.fill(X1 - 1, y, za, X2 + 1, y, za, "deepslate_tile_stairs[facing=south]")
        b.fill(X1 - 1, y, zb, X2 + 1, y, zb, "deepslate_tile_stairs[facing=north]")
        b.fill(X1, y, za + 1, X1, y, zb - 1, "stone_bricks")
        b.fill(X2, y, za + 1, X2, y, zb - 1, "stone_bricks")
    for i in range(0, 6):
        y = H + i
        xa, xb = TX1 - 1 + i, TX2 + 1 - i
        if xa >= xb:
            b.fill(xa, y, Zc - 16, xa, y, Zc + 16, "deepslate_tiles")
            break
        b.fill(xa, y, Zc - 16, xa, y, Zc + 16, "deepslate_tile_stairs[facing=east]")
        b.fill(xb, y, Zc - 16, xb, y, Zc + 16, "deepslate_tile_stairs[facing=west]")
        b.fill(xa + 1, y, Zc - 15, xb - 1, y, Zc - 15, "stone_bricks")
        b.fill(xa + 1, y, Zc + 15, xb - 1, y, Zc + 15, "stone_bricks")
    # onion dome over the crossing
    dcx = (TX1 + TX2) // 2
    b.fill(dcx - 4, H + 5, Zc - 4, dcx + 4, H + 9, Zc + 4, "stone_bricks")
    for dy in range(0, 14):
        rr = 5.5 * math.sin(math.pi * min(1.0, (dy + 1) / 11.0)) if dy < 11 else 1.2 - 0.4 * (dy - 11)
        if rr < 0.6:
            b.set(dcx, H + 10 + dy, Zc, "oxidized_copper")
            continue
        b.ring(dcx, H + 10 + dy, Zc, rr, 1.4, "oxidized_copper")
    b.fill(dcx, H + 24, Zc, dcx, H + 25, Zc, "gold_block")
    b.set(dcx, H + 26, Zc, "lightning_rod")
    # west bell tower (entrance underneath)
    bx1, bx2 = X1 - 8, X1
    b.fill(bx1, -1, Zc - 4, bx2, 34, Zc + 4, "stone_bricks")
    b.air(bx1 + 1, 0, Zc - 3, bx2 - 1, 33, Zc + 3)
    for y in (8, 16, 24):
        b.fill(bx1 + 1, y, Zc - 3, bx2 - 1, y, Zc + 3, "spruce_planks")
    b.fill(bx1 + 1, 0, Zc + 3, bx1 + 1, 24, Zc + 3, "ladder[facing=east]")
    for y in (8, 16, 24):
        b.set(bx1 + 1, y, Zc + 3, "ladder[facing=east]")
    # belfry openings
    for z in range(Zc - 2, Zc + 3, 2):
        b.air(bx1, 26, z, bx1, 30, z)
        b.air(bx2, 26, z, bx2, 30, z)
    for x in range(bx1 + 2, bx2 - 1, 2):
        b.air(x, 26, Zc - 4, x, 30, Zc - 4)
        b.air(x, 26, Zc + 4, x, 30, Zc + 4)
    b.set((bx1 + bx2) // 2, 33, Zc, "bell[attachment=ceiling,facing=east]")
    # tower spire
    for k in range(12):
        s_ = 5 - k // 2
        y = 35 + k
        if s_ <= 0:
            b.set((bx1 + bx2) // 2, y, Zc, "oxidized_cut_copper")
            b.set((bx1 + bx2) // 2, y + 1, Zc, "lightning_rod")
            break
        cxm = (bx1 + bx2) // 2
        b.fill(cxm - s_, y, Zc - s_, cxm + s_, y, Zc + s_, "oxidized_cut_copper")
        b.air(cxm - s_ + 1, y, Zc - s_ + 1, cxm + s_ - 1, y, Zc + s_ - 1)
    # entrance
    b.air(bx1, 0, Zc - 1, bx2, 4, Zc + 1)
    b.air(X1, 0, Zc - 1, X1, 4, Zc + 1)
    b.door(bx1, 0, Zc - 1, "dark_oak", "east", "left")
    b.door(bx1, 0, Zc + 1, "dark_oak", "east", "right")
    b.fill(bx1, 2, Zc, bx1, 4, Zc, "stone_bricks")
    b.fill(bx1, 0, Zc, bx1, 1, Zc, "air")
    b.set(bx1 - 1, 5, Zc, "dark_oak_wall_sign[facing=west]" + sign(["CATHEDRAL OF", "DOOMSTADT"], "black", True))
    # pews facing the altar in the east
    for x in range(X1 + 3, TX1 - 1, 2):
        b.fill(x, 0, NZ1 + 1, x, 0, Zc - 2, "spruce_stairs[facing=west]")
        b.fill(x, 0, Zc + 2, x, 0, NZ2 - 1, "spruce_stairs[facing=west]")
    # altar and sanctuary
    b.fill(X2 - 6, 0, NZ1 + 1, X2 - 1, 0, NZ2 - 1, "polished_deepslate")
    b.fill(X2 - 3, 1, Zc - 2, X2 - 3, 1, Zc + 2, "chiseled_quartz_block")
    b.set(X2 - 3, 2, Zc, "gold_block")
    b.set(X2 - 3, 2, Zc - 2, "candle[candles=4,lit=true]")
    b.set(X2 - 3, 2, Zc + 2, "candle[candles=4,lit=true]")
    b.set(X2 - 5, 1, Zc - 3, "brewing_stand")
    b.set(X2 - 5, 1, Zc + 3, "lectern[facing=west,has_book=true]" + book(
        "Book of Hours", "The Cathedral", ["In memory of Werner von Doom, healer, who never turned away the sick."]))
    b.set(X2 - 2, 1, Zc - 5, "chest[facing=west]" + loot("chests/village/village_temple"))
    for x in range(X1 + 4, X2, 8):
        b.fill(x, 12, Zc, x, H - 1, Zc, "iron_chain")
        b.set(x, 11, Zc, "lantern[hanging=true]")
    for z in (Zc - 10, Zc + 10):
        b.set(dcx, H - 1, z, "iron_chain")
        b.set(dcx, H - 2, z, "lantern[hanging=true]")
    villager(b, X2 - 6, 1, Zc, "cleric")
    villager(b, X2 - 8, 1, Zc + 3, "cleric")


def build_town_hall(b):
    b.section("town_hall", "The Rathaus of Doomstadt")
    x1, x2, z1, z2 = -44, -28, -37, -19
    b.fill(x1, -1, z1, x2, -1, z2, "polished_andesite")
    b.fill(x1, 0, z1, x2, 16, z2, "stone_bricks")
    b.air(x1 + 1, 0, z1 + 1, x2 - 1, 15, z2 - 1)
    b.fill(x1 + 1, 7, z1 + 1, x2 - 1, 7, z2 - 1, "dark_oak_planks")
    for y in (0, 8):
        for z in range(z1 + 2, z2 - 1, 3):
            for x in (x1, x2):
                b.fill(x, y + 2, z, x, y + 4, z, "glass_pane")
        for x in range(x1 + 2, x2 - 1, 3):
            for z in (z1, z2):
                b.fill(x, y + 2, z, x, y + 4, z, "glass_pane")
    # hip roof
    for k in range(0, 10):
        y = 17 + k
        a1, a2, c1, c2 = x1 - 1 + k, x2 + 1 - k, z1 - 1 + k, z2 + 1 - k
        if a1 >= a2 or c1 >= c2:
            break
        b.fill(a1, y, c1, a2, y, c1, "deepslate_tile_stairs[facing=south]")
        b.fill(a1, y, c2, a2, y, c2, "deepslate_tile_stairs[facing=north]")
        b.fill(a1, y, c1 + 1, a1, y, c2 - 1, "deepslate_tile_stairs[facing=east]")
        b.fill(a2, y, c1 + 1, a2, y, c2 - 1, "deepslate_tile_stairs[facing=west]")
        if a2 - a1 > 1 and c2 - c1 > 1:
            b.fill(a1 + 1, y, c1 + 1, a2 - 1, y, c2 - 1, "deepslate_tiles")
    # clock tower on the east front
    tx, tz = x2, (z1 + z2) // 2
    b.fill(tx - 2, -1, tz - 2, tx + 2, 34, tz + 2, "stone_bricks")
    b.air(tx - 1, 0, tz - 1, tx + 1, 33, tz + 1)
    b.fill(tx - 1, 0, tz - 1, tx - 1, 32, tz - 1, "ladder[facing=south]")
    b.fill(tx, 32, tz - 1, tx + 1, 32, tz + 1, "spruce_planks")
    b.set(tx, 33, tz, "lantern")
    for (fx, fz, f) in ((tx + 3, tz, 5), (tx, tz - 3, 2), (tx, tz + 3, 3), (tx - 3, tz, 4)):
        if fx == tx - 3:
            continue
        b.summon_later("glow_item_frame", fx + 0.5, 28.5, fz + 0.5,
                       '{Facing:%db,Fixed:1b,Invulnerable:1b,Item:{id:"minecraft:clock",count:1}}' % f)
    for (fx, fz) in ((tx + 2, tz), (tx, tz - 2), (tx, tz + 2)):
        b.set(fx, 28, fz, "chiseled_stone_bricks")
    for k in range(6):
        s_ = 3 - k // 2
        if s_ <= 0:
            b.set(tx, 35 + k, tz, "oxidized_cut_copper")
            b.set(tx, 36 + k, tz, "lightning_rod")
            break
        b.fill(tx - s_, 35 + k, tz - s_, tx + s_, 35 + k, tz + s_, "oxidized_cut_copper")
    b.air(tx + 2, 0, tz - 1, tx + 2, 3, tz + 1)
    b.door(tx + 2, 0, tz - 1, "dark_oak", "west", "left")
    b.door(tx + 2, 0, tz + 1, "dark_oak", "west", "right")
    b.air(tx - 2, 0, tz - 1, tx - 2, 2, tz + 1)
    b.set(tx + 3, 5, tz, "dark_oak_wall_sign[facing=east]" + sign(["RATHAUS", "Council of", "Doomstadt"], "black", True))
    b.set(tx + 3, 7, tz - 1, "green_wall_banner[facing=east]" + doom_banner("latveria"))
    b.set(tx + 3, 7, tz + 1, "green_wall_banner[facing=east]" + doom_banner("latveria"))
    # council chamber
    b.fill(x1 + 5, 0, tz - 1, x1 + 12, 0, tz + 1, "dark_oak_planks")
    for x in range(x1 + 5, x1 + 13, 2):
        b.set(x, 0, tz - 2, "dark_oak_stairs[facing=north]")
        b.set(x, 0, tz + 2, "dark_oak_stairs[facing=south]")
    b.set(x1 + 4, 0, tz, "dark_oak_stairs[facing=east]")
    b.set(x1 + 1, 2, tz, "green_wall_banner[facing=east]" + doom_banner())
    b.set(x1 + 2, 0, z1 + 2, "lectern[facing=east,has_book=true]" + book(
        "Laws of Latveria", "The Council", ["There is no crime in Latveria.", "Doom's word is law."]))
    b.set(x1 + 2, 0, z2 - 2, "cartography_table")
    b.set(x1 + 3, 0, z2 - 2, "chest[facing=north]" + chest_items([("map", 8), ("paper", 32), ("emerald", 16)]))
    for x in (x1 + 5, x1 + 11):
        b.set(x, 6, tz, "lantern[hanging=true]")
        b.set(x, 15, tz, "lantern[hanging=true]")
    b.fill(x1 + 1, 0, z1 + 1, x1 + 1, 7, z1 + 1, "ladder[facing=south]")
    # upper floor: archives
    for x in range(x1 + 3, x2 - 4, 3):
        b.fill(x, 8, z1 + 2, x, 10, z1 + 6, "bookshelf")
    b.bed(x2 - 4, 8, z2 - 3, "green", "north")
    b.bed(x2 - 6, 8, z2 - 3, "green", "north")
    villager(b, x1 + 3, 0, z1 + 3, "librarian")
    villager(b, x1 + 3, 0, z2 - 3, "cartographer")


def farm(b, x1, z1, x2, z2, crop):
    b.fill(x1 - 1, -1, z1 - 1, x2 + 1, -1, z2 + 1, "grass_block")
    b.fill(x1, -1, z1, x2, -1, z2, "farmland[moisture=7]")
    b.fill(x1, 0, z1, x2, 0, z2, crop)
    for x in range(x1 + 4, x2, 9):
        b.fill(x, -1, z1, x, -1, z2, "water")
        b.air(x, 0, z1, x, 0, z2)
    b.walls(x1 - 1, 0, z1 - 1, x2 + 1, 0, z2 + 1, "spruce_fence")
    b.set(x1 - 1, 0, (z1 + z2) // 2, "spruce_fence_gate[facing=east]")
    b.set(x2 + 1, 0, (z1 + z2) // 2, "spruce_fence_gate[facing=west]")
    for (px, pz) in ((x1 - 1, z1 - 1), (x2 + 1, z1 - 1), (x1 - 1, z2 + 1), (x2 + 1, z2 + 1)):
        b.set(px, 1, pz, "lantern")
    b.set(x1 - 2, 0, z1 + 2, "composter[level=0]")
    # scarecrow
    mx, mz = (x1 + x2) // 2 + 2, (z1 + z2) // 2
    b.set(mx, 0, mz, "spruce_fence")
    b.set(mx, 1, mz, "hay_block")
    b.set(mx, 2, mz, "carved_pumpkin[facing=south]")


def pen(b, x1, z1, x2, z2, animals):
    b.walls(x1, 0, z1, x2, 0, z2, "spruce_fence")
    b.set(x1, 0, (z1 + z2) // 2, "spruce_fence_gate[facing=east]")
    b.set(x1 + 1, 0, z1 + 1, "water_cauldron[level=3]")
    b.set(x1 + 2, 0, z1 + 1, "hay_block")
    for (px, pz) in ((x1, z1), (x2, z1), (x1, z2), (x2, z2)):
        b.set(px, 1, pz, "lantern")
    for i, a in enumerate(animals):
        b.summon_later(a, x1 + 2 + (i * 3) % max(1, (x2 - x1 - 3)), 0, z1 + 2 + (i * 2) % max(1, (z2 - z1 - 3)), "")


def vardo(b, x, z, col, rot=0):
    """A Romani caravan wagon, as Werner von Doom's people travelled."""
    with b.frame(x, 0, z, rot):
        b.fill(0, 0, 0, 4, 0, 6, "spruce_planks")
        b.walls(0, 1, 0, 4, 3, 6, "%s_terracotta" % col)
        b.fill(0, 4, 0, 0, 4, 6, "dark_oak_stairs[facing=east]")
        b.fill(4, 4, 0, 4, 4, 6, "dark_oak_stairs[facing=west]")
        b.fill(1, 4, 0, 3, 4, 6, "%s_wool" % ("red" if col != "red" else "yellow"))
        b.fill(1, 5, 0, 1, 5, 6, "dark_oak_stairs[facing=east]")
        b.fill(3, 5, 0, 3, 5, 6, "dark_oak_stairs[facing=west]")
        b.fill(2, 5, 0, 2, 5, 6, "dark_oak_slab[type=bottom]")
        for zz in (1, 5):
            b.set(-1, 0, zz, "spruce_trapdoor[facing=west,open=true,half=bottom]")
            b.set(5, 0, zz, "spruce_trapdoor[facing=east,open=true,half=bottom]")
        b.set(0, 2, 3, "glass_pane")
        b.set(4, 2, 3, "glass_pane")
        b.air(2, 1, 6, 2, 2, 6)
        b.door(2, 1, 6, "spruce", "north")
        b.set(2, 0, 7, "spruce_stairs[facing=north]")
        b.bed(1, 1, 2, "red", "north")
        b.set(3, 1, 1, "chest[facing=south]" + loot("chests/village/village_plains_house"))
        b.set(3, 1, 3, "barrel[facing=up]" + chest_items([("bread", 16), ("apple", 16), ("sweet_berries", 16)]))
        b.set(2, 3, 3, "lantern[hanging=true]")
        b.set(1, 1, -1, "spruce_fence")
        b.set(3, 1, -1, "spruce_fence")


def build_romani_camp(b):
    b.section("romani_camp", "Werner's Camp: the Romani quarter")
    x1, x2, z1, z2 = -140, -104, 48, 72
    b.fill(x1, -1, z1, x2, -1, z2, "grass_block")
    b.fill(x1 + 10, -1, z1 + 8, x1 + 24, -1, z1 + 16, "coarse_dirt")
    cx, cz = x1 + 17, z1 + 12
    vardo(b, x1 + 2, z1 + 2, "red")
    vardo(b, x1 + 28, z1 + 2, "yellow")
    vardo(b, x1 + 2, z1 + 15, "blue")
    vardo(b, x1 + 28, z1 + 15, "green")
    b.set(cx, -1, cz, "cobblestone")
    b.set(cx, 0, cz, "campfire[lit=true]")
    for (dx, dz, ax) in ((-3, 0, "z"), (3, 0, "z"), (0, -3, "x"), (0, 3, "x")):
        b.set(cx + dx, 0, cz + dz, "stripped_spruce_log[axis=%s]" % ax)
    # memorial stone for Werner von Doom
    b.fill(cx - 1, 0, z2 - 3, cx + 1, 0, z2 - 3, "mossy_cobblestone")
    b.set(cx, 1, z2 - 3, "mossy_stone_bricks")
    b.set(cx, 2, z2 - 3, "mossy_stone_brick_wall")
    b.set(cx, 1, z2 - 2, "spruce_wall_sign[facing=south]" + sign(["Werner", "von Doom", "Healer of", "the Romani"], "black", True))
    for dx in (-2, 2):
        b.set(cx + dx, 0, z2 - 3, "poppy")
    b.set(cx - 1, 0, z2 - 2, "lily_of_the_valley")
    b.set(cx + 1, 0, z2 - 2, "blue_orchid")
    b.set(cx + 4, 0, cz + 3, "loom[facing=north]")
    b.set(cx - 4, 0, cz + 3, "cauldron")
    villager(b, cx + 2, 0, cz + 2, "leatherworker")
    villager(b, cx - 2, 0, cz - 2, "shepherd")
    villager(b, cx + 3, 0, cz - 3, None)
    for i in range(3):
        b.summon_later("horse", cx - 6 + i * 6, 0, z2 - 6, '{Tame:1b,Variant:%d}' % (i * 2 + 1))
    b.set(cx, 3, cz, "air")


def build_orchard(b, x1, z1, x2, z2):
    b.fill(x1, -1, z1, x2, -1, z2, "grass_block")
    kinds = ["fancy_oak", "birch", "cherry", "oak"]
    k = 0
    for x in range(x1 + 3, x2 - 2, 8):
        for z in range(z1 + 3, z2 - 2, 8):
            b.feature(kinds[k % len(kinds)], x, 0, z)
            k += 1
    for _ in range(30):
        b.set(RNG.randint(x1, x2), 0, RNG.randint(z1, z2), RNG.choice(["poppy", "dandelion", "short_grass", "cornflower"]))


def build_apiary(b, x1, z1, x2, z2):
    b.fill(x1, -1, z1, x2, -1, z2, "grass_block")
    flowers = ["sunflower", "rose_bush", "lilac", "peony"]
    for x in range(x1 + 1, x2, 2):
        for z in range(z1 + 1, z2, 3):
            f = flowers[(x + z) % 4]
            b.tall_plant(x, 0, z, f)
    for x in range(x1 + 4, x2 - 2, 7):
        b.set(x, 0, z1 + 6, "spruce_fence")
        b.set(x, 1, z1 + 6, "beehive[facing=south,honey_level=3]")
        b.summon_later("bee", x, 2, z1 + 8, "")
    b.set(x1 + 1, 0, z1, "chest[facing=south]" + chest_items([("glass_bottle", 16), ("shears", 1), ("campfire", 2)]))


def build_pond(b, x1, z1, x2, z2):
    cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
    for dx, zz1, zz2 in disk_runs(8):
        b.fill(cx + dx, -4, cz + zz1, cx + dx, -2, cz + zz2, "water")
        b.fill(cx + dx, -5, cz + zz1, cx + dx, -5, cz + zz2, "gravel")
        b.fill(cx + dx, -1, cz + zz1, cx + dx, -1, cz + zz2, "water")
    b.ring(cx, -1, cz, 9, 1.0, "sand")
    for _ in range(12):
        dx, dz = RNG.randint(-6, 6), RNG.randint(-6, 6)
        if dx * dx + dz * dz < 40 and not (abs(dx) <= 1 and dz >= 2):
            b.set(cx + dx, 0, cz + dz, "lily_pad")
    b.fill(cx - 1, -1, cz + 3, cx + 1, -1, cz + 9, "spruce_planks")
    for (dx, dz) in ((-1, 3), (1, 3)):
        b.fill(cx + dx, -4, cz + dz, cx + dx, -2, cz + dz, "spruce_log")
        b.set(cx + dx, 0, cz + dz, "spruce_fence")
        b.set(cx + dx, 1, cz + dz, "lantern")
    b.summon_later("cod", cx - 3, -3, cz - 2, "")
    b.summon_later("salmon", cx + 3, -3, cz + 1, "")


def build_garrison(b, x1, z1):
    """The Doombot garrison near the foot of the Grand Stair."""
    b.section("garrison", "The Doombot garrison")
    x2, z2 = x1 + 20, z1 + 14
    b.fill(x1, -1, z1, x2, -1, z2, "polished_deepslate")
    b.fill(x1, 0, z1, x2, 9, z2, "deepslate_bricks")
    b.air(x1 + 1, 0, z1 + 1, x2 - 1, 8, z2 - 1)
    for x in range(x1 + 2, x2 - 1, 4):
        b.fill(x, 3, z1, x, 5, z1, "iron_bars")
        b.fill(x, 3, z2, x, 5, z2, "iron_bars")
    for x in range(x1, x2 + 1, 2):
        b.set(x, 10, z1, "deepslate_bricks")
        b.set(x, 10, z2, "deepslate_bricks")
    b.fill(x1 + 1, 9, z1 + 1, x2 - 1, 9, z2 - 1, "deepslate_tiles")
    cx = (x1 + x2) // 2
    b.air(cx - 1, 0, z2, cx + 1, 3, z2)
    b.set(cx, 4, z2 + 1, "dark_oak_wall_sign[facing=south]" + sign(["DOOMBOT", "GARRISON", "Doomstadt", "Division"], "dark_green", True))
    for x in (cx - 3, cx + 3):
        b.set(x, 5, z2 + 1, "green_wall_banner[facing=south]" + doom_banner())
    for i, x in enumerate(range(x1 + 2, x2 - 1, 3)):
        doombot_stand(b, x, 0, z1 + 2, yaw=0, name="Doombot Sentry %d" % (i + 1))
    for x in range(x1 + 2, x2 - 1, 6):
        b.set(x, 8, z1 + 7, "lantern[hanging=true]")
    b.set(x1 + 1, 0, z2 - 1, "chest[facing=east]" + loot("chests/village/village_weaponsmith"))
    b.set(x2 - 1, 0, z2 - 1, "smithing_table")
    b.set(x2 - 1, 0, z2 - 2, "anvil[facing=north]")


# --------------------------------------------------------------------------
# lots
# --------------------------------------------------------------------------
XB = [(-141, -103), (-97, -51), (-45, -5), (5, 45), (51, 97), (103, 141)]
ZB = [(-66, -43), (-37, -6), (6, 41), (47, 73), (79, 101)]

PROFS = ["farmer", "fisherman", "shepherd", "fletcher", "librarian", "cartographer", "cleric",
         "leatherworker", "mason", "butcher", "toolsmith", "weaponsmith", "armorer", None]


def row_houses(b, xa, xb, z_edge, facing, dmax, stories=None, avoid=None, specials=None):
    """Houses side by side between xa..xb with their fronts on z_edge (facing the lane)."""
    specials = list(specials or [])
    x = xa
    while True:
        w = RNG.randint(7, 10)
        d = RNG.randint(6, min(9, dmax))
        if x + w - 1 > xb:
            break
        zmin = z_edge - d + 1 if facing == "south" else z_edge
        if avoid and avoid(x, zmin, x + w - 1, zmin + d - 1):
            x += 3
            continue
        st = stories if stories else (2 if RNG.random() < 0.45 else 1)
        if specials:
            kind, title, prof, w2, d2, st2 = specials.pop(0)
            w, d, st = w2, min(d2, dmax + 2), st2
            if x + w - 1 > xb:
                specials.insert(0, (kind, title, prof, w2, d2, st2))
                break
            zmin = z_edge - d + 1 if facing == "south" else z_edge
            house(b, x, zmin, w, d, facing, st, None, prof, kind, title)
        else:
            house(b, x, zmin, w, d, facing, st, None, RNG.choice(PROFS))
        x += w + 2


def col_houses(b, za, zb, x_edge, facing, dmax):
    """Houses stacked along z with their fronts on x_edge (facing east or west)."""
    z = za
    while True:
        w = RNG.randint(7, 9)
        d = RNG.randint(6, min(8, dmax))
        if z + w - 1 > zb:
            break
        xmin = x_edge if facing == "east" and False else (x_edge - d + 1 if facing == "east" else x_edge)
        house(b, xmin, z, w, d, facing, 2 if RNG.random() < 0.4 else 1, None, RNG.choice(PROFS))
        z += w + 2


def plaza_clear(x1, z1, x2, z2):
    # true if the footprint comes within the plaza circle (+margin)
    nx = min(max(0, x1), x2) if not (x1 <= 0 <= x2) else 0
    nz = min(max(0, z1), z2) if not (z1 <= 0 <= z2) else 0
    return math.hypot(nx, nz) < PLAZA_R + 4


def build_quarters(b):
    b.section("houses_north", "Houses of the north quarter")
    # north band z -66..-43: fronts facing the lane at z=-40 (south)
    for (xa, xb) in (XB[2], XB[3], XB[5]):
        row_houses(b, xa + 1, xb - 1, -44, "south", 9)
    row_houses(b, XB[1][0] + 1, XB[1][0] + 18, -44, "south", 9)
    build_garrison(b, XB[1][0] + 24, -62)
    b.section("library_quarter", "Library and mason's quarter")
    row_houses(b, XB[4][0] + 1, XB[4][1] - 1, -44, "south", 9, specials=[
        ("library", ["DOOMSTADT", "LIBRARY", "& School"], "librarian", 13, 9, 2),
        ("mason", ["STONEMASON", "Guild of", "Builders"], "mason", 9, 8, 1)])
    # band z -37..-6: north side faces lane z=-40 (north), south side faces Werner Ave (south)
    b.section("houses_upper", "Houses of the upper town")
    for (xa, xb) in (XB[0], XB[5]):
        row_houses(b, xa + 1, xb - 1, -36, "north", 9)
        row_houses(b, xa + 1, xb - 1, -7, "south", 9)
    row_houses(b, XB[1][0] + 1, XB[1][1] - 1, -36, "north", 9, specials=[
        ("tavern", ["THE IRON MASK", "Tavern & Inn"], "butcher", 13, 10, 2)])
    row_houses(b, XB[1][0] + 1, XB[1][1] - 1, -7, "south", 9)
    row_houses(b, XB[3][0] + 1, XB[3][1] - 1, -36, "north", 9, avoid=plaza_clear)
    row_houses(b, XB[2][0] + 22, XB[2][1] - 1, -36, "north", 9, avoid=plaza_clear)
    # band z 6..41
    b.section("houses_lower", "Houses of the lower town")
    for (xa, xb) in (XB[0], XB[5], XB[4]):
        row_houses(b, xa + 1, xb - 1, 7, "north", 9)
        row_houses(b, xa + 1, xb - 1, 40, "south", 9,
                   specials=[("tannery", ["TANNERY"], "leatherworker", 9, 8, 1)] if xa == XB[4][0] else None)
    row_houses(b, XB[1][0] + 1, XB[1][1] - 1, 7, "north", 9, specials=[
        ("smithy", ["THE FORGE", "Armourer &", "Weaponsmith"], "armorer", 11, 9, 1),
        ("smithy", ["TOOLSMITH"], "toolsmith", 9, 8, 1)])
    row_houses(b, XB[1][0] + 1, XB[1][1] - 1, 40, "south", 9)
    row_houses(b, XB[2][0] + 1, XB[2][1] - 1, 40, "south", 9, avoid=plaza_clear, specials=[
        ("bakery", ["BAKERY", "Fresh bread", "daily"], "butcher", 11, 9, 2)])
    row_houses(b, XB[3][0] + 1, XB[3][1] - 1, 40, "south", 9, avoid=plaza_clear, specials=[
        ("clinic", ["WERNER VON DOOM", "MEMORIAL", "CLINIC"], "cleric", 13, 9, 1)])
    for (xa, xb) in (XB[2], XB[3]):
        row_houses(b, xa + 1, xb - 1, 7, "north", 9, avoid=plaza_clear)
    # band z 47..73: houses in the inner blocks
    b.section("houses_south", "Houses of the south quarter")
    for (xa, xb) in (XB[2], XB[3]):
        row_houses(b, xa + 1, xb - 1, 48, "north", 11)
        row_houses(b, xa + 1, xb - 1, 72, "south", 11)
    # band z 79..101 inner blocks
    row_houses(b, XB[3][0] + 1, XB[3][1] - 1, 80, "north", 9)
    row_houses(b, XB[2][0] + 1, XB[2][0] + 18, 80, "north", 9, specials=[
        ("fisher", ["FISHMONGER"], "fisherman", 9, 8, 1)])
    b.section("farms", "Fields and pastures")
    farm(b, XB[1][0] + 1, 48, XB[1][1] - 1, 72, "wheat[age=7]")
    farm(b, XB[4][0] + 1, 48, XB[4][1] - 1, 60, "carrots[age=7]")
    farm(b, XB[4][0] + 1, 63, XB[4][1] - 1, 72, "potatoes[age=7]")
    farm(b, XB[1][0] + 1, 80, XB[1][1] - 1, 100, "beetroots[age=3]")
    farm(b, XB[4][0] + 1, 80, XB[4][1] - 1, 100, "wheat[age=7]")
    for (xs, prof) in ((XB[1][0] + 2, "farmer"), (XB[4][0] + 2, "farmer"), (XB[1][0] + 2, "farmer")):
        pass
    villager(b, XB[1][0] - 1, 0, 60, "farmer")
    villager(b, XB[4][0] - 1, 0, 55, "farmer")
    villager(b, XB[4][0] - 1, 0, 90, "farmer")
    b.section("pastures", "Animal pens")
    pen(b, XB[5][0] + 1, 48, XB[5][0] + 17, 72, ["cow", "cow", "cow", "cow"])
    pen(b, XB[5][0] + 20, 48, XB[5][1] - 1, 60, ["sheep", "sheep", "sheep", "sheep"])
    pen(b, XB[5][0] + 20, 62, XB[5][1] - 1, 72, ["pig", "pig", "chicken", "chicken", "chicken"])
    pen(b, XB[0][0] + 1, -66, XB[0][1] - 1, -45, ["horse", "horse", "donkey"])
    build_romani_camp(b)
    b.section("orchard", "Orchard, apiary and pond")
    build_orchard(b, XB[0][0] + 1, 80, XB[0][1] - 1, 100)
    build_apiary(b, XB[5][0] + 1, 80, XB[5][1] - 1, 100)
    build_pond(b, XB[2][0] + 20, 80, XB[2][1] - 1, 100)
