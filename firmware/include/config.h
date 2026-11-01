#pragma once
// Pin assignment for Waveshare ESP32-S3-Zero.
// Checked against the official Waveshare pinout (https://docs.waveshare.com/ESP32-S3-Zero) and proven on the
// prototype: GP1 is the left header pin 4 (after 5V, GND, 3V3), GP4 / GP5 / GP6 are pins 7 / 8 / 9.
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
#define STATUS_LED_SWAP_RG 1  // 1: red and green are swapped on this board (seen on the real Zero), 0: normal order

// Throttle pulse (microseconds)
#define PULSE_MIN_US     800
#define PULSE_MAX_US    2200
#define PULSE_CENTER_US 1475   // neutral (measured: full range 977..1973 us, stick at rest ~1455); throttle = |pulse - center| / RANGE
#define PULSE_RANGE_US   490
#define PULSE_DEADBAND_US 35   // rest value jitters 1445..1465 us
#define PULSE_TIMEOUT_MS 150   // no pulse for this long -> treat as idle

// Virtual gearbox (see include/gearbox.h); used by the `engine` firmware family. Override with -D in platformio.ini.
#ifndef GEARBOX_ENABLED
#define GEARBOX_ENABLED   1
#endif
#ifndef GEAR_COUNT
#define GEAR_COUNT        5
#endif
#ifndef GEAR_SHIFT_DROP
#define GEAR_SHIFT_DROP   0.55f   // rpm (0..1) right after an upshift
#endif
#ifndef SHIFT_CUT_S
#define SHIFT_CUT_S       0.25f   // torque cut while shifting up, seconds
#endif
#ifndef SHIFT_CUT_GAIN
#define SHIFT_CUT_GAIN    0.15f   // volume factor during the cut
#endif
#ifndef GEAR_ACCEL_S
#define GEAR_ACCEL_S      6.0f    // virtual speed 0..1 at full throttle, seconds (without shifts)
#endif
#ifndef GEAR_DECEL_S
#define GEAR_DECEL_S      8.0f    // virtual speed 1..0 when the throttle is released, seconds
#endif

// Second loop "under load" (engine_truck only): played faster by LOADED_RATE_SCALE because its firing rate is
// lower (about 21 Hz against about 25 Hz of the idle loop), and scaled by LOADED_GAIN because it is louder.
#ifndef LOADED_RATE_SCALE
#define LOADED_RATE_SCALE 1.18f
#endif
#ifndef LOADED_GAIN
#define LOADED_GAIN       0.8f
#endif

// Audio
#define AUDIO_RATE        22050
#define MASTER_VOLUME     0.6f    // 0..1; speaker is rated 2 W, amp can do ~3 W. Raise gradually.
