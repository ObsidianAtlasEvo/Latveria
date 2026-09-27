"""Animation authoring, sampling, export and validation (Bedrock animation JSON as read by GeckoLib).

Conventions (derived from the transform emulation in render.py; to be confirmed in game):
  arms/legs:  rotation x NEGATIVE swings the limb FORWARD (raise an arm, step a leg forward)
  right limb: rotation z POSITIVE swings it OUTWARD (left limb: negative)
  elbow:      forearm x NEGATIVE flexes;   knee: shin x POSITIVE flexes
  head/body:  rotation x POSITIVE pitches forward/down; y POSITIVE turns toward the model's right
  cloak:      x POSITIVE swings the hem backward
  position:   model pixels, y up, z POSITIVE is backward (Bedrock space)

Keyframe easing follows our reading of GeckoLib: the easing named on a keyframe shapes the
segment that ENDS at that keyframe. Unverified until run in GeckoLib.
"""
import json
import math

CHANNELS = ("rotation", "position", "scale")


# ---- easing (Penner equations, the set GeckoLib names) ---------------------------------------------
def _bounce_out(t):
    n1, d1 = 7.5625, 2.75
    if t < 1 / d1:
        return n1 * t * t
    if t < 2 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    if t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    t -= 2.625 / d1
    return n1 * t * t + 0.984375


def _in_out(f_in):
    return lambda t: f_in(2 * t) / 2 if t < 0.5 else 1 - f_in(2 - 2 * t) / 2


_BASE_IN = {
    "Sine": lambda t: 1 - math.cos(t * math.pi / 2),
    "Quad": lambda t: t * t,
    "Cubic": lambda t: t ** 3,
    "Quart": lambda t: t ** 4,
    "Quint": lambda t: t ** 5,
    "Expo": lambda t: 0.0 if t == 0 else 2 ** (10 * t - 10),
    "Circ": lambda t: 1 - math.sqrt(max(0.0, 1 - t * t)),
    "Back": lambda t: 2.70158 * t ** 3 - 1.70158 * t * t,
    "Elastic": lambda t: float(t) if t in (0, 1) else -(2 ** (10 * t - 10)) * math.sin((t * 10 - 10.75) * (2 * math.pi) / 3),
    "Bounce": lambda t: 1 - _bounce_out(1 - t),
}
EASINGS = {"linear": lambda t: t, "step": lambda t: 0.0 if t < 1 else 1.0}
for _n, _f in _BASE_IN.items():
    EASINGS["easeIn" + _n] = _f
    EASINGS["easeOut" + _n] = (lambda f: (lambda t: 1 - f(1 - t)))(_f)
    EASINGS["easeInOut" + _n] = _in_out(_f)


