"""Tests for the art pipeline itself: the validators must reject broken input, not just pass good input.

    python3 -m unittest discover -s art/tests -v      (from doom-sovereign/)
"""
import copy
import json
import math
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ART = os.path.dirname(HERE)
sys.path.insert(0, ART)

import numpy as np

from doomart import anim as A, anim_armor, anim_doombot, doombot as DB, doom_mask as DM, royal_armor as RA, rig, render as R
from doomart.geo import Model
from doomart.paint import Painter, palette_violations
from doomart.palette import COLORS
from doomart import synth as S

ASSETS = os.path.join(os.path.dirname(ART), "mod", "src", "main", "resources", "assets", "doom_sovereign")


def armor():
    m = RA.build()
    m.pack()
    return m


class GeometryTests(unittest.TestCase):
    def test_models_validate_and_do_not_overlap(self):
        for build in (RA.build, DM.build, DB.build):
            m = build()
            m.pack()
            self.assertEqual([], m.validate(), m.identifier)

    def test_overlap_is_detected(self):
        m = Model("geometry.test", 32, 32)
        b = m.bone("b", None, (0, 0, 0))
        c1 = b.cube("a", (0, 0, 0), (4, 4, 4), "steel")
        c2 = b.cube("b", (0, 0, 0), (4, 4, 4), "steel")
        c1.uv = (0, 0)
        c2.uv = (2, 2)
        self.assertTrue(any("overlap" in p for p in m.validate()))

    def test_fractional_sizes_are_rejected(self):
        m = Model("geometry.test", 32, 32)
        b = m.bone("b", None, (0, 0, 0))
        with self.assertRaises(ValueError):
            b.cube("x", (0, 0, 0), (1.5, 1, 1), "steel")

    def test_packing_fails_loudly_when_the_texture_is_too_small(self):
        m = RA.build()
        m.tex_w, m.tex_h = 32, 32
        with self.assertRaises(ValueError):
            m.pack()

    def test_mirroring_negates_x_and_reuses_uv(self):
        m = armor()
        r, l = m.by_name["armorRightArm"], m.by_name["armorLeftArm"]
        self.assertEqual(r.pivot[0], -l.pivot[0])
        rc = m.by_name["right_forearm"].cubes[0]
        lc = m.by_name["left_forearm"].cubes[0]
        self.assertEqual(rc.uv, lc.uv)
        self.assertTrue(lc.mirror)
        self.assertAlmostEqual(rc.origin[0], -(lc.origin[0] + lc.size[0]))

    def test_exported_geometry_round_trips(self):
        m = armor()
        j = json.loads(json.dumps(m.to_json()))
        g = j["minecraft:geometry"][0]
        self.assertEqual(g["description"]["texture_width"], 128)
        self.assertEqual(len(g["bones"]), len(m.bones))


class TextureTests(unittest.TestCase):
    def test_every_generated_texture_is_on_palette(self):
        allowed = set(COLORS.values())
        bad = []
        for root, _, files in os.walk(os.path.join(ASSETS, "textures")):
            for f in files:
                if f.endswith(".png"):
                    from PIL import Image
                    a = np.array(Image.open(os.path.join(root, f)).convert("RGBA"))
                    px = {tuple(p) for p in a.reshape(-1, 4)[a.reshape(-1, 4)[:, 3] > 0][:, :3]}
                    if px - allowed:
                        bad.append(f)
        self.assertEqual([], bad)

    def test_textures_have_the_size_their_users_expect(self):
        """Guards against two generators writing the same path (the hero mask once overwrote the icon)."""
        from PIL import Image
        tex = os.path.join(ASSETS, "textures")
        self.assertEqual((16, 16), Image.open(os.path.join(tex, "item", "doom_mask.png")).size)
        self.assertEqual((64, 64), Image.open(os.path.join(tex, "item", "doom_mask_hero.png")).size)
        self.assertEqual((128, 128), Image.open(os.path.join(tex, "armor", "royal_armor.png")).size)
        self.assertEqual((64, 64), Image.open(os.path.join(tex, "entity", "doombot", "doombot_standard.png")).size)
        for f in os.listdir(os.path.join(tex, "item")):
            size = Image.open(os.path.join(tex, "item", f)).size
            self.assertEqual((64, 64) if f.startswith("doom_mask_hero") else (16, 16), size, f)

    def test_palette_checker_catches_foreign_colours(self):
        a = np.zeros((2, 2, 4), np.uint8)
        a[0, 0] = (255, 0, 0, 255)
        self.assertEqual(1, palette_violations(a))

    def test_damage_changes_pixels_but_not_layout(self):
        m = armor()
        clean, _ = Painter(m, RA.DECORATIONS, 0).paint()
        worn, _ = Painter(m, RA.DECORATIONS, 2).paint()
        self.assertGreater(int(np.sum(np.any(clean != worn, axis=2))), 50)
        # damage never paints outside the UV islands of the clean texture
        self.assertFalse(np.any((clean[..., 3] == 0) & (worn[..., 3] > 0)))

    def test_glow_states_are_ordered(self):
        m = armor()
        lit = {g: int(np.sum(Painter(m, RA.DECORATIONS, 0, g).paint()[1][..., 3] > 0)) for g in ("off", "low", "powered", "arcane")}
        self.assertEqual(0, lit["off"])
        self.assertLess(lit["low"], lit["arcane"])
        self.assertLessEqual(lit["low"], lit["powered"])

    def test_painting_is_deterministic(self):
        m = armor()
        a, _ = Painter(m, RA.DECORATIONS, 1).paint()
        b, _ = Painter(armor(), RA.DECORATIONS, 1).paint()
        self.assertTrue(np.array_equal(a, b))


class AnimationValidatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = armor()
        with open(os.path.join(ASSETS, "geckolib", "animations", "armor", "royal_armor.animation.json")) as f:
            cls.doc = json.load(f)

    def validate(self, doc):
        return A.validate(doc, self.m, linked=RA.LINKED, root_motion=rig.ROOTS)

    def test_shipped_library_is_clean(self):
        self.assertEqual([], self.validate(self.doc))
        self.assertEqual(39, len(self.doc["animations"]))

    def mutated(self, fn):
        d = copy.deepcopy(self.doc)
        fn(d["animations"]["animation.royal_armor.walk"])
        return self.validate(d)

    def test_unknown_bone(self):
        self.assertTrue(self.mutated(lambda a: a["bones"].__setitem__("tail", {"rotation": {"0.0": {"vector": [0, 0, 0]}}})))

    def test_joint_limit(self):
        def bend(a):
            a["bones"]["right_shin"]["rotation"]["0.3"] = {"vector": [-40, 0, 0]}   # knee bending backwards
        probs = self.mutated(bend)
        self.assertTrue(any("right_shin" in p and "outside" in p for p in probs), probs)

    def test_undeclared_axes_are_fixed(self):
        def twist_belt(a):
            a["bones"]["belt"] = {"rotation": {"0.0": {"vector": [0, 0, 0]}, "0.6": {"vector": [0, 20, 0]}, "1.2": {"vector": [0, 0, 0]}}}
        self.assertTrue(any("belt" in p and "outside" in p for p in self.mutated(twist_belt)))

    def test_broken_loop_seam(self):
        def seam(a):
            a["bones"]["armorHead"]["rotation"]["1.2"] = {"vector": [20, 0, 0]}
        self.assertTrue(any("loop" in p for p in self.mutated(seam)))

    def test_linked_knee_desync(self):
        def desync(a):
            a["bones"]["right_boot_knee"]["rotation"]["0.3"] = {"vector": [80, 0, 0]}
        self.assertTrue(any("must equal" in p for p in self.mutated(desync)))

    def test_bad_easing_and_vector(self):
        def bad(a):
            k = a["bones"]["armorHead"]["rotation"]
            first = sorted(k, key=float)[1]
            k[first] = {"vector": [0, 0], "easing": "easeWobbly"}
        probs = self.mutated(bad)
        self.assertTrue(any("easing" in p for p in probs) and any("3 finite" in p for p in probs), probs)

    def test_key_outside_length(self):
        self.assertTrue(self.mutated(lambda a: a["bones"]["armorHead"]["rotation"].__setitem__("9.0", {"vector": [0, 0, 0]})))

    def test_unknown_sound(self):
        d = copy.deepcopy(self.doc)
        d["animations"]["animation.royal_armor.walk"]["sound_effects"]["0.0"]["effect"] = "doom_sovereign:nope"
        self.assertTrue(A.validate(d, self.m, known_sounds={"doom_sovereign:armor.step_heavy"}, root_motion=rig.ROOTS))

    def test_easings_hit_their_endpoints(self):
        for name, f in A.EASINGS.items():
            self.assertAlmostEqual(0.0, f(0.0), 6, name)
            self.assertAlmostEqual(1.0, f(1.0), 6, name)


class RigTests(unittest.TestCase):
    def test_leg_ik_reaches_its_target(self):
        m = armor()
        for (dy, dz, fz) in ((-2.0, 0.0, 0.0), (-3.4, 4.5, 1.5), (-1.0, 2.0, -2.0)):
            hx, knee = rig.leg_ik(dy, dz, fz)
            mats = R.bone_matrices(m, {"armorRightLeg": {"rotation": [hx, 0, 0], "position": [0, dy, dz]},
                                       "right_shin": {"rotation": [knee, 0, 0]}})
            ankle = mats["right_shin"] @ np.array([1.9, 0.0, 0.0, 1.0])   # gecko space: x negated
            self.assertAlmostEqual(ankle[1], 0.0, 3)
            self.assertAlmostEqual(ankle[2], fz, 3)

    def test_rest_pose_puts_hands_at_the_model_hands(self):
        self.assertTrue(np.allclose(rig.hand_point({}, "r"), [-6, 11.5, 0]))


class AudioTests(unittest.TestCase):
    def test_report_meets_the_loudness_rules(self):
        with open(os.path.join(ART, "audio_report.json")) as f:
            rep = json.load(f)
        self.assertGreaterEqual(len(rep), 30)
        for r in rep:
            self.assertLessEqual(r["peak_dbfs"], -1.0, r["event"])
            self.assertEqual(1, r["channels"], r["event"])
            self.assertEqual(0, r["clipped"], r["event"])
            if r["kind"] == "loop":
                self.assertLess(r["loop_seam_ratio"], 1.0, r["event"])

    def test_loops_are_seamless_before_encoding(self):
        n = int(1.0 * S.SR)
        x = S.saw(110, n, 20) + S.noise(n, 1) * 0.1
        y = S.make_loop(x, 0.05)
        typical = np.percentile(np.abs(np.diff(y)), 99)
        self.assertLess(abs(y[0] - y[-1]), typical)

    def test_sounds_json_points_at_real_files(self):
        with open(os.path.join(ASSETS, "sounds.json")) as f:
            sj = json.load(f)
        for ev, e in sj.items():
            for s in e["sounds"]:
                path = os.path.join(ASSETS, "sounds", s["name"].split(":", 1)[1] + ".ogg")
                self.assertTrue(os.path.exists(path), path)


if __name__ == "__main__":
    unittest.main()
