"""Standard Doombot animation library (16 clips) on the reusable Doombot skeleton.

Doombots move like machines: poses are reached quickly and held (easeOutExpo / step), heads
move in discrete servo ticks, and the torso stays level while walking. Status: AUTHORED,
AWAITING RUNTIME VALIDATION.
"""
import math

from .anim import Anim
from .rig import leg_ik

PREFIX = "animation.doombot."
PALM = 90.0
ALL = []
THIGH_BOT = 4.5
SHIN_BOT = 5.5


class BotAnim(Anim):
    def arm(self, side, t, sh=(0, 0, 0), el=0.0, wr=(0, 0, 0), twist=0.0, ease="easeOutExpo"):
        m = 1 if side == "r" else -1
        self.rot("shoulder_" + side, t, sh[0], m * sh[1], m * sh[2], ease)
        self.rot("forearm_" + side, t, el, m * twist, 0, ease)
        self.rot("hand_" + side, t, wr[0], m * wr[1], m * wr[2], ease)
        return self

    def arms(self, t, sh=(0, 0, 0), el=0.0, wr=(0, 0, 0), twist=0.0, ease="easeOutExpo"):
        self.arm("r", t, sh, el, wr, twist, ease)
        return self.arm("l", t, sh, el, wr, twist, ease)

    def leg(self, side, t, hip=(0, 0, 0), knee=0.0, ankle=None, ease="easeInOutSine"):
        m = 1 if side == "r" else -1
        self.rot("hip_" + side, t, hip[0], m * hip[1], m * hip[2], ease)
        self.rot("shin_" + side, t, knee, 0, 0, ease)
        if ankle is None:
            ankle = -(hip[0] + knee)       # keep the sole parallel to the ground
        self.rot("foot_" + side, t, max(-50, min(50, ankle)), 0, 0, ease)
        return self

    def legs(self, t, hip=(0, 0, 0), knee=0.0, ankle=None, ease="easeInOutSine"):
        self.leg("r", t, hip, knee, ankle, ease)
        return self.leg("l", t, hip, knee, ankle, ease)

    def hips(self, t, drop=0.0, back=0.0, pitch=0.0, yaw=0.0, roll=0.0, ease="easeInOutSine"):
        self.pos("pelvis", t, 0, -drop, back, ease)
        self.rot("pelvis", t, pitch, yaw, roll, ease)
        return self

    def planted(self, side, t, drop=0.0, back=0.0, foot_z=0.0, splay=0.0, ease="easeInOutSine"):
        hx, k = leg_ik(-drop, back, foot_z, 0.0, THIGH_BOT, SHIN_BOT)
        return self.leg(side, t, (hx, 0, splay), k, None, ease)

    def upright(self, t, ease="easeInOutSine"):
        self.hips(t, ease=ease)
        self.rot("waist", t, 0, 0, 0, ease)
        self.rot("head", t, 0, 0, 0, ease)
        self.arms(t, (0, 0, 4), -10, ease=ease)
        self.legs(t, (0, 0, 1), 0, ease=ease)
        return self

    def close_loop(self):
        for key, tr in self.tracks.items():
            ts = sorted(tr)
            if ts[0] > 0:
                tr[0.0] = (list(tr[ts[0]][0]), "linear")
            ts = sorted(tr)
            if self.length not in tr:
                tr[round(self.length, 4)] = (list(tr[ts[0]][0]), "easeInOutSine")
            elif any(abs(a - b) > 1e-3 for a, b in zip(tr[ts[0]][0], tr[self.length][0])):
                raise ValueError("%s %s: loop end differs from start" % (self.name, key))
        return self


def clip(name, length, loop=False, desc=""):
    def deco(fn):
        def make():
            a = BotAnim(name, length, loop, desc, "doombot")
            fn(a)
            tabards(a)
            if loop is True:
                a.close_loop()
            return a
        ALL.append(make)
        return make
    return deco


