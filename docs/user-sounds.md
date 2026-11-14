# User sounds: what a sample must meet

Plan for the future (2026-11-08, sets decided 2026-11-14), not implemented. The firmware would load sound sets from
files in the flash data partition, uploaded over USB by a PC tool (see "Later" in `roadmap.md`). This page says how
the sets are organised and what a sample has to meet so it sounds right on the module. The numbers come from the current firmware (`engine_lab`) and the
speaker measurement (`speaker-measurement.md`).

## One kind of set (decided 2026-11-14)

There are no separate "built-in" and "user" sets. **Every set is a set of files in the data partition**, and the BOOT
button steps through the sets found there:

- **Default sets**: for now all seven `engine_lab` candidates, each with its voice prompt (decided 2026-11-14;
  together about 0.85 MB, so they fit even the current 1.5 MB partition). They are written to the data partition
  when a module is flashed the first time. To the user they are
  ordinary sets: they can be deleted, replaced or reordered like their own.
- **One fallback set is compiled into the firmware** and is used only when the data partition is empty or damaged
  (for example after a failed upload), so the module never stays silent. It is not in the list the BOOT button steps
  through. It also supplies the one-shot sounds (start, stop, horn, shift) a set leaves out.
- Every set carries its own spoken name as a sample (see "Announcing the set"); beeps only for a set without one.

Why: one kind of set keeps the firmware and the controls simple, a firmware update (also over OTA) does not touch the
sounds, and an upload of sounds does not touch the firmware. The sounds take about 0.8 MB of the firmware today
(engine samples about 355 kB, voice prompts about 480 kB); with most of them moved out, the app slots can shrink and
the data partition can grow (see "Size"). Cost: the partition table changes once, so every module is flashed
completely once more (firmware and default sets); after that firmware and sounds are uploaded separately.

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

Suggested limits per file:

| Sound | Length | Notes |
|---|---|---|
| Idle loop (required) | 1-6 s | a whole number of engine cycles; longer sounds less repetitive, shorter saves space |
| Loaded loop (optional) | 1-3 s | the same engine under load; blended in with the throttle |
| Start, stop, horn, shift (optional, one-shot) | up to about 3 s each, shift under 0.5 s | played once; without them the fallback set's ones are used |
| Name (optional, one-shot) | about 1-2 s | the spoken name of the set, played when the set is chosen; without it the set number is beeped |

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

A small text file beside the samples (format to be decided, for example JSON):

| Parameter | Meaning | Built-in default |
|---|---|---|
| name | shown in the PC tool; spoken on the module only through the name sample (see below) | - |
| idle file, loaded file | which WAV is which | - |
| rate range | playback rate at idle and at full throttle | 1.0x..3.0x |
| loaded rate scale | extra speed of the loaded loop when its firing rate is lower than the idle loop's | 1.18 (`LOADED_RATE_SCALE`) |
| loaded gain | level of the loaded loop against the idle loop | 0.8 (`LOADED_GAIN`) |
| level | volume of the set | 1.0 |
| gearbox | use the virtual gearbox and the shift sound | on |

## Announcing the set

When the BOOT button switches sets, the module now speaks the name of the built-in sound (`voice_prompts.h`). With all
sets in the data partition, **the name is one of the samples of the set**: an optional short one-shot WAV (see the
table above) that the module plays when the set is chosen. The user can record it, or the PC tool can make it with
text-to-speech from the set's name. The default sets get their names this way too (the current voice prompts move
into them).

A set without a name sample is announced **by its number as beeps** (set 3 = three beeps), the way `engine_lab`
already does for a sound without a prompt. The order is the order in the PC tool, which shows the number next to each
set.

## Licence

Sounds the user uploads stay on their module and do not go into this repo, so the CC0 rule of the repo does not apply
to them; their licence is the user's responsibility. The default sets that come with the firmware stay CC0 as now
(`assets/samples/LICENSE-SAMPLES.md`).
