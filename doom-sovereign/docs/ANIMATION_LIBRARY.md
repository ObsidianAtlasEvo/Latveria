# Animation library

Status: **authored, awaiting runtime validation.** Every clip passes `art/doomart/anim.py`'s validator
(structure, bone names, easing names, key times, loop seams, sampled joint limits, linked knee bones, sound and
particle ids) and the Java `PresentationTest`, but none has been played by GeckoLib.

Integration note: vanilla drives the armour root bones (`armorHead`, `armorBody`, limbs). Clips that move the
roots (walk, flight poses, landings) need the player model itself to take the same pose - a player-animation
hook on the Fabric side - otherwise only the child bones (elbows, knees, cloak, mask, plates) will move.
Full-body lean and roll in flight are applied by the renderer from `FlightOutput`, not by the clips.
The eye-glow bone scales only the flare planes; dimming the face-plate glow needs the glow-mask texture swap
(`_glowmask_low` / none) chosen by the renderer.

## Royal Armor (`armor/royal_armor.animation.json`)

| Clip | Length (s) | Loop | Keyframes | Sounds | Particles | Gameplay cues |
|---|---|---|---|---|---|---|
| `animation.royal_armor.idle_armored` | 4 | loop | 363 | - | - | - |
| `animation.royal_armor.idle_authoritative` | 6 | loop | 540 | - | - | - |
| `animation.royal_armor.idle_arms_behind_back` | 5 | loop | 425 | - | - | - |
| `animation.royal_armor.walk` | 1.2 | loop | 374 | armor.step_heavy@0.0, armor.servo@0.3, armor.step_heavy@0.6 | - | footstep_right@0.0, footstep_left@0.6 |
| `animation.royal_armor.sprint` | 0.72 | loop | 302 | armor.step_heavy@0.0, armor.step_heavy@0.36 | - | footstep_right@0.0, footstep_left@0.36 |
| `animation.royal_armor.crouch` | 0.35 | hold | 111 | armor.servo@0.0 | - | - |
| `animation.royal_armor.jump_anticipation` | 0.22 | hold | 92 | - | - | - |
| `animation.royal_armor.jump_launch` | 0.35 | hold | 147 | armor.servo@0.0 | - | - |
| `animation.royal_armor.falling` | 1 | loop | 347 | - | - | - |
| `animation.royal_armor.hover` | 3 | loop | 472 | flight.loop@0.0 | repulsor_idle@0.0 | - |
| `animation.royal_armor.takeoff` | 0.45 | hold | 155 | flight.thruster_ignition@0.12 | repulsor_burst@0.15, repulsor_burst@0.16 | liftoff@0.15 |
| `animation.royal_armor.vertical_ascent` | 1 | loop | 172 | - | repulsor_trail@0.0 | - |
| `animation.royal_armor.forward_flight` | 2 | loop | 623 | - | repulsor_trail@0.0 | - |
| `animation.royal_armor.strafe_left` | 1 | loop | 266 | - | - | - |
| `animation.royal_armor.strafe_right` | 1 | loop | 266 | - | - | - |
| `animation.royal_armor.boosted_flight` | 0.5 | loop | 291 | flight.boost@0.0 | repulsor_trail_boost@0.0 | - |
| `animation.royal_armor.braking` | 0.6 | hold | 208 | flight.thruster_ignition@0.05 | - | brake_thrust@0.25 |
| `animation.royal_armor.controlled_descent` | 2 | loop | 399 | - | - | - |
| `animation.royal_armor.hard_landing` | 1.2 | once | 297 | armor.impact_heavy@0.0 | landing_shockwave@0.02 | landing_impact@0.02 |
| `animation.royal_armor.gauntlet_aim` | 2 | loop | 233 | - | - | - |
| `animation.royal_armor.energy_blast_left` | 0.6 | once | 182 | gauntlet.discharge@0.16 | gauntlet_muzzle@0.16 | fire_left@0.16 |
| `animation.royal_armor.energy_blast_right` | 0.6 | once | 182 | gauntlet.discharge@0.16 | gauntlet_muzzle@0.16 | fire_right@0.16 |
| `animation.royal_armor.charged_blast` | 1.8 | once | 438 | gauntlet.charge@0.25, gauntlet.heavy_blast@1.3 | gauntlet_charge@0.3, gauntlet_heavy_muzzle@1.3 | fire_charged@1.3 |
| `animation.royal_armor.sustained_beam` | 1 | loop | 211 | gauntlet.beam_loop@0.0 | - | - |
| `animation.royal_armor.force_field_activation` | 0.8 | once | 293 | field.activate@0.36 | field_raise@0.4 | field_up@0.4 |
| `animation.royal_armor.shield_impact_reaction` | 0.5 | once | 149 | - | - | shield_hit@0.0 |
| `animation.royal_armor.scan` | 2 | loop | 275 | scan.pulse@0.0, scan.pulse@1.0 | scan_sweep@0.0 | - |
| `animation.royal_armor.tech_override` | 1.6 | once | 292 | scan.pulse@0.35, tech.override@0.95 | - | override_complete@1.2 |
| `animation.royal_armor.spell_cast` | 1 | once | 320 | sorcery.arcane_cast@0.15 | arcane_sigil@0.3 | cast@0.65 |
| `animation.royal_armor.ritual_channel` | 3 | loop | 707 | sorcery.ritual_resonance@0.0 | ritual_motes@0.0 | - |
| `animation.royal_armor.teleport_cast` | 0.9 | once | 363 | sorcery.teleport@0.3 | teleport_flash@0.62 | teleport@0.62 |
| `animation.royal_armor.doombot_command` | 1.2 | once | 239 | - | - | command_issued@0.5 |
| `animation.royal_armor.light_melee` | 0.5 | once | 164 | armor.servo@0.14 | - | hit@0.18 |
| `animation.royal_armor.heavy_punch` | 0.9 | once | 213 | armor.impact_heavy@0.43 | - | hit_heavy@0.45 |
| `animation.royal_armor.backhand` | 0.7 | once | 171 | - | - | hit@0.28 |
| `animation.royal_armor.ground_slam` | 1.4 | once | 473 | armor.impact_heavy@0.6 | landing_shockwave@0.6 | slam@0.6 |
| `animation.royal_armor.armor_initialization` | 2.5 | once | 368 | armor.servo@0.3, armor.servo@0.8, armor.servo@1.3 | - | hud_online@2.0 |
| `animation.royal_armor.mask_seal` | 1.4 | once | 137 | mask.lock@0.3, mask.lock@0.53, mask.seal@0.8 | - | sealed@0.82, eyes_lit@1.0 |
| `animation.royal_armor.shutdown_low_power` | 1.5 | hold | 180 | armor.shutdown@0.0 | - | power_low@0.6 |

