// Speaker measurement: plays a slow logarithmic sine sweep through the MAX98357A and the speaker, so that the
// frequency response of the speaker (in its housing) can be recorded with a phone and analysed on a PC with
// tools/analyze_speaker_sweep.py. Procedure: docs/speaker-measurement.md.
//
// Timeline (about 2 minutes, the same sample on both channels, 22.05 kHz like the engine firmware):
//    0 s .. 15 s   countdown, LED red. Three short beeps at 10, 11 and 12 s: the recording must be running by then.
//   15 s           sweep 1 (SWEEP_F0_HZ .. SWEEP_F1_HZ in SWEEP_SECONDS), LED green
//   then           3 s of silence (LED red), sweep 2, 3 s of silence, sweep 3 (SWEEP_RUNS in total)
//   after the last sweep: 3 s of silence, then three longer beeps = finished, LED blue. Stop the recording then.
// The silence before every sweep gives the noise floor of the room for the analysis.
#include <Arduino.h>
#include <math.h>
#include "driver/i2s.h"
#include "config.h"

#ifndef SWEEP_F0_HZ
#define SWEEP_F0_HZ 100.0f      // start frequency
#endif
#ifndef SWEEP_F1_HZ
#define SWEEP_F1_HZ 10000.0f    // end frequency (must stay below the Nyquist limit AUDIO_RATE / 2 = 11025 Hz)
#endif
#ifndef SWEEP_SECONDS
#define SWEEP_SECONDS 30        // duration of one sweep
#endif
#ifndef SWEEP_LEVEL
#define SWEEP_LEVEL 0.25f       // peak level 0..1 of full scale; keep it moderate so that low notes do not clip the speaker
#endif
#ifndef SWEEP_RUNS
#define SWEEP_RUNS 3            // number of sweeps to record
#endif
#ifndef START_DELAY_SECONDS
#define START_DELAY_SECONDS 15  // time to start the recording; beeps at START_DELAY - 5, - 4, - 3 s
#endif
#define GAP_SECONDS 3
#define FADE_SECONDS 0.05f      // fade in and out of every sweep, avoids clicks
#define CUE_LEVEL 0.2f

static void led(uint8_t r, uint8_t g, uint8_t b) {
  static uint8_t lr = 255, lg = 255, lb = 255;
  if (r == lr && g == lg && b == lb) return;
  lr = r; lg = g; lb = b;
#if STATUS_LED_ENABLED
#if STATUS_LED_SWAP_RG
  neopixelWrite(PIN_STATUS_RGB, g, r, b);
#else
  neopixelWrite(PIN_STATUS_RGB, r, g, b);
#endif
#endif
}

void setup() {
  Serial.begin(115200);
  led(STATUS_LED_MAX, 0, 0);
  i2s_config_t cfg = {};
  cfg.mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_TX);
  cfg.sample_rate = AUDIO_RATE;
  cfg.bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT;
  cfg.channel_format = I2S_CHANNEL_FMT_RIGHT_LEFT;  // same sample on both channels, as in the engine firmware
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
  Serial.printf("speaker_sweep: start the recording now, the first sweep begins in %d s (%d sweeps of %.0f..%.0f Hz, %d s each)\n",
                START_DELAY_SECONDS, SWEEP_RUNS, (double)SWEEP_F0_HZ, (double)SWEEP_F1_HZ, SWEEP_SECONDS);
}

// short sine beep with a 5 ms fade; idx = sample index inside the beep
static float beep(uint32_t idx, uint32_t len, float hz) {
  if (idx >= len) return 0.0f;
  uint32_t f = AUDIO_RATE / 200;
  float env = idx < f ? (float)idx / f : (len - idx < f ? (float)(len - idx) / f : 1.0f);
  return sinf(2.0f * PI * hz * (float)idx / AUDIO_RATE) * env * CUE_LEVEL;
}

void loop() {
  const uint32_t startN = (uint32_t)START_DELAY_SECONDS * AUDIO_RATE;
  const uint32_t sweepN = (uint32_t)SWEEP_SECONDS * AUDIO_RATE;
  const uint32_t gapN = (uint32_t)GAP_SECONDS * AUDIO_RATE;
  const uint32_t blockN = sweepN + gapN;                       // one sweep and the silence after it
  const uint32_t sweepsEndN = startN + (uint32_t)SWEEP_RUNS * blockN;
  const uint32_t fadeN = (uint32_t)(FADE_SECONDS * AUDIO_RATE);
  const uint32_t shortBeepN = AUDIO_RATE * 15 / 100, longBeepN = AUDIO_RATE * 35 / 100;
  static const float ratio = powf(SWEEP_F1_HZ / SWEEP_F0_HZ, 1.0f / (float)sweepN);  // frequency factor per sample

  static uint32_t n = 0;     // sample counter since start
  static float phase = 0.0f;
  static float freq = SWEEP_F0_HZ;
  static uint32_t lastRun = 0;
  static bool finished = false;

  int16_t buf[256 * 2];      // interleaved L,R
  for (int i = 0; i < 256; i++) {
    float s = 0.0f;
    if (n < startN) {                                          // countdown, three short beeps
      for (int k = 0; k < 3; k++) {
        uint32_t b = (uint32_t)(START_DELAY_SECONDS - 5 + k) * AUDIO_RATE;
        if (n >= b && n < b + shortBeepN) s = beep(n - b, shortBeepN, 880.0f);
      }
      led(STATUS_LED_MAX, 0, 0);
    } else if (n < sweepsEndN) {
      uint32_t k = (n - startN) % blockN;
      uint32_t run = (n - startN) / blockN;
      if (k < sweepN) {
        if (k == 0) {
          phase = 0.0f;
          freq = SWEEP_F0_HZ;
          if (run != lastRun || n == startN) Serial.printf("sweep %lu / %d\n", (unsigned long)(run + 1), SWEEP_RUNS);
          lastRun = run;
        }
        float env = 1.0f;
        if (k < fadeN) env = (float)k / fadeN;
        else if (sweepN - k < fadeN) env = (float)(sweepN - k) / fadeN;
        s = sinf(phase) * env * SWEEP_LEVEL;
        phase += 2.0f * PI * freq / AUDIO_RATE;
        if (phase > 2.0f * PI) phase -= 2.0f * PI;
        freq *= ratio;
        led(0, STATUS_LED_MAX, 0);
      } else {
        led(STATUS_LED_MAX, 0, 0);                             // silence between the sweeps
      }
    } else {                                                   // after the last sweep: silence, then three long beeps
      uint32_t after = n - sweepsEndN;
      for (int k = 0; k < 3; k++) {
        uint32_t b = (uint32_t)(k * 0.6f * AUDIO_RATE);
        if (after >= b && after < b + longBeepN) s = beep(after - b, longBeepN, 660.0f);
      }
      if (after > (uint32_t)(1.6f * AUDIO_RATE)) {
        led(0, 0, STATUS_LED_MAX);
        if (!finished) { finished = true; Serial.println("speaker_sweep: done, stop the recording"); }
      }
    }
    n++;
    int16_t v = (int16_t)(s * 32767.0f);
    buf[2 * i] = v;
    buf[2 * i + 1] = v;
  }
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);
}
