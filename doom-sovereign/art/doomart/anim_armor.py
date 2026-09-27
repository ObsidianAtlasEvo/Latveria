"""The Royal Armor animation library (39 clips) with baked cloak / tunic / pauldron secondary motion.

Every clip is authored against the documented skeleton (docs/ROYAL_ARMOR_SKELETON.md) using the
rig helpers, then ``bake_secondary`` simulates the cloth: a damped spring chain per cloak column
driven by the clip's movement speed, vertical speed, strafe, torso pitch and leg swing (so the hem
clears the legs). Status: AUTHORED, AWAITING RUNTIME VALIDATION - nothing here has been played in
GeckoLib or Minecraft; the validator only proves structural and joint-limit correctness.

Full-body lean and roll during flight come from FlightController (FlightOutput.leanDegrees /
rollDegrees) and are applied to the whole entity by the renderer, not by these clips; the clips
receive that lean only so the cloak hangs correctly.
"""
import math

from .rig import ArmorAnim, PALM, leg_ik

PREFIX = "animation.royal_armor."
ALL = []


def clip(name, length, loop=False, category="", desc="", drive=None, lean=0.0, cloak_min=0.0, wind=1.0):
    def deco(fn):
        def make():
            a = ArmorAnim(name, length, loop, desc, category)
            fn(a)
            a.drive = drive or (lambda t: {"v": 0.0, "vy": 0.0, "strafe": 0.0})
            a.lean = lean
            a.cloak_min = cloak_min
            a.wind = wind
            return a
        make.__name__ = name
        ALL.append(make)
        return make
    return deco


def const(v=0.0, vy=0.0, strafe=0.0):
    return lambda t: {"v": v, "vy": vy, "strafe": strafe}


def relaxed(a, t, ease="easeInOutSine"):
    a.torso(t, 0)
    a.head(t, 0, 0, 0, ease)
    a.arms(t, (0, 0, 4), -8, (0, 0, 0), ease=ease)
    a.legs(t, (0, 0, 1.5), 0, ease)


def stance(a, t, width=4.0, bend=0.0, drop=0.0, pitch=0.0, ease="easeInOutSine", yaw=0.0):
    dy, dz = a.torso(t, pitch, yaw=yaw, drop=drop, ease=ease)
    for s in "rl":
        a.planted(s, t, dy, dz, foot_z=0.0, splay=width, ease=ease)
    return dy, dz


# ======================================================================================= idles ======
@clip("idle_armored", 4.0, True, "idle", "Neutral armoured idle: slow breath, weight settled, cloak barely stirring",
      wind=1.0)
def _(a):
    for t, br in ((0, 0), (2, 1), (4, 0)):
        a.torso(t, 0)
        a.rot("chest", t, -1.2 * br)
        for b in ("armorHead", "armorBody", "armorRightArm", "armorLeftArm"):
            a.pos(b, t, 0, 0.15 * br, 0)
        a.head(t, -1.0 * br)
        a.arms(t, (0, 0, 3 + br), -6 - 2 * br)
        a.legs(t, (0, 0, 1.5), 0)
    a.close_loop()


@clip("idle_authoritative", 6.0, True, "idle", "Sovereign presence: chin raised, chest out, slow survey of the subjects",
      wind=1.0)
def _(a):
    for t, yaw, br in ((0, 0, 0), (1.5, 14, 1), (3, 0, 0), (4.5, -14, 1), (6, 0, 0)):
        a.torso(t, -2, yaw=yaw * 0.3)
        a.rot("chest", t, -2 - 1.0 * br)
        a.head(t, -6, yaw * 0.7)
        a.arms(t, (0, 0, 7), -12, (0, 0, 0))
        a.legs(t, (0, 0, 4), 0)
    a.close_loop()


@clip("idle_arms_behind_back", 5.0, True, "idle", "Hands clasped at the small of the back under the cloak; the regal stance",
      cloak_min=12.0, wind=1.0)
def _(a):
    for t, br in ((0, 0), (2.5, 1), (5, 0)):
        a.torso(t, -1)
        a.rot("chest", t, -1 - 1.0 * br)
        a.head(t, -3 - br, 0)
        a.arms(t, (39, -11, -30), -35, (0, 0, 10), twist=-20)
        a.legs(t, (0, 0, 3), 0)
    a.close_loop()


# ================================================================================== locomotion =====
@clip("walk", 1.2, True, "locomotion", "Heavy, measured armoured walk", drive=const(v=4.3))
def _(a):
    # (time, right hip, right knee, left hip, left knee, bob, twist, right arm swing)
    keys = [(0.0, -24, 4, 20, 10, -0.5, 3, 16),
            (0.3, -2, 6, -8, 45, 0.1, 0, 0),
            (0.6, 20, 10, -24, 4, -0.5, -3, -16),
            (0.9, -8, 45, -2, 6, 0.1, 0, 0),
            (1.2, -24, 4, 20, 10, -0.5, 3, 16)]
    for t, rh, rk, lh, lk, bob, tw, sw in keys:
        a.torso(t, 2, yaw=tw)
        a.whole(t, bob)
        a.pos("armorBody", t, 0, bob, 0)
        a.head(t, 0, -tw * 0.6)
        a.leg("r", t, (rh, 0, 1.5), rk)
        a.leg("l", t, (lh, 0, 1.5), lk)
        a.arm("r", t, (sw, 0, 4), -12 - max(0, -sw) * 0.6)
        a.arm("l", t, (-sw, 0, 4), -12 - max(0, sw) * 0.6)
    a.sound(0.0, "doom_sovereign:armor.step_heavy").sound(0.6, "doom_sovereign:armor.step_heavy")
    a.sound(0.3, "doom_sovereign:armor.servo").cue(0.0, "footstep_right").cue(0.6, "footstep_left")


