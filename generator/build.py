#!/usr/bin/env python3
"""Generate the Latveria build as a chat-command script for the Windows sender.

    python build.py            -> ../windows/latveria_commands.txt

Line format of the command file (read by Build-Latveria.ps1):
    <extra_wait_ms><TAB><command without the leading slash>
    !section<TAB><title>          progress heading (not sent)
    !wait<TAB><ms><TAB><note>     pause the sender (e.g. while chunks load)
Coordinates are written as $x(dx) $y(dy) $z(dz) offsets from the centre block.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core import Builder, pos, cx, cy, cz, tc, GenError, chat_len, CHAT_LIMIT
from layout import *
import terrain
import castle
import keep
import village

OUT = os.path.join(HERE, "..", "windows", "latveria_commands.txt")

HOSTILE = ["zombie", "skeleton", "creeper", "spider", "cave_spider", "enderman", "witch", "slime",
           "husk", "stray", "drowned", "phantom", "bogged", "zombie_villager", "pillager"]

QUADS = [(X_MIN, Z_MIN, -1, -71), (0, Z_MIN, X_MAX, -71), (X_MIN, -70, -1, Z_MAX), (0, -70, X_MAX, Z_MAX)]
PLATFORM = (0, 80, 40)


def box_sel(x1, y1, z1, x2, y2, z2):
    return "x=%s,y=%s,z=%s,dx=%d,dy=%d,dz=%d" % (cx(x1)[0:], cy(y1), cz(z1), x2 - x1, y2 - y1, z2 - z1)


def setup(b):
    b.section("setup", "Preparing the site")
    b.raw("gamerule send_command_feedback false")
    b.raw("gamerule log_admin_commands false")
    b.raw("gamerule spawn_mobs false")
    b.raw("effect give @s minecraft:saturation infinite 0 true")
    px, py, pz = PLATFORM
    b.fill(px - 4, py, pz - 4, px + 4, py, pz + 4, "black_stained_glass")
    b.walls(px - 4, py + 1, pz - 4, px + 4, py + 1, pz + 4, "glass")
    b.set(px, py + 1, pz, "lantern")
    b.raw("tp @s %s 180 25" % pos(px + 0.5, py + 1, pz + 2.5))
    for (x1, z1, x2, z2) in QUADS:
        b.raw("forceload add %s %s %s %s" % (cx(x1), cz(z1), cx(x2), cz(z2)))
    b.wait(60000, "letting the building site's chunks load")
    b.raw("kill @e[type=!player,%s]" % box_sel(X_MIN, -12, Z_MIN, X_MAX, 140, Z_MAX))


def finale(b):
    b.section("population", "Bringing Doomstadt to life")
    for cmd in b.later:
        b.raw(cmd, 30)
    golem = '{CustomName:{text:"Doombot",color:"dark_green"},PersistenceRequired:1b}'
    for (x, y, z) in ((0, 0, -21), (21, 0, 0), (-21, 0, 0), (0, 0, 26), (-138, 0, 6), (138, 0, 6),
                      (6, 0, 98), (-20, 12, -140), (20, 12, -140), (0, 12, -198)):
        b.raw("summon iron_golem %s %s" % (pos(x, y, z), golem), 30)
    for (x, y, z) in ((-40, 12, -165), (0, 0, 30), (-60, 0, 12), (70, 0, -30)):
        b.raw('summon cat %s {variant:"minecraft:all_black",PersistenceRequired:1b}' % pos(x, y, z), 30)
    b.section("cleanup", "Final sweep")
    sel = box_sel(X_MIN, -12, Z_MIN, X_MAX, 140, Z_MAX)
    b.raw("kill @e[type=item,%s]" % sel)
    b.raw("kill @e[type=experience_orb,%s]" % sel)
    for h in HOSTILE:
        b.raw("kill @e[type=%s,%s]" % (h, sel))
    px, py, pz = PLATFORM
    b.raw("tp @s %s 180 -5" % pos(0.5, 0, 34.5))
    b.air(px - 4, py, pz - 4, px + 4, py + 1, pz + 4)
    for (x1, z1, x2, z2) in QUADS:
        b.raw("forceload remove %s %s %s %s" % (cx(x1), cz(z1), cx(x2), cz(z2)))
    b.raw("gamerule spawn_mobs true")
    b.raw("gamerule log_admin_commands true")
    b.raw("gamerule send_command_feedback true")
    b.raw("effect clear @s minecraft:saturation")
    b.raw('title @s subtitle {text:"Doom welcomes you to Latveria",color:"gray",italic:1b}')
    b.raw('title @s title {text:"LATVERIA",color:"dark_green",bold:1b}')
    b.raw("playsound minecraft:block.bell.use master @s ~ ~ ~ 1 0.6")


def build():
    b = Builder()
    setup(b)
    terrain.clear_site(b)
    terrain.build_crag(b)
    terrain.build_moat(b)
    terrain.build_grand_stair(b)
    castle.build_curtain(b)
    castle.build_towers(b)
    castle.build_gatehouse(b)
    castle.build_drawbridge(b)
    castle.build_courtyard(b)
    keep.build_keep(b)
    village.build_streets(b)
    village.build_plaza(b)
    village.build_town_walls(b)
    village.build_cathedral(b)
    village.build_town_hall(b)
    village.build_quarters(b)
    finale(b)
    return b


def weight(cmd, cost):
    """Extra pause (ms) after a command, so heavy fills don't pile up on the server."""
    if cmd.startswith("fill"):
        return min(1500, cost // 40)
    if cmd.startswith("place"):
        return 200
    if cmd.startswith("summon"):
        return 40
    return 0


UNKNOWN_SECTIONS = ("setup", "clear", "ground")   # the world before these is unknown


def prune_noops(b):
    """Replay the build in a voxel model and drop fill/setblock commands that would
    change nothing (they only produce "No blocks were filled" / "Could not set the
    block" errors in chat).  The site is fully known once it has been cleared and
    levelled, so only later sections are pruned.  Columns near generated trees
    (whose exact shape is unknown) are never pruned."""
    try:
        import numpy as np
    except ImportError:
        print("numpy not installed - skipping no-op pruning")
        return 0
    import re
    TOK = re.compile(r"\$([xyz])\((-?[0-9.]+)\)")
    X0, Y0, Z0 = X_MIN - 2, -14, Z_MIN - 2
    W = np.zeros((X_MAX - X0 + 3, 160, Z_MAX - Z0 + 3), dtype=np.int32)
    states, sid = ["air"], {"air": 0}
    trees = np.zeros((W.shape[0], W.shape[2]), dtype=bool)

    def st(spec):
        spec = spec.replace("minecraft:", "")
        if spec not in sid:
            sid[spec] = len(states)
            states.append(spec)
        return sid[spec]

    removed = 0
    for sec in b.sections:
        keep_all = sec["name"] in UNKNOWN_SECTIONS
        out = []
        for text, cost in sec["cmds"]:
            op = text.split(" ", 1)[0]
            if op == "place":
                v = [int(float(t) // 1) for _, t in TOK.findall(text)]
                x, z = v[0] - X0, v[2] - Z0
                trees[max(0, x - 5):x + 6, max(0, z - 5):z + 6] = True
            if op not in ("fill", "setblock"):
                out.append((text, cost))
                continue
            v = [int(float(t) // 1) for _, t in TOK.findall(text)]
            rest = TOK.sub("", text).split()
            if op == "fill":
                x1, y1, z1, x2, y2, z2 = v
            else:
                x1, y1, z1 = v
                x2, y2, z2 = v
            blk = rest[1]
            flt = rest[3] if len(rest) > 3 and rest[2] == "replace" else None
            a = (slice(x1 - X0, x2 - X0 + 1), slice(y1 - Y0, y2 - Y0 + 1), slice(z1 - Z0, z2 - Z0 + 1))
            sub = W[a]
            has_nbt = "{" in blk
            new = st(blk.split("{", 1)[0])
            if flt:
                fname = flt.split("[", 1)[0]
                ids = [i for i, s_ in enumerate(states) if s_.split("[", 1)[0] == fname]
                mask = np.isin(sub, ids)
                noop = not mask.any()
                sub[mask] = new
            else:
                noop = (not has_nbt) and bool((sub == new).all())
                sub[...] = new
            near_tree = trees[a[0], a[2]].any()
            if noop and not keep_all and not near_tree:
                removed += 1
                continue
            out.append((text, cost))
        sec["cmds"] = out
    return removed


def main():
    b = build()
    removed = prune_noops(b)
    print("pruned %d commands that would change nothing" % removed)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    lines = []
    n = 0
    total_ms = 0
    for sec in b.sections:
        if not sec["cmds"]:
            continue
        lines.append("!section\t%s" % sec["title"])
        pct = None
        lines.append("0\ttitle @s actionbar %s" % tc("Latveria: " + sec["title"], "green"))
        for text, cost in sec["cmds"]:
            if text.startswith("!wait"):
                _, ms, note = text.split(" ", 2)
                lines.append("!wait\t%s\t%s" % (ms, note))
                total_ms += int(ms)
                continue
            if chat_len(text) > CHAT_LIMIT:
                raise GenError("too long: " + text)
            w = weight(text, cost)
            lines.append("%d\t%s" % (w, text))
            total_ms += w
            n += 1
    with open(OUT, "w", newline="\r\n") as f:
        f.write("# Latveria build - generated by generator/build.py - %d commands\n" % n)
        f.write("\n".join(lines) + "\n")
    print("commands: %d   blocks touched: %d   sections: %d" % (n, b.stats["blocks"], len(b.sections)))
    print("built-in pauses: %.1f min (plus the sender's per-command delay)" % (total_ms / 60000.0))
    print("wrote", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
