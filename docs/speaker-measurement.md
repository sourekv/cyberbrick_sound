# Measuring the speaker

Status: 2026-11-08. The 40 mm prototype speaker was measured bare and in 30 ml and 15 ml sealed boxes; the speaker EQ
for the 30 ml box is in the firmware (built into `engine_lab`; in `engine_sets` the EQ `speaker_box` of a sound set). Choosing the speaker for the model is open (`roadmap.md`).

Generic speakers come without a datasheet, so the response is measured on the real hardware: the firmware
`speaker_sweep` plays a slow sine sweep through the MAX98357A and the speaker, a phone records it, and
`tools/analyze_speaker_sweep.py` turns the recording into a frequency response, a noise floor and the harmonic distortion.
What matters is where the speaker plays nothing (the bass cut-off), where it has a resonance, and where it distorts.
The result is also the basis for an "as heard from the speaker" preview of the engine sounds.

## What the firmware plays

`pio run -e speaker_sweep -t upload` (or RESET after it was uploaded). Timeline, about 2 minutes:

| Time | What happens | LED on the Zero |
|---|---|---|
| 0 to 15 s | countdown; three short beeps at 10, 11 and 12 s = the recording must be running by then | red |
| 15 to 45 s | sweep 1, logarithmic 100 Hz to 10 kHz | green |
| 45 to 48 s | silence | red |
| 48 to 78 s and 81 to 111 s | sweeps 2 and 3, each followed by 3 s of silence | green / red |
| 114 to 116 s | three longer beeps = finished, stop the recording | blue |

Peak level 0.25 of full scale (`-DSWEEP_LEVEL=...`), the same output path as the engine firmware (22.05 kHz, the same sample on
both channels). The other parameters: `-DSWEEP_F0_HZ`, `-DSWEEP_F1_HZ`, `-DSWEEP_SECONDS`, `-DSWEEP_RUNS`,
`-DSTART_DELAY_SECONDS` (the analysis script has the same options, `--f0 --f1 --seconds --runs`).

## How to record

1. Quiet room, no fan, window closed. The module is powered as in normal use (the amplifier needs its supply).
2. The speaker in the situation that is being judged: first the bare speaker on a table (baseline), later the same speaker in the
   model or its housing, because the housing changes the bass and the resonances a lot.
3. Phone about 5 cm in front of the middle of the speaker, on its axis, not moved during the recording and in the same place in
   all measurements. Do not hold it in the hand.
4. Voice recorder in the best quality available (WAV or lossless if possible; m4a or mp3 also works). Turn off noise
   suppression, voice enhancement and automatic gain if the app has them.
5. Start the recording **first**, then press RESET on the Zero (or upload). The three beeps at 10 to 12 s tell that the sweeps
   are about to start; the three long beeps at the end (and the blue LED) tell that it is over. Stop the recording after them.

## Analysis

`python tools/analyze_speaker_sweep.py recording.m4a --out speaker_baseline` writes `speaker_baseline.csv` and `.png` and
prints a summary: the range within -3 / -6 / -10 / -20 dB of the 1 to 3 kHz level, the strongest peak and deepest dip between
400 Hz and 8 kHz, second and third harmonic distortion at some frequencies, and where the signal is less than 15 dB above the
room noise. It needs numpy, scipy, matplotlib and ffmpeg. The script was tested on a simulated recording (filtered, distorted,
with noise and clock drift) before the first real measurement.

## Limits

- The result is the speaker **plus the microphone of the phone** (and the room, at 5 cm mostly the speaker). Phone microphones
  are fairly flat from about 100 Hz to 8 kHz, but they are not calibrated, so absolute levels mean nothing. Compare several
  speakers or housings measured in the same setup, do not read the numbers as the datasheet of the speaker.
- A very low level (the phone far away or the volume low) shows up as "less than 15 dB above the noise"; there the numbers
  are not reliable.
- The distortion values are for the signal level of the sweep (0.25 of full scale); the engine sound may be louder.

## Speaker impedance: 4 Ohm or 8 Ohm (2026-11-23)

