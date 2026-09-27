# HUD specification

Status: **sprites created, layout specified and mocked up; not drawn by the game.** Sprites are in
`assets/doom_sovereign/textures/gui/sprites/hud/` (sprite ids `doom_sovereign:hud/<name>`), authored at 1x GUI
pixels; the game scales them by the integer GUI scale. Mock-ups: `art/previews/hud_mockup_*.png`.

Principles: restrained (nothing over the centre of the screen except the target bracket), anchored to the
corners, readable at every GUI scale, and never colour-only: warnings differ in shape and critical ones blink
at 2 Hz; bars have tick marks every 20 %; the heat bar marks the throttle (70 %) and warning (50 %) points.

## Anchoring (GUI pixels)

| Element | Anchor | Rectangle at 480x270 (1920x1080, scale 4) | at 426x240 (1280x720, scale 3) | at 320x240 (640x480, scale 2) |
|---|---|---|---|---|
| focus | bottom-left | x 15, y 242, 82x5 | x 15, y 212, 82x5 | x 15, y 154, 82x5 |
| shield | bottom-left | x 15, y 249, 82x3 | x 15, y 219, 82x3 | x 15, y 161, 82x3 |
| heat | bottom-left | x 15, y 254, 82x3 | x 15, y 224, 82x3 | x 15, y 166, 82x3 |
| energy | bottom-left | x 15, y 259, 82x5 | x 15, y 229, 82x5 | x 15, y 171, 82x5 |
| warnings | bottom-left | x 6, y 229, 44x9 | x 6, y 199, 44x9 | x 6, y 141, 44x9 |
| abilities | bottom-right | x 388, y 244, 86x20 | x 334, y 214, 86x20 | x 228, y 156, 86x20 |
| scan_panel | top-right | x 350, y 6, 124x58 | x 296, y 6, 124x58 | x 190, y 6, 124x58 |
| hotbar (vanilla) | bottom-centre | x 149, y 248, 182x22 | x 122, y 218, 182x22 | x 69, y 218, 182x22 |

Compact rule: when the GUI is narrower than 376 px (the status cluster would touch the hotbar), the cluster
and the ability bar move up above the vanilla health/food rows (see the 640x480 mock-up).

## Elements

- **Energy** (82x5): fill = stored / capacity; the leftmost 10 % shows the reserve band (`energy_bar_reserve`);
  at `LOW` status the fill switches to `energy_bar_fill_low` (brass, striped) and blinks at `RESERVE`.
- **Heat** (82x3): brass fill, brighter past the throttle marker; `heat_bar_fill_locked` (hatched) while locked out.
- **Force field** (82x3): segmented steel fill = field charge / capacity; hidden while the field is OFF.
- **Arcane focus** (82x5): pale fill with sigil dots (sorcery look); reserved focus for a channel shows as the
  unfilled part blinking slowly.
- **Warnings** (9x9, up to 4, left to right by severity): low energy (triangle + bolt), overheat (square + flame),
  shield down (broken hexagon), low focus (open ring), armour damaged (cracked plate), lock-on (four ticks).
- **Abilities**: 4 slots (20x20), selected slot framed in brass; icon 16x16; cooldown = `cooldown_00..15` radial
  wipe (frame = floor(progress x 16)); a charge counter digit draws bottom-right when an ability has charges.
- **Scan result**: nine-slice panel (`scan_panel`, border 4) 124 px wide; lines: subject name, knowledge % +
  `knowledge_bar`, up to 4 revealed traits, newly unlocked countermeasure; fades 6 s after the last scan.
- **Target bracket**: four `target_bracket` corners (mirrored at draw time) around the projected bounding box
  of the current target; `target_bracket_locked` when a charged shot or bot order is locked on.
- Vanilla hotbar, health, food and crosshair are untouched.
