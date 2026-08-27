local chem = require("chem")

chem.scene {
    width = 1080, height = 1920,
    logic_width = 540, logic_height = 960,
    fps = 60, view_zoom = 2.2,
    background = "E8EEF6FF", title = "ui_acceptance"
}

molecule1.LerpPos(360, 0, 30, "linear")

chem.Wait(30)

molecule1.LerpAtomXY("A6", -116.442048518, -73.7466307278, 30, "linear")

local arrow2 = chem.NewArrow()

arrow2.SetCurve(0, 0, 80, 80, -80, 80, 160, 0)

arrow2.LerpProgress(1, 30, "linear")

local molecule1 = chem.NewMol {
    source_smiles = "",
    reference_bond_length = 31.68,
    atoms = {
        { id="A1", creation_serial=1, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
        { id="A2", creation_serial=2, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-15.84, y=27.4356847919 },
        { id="A3", creation_serial=3, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-2.84217094304e-14, y=54.8713695838 },
        { id="A4", creation_serial=4, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=31.68, y=54.8713695838 },
        { id="A5", creation_serial=5, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=47.52, y=27.4356847919 },
        { id="A6", creation_serial=6, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=31.68, y=-1.42108547152e-14 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A3", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A1", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
}
molecule1.SetPos(116.442048518, 73.7466307278)
molecule1.SetScale(1)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)
molecule1.SetColor(255, 255, 255)
molecule1.SetVisible(true)

