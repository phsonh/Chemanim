from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from chemanim2d.app import MainWindow
from chemanim2d.core import BUILD_COMMIT


def capture(window: MainWindow, path: Path) -> None:
    window.canvas._refresh_now()
    QApplication.processEvents()
    if not window.grab().save(str(path)):
        raise RuntimeError(f"无法保存验收截图：{path}")


def main() -> None:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    output = ROOT / "media" / "visual_events"
    output.mkdir(parents=True, exist_ok=True)
    project_path = ROOT / "mod" / "visual_events" / "visual_events.cmm"

    window = MainWindow(ROOT)
    window.resize(1720, 1040)
    window.show()
    window.load(project_path)
    window.canvas.fit_artboard()
    QTest.qWait(250)

    lerp = next(node for node in window.session.project()["nodes"]
                if node["type"] == "molecule_lerp_position")
    base_molecules = json.loads(window.session.json())["molecules"]
    before = dict(lerp["params"])
    window.node_list.refresh(lerp["id"])
    window._node_selected(lerp["id"])
    window.canvas._refresh_now()
    assert window.session.edit_target_kind == "script_node"
    assert window.session.can_direct_manipulate and not window.session.can_edit_structure
    atom = window.canvas._depiction["atoms"][0]["center"]
    start = QPoint(round(atom["x"]), round(atom["y"]))
    end = start + QPoint(24, -12)
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=start)
    QTest.mouseMove(window.canvas, end, 80)
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=end)
    QTest.qWait(80)
    changed = next(node for node in window.session.project()["nodes"] if node["id"] == lerp["id"])["params"]
    assert changed != before
    assert window.session.project()["molecules"] == base_molecules
    capture(window, output / "editor-node-target-edit.png")

    window.load(project_path)
    window.canvas.fit_artboard()
    window.frame_spin.setValue(52)
    QTest.qWait(80)
    assert window.session.edit_target_kind == "timeline_preview"
    assert window.edit_mode.text() == "预览：只读"
    capture(window, output / "editor-timeline-readonly.png")

    window._toggle_play()
    QTest.qWait(140)
    assert window._playing and window.session.edit_target_kind == "timeline_preview"
    capture(window, output / "editor-playback-readonly.png")
    window._toggle_play()

    window.frame_spin.setValue(120)
    window.actions["final"].setChecked(True)
    window._toggle_final_effect(True)
    QTest.qWait(100)
    assert window.canvas.final_effect
    assert window.session.edit_target_kind == "timeline_preview"
    capture(window, output / "editor-final-effect.png")

    report = {
        "core": BUILD_COMMIT,
        "project": str(project_path),
        "node_target_edit_kept_base_structure": True,
        "timeline_preview_readonly": True,
        "playback_readonly": True,
        "final_effect_readonly": True,
    }
    (output / "editor-acceptance.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    window.close()


if __name__ == "__main__":
    main()
