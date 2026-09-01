from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

from PyQt6.QtCore import QPoint, QPointF, Qt, QTimer
from PyQt6.QtGui import QColor, QImage, QPainter, QWheelEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
                             QLabel, QLineEdit, QPlainTextEdit, QSpinBox, QToolBar, QInputDialog, QDialogButtonBox,
                             QPushButton, QToolButton)

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))

from chemanim2d.app import MainWindow, GradientStructureDialog
from chemanim2d.node_inspector import NodeInspector
from chemanim2d.periodic_table import PeriodicTableDialog


_APP=None
def application():
    global _APP
    _APP=QApplication.instance() or QApplication([])
    _APP.setQuitOnLastWindowClosed(False)
    return _APP


def window():
    application(); result=MainWindow(ROOT); result.show(); QApplication.processEvents(); result.canvas.fit_artboard(); QApplication.processEvents(); return result


def enable_structure(value):
    node=value._add_node("molecule_set_structure",{"target":value.session.active_molecule},False)
    value._node_selected(node);QApplication.processEvents();return node


def active_structure(value):
    current=value.session.edit_target_id
    node=next(item for item in value.session.project()["nodes"] if item["id"]==current)
    key="end_snapshot" if node["type"]=="molecule_gradient_structure" else "snapshot"
    return node["params"][key]


def open_inspector_real(value,node_id):
    item=next(value.node_list.tree.topLevelItem(index) for index in range(value.node_list.tree.topLevelItemCount()) if value.node_list.tree.topLevelItem(index).data(0,Qt.ItemDataRole.UserRole)==node_id)
    value.node_list.tree.scrollToItem(item);QApplication.processEvents();rect=value.node_list.tree.visualItemRect(item)
    QTest.mouseClick(value.node_list.tree.viewport(),Qt.MouseButton.LeftButton,pos=rect.center());QTest.qWait(40)
    QTest.mouseDClick(value.node_list.tree.viewport(),Qt.MouseButton.LeftButton,pos=rect.center(),delay=60);QApplication.processEvents()
    assert value.inspector_panel.isVisible() and value.inspector.node_id==node_id
    return value.inspector


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
    value=window();canvas=value.canvas;canvas._sync_core_viewport();value.session.set_tool("select_rectangle")
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


def test_node_move_cannot_cross_its_object_creation_boundary():
    value=window();target=value.session.import_smiles("苯","c1ccccc1");value.node_list.refresh()
    nodes=value.session.project()["nodes"];create=next(node for node in nodes if node["type"]=="molecule_create" and node["params"]["target"]==target)
    structure=next(node for node in nodes if node["type"]=="molecule_set_structure" and node["params"]["target"]==target)
    item=next(value.node_list.tree.topLevelItem(index) for index in range(value.node_list.tree.topLevelItemCount()) if value.node_list.tree.topLevelItem(index).data(0,Qt.ItemDataRole.UserRole)==structure["id"])
    value.node_list.tree.setCurrentItem(item);before=[node["id"] for node in nodes]
    up=next(button for button in value.node_list.findChildren(QPushButton) if button.text()=="上移")
    QTest.mouseClick(up,Qt.MouseButton.LeftButton);QApplication.processEvents()
    assert [node["id"] for node in value.session.project()["nodes"]]==before
    assert value.node_list.current_id()==structure["id"] and value.session.depict_at(0)["atoms"]
    assert next(index for index,node in enumerate(nodes) if node["id"]==create["id"])<next(index for index,node in enumerate(nodes) if node["id"]==structure["id"])
    value.close()


def test_node_list_ctrl_copy_paste_inserts_after_selection_and_deep_copies_creation():
    value=window();first=value._add_node("wait",{"frames":11},False);second=value._add_node("wait",{"frames":22},False)
    def select(node_id):
        item=next(value.node_list.tree.topLevelItem(index) for index in range(value.node_list.tree.topLevelItemCount()) if value.node_list.tree.topLevelItem(index).data(0,Qt.ItemDataRole.UserRole)==node_id)
        value.node_list.tree.setCurrentItem(item);value.node_list.tree.setFocus();QApplication.processEvents()
    select(first);QTest.keyClick(value.node_list.tree,Qt.Key.Key_C,Qt.KeyboardModifier.ControlModifier)
    select(second);QTest.keyClick(value.node_list.tree,Qt.Key.Key_V,Qt.KeyboardModifier.ControlModifier);QApplication.processEvents()
    pasted=value.node_list.current_id();nodes=value.session.project()["nodes"];ids=[node["id"] for node in nodes]
    assert ids.index(pasted)==ids.index(second)+1 and next(node for node in nodes if node["id"]==pasted)["params"]["frames"]==11
    value.undo();assert pasted not in [node["id"] for node in value.session.project()["nodes"]]
    create=next(node for node in value.session.project()["nodes"] if node["type"]=="molecule_create")
    select(create["id"]);QTest.keyClick(value.node_list.tree,Qt.Key.Key_C,Qt.KeyboardModifier.ControlModifier);QTest.keyClick(value.node_list.tree,Qt.Key.Key_V,Qt.KeyboardModifier.ControlModifier);QApplication.processEvents()
    creation_nodes=[node for node in value.session.project()["nodes"] if node["type"]=="molecule_create"]
    assert len(creation_nodes)==2 and len({node["params"]["target"] for node in creation_nodes})==2
    target=creation_nodes[0]["params"]["target"];alpha=value._add_node("molecule_set_alpha",{"target":target,"value":77},False)
    select(alpha);QTest.keyClick(value.node_list.tree,Qt.Key.Key_C,Qt.KeyboardModifier.ControlModifier)
    scene=next(node["id"] for node in value.session.project()["nodes"] if node["type"]=="scene");select(scene);QTest.keyClick(value.node_list.tree,Qt.Key.Key_V,Qt.KeyboardModifier.ControlModifier);QApplication.processEvents()
    pasted=value.node_list.current_id();nodes=value.session.project()["nodes"];create_index=next(index for index,node in enumerate(nodes) if node["type"]=="molecule_create" and node["params"]["target"]==target);paste_index=next(index for index,node in enumerate(nodes) if node["id"]==pasted)
    assert paste_index>create_index and next(node for node in nodes if node["id"]==pasted)["params"]==next(node for node in nodes if node["id"]==alpha)["params"]
    value.close()


def test_editor_arrow_uses_v1_progress_shape_with_a_filled_head():
    value=window();path,head=value.canvas._arrow_shape(QPointF(0,0),QPointF(30,-40),QPointF(70,-40),QPointF(100,0),1.0,20.0,15.0)
    assert len(head)==3 and abs(head[0].x()-100)<1e-6 and abs(head[0].y())<1e-6
    assert path.currentPosition().x()<head[0].x()
    half_path,half_head=value.canvas._arrow_shape(QPointF(0,0),QPointF(30,0),QPointF(70,0),QPointF(100,0),.5,20.0,15.0)
    assert len(half_head)==3 and 45<half_head[0].x()<55 and half_path.currentPosition().x()<half_head[0].x()
    value.close()


