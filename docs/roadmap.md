# Roadmap: what is open

Status: 2026-11-26. The one place for everything that is still open: decisions, checks on hardware and the plans for
later. What has been done is in the short list at the end ("Done"), with a pointer to the document that describes it. The
other documents describe what exists and link here for what is missing. Ideas that were dropped, with the reasons (among them Wi-Fi for the sets and the firmware, in favour of Bluetooth), are in
`rejected-ideas.md`.

## Next

| Item | Where | Notes |
|---|---|---|
| Speaker for the model | `speaker-measurement.md` | 40 mm or a production candidate (for example 21 mm). The box is done (30 ml best, 15 ml close); more would come from another speaker or amplifier, not from the box |
| Enclosure for the model | - | designed from scratch around the chosen speaker; the printed box is a test fixture only |
| Long power test with the motor running | `bringup.md` | does the servo-port 5 V hold with the module and the motor together |
| The other four rev A boards | `shield-pcb.md` | solder J1, J3 and J4 and check them like the first one (the first board plays, see "Done") |

## To check on hardware

- **Current:** the current of the module with the receiver and with USB at the same time (the OR-ing diode D2), and at the final volume and speaker.
  57 mA idle and 105 mA at full throttle were measured earlier on the breadboard with `MASTER_VOLUME` 0.6 and the 40 mm speaker.
- **MAX98357A at 22.05 kHz:** the datasheet does not list 22.05 kHz as a supported sample rate, yet the prototype
  plays fine at it, and so does the bare chip on the first rev A shield (checked by ear on 2026-11-21, not measured).
  Keep an eye on it in the long run; 44.1 kHz would be the fallback.
- **Lower sockets** (option, open): 3.5 mm female strips with short pins would make the stack about 5 mm lower; try one pair first (`shield-pcb.md`, "lower sockets").
- **The loaded layer** of the truck sound (`LOADED_GAIN`, `LOADED_RATE_SCALE`): set from measured values, not by ear.
- **`engine_diesel`** (an earlier variant): never run on hardware.

## Sound features not done yet

- Stalling by itself after a long idle (idea from 2026-11-03; the timeout is open). `start-stop-horn.md`
- A reverse beeper. Reverse itself is detected already (no upshift while reversing, `RC_REVERSE_SIGN`).
- Re-tune the sounds once the speaker is chosen; it changes which frequencies matter.
- Better recordings: CC0 loops of a truck diesel at several rpm with mid-frequency content, or own recordings to
  extract grains from (`sound-research.md`); more layers by rpm from better recordings (`layers-design.md`), and a loaded
  axis for the layers if the layered sound lacks it.
- `make_default_sets.py` and `make_user_sounds.py` do not read `layers` (no default set uses them).
- Free transmitter controls for later sound functions: R3, K2..K4 (`controls.md`).

## Later (development outlook)

Not started; recorded so the design does not block them.

- **A guide to the CyberBrick app, two ways** (noted 2026-11-24, not written). Today there is only the import of the ready configuration
  `Truck_with_Engine_Sound_Data.json` (`getting-started.md`, step 5). The guide would offer (a) that import, and (b) for someone who wants to keep
  their own configuration, the two things to add by hand: on the receiver the **Code** module "Sound data" (`cyberbrick-code/uart_forward.py`),
  which sends from the servo port **S4**, and the event that starts it after power-up (left stick left / right, L2: centre 600, dead zone 100;
  `controls.md`, "How the program starts by itself"). It should name what the transmitter and the receiver need to have free: S4, the L2 channel,
  and the controls of the ignition (3-position switch, L1) and of the horn (R1). It should use pictures of the app.
- **First install of a new module from the web page** (design 2026-11-26, nothing built): flashing a blank module from Chrome or Edge, without
  PlatformIO (`web-install-design.md`). The trial waits until a spare blank ESP32-S3-Zero-N8R8 is available. Its build job could also supply the
  online firmware file of the next item.
- **Learning the controls of the transmitter** (idea, noted 2026-11-25; not designed, nothing built or measured): today the throttle, the ignition and
  the horn are fixed in the firmware (the channels L3, L1 and R1 in `firmware/src/engine_sets/main.cpp`, their rest values and thresholds in
  `firmware/include/config.h`; `controls.md`). The module would instead watch all ten channels while the user moves a control, and keep the channel,
  the rest value and the threshold in NVS; the web app could show the result on a page "Controls". The
  idea for entering it: **one** setup mode for the learning and for the sound programming over Bluetooth, started by one gesture on the transmitter,
  so that a power-up without the gesture stays quiet (today the Bluetooth window and the spoken PIN come after every power-up, `ble-link.md`).
  Learning the controls would need no computer; programming the sounds still needs the web page and the PIN. The gesture must not depend on the
  ignition or the throttle, which may not be learned yet. Candidates: three short presses of a free button K2..K4 (needs one more momentary button
  module if only K1 is fitted), or three long presses of K1 (no new part, but a long press of K1 restarts the receiver program, so the gaps in the
  data have to be measured first).
