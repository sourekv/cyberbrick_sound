#pragma once
// The pure part of the layered sample sets (design: docs/layers-design.md): which two layers play at a given engine
// speed, with which weights and at which playback rates. No hardware, so tools/test_layers.cpp tests it on the PC.
//
// A layer is a loop recorded at a steady engine speed. `ratio` is its pitch (firing frequency) relative to the first
// layer (1.0), rising from layer to layer. The target pitch r at engine speed rpm is the one of the sets without layers:
// r = rateLo + (rateHi - rateLo) * rpm. Layer i is played at r / ratio[i]. Neighbours i and i+1 are crossfaded around
// the geometric mean of their ratios, over `xfade` in natural-log units, with equal power (cos / sin).
#include <math.h>

static const int LAYERS_MAX = 8;

struct LayerMix {
  int a = 0, b = -1;        // layer indexes; b = -1: only a plays
  float wa = 1.0f, wb = 0.0f;   // weights (equal power: wa^2 + wb^2 = 1)
  float ra = 1.0f, rb = 1.0f;   // playback rates
};

// The crossfade width that is allowed: the crossfades of neighbouring pairs must not overlap, so xfade may not exceed
// the distance of the centres of two consecutive pairs. Returns the width to use (xfade, limited).
static inline float layersXfade(const float* ratio, int n, float xfade) {
  float w = xfade;
  for (int k = 0; k + 2 < n; k++) {
    float gap = 0.5f * (logf(ratio[k + 2]) - logf(ratio[k]));   // centre(k+1,k+2) - centre(k,k+1)
    if (gap < w) w = gap;
  }
  return w < 0.02f ? 0.02f : w;
}

// n >= 1 layers with rising ratios; r > 0; xfade as returned by layersXfade().
static inline LayerMix layerMix(const float* ratio, int n, float r, float xfade) {
  LayerMix m;
  if (n <= 0 || r <= 0.0f) return m;
  const float lr = logf(r);
  for (int k = 0; k + 1 < n; k++) {
    float lc = 0.5f * (logf(ratio[k]) + logf(ratio[k + 1]));
    float t = (lr - lc) / xfade + 0.5f;
    if (t <= 0.0f) { m.a = k; m.ra = r / ratio[k]; return m; }
    if (t < 1.0f) {
      m.a = k; m.b = k + 1;
      m.wa = cosf(t * 1.5707963f); m.wb = sinf(t * 1.5707963f);
      m.ra = r / ratio[k]; m.rb = r / ratio[k + 1];
      return m;
    }
  }
  m.a = n - 1; m.ra = r / ratio[n - 1];
  return m;
}
