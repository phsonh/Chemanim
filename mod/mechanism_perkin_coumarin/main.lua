local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    font_pt = 10, bond_length_pt = 14.4,
    line_width_pt = 0.6, double_bond_spacing = 0.18,
    electron_dot_radius_pt = 0.75, default_arrow_width = 1.5,
    background = "FFFFFFFF", title = "邻羟基苯甲醛与乙酸酐经Perkin反应生成香豆素"
}

chem.SetGlobal("molecule", "scale_x", 1.7)
chem.SetGlobal("molecule", "scale_y", 1.7)

chem.SetGlobal("arrow", "r", 45)
chem.SetGlobal("arrow", "g", 125)
chem.SetGlobal("arrow", "b", 205)

chem.SetGlobal("arrow", "width_override", 1.5)

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
molecule1.SetPos(7.93710208263, -8.07955854328)
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
        { id="A1", creation_serial=1, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207067, y=-45.7154623567 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A3", creation_serial=3, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A7", creation_serial=7, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A9", creation_serial=9, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A3", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A7", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A8", b="A9", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B9", a="A7", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
})

molecule1.SetPos(-165, 0)

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
molecule2.SetPos(3.5527136788e-15, -5.71428571429)
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
        { id="A10", creation_serial=10, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-55.4256258422, y=24 },
        { id="A11", creation_serial=11, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-27.7128129211, y=8 },
        { id="A12", creation_serial=12, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-27.7128129211, y=-24 },
        { id="A13", creation_serial=13, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=24 },
        { id="A14", creation_serial=14, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=27.7128129211, y=8 },
        { id="A15", creation_serial=15, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=27.7128129211, y=-24 },
        { id="A16", creation_serial=16, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=55.4256258422, y=24 },
    },
    bonds = {
        { id="B10", a="A10", b="A11", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B11", a="A11", b="A12", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B12", a="A11", b="A13", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B13", a="A13", b="A14", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B14", a="A14", b="A15", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B15", a="A14", b="A16", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
})

molecule2.SetPos(165, 0)

chem.Wait(30)

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
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207067, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=138.692021217, y=24 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=166.404834138, y=8 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=166.404834138, y=-24 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=194.117647059, y=24 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=221.83045998, y=8 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=221.83045998, y=-24 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=249.543272901, y=24 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
})
molecule3.SetPos(-165, 0)
molecule3.SetScaleX(1)
molecule3.SetScaleY(1)
molecule3.SetRotation(0)
molecule3.SetAlpha(255)
molecule3.SetLayer(0)
molecule3.SetVisible(true)
molecule1.Delete()
molecule2.Delete()

local arrow1 = chem.NewArrow { thickness = 1.5 }

arrow1.SetCurve(73.2764360683, 45.1301270189, 98.323324117, 52.6086096908, 114.341329985, 43.3606096908, 120.388218034, 17.9301270189)

arrow1.SetProgress(0)

arrow1.LerpProgress(1, 12, "ease_out")

local arrow2 = chem.NewArrow { thickness = 1.5 }

arrow2.SetCurve(112.888218034, 13.6, 93.8882180341, -4.352, 93.8882180341, -22.848, 112.888218034, -40.8)

arrow2.SetProgress(0)

arrow2.LerpProgress(1, 12, "ease_out")

chem.Wait(12)

molecule3:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207067, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=138.692021217, y=24 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=166.404834138, y=8 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=166.404834138, y=-24 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=194.117647059, y=24 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=221.83045998, y=8 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=221.83045998, y=-24 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=249.543272901, y=24 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207067, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-63.3627279248, y=115.04879569 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-35.6499150037, y=99.0487956901 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-35.6499150037, y=67.0487956901 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-7.93710208263, y=115.04879569 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=19.7757108385, y=99.0487956901 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=19.7757108385, y=67.0487956901 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=47.4885237596, y=115.04879569 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, 36, "ease_in_out")

arrow1.LerpAlpha(0, 36, "linear")

arrow2.LerpAlpha(0, 36, "linear")

chem.Wait(36)

arrow1.Delete()

arrow2.Delete()

chem.Wait(18)

local arrow3 = chem.NewArrow { thickness = 1.5 }

arrow3.SetCurve(-276.474695517, 192.284922999, -234.929502796, 116.139687658, -177.411998195, 50.5993068212, -107.305564335, -0.480902993396)

arrow3.SetProgress(0)

arrow3.LerpProgress(1, 12, "ease_out")

