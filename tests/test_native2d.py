from __future__ import annotations

import json
import math
import os
from pathlib import Path
import re
import subprocess
import sys

from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from chemanim2d.core import CoreSession


def session() -> CoreSession:
    result = CoreSession(); result.add_blank_molecule("manual"); result.set_viewport(960, 540, 1, 0, 0)
    authorize_structure(result)
    return result


def authorize_structure(core: CoreSession):
    node = next((item for item in reversed(core.project()["nodes"])
                 if item["type"] == "molecule_set_structure" and
                 item.get("params", {}).get("target") == core.active_molecule), None)
    if node is None:
        node_id = core.add_node("molecule_set_structure",
                                json.dumps({"target": core.active_molecule}))
        node = next(item for item in core.project()["nodes"] if item["id"] == node_id)
    core.edit_node(node["id"])
    assert core.edit_target_kind == "structure_snapshot" and core.can_edit_structure
    return node["id"]


def gesture(core: CoreSession, tool: str, start, end=None):
    core.set_tool(tool); end = end or start
    core.pointer_down(*start); core.pointer_move(*end); return core.pointer_up(*end)


def structure_for(core: CoreSession,target: str):
    project=core.project()
    current=next((item for item in project["nodes"] if item["id"]==core.edit_target_id),None)
    if current and current["type"] in ("molecule_set_structure","molecule_gradient_structure") and current.get("params",{}).get("target")==target:
        return current["params"]["end_snapshot" if current["type"]=="molecule_gradient_structure" else "snapshot"]
    node=next(item for item in reversed(project["nodes"])
              if item["type"] in ("molecule_set_structure","molecule_gradient_structure") and item.get("params",{}).get("target")==target)
    return node["params"]["end_snapshot" if node["type"]=="molecule_gradient_structure" else "snapshot"]


def structure(core: CoreSession):
    project=core.project();target=core.active_molecule
    current=next((item for item in project["nodes"] if item["id"]==core.edit_target_id),None)
    if current and current["type"] in ("molecule_set_structure","molecule_gradient_structure"):
        return current["params"]["end_snapshot" if current["type"]=="molecule_gradient_structure" else "snapshot"]
    node=next(item for item in reversed(project["nodes"])
              if item["type"]=="molecule_set_structure" and item.get("params",{}).get("target")==target)
    return node["params"]["snapshot"]


def atoms(core: CoreSession): return structure(core)["atoms"]
def bonds(core: CoreSession): return structure(core)["bonds"]
def adornments(core: CoreSession): return structure(core)["adornments"]


def canvas_point(core: CoreSession, atom_id: str):
    depiction = core.depict(False)
    point = next(item["center"] for item in depiction["atoms"] if item["id"] == atom_id)
    return point["x"], point["y"]


def test_structure_commands_are_sealed_by_explicit_structure_node_context():
    core=CoreSession();core.add_blank_molecule("sealed");core.set_viewport(960,540,1,0,0)
    create=next(node for node in core.project()["nodes"] if node["type"]=="molecule_create")
    assert core.edit_target_kind=="script_node" and core.edit_target_id==create["id"] and not core.can_edit_structure
    gesture(core,"single_bond",(420,270),(452,270));assert not core.project()["molecules"][0]["atoms"]
    authorize_structure(core)
    gesture(core,"single_bond",(420,270),(452,270));atom_id=atoms(core)[0]["id"]
    original=(atoms(core)[0]["x"],atoms(core)[0]["y"])

    core.select_all();core.preview_timeline(0)
    assert core.edit_target_kind=="timeline_preview" and not core.can_edit_structure
    assert not core.delete_selection()
    assert not core.set_atom_position(atom_id,99,99)
    assert (atoms(core)[0]["x"],atoms(core)[0]["y"])==original
    core.set_tool("eraser");point=canvas_point(core,atom_id);core.pointer_down(*point);core.pointer_up(*point)
    assert atoms(core)[0]["alive"]
    assert not core.undo()


def test_authoring_undo_is_available_only_after_returning_to_a_node():
    core=CoreSession();core.add_blank_molecule("nodes")
    wait=core.add_node("wait",json.dumps({"frames":12}))
    core.preview_timeline(4);assert not core.undo()
    core.edit_node(wait);assert core.edit_target_kind=="script_node" and core.undo()
    assert all(node["id"]!=wait for node in core.project()["nodes"])


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
    assert sum(atom["label"] == "O" for atom in atoms(core)) == 2
    assert sum(atom["label"] == "N" for atom in atoms(core)) == 1
    assert any(bond["type"] == "double" for bond in bonds(core))
    assert "explicit-visual-bonds" in core.depict(False)["svg"]


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
    assert sum(atom["label"] == "O" for atom in atoms(core)) == 2
    assert sum(bond["type"] == "double" for bond in bonds(core)) >= 4


def test_stable_ids_survive_save_close_reopen_and_are_not_reused(tmp_path: Path):
    core = session(); gesture(core, "ring5", (480, 270)); before = core.project(); path = tmp_path / "roundtrip.cmm"; core.save(str(path))
    restored = CoreSession(); restored.load(str(path)); assert restored.project()["molecules"][0]["atoms"] == before["molecules"][0]["atoms"]
    authorize_structure(restored)
    restored.set_viewport(960, 540, 48, 0, 0); removed = atoms(restored)[-1]["id"]
    gesture(restored, "eraser", canvas_point(restored, removed)); gesture(restored, "atom_label", (700, 400))
    assert atoms(restored)[-1]["id"] != removed


def test_project_overwrite_and_molecule_ids_continue_after_reopen(tmp_path: Path):
    core = CoreSession(); assert core.add_blank_molecule() == "molecule1"
    path = tmp_path / "overwrite.cmm"; core.save(str(path)); core.save(str(path))
    restored = CoreSession(); restored.load(str(path))
    assert restored.add_blank_molecule() == "molecule2"


def test_tween_target_drag_does_not_modify_base_structure():
    core = CoreSession(); core.import_smiles("ethanol", "CCO"); core.set_viewport(960, 540, 48, 0, 0)
    atom = atoms(core)[-1]; original = (atom["x"], atom["y"]);base=structure(core)
    core.add_node("wait", json.dumps({"frames": 10}))
    tween = core.add_node("atom_lerp_xy", json.dumps({"target": core.active_molecule, "atom": atom["id"], "x": atom["x"] + 2, "y": atom["y"], "frames": 30, "easing": "linear"}))
    core.edit_node(tween)
    point = canvas_point(core, atom["id"]); core.pointer_down(*point); core.pointer_move(point[0], point[1] - 40); assert core.pointer_up(point[0], point[1] - 40)["changed"]
    after = next(item for item in base["atoms"] if item["id"] == atom["id"])
    assert (after["x"], after["y"]) == original
    node = next(item for item in core.project()["nodes"] if item["id"] == tween)
    assert node["params"]["y"] != original[1]


def test_later_overlapping_tween_starts_from_current_state():
    core = CoreSession(); core.import_smiles("ethanol", "CCO"); core.set_viewport(960, 540, 48, 0, 0)
    atom = atoms(core)[-1]
    core.add_node("atom_lerp_xy", json.dumps({"target": core.active_molecule, "atom": atom["id"], "x": atom["x"] + 6, "y": atom["y"], "frames": 60, "easing": "linear"}))
    core.add_node("wait", json.dumps({"frames": 30}))
    core.add_node("atom_lerp_xy", json.dumps({"target": core.active_molecule, "atom": atom["id"], "x": atom["x"] - 2, "y": atom["y"], "frames": 30, "easing": "linear"}))
    d29 = core.depict_at(29); d30 = core.depict_at(30)
    p29 = next(item["center"] for item in d29["atoms"] if item["id"] == atom["id"])
    p30 = next(item["center"] for item in d30["atoms"] if item["id"] == atom["id"])
    assert abs(p30["x"] - p29["x"]) < 10


def test_linear_nodes_are_the_only_serialized_authoring_timeline(tmp_path: Path):
    core = CoreSession(); molecule = core.add_blank_molecule("authoring")
    move = core.add_node("molecule_lerp_position", json.dumps({"target": molecule, "x": 120, "y": -40, "frames": 60, "easing": "linear"}))
    wait = core.add_node("wait", json.dumps({"frames": 30}))
    alpha = core.add_node("molecule_lerp_alpha", json.dumps({"target": molecule, "value": 0, "frames": 30, "easing": "linear"}))
    project = core.project()
    assert "timeline" not in project
    timings = {item["id"]: item for item in core.node_timings()}
    assert timings[move]["start"] == 0 and timings[move]["end"] == 60
    assert timings[wait]["start"] == 0 and timings[wait]["end"] == 30
    assert timings[alpha]["start"] == 30 and timings[alpha]["end"] == 60
    path = tmp_path / "nodes.cmm"; core.save(str(path)); raw = json.loads(path.read_text(encoding="utf-8"))
    assert [node["id"] for node in raw["nodes"]] == [node["id"] for node in project["nodes"]]
    assert "timeline" not in raw


def test_reordering_nodes_recompiles_typed_track_timing():
    core = CoreSession(); core.add_blank_molecule("order")
    first = core.add_node("wait", json.dumps({"frames": 20}))
    second = core.add_node("wait", json.dumps({"frames": 40}))
    lerp = core.add_node("molecule_lerp_position", "{}")
    assert next(item for item in core.node_timings() if item["id"] == lerp)["start"] == 60
    core.move_node(second, len(core.project()["nodes"])-1)
    assert next(item for item in core.node_timings() if item["id"] == lerp)["start"] == 20
    scene=core.project()["nodes"][0]["id"]
    assert not core.move_node(scene,3) and not core.delete_node(scene)


def test_all_object_nodes_are_kept_after_their_creation_boundary():
    for node_type,params in (
        ("molecule_set_structure",{}),("molecule_set_alpha",{"value":128}),
        ("molecule_set_position",{"x":10,"y":20}),
        ("molecule_lerp_scale",{"value":2,"frames":15,"easing":"linear"}),
        ("molecule_gradient_structure",{"frames":15,"easing":"linear"}),
        ("molecule_delete",{})):
        core=CoreSession();target=core.import_smiles("苯","c1ccccc1");nodes=core.project()["nodes"]
        create_index=next(index for index,node in enumerate(nodes) if node["type"]=="molecule_create")
        node=core.add_node(node_type,json.dumps({"target":target,**params}));before=[item["id"] for item in core.project()["nodes"]]
        assert not core.move_node(node,create_index)
        assert [item["id"] for item in core.project()["nodes"]]==before
    core=CoreSession();created=core.add_node("arrow_new",json.dumps({"target":"arrow1"}));curve=core.add_node("arrow_set_curve",json.dumps({"target":"arrow1"}))
    create_index=next(index for index,node in enumerate(core.project()["nodes"]) if node["id"]==created);before=[node["id"] for node in core.project()["nodes"]]
    assert not core.move_node(curve,create_index) and [node["id"] for node in core.project()["nodes"]]==before


def test_object_nodes_cannot_be_moved_past_their_delete_boundary():
    core=CoreSession();target=core.import_smiles("苯","c1ccccc1");alpha=core.add_node("molecule_set_alpha",json.dumps({"target":target,"value":128}));deleted=core.add_node("molecule_delete",json.dumps({"target":target}));nodes=core.project()["nodes"]
    alpha_index=next(index for index,node in enumerate(nodes) if node["id"]==alpha);delete_index=next(index for index,node in enumerate(nodes) if node["id"]==deleted);before=[node["id"] for node in nodes]
    assert not core.move_node(deleted,alpha_index) and not core.move_node(alpha,delete_index)
    assert [node["id"] for node in core.project()["nodes"]]==before


def test_new_and_pasted_object_nodes_are_clamped_inside_the_lifecycle():
    core=CoreSession();target=core.import_smiles("苯","c1ccccc1");deleted=core.add_node("molecule_delete",json.dumps({"target":target}));alpha=core.add_node("molecule_set_alpha",json.dumps({"target":target,"value":128}),1)
    nodes=core.project()["nodes"];indexes={node["id"]:index for index,node in enumerate(nodes)};created=next(node["id"] for node in nodes if node["type"]=="molecule_create")
    assert indexes[created]<indexes[alpha]<indexes[deleted]
    structure=next(node for node in nodes if node["type"]=="molecule_set_structure");other=core.add_blank_molecule("另一个分子")
    copied=core.duplicate_node(structure["id"],1);copied_node=next(node for node in core.project()["nodes"] if node["id"]==copied)
    assert copied_node["params"]["target"]==target and copied_node["params"]["snapshot"]==structure["params"]["snapshot"]


def test_benzene_explicit_types_and_secondary_sides_survive_substitution_motion_and_reopen(tmp_path: Path):
    core = session(); gesture(core, "benzene", (480, 270))
    ring_atoms = list(atoms(core)); original = {bond["id"]: (bond["type"],bond["secondary_line_side"]) for bond in bonds(core)}
    assert [value[0] for value in original.values()].count("double") == 3
    for atom in ring_atoms:
        point = canvas_point(core, atom["id"]); core.set_tool("single_bond"); core.pointer_down(*point); core.pointer_up(*point)
        current = {bond["id"]: (bond["type"],bond["secondary_line_side"]) for bond in bonds(core) if bond["id"] in original}
        assert current == original
    core.set_atom_position(ring_atoms[0]["id"], ring_atoms[0]["x"]+.2, ring_atoms[0]["y"]-.1)
    path=tmp_path/"stable-benzene.cmm";core.save(str(path));restored=CoreSession();restored.load(str(path))
    authorize_structure(restored);current={bond["id"]:(bond["type"],bond["secondary_line_side"]) for bond in bonds(restored) if bond["id"] in original}
    assert current==original


def test_imported_pyridine_is_flattened_to_explicit_bonds_and_persisted(tmp_path: Path):
    core=CoreSession();core.import_smiles("pyridine","n1ccccc1")
    explicit={bond["id"]:(bond["type"],bond["secondary_line_side"]) for bond in bonds(core)}
    assert len(explicit)==6 and [value[0] for value in explicit.values()].count("double")==3
    path=tmp_path/"pyridine.cmm";core.save(str(path));restored=CoreSession();restored.load(str(path))
    authorize_structure(restored);reopened={bond["id"]:(bond["type"],bond["secondary_line_side"]) for bond in bonds(restored)}
    assert reopened==explicit


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
    assert first == moved == {"origin": {"x": 480.0, "y": 270.0}, "pixels_per_unit": 1.0}


def test_atom_hit_normalizes_bond_origin_at_offsets_viewports_and_zoom():
    offsets = [(1, 0), (-3, 4), (0, -8), (9, 7), (-12, 0)]
    viewports = [(960, 540, 24, 0, 0), (1280, 720, 48, 2.5, -1.25), (1920, 1080, 96, -3, 2)]
    for width, height, scale, center_x, center_y in viewports:
        for dx, dy in offsets:
            core = CoreSession(); core.add_blank_molecule(); core.set_viewport(width, height, scale, center_x, center_y); authorize_structure(core)
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
            assert side(atom, endpoint, first) * side(atom, endpoint, second) >= -1e-8


