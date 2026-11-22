# Bluetooth link (prototype)

Status: prototype, 2026-11-22. It works, but it is not part of the normal firmware and has no security yet. The idea and
the arguments are in `roadmap.md` ("Sound sets and firmware update over Bluetooth Low Energy"); this is what was built
and what it showed.

## What was built

- **Firmware environment `engine_sets_ble`** (`pio run -e engine_sets_ble -t upload`): the `engine_sets` firmware with
  `-DBLE_LINK_ENABLED=1`. The normal `engine_sets` is unchanged and does not contain the Bluetooth code.
- **`firmware/include/ble_link.h`**: `BleUart`, a `Stream` over a Nordic-UART-like GATT service
  (service `6E400001-B5A0-F393-E0A9-E50E24DCCA9E`, RX write `...0002...`, TX notify `...0003...`). The Arduino core's own
  BLE library (Bluedroid), no download. The firmware grows from 0.46 MB to 1.09 MB (of the 1.5 MB app slot).
- **`SetLink` runs unchanged over it** (`SetLink::attach(Stream*)` in `set_link.h`): the same `@` commands as over USB.
  The end of a session (`@select`, `@demo`, `@stop`, changed files) is handled by one function, `applyEnd()`, for the
  USB and the Bluetooth link.
- **Advertising window:** the module advertises as `CBSound` for 180 s after power-up (the prototype's stand-in for a
  real trigger), and stays connected as long as the page is.
- **Page:** a `BleTransport` next to `SerialTransport` and the simulated module (`web/index.html`), a button "Connect
  over Bluetooth (prototype)" (only shown where the browser has Web Bluetooth). The rest of the page is unchanged.

## What it showed

- Chrome/Edge on Windows connected to the module, listed the sets and read one (2026-11-22, the project owner).
- **Reading a set of about 0.5 MB (08 Retro, the Edit button) took about 20 s**, so about 25 kB/s. That is usable for
  sets (the seven default sets are 2 MB, a layered set 0.5 MB). Writing was not timed yet.
- The firmware of 0.5 to 1 MB would be about 20 to 40 s at this speed, if it ever went over this link.

## Not done (what a real version needs)

- **A trigger** that is not "just after power-up". Planned: the free transmitter stick R3 held to its end for about
  3 s with the ignition off and the throttle at rest (the module already reads all channels), with a spoken
  "Bluetooth". BLE must not run while driving (the 2.4 GHz radio disturbs the receiver's link).
- **Pairing and a PIN.** Today anyone in range can connect during the window and rewrite or delete the sets.
- **Writing** to the module over Bluetooth was not tried (the page cuts lines into 200-byte writes with response, which
  is probably slower than reading).
- **Leaving the service mode:** after the page disconnects, after about 5 minutes of idle, or at power-off.
- **Firmware update over Bluetooth** into the other app slot (no way back if the new firmware does not start, without
  USB): after the sets work well.
- The firmware without the Bluetooth code stays the default; the Bluetooth build is 0.63 MB bigger. Deciding whether the
  Bluetooth service goes into the one normal firmware is open.
