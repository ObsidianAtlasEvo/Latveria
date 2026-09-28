"""Guarded, additive command layer for Latveria Refinement v3.

The world the command file runs against is a finished, lived-in build.  Everything
here is written so that a command can only ever do one of:

  put        setblock <p> <block> keep             - only into air
  fill_keep  fill <a> <b> <block> keep             - only into air cells
  swap       fill <a> <b> <new> replace <old>      - only cells that still hold <old>
  carve      fill <a> <b> air replace <material>   - only natural crag / earth materials,
                                                     and only where the model shows nothing
                                                     else in the volume
  pair       execute if block A air if block B air run setblock A <lower> strict  (+ the upper
             half only if the lower half is in place) - doors, beds, tall plants
  once       execute unless entity @e[tag=lv3_<id>] run summon ... {Tags:["lv3","lv3_<id>"]}
  stock      execute unless items block <p> container.N * run item replace block ...

so re-running a section, or resuming after an interruption, never duplicates an
entity, overwrites a changed block or refills a chest the player has emptied.
No gamerule, forceload or broad kill is ever emitted.

At generation time every command is applied to the voxel model of the world as
it stands after the three executed layers (sim.World).  The generator uses it to
  * refuse writes into protected volumes (the player's own Doombot factory room),
  * refuse carves whose volume holds anything but crag material,
  * report no-op replaces (a replace that would find nothing is a design error),
  * drop guarded placements whose target the model shows as occupied (so a
    decoration is never half-placed), grouped per `piece`,
  * check that every write lies within reach (loaded chunks) of the section's
    teleport anchor.
"""
import collections
import contextlib
import json
import re

import numpy as np

from core import Builder, GenError, check_block, check_reg, chat_len, CHAT_LIMIT, item_arg, pos, snbt_str, tc, parse_block

CRAG = ("stone", "dirt", "andesite", "cobbled_deepslate", "deepslate", "tuff", "granite", "diorite", "gravel",
        "coarse_dirt", "grass_block", "cobblestone", "mossy_cobblestone")
REACH = 128          # max horizontal (Chebyshev) distance of a write from the section anchor
REACH_ENTITY = 96    # summons / entity selectors: entities must be loaded too

# volumes v3 must never write into
PROTECTED = {
    "the player's own Doombot factory room": (-29, 0, -195, -5, 11, -167),
}

TOKXYZ = re.compile(r"\$([xyz])\((-?[0-9.]+)\)")


