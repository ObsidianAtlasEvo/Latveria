#!/usr/bin/env python3
"""Builds HUD sprites, item icons, block textures, vanilla-format model/blockstate/item/equipment
JSON, a vanilla-layout fallback armour texture, and preview sheets / HUD mock-ups.

Vanilla resource formats used here were checked against the 26.1.2 client assets (misode/mcmeta
26.1.2-assets branch): items/<id>.json model definitions, models/item with parent
minecraft:item/generated, block/orientable parents, facing blockstates, equipment/<id>.json with
humanoid / humanoid_leggings layers, 64x32 equipment textures, and nine_slice gui sprite metadata.
"""
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from doomart import hud, icons
from doomart.geo import Model
from doomart.paint import Painter, palette_violations
from doomart import royal_armor as RA
from doomart import render as R
from build_armor import ASSETS, PREVIEW

NS = "doom_sovereign"
ITEM_NAMES = {
    "doom_mask": "Mask of Doom", "royal_chestplate": "Royal Cuirass of Doom", "royal_leggings": "Royal Greaves of Doom",
    "royal_boots": "Royal Sabatons of Doom", "royal_gauntlets": "Royal Gauntlet Assembly", "power_core": "Power Core",
    "capacitor": "Capacitor Cell", "shield_emitter": "Shield Emitter", "thruster_module": "Thruster Module",
    "arcane_focus": "Arcane Focus", "rune_component": "Rune Component", "latverian_alloy": "Latverian Alloy",
    "doombot_core": "Doombot Core", "control_device": "Doombot Control Device",
    "research_sample_container": "Research Sample Container",
}
BLOCK_NAMES = {"doom_forge": "Doom Forge", "armor_cradle": "Armor Cradle", "power_core_block": "Power Core Block",
               "doombot_assembly_station": "Doombot Assembly Station", "research_console": "Research Console"}