local arrow4 = chem.NewArrow { thickness = 1.5 }

arrow4.SetCurve(-107.24849033, 6.17907807024, -109.24147941, 32.2425064427, -96.8049488308, 45.9331865996, -70.670459215, 46.445784414)

arrow4.SetProgress(0)

arrow4.LerpProgress(1, 12, "ease_out")

chem.Wait(12)

molecule3:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207067, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-63.3627279248, y=115.04879569 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-35.6499150037, y=99.0487956901 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-35.6499150037, y=67.0487956901 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-7.93710208263, y=115.04879569 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=19.7757108385, y=99.0487956901 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=19.7757108385, y=67.0487956901 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=47.4885237596, y=115.04879569 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207067, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=45.9032169249, y=-28.8198415627 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=88.9361947069, y=18.5527541358 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=110.452683598, y=42.239051985 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=98.6908859204, y=-11.9242207687 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=129.962066025, y=-18.7148978239 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=151.478554916, y=4.97140002534 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=139.716757239, y=-49.1918727284 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B31", a="A24", b="A26", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=34, atom="A25", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, 36, "ease_in_out")

arrow3.LerpAlpha(0, 36, "linear")

arrow4.LerpAlpha(0, 36, "linear")

chem.Wait(36)

arrow3.Delete()

arrow4.Delete()

chem.Wait(18)

molecule3:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207067, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=45.9032169249, y=-28.8198415627 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=88.9361947069, y=18.5527541358 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=110.452683598, y=42.239051985 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=98.6908859204, y=-11.9242207687 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=129.962066025, y=-18.7148978239 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=151.478554916, y=4.97140002534 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=139.716757239, y=-49.1918727284 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B31", a="A24", b="A26", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=34, atom="A25", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207067, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=45.9032169249, y=-28.8198415627 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=88.9361947069, y=18.5527541358 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=110.452683598, y=42.239051985 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=98.6908859204, y=-11.9242207687 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=129.962066025, y=-18.7148978239 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=151.478554916, y=4.97140002534 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=139.716757239, y=-49.1918727284 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B31", a="A24", b="A26", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=34, atom="A25", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
    }
}, 36, "ease_in_out")

chem.Wait(36)

chem.Wait(18)

local arrow5 = chem.NewArrow { thickness = 1.5 }

arrow5.SetCurve(-107.24849033, 6.17907807024, -109.24147941, 32.2425064427, -96.8049488308, 45.9331865996, -70.670459215, 46.445784414)

arrow5.SetProgress(0)

arrow5.LerpProgress(1, 12, "ease_out")

local arrow6 = chem.NewArrow { thickness = 1.5 }

arrow6.SetCurve(-108.30953362, 1.29295617891, -120.932855698, -21.5964746506, -115.294644177, -39.2121661453, -91.7265585565, -50.5179011587)

arrow6.SetProgress(0)

arrow6.LerpProgress(1, 12, "ease_out")

chem.Wait(12)

molecule3:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207067, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=45.9032169249, y=-28.8198415627 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=88.9361947069, y=18.5527541358 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=110.452683598, y=42.239051985 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=98.6908859204, y=-11.9242207687 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=129.962066025, y=-18.7148978239 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=151.478554916, y=4.97140002534 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=139.716757239, y=-49.1918727284 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B31", a="A24", b="A26", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=34, atom="A25", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207068, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=103.360856716, y=-85.2384874522 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=88.9361947069, y=18.5527541358 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=110.452683598, y=42.239051985 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=98.6908859204, y=-11.9242207687 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=129.962066025, y=-18.7148978239 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=151.478554916, y=4.97140002534 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=139.716757239, y=-49.1918727284 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=1, secondary_line_side="center", stereo="none", visible=true, alive=false, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B31", a="A24", b="A26", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=34, atom="A25", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
    }
}, 36, "ease_in_out")

arrow5.LerpAlpha(0, 36, "linear")

arrow6.LerpAlpha(0, 36, "linear")

chem.Wait(36)

arrow5.Delete()

arrow6.Delete()

chem.Wait(18)

