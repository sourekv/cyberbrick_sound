// Engine sound driven by the throttle servo pulse.
// Reads the pulse on PIN_THROTTLE_IN, smooths an "RPM" value, and plays the
// looped engine sample at a variable rate (linear interpolation) over I2S.
#include <Arduino.h>
#include "driver/i2s.h"
#include "config.h"
#include "engine_sample.h"

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

void setup() {
  Serial.begin(115200);
  pinMode(PIN_THROTTLE_IN, INPUT);
  attachInterrupt(digitalPinToInterrupt(PIN_THROTTLE_IN), onEdge, CHANGE);

  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = AUDIO_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;
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
  static float rpm = 0.0f;      // smoothed 0..1
  static uint32_t lastPrint = 0;

  const int N = 128;
  int16_t buf[N];

  // Update the smoothed RPM once per block (128 samples ~ 5.8 ms).
  float target = readThrottle();
  // Rise faster than fall, like a real engine spooling up / coasting down.
  float k = target > rpm ? 0.02f : 0.008f;
  rpm += (target - rpm) * k;

  // Playback rate: idle 0.7x .. full throttle 2.0x
  float rate = 0.7f + 1.3f * rpm;
  // Volume rises a bit with throttle.
  float vol = MASTER_VOLUME * (0.55f + 0.45f * rpm);

  for (int i = 0; i < N; i++) {
    int idx = (int)pos;
    float frac = pos - idx;
    int next = idx + 1;
    if (next >= ENGINE_SAMPLE_LEN) next = 0;
    float s = ENGINE_SAMPLE[idx] + (ENGINE_SAMPLE[next] - ENGINE_SAMPLE[idx]) * frac;
    buf[i] = (int16_t)(s * vol);
    pos += rate;
    if (pos >= ENGINE_SAMPLE_LEN) pos -= ENGINE_SAMPLE_LEN;
  }
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);

  if (millis() - lastPrint > 500) {
    lastPrint = millis();
    Serial.printf("pulse %lu us  throttle %.2f  rpm %.2f\n",
                  (unsigned long)widthUs, target, rpm);
  }
}
