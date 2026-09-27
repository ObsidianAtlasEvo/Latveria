"""The Royal Armor of Doom: geometry, bone hierarchy and texture decorations.

Root bones follow GeckoLib's armor-renderer naming (armorHead, armorBody, armorRightArm,
armorLeftArm, armorRightLeg, armorLeftLeg, armorRightBoot, armorLeftBoot); everything else hangs
below them. Vanilla drives only the roots; elbows, knees, cloak, mask and plates move only when
an animation moves them. Pivots are in Bedrock model space (see geo.py).
"""
from .geo import Model

IDENT = "geometry.doom_sovereign.royal_armor"


def build():
    m = Model(IDENT, 128, 128)

    # ---- head: hood and mask --------------------------------------------------------------------
    m.bone("armorHead", None, (0, 24, 0), dof={"x": (-60, 60), "y": (-80, 80), "z": (-35, 35)},
           desc="Head root (follows vanilla head)")
    h = m.bone("hood", "armorHead", (0, 24, 0), dof={"x": (-10, 10), "y": (-5, 5), "z": (-5, 5)},
               desc="Cloth hood; secondary sway only")
    h.cube("hood_crown", (-5, 29, -4), (10, 4, 9), "cloth")
    h.cube("hood_side_r", (-5, 23, -4), (1, 6, 9), "cloth")
    h.cube("hood_side_l", (4, 23, -4), (1, 6, 9), "cloth")
    h.cube("hood_back", (-4, 22, 4), (8, 7, 1), "cloth")
    h.cube("hood_peak", (-4, 31, -5), (8, 2, 1), "cloth", deco="hood_peak")
    k = m.bone("mask", "armorHead", (0, 28, -4.5), dof={"x": (-8, 8), "y": (-5, 5), "z": (-5, 5)},
               desc="Mask assembly; root of the lock sequence")
    k.cube("mask_face", (-4, 25, -5), (8, 6, 1), "polished", deco="mask_face")
    k.cube("mask_nose", (-1, 26, -6), (2, 3, 1), "polished", deco="mask_nose")
    b = m.bone("mask_brow", "mask", (0, 30.5, -5), dof={"x": (-20, 10), "y": (0, 0), "z": (0, 0)},
               desc="Brow ridge; drops into place during the lock")
    b.cube("mask_brow_ridge", (-4, 30, -6), (8, 1, 1), "polished", inflate=0.25, deco="brow")
    c = m.bone("mask_cheek_r", "mask", (-4, 28, -4.5), dof={"x": (0, 0), "y": (-45, 5), "z": (-5, 5)},
               desc="Right cheek guard; swings in and clamps during the lock")
    c.cube("mask_cheek_r_plate", (-5, 25, -5), (1, 5, 3), "polished", inflate=0.2, deco="cheek")
    m.mirror("mask_cheek_r", lambda n: n.replace("_r", "_l"))
    j = m.bone("mask_jaw", "mask", (0, 24.5, -5), dof={"x": (-5, 25), "y": (0, 0), "z": (0, 0)},
               desc="Jaw plate with the grille; slides up and seals last")
    j.cube("mask_jaw_plate", (-3, 23, -6), (6, 2, 2), "polished", deco="jaw")
    e = m.bone("mask_eye_glow", "mask", (0, 29.5, -5.2), dof={"x": (0, 0), "y": (0, 0), "z": (0, 0)},
               desc="Eye flare planes (emissive only); scaled 0->1 to ignite the eyes")
    e.cube("eye_glow_r", (-3, 29, -5.2), (2, 1, 0), "glow_only", deco="eye_flare")
    e.cube("eye_glow_l", (1, 29, -5.2), (2, 1, 0), "glow_only", deco="eye_flare")

    # ---- body: tunic, plates, belt, cloak -------------------------------------------------------
    m.bone("armorBody", None, (0, 24, 0), dof={"x": (-45, 70), "y": (-70, 70), "z": (-35, 35)},
           desc="Body root (follows vanilla body)")
    t = m.bone("tunic", "armorBody", (0, 24, 0), desc="Green tunic under the plates")
    t.cube("tunic_torso", (-4, 12, -2), (8, 12, 4), "cloth", inflate=0.25)
    g = m.bone("gorget", "armorBody", (0, 24, 0), dof={"x": (-10, 10), "y": (-15, 15), "z": (-5, 5)},
               desc="Neck ring; follows the head a little")
    g.cube("gorget_ring", (-4, 22, -3), (8, 3, 6), "steel", inflate=0.25, deco="gorget")
    ch = m.bone("chest", "armorBody", (0, 20, -2.5), dof={"x": (-8, 8), "y": (0, 0), "z": (0, 0)},
                desc="Breastplate and backplate; breathing motion")
    ch.cube("chest_plate", (-4, 17, -3), (8, 5, 1), "steel", inflate=0.3, deco="chest")
    ch.cube("chest_ridge", (-1, 17, -4), (2, 5, 1), "steel", deco="ridge")
    ch.cube("back_plate", (-4, 14, 2), (8, 8, 1), "steel", inflate=0.3)
    a1 = m.bone("abdomen_1", "armorBody", (0, 17, -2.6), dof={"x": (-15, 25)}, desc="Upper abdominal lame")
    a1.cube("abdomen_plate_1", (-3.5, 15, -3.1), (7, 2, 1), "steel", inflate=0.1)
    a2 = m.bone("abdomen_2", "abdomen_1", (0, 15.5, -2.5), dof={"x": (-15, 25)}, desc="Middle abdominal lame")
    a2.cube("abdomen_plate_2", (-3.5, 13.5, -2.95), (7, 2, 1), "steel", inflate=0.1)
    a3 = m.bone("abdomen_3", "abdomen_2", (0, 14, -2.4), dof={"x": (-15, 25)}, desc="Lower abdominal lame")
    a3.cube("abdomen_plate_3", (-3, 12, -2.8), (6, 2, 1), "steel", inflate=0.1)
    bl = m.bone("belt", "armorBody", (0, 12, 0), desc="Belt, buckle and hip pouches")
    bl.cube("belt_band", (-4, 10, -2), (8, 2, 4), "steel_dark", inflate=0.6, deco="belt")
    bl.cube("belt_buckle", (-1.5, 9.5, -3.2), (3, 3, 1), "brass", deco="buckle")
    bl.cube("belt_pouch_r", (-5.4, 9.2, -1), (1, 2, 2), "steel_dark")
    bl.cube("belt_pouch_l", (4.4, 9.2, -1), (1, 2, 2), "steel_dark")
    fl = m.bone("tunic_flap", "armorBody", (0, 10, -3.2), dof={"x": (-60, 15), "y": (0, 0), "z": (-10, 10)},
                desc="Front tunic flap below the belt; secondary motion")
    fl.cube("tunic_flap_cloth", (-3, 3, -3.7), (6, 7, 1), "cloth")
    fb = m.bone("tunic_flap_back", "armorBody", (0, 10, 2.8), dof={"x": (-15, 60), "y": (0, 0), "z": (-10, 10)},
                desc="Rear tunic flap below the belt (under the cloak); secondary motion")
    fb.cube("tunic_flap_back_cloth", (-3, 3, 2.6), (6, 7, 1), "cloth")
    cr = m.bone("cloak_root", "armorBody", (0, 23.5, 3), dof={"x": (-10, 30), "y": (-10, 10), "z": (-10, 10)},
                desc="Cloak mantle and clasps; parent of the three cloak columns")
    cr.cube("cloak_mantle", (-4, 22, 1), (8, 3, 3), "cloth")
    cr.cube("cloak_clasp_r", (-4, 21, -3.8), (1, 1, 1), "brass")
    cr.cube("cloak_clasp_l", (3, 21, -3.8), (1, 1, 1), "brass")
    cloak_dof = {"x": (-25, 100), "y": (-30, 30), "z": (-30, 30)}
    for col, x0, wide, zb, rz in (("c", -2, 4, 3, 0), ("r", -6, 5, 3.15, 3)):
        px = x0 + wide / 2.0
        s1 = m.bone("cloak_%s_1" % col, "cloak_root", (px, 23.5, 3.5), (4, 0, rz), dof=cloak_dof,
                    desc="Cloak %s column, upper segment" % {"c": "centre", "r": "right"}[col])
        s1.cube("cloak_%s_upper" % col, (x0, 15.5, zb), (wide, 8, 1), "cloth", deco="cloak_lining")
        s2 = m.bone("cloak_%s_2" % col, "cloak_%s_1" % col, (px, 15.5, 3.5), (3, 0, 0), dof=cloak_dof,
                    desc="Cloak %s column, middle segment" % {"c": "centre", "r": "right"}[col])
        s2.cube("cloak_%s_middle" % col, (x0, 7.5, zb), (wide, 8, 1), "cloth", deco="cloak_lining")
        s3 = m.bone("cloak_%s_3" % col, "cloak_%s_2" % col, (px, 7.5, 3.5), (3, 0, 0), dof=cloak_dof,
                    desc="Cloak %s column, lower segment (hem)" % {"c": "centre", "r": "right"}[col])
        s3.cube("cloak_%s_lower" % col, (x0, 0.5, zb), (wide, 7, 1), "cloth", deco="cloak_lining+cloak_hem")
    m.mirror("cloak_r_1", lambda n: n.replace("_r_", "_l_"))

    # ---- right arm (left arm is mirrored) -------------------------------------------------------
    m.bone("armorRightArm", None, (-5, 22, 0), dof={"x": (-190, 60), "y": (-90, 90), "z": (-30, 120)},
           desc="Right arm root (follows vanilla right arm)")
    p = m.bone("right_pauldron", "armorRightArm", (-5, 23, 0), dof={"x": (-20, 20), "y": (-10, 10), "z": (-10, 35)},
               desc="Right pauldron; lifts when the arm rises")
    p.cube("pauldron_r", (-9, 21, -3), (5, 3, 6), "steel", inflate=0.1, deco="pauldron")
    p.cube("pauldron_r_cap", (-8.5, 24, -2.5), (4, 1, 5), "steel")
    pl = m.bone("right_pauldron_lame", "right_pauldron", (-8, 21, 0), dof={"x": (-15, 15), "y": (0, 0), "z": (0, 25)},
                desc="Lower pauldron lame; secondary flap")
    pl.cube("pauldron_r_lame", (-9, 19.5, -3), (4, 2, 6), "steel", inflate=0.15, deco="rim")
    ua = m.bone("right_upper_arm", "armorRightArm", (-5, 22, 0), dof={"x": (-10, 10), "y": (-10, 10), "z": (-10, 10)},
                desc="Sleeve and rerebrace")
    ua.cube("sleeve_r", (-8, 17, -2), (4, 5, 4), "cloth", inflate=0.3)
    ua.cube("rerebrace_r", (-9, 17.5, -1.5), (1, 2, 3), "steel")
    fa = m.bone("right_forearm", "right_upper_arm", (-6, 17, 0), dof={"x": (-150, 5), "y": (-95, 95), "z": (-10, 10)},
                desc="Elbow: couter and vambrace. Flexion is negative x")
    fa.cube("couter_r", (-8, 15, -2), (4, 2, 4), "steel", inflate=0.55, deco="couter")
    fa.cube("vambrace_r", (-8, 12.5, -2), (4, 3, 4), "steel", inflate=0.45, deco="vambrace")
    gt = m.bone("right_gauntlet", "right_forearm", (-6, 12.5, 0), dof={"x": (-70, 70), "y": (-60, 60), "z": (-45, 95)},
                desc="Wrist and gauntlet; z = +90 turns the palm lens to face along the arm (repulsor pose)")
    gt.cube("gauntlet_r", (-8, 10, -2), (4, 3, 4), "steel_dark", inflate=0.5, deco="gauntlet")
    gt.cube("knuckles_r", (-9, 10.5, -2), (1, 2, 4), "steel", deco="knuckles")
    pe = m.bone("right_palm_emitter", "right_gauntlet", (-4, 11, 0), dof={"x": (0, 0), "y": (0, 0), "z": (0, 0)},
                desc="Palm repulsor lens; blast origin and emissive; scale pulses on charge")
    pe.cube("emitter_r", (-3.4, 10.5, -1), (0, 2, 2), "glass", deco="emitter")
    m.mirror("armorRightArm", lambda n: n.replace("Right", "Left").replace("right", "left").replace("_r", "_l"))

    # ---- right leg and boot (left mirrored) -----------------------------------------------------
    leg_dof = {"x": (-120, 70), "y": (-35, 35), "z": (-10, 45)}
    knee_dof = {"x": (0, 150), "y": (-15, 15), "z": (-5, 5)}
    m.bone("armorRightLeg", None, (-1.9, 12, 0), dof=leg_dof, desc="Right leg root (follows vanilla right leg)")
    th = m.bone("right_thigh", "armorRightLeg", (-1.9, 12, 0), dof={"x": (-10, 10)}, desc="Cuisse")
    th.cube("cuisse_r", (-4, 6, -2), (4, 6, 4), "steel", inflate=0.3, deco="cuisse")
    ts = m.bone("right_tasset", "right_thigh", (-2, 12, -2.6), dof={"x": (-50, 10), "y": (0, 0), "z": (-10, 10)},
                desc="Tasset hanging from the belt over the thigh")
    ts.cube("tasset_r", (-4, 8.5, -3), (4, 3, 1), "steel", inflate=0.15)
    ts2 = m.bone("right_tasset_lower", "right_tasset", (-2, 8.5, -2.8), dof={"x": (-30, 10)}, desc="Lower tasset lame")
    ts2.cube("tasset_r_lower", (-4, 6.5, -2.9), (4, 2, 1), "steel", inflate=0.1, deco="rim")
    sh = m.bone("right_shin", "right_thigh", (-1.9, 6, 0), dof=knee_dof, desc="Knee: greave and poleyn. Flexion is positive x")
    sh.cube("greave_r", (-4, 2, -2), (4, 4, 4), "steel", inflate=0.35, deco="greave")
    sh.cube("poleyn_r", (-4, 5, -3), (4, 2, 1), "steel", inflate=0.1, deco="poleyn")
    m.bone("armorRightBoot", None, (-1.9, 12, 0), dof=leg_dof, desc="Right boot root (follows vanilla right leg)")
    bk = m.bone("right_boot_knee", "armorRightBoot", (-1.9, 6, 0), dof=knee_dof,
                desc="Boot copy of the knee; animations must keep it equal to right_shin")
    bk.cube("sabaton_r", (-4, 0, -2), (4, 2, 4), "steel", inflate=0.5, deco="sabaton")
    bk.cube("boot_toe_r", (-4, 0, -4), (4, 1, 2), "steel", inflate=0.45)
    bk.cube("boot_cuff_r", (-4, 2, -2), (4, 1, 4), "steel", inflate=0.55, deco="cuff")
    ren = lambda n: n.replace("Right", "Left").replace("right", "left").replace("_r", "_l")
    m.mirror("armorRightLeg", ren)
    m.mirror("armorRightBoot", ren)
    return m