@clip("sprint", 0.72, True, "locomotion", "Armoured sprint: forward lean, pumping arms, long stride", drive=const(v=5.6))
def _(a):
    keys = [(0.0, -40, 12, 36, 60, -1.0, 45),
            (0.18, -6, 22, -30, 95, 0.4, 0),
            (0.36, 36, 60, -40, 12, -1.0, -45),
            (0.54, -30, 95, -6, 22, 0.4, 0),
            (0.72, -40, 12, 36, 60, -1.0, 45)]
    for t, rh, rk, lh, lk, bob, sw in keys:
        dy, dz = a.torso(t, 12, yaw=sw * 0.08, leg_offsets=True)
        for b in ("armorHead", "armorBody", "armorRightArm", "armorLeftArm"):
            a.pos(b, t, 0, bob, 0)
        a.head(t, -11, -sw * 0.05)
        a.leg("r", t, (rh, 0, 1), rk)
        a.leg("l", t, (lh, 0, 1), lk)
        a.arm("r", t, (sw - 12, 0, 5), -75 - max(0, -sw) * 0.4)
        a.arm("l", t, (-sw - 12, 0, 5), -75 - max(0, sw) * 0.4)
    a.sound(0.0, "doom_sovereign:armor.step_heavy").sound(0.36, "doom_sovereign:armor.step_heavy")
    a.cue(0.0, "footstep_right").cue(0.36, "footstep_left")


@clip("crouch", 0.35, "hold_on_last_frame", "locomotion", "Drop into a guarded crouch (held while sneaking)")
def _(a):
    relaxed(a, 0)
    dy, dz = a.torso(0.35, 22, drop=2.2, ease="easeOutCubic")
    for s in "rl":
        a.planted(s, 0.35, dy, dz, foot_z=1.2, splay=4, ease="easeOutCubic")
    a.head(0.35, -18, ease="easeOutCubic")
    a.arms(0.35, (-30, 0, 8), -40, ease="easeOutCubic")
    a.sound(0.0, "doom_sovereign:armor.servo")


@clip("jump_anticipation", 0.22, "hold_on_last_frame", "locomotion", "Load before a jump: dip, arms back")
def _(a):
    relaxed(a, 0)
    dy, dz = a.torso(0.22, 14, drop=1.6, ease="easeOutQuad")
    for s in "rl":
        a.planted(s, 0.22, dy, dz, foot_z=0.6, splay=2, ease="easeOutQuad")
    a.head(0.22, -10, ease="easeOutQuad")
    a.arms(0.22, (30, 0, 8), -20, ease="easeOutQuad")


@clip("jump_launch", 0.35, "hold_on_last_frame", "locomotion", "Explosive extension off the ground", drive=const(vy=8))
def _(a):
    dy, dz = a.torso(0, 14, drop=1.6)
    for s in "rl":
        a.planted(s, 0, dy, dz, foot_z=0.6, splay=2)
    a.head(0, -10)
    a.arms(0, (30, 0, 8), -20)
    a.torso(0.12, -4, ease="easeOutQuad")
    a.legs(0.12, (6, 0, 1), 4, ease="easeOutQuad")
    a.arms(0.12, (-50, 0, 10), -30, ease="easeOutQuad")
    a.head(0.12, -6, ease="easeOutQuad")
    a.torso(0.35, 0)
    a.leg("r", 0.35, (-18, 0, 2), 40)
    a.leg("l", 0.35, (8, 0, 2), 20)
    a.arms(0.35, (-30, 0, 14), -25)
    a.head(0.35, -2)
    a.sound(0.0, "doom_sovereign:armor.servo")


@clip("falling", 1.0, True, "locomotion", "Uncontrolled fall: arms out for balance, cloak streaming upward",
      drive=const(vy=-15))
def _(a):
    for t, s in ((0, 0), (0.5, 1), (1.0, 0)):
        a.torso(t, 4)
        a.head(t, 10 + 3 * s)
        a.arm("r", t, (-25 - 5 * s, 0, 40 + 6 * s), -30)
        a.arm("l", t, (-20 + 4 * s, 0, 44 - 6 * s), -26)
        a.leg("r", t, (-20 + 8 * s, 0, 6), 35 - 10 * s)
        a.leg("l", t, (4 - 8 * s, 0, 5), 20 + 10 * s)
    a.close_loop()


# ====================================================================================== flight ======
def hover_pose(a, t, s=0.0, ease="easeInOutSine"):
    a.torso(t, 2 + s)
    for b in ("armorHead", "armorBody", "armorRightArm", "armorLeftArm", "armorRightLeg", "armorLeftLeg",
              "armorRightBoot", "armorLeftBoot"):
        a.pos(b, t, 0, 0.5 * s, 0, ease)
    a.head(t, -2 - s, 0, 0, ease)
    a.arm("r", t, (6, 0, 14 + 2 * s), -12, (0, 0, PALM), ease=ease)
    a.arm("l", t, (6, 0, 14 + 2 * s), -12, (0, 0, PALM), ease=ease)
    a.leg("r", t, (4 + 2 * s, 0, 3), 12 + 3 * s, ease)
    a.leg("l", t, (9 - 2 * s, 0, 2), 18 - 3 * s, ease)


@clip("hover", 3.0, True, "flight", "Station-keeping on palm and boot repulsors; gentle bob",
      drive=lambda t: {"v": 0.0, "vy": -2.0, "strafe": 0.0}, wind=1.6)
def _(a):
    for t, s in ((0, -1), (1.5, 1), (3.0, -1)):
        hover_pose(a, t, s)
    a.sound(0.0, "doom_sovereign:flight.loop")
    a.particle(0.0, "doom_sovereign:repulsor_idle", "right_palm_emitter")
    a.close_loop()


@clip("takeoff", 0.45, "hold_on_last_frame", "flight", "Crouch and ignite: palm and boot repulsors push off",
      drive=lambda t: {"v": 0.0, "vy": 0.0 if t < 0.15 else 6.0, "strafe": 0.0})
def _(a):
    relaxed(a, 0)
    dy, dz = a.torso(0.15, 12, drop=1.8, ease="easeOutQuad")
    for s in "rl":
        a.planted(s, 0.15, dy, dz, foot_z=0.5, splay=3, ease="easeOutQuad")
    a.arms(0.15, (10, 0, 22), -10, (0, 0, PALM), ease="easeOutQuad")
    a.head(0.15, -12, ease="easeOutQuad")
    hover_pose(a, 0.45, 1, ease="easeOutBack")
    a.sound(0.12, "doom_sovereign:flight.thruster_ignition")
    a.particle(0.15, "doom_sovereign:repulsor_burst", "right_boot_knee")
    a.particle(0.16, "doom_sovereign:repulsor_burst", "left_boot_knee")
    a.cue(0.15, "liftoff")