def test_clicking_ring_bond_fuses_on_empty_side_and_preserves_shared_bond():
    core = session(); gesture(core, "benzene", (480, 270))
    original_atoms = list(atoms(core)); original_bonds = list(bonds(core))
    center = (sum(atom["x"] for atom in original_atoms) / 6,
              sum(atom["y"] for atom in original_atoms) / 6)
    shared = original_bonds[0]
    first = next(atom for atom in original_atoms if atom["id"] == shared["a"])
    second = next(atom for atom in original_atoms if atom["id"] == shared["b"])
    midpoint = ((first["x"] + second["x"]) * .5, (first["y"] + second["y"]) * .5)
    first_canvas,second_canvas=canvas_point(core,first["id"]),canvas_point(core,second["id"])
    click=((first_canvas[0]+second_canvas[0])*.5,(first_canvas[1]+second_canvas[1])*.5)
    gesture(core, "ring5", click)

    new_atoms = [atom for atom in atoms(core) if atom["id"] not in {item["id"] for item in original_atoms}]
    new_center = (sum(atom["x"] for atom in new_atoms) / len(new_atoms),
                  sum(atom["y"] for atom in new_atoms) / len(new_atoms))
    assert ((new_center[0] - midpoint[0]) * (center[0] - midpoint[0]) +
            (new_center[1] - midpoint[1]) * (center[1] - midpoint[1])) < 0
    restored_shared = next(bond for bond in bonds(core) if bond["id"] == shared["id"])
    assert restored_shared["type"] == shared["type"]
    by_id={atom["id"]:atom for atom in atoms(core)}
    shared_length=math.dist((first["x"],first["y"]),(second["x"],second["y"]))
    new_edges=bonds(core)[len(original_bonds):]
    assert len(new_atoms)==3 and len(new_edges)==4
    for edge in new_edges:
        a,b=by_id[edge["a"]],by_id[edge["b"]]
        assert abs(math.dist((a["x"],a["y"]),(b["x"],b["y"]))-shared_length)<1e-8
    assert len(bonds(core)) == len(original_bonds) + 4


def test_clicking_five_ring_bond_creates_regular_fused_eight_ring():
    core=session();gesture(core,"ring5",(480,270))
    original_atoms=list(atoms(core));original_bonds=list(bonds(core));shared=original_bonds[0]
    by_id={atom["id"]:atom for atom in original_atoms};first,second=by_id[shared["a"]],by_id[shared["b"]]
    midpoint=((first["x"]+second["x"])*.5,(first["y"]+second["y"])*.5)
    first_canvas,second_canvas=canvas_point(core,first["id"]),canvas_point(core,second["id"])
    click=((first_canvas[0]+second_canvas[0])*.5,(first_canvas[1]+second_canvas[1])*.5)
    gesture(core,"ring8",click)
    current_atoms=atoms(core);current_bonds=bonds(core);by_id={atom["id"]:atom for atom in current_atoms}
    new_atoms=[atom for atom in current_atoms if atom["id"] not in {item["id"] for item in original_atoms}]
    new_edges=current_bonds[len(original_bonds):]
    shared_length=math.dist((first["x"],first["y"]),(second["x"],second["y"]))
    assert len(new_atoms)==6 and len(new_edges)==7
    assert all(abs(math.dist((by_id[edge["a"]]["x"],by_id[edge["a"]]["y"]),(by_id[edge["b"]]["x"],by_id[edge["b"]]["y"]))-shared_length)<1e-8 for edge in new_edges)


def test_blank_bond_uses_15_degree_snap_and_alt_disables_it():
    core = session(); start = (200.0, 200.0); angle = math.radians(22)
    end = (start[0] + 100 * math.cos(angle), start[1] - 100 * math.sin(angle))
    core.set_tool("single_bond"); core.pointer_down(*start); core.pointer_move(*end); core.pointer_up(*end)
    first, second = atoms(core); snapped = math.degrees(math.atan2(second["y"] - first["y"], second["x"] - first["x"]))
    assert abs(snapped - 15) < 1e-9

    free = session(); free.set_tool("single_bond"); free.pointer_down(*start, True); free.pointer_move(*end, True); free.pointer_up(*end, True)
    first, second = atoms(free); unsnapped = math.degrees(math.atan2(second["y"] - first["y"], second["x"] - first["x"]))
    assert abs(unsnapped - 22) < 1e-9


def test_single_bond_tool_click_cycles_single_double_triple_single():
    core=session();gesture(core,"single_bond",(420,270),(500,270));bond=bonds(core)[0]
    midpoint=((canvas_point(core,bond["a"])[0]+canvas_point(core,bond["b"])[0])*.5,
              (canvas_point(core,bond["a"])[1]+canvas_point(core,bond["b"])[1])*.5)
    observed=[]
    for _ in range(3):
        gesture(core,"single_bond",midpoint);observed.append(bonds(core)[0]["type"])
    assert observed==["double","triple","single"]


def test_single_bond_click_on_blank_creates_ethane_skeleton_and_undoes_to_blank():
    core=session();core.set_tool("single_bond");core.pointer_down(420,270);result=core.pointer_up(420,270)
    live_atoms=atoms(core);live_bonds=bonds(core)
    assert result["changed"] and len(live_atoms)==2 and len(live_bonds)==1
    assert live_bonds[0]["type"]=="single"
    angle=math.degrees(math.atan2(live_atoms[1]["y"]-live_atoms[0]["y"],live_atoms[1]["x"]-live_atoms[0]["x"]))
    assert abs(angle-30.0)<1e-9
    assert math.isclose(math.hypot(live_atoms[1]["x"]-live_atoms[0]["x"],live_atoms[1]["y"]-live_atoms[0]["y"]),32.0,abs_tol=1e-12)
    assert result["selected_atoms"]==[] and result["selected_bonds"]==[]
    assert core.undo() and not atoms(core) and not bonds(core)
    assert core.redo() and len(atoms(core))==2 and len(bonds(core))==1


def test_hover_follows_pointer_without_selecting_finished_structure():
    core=session();core.set_tool("single_bond");core.pointer_down(420,270);core.pointer_up(420,270)
    drawing=core.depict(False);atom_point=drawing["atoms"][0]["center"];bond=drawing["bonds"][0]
    over_atom=core.pointer_move(atom_point["x"],atom_point["y"])
    over_bond=core.pointer_move((bond["first"]["x"]+bond["second"]["x"])*.5,(bond["first"]["y"]+bond["second"]["y"])*.5)
    away=core.pointer_move(20,20)
    assert over_atom["hover"]["kind"]=="atom"
    assert over_bond["hover"]["kind"]=="bond"
    assert away["hover"]["kind"]=="none"
    assert over_atom["selected_atoms"]==away["selected_atoms"]==[]


def test_double_bond_tool_cycles_persistent_visual_side_only():
    core=session();gesture(core,"double_bond",(420,270),(452,270))
    bond=bonds(core)[0]
    assert (bond["type"],bond["secondary_line_side"])==("double","center")
    for expected in ("left","right","center"):
        drawing=core.depict(False);visual=drawing["bonds"][0]
        midpoint=((visual["first"]["x"]+visual["second"]["x"])*.5,
                  (visual["first"]["y"]+visual["second"]["y"])*.5)
        gesture(core,"double_bond",midpoint)
        bond=bonds(core)[0]
        assert bond["type"]=="double" and bond["stereo"]=="none"
        assert bond["secondary_line_side"]==expected
    assert core.undo() and bonds(core)[0]["secondary_line_side"]=="right"


def test_depiction_exposes_all_strokes_for_double_and_triple_highlight():
    core=session();gesture(core,"double_bond",(420,250),(452,250));gesture(core,"triple_bond",(420,300),(452,300))
    drawing=core.depict(False);visual={bond["id"]:bond for bond in drawing["bonds"]}
    model={bond["id"]:bond for bond in bonds(core)}
    double=next(visual[key] for key,value in model.items() if value["type"]=="double")
    triple=next(visual[key] for key,value in model.items() if value["type"]=="triple")
    assert double["type"]=="double" and double["secondary_line_side"]=="center"
    assert triple["type"]=="triple"
    assert double["line_spacing"]>0 and triple["line_spacing"]==double["line_spacing"]


def test_multiple_bond_hit_testing_follows_visible_offset_strokes_at_high_zoom():
    core=session();core.set_viewport(960,540,3,0,0)
    gesture(core,"double_bond",(400,230),(496,230));drawing=core.depict(False);double=drawing["bonds"][0]
    midpoint=((double["first"]["x"]+double["second"]["x"])*.5,
              (double["first"]["y"]+double["second"]["y"])*.5)
    gesture(core,"double_bond",midpoint);double=core.depict(False)["bonds"][0]
    dx=double["second"]["x"]-double["first"]["x"]
    dy=double["second"]["y"]-double["first"]["y"]
    length=math.hypot(dx,dy);normal=(-dy/length,dx/length)
    # Left in model coordinates is the negative screen normal.
    secondary=(midpoint[0]-normal[0]*double["line_spacing"],
               midpoint[1]-normal[1]*double["line_spacing"])
    assert core.hit_test(*secondary)["id"]==double["id"]

    gesture(core,"triple_bond",(400,330),(496,330));triple=core.depict(False)["bonds"][-1]
    midpoint=((triple["first"]["x"]+triple["second"]["x"])*.5,
              (triple["first"]["y"]+triple["second"]["y"])*.5)
    dx=triple["second"]["x"]-triple["first"]["x"]
    dy=triple["second"]["y"]-triple["first"]["y"]
    length=math.hypot(dx,dy);normal=(-dy/length,dx/length)
    outer=(midpoint[0]+normal[0]*triple["line_spacing"],
           midpoint[1]+normal[1]*triple["line_spacing"])
    assert core.hit_test(*outer)["id"]==triple["id"]


def test_acs_visual_primitives_use_flat_secondary_caps_and_five_hash_wedge_bars():
    double=session();gesture(double,"double_bond",(420,250),(452,250))
    visual=double.depict(False)["bonds"][0]
    midpoint=((visual["first"]["x"]+visual["second"]["x"])*.5,
              (visual["first"]["y"]+visual["second"]["y"])*.5)
    gesture(double,"double_bond",midpoint)
    group=double.depict(False)["svg"].split("<g id='explicit-visual-bonds'>",1)[1].split("</g>",1)[0]
    assert group.count("stroke-linecap='butt'")==1

    hashed=session();gesture(hashed,"dashed_wedge",(420,250),(452,250))
    group=hashed.depict(False)["svg"].split("<g id='explicit-visual-bonds'>",1)[1].split("</g>",1)[0]
    assert group.count("<path")==5 and group.count("stroke-linecap='butt'")==5

    wavy=session();gesture(wavy,"wavy_bond",(420,250),(452,250))
    group=wavy.depict(False)["svg"].split("<g id='explicit-visual-bonds'>",1)[1].split("</g>",1)[0]
    assert group.count(" L ")>=64 and "stroke-linejoin='round'" in group


def test_equal_width_solid_and_hashed_bonds_are_distinct_persistent_styles(tmp_path: Path):
    solid=session();gesture(solid,"solid_bar",(420,250),(452,250))
    assert bonds(solid)[0]["stereo"]=="solid_bar"
    group=solid.depict(False)["svg"].split("<g id='explicit-visual-bonds'>",1)[1].split("</g>",1)[0]
    assert " Z' fill='" in group

    hashed=session();gesture(hashed,"hashed_bar",(420,250),(452,250))
    assert bonds(hashed)[0]["stereo"]=="hashed_bar"
    group=hashed.depict(False)["svg"].split("<g id='explicit-visual-bonds'>",1)[1].split("</g>",1)[0]
    segments=re.findall(r"M ([\d.e+-]+),([\d.e+-]+) L ([\d.e+-]+),([\d.e+-]+)",group)
    lengths=[math.dist((float(x1),float(y1)),(float(x2),float(y2))) for x1,y1,x2,y2 in segments]
    assert len(lengths)==6 and max(lengths)-min(lengths)<1e-7
    path=tmp_path/"bars.cmm";hashed.save(str(path));restored=CoreSession();restored.load(str(path))
    authorize_structure(restored);assert bonds(restored)[0]["stereo"]=="hashed_bar"


def test_solid_bar_fills_its_root_only_when_joined_to_other_bonds():
    joined=session();gesture(joined,"single_bond",(480,270),(448,252));root=atoms(joined)[0]
    root_point=canvas_point(joined,root["id"]);gesture(joined,"single_bond",root_point,(448,288))
    gesture(joined,"solid_bar",root_point,(512,270));bar=bonds(joined)[-1]
    svg=joined.depict(False)["svg"]
    path=re.search(rf"<path class='solid-bar bond-{bar['id']}' d='([^']+)'",svg)
    assert path and path.group(1).count(" L ")==3  # full rectangle is not cut down
    assert svg.count(f"class='solid-bar-junction bond-{bar['id']}'")==2

    reversed_bar=session();gesture(reversed_bar,"single_bond",(480,270),(448,252));root=atoms(reversed_bar)[0]
    root_point=canvas_point(reversed_bar,root["id"]);gesture(reversed_bar,"single_bond",root_point,(448,288))
    gesture(reversed_bar,"solid_bar",(512,270),root_point);bar=bonds(reversed_bar)[-1]
    svg=reversed_bar.depict(False)["svg"]
    path=re.search(rf"<path class='solid-bar bond-{bar['id']}' d='([^']+)'",svg)
    assert path and path.group(1).count(" L ")==3
    assert svg.count(f"class='solid-bar-junction bond-{bar['id']}'")==2

    isolated=session();gesture(isolated,"solid_bar",(420,250),(452,250));bar=bonds(isolated)[0]
    svg=isolated.depict(False)["svg"]
    path=re.search(rf"<path class='solid-bar bond-{bar['id']}' d='([^']+)'",svg)
    assert path and path.group(1).count(" L ")==3  # flat-ended rectangle
    assert f"class='solid-bar-junction bond-{bar['id']}'" not in svg


def test_centered_double_bond_keeps_chemdraw_geometry_without_rdkit_junction_patches():
    core=session();gesture(core,"double_bond",(420,270),(452,270))
    bond=bonds(core)[0]
    first=canvas_point(core,bond["a"]);second=canvas_point(core,bond["b"])
    gesture(core,"single_bond",first,(first[0]-28,first[1]+20))
    gesture(core,"single_bond",second,(second[0]+28,second[1]-20))
    drawing=core.depict(False);visual=next(item for item in drawing["bonds"] if item["id"]==bond["id"])
    assert sum(value<0 for value in visual["first_extensions"])==1
    assert sum(value>0 for value in visual["second_extensions"])==1
    group=drawing["svg"].split("<g id='explicit-visual-bonds'>",1)[1].split("</g>",1)[0]
    assert group.count("stroke-linecap='butt'")==2
    paths=re.findall(r"<path d='([^']+)'",group)
    assert len(paths)>=4 and [path.count(" L ") for path in paths[:2]]==[1,1]
    tail=drawing["svg"].split("</g>",2)[-1]
    assert not re.search(r"<path(?![^>]*class=)",tail)


