# User sounds: what a sample must meet

Planned 2026-11-08, sets decided 2026-11-14. The firmware loads sound sets from files in the flash data partition,
uploaded over USB by a PC tool (see "Later" in `roadmap.md`).

**State 2026-11-15:** step 1 is built and works on the module (flashed with `upload` and `uploadfs` on 2026-11-15: boot, 7 sets found, `@hello`/`@info`/`@ls` answered, the web app connects, lists the sets, plays the sounds and runs the Demo (`@demo`), checked by the owner on 2026-11-15; Copy and Delete work too (the owner, 2026-11-15; Copy writes a new set, so writing sets from the app works); a set made from scratch is written too: the test set (`tools/make_test_set.py`, `assets/test_set/09_test/`) was saved to the module from the app (the owner, 2026-11-15); Speak (the name made with Piper) works too (the owner, 2026-11-15); not tried yet: recording the name with the microphone, how the module reacts when the port is opened; the first `uploadfs` stopped at 17 % with "The chip stopped responding", the second went through): the firmware env `engine_sets`
(`firmware/src/engine_sets/`, `firmware/include/sound_sets.h`), the partition table `firmware/partitions_sets.csv`
(two 1.5 MB app slots, 4.9 MB data partition), the default sets in `assets/sets/` and `tools/make_default_sets.py`.
The sets go to the module with `pio run -e engine_sets -t uploadfs`, or one by one with the web app
`web/index.html` over USB (built 2026-11-14, tried against its simulated module and on 2026-11-15 on the real one over USB; see "The web app"). The names are spoken with Piper (`--piper`, `--model`, run by the owner), the number first as in today's
prompts ("One. Truck."); without Piper the script falls back to those prompts. See "Trying it" at the end.

This page says how
the sets are organised and what a sample has to meet so it sounds right on the module. The numbers come from the current firmware (`engine_lab`) and the
speaker measurement (`speaker-measurement.md`).

## One kind of set (decided 2026-11-14)

There are no separate "built-in" and "user" sets. **Every set is a set of files in the data partition**, and the BOOT
button steps through the sets found there:

- **Every set is complete** (decided 2026-11-14): it holds all its sounds (idle and loaded loop, starter, horn,
  shift) and its spoken name. Sets do not borrow sounds from each other or from the firmware, so a set can be copied,
  deleted or replaced on its own; sounds that several sets share (for example the same horn) are simply stored in
  each of them.
- **Default sets**: for now all seven `engine_lab` candidates (decided 2026-11-14). They are written to the data
  partition when a module is flashed the first time. To the user they are ordinary sets: they can be deleted,
  replaced or reordered like their own.
- **Two types of set** (decided 2026-11-14): a **sample** set plays its engine from the loops `idle.wav` and
  `loaded.wav`; a **synth** set makes its engine in real time from combustion grains, so it has no engine loops,
  only the synth parameters in `set.json` (see "Types of set"). Everything else (name, starter, horn, shift) is
  WAV files in both types.
- **One fallback set is compiled into the firmware** and is used only when the data partition is empty or damaged
  (for example after a failed upload), so the module never stays silent. It is not in the list the BOOT button steps
  through.

Why: one kind of set keeps the firmware and the controls simple, a firmware update (also over OTA) does not touch the
sounds, and an upload of sounds does not touch the firmware. The sounds take about 0.8 MB of the firmware today
(engine samples about 355 kB, voice prompts about 480 kB); with most of them moved out, the app slots can shrink and
the data partition can grow (see "Size"). Cost: the partition table changes once, so every module is flashed
completely once more (firmware and default sets); after that firmware and sounds are uploaded separately.

Size of a set, estimated from the truck set: idle loop 234 kB, loaded loop 84 kB, starter (1.1 s) about 50 kB,
horn about 25-45 kB, shift 15 kB, name about 70 kB. A sample set is about 0.5 MB, a synth set (no loops) about
0.2 MB. The seven default sets (two sample, five synth) are about 2 MB, so they need the larger data partition
(see "Size").

## Start and stop (decided 2026-11-14)

