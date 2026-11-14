# User sounds: what a sample must meet

Plan for the future (2026-11-08, sets decided 2026-11-14), not implemented. The firmware would load sound sets from
files in the flash data partition, uploaded over USB by a PC tool (see "Later" in `roadmap.md`). This page says how
the sets are organised and what a sample has to meet so it sounds right on the module. The numbers come from the current firmware (`engine_lab`) and the
speaker measurement (`speaker-measurement.md`).

## One kind of set (decided 2026-11-14)

There are no separate "built-in" and "user" sets. **Every set is a set of files in the data partition**, and the BOOT
button steps through the sets found there:

- **Every set is complete** (decided 2026-11-14): it holds all its sounds (idle and loaded loop, start, stop, horn,
  shift) and its spoken name. Sets do not borrow sounds from each other or from the firmware, so a set can be copied,
  deleted or replaced on its own; sounds that several sets share (for example the same horn) are simply stored in
  each of them.
- **Default sets**: for now all seven `engine_lab` candidates (decided 2026-11-14). They are written to the data
  partition when a module is flashed the first time. To the user they are ordinary sets: they can be deleted,
  replaced or reordered like their own.
- **Two types of set** (decided 2026-11-14): a **sample** set plays its engine from the loops `idle.wav` and
  `loaded.wav`; a **synth** set makes its engine in real time from combustion grains, so it has no engine loops,
  only the synth parameters in `set.json` (see "Types of set"). Everything else (name, start, stop, horn, shift) is
  WAV files in both types.
- **One fallback set is compiled into the firmware** and is used only when the data partition is empty or damaged
  (for example after a failed upload), so the module never stays silent. It is not in the list the BOOT button steps
  through.

Why: one kind of set keeps the firmware and the controls simple, a firmware update (also over OTA) does not touch the
sounds, and an upload of sounds does not touch the firmware. The sounds take about 0.8 MB of the firmware today
(engine samples about 355 kB, voice prompts about 480 kB); with most of them moved out, the app slots can shrink and
the data partition can grow (see "Size"). Cost: the partition table changes once, so every module is flashed
completely once more (firmware and default sets); after that firmware and sounds are uploaded separately.

Size of a set, estimated from the truck set: idle loop 234 kB, loaded loop 84 kB, start (1.1 s cranking and the
catch) and stop (1.4 s) about 120 kB together, horn about 25-45 kB, shift 15 kB, name about 70 kB. A sample set is
about 0.55-0.6 MB, a synth set (no loops) about 0.25-0.3 MB. The seven default sets (two sample, five synth) are
about 2.5 MB, so they need the larger data partition (see "Size").

## Types of set

**Why two types.** In a synth set every firing of a cylinder starts a short combustion grain of fixed timbre; the rpm
changes only how often the grains come, as in a real engine (more bangs per second, the exhaust and the block keep
resonating at the same frequencies), and every firing differs a little (four grain variants). A loop played faster
raises everything like a tape played fast: at full throttle (3.0x) a resonance at 400 Hz moves to 1200 Hz, and the
loop repeats the same pattern every few seconds. Rendering the synth candidates into loops would lose exactly what
they were tuned for, so they stay synthesised.

| | Sample set | Synth set |
|---|---|---|
| Engine sound | `idle.wav` and `loaded.wav`, played faster with the throttle | made in real time by the firmware; `set.json` names the synth and its preset |
| Other files | `name.wav`, `start.wav`, `stop.wav`, `horn.wav`, `shift.wav` | the same |
| Made by | the user (any recording) or `make_default_sets.py` | `make_default_sets.py`; the user can only change the parameters |
| Default sets | 01, 02 | 03-07 |

The synths and their grain data stay in the firmware (the grains and presets of `engine_synth2.h` are about 60 kB,
the old grain synth is smaller); a synth set only chooses one and sets its parameters. A new synth or preset
therefore comes with a firmware update, while a sample set can be made by anyone.

`set.json` of a synth set, for example:

```json
{ "name": "V eight", "type": "synth", "synth": "synth2", "preset": "v8", "eq": [[1.1087, -2.2174, 1.1087, -1.9274, 0.9289], ...],
  "level": 1.0, "gearbox": true }
```

