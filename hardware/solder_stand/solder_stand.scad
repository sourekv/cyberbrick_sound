// Soldering stand for the shield PCB (hardware/shield/): holds the board upside down while the hand-fitted parts
// are soldered (J3/J4 female socket strips 1x9, J1 right-angle servo header 1x3).
//
// How it is used:
//   1. Plug both 1x9 socket strips onto the pins of the ESP32-S3-Zero-N8R8-M; the Zero keeps them parallel and at
//      the right spacing (15.24 mm), so no other jig is needed for that.
//   2. Put a piece of soft foam (anti-static foam or sponge, about 5-8 mm thick) into the pocket.
//   3. Push the socket strips with the Zero into the board from the top side, put J1 in, and lay the board upside
//      down on the stand: the four pins go into the mounting holes, the Zero sinks into the pocket and the foam
//      presses it (and so the sockets) up against the board. The J1 plastic body lies on the ledge at the edge,
//      flat against the board.
//   4. Solder one pin at each end of every strip, check that everything sits flat, then solder the rest.
// The board rests on the four posts by the copper rings around the mounting holes; nothing else on the top side
// touches the stand (the parts under the Zero and C1/J2/LED1 beside it are all in the open pocket).
//
// All positions come from hardware/shield/shield.kicad_pcb (board 29 x 30 mm, outline 100..129 / 100..130 in the
// KiCad coordinates, used here directly; holes at +-11.5 / +-12.0 mm from the centre). The stand is symmetric about
// the board's long axis (J1 is centred on it), so it does not matter that the board lies mirrored.
// The Zero's stack height (socket 8.5 mm + its header + its own parts) was not measured; the foam takes up the
// difference, so only post_h has to be larger than the stack (about 14-15 mm).
//
// Print: PLA or PETG, flat on the base, no supports, 0.2 mm layers are fine.
// Export (OpenSCAD 2021.01):
//   openscad -o solder_stand.stl solder_stand.scad
//   openscad -o solder_stand_preview.png -D 'part="preview"' solder_stand.scad   (with the board, not for printing)
//   solder_stand_steps.png: three renders with -D 'part="assembly"' -D explode=45 / 18 / 0 (Tomorrow colour scheme),
//   joined with ImageMagick montage

part = "stand";      // "stand" or "preview" (stand with the board and the Zero as ghosts)

base_t     = 8.0;    // base plate thickness (heavier, so the stand does not tip over; thick enough for the band grooves below it)
groove_w   = 4.5;    // grooves in the underside of the base for rubber bands (a band of about 3 mm), one set each way
groove_d   = 3.0;    // groove depth (the base keeps 5 mm above it)
base_w     = 80.0;   // base plate, square, centred under the board (the stand is about 25 mm tall)
post_h     = 18.0;   // base top to the board's top side (must clear the Zero stack, foam fills the rest)
post_d     = 4.0;    // post diameter; the copper ring is 6.0 mm, J3 starts 2.6 mm and the Zero corner about 2.5 mm from the hole centre
pin_d      = 2.3;    // locating pin in the 2.7 mm hole
pin_h      = 2.2;    // through the 1.6 mm board and a little past it
board_t    = 1.6;

// board, KiCad coordinates (y grows downwards in KiCad; here it is just a mirror, see above)
bx0 = 100; bx1 = 129; by0 = 100; by1 = 130;
cx  = (bx0 + bx1) / 2;  cy = (by0 + by1) / 2;
holes = [[cx - 11.5, cy - 12], [cx + 11.5, cy - 12], [cx - 11.5, cy + 12], [cx + 11.5, cy + 12]];

// J1: PinHeader_1x03_P2.54mm_Horizontal at (111.96, 104.15), rotated 90 deg: the pins run along x
// (111.96 / 114.50 / 117.04), the plastic body lies on the board from y 100.05 to 102.71 (2.54 mm thick), the long
// pins stick out over the top edge to y 94.05.
j1_x0 = 111.96 - 1.6;  j1_x1 = 117.04 + 1.6;
j1_body_t = 2.54;
j1_y_in   = 101.8;   // ledge stops here, short of the Zero's USB-C end (Zero about y 103.2..126.8)
j1_y_out  = by0 - 7.5;
guide_w   = 1.6;     // side guides beside the body
comb_l    = 6.0;     // comb under the long pins (from j1_y_out to 1.5 mm short of the board edge)
slot_w    = 0.9;     // slot for a 0.64 mm square pin

$fn = 48;