def tabards(a):
    """Tabard flaps follow the legs (sampled, quick follow-through)."""
    steps = max(4, int(a.length * 10))
    for i in range(steps + 1):
        t = a.length * i / steps
        r = a.sample("hip_r", "rotation", t) or [0, 0, 0]
        l = a.sample("hip_l", "rotation", t) or [0, 0, 0]
        front = max(-55.0, 0.8 * min(0.0, r[0], l[0]))
        back = min(55.0, 0.8 * max(0.0, r[0], l[0]))
        a.rot("tabard_front", t, front, 0, 0, "linear")
        a.rot("tabard_back", t, back, 0, 0, "linear")


@clip("idle", 3.0, True, "Powered stand-by: reactor hum, head holds, servo ticks")
def _(a):
    a.upright(0)
    for t, y in ((0.9, 0), (1.0, 12), (2.0, 12), (2.1, 0)):
        a.rot("head", t, 0, y, 0, "easeOutExpo")
    for t, b in ((0, 0), (1.5, 1), (3.0, 0)):
        a.pos("chest", t, 0, 0.12 * b, 0)
        a.arms(t, (0, 0, 4), -10 - 2 * b, ease="easeInOutSine")
        a.legs(t, (0, 0, 1), 0)
    a.sound(1.0, "doom_sovereign:doombot.servo")


@clip("scan_idle", 4.0, True, "Sentry scan: head sweeps in stepped arcs, optics pulse")
def _(a):
    a.upright(0)
    for t, y in ((0.0, 0), (0.4, -50), (1.2, -50), (1.6, 0), (2.4, 0), (2.8, 50), (3.6, 50), (4.0, 0)):
        a.rot("head", t, 4, y, 0, "easeOutExpo")
        a.rot("waist", t, 0, y * 0.25, 0, "easeOutExpo")
    for t, s in ((0, 1), (0.45, 1.5), (0.7, 1), (2.85, 1.5), (3.1, 1), (4.0, 1)):
        a.scl("eye_glow", t, s, s, s, "easeOutExpo")
    a.legs(0, (0, 0, 2), 0)
    a.sound(0.4, "doom_sovereign:scan.pulse").sound(2.8, "doom_sovereign:scan.pulse")
    a.sound(0.0, "doom_sovereign:doombot.servo")


@clip("walk", 1.0, True, "Mechanical patrol gait: level torso, short arm swing, heavy footfalls")
def _(a):
    keys = [(0.0, -22, 4, 18, 8, -0.4, 10), (0.25, -2, 5, -6, 40, 0.1, 0),
            (0.5, 18, 8, -22, 4, -0.4, -10), (0.75, -6, 40, -2, 5, 0.1, 0), (1.0, -22, 4, 18, 8, -0.4, 10)]
    for t, rh, rk, lh, lk, bob, sw in keys:
        a.hips(t, drop=-bob, yaw=sw * 0.3)
        a.rot("waist", t, 3, -sw * 0.3, 0)
        a.rot("head", t, 0, 0, 0)
        a.leg("r", t, (rh, 0, 1), rk)
        a.leg("l", t, (lh, 0, 1), lk)
        a.arm("r", t, (sw, 0, 4), -14, ease="easeInOutSine")
        a.arm("l", t, (-sw, 0, 4), -14, ease="easeInOutSine")
    a.sound(0.0, "doom_sovereign:doombot.step_heavy").sound(0.5, "doom_sovereign:doombot.step_heavy")
    a.cue(0.0, "footstep").cue(0.5, "footstep")


@clip("run", 0.6, True, "Pursuit run: forward lean, arms locked, long stride")
def _(a):
    keys = [(0.0, -38, 10, 32, 55, -0.8, 30), (0.15, -4, 20, -26, 90, 0.4, 0),
            (0.3, 32, 55, -38, 10, -0.8, -30), (0.45, -26, 90, -4, 20, 0.4, 0), (0.6, -38, 10, 32, 55, -0.8, 30)]
    for t, rh, rk, lh, lk, bob, sw in keys:
        a.hips(t, drop=-bob, pitch=4)
        a.rot("waist", t, 14, 0, 0)
        a.rot("head", t, -14, 0, 0)
        a.leg("r", t, (rh, 0, 1), rk)
        a.leg("l", t, (lh, 0, 1), lk)
        a.arm("r", t, (sw - 10, 0, 6), -70, ease="easeInOutSine")
        a.arm("l", t, (-sw - 10, 0, 6), -70, ease="easeInOutSine")
    a.sound(0.0, "doom_sovereign:doombot.step_heavy").sound(0.3, "doom_sovereign:doombot.step_heavy")


