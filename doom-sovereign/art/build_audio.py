#!/usr/bin/env python3
"""Synthesizes every DOOM: SOVEREIGN sound from scratch and writes mono 44.1 kHz OGG Vorbis,
sounds.json, subtitles, docs/AUDIO.md data (audio_report.json) and a spectrogram sheet.

    python3 build_audio.py

No samples, recordings, voices or third-party audio: every waveform comes from doomart/synth.py.
Deterministic (fixed seeds) so rebuilding gives the same sounds.
"""
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from doomart.synth import *          # noqa: F401,F403
from doomart import synth as S
from build_armor import ASSETS, PREVIEW

SOUND_DIR = os.path.join(ASSETS, "sounds")
SOUNDS = []   # (event, file stem, fn, family, kind, subtitle, description)

TARGET_RMS = {"one_shot": -16.0, "impact": -14.0, "loop": -22.0, "ui": -19.0}


def sound(event, family, kind, subtitle, desc, variants=1):
    def deco(fn):
        for v in range(variants):
            stem = event.replace(".", "/") + ("" if variants == 1 else "_%d" % (v + 1))
            SOUNDS.append((event, stem, (lambda f, vv: (lambda: f(vv)))(fn, v), family, kind, subtitle, desc))
        return fn
    return deco


def mix(n, *parts):
    out = np.zeros(n)
    for p in parts:
        out[:len(p)] += p[:n]
    return out


def glide(n, f0, f1, curve="exp"):
    u = np.linspace(0, 1, n)
    return f0 * (f1 / f0) ** u if curve == "exp" else f0 + (f1 - f0) * u


# ===================================================================================== technology ===
@sound("mask.lock", "tech", "one_shot", "Mask plates lock", "Twin latch clicks, a short metallic ping and a low thunk")
def _(v):
    n = int(0.35 * SR)
    ping = fm(1850, 1.41, 3 * env_exp(n, 0.05), n) * env_exp(n, 0.08) * 0.5
    thunk = sine(glide(n, 140, 90), n) * env_exp(n, 0.05) * 0.9
    return mix(n, click(n, 0.0, seed=1) * 0.8, click(n, 0.022, seed=2) * 0.6, ping, thunk)


@sound("mask.seal", "tech", "one_shot", "Mask seals", "Pneumatic hiss, a deep clamp, then a rising power-on tone")
def _(v):
    n = int(0.95 * SR)
    t = np.arange(n) / SR
    hiss = bandpass(noise(n, 5), 1800, 7000) * np.clip(np.minimum(t / 0.05, (0.5 - t) / 0.2), 0, 1) * 0.35
    k = int(0.5 * SR)
    clamp = np.zeros(n)
    m = n - k
    clamp[k:] = (sine(glide(m, 95, 58), m) + 0.5 * sine(glide(m, 190, 116), m)) * env_exp(m, 0.12)
    tone = np.zeros(n)
    j = int(0.55 * SR)
    mm = n - j
    tone[j:] = lowpass(saw(glide(mm, 220, 440), mm, 12), 1800) * env_adsr(mm, 0.08, 0.1, 0.7, 0.15) * 0.35
    return mix(n, hiss, clamp, click(n, 0.5, seed=7) * 0.7, tone)


@sound("armor.servo", "tech", "ui", "Armor servos whir", "Pitch-gliding saw whine with a gear-buzz tremolo and a closing tick")
def _(v):
    n = int(0.4 * SR)
    t = np.arange(n) / SR
    f = np.interp(t, [0, 0.15, 0.4], [380, 520, 440])
    w = lowpass(saw(f, n, 16), 2600) * (0.75 + 0.25 * np.sin(2 * np.pi * 60 * t)) * env_adsr(n, 0.02, 0.05, 0.8, 0.1)
    return mix(n, w * 0.6, click(n, 0.36, seed=9) * 0.4)


