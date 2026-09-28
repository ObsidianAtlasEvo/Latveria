#!/usr/bin/env python3
"""Audit of the combined world left by the three executed layers (main build, Survival
Expansion v2, Lighting Overhaul), and - with --after - of the world after Refinement v3.

    python audit3.py            -> ../docs/v3/audit/*.png + audit_stats.json
    python audit3.py --after    -> ../docs/v3/after/*.png  (includes v3)
"""
import collections
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sim
import render3 as R

WIN = os.path.join(HERE, "..", "windows")
EXECUTED = ["latveria_commands.txt", "latveria_expansion_commands.txt", "latveria_lighting_commands.txt"]
V3 = "latveria_refinement_v3_commands.txt"

WHOLE = (-305, -12, -256, 305, 131, 244)
CASTLE = (-72, -2, -230, 72, 131, -64)
KEEP_PLAN = (-32, -198, 32, -148)
CASTLE_PLAN = (-70, -228, 70, -92)
TOWN = (-150, -2, -72, 150, 70, 112)
EAST = (145, -2, -135, 305, 60, 115)
SOUTH = (-155, -8, 110, 155, 45, 244)
WEST = (-305, -2, -135, -145, 45, 115)
UNDER = (-200, -40, -230, 200, -2, 110)
LEVELS = {"dungeon": 2, "ground": 12, "second": 28, "third": 38, "roof": 48}

DISTRICT_LABELS = [(0, -170, "CASTLE DOOM"), (0, 20, "PLAZA OF DOOM"), (0, 80, "DOOMSTADT"),
                   (225, -100, "DOOMWERK"), (0, 190, "SOUTHMARCH"), (-225, 0, "WEST MARCH"),
                   (87, 196, "HARBOUR"), (-228, -30, "MEPHISTO GATE"), (-221, 34, "MANOR"),
                   (252, -90, "Golem Works"), (256, -38, "Hall of Shadows"), (180, -91, "Depository"),
                   (182, -41, "Foundry"), (262, 60, "Quarry"), (-50, 123, "Exchange"), (-54, 144, "Nursery"),
                   (-48, 203, "Ranch"), (185, 60, "Tree farm")]


def load(files):
    w = sim.World()
    for f in files:
        w.load_file(os.path.join(WIN, f))
    return w


def stats(w):
    nonair = int(np.count_nonzero(w.W))
    idx = np.argwhere(w.W != 0)
    lo, hi = idx.min(axis=0), idx.max(axis=0)
    ents = collections.Counter(e["type"] for e in w.entities)
    golems = [e for e in w.entities if e["type"] == "iron_golem"]
    return {"non_air_blocks": nonair,
            "bounds": [int(lo[0] + w.X0), int(lo[1] + w.Y0), int(lo[2] + w.Z0), int(hi[0] + w.X0), int(hi[1] + w.Y0), int(hi[2] + w.Z0)],
            "entities": sum(ents.values()), "entities_by_type": dict(ents.most_common()),
            "iron_golems": [(round(e["x"]), round(e["y"]), round(e["z"]), e["name"]) for e in golems],
            "block_states": len(w.states), "trees_unknown_shape": len(w.trees)}


