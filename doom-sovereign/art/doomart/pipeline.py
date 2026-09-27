"""Shared build steps: pack, validate, paint every state, write files, check the palette."""
import os

from .paint import Painter, to_image, palette_violations


def paint_states(model, decorations, tex_dir, stem, damages, glows, glow_for_damage=True):
    """Writes ``<stem><dmg>.png`` for each damage level and ``<stem><dmg>_glowmask[_state].png``.

    damages: list of (suffix, level); glows: list of states, the one named "powered" is the
    default glow mask (no state suffix). Returns {suffix: (base, {state: glow})} and file names.
    """
    out, files = {}, []
    for suffix, level in damages:
        out[suffix] = [None, {}]
        for glow in glows:
            base, gl = Painter(model, decorations, damage=level, glow=glow).paint()
            if out[suffix][0] is None:
                out[suffix][0] = base
                files.append(stem + suffix + ".png")
                to_image(base).save(os.path.join(tex_dir, files[-1]))
            if level and not glow_for_damage:
                continue
            name = stem + suffix + "_glowmask" + ("" if glow == "powered" else "_" + glow) + ".png"
            to_image(gl).save(os.path.join(tex_dir, name))
            files.append(name)
            out[suffix][1][glow] = gl
        bad = palette_violations(out[suffix][0]) + sum(palette_violations(g) for g in out[suffix][1].values())
        if bad:
            raise SystemExit("%s%s: %d colours outside the palette" % (stem, suffix, bad))
    return out, files


def prepare(model):
    fill = model.pack()
    problems = model.validate()
    if problems:
        raise SystemExit("%s problems:\n  %s" % (model.identifier, "\n  ".join(problems)))
    return fill
