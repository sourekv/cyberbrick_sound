#!/usr/bin/env python3
"""Engine sound lab: renders engine-sound candidates offline, raw and "as heard" from the measured speaker.

Every candidate is driven by the same 20 s throttle profile (the one used by the other preview tools), so they
can be compared directly. The "as heard" versions go through tools/speaker_model.py and are normalised to the
same loudness, so the comparison is about the character of the sound, not its level.

Candidates:
  truck          the current `engine_truck` firmware (CC0 truck loops, virtual gearbox), as it plays today
  truck_eq       the same with the speaker EQ (see SPEAKER_EQ below) in front of the speaker
  pulse_old      the current `engine_pulse` firmware (synthesised grains, preset a_diesel6)
  diesel, petrol4, v8
                 new speaker-tuned grain synth (Synth2): fixed-timbre combustion grains made from a firing pulse
                 through exhaust-like resonances that sit where the speaker plays (300 Hz .. 4 kHz), combustion
                 noise synchronous with the firing, and the speaker EQ; RPM from the virtual gearbox

Usage: python tools/engine_lab.py OUT_DIR [candidate ...]     (default: all)
Needs numpy. Pure-Python sample loops: a few seconds per candidate.
"""
import math, os, re, sys, wave
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from speaker_model import as_heard, write_wav  # noqa: E402

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
RATE = 22050
BLOCK = 128
SECONDS = 20.0
MASTER_VOLUME = 0.6

# ---------------------------------------------------------------- shared pieces (mirror the firmware)

PROFILE = [(0, 0), (2, 0), (5, 1.0), (7, 1.0), (10, 0.0), (11, 0.0), (11.4, 0.8), (11.9, 0.0), (12.4, 0.8),
           (12.9, 0.0), (14, 0.0), (14.1, 0.5), (16.5, 0.5), (18, 0.0), (20, 0.0)]


def throttle_at(t):
    for (t0, a), (t1, b) in zip(PROFILE, PROFILE[1:]):
        if t0 <= t <= t1:
            return a + (b - a) * (t - t0) / (t1 - t0) if t1 > t0 else b
    return 0.0


class Gearbox:  # firmware/include/gearbox.h with the defaults from config.h
    COUNT, DROP, CUT_S, CUT_GAIN, ACCEL_S, DECEL_S = 5, 0.55, 0.25, 0.15, 6.0, 8.0

    def __init__(self):
        self.rpm, self.gain, self.speed, self.gear, self.cut = 0.0, 1.0, 0.0, 0, 0.0

    def update(self, thr, dt):
        shifting = self.cut > 0
        if shifting:
            self.cut -= dt
        if thr > self.speed:
            if not shifting:
                self.speed = min(thr, self.speed + dt / self.ACCEL_S)
        else:
            self.speed = max(thr, self.speed - dt / self.DECEL_S)
        band = 1.0 / self.COUNT
        if not shifting:
            if self.gear < self.COUNT - 1 and self.speed >= (self.gear + 1) * band:
                self.gear += 1; self.cut = self.CUT_S; shifting = True
            elif self.gear > 0 and self.speed < self.gear * band - 0.04:
                self.gear -= 1
        pos = min(1.0, max(0.0, (self.speed - self.gear * band) / band))
        lo = 0.0 if self.gear == 0 else self.DROP
        target = lo + (1 - lo) * pos
        self.rpm += (target - self.rpm) * min(1.0, dt * (12.0 if shifting else 6.0))
        self.gain += ((self.CUT_GAIN if shifting else 1.0) - self.gain) * min(1.0, dt * 40.0)


def biquad(kind, f0, q, gain_db=0.0, fs=RATE):
    """RBJ audio-EQ-cookbook biquad, normalised (b0, b1, b2, a1, a2)."""
    w = 2 * math.pi * f0 / fs
    al = math.sin(w) / (2 * q)
    c = math.cos(w)
    if kind == "hp":
        b = [(1 + c) / 2, -(1 + c), (1 + c) / 2]; a = [1 + al, -2 * c, 1 - al]
    elif kind == "bp":
        b = [al, 0.0, -al]; a = [1 + al, -2 * c, 1 - al]
    elif kind == "peak":
        A = 10 ** (gain_db / 40)
        b = [1 + al * A, -2 * c, 1 - al * A]; a = [1 + al / A, -2 * c, 1 - al / A]
    else:
        raise ValueError(kind)
    return [b[0] / a[0], b[1] / a[0], b[2] / a[0], a[1] / a[0], a[2] / a[0]]


