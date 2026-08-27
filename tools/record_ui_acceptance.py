from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))

from PyQt6.QtCore import QPoint,QPointF,QTimer,Qt
from PyQt6.QtGui import QWheelEvent
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication,QDialog,QMenu,QToolButton

from chemanim2d.app import MainWindow
from chemanim2d.core import BUILD_COMMIT


def main():
    app=QApplication(sys.argv);app.setStyle("Fusion");app.setQuitOnLastWindowClosed(False)
    window=MainWindow(ROOT);window.resize(1720,1040);window.show();QTest.qWait(300)
    canvas=window.canvas;canvas.fit_artboard();QTest.qWait(120)
    output=ROOT/"media"/"ui_acceptance_v5";output.mkdir(parents=True,exist_ok=True)
    for old in output.glob("frame-*.png"):old.unlink()
    frames=[];milestones=[]
    def capture(name,hold=4):
        app.processEvents();milestones.append((name,len(frames)))
        for _ in range(hold):
            path=output/f"frame-{len(frames):04d}.png";window.grab().save(str(path));frames.append(path)

    project=window.session.project();project["mod"]="ui_acceptance_v5";project["scene"].update({"background":"F4F1EAFF","title":"ui_acceptance_v5"});window.session.replace_json(json.dumps(project));window.refresh_all();canvas.fit_artboard();capture("干净布局")

    # Real keyboard dispatch plus bond-order cycling and hetero-label clipping.
    window.mode_panel.set_mode("绘制");window.mode_panel.set_category("结构");window._set_tool("single_bond")
    first=QPoint(canvas.width()//2,canvas.height()//2+70);second=first+QPoint(0,-90)
    QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=first);QTest.mouseMove(canvas,second,80);QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=second);QTest.qWait(80)
    endpoint=window.session.project()["molecules"][0]["atoms"][-1];p=next(item["center"] for item in window.session.depict(False)["atoms"] if item["id"]==endpoint["id"])
    window.mode_panel.set_category("元素");buttons={button.text():button for button in window.mode_panel.tertiary.findChildren(QToolButton)};buttons["O"].click();QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=QPoint(round(p["x"]),round(p["y"])));QTest.qWait(80)
    assert window.session.project()["molecules"][0]["atoms"][-1]["element"]=="O"
    window.mode_panel.set_category("结构");window._set_tool("single_bond");bond=window.session.depict(False)["bonds"][0];mid=QPoint(round((bond["first"]["x"]+bond["second"]["x"])/2),round((bond["first"]["y"]+bond["second"]["y"])/2));QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=mid);QTest.qWait(80)
    assert window.session.project()["molecules"][0]["bonds"][0]["type"]=="double";capture("单键重复点击变双键且 O 标签裁切")
    canvas.setFocus();QTest.keyClick(canvas,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier);assert window.session.project()["molecules"][0]["bonds"][0]["type"]=="single"
    QTest.keyClick(canvas,Qt.Key.Key_Y,Qt.KeyboardModifier.ControlModifier);assert window.session.project()["molecules"][0]["bonds"][0]["type"]=="double"
    QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=mid);assert window.session.project()["molecules"][0]["bonds"][0]["type"]=="triple"
    QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=mid);assert window.session.project()["molecules"][0]["bonds"][0]["type"]=="single"
    wait=window._add_node("wait",open_editor=False);window.node_list.tree.setFocus();QTest.keyClick(window.node_list.tree,Qt.Key.Key_D,Qt.KeyboardModifier.ControlModifier);assert len([node for node in window.session.project()["nodes"] if node["type"]=="wait"])==2
    QTest.keyClick(window.node_list.tree,Qt.Key.Key_Delete);QTest.keyClick(window.node_list.tree,Qt.Key.Key_Z,Qt.KeyboardModifier.ControlModifier);assert len([node for node in window.session.project()["nodes"] if node["type"]=="wait"])==2
    QTest.keyClick(window.node_list.tree,Qt.Key.Key_Y,Qt.KeyboardModifier.ControlModifier);assert len([node for node in window.session.project()["nodes"] if node["type"]=="wait"])==1;capture("节点和画布快捷键")

    # All structure operations below are real QTest mouse gestures on the PyQt canvas.
    window.new_project();project=window.session.project();project["mod"]="ui_acceptance_v5";project["scene"].update({"background":"F4F1EAFF","title":"ui_acceptance_v5"});window.session.replace_json(json.dumps(project));window.refresh_all();canvas.fit_artboard()
    window.mode_panel.set_mode("绘制");window.mode_panel.set_category("结构");window._set_tool("ring5")
    center=QPoint(canvas.width()//2,canvas.height()//2);QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=center);QTest.qWait(80)
    shared=window.session.depict(False)["bonds"][0];mid=QPoint(round((shared["first"]["x"]+shared["second"]["x"])/2),round((shared["first"]["y"]+shared["second"]["y"])/2))
    window._set_tool("ring8");QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=mid);QTest.qWait(100)
    assert len(window.session.project()["molecules"][0]["atoms"])==11
    capture("点击五元环键生成规则并八元环")

    window.new_project();project=window.session.project();project["mod"]="ui_acceptance_v5";project["scene"].update({"background":"F4F1EAFF","title":"ui_acceptance_v5"});window.session.replace_json(json.dumps(project));window.refresh_all();canvas.fit_artboard()
    window.mode_panel.set_mode("绘制");window.mode_panel.set_category("结构");window._set_tool("benzene")
    center=QPoint(canvas.width()//2,canvas.height()//2);QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=center);QTest.qWait(100)
    molecule=window.session.project()["molecules"][0];ring_atoms=list(molecule["atoms"]);original={b["id"]:(b["type"],b["secondary_line_side"]) for b in molecule["bonds"]};capture("显式单双键苯环")
    window._set_tool("single_bond")
    for atom in ring_atoms[:3]:
        p=next(x["center"] for x in window.session.depict(False)["atoms"] if x["id"]==atom["id"]);QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=QPoint(round(p["x"]),round(p["y"])));QTest.qWait(60)
    current={b["id"]:(b["type"],b["secondary_line_side"]) for b in window.session.project()["molecules"][0]["bonds"] if b["id"] in original};assert current==original
    capture("连续取代且副线不跳")

    substituted=window.session.project()["molecules"][0];ring_ids={value["id"] for value in ring_atoms}
    terminal=next(value for value in substituted["atoms"] if value["id"] not in ring_ids)
    terminal_point=next(x["center"] for x in window.session.depict(False)["atoms"] if x["id"]==terminal["id"])
    before_ids={value["id"] for value in substituted["atoms"]};window._set_tool("ring5")
    QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=QPoint(round(terminal_point["x"]),round(terminal_point["y"])));QTest.qWait(80)
    after=window.session.project()["molecules"][0];created=[value for value in after["atoms"] if value["id"] not in before_ids]
    assert len(created)==4
    ring=[terminal,*created];ring_center=(sum(value["x"] for value in ring)/5,sum(value["y"] for value in ring)/5)
    owner=next(value for value in ring_atoms if any(bond["alive"] and {bond["a"],bond["b"]}=={value["id"],terminal["id"]} for bond in after["bonds"]))
    existing=(owner["x"]-terminal["x"],owner["y"]-terminal["y"]);outward=(ring_center[0]-terminal["x"],ring_center[1]-terminal["y"])
    assert abs(existing[0]*outward[1]-existing[1]*outward[0])<1e-8 and existing[0]*outward[0]+existing[1]*outward[1]<0
    capture("终端原子上的环沿角平分线对称")

    window._set_tool("ring5");shared=window.session.depict(False)["bonds"][0];mid=QPoint(round((shared["first"]["x"]+shared["second"]["x"])/2),round((shared["first"]["y"]+shared["second"]["y"])/2));before_atoms=len(window.session.project()["molecules"][0]["atoms"]);QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=mid);QTest.qWait(80);assert len(window.session.project()["molecules"][0]["atoms"])==before_atoms+3;capture("点击键生成稠合五元环")
    window._set_tool("ring5");p=next(x["center"] for x in window.session.depict(False)["atoms"] if x["id"]==ring_atoms[4]["id"]);before_atoms=len(window.session.project()["molecules"][0]["atoms"]);QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=QPoint(round(p["x"]),round(p["y"])));QTest.qWait(80);assert len(window.session.project()["molecules"][0]["atoms"])==before_atoms+4;capture("点击原子生成对称螺环")

    window.mode_panel.set_category("结构");window._set_tool("charge_positive");anchor=ring_atoms[5]
    p=next(x["center"] for x in window.session.depict(False)["atoms"] if x["id"]==anchor["id"]);start=QPoint(round(p["x"]),round(p["y"]));end=start+QPoint(54,-24)
    QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=start);QTest.mouseMove(canvas,end,80);QTest.qWait(60);capture("形式电荷蓝色轮廓预览")
    QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=end);QTest.qWait(80);capture("带圈形式电荷")

    all_atoms=window.session.project()["molecules"][0]["atoms"];points=[]
    for atom in all_atoms[-3:]:
        value=next(x["center"] for x in window.session.depict(False)["atoms"] if x["id"]==atom["id"]);points.append(QPoint(round(value["x"]),round(value["y"])))
    window._set_tool("eraser");QTest.mousePress(canvas,Qt.MouseButton.LeftButton,pos=points[0])
    for point in points[1:]:QTest.mouseMove(canvas,point,60)
    QTest.mouseRelease(canvas,Qt.MouseButton.LeftButton,pos=points[-1]);capture("连续橡皮删除")
    window.undo();assert all(a["alive"] for a in window.session.project()["molecules"][0]["atoms"]);capture("一次撤销全部恢复")

    canvas.pan=QPointF(240,-150);mouse=QPointF(canvas.width()*.78,canvas.height()*.22)
    for _ in range(80):
        event=QWheelEvent(mouse,QPointF(canvas.mapToGlobal(mouse.toPoint())),QPoint(),QPoint(0,-120),Qt.MouseButton.NoButton,Qt.KeyboardModifier.NoModifier,Qt.ScrollPhase.ScrollUpdate,False);canvas.wheelEvent(event)
    assert canvas.pan==QPointF();capture("最小缩放自动居中");canvas.fit_artboard()

    def close_dialogs():
        for widget in QApplication.topLevelWidgets():
            if isinstance(widget,QDialog) and widget.isVisible():widget.reject()
    def context_action(position,path):
        error=[]
        def choose():
            menu=QApplication.activePopupWidget()
            try:
                for index,label in enumerate(path):
                    if not isinstance(menu,QMenu):raise RuntimeError(f"{label}: no menu")
                    action=next(a for a in menu.actions() if a.text()==label)
                    if index+1<len(path):menu=action.menu()
                    else:QTimer.singleShot(120,close_dialogs);action.trigger()
            except Exception as exc:
                error.append(f"{'/'.join(path)}: {type(exc).__name__}: {exc}")
                if isinstance(menu,QMenu):menu.close()
        QTimer.singleShot(80,choose);QTest.mouseClick(canvas,Qt.MouseButton.RightButton,pos=position);QTest.qWait(180)
        if error:raise RuntimeError(error[0])

    canvas.fit_artboard();QTest.qWait(80);drawing=window.session.depict(False);atom_p=drawing["atoms"][0]["center"];atom_p=QPoint(round(atom_p["x"]),round(atom_p["y"]));bond=drawing["bonds"][0];bond_p=QPoint(round((bond["first"]["x"]+bond["second"]["x"])/2),round((bond["first"]["y"]+bond["second"]["y"])/2))
    mol=window.session.project()["molecules"][0];ad=mol["adornments"][0];owner=next(a for a in mol["atoms"] if a["id"]==ad["atom"]);ad_p=canvas.world_to_screen(QPointF(owner["x"]+ad["x"],owner["y"]+ad["y"])).toPoint()
    actions=((atom_p,["分子","设定","坐标"]),(atom_p,["分子","插值","坐标"]),(atom_p,["原子","设定","透明度"]),(atom_p,["原子","插值","坐标"]),(bond_p,["键","设定","视觉键型"]),(bond_p,["键","插值","透明度"]),(ad_p,["形式电荷","设定","透明度"]),(ad_p,["形式电荷","插值","坐标"]))
    for position,path in actions:context_action(position,path)
    capture("右键 Set Lerp 进入左侧节点")

    scene=window.session.project()["scene"];scene.update({"width":1080,"height":1920,"logic_width":540,"logic_height":960,"background":"16243BFF"});window.session.update_scene(json.dumps(scene));canvas.fit_artboard();window.refresh_all(window.node_list.current_id());capture("竖屏场景和背景")
    save=ROOT/"mod"/"ui_acceptance_v5"/"ui_acceptance_v5.cmm";save.parent.mkdir(parents=True,exist_ok=True);window.session.save(str(save));before=json.loads(window.session.json());window.load(save);after=window.session.project();assert [n["id"] for n in before["nodes"]]==[n["id"] for n in after["nodes"]];capture("保存关闭重开")

    import imageio_ffmpeg
    video=output/f"ui-acceptance-{BUILD_COMMIT[:12]}.mp4";ffmpeg=imageio_ffmpeg.get_ffmpeg_exe();subprocess.run([ffmpeg,"-y","-framerate","10","-i",str(output/"frame-%04d.png"),"-c:v","libx264","-pix_fmt","yuv420p","-movflags","+faststart",str(video)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    report={"core":BUILD_COMMIT,"frames":len(frames),"video":str(video),"project":str(save),"milestones":milestones};(output/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False));window.close()


if __name__=="__main__":main()