@clip("vertical_ascent", 1.0, True, "flight", "Straight climb: arms driving down, head up, legs together",
      drive=const(vy=6.0), wind=1.2)
def _(a):
    for t, s in ((0, 0), (0.5, 1), (1.0, 0)):
        a.torso(t, -2)
        a.head(t, -14 - 2 * s)
        a.arms(t, (8, 0, 9 + 2 * s), -4, (0, 0, PALM))
        a.leg("r", t, (3, 0, 1), 5 + 2 * s)
        a.leg("l", t, (5, 0, 1), 8 - 2 * s)
    a.particle(0.0, "doom_sovereign:repulsor_trail", "right_palm_emitter")
    a.close_loop()


@clip("forward_flight", 2.0, True, "flight", "Cruise: arms swept back as thrusters, legs trailing, eyes ahead",
      drive=const(v=11.0), lean=14.0, wind=1.2)
def _(a):
    for t, s in ((0, 0), (1.0, 1), (2.0, 0)):
        a.torso(t, 0)
        a.head(t, -18 - s)
        a.arms(t, (30 + 2 * s, 0, 10), -6, (0, 0, PALM))
        a.leg("r", t, (12 + 2 * s, 0, 2), 10 + 2 * s)
        a.leg("l", t, (14 - 2 * s, 0, 2), 14 - 2 * s)
    a.particle(0.0, "doom_sovereign:repulsor_trail", "right_boot_knee")
    a.close_loop()


def strafe(a, side):
    m = 1 if side == "r" else -1
    lead, trail = ("r", "l") if side == "r" else ("l", "r")
    for t, s in ((0, 0), (0.5, 1), (1.0, 0)):
        a.torso(t, 2, roll=-m * 4)
        a.head(t, -4, 0, m * 6)
        a.arm(lead, t, (-10, 0, 34 + 3 * s), -20, (0, 0, PALM))
        a.arm(trail, t, (10, 0, 8), -12, (0, 0, PALM))
        a.leg(lead, t, (4, 0, 16 + 2 * s), 10)
        a.leg(trail, t, (8, 0, 2), 22 - 3 * s)
    a.close_loop()


@clip("strafe_left", 1.0, True, "flight", "Sideways flight to the left: leading arm out, legs swing wide",
      drive=const(v=6.0, strafe=-1.0))
def _(a):
    strafe(a, "l")


@clip("strafe_right", 1.0, True, "flight", "Sideways flight to the right: leading arm out, legs swing wide",
      drive=const(v=6.0, strafe=1.0))
def _(a):
    strafe(a, "r")


@clip("boosted_flight", 0.5, True, "flight", "Afterburners: arms locked back, body a spear, cloak thrashing",
      drive=const(v=22.0), lean=28.0, wind=1.5)
def _(a):
    for t, s in ((0, 0), (0.25, 1), (0.5, 0)):
        a.torso(t, 0)
        a.head(t, -30)
        a.arms(t, (42 + s, 0, 6), -2, (0, 0, PALM))
        a.legs(t, (16 + s, 0, 1), 4)
    a.sound(0.0, "doom_sovereign:flight.boost")
    a.particle(0.0, "doom_sovereign:repulsor_trail_boost", "right_boot_knee")
    a.close_loop()


@clip("braking", 0.6, "hold_on_last_frame", "flight", "Air brake: legs swing forward, palms thrust ahead, cloak whips forward",
      drive=lambda t: {"v": max(0.0, 11.0 - 30.0 * t), "vy": 0.0, "strafe": 0.0}, lean=6.0)
def _(a):
    a.torso(0, 0)
    a.head(0, -18)
    a.arms(0, (30, 0, 10), -6, (0, 0, PALM))
    a.legs(0, (12, 0, 2), 10)
    a.torso(0.25, -14, ease="easeOutQuad")
    a.head(0.25, 4, ease="easeOutQuad")
    a.arms(0.25, (-75, 0, 18), -10, (0, 0, PALM), ease="easeOutQuad")
    a.leg("r", 0.25, (-38, 0, 4), 32, ease="easeOutQuad")
    a.leg("l", 0.25, (-28, 0, 3), 40, ease="easeOutQuad")
    hover_pose(a, 0.6, 0)
    a.sound(0.05, "doom_sovereign:flight.thruster_ignition")
    a.cue(0.25, "brake_thrust")


@clip("controlled_descent", 2.0, True, "flight", "Powered-down glide to the ground, ready to land",
      drive=const(vy=-5.0), wind=1.3)
def _(a):
    for t, s in ((0, 0), (1.0, 1), (2.0, 0)):
        a.torso(t, 4)
        a.head(t, 10 + s)
        a.arms(t, (-4, 0, 22 + 2 * s), -18, (0, 0, PALM))
        a.leg("r", t, (-6, 0, 3), 16 + 2 * s)
        a.leg("l", t, (4, 0, 3), 22 - 2 * s)
    a.close_loop()


@clip("hard_landing", 1.2, False, "flight", "Three-point impact landing: knee bent deep, fist to the ground, then rise",
      drive=lambda t: {"v": 0.0, "vy": -18.0 if t < 0.05 else 0.0, "strafe": 0.0})
def _(a):
    hover_pose(a, 0, 0)
    dy, dz = a.torso(0.12, 34, drop=4.5, ease="easeOutExpo")
    a.planted("r", 0.12, dy, dz, foot_z=-2.5, splay=6, ease="easeOutExpo")
    a.planted("l", 0.12, dy, dz, foot_z=2.5, foot_y=0, splay=5, ease="easeOutExpo")
    a.arm("r", 0.12, (-40, 0, 6), -2, (0, 0, 0), ease="easeOutExpo")
    a.arm("l", 0.12, (40, 0, 38), -10, (0, 0, PALM), ease="easeOutExpo")
    a.head(0.12, 22, ease="easeOutExpo")
    dy, dz = a.torso(0.55, 30, drop=4.2)
    a.planted("r", 0.55, dy, dz, foot_z=-2.5, splay=6)
    a.planted("l", 0.55, dy, dz, foot_z=2.5, splay=5)
    a.arm("r", 0.55, (-38, 0, 6), -4)
    a.arm("l", 0.55, (36, 0, 34), -12, (0, 0, PALM))
    a.head(0.55, -10)
    relaxed(a, 1.2)
    a.sound(0.0, "doom_sovereign:armor.impact_heavy")
    a.particle(0.02, "doom_sovereign:landing_shockwave", "armorRightBoot")
    a.cue(0.02, "landing_impact")


