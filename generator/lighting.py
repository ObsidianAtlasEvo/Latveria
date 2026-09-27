"""Latveria Lighting Overhaul: bright, architectural light for the whole capital.

Runs on top of the first build and Survival Expansion v2.  Two layers:

1. Designed features, placed by hand:
   - glowing runner hidden beneath the throne-room carpet, Doom-green light bands on the pillars
   - glass-over-froglight light strips along the dungeon corridor, a light ring on the Time Platform
   - flush lights along the castle wall walks, the processional way and the Grand Stair
   - green uplights set into the plinth of every castle wall, a glowing ring on the plaza, a
     lit rim around the statue plinth, and runway lights down Doom Boulevard, Werner Avenue
     and the lanes
2. A light-level pass over every room of the castle, the town and the new districts.  Wherever
   the place a person stands is dimmer than level 11, it adds light in this order of preference:
     ceiling coffer   a flush light panel set into the ceiling (material-matched)
     wall sconce      a light recessed flush into a thick wall at eye level
     floor inlay      glass over a froglight (where the floor is two blocks thick),
                      otherwise a flush light tile
     lantern          only where none of the above is possible
   Material matching: wood gets shroomlight, deepslate/blackstone gets ochre froglight, stone
   gets sea lanterns, and the dungeons and laboratory get Doom-green verdant froglight.

Every replacement is written as `fill ... replace <the block that was built there>`, so any block
the player has since changed by hand is left alone.
"""
import re

import numpy as np

from core import pos, check_block
from layout import *

STRUCT = {
    "dark_oak_planks": "wood", "spruce_planks": "wood", "oak_planks": "wood", "mangrove_planks": "wood",
    "birch_planks": "wood", "stripped_dark_oak_log": "wood",
    "deepslate_bricks": "dark", "deepslate_tiles": "dark", "polished_deepslate": "dark", "cracked_deepslate_bricks": "dark",
    "blackstone": "dark", "polished_blackstone": "dark", "polished_blackstone_bricks": "dark",
    "stone_bricks": "stone", "polished_andesite": "stone", "smooth_stone": "stone", "stone": "stone",
    "cobblestone": "stone", "mossy_cobblestone": "stone", "bricks": "brick", "mud_bricks": "brick",
    "calcite": "plaster", "white_terracotta": "plaster", "yellow_terracotta": "plaster",
    "light_gray_terracotta": "plaster", "smooth_sandstone": "plaster", "smooth_quartz": "stone",
}
DEPENDENT = ("ladder", "iron_chain", "lever", "bell", "pointed_dripstone", "lantern", "soul_lantern",
             "copper_lantern", "vine", "glow_lichen", "tripwire_hook", "cocoa")
DEPENDENT_SUFFIX = ("_banner", "_sign", "torch", "_button", "_lantern")
FEET_OK = ("air", "light", "short_grass", "fern", "poppy", "dandelion", "cornflower", "oxeye_daisy", "azure_bluet",
           "allium", "blue_orchid", "lily_of_the_valley")
FEET_SUFFIX = ("_carpet", "_pressure_plate", "rail", "_tulip")

# the player's own Doombot factory room (left exactly as they rebuilt it)
FACTORY = (-29, 0, -195, -5, 11, -167)


class Lighter:
    def __init__(self, b, world, protected):
        self.b, self.w = b, world
        self.protected = set(protected)
        self.placed = []          # (x, y, z, kind)
        self.count = 0

    # ---- primitive: replace exactly the block we expect ------------------
    def swap(self, x, y, z, new, expect=None):
        cur = self.w.name(x, y, z)
        if expect is None:
            expect = cur
        if cur != expect or (x, y, z) in self.protected:
            return False
        check_block(new)
        self.b.raw("fill %s %s %s replace %s" % (pos(x, y, z), pos(x, y, z), new, expect), 1)
        self.w.apply("setblock %s %s" % (pos(x, y, z), new))
        self.count += 1
        return True

    def swap_line(self, x1, y1, z1, x2, y2, z2, new, expect):
        check_block(new)
        self.b.raw("fill %s %s %s replace %s" % (pos(x1, y1, z1), pos(x2, y2, z2), new, expect), 1)
        self.w.apply("fill %s %s %s replace %s" % (pos(x1, y1, z1), pos(x2, y2, z2), new, expect))
        self.count += 1

    def free_of_dependents(self, x, y, z):
        for (dx, dy, dz) in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = self.w.name(x + dx, y + dy, z + dz)
            if n in DEPENDENT or n.endswith(DEPENDENT_SUFFIX):
                return False
        return (x, y, z) not in self.protected

    def near_placed(self, x, y, z, r):
        for (px, py, pz, _) in self.placed[-4000:]:
            if abs(px - x) <= r and abs(py - y) <= r and abs(pz - z) <= r:
                return True
        return False


