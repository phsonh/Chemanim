from __future__ import annotations

import argparse
import copy
from dataclasses import dataclass, field
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Iterable

from PIL import Image, ImageChops, ImageDraw, ImageFont, ImageStat
from rdkit import Chem


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from chemanim2d.core import BUILD_COMMIT, CoreSession


@dataclass(frozen=True)
class Reactant:
    name: str
    smiles: str
    x: float
    y: float = 0.0


@dataclass(frozen=True)
class Stage:
    name: str
    smiles: str
    anchors: tuple[int, ...]
    arrows: tuple[tuple[int, int, int], ...] = ()
    frames: int = 36
    hold: int = 18
    offsets: dict[int, tuple[float, float]] = field(default_factory=dict)
    placements: dict[int, tuple[int, float, float]] = field(default_factory=dict)


@dataclass(frozen=True)
class Reaction:
    mod: str
    title: str
    desktop_video: str
    desktop_project: str
    reactants: tuple[Reactant, ...]
    stages: tuple[Stage, ...]


REACTIONS = (
    Reaction(
        mod="mechanism_aldol_hexanedione",
        title="2,5-己二酮分子内羟醛缩合生成3-甲基-2-环戊烯酮",
        desktop_video="2,5-己二酮分子内羟醛缩合机理.mp4",
        desktop_project="2,5-己二酮分子内羟醛缩合机理.cmm",
        reactants=(
            Reactant(
                "2,5-己二酮",
                "[CH3:1][C:2](=[O:3])[CH2:4][CH2:5][C:6](=[O:7])[CH3:8]",
                0.0,
            ),
        ),
        stages=(
            Stage(
                "碱夺取α-H，形成烯醇盐",
                "[CH2:1]=[C:2]([O-:3])[CH2:4][CH2:5][C:6](=[O:7])[CH3:8]",
                (2, 4, 5, 6),
                ((1, 2, 1), (2, 3, -1)),
            ),
            Stage(
                "分子内亲核加成，闭合五元环",
                "[CH2:1]1[C:2](=[O:3])[CH2:4][CH2:5][C:6]1([O-:7])[CH3:8]",
                (2, 4, 5),
                ((1, 6, -1), (6, 7, 1)),
            ),
            Stage(
                "醇盐质子化，得到β-羟基酮",
                "[CH2:1]1[C:2](=[O:3])[CH2:4][CH2:5][C:6]1([OH:7])[CH3:8]",
                (2, 4, 5, 6),
                (),
                hold=24,
            ),
            Stage(
                "E1cb脱水，形成共轭烯酮",
                "[CH:1]1=[C:6]([CH3:8])[CH2:5][CH2:4][C:2]1=[O:3].[OH2:7]",
                (2, 4, 5, 6),
                ((1, 6, 1), (6, 7, -1)),
                hold=36,
                placements={7: (6, 75.0, -55.0)},
            ),
        ),
    ),
    Reaction(
        mod="mechanism_cyclohexanone_ketal",
        title="环己酮与乙二醇酸催化生成环状缩酮",
        desktop_video="环己酮与乙二醇生成缩酮机理.mp4",
        desktop_project="环己酮与乙二醇生成缩酮机理.cmm",
        reactants=(
            Reactant("环己酮", "[O:1]=[C:2]1[CH2:3][CH2:4][CH2:5][CH2:6][CH2:7]1", -155.0),
            Reactant("乙二醇", "[OH:101][CH2:102][CH2:103][OH:104]", 155.0),
        ),
        stages=(
            Stage(
                "羰基氧质子化",
                "[OH+:1]=[C:2]1[CH2:3][CH2:4][CH2:5][CH2:6][CH2:7]1.[OH:101][CH2:102][CH2:103][OH:104]",
                (2, 3, 4, 5, 6, 7),
            ),
            Stage(
                "乙二醇第一次亲核加成",
                "[OH:1][C:2]1([OH+:101][CH2:102][CH2:103][OH:104])[CH2:3][CH2:4][CH2:5][CH2:6][CH2:7]1",
                (2, 3, 4, 5, 6, 7),
                ((101, 2, -1), (2, 1, 1)),
            ),
            Stage(
                "去质子化，形成半缩酮",
                "[OH:1][C:2]1([O:101][CH2:102][CH2:103][OH:104])[CH2:3][CH2:4][CH2:5][CH2:6][CH2:7]1",
                (2, 3, 4, 5, 6, 7),
            ),
            Stage(
                "羟基质子化成为离去基",
                "[OH2+:1][C:2]1([O:101][CH2:102][CH2:103][OH:104])[CH2:3][CH2:4][CH2:5][CH2:6][CH2:7]1",
                (2, 3, 4, 5, 6, 7),
            ),
            Stage(
                "失水并由第二个氧闭环",
                "[OH2:1].[C:2]12([O:101][CH2:102][CH2:103][OH+:104]1)[CH2:3][CH2:4][CH2:5][CH2:6][CH2:7]2",
                (2, 3, 4, 5, 6, 7),
                ((2, 1, -1), (104, 2, 1)),
                placements={1: (2, 90.0, -55.0)},
            ),
            Stage(
                "去质子化，得到环状缩酮",
                "[OH2:1].[C:2]12([O:101][CH2:102][CH2:103][O:104]1)[CH2:3][CH2:4][CH2:5][CH2:6][CH2:7]2",
                (2, 3, 4, 5, 6, 7),
                (),
                hold=36,
                placements={1: (2, 90.0, -55.0)},
            ),
        ),
    ),
    Reaction(
        mod="mechanism_perkin_coumarin",
        title="邻羟基苯甲醛与乙酸酐经Perkin反应生成香豆素",
        desktop_video="Perkin反应合成香豆素机理.mp4",
        desktop_project="Perkin反应合成香豆素机理.cmm",
        reactants=(
            Reactant(
                "邻羟基苯甲醛",
                "[OH:1][c:2]1[cH:3][cH:4][cH:5][cH:6][c:7]1[CH:8]=[O:9]",
                -165.0,
            ),
            Reactant(
                "乙酸酐",
                "[CH3:101][C:102](=[O:103])[O:104][C:105](=[O:106])[CH3:107]",
                165.0,
            ),
        ),
        stages=(
            Stage(
                "乙酸根催化形成乙酸酐烯醇盐",
                "[OH:1][c:2]1[cH:3][cH:4][cH:5][cH:6][c:7]1[CH:8]=[O:9].[CH2:101]=[C:102]([O-:103])[O:104][C:105](=[O:106])[CH3:107]",
                (2, 3, 4, 5, 6, 7),
                ((101, 102, 1), (102, 103, -1)),
            ),
            Stage(
                "烯醇盐进攻醛基",
                "[OH:1][c:2]1[cH:3][cH:4][cH:5][cH:6][c:7]1[CH:8]([O-:9])[CH2:101][C:102](=[O:103])[O:104][C:105](=[O:106])[CH3:107]",
                (2, 3, 4, 5, 6, 7),
                ((101, 8, -1), (8, 9, 1)),
            ),
            Stage(
                "醇盐质子化",
                "[OH:1][c:2]1[cH:3][cH:4][cH:5][cH:6][c:7]1[CH:8]([OH:9])[CH2:101][C:102](=[O:103])[O:104][C:105](=[O:106])[CH3:107]",
                (2, 3, 4, 5, 6, 7),
            ),
            Stage(
                "脱水形成邻羟基肉桂酸混合酸酐",
                "[OH:1][c:2]1[cH:3][cH:4][cH:5][cH:6][c:7]1[CH:8]=[CH:101][C:102](=[O:103])[O:104][C:105](=[O:106])[CH3:107].[OH2:9]",
                (2, 3, 4, 5, 6, 7),
                ((8, 101, 1), (8, 9, -1)),
                placements={9: (2, 120.0, -70.0)},
            ),
            Stage(
                "酚羟基去质子化",
                "[O-:1][c:2]1[cH:3][cH:4][cH:5][cH:6][c:7]1[CH:8]=[CH:101][C:102](=[O:103])[O:104][C:105](=[O:106])[CH3:107].[OH2:9]",
                (2, 3, 4, 5, 6, 7),
                (),
                placements={9: (2, 120.0, -70.0)},
            ),
            Stage(
                "分子内酰基取代并内酯化",
                "[O:1]1[c:2]2[cH:3][cH:4][cH:5][cH:6][c:7]2[CH:8]=[CH:101][C:102]1=[O:103].[OH:104][C:105](=[O:106])[CH3:107].[OH2:9]",
                (2, 3, 4, 5, 6, 7),
                ((1, 102, -1), (102, 104, 1)),
                hold=42,
                placements={
                    9: (2, 125.0, -70.0),
                    104: (2, 90.0, 62.0),
                    105: (2, 118.0, 62.0),
                    106: (2, 134.0, 34.0),
                    107: (2, 134.0, 90.0),
                },
            ),
        ),
    ),
)


