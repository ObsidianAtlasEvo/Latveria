"""16 x 16 item icons, drawn pixel by pixel from the palette. Vanilla conventions: a one-pixel
dark outline, light from the top-left, a single strong silhouette per item."""
from .pixel import Canvas

ICONS = {}


def icon(name):
    def deco(fn):
        ICONS[name] = fn
        return fn
    return deco


@icon("doom_mask")
def _():
    c = Canvas(16, 16)
    c.rect(3, 2, 12, 12, "steel_mid")
    c.rect(4, 13, 11, 13, "steel_mid")
    c.hline(3, 12, 2, "steel_hi")
    c.hline(3, 12, 3, "steel_hi")
    c.px(3, 3, "brass").px(12, 3, "brass")
    for x in (4, 5, 6, 9, 10, 11):
        c.px(x, 6, "glass_dark")
    c.px(6, 6, "arcane").px(9, 6, "arcane").px(5, 6, "arcane_dim").px(10, 6, "arcane_dim")
    c.px(4, 6, "glass_dark").px(11, 6, "glass_dark")
    for x in (4, 5, 6, 9, 10, 11):
        c.px(x, 7, "steel")
    c.vline(7, 5, 10, "steel_hi").vline(8, 5, 10, "steel")
    c.px(3, 8, "steel_hi").px(12, 8, "steel_hi")
    c.px(5, 9, "steel_recess").px(4, 10, "steel_recess").px(10, 9, "steel_recess").px(11, 10, "steel_recess")
    for x in (5, 7, 8, 10):
        c.px(x, 12, "steel_recess").px(x, 13, "steel_recess")
    c.hline(4, 11, 11, "steel_hi")
    c.vline(12, 4, 12, "steel")
    return c.outline()


@icon("royal_chestplate")
def _():
    c = Canvas(16, 16)
    c.rect(1, 2, 4, 5, "steel")            # pauldrons
    c.rect(11, 2, 14, 5, "steel")
    c.hline(1, 4, 2, "steel_hi").hline(11, 14, 2, "steel_hi")
    c.hline(1, 4, 5, "brass").hline(11, 14, 5, "brass")
    c.rect(4, 2, 11, 13, "green_dark")      # tunic
    for x in (5, 6, 9, 10):
        c.vline(x, 4, 13, "green")
    c.vline(7, 4, 13, "cloth_shadow")
    c.rect(5, 2, 10, 3, "steel_mid")        # gorget
    c.hline(5, 10, 2, "steel_hi")
    c.rect(4, 10, 11, 10, "steel_recess")   # belt
    c.rect(7, 10, 8, 11, "brass")
    c.px(7, 10, "brass_hi")
    c.rect(2, 6, 3, 8, "steel_mid")         # upper arms
    c.rect(12, 6, 13, 8, "steel_mid")
    return c.outline()


@icon("royal_gauntlets")
def _():
    c = Canvas(16, 16)
    c.rect(5, 11, 10, 14, "steel")           # vambrace
    c.hline(5, 10, 11, "brass_hi")
    c.hline(5, 10, 14, "brass_lo")
    c.rect(4, 4, 11, 10, "steel_mid")        # hand
    c.hline(4, 11, 4, "steel_hi")
    for x in (4, 6, 8, 10):
        c.px(x, 3, "steel_hi")               # fingertips
        c.px(x + 1, 3, "steel")
    c.vline(4, 5, 10, "steel_hi")
    c.vline(11, 5, 10, "steel")
    c.disc(7.5, 7.5, 1.6, "glass_dark")
    c.px(7, 7, "arcane_core").px(8, 7, "arcane").px(7, 8, "arcane").px(8, 8, "arcane_dim")
    c.px(3, 8, "steel_mid").px(3, 9, "steel_mid")    # thumb
    return c.outline()


