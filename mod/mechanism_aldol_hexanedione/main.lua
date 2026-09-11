local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    font_pt = 10, bond_length_pt = 14.4,
    line_width_pt = 0.6, double_bond_spacing = 0.18,
    electron_dot_radius_pt = 0.75, default_arrow_width = 1.5,
    background = "FFFFFFFF", title = "2,5-己二酮分子内羟醛缩合生成3-甲基-2-环戊烯酮"
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
molecule1.SetPos(0, 5.3290705182e-15)
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
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=66.5217472496, y=20.9489174627 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=42.332020977, y=-1.36187357687e-14 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=48.3794525452, y=-31.423376194 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=12.0948631363, y=10.4744587313 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-12.0948631363, y=-10.4744587313 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-42.332020977, y=5.92118946467e-16 },
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-48.3794525452, y=31.423376194 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-66.5217472496, y=-20.9489174627 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A6", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
})

molecule1.SetPos(0, 0)

chem.Wait(30)

local arrow1 = chem.NewArrow { thickness = 1.5 }

arrow1.SetCurve(116.360238678, 31.8335149564, 115.228221982, 5.71852228552, 101.246560197, -6.38995200789, 75.2377040145, -3.77964473009)

arrow1.SetProgress(0)

arrow1.LerpProgress(1, 12, "ease_out")

local arrow2 = chem.NewArrow { thickness = 1.5 }

arrow2.SetCurve(67.0545331306, -0.944911182523, 51.7895126252, -22.1640877209, 55.2849280716, -40.3267991611, 77.3351667965, -54.3646507123)

arrow2.SetProgress(0)

arrow2.LerpProgress(1, 12, "ease_out")

chem.Wait(12)

molecule1:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=66.5217472496, y=20.9489174627 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=42.332020977, y=-1.36187357687e-14 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=48.3794525452, y=-31.423376194 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=12.0948631363, y=10.4744587313 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-12.0948631363, y=-10.4744587313 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-42.332020977, y=5.92118946467e-16 },
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-48.3794525452, y=31.423376194 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-66.5217472496, y=-20.9489174627 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A6", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=66.5217472496, y=20.9489174627 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=42.332020977, y=-1.36187357687e-14 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=48.3794525452, y=-31.423376194 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=12.0948631363, y=10.4744587313 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-12.0948631363, y=-10.4744587313 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-42.332020977, y=5.92118946467e-16 },
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-48.3794525452, y=31.423376194 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-66.5217472496, y=-20.9489174627 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A6", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=9, atom="A3", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, 36, "ease_in_out")

arrow1.LerpAlpha(0, 36, "linear")

arrow2.LerpAlpha(0, 36, "linear")

chem.Wait(36)

arrow1.Delete()

arrow2.Delete()

chem.Wait(18)

local arrow3 = chem.NewArrow { thickness = 1.5 }

arrow3.SetCurve(112.142059142, 40.5230622168, 47.4844326731, 47.4283491355, -15.4330453619, 35.319874842, -72.9093468435, 4.90990253031)

arrow3.SetProgress(0)

arrow3.LerpProgress(1, 12, "ease_out")

local arrow4 = chem.NewArrow { thickness = 1.5 }

arrow4.SetCurve(-76.8743381913, -0.944911182523, -98.9245769162, 13.0929403687, -102.419992363, 31.2556518088, -87.1549718571, 52.4748283472)

arrow4.SetProgress(0)

arrow4.LerpProgress(1, 12, "ease_out")

chem.Wait(12)

molecule1:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=66.5217472496, y=20.9489174627 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=42.332020977, y=-1.36187357687e-14 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=48.3794525452, y=-31.423376194 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=12.0948631363, y=10.4744587313 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-12.0948631363, y=-10.4744587313 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-42.332020977, y=5.92118946467e-16 },
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-48.3794525452, y=31.423376194 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-66.5217472496, y=-20.9489174627 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A6", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=9, atom="A3", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=37.6766976284, y=-34.356805027 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=41.7960776291, y=-1.31550336586 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=70.9483630023, y=14.7730380402 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=11.6448908039, y=12.8125835565 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-11.108947456, y=-11.4970801906 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.97959395014, y=-40.6493655638 },
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-25.6947026629, y=-53.6025286659 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=14.6554611827, y=-72.509599404 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A6", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A6", b="A1", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=9, atom="A3", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=10, atom="A7", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, 36, "ease_in_out")

