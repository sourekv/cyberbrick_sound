# CyberBrick configuration: Truck with Engine Sound

`Truck_with_Engine_Sound.json` is the official CyberBrick Truck configuration plus one extra servo output for the sound module:

- **PWM2 (Angular)**: min 45 deg, max 135 deg, speed 100 %, initial 90 deg (about 1.0-2.0 ms pulse, 1.5 ms at the centre)
- **L Stick, Y channel** drives both Throttle (motor M1) and PWM2, direction Negative

Our module listens to the PWM2 servo port; the motor keeps working as before. Only the names inside the file were changed; the settings are the app's export from 26 Oct 2026.

Use: import the file in the CyberBrick app, then **Send to Device** to the transmitter and to the receiver (both load the same configuration; each uses its own part). Not yet tested on real hardware. See `docs/bringup.md`.

## Truck_stock.json (baseline without sound)
The same configuration with the sound-module additions removed: PWM2 is empty and the L Stick Y channel drives only Throttle. It was derived from the engine-sound export by deleting those two entries, not exported from the app separately, so it may differ in small details from the original model's file. If exact fidelity matters, export the stock configuration from the app and replace this file.