@sound("armor.step_heavy", "tech", "impact", "Heavy armored footstep", "Low pitched thud, a padded thump and a short plate clank", variants=3)
def _(v):
    n = int(0.45 * SR)
    f0 = (58, 63, 54)[v]
    thud = sine(glide(n, f0 * 1.6, f0), n) * env_exp(n, 0.09)
    thump = lowpass(noise(n, 20 + v), 380) * env_exp(n, 0.05) * 1.4
    clank = fm((640, 760, 700)[v], 2.7, 2 * env_exp(n, 0.04), n) * env_exp(n, 0.06) * 0.25
    grit = highpass(noise(n, 30 + v), 3000) * env_exp(n, 0.02) * 0.08
    return mix(n, thud, thump, clank, grit)


@sound("armor.impact_heavy", "tech", "impact", "Heavy impact", "Sub boom, a low noise blast, a ringing metal body and debris ticks")
def _(v):
    n = int(1.0 * SR)
    boom = sine(glide(n, 80, 42), n) * env_exp(n, 0.35)
    blast = lowpass(noise(n, 41), 900) * env_exp(n, 0.15) * 1.2
    ring = fm(330, 1.93, 4 * env_exp(n, 0.2), n) * env_exp(n, 0.4) * 0.22
    debris = sum(click(n, a, seed=50 + i) * 0.25 for i, a in enumerate((0.12, 0.19, 0.27, 0.41)))
    return reverb(mix(n, boom, blast, ring, debris), 0.8, 0.2)


@sound("armor.shutdown", "tech", "one_shot", "Armor powers down", "Descending whine with a closing filter, a stutter and a final relay click")
def _(v):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = glide(n, 440, 55)
    w = lowpass(saw(f, n, 20), glide(n, 4000, 200)) * env_adsr(n, 0.01, 0.1, 0.9, 0.3)
    w *= np.where(t > 1.1, 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 14 * t)), 1.0)
    return mix(n, w * 0.7, click(n, 1.5, seed=61) * 0.5)


@sound("flight.thruster_ignition", "tech", "one_shot", "Thrusters ignite", "Igniter clicks, a filtered whoomp that opens up, and a settling roar")
def _(v):
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    clicks = sum(click(n, a, seed=70 + i, bright=8000) * 0.5 for i, a in enumerate((0.0, 0.035, 0.07)))
    cutoff = np.interp(t, [0.08, 0.3, 1.2], [200, 3200, 1400])
    roar = lowpass(noise(n, 71), cutoff) * np.interp(t, [0.08, 0.25, 0.6, 1.2], [0, 1.2, 0.7, 0]) * 1.2
    rumble = sine(44, n) * np.interp(t, [0.08, 0.3, 1.2], [0, 1, 0]) * 0.6
    return mix(n, clicks, roar, rumble)


@sound("flight.loop", "tech", "loop", "Thrusters roar", "Seamless roar: filtered noise bands, a 48 Hz rumble breathing at 3 Hz, a faint repulsor whine")
def _(v):
    n = int(3.08 * SR)
    t = np.arange(n) / SR
    roar = lowpass(noise(n, 80), 1200) * 1.0 + bandpass(noise(n, 81), 300, 2500) * 0.5
    rumble = sine(48, n) * (0.8 + 0.2 * np.sin(2 * np.pi * 3 * t)) * 0.7
    whine = sine(880 * (1 + 0.004 * np.sin(2 * np.pi * 5 * t)), n) * 0.05
    return make_loop(mix(n, roar, rumble, whine), 0.08)


@sound("flight.boost", "tech", "one_shot", "Afterburners engage", "A sharp crack, then a roar whose filter and whine climb")
def _(v):
    n = int(1.4 * SR)
    t = np.arange(n) / SR
    crack = highpass(noise(n, 90), 1500) * env_exp(n, 0.03) * 1.0
    roar = lowpass(noise(n, 91), np.interp(t, [0, 1.0, 1.4], [800, 6000, 3000])) * np.interp(t, [0, 0.1, 1.0, 1.4], [0, 1, 0.9, 0])
    whine = sine(glide(n, 900, 1800), n) * np.interp(t, [0, 0.2, 1.2, 1.4], [0, 0.12, 0.1, 0])
    return mix(n, crack, roar, whine)