# ====================================================================================== combat ======
def aim_pose(a, t, side="r", ease="easeInOutSine"):
    other = "l" if side == "r" else "r"
    m = 1 if side == "r" else -1
    stance(a, t, width=5, bend=0, ease=ease, yaw=-12 * m)
    a.head(t, 0, 10 * m, 0, ease)
    a.arm(side, t, (-88, 12, 0), -4, (0, 0, PALM), ease=ease)
    a.arm(other, t, (12, 0, 8), -22, ease=ease)


@clip("gauntlet_aim", 2.0, True, "combat", "Right gauntlet raised, palm lens forward, bladed stance")
def _(a):
    for t in (0, 1.0, 2.0):
        aim_pose(a, t)
    a.rot("right_palm_emitter", 1.0, 0, 0, 0)
    a.scl("right_palm_emitter", 0, 1, 1, 1).scl("right_palm_emitter", 1.0, 1.15, 1.15, 1.15).scl("right_palm_emitter", 2.0, 1, 1, 1)
    a.close_loop()


def blast(a, side):
    other = "l" if side == "r" else "r"
    m = 1 if side == "r" else -1
    relaxed(a, 0)
    aim_pose(a, 0.14, side, ease="easeOutQuad")
    a.arm(side, 0.2, (-80, 12, 0), -18, (0, 0, PALM), ease="easeOutExpo")    # recoil
    a.torso(0.2, -3, yaw=-10 * m, ease="easeOutExpo")
    aim_pose(a, 0.36, side)
    relaxed(a, 0.6)
    a.scl("%s_palm_emitter" % ("right" if side == "r" else "left"), 0.14, 1, 1, 1)
    a.scl("%s_palm_emitter" % ("right" if side == "r" else "left"), 0.18, 1.6, 1.6, 1.6, ease="easeOutExpo")
    a.scl("%s_palm_emitter" % ("right" if side == "r" else "left"), 0.3, 1, 1, 1)
    a.sound(0.16, "doom_sovereign:gauntlet.discharge")
    a.particle(0.16, "doom_sovereign:gauntlet_muzzle", "%s_palm_emitter" % ("right" if side == "r" else "left"))
    a.cue(0.16, "fire_" + ("right" if side == "r" else "left"))


@clip("energy_blast_left", 0.6, False, "combat", "Snap aim and fire the left gauntlet; recoil through the shoulder")
def _(a):
    blast(a, "l")


@clip("energy_blast_right", 0.6, False, "combat", "Snap aim and fire the right gauntlet; recoil through the shoulder")
def _(a):
    blast(a, "r")


@clip("charged_blast", 1.8, False, "combat", "Both gauntlets gather power, then a two-handed heavy discharge",
      drive=lambda t: {"v": 0.0, "vy": -3.0 if 0.3 < t < 1.3 else 0.0, "strafe": 0.0}, wind=2.0)
def _(a):
    relaxed(a, 0)
    stance(a, 0.3, width=7, drop=1.0, pitch=6)
    a.arm("r", 0.3, (-70, 20, -10), -40, (0, 0, PALM))
    a.arm("l", 0.3, (-70, 20, -10), -40, (0, 0, PALM))
    a.head(0.3, 6)
    stance(a, 1.2, width=7, drop=1.4, pitch=8)
    a.arm("r", 1.2, (-78, 18, -14), -30, (0, 0, PALM))
    a.arm("l", 1.2, (-78, 18, -14), -30, (0, 0, PALM))
    a.head(1.2, 4)
    stance(a, 1.32, width=7, drop=0.6, pitch=-8, ease="easeOutExpo")
    a.arm("r", 1.32, (-92, 16, -10), -2, (0, 0, PALM), ease="easeOutExpo")
    a.arm("l", 1.32, (-92, 16, -10), -2, (0, 0, PALM), ease="easeOutExpo")
    a.head(1.32, -4, ease="easeOutExpo")
    relaxed(a, 1.8)
    for side in ("right", "left"):
        b = side + "_palm_emitter"
        a.scl(b, 0, 1, 1, 1).scl(b, 1.2, 1.5, 1.5, 1.5, ease="easeInQuad").scl(b, 1.32, 2.0, 2.0, 2.0, ease="easeOutExpo")
        a.scl(b, 1.6, 1, 1, 1)
    a.sound(0.25, "doom_sovereign:gauntlet.charge").sound(1.3, "doom_sovereign:gauntlet.heavy_blast")
    a.particle(0.3, "doom_sovereign:gauntlet_charge", "right_palm_emitter")
    a.particle(1.3, "doom_sovereign:gauntlet_heavy_muzzle", "right_palm_emitter")
    a.cue(1.3, "fire_charged")


@clip("sustained_beam", 1.0, True, "combat", "Braced beam: right arm locked forward, left hand steadying the wrist, feet planted")
def _(a):
    tgt = [(-1, 13.0, -9.0)]
    for t, j in ((0, 0), (0.25, 1), (0.5, -1), (0.75, 1), (1.0, 0)):
        stance(a, t, width=7, drop=1.0, pitch=4, yaw=-6)
        a.head(t, 2, 4)
        a.arm("r", t, (-86 + 0.6 * j, 6, -8), -4, (0, 0, PALM))
        a.arm("l", t, (-70 + 0.6 * j, 34, -22), -48)
    a.scl("right_palm_emitter", 0, 1.3, 1.3, 1.3).scl("right_palm_emitter", 0.5, 1.45, 1.45, 1.45).scl("right_palm_emitter", 1.0, 1.3, 1.3, 1.3)
    a.sound(0.0, "doom_sovereign:gauntlet.beam_loop")
    a.close_loop()


