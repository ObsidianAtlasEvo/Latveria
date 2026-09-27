"""A small software renderer for Bedrock/GeckoLib geometry, used only to preview and inspect the
generated assets (no Minecraft available). Orthographic, z-buffered, nearest-texel sampling,
flat per-face light, emissive pass drawn unlit.

Transform emulation (our reading of GeckoLib's renderer; exact parity is awaiting runtime
validation in the game):
  gecko space  g = (-x, y, z) of Bedrock space (x negated), pivots and position offsets likewise.
  bone matrix  M = parent * T(pos) * T(pivot) * Rz(rz) * Ry(-ry) * Rx(-rx) * S(scale) * T(-pivot)
  world        = Ry(180 deg) * g   (an entity at yaw 0 faces south, +z)
So the model's front ends up facing +z and its right side at -x, which the front camera (at +z,
looking toward -z) shows on the viewer's left - as when facing a real person.
"""
import math

import numpy as np

FACE_NORMALS = {  # Bedrock space
    "front": (0, 0, -1), "back": (0, 0, 1), "right": (-1, 0, 0),
    "left": (1, 0, 0), "top": (0, 1, 0), "bottom": (0, -1, 0),
}
LIGHT = np.array([-0.3, 0.6, 0.75])
LIGHT = LIGHT / np.linalg.norm(LIGHT)


def rx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0, 0], [0, c, -s, 0], [0, s, c, 0], [0, 0, 0, 1]], float)


def ry(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s, 0], [0, 1, 0, 0], [-s, 0, c, 0], [0, 0, 0, 1]], float)


def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], float)


def tr(x, y, z):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def sc(x, y, z):
    return np.diag([x, y, z, 1.0])


def bone_matrices(model, pose=None):
    """World matrices (in gecko space) for every bone, given an optional additive pose."""
    pose = pose or {}
    mats = {}
    for b in model.bones:
        p = pose.get(b.name, {})
        rot = [b.rotation[i] + p.get("rotation", (0, 0, 0))[i] for i in range(3)]
        pos = p.get("position", (0, 0, 0))
        s = p.get("scale", (1, 1, 1))
        piv = (-b.pivot[0], b.pivot[1], b.pivot[2])
        local = (tr(-pos[0], pos[1], pos[2]) @ tr(*piv) @ rz(math.radians(rot[2])) @ ry(math.radians(-rot[1]))
                 @ rx(math.radians(-rot[0])) @ sc(*s) @ tr(-piv[0], -piv[1], -piv[2]))
        mats[b.name] = (mats[b.parent] @ local) if b.parent else local
    return mats


def cube_faces(c):
    """(face, corners in Bedrock space, uv corners) with inflate applied to geometry only."""
    i = c.inflate
    x0, y0, z0 = (c.origin[k] - i for k in range(3))
    x1, y1, z1 = (c.origin[k] + c.size[k] + i for k in range(3))
    f = c.faces()
    out = []

    def rect(name, corners):
        u, v, w, h = f[name]
        uv = [(u, v), (u + w, v), (u + w, v + h), (u, v + h)]
        out.append((name, corners, uv, (u, v, w, h)))

    rect("front", [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)])
    rect("back", [(x1, y1, z1), (x0, y1, z1), (x0, y0, z1), (x1, y0, z1)])
    rect("right", [(x0, y1, z1), (x0, y1, z0), (x0, y0, z0), (x0, y0, z1)])
    rect("left", [(x1, y1, z0), (x1, y1, z1), (x1, y0, z1), (x1, y0, z0)])
    rect("top", [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)])
    rect("bottom", [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)])
    if c.mirror:
        # vanilla mirror: every face flipped horizontally; left and right swap texture regions
        regions = {n: r for (n, _, _, r) in out}
        fixed = []
        for (n, corners, uv, r) in out:
            src = {"left": "right", "right": "left"}.get(n, n)
            u, v, w, h = regions[src]
            fixed.append((n, corners, [(u + w, v), (u, v), (u, v + h), (u + w, v + h)], regions[src]))
        out = fixed
    return out