# ---- authoring --------------------------------------------------------------------------------------
class Anim:
    def __init__(self, name, length, loop=False, desc="", category=""):
        self.name = name
        self.length = float(length)
        self.loop = loop          # True, False or "hold_on_last_frame"
        self.desc = desc
        self.category = category
        self.tracks = {}          # (bone, channel) -> {time: (vector, easing)}
        self.sounds = {}          # time -> sound event id
        self.particles = {}       # time -> (effect id, locator bone)
        self.cues = {}            # time -> instruction string (gameplay hooks: "fire", "impact", ...)

    def key(self, bone, channel, t, vec, ease="easeInOutSine"):
        if channel not in CHANNELS:
            raise ValueError(channel)
        t = round(float(t), 4)
        self.tracks.setdefault((bone, channel), {})[t] = ([float(v) for v in vec], ease)
        return self

    def rot(self, bone, t, x=0, y=0, z=0, ease="easeInOutSine"):
        return self.key(bone, "rotation", t, (x, y, z), ease)

    def pos(self, bone, t, x=0, y=0, z=0, ease="easeInOutSine"):
        return self.key(bone, "position", t, (x, y, z), ease)

    def scl(self, bone, t, x=1, y=1, z=1, ease="easeInOutSine"):
        return self.key(bone, "scale", t, (x, y, z), ease)

    def pose(self, t, spec, ease="easeInOutSine"):
        """spec: {bone: (rx, ry, rz)} or {bone: {"rotation": .., "position": ..}}."""
        for bone, v in spec.items():
            if isinstance(v, dict):
                for ch, vec in v.items():
                    self.key(bone, ch, t, vec, ease)
            else:
                self.rot(bone, t, *v, ease=ease)
        return self

    def sound(self, t, event):
        self.sounds[round(float(t), 4)] = event
        return self

    def particle(self, t, effect, locator):
        self.particles[round(float(t), 4)] = (effect, locator)
        return self

    def cue(self, t, what):
        self.cues[round(float(t), 4)] = what
        return self

    def bones(self):
        return sorted({b for (b, _) in self.tracks})

    # ---- sampling -----------------------------------------------------------------------------
    def sample(self, bone, channel, t):
        tr = self.tracks.get((bone, channel))
        if not tr:
            return None
        times = sorted(tr)
        if t <= times[0]:
            return list(tr[times[0]][0])
        if t >= times[-1]:
            return list(tr[times[-1]][0])
        for i in range(1, len(times)):
            t1 = times[i]
            if t <= t1:
                t0 = times[i - 1]
                a, _ = tr[t0]
                b, ease = tr[t1]
                u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
                e = EASINGS[ease](u)
                return [a[k] + (b[k] - a[k]) * e for k in range(3)]
        return list(tr[times[-1]][0])

    def pose_at(self, t):
        out = {}
        for (bone, ch) in self.tracks:
            out.setdefault(bone, {})[ch] = self.sample(bone, ch, t)
        return out

    # ---- export ---------------------------------------------------------------------------------
    def to_json(self, prefix):
        bones = {}
        for (bone, ch), keys in sorted(self.tracks.items()):
            chan = {}
            for t in sorted(keys):
                vec, ease = keys[t]
                entry = {"vector": [_r(v) for v in vec]}
                if ease != "linear":
                    entry["easing"] = ease
                chan[_fmt(t)] = entry
            bones.setdefault(bone, {})[ch] = chan
        j = {"loop": self.loop, "animation_length": _r(self.length), "bones": bones}
        if self.sounds:
            j["sound_effects"] = {_fmt(t): {"effect": e} for t, e in sorted(self.sounds.items())}
        if self.particles:
            j["particle_effects"] = {_fmt(t): {"effect": e, "locator": loc} for t, (e, loc) in sorted(self.particles.items())}
        if self.cues:
            j["timeline"] = {_fmt(t): c for t, c in sorted(self.cues.items())}
        return prefix + self.name, j