module stand() {
  difference() {
    union() {
      // base plate
      translate([cx - base_w / 2, cy - base_w / 2, 0]) cube([base_w, base_w, base_t]);
      // posts with locating pins
      // each post is braced outwards to the board corner (nothing is fitted there), so it does not bend when the
      // board is pressed down while soldering
      for (h = holes) translate([h[0], h[1], 0]) {
        sx = h[0] < cx ? -1 : 1;  sy = h[1] < cy ? -1 : 1;
        hull() {
          cylinder(d = post_d, h = base_t + post_h);
          translate([sx * 4, sy * 4, 0]) cylinder(d = post_d, h = base_t + post_h);
        }
        translate([0, 0, base_t + post_h]) {
          cylinder(d = pin_d, h = pin_h - 0.5);
          translate([0, 0, pin_h - 0.5]) cylinder(d1 = pin_d, d2 = pin_d - 0.8, h = 0.5);
        }
      }
      // ledge under the J1 plastic body (the pins over the edge stay 0.9 mm above it)
      translate([j1_x0, j1_y_out, 0])
        cube([j1_x1 - j1_x0, j1_y_in - j1_y_out, base_t + post_h - j1_body_t]);
      // shelf in the air under the body of J1 when it is fitted from the UNDERSIDE of the board and turned by 180 degrees (pins pointing
      // into the board, docs/shield-pcb.md "The servo connector on the underside"; soldered in a separate pass, the board lying top side
      // up): it continues the ledge past y_in as a slab at the height of the ledge (2.54 mm under the board), over the body at
      // 5.7 to 8.4 mm from the edge, with a 45 degree wedge under it, so that it prints without supports. With the board face down
      // (the pass with J3 and J4) it clears everything: the Zero hangs 11 mm below the board and its pocket starts at y 103.2, the
      // parts on the board hang at most 1.1 mm.
      {
        top_z = base_t + post_h - j1_body_t;          // top of the ledge
        shelf_end = by0 + 8.5;  shelf_t = 2.0;  L = shelf_end - j1_y_in;
        translate([j1_x0, j1_y_in, top_z - shelf_t]) cube([j1_x1 - j1_x0, L, shelf_t]);
        translate([j1_x0, 0, 0]) rotate([90, 0, 90]) linear_extrude(j1_x1 - j1_x0)
          polygon([[j1_y_in, top_z - shelf_t - L], [shelf_end, top_z - shelf_t], [j1_y_in, top_z - shelf_t]]);
        // the long pins of the turned header run on from the body (8.4 mm from the edge) to about 15 mm: the shelf goes on as a thin
        // slab with a slot for each pin, as the comb outside the edge does; the ribs stop 1.3 mm under the board, so the parts on
        // the board (they hang at most 1.1 mm in the face-down pass) clear them. Nothing supports this part from below (the Zero
        // hangs there in the other pass), so it is a short cantilever: the thin support under its end is broken off after printing.
        pin_end = by0 + 15.0;
        translate([j1_x0, shelf_end - 0.01, 0]) difference() {
          translate([0, 0, top_z - shelf_t]) cube([j1_x1 - j1_x0, pin_end - shelf_end + 0.01, shelf_t + 1.24]);
          for (x = [111.96, 114.50, 117.04])
            translate([x - j1_x0 - slot_w / 2, -1, top_z + 0.85]) cube([slot_w, pin_end - shelf_end + 2, 5]);
        }
        // a thin support under the end of the comb, to be BROKEN OFF after printing (the Zero hangs there in the pass with J3 and J4):
        // 3 x 1.2 mm at the foot, tapering to a 1.0 x 0.4 mm tip that touches the slab
        sy = by0 + 13.5;  sx = (j1_x0 + j1_x1) / 2;  sz = top_z - shelf_t;
        hull() {
          translate([sx - 1.5, sy - 0.6, base_t - 0.01]) cube([3.0, 1.2, 0.01]);
          translate([sx - 0.5, sy - 0.2, sz - 0.01]) cube([1.0, 0.4, 0.01]);
        }
      }
      // side guides at both ends of the J1 body, so it cannot turn or slide along the edge
      for (x = [j1_x0 - guide_w, j1_x1]) translate([x, j1_y_out, 0])
        cube([guide_w, j1_y_in - j1_y_out, base_t + post_h - 0.3]);
      // comb past the board edge: one slot per pin keeps the long pins straight and square to the edge
      translate([j1_x0, j1_y_out, 0]) difference() {
        cube([j1_x1 - j1_x0, comb_l, base_t + post_h - 0.3]);
        for (x = [111.96, 114.50, 117.04])
          translate([x - j1_x0 - slot_w / 2, -1, base_t + post_h - 1.27 - 0.32 - 0.1]) cube([slot_w, comb_l + 2, 5]);
      }
    }
    // grooves in the underside, both ways (three each: the two named below and one in the middle between them), for a rubber band that holds the board down (docs/shield-pcb.md): along the long axis
    // (y) at the two strips beside the board, 2.5 mm from its long edges over the copper rings, and across it (x) at the rows of
    // the mounting holes; the bands run round the whole base and sit in the grooves, so they cannot slip off and the base lies flat
    for (x = [bx0 + 2.5, cx, bx1 - 2.5]) translate([x - groove_w / 2, cy - base_w / 2 - 1, -0.01]) cube([groove_w, base_w + 2, groove_d + 0.01]);
    for (y = [cy - 12, cy, cy + 12]) translate([cx - base_w / 2 - 1, y - groove_w / 2, -0.01]) cube([base_w + 2, groove_w, groove_d + 0.01]);
    // label on the base, so the stand is not taken for something else
    translate([cx, cy + base_w / 2 - 8, base_t - 0.6])
      linear_extrude(1) text("shield solder stand", size = 4, halign = "center", valign = "center");
  }
}

