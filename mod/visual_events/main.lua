local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "F4F1EAFF", title = "visual_events"
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
molecule1.SetPos(-222.231745334, 67.088009952)
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
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=29.445001708, y=12.5296398358 },
        { id="A3", creation_serial=3, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=55.0184889601, y=-6.70565973985 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=84.4634906681, y=5.82398009599 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A3", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
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
molecule2.SetPos(230, 70)
molecule2.SetScaleX(1)
molecule2.SetScaleY(1)
molecule2.SetRotation(0)
molecule2.SetAlpha(255)
molecule2.SetLayer(0)
molecule2.SetVisible(true)

molecule2:SetStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A5", creation_serial=5, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
    },
    bonds = {
    },
    adornments = {
    }
})

local molecule3 = chem.NewMol {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
    },
    bonds = {
    },
    adornments = {
    }
}
molecule3.SetPos(0, 0)
molecule3.SetScaleX(1)
molecule3.SetScaleY(1)
molecule3.SetRotation(0)
molecule3.SetAlpha(255)
molecule3.SetLayer(0)
molecule3.SetVisible(true)

local molecule4 = chem.NewMol {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
    },
    bonds = {
    },
    adornments = {
    }
}
molecule4.SetPos(-47.7128129211, -175.333333333)
molecule4.SetScaleX(1)
molecule4.SetScaleY(1)
molecule4.SetRotation(0)
molecule4.SetAlpha(255)
molecule4.SetLayer(0)
molecule4.SetVisible(true)

molecule4:SetStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
        { id="A7", creation_serial=7, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=27.7128129211, y=16 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=55.4256258422, y=-2.84217094304e-14 },
    },
    bonds = {
        { id="B4", a="A6", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A7", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
})

chem.Wait(30)

molecule1.DetachSubgraph(molecule3, {"A3","A4",}, {"B3",})

molecule3.LerpPos(-37.2132563739, 150.382350212, 45, "smoothstep")

molecule3.LerpAlpha(0, 45, "linear")

chem.Wait(45)

molecule1.MergeFrom(molecule2, "B900", "A2", "A5", "single", 30, "linear")

molecule4.FormBond("B901", "A6", "A8", "single", "none")
molecule4.SetBondSecondarySide("B901", "center")
molecule4.SetBondAlpha("B901", 0)
molecule4.LerpBondAlpha("B901", 255, 30, "linear")

chem.Wait(45)
