from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from chemanim2d.core import BUILD_COMMIT, CoreSession


def params_for(session: CoreSession, node_id: str) -> dict:
    return next(node["params"] for node in session.project()["nodes"] if node["id"] == node_id)


def update_gradient(session: CoreSession, node_id: str, mutate) -> None:
    params = params_for(session, node_id)
    mutate(params["end_snapshot"])
    if not session.update_node(node_id, json.dumps(params, ensure_ascii=False)):
        raise RuntimeError(f"未能更新渐变结构节点 {node_id}")


def charge(adornment_id: str, atom_id: str, text: str, serial: int) -> dict:
    return {
        "id": adornment_id, "atom": atom_id, "text": text,
        "x": 18.0, "y": 18.0, "alive": True, "alpha": 255,
        "creation_serial": serial, "color": {"r": 0, "g": 0, "b": 0},
    }


def main() -> None:
    session = CoreSession()
    substrate = session.import_smiles("叔丁基溴", "CC(C)(C)Br")
    chloride = session.import_smiles("氯离子", "[Cl-]")
    chloride_structure = next(
        node for node in session.project()["nodes"]
        if node["type"] == "molecule_set_structure" and node["params"]["target"] == chloride
    )
    chloride_params = chloride_structure["params"]
    next(atom for atom in chloride_params["snapshot"]["atoms"] if atom["element"] == "Cl")["label"] = "Cl"
    session.update_node(chloride_structure["id"], json.dumps(chloride_params, ensure_ascii=False))
    session.add_node("molecule_set_position", json.dumps({"target": substrate, "x": -75.0, "y": 0.0}))
    session.add_node("molecule_set_position", json.dumps({"target": chloride, "x": 135.0, "y": 0.0}))

    # One object becomes two independent identities at exactly the same pose.
    session.set_active_molecule(substrate)
    split = session.add_node("split_molecule", "{}")
    carbocation = params_for(session, split)["output"]
    split_map = params_for(session, split)["id_map"]["target"]["atoms"]
    substrate_snapshot = next(
        node["params"]["snapshot"] for node in session.project()["nodes"]
        if node["type"] == "molecule_set_structure" and node["params"]["target"] == substrate
    )
    neighbours: dict[str, set[str]] = {atom["id"]: set() for atom in substrate_snapshot["atoms"]}
    for bond in substrate_snapshot["bonds"]:
        neighbours[bond["a"]].add(bond["b"]);neighbours[bond["b"]].add(bond["a"])
    central_old = next(atom_id for atom_id, values in neighbours.items() if len(values) == 4)
    bromine_old = next(atom["id"] for atom in substrate_snapshot["atoms"] if atom["element"] == "Br")
    central = split_map[central_old];bromine_copy = split_map[bromine_old]

    # The copied identity becomes the carbocation while the original becomes
    # bromide.  Both ordinary gradients start at frame zero and share no IDs.
    session.set_active_molecule(carbocation)
    cation_gradient = session.add_node("molecule_gradient_structure", json.dumps({"frames": 30, "easing": "in_out_quad"}))
    def make_cation(snapshot: dict) -> None:
        for atom in snapshot["atoms"]:
            if atom["id"] == bromine_copy:atom["alive"] = False
        for bond in snapshot["bonds"]:
            if bromine_copy in (bond["a"], bond["b"]):bond["alive"] = False
        snapshot["adornments"].append(charge("D9001", central, "⊕", 9001))
        snapshot["next_adornment_id"] = 9002
    update_gradient(session, cation_gradient, make_cation)

    session.set_active_molecule(substrate)
    bromide_gradient = session.add_node("molecule_gradient_structure", json.dumps({"frames": 30, "easing": "in_out_quad"}))
    def make_bromide(snapshot: dict) -> None:
        for atom in snapshot["atoms"]:
            atom["alive"] = atom["id"] == bromine_old
            if atom["id"] == bromine_old:atom["label"] = "Br"
        for bond in snapshot["bonds"]:bond["alive"] = False
        snapshot["adornments"].append(charge("D9002", bromine_old, "⊖", 9002))
        snapshot["next_adornment_id"] = 9003
    update_gradient(session, bromide_gradient, make_bromide)
    session.add_node("molecule_lerp_position", json.dumps({"target": substrate, "x": -205.0, "y": 70.0, "frames": 30, "easing": "out_cubic"}))
    session.add_node("wait", json.dumps({"frames": 30}))

    # Merge makes a third, disconnected object.  Its own ordinary structure
    # gradient moves chloride to the carbocation and creates the C-Cl bond.
    session.set_active_molecule(carbocation)
    merge = session.add_node("merge_molecules", json.dumps({"source": chloride}))
    product = params_for(session, merge)["output"]
    merge_map = params_for(session, merge)["id_map"]
    central_product = merge_map["target"]["atoms"][central]
    chloride_old = next(
        atom["id"] for node in session.project()["nodes"]
        if node["type"] == "molecule_set_structure" and node["params"]["target"] == chloride
        for atom in node["params"]["snapshot"]["atoms"] if atom["element"] == "Cl"
    )
    chloride_product = merge_map["source"]["atoms"][chloride_old]
    product_gradient = session.add_node("molecule_gradient_structure", json.dumps({"frames": 30, "easing": "in_out_quad"}))
    def make_product(snapshot: dict) -> None:
        central_atom = next(atom for atom in snapshot["atoms"] if atom["id"] == central_product)
        chlorine_atom = next(atom for atom in snapshot["atoms"] if atom["id"] == chloride_product)
        chlorine_atom["x"] = central_atom["x"] - 16.0
        chlorine_atom["y"] = central_atom["y"] + 27.7128129211
        for adornment in snapshot["adornments"]:adornment["alive"] = False
        snapshot["bonds"].append({
            "id": "B9001", "a": central_product, "b": chloride_product,
            "type": "single", "secondary_line_side": "center", "stereo": "none",
            "visible": True, "alive": True, "alpha": 255,
            "color": {"r": 0, "g": 0, "b": 0},
        })
        snapshot["next_bond_id"] = 9002
    update_gradient(session, product_gradient, make_product)
    session.add_node("wait", json.dumps({"frames": 30}))

    raw = json.loads(session.json());raw["mod"] = "sn1_object_acceptance"
    session.replace_json(json.dumps(raw, ensure_ascii=False))
    mod = ROOT / "mod" / raw["mod"];output = ROOT / "media" / raw["mod"]
    mod.mkdir(parents=True, exist_ok=True);output.mkdir(parents=True, exist_ok=True)
    session.save(str(mod / f'{raw["mod"]}.cmm'));session.write_mod(str(ROOT))

    reopened = CoreSession();reopened.load(str(mod / f'{raw["mod"]}.cmm'))
    if reopened.evaluated_project(60) != session.evaluated_project(60):
        raise RuntimeError("SN1 项目保存重开后结果不同")
    scene = session.project()["scene"]
    session.set_viewport(scene["width"], scene["height"], scene["width"] / scene["logic_width"], 0.0, 0.0)
    executable = ROOT / "build" / "release" / "chemanim.exe"
    comparisons: dict[str, object] = {}
    for frame in (0, 15, 30, 45, 60):
        run = subprocess.run([str(executable), raw["mod"], "--frame", str(frame), "--no-open"], cwd=ROOT, capture_output=True, text=True, timeout=120)
        if run.returncode:raise RuntimeError(run.stdout + "\n" + run.stderr)
        engine_source = ROOT / "media" / raw["mod"] / f'{raw["mod"]}_frame_{frame}.png'
        engine_path = output / f"engine-{frame:03d}.png";shutil.copy2(engine_source, engine_path)
        drawing = session.depict_at(frame, True);core_path = output / f"core-{frame:03d}.png"
        Image.frombytes("RGBA", (drawing["width"], drawing["height"]), bytes(drawing["rgba"])).save(core_path)
        difference = ImageChops.difference(Image.open(core_path).convert("RGBA"), Image.open(engine_path).convert("RGBA"))
        difference.save(output / f"difference-{frame:03d}.png");statistics = ImageStat.Stat(difference)
        comparisons[str(frame)] = {"bbox": difference.getbbox(), "max_rms": max(statistics.rms)}

    before = set(output.glob(f'{raw["mod"]}_*.mp4'))
    run = subprocess.run([str(executable), raw["mod"], "--no-open"], cwd=ROOT, capture_output=True, text=True, timeout=240)
    if run.returncode:raise RuntimeError(run.stdout + "\n" + run.stderr)
    created = sorted(set(output.glob(f'{raw["mod"]}_*.mp4')) - before, key=lambda path: path.stat().st_mtime)
    if not created:raise RuntimeError("SN1 最终引擎没有生成 MP4")
    video = output / "sn1-split-merge.mp4";shutil.copy2(created[-1], video)
    report = {
        "core": BUILD_COMMIT, "saved_reopened": True,
        "split": {"input": substrate, "output": carbocation},
        "merge": {"inputs": [carbocation, chloride], "output": product},
        "frames": comparisons, "mp4": video.name,
    }
    from PyQt6.QtWidgets import QApplication
    from chemanim2d.app import MainWindow
    application = QApplication.instance() or QApplication([])
    editor = MainWindow(ROOT);editor.session.load(str(mod / f'{raw["mod"]}.cmm'));editor.refresh_all(merge)
    editor.resize(1800, 1050);editor.show();editor.mode_panel.set_mode("脚本");editor.mode_panel.set_category("分子");editor.mode_panel.set_script_scope("对象")
    editor._node_selected(merge);application.processEvents();editor.grab().save(str(output / "editor-sn1-object-workflow.png"))
    editor.mode_panel.set_category("通用");application.processEvents();editor.grab().save(str(output / "editor-general-direct-tools.png"))
    editor.close();application.processEvents()
    report["ui"] = ["editor-sn1-object-workflow.png", "editor-general-direct-tools.png"]
    (output / "acceptance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
