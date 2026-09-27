"""Rig helpers for authoring Royal Armor animations with plausible body mechanics.

The armour has separate root bones (head, body, arms, legs, boots) that vanilla positions
independently. To bow the torso, crouch or land, the roots must move together as if they were one
skeleton; these helpers compute the offsets so authored poses stay connected:

  torso(): pitches the body about the neck and moves the leg and arm roots with the hips and
           shoulders, plus an overall drop.
  leg_ik(): two-bone IK in the sagittal plane: hip offset + foot position -> hip angle and knee.
  arm_ik(): numeric IK for a hand target in Bedrock model space (deterministic search).
"""
import math

import numpy as np

from .anim import Anim
from . import render as R

THIGH = 6.0
SHIN = 6.0
PALM = 90.0            # gauntlet z for the repulsor (palm-forward) pose, right hand; left is -PALM

ROOTS = ("armorHead", "armorBody", "armorRightArm", "armorLeftArm", "armorRightLeg", "armorLeftLeg",
         "armorRightBoot", "armorLeftBoot")
UPPER = ("armorHead", "armorBody", "armorRightArm", "armorLeftArm")
LEGS = {"r": ("armorRightLeg", "armorRightBoot", "right_shin", "right_boot_knee"),
        "l": ("armorLeftLeg", "armorLeftBoot", "left_shin", "left_boot_knee")}
ARMS = {"r": ("armorRightArm", "right_forearm", "right_gauntlet"),
        "l": ("armorLeftArm", "left_forearm", "left_gauntlet")}


def leg_ik(hip_dy, hip_dz, foot_z=0.0, foot_y=0.0, thigh=THIGH, shin=SHIN):
    """Hip rx and knee flex (degrees) placing the ankle at (foot_z, foot_y) relative to the rest
    ankle, with the hip moved by (hip_dz, hip_dy). z positive is backward."""
    THIGH_, SHIN_ = thigh, shin
    hz, hy = hip_dz, thigh + shin + hip_dy
    fz, fy = foot_z, foot_y
    dz, dy = fz - hz, hy - fy
    d = min(math.hypot(dz, dy), THIGH_ + SHIN_ - 1e-6)
    inner = math.degrees(math.acos((THIGH_ ** 2 + SHIN_ ** 2 - d * d) / (2 * THIGH_ * SHIN_)))
    knee = 180.0 - inner
    phi = math.degrees(math.atan2(dz, dy))                      # direction hip -> foot, back positive
    off = math.degrees(math.acos(max(-1.0, min(1.0, (THIGH_ ** 2 + d * d - SHIN_ ** 2) / (2 * THIGH_ * d)))))
    return phi - off, knee