def render_all(w, out, tag):
    os.makedirs(out, exist_ok=True)
    # full map
    img = R.top_down(w, WHOLE, scale=2)
    R.grid(img, WHOLE, 2)
    R.labels(img, WHOLE, 2, DISTRICT_LABELS)
    R.label(img, "Latveria %s - top-down (1 px = 0.5 block), grid 50 blocks, origin = plaza centre" % tag)
    img.save(os.path.join(out, "map_full.png"))
    # castle plans
    ims = []
    for nm, y in LEVELS.items():
        im = R.plan(w, KEEP_PLAN, y, scale=6)
        R.label(im, "Keep %s level (walk y=%d)" % (nm, y))
        ims.append(im)
    R.sheet(ims, 3).save(os.path.join(out, "castle_keep_plans.png"))
    im = R.plan(w, CASTLE_PLAN, 12, scale=4)
    R.label(im, "Castle Doom courtyard level (y=12)")
    im.save(os.path.join(out, "castle_courtyard_plan.png"))
    im = R.plan(w, CASTLE_PLAN, 28, scale=4)
    R.label(im, "Castle Doom wall-walk level (y=28)")
    im.save(os.path.join(out, "castle_wallwalk_plan.png"))
    # elevations
    ims = []
    for f in ("south", "east", "west", "north"):
        im = R.elevation(w, CASTLE, f, scale=3)
        R.label(im, "Castle Doom - %s elevation" % f)
        ims.append(im)
    R.sheet(ims, 2).save(os.path.join(out, "castle_elevations.png"))
    # districts
    for nm, box in (("doomstadt", TOWN), ("doomwerk", EAST), ("southmarch", SOUTH), ("west_march", WEST)):
        im = R.top_down(w, box, scale=3)
        R.grid(im, box, 3, step=25)
        R.label(im, "%s plan (grid 25)" % nm)
        im.save(os.path.join(out, "plan_%s.png" % nm))
    # underground
    im = R.underground(w, UNDER, scale=3)
    R.grid(im, UNDER, 3, step=25)
    R.label(im, "Underground voids y -40..-2 (blue deep, orange shallow)")
    im.save(os.path.join(out, "map_underground.png"))
    # entities
    img = R.top_down(w, WHOLE, scale=2)
    cols = {"villager": (60, 220, 90), "iron_golem": (255, 255, 255), "armor_stand": (230, 200, 60),
            "minecart": (255, 80, 80), "zombie": (255, 0, 255)}
    for t, c in cols.items():
        R.overlay_points(img, WHOLE, 2, [(e["x"], e["z"]) for e in w.entities if e["type"] == t], c, r=3)
    other = [(e["x"], e["z"]) for e in w.entities if e["type"] not in cols]
    R.overlay_points(img, WHOLE, 2, other, (120, 170, 255), r=2)
    R.label(img, "Entities: green villagers, white golems, yellow armour stands, red minecarts, blue animals/boats")
    img.save(os.path.join(out, "map_entities.png"))


SEWER = (-150, -14, -72, 150, -4, 112)
LIGHT_Y = 0