def test_explicit_double_bond_is_clipped_outside_hetero_atom_label():
    core=session();gesture(core,"atom_label",(480,300));start=atoms(core)[0]
    gesture(core,"single_bond",canvas_point(core,start["id"]),(480,220));oxygen=atoms(core)[-1]
    core.set_element("O");gesture(core,"atom_label",canvas_point(core,oxygen["id"]))
    bond=bonds(core)[0];midpoint=((canvas_point(core,bond["a"])[0]+canvas_point(core,bond["b"])[0])*.5,
                                 (canvas_point(core,bond["a"])[1]+canvas_point(core,bond["b"])[1])*.5)
    gesture(core,"single_bond",midpoint)
    drawing=core.depict(False);svg=drawing["svg"]
    viewbox=[float(value) for value in re.search(r"viewBox='([^']+)'",svg).group(1).split()]
    left,top,width,height=viewbox
    group=svg.split("<g id='explicit-visual-bonds'>",1)[1].split("</g>",1)[0]
    endpoints=[]
    for match in re.finditer(r"M ([\-0-9.eE]+),([\-0-9.eE]+) L ([\-0-9.eE]+),([\-0-9.eE]+)",group):
        for x,y in ((float(match.group(1)),float(match.group(2))),(float(match.group(3)),float(match.group(4)))):
            endpoints.append(((x-left)*drawing["width"]/width,(y-top)*drawing["height"]/height))
    oxygen_center=next(item["center"] for item in drawing["atoms"] if item["id"]==oxygen["id"])
    distances=[math.hypot(x-oxygen_center["x"],y-oxygen_center["y"]) for x,y in endpoints]
    assert len(endpoints)==4 and min(distances)>7


def double_bond_count(svg: str) -> int:
    classes = re.findall(r"class='bond-(\d+)[^']*'", svg)
    return sum(classes.count(bond) >= 2 for bond in set(classes))


def test_smiles_and_benzene_template_only_create_explicit_visual_bonds():
    imported = CoreSession(); imported.import_smiles("benzene", "c1ccccc1"); imported.set_viewport(960, 540, 48, 0, 0)
    imported_svg = imported.depict(False)["svg"]
    assert "stroke-dasharray" not in imported_svg
    assert [bond["type"] for bond in bonds(imported)].count("double") == 3

    manual = session(); gesture(manual, "benzene", (480, 270))
    manual_svg = manual.depict(False)["svg"]
    assert "stroke-dasharray" not in manual_svg
    assert [bond["type"] for bond in bonds(manual)].count("double") == 3


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
    for scale in (1, 2, 4):
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
        canonical_stroke = float(re.search(r"stroke-width='([0-9.]+)'", drawing["svg"]).group(1))
        effective_strokes.append(canonical_stroke * 960 / viewbox_width)

    for values in (bond_lengths, effective_strokes):
        assert abs(values[1] / values[0] - 2) < 1e-9
        assert abs(values[2] / values[0] - 4) < 1e-9
    for dimension in (0, 1):
        assert abs(label_boxes[1][dimension] / label_boxes[0][dimension] - 2) < 0.03
        assert abs(label_boxes[2][dimension] / label_boxes[0][dimension] - 4) < 0.1


def test_v8_serialization_contains_visual_labels_and_no_runtime_aromatic_fields(tmp_path: Path):
    core=CoreSession();core.import_smiles("benzene","c1ccccc1");path=tmp_path/"flat.cmm";core.save(str(path));raw=path.read_text(encoding="utf-8")
    assert '"version": 8' in raw and '"secondary_line_side"' in raw and '"label"' in raw and '"anchor"' in raw
    assert '"scale_x"' in raw and '"scale_y"' in raw and '"scale":' not in raw
    assert '"aromatic"' not in raw and '"display_type"' not in raw and '"formal_charge"' not in raw


def test_creation_serial_is_monotonic_across_delete_and_undo():
    core=session();gesture(core,"atom_label",(480,270));first=atoms(core)[-1]["creation_serial"]
    assert core.undo();gesture(core,"atom_label",(520,270));second=atoms(core)[-1]["creation_serial"]
    assert second>first
    gesture(core,"eraser",canvas_point(core,atoms(core)[-1]["id"]));gesture(core,"atom_label",(560,270))
    assert atoms(core)[-1]["creation_serial"]>second


def test_spiro_ring_click_is_symmetric_and_shares_exactly_one_atom():
    core=session();gesture(core,"ring6",(480,270));before_atoms=list(atoms(core));shared=before_atoms[0];point=canvas_point(core,shared["id"])
    gesture(core,"ring5",point);after=atoms(core);new=[atom for atom in after if atom["id"] not in {value["id"] for value in before_atoms}]
    assert len(new)==4
    new_neighbors=[]
    for bond in bonds(core):
        if shared["id"] in (bond["a"],bond["b"]):
            other=bond["b"] if bond["a"]==shared["id"] else bond["a"]
            if any(value["id"]==other for value in new):new_neighbors.append(next(value for value in new if value["id"]==other))
    assert len(new_neighbors)==2
    lengths=[math.hypot(value["x"]-shared["x"],value["y"]-shared["y"]) for value in new_neighbors]
    assert abs(lengths[0]-lengths[1])<1e-9


def test_ring_on_terminal_atom_is_centered_on_existing_bond_axis():
    core=session();gesture(core,"atom_label",(420,270));start=atoms(core)[0]
    gesture(core,"single_bond",canvas_point(core,start["id"]),(510,270));terminal=atoms(core)[-1]
    before_ids={value["id"] for value in atoms(core)}
    gesture(core,"ring5",canvas_point(core,terminal["id"]));created=[value for value in atoms(core) if value["id"] not in before_ids]
    assert len(created)==4
    ring=[terminal,*created]
    center=(sum(value["x"] for value in ring)/5,sum(value["y"] for value in ring)/5)
    existing=(start["x"]-terminal["x"],start["y"]-terminal["y"])
    outward=(center[0]-terminal["x"],center[1]-terminal["y"])
    cross=existing[0]*outward[1]-existing[1]*outward[0]
    dot=existing[0]*outward[0]+existing[1]*outward[1]
    assert abs(cross)<1e-9
    assert dot<0


def test_attached_ring_drag_snaps_relative_to_empty_sector_bisector():
    core=session();gesture(core,"atom_label",(420,270));start=atoms(core)[0]
    gesture(core,"single_bond",canvas_point(core,start["id"]),(510,270));terminal=atoms(core)[-1]
    point=canvas_point(core,terminal["id"]);angle=math.radians(22);distance_px=90
    end=(point[0]+distance_px*math.cos(angle),point[1]-distance_px*math.sin(angle))
    before={value["id"] for value in atoms(core)};gesture(core,"ring5",point,end)
    ring=[terminal,*[value for value in atoms(core) if value["id"] not in before]]
    center=(sum(value["x"] for value in ring)/5,sum(value["y"] for value in ring)/5)
    snapped=math.degrees(math.atan2(center[1]-terminal["y"],center[0]-terminal["x"]))
    assert abs(snapped-15)<1e-9


def test_continuous_eraser_is_one_undo_transaction():
    core=session();gesture(core,"ring6",(480,270));original=[atom["id"] for atom in atoms(core)];points=[canvas_point(core,atom_id) for atom_id in original[:3]]
    core.set_tool("eraser");core.pointer_down(*points[0])
    for point in points[1:]:core.pointer_move(*point)
    result=core.pointer_up(*points[-1]);assert result["changed"]
    assert sum(atom["alive"] for atom in atoms(core))==3
    assert core.undo();assert all(atom["alive"] for atom in atoms(core))


def test_charge_adornment_follows_atom_and_lerps_local_offset():
    core=session();gesture(core,"atom_label",(480,270));atom=atoms(core)[0];gesture(core,"charge_positive",canvas_point(core,atom["id"]));adornment=adornments(core)[0]
    assert adornment["text"]=="⊕"
    core.set_atom_position(atom["id"],10,20);molecule=structure(core);moved=next(value for value in molecule["atoms"] if value["id"]==atom["id"]);assert (moved["x"]+adornment["x"],moved["y"]+adornment["y"])==(10+adornment["x"],20+adornment["y"])
    core.add_node("adornment_lerp_offset",json.dumps({"target":core.active_molecule,"adornment":adornment["id"],"x":30,"y":-10,"frames":30,"easing":"linear"}))
    mid=core.evaluated_project(15)["molecules"][0]["adornments"][0];end=core.evaluated_project(30)["molecules"][0]["adornments"][0]
    assert abs(mid["x"]-(adornment["x"]+30)*.5)<1e-9 and abs(mid["y"]-(adornment["y"]-10)*.5)<1e-9
    assert (end["x"],end["y"])==(30,-10)


def test_formal_charge_has_drag_preview_15_degree_offset_and_circled_svg():
    core=session();gesture(core,"atom_label",(480,270));atom=atoms(core)[0];point=canvas_point(core,atom["id"])
    core.set_tool("charge_positive");down=core.pointer_down(*point)
    assert down["preview"]["kind"]=="adornment" and down["preview"]["text"]=="⊕"
    angle=math.radians(22);end=(point[0]+80*math.cos(angle),point[1]-80*math.sin(angle))
    moved=core.pointer_move(*end);assert moved["preview"]["kind"]=="adornment"
    assert core.pointer_up(*end)["changed"]
    charge=adornments(core)[0]
    snapped=math.degrees(math.atan2(charge["y"],charge["x"]));assert abs(snapped-15)<1e-9
    svg=core.depict(False)["svg"]
    assert "class='formal-charge'" in svg and "<circle" in svg


def test_formal_charge_uses_one_fixed_twenty_unit_radius():
    core=session();gesture(core,"atom_label",(480,270));atom=atoms(core)[0];point=canvas_point(core,atom["id"])
    gesture(core,"charge_positive",point)
    clicked=adornments(core)[-1]
    gesture(core,"charge_negative",point,(point[0]+100,point[1]))
    dragged=adornments(core)[-1]
    assert math.isclose(math.hypot(clicked["x"],clicked["y"]),20,rel_tol=1e-9)
    assert math.isclose(math.hypot(dragged["x"],dragged["y"]),20,rel_tol=1e-9)


def test_atom_text_requests_left_right_and_persists_one_visual_label_field():
    core=session();gesture(core,"single_bond",(420,270),(452,270));molecule=structure(core)
    left,right=molecule["atoms"][0],molecule["atoms"][1]
    core.set_tool("atom_text");left_point=canvas_point(core,left["id"]);right_point=canvas_point(core,right["id"])
    core.pointer_down(*left_point);left_request=core.pointer_up(*left_point)["message"]
    core.pointer_down(*right_point);right_request=core.pointer_up(*right_point)["message"]
    assert left_request==f'atom_text|{left["id"]}|left'
    assert right_request==f'atom_text|{right["id"]}|right'
    core.pointer_down(*right_point);dragged=core.pointer_up(right_point[0]-80,right_point[1])["message"]
    assert dragged==f'atom_text|{right["id"]}|left'
    assert core.set_atom_label(right["id"],"NO2","left","superscript")
    stored=next(atom for atom in atoms(core) if atom["id"]==right["id"])
    assert stored["label"]=="NO2" and stored["label_side"]=="left" and stored["number_style"]=="superscript"
    raw=json.loads(core.json());saved=next(atom for atom in structure(core)["atoms"] if atom["id"]==right["id"])
    assert saved["label"]=="NO2" and "alias" not in saved


def test_atom_text_click_scores_both_sides_for_degree_two_vertices_and_ties_right():
    core=session();gesture(core,"single_bond",(480,270),(448,252));center=atoms(core)[0]
    center_point=canvas_point(core,center["id"])
    gesture(core,"single_bond",center_point,(448,288))
    core.set_tool("atom_text");core.pointer_down(*center_point)
    assert core.pointer_up(*center_point)["message"]==f'atom_text|{center["id"]}|right'

    mirrored=session();gesture(mirrored,"single_bond",(480,270),(512,252));middle=atoms(mirrored)[0]
    middle_point=canvas_point(mirrored,middle["id"])
    gesture(mirrored,"single_bond",middle_point,(512,288))
    mirrored.set_tool("atom_text");mirrored.pointer_down(*middle_point)
    assert mirrored.pointer_up(*middle_point)["message"]==f'atom_text|{middle["id"]}|left'

    tied=session();gesture(tied,"single_bond",(480,270),(480,238));origin=atoms(tied)[0]
    origin_point=canvas_point(tied,origin["id"])
    gesture(tied,"single_bond",origin_point,(480,302))
    tied.set_tool("atom_text");tied.pointer_down(*origin_point)
    assert tied.pointer_up(*origin_point)["message"]==f'atom_text|{origin["id"]}|right'


def test_text_and_element_tools_create_standalone_atoms_on_blank_canvas():
    core=CoreSession();target=core.add_blank_molecule("空白分子")
    structure=core.add_node("molecule_set_structure",json.dumps({"target":target}));core.edit_node(structure)
    core.set_viewport(960,540,1,0,0);core.set_tool("atom_text")
    core.pointer_down(480,270);result=core.pointer_up(480,270)
    assert result["changed"] and result["message"].startswith("atom_text|")
    atom_id=result["message"].split("|")[1]
    assert core.set_atom_label(atom_id,"OH","right","subscript")
    atoms=next(node for node in core.project()["nodes"] if node["id"]==structure)["params"]["snapshot"]["atoms"]
    assert len(atoms)==1 and atoms[0]["label"]=="OH"
    core.set_element("Cl");core.set_tool("atom_label");core.pointer_down(560,270)
    assert core.pointer_up(560,270)["changed"]
    atoms=next(node for node in core.project()["nodes"] if node["id"]==structure)["params"]["snapshot"]["atoms"]
    assert len(atoms)==2 and atoms[1]["label"]=="Cl"


def test_control_drag_is_rectangle_selection_without_switching_drawing_tool():
    core=session();gesture(core,"ring6",(480,270));core.set_tool("single_bond")
    down=core.pointer_down(350,150,False,True,False)
    assert down["preview"]["kind"]=="rectangle"
    core.pointer_move(610,390,False,True,False)
    up=core.pointer_up(610,390,False,True,False)
    assert set(up["selected_atoms"])=={atom["id"] for atom in atoms(core) if atom["alive"]}
    assert core.tool=="single_bond"


