"""Model authoring: bones and box-UV cubes in Bedrock geometry space, packed and exported as
Bedrock ``format_version 1.12.0`` geometry (the format GeckoLib's Blockbench plugin writes).

Coordinate conventions (Bedrock geometry space, units = model pixels, 16 per block):
  +y up, the model's FRONT faces -z (the "north" face), the model's RIGHT side is -x.
  Cube ``origin`` is the minimum corner. Bone ``pivot`` is absolute (not relative to the parent).
  Rotations are Euler degrees; see render.py for how they are applied.

Box UV layout for a cube of size (w, h, d) at uv (u, v) - the standard Minecraft layout:
    row 0 (height d):  [ d pad ][ top  w ][ bottom w ]
    row 1 (height h):  [ right d ][ front w ][ left d ][ back w ]
"""
import json
import math


class Cube:
    def __init__(self, name, origin, size, material, inflate=0.0, deco=None, mirror=False):
        self.name = name
        self.origin = [float(c) for c in origin]
        self.size = [int(s) for s in size]
        if any(float(s) != int(s) for s in size):
            raise ValueError("%s: box-UV cubes need integer sizes (use inflate for fractions)" % name)
        self.material = material
        self.inflate = float(inflate)
        self.deco = deco            # decoration key understood by the painter
        self.mirror = mirror
        self.uv = None
        self.share = None           # a cube whose UV region this cube reuses (mirrored limbs)
        self.bone = None

    def region(self):
        w, h, d = self.size
        return max(1, 2 * (d + w)), max(1, d + h)

    def faces(self):
        """Face name -> (u, v, width, height) texture rectangle."""
        w, h, d = self.size
        u, v = self.uv
        return {
            "top": (u + d, v, w, d),
            "bottom": (u + d + w, v, w, d),
            "right": (u, v + d, d, h),
            "front": (u + d, v + d, w, h),
            "left": (u + d + w, v + d, d, h),
            "back": (u + 2 * d + w, v + d, w, h),
        }


class Bone:
    def __init__(self, name, parent, pivot, rotation=(0, 0, 0), dof=None, desc=""):
        self.name = name
        self.parent = parent
        self.pivot = [float(p) for p in pivot]
        self.rotation = [float(r) for r in rotation]
        self.cubes = []
        # rotation limits in degrees per axis, used by the animation validator
        self.dof = dof or {}
        self.desc = desc

    def cube(self, *a, **k):
        c = Cube(*a, **k)
        c.bone = self
        self.cubes.append(c)
        return c