def test_arrow_curve_editor_shows_complete_arrow_when_draw_progress_is_zero():
    value=window();created=value._add_node("arrow_new",{"target":"arrow1"},False);curve=value._add_node("arrow_set_curve",{"target":"arrow1"},False)
    value.session.update_node(curve,json.dumps({"target":"arrow1","x1":-80,"y1":0,"cx1":-30,"cy1":50,"cx2":30,"cy2":50,"x2":80,"y2":0,"initialized":True}))
    value._add_node("arrow_set_progress",{"target":"arrow1","value":0},False);value._node_selected(curve);value.canvas._sync_core_viewport()
    assert value.session.evaluated_arrows(value.canvas.preview_frame)["arrow1"]["progress"]==0
    image=QImage(value.canvas.size(),QImage.Format.Format_ARGB32);image.fill(QColor(0,0,0,0));painter=QPainter(image);value.canvas._draw_arrows(painter);painter.end()
    painted=sum(image.pixelColor(x,y).alpha()>0 for x in range(image.width()) for y in range(image.height()))
    assert 100<painted<2500
    value.close()


def test_node_list_is_one_natural_language_column():
    value=window();target=value.session.active_molecule
    value._add_node("molecule_set_alpha",{"target":target,"value":255},False)
    value._add_node("molecule_lerp_position",{"target":target,"x":0,"y":0,"frames":30,"easing":"linear"},False)
    value._add_node("wait",{"frames":120},False);value.node_list.refresh()
    texts=[value.node_list.tree.topLevelItem(index).text(0) for index in range(value.node_list.tree.topLevelItemCount())]
    assert value.node_list.tree.columnCount()==1 and value.node_list.tree.isHeaderHidden()
    assert "设定 molecule1 透明度为 255" in texts
    assert "30 帧内将 molecule1 坐标变为 (0, 0)，线性" in texts
    assert "等待 120 帧" in texts
    value.close()