- **Start:** `start.wav` holds **only the starter** cranking the engine. It plays when the ignition switch leaves OFF;
  its length is how long the engine cranks. Then the set's own engine (loop or synth) **catches by itself**: a short
  rev that settles to idle, as the firmware does today. So the catch always matches the engine of the set.
- **Stop: automatic, no file.** When the ignition switch goes back to OFF, the firmware pulls the rpm of the set's
  own engine down from wherever it is, fast at first and then slower, below idle, and fades it out (1.4 s; 0.35 s
  when the engine was still cranking). A stop from full throttle sounds different from one at idle, there is no seam
  between a recording and the engine, and it works for both types of set. `set.json` may set the length
  (`stop_s`).
- From a real start recording only the cranking is kept: it is the even "chug-chug" before the first firing, and the
  first firing is a sudden jump in level that is easy to see in the waveform. Cut just before it, fade out the last
  20-50 ms. The catch of the recording is not used.

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
| Other files | `name.wav`, `start.wav`, `horn.wav`, `shift.wav` | the same |
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

**Speaker EQ (decided 2026-11-14): part of the set, not a switch.** Every set carries its own EQ in `set.json`
(`"eq"`: the filter coefficients; a set without it plays without EQ), and the firmware runs it after the engine,
live. Live and not baked into the WAVs because the loops are played up to 3x faster: an EQ baked in would move up
with them (a cut at 420 Hz would sit at 1260 Hz at full throttle), while the speaker's resonance stays where it is.
So `02_truck_eq` uses the same loops as `01_truck` and differs only in its `eq`. The copy of the coefficients is
small, so each set simply has its own.

## The PC tool

Decided 2026-11-08 as a plan, in two steps that use the same set format. Changed 2026-11-14: the web page came
first, without the Python script (see "The web app" below); `tools/make_default_sets.py` stays for the default
sets. The module as a USB drive was considered as an alternative and dropped the same day (`rejected-ideas.md`).

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

