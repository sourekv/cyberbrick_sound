#pragma once
// Speaker-tuned grain engine synthesiser (used by the `engine_lab` test firmware).
// Mirrors Synth2 in tools/engine_lab.py, which renders the previews; the data (grains, presets, speaker EQ) comes
// from tools/make_engine_lab_header.py. Keep both in step when changing one of them.
//
// Per firing pulse a fixed-timbre combustion grain is started (RPM changes only how often), plus a brighter grain
// under load and a short burst of band-pass noise synchronous with the firing. Then soft clip and the speaker EQ:
// the EQ comes after the clipper so the difference tones the clipper creates at the firing rate are removed.
#include <math.h>
#include <stdint.h>
#include "engine_lab_data.h"
#include "gearbox.h"

class Biquad {
 public:
  void set(const float* c) { b0 = c[0]; b1 = c[1]; b2 = c[2]; a1 = c[3]; a2 = c[4]; z1 = z2 = 0.0f; }
  float run(float x) {   // transposed direct form II
    float y = b0 * x + z1;
    z1 = b1 * x - a1 * y + z2;
    z2 = b2 * x - a2 * y;
    return y;
  }
 private:
  float b0 = 1, b1 = 0, b2 = 0, a1 = 0, a2 = 0, z1 = 0, z2 = 0;
};

class SpeakerEq {
 public:
  SpeakerEq() { for (int i = 0; i < LAB_EQ_STAGES; i++) st[i].set(LAB_EQ[i]); }
  float run(float x) { for (int i = 0; i < LAB_EQ_STAGES; i++) x = st[i].run(x); return x; }
 private:
  Biquad st[LAB_EQ_STAGES];
};

class EngineSynth2 {
 public:
  float rpm = 0.0f, load = 0.0f;

  void setPreset(int i) {
    preset = i;
    const LabPreset& p = LAB_PRESET[i];
    noiseBp.set(p.noiseBp);
    eq = SpeakerEq();
    for (int v = 0; v < MAXV; v++) voices[v].data = nullptr;
    fire = p.fireIdle;
    countdown = 1.0f;
    env = 0.0f;
  }

  // Once per audio block, after gearbox.update().
  void block(float throttle, const Gearbox& gb) {
    const LabPreset& p = LAB_PRESET[preset];
    rpm = gb.rpm;
    float push = throttle - gb.speed;
    if (push < 0.0f) push = 0.0f;
    load = 0.3f * throttle + 2.5f * push;
    if (load > 1.0f) load = 1.0f;
    fire = p.fireIdle + (p.fireMax - p.fireIdle) * rpm;
    vol = (0.55f + 0.45f * rpm) * gb.gain * p.outGain;
  }

  // One sample, about -1..1 (apply MASTER_VOLUME outside).
  float sample() {
    const LabPreset& p = LAB_PRESET[preset];
    countdown -= 1.0f;
    if (countdown <= 0.0f) trigger(p);
    float s = 0.0f;
    for (int i = 0; i < MAXV; i++) {
      Voice& v = voices[i];
      if (v.data) {
        s += v.amp * (float)v.data[v.pos] * (1.0f / 32768.0f);
        if (++v.pos >= p.grainLen) v.data = nullptr;
      }
    }
    s += noiseBp.run(rnd()) * env * (p.noiseLo + p.noiseHi * rpm + 0.5f * p.noiseHi * load);
    env *= p.envK;
    s *= vol;
    s = s / (1.0f + fabsf(s));
    return eq.run(s) * 0.8f;
  }

 private:
  static const int MAXV = 8;
  struct Voice { const int16_t* data = nullptr; int pos = 0; float amp = 0; };
  Voice voices[MAXV];
  int preset = 0;
  float countdown = 1.0f, fire = 30.0f, vol = 0.55f, env = 0.0f;
  int cyl = 0;
  uint32_t seed = 0x1234567u;
  Biquad noiseBp;
  SpeakerEq eq;

  float rnd() {   // -1..1 (xorshift32)
    seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5;
    return (float)(int32_t)seed * (1.0f / 2147483648.0f);
  }

  void start(const int16_t* data, float amp) {
    for (int i = 0; i < MAXV; i++) {
      if (!voices[i].data) { voices[i].data = data; voices[i].pos = 0; voices[i].amp = amp; return; }
    }
    int o = 0;   // all busy: steal the oldest
    for (int i = 1; i < MAXV; i++) if (voices[i].pos > voices[o].pos) o = i;
    voices[o].data = data; voices[o].pos = 0; voices[o].amp = amp;
  }

  void trigger(const LabPreset& p) {
    int k = cyl % p.patternLen;
    cyl++;
    float uneven = 0.2f + 0.8f * (1.0f - rpm);
    float amp = (1.0f + (p.ampPattern[k] - 1.0f) * uneven) * (0.93f + 0.07f * rnd());
    int variant = (int)((0.5f + 0.5f * rnd()) * LAB_VARIANTS) % LAB_VARIANTS;
    start(LAB_GRAIN_BASE[preset][variant], amp * (1.0f - 0.4f * load));
    if (load > 0.05f) start(LAB_GRAIN_BRIGHT[preset][variant], amp * load);
    env = amp;
    float period = 22050.0f / fire;
    countdown += period * (1.0f + p.timePattern[k] * uneven + (0.01f + 0.05f * (1.0f - rpm)) * rnd());
  }
};