@icon("royal_leggings")
def _():
    c = Canvas(16, 16)
    c.rect(3, 2, 12, 3, "steel_recess")
    c.hline(3, 12, 2, "steel_mid")
    c.rect(7, 2, 8, 3, "brass")
    c.rect(3, 4, 6, 14, "steel")
    c.rect(9, 4, 12, 14, "steel")
    c.vline(3, 4, 14, "steel_hi").vline(9, 4, 14, "steel_hi")
    c.hline(3, 6, 8, "steel_hi").hline(9, 12, 8, "steel_hi")     # knee plates
    c.hline(3, 6, 9, "steel_recess").hline(9, 12, 9, "steel_recess")
    c.rect(6, 4, 9, 7, "green_dark")                             # tunic skirt between the legs
    c.vline(7, 4, 7, "green").vline(8, 4, 7, "cloth_shadow")
    return c.outline()


@icon("royal_boots")
def _():
    c = Canvas(16, 16)
    for x0 in (1, 9):
        c.rect(x0, 6, x0 + 4, 11, "steel")
        c.rect(x0 - 1 if x0 == 1 else x0, 12, x0 + 5 if x0 == 9 else x0 + 4, 14, "steel_mid")
        c.hline(x0, x0 + 4, 6, "brass")
        c.hline(x0, x0 + 4, 7, "brass_lo")
        c.vline(x0, 8, 11, "steel_hi")
        c.hline(x0 - 1 if x0 == 1 else x0, x0 + 5 if x0 == 9 else x0 + 4, 14, "steel_recess")
    c.rect(0, 12, 1, 14, "steel_mid").px(0, 12, "steel_hi")
    c.rect(14, 12, 15, 14, "steel_mid").px(15, 12, "steel_hi")
    return c.outline()


@icon("power_core")
def _():
    c = Canvas(16, 16)
    c.disc(7.5, 7.5, 4.6, "arcane_dim")
    c.disc(7.5, 7.5, 3.4, "arcane")
    c.disc(6.8, 6.8, 1.4, "arcane_core")
    for x in (3, 12):
        c.vline(x, 3, 12, "steel")
    for y in (3, 12):
        c.hline(3, 12, y, "steel")
    c.vline(7, 3, 12, "steel_mid").hline(3, 12, 7, "steel_mid")
    c.rect(5, 1, 10, 2, "brass").hline(5, 10, 1, "brass_hi")
    c.rect(5, 13, 10, 14, "brass").hline(5, 10, 14, "brass_lo")
    return c.outline()


@icon("capacitor")
def _():
    c = Canvas(16, 16)
    c.rect(4, 3, 11, 13, "steel")
    c.vline(4, 3, 13, "steel_hi").vline(5, 3, 13, "steel_mid").vline(11, 3, 13, "steel_recess")
    c.rect(4, 6, 11, 8, "arcane_dim")
    c.hline(4, 11, 7, "arcane").px(5, 7, "arcane_core")
    c.hline(4, 11, 3, "steel_mid")
    c.rect(6, 1, 6, 2, "brass").rect(9, 1, 9, 2, "brass").px(6, 1, "brass_hi").px(9, 1, "brass_hi")
    c.hline(4, 11, 13, "steel_recess")
    return c.outline()


@icon("shield_emitter")
def _():
    c = Canvas(16, 16)
    c.disc(7.5, 6.5, 5.6, "steel")
    c.ring(7.5, 6.5, 5.2, "steel_hi")
    c.disc(7.5, 6.5, 3.2, "arcane_dim")
    c.disc(7.5, 6.5, 2.0, "arcane")
    c.px(6, 5, "arcane_core").px(7, 5, "arcane_core")
    for (x, y) in ((7, 2), (7, 11), (3, 6), (12, 6)):
        c.px(x, y, "brass")
    c.rect(6, 12, 9, 14, "steel_recess")
    c.hline(4, 11, 14, "steel_mid")
    return c.outline()