def test_minimum_zoom_recenters_artboard():
    value=window();canvas=value.canvas;canvas.pan=QPointF(260,-170);low,_=canvas._scale_limits();canvas.view_scale=low*1.01
    mouse=QPointF(canvas.width()*.8,canvas.height()*.2);event=QWheelEvent(mouse,QPointF(canvas.mapToGlobal(mouse.toPoint())),QPoint(),QPoint(0,-120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.ScrollUpdate,False)
    canvas.wheelEvent(event);assert canvas.view_scale==low and canvas.pan==QPointF()
    value.close()


def test_editor_layout_has_node_list_canvas_and_compact_transport_only():
    value=window();assert not hasattr(value,"tree") and not hasattr(value,"atom_inspector")
    assert value.node_list.width()<value.canvas.width() and value.transport.height()<70
    assert value.mode_panel.height()<220
    value.close()


def test_script_molecule_position_drag_changes_node_target_not_base():
    value=window();enable_structure(value);canvas=value.canvas;canvas._sync_core_viewport();value._set_tool("atom_label")
    center=(canvas.width()*.5,canvas.height()*.5);value.session.pointer_down(*center);value.session.pointer_up(*center)
    base=active_structure(value)["atoms"][0].copy();structure_before=json.loads(json.dumps(active_structure(value)));node=value._add_node("molecule_lerp_position",{"x":base["x"],"y":base["y"],"frames":30},False)
    value._node_selected(node);drawing=value.session.depict_at(30,False);point=next(item["center"] for item in drawing["atoms"] if item["id"]==base["id"])
    value.session.pointer_down(point["x"],point["y"]);value.session.pointer_move(point["x"]+40,point["y"]-20);assert value.session.pointer_up(point["x"]+40,point["y"]-20)["changed"]
    structure_node=next(item for item in value.session.project()["nodes"] if item["type"]=="molecule_set_structure");assert structure_node["params"]["snapshot"]==structure_before
    params=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"];assert (params["x"],params["y"])!=(base["x"],base["y"])
    value.close()


def test_element_toolbar_passes_the_selected_symbol_and_relabels_in_place():
    value=window();enable_structure(value);value.mode_panel.set_mode("绘制");value.mode_panel.set_category("元素")
    buttons={button.text():button for button in value.mode_panel.tertiary.findChildren(QToolButton)}
    buttons["O"].click();value.canvas._sync_core_viewport()
    center=(value.canvas.width()*.5,value.canvas.height()*.5)
    value.session.pointer_down(*center);value.session.pointer_up(*center)
    atom=active_structure(value)["atoms"][0];assert atom["element"]=="C" and atom["label"]=="O"
    buttons={button.text():button for button in value.mode_panel.tertiary.findChildren(QToolButton)}
    buttons["N"].click();point=next(item["center"] for item in value.session.depict(False)["atoms"] if item["id"]==atom["id"])
    value.session.pointer_down(point["x"],point["y"]);value.session.pointer_up(point["x"],point["y"])
    atoms=active_structure(value)["atoms"]
    assert len(atoms)==1 and atoms[0]["alive"] and atoms[0]["element"]=="C" and atoms[0]["label"]=="N"
    assert value.session.depict(False)["svg"]
    value.close()


def test_real_blank_canvas_click_can_create_text_group_and_element(monkeypatch):
    value=window();enable_structure(value);panel=value.mode_panel;panel.set_mode("绘制");QApplication.processEvents()
    monkeypatch.setattr(QInputDialog,"getText",staticmethod(lambda *args,**kwargs:("OH",True)))
    text=next(button for button in panel.tertiary.findChildren(QToolButton) if button.property("drawKind")=="atom_text")
    text.click();first=QPoint(value.canvas.width()//2-45,value.canvas.height()//2)
    QTest.mouseClick(value.canvas,Qt.MouseButton.LeftButton,pos=first);QApplication.processEvents()
    assert len(active_structure(value)["atoms"])==1 and active_structure(value)["atoms"][0]["label"]=="OH"
    oxygen=next(button for button in panel.tertiary.findChildren(QToolButton) if button.property("elementKind")=="O")
    oxygen.click();second=QPoint(value.canvas.width()//2+45,value.canvas.height()//2)
    QTest.mouseClick(value.canvas,Qt.MouseButton.LeftButton,pos=second);QApplication.processEvents()
    atoms=active_structure(value)["atoms"]
    assert len(atoms)==2 and atoms[-1]["label"]=="O"
    value.close()


def test_periodic_table_uses_complete_32_column_long_form_layout():
    application();dialog=PeriodicTableDialog()
    assert len(dialog.buttons)==118
    assert dialog.table_layout.itemAtPosition(1,1).widget()==dialog.buttons["H"]
    assert dialog.table_layout.itemAtPosition(1,32).widget()==dialog.buttons["He"]
    assert dialog.table_layout.itemAtPosition(6,3).widget()==dialog.buttons["La"]
    assert dialog.table_layout.itemAtPosition(6,17).widget()==dialog.buttons["Lu"]
    assert dialog.table_layout.itemAtPosition(6,18).widget()==dialog.buttons["Hf"]
    assert dialog.table_layout.itemAtPosition(7,3).widget()==dialog.buttons["Ac"]
    assert dialog.table_layout.itemAtPosition(7,18).widget()==dialog.buttons["Rf"]
    assert not hasattr(dialog,"expand_button")
    dialog.buttons["Og"].click();assert dialog.selected_element=="Og"


def test_element_toolbar_tracks_only_ten_most_recent_elements():
    value=window();enable_structure(value);value.mode_panel.set_mode("绘制");value.mode_panel.set_category("元素")
    value._set_element("Xe")
    assert value.mode_panel.recent_elements==["Xe","C","N","O","H","S","P","F","Cl","Br"]
    QApplication.processEvents()
    buttons=[button.text() for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible() and button.property("drawKind") is None and button.property("textNumberStyle") is None and button.text()!="周期表…"]
    assert buttons==value.mode_panel.recent_elements and len(buttons)==10
    value.close()


def test_script_tools_are_text_only_and_molecule_arrow_use_scope_tabs():
    value=window();value.mode_panel.set_mode("脚本");value.mode_panel.set_category("分子")
    assert [value.mode_panel.scope_tabs.tabText(i) for i in range(value.mode_panel.scope_tabs.count())]==["对象","设定","变换","全局"]
    for scope in ("对象","设定","变换","全局"):
        value.mode_panel.set_script_scope(scope);QApplication.processEvents()
        buttons=[button for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible()]
        assert buttons and all(button.icon().isNull() for button in buttons)
    value.mode_panel.set_category("箭头");assert value.mode_panel.scope_row.isVisible()
    value.close()


def test_primary_node_toolbar_is_registry_driven_and_has_exact_object_commands():
    value=window();value.mode_panel.set_mode("脚本");value.mode_panel.set_category("分子")
    value.mode_panel.set_script_scope("对象");QApplication.processEvents()
    assert [button.text() for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible()]==["新建分子","删除分子","合并分子","分裂分子"]
    value.mode_panel.set_category("箭头");value.mode_panel.set_script_scope("对象");QApplication.processEvents()
    assert [button.text() for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible()]==["新建箭头","删除箭头"]
    value.close()


def test_primary_node_toolbar_uses_four_visible_rows_and_direct_action_buttons():
    value=window();panel=value.mode_panel;panel.set_mode("脚本");panel.set_category("分子")
    def visible_sections(scope):
        panel.set_script_scope(scope);QApplication.processEvents()
        return [panel.section_tabs.tabText(index) for index in range(panel.section_tabs.count())]
    def actions(section):
        panel.set_script_section(section);QApplication.processEvents()
        buttons=[button for button in panel.tertiary.findChildren(QToolButton) if button.isVisible()]
        assert all(button.menu() is None for button in buttons)
        return [button.text() for button in buttons]
    assert visible_sections("全局")==["颜色","缩放"] and actions("颜色")==["透明度","颜色"]
    assert visible_sections("设定")==["结构","位置","缩放","旋转","颜色","排列"] and actions("位置")==["坐标","横坐标","纵坐标"]
    assert visible_sections("变换")==["结构","位置","缩放","旋转","颜色"] and actions("结构")==["渐变结构"]
    assert panel.secondary_row.isVisible() and panel.scope_row.isVisible() and panel.section_row.isVisible() and panel.scroll.isVisible()
    panel.set_category("箭头")
    assert visible_sections("设定")==["曲线","绘制","缩放","颜色","线条"]
    assert "位置" not in visible_sections("设定") and "位置" not in visible_sections("变换")
    value.close()


def test_general_toolbar_has_no_redundant_scope_or_section_rows():
    value=window();panel=value.mode_panel;panel.set_mode("脚本");panel.set_category("通用");QApplication.processEvents()
    assert not panel.scope_row.isVisible() and not panel.section_row.isVisible()
    assert [button.text() for button in panel.tertiary.findChildren(QToolButton) if button.isVisible()]==["场景设置","等待"]
    value.close()


def test_object_split_merge_have_human_readable_locked_targets_and_no_internal_ids():
    value=window();first=value.session.import_smiles("主分子","CC");second=value.session.import_smiles("并入分子","O");last=value.session.project()["nodes"][-1]["id"];value.refresh_all(last);value.session.set_active_molecule(first)
    node=value._add_node("merge_molecules",{"source":second},False);QApplication.processEvents()
    created=next(item for item in value.session.project()["nodes"] if item["id"]==node)
    assert created["params"]["target"]==first and created["params"]["source"]==second and created["params"]["output"]
    item=next(value.node_list.tree.topLevelItem(index) for index in range(value.node_list.tree.topLevelItemCount()) if value.node_list.tree.topLevelItem(index).data(0,Qt.ItemDataRole.UserRole)==node)
    assert item.text(0)==f'合并 {first} 与 {second}，生成 {created["params"]["output"]}'
    value._edit_node_dialog(node);QApplication.processEvents()
    assert value.inspector.title.text().startswith("合并分子")
    assert set(value.inspector.editors)=={"target","source","output"}
    assert all(value.inspector.editors[key][0].isReadOnly() for key in ("target","source","output"))
    assert not any("ID" in label.text() for label in value.inspector.findChildren(QLabel))
    value.close()


def test_real_object_toolbar_split_merge_and_pair_move_do_not_crash_or_swallow_nodes(monkeypatch):
    value=window();primary=value.session.import_smiles("叔丁基溴","CC(C)(C)Br");partner=value.session.import_smiles("氯离子","[Cl-]")
    project=value.session.project();primary_structure=next(node["id"] for node in project["nodes"] if node["type"]=="molecule_set_structure" and node["params"]["target"]==primary)
    value.refresh_all(primary_structure);value._node_selected(primary_structure);QApplication.processEvents()
    panel=value.mode_panel;panel.set_mode("脚本");panel.set_category("分子");panel.set_script_scope("对象");QApplication.processEvents()

    split_button=next(button for button in panel.tertiary.findChildren(QToolButton) if button.isVisible() and button.text()=="分裂分子")
    QTest.mouseClick(split_button,Qt.MouseButton.LeftButton);QApplication.processEvents()
    split_id=value.node_list.current_id();split=next(node for node in value.session.project()["nodes"] if node["id"]==split_id)
    assert split["type"]=="split_molecule" and split["params"]["target"]==primary
    split_output=split["params"]["output"]
    assert value.session.active_molecule==split_output

    def choose_partner(*args,**kwargs):
        items=list(args[3]);choice=next(item for item in items if item==partner);return choice,True
    monkeypatch.setattr(QInputDialog,"getItem",staticmethod(choose_partner))
    panel.set_mode("脚本");panel.set_category("分子");panel.set_script_scope("对象");QApplication.processEvents()
    merge_button=next(button for button in panel.tertiary.findChildren(QToolButton) if button.isVisible() and button.text()=="合并分子")
    QTest.mouseClick(merge_button,Qt.MouseButton.LeftButton);QApplication.processEvents()
    merge_id=value.node_list.current_id();merge=next(node for node in value.session.project()["nodes"] if node["id"]==merge_id)
    assert merge["type"]=="merge_molecules" and merge["params"]["target"]==split_output and merge["params"]["source"]==partner

    before_ids=[node["id"] for node in value.session.project()["nodes"]]
    output=merge["params"]["output"]
    create_id=next(node["id"] for node in value.session.project()["nodes"] if node["type"]=="molecule_create" and node["params"]["target"]==output)
    up=next(button for button in value.node_list.findChildren(QPushButton) if button.text()=="上移")
    QTest.mouseClick(up,Qt.MouseButton.LeftButton);QApplication.processEvents()
    moved=[node["id"] for node in value.session.project()["nodes"]]
    assert set(moved)==set(before_ids) and len(moved)==len(before_ids)
    assert moved.index(create_id)+1==moved.index(merge_id)
    assert value.node_list.current_id()==merge_id and value.session.active_molecule==output

    # A retired cached active target must never produce the false "no living
    # molecule" error while the newly merged output is visibly alive.
    value.session.set_active_molecule(split_output)
    gradient_id=value._add_node("molecule_gradient_structure",open_editor=False);QApplication.processEvents()
    gradient=next(node for node in value.session.project()["nodes"] if node["id"]==gradient_id)
    assert gradient["type"]=="molecule_gradient_structure" and gradient["params"]["target"]==output
    assert value.session.active_molecule==output and "没有仍然存活" not in value.statusBar().currentMessage()
    value.close()


def test_gradient_inspector_and_tree_hide_internal_ids_and_legacy_fields():
    value=window();value.session.import_smiles("苯","c1ccccc1");value.refresh_all();value._select_default_authoring_node()
    node=value._add_node("molecule_gradient_structure",open_editor=False);QApplication.processEvents()
    target=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]["target"]
    item=value.node_list.tree.currentItem();assert item.text(0)==f"30 帧内将 {target} 结构渐变为终态，线性" and "N" not in item.text(0)
    inspector=NodeInspector(value.session);inspector.set_node(node)
    visible=" ".join(label.text() for label in inspector.findChildren(__import__('PyQt6.QtWidgets',fromlist=['QLabel']).QLabel))
    assert "目标分子" not in visible or target in visible
    assert not any(text in visible for text in ("原子 ID","键 ID","标记 ID",node))
    snapshots=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]
    inspector.editors["frames"][0].setValue(42);inspector.apply()
    changed=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]
    assert changed["frames"]==42 and changed["start_snapshot"]==snapshots["start_snapshot"] and changed["end_snapshot"]==snapshots["end_snapshot"]
    legacy=value.session.add_node("selection_show",json.dumps({"target":value.session.active_molecule,"atoms":"A1","bonds":"B1","frames":10}))
    inspector.set_node(legacy);visible=" ".join(label.text() for label in inspector.findChildren(__import__('PyQt6.QtWidgets',fromlist=['QLabel']).QLabel))
    assert "旧版结构节点，仅用于兼容" in visible and "A1" not in visible and "B1" not in visible and legacy not in visible
    value.close()