@clip("turn_look", 1.2, False, "Head snaps to a contact, torso follows, then settles")
def _(a):
    a.upright(0)
    a.rot("head", 0.12, 0, 60, 0, "easeOutExpo")
    a.rot("waist", 0.35, 0, 25, 0, "easeOutExpo")
    a.rot("head", 0.35, 0, 38, 0, "easeOutExpo")
    a.rot("head", 0.9, 0, 38, 0)
    a.rot("waist", 0.9, 0, 25, 0)
    a.upright(1.2)
    a.sound(0.1, "doom_sovereign:doombot.servo")


@clip("melee_strike", 0.8, False, "Overhead hammer-fist")
def _(a):
    a.upright(0)
    a.arm("r", 0.25, (-165, 0, 10), -60)
    a.rot("waist", 0.25, -10, 10, 0, "easeOutExpo")
    a.arm("r", 0.38, (-40, 0, 6), -10, ease="easeInExpo")
    a.rot("waist", 0.38, 20, -5, 0, "easeInExpo")
    a.hips(0.38, drop=1.0, ease="easeInExpo")
    for s in "rl":
        a.planted(s, 0.38, drop=1.0, foot_z=0, splay=3, ease="easeInExpo")
    a.upright(0.8)
    a.sound(0.36, "doom_sovereign:armor.impact_heavy")
    a.cue(0.38, "hit")


def aim(a, t, charge=0.0, ease="easeOutExpo"):
    a.hips(t, drop=0.5 + 0.5 * charge, ease=ease)
    for s, fz in (("r", -1.5), ("l", 1.5)):
        a.planted(s, t, drop=0.5 + 0.5 * charge, foot_z=fz, splay=4, ease=ease)
    a.rot("waist", t, 4 * charge, -10, 0, ease)
    a.rot("head", t, 0, 10, 0, ease)
    a.arm("r", t, (-88, 10, 0), -4, (0, 0, PALM), ease=ease)
    a.arm("l", t, (-60, 30, -20), -50, ease=ease)


@clip("ranged_aim", 1.0, True, "Emitter raised and locked on target")
def _(a):
    for t in (0, 0.5, 1.0):
        aim(a, t)
    a.scl("palm_emitter_r", 0, 1, 1, 1).scl("palm_emitter_r", 0.5, 1.1, 1.1, 1.1, "easeInOutSine").scl("palm_emitter_r", 1.0, 1, 1, 1)


@clip("ranged_charge", 1.0, "hold_on_last_frame", "Emitter spins up; the bot braces")
def _(a):
    aim(a, 0)
    aim(a, 1.0, charge=1.0, ease="easeInOutSine")
    a.scl("palm_emitter_r", 0, 1, 1, 1).scl("palm_emitter_r", 1.0, 1.7, 1.7, 1.7, "easeInQuad")
    a.sound(0.0, "doom_sovereign:gauntlet.charge")
    a.particle(0.1, "doom_sovereign:gauntlet_charge", "palm_emitter_r")


@clip("ranged_fire", 0.5, False, "Discharge and recoil")
def _(a):
    aim(a, 0, charge=1.0)
    a.arm("r", 0.06, (-76, 10, 0), -22, (0, 0, PALM))
    a.rot("waist", 0.06, -6, -14, 0, "easeOutExpo")
    aim(a, 0.3)
    a.scl("palm_emitter_r", 0, 1.7, 1.7, 1.7).scl("palm_emitter_r", 0.05, 2.2, 2.2, 2.2, "easeOutExpo").scl("palm_emitter_r", 0.25, 1, 1, 1)
    a.upright(0.5)
    a.sound(0.02, "doom_sovereign:gauntlet.discharge")
    a.particle(0.02, "doom_sovereign:gauntlet_muzzle", "palm_emitter_r")
    a.cue(0.02, "fire")


