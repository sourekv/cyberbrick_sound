# Roadmap: what is open

Status: 2026-11-21. The one place for everything that is still open: decisions, checks on hardware and the plans for
later. The other documents describe what exists and link here for what is missing. Ideas that were dropped, with the
reasons, are in `rejected-ideas.md`.

## Next

| Item | Where | Notes |
|---|---|---|
| Choose the engine sound (**done**: the truck engine is a Detroit Diesel Series 60, shift sound in all sounds) | `engine_lab`, `sound-research.md` | the candidates became the default sets of the sets app; every user can change them (see "User-changeable sounds" below) |
| Shield: approve and receive (**done 2026-11-21**: the first rev A board works) | `shield-pcb.md` "Order of 2026-11-13" | ordered at JLCPCB on 2026-11-13 ([order number removed], 5 boards with basic parts, DHL Express, 84.41 USD paid incl. customs); approved on 2026-11-14; delivered 2026-11-20 at 12:14 (five boards, SMD fitted); J1/J3/J4 and the servo cables ordered at GME on 2026-11-13 (arrived); speaker cables (IC007) ordered at Bambu Lab on 2026-11-13 (arrived); J1/J3/J4 soldered on the first board on 2026-11-21 and the first power-up done (`shield-pcb.md` "First power-up of rev A"); the other four boards are not fitted yet |
| Speaker for the model | `speaker-measurement.md` | 40 mm or a production candidate (for example 21 mm). The box is done (30 ml best, 15 ml close); more would come from another speaker or amplifier, not from the box |
| Enclosure for the model | - | designed from scratch around the chosen speaker; the printed box is a test fixture only |
| Long power test with the motor running | `bringup.md` | does the servo-port 5 V hold with the module and the motor together |

## To check on hardware

- **First shield boards: done on the first board, 2026-11-21** (`shield-pcb.md` "First power-up of rev A"). Checked by the working board: USB and the receiver connected at the same time (the OR-ing diode D2, `shield-pcb.md` "Decided"; the currents were not measured), the Zero's underside clears the parts under it (it sits on the sockets and nothing touches). Still open: the current, the long run with the motor, the other four boards.
- **MAX98357A at 22.05 kHz:** the datasheet does not list 22.05 kHz as a supported sample rate, yet the prototype
  plays fine at it, and so does the bare chip on the first rev A shield (checked by ear on 2026-11-21, not measured).
  Keep an eye on it in the long run; 44.1 kHz would be the fallback.
- **Lower sockets for rev B (open, decided 2026-11-21 to keep the 8.5 mm sockets for now; only if the model is too tight):** measure the Zero's pin length, try the 3.5 mm LaskaKit
  strip on one rev A board (`shield-pcb.md` "low sockets"); the solder stand needs a new pocket depth.
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

- **User-changeable sounds** (**done**: planned 2026-11-08, the sets and the web page work on the module since 2026-11-15, the user guide is `user-guide.md`; the text below is the original plan, the design is `user-sounds.md`): sound sets as files in the 1.5 MB data partition, loaded over USB
  with a web page (Web Serial, `web/index.html`, built 2026-11-14, works on the module since 2026-11-15). The BOOT button keeps switching sets. Decided
  2026-11-14: one kind of set, all in the data partition (the seven `engine_lab` candidates become the default sets,
  each with its spoken name), plus one fallback set compiled into the firmware for an empty or damaged partition;
  the data partition grows once the sounds leave the firmware. Details, requirements for a sample, the set format,
  the directory structure and how to make the spoken name: `user-sounds.md` (the design). For users it gets its
  own guide later, written when the tool exists: what each sample must meet and how to make it (loops, one-shots,
  the spoken name), the directory structure and the file names of a set, how to upload a set, and what is needed
  for it (a computer with Chrome or Edge: no Safari, Firefox, iPhone or iPad, see `user-sounds.md`, "The web page").
