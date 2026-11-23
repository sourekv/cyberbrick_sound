// Soldering stand for the shield PCB (hardware/shield/): holds the board upside down while the hand-fitted parts
// are soldered (J3/J4 female socket strips 1x9, J1 right-angle servo header 1x3).
//
// How it is used (J1 is always on the underside of the board, in one of two variants: the pins out or the pins in):
//   First pass, J1: the board lies top side up on the four posts, no foam. Put the loose insert (part "j1_insert") into
//      socket A (the pins of J1 point out of the board: variant a) or, turned by 180 degrees, into socket B (the pins point
//      into the board: variant b). Hold the pins of J1 in place by hand, put the board on, solder J1 from the top side,
//      take the insert out.
//   Second pass, J3/J4: plug both 1x9 socket strips onto the pins of the ESP32-S3-Zero-N8R8-M (the Zero keeps them parallel
//      and at the right spacing, 15.24 mm), put a piece of soft foam (about 5-8 mm thick) into the pocket, push the strips
//      with the Zero into the board from the top side and lay the board upside down on the stand: the four pins go into the
//      mounting holes, the Zero sinks into the pocket and the foam presses it (and so the sockets) up against the board.
//      The insert is not used in this pass. Secure the board with a rubber band round the whole stand (it sits in the
//      grooves in the underside of the base), solder one pin at each end of every strip, check that everything sits flat,
//      then solder the rest.
// The board rests on the four posts by the copper rings around the mounting holes; nothing else on the top side
// touches the stand (the parts under the Zero and C1/J2/LED1 beside it are all in the open pocket).
//
// All positions come from hardware/shield/shield.kicad_pcb (board 29 x 30 mm, outline 100..129 / 100..130 in the
// KiCad coordinates, used here directly; holes at +-11.5 / +-12.0 mm from the centre). The stand is symmetric about
// the board's long axis (J1 is centred on it), so it does not matter that the board lies mirrored.
// The Zero's stack height (socket 8.5 mm + its header + its own parts) was not measured; the foam takes up the
// difference, so only post_h has to be larger than the stack (about 14-15 mm).
//
// Print: PLA or PETG, flat on the base, 0.2 mm layers are fine. Slicer setting (Bambu Studio, Advanced): Bridge direction 45 degrees
// (not automatic), because of the rubber band grooves in the underside: the first layer bridges over grooves that run both
// ways, and 45 degrees crosses both.
// Export (OpenSCAD 2021.01):
//   openscad -o solder_stand.stl solder_stand.scad
//   openscad -o solder_stand_preview.png -D 'part="preview"' solder_stand.scad   (with the board, not for printing)
//   solder_stand_variants.png: -D 'part="use_a"' and 'part="use_b"' (the stand with the insert and J1, without the board), camera
//   114.5,106,22,55,0,160,170, joined with montage and labels
//   solder_stand_steps.png: six renders (-D 'part="assembly"' -D pass_no=1 or 2 -D explode=40 / 15 / 0, Tomorrow colour scheme, camera
//   114.5,108,38,60,0,200,250; the top row the first pass, the bottom row the second), joined with ImageMagick montage

part = "stand";      // "stand", "j1_insert" (the loose insert for J1) or "preview" (stand with the board and the Zero as ghosts)

// The loose insert for J1 (part = "j1_insert", printed on its own, lying on its back): one piece that carries the body of J1 on a
// ledge, has guides at both ends of the body and a comb with a slot for each long pin. It is plugged into one of two sockets in the
// base, which are mirror images about the row of J1's holes (y 104.15): in socket A (outside the board edge) it serves J1 with the
// pins out (variant a), in socket B (the insert turned by 180 degrees) J1 turned by 180 degrees, pins in (variant b; docs/shield-pcb.md).
// J1 is always on the underside. The insert is used in the first pass only (the board top side up, without foam) and taken out
// before the pass with J3 and J4, because the Zero hangs in its place.
row_y  = 104.15;                            // the row of J1's holes (KiCad coordinates)
ins_u0 = row_y - 102.71;                    // the insert starts at the far edge of the body (distance from the row)
ins_uc = row_y - 98.5;                      // the comb starts here, 1.5 mm past the board edge (as before)
ins_ue = row_y - 92.5;                      // the back of the insert, flush with the peg
peg_t = 3.0;  peg_l = 3.0;                  // the peg is as wide as the insert and flush with its back
peg_gap = 0.1;                              // clearance of the socket around the peg, on each side

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
guide_w   = 1.6;     // side guides beside the body
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
    }
    // grooves in the underside, both ways (three each: the two named below and one in the middle between them), for a rubber band that holds the board down (docs/shield-pcb.md): along the long axis
    // (y) at the two strips beside the board, 2.5 mm from its long edges over the copper rings, and across it (x) at the rows of
    // the mounting holes; the bands run round the whole base and sit in the grooves, so they cannot slip off and the base lies flat
    for (x = [bx0 + 2.5, cx, bx1 - 2.5]) translate([x - groove_w / 2, cy - base_w / 2 - 1, -0.01]) cube([groove_w, base_w + 2, groove_d + 0.01]);
    for (y = [cy - 12, cy, cy + 12]) translate([cx - base_w / 2 - 1, y - groove_w / 2, -0.01]) cube([base_w + 2, groove_w, groove_d + 0.01]);
    // two sockets for the loose insert of J1 (part = "j1_insert"): A outside the board edge (J1 with the pins out), B on the
    // inner side (J1 turned by 180 degrees, pins in); the same insert, turned by 180 degrees about J1's row of holes
    for (y = [row_y - ins_ue, row_y + ins_ue - peg_t])
      translate([j1_x0 - guide_w - peg_gap, y - peg_gap, base_t - peg_l]) cube([j1_x1 - j1_x0 + 2 * guide_w + 2 * peg_gap, peg_t + 2 * peg_gap, peg_l + 0.01]);
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
pass_no = 2;   // 1: first pass (J1, board top side up, the loose insert, no foam), 2: second pass (J3/J4 with the Zero and the foam, no insert)
foam_t  = 6;

