# Fusion 360 script: the sealed speaker box with a screw cap, the same design as ../../speaker_box.scad, built as a
# parametric Fusion design (timeline, user parameters, a real modelled ISO metric thread).
#
# Run: Fusion 360 -> Utilities -> Scripts and Add-Ins (Shift+S) -> "+" next to My Scripts -> pick this folder
# (SpeakerBox) -> select SpeakerBox -> Run. It opens a new design with two components, Box and Cap, and saves
# box.stl and cap.stl next to this file.
# Afterwards: Modify -> Change Parameters shows the speaker dimensions as user parameters; change one and the model
# updates. The air volume (VOLUME_ML below) is turned into inner_h when the script runs; to change it, edit
# inner_h or run the script again.
#
# Written 2026-11-07 and run in Fusion 360 the same day: the box had no wall under the thread, because the cap's
# thread hole (cut with the cap in place on the box) also cut the box. Fixed by limiting every cut to its own part;
# re-run the same day, and the cross-sections of box.stl and cap.stl are solid.
# Not printed yet. A printed thread from the ISO table has almost no
# play; if the cap is too tight, scale the cap 101 % in X and Y in the slicer (or use the slicer's hole compensation).

import math
import os
import traceback

import adsk.core
import adsk.fusion

VOLUME_ML = 30          # air volume behind the speaker

# Speaker (Solectro M0069, measured with a caliper on 2026-11-07) and box, all in mm.
PARAMS = [
    ('rim_d', 39.70, 'outer diameter of the speaker rim'),
    ('rim_t', 2.55, 'rim thickness'),
    ('tabs_d', 39.97, 'across the solder tabs and wires'),
    ('speaker_h', 20.65, 'front of the rim to the back of the magnet'),
    ('magnet_d', 34.45, 'magnet diameter'),
    ('basket_d', 35.5, 'basket without the tabs'),
    ('tab_w', 23.26, 'width of the solder tab strip'),
    ('fit', 0.4, 'clearance around the rim'),
    ('notch_side', 1.0, 'clearance on each side of the solder tab strip (was 0.4: too tight)'),
    ('notch_radial', 0.8, 'clearance beyond the solder tabs towards the wall (was 0.4: too tight)'),
    ('bottom', 3.0, 'bottom thickness'),
    ('rim_proud', 0.3, 'the rim stands this much above the box, so the cap presses the rim'),
    ('thread_d', 48.0, 'nominal thread diameter (ISO metric M48)'),
    ('thread_len', 8.0, 'thread length'),
    ('cap_top', 2.0, 'thickness of the cap top plate'),
    ('cap_wall', 2.5, 'cap wall outside the thread'),
    ('cap_opening_d', 37.0, 'opening in the cap for the membrane'),
    ('cable_hole_d', 5.0, 'cable hole: set it for your cable and connector before printing (connector about 4.87 mm)'),
    ('cable_hole_drop', 10.5, 'cable hole centre below the start of the thread'),
    ('chamfer', 0.6, '45 deg chamfer on the edges that lie on the bed: box bottom, cap top'),
]
THREAD_TYPE = 'ISO Metric profile'
THREAD_PITCH = 2.0


def V(expr):
    return adsk.core.ValueInput.createByString(expr)


def P3(x, y, z=0.0):
    return adsk.core.Point3D.create(x, y, z)


def mm(v):              # mm -> Fusion internal cm
    return v / 10.0


