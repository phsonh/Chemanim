from __future__ import annotations

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageStat

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
os.environ.setdefault("QT_QPA_PLATFORM","offscreen")

from PyQt6.QtCore import QTimer,Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication,QDialogButtonBox

from chemanim2d.app import GradientStructureDialog,MainWindow
from chemanim2d.core import BUILD_COMMIT,CoreSession


def by_id(session:CoreSession,node_id:str)->dict:
    return next(value for value in session.project()["nodes"] if value["id"]==node_id)


def capture(window:MainWindow,path:Path)->None:
    window.canvas._refresh_now();QApplication.processEvents();QTest.qWait(80)
    if not window.grab().save(str(path)):raise RuntimeError(f"cannot save {path}")


def main()->None:
    app=QApplication.instance() or QApplication(sys.argv);app.setQuitOnLastWindowClosed(False)
    media=ROOT/"media"/"benzene_acylium_acceptance";mod=ROOT/"mod"/"benzene_acylium_acceptance"
    media.mkdir(parents=True,exist_ok=True);mod.mkdir(parents=True,exist_ok=True)
    window=MainWindow(ROOT);window.resize(1900,1120);window.show();window.session.new_project()

    # The colour overrides intentionally precede the objects.  This is the
    # exact ordering that exposed the stale/black editor path.
    window.session.add_node("arrow_global_set_color",json.dumps({"r":190,"g":45,"b":35}))
    ring=window.session.import_smiles("benzene","c1ccccc1")
    acylium=window.session.import_smiles("acylium","CC#[O+]")
    window.session.add_node("molecule_set_position",json.dumps({"target":ring,"x":-75.0,"y":0.0}))
    window.session.add_node("molecule_set_position",json.dumps({"target":acylium,"x":95.0,"y":0.0}))
    window.session.add_node("arrow_new",json.dumps({"target":"arrow1"}))
    window.session.add_node("arrow_set_curve",json.dumps({"target":"arrow1","initialized":True,"x1":-48.0,"y1":22.0,"cx1":-5.0,"cy1":70.0,"cx2":42.0,"cy2":55.0,"x2":72.0,"y2":12.0}))
    window.session.add_node("arrow_set_progress",json.dumps({"target":"arrow1","value":0.0}))
    window.session.add_node("arrow_lerp_progress",json.dumps({"target":"arrow1","value":1.0,"frames":30,"easing":"linear"}))
    wait=window.session.add_node("wait",json.dumps({"frames":30}))
    window.refresh_all(wait);window._node_selected(wait);window.canvas.fit_artboard();QTest.qWait(80)

    # Manual object merge first, then the public Gradient Structure action.
    window.session.set_active_molecule(ring)
    merge_id=window._add_node("merge_molecules",{"source":acylium},False);QApplication.processEvents()
    merge=by_id(window.session,merge_id);output=merge["params"]["output"]
    if window.session.active_molecule!=output:raise RuntimeError("merge output was not activated")

    def accept_gradient()->None:
        dialog=next((value for value in QApplication.topLevelWidgets() if isinstance(value,GradientStructureDialog) and value.isVisible()),None)
        if dialog is None:QTimer.singleShot(10,accept_gradient);return
        if dialog.target.currentData()!=output:raise RuntimeError("merged output missing from target list")
        dialog.frames.setValue(30);dialog.easing.setCurrentIndex(dialog.easing.findData("linear"))
        QTest.mouseClick(dialog.buttons.button(QDialogButtonBox.StandardButton.Ok),Qt.MouseButton.LeftButton)
    QTimer.singleShot(0,accept_gradient)
    gradient_id=window._add_node("molecule_gradient_structure")
    gradient=by_id(window.session,gradient_id)
    if gradient["params"]["target"]!=output or not window.session.can_edit_structure:
        raise RuntimeError("merged gradient endpoint was not activated")

    params=gradient["params"];end=json.loads(json.dumps(params["end_snapshot"]))
    atoms={value["id"]:value for value in end["atoms"]}
    ring_ids=set(merge["params"]["id_map"]["target"]["atoms"].values())
    acyl_ids=set(merge["params"]["id_map"]["source"]["atoms"].values())
    carbonyl_bond=next(value for value in end["bonds"] if value["type"]=="triple" and value["a"] in acyl_ids and value["b"] in acyl_ids)
    carbonyl_carbon=next(value for value in (carbonyl_bond["a"],carbonyl_bond["b"]) if (atoms[value].get("label") or atoms[value].get("element"))=="C")
    ring_atoms=[atoms[value] for value in ring_ids];centre=(sum(value["x"] for value in ring_atoms)/len(ring_atoms),sum(value["y"] for value in ring_atoms)/len(ring_atoms))
    attack=max(ring_atoms,key=lambda value:value["x"]);length=float(end["reference_bond_length"])
    angle=math.atan2(attack["y"]-centre[1],attack["x"]-centre[0]);desired=(attack["x"]+length*math.cos(angle),attack["y"]+length*math.sin(angle))
    delta=(desired[0]-atoms[carbonyl_carbon]["x"],desired[1]-atoms[carbonyl_carbon]["y"])
    for atom_id in acyl_ids:atoms[atom_id]["x"]+=delta[0];atoms[atom_id]["y"]+=delta[1]
    oxygen_id=carbonyl_bond["b"] if carbonyl_bond["a"]==carbonyl_carbon else carbonyl_bond["a"]
    methyl_id=next(value for value in acyl_ids if value not in (carbonyl_carbon,oxygen_id))
    atoms[oxygen_id]["x"]=atoms[carbonyl_carbon]["x"]+length*math.cos(angle+math.pi/3)
    atoms[oxygen_id]["y"]=atoms[carbonyl_carbon]["y"]+length*math.sin(angle+math.pi/3)
    atoms[methyl_id]["x"]=atoms[carbonyl_carbon]["x"]+length*math.cos(angle-math.pi/3)
    atoms[methyl_id]["y"]=atoms[carbonyl_carbon]["y"]+length*math.sin(angle-math.pi/3)

    bond_id=f'B{end["next_bond_id"]}';end["next_bond_id"]+=1
    end["bonds"].append({"id":bond_id,"a":attack["id"],"b":carbonyl_carbon,"type":"single","secondary_line_side":"center","stereo":"none","visible":True,"alive":True,"alpha":255,"color":{"r":0,"g":0,"b":0}})
    carbonyl_bond["type"]="double"
    changed=next(value for value in end["bonds"] if value["type"]=="double" and value["a"] in ring_ids and value["b"] in ring_ids and attack["id"] in (value["a"],value["b"]))
    changed["type"]="single"
    adjacent=changed["b"] if changed["a"]==attack["id"] else changed["a"]
    # The positive charge belongs to the incoming acylium ion at the start;
    # it fades out while the Wheland-intermediate charge fades in on the ring.
    end["adornments"]=[value for value in end["adornments"] if value.get("atom") not in acyl_ids]
    charge=f'D{end["next_adornment_id"]}';end["next_adornment_id"]+=1
    end["adornments"].append({"id":charge,"creation_serial":990101,"atom":adjacent,"text":"⊕","x":18.0,"y":18.0,"alpha":255,"alive":True,"color":{"r":0,"g":0,"b":0}})
    params["end_snapshot"]=end;window.session.update_node(gradient_id,json.dumps(params,ensure_ascii=False))
    window.session.add_node("arrow_lerp_alpha",json.dumps({"target":"arrow1","value":0,"frames":30,"easing":"linear"}))
    window.refresh_all(gradient_id);window._node_selected(gradient_id);window.canvas.fit_all();capture(window,media/"01-merged-gradient-endpoint.png")

    raw=json.loads(window.session.json());raw["mod"]="benzene_acylium_acceptance";window.session.replace_json(json.dumps(raw,ensure_ascii=False))
    project_path=mod/"benzene_acylium_acceptance.cmm";window.session.save(str(project_path));window.session.write_mod(str(ROOT))
    reopened=CoreSession();reopened.load(str(project_path))
    if reopened.evaluated_project(45)!=window.session.evaluated_project(45):raise RuntimeError("save/reopen mismatch")

    scene=window.session.project()["scene"];window.session.set_viewport(scene["width"],scene["height"],scene["width"]/scene["logic_width"],0.0,0.0)
    executable=ROOT/"build"/"release"/"chemanim.exe";comparison={}
    for label,frame in (("reactants",30),("middle",45),("product",60)):
        window._preview_frame(frame);capture(window,media/f"editor-{label}.png")
        run=subprocess.run([str(executable),raw["mod"],"--frame",str(frame),"--no-open"],cwd=ROOT,capture_output=True,text=True,timeout=120)
        if run.returncode:raise RuntimeError(run.stdout+"\n"+run.stderr)
        engine=media/f"engine-{label}.png";shutil.copy2(media/f'{raw["mod"]}_frame_{frame}.png',engine)
        window.session.set_viewport(scene["width"],scene["height"],scene["width"]/scene["logic_width"],0.0,0.0)
        drawing=window.session.depict_at(frame,True);core=media/f"core-{label}.png";Image.frombytes("RGBA",(drawing["width"],drawing["height"]),bytes(drawing["rgba"])).save(core)
        diff=ImageChops.difference(Image.open(core).convert("RGBA"),Image.open(engine).convert("RGBA"));stats=ImageStat.Stat(diff)
        comparison[label]={"frame":frame,"max_rms":max(stats.rms),"bbox":diff.getbbox()}

    before=set(media.glob(f'{raw["mod"]}_*.mp4'));run=subprocess.run([str(executable),raw["mod"],"--no-open"],cwd=ROOT,capture_output=True,text=True,timeout=240)
    if run.returncode:raise RuntimeError(run.stdout+"\n"+run.stderr)
    created=sorted(set(media.glob(f'{raw["mod"]}_*.mp4'))-before,key=lambda value:value.stat().st_mtime)
    if not created:raise RuntimeError("engine did not create MP4")
    video=media/"benzene-acylium-mechanism.mp4";shutil.copy2(created[-1],video)
    report={"core":BUILD_COMMIT,"merge":merge_id,"output":output,"gradient":gradient_id,"summary":window.session.gradient_summary(gradient_id),"saved_reopened":True,"default_arrow_width":window.session.evaluated_arrows(0)["arrow1"]["width"],"core_engine":comparison,"mp4":video.name}
    (media/"acceptance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(report,ensure_ascii=False))
    window.close();QApplication.processEvents()


if __name__=="__main__":main()
