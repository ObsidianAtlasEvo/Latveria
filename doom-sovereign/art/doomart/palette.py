"""The DOOM: SOVEREIGN palette.

The eight SPEC colours are the ones fixed by the art direction. The DERIVED colours are the
minimum extra steps needed for pixel-art shading of brass and for the emissive ramp; each is
documented with what it is derived from so nobody mistakes it for a free choice.
"""


def hexrgb(h):
    h = h.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


SPEC = {
    "green_dark": "#1F4934",      # primary green (low end of #1F4934-#285C3E)
    "green": "#285C3E",           # primary green (high end)
    "cloth_shadow": "#142D24",
    "green_hi": "#39724C",        # green highlight
    "steel": "#343A3C",           # steel base
    "steel_hi": "#667074",        # steel highlight
    "steel_recess": "#1E2325",
    "brass": "#8D743F",           # aged brass
    "arcane": "#65E86B",          # arcane green
}

DERIVED = {
    # brass needs a light and a dark step; both keep the aged-brass hue (about 41 deg)
    "brass_hi": ("#B39456", "aged brass lightened ~27 % in value, same hue"),
    "brass_lo": ("#5B4A28", "aged brass darkened ~35 % in value, same hue"),
    # one intermediate steel step for bevels on large plates
    "steel_mid": ("#4B5356", "midpoint of steel base and steel highlight"),
    # emissive ramp: arcane green as the body, a near-white core and a dim edge
    "arcane_core": ("#D2FFD4", "arcane green toward white, for the hottest emitter pixels"),
    "arcane_dim": ("#2F9A45", "arcane green at ~60 % value, for fading edges and low power"),
    # tech glow for the scanner/HUD accents (still green: Doom's tech glows green, sorcery glows green-white)
    "glass_dark": ("#16201C", "steel recess with a green cast: unlit lens/eye glass"),
}

COLORS = {k: hexrgb(v) for k, v in SPEC.items()}
COLORS.update({k: hexrgb(v[0]) for k, v in DERIVED.items()})
TRANSPARENT = (0, 0, 0, 0)


def rgba(name, a=255):
    r, g, b = COLORS[name]
    return (r, g, b, a)


def all_rgb():
    """Every colour a generated texture is allowed to contain (alpha aside)."""
    return set(COLORS.values())
