from __future__ import annotations

import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))

from PyQt6.QtCore import QPoint,QPointF,Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication,QSpinBox,QToolButton

from chemanim2d.app import MainWindow
from chemanim2d.core import BUILD_COMMIT


def capture(window:MainWindow,path:Path)->None:
    window.canvas._refresh_now();QApplication.processEvents();QTest.qWait(100)
    if not window.grab().save(str(path)):raise RuntimeError(f"无法保存截图：{path}")


def node_item(window:MainWindow,node_id:str):
    return next(window.node_list.tree.topLevelItem(index) for index in range(window.node_list.tree.topLevelItemCount()) if window.node_list.tree.topLevelItem(index).data(0,Qt.ItemDataRole.UserRole)==node_id)


def open_inspector(window:MainWindow,node_id:str):
    item=node_item(window,node_id);window.node_list.tree.scrollToItem(item);QApplication.processEvents();rect=window.node_list.tree.visualItemRect(item)
    QTest.mouseClick(window.node_list.tree.viewport(),Qt.MouseButton.LeftButton,pos=rect.center());QTest.qWait(40)
    QTest.mouseDClick(window.node_list.tree.viewport(),Qt.MouseButton.LeftButton,pos=rect.center(),delay=60);QApplication.processEvents()
    if window.inspector.node_id!=node_id:raise RuntimeError("真实双击没有打开目标参数面板")


def main()->None:
    app=QApplication(sys.argv);app.setStyle("Fusion");app.setQuitOnLastWindowClosed(False)
    output=ROOT/"media"/"anchor_parameter_acceptance";output.mkdir(parents=True,exist_ok=True)
    window=MainWindow(ROOT);window.resize(1880,1120);window.show();QTest.qWait(150)
    create=next(node for node in window.session.project()["nodes"] if node["type"]=="molecule_create");target=create["params"]["target"]
    structure=window._add_node("molecule_set_structure",{"target":target},False);window.mode_panel.set_mode("绘制");QApplication.processEvents()
    ring=next(button for button in window.mode_panel.tertiary.findChildren(QToolButton) if button.property("drawKind")=="benzene")
    QTest.mouseClick(ring,Qt.MouseButton.LeftButton);click=QPoint(window.canvas.width()//2+230,window.canvas.height()//2-135)
    QTest.mouseClick(window.canvas,Qt.MouseButton.LeftButton,pos=click);QApplication.processEvents()
    identity=next(item for item in window.session.project()["molecules"] if item["id"]==target);anchor=dict(identity["anchor"])
    snapshot=next(item for item in window.session.project()["nodes"] if item["id"]==structure)["params"]["snapshot"]
    atoms=[atom for atom in snapshot["atoms"] if atom.get("alive",True)];local_center=((min(atom["x"] for atom in atoms)+max(atom["x"] for atom in atoms))*.5,(min(atom["y"] for atom in atoms)+max(atom["y"] for atom in atoms))*.5)
    if not identity["anchor_initialized"] or math.hypot(*local_center)>1e-7:raise RuntimeError("首次结构没有归一化到真实锚点")

    position=window._add_node("molecule_set_position",{"target":target,"x":anchor["x"],"y":anchor["y"]},False);window._node_selected(position);window.canvas._refresh_now();QApplication.processEvents()
    control=next(item for item in window.session.direct_controls() if item["id"]=="anchor")["position"]
    shown=window.session.depict(False);screen_center=(sum(item["center"]["x"] for item in shown["atoms"])/6,sum(item["center"]["y"] for item in shown["atoms"])/6)
    anchor_screen=window.canvas.world_to_screen(QPointF(control["x"],control["y"]))
    alignment=math.hypot(anchor_screen.x()-screen_center[0],anchor_screen.y()-screen_center[1]);
    if alignment>1e-6:raise RuntimeError(f"对象锚点没有位于苯环中心：{alignment}")
    capture(window,output/"01-benzene-real-center-anchor.png")

    window._add_node("molecule_set_scale",{"target":target,"value":1.4},False)
    window._add_node("molecule_set_rotation",{"target":target,"value":35.0},False)
    alpha=window._add_node("molecule_set_alpha",{"target":target,"value":255},False);open_inspector(window,alpha)
    editor=window.inspector.editors["value"][0];editor_identity=id(editor)
    if not isinstance(editor,QSpinBox):raise RuntimeError("Alpha 没有使用 QSpinBox")
    results=[]
    for number,key in ((0,Qt.Key.Key_Return),(128,Qt.Key.Key_Tab),(255,Qt.Key.Key_Return)):
        editor.setFocus();QTest.keyClick(editor,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(editor,str(number));QTest.keyClick(editor,key);QApplication.processEvents();QTest.qWait(60)
        stored=next(item for item in window.session.project()["nodes"] if item["id"]==alpha)["params"]["value"]
        results.append(stored)
        if stored!=number or id(window.inspector.editors["value"][0])!=editor_identity:raise RuntimeError("参数提交重建了控件或没有保存")
        if number==0:capture(window,output/"02-alpha-zero-editor-alive.png")
    window.undo();undo_value=next(item for item in window.session.project()["nodes"] if item["id"]==alpha)["params"]["value"]
    window.redo();redo_value=next(item for item in window.session.project()["nodes"] if item["id"]==alpha)["params"]["value"]

    window.inspector_panel.hide();window.node_list.refresh(structure);window._node_selected(structure);window.mode_panel.set_mode("绘制");QApplication.processEvents()
    single=next(button for button in window.mode_panel.tertiary.findChildren(QToolButton) if button.property("drawKind")=="single_bond");QTest.mouseClick(single,Qt.MouseButton.LeftButton)
    for atom_id in (atoms[0]["id"],atoms[2]["id"]):
        window.canvas._refresh_now();center=next(item["center"] for item in window.canvas._depiction["atoms"] if item["id"]==atom_id);QTest.mouseClick(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(round(center["x"]),round(center["y"])));QApplication.processEvents()
    after_topology=next(item for item in window.session.project()["molecules"] if item["id"]==target)["anchor"]
    saved=output/"anchor-parameter-roundtrip.cmm";window.path=saved;window.save();window.load(saved)
    reopened=next(item for item in window.session.project()["molecules"] if item["id"]==target)
    if after_topology!=anchor or reopened["anchor"]!=anchor:raise RuntimeError("拓扑变化或保存重开导致锚点漂移")

    window._add_node("arrow_new",{"target":"arrow1"},False);curve=window._add_node("arrow_set_curve",{"target":"arrow1"},False)
    window.session.update_node(curve,json.dumps({"target":"arrow1","x1":-70,"y1":20,"cx1":-30,"cy1":85,"cx2":35,"cy2":85,"x2":80,"y2":15,"initialized":True}))
    window._add_node("arrow_set_progress",{"target":"arrow1","value":0},False);open_inspector(window,curve);window._node_selected(curve)
    capture(window,output/"03-arrow-progress-zero-natural-node-list.png")

    report={"core":BUILD_COMMIT,"anchor":anchor,"anchor_initialized":True,"local_bbox_center":local_center,"anchor_screen_alignment_pixels":alignment,"alpha_sequence":results,"inspector_widget_preserved":True,"undo_value":undo_value,"redo_value":redo_value,"anchor_after_two_methyl":after_topology,"saved_reopened_anchor":reopened["anchor"],"screenshots":["01-benzene-real-center-anchor.png","02-alpha-zero-editor-alive.png","03-arrow-progress-zero-natural-node-list.png"]}
    (output/"acceptance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(report,ensure_ascii=False));window.close()


if __name__=="__main__":main()