A set is one folder in the data partition, `/sets/<index>_<description>/`, for example `/sets/01_truck/`
(decided 2026-11-14). The **first two characters are the index** (01..99): the order in which the BOOT button steps
through the sets. Everything after the underscore is a **free description for people looking at the files; the
firmware ignores it** (the set's name comes from `set.json` and `name.wav`). A folder without a two-digit index is
skipped; when two folders share an index, the firmware takes the first in alphabetical order and reports the other
over USB serial. The PC tool keeps the indexes unique and renumbers the folders when sets are reordered.
The files inside always have the same names, so the firmware needs no list of them:

| File | What it holds | How it is played | Length |
|---|---|---|---|
| `set.json` | the parameters of the set (see "Parameters of a set") and its name as text for the PC tool | - | - |
| `name.wav` | the spoken name of the set with its number in front, for example "One. Truck." (the number is part of the name) | once, when the set is chosen with BOOT | about 1-2 s |
| `idle.wav` | the engine at idle (sample sets only) | loop; sped up with the throttle (1.0x..3.0x) | 1-6 s, a whole number of engine cycles |
| `loaded.wav` | the same engine under load (sample sets only) | loop, blended in with the throttle | 1-3 s |
| `start.wav` | the starter cranking the engine, without the catch (see "Start and stop") | once, when the ignition switch leaves OFF; then the engine catches by itself | about 0.5-2 s |
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
│   │   ├── horn.wav
│   │   └── shift.wav
│   ├── 02_truck_eq/
│   │   └── ... (the same seven files)
│   ├── 03_pulse_old/        synth set: the same files without idle.wav and loaded.wav
│   │   └── ...
│   └── ... 07_v12/
└── state.json        the set the module starts with after power-up (the default; set by BOOT or by the app's Default)
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
web/
├── index.html               the PC tool: lists, plays, edits, copies, deletes and uploads sets over USB
└── demo_sets.js             generated, not committed: the default sets for the app's simulated module
tools/
└── make_default_sets.py     builds the WAVs of the default sets from assets/ (renders, EQ, text-to-speech)
firmware/
└── data/                    generated by make_default_sets.py, not committed: the image of the data partition,
    └── sets/...             written with `pio run -t uploadfs`
```

The WAVs are built, not committed (about 2 MB that a script can make again), like the STL files of the printed
parts. Only `set.json` and the sources are in git.

## Default sets

For now all seven `engine_lab` candidates (decided 2026-11-14), in their current order and with their current
numbers.

| Folder | Type | Spoken name | Engine | `start.wav`, `horn.wav` | `shift.wav` |
|---|---|---|---|---|---|
| `01_truck` | sample | "One. Truck." | `idle.wav`, `loaded.wav`: the CC0 truck loops (`engine_truck`, `assets/samples/`) | rendered from today's synthesis (`engine_events.h`) | the CC0 shift sound (`shift_sound.h`) |
| `02_truck_eq` | sample | "Two. Truck with E Q." | the same loops through the speaker EQ for the 30 ml box | as 01 | as 01 |
| `03_pulse_old` | synth | "Three. Old synth." | the old grain synth (`engine_pulse`), preset a_diesel6 | as 01 | as 01 |
| `04_diesel` | synth | "Four. Diesel." | the speaker-tuned synth (`engine_synth2.h`), preset diesel | as 01 | as 01 |
| `05_petrol4` | synth | "Five. Petrol, four cylinder." | the same synth, preset petrol4 | as 01 | as 01 |
| `06_v8` | synth | "Six. V eight." | the same synth, preset v8 (cross-plane) | as 01 | as 01 |
| `07_v12` | synth | "Seven. V twelve." | the same synth, preset v12 | as 01 | as 01 |

The starter, horn and shift sounds are the same in all seven sets today (stored seven times, see "One kind of
set"); they can be made to suit each engine later. The spoken names are made with the same text-to-speech as today
(`tools/make_voice_prompts.ps1`, Piper, voice en_US-ljspeech), with the number in front like the current prompts.

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
| stop_s | how long the engine winds down after the ignition is switched off | 1.4 |
| gearbox | use the virtual gearbox and the shift sound | on |

## Announcing the set

When the BOOT button switches sets, the module now speaks the name of the built-in sound (`voice_prompts.h`). With all
sets in the data partition, **the name is one of the files of the set** (`name.wav`), played when the set is chosen.
The user can record it, or the PC tool can make it with text-to-speech from the set's name. The default sets get
their names this way too (the current voice prompts move into them). Every set has a name file, so the beeps are
only a fallback for a damaged file. The PC tool shows the sets in the order of their folder numbers.

**The default name is the number (decided and built 2026-11-15).** A new set on the web app gets `name.wav` with only
its number spoken, "One." to "Ninety nine.", from `web/number_names.js` (99 numbers, Opus in Ogg as base64, about
0.35 MB, committed; made by `tools/make_number_names.py` with the user's `piper.exe`, same voice as the default sets,
public domain, so the sounds are ours). Nothing is downloaded for it. The app keeps the sound in step with the number
while it is "number NN": choosing another number gives the new sound, and a set without any name sound gets its
number when it is written. The button "Number only" in the Name row puts the number back. A spoken name ("Eight.
Detroit sixty.") is still made with Speak (downloads Piper, see below), recorded, or chosen as a file; such a sound is
not replaced when the number changes, so it has to be made again then. A set opened for editing keeps the name sound it
has. The default sets keep their spoken names, made offline.

## Making the name (`name.wav`)

The name is announced once, when the set is chosen, so it only has to be short and clear on a 40 mm speaker.

**What makes a good name sample:**

- The number of the set, then one to three words, about 1-2 s: "One. Truck.", "Six. V eight.", "Eight. Detroit
  sixty.". The number is part of the name, so the owner hears where in the order the set is; it is the folder's
  index, and when a set moves to another index its `name.wav` has to be made again. No "set" or "sound" around it.
- Spoken a little slower and more clearly than normal speech. Consonants carry the words on a small speaker; a deep
  voice loses most of its body below about 300 Hz.
- No silence at the start or the end (cut it off), a fade of about 10 ms at both ends so it does not click, peak at
  about -1 dBFS like the engine sounds. A quiet background: the speaker makes noise louder, not softer.
- Then the usual format: 22 050 Hz, 16 bit, mono (the PC tool converts any WAV).

**Three ways to make it:**

1. **Text-to-speech with Piper** (how the default sets get their names): the same open voice as today's prompts,
   en_US-ljspeech (trained on LJ Speech, public domain). The user runs piper.exe themselves (it is a downloaded
   binary):
   `echo "Six. V eight." | piper.exe --model en_US-ljspeech-medium.onnx --output_file name.wav`.
   `tools/make_default_sets.py` does this for the default sets (it replaces `make_voice_prompts.ps1`; the texts
   are in each set's `set.json`). Piper has voices in other languages too, Czech among them (cs_CZ-jirka); check the
   licence on the voice's model card before a voice goes into the default sets.
2. **Own recording**: a phone or a PC microphone, a quiet room, about 20 cm from the mouth. In Audacity: record,
   Effect > Normalize to -1 dB, cut the silence at both ends, Effect > Fade In / Fade Out on the first and last
   10 ms, File > Export > WAV. The PC tool converts the rest.
3. **On the web app** (`web/index.html`): Record (the microphone) or Speak (type the name, Piper speaks it in
   the browser with the same voice as the default sets; see "The web app"). The browser's own speech
   (Web Speech API) is simpler but uses the voices of the operating system, whose licences for redistributed
   recordings are unclear (the reason Windows TTS was not used for the prompts, 2026-11-05); it would be fine only
   for a name that stays on the user's own module. Recording through the microphone in the app is the other
   option.

The PC tool plays the name through a model of the speaker (`tools/speaker_model.py`) before uploading, so it can be
checked by ear first.

## Licence

Sounds the user uploads stay on their module and do not go into this repo, so the CC0 rule of the repo does not apply
to them; their licence is the user's responsibility. The default sets that come with the firmware stay CC0 as now
(`assets/samples/LICENSE-SAMPLES.md`).

## The web app

`web/index.html` is one file without a build step or a server: open it in Chrome or Edge (from disk works, Web
Serial runs on `file:` pages), press "Connect module" and choose the module's USB port. It needs `engine_sets` on
the module.

**What the user needs** (for the user guide): a computer (Windows, macOS, Linux or ChromeOS) with **Chrome or Edge**
(version 89 or newer), and a USB-C cable. Only Chromium browsers have Web Serial. Safari and Firefox do not, and
neither does any browser on an iPhone or iPad; there the app says so and "Connect module" stays off. On a Mac,
installing Chrome is enough. Tested so far only in Edge on Windows.

- **User guide (2026-11-15):** `user-guide.md`, with pictures made by `tools/make_guide_images.py` (always the light
  look, whatever the system's colour setting is) and a panel "How to use" at the top of the app. The firmware
  version shows in the connection line and under the list (both confirmed on the real module by the owner,
  2026-11-15).
- **Default set (2026-11-15)**: the row of the set the module starts with after power-up is tinted and has a green
  "default" mark; the button "Default" on any other row makes it the default set (`@default`). Test only
  tries a set and does not change it; BOOT on the module does (it steps to the next set and remembers it). The small
  green dot is the set chosen on the module now. Renaming the default set keeps it the default.
- **On the module**: every set with its number, name, type and size, and the free space. "Test" chooses the set on
  the module, it speaks the name and plays a demo of about 25 s (below; this was "Demo", and a separate "Play" that
  only spoke the name was dropped on 2026-11-15 because users could not tell the two apart), "Edit" and "Copy" open it in the editor, "Delete" removes it after a question. Folders the module skips
  (no number, a number used twice, no `set.json`) are marked. Every Test and every Play of a sound on the app has a Stop beside it (on the module it sends `@stop`; checked on the module on 2026-11-15: it stops a running demo).
- **Test** (the demo): the name, ignition on (starter, the engine catches), the throttle profile of `engine_demo` from 2.5 s
  (idle, full throttle through the gears, release, two blips, half throttle, idle), the horn at 17 s, ignition off
  at 21.5 s and the wind-down. On the module (`@demo`) it runs in the firmware for every set, without a receiver;
  BOOT or the receiver's data end it. In the simulated module the app renders it for sample sets with a port of
  what the firmware does (EngineState, Gearbox, loops, EQ, starter, horn, shift), without the speaker; synth sets
  are made by the firmware and cannot be rendered in the browser, so their Test is off there, with a tooltip saying
  so.
- **Editor**: number (only free ones are offered), name, folder description, type (sample, or synth with its
  preset), the sounds and the parameters of `set.json`. A sound is dropped on its row or chosen; any format the
  browser can decode is converted to 22 050 Hz, 16 bit, mono. The name can also be recorded with the microphone;
  the app cuts the silence, adds 10 ms fades and sets the peak to -1 dB. Each sound can be heard in the browser,
  the loops looped and at any playback rate of the rpm range. Lengths outside the expected range, clipping and very
  quiet sounds are flagged, not refused. Speaker EQ: none, the 30 ml box, or the one already in the set, with a
  gain.
- **Write to the module** writes only the changed WAVs and `set.json`; a new number or description renames the
  folder first, and a set changed to synth loses its `idle.wav` and `loaded.wav`.
- **Copy** is the easy way to a new set: the starter, horn and shift come along and only the engine changes.
- **Simulated module**: the same protocol inside the app, for trying the app without hardware. It holds the
  seven default sets from `web/demo_sets.js` (2.8 MB of base64, written by `tools/make_default_sets.py`, or alone
  with `--demo-only`; generated, not committed); without that file, two small demo sets with beeps. Changes live
  only until the app is closed. `index.html#selftest` runs an automatic test against the two small demo sets
  (13 checks, all passing on 2026-11-14 in Edge).

- **Speak** (the Name row): the name made with [Piper](https://github.com/rhasspy/piper) text-to-speech in the
  browser through [piper-tts-web](https://github.com/Mintplex-Labs/piper-tts-web), the same voice as the default
  sets. The text starts as the number in words and the name ("Eight. Detroit sixty."), and can be changed. Nothing
  is loaded until the first Speak, and then only after a question that says what is downloaded and from where. The
  part "What is downloaded and used" under the box names the projects with links.

  *What the app loads, from third parties (checked on 2026-11-14 in the code of piper-tts-web 1.0.4):*

  | What | From | Licence |
  |---|---|---|
  | library `@mintplex-labs/piper-tts-web` 1.0.4 | cdn.jsdelivr.net | MIT (npm field; the package has no LICENSE file) |
  | phonemizer `@diffusionstudio/piper-wasm` 1.0.0 (0.6 MB wasm + 18 MB data) | cdn.jsdelivr.net | npm says MIT, but it is a build of Piper's phonemizer with eSpeak NG, **GPL 3 or later** (its README gives the build steps) |
  | ONNX Runtime Web 1.18.0 | cdnjs.cloudflare.com | MIT (not checked here) |
  | voice en_US-ljspeech-medium (about 63 MB) | `huggingface.co/diffusionstudio/piper-voices/resolve/main`, a copy of the Rhasspy voices, not pinned to a commit | public domain (model card: trained on LJ Speech) |

  The text is turned into speech on the computer, not sent anywhere. The result is 22 050 Hz, 16 bit, mono, then
  trimmed like any name. The browser's private storage (OPFS) is not available to a page opened from disk, so the
  voice is not stored for good: the browser's cache may keep it, otherwise it is downloaded again. Tested on
  2026-11-14 in Edge from `file://`: about 11 s the first time with the download, about 1.3 s after.

  *If a host or an author withdraws or changes a file:* Speak fails with a message and a line in the log; Record,
  Choose file and everything else keep working, and the names already made (the default sets, in git) are ordinary
  WAV files. The URLs are fixed inside the library, so changing them (a copy of the files, or a pinned voice) needs
  a patched copy of it.

  *Copying these files into this repository or its Pages* makes this project a distributor: the MIT parts need
  their licence texts and notices, the voice a mention of its source, and the phonemizer, which contains eSpeak NG
  (GPL 3 or later), its licence text and the corresponding source (or an offer of it) with the build steps and
  versions. Not done; until then nothing is redistributed, the browser fetches the files directly from their hosts.
  The Piper repository `rhasspy/piper` (MIT) was archived on 2025-10-06 and development moved to
  `OHF-Voice/piper1-gpl`; that project's licence has not been checked here.

Not on the app yet: help with the loop points, the user guide. Hosting on GitHub Pages needs the repo public or a paid plan; until then the file is opened from disk.

### The USB protocol

`firmware/include/set_link.h`, version 1. Text lines both ways over the USB serial port (115200 Bd, the rate does
not matter on USB), binary data as base64, so the firmware's log lines can share the port: the app reads only
lines starting with `@`. Every command ends with one line `@ok ...` or `@err <why>`, and the app sends the next
command only after it; that is the flow control (the ESP32-S3 USB driver drops bytes when its 8 kB receive buffer is
full).

| Command | Answer |
|---|---|
| `@hello` | `@ok cbsound 1` |
| `@info` | `@ok free=<bytes> total=<bytes> set=<folder or -> psram=<bytes> fw=<version> built=<date> default=<folder or ->`; the app shows the firmware version under the list and marks the default set |
| `@default <folder>` | `@ok`; the set the module starts with after power-up (written 2026-11-15, checked on the module); it does not change what is playing, and `@select` and `@demo` do not change it |
| `@ls` | `@set <bytes> <folder>` per folder in `/sets`, then `@ok <count>` |
| `@files <folder>` | `@file <bytes> <name>` per file, then `@ok <count>` |
| `@get <path>` | `@d <base64>` lines of up to 3072 bytes, then `@ok <size> <crc32>` |
| `@put <size> <path>` | `@ok`; then `@w <base64>` (up to 3072 bytes) -> `@ok <bytes so far>`, and `@end <crc32>` -> `@ok` |
| `@rm <path>` | `@ok` (a file, or a set folder with its files) |
| `@mv <from> <to>` | `@ok` |
| `@select <folder>` | `@ok`; ends the session, the set plays and speaks its name |
| `@demo <folder>` | `@ok`; the same, then the demo of about 25 s |
| `@stop` | `@ok`; ends the session and silences the name and the demo that are playing (the set stays chosen, the engine winds down); added 2026-11-15, the Stop button of every row uses it; an older firmware answers `@err unknown command` |
| `@bye` | `@ok`; ends the session |

`@put` writes to `<path>.tmp` and replaces the file only when the size and the CRC-32 (zlib) match, so a broken
transfer leaves the old file. Paths must be under `/sets/`. While the app talks to the module (a session: from the
first command until `@bye`, `@select` or 3 s without a command) the engine is silent, BOOT is ignored and the
firmware writes no log lines. When a session that changed files ends, the module scans `/sets` again and reloads
the current set without speaking its name; a set that is gone gives way to the first one.

Still to check on the module: that opening the port from the browser does not reset the Zero (the app retries
`@hello` for about 8 s, so a reset would only cost time), the transfer speed, and writing while the module runs
from the receiver.

## Trying it (step 1)

From the repo root, then from `firmware/`:

1. `python tools/make_default_sets.py` builds the seven default sets into `firmware/data/sets/` (about 2.1 MB). With
   `--piper <folder with piper.exe> --model <en_US-ljspeech-medium.onnx>` it also speaks the plain names (the user
   runs it, Piper is a downloaded binary).
2. `pio run -e engine_sets -t upload` flashes the firmware **and the new partition table**. The first time, the old
   data partition is gone, so the module plays the fallback (diesel synth) and beeps once until step 3.
3. `pio run -e engine_sets -t uploadfs` writes the sets (the whole data partition, about 5 MB, takes a while).
4. The serial monitor (115200 Bd) lists the sets found and every set loaded; BOOT steps to the next set, which
   speaks its name. After a power cycle the module starts with the set chosen last with BOOT, or with the default set of the web app.

Going back to `engine_lab` is just `pio run -e engine_lab -t upload` (it brings its own partition table).
Flash with the USB power rule in mind (`bringup.md`).
