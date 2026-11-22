# Bluetooth link

Status: 2026-11-22. Part of the one firmware `engine_sets` (decided the same day: no alternative variants, nothing from
the older firmware is out in the world). It started as a prototype; the idea and the arguments are in `roadmap.md`
("Sound sets and firmware update over Bluetooth Low Energy"); this is what is built, how it behaves and what it showed.
USB stays as the basic and the backup way, see below.

## How it works for the user

Switch the receiver on. The module says a beep and a four digit PIN (twice) and for **3 minutes** it can be reached over
Bluetooth. On the page choose **Connect over Bluetooth**, pick `CBSound` (or `CBSound-<name of the module>`) and enter the
PIN. It does everything the USB link does (list, test, read, write, delete the sets). If something was written, deleted or
renamed, the module restarts after the page has left and Bluetooth stays off until the next power-up of the receiver;
otherwise the page may connect again within the 3 minutes.

## What was built

- **One firmware, `engine_sets`** (`pio run -e engine_sets -t upload`): Bluetooth is in it (`-DBLE_LINK_ENABLED=1` in
  `platformio.ini`; `=0` leaves it out). The firmware grows from 0.46 MB to 1.1 MB of the 1.5 MB app slot.
- **`firmware/include/ble_link.h`**: `BleUart`, a `Stream` over a Nordic-UART-like GATT service
  (service `6E400001-B5A0-F393-E0A9-E50E24DCCA9E`, RX write `...0002...`, TX notify `...0003...`). The Arduino core's own
  BLE library (Bluedroid), no download.
- **`SetLink` runs unchanged over it** (`SetLink::attach(Stream*)` in `set_link.h`): the same `@` commands as over USB.
  The end of a session (`@select`, `@demo`, `@stop`, changed files) is handled by one function, `applyEnd()`, for the
  USB and the Bluetooth link.
- **Advertising window:** the module advertises for 180 s after power-up and stays connected as long as the page is.
- **Page:** a `BleTransport` next to `SerialTransport` and the simulated module (`web/index.html`), a button "Connect
  over Bluetooth" (only shown where the browser has Web Bluetooth). The rest of the page is unchanged.

## What it showed

- Chrome/Edge on Windows connected to the module, listed the sets and read one (2026-11-22, the project owner).
- **Reading a set of about 0.5 MB (08 Retro, the Edit button) took about 20 s**, so about 25 kB/s. That is usable for
  sets (the seven default sets are 2 MB, a layered set 0.5 MB). Writing was not timed yet.
- The firmware of 0.5 to 1 MB would be about 20 to 40 s at this speed, if it ever went over this link.

## What is open (state 2026-11-22)

Everything the first prototype lacked is done or decided: the PIN, the name, the window of 3 minutes after the power-up, leaving the
session (restart after a change), writing sets and the firmware update. What stays open:

- **Firmware update over Bluetooth and USB: tried on the real module** (see the last sections); until then it has the risk that a
  new firmware that does not start can only be rescued over USB.
- **No trigger from the transmitter**: tried to think through and dropped as overkill (see "Decision: no trigger from the transmitter").
- **The firmware is one**: Bluetooth is part of `engine_sets`; there is no variant without it (it can be left out with `-DBLE_LINK_ENABLED=0`).

## Several modules: name and PIN (decided 2026-11-22, built)

- **Name of the module** (for example `Truck`, up to about 8 characters, because it goes into the BLE advertising
  of 31 bytes: `CBSound-Truck`). Kept in **NVS** (`Preferences`), not in the file system: `uploadfs` rewrites the whole data
  partition and would erase it. Set with a new command `@name <text>` from the page, reported in `@info`
  (`name=...`); the page shows it in the device list and in its status line. The module may speak it on entry.
- **PIN at the level of the protocol**, not the operating system's pairing: the first command of a session must be
  `@auth <pin>`, otherwise every command except `@hello` and `@info` answers `@err auth`. It works the same over Bluetooth
  and USB; over USB it is not needed (a cable is physical access) and stays off. Chosen over BLE passkey pairing because
  it needs no handling in the operating system and no stored bond, and it is easy to test.
- **The PIN is random for every service session and spoken by the module** when the service starts: "Bluetooth. Truck.
  PIN four two seven one." Nothing to remember or to write down, only someone standing at the model hears it, and with
  several modules each says its own name and PIN. The page asks for it after connecting. (A fixed PIN set over USB
  could be a fallback.)
