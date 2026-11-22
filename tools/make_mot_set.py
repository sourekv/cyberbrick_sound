#!/usr/bin/env python3
"""Builds one sound set (docs/user-sounds.md) from the user's old "mot..." recordings (8 bit, 22 050 Hz, mono).

The recordings are of unknown origin, so they are NOT in the repository: the sources are read from a folder given on
the command line (work/mot_src, which is git-ignored), and the finished set is written to another git-ignored folder
(work/mot_set/08_retro). Only this script is committed.

What is made of what (all passed through a 150 Hz high-pass, the 40 mm speaker plays nothing useful below it):
  idle.wav    motidle.wav, a steady 4 s stretch cut to a whole number of its repeat period, the end crossfaded into the
              start (equal power, 150 ms) so that the loop has no seam
  loaded.wav  motcrui1.wav (steady cruise), the same way, about 2.6 s
  start.wav   motstar3.wav, the cranking only (2.0 s, 40 ms fade-out)
  shift.wav   motshup2.wav, the first 0.45 s with a 50 ms fade-out
  horn.wav    copied from the default set 01_truck (the recordings have no horn)
  name.wav    spoken with Piper ("Eight. Retro."), as tools/make_default_sets.py does
Loudness: every file gets the RMS of the same file of the default set 01_truck, the peak is kept below -1 dBFS.

With --layered a second set is built from the same recordings, as a layered set (docs/layers-design.md): three loops
cut at different steady engine speeds (motidle 1.0 s.., motacc1 3.3..4.7 s, motcrui1 4.0..6.2 s) written as layer_1.wav ..
layer_3.wav, with their "ratio" (firing frequency relative to the first layer, measured from the envelope of the raw
recording) in set.json. start and horn are as in the set 08, the shift is the one of the default set 01_truck (CC0), the name is made as above (name "Nine. Layers.").

Usage (from the repo root):
    python tools/make_mot_set.py --src work/mot_src --out work/mot_set [--piper DIR --model ONNX] [--layered]
"""
import argparse, json, os, shutil, sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
RATE = 22050
sys.path.insert(0, os.path.join(ROOT, "tools"))


def load8(path):
    with wave.open(path) as w:
        r, n, sw = w.getframerate(), w.getnframes(), w.getsampwidth()
        raw = w.readframes(n)
    x = (np.frombuffer(raw, np.uint8).astype(np.float64) - 128.0) / 128.0 if sw == 1 else \
        np.frombuffer(raw, "<i2").astype(np.float64) / 32768.0
    if r != RATE:
        x = np.interp(np.arange(int(len(x) * RATE / r)) * r / RATE, np.arange(len(x)), x)
    return x


def read16(path):
    with wave.open(path) as w:
        return np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64) / 32768.0


