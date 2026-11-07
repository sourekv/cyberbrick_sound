# Engine start, stop and horn

## Implemented with the channel data (2026-11-06, first version, to be tried)

With the receiver's channel data on a wire (`docs/cyberbrick-code/`, `Truck_with_Engine_Sound_Data.json`) the
module sees every control of the transmitter, so the one-button design below is no longer needed. `engine_lab`
(`include/engine_events.h`) now does:

| Control | Action |
|---|---|
| **Left shoulder 3-position switch** (L1) = ignition: **middle = OFF, left or right = ON** | moved from the middle to either side: **starter** cranks for 1.1 s, the engine catches with a short rev and settles to idle; moved back to the middle: the engine **winds down** below idle (1.4 s) and goes silent |
| **Throttle** while the engine is off | the engine runs at once, without the starter (the sound is never silent while the truck moves); it stays on until the switch goes ON and back to OFF |
| **Right shoulder stick** (R1), pushed either way | **horn** (two-tone, 415 + 523 Hz), as long as it is held; works with the engine off too |
| L Shoulder Button | unchanged: short = lights, long = start the data |

- Switch values: left about 4089, middle about 1760, right about 0 (`RC_IGNITION_MID`, `RC_IGNITION_BAND` in
  `config.h`). A new position must hold for 250 ms, so flipping from left to right through the middle does not stop
  the engine. (First version had OFF on the right end; changed on the owner's request.)
- After power-up the engine is **silent**. The data starts by itself (`Truck_with_Engine_Sound_Data.json`); if the
  switch is already on a side when the data arrives, the starter runs at once.
- Without channel data (servo pulse only, older configs) the engine starts with the throttle, without a starter,
  and then keeps running; no ignition or horn.
- The frames sometimes pause for about 0.4 s; the engine state holds over gaps up to 2 s (`RC_STATE_HOLD_MS`), so a
  stopped engine does not blip on. Only after a longer loss does the module go back to the plain running engine.
- The starter, the stall and the horn are synthesised in the firmware (no recordings, no licences). The samples
  chosen below are not used.
- Not done yet: stalling by itself after a long idle, reverse beeper.

## Earlier design notes (one button through PWM3)


Status of this part: superseded by the section above. When written: **thinking, not a task.** Nothing here was in the firmware, the shield or the CyberBrick config files yet. These notes record what was discussed and decided on 2026-11-01 and 2026-11-02 so the work can resume later.

## Idea

One transmitter button controls engine sounds, depending on what the truck is doing:

| Situation | Button press |
|---|---|
| Throttle at rest, engine sound off | **start**: start sample, then idle |
| Throttle at rest, engine sound running | **stop**: stop (stall) sample, then silence |
| Truck moving (throttle off rest) | **horn**, fixed length |

## How the button reaches the module

The CyberBrick receiver has no inputs, only outputs, so the button is passed through a second servo port, the same way the throttle is copied to PWM2.

- App setup (tried in the app, not yet on hardware): receiver **PWM3** as an Angular Servo, min 45°, max 135°, speed 100 %, centre offset 0°. Transmitter button event **Short Hold → PWM3, values 45° and 135°** (added with +Add; the values alternate on each press).
- The module sees **every change of the PWM3 pulse width** (more than ~0.3 ms, stable for ~100 ms as debounce) as one press. Whether it means start, stop or horn is decided by the module from its own state, so the order of the values does not matter.
- The initial value cannot be set in the app's servo dialog; after power-up PWM3 is expected to sit near the centre (~1.5 ms) until the first press.
- Long Hold stays free for later. A double press could be detected in the module by timing, but it is not needed.
- The horn has a fixed length because the module cannot tell how long the button is held.
- Code snippets (MicroPython in the CyberBrick app) were looked at and rejected: isolated, no state, 2048-character limit. Built-in rules are enough.

## Engine state rules

- After the receiver is powered on: **engine off, silence.** The engine starts on a button press, or when the throttle leaves rest; in the second case the start sample is skipped and the sound picks up the throttle position directly (a short ~0.3 s ramp was suggested so a full throttle does not jump straight to 5th gear).
- A press during the start sample with the throttle moving: skip the rest of the start, follow the throttle.
- Throttle moved while the stop sample plays: **interrupt the stop** (fade ~30–50 ms) and go straight to the engine sound for the current throttle position (same ramp note as above).
- Missing or out-of-range PWM3 pulse: state unchanged. PWM2 signal lost: idle, as today.
- Idea (2026-11-03, not decided): after the throttle has been at rest for a longer time, the engine could stall by itself (stop sample, then silence), as if left idling. The timeout is open.
- The sound never goes silent while the truck moves; the button cannot stop the real motor (the app has no way to make M1 depend on the button), so this is a sound effect only.

## Samples chosen for a first try

Authors are credited in `assets/samples/LICENSE-SAMPLES.md` when the samples are added. **CC BY samples are acceptable** with attribution (decided 2026-11-02); until then the rule had been CC0 only.

| Use | Recording | Licence | Cut |
|---|---|---|---|
| Start and stop | the_bloke33, "Diesel Car Star Rev Stop.mp3", https://freesound.org/people/the_bloke33/sounds/75362/ (Peugeot 406, 2009, MP3 128 kbps, 20.5 s) | CC BY 3.0 | start 0–2.5 s, stop ~13.5–15.4 s |
| Horn | danlucaz, "Truck Horn", https://freesound.org/people/danlucaz/sounds/513741/ (0.57 s, 44.1 kHz WAV) | CC0 (the author asks for credit; we give it) | whole |

Licences were read from the Freesound pages pasted by the project owner on 2026-11-02. Both are "for a start"; the Peugeot is a passenger car and a dull MP3, not a truck.

Also considered: phenoxy "Diesel_start_idle2.wav" (https://freesound.org/people/phenoxy/sounds/195451/, CC BY 4.0, clean ~2 s start, no stop); DominikBraun "Bus Truck Horn Blast" (https://freesound.org/people/DominikBraun/sounds/504565/, CC BY 4.0, nine two-tone blasts, more European than an American air horn); BigSoundBank "Truck horn" (https://bigsoundbank.com/truck-horn-s2721.html, CC0, air horn, not listened to yet).

## Still to check on hardware

0. Safety: the measurement runs over USB, so the servo cable's V (red) wire must be disconnected first; only signal (through 1 kΩ) and GND go to the Zero (see the rule at the top of `bringup.md`).
1. Send the config to both cores (Bluetooth, "Send to Device") and measure the PWM3 pulse with `pulse_measure` on a second pin: does it change on every Short Hold press and hold its value?
2. Does the receiver keep sending pulses when the transmitter is off or out of range?
3. ~~The shield then needs a second servo input (signal through 1 kΩ to a free GPIO, for example GPIO2, with a pull-down; GND shared, V not connected).~~ Dropped on 2026-11-07: the channel data on one cable replaces it, see the top of this file. A draft of this was committed and reverted on 2026-11-01 (`91d2b26`, revert `54d28b3`) because it was only thinking aloud.

## Side research: listening to the radio link

The transmitter talks to the receiver over ESP-NOW (from forum posts and a community transmitter project; the official packet format is undocumented). The Zero could in principle listen to it and the servo input would not be needed.

Decided: **side research only, never a dependency of the main design.** The format may change with any CyberBrick firmware update, packets may be encrypted, receiving costs an estimated 80–100 mA more, and the Zero's antenna would need a copper keep-out on the shield. A first experiment would be a small sniffer firmware that prints frames from the transmitter while moving the sticks.

### Result of the first experiment (2026-11-05): the payload is encrypted

Firmware `espnow_sniff` (listens only, never transmits; promiscuous mode, channels 1..13, also 802.11 LR) on the
prototype Zero, transmitter and receiver switched on and bound:

- ESP-NOW frames were found on **Wi-Fi channel 2** from two senders, `80:F1:B2:34:1A:B8` (about 10-20 frames/s,
  59 bytes, RSSI about -45 dBm; sends to the other one, so most likely the **transmitter**) and `80:F1:B2:19:48:74`
  (about 1 frame/s, 44 bytes, RSSI about -25 dBm next to the breadboard; most likely the **receiver** answering).
  The 802.11 "protected" bit is not set.
- Frame layout: byte 0 = `2A`, byte 1 = length of the rest after byte 19 (`27` = 39, `18` = 24), bytes 2-3 change
  in every frame (nonce or checksum), bytes 4-7 = `41 40 00 00`, bytes 8-13 = destination MAC, bytes 14-19 = source
  MAC, then the data.
- 40 s test with timestamps: 10 s at rest, 10 s moving the throttle stick end to end, 10 s pressing the button, 10 s
  at rest. **Nothing in the frames followed the stick or the button**: the same length (59, sometimes 60) and the
  same frame rate in all four phases, and every data byte after byte 19 takes a different value in practically
  every frame even at rest (126-134 distinct values per byte position in 190 frames).
- That is what encrypted data with a per-frame nonce looks like (application-level encryption, not the ESP-NOW
  built-in one). Without the key it cannot be read, and the CyberBrick cores use flash encryption and secure boot,
  so the key is not reachable.

**Conclusion: investigated, no result. The data cannot be read, the servo-port input stays.** The side research
is closed. Breaking or bypassing the CyberBrick encryption is not an option for this project. The sniffer firmware
was not kept in the repository; it was a short promiscuous-mode program and can be rewritten if Bambu ever
publishes the protocol or stops encrypting it.

## Option found later: the receiver's own, documented data API (2026-11-06, not tried)

Bambu publishes the MicroPython application of the CyberBrick cores at
https://github.com/CyberBrick-Official/CyberBrick_Controller_Core (read 2026-11-06; the code was not copied into
this repository):

- The receiver and the transmitter run the same ESP32-C3 core board with MicroPython; `src/app_rc/app/rc_main.py`
  picks the role from GPIO10 at start-up. The receiver application (`control.py`, `parser.py`, `bbl/servos.py`,
  ...) is source code; the radio itself, its encryption and the pin numbers of the servo outputs live in the
  closed, built-in module `rc_module`.
- `docs/cyberbrick_core/lib/rc_module.rst` documents `rc_module.rc_slave_data()`: on the receiver it returns the
  transmitter's channels **already decoded**, as `[L1, L2, L3, R1, R2, R3, K1, K2, K3, K4]` (six stick channels as
  ADC values 0..4095, four buttons as 0/1), or `None` when not paired. The receiver's main loop calls it every
  20 ms. `rc_index()` gives which of the two receivers this is.