- **Open:** how the spoken digits are made (the numbers of the sets are spoken from `number_names.js`; digits would need
  the same, as short clips in the firmware or as spoken numbers), the length of the PIN (4 digits is enough against
  someone passing by, the service is up for minutes only), a limit on wrong PINs (for example 3, then the service
  closes), and what happens when the module is mute.

## USB stays (decided 2026-11-22)

USB remains the basic and the backup way: the same protocol, no PIN, `pio` as before. It is also the way to the first
flash and the rescue when a firmware does not start (the bootloader is in the chip's ROM), and the way back after a
firmware update over Bluetooth into the other app slot. The normal `engine_sets` does not contain Bluetooth.

## The prototype with name and PIN (2026-11-22)

`engine_sets` has `@name` (NVS), `@auth <pin>` and `auth=`, `name=` in `@info`; a random 4 digit PIN per power-up,
spoken with digit clips from `/voice/d0.wav .. d9.wav` (`tools/make_voice_digits.py`, written by `uploadfs`) when the
advertising starts and every 40 s until the page has authenticated; 3 wrong PINs lock the Bluetooth link until restart;
after a disconnect the PIN is spoken again and the advertising window is renewed. The page asks for the PIN after
connecting over Bluetooth and has a "Module name" button. The PIN is also printed to the USB serial log.

## Tried without USB (2026-11-22)

The module powered only from the receiver (no USB), the spoken PIN, the page connected over Bluetooth and showed
"Connected over Bluetooth to Truck, firmware 0.1.0+f5d134c-dirty". The name (set over USB with `@name`, shown as
`CBSound-Truck`) and the PIN work. Windows may keep the old name of a device that was paired before (it showed
"CBSound" until the name was set). The advertising window of 3 minutes after power-up ended once before the page was
opened: the module must be restarted then (a real version needs a trigger from the transmitter instead).

## Writing a set over Bluetooth (2026-11-22)

A copy of the set 04 diesel (205 kB) was written to the module over Bluetooth, no USB: **12 kB/s, 17 s in all**. The first
try, with blocks of 200 bytes written with response, ran at only 1 kB/s (every write waited for its acknowledgement,
hundreds of ms): about 3 minutes for the same set, and an interrupted write left an empty folder (the module creates
it at the first `@put`; the files appear only when each transfer has ended with a right CRC). The page now writes
without response in blocks of 240 bytes (halved when the stack refuses), which gave the 12 kB/s. Reading was 25 kB/s
before. The page also got a progress bar with percentage, size, speed and time left, and a notice with a beep when a set
is written or deleted.

So over Bluetooth: a default-size set of 0.2 to 0.6 MB takes about 17 to 50 s to write.

## Behaviour agreed after the first trials (2026-11-22, built and tried)

- **Window of 3 minutes after a real power-up**: advertising and the PIN, spoken **once** after the name of the set
  (no repeating while nobody connects). If nobody connects in the 3 minutes, Bluetooth is switched off.
- **A page connects**: the PIN is spoken again (every 40 s) until it has been entered.
- **The page leaves**: advertising off, and after 1.5 s the module **restarts** (loads the new sets, frees the memory).
  After this restart Bluetooth stays **off** (the reset reason is a software reset), so it does not speak the PIN again
  after every session. It starts again at the next real power-up of the receiver.

## Reconnecting within the window (2026-11-22, built and tried)

- **The page leaves and nothing was changed** (only looked, read sets, or the link broke): no restart, the module advertises
  again until the 3 minutes after power-up are over; the page may connect again and again. The PIN is spoken again only
  when a page has connected and not yet entered it.
- **The page leaves after a change** (a set written, moved or deleted, or the name changed): advertising off and, after 1.5 s,
  a restart that loads the changes; Bluetooth stays off after it until the next real power-up of the receiver.
- Three wrong PINs lock the link until the next power-up, in both cases.

## How the PIN is spoken (2026-11-22, tried)

A short beep (`/voice/pin.wav`, 1 kHz, 0.22 s), the four digits in a row with gaps of about 160 ms (`/voice/d0.wav .. d9.wav`), a pause of 0.7 s, and
the four digits once more. Spoken once after power-up; again (every 40 s) only while a page has connected and not yet
entered the PIN. Until the PIN is entered, a Bluetooth session does not silence the engine output (it had cut the
spoken PIN into pieces before). Heard whole and without a break by the project owner after these changes.

**Clearer for the 40 mm speaker (2026-11-22, "much better" by the project owner):** the spoken digits are processed by
`tools/make_voice_digits.py` (`clarify`): high-pass at 250 Hz (the speaker plays nothing useful below), +7 dB presence around
2.5 kHz for the consonants, soft compression, peak at -1 dBFS; about 5 to 6 dB louder at the same peak. The word "Pin" was replaced
by the beep. The same treatment may help the spoken names of the sets (`name.wav`), which are not processed yet.

## Decision: no trigger from the transmitter (2026-11-22)

Starting Bluetooth from the transmitter (the free stick R3 held, an extra button) is judged overkill and is **dropped**. The way is
the window of 3 minutes after the power-up of the receiver, with the spoken PIN, the reconnecting within the window and the
restart after a change (see above). The rejected idea and its reasons: `rejected-ideas.md`.

**Digits of the PIN (2026-11-22, "much better"):** a PIN with five, six, seven and nine (5679) was hard to hear on the small speaker (five
and nine rhyme, six and seven begin alike). The PIN is now drawn only from the digits 0, 1, 2, 3, 4, 6 and 8 (2401 PINs, enough
for three tries before the lock), and the spoken digits are brought to a similar level (`equalise` in `tools/make_voice_digits.py`).

## Which spoken digits are easy to understand (2026-11-22)

Tried on the 40 mm speaker in its box (the owner, listening), English Piper voice, after the clarifying filter of
`tools/voice_clarify.py`:

| Digit | Heard | Why | Use |
|---|---|---|---|
| 0, 1, 2, 3, 4, 6, 8 | clear | different vowels and consonants | **recommended**, the PIN is made of these |
| 5 (five) | hard | rhymes with nine; the quiet fricative "f" is lost on the small speaker | **not recommended** |
| 7 (seven) | hard | begins like six, the two syllables run together | **not recommended** |
| 9 (nine) | hard | rhymes with five | **not recommended** |

The PIN never contains 5, 7 or 9. The same holds for any other thing that is only spoken: the spoken number at the start of
the name of a set ("Five.", "Seven.", "Nine.") is announced less clearly than the others, so a number given to a set by its
name text (for example "Seven. V twelve.") is the weaker way to tell sets apart; the name of the set that follows the number
is what makes it recognisable. The PIN was 5679 when this was found: "much worse", and 0, 1, 2, 3, 4, 6, 8 "much better".

**No same digit twice in a row (2026-11-22):** "two two" or "eight eight" runs together on the small speaker. The PIN is drawn from 0, 1, 2, 3, 4, 6, 8 so
that a digit is never the same as the one before it: 7 x 6 x 6 x 6 = 1512 PINs. With three tries before the lock and only the 3 minutes
after the power-up, the chance of a guess is 3/1512 (0.2 %), which is enough against someone passing by.

## Firmware update over the link (2026-11-22, built and tried)

The page's button **Update firmware** sends a firmware image over the link in use, USB or Bluetooth, with the protocol commands `@fwput <size> <crc>`,
`@fww <base64>` and `@fwend` (`set_link.h`). The module writes the image into the **other app slot** with the `Update` library (the running
firmware is never touched), checks the ESP32-S3 image header in the first block, the size and the CRC, makes the new slot the boot slot only at `@fwend`
and restarts 1.2 s after the reply. The page checks the file too (size 100 kB to 1.5 MB, header) and asks before it writes.

**Tried on the real module:** over USB (the image went at about 74 kB/s) and over Bluetooth with the spoken PIN (1.05 MB in 59 s, 18 kB/s): the module
restarted and came up as `0.1.0+32e540d`, the clean image, from `0.1.0+35d5699-dirty`. The file to choose is
`firmware/.pio/build/engine_sets/firmware.bin` (`pio run -e engine_sets`).

What the trials found: `@fwput` erases the other slot, which takes seconds, and the session timed out (3 s without a command) right after it, so the next block
was answered with "no @fwput". The time of the last command is now taken after the command has run. The page's progress bar for the update had first been
written into the editor, which was hidden: the update has its own bar under the list of sets.

**The risk stays:** there is no automatic return to the old firmware (the Arduino core's bootloader has no rollback). If a new firmware does not start, only USB
helps (`pio run -e engine_sets -t upload`; the bootloader is in the chip's ROM). The Bluetooth update therefore needs a PIN and the page warns before it writes.

## Overall volume (2026-11-22)

`@volume <0..100>` sets the volume of the whole module in percent, kept in NVS (the key `volume`, default 60 = the old fixed `MASTER_VOLUME` 0.6); `@info` reports
`volume=`. It scales the engine, starter, horn and shift (`masterVol` in `engine_sets/main.cpp`); the spoken names and the PIN digits are at full level already and follow it only
downwards (`voiceGain`). It takes effect when the session ends (the next Test). The page has the slider "Volume" above the list of sets.
