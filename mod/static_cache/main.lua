local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "FFFFFFFF", title = "static_cache"
}

local molecule1 = chem.NewMol {
    source_smiles = "CC(C)C1=CC=C(C=C1)C(C)C(=O)O",
    reference_bond_length = 1.5,
    atoms = {
        { id="A1", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=3, aromatic=false, hidden=false, x=4.16874016349, y=-1.57885367236 },
        { id="A2", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=false, hidden=false, x=3.59488868771, y=-0.192962448726 },
        { id="A3", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=3, aromatic=false, hidden=false, x=4.50817995638, y=0.99695311911 },
        { id="A4", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=true, hidden=false, x=2.10774594328, y=0.00301320707641 },
        { id="A5", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=true, hidden=false, x=1.19445467461, y=-1.18690236076 },
        { id="A6", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=true, hidden=false, x=-0.292688069827, y=-0.990926704957 },
        { id="A7", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=true, hidden=false, x=-0.866539545598, y=0.394964518681 },
        { id="A8", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=true, hidden=false, x=0.0467517230684, y=1.58488008652 },
        { id="A9", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=true, hidden=false, x=1.53389446751, y=1.38890443071 },
        { id="A10", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=false, hidden=false, x=-2.35368229004, y=0.590940174483 },
        { id="A11", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=3, aromatic=false, hidden=false, x=-2.92753376581, y=1.97683139812 },
        { id="A12", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=-3.2669735587, y=-0.598975393353 },
        { id="A13", element="O", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=-2.69312208293, y=-1.98486661699 },
        { id="A14", element="O", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=false, hidden=false, x=-4.75411630314, y=-0.402999737551 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, aromatic=false, stereo="none", visible=true },
        { id="B2", a="A2", b="A3", order=1, aromatic=false, stereo="none", visible=true },
        { id="B3", a="A2", b="A4", order=1, aromatic=false, stereo="none", visible=true },
        { id="B4", a="A4", b="A5", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B5", a="A5", b="A6", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B6", a="A6", b="A7", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B7", a="A7", b="A8", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B8", a="A8", b="A9", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B9", a="A7", b="A10", order=1, aromatic=false, stereo="none", visible=true },
        { id="B10", a="A10", b="A11", order=1, aromatic=false, stereo="none", visible=true },
        { id="B11", a="A10", b="A12", order=1, aromatic=false, stereo="none", visible=true },
        { id="B12", a="A12", b="A13", order=2, aromatic=false, stereo="none", visible=true },
        { id="B13", a="A12", b="A14", order=1, aromatic=false, stereo="none", visible=true },
        { id="B14", a="A9", b="A4", order=1.5, aromatic=true, stereo="none", visible=true },
    }
}
molecule1.SetPos(0, 0)
molecule1.SetScale(4)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)

chem.SetFrame(0)
molecule1.LerpAtomXY("A1", 4.16874016349, -1.57885367236, 60, "linear")
