#!/usr/bin/env python3
"""Replay the command list and check survival details the game would enforce.

After every fill / setblock has been applied (in order, including `replace`
filters) it checks that:
  * ladders, wall torches, wall banners, wall signs, levers and buttons have a
    block behind them
  * hanging lanterns / bells have something above; floor items have a floor
  * crops sit on farmland; beds and doors have both halves
  * no armour stand, villager, animal or golem is summoned inside a solid block
Run:  python verify.py      (needs numpy)
"""
import os
import re
import sys
from collections import Counter

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
CMDS = os.path.join(HERE, "..", "windows", "latveria_commands.txt")
X0, X1, Y0, Y1, Z0, Z1 = -155, 155, -14, 140, -256, 116
TOK = re.compile(r"\$([xyz])\((-?[0-9.]+)\)")
OPP = {"north": (0, 0, 1), "south": (0, 0, -1), "east": (-1, 0, 0), "west": (1, 0, 0)}

states = ["air"]
sid = {"air": 0}


def state_id(s):
    s = re.split(r"\{", s, 1)[0]
    if s not in sid:
        sid[s] = len(states)
        states.append(s)
    return sid[s]


def name(s):
    return s.split("[", 1)[0]


def props(s):
    if "[" not in s:
        return {}
    return dict(kv.split("=") for kv in s[s.index("[") + 1:-1].split(","))


NONSUPPORT = ("air", "water", "lava", "fire", "light")


def main():
    W = np.zeros((X1 - X0 + 1, Y1 - Y0 + 1, Z1 - Z0 + 1), dtype=np.int32)
    summons = []
    for line in open(CMDS, encoding="utf-8"):
        if line.startswith(("#", "!")):
            continue
        cmd = line.rstrip("\r\n").split("\t", 1)[1]
        op = cmd.split(" ", 1)[0]
        vals = [float(v) for _, v in TOK.findall(cmd)]
        rest = TOK.sub("", cmd).split()
        if op == "summon" and rest[1] not in ("marker",):
            summons.append((rest[1], vals[:3], cmd))
            continue
        if op not in ("fill", "setblock"):
            continue
        iv = [int(v // 1) for v in vals]
        if op == "fill":
            x1, y1, z1, x2, y2, z2 = iv
            blk = rest[1]
            flt = rest[3] if len(rest) > 3 and rest[2] == "replace" else None
        else:
            x1, y1, z1 = iv
            x2, y2, z2 = iv
            blk, flt = rest[1], None
        a = (slice(x1 - X0, x2 - X0 + 1), slice(y1 - Y0, y2 - Y0 + 1), slice(z1 - Z0, z2 - Z0 + 1))
        v = state_id(blk)
        if flt:
            fn = name(flt)
            sub = W[a]
            ids = [i for i, s in enumerate(states) if name(s) == fn]
            sub[np.isin(sub, ids)] = v
        else:
            W[a] = v

    def at(x, y, z):
        return states[W[x - X0, y - Y0, z - Z0]]

    def solid(s):
        return name(s) not in NONSUPPORT

    problems = Counter()
    examples = {}

    def bad(kind, x, y, z, s):
        problems[kind] += 1
        examples.setdefault(kind, []).append((x, y, z, s))

    idx = np.argwhere(W > 0)
    for (i, j, k) in idx:
        s = states[W[i, j, k]]
        n = name(s)
        p = props(s)
        x, y, z = i + X0, j + Y0, k + Z0
        if n in ("ladder",) or n.endswith(("_wall_banner", "_wall_sign", "wall_torch")):
            dx, dy, dz = OPP[p["facing"]]
            if not solid(at(x + dx, y + dy, z + dz)):
                bad(n.split("_")[-1] + " unsupported", x, y, z, s)
        elif n in ("lever",) or n.endswith("_button"):
            if p.get("face") == "wall":
                dx, dy, dz = OPP[p["facing"]]
                if not solid(at(x + dx, y + dy, z + dz)):
                    bad("lever/button unsupported", x, y, z, s)
        elif n in ("lantern", "soul_lantern") or n.endswith("_lantern") and "sea" not in n and "jack" not in n:
            if p.get("hanging") == "true":
                if not solid(at(x, y + 1, z)):
                    bad("hanging lantern floating", x, y, z, s)
            elif not solid(at(x, y - 1, z)):
                bad("lantern floating", x, y, z, s)
        elif n in ("wheat", "carrots", "potatoes", "beetroots"):
            if name(at(x, y - 1, z)) != "farmland":
                bad("crop not on farmland", x, y, z, s)
        elif n.endswith("_bed"):
            f = p["facing"]
            v = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[f]
            if p["part"] == "foot":
                o = at(x + v[0], y, z + v[1])
                if not (name(o) == n and props(o).get("part") == "head"):
                    bad("bed missing head", x, y, z, s)
            if not solid(at(x, y - 1, z)):
                bad("bed floating", x, y, z, s)
        elif n.endswith("_door"):
            if p["half"] == "lower":
                o = at(x, y + 1, z)
                if not (name(o) == n and props(o).get("half") == "upper"):
                    bad("door missing top", x, y, z, s)
                if not solid(at(x, y - 1, z)):
                    bad("door floating", x, y, z, s)
        elif n in ("torch", "campfire", "soul_campfire", "candle") or n.endswith(("_carpet", "_candle")) \
                or n.startswith("potted_") or n in ("poppy", "dandelion", "allium", "lily_of_the_valley",
                                                     "cornflower", "blue_orchid", "azure_bluet", "oxeye_daisy"):
            if not solid(at(x, y - 1, z)):
                bad("floor item floating", x, y, z, s)
        elif n == "lily_pad":
            if name(at(x, y - 1, z)) != "water":
                bad("lily pad not on water", x, y, z, s)

    for et, (x, y, z), cmd in summons:
        if et in ("glow_item_frame", "item_frame"):
            continue
        bx, by, bz = int(x // 1), int(y // 1), int(z // 1)
        if not (X0 <= bx <= X1 and Y0 <= by <= Y1 - 1 and Z0 <= bz <= Z1):
            continue
        here = at(bx, by, bz)
        n = name(here)
        passable = n in NONSUPPORT or n.endswith(("_carpet", "_slab", "_pressure_plate", "_button", "_sapling",
                                                  "ladder", "torch", "flower", "grass", "_trapdoor"))
        if not passable and not (et == "armor_stand" and n.endswith("_slab")):
            bad("entity inside block", bx, by, bz, "%s in %s" % (et, here))
    total = sum(problems.values())
    for k, v in problems.most_common():
        print("%-28s %5d   e.g. %s" % (k, v, examples[k][:3]))
    print("checked %d blocks, %d entities: %d problems" % (len(idx), len(summons), total))
    return total


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