module j1_on_board(top) {
  // J1: body on the board, long pins over the edge, short pins through the board
  color([0.1, 0.1, 0.1]) translate([j1_x0 + 0.3, by0 + 0.05, top - j1_body_t]) cube([j1_x1 - j1_x0 - 0.6, 2.66, j1_body_t]);
  for (x = [111.96, 114.50, 117.04]) color("gold") {
    translate([x - 0.32, 94.05, top - 1.27 - 0.32]) cube([0.64, 104.15 - 94.05 + 0.32, 0.64]);
    translate([x - 0.32, 104.15 - 0.32, top - 1.27 - 0.32]) cube([0.64, 0.64, 1.27 + 0.32 + board_t + 1.5]);
  }
}

module board_assembly() {
  top = base_t + post_h;
  color("darkgreen") difference() {
    translate([bx0, by0, top]) cube([bx1 - bx0, by1 - by0, board_t]);
    for (h = holes) translate([h[0], h[1], top - 1]) cylinder(d = 2.7, h = 5);
  }
  for (h = holes) color("gold") translate([h[0], h[1], top + board_t - 0.01])
    difference() { cylinder(d = 6, h = 0.05); cylinder(d = 2.7, h = 1, center = true); }
  if (pass_no == 2) {
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
  }
  // J1 (always on the underside of the board): in the first pass it hangs on the stand side, in the second it is on the far side
  if (pass_no == 1) j1_on_board(top);
  else translate([0, 0, 2 * top + board_t]) mirror([0, 0, 1]) j1_on_board(top);
}

module foam() {
  color([0.95, 0.75, 0.8]) translate([cx - 9, cy - 11, base_t]) cube([18, 22, foam_t]);
}

// the loose insert, shown in socket A (outside the board edge, y = row_y - u); for socket B turn it by 180 degrees about (cx, row_y).
// Printed lying on its back (the face at u = ins_ue with the peg), which is flat.
module j1_insert() {
  zt = base_t + post_h;
  x0 = j1_x0 - guide_w;  w = j1_x1 - j1_x0 + 2 * guide_w;
  translate([x0, row_y - ins_ue, base_t - peg_l]) cube([w, peg_t, peg_l + 0.5]);                       // the peg
  difference() {
    union() {
      translate([j1_x0, row_y - ins_uc, base_t]) cube([j1_x1 - j1_x0, ins_uc - ins_u0, zt - j1_body_t - base_t]);   // ledge under the body of J1
      translate([j1_x0, row_y - ins_ue, base_t]) cube([j1_x1 - j1_x0, ins_ue - ins_uc + 0.01, zt - 0.3 - base_t]);  // comb block
      for (x = [x0, j1_x1]) translate([x, row_y - ins_ue, base_t]) cube([guide_w, ins_ue - ins_u0, zt - 0.3 - base_t]); // guides
    }
    for (x = [111.96, 114.50, 117.04])
      translate([x - slot_w / 2, row_y - ins_ue - 1, zt - 1.27 - 0.32 - 0.1]) cube([slot_w, ins_ue - ins_uc + 2, 5]);
  }
}

// J1 as it lies in the stand in the first pass (the right-angle header with the long pins out, in the position of socket A): the body on the
// ledge, the long pins in the slots, the short pins pointing up (through the board, which is not drawn)
module j1_header() {
  top = base_t + post_h;
  color([0.1, 0.1, 0.1]) translate([j1_x0 + 0.3, by0 + 0.05, top - j1_body_t]) cube([j1_x1 - j1_x0 - 0.6, 2.66, j1_body_t]);
  for (x = [111.96, 114.50, 117.04]) color("gold") {
    translate([x - 0.32, 94.05, top - 1.27 - 0.32]) cube([0.64, 104.15 - 94.05 + 0.32, 0.64]);
    translate([x - 0.32, 104.15 - 0.32, top - 1.27 - 0.32]) cube([0.64, 0.64, 1.27 + 0.32 + board_t + 1.5]);
  }
}

// the two ways of use, without the board: a = the pins out (insert in socket A), b = the pins in (insert and J1 turned by 180 degrees, socket B)
if (part == "use_a" || part == "use_b") {
  color("orange") stand();
  turn = part == "use_b" ? 180 : 0;
  translate([cx, row_y, 0]) rotate([0, 0, turn]) translate([-cx, -row_y, 0]) { color("orange") j1_insert(); j1_header(); }
} else if (part == "assembly") {
  color("orange") stand();
  if (pass_no == 1) color("orange") j1_insert();
  if (pass_no == 2) translate([0, 0, explode / 2]) foam();
  translate([0, 0, explode]) board_assembly();
} else if (part == "j1_insert") {
  j1_insert();
} else {
  stand();
  if (part == "preview") { ghosts(); j1_insert(); }
}