def test_anchor_deletion_and_detach_preserve_world_coordinates():
    core=session();gesture(core,"ring5",(480,270));base=structure(core);ordered=sorted(base["atoms"],key=lambda value:value["creation_serial"]);positions={value["id"]:(value["x"],value["y"]) for value in ordered}
    gesture(core,"eraser",canvas_point(core,ordered[0]["id"]));after={value["id"]:(value["x"],value["y"]) for value in atoms(core) if value["alive"]};assert all(after[key]==positions[key] for key in after)
    destination=core.add_blank_molecule("fragment");source=core.project()["molecules"][0]["id"]
    moving=[ordered[1]["id"],ordered[2]["id"]];core.add_node("detach_subgraph",json.dumps({"target":source,"destination":destination,"atoms":moving,"bonds":[]}))
    evaluated=core.evaluated_project(0);dest=next(value for value in evaluated["molecules"] if value["id"]==destination)
    assert {value["id"]:(value["x"],value["y"]) for value in dest["atoms"]}=={key:positions[key] for key in moving}


def test_form_break_merge_and_intramolecular_form_are_reversible():
    core=CoreSession();first=core.import_smiles("first","CC");second=core.import_smiles("second","O");a=structure_for(core,first)["atoms"][1]["id"];b=structure_for(core,second)["atoms"][0]["id"]
    # Pre-v8 merge nodes remain readable and evaluable, but the public command
    # now creates an instantaneous disconnected output object.
    legacy=json.loads(core.json());legacy["nodes"].append({"id":"N999","type":"merge_molecules","enabled":True,"params":{"target":first,"source":second,"bond":"B99","a":a,"b":b,"order":"single","frames":30,"easing":"linear"}});core.replace_json(json.dumps(legacy))
    mid=core.evaluated_project(15);target=next(value for value in mid["molecules"] if value["id"]==first);bond=next(value for value in target["bonds"] if value["id"]=="B99");assert 120<=bond["alpha"]<=135
    assert next(value for value in mid["molecules"] if value["id"]==second)["retired"]
    before=core.evaluated_project(-1);assert not next(value for value in before["molecules"] if value["id"]==second)["retired"]
    # Forming a bond inside one molecule never retires or merges another molecule.
    atom_ids=[value["id"] for value in structure_for(core,first)["atoms"]];core.add_node("bond_form",json.dumps({"target":first,"bond":"B100","a":atom_ids[0],"b":atom_ids[1],"order":"single","frames":30,"easing":"linear"}))
    assert any(value["id"]=="B100" for value in next(value for value in core.evaluated_project(15)["molecules"] if value["id"]==first)["bonds"])


def test_imports_allocate_project_wide_stable_ids_for_ownership_transfer():
    core=CoreSession();first=core.import_smiles("first","CCO");second=core.import_smiles("second","C=O")
    a=structure_for(core,first);b=structure_for(core,second)
    assert set(value["id"] for value in a["atoms"]).isdisjoint(value["id"] for value in b["atoms"])
    assert set(value["id"] for value in a["bonds"]).isdisjoint(value["id"] for value in b["bonds"])


def test_smiles_import_is_one_atomic_create_transaction_for_undo_and_redo():
    core=CoreSession();target=core.import_smiles("ethanol","CCO");created=core.project()
    assert len(created["molecules"])==1 and not created["molecules"][0]["atoms"] and len(structure_for(core,target)["atoms"])==3
    assert len([node for node in created["nodes"] if node["type"]=="molecule_create" and node["params"]["target"]==target])==1
    assert [node["type"] for node in created["nodes"] if node.get("params",{}).get("target")==target]==["molecule_create","molecule_set_structure"]
    assert core.undo() and not core.project()["molecules"]
    assert core.redo() and core.project()["molecules"]==created["molecules"]


def test_visual_events_generate_runtime_lua_without_chemical_fields():
    core=CoreSession();first=core.import_smiles("first","CC");second=core.import_smiles("second","O")
    a=structure_for(core,first)["atoms"][0]["id"];b=structure_for(core,second)["atoms"][0]["id"]
    core.add_node("selection_fade",json.dumps({"target":first,"atoms":[a],"bonds":[],"adornments":[],"value":0,"frames":30,"easing":"linear"}))
    core.add_node("detach_subgraph",json.dumps({"target":first,"destination":second,"atoms":[a],"bonds":[]}))
    legacy=json.loads(core.json());legacy["nodes"].append({"id":"N999","type":"merge_molecules","enabled":True,"params":{"target":first,"source":second,"bond":"B999","a":a,"b":b,"order":"single","frames":30,"easing":"linear"}});core.replace_json(json.dumps(legacy))
    lua=core.generate_lua();assert "LerpAtomAlpha" in lua and ".DetachSubgraph(" in lua and ".MergeFrom(" in lua
    assert "aromatic" not in lua and "formal_charge" not in lua and "displayType" not in lua


def test_repository_visual_events_is_one_reversible_authoring_model():
    core=CoreSession();core.load(str(ROOT/"mod"/"visual_events"/"visual_events.cmm"))
    before=core.json();assert core.end_frame==120
    forward={frame:core.evaluated_molecules(frame) for frame in (0,30,52,75,120)}
    backward={frame:core.evaluated_molecules(frame) for frame in (120,75,52,30,0)}
    assert all(forward[frame]==backward[frame] for frame in forward)
    assert core.json()==before
    assert forward[30]["molecule3"]["has_coordinate"]
    assert forward[52]["molecule3"]["alpha"]==130
    assert not forward[75]["molecule2"]["exists"]
    assert forward[75]["molecule3"]["alpha"]==0
    assert core.generate_lua()==(ROOT/"mod"/"visual_events"/"main.lua").read_text(encoding="utf-8")


def test_node_registry_exposes_explicit_four_scope_metadata():
    core=CoreSession();registry={item["type"]:item for item in core.node_registry()}
    for key in ("category","scope","section","order","exposure","target_kind","structure_edit_capability"):
        assert all(key in item for item in registry.values())
    molecule_object=[item["label"] for item in registry.values() if item["category"]=="分子" and item["scope"]=="object" and item["exposure"]=="primary"]
    assert molecule_object==["新建分子","删除分子","合并分子","分裂分子"]
    assert registry["arrow_set_position"]["exposure"]=="legacy"
    assert registry["arrow_lerp_position"]["exposure"]=="legacy"


def test_primary_node_hierarchy_matches_the_four_scope_authoring_contract():
    registry=CoreSession().node_registry()
    def types(category,scope):
        values=[item for item in registry if item["category"]==category and item["scope"]==scope and item["exposure"]=="primary"]
        return [item["type"] for item in sorted(values,key=lambda item:item["order"])]
    assert types("分子","object")==["molecule_create","molecule_delete","merge_molecules","split_molecule"]
    assert types("分子","global")==["molecule_global_set_alpha","molecule_global_set_color","molecule_global_set_scale","molecule_global_set_scale_x","molecule_global_set_scale_y"]
    assert types("分子","set")==["molecule_set_structure","molecule_set_position","molecule_set_x","molecule_set_y","molecule_set_scale","molecule_set_scale_x","molecule_set_scale_y","molecule_set_rotation","molecule_set_alpha","molecule_set_color","molecule_set_layer"]
    assert types("分子","transform")==["molecule_gradient_structure","molecule_lerp_position","molecule_lerp_x","molecule_lerp_y","molecule_lerp_scale","molecule_lerp_scale_x","molecule_lerp_scale_y","molecule_lerp_rotation","molecule_lerp_alpha","molecule_lerp_color"]
    assert types("箭头","object")==["arrow_new","arrow_delete"]
    assert types("箭头","global")==["arrow_global_set_alpha","arrow_global_set_color","arrow_global_set_scale","arrow_global_set_scale_x","arrow_global_set_scale_y","arrow_global_set_width"]
    assert types("箭头","set")==["arrow_set_curve","arrow_set_progress","arrow_set_scale","arrow_set_scale_x","arrow_set_scale_y","arrow_set_alpha","arrow_set_color","arrow_set_width"]
    assert types("箭头","transform")==["arrow_lerp_progress","arrow_lerp_scale","arrow_lerp_scale_x","arrow_lerp_scale_y","arrow_lerp_alpha","arrow_lerp_color","arrow_lerp_width"]
    primary={item["type"]:item for item in registry if item["exposure"]=="primary"}
    assert primary["molecule_gradient_structure"]["tool_label"]=="渐变结构"
    for legacy in ("molecule_lerp_structure","molecule_merge_gradient_structure","molecule_split_gradient_structure","bond_form","bond_break","selection_show","selection_hide","selection_fade"):
        assert registry[next(index for index,item in enumerate(registry) if item["type"]==legacy)]["exposure"]=="legacy"
    assert primary["arrow_set_curve"]["tool_label"]=="箭头曲线"
    assert "arrow_set_position" not in {item for scope in ("object","global","set","transform") for item in types("箭头",scope)}


def test_split_and_merge_are_atomic_disconnected_object_operations():
    core=CoreSession();source=core.import_smiles("原分子","CC");core.set_active_molecule(source)
    core.add_node("molecule_set_position",json.dumps({"target":source,"x":35.0,"y":-12.0}))
    core.add_node("molecule_set_scale_x",json.dumps({"target":source,"value":1.4}))
    core.add_node("molecule_set_alpha",json.dumps({"target":source,"value":137}))
    before=core.project();split=core.add_node("split_molecule","{}")
    split_params=next(node for node in core.project()["nodes"] if node["id"]==split)["params"]
    copy_id=split_params["output"];assert copy_id!=source and core.active_molecule==copy_id
    assert next(value for value in core.project()["molecules"] if value["id"]==copy_id)["name"]==copy_id
    scene=core.evaluated_project(0);original=next(m for m in scene["molecules"] if m["id"]==source);copied=next(m for m in scene["molecules"] if m["id"]==copy_id)
    assert copied["anchor"]==original["anchor"] and copied["scale_x"]==original["scale_x"] and copied["alpha"]==original["alpha"]
    assert len(copied["atoms"])==len(original["atoms"])==2
    assert not ({a["id"] for a in copied["atoms"]}&{a["id"] for a in original["atoms"]})
    assert core.undo();undone=core.project()
    assert undone["nodes"]==before["nodes"] and undone["molecules"]==before["molecules"]
    assert core.redo();core.set_active_molecule(copy_id)
    merge=core.add_node("merge_molecules",json.dumps({"source":source}))
    merge_params=next(node for node in core.project()["nodes"] if node["id"]==merge)["params"]
    merged_id=merge_params["output"];assert merge_params["target"]==copy_id and merged_id not in (source,copy_id)
    assert next(value for value in core.project()["molecules"] if value["id"]==merged_id)["name"]==merged_id
    final=core.evaluated_project(0);merged=next(m for m in final["molecules"] if m["id"]==merged_id)
    assert len([a for a in merged["atoms"] if a.get("alive",True)])==4
    assert not merged["bonds"] or len(merged["bonds"])==2  # two disconnected ethane components
    assert all(next(m for m in final["molecules"] if m["id"]==value)["retired"] for value in (source,copy_id))
    reopened=CoreSession();reopened.replace_json(core.json());assert reopened.evaluated_project(0)==final
    lua=core.generate_lua();assert f"{source}.Delete()" in lua and f"{copy_id}.Delete()" in lua


def test_object_operation_output_creation_moves_as_one_lifecycle_safe_block():
    core=CoreSession();core.import_smiles("原分子","CC")
    first_wait=core.add_node("wait",json.dumps({"frames":10}));operation=core.add_node("split_molecule","{}");core.add_node("wait",json.dumps({"frames":20}))
    before=core.project();params=next(node["params"] for node in before["nodes"] if node["id"]==operation);output=params["output"]
    old=next(index for index,node in enumerate(before["nodes"]) if node["id"]==operation)
    assert core.move_node(operation,old-1)
    nodes=core.project()["nodes"];new=next(index for index,node in enumerate(nodes) if node["id"]==operation)
    assert nodes[new-1]["type"]=="molecule_create" and nodes[new-1]["params"]["target"]==output
    assert new<next(index for index,node in enumerate(nodes) if node["id"]==first_wait)
    assert not core.diagnostics(30)
    assert core.undo() and core.project()["nodes"]==before["nodes"]


def test_explicit_merge_source_clamps_insertion_after_both_inputs_without_substitution():
    core=CoreSession();primary=core.import_smiles("主分子","CC");source=core.import_smiles("并入分子","[Cl-]")
    nodes=core.project()["nodes"];early=next(index+1 for index,node in enumerate(nodes) if node["type"]=="molecule_set_structure" and node["params"]["target"]==primary)
    core.set_active_molecule(primary);operation=core.add_node("merge_molecules",json.dumps({"source":source}),early)
    project=core.project();params=next(node["params"] for node in project["nodes"] if node["id"]==operation)
    assert params["target"]==primary and params["source"]==source
    operation_index=next(index for index,node in enumerate(project["nodes"]) if node["id"]==operation)
    source_structure=next(index for index,node in enumerate(project["nodes"]) if node["type"]=="molecule_set_structure" and node["params"]["target"]==source)
    assert operation_index>source_structure and not core.diagnostics(0)


def test_structure_nodes_honor_explicit_target_and_recover_from_stale_active_molecule():
    core=CoreSession();first=core.import_smiles("分子 1","CC");second=core.import_smiles("分子 2","O")
    core.set_active_molecule(first)
    explicit=core.add_node("molecule_gradient_structure",json.dumps({"target":second,"frames":12,"easing":"linear"}))
    assert next(node for node in core.project()["nodes"] if node["id"]==explicit)["params"]["target"]==second
    assert core.active_molecule==second

    core.set_active_molecule(first);core.add_node("molecule_delete",json.dumps({"target":first}))
    recovered=core.add_node("molecule_gradient_structure",json.dumps({"target":first,"frames":8,"easing":"linear"}))
    params=next(node for node in core.project()["nodes"] if node["id"]==recovered)["params"]
    assert params["target"]==second and core.active_molecule==second


def test_global_arrow_width_is_an_absolute_override_not_a_multiplier():
    core=CoreSession();core.add_node("arrow_new",json.dumps({"target":"arrow1"}))
    core.add_node("arrow_set_curve",json.dumps({"target":"arrow1","initialized":True,"x1":0,"y1":0,"cx1":20,"cy1":30,"cx2":40,"cy2":30,"x2":60,"y2":0}))
    core.add_node("arrow_set_progress",json.dumps({"target":"arrow1","value":1.0}))
    core.add_node("arrow_set_width",json.dumps({"target":"arrow1","value":8.0}))
    core.add_node("arrow_global_set_width",json.dumps({"value":4.0}))
    arrow=core.evaluated_arrows(0)["arrow1"]
    assert arrow["width"]==4.0
    assert 'SetGlobal("arrow", "width_override", 4)' in core.generate_lua()


