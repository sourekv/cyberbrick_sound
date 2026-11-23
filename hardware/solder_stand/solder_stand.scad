// Soldering stand for the shield PCB (hardware/shield/): holds the board upside down while the hand-fitted parts
// are soldered (J3/J4 female socket strips 1x9, J1 right-angle servo header 1x3).
//
// How it is used (J1 lies between the board and the stand in the first pass, in one of two variants: the pins out (J1 on the Zero side) or the pins in (J1 on the opposite side)):
//   Variant a), the pins out: ONE pass (tried 2026-11-23). The loose insert (part "j1_insert") sits in socket A, outside the board edge, and
//      stays there; it does not obstruct fitting the Zero. J1 lies on the insert (body on the ledge, the long pins in the slots, pointing
//      out), both 1x9 socket strips are plugged onto the Zero, a piece of soft foam (about 5-8 mm thick) goes into the pocket, and the board
//      with the Zero is put on the four posts: the locating pins go into the mounting holes, the pins of J1 through its holes, the Zero
//      sinks into the pocket and the foam presses it (and so the sockets) up against the board. J1, J3, J4 and the Zero are all on the
//      same side of the board, facing the stand; everything is soldered from the visible side. A rubber band lengthwise round the whole
//      stand (it sits in the grooves in the underside of the base) holds the board while the strips (J3, J4) are soldered, then it is moved
//      across the board and the pins of J1 are soldered.
//   Variant b), the pins in: TWO passes. First pass, J1: put the insert, turned by 180 degrees, into socket B, hold the pins of J1 in
//      place by hand, put the board on the four posts top side up (no foam), solder J1 from the top side and take the insert out.
//      Second pass, J3/J4: as variant a), without the insert.
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
//   solder_stand_variants.png: -D 'part="use_a"' and 'part="use_b"' (the stand with the insert and J1, without the board), camera
//   114.5,106,22,55,0,160,170, joined with montage and labels
//   solder_stand_steps.png: six renders (-D 'part="assembly"' -D pass_no=1 or 2 -D explode=40 / 15 / 0, Tomorrow colour scheme, camera
//   114.5,108,38,60,0,200,250; variant a): pass_no=3 and -D band=true / 'band="across"', four pictures; variant b): the top row the first pass, the bottom row the second), joined with ImageMagick montage; the last picture with -D band=true (the rubber bands), black frames and captions under the pictures; the same with -D xray=true goes to xray/ (title "X-ray" in quotes); solder_stand_steps_b.png is the same with -D variant=\"b\" (variant a is the default)

part = "stand";      // "stand", "j1_insert" (the loose insert for J1) or "preview" (stand with the board and the Zero as ghosts)

// The loose insert for J1 (part = "j1_insert", printed on its own, lying on its back): one piece that carries the body of J1 on a
// ledge, has guides at both ends of the body and a comb with a slot for each long pin. It is plugged into one of two sockets in the
// base, which are mirror images about the row of J1's holes (y 104.15): in socket A (outside the board edge) it serves J1 with the
// pins out (variant a), in socket B (the insert turned by 180 degrees) J1 turned by 180 degrees, pins in (variant b; docs/shield-pcb.md).
// In variant a) J1 is on the Zero side, in variant b) on the opposite side. In variant a) the insert stays in socket A and everything is soldered in one pass; in variant b) it is used in the
// first pass only and taken out of socket B before the pass with J3 and J4.
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
variant = "a";   // "a": J1 pins out (insert in socket A), "b": pins in (insert and J1 turned by 180 degrees, socket B); for the assembly pictures
xray = false;   // semi-transparent stand, board and foam, so that hidden parts show (pictures in xray/); J1, the insert and the Zero stay opaque
band = false;   // draw the rubber bands (second pass, explode = 0)
pass_no = 2;   // 3: variant a), ONE pass: J1 on the insert, the Zero with the strips and the foam, all together (as photographed 2026-11-23)
// (pass_no 1 and 2 are the two passes of variant b)   // 1: first pass (J1, board top side up, the loose insert, no foam), 2: second pass (J3/J4 with the Zero and the foam; the insert only in variant a)
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
  color("darkgreen", xray ? 0.35 : 1) difference() {
    translate([bx0, by0, top]) cube([bx1 - bx0, by1 - by0, board_t]);
    for (h = holes) translate([h[0], h[1], top - 1]) cylinder(d = 2.7, h = 5);
  }
  for (h = holes) color("gold") translate([h[0], h[1], top + board_t - 0.01])
    difference() { cylinder(d = 6, h = 0.05); cylinder(d = 2.7, h = 1, center = true); }
  if (pass_no >= 2) {
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
  // J1 (variant b: on the underside of the board): in the first pass it lies on the insert (drawn separately), in the second it is on the far side
  turn_b = variant == "b" ? 180 : 0;
  translate([cx, row_y, 0]) rotate([0, 0, turn_b]) translate([-cx, -row_y, 0]) {
    if (pass_no == 2) translate([0, 0, 2 * top + board_t]) mirror([0, 0, 1]) j1_on_board(top);
  }
}