class Builder:
    def __init__(self, comp):
        self.comp = comp

    def plane(self, expr):
        if expr == '0 mm':
            return self.comp.xYConstructionPlane
        pi = self.comp.constructionPlanes.createInput()
        pi.setByOffset(self.comp.xYConstructionPlane, V(expr))
        return self.comp.constructionPlanes.add(pi)

    def circle(self, plane, d_expr, d_mm):
        sk = self.comp.sketches.add(plane)
        c = sk.sketchCurves.sketchCircles.addByCenterRadius(P3(0, 0), mm(d_mm / 2))
        sk.geometricConstraints.addCoincident(c.centerSketchPoint, sk.originPoint)
        dim = sk.sketchDimensions.addDiameterDimension(c, P3(mm(d_mm / 2 + 5), mm(5)))
        dim.parameter.expression = d_expr
        return sk

    def extrude(self, sk, dist_expr, op, profile=None):
        prof = profile or sk.profiles.item(0)
        ei = self.comp.features.extrudeFeatures.createInput(prof, op)
        ei.setDistanceExtent(False, V(dist_expr))
        self.own_bodies(ei, op)
        return self.comp.features.extrudeFeatures.add(ei)

    def own_bodies(self, ei, op):
        # A cut in Fusion hits every body it passes through, also in other components: the cap's thread hole, cut
        # with the cap on the box, removed the box wall under the thread. Limit cuts to this component's bodies.
        if op == adsk.fusion.FeatureOperations.CutFeatureOperation and self.comp.bRepBodies.count:
            ei.participantBodies = [self.comp.bRepBodies.item(i) for i in range(self.comp.bRepBodies.count)]

    def cylinder_face(self, r_mm):
        for body in self.comp.bRepBodies:
            for f in body.faces:
                g = f.geometry
                if g.surfaceType == adsk.core.SurfaceTypes.CylinderSurfaceType and abs(g.radius - mm(r_mm)) < 1e-4:
                    return f
        raise RuntimeError('no cylindrical face with radius %.3f mm' % r_mm)

    def chamfer_circle(self, r_mm, z_mm, dist_expr):
        # 45 deg chamfer on the circular outer edge with radius r_mm at height z_mm (model space)
        for body in self.comp.bRepBodies:
            for e in body.edges:
                g = e.geometry
                if (g.curveType == adsk.core.Curve3DTypes.Circle3DCurveType and abs(g.radius - mm(r_mm)) < 1e-4
                        and abs(g.center.z - mm(z_mm)) < 1e-4):
                    edges = adsk.core.ObjectCollection.create()
                    edges.add(e)
                    cf = self.comp.features.chamferFeatures
                    ci = cf.createInput2()
                    ci.chamferEdgeSets.addEqualDistanceChamferEdgeSet(edges, V(dist_expr), False)
                    return cf.add(ci)
        raise RuntimeError('no circular edge with radius %.3f mm at z %.3f mm' % (r_mm, z_mm))

    def merge(self):
        # One solid per part: join any extra bodies. The first run exported only body 1, and at the thread the box STL
        # held the thread ridge alone, without the wall under it. Returns the body count before merging.
        bodies = self.comp.bRepBodies
        n = bodies.count
        if n > 1:
            tools = adsk.core.ObjectCollection.create()
            for i in range(1, n):
                tools.add(bodies.item(i))
            ci = self.comp.features.combineFeatures.createInput(bodies.item(0), tools)
            ci.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            self.comp.features.combineFeatures.add(ci)
        return n

    def thread(self, face, internal):
        tf = self.comp.features.threadFeatures
        q = tf.threadDataQuery
        sizes = list(q.allSizes(THREAD_TYPE))
        size = min(sizes, key=lambda s: abs(float(s) - THREAD_D))
        desigs = list(q.allDesignations(THREAD_TYPE, size))
        desig = next((d for d in desigs if d.endswith('x%g' % THREAD_PITCH)), desigs[0])
        classes = list(q.allClasses(internal, THREAD_TYPE, desig))
        cls = next((c for c in classes if c in ('6H', '6g')), classes[0])
        info = tf.createThreadInfo(internal, THREAD_TYPE, desig, cls)
        ti = tf.createInput(face, info)
        ti.isFullLength = True
        ti.isModeled = True
        tf.add(ti)
        return desig, cls


