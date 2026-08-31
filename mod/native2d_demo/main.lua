local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 480, logic_height = 270,
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
molecule1.SetPos(-23.683669106, 11.2168439537)
molecule1.SetScaleX(1)
molecule1.SetScaleY(1)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)
molecule1.SetColor(255, 255, 255)
molecule1.SetVisible(true)

molecule1:SetStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=7, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=-32 },
        { id="A2", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=27.7128129211, y=-16 },
        { id="A3", creation_serial=9, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=27.7128129211, y=16 },
        { id="A4", creation_serial=10, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=3.5527136788e-15, y=32 },
        { id="A5", creation_serial=11, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-27.7128129211, y=16 },
        { id="A6", creation_serial=12, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-27.7128129211, y=-16 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A3", b="A4", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A1", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
})

molecule1.SetPos(0, 0)

local molecule2 = chem.NewMol {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
    },
    bonds = {
    },
    adornments = {
    }
}
molecule2.SetPos(34.4089170055, -50.5219773352)
molecule2.SetScaleX(1)
molecule2.SetScaleY(1)
molecule2.SetRotation(0)
molecule2.SetAlpha(255)
molecule2.SetLayer(0)
molecule2.SetColor(255, 255, 255)
molecule2.SetVisible(true)

molecule2:SetStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A7", creation_serial=13, element="C", label="N", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
        { id="A8", creation_serial=14, element="C", label="O", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=1.95943487864e-15, y=32 },
        { id="A9", creation_serial=15, element="C", label="O", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=1.95943487864e-15, y=-32 },
    },
    bonds = {
        { id="B7", a="A7", b="A8", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A7", b="A9", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=16, atom="A7", text="⊕", x=20, y=0, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
})

molecule2.SetPos(100, 0)

molecule1.SetAlpha(0)

molecule2.SetAlpha(0)

molecule1.LerpAlpha(255, 30, "linear")

chem.Wait(30)

molecule2.LerpAlpha(255, 30, "linear")

chem.Wait(30)

local arrow1 = chem.NewArrow()

arrow1.SetCurve(9.90357619969, 15.3358411994, 0.0965967156728, -32.4086641833, 54.2930622852, 78.5650510305, 88.8650931484, -0.897425919081)

arrow1.SetWidth(1.5)

arrow1.LerpProgress(1, 30, "linear")

chem.Wait(30)

local arrow2 = chem.NewArrow()

arrow2.SetWidth(1.5)

arrow2.SetCurve(92.8940382881, 16.5440083522, 84.4882359597, 12.7550571246, 71.5542045752, 23.8046105007, 90.6821177391, 34.4336433525)

arrow2.LerpProgress(1, 30, "linear")

chem.Wait(30)

arrow1.LerpAlpha(0, 30, "linear")

arrow2.LerpAlpha(0, 30, "linear")

chem.Wait(30)

arrow2.Delete()

arrow1.Delete()

chem.Wait(120)
