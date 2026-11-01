#pragma once
// Virtual gearbox for the engine sound. Pure C++ (no Arduino), so tools/test_gearbox.cpp can test it on a PC.
//
// The module only sees the throttle, not the real speed of the model. So it keeps a virtual speed that follows the
// throttle with some inertia, derives the gear from it and turns that into the "rpm" (0..1) that drives the
// playback rate of the engine loop:
//   - speed rises linearly towards the throttle (GEAR_ACCEL_S for 0..1) and falls towards it (GEAR_DECEL_S)
//   - gear g covers the speed band g/N .. (g+1)/N; rpm rises across the band
//   - shifting up: rpm drops to GEAR_SHIFT_DROP of the next gear, and for SHIFT_CUT_S the sound is dimmed
//     (torque cut) and the speed does not rise
//   - shifting down (with a small hysteresis): the rpm jumps up again, like a throttle blip
// This is an effect, not a simulation: the sound does not follow the real speed of the model.
#include "config.h"

class Gearbox {
 public:
  float rpm = 0.0f;    // 0..1, to use like the smoothed rpm of the plain engine firmware
  float gain = 1.0f;   // 0..1 volume factor (dips while shifting up)
  float speed = 0.0f;  // 0..1 virtual speed
  int gear = 0;        // 0 .. GEAR_COUNT-1

  // Call once per audio block. throttle 0..1, dt = block duration in seconds.
  void update(float throttle, float dt) {
    bool shifting = cutLeft > 0.0f;
    if (shifting) cutLeft -= dt;

    if (throttle > speed) {
      if (!shifting) {
        speed += dt / GEAR_ACCEL_S;
        if (speed > throttle) speed = throttle;
      }
    } else {
      speed -= dt / GEAR_DECEL_S;
      if (speed < throttle) speed = throttle;
    }

    const float band = 1.0f / GEAR_COUNT;
    if (!shifting) {
      if (gear < GEAR_COUNT - 1 && speed >= (gear + 1) * band) {
        gear++;
        cutLeft = SHIFT_CUT_S;
        shifting = true;
      } else if (gear > 0 && speed < gear * band - 0.04f) {
        gear--;
      }
    }

    float pos = (speed - gear * band) / band;
    if (pos < 0.0f) pos = 0.0f;
    if (pos > 1.0f) pos = 1.0f;
    float lo = gear == 0 ? 0.0f : GEAR_SHIFT_DROP;
    float target = lo + (1.0f - lo) * pos;

    rpm += (target - rpm) * clamp01(dt * (shifting ? 12.0f : 6.0f));
    gain += ((shifting ? SHIFT_CUT_GAIN : 1.0f) - gain) * clamp01(dt * 40.0f);
  }

 private:
  float cutLeft = 0.0f;
  static float clamp01(float v) { return v < 0.0f ? 0.0f : (v > 1.0f ? 1.0f : v); }
};
