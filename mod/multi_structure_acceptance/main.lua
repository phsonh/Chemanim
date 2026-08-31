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
molecule1.SetPos(0, 0)
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
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=1.18423789293e-15 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=-1.18423789293e-15 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
})

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
molecule2.SetPos(0, 0)
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
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
    },
    bonds = {
    },
    adornments = {
    }
})

molecule1.SetPos(-75, 15)

molecule1.SetRotation(18)

molecule2.SetPos(85, -20)

molecule1:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=1.18423789293e-15 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=-1.18423789293e-15 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=1.18423789293e-15 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=-1.18423789293e-15 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=141.353447804, y=-82.7296971703 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
}, 30, "linear")
molecule2:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
    },
    bonds = {
    },
    adornments = {
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
    },
    bonds = {
    },
    adornments = {
    }
}, 30, "linear")
local __merge_frame = chem.GetFrame()
chem.SetFrame(__merge_frame + 30)
molecule2:Delete()
chem.SetFrame(__merge_frame)

chem.Wait(30)
