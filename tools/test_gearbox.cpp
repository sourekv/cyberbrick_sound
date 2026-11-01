// Host test of firmware/include/gearbox.h: prints speed, gear, rpm and gain for a throttle profile.
// Build: g++ -O1 -Ifirmware/include -o /tmp/test_gearbox tools/test_gearbox.cpp && /tmp/test_gearbox
#include <cstdio>
#include "gearbox.h"

int main() {
  Gearbox g;
  const float dt = 128.0f / 22050.0f;   // one audio block of engine/main.cpp
  struct Seg { float secs, throttle; } profile[] = {{1, 0}, {14, 1.0f}, {5, 0.5f}, {10, 0}};
  float t = 0, next = 0;
  int lastGear = 0;
  for (auto &s : profile) {
    for (float u = 0; u < s.secs; u += dt, t += dt) {
      g.update(s.throttle, dt);
      if (g.gear != lastGear) { printf("   -> gear %d at %.2f s (%s)\n", g.gear, t, g.gear > lastGear ? "up" : "down"); lastGear = g.gear; }
      if (t >= next) { printf("t=%5.2f thr=%.2f speed=%.2f gear=%d rpm=%.2f gain=%.2f\n", t, s.throttle, g.speed, g.gear, g.rpm, g.gain); next += 0.5f; }
    }
  }
  return 0;
}
