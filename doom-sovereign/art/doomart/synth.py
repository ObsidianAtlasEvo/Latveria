"""Tiny deterministic synthesis toolkit for the original DOOM: SOVEREIGN sounds.

Everything is generated from oscillators, filtered noise and envelopes: no samples, recordings,
voices or third-party audio are used anywhere. Two vocabularies keep technology and sorcery apart:

  technology: filtered noise bursts, FM metal, servo whines (pitch-gliding saw/pulse), hard
              transients, mains-like hum at 50/100 Hz multiples, clicks.
  sorcery:    stacks of pure sine partials in just intonation, inharmonic bell partials, slow
              beating drones, reversed swells, airy breath noise (never harsh), long tails.
"""
import numpy as np

SR = 44100


def t_axis(dur):
    return np.arange(int(round(dur * SR))) / SR


def rng(seed):
    return np.random.default_rng(seed)


def env_adsr(n, a=0.005, d=0.05, s=0.6, r=0.1):
    t = np.arange(n) / SR
    dur = n / SR
    e = np.ones(n) * s
    e[t < a] = t[t < a] / max(a, 1e-9)
    m = (t >= a) & (t < a + d)
    e[m] = 1 - (1 - s) * (t[m] - a) / max(d, 1e-9)
    rm = t > dur - r
    e[rm] *= np.clip((dur - t[rm]) / max(r, 1e-9), 0, 1)
    return e


def env_exp(n, tau, attack=0.002):
    t = np.arange(n) / SR
    e = np.exp(-t / tau)
    if attack > 0:
        e *= np.clip(t / attack, 0, 1)
    return e


def lowpass(x, fc):
    """One-pole low-pass, fc may be an array (per-sample cutoff)."""
    fc = np.broadcast_to(np.asarray(fc, float), x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def highpass(x, fc):
    return x - lowpass(x, fc)


def bandpass(x, lo, hi):
    return lowpass(highpass(x, lo), hi)


def biquad_bp(x, f0, q):
    """Resonant band-pass (RBJ cookbook), static centre frequency."""
    w0 = 2 * np.pi * f0 / SR
    alpha = np.sin(w0) / (2 * q)
    b0, b1, b2 = alpha, 0.0, -alpha
    a0, a1, a2 = 1 + alpha, -2 * np.cos(w0), 1 - alpha
    b0, b1, b2, a1, a2 = b0 / a0, b1 / a0, b2 / a0, a1 / a0, a2 / a0
    y = np.zeros_like(x)
    x1 = x2 = y1 = y2 = 0.0
    for i, xi in enumerate(x):
        yi = b0 * xi + b1 * x1 + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1, y2, y1 = x1, xi, y1, yi
        y[i] = yi
    return y


def phase(freq):
    """Integrates an instantaneous frequency (Hz, scalar or array) into phase (radians)."""
    f = np.asarray(freq, float)
    return 2 * np.pi * np.cumsum(f) / SR


def sine(freq, n=None):
    if np.ndim(freq) == 0:
        freq = np.full(n, float(freq))
    return np.sin(phase(freq))


def saw(freq, n=None, harmonics=24):
    if np.ndim(freq) == 0:
        freq = np.full(n, float(freq))
    ph = phase(freq)
    out = np.zeros_like(ph)
    nyq = SR / 2
    for k in range(1, harmonics + 1):
        out += np.where(freq * k < nyq, np.sin(k * ph) / k, 0.0)
    return out * (2 / np.pi)


def fm(carrier, ratio, index, n):
    """Two-operator FM; index may be an array (envelope)."""
    if np.ndim(carrier) == 0:
        carrier = np.full(n, float(carrier))
    mod = np.sin(phase(carrier * ratio))
    return np.sin(phase(carrier) + np.asarray(index) * mod)


def noise(n, seed):
    return rng(seed).standard_normal(n)


def click(n, at, width=0.0015, seed=1, bright=6000):
    out = np.zeros(n)
    i = int(at * SR)
    w = int(width * SR)
    if i >= n:
        return out
    seg = noise(min(w * 8, n - i), seed) * env_exp(min(w * 8, n - i), width)
    out[i:i + len(seg)] += highpass(seg, bright * 0.2)
    return out


def bell(f0, n, partials=((1, 1), (2.76, 0.5), (5.4, 0.25), (8.93, 0.12)), tau=1.2):
    """Inharmonic bell/chime partials (sorcery)."""
    out = np.zeros(n)
    for ratio, amp in partials:
        out += amp * sine(f0 * ratio, n) * env_exp(n, tau / ratio ** 0.5, 0.003)
    return out


def choir(f0, n, ratios=(1, 5 / 4, 3 / 2, 2, 5 / 2), detune=0.004, seed=3):
    """Stack of just-intonation sines with slow detune beating (sorcery)."""
    out = np.zeros(n)
    r = rng(seed)
    for k, ratio in enumerate(ratios):
        for d in (-detune, detune):
            f = f0 * ratio * (1 + d + 0.001 * r.standard_normal())
            out += sine(f, n) / (1 + k * 0.6)
    return out


def reverb(x, decay=1.2, mix=0.25, seed=11):
    """Cheap diffuse tail: a few comb filters with noisy delays (deterministic)."""
    out = x.copy()
    r = rng(seed)
    for d in (0.0297, 0.0371, 0.0411, 0.0437):
        d = d * (1 + 0.05 * r.standard_normal())
        k = int(d * SR)
        g = 10 ** (-3 * d / decay)
        y = np.copy(x)
        for i in range(k, len(y)):
            y[i] += g * y[i - k]
        out += mix * y / 4
    return out


def fade(x, fin=0.002, fout=0.02):
    n = len(x)
    a, b = int(fin * SR), int(fout * SR)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def make_loop(x, xfade=0.08):
    """Seamless loop: crossfade the tail into the head (equal power)."""
    k = int(xfade * SR)
    head, tail = x[:k].copy(), x[-k:].copy()
    w = np.linspace(0, np.pi / 2, k)
    y = x[:-k].copy()
    y[:k] = head * np.sin(w) + tail * np.cos(w)
    # rotate so the seam sits at the quietest, flattest sample: lossy encoders smear the edges
    look = min(len(y) - 1, int(0.5 * SR))
    score = np.abs(y[1:look + 1]) + np.abs(np.diff(y[:look + 1]))
    return np.roll(y, -(int(np.argmin(score)) + 1))


def normalize(x, peak_db=-1.0, rms_db=None):
    x = x - np.mean(x)
    if rms_db is not None:
        rms = np.sqrt(np.mean(x ** 2)) + 1e-12
        x = x * (10 ** (rms_db / 20) / rms)
    pk = np.max(np.abs(x)) + 1e-12
    lim = 10 ** (peak_db / 20)
    if pk > lim:
        x = x * (lim / pk)
    return x


def stats(x):
    pk = float(np.max(np.abs(x)))
    rms = float(np.sqrt(np.mean(x ** 2)))
    return {
        "duration_s": round(len(x) / SR, 3),
        "peak_dbfs": round(20 * np.log10(pk + 1e-12), 2),
        "rms_dbfs": round(20 * np.log10(rms + 1e-12), 2),
        "dc": round(float(np.mean(x)), 5),
        "clipped": int(np.sum(np.abs(x) >= 0.999)),
    }