**Speaker EQ (decided 2026-11-14): part of the sound, not a parameter.** A sample set has the EQ baked into its WAVs
(`02_truck_eq` is its own copy of the truck loops, run through the EQ by `make_default_sets.py`); the firmware plays
sample sets without an EQ of its own. A synth set carries its EQ in `set.json` (the filter coefficients, today
`LAB_EQ`), because the synth runs live and its EQ comes after the soft clipper; the copy is small, so each synth set
simply has its own.

## The PC tool

Decided 2026-11-08 as a plan, in two steps that use the same set format:

1. **A Python script in `tools/`** first, as our working tool: converts the WAVs, helps find the loop point, writes the
   parameter file and uploads the set over USB. Used to settle the set format and the firmware side.
2. **A web page for users** (for example on GitHub Pages), so nothing has to be installed. Chrome and Edge reach the
   Zero over USB with Web Serial. On the page: drop in WAVs, listen to the loop and adjust its ends, set the
   parameters, make the name sample with the browser's text-to-speech (or record it), and upload the set. With
   esptool-js the same page could also flash firmware updates.

## Format on the module

| Item | Value | Why |
|---|---|---|
| Container | WAV, PCM (no MP3, no compression) | the firmware plays raw samples; decoding costs CPU and adds latency |
| Sample rate | 22 050 Hz | the output rate of the firmware (`AUDIO_RATE`); the speaker plays nothing useful above about 8 kHz |
| Bit depth | 16 bit signed | what the firmware mixes; 8 bit is audibly noisy |
| Channels | mono | one speaker; a stereo file would be mixed down |

The PC tool would accept any common WAV (44.1 / 48 kHz, 24 bit, stereo) and convert it, so the user does not need to
prepare this exact format.

## Size

- One second costs 44.1 kB (22 050 samples x 2 bytes).
- The data partition has 1.5 MB today, so about **35 s of sound in total**, for all sets together (minus a little for
  the file system and the parameter files). With the sounds moved out of the firmware (see "One kind of set") the
  two OTA app slots can be smaller and the data partition can grow to about 4-5 MB, about 100 s of sound; the new
  partition table is to be worked out with the firmware's real size.
- For comparison, the built-in truck set: idle loop 5.3 s (234 kB), loaded loop 1.9 s (84 kB), shift sound 0.35 s
  (15 kB). One engine set of this kind is about 0.3-0.4 MB, so three to four sets fit.

## Files of a set

A set is one folder in the data partition, `/sets/<order>_<id>/`, for example `/sets/01_truck/`. The two-digit
number gives the order in which the BOOT button steps through the sets; `<id>` is a short name of lower-case
letters, digits and underscores. The files inside always have the same names, so the firmware needs no list of them:

| File | What it holds | How it is played | Length |
|---|---|---|---|
| `set.json` | the parameters of the set (see "Parameters of a set") and its name as text for the PC tool | - | - |
| `name.wav` | the spoken name of the set, for example "Truck" (no number: the order can change) | once, when the set is chosen with BOOT | about 1-2 s |
| `idle.wav` | the engine at idle (sample sets only) | loop; sped up with the throttle (1.0x..3.0x) | 1-6 s, a whole number of engine cycles |
| `loaded.wav` | the same engine under load (sample sets only) | loop, blended in with the throttle | 1-3 s |
| `start.wav` | starter cranking and the engine catching, ending at idle | once, when the ignition switch leaves OFF; `idle.wav` follows | about 1.5-3 s |
| `stop.wav` | the engine winding down to silence | once, when the ignition switch goes back to OFF | about 1.5-2 s |
| `horn.wav` | the horn | loop, as long as the horn control is held, so it must loop cleanly like the engine | 0.3-1 s |
| `shift.wav` | the gear-change sound | once, on every upshift of the virtual gearbox | under 0.5 s |

Every file is required (decided 2026-11-14: every set is complete), except that a synth set has no `idle.wav` and
`loaded.wav`. The PC tool refuses a set with a file missing.
All WAVs in the format of "Format on the module".

## Directory structure

**On the module** (the data partition, LittleFS; the `spiffs` partition of `default_8MB.csv` today, 1.5 MB):

```
/
├── sets/
│   ├── 01_truck/
│   │   ├── set.json
│   │   ├── name.wav
│   │   ├── idle.wav
│   │   ├── loaded.wav
│   │   ├── start.wav
│   │   ├── stop.wav
│   │   ├── horn.wav
│   │   └── shift.wav
│   ├── 02_truck_eq/
│   │   └── ... (the same eight files)
│   ├── 03_pulse_old/        synth set: the same files without idle.wav and loaded.wav
│   │   └── ...
│   └── ... 07_v12/
└── state.json        the number of the set chosen last, so the module starts with it after power-up
```

