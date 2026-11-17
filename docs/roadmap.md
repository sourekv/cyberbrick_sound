# Roadmap: what is open

Status: 2026-11-13. The one place for everything that is still open: decisions, checks on hardware and the plans for
later. The other documents describe what exists and link here for what is missing. Ideas that were dropped, with the
reasons, are in `rejected-ideas.md`.

## Next

| Item | Where | Notes |
|---|---|---|
| Choose the engine sound | `engine_lab`, `sound-research.md` | candidates are judged by ear on the real speaker |
| Shield: approve and receive | `shield-pcb.md` "Order of 2026-11-13" | ordered at JLCPCB on 2026-11-13 ([order number removed], 5 boards with basic parts, DHL Express, 84.41 USD paid incl. customs); to do: approve the production file and the parts placement when JLCPCB sends them (check where the tooling holes went), J1/J3/J4 and the servo cables ordered at GME on 2026-11-13; the first board gets the prototype's Zero and speaker, more are ordered once it works; speaker cables (IC007) ordered at Bambu Lab on 2026-11-13 (`shield-pcb.md` "Needed besides the board"); after delivery solder J1/J3/J4 and do the first checks below |
| Speaker for the model | `speaker-measurement.md` | 40 mm or a production candidate (for example 21 mm). The box is done (30 ml best, 15 ml close); more would come from another speaker or amplifier, not from the box |
| Enclosure for the model | - | designed from scratch around the chosen speaker; the printed box is a test fixture only |
| Long power test with the motor running | `bringup.md` | does the servo-port 5 V hold with the module and the motor together |

## To check on hardware

- **First shield boards:** voltages and currents with USB and the receiver connected at the same time (the OR-ing
  diode D2 should make this safe, `shield-pcb.md` "Decided"); whether the Zero's underside is flat enough for the
  parts under it (about 7 mm of clearance).
- **MAX98357A at 22.05 kHz:** the datasheet does not list 22.05 kHz as a supported sample rate, yet the prototype
  plays fine at it. Keep an eye on it with the bare chip on the shield; 44.1 kHz would be the fallback.
- **The loaded layer** of the truck sound (`LOADED_GAIN`, `LOADED_RATE_SCALE`): set from measured values, not by ear.
- **`engine_diesel`** (an earlier variant): never run on hardware.
- **Current at the final volume and speaker:** 57 mA idle and 105 mA at full throttle were measured with
  `MASTER_VOLUME` 0.6 and the 40 mm speaker.

## Sound features not done yet

- Stalling by itself after a long idle (idea from 2026-11-03; the timeout is open). `start-stop-horn.md`
- A reverse beeper. Reverse itself is detected already (no upshift while reversing, `RC_REVERSE_SIGN`).
- Re-tune the sounds once the speaker is chosen; it changes which frequencies matter.
- Better recordings: CC0 loops of a truck diesel at several rpm with mid-frequency content, or own recordings to
  extract grains from (`sound-research.md`).
- Free transmitter controls for later sound functions: R3, K2..K4 (`controls.md`).

## Later (development outlook)

Not started; recorded so the design does not block them.

- **User-changeable sounds** (planned 2026-11-08): sound sets as files in the 1.5 MB data partition, loaded over USB
  with a web page (Web Serial, `web/index.html`, built 2026-11-14, works on the module since 2026-11-15). The BOOT button keeps switching sets. Decided
  2026-11-14: one kind of set, all in the data partition (the seven `engine_lab` candidates become the default sets,
  each with its spoken name), plus one fallback set compiled into the firmware for an empty or damaged partition;
  the data partition grows once the sounds leave the firmware. Details, requirements for a sample, the set format,
  the directory structure and how to make the spoken name: `user-sounds.md` (the design). For users it gets its
  own guide later, written when the tool exists: what each sample must meet and how to make it (loops, one-shots,
  the spoken name), the directory structure and the file names of a set, how to upload a set, and what is needed
  for it (a computer with Chrome or Edge: no Safari, Firefox, iPhone or iPad, see `user-sounds.md`, "The web page").