class ArmorAnim(Anim):
    """Anim with rig-aware helpers. Left-side values are mirrored automatically."""

    def arm(self, side, t, sh=(0, 0, 0), el=0.0, wr=(0, 0, 0), twist=0.0, ease="easeInOutSine"):
        a, f, g = ARMS[side]
        m = 1 if side == "r" else -1
        self.rot(a, t, sh[0], m * sh[1], m * sh[2], ease)
        self.rot(f, t, el, m * twist, 0, ease)
        self.rot(g, t, wr[0], m * wr[1], m * wr[2], ease)
        return self

    def arms(self, t, sh=(0, 0, 0), el=0.0, wr=(0, 0, 0), twist=0.0, ease="easeInOutSine"):
        self.arm("r", t, sh, el, wr, twist, ease)
        return self.arm("l", t, sh, el, wr, twist, ease)

    def leg(self, side, t, hip=(0, 0, 0), knee=0.0, ease="easeInOutSine"):
        root, boot, shin, bknee = LEGS[side]
        m = 1 if side == "r" else -1
        for b in (root, boot):
            self.rot(b, t, hip[0], m * hip[1], m * hip[2], ease)
        for b in (shin, bknee):
            self.rot(b, t, knee, 0, 0, ease)
        return self

    def legs(self, t, hip=(0, 0, 0), knee=0.0, ease="easeInOutSine"):
        self.leg("r", t, hip, knee, ease)
        return self.leg("l", t, hip, knee, ease)

    def torso(self, t, pitch=0.0, yaw=0.0, roll=0.0, drop=0.0, fwd=0.0, arm_follow=True, ease="easeInOutSine",
              leg_offsets=True):
        """Pitches the body about the neck, moving the hips (leg roots) and shoulders (arm roots)
        with it, then drops/shifts the whole figure. Returns the hip offset (dy, dz)."""
        th = math.radians(pitch)
        hip_dy = -12.0 * (1 - math.cos(th)) - drop
        hip_dz = 12.0 * math.sin(th) - fwd
        sh_dy = -2.0 * (1 - math.cos(th)) - drop
        sh_dz = 2.0 * math.sin(th) - fwd
        self.rot("armorBody", t, pitch, yaw, roll, ease)
        for b in ("armorHead", "armorBody"):
            self.pos(b, t, 0, -drop, -fwd, ease)
        for b in ("armorRightArm", "armorLeftArm"):
            self.pos(b, t, 0, sh_dy, sh_dz, ease)
        if leg_offsets:
            for b in ("armorRightLeg", "armorLeftLeg", "armorRightBoot", "armorLeftBoot"):
                self.pos(b, t, 0, hip_dy, hip_dz, ease)
        return hip_dy, hip_dz

    def planted(self, side, t, hip_dy, hip_dz, foot_z=0.0, foot_y=0.0, splay=0.0, twist=0.0, ease="easeInOutSine"):
        """Leg pose from IK so the foot stays at (foot_z, foot_y)."""
        hx, k = leg_ik(hip_dy, hip_dz, foot_z, foot_y)
        return self.leg(side, t, (hx, twist, splay), k, ease)

    def head(self, t, x=0.0, y=0.0, z=0.0, ease="easeInOutSine"):
        return self.rot("armorHead", t, x, y, z, ease)

    def whole(self, t, dy=0.0, dz=0.0, ease="easeInOutSine"):
        for b in ROOTS:
            self.pos(b, t, 0, dy, dz, ease)
        return self

    def close_loop(self):
        """Makes every track start at 0 and end at the length with identical values."""
        for key, tr in self.tracks.items():
            ts = sorted(tr)
            if ts[0] > 0:
                tr[0.0] = (list(tr[ts[0]][0]), "linear")
            ts = sorted(tr)
            first = tr[ts[0]][0]
            if self.length in tr:
                if any(abs(a - b) > 1e-3 for a, b in zip(first, tr[self.length][0])):
                    raise ValueError("%s %s: loop end differs from start" % (self.name, key))
            else:
                tr[round(self.length, 4)] = (list(first), tr[ts[1]][1] if len(ts) > 1 else "linear")
        return self


# ---- arm IK ------------------------------------------------------------------------------------------
_MODEL = None


def _model():
    global _MODEL
    if _MODEL is None:
        from . import royal_armor
        _MODEL = royal_armor.build()
    return _MODEL


def hand_point(pose, side):
    """Gauntlet centre in Bedrock model space for a pose."""
    m = _model()
    mats = R.bone_matrices(m, pose)
    bone = ARMS[side][2]
    px = -6.0 if side == "r" else 6.0
    g = mats[bone] @ np.array([-px, 11.5, 0.0, 1.0])
    return np.array([-g[0], g[1], g[2]])


def arm_ik(side, target, prefer=(0, 0, 0, -20), extra_pose=None, iters=3000, seed=7):
    """Finds (sh_x, sh_y, sh_z, elbow) for the right-side convention placing the hand at
    ``target`` (Bedrock space) - for the left arm pass the mirrored target; the returned values
    are right-side conventions (ArmorAnim.arm mirrors them)."""
    import random
    m = _model()
    arm_b, fore_b, _ = ARMS["r"]
    lim = [m.by_name[arm_b].dof.get(a, (-180, 180)) for a in "xyz"] + [m.by_name[fore_b].dof["x"]]
    tgt = np.array(target, float)
    if side == "l":
        tgt = tgt * np.array([-1, 1, 1])

    def cost(v):
        pose = dict(extra_pose or {})
        pose[arm_b] = {"rotation": [v[0], v[1], v[2]]}
        pose[fore_b] = {"rotation": [v[3], 0, 0]}
        d = hand_point(pose, "r") - tgt
        return float(d @ d) + 0.0004 * sum((a - b) ** 2 for a, b in zip(v, prefer))

    rng = random.Random(seed)
    best = list(prefer)
    bc = cost(best)
    step = 40.0
    for i in range(iters):
        cand = [min(max(best[k] + rng.gauss(0, step), lim[k][0]), lim[k][1]) for k in range(4)]
        c = cost(cand)
        if c < bc:
            best, bc = cand, c
        if i % 300 == 299:
            step *= 0.6
    return [round(v, 1) for v in best], math.sqrt(max(0.0, bc))