# bones whose rotation must match between the leg and boot parts in every animation
LINKED = {"right_boot_knee": "right_shin", "left_boot_knee": "left_shin",
          "armorRightBoot": "armorRightLeg", "armorLeftBoot": "armorLeftLeg"}


# ---- decorations -----------------------------------------------------------------------------------
def mask_face(c):
    f = "front"
    w, h = c.size(f)  # 8 x 6, polished steel
    eyes = [(1, 1), (2, 1), (5, 1), (6, 1)]
    for (x, y) in eyes:
        c.put(f, x, y, "glass_dark")
    for (x, y) in ((1, 2), (2, 2), (5, 2), (6, 2)):
        c.put(f, x, y, "steel")                   # soft shadow under the slits
    for (x, y) in ((0, 1), (7, 1), (0, 2), (7, 2)):
        c.put(f, x, y, "steel_hi")                # cheekbones catch the light
    for (x, y) in ((2, 4), (1, 5), (5, 4), (6, 5)):
        c.put(f, x, y, "steel_recess")            # the stern lines from nose to jaw
    c.put(f, 0, 0, "brass")
    c.put(f, 7, 0, "brass")                       # temple rivets
    lvl = c.glow_level()
    if lvl:
        for (x, y) in eyes:
            c.shine(f, x, y, lvl)
        if c.state in ("powered", "arcane"):
            c.shine(f, 2, 1, "arcane_core")
            c.shine(f, 5, 1, "arcane_core")
    if c.state == "arcane":
        for (x, y) in ((0, 4), (7, 4)):
            c.shine(f, x, y, "arcane_dim")       # engraved sigils wake up
    if c.damage >= 1:
        for (x, y) in ((0, 3), (1, 4)):
            c.put(f, x, y, "steel_hi")           # scratch across the right cheek
        c.put(f, 6, 3, "steel")
    if c.damage >= 2:
        crack = [(6, 0), (5, 2), (6, 3), (6, 4), (5, 5)]
        for (x, y) in crack:
            c.put(f, x, y, "steel_recess")
        c.put(f, 6, 3, "glass_dark")
        c.put(f, 0, 0, "steel_recess")           # a rivet is gone
        if lvl:
            c.shine(f, 5, 1, "arcane_dim")      # the cracked eye gutters
            c.shine(f, 6, 1, "arcane_dim")
            c.shine(f, 6, 3, "arcane_dim")      # power leaking through the crack