class Model:
    def __init__(self, identifier, tex_w, tex_h):
        self.identifier = identifier
        self.tex_w = tex_w
        self.tex_h = tex_h
        self.bones = []
        self.by_name = {}

    def bone(self, name, parent, pivot, rotation=(0, 0, 0), dof=None, desc=""):
        if name in self.by_name:
            raise ValueError("duplicate bone " + name)
        if parent is not None and parent not in self.by_name:
            raise ValueError("bone %s: parent %s must be declared first" % (name, parent))
        b = Bone(name, parent, pivot, rotation, dof, desc)
        self.bones.append(b)
        self.by_name[name] = b
        return b

    def cubes(self):
        for b in self.bones:
            for c in b.cubes:
                yield c

    # ---- mirroring ----------------------------------------------------------------------------
    def mirror(self, root_name, rename):
        """Mirrors a bone subtree across x = 0. ``rename(name) -> new name``. Mirrored cubes reuse
        the source UV with the mirror flag, like vanilla's left limbs."""
        order = []
        todo = [root_name]
        while todo:
            n = todo.pop(0)
            order.append(n)
            todo.extend(b.name for b in self.bones if b.parent == n)
        for n in order:
            src = self.by_name[n]
            # the subtree root keeps its parent (e.g. a cloak column under the shared cloak root)
            parent = src.parent if n == root_name else rename(src.parent)
            dof = {}
            for ax, (lo, hi) in src.dof.items():
                dof[ax] = (lo, hi) if ax == "x" else (-hi, -lo)
            b = self.bone(rename(n), parent, (-src.pivot[0], src.pivot[1], src.pivot[2]),
                          (src.rotation[0], -src.rotation[1], -src.rotation[2]), dof, src.desc.replace("right", "left").replace("Right", "Left"))
            for c in src.cubes:
                m = b.cube(rename(c.name), (-(c.origin[0] + c.size[0]), c.origin[1], c.origin[2]), c.size, c.material,
                           c.inflate, c.deco, not c.mirror)
                m.share = c

    # ---- UV packing -----------------------------------------------------------------------------
    def pack(self, pad=0):
        own = [c for c in self.cubes() if c.share is None]
        own.sort(key=lambda c: (-c.region()[1], -c.region()[0], c.name))
        x = y = shelf_h = 0
        for c in own:
            rw, rh = c.region()
            if x + rw > self.tex_w:
                x = 0
                y += shelf_h + pad
                shelf_h = 0
            if y + rh > self.tex_h or rw > self.tex_w:
                raise ValueError("texture %dx%d too small at cube %s" % (self.tex_w, self.tex_h, c.name))
            c.uv = (x, y)
            x += rw + pad
            shelf_h = max(shelf_h, rh)
        for c in self.cubes():
            if c.share is not None:
                c.uv = c.share.uv
        used = sum(c.region()[0] * c.region()[1] for c in own)
        return used / float(self.tex_w * self.tex_h)

    # ---- export ---------------------------------------------------------------------------------
    def to_json(self):
        bones = []
        for b in self.bones:
            j = {"name": b.name}
            if b.parent:
                j["parent"] = b.parent
            j["pivot"] = [r(p) for p in b.pivot]
            if any(b.rotation):
                j["rotation"] = [r(a) for a in b.rotation]
            if b.cubes:
                cs = []
                for c in b.cubes:
                    cj = {"origin": [r(o) for o in c.origin], "size": c.size, "uv": list(c.uv)}
                    if c.inflate:
                        cj["inflate"] = r(c.inflate)
                    if c.mirror:
                        cj["mirror"] = True
                    cs.append(cj)
                j["cubes"] = cs
            bones.append(j)
        return {
            "format_version": "1.12.0",
            "minecraft:geometry": [{
                "description": {
                    "identifier": self.identifier,
                    "texture_width": self.tex_w,
                    "texture_height": self.tex_h,
                    "visible_bounds_width": 3,
                    "visible_bounds_height": 3.5,
                    "visible_bounds_offset": [0, 1.5, 0],
                },
                "bones": bones,
            }],
        }

    def write(self, path):
        with open(path, "w") as f:
            json.dump(self.to_json(), f, indent=1)
            f.write("\n")

    # ---- checks ---------------------------------------------------------------------------------
    def validate(self):
        problems = []
        names = set()
        for b in self.bones:
            if b.name in names:
                problems.append("duplicate bone " + b.name)
            names.add(b.name)
            if b.parent is not None and b.parent not in names:
                problems.append("bone %s parent %s missing or declared later" % (b.name, b.parent))
            for v in b.pivot + b.rotation:
                if not math.isfinite(v):
                    problems.append("non-finite value in " + b.name)
        occupied = {}
        for c in self.cubes():
            if c.uv is None:
                problems.append("cube %s not packed" % c.name)
                continue
            if any(s < 0 for s in c.size):
                problems.append("negative size " + c.name)
            rw, rh = c.region()
            u, v = c.uv
            if u < 0 or v < 0 or u + rw > self.tex_w or v + rh > self.tex_h:
                problems.append("cube %s UV outside texture" % c.name)
            if c.share is None:
                for (fu, fv, fw, fh) in c.faces().values():
                    for yy in range(fv, fv + fh):
                        for xx in range(fu, fu + fw):
                            if (xx, yy) in occupied and occupied[(xx, yy)] is not c:
                                problems.append("UV overlap %s / %s" % (c.name, occupied[(xx, yy)].name))
                                break
                            occupied[(xx, yy)] = c
        return sorted(set(problems))

    def children(self, name):
        return [b for b in self.bones if b.parent == name]


def r(x):
    x = round(float(x), 4)
    return int(x) if x == int(x) else x
