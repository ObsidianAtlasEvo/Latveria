"""Hero mask animations (item display / Armor Cradle / equip cut-in). AWAITING RUNTIME VALIDATION."""
from .anim import Anim

PREFIX = "animation.doom_mask."


def build():
    out = []
    a = Anim("lock", 1.4, "hold_on_last_frame", "Plates close: brow drops, cheeks clamp, jaw seals, eyes ignite", "mask")
    a.rot("brow", 0, -22).rot("cheek_r", 0, 0, -45).rot("cheek_l", 0, 0, 45).rot("jaw", 0, 26)
    a.pos("jaw", 0, 0, -1.5, 0.5).scl("eye_glow", 0, 0, 0, 0)
    a.rot("brow", 0.2, -22).rot("brow", 0.32, 0, ease="easeOutBounce")
    a.rot("cheek_r", 0.4, 0, -45).rot("cheek_l", 0.4, 0, 45)
    a.rot("cheek_r", 0.55, 0, 0, 0, "easeOutBack").rot("cheek_l", 0.55, 0, 0, 0, "easeOutBack")
    a.rot("jaw", 0.65, 26).pos("jaw", 0.65, 0, -1.5, 0.5)
    a.rot("jaw", 0.82, 0, ease="easeOutExpo").pos("jaw", 0.82, 0, 0, 0, "easeOutExpo")
    a.rot("mask_root", 0, 0).rot("mask_root", 0.82, 0).rot("mask_root", 0.9, 4, ease="easeOutQuad").rot("mask_root", 1.1, 0)
    a.scl("eye_glow", 0.95, 0, 0, 0).scl("eye_glow", 1.08, 1.3, 1.3, 1.3, "easeOutExpo").scl("eye_glow", 1.25, 1, 1, 1)
    a.sound(0.3, "doom_sovereign:mask.lock").sound(0.53, "doom_sovereign:mask.lock").sound(0.8, "doom_sovereign:mask.seal")
    a.cue(0.82, "sealed").cue(1.0, "eyes_lit")
    out.append(a)
    b = Anim("display_idle", 8.0, True, "Slow turntable with a breathing glow", "mask")
    for t, y in ((0, -20), (4, 20), (8, -20)):
        b.rot("mask_root", t, 0, y, 0)
    for t, s in ((0, 1), (2, 1.12), (4, 1), (6, 1.12), (8, 1)):
        b.scl("eye_glow", t, s, s, s)
    out.append(b)
    c = Anim("power_down", 1.2, "hold_on_last_frame", "Eyes gutter out; the jaw unlatches", "mask")
    c.scl("eye_glow", 0, 1, 1, 1).scl("eye_glow", 0.3, 0.5, 0.5, 0.5, "step").scl("eye_glow", 0.4, 0.9, 0.9, 0.9, "step")
    c.scl("eye_glow", 1.0, 0, 0, 0, "easeInQuad")
    c.rot("jaw", 0, 0).rot("jaw", 0.9, 0).rot("jaw", 1.2, 8, ease="easeOutBounce")
    c.sound(0.0, "doom_sovereign:armor.shutdown")
    out.append(c)
    return out