def test_gradient_start_current_end_modes_gate_endpoint_editing():
    value=window();value.session.import_smiles("苯","c1ccccc1");value.refresh_all();value._select_default_authoring_node()
    node=value._add_node("molecule_gradient_structure",open_editor=False)
    assert value.edit_mode.text()=="正在编辑：渐变结构终态" and value.session.can_edit_structure
    value._show_gradient_phase("start");assert value.edit_mode.text()=="渐变结构起点：只读" and not value.session.can_edit_structure
    value.frame_spin.setValue(15);QApplication.processEvents();assert value.edit_mode.text()=="预览：只读" and not value.session.can_edit_structure
    value._show_gradient_phase("end");assert value.edit_mode.text()=="正在编辑：渐变结构终态" and value.session.can_edit_structure
    value.close()


def test_gradient_endpoint_single_bond_tool_stays_authoritative_for_two_clicks_after_upstream_nodes():
    value=window();target=value.session.import_smiles("苯","c1ccccc1");value.refresh_all();value._select_default_authoring_node()
    value._add_node("molecule_set_position",{"target":target,"x":120.0,"y":-40.0},False)
    value._add_node("molecule_set_scale",{"target":target,"value":0.5},False)
    value._add_node("molecule_lerp_scale",{"target":target,"value":0.2,"frames":12,"easing":"linear"},False)
    value._add_node("molecule_lerp_alpha",{"target":target,"value":180,"frames":8,"easing":"linear"},False)
    value._add_node("wait",{"frames":6},False)
    node=value._add_node("molecule_gradient_structure",{"frames":30,"easing":"linear"},False)
    start=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]["start_snapshot"]
    original_ids=[atom["id"] for atom in start["atoms"] if atom.get("alive",True)]

    panel=value.mode_panel;panel.set_mode("绘制");QApplication.processEvents()
    single=next(button for button in panel.tertiary.findChildren(QToolButton) if button.property("drawKind")=="single_bond")
    single.click();assert single.isChecked();value.canvas._sync_core_viewport()
    for atom_id in (original_ids[0],original_ids[2]):
        point=next(item["center"] for item in value.session.depict(False)["atoms"] if item["id"]==atom_id)
        value.session.pointer_down(point["x"],point["y"]);result=value.session.pointer_up(point["x"],point["y"])
        assert result["changed"];value._transaction();QApplication.processEvents()

    params=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]
    end=params["end_snapshot"]
    assert len([atom for atom in end["atoms"] if atom["id"] not in original_ids and atom.get("alive",True)])==2
    assert len([bond for bond in end["bonds"] if bond["id"] not in {item["id"] for item in start["bonds"]} and bond.get("alive",True)])==2
    assert value.session.tool=="single_bond"
    assert single.isChecked() and panel._active_draw_tool==value.session.tool
    value.close()


def test_draw_tool_ui_follows_core_across_element_eraser_undo_redo_and_real_node_switch():
    value=window();value.session.import_smiles("苯","c1ccccc1");value.refresh_all();value._select_default_authoring_node()
    wait=value._add_node("wait",{"frames":5},False);node=value._add_node("molecule_gradient_structure",{"frames":20},False)
    start=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]["start_snapshot"]
    ids=[atom["id"] for atom in start["atoms"] if atom.get("alive",True)]
    panel=value.mode_panel;panel.set_mode("绘制");QApplication.processEvents();value.canvas._sync_core_viewport()

    h_button=next(button for button in panel.tertiary.findChildren(QToolButton) if button.property("elementKind")=="H")
    h_button.click();assert value.session.tool=="atom_label" and value.session.element=="H" and h_button.isChecked()
    for atom_id in ids[:2]:
        point=next(item["center"] for item in value.session.depict(False)["atoms"] if item["id"]==atom_id)
        value.session.pointer_down(point["x"],point["y"]);assert value.session.pointer_up(point["x"],point["y"])["changed"];value._transaction()
        assert value.session.tool=="atom_label" and h_button.isChecked()
    end=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]["end_snapshot"]
    assert all(next(atom for atom in end["atoms"] if atom["id"]==atom_id)["label"]=="H" for atom_id in ids[:2])

    eraser=next(button for button in panel.tertiary.findChildren(QToolButton) if button.property("drawKind")=="eraser")
    eraser.click();points=[next(item["center"] for item in value.session.depict(False)["atoms"] if item["id"]==atom_id) for atom_id in ids[2:4]]
    value.session.pointer_down(points[0]["x"],points[0]["y"]);value.session.pointer_move(points[1]["x"],points[1]["y"])
    assert value.session.pointer_up(points[1]["x"],points[1]["y"])["changed"];value._transaction()
    assert value.session.tool=="eraser" and eraser.isChecked()
    value.undo();assert value.session.tool=="eraser" and eraser.isChecked()
    value.redo();assert value.session.tool=="eraser" and eraser.isChecked()

    value.node_list.refresh(wait);value._node_selected(wait)
    rectangle=next(button for button in panel.tertiary.findChildren(QToolButton) if button.property("drawKind")=="select_rectangle")
    assert value.session.tool=="select_rectangle" and rectangle.isChecked() and panel._active_draw_tool==value.session.tool
    value.close()