def node_by_id(session: CoreSession, node_id: str) -> dict:
    return next(node for node in session.project()["nodes"] if node["id"] == node_id)


def structure_snapshot(session: CoreSession, target: str) -> dict:
    nodes = [
        node
        for node in session.project()["nodes"]
        if node["type"] == "molecule_set_structure" and node.get("params", {}).get("target") == target
    ]
    if not nodes:
        raise RuntimeError(f"missing structure snapshot for {target}")
    return copy.deepcopy(nodes[-1]["params"]["snapshot"])


def rdkit_maps(smiles: str) -> list[int]:
    molecule = Chem.MolFromSmiles(smiles)
    if molecule is None:
        raise ValueError(f"invalid mapped SMILES: {smiles}")
    result = [atom.GetAtomMapNum() for atom in molecule.GetAtoms()]
    if any(value <= 0 for value in result) or len(set(result)) != len(result):
        raise ValueError(f"every heavy atom needs one unique positive map number: {smiles}")
    return result


def imported_template(smiles: str) -> tuple[dict, dict[str, int]]:
    session = CoreSession()
    target = session.import_smiles("stage", smiles)
    snapshot = structure_snapshot(session, target)
    maps = rdkit_maps(smiles)
    if len(snapshot["atoms"]) != len(maps):
        raise RuntimeError(f"Core/RDKit atom count mismatch for {smiles}")
    return snapshot, {atom["id"]: map_number for atom, map_number in zip(snapshot["atoms"], maps)}


