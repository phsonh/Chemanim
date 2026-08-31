from __future__ import annotations

import faulthandler
import json
from pathlib import Path
import sys

faulthandler.enable(all_threads=True)

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QSpinBox, QToolButton

from chemanim2d.app import MainWindow


def checkpoint(name: str, **values: object) -> None:
    print(json.dumps({"checkpoint": name, **values}, ensure_ascii=False), flush=True)


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(False)
    window = MainWindow(ROOT)
    window.resize(1500, 900)
    window.show()
    QTest.qWait(120)

    create = next(node for node in window.session.project()["nodes"] if node["type"] == "molecule_create")
    target = create["params"]["target"]
    structure = window._add_node("molecule_set_structure", {"target": target}, False)
    window.mode_panel.set_mode("绘制")
    QApplication.processEvents()
    ring = next(
        button for button in window.mode_panel.tertiary.findChildren(QToolButton)
        if button.property("drawKind") == "ring6"
    )
    QTest.mouseClick(ring, Qt.MouseButton.LeftButton)
    QTest.mouseClick(
        window.canvas, Qt.MouseButton.LeftButton,
        pos=QPoint(window.canvas.width() // 2 + 170, window.canvas.height() // 2 - 90),
    )
    QApplication.processEvents()
    checkpoint("structure-created", structure=structure)

    alpha = window._add_node("molecule_set_alpha", {"target": target, "value": 255}, False)
    item = next(
        window.node_list.tree.topLevelItem(index)
        for index in range(window.node_list.tree.topLevelItemCount())
        if window.node_list.tree.topLevelItem(index).data(0, Qt.ItemDataRole.UserRole) == alpha
    )
    window.node_list.tree.setCurrentItem(item)
    window.node_list.tree.scrollToItem(item)
    QApplication.processEvents()
    rect = window.node_list.tree.visualItemRect(item)
    QTest.mouseClick(
        window.node_list.tree.viewport(), Qt.MouseButton.LeftButton,
        pos=rect.center(),
    )
    QTest.qWait(60)
    QTest.mouseDClick(
        window.node_list.tree.viewport(), Qt.MouseButton.LeftButton,
        pos=rect.center(), delay=60,
    )
    QApplication.processEvents()
    checkpoint("inspector-opened", node=alpha, inspector_node=window.inspector.node_id, editors=sorted(window.inspector.editors), title=window.inspector.title.text(), rows=window.inspector.layout.rowCount())

    if "value" not in window.inspector.editors:
        checkpoint("inspector-controls-lost-during-open")
        QTest.mouseDClick(
            window.node_list.tree.viewport(), Qt.MouseButton.LeftButton,
            pos=rect.center(), delay=60,
        )
        QApplication.processEvents()
        checkpoint("inspector-reopened", node=alpha, editors=sorted(window.inspector.editors))

    editor = window.inspector.editors["value"][0]
    if not isinstance(editor, QSpinBox):
        raise RuntimeError(f"透明度编辑器不是 QSpinBox：{type(editor)!r}")
    editor.setFocus()
    QTest.keyClick(editor, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClicks(editor, "0")
    checkpoint("alpha-typed", value=editor.value())
    QTest.keyClick(editor, Qt.Key.Key_Return)
    QApplication.processEvents()
    QTest.qWait(200)
    stored = next(node for node in window.session.project()["nodes"] if node["id"] == alpha)["params"]["value"]
    checkpoint(
        "alpha-committed",
        stored=stored,
        inspector_alive=window.inspector.node_id == alpha,
        panel_visible=window.inspector_panel.isVisible(),
    )
    window.close()
    QApplication.processEvents()
    checkpoint("normal-exit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
