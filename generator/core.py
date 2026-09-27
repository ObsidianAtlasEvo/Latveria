"""Core command-emitting engine for the Latveria build.

Output target: a plain list of chat commands that a Windows automation script
types into Minecraft one by one.  That shapes everything here:

* Coordinates are written as tokens  $x(12) $y(-3) $z(150)  - offsets from the
  centre block.  The PowerShell sender asks for the centre's X Y Z and turns
  each token into an absolute coordinate, so it does not matter if the player
  moves, falls or is teleported during the build.
* Minecraft's chat box accepts at most 256 characters.  Anything longer is
  split automatically: chest contents become one `item replace` per slot,
  banner patterns / book pages / sign lines are appended with `data modify`,
  armour-stand gear is equipped with `item replace entity`.  Every finished
  line is checked against the limit (assuming 8-character coordinates).
* Every block state is validated against the Minecraft 26.1.2 block registry
  (mcdata/blocks.json, extracted from the game's data), every item, entity,
  loot table and feature id against the 26.1.2 registries.
"""
import json
import math
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
BLOCKS = json.load(open(os.path.join(HERE, "mcdata", "blocks.json")))
REG = json.load(open(os.path.join(HERE, "mcdata", "registries.json")))

MAX_FILL = 32768     # default max_block_modifications game rule
CHAT_LIMIT = 256     # chat input box limit
COORD_W = 8          # worst-case printed width of one absolute coordinate

FACINGS = ["north", "east", "south", "west"]


class GenError(Exception):
    pass


# --------------------------------------------------------------------------
# validation
# --------------------------------------------------------------------------
_BLOCK_RE = re.compile(r"^(?:minecraft:)?([a-z0-9_]+)(\[[^\]]*\])?(\{.*\})?$", re.S)


def parse_block(spec):
    m = _BLOCK_RE.match(spec)
    if not m:
        raise GenError("unparseable block: %r" % spec)
    name, props, nbt = m.group(1), m.group(2), m.group(3)
    pd = {}
    if props:
        body = props[1:-1].strip()
        if body:
            for kv in body.split(","):
                k, v = kv.split("=")
                pd[k.strip()] = v.strip()
    return name, pd, nbt


def check_block(spec):
    name, pd, _ = parse_block(spec)
    if name not in BLOCKS:
        raise GenError("unknown block %r in %r" % (name, spec))
    allowed = BLOCKS[name][0]
    for k, v in pd.items():
        if k not in allowed:
            raise GenError("block %s has no property %s (%r)" % (name, k, spec))
        if v not in allowed[k]:
            raise GenError("block %s property %s=%s invalid (%r)" % (name, k, v, spec))
    return name, pd


def join_block(name, pd, nbt=None):
    s = name
    if pd:
        s += "[" + ",".join("%s=%s" % kv for kv in pd.items()) + "]"
    if nbt:
        s += nbt
    return s


def check_reg(kind, rid):
    rid = rid.replace("minecraft:", "")
    if rid not in REG[kind]:
        raise GenError("unknown %s %r" % (kind, rid))
    return "minecraft:" + rid


_ID_RE = re.compile(r'id:"minecraft:([a-z0-9_]+)"')


def check_item_ids(text):
    for m in _ID_RE.finditer(text):
        check_reg("item", m.group(1))


def item_arg(rid, components=None):
    """An item stack argument for /item and /give: minecraft:x[comp=val,...]"""
    s = check_reg("item", rid)
    if components:
        s += "[" + components + "]"
    return s


def rot_facing(f, r):
    if f in FACINGS:
        return FACINGS[(FACINGS.index(f) + r) % 4]
    return f


def rotate_state(spec, r):
    """Rotate a block state clockwise (seen from above) by r quarter turns."""
    if r % 4 == 0:
        return spec
    name, pd, nbt = parse_block(spec)
    out = {}
    for k, v in pd.items():
        if k == "facing":
            v = rot_facing(v, r)
        elif k == "axis" and r % 2 == 1 and v in ("x", "z"):
            v = "z" if v == "x" else "x"
        elif k == "rotation":
            v = str((int(v) + 4 * r) % 16)
        out[k] = v
    return join_block(name, out, nbt)


