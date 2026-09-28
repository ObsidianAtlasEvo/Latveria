"""Renders the voxel model of the combined world (for the v3 audit and the v3 previews).

All renders are orthographic, 1 pixel per block times a scale factor, drawn from sim.World.
They show exactly what the command files build (trees placed by `place feature` are unknown to
the model and appear only as a marker).
"""
import numpy as np
from PIL import Image, ImageDraw

import preview

LABEL = (235, 235, 235)


def lut(world):
    """RGB per state id (air = None -> alpha 0)."""
    n = len(world.states)
    rgb = np.zeros((n, 3), np.uint8)
    solid = np.zeros(n, bool)
    for i, s in enumerate(world.states):
        nm = s.split("[", 1)[0]
        c = preview.color(nm)
        if c is None or nm in ("light", "barrier", "structure_void"):
            continue
        rgb[i] = c
        solid[i] = True
    return rgb, solid


def crop(world, x1, y1, z1, x2, y2, z2):
    return world.W[world._sl(x1, y1, z1, x2, y2, z2)]


def top_down(world, box, scale=2, shade=True):
    """box = (x1, y1, z1, x2, y2, z2). Colour of the highest non-air block, shaded by height."""
    x1, y1, z1, x2, y2, z2 = box
    sub = crop(world, *box)
    rgb, solid = lut(world)
    S = solid[sub]                                        # x, y, z
    any_ = S.any(axis=1)
    ytop = S.shape[1] - 1 - np.argmax(S[:, ::-1, :], axis=1)
    ids = np.take_along_axis(sub, ytop[:, None, :], axis=1)[:, 0, :]
    img = rgb[ids].astype(float)
    if shade:
        h = (ytop + y1).astype(float)
        f = np.clip(0.55 + (h - y1) / max(1, (y2 - y1)) * 0.9, 0.5, 1.25)
        # relief: darker on the south/east side of height steps
        dz = np.zeros_like(h)
        dz[:, 1:] = h[:, 1:] - h[:, :-1]
        f = f * np.clip(1 - 0.04 * np.clip(-dz, 0, 8), 0.6, 1)
        img = img * f[..., None]
    img[~any_] = (18, 22, 26)
    img = np.clip(img, 0, 255).astype(np.uint8).transpose(1, 0, 2)      # rows = z, cols = x
    return Image.fromarray(img).resize(((x2 - x1 + 1) * scale, (z2 - z1 + 1) * scale), Image.NEAREST)


def plan(world, box, y, scale=6, window=(0, 2)):
    """Floor plan at walking level y: walls (solid at y..y+1) dark, floor colours, openings light."""
    x1, z1, x2, z2 = box
    rgb, solid = lut(world)
    feet = crop(world, x1, y, z1, x2, y, z2)[:, 0, :]
    head = crop(world, x1, y + 1, z1, x2, y + 1, z2)[:, 0, :]
    floor = crop(world, x1, y - 1, z1, x2, y - 1, z2)[:, 0, :]
    img = rgb[floor].astype(float) * 0.9 + 25
    wall = solid[feet] & solid[head]
    obj = solid[feet] & ~solid[head]
    img[wall] = rgb[feet][wall] * 0.45
    img[obj] = rgb[feet][obj] * 0.95
    nofloor = ~solid[floor] & ~solid[feet]
    img[nofloor] = (14, 16, 20)
    img = np.clip(img, 0, 255).astype(np.uint8).transpose(1, 0, 2)
    return Image.fromarray(img).resize(((x2 - x1 + 1) * scale, (z2 - z1 + 1) * scale), Image.NEAREST)


