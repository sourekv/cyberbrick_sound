#!/usr/bin/env python3
"""Builds the default sound sets of the `engine_sets` firmware (docs/user-sounds.md) into firmware/data/sets/.

Every folder assets/sets/NN_description/ holds a set.json: the parameters that go to the module, plus "sources",
which says where each WAV comes from. This script writes firmware/data/sets/NN_description/ with the set.json for
the module (without "sources", with the EQ as numbers) and the WAVs, all 22 050 Hz, 16 bit, mono. Then
    pio run -e engine_sets -t uploadfs     (from firmware/)
writes them to the data partition. firmware/data/ is generated and not committed.

Sources:
  a path                 a WAV in the repo (must already be 22 050 Hz, 16 bit, mono; the CC0 loops are)
  "render:starter"       the starter of include/engine_events.h (StarterSound), cranking 1.1 s and the 0.12 s fade
  "render:horn"          the horn of include/engine_events.h (HornSound), 2.0 s of its steady sound: a whole number
                         of periods of both tones and the vibrato, so it loops without a seam (the firmware adds the
                         attack, the pitch bend and the release)
  "header:shift_sound"   the CC0 shift sound of include/shift_sound.h
  name: {"text", "voice_prompt"}
                         with --piper and --model: the text spoken by Piper (the user runs this script, piper.exe is
                         a downloaded binary); without them the prompt of the same number is taken from
                         include/voice_prompts.h (still with the number in front, "One. Truck.") and a note says so

The starter and the horn go through the speaker EQ (LAB_EQ) as in the firmware today, so they sound the same.
The EQ named "speaker_box" in a set.json is LAB_EQ of include/engine_lab_data.h; "eq_gain" is folded into the first
stage.

It also writes web/demo_sets.js, the built sets as base64 for the simulated module of the web page
(web/index.html); generated, not committed. --demo-only writes only that file, from the sets already in
firmware/data/sets/ (keeps names spoken with Piper earlier).

Usage (from the repo root):
    python tools/make_default_sets.py [--piper DIR --model ONNX] [--demo-only]
"""
import argparse, base64, json, math, os, re, shutil, subprocess, sys, tempfile, wave
import numpy as np

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
INC = os.path.join(ROOT, "firmware", "include")
SRC = os.path.join(ROOT, "assets", "sets")
OUT = os.path.join(ROOT, "firmware", "data", "sets")
DEMO_JS = os.path.join(ROOT, "web", "demo_sets.js")
RATE = 22050


# ---------------------------------------------------------------- headers of the firmware

def header_array(path, name):
    h = open(path, encoding="utf8").read()
    body = h.split(name + "[", 1)[1].split("= {", 1)[1].split("};", 1)[0]
    return np.array([int(v) for v in re.findall(r"-?\d+", body)], dtype=np.int16)


