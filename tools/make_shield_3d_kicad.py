"""Interactive 3D page of the real shield board, made from KiCad: docs/shield-3d-kicad.html.

kicad-cli exports the board (copper, silkscreen, pads and the STEP shapes of the parts) as GLB, and a three.js page
shows it (drag to turn, wheel to zoom). The GLB is embedded in the page, so the file is about 5 MB. Compare
docs/shield-3d.html (tools/make_shield_mock.py): an illustrative model of boxes with a parts list, made without KiCad.

    python tools/make_shield_3d_kicad.py          (plain Python; it calls KiCad's kicad-cli)

The page is not committed (it is in .gitignore, about 5 MB): run the tool to make it.

The 3D models of the board are named .wrl, which KiCad 10 does not ship, so a temporary copy of the board with the
.step files is exported; the board in the repository is not changed. The page loads three.js from cdn.jsdelivr.net
(same version as docs/shield-3d.html). Made with KiCad 10.0.8, 2026-11-18.
"""
import base64
import os
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PCB = ROOT / "hardware" / "shield" / "shield.kicad_pcb"
OUT = ROOT / "docs" / "shield-3d-kicad.html"
KICAD = Path(os.environ.get("KICAD_DIR", r"C:\Program Files\KiCad"))
MODELS = (KICAD / "share" / "kicad" / "3dmodels").as_posix()

PAGE = r"""<!doctype html><html><head><meta charset="utf-8"><title>Shield 3D from KiCad</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>html,body{margin:0;height:100%;background:#e9edf1;font:14px system-ui}#c{width:100%;height:100%;display:block}
#t{position:fixed;left:12px;top:10px;color:#1b2530}</style></head><body>
<div id="t"><b>Shield, 3D from KiCad</b> (drag to turn, wheel to zoom). Colours by kind of part; the LED is shown green as in the design, the ordered boards have the red one.</div><canvas id="c"></canvas>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/loaders/GLTFLoader.js"></script>
<script>
const B64="__GLB__";
const bin=Uint8Array.from(atob(B64),c=>c.charCodeAt(0)).buffer;
const cv=document.getElementById('c');
const r=new THREE.WebGLRenderer({canvas:cv,antialias:true});r.setPixelRatio(devicePixelRatio);
const sc=new THREE.Scene();sc.background=new THREE.Color(0xe9edf1);
const cam=new THREE.PerspectiveCamera(35,1,1,5000);
sc.add(new THREE.AmbientLight(0xffffff,0.55));sc.add(new THREE.HemisphereLight(0xffffff,0x8899aa,0.7));
const d=new THREE.DirectionalLight(0xffffff,0.9);d.position.set(60,120,80);sc.add(d);
const ctl=new THREE.OrbitControls(cam,cv);
new THREE.GLTFLoader().parse(bin,'',g=>{
  const m=g.scene;m.scale.setScalar(1000);sc.add(m);m.updateMatrixWorld(true);   // KiCad's GLB is in metres
  // colour by kind of part: the nodes of the parts are named by reference (R1, C3, J2, ...)
  const COL={R:0x4a5f8a,FB:0x8a6a3a,D:0x3a3c46,TVS:0x8a3a46,U:0x22232a,J:0x3a3d46,LED:0x2fc24a};
  const refs=[];m.traverse(o=>{if(/^[A-Z]{1,3}\d+$/.test(o.name||''))refs.push(o)});
  refs.forEach(ch=>{
    const ref=ch.name||'', kind=/^TVS/.test(ref)?'TVS':ref.replace(/\d+$/,''), col=COL[kind];
    ch.traverse(o=>{
      if(!o.isMesh)return;
      o.material=o.material.clone();
      const t=o.material, dark=Math.max(t.color.r,t.color.g,t.color.b)<0.25;
      if(col!==undefined&&(dark||kind==='LED')){t.color.setHex(col);t.metalness=0;t.roughness=0.55}
      else if(t.metalness===1&&t.roughness===1){t.metalness=0.2;t.roughness=0.5}
    });
  });
  const box=new THREE.Box3().setFromObject(m),c=box.getCenter(new THREE.Vector3()),s=box.getSize(new THREE.Vector3());
  const R=Math.max(s.x,s.y,s.z);
  cam.position.set(c.x+R*0.9,c.y+R*1.2,c.z+R*1.1);ctl.target.copy(c);ctl.update();
},e=>{document.getElementById('t').textContent='Could not read the model: '+e});
function rs(){r.setSize(innerWidth,innerHeight,false);cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix()}
addEventListener('resize',rs);rs();
(function a(){requestAnimationFrame(a);ctl.update();r.render(sc,cam)})();
</script></body></html>"""


def main():
    text = PCB.read_text(encoding="utf-8")
    text = text.replace('.wrl"', '.step"')
    for v in ("KICAD6_3DMODEL_DIR", "KICAD7_3DMODEL_DIR", "KICAD8_3DMODEL_DIR", "KICAD9_3DMODEL_DIR"):
        text = text.replace("${%s}" % v, MODELS)
    with tempfile.TemporaryDirectory() as tmp:
        pcb = Path(tmp) / "shield.kicad_pcb"
        glb = Path(tmp) / "shield.glb"
        pcb.write_text(text, encoding="utf-8")
        subprocess.run([str(KICAD / "bin" / "kicad-cli.exe"), "pcb", "export", "glb", "-f", "--include-tracks", "--include-pads",
                        "--include-zones", "--include-silkscreen", "--include-soldermask", "-o", str(glb), str(pcb)], check=True)
        data = base64.b64encode(glb.read_bytes()).decode()
    OUT.write_text(PAGE.replace("__GLB__", data), encoding="utf-8")
    print("wrote", OUT, f"({OUT.stat().st_size // 1024} kB)")


if __name__ == "__main__":
    main()