@clip("force_field_activation", 0.8, False, "combat", "Arms cross, then sweep outward as the field snaps up",
      drive=lambda t: {"v": 0.0, "vy": -6.0 if 0.35 < t < 0.6 else 0.0, "strafe": 0.0}, wind=2.0)
def _(a):
    relaxed(a, 0)
    stance(a, 0.3, width=5, drop=0.8, pitch=8)
    a.arm("r", 0.3, (-70, 0, -28), -95, (0, 0, 20))
    a.arm("l", 0.3, (-66, 0, -28), -95, (0, 0, 20))
    a.head(0.3, 10)
    stance(a, 0.42, width=6, drop=0.4, pitch=-4, ease="easeOutExpo")
    a.arms(0.42, (-40, 0, 62), -8, (0, 0, PALM), ease="easeOutExpo")
    a.head(0.42, -6, ease="easeOutExpo")
    relaxed(a, 0.8)
    a.sound(0.36, "doom_sovereign:field.activate")
    a.particle(0.4, "doom_sovereign:field_raise", "armorBody")
    a.cue(0.4, "field_up")


@clip("shield_impact_reaction", 0.5, False, "combat", "The field takes a hit: body jolts, bracing arm pushes into it")
def _(a):
    relaxed(a, 0)
    a.torso(0.08, -7, fwd=-0.8, ease="easeOutExpo")
    a.head(0.08, -8, ease="easeOutExpo")
    a.arm("r", 0.08, (-50, 0, 10), -30, (0, 0, PALM), ease="easeOutExpo")
    a.arm("l", 0.08, (8, 0, 14), -20, ease="easeOutExpo")
    a.leg("r", 0.08, (8, 0, 3), 6, ease="easeOutExpo")
    a.leg("l", 0.08, (-6, 0, 3), 8, ease="easeOutExpo")
    relaxed(a, 0.5)
    a.cue(0.0, "shield_hit")


@clip("scan", 2.0, True, "combat", "Sensor sweep: open palm projects the scan cone as the head tracks it")
def _(a):
    for t, s in ((0, 0), (0.5, 1), (1.0, 0), (1.5, -1), (2.0, 0)):
        stance(a, t, width=4)
        a.head(t, 4, 26 * s)
        a.arm("r", t, (-62, 0, -8 * s), -14, (0, 0, PALM), twist=0)
        a.rot("armorRightArm", t, -62, 28 * s, 4)
        a.arm("l", t, (4, 0, 6), -14)
    a.sound(0.0, "doom_sovereign:scan.pulse").sound(1.0, "doom_sovereign:scan.pulse")
    a.particle(0.0, "doom_sovereign:scan_sweep", "right_palm_emitter")
    a.close_loop()


@clip("tech_override", 1.6, False, "combat", "Hack: right palm on target, left hand keying the vambrace console")
def _(a):
    relaxed(a, 0)
    for t, k in ((0.3, 0), (0.6, 1), (0.9, 0), (1.2, 1)):
        stance(a, t, width=4, pitch=4)
        a.head(t, 12, 8)
        a.arm("r", t, (-70, 0, 4), -30, (0, 0, PALM))
        a.arm("l", t, (-58 - 4 * k, 32, -30), -82, (6 * k, 0, 0))
    relaxed(a, 1.6)
    a.sound(0.35, "doom_sovereign:scan.pulse").sound(0.95, "doom_sovereign:tech.override")
    a.cue(1.2, "override_complete")


@clip("spell_cast", 1.0, False, "sorcery", "Draw the sigil with both hands, then thrust it outward",
      drive=lambda t: {"v": 0.0, "vy": -4.0 if 0.4 < t < 0.8 else 0.0, "strafe": 0.0}, wind=2.0)
def _(a):
    relaxed(a, 0)
    stance(a, 0.25, width=5, pitch=4)
    a.arm("r", 0.25, (-100, 10, 20), -80, (20, 0, 0))
    a.arm("l", 0.25, (-60, 0, -10), -60, (-10, 0, 0))
    a.head(0.25, 4)
    stance(a, 0.5, width=5, pitch=2)
    a.arm("r", 0.5, (-60, 0, 30), -70, (-20, 0, 0))
    a.arm("l", 0.5, (-100, 10, 20), -80, (20, 0, 0))
    stance(a, 0.65, width=6, pitch=-4, ease="easeOutBack")
    a.arms(0.65, (-84, 8, -4), -6, (0, 0, PALM), ease="easeOutQuart")
    a.head(0.65, -4, ease="easeOutBack")
    relaxed(a, 1.0)
    a.sound(0.15, "doom_sovereign:sorcery.arcane_cast")
    a.particle(0.3, "doom_sovereign:arcane_sigil", "right_palm_emitter")
    a.cue(0.65, "cast")


@clip("ritual_channel", 3.0, True, "sorcery", "Arms raised and open, palms up, head back: the circle resonates",
      drive=const(vy=-6.0), wind=2.5)
def _(a):
    for t, s in ((0, 0), (1.5, 1), (3.0, 0)):
        stance(a, t, width=6, pitch=-4)
        a.head(t, -16 - 2 * s)
        a.arms(t, (-40 - 3 * s, 20, 64 + 4 * s), -18, (0, 60, 30), twist=90)   # palms up (solved pose)
    a.sound(0.0, "doom_sovereign:sorcery.ritual_resonance")
    a.particle(0.0, "doom_sovereign:ritual_motes", "armorBody")
    a.close_loop()


@clip("teleport_cast", 0.9, False, "sorcery", "Cloak swept around the body, arms flung wide: gone",
      drive=lambda t: {"v": 0.0, "vy": -10.0 if 0.35 < t < 0.8 else 0.0, "strafe": 0.8 if t < 0.35 else 0.0}, wind=2.5)
