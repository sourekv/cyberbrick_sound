#pragma once
// Gear announcement for the `engine_gears` test firmware: after every gear change it plays as many short beeps as
// the number of the new gear (1..5), so you can hear which gear the virtual gearbox is in. Pure C++ (no Arduino),
// so tools/test_gear_beep.cpp can test it on a PC. Test aid only: the beeps are mixed over the engine sound.
#include <math.h>
#include <stdint.h>

#ifndef GEAR_BEEP_HZ
#define GEAR_BEEP_HZ     1000.0f   // clean part of the measured speaker response (docs/speaker-measurement.md)
#endif
#ifndef GEAR_BEEP_MS
#define GEAR_BEEP_MS     70        // length of one beep
#endif
#ifndef GEAR_BEEP_GAP_MS
#define GEAR_BEEP_GAP_MS 90        // pause between beeps
#endif
#ifndef GEAR_BEEP_DELAY_MS
#define GEAR_BEEP_DELAY_MS 250     // wait after the gear change (the torque cut is over by then)
#endif
#ifndef GEAR_BEEP_LEVEL
#define GEAR_BEEP_LEVEL  0.22f     // peak, fraction of full scale (before the final clip)
#endif

class GearBeeper {
 public:
  explicit GearBeeper(float sampleRate) : fs(sampleRate) {}

  // Start announcing gear number n (1..); an announcement in progress is replaced.
  void announce(int n) {
    count = n;
    pos = -(int32_t)(GEAR_BEEP_DELAY_MS * 0.001f * fs);
  }

  bool active() const { return count > 0; }

  // Next sample, -1..1 (already scaled by GEAR_BEEP_LEVEL); 0 when nothing is playing.
  float next() {
    if (count <= 0) return 0.0f;
    if (pos < 0) { pos++; return 0.0f; }
    const int32_t beepLen = (int32_t)(GEAR_BEEP_MS * 0.001f * fs);
    const int32_t period = beepLen + (int32_t)(GEAR_BEEP_GAP_MS * 0.001f * fs);
    const int32_t inBeep = pos % period;
    float s = 0.0f;
    if (inBeep < beepLen) {
      const float ramp = 0.005f * fs;   // 5 ms raised-cosine attack and release against clicks
      float env = 1.0f;
      if (inBeep < ramp) env = 0.5f - 0.5f * cosf(3.14159265f * inBeep / ramp);
      else if (beepLen - inBeep < ramp) env = 0.5f - 0.5f * cosf(3.14159265f * (beepLen - inBeep) / ramp);
      s = GEAR_BEEP_LEVEL * env * sinf(6.2831853f * GEAR_BEEP_HZ * inBeep / fs);
    }
    pos++;
    if (pos >= (int32_t)count * period) count = 0;   // all beeps played
    return s;
  }

 private:
  float fs;
  int count = 0;
  int32_t pos = 0;
};
