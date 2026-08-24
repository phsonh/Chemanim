from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

from PIL import Image

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


def test_atom_hit_normalizes_bond_origin_at_offsets_viewports_and_zoom():
    offsets = [(1, 0), (-3, 4), (0, -8), (9, 7), (-12, 0)]
    viewports = [(960, 540, 24, 0, 0), (1280, 720, 48, 2.5, -1.25), (1920, 1080, 96, -3, 2)]
    for width, height, scale, center_x, center_y in viewports:
        for dx, dy in offsets:
            core = CoreSession(); core.add_blank_molecule(); core.set_viewport(width, height, scale, center_x, center_y)
            origin = (width * .5 - center_x * scale, height * .5 + center_y * scale)
            gesture(core, "atom_label", origin)
            core.set_tool("single_bond")
            core.pointer_down(origin[0] + dx, origin[1] + dy)
            core.pointer_move(origin[0] + 2 * scale, origin[1])
            core.pointer_up(origin[0] + 2 * scale, origin[1])
            first, second = atoms(core)
            assert first["y"] == second["y"]


def test_clicking_each_benzene_vertex_places_substituent_outside_ring():
    core = session(); gesture(core, "benzene", (480, 270)); ring_atoms = list(atoms(core)); ring_bonds = list(bonds(core))
    center_x = sum(atom["x"] for atom in ring_atoms) / 6
    center_y = sum(atom["y"] for atom in ring_atoms) / 6
    for atom in ring_atoms:
        before = {item["id"] for item in atoms(core)}
        point = canvas_point(core, atom["id"])
        core.set_tool("single_bond"); core.pointer_down(*point); core.pointer_up(*point)
        endpoint = next(item for item in atoms(core) if item["id"] not in before)
        outward = ((endpoint["x"] - atom["x"]) * (atom["x"] - center_x) +
                   (endpoint["y"] - atom["y"]) * (atom["y"] - center_y))
        assert outward > 0
        def side(a, b, c): return ((b["x"] - a["x"]) * (c["y"] - a["y"]) -
                                  (b["y"] - a["y"]) * (c["x"] - a["x"]))
        for bond in ring_bonds:
            if atom["id"] in (bond["a"], bond["b"]): continue
            first = next(item for item in ring_atoms if item["id"] == bond["a"])
            second = next(item for item in ring_atoms if item["id"] == bond["b"])
            assert side(atom, endpoint, first) * side(atom, endpoint, second) >= -1e-12


def test_clicking_ring_bond_fuses_on_empty_side_and_preserves_shared_bond():
    core = session(); gesture(core, "benzene", (480, 270))
    original_atoms = list(atoms(core)); original_bonds = list(bonds(core))
    center = (sum(atom["x"] for atom in original_atoms) / 6,
              sum(atom["y"] for atom in original_atoms) / 6)
    shared = original_bonds[0]
    first = next(atom for atom in original_atoms if atom["id"] == shared["a"])
    second = next(atom for atom in original_atoms if atom["id"] == shared["b"])
    midpoint = ((first["x"] + second["x"]) * .5, (first["y"] + second["y"]) * .5)
    transform = core.depict(False)["transform"]
    click = (transform["origin"]["x"] + midpoint[0] * transform["pixels_per_unit"],
             transform["origin"]["y"] - midpoint[1] * transform["pixels_per_unit"])
    gesture(core, "ring6", click)

    new_atoms = [atom for atom in atoms(core) if atom["id"] not in {item["id"] for item in original_atoms}]
    new_center = (sum(atom["x"] for atom in new_atoms) / len(new_atoms),
                  sum(atom["y"] for atom in new_atoms) / len(new_atoms))
    assert ((new_center[0] - midpoint[0]) * (center[0] - midpoint[0]) +
            (new_center[1] - midpoint[1]) * (center[1] - midpoint[1])) < 0
    restored_shared = next(bond for bond in bonds(core) if bond["id"] == shared["id"])
    assert restored_shared["type"] == shared["type"]
    assert len(bonds(core)) == len(original_bonds) + 5


def test_blank_bond_uses_15_degree_snap_and_alt_disables_it():
    core = session(); start = (200.0, 200.0); angle = math.radians(22)
    end = (start[0] + 100 * math.cos(angle), start[1] - 100 * math.sin(angle))
    core.set_tool("single_bond"); core.pointer_down(*start); core.pointer_move(*end); core.pointer_up(*end)
    first, second = atoms(core); snapped = math.degrees(math.atan2(second["y"] - first["y"], second["x"] - first["x"]))
    assert abs(snapped - 15) < 1e-9

    free = session(); free.set_tool("single_bond"); free.pointer_down(*start, True); free.pointer_move(*end, True); free.pointer_up(*end, True)
    first, second = atoms(free); unsnapped = math.degrees(math.atan2(second["y"] - first["y"], second["x"] - first["x"]))
    assert abs(unsnapped - 22) < 1e-9


