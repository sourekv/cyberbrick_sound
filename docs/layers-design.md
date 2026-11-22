# Design: sample layers by rpm

Status: 2026-11-22. **The firmware is built and was tried on the module**: layers.h, the loader and the playback (commit b7ecc77); all eight old sets load and play as before, and the test set `09_layers` (three layers, `tools/make_mot_set.py --layered`) was judged "very good" by ear against the same recordings played faster. **Not done yet: the page and the PC tools** (they do not know layers: do not edit a layered set with the page). The idea and the prototype
result are in `roadmap.md` ("Sample layers by rpm"); this is the plan to build it. Set format today:
`user-sounds.md`; playback today: `firmware/src/engine_sets/main.cpp` (the block that mixes `idleWav` and `loadedWav`).

## Why

A sample set plays one loop faster as the rpm rises (`rate` 1.0x at idle to 3.0x at full throttle), which shifts the
whole spectrum, noise included, and sounds like a tape played fast. With several loops recorded at different
steady rpm, each loop is played only a little off its own speed. The PC prototype (2026-11-22, three layers cut from
old recordings) was called a big improvement.

## The rule that must hold

**A set without a `layers` list plays exactly as today.** Every set on the modules now (eight of them, the synth sets
included) keeps working, with no change of files. The new firmware is loaded with `upload` only; the data
partition and the sets in it stay.

## Set format

`set.json` of a layered sample set gets an optional list:

```json
{
 "name": "Retro",
 "type": "sample",
 "rate": [1.0, 3.0],
 "layers": [
  {"file": "layer_1.wav", "ratio": 1.0},
  {"file": "layer_2.wav", "ratio": 2.0},
  {"file": "layer_3.wav", "ratio": 2.3}
 ],
 "xfade": 0.36
}
```

- **`ratio`**: the pitch of the layer relative to the first one, measured as the firing frequency of the engine
  (the first layer, the idle one, is 1.0 by definition; layers are sorted by `ratio`, strictly rising). A layer
  recorded at twice the firing frequency of the idle layer has 2.0. The PC tool measures it (autocorrelation of the
  envelope, as the prototype did) and shows it, the user may correct it.
- **Target pitch** at engine speed `rpm` (0..1) is the one of today: `r = rate[0] + (rate[1] - rate[0]) * rpm`, in the
  same units (the idle loop played at `r` times its speed). So `rate` keeps its meaning, and a user who changes it
  changes how high the engine revs.
- **Layer `i` is played at `r / ratio_i`.** At idle that is 1.0 for the first layer, and so on.
- **Crossfade** between neighbours `i` and `i+1`: centred at the geometric mean of their ratios, width `xfade` in
  natural-log units (default 0.36, that is about plus or minus 19 %), equal power (cos / sin). Outside the crossfade
  only one layer plays. At most two layers play at a time.
- **No `idle.wav` and `loaded.wav`** in a layered set. The loaded blend of today (idle loop to loaded loop by the
  throttle) is not part of version 1: the prototype was judged without it. See "Open" for adding it.
- `name.wav`, `start.wav`, `horn.wav`, `shift.wav`, `level`, `stop_s`, `gearbox`, `eq` are unchanged. The layers
  are normalised by the user (or the tool) to about the same loudness.
- Limits: 2 to 8 layers, each a loop of 0.5 to 6 s, whole number of engine cycles, no seam (as `idle.wav` today).
  All layers together are loaded into PSRAM when the set is chosen, as the other files are (four layers of 2 to 4 s
  are about 0.4 to 0.7 MB).

## Firmware (`engine_sets`)

1. `sound_sets.h`: `SoundSet` gets `struct Layer { Clip clip; float ratio; }`, `std::vector<Layer> layers`,
   `xfade`; `release()` frees them. `SetLibrary::load()` reads `layers` when present: checks 2..8 entries, `ratio`
   strictly rising and positive, loads every file; a bad entry fails the load with a message over USB serial, as a
   missing file does today (the set is skipped, the module goes on to the next). Without `layers` nothing changes,
   `idle.wav` and `loaded.wav` stay required for a non-layered sample set.
2. A small header `layers.h` with the pure part, so it can be tested on the PC like `test_gearbox.cpp`: from `r`
   and the ratios it returns the two layers, their weights and their playback rates; and a player with one position
   per layer.
3. `main.cpp`: a new branch next to the `SoundSet::SAMPLE` one: if `cur.layers` is not empty, mix the (at most) two
   layers with their positions and rates, then the same gain, volume curve (0.55 + 0.45 * rpm), set EQ and level as
   today. The branch of today stays as it is.
4. `@info` and the log line say how many layers a set has (for the page and for debugging).
5. A firmware with layers cannot break old sets, but an **old firmware cannot play a layered set**: it looks for
   `idle.wav`, does not find it, skips the set and says so over USB. That is a safe failure, no crash.

CPU: two `playLoop` calls per sample instead of one (two with the loaded blend today as well), so no new load.

## Page (`web/index.html`) and the PC tool

- The set list shows a layered set (for example "3 layers"); the editor shows the layers with their file, `ratio`
  and a Play button (a layer at its own speed), and lets the user add, remove and reorder them (sorted by `ratio`).
- Drop a file on a layer row: the page measures the `ratio` against the first layer (same method as the
  prototype), the user may change it.
- A preview of the sweep (idle, up, down) like `AB_porovnani.wav`, rendered by the page with the same maths as the
  firmware, so the set can be judged before writing it.
- The check "a set is complete" accepts layers in place of `idle.wav` and `loaded.wav`.
- **A page that does not know layers must not damage a layered set.** The page that knows them is released together
  with the firmware; the page also shows the firmware version, so a layered set with an old firmware gets a warning.
- The simulated module of the page plays layered sets too.
- `tools/make_default_sets.py` and `tools/make_user_sounds.py` read `layers` too; `tools/make_mot_set.py` gets a
  layered variant of the Retro set as the first test material (the sources stay out of git).

## Tests

- **On the PC** (`firmware/test` style, g++ like `test_gearbox.cpp`): the weights are continuous in `rpm`, sum to 1
  in power, only two layers are ever active, the rates stay within the expected range, a set with ratios `1.0, 2.0,
  2.3` gives the same rates as the Python prototype (`work/layers_demo.py` figures).
- **Compatibility**: load all eight sets of today on the module and listen to each (start, throttle, shift, horn,
  stop), compare with a recording made before the change.
- **On the module**: a layered set with the Retro material, listened to at idle, mid and full throttle and over a
  sweep, and the PSRAM free figure in the log.

## Open

- **The load axis.** Today the throttle blends an idle loop with a loaded loop. Version 1 has none; if the layered
  sound lacks it, a second list `loaded_layers` (same ratios) could be blended by the throttle, doubling the memory.
  Decide after listening on the truck.
- **`xfade` default** (0.36 in the prototype): to be tuned by ear with better material (five layers instead of three).
- **Where `ratio` comes from when the first layer is not at idle.** Defined as relative to the first layer, so a
  set whose first layer is at higher rpm is also fine; `rate` then means the pitch of the first layer at `rpm` 0.
- **Better material**: clean steady loops at five or so rpm; today's recordings give three, two of them close.
- **Layers by other means** (grain synthesis from the recording) stay open as a different route, `roadmap.md`.
