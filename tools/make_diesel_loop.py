#!/usr/bin/env python3
"""Cut a seamless idle loop out of a recording of a steady engine and write it as a 22.05 kHz mono WAV.

Used so far (originals are not stored in the repository, download them from Freesound):
  Citroen diesel: https://freesound.org/people/chlund/sounds/500193/ (CC0)
      python tools/make_diesel_loop.py 500193__chlund__...wav assets/samples/diesel_idle_loop.wav
      (defaults: --start 4.0 --min 1.5 --max 3.2)

Steps: mono, resample to 22.05 kHz, take the steady part from --start, search the loop length (--min..--max seconds)
whose end best continues into its start, and crossfade 50 ms (the loop start blends into the real continuation
of the recording). Normalise to 0.85 of full scale.

Usage: python tools/make_diesel_loop.py input.wav output.wav [--start S] [--min SECONDS] [--max SECONDS]
Needs numpy and scipy.
"""
import argparse
import os, sys
import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as sg

OUT = 22050
ap = argparse.ArgumentParser()
ap.add_argument("src"); ap.add_argument("dst")
ap.add_argument("--start", type=float, default=4.0)
ap.add_argument("--min", type=float, default=1.5)
ap.add_argument("--max", type=float, default=3.2)
args = ap.parse_args()
START_S = args.start
MATCH_S = 0.25
LOOP_MIN_S, LOOP_MAX_S = args.min, args.max
XFADE_S = 0.05
PEAK = 0.85

src, dst = args.src, args.dst

sr, x = wav.read(src)
x = x.astype(float)
if x.ndim > 1:
    x = x.mean(axis=1)
x /= np.abs(x).max()
x = sg.resample_poly(x, OUT, sr)

s = int(START_S * OUT)
w = int(MATCH_S * OUT)
seg = x[s:s + w]
best = (-2.0, 0)
for n in range(int(LOOP_MIN_S * OUT), int(LOOP_MAX_S * OUT)):
    cand = x[s + n:s + n + w]
    c = float(np.dot(seg, cand) / (np.linalg.norm(seg) * np.linalg.norm(cand) + 1e-9))
    if c > best[0]:
        best = (c, n)
corr, n = best

loop = x[s:s + n].copy()
xf = int(XFADE_S * OUT)
fade = np.linspace(0.0, 1.0, xf)
loop[:xf] = loop[:xf] * fade + x[s + n:s + n + xf] * (1.0 - fade)
loop -= loop.mean()
loop *= PEAK / np.abs(loop).max()
wav.write(dst, OUT, (loop * 32767).astype(np.int16))
print("wrote %s: %d samples (%.3f s), seam match %.2f" % (dst, len(loop), len(loop) / OUT, corr))