module foam() {
  color([0.95, 0.75, 0.8], xray ? 0.35 : 1) translate([cx - 9, cy - 11, base_t]) cube([18, 22, foam_t]);
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

// rubber bands round the stand (second pass): one loop along the long axis, in the middle groove. Under tension a band does not run straight up and down
// but straight from the edge of the board to the edge of the base (over the top), then down the side and back through the groove
module band_seg(a, b) {   // a, b = [x, y, z]; a strip 1.5 mm wide (x) and 0.8 mm thick
  hull() for (q = [a, b]) translate([q[0] - 0.75, q[1] - 0.4, q[2] - 0.4]) cube([1.5, 0.8, 0.8]);
}
// over the board the band runs between the first and the second pin of J1 (x = 113.23) and over the top of its collar (the body, 2.54 mm
// tall, y 100 to 102.7), then straight (it does not follow the board) to the far edge of the board and slanted to the middle (x = cx); under the base it sits in the middle groove
module bands() {
  zt = base_t + post_h + board_t + 0.4;
  zc = zt + j1_body_t;
  ya = cy - base_w / 2;  yb = cy + base_w / 2;  xb = 113.23;
  // variant b): J1 is turned by 180 degrees, its collar is on the inner side of the row of holes (y 105.6 to 108.3): the band first
  // touches the near edge of the board, then rises onto the collar
  path = variant == "b"
    ? [[cx, ya, 0.4], [cx, ya, base_t], [cx, by0, zt], [xb, 2 * row_y - 102.7, zc], [xb, 2 * row_y - by0 - 0.05, zc], [cx, by1, zt], [cx, yb, base_t], [cx, yb, 0.4], [cx, ya, 0.4]]
    : [[cx, ya, 0.4], [cx, ya, base_t], [xb, by0 + 0.05, zc], [xb, 102.7, zc], [cx, by1, zt], [cx, yb, base_t], [cx, yb, 0.4], [cx, ya, 0.4]];
  color("red") for (k = [0 : len(path) - 2]) band_seg(path[k], path[k + 1]);
}

// variant a), one pass, the band for soldering the strips: lengthwise, from the edge of the base over the near edge of the board (the J1
// side, above the comb of the insert, between the pins of J1) to the far edge of the board and down; the pads of the strips stay free
module bands_along() {
  zt = base_t + post_h + board_t + 0.4;
  ya = cy - base_w / 2;  yb = cy + base_w / 2;  xb = 113.23;
  path = [[cx, ya, 0.4], [cx, ya, base_t], [xb, by0, zt], [cx, by1, zt], [cx, yb, base_t], [cx, yb, 0.4], [cx, ya, 0.4]];
  color("red") for (k = [0 : len(path) - 2]) band_seg(path[k], path[k + 1]);
}
// the same band moved across the board (for soldering J1): in the groove across the base at y = cy, over the middle of the board
module bands_across() {
  zt = base_t + post_h + board_t + 0.4;
  xa = cx - base_w / 2;  xb = cx + base_w / 2;
  path = [[xa, cy, 0.4], [xa, cy, base_t], [bx0, cy, zt], [bx1, cy, zt], [xb, cy, base_t], [xb, cy, 0.4], [xa, cy, 0.4]];
  color("red") for (k = [0 : len(path) - 2])
    hull() for (q = [path[k], path[k + 1]]) translate([q[0] - 0.4, q[1] - 0.75, q[2] - 0.4]) cube([0.8, 1.5, 0.8]);
}

// the two ways of use, without the board: a = the pins out (insert in socket A), b = the pins in (insert and J1 turned by 180 degrees, socket B)
if (part == "use_a" || part == "use_b") {
  color("orange") stand();
  turn = part == "use_b" ? 180 : 0;
  translate([cx, row_y, 0]) rotate([0, 0, turn]) translate([-cx, -row_y, 0]) { color("orange") j1_insert(); j1_header(); }
} else if (part == "assembly") {
  color("orange", xray ? 0.2 : 1) stand();
  if (pass_no == 1 || variant == "a") translate([cx, row_y, 0]) rotate([0, 0, variant == "b" ? 180 : 0]) translate([-cx, -row_y, 0]) color("orange") j1_insert();
  // first pass: J1 lies on the insert (the board comes over its short pins and ends up above it)
  if (pass_no == 1 || pass_no == 3) translate([cx, row_y, 0]) rotate([0, 0, variant == "b" ? 180 : 0]) translate([-cx, -row_y, 0]) j1_header();
  if (pass_no >= 2) translate([0, 0, explode / 2]) foam();
  translate([0, 0, explode]) board_assembly();
  if (band == "across") bands_across();
  else if (pass_no == 3 && band == true) bands_along();
  else if (band) bands();
} else if (part == "j1_insert") {
  j1_insert();
} else {
  stand();
  if (part == "preview") { ghosts(); j1_insert(); }
}
