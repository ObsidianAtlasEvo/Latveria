# Doombot skeleton (reusable)

Shared by every Doombot variant: variants change cubes and textures, never bone names or pivots, so all Doombot clips apply to all variants.

Coordinates: Bedrock geometry space, 1 unit = 1 model pixel (16 per block), +y up, the model's front faces -z,
the model's right side is -x. Pivots are absolute. Rotations are degrees; limits below are the ranges the
animation validator enforces for rest rotation + animated rotation. Sign conventions (from the transform
emulation in `art/doomart/render.py`, awaiting in-game confirmation): limb x negative = swing forward, right
limb z positive = outward, elbow x negative = flex, knee x positive = flex, head/body x positive = pitch down.

| Bone | Parent | Pivot | Rest rotation | Rotation limits (DOF) | Cubes | Purpose |
|---|---|---|---|---|---|---|
| `root` | (root) | (0, 0, 0) | - | x -95..95, y -180..180, z -95..95 | 0 | Entity root; whole-body falls and collapses |
| `pelvis` | `root` | (0, 13, 0) | - | x -40..40, y -45..45, z -20..20 | 2 | Hips; moving it moves torso and legs together |
| `tabard_front` | `pelvis` | (0, 11.5, -3.2) | - | x -60..15, y 0..0, z -10..10 | 1 | Green service tabard (front); secondary motion |
| `tabard_back` | `pelvis` | (0, 11.5, 2.8) | - | x -15..60, y 0..0, z -10..10 | 1 | Green service tabard (back) |
| `waist` | `pelvis` | (0, 14, 0) | - | x -40..60, y -70..70, z -25..25 | 3 | Spine actuator between pelvis and chest |
| `chest` | `waist` | (0, 19, 0) | - | x -20..30, y -30..30, z -15..15 | 4 | Chest shell with the reactor core |
| `neck` | `chest` | (0, 27, 0) | - | x -20..20, y -40..40, z -10..10 | 1 | Neck actuator |
| `head` | `neck` | (0, 28.5, 0) | - | x -45..45, y -90..90, z -25..25 | 4 | Sensor head in the master's likeness |
| `eye_glow` | `head` | (0, 32.5, -3.9) | - | fixed (driven only through its parent) | 2 | Optic flare planes (emissive); scaled for scan pulses |
| `shoulder_r` | `chest` | (-6, 25.5, 0) | - | x -180..60, y -90..90, z -35..120 | 2 | Right shoulder; x negative raises the arm forward |
| `forearm_r` | `shoulder_r` | (-6.5, 19.5, 0) | - | x -140..5, y -90..90, z -10..10 | 2 | Right elbow; x negative flexes |
| `hand_r` | `forearm_r` | (-6.5, 13, 0) | - | x -60..60, y -60..60, z -45..95 | 1 | Right hand; z = +90 turns the palm emitter along the arm |
| `palm_emitter_r` | `hand_r` | (-4.5, 11, 0) | - | fixed (driven only through its parent) | 1 | Palm emitter lens; weapon origin |
| `shoulder_l` | `chest` | (6, 25.5, 0) | - | x -180..60, y -90..90, z -120..35 | 2 | Left shoulder; x negative raises the arm forward |
| `forearm_l` | `shoulder_l` | (6.5, 19.5, 0) | - | x -140..5, y -90..90, z -10..10 | 2 | Left elbow; x negative flexes |
| `hand_l` | `forearm_l` | (6.5, 13, 0) | - | x -60..60, y -60..60, z -95..45 | 1 | Left hand; z = +90 turns the palm emitter along the arm |
| `palm_emitter_l` | `hand_l` | (4.5, 11, 0) | - | fixed (driven only through its parent) | 1 | Palm emitter lens; weapon origin |
| `hip_r` | `pelvis` | (-2.5, 12, 0) | - | x -110..60, y -30..30, z -10..40 | 1 | Right hip; x negative swings the leg forward |
| `shin_r` | `hip_r` | (-2.5, 7.5, 0) | - | x 0..140, y -10..10, z -5..5 | 2 | Right knee; x positive flexes |
| `foot_r` | `shin_r` | (-2.5, 2, 0) | - | x -50..50, y -10..10, z -15..15 | 1 | Right ankle; keep the sole flat when planted |
| `hip_l` | `pelvis` | (2.5, 12, 0) | - | x -110..60, y -30..30, z -40..10 | 1 | Left hip; x negative swings the leg forward |
| `shin_l` | `hip_l` | (2.5, 7.5, 0) | - | x 0..140, y -10..10, z -5..5 | 2 | Left knee; x positive flexes |
| `foot_l` | `shin_l` | (2.5, 2, 0) | - | x -50..50, y -10..10, z -15..15 | 1 | Left ankle; keep the sole flat when planted |
| `spark_chest` | `chest` | (2, 24, -3.2) | - | fixed (driven only through its parent) | 0 | Particle locator (no geometry) |
| `spark_head` | `head` | (-2, 34, -2) | - | fixed (driven only through its parent) | 0 | Particle locator (no geometry) |
| `spark_shoulder_l` | `shoulder_l` | (7.5, 25, 0) | - | fixed (driven only through its parent) | 0 | Particle locator (no geometry) |

Hierarchy:

```
root
  pelvis
    tabard_front
    tabard_back
    waist
      chest
        neck
          head
            eye_glow
            spark_head
        shoulder_r
          forearm_r
            hand_r
              palm_emitter_r
        shoulder_l
          forearm_l
            hand_l
              palm_emitter_l
          spark_shoulder_l
        spark_chest
    hip_r
      shin_r
        foot_r
    hip_l
      shin_l
        foot_l
```

Texture: 64x64, box UV, 38 cubes. Geometry identifier `geometry.doom_sovereign.doombot_standard`.
