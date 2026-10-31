// Host preview of the real-recording engine (firmware/include/engine_real.h, unchanged).
// Needs firmware/include/user_sounds.h (generate it with tools/make_user_sounds.py).
//
// Build:  g++ -O2 -std=c++17 -I firmware/include tools/render_engine_real.cpp -o render_engine_real
// Run:    ./render_engine_real <out_prefix> [master_volume]
// Writes <out_prefix>_full.wav and <out_prefix>_small_speaker.wav (800 Hz two-pole high-pass).
#include <cstdio>
#include <cstdlib>
#include <cstdint>
#include <cmath>
#include <vector>
#include <string>
#include "engine_real.h"

static const int RATE = 22050;

static float throttleAt(float t) {   // start-up first, then the usual stick profile (shifted by 11 s)
  static const float p[][2] = {{0,0},{13,0},{16,1.0f},{18,1.0f},{21,0},{22,0},{22.4f,0.8f},{22.9f,0},
                               {23.4f,0.8f},{23.9f,0},{25,0},{25.1f,0.5f},{27.5f,0.5f},{29,0},{31,0}};
  int n = sizeof(p) / sizeof(p[0]);
  for (int i = 0; i + 1 < n; i++)
    if (t >= p[i][0] && t <= p[i + 1][0]) {
      float dt = p[i + 1][0] - p[i][0];
      return dt > 0 ? p[i][1] + (p[i + 1][1] - p[i][1]) * (t - p[i][0]) / dt : p[i + 1][1];
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
  if (argc < 2) { fprintf(stderr, "usage: %s out_prefix [volume]\n", argv[0]); return 1; }
  std::string prefix = argv[1];
  float master = argc >= 3 ? atof(argv[2]) : 0.6f;
  EngineReal e;
  int total = 31 * RATE;
  std::vector<int16_t> full, small;
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
  printf("%s: volume %.2f, rms %.3f, peak %.3f\n", prefix.c_str(), master, sqrt(sumSq / full.size()) / 32768.0, peak / 32768.0);
  return 0;
}
