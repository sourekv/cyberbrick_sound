# Sound samples

## Overview: who made what, and what we owe them

All third-party sounds are CC0 (public domain), so no credit is legally required. Where the author asked for something,
or it is polite, it is in the last column; the details of each sound are in the sections below.

| Sound (files) | Source | Author | Licence | Credit and wishes |
|---|---|---|---|---|
| Engine loops (`loop_0.wav` .. `loop_5.wav`, early variants only) | [OpenGameArt: racing car engine sound loops](https://opengameart.org/content/racing-car-engine-sound-loops), cut from [start up car with seat belt warning beep](https://www.pdsounds.org/sounds/start_up_car_with_seat_belt_warning_beep) | domasx2; the source recording by Stephan (pdsounds.org, 2007) | CC0 | Thanks to domasx2 and Stephan |
| Diesel idle (`diesel_idle_loop.wav`) | [Freesound 500193](https://freesound.org/people/chlund/sounds/500193/) | chlund | CC0 | Thanks to chlund |
| Truck idle (`truck_idle_loop.wav`; the idle loop of the default sets `01_truck`, `02_truck_eq`) | [Freesound 680686](https://freesound.org/people/wesleywestmusic/sounds/680686/) | wesleywestmusic | CC0 | **Asks (not a condition) that users subscribe to his YouTube channel: [@WesleyWestMusic](https://www.youtube.com/@WesleyWestMusic)** |
| Truck under load (`truck_loaded_loop.wav`; the loaded loop of `01_truck`, `02_truck_eq`) | [Freesound 637914](https://freesound.org/s/637914/) | kyles | CC0 | Thanks to kyles |
| Per-gear loops (`gear_a_r03-29.wav`, `gear_b_r03-32.wav`) | Freesound [487151](https://freesound.org/s/487151/), [487152](https://freesound.org/s/487152/), pack [Vintage Trucks (Red Lib)](https://freesound.org/people/craigsmith/packs/27529/) | craigsmith (Red Library, digitised 1930s-40s optical sound effects) | CC0 | Thanks to craigsmith |
| Gear shift grind (`shift_grind.wav`, in every set) | [Freesound 438031](https://freesound.org/s/438031/) | craigsmith (a digitised copy of Hollywood sound effects, transferred by USC Cinema) | CC0 | Thanks to craigsmith and USC Cinema |
| Spoken names and numbers (`firmware/include/voice_prompts.h`, `web/number_names.js`, `name.wav` of the default sets) | made with [Piper](https://github.com/rhasspy/piper) and the voice `en_US-ljspeech-medium` ([model card](https://huggingface.co/rhasspy/piper-voices/tree/main/en/en_US/ljspeech/medium)), trained on the LJ Speech dataset | Piper: rhasspy; the voice: LJ Speech (public domain) | Piper MIT; voice public domain | Thanks to the Piper project and the LJ Speech dataset |
| Synthesised engines, starter, horn, test set (`assets/test_set/`, the synth presets) | made by this project's own code from formulas | this project | MIT (our own) | none |

Checked on the Freesound pages of all Freesound sounds and of the craigsmith pack on 2026-11-17: all show Creative Commons 0, and only wesleywestmusic asks for something.

Source: https://opengameart.org/content/racing-car-engine-sound-loops
Author: domasx2
License: CC0 (public domain)
Files: loop_0.wav .. loop_5.wav (differ in pitch only)
Origin (checked 2026-11-17 on the OpenGameArt page and on an archive.org copy of the source): the author made the loops for banditracer.eu by cutting a piece out of "start up car with seat belt warning beep" (Stephan, 2007-04-02, https://www.pdsounds.org/sounds/start_up_car_with_seat_belt_warning_beep), editing it into a loop and changing the pitch. pdsounds.org stated on every page "Recordings are in the public domain" (archive.org copy of 2012-01-02; the site is gone).
Note on the 2011 comment: the user qubodup pointed out on 2011-07-24 that sounds under cc-sampling-plus cannot be released as CC BY. The author replied the same day (15:28) "Remade these using a public domain sample"; the question concerned the earlier version of the loops, not the files now on the page. Remaining uncertainty: the public domain statement of pdsounds.org is a site-wide statement that can no longer be checked. Credit (not a condition): domasx2, and Stephan of pdsounds.org.

Download URLs:
- loop_0.wav https://opengameart.org/sites/default/files/loop_0.wav
- loop_1.wav https://opengameart.org/sites/default/files/loop_1_0.wav
- loop_2.wav https://opengameart.org/sites/default/files/loop_2_0.wav
- loop_3.wav https://opengameart.org/sites/default/files/loop_3_0.wav
- loop_4.wav https://opengameart.org/sites/default/files/loop_4_0.wav
- loop_5.wav https://opengameart.org/sites/default/files/loop_5_0.wav

## Diesel idle loop (used by the `engine_diesel` firmware)
Source: https://freesound.org/people/chlund/sounds/500193/
Author: chlund (Bergeforsen, Sweden)
License: CC0 1.0 (public domain dedication), http://creativecommons.org/publicdomain/zero/1.0/ , checked on the Freesound page on 2026-10-31
Original: "Diesel engine starting revving and stopping", Citroen Jumpy 2010 2.0 HDI, 18.08 s, 44.1 kHz stereo, recorded with a Zoom H1n. The original is not stored here.
Derived file: `diesel_idle_loop.wav` (2.09 s, 22.05 kHz mono), cut from the steady idle part with `tools/make_diesel_loop.py`; `tools/make_engine_diesel.py` turns it into `firmware/include/engine_diesel.h`.
Note: the same recording is also offered on Pixabay under the Pixabay licence; use the Freesound original (CC0).

## Truck idle recording (used by the `engine_truck` firmware)
Source: https://freesound.org/people/wesleywestmusic/sounds/680686/
Author: wesleywestmusic (recorded in Bellville, Western Cape, South Africa; uploaded 2023-03-27)
License: CC0 1.0 (public domain dedication); the licence on the Freesound page was checked on 2026-10-31 from a screenshot of the page supplied by the project owner, and again on the page itself on 2026-11-17 (CC0; the author's text asks only for the YouTube subscription)
Original: "Truck Revving Idling Engine Sound", 48 s, 48 kHz 16 bit stereo WAV, recorded and edited by the author in Logic Pro. The original is not stored here.
Derived file: `truck_idle_loop.wav` (5.34 s, 22.05 kHz mono), cut from the idle part from 10 s with `python tools/make_diesel_loop.py <original> assets/samples/truck_idle_loop.wav --start 10 --min 3 --max 6`; `tools/make_engine_diesel.py assets/samples/truck_idle_loop.wav firmware/include/engine_truck.h` turns it into the firmware header.
Content (own analysis): a steady idle of a larger diesel at about 8 crank revolutions per second (roughly 500 rpm, about 25 firing pulses per second), constant level from 2 s to 46 s, no real rev sweep; the first 2 s are louder and lower.
The author asks (not a licence condition) that users of his sounds subscribe to his YouTube channel: https://www.youtube.com/@WesleyWestMusic

## Truck "under load" loop (used by the `engine_truck` firmware as a second layer)
Source: https://freesound.org/s/637914/ ("truck big diesel engine work up a hill sustained rev and pass by2.flac")
Author: kyles (uploaded 2022-06-09)
License: CC0 1.0 (public domain dedication); checked on 2026-11-01 from a screenshot of the Freesound page supplied by the project owner, and again on the page itself on 2026-11-17 (CC0, no requests in the description)
Original: 25 s, 48 kHz mono FLAC, a big diesel truck working up a hill and passing by. The original is not stored here.
Derived file: `truck_loaded_loop.wav` (1.90 s, 22.05 kHz mono), cut from the louder approach part with `python tools/make_diesel_loop.py <original> assets/samples/truck_loaded_loop.wav --start 6.6 --min 1.5 --max 2.6`; `python tools/make_engine_diesel.py assets/samples/truck_loaded_loop.wav firmware/include/engine_truck_loaded.h ENGINE_LOADED` turns it into the firmware header.
Content (own analysis): the firing rate stays at about 21 Hz throughout (no real rev change), the level and brightness change because the truck passes; the loop seam is weak (match 0.22), so the repetition may be audible. Used only as a brighter, louder layer that is blended in with the throttle.

## Note: what the firmware actually uses
These loops are almost pure 40-80 Hz tones (99.99 % of the energy below 500 Hz). A 40 mm speaker cannot reproduce that, so the firmware now uses a synthesised loop generated by `tools/make_engine_synth.py` (original, no third-party audio). The CC0 loops are kept only for reference; `tools/make_sample.py` can still convert them.

## User-supplied recordings (origin and license unknown)
Six engine recordings were provided by the project owner for evaluation (mono, 8 bit; 22.05 kHz except the idle loop at 44.1 kHz):
- `volnoběh` (idle loop, 1.1 s)
- `studený start` (cold start, 20 s)
- `teplý start` (warm start, 10 s)
- `rozjezd` (pull-away, 10 s)
- `další rozjezd` (second pull-away, 7.7 s)
- `Stop` (10 s)

**We do not know where these recordings come from and their license is unknown.** Treat them as not cleared for redistribution: they are not committed to this repository and must not be published or included in a public release until the origin and license are established. Findings from the analysis (spectrum, structure) are in the project notes only.

## Per-gear loops (used by the `engine_gears` firmware)
Source: Freesound pack "Vintage Trucks (Red Lib)" by craigsmith, https://freesound.org/people/craigsmith/packs/27529/ (the Red Library: 1930s-40s nitrate optical sound effects made for Hollywood studios, digitised and cleaned of splices)
License: Creative Commons 0 (CC0 1.0); the pack's readme lists CC0 for every sound in it (checked 2026-11-01 from the readme of the pack download supplied by the project owner; on 2026-11-17 the Freesound pages of the pack and of both sounds show CC0 too, with no requests; the pack text only explains the Red Library and asks to "embrace the noise")
Used sounds (48 kHz mono, originals not stored here):
- https://freesound.org/s/487151/ "R03-29-Large Truck Constant Engine" (10.8 s) -> `gear_a_r03-29.wav` (5.00 s, 22.05 kHz mono): `python tools/make_gear_loop.py <original> assets/samples/gear_a_r03-29.wav --start 0.6 --end 6.6`
- https://freesound.org/s/487152/ "R03-32-Old Truck Engine Working Hard" (33.1 s) -> `gear_b_r03-32.wav` (7.00 s): `python tools/make_gear_loop.py <original> assets/samples/gear_b_r03-32.wav --start 5 --end 13`
Headers: `python tools/make_engine_diesel.py assets/samples/gear_a_r03-29.wav firmware/include/gear_a.h GEAR_A` (and `gear_b_r03-32.wav ... gear_b.h GEAR_B`).
Content (own analysis): old noisy optical recordings of a large old truck, a visible 60 Hz line (hum) below the range of the speaker, no reliable firing rate measurable; the loops are made seamless only by a 1 s crossfade, so a repetition may be audible, and the pitch of the two loops is not matched. Gear 1 uses the first loop and gears 2..5 share the second one while the sound is being chosen (see `firmware/include/gear_bank.h`).


## Synthesised sounds (no third-party audio)
The `engine_pulse` grain synth (`tools/make_engine_grains.py`, `firmware/include/engine_synth.h`), the earlier synthesised loop (`tools/make_engine_synth.py`) and the speaker-tuned grain synth with the presets `diesel`, `petrol4`, `v8` and `v12` (`tools/engine_lab.py`, `firmware/include/engine_synth2.h`, data in `firmware/include/engine_lab_data.h`) are generated entirely by this project's code from formulas. They contain no recorded audio, so no third-party licence applies.

## Voice prompts (used by the `engine_lab` / `engine_demo` firmware)
Text-to-speech: Piper (https://github.com/rhasspy/piper, MIT licence), voice `en_US-ljspeech-medium` (https://huggingface.co/rhasspy/piper-voices, en/en_US/ljspeech/medium), trained on the LJ Speech dataset, which its model card lists as public domain.
Generated file: `firmware/include/voice_prompts.h` (six short English prompts "One. Truck." .. "Six. V eight."; "Seven. V twelve." is in the script but the committed header still has six prompts until it is regenerated), made with `pwsh tools/make_voice_prompts.ps1` and `tools/make_voice_header.py` (resampled to 22.05 kHz, trimmed, high-passed at 250 Hz, normalised). Neither Piper nor the voice model is stored here.
Replaced the earlier Windows text-to-speech prompts (2026-11-05), because the licence of the Windows voices for redistribution was unclear.

## Gear-shift sound (used by `engine_lab`, all engine sounds)
Source: https://freesound.org/s/438031/ ("G13.1-04-Old Car Gearshift Grind.wav")
Author: craigsmith (uploaded 2018-08-26; a digitised copy of Hollywood optical and magnetic sound effects from the 1930s to the 1960s, transferred by USC Cinema)
License: CC0 1.0 (public domain dedication), checked on the Freesound page on 2026-11-08; the file was downloaded by the project owner.
Original: 72.3 s, 48 kHz 24 bit mono: an old car sputtering, many starts and stops, grinding and clanking, a voice in the background, some noise and hum. The original is not stored here.
Derived file: `shift_grind.wav` (0.35 s, 22.05 kHz mono), one grinding event without voice (event 21 of the 24 loud events, at 62.79 s, picked by ear by the project owner), high-passed at 200 Hz, faded and normalised, with `python tools/make_shift_sound.py <original>`; the same tool writes `firmware/include/shift_sound.h`.
