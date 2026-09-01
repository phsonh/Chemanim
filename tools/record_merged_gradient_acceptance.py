from __future__ import annotations

import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PyQt6.QtCore import QPoint, QTimer, Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication, QDialogButtonBox

from chemanim2d.app import GradientStructureDialog, MainWindow
from chemanim2d.core import BUILD_COMMIT, CoreSession


def capture(window: MainWindow, path: Path) -> None:
    window.canvas._refresh_now()
    QApplication.processEvents()
    QTest.qWait(80)
    if not window.grab().save(str(path)):
        raise RuntimeError(f"cannot save {path}")


def node(session: CoreSession, node_id: str) -> dict:
    return next(value for value in session.project()["nodes"] if value["id"] == node_id)


def main() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    output = ROOT / "media" / "merged_gradient_acceptance"
    mod = ROOT / "mod" / "merged_gradient_acceptance"
    output.mkdir(parents=True, exist_ok=True)
    mod.mkdir(parents=True, exist_ok=True)

    window = MainWindow(ROOT)
    window.resize(1900, 1120)
    window.show()
    window.session.new_project()
    ring = window.session.import_smiles("benzene", "c1ccccc1")
    nitro = window.session.import_smiles("nitronium", "O=[N+]=O")
    window.session.add_node("molecule_set_position", json.dumps({"target": ring, "x": -70.0, "y": 0.0}))
    position = window.session.add_node("molecule_set_position", json.dumps({"target": nitro, "x": 105.0, "y": 0.0}))
    window.refresh_all(position)
    window._node_selected(position)
    window.canvas.fit_artboard()
    QTest.qWait(120)

    observed: list[str] = []

    def accept_dialog() -> None:
        dialog = next(value for value in QApplication.topLevelWidgets()
                      if isinstance(value, GradientStructureDialog) and value.isVisible())
        observed.extend(dialog.target.itemData(index) for index in range(dialog.target.count()))
        dialog.target.setCurrentIndex(dialog.target.findData(ring))
        dialog.merge.setChecked(True)
        dialog.source.setCurrentIndex(dialog.source.findData(nitro))
        QApplication.processEvents()
        dialog.grab().save(str(output / "01-multi-molecule-target-dialog.png"))
        QTest.mouseClick(dialog.buttons.button(QDialogButtonBox.StandardButton.Ok),
                         Qt.MouseButton.LeftButton)

    QTimer.singleShot(0, accept_dialog)
    gradient_id = window._add_node("molecule_gradient_structure")
    if observed != [ring, nitro]:
        raise RuntimeError(f"unexpected living targets: {observed}")
    project = window.session.project()
    gradient = node(window.session, gradient_id)
    merge = next(value for value in project["nodes"]
                 if value["type"] == "merge_molecules" and
                 value["params"].get("output") == gradient["params"]["target"])
    source_ids = set(merge["params"]["id_map"]["source"]["atoms"].values())
    ring_ids = set(merge["params"]["id_map"]["target"]["atoms"].values())
    end = gradient["params"]["end_snapshot"]
    nitrogen_id = next(atom["id"] for atom in end["atoms"]
                       if atom["id"] in source_ids and
                       (atom.get("label") or atom.get("element")) == "N")

    window._set_tool("move")
    window.canvas._sync_core_viewport()
    window.canvas._refresh_now()
    points = {item["id"]: item["center"] for item in window.session.depict(False)["atoms"]}
    pivot = QPoint(round(points[nitrogen_id]["x"]), round(points[nitrogen_id]["y"]))
    stationary_id = min(ring_ids)
    stationary = points[stationary_id]
    candidate = QPoint(round(stationary["x"] + end["reference_bond_length"] * window.canvas.view_scale),
                       round(stationary["y"]))
    QTest.mouseDClick(window.canvas, Qt.MouseButton.LeftButton, pos=pivot)
    QTest.mousePress(window.canvas, Qt.MouseButton.LeftButton, pos=pivot)
    QTest.mouseMove(window.canvas, candidate, 100)
    QApplication.processEvents()
    if not window.canvas._preview.get("text", "").startswith("1.00×"):
        raise RuntimeError(f"chemical snap did not activate: {window.canvas._preview}")
    capture(window, output / "02-nitrogen-fragment-snap.png")
    QTest.mouseRelease(window.canvas, Qt.MouseButton.LeftButton, pos=candidate)
    QApplication.processEvents()

    params = node(window.session, gradient_id)["params"]
    end = json.loads(json.dumps(params["end_snapshot"]))
    atoms = {atom["id"]: atom for atom in end["atoms"]}
    nitrogen = atoms[nitrogen_id]
    oxygens = [atoms[value] for value in source_ids
               if (atoms[value].get("label") or atoms[value].get("element")) == "O"]
    carbon = atoms[stationary_id]
    length = float(end["reference_bond_length"])
    attack_angle = math.atan2(nitrogen["y"] - carbon["y"], nitrogen["x"] - carbon["x"])
    for oxygen, angle in zip(oxygens, (attack_angle - math.pi / 3, attack_angle + math.pi / 3)):
        oxygen["x"] = nitrogen["x"] + length * math.cos(angle)
        oxygen["y"] = nitrogen["y"] + length * math.sin(angle)

    new_bond = f'B{end["next_bond_id"]}'
    end["next_bond_id"] += 1
    end["bonds"].append({"id": new_bond, "a": carbon["id"], "b": nitrogen_id,
                         "type": "single", "secondary_line_side": "center",
                         "stereo": "none", "visible": True, "alive": True,
                         "alpha": 255, "color": {"r": 0, "g": 0, "b": 0}})
    changed = next(value for value in end["bonds"]
                   if value["a"] in ring_ids and value["b"] in ring_ids and value["type"] == "double")
    changed["type"] = "single"
    adjacent_id = next(value["b"] if value["a"] == carbon["id"] else value["a"]
                       for value in end["bonds"]
                       if carbon["id"] in (value["a"], value["b"]) and
                       (value["b"] if value["a"] == carbon["id"] else value["a"]) in ring_ids)
    charge = f'D{end["next_adornment_id"]}'
    end["next_adornment_id"] += 1
    end["adornments"].append({"id": charge, "creation_serial": 990001,
                               "atom": adjacent_id, "text": "⊕", "x": 18.0, "y": 18.0,
                               "alpha": 255, "alive": True, "color": {"r": 0, "g": 0, "b": 0}})
    living_ring = [atoms[value] for value in ring_ids]
    centre = (sum(value["x"] for value in living_ring) / len(living_ring),
              sum(value["y"] for value in living_ring) / len(living_ring))
    direction = math.atan2(carbon["y"] - centre[1], carbon["x"] - centre[0])
    hydrogen = f'A{end["next_atom_id"]}'
    end["next_atom_id"] += 1
    end["atoms"].append({"id": hydrogen, "creation_serial": 990002, "element": "H",
                         "label": "H", "label_side": "right", "number_style": "subscript",
                         "isotope": 0, "radical_electrons": 0, "implicit_hydrogens": 0,
                         "hidden": False, "alive": True, "alpha": 255,
                         "color": {"r": 0, "g": 0, "b": 0},
                         "x": carbon["x"] + length * math.cos(direction),
                         "y": carbon["y"] + length * math.sin(direction)})
    h_bond = f'B{end["next_bond_id"]}'
    end["next_bond_id"] += 1
    end["bonds"].append({"id": h_bond, "a": carbon["id"], "b": hydrogen,
                         "type": "single", "secondary_line_side": "center",
                         "stereo": "none", "visible": True, "alive": True,
                         "alpha": 255, "color": {"r": 0, "g": 0, "b": 0}})
    params["end_snapshot"] = end
    window.session.update_node(gradient_id, json.dumps(params, ensure_ascii=False))
    window.refresh_all(gradient_id)
    window._node_selected(gradient_id)
    window.canvas.fit_all()
    capture(window, output / "03-gradient-endpoint-editor.png")

    raw = json.loads(window.session.json())
    raw["mod"] = "merged_gradient_acceptance"
    window.session.replace_json(json.dumps(raw, ensure_ascii=False))
    project_path = mod / "merged_gradient_acceptance.cmm"
    window.session.save(str(project_path))
    window.session.write_mod(str(ROOT))
    reopened = CoreSession()
    reopened.load(str(project_path))
    if reopened.evaluated_project(15) != window.session.evaluated_project(15):
        raise RuntimeError("save/reopen mismatch")

    scene = window.session.project()["scene"]
    window.session.set_viewport(scene["width"], scene["height"],
                                scene["width"] / scene["logic_width"], 0.0, 0.0)
    comparisons: dict[str, object] = {}
    executable = ROOT / "build" / "release" / "chemanim.exe"
    for phase, frame in (("start", 0), ("middle", 15), ("end", 30)):
        window._preview_frame(frame)
        capture(window, output / f"04-editor-{phase}.png")
        run = subprocess.run([str(executable), raw["mod"], "--frame", str(frame), "--no-open"],
                             cwd=ROOT, capture_output=True, text=True, timeout=120)
        if run.returncode:
            raise RuntimeError(run.stdout + "\n" + run.stderr)
        engine_source = output / f'{raw["mod"]}_frame_{frame}.png'
        engine_path = output / f"engine-{phase}.png"
        shutil.copy2(engine_source, engine_path)
        # Capturing the live editor resizes the session viewport back to the
        # canvas widget.  Restore the authoritative output viewport before
        # producing the Core comparison frame.
        window.session.set_viewport(scene["width"], scene["height"],
                                    scene["width"] / scene["logic_width"], 0.0, 0.0)
        drawing = window.session.depict_at(frame, True)
        core_path = output / f"core-{phase}.png"
        Image.frombytes("RGBA", (drawing["width"], drawing["height"]), bytes(drawing["rgba"])).save(core_path)
        difference = ImageChops.difference(Image.open(core_path).convert("RGBA"),
                                           Image.open(engine_path).convert("RGBA"))
        difference_path = output / f"difference-{phase}.png"
        difference.save(difference_path)
        stats = ImageStat.Stat(difference)
        comparisons[phase] = {"frame": frame, "bbox": difference.getbbox(),
                              "mean": stats.mean, "rms": stats.rms,
                              "max_rms": max(stats.rms)}

    before = set(output.glob(f'{raw["mod"]}_*.mp4'))
    run = subprocess.run([str(executable), raw["mod"], "--no-open"], cwd=ROOT,
                         capture_output=True, text=True, timeout=240)
    if run.returncode:
        raise RuntimeError(run.stdout + "\n" + run.stderr)
    created = sorted(set(output.glob(f'{raw["mod"]}_*.mp4')) - before,
                     key=lambda value: value.stat().st_mtime)
    if not created:
        raise RuntimeError("engine did not create MP4")
    video = output / "benzene-nitronium-merged-gradient.mp4"
    shutil.copy2(created[-1], video)

    report = {
        "core": BUILD_COMMIT,
        "living_targets": observed,
        "atomic_nodes": ["molecule_create", "merge_molecules", "molecule_gradient_structure"],
        "target": gradient["params"]["target"],
        "summary": window.session.gradient_summary(gradient_id),
        "saved_reopened": True,
        "lua_has_single_structure_gradient": window.session.generate_lua().count("LerpStructure(") == 1,
        "editor_engine_comparison": comparisons,
        "mp4": video.name,
    }
    (output / "acceptance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))
    window.close()
    QApplication.processEvents()


if __name__ == "__main__":
    main()
