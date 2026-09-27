# Doom mask hero asset

Stand-alone mask for item display, the Armor Cradle and the equip cut-in; the lock sequence moves brow, cheeks, jaw and eye glow.

Coordinates: Bedrock geometry space, 1 unit = 1 model pixel (16 per block), +y up, the model's front faces -z,
the model's right side is -x. Pivots are absolute. Rotations are degrees; limits below are the ranges the
animation validator enforces for rest rotation + animated rotation. Sign conventions (from the transform
emulation in `art/doomart/render.py`, awaiting in-game confirmation): limb x negative = swing forward, right
limb z positive = outward, elbow x negative = flex, knee x positive = flex, head/body x positive = pitch down.

| Bone | Parent | Pivot | Rest rotation | Rotation limits (DOF) | Cubes | Purpose |
|---|---|---|---|---|---|---|
| `mask_root` | (root) | (0, 8, 0) | - | x -30..30, y -180..180, z -30..30 | 0 | Whole mask; display/turntable rotation |
| `faceplate` | `mask_root` | (0, 8, -1) | - | x -10..10, y 0..0, z 0..0 | 3 | Face plate with eye slits |
| `brow` | `faceplate` | (0, 14, -2) | - | x -25..5, y 0..0, z 0..0 | 1 | Brow ridge; drops into place |
| `cheek_r` | `faceplate` | (-8, 8, -1) | - | x 0..0, y -50..5, z 0..0 | 1 | Right cheek guard; swings in |
| `cheek_l` | `faceplate` | (8, 8, -1) | - | x 0..0, y -5..50, z 0..0 | 1 | Left cheek guard; swings in |
| `jaw` | `faceplate` | (0, 3, -2) | - | x -5..30, y 0..0, z 0..0 | 1 | Jaw and grille; rises and seals last |
| `eye_glow` | `faceplate` | (0, 10, -2.2) | - | fixed (driven only through its parent) | 2 | Eye flare planes (emissive only) |

Hierarchy:

```
mask_root
  faceplate
    brow
    cheek_r
    cheek_l
    jaw
    eye_glow
```

Texture: 64x64, box UV, 9 cubes. Geometry identifier `geometry.doom_sovereign.doom_mask`.
