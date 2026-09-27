#!/usr/bin/env python3
"""Writes assets/doom_sovereign/lang/en_us.json from the names used by the other builders."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from build_armor import ASSETS
from build_ui import ITEM_NAMES, BLOCK_NAMES

HUD = {
    "hud.doom_sovereign.energy": "Doom Energy", "hud.doom_sovereign.focus": "Arcane Focus",
    "hud.doom_sovereign.shield": "Force Field", "hud.doom_sovereign.heat": "Gauntlet Heat",
    "hud.doom_sovereign.scan.knowledge": "Knowledge %s%%", "hud.doom_sovereign.scan.countermeasure": "Countermeasure: %s",
    "hud.doom_sovereign.warn.low_energy": "Energy low", "hud.doom_sovereign.warn.overheat": "Gauntlets overheated",
    "hud.doom_sovereign.warn.shield_down": "Force field down", "hud.doom_sovereign.warn.low_focus": "Focus low",
    "hud.doom_sovereign.warn.armor_damaged": "Armor damaged", "hud.doom_sovereign.warn.lock_on": "Targeted",
    "key.doom_sovereign.flight": "Toggle Flight", "key.doom_sovereign.ability_next": "Next Ability",
    "key.doom_sovereign.ability_use": "Use Ability", "key.doom_sovereign.scan": "Doom Analysis Scan",
    "key.doom_sovereign.field": "Raise Force Field", "key.doom_sovereign.command": "Command Doombots",
    "key.categories.doom_sovereign": "DOOM: SOVEREIGN",
    "entity.doom_sovereign.doombot_standard": "Standard Doombot",
    "itemGroup.doom_sovereign": "DOOM: SOVEREIGN",
}


def build():
    lang = {}
    for k, v in ITEM_NAMES.items():
        lang["item.doom_sovereign." + k] = v
    for k, v in BLOCK_NAMES.items():
        lang["block.doom_sovereign." + k] = v
    with open(os.path.join(HERE, "subtitles_en_us.json")) as f:
        lang.update(json.load(f))
    lang.update(HUD)
    d = os.path.join(ASSETS, "lang")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "en_us.json"), "w") as f:
        json.dump(dict(sorted(lang.items())), f, indent=2)
        f.write("\n")
    print("lang: %d strings" % len(lang))


if __name__ == "__main__":
    build()