def fitted_positions(
    template: dict,
    template_map: dict[str, int],
    current: dict,
    output_by_map: dict[int, str],
    anchors: Iterable[int],
) -> dict[int, tuple[float, float]]:
    template_atoms = {template_map[atom["id"]]: atom for atom in template["atoms"]}
    current_atoms = {atom["id"]: atom for atom in current["atoms"]}
    usable = [value for value in anchors if value in template_atoms and output_by_map[value] in current_atoms]
    if len(usable) < 2:
        raise RuntimeError("at least two stable scaffold atoms are required for alignment")

    destination = [(current_atoms[output_by_map[value]]["x"], current_atoms[output_by_map[value]]["y"]) for value in usable]
    dst_centre = (sum(x for x, _ in destination) / len(destination), sum(y for _, y in destination) / len(destination))
    best = None
    for reflected in (False, True):
        source = [
            ((-template_atoms[value]["x"] if reflected else template_atoms[value]["x"]), template_atoms[value]["y"])
            for value in usable
        ]
        src_centre = (sum(x for x, _ in source) / len(source), sum(y for _, y in source) / len(source))
        src_vectors = [(x - src_centre[0], y - src_centre[1]) for x, y in source]
        dst_vectors = [(x - dst_centre[0], y - dst_centre[1]) for x, y in destination]
        dot = sum(sx * dx + sy * dy for (sx, sy), (dx, dy) in zip(src_vectors, dst_vectors))
        cross = sum(sx * dy - sy * dx for (sx, sy), (dx, dy) in zip(src_vectors, dst_vectors))
        angle = math.atan2(cross, dot)
        src_energy = sum(sx * sx + sy * sy for sx, sy in src_vectors)
        dst_energy = sum(dx * dx + dy * dy for dx, dy in dst_vectors)
        scale = math.sqrt(dst_energy / src_energy) if src_energy > 1e-9 else 1.0
        scale = min(1.15, max(0.85, scale))
        cosine, sine = math.cos(angle), math.sin(angle)
        error = 0.0
        for (sx, sy), (dx, dy) in zip(src_vectors, dst_vectors):
            px = scale * (sx * cosine - sy * sine)
            py = scale * (sx * sine + sy * cosine)
            error += (px - dx) ** 2 + (py - dy) ** 2
        candidate = (error, reflected, scale, angle, src_centre[0], src_centre[1])
        if best is None or candidate[0] < best[0]:
            best = candidate
    assert best is not None
    _, reflected, scale, angle, src_x, src_y = best
    cosine, sine = math.cos(angle), math.sin(angle)
    result: dict[int, tuple[float, float]] = {}
    for map_number, atom in template_atoms.items():
        x = -atom["x"] if reflected else atom["x"]
        x -= src_x
        y = atom["y"] - src_y
        result[map_number] = (
            dst_centre[0] + scale * (x * cosine - y * sine),
            dst_centre[1] + scale * (x * sine + y * cosine),
        )
    return result


