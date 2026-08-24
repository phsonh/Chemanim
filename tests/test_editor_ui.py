from __future__ import annotations

import json
from pathlib import Path
import sys

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtWidgets import QApplication

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))

from chemanim2d.app import MainWindow


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
    value.scene_inspector.refresh();value.canvas.fit_artboard();QApplication.processEvents()
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
    value=window();value._add_node("wait");wait_id=value.node_list.current_id();value._add_node("molecule_lerp_position");lerp_id=value.node_list.current_id()
    nodes=value.session.project()["nodes"];assert any(node["id"]==wait_id for node in nodes) and any(node["id"]==lerp_id for node in nodes)
    timing=next(item for item in value.session.node_timings() if item["id"]==lerp_id);assert timing["start"]==30
    assert value.session.move_node(lerp_id,next(i for i,node in enumerate(nodes) if node["id"]==wait_id))
    timing=next(item for item in value.session.node_timings() if item["id"]==lerp_id);assert timing["start"]==0
    path=tmp_path/"ui-roundtrip.cmm";value.session.save(str(path));value.session.load(str(path))
    assert [node["id"] for node in value.session.project()["nodes"]]==[node["id"] for node in json.loads(path.read_text(encoding="utf-8"))["nodes"]]
    value.close()