THREAD_D = 48.0


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
        design = adsk.fusion.Design.cast(app.activeProduct)
        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent
        p = {name: val for name, val, _ in PARAMS}

        # Air volume -> cavity height (the speaker takes part of the cavity; rough estimate, as in the .scad).
        inner_d = p['basket_d'] + 0.6
        speaker_vol = (math.pi * (p['magnet_d'] / 2) ** 2 * p['speaker_h'] * 0.6
                       + math.pi * (p['basket_d'] / 2) ** 2 * p['speaker_h'] * 0.4)
        inner_h = max(p['speaker_h'] - p['rim_t'] + 3,
                      (VOLUME_ML * 1000 + speaker_vol) / (math.pi * (inner_d / 2) ** 2))

        up = design.userParameters
        for name, val, comment in PARAMS:
            up.add(name, V('%g mm' % val), 'mm', comment)
        up.add('inner_h', V('%.3f mm' % inner_h), 'mm', 'cavity height for %d ml of air' % VOLUME_ML)
        up.add('inner_d', V('basket_d + 0.6 mm'), 'mm', 'cavity diameter')
        up.add('cb_h', V('rim_t - rim_proud'), 'mm', 'counterbore depth for the rim')
        up.add('total_h', V('bottom + inner_h + cb_h'), 'mm', 'box height')
        up.add('thread_minor', V('thread_d - 1.0825 * %g mm' % THREAD_PITCH), 'mm', 'minor diameter of the thread')
        up.add('cap_d', V('thread_d + 2 * cap_wall'), 'mm', 'cap outer diameter')
        up.add('cap_z', V('total_h + rim_proud - thread_len'), 'mm', 'cap bottom, assembled')

        total_h = p['bottom'] + inner_h + p['rim_t'] - p['rim_proud']
        cb_h = p['rim_t'] - p['rim_proud']
        new = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
        join = adsk.fusion.FeatureOperations.JoinFeatureOperation
        cut = adsk.fusion.FeatureOperations.CutFeatureOperation

        # ---- Box ----
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        box = occ.component
        box.name = 'Box'
        b = Builder(box)
        b.extrude(b.circle(b.plane('0 mm'), 'thread_d - 1 mm', THREAD_D - 1), 'total_h - thread_len', new)
        b.extrude(b.circle(b.plane('total_h - thread_len'), 'thread_d', THREAD_D), 'thread_len', join)
        b.extrude(b.circle(b.plane('bottom'), 'inner_d', inner_d), 'inner_h + 1 mm', cut)
        b.extrude(b.circle(b.plane('total_h - cb_h'), 'rim_d + fit', p['rim_d'] + p['fit']), 'cb_h + 1 mm', cut)

        # notch for the solder tabs: the part of a circle (tabs_d + 2 notch_radial) between
        # y = +-(tab_w / 2 + notch_side), x > 0
        sk = box.sketches.add(b.plane('total_h - cb_h - speaker_h - 1 mm'))
        r = mm((p['tabs_d'] + 2 * p['notch_radial']) / 2)
        w = mm(p['tab_w'] / 2 + p['notch_side'])
        xc = math.sqrt(r * r - w * w)
        lines = sk.sketchCurves.sketchLines
        lines.addByTwoPoints(P3(0, -w), P3(xc, -w))
        sk.sketchCurves.sketchArcs.addByThreePoints(P3(xc, -w), P3(r, 0), P3(xc, w))
        lines.addByTwoPoints(P3(xc, w), P3(0, w))
        lines.addByTwoPoints(P3(0, w), P3(0, -w))
        b.extrude(sk, 'speaker_h + 1 mm', cut)

        # cable hole through the wall at the notch, below the thread
        sk = box.sketches.add(box.yZConstructionPlane)
        z = mm(total_h - p['thread_len'] - p['cable_hole_drop'])
        hole_c = sk.modelToSketchSpace(P3(0, 0, z))
        sk.sketchCurves.sketchCircles.addByCenterRadius(hole_c, mm(p['cable_hole_d'] / 2))
        for direction in (adsk.fusion.ExtentDirections.PositiveExtentDirection,
                          adsk.fusion.ExtentDirections.NegativeExtentDirection):
            ei = box.features.extrudeFeatures.createInput(sk.profiles.item(0), cut)
            ei.setOneSideExtent(adsk.fusion.DistanceExtentDefinition.create(V('30 mm')), direction)
            b.own_bodies(ei, cut)
            feat = box.features.extrudeFeatures.add(ei)
            inside = box.bRepBodies.item(0).pointContainment(P3(mm(THREAD_D / 2 - 1), 0, z))
            if inside == adsk.fusion.PointContainment.PointOutsidePointContainment:
                break                                   # the hole goes out on the notch side (+x)
            feat.deleteMe()                             # wrong side: try the other direction

        box_thread = b.thread(b.cylinder_face(THREAD_D / 2), False)
        box_bodies = b.merge()
        b.chamfer_circle((THREAD_D - 1) / 2, 0.0, 'chamfer')            # bottom edge, on the bed

        # ---- Cap (assembled on the box; print it upside down, top plate on the bed) ----
        occ = root.occurrences.addNewComponent(adsk.core.Matrix3D.create())
        cap = occ.component
        cap.name = 'Cap'
        c = Builder(cap)
        cap_d = THREAD_D + 2 * p['cap_wall']
        c.extrude(c.circle(c.plane('cap_z'), 'cap_d', cap_d), 'thread_len + cap_top', new)
        minor = THREAD_D - 1.0825 * THREAD_PITCH
        c.extrude(c.circle(c.plane('cap_z'), 'thread_minor', minor), 'thread_len', cut)
        c.extrude(c.circle(c.plane('cap_z'), 'cap_opening_d', p['cap_opening_d']), 'thread_len + cap_top', cut)
        cap_thread = c.thread(c.cylinder_face(minor / 2), True)
        cap_bodies = c.merge()
        cap_top_z = total_h + p['rim_proud'] + p['cap_top']           # cap_z + thread_len + cap_top
        c.chamfer_circle(cap_d / 2, cap_top_z, 'chamfer')               # top edge, on the bed when printed

        # ---- STL export next to this script ----
        here = os.path.dirname(os.path.realpath(__file__))
        em = design.exportManager
        for comp, fname in ((box, 'box.stl'), (cap, 'cap.stl')):
            opts = em.createSTLExportOptions(comp, os.path.join(here, fname))   # all bodies of the part
            opts.meshRefinement = adsk.fusion.MeshRefinementSettings.MeshRefinementHigh
            em.execute(opts)

        app.activeViewport.fit()
        ui.messageBox('Speaker box done.\nBox thread: %s %s\nCap thread: %s %s\nAir volume %d ml, box height %.1f mm.\n'
                      'Bodies before merging: box %d, cap %d.\n'
                      'STL files saved to:\n%s\n'
                      '(cap.stl is in the assembled position: flip it in the slicer, top plate on the bed)'
                      % (box_thread + cap_thread + (VOLUME_ML, total_h, box_bodies, cap_bodies, here)))
    except Exception:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