def test_merge_structure_transform_uses_two_fixed_molecules_and_preserves_world_geometry():
    core=CoreSession();main=core.import_smiles("主分子","CC");joined=core.import_smiles("并入分子","O")
    core.set_active_molecule(main);core.add_node("molecule_set_position",json.dumps({"target":main,"x":-40,"y":15}))
    core.add_node("molecule_set_scale_x",json.dumps({"target":main,"value":1.5}));core.add_node("molecule_set_rotation",json.dumps({"target":main,"value":20}))
    core.add_node("molecule_set_position",json.dumps({"target":joined,"x":90,"y":-25}))
    before=core.evaluated_project(0);source_before=next(m for m in before["molecules"] if m["id"]==joined);source_points=[(a["x"],a["y"]) for a in source_before["atoms"] if a.get("alive",True)]
    node=core.add_node("molecule_merge_gradient_structure",json.dumps({"source":joined,"frames":30,"easing":"linear"}))
    params=next(item for item in core.project()["nodes"] if item["id"]==node)["params"]
    assert params["target"]==main and params["source"]==joined and params["coordinate_space"]=="molecule_local_v2"
    redirected=dict(params);redirected["source"]=main
    try:core.update_node(node,json.dumps(redirected));assert False,"多分子结构变换不应允许重指向"
    except RuntimeError:pass
    assert params["id_map"]["atoms"] and not ({a["id"] for a in params["target_start_snapshot"]["atoms"]}&{a["id"] for a in params["source_start_snapshot"]["atoms"]})
    middle=core.evaluated_project(15);middle_main=next(m for m in middle["molecules"] if m["id"]==main)
    assert any(0<a["alpha"]<255 for a in middle_main["atoms"])
    final=core.evaluated_project(30);main_final=next(m for m in final["molecules"] if m["id"]==main);source_final=next(m for m in final["molecules"] if m["id"]==joined)
    assert source_final["retired"] and not source_final["visible"]
    final_points=[(a["x"],a["y"]) for a in main_final["atoms"] if a.get("alive",True)]
    for expected in source_points:assert min(((x-expected[0])**2+(y-expected[1])**2)**.5 for x,y in final_points)<1e-6
    restored=CoreSession();restored.replace_json(core.json());assert restored.evaluated_project(30)==final
    lua=core.generate_lua();assert lua.count("LerpStructure(")>=2 and f"{joined}:Delete()" in lua


def test_split_structure_transform_moves_deleted_subgraph_to_second_molecule_without_ids_in_ui_schema():
    core=CoreSession();source=core.import_smiles("来源分子","CC");destination=core.add_blank_molecule("分出分子");core.set_active_molecule(source)
    core.add_node("molecule_set_position",json.dumps({"target":source,"x":75,"y":20}));core.add_node("molecule_set_rotation",json.dumps({"target":source,"value":-25}))
    node=core.add_node("molecule_split_gradient_structure",json.dumps({"destination":destination,"frames":20,"easing":"linear"}))
    core.edit_node(node);assert not core.can_edit_structure
    definition=next(item for item in core.node_registry() if item["type"]=="molecule_split_gradient_structure")
    assert definition["exposure"]=="legacy" and all("ID" not in field["label"] for field in definition["fields"])
    restored=CoreSession();restored.replace_json(core.json());assert restored.evaluated_project(20)==core.evaluated_project(20)


def test_split_structure_transform_creates_its_output_identity_as_one_undo_transaction():
    core=CoreSession();source=core.import_smiles("来源","CC");before=core.project();node=core.add_node("molecule_split_gradient_structure",json.dumps({"frames":12}))
    project=core.project();created=next(item for item in project["nodes"] if item["id"]==node);destination=created["params"]["destination"]
    assert destination!=source and len(project["molecules"])==len(before["molecules"])+1
    index=next(index for index,item in enumerate(project["nodes"]) if item["id"]==node)
    assert project["nodes"][index-1]["type"]=="molecule_create" and project["nodes"][index-1]["params"]["target"]==destination
    assert core.undo();restored=core.project()
    assert restored["nodes"]==before["nodes"] and restored["molecules"]==before["molecules"]
    assert core.redo() and next(item for item in core.project()["nodes"] if item["id"]==node)["params"]["destination"]==destination


def test_split_structure_transform_treats_erased_bridge_as_the_natural_split_gesture():
    core=CoreSession();source=core.import_smiles("来源","CCC");core.set_active_molecule(source);node=core.add_node("molecule_split_gradient_structure",json.dumps({"frames":10}));core.edit_node(node)
    assert not core.can_edit_structure and core.edit_target_kind=="script_node"


def test_every_public_transform_node_exposes_a_deterministic_comparison_frame():
    registry=[item for item in CoreSession().node_registry() if item["scope"]=="transform" and item["exposure"]=="primary"]
    assert registry
    for definition in registry:
        core=CoreSession();molecule=core.import_smiles("比较对象","CC")
        secondary=core.import_smiles("第二对象","O") if definition["type"] in ("molecule_merge_gradient_structure","molecule_split_gradient_structure") else ""
        core.set_active_molecule(molecule)
        core.add_node("arrow_new",json.dumps({"target":"arrow1"}))
        core.add_node("arrow_set_curve",json.dumps({"target":"arrow1","initialized":True,"x1":-40,"y1":0,"cx1":-10,"cy1":30,"cx2":20,"cy2":30,"x2":50,"y2":0}))
        core.add_node("wait",json.dumps({"frames":7}))
        params={field["key"]:field.get("default") for field in definition["fields"]}
        if definition["target_kind"]=="molecule":params["target"]=molecule
        elif definition["target_kind"]=="arrow":params["target"]="arrow1"
        if definition["type"]=="molecule_merge_gradient_structure":params["source"]=secondary
        elif definition["type"]=="molecule_split_gradient_structure":params["destination"]=secondary
        node=core.add_node(definition["type"],json.dumps(params));core.edit_node(node)
        timing=next(item for item in core.node_timings() if item["id"]==node)
        assert core.comparison_frame==timing["start"],definition["type"]


def test_new_molecule_is_atomic_immutable_and_duplicate_is_deep_copy():
    core=CoreSession();molecule=core.add_blank_molecule("first");project=core.project()
    creates=[node for node in project["nodes"] if node["type"]=="molecule_create"]
    assert len(project["molecules"])==1 and len(creates)==1 and creates[0]["params"]["target"]==molecule
    try:core.add_node("molecule_create",json.dumps({"target":molecule}));assert False
    except RuntimeError:pass
    changed=dict(creates[0]["params"]);changed["target"]="somewhere_else"
    try:core.update_node(creates[0]["id"],json.dumps(changed));assert False
    except RuntimeError:pass
    core.set_viewport(960,540,1,0,0);core.set_tool("single_bond");core.pointer_down(420,270);core.pointer_up(470,270)
    original=core.project()["molecules"][0]
    duplicate_node=core.duplicate_node(creates[0]["id"]);project=core.project();duplicate=project["molecules"][1]
    assert duplicate_node and duplicate["id"]!=original["id"]
    assert not original["atoms"] and not duplicate["atoms"]
    assert len([node for node in project["nodes"] if node["type"]=="molecule_create"])==2


def test_v6_uniform_scale_migrates_to_v8_xy_components_anchor_and_roundtrips():
    core=CoreSession();core.add_blank_molecule("old");raw=json.loads(core.json());raw["version"]=6
    molecule=raw["molecules"][0];molecule.pop("scale_x");molecule.pop("scale_y");molecule["scale"]=1.75
    migrated=CoreSession();migrated.replace_json(json.dumps(raw));value=migrated.project()["molecules"][0]
    assert value["scale_x"]==value["scale_y"]==1.75 and migrated.project()["version"]==8 and value["anchor"]=={"x":0.0,"y":0.0}
    reopened=CoreSession();reopened.replace_json(migrated.json());assert reopened.project()==migrated.project()


def test_v7_base_structure_migrates_to_v8_identity_snapshot_and_preserves_world_frame():
    source=CoreSession();target=source.import_smiles("迁移苯","c1ccccc1");raw=json.loads(source.json());raw["version"]=7
    structure_node=next(node for node in raw["nodes"] if node["type"]=="molecule_set_structure")
    snapshot=structure_node["params"]["snapshot"];raw["nodes"].remove(structure_node)
    molecule=next(item for item in raw["molecules"] if item["id"]==target);molecule.pop("anchor",None)
    shift=(47.0,-23.0)
    molecule["atoms"]=[{**atom,"x":atom["x"]+shift[0],"y":atom["y"]+shift[1]} for atom in snapshot["atoms"]]
    molecule["bonds"]=snapshot["bonds"];molecule["adornments"]=snapshot["adornments"]
    molecule["next_atom_id"]=snapshot["next_atom_id"];molecule["next_bond_id"]=snapshot["next_bond_id"];molecule["next_adornment_id"]=snapshot["next_adornment_id"]
    molecule.update(scale_x=.45,scale_y=1.7,rotation=31.0)
    create_index=next(i for i,node in enumerate(raw["nodes"]) if node["type"]=="molecule_create")
    raw["nodes"][create_index+1:create_index+1]=[
        {"id":"N800","type":"molecule_set_position","enabled":True,"params":{"target":target,"x":130.0,"y":-80.0}},
        {"id":"N801","type":"molecule_global_set_scale_x","enabled":True,"params":{"value":1.3}},
        {"id":"N802","type":"molecule_global_set_scale_y","enabled":True,"params":{"value":.8}},
    ];raw["next_node_id"]=900
    old_ids=([atom["id"] for atom in molecule["atoms"]],[bond["id"] for bond in molecule["bonds"]])
    anchor=min((atom for atom in molecule["atoms"] if atom.get("alive",True)),key=lambda atom:atom["creation_serial"])
    sx,sy=molecule["scale_x"]*1.3,molecule["scale_y"]*.8;r=math.radians(molecule["rotation"]);c,s=math.cos(r),math.sin(r)
    expected={atom["id"]:(130+(atom["x"]-anchor["x"])*sx*c-(atom["y"]-anchor["y"])*sy*s,
                              -80+(atom["x"]-anchor["x"])*sx*s+(atom["y"]-anchor["y"])*sy*c) for atom in molecule["atoms"]}
    migrated=CoreSession();migrated.replace_json(json.dumps(raw));project=migrated.project();identity=next(item for item in project["molecules"] if item["id"]==target)
    assert project["version"]==8 and not identity["atoms"] and identity["anchor"]=={"x":anchor["x"],"y":anchor["y"]}
    create_index=next(i for i,node in enumerate(project["nodes"]) if node["type"]=="molecule_create" and node["params"]["target"]==target)
    migrated_structure=project["nodes"][create_index+1];assert migrated_structure["type"]=="molecule_set_structure"
    assert migrated_structure["params"]["coordinate_space"]=="molecule_local_v2"
    assert ([atom["id"] for atom in migrated_structure["params"]["snapshot"]["atoms"]],[bond["id"] for bond in migrated_structure["params"]["snapshot"]["bonds"]])==old_ids
    final=next(item for item in migrated.evaluated_project(0)["molecules"] if item["id"]==target);actual={atom["id"]:(atom["x"],atom["y"]) for atom in final["atoms"]}
    for atom_id,point in expected.items():assert math.isclose(actual[atom_id][0],point[0],abs_tol=1e-7) and math.isclose(actual[atom_id][1],point[1],abs_tol=1e-7)
    reopened=CoreSession();reopened.replace_json(migrated.json());assert reopened.evaluated_project(0)==migrated.evaluated_project(0) and reopened.project()["nodes"]==project["nodes"]


def test_global_molecule_tracks_compose_after_local_and_affect_future_objects():
    core=CoreSession();first=core.add_blank_molecule("first")
    core.add_node("molecule_set_scale_x",json.dumps({"target":first,"value":2}))
    core.add_node("molecule_set_scale_y",json.dumps({"target":first,"value":3}))
    core.add_node("molecule_set_alpha",json.dumps({"target":first,"value":200}))
    core.add_node("molecule_set_color",json.dumps({"target":first,"r":100,"g":150,"b":200}))
    core.add_node("molecule_global_set_scale_x",json.dumps({"value":4}))
    core.add_node("molecule_global_set_scale_y",json.dumps({"value":5}))
    core.add_node("molecule_global_set_alpha",json.dumps({"value":128}))
    core.add_node("molecule_global_set_color",json.dumps({"r":128,"g":64,"b":255}))
    second=core.add_blank_molecule("future");values=core.evaluated_molecules(0)
    assert values[first]["scale_x"]==8 and values[first]["scale_y"]==15
    assert values[first]["alpha"]==128 and values[first]["r"]==128 and values[first]["g"]==64 and values[first]["b"]==255
    assert values[second]["scale_x"]==4 and values[second]["scale_y"]==5 and values[second]["alpha"]==128
    saved=core.json();restored=CoreSession();restored.replace_json(saved);assert restored.evaluated_molecules(0)==values


def test_local_and_global_color_nodes_render_and_global_visuals_override_except_scale():
    core=CoreSession();molecule=core.import_smiles("colored","c1ccccc1")
    # The declaration's neutral white object colour is an identity state, not
    # an instruction to paint black structure primitives white in the engine.
    assert f"{molecule}.SetColor" not in core.generate_lua()
    core.add_node("molecule_set_color",json.dumps({"target":molecule,"r":255,"g":0,"b":0}))
    assert f"{molecule}.SetColor(255, 0, 0)" in core.generate_lua()
    assert "rgb(255,0,0)" in core.depict_at(0,True)["svg"]
    core.add_node("molecule_lerp_color",json.dumps({"target":molecule,"r":15,"g":90,"b":210,"frames":20,"easing":"linear"}))
    middle=core.evaluated_molecules(10)[molecule]
    assert (middle["r"],middle["g"],middle["b"])==(135,45,105)
    core.add_node("molecule_set_alpha",json.dumps({"target":molecule,"value":0}))
    core.add_node("molecule_global_set_alpha",json.dumps({"value":140}))
    core.add_node("molecule_global_set_color",json.dumps({"r":12,"g":34,"b":56}))
    core.add_node("molecule_set_scale",json.dumps({"target":molecule,"value":2}))
    core.add_node("molecule_global_set_scale",json.dumps({"value":3}))
    final=core.evaluated_molecules(20)[molecule]
    assert (final["alpha"],final["r"],final["g"],final["b"])==(140,12,34,56)
    assert final["scale_x"]==final["scale_y"]==6
    assert "rgb(12,34,56)" in core.depict_at(20,True)["svg"]

    core.add_node("arrow_new",json.dumps({"target":"arrow1"}))
    core.add_node("arrow_set_curve",json.dumps({"target":"arrow1","initialized":True,"x1":0,"y1":0,"cx1":20,"cy1":20,"cx2":40,"cy2":20,"x2":60,"y2":0}))
    core.add_node("arrow_set_color",json.dumps({"target":"arrow1","r":240,"g":30,"b":60}))
    core.add_node("arrow_lerp_color",json.dumps({"target":"arrow1","r":20,"g":130,"b":220,"frames":20,"easing":"linear"}))
    arrow_middle=core.evaluated_arrows(10)["arrow1"]
    assert (arrow_middle["r"],arrow_middle["g"],arrow_middle["b"])==(130.0,80.0,140.0)
    core.add_node("arrow_set_alpha",json.dumps({"target":"arrow1","value":0}))
    core.add_node("arrow_set_width",json.dumps({"target":"arrow1","value":9}))
    core.add_node("arrow_global_set_color",json.dumps({"r":20,"g":80,"b":160}))
    core.add_node("arrow_global_set_alpha",json.dumps({"value":170}))
    core.add_node("arrow_global_set_width",json.dumps({"value":4}))
    arrow=core.evaluated_arrows(20)["arrow1"]
    assert (arrow["alpha"],arrow["r"],arrow["g"],arrow["b"],arrow["width"])==(170.0,20.0,80.0,160.0,4.0)


