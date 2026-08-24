from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from chemanim2d.core import CoreSession


def atom_motion() -> None:
    core = CoreSession()
    core.import_smiles("移动原子示例", "O=C1NCC(=O)N1")
    document = json.loads(core.json())
    document["mod"] = "atom_motion"
    document["scene"]["title"] = "atom_motion"
    document["scene"]["background"] = "FFFFFFFF"
    molecule = document["molecules"][0]
    molecule["x"] = 0
    molecule["y"] = 0
    molecule["scale"] = 5.0
    core.replace_json(json.dumps(document, ensure_ascii=False))
    atoms = core.project()["molecules"][0]["atoms"]
    movable = [atoms[0], atoms[1], atoms[-1]]
    for index, atom in enumerate(movable):
        core.add_node("atom_lerp_xy", json.dumps({"target": core.active_molecule, "atom": atom["id"], "x": atom["x"] + .55 * (index + 1), "y": atom["y"] + (-.45 if index % 2 else .4), "frames": 60, "easing": "linear"}))
    directory = ROOT / "mod" / "atom_motion"
    directory.mkdir(parents=True, exist_ok=True)
    core.save(str(directory / "atom_motion.cmm"))
    core.write_mod(str(ROOT))


def static_cache_benchmark() -> None:
    core = CoreSession(); core.import_smiles("静止缓存基准", "CC(C)C1=CC=C(C=C1)C(C)C(=O)O")
    document = json.loads(core.json()); document["mod"] = "static_cache"; document["scene"]["title"] = "static_cache"; document["molecules"][0]["scale"] = 4.0
    core.replace_json(json.dumps(document, ensure_ascii=False))
    atom = core.project()["molecules"][0]["atoms"][0]
    core.add_node("atom_lerp_xy", json.dumps({"target": core.active_molecule, "atom": atom["id"], "x": atom["x"], "y": atom["y"], "frames": 60, "easing": "linear"}))
    directory = ROOT / "mod" / "static_cache"; directory.mkdir(parents=True, exist_ok=True)
    core.save(str(directory / "static_cache.cmm")); core.write_mod(str(ROOT))


def medium_motion_benchmark() -> None:
    core = CoreSession()
    core.import_smiles("中等分子运动基准", "CCOC(=O)N1CCC(CC1)OC2=CC=CC=C2")
    document = json.loads(core.json())
    document["mod"] = "medium_motion"
    document["scene"]["title"] = "medium_motion"
    document["molecules"][0]["scale"] = 3.2
    core.replace_json(json.dumps(document, ensure_ascii=False))
    atoms = core.project()["molecules"][0]["atoms"]
    for index in (0, len(atoms) // 2, len(atoms) - 1):
        atom = atoms[index]
        core.add_node("atom_lerp_xy", json.dumps({"target": core.active_molecule, "atom": atom["id"], "x": atom["x"] + .5, "y": atom["y"] + .35, "frames": 60, "easing": "linear"}))
    directory = ROOT / "mod" / "medium_motion"
    directory.mkdir(parents=True, exist_ok=True)
    core.save(str(directory / "medium_motion.cmm"))
    core.write_mod(str(ROOT))


if __name__ == "__main__":
    atom_motion()
    static_cache_benchmark()
    medium_motion_benchmark()
    print(ROOT / "mod" / "atom_motion" / "atom_motion.cmm")
