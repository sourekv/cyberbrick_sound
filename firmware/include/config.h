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

// Channel data from the receiver over a wire (include/rc_link.h, docs/cyberbrick-code/), on PIN_THROTTLE_IN as well.
// Used instead of the servo pulse while frames arrive; raw stick values 0..4095.
#ifndef RC_LINK_ENABLED
#define RC_LINK_ENABLED   1
#endif
#define RC_THROTTLE_MID   2020   // mid_value of the L Stick Y channel in the CyberBrick config (measured rest ~1830)
#define RC_THROTTLE_DEADZONE 250 // counts; the app uses 200, the measured rest is 190 from the mid
#define RC_LINK_TIMEOUT_MS 300   // no frame for this long -> back to the servo pulse
#define RC_STATE_HOLD_MS  2000   // engine on/off state survives a data gap this long (frames sometimes pause ~0.4 s)
// Start / stop / horn from the channel data (include/engine_events.h, docs/start-stop-horn.md)
#define RC_IGNITION_MID   1760   // left shoulder 3-position switch (L1): the middle position = ignition OFF
#define RC_IGNITION_BAND   800   // within this of the middle = OFF; both end positions (about 0 and 4089) = ON
#define RC_IGNITION_SETTLE_MS 250 // a new switch position must hold this long (passing the middle does not stop)
#define RC_HORN_REST      2260   // right shoulder stick (R1) at rest, measured
#define RC_HORN_THRESHOLD  800   // counts away from rest (either way) = horn

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

// Per-gear samples (`engine_gears` only, see include/gear_bank.h): playback rate range inside a gear (1.0 = as recorded)
// and the time constant of the crossfade between the samples of two gears.
#ifndef GEAR_RATE_LO
#define GEAR_RATE_LO      0.75f
#endif
#ifndef GEAR_RATE_HI
#define GEAR_RATE_HI      1.30f
#endif
#ifndef GEAR_XFADE_S
#define GEAR_XFADE_S      0.033f
#endif
// 1: announce the gear after every change with 1..GEAR_COUNT beeps (include/gear_beep.h), a test aid
#ifndef GEAR_BEEP
#define GEAR_BEEP         0
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
