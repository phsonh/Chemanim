from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from . import FORMAT, VERSION


@dataclass
class Atom:
    id: str
    element: str
    x: float
    y: float
    isotope: int = 0
    formal_charge: int = 0
    radical_electrons: int = 0
    implicit_hydrogens: int = 0
    aromatic: bool = False
    chirality: str = ""
    alias: str = ""
    hidden: bool = False


@dataclass
class Bond:
    id: str
    a: str
    b: str
    order: float = 1.0
    aromatic: bool = False
    stereo: str = "none"
    visible: bool = True


@dataclass
class Molecule:
    id: str
    name: str
    source_smiles: str
    reference_bond_length: float = 1.0
    atoms: list[Atom] = field(default_factory=list)
    bonds: list[Bond] = field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    scale: float = 2.2
    alpha: int = 255
    layer: int = 0
    poses: dict[str, Any] = field(default_factory=dict)


@dataclass
class Scene:
    width: int = 1920
    height: int = 1080
    logic_width: int = 960
    logic_height: int = 540
    fps: int = 60
    view_zoom: float = 2.2
    background: str = "FFFFFFFF"
    title: str = "native2d"


@dataclass
class Project:
    mod: str = "native2d_demo"
    scene: Scene = field(default_factory=Scene)
    style: dict[str, Any] = field(default_factory=lambda: {
        "preset": "acs_document_1996", "font_family": "Arial", "font_pt": 10.0,
        "bond_length_pt": 14.4, "line_width_pt": 0.6, "double_bond_spacing": 0.18,
    })
    molecules: list[Molecule] = field(default_factory=list)
    nodes: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {"format": FORMAT, "version": VERSION, **asdict(self)}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        if data.get("format") != FORMAT or data.get("version") != VERSION:
            raise ValueError("这不是 Chemanim 原生二维 v2 工程。旧版贴图 .cmm 请用 Git 中的旧编辑器打开。")
        molecules = []
        for raw in data.get("molecules", []):
            atoms = [Atom(**atom) for atom in raw.get("atoms", [])]
            bonds = [Bond(**bond) for bond in raw.get("bonds", [])]
            values = {k: v for k, v in raw.items() if k not in {"atoms", "bonds"}}
            molecules.append(Molecule(atoms=atoms, bonds=bonds, **values))
        return cls(mod=data.get("mod", "native2d_demo"), scene=Scene(**data.get("scene", {})),
                   style=data.get("style", {}), molecules=molecules, nodes=data.get("nodes", []))


def load_project(path: Path) -> Project:
    return Project.from_dict(json.loads(path.read_text(encoding="utf-8")))


def save_project(project: Project, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.stem + "-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(project.to_dict(), stream, ensure_ascii=False, indent=2)
            stream.write("\n"); stream.flush(); os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try: os.unlink(temporary)
        except FileNotFoundError: pass
        raise
