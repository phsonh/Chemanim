from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from PIL import Image, ImageChops, ImageStat

from chemanim2d.app import MainWindow
from chemanim2d.core import BUILD_COMMIT, DOCUMENT_VERSION, CoreSession


def capture(window: MainWindow, path: Path) -> None:
    window.canvas._refresh_now()
    QApplication.processEvents()
    if not window.grab().save(str(path)):
        raise RuntimeError(f"无法保存验收截图：{path}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    output = ROOT / "media" / "node_semantics_v7"
    output.mkdir(parents=True, exist_ok=True)

    window = MainWindow(ROOT)
    window.resize(1720, 1040)
    window.show()
    window.load(ROOT / "mod" / "visual_events" / "visual_events.cmm")
    window.canvas.fit_artboard()
    QTest.qWait(200)

    toolbar = {}
    for category in ("分子", "箭头"):
        window.mode_panel.set_mode("脚本")
        window.mode_panel.set_category(category)
        for scope in ("对象", "全局", "设定", "变换"):
            window.mode_panel.set_script_scope(scope)
            QTest.qWait(50)
            name = f"toolbar-{category}-{scope}.png"
            capture(window, output / name)
            toolbar[f"{category}/{scope}"] = name

    project = window.session.project()
    target = project["molecules"][0]["id"]
    create_index = next(index for index, node in enumerate(project["nodes"])
                        if node["type"] == "molecule_create" and node["params"]["target"] == target)
    insert = create_index + 1
    for node_type, params in (
        ("molecule_global_set_color", {"r": 210, "g": 235, "b": 255}),
        ("molecule_global_set_scale_x", {"value": 1.15}),
        ("molecule_global_set_scale_y", {"value": .85}),
        ("molecule_lerp_scale_x", {"target": target, "value": 1.8, "frames": 30, "easing": "linear"}),
        ("molecule_lerp_scale_y", {"target": target, "value": .65, "frames": 30, "easing": "linear"}),
    ):
        window.session.add_node(node_type, json.dumps(params, ensure_ascii=False), insert)
        insert += 1
    structure_node = window.session.add_node(
        "molecule_set_structure", json.dumps({"target": target, "snapshot": {}}), insert)
    window.session.edit_node(structure_node)
    window.session.set_tool("single_bond")
    anchor = window.session.depict(False)["atoms"][0]["center"]
    window.session.pointer_down(anchor["x"], anchor["y"])
    window.session.pointer_move(anchor["x"], anchor["y"] - 42)
    if not window.session.pointer_up(anchor["x"], anchor["y"] - 42)["changed"]:
        raise RuntimeError("结构快照端到端验收没有创建预期的新键")
    window.refresh_all()
    keyframes = {}
    for frame in (0, 15, 30):
        window.frame_spin.setValue(frame)
        QTest.qWait(80)
        name = f"global-local-frame-{frame:03d}.png"
        capture(window, output / name)
        keyframes[str(frame)] = {
            "image": name,
            "molecule": window.session.evaluated_molecules(frame)[target],
        }

    generated = window.session.generate_lua()
    (output / "generated-main.lua").write_text(generated, encoding="utf-8")
    scene = window.session.project()["scene"]
    entry = ROOT / "mod" / "visual_events" / "main.lua"
    original = entry.read_text(encoding="utf-8")
    comparisons = {}
    comparison_core = CoreSession()
    comparison_core.replace_json(window.session.json())
    comparison_core.set_viewport(scene["width"], scene["height"], 2.0, 0.0, 0.0)
    try:
        entry.write_text(generated, encoding="utf-8")
        for frame in (0, 15, 30):
            rendered = subprocess.run([str(ROOT / "build" / "release" / "chemanim.exe"),
                                       "visual_events", "--frame", str(frame), "--no-open"],
                                      cwd=ROOT, capture_output=True, text=True)
            if rendered.returncode:
                raise RuntimeError(f"最终引擎验收失败：\n{rendered.stdout}\n{rendered.stderr}")
            engine_source = ROOT / "media" / "visual_events" / f"visual_events_frame_{frame}.png"
            engine_path = output / f"engine-frame-{frame:03d}.png"
            shutil.copy2(engine_source, engine_path)
            core_path = output / f"core-frame-{frame:03d}.png"
            drawing = comparison_core.depict_at(frame, True)
            Image.frombytes("RGBA", (drawing["width"], drawing["height"]),
                            bytes(drawing["rgba"])).save(core_path)
            core_image = Image.open(core_path).convert("RGBA")
            engine_image = Image.open(engine_path).convert("RGBA")
            difference = ImageChops.difference(core_image, engine_image)
            diff_path = output / f"difference-frame-{frame:03d}.png"
            difference.save(diff_path)
            statistics = ImageStat.Stat(difference)
            comparisons[str(frame)] = {
                "core": core_path.name, "engine": engine_path.name,
                "difference": diff_path.name, "bbox": difference.getbbox(),
                "mean": statistics.mean, "rms": statistics.rms,
            }
    finally:
        entry.write_text(original, encoding="utf-8")

    report = {
        "core": BUILD_COMMIT,
        "document_version": DOCUMENT_VERSION,
        "project": "mod/visual_events/visual_events.cmm (in-memory acceptance edits)",
        "structure_snapshot_node": structure_node,
        "toolbar": toolbar,
        "keyframes": keyframes,
        "editor_engine_comparison": comparisons,
    }
    (output / "acceptance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    window.close()


if __name__ == "__main__":
    main()