def test_global_override_order_delete_undo_redo_and_reload_are_deterministic():
    core=CoreSession();target=core.add_blank_molecule("global-order")
    first=core.add_node("molecule_global_set_scale_x",json.dumps({"value":2}))
    wait=core.add_node("wait",json.dumps({"frames":10}))
    second=core.add_node("molecule_global_set_scale_x",json.dumps({"value":3}))
    assert core.evaluated_molecules(0)[target]["scale_x"]==2
    assert core.evaluated_molecules(10)[target]["scale_x"]==3
    assert core.delete_node(second) and core.evaluated_molecules(10)[target]["scale_x"]==2
    assert core.undo() and core.evaluated_molecules(10)[target]["scale_x"]==3
    assert core.redo() and core.evaluated_molecules(10)[target]["scale_x"]==2
    assert core.undo();core.move_node(second,1)
    assert core.evaluated_molecules(0)[target]["scale_x"]==2
    restored=CoreSession();restored.replace_json(core.json())
    assert restored.project()["nodes"]==core.project()["nodes"]
    assert restored.evaluated_molecules(0)==core.evaluated_molecules(0)


def test_local_xy_scale_transform_midpoint_and_codegen_are_consistent():
    core=CoreSession();target=core.add_blank_molecule("xy")
    core.add_node("molecule_lerp_scale_x",json.dumps({"target":target,"value":3,"frames":20,"easing":"linear"}))
    core.add_node("molecule_lerp_scale_y",json.dumps({"target":target,"value":5,"frames":20,"easing":"linear"}))
    assert core.evaluated_molecules(10)[target]["scale_x"]==2
    assert core.evaluated_molecules(10)[target]["scale_y"]==3
    lua=core.generate_lua();assert ".LerpScaleX(3" in lua and ".LerpScaleY(5" in lua


def test_arrow_scale_keeps_curve_start_fixed_and_legacy_position_remains_hidden():
    core=CoreSession();core.add_blank_molecule("host")
    arrow=core.add_node("arrow_new",json.dumps({"target":"arrow1"}))
    core.add_node("arrow_set_curve",json.dumps({"target":"arrow1","x1":40,"y1":20,"cx1":50,"cy1":30,"cx2":70,"cy2":40,"x2":80,"y2":60}))
    core.add_node("arrow_set_scale_x",json.dumps({"target":"arrow1","value":2}))
    core.add_node("arrow_set_scale_y",json.dumps({"target":"arrow1","value":3}))
    value=core.evaluated_arrows(0)["arrow1"]
    assert value["start"]=={"x":40.0,"y":20.0} and value["end"]=={"x":120.0,"y":140.0}
    registry={item["type"]:item for item in core.node_registry()};assert registry["arrow_set_position"]["exposure"]=="legacy"
    legacy=core.add_node("arrow_set_position",json.dumps({"target":"arrow1","x":7,"y":9}));assert core.evaluated_arrows(0)["arrow1"]["position"]=={"x":7.0,"y":9.0}
    assert "arrow1.SetPos(7, 9)" in core.generate_lua()
    restored=CoreSession();restored.replace_json(core.json())
    assert next(node for node in restored.project()["nodes"] if node["id"]==legacy)["type"]=="arrow_set_position"
    assert restored.evaluated_arrows(0)["arrow1"]["position"]=={"x":7.0,"y":9.0}


def test_invalid_lifetime_and_stable_member_references_report_diagnostics():
    core=CoreSession();target=core.add_blank_molecule("invalid");create=next(node for node in core.project()["nodes"] if node["type"]=="molecule_create")
    deleted=core.add_node("molecule_delete",json.dumps({"target":target}))
    invalid=core.add_node("atom_set_xy",json.dumps({"target":target,"atom":"A999","x":1,"y":2}))
    messages={item["node_id"]:item["message"] for item in core.diagnostics(0)}
    assert invalid in messages and "已经消失的原子" in messages[invalid]
    raw=json.loads(core.json())
    invalid_node=next(node for node in raw["nodes"] if node["id"]==invalid)
    raw["nodes"].remove(invalid_node)
    delete_index=next(index for index,node in enumerate(raw["nodes"]) if node["id"]==deleted)
    raw["nodes"].insert(delete_index+1,invalid_node)
    lifetime=CoreSession();lifetime.replace_json(json.dumps(raw));messages={item["node_id"]:item["message"] for item in lifetime.diagnostics(0)}
    assert invalid in messages and "已经删除" in messages[invalid]
    create_index=next(index for index,node in enumerate(raw["nodes"]) if node["type"]=="molecule_create");raw["nodes"].insert(create_index+1,{"id":"N999","type":"molecule_create","enabled":True,"params":{"target":target}});raw["next_node_id"]=1000
    legacy=CoreSession();legacy.replace_json(json.dumps(raw));messages={item["node_id"]:item["message"] for item in legacy.diagnostics(0)}
    assert "N999" in messages and "重复" in messages["N999"]


def test_structure_snapshot_edits_its_own_state_without_mutating_created_structure():
    core=session();gesture(core,"single_bond",(420,270),(470,270))
    target=core.active_molecule;identity=json.loads(core.json())["molecules"][0];base=json.loads(json.dumps(structure(core)))
    atom_id=base["atoms"][0]["id"]
    node=core.add_node("molecule_set_structure",json.dumps({"target":target,"snapshot":{}}))
    core.edit_node(node)
    assert core.edit_target_kind=="structure_snapshot" and core.can_edit_structure
    assert core.set_atom_position(atom_id,13.0,-7.0)
    point=next(item["center"] for item in core.depict(False)["atoms"] if item["id"]==atom_id)
    core.set_tool("single_bond");core.pointer_down(point["x"],point["y"]);core.pointer_move(point["x"]+50,point["y"]);assert core.pointer_up(point["x"]+50,point["y"])["changed"]
    project=core.project();assert not project["molecules"][0]["atoms"] and project["molecules"][0]["anchor"]==identity["anchor"]
    first=next(value for value in project["nodes"] if value["type"]=="molecule_set_structure" and value["id"]!=node);assert first["params"]["snapshot"]==base
    params=next(value["params"] for value in project["nodes"] if value["id"]==node)
    assert params["snapshot"]["id"]==target
    stored=next(value for value in params["snapshot"]["atoms"] if value["id"]==atom_id)
    assert (stored["x"],stored["y"])==(13.0,-7.0)
    evaluated=next(value for value in core.evaluated_project(0)["molecules"] if value["id"]==target)
    moved=next(value for value in evaluated["atoms"] if value["id"]==atom_id)
    assert (moved["x"],moved["y"])==(identity["anchor"]["x"]+13.0,identity["anchor"]["y"]-7.0)
    assert len(evaluated["atoms"])==len(base["atoms"])+1 and ":SetStructure({" in core.generate_lua()
    core.preview_timeline(0)
    assert core.edit_target_kind=="timeline_preview" and not core.can_edit_structure
    assert not core.set_atom_position(atom_id,99.0,99.0)
    core.set_viewport(1920,1080,2.0,0.0,0.0)
    final=core.depict_at(120,True)
    assert len(final["rgba"])==1920*1080*4 and any(final["rgba"])


def test_first_nonempty_structure_initializes_real_anchor_without_visual_jump():
    core=CoreSession();target=core.add_blank_molecule("anchor");core.set_viewport(960,540,1,0,0)
    node=core.add_node("molecule_set_structure",json.dumps({"target":target}));core.edit_node(node);core.set_tool("ring6")
    core.pointer_down(650,360);preview=core.pointer_move(650,360)["preview"];assert len(preview["polygon"])==6
    assert core.pointer_up(650,360)["changed"]
    project=core.project();identity=project["molecules"][0];snapshot=next(item for item in project["nodes"] if item["id"]==node)["params"]["snapshot"]
    living=[atom for atom in snapshot["atoms"] if atom.get("alive",True)]
    assert identity["anchor_initialized"] is True
    assert abs((min(atom["x"] for atom in living)+max(atom["x"] for atom in living))*.5)<1e-9
    assert abs((min(atom["y"] for atom in living)+max(atom["y"] for atom in living))*.5)<1e-9
    actual=[item["center"] for item in core.depict(False)["atoms"]]
    assert all(min(math.dist((point["x"],point["y"]),(other["x"],other["y"])) for other in actual)<1e-6 for point in preview["polygon"])
    position=core.add_node("molecule_set_position",json.dumps({"target":target,"x":210.0,"y":-45.0}));core.edit_node(position)
    control=next(item for item in core.direct_controls() if item["id"]=="anchor")
    assert control["position"]=={"x":210.0,"y":-45.0}


def test_initialized_anchor_does_not_drift_after_topology_change_or_roundtrip():
    core=session();gesture(core,"benzene",(620,330));before=core.project()["molecules"][0]["anchor"]
    atom_id=atoms(core)[0]["id"];point=canvas_point(core,atom_id);gesture(core,"single_bond",point)
    after=core.project()["molecules"][0];assert after["anchor_initialized"] is True and after["anchor"]==before
    restored=CoreSession();restored.replace_json(core.json());identity=restored.project()["molecules"][0]
    assert identity["anchor_initialized"] is True and identity["anchor"]==before


def test_existing_v8_without_anchor_flag_is_preserved_and_marked_for_explicit_repair():
    core=session();gesture(core,"benzene",(620,330));raw=json.loads(core.json())
    identity=raw["molecules"][0];anchor=identity["anchor"];identity.pop("anchor_initialized");identity.pop("anchor_needs_repair",None)
    restored=CoreSession();restored.replace_json(json.dumps(raw));loaded=restored.project()["molecules"][0]
    assert loaded["anchor_initialized"] is True and loaded["anchor"]==anchor and loaded["anchor_needs_repair"] is True
    assert any("锚点需要检查" in item["message"] for item in restored.diagnostics(0))


def test_explicit_old_v8_anchor_repair_recentres_local_structure_without_moving_picture():
    core=CoreSession();target=core.import_smiles("old","c1ccccc1");raw=json.loads(core.json())
    identity=next(item for item in raw["molecules"] if item["id"]==target);identity.pop("anchor_initialized",None);identity.pop("anchor_needs_repair",None)
    structure=next(item for item in raw["nodes"] if item["type"]=="molecule_set_structure" and item["params"]["target"]==target)["params"]["snapshot"]
    for atom in structure["atoms"]:atom["x"]+=140.0;atom["y"]-=65.0
    core.replace_json(json.dumps(raw));before=next(item for item in core.evaluated_project(0)["molecules"] if item["id"]==target)
    before_points={atom["id"]:(atom["x"],atom["y"]) for atom in before["atoms"] if atom.get("alive",True)}
    assert core.repair_molecule_anchor(target)
    after=next(item for item in core.evaluated_project(0)["molecules"] if item["id"]==target)
    assert {atom["id"]:(atom["x"],atom["y"]) for atom in after["atoms"] if atom.get("alive",True)}==before_points
    local=next(item for item in core.project()["nodes"] if item["type"]=="molecule_set_structure")["params"]["snapshot"]["atoms"]
    assert abs((min(atom["x"] for atom in local)+max(atom["x"] for atom in local))*.5)<1e-8
    assert core.project()["molecules"][0]["anchor_needs_repair"] is False


def test_first_structure_after_position_nonuniform_scale_and_rotation_does_not_jump():
    core=CoreSession();target=core.add_blank_molecule("molecule");core.set_viewport(960,540,1,0,0)
    core.add_node("molecule_set_position",json.dumps({"target":target,"x":85.0,"y":-35.0}))
    core.add_node("molecule_set_scale_x",json.dumps({"target":target,"value":0.55}))
    core.add_node("molecule_set_scale_y",json.dumps({"target":target,"value":1.7}))
    core.add_node("molecule_set_rotation",json.dumps({"target":target,"value":28.0}))
    node=core.add_node("molecule_set_structure",json.dumps({"target":target}));core.edit_node(node);core.set_tool("benzene")
    core.pointer_down(670,355);preview=core.pointer_move(670,355)["preview"];assert core.pointer_up(670,355)["changed"]
    actual=[item["center"] for item in core.depict(False)["atoms"]]
    assert all(min(math.dist((point["x"],point["y"]),(other["x"],other["y"])) for other in actual)<1e-6 for point in preview["polygon"])


def test_smiles_import_uses_the_same_one_time_anchor_normalization():
    core=CoreSession();target=core.import_smiles("苯","c1ccccc1");project=core.project();identity=next(item for item in project["molecules"] if item["id"]==target)
    snapshot=next(item for item in project["nodes"] if item["type"]=="molecule_set_structure" and item["params"]["target"]==target)["params"]["snapshot"]
    living=[atom for atom in snapshot["atoms"] if atom.get("alive",True)]
    assert identity["anchor_initialized"] is True
    assert abs((min(atom["x"] for atom in living)+max(atom["x"] for atom in living))*.5)<1e-8
    assert abs((min(atom["y"] for atom in living)+max(atom["y"] for atom in living))*.5)<1e-8


def test_script_preview_preserves_each_depiction_viewbox_transform():
    core=session();gesture(core,"ring6",(480,270))
    core.add_node("atom_lerp_xy",json.dumps({"target":core.active_molecule,"atom":atoms(core)[0]["id"],"x":12,"y":5,"frames":30,"easing":"linear"}))
    core.set_viewport(960,540,1.0,0,0)
    drawing=core.depict_at(15,True)
    assert "transform='matrix(" in drawing["svg"]
    rgba=drawing["rgba"]
    assert any(rgba[index+3] for index in range(0,len(rgba),4))


def test_final_molecule_size_scales_with_output_canvas_like_editor_logic_space():
    core=CoreSession();core.import_smiles("苯","c1ccccc1")
    boxes=[]
    for width,height in ((960,540),(1920,1080)):
        core.set_viewport(width,height,width/960.0,0,0)
        drawing=core.depict_at(0,True);image=Image.frombytes("RGBA",(width,height),drawing["rgba"])
        background=Image.new("RGBA",image.size,image.getpixel((0,0)))
        box=ImageChops.difference(image,background).convert("RGB").getbbox();assert box is not None
        boxes.append((box[2]-box[0],box[3]-box[1]))
    assert 1.9<boxes[1][0]/boxes[0][0]<2.1
    assert 1.9<boxes[1][1]/boxes[0][1]<2.1