@icon("thruster_module")
def _():
    c = Canvas(16, 16)
    c.rect(6, 1, 9, 3, "brass").hline(6, 9, 1, "brass_hi")
    rows = [(6, 9), (5, 10), (5, 10), (4, 11), (4, 11), (3, 12), (3, 12), (2, 13)]
    for i, (a, b) in enumerate(rows):
        c.hline(a, b, 4 + i, "steel")
        c.px(a, 4 + i, "steel_hi")
        c.px(b, 4 + i, "steel_recess")
    c.hline(3, 12, 8, "steel_mid")
    c.hline(3, 12, 12, "arcane_dim").hline(4, 11, 12, "arcane").hline(6, 9, 12, "arcane_core")
    c.hline(5, 10, 13, "arcane_dim").hline(6, 9, 13, "arcane")
    c.hline(7, 8, 14, "arcane_dim")
    return c.outline()


@icon("arcane_focus")
def _():
    c = Canvas(16, 16)
    for y in range(1, 11):
        half = min(y, 11 - y, 4)
        c.hline(7 - half + (1 if y < 3 else 0), 8 + half - (1 if y < 3 else 0), y, "arcane_dim")
    for y in range(2, 10):
        c.px(7, y, "arcane").px(6, y, "arcane" if 3 < y < 8 else "arcane_dim")
    c.px(6, 4, "arcane_core").px(7, 3, "arcane_core").px(7, 4, "arcane_core")
    c.vline(9, 4, 8, "green_hi")
    c.rect(4, 11, 11, 12, "brass").hline(4, 11, 11, "brass_hi")
    c.px(4, 10, "brass").px(11, 10, "brass").px(3, 9, "brass_lo").px(12, 9, "brass_lo")
    c.rect(6, 13, 9, 14, "brass_lo")
    return c.outline()


@icon("rune_component")
def _():
    c = Canvas(16, 16)
    c.rect(3, 2, 12, 13, "steel_mid")
    c.hline(4, 11, 1, "steel_mid").hline(4, 11, 14, "steel")
    c.hline(3, 12, 2, "steel_hi").vline(3, 2, 13, "steel_hi")
    c.vline(12, 3, 13, "steel").hline(3, 12, 13, "steel")
    glyph = [(7, 4), (8, 4), (7, 5), (6, 6), (9, 6), (5, 7), (7, 7), (8, 7), (10, 7), (6, 8), (9, 8), (7, 9), (8, 9),
             (7, 10), (5, 11), (6, 11), (9, 11), (10, 11)]
    for (x, y) in glyph:
        c.px(x, y, "arcane")
    c.px(7, 7, "arcane_core").px(8, 7, "arcane_core")
    return c.outline()


@icon("latverian_alloy")
def _():
    c = Canvas(16, 16)
    # a vanilla-style ingot seen at an angle
    for i in range(6):
        c.hline(2 + i, 9 + i, 9 - i, "steel_mid")
        c.hline(2 + i, 9 + i, 10 - i, "steel")
    for i in range(4):
        c.hline(2, 9, 10 + i, "steel" if i < 3 else "steel_recess")
    for i in range(6):
        c.px(9 + i, 10 - i + 3, "steel_recess")
        c.vline(10 + i, 10 - i, 12 - i, "steel_recess" if i > 3 else "steel")
    c.line(3, 9, 8, 4, "green_hi")
    c.line(4, 9, 9, 4, "steel_hi")
    c.px(3, 11, "green_hi")
    return c.outline()


@icon("doombot_core")
def _():
    c = Canvas(16, 16)
    c.rect(3, 3, 12, 12, "steel_recess")
    c.frame(3, 3, 12, 12, "steel")
    c.hline(3, 12, 3, "steel_hi").vline(3, 3, 12, "steel_hi")
    for k in (5, 8, 11):
        c.px(1, k - 1, "brass").px(2, k - 1, "brass_lo").px(14, k - 1, "brass").px(13, k - 1, "brass_lo")
        c.px(k - 1, 1, "brass").px(k - 1, 2, "brass_lo").px(k - 1, 14, "brass").px(k - 1, 13, "brass_lo")
    c.disc(7.5, 7.5, 2.2, "glass_dark")
    c.px(7, 7, "arcane_core").px(8, 7, "arcane").px(7, 8, "arcane").px(8, 8, "arcane_dim")
    c.line(5, 10, 6, 9, "steel_mid").line(10, 5, 9, 6, "steel_mid")
    return c.outline()


