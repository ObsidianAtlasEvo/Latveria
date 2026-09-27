# Royal Armor skeleton

The one bone hierarchy every Royal Armor clip targets (`geckolib/models/armor/royal_armor.geo.json`). Root bone names follow GeckoLib's armour-renderer convention.

Coordinates: Bedrock geometry space, 1 unit = 1 model pixel (16 per block), +y up, the model's front faces -z,
the model's right side is -x. Pivots are absolute. Rotations are degrees; limits below are the ranges the
animation validator enforces for rest rotation + animated rotation. Sign conventions (from the transform
emulation in `art/doomart/render.py`, awaiting in-game confirmation): limb x negative = swing forward, right
limb z positive = outward, elbow x negative = flex, knee x positive = flex, head/body x positive = pitch down.

| Bone | Parent | Pivot | Rest rotation | Rotation limits (DOF) | Cubes | Purpose |
|---|---|---|---|---|---|---|
| `armorHead` | (root) | (0, 24, 0) | - | x -60..60, y -80..80, z -35..35 | 0 | Head root (follows vanilla head) |
| `hood` | `armorHead` | (0, 24, 0) | - | x -10..10, y -5..5, z -5..5 | 5 | Cloth hood; secondary sway only |
| `mask` | `armorHead` | (0, 28, -4.5) | - | x -8..8, y -5..5, z -5..5 | 2 | Mask assembly; root of the lock sequence |
| `mask_brow` | `mask` | (0, 30.5, -5) | - | x -20..10, y 0..0, z 0..0 | 1 | Brow ridge; drops into place during the lock |
| `mask_cheek_r` | `mask` | (-4, 28, -4.5) | - | x 0..0, y -45..5, z -5..5 | 1 | Right cheek guard; swings in and clamps during the lock |
| `mask_cheek_l` | `mask` | (4, 28, -4.5) | - | x 0..0, y -5..45, z -5..5 | 1 | Left cheek guard; swings in and clamps during the lock |
| `mask_jaw` | `mask` | (0, 24.5, -5) | - | x -5..25, y 0..0, z 0..0 | 1 | Jaw plate with the grille; slides up and seals last |
| `mask_eye_glow` | `mask` | (0, 29.5, -5.2) | - | x 0..0, y 0..0, z 0..0 | 2 | Eye flare planes (emissive only); scaled 0->1 to ignite the eyes |
| `armorBody` | (root) | (0, 24, 0) | - | x -45..70, y -70..70, z -35..35 | 0 | Body root (follows vanilla body) |
| `tunic` | `armorBody` | (0, 24, 0) | - | fixed (driven only through its parent) | 1 | Green tunic under the plates |
| `gorget` | `armorBody` | (0, 24, 0) | - | x -10..10, y -15..15, z -5..5 | 1 | Neck ring; follows the head a little |
| `chest` | `armorBody` | (0, 20, -2.5) | - | x -8..8, y 0..0, z 0..0 | 3 | Breastplate and backplate; breathing motion |
| `abdomen_1` | `armorBody` | (0, 17, -2.6) | - | x -15..25, y fixed, z fixed | 1 | Upper abdominal lame |
| `abdomen_2` | `abdomen_1` | (0, 15.5, -2.5) | - | x -15..25, y fixed, z fixed | 1 | Middle abdominal lame |
| `abdomen_3` | `abdomen_2` | (0, 14, -2.4) | - | x -15..25, y fixed, z fixed | 1 | Lower abdominal lame |
| `belt` | `armorBody` | (0, 12, 0) | - | fixed (driven only through its parent) | 4 | Belt, buckle and hip pouches |
| `tunic_flap` | `armorBody` | (0, 10, -3.2) | - | x -60..15, y 0..0, z -10..10 | 1 | Front tunic flap below the belt; secondary motion |
| `tunic_flap_back` | `armorBody` | (0, 10, 2.8) | - | x -15..60, y 0..0, z -10..10 | 1 | Rear tunic flap below the belt (under the cloak); secondary motion |
| `cloak_root` | `armorBody` | (0, 23.5, 3) | - | x -10..30, y -10..10, z -10..10 | 3 | Cloak mantle and clasps; parent of the three cloak columns |
| `cloak_c_1` | `cloak_root` | (0, 23.5, 3.5) | (4, 0, 0) | x -25..100, y -30..30, z -30..30 | 1 | Cloak centre column, upper segment |
| `cloak_c_2` | `cloak_c_1` | (0, 15.5, 3.5) | (3, 0, 0) | x -25..100, y -30..30, z -30..30 | 1 | Cloak centre column, middle segment |
| `cloak_c_3` | `cloak_c_2` | (0, 7.5, 3.5) | (3, 0, 0) | x -25..100, y -30..30, z -30..30 | 1 | Cloak centre column, lower segment (hem) |
| `cloak_r_1` | `cloak_root` | (-3.5, 23.5, 3.5) | (4, 0, 3) | x -25..100, y -30..30, z -30..30 | 1 | Cloak right column, upper segment |
| `cloak_r_2` | `cloak_r_1` | (-3.5, 15.5, 3.5) | (3, 0, 0) | x -25..100, y -30..30, z -30..30 | 1 | Cloak right column, middle segment |
| `cloak_r_3` | `cloak_r_2` | (-3.5, 7.5, 3.5) | (3, 0, 0) | x -25..100, y -30..30, z -30..30 | 1 | Cloak right column, lower segment (hem) |
| `cloak_l_1` | `cloak_root` | (3.5, 23.5, 3.5) | (4, -0, -3) | x -25..100, y -30..30, z -30..30 | 1 | Cloak left column, upper segment |
| `cloak_l_2` | `cloak_l_1` | (3.5, 15.5, 3.5) | (3, -0, -0) | x -25..100, y -30..30, z -30..30 | 1 | Cloak left column, middle segment |
| `cloak_l_3` | `cloak_l_2` | (3.5, 7.5, 3.5) | (3, -0, -0) | x -25..100, y -30..30, z -30..30 | 1 | Cloak left column, lower segment (hem) |
| `armorRightArm` | (root) | (-5, 22, 0) | - | x -190..60, y -90..90, z -30..120 | 0 | Right arm root (follows vanilla right arm) |
| `right_pauldron` | `armorRightArm` | (-5, 23, 0) | - | x -20..20, y -10..10, z -10..35 | 2 | Right pauldron; lifts when the arm rises |
| `right_pauldron_lame` | `right_pauldron` | (-8, 21, 0) | - | x -15..15, y 0..0, z 0..25 | 1 | Lower pauldron lame; secondary flap |
| `right_upper_arm` | `armorRightArm` | (-5, 22, 0) | - | x -10..10, y -10..10, z -10..10 | 2 | Sleeve and rerebrace |
| `right_forearm` | `right_upper_arm` | (-6, 17, 0) | - | x -150..5, y -95..95, z -10..10 | 2 | Elbow: couter and vambrace. Flexion is negative x |
| `right_gauntlet` | `right_forearm` | (-6, 12.5, 0) | - | x -70..70, y -60..60, z -45..95 | 2 | Wrist and gauntlet; z = +90 turns the palm lens to face along the arm (repulsor pose) |
| `right_palm_emitter` | `right_gauntlet` | (-4, 11, 0) | - | x 0..0, y 0..0, z 0..0 | 1 | Palm repulsor lens; blast origin and emissive; scale pulses on charge |
| `armorLeftArm` | (root) | (5, 22, 0) | - | x -190..60, y -90..90, z -120..30 | 0 | Left arm root (follows vanilla left arm) |
| `left_pauldron` | `armorLeftArm` | (5, 23, 0) | - | x -20..20, y -10..10, z -35..10 | 2 | Left pauldron; lifts when the arm rises |
| `left_upper_arm` | `armorLeftArm` | (5, 22, 0) | - | x -10..10, y -10..10, z -10..10 | 2 | Sleeve and rerebrace |
| `left_pauldron_lame` | `left_pauldron` | (8, 21, 0) | - | x -15..15, y 0..0, z -25..0 | 1 | Lower pauldron lame; secondary flap |
| `left_forearm` | `left_upper_arm` | (6, 17, 0) | - | x -150..5, y -95..95, z -10..10 | 2 | Elbow: couter and vambrace. Flexion is negative x |
| `left_gauntlet` | `left_forearm` | (6, 12.5, 0) | - | x -70..70, y -60..60, z -95..45 | 2 | Wrist and gauntlet; z = +90 turns the palm lens to face along the arm (repulsor pose) |
| `left_palm_emitter` | `left_gauntlet` | (4, 11, 0) | - | x 0..0, y 0..0, z 0..0 | 1 | Palm repulsor lens; blast origin and emissive; scale pulses on charge |
| `armorRightLeg` | (root) | (-1.9, 12, 0) | - | x -120..70, y -35..35, z -10..45 | 0 | Right leg root (follows vanilla right leg) |
| `right_thigh` | `armorRightLeg` | (-1.9, 12, 0) | - | x -10..10, y fixed, z fixed | 1 | Cuisse |
| `right_tasset` | `right_thigh` | (-2, 12, -2.6) | - | x -50..10, y 0..0, z -10..10 | 1 | Tasset hanging from the belt over the thigh |
| `right_tasset_lower` | `right_tasset` | (-2, 8.5, -2.8) | - | x -30..10, y fixed, z fixed | 1 | Lower tasset lame |
| `right_shin` | `right_thigh` | (-1.9, 6, 0) | - | x 0..150, y -15..15, z -5..5 | 2 | Knee: greave and poleyn. Flexion is positive x |
| `armorRightBoot` | (root) | (-1.9, 12, 0) | - | x -120..70, y -35..35, z -10..45 | 0 | Right boot root (follows vanilla right leg) |
| `right_boot_knee` | `armorRightBoot` | (-1.9, 6, 0) | - | x 0..150, y -15..15, z -5..5 | 3 | Boot copy of the knee; animations must keep it equal to right_shin |
| `armorLeftLeg` | (root) | (1.9, 12, 0) | - | x -120..70, y -35..35, z -45..10 | 0 | Left leg root (follows vanilla left leg) |
| `left_thigh` | `armorLeftLeg` | (1.9, 12, 0) | - | x -10..10, y fixed, z fixed | 1 | Cuisse |
| `left_tasset` | `left_thigh` | (2, 12, -2.6) | - | x -50..10, y 0..0, z -10..10 | 1 | Tasset hanging from the belt over the thigh |
| `left_shin` | `left_thigh` | (1.9, 6, 0) | - | x 0..150, y -15..15, z -5..5 | 2 | Knee: greave and poleyn. Flexion is positive x |
| `left_tasset_lower` | `left_tasset` | (2, 8.5, -2.8) | - | x -30..10, y fixed, z fixed | 1 | Lower tasset lame |
| `armorLeftBoot` | (root) | (1.9, 12, 0) | - | x -120..70, y -35..35, z -45..10 | 0 | Left boot root (follows vanilla left leg) |
| `left_boot_knee` | `armorLeftBoot` | (1.9, 6, 0) | - | x 0..150, y -15..15, z -5..5 | 3 | Boot copy of the knee; animations must keep it equal to left_shin |