def extra_maps(w, out, before=None):
    """Transport, lighting, functional-infrastructure and sewer maps (+ before/after sheets)."""
    import numpy as np
    from PIL import Image
    # sewer / cistern map: built voids between y -14 and -4
    im = R.underground(w, SEWER, scale=3)
    R.grid(im, SEWER, 3, step=25)
    R.label(im, "Sewers, cistern and tunnels (y -14..-4)")
    im.save(os.path.join(out, "map_sewers.png"))
    # transport: rails, roads, stations
    img = R.top_down(w, WHOLE, scale=2, shade=False)
    img = Image.fromarray((np.asarray(img) * 0.45).astype("uint8"))
    sub = w.W[w._sl(*WHOLE)]
    names = np.array([s_.split("[", 1)[0] for s_ in w.states])
    top = np.zeros(sub.shape[::2], dtype=int)
    rails = np.isin(names[sub], ["rail", "powered_rail", "detector_rail", "activator_rail"]).any(axis=1)
    road = np.isin(names[sub[:, 12, :]], ["stone_bricks", "polished_andesite", "cobblestone", "cracked_stone_bricks",
                                          "mossy_stone_bricks", "andesite", "dirt_path"])      # y = -1 is index 11 from -12
    pts_r = [(int(i) + WHOLE[0], int(k) + WHOLE[2]) for i, k in np.argwhere(road)[::3]]
    R.overlay_points(img, WHOLE, 2, pts_r, (150, 150, 150), r=1)
    pts = [(int(i) + WHOLE[0], int(k) + WHOLE[2]) for i, k in np.argwhere(rails)]
    R.overlay_points(img, WHOLE, 2, pts, (255, 200, 40), r=1)
    R.labels(img, WHOLE, 2, [(27, 8, "Plaza stn"), (292, 8, "Doomwerk stn"), (10, 30, "Plaza South stn"), (12, 148, "Harbour stn"),
                             (-228, -24, "Mephisto Gate"), (0, -84, "Grand Stair")], (255, 230, 120))
    R.label(img, "Transport: rail lines (yellow), paved roads (grey), stations")
    img.save(os.path.join(out, "map_transport.png"))
    # lighting: max block light at walking level over the whole map
    L, subl, (ox, oy, oz) = w.block_light((WHOLE[0] + 15, -2, WHOLE[2] + 15, WHOLE[3] - 15, 60, WHOLE[5] - 15))
    Lm = L.max(axis=1)
    rgb = np.zeros(Lm.shape + (3,), "uint8")
    rgb[..., 0] = np.clip(Lm * 17, 0, 255)
    rgb[..., 1] = np.clip(Lm * 14, 0, 255)
    rgb[..., 2] = np.clip(Lm * 6, 0, 255)
    im = Image.fromarray(rgb.transpose(1, 0, 2)).resize((Lm.shape[0] * 2, Lm.shape[1] * 2), Image.NEAREST)
    R.label(im, "Lighting: brightest block light in each column (black = none)")
    im.save(os.path.join(out, "map_lighting.png"))
    # functional infrastructure: farms, storage, transport, defence markers
    img = R.top_down(w, WHOLE, scale=2)
    items = [(252, -90, "IRON (Golem Works)"), (256, -38, "XP (Hall of Shadows)"), (180, -91, "STORAGE"),
             (210, -104, "SORTER"), (182, -41, "SMELTING"), (193, -54, "LAVA"), (-54, 144, "BREEDING"),
             (-39, 145, "Children's Yard"), (-126, 175, "CANE/MELON"), (-88, 175, "BAMBOO"), (-30, 200, "RANCH"),
             (-244, -55, "NETHER WART"), (-228, -30, "PORTALS"), (185, 60, "TREES"), (262, 60, "QUARRY"),
             (87, 196, "FISH"), (0, 104, "GATE BATTERY"), (-144, 0, "GATE BATTERY"), (144, 0, "GATE BATTERY"),
             (0, -112, "ALARM BELLS"), (0, -184, "TIME PLATFORM"), (-26, -131, "DEEP CELLS")]
    R.labels(img, WHOLE, 2, items, (120, 255, 160))
    R.label(img, "Functional infrastructure")
    img.save(os.path.join(out, "map_infrastructure.png"))
    if before is not None:
        for nm, box, facing in (("castle_south", CASTLE, "south"), ("castle_east", CASTLE, "east")):
            a = R.elevation(before, box, facing, scale=3)
            b = R.elevation(w, box, facing, scale=3)
            R.label(a, "before v3")
            R.label(b, "after v3")
            R.sheet([a, b], 2).save(os.path.join(out, "before_after_%s.png" % nm))
        a = R.top_down(before, KEEP_BOX, scale=4)
        b = R.top_down(w, KEEP_BOX, scale=4)
        R.label(a, "keep roof before")
        R.label(b, "keep roof after")
        R.sheet([a, b], 2).save(os.path.join(out, "before_after_keep_roof.png"))
        for nm, box in (("town_north", (-50, -2, -75, 50, 40, -5)), ("southmarch", (-70, -4, 130, 30, 30, 240))):
            a = R.top_down(before, box, scale=4)
            b = R.top_down(w, box, scale=4)
            R.label(a, nm + " before")
            R.label(b, nm + " after")
            R.sheet([a, b], 2).save(os.path.join(out, "before_after_%s.png" % nm))


KEEP_BOX = (-34, -2, -200, 34, 110, -146)


def main():
    after = "--after" in sys.argv
    files = EXECUTED + ([V3] if after else [])
    w = load(files)
    out = os.path.join(HERE, "..", "docs", "v3", "after" if after else "audit")
    st = stats(w)
    render_all(w, out, "after Refinement v3" if after else "as executed (main + v2 + lighting)")
    extra_maps(w, out, load(EXECUTED) if after else None)
    with open(os.path.join(out, "stats.json"), "w") as f:
        json.dump(st, f, indent=1)
    print(json.dumps({k: v for k, v in st.items() if k != "iron_golems"}, indent=1))
    return w


if __name__ == "__main__":
    main()