def mask_nose(c):
    w, h = c.size("front")
    for y in range(h):
        c.put("front", 0, y, "steel_hi")
        c.put("front", 1, y, "steel_mid")


def brow(c):
    row = ["brass", "steel_hi", "steel_hi", "steel_mid", "steel_mid", "steel_hi", "steel_hi", "brass"]
    for x, n in enumerate(row):
        c.put("front", x, 0, n)
    if c.state == "arcane":
        for x in (2, 5):
            c.shine("front", x, 0, "arcane_dim")
    if c.damage >= 1:
        c.put("front", 2, 0, "steel_mid")
    if c.damage >= 2:
        c.put("front", 5, 0, "steel_recess")


def cheek(c):
    for f in ("right", "front"):
        w, h = c.size(f)
        for y in range(h):
            c.put(f, 0, y, "steel_hi")


def jaw(c):
    f = "front"
    top = ["steel_hi", "steel_recess", "steel_hi", "steel_hi", "steel_recess", "steel_hi"]
    bot = ["steel_mid", "steel_recess", "steel_mid", "steel_mid", "steel_recess", "steel"]
    for x in range(6):
        c.put(f, x, 0, top[x])
        c.put(f, x, 1, bot[x])
    if c.state == "arcane":
        for x in (1, 4):
            c.shine(f, x, 1, "arcane_dim")     # sorcerous breath through the grille
    if c.damage >= 2:
        c.put(f, 2, 1, "steel_recess")