molecule3:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207068, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=103.360856716, y=-85.2384874522 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=88.9361947069, y=18.5527541358 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=110.452683598, y=42.239051985 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=98.6908859204, y=-11.9242207687 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=129.962066025, y=-18.7148978239 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=151.478554916, y=4.97140002534 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=139.716757239, y=-49.1918727284 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=1, secondary_line_side="center", stereo="none", visible=true, alive=false, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B31", a="A24", b="A26", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=34, atom="A25", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207068, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=103.360856716, y=-85.2384874522 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=88.9361947069, y=18.5527541358 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=110.452683598, y=42.239051985 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=98.6908859204, y=-11.9242207687 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=129.962066025, y=-18.7148978239 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=151.478554916, y=4.97140002534 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=139.716757239, y=-49.1918727284 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=1, secondary_line_side="center", stereo="none", visible=true, alive=false, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B31", a="A24", b="A26", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=34, atom="A25", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D3", creation_serial=35, atom="A17", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, 36, "ease_in_out")

chem.Wait(36)

chem.Wait(18)

local arrow7 = chem.NewArrow { thickness = 1.5 }

arrow7.SetCurve(-173.918444122, -81.8687650353, -109.579588566, -61.5937158928, -54.1952547282, -24.4466867602, -11.0233445999, 27.387203002)

arrow7.SetProgress(0)

arrow7.LerpProgress(1, 12, "ease_out")

local arrow8 = chem.NewArrow { thickness = 1.5 }

arrow8.SetCurve(-9.04644166946, 33.063852533, 14.5216439509, 21.7581175196, 20.1598554723, 4.14242602482, 7.53653339358, -18.7470048046)

arrow8.SetProgress(0)

arrow8.LerpProgress(1, 12, "ease_out")

chem.Wait(12)

molecule3:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207068, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=103.360856716, y=-85.2384874522 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=57.6650146023, y=25.343431191 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=88.9361947069, y=18.5527541358 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=110.452683598, y=42.239051985 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=98.6908859204, y=-11.9242207687 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=129.962066025, y=-18.7148978239 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=151.478554916, y=4.97140002534 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=139.716757239, y=-49.1918727284 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=1, secondary_line_side="center", stereo="none", visible=true, alive=false, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B31", a="A24", b="A26", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=34, atom="A25", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D3", creation_serial=35, atom="A17", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A17", creation_serial=17, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-6.88445207068, y=-45.7154623567 },
        { id="A18", creation_serial=18, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-16.6391432842, y=-15.2384874522 },
        { id="A19", creation_serial=19, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-47.9103233888, y=-8.44781039701 },
        { id="A20", creation_serial=20, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-57.6650146023, y=22.0291645075 },
        { id="A21", creation_serial=21, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-36.1485257113, y=45.7154623567 },
        { id="A22", creation_serial=22, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-4.87734560678, y=38.9247853015 },
        { id="A23", creation_serial=23, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.87734560678, y=8.44781039701 },
        { id="A24", creation_serial=24, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.1485257113, y=1.65713334178 },
        { id="A25", creation_serial=25, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=108.360856716, y=-85.2384874522 },
        { id="A26", creation_serial=26, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=45.9032169249, y=-28.8198415627 },
        { id="A27", creation_serial=27, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=24.3867280339, y=-52.5061394119 },
        { id="A28", creation_serial=28, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=34.1414192474, y=-82.9831143164 },
        { id="A29", creation_serial=29, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=73.3608567158, y=46.7615125478 },
        { id="A30", creation_serial=30, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=101.360856716, y=46.7615125478 },
        { id="A31", creation_serial=31, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=117.360856716, y=18.7615125478 },
        { id="A32", creation_serial=32, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=117.360856716, y=74.7615125478 },
    },
    bonds = {
        { id="B16", a="A17", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A18", b="A19", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A19", b="A20", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A20", b="A21", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B20", a="A21", b="A22", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B21", a="A22", b="A23", order=2, secondary_line_side="right", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B22", a="A23", b="A24", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B23", a="A24", b="A25", order=1, secondary_line_side="center", stereo="none", visible=true, alive=false, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B24", a="A23", b="A18", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B25", a="A26", b="A27", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B26", a="A27", b="A28", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B27", a="A27", b="A29", order=1, secondary_line_side="center", stereo="none", visible=true, alive=false, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B28", a="A29", b="A30", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B29", a="A30", b="A31", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B30", a="A30", b="A32", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B31", a="A24", b="A26", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B32", a="A27", b="A17", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=33, atom="A28", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=34, atom="A25", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D3", creation_serial=35, atom="A17", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
    }
}, 36, "ease_in_out")

arrow7.LerpAlpha(0, 36, "linear")

arrow8.LerpAlpha(0, 36, "linear")

chem.Wait(36)

arrow7.Delete()

arrow8.Delete()

chem.Wait(42)

chem.Wait(60)