def _(a):
    relaxed(a, 0)
    stance(a, 0.35, width=3, drop=0.6, pitch=10, yaw=20)
    a.arm("r", 0.35, (-60, 0, -30), -100)
    a.arm("l", 0.35, (-60, 0, -26), -100)
    a.head(0.35, 14, 10)
    stance(a, 0.6, width=6, pitch=-6, ease="easeOutExpo")
    a.arms(0.6, (-30, 0, 80), -10, (0, 0, PALM), ease="easeOutExpo")
    a.head(0.6, -10, ease="easeOutExpo")
    relaxed(a, 0.9)
    a.sound(0.3, "doom_sovereign:sorcery.teleport")
    a.particle(0.62, "doom_sovereign:teleport_flash", "armorBody")
    a.cue(0.62, "teleport")


@clip("doombot_command", 1.2, False, "command", "Imperious point: right arm commands, left hand behind the back, head nods")
def _(a):
    relaxed(a, 0)
    for t, n in ((0.35, 0), (0.55, 1), (0.8, 0)):
        stance(a, t, width=4, pitch=-2, yaw=-8)
        a.head(t, -6 + 6 * n, 6)
        a.arm("r", t, (-102, 8, -6), -4, (-10, 0, 0))
        a.arm("l", t, (39, -11, -30), -35, (0, 0, 10), twist=-20)
    relaxed(a, 1.2)
    a.cue(0.5, "command_issued")


@clip("light_melee", 0.5, False, "melee", "Quick right jab with the gauntlet")
def _(a):
    relaxed(a, 0)
    stance(a, 0.1, width=4, yaw=8)
    a.arm("r", 0.1, (-40, 0, 8), -110)
    a.arm("l", 0.1, (-30, 0, 10), -90)
    stance(a, 0.18, width=4, pitch=4, yaw=-16, ease="easeOutExpo")
    a.arm("r", 0.18, (-86, 0, -4), -6, ease="easeOutExpo")
    a.arm("l", 0.18, (-24, 0, 12), -96, ease="easeOutExpo")
    relaxed(a, 0.5)
    a.sound(0.14, "doom_sovereign:armor.servo")
    a.cue(0.18, "hit")


@clip("heavy_punch", 0.9, False, "melee", "Wind-up and a full-weight straight punch; the step sells the mass")
def _(a):
    relaxed(a, 0)
    dy, dz = a.torso(0.35, 6, yaw=24, drop=0.8)
    a.planted("r", 0.35, dy, dz, foot_z=2, splay=5)
    a.planted("l", 0.35, dy, dz, foot_z=-2, splay=5)
    a.arm("r", 0.35, (40, 0, 14), -110)
    a.arm("l", 0.35, (-50, 0, 10), -80)
    a.head(0.35, 6, -10)
    dy, dz = a.torso(0.45, 10, yaw=-22, drop=1.2, ease="easeOutExpo")
    a.planted("r", 0.45, dy, dz, foot_z=-3, splay=5, ease="easeOutExpo")
    a.planted("l", 0.45, dy, dz, foot_z=2.5, splay=5, ease="easeOutExpo")
    a.arm("r", 0.45, (-88, 0, -6), -2, ease="easeOutExpo")
    a.arm("l", 0.45, (20, 0, 12), -70, ease="easeOutExpo")
    a.head(0.45, 2, 12, ease="easeOutExpo")
    relaxed(a, 0.9)
    a.sound(0.43, "doom_sovereign:armor.impact_heavy")
    a.cue(0.45, "hit_heavy")


@clip("backhand", 0.7, False, "melee", "Contemptuous backhand across the body")
def _(a):
    relaxed(a, 0)
    stance(a, 0.2, width=4, yaw=-20)
    a.arm("r", 0.2, (-62, 0, -30), -70, (0, 0, -20))
    a.arm("l", 0.2, (6, 0, 8), -20)
    a.head(0.2, 0, -12)
    stance(a, 0.3, width=4, yaw=24, ease="easeOutExpo")
    a.arm("r", 0.3, (-72, 0, 60), -12, (0, 0, 30), ease="easeOutExpo")
    a.head(0.3, 0, 16, ease="easeOutExpo")
    relaxed(a, 0.7)
    a.cue(0.28, "hit")


@clip("ground_slam", 1.4, False, "melee", "Leap, both fists overhead, crash down: shockwave",
      drive=lambda t: {"v": 0.0, "vy": 8.0 if t < 0.35 else (-14.0 if t < 0.6 else 0.0), "strafe": 0.0}, wind=1.5)
def _(a):
    relaxed(a, 0)
    dy, dz = a.torso(0.15, 14, drop=1.8, ease="easeOutQuad")
    for s in "rl":
        a.planted(s, 0.15, dy, dz, foot_z=0.6, splay=3, ease="easeOutQuad")
    a.arms(0.15, (30, 0, 10), -20, ease="easeOutQuad")
    a.torso(0.4, -8, drop=-2.5, ease="easeOutQuad")
    a.legs(0.4, (-10, 0, 3), 30, ease="easeOutQuad")
    a.arms(0.4, (-170, 0, 12), -10, ease="easeOutQuad")
    a.head(0.4, -14, ease="easeOutQuad")
    dy, dz = a.torso(0.6, 30, drop=4.6, ease="easeInExpo")
    a.planted("r", 0.6, dy, dz, foot_z=-1.5, splay=7, ease="easeInExpo")
    a.planted("l", 0.6, dy, dz, foot_z=1.5, splay=7, ease="easeInExpo")
    a.arms(0.6, (-40, 0, 8), -2, ease="easeInExpo")
    a.head(0.6, 16, ease="easeInExpo")
    dy, dz = a.torso(0.95, 28, drop=4.2)
    a.planted("r", 0.95, dy, dz, foot_z=-1.5, splay=7)
    a.planted("l", 0.95, dy, dz, foot_z=1.5, splay=7)
    a.arms(0.95, (-38, 0, 10), -4)
    a.head(0.95, 0)
    relaxed(a, 1.4)
    a.sound(0.6, "doom_sovereign:armor.impact_heavy")
    a.particle(0.6, "doom_sovereign:landing_shockwave", "armorBody")
    a.cue(0.6, "slam")


