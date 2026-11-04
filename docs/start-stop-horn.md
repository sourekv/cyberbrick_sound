# Engine start, stop and horn (design notes, not implemented)

Status: **thinking, not a task.** Nothing here is in the firmware, the shield or the CyberBrick config files yet. These notes record what was discussed and decided on 2026-11-01 and 2026-11-02 so the work can resume later.

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
3. The shield then needs a second servo input (signal through 1 kΩ to a free GPIO, for example GPIO2, with a pull-down; GND shared, V not connected). A draft of this was committed and reverted on 2026-11-01 (`91d2b26`, revert `54d28b3`) because it was only thinking aloud.

## Side research: listening to the radio link

The transmitter talks to the receiver over ESP-NOW (from forum posts and a community transmitter project; the official packet format is undocumented). The Zero could in principle listen to it and the servo input would not be needed.

Decided: **side research only, never a dependency of the main design.** The format may change with any CyberBrick firmware update, packets may be encrypted, receiving costs an estimated 80–100 mA more, and the Zero's antenna would need a copper keep-out on the shield. A first experiment would be a small sniffer firmware that prints frames from the transmitter while moving the sticks.
