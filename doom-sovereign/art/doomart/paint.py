"""Procedural pixel-art painter for box-UV models.

Every face is painted as a small grid of palette names, never with gradients or noise: flat
material colour, a one-pixel top-left light (highlight on the upper and left edges, recess on the
lower and right edges), deliberate seams and rivets, and hand-placed decorations for the faces
that matter (the mask, buckle, chest, gauntlets). The same painter produces the base texture,
damage variants and the emissive glow masks, so every variant lines up pixel for pixel.

Face grids: ``g[y][x]``; for side faces y = 0 is the top of the face and x runs along the UV
direction documented in geo.py; for the top face y = 0 is the back edge; for the bottom face
y = 0 is the front edge.
"""
import hashlib
import random

import numpy as np

from .palette import COLORS

SIDE_FACES = ("front", "back", "left", "right")


def seed_for(*parts):
    return int(hashlib.sha1("|".join(parts).encode()).hexdigest()[:12], 16)


def grid(w, h, fill):
    return [[fill] * w for _ in range(h)]


# ---- materials -------------------------------------------------------------------------------------
def steel(face, w, h, rng, base="steel"):
    g = grid(w, h, base)
    if face == "top":
        g = grid(w, h, "steel_mid")
        if h:
            g[h - 1] = ["steel_hi"] * w       # front edge catches the light
        return g
    if face == "bottom":
        return grid(w, h, "steel_recess")
    if w >= 2 and h >= 2:
        for x in range(w):
            g[0][x] = "steel_hi"
            g[h - 1][x] = "steel_recess"
        for y in range(1, h - 1):
            g[y][0] = "steel_mid"
            if w >= 3:
                g[y][w - 1] = "steel_recess"
    elif h == 1 and w >= 1:
        g[0] = ["steel_mid"] * w
    # large plates get a seam and rivets
    if w >= 6 and h >= 5:
        sy = h // 2
        for x in range(1, w - 1):
            g[sy][x] = "steel_recess"
            g[sy + 1][x] = "steel_mid" if g[sy + 1][x] == base else g[sy + 1][x]
    if w >= 5 and h >= 4:
        for (x, y) in ((1, 1), (w - 2, 1)):
            g[y][x] = "steel_hi"
            if y + 1 < h - 1:
                g[y + 1][x] = "steel_recess"
    # sparse wear marks: at most one per ~40 px, never on the edge rows
    for _ in range((w * h) // 40):
        x, y = rng.randrange(1, max(2, w - 1)), rng.randrange(1, max(2, h - 1))
        if 0 < x < w - 1 and 0 < y < h - 1 and g[y][x] == base:
            g[y][x] = "steel_mid"
    return g


def polished(face, w, h, rng):
    """The mask and other hero plates: lighter steel, bevelled, no seams, rivets or wear marks."""
    if face == "bottom":
        return grid(w, h, "steel_recess")
    g = grid(w, h, "steel_mid")
    if face == "top":
        if h:
            g[h - 1] = ["steel_hi"] * w
        return g
    if h >= 2:
        g[0] = ["steel_hi"] * w
        g[h - 1] = ["steel"] * w
    if w >= 3:
        for y in range(1, h):
            g[y][w - 1] = "steel"
    return g


def steel_dark(face, w, h, rng):
    g = steel(face, w, h, rng, base="steel_recess")
    for y in range(h):
        for x in range(w):
            if g[y][x] == "steel_hi" and face != "top":
                g[y][x] = "steel_mid"
    return g


def brass(face, w, h, rng):
    g = grid(w, h, "brass")
    if face == "bottom":
        return grid(w, h, "brass_lo")
    if face == "top":
        if h:
            g[h - 1] = ["brass_hi"] * w
        return g
    if h >= 2:
        g[0] = ["brass_hi"] * w
        g[h - 1] = ["brass_lo"] * w
    if w >= 3:
        for y in range(1, h - 1):
            g[y][w - 1] = "brass_lo"
    return g


def cloth(face, w, h, rng, inner=False):
    base, light, crease, hi = ("cloth_shadow", "green_dark", "cloth_shadow", "green") if inner else \
        ("green_dark", "green", "cloth_shadow", "green_hi")
    g = grid(w, h, base)
    if face == "bottom":
        return grid(w, h, "cloth_shadow")
    phase = rng.randrange(4)
    if face == "top":
        for y in range(h):
            for x in range(w):
                g[y][x] = light if (x + phase) % 4 < 2 else base
        return g
    for x in range(w):
        k = (x + phase) % 4
        col = light if k < 2 else base
        for y in range(h):
            g[y][x] = col
        if k == 1 and h >= 3:           # fold ridge: highlight near the top, crease line beside it
            g[0][x] = hi
        if k == 2:
            for y in range(1, h):
                g[y][x] = crease if y % 3 != 0 else base
    if h >= 2:
        g[h - 1] = [crease] * w        # hem shadow
    return g


def glass(face, w, h, rng):
    return grid(w, h, "glass_dark")


def blank(face, w, h, rng):
    return grid(w, h, None)


MATERIALS = {
    "steel": steel,
    "steel_dark": steel_dark,
    "polished": polished,
    "brass": brass,
    "cloth": cloth,
    "cloth_inner": lambda f, w, h, rng: cloth(f, w, h, rng, inner=True),
    "glass": glass,
    "glow_only": blank,    # geometry that exists only in the emissive pass (eye flare planes)
}


# ---- the painter -----------------------------------------------------------------------------------
class Painter:
    """Paints a packed model. ``decorations`` maps a deco key to ``fn(ctx)`` where ctx gives the
    face grids of that cube, the glow grids, the state and an rng."""

    def __init__(self, model, decorations, damage=0, glow="powered"):
        self.model = model
        self.decorations = decorations
        self.damage = damage          # 0 pristine, 1 moderate, 2 severe
        self.glow = glow              # "off", "low", "powered", "arcane"

    def paint(self):
        m = self.model
        base = np.zeros((m.tex_h, m.tex_w, 4), dtype=np.uint8)
        glowimg = np.zeros((m.tex_h, m.tex_w, 4), dtype=np.uint8)
        for c in m.cubes():
            if c.share is not None:
                continue
            rng = random.Random(seed_for(m.identifier, c.name))
            faces = c.faces()
            grids = {f: MATERIALS[c.material](f, fw, fh, rng) for f, (fu, fv, fw, fh) in faces.items()}
            glows = {f: grid(fw, fh, None) for f, (fu, fv, fw, fh) in faces.items()}
            ctx = Ctx(c, grids, glows, self, rng)
            if c.deco:
                for key in c.deco.split("+"):
                    self.decorations[key](ctx)
            if self.damage and c.material in ("steel", "steel_dark", "polished", "brass", "cloth", "cloth_inner"):
                wear(ctx, self.damage)
            for f, (fu, fv, fw, fh) in faces.items():
                for y in range(fh):
                    for x in range(fw):
                        n = grids[f][y][x]
                        if n is not None:
                            base[fv + y, fu + x] = COLORS[n] + (255,)
                        gn = glows[f][y][x]
                        if gn is not None:
                            glowimg[fv + y, fu + x] = COLORS[gn] + (255,)
        return base, glowimg


class Ctx:
    def __init__(self, cube, grids, glows, painter, rng):
        self.cube = cube
        self.g = grids
        self.glow = glows
        self.painter = painter
        self.rng = rng

    @property
    def state(self):
        return self.painter.glow

    @property
    def damage(self):
        return self.painter.damage

    def size(self, face):
        g = self.g[face]
        return (len(g[0]) if g else 0), len(g)

    def put(self, face, x, y, name):
        w, h = self.size(face)
        if 0 <= x < w and 0 <= y < h:
            self.g[face][y][x] = name

    def shine(self, face, x, y, name):
        w, h = self.size(face)
        if 0 <= x < w and 0 <= y < h:
            self.glow[face][y][x] = name

    def glow_level(self, powered="arcane", low="arcane_dim"):
        """Colour for an emitter pixel in the current glow state (None = dark)."""
        return {"off": None, "low": low, "powered": powered, "arcane": powered}[self.state]


def wear(ctx, level):
    """Battle damage: scratches (moderate), plus dents, cracks and scorch (severe). Placed with a
    per-cube seed so every variant is stable between builds."""
    rng = random.Random(seed_for("wear", ctx.cube.name, str(level)))
    cloth_like = ctx.cube.material.startswith("cloth")
    for f in SIDE_FACES + ("top",):
        w, h = ctx.size(f)
        if w < 3 or h < 3:
            continue
        area = w * h
        scratches = max(1, area // (28 if level == 1 else 14))
        for _ in range(scratches):
            if rng.random() > (0.55 if level == 1 else 0.9):
                continue
            x, y = rng.randrange(w), rng.randrange(h)
            length = rng.randint(2, 3 if level == 1 else 4)
            dx = rng.choice((-1, 1))
            for i in range(length):
                xx, yy = x + i * dx, y + i
                if 0 <= xx < w and 0 <= yy < h:
                    if cloth_like:
                        ctx.put(f, xx, yy, "cloth_shadow")
                    else:
                        ctx.put(f, xx, yy, "steel_hi" if i == 0 else "steel_mid")
        if level >= 2 and not cloth_like and area >= 12:
            # dent: a recess pixel with a highlight lip above it
            x, y = rng.randrange(1, w - 1), rng.randrange(1, h - 1)
            ctx.put(f, x, y, "steel_recess")
            ctx.put(f, x, y - 1, "steel_hi")
            if area >= 24 and rng.random() < 0.6:
                # crack: a jagged recess line; glass shows through the deepest point
                x, y = rng.randrange(w), 0
                for i in range(rng.randint(3, min(6, h))):
                    ctx.put(f, x, y, "steel_recess")
                    if i == 2:
                        ctx.put(f, x, y, "glass_dark")
                    y += 1
                    x += rng.choice((-1, 0, 1))
        if level >= 2 and cloth_like and h >= 4:
            # torn hem: notches in the bottom rows
            for x in range(w):
                if rng.random() < 0.3:
                    ctx.put(f, x, h - 1, None if f != "top" else "cloth_shadow")
                    ctx.put(f, x, h - 2, "cloth_shadow")


def to_image(arr):
    from PIL import Image
    return Image.fromarray(arr, "RGBA")


def palette_violations(arr):
    """Pixels whose RGB is not in the palette (ignoring fully transparent pixels)."""
    allowed = set(COLORS.values())
    bad = 0
    a = arr.reshape(-1, 4)
    for px in {tuple(p) for p in a[a[:, 3] > 0][:, :3]}:
        if px not in allowed:
            bad += 1
    return bad
