local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "FFFFFFFF", title = "atom_motion"
}

local molecule1 = chem.NewMol {
    source_smiles = "O=C1NCC(=O)N1",
    reference_bond_length = 72,
    atoms = {
        { id="A1", creation_serial=1, element="O", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
        { id="A2", creation_serial=2, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-68.4760691733, y=22.249223595 },
        { id="A3", creation_serial=3, element="N", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-90.7252927682, y=90.7252927682 },
        { id="A4", creation_serial=4, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-162.725292768, y=90.7252927682 },
        { id="A5", creation_serial=5, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-184.974516363, y=22.249223595 },
        { id="A6", creation_serial=6, element="O", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-253.450585536, y=1.7763568394e-14 },
        { id="A7", creation_serial=7, element="N", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-126.725292768, y=-20.0713145701 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A3", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A5", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A7", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
}
molecule1.SetPos(126.725292768, -29.4111025938)
molecule1.SetScale(1)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)
molecule1.SetColor(255, 255, 255)
molecule1.SetVisible(true)

molecule1.LerpAtomXY("A1", -123.535182502, 29.1983712897, 60, "linear")

molecule1.LerpAtomXY("A2", -124.411767277, 28.8118967813, 60, "linear")

molecule1.LerpAtomXY("A7", -125.075292768, 28.7802189029, 60, "linear")

