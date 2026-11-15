#!/usr/bin/env python3
"""Builds a small test sound set for the `engine_sets` firmware and the web page (docs/user-sounds.md): a sample set
made of synthetic sounds that are easy to tell apart, so that writing a set to the module, playing it and the demo can
be checked by ear. Everything is generated here (no recordings, no third-party sound), so the files are ours (MIT).

    python tools/make_test_set.py            writes assets/test_set/08_test/ (about 0.3 MB)

Then on the web page: "Add set" (or Copy), number 8, drop each WAV on its row, "Write to the module". Or copy the
folder to firmware/data/sets/ and run `pio run -e engine_sets -t uploadfs` (this writes all the sets).

What to hear:
  name.wav    three rising beeps (a spoken name needs Piper: make it with the page's Speak button, "Eight. Test.")
  idle.wav    2 s, a slow low "tuk tuk tuk" (12 pulses per second), loops seamlessly
  loaded.wav  1 s, a faster and brighter "trrr" (18 pulses per second), blends in with the throttle
  start.wav   1 s, a slow crank that speeds up (no catch; the engine catches by itself)
  horn.wav    1 s, two tones (392 and 494 Hz), whole periods so it loops cleanly
  shift.wav   0.25 s, a short thump
22 050 Hz, 16 bit, mono, peak -1 dBFS, 10 ms fades where a sound is played once.
"""
import json, os, wave
import numpy as np

RATE = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "test_set", "08_test")
rng = np.random.default_rng(8)


def t(sec):
    return np.arange(int(round(sec * RATE))) / RATE


def norm(x, peak_db=-1.0):
    return x * (10 ** (peak_db / 20) / np.max(np.abs(x)))


def fade(x, ms=10):
    n = int(RATE * ms / 1000)
    x = x.copy(); x[:n] *= np.linspace(0, 1, n); x[-n:] *= np.linspace(1, 0, n)
    return x


def pulses(sec, per_sec, f0, decay, harm=0.0):
    """Exactly sec*per_sec identical decaying bursts, wrapped around, so the loop has no seam."""
    n = int(round(sec * RATE)); out = np.zeros(n)
    k = int(per_sec * sec); burst_t = t(0.12)
    burst = np.exp(-burst_t * decay) * (np.sin(2 * np.pi * f0 * burst_t) + harm * np.sin(2 * np.pi * 3 * f0 * burst_t)
                                        + 0.15 * rng.standard_normal(len(burst_t)))
    for i in range(k):
        s = int(round(i * n / k)); idx = (s + np.arange(len(burst))) % n
        out[idx] += burst
    return out


def wav(name, x):
    pcm = np.round(np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(os.path.join(OUT, name), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE); w.writeframes(pcm.tobytes())


def main():
    os.makedirs(OUT, exist_ok=True)
    wav("idle.wav", norm(pulses(2.0, 12, 70, 28)))
    wav("loaded.wav", norm(pulses(1.0, 18, 110, 30, harm=0.5)))
    # start: a crank that speeds up from 4 to 9 pulses per second, then fades out
    n = int(RATE * 1.0); ph = np.cumsum(np.linspace(4, 9, n)) / RATE
    x = (np.maximum(0, np.sin(2 * np.pi * ph)) ** 6) * np.sin(2 * np.pi * 75 * t(1.0)) * 1.0
    wav("start.wav", norm(fade(x + 0.05 * rng.standard_normal(n))))
    h = t(1.0)
    horn = np.sin(2 * np.pi * 392 * h) + 0.5 * np.sin(2 * np.pi * 3 * 392 * h) \
        + np.sin(2 * np.pi * 494 * h) + 0.5 * np.sin(2 * np.pi * 3 * 494 * h)
    wav("horn.wav", norm(horn))
    s = t(0.25)
    wav("shift.wav", norm(fade(np.exp(-s * 25) * np.sin(2 * np.pi * 190 * s) + 0.3 * np.exp(-s * 60) * rng.standard_normal(len(s)), 5)))
    jingle = np.concatenate([fade(np.sin(2 * np.pi * f * t(0.3)) * np.exp(-t(0.3) * 3)) for f in (523.25, 659.25, 784.0)])
    wav("name.wav", norm(jingle))
    with open(os.path.join(OUT, "set.json"), "w", encoding="utf8") as f:
        json.dump({"name": "Test", "type": "sample", "rate": [1.0, 3.0], "loaded_rate_scale": 1.18, "loaded_gain": 0.8,
                   "level": 1.0, "stop_s": 1.4, "gearbox": True}, f, indent=2)
    tot = 0
    for fn in sorted(os.listdir(OUT)):
        p = os.path.join(OUT, fn); tot += os.path.getsize(p)
        if fn.endswith(".wav"):
            with wave.open(p) as w:
                print(f"{fn:11} {w.getnframes() / w.getframerate():5.2f} s  {w.getframerate()} Hz  {w.getsampwidth() * 8} bit  ch {w.getnchannels()}")
    print("total", tot, "bytes in", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
