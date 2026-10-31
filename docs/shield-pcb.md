# Shield PCB (iteration 2): scope

Status: requirements only, no schematic yet. The prototype (iteration 1) is a breadboard with an ESP32-S3-Zero-N8R8-M and a MAX98357A, powered and verified as described in `bringup.md`.

## Rule: PWM2 is dedicated to the sound module

The throttle is copied to the servo port **PWM2** in the CyberBrick app (L Stick Y drives both Throttle on M1 and PWM2). The module only listens to that copy and takes its power from the same port:

- S: throttle copy, 50 Hz, about 3.3 V, 977..1973 us (45..135 deg), centre about 1455 us
- V: about 4.94 V without load; the module draws about 57 mA idle and 105 mA at full throttle (`MASTER_VOLUME` 0.6, 40 mm speaker)
- G: ground

Nothing else can be connected to PWM2: a servo there would follow the throttle. The original path to the motor (port M1) is untouched, so **the board needs no pass-through connector**. PWM1 (steering), PWM3 and PWM4 stay free.

## On the board

![Shield mock](shield-mock.png)

Mock of the layout (top view, illustrative placement, not routed). An interactive 3D model is `shield-3d.html`. Both are generated from the same layout data by `tools/make_shield_mock.py` (layout in `tools/shield_layout.py`).

**Board size: 18 x 23.5 mm, exactly the outline of the ESP32-S3-Zero**, which sits on top of it in two 9-pin female header strips (15.24 mm apart, 8.5 mm tall). Everything fits in the 12.7 mm gap between the strips (top side) or on the bottom side (test pads, GND plane). Only the two cable plugs stick out past the board ends: the servo plug at the USB end (right-angle header J1) and the speaker plug at the opposite end (side-entry JST-PH J2). With the Zero the stack is about 14 mm high. All pins used by the firmware are on one side of the Zero (5V, GPIO1, GPIO4-6 on the left column), the right column stays free.

1. **Socket or pads for the ESP32-S3-Zero**, same pin use as the prototype: GPIO1 throttle in, GPIO4 I2S DOUT, GPIO5 BCLK, GPIO6 LRC. The USB-C port and the Boot/Reset buttons must stay reachable for flashing.
2. **Input connector** (3-pin servo type: S, V, G) to PWM2. S goes through a 1 kOhm series resistor to GPIO1, optionally with a large pull-down (for example 100 kOhm) so the input is defined when disconnected, and optionally an ESD/TVS device.
3. **Power from the servo port**: reverse-polarity protection (Schottky diode or P-MOSFET), a resettable fuse, a bulk capacitor (about 100-470 uF) near the amplifier and small ceramic decoupling capacitors. A diode (or ideal diode) between the servo-port 5 V and the USB 5 V so both can be connected at the same time; on the breadboard only one of them may ever be connected.
4. **MAX98357A amplifier**: gain and shutdown/channel pins configurable (resistors or jumpers), speaker output to a connector (for example JST-PH) or solder pads. The chip is hard to solder by hand; assembly by a PCB service is likely.
5. **Service items**: test points (5 V, 3.3 V, GND, GPIO1, I2S lines) as pads on the bottom side. Because the board is only as large as the Zero there are no mounting holes (the sockets and the cables hold it; fix it with a stand-off or tape), and no room for a status LED or a spare GPIO header: the unused Zero pins are reachable at the socket tails on the bottom.

## Decided

- Board size: the outline of the ESP32-S3-Zero (see above).
- The amplifier is a bare MAX98357A chip on the board, **assembled by a PCB service** (the TQFN-16 package is not practical to hand-solder). No plug-in breakout module.

## Decisions still open

- The speaker it has to carry (40 mm or a production candidate; see `sound-research.md`). The board size itself is settled: the outline of the Zero.
- Whether the Zero's underside is flat (the headers leave about 7 mm of clearance under it, enough for everything on the board; check the real module).
- ESP32-S3-Zero in a socket (replaceable) or soldered directly.
- How much the PCB service assembles besides the amplifier: only the SMD parts (and the rest by hand) or the whole board.

## Out of scope for this iteration