@sound("gauntlet.charge", "tech", "one_shot", "Gauntlet charges", "Rising FM whine, accelerating capacitor chirps and thickening crackle")
def _(v):
    n = int(1.5 * SR)
    t = np.arange(n) / SR
    car = glide(n, 200, 1600)
    whine = fm(car, 1.5, np.interp(t, [0, 1.5], [1, 3]), n) * np.interp(t, [0, 1.3, 1.5], [0.1, 0.6, 0.4])
    am_rate = glide(n, 8, 40)
    whine *= 0.7 + 0.3 * np.sign(np.sin(phase(am_rate)))
    r = S.rng(100)
    crackle = np.zeros(n)
    for _ in range(90):
        a = r.random() ** 0.6 * 1.45
        crackle += click(n, a, seed=int(r.integers(1e6)), bright=6000) * 0.25 * a / 1.45
    return mix(n, whine, crackle)


@sound("gauntlet.discharge", "tech", "impact", "Gauntlet fires", "Downward FM zap, a bright noise snap and a low punch")
def _(v):
    n = int(0.6 * SR)
    zap = fm(glide(n, 1200, 300), 1.3, 6 * env_exp(n, 0.08), n) * env_exp(n, 0.12) * 0.7
    snap = bandpass(noise(n, 110), 1000, 6000) * env_exp(n, 0.05) * 1.2
    punch = sine(glide(n, 120, 70), n) * env_exp(n, 0.06)
    return mix(n, zap, snap, punch)


@sound("gauntlet.heavy_blast", "tech", "impact", "Heavy gauntlet blast", "A sucking pre-swell, a crack, a falling FM roar, a sub drop and a tail")
def _(v):
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    pre = lowpass(noise(n, 120), 1500) * np.clip((t - 0.0) / 0.15, 0, 1) * (t < 0.15) * 0.6
    k = int(0.15 * SR)
    m = n - k
    body = np.zeros(n)
    body[k:] = (fm(glide(m, 800, 120), 1.41, 5 * env_exp(m, 0.2), m) * env_exp(m, 0.35) * 0.5
                + sine(glide(m, 70, 35), m) * env_exp(m, 0.4)
                + lowpass(noise(m, 121), glide(m, 5000, 300)) * env_exp(m, 0.3) * 0.9)
    return reverb(mix(n, pre, body, click(n, 0.15, seed=122) * 1.0), 1.0, 0.25)


@sound("gauntlet.beam_loop", "tech", "loop", "Beam sustains", "Beating saw drone with a wobbling FM layer and fine crackle, seamless")
def _(v):
    n = int(2.08 * SR)
    t = np.arange(n) / SR
    drone = lowpass(saw(110, n, 30) + saw(110.5, n, 30) * 0.8 + saw(220.7, n, 20) * 0.4, 2500) * 0.5
    wob = fm(660, 1.5, 2 * (0.6 + 0.4 * np.sin(2 * np.pi * 10 * t)), n) * 0.25
    crackle = highpass(noise(n, 130), 4000) * (S.rng(131).random(n) > 0.997) * 2.0
    return make_loop(mix(n, drone, wob, crackle), 0.08)


@sound("field.activate", "tech", "one_shot", "Force field activates", "An upward shimmer sweep and whoosh, locking into a fifth")
def _(v):
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    sweep = fm(glide(n, 150, 900), 2.01, 1.5, n) * np.interp(t, [0, 0.35, 0.45], [0.1, 0.6, 0]) * 0.6
    whoosh = bandpass(noise(n, 140), 400, 4000) * np.interp(t, [0, 0.3, 0.45], [0, 0.8, 0])
    k = int(0.4 * SR)
    m = n - k
    chord = np.zeros(n)
    chord[k:] = (sine(300, m) + 0.7 * sine(450, m) + 0.3 * sine(600, m)) * env_exp(m, 0.3, 0.005) * 0.5
    return mix(n, sweep, whoosh, chord)


