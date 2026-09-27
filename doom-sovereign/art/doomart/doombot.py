"""The Standard Doombot: an industrial automaton in its master's likeness.

Reusable skeleton: every Doombot variant (Standard, Sentinel, Praetorian ...) is meant to keep
these bone names and pivots and change only cubes and textures, so all bot animations apply to
all variants. Units: model pixels, Bedrock space (front = -z, right = -x). Height 36 px (2.25 blocks).
"""
from .geo import Model

IDENT = "geometry.doom_sovereign.doombot_standard"


def build():
    m = Model(IDENT, 64, 64)
    m.bone("root", None, (0, 0, 0), dof={"x": (-95, 95), "y": (-180, 180), "z": (-95, 95)},
           desc="Entity root; whole-body falls and collapses")
    p = m.bone("pelvis", "root", (0, 13, 0), dof={"x": (-40, 40), "y": (-45, 45), "z": (-20, 20)},
               desc="Hips; moving it moves torso and legs together")
    p.cube("pelvis_block", (-4, 11, -2.5), (8, 3, 5), "steel_dark", deco="bot_pelvis")
    p.cube("pelvis_plate", (-3, 11.5, -3.2), (6, 2, 1), "steel")
    tf = m.bone("tabard_front", "pelvis", (0, 11.5, -3.2), dof={"x": (-60, 15), "y": (0, 0), "z": (-10, 10)},
                desc="Green service tabard (front); secondary motion")
    tf.cube("tabard_front_cloth", (-2.5, 5, -3.6), (5, 6, 1), "cloth", deco="bot_tabard")
    tb = m.bone("tabard_back", "pelvis", (0, 11.5, 2.8), dof={"x": (-15, 60), "y": (0, 0), "z": (-10, 10)},
                desc="Green service tabard (back)")
    tb.cube("tabard_back_cloth", (-2.5, 5, 2.6), (5, 6, 1), "cloth")
    w = m.bone("waist", "pelvis", (0, 14, 0), dof={"x": (-40, 60), "y": (-70, 70), "z": (-25, 25)},
               desc="Spine actuator between pelvis and chest")
    w.cube("abdomen_core", (-2.5, 14, -1.5), (5, 5, 3), "steel_dark", deco="bot_abdomen")
    w.cube("piston_r", (-3.5, 14, -0.5), (1, 5, 1), "brass")
    w.cube("piston_l", (2.5, 14, -0.5), (1, 5, 1), "brass")
    c = m.bone("chest", "waist", (0, 19, 0), dof={"x": (-20, 30), "y": (-30, 30), "z": (-15, 15)},
               desc="Chest shell with the reactor core")
    c.cube("chest_shell", (-5, 19, -3), (10, 8, 6), "steel", deco="bot_chest")
    c.cube("chest_core", (-1.5, 21.5, -3.6), (3, 3, 1), "glass", deco="bot_core")
    c.cube("collar", (-3.5, 26.5, -2.5), (7, 1, 5), "steel", inflate=0.2)
    c.cube("back_vents", (-3, 20, 2.6), (6, 5, 1), "steel_dark", deco="bot_vents")
    n = m.bone("neck", "chest", (0, 27, 0), dof={"x": (-20, 20), "y": (-40, 40), "z": (-10, 10)}, desc="Neck actuator")
    n.cube("neck_column", (-1, 27, -1), (2, 2, 2), "steel_dark")
    h = m.bone("head", "neck", (0, 28.5, 0), dof={"x": (-45, 45), "y": (-90, 90), "z": (-25, 25)},
               desc="Sensor head in the master's likeness")
    h.cube("head_shell", (-3.5, 28.5, -3), (7, 7, 6), "steel", deco="bot_head")
    h.cube("face_plate", (-3, 29, -3.8), (6, 5, 1), "polished", deco="bot_face")
    h.cube("head_crest", (-2.5, 35.5, -2.5), (5, 1, 5), "steel_dark")
    h.cube("antenna", (2.5, 35, 1), (1, 3, 1), "steel_dark", deco="bot_antenna")
    e = m.bone("eye_glow", "head", (0, 32.5, -3.9), desc="Optic flare planes (emissive); scaled for scan pulses")
    e.cube("optic_r", (-2.5, 32, -4.0), (2, 1, 0), "glow_only", deco="bot_optic")
    e.cube("optic_l", (0.5, 32, -4.0), (2, 1, 0), "glow_only", deco="bot_optic")
    # arms
    s = m.bone("shoulder_r", "chest", (-6, 25.5, 0), dof={"x": (-180, 60), "y": (-90, 90), "z": (-35, 120)},
               desc="Right shoulder; x negative raises the arm forward")
    s.cube("pauldron_r", (-9.5, 23.5, -3), (4, 4, 6), "steel", deco="bot_pauldron")
    s.cube("upper_arm_r", (-8, 19.5, -1.5), (3, 5, 3), "steel_dark")
    f = m.bone("forearm_r", "shoulder_r", (-6.5, 19.5, 0), dof={"x": (-140, 5), "y": (-90, 90), "z": (-10, 10)},
               desc="Right elbow; x negative flexes")
    f.cube("elbow_r", (-7.5, 18.5, -1), (2, 2, 2), "brass")
    f.cube("forearm_shell_r", (-8.5, 13, -2), (4, 6, 4), "steel", deco="bot_forearm")
    hd = m.bone("hand_r", "forearm_r", (-6.5, 13, 0), dof={"x": (-60, 60), "y": (-60, 60), "z": (-45, 95)},
                desc="Right hand; z = +90 turns the palm emitter along the arm")
    hd.cube("hand_block_r", (-8.5, 10, -2), (4, 3, 4), "steel_dark", deco="bot_hand")
    pe = m.bone("palm_emitter_r", "hand_r", (-4.5, 11, 0), desc="Palm emitter lens; weapon origin")
    pe.cube("emitter_lens_r", (-4.4, 10.5, -1), (0, 2, 2), "glass", deco="bot_emitter")
    m.mirror("shoulder_r", lambda nme: nme.replace("_r", "_l").replace("Right", "Left"))
    # legs
    if True:  # right leg; the left leg is its mirror
        hp = m.bone("hip_r", "pelvis", (-2.5, 12, 0), dof={"x": (-110, 60), "y": (-30, 30), "z": (-10, 40)},
                    desc="Right hip; x negative swings the leg forward")
        hp.cube("thigh_r", (-4.5, 7, -2), (4, 5, 4), "steel", deco="bot_thigh")
        k = m.bone("shin_r", "hip_r", (-2.5, 7.5, 0), dof={"x": (0, 140), "y": (-10, 10), "z": (-5, 5)},
                   desc="Right knee; x positive flexes")
        k.cube("knee_cap_r", (-4, 6, -2.8), (3, 2, 1), "brass")
        k.cube("shin_r_shell", (-4.5, 2, -2), (4, 5, 4), "steel", deco="bot_shin")
        ft = m.bone("foot_r", "shin_r", (-2.5, 2, 0), dof={"x": (-50, 50), "y": (-10, 10), "z": (-15, 15)},
                    desc="Right ankle; keep the sole flat when planted")
        ft.cube("foot_r_block", (-5, 0, -4), (5, 2, 6), "steel_dark", deco="bot_foot")
    m.mirror("hip_r", lambda nme: nme.replace("_r", "_l"))
    # damage/sparks locators: empty bones the renderer attaches particles to
    for nme, parent, piv in (("spark_chest", "chest", (2, 24, -3.2)), ("spark_head", "head", (-2, 34, -2)),
                             ("spark_shoulder_l", "shoulder_l", (7.5, 25, 0))):
        m.bone(nme, parent, piv, desc="Particle locator (no geometry)")
    return m