def test_main_menu_has_no_redundant_second_row_toolbar_and_nodes_have_no_checks():
    value=window();assert value.findChildren(QToolBar)==[]
    item=value.node_list.tree.topLevelItem(0)
    assert not bool(item.flags()&Qt.ItemFlag.ItemIsUserCheckable)
    assert value.node_list.tree.font().pointSizeF()>=10.5
    value.close()


def test_charge_tools_are_circled_symbols_inside_structure_not_a_category():
    value=window();value.mode_panel.set_mode("绘制")
    assert value.mode_panel.DRAW_CATEGORIES==("绘制",) and not value.mode_panel.secondary_row.isVisible()
    buttons={button.property("drawKind"):button for button in value.mode_panel.tertiary.findChildren(QToolButton)}
    assert "charge_positive" in buttons and "charge_negative" in buttons
    assert buttons["charge_positive"].toolTip()=="形式正电荷（带圈 +）"
    assert {"select_rectangle","single_bond","ring6","solid_bar","hashed_bar"}<set(buttons)
    value.close()


def test_text_tool_number_style_controls_are_only_enabled_for_text():
    value=window();enable_structure(value);value.mode_panel.set_mode("绘制")
    buttons={button.property("drawKind"):button for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.property("drawKind")}
    styles={button.property("textNumberStyle"):button for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.property("textNumberStyle")}
    assert set(styles)=={"normal","subscript","superscript"} and not any(button.isEnabled() for button in styles.values())
    buttons["atom_text"].click();assert all(button.isEnabled() for button in styles.values())
    styles["superscript"].click();assert value.mode_panel.text_number_style=="superscript" and styles["superscript"].isChecked()
    buttons["single_bond"].click();assert not any(button.isEnabled() for button in styles.values())
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
    value=window();enable_structure(value);canvas=value.canvas;canvas.setFocus();canvas._sync_core_viewport();value._set_tool("atom_label")
    center=(canvas.width()*.5,canvas.height()*.5);value.session.pointer_down(*center);value.session.pointer_up(*center);value.refresh_all()
    assert len(active_structure(value)["atoms"])==1
    QTest.keyClick(canvas,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier);assert not active_structure(value)["atoms"]
    QTest.keyClick(canvas,Qt.Key.Key_Y,Qt.KeyboardModifier.ControlModifier);assert len(active_structure(value)["atoms"])==1
    atom=active_structure(value)["atoms"][0];value._set_tool("select_rectangle");point=next(item["center"] for item in value.session.depict(False)["atoms"] if item["id"]==atom["id"])
    value.session.pointer_down(point["x"],point["y"]);value.session.pointer_up(point["x"],point["y"]);canvas.setFocus();QTest.keyClick(canvas,Qt.Key.Key_Delete)
    assert not next(item for item in active_structure(value)["atoms"] if item["id"]==atom["id"])["alive"]
    value.close()


def test_canvas_control_a_selects_all_alive_structure():
    value=window();enable_structure(value);canvas=value.canvas;canvas.setFocus();canvas._sync_core_viewport();value._set_tool("ring5")
    center=(canvas.width()*.5,canvas.height()*.5);value.session.pointer_down(*center);value.session.pointer_up(*center);value.refresh_all()
    QTest.keyClick(canvas,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
    molecule=active_structure(value)
    assert set(canvas.selected_atoms)=={atom["id"] for atom in molecule["atoms"] if atom["alive"]}
    assert set(canvas.selected_bonds)=={bond["id"] for bond in molecule["bonds"] if bond["alive"]}
    value.close()


def test_canvas_control_drag_rect_selects_without_leaving_current_draw_tool():
    value=window();enable_structure(value);canvas=value.canvas;canvas._sync_core_viewport();value._set_tool("ring5")
    center=QPoint(canvas.width()//2,canvas.height()//2);QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=center);QApplication.processEvents()
    points=[item["center"] for item in value.session.depict(False)["atoms"]]
    start=QPoint(round(min(point["x"] for point in points)-20),round(min(point["y"] for point in points)-20))
    end=QPoint(round(max(point["x"] for point in points)+20),round(max(point["y"] for point in points)+20))
    value._set_tool("single_bond")
    QTest.mousePress(canvas,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.ControlModifier,pos=start)
    QTest.mouseMove(canvas,end,80)
    assert canvas._preview["kind"]=="rectangle"
    QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.ControlModifier,pos=end)
    assert value.session.tool=="single_bond" and len(canvas.selected_atoms)==5 and len(canvas.selected_bonds)==5
    value.close()


def test_bond_hover_outline_uses_every_visible_double_and_triple_stroke():
    value=window();canvas=value.canvas
    base={"first":{"x":100.0,"y":100.0},"second":{"x":180.0,"y":100.0},
          "line_spacing":12.0,"secondary_line_side":"center"}
    assert len(canvas._bond_highlight_segments({**base,"type":"single"}))==1
    double=canvas._bond_highlight_segments({**base,"type":"double"})
    triple=canvas._bond_highlight_segments({**base,"type":"triple"})
    assert len(double)==2 and len(triple)==3
    assert {round(segment[0].y(),2) for segment in double}=={94.0,106.0}
    assert {round(segment[0].y(),2) for segment in triple}=={88.0,100.0,112.0}
    extended=canvas._bond_highlight_segments({**base,"type":"double",
        "first_extensions":(-4.0,0.0),"second_extensions":(4.0,0.0)})
    assert len(extended)==2
    assert extended[0][0].x()==100.0 and extended[0][1].x()==180.0
    assert extended[1][0].x()==96.0 and extended[1][1].x()==184.0
    value.close()


def test_structure_toolbar_requires_explicit_structure_node_and_keeps_selection():
    value=window();create=next(node for node in value.session.project()["nodes"] if node["type"]=="molecule_create")
    assert value.node_list.current_id()==create["id"] and not value.session.can_edit_structure
    value.mode_panel.set_mode("绘制");QApplication.processEvents()
    buttons={button.property("drawKind"):button for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.property("drawKind")}
    assert not buttons["single_bond"].isEnabled()
    structure_node=enable_structure(value);value.mode_panel.set_mode("绘制");QApplication.processEvents()
    buttons={button.property("drawKind"):button for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.property("drawKind")}
    assert buttons["single_bond"].isEnabled();assert value.edit_mode.text()=="正在编辑：分子结构";value._set_tool("single_bond");assert value.node_list.current_id()==structure_node

    wait=value._add_node("wait",open_editor=False);assert value.node_list.current_id()==wait
    assert value.session.edit_target_kind=="script_node" and not value.session.can_edit_structure
    value.mode_panel.set_mode("绘制");QApplication.processEvents()
    buttons={button.property("drawKind"):button for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.property("drawKind")}
    assert not buttons["single_bond"].isEnabled() and buttons["select_rectangle"].isEnabled()
    old_tool=value.session.tool;value._set_tool("single_bond")
    assert value.session.tool==old_tool and value.node_list.current_id()==wait


def test_blank_molecule_real_ui_inserts_after_selection_and_before_wait():
    value=window()
    first=next(node for node in value.session.project()["nodes"] if node["type"]=="molecule_create")
    value.add_blank();second=value.node_list.current_id();wait=value._add_node("wait",{"frames":120},False)
    value.node_list.refresh(second);value._node_selected(second);value.add_blank();third=value.node_list.current_id()
    nodes=value.session.project()["nodes"]
    assert [node["id"] for node in nodes]==[nodes[0]["id"],first["id"],second,third,wait]
    timings={item["id"]:item for item in value.session.node_timings()}
    assert timings[third]["start"]==0 and timings[wait]["start"]==0
    assert value.session.active_molecule==next(node for node in nodes if node["id"]==third)["params"]["target"]
    value.close()


def test_double_click_parameter_panel_is_nonmodal_and_coordinate_drag_uses_real_mouse():
    value=window();target=value.session.import_smiles("苯","c1ccccc1");value.refresh_all();value._select_default_authoring_node()
    node=value._add_node("molecule_lerp_position",{"target":target,"x":0.0,"y":0.0,"frames":30,"easing":"linear"},False)
    item=value.node_list.tree.currentItem();value.node_list.tree.scrollToItem(item);QApplication.processEvents();rect=value.node_list.tree.visualItemRect(item)
    QTest.mouseClick(value.node_list.tree.viewport(),Qt.MouseButton.LeftButton,pos=rect.center());QTest.qWait(80)
    QTest.mouseDClick(value.node_list.tree.viewport(),Qt.MouseButton.LeftButton,pos=rect.center(),delay=80);QApplication.processEvents()
    assert value.inspector_panel.isVisible() and value.inspector.node_id==node
    assert {"x","y","frames","easing"}<=set(value.inspector.editors)
    canvas=value.canvas;canvas._sync_core_viewport();point=value.session.depict(False)["atoms"][0]["center"]
    start=QPoint(round(point["x"]),round(point["y"]));end=start+QPoint(36,-24)
    before_world=canvas.screen_to_world(QPointF(start));after_world=canvas.screen_to_world(QPointF(end))
    QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=start);QTest.mouseMove(canvas,end,80);QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=end);QApplication.processEvents()
    params=next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]
    assert abs(params["x"]-(after_world.x()-before_world.x()))<1.0 and abs(params["y"]-(after_world.y()-before_world.y()))<1.0
    assert abs(value.inspector.editors["x"][0].value()-params["x"])<.01
    value.close()


