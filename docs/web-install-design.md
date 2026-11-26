# Design: first install of a new module from the web page

Status: 2026-11-26. **Design only, nothing is built.**

## Goal

A person with a new ESP32-S3-Zero-N8R8 opens the web page in Chrome or Edge, connects the module with a USB-C cable, presses one button
and gets a working module with the default sound sets. No PlatformIO, Python or Git.

Today the first install is by cable with PlatformIO (`first-install.md`). The page can only **update** a module that already runs
`engine_sets`, because it talks to that firmware. A blank module has no firmware to talk to.

## How it can work

The ROM bootloader of the ESP32-S3 can be reached from the browser over Web Serial. Two libraries do the flashing:

| Option | What it is | For and against |
|---|---|---|
| **ESP Web Tools** (proposed) | a ready button (a web component) that reads a `manifest.json` with the files and their offsets | least code, it handles the port choice, the chip check, progress and errors; the look of its dialog is its own |
| esptool-js | the flashing library underneath | full control of the page, but we write and test the whole dialog ourselves |

The library is loaded from a CDN with an exact version (both are Apache-2.0; check at implementation), as the page does for other libraries.

## What gets written

The 8 MB layout of `firmware/partitions_sets.csv`:

| Offset | File | Where it comes from |
|---|---|---|
| 0x0 | `bootloader.bin` | the PlatformIO build of `engine_sets` |
| 0x8000 | `partitions.bin` | the build |
| 0xe000 | `boot_app0.bin` | the Arduino framework package |
| 0x10000 | `firmware.bin` (about 1.1 MB) | the build |
| 0x310000 | `littlefs.bin` (4.9 MB, the whole data partition) | `tools/make_default_sets.py`, then `pio run -e engine_sets -t buildfs` |

The offsets of the first three files are the usual ones for this chip and framework; they are to be compared with the upload command that
PlatformIO prints, before the first test.

## Building and publishing

The files are not committed. A GitHub Actions job builds them and publishes them next to the page:

1. Check out the repository with its full history (the firmware version contains the commit hash).
2. Install Python, `platformio` and `numpy`.
3. `pio run -e engine_sets`, `python tools/make_default_sets.py`, `pio run -e engine_sets -t buildfs`.
4. Copy the five files to `web/firmware/` and write `manifest.json` (name, version, chip `ESP32-S3`, the files and offsets).
5. Publish `web/` on GitHub Pages (the existing workflow `.github/workflows/pages.yml`, extended).

**Proposed trigger: a version tag** (`v*`), not every commit. A new user then gets a version that someone tried on a module. The same files
can be attached to the GitHub release, so that old versions stay available. The page itself keeps being published on changes of `web/`; that
run has to take the files of the latest release, otherwise it would publish a page without them.

`make_default_sets.py` without Piper takes the spoken names from the repository, so the job needs no speech engine. Check that its output in
the job is the same as on a developer's computer.

## On the page

- A section **"New module"**, separate from the connect buttons, with the button **Install**.
- Before the button, in plain words: only the **ESP32-S3-Zero-N8R8** (8 MB flash, 8 MB PSRAM); the basic Zero with 2 MB PSRAM does not work,
  and the installer cannot tell them apart. Installing **overwrites all sound sets** on the module; for a module that already works use
  **Update firmware**.
- The name and the volume (NVS) stay, unless the user chooses to erase the whole flash.
- If no port appears: hold **B**, press and release **R**, release **B**; close other programs and tabs that hold the port.
- After the install: unplug and plug in again, then **Connect over USB**. The amplifier is powered from the receiver, so USB alone gives no sound.
- Desktop Chrome and Edge only (Web Serial).

## Licences

- The firmware is GPL v3 or later: the page says the version, links to the source at that commit, and the licence.
- The default sets contain third-party sounds: link to `assets/samples/LICENSE-SAMPLES.md`.
- List the licences of the libraries that are compiled into the firmware, since the binary is now distributed.

## Tests before it is published

1. A blank module: install, the module starts, speaks the name of the set, the page connects, seven sets are there.
2. A module with own sets and a name: the install overwrites the sets and keeps the name and volume.
3. A Zero with 2 MB PSRAM: what the user sees (the firmware says `sets: no PSRAM`); the text on the page must lead them there.
4. The cable pulled out during the install: install again works.
5. The version shown by the module is the version of the tag.

## Steps

1. The job that builds the five files and the manifest, checked by flashing them by hand with `esptool`.
2. The button on a test page, tried on a blank module.
3. The texts on the page, `first-install.md` and `getting-started.md` (the cable way stays as the backup).
4. The release tag and the publishing.

## Open questions

- Publish on a version tag (proposed) or on every change of the firmware?
- No spare blank module is available (owner, 2026-11-26). The tests use a working module whose flash is erased first (`pio run -e engine_sets -t erase`), which makes it behave like a new one. Its own sound sets, name and volume are lost, so save what matters with the page first; the cable install (`first-install.md`) brings the default state back. A bought spare module would avoid this. Test 3 (a Zero with 2 MB PSRAM) needs such a basic module and stays open without one.