@icon("control_device")
def _():
    c = Canvas(16, 16)
    c.vline(10, 1, 4, "steel_mid").px(10, 1, "arcane")
    c.rect(4, 4, 11, 14, "steel")
    c.vline(4, 4, 14, "steel_hi").hline(4, 11, 4, "steel_hi").vline(11, 5, 14, "steel_recess")
    c.rect(5, 5, 10, 8, "glass_dark")
    c.hline(6, 8, 6, "arcane").px(6, 7, "arcane_dim").px(9, 7, "arcane_dim")
    for (x, y) in ((6, 10), (9, 10), (6, 12), (9, 12)):
        c.px(x, y, "brass")
    c.px(7, 11, "steel_recess").px(8, 11, "steel_recess")
    return c.outline()


@icon("research_sample_container")
def _():
    c = Canvas(16, 16)
    c.rect(6, 3, 9, 12, "glass_dark")
    c.vline(6, 3, 12, "steel_hi")
    c.rect(7, 7, 9, 11, "arcane_dim")
    c.hline(7, 9, 7, "arcane").px(8, 9, "green_hi").px(7, 10, "green_hi")
    c.rect(5, 1, 10, 2, "brass").hline(5, 10, 1, "brass_hi")
    c.rect(5, 13, 10, 14, "brass").hline(5, 10, 14, "brass_lo")
    return c.outline()


# ---------------------------------------------------------------------------------- block faces -----
def steel_panel(c, x0=0, y0=0, x1=15, y1=15, rivets=True):
    c.rect(x0, y0, x1, y1, "steel")
    c.hline(x0, x1, y0, "steel_hi").vline(x0, y0, y1, "steel_mid")
    c.hline(x0, x1, y1, "steel_recess").vline(x1, y0, y1, "steel_recess")
    if rivets:
        for (x, y) in ((x0 + 1, y0 + 1), (x1 - 1, y0 + 1), (x0 + 1, y1 - 1), (x1 - 1, y1 - 1)):
            c.px(x, y, "brass")
    return c


