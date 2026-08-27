local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "FFFFFFFF", title = "medium_motion"
}

local molecule1 = chem.NewMol {
    source_smiles = "CCOC(=O)N1CCC(CC1)OC2=CC=CC=C2",
    reference_bond_length = 46.08,
    atoms = {
        { id="A1", creation_serial=1, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
        { id="A2", creation_serial=2, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=36.2296379484, y=-28.4741941787 },
        { id="A3", creation_serial=3, element="O", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=79.0038324337, y=-11.3355044349 },
        { id="A4", creation_serial=4, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=115.233470382, y=-39.8096986137 },
        { id="A5", creation_serial=5, element="O", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=108.688913845, y=-85.4225825362 },
        { id="A6", creation_serial=6, element="N", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=158.007664867, y=-22.6710088698 },
        { id="A7", creation_serial=7, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=164.552221404, y=22.9418750528 },
        { id="A8", creation_serial=8, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=207.326415889, y=40.0805647966 },
        { id="A9", creation_serial=9, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=243.556053838, y=11.6063706179 },
        { id="A10", creation_serial=10, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=237.011497301, y=-34.0065133047 },
        { id="A11", creation_serial=11, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=2, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=194.237302816, y=-51.1452030486 },
        { id="A12", creation_serial=12, element="O", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=286.330248323, y=28.7450603617 },
        { id="A13", creation_serial=13, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=322.559886272, y=0.270866182939 },
        { id="A14", creation_serial=14, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=316.015329735, y=-45.3420177396 },
        { id="A15", creation_serial=15, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=352.244967683, y=-73.8162119184 },
        { id="A16", creation_serial=16, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=395.019162168, y=-56.6775221746 },
        { id="A17", creation_serial=17, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=401.563718705, y=-11.064638252 },
        { id="A18", creation_serial=18, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=365.334080757, y=17.4095559268 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A3", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A4", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A7", b="A8", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A8", b="A9", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B9", a="A9", b="A10", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B10", a="A10", b="A11", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B11", a="A9", b="A12", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B12", a="A12", b="A13", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B13", a="A13", b="A14", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B14", a="A14", b="A15", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B15", a="A15", b="A16", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B16", a="A16", b="A17", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B17", a="A17", b="A18", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B18", a="A11", b="A6", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B19", a="A18", b="A13", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
}
molecule1.SetPos(-221.273022465, 18.8172667851)
molecule1.SetScale(1)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)
molecule1.SetColor(255, 255, 255)
molecule1.SetVisible(true)

molecule1.LerpAtomXY("A1", 214.570124598, -17.8547255487, 60, "linear")

molecule1.LerpAtomXY("A10", 222.285342609, -18.9617084036, 60, "linear")

molecule1.LerpAtomXY("A18", 226.462510039, -17.2880082333, 60, "linear")