@sound("field.hum", "tech", "loop", "Force field hums", "100/200/300 Hz harmonic hum with slow beating and a faint high flutter, seamless")
def _(v):
    n = int(3.08 * SR)
    t = np.arange(n) / SR
    hum = (sine(100, n) + 0.5 * sine(200.33, n) + 0.3 * sine(300, n)) * (0.85 + 0.15 * np.sin(2 * np.pi * 0.667 * t))
    flutter = sine(3000, n) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t)) * 0.02
    return make_loop(mix(n, hum * 0.5, flutter), 0.08)


@sound("field.impact", "tech", "impact", "Force field absorbs a hit", "A dull falling 'bwomm' with FM ripple, a padded thump and a brief ring")
def _(v):
    n = int(0.5 * SR)
    bwomm = fm(glide(n, 180, 120), 0.5, 1.2 * env_exp(n, 0.1), n) * env_exp(n, 0.18)
    thump = lowpass(noise(n, 150), 1500) * env_exp(n, 0.03) * 0.8
    ring = sine(1200, n) * env_exp(n, 0.15) * 0.1
    return mix(n, bwomm, thump, ring)


@sound("field.collapse", "tech", "impact", "Force field collapses", "A bright shatter, a stuttering FM fall, glassy crackle and a low drop")
def _(v):
    n = int(1.3 * SR)
    t = np.arange(n) / SR
    shatter = highpass(noise(n, 160), 2500) * env_exp(n, 0.08) * 0.9
    fall = fm(glide(n, 900, 80), 1.7, 3, n) * env_exp(n, 0.5) * (0.6 + 0.4 * np.sign(np.sin(2 * np.pi * 18 * t))) * 0.4
    r = S.rng(161)
    crackle = sum(click(n, float(r.random() * 0.9), seed=int(r.integers(1e6)), bright=9000) * 0.3 for _ in range(25))
    drop = sine(glide(n, 90, 40), n) * env_exp(n, 0.3) * 0.8
    return mix(n, shatter, fall, crackle, drop)


@sound("scan.pulse", "tech", "ui", "Scanner pulses", "A chirp under a 1320 Hz blip with two filtered echoes")
def _(v):
    n = int(0.8 * SR)
    out = np.zeros(n)
    blip_n = int(0.04 * SR)
    for delay, g in ((0.0, 1.0), (0.18, 0.4), (0.36, 0.16)):
        b = sine(1320, blip_n) * env_adsr(blip_n, 0.002, 0.01, 0.6, 0.015) * g
        i = int(delay * SR)
        out[i:i + blip_n] += lowpass(b, 6000 if delay == 0 else 2500)
    cn = int(0.1 * SR)
    out[:cn] += sine(glide(cn, 600, 2400), cn) * env_adsr(cn, 0.005, 0.02, 0.5, 0.03) * 0.3
    return out


@sound("tech.override", "tech", "ui", "Systems overridden", "Rapid data-chatter blips from a fixed pitch set, then a rising two-tone confirm")
def _(v):
    n = int(1.0 * SR)
    out = np.zeros(n)
    r = S.rng(170)
    pitches = [800, 960, 1200, 1440, 1600, 1920, 2400]
    bn = int(0.028 * SR)
    for k in range(20):
        i = int(k * 0.03 * SR)
        f = pitches[int(r.integers(len(pitches)))]
        out[i:i + bn] += np.sign(sine(f, bn)) * env_adsr(bn, 0.001, 0.005, 0.5, 0.008) * 0.25
    for f, a in ((880, 0.7), (1320, 0.82)):
        m = int(0.12 * SR)
        i = int(a * SR)
        out[i:i + m] += sine(f, m) * env_adsr(m, 0.003, 0.02, 0.7, 0.05) * 0.6
    return lowpass(out, 7000)


