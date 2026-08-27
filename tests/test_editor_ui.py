from __future__ import annotations

import json
from pathlib import Path
import sys

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QToolButton

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))

from chemanim2d.app import MainWindow
from chemanim2d.periodic_table import PeriodicTableDialog


_APP=None
def application():
    global _APP
    _APP=QApplication.instance() or QApplication([])
    _APP.setQuitOnLastWindowClosed(False)
    return _APP


def window():
    application(); result=MainWindow(ROOT); result.show(); QApplication.processEvents(); result.canvas.fit_artboard(); QApplication.processEvents(); return result


def test_scene_is_single_core_state_and_artboard_updates():
    value=window()
    scene=value.session.project()["scene"]
    scene.update({"width":1080,"height":1920,"logic_width":540,"logic_height":960,"background":"192A44FF"})
    assert value.session.update_scene(json.dumps(scene))
    value.canvas.fit_artboard();QApplication.processEvents()
    rect=value.canvas.artboard_rect()
    assert abs(rect.width()/rect.height()-540/960)<1e-9
    assert value.canvas.scene()["background"]=="192A44FF"
    value.close()


def test_wheel_zoom_keeps_world_point_under_same_pixel():
    value=window();canvas=value.canvas;mouse=QPointF(canvas.width()*.71,canvas.height()*.37);before=canvas.screen_to_world(mouse)
    event=QWheelEvent(mouse,QPointF(canvas.mapToGlobal(mouse.toPoint())),QPoint(),QPoint(0,120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.ScrollUpdate,False)
    canvas.wheelEvent(event);after=canvas.world_to_screen(before)
    assert abs(after.x()-mouse.x())<1e-9 and abs(after.y()-mouse.y())<1e-9
    value.close()


def test_rectangle_preview_has_explicit_kind_and_normalized_geometry():
    value=window();canvas=value.canvas;canvas._sync_core_viewport();value.session.edit_base(0);value.session.set_tool("select_rectangle")
    start=(canvas.width()*.75,canvas.height()*.75);end=(canvas.width()*.25,canvas.height()*.25)
    down=value.session.pointer_down(*start);preview=value.session.pointer_move(*end)["preview"]
    assert down["preview"]["kind"]=="rectangle" and preview["kind"]=="rectangle"
    from PyQt6.QtCore import QRectF
    rect=QRectF(QPointF(preview["start"]["x"],preview["start"]["y"]),QPointF(preview["current"]["x"],preview["current"]["y"])).normalized()
    assert rect.width()>0 and rect.height()>0
    value.session.cancel_gesture();value.close()


def test_node_ui_edits_the_core_ordered_sequence(tmp_path:Path):
    value=window();value._add_node("wait",open_editor=False);wait_id=value.node_list.current_id();value._add_node("molecule_lerp_position",open_editor=False);lerp_id=value.node_list.current_id()
    nodes=value.session.project()["nodes"];assert any(node["id"]==wait_id for node in nodes) and any(node["id"]==lerp_id for node in nodes)
    timing=next(item for item in value.session.node_timings() if item["id"]==lerp_id);assert timing["start"]==30
    assert value.session.move_node(lerp_id,next(i for i,node in enumerate(nodes) if node["id"]==wait_id))
    timing=next(item for item in value.session.node_timings() if item["id"]==lerp_id);assert timing["start"]==0
    path=tmp_path/"ui-roundtrip.cmm";value.session.save(str(path));value.session.load(str(path))
    assert [node["id"] for node in value.session.project()["nodes"]]==[node["id"] for node in json.loads(path.read_text(encoding="utf-8"))["nodes"]]
    value.close()


def test_minimum_zoom_recenters_artboard():
    value=window();canvas=value.canvas;canvas.pan=QPointF(260,-170);low,_=canvas._scale_limits();canvas.view_scale=low*1.01
    mouse=QPointF(canvas.width()*.8,canvas.height()*.2);event=QWheelEvent(mouse,QPointF(canvas.mapToGlobal(mouse.toPoint())),QPoint(),QPoint(0,-120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.ScrollUpdate,False)
    canvas.wheelEvent(event);assert canvas.view_scale==low and canvas.pan==QPointF()
    value.close()


def test_editor_layout_has_node_list_canvas_and_compact_transport_only():
    value=window();assert not hasattr(value,"tree") and not hasattr(value,"atom_inspector")
    assert value.node_list.width()<value.canvas.width() and value.transport.height()<70
    assert value.mode_panel.height()<190
    value.close()


def test_script_molecule_position_drag_changes_node_target_not_base():
    value=window();canvas=value.canvas;canvas._sync_core_viewport();value._set_tool("atom_label")
    center=(canvas.width()*.5,canvas.height()*.5);value.session.pointer_down(*center);value.session.pointer_up(*center)
    base=value.session.project()["molecules"][0]["atoms"][0].copy();node=value._add_node("molecule_lerp_position",{"x":base["x"],"y":base["y"],"frames":30},False)
    value._node_selected(node);drawing=value.session.depict_at(30,False);point=next(item["center"] for item in drawing["atoms"] if item["id"]==base["id"])
    value.session.pointer_down(point["x"],point["y"]);value.session.pointer_move(point["x"]+40,point["y"]-20);assert value.session.pointer_up(point["x"]+40,point["y"]-20)["changed"]
    unchanged=value.session.project()["molecules"][0]["atoms"][0];assert (unchanged["x"],unchanged["y"])==(base["x"],base["y"])
    params=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"];assert (params["x"],params["y"])!=(base["x"],base["y"])
    value.close()


def test_element_toolbar_passes_the_selected_symbol_and_relabels_in_place():
    value=window();value.mode_panel.set_mode("绘制");value.mode_panel.set_category("元素")
    buttons={button.text():button for button in value.mode_panel.tertiary.findChildren(QToolButton)}
    buttons["O"].click();value.canvas._sync_core_viewport()
    center=(value.canvas.width()*.5,value.canvas.height()*.5)
    value.session.pointer_down(*center);value.session.pointer_up(*center)
    atom=value.session.project()["molecules"][0]["atoms"][0];assert atom["element"]=="O"
    buttons["N"].click();point=next(item["center"] for item in value.session.depict(False)["atoms"] if item["id"]==atom["id"])
    value.session.pointer_down(point["x"],point["y"]);value.session.pointer_up(point["x"],point["y"])
    atoms=value.session.project()["molecules"][0]["atoms"]
    assert len(atoms)==1 and atoms[0]["alive"] and atoms[0]["element"]=="N"
    assert value.session.depict(False)["svg"]
    value.close()


def test_periodic_table_uses_real_layout_and_folds_later_periods():
    application();dialog=PeriodicTableDialog()
    assert len(dialog.buttons)==118
    assert dialog.expanded.isHidden()
    assert dialog.table_layout.itemAtPosition(1,1).widget()==dialog.buttons["H"]
    assert dialog.table_layout.itemAtPosition(1,18).widget()==dialog.buttons["He"]
    dialog.expand_button.click();assert not dialog.expanded.isHidden()
    dialog.buttons["Og"].click();assert dialog.selected_element=="Og"


def test_charge_tools_are_circled_symbols_inside_structure_not_a_category():
    value=window();value.mode_panel.set_mode("绘制")
    assert value.mode_panel.DRAW_CATEGORIES==("工具","结构","元素")
    value.mode_panel.set_category("结构")
    buttons={button.property("drawKind"):button for button in value.mode_panel.tertiary.findChildren(QToolButton)}
    assert "charge_positive" in buttons and "charge_negative" in buttons
    assert buttons["charge_positive"].toolTip()=="形式正电荷（带圈 +）"
    value.close()


def test_node_keyboard_delete_undo_redo_and_duplicate_are_focus_aware():
    value=window();created=value._add_node("wait",open_editor=False);value.node_list.tree.setFocus();QApplication.processEvents()
    QTest.keyClick(value.node_list.tree,Qt.Key.Key_D,Qt.KeyboardModifier.ControlModifier)
    assert len([node for node in value.session.project()["nodes"] if node["type"]=="wait"])==2
    QTest.keyClick(value.node_list.tree,Qt.Key.Key_Delete)
    assert len([node for node in value.session.project()["nodes"] if node["type"]=="wait"])==1
    QTest.keyClick(value.node_list.tree,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier)
    assert len([node for node in value.session.project()["nodes"] if node["type"]=="wait"])==2
    QTest.keyClick(value.node_list.tree,Qt.Key.Key_Y,Qt.KeyboardModifier.ControlModifier)
    assert len([node for node in value.session.project()["nodes"] if node["type"]=="wait"])==1
    value.close()


def test_canvas_keyboard_undo_redo_and_delete_operate_on_structure():
    value=window();canvas=value.canvas;canvas.setFocus();canvas._sync_core_viewport();value._set_tool("atom_label")
    center=(canvas.width()*.5,canvas.height()*.5);value.session.pointer_down(*center);value.session.pointer_up(*center);value.refresh_all()
    assert len(value.session.project()["molecules"][0]["atoms"])==1
    QTest.keyClick(canvas,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier);assert not value.session.project()["molecules"][0]["atoms"]
    QTest.keyClick(canvas,Qt.Key.Key_Y,Qt.KeyboardModifier.ControlModifier);assert len(value.session.project()["molecules"][0]["atoms"])==1
    atom=value.session.project()["molecules"][0]["atoms"][0];value._set_tool("select_rectangle");point=next(item["center"] for item in value.session.depict(False)["atoms"] if item["id"]==atom["id"])
    value.session.pointer_down(point["x"],point["y"]);value.session.pointer_up(point["x"],point["y"]);canvas.setFocus();QTest.keyClick(canvas,Qt.Key.Key_Delete)
    assert not value.session.project()["molecules"][0]["atoms"][0]["alive"]
    value.close()
