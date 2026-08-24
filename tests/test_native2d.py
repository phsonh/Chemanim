from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from chemanim2d.core import CoreSession


def session() -> CoreSession:
    result = CoreSession(); result.add_blank_molecule("manual"); result.set_viewport(960, 540, 48, 0, 0); return result


def gesture(core: CoreSession, tool: str, start, end=None):
    core.set_tool(tool); end = end or start
    core.pointer_down(*start); core.pointer_move(*end); return core.pointer_up(*end)


def atoms(core: CoreSession): return core.project()["molecules"][0]["atoms"]
def bonds(core: CoreSession): return core.project()["molecules"][0]["bonds"]


def canvas_point(core: CoreSession, atom_id: str):
    depiction = core.depict(False)
    point = next(item["center"] for item in depiction["atoms"] if item["id"] == atom_id)
    return point["x"], point["y"]


def test_manual_acetaminophen_from_blank_canvas():
    core = session(); gesture(core, "benzene", (480, 270))
    ring = list(atoms(core)); assert len(ring) == 6
    left = canvas_point(core, ring[0]["id"]); gesture(core, "single_bond", left, (left[0] - 65, left[1]))
    oxygen = atoms(core)[-1]["id"]; gesture(core, "atom_label", canvas_point(core, oxygen)); core.set_element("O"); gesture(core, "atom_label", canvas_point(core, oxygen))
    right = canvas_point(core, ring[3]["id"]); gesture(core, "single_bond", right, (right[0] + 65, right[1]))
    nitrogen = atoms(core)[-1]["id"]; core.set_element("N"); gesture(core, "atom_label", canvas_point(core, nitrogen))
    npoint = canvas_point(core, nitrogen); gesture(core, "single_bond", npoint, (npoint[0] + 62, npoint[1] - 25))
    carbonyl = atoms(core)[-1]["id"]; cpoint = canvas_point(core, carbonyl)
    gesture(core, "double_bond", cpoint, (cpoint[0], cpoint[1] - 65)); carbonyl_o = atoms(core)[-1]["id"]
    core.set_element("O"); gesture(core, "atom_label", canvas_point(core, carbonyl_o))
    gesture(core, "single_bond", canvas_point(core, carbonyl), (cpoint[0] + 62, cpoint[1] + 25))
    assert len(atoms(core)) == 11
    assert sum(atom["element"] == "O" for atom in atoms(core)) == 2
    assert sum(atom["element"] == "N" for atom in atoms(core)) == 1
    assert any(bond["type"] == "double" for bond in bonds(core))
    assert "bond-" in core.depict(False)["svg"]


def test_manual_ibuprofen_uses_ring_double_element_and_wedge():
    core = session(); gesture(core, "benzene", (480, 270)); ring = list(atoms(core))
    first = canvas_point(core, ring[0]["id"]); gesture(core, "single_bond", first, (first[0] - 60, first[1])); chain1 = atoms(core)[-1]["id"]
    gesture(core, "single_bond", canvas_point(core, chain1), (canvas_point(core, chain1)[0] - 55, canvas_point(core, chain1)[1] - 35)); branch = atoms(core)[-1]["id"]
    gesture(core, "single_bond", canvas_point(core, branch), (canvas_point(core, branch)[0] - 45, canvas_point(core, branch)[1] - 45))
    gesture(core, "single_bond", canvas_point(core, branch), (canvas_point(core, branch)[0] - 45, canvas_point(core, branch)[1] + 45))
    other = canvas_point(core, ring[3]["id"]); gesture(core, "solid_wedge", other, (other[0] + 62, other[1])); chiral = atoms(core)[-1]["id"]
    gesture(core, "single_bond", canvas_point(core, chiral), (canvas_point(core, chiral)[0] + 58, canvas_point(core, chiral)[1] + 30))
    acid = atoms(core)[-1]["id"]; ap = canvas_point(core, acid)
    gesture(core, "double_bond", ap, (ap[0], ap[1] - 62)); o1 = atoms(core)[-1]["id"]
    core.set_element("O"); gesture(core, "atom_label", canvas_point(core, o1))
    gesture(core, "single_bond", canvas_point(core, acid), (ap[0] + 55, ap[1] + 35)); o2 = atoms(core)[-1]["id"]
    core.set_element("O"); gesture(core, "atom_label", canvas_point(core, o2))
    assert any(bond["stereo"] == "wedge" for bond in bonds(core))
    assert sum(atom["element"] == "O" for atom in atoms(core)) == 2
    assert sum(bond["type"] == "double" for bond in bonds(core)) >= 4


