"""Castle Doom: curtain walls, towers, gatehouse, drawbridge and courtyard."""
import math
import random

from core import disk_runs, ring_cells, loot, chest_items, sign, book, tc
from layout import *
from statue import build_statue
from terrain import doom_banner

WALL = "deepslate_bricks"
TRIM = "deepslate_tiles"
DARK = "polished_deepslate"
ROOF = "oxidized_cut_copper"
ROOF_STAIR = "oxidized_cut_copper_stairs"
GLASS = "green_stained_glass_pane"

DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


# --------------------------------------------------------------------------
# towers
# --------------------------------------------------------------------------
def round_tower(b, cx, cz, r, ybase, ytop, floors, ladder="north", windows=("south",),
                roof_h=None, furnish=None, cone=ROOF, rng=None):
    rng = rng or random.Random(cx * 31 + cz)
    # plinth
    for dx, z1, z2 in disk_runs(r + 1):
        b.fill(cx + dx, ybase, cz + z1, cx + dx, ybase + 2, cz + z2, DARK)
    # shell, with horizontal bands
    for dx, z1, z2 in disk_runs(r):
        b.fill(cx + dx, ybase + 3, cz + z1, cx + dx, ytop, cz + z2, WALL)
    for yb in range(ybase + 8, ytop, 8):
        for dx, z1, z2 in disk_runs(r):
            b.fill(cx + dx, yb, cz + z1, cx + dx, yb, cz + z2, TRIM)
    # weathering
    for _ in range(int(r * 6)):
        dx, dz = rng.choice(ring_cells(r, 1.0))
        y = rng.randint(ybase + 3, ytop - 2)
        b.fill(cx + dx, y, cz + dz, cx + dx, y + 1, cz + dz, "cracked_deepslate_bricks",
               "replace " + WALL)
    # hollow interior
    for dx, z1, z2 in disk_runs(r - 2):
        b.fill(cx + dx, ybase + 1, cz + z1, cx + dx, ytop - 1, cz + z2, "air")
    # floors
    for fy in floors:
        for dx, z1, z2 in disk_runs(r - 2):
            b.fill(cx + dx, fy, cz + z1, cx + dx, fy, cz + z2,
                   "spruce_planks" if fy > ybase else "polished_deepslate")
    # corbelled parapet crown
    b.ring(cx, ytop - 1, cz, r + 1, 1.0, "deepslate_tile_slab[type=top]")
    b.ring(cx, ytop, cz, r + 1, 1.0, TRIM)
    for i, (dx, dz) in enumerate(sorted(ring_cells(r + 1, 1.0), key=lambda p: math.atan2(p[1], p[0]))):
        b.set(cx + dx, ytop + 1, cz + dz, WALL)
        if (i // 2) % 2 == 0:
            b.set(cx + dx, ytop + 2, cz + dz, WALL)
    # roof cone over the top
    if roof_h:
        b.cone(cx, ytop + 1, cz, r, roof_h, cone, "lightning_rod")
    else:
        for dx, z1, z2 in disk_runs(r - 2):
            b.fill(cx + dx, ytop, cz + z1, cx + dx, ytop, cz + z2, TRIM)
    # windows
    for w in windows:
        vx, vz = DIRS[w]
        for fy in floors[1:]:
            for d in (r - 1, r):
                b.fill(cx + vx * d, fy + 2, cz + vz * d, cx + vx * d, fy + 3, cz + vz * d,
                       GLASS if d == r else "air")
    # ladder from the ground floor to the top floor
    vx, vz = DIRS[ladder]
    lx, lz = cx + vx * (r - 2), cz + vz * (r - 2)
    b.fill(cx + vx * (r - 1), ybase + 1, cz + vz * (r - 1), cx + vx * (r - 1), floors[-1] + 1,
           cz + vz * (r - 1), WALL)
    b.fill(lx, ybase + 1, lz, lx, floors[-1], lz, "ladder[facing=%s]" % OPP[ladder])
    # light and furnishings on every floor
    for i, fy in enumerate(floors):
        b.set(cx, fy + 1, cz, "lantern")
        if furnish:
            furnish(b, cx, fy, cz, r - 2, i)


def square_tower(b, cx, cz, h, ybase, ytop, floors, ladder="east", door=None, windows=()):
    x1, x2, z1, z2 = cx - h, cx + h, cz - h, cz + h
    b.fill(x1 - 1, ybase, z1 - 1, x2 + 1, ybase + 2, z2 + 1, DARK)
    b.fill(x1, ybase + 3, z1, x2, ytop, z2, WALL)
    for yb in range(ybase + 8, ytop, 8):
        b.fill(x1, yb, z1, x2, yb, z2, TRIM)
    # pilaster corners
    for (px, pz) in [(x1, z1), (x1, z2), (x2, z1), (x2, z2)]:
        b.fill(px, ybase + 3, pz, px, ytop, pz, DARK)
    b.air(x1 + 2, ybase + 1, z1 + 2, x2 - 2, ytop - 1, z2 - 2)
    for fy in floors:
        b.fill(x1 + 2, fy, z1 + 2, x2 - 2, fy, z2 - 2, "spruce_planks" if fy > ybase else DARK)
    b.fill(x1 + 2, ytop, z1 + 2, x2 - 2, ytop, z2 - 2, TRIM)
    # hipped copper roof
    for k in range(0, h + 2):
        s = h + 1 - k
        y = ytop + 1 + k
        if s <= 0:
            b.set(cx, y, cz, ROOF)
            b.set(cx, y + 1, cz, "lightning_rod")
            break
        b.fill(cx - s, y, cz - s, cx + s, y, cz - s, ROOF_STAIR + "[facing=south]")
        b.fill(cx - s, y, cz + s, cx + s, y, cz + s, ROOF_STAIR + "[facing=north]")
        b.fill(cx - s, y, cz - s + 1, cx - s, y, cz + s - 1, ROOF_STAIR + "[facing=east]")
        b.fill(cx + s, y, cz - s + 1, cx + s, y, cz + s - 1, ROOF_STAIR + "[facing=west]")
        if s > 1:
            b.fill(cx - s + 1, y, cz - s + 1, cx + s - 1, y, cz + s - 1, ROOF)
    # dormer lucarnes with lanterns on the four roof faces
    # windows
    for w in windows:
        vx, vz = DIRS[w]
        for fy in floors[1:]:
            for d in (h - 1, h):
                b.fill(cx + vx * d, fy + 2, cz + vz * d, cx + vx * d, fy + 3, cz + vz * d,
                       GLASS if d == h else "air")
    # ladder
    vx, vz = DIRS[ladder]
    lx, lz = cx + vx * (h - 2), cz + vz * (h - 2)
    b.fill(lx, ybase + 1, lz, lx, floors[-1], lz, "ladder[facing=%s]" % OPP[ladder])
    for fy in floors:
        b.set(cx, fy + 1, cz, "lantern")
    if door:
        dx_, dz_ = DIRS[door]
        px, pz = cx + dx_ * h, cz + dz_ * h
        px2, pz2 = cx + dx_ * (h - 1), cz + dz_ * (h - 1)
        b.air(px2, ybase + 1, pz2, px2, ybase + 2, pz2)
        b.door(px, ybase + 1, pz, "dark_oak", OPP[door])


# --------------------------------------------------------------------------
# tower furnishings
# --------------------------------------------------------------------------
def furnish_guard_tower(b, cx, fy, cz, ri, idx):
    y = fy + 1
    if idx == 0:
        b.set(cx + ri - 1, y, cz, "barrel[facing=up]" + loot("chests/village/village_weaponsmith"))
        b.set(cx + ri - 1, y, cz + 1, "barrel[facing=up]" + chest_items(
            [("arrow", 64), ("arrow", 64), ("bow", 1), ("crossbow", 1), ("torch", 32)]))
        b.set(cx - ri + 1, y, cz, "chest[facing=east]" + loot("chests/village/village_armorer"))
        b.set(cx - ri + 1, y, cz + 1, "smithing_table")
    elif idx == 1:
        b.bed(cx - ri + 1, y, cz + 1, "green", "west")
        b.bed(cx + ri - 1, y, cz + 1, "green", "east")
        b.set(cx, y, cz + ri - 1, "chest[facing=north]" + loot("chests/village/village_taiga_house"))
    elif idx == 2:
        b.set(cx + ri - 1, y, cz, "grindstone[face=floor,facing=north]")
        b.set(cx - ri + 1, y, cz, "anvil[facing=north]")
        b.set(cx, y, cz + ri - 1, "fletching_table")
    else:
        b.set(cx + ri - 1, y, cz, "cartography_table")
        b.set(cx - ri + 1, y, cz, "lectern[facing=east]")
        b.set(cx, y, cz + ri - 1, "barrel[facing=up]" + chest_items(
            [("spyglass", 1), ("map", 4), ("compass", 1), ("firework_rocket", 16)]))


# --------------------------------------------------------------------------
# curtain wall
# --------------------------------------------------------------------------
def build_curtain(b):
    b.section("curtain", "Raising the curtain walls")
    T = WALL_T - 1
    Y = WALL_TOP
    segs = [  # x1,x2,z1,z2, outward facing, outer row coordinate
        (WX1, WX2, WZ2 - T, WZ2, "south"),
        (WX1, WX2, WZ1, WZ1 + T, "north"),
        (WX1, WX1 + T, WZ1, WZ2, "west"),
        (WX2 - T, WX2, WZ1, WZ2, "east"),
    ]
    rng = random.Random(3)
    for x1, x2, z1, z2, out in segs:
        b.fill(x1, 5, z1, x2, Y, z2, WALL)
        b.fill(x1, 19, z1, x2, 19, z2, TRIM)
        b.fill(x1, Y, z1, x2, Y, z2, TRIM)
        # outer battered plinth
        vx, vz = DIRS[out]
        if vz:
            zz = (z2 if vz > 0 else z1) + vz
            b.fill(x1, 11, zz, x2, 12, zz, DARK)
            b.fill(x1, 13, zz, x2, 13, zz, "polished_deepslate_stairs[facing=%s]" % OPP[out])
            orow = (x1, x2, zz - vz, zz - vz)
            irow = (x1, x2, zz - vz * WALL_T, zz - vz * WALL_T)
        else:
            xx = (x2 if vx > 0 else x1) + vx
            b.fill(xx, 11, z1, xx, 12, z2, DARK)
            b.fill(xx, 13, z1, xx, 13, z2, "polished_deepslate_stairs[facing=%s]" % OPP[out])
            orow = (xx - vx, xx - vx, z1, z2)
            irow = (xx - vx * WALL_T, xx - vx * WALL_T, z1, z2)
        # battlements: outer merlons, inner rail
        ax1, ax2, az1, az2 = orow
        b.fill(ax1, Y + 1, az1, ax2, Y + 1, az2, WALL)
        length = max(ax2 - ax1, az2 - az1) + 1
        for i in range(0, length, 3):
            if vz:
                b.fill(ax1 + i, Y + 2, az1, min(ax1 + i + 1, ax2), Y + 2, az1, WALL)
                b.set(ax1 + i, Y + 3, az1, "deepslate_brick_slab[type=bottom]")
            else:
                b.fill(ax1, Y + 2, az1 + i, ax1, Y + 2, min(az1 + i + 1, az2), WALL)
                b.set(ax1, Y + 3, az1 + i, "deepslate_brick_slab[type=bottom]")
        bx1, bx2, bz1, bz2 = irow
        b.fill(bx1, Y + 1, bz1, bx2, Y + 1, bz2, "deepslate_brick_wall")
        for i in range(4, length - 4, 8):
            if vz:
                b.set(bx1 + i, Y + 1, bz1, TRIM)
                b.set(bx1 + i, Y + 2, bz1, "lantern")
            else:
                b.set(bx1, Y + 1, bz1 + i, TRIM)
                b.set(bx1, Y + 2, bz1 + i, "lantern")
        # green banners of Doom hanging outward
        for i in range(8, length - 8, 12):
            if vz:
                b.set(ax1 + i, Y - 2, az1 + vz, "green_wall_banner[facing=%s]%s" % (out, doom_banner()))
            else:
                b.set(ax1 + vx, Y - 2, az1 + i, "green_wall_banner[facing=%s]%s" % (out, doom_banner()))
        # weathering on the outer face
        for _ in range(length // 3):
            i = rng.randint(0, length - 1)
            y = rng.randint(12, Y - 2)
            if vz:
                b.fill(ax1 + i, y, az1, min(ax1 + i + 1, ax2), y + 1, az1, "cracked_deepslate_bricks",
                       "replace " + WALL)
            else:
                b.fill(ax1, y, az1 + i, ax1, y + 1, min(az1 + i + 1, az2), "cracked_deepslate_bricks",
                       "replace " + WALL)
    # stairs up to the wall walk (courtyard side)
    b.section("curtain_stairs", "Wall-walk stairways")
    for sgn in (1, -1):
        # along the south wall, rising away from the gate
        for k in range(16):
            x = sgn * (20 + k)
            f = "east" if sgn > 0 else "west"
            b.fill(x, 11, WZ2 - 4, x, 11 + k, WZ2 - 3, WALL)
            b.fill(x, 12 + k, WZ2 - 4, x, 12 + k, WZ2 - 3, "deepslate_brick_stairs[facing=%s]" % f)
        b.air(sgn * 33, Y + 1, WZ2 - 2, sgn * 36, Y + 1, WZ2 - 2)
        # along the north wall
        for k in range(16):
            x = sgn * (20 + k)
            f = "east" if sgn > 0 else "west"
            b.fill(x, 11, WZ1 + 3, x, 11 + k, WZ1 + 4, WALL)
            b.fill(x, 12 + k, WZ1 + 3, x, 12 + k, WZ1 + 4, "deepslate_brick_stairs[facing=%s]" % f)
        b.air(sgn * 33, Y + 1, WZ1 + 2, sgn * 36, Y + 1, WZ1 + 2)


def build_towers(b):
    b.section("corner_towers", "Corner towers")
    corners = [(WX1, WZ2), (WX2, WZ2), (WX1, WZ1), (WX2, WZ1)]
    for cx, cz in corners:
        sx = 1 if cx < 0 else -1          # inward x
        sz = 1 if cz < 0 else -1          # inward z (north corners are at negative z)
        sz = 1 if cz == WZ1 else -1
        out_x = "west" if cx < 0 else "east"
        round_tower(b, cx, cz, 8, 11, 44, [11, 19, 27, 35], ladder=out_x,
                    windows=("north" if cz == WZ1 else "south",), roof_h=20,
                    furnish=furnish_guard_tower)
        # doorways onto both wall walks
        b.air(cx, WALL_TOP + 1, cz, cx + 9 * sx, WALL_TOP + 2, cz + 2 * sz)
        b.air(cx, WALL_TOP + 1, cz, cx + 2 * sx, WALL_TOP + 2, cz + 9 * sz)
        b.fill(cx, WALL_TOP, cz, cx + 9 * sx, WALL_TOP, cz + 2 * sz, TRIM)
        b.fill(cx, WALL_TOP, cz, cx + 2 * sx, WALL_TOP, cz + 9 * sz, TRIM)
    b.section("wall_towers", "Wall towers")
    for cx in (WX1, WX2):
        cz = -160
        out = "west" if cx < 0 else "east"
        inn = OPP[out]
        square_tower(b, cx, cz, 5, 11, 39, [11, 19, 27, 35], ladder=out, door=inn,
                     windows=("north", "south"))
        wx1, wx2 = (cx, cx + 2) if cx < 0 else (cx - 2, cx)
        b.air(wx1, WALL_TOP + 1, cz - 6, wx2, WALL_TOP + 2, cz + 6)
        furnish_square(b, cx, cz)
    square_tower(b, 0, WZ1, 5, 11, 39, [11, 19, 27, 35], ladder="north", door="south",
                 windows=("east", "west"))
    b.air(-6, WALL_TOP + 1, WZ1, 6, WALL_TOP + 2, WZ1 + 2)
    furnish_square(b, 0, WZ1, north=True)


def furnish_square(b, cx, cz, north=False):
    # interior is cx-3..cx+3 / cz-3..cz+3; keep clear of the ladder and walk-through
    if north:
        spots = [(-3, 2), (3, 2), (-3, -2), (3, -2)]
    else:
        s = 1 if cx > 0 else -1
        spots = [(-3 * s, -3), (-3 * s, 3), (-2 * s, -3), (-2 * s, 3)]
    (ax, az), (bx, bz), (cx2, cz2), (dx, dz) = spots
    b.set(cx + ax, 12, cz + az, "chest[facing=north]" + loot("chests/village/village_armorer"))
    b.set(cx + bx, 12, cz + bz, "barrel[facing=up]" + chest_items([("cooked_beef", 32), ("bread", 32), ("golden_carrot", 16)]))
    b.set(cx + cx2, 12, cz + cz2, "crafting_table")
    b.bed(cx + ax, 20, cz + az, "green", "south" if az < 0 else "north")
    b.bed(cx + bx, 20, cz + bz, "green", "north" if bz > 0 else "south")
    b.set(cx + ax, 28, cz + az, "fletching_table")
    b.set(cx + bx, 28, cz + bz, "barrel[facing=up]" + chest_items([("arrow", 64), ("arrow", 64), ("bow", 2)]))
    b.set(cx + ax, 36, cz + az, "cartography_table")
    b.set(cx + bx, 36, cz + bz, "barrel[facing=up]" + chest_items([("spyglass", 1), ("map", 4)]))


# --------------------------------------------------------------------------
# gatehouse & drawbridge
# --------------------------------------------------------------------------
MASK_ART = [  # 7 wide, 9 tall, top row first ('G' green hood, 'I' iron, 'B' black)
    "GGGGGGG",
    "GIIIIIG",
    "GIIIIIG",
    "GBBIBBG",
    "GIIIIIG",
    "GIIBIIG",
    "GIBBBIG",
    "GIIIIIG",
    ".GIIIG.",
]
ART = {"G": "green_concrete", "I": "iron_block", "B": "black_concrete"}


def mask_relief(b, x0, ytop, z, facing_sign=1):
    for row, line in enumerate(MASK_ART):
        for col, ch in enumerate(line):
            if ch in ART:
                b.set(x0 + col, ytop - row, z, ART[ch])


def build_gatehouse(b):
    b.section("gatehouse", "The Gatehouse of Doom")
    z1, z2 = -118, -106
    b.fill(-9, 5, z1, 9, 35, z2, WALL)
    for yb in (19, 27, 35):
        b.fill(-9, yb, z1, 9, yb, z2, TRIM)
    gate_room(b, z1, z2)
    # twin drum towers
    for sgn in (-1, 1):
        cx = 10 * sgn
        round_tower(b, cx, -112, 6, 11, 39, [11, 19, 27], ladder="north", windows=("south",),
                    roof_h=16, furnish=furnish_guard_tower)
        # door from the passage
        b.air(4 * sgn, 12, -112, 5 * sgn, 13, -112)
        b.door(4 * sgn, 12, -112, "dark_oak", "east" if sgn > 0 else "west")
        # doorways to the gate room and to the wall walk
        b.air(4 * sgn, WALL_TOP + 1, -113, 5 * sgn, WALL_TOP + 2, -111)
        b.air(14 * sgn, WALL_TOP + 1, -114, 17 * sgn, WALL_TOP + 2, -112)
        b.fill(14 * sgn, WALL_TOP, -114, 17 * sgn, WALL_TOP, -112, TRIM)
    # gate passage with a pointed arch (carved after the towers so their plinths do not intrude)
    b.air(-3, 12, z1 - 1, 3, 21, z2 + 1)
    b.fill(-3, 11, z1, 3, 11, z2, "polished_deepslate")
    for z in (z1, z2):
        b.set(-3, 21, z, "deepslate_brick_stairs[facing=west,half=top]")
        b.set(3, 21, z, "deepslate_brick_stairs[facing=east,half=top]")
        b.set(-2, 21, z, "deepslate_brick_stairs[facing=west,half=top]")
        b.set(2, 21, z, "deepslate_brick_stairs[facing=east,half=top]")
    # raised portcullises (iron grilles in their slots)
    for z in (z1 + 1, z2 - 1):
        b.fill(-3, 18, z, 3, 20, z, "iron_bars")
    for z in range(z1 + 2, z2 - 1, 3):
        for x in (-2, 2):
            b.set(x, 21, z, "lantern[hanging=true]")
    # murder-hole grates in the passage ceiling
    for z in range(z1 + 3, z2 - 2, 3):
        b.set(0, 21, z, "iron_trapdoor[half=top,facing=north]")
    gate_face(b, z1, z2)


def gate_room(b, z1, z2):
    # gate room above the passage
    b.air(-3, 28, z1 + 1, 3, 34, z2 - 1)
    b.fill(-3, 27, z1 + 1, 3, 27, z2 - 1, "spruce_planks")
    b.set(0, 34, -112, "lantern[hanging=true]")
    b.set(-3, 28, z1 + 1, "chest[facing=south]" + loot("chests/village/village_weaponsmith"))
    b.set(3, 28, z1 + 1, "barrel[facing=up]" + chest_items([("arrow", 64), ("crossbow", 2), ("shield", 2)]))
    b.bed(-3, 28, z2 - 3, "black", "south")
    b.bed(3, 28, z2 - 3, "black", "south")
    b.set(0, 28, z2 - 1, "dispenser[facing=south]" + chest_items([("arrow", 64)]))
    b.set(-2, 28, z2 - 1, "lever[face=floor,facing=south]")


def gate_face(b, z1, z2):
    # roof battlements
    for x in range(-9, 10):
        for z in (z1, z2):
            b.set(x, 36, z, WALL)
            if x % 2 == 0:
                b.set(x, 37, z, WALL)
    for z in range(z1 + 1, z2):
        for x in (-9, 9):
            b.set(x, 36, z, WALL)
            if z % 2 == 0:
                b.set(x, 37, z, WALL)
    # Doom mask relief and banners over the gate
    mask_relief(b, -3, 33, z2 + 1)
    for x in (-6, 6):
        b.set(x, 33, z2 + 1, "green_wall_banner[facing=south]" + doom_banner("latveria"))
        b.set(x, 30, z2 + 1, "green_wall_banner[facing=south]" + doom_banner())
    b.set(0, 23, z2 + 1, "dark_oak_wall_sign[facing=south]" + sign(
        ["CASTLE DOOM", "Seat of the", "Latverian", "Monarchy"], "dark_green", True))


def build_drawbridge(b):
    b.section("drawbridge", "Drawbridge over the moat")
    iz2 = MOAT_IN[3]
    oz2 = MOAT_OUT[3]
    b.fill(-3, 10, iz2, 3, 10, oz2 + 2, "dark_oak_planks")
    b.fill(-3, 11, iz2 - 3, 3, 11, oz2 + 2, "spruce_planks")
    b.fill(-2, 11, iz2 - 3, 2, 11, oz2 + 2, "stripped_dark_oak_log[axis=z]")
    for x in (-4, 4):
        b.fill(x, 10, iz2 - 3, x, 11, oz2 + 2, "dark_oak_log[axis=z]")
        b.fill(x, 12, iz2 - 3, x, 12, oz2 + 2, "dark_oak_fence")
        for z in (iz2 - 3, oz2 + 2):
            b.fill(x, 12, z, x, 14, z, "dark_oak_log")
            b.set(x, 15, z, "lantern")
        # chains that raise the bridge, running up to the gatehouse
        b.fill(x, 13, iz2 - 3, x, 20, iz2 - 3, "iron_chain")
    # pillars under the bridge
    for z in range(iz2 + 1, oz2, 2):
        b.fill(-3, 5, z, -3, 9, z, "stone_bricks")
        b.fill(3, 5, z, 3, 9, z, "stone_bricks")
    # approach between the stair top and the bridge
    b.fill(-STAIR_X, 11, PLAT[3] - 1, STAIR_X, 11, PLAT[3], "stone_bricks")
    b.fill(-3, 11, oz2 + 1, 3, 11, PLAT[3], "polished_deepslate")


# --------------------------------------------------------------------------
# courtyard
# --------------------------------------------------------------------------
def lamp_post(b, x, y, z, style="dark_oak_fence"):
    b.set(x, y, z, "polished_deepslate")
    b.fill(x, y + 1, z, x, y + 3, z, style)
    b.set(x, y + 4, z, "lantern")


def build_courtyard(b):
    b.section("courtyard", "Courtyard of Castle Doom")
    ix1, ix2, iz1, iz2 = WX1 + 3, WX2 - 3, WZ1 + 3, WZ2 - 3
    rng = random.Random(11)
    # processional way from the gate to the keep
    b.fill(-4, 11, KEEP[3] + 1, 4, 11, iz2, "stone_bricks")
    b.fill(-1, 11, KEEP[3] + 1, 1, 11, iz2, "polished_deepslate")
    # ring road around the keep
    kx1, kx2, kz1, kz2 = KEEP
    for (a, c_, d, e) in [(kx1 - 4, kx2 + 4, kz2 + 1, kz2 + 4), (kx1 - 4, kx2 + 4, kz1 - 4, kz1 - 1),
                          (kx1 - 4, kx1 - 1, kz1 - 4, kz2 + 4), (kx2 + 1, kx2 + 4, kz1 - 4, kz2 + 4)]:
        b.fill(a, 11, d, c_, 11, e, "stone_bricks")
    for _ in range(120):
        x, z = rng.randint(kx1 - 4, kx2 + 4), rng.randint(kz1 - 4, iz2)
        if kx1 <= x <= kx2 and kz1 <= z <= kz2:
            continue
        b.fill(x, 11, z, x, 11, z, rng.choice(["cracked_stone_bricks", "mossy_stone_bricks", "andesite"]),
               "replace stone_bricks")
    # fountain of Doom in the outer bailey
    fz = -133
    for dx, z1, z2 in disk_runs(8):
        b.fill(dx, 10, fz + z1, dx, 11, fz + z2, "polished_deepslate")
    for dx, z1, z2 in disk_runs(7):
        b.fill(dx, 11, fz + z1, dx, 11, fz + z2, "water")
    b.ring(0, 12, fz, 8, 1.0, "polished_deepslate_slab[type=bottom]")
    b.fill(-2, 11, fz - 2, 2, 13, fz + 2, "polished_deepslate")
    b.fill(-2, 14, fz - 2, 2, 14, fz + 2, "deepslate_tile_slab[type=bottom]")
    b.fill(-1, 14, fz - 1, 1, 14, fz + 1, "polished_deepslate")
    build_statue(b, 0, 15, fz, 0.5, rot=0)
    for (dx, dz) in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
        b.set(dx, 14, fz + dz, "sea_lantern")
    for (dx, dz) in [(-5, 0), (5, 0), (0, 5), (0, -5)]:
        b.set(dx, 10, fz + dz, "sea_lantern")
    # re-route the processional way around the fountain
    b.fill(-9, 11, fz - 10, 9, 11, fz - 9, "stone_bricks")
    b.fill(-9, 11, fz + 9, 9, 11, fz + 10, "stone_bricks")
    for sx in (-10, 10):
        b.fill(sx - 1, 11, fz - 10, sx, 11, fz + 10, "stone_bricks")
    # lamp posts lining the way
    for z in range(iz2 - 2, kz2 + 2, -6):
        if abs(z - fz) <= 11:
            continue
        lamp_post(b, -6, 12, z)
        lamp_post(b, 6, 12, z)
    for x in range(kx1 - 2, kx2 + 3, 10):
        lamp_post(b, x, 12, kz2 + 5)
        lamp_post(b, x, 12, kz1 - 5)
    for z in range(kz1, kz2 + 1, 10):
        lamp_post(b, kx1 - 5, 12, z)
        lamp_post(b, kx2 + 5, 12, z)
    # courtyard lighting in the grassy areas
    for x in range(ix1 + 4, ix2, 12):
        for z in range(iz1 + 4, iz2, 12):
            if kx1 - 6 <= x <= kx2 + 6 and kz1 - 6 <= z <= kz2 + 6:
                continue
            if abs(x) < 12 and abs(z - fz) < 12:
                continue
            b.set(x, 12, z, "lantern")
            b.set(x, 11, z, "polished_deepslate")
    build_stables(b)
    build_forge(b)
    build_barracks(b)
    build_memorial(b)
    build_training_yard(b)


def build_stables(b):
    b.section("stables", "Royal stables")
    x1, x2, z1, z2 = -48, -36, -150, -120
    b.fill(x1, 11, z1, x2, 11, z2, "spruce_planks")
    b.walls(x1, 12, z1, x1, 17, z2, "stone_bricks")
    b.fill(x1, 12, z1, x2, 17, z1, "stone_bricks")
    b.fill(x1, 12, z2, x2, 17, z2, "stone_bricks")
    # timber front with posts
    for z in range(z1, z2 + 1, 5):
        b.fill(x2, 12, z, x2, 17, z, "dark_oak_log")
    b.fill(x1, 17, z1, x2, 17, z2, "dark_oak_planks")
    # lean-to roof
    for i, x in enumerate(range(x2 + 1, x1 - 2, -1)):
        y = 18 + i // 3
        b.fill(x, y, z1 - 1, x, y, z2 + 1, "dark_oak_slab[type=bottom]" if i % 3 == 0 else "dark_oak_planks")
    # stalls
    for zs in range(z1 + 1, z2 - 3, 5):
        b.fill(x1 + 1, 12, zs, x2 - 4, 12, zs, "spruce_fence")
        b.set(x2 - 3, 12, zs + 2, "spruce_fence_gate[facing=east]")
        b.fill(x2 - 3, 12, zs + 1, x2 - 3, 12, zs + 1, "spruce_fence")
        b.fill(x2 - 3, 12, zs + 3, x2 - 3, 12, zs + 4, "spruce_fence")
        b.set(x1 + 1, 12, zs + 2, "hay_block[axis=x]")
        b.set(x1 + 1, 12, zs + 3, "water_cauldron[level=3]")
        b.set(x1 + 2, 16, zs + 2, "lantern[hanging=true]")
        b.summon_later("horse", x1 + 3, 12, zs + 2,
                 '{Tame:1b,PersistenceRequired:1b,Variant:%d,equipment:{saddle:{id:"minecraft:saddle",count:1}},CustomName:"%s"}'
                 % ([0, 1, 3, 4, 5, 6][(zs // 5) % 6], ["Kraken", "Nocturne", "Tempest", "Vendetta", "Ironhoof", "Sable"][(zs // 5) % 6]))
    b.set(x2 - 1, 12, z1 + 1, "chest[facing=west]" + chest_items(
        [("saddle", 2), ("lead", 6), ("iron_horse_armor", 1), ("golden_horse_armor", 1),
         ("diamond_horse_armor", 1), ("hay_block", 16), ("golden_apple", 2), ("golden_carrot", 16)]))
    b.set(x2 - 1, 12, z2 - 1, "composter[level=0]")
    b.set(x2 - 2, 12, z2 - 1, "hay_block")
    b.set(x2 - 2, 13, z2 - 1, "hay_block")


def build_forge(b):
    b.section("forge", "The castle forge")
    x1, x2, z1, z2 = 36, 48, -150, -134
    b.fill(x1, 11, z1, x2, 11, z2, "polished_deepslate")
    b.walls(x1, 12, z1, x2, 17, z2, "stone_bricks")
    b.fill(x1, 18, z1, x2, 18, z2, "deepslate_tiles")
    for x in range(x1, x2 + 1, 4):
        for z in (z1, z2):
            b.fill(x, 12, z, x, 17, z, "polished_deepslate")
    # open arcade toward the courtyard
    for z in range(z1 + 2, z2 - 1, 4):
        b.air(x1, 12, z, x1, 15, z + 1)
    # chimney & forge hearth with lava behind glass
    b.fill(x2 - 3, 12, z1 + 5, x2 - 1, 13, z1 + 9, "bricks")
    b.set(x2 - 2, 13, z1 + 7, "lava")
    b.set(x2 - 3, 13, z1 + 7, "iron_bars")
    b.fill(x2 - 3, 19, z1 + 6, x2 - 1, 24, z1 + 8, "bricks")
    b.set(x2 - 2, 25, z1 + 7, "campfire[lit=true,signal_fire=true]")
    b.set(x2 - 2, 24, z1 + 7, "hay_block")
    b.set(x2 - 2, 18, z1 + 7, "bricks")
    b.set(x2 - 1, 12, z1 + 2, "blast_furnace[facing=west]")
    b.set(x2 - 1, 12, z1 + 3, "blast_furnace[facing=west]")
    b.set(x2 - 1, 12, z1 + 11, "smithing_table")
    b.set(x2 - 1, 12, z1 + 12, "grindstone[face=floor,facing=west]")
    b.set(x2 - 4, 12, z1 + 3, "anvil[facing=north]")
    b.set(x2 - 4, 12, z1 + 12, "chipped_anvil[facing=north]")
    b.set(x1 + 2, 12, z1 + 1, "chest[facing=south]" + loot("chests/village/village_toolsmith"))
    b.set(x1 + 3, 12, z1 + 1, "chest[facing=south]" + chest_items(
        [("iron_ingot", 64), ("gold_ingot", 32), ("coal", 64), ("iron_block", 8),
         ("netherite_upgrade_smithing_template", 1), ("diamond", 8)]))
    b.set(x1 + 4, 12, z1 + 1, "water_cauldron[level=3]")
    b.set(x1 + 5, 12, z1 + 1, "stonecutter[facing=south]")
    for z in range(z1 + 3, z2, 5):
        b.set(x1 + 5, 17, z, "lantern[hanging=true]")
        b.set(x2 - 5, 17, z, "lantern[hanging=true]")


def build_barracks(b):
    b.section("barracks", "Barracks of the Latverian Guard")
    x1, x2, z1, z2 = 36, 48, -198, -168
    b.fill(x1, 11, z1, x2, 11, z2, "spruce_planks")
    b.walls(x1, 12, z1, x2, 25, z2, "stone_bricks")
    b.fill(x1 + 1, 18, z1 + 1, x2 - 1, 18, z2 - 1, "spruce_planks")
    for z in range(z1, z2 + 1, 6):
        b.fill(x1, 12, z, x1, 25, z, "polished_deepslate")
        b.fill(x2, 12, z, x2, 25, z, "polished_deepslate")
    # windows
    for z in range(z1 + 3, z2 - 1, 6):
        for y in (14, 21):
            b.fill(x1, y, z, x1, y + 1, z, GLASS)
            b.fill(x2, y, z, x2, y + 1, z, GLASS)
    # gabled copper roof along z
    for i in range(0, 9):
        y = 26 + i
        xa, xb = x1 - 1 + i, x2 + 1 - i
        if xa > xb:
            break
        if xa == xb:
            b.fill(xa, y, z1 - 1, xa, y, z2 + 1, ROOF)
            break
        b.fill(xa, y, z1 - 1, xa, y, z2 + 1, ROOF_STAIR + "[facing=east]")
        b.fill(xb, y, z1 - 1, xb, y, z2 + 1, ROOF_STAIR + "[facing=west]")
        b.fill(xa + 1, y, z1, xb - 1, y, z1, "stone_bricks")
        b.fill(xa + 1, y, z2, xb - 1, y, z2, "stone_bricks")
    # doors
    b.air(x1, 12, -180, x1, 13, -179)
    b.door(x1, 12, -180, "dark_oak", "east", "left")
    b.door(x1, 12, -179, "dark_oak", "east", "right")
    # bunks on both floors
    for fl, y in enumerate((12, 19)):
        for z in range(z1 + 2, z2 - 1, 3):
            if fl == 0 and -182 <= z <= -177:
                continue
            b.bed(x2 - 2, y, z, "green", "east")
            if z % 2 == 0:
                b.set(x2 - 3, y, z + 1, "chest[facing=west]" + loot("chests/village/village_taiga_house"))
            b.bed(x1 + 3, y, z, "black", "west")
        for z in range(z1 + 3, z2, 7):
            b.set(x1 + 6, y + 5 if y == 12 else y, z, "lantern[hanging=true]" if y == 12 else "lantern")
        b.set(x1 + 7, y, z1 + 2, "crafting_table")
        b.set(x1 + 8, y, z1 + 2, "furnace[facing=south]")
        b.set(x1 + 6, y, z1 + 2, "barrel[facing=up]" + chest_items([("bread", 64), ("cooked_mutton", 32), ("apple", 32)]))
    # ladder between floors
    b.fill(x1 + 7, 12, z2 - 1, x1 + 7, 18, z2 - 1, "ladder[facing=north]")
    # armour stands of the guard
    for z in range(z1 + 4, z2 - 3, 9):
        guard_stand(b, x1 + 6, 12, z, yaw=90)


def guard_stand(b, x, y, z, yaw=0, name="Latverian Guard"):
    b.armor_stand(x, y, z, yaw, name, {
        "head": ("iron_helmet", None),
        "chest": ("leather_chestplate", "dyed_color=2004515"),
        "legs": ("chainmail_leggings", None),
        "feet": ("iron_boots", None),
        "mainhand": ("iron_spear", None),
        "offhand": ("shield", None)})


def doombot_stand(b, x, y, z, yaw=0, name="Doombot", netherite=False):
    m = "netherite" if netherite else "iron"
    b.armor_stand(x, y, z, yaw, name, {
        "head": (m + "_helmet", None),
        "chest": ("leather_chestplate", "dyed_color=1332255"),
        "legs": (m + "_leggings", None),
        "feet": (m + "_boots", None)},
        extra="Pose:{RightArm:[-15f,0f,10f],LeftArm:[-15f,0f,-10f]}")


def build_memorial(b):
    """Cynthia von Doom's memorial garden and mausoleum (west of the keep)."""
    b.section("memorial", "Memorial garden of Cynthia von Doom")
    x1, x2, z1, z2 = -49, -36, -198, -168
    rng = random.Random(5)
    b.fill(x1, 11, z1, x2, 11, z2, "grass_block")
    b.fill(x1 + 6, 11, z1, x1 + 8, 11, z2, "moss_block")
    # hedge border
    b.fill(x2, 12, z1, x2, 12, z2, "dark_oak_leaves[persistent=true]")
    b.air(x2, 12, -181, x2, 12, -177)
    flowers = ["allium", "lilac", "blue_orchid", "azure_bluet", "lily_of_the_valley", "cornflower",
               "white_tulip", "oxeye_daisy", "torchflower", "pink_tulip"]
    for _ in range(90):
        x, z = rng.randint(x1, x2 - 1), rng.randint(z1, z2)
        if -191 <= z <= -171 and x1 + 2 <= x <= x2 - 2:
            continue
        f = rng.choice(flowers)
        if f == "lilac":
            b.tall_plant(x, 12, z, "lilac")
        else:
            b.set(x, 12, z, f)
    # the mausoleum
    mx1, mx2, mz1, mz2 = -47, -39, -190, -172
    b.fill(mx1, 11, mz1, mx2, 12, mz2, "polished_blackstone")
    b.fill(mx1 + 1, 13, mz1 + 1, mx2 - 1, 19, mz2 - 1, "polished_blackstone_bricks")
    b.air(mx1 + 2, 13, mz1 + 2, mx2 - 2, 18, mz2 - 2)
    b.fill(mx1 + 2, 12, mz1 + 2, mx2 - 2, 12, mz2 - 2, "polished_deepslate")
    for (px, pz) in [(mx1 + 1, mz1 + 1), (mx1 + 1, mz2 - 1), (mx2 - 1, mz1 + 1), (mx2 - 1, mz2 - 1)]:
        b.fill(px, 13, pz, px, 21, pz, "chiseled_polished_blackstone")
        b.set(px, 22, pz, "soul_lantern")
    # stepped pyramidal roof
    for k in range(4):
        b.fill(mx1 + 1 + k, 20 + k, mz1 + 2 + k, mx2 - 1 - k, 20 + k, mz2 - 2 - k,
               "polished_blackstone_bricks")
    b.set(-43, 24, -181, "polished_blackstone_wall")
    b.set(-43, 25, -181, "soul_lantern")
    # entrance facing east
    b.air(mx2 - 1, 13, -182, mx2 - 1, 15, -180)
    b.set(mx2 - 1, 16, -181, "polished_blackstone_brick_stairs[facing=east,half=top]")
    b.fill(mx2, 12, -182, mx2 + 1, 12, -180, "polished_blackstone_slab[type=bottom]")
    # interior: sarcophagus, candles, book of remembrance
    b.fill(-44, 13, -184, -42, 14, -178, "polished_deepslate")
    b.set(-44, 15, -184, "green_candle[candles=3,lit=true]")
    b.set(-42, 15, -178, "green_candle[candles=3,lit=true]")
    b.set(-44, 15, -178, "white_candle[candles=2,lit=true]")
    b.set(-42, 15, -184, "white_candle[candles=2,lit=true]")
    b.set(-43, 15, -181, "potted_lily_of_the_valley")
    b.set(-41, 13, -181, "dark_oak_wall_sign[facing=east]" + sign(
        ["Cynthia", "von Doom", "Beloved Mother", "Sorceress"], "dark_purple", True))
    b.set(-45, 13, -187, "soul_lantern")
    b.set(-45, 13, -175, "soul_lantern")
    b.set(-41, 13, -187, "potted_lily_of_the_valley")
    b.set(-41, 13, -175, "potted_allium")
    b.set(-45, 13, -181, "lectern[facing=east,has_book=true]" + cynthia_book())
    b.set(-43, 18, -176, "soul_lantern[hanging=true]")
    b.set(-43, 18, -186, "soul_lantern[hanging=true]")
    # a ring of amethyst — her sorcerous circle
    b.ring(-41, 12, -164, 4, 1.0, "amethyst_block")
    b.set(-41, 12, -164, "enchanting_table")
    b.feature("azalea_tree", -44, 12, -197)
    b.feature("azalea_tree", -38, 12, -160)


def build_training_yard(b):
    b.section("training", "Doombot proving ground")
    for i, z in enumerate(range(-204, -198, 3)):
        pass
    # targets and practice dummies north of the forge
    for x in (38, 42, 46):
        b.set(x, 12, -123, "hay_block")
        b.set(x, 13, -123, "target")
    for x in (38, 44):
        doombot_stand(b, x, 12, -128, yaw=180, name="Practice Doombot")


def cynthia_book():
    pages = [
        "In memory of Cynthia von Doom, sorceress of the Latverian Romani, who dared to bargain with the Devil to save her people.",
        "Her son swore upon her grave that he would free her soul from Mephisto's realm, whatever the cost. Each Midsummer's Eve he keeps that vow.",
        "\"Mother, I have not forgotten.\"\n\n- V.",
    ]
    return book_nbt("In Memoriam", "Victor von Doom", pages)


def book_nbt(title, author, pages):
    return book(title, author, pages)
