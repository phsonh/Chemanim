"""Independent RDKit ACS1996 reference generator.

This script intentionally does not import chemanim_core or any Chemanim Python
package. Run it with the Python interpreter from the project RDKit prefix.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from rdkit import Chem
from rdkit.Chem import rdDepictor
from rdkit.Chem.Draw import rdMolDraw2D


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smiles", required=True)
    parser.add_argument("--png", type=Path, required=True)
    parser.add_argument("--svg", type=Path, required=True)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--font", default="C:/Windows/Fonts/arial.ttf")
    args = parser.parse_args()

    molecule = Chem.MolFromSmiles(args.smiles)
    if molecule is None:
        raise ValueError(f"RDKit could not parse {args.smiles!r}")
    rdDepictor.Compute2DCoords(molecule)
    molecule = rdMolDraw2D.PrepareMolForDrawing(
        molecule, kekulize=True, addChiralHs=False, wedgeBonds=True,
        forceCoords=False, wavyBonds=True)

    cairo = rdMolDraw2D.MolDraw2DCairo(args.width, args.height)
    cairo.drawOptions().fontFile = args.font
    rdMolDraw2D.DrawMoleculeACS1996(cairo, molecule)
    cairo.FinishDrawing()
    args.png.parent.mkdir(parents=True, exist_ok=True)
    args.png.write_bytes(cairo.GetDrawingText())

    svg = rdMolDraw2D.MolDraw2DSVG(args.width, args.height)
    svg.drawOptions().fontFile = args.font
    rdMolDraw2D.DrawMoleculeACS1996(svg, molecule)
    svg.FinishDrawing()
    args.svg.parent.mkdir(parents=True, exist_ok=True)
    args.svg.write_text(svg.GetDrawingText(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
