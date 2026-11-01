#!/usr/bin/env python3
"""Analyse a phone recording of the `speaker_sweep` firmware: frequency response, noise floor and distortion.

Usage: python tools/analyze_speaker_sweep.py recording.(wav|m4a|mp3|...) [--out PREFIX]
       [--f0 100] [--f1 10000] [--seconds 30] [--runs 3]       (defaults match firmware/src/speaker_sweep)

How it works: the known sweep is used as a matched filter to find where every sweep starts in the recording
(independent of when the phone started recording). For every moment of the sweep the level around the expected
frequency (+-10 %) is measured with a 0.25 s Hann window, plus the level at 2x and 3x that frequency (harmonic
distortion). The runs are combined by the median, the result is smoothed to 1/6 octave and shown relative to
the median level between 1 and 3 kHz. The silence before the first sweep gives the noise floor.

What it does NOT remove: the response of the phone microphone and of the room. Keep the microphone at the same
spot (for example 5 cm in front of the speaker, on its axis) and record in a quiet room; the result is the
speaker plus phone microphone, which is good enough for judging where the speaker plays nothing.
Output: PREFIX.csv, PREFIX.png and a summary on the screen. Needs numpy, scipy, matplotlib and ffmpeg.
"""
import argparse
import subprocess
import sys

import numpy as np
from scipy import signal

FS = 48000