# Speaker EQ, from the measurements (docs/speaker-measurement.md).
# Bare speaker (2026-11-01): 4th-order high-pass at 260 Hz (keeps the energy away from where the cone distorts and
# plays nothing), -7 dB at the 450 Hz resonance, +4 dB in the 2-3 kHz dip.
SPEAKER_EQ_BARE = [biquad("hp", 260, 0.5412), biquad("hp", 260, 1.3066),
                   biquad("peak", 450, 1.2, -7.0), biquad("peak", 2500, 0.9, 4.0)]
# Speaker in the 30 ml sealed box (2026-11-07), fitted to the measurement (flat within about +-2 dB from 200 Hz to
# 5 kHz): 4th-order high-pass at 140 Hz (the box lets the speaker play down to about 120 Hz), -15 dB at the 420 Hz
# box resonance plus -6 dB at 315 Hz for its lower flank, +5 dB at 5.3 kHz where the box lost some top.
# BOX_EQ_GAIN brings the level back after the cuts (same peak level as with the bare-speaker EQ).
BOX_EQ_GAIN = 1.15
SPEAKER_EQ_BOX = [biquad("hp", 140, 0.5412), biquad("hp", 140, 1.3066),
                  biquad("peak", 420, 1.6, -15.0), biquad("peak", 315, 1.3, -6.0), biquad("peak", 5300, 2.4, 5.0)]
SPEAKER_EQ_BOX[0] = [c * BOX_EQ_GAIN for c in SPEAKER_EQ_BOX[0][:3]] + SPEAKER_EQ_BOX[0][3:]
SPEAKER_EQ = SPEAKER_EQ_BOX


class Chain:
    def __init__(self, coefs):
        self.c = coefs
        self.z = [[0.0, 0.0] for _ in coefs]

    def __call__(self, x):  # transposed direct form II, like the firmware will do it
        for (b0, b1, b2, a1, a2), z in zip(self.c, self.z):
            y = b0 * x + z[0]
            z[0] = b1 * x - a1 * y + z[1]
            z[1] = b2 * x - a2 * y
            x = y
        return x


class Rng:  # xorshift32, as in engine_synth.h
    def __init__(self, seed=0x1234567):
        self.s = seed

    def __call__(self):  # -1..1
        s = self.s
        s ^= (s << 13) & 0xFFFFFFFF; s ^= s >> 17; s ^= (s << 5) & 0xFFFFFFFF
        self.s = s
        return (s - (1 << 32) if s >= (1 << 31) else s) / 2147483648.0


def run(engine):
    """engine.block(throttle) once per BLOCK samples, engine.sample() -> float in -1..1 (before MASTER_VOLUME)."""
    n_total = int(SECONDS * RATE)
    out = np.zeros(n_total)
    for n in range(0, n_total, BLOCK):
        engine.block(throttle_at(n / RATE))
        for i in range(n, min(n + BLOCK, n_total)):
            out[i] = engine.sample()
    return np.clip(out * MASTER_VOLUME, -1.0, 1.0)


# ---------------------------------------------------------------- current firmware: engine_truck

def load_wav(name):
    w = wave.open(os.path.join(ROOT, "assets", "samples", name))
    d = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64)
    w.close()
    return d


class TruckEngine:  # firmware/src/engine/main.cpp with ENGINE_TRUCK
    def __init__(self, eq=False):
        self.idle, self.loaded = load_wav("truck_idle_loop.wav"), load_wav("truck_loaded_loop.wav")
        self.pos = self.pos_l = 0.0
        self.load = 0.0
        self.gb = Gearbox()
        self.prev_gain = 1.0
        self.eq = Chain(SPEAKER_EQ) if eq else None
        self.buf, self.i = [], 0

    @staticmethod
    def _play(d, pos, rate):
        idx = int(pos); fr = pos - idx; nx = idx + 1 if idx + 1 < len(d) else 0
        s = d[idx] + (d[nx] - d[idx]) * fr
        pos += rate
        if pos >= len(d):
            pos -= len(d)
        return s, pos

    def block(self, thr):
        self.gb.update(thr, BLOCK / RATE)
        rpm, gain = self.gb.rpm, self.gb.gain
        rate = 1.0 + 2.0 * rpm
        vol = 0.55 + 0.45 * rpm
        self.load += (thr - self.load) * 0.04
        wi, wl = math.cos(self.load * math.pi / 2), math.sin(self.load * math.pi / 2)
        self.buf = []
        for i in range(BLOCK):
            a, self.pos = self._play(self.idle, self.pos, rate)
            b, self.pos_l = self._play(self.loaded, self.pos_l, rate * 1.18)
            g = self.prev_gain + (gain - self.prev_gain) * (i + 1) / BLOCK
            s = (wi * a + wl * 0.8 * b) * vol * g / 32768.0
            if self.eq:
                s = self.eq(s) * 1.6   # EQ removes energy; 1.6 brings the level back (checked in the analysis)
            self.buf.append(s)
        self.prev_gain = gain
        self.i = 0

    def sample(self):
        s = self.buf[self.i]; self.i += 1
        return s