- The servo outputs are ordinary 50 Hz PWM (`bbl/servos.py`), which is what the module reads on GPIO1 today.
- Pins used by the receiver application: 0..5 outputs (also the wake-up pins for deep sleep), 8 the RGB LED, 9 the
  board key, 10 the role pin. Which other pins of the core board are brought out is not documented there.

So the decoded data is available on the receiver through an official interface; nothing has to be broken. A small
piece of code on the receiver could send all ten channels over a wire (for example UART) to the sound module:
throttle, the start/stop/horn button and the other sticks at once, without using a servo output for each.

Open points before trying it:

- **Licence.** The "CyberBrick Codebase License" allows use only through MakerWorld's services and products (or with
  written permission) and requires the licence notice in all copies. Modified receiver code therefore does not go
  into this repository as it is; check whether a snippet through the official "Code" option of the CyberBrick app
  is enough, or keep the change local.
- **A free pin** on the receiver core for the data wire (GPIO 20/21 are the ESP32-C3 UART0 pins, but whether they are
  brought out and unused is not known).
- **Getting back** to the original receiver application before changing anything (the app can re-send the
  configuration; whether it restores the application files was not checked).
- Shared ground and a 3.3 V signal level between the receiver core and the Zero; the [USB power
  rule](bringup.md) still applies.