# ===================================================================================== systems ======
def slump(a, t, ease="easeInOutSine"):
    dy, dz = a.torso(t, 10, drop=0.8, ease=ease)
    for s in "rl":
        a.planted(s, t, dy, dz, foot_z=0.4, splay=2, ease=ease)
    a.head(t, 28, 0, 0, ease)
    a.arms(t, (-6, 0, 2), -4, ease=ease)
    for side in ("right", "left"):
        a.rot(side + "_pauldron", t, 6, 0, 0, ease)


@clip("armor_initialization", 2.5, False, "systems", "Power-up: from dormant slump, joints test in sequence, head rises",
      drive=lambda t: {"v": 0.0, "vy": -2.0 if 1.9 < t < 2.3 else 0.0, "strafe": 0.0})
def _(a):
    slump(a, 0)
    slump(a, 0.3)
    a.rot("right_gauntlet", 0.45, 0, 0, 30).rot("right_gauntlet", 0.6, 0, 0, 0)
    a.rot("left_gauntlet", 0.65, 0, 0, -30).rot("left_gauntlet", 0.8, 0, 0, 0)
    for side, t0 in (("right", 0.9), ("left", 1.05)):
        a.rot(side + "_pauldron", t0, -6, 0, 18 * (1 if side == "right" else -1), "easeOutBack")
        a.rot(side + "_pauldron", t0 + 0.25, 0, 0, 0)
    stance(a, 1.6, width=3, pitch=2)
    a.head(1.6, 6)
    a.arms(1.6, (0, 0, 5), -10)
    stance(a, 2.2, width=4, pitch=-2, ease="easeOutBack")
    a.head(2.2, -6, ease="easeOutBack")
    a.arms(2.2, (0, 0, 7), -12, ease="easeOutBack")
    stance(a, 2.5, width=4)
    a.head(2.5, -3)
    a.arms(2.5, (0, 0, 5), -10)
    for t in (0.3, 0.8, 1.3):
        a.sound(t, "doom_sovereign:armor.servo")
    a.cue(2.0, "hud_online")


@clip("mask_seal", 1.4, False, "systems", "Mask lock: brow drops, cheek guards clamp, jaw seals, eyes ignite")
def _(a):
    a.rot("mask_brow", 0, -18).rot("mask_cheek_r", 0, 0, -40).rot("mask_cheek_l", 0, 0, 40)
    a.rot("mask_jaw", 0, 22).pos("mask_jaw", 0, 0, -1.0, 0.4).scl("mask_eye_glow", 0, 0, 0, 0)
    a.rot("mask_brow", 0.2, -18)
    a.rot("mask_brow", 0.32, 0, ease="easeOutBounce")
    a.rot("mask_cheek_r", 0.4, 0, -40).rot("mask_cheek_l", 0.4, 0, 40)
    a.rot("mask_cheek_r", 0.55, 0, 0, 0, "easeOutBack").rot("mask_cheek_l", 0.55, 0, 0, 0, "easeOutBack")
    a.rot("mask_jaw", 0.65, 22).pos("mask_jaw", 0.65, 0, -1.0, 0.4)
    a.rot("mask_jaw", 0.82, 0, ease="easeOutExpo").pos("mask_jaw", 0.82, 0, 0, 0, "easeOutExpo")
    a.head(0.0, 0).head(0.82, 0).head(0.9, 4, ease="easeOutQuad").head(1.1, 0)
    a.scl("mask_eye_glow", 0.95, 0, 0, 0).scl("mask_eye_glow", 1.08, 1.3, 1.3, 1.3, "easeOutExpo").scl("mask_eye_glow", 1.25, 1, 1, 1)
    a.sound(0.3, "doom_sovereign:mask.lock").sound(0.53, "doom_sovereign:mask.lock").sound(0.8, "doom_sovereign:mask.seal")
    a.cue(0.82, "sealed").cue(1.0, "eyes_lit")


@clip("shutdown_low_power", 1.5, "hold_on_last_frame", "systems", "Systems fail: shoulders fall, head bows, eyes gutter")
def _(a):
    stance(a, 0, width=4)
    a.head(0, -3)
    a.arms(0, (0, 0, 5), -10)
    a.scl("mask_eye_glow", 0, 1, 1, 1)
    a.scl("mask_eye_glow", 0.5, 0.6, 0.6, 0.6, "easeInQuad").scl("mask_eye_glow", 0.6, 0.9, 0.9, 0.9)
    a.scl("mask_eye_glow", 1.5, 0.3, 0.3, 0.3, "easeInQuad")
    slump(a, 1.5, ease="easeInOutQuad")
    a.sound(0.0, "doom_sovereign:armor.shutdown")
    a.cue(0.6, "power_low")


# ============================================================================= secondary motion =====
CLOAK_COLS = ("c", "r", "l")
SEG_W = (0.75, 1.0, 1.12)
SEG_OMEGA = (11.0, 8.5, 7.0)
ZETA = 0.32