- ESP32 module directly on the board without the Zero (iteration 3, only if size or cost demands it).
- Further sound features beyond the current firmware.

## Possible future variant: classic RC receiver

On a classic RC model the receiver drives the ESC with a servo-type signal, so a module would sit between receiver and ESC: read the signal, play the sound and pass the signal on unchanged. That needs a different board (input from the receiver, output to the ESC, a pass-through path that never interferes). It is **not** needed for CyberBrick and is not planned now.

Before such a variant, the signals of the target receiver would have to be measured, because they are more varied than the CyberBrick servo port: signal level (3.3 V or 5 V), pulse range and neutral point of the throttle channel, frame rate (50 Hz up to several hundred Hz for some receivers), behaviour at failsafe and whether the ESC's BEC powers the receiver (and so whether the module may take power from it). The firmware's pulse constants in `config.h` would then be re-derived from those measurements.

## Component list (draft, independent of how the board is assembled)

Part numbers are examples to be checked when the schematic is drawn; values marked "check" depend on a datasheet detail not yet verified.

| Group | Component | Qty | Notes |
|---|---|---|---|
| Controller | Waveshare ESP32-S3-Zero-N8R8-M | 1 | as on the prototype |
| | 2.54 mm female header, 9 pins | 2 | one per long edge of the Zero (5V, GND, 3V3, 1..6 and TX, RX, 13..7); omit if the Zero is soldered directly |
| Amplifier | MAX98357AETE+ (I2S class-D amp, TQFN-16 3x3 mm) | 1 | alternative: MAX98357AEWL+ (WLP-9), smaller but harder to route; or a plug-in breakout module instead of the chip |
| | Decoupling for the amp supply: 10 uF + 100 nF ceramic, close to VDD | 1 + 1 | |
| | Bulk capacitor 100 uF, 6.3-10 V, polymer or tantalum, 6032 (case C) | 1 | near the amplifier supply; flat enough to fit under the Zero (a radial electrolytic is too tall) |
| | GAIN and SD_MODE configuration: solder-jumper pads and 100 kOhm resistors | 2-3 | default GAIN open = 9 dB; the SD_MODE resistor values that give (L+R)/2 are to be checked in the datasheet (the firmware sends the same sample on both channels) |
| | Optional 22-33 Ohm series resistors on BCLK, LRC, DIN | 3 | EMI damping; can be 0 Ohm |
| | Optional ferrite beads and small capacitors on the speaker outputs | 2 + 2 | only if EMI becomes a problem with longer speaker wires |
| Speaker | JST-PH 2-pin side-entry SMD connector (for example S2B-PH-SM4-TB) + mating cable | 1 | at the board end, plug enters from outside; or two solder pads |
| Input | 3-pin 2.54 mm right-angle pin header (S, V, G) | 1 | at the USB end of the board; mates with a 3-pin female servo/Dupont cable to PWM2 (check the orientation against the receiver's header) |
| | Resistor 1 kOhm | 1 | series resistor S to GPIO1 |
| | Resistor 100 kOhm | 1 | pull-down on GPIO1 (defined level when the cable is unplugged) |
| | ESD/TVS diode, low capacitance (optional) | 1 | on the S line |
| Power | Resettable fuse (PTC), about 0.5 A hold, 1206 | 1 | the module draws about 0.1 A average |
| | Reverse-polarity protection: Schottky diode in SOD-123 (rated 1 A or more) or P-MOSFET | 1 | a Schottky drops about 0.3-0.4 V, which is acceptable at this current (the amplifier needs 2.5-5.5 V) |
| | Diode (or ideal diode) between servo 5 V and USB 5 V | 1 | so both can be connected; check first whether the Zero's 5V pin already has a diode towards USB |
| | Ceramic capacitors 100 nF | 2-3 | general decoupling |
| Service | Test points (5 V, 3.3 V, GND, GPIO1, BCLK, LRC, DIN) | 7 | 1 mm pads on the bottom side |
| Dropped for size | Status LED, spare GPIO header, M2 mounting holes | - | no room on a board the size of the Zero; the Zero's own pins and socket tails serve for spare GPIOs |