@sound("doombot.servo", "tech", "ui", "Doombot servos grind", "Lower, heavier servo than the armor, with a 90 Hz gear buzz and a hydraulic puff")
def _(v):
    n = int(0.35 * SR)
    t = np.arange(n) / SR
    f = np.interp(t, [0, 0.12, 0.35], [180, 260, 200])
    w = lowpass(saw(f, n, 20), 1800) * (0.7 + 0.3 * np.sin(2 * np.pi * 90 * t)) * env_adsr(n, 0.01, 0.05, 0.8, 0.08)
    puff = bandpass(noise(n, 180), 2000, 7000) * env_exp(n, 0.04) * 0.2
    return mix(n, w * 0.7, puff)


@sound("doombot.step_heavy", "tech", "impact", "Doombot footstep", "Deeper thud than the armor, a brighter clank and a hydraulic hiss tail", variants=3)
def _(v):
    n = int(0.5 * SR)
    f0 = (48, 52, 45)[v]
    thud = sine(glide(n, f0 * 1.7, f0), n) * env_exp(n, 0.1)
    clank = fm((420, 470, 390)[v], 3.1, 2.5 * env_exp(n, 0.05), n) * env_exp(n, 0.08) * 0.35
    hiss = bandpass(noise(n, 190 + v), 2500, 8000) * np.clip(np.arange(n) / SR / 0.05, 0, 1) * env_exp(n, 0.12) * 0.12
    return mix(n, thud, lowpass(noise(n, 195 + v), 300) * env_exp(n, 0.05), clank, hiss)


@sound("doombot.diagnostic", "tech", "ui", "Doombot chirps", "Three ring-modulated FM beeps: the acknowledge pattern")
def _(v):
    n = int(0.9 * SR)
    out = np.zeros(n)
    for f, a in ((1000, 0.0), (1500, 0.18), (1250, 0.36)):
        m = int(0.14 * SR)
        i = int(a * SR)
        b = fm(f, 0.5, 1.5, m) * np.sin(2 * np.pi * 70 * np.arange(m) / SR) * env_adsr(m, 0.004, 0.03, 0.6, 0.05)
        out[i:i + m] += b * 0.6
    return out


@sound("doombot.shutdown", "tech", "one_shot", "Doombot shuts down", "Power-down whine from 600 to 40 Hz, relay clunks and a dying reactor hum")
def _(v):
    n = int(1.4 * SR)
    whine = lowpass(saw(glide(n, 600, 40), n, 20), glide(n, 3000, 150)) * env_adsr(n, 0.01, 0.1, 0.9, 0.2) * 0.6
    hum = (sine(100, n) + 0.4 * sine(200, n)) * np.linspace(0.4, 0, n)
    return mix(n, whine, hum, click(n, 0.05, seed=200) * 0.6, click(n, 1.2, seed=201) * 0.6)


@sound("time_platform.charge", "tech", "one_shot", "Time Platform charges", "A deep drone opening upward, accelerating pulses and a rising shimmer with phasing")
def _(v):
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    drone = lowpass(saw(glide(n, 40, 160), n, 30), glide(n, 200, 3000)) * np.interp(t, [0, 2.5, 3.0], [0.2, 1, 0.6])
    pulses = 0.6 + 0.4 * np.sign(np.sin(phase(glide(n, 4, 16))))
    shimmer = (sine(glide(n, 1200, 2400), n) + sine(glide(n, 1206, 2412), n)) * np.interp(t, [0, 3.0], [0, 0.12])
    return mix(n, drone * pulses * 0.7, shimmer)


@sound("time_platform.discharge", "tech", "impact", "Time Platform discharges", "A crack and sub drop, followed by the charge heard backwards: time folding")
def _(v):
    n = int(2.0 * SR)
    t = np.arange(n) / SR
    crack = highpass(noise(n, 210), 1200) * env_exp(n, 0.04)
    sub = sine(glide(n, 70, 30), n) * env_exp(n, 0.5)
    m = int(1.2 * SR)
    rev = lowpass(saw(glide(m, 40, 160), m, 20), glide(m, 200, 2500))[::-1] * np.linspace(0, 0.6, m)[::-1] * np.linspace(1, 0, m)
    tail = np.zeros(n)
    tail[int(0.6 * SR):int(0.6 * SR) + m] = rev[:n - int(0.6 * SR)]
    return reverb(mix(n, crack, sub, tail), 1.5, 0.25)


