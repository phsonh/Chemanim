local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "FFFFFFFF", title = "medium_motion"
}

local molecule1 = chem.NewMol {
    source_smiles = "CCOC(=O)N1CCC(CC1)OC2=CC=CC=C2",
    reference_bond_length = 1.5,
    atoms = {
        { id="A1", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=3, aromatic=false, hidden=false, x=-7.20289786669, y=0.612541236496 },
        { id="A2", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=2, aromatic=false, hidden=false, x=-6.02354767306, y=-0.31435310526 },
        { id="A3", element="O", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=-4.63115852966, y=0.243546951505 },
        { id="A4", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=-3.45180833603, y=-0.683347390251 },
        { id="A5", element="O", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=-3.6648472858, y=-2.16814178877 },
        { id="A6", element="N", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=-2.05941919263, y=-0.125447333486 },
        { id="A7", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=2, aromatic=false, hidden=false, x=-1.84638024286, y=1.35934706504 },
        { id="A8", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=2, aromatic=false, hidden=false, x=-0.453991099459, y=1.9172471218 },
        { id="A9", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=false, hidden=false, x=0.725359094174, y=0.990352780046 },
        { id="A10", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=2, aromatic=false, hidden=false, x=0.512320144405, y=-0.494441618476 },
        { id="A11", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=2, aromatic=false, hidden=false, x=-0.880068998996, y=-1.05234167524 },
        { id="A12", element="O", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=false, hidden=false, x=2.11774823757, y=1.54825283681 },
        { id="A13", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=0, aromatic=true, hidden=false, x=3.29709843121, y=0.621358495055 },
        { id="A14", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=true, hidden=false, x=3.08405948144, y=-0.863435903467 },
        { id="A15", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=true, hidden=false, x=4.26340967507, y=-1.79033024522 },
        { id="A16", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=true, hidden=false, x=5.65579881847, y=-1.23243018846 },
        { id="A17", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=true, hidden=false, x=5.86883776824, y=0.252364210064 },
        { id="A18", element="C", alias="", isotope=0, formal_charge=0, radical_electrons=0, implicit_hydrogens=1, aromatic=true, hidden=false, x=4.68948757461, y=1.17925855182 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, aromatic=false, stereo="none", visible=true },
        { id="B2", a="A2", b="A3", order=1, aromatic=false, stereo="none", visible=true },
        { id="B3", a="A3", b="A4", order=1, aromatic=false, stereo="none", visible=true },
        { id="B4", a="A4", b="A5", order=2, aromatic=false, stereo="none", visible=true },
        { id="B5", a="A4", b="A6", order=1, aromatic=false, stereo="none", visible=true },
        { id="B6", a="A6", b="A7", order=1, aromatic=false, stereo="none", visible=true },
        { id="B7", a="A7", b="A8", order=1, aromatic=false, stereo="none", visible=true },
        { id="B8", a="A8", b="A9", order=1, aromatic=false, stereo="none", visible=true },
        { id="B9", a="A9", b="A10", order=1, aromatic=false, stereo="none", visible=true },
        { id="B10", a="A10", b="A11", order=1, aromatic=false, stereo="none", visible=true },
        { id="B11", a="A9", b="A12", order=1, aromatic=false, stereo="none", visible=true },
        { id="B12", a="A12", b="A13", order=1, aromatic=false, stereo="none", visible=true },
        { id="B13", a="A13", b="A14", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B14", a="A14", b="A15", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B15", a="A15", b="A16", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B16", a="A16", b="A17", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B17", a="A17", b="A18", order=1.5, aromatic=true, stereo="none", visible=true },
        { id="B18", a="A11", b="A6", order=1, aromatic=false, stereo="none", visible=true },
        { id="B19", a="A18", b="A13", order=1.5, aromatic=true, stereo="none", visible=true },
    }
}
molecule1.SetPos(0, 0)
molecule1.SetScale(3.2)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)

chem.SetFrame(0)
molecule1.LerpAtomXY("A1", -6.70289786669, 0.962541236496, 60, "linear")
chem.SetFrame(0)
molecule1.LerpAtomXY("A10", 1.0123201444, -0.144441618476, 60, "linear")
chem.SetFrame(0)
molecule1.LerpAtomXY("A18", 5.18948757461, 1.52925855182, 60, "linear")
