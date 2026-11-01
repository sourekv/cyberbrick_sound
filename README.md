# cyberbrick_sound

Engine sound module for Bambu Lab CyberBrick RC. The module taps the throttle PWM signal from the receiver's servo port, plays a throttle-dependent engine sound through an I2S amplifier, and never interferes with the original signal.

## Status
Phase 1: prototype on a dev board (Waveshare ESP32-S3-Zero-N8R8-M + MAX98357A + 4 Ω speaker). A custom PCB comes only after the prototype works.

## Structure
- `firmware/` - PlatformIO (Arduino) project
- `docs/` - wiring, measurements, notes (sound research: `docs/sound-research.md`, shield PCB scope: `docs/shield-pcb.md`)
- `3d/` - cases, links
- `hardware/` - KiCad, later

## Wiring overview
![Wiring overview](docs/wiring-overview.png)

Stage 2 (powered from the CyberBrick servo port): `docs/wiring-stage2.png`.

Source: `docs/wiring-overview.svg`. Details and measurements: `docs/bringup.md`.

## Firmware plan
1. Test tone over I2S
2. Measure pulse width (50 Hz servo PWM) and print it to serial
3. Engine loop with smooth playback-rate change driven by throttle

## Sound samples
The firmware embeds `firmware/include/engine_sample.h`, a synthesised engine loop generated with:

    python tools/make_engine_synth.py

The CC0 loops in `assets/samples/` (see `LICENSE-SAMPLES.md`) are almost pure low tones that a small speaker cannot play, so they are kept only for reference (`tools/make_sample.py` converts them).

## Virtual gearbox
The `engine_diesel` and `engine_truck` firmware shift gears like a truck: the module only sees the throttle, so it keeps a virtual speed that follows the throttle with some inertia, derives the gear from it (5 gears) and plays the loop at a rate that rises within each gear. On an upshift the pitch drops and the sound is dimmed for a quarter of a second (torque cut); on a downshift the pitch jumps up. This is an effect, not a simulation: the sound does not follow the real speed of the model. Tune it in `firmware/include/config.h` (`GEAR_COUNT`, `GEAR_SHIFT_DROP`, `SHIFT_CUT_S`, `SHIFT_CUT_GAIN`, `GEAR_ACCEL_S`, `GEAR_DECEL_S`) or switch it off with `GEARBOX_ENABLED 0`. The logic is in `firmware/include/gearbox.h` and can be tested on a PC with `tools/test_gearbox.cpp`. Not tested on hardware yet.

`engine_truck` also blends in a second loop "under load" (brighter and louder, from a recording of a truck climbing a hill) as the throttle rises, on top of the idle loop. Level and pitch matching are in `firmware/include/config.h` (`LOADED_GAIN`, `LOADED_RATE_SCALE`). Not tested on hardware yet.

## Building
Open the `firmware/` folder in VS Code with the PlatformIO extension, or run `pio run -e <env> -t upload` with `<env>` one of `test_tone`, `pulse_measure`, `engine`, `engine_pulse` (default engine sound), `engine_diesel` and `engine_truck` (real diesel and truck idle loops, pitch-shifted; also show the status colours), `engine_real` (experiment, needs a locally generated header). See `docs/bringup.md`.

## Status LED
The `engine` and `engine_pulse` families show their state on the Zero's onboard RGB LED (GPIO21): a blue flash at start-up, **red** when no valid throttle pulse arrives (cable, port or receiver problem), **dim green** with the stick at rest and **cyan**, brightening with the throttle. Switch it off with `STATUS_LED_ENABLED` in `firmware/include/config.h`. On the tested Zero the red and green channels turned out to be swapped, which `STATUS_LED_SWAP_RG` (default 1) corrects; if your board shows the colours as described, set it to 0.
