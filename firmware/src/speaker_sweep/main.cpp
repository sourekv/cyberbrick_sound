// Speaker measurement: plays a slow logarithmic sine sweep through the MAX98357A and the speaker, so that the
// frequency response of the speaker (in its housing) can be recorded with a phone and analysed on a PC with
// tools/analyze_speaker_sweep.py. Procedure: docs/speaker-measurement.md.
//
// Sequence: SWEEP_RUNS times [GAP_SECONDS of silence, then the sweep SWEEP_F0_HZ .. SWEEP_F1_HZ in SWEEP_SECONDS],
// then GAP_SECONDS of silence and nothing more. The silences give the noise floor of the room for the analysis.
// Same output path as the engine firmware (22.05 kHz, the same sample on both channels).
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
#define GAP_SECONDS 3
#define FADE_SECONDS 0.05f      // fade in and out of every sweep, avoids clicks

void setup() {
  Serial.begin(115200);
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
  Serial.printf("speaker_sweep: %d runs of %.0f..%.0f Hz in %d s, level %.2f, %d s of silence before each\n",
                SWEEP_RUNS, (double)SWEEP_F0_HZ, (double)SWEEP_F1_HZ, SWEEP_SECONDS, (double)SWEEP_LEVEL, GAP_SECONDS);
}

void loop() {
  const uint32_t gapN = (uint32_t)GAP_SECONDS * AUDIO_RATE;
  const uint32_t sweepN = (uint32_t)SWEEP_SECONDS * AUDIO_RATE;
  const uint32_t runN = gapN + sweepN;
  const uint32_t totalN = (uint32_t)SWEEP_RUNS * runN + gapN;
  const uint32_t fadeN = (uint32_t)(FADE_SECONDS * AUDIO_RATE);
  static const float ratio = powf(SWEEP_F1_HZ / SWEEP_F0_HZ, 1.0f / (float)sweepN);  // frequency factor per sample

  static uint32_t n = 0;     // sample counter since start
  static float phase = 0.0f;
  static float freq = SWEEP_F0_HZ;
  static bool finished = false;

  int16_t buf[256 * 2];      // interleaved L,R
  for (int i = 0; i < 256; i++) {
    float s = 0.0f;
    if (n < totalN) {
      uint32_t k = n % runN;
      if (n >= (uint32_t)SWEEP_RUNS * runN) k = 0;          // the last gap
      if (k >= gapN && n < (uint32_t)SWEEP_RUNS * runN) {
        uint32_t idx = k - gapN;                           // position in the sweep
        if (idx == 0) {
          phase = 0.0f;
          freq = SWEEP_F0_HZ;
          Serial.printf("sweep %lu / %d\n", (unsigned long)(n / runN + 1), SWEEP_RUNS);
        }
        float env = 1.0f;
        if (idx < fadeN) env = (float)idx / fadeN;
        else if (sweepN - idx < fadeN) env = (float)(sweepN - idx) / fadeN;
        s = sinf(phase) * env * SWEEP_LEVEL;
        phase += 2.0f * PI * freq / AUDIO_RATE;
        if (phase > 2.0f * PI) phase -= 2.0f * PI;
        freq *= ratio;
      }
      n++;
    } else if (!finished) {
      finished = true;
      Serial.println("speaker_sweep: done");
    }
    int16_t v = (int16_t)(s * 32767.0f);
    buf[2 * i] = v;
    buf[2 * i + 1] = v;
  }
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);
}
