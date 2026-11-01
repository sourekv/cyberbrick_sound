# Measuring the speaker

Generic speakers come without a datasheet, so the response is measured on the real hardware: the firmware
`speaker_sweep` plays a slow sine sweep through the MAX98357A and the speaker, a phone records it, and
`tools/analyze_speaker_sweep.py` turns the recording into a frequency response, a noise floor and the harmonic distortion.
What matters is where the speaker plays nothing (the bass cut-off), where it has a resonance, and where it distorts.
The result is also the basis for an "as heard from the speaker" preview of the engine sounds.

## What the firmware plays

`pio run -e speaker_sweep -t upload`: three times 3 s of silence followed by a logarithmic sweep 100 Hz to 10 kHz in 30 s,
then 3 s of silence (about 105 s in total, serial monitor shows `sweep n / 3` and `done`). Peak level 0.25 of full scale
(`-DSWEEP_LEVEL=...`), the same output path as the engine firmware (22.05 kHz, the same sample on both channels).
The other parameters can be changed with `-DSWEEP_F0_HZ`, `-DSWEEP_F1_HZ`, `-DSWEEP_SECONDS` and `-DSWEEP_RUNS`
(the analysis script has the same options, `--f0 --f1 --seconds --runs`).

## How to record

1. Quiet room, no fan, window closed. The module is powered as in normal use (the amplifier needs its supply).
2. The speaker in the situation that is being judged: first the bare speaker on a table (baseline), later the same speaker in the
   model or its housing, because the housing changes the bass and the resonances a lot.
3. Phone about 5 cm in front of the middle of the speaker, on its axis, not moved during the recording and in the same place in
   all measurements. Do not hold it in the hand.
4. Voice recorder in the best quality available (WAV or lossless if possible; m4a or mp3 also works). Turn off noise
   suppression, voice enhancement and automatic gain if the app has them.
5. Start the recording, then press RESET on the Zero (the sweeps start after 3 s). Stop after about 110 s.

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
