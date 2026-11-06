# CyberBrick configuration: Truck with Engine Sound

**Current configuration (use this one): `Truck_with_Engine_Sound_Data.json`** (tested on the truck on 2026-11-06)
together with the `engine_lab` firmware. Send it to both the transmitter and the receiver; the module's servo cable
goes to the receiver's **S4** port. The other files are kept for reference:

| File | Status |
|---|---|
| `Truck_with_Engine_Sound_Data.json` | **current**: channel data to the module, starts by itself; ignition, horn, lights |
| `Truck_with_Engine_Sound.json` | older: throttle copied to PWM2 as a servo pulse |
| `Truck_with_Engine_Sound_Button.json` | older: PWM2 plus the planned PWM3 button (superseded by the data) |
| `Truck_Code_Test.json` | test only: the two Code snippets on one button |
| `Truck_stock.json` | the original truck, no sound module |

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

## Truck_Code_Test.json (receiver "Code" experiment)
`Truck_stock.json` changed for the Code snippets in `docs/cyberbrick-code/` (written by hand on 2026-11-06, not an
app export, **not tried yet**):

- **LED2 is switched off** (no lights; it was first meant for the data wire, now PWM4 is used). The lights events on
  the R Stick and the L Shoulder Button are removed. **PWM4** stays unconfigured: the UART snippet sends on it.
- **CODE** holds two snippets: effect 1 = `blink_test.py`, effect 2 = `uart_forward.py` (comments removed).
- **L Shoulder Button** (K1, the only button the stock truck transmitter is sure to have): short press runs
  snippet 1 (the core LED blinks blue), long press runs snippet 2 (forward the channels over UART). Starting one
  snippet stops the other.
- Throttle and steering as in the stock truck; no PWM2 / PWM3 for the sound module.

The CODE entries follow what the receiver parser reads (`effect`, `code`); whether the app accepts them as they are
is not known. If the app does not show the two snippets after the import, add them in the app by hand instead.
Restore the truck afterwards with `Truck_stock.json` or `Truck_with_Engine_Sound_Button.json`.

## Truck_with_Engine_Sound_Data.json (sound module on channel data, tested 2026-11-06)
`Truck_stock.json` plus the data link to the sound module (2026-11-06):

- **The data starts by itself after power-up.** The L Stick X channel (unused in the truck) has its mid value moved
  to 600 (dead zone 100), so the stick at rest (about 2130) counts as "above mid" and the receiver fires its
  `gt_mid` event (above mid) on the first data after power-up; the event runs the Code snippet "Sound data"
  (`docs/cyberbrick-code/uart_forward.py`). The receiver's stick events fire only on a change, and every stick
  starts as "at mid", which is why the mid is moved instead of using an event at mid. Pushing the left stick
  fully left and back restarts the snippet (a short gap in the data).
- **L Shoulder Button**: short press = lights as in the stock truck; long press = start the snippet again (backup).
- The data goes out on the **PWM4** servo port (S4): S orange, G brown to the module; V stays disconnected while the
  Zero is on USB. PWM4 has no servo in this config (the earlier "Sound" servo there, which carried the throttle
  pulse until the long press, was removed).
- Sound module: `engine_lab` is silent after power-up; the ignition switch or the throttle starts the engine
  (`docs/start-stop-horn.md`).
