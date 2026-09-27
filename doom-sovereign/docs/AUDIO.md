# Audio

Status: **created and measured; not heard in game.** Every sound is synthesized by `art/build_audio.py` from
oscillators, filtered noise and envelopes (`art/doomart/synth.py`). No samples, recordings, voices, ripped or
third-party audio, and no imitation of any actor or existing game/film sound. Mono 44.1 kHz OGG Vorbis
(mono so Minecraft can position it).

Two families: **technology** (filtered noise, FM metal, gliding servo whines, hard transients, mains-like
hum) and **sorcery** (just-intonation sine stacks, inharmonic bells, reversed swells, long airy tails).
Spectrograms: `art/previews/audio_spectrograms.png`.

Loudness rules: peak <= -1 dBFS after encoding (2 dB pre-encode headroom); RMS targets -14 (impacts),
-16 (one-shots), -19 (UI), -22 (loops) dBFS; transient sounds sit below their target because the peak limit
wins. Loops are cross-faded and rotated to a quiet seam; `seam` is the seam step divided by the loop's
99th-percentile sample step (< 1 means inaudible).

| Event | File | Family | Kind | Length (s) | Peak dBFS | RMS dBFS | Seam | Design |
|---|---|---|---|---|---|---|---|---|
| `doom_sovereign:mask.lock` | `sounds/mask/lock.ogg` | tech | one_shot | 0.35 | -1.91 | -18.69 | - | Twin latch clicks, a short metallic ping and a low thunk |
| `doom_sovereign:mask.seal` | `sounds/mask/seal.ogg` | tech | one_shot | 0.95 | -2.30 | -17.79 | - | Pneumatic hiss, a deep clamp, then a rising power-on tone |
| `doom_sovereign:armor.servo` | `sounds/armor/servo.ogg` | tech | ui | 0.40 | -8.80 | -18.98 | - | Pitch-gliding saw whine with a gear-buzz tremolo and a closing tick |
| `doom_sovereign:armor.step_heavy` | `sounds/armor/step_heavy_1.ogg` | tech | impact | 0.45 | -2.09 | -18.80 | - | Low pitched thud, a padded thump and a short plate clank |
| `doom_sovereign:armor.step_heavy` | `sounds/armor/step_heavy_2.ogg` | tech | impact | 0.45 | -2.06 | -17.45 | - | Low pitched thud, a padded thump and a short plate clank |
| `doom_sovereign:armor.step_heavy` | `sounds/armor/step_heavy_3.ogg` | tech | impact | 0.45 | -2.29 | -18.24 | - | Low pitched thud, a padded thump and a short plate clank |
| `doom_sovereign:armor.impact_heavy` | `sounds/armor/impact_heavy.ogg` | tech | impact | 1.00 | -2.00 | -16.75 | - | Sub boom, a low noise blast, a ringing metal body and debris ticks |
| `doom_sovereign:armor.shutdown` | `sounds/armor/shutdown.ogg` | tech | one_shot | 1.60 | -8.52 | -15.97 | - | Descending whine with a closing filter, a stutter and a final relay click |
| `doom_sovereign:flight.thruster_ignition` | `sounds/flight/thruster_ignition.ogg` | tech | one_shot | 1.20 | -1.06 | -18.08 | - | Igniter clicks, a filtered whoomp that opens up, and a settling roar |
| `doom_sovereign:flight.loop` | `sounds/flight/loop.ogg` | tech | loop | 3.00 | -10.39 | -22.10 | 0.045 | Seamless roar: filtered noise bands, a 48 Hz rumble breathing at 3 Hz, a faint repulsor whine |
| `doom_sovereign:flight.boost` | `sounds/flight/boost.ogg` | tech | one_shot | 1.40 | -2.15 | -16.34 | - | A sharp crack, then a roar whose filter and whine climb |
| `doom_sovereign:gauntlet.charge` | `sounds/gauntlet/charge.ogg` | tech | one_shot | 1.50 | -5.29 | -16.15 | - | Rising FM whine, accelerating capacitor chirps and thickening crackle |
| `doom_sovereign:gauntlet.discharge` | `sounds/gauntlet/discharge.ogg` | tech | impact | 0.60 | -1.65 | -22.68 | - | Downward FM zap, a bright noise snap and a low punch |
| `doom_sovereign:gauntlet.heavy_blast` | `sounds/gauntlet/heavy_blast.ogg` | tech | impact | 1.60 | -1.70 | -20.42 | - | A sucking pre-swell, a crack, a falling FM roar, a sub drop and a tail |
| `doom_sovereign:gauntlet.beam_loop` | `sounds/gauntlet/beam_loop.ogg` | tech | loop | 2.00 | -5.47 | -22.04 | 0.056 | Beating saw drone with a wobbling FM layer and fine crackle, seamless |
| `doom_sovereign:field.activate` | `sounds/field/activate.ogg` | tech | one_shot | 1.00 | -1.59 | -16.88 | - | An upward shimmer sweep and whoosh, locking into a fifth |
| `doom_sovereign:field.hum` | `sounds/field/hum.ogg` | tech | loop | 3.00 | -13.79 | -21.99 | 0.079 | 100/200/300 Hz harmonic hum with slow beating and a faint high flutter, seamless |
| `doom_sovereign:field.impact` | `sounds/field/impact.ogg` | tech | impact | 0.50 | -2.35 | -16.44 | - | A dull falling 'bwomm' with FM ripple, a padded thump and a brief ring |
| `doom_sovereign:field.collapse` | `sounds/field/collapse.ogg` | tech | impact | 1.30 | -3.22 | -23.94 | - | A bright shatter, a stuttering FM fall, glassy crackle and a low drop |
| `doom_sovereign:scan.pulse` | `sounds/scan/pulse.ogg` | tech | ui | 0.80 | -1.66 | -22.90 | - | A chirp under a 1320 Hz blip with two filtered echoes |
| `doom_sovereign:tech.override` | `sounds/tech/override.ogg` | tech | ui | 1.00 | -7.57 | -19.03 | - | Rapid data-chatter blips from a fixed pitch set, then a rising two-tone confirm |
| `doom_sovereign:doombot.servo` | `sounds/doombot/servo.ogg` | tech | ui | 0.35 | -8.51 | -19.02 | - | Lower, heavier servo than the armor, with a 90 Hz gear buzz and a hydraulic puff |
| `doom_sovereign:doombot.step_heavy` | `sounds/doombot/step_heavy_1.ogg` | tech | impact | 0.50 | -2.04 | -17.58 | - | Deeper thud than the armor, a brighter clank and a hydraulic hiss tail |
| `doom_sovereign:doombot.step_heavy` | `sounds/doombot/step_heavy_2.ogg` | tech | impact | 0.50 | -2.19 | -17.45 | - | Deeper thud than the armor, a brighter clank and a hydraulic hiss tail |
| `doom_sovereign:doombot.step_heavy` | `sounds/doombot/step_heavy_3.ogg` | tech | impact | 0.50 | -2.04 | -17.77 | - | Deeper thud than the armor, a brighter clank and a hydraulic hiss tail |
| `doom_sovereign:doombot.diagnostic` | `sounds/doombot/diagnostic.ogg` | tech | ui | 0.90 | -4.42 | -19.03 | - | Three ring-modulated FM beeps: the acknowledge pattern |
| `doom_sovereign:doombot.shutdown` | `sounds/doombot/shutdown.ogg` | tech | one_shot | 1.40 | -5.91 | -16.00 | - | Power-down whine from 600 to 40 Hz, relay clunks and a dying reactor hum |
| `doom_sovereign:time_platform.charge` | `sounds/time_platform/charge.ogg` | tech | one_shot | 3.00 | -3.42 | -16.01 | - | A deep drone opening upward, accelerating pulses and a rising shimmer with phasing |
| `doom_sovereign:time_platform.discharge` | `sounds/time_platform/discharge.ogg` | tech | impact | 2.00 | -2.69 | -21.76 | - | A crack and sub drop, followed by the charge heard backwards: time folding |
| `doom_sovereign:sorcery.arcane_cast` | `sounds/sorcery/arcane_cast.ogg` | sorcery | one_shot | 1.40 | -2.16 | -18.31 | - | A reversed bell swell into a just-intonation chime cluster over an airy breath |
| `doom_sovereign:sorcery.ritual_resonance` | `sounds/sorcery/ritual_resonance.ogg` | sorcery | loop | 4.00 | -9.25 | -21.98 | 0.16 | Slow-beating just-intonation drone on 110 Hz with swelling partials and two bell strikes, seamless |
| `doom_sovereign:sorcery.teleport` | `sounds/sorcery/teleport.ogg` | sorcery | one_shot | 1.30 | -2.25 | -18.09 | - | An inward airy rush, a rising pop, then a descending bell arpeggio in a long tail |

In-game categories (set in code when played): armour, flight and weapons -> `players`; Doombots -> `hostile`
when hostile to the listener else `neutral`; machines and Time Platform -> `blocks`; sorcery -> `players`.
