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
    result = CoreSession(); result.add_blank_molecule("manual"); result.set_viewport(960, 540, 1, 0, 0); return result


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
    core.add_node("wait", json.dumps({"frames": 10}))
    tween = core.add_node("atom_lerp_xy", json.dumps({"target": core.active_molecule, "atom": atom["id"], "x": atom["x"] + 2, "y": atom["y"], "frames": 30, "easing": "linear"}))
    core.edit_node(tween)
    point = canvas_point(core, atom["id"]); core.pointer_down(*point); core.pointer_move(point[0], point[1] - 40); assert core.pointer_up(point[0], point[1] - 40)["changed"]
    after = next(item for item in core.project()["molecules"][0]["atoms"] if item["id"] == atom["id"])
    assert (after["x"], after["y"]) == original
    node = next(item for item in core.project()["nodes"] if item["id"] == tween)
    assert node["params"]["y"] != original[1]


def test_later_overlapping_tween_starts_from_current_state():
    core = CoreSession(); core.import_smiles("ethanol", "CCO"); core.set_viewport(960, 540, 48, 0, 0)
    atom = core.project()["molecules"][0]["atoms"][-1]
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
    current={bond["id"]:(bond["type"],bond["secondary_line_side"]) for bond in restored.project()["molecules"][0]["bonds"] if bond["id"] in original}
    assert current==original


def test_imported_pyridine_is_flattened_to_explicit_bonds_and_persisted(tmp_path: Path):
    core=CoreSession();core.import_smiles("pyridine","n1ccccc1")
    explicit={bond["id"]:(bond["type"],bond["secondary_line_side"]) for bond in bonds(core)}
    assert len(explicit)==6 and [value[0] for value in explicit.values()].count("double")==3
    path=tmp_path/"pyridine.cmm";core.save(str(path));restored=CoreSession();restored.load(str(path))
    reopened={bond["id"]:(bond["type"],bond["secondary_line_side"]) for bond in restored.project()["molecules"][0]["bonds"]}
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
    transform = core.depict(False)["transform"]
    click = (transform["origin"]["x"] + midpoint[0] * transform["pixels_per_unit"],
             transform["origin"]["y"] - midpoint[1] * transform["pixels_per_unit"])
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
    transform=core.depict(False)["transform"]
    click=(transform["origin"]["x"]+midpoint[0]*transform["pixels_per_unit"],transform["origin"]["y"]-midpoint[1]*transform["pixels_per_unit"])
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
    assert abs(live_atoms[0]["y"]-live_atoms[1]["y"])<1e-12
    assert abs(abs(live_atoms[1]["x"]-live_atoms[0]["x"])-32.0)<1e-12
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


def test_v5_serialization_contains_no_runtime_aromatic_fields(tmp_path: Path):
    core=CoreSession();core.import_smiles("benzene","c1ccccc1");path=tmp_path/"flat.cmm";core.save(str(path));raw=path.read_text(encoding="utf-8")
    assert '"version": 5' in raw and '"secondary_line_side"' in raw
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
    core=session();gesture(core,"atom_label",(480,270));atom=atoms(core)[0];gesture(core,"charge_positive",canvas_point(core,atom["id"]));adornment=core.project()["molecules"][0]["adornments"][0]
    assert adornment["text"]=="⊕"
    core.set_atom_position(atom["id"],10,20);molecule=core.project()["molecules"][0];moved=next(value for value in molecule["atoms"] if value["id"]==atom["id"]);assert (moved["x"]+adornment["x"],moved["y"]+adornment["y"])==(10+adornment["x"],20+adornment["y"])
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
    charge=core.project()["molecules"][0]["adornments"][0]
    snapped=math.degrees(math.atan2(charge["y"],charge["x"]));assert abs(snapped-15)<1e-9
    svg=core.depict(False)["svg"]
    assert "class='formal-charge'" in svg and "<circle" in svg


