from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from PIL import Image, ImageChops, ImageStat
from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QToolButton

from chemanim2d.app import MainWindow
from chemanim2d.core import BUILD_COMMIT, CoreSession


def capture(window: MainWindow, path: Path) -> None:
    window.canvas._refresh_now();QApplication.processEvents();QTest.qWait(80)
    if not window.grab().save(str(path)):raise RuntimeError(f"无法保存截图：{path}")


def visible_tools(window: MainWindow):
    return [button for button in window.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible()]


def main() -> None:
    app=QApplication(sys.argv);app.setStyle("Fusion");app.setQuitOnLastWindowClosed(False)
    output=ROOT/"media"/"gradient_structure_v7";output.mkdir(parents=True,exist_ok=True)
    window=MainWindow(ROOT);window.resize(1800,1080);window.show();QTest.qWait(160)
    window.session.new_project();target=window.session.import_smiles("苯","c1ccccc1")
    window.refresh_all();window._select_default_authoring_node();window.canvas.fit_artboard();QTest.qWait(120)

    panel=window.mode_panel;panel.set_mode("脚本");panel.set_category("分子");panel.set_script_scope("变换");panel.set_script_section("结构");QApplication.processEvents()
    actions=visible_tools(window)
    if [button.text() for button in actions] != ["渐变结构"]:raise RuntimeError("分子/变换/结构没有唯一显示渐变结构")
    capture(window,output/"toolbar-four-visible-rows.png")
    QTest.mouseClick(actions[0],Qt.MouseButton.LeftButton);QApplication.processEvents()
    node=next(value for value in window.session.project()["nodes"] if value["type"]=="molecule_gradient_structure")
    if window.session.edit_target_kind!="structure_snapshot":raise RuntimeError("创建后没有进入终态编辑")

    panel.set_mode("绘制");QApplication.processEvents()
    draw={button.property("drawKind"):button for button in visible_tools(window) if button.property("drawKind")}
    QTest.mouseClick(draw["single_bond"],Qt.MouseButton.LeftButton);window.canvas._refresh_now();QApplication.processEvents()
    anchor=window.canvas._depiction["atoms"][0]["center"]
    start=QPoint(round(anchor["x"]),round(anchor["y"]));end=start+QPoint(52,0)
    QTest.mousePress(window.canvas,Qt.MouseButton.LeftButton,pos=start);QTest.mouseMove(window.canvas,end,90);QTest.mouseRelease(window.canvas,Qt.MouseButton.LeftButton,pos=end);QApplication.processEvents()
    endpoint=window.session.gradient_summary(node["id"])
    if endpoint["added_atoms"]!=1 or endpoint["added_bonds"]!=1:raise RuntimeError("实际画布手势没有添加一个原子和一根键")
    buttons={button.text():button for button in visible_tools(window) if not button.property("drawKind") and not button.property("textNumberStyle")}
    QTest.mouseClick(buttons["H"],Qt.MouseButton.LeftButton);window.canvas._refresh_now();QApplication.processEvents()
    params=next(value for value in window.session.project()["nodes"] if value["id"]==node["id"])["params"]
    start_ids={atom["id"] for atom in params["start_snapshot"]["atoms"]};new_id=next(atom["id"] for atom in params["end_snapshot"]["atoms"] if atom["id"] not in start_ids)
    atom=next(value["center"] for value in window.canvas._depiction["atoms"] if value["id"]==new_id)
    QTest.mouseClick(window.canvas,Qt.MouseButton.LeftButton,pos=QPoint(round(atom["x"]),round(atom["y"])));QApplication.processEvents()
    capture(window,output/"gradient-endpoint-edit.png")

    project_path=output/"benzene-explicit-h.cmm";window.path=project_path;window.save()
    saved_json=window.session.json();window.session.new_project();window.load(project_path)
    if window.session.json()!=saved_json:raise RuntimeError("保存关闭重开后工程发生变化")
    node=next(value for value in window.session.project()["nodes"] if value["type"]=="molecule_gradient_structure")
    window.node_list.refresh(node["id"]);window._node_selected(node["id"]);panel.set_mode("脚本");panel.set_category("分子");panel.set_script_scope("变换");panel.set_script_section("结构");window.canvas.request_refresh()
    keyframes={}
    for phase,frame in (("start",0),("current",15),("end",30)):
        if phase=="end":window._show_gradient_phase("end")
        else:window.frame_spin.setValue(frame)
        QTest.qWait(80);name=f"editor-{phase}-{frame:03d}.png";capture(window,output/name);keyframes[phase]=name

    generated=window.session.generate_lua();(output/"generated-main.lua").write_text(generated,encoding="utf-8")
    comparison=CoreSession();comparison.load(str(project_path));scene=comparison.project()["scene"];comparison.set_viewport(scene["width"],scene["height"],2.0,0.0,0.0)
    entry=ROOT/"mod"/"visual_events"/"main.lua";original=entry.read_text(encoding="utf-8");comparisons={}
    try:
        entry.write_text(generated,encoding="utf-8")
        for frame in (0,15,30):
            run=subprocess.run([str(ROOT/"build"/"release"/"chemanim.exe"),"visual_events","--frame",str(frame),"--no-open"],cwd=ROOT,capture_output=True,text=True)
            if run.returncode:raise RuntimeError(run.stdout+"\n"+run.stderr)
            engine_source=ROOT/"media"/"visual_events"/f"visual_events_frame_{frame}.png";engine_path=output/f"engine-{frame:03d}.png";shutil.copy2(engine_source,engine_path)
            drawing=comparison.depict_at(frame,True);core_path=output/f"core-{frame:03d}.png";Image.frombytes("RGBA",(drawing["width"],drawing["height"]),bytes(drawing["rgba"])).save(core_path)
            core_image=Image.open(core_path).convert("RGBA");engine_image=Image.open(engine_path).convert("RGBA");difference=ImageChops.difference(core_image,engine_image);diff_path=output/f"difference-{frame:03d}.png";difference.save(diff_path);statistics=ImageStat.Stat(difference)
            comparisons[str(frame)]={"bbox":difference.getbbox(),"mean":statistics.mean,"rms":statistics.rms,"core":core_path.name,"engine":engine_path.name,"difference":diff_path.name}
        before=set((ROOT/"media"/"visual_events").glob("visual_events_*.mp4"))
        run=subprocess.run([str(ROOT/"build"/"release"/"chemanim.exe"),"visual_events","--no-open"],cwd=ROOT,capture_output=True,text=True)
        if run.returncode:raise RuntimeError(run.stdout+"\n"+run.stderr)
        created=sorted(set((ROOT/"media"/"visual_events").glob("visual_events_*.mp4"))-before,key=lambda value:value.stat().st_mtime)
        if created:shutil.copy2(created[-1],output/"benzene-explicit-h.mp4")
    finally:entry.write_text(original,encoding="utf-8")
    report={"core":BUILD_COMMIT,"node_title":window.node_list.tree.currentItem().text(0),"summary":window.session.gradient_summary(node["id"]),"saved_reopened":True,"toolbar":"toolbar-four-visible-rows.png","endpoint":"gradient-endpoint-edit.png","keyframes":keyframes,"editor_engine_comparison":comparisons,"mp4":"benzene-explicit-h.mp4"}
    (output/"acceptance.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8");print(json.dumps(report,ensure_ascii=False))
    window.close()


if __name__=="__main__":main()