def double_bond_count(svg: str) -> int:
    classes = re.findall(r"class='bond-(\d+)[^']*'", svg)
    return sum(classes.count(bond) >= 2 for bond in set(classes))


def test_aromatic_smiles_and_aromatic_tool_draw_kekule_bonds_without_dashes():
    imported = CoreSession(); imported.import_smiles("benzene", "c1ccccc1"); imported.set_viewport(960, 540, 48, 0, 0)
    imported_svg = imported.depict(False)["svg"]
    assert "stroke-dasharray" not in imported_svg
    assert double_bond_count(imported_svg) == 3

    manual = session(); gesture(manual, "ring6", (480, 270))
    for bond in list(bonds(manual)):
        first = next(atom for atom in atoms(manual) if atom["id"] == bond["a"])
        second = next(atom for atom in atoms(manual) if atom["id"] == bond["b"])
        midpoint = ((first["x"] + second["x"]) * .5, (first["y"] + second["y"]) * .5)
        canvas = manual.depict(False)["transform"]
        point = (canvas["origin"]["x"] + midpoint[0] * canvas["pixels_per_unit"],
                 canvas["origin"]["y"] - midpoint[1] * canvas["pixels_per_unit"])
        gesture(manual, "aromatic_bond", point)
    manual_svg = manual.depict(False)["svg"]
    assert "stroke-dasharray" not in manual_svg
    assert double_bond_count(manual_svg) == 3


def test_view_zoom_is_one_uniform_svg_transform():
    core = CoreSession(); core.import_smiles("charged", "C[NH2+]C(=O)O");
    measurements = []
    for scale in (24, 48, 96):
        core.set_viewport(960, 540, scale, 0, 0)
        drawing = core.depict(False); atom_points = drawing["atoms"]
        distance_px = math.dist((atom_points[0]["center"]["x"], atom_points[0]["center"]["y"]),
                                (atom_points[1]["center"]["x"], atom_points[1]["center"]["y"]))
        viewbox = [float(value) for value in re.search(r"viewBox='([^']+)'", drawing["svg"]).group(1).split()]
        measurements.append((distance_px, viewbox[2]))
    assert abs(measurements[1][0] / measurements[0][0] - 2) < 1e-9
    assert abs(measurements[2][0] / measurements[0][0] - 4) < 1e-9
    assert abs(measurements[0][1] / measurements[1][1] - 2) < 1e-9
    assert abs(measurements[0][1] / measurements[2][1] - 4) < 1e-9


def test_view_zoom_scales_font_and_stroke_with_bonds():
    label = CoreSession(); label.import_smiles("ammonium", "[NH4+]")
    bond = CoreSession(); bond.import_smiles("ethane", "CC")
    label_boxes, bond_lengths, effective_strokes = [], [], []
    for scale in (48, 96, 192):
        label.set_viewport(960, 540, scale, 0, 0)
        label_image = Image.frombytes("RGBA", (960, 540), label.depict(True)["rgba"])
        box = label_image.getchannel("A").getbbox()
        assert box is not None
        label_boxes.append((box[2] - box[0], box[3] - box[1]))

        bond.set_viewport(960, 540, scale, 0, 0)
        drawing = bond.depict(False)
        first, second = drawing["atoms"]
        bond_lengths.append(math.dist((first["center"]["x"], first["center"]["y"]),
                                      (second["center"]["x"], second["center"]["y"])))
        viewbox_width = float(re.search(r"viewBox='([^']+)'", drawing["svg"]).group(1).split()[2])
        canonical_stroke = float(re.search(r"stroke-width:([0-9.]+)px", drawing["svg"]).group(1))
        effective_strokes.append(canonical_stroke * 960 / viewbox_width)

    for values in (bond_lengths, effective_strokes):
        assert abs(values[1] / values[0] - 2) < 1e-9
        assert abs(values[2] / values[0] - 4) < 1e-9
    for dimension in (0, 1):
        assert abs(label_boxes[1][dimension] / label_boxes[0][dimension] - 2) < 0.03
        assert abs(label_boxes[2][dimension] / label_boxes[0][dimension] - 4) < 0.04


def test_official_rdkit_acs_pixel_regression():
    env = os.environ.copy()
    env["QT_QPA_PLATFORM"] = "offscreen"
    subprocess.run([sys.executable, str(ROOT / "tools" / "generate_acs_correctness_gallery.py")],
                   cwd=ROOT, env=env, check=True)
    report = json.loads((ROOT / "media" / "correctness" / "acs_comparison.json").read_text(encoding="utf-8"))
    assert set(report["molecules"]) == {
        "benzene", "acetaminophen", "ibuprofen_wedge", "charged_heteroatoms",
        "azulene", "hexaphenylbenzene", "phthalocyanine", "porphyrin",
    }
    for result in report["molecules"].values():
        assert result["qt_iou"] >= 0.90
        assert result["nanosvg_iou"] >= 0.90
