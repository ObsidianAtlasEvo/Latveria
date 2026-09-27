"""The Doom mask as a standalone hero asset (item display, Armor Cradle close-up, equip
sequence). Twice the texel density of the worn helmet: the face plate is 16 x 12 texels.

States: pristine / moderate damage / severe damage (base textures) and low power / powered /
arcane-enhanced (emissive glow masks). The bones are split so the lock animation can bring the
plates together: brow drops, cheeks swing in, jaw rises, then the eyes ignite.
"""
from .geo import Model

IDENT = "geometry.doom_sovereign.doom_mask"


def build():
    m = Model(IDENT, 64, 64)
    m.bone("mask_root", None, (0, 8, 0), dof={"x": (-30, 30), "y": (-180, 180), "z": (-30, 30)},
           desc="Whole mask; display/turntable rotation")
    f = m.bone("faceplate", "mask_root", (0, 8, -1), dof={"x": (-10, 10), "y": (0, 0), "z": (0, 0)},
               desc="Face plate with eye slits")
    f.cube("hero_face", (-8, 2, -2), (16, 12, 2), "polished", deco="hero_face")
    f.cube("hero_nose", (-1, 4, -3), (2, 7, 1), "polished", deco="hero_nose")
    f.cube("hero_backing", (-7, 2, 0), (14, 12, 1), "steel_dark")
    b = m.bone("brow", "faceplate", (0, 14, -2), dof={"x": (-25, 5), "y": (0, 0), "z": (0, 0)},
               desc="Brow ridge; drops into place")
    b.cube("hero_brow", (-8, 13, -3), (16, 2, 1), "polished", inflate=0.2, deco="hero_brow")
    for side, x0, px in (("r", -9, -8), ("l", 8, 8)):
        c = m.bone("cheek_" + side, "faceplate", (px, 8, -1),
                   dof={"x": (0, 0), "y": (-50, 5) if side == "r" else (-5, 50), "z": (0, 0)},
                   desc="%s cheek guard; swings in" % {"r": "Right", "l": "Left"}[side])
        c.cube("hero_cheek_" + side, (x0, 3, -2), (1, 10, 6), "polished", deco="hero_cheek")
    j = m.bone("jaw", "faceplate", (0, 3, -2), dof={"x": (-5, 30), "y": (0, 0), "z": (0, 0)},
               desc="Jaw and grille; rises and seals last")
    j.cube("hero_jaw", (-6, 0, -3), (12, 4, 2), "polished", deco="hero_jaw")
    e = m.bone("eye_glow", "faceplate", (0, 10, -2.2), desc="Eye flare planes (emissive only)")
    e.cube("hero_eye_r", (-6, 9, -2.2), (4, 2, 0), "glow_only", deco="hero_flare")
    e.cube("hero_eye_l", (2, 9, -2.2), (4, 2, 0), "glow_only", deco="hero_flare")
    return m


# Face plate is 16 x 12; x = 0 is the mask's right edge (viewer's left).
EYES = [(2, 3), (3, 3), (4, 3), (5, 3), (3, 4), (4, 4), (5, 4),        # right eye, inner corner slants down
        (10, 3), (11, 3), (12, 3), (13, 3), (10, 4), (11, 4), (12, 4)]