# ---------------------------------------------------------------- current firmware: engine_pulse (a_diesel6)

def load_old_grains():
    h = open(os.path.join(ROOT, "firmware", "include", "engine_grains.h")).read()
    length = int(re.search(r"#define GRAIN_LEN (\d+)", h).group(1))
    out = {}
    for name in ("GRAIN_BASE", "GRAIN_BRIGHT"):
        body = h.split(name)[1].split("};")[0]
        nums = [int(v) for v in re.findall(r"-?\d+", body.split("= {", 1)[1])]
        out[name] = [np.array(nums[i:i + length]) / 32768.0 for i in range(0, len(nums), length)]
    return out["GRAIN_BASE"], out["GRAIN_BRIGHT"]


class OldPulse:  # firmware/include/engine_synth.h, unchanged
    def __init__(self):
        self.base, self.bright = load_old_grains()
        self.rpm = self.load = 0.0
        self.voices = []
        self.countdown, self.fire, self.gain, self.noise, self.cyl = 1.0, 30.0, 0.55, 0.0, 0
        self.rnd = Rng()

    def block(self, thr):
        self.rpm += (thr - self.rpm) * (0.02 if thr > self.rpm else 0.008)
        self.load = min(1.0, 0.35 * thr + 3.0 * max(0.0, thr - self.rpm))
        self.fire = 30.0 + 70.0 * self.rpm
        self.gain = (0.55 + 0.45 * self.rpm) * 5.0

    def _start(self, g, amp):
        if len(self.voices) >= 8:
            self.voices.sort(key=lambda v: -v[1]); self.voices.pop(0)
        self.voices.append([g, 0, amp])

    def sample(self):
        self.countdown -= 1
        if self.countdown <= 0:
            pat = (1.0, 0.82, 0.95, 0.78, 1.0, 0.88)[self.cyl % 6]; self.cyl += 1
            amp = (1 + (pat - 1) * (0.15 + 0.85 * (1 - self.rpm))) * (0.92 + 0.16 * (0.5 + 0.5 * self.rnd()))
            var = int((0.5 + 0.5 * self.rnd()) * 4) % 4
            self._start(self.base[var], amp * (1 - 0.35 * self.load))
            if self.load > 0.05:
                self._start(self.bright[var], amp * self.load * 0.9)
            self.countdown += RATE / self.fire * (1 + (0.02 + 0.10 * (1 - self.rpm)) * self.rnd())
        s = 0.0
        for v in self.voices:
            s += v[2] * v[0][v[1]]; v[1] += 1
        self.voices = [v for v in self.voices if v[1] < len(v[0])]
        self.noise += 0.30 * (self.rnd() - self.noise)
        s += self.noise * (0.03 + 0.16 * self.rpm * self.rpm)
        s *= self.gain * 0.55
        return s / (1 + abs(s))


# ---------------------------------------------------------------- new: speaker-tuned grain synth

