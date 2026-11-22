"""Build hardware/solder_stand/solder_stand.3mf from the two STL files of the solder stand.

The stand lies on its base, the loose insert (part "j1_insert") lies on its back (the flat face with the peg).
Plain 3MF: geometry and placement only; the print profile (Bridge direction 45 degrees, docs/shield-pcb.md) is set in the slicer.
Run from the repository root after exporting both STL files with OpenSCAD (see hardware/solder_stand/solder_stand.scad).
"""
import re, sys, zipfile

D = "hardware/solder_stand/"

def load(path):
    t = open(path).read()
    pts = [tuple(float(a) for a in m) for m in re.findall(r"vertex\s+(\S+)\s+(\S+)\s+(\S+)", t)]
    return [pts[i:i + 3] for i in range(0, len(pts), 3)]

def place(tris, fn):
    out = [[fn(p) for p in tri] for tri in tris]
    mn = [min(p[i] for tri in out for p in tri) for i in range(3)]
    return out, mn

def shift(tris, d):
    return [[(p[0] + d[0], p[1] + d[1], p[2] + d[2]) for p in tri] for tri in tris]

def mesh_xml(tris, oid, name):
    vid, verts, idx = {}, [], []
    for tri in tris:
        for p in tri:
            k = tuple(round(c, 5) for c in p)
            if k not in vid:
                vid[k] = len(verts); verts.append(k)
        idx.append([vid[tuple(round(c, 5) for c in p)] for p in tri])
    v = "".join('<vertex x="%g" y="%g" z="%g"/>' % p for p in verts)
    t = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % tuple(i) for i in idx)
    return '<object id="%d" name="%s" type="model"><mesh><vertices>%s</vertices><triangles>%s</triangles></mesh></object>' % (oid, name, v, t)

stand = load(D + "solder_stand.stl")
insert = load(D + "solder_stand_j1_insert.stl")
# the stand: base on the bed, corner at (5, 5)
stand, mn = place(stand, lambda p: p)
stand = shift(stand, (5 - mn[0], 5 - mn[1], -mn[2]))
# the insert: rotate about x by +90 degrees, (x, y, z) -> (x, -z, y), so the back face (smallest y) is down
insert, mn = place(insert, lambda p: (p[0], -p[2], p[1]))
insert = shift(insert, (95 - mn[0], 5 - mn[1], -mn[2]))

model = ('<?xml version="1.0" encoding="UTF-8"?><model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>'
         + mesh_xml(stand, 1, "solder_stand") + mesh_xml(insert, 2, "j1_insert")
         + '</resources><build><item objectid="1"/><item objectid="2"/></build></model>')
ctypes = ('<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
          '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
          '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
rels = ('<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
out = D + "solder_stand.3mf"
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    z.writestr("[Content_Types].xml", ctypes)
    z.writestr("_rels/.rels", rels)
    z.writestr("3D/3dmodel.model", model)
print("written", out)