def test_direct_lerp_edit_order_undo_redo_and_reopen_are_one_authoring_model(tmp_path: Path):
    core=session();gesture(core,"single_bond",(420,270),(452,270));base=json.loads(core.json())
    wait=core.add_node("wait",json.dumps({"frames":10}))
    lerp=core.add_node("molecule_lerp_position",json.dumps({"target":core.active_molecule,
        "x":64.0,"y":0.0,"frames":30,"easing":"linear"}))
    core.edit_node(lerp);assert core.can_direct_manipulate and not core.can_edit_structure
    before_node=next(node for node in core.project()["nodes"] if node["id"]==lerp)["params"]
    first=core.depict(False)["atoms"][0]["center"]
    core.pointer_down(first["x"],first["y"]);core.pointer_move(first["x"]+20,first["y"])
    assert core.pointer_up(first["x"]+20,first["y"])["changed"]
    after_node=next(node for node in core.project()["nodes"] if node["id"]==lerp)["params"]
    assert after_node["x"]==before_node["x"]+20
    assert core.project()["molecules"]==base["molecules"]

    assert core.undo()
    assert next(node for node in core.project()["nodes"] if node["id"]==lerp)["params"]==before_node
    assert core.redo()
    assert next(node for node in core.project()["nodes"] if node["id"]==lerp)["params"]==after_node

    timings={item["id"]:item for item in core.node_timings()};assert timings[lerp]["start"]==10
    core.move_node(lerp,2);timings={item["id"]:item for item in core.node_timings()};assert timings[lerp]["start"]==0
    core.move_node(lerp,len(core.project()["nodes"])-1)
    timings={item["id"]:item for item in core.node_timings()};assert timings[lerp]["start"]==10

    path=tmp_path/"animation-roundtrip.cmm";core.save(str(path));restored=CoreSession();restored.load(str(path))
    assert restored.project()["nodes"]==core.project()["nodes"]
    for frame in (0,10,25,40):assert restored.evaluated_project(frame)==core.evaluated_project(frame)
    lua=restored.generate_lua();assert lua.index("chem.Wait(10)")<lua.index(".LerpPos(")


def test_direct_molecule_axis_drag_updates_only_the_active_node_target():
    core=session();gesture(core,"single_bond",(420,270),(452,270));base=json.loads(core.json())
    for node_type,axis,canvas_delta,model_delta in (("molecule_lerp_x","x",24,24),("molecule_set_y","y",-18,18)):
        node=core.add_node(node_type,json.dumps({"target":core.active_molecule,"value":0.0,"frames":30,"easing":"linear"}))
        core.edit_node(node);assert core.can_direct_manipulate and not core.can_edit_structure
        point=core.depict(False)["atoms"][0]["center"]
        end={"x":point["x"]+(canvas_delta if axis=="x" else 11),"y":point["y"]+(canvas_delta if axis=="y" else 9)}
        core.pointer_down(point["x"],point["y"]);core.pointer_move(end["x"],end["y"])
        assert core.pointer_up(end["x"],end["y"])["changed"]
        params=next(value["params"] for value in core.project()["nodes"] if value["id"]==node)
        assert abs(params["value"]-model_delta)<1e-9
        assert "x" not in params and "y" not in params
        assert core.project()["molecules"]==base["molecules"]


def test_gradient_structure_adds_explicit_h_without_exposing_member_ids_and_roundtrips(tmp_path: Path):
    core=CoreSession();target=core.import_smiles("苯","c1ccccc1");core.set_viewport(960,540,1,0,0)
    identity=json.loads(core.json())["molecules"][0];base=json.loads(json.dumps(structure_for(core,target)))
    node=core.add_node("molecule_gradient_structure",json.dumps({"frames":30,"easing":"linear"}))
    assert core.edit_target_kind=="structure_snapshot" and core.can_edit_structure
    point=core.depict(False)["atoms"][0]["center"]
    core.set_tool("single_bond");core.pointer_down(point["x"],point["y"]);core.pointer_move(point["x"]+50,point["y"])
    assert core.pointer_up(point["x"]+50,point["y"])["changed"]
    end=next(value for value in core.project()["nodes"] if value["id"]==node)["params"]["end_snapshot"]
    new_atom=next(atom for atom in end["atoms"] if atom["id"] not in {value["id"] for value in base["atoms"]})
    endpoint=next(value["center"] for value in core.depict(False)["atoms"] if value["id"]==new_atom["id"])
    core.set_element("H");core.set_tool("atom_label");core.pointer_down(endpoint["x"],endpoint["y"]);assert core.pointer_up(endpoint["x"],endpoint["y"])["changed"]
    current_identity=core.project()["molecules"][0];assert not current_identity["atoms"] and current_identity["anchor"]==identity["anchor"]
    start=next(value for value in core.evaluated_project(0)["molecules"] if value["id"]==target)
    middle=next(value for value in core.evaluated_project(15)["molecules"] if value["id"]==target)
    finish=next(value for value in core.evaluated_project(30)["molecules"] if value["id"]==target)
    assert len(start["atoms"])==6 and len(start["bonds"])==6
    assert next(value for value in middle["atoms"] if value["id"]==new_atom["id"])["alpha"] in (127,128)
    assert next(value for value in finish["atoms"] if value["id"]==new_atom["id"])["label"]=="H"
    assert core.gradient_summary(node)["added_atoms"]==1 and core.gradient_summary(node)["added_bonds"]==1
    assert "LerpStructure" in core.generate_lua()
    path=tmp_path/"gradient.cmm";core.save(str(path));restored=CoreSession();restored.load(str(path))
    assert restored.evaluated_project(15)==core.evaluated_project(15)


def test_gradient_snapshots_are_molecule_local_after_upstream_object_and_global_transforms():
    core=CoreSession();target=core.import_smiles("苯","c1ccccc1");core.set_viewport(960,540,1,0,0)
    core.add_node("molecule_set_position",json.dumps({"target":target,"x":125.0,"y":-75.0}))
    core.add_node("molecule_set_scale_x",json.dumps({"target":target,"value":0.2}))
    core.add_node("molecule_set_scale_y",json.dumps({"target":target,"value":0.35}))
    core.add_node("molecule_set_rotation",json.dumps({"target":target,"value":30.0}))
    core.add_node("molecule_global_set_scale",json.dumps({"value":1.7}))
    core.add_node("wait",json.dumps({"frames":8}))
    node=core.add_node("molecule_gradient_structure",json.dumps({"frames":30,"easing":"linear"}))
    params=next(item for item in core.project()["nodes"] if item["id"]==node)["params"]
    start=params["start_snapshot"]
    assert params["coordinate_space"]=="molecule_local_v2"
    by_id={atom["id"]:atom for atom in start["atoms"]}
    original=start["bonds"][0];a=by_id[original["a"]];b=by_id[original["b"]]
    assert math.isclose(math.hypot(a["x"]-b["x"],a["y"]-b["y"]),start["reference_bond_length"],rel_tol=1e-6)

    point=next(item["center"] for item in core.depict(False)["atoms"] if item["id"]==a["id"])
    core.set_tool("single_bond");core.pointer_down(point["x"],point["y"]);assert core.pointer_up(point["x"],point["y"])["changed"]
    end=next(item for item in core.project()["nodes"] if item["id"]==node)["params"]["end_snapshot"]
    added=next(bond for bond in end["bonds"] if bond["id"] not in {item["id"] for item in start["bonds"]})
    end_atoms={atom["id"]:atom for atom in end["atoms"]};first=end_atoms[added["a"]];second=end_atoms[added["b"]]
    assert math.isclose(math.hypot(first["x"]-second["x"],first["y"]-second["y"]),end["reference_bond_length"],rel_tol=1e-6)


def test_gradient_local_coordinate_space_matrix_two_outward_click_bonds_and_roundtrip():
    transform_cases=[
        [],
        [("molecule_set_position",{"x":80.0,"y":-45.0})],
        [("molecule_set_scale",{"value":0.2})],
        [("molecule_set_scale",{"value":2.0})],
        [("molecule_set_scale_x",{"value":0.35}),("molecule_set_scale_y",{"value":1.8})],
        [("molecule_set_rotation",{"value":37.0})],
        [("molecule_global_set_scale",{"value":1.6})],
        [("molecule_set_position",{"x":-70.0,"y":55.0}),("molecule_set_scale_x",{"value":0.4}),("molecule_set_scale_y",{"value":1.7}),("molecule_set_rotation",{"value":-28.0}),("molecule_global_set_scale_x",{"value":1.3}),("molecule_global_set_scale_y",{"value":0.75}),("molecule_lerp_scale",{"value":0.8,"frames":6,"easing":"linear"})],
    ]
    for case_index,case in enumerate(transform_cases):
        for canvas_zoom in (0.5,1.39,2.0):
            core=CoreSession();target=core.import_smiles(f"matrix-{case_index}-{canvas_zoom}","c1ccccc1")
            for node_type,params in case:core.add_node(node_type,json.dumps({"target":target,**params} if not node_type.startswith("molecule_global_") else params))
            core.add_node("wait",json.dumps({"frames":8}))
            node=core.add_node("molecule_gradient_structure",json.dumps({"frames":30,"easing":"linear"}))
            params=next(item for item in core.project()["nodes"] if item["id"]==node)["params"]
            assert params["coordinate_space"]=="molecule_local_v2"
            start=params["start_snapshot"];original_atoms={atom["id"]:atom for atom in start["atoms"] if atom.get("alive",True)};original_bonds={bond["id"] for bond in start["bonds"]}
            center=(sum(atom["x"] for atom in original_atoms.values())/len(original_atoms),sum(atom["y"] for atom in original_atoms.values())/len(original_atoms))
            ppu=48.0*canvas_zoom;core.set_viewport(960,540,ppu,0,0);core.set_tool("single_bond")
            for atom_id in list(original_atoms)[:2]:
                point=next(item["center"] for item in core.depict(False)["atoms"] if item["id"]==atom_id);screen=(point["x"],point["y"])
                core.pointer_down(*screen);assert core.pointer_up(*screen)["changed"]
            end=next(item for item in core.project()["nodes"] if item["id"]==node)["params"]["end_snapshot"]
            end_atoms={atom["id"]:atom for atom in end["atoms"] if atom.get("alive",True)};added_bonds=[bond for bond in end["bonds"] if bond["id"] not in original_bonds and bond.get("alive",True)]
            assert len(added_bonds)==2
            lengths=[]
            for bond in added_bonds:
                a,b=end_atoms[bond["a"]],end_atoms[bond["b"]];lengths.append(math.hypot(a["x"]-b["x"],a["y"]-b["y"]))
                attachment=a if a["id"] in original_atoms else b;terminal=b if attachment is a else a
                outward=(attachment["x"]-center[0],attachment["y"]-center[1]);new_vector=(terminal["x"]-attachment["x"],terminal["y"]-attachment["y"])
                assert outward[0]*new_vector[0]+outward[1]*new_vector[1]>0
            assert all(math.isclose(length,end["reference_bond_length"],rel_tol=1e-6) for length in lengths)
            assert math.isclose(lengths[0],lengths[1],rel_tol=1e-9)
            for bond in start["bonds"]:
                a,b=original_atoms[bond["a"]],original_atoms[bond["b"]]
                assert math.isclose(math.hypot(a["x"]-b["x"],a["y"]-b["y"]),start["reference_bond_length"],rel_tol=1e-6)

            finish=next(item for item in core.evaluated_project(38)["molecules"] if item["id"]==target);finish_atoms={atom["id"]:atom for atom in finish["atoms"] if atom.get("alive",True)}
            values=core.evaluated_molecules(38)[target];radians=math.radians(values["rotation"]);c,s=math.cos(radians),math.sin(radians)
            for atom_id,local in end_atoms.items():
                x=local["x"]*values["scale_x"];y=local["y"]*values["scale_y"]
                expected=(values["x"]+x*c-y*s,values["y"]+x*s+y*c);actual=finish_atoms[atom_id]
                assert math.isclose(actual["x"],expected[0],abs_tol=1e-7) and math.isclose(actual["y"],expected[1],abs_tol=1e-7)
            restored=CoreSession();restored.replace_json(core.json());saved=next(item for item in restored.project()["nodes"] if item["id"]==node)["params"]
            assert saved["start_snapshot"]==start and saved["end_snapshot"]==end
            assert restored.evaluated_project(38)==core.evaluated_project(38) and "LerpStructure" in restored.generate_lua()


def test_unmarked_b719_gradient_requires_explicit_local_space_rebuild():
    core=CoreSession();core.import_smiles("旧渐变","c1ccccc1");node=core.add_node("molecule_gradient_structure",json.dumps({"frames":30}))
    raw=json.loads(core.json());stored=next(item for item in raw["nodes"] if item["id"]==node);stored["params"].pop("coordinate_space")
    legacy=CoreSession();legacy.replace_json(json.dumps(raw));legacy.edit_node(node)
    assert not legacy.can_edit_structure and legacy.edit_target_kind=="script_node"
    summary=legacy.gradient_summary(node);assert summary["legacy_coordinate_space"] and summary["needs_review"]
    assert any("旧渐变结构使用了显示坐标" in item["message"] for item in legacy.diagnostics(30))
    assert legacy.rebuild_gradient(node);rebuilt=next(item for item in legacy.project()["nodes"] if item["id"]==node)["params"]
    assert rebuilt["coordinate_space"]=="molecule_local_v2" and legacy.can_edit_structure


def test_gradient_structure_deletion_motion_and_visual_change_crossfade():
    core=CoreSession();target=core.import_smiles("苯","c1ccccc1");core.set_viewport(960,540,1,0,0)
    node=core.add_node("molecule_gradient_structure",json.dumps({"frames":20,"easing":"linear"}))
    end=next(value for value in core.project()["nodes"] if value["id"]==node)["params"]["end_snapshot"]
    moved_id=end["atoms"][0]["id"];deleted_id=end["atoms"][1]["id"]
    changed_bond=next(bond["id"] for bond in end["bonds"] if deleted_id not in (bond["a"],bond["b"]))
    changed_atom=end["atoms"][2]["id"]
    end["atoms"][0]["x"]+=20;end["atoms"][1]["alive"]=False;end["atoms"][2]["label"]="N"
    for bond in end["bonds"]:
        if deleted_id in (bond["a"],bond["b"]):bond["alive"]=False
        if bond["id"]==changed_bond:bond["type"]="triple"
    params=next(value for value in core.project()["nodes"] if value["id"]==node)["params"];params["end_snapshot"]=end
    assert core.update_node(node,json.dumps(params))
    middle=next(value for value in core.evaluated_project(10)["molecules"] if value["id"]==target)
    finish=next(value for value in core.evaluated_project(20)["molecules"] if value["id"]==target)
    assert next(value for value in middle["atoms"] if value["id"]==moved_id)["x"]==end["atoms"][0]["x"]-10
    assert next(value for value in middle["atoms"] if value["id"]==deleted_id)["alpha"] in (127,128)
    assert any(value["id"]=="__gradient_old_atom__"+changed_atom for value in middle["atoms"])
    assert any(value["id"].startswith("__gradient_old_bond__") for value in middle["bonds"])
    assert not any(value["id"]==deleted_id and value["alive"] for value in finish["atoms"])
    assert next(value for value in finish["bonds"] if value["id"]==changed_bond)["type"]=="triple"


