# Controls: transmitter, receiver program and sound module

What every control of the CyberBrick transmitter does in the truck with the sound module, and what our program on
the receiver does. Valid for the current configuration `docs/cyberbrick-config/Truck_with_Engine_Sound_Data.json`
with the `engine_lab` firmware (state of 2026-11-08). The module's servo cable goes to the receiver's **S4** header.

## What we added where

```
transmitter --radio--> receiver in the model --S4 servo header (S, V, G)--> sound module
```

| Where | What we added | Where in the config |
|---|---|---|
| Transmitter (CyberBrick Remote Control Transmitter Shield - XA003 XA005) | the trigger for the snippet: the moved centre of L2 (`mid_value` 600, `deadzone` 100) with a `gt_mid` event to CODE | `sender/channels[1]` |
| Transmitter | a long press of the L Shoulder Button to CODE (manual restart) | `sender/channels[6]/event[1]` |
| Receiver in the model (CyberBrick Remote Control Receiver Shield - XA003 XA004) | our Python snippet `uart_forward.py` (module CODE, "Sound data"): every 20 ms it takes all channels received over the radio and **sends them as serial data from servo header 4 (S4, pin S) to our module**; the module also takes its power from the same header (V, G) | `receiver_1/CODE` |
| Our module (ESP32-S3-Zero) | our firmware: reads the data from the receiver's S4 and makes the sound from it | - |

Bambu's original firmware is unchanged on both boards; only the configuration was changed.

## Transmitter controls

Channel names as in the receiver's data (`rc_module.rc_slave_data()`): sticks 0..4095, buttons 1 = released,
0 = pressed. Rest values are those of our transmitter.

| Control | Channel (rest) | Truck (receiver) | Sound module |
|---|---|---|---|
| Left stick, up / down | L3 (about 1830) | throttle, motor M1 | engine rpm and the virtual gearbox; moving it while the engine is off starts the engine at once, without the starter |
| Left stick, left / right | L2 (about 2130) | nothing | nothing; its centre is moved in the config so that it **starts the data program by itself** (see below) |
| Right stick, left / right | R2 (about 2030) | steering (servo S1, 50..130 deg) and the turn signals on LED2: left = left turn, right = right turn, back to the centre = lights off | nothing |
| Right stick, up / down | R3 (about 2050) | nothing | nothing |
| Left shoulder switch, 3 positions | L1 (left about 4089, middle about 1760, right about 0) | nothing | **ignition**: middle = off, left or right = on (see below) |
| Right shoulder stick | R1 (about 2260) | nothing | **horn**, pushed either way, as long as it is held |
| Left shoulder button | K1 | short press: lights on / off (LED2); long press: start the data program again | nothing |
| Buttons K2..K4 | K2..K4 | nothing | nothing |

Not used yet and free for later sound functions: R3, K2..K4 (L2 is taken by the auto-start, see its side effects).

## Engine sound: ignition, starter, stop, horn

Details and the reasoning in `start-stop-horn.md`; the code is `firmware/include/engine_events.h`.

- **After power-up the engine is silent.**
- **Ignition on** (switch from the middle to either side): the starter cranks for 1.1 s, the engine catches with a
  short rev and settles to idle. If the switch is already on a side when the data arrives, the starter runs at once.
- **Ignition off** (switch back to the middle): the engine winds down below idle in 1.4 s and goes silent.
- A new switch position must hold for 250 ms, so flipping from left to right through the middle does not stop the
  engine.
- **Throttle while the engine is off**: the engine runs at once without the starter, so the truck never moves in
  silence. It keeps running until the ignition goes on and off again.
- **Horn**: two tones (415 + 523 Hz), works with the engine on or off.
- All these sounds are synthesised in the firmware (no recordings).
- Data gaps: the frames sometimes pause for about 0.4 s; the engine state holds over gaps up to 2 s. After a longer
  loss of data the engine keeps its state (a running engine keeps running, a stopped one stays silent) and only the
  throttle, as a servo pulse if there is one, can start it; ignition and horn need the data.

## All sound effects: which ones the user controls

The module has five effects that the user triggers directly, and several that happen by themselves from the situation. Each set of sounds
holds the files for them (`user-sounds.md`, "Files of a set").

**The user controls these directly:**