def write16(path, x):
    d = np.clip(np.round(np.asarray(x) * 32768.0), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(d.tobytes())


def highpass(x, f=150.0):
    return sosfilt(butter(2, f, "highpass", fs=RATE, output="sos"), x)


def rms(x):
    return float(np.sqrt(np.mean(np.square(x))))


def repeat_period(x, lo=0.02, hi=0.5):
    """Strongest repeat period in seconds, by autocorrelation of the envelope-free signal."""
    x = x - x.mean()
    n2 = 1 << (2 * len(x)).bit_length()
    F = np.fft.rfft(x, n2)
    ac = np.fft.irfft(F * np.conj(F))[:len(x)]
    ac /= ac[0]
    a, b = int(lo * RATE), int(hi * RATE)
    return (a + int(np.argmax(ac[a:b]))) / RATE


def firing_frequency(x, win=0.4, hop=0.2, fmin=10.0, fmax=80.0):
    """Median repeat frequency (Hz) of the amplitude envelope of the raw signal, by autocorrelation per window."""
    n = int(win * RATE)
    out = []
    for s0 in range(0, len(x) - n, int(hop * RATE)):
        e = np.abs(x[s0:s0 + n] - x[s0:s0 + n].mean())
        e = e - e.mean()
        n2 = 1 << (2 * len(e)).bit_length()
        F = np.fft.rfft(e, n2)
        ac = np.fft.irfft(F * np.conj(F))[:len(e)]
        ac /= ac[0]
        a, b = int(RATE / fmax), int(RATE / fmin)
        out.append(RATE / (a + int(np.argmax(ac[a:b]))))
    return float(np.median(out))


def make_loop(x, start_s, length_s, period_s, fade_s=0.15):
    k = max(1, round(length_s / period_s))
    L = int(round(k * period_s * RATE))
    X = int(fade_s * RATE)
    s = int(start_s * RATE)
    seg = x[s:s + L + X]
    if len(seg) < L + X:
        raise SystemExit("source too short for the loop")
    out = seg[:L].copy()
    t = np.linspace(0, np.pi / 2, X)
    out[:X] = seg[:X] * np.sin(t) + seg[L:L + X] * np.cos(t)     # equal power: end of the cut fades into its start
    return out, k


def fade_out(x, s):
    n = min(len(x) // 2, int(s * RATE)); y = x.copy(); y[-n:] *= np.linspace(1, 0, n); return y


def level_to(x, target_rms, peak=0.89):
    y = x * (target_rms / max(rms(x), 1e-9))
    p = np.max(np.abs(y))
    return y * (peak / p) if p > peak else y


LAYER_SOURCES = [("motidle.wav", 1.0, 5.0, 3.0), ("motacc1.wav", 3.3, 4.7, 1.0), ("motcrui1.wav", 4.0, 6.2, 1.8)]


def build_layered(a, ref):
    dst = os.path.join(a.out, "09_layers")
    os.makedirs(dst, exist_ok=True)
    layers = []
    for name, t0, t1, length in LAYER_SOURCES:
        raw = load8(os.path.join(a.src, name))
        f = firing_frequency(raw[int(t0 * RATE):int(t1 * RATE)])
        loop, k = make_loop(highpass(raw), t0, length, 1.0 / f, fade_s=0.12)
        layers.append((loop, f))
    base_rms = ref("idle.wav")
    json_layers = []
    for i, (loop, f) in enumerate(layers, 1):
        write16(os.path.join(dst, "layer_%d.wav" % i), level_to(loop, base_rms))
        json_layers.append({"file": "layer_%d.wav" % i, "ratio": round(f / layers[0][1], 3)})
        print("layer %d: %.1f Hz, ratio %.3f, %.2f s" % (i, f, f / layers[0][1], len(loop) / RATE))
    for f in ("start.wav", "horn.wav"):
        shutil.copy(os.path.join(a.out, a.folder, f), os.path.join(dst, f))     # as in the set 08
    shutil.copy(os.path.join(a.ref, "shift.wav"), os.path.join(dst, "shift.wav"))   # the shift of the default set 01_truck (CC0), chosen by the owner
    if a.piper and a.model:
        import make_default_sets as m
        write16(os.path.join(dst, "name.wav"), m.piper_name("Nine. Layers.", a.piper, a.model).astype(np.float64) / 32768.0)
    with open(os.path.join(dst, "set.json"), "w", encoding="utf8") as fh:
        json.dump({"name": "9 - layers", "type": "sample", "rate": [1.0, 3.0], "level": 1.0, "stop_s": 1.4,
                   "gearbox": True, "layers": json_layers, "xfade": 0.36}, fh, indent=1)
    print("written:", dst)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=os.path.join(ROOT, "work", "mot_src"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "mot_set"))
    ap.add_argument("--piper"); ap.add_argument("--model")
    ap.add_argument("--ref", default=os.path.join(ROOT, "firmware", "data", "sets", "01_truck"))
    ap.add_argument("--folder", default="08_retro")
    ap.add_argument("--layered", action="store_true", help="also build the layered variant (needs the set 08 built first or in the same run)")
    a = ap.parse_args()
    dst = os.path.join(a.out, a.folder)
    os.makedirs(dst, exist_ok=True)
    S = lambda f: highpass(load8(os.path.join(a.src, f)))
    ref = lambda f: rms(read16(os.path.join(a.ref, f)))
    report = []

    x = S("motidle.wav")
    p = repeat_period(x[:RATE * 6])
    idle, k = make_loop(x, 1.0, 4.0, p)
    report.append("idle: repeat period %.1f ms, %d periods, %.2f s" % (p * 1000, k, len(idle) / RATE))
    write16(os.path.join(dst, "idle.wav"), level_to(idle, ref("idle.wav")))

    x = S("motcrui1.wav")
    p = repeat_period(x[:RATE * 6])
    loaded, k = make_loop(x, 1.0, 2.6, p)
    report.append("loaded: repeat period %.1f ms, %d periods, %.2f s" % (p * 1000, k, len(loaded) / RATE))
    write16(os.path.join(dst, "loaded.wav"), level_to(loaded, ref("loaded.wav")))

    x = S("motstar3.wav")[:int(2.0 * RATE)]
    write16(os.path.join(dst, "start.wav"), level_to(fade_out(x, 0.04), ref("start.wav")))

    x = S("motshup2.wav")[:int(0.45 * RATE)]
    write16(os.path.join(dst, "shift.wav"), level_to(fade_out(x, 0.05), ref("shift.wav")))

    write16(os.path.join(dst, "horn.wav"), read16(os.path.join(a.ref, "horn.wav")))

    if a.piper and a.model:
        import make_default_sets as m
        write16(os.path.join(dst, "name.wav"), m.piper_name("Eight. Retro.", a.piper, a.model).astype(np.float64) / 32768.0)
        report.append("name: spoken with Piper")
    else:
        report.append("name.wav NOT written (no --piper/--model)")

    with open(os.path.join(dst, "set.json"), "w", encoding="utf8") as f:
        json.dump({"name": "Retro", "type": "sample", "rate": [1.0, 3.0], "loaded_rate_scale": 1.18,
                   "loaded_gain": 0.8, "level": 1.0, "stop_s": 1.4, "gearbox": True}, f, indent=1)
    print("\n".join(report))
    print("written:", dst)
    if a.layered:
        build_layered(a, ref)


if __name__ == "__main__":
    main()