def stage_snapshot(current: dict, stage: Stage, output_by_map: dict[int, str]) -> dict:
    template, template_map = imported_template(stage.smiles)
    positions = fitted_positions(template, template_map, current, output_by_map, stage.anchors)
    for map_number, (dx, dy) in stage.offsets.items():
        if map_number in positions:
            positions[map_number] = (positions[map_number][0] + dx, positions[map_number][1] + dy)
    for map_number, (anchor_map, dx, dy) in stage.placements.items():
        if map_number in positions and anchor_map in positions:
            positions[map_number] = (positions[anchor_map][0] + dx, positions[anchor_map][1] + dy)

    result = copy.deepcopy(current)
    current_atoms = {atom["id"]: atom for atom in result["atoms"]}
    template_atoms = {template_map[atom["id"]]: atom for atom in template["atoms"]}
    for map_number, template_atom in template_atoms.items():
        stable_id = output_by_map[map_number]
        atom = current_atoms[stable_id]
        for key in ("element", "hidden", "implicit_hydrogens", "isotope", "label", "label_side", "number_style", "radical_electrons"):
            atom[key] = copy.deepcopy(template_atom[key])
        atom["x"], atom["y"] = positions[map_number]
        atom["alive"] = True
        atom["alpha"] = 255

    bonds_by_pair: dict[frozenset[str], dict] = {}
    for bond in result["bonds"]:
        bond["alive"] = False
        bonds_by_pair.setdefault(frozenset((bond["a"], bond["b"])), bond)
    for template_bond in template["bonds"]:
        a = output_by_map[template_map[template_bond["a"]]]
        b = output_by_map[template_map[template_bond["b"]]]
        pair = frozenset((a, b))
        bond = bonds_by_pair.get(pair)
        if bond is None:
            bond = {
                "id": f'B{result["next_bond_id"]}',
                "a": a,
                "b": b,
                "color": {"r": 0, "g": 0, "b": 0},
                "alpha": 255,
            }
            result["next_bond_id"] += 1
            result["bonds"].append(bond)
            bonds_by_pair[pair] = bond
        bond.update(
            {
                "a": a,
                "b": b,
                "type": template_bond["type"],
                "secondary_line_side": template_bond["secondary_line_side"],
                "stereo": template_bond["stereo"],
                "visible": template_bond["visible"],
                "alive": True,
                "alpha": 255,
            }
        )

    adornments_by_key: dict[tuple[str, str], dict] = {}
    for adornment in result["adornments"]:
        adornment["alive"] = False
        adornments_by_key.setdefault((adornment["atom"], adornment["text"]), adornment)
    for template_adornment in template["adornments"]:
        atom = output_by_map[template_map[template_adornment["atom"]]]
        key = (atom, template_adornment["text"])
        adornment = adornments_by_key.get(key)
        if adornment is None:
            adornment = {
                "id": f'D{result["next_adornment_id"]}',
                "creation_serial": max((value.get("creation_serial", 0) for value in result["atoms"] + result["adornments"]), default=0) + 1,
                "color": {"r": 0, "g": 0, "b": 0},
            }
            result["next_adornment_id"] += 1
            result["adornments"].append(adornment)
            adornments_by_key[key] = adornment
        adornment.update(
            {
                "atom": atom,
                "text": template_adornment["text"],
                "x": template_adornment["x"],
                "y": template_adornment["y"],
                "alpha": 255,
                "alive": True,
            }
        )
    return result