def test_alpha_real_keyboard_commits_keep_inspector_alive_and_use_one_undo_each():
    value=window();target=value.session.import_smiles("苯","c1ccccc1");value.refresh_all();value._select_default_authoring_node()
    node=value._add_node("molecule_set_alpha",{"target":target,"value":255},False);inspector=open_inspector_real(value,node)
    editor=inspector.editors["value"][0];assert isinstance(editor,QSpinBox)
    def commit(number,key):
        editor.setFocus();QTest.keyClick(editor,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(editor,str(number));QTest.keyClick(editor,key);QApplication.processEvents();QTest.qWait(40)
        assert inspector.node_id==node and inspector.editors["value"][0] is editor and value.inspector_panel.isVisible()
        return next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]["value"]
    assert commit(0,Qt.Key.Key_Return)==0
    evaluated=next(item for item in value.session.evaluated_project(value.session.preview_frame)["molecules"] if item["id"]==target);assert evaluated["alpha"]==0
    assert commit(128,Qt.Key.Key_Tab)==128
    assert commit(255,Qt.Key.Key_Return)==255
    value.undo();assert next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]["value"]==128
    value.undo();assert next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]["value"]==0
    value.undo();assert next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]["value"]==255
    value.redo();assert next(item for item in value.session.project()["nodes"] if item["id"]==node)["params"]["value"]==0
    value.close()