Hierarchy:

```
armorHead
  hood
  mask
    mask_brow
    mask_cheek_r
    mask_cheek_l
    mask_jaw
    mask_eye_glow
armorBody
  tunic
  gorget
  chest
  abdomen_1
    abdomen_2
      abdomen_3
  belt
  tunic_flap
  tunic_flap_back
  cloak_root
    cloak_c_1
      cloak_c_2
        cloak_c_3
    cloak_r_1
      cloak_r_2
        cloak_r_3
    cloak_l_1
      cloak_l_2
        cloak_l_3
armorRightArm
  right_pauldron
    right_pauldron_lame
  right_upper_arm
    right_forearm
      right_gauntlet
        right_palm_emitter
armorLeftArm
  left_pauldron
    left_pauldron_lame
  left_upper_arm
    left_forearm
      left_gauntlet
        left_palm_emitter
armorRightLeg
  right_thigh
    right_tasset
      right_tasset_lower
    right_shin
armorRightBoot
  right_boot_knee
armorLeftLeg
  left_thigh
    left_tasset
      left_tasset_lower
    left_shin
armorLeftBoot
  left_boot_knee
```

Linked bones (must be animated identically; the validator checks every sampled frame):

- `right_boot_knee` = `right_shin`
- `left_boot_knee` = `left_shin`
- `armorRightBoot` = `armorRightLeg`
- `armorLeftBoot` = `armorLeftLeg`

Texture: 128x128, box UV, 75 cubes. Geometry identifier `geometry.doom_sovereign.royal_armor`.
