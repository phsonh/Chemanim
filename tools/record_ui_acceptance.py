from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from chemanim2d.app import MainWindow
from chemanim2d.core import BUILD_COMMIT


def main():
    def milestone(value): print(value,flush=True)
    application=QApplication(sys.argv);application.setStyle("Fusion");application.setQuitOnLastWindowClosed(False)
    window=MainWindow(ROOT);window.resize(1580,960);window.show();QTest.qWait(250);window.canvas.fit_artboard();QTest.qWait(120)
    directory=ROOT/"media"/"ui_acceptance";directory.mkdir(parents=True,exist_ok=True)
    for old in directory.glob("frame-*.png"):old.unlink()
    frames=[]
    def capture(hold=4):
        application.processEvents();path=directory/f"frame-{len(frames):04d}.png";window.grab().save(str(path));frames.append(path)
        for _ in range(hold-1):
            duplicate=directory/f"frame-{len(frames):04d}.png";window.grab().save(str(duplicate));frames.append(duplicate)

    capture(8);milestone("initial")
    document=window.session.project();document["mod"]="ui_acceptance";window.session.replace_json(json.dumps(document));window.refresh_all()
    scene=window.session.project()["scene"];scene.update({"width":1080,"height":1920,"logic_width":540,"logic_height":960,"background":"E8EEF6FF","title":"ui_acceptance"});window.session.update_scene(json.dumps(scene));window.scene_inspector.refresh();window.canvas.fit_artboard();capture(10);milestone("scene")

    canvas=window.canvas
    start=QPoint(canvas.width()//2,canvas.height()//2);end=start+QPoint(85,45)
    QTest.mousePress(canvas,Qt.MouseButton.MiddleButton,Qt.KeyboardModifier.NoModifier,start);QTest.mouseMove(canvas,end,80);capture(3);QTest.mouseRelease(canvas,Qt.MouseButton.MiddleButton,Qt.KeyboardModifier.NoModifier,end);capture(5);milestone("pan")
    mouse=QPointF(canvas.width()*.62,canvas.height()*.38)
    for _ in range(5):
        wheel=QWheelEvent(mouse,QPointF(canvas.mapToGlobal(mouse.toPoint())),QPoint(),QPoint(0,120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.ScrollUpdate,False);canvas.wheelEvent(wheel)
    capture(7);milestone("zoom")

    window.mode_panel.set_mode("绘制");window.mode_panel.set_category("结构");window._set_tool("benzene");canvas.fit_artboard();QTest.qWait(80)
    center=QPoint(canvas.width()//2,canvas.height()//2);QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,center);QTest.qWait(100);capture(8);milestone("benzene")
    window._set_tool("single_bond")
    for atom in window.session.depict(False)["atoms"][:3]:
        point=QPoint(round(atom["center"]["x"]),round(atom["center"]["y"]));QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,point);QTest.qWait(80);capture(4)
    milestone("substituents")

    window.mode_panel.set_category("工具");window._set_tool("select_rectangle");depiction=window.session.depict(False);centers=[item["center"] for item in depiction["atoms"]];left=min(item["x"] for item in centers)-18;right=max(item["x"] for item in centers)+18;top=min(item["y"] for item in centers)-18;bottom=max(item["y"] for item in centers)+18
    first=QPoint(round(right),round(bottom));last=QPoint(round(left),round(top));QTest.mousePress(canvas,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,first);QTest.mouseMove(canvas,last,100);capture(5);QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,last);capture(5)
    atom_point=window.session.depict(False)["atoms"][0]["center"];first=QPoint(round(atom_point["x"]),round(atom_point["y"]));last=first+QPoint(45,-28);QTest.mousePress(canvas,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,first);QTest.mouseMove(canvas,last,100);capture(4);QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,Qt.KeyboardModifier.NoModifier,last);capture(7);milestone("select-move")

    window.mode_panel.set_mode("脚本");window.mode_panel.set_category("通用");window._add_node("wait");wait_id=window.node_list.current_id();capture(5);milestone("wait")
    window.mode_panel.set_category("分子");window._add_node("molecule_lerp_position");move_id=window.node_list.current_id();move=next(item for item in window.session.project()["nodes"] if item["id"]==move_id);params=move["params"]|{"x":360,"y":0,"frames":30,"easing":"linear"};window.session.update_node(move_id,json.dumps(params));window.refresh_all(move_id);capture(6)
    if canvas.selected_atoms:
        window._add_node("atom_lerp_xy");capture(5)
    window.mode_panel.set_category("箭头");window._add_node("arrow_new");window._add_node("arrow_set_curve");window._add_node("arrow_lerp_progress");capture(7);milestone("arrows")
    window.node_list.refresh(wait_id);window.node_list.move(1);capture(6);milestone("reorder")
    window._set_frame(window.session.end_frame);capture(8)

    save_path=ROOT/"mod"/"ui_acceptance"/"ui_acceptance.cmm";save_path.parent.mkdir(parents=True,exist_ok=True);window.session.save(str(save_path));window.path=save_path;window.dirty=False;window.refresh_all();capture(5);window.load(save_path);capture(8)
    window.actions["final"].setChecked(True);canvas.set_final_effect(True);capture(10)

    import imageio_ffmpeg
    output=directory/f"ui-acceptance-{BUILD_COMMIT[:12]}.mp4"
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();subprocess.run([ffmpeg,"-y","-framerate","12","-i",str(directory/"frame-%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(output)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print(json.dumps({"core":BUILD_COMMIT,"frames":len(frames),"video":str(output),"project":str(save_path)},ensure_ascii=False));window.close()


if __name__=="__main__":main()
