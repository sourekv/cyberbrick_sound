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

## Real-recording engine (`engine_real` firmware)

Plays the start-up part of a user-supplied recording once, then repeats a seamless idle loop; RPM raises the playback rate by up to 40 % and the volume. The recording's origin and license are unknown, so it is **not** in the repository: generate the header locally with `python tools/make_user_sounds.py "<path to warm start.wav>"` (writes the git-ignored `firmware/include/user_sounds.h`), then `pio run -e engine_real -t upload`. Host preview: `g++ -O2 -std=c++17 -I firmware/include tools/render_engine_real.cpp -o render_engine_real && ./render_engine_real <prefix>`.

## Speaker-tuned candidates (`engine_lab` / `engine_demo` firmware)

Files in `lab/`, rendered by `python tools/engine_lab.py <out_dir>` with the same 20 s throttle profile and virtual
gearbox as the `engine_demo` firmware. The number is the sound's number in the firmware (BOOT switches them):

| File prefix | Sound (`tools/engine_lab.py` name) | Made from |
|---|---|---|
| `1_truck` | truck loops (`truck`) | CC0 recordings: truck idle (wesleywestmusic) and truck under load (kyles) |
| `2_truck_with_eq` | truck loops through the speaker EQ (`truck_eq`) | the same CC0 recordings |
| `3_old_pulse_synth` | the old `engine_pulse` synth (`pulse_old`) | synthesised, no recorded audio |
| `4_diesel` | new grain synth, diesel (`diesel`) | synthesised, no recorded audio |
| `5_petrol_4_cylinder` | new grain synth, four-cylinder petrol (`petrol4`) | synthesised, no recorded audio |
| `6_v8` | new grain synth, V8 (`v8`) | synthesised, no recorded audio |

Sources and licences of the recordings: `assets/samples/LICENSE-SAMPLES.md`.

`*_raw.wav` is what the firmware sends to the amplifier. `*_as_heard.wav` goes through `tools/speaker_model.py` (the
measured response of the 40 mm speaker plus a rough model of its bass distortion) and all of them are normalised to
the same loudness, so they can be compared directly. The tool writes its short names (`truck_raw.wav`, ...); the
files here were renamed to the numbered names above. See `docs/sound-research.md` for the background.
