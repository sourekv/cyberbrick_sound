// I2S test tone: 440 Hz sine, to check MAX98357A + speaker wiring.
#include <Arduino.h>
#include <math.h>
#include "driver/i2s.h"
#include "config.h"

void setup() {
  Serial.begin(115200);
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
  Serial.println("test_tone: 440 Hz");
}

void loop() {
  static float phase = 0;
  int16_t buf[256];
  for (int i = 0; i < 256; i++) {
    buf[i] = (int16_t)(sinf(phase) * 32767.0f * MASTER_VOLUME);
    phase += 2.0f * PI * 440.0f / AUDIO_RATE;
    if (phase > 2.0f * PI) phase -= 2.0f * PI;
  }
  size_t written;
  i2s_write(I2S_NUM_0, buf, sizeof(buf), &written, portMAX_DELAY);
}
