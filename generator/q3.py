"""Interactive helpers for querying the combined world (used while authoring v3)."""
import collections, os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import sim
_W = None
def world():
    global _W
    if _W is None:
        _W = sim.World()
        for f in ("latveria_commands.txt", "latveria_expansion_commands.txt", "latveria_lighting_commands.txt"):
            _W.load_file(os.path.join(HERE, "..", "windows", f))
    return _W
def names(x1, y1, z1, x2, y2, z2):
    w = world(); sub = w.W[w._sl(min(x1,x2),min(y1,y2),min(z1,z2),max(x1,x2),max(y1,y2),max(z1,z2))]
    ids, cnt = np.unique(sub, return_counts=True)
    c = collections.Counter()
    for i, n in zip(ids, cnt): c[w.states[i].split("[")[0]] += int(n)
    return c.most_common()
def column(x, z, y1, y2):
    w = world(); return [(y, w.get(x, y, z)) for y in range(y1, y2 + 1) if w.name(x, y, z) != "air"]
def slice_y(x1, z1, x2, z2, y, legend=None):
    w = world(); legend = legend or {}
    out = []
    for z in range(z1, z2 + 1):
        row = ""
        for x in range(x1, x2 + 1):
            n = w.name(x, y, z)
            row += legend.get(n, "." if n == "air" else n[0])
        out.append("%5d %s" % (z, row))
    return "\n".join(out)
def show(x1, z1, x2, z2, y):
    """Slice with an automatic one-character legend."""
    w = world(); chars = ".#abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789@$%&*+=?<>~^"
    leg = {"air": "."}; rows = []
    for z in range(z1, z2 + 1):
        row = ""
        for x in range(x1, x2 + 1):
            n = w.name(x, y, z)
            if n not in leg: leg[n] = chars[len(leg)] if len(leg) < len(chars) else "!"
            row += leg[n]
        rows.append("%5d %s" % (z, row))
    hdr = "      " + "".join(str(abs(x) % 10) for x in range(x1, x2 + 1))
    return "y=%d  x %d..%d\n" % (y, x1, x2) + hdr + "\n" + "\n".join(rows) + "\n  " + "  ".join("%s=%s" % (c, n) for n, c in leg.items())
