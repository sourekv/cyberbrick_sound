# Engine sound research

Status: 2026-11-26. The current firmware is `engine_sets`. The seven candidates of the earlier `engine_lab` (section "Speaker-tuned candidates") are its default sound sets, and which one to use is the user's choice (2026-11-14). Until 2026-11-05 the default was the synthesised "a_diesel6" preset (`engine_pulse`). This page records what was tried and measured; what is open is in `roadmap.md`.

## Constraints that shape everything

- The speaker is small (40 mm prototype speaker, production candidates 21 mm). It reproduces almost nothing below about 300 Hz, and the bass of the 21 mm candidates starts around 800 Hz. Sound that lives below 150 Hz is nearly inaudible on it and mostly sounds like hiss.
- Playback is 22.05 kHz mono over I2S into a MAX98357A (the same sample is sent to both channels, because the amplifier outputs (L+R)/2).
- At the time of the first approaches the throttle was the only live input (servo pulse 977..1973 us, 50 Hz, centre about 1455 us; the sound follows the absolute deflection from centre in both directions). Since 2026-11-06 the module gets all transmitter channels (ignition, horn, the stick direction), see `controls.md`.
- RPM is smoothed in firmware (rises faster than it falls), so the sound follows the stick with some inertia.
- I could only measure the sounds offline (level, spectrum, loop seams). How they sound was judged by the project owner listening on the real speaker.

## Approaches tried

| # | Firmware env | Idea | Result |
|---|---|---|---|
| 1 | `engine` (first version) | CC0 loops from OpenGameArt (domasx2), pitch-shifted by playback rate | Almost pure 40-80 Hz tones (99.99 % of the energy below 500 Hz), nearly inaudible on the small speaker, hissy. Replaced. |
| 2 | `engine` | One synthesised firing-pulse loop (`tools/make_engine_synth.py`), played back 0.7x-2.0x | Audible, "less pretty but better heard". Changing the rate also shifts the timbre, so the sound tends toward a siren. |
| 3 | `engine_pulse` | Real-time synthesis: RPM only sets how often a short combustion grain is triggered; the grain's timbre stays fixed (`include/engine_synth.h`, grains from `tools/make_engine_grains.py`) | Deeper and "bubbly" diesel chug. Was the default until `engine_lab` (preset a_diesel6). |
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

## Speaker-tuned candidates (2026-11-05)

Based on the speaker measurement (`docs/speaker-measurement.md`: plays about 210 Hz to 8 kHz, +8 dB resonance at
450 Hz, a dip at 2-3 kHz, strong distortion below 300 Hz):

- `tools/speaker_model.py` turns any WAV into an approximate "as heard from the speaker" version: the measured
  response plus a rough model of the bass distortion. A listening aid, not a calibrated model.
- **Speaker EQ**: 4th-order high-pass at 260 Hz, -7 dB at 450 Hz, +4 dB at 2.5 kHz. Removes the energy the speaker
  cannot play and would only distort.
- **New grain synth** (`Synth2` in `tools/engine_lab.py`, `firmware/include/engine_synth2.h`): a firing pulse through
  exhaust-like resonances placed between 300 Hz and 4 kHz, band-pass combustion noise synchronous with the firing,
  then soft clip and the speaker EQ. The low engine pitch comes from the firing rhythm (the ear infers it), not from
  bass the speaker cannot play. Presets: `diesel` (28-105 firings/s), `petrol4` (26-190), `v8` (36-150, uneven
  cross-plane firing), `v12` (60-270, six even firings per revolution, short bright grains: a smooth howl). RPM from the virtual gearbox.
- Found on the way: the soft clipper at the end of the old `engine_pulse` synth creates difference tones at the
  firing rate (below 250 Hz), which the speaker only distorts. In the new synth the EQ comes after the clipper.
- `python tools/engine_lab.py OUT_DIR` renders all candidates (raw and as heard, same loudness);
  `python tools/make_engine_lab_header.py` writes `firmware/include/engine_lab_data.h` from the same source.
- Firmware `engine_lab`: all seven candidates in one build, the **BOOT button** on the Zero switches 1..7 and the module
  announces it: 1 truck, 2 truck with EQ, 3 old pulse synth, 4 diesel, 5 petrol4, 6 v8, 7 v12
  (added 2026-11-05 after the owner liked the V8 best). The announcement is spoken
  (English, Piper text-to-speech with the voice `en_US-ljspeech`, trained on the public-domain LJ Speech dataset)
  when `firmware/include/voice_prompts.h` exists; it is generated locally with `pwsh tools/make_voice_prompts.ps1
  -Piper <piper folder> -Model <en_US-ljspeech-medium.onnx>` and kept in git (the voice is licence-clean); without the header the module beeps the number.
- Firmware `engine_demo` (same source, `-DENGINE_LAB_DEMO=1`): needs no receiver; announces each sound in turn and
  plays it through the whole RPM range with the same 20 s throttle profile as the previews, then the next one, in a
  loop. BOOT skips to the next sound.

## Lessons

- Do not pitch-shift a recording to follow RPM: it moves the timbre as well. Trigger fixed-timbre grains at a rate set by RPM instead.
- Check the spectrum before using any sample: it must contain energy above about 300 Hz for a 40 mm speaker.
- Recordings of a single steady idle have too little RPM information for a throttle-driven sound; real multi-RPM loops (or a recording with a clean RPM sweep) would be needed.

## Open questions and ideas

Moved to `roadmap.md` ("Sound features not done yet" and "To check on hardware"). The start-up and stop sounds
once listed here exist now (synthesised, `start-stop-horn.md`).