def light_for(material, zone, where):
    cls = STRUCT.get(material)
    if zone in ("dungeon", "lab"):
        return "verdant_froglight"
    if cls == "wood":
        return "shroomlight"
    if cls == "dark":
        return "ochre_froglight" if where != "floor" else "pearlescent_froglight"
    if cls == "brick":
        return "ochre_froglight"
    if cls == "plaster":
        return "shroomlight"
    return "sea_lantern"


def zone_of(x, y, z):
    if -30 <= x <= 30 and -196 <= z <= -150 and 0 <= y <= 11:
        return "dungeon"
    if 1 <= x <= 28 and -194 <= z <= -164 and 27 <= y <= 37:
        return "lab"
    if y < -5:
        return "dungeon"
    return "general"


# --------------------------------------------------------------------------
# designed features
# --------------------------------------------------------------------------
def designed_castle(L):
    b, w = L.b, L.w
    b.section("light_throne", "Light: the Throne Room")
    # glowing runner hidden under the green carpet (the floor block beneath carpet)
    L.swap_line(0, 11, -185, 0, 11, -152, "ochre_froglight", "polished_deepslate")
    L.swap_line(0, 11, -185, 0, 11, -152, "ochre_froglight", "deepslate_tiles")
    for z in range(-184, -152, 3):
        for x in (-2, 2):
            L.swap(x, 11, z, "ochre_froglight")
    # Doom-green light bands around every pillar
    for x in (-13, 12):
        for z in range(-188, -153, 6):
            L.swap_line(x, 19, z, x + 1, 19, z + 1, "verdant_froglight", "polished_deepslate")
    # lit dais edges
    for x in range(-10, 11, 4):
        L.swap(x, 12, -187, "ochre_froglight")
    b.section("light_dungeon_strips", "Light: glass light strips in the dungeon")
    # corridor floor: glass tiles over green froglight, as in the rebuilt factory
    for x in range(-26, 27):
        for z in (-165, -164):
            if w.name(x, 1, z) in ("deepslate_tiles", "polished_deepslate") and w.name(x, 0, z) == "deepslate_bricks" \
                    and w.name(x, 2, z) == "air":
                L.swap(x, 0, z, "verdant_froglight")
                L.swap(x, 1, z, "glass")
    # the Time Platform: a ring of light in the quartz dais
    import math
    for a in range(0, 360, 15):
        x = 12 + round(7.4 * math.cos(math.radians(a)))
        z = -181 + round(7.4 * math.sin(math.radians(a)))
        L.swap(x, 1, z, "sea_lantern", "smooth_quartz")
    b.section("light_battlements", "Light: wall walks, processional way, uplights")
    Y = 27
    for (x1, x2, z) in ((-49, 49, -113), (-49, 49, -207)):
        for x in range(x1, x2 + 1, 5):
            L.swap(x, Y, z, "ochre_froglight", "deepslate_tiles")
    for (x, z1, z2) in ((-51, -205, -115), (51, -205, -115)):
        for z in range(z1, z2 + 1, 5):
            L.swap(x, Y, z, "ochre_froglight", "deepslate_tiles")
    # green uplights in the battered plinth at the foot of every curtain wall
    for x in range(-48, 49, 8):
        L.swap(x, 12, -111, "verdant_froglight", "polished_deepslate")
        L.swap(x, 12, -209, "verdant_froglight", "polished_deepslate")
    for z in range(-204, -115, 8):
        L.swap(-53, 12, z, "verdant_froglight", "polished_deepslate")
        L.swap(53, 12, z, "verdant_froglight", "polished_deepslate")
    # processional way from the gate to the keep
    for z in range(-148, -114, 3):
        L.swap(0, 11, z, "sea_lantern", "polished_deepslate")
    # Grand Stair: lights in the centre of every full step
    for j in range(0, STAIR_Z2 - STAIR_Z1 + 1, 2):
        L.swap(0, 11 - j // 2, STAIR_Z1 + j, "sea_lantern", "polished_deepslate")
    # keep roof: a lit cross on the roof walk
    for x in range(-26, 27, 4):
        L.swap(x, 47, -158, "ochre_froglight", "deepslate_tiles")
        L.swap(x, 47, -190, "ochre_froglight", "deepslate_tiles")


def designed_town(L):
    b, w = L.b, L.w
    b.section("light_streets", "Light: the plaza and the streets")
    import math
    # a glowing ring and twelve rays on the plaza
    for a in range(0, 360, 10):
        x, z = round(17 * math.cos(math.radians(a))), round(17 * math.sin(math.radians(a)))
        L.swap(x, -1, z, "pearlescent_froglight", "polished_deepslate")
    for a in range(15, 360, 30):
        for r in (12, 20):
            x, z = round(r * math.cos(math.radians(a))), round(r * math.sin(math.radians(a)))
            L.swap(x, -1, z, "sea_lantern")
    # lit rim around the Colossus plinth
    for x in range(-10, 11, 3):
        L.swap(x, 4, -8, "verdant_froglight", "deepslate_tiles")
        L.swap(x, 4, 8, "verdant_froglight", "deepslate_tiles")
    for z in range(-5, 6, 3):
        L.swap(-11, 4, z, "verdant_froglight", "deepslate_tiles")
        L.swap(11, 4, z, "verdant_froglight", "deepslate_tiles")
    # runway lights down the centre of the avenues and lanes
    for z in list(range(-66, -24, 6)) + list(range(28, 240, 6)):
        L.swap(0, -1, z, "sea_lantern")
    for x in list(range(-296, -26, 6)) + list(range(30, 297, 6)):
        L.swap(x, -1, 0, "sea_lantern")
    for zc in (-40, 44, 76):
        for x in range(-138, 139, 8):
            L.swap(x, -1, zc, "sea_lantern")
    for xc in (-100, -48, 48, 100):
        for z in range(-62, 101, 8):
            L.swap(xc, -1, z, "sea_lantern")
    # town wall walk
    for z in range(-70, 103, 6):
        L.swap(-143, 8, z, "ochre_froglight", "stone_bricks")
        L.swap(143, 8, z, "ochre_froglight", "stone_bricks")
    for x in range(-140, 141, 6):
        L.swap(x, 8, 103, "ochre_froglight", "stone_bricks")


# --------------------------------------------------------------------------
# light-level pass
# --------------------------------------------------------------------------
def light_pass(L, box, title, target=11, exclude=(), max_rounds=25):
    b, w = L.b, L.w
    b.section("light_" + title.replace(" ", "_").lower(), "Light: " + title)
    x1, y1, z1, x2, y2, z2 = box

    def excluded(x, y, z):
        for (a, b_, c_, d, e, f) in exclude:
            if a <= x <= d and b_ <= y <= e and c_ <= z <= f:
                return True
        return False

    names = None
    for rnd in range(max_rounds):
        Lgt, sub, (ox, oy, oz) = w.block_light(box)
        st = w.states
        nm = np.array([s.split("[", 1)[0] for s in st])
        feet_ok = np.array([n in FEET_OK or n.endswith(FEET_SUFFIX) for n in nm])
        head_ok = np.array([n in FEET_OK for n in nm])
        opaque = w._class_luts()[1]
        solid = np.array([n not in ("air", "water", "lava", "light") and not n.endswith(("_carpet",)) for n in nm])
        S = sub
        feet = feet_ok[S]
        head = np.roll(head_ok[S], -1, axis=1)
        below = np.roll(solid[S], 1, axis=1)
        # covered = something opaque somewhere above in the column (an interior)
        op = opaque[S]
        covered = np.flip(np.cumsum(np.flip(op, axis=1), axis=1), axis=1) > 0
        covered = np.roll(covered, -2, axis=1)
        lite = np.maximum(Lgt, np.roll(Lgt, -1, axis=1))
        dark = feet & head & below & covered & (lite < target)
        dark = dark[x1 - ox:x2 - ox + 1, y1 - oy:y2 - oy + 1, z1 - oz:z2 - oz + 1]
        lite_c = lite[x1 - ox:x2 - ox + 1, y1 - oy:y2 - oy + 1, z1 - oz:z2 - oz + 1]
        pts = np.argwhere(dark)
        if len(pts) == 0:
            break
        order = np.argsort(lite_c[dark], kind="stable")
        pts = pts[order]
        batch = set()
        placed_now = 0
        for p in pts:
            x, y, z = int(p[0]) + x1, int(p[1]) + y1, int(p[2]) + z1
            if excluded(x, y, z):
                continue
            key = (x // 5, y // 6, z // 5)
            if key in batch:
                continue
            if place_for(L, x, y, z):
                batch.add(key)
                placed_now += 1
        if placed_now == 0:
            break
    Lgt, sub, (ox, oy, oz) = w.block_light(box)
    return L.count


def place_for(L, x, y, z):
    """Light the standing cell (x,y,z): feet at y, head at y+1."""
    w = L.w
    zone = zone_of(x, y, z)
    # 1. ceiling coffer within 4 blocks above the head
    for dy in range(2, 7):
        n = w.name(x, y + dy, z)
        if n in ("air", "light"):
            continue
        if n in STRUCT and dy <= 5 and L.free_of_dependents(x, y + dy, z) and not L.near_placed(x, y + dy, z, 2):
            if L.swap(x, y + dy, z, light_for(n, zone, "ceiling")):
                L.placed.append((x, y + dy, z, "ceiling"))
                return True
        break
    # 2. wall sconce: nearest thick wall at head height within 4 blocks
    for (dx, dz) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        for d in range(1, 5):
            wx, wz = x + dx * d, z + dz * d
            n = w.name(wx, y + 1, wz)
            if n in ("air", "light") or n in FEET_OK:
                continue
            behind = w.name(wx + dx, y + 1, wz + dz)
            if n in STRUCT and behind not in ("air", "water", "light") and L.free_of_dependents(wx, y + 1, wz) \
                    and not L.near_placed(wx, y + 1, wz, 3):
                if L.swap(wx, y + 1, wz, light_for(n, zone, "wall")):
                    L.placed.append((wx, y + 1, wz, "wall"))
                    return True
            break
    # 3. floor inlay under the cell (or a neighbour)
    for (dx, dz) in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        fx, fz = x + dx, z + dz
        n = w.name(fx, y - 1, fz)
        if n in STRUCT and L.free_of_dependents(fx, y - 1, fz) and not L.near_placed(fx, y - 1, fz, 2) \
                and w.name(fx, y, fz) in FEET_OK + ("air",):
            under = w.name(fx, y - 2, fz)
            if under in STRUCT and L.free_of_dependents(fx, y - 2, fz):
                L.swap(fx, y - 2, fz, "verdant_froglight" if zone != "general" else "ochre_froglight")
                L.swap(fx, y - 1, fz, "glass")
            else:
                L.swap(fx, y - 1, fz, light_for(n, zone, "floor"))
            L.placed.append((fx, y - 1, fz, "floor"))
            return True
    # 4. a lantern on the floor
    if w.name(x, y, z) == "air" and not L.near_placed(x, y, z, 2):
        L.b.raw("setblock %s lantern keep" % pos(x, y, z), 1)
        w.apply("setblock %s lantern" % pos(x, y, z))
        L.count += 1
        L.placed.append((x, y, z, "lantern"))
        return True
    return False


def frame_supports(paths):
    """Blocks that hold item frames (entities the voxel model does not see)."""
    out = set()
    tok = re.compile(r"\$([xyz])\((-?[0-9.]+)\)")
    back = {"2": (0, 0, 1), "3": (0, 0, -1), "4": (1, 0, 0), "5": (-1, 0, 0), "0": (0, 1, 0), "1": (0, -1, 0)}
    for p in paths:
        for line in open(p, encoding="utf-8"):
            if "item_frame" not in line or "summon" not in line:
                continue
            v = [int(float(t) // 1) for _, t in tok.findall(line)]
            f = re.search(r"Facing:(\d)b", line).group(1)
            dx, dy, dz = back[f]
            out.add((v[0] + dx, v[1] + dy, v[2] + dz))
    return out