# ======================================================================================== sorcery ===
@sound("sorcery.arcane_cast", "sorcery", "one_shot", "Spell cast", "A reversed bell swell into a just-intonation chime cluster over an airy breath")
def _(v):
    n = int(1.4 * SR)
    sw_n = int(0.3 * SR)
    swell = bell(660, sw_n, tau=0.2)[::-1] * 0.5
    out = np.zeros(n)
    out[:sw_n] += swell
    k = sw_n
    m = n - k
    chime = (bell(660, m, tau=0.9) + 0.7 * bell(990, m, tau=0.8) + 0.5 * bell(1320, m, tau=0.7)) * 0.4
    shimmer = choir(1320, m, (1, 3 / 2, 2), 0.003, 7) * env_exp(m, 0.6, 0.05) * 0.08
    out[k:] += chime + shimmer
    breath = lowpass(noise(n, 220), 3000) * np.interp(np.arange(n) / SR, [0, 0.3, 0.6, 1.4], [0, 0.12, 0.05, 0])
    return reverb(out + breath, 1.8, 0.35)


@sound("sorcery.ritual_resonance", "sorcery", "loop", "Ritual circle resonates", "Slow-beating just-intonation drone on 110 Hz with swelling partials and two bell strikes, seamless")
def _(v):
    n = int(4.08 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for k, (ratio, rate) in enumerate(((1, 0.25), (3 / 2, 0.5), (2, 0.75), (5 / 2, 0.5), (3, 0.25))):
        amp = (0.6 + 0.4 * np.sin(2 * np.pi * rate * t + k)) / (1 + 0.5 * k)
        out += (sine(110 * ratio, n) + sine(110 * ratio * 1.0025, n)) * amp * 0.5
    for a in (0.0, 2.0):
        i = int(a * SR)
        m = n - i
        out[i:] += bell(440, m, tau=1.0)[:m] * 0.2
    air = lowpass(noise(n, 230), 1500) * 0.03
    return make_loop(out + air, 0.08)


@sound("sorcery.teleport", "sorcery", "one_shot", "Sorcerous teleport", "An inward airy rush, a rising pop, then a descending bell arpeggio in a long tail")
def _(v):
    n = int(1.3 * SR)
    t = np.arange(n) / SR
    rush = lowpass(noise(n, 240), 2000) * np.interp(t, [0, 0.4, 0.42], [0, 0.6, 0])
    pn = int(0.06 * SR)
    pop = np.zeros(n)
    i = int(0.4 * SR)
    pop[i:i + pn] = sine(glide(pn, 500, 1400), pn) * env_adsr(pn, 0.002, 0.02, 0.4, 0.02)
    arp = np.zeros(n)
    for f, a in ((1760, 0.45), (1320, 0.52), (990, 0.59)):
        j = int(a * SR)
        m = n - j
        arp[j:] += bell(f, m, tau=0.7) * 0.3
    return reverb(rush + pop + arp, 2.0, 0.4)


# ========================================================================================== build ===
def spectrogram(x, h=96, w=240):
    nfft = 1024
    hop = max(1, (len(x) - nfft) // w)
    frames = []
    win = np.hanning(nfft)
    for k in range(w):
        seg = x[k * hop:k * hop + nfft]
        if len(seg) < nfft:
            seg = np.pad(seg, (0, nfft - len(seg)))
        frames.append(np.abs(np.fft.rfft(seg * win)))
    s = np.array(frames).T                                     # freq x time
    freqs = np.fft.rfftfreq(nfft, 1 / SR)
    edges = np.geomspace(40, 16000, h + 1)                     # log frequency axis
    rows = []
    for a, b in zip(edges[:-1], edges[1:]):
        m = (freqs >= a) & (freqs < b)
        rows.append(s[m].mean(axis=0) if m.any() else np.zeros(w))
    img = 20 * np.log10(np.array(rows)[::-1] + 1e-9)
    img = np.clip((img - img.max() + 70) / 70, 0, 1)
    return img


def build():
    from PIL import Image, ImageDraw
    os.makedirs(SOUND_DIR, exist_ok=True)
    sounds_json, report, subtitles, cells = {}, [], {}, []
    for event, stem, fn, family, kind, subtitle, desc in SOUNDS:
        x = np.asarray(fn(), float)
        x = S.fade(x, 0.001, 0.0 if kind == "loop" else 0.01)
        x = S.normalize(x, -2.0, TARGET_RMS[kind])   # 2 dB headroom: Vorbis overshoots peaks by up to ~0.8 dB
        path = os.path.join(SOUND_DIR, stem + ".ogg")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        sf.write(path, x.astype(np.float32), SR, format="OGG", subtype="VORBIS")
        y, sr = sf.read(path)
        st = S.stats(y)
        st.update({"event": "doom_sovereign:" + event, "file": "sounds/" + stem + ".ogg", "family": family, "kind": kind,
                   "target_rms_dbfs": TARGET_RMS[kind], "sample_rate": sr, "channels": 1 if y.ndim == 1 else y.shape[1],
                   "description": desc})
        if kind == "loop":
            # seam step relative to this loop's typical sample-to-sample step (1.0 = indistinguishable)
            typical = float(np.percentile(np.abs(np.diff(y)), 99)) + 1e-12
            st["loop_seam_ratio"] = round(float(abs(y[0] - y[-1])) / typical, 3)
        report.append(st)
        e = sounds_json.setdefault(event, {"sounds": [], "subtitle": "subtitles.doom_sovereign." + event})
        e["sounds"].append({"name": "doom_sovereign:" + stem, "stream": kind == "loop"})
        subtitles["subtitles.doom_sovereign." + event] = subtitle
        if stem.endswith("_2") or stem.endswith("_3"):
            continue
        img = spectrogram(y)
        tint = np.array((101, 232, 107)) if family == "sorcery" else np.array((150, 170, 175))
        rgb = (img[..., None] * tint).astype(np.uint8)
        cell = Image.new("RGB", (240, 112), (18, 20, 22))
        cell.paste(Image.fromarray(rgb, "RGB"), (0, 0))
        ImageDraw.Draw(cell).text((2, 98), "%s  %.2fs" % (event, st["duration_s"]), fill=(200, 205, 200))
        cells.append(cell)
    with open(os.path.join(ASSETS, "sounds.json"), "w") as f:
        json.dump(sounds_json, f, indent=1)
        f.write("\n")
    with open(os.path.join(HERE, "audio_report.json"), "w") as f:
        json.dump(report, f, indent=1)
        f.write("\n")
    with open(os.path.join(HERE, "subtitles_en_us.json"), "w") as f:
        json.dump(subtitles, f, indent=1)
        f.write("\n")
    cols = 4
    sheet = Image.new("RGB", (cols * 244 + 4, ((len(cells) + cols - 1) // cols) * 116 + 4), (10, 11, 12))
    for k, c in enumerate(cells):
        sheet.paste(c, (4 + (k % cols) * 244, 4 + (k // cols) * 116))
    sheet.save(os.path.join(PREVIEW, "audio_spectrograms.png"))
    bad = [r for r in report if r["clipped"] or r["peak_dbfs"] > -1.0 or abs(r["dc"]) > 0.01
           or r.get("loop_seam_ratio", 0) > 1.0 or r["channels"] != 1]
    print("audio: %d files for %d events, %d problems" % (len(report), len(sounds_json), len(bad)))
    for r in bad:
        print("  ", r)
    return report


if __name__ == "__main__":
    build()
