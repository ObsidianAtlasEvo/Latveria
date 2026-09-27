"""Voxel statue of Victor von Doom (hooded, masked, cloaked, in armour).

The figure is modelled on a 16x32 "pixel" humanoid, the same proportions as
a Minecraft player model, and can be built at any scale.  At scale 1 it is 32
blocks tall.  Local frame: statue faces +z (south), feet centred on x=0,
standing at y=0.
"""
import math

MASK = "iron_block"
METAL = "iron_block"
METAL_DARK = "light_gray_concrete"
JOINT = "polished_andesite"
TUNIC = "green_concrete"
TUNIC_TRIM = "green_terracotta"
CLOAK = "green_wool"
HOOD = "green_concrete"
BELT = "black_concrete"
BUCKLE = "gold_block"
SLIT = "black_concrete"
EYES = "lime_stained_glass"


def build_statue(b, x0, y0, z0, scale=1.0, rot=0, eyes_glow=True):
    s = scale

    def box(px1, py1, pz1, px2, py2, pz2, block):
        # pixel box [px1..px2] inclusive -> block box
        bx1 = math.floor(px1 * s)
        bx2 = math.floor((px2 + 1) * s) - 1
        by1 = math.floor(py1 * s)
        by2 = math.floor((py2 + 1) * s) - 1
        bz1 = math.floor(pz1 * s)
        bz2 = math.floor((pz2 + 1) * s) - 1
        bx2 = max(bx2, bx1); by2 = max(by2, by1); bz2 = max(bz2, bz1)
        b.fill(bx1, by1, bz1, bx2, by2, bz2, block)

    with b.frame(x0, y0, z0, rot):
        # ---- cloak (behind the body, flaring to the ground) ----
        box(-7, 2, -3, 6, 23, -3, CLOAK)
        box(-8, 0, -4, 7, 3, -3, CLOAK)
        box(-8, 4, -3, 7, 10, -3, CLOAK)
        box(-9, 0, -3, -8, 12, -2, CLOAK)          # cloak edges wrap forward
        box(8, 0, -3, 8, 12, -2, CLOAK)
        # ---- legs: armoured greaves, tunic skirt above ----
        box(-4, 0, -2, -1, 5, 1, METAL)
        box(0, 0, -2, 3, 5, 1, METAL)
        box(-5, 0, -3, -1, 1, 2, METAL_DARK)      # sabatons
        box(0, 0, -3, 4, 1, 2, METAL_DARK)
        box(-5, 6, -3, 4, 11, 2, TUNIC)            # skirt flares out
        box(-5, 6, 2, 4, 6, 2, TUNIC_TRIM)
        box(-1, 6, 2, 0, 11, 2, TUNIC_TRIM)        # front split of the tunic
        # ---- torso ----
        box(-4, 12, -2, 3, 23, 1, TUNIC)
        box(-4, 12, -2, 3, 13, 1, BELT)
        box(-1, 12, 2, 0, 13, 2, BUCKLE)          # belt buckle / pouch
        box(-4, 12, 2, -3, 13, 2, BELT)
        box(2, 12, 2, 3, 13, 2, BELT)
        box(-3, 19, 2, 2, 22, 2, METAL)            # armoured chest plate
        box(-1, 20, 2, 0, 21, 2, METAL_DARK)
        # ---- arms: armoured, gauntlets, hood drapes over shoulders ----
        box(-8, 12, -2, -5, 23, 1, METAL)
        box(4, 12, -2, 7, 23, 1, METAL)
        box(-8, 12, -2, -5, 15, 1, METAL_DARK)     # gauntlets
        box(4, 12, -2, 7, 15, 1, METAL_DARK)
        box(-8, 16, -2, -5, 16, 1, JOINT)
        box(4, 16, -2, 7, 16, 1, JOINT)
        box(-8, 20, -3, -5, 23, 2, HOOD)           # cowl over shoulders
        box(4, 20, -3, 7, 23, 2, HOOD)
        # ---- head: green hood around an iron mask ----
        box(-5, 24, -5, 4, 32, 3, HOOD)
        box(-4, 24, 3, 3, 30, 4, MASK)
        box(-5, 31, 3, 4, 32, 4, HOOD)             # hood brim over the mask
        box(-5, 24, 3, -5, 32, 4, HOOD)
        box(4, 24, 3, 4, 32, 4, HOOD)
        # eye slits and grille mouth
        box(-3, 28, 4, -2, 28, 4, EYES if eyes_glow else SLIT)
        box(1, 28, 4, 2, 28, 4, EYES if eyes_glow else SLIT)
        box(-2, 25, 4, 1, 25, 4, SLIT)
        box(-1, 26, 4, 0, 26, 4, METAL_DARK)        # nose ridge
        box(-4, 27, 4, -4, 29, 4, METAL_DARK)      # rivets / cheek plates
        box(3, 27, 4, 3, 29, 4, METAL_DARK)
        if eyes_glow and s >= 1:
            # a light source behind each eye makes them glow green at night
            box(-3, 28, 3, -2, 28, 3, "verdant_froglight")
            box(1, 28, 3, 2, 28, 3, "verdant_froglight")


def statue_height(scale):
    return math.floor(33 * scale)