The amplifier (MAX98357A) is made for 4 to 8 Ohm, so a 4 Ohm and an 8 Ohm speaker both work on the shield without any change of the board or the firmware. At the same drive voltage an 8 Ohm speaker gets half the power of a 4 Ohm one, so it plays about 3 dB quieter (for the same sensitivity); it also draws less current from the servo-port supply.

**The jumper JP1 is the way to get the level back without changing a part:** open (as delivered on rev A) the GAIN pin floats and the gain is 9 dB; bridged with a blob of solder it is 15 dB, 6 dB more, which is more than the 3 dB lost with an 8 Ohm speaker (`shield-pcb.md`, "GAIN and SD_MODE configuration"). JP2 stays bridged (it keeps the amplifier on). The other way is `MASTER_VOLUME` in `firmware/include/config.h` (0.6 at the moment, "raise gradually"); use it first, because it changes nothing on the board, and JP1 if the volume is still not enough.

![The solder jumper JP1 (gain) and JP2 on rev A](shield-jp1-gain.png)

**Example, an 8 Ohm speaker:** it plays about 3 dB quieter than the 4 Ohm one. Step 1: raise `MASTER_VOLUME` from 0.6 to about 0.85 (3 dB is a factor of 1.41 in amplitude, 0.6 x 1.41), flash the firmware and listen. Step 2, only if that is still too quiet or the volume is already at 1.0: bridge JP1 with a small blob of solder (the pair of pads in the picture, bottom left of J2), which adds 6 dB; then lower `MASTER_VOLUME` again to about 0.6 to 0.7, because 6 dB is a factor of 2 and the old value would be much too loud and may distort. Do not bridge JP2 or open it: it keeps the amplifier switched on.

Measured so far: only the 4 Ohm 40 mm speaker (below). An 8 Ohm speaker has not been measured.

## Results

### 2026-11-01: bare speaker (the 40 mm prototype speaker), phone 5 cm in front, quiet room

`docs/measurements/speaker_baseline_2026-11-01.csv` and `.png`. The recording had two sweeps (the first one started before the
recording, so its first 1.5 s are missing; the third did not play). Relative to the median level between 1 and 3 kHz:

- within -3 dB from 212 Hz to 8 kHz; the response falls steeply below that: about -20 dB at 150 Hz and below the noise at 130 Hz.
  A cut this sharp may come partly from the phone (microphone or app high-pass filter), a speaker alone usually rolls off more
  gently. Treat the bass limit as "at most about 200 Hz" until a second phone or a measurement in the housing confirms it.
- up to +8 dB around 450 Hz and +3 to +5 dB at 0.5 to 1.3 kHz, a dip of about -5 dB at 2 to 3 kHz, then flat to 8 kHz.
- strong distortion below about 300 Hz at this level (second and third harmonic only 9 to 11 dB below the fundamental, the third
  harmonic is stronger than the fundamental around 170 Hz); clean at 1 kHz (-39 dB and below), the third harmonic is
  -15 to -25 dB between 2 and 6 kHz.

### 2026-11-07: the same speaker in the 30 ml sealed box

`docs/measurements/speaker_box30_2026-11-07.csv` and `.png`, comparison with the bare speaker in
`speaker_box30_vs_bare_2026-11-07.png`. Box from `hardware/speaker_box` (OpenSCAD version, screw cap; the rim held only by the
cap, no plasticine under it; cable hole sealed with hot glue). Phone 5 cm in front, all three sweeps recorded.

| | bare speaker | 30 ml box |
|---|---|---|
| within -3 dB | 212 Hz to 8 kHz | 159 Hz to 4.3 kHz |
| within -6 dB | | 119 Hz to 7.2 kHz |
| 150 Hz | -22 dB | -6 dB |
| 200 / 300 / 450 Hz | -5 / -5 / +8 dB | +8 / +12 / +18 dB (peak +19 dB at 424 Hz) |
| 2nd / 3rd harmonic at 200 Hz | -9 / -16 dB | -25 / -39 dB |
| 2nd / 3rd harmonic at 300 Hz | -11 / -9 dB | -33 / -46 dB |

