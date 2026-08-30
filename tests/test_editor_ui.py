from __future__ import annotations

import json
from pathlib import Path
import sys

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QToolBar, QToolButton

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
    atom=value.session.project()["molecules"][0]["atoms"][0];assert atom["element"]=="C" and atom["label"]=="O"
    buttons={button.text():button for button in value.mode_panel.tertiary.findChildren(QToolButton)}
    buttons["N"].click();point=next(item["center"] for item in value.session.depict(False)["atoms"] if item["id"]==atom["id"])
    value.session.pointer_down(point["x"],point["y"]);value.session.pointer_up(point["x"],point["y"])
    atoms=value.session.project()["molecules"][0]["atoms"]
    assert len(atoms)==1 and atoms[0]["alive"] and atoms[0]["element"]=="C" and atoms[0]["label"]=="N"
    assert value.session.depict(False)["svg"]
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
    value=window();value.mode_panel.set_mode("绘制");value.mode_panel.set_category("元素")
    value._set_element("Xe")
    assert value.mode_panel.recent_elements==["Xe","C","N","O","H","S","P","F","Cl","Br"]
    QApplication.processEvents()
    buttons=[button.text() for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible() and button.property("drawKind") is None and button.property("textNumberStyle") is None and button.text()!="周期表…"]
    assert buttons==value.mode_panel.recent_elements and len(buttons)==10
    value.close()


def test_script_tools_are_text_only_and_molecule_arrow_use_scope_tabs():
    value=window();value.mode_panel.set_mode("脚本");value.mode_panel.set_category("分子")
    assert [value.mode_panel.scope_tabs.tabText(i) for i in range(value.mode_panel.scope_tabs.count())]==["对象","全局","设定","变换"]
    for scope in ("对象","全局","设定","变换"):
        value.mode_panel.set_script_scope(scope);QApplication.processEvents()
        buttons=[button for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible()]
        assert buttons and all(button.icon().isNull() for button in buttons)
    value.mode_panel.set_category("箭头");assert value.mode_panel.scope_row.isVisible()
    value.close()


def test_primary_node_toolbar_is_registry_driven_and_has_exact_object_commands():
    value=window();value.mode_panel.set_mode("脚本");value.mode_panel.set_category("分子")
    value.mode_panel.set_script_scope("对象");QApplication.processEvents()
    assert [button.text() for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible()]==["新建分子","删除分子","合并分子"]
    value.mode_panel.set_category("箭头");value.mode_panel.set_script_scope("对象");QApplication.processEvents()
    assert [button.text() for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible()]==["新建箭头","删除箭头"]
    value.close()


def test_primary_node_toolbar_uses_exact_section_menus_and_short_action_names():
    value=window();panel=value.mode_panel;panel.set_mode("脚本");panel.set_category("分子")
    def visible_menus(scope):
        panel.set_script_scope(scope);QApplication.processEvents()
        return {button.text():[action.text() for action in button.menu().actions()]
                for button in panel.tertiary.findChildren(QToolButton) if button.isVisible() and button.menu()}
    assert visible_menus("全局")=={"颜色":["透明度","颜色"],"缩放":["缩放","横向缩放","纵向缩放"]}
    assert visible_menus("设定")=={"结构":["分子结构"],"位置":["坐标","横坐标","纵坐标"],"缩放":["缩放","横向缩放","纵向缩放"],"旋转":["旋转角度"],"颜色":["透明度","颜色"],"排列":["图层"]}
    assert visible_menus("变换")["结构"]==["结构形变","成键","断键","选区显现","选区消失"]
    panel.set_category("箭头")
    assert visible_menus("设定")=={"曲线":["箭头曲线"],"绘制":["绘制进度"],"缩放":["缩放","横向缩放","纵向缩放"],"颜色":["透明度","颜色"],"线条":["线宽"]}
    assert "位置" not in visible_menus("设定") and "位置" not in visible_menus("变换")
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
    value=window();value.mode_panel.set_mode("绘制")
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
    value=window();canvas=value.canvas;canvas.setFocus();canvas._sync_core_viewport();value._set_tool("atom_label")
    center=(canvas.width()*.5,canvas.height()*.5);value.session.pointer_down(*center);value.session.pointer_up(*center);value.refresh_all()
    assert len(value.session.project()["molecules"][0]["atoms"])==1
    QTest.keyClick(canvas,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier);assert not value.session.project()["molecules"][0]["atoms"]
    QTest.keyClick(canvas,Qt.Key.Key_Y,Qt.KeyboardModifier.ControlModifier);assert len(value.session.project()["molecules"][0]["atoms"])==1
    atom=value.session.project()["molecules"][0]["atoms"][0];value._set_tool("select_rectangle");point=next(item["center"] for item in value.session.depict(False)["atoms"] if item["id"]==atom["id"])
    value.session.pointer_down(point["x"],point["y"]);value.session.pointer_up(point["x"],point["y"]);canvas.setFocus();QTest.keyClick(canvas,Qt.Key.Key_Delete)
    assert not value.session.project()["molecules"][0]["atoms"][0]["alive"]
    value.close()