| Effect | What triggers it |
|---|---|
| **Start of the engine**: the starter (`start.wav`, or synthesised), the engine catches with a short rev and settles to idle | the ignition switch (L1) moved from the middle to either side |
| **Stop of the engine**: it winds down below idle and goes silent (1.4 s) | the ignition switch back to the middle |
| **Running engine**: the rpm follows the throttle | left stick up / down (L3) |
| **Horn** (`horn.wav`, a loop for as long as the control is held) | right shoulder stick (R1), pushed either way |
| **Spoken name of the set** ("One. Truck.") | choosing a set with the BOOT button or in the web app |

**These happen by themselves, the user does not control them:**

| Effect | What causes it |
|---|---|
| **Loaded layer**: the "under load" sound is blended into the idle one | the size of the throttle, worked out by the module |
| **Gear shift**: on a shift to a higher gear the shift sound (`shift.wav`) and a short dip of the pitch, on a shift down a jump of the pitch | the virtual gearbox (five gears), worked out from the throttle |
| **Reverse**: no shift | the stick pushed the other way from forward |
| **The engine starts without the starter** | the throttle moved while the engine is off, so that the truck never moves in silence |
| **The shape of the stop** | the rpm at the moment of the stop: from full throttle it sounds different from one at idle |
| **Status LED** (not a sound): a blue flash after power-up, red without data, dim green at rest, brightening cyan with the throttle | the state of the data and the throttle |

Not effects, but worth knowing: the engine state is held over a data gap of up to 2 s, and the speaker EQ corrects the sound for the box.

## The program on the receiver ("Sound data")

The program runs on the receiver in the model (CyberBrick Remote Control Receiver Shield - XA003 XA004; an ESP32-C3
with MicroPython). It is our snippet `docs/cyberbrick-code/uart_forward.py`, stored in the receiver's part of the
config as the **Code** module with the effect name "Sound data". It is our own code and uses only the documented
`rc_module` and MicroPython; nothing of Bambu's firmware is changed.

- Every 20 ms it reads all ten channels that the receiver got from the transmitter over the radio.
- It sends them as serial data from the **S4** servo header (GPIO0), 115200 baud 8N1, in a frame of 23 bytes:
  `A5 5A`, ten 16-bit values little endian `[L1 L2 L3 R1 R2 R3 K1 K2 K3 K4]`, XOR of the 20 data bytes.
  Measured: about 27 frames per second, no checksum errors.
- On the module the data arrive on the same input as the old servo pulse (GPIO1, through 1 kOhm), so the firmware
  still works with the older pulse configurations.
- The program runs until the receiver is switched off or another Code program is started (only one runs at a
  time).

## How the program starts by itself

The app has no "run at power-up" option: a Code program only starts on an **event** from the transmitter, a button
press or a stick movement. Stick events work like this:

- every stick channel has a **centre** (`mid_value`) and a **dead zone** around it;
- leaving the dead zone fires an event, "greater than the centre" (`gt_mid`) or "less than the centre" (`lt_mid`);
- after power-up the receiver assumes that every stick is in its centre, so an event only fires when the value
  from the transmitter is outside the dead zone.

The trick: the left stick's left / right channel (L2) rests at about **2130**, but its centre in the config is set to
**600** with a dead zone of 100. To the receiver the stick at rest is therefore "far to the right". The first data
after power-up (2130 > 700) fire `gt_mid`, and that event starts "Sound data".

Side effects:

- L2 cannot be used for anything else: moving the stick far to the left (below 700) and back would start the
  program again, with a short gap in the data. The truck does not use this channel.
- If the program stops (for example because another Code program was started), a **long press of the left
  shoulder button** starts it again.

## Power-up order

1. Switch on the transmitter and the truck (any order). The receiver and the transmitter pair.
2. The data start by themselves within about a second; the engine stays silent.
3. Turn the ignition on (switch to either side), or just drive off.

The sound module is powered from the receiver's servo header. USB (flashing, tests) may stay connected with the
receiver on, thanks to the 1N5819 in the breadboard's V wire; without that diode the V wire must be disconnected
first (`bringup.md`).

## Files

| File | What |
|---|---|
| `docs/cyberbrick-config/Truck_with_Engine_Sound_Data.json` | the configuration to send to the transmitter and the receiver |
| `docs/cyberbrick-code/uart_forward.py` | the receiver program (readable version with comments; the config holds the same code without comments) |
| `firmware/include/rc_link.h` | reading the frames on the module |
| `firmware/include/engine_events.h` | ignition, starter, stop, horn |
| `firmware/include/config.h` | thresholds: `RC_IGNITION_*`, `RC_HORN_*`, `RC_THROTTLE_*`, timeouts |
| `start-stop-horn.md` | design of start, stop and horn |
