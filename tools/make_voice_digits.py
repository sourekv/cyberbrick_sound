#!/usr/bin/env python3
"""Speaks the digits 0 to 9 with Piper (the same voice as the set names) and writes firmware/data/voice/d0.wav ..
d9.wav and pin.wav (a short beep before the digits), 22 050 Hz, 16 bit, mono, silence trimmed. The module speaks its Bluetooth PIN with them (docs/ble-link.md).
firmware/data/ is generated and git-ignored; `pio run -e engine_sets_ble -t uploadfs` writes it to the data partition.

    python tools/make_voice_digits.py --piper DIR --model ONNX
"""
import argparse, math, os, sys, wave
import numpy as np
from scipy.signal import butter, sosfilt

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_default_sets as m   # piper_name: speaks a text, trims the silence, 10 ms fades, -1 dBFS

def clarify(pcm):
    """For the 40 mm speaker (docs/speaker-measurement.md): it plays nothing useful below about 200 Hz, so the voice sounds
    thin and the consonants are lost. High-pass at 250 Hz, +7 dB presence around 2.5 kHz (RBJ peaking filter), then a
    soft compression (tanh) that lifts the quiet parts, and the peak back to -1 dBFS: louder and clearer at the same peak."""
    x = np.asarray(pcm, dtype=np.float64) / 32768.0
    x = sosfilt(butter(2, 250.0, "highpass", fs=m.RATE, output="sos"), x)
    f0, q, gain_db = 2500.0, 0.9, 7.0
    A = 10 ** (gain_db / 40.0); w0 = 2 * math.pi * f0 / m.RATE; al = math.sin(w0) / (2 * q)
    b = [1 + al * A, -2 * math.cos(w0), 1 - al * A]; a = [1 + al / A, -2 * math.cos(w0), 1 - al / A]
    x = sosfilt([[b[0] / a[0], b[1] / a[0], b[2] / a[0], 1.0, a[1] / a[0], a[2] / a[0]]], x)
    x = x / max(np.max(np.abs(x)), 1e-9)
    g = 3.0
    x = np.tanh(g * x) / math.tanh(g)                      # lifts the quiet parts, flattens the peaks
    x = x * (0.891 / max(np.max(np.abs(x)), 1e-9))
    return np.clip(np.round(x * 32768.0), -32768, 32767).astype(np.int16)


def rms_db(pcm):
    x = np.asarray(pcm, dtype=np.float64) / 32768.0
    return 20 * math.log10(max(math.sqrt(np.mean(x * x)), 1e-9))


WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piper", required=True); ap.add_argument("--model", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "firmware", "data", "voice"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for d, word in enumerate(WORDS):
        raw = m.piper_name(word.capitalize() + ".", a.piper, a.model)
        pcm = clarify(raw)
        with wave.open(os.path.join(a.out, "d%d.wav" % d), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(m.RATE)
            w.writeframes(np.asarray(pcm, dtype="<i2").tobytes())
        print("d%d.wav: %s, %.2f s, level %.1f dB RMS (before %.1f)" % (d, word, len(pcm) / m.RATE, rms_db(pcm), rms_db(raw)))
    n = int(0.22 * m.RATE)                                  # a short beep: 1 kHz, 5 ms attack, soft decay, -1 dBFS
    t = np.arange(n) / m.RATE
    env = np.minimum(1.0, t / 0.005) * np.exp(-t / 0.09)
    pcm = np.round(0.891 * 32768 * env * np.sin(2 * math.pi * 1000.0 * t)).astype(np.int16)
    with wave.open(os.path.join(a.out, "pin.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(m.RATE)
        w.writeframes(np.asarray(pcm, dtype="<i2").tobytes())
    print("pin.wav: %.2f s" % (len(pcm) / m.RATE))


if __name__ == "__main__":
    main()