def world_atom(session: CoreSession, target: str, atom_id: str, frame: int) -> tuple[float, float]:
    molecule = next(item for item in session.evaluated_project(frame)["molecules"] if item["id"] == target)
    atom = next(item for item in molecule["atoms"] if item["id"] == atom_id)
    return float(atom["x"]), float(atom["y"])


def create_arrows(
    session: CoreSession,
    target: str,
    output_by_map: dict[int, str],
    specs: Iterable[tuple[int, int, int]],
    counter: list[int],
) -> list[str]:
    frame = session.end_frame
    arrows: list[str] = []
    for start_map, end_map, sign in specs:
        start = world_atom(session, target, output_by_map[start_map], frame)
        end = world_atom(session, target, output_by_map[end_map], frame)
        dx, dy = end[0] - start[0], end[1] - start[1]
        length = max(math.hypot(dx, dy), 1.0)
        nx, ny = -dy / length, dx / length
        counter[0] += 1
        name = f"arrow{counter[0]}"
        session.add_node("arrow_new", json.dumps({"target": name}))
        session.add_node(
            "arrow_set_curve",
            json.dumps(
                {
                    "target": name,
                    "initialized": True,
                    "x1": start[0] + nx * 5.0 * sign,
                    "y1": start[1] + ny * 5.0 * sign,
                    "cx1": start[0] + dx * 0.33 + nx * 24.0 * sign,
                    "cy1": start[1] + dy * 0.33 + ny * 24.0 * sign,
                    "cx2": start[0] + dx * 0.67 + nx * 24.0 * sign,
                    "cy2": start[1] + dy * 0.67 + ny * 24.0 * sign,
                    "x2": end[0] + nx * 5.0 * sign,
                    "y2": end[1] + ny * 5.0 * sign,
                }
            ),
        )
        session.add_node("arrow_set_progress", json.dumps({"target": name, "value": 0.0}))
        session.add_node("arrow_lerp_progress", json.dumps({"target": name, "value": 1.0, "frames": 12, "easing": "ease_out"}))
        arrows.append(name)
    if arrows:
        session.add_node("wait", json.dumps({"frames": 12}))
    return arrows


def add_stage(
    session: CoreSession,
    target: str,
    output_by_map: dict[int, str],
    current: dict,
    stage: Stage,
    arrow_counter: list[int],
) -> tuple[dict, dict]:
    arrows = create_arrows(session, target, output_by_map, stage.arrows, arrow_counter)
    node_id = session.add_node(
        "molecule_gradient_structure",
        json.dumps({"target": target, "frames": stage.frames, "easing": "ease_in_out"}),
    )
    node = node_by_id(session, node_id)
    params = node["params"]
    target_snapshot = stage_snapshot(current, stage, output_by_map)
    params["end_snapshot"] = target_snapshot
    if not session.update_node(node_id, json.dumps(params, ensure_ascii=False)):
        raise RuntimeError(f"failed to update gradient for {stage.name}")
    for arrow in arrows:
        session.add_node("arrow_lerp_alpha", json.dumps({"target": arrow, "value": 0, "frames": stage.frames, "easing": "linear"}))
    session.add_node("wait", json.dumps({"frames": stage.frames}))
    for arrow in arrows:
        session.add_node("arrow_delete", json.dumps({"target": arrow}))
    if stage.hold:
        session.add_node("wait", json.dumps({"frames": stage.hold}))
    return target_snapshot, {
        "name": stage.name,
        "gradient": node_id,
        "start": session.end_frame - stage.hold - stage.frames,
        "end": session.end_frame - stage.hold,
        "summary": session.gradient_summary(node_id),
    }


