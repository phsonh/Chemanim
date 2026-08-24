local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "FFFFFFFF", title = "atom_motion"
}

local molecule1 = chem.NewMol {
    source_smiles = "O=C1NCC(=O)N1",
    reference_bond_length = 1.5,
    atoms = {
        { id="A1", element="O", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=2.64011026601, y=-0.612731304037 },
        { id="A2", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=1.21352549156, y=-0.149205812475 },
        { id="A3", element="N", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=false, hidden=false, x=0.75, y=1.27737896197 },
        { id="A4", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=2, aromatic=false, hidden=false, x=-0.75, y=1.27737896197 },
        { id="A5", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=-1.21352549156, y=-0.149205812475 },
        { id="A6", element="O", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=-2.64011026601, y=-0.612731304037 },
        { id="A7", element="N", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=false, hidden=false, x=-1.11022302463e-16, y=-1.03088369091 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=2, aromatic=false, stereo="none", visible=true },
        { id="B2", a="A2", b="A3", order=1, aromatic=false, stereo="none", visible=true },
        { id="B3", a="A3", b="A4", order=1, aromatic=false, stereo="none", visible=true },
        { id="B4", a="A4", b="A5", order=1, aromatic=false, stereo="none", visible=true },
        { id="B5", a="A5", b="A6", order=2, aromatic=false, stereo="none", visible=true },
        { id="B6", a="A5", b="A7", order=1, aromatic=false, stereo="none", visible=true },
        { id="B7", a="A7", b="A2", order=1, aromatic=false, stereo="none", visible=true },
    }
}
molecule1.SetPos(0, 0)
molecule1.SetScale(5)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)

chem.SetFrame(0)
molecule1.LerpAtomXY("A1", 3.19011026601, -0.212731304037, 60, "linear")
chem.SetFrame(0)
molecule1.LerpAtomXY("A2", 2.31352549156, -0.599205812475, 60, "linear")
chem.SetFrame(0)
molecule1.LerpAtomXY("A7", 1.65, -0.630883690913, 60, "linear")
