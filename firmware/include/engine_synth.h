#pragma once
// Pulse-based engine synthesiser (header only, no Arduino dependencies, so the exact same
// code runs on the ESP32 and in the host preview tool tools/render_engine_pulse.cpp).
//
// RPM sets how often a short combustion "grain" is triggered; the timbre of the grain does not
// change with RPM. Throttle pushed beyond the current RPM (accelerating) mixes in a brighter
// grain, so the engine sounds harder under load. Idle has an uneven "lope" that smooths out as
// the revs rise.
#include <stdint.h>
#include <math.h>
#include "engine_grains.h"

#ifndef ENGINE_FIRE_IDLE_HZ
#define ENGINE_FIRE_IDLE_HZ 38.0f    // firing pulses per second at idle
#endif
#ifndef ENGINE_FIRE_MAX_HZ
#define ENGINE_FIRE_MAX_HZ 125.0f    // firing pulses per second at full throttle
#endif
#ifndef ENGINE_OUT_GAIN
#define ENGINE_OUT_GAIN 5.0f
#endif

class EngineSynth {
 public:
  float rpm = 0.0f;        // smoothed 0..1
  float load = 0.0f;       // 0..1
  float fireIdle = ENGINE_FIRE_IDLE_HZ;
  float fireMax = ENGINE_FIRE_MAX_HZ;
  float sampleRate = (float)GRAIN_RATE;

  // Call once per audio block (about every 5.8 ms) with throttle 0..1.
  void block(float throttle) {
    float k = throttle > rpm ? 0.02f : 0.008f;   // spools up faster than it coasts down
    rpm += (throttle - rpm) * k;
    float push = throttle - rpm;
    if (push < 0) push = 0;
    load = 0.35f * throttle + 3.0f * push;
    if (load > 1.0f) load = 1.0f;
    fireHz = fireIdle + (fireMax - fireIdle) * rpm;
    float v = 0.55f + 0.45f * rpm;               // louder with revs
    gain = v * ENGINE_OUT_GAIN;
  }

  // One output sample in -1..1 (apply the master volume outside).
  float sample() {
    if (--countdown <= 0.0f) trigger();
    float s = 0.0f;
    for (int i = 0; i < MAXV; i++) {
      Voice& v = voices[i];
      if (v.data) {
        s += v.amp * (float)v.data[v.pos] * (1.0f / 32768.0f);
        if (++v.pos >= GRAIN_LEN) v.data = nullptr;
      }
    }
    // mechanical / combustion noise bed, grows with revs
    noiseState += 0.30f * (rnd() - noiseState);
    s += noiseState * (0.03f + 0.16f * rpm * rpm);
    s *= gain * 0.55f;
    // soft clip (keeps loud overlaps from hard clipping)
    return s / (1.0f + fabsf(s));
  }

 private:
  static const int MAXV = 8;
  struct Voice { const int16_t* data = nullptr; int pos = 0; float amp = 0; };
  Voice voices[MAXV];
  float countdown = 1.0f;
  float fireHz = ENGINE_FIRE_IDLE_HZ;
  float gain = 0.55f;
  float noiseState = 0.0f;
  uint32_t seed = 0x1234567u;
  int cyl = 0;

  // 6-cylinder firing "unevenness" pattern (1 = normal)
  static float pattern(int i) {
    static const float p[6] = {1.00f, 0.82f, 0.95f, 0.78f, 1.00f, 0.88f};
    return p[i % 6];
  }

  float rnd() {                       // -1..1 (xorshift32)
    seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5;
    return (float)(int32_t)seed * (1.0f / 2147483648.0f);
  }
  float rnd01() { return 0.5f + 0.5f * rnd(); }

  void start(const int16_t* data, float amp) {
    for (int i = 0; i < MAXV; i++) {
      if (!voices[i].data) { voices[i].data = data; voices[i].pos = 0; voices[i].amp = amp; return; }
    }
    // all voices busy: steal the oldest
    int o = 0;
    for (int i = 1; i < MAXV; i++) if (voices[i].pos > voices[o].pos) o = i;
    voices[o].data = data; voices[o].pos = 0; voices[o].amp = amp;
  }

  void trigger() {
    float uneven = 0.15f + 0.85f * (1.0f - rpm);          // lope strongest at idle
    float amp = 1.0f + (pattern(cyl++) - 1.0f) * uneven;
    amp *= 0.92f + 0.16f * rnd01();
    int variant = (int)(rnd01() * GRAIN_VARIANTS) % GRAIN_VARIANTS;
    start(GRAIN_BASE[variant], amp * (1.0f - 0.35f * load));
    if (load > 0.05f) start(GRAIN_BRIGHT[variant], amp * load * 0.9f);
    float jitter = 0.02f + 0.10f * (1.0f - rpm);           // timing jitter
    countdown += (sampleRate / fireHz) * (1.0f + jitter * rnd());
  }
};
