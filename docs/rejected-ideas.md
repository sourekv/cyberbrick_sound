# Rejected ideas

Ideas that were considered, sometimes drawn or built, and then dropped. Each row says why and what is used instead, so the
same question does not have to be worked through again. Details stay in the linked documents; an idea can come back if
the reason no longer holds.

## Shield PCB

| Idea | Date | Why it was dropped | Instead | Details |
|---|---|---|---|---|
| Board the size of the Zero, without mounting holes | 2026-10-31 | no room for anything beside the Zero | 29 x 30 mm board with the CyberBrick receiver's four holes | `shield-pcb.md` |
| Zero-sized board with "ears" for the mounting holes | 2026-10-31 | the ears would be fragile | the same 29 x 30 mm board | `shield-pcb.md` |
| Spare GPIO header for later inputs | 2026-10-31 | keeps the first board small; nothing needs it yet | recorded as a future option | `shield-pcb.md` ("Out of scope") |
| Amplifier as a plug-in breakout module on the shield | 2026-10-31 | taller and larger than the chip | bare MAX98357A chip, soldered by the PCB service | `shield-pcb.md` |
| Second servo input (PWM3) for engine start, stop and horn on one transmitter button | 2026-11-07 | the channel data on one cable carries every control | one servo cable to S4 with all channels | `start-stop-horn.md` |
| Screw terminal or a dual footprint for the speaker | 2026-11-08 | the owner wants the same connector as CyberBrick uses | JST SH 1.0 mm 2-pin, as on the CyberBrick motor port | `shield-pcb.md` |
| Zero soldered straight onto the shield | 2026-11-08 | the Zero would no longer be replaceable; soldering only pays off with a single board carrying the ESP32-S3 itself | the Zero in two female socket strips | `shield-pcb.md` |
| Strain relief for a soldered servo cable: a cable tie through two small holes next to J1 | 2026-11-08 | a tie would not hold the cable | (see the next row) | `shield-pcb.md` |
| Strain relief: an unplated slot (4.4 x 1.6 mm) between the board edge and J1, the cable going up through it | 2026-11-08 | complicates the prototype; only 1 mm of board left between slot and edge | right-angle header J1; may come back with a soldered-cable variant of a later board | `shield-pcb.md` |

## Link to the receiver

| Idea | Date | Why it was dropped | Instead | Details |
|---|---|---|---|---|
| Right-angle adapter or a printed housing for the servo plug on S4 | 2026-11-07 | other servos of a model may plug in next to it | the existing servo cable, bent towards the USB end | - |
| Data wire on the receiver's LED2 port (GPIO20) | 2026-11-06 | the pin order of the LED ports is not marked on the receiver | servo header S4 (labelled S / V / G) | `cyberbrick-code/README.md` |
| Listening to the radio link (ESP-NOW) with the Zero instead of a wire | 2026-11-05 | the frames were found, but the payload is encrypted (nothing followed the sticks); breaking the encryption is not an option | the receiver's documented `rc_module.rc_slave_data()` read by our Code snippet and sent over a wire from S4 | `start-stop-horn.md` ("Side research") |
| (not a real rejection) Code snippets on the receiver | 2026-11-03 | the button design notes, carried over from the claude.ai chat, dismissed them in one line ("isolated, no state, 2048-character limit") without looking closer; the work then went into the radio link | found again through the receiver's source on 2026-11-06; a snippet is the current design | `start-stop-horn.md`, `controls.md` |
| Starting the data snippet with ignition events on the L1 switch | 2026-11-06 | a stick event fires right after power-up, without any action | the moved centre of L2 (`gt_mid` on the first data) | `controls.md`, `cyberbrick-config/README.md` |
| An extra angular servo on PWM4 in the configuration (throttle pulse before the snippet ran) | 2026-11-06 | not needed once the snippet starts by itself | only the snippet's data on S4 | `cyberbrick-config/README.md` |
| Green LED flash in the snippet on every frame | 2026-11-06 | only a test aid | removed | `cyberbrick-code/README.md` |
| Bluetooth audio from the PC for listening tests | 2026-11-05 | the ESP32-S3 has only Bluetooth LE, no classic audio (A2DP) | tried next: the Zero as a USB audio device (next row) | - |
| The Zero as a USB speaker for the PC (USB Audio Class), to compare the same sound from the PC and through the module | 2026-11-08 | built and tried, no sound. The Arduino core 2.0.17 (platform espressif32 6.9.0) ships TinyUSB 0.16 without the audio class, so a small UAC1 driver of our own was added through `usbd_app_driver_get_cb()`. Windows accepted the device without a driver and switched the stream on, but no packet ever arrived: the core's ESP32-S3 USB driver (`dcd_esp32sx`) writes the OUT transfer size with the 7-bit mask of endpoint 0 (196 bytes became 68), and with that worked around, still nothing came through. Others report the same: it works in ESP-IDF (with crackling), not in Arduino | nothing for now; worth another try after moving to Arduino core 3.x, whose TinyUSB uses the newer `dwc2` driver. Flashing an USB-OTG firmware needs the bootloader by hand (unplug, hold BOOT, plug in) | - |

## Engine sound

| Idea | Date | Why it was dropped | Instead | Details |
|---|---|---|---|---|
| The first CC0 car engine loops | 2026-10-31 | almost pure 40 to 80 Hz tones: nearly inaudible and hissy on a small speaker | synthesised sounds and loops with mid-frequency content | `sound-research.md` |
| One loop played faster and faster | 2026-10-31 | the whole timbre shifts, it turns into a siren | grain synthesis (fixed timbre, rate changes) | `sound-research.md` |
| Playback rate 1.0x to 4.0x for the real loops | 2026-10-31 | at 4x the timbre shifts too far and aliases | 1.0x to 3.0x plus the virtual gearbox | `sound-research.md` |
| The owner's own engine recordings | 2026-10-31 | pulsated when looped; licence unknown | parked (`engine_real`, header not in the repo) | `sound-research.md`, `assets/samples/LICENSE-SAMPLES.md` |

## Speaker box

| Idea | Date | Why it was dropped | Instead | Details |
|---|---|---|---|---|
| Sealing the speaker rim with plasticine only | 2026-11-07 | the owner found plasticine impractical (no TPU at hand for a printed seal either) | a screw cap that presses the rim | `hardware/speaker_box/speaker_box.scad` |
| A barrel-shaped box | 2026-11-08 | at these frequencies only the air volume matters, not the shape | the plain cylinder | `speaker-measurement.md` |
| Foam on the bottom of the box | 2026-11-08 | measured: no change | empty box | `speaker-measurement.md` |
| A flat or a polygon outside on the test box, so it does not roll when laid on its side | 2026-11-08 | the box is only a test fixture and does not go into the model; a reprint brings nothing (put it on its bottom or under a bit of plasticine) | the enclosure for the model will be designed from scratch around the chosen speaker; it can have a flat or a mounting foot then | `hardware/speaker_box/speaker_box.scad` |
| Further box experiments | 2026-11-08 | the 30 ml (and 15 ml) box already works well | if the sound must improve: a larger or different speaker, or a different amplifier / converter | `speaker-measurement.md` |
