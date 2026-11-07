// Sealed box for the 40 mm prototype speaker (Solectro M0069, 40 mm, 3 W, 4 Ohm), to test how much a closed box
// helps the low end (docs/speaker-measurement.md: measure again with speaker_sweep in the box).
//
// Two printed parts: the box and a screw cap. The speaker sits face out in a counterbore at the top, its rim on a
// ledge; the cap screws onto the box and presses the rim down onto a thin ring of plasticine on the ledge, so the
// box is airtight (a leaking box loses most of its bass). Where to put the plasticine:
//   1. a thin roll on the ledge under the rim, all round;
//   2. in the notch for the solder tabs, around the tabs up to the underside of the rim;
//   3. around the wires in the cable hole, inside and outside (hot glue works too: used on the first box).
// The tabs sit in the notch, so the speaker does not turn while the cap is screwed on.
// Print: PETG or PLA, 100 % infill or at least 4 walls, so the box itself does not resonate. The box stands on its
// bottom, the cap on its top face. A tuft of cotton wool or foam inside is optional (acts like a larger box).
// speaker_box.3mf is the Bambu Studio project used for the first print (2026-11-07, X1E, 0.16 mm layers, 6 walls,
// 6 top and bottom layers, 40 % gyroid; both boxes and the cap). It holds a copy of the STLs: re-import them after
// changing this file.
//
// Speaker dimensions measured with a caliper on 2026-11-07. The solder tabs stick out 0.14 mm past the rim, so the
// cavity is a little wider than the basket and has a notch for the tab strip; the rim rests on the ledge that is left.
// Export (OpenSCAD 2021.01, takes a minute or two each):
//   openscad -o speaker_box_30ml.stl speaker_box.scad
//   openscad -o speaker_box_15ml.stl -D box_volume_ml=15 speaker_box.scad
//   openscad -o speaker_box_cap.stl -D 'part="cap"' speaker_box.scad
//   openscad -o speaker_box_assembly.png -D 'part="both"' speaker_box.scad   (preview, not for printing)

part = "box";         // "box", "cap" or "both" (assembled, cut open, for a preview)

rim_d        = 39.70; // outer diameter of the speaker rim (measured)
rim_t        = 2.55;  // thickness of the rim that rests on the ledge (measured)
tabs_d       = 39.97; // widest part behind the rim, across the solder tabs and wires (measured)
speaker_h    = 20.65; // total depth, front of the rim to the back of the magnet (measured)
magnet_d     = 34.45; // magnet diameter (measured)
basket_d     = 35.5;  // basket without the tabs (measured)
tab_w        = 23.26; // width of the solder tab strip with the wires, along the rim (measured)

box_volume_ml = 30;   // air volume behind the speaker (try 15 and 30 and compare)
bottom        = 3.0;
fit           = 0.4;  // clearance around the rim and the tabs
rim_proud     = 0.3;  // the rim stands this much above the box, so the cap presses the rim and not the box
cable_hole_d  = 3.0;  // TODO: too small for the speaker cable with its connector on; size it (or make a slot) so
                      // the connector passes, then seal around the wires. Connector size not measured yet.
cable_hole_drop = 10.5; // cable hole centre below the start of the thread (was 3 mm: the wires came out right at
                      // the edge of the cap; moved 7.5 mm lower on 2026-11-07)

// thread: a rounded single-start thread made by twisting an off-centre circle; prints without supports
thread_len    = 8.0;  // length of the thread on the box
pitch         = 2.5;
thread_depth  = 1.2;
thread_gap    = 0.35; // radial clearance between the box thread and the cap thread
thread_r      = 23.4; // outer radius of the box thread
cap_top       = 2.0;  // thickness of the cap's top plate
cap_wall      = 2.0;
cap_opening_d = 37.0; // the cap covers (rim_d - cap_opening_d) / 2 = 1.35 mm of the rim

$fn = 96;

speaker_vol = PI * pow(magnet_d / 2, 2) * speaker_h * 0.6 + PI * pow(basket_d / 2, 2) * speaker_h * 0.4;
inner_d = basket_d + 0.6;
inner_h = max(speaker_h - rim_t + 3, (box_volume_ml * 1000 + speaker_vol) / (PI * pow(inner_d / 2, 2)));
outer_d = 2 * (thread_r - thread_depth);         // plain part of the box below the thread
seat_d  = rim_d + fit;
cb_h    = rim_t - rim_proud;                     // counterbore depth
total_h = bottom + inner_h + cb_h;
cap_d   = 2 * (thread_r + thread_gap + cap_wall);
cap_h   = cap_top + thread_len;

echo(str("box: inner height ", inner_h, " mm, outside ", 2 * thread_r, " x ", total_h, " mm, air about ",
         box_volume_ml, " ml, ledge ", (rim_d - inner_d) / 2, " mm; cap ", cap_d, " x ", cap_h, " mm"));

// Thread solid of radius r (outer) over length h; the crests follow a helix, right-handed.
module thread(r, h) {
  e = thread_depth / 2;
  linear_extrude(height = h, twist = -360 * h / pitch, slices = ceil(h / pitch * 36), convexity = 4)
    translate([e, 0]) circle(r = r - e, $fn = 64);
}

module box() {
  difference() {
    union() {
      cylinder(d = outer_d, h = total_h - thread_len);
      translate([0, 0, total_h - thread_len]) intersection() {
        thread(thread_r, thread_len);
        cylinder(r1 = thread_r, r2 = thread_r - 0.6, h = thread_len);   // chamfer at the top for an easy start
      }
      translate([0, 0, total_h - thread_len]) cylinder(r = thread_r - thread_depth, h = thread_len);
    }
    translate([0, 0, bottom]) cylinder(d = inner_d, h = inner_h + 1);                 // cavity
    translate([0, 0, total_h - cb_h - speaker_h - 1]) intersection() {               // notch for the solder tabs
      cylinder(d = tabs_d + 2 * fit, h = speaker_h + 2);
      translate([0, -tab_w / 2 - fit, 0]) cube([tabs_d, tab_w + 2 * fit, speaker_h + 2]);
    }
    translate([0, 0, total_h - cb_h]) cylinder(d = seat_d, h = cb_h + 1);            // counterbore for the rim
    translate([0, 0, total_h - thread_len - cable_hole_drop]) rotate([0, 90, 0])      // cable hole below the thread
      cylinder(d = cable_hole_d, h = outer_d);
  }
}

// The cap as printed: top plate on the bed (z = 0), thread upwards.
module cap() {
  difference() {
    cylinder(d = cap_d, h = cap_h);
    translate([0, 0, -1]) cylinder(d = cap_opening_d, h = cap_top + 2);
    translate([0, 0, cap_top]) thread(thread_r + thread_gap, thread_len + 1);
    translate([0, 0, cap_h - 0.6]) cylinder(r1 = thread_r - thread_depth + thread_gap, r2 = thread_r + thread_gap + 0.6, h = 0.61);
  }
}

if (part == "box") box();
else if (part == "cap") cap();
else difference() {
  union() {
    box();
    color("teal") translate([0, 0, total_h + rim_proud + cap_top]) rotate([180, 0, 0]) cap();
  }
  translate([0, -100, -1]) cube([100, 200, 200]);   // cut open to show the inside
}