def bake_secondary(a, model):
    L = a.length
    loop = a.loop is True
    fps = 60
    n = int(round(L * fps))
    cycles = 3 if loop else 1
    rest = {b.name: b.rotation for b in model.bones}
    dof = {b.name: b.dof for b in model.bones}

    def s(bone, ch, t, k):
        v = a.sample(bone, ch, t)
        return 0.0 if v is None else v[k]

    def targets(t):
        d = a.drive(t)
        v, vy, st = d["v"], d["vy"], d.get("strafe", 0.0)
        df = 75 * (1 - math.exp(-((abs(v) / 10.0) ** 1.5)))
        dv = 95 * (1 - math.exp(-((max(0.0, -vy) / 8.0) ** 1.3)))
        amt = min(100.0, math.hypot(df, dv)) - min(10.0, 1.5 * max(0.0, vy))
        pitch = s("armorBody", "rotation", t, 0) + a.lean + s("cloak_root", "rotation", t, 0)
        rl = s("armorRightLeg", "rotation", t, 0)
        ll = s("armorLeftLeg", "rotation", t, 0)
        out = {}
        for col in CLOAK_COLS:
            leg = {"c": max(rl, ll), "r": rl, "l": ll}[col]
            absang = []
            for i in range(3):
                A = 3.0 + amt * SEG_W[i]
                if i >= 1:
                    A = max(A, 0.8 * max(0.0, leg) + 2.0)
                A = max(A, a.cloak_min)
                absang.append(A)
            prev = pitch
            side = {"c": 0, "r": 1, "l": -1}[col]
            for i in range(3):
                bone = "cloak_%s_%d" % (col, i + 1)
                rx = absang[i] - prev - rest[bone][0]
                prev = absang[i]
                rz = (side * min(12.0, 0.12 * amt) - 8.0 * st * min(1.0, abs(v) / 4.0)) * (0.6 if i else 1.0)
                out[bone] = (rx, rz)
        front = 0.85 * min(0.0, rl, ll)
        back = 0.85 * max(0.0, rl, ll) + 0.3 * amt
        out["tunic_flap"] = (front, 0.0)
        out["tunic_flap_back"] = (back, 0.0)
        for side, arm in (("right", "armorRightArm"), ("left", "armorLeftArm")):
            m = 1 if side == "right" else -1
            outward = m * s(arm, "rotation", t, 2)          # positive = arm raised away from the body
            rxa = s(arm, "rotation", t, 0)
            out[side + "_pauldron"] = (max(-12.0, min(12.0, -0.08 * rxa)), m * max(0.0, 0.3 * outward))
        return out

    names = list(targets(0.0).keys())
    state = {b: [targets(0.0)[b][0], 0.0, targets(0.0)[b][1], 0.0] for b in names}
    omega = {}
    for b in names:
        if b.startswith("cloak_"):
            omega[b] = SEG_OMEGA[int(b[-1]) - 1]
        elif b.startswith("tunic"):
            omega[b] = 10.0
        else:
            omega[b] = 14.0
    samples = {b: [] for b in names}
    dt = 1.0 / fps
    for c in range(cycles):
        for i in range(n + 1 if c == cycles - 1 else n):
            t = i * dt
            tg = targets(min(t, L))
            for b in names:
                st = state[b]
                w = omega[b]
                for k, idx in ((0, 0), (1, 2)):
                    x, vel = st[idx], st[idx + 1]
                    acc = w * w * (tg[b][k] - x) - 2 * ZETA * w * vel
                    vel += acc * dt
                    x += vel * dt
                    st[idx], st[idx + 1] = x, vel
                if c == cycles - 1:
                    samples[b].append((t, st[0], st[2]))
    # flutter, quantised to whole cycles per clip for loops
    for b in names:
        if not b.startswith("cloak_"):
            continue
        seg = int(b[-1])
        ph = {"c": 0.0, "r": 1.7, "l": 3.1}[b.split("_")[1]] + seg * 0.9
        out = []
        for (t, x, z) in samples[b]:
            d = a.drive(min(t, L))
            amp = (min(9.0, 0.35 * abs(d["v"]) + 0.25 * max(0.0, -d["vy"])) + 0.8 * a.wind) * (0.35, 0.75, 1.0)[seg - 1]
            f1, f2 = 5.5, 7.3
            if loop:
                f1 = max(1, round(f1 * L)) / L
                f2 = max(1, round(f2 * L)) / L
                f0 = max(1, round(0.5 * L)) / L
            else:
                f0 = 0.5
            x += amp * (0.6 * math.sin(2 * math.pi * f1 * t + ph) + 0.4 * math.sin(2 * math.pi * f2 * t + 2 * ph))
            x += a.wind * 1.2 * math.sin(2 * math.pi * f0 * t + ph)
            z += 0.35 * amp * math.sin(2 * math.pi * f2 * t + ph)
            out.append((t, x, z))
        samples[b] = out
    for b in names:
        lo_x, hi_x = dof[b].get("x", (-180, 180))
        lo_z, hi_z = dof[b].get("z", (-180, 180))
        rx0, rz0 = rest[b][0], rest[b][2]
        pts = [(t, min(max(x + rx0, lo_x + 0.5), hi_x - 0.5) - rx0, min(max(z + rz0, lo_z + 0.5), hi_z - 0.5) - rz0)
               for (t, x, z) in samples[b]]
        if loop:
            (t0, x0, z0), (tn, xn, zn) = pts[0], pts[-1]
            pts = [(t, x + (x0 - xn) * (t / L), z + (z0 - zn) * (t / L)) for (t, x, z) in pts]
        pts = [(t, x, z) for (t, x, z) in pts if t <= L + 1e-9]
        authored = a.tracks.get((b, "rotation"))
        if authored:
            # secondary motion rides on top of hand-authored keys (e.g. the pauldron shrug in armor_initialization)
            pts = [(t, x + a.sample(b, "rotation", t)[0], z + a.sample(b, "rotation", t)[2]) for (t, x, z) in pts]
            pts = [(t, min(max(x + rx0, lo_x + 0.5), hi_x - 0.5) - rx0, min(max(z + rz0, lo_z + 0.5), hi_z - 0.5) - rz0)
                   for (t, x, z) in pts]
        keys = reduce_keys(pts, 0.5)
        a.tracks[(b, "rotation")] = {}
        for (t, x, z) in keys:
            a.key(b, "rotation", t, (x, 0.0, z), "linear")
        if loop:
            a.tracks[(b, "rotation")][round(L, 4)] = (list(a.tracks[(b, "rotation")][0.0][0]), "linear")
    return a


def reduce_keys(pts, tol):
    """Greedy simplification: keep the fewest points whose linear interpolation stays within tol."""
    keep = [pts[0]]
    i = 0
    while i < len(pts) - 1:
        j = i + 2
        while j < len(pts):
            t0, x0, z0 = pts[i]
            t1, x1, z1 = pts[j]
            ok = True
            for k in range(i + 1, j):
                tk, xk, zk = pts[k]
                u = (tk - t0) / (t1 - t0)
                if abs(x0 + (x1 - x0) * u - xk) > tol or abs(z0 + (z1 - z0) * u - zk) > tol:
                    ok = False
                    break
            if not ok:
                break
            j += 1
        keep.append(pts[j - 1])
        i = j - 1
    return [(round(t, 4), round(x, 3), round(z, 3)) for (t, x, z) in keep]


def build(model):
    anims = []
    for make in ALL:
        a = make()
        bake_secondary(a, model)
        anims.append(a)
    return anims
