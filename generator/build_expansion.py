#!/usr/bin/env python3
"""Generate Latveria Survival Expansion v2 as a second chat-command file.

    python build_expansion.py      -> ../windows/latveria_expansion_commands.txt

Needs numpy.  Reads ../windows/latveria_commands.txt (the first build) to model
the finished city, so it must be generated after build.py.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from core import Builder, pos, cx, cy, cz, tc, GenError, chat_len, CHAT_LIMIT
from layout import *
import build as build1
import expansion as E
import sim

OUT = os.path.join(HERE, "..", "windows", "latveria_expansion_commands.txt")
FIRST = os.path.join(HERE, "..", "windows", "latveria_commands.txt")

TOWN_QUADS = build1.QUADS
EAST_Q = [(151, -130, 300, -10), (151, -9, 300, 112)]
SOUTH_Q = [(-150, 113, -1, 240), (0, 113, 150, 240)]
WEST_Q = [(-300, -130, -151, -10), (-300, -9, -151, 112)]
PLATFORM = build1.PLATFORM


class Runner:
    def __init__(self):
        self.b = Builder()
        self.world = sim.World()
        self.world.load_file(FIRST)
        E.WORLD = self.world
        self._seen = {}

    def sync(self):
        for sec in self.b.sections:
            done = self._seen.get(id(sec), 0)
            for text, _ in sec["cmds"][done:]:
                if not text.startswith("!"):
                    self.world.apply(text)
            self._seen[id(sec)] = len(sec["cmds"])

    def run(self, fn, *a):
        fn(self.b, *a)
        self.sync()

    def load(self, quads, note):
        for q in quads:
            E.forceload(self.b, q, True)
        self.b.wait(60000, note)

    def unload(self, quads):
        for q in quads:
            E.forceload(self.b, q, False)

    def populate(self, title):
        b = self.b
        if not b.later:
            return
        b.section("population_" + title, "Bringing the %s to life" % title)
        for cmd in b.later:
            b.raw(cmd, 30)
        b.later = []


def main():
    R = Runner()
    b = R.b
    # ---- setup -----------------------------------------------------------
    b.section("setup", "Preparing the expansion")
    b.raw("gamerule send_command_feedback false")
    b.raw("gamerule log_admin_commands false")
    b.raw("gamerule spawn_mobs false")
    b.raw("effect give @s minecraft:saturation infinite 0 true")
    px, py, pz = PLATFORM
    b.fill(px - 4, py, pz - 4, px + 4, py, pz + 4, "black_stained_glass")
    b.walls(px - 4, py + 1, pz - 4, px + 4, py + 1, pz + 4, "glass")
    b.raw("tp @s %s 180 25" % pos(px + 0.5, py + 1, pz + 2.5))
    R.load(TOWN_QUADS, "loading the city")

    # ---- underground and the town ---------------------------------------
    R.run(E.build_cistern)
    R.run(E.build_gate_defences)

    # ---- east: Doomwerk --------------------------------------------------
    b.section("load_east", "Loading the east")
    R.load(EAST_Q, "loading the east district")
    R.run(E.clear_district, E.EAST, "east district")
    R.run(E.build_east_roads)
    R.run(E.build_depository)
    R.run(E.build_foundry)
    R.run(E.build_golem_works)
    R.run(E.build_hall_of_shadows)
    R.run(E.build_tree_farm)
    R.run(E.build_quarry)
    R.run(E.build_mine)
    R.run(lambda bb: (bb.section("rail_east", "The east minecart line"),
                      E.rail_line(bb, 26, 296, 2, "x", "Plaza", "Doomwerk")))
    hall = (230, 0, -46, 280, 34, -29)
    golem = (242, -1, -100, 263, 14, -79)
    mine = (230, -135, 30, 300, -50, 90)
    print("lighting (east): %d lights" % E.lighting_audit(b, R.world, [(151, -1, -130, 300, 44, 112)],
                                                         [hall, golem, mine], "the east"))
    R.populate("east")
    b.section("unload_east", "Leaving the east")
    R.unload(EAST_Q)

    # ---- south -----------------------------------------------------------
    b.section("load_south", "Loading the south")
    R.load(SOUTH_Q, "loading the south district")
    R.run(E.clear_district, E.SOUTH, "south district")
    R.run(E.build_south_roads)
    R.run(E.build_exchange)
    R.run(E.build_nursery)
    R.run(E.build_cane_melon_bamboo)
    R.run(E.build_ranch)
    R.run(E.build_harbour)
    R.run(lambda bb: (bb.section("rail_south", "The south minecart line"),
                      E.rail_line(bb, 26, 150, 2, "z", "Plaza South", "Harbour")))
    print("lighting (south): %d lights" % E.lighting_audit(b, R.world, [(-150, -6, 113, 150, 40, 240)], [], "the south"))
    R.populate("south")
    b.section("unload_south", "Leaving the south")
    R.unload(SOUTH_Q)

    # ---- west ------------------------------------------------------------
    b.section("load_west", "Loading the west")
    R.load(WEST_Q, "loading the west district")
    R.run(E.clear_district, E.WEST, "west district")
    R.run(E.build_west_roads)
    R.run(E.build_nether_hub)
    R.run(E.build_manor)
    # the sewers and Doom's escape tunnel reach under the west district, so they come after it is cleared
    R.run(E.build_sewers)
    R.run(E.build_escape_tunnel)
    print("lighting (west): %d lights" % E.lighting_audit(b, R.world, [(-300, -1, -130, -151, 40, 112)], [], "the west"))
    R.populate("west")
    b.section("unload_west", "Leaving the west")
    R.unload(WEST_Q)

    # ---- stations and the lighting audit of the capital ------------------
    R.run(station_signs)
    placed = E.lighting_audit(b, R.world, E.AUDIT_BOXES, [], "the capital")
    print("lighting audit (city): %d lights" % placed)
    R.sync()

    # ---- finish ----------------------------------------------------------
    b.section("cleanup", "Final sweep")
    sel = build1.box_sel(X_MIN, -12, Z_MIN, X_MAX, 140, Z_MAX)
    b.raw("kill @e[type=item,%s]" % sel)
    for h in build1.HOSTILE:
        b.raw("kill @e[type=%s,%s]" % (h, sel))
    b.raw("tp @s %s 180 -5" % pos(0.5, 0, 34.5))
    b.air(px - 4, py, pz - 4, px + 4, py + 1, pz + 4)
    R.unload(TOWN_QUADS)
    b.raw("gamerule spawn_mobs true")
    b.raw("gamerule log_admin_commands true")
    b.raw("gamerule send_command_feedback true")
    b.raw("effect clear @s minecraft:saturation")
    b.raw('title @s subtitle {text:"Latveria Survival Expansion v2 complete",color:"gray",italic:1b}')
    b.raw('title @s title {text:"DOOM PROVIDES",color:"dark_green",bold:1b}')
    write(b, R)


def station_signs(b):
    b.section("stations", "Station signs")
    for (x, z, f, t) in ((26, 4, "south", ["PLAZA", "STATION", "East line:", "Doomwerk"]),
                         (4, 26, "east", ["PLAZA", "STATION", "South line:", "Harbour"])):
        b.set(x, 0, z, "polished_blackstone_bricks")
        b.set(x, 1, z, "polished_blackstone_bricks")
        side = (x, 1, z + 1) if f == "south" else (x + 1, 1, z)
        b.set(*side, "dark_oak_wall_sign[facing=%s]" % f + E.sign(t, "dark_green", True))
        b.set(x, 2, z, "lantern")


def write(b, R):
    lines = []
    n = 0
    total_ms = 0
    ymin, ymax = 0, 0
    import re
    for sec in b.sections:
        if not sec["cmds"]:
            continue
        lines.append("!section\t%s" % sec["title"])
        lines.append("0\ttitle @s actionbar %s" % tc("Expansion: " + sec["title"], "green"))
        for text, cost in sec["cmds"]:
            if text.startswith("!wait"):
                _, ms, note = text.split(" ", 2)
                lines.append("!wait\t%s\t%s" % (ms, note))
                total_ms += int(ms)
                continue
            if chat_len(text) > CHAT_LIMIT:
                raise GenError("too long: " + text)
            for yv in re.findall(r"\$y\((-?[0-9.]+)\)", text):
                ymin = min(ymin, float(yv)); ymax = max(ymax, float(yv))
            w = build1.weight(text, cost)
            lines.append("%d\t%s" % (w, text))
            total_ms += w
            n += 1
    with open(OUT, "w", newline="\r\n") as f:
        f.write("# Latveria Survival Expansion v2 - generated by generator/build_expansion.py - %d commands\n" % n)
        f.write("# range y %d %d\n" % (int(ymin) - 1, int(ymax) + 1))
        f.write("\n".join(lines) + "\n")
    print("commands: %d   sections: %d   y range %d..%d" % (n, len(b.sections), ymin, ymax))
    print("built-in pauses: %.1f min" % (total_ms / 60000.0))
    print("wrote", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
