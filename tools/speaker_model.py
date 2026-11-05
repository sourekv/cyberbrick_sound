#!/usr/bin/env python3
"""Approximate "as heard from the speaker" preview, built from the measured speaker response.

Uses docs/measurements/speaker_baseline_2026-11-01.csv (40 mm prototype speaker, phone 5 cm in front):
- the frequency response (relative dB) is applied as a zero-phase filter; below the measured range it is
  held at FLOOR_DB, so bass that the speaker cannot play disappears;
- the strong distortion below about 300 Hz is imitated by adding 2nd and 3rd harmonics of the low band.
  The amounts are set so that a 200 Hz sine at 0.25 of full scale gets about -9 dB 2nd and -15 dB 3rd
  harmonic, as measured; louder bass distorts more, like a real speaker cone at its excursion limit.

This is a listening aid, not a calibrated model: the phone microphone is part of the measurement, and the
distortion model is a rough fit. Compare candidates with it, then confirm on the real speaker.

Library use:  from speaker_model import as_heard;  y = as_heard(x, rate)   (x: numpy float array, -1..1)
Command line: python tools/speaker_model.py in.wav out.wav
Needs numpy.
"""
import csv, os, sys, wave
import numpy as np

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
CSV = os.path.join(ROOT, "docs", "measurements", "speaker_baseline_2026-11-01.csv")
FLOOR_DB = -45.0      # level for frequencies the speaker does not play at all
LOW_SPLIT_HZ = 300.0  # band that distorts
HD2_COEF = 2.84       # 2nd-harmonic term: a*A/2 = 0.355 (-9 dB) at A = 0.25
HD3_COEF = 11.4       # 3rd-harmonic term: b*A^2/4 = 0.178 (-15 dB) at A = 0.25


def _response():
    f, db = [], []
    with open(CSV, newline="") as fh:
        for row in csv.DictReader(fh):
            f.append(float(row["freq_hz"]))
            db.append(max(FLOOR_DB, float(row["response_db"])))
    return np.array(f), np.array(db)


def _magnitude(n_fft, rate):
    f, db = _response()
    grid = np.fft.rfftfreq(n_fft, 1.0 / rate)
    g = np.interp(np.log10(np.maximum(grid, 1.0)), np.log10(f), db, left=FLOOR_DB, right=db[-1])
    above = grid > f[-1]  # above the last point: keep falling about 12 dB per octave
    g[above] = db[-1] - 12.0 * np.log2(grid[above] / f[-1])
    return 10 ** (np.maximum(g, FLOOR_DB) / 20.0)


def _fft_filter(x, mag):
    n = len(mag) * 2 - 2
    return np.fft.irfft(np.fft.rfft(x, n) * mag, n)[: len(x)]


def as_heard(x, rate=22050, distortion=True):
    x = np.asarray(x, dtype=np.float64)
    pad = int(0.25 * rate)
    n_fft = 1 << int(np.ceil(np.log2(len(x) + 2 * pad)))
    xp = np.concatenate([np.zeros(pad), x, np.zeros(n_fft - len(x) - pad)])
    if distortion:
        grid = np.fft.rfftfreq(n_fft, 1.0 / rate)
        low = 1.0 / np.sqrt(1.0 + (grid / LOW_SPLIT_HZ) ** 8)  # 4th-order-like low-pass, zero phase
        xl = _fft_filter(xp, low)
        extra = HD2_COEF * xl ** 2 + HD3_COEF * xl ** 3
        xp = xp + np.tanh(extra)  # the added harmonics cannot grow without limit
    y = _fft_filter(xp, _magnitude(n_fft, rate))
    return y[pad: pad + len(x)]


def read_wav(path):
    w = wave.open(path)
    rate, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
    raw = w.readframes(n)
    w.close()
    if sw != 2:
        raise SystemExit("only 16-bit WAV is supported")
    x = np.frombuffer(raw, "<i2").astype(np.float64) / 32768.0
    return x.reshape(-1, ch).mean(axis=1), rate


def write_wav(path, x, rate):
    d = (np.clip(x, -1.0, 32767 / 32768.0) * 32768.0).astype("<i2")
    w = wave.open(path, "wb")
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(rate)
    w.writeframes(d.tobytes())
    w.close()


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    x, rate = read_wav(sys.argv[1])
    write_wav(sys.argv[2], as_heard(x, rate), rate)
