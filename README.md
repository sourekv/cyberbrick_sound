# cyberbrick_sound

Engine sound module for Bambu Lab CyberBrick RC. The module taps the throttle PWM signal from the receiver's servo port, plays a throttle-dependent engine sound through an I2S amplifier, and never interferes with the original signal.

## Status
Phase 1: prototype on a dev board (Waveshare ESP32-S3-Zero-N8R8-M + MAX98357A + 4 Ω speaker). A custom PCB comes only after the prototype works.

## Structure
- `firmware/` - PlatformIO (Arduino) project
- `docs/` - wiring, measurements, notes
- `3d/` - cases, links
- `hardware/` - KiCad, later

## Firmware plan
1. Test tone over I2S
2. Measure pulse width (50 Hz servo PWM) and print it to serial
3. Engine loop with smooth playback-rate change driven by throttle

## Sound samples
See `firmware/data/samples/LICENSE-SAMPLES.md`.