LINKED = {}


def bot_face(c):
    f = "front"   # 6 x 5 simplified mask
    for (x, y) in ((1, 1), (2, 1), (3, 1), (4, 1)):
        c.put(f, x, y, "glass_dark" if x in (1, 4) else "steel")
    c.put(f, 1, 1, "glass_dark")
    c.put(f, 4, 1, "glass_dark")
    for x in range(6):
        c.put(f, x, 0, "steel_hi")
    for (x, y) in ((1, 3), (4, 3), (2, 4), (3, 4)):
        c.put(f, x, y, "steel_recess")
    c.put(f, 0, 2, "steel_hi")
    c.put(f, 5, 2, "steel_hi")
    lvl = c.glow_level()
    if lvl:
        c.shine(f, 1, 1, lvl)
        c.shine(f, 4, 1, lvl)
    if c.damage >= 2:
        c.put(f, 4, 2, "steel_recess")
        c.put(f, 5, 3, "glass_dark")
        if lvl:
            c.shine(f, 4, 1, "arcane_dim")


def bot_optic(c):
    if c.state == "powered":
        w, h = c.size("front")
        for x in range(w):
            c.shine("front", x, 0, "arcane_core" if x == w - 1 else "arcane")


def bot_head(c):
    for f in ("left", "right"):
        w, h = c.size(f)
        for y in range(1, h - 1):
            c.put(f, w // 2, y, "steel_recess")          # side seam: the head is a riveted shell
        c.put(f, 1, 1, "brass")
    w, h = c.size("back")
    for x in range(1, w - 1):
        c.put("back", x, h - 2, "steel_recess" if x % 2 else "steel_mid")   # cooling slots


def bot_antenna(c):
    c.put("top", 0, 0, "brass_hi")
    if c.state == "powered":
        c.shine("top", 0, 0, "arcane")


def bot_chest(c):
    f = "front"
    w, h = c.size(f)  # 10 x 8
    for x in range(w):
        c.put(f, x, 0, "steel_hi")
    for y in range(1, h - 1):
        c.put(f, 3, y, "steel_recess")
        c.put(f, 6, y, "steel_recess")
        c.put(f, 4, y, "steel_mid")
    for (x, y) in ((1, 1), (8, 1), (1, h - 2), (8, h - 2)):
        c.put(f, x, y, "brass")
    for y in range(h):
        c.put("back", 0, y, "steel_mid")


def bot_core(c):
    lvl = c.glow_level()
    for f in ("front",):
        w, h = c.size(f)
        for y in range(h):
            for x in range(w):
                c.put(f, x, y, "glass_dark")
                if lvl:
                    c.shine(f, x, y, "arcane_core" if (x, y) == (1, 1) and c.state == "powered" else lvl)
    if c.damage >= 2:
        c.put("front", 2, 0, "steel_recess")
        c.shine("front", 2, 0, None)


def bot_vents(c):
    f = "back"
    w, h = c.size(f)
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if y % 2 == 1:
                c.put(f, x, y, "steel_recess")
                if c.state == "powered":
                    c.shine(f, x, y, "arcane_dim")


def bot_abdomen(c):
    w, h = c.size("front")
    for y in range(h):
        c.put("front", w // 2, y, "steel_mid" if y % 2 else "steel_recess")


def bot_pelvis(c):
    w, h = c.size("front")
    for x in range(w):
        c.put("front", x, 0, "brass" if x in (0, w - 1) else "steel_mid")


def bot_tabard(c):
    w, h = c.size("front")
    for y in range(h):
        c.put("front", w // 2, y, "brass" if y == 1 else c.g["front"][y][w // 2])
    c.put("front", w // 2 - 1, 1, "brass_lo")
    c.put("front", w // 2 + 1, 1, "brass_lo")


def bot_pauldron(c):
    for f in ("front", "back", "right", "left"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, h - 1, "steel_recess")
            c.put(f, x, 0, "steel_hi")
    w, h = c.size("top")
    c.put("top", 1, 1, "brass")
    c.put("top", w - 2, h - 2, "brass")


def bot_forearm(c):
    for f in ("front", "right", "back", "left"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, 1, "steel_recess")
            c.put(f, x, h - 1, "steel_recess")


def bot_hand(c):
    for f in ("front", "back"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, h - 1, "steel_mid" if x % 2 == 0 else "steel_recess")


def bot_emitter(c):
    lvl = c.glow_level()
    for f in ("left", "right"):
        w, h = c.size(f)
        for y in range(h):
            for x in range(w):
                c.put(f, x, y, "glass_dark")
                if lvl:
                    c.shine(f, x, y, lvl)


def bot_thigh(c):
    w, h = c.size("front")
    for y in range(1, h - 1):
        c.put("front", 1, y, "steel_mid")


def bot_shin(c):
    w, h = c.size("front")
    for y in range(h):
        c.put("front", w // 2, y, "steel_hi" if y < 2 else "steel_mid")


def bot_foot(c):
    for f in ("front", "right", "left", "back"):
        w, h = c.size(f)
        for x in range(w):
            c.put(f, x, h - 1, "steel_recess")
    w, h = c.size("top")
    for x in range(w):
        c.put("top", x, h - 1, "steel_hi")


DECORATIONS = {k: v for k, v in globals().items() if k.startswith("bot_")}
