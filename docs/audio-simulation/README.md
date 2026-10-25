# Engine sound simulation

Simulation of the intended end result: what the `engine` firmware should sound like as the throttle changes.
It is rendered offline with the same algorithm as `firmware/src/engine/main.cpp` (loop `loop_2.wav`, smoothed RPM,
playback rate 0.7x-2.0x, volume rising with throttle).

- `engine_simulation_full.wav` - full range, roughly a 40 mm speaker.
- `engine_simulation_small_speaker.wav` - same, with an 800 Hz high-pass: a rough estimate for a tiny rectangular speaker.

Throttle profile (20 s): idle, ramp to full, hold, release, two quick blips, half throttle, back to idle.

Limits: this is a simulation, not a recording of real hardware. It does not include the amplifier, enclosure or real
speaker response. Regenerate with `python tools/simulate_engine.py` after changing the sample or constants.