- The box removes the acoustic short circuit of the open back: the speaker now plays down to about 120 Hz instead of stopping
  at about 200 Hz. So the steep cut of the bare measurement was the speaker, not a high-pass in the phone.
- The air in the box also holds the cone back: distortion below 500 Hz falls by 15 to 35 dB.
- The price is a strong resonance hump, +12 to +19 dB from 300 to 500 Hz relative to 1 to 3 kHz (boomy), and a little less
  top (-5 to -7 dB around 5 kHz). The speaker EQ in the firmware (`SPEAKER_EQ` in `tools/engine_lab.py`: high-pass at 260 Hz,
  -7 dB at 450 Hz) was made for the bare speaker and needs a new version for the box.
- New speaker EQ for the box (`SPEAKER_EQ_BOX` in `tools/engine_lab.py`, now the default and in the firmware): high-pass
  at 140 Hz, -15 dB at 420 Hz, -6 dB at 315 Hz, +5 dB at 5.3 kHz, gain 1.15 for the same peak level as before. Fitted to
  this measurement (flat within about +-2 dB from 200 Hz to 5 kHz); listened to with `engine_demo` in the box on 2026-11-07:
  "dojem je dobrý" (a good impression). `tools/speaker_model.py` now previews the box by default (`SPEAKER=bare` for the old one).
- Not yet measured: the box with plasticine under the rim.

### 2026-11-08: the 15 ml sealed box

`docs/measurements/speaker_box15_2026-11-08.csv` and `.png`; comparison with the bare speaker and the 30 ml box in
`speaker_box15_vs_box30_2026-11-08.png`. Same speaker, same cap, phone 5 cm in front. The first recording was made before
the cable hole was sealed (`speaker_box15_unsealed_2026-11-08.csv` / `.png`); the second after sealing it with hot glue.

| | 30 ml box | 15 ml, cable hole open | 15 ml box (sealed) |
|---|---|---|---|
| within -3 dB | 159 Hz to 4.3 kHz | 178 Hz to 7.2 kHz | 178 Hz to 4.8 kHz |
| 150 Hz | -5 dB | -7 dB | -10 dB |
| 200 / 300 / 450 Hz | +8 / +12 / +18 dB | +3 / +6 / +15 dB | +4 / +8 / +18 dB |
| resonance peak | +19 dB at 424 Hz | +15 dB at 534 Hz | +18 dB at 449 Hz |
| 2nd / 3rd harmonic at 200 Hz | -25 / -39 dB | -18 / -4 dB | -32 / -37 dB |
| 2nd / 3rd harmonic at 300 Hz | -33 / -46 dB | -16 / -13 dB | -34 / -43 dB |

- **An open cable hole ruins the box**: with the hole open the distortion below 300 Hz was as bad as with the bare speaker
  (the 3rd harmonic even above the fundamental at 150 to 180 Hz) and the resonance moved up. Air pushed through the small
  hole is noisy and the box no longer holds the cone back. Sealing the hole fixed it. (The first guess, rattling solder
  tabs in the tight notch, was wrong; the notch was widened anyway, see `hardware/speaker_box`.)
- **Sealed, 15 ml is only a little worse than 30 ml**: above about 450 Hz the two boxes are nearly the same; below it the
  15 ml box gives 4 to 5 dB less (at 150 Hz -10 instead of -5 dB), the resonance is a little higher (449 instead of
  424 Hz). Distortion is about as low as in the 30 ml box.
- So the smaller box costs some low bass but works; the 30 ml box stays the better one where it fits. `SPEAKER_EQ_BOX` was
  fitted to the 30 ml box; with the 15 ml box it is close, with slightly less bass. A separate EQ was not made.
- **A foam disc (6 to 8 mm) on the bottom of the 15 ml box changes nothing**: the response stayed within the spread of two
  recordings (band means within 1 dB, single points within 2 to 4 dB), so there is no standing wave between the cone and
  the bottom worth damping. (The distortion below 300 Hz rose again in that recording, most likely a small leak after the
  box was opened; not followed up.) Recording not stored.
- **End of the box experiments (2026-11-08).** The box shape and filling are not worth more work. If the sound needs to
  get better later, the next step is a larger or different speaker, or a different amplifier / converter.
