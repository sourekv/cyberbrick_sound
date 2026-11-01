// Engine sound with a separate sample for every gear (test firmware), driven by the throttle servo pulse.
// Like the `engine` firmware family (virtual gearbox, include/gearbox.h), but instead of one idle loop played
// at 1x..3x, each gear plays its own loop (include/gear_bank.h) at only GEAR_RATE_LO..GEAR_RATE_HI, so the timbre
// stays close to the recording. The samples of two gears are crossfaded when the gear changes.
// With -DGEAR_BEEP=1 (env engine_gears) every gear change is announced with 1..5 beeps (include/gear_beep.h).
#include <Arduino.h>
#include <math.h>
#include "driver/i2s.h"
#include "config.h"
#include "status_led.h"
#include "gearbox.h"
#include "gear_bank.h"
#include "gear_beep.h"

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

// Adds N samples of a loop played at a variable rate (linear interpolation) times weight w to out[]; pos stays in the loop.
static void addLoop(float* out, int n, const GearSample& g, float& pos, float rate, float w) {
  for (int i = 0; i < n; i++) {
    int idx = (int)pos;
    int next = idx + 1;
    if (next >= g.len) next = 0;
    float frac = pos - idx;
    out[i] += w * (g.data[idx] + (g.data[next] - g.data[idx]) * frac);
    pos += rate;
    if (pos >= g.len) pos -= g.len;
  }
}

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
  Serial.println("engine_gears: running");
}

void loop() {
  static float pos[GEAR_COUNT] = {};   // position in the loop of each gear
  static float mix[GEAR_COUNT] = {1.0f};   // crossfade weight of each gear's loop (sums to ~1)
  static float prevGain = 1.0f;        // volume factor of the previous block (gearbox cut), ramped inside a block
  static Gearbox gearbox;
  static int lastGear = 0;
#if GEAR_BEEP
  static GearBeeper beeper((float)AUDIO_RATE);
#endif
  static uint32_t lastPrint = 0;

  const int N = 128;
  const float dt = (float)N / AUDIO_RATE;
  int16_t buf[N * 2];  // interleaved L,R
  float s[N];

  float target = readThrottle();
  statusLed.update(signalPresent(), target);
  gearbox.update(target, dt);
  const float rpm = gearbox.rpm;
  const float gain = gearbox.gain;

  if (gearbox.gear != lastGear) {
    lastGear = gearbox.gear;
#if GEAR_BEEP
    beeper.announce(lastGear + 1);
#endif
    Serial.printf("gear %d\n", lastGear + 1);
  }

  // Crossfade towards the loop of the current gear (first order, GEAR_XFADE_S); play only the audible ones.
  const float kx = dt / GEAR_XFADE_S > 1.0f ? 1.0f : dt / GEAR_XFADE_S;
  const float rate = GEAR_RATE_LO + (GEAR_RATE_HI - GEAR_RATE_LO) * rpm;
  for (int i = 0; i < N; i++) s[i] = 0.0f;
  for (int g = 0; g < GEAR_COUNT; g++) {
    mix[g] += ((g == gearbox.gear ? 1.0f : 0.0f) - mix[g]) * kx;
    if (mix[g] > 0.002f) addLoop(s, N, GEAR_BANK[g], pos[g], rate, sqrtf(mix[g]));   // equal power
    else mix[g] = 0.0f;
  }

  const float vol = MASTER_VOLUME * (0.55f + 0.45f * rpm);   // a bit louder with the revs
  for (int i = 0; i < N; i++) {
    float g = prevGain + (gain - prevGain) * ((float)(i + 1) / N);
    float v = s[i] * vol * g;
#if GEAR_BEEP
    v += beeper.next() * 32767.0f;
#endif
    if (v > 32767.0f) v = 32767.0f;
    if (v < -32768.0f) v = -32768.0f;
    buf[2 * i] = (int16_t)v;       // left
    buf[2 * i + 1] = (int16_t)v;   // right (the amp mixes (L+R)/2, so both must carry the signal)
  }
  prevGain = gain;
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);

  if (millis() - lastPrint > 500) {
    lastPrint = millis();
    Serial.printf("pulse %lu us  throttle %.2f  rpm %.2f  gear %d  rate %.2f\n",
                  (unsigned long)widthUs, target, rpm, gearbox.gear + 1, rate);
  }
}