### The "Code" option of the CyberBrick app (read from the receiver source, 2026-11-06, not tried)

How a code snippet runs on the receiver (`src/app_rc/app/control.py`, `src/app_rc/bbl/executor.py` in the Bambu
repository):

- A snippet is stored in the configuration JSON (`CODE` section) and started as the action of an **event**: short or
  long press, press or release of a button, or a stick above, at or below its centre. One snippet runs at a time;
  starting another stops the running one.
- It runs as full MicroPython, as an asyncio task next to the normal control loop. The executor rejects lines that
  contain `exit`, `quit`, `sys.exit`, `os.system`, `__import__`, `open`, `eval`, `exec`, `subprocess`, `os.remove`
  or `os.rmdir`. Importing `machine` (UART, Pin) or `rc_module` is not blocked.
- It rewrites `time.sleep(x)` into `await asyncio.sleep(x)` and `while True:` into a loop that ends when the snippet
  is stopped, so an endless loop is allowed and does not block the receiver.

Receiver pins (constants in `src/app_rc/bbl/*.py`):

| Receiver output | Core GPIO |
|---|---|
| PWM1, PWM2, PWM3, PWM4 (servo ports) | 3, 2, 1, 0 |
| LED1 / buzzer 1 | 21 |
| LED2 / buzzer 2 | 20 |
| RGB LED on the core | 8 |
| Board key | 9 |
| Role pin (transmitter / receiver) | 10 |

Idea: a snippet started by a button that reads `rc_module.rc_slave_data()` every 20 ms and sends the ten channels as
a short UART frame from the **LED2 port (GPIO20)**, so all servo ports stay free. One data wire plus GND to the sound
module, 3.3 V logic on both sides. The snippet is our own code sent through Bambu's official app, nothing in the
receiver's files changes, and no Bambu code is copied.

To find out by testing:

- Whether the snippet can start by itself after power-up, or a button has to be pressed once every time.
- Whether the LED port stays ours while the configuration does not use it for lights (the receiver resets the LED
  ports when it reloads the configuration).
- The UART RX pin must be set explicitly to a pin that is not used, otherwise the default may collide with the board
  key.
- Frame rate, frame format and checksum, and what the sound module does when frames stop (fall back to the servo
  input).

First test, without risk: receiver on the model battery, Zero on USB, only GND and the data wire between them (the
V wire disconnected, [USB power rule](bringup.md)); a small firmware on the Zero only prints what arrives over UART.
