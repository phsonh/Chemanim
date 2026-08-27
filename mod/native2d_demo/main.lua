local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "FFFFFFFF", title = "native2d"
}

local molecule1 = chem.NewMol {
    source_smiles = "CC(C)C1=CC=C(C=C1)[C@@H](C)C(=O)O",
    reference_bond_length = 31.68,
    atoms = {
        { id="A1", creation_serial=1, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
        { id="A2", creation_serial=2, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0.0253445710324, y=31.6807137905 },
        { id="A3", creation_serial=3, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-27.397481286, y=47.5400791141 },
        { id="A4", creation_serial=4, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=27.4735149991, y=47.4957261147 },
        { id="A5", creation_serial=5, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=54.8963408562, y=31.642696934 },
        { id="A6", creation_serial=6, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=82.3445112843, y=47.4513731154 },
        { id="A7", creation_serial=7, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=82.3698558553, y=79.1384230487 },
        { id="A8", creation_serial=8, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=54.9470299983, y=94.9977883722 },
        { id="A9", creation_serial=9, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=27.4988595702, y=79.182776048 },
        { id="A10", creation_serial=10, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=109.818026283, y=94.9534353729 },
        { id="A11", creation_serial=11, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=137.240852141, y=79.0940700494 },
        { id="A12", creation_serial=12, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=109.843370854, y=126.634149163 },
        { id="A13", creation_serial=13, element="O", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=82.4205449974, y=142.49985063 },
        { id="A14", creation_serial=14, element="O", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=137.291541283, y=142.45549763 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A7", b="A8", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A8", b="A9", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B9", a="A7", b="A10", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B10", a="A10", b="A11", order=1, secondary_line_side="center", stereo="dash", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B11", a="A10", b="A12", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B12", a="A12", b="A13", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B13", a="A12", b="A14", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B14", a="A9", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
}
molecule1.SetPos(-62.7689982332, -74.6270894049)
molecule1.SetScale(1)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)
molecule1.SetColor(255, 255, 255)
molecule1.SetVisible(true)

