from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from chemanim2d.codegen import generate_lua
from chemanim2d.depiction import render_acs1996
from chemanim2d.model import Project, load_project, save_project
from chemanim2d.smiles import molecule_from_smiles


def test_smiles_compiles_stable_ids_and_display_bonds():
    molecule = molecule_from_smiles("mapped", "[CH3:7][C:8](=O)O")
    assert [atom.id for atom in molecule.atoms[:2]] == ["A7", "A8"]
    assert len({atom.id for atom in molecule.atoms}) == len(molecule.atoms)
    assert any(bond.order == 2 for bond in molecule.bonds)


def test_v2_round_trip_and_lua_contains_no_texture(tmp_path: Path):
    project = Project(molecules=[molecule_from_smiles("acetaminophen", "CC(=O)NC1=CC=C(O)C=C1")])
    path = tmp_path / "demo.cmm"
    save_project(project, path)
    restored = load_project(path)
    assert restored.molecules[0].atoms[2].element == "O"
    lua = generate_lua(restored)
    assert "chem.NewMol {" in lua
    assert "source_smiles" in lua
    assert "acs_svg = [==[" in lua
    assert "load_texture" not in lua


def test_acs_svg_rebuilds_from_authoritative_xy():
    molecule = molecule_from_smiles("ethanol", "CCO")
    before = render_acs1996(molecule)
    reference = molecule.reference_bond_length
    molecule.atoms[-1].y += 0.4
    after = render_acs1996(molecule)
    assert after.svg != before.svg
    assert after.atom_points[molecule.atoms[-1].id] != before.atom_points[molecule.atoms[-1].id]
    assert molecule.reference_bond_length == reference


def test_stereochemical_smiles_produces_wedge_path():
    molecule = molecule_from_smiles("ibuprofen", "CC(C)C1=CC=C(C=C1)[C@@H](C)C(=O)O")
    depiction = render_acs1996(molecule)
    assert any(bond.stereo in {"wedge", "dash"} for bond in molecule.bonds)
    assert "bond-" in depiction.svg


def test_v1_project_reports_clear_error(tmp_path: Path):
    path = tmp_path / "old.cmm"
    path.write_text(json.dumps({"format": "chemanim-linear-nodes", "version": 1}), encoding="utf-8")
    try:
        load_project(path)
    except ValueError as error:
        assert "原生二维 v2" in str(error)
    else:
        raise AssertionError("v1 should not be silently accepted")
