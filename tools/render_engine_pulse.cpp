// Host preview of the pulse-based engine synth. Uses firmware/include/engine_synth.h unchanged,
// so the WAV files are what the ESP32 will play (before the speaker).
//
// Build:  g++ -O2 -std=c++17 -I firmware/include tools/render_engine_pulse.cpp -o render_engine_pulse
// Run:    ./render_engine_pulse <out_prefix> [fire_idle_hz fire_max_hz [master_volume]]
// Writes <out_prefix>_full.wav and <out_prefix>_small_speaker.wav (800 Hz two-pole high-pass,
// roughly what a 40 mm speaker does to the low end).
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cmath>
#include <vector>
#include <string>
#include "engine_synth.h"

static const int RATE = 22050;

static float throttleAt(float t) {   // same stick-movement profile as tools/simulate_engine.py
  static const float p[][2] = {{0,0},{2,0},{5,1.0f},{7,1.0f},{10,0},{11,0},{11.4f,0.8f},{11.9f,0},
                               {12.4f,0.8f},{12.9f,0},{14,0},{14.1f,0.5f},{16.5f,0.5f},{18,0},{20,0}};
  int n = sizeof(p) / sizeof(p[0]);
  for (int i = 0; i + 1 < n; i++) {
    if (t >= p[i][0] && t <= p[i + 1][0]) {
      float dt = p[i + 1][0] - p[i][0];
      return dt > 0 ? p[i][1] + (p[i + 1][1] - p[i][1]) * (t - p[i][0]) / dt : p[i + 1][1];
    }
  }
  return 0;
}

static void writeWav(const std::string& name, const std::vector<int16_t>& d) {
  FILE* f = fopen(name.c_str(), "wb");
  uint32_t dataBytes = d.size() * 2, riff = 36 + dataBytes, fmt = 16, rate = RATE, br = RATE * 2;
  uint16_t pcm = 1, ch = 1, align = 2, bits = 16;
  fwrite("RIFF", 1, 4, f); fwrite(&riff, 4, 1, f); fwrite("WAVEfmt ", 1, 8, f);
  fwrite(&fmt, 4, 1, f); fwrite(&pcm, 2, 1, f); fwrite(&ch, 2, 1, f); fwrite(&rate, 4, 1, f);
  fwrite(&br, 4, 1, f); fwrite(&align, 2, 1, f); fwrite(&bits, 2, 1, f);
  fwrite("data", 1, 4, f); fwrite(&dataBytes, 4, 1, f); fwrite(d.data(), 2, d.size(), f);
  fclose(f);
}

int main(int argc, char** argv) {
  if (argc < 2) { fprintf(stderr, "usage: %s out_prefix [idle_hz max_hz [volume]]\n", argv[0]); return 1; }
  std::string prefix = argv[1];
  EngineSynth e;
  if (argc >= 4) { e.fireIdle = atof(argv[2]); e.fireMax = atof(argv[3]); }
  float master = argc >= 5 ? atof(argv[4]) : 0.6f;   // same as MASTER_VOLUME in config.h

  int total = 20 * RATE;
  std::vector<int16_t> full, small;
  full.reserve(total); small.reserve(total);
  float a = expf(-2.0f * M_PI * 800.0f / RATE);
  float y1 = 0, x1 = 0, y2 = 0, x2 = 0;
  double sumSq = 0; int peak = 0;
  for (int n = 0; n < total; n += 128) {
    e.block(throttleAt((float)n / RATE));
    for (int i = 0; i < 128; i++) {
      float v = e.sample() * master * 32767.0f;
      int16_t s = (int16_t)fmaxf(-32768.f, fminf(32767.f, v));
      full.push_back(s);
      float h1 = a * (y1 + v - x1); x1 = v; y1 = h1;
      float h2 = a * (y2 + h1 - x2); x2 = h1; y2 = h2;
      small.push_back((int16_t)fmaxf(-32768.f, fminf(32767.f, h2)));
      sumSq += (double)s * s; if (abs(s) > peak) peak = abs(s);
    }
  }
  writeWav(prefix + "_full.wav", full);
  writeWav(prefix + "_small_speaker.wav", small);
  printf("%s: fire %.0f..%.0f Hz, volume %.2f, rms %.3f, peak %.3f\n", prefix.c_str(), e.fireIdle,
         e.fireMax, master, sqrt(sumSq / full.size()) / 32768.0, peak / 32768.0);
  return 0;
}