def make_grains(formants, length, pulse_ms, noise, decay_mul, seed, variants=4):
    """Firing pulse (half-sine pressure pulse + short noise burst) through parallel 2-pole resonators."""
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(variants):
        w = max(2, int(pulse_ms * 1e-3 * RATE))
        exc = np.zeros(length)
        exc[:w] = np.sin(np.pi * np.arange(w) / w)
        burst = rng.uniform(-1, 1, length) * np.exp(-np.arange(length) / (0.0012 * RATE))
        exc += noise * burst
        g = np.zeros(length)
        for f, bw, amp in formants:
            f *= 1 + rng.uniform(-0.04, 0.04)          # each variant slightly different
            r = math.exp(-math.pi * bw / decay_mul / RATE)
            c1, c2 = 2 * r * math.cos(2 * math.pi * f / RATE), -r * r
            y1 = y2 = 0.0
            for n in range(length):
                y = exc[n] + c1 * y1 + c2 * y2
                g[n] += amp * y * (1 - r)
                y2, y1 = y1, y
        g *= np.minimum(1.0, (np.arange(length) + 1) / 6.0)        # no click at the start
        fade = 64
        g[-fade:] *= np.linspace(1, 0, fade)                       # ends at zero
        out.append(0.9 * g / np.max(np.abs(g)))
    return out


PRESETS = {
    # big diesel: low firing rate, dark but kept above 300 Hz, uneven 6-cylinder idle
    "diesel": dict(fire=(28.0, 105.0), length=520, pulse_ms=1.6, noise=0.35, decay=1.0,
                   base=[(340, 110, 0.7), (640, 140, 1.0), (1050, 200, 0.85), (1650, 300, 0.55), (2500, 450, 0.3)],
                   bright=[(900, 250, 0.5), (1600, 300, 0.9), (2600, 450, 0.8), (3600, 600, 0.5)],
                   amp_pattern=(1.0, 0.8, 0.95, 0.75, 1.0, 0.85), time_pattern=(0, 0, 0, 0, 0, 0),
                   noise_level=(0.10, 0.45), noise_bp=(1800, 0.7), noise_tau_ms=3.0, out_gain=4.0),
    # petrol 4-cylinder: higher firing rate range, brighter, smoother
    "petrol4": dict(fire=(26.0, 190.0), length=420, pulse_ms=1.0, noise=0.25, decay=1.0,
                    base=[(480, 140, 0.8), (900, 180, 1.0), (1450, 240, 0.8), (2200, 350, 0.55), (3300, 500, 0.3)],
                    bright=[(1300, 300, 0.6), (2300, 350, 0.9), (3400, 500, 0.8), (4500, 700, 0.4)],
                    amp_pattern=(1.0, 0.9, 0.97, 0.88), time_pattern=(0, 0, 0, 0),
                    noise_level=(0.06, 0.35), noise_bp=(2600, 0.8), noise_tau_ms=2.0, out_gain=3.5),
    # V8 (cross-plane): uneven firing per bank gives the "burble"; longer ringing exhaust
    "v8": dict(fire=(36.0, 150.0), length=560, pulse_ms=1.4, noise=0.3, decay=0.8,
               base=[(320, 100, 0.8), (560, 120, 1.0), (900, 170, 0.85), (1400, 260, 0.5), (2100, 400, 0.3)],
               bright=[(800, 220, 0.5), (1400, 280, 0.9), (2300, 420, 0.8), (3300, 600, 0.5)],
               amp_pattern=(1.0, 0.65, 0.9, 0.6, 1.0, 0.7, 0.85, 0.62), time_pattern=(0.10, -0.08, 0.06, -0.10, 0.08, -0.06, 0.10, -0.10),
               noise_level=(0.08, 0.40), noise_bp=(1500, 0.7), noise_tau_ms=3.5, out_gain=3.6),
    # V12: six even firings per revolution (60 deg), so the pulses blend into a smooth, higher howl; short, bright
    # grains so they do not smear at up to 270 firings/s (about 2700 rpm); almost no unevenness
    "v12": dict(fire=(60.0, 270.0), length=260, pulse_ms=0.8, noise=0.22, decay=1.0,
                base=[(420, 130, 0.7), (780, 160, 1.0), (1250, 220, 0.9), (1900, 320, 0.6), (2900, 480, 0.35)],
                bright=[(1500, 300, 0.6), (2600, 380, 0.9), (3700, 520, 0.8), (5000, 700, 0.4)],
                amp_pattern=(1.0, 0.95, 0.98, 0.94, 1.0, 0.96), time_pattern=(0, 0, 0, 0, 0, 0),
                noise_level=(0.05, 0.30), noise_bp=(2800, 0.8), noise_tau_ms=1.5, out_gain=2.8),
}