def test_gradient_structure_undo_duplicate_move_and_upstream_review():
    core=CoreSession();core.import_smiles("苯","c1ccccc1")
    node=core.add_node("molecule_gradient_structure",json.dumps({"frames":30,"easing":"linear"}))
    assert core.undo() and not any(value["id"]==node for value in core.project()["nodes"])
    assert core.redo();copy=core.duplicate_node(node);assert copy
    original=next(value for value in core.project()["nodes"] if value["id"]==node)["params"]
    duplicated=next(value for value in core.project()["nodes"] if value["id"]==copy)["params"]
    assert duplicated["end_snapshot"]==original["end_snapshot"] and duplicated["needs_review"]
    assert core.move_node(node,len(core.project()["nodes"])-1)
    assert core.gradient_summary(node)["needs_review"]
    assert core.rebuild_gradient(node) and not core.gradient_summary(node)["needs_review"]


def test_living_molecule_targets_are_resolved_at_the_exact_insertion_point():
    core=CoreSession();first=core.import_smiles("first","c1ccccc1")
    before_second=len(core.project()["nodes"]);second=core.import_smiles("second","O=[N+]=O")
    assert list(core.living_molecule_targets(before_second))==[first]
    assert list(core.living_molecule_targets())==[first,second]
    node=core.add_node("molecule_gradient_structure",json.dumps({"target":second,"frames":18,"easing":"linear"}))
    params=next(item for item in core.project()["nodes"] if item["id"]==node)["params"]
    assert params["target"]==second
    assert params["start_snapshot"]["id"]==second and params["end_snapshot"]["id"]==second
    assert core.active_molecule==second


def test_merge_then_gradient_is_one_undo_and_lifecycle_block_cannot_be_orphaned():
    core=CoreSession();first=core.import_smiles("first","c1ccccc1");second=core.import_smiles("second","O=[N+]=O")
    before=core.project();gradient=core.create_merged_gradient(first,second,30,"linear")
    project=core.project();created,merge,node=project["nodes"][-3:]
    assert [created["type"],merge["type"],node["type"]]==["molecule_create","merge_molecules","molecule_gradient_structure"]
    assert node["id"]==gradient and node["params"]["target"]==merge["params"]["output"]
    start=node["params"]["start_snapshot"]
    assert len([atom for atom in start["atoms"] if atom.get("alive",True)])==9
    assert not core.delete_node(merge["id"])  # the gradient consumes its output
    assert core.undo();restored=core.project()
    assert restored["nodes"]==before["nodes"] and restored["molecules"]==before["molecules"]
    assert core.redo() and any(item["id"]==gradient for item in core.project()["nodes"])
    assert core.delete_node(gradient)
    merge=next(item for item in core.project()["nodes"] if item["type"]=="merge_molecules" and item.get("params",{}).get("operation_version")=="object_v1")
    output=merge["params"]["output"];assert core.delete_node(merge["id"])
    assert not any(item.get("params",{}).get("target")==output or item.get("params",{}).get("output")==output for item in core.project()["nodes"])


def test_gradient_component_selection_drag_snap_alt_and_cancel_are_atomic():
    core=CoreSession();core.set_viewport(960,540,1,0,0)
    ring=core.import_smiles("ring","c1ccccc1");nitro=core.import_smiles("nitro","O=[N+]=O")
    core.add_node("molecule_set_position",json.dumps({"target":nitro,"x":120.0,"y":0.0}))
    gradient=core.create_merged_gradient(ring,nitro,30,"linear");core.edit_node(gradient);core.set_tool("move")
    nodes=core.project()["nodes"];merge=next(item for item in nodes if item["type"]=="merge_molecules" and item.get("params",{}).get("output")==core.active_molecule)
    mapping=merge["params"]["id_map"];source_atoms=set(mapping["source"]["atoms"].values());target_atoms=set(mapping["target"]["atoms"].values())
    end=next(item for item in nodes if item["id"]==gradient)["params"]["end_snapshot"]
    nitrogen=next(atom["id"] for atom in end["atoms"] if atom["id"] in source_atoms and (atom.get("label") or atom.get("element"))=="N")
    selected=core.select_connected_component(nitrogen)
    assert set(selected["selected_atoms"])==source_atoms
    drawing=core.depict(False);points={item["id"]:item["center"] for item in drawing["atoms"]}
    pivot=points[nitrogen];stationary=points[next(iter(target_atoms))]
    destination=(stationary["x"]+32.0,stationary["y"])
    core.pointer_down(pivot["x"],pivot["y"]);preview=core.pointer_move(*destination)["preview"]
    assert preview["snap_atom"] in target_atoms and preview["text"].startswith("1.00×")
    assert core.pointer_up(*destination)["changed"]
    after=next(item for item in core.project()["nodes"] if item["id"]==gradient)["params"]["end_snapshot"]
    moved=next(atom for atom in after["atoms"] if atom["id"]==nitrogen)
    target=next(atom for atom in after["atoms"] if atom["id"]==preview["snap_atom"])
    assert math.isclose(math.hypot(moved["x"]-target["x"],moved["y"]-target["y"]),after["reference_bond_length"],rel_tol=1e-7)
    # Alt bypasses the chemical snap, and Esc/cancel restores the private endpoint draft.
    core.pointer_down(*destination);unsnapped=core.pointer_move(stationary["x"]+32.0,stationary["y"],True)["preview"]
    assert unsnapped["snap_atom"] is None
    before_cancel=next(item for item in core.project()["nodes"] if item["id"]==gradient)["params"]["end_snapshot"]
    core.cancel_gesture();assert next(item for item in core.project()["nodes"] if item["id"]==gradient)["params"]["end_snapshot"]==before_cancel


def test_double_to_single_keeps_primary_stroke_and_fades_only_secondary_glyph():
    core=CoreSession();target=core.import_smiles("alkene","C=C")
    node=core.add_node("molecule_gradient_structure",json.dumps({"target":target,"frames":30,"easing":"linear"}))
    params=next(item for item in core.project()["nodes"] if item["id"]==node)["params"]
    bond=params["end_snapshot"]["bonds"][0];bond["type"]="single"
    assert core.update_node(node,json.dumps(params))
    middle=next(item for item in core.evaluated_project(15)["molecules"] if item["id"]==target)
    common=next(item for item in middle["bonds"] if item["id"]==bond["id"])
    extra=next(item for item in middle["bonds"] if item["id"].startswith("__gradient_secondary_bond__"))
    assert common["type"]=="single" and common["alpha"]==255 and 120<=extra["alpha"]<=135
    core.preview_timeline(15)
    # The transient secondary stroke is a visual overlay with the same atom
    # endpoints.  Depiction must not feed both edges to RDKit's topology model.
    assert "<svg" in core.depict(False)["svg"]
    assert core.gradient_summary(node)["changed_bonds"]==1


def test_merge_bakes_each_source_object_appearance_without_recolouring_the_other_component():
    core=CoreSession();first=core.import_smiles("first","C");second=core.import_smiles("second","O")
    for target in (first,second):
        node=next(item for item in core.project()["nodes"] if item["type"]=="molecule_set_structure" and item["params"]["target"]==target)
        params=node["params"]
        for atom in params["snapshot"]["atoms"]:atom["color"]={"r":255,"g":255,"b":255}
        assert core.update_node(node["id"],json.dumps(params))
    core.add_node("molecule_set_color",json.dumps({"target":first,"r":255,"g":0,"b":0}));core.add_node("molecule_set_alpha",json.dumps({"target":first,"value":128}))
    core.add_node("molecule_set_color",json.dumps({"target":second,"r":0,"g":0,"b":255}));core.add_node("molecule_set_alpha",json.dumps({"target":second,"value":64}))
    gradient=core.create_merged_gradient(first,second,12,"linear");project=core.project();merge=next(item for item in project["nodes"] if item["type"]=="merge_molecules" and item.get("params",{}).get("output")==core.active_molecule)
    start=next(item for item in project["nodes"] if item["id"]==gradient)["params"]["start_snapshot"]
    by_id={atom["id"]:atom for atom in start["atoms"]};first_id=next(iter(merge["params"]["id_map"]["target"]["atoms"].values()));second_id=next(iter(merge["params"]["id_map"]["source"]["atoms"].values()))
    assert by_id[first_id]["color"]=={"r":255,"g":0,"b":0} and by_id[first_id]["alpha"]==128
    assert by_id[second_id]["color"]=={"r":0,"g":0,"b":255} and by_id[second_id]["alpha"]==64
    assert merge["params"]["r"]==merge["params"]["g"]==merge["params"]["b"]==255 and merge["params"]["alpha"]==255


def test_one_merged_gradient_expresses_nitro_attack_geometry_bond_charge_h_and_bond_order_together():
    core=CoreSession();ring=core.import_smiles("ring","c1ccccc1");nitro=core.import_smiles("nitro","O=[N+]=O")
    core.add_node("molecule_set_position",json.dumps({"target":nitro,"x":115.0,"y":0.0}))
    node=core.create_merged_gradient(ring,nitro,30,"linear");project=core.project();gradient=next(item for item in project["nodes"] if item["id"]==node);merge=next(item for item in project["nodes"] if item["type"]=="merge_molecules" and item["params"].get("output")==gradient["params"]["target"])
    params=gradient["params"];start=params["start_snapshot"];end=json.loads(json.dumps(params["end_snapshot"]));atoms_by_id={atom["id"]:atom for atom in end["atoms"]}
    source_ids=set(merge["params"]["id_map"]["source"]["atoms"].values());ring_ids=set(merge["params"]["id_map"]["target"]["atoms"].values())
    nitrogen=next(atom for atom in end["atoms"] if atom["id"] in source_ids and (atom.get("label") or atom.get("element"))=="N")
    oxygens=[atom for atom in end["atoms"] if atom["id"] in source_ids and (atom.get("label") or atom.get("element"))=="O"]
    carbon=next(atom for atom in end["atoms"] if atom["id"] in ring_ids);length=end["reference_bond_length"]
    old_n=(nitrogen["x"],nitrogen["y"]);old_vectors=[(atom["x"]-old_n[0],atom["y"]-old_n[1]) for atom in oxygens]
    first_angle=math.atan2(old_vectors[0][1],old_vectors[0][0]);second_angle=math.atan2(old_vectors[1][1],old_vectors[1][0]);delta=(second_angle-first_angle+math.pi)%(2*math.pi)-math.pi
    if abs(delta)<math.pi*.9:delta=math.pi if delta>=0 else -math.pi
    centre=first_angle+delta*.5;sign=1 if delta>=0 else -1
    new_n=(carbon["x"]+length,carbon["y"]);nitrogen["x"],nitrogen["y"]=new_n
    for atom,angle in zip(oxygens,(centre-sign*math.pi/3,centre+sign*math.pi/3)):
        atom["x"]=new_n[0]+length*math.cos(angle);atom["y"]=new_n[1]+length*math.sin(angle)
    new_bond=f'B{end["next_bond_id"]}';end["next_bond_id"]+=1
    end["bonds"].append({"id":new_bond,"a":carbon["id"],"b":nitrogen["id"],"type":"single","secondary_line_side":"center","stereo":"none","visible":True,"alive":True,"alpha":255,"color":{"r":0,"g":0,"b":0}})
    changed=next(bond for bond in end["bonds"] if bond["a"] in ring_ids and bond["b"] in ring_ids and bond["type"]=="double");changed["type"]="single"
    positive_carbon=next(atoms_by_id[bond["b"] if bond["a"]==carbon["id"] else bond["a"]] for bond in end["bonds"] if carbon["id"] in (bond["a"],bond["b"]) and (bond["b"] if bond["a"]==carbon["id"] else bond["a"]) in ring_ids)
    adornment=f'D{end["next_adornment_id"]}';end["next_adornment_id"]+=1
    end["adornments"].append({"id":adornment,"creation_serial":999001,"atom":positive_carbon["id"],"text":"⊕","x":18.0,"y":18.0,"alpha":255,"alive":True,"color":{"r":0,"g":0,"b":0}})
    hydrogen=f'A{end["next_atom_id"]}';end["next_atom_id"]+=1
    end["atoms"].append({"id":hydrogen,"creation_serial":999002,"element":"H","label":"H","label_side":"right","number_style":"subscript","isotope":0,"radical_electrons":0,"implicit_hydrogens":0,"hidden":False,"alive":True,"alpha":255,"color":{"r":0,"g":0,"b":0},"x":carbon["x"],"y":carbon["y"]+length})
    h_bond=f'B{end["next_bond_id"]}';end["next_bond_id"]+=1
    end["bonds"].append({"id":h_bond,"a":carbon["id"],"b":hydrogen,"type":"single","secondary_line_side":"center","stereo":"none","visible":True,"alive":True,"alpha":255,"color":{"r":0,"g":0,"b":0}})
    params["end_snapshot"]=end;assert core.update_node(node,json.dumps(params))
    def molecule(frame):return next(item for item in core.evaluated_project(frame)["molecules"] if item["id"]==gradient["params"]["target"])
    beginning,middle,finish=molecule(0),molecule(15),molecule(30)
    assert not any(atom["id"]==hydrogen for atom in beginning["atoms"])
    for stable_id in (new_bond,h_bond):assert 120<=next(bond for bond in middle["bonds"] if bond["id"]==stable_id)["alpha"]<=135
    assert 120<=next(item for item in middle["adornments"] if item["id"]==adornment)["alpha"]<=135
    middle_n=next(atom for atom in middle["atoms"] if atom["id"]==nitrogen["id"]);assert math.isclose(middle_n["x"],(old_n[0]+new_n[0])*.5,abs_tol=1e-6)
    def angle(state):
        by={atom["id"]:atom for atom in state["atoms"]};n=by[nitrogen["id"]];vectors=[(by[o["id"]]["x"]-n["x"],by[o["id"]]["y"]-n["y"]) for o in oxygens]
        return abs(math.degrees(math.acos(max(-1,min(1,(vectors[0][0]*vectors[1][0]+vectors[0][1]*vectors[1][1])/(math.hypot(*vectors[0])*math.hypot(*vectors[1])))))))
    assert 145<=angle(middle)<=155 and 118<=angle(finish)<=122
    assert next(bond for bond in middle["bonds"] if bond["id"]==changed["id"])["type"]=="single"
    assert any(bond["id"].startswith("__gradient_secondary_bond__") for bond in middle["bonds"])
    summary=core.gradient_summary(node);assert summary["added_atoms"]==1 and summary["added_bonds"]==2 and summary["added_adornments"]==1 and summary["changed_bonds"]==1
    assert next(item for item in core.evaluated_project(30)["molecules"] if item["id"]==nitro)["retired"] is True