@clip("stagger", 0.7, False, "Knocked back: torso twists, a step back, arms thrown")
def _(a):
    a.upright(0)
    a.hips(0.1, drop=0.6, back=1.2, pitch=-8, yaw=14, ease="easeOutExpo")
    a.rot("waist", 0.1, -16, 10, 6, "easeOutExpo")
    a.rot("head", 0.1, -20, -14, 0, "easeOutExpo")
    a.arm("r", 0.1, (-40, 0, 40), -30)
    a.arm("l", 0.1, (-20, 0, 30), -20)
    a.leg("r", 0.1, (-18, 0, 4), 24, ease="easeOutExpo")
    a.leg("l", 0.1, (14, 0, 3), 10, ease="easeOutExpo")
    a.upright(0.7)
    a.sound(0.0, "doom_sovereign:doombot.servo")
    a.particle(0.02, "doom_sovereign:sparks", "spark_chest")


@clip("shield_brace", 0.35, "hold_on_last_frame", "Forearms crossed before the core, knees bent")
def _(a):
    a.upright(0)
    a.hips(0.35, drop=1.5)
    for s in "rl":
        a.planted(s, 0.35, drop=1.5, foot_z=0.5, splay=5)
    a.rot("waist", 0.35, 12, 0, 0)
    a.rot("head", 0.35, 10, 0, 0)
    a.arm("r", 0.35, (-80, 0, -24), -95)
    a.arm("l", 0.35, (-74, 0, -24), -95)


@clip("low_health_malfunction", 2.0, True, "Damaged: twitching servos, glitching head, sparks")
def _(a):
    a.upright(0)
    for t, (hx, hy, hz) in ((0.3, (0, 0, 0)), (0.32, (12, -20, 8)), (0.5, (12, -20, 8)), (0.52, (0, 0, 0)),
                            (1.2, (0, 0, 0)), (1.22, (-8, 26, -6)), (1.3, (-8, 26, -6)), (1.32, (0, 0, 0))):
        a.rot("head", t, hx, hy, hz, "step")
    a.arm("r", 0.9, (0, 0, 4), -10, ease="step").arm("r", 0.92, (-30, 0, 20), -60, ease="step")
    a.arm("r", 1.0, (-30, 0, 20), -60, ease="step").arm("r", 1.02, (0, 0, 4), -10, ease="step")
    for t, s in ((0.0, 1), (0.3, 0.2), (0.35, 1), (1.2, 1), (1.25, 0.3), (1.3, 1.1), (1.4, 1), (2.0, 1)):
        a.scl("eye_glow", t, s, s, s, "step")
    a.rot("waist", 0, 4, 0, 3).rot("waist", 1.0, 5, 0, 5).rot("waist", 2.0, 4, 0, 3)
    a.legs(0, (0, 0, 2), 4)
    a.sound(0.3, "doom_sovereign:doombot.diagnostic").sound(1.2, "doom_sovereign:doombot.servo")
    a.particle(0.32, "doom_sovereign:sparks", "spark_head").particle(0.92, "doom_sovereign:sparks", "spark_shoulder_l")


@clip("repair", 3.0, True, "Self-repair: left hand works over the damaged right forearm")
def _(a):
    for t, k in ((0, 0), (0.75, 1), (1.5, 0), (2.25, 1), (3.0, 0)):
        a.hips(t, drop=0.4)
        a.rot("waist", t, 18, 10, 0, "easeInOutSine")
        a.rot("head", t, 26, 12 + 4 * k, 0, "easeInOutSine")
        a.arm("r", t, (-52, 30, -10), -70, (0, 0, 20), ease="easeInOutSine")
        a.arm("l", t, (-60 - 6 * k, 30, -24), -70 + 6 * k, (10 * k, 0, 0), ease="easeInOutSine")
        a.legs(t, (0, 0, 2), 3)
    a.sound(0.2, "doom_sovereign:doombot.diagnostic")
    a.particle(0.75, "doom_sovereign:repair_weld", "hand_l").particle(2.25, "doom_sovereign:repair_weld", "hand_l")


