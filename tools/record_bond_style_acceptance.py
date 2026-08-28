from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from PyQt6.QtCore import QPoint, QPointF, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from chemanim2d.app import MainWindow
from chemanim2d.core import BUILD_COMMIT


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow(ROOT)
    window.resize(1680, 1000)
    window.show()
    QTest.qWait(250)
    canvas = window.canvas
    project = window.session.project()
    project["scene"].update({"background": "FFFFFFFF", "title": "bond_style_acceptance"})
    window.session.replace_json(json.dumps(project))
    window.mode_panel.set_mode("绘制")
    window.mode_panel.set_category("结构")
    canvas.fit_artboard()
    canvas.view_scale = 3.0
    canvas.pan = QPointF()
    canvas.request_refresh()
    QTest.qWait(100)
    output = ROOT / "media" / "bond_style_acceptance"
    output.mkdir(parents=True, exist_ok=True)

    def drag(tool: str, start: QPoint, end: QPoint):
        window._set_tool(tool)
        QTest.mousePress(canvas, Qt.MouseButton.LeftButton, pos=start)
        QTest.mouseMove(canvas, end, 90)
        QTest.mouseRelease(canvas, Qt.MouseButton.LeftButton, pos=end)
        QTest.qWait(70)
        return window.session.project()["molecules"][0]["bonds"][-1]["id"]

    def midpoint(bond_id: str) -> QPoint:
        bond = next(item for item in window.session.depict(False)["bonds"] if item["id"] == bond_id)
        return QPoint(round((bond["first"]["x"] + bond["second"]["x"]) * .5),
                      round((bond["first"]["y"] + bond["second"]["y"]) * .5))

    def click_double(bond_id: str, count: int):
        window._set_tool("double_bond")
        for _ in range(count):
            QTest.mouseClick(canvas, Qt.MouseButton.LeftButton, pos=midpoint(bond_id))
            QTest.qWait(60)

    # Three disconnected bonds exercise the exact canvas gesture used by the
    # editor. The second/third are then cycled to persistent Left/Right styles.
    center = drag("double_bond", QPoint(650, 300), QPoint(750, 300))
    left = drag("double_bond", QPoint(650, 450), QPoint(750, 450))
    right = drag("double_bond", QPoint(650, 600), QPoint(750, 600))
    triple = drag("triple_bond", QPoint(900, 450), QPoint(1000, 450))
    click_double(left, 1)
    click_double(right, 2)
    sides = [bond["secondary_line_side"] for bond in window.session.project()["molecules"][0]["bonds"][:3]]
    assert sides == ["center", "left", "right"], sides
    QTest.mouseMove(canvas, QPoint(40, 40), 50)
    window.refresh_all()
    QTest.qWait(120)
    window.grab().save(str(output / "double-center-left-right.png"))

    # Hover must outline every visible stroke of a multiple bond.
    QTest.mouseMove(canvas, midpoint(center), 100)
    QTest.qWait(80)
    assert canvas._hover.get("kind") == "bond" and canvas._hover.get("id") == center
    window.grab().save(str(output / "double-hover-two-strokes.png"))
    QTest.mouseMove(canvas, midpoint(triple), 100)
    QTest.qWait(80)
    assert canvas._hover.get("kind") == "bond" and canvas._hover.get("id") == triple
    window.grab().save(str(output / "triple-hover-three-strokes.png"))

    # A centered alkene joined to a single bond reproduces the junction from
    # the user report and records the flat secondary-line caps.
    alkene = drag("double_bond", QPoint(870, 700), QPoint(970, 700))
    depiction = window.session.depict(False)
    alkene_geometry = next(item for item in depiction["bonds"] if item["id"] == alkene)
    endpoint = QPoint(round(alkene_geometry["second"]["x"]), round(alkene_geometry["second"]["y"]))
    drag("single_bond", endpoint, endpoint + QPoint(55, -75))
    QTest.mouseMove(canvas, QPoint(40, 40), 50)
    window.refresh_all()
    QTest.qWait(100)
    window.grab().save(str(output / "alkene-single-junction.png"))

    # Record the other explicit visual primitives against the same ACS scale.
    window.new_project()
    project = window.session.project()
    project["scene"].update({"background": "FFFFFFFF", "title": "bond_primitives"})
    window.session.replace_json(json.dumps(project))
    canvas.view_scale = 3.0
    canvas.pan = QPointF()
    for x,tool in zip((540,650,760,870,980,1090),
                      ("single_bond","double_bond","triple_bond",
                       "solid_wedge","dashed_wedge","wavy_bond")):
        drag(tool,QPoint(x,300),QPoint(x,400))
    canvas._hover={"kind":"none","id":""}
    window.refresh_all()
    QTest.qWait(100)
    window.grab().save(str(output / "bond-primitives-acs-shape.png"))

    # The previous regression hid at normal zoom. Recreate the user's 8x
    # centred-double benzene with the ChemDraw terminal geometry unchanged;
    # the discarded RDKit layer must not leave anonymous black hooks behind.
    window.new_project()
    project=window.session.project()
    project["scene"].update({"background":"FFFFFFFF","title":"centered_double_junctions"})
    window.session.replace_json(json.dumps(project))
    canvas.view_scale=8.0
    canvas.pan=QPointF()
    window._set_tool("benzene")
    QTest.mouseClick(canvas,Qt.MouseButton.LeftButton,pos=QPoint(760,500))
    QTest.qWait(100)
    for value in list(window.session.project()["molecules"][0]["bonds"]):
        if value["type"]!="double":continue
        click_double(value["id"],2 if value["secondary_line_side"]=="left" else 1)
    drawing=window.session.depict(False)
    centered=[bond for bond in drawing["bonds"] if bond["type"]=="double"]
    assert len(centered)==3 and all(bond["secondary_line_side"]=="center" for bond in centered)
    assert all(sum(value<0 for value in bond["first_extensions"])==1 and
               sum(value>0 for value in bond["second_extensions"])==1 for bond in centered)
    (output / "benzene-centered-double-junctions.svg").write_text(
        drawing["svg"], encoding="utf-8")
    canvas._hover={"kind":"none","id":""}
    window.refresh_all()
    QTest.qWait(100)
    window.grab().save(str(output / "benzene-centered-double-junctions-8x.png"))

    report = {"core": BUILD_COMMIT, "sides": sides,
              "screenshots": [str(path) for path in sorted(output.glob("*.png"))]}
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    window.close()


if __name__ == "__main__":
    main()