def eye_flare(c):
    lvl = c.glow_level("arcane_core", "arcane_dim")
    if lvl and c.state != "low":
        for x in range(2):
            c.shine("front", x, 0, "arcane" if x == 0 else "arcane_core")
            c.shine("back", x, 0, "arcane")


def hood_peak(c):
    w, h = c.size("bottom")
    for y in range(h):
        for x in range(w):
            c.put("bottom", x, y, "cloth_shadow")


def gorget(c):
    for f in ("front", "back", "left", "right"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, 0, "steel_hi")
            if h > 2:
                c.put(f, x, 1, "steel")
                c.put(f, x, 2, "steel_recess")


def chest(c):
    f = "front"
    w, h = c.size(f)
    c.put(f, 0, 1, "brass")
    c.put(f, w - 1, 1, "brass")
    for x in (1, 2, w - 3, w - 2):
        c.put(f, x, 2, "steel_mid")
        c.put(f, x, 3, "steel_recess")


def ridge(c):
    w, h = c.size("front")
    for y in range(h):
        c.put("front", 0, y, "steel_hi")
        c.put("front", 1, y, "steel_mid")


def belt(c):
    for f in ("front", "back", "left", "right"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, 0, "brass" if x % 2 == 0 else "steel_mid")


def buckle(c):
    f = "front"
    for y in range(3):
        for x in range(3):
            c.put(f, x, y, "brass")
    c.put(f, 0, 0, "brass_hi")
    c.put(f, 1, 0, "brass_hi")
    c.put(f, 2, 0, "brass_hi")
    c.put(f, 1, 1, "brass_lo")
    c.put(f, 2, 2, "brass_lo")
    c.put(f, 1, 2, "brass_lo")


