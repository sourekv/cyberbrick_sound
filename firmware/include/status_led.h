#pragma once
// Status colour on the onboard RGB LED of the Waveshare ESP32-S3-Zero (a WS2812 on GPIO21).
// Colours (kept dim, the LED is bright):
//   blue flash at start-up
//   red         no valid throttle pulse (cable, port or receiver problem)
//   dim green   signal present, stick at rest
//   cyan        signal present, brightens with the throttle
// Set STATUS_LED_ENABLED to 0 in config.h to switch it off.
#include <Arduino.h>
#include "config.h"

#if STATUS_LED_ENABLED

class StatusLed {
 public:
  void begin() {
    write(0, 0, STATUS_LED_MAX);   // start-up flash
    delay(250);
    write(0, 0, 0);
    lastMs = millis();
  }

  // signalPresent: valid pulse seen recently; throttle: 0..1
  void update(bool signalPresent, float throttle) {
    uint32_t now = millis();
    if (now - lastMs < 40) return;   // 25 Hz is plenty
    lastMs = now;
    float m = STATUS_LED_MAX;
    uint8_t nr = 0, ng = 0, nb = 0;
    if (!signalPresent) {
      nr = (uint8_t)m;
    } else {
      float t = throttle < 0 ? 0 : (throttle > 1 ? 1 : throttle);
      ng = (uint8_t)(m * (0.25f + 0.55f * t));
      nb = (uint8_t)(m * t);
    }
    write(nr, ng, nb);
  }

 private:
  uint32_t lastMs = 0;
  uint8_t cr = 255, cg = 255, cb = 255;   // impossible first value, so the first write always happens

  void write(uint8_t r, uint8_t g, uint8_t b) {
    if (r == cr && g == cg && b == cb) return;
    cr = r; cg = g; cb = b;
    neopixelWrite(PIN_STATUS_RGB, r, g, b);   // arduino-esp32: RGB order, handled for the WS2812
  }
};

#else

class StatusLed {
 public:
  void begin() {}
  void update(bool, float) {}
};

#endif
