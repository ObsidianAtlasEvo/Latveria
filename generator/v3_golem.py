"""Refinement v3 - Golem Works rework (the iron farm).

Faults of the v2 farm, found in the audit (docs/v3/AUDIT.md):
  1. The pads were dry: a golem could stand on them for minutes.  While a golem lives within
     16 blocks every villager keeps GOLEM_DETECTED_RECENTLY, so the farm stalls.
  2. The villager pod floor was stone: spawn attempts land INSIDE the pod on the two free cells
     (golem spawning uses no collision check), trapping golems with the villagers.
  3. The zombie was visible to the villagers through glass day and night (if glass passes line
     of sight) - panicking villagers never sleep, and without sleep the farm stops after one day.
     If glass blocks line of sight the villagers never panic at all.  Either way it fails.
  4. No way to switch it off.

The rework (all in place, no block of the old platform is moved):
  * channel troughs filled flush with stone bricks; water sources along the inner edge of the
    rim at walking level: every pad cell is flowing water that pushes golems to the 2x2 shaft
    (water reaches exactly 7 cells, stopping at the shaft edge, so the shaft stays dry);
  * pod floors -> glass (golems never spawn on glass), so every spawn attempt that lands under
    the pod drops through to the pad;
  * the villager/zombie partition (x = 255) becomes opaque stone brick with ONE window at the
    villagers' eye height (1 block high - no villager or zombie can pass it, and the zombie's
    reach cannot cross the 1-block gap);
  * a sticky piston above the window, driven by an inverted daylight detector, closes the window
    with a full block from dusk to dawn (and in rain), so the villagers calm down and sleep;
  * a lever on the piston holds the window shut: ON = farm off;
  * missing hands or the zombie are re-summoned (only if absent).
"""
from core import pos
from v3core import restore_named

CX, CZ = 252, -90          # shaft north-west cell
PX1, PX2, PZ1, PZ2 = 244, 261, -98, -81   # pad interior (inside the rim)
WIN = (255, 10, -89)       # the single window
PISTON = (255, 12, -89)
LEVER = (256, 12, -89)
DETECTOR = (255, 13, -89)


def build(v):
    v.section("golem_works", "Golem Works rework", (263, -76))
    # 1. flush pad floor (the old channels held water sources at their outer ends + flowing water)
    arms = [(252, -98, 253, -91), (252, -88, 253, -81), (244, -90, 251, -89), (254, -90, 261, -89)]
    for (x1, z1, x2, z2) in arms:
        v.swap(x1, 4, z1, x2, 4, z2, "stone_bricks", "water", expect=0)
        v.b.fill(x1, 4, z1, x2, 4, z2, "stone_bricks", mode="replace air")   # flowing water is air in the model
        v.w.apply("fill %s %s stone_bricks replace air" % (pos(x1, 4, z1), pos(x2, 4, z2)))
        v.stats["swap"] += 1
    # 2. water sources along the inner rim at walking level
    v.fill_keep(PX1, 5, PZ1, PX2, 5, PZ1, "water")
    v.fill_keep(PX1, 5, PZ2, PX2, 5, PZ2, "water")
    v.fill_keep(PX1, 5, PZ1 + 1, PX1, 5, PZ2 - 1, "water")
    v.fill_keep(PX2, 5, PZ1 + 1, PX2, 5, PZ2 - 1, "water")
    # 3. glass pod floors (villager pod x 250..254, zombie pod x 256..257)
    v.swap(250, 8, -91, 254, 8, -88, "glass", "stone_bricks")
    v.swap(256, 8, -90, 257, 8, -88, "glass", "stone_bricks")
    # 4. opaque partition with one window
    v.swap(255, 9, -90, 255, 11, -89, "stone_bricks", "glass")
    v.swap(255, 11, -90, 255, 11, -89, "stone_bricks", "tinted_glass")
    v.b.raw("fill %s %s air replace stone_bricks" % (pos(*WIN), pos(*WIN)))
    v.w.apply("fill %s %s air replace stone_bricks" % (pos(*WIN), pos(*WIN)))
    # 5. night shutter: sticky piston (replaces one roof pane), detector on top, OFF lever beside
    v.swap(*PISTON, *PISTON, "sticky_piston[facing=down,extended=false]", "tinted_glass")
    v.put(*DETECTOR, "daylight_detector[inverted=true,power=0]")
    v.put(*LEVER, "lever[face=wall,facing=east,powered=false]")
    v.mechanism("Golem Works night shutter", "requires live Minecraft test",
                "Inverted daylight detector (255,13,-89) powers the sticky piston below it; at night and in rain "
                "the piston pushes a stone-brick block into the villagers' only window onto the zombie, so they "
                "stop panicking and sleep. Lever (256,12,-89) on the piston's east face holds it shut (farm off).")
    # a plaque at the service ladder
    v.sign(263, 5, -86, "dark_oak_wall_sign[facing=east]", ["GOLEM WORKS", "Shutter lever on", "the pod roof:", "on = stopped"], "dark_green", True)
    # 6. restore the crew only if missing (never duplicates while they live)
    vd = 'VillagerData:{profession:"minecraft:none",level:1,type:"minecraft:taiga"},PersistenceRequired:1b'
    for i in range(3):
        restore_named(v, "villager", "Golem Works Hand %d" % (i + 1), 253.5, 9, -88.5, vd)
    restore_named(v, "zombie", "The Frightener", 256.5, 9, -88.5,
                  'PersistenceRequired:1b,CanPickUpLoot:0b,equipment:{head:{id:"minecraft:carved_pumpkin",count:1}}')
