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
std::optional<Molecule> decodedSnapshot(const json& snapshot){if(!snapshot.is_object()||!snapshot.contains("atoms"))return std::nullopt;try{json wrapper={{"format","chemanim-native-2d"},{"version",8},{"molecules",json::array({snapshot})},{"nodes",json::array()}};Project loaded=fromJson(wrapper.dump());if(!loaded.molecules.empty())return loaded.molecules.front();}catch(...){}return std::nullopt;}
std::string moleculeTable(const Molecule& molecule,Point anchor){
    std::ostringstream out;out<<std::setprecision(12)<<"{\n    source_smiles = "<<quote(molecule.sourceSmiles)<<",\n    reference_bond_length = "<<molecule.referenceBondLength<<",\n    atoms = {\n";
    for(const Atom& atom:molecule.atoms)out<<"        { id="<<quote(atom.id)<<", creation_serial="<<atom.creationSerial<<", element="<<quote(atom.element)<<", label="<<quote(atom.alias)<<", label_side="<<quote(toString(atom.labelSide))<<", number_style="<<quote(toString(atom.numberStyle))<<", isotope="<<atom.isotope<<", radical_electrons="<<atom.radicalElectrons<<", implicit_hydrogens="<<atom.implicitHydrogens<<", hidden="<<(atom.hidden?"true":"false")<<", alive="<<(atom.alive?"true":"false")<<", alpha="<<atom.alpha<<", color_r="<<atom.color.red<<", color_g="<<atom.color.green<<", color_b="<<atom.color.blue<<", x="<<(atom.position.x-anchor.x)<<", y="<<(atom.position.y-anchor.y)<<" },\n";
    out<<"    },\n    bonds = {\n";for(const Bond& bond:molecule.bonds)out<<"        { id="<<quote(bond.id)<<", a="<<quote(bond.atomA)<<", b="<<quote(bond.atomB)<<", order="<<orderValue(bond.type)<<", secondary_line_side="<<quote(toString(bond.secondaryLineSide))<<", stereo="<<quote(toString(bond.stereo))<<", visible="<<(bond.visible?"true":"false")<<", alive="<<(bond.alive?"true":"false")<<", alpha="<<bond.alpha<<", color_r="<<bond.color.red<<", color_g="<<bond.color.green<<", color_b="<<bond.color.blue<<" },\n";
    out<<"    },\n    adornments = {\n";for(const AtomAdornment& value:molecule.adornments)out<<"        { id="<<quote(value.id)<<", creation_serial="<<value.creationSerial<<", atom="<<quote(value.atomId)<<", text="<<quote(value.text)<<", x="<<value.offset.x<<", y="<<value.offset.y<<", alpha="<<value.alpha<<", color_r="<<value.color.red<<", color_g="<<value.color.green<<", color_b="<<value.color.blue<<", alive="<<(value.alive?"true":"false")<<" },\n";out<<"    }\n}";return out.str();
}
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
       <<molecule.id<<".SetScaleX("<<molecule.scaleX<<")\n"<<molecule.id<<".SetScaleY("<<molecule.scaleY<<")\n"<<molecule.id<<".SetRotation("<<molecule.rotation<<")\n"
       <<molecule.id<<".SetAlpha("<<molecule.alpha<<")\n"<<molecule.id<<".SetLayer("<<molecule.layer<<")\n"
       <<molecule.id<<".SetColor("<<molecule.color.red<<", "<<molecule.color.green<<", "<<molecule.color.blue<<")\n"
       <<molecule.id<<".SetVisible("<<(molecule.visible?"true":"false")<<")";
    std::string result=out.str();
    while(result.size()>1&&result.back()=='\n'&&result[result.size()-2]=='\n')result.pop_back();
    return result;
}
std::string capturedObjectCommands(const json& params) {
    const std::string output=params.value("output","");if(output.empty())return{};
    json snapshot=params.value("snapshot",json::object());if(snapshot.is_string())snapshot=json::parse(snapshot.get<std::string>());
    const auto molecule=decodedSnapshot(snapshot);if(!molecule)return{};
    std::ostringstream out;out<<output<<":SetStructure("<<moleculeTable(*molecule,{})<<")\n"
       <<output<<".SetPos("<<number(params.value("origin_x",0.0))<<", "<<number(params.value("origin_y",0.0))<<")\n"
       <<output<<".SetScaleX("<<number(params.value("scale_x",1.0))<<")\n"
       <<output<<".SetScaleY("<<number(params.value("scale_y",1.0))<<")\n"
       <<output<<".SetRotation("<<number(params.value("rotation",0.0))<<")\n"
       <<output<<".SetAlpha("<<params.value("alpha",255)<<")\n"
       <<output<<".SetLayer("<<params.value("layer",0)<<")\n"
       <<output<<".SetColor("<<params.value("r",255)<<", "<<params.value("g",255)<<", "<<params.value("b",255)<<")\n"
       <<output<<".SetVisible("<<(params.value("visible",true)?"true":"false")<<")";
    return out.str();
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
        else if(node.type=="molecule_set_x")line=target+".SetPosX("+number(p.value("value",0.0))+")";
        else if(node.type=="molecule_set_y")line=target+".SetPosY("+number(p.value("value",0.0))+")";
        else if(node.type=="molecule_lerp_x")line=target+".LerpPosX("+number(p.value("value",0.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_lerp_y")line=target+".LerpPosY("+number(p.value("value",0.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_scale")line=target+".SetScale("+number(p.value("value",1.0))+")";
        else if(node.type=="molecule_lerp_scale")line=target+".LerpScale("+number(p.value("value",1.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_scale_x")line=target+".SetScaleX("+number(p.value("value",1.0))+")";
        else if(node.type=="molecule_set_scale_y")line=target+".SetScaleY("+number(p.value("value",1.0))+")";
        else if(node.type=="molecule_lerp_scale_x")line=target+".LerpScaleX("+number(p.value("value",1.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_lerp_scale_y")line=target+".LerpScaleY("+number(p.value("value",1.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type.rfind("molecule_global_set_",0)==0){const std::string property=node.type.substr(std::string("molecule_global_set_").size());if(property=="scale"){line="chem.SetGlobal(\"molecule\", \"scale_x\", "+number(p.value("value",1.0))+")\nchem.SetGlobal(\"molecule\", \"scale_y\", "+number(p.value("value",1.0))+")";}else if(property=="color")line="chem.SetGlobal(\"molecule\", \"r\", "+number(p.value("r",255.0))+")\nchem.SetGlobal(\"molecule\", \"g\", "+number(p.value("g",255.0))+")\nchem.SetGlobal(\"molecule\", \"b\", "+number(p.value("b",255.0))+")";else line="chem.SetGlobal(\"molecule\", "+quote(property)+", "+number(p.value("value",property=="alpha"?255.0:1.0))+")";}
        else if(node.type=="molecule_set_rotation")line=target+".SetRotation("+number(p.value("value",0.0))+")";
        else if(node.type=="molecule_lerp_rotation")line=target+".LerpRotation("+number(p.value("value",0.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_alpha")line=target+".SetAlpha("+std::to_string(p.value("value",255))+")";
        else if(node.type=="molecule_lerp_alpha")line=target+".LerpAlpha("+std::to_string(p.value("value",255))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_color")line=target+".SetColor("+std::to_string(p.value("r",255))+", "+std::to_string(p.value("g",255))+", "+std::to_string(p.value("b",255))+")";
        else if(node.type=="molecule_lerp_color")line=target+".LerpColor("+std::to_string(p.value("r",255))+", "+std::to_string(p.value("g",255))+", "+std::to_string(p.value("b",255))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="molecule_set_layer")line=target+".SetLayer("+std::to_string(p.value("value",0))+")";
        else if(node.type=="molecule_set_visible")line=target+".SetVisible("+std::string(p.value("value",true)?"true":"false")+")";
        else if(node.type=="molecule_delete")line=target+".Delete()";
        else if(node.type=="split_molecule"||(node.type=="merge_molecules"&&p.value("operation_version","")=="object_v1")){
            line=capturedObjectCommands(p);if(node.type=="merge_molecules")line+="\n"+target+".Delete()\n"+p.value("source","")+".Delete()";
        }
        else if(node.type=="molecule_set_structure"){try{json snapshot=p.value("snapshot",json::object());if(snapshot.is_string())snapshot=json::parse(snapshot.get<std::string>());if(const auto value=decodedSnapshot(snapshot))line=target+":SetStructure("+moleculeTable(*value,{})+")";}catch(...){} }
        else if(node.type=="molecule_gradient_structure"){try{json start=p.value("start_snapshot",json::object()),end=p.value("end_snapshot",json::object());if(start.is_string())start=json::parse(start.get<std::string>());if(end.is_string())end=json::parse(end.get<std::string>());const auto startMolecule=decodedSnapshot(start),endMolecule=decodedSnapshot(end);if(startMolecule&&endMolecule)line=target+":LerpStructure("+moleculeTable(*startMolecule,{})+", "+moleculeTable(*endMolecule,{})+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";}catch(...){} }
        else if(node.type=="molecule_merge_gradient_structure"||node.type=="molecule_split_gradient_structure"){try{const bool merging=node.type=="molecule_merge_gradient_structure";const std::string secondary=p.value(merging?"source":"destination","");const char* firstStartKey=merging?"target_start_snapshot":"source_start_snapshot";const char* firstEndKey=merging?"target_end_snapshot":"source_end_snapshot";const char* secondStartKey=merging?"source_start_snapshot":"destination_start_snapshot";const char* secondEndKey=merging?"source_end_snapshot":"destination_end_snapshot";json a=p.value(firstStartKey,json::object()),b=p.value(firstEndKey,json::object()),c=p.value(secondStartKey,json::object()),d=p.value(secondEndKey,json::object());const auto firstStart=decodedSnapshot(a),firstEnd=decodedSnapshot(b),secondStart=decodedSnapshot(c),secondEnd=decodedSnapshot(d);if(firstStart&&firstEnd&&secondStart&&secondEnd){const std::string frames=std::to_string(p.value("frames",30)),ease=quote(p.value("easing","linear"));line=target+":LerpStructure("+moleculeTable(*firstStart,{})+", "+moleculeTable(*firstEnd,{})+", "+frames+", "+ease+")\n"+secondary+":LerpStructure("+moleculeTable(*secondStart,{})+", "+moleculeTable(*secondEnd,{})+", "+frames+", "+ease+")";if(merging)line+="\nlocal __merge_frame = chem.GetFrame()\nchem.SetFrame(__merge_frame + "+frames+")\n"+secondary+":Delete()\nchem.SetFrame(__merge_frame)";}}catch(...){} }
        else if(node.type=="molecule_lerp_structure"){try{json atoms=p.value("atoms",std::string("{}"));if(atoms.is_string())atoms=json::parse(atoms.get<std::string>());std::ostringstream value;value<<target<<".LerpAtomsXY({";for(const auto& [id,atom]:atoms.items())value<<" ["<<quote(id)<<"]={"<<number(atom.value("x",0.0))<<","<<number(atom.value("y",0.0))<<"},";value<<" }, "<<p.value("frames",30)<<", "<<quote(p.value("easing","linear"))<<")";line=value.str();}catch(...){} }
        else if(node.type=="atom_set_xy")line=target+".SetAtomXY("+quote(p.value("atom",""))+", "+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+")";
        else if(node.type=="atom_lerp_xy")line=target+".LerpAtomXY("+quote(p.value("atom",""))+", "+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
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
        else if(node.type=="selection_fade"||node.type=="selection_show"||node.type=="selection_hide"){const int alpha=node.type=="selection_show"?255:node.type=="selection_hide"?0:p.value("value",0);std::ostringstream value;for(const std::string& id:idValues(p,"atoms"))value<<target<<".LerpAtomAlpha("<<quote(id)<<", "<<alpha<<", "<<p.value("frames",30)<<", "<<quote(p.value("easing","linear"))<<")\n";for(const std::string& id:idValues(p,"bonds"))value<<target<<".LerpBondAlpha("<<quote(id)<<", "<<alpha<<", "<<p.value("frames",30)<<", "<<quote(p.value("easing","linear"))<<")\n";for(const std::string& id:idValues(p,"adornments"))value<<target<<".LerpAdornmentAlpha("<<quote(id)<<", "<<alpha<<", "<<p.value("frames",30)<<", "<<quote(p.value("easing","linear"))<<")\n";line=value.str();}
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
        else if(node.type=="arrow_set_curve"&&p.value("initialized",true))line=target+".SetCurve("+number(p.value("x1",0.0))+", "+number(p.value("y1",0.0))+", "+number(p.value("cx1",80.0))+", "+number(p.value("cy1",80.0))+", "+number(p.value("cx2",-80.0))+", "+number(p.value("cy2",80.0))+", "+number(p.value("x2",160.0))+", "+number(p.value("y2",0.0))+")";
        else if(node.type=="arrow_set_position")line=target+".SetPos("+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+")";
        else if(node.type=="arrow_lerp_position")line=target+".LerpPos("+number(p.value("x",0.0))+", "+number(p.value("y",0.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_set_progress")line=target+".SetProgress("+number(p.value("value",0.0))+")";
        else if(node.type=="arrow_lerp_progress")line=target+".LerpProgress("+number(p.value("value",1.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_set_alpha")line=target+".SetAlpha("+std::to_string(p.value("value",255))+")";
        else if(node.type=="arrow_lerp_alpha")line=target+".LerpAlpha("+std::to_string(p.value("value",0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_set_color")line=target+".SetColor("+std::to_string(p.value("r",25))+", "+std::to_string(p.value("g",25))+", "+std::to_string(p.value("b",25))+")";
        else if(node.type=="arrow_lerp_color")line=target+".LerpColor("+std::to_string(p.value("r",25))+", "+std::to_string(p.value("g",25))+", "+std::to_string(p.value("b",25))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_set_width")line=target+".SetWidth("+number(p.value("value",3.0))+")";
        else if(node.type=="arrow_lerp_width")line=target+".LerpWidth("+number(p.value("value",3.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_set_scale")line=target+".SetScale("+number(p.value("value",1.0))+")";
        else if(node.type=="arrow_set_scale_x")line=target+".SetScaleX("+number(p.value("value",1.0))+")";
        else if(node.type=="arrow_set_scale_y")line=target+".SetScaleY("+number(p.value("value",1.0))+")";
        else if(node.type=="arrow_lerp_scale")line=target+".LerpScale("+number(p.value("value",1.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_lerp_scale_x")line=target+".LerpScaleX("+number(p.value("value",1.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type=="arrow_lerp_scale_y")line=target+".LerpScaleY("+number(p.value("value",1.0))+", "+std::to_string(p.value("frames",30))+", "+quote(p.value("easing","linear"))+")";
        else if(node.type.rfind("arrow_global_set_",0)==0){const std::string property=node.type.substr(std::string("arrow_global_set_").size());if(property=="scale"){line="chem.SetGlobal(\"arrow\", \"scale_x\", "+number(p.value("value",1.0))+")\nchem.SetGlobal(\"arrow\", \"scale_y\", "+number(p.value("value",1.0))+")";}else if(property=="color")line="chem.SetGlobal(\"arrow\", \"r\", "+number(p.value("r",255.0))+")\nchem.SetGlobal(\"arrow\", \"g\", "+number(p.value("g",255.0))+")\nchem.SetGlobal(\"arrow\", \"b\", "+number(p.value("b",255.0))+")";else if(property=="width")line="chem.SetGlobal(\"arrow\", \"width_override\", "+number(p.value("value",3.0))+")";else line="chem.SetGlobal(\"arrow\", "+quote(property)+", "+number(p.value("value",property=="alpha"?255.0:1.0))+")";}
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
