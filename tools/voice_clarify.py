"""Makes a spoken clip clearer on the 40 mm speaker (docs/speaker-measurement.md): it plays nothing useful below about 200 Hz,
so a voice sounds thin and the consonants are lost. High-pass at 250 Hz, +7 dB presence around 2.5 kHz (RBJ peaking filter),
a soft compression (tanh) that lifts the quiet parts, and the peak back to -1 dBFS: louder and clearer at the same peak.
The same chain is in web/index.html (`clarifyPcm`), for the names that are recorded or spoken in the page; keep them in step."""
import math
import numpy as np
from scipy.signal import butter, sosfilt

RATE = 22050


def clarify(pcm, rate=RATE):
    x = np.asarray(pcm, dtype=np.float64) / 32768.0
    x = sosfilt(butter(2, 250.0, "highpass", fs=rate, output="sos"), x)
    f0, q, gain_db = 2500.0, 0.9, 7.0
    A = 10 ** (gain_db / 40.0); w0 = 2 * math.pi * f0 / rate; al = math.sin(w0) / (2 * q)
    b = [1 + al * A, -2 * math.cos(w0), 1 - al * A]; a = [1 + al / A, -2 * math.cos(w0), 1 - al / A]
    x = sosfilt([[b[0] / a[0], b[1] / a[0], b[2] / a[0], 1.0, a[1] / a[0], a[2] / a[0]]], x)
    x = x / max(np.max(np.abs(x)), 1e-9)
    g = 3.0
    x = np.tanh(g * x) / math.tanh(g)
    x = x * (0.891 / max(np.max(np.abs(x)), 1e-9))
    return np.clip(np.round(x * 32768.0), -32768, 32767).astype(np.int16)


def rms_db(pcm):
    x = np.asarray(pcm, dtype=np.float64) / 32768.0
    return 20 * math.log10(max(math.sqrt(np.mean(x * x)), 1e-9))