- **Shield revision ID by a resistor** (considered 2026-11-16, not planned). A resistor (or a divider) on the shield on a free pin of the Zero's right column, read by the firmware at start (ADC), would tell one firmware which shield revision the Zero is plugged into; no resistor (breadboard) would mean "prototype" and the default setting. The firmware runs on the Zero, which can be moved between boards, so the ID belongs to the shield. Not worth it while the shield does not change in function: rev A and rev B do not differ in a way the firmware must know, so rev B gets none. Add it to the first revision whose pin assignment, gain or inputs differ; keep a free pin for it when that board is designed.
- **Firmware check and update on the web page** (idea 2026-11-14, after the page has been tried with the module):
  - *Check*: the firmware reports its version and build date in the reply to `@info` (done 2026-11-14, see
    "Firmware version" in the README) and the page shows it; still to do: say when the one it carries is newer ("on the module 1.2, available 1.3"). After an update the page checks
    that the module answers `@hello` with the new version.
  - *Update, preferred way*: esptool-js (Espressif's library for flashing from the browser, the one ESP Web Tools
    uses) over the same Web Serial port. The page puts the Zero into its ROM bootloader through the chip's own USB
    (no buttons) and writes only the app: never the data partition with the user's sets. Works even when the
    firmware on the module is broken, because the bootloader is in ROM. With the two app slots of
    `partitions_sets.csv` it has to write `app0` (0x10000) and reset `otadata` (0xe000), or the module may keep
    booting `app1`.
  - *Other way*: an update through the page's own protocol into the other app slot (Arduino's `Update`), which
    the partition table already allows. Simpler for the page, but no way back if the new firmware does not start.
  - Open: where the page gets the firmware. From git once the repo is public: the built `firmware.bin` attached
    to a GitHub release, fetched through a host that allows it from the page (raw.githubusercontent.com or
    cdn.jsdelivr.net/gh/..., by the release tag; GitHub's own release downloads do not allow a page to read them).
    The page then also knows the newest version without being downloaded again. While the repo is private: a
    `firmware.bin` or a generated JS file beside `index.html` like `demo_sets.js`, or a file the user chooses. Also
    open: whether esptool-js is loaded from a CDN like Piper or kept with the page, and its licence (Apache 2.0).
  - *Leaning (2026-11-17, not decided)*: both ways of getting the firmware, online as the main one and a file the user chooses as the fallback. Build the file chooser first: it works with the repo private, and it is how the flashing itself gets tested. Online comes once the repo is public (with a small manifest: version, date, checksum, fetched through a host that allows it, as above; it does not work from `file://`). For a chosen file the page checks the image header (magic byte 0xE9, chip ESP32-S3) and the project name in the app descriptor before it writes, and it always asks first. Both ways use the same esptool-js writer, the app slot only.
- **Revisions for the printed parts** (to consider, noted 2026-11-14): the speaker box, its cap and the solder
  stand (`hardware/speaker_box/`, `hardware/solder_stand/`) could get revision letters like the shield (rev A, ...,
  git tags `hw-speaker_box-revA` and so on) once printed copies need telling apart, perhaps with the revision
  embossed in the part (a small text in the OpenSCAD model). Until then git alone tracks them.
- **Firmware updates over Wi-Fi (OTA)**, with Wi-Fi switched on only in an update mode (for example BOOT held at
  power-up). The 8 MB partition table already has two 3.3 MB app slots; `engine_lab` is about 1.15 MB, of which the
  voice prompts are about 480 kB and the engine samples about 355 kB. The sounds are compiled into the firmware, so an
  OTA update also brings new sounds.
- **Sound sets over Wi-Fi** (considered 2026-11-17, not planned). The same job as the web app does over USB, without a cable, in the same service mode as the OTA update above (Wi-Fi only on request, for example BOOT held at power-up, because the 2.4 GHz radio would disturb the receiver's link while driving). A page from https cannot call an http device on the home network (mixed content), so the module would serve the page itself (from flash: about 200 kB plus `number_names.js` 355 kB) and speak the same `@` commands over a WebSocket; or the page is opened from disk (`file://`) and uses a WebSocket. Connection: the module as a hotspot with a password (nothing to store, but the computer loses its internet meanwhile), or as a client of the home network (the password has to be entered and kept). Gain: no USB cable with the module in the model, and Safari, Firefox and phones could use the app, because Web Serial is not needed. Cost: a bigger firmware, a server to secure (without a password anyone nearby could change the sounds or the firmware), and the page to serve. The Web Serial way stays.
  Memory (estimate, nothing built): the data partition is 4.66 MB for sounds today (2.25 MB with the seven default sets, so about 2.4 MB free; a set is 0.2-0.6 MB). `engine_sets` is 0.46 MB of a 1.5 MB app slot; with Wi-Fi and a server it would be about 1.0-1.2 MB, which still fits but leaves 0.3-0.5 MB. The page (`index.html` 78 kB + `number_names.js` 355 kB, about 0.43 MB) would not fit in the slot, so it goes to the data partition and takes that much from the sounds (about 2.0 MB free with the default sets); it could be made smaller (minified page, fewer spoken numbers).
  Decided as the likely way (2026-11-17): the page served by the module has no Speak (the computer has no internet while it is joined to the module's network), so the spoken name of a set is limited to its **index**, the spoken number from `number_names.js`. A name from a file or the microphone could stay in the module's page if it is wanted, but it is not needed for this variant. The USB page keeps all three ways.
- **USB audio** (the Zero as a USB speaker for the PC, to compare the same sound from the PC and from the module):
  tried on 2026-11-08, does not work with the current Arduino core; parked until a move to core 3.x
  (`rejected-ideas.md`).
- **Spare inputs** on the shield (IO10..IO12 on a cable connector), only if a use turns up (`shield-pcb.md`).
- **Iteration 3** of the board with the ESP32-S3 itself instead of the Zero, only if size or cost demands it.
- **A variant for a classic RC receiver** (between receiver and ESC), not needed for CyberBrick (`shield-pcb.md`).