@clip("shutdown", 1.5, "hold_on_last_frame", "Power-down: optics fade, head drops, arms fall slack")
def _(a):
    a.upright(0)
    a.scl("eye_glow", 0, 1, 1, 1).scl("eye_glow", 0.3, 1.2, 1.2, 1.2).scl("eye_glow", 1.2, 0, 0, 0, "easeInQuad")
    a.rot("head", 1.5, 32, 0, 0, "easeInOutQuad")
    a.rot("waist", 1.5, 10, 0, 0, "easeInOutQuad")
    a.arms(1.5, (-4, 0, 2), -2, ease="easeInOutQuad")
    a.hips(1.5, drop=0.6, ease="easeInOutQuad")
    for s in "rl":
        a.planted(s, 1.5, drop=0.6, foot_z=0.3, splay=2, ease="easeInOutQuad")
    a.sound(0.1, "doom_sovereign:doombot.shutdown")


@clip("death_collapse", 1.8, "hold_on_last_frame", "Destroyed: knees buckle, the frame topples forward and lies still")
def _(a):
    a.upright(0)
    a.rot("root", 0, 0, 0, 0)
    a.pos("root", 0, 0, 0, 0)
    a.hips(0.45, drop=3.5, pitch=6, ease="easeInQuad")
    for s in "rl":
        a.planted(s, 0.45, drop=3.5, foot_z=0.5, splay=4, ease="easeInQuad")
    a.rot("head", 0.45, 30, 20, 10, "easeInQuad")
    a.arms(0.45, (-20, 0, 12), -30, ease="easeInQuad")
    a.rot("root", 0.45, 0, 0, 0)
    a.rot("root", 1.15, 84, 0, 4, "easeInQuad")
    a.pos("root", 1.15, 0, 0, -3, "easeInQuad")
    a.rot("root", 1.3, 80, 0, 4, "easeOutQuad")
    a.rot("root", 1.45, 86, 0, 4, "easeInQuad")
    a.rot("root", 1.8, 85, 0, 4, "easeOutQuad")
    a.arms(1.15, (-150, 0, 40), -20)
    a.rot("head", 1.15, -30, 30, 10)
    a.rot("head", 1.8, -35, 34, 10)
    a.scl("eye_glow", 0, 1, 1, 1).scl("eye_glow", 1.2, 1.3, 1.3, 1.3, "step").scl("eye_glow", 1.8, 0, 0, 0, "easeInQuad")
    a.sound(0.0, "doom_sovereign:doombot.shutdown").sound(1.15, "doom_sovereign:armor.impact_heavy")
    a.particle(0.05, "doom_sovereign:sparks", "spark_chest").particle(1.15, "doom_sovereign:landing_shockwave", "chest")
    a.cue(1.15, "hit_ground")


@clip("command_acknowledgement", 0.8, False, "Order received: fist to chest, head dips, optics flash")
def _(a):
    a.upright(0)
    a.arm("r", 0.2, (-60, 0, -26), -120, (0, 0, 0))
    a.rot("head", 0.2, 0, 0, 0)
    a.rot("head", 0.32, 16, 0, 0, "easeOutExpo")
    a.rot("head", 0.5, 0, 0, 0)
    a.scl("eye_glow", 0, 1, 1, 1).scl("eye_glow", 0.3, 1.6, 1.6, 1.6, "easeOutExpo").scl("eye_glow", 0.5, 1, 1, 1)
    a.upright(0.8)
    a.sound(0.28, "doom_sovereign:doombot.diagnostic")
    a.cue(0.3, "acknowledged")


def build():
    return [make() for make in ALL]
