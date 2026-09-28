#!/usr/bin/env python3
"""Verifier for Latveria Refinement v3.

Replays the three executed layers and then v3 in the voxel model (sim.World) and checks:

  command hygiene   every block-changing v3 command is guarded (keep / replace <old> /
                    execute if ... / carve of crag only); no gamerule, forceload, kill or
                    unguarded summon; every line fits the 256-character chat limit
  protection        the player's own Doombot factory room is bit-for-bit unchanged
  support           ladders, torches, signs, banners, levers, buttons, lanterns, doors, beds,
                    carpets and crops that v3 placed - or whose support v3 touched - stand on
                    or hang from something solid
  entities          no entity (old or new) ends up inside a solid block; v3 entities are all
                    tagged; the entity total is reported by type
  idempotency       replaying v3 a second time changes no block and adds no entity
  darkness          the Hall of Shadows stays at block light 0; the new rooms v3 carved have
                    no block-light-0 spawnable floor
  Golem Works       spawn attempts from every villager cell are simulated with the
                    LEGACY_IRON_GOLEM rules; every one must land on the flooded pad; the pod
                    partition is opaque except the one window; the kill shaft stays open

    python verify3.py         (needs numpy; exit code 0 = no structural problems)
"""
import collections
import copy
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sim
from core import chat_len

WIN = os.path.join(HERE, "..", "windows")
EXECUTED = ["latveria_commands.txt", "latveria_expansion_commands.txt", "latveria_lighting_commands.txt"]
V3 = os.path.join(WIN, "latveria_refinement_v3_commands.txt")
OUT = os.path.join(HERE, "..", "docs", "v3", "verification.json")

FACTORY = (-29, 0, -195, -5, 11, -167)
HALL = (232, 0, -46, 280, 34, -29)          # Hall of Shadows interior (lit area excluded by earlier layers)
NEW_ROOMS = {"Deep Cells": (-36, 2, -137, -16, 5, -125), "Doombot proving ground": (32, 2, -170, 47, 6, -152),
             "oriel study": (-33, 38, -169, -31, 42, -166), "observatory": (-15, 48, -165, -9, 51, -159)}
OPP = {"north": (0, 0, 1), "south": (0, 0, -1), "east": (-1, 0, 0), "west": (1, 0, 0)}
NONSUPPORT = ("air", "water", "lava", "fire", "light", "cave_air")


def props(s):
    if "[" not in s:
        return {}
    return dict(kv.split("=") for kv in s[s.index("[") + 1:-1].split(","))


def load_base():
    w = sim.World()
    for f in EXECUTED:
        w.load_file(os.path.join(WIN, f))
    return w


def v3_lines():
    out = []
    for line in open(V3, encoding="utf-8"):
        if line.startswith(("#", "!")):
            continue
        out.append(line.rstrip("\r\n").split("\t", 1)[1])
    return out


# ------------------------------------------------------------------ hygiene
GUARDED = [
    re.compile(r"^setblock \S+ \S+ \S+ .+ keep$"),
    re.compile(r"^fill (\S+ ){6}\S+ keep$"),
    re.compile(r"^fill (\S+ ){6}\S+ replace \S+$"),
    re.compile(r"^execute if block .* run setblock \S+ \S+ \S+ \S+ strict$"),
    re.compile(r"^execute unless entity @e\[(tag=lv3_[a-z0-9_]+|type=[a-z_]+,name=\"[^\"]+\")\] run summon "),
    re.compile(r"^execute unless items block \S+ \S+ \S+ container\.\d+ \* run item replace block "),
]
HARMLESS = ("tp @s ", "title @s ", "tag @e[tag=lv3_", "item replace entity @e[tag=lv3_", "data modify block ",
            "tp @e[type=")


