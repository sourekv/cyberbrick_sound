#!/usr/bin/env python3
"""Speaks the digits 0 to 9 with Piper (the same voice as the set names) and writes firmware/data/voice/d0.wav ..
d9.wav, 22 050 Hz, 16 bit, mono, silence trimmed. The module speaks its Bluetooth PIN with them (docs/ble-link.md).
firmware/data/ is generated and git-ignored; `pio run -e engine_sets_ble -t uploadfs` writes it to the data partition.

    python tools/make_voice_digits.py --piper DIR --model ONNX
"""
import argparse, os, sys, wave
import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import make_default_sets as m   # piper_name: speaks a text, trims the silence, 10 ms fades, -1 dBFS

WORDS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piper", required=True); ap.add_argument("--model", required=True)
    ap.add_argument("--out", default=os.path.join(ROOT, "firmware", "data", "voice"))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    for d, word in enumerate(WORDS):
        pcm = m.piper_name(word.capitalize() + ".", a.piper, a.model)
        with wave.open(os.path.join(a.out, "d%d.wav" % d), "wb") as w:
            w.setnchannels(1); w.setsampwidth(2); w.setframerate(m.RATE)
            w.writeframes(np.asarray(pcm, dtype="<i2").tobytes())
        print("d%d.wav: %s, %.2f s" % (d, word, len(pcm) / m.RATE))


if __name__ == "__main__":
    main()