def load(path):
    cmd = ["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(FS), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def reference_sweep(f0, f1, secs):
    n = int(secs * FS)
    t = np.arange(n) / FS
    r = f1 / f0
    return np.sin(2 * np.pi * f0 * secs / np.log(r) * (r ** (t / secs) - 1.0))


PAD = 8 * FS      # zeros in front of the recording: a sweep that started before the recording can still be located


def find_starts(rec, ref, runs, secs):
    corr = signal.fftconvolve(rec, ref[::-1], mode="valid")
    env = np.abs(corr)
    env = np.convolve(env, np.ones(int(0.005 * FS)) / int(0.005 * FS), mode="same")
    peaks, _ = signal.find_peaks(env, height=0.12 * env.max(), distance=int(0.8 * secs * FS))
    peaks = peaks[np.argsort(env[peaks])[::-1][:runs]]
    return np.sort(peaks), env


def band_peak(seg, win, f, nfft=1 << 16, rel=0.10):
    """Amplitude of the strongest spectral line within +-rel of f (0 if outside the usable range)."""
    if f * (1 + rel) > 0.45 * FS:
        return np.nan
    spec = np.abs(np.fft.rfft(seg * win, nfft)) * 2.0 / win.sum()
    lo, hi = int(f * (1 - rel) * nfft / FS), int(f * (1 + rel) * nfft / FS) + 1
    return spec[lo:hi].max()


def measure(rec, start, f0, f1, secs, step=0.1, win_s=0.25):
    L = int(win_s * FS)
    win = np.hanning(L)
    r = f1 / f0
    rows = []
    for tc in np.arange(0.3, secs - 0.3, step):
        f = f0 * r ** (tc / secs)
        a = start + int(tc * FS) - L // 2
        if a < 0 or a + L > len(rec):
            continue
        seg = rec[a:a + L]
        rows.append((f, band_peak(seg, win, f), band_peak(seg, win, 2 * f), band_peak(seg, win, 3 * f)))
    return np.array(rows)


def noise_curve(rec, starts, f0, f1, secs, step=0.1, win_s=0.25):
    """Same measurement on a silent part: 2.5 s .. 0.3 s before the first sweep, else after the end of the last one."""
    L = int(win_s * FS)
    win = np.hanning(L)
    a0, a1 = starts[0] - int(2.5 * FS), starts[0] - int(0.3 * FS)
    if a0 < PAD:
        a0, a1 = starts[-1] + int((secs + 0.7) * FS), starts[-1] + int((secs + 2.7) * FS)
    quiet = rec[max(a0, 0):max(min(a1, len(rec)), 0)]
    if len(quiet) < 2 * L:
        return None
    r = f1 / f0
    out = []
    for tc in np.arange(0.3, secs - 0.3, step):
        f = f0 * r ** (tc / secs)
        vals = [band_peak(quiet[i:i + L], win, f) for i in range(0, len(quiet) - L, L // 2)]
        out.append((f, np.nanmedian(vals)))
    return np.array(out)


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-12))


def smooth_log(freq, vals, grid):
    """Median of vals in +-1/12 octave around every grid frequency."""
    out = np.full(len(grid), np.nan)
    for i, g in enumerate(grid):
        m = (freq > g * 2 ** (-1 / 12)) & (freq < g * 2 ** (1 / 12)) & np.isfinite(vals)
        if m.any():
            out[i] = np.median(vals[m])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("recording")
    ap.add_argument("--out", default="speaker_response")
    ap.add_argument("--f0", type=float, default=100.0)
    ap.add_argument("--f1", type=float, default=10000.0)
    ap.add_argument("--seconds", type=float, default=30.0)
    ap.add_argument("--runs", type=int, default=3)
    a = ap.parse_args()

    rec = load(a.recording)
    print(f"recording: {len(rec) / FS:.1f} s, peak {np.abs(rec).max():.3f} of full scale")
    clips = np.abs(rec).max() > 0.98
    rec = np.concatenate([np.zeros(PAD), rec])
    if clips:
        print("WARNING: the recording clips, lower the phone input level (or move the phone away) and record again")
    ref = reference_sweep(a.f0, a.f1, a.seconds)
    starts, env = find_starts(rec, ref, a.runs, a.seconds)
    if len(starts) == 0:
        sys.exit("no sweep found in the recording (too quiet, or wrong --f0/--f1/--seconds?)")
    print("sweeps found starting at", ", ".join(f"{(s - PAD) / FS:.1f} s" for s in starts), f"({len(starts)} of {a.runs}; a negative start means the recording began during the sweep)")

    runs = [measure(rec, s, a.f0, a.f1, a.seconds) for s in starts]
    grid = a.f0 * 2 ** (np.arange(0, np.log2(a.f1 / a.f0) * 12 - 1) / 12)
    # every run on the common grid first (a run may start or end outside the recording), then the median of the runs
    resp = np.nanmedian([smooth_log(r[:, 0], db(r[:, 1]), grid) for r in runs], axis=0)
    ref_level = np.nanmedian(resp[(grid >= 1000) & (grid <= 3000)])
    rel = resp - ref_level
    hd2 = np.nanmedian([smooth_log(r[:, 0], db(r[:, 2]) - db(r[:, 1]), grid) for r in runs], axis=0)
    hd3 = np.nanmedian([smooth_log(r[:, 0], db(r[:, 3]) - db(r[:, 1]), grid) for r in runs], axis=0)
    noise = noise_curve(rec, starts, a.f0, a.f1, a.seconds)
    if noise is not None:
        nz = smooth_log(noise[:, 0], db(noise[:, 1]), grid) - ref_level
    else:
        nz = np.full(len(grid), np.nan)
        print("note: no silent part long enough in the recording, the noise floor is not shown")
    snr = rel - nz

    # summary
    print(f"\nreference level (median 1-3 kHz): {ref_level:.1f} dBFS in the recording = 0 dB below")
    for drop in (3, 6, 10, 20):
        ok = np.nonzero(rel >= -drop)[0]
        if len(ok):
            print(f"  within -{drop:2d} dB from {grid[ok[0]]:6.0f} Hz up to {grid[ok[-1]]:6.0f} Hz")
    m = (grid >= 400) & (grid <= 8000)
    print(f"  in 400..8000 Hz: strongest peak {np.nanmax(rel[m]):+.1f} dB at {grid[m][np.nanargmax(rel[m])]:.0f} Hz, "
          f"deepest dip {np.nanmin(rel[m]):+.1f} dB at {grid[m][np.nanargmin(rel[m])]:.0f} Hz")
    for f in (200, 300, 500, 1000, 2000):
        i = int(np.argmin(np.abs(grid - f)))
        print(f"  {grid[i]:6.0f} Hz: {rel[i]:+6.1f} dB   2nd harmonic {hd2[i]:+6.1f} dB   3rd {hd3[i]:+6.1f} dB   signal above noise {snr[i]:5.1f} dB")
    bad = grid[(snr < 15) & np.isfinite(snr)]
    if len(bad):
        print(f"  less than 15 dB above the room noise at: {', '.join(f'{b:.0f}' for b in bad[:12])}{' ...' if len(bad) > 12 else ''} Hz "
              "(values there are not reliable)")

    with open(a.out + ".csv", "w") as f:
        f.write("freq_hz,response_db,noise_db,hd2_db,hd3_db\n")
        for i, g in enumerate(grid):
            f.write(f"{g:.1f},{rel[i]:.2f},{nz[i]:.2f},{hd2[i]:.2f},{hd3[i]:.2f}\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(2, 1, figsize=(10, 8), sharex=True)
    ax[0].semilogx(grid, rel, "C0", lw=2, label="speaker + phone microphone")
    ax[0].semilogx(grid, nz, "0.6", lw=1, label="room noise")
    for d in (3, 6, 10):
        ax[0].axhline(-d, color="C3", lw=0.6, ls=":")
        ax[0].text(grid[-1], -d, f" -{d} dB", va="center", fontsize=8, color="C3")
    ax[0].set_ylabel("dB relative to 1-3 kHz"); ax[0].grid(alpha=.3, which="both"); ax[0].legend(); ax[0].set_ylim(-60, 15)
    ax[0].set_title("Frequency response (recorded)")
    ax[1].semilogx(grid, hd2, label="2nd harmonic"); ax[1].semilogx(grid, hd3, label="3rd harmonic")
    ax[1].set_ylabel("dB below the fundamental"); ax[1].set_xlabel("Hz"); ax[1].grid(alpha=.3, which="both"); ax[1].legend()
    plt.tight_layout(); plt.savefig(a.out + ".png", dpi=100)
    print(f"\nwritten {a.out}.csv and {a.out}.png")


if __name__ == "__main__":
    main()