def render(model, tex, glow=None, pose=None, yaw=0.0, pitch=0.0, ppu=12, size=None, center=None,
           hide=(), background=(24, 26, 28, 255), lean=0.0, roll=0.0, lift=0.0):
    """Renders the model. ``ppu`` = output pixels per model unit. ``lean``/``roll`` tilt the whole
    entity forward/sideways about its middle (what the flight renderer does with FlightOutput),
    ``lift`` raises it. Returns an RGBA numpy image."""
    mats = bone_matrices(model, pose)
    flip = ry(math.pi)
    body = tr(0, 16 + lift, 0) @ rz(math.radians(-roll)) @ rx(math.radians(lean)) @ tr(0, -16, 0)
    view = rx(math.radians(pitch)) @ ry(math.radians(yaw)) @ body @ flip
    tris = []
    for b in model.bones:
        if b.name in hide:
            continue
        M = view @ mats[b.name]
        lin = M[:3, :3]
        for c in b.cubes:
            for (name, corners, uv, r) in cube_faces(c):
                if r[2] == 0 or r[3] == 0:
                    continue
                n = np.array(FACE_NORMALS[name], float)
                n = lin @ np.array([-n[0], n[1], n[2]])
                nn = np.linalg.norm(n)
                if nn == 0:
                    continue
                n /= nn
                if n[2] <= 1e-6:
                    continue
                pts = []
                for (x, y, z) in corners:
                    g = M @ np.array([-x, y, z, 1.0])
                    pts.append(g[:3])
                light = 0.62 + 0.38 * max(0.0, float(n @ LIGHT))  # roughly vanilla entity shading: top/front bright, sides and bottom darker
                tris.append((pts, uv, light))
    if not tris:
        raise ValueError("nothing visible")
    allp = np.array([p for t in tris for p in t[0]])
    lo, hi = allp.min(axis=0), allp.max(axis=0)
    if center is None:
        center = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)
    if size is None:
        size = (int((hi[0] - lo[0]) * ppu) + 2 * ppu, int((hi[1] - lo[1]) * ppu) + 2 * ppu)
    W, H = size
    color = np.zeros((H, W, 3), float)
    alpha = np.zeros((H, W), bool)
    zbuf = np.full((H, W), -1e9)
    emis = np.zeros((H, W), bool)
    th, tw = tex.shape[:2]
    for pts, uv, light in tris:
        sp = [((p[0] - center[0]) * ppu + W / 2, (center[1] - p[1]) * ppu + H / 2, p[2]) for p in pts]
        for tri in ((0, 1, 2), (0, 2, 3)):
            raster(sp, uv, tri, tex, glow, light, color, alpha, zbuf, emis, W, H, tw, th)
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.array(background[:3])
    out[..., 3] = background[3]
    out[alpha, :3] = np.clip(color[alpha], 0, 255).astype(np.uint8)
    out[alpha, 3] = 255
    return out


def raster(sp, uv, tri, tex, glow, light, color, alpha, zbuf, emis, W, H, tw, th):
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = (sp[i] for i in tri)
    (u0, v0), (u1, v1), (u2, v2) = (uv[i] for i in tri)
    minx, maxx = int(max(0, math.floor(min(x0, x1, x2)))), int(min(W - 1, math.ceil(max(x0, x1, x2))))
    miny, maxy = int(max(0, math.floor(min(y0, y1, y2)))), int(min(H - 1, math.ceil(max(y0, y1, y2))))
    if minx > maxx or miny > maxy:
        return
    den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(den) < 1e-12:
        return
    ys, xs = np.mgrid[miny:maxy + 1, minx:maxx + 1]
    px, py = xs + 0.5, ys + 0.5
    a = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / den
    b = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / den
    c = 1 - a - b
    inside = (a >= -1e-9) & (b >= -1e-9) & (c >= -1e-9)
    if not inside.any():
        return
    z = a * z0 + b * z1 + c * z2
    u = a * u0 + b * u1 + c * u2
    v = a * v0 + b * v1 + c * v2
    tu = np.clip(np.floor(u).astype(int), min(u0, u1, u2), max(u0, u1, u2) - 1)
    tv = np.clip(np.floor(v).astype(int), min(v0, v1, v2), max(v0, v1, v2) - 1)
    tu = np.clip(tu, 0, tw - 1)
    tv = np.clip(tv, 0, th - 1)
    texel = tex[tv, tu]
    g = glow[tv, tu] if glow is not None else None
    sub = (slice(miny, maxy + 1), slice(minx, maxx + 1))
    visible = inside & (z > zbuf[sub] + 1e-7)
    solid = visible & (texel[..., 3] > 0)
    if g is not None:
        lit = visible & (g[..., 3] > 0)
    else:
        lit = np.zeros_like(visible)
    draw = solid | lit
    if not draw.any():
        return
    zsub = zbuf[sub]
    zsub[draw] = z[draw]
    csub = color[sub]
    csub[solid] = texel[solid][:, :3] * light
    if g is not None:
        csub[lit] = g[lit][:, :3]
    alpha[sub][draw] = True
    asub = alpha[sub]
    asub[draw] = True
    emis[sub][lit] = True


def sheet(images, cols, gap=8, background=(24, 26, 28, 255), labels=None):
    """Tiles images into one contact sheet (all cells sized to the largest image)."""
    from PIL import Image, ImageDraw
    cw = max(i.shape[1] for i in images)
    ch = max(i.shape[0] for i in images) + (14 if labels else 0)
    rows = (len(images) + cols - 1) // cols
    out = Image.new("RGBA", (cols * cw + (cols + 1) * gap, rows * ch + (rows + 1) * gap), background)
    d = ImageDraw.Draw(out)
    for k, im in enumerate(images):
        x = gap + (k % cols) * (cw + gap)
        y = gap + (k // cols) * (ch + gap)
        img = Image.fromarray(im, "RGBA")
        out.paste(img, (x + (cw - im.shape[1]) // 2, y + (ch - im.shape[0] - (14 if labels else 0)) // 2), img)
        if labels:
            d.text((x + 2, y + ch - 13), labels[k], fill=(190, 200, 195, 255))
    return out


def upscale(arr, k):
    return np.repeat(np.repeat(arr, k, axis=0), k, axis=1)
