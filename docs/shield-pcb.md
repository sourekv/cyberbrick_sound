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

**Board: 29 x 30 mm, the size of the CyberBrick receiver shield, with its four mounting holes** (see below). The ESP32-S3-Zero (18 x 23.5 mm) sits in the middle in two 9-pin female header strips (15.24 mm apart, 8.5 mm tall). Most parts are in the 12.7 mm gap under the Zero (everything under it stays below about 4.4 mm); the power LED is beside the Zero, where it stays visible. Only the two cable plugs stick out: the servo plug at the USB end (right-angle header J1) and the speaker plug at the opposite end (side-entry JST SH 1.0 mm J2). With the Zero the stack is about 14 mm high. All pins used by the firmware are on the left column of the Zero (5V, GPIO1, GPIO4-6); the right column is unused and stays free at the socket.

1. **Socket or pads for the ESP32-S3-Zero**, same pin use as the prototype: GPIO1 throttle in, GPIO4 I2S DOUT, GPIO5 BCLK, GPIO6 LRC. The USB-C port and the Boot/Reset buttons must stay reachable for flashing.
2. **Input connector** (3-pin servo type: S, V, G) to PWM2. S goes through a 1 kOhm series resistor to GPIO1, optionally with a large pull-down (for example 100 kOhm) so the input is defined when disconnected, and optionally an ESD/TVS device.
3. **Power from the servo port**: reverse-polarity protection (Schottky diode or P-MOSFET), a resettable fuse, a bulk capacitor (about 100-470 uF) near the amplifier and small ceramic decoupling capacitors. A diode (or ideal diode) between the servo-port 5 V and the USB 5 V so both can be connected at the same time; on the breadboard only one of them may ever be connected.
4. **MAX98357A amplifier**: gain and shutdown/channel pins configurable (resistors or jumpers), speaker output to a JST SH 1.0 mm 2-pin connector (see below) or solder pads. The chip is hard to solder by hand; assembly by a PCB service is likely.
5. **Service items**: test points (5 V, 3.3 V, GND, GPIO1, I2S lines) as pads on the bottom side, four M2/M2.5 mounting holes in the CyberBrick pattern, a **power LED** (taken from the servo-port 5 V after the reverse-polarity diode, so it shows that cable and receiver are fine; the Zero has no power LED of its own, only a programmable RGB LED). The status of the signal is shown by the Zero's own RGB LED from firmware (see the README).

## Mounting holes matching the CyberBrick receiver shield