# --------------------------------------------------------------------------
# coordinate tokens
# --------------------------------------------------------------------------
def _num(v):
    if isinstance(v, float) and not v.is_integer():
        return ("%.3f" % v).rstrip("0").rstrip(".")
    return "%d" % int(v)


def cx(v):
    return "$x(%s)" % _num(v)


def cy(v):
    return "$y(%s)" % _num(v)


def cz(v):
    return "$z(%s)" % _num(v)


def pos(x, y, z):
    return "%s %s %s" % (cx(x), cy(y), cz(z))


_TOKEN_RE = re.compile(r"\$[xyz]\(-?[0-9.]+\)")


def chat_len(cmd):
    """Length once typed into chat: leading '/' plus coordinates at worst-case width."""
    return 1 + len(_TOKEN_RE.sub("X" * COORD_W, cmd))


# --------------------------------------------------------------------------
# NBT payload markers.  Helpers return these; Builder.set() expands them into
# as many short commands as needed.
# --------------------------------------------------------------------------
def _marker(kind, payload):
    return "{@@%s@@%s}" % (kind, json.dumps(payload))


def _unmarker(nbt):
    m = re.match(r"^\{@@([A-Z]+)@@(.*)\}$", nbt, re.S)
    if not m:
        return None, None
    return m.group(1), json.loads(m.group(2))


def chest_items(items):
    """items: list of (item_id, count[, components]) placed in consecutive slots."""
    for it in items:
        check_reg("item", it[0])
    return _marker("ITEMS", [list(it) for it in items])


def loot(table):
    check_reg("loot_table", table)
    return '{LootTable:"minecraft:%s"}' % table


def banner(patterns):
    for p, _ in patterns:
        check_reg("banner_pattern", p)
    return _marker("BANNER", patterns)


def book(title, author, pages):
    return _marker("BOOK", {"title": title, "author": author, "pages": pages})


def sign(lines, color="black", glow=False):
    return _marker("SIGN", {"lines": (list(lines) + ["", "", "", ""])[:4], "color": color, "glow": glow})


