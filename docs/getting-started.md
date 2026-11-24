# Getting started from scratch

The whole way from the parts to an engine sound in a CyberBrick truck, in the order you do it. Each step is short and points to the
document that has the details.

```
transmitter --radio--> receiver in the model --S4 servo header (S, V, G)--> sound module (shield + Zero + speaker)
```

## What you need

| What | Note |
|---|---|
| A **Bambu Lab CyberBrick RC model** with the transmitter and the receiver (the truck is the first target) | the original firmware stays unchanged; we only send a configuration with the app |
| **Waveshare ESP32-S3-Zero-N8R8-M** | the N8R8 version (8 MB flash, 8 MB PSRAM) is needed; the "-M" has the pin headers fitted. The plain Zero with 2 MB PSRAM does not work |
| The **shield board** (rev A) with its parts, or the breadboard version | files and ordering: `shield-pcb.md`; breadboard: `bringup.md` |
| By hand on the shield: **J1** (right-angle pin header 1x3), **J3, J4** (female socket strips 1x9, 8.5 mm tall) | `shield-pcb.md`, "Needed besides the board" |
| **Servo cable**, 3 pins, female to female | from J1 to the receiver's S4 header |
| **Speaker**, 4 Ohm (8 Ohm also works, a little quieter) with a JST SH 1.0 mm 2-pin cable | to J2; `speaker-measurement.md` |
| A **USB-C data cable** (not a charge-only one) | for the first firmware |
| Soldering iron, and the **printed solder stand** (optional but it makes J1, J3 and J4 easy) | `soldering.md` |
| On the computer: **PlatformIO**, **Python 3 with numpy**, **Git**, and **Chrome or Edge** | `first-install.md` |

## 1. The board

Rev A is the board that was ordered and works (`shield-pcb.md`). Ordering from the files, the parts and the price: `shield-pcb.md`
and `shield-cost-comparison.md`. SMD parts come fitted by the service; J1, J3 and J4 you solder yourself. If you start on a
breadboard instead, the wiring is in `bringup.md`.

## 2. Solder J1, J3 and J4

With the printed stand, in one of two variants of fitting the servo header J1 (the pins out: one pass; the pins in: two passes):
**`soldering.md`**, with pictures.

## 3. The firmware and the default sound sets

Once, by cable: **`first-install.md`** (PlatformIO builds and writes `engine_sets`, then the default sets). After that sets, the volume
and a new firmware can also be changed from the web page over USB or Bluetooth.

## 4. The speaker

Plug the speaker's JST SH cable into J2. If it is too quiet, raise `MASTER_VOLUME` in the firmware, or bridge the solder jumper JP1
for 6 dB more (`speaker-measurement.md`).

## 5. The CyberBrick configuration

Import **`docs/cyberbrick-config/Truck_with_Engine_Sound_Data.json`** in the CyberBrick app and use *Send to Device* for **both** the transmitter
and the receiver (`cyberbrick-config/README.md`). The receiver then runs our small program ("Sound data") that sends all channels as serial data
from its S4 header; it starts by itself after power-up (`controls.md`, "How the program starts by itself").

## 6. Connect the module to the receiver

The servo cable goes from **J1** on the shield to the receiver's **S4** header. Two things are easy to get wrong:

- **The wrong port:** in another port the shield is powered, but no channel data arrive (no start, no horn). It must be **S4**.
- **The cable turned round:** S and G swap. The module does not start, but nothing is damaged. The wire with the colour mark is S. With the
  GME cable 775-123 the yellow wire is S, on the right seen from the bottom of the board (`shield-pcb.md`).

The shield's diode D2 lets USB and the receiver's 5 V be connected at the same time. With only USB connected the amplifier is silent by
design (it takes its power from the servo port); sound needs the receiver.

## 7. Switch on

Transmitter and truck on, in any order. The data start within about a second and the engine stays silent until you turn the ignition on or
drive off (`controls.md`, "Power-up order"; the controls of the transmitter are in the same document).

## 8. Change the sounds

Open the web app, **https://sourekv.github.io/cyberbrick_sound/**, in Chrome or Edge: test the sets, copy one, write your own, rename it, set the volume
(`user-guide.md`).

## When something does not work

- No sound at all: is the cable in S4 and the right way round, is the transmitter on, does the RGB LED of the Zero show data (`controls.md`)?
- Sound over USB only does not exist by design: the amplifier needs the receiver's 5 V.
- Firmware says `sets: no PSRAM`: the module is not an N8R8 (`first-install.md`).
- More: `first-install.md` and `user-guide.md` have their own "When something does not work" sections.