def test_anchor_deletion_and_detach_preserve_world_coordinates():
    core=session();gesture(core,"ring5",(480,270));base=core.project()["molecules"][0];ordered=sorted(base["atoms"],key=lambda value:value["creation_serial"]);positions={value["id"]:(value["x"],value["y"]) for value in ordered}
    gesture(core,"eraser",canvas_point(core,ordered[0]["id"]));after={value["id"]:(value["x"],value["y"]) for value in atoms(core) if value["alive"]};assert all(after[key]==positions[key] for key in after)
    destination=core.add_blank_molecule("fragment");source=core.project()["molecules"][0]["id"]
    moving=[ordered[1]["id"],ordered[2]["id"]];core.add_node("detach_subgraph",json.dumps({"target":source,"destination":destination,"atoms":moving,"bonds":[]}))
    evaluated=core.evaluated_project(0);dest=next(value for value in evaluated["molecules"] if value["id"]==destination)
    assert {value["id"]:(value["x"],value["y"]) for value in dest["atoms"]}=={key:positions[key] for key in moving}


def test_form_break_merge_and_intramolecular_form_are_reversible():
    core=CoreSession();first=core.import_smiles("first","CC");second=core.import_smiles("second","O");project=core.project();a=project["molecules"][0]["atoms"][1]["id"];b=project["molecules"][1]["atoms"][0]["id"]
    core.add_node("merge_molecules",json.dumps({"target":first,"source":second,"bond":"B99","a":a,"b":b,"order":"single","frames":30,"easing":"linear"}))
    mid=core.evaluated_project(15);target=next(value for value in mid["molecules"] if value["id"]==first);bond=next(value for value in target["bonds"] if value["id"]=="B99");assert 120<=bond["alpha"]<=135
    assert next(value for value in mid["molecules"] if value["id"]==second)["retired"]
    before=core.evaluated_project(-1);assert not next(value for value in before["molecules"] if value["id"]==second)["retired"]
    # Forming a bond inside one molecule never retires or merges another molecule.
    atom_ids=[value["id"] for value in project["molecules"][0]["atoms"]];core.add_node("bond_form",json.dumps({"target":first,"bond":"B100","a":atom_ids[0],"b":atom_ids[1],"order":"single","frames":30,"easing":"linear"}))
    assert any(value["id"]=="B100" for value in next(value for value in core.evaluated_project(15)["molecules"] if value["id"]==first)["bonds"])


def test_imports_allocate_project_wide_stable_ids_for_ownership_transfer():
    core=CoreSession();first=core.import_smiles("first","CCO");second=core.import_smiles("second","C=O")
    project=core.project();a=next(value for value in project["molecules"] if value["id"]==first);b=next(value for value in project["molecules"] if value["id"]==second)
    assert set(value["id"] for value in a["atoms"]).isdisjoint(value["id"] for value in b["atoms"])
    assert set(value["id"] for value in a["bonds"]).isdisjoint(value["id"] for value in b["bonds"])


def test_visual_events_generate_runtime_lua_without_chemical_fields():
    core=CoreSession();first=core.import_smiles("first","CC");second=core.import_smiles("second","O")
    project=core.project();a=project["molecules"][0]["atoms"][0]["id"];b=project["molecules"][1]["atoms"][0]["id"]
    core.add_node("selection_fade",json.dumps({"target":first,"atoms":[a],"bonds":[],"adornments":[],"value":0,"frames":30,"easing":"linear"}))
    core.add_node("detach_subgraph",json.dumps({"target":first,"destination":second,"atoms":[a],"bonds":[]}))
    core.add_node("merge_molecules",json.dumps({"target":first,"source":second,"bond":"B999","a":a,"b":b,"order":"single","frames":30,"easing":"linear"}))
    lua=core.generate_lua();assert "LerpAtomAlpha" in lua and ".DetachSubgraph(" in lua and ".MergeFrom(" in lua
    assert "aromatic" not in lua and "formal_charge" not in lua and "displayType" not in lua


def test_script_preview_preserves_each_depiction_viewbox_transform():
    core=session();gesture(core,"ring6",(480,270))
    core.add_node("atom_lerp_xy",json.dumps({"target":core.active_molecule,"atom":atoms(core)[0]["id"],"x":12,"y":5,"frames":30,"easing":"linear"}))
    core.set_viewport(960,540,1.0,0,0)
    drawing=core.depict_at(15,True)
    assert "transform='matrix(" in drawing["svg"]
    rgba=drawing["rgba"]
    assert any(rgba[index+3] for index in range(0,len(rgba),4))
