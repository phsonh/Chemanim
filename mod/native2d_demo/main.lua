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
    source_smiles = "CC(C)C1=CC=C(C=C1)[C@@H](C)C(=O)O",
    reference_bond_length = 0.99997747,
    acs_svg = [==[<?xml version='1.0' encoding='iso-8859-1'?>
<svg version='1.1' baseProfile='full'
              xmlns='http://www.w3.org/2000/svg'
                      xmlns:rdkit='http://www.rdkit.org/xml'
                      xmlns:xlink='http://www.w3.org/1999/xlink'
                  xml:space='preserve'
width='93px' height='75px' viewBox='0 0 93 75'>
<!-- END OF HEADER -->
<path class='bond-0 atom-0 atom-1' d='M 16.8,70.6 L 16.8,56.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-1 atom-1 atom-2' d='M 16.8,56.6 L 4.7,49.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-2 atom-1 atom-3' d='M 16.8,56.6 L 28.9,49.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-3 atom-3 atom-4' d='M 28.9,49.6 L 41.1,56.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-4 atom-4 atom-5' d='M 41.1,56.6 L 53.2,49.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-4 atom-4 atom-5' d='M 41.1,53.7 L 50.7,48.1' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-5 atom-5 atom-6' d='M 53.2,49.6 L 53.2,35.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-6 atom-6 atom-7' d='M 53.2,35.6 L 41.1,28.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-6 atom-6 atom-7' d='M 50.7,37.0 L 41.1,31.5' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-7 atom-7 atom-8' d='M 41.1,28.6 L 29.0,35.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-8 atom-6 atom-9' d='M 53.2,35.6 L 65.4,28.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-9 atom-9 atom-10' d='M 67.9,29.8 L 67.7,30.2' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-9 atom-9 atom-10' d='M 70.5,31.0 L 70.0,31.8' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-9 atom-9 atom-10' d='M 73.0,32.1 L 72.3,33.5' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-9 atom-9 atom-10' d='M 75.6,33.3 L 74.6,35.1' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-9 atom-9 atom-10' d='M 78.1,34.5 L 76.9,36.7' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-10 atom-9 atom-11' d='M 65.4,28.6 L 65.4,14.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-11 atom-11 atom-12' d='M 66.6,13.8 L 58.7,9.2' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-11 atom-11 atom-12' d='M 65.4,16.0 L 57.4,11.4' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-12 atom-11 atom-13' d='M 65.4,14.6 L 72.7,10.3' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-13 atom-8 atom-3' d='M 29.0,35.6 L 28.9,49.6' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path class='bond-13 atom-8 atom-3' d='M 31.5,37.0 L 31.5,48.1' style='fill:none;fill-rule:evenodd;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-opacity:1' />
<path d='M 40.5,56.2 L 41.1,56.6 L 41.7,56.2' style='fill:none;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:10;stroke-opacity:1;' />
<path d='M 52.6,49.9 L 53.2,49.6 L 53.2,48.9' style='fill:none;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:10;stroke-opacity:1;' />
<path d='M 41.7,28.9 L 41.1,28.6 L 40.5,28.9' style='fill:none;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:10;stroke-opacity:1;' />
<path d='M 29.6,35.2 L 29.0,35.6 L 29.0,36.3' style='fill:none;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:10;stroke-opacity:1;' />
<path d='M 64.8,28.9 L 65.4,28.6 L 65.4,27.9' style='fill:none;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:10;stroke-opacity:1;' />
<path d='M 65.4,15.3 L 65.4,14.6 L 65.7,14.4' style='fill:none;stroke:#000000;stroke-width:0.6px;stroke-linecap:butt;stroke-linejoin:miter;stroke-miterlimit:10;stroke-opacity:1;' />
<path class='atom-12' d='M 49.8 7.7
Q 49.8 5.9, 50.8 4.9
Q 51.7 3.9, 53.3 3.9
Q 54.2 3.9, 55.0 4.4
Q 55.8 4.9, 56.3 5.7
Q 56.7 6.6, 56.7 7.6
Q 56.7 8.7, 56.2 9.6
Q 55.8 10.4, 55.0 10.9
Q 54.2 11.3, 53.2 11.3
Q 52.2 11.3, 51.4 10.8
Q 50.6 10.3, 50.2 9.5
Q 49.8 8.7, 49.8 7.7
M 50.8 7.7
Q 50.8 9.0, 51.5 9.8
Q 52.2 10.5, 53.2 10.5
Q 54.3 10.5, 55.0 9.8
Q 55.7 9.0, 55.7 7.6
Q 55.7 6.7, 55.4 6.1
Q 55.1 5.4, 54.5 5.1
Q 54.0 4.7, 53.3 4.7
Q 52.3 4.7, 51.5 5.4
Q 50.8 6.1, 50.8 7.7
' fill='#000000'/>
<path class='atom-13' d='M 74.1 7.7
Q 74.1 5.9, 75.1 4.9
Q 76.0 3.9, 77.5 3.9
Q 78.5 3.9, 79.3 4.4
Q 80.1 4.9, 80.5 5.7
Q 80.9 6.6, 80.9 7.6
Q 80.9 8.7, 80.5 9.6
Q 80.1 10.5, 79.3 10.9
Q 78.5 11.3, 77.5 11.3
Q 76.5 11.3, 75.7 10.9
Q 74.9 10.4, 74.5 9.5
Q 74.1 8.7, 74.1 7.7
M 75.1 7.7
Q 75.1 9.0, 75.8 9.8
Q 76.5 10.5, 77.5 10.5
Q 78.6 10.5, 79.3 9.8
Q 80.0 9.0, 80.0 7.6
Q 80.0 6.8, 79.7 6.1
Q 79.4 5.5, 78.8 5.1
Q 78.2 4.7, 77.5 4.7
Q 76.5 4.7, 75.8 5.4
Q 75.1 6.1, 75.1 7.7
' fill='#000000'/>
<path class='atom-13' d='M 82.0 11.2
L 82.0 4.1
L 83.0 4.1
L 83.0 7.0
L 86.7 7.0
L 86.7 4.1
L 87.6 4.1
L 87.6 11.2
L 86.7 11.2
L 86.7 7.8
L 83.0 7.8
L 83.0 11.2
L 82.0 11.2
' fill='#000000'/>
</svg>
]==],
    atoms = {
        { id = "A1", element = "C", x = -1.9813, y = -2.3556, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 3, aromatic = false, alias = "", hidden = false },
        { id = "A2", element = "C", x = -1.9805, y = -1.3556, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = false, alias = "", hidden = false },
        { id = "A3", element = "C", x = -2.8461, y = -0.8550, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 3, aromatic = false, alias = "", hidden = false },
        { id = "A4", element = "C", x = -1.1141, y = -0.8564, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 0, aromatic = true, alias = "", hidden = false },
        { id = "A5", element = "C", x = -0.2485, y = -1.3568, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = true, alias = "", hidden = false },
        { id = "A6", element = "C", x = 0.6179, y = -0.8578, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = true, alias = "", hidden = false },
        { id = "A7", element = "C", x = 0.6187, y = 0.1424, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 0, aromatic = true, alias = "", hidden = false },
        { id = "A8", element = "C", x = -0.2469, y = 0.6430, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = true, alias = "", hidden = false },
        { id = "A9", element = "C", x = -1.1133, y = 0.1438, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = true, alias = "", hidden = false },
        { id = "A10", element = "C", x = 1.4851, y = 0.6416, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = false, alias = "", hidden = false },
        { id = "A11", element = "C", x = 2.3507, y = 0.1410, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 3, aromatic = false, alias = "", hidden = false },
        { id = "A12", element = "C", x = 1.4859, y = 1.6416, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 0, aromatic = false, alias = "", hidden = false },
        { id = "A13", element = "O", x = 0.6203, y = 2.1424, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 0, aromatic = false, alias = "", hidden = false },
        { id = "A14", element = "O", x = 2.3523, y = 2.1410, isotope = 0, formal_charge = 0, radical_electrons = 0, implicit_hydrogens = 1, aromatic = false, alias = "", hidden = false },
    },
    bonds = {
        { id = "B1", a = "A1", b = "A2", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B2", a = "A2", b = "A3", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B3", a = "A2", b = "A4", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B4", a = "A4", b = "A5", order = 1, aromatic = true, stereo = "none", visible = true },
        { id = "B5", a = "A5", b = "A6", order = 2, aromatic = true, stereo = "none", visible = true },
        { id = "B6", a = "A6", b = "A7", order = 1, aromatic = true, stereo = "none", visible = true },
        { id = "B7", a = "A7", b = "A8", order = 2, aromatic = true, stereo = "none", visible = true },
        { id = "B8", a = "A8", b = "A9", order = 1, aromatic = true, stereo = "none", visible = true },
        { id = "B9", a = "A7", b = "A10", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B10", a = "A10", b = "A11", order = 1, aromatic = false, stereo = "dash", visible = true },
        { id = "B11", a = "A10", b = "A12", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B12", a = "A12", b = "A13", order = 2, aromatic = false, stereo = "none", visible = true },
        { id = "B13", a = "A12", b = "A14", order = 1, aromatic = false, stereo = "none", visible = true },
        { id = "B14", a = "A9", b = "A4", order = 2, aromatic = true, stereo = "none", visible = true },
    }
}
molecule1.SetPos(0, 0)
molecule1.SetScale(2.2)
molecule1.SetRotation(0)
molecule1.SetAlpha(255)
molecule1.SetLayer(0)
