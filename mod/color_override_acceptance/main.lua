local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "FFFFFFFF", title = "native2d"
}

local molecule1 = chem.NewMol {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
    },
    bonds = {
    },
    adornments = {
    }
}
molecule1.SetPos(3.5527136788e-15, 0)
molecule1.SetScaleX(1)
molecule1.SetScaleY(1)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)
molecule1.SetVisible(true)

molecule1:SetStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=32, y=2.36847578587e-15 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=-27.7128129211 },
        { id="A3", creation_serial=3, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=-27.7128129211 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-32, y=6.28734554314e-15 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=27.7128129211 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=27.7128129211 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A3", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A1", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
})

molecule1.SetPos(-75, 0)

molecule1.SetScale(1.5)

molecule1.SetColor(255, 0, 0)

molecule1.LerpColor(0, 200, 120, 20, "linear")

local arrow1 = chem.NewArrow()

arrow1.SetCurve(20, -15, 45, 30, 75, 30, 105, -15)

arrow1.SetProgress(1)

arrow1.SetColor(0, 210, 40)

arrow1.LerpColor(80, 40, 220, 20, "linear")

chem.Wait(20)

molecule1.SetAlpha(0)

arrow1.SetAlpha(0)

arrow1.SetWidth(9)

chem.SetGlobal("molecule", "r", 20)
chem.SetGlobal("molecule", "g", 80)
chem.SetGlobal("molecule", "b", 220)

chem.SetGlobal("molecule", "alpha", 180)

chem.SetGlobal("molecule", "scale_x", 2)
chem.SetGlobal("molecule", "scale_y", 2)

chem.SetGlobal("arrow", "r", 230)
chem.SetGlobal("arrow", "g", 100)
chem.SetGlobal("arrow", "b", 20)

chem.SetGlobal("arrow", "alpha", 180)

chem.SetGlobal("arrow", "width_override", 4)
