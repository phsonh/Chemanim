from __future__ import annotations

from dataclasses import dataclass
import re

from rdkit import Chem
from rdkit.Chem.Draw import rdMolDraw2D
from rdkit.Geometry import Point3D

from .model import Molecule


@dataclass(frozen=True)
class AcsDepiction:
    svg: str
    width: float
    height: float
    atom_points: dict[str, tuple[float, float]]


def _rdkit_molecule(molecule: Molecule):
    result = Chem.MolFromSmiles(molecule.source_smiles)
    if result is None or result.GetNumAtoms() != len(molecule.atoms):
        raise ValueError("保存的原子数据与源 SMILES 已不一致，无法生成 ACS1996 基准图。")
    result.RemoveAllConformers()
    conformer = Chem.Conformer(result.GetNumAtoms())
    conformer.Set3D(False)
    for index, atom in enumerate(molecule.atoms):
        conformer.SetAtomPosition(index, Point3D(float(atom.x), float(atom.y), 0.0))
    result.AddConformer(conformer, assignId=True)
    Chem.WedgeMolBonds(result, result.GetConformer())
    return result


def render_acs1996(molecule: Molecule) -> AcsDepiction:
    """Render current authoritative XY with RDKit's own ACS 1996 rules."""
    mol = _rdkit_molecule(molecule)
    drawer = rdMolDraw2D.MolDraw2DSVG(-1, -1)
    options = drawer.drawOptions()
    options.fontFile = r"C:\Windows\Fonts\arial.ttf"
    options.clearBackground = False
    reference = molecule.reference_bond_length or rdMolDraw2D.MeanBondLength(mol)
    rdMolDraw2D.SetACS1996Mode(options, reference)
    drawer.DrawMolecule(mol)
    points = {}
    for index, atom in enumerate(molecule.atoms):
        point = drawer.GetDrawCoords(index)
        points[atom.id] = (float(point.x), float(point.y))
    drawer.FinishDrawing()
    svg = drawer.GetDrawingText()
    width_match = re.search(r"width='([0-9.]+)px'", svg)
    height_match = re.search(r"height='([0-9.]+)px'", svg)
    if not width_match or not height_match:
        raise ValueError("RDKit 返回的 ACS1996 SVG 缺少自然尺寸。")
    return AcsDepiction(svg, float(width_match.group(1)), float(height_match.group(1)), points)