def hygiene(lines, problems):
    stats = collections.Counter()
    longest = max(lines, key=chat_len)
    for c in lines:
        if chat_len(c) > 256:
            problems.append("too long for chat: " + c[:80])
        if re.match(r"^(gamerule|forceload|kill|clone|difficulty|weather|time |gamemode|effect )", c):
            problems.append("forbidden command: " + c[:80])
            continue
        if any(g.match(c.replace("  ", " ")) for g in GUARDED):
            kind = c.split(" ")[0] + (" keep" if c.endswith(" keep") else " replace" if " replace " in c else "")
            if c.startswith("execute unless entity"):
                kind = "guarded summon"
            elif c.startswith("execute unless items"):
                kind = "guarded container item"
            elif c.startswith("execute if block"):
                kind = "guarded two-part block"
            stats[kind] += 1
            continue
        if c.startswith(HARMLESS):
            stats[c.split(" ")[0] + " (harmless)"] += 1
            if c.startswith("data modify block") and "Book.components" not in c:
                problems.append("data modify outside a v3 lectern book: " + c[:80])
            continue
        problems.append("unguarded command: " + c[:100])
    return stats, longest


# ------------------------------------------------------------------ support
def support(w, changed, problems):
    idx = np.argwhere(changed)
    cells = set()
    for (i, j, k) in idx:
        for d in ((0, 0, 0), (1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            cells.add((i + d[0], j + d[1], k + d[2]))
    bad = collections.Counter()
    ex = {}

    def at(x, y, z):
        return w.get(x, y, z)

    def solid(s):
        return s.split("[", 1)[0] not in NONSUPPORT

    def full(s):
        nm = s.split("[", 1)[0]
        return solid(s) and not nm.endswith(("lantern", "_slab", "_stairs", "_fence", "_wall", "_pane", "bars", "chain",
                                             "_trapdoor", "_door", "_sign", "_banner", "ladder", "torch", "_carpet"))

    for (i, j, k) in cells:
        x, y, z = i + w.X0, j + w.Y0, k + w.Z0
        s = at(x, y, z)
        n = s.split("[", 1)[0]
        p = props(s)
        kind = None
        if n == "ladder" or n.endswith(("_wall_banner", "_wall_sign", "wall_torch")):
            dx, dy, dz = OPP[p["facing"]]
            if not solid(at(x + dx, y + dy, z + dz)):
                kind = n + " unsupported"
        elif n == "lever" or n.endswith("_button"):
            if p.get("face") == "wall":
                dx, dy, dz = OPP[p["facing"]]
                if not solid(at(x + dx, y + dy, z + dz)):
                    kind = "lever/button unsupported"
            elif p.get("face") == "floor" and not solid(at(x, y - 1, z)):
                kind = "lever/button unsupported"
        elif n in ("lantern", "soul_lantern", "copper_lantern"):
            if p.get("hanging") == "true":
                if not solid(at(x, y + 1, z)):
                    kind = "hanging lantern floating"
            elif not solid(at(x, y - 1, z)):
                kind = "lantern floating"
        elif n == "bell":
            at_ = p.get("attachment")
            up = at(x, y + 1, z)
            if at_ == "ceiling" and not (full(up) or up.split("[", 1)[0].endswith("_slab") and "type=top" not in up):
                kind = "bell unsupported"
            elif at_ == "floor" and not full(at(x, y - 1, z)):
                kind = "bell unsupported"
        elif n.endswith(("_skull", "_head")) and "wall" not in n or n in ("anvil", "chipped_anvil", "damaged_anvil",
                                                                          "decorated_pot", "flower_pot", "cauldron"):
            if not solid(at(x, y - 1, z)) and n not in ("anvil", "chipped_anvil", "damaged_anvil"):
                kind = "floor item floating"
        elif n in ("sand", "gravel", "red_sand") or n.endswith(("concrete_powder", "anvil")):
            if at(x, y - 1, z).split("[", 1)[0] in NONSUPPORT:
                kind = "gravity block over nothing"
        elif n in ("wheat", "carrots", "potatoes", "beetroots"):
            if at(x, y - 1, z).split("[")[0] != "farmland":
                kind = "crop not on farmland"
        elif n.endswith("_bed"):
            v = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[p["facing"]]
            if p["part"] == "foot":
                o = at(x + v[0], y, z + v[1])
                if not (o.split("[")[0] == n and props(o).get("part") == "head"):
                    kind = "bed missing head"
        elif n.endswith("_door"):
            if p["half"] == "lower":
                o = at(x, y + 1, z)
                if not (o.split("[")[0] == n and props(o).get("half") == "upper"):
                    kind = "door missing top"
                elif not solid(at(x, y - 1, z)):
                    kind = "door floating"
        elif n.endswith(("_carpet", "_pressure_plate", "_banner")) and "wall" not in n or n in (
                "torch", "soul_torch", "redstone_torch", "candle", "campfire", "soul_campfire", "repeater",
                "comparator", "redstone_wire", "rail", "powered_rail") or n.endswith("_candle") or n.startswith("potted_"):
            if not solid(at(x, y - 1, z)):
                kind = "floor item floating"
        elif n.endswith("_sign") and "wall" not in n and "hanging" not in n:
            if not solid(at(x, y - 1, z)):
                kind = "standing sign floating"
        if kind:
            bad[kind] += 1
            ex.setdefault(kind, []).append((x, y, z, s))
    for k, v in bad.items():
        problems.append("%s: %d  e.g. %s" % (k, v, ex[k][:3]))
    return len(cells)


# ------------------------------------------------------------------ entities
SOLID_OK = ("_slab", "_carpet", "_pressure_plate", "_button", "_trapdoor", "rail", "ladder", "torch",
            "_sign", "_banner", "_bed", "snow", "farmland", "dirt_path", "soul_sand", "_stairs")


def entities(w, problems):
    by = collections.Counter(e["type"] for e in w.entities)
    for e in w.entities:
        if e["type"] in ("glow_item_frame", "item_frame", "painting", "marker"):
            continue
        bx, by_, bz = int(e["x"] // 1), int(e["y"] // 1), int(e["z"] // 1)
        s = w.get(bx, by_, bz).split("[", 1)[0]
        if s not in NONSUPPORT and not s.endswith(SOLID_OK) and not (s in ("hopper", "chest", "iron_block", "water")):
            problems.append("entity inside a block: %s %s at %s in %s" % (e["type"], e["name"], (bx, by_, bz), s))
    return dict(by.most_common())


# ------------------------------------------------------------------ golem works
GOLEM_BELOW_BAD = ("glass", "stained_glass", "tinted_glass", "glass_pane", "sea_lantern", "glowstone", "leaves",
                   "ice", "beacon", "conduit", "tnt", "cactus", "cobweb", "daylight_detector")
NOT_SOLID_RENDER = ("air", "water", "lava", "hopper", "lever", "ladder", "wall_sign", "_sign", "_bed", "lantern",
                    "_slab", "_stairs", "chest", "iron_bars", "piston_head", "daylight_detector", "tinted_glass",
                    "glass", "_pane", "_trapdoor", "_door", "_fence", "_wall", "campfire", "carpet")


def solid_render(n):
    return not any(n == t or n.endswith(t) for t in NOT_SOLID_RENDER)


def golem_works(w, problems):
    rep = {}
    vill = [(x, 9, z) for x in range(251, 255) for z in (-90, -89)]
    landed = collections.Counter()
    bad = []
    for (vx, vy, vz) in vill:
        for dx in range(-8, 9):
            for dz in range(-8, 9):
                x, z = vx + dx, vz + dz
                above = w.name(x, vy + 6, z)
                spot = None
                for yb in range(vy + 5, vy - 8, -1):          # block below the candidate cell
                    below = w.name(x, yb, z)
                    ok_above = above in ("air", "water", "lava", "cave_air")
                    if ok_above and solid_render(below) and not any(below == t or below.endswith(t) for t in GOLEM_BELOW_BAD):
                        spot = (x, yb + 1, z)
                        break
                    above = below
                if spot is None:
                    landed["no spawn position"] += 1
                    continue
                # obstruction: feet cell may hold water; the two cells above must be free of fluid and collision
                sx, sy, sz = spot
                c1, c2 = w.name(sx, sy + 1, sz), w.name(sx, sy + 2, sz)
                if c1 not in ("air", "cave_air") or c2 not in ("air", "cave_air"):
                    landed["obstructed"] += 1
                    continue
                on_pad = 244 <= sx <= 261 and -98 <= sz <= -81 and sy == 5
                if on_pad:
                    landed["on the flooded pad"] += 1
                else:
                    landed["elsewhere"] += 1
                    bad.append(spot)
    rep["spawn attempts (villager cell x offset)"] = dict(landed)
    if bad:
        problems.append("Golem Works: %d spawn positions off the pad, e.g. %s" % (len(bad), sorted(set(bad))[:6]))
    # pad flooded: water sources along the rim, floor flush at y 4
    dry = [(x, z) for x in range(244, 262) for z in range(-98, -80) if w.name(x, 4, z) != "stone_bricks"
           and not (252 <= x <= 253 and -90 <= z <= -89)]
    if dry:
        problems.append("Golem Works: pad floor not flush at %s" % dry[:5])
    src = sum(1 for x in range(244, 262) for z in range(-98, -80)
              if (x in (244, 261) or z in (-98, -81)) and w.name(x, 5, z) == "water")
    rep["rim water sources"] = src
    if src < 68:
        problems.append("Golem Works: only %d of 68 rim water sources" % src)
    # water reach: every pad cell within 7 of a source along x or z
    far = [(x, z) for x in range(244, 262) for z in range(-98, -80)
           if min(x - 244, 261 - x, z + 98, -81 - z) > 7 and not (252 <= x <= 253 and -90 <= z <= -89)]
    rep["pad cells beyond water reach"] = len(far)
    # shaft open, lava blade, hoppers, chest
    for y in range(1, 5):
        for x in (252, 253):
            for z in (-90, -89):
                n = w.name(x, y, z)
                if y == 2 and n != "lava" or y in (3, 4) and n != "air" or y == 1 and n != "oak_wall_sign":
                    problems.append("Golem Works: shaft cell %s is %s" % ((x, y, z), n))
    # partition x=255 between villagers (x<=254) and the zombie (x=256): opaque except the window
    part = {(y, z): w.name(255, y, z) for y in (9, 10, 11) for z in (-90, -89)}
    window = [k for k, n in part.items() if n == "air"]
    see_through = [k for k, n in part.items() if n in ("glass", "tinted_glass") or n.endswith("_pane")]
    rep["partition"] = {"%d,%d" % k: n for k, n in part.items()}
    if window != [(10, -89)] or see_through:
        problems.append("Golem Works: partition wrong (window %s, glass %s)" % (window, see_through))
    for (p, n) in (((255, 12, -89), "sticky_piston"), ((255, 11, -89), "stone_bricks"), ((255, 13, -89), "daylight_detector"),
                   ((256, 12, -89), "lever")):
        if w.name(*p) != n:
            problems.append("Golem Works: %s should be %s, is %s" % (p, n, w.name(*p)))
    floors = {w.name(x, 8, z) for x in range(251, 255) for z in (-90, -89)} | {w.name(256, 8, -89)}
    rep["pod floors"] = sorted(floors)
    if floors != {"glass"}:
        problems.append("Golem Works: pod floors %s (must be glass)" % floors)
    # villagers and zombie present, beds
    names = collections.Counter(e["name"] for e in w.entities if abs(e["x"] - 253) < 6 and abs(e["z"] + 89) < 6)
    rep["crew"] = dict(names)
    beds = sum(1 for x in range(250, 256) for z in (-90, -89) if w.get(x, 9, z).endswith("part=foot]")
               or "part=foot" in w.get(x, 9, z))
    rep["beds"] = beds
    if beds < 3:
        problems.append("Golem Works: %d beds" % beds)
    others = [e for e in w.entities if e["type"] == "iron_golem" and abs(e["x"] - 252) < 40 and abs(e["z"] + 90) < 40]
    rep["iron golems within 40 blocks"] = len(others)
    return rep


# ------------------------------------------------------------------ darkness
def darkness(w, before_world, problems):
    rep = {}
    L0, _, (ox, oy, oz) = before_world.block_light(HALL)
    L1, _, _ = w.block_light(HALL)
    x1, y1, z1, x2, y2, z2 = HALL
    sl = (slice(x1 - ox, x2 - ox + 1), slice(y1 - oy, y2 - oy + 1), slice(z1 - oz, z2 - oz + 1))
    dark0 = L0[sl] == 0
    lit_now = int(np.count_nonzero(dark0 & (L1[sl] > 0)))
    rep["Hall of Shadows dark cells before"] = int(dark0.sum())
    rep["Hall of Shadows dark cells lit by v3"] = lit_now
    if lit_now:
        problems.append("v3 lights %d cells of the Hall of Shadows" % lit_now)
    for nm, box in NEW_ROOMS.items():
        dark = w.dark_spawn_cells(box)
        rep["dark spawnable cells in " + nm] = len(dark)
        if dark:
            problems.append("%s: %d dark spawnable cells, e.g. %s" % (nm, len(dark), dark[:4]))
    return rep


def new_dark(w, before_world, changed, problems):
    """Every 32x32 column tile v3 touched: spawnable block-light-0 floor cells that did not exist before."""
    idx = np.argwhere(changed)
    tiles = {}
    for (i, j, k) in idx:
        key = ((i + w.X0) // 32, (k + w.Z0) // 32)
        y = j + w.Y0
        lo, hi = tiles.get(key, (y, y))
        tiles[key] = (min(lo, y), max(hi, y))
    total = 0
    ex = []
    for (tx, tz), (ylo, yhi) in tiles.items():
        box = (tx * 32, ylo - 2, tz * 32, tx * 32 + 31, yhi + 3, tz * 32 + 31)
        before = set(before_world.dark_spawn_cells(box))
        after = set(w.dark_spawn_cells(box))
        new = after - before
        total += len(new)
        ex += sorted(new)[:3]
    if total:
        problems.append("%d new dark spawnable cells where v3 built, e.g. %s" % (total, ex[:6]))
    return {"tiles_checked": len(tiles), "new_dark_spawnable_cells": total}


def mechanisms(w, problems):
    """State checks of the redstone and survival mechanisms v3 builds."""
    rep = {}

    def want(p, name, what):
        n = w.get(*p)
        if not (n == name or n.split("[", 1)[0] == name):
            problems.append("%s: %s should be %s, is %s" % (what, p, name, n))

    # throne hatch
    want((6, 14, -194), "sticky_piston[facing=west,extended=true]", "throne hatch")
    want((5, 14, -194), "piston_head[facing=west,type=sticky,short=false]", "throne hatch")
    want((4, 14, -194), "polished_deepslate", "throne hatch")
    want((6, 16, -194), "lever[face=floor,facing=west,powered=true]", "throne hatch")
    for y in range(2, 14):
        want((4, y, -194), "ladder", "throne shaft")
    # time platform chain: repeaters (input west) at x -3, -2 and every even x to 22; wall blocks between
    for x in [-3, -2] + list(range(0, 23, 2)):
        want((x, 2, -195), "repeater[delay=4,facing=west,locked=false,powered=false]" if False else "repeater", "time chain")
        if "facing=west" not in w.get(x, 2, -195):
            problems.append("time chain: repeater at x=%d does not take input from the west" % x)
    for x in range(-1, 24, 2):
        n = w.name(x, 2, -195)
        if n in ("air", "repeater"):
            problems.append("time chain: wall block missing at x=%d" % x)
    rep["time chain lamps"] = sum(1 for x in range(-1, 24, 4) if w.name(x, 2, -194) == "redstone_lamp")
    # nursery: exit one block high, pit two deep
    want((-44, 0, 145), "air", "nursery exit")
    want((-44, 1, 145), "bricks", "nursery exit lintel")
    rep["children's yard floor y"] = -3 if w.name(-40, -3, 146) == "grass_block" and w.name(-43, -1, 145) == "air" else None
    if rep["children's yard floor y"] is None or w.name(-43, -2, 145) != "air":
        problems.append("nursery: the drop below the exit is not two clear blocks")
    # sorting office modules
    ok = 0
    for i in range(6):
        x0, zs = 205 + 2 * i, -104
        cells = {(x0, 2, zs): "hopper", (x0, 1, zs): "hopper", (x0, 0, zs): "hopper", (x0, -1, zs): "stone_bricks",
                 (x0, 0, zs - 1): "chest", (x0 + 1, 0, zs - 1): "chest", (x0, 1, zs + 1): "comparator",
                 (x0, 1, zs + 2): "redstone_wire", (x0, 1, zs + 3): "redstone_wire", (x0, 1, zs + 4): "repeater",
                 (x0, 1, zs + 5): "stone_bricks", (x0, 0, zs + 5): "glass", (x0, 1, zs + 6): "redstone_wall_torch",
                 (x0, 0, zs + 6): "redstone_wire"}
        for z in range(zs + 1, zs + 6):
            cells[(x0, -1, z)] = "redstone_wire"
        bad = [(p, n, w.name(*p)) for p, n in cells.items() if w.name(*p) != n]
        if bad:
            problems.append("sorter module %d: %s" % (i, bad[:3]))
        else:
            ok += 1
        # nothing but the stream hopper may sit above a filter's neighbours (no stray containers under the stream)
        if i < 5 and w.name(x0 + 1, 1, zs) in ("hopper", "chest", "barrel"):
            problems.append("sorter: container under a plain stream hopper at x=%d" % (x0 + 1))
    rep["sorter modules complete"] = ok
    for x in range(204, 217):
        if w.get(x, 2, -104) != "hopper[facing=east]":
            problems.append("sorter stream hopper at x=%d is %s" % (x, w.get(x, 2, -104)))
    want((217, 2, -104), "hopper[facing=down]", "sorter overflow")
    want((217, 1, -104), "hopper[facing=down]", "sorter overflow")
    want((217, 0, -104), "chest", "sorter overflow chest")
    return rep


def main():
    problems = []
    base = load_base()
    before_world = load_base()
    before = base.W.copy()
    n_ent0 = len(base.entities)
    lines = v3_lines()
    w = base
    w.layer = "v3"
    for c in lines:
        w.apply(c)
    after = w.W.copy()
    ents_after = copy.deepcopy(w.entities)
    # idempotency: replay the whole layer again
    for c in lines:
        w.apply(c)
    idem_blocks = int(np.count_nonzero(w.W != after))
    idem_ents = len(w.entities) - len(ents_after)
    if idem_blocks or idem_ents:
        problems.append("not idempotent: second replay changes %d blocks, adds %d entities" % (idem_blocks, idem_ents))
    changed = before != after
    fx = w._sl(*FACTORY)
    if np.count_nonzero(changed[fx]):
        problems.append("the player's Doombot factory room was changed (%d cells)" % np.count_nonzero(changed[fx]))
    cmd_stats, longest = hygiene(lines, problems)
    checked = support(w, changed, problems)
    ent = entities(w, problems)
    untagged = [e for e in w.entities if e["layer"] == "v3" and not e["tag"] and not e["name"]]
    if untagged:
        problems.append("%d v3 entities without tag or name" % len(untagged))
    gw = golem_works(w, problems)
    dk = darkness(w, before_world, problems)
    nd = new_dark(w, before_world, changed, problems)
    mech = mechanisms(w, problems)
    idx = np.argwhere(changed)
    lo, hi = idx.min(axis=0), idx.max(axis=0)
    ys = [float(v) for c in lines for v in re.findall(r"\$y\((-?[0-9.]+)\)", c)]
    rep = {
        "structural_problems": problems,
        "commands": len(lines),
        "command_kinds": dict(cmd_stats),
        "longest_command_chars": chat_len(longest),
        "longest_command": longest,
        "cells_changed_by_v3": int(changed.sum()),
        "changed_bounds_rel": [int(lo[0] + w.X0), int(lo[1] + w.Y0), int(lo[2] + w.Z0),
                               int(hi[0] + w.X0), int(hi[1] + w.Y0), int(hi[2] + w.Z0)],
        "y_range_rel": [min(ys), max(ys)],
        "non_air_blocks_before": int(np.count_nonzero(before)),
        "non_air_blocks_after": int(np.count_nonzero(after)),
        "entities_before": n_ent0,
        "entities_after": len(ents_after),
        "entities_by_type_after": ent,
        "v3_entities": collections.Counter(e["type"] for e in ents_after if e["layer"] == "v3"),
        "support_cells_checked": checked,
        "idempotency": {"blocks_changed_on_second_replay": idem_blocks, "entities_added_on_second_replay": idem_ents},
        "golem_works": gw,
        "darkness": dk,
        "new_dark_cells": nd,
        "mechanisms": mech,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(rep, f, indent=1, default=str)
    for p in problems:
        print("PROBLEM", p)
    print(json.dumps({k: rep[k] for k in ("commands", "cells_changed_by_v3", "entities_before", "entities_after",
                                           "longest_command_chars", "idempotency", "golem_works", "darkness",
                                           "new_dark_cells", "mechanisms")},
                     indent=1, default=str))
    print("structural problems: %d" % len(problems))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
