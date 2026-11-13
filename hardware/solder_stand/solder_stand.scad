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

part = "stand";      // "stand" or "preview" (stand with the board and the Zero as ghosts)

base_t     = 2.0;    // base plate thickness
post_h     = 18.0;   // base top to the board's top side (must clear the Zero stack, foam fills the rest)
post_d     = 4.5;    // post diameter; the copper ring is 6.0 mm, J3 starts 2.6 mm from the hole centre
pin_d      = 2.3;    // locating pin in the 2.7 mm hole
pin_h      = 2.2;    // through the 1.6 mm board and a little past it
margin     = 6.0;    // base plate beyond the board outline
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

$fn = 48;

module stand() {
  difference() {
    union() {
      // base plate
      translate([bx0 - margin, j1_y_out - 2, 0])
        cube([bx1 - bx0 + 2 * margin, by1 + margin - (j1_y_out - 2), base_t]);
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
    }
    // label on the base, so the stand is not taken for something else
    translate([cx, by1 + margin / 2, base_t - 0.6])
      linear_extrude(1) text("shield", size = 3, halign = "center", valign = "center");
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

stand();
if (part == "preview") ghosts();