The firmware lists `/sets/` at start-up, sorts the folders by name and skips a folder with a file missing (it
reports which one over USB serial). The PC tool uploads a set into a temporary folder and renames it when every
file has arrived, so a broken upload never leaves a half set in the list.

**In the repo:**

```
assets/
├── samples/                 the CC0 recordings, as now (LICENSE-SAMPLES.md)
└── sets/                    sources of the default sets, one folder per set, same layout as on the module
    ├── 01_truck/
    │   └── set.json         parameters, and for each WAV where it comes from (a recording, a render, text-to-speech)
    └── ...
tools/
├── make_default_sets.py     builds the WAVs of the default sets from assets/ (renders, EQ, text-to-speech)
└── sound_upload.py          the PC tool, step 1: checks and converts WAVs, uploads a set over USB
firmware/
└── data/                    generated by make_default_sets.py, not committed: the image of the data partition,
    └── sets/...             written with `pio run -t uploadfs`
```

The WAVs are built, not committed (about 2.5 MB that a script can make again), like the STL files of the printed
parts. Only `set.json` and the sources are in git.

## Default sets

For now all seven `engine_lab` candidates (decided 2026-11-14), in their current order and with their current
numbers.

| Folder | Type | Spoken name | Engine | `start.wav`, `stop.wav`, `horn.wav` | `shift.wav` |
|---|---|---|---|---|---|
| `01_truck` | sample | "Truck" | `idle.wav`, `loaded.wav`: the CC0 truck loops (`engine_truck`, `assets/samples/`) | rendered from today's synthesis (`engine_events.h`) | the CC0 shift sound (`shift_sound.h`) |
| `02_truck_eq` | sample | "Truck with EQ" | the same loops through the speaker EQ for the 30 ml box | as 01 | as 01 |
| `03_pulse_old` | synth | "Old synth" | the old grain synth (`engine_pulse`), preset a_diesel6 | as 01 | as 01 |
| `04_diesel` | synth | "Diesel" | the speaker-tuned synth (`engine_synth2.h`), preset diesel | as 01 | as 01 |
| `05_petrol4` | synth | "Petrol, four cylinder" | the same synth, preset petrol4 | as 01 | as 01 |
| `06_v8` | synth | "V eight" | the same synth, preset v8 (cross-plane) | as 01 | as 01 |
| `07_v12` | synth | "V twelve" | the same synth, preset v12 | as 01 | as 01 |

