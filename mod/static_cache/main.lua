local chem = require("chem")

chem.scene {
    width = 1920, height = 1080,
    logic_width = 960, logic_height = 540,
    fps = 60, view_zoom = 2.2,
    background = "FFFFFFFF", title = "static_cache"
}

local molecule1 = chem.NewMol {
    source_smiles = "CC(C)C1=CC=C(C=C1)C(C)C(=O)O",
    reference_bond_length = 57.6,
    atoms = {
        { id="A1", creation_serial=1, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=0, y=0 },
        { id="A2", creation_serial=2, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-22.0358966696, y=53.2182229877 },
        { id="A3", creation_serial=3, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=13.0344880472, y=98.9109807926 },
        { id="A4", creation_serial=4, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-79.142178056, y=60.7436881705 },
        { id="A5", creation_serial=5, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-114.212562773, y=15.0509303656 },
        { id="A6", creation_serial=6, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-171.318844159, y=22.5763955484 },
        { id="A7", creation_serial=7, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-193.354740829, y=75.7946185361 },
        { id="A8", creation_serial=8, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-158.284356112, y=121.487376341 },
        { id="A9", creation_serial=9, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-101.178074726, y=113.961911158 },
        { id="A10", creation_serial=10, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-250.461022215, y=83.3200837189 },
        { id="A11", creation_serial=11, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=3, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-272.496918885, y=136.538306707 },
        { id="A12", creation_serial=12, element="C", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-285.531406932, y=37.627325914 },
        { id="A13", creation_serial=13, element="O", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=0, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-263.495510262, y=-15.5908970737 },
        { id="A14", creation_serial=14, element="O", alias="", isotope=0, radical_electrons=0, implicit_hydrogens=1, hidden=false, alive=true, alpha=255, color_r=0, color_g=0, color_b=0, x=-342.637688318, y=45.1527910968 },
    },
    bonds = {
        { id="B1", a="A1", b="A2", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B2", a="A2", b="A3", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B3", a="A2", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B4", a="A4", b="A5", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B5", a="A5", b="A6", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B6", a="A6", b="A7", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B7", a="A7", b="A8", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B8", a="A8", b="A9", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B9", a="A7", b="A10", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B10", a="A10", b="A11", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B11", a="A10", b="A12", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B12", a="A12", b="A13", order=2, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B13", a="A12", b="A14", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
        { id="B14", a="A9", b="A4", order=1, secondary_line_side="center", stereo="none", visible=true, alive=true, alpha=255, color_r=0, color_g=0, color_b=0 },
    },
    adornments = {
    }
}
molecule1.SetPos(160.079622278, -60.6279810187)
molecule1.SetScale(1)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)
molecule1.SetColor(255, 255, 255)
molecule1.SetVisible(true)

molecule1.LerpAtomXY("A1", -155.910882114, 59.0491273464, 60, "linear")