- **Firmware file for the page, online** (the open part of the firmware update): where the page gets `firmware.bin` from instead of a file the user
  chooses. From git once the repo is public: the built `firmware.bin` attached to a GitHub release, fetched through a host that allows it from the
  page (raw.githubusercontent.com or cdn.jsdelivr.net/gh/..., by the release tag; GitHub's own release downloads do not allow a page to read them),
  with a small manifest (version, date, checksum); it does not work from `file://`. The page then also knows the newest version and can say "on
  the module 1.2, available 1.3". Until then the file chooser is the way.
- **Shield revision ID by a resistor** (considered 2026-11-16, not planned). A resistor (or a divider) on the shield on a free pin of the Zero's right
  column, read by the firmware at start (ADC), would tell one firmware which shield revision the Zero is plugged into; no resistor (breadboard) would mean
  "prototype" and the default setting. The firmware runs on the Zero, which can be moved between boards, so the ID belongs to the shield. Not worth it
  while the shield does not change in function: rev A and rev B do not differ in a way the firmware must know, so rev B gets none. Add it to the first
  revision whose pin assignment, gain or inputs differ; keep a free pin for it when that board is designed.
- **Revisions for the printed parts** (to consider, noted 2026-11-14; the solder stand was changed on 2026-11-22: a thicker base and grooves for rubber
  bands, no revision letters yet): the speaker box, its cap and the solder stand (`hardware/speaker_box/`, `hardware/solder_stand/`) could get revision
  letters like the shield (rev A, ..., git tags `hw-speaker_box-revA` and so on) once printed copies need telling apart, perhaps with the revision
  embossed in the part (a small text in the OpenSCAD model). Until then git alone tracks them.
- **USB audio** (the Zero as a USB speaker for the PC, to compare the same sound from the PC and from the module): tried on 2026-11-08, does not work with
  the current Arduino core; parked until a move to core 3.x (`rejected-ideas.md`).
- **Spare inputs** on the shield (IO10..IO12 on a cable connector), only if a use turns up (`shield-pcb.md`).
- **Iteration 3** of the board with the ESP32-S3 itself instead of the Zero, only if size or cost demands it.
- **A variant for a classic RC receiver** (between receiver and ESC), not needed for CyberBrick (`shield-pcb.md`).

## Done

The detail is in the document named at the end of each line.

- **Solder stand, third iteration** (2026-11-23): the base with the grooves for rubber bands, two sockets and one loose insert for J1 (pins out: J1 on the Zero side, one pass; pins in: J1 on the opposite side, two passes), printed and works, both variants tried; the J1 pins have to be held in place by hand first and then the board is put into the stand (`shield-pcb.md`, `hardware/solder_stand/`).
- **Choose the engine sound** (2026-11-14): the choice is left to the user; the candidates became the default sets of the sets app, with the shift sound in all
  of them (`user-sounds.md`, `sound-research.md`).
- **Shield: approve and receive, first power-up** (ordered 2026-11-13, delivered 2026-11-20, the first rev A board works since 2026-11-21): J1, J3 and J4
  soldered, USB and the receiver connected at the same time, the Zero clears the parts under it, sound. The servo cable must go to S4 (`shield-pcb.md`
  "First power-up of rev A").
- **User-changeable sounds** (planned 2026-11-08, working on the module since 2026-11-15): sound sets in the data partition, a web page (Web Serial) that
  lists, tests, edits, writes and deletes them, spoken names, default sets (`user-sounds.md`, `user-guide.md`).
- **Firmware check and update on the web page** (2026-11-22): the version is shown; the update goes over USB and Bluetooth into the other app slot, with a
  file the user chooses, checked and confirmed first. Not by esptool-js: the page's own protocol (`@fwput`, `@fww`, `@fwend`) was simpler and is tried on the
  real module (`ble-link.md`).
- **Sound sets and firmware update over Bluetooth Low Energy** (2026-11-22): in the one firmware `engine_sets`; a window of 3 minutes after the power-up, a
  spoken random PIN (digits that are easy to hear), a name of the module, reconnecting, a restart after a change; no trigger from the transmitter (dropped as
  overkill, `rejected-ideas.md`) (`ble-link.md`). Why Bluetooth rather than Wi-Fi is in the same document.
- **Sample layers by rpm** (2026-11-22): several loops at different steady speeds, crossfaded; sets without them play as before; the page edits and previews
  them (`layers-design.md`).
- **Overall volume of the module** (2026-11-22): `@volume`, kept in NVS, a slider on the page (`ble-link.md`, `user-guide.md`).
- **Set numbers without the hard to hear digits 5, 7, 9** (2026-11-22): the default sets are 01, 02, 03, 04, 06, 08 and 10; the page gives only such numbers
  (`user-sounds.md`).
- **Spoken names and the PIN made clearer for the 40 mm speaker** (2026-11-22): `tools/voice_clarify.py`, the same chain in the page (`ble-link.md`).
