# First install by cable

How to put the firmware and the default sound sets on a new module, from nothing. After this one time, everything else
(sets, the volume, a new firmware) can also be done from the web page, over USB or over Bluetooth (`user-guide.md`,
`ble-link.md`). The cable stays the backup way: if a firmware does not start, this is the way to fix it.

## What you need

- **The module:** a Waveshare **ESP32-S3-Zero-N8R8** (8 MB flash, 8 MB PSRAM; with the pin headers, the "-M" version, if it goes into the
  shield sockets). The basic ESP32-S3-Zero with 2 MB PSRAM does **not** work: the firmware says `sets: no PSRAM (an N8R8 Zero is needed)`.
- **A USB-C data cable** (not a charge-only one) and a computer with a free USB port.
- **PlatformIO** to build and write the firmware: the VS Code extension "PlatformIO IDE" (the easiest), or on the command line
  `pip install platformio` (then `pio` works in a new terminal). The first build downloads the ESP32 platform (`espressif32@6.9.0`) and the
  Arduino framework, so it needs the internet and a few minutes.
- **Python 3 with `numpy`** to make the default sound sets (`pip install numpy`). Nothing else is needed: the spoken names of the
  default sets are in the repository, so you do not need Piper.
- **Git** to get the repository (or download it as a ZIP from GitHub and unpack it).
- **A driver for the USB port:** normally none. The Zero shows up as a "USB JTAG/serial debug unit", which Windows 10 and 11, macOS and Linux
  know; an older Windows may need the driver from Espressif.
- **Chrome or Edge** for the web page afterwards (not Safari or Firefox).

Get the repository (`git clone`) and open a terminal in it.

## 1. The firmware

```powershell
cd firmware
pio run -e engine_sets -t upload
```

`engine_sets` is the one firmware (sounds as sets, the web link over USB and Bluetooth). PlatformIO finds the port itself and
writes the firmware; at the end it says `SUCCESS`. About one minute the first time.

**No port found?** A brand new Zero should appear as a "USB JTAG/serial debug unit". If it does not, put it into the
bootloader by hand: hold the button marked **B** (BOOT), press and release **R** (RESET), release **B**, and run the command again.
Another program that holds the port (a serial monitor, a browser tab with the web page connected) also blocks it: close it.

## 2. The default sets

The firmware starts with no sets and then plays a built-in sound. The sets are written to a separate data partition:

```powershell
cd ..
python tools/make_default_sets.py
cd firmware
pio run -e engine_sets -t uploadfs
```

`make_default_sets.py` builds the seven default sets (`01_truck` ... `10_v12`, about 2 MB) into `firmware/data/sets`; `uploadfs` writes
the whole data partition (about 5 MB, 40 seconds) and restarts the module. It overwrites all sets, so do it only on a new module or when
you want the default sets back.

## 3. Check that it works

- **The log:** `pio device monitor` (115200) shows at start `cyberbrick_sound engine_sets 0.1.0+<hash>`, `sets: 7 found` and the name of the set that
  is chosen. Close the monitor afterwards.
- **The sound:** the module speaks the number and the name of the set (for example "One. Truck.") and, with the speaker, you hear it. The amplifier is
  powered only from the receiver, so with USB alone you hear **nothing**: connect the servo cable to the receiver's S4 and switch the receiver on
  (`shield-pcb.md`, `controls.md`; the receiver needs the configuration `docs/cyberbrick-config/Truck_with_Engine_Sound_Data.json`).
- **The web page:** open `web/index.html` in Chrome or Edge, press **Connect over USB**, choose the module's port. It shows "Connected, firmware
  0.1.0+<hash>" and the list of sets. **Test** plays a set.

## 4. What next

- **Your own name and volume:** **Module name** and the **Volume** slider on the page (60 % is the default).
- **Without a cable from now on:** switch the receiver off and on; for 3 minutes the module can be reached over Bluetooth (a beep and a spoken PIN, then
  **Connect over Bluetooth** on the page). Sets and a new firmware (the button **Update firmware**, with `firmware/.pio/build/engine_sets/firmware.bin`
  from `pio run -e engine_sets`) go the same way (`ble-link.md`).
- **Your own sounds:** `user-guide.md`.

## When something does not work

| What you see | What to do |
|---|---|
| `pio` cannot find the port | A data cable, the bootloader by hand (above), another program holding the port. |
| `sets: no PSRAM (an N8R8 Zero is needed)` in the log | The module is the basic ESP32-S3-Zero without the 8 MB PSRAM: use the N8R8 version. |
| `sets: no file system in the data partition` or `no /sets folder` | `uploadfs` has not been done: step 2. |
| The page says "the module does not answer" | The module has another firmware or the port is held elsewhere: step 1, and close other programs. |
| The module starts and is silent | USB alone does not power the amplifier: the receiver must be on and the servo cable in S4. |
| A firmware that does not start after an update over the link | Fix it over USB: `pio run -e engine_sets -t upload` (the bootloader is in the chip's ROM and always works). |