def snbt_str(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def tc(text, color=None, bold=False, italic=None):
    parts = ["text:" + snbt_str(text)]
    if color:
        parts.append("color:" + snbt_str(color))
    if bold:
        parts.append("bold:1b")
    if italic is not None:
        parts.append("italic:%s" % ("1b" if italic else "0b"))
    return "{" + ",".join(parts) + "}"


# --------------------------------------------------------------------------
# builder
# --------------------------------------------------------------------------
class Frame:
    def __init__(self, ox, oy, oz, r):
        self.ox, self.oy, self.oz, self.r = ox, oy, oz, r % 4

    def pt(self, x, y, z):
        for _ in range(self.r):
            x, z = -z, x
        return x + self.ox, y + self.oy, z + self.oz


class Builder:
    def __init__(self):
        self.sections = []
        self.cur = None
        self.frames = []
        self.stats = {"commands": 0, "blocks": 0}
        self.tag_n = 0
        self.later = []      # mob summons deferred until every block is in place

    # ---- sections -------------------------------------------------------
    def section(self, name, title=None):
        self.cur = {"name": name, "title": title or name, "cmds": []}
        self.sections.append(self.cur)

    def raw(self, text, cost=1):
        n = chat_len(text)
        if n > CHAT_LIMIT:
            raise GenError("command too long for chat (%d chars): %s" % (n, text))
        self.cur["cmds"].append((text, cost))
        self.stats["commands"] += 1

    def wait(self, ms, note=""):
        self.cur["cmds"].append(("!wait %d %s" % (ms, note), 0))

    def comment(self, text):
        pass

    # ---- frames ---------------------------------------------------------
    class _FrameCtx:
        def __init__(self, b, f):
            self.b, self.f = b, f

        def __enter__(self):
            self.b.frames.append(self.f)
            return self.b

        def __exit__(self, *a):
            self.b.frames.pop()

    def frame(self, ox, oy, oz, r=0):
        return Builder._FrameCtx(self, Frame(ox, oy, oz, r))

    def tp(self, x, y, z):
        for f in reversed(self.frames):
            x, y, z = f.pt(x, y, z)
        return x, y, z

    def rot(self):
        return sum(f.r for f in self.frames) % 4

    def tr_state(self, spec):
        return rotate_state(spec, self.rot())

    def tr_yaw(self, yaw):
        return (yaw + 90 * self.rot()) % 360

    # ---- primitives ------------------------------------------------------
    def fill(self, x1, y1, z1, x2, y2, z2, block, mode=None):
        check_block(block)
        block = self.tr_state(block)
        if mode and mode.startswith("replace "):
            flt = mode[8:]
            if not flt.startswith("#"):
                check_block(flt)
                mode = "replace " + self.tr_state(flt)
        if mode in ("hollow", "outline"):
            raise GenError("use walls/box_outline helpers instead")
        ax, ay, az = self.tp(x1, y1, z1)
        bx, by, bz = self.tp(x2, y2, z2)
        self._fill_world(min(ax, bx), min(ay, by), min(az, bz),
                         max(ax, bx), max(ay, by), max(az, bz), block, mode)

    def _fill_world(self, x1, y1, z1, x2, y2, z2, block, mode):
        dx, dy, dz = x2 - x1 + 1, y2 - y1 + 1, z2 - z1 + 1
        vol = dx * dy * dz
        if vol > MAX_FILL:
            if dx >= dy and dx >= dz:
                m = x1 + dx // 2
                self._fill_world(x1, y1, z1, m - 1, y2, z2, block, mode)
                self._fill_world(m, y1, z1, x2, y2, z2, block, mode)
            elif dz >= dy:
                m = z1 + dz // 2
                self._fill_world(x1, y1, z1, x2, y2, m - 1, block, mode)
                self._fill_world(x1, y1, m, x2, y2, z2, block, mode)
            else:
                m = y1 + dy // 2
                self._fill_world(x1, y1, z1, x2, m - 1, z2, block, mode)
                self._fill_world(x1, m, z1, x2, y2, z2, block, mode)
            return
        if vol == 1 and not mode:
            self.raw("setblock %s %s" % (pos(x1, y1, z1), block), 1)
        else:
            self.raw("fill %s %s %s%s" % (pos(x1, y1, z1), pos(x2, y2, z2), block,
                                           (" " + mode) if mode else ""), vol)
        self.stats["blocks"] += vol

    def set(self, x, y, z, block, strict=False):
        name, pd, nbt = parse_block(block)
        check_block(block)
        kind, payload = _unmarker(nbt) if nbt else (None, None)
        if nbt:
            check_item_ids(nbt)
        base = join_block(name, pd, None if kind else nbt)
        base = self.tr_state(base)
        wx, wy, wz = self.tp(x, y, z)
        P = pos(wx, wy, wz)
        sfx = " strict" if strict else ""
        self.stats["blocks"] += 1
        if kind is None:
            self.raw("setblock %s %s%s" % (P, base, sfx), 1)
            return
        if kind == "ITEMS":
            self.raw("setblock %s %s%s" % (P, base, sfx), 1)
            for slot, it in enumerate(payload):
                rid, cnt = it[0], it[1]
                comp = it[2] if len(it) > 2 else None
                self.raw("item replace block %s container.%d with %s %d"
                         % (P, slot, item_arg(rid, comp), cnt), 1)
        elif kind == "BANNER":
            inline = "{patterns:[%s]}" % ",".join(
                '{pattern:"%s",color:"%s"}' % (p, c_) for p, c_ in payload)
            cmd = "setblock %s %s%s%s" % (P, base, inline, sfx)
            if chat_len(cmd) <= CHAT_LIMIT:
                self.raw(cmd, 1)
            else:
                self.raw("setblock %s %s%s" % (P, base, sfx), 1)
                for p, c_ in payload:
                    self.raw('data modify block %s patterns append value {pattern:"%s",color:"%s"}'
                             % (P, p, c_), 1)
        elif kind == "SIGN":
            msgs = [tc(l, payload["color"]) if l else '""' for l in payload["lines"]]
            glow = "1b" if payload["glow"] else "0b"
            inline = "{front_text:{messages:[%s],has_glowing_text:%s},is_waxed:1b}" % (",".join(msgs), glow)
            cmd = "setblock %s %s%s%s" % (P, base, inline, sfx)
            if chat_len(cmd) <= CHAT_LIMIT:
                self.raw(cmd, 1)
            else:
                self.raw("setblock %s %s{is_waxed:1b}%s" % (P, base, sfx), 1)
                for i, m in enumerate(msgs):
                    if m != '""':
                        self.raw("data modify block %s front_text.messages[%d] set value %s" % (P, i, m), 1)
                if payload["glow"]:
                    self.raw("data modify block %s front_text.has_glowing_text set value 1b" % P, 1)
        elif kind == "BOOK":
            self.raw("setblock %s %s%s" % (P, base, sfx), 1)
            self.raw('data modify block %s Book set value {id:"minecraft:written_book",count:1,'
                     'components:{"minecraft:written_book_content":{title:{raw:%s},author:%s,pages:[]}}}'
                     % (P, snbt_str(payload["title"]), snbt_str(payload["author"])), 1)
            for page in split_pages(payload["pages"]):
                self.raw('data modify block %s Book.components."minecraft:written_book_content".pages '
                         'append value {raw:{text:%s}}' % (P, snbt_str(page)), 1)
        else:
            raise GenError("unknown marker " + kind)

    def air(self, x1, y1, z1, x2, y2, z2):
        self.fill(x1, y1, z1, x2, y2, z2, "air")

    def walls(self, x1, y1, z1, x2, y2, z2, block):
        """Four vertical walls of a box (no floor or ceiling)."""
        x1, x2 = sorted((x1, x2)); z1, z2 = sorted((z1, z2))
        self.fill(x1, y1, z1, x2, y2, z1, block)
        self.fill(x1, y1, z2, x2, y2, z2, block)
        if z2 - z1 > 1:
            self.fill(x1, y1, z1 + 1, x1, y2, z2 - 1, block)
            self.fill(x2, y1, z1 + 1, x2, y2, z2 - 1, block)

    # ---- multi-part blocks (placed strict so halves are not dropped) ----
    def door(self, x, y, z, wood, facing, hinge="left", iron=False):
        name = "iron_door" if iron else wood + "_door"
        self.set(x, y, z, "%s[half=lower,facing=%s,hinge=%s]" % (name, facing, hinge), strict=True)
        self.set(x, y + 1, z, "%s[half=upper,facing=%s,hinge=%s]" % (name, facing, hinge), strict=True)

    def bed(self, x, y, z, color, facing):
        """Bed whose foot is at (x,y,z) and whose head is one block toward `facing`."""
        v = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}[facing]
        self.set(x, y, z, "%s_bed[part=foot,facing=%s]" % (color, facing), strict=True)
        self.set(x + v[0], y, z + v[1], "%s_bed[part=head,facing=%s]" % (color, facing), strict=True)

    def tall_plant(self, x, y, z, name):
        self.set(x, y, z, "%s[half=lower]" % name, strict=True)
        self.set(x, y + 1, z, "%s[half=upper]" % name, strict=True)

    # ---- entities --------------------------------------------------------
    def summon(self, etype, x, y, z, nbt="", yaw=None):
        check_reg("entity_type", etype)
        check_item_ids(nbt)
        wx, wy, wz = self.tp(x, y, z)
        if yaw is not None:
            rot = "Rotation:[%.0ff,0f]" % self.tr_yaw(yaw)
            nbt = ("{" + rot + "," + nbt[1:]) if nbt.startswith("{") and len(nbt) > 2 else "{" + rot + "}"
        self.raw(("summon %s %s %s" % (etype, pos(wx, wy, wz), nbt)).rstrip(), 40)

    def summon_later(self, etype, x, y, z, nbt=""):
        """Queue a living mob (villager, animal, golem) for the final population pass,
        so nothing wanders into areas that are still being built."""
        check_reg("entity_type", etype)
        check_item_ids(nbt)
        wx, wy, wz = self.tp(x, y, z)
        cmd = ("summon %s %s %s" % (etype, pos(wx, wy, wz), nbt)).rstrip()
        if chat_len(cmd) > CHAT_LIMIT:
            raise GenError("command too long: " + cmd)
        self.later.append(cmd)

    def armor_stand(self, x, y, z, yaw, name, equip, extra=""):
        """Summon an armour stand, then equip it slot by slot (keeps each line short).
        equip: dict slot -> (item_id, components or None); slots: head chest legs feet mainhand offhand"""
        self.tag_n += 1
        tag = "lv%d" % self.tag_n
        nbt = '{Tags:["%s"],ShowArms:1b,NoBasePlate:1b,CustomName:%s%s}' % (
            tag, snbt_str(name), ("," + extra) if extra else "")
        self.summon("armor_stand", x, y, z, nbt, yaw=yaw)
        slotname = {"head": "armor.head", "chest": "armor.chest", "legs": "armor.legs", "feet": "armor.feet",
                    "mainhand": "weapon.mainhand", "offhand": "weapon.offhand"}
        for slot, (rid, comp) in equip.items():
            self.raw("item replace entity @e[type=armor_stand,tag=%s,limit=1] %s with %s"
                     % (tag, slotname[slot], item_arg(rid, comp)), 1)

    def ring(self, x, y, z, r, thick, block):
        for dx, z1, z2 in ring_runs(r, thick):
            self.fill(x + dx, y, z + z1, x + dx, y, z + z2, block)

    def cone(self, x, y0, z, r, h, block, tip=None):
        """Solid cone of height h on a disk of radius r; layers with the same
        footprint are merged into single tall fills."""
        layers = []
        for k in range(h):
            rk = r * (1 - k / float(h))
            layers.append(tuple(disk_runs(rk)) if rk >= 0.6 else ((0, 0, 0),))
        k = 0
        while k < h:
            j = k
            while j + 1 < h and layers[j + 1] == layers[k]:
                j += 1
            for dx, z1, z2 in layers[k]:
                self.fill(x + dx, y0 + k, z + z1, x + dx, y0 + j, z + z2, block)
            k = j + 1
        self.set(x, y0 + h, z, block)
        if tip:
            self.set(x, y0 + h + 1, z, tip)

    def feature(self, fid, x, y, z):
        check_reg("worldgen/configured_feature", fid)
        wx, wy, wz = self.tp(x, y, z)
        self.raw("place feature minecraft:%s %s" % (fid, pos(wx, wy, wz)), 400)


