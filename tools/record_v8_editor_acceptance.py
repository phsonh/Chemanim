from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QToolButton

from chemanim2d.app import MainWindow
from chemanim2d.core import BUILD_COMMIT


def capture(window:MainWindow,path:Path)->None:
    window.canvas._refresh_now();QApplication.processEvents();QTest.qWait(120)
    if not window.grab().save(str(path)):raise RuntimeError(f"无法保存截图：{path}")


def current_params(window:MainWindow,node_id:str)->dict:
    return next(node for node in window.session.project()["nodes"] if node["id"]==node_id)["params"]


def main()->None:
    app=QApplication(sys.argv);app.setStyle("Fusion");app.setQuitOnLastWindowClosed(False)
    output=ROOT/"media"/"v8_editor_acceptance";output.mkdir(parents=True,exist_ok=True)
    window=MainWindow(ROOT);window.resize(1880,1120);window.show();QTest.qWait(180)

    # Registry-driven toolbar: object commands have no redundant section row.
    panel=window.mode_panel;panel.set_mode("脚本");panel.set_category("分子");panel.set_script_scope("对象");QApplication.processEvents()
    assert not panel.section_row.isVisible()
    assert [button.text() for button in panel.tertiary.findChildren(QToolButton) if button.isVisible()]==["新建分子","删除分子","合并分子"]
    capture(window,output/"01-toolbar-no-object-object.png")

    # Atomic insertion below the current selection, before a later Wait.
    first=next(node for node in window.session.project()["nodes"] if node["type"]=="molecule_create")
    window.add_blank();second=window.node_list.current_id();wait=window._add_node("wait",{"frames":120},False)
    window.node_list.refresh(second);window._node_selected(second);window.add_blank();third=window.node_list.current_id()
    ids=[node["id"] for node in window.session.project()["nodes"]]
    assert ids==[ids[0],first["id"],second,third,wait]
    capture(window,output/"02-create-inserted-before-wait.png")

    # A transformed benzene and a real canvas drag on its coordinate node.
    window.session.new_project();target=window.session.import_smiles("苯","c1ccccc1");window.refresh_all();window._select_default_authoring_node();window.canvas.fit_artboard();QTest.qWait(100)
    position=window._add_node("molecule_lerp_position",{"target":target,"x":85.0,"y":-35.0,"frames":18,"easing":"linear"},False)
    position_before=dict(current_params(window,position))
    point=window.session.depict(False)["atoms"][0]["center"];start=QPoint(round(point["x"]),round(point["y"]));end=start+QPoint(58,-32)
    QTest.mousePress(window.canvas,Qt.MouseButton.LeftButton,pos=start);QTest.mouseMove(window.canvas,end,90);QTest.mouseRelease(window.canvas,Qt.MouseButton.LeftButton,pos=end);QApplication.processEvents()
    position_after=dict(current_params(window,position));assert position_after["x"]!=85.0
    window._edit_node_dialog(position);QApplication.processEvents();assert window.inspector_panel.isVisible()
    capture(window,output/"03-molecule-coordinate-drag-and-parameters.png")
    window.inspector_panel.hide();window._add_node("wait",{"frames":18},False)

    # Upstream non-uniform/object/global transforms followed by an aligned local endpoint draft.
    window._add_node("molecule_set_scale_x",{"target":target,"value":.55},False)
    window._add_node("molecule_set_scale_y",{"target":target,"value":1.35},False)
    window._add_node("molecule_set_rotation",{"target":target,"value":28.0},False)
    window._add_node("molecule_global_set_scale",{"value":1.25},False)
    window._add_node("wait",{"frames":8},False)
    gradient=window._add_node("molecule_gradient_structure",{"target":target,"frames":30,"easing":"linear"},False)
    timing=next(item for item in window.session.node_timings() if item["id"]==gradient)
    source=window.session.depict_at(timing["start"],False);target_drawing=window.session.depict(False)
    source_centers={item["id"]:item["center"] for item in source["atoms"]};target_centers={item["id"]:item["center"] for item in target_drawing["atoms"]}
    alignment=max(math.hypot(source_centers[key]["x"]-target_centers[key]["x"],source_centers[key]["y"]-target_centers[key]["y"]) for key in source_centers)
    assert alignment<1e-7,(alignment,source_centers,target_centers)
    window.canvas._refresh_now();QApplication.processEvents();assert window.canvas._onion_raster is not None
    capture(window,output/"04-gradient-onion-aligned.png")

    # v1.0-style arrow free drag first, then P0/C1/C2/P3 fine controls and parameter panel.
    arrow=window._add_node("arrow_new",{"target":"arrow1"},False)
    curve=window._add_node("arrow_set_curve",{"target":"arrow1"},False);canvas=window.canvas;canvas._sync_core_viewport()
    a=QPoint(canvas.width()//2-210,canvas.height()//2+170);b=QPoint(canvas.width()//2+210,canvas.height()//2-150)
    QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=a);QTest.mouseMove(canvas,b,110);QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=b);QApplication.processEvents()
    assert current_params(window,curve)["initialized"] and {item["id"] for item in window.session.direct_controls()}=={"p0","c1","c2","p3"}
    window._add_node("arrow_set_progress",{"target":"arrow1","value":1.0},False);window.node_list.refresh(curve);window._node_selected(curve);window._edit_node_dialog(curve);QApplication.processEvents()
    capture(window,output/"05-arrow-free-drag-four-controls.png")

    # Default click geometry in a fresh local structure: +30 degree bond and point-up ring.
    window.inspector_panel.hide();window.session.new_project();window.session.add_blank_molecule("默认几何");structure=window.session.add_node("molecule_set_structure",json.dumps({"target":window.session.active_molecule}));window.refresh_all(structure);window._node_selected(structure)
    panel.set_mode("绘制");QApplication.processEvents();buttons={button.property("drawKind"):button for button in panel.tertiary.findChildren(QToolButton) if button.property("drawKind")}
    left=QPoint(window.canvas.width()//2-180,window.canvas.height()//2);right=QPoint(window.canvas.width()//2+180,window.canvas.height()//2)
    buttons["single_bond"].click();QTest.mouseClick(window.canvas,Qt.MouseButton.LeftButton,pos=left);buttons["ring6"].click();QTest.mouseClick(window.canvas,Qt.MouseButton.LeftButton,pos=right);QApplication.processEvents()
    snapshot=current_params(window,structure)["snapshot"];atoms=[atom for atom in snapshot["atoms"] if atom.get("alive",True)]
    bond=snapshot["bonds"][0];by_id={atom["id"]:atom for atom in atoms};first_atom,second_atom=by_id[bond["a"]],by_id[bond["b"]]
    angle=math.degrees(math.atan2(second_atom["y"]-first_atom["y"],second_atom["x"]-first_atom["x"]));assert abs(angle-30)<1e-6
    ring_atoms=atoms[2:];top=max(atom["y"] for atom in ring_atoms);bottom=min(atom["y"] for atom in ring_atoms)
    assert sum(abs(atom["y"]-top)<1e-6 for atom in ring_atoms)==1 and sum(abs(atom["y"]-bottom)<1e-6 for atom in ring_atoms)==1
    capture(window,output/"06-default-30-bond-point-up-ring.png")

    report={"core":BUILD_COMMIT,"toolbar_no_duplicate_object":True,"insertion_order":ids,"coordinate_drag":{"changed":position_after!=position_before,"before":{"x":position_before["x"],"y":position_before["y"]},"after":{"x":position_after["x"],"y":position_after["y"]},"parameter_panel_visible":True},"gradient_alignment_max_pixels":alignment,"arrow_free_drag":True,"arrow_controls":["P0","C1","C2","P3"],"default_bond_angle":angle,"point_up_ring":True,"screenshots":[path.name for path in sorted(output.glob("*.png"))]}
    (output/"acceptance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(report,ensure_ascii=False))
    window.close()


if __name__=="__main__":main()
