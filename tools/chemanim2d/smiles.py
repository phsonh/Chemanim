from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D

from .model import Atom, Bond, Molecule


def molecule_from_smiles(name: str, smiles: str, object_id: str = "molecule1") -> Molecule:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("RDKit 无法解析这个 SMILES。请检查括号、环编号和电荷写法。")
    rdDepictor.SetPreferCoordGen(True)
    rdDepictor.Compute2DCoords(mol, canonOrient=True, clearConfs=True)
    conformer = mol.GetConformer()
    Chem.WedgeMolBonds(mol, conformer)
    # Keep aromatic metadata, but export a deterministic Kekule display order.
    # This produces normal publication-style alternating ring bonds without
    # asking the C++ renderer to perceive rings.
    Chem.Kekulize(mol, clearAromaticFlags=False)
    atom_ids: dict[int, str] = {}; atoms: list[Atom] = []; used: set[str] = set()
    for index, source in enumerate(mol.GetAtoms()):
        mapped = source.GetAtomMapNum(); stable_id = f"A{mapped}" if mapped else f"A{index + 1}"
        if stable_id in used: stable_id = f"A{index + 1}"
        used.add(stable_id); atom_ids[index] = stable_id
        point = conformer.GetAtomPosition(index)
        atoms.append(Atom(id=stable_id, element=source.GetSymbol(), x=round(float(point.x), 4),
                          y=round(float(point.y), 4), isotope=source.GetIsotope(),
                          formal_charge=source.GetFormalCharge(), radical_electrons=source.GetNumRadicalElectrons(),
                          implicit_hydrogens=source.GetTotalNumHs(includeNeighbors=False),
                          aromatic=source.GetIsAromatic(), chirality=str(source.GetChiralTag()).removeprefix("CHI_")))
    bonds: list[Bond] = []
    for index, source in enumerate(mol.GetBonds()):
        direction = source.GetBondDir(); stereo = "none"
        if direction == Chem.BondDir.BEGINWEDGE: stereo = "wedge"
        elif direction == Chem.BondDir.BEGINDASH: stereo = "dash"
        elif direction in (Chem.BondDir.ENDUPRIGHT, Chem.BondDir.ENDDOWNRIGHT): stereo = "either"
        bonds.append(Bond(id=f"B{index + 1}", a=atom_ids[source.GetBeginAtomIdx()],
                          b=atom_ids[source.GetEndAtomIdx()], order=float(source.GetBondTypeAsDouble()),
                          aromatic=source.GetIsAromatic(), stereo=stereo))
    return Molecule(id=object_id, name=name, source_smiles=smiles,
                    reference_bond_length=float(rdMolDraw2D.MeanBondLength(mol)), atoms=atoms, bonds=bonds)