def lab_eq():
    h = open(os.path.join(INC, "engine_lab_data.h"), encoding="utf8").read()
    body = h.split("LAB_EQ[LAB_EQ_STAGES][5] = {", 1)[1].split("};", 1)[0]
    nums = [float(v) for v in re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", body)]
    return [nums[i:i + 5] for i in range(0, len(nums), 5)]


class Chain:  # transposed direct form II, float32 like the firmware
    def __init__(self, coefs):
        self.c = [[np.float32(v) for v in c] for c in coefs]
        self.z = [[np.float32(0), np.float32(0)] for _ in coefs]

    def __call__(self, x):
        x = np.float32(x)
        for (b0, b1, b2, a1, a2), z in zip(self.c, self.z):
            y = b0 * x + z[0]
            z[0] = b1 * x - a1 * y + z[1]
            z[1] = b2 * x - a2 * y
            x = y
        return x


# ---------------------------------------------------------------- include/engine_events.h, ported

class SawTable:
    N = 512

    def __init__(self, harmonics):
        i = np.arange(self.N)
        t = sum(np.sin(2 * np.pi * k * i / self.N) / k for k in range(1, harmonics + 1))
        self.t = (t / np.max(np.abs(t))).astype(np.float32)

    def at(self, phase):
        x = phase * self.N
        i = int(x); f = x - i; i &= self.N - 1
        return self.t[i] + (self.t[(i + 1) & (self.N - 1)] - self.t[i]) * f


def xorshift(seed):
    while True:
        seed ^= (seed << 13) & 0xFFFFFFFF; seed ^= seed >> 17; seed ^= (seed << 5) & 0xFFFFFFFF
        yield (seed - (1 << 32) if seed >= (1 << 31) else seed) / 2147483648.0


def render_starter(crank_s=1.1):
    saw, eq, rnd = SawTable(14), Chain(lab_eq()), xorshift(0x2468ACE1)
    dt = 1.0 / RATE
    t = ph = stroke = 0.0
    fade, stopping, out = 1.0, False, []
    while True:
        t += dt
        if not stopping and t >= crank_s:
            stopping = True
        stroke_hz = 7.5 + 2.0 * min(t / 0.6, 1.0)
        stroke += stroke_hz * dt
        if stroke >= 1.0: stroke -= 1.0
        squeeze = 0.5 + 0.5 * math.cos(2 * math.pi * stroke)
        f0 = (150.0 + 40.0 * min(t / 0.6, 1.0)) * (1.0 - 0.12 * squeeze)
        ph += f0 * dt
        if ph >= 1.0: ph -= 1.0
        buzz, noise = saw.at(ph), next(rnd) * 0.35
        level = (0.45 + 0.55 * (1.0 - squeeze)) * min(t / 0.05, 1.0)
        if stopping:
            fade -= dt / 0.12
            if fade <= 0.0:
                break
        out.append(eq((buzz + noise * squeeze) * level * fade) * 0.55)
    return np.array(out)


def render_horn(seconds=2.0, warmup=2.0):
    # steady sound only (env = 1, pitch bend settled); 415 Hz, 523 Hz and the 5.5 Hz vibrato are all whole
    # numbers of periods in 2.0 s, so the loop is seamless; the warm-up lets the EQ settle
    saw, eq = SawTable(10), Chain(lab_eq())
    dt = 1.0 / RATE
    n_warm, n = int(warmup * RATE), int(seconds * RATE)
    p1, p2, out = 0.0, 0.25, []
    for k in range(n_warm + n):
        tt = k * dt
        vib = 1.0 + 0.004 * math.sin(2 * math.pi * 5.5 * tt)
        p1 += 415.0 * vib * dt; p1 -= p1 >= 1.0
        p2 += 523.0 * vib * dt; p2 -= p2 >= 1.0
        s = eq(0.5 * (saw.at(p1) + saw.at(p2))) * 0.6
        if k >= n_warm:
            out.append(s)
    return np.array(out)


# ---------------------------------------------------------------- WAV files

def to_i16(x):
    return np.clip(np.round(np.asarray(x, dtype=np.float64) * 32768.0), -32768, 32767).astype(np.int16)


def write_wav(path, data_i16):
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(RATE)
        w.writeframes(np.asarray(data_i16, dtype="<i2").tobytes())


def read_wav(path):
    with wave.open(path) as w:
        if (w.getframerate(), w.getnchannels(), w.getsampwidth()) != (RATE, 1, 2):
            raise SystemExit("%s: must be 22050 Hz, mono, 16 bit" % path)
        return np.frombuffer(w.readframes(w.getnframes()), "<i2")


def voice_prompt(i):
    path = os.path.join(INC, "voice_prompts.h")
    return header_array(path, "VOICE_%d" % i)


def piper_name(text, piper, model):
    fd, tmp = tempfile.mkstemp(suffix=".wav"); os.close(fd)
    try:
        subprocess.run([os.path.join(piper, "piper.exe"), "--model", model, "--output_file", tmp],
                       input=text.encode("utf8"), check=True, capture_output=True)
        with wave.open(tmp) as w:
            rate, ch, sw = w.getframerate(), w.getnchannels(), w.getsampwidth()
            d = np.frombuffer(w.readframes(w.getnframes()), "<i2").astype(np.float64)
    finally:
        os.remove(tmp)
    if ch != 1 or sw != 2:
        raise SystemExit("piper wrote an unexpected format")
    if rate != RATE:   # linear resampling is enough for speech on this speaker
        n = int(len(d) * RATE / rate)
        d = np.interp(np.arange(n) * rate / RATE, np.arange(len(d)), d)
    nz = np.nonzero(np.abs(d) > 300)[0]   # cut the silence at both ends, 10 ms fades
    if len(nz):
        d = d[max(0, nz[0] - 220):nz[-1] + 220]
    f = min(220, len(d) // 2)
    d[:f] *= np.linspace(0, 1, f); d[-f:] *= np.linspace(1, 0, f)
    d *= 0.89 * 32767 / max(1.0, np.max(np.abs(d)))   # -1 dBFS
    return d.astype(np.int16)


# ---------------------------------------------------------------- main

def module_json(src):
    d = {k: v for k, v in src.items() if k not in ("sources", "eq", "eq_gain")}
    if src.get("eq"):
        if src["eq"] != "speaker_box":
            raise SystemExit("unknown eq %r" % src["eq"])
        eq = [list(c) for c in lab_eq()]
        g = float(src.get("eq_gain", 1.0))
        eq[0] = [eq[0][0] * g, eq[0][1] * g, eq[0][2] * g, eq[0][3], eq[0][4]]
        d["eq"] = [[float("%.9g" % v) for v in c] for c in eq]
    return d


def write_demo_js():
    """The built sets as window.DEMO_SETS = {folder: {file: base64}} for the page's simulated module."""
    sets = {}
    for folder in sorted(os.listdir(OUT)):
        d = os.path.join(OUT, folder)
        sets[folder] = {f: base64.b64encode(open(os.path.join(d, f), "rb").read()).decode("ascii")
                        for f in sorted(os.listdir(d))}
    with open(DEMO_JS, "w", newline="\n") as f:
        f.write("// Generated by tools/make_default_sets.py: the default sets for the simulated module of index.html.\n")
        f.write("window.DEMO_SETS = " + json.dumps(sets, indent=0) + ";\n")
    print("%s: %d sets, %.2f MB" % (os.path.relpath(DEMO_JS, ROOT), len(sets), os.path.getsize(DEMO_JS) / 1048576))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--piper", help="folder with piper.exe (speaks the names from set.json)")
    ap.add_argument("--model", help="Piper voice, .onnx (with its .onnx.json beside it)")
    ap.add_argument("--demo-only", action="store_true", help="only write web/demo_sets.js from firmware/data/sets")
    a = ap.parse_args()
    if a.demo_only:
        if not os.path.isdir(OUT):
            raise SystemExit("no sets in %s yet: run without --demo-only first" % OUT)
        return write_demo_js()
    cache = {"render:starter": to_i16(render_starter()), "render:horn": to_i16(render_horn()),
             "header:shift_sound": header_array(os.path.join(INC, "shift_sound.h"), "SHIFT_SOUND")}
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    total = 0
    for folder in sorted(os.listdir(SRC)):
        src = json.load(open(os.path.join(SRC, folder, "set.json"), encoding="utf8"))
        dst = os.path.join(OUT, folder)
        os.makedirs(dst)
        json.dump(module_json(src), open(os.path.join(dst, "set.json"), "w", newline="\n"), indent=1)
        files = {}
        for key, s in src["sources"].items():
            if key == "name":
                if a.piper and a.model:
                    files["name"] = piper_name(s["text"], a.piper, a.model)
                else:
                    files["name"] = voice_prompt(s["voice_prompt"])
                    print("  %s: name from voice_prompts.h (with its number); use --piper/--model for the plain name"
                          % folder)
            elif s in cache:
                files[key] = cache[s]
            else:
                files[key] = read_wav(os.path.join(ROOT, s))
        for key, data in files.items():
            write_wav(os.path.join(dst, key + ".wav"), data)
        size = sum(os.path.getsize(os.path.join(dst, f)) for f in os.listdir(dst))
        total += size
        print("%-14s %-6s %6.0f kB  %s" % (folder, src["type"], size / 1024, ", ".join(sorted(files))))
    print("total %.2f MB in %s" % (total / 1048576, os.path.relpath(OUT, ROOT)))
    write_demo_js()


if __name__ == "__main__":
    main()
