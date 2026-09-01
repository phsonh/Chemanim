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
molecule2.SetPos(0, -3.26572479773e-16)
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
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=32, y=9.79717439318e-16 },
        { id="A8", creation_serial=8, element="N", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=1.59974376817e-31, y=-9.79717439318e-16 },
        { id="A9", creation_serial=9, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-32, y=9.79717439318e-16 },
    },
    bonds = {
        { id="B7", a="A7", b="A8", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A8", b="A9", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=10, atom="A8", text="⊕", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
})

molecule1.SetPos(-70, 0)

molecule2.SetPos(105, 0)

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

molecule3:SetStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A10", creation_serial=11, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=32, y=2.36847578587e-15 },
        { id="A11", creation_serial=12, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=-27.7128129211 },
        { id="A12", creation_serial=13, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=-27.7128129211 },
        { id="A13", creation_serial=14, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-32, y=6.28734554314e-15 },
        { id="A14", creation_serial=15, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=27.7128129211 },
        { id="A15", creation_serial=16, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=27.7128129211 },
        { id="A16", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=207, y=9.79717439318e-16 },
        { id="A17", creation_serial=18, element="N", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=175, y=-9.79717439318e-16 },
        { id="A18", creation_serial=19, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=143, y=9.79717439318e-16 },
    },
    bonds = {
        { id="B9", a="A10", b="A11", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B10", a="A11", b="A12", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B11", a="A12", b="A13", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B12", a="A13", b="A14", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B13", a="A14", b="A15", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B14", a="A15", b="A10", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B15", a="A16", b="A17", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B16", a="A17", b="A18", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D2", creation_serial=20, atom="A17", text="⊕", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
})
molecule3.SetPos(-70, 0)
molecule3.SetScaleX(1)
molecule3.SetScaleY(1)
molecule3.SetRotation(0)
molecule3.SetAlpha(255)
molecule3.SetLayer(0)
molecule3.SetVisible(true)
molecule1.Delete()
molecule2.Delete()

molecule3:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A10", creation_serial=11, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=32, y=2.36847578587e-15 },
        { id="A11", creation_serial=12, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=-27.7128129211 },
        { id="A12", creation_serial=13, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=-27.7128129211 },
        { id="A13", creation_serial=14, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-32, y=6.28734554314e-15 },
        { id="A14", creation_serial=15, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=27.7128129211 },
        { id="A15", creation_serial=16, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=27.7128129211 },
        { id="A16", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=207, y=9.79717439318e-16 },
        { id="A17", creation_serial=18, element="N", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=175, y=-9.79717439318e-16 },
        { id="A18", creation_serial=19, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=143, y=9.79717439318e-16 },
    },
    bonds = {
        { id="B9", a="A10", b="A11", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B10", a="A11", b="A12", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B11", a="A12", b="A13", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B12", a="A13", b="A14", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B13", a="A14", b="A15", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B14", a="A15", b="A10", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B15", a="A16", b="A17", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B16", a="A17", b="A18", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D2", creation_serial=20, atom="A17", text="⊕", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A10", creation_serial=11, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=32, y=2.36847578587e-15 },
        { id="A11", creation_serial=12, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=-27.7128129211 },
        { id="A12", creation_serial=13, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=-27.7128129211 },
        { id="A13", creation_serial=14, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-32, y=6.28734554314e-15 },
        { id="A14", creation_serial=15, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16, y=27.7128129211 },
        { id="A15", creation_serial=16, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=16, y=27.7128129211 },
        { id="A16", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=80, y=-27.7128129211 },
        { id="A17", creation_serial=18, element="N", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=64, y=2.36847578587e-15 },
        { id="A18", creation_serial=19, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=80, y=27.7128129211 },
        { id="A19", creation_serial=990002, element="H", label="H", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=64, y=3.29431468357e-15 },
    },
    bonds = {
        { id="B9", a="A10", b="A11", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B10", a="A11", b="A12", order=1, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B11", a="A12", b="A13", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B12", a="A13", b="A14", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B13", a="A14", b="A15", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B14", a="A15", b="A10", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B15", a="A16", b="A17", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B16", a="A17", b="A18", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A10", b="A17", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A10", b="A19", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D2", creation_serial=20, atom="A17", text="⊕", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
        { id="D3", creation_serial=990001, atom="A11", text="⊕", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, 30, "linear")
