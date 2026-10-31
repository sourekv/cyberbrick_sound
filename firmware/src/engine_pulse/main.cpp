// Pulse-based engine sound driven by the throttle servo pulse.
// Same input and output wiring as the `engine` env; only the sound generation differs:
// RPM sets how often a combustion grain is triggered (see include/engine_synth.h).
#include <Arduino.h>
#include "driver/i2s.h"
#include "config.h"
#include "engine_synth.h"

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

// Throttle 0..1 from the pulse width (either stick direction); 0 when the signal is missing.
static float readThrottle() {
  if (millis() - lastEdgeMs > PULSE_TIMEOUT_MS) return 0.0f;
  int d = (int)widthUs - PULSE_CENTER_US;
  if (d < 0) d = -d;
  if (d < PULSE_DEADBAND_US) return 0.0f;
  float t = (float)(d - PULSE_DEADBAND_US) / (float)(PULSE_RANGE_US - PULSE_DEADBAND_US);
  return t > 1.0f ? 1.0f : t;
}

static EngineSynth synth;

void setup() {
  Serial.begin(115200);
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
  Serial.println("engine_pulse: running");
}

void loop() {
  static uint32_t lastPrint = 0;
  const int N = 128;
  int16_t buf[N * 2];  // interleaved L,R

  float target = readThrottle();
  synth.block(target);
  for (int i = 0; i < N; i++) {
    float s = synth.sample() * MASTER_VOLUME * 32767.0f;
    if (s > 32767.0f) s = 32767.0f;
    if (s < -32768.0f) s = -32768.0f;
    int16_t v = (int16_t)s;
    buf[2 * i] = v;
    buf[2 * i + 1] = v;
  }
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);

  if (millis() - lastPrint > 500) {
    lastPrint = millis();
    Serial.printf("pulse %lu us  throttle %.2f  rpm %.2f  load %.2f\n",
                  (unsigned long)widthUs, target, synth.rpm, synth.load);
  }
}
