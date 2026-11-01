// Engine sound driven by the throttle servo pulse.
// Reads the pulse on PIN_THROTTLE_IN, smooths an "RPM" value, and plays the
// looped engine sample at a variable rate (linear interpolation) over I2S.
#include <Arduino.h>
#include <math.h>
#include "driver/i2s.h"
#include "config.h"
#include "status_led.h"
#include "gearbox.h"
#if defined(ENGINE_TRUCK)
#include "engine_truck.h"           // real truck idle loop (CC0), see assets/samples/LICENSE-SAMPLES.md
#include "engine_truck_loaded.h"    // second loop "under load" (CC0), blended in with the throttle
#define LOADED_LAYER 1
static const float RATE_IDLE = 1.0f;  // playback rate at rest
static const float RATE_FULL = 3.0f;  // playback rate at full throttle
#elif defined(ENGINE_DIESEL)
#include "engine_diesel.h"          // real diesel idle loop (CC0), see assets/samples/LICENSE-SAMPLES.md
static const float RATE_IDLE = 1.0f;
static const float RATE_FULL = 3.0f;
#else
#include "engine_sample.h"          // synthesised loop
static const float RATE_IDLE = 0.7f;
static const float RATE_FULL = 2.0f;
#endif
#ifndef LOADED_LAYER
#define LOADED_LAYER 0
#endif

static volatile uint32_t riseUs = 0;
static volatile uint32_t widthUs = 0;
static volatile uint32_t lastEdgeMs = 0;

void IRAM_ATTR onEdge() {
  uint32_t now = micros();
  if (digitalRead(PIN_THROTTLE_IN)) {
    riseUs = now;
  } else if (riseUs) {
    uint32_t w = now - riseUs;
    if (w >= PULSE_MIN_US && w <= PULSE_MAX_US) {
      widthUs = w;
      lastEdgeMs = millis();
    }
  }
}

// Throttle 0..1 from the pulse width; 0 when the signal is missing.
static float readThrottle() {
  if (millis() - lastEdgeMs > PULSE_TIMEOUT_MS) return 0.0f;
  int d = (int)widthUs - PULSE_CENTER_US;
  if (d < 0) d = -d;
  if (d < PULSE_DEADBAND_US) return 0.0f;
  float t = (float)(d - PULSE_DEADBAND_US) / (float)(PULSE_RANGE_US - PULSE_DEADBAND_US);
  return t > 1.0f ? 1.0f : t;
}

// True while valid pulses keep arriving.
static bool signalPresent() {
  return lastEdgeMs != 0 && millis() - lastEdgeMs <= PULSE_TIMEOUT_MS;
}

static StatusLed statusLed;

#if LOADED_LAYER
// Plays a loop at a variable rate with linear interpolation; pos is kept inside the loop.
static inline float playLoop(const int16_t* data, int len, float& pos, float rate) {
  int idx = (int)pos;
  float frac = pos - idx;
  int next = idx + 1;
  if (next >= len) next = 0;
  float s = data[idx] + (data[next] - data[idx]) * frac;
  pos += rate;
  if (pos >= len) pos -= len;
  return s;
}
#endif

void setup() {
  Serial.begin(115200);
  statusLed.begin();
  pinMode(PIN_THROTTLE_IN, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_THROTTLE_IN), onEdge, CHANGE);

  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = AUDIO_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;  // same sample on both channels
  cfg.communication_format = I2S_COMM_FORMAT_STAND_I2S;
  cfg.intr_alloc_flags = ESP_INTR_FLAG_LEVEL1;
  cfg.dma_buf_count = 6;
  cfg.dma_buf_len = 256;
  cfg.tx_desc_auto_clear = true;
  i2s_pin_config_t pins = {};
  pins.mck_io_num = I2S_PIN_NO_CHANGE;
  pins.bck_io_num = PIN_I2S_BCLK;
  pins.ws_io_num = PIN_I2S_LRC;
  pins.data_out_num = PIN_I2S_DOUT;
  pins.data_in_num = I2S_PIN_NO_CHANGE;
  i2s_driver_install(I2S_NUM_0, &cfg, 0, nullptr);
  i2s_set_pin(I2S_NUM_0, &pins);
  Serial.println("engine: running");
}

