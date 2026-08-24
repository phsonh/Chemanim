from __future__ import annotations

from pathlib import Path
from .model import Project
from .depiction import render_acs1996


def _s(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def generate_lua(project: Project) -> str:
    s = project.scene
    lines = ['local chem = require("chem")', "", "chem.scene {", f"    width = {s.width},",
             f"    height = {s.height},", f"    logic_width = {s.logic_width},",
             f"    logic_height = {s.logic_height},", f"    fps = {s.fps},",
             f"    view_zoom = {s.view_zoom:g},",
             f"    background = {_s(s.background)},", f"    title = {_s(s.title)}", "}", ""]
    for m in project.molecules:
        svg = render_acs1996(m).svg
        lines += [f"local {m.id} = chem.NewMol {{", f"    source_smiles = {_s(m.source_smiles)},",
                  f"    reference_bond_length = {m.reference_bond_length:.8g},", "    acs_svg = [==[" + svg + "]==],", "    atoms = {"]
        for a in m.atoms:
            fields = [f"id = {_s(a.id)}", f"element = {_s(a.element)}", f"x = {a.x:.4f}", f"y = {a.y:.4f}",
                      f"isotope = {a.isotope}", f"formal_charge = {a.formal_charge}",
                      f"radical_electrons = {a.radical_electrons}", f"implicit_hydrogens = {a.implicit_hydrogens}",
                      f"aromatic = {str(a.aromatic).lower()}", f"alias = {_s(a.alias)}", f"hidden = {str(a.hidden).lower()}"]
            lines.append("        { " + ", ".join(fields) + " },")
        lines += ["    },", "    bonds = {"]
        for b in m.bonds:
            fields = [f"id = {_s(b.id)}", f"a = {_s(b.a)}", f"b = {_s(b.b)}", f"order = {b.order:g}",
                      f"aromatic = {str(b.aromatic).lower()}", f"stereo = {_s(b.stereo)}", f"visible = {str(b.visible).lower()}"]
            lines.append("        { " + ", ".join(fields) + " },")
        lines += ["    }", "}", f"{m.id}.SetPos({m.x:g}, {m.y:g})", f"{m.id}.SetScale({m.scale:g})",
                  f"{m.id}.SetRotation({m.rotation:g})", f"{m.id}.SetAlpha({m.alpha})",
                  f"{m.id}.SetLayer({m.layer})", ""]
    return "\n".join(lines).rstrip() + "\n"


def write_mod(project: Project, root: Path) -> Path:
    destination = root / "mod" / project.mod / "main.lua"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(generate_lua(project), encoding="utf-8", newline="\n")
    return destination