def initialise_reaction(session: CoreSession, reaction: Reaction) -> tuple[str, dict[int, str], dict]:
    session.new_project()
    session.add_node("molecule_global_set_scale", json.dumps({"value": 1.7}))
    session.add_node("arrow_global_set_color", json.dumps({"r": 45, "g": 125, "b": 205}))
    session.add_node("arrow_global_set_width", json.dumps({"value": 1.5}))
    components: list[tuple[Reactant, str, dict, list[int]]] = []
    for reactant in reaction.reactants:
        target = session.import_smiles(reactant.name, reactant.smiles)
        snapshot = structure_snapshot(session, target)
        maps = rdkit_maps(reactant.smiles)
        components.append((reactant, target, snapshot, maps))
        session.add_node("molecule_set_position", json.dumps({"target": target, "x": reactant.x, "y": reactant.y}))
    session.add_node("wait", json.dumps({"frames": 30}))

    if len(components) == 1:
        _, target, snapshot, maps = components[0]
        return target, {map_number: atom["id"] for atom, map_number in zip(snapshot["atoms"], maps)}, snapshot
    if len(components) != 2:
        raise RuntimeError("the acceptance generator currently supports one or two reactants")
    (_, primary, primary_snapshot, primary_maps), (_, source, source_snapshot, source_maps) = components
    session.set_active_molecule(primary)
    merge_id = session.add_node("merge_molecules", json.dumps({"source": source}))
    merge = node_by_id(session, merge_id)
    target = merge["params"]["output"]
    id_map = merge["params"]["id_map"]
    output_by_map = {
        map_number: id_map["target"]["atoms"][atom["id"]]
        for atom, map_number in zip(primary_snapshot["atoms"], primary_maps)
    }
    output_by_map.update(
        {
            map_number: id_map["source"]["atoms"][atom["id"]]
            for atom, map_number in zip(source_snapshot["atoms"], source_maps)
        }
    )
    return target, output_by_map, copy.deepcopy(merge["params"]["snapshot"])


def save_rgba(drawing: dict, path: Path) -> None:
    Image.frombytes("RGBA", (drawing["width"], drawing["height"]), bytes(drawing["rgba"])).save(path)


def contact_sheet(images: list[tuple[str, Path]], output: Path) -> None:
    opened = [Image.open(path).convert("RGB") for _, path in images]
    width, height = 640, 360
    sheet = Image.new("RGB", (width * len(opened), height + 44), "white")
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    for index, ((label, _), image) in enumerate(zip(images, opened)):
        image.thumbnail((width, height))
        x = index * width + (width - image.width) // 2
        y = (height - image.height) // 2
        sheet.paste(image, (x, y))
        draw.text((index * width + 12, height + 12), label, fill="black", font=font)
    sheet.save(output)


