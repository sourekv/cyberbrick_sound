# CyberBrick configuration: Truck with Engine Sound

`Truck_with_Engine_Sound.json` is the official CyberBrick Truck configuration plus one extra servo output for the sound module:

- **PWM2 (Angular)**: min 45 deg, max 135 deg, speed 100 %, initial 90 deg (about 1.0-2.0 ms pulse, 1.5 ms at the centre)
- **L Stick, Y channel** drives both Throttle (motor M1) and PWM2, direction Negative

Our module listens to the PWM2 servo port; the motor keeps working as before. Only the names inside the file were changed; the settings are the app's export from 26 Oct 2026.

Use: import the file in the CyberBrick app, then **Send to Device** to the transmitter and to the receiver (both load the same configuration; each uses its own part). Not yet tested on real hardware. See `docs/bringup.md`.

## Truck_stock.json (baseline without sound)
The original CyberBrick Truck configuration exactly as exported from the app, without any of our additions: PWM2 is empty and the L Stick Y channel drives only Throttle. Use it to restore the stock behaviour.

## Truck_with_Engine_Sound_Button.json (start/stop/horn button)
`Truck_with_Engine_Sound.json` plus one button for the planned start/stop/horn feature (see `docs/start-stop-horn.md`), exported from the app by the project owner on 1 Nov 2026:

- **PWM3 (Angular)**: min 45 deg, max 135 deg, speed 100 %, initial 90 deg, centre offset 0
- **Button channel "StartStopHorn"**, event **Short Hold** (`short`) sets PWM3 to **45 and 135 deg, alternating on each press**

After power-up PWM3 sits at the centre (about 1.5 ms); each press then flips it between about 1.0 and 2.0 ms, and the module treats every change as one press. Not yet tested on hardware, and the firmware does not read PWM3 yet.
