// Host test of firmware/include/gear_beep.h: for gears 1..5 counts the beeps and checks their timing.
// Build: g++ -O1 -Ifirmware/include -o /tmp/test_gear_beep tools/test_gear_beep.cpp && /tmp/test_gear_beep
#include <cstdio>
#include <cmath>
#include "gear_beep.h"

int main() {
  const float fs = 22050.0f;
  int failures = 0;
  for (int gear = 1; gear <= 5; gear++) {
    GearBeeper b(fs);
    b.announce(gear);
    int beeps = 0, n = 0, firstOn = -1, lastOn = -1, lastAbove = -100000;
    bool on = false;
    float peak = 0.0f;
    while (b.active() && n < (int)(5 * fs)) {
      float s = b.next(); n++;
      float a = fabsf(s);
      if (a > peak) peak = a;
      if (a > 0.02f * GEAR_BEEP_LEVEL) lastAbove = n;       // above the fade-in/out edges
      bool nowOn = n - lastAbove < (int)(0.005f * fs);      // hold 5 ms: the sine crosses zero every cycle
      if (nowOn && !on) { beeps++; if (firstOn < 0) firstOn = n; }
      if (nowOn) lastOn = n;
      on = nowOn;
    }
    float startS = firstOn / fs, endS = lastOn / fs;
    bool ok = beeps == gear && startS >= GEAR_BEEP_DELAY_MS * 0.001f && peak <= GEAR_BEEP_LEVEL + 1e-4f;
    printf("gear %d: %d beeps, first at %.3f s, last ends %.3f s, peak %.2f %s\n", gear, beeps, startS, endS, peak, ok ? "ok" : "FAIL");
    if (!ok) failures++;
    if (b.next() != 0.0f) { printf("  not silent after the last beep\n"); failures++; }
  }
  // a new gear change replaces an announcement in progress
  GearBeeper b(fs);
  b.announce(5);
  for (int i = 0; i < (int)(0.4f * fs); i++) b.next();
  b.announce(2);
  int beeps = 0, lastAbove = -100000; bool on = false;
  for (int i = 0; i < (int)(3 * fs); i++) {
    if (fabsf(b.next()) > 0.02f * GEAR_BEEP_LEVEL) lastAbove = i;
    bool nowOn = i - lastAbove < (int)(0.005f * fs);
    if (nowOn && !on) beeps++;
    on = nowOn;
  }
  printf("replaced announcement: %d beeps %s\n", beeps, beeps == 2 ? "ok" : "FAIL");
  if (beeps != 2) failures++;
  return failures ? 1 : 0;
}
