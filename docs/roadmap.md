# Roadmap: what is open

Status: 2026-11-12. The one place for everything that is still open: decisions, checks on hardware and the plans for
later. The other documents describe what exists and link here for what is missing. Ideas that were dropped, with the
reasons, are in `rejected-ideas.md`.

## Next

| Item | Where | Notes |
|---|---|---|
| Choose the engine sound | `engine_lab`, `sound-research.md` | candidates are judged by ear on the real speaker |
| Shield: order | `shield-pcb.md` "Ordering at JLCPCB" | reviewed in KiCad 2026-11-12; decided 2026-11-12: JLCPCB with the basic parts (`fab/jlcpcb_basic/`, red LED, J1/J3/J4 by hand), about 72-87 USD for 5 boards incl. VAT depending on shipping (`shield-cost-comparison.md`); stock checked 2026-11-12; to do: upload, confirm the placement preview (C1 and U1 rotations already fixed, check the LED polarity), choose shipping, order |
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

- **User-changeable sounds** (planned 2026-11-08): sound sets as files in the 1.5 MB data partition, loaded over USB,
  first with a Python script, then with a web page (Web Serial). The BOOT button keeps switching sets; the built-in
  sets stay as a fallback. Requirements for a sample and the set format: `user-sounds.md`.
- **Firmware updates over Wi-Fi (OTA)**, with Wi-Fi switched on only in an update mode (for example BOOT held at
  power-up). The 8 MB partition table already has two 3.3 MB app slots; `engine_lab` is about 1.15 MB, of which the
  voice prompts are about 480 kB and the engine samples about 355 kB. The sounds are compiled into the firmware, so an
  OTA update also brings new sounds.
- **USB audio** (the Zero as a USB speaker for the PC, to compare the same sound from the PC and from the module):
  tried on 2026-11-08, does not work with the current Arduino core; parked until a move to core 3.x
  (`rejected-ideas.md`).
- **Spare inputs** on the shield (IO10..IO12 on a cable connector), only if a use turns up (`shield-pcb.md`).
- **Iteration 3** of the board with the ESP32-S3 itself instead of the Zero, only if size or cost demands it.
- **A variant for a classic RC receiver** (between receiver and ESC), not needed for CyberBrick (`shield-pcb.md`).