def elevation(world, box, facing, scale=3):
    """Orthographic elevation seen from `facing` (the side the viewer stands on): south, north, east, west."""
    x1, y1, z1, x2, y2, z2 = box
    sub = crop(world, *box)
    rgb, solid = lut(world)
    S = solid[sub]
    if facing in ("south", "north"):
        axis = 2
        order = slice(None, None, -1) if facing == "south" else slice(None)
        A = S[:, :, order]
        ids = sub[:, :, order]
        depth = np.argmax(A, axis=2)
        hit = A.any(axis=2)
        col = np.take_along_axis(ids, depth[..., None], axis=2)[..., 0]
        n = A.shape[2]
        img = rgb[col].astype(float) * (1.1 - 0.6 * depth[..., None] / n)
        img[~hit] = (150, 175, 200)
        img = img.transpose(1, 0, 2)[::-1]                     # rows = y (top first), cols = x
        if facing == "north":
            img = img[:, ::-1]
    else:
        order = slice(None, None, -1) if facing == "east" else slice(None)
        A = S[order, :, :]
        ids = sub[order, :, :]
        depth = np.argmax(A, axis=0)
        hit = A.any(axis=0)
        col = np.take_along_axis(ids, depth[None], axis=0)[0]
        n = A.shape[0]
        img = rgb[col].astype(float) * (1.1 - 0.6 * depth[..., None] / n)
        img[~hit] = (150, 175, 200)
        img = img[::-1]                                        # rows = y (top first), cols = z
        if facing == "east":
            img = img[:, ::-1]
    img = np.clip(img, 0, 255).astype(np.uint8)
    h, w = img.shape[:2]
    return Image.fromarray(img).resize((w * scale, h * scale), Image.NEAREST)


def underground(world, box, scale=2):
    """Air voids below ground (tunnels, cisterns, mines), coloured by depth; solid ground dark."""
    x1, y1, z1, x2, y2, z2 = box
    sub = crop(world, *box)
    rgb, solid = lut(world)
    S = solid[sub]
    void = ~S
    # a void counts as a built underground space when it has a floor and a ceiling close by
    # (the model knows nothing of natural ground, so open unknown volume must not show)
    up = np.zeros_like(S)
    dn = np.zeros_like(S)
    for k in range(1, 6):
        up[:, :-k, :] |= S[:, k:, :]
        dn[:, k:, :] |= S[:, :-k, :]
    ug = void & up & dn
    anyv = ug.any(axis=1)
    ytop = S.shape[1] - 1 - np.argmax(ug[:, ::-1, :], axis=1)
    t = (ytop / max(1, S.shape[1] - 1))
    img = np.zeros(anyv.shape + (3,))
    img[..., 0] = 60 + 190 * t
    img[..., 1] = 90 + 120 * (1 - abs(t - 0.5) * 2)
    img[..., 2] = 220 - 170 * t
    img[~anyv] = (28, 30, 34)
    img = np.clip(img, 0, 255).astype(np.uint8).transpose(1, 0, 2)
    return Image.fromarray(img).resize(((x2 - x1 + 1) * scale, (z2 - z1 + 1) * scale), Image.NEAREST)


def overlay_points(img, box, scale, pts, color, r=2):
    x1, z1 = box[0], box[2]
    d = ImageDraw.Draw(img)
    for (x, z) in pts:
        px, pz = (x - x1) * scale, (z - z1) * scale
        d.ellipse([px - r, pz - r, px + r, pz + r], fill=color)
    return img


def label(img, text, xy=(6, 4)):
    d = ImageDraw.Draw(img)
    d.rectangle([xy[0] - 3, xy[1] - 2, xy[0] + 7 * len(text) + 3, xy[1] + 12], fill=(0, 0, 0))
    d.text(xy, text, fill=LABEL)
    return img


def labels(img, box, scale, items, color=(255, 255, 255)):
    x1, z1 = box[0], box[2]
    d = ImageDraw.Draw(img)
    for (x, z, t) in items:
        px, pz = (x - x1) * scale, (z - z1) * scale
        w = 6 * len(t)
        d.rectangle([px - w // 2 - 2, pz - 6, px + w // 2 + 2, pz + 6], fill=(0, 0, 0))
        d.text((px - w // 2, pz - 5), t, fill=color)
    return img


def grid(img, box, scale, step=50, color=(255, 255, 255, 60)):
    x1, z1, x2, z2 = box[0], box[2], box[3], box[5]
    d = ImageDraw.Draw(img, "RGBA")
    for x in range((x1 // step) * step, x2 + 1, step):
        d.line([((x - x1) * scale, 0), ((x - x1) * scale, img.size[1])], fill=color)
    for z in range((z1 // step) * step, z2 + 1, step):
        d.line([(0, (z - z1) * scale), (img.size[0], (z - z1) * scale)], fill=color)
    return img


def sheet(images, cols, pad=8, bg=(10, 12, 14)):
    w = max(i.size[0] for i in images)
    h = max(i.size[1] for i in images)
    rows = (len(images) + cols - 1) // cols
    out = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad) + pad), bg)
    for k, im in enumerate(images):
        out.paste(im, (pad + (k % cols) * (w + pad), pad + (k // cols) * (h + pad)))
    return out