def block_faces():
    out = {}
    # Doom Forge
    f = steel_panel(Canvas(16, 16))
    f.rect(3, 6, 12, 13, "steel_recess")
    f.rect(4, 7, 11, 12, "glass_dark")
    for x in range(4, 12):
        f.px(x, 11, "arcane_dim").px(x, 12, "arcane" if x % 2 else "arcane_dim")
    f.px(6, 10, "arcane_dim").px(9, 10, "arcane_dim")
    for x in (5, 7, 9, 11):
        f.vline(x, 7, 10, "steel")          # grate bars in front of the glow
    f.hline(3, 12, 5, "brass").hline(3, 12, 4, "brass_hi")
    out["doom_forge_front"] = f
    s = steel_panel(Canvas(16, 16))
    s.hline(1, 14, 7, "steel_recess").hline(1, 14, 8, "steel_mid")
    s.vline(3, 2, 13, "brass_lo").vline(12, 2, 13, "brass_lo")
    out["doom_forge_side"] = s
    t = steel_panel(Canvas(16, 16))
    for y in (4, 7, 10):
        t.hline(3, 12, y, "steel_recess")
        t.hline(4, 11, y, "arcane_dim" if y == 7 else "steel_recess")
    out["doom_forge_top"] = t
    # Armor Cradle
    a = steel_panel(Canvas(16, 16))
    a.rect(4, 2, 11, 13, "green_dark")
    for x in (5, 7, 9):
        a.vline(x, 2, 13, "green")
    a.rect(6, 4, 9, 8, "steel_mid").hline(6, 9, 4, "steel_hi")
    a.px(6, 6, "arcane").px(9, 6, "arcane")
    a.hline(4, 11, 13, "brass")
    out["armor_cradle_front"] = a
    b = steel_panel(Canvas(16, 16))
    b.vline(7, 1, 14, "steel_recess").vline(8, 1, 14, "steel_mid")
    b.hline(1, 14, 5, "brass_lo")
    out["armor_cradle_side"] = b
    tt = steel_panel(Canvas(16, 16))
    tt.disc(7.5, 7.5, 3.5, "steel_mid").ring(7.5, 7.5, 3.5, "brass")
    out["armor_cradle_top"] = tt
    # Power Core block
    p = steel_panel(Canvas(16, 16), rivets=False)
    p.rect(3, 3, 12, 12, "glass_dark")
    p.disc(7.5, 7.5, 3.4, "arcane_dim").disc(7.5, 7.5, 2.2, "arcane").px(7, 7, "arcane_core").px(6, 6, "arcane_core")
    p.frame(3, 3, 12, 12, "brass")
    for k in (3, 12):
        p.px(k, 7, "brass_hi").px(7, k, "brass_hi")
    out["power_core_side"] = p
    pt = steel_panel(Canvas(16, 16))
    pt.rect(5, 5, 10, 10, "arcane_dim").rect(6, 6, 9, 9, "arcane").frame(4, 4, 11, 11, "steel_recess")
    out["power_core_top"] = pt
    # Doombot Assembly Station
    d = steel_panel(Canvas(16, 16))
    d.rect(3, 3, 12, 12, "steel_recess")
    d.rect(6, 4, 9, 7, "steel_mid").px(6, 5, "arcane").px(9, 5, "arcane")     # a bot head on the bench
    d.hline(4, 11, 9, "steel_mid").vline(5, 9, 11, "steel_mid").vline(10, 9, 11, "steel_mid")
    d.hline(3, 12, 12, "brass")
    out["doombot_assembly_station_front"] = d
    ds = steel_panel(Canvas(16, 16))
    for y in (4, 8, 12):
        ds.hline(2, 13, y, "steel_recess")
    ds.vline(13, 2, 13, "brass_lo")
    out["doombot_assembly_station_side"] = ds
    dt = steel_panel(Canvas(16, 16))
    dt.line(3, 12, 8, 5, "brass").line(8, 5, 12, 7, "brass").px(12, 7, "arcane")    # an assembly arm
    out["doombot_assembly_station_top"] = dt
    # Research Console
    r = steel_panel(Canvas(16, 16))
    r.rect(2, 2, 13, 9, "glass_dark").frame(2, 2, 13, 9, "steel_recess")
    for (x0, x1, y) in ((3, 8, 3), (3, 6, 5), (3, 10, 7)):
        r.hline(x0, x1, y, "arcane_dim")
    r.rect(10, 3, 12, 5, "arcane_dim").px(11, 4, "arcane")
    for x in (3, 5, 7, 9, 11):
        r.px(x, 12, "brass").px(x, 13, "steel_recess")
    out["research_console_front"] = r
    rs = steel_panel(Canvas(16, 16))
    rs.rect(3, 3, 12, 6, "steel_recess").hline(4, 11, 4, "steel_mid")
    out["research_console_side"] = rs
    rt = steel_panel(Canvas(16, 16))
    rt.rect(3, 3, 12, 12, "steel_mid").frame(3, 3, 12, 12, "steel_recess")
    out["research_console_top"] = rt
    return out


BLOCKS = {
    "doom_forge": ("doom_forge_front", "doom_forge_side", "doom_forge_top"),
    "armor_cradle": ("armor_cradle_front", "armor_cradle_side", "armor_cradle_top"),
    "power_core_block": ("power_core_side", "power_core_side", "power_core_top"),
    "doombot_assembly_station": ("doombot_assembly_station_front", "doombot_assembly_station_side", "doombot_assembly_station_top"),
    "research_console": ("research_console_front", "research_console_side", "research_console_top"),
}