module ghosts() {
  top = base_t + post_h;
  // board (upside down: its top side faces the stand)
  %translate([bx0, by0, top]) cube([bx1 - bx0, by1 - by0, board_t]);
  // socket strips (8.5 mm) and the Zero below them
  %for (x = [106.88, 122.12]) translate([x - 1.27, 104.84 - 1.27, top - 8.5]) cube([2.54, 9 * 2.54, 8.5]);
  %translate([cx - 9, cy - 11.75, top - 8.5 - 2.5 - 1.0]) cube([18, 23.5, 1.0]);
  // J1 body and pins
  %translate([j1_x0 + 0.3, by0 + 0.05, top - j1_body_t]) cube([j1_x1 - j1_x0 - 0.6, 2.66, j1_body_t]);
  %for (x = [111.96, 114.50, 117.04]) translate([x - 0.32, 94.05, top - 1.27 - 0.32]) cube([0.64, 8, 0.64]);
}

// Coloured assembly for the how-to pictures (part="assembly"): the board with the Zero, the socket strips and J1,
// upside down, lifted by `explode` mm above its place; the foam lifted by explode / 2.
explode = 0;
foam_t  = 6;

module board_assembly() {
  top = base_t + post_h;
  color("darkgreen") difference() {
    translate([bx0, by0, top]) cube([bx1 - bx0, by1 - by0, board_t]);
    for (h = holes) translate([h[0], h[1], top - 1]) cylinder(d = 2.7, h = 5);
  }
  for (h = holes) color("gold") translate([h[0], h[1], top + board_t - 0.01])
    difference() { cylinder(d = 6, h = 0.05); cylinder(d = 2.7, h = 1, center = true); }
  // socket strips with their pins through the board
  for (x = [106.88, 122.12]) {
    color([0.1, 0.1, 0.1]) translate([x - 1.27, 104.84 - 1.27, top - 8.5]) cube([2.54, 9 * 2.54, 8.5]);
    for (i = [0 : 8]) color("silver") translate([x - 0.3, 104.84 + i * 2.54 - 0.3, top]) cube([0.6, 0.6, board_t + 1.5]);
  }
  // Zero: its pin headers in the sockets, its board below, the chip and the USB-C facing down
  zt = top - 8.5 - 2.5;
  color([0.1, 0.1, 0.1]) for (x = [106.88, 122.12]) translate([x - 1.27, 104.84 - 1.27, zt]) cube([2.54, 9 * 2.54, 2.5]);
  color("royalblue") translate([cx - 9, cy - 11.75, zt - 1.0]) cube([18, 23.5, 1.0]);
  color("silver") translate([cx - 4.5, cy - 11.75 - 0.5, zt - 1.0 - 3.2]) cube([9, 7.4, 3.2]);   // USB-C
  color([0.2, 0.2, 0.2]) translate([cx - 3.5, cy - 1, zt - 1.0 - 0.9]) cube([7, 7, 0.9]);         // chip
  // J1: body on the board, long pins over the edge, short pins through the board
  color([0.1, 0.1, 0.1]) translate([j1_x0 + 0.3, by0 + 0.05, top - j1_body_t]) cube([j1_x1 - j1_x0 - 0.6, 2.66, j1_body_t]);
  for (x = [111.96, 114.50, 117.04]) color("gold") {
    translate([x - 0.32, 94.05, top - 1.27 - 0.32]) cube([0.64, 104.15 - 94.05 + 0.32, 0.64]);
    translate([x - 0.32, 104.15 - 0.32, top - 1.27 - 0.32]) cube([0.64, 0.64, 1.27 + 0.32 + board_t + 1.5]);
  }
}

module foam() {
  color([0.95, 0.75, 0.8]) translate([cx - 9, cy - 11, base_t]) cube([18, 22, foam_t]);
}

if (part == "assembly") {
  color("orange") stand();
  translate([0, 0, explode / 2]) foam();
  translate([0, 0, explode]) board_assembly();
} else {
  stand();
  if (part == "preview") ghosts();
}