def split_pages(pages, limit=95):
    out = []
    for p in pages:
        while len(p) > limit:
            cut = p.rfind(" ", 0, limit)
            if cut < 40:
                cut = limit
            out.append(p[:cut].rstrip())
            p = p[cut:].lstrip()
        if p:
            out.append(p)
    return out


# --------------------------------------------------------------------------
# geometry helpers
# --------------------------------------------------------------------------
def disk_runs(r, inner=-1.0):
    """Yield (dx, dz1, dz2) z-runs of the cells with inner < dist <= r+0.5."""
    R = int(math.ceil(r + 1))
    for dx in range(-R, R + 1):
        run = None
        for dz in range(-R, R + 2):
            d = math.hypot(dx, dz)
            inside = (dz <= R) and (d <= r + 0.5) and (d > inner)
            if inside and run is None:
                run = dz
            elif not inside and run is not None:
                yield dx, run, dz - 1
                run = None


def ring_runs(r, thick=2.0):
    """(dx, dz1, dz2) z-runs covering ring_cells(r, thick)."""
    cells = set(ring_cells(r, thick))
    for dx in sorted({c[0] for c in cells}):
        zs = sorted(dz for (x, dz) in cells if x == dx)
        start = prev = zs[0]
        for z in zs[1:]:
            if z != prev + 1:
                yield dx, start, prev
                start = z
            prev = z
        yield dx, start, prev


def ring_cells(r, thick=2.0):
    cells = []
    R = int(math.ceil(r + 1))
    for dx in range(-R, R + 1):
        for dz in range(-R, R + 1):
            d = math.hypot(dx, dz)
            if r + 0.5 - thick < d <= r + 0.5:
                cells.append((dx, dz))
    return cells