def test_stable_ids_survive_save_close_reopen_and_are_not_reused(tmp_path: Path):
    core = session(); gesture(core, "ring5", (480, 270)); before = core.project(); path = tmp_path / "roundtrip.cmm"; core.save(str(path))
    restored = CoreSession(); restored.load(str(path)); assert restored.project()["molecules"][0]["atoms"] == before["molecules"][0]["atoms"]
    restored.set_viewport(960, 540, 48, 0, 0); removed = restored.project()["molecules"][0]["atoms"][-1]["id"]
    gesture(restored, "eraser", canvas_point(restored, removed)); gesture(restored, "atom_label", (700, 400))
    assert atoms(restored)[-1]["id"] != removed


def test_project_overwrite_and_molecule_ids_continue_after_reopen(tmp_path: Path):
    core = CoreSession(); assert core.add_blank_molecule() == "molecule1"
    path = tmp_path / "overwrite.cmm"; core.save(str(path)); core.save(str(path))
    restored = CoreSession(); restored.load(str(path))
    assert restored.add_blank_molecule() == "molecule2"


def test_tween_target_drag_does_not_modify_base_structure():
    core = CoreSession(); core.import_smiles("ethanol", "CCO"); core.set_viewport(960, 540, 48, 0, 0)
    atom = core.project()["molecules"][0]["atoms"][-1]; original = (atom["x"], atom["y"])
    tween = core.add_atom_tween(atom["id"], 10, 30, atom["x"] + 2, atom["y"]); core.edit_atom_tween(tween)
    point = canvas_point(core, atom["id"]); core.pointer_down(*point); core.pointer_move(point[0], point[1] - 40); assert core.pointer_up(point[0], point[1] - 40)["changed"]
    after = next(item for item in core.project()["molecules"][0]["atoms"] if item["id"] == atom["id"])
    assert (after["x"], after["y"]) == original
    assert core.project()["timeline"]["atom_tweens"][0]["y"] != original[1]


def test_later_overlapping_tween_starts_from_current_state():
    core = CoreSession(); core.import_smiles("ethanol", "CCO"); core.set_viewport(960, 540, 48, 0, 0)
    atom = core.project()["molecules"][0]["atoms"][-1]
    core.add_atom_tween(atom["id"], 0, 60, atom["x"] + 6, atom["y"])
    core.add_atom_tween(atom["id"], 30, 30, atom["x"] - 2, atom["y"])
    d29 = core.depict_at(29); d30 = core.depict_at(30)
    p29 = next(item["center"] for item in d29["atoms"] if item["id"] == atom["id"])
    p30 = next(item["center"] for item in d30["atoms"] if item["id"] == atom["id"])
    assert abs(p30["x"] - p29["x"]) < 10


def test_lua_uses_authoritative_tables_and_no_embedded_svg():
    core = CoreSession(); core.import_smiles("ethanol", "CCO"); lua = core.generate_lua()
    assert "chem.NewMol" in lua and "atoms =" in lua and "bonds =" in lua
    assert "acs_svg" not in lua


def test_irregular_coordinates_are_not_relaid_out():
    core = session(); gesture(core, "ring5", (480, 270)); ids = [atom["id"] for atom in atoms(core)]
    targets = [(0,0),(2.7,.2),(2.2,2.1),(.4,1.3),(-1.0,.4)]
    for atom_id, (x, y) in zip(ids, targets): core.set_atom_position(atom_id, x, y)
    saved = [(a["x"],a["y"]) for a in atoms(core)]; core.depict(False)
    assert [(a["x"],a["y"]) for a in atoms(core)] == saved


def test_fixed_depiction_scale_does_not_refit_irregular_coordinates():
    core = session(); gesture(core, "ring5", (480, 270)); ids = [atom["id"] for atom in atoms(core)]
    first = core.depict(False)["transform"]
    core.set_atom_position(ids[0], 12.0, -7.0)
    moved = core.depict(False)["transform"]
    assert first == moved == {"origin": {"x": 480.0, "y": 270.0}, "pixels_per_unit": 48.0}
