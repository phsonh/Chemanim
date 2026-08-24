local chem = require("chem")

chem.scene {
    width = 1920,
    height = 1080,
    logic_width = 960,
    logic_height = 540,
    fps = 60,
    view_zoom = 2.2,
    background = "FFFFFFFF",
    title = "native2d"
}

local molecule1 = chem.NewMol {
    source_smiles = "CC(=O)NC1=CC=C(O)C=C1",
    atoms = {
        { id = "A1", element = "C", x = -2.6735, y = -0.9186, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 3, aromatic = false, alias = "", hidden = false },
        { id = "A2", element = "C", x = -1.8093, y = -0.4156, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 0, aromatic = false, alias = "", hidden = false },
        { id = "A3", element = "O", x = -1.8129, y = 0.5844, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 0, aromatic = false, alias = "", hidden = false },
        { id = "A4", element = "N", x = -0.9415, y = -0.9124, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = false, alias = "", hidden = false },
        { id = "A5", element = "C", x = -0.0773, y = -0.4094, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 0, aromatic = true, alias = "", hidden = false },
        { id = "A6", element = "C", x = 0.7905, y = -0.9062, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = true, alias = "", hidden = false },
        { id = "A7", element = "C", x = 1.6547, y = -0.4030, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = true, alias = "", hidden = false },
        { id = "A8", element = "C", x = 1.6511, y = 0.5968, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 0, aromatic = true, alias = "", hidden = false },
        { id = "A9", element = "O", x = 2.5153, y = 1.1000, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = false, alias = "", hidden = false },
        { id = "A10", element = "C", x = 0.7833, y = 1.0938, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = true, alias = "", hidden = false },
        { id = "A11", element = "C", x = -0.0809, y = 0.5906, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = true, alias = "", hidden = false },
    },
    bonds = {
        { id = "B1", a = "A1", b = "A2", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B2", a = "A2", b = "A3", order = 2, aromatic = false, stereo = "none", visible = true },
        { id = "B3", a = "A2", b = "A4", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B4", a = "A4", b = "A5", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B5", a = "A5", b = "A6", order = 1, aromatic = true, stereo = "none", visible = true },
        { id = "B6", a = "A6", b = "A7", order = 2, aromatic = true, stereo = "none", visible = true },
        { id = "B7", a = "A7", b = "A8", order = 1, aromatic = true, stereo = "none", visible = true },
        { id = "B8", a = "A8", b = "A9", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B9", a = "A8", b = "A10", order = 2, aromatic = true, stereo = "none", visible = true },
        { id = "B10", a = "A10", b = "A11", order = 1, aromatic = true, stereo = "none", visible = true },
        { id = "B11", a = "A11", b = "A5", order = 2, aromatic = true, stereo = "none", visible = true },
    }
}
molecule1.SetPos(0, 0)
molecule1.SetScale(2.2)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)
