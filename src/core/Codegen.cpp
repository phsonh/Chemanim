#include "Codegen.hpp"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <fstream>
#include <iomanip>
#include <sstream>
#include <stdexcept>

namespace chem::core {
namespace {
using json=nlohmann::json;
std::string quote(const std::string& value) {
    std::string result = "\"";
    for (char c : value) { if (c == '\\' || c == '"') result.push_back('\\'); if (c == '\n') result += "\\n"; else result.push_back(c); }
    return result + "\"";
}
double orderValue(BondType type) { return type == BondType::Double ? 2.0 : type == BondType::Triple ? 3.0 : 1.0; }
std::string number(double value) { std::ostringstream out; out << std::setprecision(12) << value; return out.str(); }
std::vector<std::string> idValues(const json& params,const char* key){std::vector<std::string> result;const auto found=params.find(key);if(found==params.end())return result;if(found->is_array()){for(const json& value:*found)if(value.is_string())result.push_back(value.get<std::string>());return result;}if(found->is_string()){const std::string raw=found->get<std::string>();std::size_t start=0;while(start<raw.size()){const std::size_t end=raw.find_first_of(", ;",start);const std::string value=raw.substr(start,end==std::string::npos?raw.size()-start:end-start);if(!value.empty())result.push_back(value);if(end==std::string::npos)break;start=end+1;}}return result;}
std::string moleculeDeclaration(const Molecule& molecule) {
    std::ostringstream out;out<<std::setprecision(12);
    const Point anchor=molecule.coordinate().value_or(Point{});
    out<<"local "<<molecule.id<<" = chem.NewMol {\n"
       <<"    source_smiles = "<<quote(molecule.sourceSmiles)<<",\n"
       <<"    reference_bond_length = "<<molecule.referenceBondLength<<",\n    atoms = {\n";
    for(const Atom& atom:molecule.atoms)out<<"        { id="<<quote(atom.id)<<", creation_serial="<<atom.creationSerial<<", element="<<quote(atom.element)
       <<", label="<<quote(atom.alias)<<", label_side="<<quote(toString(atom.labelSide))
       <<", number_style="<<quote(toString(atom.numberStyle))<<", isotope="<<atom.isotope
       <<", radical_electrons="<<atom.radicalElectrons<<", implicit_hydrogens="<<atom.implicitHydrogens
       <<", hidden="<<(atom.hidden?"true":"false")<<", alive="<<(atom.alive?"true":"false")
       <<", alpha="<<atom.alpha<<", color_r="<<atom.color.red<<", color_g="<<atom.color.green<<", color_b="<<atom.color.blue<<", x="<<(atom.position.x-anchor.x)<<", y="<<(atom.position.y-anchor.y)<<" },\n";
    out<<"    },\n    bonds = {\n";
    for(const Bond& bond:molecule.bonds)out<<"        { id="<<quote(bond.id)<<", a="<<quote(bond.atomA)<<", b="<<quote(bond.atomB)
       <<", order="<<orderValue(bond.type)<<", secondary_line_side="<<quote(toString(bond.secondaryLineSide))
       <<", stereo="<<quote(toString(bond.stereo))<<", visible="<<(bond.visible?"true":"false")
       <<", alive="<<(bond.alive?"true":"false")<<", alpha="<<bond.alpha<<", color_r="<<bond.color.red<<", color_g="<<bond.color.green<<", color_b="<<bond.color.blue<<" },\n";
    out<<"    },\n    adornments = {\n";
    for(const AtomAdornment& adornment:molecule.adornments)out<<"        { id="<<quote(adornment.id)<<", creation_serial="<<adornment.creationSerial<<", atom="<<quote(adornment.atomId)<<", text="<<quote(adornment.text)<<", x="<<adornment.offset.x<<", y="<<adornment.offset.y<<", alpha="<<adornment.alpha<<", color_r="<<adornment.color.red<<", color_g="<<adornment.color.green<<", color_b="<<adornment.color.blue<<", alive="<<(adornment.alive?"true":"false")<<" },\n";
    out<<"    }\n}\n"<<molecule.id<<".SetPos("<<anchor.x<<", "<<anchor.y<<")\n"
       <<molecule.id<<".SetScale("<<molecule.scale<<")\n"<<molecule.id<<".SetRotation("<<molecule.rotation<<")\n"
       <<molecule.id<<".SetAlpha("<<molecule.alpha<<")\n"<<molecule.id<<".SetLayer("<<molecule.layer<<")\n"
       <<molecule.id<<".SetColor("<<molecule.color.red<<", "<<molecule.color.green<<", "<<molecule.color.blue<<")\n"
       <<molecule.id<<".SetVisible("<<(molecule.visible?"true":"false")<<")";
    std::string result=out.str();
    while(result.size()>1&&result.back()=='\n'&&result[result.size()-2]=='\n')result.pop_back();
    return result;
}
}  // namespace

std::string compileLua(const Project& project) {
    std::ostringstream out;out<<std::setprecision(12)<<"local chem = require(\"chem\")\n\n";std::set<std::string> declaredMolecules,declaredArrows;
    for(const ScriptNode& node:project.nodes){if(!node.enabled)continue;const json p=json::parse(node.paramsJson);const std::string target=p.value("target","");std::string line;
        if(node.type=="scene"){const Scene& s=project.scene;std::ostringstream value;value<<"chem.scene {\n    width = "<<s.width<<", height = "<<s.height<<",\n    logic_width = "<<s.logicWidth<<", logic_height = "<<s.logicHeight<<",\n    fps = "<<s.fps<<", view_zoom = "<<s.viewZoom<<",\n    background = "<<quote(s.background)<<", title = "<<quote(s.title)<<"\n}";line=value.str();}
        else if(node.type=="wait")line="chem.Wait("+std::to_string(std::max(0,p.value("frames",30)))+")";
        else if(node.type=="raw_lua")line=p.value("code","");
        else if(node.type=="molecule_create"){if(const Molecule* molecule=project.molecule(target);molecule&&!declaredMolecules.contains(target)){line=moleculeDeclaration(*molecule);declaredMolecules.insert(target);}}
        else if(node.type=="molecule_set_position")line=target+".SetPos("+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+")";
        else if(node.type=="molecule_lerp_position")line=target+".LerpPos("+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_scale")line=target+".SetScale("+number(p.value("value",1.0))+")";
        else if(node.type=="molecule_lerp_scale")line=target+".LerpScale("+number(p.value("value",1.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_rotation")line=target+".SetRotation("+number(p.value("value",0.0))+")";
        else if(node.type=="molecule_lerp_rotation")line=target+".LerpRotation("+number(p.value("value",0.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_alpha")line=target+".SetAlpha("+std::to_string(p.value("value",255))+")";
        else if(node.type=="molecule_lerp_alpha")line=target+".LerpAlpha("+std::to_string(p.value("value",255))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_color")line=target+".SetColor("+std::to_string(p.value("r",255))+", "+std::to_string(p.value("g",255))+", "+std::to_string(p.value("b",255))+")";
        else if(node.type=="molecule_lerp_color")line=target+".LerpColor("+std::to_string(p.value("r",255))+", "+std::to_string(p.value("g",255))+", "+std::to_string(p.value("b",255))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_layer")line=target+".SetLayer("+std::to_string(p.value("value",0))+")";
        else if(node.type=="molecule_set_visible")line=target+".SetVisible("+std::string(p.value("value",true)?"true":"false")+")";
        else if(node.type=="molecule_delete")line=target+".Delete()";
        else if(node.type=="atom_set_xy"){Point anchor{};if(const Molecule* molecule=project.molecule(target))anchor=molecule->coordinate().value_or(Point{});line=target+".SetAtomXY("+quote(p.value("atom",""))+", "+number(p.value("x",0.0)-anchor.x)+", "+number(p.value("y",0.0)-anchor.y)+")";}
        else if(node.type=="atom_lerp_xy"){Point anchor{};if(const Molecule* molecule=project.molecule(target))anchor=molecule->coordinate().value_or(Point{});line=target+".LerpAtomXY("+quote(p.value("atom",""))+", "+number(p.value("x",0.0)-anchor.x)+", "+number(p.value("y",0.0)-anchor.y)+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";}
        else if(node.type=="atom_lerp_pose"){if(const Molecule* molecule=project.molecule(target);molecule){if(auto pose=molecule->poses.find(p.value("pose",""));pose!=molecule->poses.end()){const Point anchor=molecule->coordinate().value_or(Point{});std::ostringstream value;value<<target<<".LerpAtomsXY({";for(const auto& [id,point]:pose->second.atomPositions)value<<" ["<<quote(id)<<"]={"<<point.x-anchor.x<<","<<point.y-anchor.y<<"},";value<<" }, "<<p.value("frames",30)<<", "<<quote(p.value("easing","linear"))<<")";line=value.str();}}}
        else if(node.type=="atom_set_element")line=target+".SetAtomElement("+quote(p.value("atom",""))+", "+quote(p.value("value","C"))+")";
        else if(node.type=="atom_set_alpha")line=target+".SetAtomAlpha("+quote(p.value("atom",""))+", "+std::to_string(p.value("value",255))+")";
        else if(node.type=="atom_lerp_alpha")line=target+".LerpAtomAlpha("+quote(p.value("atom",""))+", "+std::to_string(p.value("value",255))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="atom_set_color")line=target+".SetAtomColor("+quote(p.value("atom",""))+", "+std::to_string(p.value("r",0))+", "+std::to_string(p.value("g",0))+", "+std::to_string(p.value("b",0))+")";
        else if(node.type=="atom_lerp_color")line=target+".LerpAtomColor("+quote(p.value("atom",""))+", "+std::to_string(p.value("r",0))+", "+std::to_string(p.value("g",0))+", "+std::to_string(p.value("b",0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="atom_set_hidden")line=target+".SetAtomHidden("+quote(p.value("atom",""))+", "+std::string(p.value("value",true)?"true":"false")+")";
        else if(node.type=="bond_form")line=target+".FormBond("+quote(p.value("bond",""))+", "+quote(p.value("a",""))+", "+quote(p.value("b",""))+", "+quote(p.value("order","single"))+", "+quote(p.value("stereo","none"))+")\n"+target+".SetBondSecondarySide("+quote(p.value("bond",""))+", "+quote(p.value("secondary_line_side","center"))+")\n"+target+".SetBondAlpha("+quote(p.value("bond",""))+", 0)\n"+target+".LerpBondAlpha("+quote(p.value("bond",""))+", 255, "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="bond_break")line=target+".BreakBond("+quote(p.value("bond",""))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="bond_delete")line=target+".DeleteBond("+quote(p.value("bond",""))+")";
        else if(node.type=="bond_set_order")line=target+".SetBondOrder("+quote(p.value("bond",""))+", "+quote(p.value("value","single"))+")";
        else if(node.type=="bond_set_secondary_side")line=target+".SetBondSecondarySide("+quote(p.value("bond",""))+", "+quote(p.value("value","center"))+")";
        else if(node.type=="bond_set_stereo")line=target+".SetBondStereo("+quote(p.value("bond",""))+", "+quote(p.value("value","none"))+")";
        else if(node.type=="bond_set_visible")line=target+".SetBondVisible("+quote(p.value("bond",""))+", "+std::string(p.value("value",true)?"true":"false")+")";
        else if(node.type=="bond_set_alpha")line=target+".SetBondAlpha("+quote(p.value("bond",""))+", "+std::to_string(p.value("value",255))+")";
        else if(node.type=="bond_lerp_alpha")line=target+".LerpBondAlpha("+quote(p.value("bond",""))+", "+std::to_string(p.value("value",255))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="bond_set_color")line=target+".SetBondColor("+quote(p.value("bond",""))+", "+std::to_string(p.value("r",0))+", "+std::to_string(p.value("g",0))+", "+std::to_string(p.value("b",0))+")";
        else if(node.type=="bond_lerp_color")line=target+".LerpBondColor("+quote(p.value("bond",""))+", "+std::to_string(p.value("r",0))+", "+std::to_string(p.value("g",0))+", "+std::to_string(p.value("b",0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="selection_fade"){std::ostringstream value;for(const std::string& id:idValues(p,"atoms"))value<<target<<".LerpAtomAlpha("<<quote(id)<<", "<<p.value("value",0)<<", "<<p.value("frames",30)<<", "<<quote(p.value("easing","linear"))<<")\n";for(const std::string& id:idValues(p,"bonds"))value<<target<<".LerpBondAlpha("<<quote(id)<<", "<<p.value("value",0)<<", "<<p.value("frames",30)<<", "<<quote(p.value("easing","linear"))<<")\n";for(const std::string& id:idValues(p,"adornments"))value<<target<<".LerpAdornmentAlpha("<<quote(id)<<", "<<p.value("value",0)<<", "<<p.value("frames",30)<<", "<<quote(p.value("easing","linear"))<<")\n";line=value.str();}
        else if(node.type=="detach_subgraph"){std::ostringstream value;value<<target<<".DetachSubgraph("<<p.value("destination","")<<", {";for(const std::string& id:idValues(p,"atoms"))value<<quote(id)<<',';value<<"}, {";for(const std::string& id:idValues(p,"bonds"))value<<quote(id)<<',';value<<"})";line=value.str();}
        else if(node.type=="merge_molecules")line=target+".MergeFrom("+p.value("source","")+", "+quote(p.value("bond",""))+", "+quote(p.value("a",""))+", "+quote(p.value("b",""))+", "+quote(p.value("order","single"))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="adornment_set_offset")line=target+".SetAdornmentOffset("+quote(p.value("adornment",""))+", "+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+")";
        else if(node.type=="adornment_lerp_offset")line=target+".LerpAdornmentOffset("+quote(p.value("adornment",""))+", "+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="adornment_set_alpha")line=target+".SetAdornmentAlpha("+quote(p.value("adornment",""))+", "+std::to_string(p.value("value",255))+")";
        else if(node.type=="adornment_lerp_alpha")line=target+".LerpAdornmentAlpha("+quote(p.value("adornment",""))+", "+std::to_string(p.value("value",255))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="adornment_set_color")line=target+".SetAdornmentColor("+quote(p.value("adornment",""))+", "+std::to_string(p.value("r",0))+", "+std::to_string(p.value("g",0))+", "+std::to_string(p.value("b",0))+")";
        else if(node.type=="adornment_lerp_color")line=target+".LerpAdornmentColor("+quote(p.value("adornment",""))+", "+std::to_string(p.value("r",0))+", "+std::to_string(p.value("g",0))+", "+std::to_string(p.value("b",0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="adornment_set_text")line=target+".SetAdornmentText("+quote(p.value("adornment",""))+", "+quote(p.value("value","⊕"))+")";
        else if(node.type=="arrow_new"){if(!declaredArrows.contains(target)){line="local "+target+" = chem.NewArrow()";declaredArrows.insert(target);}}
        else if(node.type=="arrow_delete")line=target+".Delete()";
        else if(node.type=="arrow_set_curve")line=target+".SetCurve("+number(p.value("x1",0.0))+", "+number(p.value("y1",0.0))+", "+number(p.value("cx1",80.0))+", "+number(p.value("cy1",80.0))+", "+number(p.value("cx2",-80.0))+", "+number(p.value("cy2",80.0))+", "+number(p.value("x2",160.0))+", "+number(p.value("y2",0.0))+")";
        else if(node.type=="arrow_set_position")line=target+".SetPos("+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+")";
        else if(node.type=="arrow_lerp_position")line=target+".LerpPos("+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_set_progress")line=target+".SetProgress("+number(p.value("value",0.0))+")";
        else if(node.type=="arrow_lerp_progress")line=target+".LerpProgress("+number(p.value("value",1.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_set_alpha")line=target+".SetAlpha("+std::to_string(p.value("value",255))+")";
        else if(node.type=="arrow_lerp_alpha")line=target+".LerpAlpha("+std::to_string(p.value("value",0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_set_color")line=target+".SetColor("+std::to_string(p.value("r",25))+", "+std::to_string(p.value("g",25))+", "+std::to_string(p.value("b",25))+")";
        else if(node.type=="arrow_lerp_color")line=target+".LerpColor("+std::to_string(p.value("r",25))+", "+std::to_string(p.value("g",25))+", "+std::to_string(p.value("b",25))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_set_width")line=target+".SetWidth("+number(p.value("value",3.0))+")";
        if(!line.empty())out<<line<<"\n\n";
    }
    std::string result=out.str();
    while(result.size()>1&&result.back()=='\n'&&result[result.size()-2]=='\n')result.pop_back();
    return result;
}

std::filesystem::path writeMod(const Project& project, const std::filesystem::path& repositoryRoot) {
    const auto destination = repositoryRoot / "mod" / project.mod / "main.lua";
    std::filesystem::create_directories(destination.parent_path());
    std::ofstream stream(destination, std::ios::binary | std::ios::trunc); if (!stream) throw std::runtime_error("Unable to write main.lua");
    stream << compileLua(project); return destination;
}

}  // namespace chem::core
