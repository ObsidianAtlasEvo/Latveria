"""A voxel model of the world as the command lists leave it.

Used by the expansion generator to (a) find free ground next to the existing
city, (b) check new pieces against what is already there and (c) run a block-
light audit so dark, mob-spawnable spots can be lit.
"""
import re

import numpy as np

TOK = re.compile(r"\$([xyz])\((-?[0-9.]+)\)")

# light emitted by blocks (block light, 26.1 values)
LIGHT = {
    "lantern": 15, "sea_lantern": 15, "glowstone": 15, "jack_o_lantern": 15, "campfire": 15, "lava": 15,
    "fire": 15, "beacon": 15, "shroomlight": 15, "verdant_froglight": 15, "ochre_froglight": 15,
    "pearlescent_froglight": 15, "end_rod": 14, "torch": 14, "wall_torch": 14, "copper_lantern": 15,
    "soul_lantern": 10, "soul_campfire": 10, "soul_torch": 10, "soul_wall_torch": 10, "copper_torch": 14,
    "crying_obsidian": 10, "enchanting_table": 7, "ender_chest": 7, "magma_block": 3, "brewing_stand": 1,
    "amethyst_cluster": 5, "nether_portal": 11, "respawn_anchor": 0,
}
TRANSPARENT = ("air", "glass", "pane", "bars", "fence", "door", "ladder", "torch", "lantern", "chain", "carpet",
               "sign", "banner", "flower", "grass", "sapling", "leaves", "water", "wheat", "carrots", "potatoes",
               "beetroots", "lily", "rail", "button", "lever", "pressure_plate", "candle", "campfire", "potted",
               "flower_pot", "skull", "head", "bell", "cobweb", "end_rod", "lightning_rod", "chest", "anvil",
               "brewing_stand", "cauldron", "enchanting_table", "lectern", "stairs", "slab", "_wall", "hopper",
               "composter", "grindstone", "stonecutter", "beacon", "dripstone", "bamboo", "sugar_cane", "vine",
               "bed", "stem", "tulip", "poppy", "dandelion", "allium", "orchid", "bluet", "daisy", "cornflower",
               "lily_of_the_valley", "lilac", "rose", "peony", "sunflower", "torchflower", "nether_wart",
               "trapdoor", "fire", "portal", "item_frame", "amethyst_cluster", "sculk_sensor", "daylight",
               "repeater", "comparator", "redstone_wire", "tripwire", "conduit", "scaffolding", "snow",
               "cactus", "kelp", "seagrass", "iron_chain", "spore", "azalea", "dead_bush", "fern", "moss_carpet",
               "light")
PASSABLE = ("air", "short_grass", "tall_grass", "fern", "poppy", "dandelion", "cornflower", "light",
            "oxeye_daisy", "azure_bluet", "allium", "blue_orchid", "lily_of_the_valley", "tulip")