def pauldron(c):
    for f in ("front", "back", "right", "left"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, h - 1, "brass")
    w, h = c.size("top")
    for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
        c.put("top", x, y, "brass_hi")


def rim(c):
    for f in ("front", "back", "right", "left"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, h - 1, "brass")


def couter(c):
    for f in ("front", "right"):
        w, h = c.size(f)
        if w >= 3:
            c.put(f, w // 2 - 1, 0, "steel_hi")
            c.put(f, w // 2, 0, "steel_hi")
            c.put(f, w // 2 - 1, h - 1, "steel_recess")


def vambrace(c):
    for f in ("front", "back", "right", "left"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, 0, "steel_hi")
            c.put(f, x, h - 1, "steel_recess")
    w, h = c.size("right")
    c.put("right", w // 2, 1, "brass")            # a single brass stud on the outer vambrace
    if c.state == "arcane":
        c.shine("right", 1, 1, "arcane_dim")


def cuff(c):
    for f in ("front", "back", "right", "left"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, 0, "brass_lo" if x % 2 else "brass")


def gauntlet(c):
    for f in ("front", "back"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, h - 1, "steel_mid" if x % 2 == 0 else "steel_recess")
    w, h = c.size("bottom")
    for y in range(h):
        for x in range(w):
            c.put("bottom", x, y, "steel_recess" if (x + y) % 2 else "steel")


def knuckles(c):
    f = "right"
    w, h = c.size(f)
    for x in range(w):
        c.put(f, x, 0, "steel_hi" if x % 2 == 0 else "steel_mid")
        if h > 1:
            c.put(f, x, 1, "steel_recess" if x % 2 == 0 else "steel")


def emitter(c):
    lvl = c.glow_level()
    for f in ("left", "right"):
        w, h = c.size(f)
        for y in range(h):
            for x in range(w):
                c.put(f, x, y, "glass_dark")
                if lvl:
                    c.shine(f, x, y, lvl)
        if c.state in ("powered", "arcane") and w and h:
            c.shine(f, 0, 0, "arcane_core")


def cuisse(c):
    w, h = c.size("front")
    for y in range(1, h - 1):
        c.put("front", w // 2, y, "steel_mid")


def greave(c):
    w, h = c.size("front")
    for y in range(h):
        c.put("front", w // 2 - 1, y, "steel_hi")


def poleyn(c):
    c.put("front", 1, 0, "steel_hi")
    c.put("front", 2, 0, "steel_hi")
    c.put("front", 0, 1, "steel_recess")
    c.put("front", 3, 1, "steel_recess")


def sabaton(c):
    for f in ("front", "back", "left", "right"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, h - 1, "steel_recess")


def cloak_lining(c):
    w, h = c.size("front")
    rng = c.rng
    for y in range(h):
        for x in range(w):
            c.put("front", x, y, "cloth_shadow" if (x + rng.randrange(2)) % 3 else "green_dark")


def cloak_hem(c):
    w, h = c.size("back")
    if c.state == "arcane":
        for x in range(w):
            if x % 3 != 1:
                c.shine("back", x, h - 2, "arcane_dim")
    if c.damage >= 2:
        c.put("back", 1, h - 1, None)
        c.put("front", 2, h - 1, None)


DECORATIONS = {
    "mask_face": mask_face, "mask_nose": mask_nose, "brow": brow, "cheek": cheek, "jaw": jaw,
    "eye_flare": eye_flare, "hood_peak": hood_peak, "gorget": gorget, "chest": chest, "ridge": ridge,
    "belt": belt, "buckle": buckle, "pauldron": pauldron, "rim": rim, "couter": couter,
    "vambrace": vambrace, "cuff": cuff, "gauntlet": gauntlet, "knuckles": knuckles, "emitter": emitter,
    "cuisse": cuisse, "greave": greave, "poleyn": poleyn, "sabaton": sabaton,
    "cloak_lining": cloak_lining, "cloak_hem": cloak_hem,
}
