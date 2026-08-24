#include "Codegen.hpp"

#include <algorithm>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace chem::core {
namespace {
std::string quote(const std::string& value) {
    std::string result = "\"";
    for (char c : value) { if (c == '\\' || c == '"') result.push_back('\\'); if (c == '\n') result += "\\n"; else result.push_back(c); }
    return result + "\"";
}
const char* easeName(Easing value) {
    switch (value) { case Easing::InQuad:return "inquad"; case Easing::OutQuad:return "outquad"; case Easing::InOutQuad:return "inoutquad"; case Easing::SmoothStep:return "smoothstep"; case Easing::Step:return "step"; default:return "linear"; }
}
double orderValue(BondType type) { return type == BondType::Double ? 2.0 : type == BondType::Triple ? 3.0 : type == BondType::Aromatic ? 1.5 : 1.0; }
std::string number(double value) { std::ostringstream out; out << std::setprecision(12) << value; return out.str(); }
}  // namespace

std::string compileLua(const Project& project) {
    std::ostringstream out; out << std::setprecision(12);
    const Scene& s = project.scene;
    out << "local chem = require(\"chem\")\n\nchem.scene {\n"
        << "    width = " << s.width << ", height = " << s.height << ",\n"
        << "    logic_width = " << s.logicWidth << ", logic_height = " << s.logicHeight << ",\n"
        << "    fps = " << s.fps << ", view_zoom = " << s.viewZoom << ",\n"
        << "    background = " << quote(s.background) << ", title = " << quote(s.title) << "\n}\n\n";
    for (const Molecule& molecule : project.molecules) {
        out << "local " << molecule.id << " = chem.NewMol {\n"
            << "    source_smiles = " << quote(molecule.sourceSmiles) << ",\n"
            << "    reference_bond_length = " << molecule.referenceBondLength << ",\n    atoms = {\n";
        for (const Atom& atom : molecule.atoms) out << "        { id=" << quote(atom.id) << ", element=" << quote(atom.element)
            << ", alias=" << quote(atom.alias) << ", isotope=" << atom.isotope << ", formal_charge=" << atom.formalCharge
            << ", radical_electrons=" << atom.radicalElectrons << ", implicit_hydrogens=" << atom.implicitHydrogens
            << ", aromatic=" << (atom.aromatic?"true":"false") << ", hidden=" << (atom.hidden?"true":"false")
            << ", x=" << atom.position.x << ", y=" << atom.position.y << " },\n";
        out << "    },\n    bonds = {\n";
        for (const Bond& bond : molecule.bonds) out << "        { id=" << quote(bond.id) << ", a=" << quote(bond.atomA) << ", b=" << quote(bond.atomB)
            << ", order=" << orderValue(bond.type) << ", aromatic=" << (bond.type==BondType::Aromatic?"true":"false")
            << ", stereo=" << quote(toString(bond.stereo)) << ", visible=" << (bond.visible?"true":"false") << " },\n";
        out << "    }\n}\n" << molecule.id << ".SetPos(" << molecule.scenePosition.x << ", " << molecule.scenePosition.y << ")\n"
            << molecule.id << ".SetScale(" << molecule.scale << ")\n" << molecule.id << ".SetRotation(" << molecule.rotation << ")\n"
            << molecule.id << ".SetAlpha(" << molecule.alpha << ")\n" << molecule.id << ".SetLayer(" << molecule.layer << ")\n\n";
    }
    struct Command { int frame; std::size_t order; std::string text; };
    std::vector<Command> commands; std::size_t order = 0;
    for (const AtomTween& tween : project.atomTweens) commands.push_back({tween.startFrame,order++,tween.moleculeId+".LerpAtomXY("+quote(tween.atomId)+", "+number(tween.target.x)+", "+number(tween.target.y)+", "+std::to_string(tween.frames)+", "+quote(easeName(tween.easing))+")"});
    for (const PoseTween& tween : project.poseTweens) {
        const Molecule* molecule = project.molecule(tween.moleculeId); const auto pose = molecule ? molecule->poses.find(tween.poseId) : std::map<std::string,Pose>::const_iterator{};
        if (!molecule || pose == molecule->poses.end()) continue;
        std::ostringstream line; line << tween.moleculeId << ".LerpAtomsXY({";
        for (const auto& [atomId, target] : pose->second.atomPositions) line << " [" << quote(atomId) << "]={" << target.x << "," << target.y << "},";
        line << " }, " << tween.frames << ", " << quote(easeName(tween.easing)) << ")";
        commands.push_back({tween.startFrame,order++,line.str()});
    }
    std::stable_sort(commands.begin(),commands.end(),[](const Command& a,const Command& b){return a.frame!=b.frame?a.frame<b.frame:a.order<b.order;});
    for (const Command& command : commands) out << "chem.SetFrame(" << command.frame << ")\n" << command.text << "\n";
    return out.str();
}

std::filesystem::path writeMod(const Project& project, const std::filesystem::path& repositoryRoot) {
    const auto destination = repositoryRoot / "mod" / project.mod / "main.lua";
    std::filesystem::create_directories(destination.parent_path());
    std::ofstream stream(destination, std::ios::binary | std::ios::trunc); if (!stream) throw std::runtime_error("Unable to write main.lua");
    stream << compileLua(project); return destination;
}

}  // namespace chem::core