class World:
    X0, X1 = -320, 320
    Y0, Y1 = -140, 140
    Z0, Z1 = -260, 250

    def __init__(self):
        self.W = np.zeros((self.X1 - self.X0 + 1, self.Y1 - self.Y0 + 1, self.Z1 - self.Z0 + 1), dtype=np.uint16)
        self.states = ["air"]
        self.sid = {"air": 0}
        self.trees = []

    # ------------------------------------------------------------------
    def st(self, spec):
        spec = spec.replace("minecraft:", "").split("{", 1)[0]
        if spec not in self.sid:
            self.sid[spec] = len(self.states)
            self.states.append(spec)
        return self.sid[spec]

    def _sl(self, x1, y1, z1, x2, y2, z2):
        return (slice(x1 - self.X0, x2 - self.X0 + 1), slice(y1 - self.Y0, y2 - self.Y0 + 1),
                slice(z1 - self.Z0, z2 - self.Z0 + 1))

    def apply(self, text):
        op = text.split(" ", 1)[0]
        if op == "place":
            v = [int(float(t) // 1) for _, t in TOK.findall(text)]
            self.trees.append(tuple(v))
            return
        if op not in ("fill", "setblock"):
            return
        v = [int(float(t) // 1) for _, t in TOK.findall(text)]
        rest = TOK.sub("", text).split()
        if op == "fill":
            x1, y1, z1, x2, y2, z2 = v
        else:
            x1, y1, z1 = v
            x2, y2, z2 = v
        blk = rest[1]
        flt = rest[3] if len(rest) > 3 and rest[2] == "replace" else None
        sub = self.W[self._sl(x1, y1, z1, x2, y2, z2)]
        new = self.st(blk)
        if flt:
            fname = flt.split("[", 1)[0]
            ids = [i for i, s in enumerate(self.states) if s.split("[", 1)[0] == fname]
            sub[np.isin(sub, ids)] = new
        else:
            sub[...] = new

    def load_file(self, path):
        for line in open(path, encoding="utf-8"):
            if line.startswith(("#", "!")):
                continue
            self.apply(line.rstrip("\r\n").split("\t", 1)[1])

    def load_builder(self, b):
        for sec in b.sections:
            for text, _ in sec["cmds"]:
                if not text.startswith("!"):
                    self.apply(text)

    # ------------------------------------------------------------------
    def get(self, x, y, z):
        return self.states[self.W[x - self.X0, y - self.Y0, z - self.Z0]]

    def name(self, x, y, z):
        return self.get(x, y, z).split("[", 1)[0]

    def box_names(self, x1, y1, z1, x2, y2, z2):
        ids = np.unique(self.W[self._sl(x1, y1, z1, x2, y2, z2)])
        return {self.states[i].split("[", 1)[0] for i in ids}

    def box_is(self, x1, y1, z1, x2, y2, z2, allowed):
        return self.box_names(x1, y1, z1, x2, y2, z2) <= set(allowed)

    # ------------------------------------------------------------------
    def _class_luts(self):
        n = len(self.states)
        emit = np.zeros(n, dtype=np.int8)
        opaque = np.zeros(n, dtype=bool)
        floor_ok = np.zeros(n, dtype=bool)
        passable = np.zeros(n, dtype=bool)
        for i, s in enumerate(self.states):
            nm = s.split("[", 1)[0]
            lit = "lit=false" not in s
            e = LIGHT.get(nm, 0)
            if nm == "light":
                m = re.search(r"level=(\d+)", s)
                e = int(m.group(1)) if m else 15
            if nm.endswith("copper_bulb") and "lit=true" in s:
                e = 15
            if nm == "redstone_lamp" and "lit=true" in s:
                e = 15
            if nm.endswith(("campfire",)) and not lit:
                e = 0
            if nm.endswith("candle") and "lit=true" in s:
                e = 3 * int(re.search(r"candles=(\d)", s).group(1)) if "candles=" in s else 3
            emit[i] = e
            tr = any(t in nm for t in TRANSPARENT)
            opaque[i] = not tr
            floor_ok[i] = (not tr) and nm not in ("bedrock", "barrier", "farmland", "dirt_path", "magma_block",
                                                  "soul_sand", "honey_block", "tinted_glass", "water", "lava")
            passable[i] = nm in PASSABLE or nm.endswith("_tulip")
        return emit, opaque, floor_ok, passable

    def block_light(self, box):
        """Block light over box (x1,y1,z1,x2,y2,z2) plus a 15-block margin.
        Returns (light, states, origin) for the padded box."""
        x1, y1, z1, x2, y2, z2 = box
        m = 15
        ax1, ay1, az1 = max(self.X0, x1 - m), max(self.Y0, y1 - m), max(self.Z0, z1 - m)
        ax2, ay2, az2 = min(self.X1, x2 + m), min(self.Y1, y2 + m), min(self.Z1, z2 + m)
        sub = self.W[self._sl(ax1, ay1, az1, ax2, ay2, az2)]
        emit, opaque, _, _ = self._class_luts()
        E = emit[sub]
        op = opaque[sub]
        L = E.copy()
        for _ in range(15):
            P = L.copy()
            for ax in range(3):
                for sh in (1, -1):
                    R = np.roll(L, sh, axis=ax)
                    idx = [slice(None)] * 3
                    idx[ax] = slice(0, 1) if sh == 1 else slice(-1, None)
                    R[tuple(idx)] = 0
                    np.maximum(P, R - 1, out=P)
            P[op] = E[op]
            L = P
        return L, sub, (ax1, ay1, az1)

    def dark_spawn_cells(self, box, exclude=None):
        """Cells in box where a monster could spawn at night: a full solid floor,
        two passable cells above it, and block light 0."""
        L, sub, (ox, oy, oz) = self.block_light(box)
        emit, opaque, floor_ok, passable = self._class_luts()
        pas = passable[sub]
        flo = floor_ok[sub]
        up = np.roll(pas, -1, axis=1)
        up[:, -1, :] = False
        below = np.roll(flo, 1, axis=1)
        below[:, 0, :] = False
        cell = pas & up & below & (L <= 0)
        x1, y1, z1, x2, y2, z2 = box
        cell = cell[x1 - ox:x2 - ox + 1, y1 - oy:y2 - oy + 1, z1 - oz:z2 - oz + 1]
        pts = np.argwhere(cell)
        out = [(int(p[0]) + x1, int(p[1]) + y1, int(p[2]) + z1) for p in pts]
        if exclude:
            out = [p for p in out if not exclude(*p)]
        return out
