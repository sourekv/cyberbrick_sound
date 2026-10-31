# Engine sound simulation

Simulation of the intended end result: what the `engine` firmware should sound like as the throttle changes.
It is rendered offline with the same algorithm as `firmware/src/engine/main.cpp` (loop `loop_2.wav`, smoothed RPM,
playback rate 0.7x-2.0x, volume rising with throttle).

- `engine_simulation_full.wav` - full range, roughly a 40 mm speaker.
- `engine_simulation_small_speaker.wav` - same, with an 800 Hz high-pass: a rough estimate for a tiny rectangular speaker.

Throttle profile (20 s): idle, ramp to full, hold, release, two quick blips, half throttle, back to idle.

Limits: this is a simulation, not a recording of real hardware. It does not include the amplifier, enclosure or real
speaker response. Regenerate with `python tools/simulate_engine.py` after changing the sample or constants.

## Pulse-based engine (`engine_pulse` firmware)

`tools/render_engine_pulse.cpp` compiles the same `firmware/include/engine_synth.h` that runs on the ESP32 and renders the throttle profile below (20 s). Files in `pulse/`:

| Preset | Firing rate idle..max | Character |
|---|---|---|
| `a_diesel6` | 30..100 Hz | slow, chugging diesel |
| `b_truck` | 40..130 Hz | medium truck |
| `c_fast` | 55..180 Hz | faster, lighter engine |

`*_small_speaker.wav` applies an 800 Hz two-pole high-pass, roughly what a 40 mm speaker does to the low end. Build: `g++ -O2 -std=c++17 -I firmware/include tools/render_engine_pulse.cpp -o render_engine_pulse`, run: `./render_engine_pulse <prefix> [idle_hz max_hz [volume]]`.