def test_all_parameter_widget_classes_use_real_events_without_rebuilding(tmp_path):
    value=window();target=value.session.import_smiles("苯","c1ccccc1");value.refresh_all();value._select_default_authoring_node()
    second=value.session.add_blank_molecule("第二分子");second_create=next(item["id"] for item in value.session.project()["nodes"] if item["type"]=="molecule_create" and item["params"]["target"]==second);value.refresh_all(second_create);value._node_selected(second_create)

    position=value._add_node("molecule_lerp_position",{"target":target,"x":0.0,"y":0.0,"frames":30,"easing":"linear"},False)
    inspector=open_inspector_real(value,position);x=inspector.editors["x"][0];frames=inspector.editors["frames"][0];easing=inspector.editors["easing"][0]
    assert isinstance(x,QDoubleSpinBox) and isinstance(frames,QSpinBox) and isinstance(easing,QComboBox)
    x.setFocus();QTest.keyClick(x,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(x,"42.5");QTest.keyClick(x,Qt.Key.Key_Return)
    frames.setFocus();QTest.keyClick(frames,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(frames,"18");QTest.keyClick(frames,Qt.Key.Key_Tab)
    easing.setFocus();QTest.keyClick(easing,Qt.Key.Key_Down);QApplication.processEvents();assert inspector.editors["x"][0] is x

    alpha=value._add_node("molecule_set_alpha",{"target":target,"value":255},False);inspector=open_inspector_real(value,alpha);target_box=inspector.editors["target"][0]
    assert isinstance(target_box,QComboBox) and target_box.count()>=2;choice=target_box.findData(second);assert choice>=0
    target_box.setFocus();target_box.showPopup();QApplication.processEvents();QTest.keyClick(target_box,Qt.Key.Key_End);QTest.keyClick(target_box,Qt.Key.Key_Return);QApplication.processEvents()
    assert next(item for item in value.session.project()["nodes"] if item["id"]==alpha)["params"]["target"]==second

    color=value._add_node("molecule_set_color",{"target":target,"r":255,"g":255,"b":255},False);inspector=open_inspector_real(value,color);red=inspector.editors["r"][0]
    assert isinstance(red,QSpinBox);red.setFocus();QTest.keyClick(red,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(red,"64");QTest.keyClick(red,Qt.Key.Key_Return);QApplication.processEvents()
    layer=value._add_node("molecule_set_layer",{"target":target,"value":0},False);inspector=open_inspector_real(value,layer);layer_spin=inspector.editors["value"][0]
    assert isinstance(layer_spin,QSpinBox);layer_spin.setFocus();QTest.keyClick(layer_spin,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(layer_spin,"3");QTest.keyClick(layer_spin,Qt.Key.Key_Tab);QApplication.processEvents()

    visible=value._add_node("molecule_set_visible",{"target":target,"value":True},False);inspector=open_inspector_real(value,visible);check=inspector.editors["value"][0]
    assert isinstance(check,QCheckBox);check.setFocus();QTest.keyClick(check,Qt.Key.Key_Space);QApplication.processEvents();assert not next(item for item in value.session.project()["nodes"] if item["id"]==visible)["params"]["value"]

    atom=next(item for item in value.session.evaluated_project(0)["molecules"] if item["id"]==target)["atoms"][0]["id"]
    text_node=value._add_node("atom_set_element",{"target":target,"atom":atom,"value":"C"},False);inspector=open_inspector_real(value,text_node);line=inspector.editors["value"][0]
    assert isinstance(line,QLineEdit);line.setFocus();QTest.keyClick(line,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(line,"N");QTest.keyClick(line,Qt.Key.Key_Return);QApplication.processEvents()

    raw=value._add_node("raw_lua",{"code":"-- initial"},False);inspector=open_inspector_real(value,raw);multiline=inspector.editors["code"][0]
    assert isinstance(multiline,QPlainTextEdit);multiline.setFocus();QTest.keyClick(multiline,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(multiline,"-- edited once");QTest.qWait(320);QApplication.processEvents()
    assert inspector.editors["code"][0] is multiline and next(item for item in value.session.project()["nodes"] if item["id"]==raw)["params"]["code"]=="-- edited once"

    arrow=value._add_node("arrow_new",{"target":"arrow1"},False);curve=value._add_node("arrow_set_curve",{"target":"arrow1"},False);inspector=open_inspector_real(value,curve);control=inspector.editors["cx1"][0]
    assert isinstance(control,QDoubleSpinBox);control.setFocus();QTest.keyClick(control,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier);QTest.keyClicks(control,"73.5");QTest.keyClick(control,Qt.Key.Key_Return);QApplication.processEvents();assert inspector.editors["cx1"][0] is control

    saved=tmp_path/"parameter-controls.cmm";value.session.save(str(saved));value.load(saved)
    reopened={item["id"]:item for item in value.session.project()["nodes"]};assert reopened[position]["params"]["x"]==42.5 and reopened[position]["params"]["frames"]==18
    assert reopened[color]["params"]["r"]==64 and reopened[layer]["params"]["value"]==3
    assert reopened[text_node]["params"]["value"]=="N" and reopened[raw]["params"]["code"]=="-- edited once" and reopened[curve]["params"]["cx1"]==73.5
    value.close()


def test_gradient_creation_dialog_uses_core_living_targets_and_selected_molecule():
    value=window();first=value.session.import_smiles("first","c1ccccc1");second=value.session.import_smiles("second","O=[N+]=O")
    last=value.session.project()["nodes"][-1]["id"];value.refresh_all(last);value._node_selected(last)
    observed=[]
    def accept_dialog():
        dialog=next(widget for widget in QApplication.topLevelWidgets() if isinstance(widget,GradientStructureDialog) and widget.isVisible())
        observed.extend(dialog.target.itemData(index) for index in range(dialog.target.count()))
        index=dialog.target.findData(first);assert index>=0
        dialog.target.setFocus();dialog.target.setCurrentIndex(index)
        QTest.mouseClick(dialog.buttons.button(QDialogButtonBox.StandardButton.Ok),Qt.MouseButton.LeftButton)
    QTimer.singleShot(0,accept_dialog)
    node_id=value._add_node("molecule_gradient_structure")
    node=next(item for item in value.session.project()["nodes"] if item["id"]==node_id)
    assert first in observed and second in observed
    assert node["params"]["target"]==first and node["params"]["start_snapshot"]["id"]==first
    assert value.session.active_molecule==first
    value.close()


def test_gradient_creation_dialog_can_atomically_merge_two_living_molecules():
    value=window();first=value.session.import_smiles("first","c1ccccc1");second=value.session.import_smiles("second","O=[N+]=O")
    last=value.session.project()["nodes"][-1]["id"];value.refresh_all(last);value._node_selected(last)
    def accept_dialog():
        dialog=next(widget for widget in QApplication.topLevelWidgets() if isinstance(widget,GradientStructureDialog) and widget.isVisible())
        dialog.target.setCurrentIndex(dialog.target.findData(first));dialog.merge.setChecked(True)
        dialog.source.setCurrentIndex(dialog.source.findData(second))
        QTest.mouseClick(dialog.buttons.button(QDialogButtonBox.StandardButton.Ok),Qt.MouseButton.LeftButton)
    before=len(value.session.project()["nodes"]);QTimer.singleShot(0,accept_dialog);gradient=value._add_node("molecule_gradient_structure")
    created=value.session.project()["nodes"][before:]
    assert [item["type"] for item in created]==["molecule_create","merge_molecules","molecule_gradient_structure"]
    assert created[-1]["id"]==gradient and value.session.edit_target_id==gradient and value.session.can_edit_structure
    value.undo();assert len(value.session.project()["nodes"])==before
    value.close()


def test_real_double_click_selects_start_component_and_drag_shows_chemical_snap():
    value=window();ring=value.session.import_smiles("ring","c1ccccc1");nitro=value.session.import_smiles("nitro","O=[N+]=O")
    value.session.add_node("molecule_set_position",json.dumps({"target":nitro,"x":120.0,"y":0.0}))
    gradient=value.session.create_merged_gradient(ring,nitro,30,"linear");value.refresh_all(gradient);value._node_selected(gradient);value._set_tool("move");value.canvas._sync_core_viewport()
    project=value.session.project();merge=next(item for item in project["nodes"] if item["type"]=="merge_molecules" and item.get("params",{}).get("output")==value.session.active_molecule)
    source_ids=set(merge["params"]["id_map"]["source"]["atoms"].values());target_ids=set(merge["params"]["id_map"]["target"]["atoms"].values())
    end=next(item for item in project["nodes"] if item["id"]==gradient)["params"]["end_snapshot"]
    nitrogen=next(atom["id"] for atom in end["atoms"] if atom["id"] in source_ids and (atom.get("label") or atom.get("element"))=="N")
    points={item["id"]:item["center"] for item in value.session.depict(False)["atoms"]};pivot=QPoint(round(points[nitrogen]["x"]),round(points[nitrogen]["y"]));stationary_id=next(iter(target_ids));stationary=points[stationary_id]
    QTest.mouseDClick(value.canvas,Qt.MouseButton.LeftButton,pos=pivot);QApplication.processEvents();assert set(value.canvas._selected_atoms)==source_ids
    destination=QPoint(round(stationary["x"]+32),round(stationary["y"]))
    QTest.mousePress(value.canvas,Qt.MouseButton.LeftButton,pos=pivot);QTest.mouseMove(value.canvas,destination,80);QApplication.processEvents()
    assert value.canvas._preview.get("snap_atom") in target_ids and value.canvas._preview.get("text","").startswith("1.00×")
    QTest.mouseRelease(value.canvas,Qt.MouseButton.LeftButton,pos=destination);QApplication.processEvents()
    assert value.session.gradient_summary(gradient)["moved_atoms"]==len(source_ids)
    value.close()


def test_parameter_panel_native_crash_probe_exits_cleanly():
    run=subprocess.run([sys.executable,"-X","faulthandler","-u",str(ROOT/"tools"/"probe_parameter_panel.py")],cwd=ROOT,capture_output=True,text=True,timeout=30)
    assert run.returncode==0,(run.returncode,run.stdout,run.stderr)
    assert '"checkpoint": "alpha-committed"' in run.stdout and '"stored": 0' in run.stdout and '"checkpoint": "normal-exit"' in run.stdout


def test_arrow_curve_real_ui_free_drag_then_all_four_handles_remain_editable():
    value=window();arrow=value._add_node("arrow_new",{"target":"arrow1"},False)
    curve=value._add_node("arrow_set_curve",{"target":"arrow1"},False);canvas=value.canvas;canvas._sync_core_viewport()
    params=next(item for item in value.session.project()["nodes"] if item["id"]==curve)["params"]
    assert params["initialized"] is False and value.session.direct_controls()==[]
    start=QPoint(canvas.width()//2-130,canvas.height()//2+55);end=QPoint(canvas.width()//2+150,canvas.height()//2-75)
    QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=start);QTest.mouseMove(canvas,end,100)
    before_bend=next(item for item in value.session.project()["nodes"] if item["id"]==curve)["params"].copy()
    wheel=QWheelEvent(QPointF(end),QPointF(canvas.mapToGlobal(end)),QPoint(),QPoint(0,120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.ScrollUpdate,False)
    canvas.wheelEvent(wheel);QApplication.processEvents()
    during_bend=next(item for item in value.session.project()["nodes"] if item["id"]==curve)["params"].copy()
    assert (during_bend["cx1"],during_bend["cy1"],during_bend["cx2"],during_bend["cy2"])!=(before_bend["cx1"],before_bend["cy1"],before_bend["cx2"],before_bend["cy2"])
    QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=end);QApplication.processEvents()
    params=next(item for item in value.session.project()["nodes"] if item["id"]==curve)["params"]
    assert params["initialized"] is True
    controls={item["id"]:item["position"] for item in value.session.direct_controls()};assert set(controls)=={"p0","c1","c2","p3"}
    assert abs(params["x1"]-canvas.screen_to_world(QPointF(start)).x())<1.0
    assert abs(params["y1"]-canvas.screen_to_world(QPointF(start)).y())<1.0
    original=dict(params);scale_before=canvas.view_scale
    wheel=QWheelEvent(QPointF(end),QPointF(canvas.mapToGlobal(end)),QPoint(),QPoint(0,120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.ScrollUpdate,False)
    canvas.wheelEvent(wheel);QApplication.processEvents();after_wheel=next(item for item in value.session.project()["nodes"] if item["id"]==curve)["params"]
    assert after_wheel==original and canvas.view_scale>scale_before
    for key,delta in (("p0",QPoint(12,8)),("c1",QPoint(-10,14)),("c2",QPoint(15,-11)),("p3",QPoint(-8,-13))):
        controls={item["id"]:item["position"] for item in value.session.direct_controls()};world=controls[key]
        screen=canvas.world_to_screen(QPointF(world["x"],world["y"]));a=QPoint(round(screen.x()),round(screen.y()));b=a+delta
        QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=a);QTest.mouseMove(canvas,b,60);QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=b);QApplication.processEvents()
    changed=next(item for item in value.session.project()["nodes"] if item["id"]==curve)["params"]
    assert any(abs(changed[key]-original[key])>1 for key in ("x1","y1","cx1","cy1","cx2","cy2","x2","y2"))
    value._edit_node_dialog(curve);QApplication.processEvents()
    assert value.inspector_panel.isVisible() and all(key in value.inspector.editors for key in ("x1","y1","cx1","cy1","cx2","cy2","x2","y2"))
    value.close()


def test_real_click_default_bond_is_thirty_degrees_and_ring_is_point_up():
    value=window();enable_structure(value);panel=value.mode_panel;panel.set_mode("绘制");QApplication.processEvents();canvas=value.canvas
    buttons={button.property("drawKind"):button for button in panel.tertiary.findChildren(QToolButton) if button.property("drawKind")}
    center=QPoint(canvas.width()//2,canvas.height()//2)
    buttons["single_bond"].click();QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=center);QApplication.processEvents()
    snapshot=active_structure(value);a,b=(snapshot["atoms"][0],snapshot["atoms"][1]);import math
    assert abs(math.degrees(math.atan2(b["y"]-a["y"],b["x"]-a["x"]))-30)<1e-6
    value.undo();buttons["ring6"].click();QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=center);QApplication.processEvents()
    atoms=[atom for atom in active_structure(value)["atoms"] if atom.get("alive",True)];xs=[atom["x"] for atom in atoms];ys=[atom["y"] for atom in atoms]
    top=[atom for atom in atoms if abs(atom["y"]-max(ys))<1e-6];bottom=[atom for atom in atoms if abs(atom["y"]-min(ys))<1e-6]
    assert len(top)==len(bottom)==1 and abs(top[0]["x"]-bottom[0]["x"])<1e-6
    value.close()
    value.close()


def test_scrub_play_stop_and_node_return_keep_ui_and_core_state_in_sync():
    value=window();create=next(node for node in value.session.project()["nodes"] if node["type"]=="molecule_create")
    wait=value._add_node("wait",{"frames":8},open_editor=False)
    assert value.session.edit_target_id==wait and value.edit_mode.text()=="编辑节点：等待"

    value.frame_spin.setValue(3);QApplication.processEvents()
    assert value.session.edit_target_kind=="timeline_preview" and value.session.preview_frame==3
    assert value.edit_mode.text()=="预览：只读" and not value.mode_panel._structure_enabled

    value.node_list.refresh(create["id"]);value._node_selected(create["id"])
    assert value.session.edit_target_kind=="script_node" and value.edit_mode.text()=="编辑节点：新建分子" and not value.session.can_edit_structure
    value._toggle_play();assert value._playing and value.session.edit_target_kind=="timeline_preview" and value.edit_mode.text()=="播放：只读预览"
    value._toggle_play();assert not value._playing and value.session.edit_target_kind=="script_node" and value.node_list.current_id()==create["id"]

    value.actions["final"].setChecked(True);value._toggle_final_effect(True)
    assert value.canvas.final_effect and value.session.edit_target_kind=="timeline_preview" and value.edit_mode.text()=="最终效果：只读预览"
    value.actions["final"].setChecked(False);value._toggle_final_effect(False)
    assert not value.canvas.final_effect and value.session.edit_target_kind=="script_node"
    value.close()


def test_adding_one_node_is_one_undo_step_and_returns_to_valid_context():
    value=window();before=[node["id"] for node in value.session.project()["nodes"]]
    created=value._add_node("wait",{"frames":17},open_editor=False)
    assert created and len(value.session.project()["nodes"])==len(before)+1
    value.undo();assert [node["id"] for node in value.session.project()["nodes"]]==before
    assert value.session.edit_target_kind=="script_node"
    value.redo();assert any(node["id"]==created for node in value.session.project()["nodes"])
    value.close()
