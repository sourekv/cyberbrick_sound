# Engine sound simulation

Offline renders of what the `engine` firmware should sound like, made with the same algorithm
(`firmware/src/engine/main.cpp`): loop `loop_2.wav`, smoothed RPM, playback rate 0.7x-2.0x, volume rising with throttle.

- `engine_demo_full.wav` - full range, roughly a 40 mm speaker.
- `engine_demo_small_speaker.wav` - same, with an 800 Hz high-pass: a rough guess for a tiny rectangular speaker.

Throttle profile (20 s): idle, ramp to full, hold, release, two quick blips, half throttle, back to idle.

This is not a recording of real hardware: no amplifier, enclosure or real speaker response. Regenerate with
`python tools/simulate_engine.py` after changing the sample or constants.