- **Sample layers by rpm** (idea 2026-11-21, low priority, not planned). Today a sample set has two loops (`idle.wav`, `loaded.wav`), blended by the throttle, and the rpm is made only by playing them faster (`rate`, 1.0x at idle to 3.0x at full throttle), which shifts the whole spectrum (and the noise). Several loops recorded at different steady rpm (for example idle, middle, high), each played only in a narrow rate range (about 0.8x to 1.3x) and crossfaded with its neighbour, would sound more natural and move less from the original recordings. By rpm, not by gear: a gear has no fixed rpm (the virtual gearbox lets the rpm fall at a shift and rise again). Cost: about 0.5 to 0.7 MB per set for four layers (fits the 4.66 MB data partition and the 8 MB PSRAM), a firmware change (pick two neighbouring layers by rpm and crossfade), a longer `set.json` (a list of layers with their rpm range; without the list today's pair still works), and the page and the PC tool must show and upload them. The hard part is the material: clean loops at several steady rpm. Synth sets do not need it (they make the engine from firings).
- **Shield revision ID by a resistor** (considered 2026-11-16, not planned). A resistor (or a divider) on the shield on a free pin of the Zero's right column, read by the firmware at start (ADC), would tell one firmware which shield revision the Zero is plugged into; no resistor (breadboard) would mean "prototype" and the default setting. The firmware runs on the Zero, which can be moved between boards, so the ID belongs to the shield. Not worth it while the shield does not change in function: rev A and rev B do not differ in a way the firmware must know, so rev B gets none. Add it to the first revision whose pin assignment, gain or inputs differ; keep a free pin for it when that board is designed.
- **Firmware check and update on the web page** (idea 2026-11-14, after the page has been tried with the module; makes sense, confirmed 2026-11-18, over USB with esptool-js, not over Wi-Fi):
  - *Check*: the firmware reports its version and build date in the reply to `@info` (done 2026-11-14, see
    "Firmware version" in the README) and the page shows it (**done**, seen on the real module 2026-11-21); still to do: say when the one it carries is newer ("on the module 1.2, available 1.3"). After an update the page checks
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
- **Firmware updates over Wi-Fi (OTA)** (**low priority** since 2026-11-18), with Wi-Fi switched on only in an update mode (for example BOOT held at
  power-up). The 8 MB partition table already has two 3.3 MB app slots; `engine_lab` is about 1.15 MB, of which the
  voice prompts are about 480 kB and the engine samples about 355 kB. The sounds are compiled into the firmware, so an
  OTA update also brings new sounds.
- **Sound sets over Wi-Fi** (considered 2026-11-17, **low priority** since 2026-11-18: a web server on the module is judged too much for what it brings; USB and the page opened from disk or from GitHub Pages are enough). The same job as the web app does over USB, without a cable, in the same service mode as the OTA update above (Wi-Fi only on request, for example BOOT held at power-up, because the 2.4 GHz radio would disturb the receiver's link while driving). A page from https cannot call an http device on the home network (mixed content), so the module would serve the page itself (from flash: about 200 kB plus `number_names.js` 355 kB) and speak the same `@` commands over a WebSocket; or the page is opened from disk (`file://`) and uses a WebSocket. Connection: the module as a hotspot with a password (nothing to store, but the computer loses its internet meanwhile), or as a client of the home network (the password has to be entered and kept). Gain: no USB cable with the module in the model, and Safari, Firefox and phones could use the app, because Web Serial is not needed. Cost: a bigger firmware, a server to secure (without a password anyone nearby could change the sounds or the firmware), and the page to serve. The Web Serial way stays.
  Memory (estimate, nothing built): the data partition is 4.66 MB for sounds today (2.25 MB with the seven default sets, so about 2.4 MB free; a set is 0.2-0.6 MB). `engine_sets` is 0.46 MB of a 1.5 MB app slot; with Wi-Fi and a server it would be about 1.0-1.2 MB, which still fits but leaves 0.3-0.5 MB. The page (`index.html` 78 kB + `number_names.js` 355 kB, about 0.43 MB) would not fit in the slot, so it goes to the data partition and takes that much from the sounds (about 2.0 MB free with the default sets); it could be made smaller (minified page, fewer spoken numbers).
  Decided as the likely way (2026-11-17): the page served by the module has no Speak (the computer has no internet while it is joined to the module's network), so the spoken name of a set is limited to its **index**, the spoken number from `number_names.js`. A name from a file or the microphone could stay in the module's page if it is wanted, but it is not needed for this variant. The USB page keeps all three ways.
- **Sound sets and firmware update over Bluetooth Low Energy** (considered 2026-11-18, low priority; looks better than Wi-Fi). The ESP32-S3 has BLE (no classic Bluetooth); Chrome and Edge (also on Android) have Web Bluetooth, so the page could talk to the module with the same `@` commands over one GATT service (like Nordic UART), as a third transport next to Web Serial and the simulated module. Against Wi-Fi: the computer keeps its internet (so Speak works and the spoken name need not be limited to the index), the page stays where it is (disk or GitHub Pages, nothing served by the module, no mixed-content problem), no network to join, pairing once with a PIN. Against USB: slower (tens of kB/s: a set of 0.2-0.6 MB seconds to a few minutes, a firmware of 0.5-1 MB about a minute), Chrome and Edge only (no Safari, Firefox or iPhone), a bigger firmware (NimBLE, roughly 0.1-0.3 MB), and security to design (pairing or a PIN, active only in a service mode such as BOOT held at power-up). A firmware update over BLE would use the other app slot (no way back from a build that does not start, without USB). Estimates, nothing built.
  How it would be started (2026-11-18): BLE does not run all the time (it would disturb the receiver's 2.4 GHz link, is open to anyone nearby, and costs RAM); it is a service mode that ends on disconnect, after about 5 minutes of idle or at power-off, with a spoken "Bluetooth" on entry and PIN pairing. The BOOT button is no use as the trigger, because the module sits inside the model. The module already reads all transmitter channels `[L1 L2 L3 R1 R2 R3 K1 K2 K3 K4]` through the receiver's S4, so the trigger can come from the transmitter, always with the ignition off and the throttle at rest, so it cannot start while driving. Options: (1) a button added to the transmitter's K2..K4 ports (the transmitter in use has only K1, the left shoulder button; K1 is not usable, its long press restarts the data program on the receiver and a short press switches the lights); (2) the free stick R3 held to its end for about 3 s, which needs nothing new (preferred without extra hardware); (3) a window of about 60 s after power-up as the fallback, needing no transmitter; a pattern on the ignition switch and the horn stick R1 are poor choices (they have their own functions). The same transmitter control could also step the sound sets, which BOOT does today (and BOOT is as hard to reach).
- **USB audio** (the Zero as a USB speaker for the PC, to compare the same sound from the PC and from the module):
  tried on 2026-11-08, does not work with the current Arduino core; parked until a move to core 3.x
  (`rejected-ideas.md`).
- **Spare inputs** on the shield (IO10..IO12 on a cable connector), only if a use turns up (`shield-pcb.md`).
- **Iteration 3** of the board with the ESP32-S3 itself instead of the Zero, only if size or cost demands it.
- **A variant for a classic RC receiver** (between receiver and ESC), not needed for CyberBrick (`shield-pcb.md`).