The start, stop, horn and shift sounds are the same in all seven sets today (stored seven times, see "One kind of
set"); they can be made to suit each engine later. The spoken names are made with the same text-to-speech as today
(`tools/make_voice_prompts.ps1`, Piper, voice en_US-ljspeech), without the numbers the current prompts start with.

## The loop

The idle (and loaded) loop is played over and over, so its end must join its start without a click:

- Recorded at **steady rpm**: no revving, no gear change, no starter, no voice or wind in the loop.
- **Cut at the same point of the engine cycle** at both ends, ideally a whole number of firing cycles (an inline-6
  four-stroke fires 3 times per crank revolution, a V8 4 times). Cut near a zero crossing.
- **No fade-in or fade-out** in a loop (that would be heard as a dip every lap). One-shot sounds, on the other hand,
  should have a short fade-out (about 50 ms) so they do not end with a click.
- Steady level over the whole loop; a loop that gets louder towards the end pumps on every repeat.

The PC tool could help: find a good loop point automatically and let the user listen to the loop on the PC before
uploading.

## Sound content

- **Playback rate:** the firmware speeds the loop up from 1.0x at idle to 3.0x at full throttle (the pitch rises with it).
  So the loop should be recorded at **idle or low rpm**; a loop recorded at high rpm sounds like a racing engine at idle
  and unnaturally high at full throttle.
- **Bass:** the 40 mm speaker plays nothing useful below about 200 Hz and distorts strongly below about 300 Hz. The
  character of the engine has to be audible above that (the firing rhythm, the mid-range rasp); a deep rumble alone
  sounds like silence. A high-pass filter around 150-200 Hz in the tool removes energy the speaker only turns into
  distortion.
- **Level:** normalised to a peak of about -1 dBFS, no clipping. The master volume (`MASTER_VOLUME`) is applied in the
  firmware; the sets should have about the same loudness, so switching sets does not jump in volume.
- **Noise:** a quiet recording; background noise gets louder and higher with the playback rate.

## Parameters of a set

`set.json` beside the WAVs (JSON):

| Parameter | Meaning | Default |
|---|---|---|
| name | shown in the PC tool; spoken on the module only through `name.wav` (see below) | - |
| type | `sample` or `synth` (see "Types of set") | sample |
| synth, preset | synth sets only: which synth of the firmware and which of its presets | - |
| eq | synth sets only: the speaker EQ as biquad stages (b0 b1 b2 a1 a2); sample sets have it in their WAVs | none |
| rate range | sample sets: playback rate at idle and at full throttle | 1.0x..3.0x |
| loaded rate scale | sample sets: extra speed of the loaded loop when its firing rate is lower than the idle loop's | 1.18 (`LOADED_RATE_SCALE`) |
| loaded gain | sample sets: level of the loaded loop against the idle loop | 0.8 (`LOADED_GAIN`) |
| level | volume of the set | 1.0 |
| gearbox | use the virtual gearbox and the shift sound | on |

## Announcing the set

When the BOOT button switches sets, the module now speaks the name of the built-in sound (`voice_prompts.h`). With all
sets in the data partition, **the name is one of the files of the set** (`name.wav`), played when the set is chosen.
The user can record it, or the PC tool can make it with text-to-speech from the set's name. The default sets get
their names this way too (the current voice prompts move into them). Every set has a name file, so the beeps are
only a fallback for a damaged file. The PC tool shows the sets in the order of their folder numbers.

## Making the name (`name.wav`)

The name is announced once, when the set is chosen, so it only has to be short and clear on a 40 mm speaker.

**What makes a good name sample:**

- One to three words, about 1-2 s: "Truck", "V eight", "Detroit sixty". No number (the order of the sets can
  change) and no "set" or "sound" around it.
- Spoken a little slower and more clearly than normal speech. Consonants carry the words on a small speaker; a deep
  voice loses most of its body below about 300 Hz.
- No silence at the start or the end (cut it off), a fade of about 10 ms at both ends so it does not click, peak at
  about -1 dBFS like the engine sounds. A quiet background: the speaker makes noise louder, not softer.
- Then the usual format: 22 050 Hz, 16 bit, mono (the PC tool converts any WAV).

**Three ways to make it:**

1. **Text-to-speech with Piper** (how the default sets get their names): the same open voice as today's prompts,
   en_US-ljspeech (trained on LJ Speech, public domain). The user runs piper.exe themselves (it is a downloaded
   binary):
   `echo "V eight." | piper.exe --model en_US-ljspeech-medium.onnx --output_file name.wav`.
   `tools/make_default_sets.py` does this for the default sets (it replaces `make_voice_prompts.ps1`; the texts
   are in each set's `set.json`). Piper has voices in other languages too, Czech among them (cs_CZ-jirka); check the
   licence on the voice's model card before a voice goes into the default sets.
2. **Own recording**: a phone or a PC microphone, a quiet room, about 20 cm from the mouth. In Audacity: record,
   Effect > Normalize to -1 dB, cut the silence at both ends, Effect > Fade In / Fade Out on the first and last
   10 ms, File > Export > WAV. The PC tool converts the rest.
3. **On the web page (step 2 of the PC tool)**: type the name and the page speaks it. Piper also runs in the browser
   (WebAssembly), so the same voices work there without installing anything. The browser's own speech
   (Web Speech API) is simpler but uses the voices of the operating system, whose licences for redistributed
   recordings are unclear (the reason Windows TTS was not used for the prompts, 2026-11-05); it would be fine only
   for a name that stays on the user's own module. Recording through the microphone in the page is the other
   option.

The PC tool plays the name through a model of the speaker (`tools/speaker_model.py`) before uploading, so it can be
checked by ear first.

## Licence

Sounds the user uploads stay on their module and do not go into this repo, so the CC0 rule of the repo does not apply
to them; their licence is the user's responsibility. The default sets that come with the firmware stay CC0 as now
(`assets/samples/LICENSE-SAMPLES.md`).
