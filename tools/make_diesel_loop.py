#!/usr/bin/env python3
"""Cut a seamless idle loop out of the CC0 diesel recording and write assets/samples/diesel_idle_loop.wav.

Source: https://freesound.org/people/chlund/sounds/500193/  (chlund, CC0)
        "Diesel engine starting revving and stopping", Citroen Jumpy 2010 2.0 HDI, 18.08 s, 44.1 kHz stereo.
The original is not stored in the repository; download it from Freesound and pass its path.

Steps: mono, resample to 22.05 kHz, take the steady idle part (from 4.0 s), search the loop length (1.5..3.2 s)
whose end best continues into its start, and crossfade 50 ms (the loop start blends into the real continuation
of the recording). Normalise to 0.85 of full scale.

Usage: python tools/make_diesel_loop.py path/to/500193__chlund__diesel-engine-starting-revving-and-stopping.wav
Needs numpy and scipy.
"""
import os, sys
import numpy as np
import scipy.io.wavfile as wav
import scipy.signal as sg

OUT = 22050
START_S = 4.0
MATCH_S = 0.25
LOOP_MIN_S, LOOP_MAX_S = 1.5, 3.2
XFADE_S = 0.05
PEAK = 0.85

src = sys.argv[1]
dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "samples", "diesel_idle_loop.wav")

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
