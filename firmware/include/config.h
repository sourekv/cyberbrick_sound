#pragma once
// Pin assignment for Waveshare ESP32-S3-Zero.
// PROPOSED from the header labels on the board photo - VERIFY against the
// silkscreen on the real board before wiring.
// Deliberately avoided: GPIO0 (BOOT), GPIO3/45/46 (strapping), GPIO19/20 (USB),
// GPIO21 (onboard RGB LED), GPIO33-37 (octal PSRAM), GPIO43/44 (UART0).

#define PIN_THROTTLE_IN 1   // from receiver servo port signal, via ~1k series resistor
#define PIN_I2S_DOUT    4   // -> MAX98357A DIN
#define PIN_I2S_BCLK    5   // -> MAX98357A BCLK
#define PIN_I2S_LRC     6   // -> MAX98357A LRC

// Status colour on the Zero's onboard RGB LED (WS2812 on GPIO21), see include/status_led.h
#define STATUS_LED_ENABLED 1
#define PIN_STATUS_RGB    21
#define STATUS_LED_MAX    40  // 0..255 brightness limit; the LED is very bright

// Throttle pulse (microseconds)
#define PULSE_MIN_US     800
#define PULSE_MAX_US    2200
#define PULSE_CENTER_US 1475   // neutral (measured: full range 977..1973 us, stick at rest ~1455); throttle = |pulse - center| / RANGE
#define PULSE_RANGE_US   490
#define PULSE_DEADBAND_US 35   // rest value jitters 1445..1465 us
#define PULSE_TIMEOUT_MS 150   // no pulse for this long -> treat as idle

// Audio
#define AUDIO_RATE        22050
#define MASTER_VOLUME     0.6f    // 0..1; speaker is rated 2 W, amp can do ~3 W. Raise gradually.