class Synth2:
    def __init__(self, p):
        self.p = p
        self.base = make_grains(p["base"], p["length"], p["pulse_ms"], p["noise"], p["decay"], 1)
        self.bright = make_grains(p["bright"], p["length"], p["pulse_ms"] * 0.6, p["noise"] * 2, p["decay"], 2)
        self.gb = Gearbox()
        self.voices = []
        self.countdown, self.cyl, self.env = 1.0, 0, 0.0
        self.rnd = Rng()
        self.nbp = Chain([biquad("bp", *p["noise_bp"])])
        self.eq = Chain(SPEAKER_EQ)
        self.env_k = math.exp(-1.0 / (p["noise_tau_ms"] * 1e-3 * RATE))
        self.rpm = self.load = 0.0
        self.fire, self.vol = p["fire"][0], 0.55

    def block(self, thr):
        self.gb.update(thr, BLOCK / RATE)
        self.rpm = self.gb.rpm
        self.load = min(1.0, 0.3 * thr + 2.5 * max(0.0, thr - self.gb.speed))
        lo, hi = self.p["fire"]
        self.fire = lo + (hi - lo) * self.rpm
        self.vol = (0.55 + 0.45 * self.rpm) * self.gb.gain * self.p["out_gain"]

    def _start(self, g, amp):
        if len(self.voices) >= 8:
            self.voices.sort(key=lambda v: -v[1]); self.voices.pop(0)
        self.voices.append([g, 0, amp])

    def sample(self):
        p = self.p
        self.countdown -= 1
        if self.countdown <= 0:
            k = self.cyl % len(p["amp_pattern"]); self.cyl += 1
            uneven = 0.2 + 0.8 * (1 - self.rpm)
            amp = (1 + (p["amp_pattern"][k] - 1) * uneven) * (0.93 + 0.07 * self.rnd())
            var = int((0.5 + 0.5 * self.rnd()) * 4) % 4
            self._start(self.base[var], amp * (1 - 0.4 * self.load))
            if self.load > 0.05:
                self._start(self.bright[var], amp * self.load)
            self.env = amp
            period = RATE / self.fire
            self.countdown += period * (1 + p["time_pattern"][k] * uneven + (0.01 + 0.05 * (1 - self.rpm)) * self.rnd())
        s = 0.0
        for v in self.voices:
            s += v[2] * v[0][v[1]]; v[1] += 1
        self.voices = [v for v in self.voices if v[1] < len(v[0])]
        nl0, nl1 = p["noise_level"]
        s += self.nbp(self.rnd()) * self.env * (nl0 + nl1 * self.rpm + 0.5 * nl1 * self.load)
        self.env *= self.env_k
        # soft clip first, then the EQ: a clipper creates difference tones at the firing rate (30..190 Hz), which
        # the speaker cannot play and only distorts; the EQ after it removes them
        s *= self.vol
        s = s / (1 + abs(s))
        return self.eq(s) * 0.8


CANDIDATES = {
    "truck": lambda: TruckEngine(eq=False),
    "truck_eq": lambda: TruckEngine(eq=True),
    "pulse_old": OldPulse,
    "diesel": lambda: Synth2(PRESETS["diesel"]),
    "petrol4": lambda: Synth2(PRESETS["petrol4"]),
    "v8": lambda: Synth2(PRESETS["v8"]),
    "v12": lambda: Synth2(PRESETS["v12"]),
}

TARGET_RMS = 0.10  # loudness of the "as heard" previews (all the same)


def main():
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    out_dir = sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    names = sys.argv[2:] or list(CANDIDATES)
    for name in names:
        raw = run(CANDIDATES[name]())
        heard = as_heard(raw, RATE)
        k = TARGET_RMS / max(1e-9, float(np.sqrt(np.mean(heard ** 2))))
        write_wav(os.path.join(out_dir, name + "_raw.wav"), raw, RATE)
        write_wav(os.path.join(out_dir, name + "_as_heard.wav"), heard * k, RATE)
        spec = np.abs(np.fft.rfft(raw)) ** 2
        f = np.fft.rfftfreq(len(raw), 1 / RATE)
        below = spec[f < 250].sum() / spec.sum()
        print("%-10s raw rms %.3f peak %.2f  energy below 250 Hz %4.1f %%  as-heard gain x%.2f"
              % (name, np.sqrt(np.mean(raw ** 2)), np.max(np.abs(raw)), 100 * below, k))


if __name__ == "__main__":
    main()