class V3:
    def __init__(self, world):
        self.w = world
        self.w.layer = "latveria_refinement_v3_commands.txt"
        self.b = Builder()
        self.anchor = None
        self.sec = None
        self.problems = []           # structural problems (must be 0)
        self.notes = collections.Counter()
        self.stats = collections.Counter()
        self.skipped = []            # (section, piece, reason)
        self.mechanisms = []         # (section, name, status, description)
        self.piece_stack = []
        self.sec_bounds = {}
        self.entity_ids = set()
        self.replace_ops = 0
        self.w0 = None                # the world before v3 (for "new" dark cells)
        self.cur_bounds = None        # bounds of the current section's writes
        self.autolight = True

    # ------------------------------------------------------------------ sections
    def close_section(self):
        """Light any spawnable block-light-0 surface the section created (roofs, stall tops, hay)."""
        if self.sec is None or self.cur_bounds is None:
            return
        x1, y1, z1, x2, y2, z2 = self.cur_bounds
        self.cur_bounds = None
        if not self.autolight:
            return
        relight(self, (x1 - 1, y1 - 2, z1 - 1, x2 + 1, y2 + 3, z2 + 1), target=1, interiors=False)

    def section(self, name, title, anchor):
        """anchor: (x, z) or (x, y, z).  The player is teleported to a safe standing cell there so the
        section's chunks are loaded (no forceload)."""
        self.close_section()
        self.b.section(name, title)
        self.sec = name
        ax, az = anchor[0], anchor[-1]
        if len(anchor) == 3:
            ay = self.safe_y(ax, az, anchor[1])
        else:
            ax, ay, az = self.find_anchor(ax, az)
        self.anchor = (ax, ay, az)
        self._raw("tp @s %s" % pos(ax + 0.5, ay, az + 0.5))
        self.b.raw("title @s actionbar %s" % tc("Refinement v3: " + title, "dark_green"))
        self.b.wait(6000, "loading " + title)
        self.sec_bounds[name] = {"title": title, "anchor": self.anchor, "cmds_start": self.b.stats["commands"]}

    def safe_y(self, x, z, y=None):
        """Standing cell: solid floor, feet and head free.  With no y, the highest one in the column."""
        if y is not None:
            if self._standable(x, y, z):
                return y
            raise GenError("anchor %s not standable" % ((x, y, z),))
        for yy in range(130, -30, -1):
            if self._standable(x, yy, z):
                return yy
        raise GenError("no standing cell at %s" % ((x, z),))

    def find_anchor(self, x, z):
        for r in range(0, 12):
            for dx in range(-r, r + 1):
                for dz in (-r, r) if abs(dx) != r else range(-r, r + 1):
                    try:
                        return x + dx, self.safe_y(x + dx, z + dz), z + dz
                    except GenError:
                        pass
        raise GenError("no standing cell near %s" % ((x, z),))

    def _standable(self, x, y, z):
        w = self.w
        fl = w.name(x, y - 1, z)
        return (w.name(x, y, z) == "air" and w.name(x, y + 1, z) == "air" and fl not in
                ("air", "water", "lava", "fire", "light", "magma_block", "campfire", "soul_campfire")
                and not fl.endswith(("_carpet", "_slab", "_trapdoor", "_pressure_plate")))

    # ------------------------------------------------------------------ low level
    def _raw(self, text, cost=1):
        self.b.raw(text, cost)
        self.w.apply(text)

    def _reach(self, x, z, entity=False):
        if self.anchor is None:
            raise GenError("write before the first section")
        lim = REACH_ENTITY if entity else REACH
        d = max(abs(x - self.anchor[0]), abs(z - self.anchor[2]))
        if d > lim:
            self.problems.append("%s: write at %s is %d blocks from the anchor %s" % (self.sec, (x, z), d, self.anchor))

    def _protect(self, x1, y1, z1, x2, y2, z2):
        for nm, (a, b_, c, d, e, f) in PROTECTED.items():
            if x1 <= d and x2 >= a and y1 <= e and y2 >= b_ and z1 <= f and z2 >= c:
                self.problems.append("%s: write %s touches %s" % (self.sec, (x1, y1, z1, x2, y2, z2), nm))

    def _in_protected(self, x, y, z):
        return any(a <= x <= d and b_ <= y <= e and c <= z <= f for (a, b_, c, d, e, f) in PROTECTED.values())

    def _box(self, x1, y1, z1, x2, y2, z2):
        x1, x2 = sorted((x1, x2)); y1, y2 = sorted((y1, y2)); z1, z2 = sorted((z1, z2))
        cb = self.cur_bounds
        self.cur_bounds = (x1, y1, z1, x2, y2, z2) if cb is None else (
            min(cb[0], x1), min(cb[1], y1), min(cb[2], z1), max(cb[3], x2), max(cb[4], y2), max(cb[5], z2))
        self._protect(x1, y1, z1, x2, y2, z2)
        self._reach(x1, z1); self._reach(x2, z2)
        return x1, y1, z1, x2, y2, z2

    # ------------------------------------------------------------------ pieces
    @contextlib.contextmanager
    def piece(self, name):
        """Group guarded placements: if any keep-target of the group is occupied in the model, the
        whole group is left out (and listed in the report) so nothing is ever half-built."""
        self.piece_stack.append({"name": name, "ops": []})
        try:
            yield self
        finally:
            p = self.piece_stack.pop()
            blocked = [op for op in p["ops"] if op[0] == "keep" and not self._free(*op[1])]
            if blocked:
                self.skipped.append((self.sec, name, "occupied at %s" % (blocked[0][1][:3],)))
                self.stats["pieces_skipped"] += 1
            else:
                self.stats["pieces"] += 1
                for op in p["ops"]:
                    op[2]()

    def _free(self, x1, y1, z1, x2, y2, z2):
        """Air in the model, and no entity (animal, villager, stand) standing in the volume."""
        w = self.w
        if np.any(w.W[w._sl(x1, y1, z1, x2, y2, z2)]):
            return False
        for e in w.entities:
            ex, ey, ez = int(e["x"] // 1), int(e["y"] // 1), int(e["z"] // 1)
            if x1 - 1 <= ex <= x2 + 1 and y1 - 2 <= ey <= y2 and z1 - 1 <= ez <= z2 + 1:
                return False
        return True

    def _op(self, kind, box, fn):
        if self.piece_stack:
            self.piece_stack[-1]["ops"].append((kind, box, fn))
        else:
            if kind == "keep" and not self._free(*box):
                self.skipped.append((self.sec, "single", "occupied at %s" % (box[:3],)))
                self.stats["singles_skipped"] += 1
                return
            fn()

    # ------------------------------------------------------------------ guarded writes
    def put(self, x, y, z, block, force_nbt=None):
        """setblock ... keep (with optional inline NBT such as sign text)."""
        check_block(block.split("{", 1)[0])
        box = self._box(x, y, z, x, y, z)
        cmd = "setblock %s %s keep" % (pos(x, y, z), block)
        if chat_len(cmd) > CHAT_LIMIT:
            raise GenError("too long: " + cmd)

        def go():
            self._raw(cmd)
            self.stats["put"] += 1
        self._op("keep", box, go)

    def fill_keep(self, x1, y1, z1, x2, y2, z2, block):
        check_block(block)
        box = self._box(x1, y1, z1, x2, y2, z2)
        if box[0] == box[3] and box[1] == box[4] and box[2] == box[5]:
            return self.put(x1, y1, z1, block)

        def go():
            self.b.fill(*box, block, mode="keep")
            self.w.apply("fill %s %s %s keep" % (pos(*box[:3]), pos(*box[3:]), block))
            self.stats["fill_keep"] += 1
        self._op("keep", box, go)

    def swap(self, x1, y1, z1, x2, y2, z2, new, old, expect=1, always=False):
        """Replace cells that hold `old` (a block name, optionally with states) by `new`."""
        check_block(new)
        check_block(old)
        box = self._box(x1, y1, z1, x2, y2, z2)
        w = self.w
        oname = old.split("[", 1)[0]
        sec = self.sec

        def count():
            sub = w.W[w._sl(*box)]
            ids = [i for i, s in enumerate(w.states) if s.split("[", 1)[0] == oname and (old == oname or s == old)]
            return ids, int(np.isin(sub, ids).sum())

        ids, n = count()
        if n < expect and not self.piece_stack:
            self.problems.append("%s: replace %s->%s in %s finds %d cells (expected >= %d)" % (sec, old, new, box, n, expect))
            return 0

        def go():
            ids, n = count()                # counted again: inside a piece the old block may be the piece's own
            if n == 0 and not always:
                self.stats["noop_swaps_dropped"] += 1
                return                      # nothing to swap: the command would only print an error in chat
            if n < expect:
                self.problems.append("%s: replace %s->%s in %s finds %d cells (expected >= %d)" % (sec, old, new, box, n, expect))
                return
            self.b.fill(*box, new, mode="replace " + old)
            s = w.W[w._sl(*box)]
            s[np.isin(s, ids)] = w.st(new)
            self.stats["swap"] += 1
            self.stats["swapped_cells"] += n
            self.replace_ops += 1
        self._op("swap", box, go)
        return n

    def carve(self, x1, y1, z1, x2, y2, z2, allow=CRAG, fill_with="air"):
        """Hollow a volume of natural ground.  Refused (problem) if the model shows anything else."""
        box = self._box(x1, y1, z1, x2, y2, z2)
        names = self.w.box_names(*box) - {"air"}
        foreign = names - set(allow)
        if foreign:
            self.problems.append("%s: carve %s would hit %s" % (self.sec, box, sorted(foreign)))
            return

        def go():
            for m in sorted(names):
                self.b.fill(*box, fill_with, mode="replace " + m)
                self.w.apply("fill %s %s %s replace %s" % (pos(*box[:3]), pos(*box[3:]), fill_with, m))
                self.stats["carve"] += 1
            self.replace_ops += len(names)
        self._op("carve", box, go)

    def pair(self, a, sa, b_, sb):
        """Two-part block (door, bed, tall plant): both cells must be air; the second half is only
        set if the first half is in place."""
        check_block(sa); check_block(sb)
        self._box(*a, *a); self._box(*b_, *b_)
        c1 = "execute if block %s air if block %s air run setblock %s %s strict" % (pos(*a), pos(*b_), pos(*a), sa)
        c2 = "execute if block %s %s if block %s air run setblock %s %s strict" % (pos(*a), sa, pos(*b_), pos(*b_), sb)
        box = (min(a[0], b_[0]), min(a[1], b_[1]), min(a[2], b_[2]), max(a[0], b_[0]), max(a[1], b_[1]), max(a[2], b_[2]))

        def go():
            for c in (c1, c2):
                if chat_len(c) > CHAT_LIMIT:
                    raise GenError("too long: " + c)
                self.b.raw(c)
            self.w.apply("setblock %s %s" % (pos(*a), sa))
            self.w.apply("setblock %s %s" % (pos(*b_), sb))
            self.stats["pair"] += 1
        self._op("keep", box, go)

    def door(self, x, y, z, kind, facing, hinge="left"):
        self.pair((x, y, z), "%s_door[half=lower,facing=%s,hinge=%s]" % (kind, facing, hinge),
                  (x, y + 1, z), "%s_door[half=upper,facing=%s,hinge=%s]" % (kind, facing, hinge))

    def bed(self, x, y, z, color, facing):
        v = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing]
        self.pair((x, y, z), "%s_bed[part=foot,facing=%s]" % (color, facing),
                  (x + v[0], y, z + v[1]), "%s_bed[part=head,facing=%s]" % (color, facing))

    DYE = {"dark_green": "green", "gold": "orange", "dark_red": "red", "dark_gray": "gray", "dark_purple": "purple",
           "dark_blue": "blue", "dark_aqua": "cyan", "aqua": "light_blue", "yellow": "yellow", "white": "white",
           "black": "black", "gray": "light_gray", "green": "lime", "red": "red"}

    def sign(self, x, y, z, block, lines, color="black", glow=False):
        """Waxed sign with its text inline (plain strings coloured by the sign's dye colour)."""
        msgs = ",".join(snbt_str(l) for l in (list(lines) + ["", "", "", ""])[:4])
        dye = self.DYE.get(color, color)
        nbt = '{front_text:{color:"%s",%smessages:[%s]},is_waxed:1b}' % (dye, "has_glowing_text:1b," if glow else "", msgs)
        self.put(x, y, z, block + nbt)
        self.stats["signs"] += 1

    # ------------------------------------------------------------------ entities
    def once(self, ident, etype, x, y, z, nbt="", yaw=None):
        """Summon exactly once: skipped when an entity with the tag lv3_<ident> is loaded."""
        check_reg("entity_type", etype)
        if ident in self.entity_ids:
            raise GenError("duplicate entity id " + ident)
        self.entity_ids.add(ident)
        self._reach(x, z, entity=True)
        self._protect(int(x // 1), int(y // 1), int(z // 1), int(x // 1), int(y // 1), int(z // 1))
        tag = "lv3_" + ident
        inner = nbt[1:-1] if nbt.startswith("{") else ""
        parts = ['Tags:["%s"]' % tag]
        if yaw is not None:
            parts.append("Rotation:[%.0ff,0f]" % yaw)
        if inner:
            parts.append(inner)
        cmd = "execute unless entity @e[tag=%s] run summon %s %s {%s}" % (tag, etype, pos(x, y, z), ",".join(parts))
        if chat_len(cmd) > CHAT_LIMIT:
            raise GenError("summon too long (%d): %s" % (chat_len(cmd), cmd))
        self.b.raw(cmd, 40)
        self.b.raw("tag @e[tag=%s] add lv3" % tag)       # the common tag, for finding every v3 entity
        self.w.apply(cmd)
        self.stats["summon"] += 1
        return tag

    def equip(self, tag, slot, item, comp=None):
        self.b.raw("item replace entity @e[tag=%s,limit=1] %s with %s" % (tag, slot, item_arg(item, comp)))

    def move_named(self, etype, name, near, radius, to, yaw=None):
        """Teleport an existing named entity (from an earlier layer) - idempotent by nature."""
        x, y, z = near
        self._reach(x, z, entity=True)
        sel = '@e[type=%s,name="%s",x=%s,y=%s,z=%s,distance=..%d,limit=1]' % (
            etype, name, "$x(%s)" % _n(x), "$y(%s)" % _n(y), "$z(%s)" % _n(z), radius)
        cmd = "tp %s %s%s" % (sel, pos(*to), (" %d 0" % yaw) if yaw is not None else "")
        self._raw(cmd)
        self.stats["tp_entity"] += 1

    # ------------------------------------------------------------------ containers
    def stock(self, x, y, z, items):
        """items: list of (slot, item_id, count[, components]).  A slot is only filled when empty."""
        self._reach(x, z)
        for it in items:
            slot, rid, cnt = it[0], it[1], it[2]
            comp = it[3] if len(it) > 3 else None
            cmd = "execute unless items block %s container.%d * run item replace block %s container.%d with %s %d" % (
                pos(x, y, z), slot, pos(x, y, z), slot, item_arg(rid, comp), cnt)
            if chat_len(cmd) > CHAT_LIMIT:
                raise GenError("stock too long (%d): %s" % (chat_len(cmd), cmd))
            self.b.raw(cmd)
            self.stats["stock"] += 1

    def lectern(self, x, y, z, facing, title, author, pages):
        """A lectern with a written book.  The lectern is placed with `keep` (only into air) holding a book
        of blank pages; each page is then *set* by index, so re-running rewrites the same text and never
        appends duplicates."""
        blank = ",".join('""' for _ in pages)
        nbt = '{Book:{id:"minecraft:written_book",components:{"minecraft:written_book_content":{title:%s,author:%s,pages:[%s]}}}}' % (
            snbt_str(title), snbt_str(author), blank)
        cmds = []
        for i, pg in enumerate(pages):
            cmds.append('data modify block %s Book.components."minecraft:written_book_content".pages[%d] set value %s'
                        % (pos(x, y, z), i, snbt_str(pg)))
        for c in cmds:
            if chat_len(c) > CHAT_LIMIT:
                raise GenError("page too long (%d): %s" % (chat_len(c), c))
        box = self._box(x, y, z, x, y, z)
        cmd = "setblock %s lectern[facing=%s,has_book=true]%s keep" % (pos(x, y, z), facing, nbt)
        if chat_len(cmd) > CHAT_LIMIT:
            raise GenError("lectern too long (%d): %s" % (chat_len(cmd), cmd))

        def go():
            self._raw(cmd)
            for c in cmds:
                self.b.raw(c)
            self.stats["books"] += 1
        self._op("keep", box, go)

    def mechanism(self, name, status, text):
        self.mechanisms.append((self.sec, name, status, text))

    # ------------------------------------------------------------------ queries
    def name(self, x, y, z):
        return self.w.name(x, y, z)

    def is_air(self, x1, y1, z1, x2=None, y2=None, z2=None):
        if x2 is None:
            return self.w.name(x1, y1, z1) == "air"
        return self._free(min(x1, x2), min(y1, y2), min(z1, z2), max(x1, x2), max(y1, y2), max(z1, z2))

    def ground(self, x, z, top=130, bottom=-30):
        """Highest y whose block is not air (the floor under an outdoor standing cell)."""
        for y in range(top, bottom, -1):
            if self.w.name(x, y, z) != "air":
                return y
        return None


def _n(v):
    if isinstance(v, float) and not v.is_integer():
        return ("%.3f" % v).rstrip("0").rstrip(".")
    return "%d" % int(v)


def restore_named(v, etype, name, x, y, z, nbt_inner):
    """Re-summon a named entity from an earlier layer only if no entity of that type and name is loaded."""
    v._reach(x, z, entity=True)
    cmd = 'execute unless entity @e[type=%s,name="%s"] run summon %s %s {CustomName:"%s",%s}' % (
        etype, name, etype, pos(x, y, z), name, nbt_inner)
    if chat_len(cmd) > CHAT_LIMIT:
        raise GenError("restore too long (%d): %s" % (chat_len(cmd), cmd))
    v.b.raw(cmd, 40)
    v.w.apply(cmd)
    v.stats["restore_guard"] += 1


# ---------------------------------------------------------------------------- lighting
def relight(v, box, target=8, interiors=True):
    """Keep the Lighting Overhaul's promise inside a v3 volume: every covered standing cell gets at least
    `target` block light, and no cell that v3 turned into a spawnable surface stays at block light 0.
    Uses the overhaul's own placement rules (ceiling coffer, wall sconce, floor inlay, lantern)."""
    import lighting as LG
    L = LG.Lighter(v.b, v.w, set())
    w = v.w
    x1, y1, z1, x2, y2, z2 = box
    before = set(v.w0.dark_spawn_cells(box)) if v.w0 is not None else set()
    for rnd in range(12):
        Lgt, sub, (ox, oy, oz) = w.block_light(box)
        nm = np.array([s.split("[", 1)[0] for s in w.states])
        feet_ok = np.array([n in LG.FEET_OK or n.endswith(LG.FEET_SUFFIX) for n in nm])
        head_ok = np.array([n in LG.FEET_OK for n in nm])
        opaque = w._class_luts()[1]
        solid = np.array([n not in ("air", "water", "lava", "light") and not n.endswith(("_carpet",)) for n in nm])
        S = sub
        feet = feet_ok[S]
        head = np.roll(head_ok[S], -1, axis=1)
        below = np.roll(solid[S], 1, axis=1)
        op = opaque[S]
        covered = np.flip(np.cumsum(np.flip(op, axis=1), axis=1), axis=1) > 0
        covered = np.roll(covered, -2, axis=1)
        lite = np.maximum(Lgt, np.roll(Lgt, -1, axis=1))
        dark = feet & head & below & covered & (lite < target)
        dark = dark[x1 - ox:x2 - ox + 1, y1 - oy:y2 - oy + 1, z1 - oz:z2 - oz + 1]
        pts = [(int(p[0]) + x1, int(p[1]) + y1, int(p[2]) + z1) for p in np.argwhere(dark)] if interiors else []
        # new outdoor spawn surfaces (roofs, stall tops) at block light 0
        pts += [p for p in w.dark_spawn_cells(box) if p not in before]
        pts = [p for p in pts if not v._in_protected(*p)]
        if not pts:
            break
        batch = set()
        n = 0
        for (x, y, z) in pts:
            key = (x // 5, y // 6, z // 5)
            if key in batch:
                continue
            if LG.place_for(L, x, y, z):
                batch.add(key)
                n += 1
        if n == 0:
            break
    v.stats["lights"] += L.count
    return L.count
