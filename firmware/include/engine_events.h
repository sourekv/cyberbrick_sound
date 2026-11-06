#pragma once
// Engine start, stop and horn for the `engine_lab` firmware, driven by the receiver's channel data
// (include/rc_link.h). All three sounds are synthesised here (no recordings, no licences); design and controls in
// docs/start-stop-horn.md.
//
//   ignition switch (left shoulder 3-position switch, L1) moved out of OFF  -> starter cranks, engine catches
//   ignition switch moved back to OFF                                         -> engine winds down and stops
//   throttle moved while the engine is off                                    -> engine runs at once (no starter)
//   right shoulder stick (R1) pushed either way                               -> horn, as long as it is held
//
// Without channel data (servo pulse only) the engine just runs, as before.
#include <math.h>
#include <stdint.h>
#include "engine_synth2.h"   // SpeakerEq

// One cycle of a band-limited sawtooth (harmonics 1..H with 1/k amplitudes), read with linear interpolation.
class SawTable {
 public:
  static const int N = 512;
  void build(int harmonics) {
    float peak = 0.0f;
    for (int i = 0; i < N; i++) {
      float s = 0.0f;
      for (int k = 1; k <= harmonics; k++) s += sinf(6.2831853f * k * i / N) / k;
      t[i] = s;
      if (fabsf(s) > peak) peak = fabsf(s);
    }
    for (int i = 0; i < N; i++) t[i] /= peak;
  }
  float at(float phase) const {   // phase 0..1
    float x = phase * N;
    int i = (int)x;
    float f = x - i;
    i &= N - 1;
    return t[i] + (t[(i + 1) & (N - 1)] - t[i]) * f;
  }
 private:
  float t[N];
};

// Electric starter turning the engine over: a buzzing motor whose speed and level dip on every compression stroke.
class StarterSound {
 public:
  void begin() { saw.build(14); }
  void start() { t = 0.0f; on = true; fade = 1.0f; stopping = false; }
  void stop() { stopping = true; }            // fades out quickly (engine caught)
  bool active() const { return on; }
  float sample() {
    if (!on) return 0.0f;
    const float dt = 1.0f / 22050.0f;
    t += dt;
    // compression strokes about 9 per second, a little faster as the starter spins up
    float strokeHz = 7.5f + 2.0f * fminf(t / 0.6f, 1.0f);
    strokePh += strokeHz * dt;
    if (strokePh >= 1.0f) strokePh -= 1.0f;
    float squeeze = 0.5f + 0.5f * cosf(6.2831853f * strokePh);   // 1 at the top of a compression
    float f0 = (150.0f + 40.0f * fminf(t / 0.6f, 1.0f)) * (1.0f - 0.12f * squeeze);
    ph += f0 * dt;
    if (ph >= 1.0f) ph -= 1.0f;
    float buzz = saw.at(ph);
    float noise = rnd() * 0.35f;
    float level = (0.45f + 0.55f * (1.0f - squeeze)) * fminf(t / 0.05f, 1.0f);
    if (stopping) { fade -= dt / 0.12f; if (fade <= 0.0f) { on = false; return 0.0f; } }
    return eq.run((buzz + noise * squeeze) * level * fade) * 0.55f;
  }
 private:
  SawTable saw;
  SpeakerEq eq;
  float t = 0.0f, ph = 0.0f, strokePh = 0.0f, fade = 1.0f;
  bool on = false, stopping = false;
  uint32_t seed = 0x2468ace1u;
  float rnd() { seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5; return (float)(int32_t)seed * (1.0f / 2147483648.0f); }
};

// Two-tone air horn (a major third, placed above the speaker's 450 Hz resonance), held as long as the stick is.
class HornSound {
 public:
  void begin() { saw.build(10); }
  void set(bool held) { this->held = held; }
  float sample() {
    const float dt = 1.0f / 22050.0f;
    if (held) { if (env == 0.0f) blat = 0.0f; env += dt / 0.025f; if (env > 1.0f) env = 1.0f; }
    else { env -= dt / 0.12f; if (env < 0.0f) env = 0.0f; }
    if (env == 0.0f) return 0.0f;
    blat += dt;
    float bend = 1.0f - 0.05f * expf(-blat / 0.06f);       // the pitch settles as the air pressure builds up
    float vib = 1.0f + 0.004f * sinf(6.2831853f * 5.5f * blat);
    p1 += 415.0f * bend * vib * dt; if (p1 >= 1.0f) p1 -= 1.0f;
    p2 += 523.0f * bend * vib * dt; if (p2 >= 1.0f) p2 -= 1.0f;
    float s = 0.5f * (saw.at(p1) + saw.at(p2));
    return eq.run(s * env) * 0.6f;
  }
 private:
  SawTable saw;
  SpeakerEq eq;
  bool held = false;
  float env = 0.0f, blat = 0.0f, p1 = 0.0f, p2 = 0.25f;
};