void loop() {
  static float pos = 0.0f;      // position in the sample
#if LOADED_LAYER
  static float posLoaded = 0.0f;  // position in the "under load" loop
  static float load = 0.0f;       // smoothed throttle 0..1: share of the "under load" loop
#endif
  static float rpm = 0.0f;      // smoothed 0..1
  static float prevGain = 1.0f; // volume factor of the previous block (gearbox cut), ramped inside a block
  static Gearbox gearbox;
  static uint32_t lastPrint = 0;

  const int N = 128;
  int16_t buf[N * 2];  // interleaved L,R

  // Update the smoothed RPM once per block (128 samples ~ 5.8 ms).
  float target = readThrottle();
  statusLed.update(signalPresent(), target);
  float gain = 1.0f;
#if GEARBOX_ENABLED
  // Virtual gearbox: rpm and volume cut come from the shift logic (see include/gearbox.h).
  gearbox.update(target, (float)N / AUDIO_RATE);
  rpm = gearbox.rpm;
  gain = gearbox.gain;
#else
  // Rise faster than fall, like a real engine spooling up / coasting down.
  float k = target > rpm ? 0.02f : 0.008f;
  rpm += (target - rpm) * k;
#endif

  // Playback rate: RATE_IDLE at rest .. RATE_FULL at full throttle
  float rate = RATE_IDLE + (RATE_FULL - RATE_IDLE) * rpm;
  // Volume rises a bit with throttle.
  float vol = MASTER_VOLUME * (0.55f + 0.45f * rpm);

#if LOADED_LAYER
  // Blend idle loop and "under load" loop by the throttle (equal power). The loaded loop has a slightly lower
  // firing rate and a different level, so it is played faster / quieter to match (see config.h).
  load += (target - load) * 0.04f;
  const float wIdle = cosf(load * 1.5707963f);
  const float wLoaded = sinf(load * 1.5707963f);
  for (int i = 0; i < N; i++) {
    float s = wIdle * playLoop(ENGINE_SAMPLE, ENGINE_SAMPLE_LEN, pos, rate)
            + wLoaded * LOADED_GAIN * playLoop(ENGINE_LOADED, ENGINE_LOADED_LEN, posLoaded, rate * LOADED_RATE_SCALE);
    float g = prevGain + (gain - prevGain) * ((float)(i + 1) / N);
    int16_t v = (int16_t)(s * vol * g);
    buf[2 * i] = v;      // left
    buf[2 * i + 1] = v;  // right (the amp mixes (L+R)/2, so both must carry the signal)
  }
#else
  for (int i = 0; i < N; i++) {
    int idx = (int)pos;
    float frac = pos - idx;
    int next = idx + 1;
    if (next >= ENGINE_SAMPLE_LEN) next = 0;
    float s = ENGINE_SAMPLE[idx] + (ENGINE_SAMPLE[next] - ENGINE_SAMPLE[idx]) * frac;
    float g = prevGain + (gain - prevGain) * ((float)(i + 1) / N);
    int16_t v = (int16_t)(s * vol * g);
    buf[2 * i] = v;      // left
    buf[2 * i + 1] = v;  // right (the amp mixes (L+R)/2, so both must carry the signal)
    pos += rate;
    if (pos >= ENGINE_SAMPLE_LEN) pos -= ENGINE_SAMPLE_LEN;
  }
#endif
  prevGain = gain;
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);

  if (millis() - lastPrint > 500) {
    lastPrint = millis();
    Serial.printf("pulse %lu us  throttle %.2f  rpm %.2f  gear %d\n",
                  (unsigned long)widthUs, target, rpm,
#if GEARBOX_ENABLED
                  gearbox.gear + 1);
#else
                  0);
#endif
  }
}