def render_and_verify(session: CoreSession, reaction: Reaction, stages: list[dict], media: Path) -> dict:
    executable = ROOT / "build" / "release" / "chemanim.exe"
    if not executable.exists():
        raise RuntimeError("Release engine is missing; run build.ps1 first")
    scene = session.project()["scene"]
    session.set_viewport(scene["width"], scene["height"], scene["width"] / scene["logic_width"], 0.0, 0.0)
    engine_output = media
    project_path = media / f"{reaction.mod}.cmm"
    keyframes = [15, stages[max(0, len(stages) // 2 - 1)]["end"], stages[-1]["end"]]
    comparisons: dict[str, dict] = {}
    core_images: list[tuple[str, Path]] = []
    for label, frame in zip(("start", "middle", "product"), keyframes):
        core_path = media / f"core-{label}.png"
        save_rgba(session.depict_at(frame, True), core_path)
        core_images.append((label, core_path))
        run = subprocess.run(
            [str(executable), str(project_path), "--frame", str(frame), "--no-open"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if run.returncode:
            raise RuntimeError(run.stdout + "\n" + run.stderr)
        generated = engine_output / f"{reaction.mod}_frame_{frame}.png"
        engine_path = media / f"engine-{label}.png"
        shutil.copy2(generated, engine_path)
        core_image = Image.open(core_path).convert("RGBA")
        engine_image = Image.open(engine_path).convert("RGBA")
        if core_image.size != engine_image.size:
            raise RuntimeError(f"Core/engine size mismatch at frame {frame}")
        difference = ImageChops.difference(core_image, engine_image)
        stats = ImageStat.Stat(difference)
        comparisons[label] = {"frame": frame, "max_rms": max(stats.rms), "bbox": difference.getbbox()}
    contact_sheet(core_images, media / "contact-sheet.png")

    before = set(engine_output.glob(f"{reaction.mod}_*.mp4"))
    run = subprocess.run(
        [str(executable), str(project_path), "--no-open"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=480,
    )
    if run.returncode:
        raise RuntimeError(run.stdout + "\n" + run.stderr)
    created = sorted(set(engine_output.glob(f"{reaction.mod}_*.mp4")) - before, key=lambda value: value.stat().st_mtime)
    if not created:
        candidates = sorted(engine_output.glob(f"{reaction.mod}_*.mp4"), key=lambda value: value.stat().st_mtime)
        created = candidates[-1:]
    if not created:
        raise RuntimeError(f"engine did not produce an MP4 for {reaction.mod}")
    video = media / f"{reaction.mod}.mp4"
    shutil.copy2(created[-1], video)
    return {"keyframes": keyframes, "core_engine": comparisons, "video": str(video)}


def build_reaction(reaction: Reaction, render: bool) -> dict:
    media = ROOT / "media" / "reaction_mechanisms" / reaction.mod
    media.mkdir(parents=True, exist_ok=True)
    session = CoreSession()
    target, output_by_map, current = initialise_reaction(session, reaction)
    arrow_counter = [0]
    stages: list[dict] = []
    for stage in reaction.stages:
        current, record = add_stage(session, target, output_by_map, current, stage, arrow_counter)
        stages.append(record)
    session.add_node("wait", json.dumps({"frames": 60}))

    raw = json.loads(session.json())
    raw["mod"] = reaction.mod
    raw["scene"]["title"] = reaction.title
    session.replace_json(json.dumps(raw, ensure_ascii=False))
    project_path = media / f"{reaction.mod}.cmm"
    session.save(str(project_path))
    reopened = CoreSession()
    reopened.load(str(project_path))
    if reopened.evaluated_project(session.end_frame) != session.evaluated_project(session.end_frame):
        raise RuntimeError(f"save/reopen mismatch for {reaction.mod}")
    lua = session.generate_lua()
    if lua.count("LerpStructure") != len(reaction.stages):
        raise RuntimeError(f"Lua contains the wrong number of structure gradients for {reaction.mod}")
    report = {
        "title": reaction.title,
        "core": BUILD_COMMIT,
        "project": str(project_path),
        "target": target,
        "end_frame": session.end_frame,
        "stages": stages,
        "saved_reopened": True,
        "lua_structure_gradients": lua.count("LerpStructure"),
    }
    if render:
        report.update(render_and_verify(session, reaction, stages, media))
    (media / "acceptance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def validate_reaction(reaction: Reaction) -> None:
    expected: set[int] = set()
    for reactant in reaction.reactants:
        expected.update(rdkit_maps(reactant.smiles))
        imported_template(reactant.smiles)
    for stage in reaction.stages:
        maps = set(rdkit_maps(stage.smiles))
        if maps != expected:
            raise ValueError(f"{reaction.mod}/{stage.name}: atom maps changed: {sorted(expected ^ maps)}")
        imported_template(stage.smiles)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--no-render", action="store_true")
    parser.add_argument("--only", choices=[reaction.mod for reaction in REACTIONS])
    args = parser.parse_args()
    selected = [reaction for reaction in REACTIONS if not args.only or reaction.mod == args.only]
    for reaction in selected:
        validate_reaction(reaction)
    if args.validate_only:
        print(json.dumps({"validated": [reaction.mod for reaction in selected]}, ensure_ascii=False))
        return
    reports = [build_reaction(reaction, not args.no_render) for reaction in selected]
    print(json.dumps(reports, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
