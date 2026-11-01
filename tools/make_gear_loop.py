#!/usr/bin/env python3
"""Cut a loop out of a recording and write it as a 22.05 kHz mono WAV for the per-gear sample bank.

Unlike tools/make_diesel_loop.py (which searches for a seamless idle loop in a steady recording), this takes the
section you name and makes it loop by blending the last --xfade seconds into the first ones (equal-power
crossfade). That works for noise-like engine recordings (old optical film, constant revs); it will not hide a
changing pitch. The level is set by RMS (--rms, fraction of full scale) so that all gears are equally loud.

Used for the gear bank (originals are not stored in the repository, see assets/samples/LICENSE-SAMPLES.md):
  python tools/make_gear_loop.py 487151__craigsmith__r03-29-large-truck-constant-engine.wav assets/samples/gear_a_r03-29.wav --start 0.6 --end 6.6
  python tools/make_gear_loop.py 487152__craigsmith__r03-32-old-truck-engine-working-hard.wav assets/samples/gear_b_r03-32.wav --start 5 --end 13
then tools/make_engine_diesel.py turns each WAV into a header (see firmware/src/engine_gears/main.cpp).

Usage: python tools/make_gear_loop.py input.wav output.wav [--start S] [--end S] [--xfade SECONDS] [--rms 0.14]
Needs numpy and scipy.
"""
import argparse
from math import gcd
import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as sg

OUT = 22050
ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst")
ap.add_argument("--start", type=float, default=0.0)
ap.add_argument("--end", type=float, default=None)
ap.add_argument("--xfade", type=float, default=1.0)
ap.add_argument("--rms", type=float, default=0.14)
a = ap.parse_args()

fs, x = wav.read(a.src)
x = x.astype(np.float64)
if x.ndim > 1:
    x = x.mean(axis=1)
x /= np.abs(x).max()
end = a.end if a.end is not None else len(x) / fs
x = x[int(a.start * fs):int(end * fs)]
g = gcd(OUT, fs)
x = sg.resample_poly(x, OUT // g, fs // g)
L = int(a.xfade * OUT)
assert 2 * L < len(x), "crossfade longer than half the section"
w = np.linspace(0.0, 1.0, L)
y = x[:len(x) - L].copy()
y[:L] = x[:L] * np.sqrt(w) + x[len(x) - L:] * np.sqrt(1.0 - w)   # the end of the section blends into the start
y -= y.mean()
y *= a.rms / y.std()
peak = np.abs(y).max()
if peak > 0.95:
    y *= 0.95 / peak
wav.write(a.dst, OUT, np.round(y * 32767).astype(np.int16))
print("wrote %s: %.2f s, rms %.3f, peak %.2f" % (a.dst, len(y) / OUT, y.std(), np.abs(y).max()))