arrow3.LerpAlpha(0, 36, "linear")

arrow4.LerpAlpha(0, 36, "linear")

chem.Wait(36)

arrow3.Delete()

arrow4.Delete()

chem.Wait(18)

molecule1:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=37.6766976284, y=-34.356805027 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=41.7960776291, y=-1.31550336586 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=70.9483630023, y=14.7730380402 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=11.6448908039, y=12.8125835565 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-11.108947456, y=-11.4970801906 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.97959395014, y=-40.6493655638 },
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-25.6947026629, y=-53.6025286659 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=14.6554611827, y=-72.509599404 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A6", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A6", b="A1", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=9, atom="A3", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=10, atom="A7", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=true },
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=37.6766976284, y=-34.356805027 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=41.7960776291, y=-1.31550336586 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=70.9483630023, y=14.7730380402 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=11.6448908039, y=12.8125835565 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-11.108947456, y=-11.4970801906 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.97959395014, y=-40.6493655638 },
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-25.6947026629, y=-53.6025286659 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=14.6554611827, y=-72.509599404 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A6", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A6", b="A1", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=9, atom="A3", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=10, atom="A7", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
    }
}, 36, "ease_in_out")

chem.Wait(36)

chem.Wait(24)

local arrow5 = chem.NewArrow { thickness = 1.5 }

arrow5.SetCurve(64.9952971508, -63.3164710763, 50.2428844809, -85.5042271526, 31.3439585548, -89.1413271428, 9.41022089776, -74.0138239888)

arrow5.SetProgress(0)

arrow5.LerpProgress(1, 12, "ease_out")

local arrow6 = chem.NewArrow { thickness = 1.5 }

arrow6.SetCurve(6.52022097232, -64.4977701602, -18.0793966507, -54.2611197273, -35.809140093, -61.7480480003, -45.6260832698, -86.5181474338)

arrow6.SetProgress(0)

arrow6.LerpProgress(1, 12, "ease_out")

chem.Wait(12)

molecule1:LerpStructure({
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=37.6766976284, y=-34.356805027 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=41.7960776291, y=-1.31550336586 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=70.9483630023, y=14.7730380402 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=11.6448908039, y=12.8125835565 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-11.108947456, y=-11.4970801906 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.97959395014, y=-40.6493655638 },
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-25.6947026629, y=-53.6025286659 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=14.6554611827, y=-72.509599404 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A6", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A6", b="A1", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=9, atom="A3", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=10, atom="A7", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
    }
}, {
    source_smiles = "",
    reference_bond_length = 32,
    atoms = {
        { id="A1", creation_serial=1, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=37.6766976284, y=-34.356805027 },
        { id="A2", creation_serial=2, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=41.7960776291, y=-1.31550336586 },
        { id="A3", creation_serial=3, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=70.9483630023, y=14.7730380402 },
        { id="A4", creation_serial=4, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=11.6448908039, y=12.8125835565 },
        { id="A5", creation_serial=5, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-11.108947456, y=-11.4970801906 },
        { id="A6", creation_serial=6, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=4.97959395014, y=-40.6493655638 },
        { id="A7", creation_serial=7, element="O", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=79.9795939501, y=-95.6493655638 },
        { id="A8", creation_serial=8, element="C", label="", label_side="right", number_style="subscript", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-9.14849297221, y=-70.800552389 },
    },
    bonds = {
        { id="B1", a="A2", b="A1", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A4", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A5", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A6", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=false, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A6", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A1", b="A6", order=2, secondary_line_side="left", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
        { id="D1", creation_serial=9, atom="A3", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
        { id="D2", creation_serial=10, atom="A7", text="⊖", x=18, y=18, alpha=255, color_r=0, color_g=0, color_b=0, alive=false },
    }
}, 36, "ease_in_out")

arrow5.LerpAlpha(0, 36, "linear")

arrow6.LerpAlpha(0, 36, "linear")

chem.Wait(36)

arrow5.Delete()

arrow6.Delete()

chem.Wait(36)

chem.Wait(60)
