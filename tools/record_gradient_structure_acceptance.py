from __future__ import annotations

import json
import math
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
    window.canvas._refresh_now()
    QApplication.processEvents()
    QTest.qWait(100)
    if not window.grab().save(str(path)):
        raise RuntimeError(f"无法保存截图：{path}")


def visible_tools(window: MainWindow):
    return [button for button in window.mode_panel.tertiary.findChildren(QToolButton) if button.isVisible()]


def stable_canvas(window: MainWindow) -> None:
    window.canvas._sync_core_viewport()
    window.canvas._refresh_now()
    QApplication.processEvents()
    QTest.qWait(50)


def click_atom(window: MainWindow, atom_id: str) -> None:
    """Exercise the real PyQt pure-click path, including hover and transaction signals."""
    stable_canvas(window)
    center = next(item["center"] for item in window.canvas._depiction["atoms"] if item["id"] == atom_id)
    point = QPoint(round(center["x"]), round(center["y"]))
    QTest.mouseMove(window.canvas, point, 60)
    QApplication.processEvents()
    hit = window.session.hit_test(point.x(), point.y())
    if hit.get("kind") != "atom" or hit.get("id") != atom_id:
        raise RuntimeError(f"真实画布未命中目标原子：期望 {atom_id}，实际 {hit}")
    QTest.mouseClick(window.canvas, Qt.MouseButton.LeftButton, pos=point)
    QApplication.processEvents()
    QTest.qWait(60)


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    output = ROOT / "media" / "gradient_structure_local_v1"
    output.mkdir(parents=True, exist_ok=True)

    window = MainWindow(ROOT)
    window.resize(1800, 1080)
    window.show()
    QTest.qWait(200)
    window.session.new_project()
    target = window.session.import_smiles("苯", "c1ccccc1")
    window.refresh_all()
    window._select_default_authoring_node()
    window.canvas.fit_artboard()
    QTest.qWait(150)

    # Reproduce the user's real upstream chain before creating the gradient.
    window._add_node("molecule_set_position", {"target": target, "x": 30.0, "y": -20.0}, False)
    window._add_node("molecule_set_scale", {"target": target, "value": 0.55}, False)
    window._add_node("molecule_lerp_scale", {"target": target, "value": 0.2, "frames": 12, "easing": "linear"}, False)
    window._add_node("molecule_lerp_alpha", {"target": target, "value": 190, "frames": 8, "easing": "linear"}, False)
    window._add_node("wait", {"frames": 14}, False)

    panel = window.mode_panel
    panel.set_mode("脚本")
    panel.set_category("分子")
    panel.set_script_scope("变换")
    panel.set_script_section("结构")
    QApplication.processEvents()
    actions = visible_tools(window)
    if [button.text() for button in actions] != ["渐变结构"]:
        raise RuntimeError("分子/变换/结构没有唯一显示渐变结构")
    capture(window, output / "toolbar-four-visible-rows.png")
    QTest.mouseClick(actions[0], Qt.MouseButton.LeftButton)
    QApplication.processEvents()
    node = next(value for value in window.session.project()["nodes"] if value["type"] == "molecule_gradient_structure")
    node_id = node["id"]
    if window.session.edit_target_kind != "structure_snapshot":
        raise RuntimeError("创建后没有进入终态编辑")
    params = node["params"]
    if params.get("coordinate_space") != "molecule_local_v1":
        raise RuntimeError("渐变结构没有写入局部坐标空间标记")
    original_atoms = [atom["id"] for atom in params["start_snapshot"]["atoms"] if atom.get("alive", True)]
    original_bonds = {bond["id"] for bond in params["start_snapshot"]["bonds"] if bond.get("alive", True)}

    panel.set_mode("绘制")
    QApplication.processEvents()
    single = next(button for button in visible_tools(window) if button.property("drawKind") == "single_bond")
    # The toolbar is touched exactly once. Both methyl bonds are subsequent pure clicks.
    QTest.mouseClick(single, Qt.MouseButton.LeftButton)
    if window.session.tool != "single_bond" or not single.isChecked():
        raise RuntimeError("单键工具没有在 Core 与工具栏中同步激活")
    for atom_id in (original_atoms[0], original_atoms[2]):
        click_atom(window, atom_id)
        if window.session.tool != "single_bond" or not single.isChecked() or panel._active_draw_tool != window.session.tool:
            raise RuntimeError("一次画布提交后单键工具被重置或 UI/Core 状态分裂")

    stored = next(value for value in window.session.project()["nodes"] if value["id"] == node_id)["params"]
    start, end = stored["start_snapshot"], stored["end_snapshot"]
    start_atom_ids = {atom["id"] for atom in start["atoms"]}
    end_atoms = {atom["id"]: atom for atom in end["atoms"] if atom.get("alive", True)}
    added_atoms = [atom for atom in end_atoms.values() if atom["id"] not in start_atom_ids]
    added_bonds = [bond for bond in end["bonds"] if bond["id"] not in original_bonds and bond.get("alive", True)]
    if len(added_atoms) != 2 or len(added_bonds) != 2:
        raise RuntimeError("连续两次纯点击没有生成两个甲基")
    lengths = []
    ring_atoms = [atom for atom in start["atoms"] if atom.get("alive", True)]
    ring_center = (sum(atom["x"] for atom in ring_atoms) / len(ring_atoms), sum(atom["y"] for atom in ring_atoms) / len(ring_atoms))
    for bond in added_bonds:
        a, b = end_atoms[bond["a"]], end_atoms[bond["b"]]
        lengths.append(math.hypot(a["x"] - b["x"], a["y"] - b["y"]))
        attachment = a if a["id"] in start_atom_ids else b
        terminal = b if attachment is a else a
        outward = (attachment["x"] - ring_center[0], attachment["y"] - ring_center[1])
        direction = (terminal["x"] - attachment["x"], terminal["y"] - attachment["y"])
        if outward[0] * direction[0] + outward[1] * direction[1] <= 0:
            raise RuntimeError("新增键没有沿苯环顶点的外侧方向生成")
    reference = float(end["reference_bond_length"])
    if not all(math.isclose(length, reference, rel_tol=1e-6) for length in lengths):
        raise RuntimeError(f"新增键不是规范局部键长：{lengths}，reference={reference}")
    capture(window, output / "terminal-two-methyl-local-edit.png")

    project_path = output / "benzene-two-methyl-local-space.cmm"
    window.path = project_path
    window.save()
    saved_node_order = [item["id"] for item in window.session.project()["nodes"]]
    window.session.new_project()
    window.load(project_path)
    if [item["id"] for item in window.session.project()["nodes"]] != saved_node_order:
        raise RuntimeError("保存关闭重开后节点顺序或 ID 发生变化")
    reopened = next(value for value in window.session.project()["nodes"] if value["id"] == node_id)
    if reopened["params"]["end_snapshot"] != end:
        raise RuntimeError("保存重开后局部终态坐标发生变化")
    capture(window, output / "saved-reopened.png")

    end_frame = int(window.session.end_frame)
    start_frame = end_frame - int(reopened["params"]["frames"])
    middle_frame = start_frame + (end_frame - start_frame) // 2
    keyframes = {}
    # Leave endpoint editing: these are ordinary read-only timeline previews.
    window.canvas.view_scale = 6.0
    window.canvas.pan.setX(0.0)
    window.canvas.pan.setY(0.0)
    for phase, frame in (("start", start_frame), ("middle", middle_frame), ("end", end_frame)):
        window._preview_frame(frame)
        QTest.qWait(100)
        name = f"editor-{phase}-{frame:03d}.png"
        capture(window, output / name)
        keyframes[phase] = name

    generated = window.session.generate_lua()
    (output / "generated-main.lua").write_text(generated, encoding="utf-8")
    comparison = CoreSession()
    comparison.load(str(project_path))
    scene = comparison.project()["scene"]
    comparison.set_viewport(scene["width"], scene["height"], 2.0, 0.0, 0.0)
    entry = ROOT / "mod" / "visual_events" / "main.lua"
    original = entry.read_text(encoding="utf-8")
    comparisons = {}
    try:
        entry.write_text(generated, encoding="utf-8")
        for frame in (start_frame, middle_frame, end_frame):
            run = subprocess.run(
                [str(ROOT / "build" / "release" / "chemanim.exe"), "visual_events", "--frame", str(frame), "--no-open"],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
            )
            if run.returncode:
                raise RuntimeError(run.stdout + "\n" + run.stderr)
            engine_source = ROOT / "media" / "visual_events" / f"visual_events_frame_{frame}.png"
            engine_path = output / f"engine-{frame:03d}.png"
            shutil.copy2(engine_source, engine_path)
            drawing = comparison.depict_at(frame, True)
            core_path = output / f"core-{frame:03d}.png"
            Image.frombytes("RGBA", (drawing["width"], drawing["height"]), bytes(drawing["rgba"])).save(core_path)
            core_image = Image.open(core_path).convert("RGBA")
            engine_image = Image.open(engine_path).convert("RGBA")
            difference = ImageChops.difference(core_image, engine_image)
            diff_path = output / f"difference-{frame:03d}.png"
            difference.save(diff_path)
            statistics = ImageStat.Stat(difference)
            comparisons[str(frame)] = {
                "bbox": difference.getbbox(), "mean": statistics.mean, "rms": statistics.rms,
                "core": core_path.name, "engine": engine_path.name, "difference": diff_path.name,
            }
        before = set((ROOT / "media" / "visual_events").glob("visual_events_*.mp4"))
        run = subprocess.run(
            [str(ROOT / "build" / "release" / "chemanim.exe"), "visual_events", "--no-open"],
            cwd=ROOT, capture_output=True, text=True, timeout=180,
        )
        if run.returncode:
            raise RuntimeError(run.stdout + "\n" + run.stderr)
        created = sorted(set((ROOT / "media" / "visual_events").glob("visual_events_*.mp4")) - before, key=lambda value: value.stat().st_mtime)
        if not created:
            raise RuntimeError("最终引擎没有生成 MP4")
        shutil.copy2(created[-1], output / "benzene-two-methyl-local-space.mp4")
    finally:
        entry.write_text(original, encoding="utf-8")

    report = {
        "core": BUILD_COMMIT,
        "node_title": "渐变结构 · 苯",
        "coordinate_space": reopened["params"].get("coordinate_space"),
        "summary": window.session.gradient_summary(node_id),
        "single_tool_selected_once": True,
        "tool_after_each_commit": "single_bond",
        "local_reference_bond_length": reference,
        "local_added_bond_lengths": lengths,
        "saved_reopened": True,
        "frames": {"start": start_frame, "middle": middle_frame, "end": end_frame},
        "toolbar": "toolbar-four-visible-rows.png",
        "endpoint": "terminal-two-methyl-local-edit.png",
        "keyframes": keyframes,
        "editor_engine_comparison": comparisons,
        "mp4": "benzene-two-methyl-local-space.mp4",
    }
    (output / "acceptance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    window.close()


if __name__ == "__main__":
    main()