def test_canvas_control_a_selects_all_alive_structure():
    value=window();canvas=value.canvas;canvas.setFocus();canvas._sync_core_viewport();value._set_tool("ring5")
    center=(canvas.width()*.5,canvas.height()*.5);value.session.pointer_down(*center);value.session.pointer_up(*center);value.refresh_all()
    QTest.keyClick(canvas,Qt.Key.Key_A,Qt.KeyboardModifier.ControlModifier)
    molecule=value.session.project()["molecules"][0]
    assert set(canvas.selected_atoms)=={atom["id"] for atom in molecule["atoms"] if atom["alive"]}
    assert set(canvas.selected_bonds)=={bond["id"] for bond in molecule["bonds"] if bond["alive"]}
    value.close()


def test_canvas_control_drag_rect_selects_without_leaving_current_draw_tool():
    value=window();canvas=value.canvas;canvas._sync_core_viewport();value._set_tool("ring5")
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


def test_structure_toolbar_requires_selected_creation_node_and_keeps_selection():
    value=window();create=next(node for node in value.session.project()["nodes"] if node["type"]=="molecule_create")
    assert value.node_list.current_id()==create["id"] and value.session.can_edit_structure
    value.mode_panel.set_mode("绘制");QApplication.processEvents()
    buttons={button.property("drawKind"):button for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.property("drawKind")}
    assert buttons["single_bond"].isEnabled()
    value._set_tool("single_bond");assert value.node_list.current_id()==create["id"]

    wait=value._add_node("wait",open_editor=False);assert value.node_list.current_id()==wait
    assert value.session.edit_target_kind=="script_node" and not value.session.can_edit_structure
    value.mode_panel.set_mode("绘制");QApplication.processEvents()
    buttons={button.property("drawKind"):button for button in value.mode_panel.tertiary.findChildren(QToolButton) if button.property("drawKind")}
    assert not buttons["single_bond"].isEnabled() and buttons["select_rectangle"].isEnabled()
    old_tool=value.session.tool;value._set_tool("single_bond")
    assert value.session.tool==old_tool and value.node_list.current_id()==wait
    value.close()


def test_scrub_play_stop_and_node_return_keep_ui_and_core_state_in_sync():
    value=window();create=next(node for node in value.session.project()["nodes"] if node["type"]=="molecule_create")
    wait=value._add_node("wait",{"frames":8},open_editor=False)
    assert value.session.edit_target_id==wait and value.edit_mode.text().startswith("编辑节点")

    value.frame_spin.setValue(3);QApplication.processEvents()
    assert value.session.edit_target_kind=="timeline_preview" and value.session.preview_frame==3
    assert value.edit_mode.text()=="预览：只读" and not value.mode_panel._structure_enabled

    value.node_list.refresh(create["id"]);value._node_selected(create["id"])
    assert value.session.edit_target_kind=="base_structure" and value.edit_mode.text()=="编辑：基础结构节点"
    value._toggle_play();assert value._playing and value.session.edit_target_kind=="timeline_preview" and value.edit_mode.text()=="播放：只读预览"
    value._toggle_play();assert not value._playing and value.session.edit_target_kind=="base_structure" and value.node_list.current_id()==create["id"]

    value.actions["final"].setChecked(True);value._toggle_final_effect(True)
    assert value.canvas.final_effect and value.session.edit_target_kind=="timeline_preview" and value.edit_mode.text()=="最终效果：只读预览"
    value.actions["final"].setChecked(False);value._toggle_final_effect(False)
    assert not value.canvas.final_effect and value.session.edit_target_kind=="base_structure"
    value.close()


def test_adding_one_node_is_one_undo_step_and_returns_to_valid_context():
    value=window();before=[node["id"] for node in value.session.project()["nodes"]]
    created=value._add_node("wait",{"frames":17},open_editor=False)
    assert created and len(value.session.project()["nodes"])==len(before)+1
    value.undo();assert [node["id"] for node in value.session.project()["nodes"]]==before
    assert value.session.edit_target_kind in ("base_structure","script_node")
    value.redo();assert any(node["id"]==created for node in value.session.project()["nodes"])
    value.close()
