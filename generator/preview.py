#!/usr/bin/env python3
"""Dry-run the generated command file in a voxel grid and render preview images.

    pip install numpy pillow
    python preview.py            -> ../docs/preview_*.png

This executes every fill / setblock (including `replace` filters) the way the
game would, so the images show exactly what the command list builds.
"""
import os
import re
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
CMDS = [os.path.join(HERE, "..", "windows", f) for f in (sys.argv[1:] or ["latveria_commands.txt"])]
TAG = "" if len(CMDS) == 1 else "_expansion"
OUT = os.path.join(HERE, "..", "docs")

X0, X1 = -305, 305
Y0, Y1 = -12, 135
Z0, Z1 = -256, 244
TOK = re.compile(r"\$([xyz])\((-?[0-9.]+)\)")

names = ["air"]
ids = {"air": 0}


def bid(name):
    if name not in ids:
        ids[name] = len(names)
        names.append(name)
    return ids[name]


def base(spec):
    return re.split(r"[\[{]", spec.replace("minecraft:", ""), 1)[0]


def coords(tokens):
    return [int(float(v) // 1) for v in tokens]


COL = [
    ("air", None), ("water", (50, 90, 200)), ("lava", (230, 100, 20)), ("grass_block", (95, 150, 60)),
    ("moss", (90, 130, 50)), ("leaves", (60, 110, 40)), ("farmland", (110, 75, 45)), ("wheat", (200, 180, 80)),
    ("carrots", (230, 130, 40)), ("potatoes", (180, 170, 70)), ("beetroots", (150, 40, 50)),
    ("dirt", (120, 85, 55)), ("coarse_dirt", (110, 80, 55)), ("oxidized", (80, 160, 130)), ("copper", (200, 120, 80)),
    ("deepslate", (65, 65, 70)), ("blackstone", (40, 35, 40)), ("stone_brick", (125, 125, 125)),
    ("andesite", (135, 135, 135)), ("cobble", (115, 115, 115)), ("tuff", (105, 105, 95)), ("stone", (120, 120, 120)),
    ("calcite", (225, 225, 220)), ("white_terracotta", (210, 180, 160)), ("yellow_terracotta", (190, 140, 50)),
    ("light_gray_terracotta", (140, 115, 105)), ("terracotta", (160, 90, 60)), ("sandstone", (215, 205, 160)),
    ("mud_brick", (140, 105, 80)), ("brick", (150, 70, 55)), ("mangrove", (120, 50, 45)), ("dark_oak", (65, 45, 25)),
    ("spruce", (110, 80, 50)), ("oak", (160, 130, 80)), ("birch", (200, 185, 130)), ("green", (40, 110, 40)),
    ("lime", (110, 190, 40)), ("iron", (220, 220, 220)), ("gold", (240, 200, 60)), ("emerald", (40, 200, 90)),
    ("glass", (170, 210, 220)), ("lantern", (250, 210, 120)), ("wool", (220, 220, 220)), ("red", (170, 40, 40)),
    ("blue", (50, 60, 160)), ("yellow", (220, 200, 50)), ("black", (25, 25, 25)), ("white", (235, 235, 235)),
    ("quartz", (235, 230, 225)), ("obsidian", (30, 20, 50)), ("sand", (220, 210, 160)), ("gravel", (130, 125, 120)),
    ("hay", (200, 170, 50)), ("bookshelf", (120, 90, 50)), ("path", (150, 120, 70)),
]


def color(name):
    if name in ("air", "cave_air", "void_air"):
        return None
    for key, c in COL[1:]:
        if key in name:
            return c
    return (150, 140, 130)


def main():
    W = np.zeros((X1 - X0 + 1, Y1 - Y0 + 1, Z1 - Z0 + 1), dtype=np.uint16)
    n = 0
    import itertools
    for line in itertools.chain(*[open(p, encoding="utf-8") for p in CMDS]):
        if line.startswith(("#", "!")):
            continue
        cmd = line.rstrip("\r\n").split("\t", 1)[1]
        parts = cmd.split(" ")
        if parts[0] not in ("fill", "setblock"):
            continue
        nums = TOK.findall(cmd)
        vals = coords([v for _, v in nums])
        rest = TOK.sub("", cmd).split()
        if parts[0] == "fill":
            x1, y1, z1, x2, y2, z2 = vals
            blk = rest[1]
            flt = rest[3] if len(rest) > 3 and rest[2] == "replace" else None
        else:
            x1, y1, z1 = vals
            x2, y2, z2 = x1, y1, z1
            blk = rest[1]
            flt = None
        if y2 < Y0 or y1 > Y1:
            continue
        a = (slice(x1 - X0, x2 - X0 + 1), slice(max(y1, Y0) - Y0, min(y2, Y1) - Y0 + 1), slice(z1 - Z0, z2 - Z0 + 1))
        v = bid(base(blk))
        if flt:
            sub = W[a]
            sub[sub == bid(base(flt))] = v
        else:
            W[a] = v
        n += 1
    print("executed", n, "block commands;", len(names), "distinct blocks")
    lut = np.array([color(nm) or (0, 0, 0) for nm in names], dtype=np.float32)
    os.makedirs(OUT, exist_ok=True)

    # top-down map with height shading
    solid = W != 0
    ny = W.shape[1]
    top = ny - 1 - np.argmax(solid[:, ::-1, :], axis=1)
    has = solid.any(axis=1)
    topid = np.take_along_axis(W, top[:, None, :], axis=1)[:, 0, :]
    rgb = lut[topid]
    shade = 0.55 + 0.45 * (top / float(ny))
    rgb = rgb * shade[..., None]
    rgb[~has] = (0, 0, 0)
    img = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8).transpose(1, 0, 2))
    img = img.resize((img.width * 3, img.height * 3), Image.NEAREST)
    img.save(os.path.join(OUT, "preview_top%s.png" % TAG))

    # elevation from the south (looking north), depth-shaded
    def elevation(axis_view, fname, flip=False):
        if axis_view == "south":
            arr = W[:, :, ::-1]            # scan from +z towards -z
            depth_axis = 2
        else:
            arr = np.transpose(W, (2, 1, 0))[:, :, ::-1]  # from +x looking west
            depth_axis = 2
        s = arr != 0
        first = np.argmax(s, axis=depth_axis)
        hit = s.any(axis=depth_axis)
        fid = np.take_along_axis(arr, first[..., None], axis=depth_axis)[..., 0]
        c_ = lut[fid] * (1.0 - 0.55 * (first / float(arr.shape[depth_axis])))[..., None]
        c_[~hit] = (160, 200, 235)
        im = Image.fromarray(np.clip(c_, 0, 255).astype(np.uint8).transpose(1, 0, 2)[::-1])
        im = im.resize((im.width * 3, im.height * 3), Image.NEAREST)
        im.save(os.path.join(OUT, fname))

    elevation("south", "preview_south%s.png" % TAG)
    elevation("east", "preview_east%s.png" % TAG)

    # horizontal slices through the keep
    for yy, nm in (() if TAG else ((6, "dungeon"), (13, "ground"), (29, "second"), (39, "third"))):
        sl = W[:, yy - Y0, :]
        c_ = lut[sl]
        c_[sl == 0] = (20, 20, 20)
        im = Image.fromarray(np.clip(c_, 0, 255).astype(np.uint8).transpose(1, 0, 2))
        im = im.crop((-X0 - 60, -Z0 - 225, -X0 + 60, -Z0 - 95)).resize((120 * 5, 130 * 5), Image.NEAREST)
        im.save(os.path.join(OUT, "plan_%s.png" % nm))
    print("images written to", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