## Standard Doombot (`entity/doombot.animation.json`)

| Clip | Length (s) | Loop | Keyframes | Sounds | Particles | Gameplay cues |
|---|---|---|---|---|---|---|
| `animation.doombot.idle` | 3 | loop | 113 | doombot.servo@1.0 | - | - |
| `animation.doombot.scan_idle` | 4 | loop | 132 | doombot.servo@0.0, scan.pulse@0.4, scan.pulse@2.8 | - | - |
| `animation.doombot.walk` | 1 | loop | 102 | doombot.step_heavy@0.0, doombot.step_heavy@0.5 | - | footstep@0.0, footstep@0.5 |
| `animation.doombot.run` | 0.6 | loop | 94 | doombot.step_heavy@0.0, doombot.step_heavy@0.3 | - | - |
| `animation.doombot.turn_look` | 1.2 | once | 63 | doombot.servo@0.1 | - | - |
| `animation.doombot.melee_strike` | 0.8 | once | 66 | armor.impact_heavy@0.36 | - | hit@0.38 |
| `animation.doombot.ranged_aim` | 1 | loop | 73 | - | - | - |
| `animation.doombot.ranged_charge` | 1 | hold | 56 | gauntlet.charge@0.0 | gauntlet_charge@0.1 | - |
| `animation.doombot.ranged_fire` | 0.5 | once | 67 | gauntlet.discharge@0.02 | gauntlet_muzzle@0.02 | fire@0.02 |
| `animation.doombot.stagger` | 0.7 | once | 64 | doombot.servo@0.0 | sparks@0.02 | - |
| `animation.doombot.shield_brace` | 0.35 | hold | 42 | - | - | - |
| `animation.doombot.low_health_malfunction` | 2 | loop | 103 | doombot.diagnostic@0.3, doombot.servo@1.2 | sparks@0.32, sparks@0.92 | - |
| `animation.doombot.repair` | 3 | loop | 142 | doombot.diagnostic@0.2 | repair_weld@0.75, repair_weld@2.25 | - |
| `animation.doombot.shutdown` | 1.5 | hold | 67 | doombot.shutdown@0.1 | - | - |
| `animation.doombot.death_collapse` | 1.8 | hold | 88 | doombot.shutdown@0.0, armor.impact_heavy@1.15 | sparks@0.05, landing_shockwave@1.15 | hit_ground@1.15 |
| `animation.doombot.command_acknowledgement` | 0.8 | once | 59 | doombot.diagnostic@0.28 | - | acknowledged@0.3 |

## Doom mask (hero asset) (`item/doom_mask.animation.json`)

| Clip | Length (s) | Loop | Keyframes | Sounds | Particles | Gameplay cues |
|---|---|---|---|---|---|---|
| `animation.doom_mask.lock` | 1.4 | hold | 23 | mask.lock@0.3, mask.lock@0.53, mask.seal@0.8 | - | sealed@0.82, eyes_lit@1.0 |
| `animation.doom_mask.display_idle` | 8 | loop | 8 | - | - | - |
| `animation.doom_mask.power_down` | 1.2 | hold | 7 | armor.shutdown@0.0 | - | - |

Descriptions and authoring notes live next to each clip in `art/doomart/anim_armor.py`,
`anim_doombot.py` and `anim_mask.py`. Contact sheets: `art/previews/anim/`.
