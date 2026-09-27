"""Site preparation: clearing, levelling, the castle crag, moat and grand stair."""
import math
import random

from layout import *


def clear_site(b):
    b.section("clear", "Clearing the land")
    b.comment("remove everything above the build level")
    b.air(X_MIN, 0, Z_MIN, X_MAX, CLEAR_TOP, Z_MAX)
    x1, x2, z1, z2, yt = CASTLE_CLEAR
    b.air(x1, CLEAR_TOP + 1, z1, x2, yt, z2)
    b.section("ground", "Levelling the valley")
    b.fill(X_MIN, -10, Z_MIN, X_MAX, -5, Z_MAX, "stone")
    b.fill(X_MIN, -4, Z_MIN, X_MAX, -2, Z_MAX, "dirt")
    b.fill(X_MIN, -1, Z_MIN, X_MAX, -1, Z_MAX, "grass_block")


def _level_rect(y):
    e = (11 - y) * CRAG_STEP
    x1, x2, z1, z2 = PLAT
    return x1 - e, x2 + e, z1 - e, z2 + e, 4 + e * 0.8


def _row_extent(y, z, rng_cache):
    x1, x2, z1, z2, rc = _level_rect(y)
    if z < z1 or z > z2:
        return None
    dist = min(z - z1, z2 - z)
    inset = 0
    if dist < rc:
        inset = int(round(rc - math.sqrt(max(0.0, rc * rc - (rc - dist) ** 2))))
    key = (y, z // 3)
    if key not in rng_cache:
        r = random.Random(hash(key) & 0xFFFF)
        rng_cache[key] = (r.randint(-1, 1), r.randint(-1, 1))
    j1, j2 = rng_cache[key]
    if y == 11:
        j1 = j2 = 0
    a = max(X_MIN, x1 + inset + j1)
    bb = min(X_MAX, x2 - inset + j2)
    return a, bb


def build_crag(b):
    b.section("crag", "Raising the crag of Castle Doom")
    rng = random.Random(1961)
    cache = {}
    rock = ["stone", "stone", "stone", "andesite", "tuff", "stone", "deepslate", "cobbled_deepslate"]
    extents = {}
    for y in range(0, 12):
        x1, x2, z1, z2, _ = _level_rect(y)
        for z in range(max(Z_MIN, z1), min(Z_MAX, z2) + 1):
            ext = _row_extent(y, z, cache)
            if ext is None:
                continue
            extents[(y, z)] = ext
    # fill rock in long runs, choosing strata per 4-row band
    for y in range(0, 12):
        zs = sorted(z for (yy, z) in extents if yy == y)
        for z in zs:
            a, c_ = extents[(y, z)]
            mat = rock[(hash((y // 2, z // 5)) & 0xFFFF) % len(rock)] if y < 11 else "stone"
            b.fill(a, y, z, c_, y, z, mat)
    # dress exposed step tops with turf, moss and scree; plant pines
    b.section("crag_dress", "Dressing the crag")
    trees = []
    for y in range(0, 11):
        zs = sorted(z for (yy, z) in extents if yy == y)
        for z in zs:
            a, c_ = extents[(y, z)]
            up = extents.get((y + 1, z))
            segs = [(a, c_)] if up is None else [(a, up[0] - 1), (up[1] + 1, c_)]
            for s1, s2 in segs:
                if s2 < s1:
                    continue
                # leave the grand stair corridor alone
                if z > STAIR_Z1 - 1 and s1 <= STAIR_X + 3 and s2 >= -STAIR_X - 3:
                    continue
                roll = rng.random()
                top = "grass_block" if roll < 0.55 else "moss_block" if roll < 0.63 else \
                      "coarse_dirt" if roll < 0.72 else None
                if top:
                    b.fill(s1, y, z, s2, y, z, top)
                    if top in ("grass_block", "moss_block") and s2 - s1 >= 2 and rng.random() < 0.05:
                        trees.append((rng.randint(s1, s2), y + 1, z))
    for (x, y, z) in trees[:70]:
        b.feature(rng.choice(["spruce", "pine", "spruce", "birch"]), x, y, z)
    # plateau surface
    x1, x2, z1, z2 = PLAT
    b.fill(x1, 11, z1, x2, 11, z2, "grass_block")
    b.fill(x1, 8, z1, x2, 10, z2, "dirt")


def build_moat(b):
    b.section("moat", "Cutting the moat")
    ox1, ox2, oz1, oz2 = MOAT_OUT
    ix1, ix2, iz1, iz2 = MOAT_IN
    b.fill(ox1, 5, oz1, ox2, 11, oz2, "stone_bricks")
    b.fill(ox1 + 1, 6, oz1 + 1, ox2 - 1, 10, oz2 - 1, "water")
    b.air(ox1 + 1, 11, oz1 + 1, ox2 - 1, 11, oz2 - 1)
    # restore the island inside the moat
    b.fill(ix1, 5, iz1, ix2, 10, iz2, "stone")
    b.fill(ix1 + 1, 8, iz1 + 1, ix2 - 1, 10, iz2 - 1, "dirt")
    b.fill(ix1, 11, iz1, ix2, 11, iz2, "stone_bricks")
    b.fill(ix1 + 1, 11, iz1 + 1, ix2 - 1, 11, iz2 - 1, "grass_block")
    # moss and lily pads
    rng = random.Random(7)
    for _ in range(60):
        side = rng.randint(0, 3)
        if side == 0:
            x, z = rng.randint(ox1 + 1, ox2 - 1), rng.randint(oz1 + 1, iz1 - 1)
        elif side == 1:
            x, z = rng.randint(ox1 + 1, ox2 - 1), rng.randint(iz2 + 1, oz2 - 1)
        elif side == 2:
            x, z = rng.randint(ox1 + 1, ix1 - 1), rng.randint(oz1 + 1, oz2 - 1)
        else:
            x, z = rng.randint(ix2 + 1, ox2 - 1), rng.randint(oz1 + 1, oz2 - 1)
        if -5 <= x <= 5 and z > iz2:
            continue
        b.set(x, 11, z, "lily_pad")
    # plateau rim wall with lanterns (a low parapet on the crag edge)
    px1, px2, pz1, pz2 = PLAT
    for (a, c_, zz) in [(px1, px2, pz1), (px1, px2, pz2)]:
        b.fill(a, 12, zz, c_, 12, zz, "stone_brick_wall")
    b.fill(px1, 12, pz1 + 1, px1, 12, pz2 - 1, "stone_brick_wall")
    b.fill(px2, 12, pz1 + 1, px2, 12, pz2 - 1, "stone_brick_wall")
    b.air(-STAIR_X, 12, pz2, STAIR_X, 12, pz2)
    for x in range(px1, px2 + 1, 10):
        for zz in (pz1, pz2):
            if abs(x) > STAIR_X:
                b.set(x, 12, zz, "stone_bricks")
                b.set(x, 13, zz, "lantern")
    for z in range(pz1, pz2 + 1, 10):
        for xx in (px1, px2):
            b.set(xx, 12, z, "stone_bricks")
            b.set(xx, 13, z, "lantern")


def build_grand_stair(b):
    """A 15-wide slab ramp climbing the crag from the town to the drawbridge."""
    b.section("grand_stair", "The Grand Stair of Doom")
    W = STAIR_X
    n = STAIR_Z2 - STAIR_Z1
    b.air(-W - 1, 0, STAIR_Z1, W + 1, 30, STAIR_Z2)
    for j in range(0, n + 1):
        z = STAIR_Z1 + j
        if j % 2 == 0:
            top = 11 - j // 2
            b.fill(-W, -3, z, W, top, z, "stone_bricks")
            b.fill(-2, top, z, 2, top, z, "polished_deepslate")
        else:
            top = 11 - (j - 1) // 2
            b.fill(-W, -3, z, W, top - 1, z, "stone_bricks")
            b.fill(-W, top, z, W, top, z, "stone_brick_slab[type=bottom]")
            b.fill(-2, top, z, 2, top, z, "polished_deepslate_slab[type=bottom]")
        # side walls
        base = 11 - j // 2
        for sx in (-W - 1, W + 1):
            b.fill(sx, -3, z, sx, base + 1, z, "stone_bricks")
            b.set(sx, base + 2, z, "stone_brick_wall")
    # lamp pillars and Doom's banners every 6 blocks
    for j in range(0, n + 1, 6):
        z = STAIR_Z1 + j
        base = 11 - j // 2
        for sx in (-W - 1, W + 1):
            b.fill(sx, base + 2, z, sx, base + 4, z, "polished_deepslate")
            b.set(sx, base + 5, z, "chiseled_stone_bricks")
            b.set(sx, base + 6, z, "lantern")
            face = "west" if sx > 0 else "east"
            b.set(sx - (1 if sx > 0 else -1), base + 4, z,
                  "green_wall_banner[facing=%s]%s" % (face, doom_banner()))
    # flanking guardian plinths at the foot of the stair
    for sx in (-W - 4, W + 4):
        b.fill(sx - 1, -1, STAIR_Z2 - 3, sx + 1, 1, STAIR_Z2 - 1, "polished_deepslate")
        b.fill(sx - 1, 2, STAIR_Z2 - 3, sx + 1, 2, STAIR_Z2 - 1, "deepslate_tile_slab[type=bottom]")
        b.set(sx, 2, STAIR_Z2 - 2, "polished_deepslate")
        b.set(sx, 3, STAIR_Z2 - 2, "polished_blackstone_wall")
        b.set(sx, 4, STAIR_Z2 - 2, "lantern")


def doom_banner(kind="doom"):
    """Doom's heraldry: an iron mask sigil on green, bordered in black."""
    from core import banner
    if kind == "doom":
        pats = [("rhombus", "light_gray"), ("stripe_middle", "black"), ("circle", "light_gray"),
                ("border", "black")]
    elif kind == "latveria":
        # national colours: green over black with an iron chevron
        pats = [("half_horizontal_bottom", "black"), ("triangle_top", "gray"), ("border", "black")]
    else:
        pats = [("stripe_left", "black"), ("stripe_right", "black")]
    return banner(pats)
