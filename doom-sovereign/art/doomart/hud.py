"""HUD sprites and the HUD layout (one source for the sprites, the mock-ups and docs/HUD.md).

Design rules: restrained (no full-screen overlays, nothing in the centre except vanilla's
crosshair and the target bracket), readable at every GUI scale (sprites are authored at 1x GUI
pixels and only ever scaled by whole numbers), and accessible: every warning has its own shape
and a 2 Hz blink for critical states, so nothing depends on colour alone.
"""
import math

import numpy as np

from .pixel import Canvas
from .palette import COLORS

BAR_W = 82


def bar(h, fill=None, pattern=None, ticks=True):
    c = Canvas(BAR_W, h)
    if fill is None:
        c.rect(0, 0, BAR_W - 1, h - 1, "steel_recess")
        c.rect(1, 1, BAR_W - 2, h - 2, "glass_dark")
        c.hline(0, BAR_W - 1, 0, "steel")
        if ticks:
            for k in range(1, 5):
                c.px(1 + k * (BAR_W - 2) // 5, h - 2, "steel_mid")
        return c
    for y in range(1, h - 1):
        for x in range(1, BAR_W - 1):
            c.px(x, y, pattern(x, y) if pattern else fill)
    return c


def sprites():
    s = {}
    s["energy_bar_background"] = bar(5)
    s["energy_bar_fill"] = bar(5, "arcane", lambda x, y: "arcane" if y == 1 else "arcane_dim")
    s["energy_bar_fill_low"] = bar(5, "brass", lambda x, y: "brass_hi" if y == 1 else ("brass" if (x // 3) % 2 else "brass_lo"))
    s["energy_bar_reserve"] = bar(5, "brass_lo", lambda x, y: "brass_lo" if x <= 8 else None)
    s["focus_bar_background"] = bar(5)
    s["focus_bar_fill"] = bar(5, "arcane_core", lambda x, y: "arcane_core" if (x % 6 == 3 and y == 2) else ("arcane" if y != 2 else "green_hi"))
    s["shield_bar_background"] = bar(3, ticks=False)
    s["shield_bar_fill"] = bar(3, "steel_hi", lambda x, y: None if x % 8 == 0 else "steel_hi")
    s["heat_bar_background"] = bar(3, ticks=False)
    hb = s["heat_bar_background"]
    hb.px(int(BAR_W * 0.70), 0, "arcane_core").px(int(BAR_W * 0.70), 2, "arcane_core")     # throttle threshold marker
    hb.px(int(BAR_W * 0.50), 0, "steel_hi")                                                  # warning threshold
    s["heat_bar_fill"] = bar(3, "brass", lambda x, y: "brass" if x < BAR_W * 0.7 else "brass_hi")
    s["heat_bar_fill_locked"] = bar(3, "brass_hi", lambda x, y: "brass_hi" if (x + y) % 3 else "steel_recess")
    # 7x7 bar labels
    e = Canvas(7, 7)
    for (x, y) in ((4, 0), (3, 1), (2, 2), (3, 2), (4, 2), (5, 2), (3, 3), (2, 4), (1, 5), (1, 6)):
        e.px(x, y, "arcane")
    s["icon_energy"] = e
    f = Canvas(7, 7)
    f.ring(3, 3, 2.6, "arcane").px(3, 3, "arcane_core").px(3, 0, "arcane_core").px(3, 6, "arcane_core")
    s["icon_focus"] = f
    sh = Canvas(7, 7)
    for (x, y) in ((2, 0), (3, 0), (4, 0), (1, 1), (5, 1), (0, 2), (6, 2), (0, 3), (6, 3), (1, 4), (5, 4), (2, 5), (4, 5), (3, 6)):
        sh.px(x, y, "steel_hi")
    s["icon_shield"] = sh
    ht = Canvas(7, 7)
    for (x, y) in ((3, 0), (2, 1), (4, 2), (3, 3), (1, 3), (5, 4), (2, 5), (4, 5), (3, 6), (1, 6), (5, 6)):
        ht.px(x, y, "brass_hi")
    s["icon_heat"] = ht
    # ability slots
    slot = Canvas(20, 20)
    slot.rect(0, 0, 19, 19, "steel_recess").rect(1, 1, 18, 18, "glass_dark")
    slot.hline(0, 19, 0, "steel").vline(0, 0, 19, "steel")
    s["ability_slot"] = slot
    sel = Canvas(20, 20)
    sel.frame(0, 0, 19, 19, "brass").hline(0, 19, 0, "brass_hi").vline(0, 0, 19, "brass_hi")
    s["ability_slot_selected"] = sel
    s.update(ability_icons())
    # 9x9 warnings: distinct silhouettes
    s.update(warnings())
    tb = Canvas(5, 5)
    tb.hline(0, 4, 0, "steel_hi").vline(0, 0, 4, "steel_hi")
    s["target_bracket"] = tb
    tl = Canvas(5, 5)
    tl.hline(0, 4, 0, "arcane").vline(0, 0, 4, "arcane").px(1, 1, "arcane_core")
    s["target_bracket_locked"] = tl
    p = Canvas(24, 24)
    p.rect(0, 0, 23, 23, "glass_dark").frame(0, 0, 23, 23, "steel_recess").frame(1, 1, 22, 22, "steel")
    p.hline(1, 22, 1, "steel_mid")
    for (x, y) in ((1, 1), (22, 1), (1, 22), (22, 22)):
        p.px(x, y, "brass")
    s["scan_panel"] = p
    kb = Canvas(60, 3)
    kb.rect(0, 0, 59, 2, "steel_recess").hline(1, 58, 1, "arcane_dim")
    s["knowledge_bar"] = kb
    return s


NINE_SLICE = {"scan_panel": (24, 24, 4)}


def ability_icons():
    out = {}

    def new():
        return Canvas(16, 16)

    c = new()   # bolt
    c.line(3, 12, 12, 3, "arcane").line(4, 12, 13, 3, "arcane_dim").px(12, 3, "arcane_core").px(13, 2, "arcane_core")
    out["ability_bolt"] = c
    c = new()   # charged blast
    c.disc(7.5, 7.5, 5, "arcane_dim").disc(7.5, 7.5, 3.2, "arcane").disc(7.5, 7.5, 1.5, "arcane_core")
    for k in range(8):
        a = k * math.pi / 4
        c.px(int(7.5 + 7 * math.cos(a)), int(7.5 + 7 * math.sin(a)), "arcane")
    out["ability_charged_blast"] = c
    c = new()   # beam
    c.rect(1, 6, 14, 9, "arcane_dim").rect(1, 7, 14, 8, "arcane").hline(1, 14, 7, "arcane_core")
    c.rect(0, 5, 1, 10, "steel_hi")
    out["ability_beam"] = c
    c = new()   # force field
    for (x, y) in ((7, 1), (8, 1), (3, 3), (12, 3), (1, 7), (14, 7), (1, 8), (14, 8), (3, 12), (12, 12), (7, 14), (8, 14)):
        c.px(x, y, "steel_hi")
    c.ring(7.5, 7.5, 6.4, "steel_hi").ring(7.5, 7.5, 5.2, "steel_mid")
    c.disc(7.5, 7.5, 1.5, "arcane")
    out["ability_force_field"] = c
    c = new()   # scan
    c.ring(7.5, 7.5, 6.5, "arcane_dim").ring(7.5, 7.5, 4, "arcane_dim").px(7, 7, "arcane_core").px(8, 8, "arcane_core")
    c.line(8, 7, 13, 2, "arcane")
    out["ability_scan"] = c
    c = new()   # pulse
    c.ring(7.5, 7.5, 6.8, "steel_hi").ring(7.5, 7.5, 4.3, "steel_mid").disc(7.5, 7.5, 2.0, "arcane")
    out["ability_pulse"] = c
    c = new()   # flight
    c.rect(6, 2, 9, 9, "steel_mid").hline(6, 9, 2, "steel_hi")
    c.rect(5, 10, 10, 11, "steel")
    c.rect(6, 12, 9, 13, "arcane").hline(7, 8, 14, "arcane_dim").hline(6, 9, 12, "arcane_core")
    out["ability_flight"] = c
    c = new()   # boost
    for x0 in (2, 7):
        c.line(x0, 3, x0 + 5, 8, "arcane").line(x0 + 5, 8, x0, 13, "arcane")
    c.px(12, 8, "arcane_core")
    out["ability_boost"] = c
    c = new()   # spell (sigil)
    c.ring(7.5, 7.5, 6, "arcane_dim")
    for (a, b) in (((7, 2), (12, 11)), ((12, 11), (3, 11)), ((3, 11), (7, 2))):
        c.line(a[0], a[1], b[0], b[1], "arcane")
    c.px(7, 7, "arcane_core")
    out["ability_spell"] = c
    c = new()   # ritual
    c.ring(7.5, 9, 5.5, "arcane_dim")
    for x in (3, 7, 12):
        c.vline(x, 3, 6, "arcane").px(x, 2, "arcane_core")
    out["ability_ritual"] = c
    c = new()   # teleport
    c.ring(7.5, 7.5, 6, "arcane_dim").ring(7.5, 7.5, 3, "arcane").px(7, 7, "arcane_core").px(8, 8, "arcane_core")
    for (x, y) in ((1, 1), (14, 1), (1, 14), (14, 14)):
        c.px(x, y, "arcane")
    out["ability_teleport"] = c
    c = new()   # doombot command
    c.rect(5, 2, 10, 7, "steel_mid").hline(5, 10, 2, "steel_hi").px(6, 4, "arcane").px(9, 4, "arcane")
    c.rect(4, 9, 11, 13, "steel").hline(4, 11, 9, "steel_hi")
    c.line(12, 8, 15, 5, "brass")
    out["ability_command"] = c
    return out


def warnings():
    out = {}

    def tri():
        c = Canvas(9, 9)
        for y in range(9):
            half = y // 2
            c.px(4 - half, y, "brass").px(4 + half, y, "brass")
        c.hline(0, 8, 8, "brass")
        return c

    c = tri()                                              # low energy: triangle with a bolt
    c.px(4, 3, "arcane").px(3, 5, "arcane").px(4, 4, "arcane").px(5, 5, "arcane").px(4, 6, "arcane")
    out["warn_low_energy"] = c
    c = Canvas(9, 9)                                       # overheat: square with a flame
    c.frame(0, 0, 8, 8, "brass")
    for (x, y) in ((4, 2), (3, 3), (5, 4), (4, 5), (3, 6), (5, 6)):
        c.px(x, y, "brass_hi")
    out["warn_overheat"] = c
    c = Canvas(9, 9)                                       # shield down: broken hexagon
    for (x, y) in ((3, 0), (5, 0), (1, 1), (7, 1), (0, 3), (8, 3), (0, 5), (8, 5), (1, 7), (7, 7), (3, 8), (5, 8)):
        c.px(x, y, "steel_hi")
    c.line(2, 6, 6, 2, "brass_hi")
    out["warn_shield_down"] = c
    c = Canvas(9, 9)                                       # low focus: circle with a gap
    c.ring(4, 4, 3.6, "arcane_dim").px(4, 0, None).px(4, 8, None).px(4, 4, "arcane_core")
    out["warn_low_focus"] = c
    c = Canvas(9, 9)                                       # armour damaged: cracked plate
    c.rect(1, 1, 7, 7, "steel").frame(1, 1, 7, 7, "steel_hi").line(2, 2, 6, 6, "steel_recess").px(5, 3, "steel_recess")
    out["warn_armor_damaged"] = c
    c = Canvas(9, 9)                                       # lock-on: four inward ticks around a dot
    for (x, y) in ((4, 0), (4, 1), (4, 7), (4, 8), (0, 4), (1, 4), (7, 4), (8, 4)):
        c.px(x, y, "brass_hi")
    c.px(4, 4, "brass")
    out["warn_lock_on"] = c
    return out


def cooldown_frames(n=16, alpha=170):
    """Radial wipe: frame k covers the remaining (n - k) / n of the slot, clockwise from 12 o'clock."""
    frames = []
    r, g, b = COLORS["glass_dark"]
    for k in range(n):
        remaining = 1 - k / n
        a = np.zeros((16, 16, 4), np.uint8)
        for y in range(16):
            for x in range(16):
                ang = (math.atan2(x - 7.5, -(y - 7.5)) / (2 * math.pi)) % 1.0
                if ang >= 1 - remaining:
                    a[y, x] = (r, g, b, alpha)
        frames.append(a)
    return frames


# ---- layout --------------------------------------------------------------------------------------
HOTBAR_W = 182
MIN_SIDE_W = 2 * 97 + HOTBAR_W        # cluster (6 + 91) on each side of the hotbar


def layout(gw, gh):
    """Element rectangles in GUI pixels for a GUI of gw x gh. Mirrors docs/HUD.md."""
    items = {}
    compact = gw < MIN_SIDE_W
    x0 = 6
    base = gh - 6 if not compact else gh - 22 - 42            # compact: lift above the vanilla status rows
    rows = [("energy", 5, "energy_bar"), ("heat", 3, "heat_bar"), ("shield", 3, "shield_bar"), ("focus", 5, "focus_bar")]
    y = base
    for name, h, sprite in rows:
        y -= h
        items[name] = (x0 + 9, y, BAR_W, h, sprite)
        items[name + "_icon"] = (x0, y + h // 2 - 3, 7, 7, "icon_" + {"energy": "energy", "heat": "heat", "shield": "shield", "focus": "focus"}[name])
        y -= 2
    items["warnings"] = (x0, y - 11, 4 * 11, 9, "warn_*")
    slots_w = 4 * 20 + 3 * 2
    if compact:
        items["abilities"] = (gw - 6 - slots_w, gh - 22 - 42 - 20, slots_w, 20, "ability_slot")
    else:
        items["abilities"] = (gw - 6 - slots_w, gh - 6 - 20, slots_w, 20, "ability_slot")
    items["scan_panel"] = (gw - 6 - 124, 6, 124, 58, "scan_panel")
    items["hotbar (vanilla)"] = ((gw - HOTBAR_W) // 2, gh - 22, HOTBAR_W, 22, None)
    items["compact"] = compact
    return items