def hero_face(c):
    f = "front"
    for (x, y) in EYES:
        c.put(f, x, y, "glass_dark")
    for x in (2, 3, 4, 5, 10, 11, 12, 13):
        c.put(f, x, 5, "steel")                          # lid shadow
    for (x, y) in ((0, 2), (1, 2), (14, 2), (15, 2), (0, 6), (1, 7), (15, 6), (14, 7)):
        c.put(f, x, y, "steel_hi")                       # temples and cheekbones
    for (x, y) in ((5, 8), (4, 9), (3, 10), (10, 8), (11, 9), (12, 10)):
        c.put(f, x, y, "steel_recess")                   # stern lines
    for (x, y) in ((6, 8), (5, 9), (9, 8), (10, 9)):
        c.put(f, x, y, "steel")
    for (x, y) in ((1, 1), (14, 1), (1, 10), (14, 10)):
        c.put(f, x, y, "brass")                          # rivets
        c.put(f, x, y + 1, "brass_lo")
    lvl = c.glow_level()
    if lvl:
        for (x, y) in EYES:
            c.shine(f, x, y, lvl)
        if c.state in ("powered", "arcane"):
            for (x, y) in ((5, 3), (5, 4), (10, 3), (10, 4)):
                c.shine(f, x, y, "arcane_core")         # hottest at the inner corners
    if c.state == "arcane":
        for (x, y) in ((0, 8), (0, 9), (1, 9), (15, 8), (15, 9), (14, 9), (7, 1), (8, 1)):
            c.shine(f, x, y, "arcane_dim")              # cheek and brow sigils
    if c.damage >= 1:
        for (x, y) in ((1, 4), (2, 5), (3, 6), (12, 7), (13, 8)):
            c.put(f, x, y, "steel_hi")                   # scratches
        c.put(f, 9, 10, "steel_recess")                  # dent
        c.put(f, 9, 9, "steel_hi")
    if c.damage >= 2:
        crack = [(12, 0), (12, 1), (11, 2), (12, 5), (11, 6), (12, 7), (13, 8), (12, 9), (12, 10), (13, 11)]
        for (x, y) in crack:
            c.put(f, x, y, "steel_recess")
        for (x, y) in ((11, 6), (12, 9)):
            c.put(f, x, y, "glass_dark")
        c.put(f, 14, 1, "steel_recess")                  # rivet sheared off
        c.put(f, 14, 2, "steel_recess")
        c.put(f, 15, 11, None)                           # chipped corner
        c.put(f, 14, 11, None)
        if lvl:
            for (x, y) in ((10, 3), (11, 3), (12, 3), (13, 3), (10, 4), (11, 4), (12, 4)):
                c.shine(f, x, y, "arcane_dim")          # the cracked eye gutters
            for (x, y) in ((11, 6), (12, 9), (13, 8)):
                c.shine(f, x, y, "arcane_dim")          # power bleeding through


def hero_nose(c):
    w, h = c.size("front")
    for y in range(h):
        c.put("front", 0, y, "steel_hi")
        c.put("front", 1, y, "steel_mid")
    c.put("front", 0, h - 1, "steel")
    c.put("front", 1, h - 1, "steel")


def hero_brow(c):
    w, h = c.size("front")
    for x in range(w):
        c.put("front", x, 0, "steel_hi")
        c.put("front", x, 1, "steel_mid" if 3 < x < 12 else "steel")
    for x in (0, 15):
        c.put("front", x, 1, "brass")
    if c.state == "arcane":
        for x in (4, 6, 9, 11):
            c.shine("front", x, 1, "arcane_dim")
    if c.damage >= 2:
        c.put("front", 12, 0, "steel_recess")
        c.put("front", 12, 1, "steel_recess")


def hero_cheek(c):
    for f in ("front", "right", "left"):
        w, h = c.size(f)
        for y in range(h):
            c.put(f, 0, y, "steel_hi")
    w, h = c.size("front")
    c.put("front", 0, h - 1, "steel")


SLOTS = (2, 4, 7, 9)


def hero_jaw(c):
    f = "front"
    w, h = c.size(f)  # 12 x 4
    for x in range(w):
        c.put(f, x, 0, "steel_hi")
        c.put(f, x, h - 1, "steel")
    for x in SLOTS:
        for y in (1, 2):
            c.put(f, x, y, "steel_recess")
    if c.state == "arcane":
        for x in SLOTS:
            c.shine(f, x, 2, "arcane_dim")
    if c.damage >= 1:
        c.put(f, 5, 1, "steel_hi")
    if c.damage >= 2:
        c.put(f, 10, 3, None)
        c.put(f, 11, 3, None)
        c.put(f, 11, 2, None)


def hero_flare(c):
    """Flare planes sit over the slits; lit pixels follow the slanted eye shape exactly."""
    if c.state not in ("powered", "arcane"):
        return
    col0 = 2 if c.cube.name.endswith("_r") else 10
    for (x, y) in EYES:
        if col0 <= x < col0 + 4:
            px, py = x - col0, y - 3
            hot = (x, y) in ((5, 3), (5, 4), (10, 3), (10, 4))
            c.shine("front", px, py, "arcane_core" if hot else "arcane")
            c.shine("back", 3 - px, py, "arcane")


DECORATIONS = {"hero_face": hero_face, "hero_nose": hero_nose, "hero_brow": hero_brow, "hero_cheek": hero_cheek,
               "hero_jaw": hero_jaw, "hero_flare": hero_flare}
