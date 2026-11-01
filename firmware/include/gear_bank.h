#pragma once
// Per-gear sample bank for the `engine_gears` firmware: one loop for every gear of the virtual gearbox
// (include/gearbox.h). Gears may share a loop (the table just points at the same array, no extra flash).
// The loops are CC0 recordings from the Freesound "Vintage Trucks (Red Lib)" pack, see assets/samples/LICENSE-SAMPLES.md.
// To use another sample in a gear: generate a header with tools/make_gear_loop.py + tools/make_engine_diesel.py
// and change the table below.
#include <stdint.h>
#include "config.h"
#include "gear_a.h"   // GEAR_A / GEAR_A_LEN: R03-29 "Large Truck Constant Engine"
#include "gear_b.h"   // GEAR_B / GEAR_B_LEN: R03-32 "Old Truck Engine Working Hard"

struct GearSample { const int16_t* data; int len; };

static const GearSample GEAR_BANK[] = {
  {GEAR_A, GEAR_A_LEN},   // gear 1
  {GEAR_B, GEAR_B_LEN},   // gear 2
  {GEAR_B, GEAR_B_LEN},   // gear 3
  {GEAR_B, GEAR_B_LEN},   // gear 4
  {GEAR_B, GEAR_B_LEN},   // gear 5
};
static_assert(sizeof(GEAR_BANK) / sizeof(GEAR_BANK[0]) == GEAR_COUNT, "GEAR_BANK needs one entry per gear (GEAR_COUNT)");