// Engine state: decides whether the engine sound plays, and overrides the rpm while it starts and stops.
// Per audio block: throttle = block(...) before gearbox.update(throttle), then apply(gearbox.rpm, gearbox.gain).
class EngineState {
 public:
  enum State { OFF, CRANKING, RUNNING, STOPPING };
  State state = RUNNING;      // without channel data the engine simply runs
  float gain = 1.0f;          // engine sound level 0..1 (multiply the engine samples)

  // dataAlive: channel data present; ignitionOn: switch out of OFF; moving: throttle off rest; rpmNow: the
  // gearbox rpm of the previous block. Returns the throttle to feed to the gearbox.
  float block(bool dataAlive, bool ignitionOn, bool moving, float throttle, float dt, float rpmNow,
              StarterSound& starter) {
    override = false;
    if (!dataAlive) {                       // servo pulse only: run as before
      if (state != RUNNING) { state = RUNNING; flare = false; starter.stop(); }
      wasAlive = false;
      gain = approach(gain, 1.0f, dt / 0.3f);
      return throttle;
    }
    if (!wasAlive) {                        // first frames: follow the switch, quietly
      wasAlive = true;
      lastIgnition = ignitionOn;
      if (!ignitionOn && !moving && state == RUNNING) { state = STOPPING; t = 0.0f; rpm0 = rpmNow; quietStop = true; }
    }
    if (ignitionOn && !lastIgnition && (state == OFF || state == STOPPING)) {
      state = CRANKING; t = 0.0f; starter.start();
    }
    if (!ignitionOn && lastIgnition && (state == RUNNING || state == CRANKING)) {
      if (state == CRANKING) starter.stop();
      state = STOPPING; t = 0.0f; rpm0 = rpmNow; quietStop = false;
    }
    lastIgnition = ignitionOn;
    if (moving && (state == OFF || state == STOPPING)) {   // never silent while the truck moves
      state = RUNNING; flare = false;
    }

    t += dt;
    switch (state) {
      case OFF:
        gain = 0.0f; override = true; rpmSet = 0.0f;
        return 0.0f;
      case CRANKING:
        gain = 0.0f; override = true; rpmSet = 0.0f;
        if (t >= CRANK_S) { state = RUNNING; t = 0.0f; flare = true; starter.stop(); }
        return 0.0f;
      case STOPPING: {
        float x = t / (quietStop ? 0.35f : STOP_S);
        if (x >= 1.0f) { state = OFF; gain = 0.0f; override = true; rpmSet = 0.0f; return 0.0f; }
        override = true;
        rpmSet = rpm0 + (-0.3f - rpm0) * (1.0f - (1.0f - x) * (1.0f - x));   // falls fast, then slower, below idle
        gain = x < 0.6f ? 1.0f : 1.0f - (x - 0.6f) / 0.4f;
        gain *= gain;
        return 0.0f;
      }
      case RUNNING:
      default:
        gain = approach(gain, 1.0f, dt / (flare ? 0.06f : 0.3f));
        if (flare) {                        // the engine catches: a short rev, settling to idle
          flareRpm = t < 0.15f ? 0.45f * t / 0.15f : 0.45f * expf(-(t - 0.15f) / 0.3f);
          if (t > 1.5f) flare = false;
        }
        return throttle;
    }
  }

  // After gearbox.update(): replace the rpm while starting or stopping.
  void apply(float& rpm, float& gbGain) {
    if (override) { rpm = rpmSet; gbGain = 1.0f; }
    else if (flare && flareRpm > rpm) { rpm = flareRpm; gbGain = 1.0f; }
  }

  bool silent() const { return state == OFF || state == CRANKING; }

 private:
  static constexpr float CRANK_S = 1.1f;
  static constexpr float STOP_S = 1.4f;
  bool wasAlive = false, lastIgnition = false, flare = false, quietStop = false, override = false;
  float t = 0.0f, rpm0 = 0.0f, rpmSet = 0.0f, flareRpm = 0.0f;
  static float approach(float v, float to, float step) { return v < to ? fminf(v + step, to) : fmaxf(v - step, to); }
};
