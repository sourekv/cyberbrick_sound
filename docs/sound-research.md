# Engine sound research

Status: parked. The default sound is the synthesised "a_diesel6" preset (`engine_pulse` firmware). This page records what was tried, what was measured and what is still open, so the work can be resumed later.

## Constraints that shape everything

- The speaker is small (40 mm prototype speaker, production candidates 21 mm). It reproduces almost nothing below about 300 Hz, and the bass of the 21 mm candidates starts around 800 Hz. Sound that lives below 150 Hz is nearly inaudible on it and mostly sounds like hiss.
- Playback is 22.05 kHz mono over I2S into a MAX98357A (the same sample is sent to both channels, because the amplifier outputs (L+R)/2).
- Throttle is the only live input (servo pulse 977..1973 us, 50 Hz, centre about 1455 us; the sound follows the absolute deflection from centre in both directions). There is no key/ignition signal, so "engine stop" cannot be triggered from the stick alone.
- RPM is smoothed in firmware (rises faster than it falls), so the sound follows the stick with some inertia.
- I could only measure the sounds offline (level, spectrum, loop seams). How they sound was judged by the project owner listening on the real speaker.

## Approaches tried

| # | Firmware env | Idea | Result |
|---|---|---|---|
| 1 | `engine` (first version) | CC0 loops from OpenGameArt (domasx2), pitch-shifted by playback rate | Almost pure 40-80 Hz tones (99.99 % of the energy below 500 Hz), nearly inaudible on the small speaker, hissy. Replaced. |
| 2 | `engine` | One synthesised firing-pulse loop (`tools/make_engine_synth.py`), played back 0.7x-2.0x | Audible, "less pretty but better heard". Changing the rate also shifts the timbre, so the sound tends toward a siren. |
| 3 | `engine_pulse` | Real-time synthesis: RPM only sets how often a short combustion grain is triggered; the grain's timbre stays fixed (`include/engine_synth.h`, grains from `tools/make_engine_grains.py`) | Deeper and "bubbly" diesel chug. Chosen as the current default (preset a_diesel6). |
| 4 | `engine_real` | Start-up and an idle loop from a user-supplied recording | Pulsates and was not clearly better than the synthesised sound. Parked, see below. |

### Synthesised grain engine (`engine_pulse`)

- Firing rate runs from `ENGINE_FIRE_IDLE_HZ` to `ENGINE_FIRE_MAX_HZ` (default 30..100 Hz, preset **a_diesel6**; other presets rendered: b_truck 40..130 Hz, c_fast 55..180 Hz).
- Idle has a six-cylinder unevenness pattern and timing jitter that fade as the revs rise; pushing the throttle beyond the current RPM mixes in a brighter "crack" grain (load); a small noise bed grows with RPM.
- Grain content was shifted toward 600-1500 Hz so the small speaker can reproduce it.
- Output level was tuned to be comparable to the earlier loop (about 0.15 RMS at `MASTER_VOLUME` 0.6; the 800 Hz high-passed version about 0.05).
- Preview WAVs: `docs/audio-simulation/pulse/`, rendered from the same `engine_synth.h` by `tools/render_engine_pulse.cpp`.

### User-supplied recordings (`engine_real`)

Six recordings were supplied (cold start 20 s, warm start 10 s, pull-away 10 s, second pull-away 7.7 s, "Stop" 10 s, idle loop 1.1 s; 8-bit mono, 22.05 kHz except the idle loop at 44.1 kHz). **Origin and license are unknown**, so they are not in the repository (see `assets/samples/LICENSE-SAMPLES.md`).

Analysis:
- The steady parts of the start and "Stop" files have most of their energy at 400-1000 Hz and 1-2.5 kHz, which suits a small speaker.
- The idle-loop and pull-away files have 60-80 % of their energy below 150 Hz, so the small speaker plays them poorly.
- The pull-aways have no clean rising pitch, so they cannot be mapped to the throttle.
- The steady parts contain a regular amplitude wobble (period about 0.3 s to 1 s) that becomes audible pulsation once the part is looped, and the pulsation speeds up when the playback rate rises.
- "Stop" contains a 2 s fade-out followed by a steady idle section, not a shutdown at the end.

Implementation: `tools/make_user_sounds.py <warm start.wav>` trims the silence, searches a seamless loop (found: 4.6-7.4 s, seam correlation 0.41) and writes the git-ignored `firmware/include/user_sounds.h`; `include/engine_real.h` plays the start-up once, then loops with an equal-power crossfade and raises the playback rate by up to 40 % with RPM. Preview renderer: `tools/render_engine_real.cpp`.

## Lessons

- Do not pitch-shift a recording to follow RPM: it moves the timbre as well. Trigger fixed-timbre grains at a rate set by RPM instead.
- Check the spectrum before using any sample: it must contain energy above about 300 Hz for a 40 mm speaker.
- Recordings of a single steady idle have too little RPM information for a throttle-driven sound; real multi-RPM loops (or a recording with a clean RPM sweep) would be needed.

## Open questions and ideas

- Find recordings with a known free license (CC0), ideally steady loops at several RPM with mid-frequency content; or record one and extract grains from it, so the real timbre drives the grain engine instead of a synthesised one.
- A start-up sound at power-on, then handing over to the grain engine (the start part is short, so the pulsation does not matter).
- A stop sound needs another input (button or switch channel on the transmitter).
- Speaker comparison (40 mm prototype speaker vs. the production candidates) will change which frequencies matter; re-tune the grains afterwards.
- Possible tunable parameters: firing range, idle unevenness and jitter, load behaviour, RPM smoothing speeds, output gain and `MASTER_VOLUME`.
- Measure the current at the final volume and speaker (57 mA idle and 105 mA at full throttle were measured with `MASTER_VOLUME` 0.6 and the 40 mm speaker).