The receiver shield (XA004) is 29 x 30 mm with four corner holes: 2.7 mm in diameter with a copper ring of about 5.7 mm (from the manufacturer's product image, reference only, not stored here), centred 3.0 mm from the board edges. The spacing is **23.0 x 24.0 mm** according to the CAD model of the community "CyberBrick Remote Control Receiver Test Housing" (its four heat-set insert holes of 3.1 mm are at +-11.5 / +-12.0 mm from the centre; the pocket for the board is 30 x 31 mm); the product image gives the same within its reading error. The test housing is only a size reference: our board needs the servo input and the speaker output and does not go into that housing. Our board is therefore a plain rectangle of the same size as the receiver shield (29 x 30 mm) with the same four holes, and the Zero (18 x 23.5 mm) sits in the middle, as drawn above.

To check before ordering: measure the hole spacing and diameter with calipers on the real receiver, and find out which way the receiver sits in its housing (the J1 and J2 plugs must stay accessible). A screw head of 4.5 mm leaves only about 0.25 mm to the corner of the Zero, so use a low or countersunk head or shift the Zero. The screw size is not known (the housing's 3.1 mm holes are for heat-set inserts, probably M2, and the 2.7 mm board holes would also take M2.5).

## Connectors used by CyberBrick

From the Maker's Supply CyberBrick user's manual (the Bambu store page names only the power input): DC motor ports M1/M2 and the transmitter button ports K1-K4 are **JST SH 1.0 mm 2-pin**; joystick (ADC) and WS2812 LED ports are SH 1.0 mm 3-pin; servo ports S1-S4 are 3-pin headers (2.54 mm); power inputs and the power switch are **XH 2.54 mm 2-pin**. The kit's SH 2-pin wires (button module, N20 motor) therefore fit a speaker connector of the same type, so the speaker connector J2 is SH 1.0 mm 2-pin and users need no crimping: a 2-pin SH cable with one free end is soldered to the speaker (or supplied with it). Open: whether the kit has spare 2-pin SH cables (the manual does not list the kit's cables); cheap SH 2-pin pigtails are sold separately.

## Decided

- Board size and shape: CyberBrick-sized rectangle (29 x 30 mm) with the four CyberBrick mounting holes (23.0 x 24.0 mm), Zero in the middle.
- Power LED on the board (from the servo-port 5 V); the signal status is shown by the Zero's RGB LED in firmware.
- No spare GPIO header in this iteration, to keep the scope small (see "Out of scope").
- Speaker connector J2: JST SH 1.0 mm 2-pin, as used by the CyberBrick motor and button ports.
- The amplifier is a bare MAX98357A chip on the board, **assembled by a PCB service** (the TQFN-16 package is not practical to hand-solder). No plug-in breakout module.

## Decisions still open

- The speaker it has to carry (40 mm or a production candidate; see `sound-research.md`). The board size itself is settled: the outline of the Zero.
- Whether the Zero's underside is flat (the headers leave about 7 mm of clearance under it, enough for everything on the board; check the real module).
- ESP32-S3-Zero in a socket (replaceable) or soldered directly.
- How much the PCB service assembles besides the amplifier: only the SMD parts (and the rest by hand) or the whole board.

## Out of scope for this iteration

- ESP32 module directly on the board without the Zero (iteration 3, only if size or cost demands it).
- Further sound features beyond the current firmware.
- **Future option: spare inputs.** A connector for the unused GPIOs (IO12, IO11, IO10 and GND) for later inputs, for example a switch for an engine-stop sound. It has to be a cable connector, because a plain vertical pin header beside the Zero is hard to plug into from above; for example a JST SH 1.0 mm or a right-angle header at a board edge. Added only if a use turns up; the right-hand column of the Zero is left free for it.

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
| Speaker | JST SH 1.0 mm 2-pin side-entry SMD connector (for example SM02B-SRSS-TB; footprint about 4 x 4.3 mm, check the datasheet) + mating cable | 1 | same type as the CyberBrick M1/M2 and button ports; at the board end, plug enters from outside; rated about 1 A per contact, enough here (the whole module drew 105 mA at full throttle) |
| Input | 3-pin 2.54 mm right-angle pin header (S, V, G) | 1 | at the USB end of the board; mates with a 3-pin female servo/Dupont cable to PWM2 (check the orientation against the receiver's header) |
| | Resistor 1 kOhm | 1 | series resistor S to GPIO1 |
| | Resistor 100 kOhm | 1 | pull-down on GPIO1 (defined level when the cable is unplugged) |
| | ESD/TVS diode, low capacitance (optional) | 1 | on the S line |
| Power | Resettable fuse (PTC), about 0.5 A hold, 1206 | 1 | the module draws about 0.1 A average |
| | Reverse-polarity protection: Schottky diode in SOD-123 (rated 1 A or more) or P-MOSFET | 1 | a Schottky drops about 0.3-0.4 V, which is acceptable at this current (the amplifier needs 2.5-5.5 V) |
| | Diode (or ideal diode) between servo 5 V and USB 5 V | 1 | so both can be connected; check first whether the Zero's 5V pin already has a diode towards USB |
| | Ceramic capacitors 100 nF | 2-3 | general decoupling |
| Service | Test points (5 V, 3.3 V, GND, GPIO1, BCLK, LRC, DIN) | 7 | 1 mm pads on the bottom side |
| | Power LED (green, 0603) + 1 kOhm resistor | 1 + 1 | beside the Zero; about 3 mA from the servo-port 5 V |
| Mechanical | Mounting holes 2.7 mm, 23.0 x 24.0 mm apart | 4 | same pattern as the CyberBrick receiver shield |