def jdump(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def save(arr, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(arr, "RGBA").save(path)


def build():
    counts = {"hud_sprites": 0, "item_icons": 0, "block_textures": 0, "json": 0}
    bad = 0
    # ---- HUD ----
    sdir = os.path.join(ASSETS, "textures", "gui", "sprites", "hud")
    spr = hud.sprites()
    for name, c in spr.items():
        a = c.array()
        bad += palette_violations(a)
        save(a, os.path.join(sdir, name + ".png"))
        counts["hud_sprites"] += 1
        if name in hud.NINE_SLICE:
            w, h, border = hud.NINE_SLICE[name]
            jdump(os.path.join(sdir, name + ".png.mcmeta"),
                  {"gui": {"scaling": {"type": "nine_slice", "width": w, "height": h, "border": border}}})
            counts["json"] += 1
    for k, a in enumerate(hud.cooldown_frames()):
        save(a, os.path.join(sdir, "cooldown_%02d.png" % k))
        counts["hud_sprites"] += 1
    # ---- items ----
    icon_arrays = {}
    for name, fn in icons.ICONS.items():
        a = fn().array()
        bad += palette_violations(a)
        icon_arrays[name] = a
        save(a, os.path.join(ASSETS, "textures", "item", name + ".png"))
        jdump(os.path.join(ASSETS, "models", "item", name + ".json"),
              {"parent": "minecraft:item/generated", "textures": {"layer0": "%s:item/%s" % (NS, name)}})
        jdump(os.path.join(ASSETS, "items", name + ".json"), {"model": {"type": "minecraft:model", "model": "%s:item/%s" % (NS, name)}})
        counts["item_icons"] += 1
        counts["json"] += 2
    # ---- blocks ----
    faces = icons.block_faces()
    face_arrays = {}
    for name, c in faces.items():
        a = c.array()
        bad += palette_violations(a)
        face_arrays[name] = a
        save(a, os.path.join(ASSETS, "textures", "block", name + ".png"))
        counts["block_textures"] += 1
    for block, (front, side, top) in icons.BLOCKS.items():
        jdump(os.path.join(ASSETS, "models", "block", block + ".json"), {
            "parent": "minecraft:block/orientable",
            "textures": {"front": "%s:block/%s" % (NS, front), "side": "%s:block/%s" % (NS, side), "top": "%s:block/%s" % (NS, top)}})
        variants = {}
        for facing, yrot in (("north", 0), ("east", 90), ("south", 180), ("west", 270)):
            v = {"model": "%s:block/%s" % (NS, block)}
            if yrot:
                v["y"] = yrot
            variants["facing=" + facing] = v
        jdump(os.path.join(ASSETS, "blockstates", block + ".json"), {"variants": variants})
        jdump(os.path.join(ASSETS, "items", block + ".json"), {"model": {"type": "minecraft:model", "model": "%s:block/%s" % (NS, block)}})
        counts["json"] += 3
    # ---- equipment fallback (vanilla 64x32 layout, used if the GeckoLib renderer is unavailable) ----
    jdump(os.path.join(ASSETS, "equipment", "royal.json"), {"layers": {
        "humanoid": [{"texture": "%s:royal" % NS}], "humanoid_leggings": [{"texture": "%s:royal" % NS}]}})
    counts["json"] += 1
    for layer, arr in vanilla_armor().items():
        bad += palette_violations(arr)
        save(arr, os.path.join(ASSETS, "textures", "entity", "equipment", layer, "royal.png"))
    # ---- previews ----
    sheet_icons(icon_arrays, face_arrays)
    mockups(spr)
    print("ui: %(hud_sprites)d HUD sprites, %(item_icons)d item icons, %(block_textures)d block textures, %(json)d JSON files" % counts,
          "- palette violations: %d" % bad)
    if bad:
        raise SystemExit(1)
    return counts, ITEM_NAMES, BLOCK_NAMES


def vanilla_armor():
    """Paints the vanilla humanoid equipment layout with the Royal Armor look."""
    out = {}
    for layer, parts in (("humanoid", [("head", (0, 0), (8, 8, 8), "cloth", "hood_face"), ("body", (16, 16), (8, 12, 4), "cloth", "tabard"),
                                       ("arm", (40, 16), (4, 12, 4), "steel", "vam"), ("leg", (0, 16), (4, 12, 4), "steel", "boot")]),
                         ("humanoid_leggings", [("body", (16, 16), (8, 12, 4), "steel_dark", "belt_skirt"), ("leg", (0, 16), (4, 12, 4), "steel", "greave")])):
        m = Model("geometry.%s.vanilla_%s" % (NS, layer), 64, 32)
        b = m.bone("root", None, (0, 0, 0))
        for name, uv, size, mat, deco in parts:
            c = b.cube(name, (0, 0, 0), size, mat, deco=deco)
            c.uv = uv
        base, _ = Painter(m, VANILLA_DECOS, glow="powered").paint()
        out[layer] = base
    return out


def _hood_face(c):
    w, h = c.size("front")        # 8x8 head front: hood rim around a mask
    for y in range(1, 8):
        for x in range(1, 7):
            c.put("front", x, y, "steel_mid")
    for x in range(1, 7):
        c.put("front", x, 1, "steel_hi")
    for (x, y) in ((1, 3), (2, 3), (5, 3), (6, 3)):
        c.put("front", x, y, "arcane" if x in (2, 5) else "glass_dark")
    c.put("front", 3, 3, "steel_hi")
    c.put("front", 4, 3, "steel")
    for (x, y) in ((2, 6), (5, 6), (3, 7), (4, 7)):
        c.put("front", x, y, "steel_recess")


def _tabard(c):
    w, h = c.size("front")
    for x in range(w):
        c.put("front", x, 0, "steel_hi")
        c.put("front", x, 8, "steel_recess")
    c.put("front", 3, 8, "brass")
    c.put("front", 4, 8, "brass")
    for f in ("left", "right"):
        fw, fh = c.size(f)
        for y in range(fh):
            for x in range(fw):
                c.put(f, x, y, "steel" if y < 6 else c.g[f][y][x])


def _vam(c):
    for f in ("front", "back", "left", "right"):
        fw, fh = c.size(f)
        for x in range(fw):
            c.put(f, x, 0, "steel_hi")
            c.put(f, x, 3, "brass")
            c.put(f, x, 8, "steel_hi")
            c.put(f, x, fh - 1, "steel_recess")


def _boot(c):
    for f in ("front", "back", "left", "right"):
        fw, fh = c.size(f)
        for x in range(fw):
            c.put(f, x, fh - 4, "brass")
            c.put(f, x, fh - 1, "steel_recess")


def _belt_skirt(c):
    for f in ("front", "back", "left", "right"):
        fw, fh = c.size(f)
        for x in range(fw):
            c.put(f, x, 8, "steel_recess")
            c.put(f, x, 9, "brass" if x % 2 == 0 else "steel_mid")
            for y in range(10, fh):
                c.put(f, x, y, "green" if (x // 2) % 2 else "green_dark")


def _greave(c):
    fw, fh = c.size("front")
    for x in range(fw):
        c.put("front", x, 5, "steel_hi")
        c.put("front", x, 6, "steel_recess")


VANILLA_DECOS = {"hood_face": _hood_face, "tabard": _tabard, "vam": _vam, "boot": _boot, "belt_skirt": _belt_skirt, "greave": _greave}


def sheet_icons(icon_arrays, face_arrays):
    cells, labels = [], []
    for name, a in icon_arrays.items():
        cells.append(_on_bg(R.upscale(a, 6)))
        labels.append(name)
    for block, (front, side, top) in icons.BLOCKS.items():
        cells.append(_block_preview(face_arrays[front], face_arrays[side], face_arrays[top]))
        labels.append(block)
    R.sheet(cells, 5, labels=labels).save(os.path.join(PREVIEW, "item_icons.png"))


def _on_bg(a):
    out = np.zeros_like(a)
    out[..., :3] = 58
    out[..., 3] = 255
    al = a[..., 3:4] / 255.0
    out[..., :3] = (a[..., :3] * al + out[..., :3] * (1 - al)).astype(np.uint8)
    return out


def _block_preview(front, side, top):
    """A 16-px cube rendered with the preview renderer (the game draws block icons itself)."""
    m = Model("geometry.preview.block", 64, 48)
    b = m.bone("b", None, (0, 0, 0))
    c = b.cube("block", (-8, 0, -8), (16, 16, 16), "steel")
    c.uv = (0, 0)
    tex = np.zeros((48, 64, 4), np.uint8)
    f = c.faces()
    for name, arr in (("front", front), ("left", side), ("right", side), ("back", side), ("top", top), ("bottom", top)):
        u, v, w, h = f[name]
        tex[v:v + h, u:u + w] = arr
    return R.render(m, tex, None, yaw=-35, pitch=25, ppu=4.4, size=(96, 96), center=(0, 8), background=(58, 58, 58, 255))


def mockups(spr):
    """HUD mock-ups at three screen sizes / GUI scales (vanilla elements drawn as grey placeholders)."""
    shots = []
    for (sw, sh, scale) in ((1920, 1080, 4), (1280, 720, 3), (640, 480, 2)):
        gw, gh = sw // scale, sh // scale
        img = Image.new("RGBA", (gw, gh), (0, 0, 0, 255))
        px = img.load()
        for y in range(gh):                      # neutral sky/ground gradient so the HUD is judged on a scene-like field
            for x in range(gw):
                t = y / gh
                px[x, y] = (int(70 + 40 * t), int(96 + 20 * t), int(120 - 30 * t), 255) if t < 0.55 else (60, 78, 52, 255)
        d = ImageDraw.Draw(img)
        L = hud.layout(gw, gh)
        hx, hy, hw, hh, _ = L["hotbar (vanilla)"]
        d.rectangle([hx, hy, hx + hw - 1, hy + hh - 1], outline=(150, 150, 150, 255), fill=(40, 40, 40, 200))
        d.rectangle([hx, hy - 10, hx + 80, hy - 2], outline=(120, 120, 120, 255))       # vanilla hearts row placeholder
        d.rectangle([hx + hw - 81, hy - 10, hx + hw - 1, hy - 2], outline=(120, 120, 120, 255))

        def paste(name, x, y, frac=None):
            a = spr[name].array()
            if frac is not None:
                a = a.copy()
                a[:, int(a.shape[1] * frac):] = 0
            im = Image.fromarray(a, "RGBA")
            img.alpha_composite(im, (x, y))

        for bar, frac in (("energy", 0.62), ("heat", 0.35), ("shield", 0.8), ("focus", 0.45)):
            x, y, w, h, s = L[bar]
            paste(s + "_background", x, y)
            paste(s + "_fill", x, y, frac)
            ix, iy, _, _, isp = L[bar + "_icon"]
            paste(isp, ix, iy)
        x, y, w, h, _ = L["warnings"]
        paste("warn_overheat", x, y)
        paste("warn_lock_on", x + 11, y)
        x, y, w, h, _ = L["abilities"]
        for k, ab in enumerate(("ability_bolt", "ability_force_field", "ability_scan", "ability_flight")):
            paste("ability_slot", x + k * 22, y)
            paste(ab, x + k * 22 + 2, y + 2)
            if k == 1:                                   # the force field is on cooldown in this mock-up
                img.alpha_composite(Image.fromarray(hud.cooldown_frames()[6], "RGBA"), (x + k * 22 + 2, y + 2))
        paste("ability_slot_selected", x, y)
        x, y, w, h, _ = L["scan_panel"]
        panel = spr["scan_panel"].array()
        big = nine_slice(panel, w, h, 4)
        img.alpha_composite(Image.fromarray(big, "RGBA"), (x, y))
        d.text((x + 6, y + 5), "BLAZE", fill=(210, 255, 212, 255))
        d.text((x + 6, y + 17), "Knowledge 62%", fill=(160, 170, 170, 255))
        img.alpha_composite(Image.fromarray(spr["knowledge_bar"].array(), "RGBA"), (x + 6, y + 30))
        d.text((x + 6, y + 36), "Immune: fire", fill=(160, 170, 170, 255))
        cx, cy = gw // 2, int(gh * 0.45)
        d.rectangle([cx - 8, cy - 14, cx + 8, cy + 14], fill=(170, 120, 40, 255))          # a target stand-in
        tb = spr["target_bracket_locked"].array()
        for fx, fy, (ox, oy) in ((False, False, (-12, -18)), (True, False, (8, -18)), (False, True, (-12, 14)), (True, True, (8, 14))):
            a = tb[:, ::-1] if fx else tb
            a = a[::-1] if fy else a
            img.alpha_composite(Image.fromarray(np.ascontiguousarray(a), "RGBA"), (cx + ox, cy + oy))
        d.line([gw // 2 - 4, gh // 2, gw // 2 + 4, gh // 2], fill=(255, 255, 255, 255))
        d.line([gw // 2, gh // 2 - 4, gw // 2, gh // 2 + 4], fill=(255, 255, 255, 255))
        out = img.resize((sw, sh), Image.NEAREST)
        out = out.resize((sw // 2, sh // 2), Image.NEAREST) if sw > 1000 else out
        ImageDraw.Draw(out).text((8, 8), "%dx%d, GUI scale %d%s" % (sw, sh, scale, "  (compact layout)" if L["compact"] else ""), fill=(255, 255, 255, 255))
        out.save(os.path.join(PREVIEW, "hud_mockup_%dx%d_gui%d.png" % (sw, sh, scale)))


def nine_slice(src, w, h, b):
    sh_, sw_ = src.shape[:2]
    out = np.zeros((h, w, 4), np.uint8)
    xs = [0, b, sw_ - b, sw_]
    ys = [0, b, sh_ - b, sh_]
    xd = [0, b, w - b, w]
    yd = [0, b, h - b, h]
    for i in range(3):
        for j in range(3):
            tile = src[ys[i]:ys[i + 1], xs[j]:xs[j + 1]]
            th, tw = yd[i + 1] - yd[i], xd[j + 1] - xd[j]
            ry = np.arange(th) % tile.shape[0]
            rx = np.arange(tw) % tile.shape[1]
            out[yd[i]:yd[i + 1], xd[j]:xd[j + 1]] = tile[ry][:, rx]
    return out


if __name__ == "__main__":
    build()