def write_library(path, prefix, anims):
    doc = {"format_version": "1.8.0", "animations": {}}
    for a in anims:
        k, v = a.to_json(prefix)
        if k in doc["animations"]:
            raise ValueError("duplicate animation " + k)
        doc["animations"][k] = v
    with open(path, "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    return doc


def _r(x):
    x = round(float(x), 3)
    return int(x) if x == int(x) else x


def _fmt(t):
    return ("%.4f" % t).rstrip("0").rstrip(".") if t != int(t) else "%d.0" % int(t)


# ---- validation (runs on the exported JSON, independent of the authoring objects) ------------------
def validate(doc, model, linked=None, known_sounds=None, known_particles=None, root_motion=()):
    """Returns a list of problems. Checks what GeckoLib would choke on and what would look broken:
    structure, bone names, keyframe times, easing names, loop seams, joint limits (sampled, not just
    at keys), linked bones, sound/particle ids."""
    problems = []
    if doc.get("format_version") != "1.8.0":
        problems.append("format_version must be 1.8.0")
    anims = doc.get("animations")
    if not isinstance(anims, dict) or not anims:
        return problems + ["no animations"]
    bones = {b.name: b for b in model.bones}
    for name, a in anims.items():
        where = name
        if not name.startswith("animation."):
            problems.append(where + ": name must start with 'animation.'")
        loop = a.get("loop")
        if loop not in (True, False, "hold_on_last_frame"):
            problems.append(where + ": bad loop value %r" % (loop,))
        length = a.get("animation_length")
        if not isinstance(length, (int, float)) or not math.isfinite(length) or length <= 0:
            problems.append(where + ": bad animation_length")
            continue
        tracks = {}
        for bone, chans in a.get("bones", {}).items():
            if bone not in bones:
                problems.append("%s: unknown bone %s" % (where, bone))
                continue
            for ch, keys in chans.items():
                if ch not in CHANNELS:
                    problems.append("%s/%s: unknown channel %s" % (where, bone, ch))
                    continue
                parsed = {}
                for ts, entry in keys.items():
                    try:
                        t = float(ts)
                    except ValueError:
                        problems.append("%s/%s/%s: bad time %r" % (where, bone, ch, ts))
                        continue
                    if not (0 <= t <= length + 1e-6):
                        problems.append("%s/%s/%s: key %.3f outside 0..%.3f" % (where, bone, ch, t, length))
                    vec = entry.get("vector") if isinstance(entry, dict) else entry
                    ease = entry.get("easing", "linear") if isinstance(entry, dict) else "linear"
                    if ease not in EASINGS:
                        problems.append("%s/%s/%s: unknown easing %s" % (where, bone, ch, ease))
                        ease = "linear"
                    if not (isinstance(vec, list) and len(vec) == 3 and all(isinstance(v, (int, float)) and math.isfinite(v) for v in vec)):
                        problems.append("%s/%s/%s @%s: vector must be 3 finite numbers" % (where, bone, ch, ts))
                        continue
                    if t in parsed:
                        problems.append("%s/%s/%s: duplicate key time %s" % (where, bone, ch, ts))
                    parsed[t] = (vec, ease)
                if parsed:
                    tracks[(bone, ch)] = parsed
        # loop seams
        if loop is True:
            for (bone, ch), keys in tracks.items():
                ts = sorted(keys)
                if len(ts) > 1 and (abs(ts[0]) > 1e-6 or abs(ts[-1] - length) > 1e-6 or
                                    any(abs(p - q) > 1e-3 for p, q in zip(keys[ts[0]][0], keys[ts[-1]][0]))):
                    problems.append("%s/%s/%s: looping track must start at 0 and end at the length with the same value" % (where, bone, ch))
        # sampled joint limits
        probe = Anim("probe", length)
        probe.tracks = {k: {t: (v, e) for t, (v, e) in keys.items()} for k, keys in tracks.items()}
        steps = max(8, int(length * 40))
        for (bone, ch) in tracks:
            b = bones[bone]
            for i in range(steps + 1):
                t = length * i / steps
                v = probe.sample(bone, ch, t)
                if ch == "rotation":
                    for k, ax in enumerate("xyz"):
                        lo, hi = b.dof.get(ax, (0.0, 0.0))     # an axis without a declared range is fixed
                        total = b.rotation[k] + v[k]
                        if not (lo - 0.51 <= total <= hi + 0.51):
                            problems.append("%s/%s: rotation %s = %.1f outside %s..%s at t=%.2f" % (where, bone, ax, total, lo, hi, t))
                            break
                    else:
                        continue
                    break
                if ch == "position" and bone not in root_motion and max(abs(c) for c in v) > 4.01:
                    problems.append("%s/%s: position offset %.2f px exceeds 4 px at t=%.2f" % (where, bone, max(abs(c) for c in v), t))
                    break
                if ch == "scale" and min(v) < -1e-9:
                    problems.append("%s/%s: negative scale at t=%.2f" % (where, bone, t))
                    break
        # linked bones (knee copies in the boot parts)
        for dst, src in (linked or {}).items():
            for ch in ("rotation", "position"):
                a_t, b_t = tracks.get((dst, ch)), tracks.get((src, ch))
                if a_t is None and b_t is None:
                    continue
                for i in range(steps + 1):
                    t = length * i / steps
                    va = probe.sample(dst, ch, t) if a_t else [0, 0, 0]
                    vb = probe.sample(src, ch, t) if b_t else [0, 0, 0]
                    if any(abs(p - q) > 1e-3 for p, q in zip(va, vb)):
                        problems.append("%s: %s.%s must equal %s.%s (t=%.2f)" % (where, dst, ch, src, ch, t))
                        break
        for kind, key, known in (("sound_effects", "effect", known_sounds), ("particle_effects", "effect", known_particles)):
            for ts, e in a.get(kind, {}).items():
                if not (0 <= float(ts) <= length + 1e-6):
                    problems.append("%s: %s at %s outside the animation" % (where, kind, ts))
                if known is not None and e.get(key) not in known:
                    problems.append("%s: unknown %s %s" % (where, kind[:-8], e.get(key)))
                if kind == "particle_effects" and e.get("locator") not in bones:
                    problems.append("%s: particle locator %s is not a bone" % (where, e.get("locator")))
    return problems


def to_anim(name, j):
    """Rebuilds a sampler from exported JSON (used for previews of the file as written)."""
    a = Anim(name, j["animation_length"], j.get("loop", False))
    for bone, chans in j.get("bones", {}).items():
        for ch, keys in chans.items():
            for ts, entry in keys.items():
                a.key(bone, ch, float(ts), entry["vector"], entry.get("easing", "linear"))
    return a
