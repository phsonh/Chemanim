#include "Document.hpp"
#include "Nodes.hpp"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <cmath>
#include <fstream>
#include <stdexcept>
#include <string_view>

#ifdef _WIN32
#define NOMINMAX
#include <windows.h>
#endif

namespace chem::core {
namespace {
using json = nlohmann::json;

std::uint64_t numericSuffix(const std::string& id, char prefix) {
    if (id.size() < 2 || id.front() != prefix) return 0;
    try { return std::stoull(id.substr(1)); } catch (...) { return 0; }
}

std::uint64_t numericSuffix(const std::string& id, const std::string_view prefix) {
    if (!id.starts_with(prefix) || id.size() == prefix.size()) return 0;
    try { return std::stoull(id.substr(prefix.size())); } catch (...) { return 0; }
}

void pointToJson(json& value, const Point& point) { value = json{{"x", point.x}, {"y", point.y}}; }
Point pointFromJson(const json& value) {
    return {value.value("x", 0.0), value.value("y", 0.0)};
}
}  // namespace

bool Rect::contains(Point point, double padding) const {
    return point.x >= left - padding && point.x <= right + padding &&
           point.y >= top - padding && point.y <= bottom + padding;
}

Atom* Molecule::atom(const std::string& stableId) {
    const auto found = std::find_if(atoms.begin(), atoms.end(), [&](const Atom& value) { return value.id == stableId; });
    return found == atoms.end() ? nullptr : &*found;
}
const Atom* Molecule::atom(const std::string& stableId) const {
    const auto found = std::find_if(atoms.begin(), atoms.end(), [&](const Atom& value) { return value.id == stableId; });
    return found == atoms.end() ? nullptr : &*found;
}
Bond* Molecule::bond(const std::string& stableId) {
    const auto found = std::find_if(bonds.begin(), bonds.end(), [&](const Bond& value) { return value.id == stableId; });
    return found == bonds.end() ? nullptr : &*found;
}
const Bond* Molecule::bond(const std::string& stableId) const {
    const auto found = std::find_if(bonds.begin(), bonds.end(), [&](const Bond& value) { return value.id == stableId; });
    return found == bonds.end() ? nullptr : &*found;
}
Bond* Molecule::bondBetween(const std::string& first, const std::string& second) {
    const auto found = std::find_if(bonds.begin(), bonds.end(), [&](const Bond& value) {
        return (value.atomA == first && value.atomB == second) || (value.atomA == second && value.atomB == first);
    });
    return found == bonds.end() ? nullptr : &*found;
}

std::string Molecule::allocateAtomId() {
    for (;;) {
        const std::string result = "A" + std::to_string(nextAtomId++);
        if (!atom(result)) return result;
    }
}
std::string Molecule::allocateBondId() {
    for (;;) {
        const std::string result = "B" + std::to_string(nextBondId++);
        if (!bond(result)) return result;
    }
}
std::string Molecule::addAtom(Point position, std::string element) {
    const std::string stableId = allocateAtomId();
    atoms.push_back(Atom{.id = stableId, .element = std::move(element), .position = position});
    return stableId;
}
std::string Molecule::addBond(const std::string& first, const std::string& second,
                              BondType type, BondStereo stereo) {
    if (first == second || !atom(first) || !atom(second)) return {};
    if (Bond* existing = bondBetween(first, second)) {
        existing->type = type;
        existing->displayType = type == BondType::Aromatic
            ? std::optional<BondType>((numericSuffix(existing->id,'B')%2)?BondType::Double:BondType::Single)
            : std::nullopt;
        existing->stereo = stereo;
        return existing->id;
    }
    const std::string stableId = allocateBondId();
    bonds.push_back(Bond{.id = stableId, .atomA = first, .atomB = second, .type = type,
        .displayType = type == BondType::Aromatic ? std::optional<BondType>((numericSuffix(stableId,'B')%2)?BondType::Double:BondType::Single) : std::nullopt,
        .stereo = stereo});
    return stableId;
}
bool Molecule::removeAtom(const std::string& stableId) {
    const auto before = atoms.size();
    std::erase_if(atoms, [&](const Atom& value) { return value.id == stableId; });
    if (atoms.size() == before) return false;
    std::erase_if(bonds, [&](const Bond& value) { return value.atomA == stableId || value.atomB == stableId; });
    for (auto& [_, pose] : poses) pose.atomPositions.erase(stableId);
    return true;
}
bool Molecule::removeBond(const std::string& stableId) {
    const auto before = bonds.size();
    std::erase_if(bonds, [&](const Bond& value) { return value.id == stableId; });
    return bonds.size() != before;
}
void Molecule::validateIds() const {
    std::set<std::string> atomIds;
    for (const Atom& value : atoms) {
        if (value.id.empty() || !atomIds.insert(value.id).second) throw std::runtime_error("Duplicate or empty atom ID: " + value.id);
    }
    std::set<std::string> bondIds;
    for (const Bond& value : bonds) {
        if (value.id.empty() || !bondIds.insert(value.id).second) throw std::runtime_error("Duplicate or empty bond ID: " + value.id);
        if (!atomIds.contains(value.atomA) || !atomIds.contains(value.atomB) || value.atomA == value.atomB) {
            throw std::runtime_error("Bond " + value.id + " has invalid endpoints");
        }
    }
}

Molecule* Project::molecule(const std::string& stableId) {
    const auto found = std::find_if(molecules.begin(), molecules.end(), [&](const Molecule& value) { return value.id == stableId; });
    return found == molecules.end() ? nullptr : &*found;
}
const Molecule* Project::molecule(const std::string& stableId) const {
    const auto found = std::find_if(molecules.begin(), molecules.end(), [&](const Molecule& value) { return value.id == stableId; });
    return found == molecules.end() ? nullptr : &*found;
}
std::string Project::addBlankMolecule(std::string name) {
    std::string id;
    do { id = "molecule" + std::to_string(nextMoleculeId++); } while (molecule(id));
    if (name.empty()) name = id;
    Molecule value;
    value.id = id;
    value.name = std::move(name);
    molecules.push_back(std::move(value));
    const std::string createNodeId=addNode("molecule_create", json({{"target", id}}).dump());
    (void)createNodeId;
    return id;
}
std::string Project::addAtomTween(const std::string& moleculeId, const std::string& atomId,
                                  int startFrame, int frames, Point target, Easing easing) {
    const Molecule* value = molecule(moleculeId);
    if (!value || !value->atom(atomId)) throw std::runtime_error("Atom tween references an unknown molecule or atom");
    const std::string id = "T" + std::to_string(nextTimelineId++);
    atomTweens.push_back({id,moleculeId,atomId,startFrame,frames,target,easing});
    return id;
}
ScriptNode* Project::node(const std::string& stableId) {
    const auto found=std::find_if(nodes.begin(),nodes.end(),[&](const ScriptNode& value){return value.id==stableId;});
    return found==nodes.end()?nullptr:&*found;
}
const ScriptNode* Project::node(const std::string& stableId) const {
    const auto found=std::find_if(nodes.begin(),nodes.end(),[&](const ScriptNode& value){return value.id==stableId;});
    return found==nodes.end()?nullptr:&*found;
}
std::string Project::addNode(const std::string& type,std::string paramsJson,std::optional<std::size_t> index) {
    if(paramsJson.empty()||paramsJson=="{}") paramsJson=defaultNodeParamsJson(type);
    // Validate at the boundary; invalid JSON must never enter the C++ model.
    const json parsed=json::parse(paramsJson); if(!parsed.is_object()) throw std::runtime_error("Node params must be a JSON object");
    std::string id; do{id="N"+std::to_string(nextNodeId++);}while(node(id));
    ScriptNode value{id,type,true,std::move(paramsJson)};
    if(index&&*index<nodes.size()) {
        const std::size_t safeIndex=(!nodes.empty()&&nodes.front().type=="scene"&&type!="scene")?std::max<std::size_t>(1,*index):*index;
        nodes.insert(nodes.begin()+static_cast<std::ptrdiff_t>(safeIndex),std::move(value));
    }
    else nodes.push_back(std::move(value));
    return id;
}
void Project::ensureDefaultNodes() {
    if(!nodes.empty()) return;
    const std::string sceneNodeId=addNode("scene");
    (void)sceneNodeId;
    for(const Molecule& molecule:molecules) {
        const std::string createNodeId=addNode("molecule_create",json({{"target",molecule.id}}).dump());
        (void)createNodeId;
    }
}
void Project::validateIds() const {
    std::set<std::string> moleculeIds;
    for (const Molecule& value : molecules) {
        if (value.id.empty() || !moleculeIds.insert(value.id).second) throw std::runtime_error("Duplicate or empty molecule ID: " + value.id);
        value.validateIds();
    }
    std::set<std::string> nodeIds;
    for(const ScriptNode& value:nodes){
        if(value.id.empty()||!nodeIds.insert(value.id).second)throw std::runtime_error("Duplicate or empty node ID: "+value.id);
        const json params=json::parse(value.paramsJson); if(!params.is_object())throw std::runtime_error("Node params are not an object: "+value.id);
    }
}

const char* toString(BondType value) {
    switch (value) {
        case BondType::Single: return "single";
        case BondType::Double: return "double";
        case BondType::Triple: return "triple";
        case BondType::Aromatic: return "aromatic";
    }
    return "single";
}
const char* toString(BondStereo value) {
    switch (value) {
        case BondStereo::None: return "none";
        case BondStereo::SolidWedge: return "wedge";
        case BondStereo::DashedWedge: return "dash";
        case BondStereo::Wavy: return "wavy";
    }
    return "none";
}
BondType bondTypeFromString(const std::string& value) {
    if (value == "double") return BondType::Double;
    if (value == "triple") return BondType::Triple;
    if (value == "aromatic") return BondType::Aromatic;
    return BondType::Single;
}
BondStereo bondStereoFromString(const std::string& value) {
    if (value == "wedge") return BondStereo::SolidWedge;
    if (value == "dash") return BondStereo::DashedWedge;
    if (value == "wavy" || value == "either") return BondStereo::Wavy;
    return BondStereo::None;
}

std::string toJson(const Project& project, int indent) {
    json root{{"format", "chemanim-native-2d"}, {"version", 4}, {"mod", project.mod}, {"next_molecule_id", project.nextMoleculeId}, {"next_timeline_id", project.nextTimelineId}, {"next_node_id",project.nextNodeId}};
    root["scene"] = {{"width", project.scene.width}, {"height", project.scene.height},
        {"logic_width", project.scene.logicWidth}, {"logic_height", project.scene.logicHeight},
        {"fps", project.scene.fps}, {"view_zoom", project.scene.viewZoom},
        {"background", project.scene.background}, {"title", project.scene.title}};
    root["style"] = {{"preset", project.style.preset}, {"font_family", project.style.fontFamily},
        {"font_file", project.style.fontFile}, {"font_pt", project.style.fontPt},
        {"bond_length_pt", project.style.bondLengthPt}, {"line_width_pt", project.style.lineWidthPt},
        {"double_bond_spacing", project.style.doubleBondSpacing}};
    root["molecules"] = json::array();
    for (const Molecule& molecule : project.molecules) {
        json item{{"id", molecule.id}, {"name", molecule.name}, {"source_smiles", molecule.sourceSmiles},
            {"reference_bond_length", molecule.referenceBondLength}, {"next_atom_id", molecule.nextAtomId},
            {"next_bond_id", molecule.nextBondId}, {"x", molecule.scenePosition.x}, {"y", molecule.scenePosition.y},
            {"rotation", molecule.rotation}, {"scale", molecule.scale}, {"alpha", molecule.alpha}, {"layer", molecule.layer}, {"visible",molecule.visible}};
        item["atoms"] = json::array();
        for (const Atom& atom : molecule.atoms) item["atoms"].push_back({{"id", atom.id}, {"element", atom.element},
            {"alias", atom.alias}, {"isotope", atom.isotope}, {"formal_charge", atom.formalCharge},
            {"radical_electrons", atom.radicalElectrons}, {"implicit_hydrogens", atom.implicitHydrogens},
            {"aromatic", atom.aromatic}, {"hidden", atom.hidden}, {"x", atom.position.x}, {"y", atom.position.y}});
        item["bonds"] = json::array();
        for (const Bond& bond : molecule.bonds) {
            json raw={{"id", bond.id}, {"a", bond.atomA}, {"b", bond.atomB}, {"type", toString(bond.type)},
                {"order", bond.type == BondType::Double ? 2.0 : bond.type == BondType::Triple ? 3.0 : bond.type == BondType::Aromatic ? 1.5 : 1.0},
                {"aromatic", bond.type == BondType::Aromatic}, {"stereo", toString(bond.stereo)}, {"visible", bond.visible}};
            if(bond.displayType)raw["display_type"]=toString(*bond.displayType);
            item["bonds"].push_back(std::move(raw));
        }
        item["poses"] = json::object();
        for (const auto& [id, pose] : molecule.poses) {
            json positions = json::object();
            for (const auto& [atomId, position] : pose.atomPositions) pointToJson(positions[atomId], position);
            item["poses"][id] = {{"id", pose.id}, {"atoms", std::move(positions)}};
        }
        root["molecules"].push_back(std::move(item));
    }
    root["nodes"]=json::array();
    for(const ScriptNode& node:project.nodes)root["nodes"].push_back({{"id",node.id},{"type",node.type},{"enabled",node.enabled},{"params",json::parse(node.paramsJson)}});
    return root.dump(indent);
}

Project fromJson(const std::string& source) {
    const json root = json::parse(source);
    if (root.value("format", "") != "chemanim-native-2d") throw std::runtime_error("Not a Chemanim native 2D project");
    const int version = root.value("version", 0);
    if (version != 2 && version != 3 && version != 4) throw std::runtime_error("Unsupported Chemanim native 2D project version");
    Project project;
    project.mod = root.value("mod", project.mod);
    project.nextMoleculeId = root.value("next_molecule_id", std::uint64_t{1});
    project.nextTimelineId = root.value("next_timeline_id", std::uint64_t{1});
    project.nextNodeId = root.value("next_node_id", std::uint64_t{1});
    if (const auto found = root.find("scene"); found != root.end()) {
        project.scene.width = found->value("width", project.scene.width); project.scene.height = found->value("height", project.scene.height);
        project.scene.logicWidth = found->value("logic_width", project.scene.logicWidth); project.scene.logicHeight = found->value("logic_height", project.scene.logicHeight);
        project.scene.fps = found->value("fps", project.scene.fps); project.scene.viewZoom = found->value("view_zoom", project.scene.viewZoom);
        project.scene.background = found->value("background", project.scene.background); project.scene.title = found->value("title", project.scene.title);
    }
    if (const auto found = root.find("style"); found != root.end()) {
        project.style.preset = found->value("preset", project.style.preset); project.style.fontFamily = found->value("font_family", project.style.fontFamily);
        project.style.fontFile = found->value("font_file", project.style.fontFile); project.style.fontPt = found->value("font_pt", project.style.fontPt);
        project.style.bondLengthPt = found->value("bond_length_pt", project.style.bondLengthPt); project.style.lineWidthPt = found->value("line_width_pt", project.style.lineWidthPt);
        project.style.doubleBondSpacing = found->value("double_bond_spacing", project.style.doubleBondSpacing);
    }
    for (const json& raw : root.value("molecules", json::array())) {
        Molecule molecule;
        molecule.id = raw.value("id", ""); molecule.name = raw.value("name", molecule.id); molecule.sourceSmiles = raw.value("source_smiles", "");
        molecule.referenceBondLength = raw.value("reference_bond_length", molecule.referenceBondLength);
        molecule.nextAtomId = raw.value("next_atom_id", std::uint64_t{1}); molecule.nextBondId = raw.value("next_bond_id", std::uint64_t{1});
        molecule.scenePosition = {raw.value("x", 0.0), raw.value("y", 0.0)}; molecule.rotation = raw.value("rotation", 0.0);
        molecule.scale = raw.value("scale", 2.2); molecule.alpha = raw.value("alpha", 255); molecule.layer = raw.value("layer", 0); molecule.visible=raw.value("visible",true);
        for (const json& value : raw.value("atoms", json::array())) {
            Atom atom; atom.id = value.value("id", ""); atom.element = value.value("element", "C"); atom.alias = value.value("alias", "");
            atom.isotope = value.value("isotope", 0); atom.formalCharge = value.value("formal_charge", 0); atom.radicalElectrons = value.value("radical_electrons", 0);
            atom.implicitHydrogens = value.value("implicit_hydrogens", 0); atom.aromatic = value.value("aromatic", false); atom.hidden = value.value("hidden", false);
            atom.position = {value.value("x", 0.0), value.value("y", 0.0)}; molecule.nextAtomId = std::max(molecule.nextAtomId, numericSuffix(atom.id, 'A') + 1); molecule.atoms.push_back(std::move(atom));
        }
        for (const json& value : raw.value("bonds", json::array())) {
            Bond bond; bond.id = value.value("id", ""); bond.atomA = value.value("a", ""); bond.atomB = value.value("b", "");
            if (value.contains("type")) bond.type = bondTypeFromString(value.value("type", "single"));
            else { const double order = value.value("order", 1.0); bond.type = value.value("aromatic", false) ? BondType::Aromatic : order > 2.5 ? BondType::Triple : order > 1.5 ? BondType::Double : BondType::Single; }
            if(value.contains("display_type"))bond.displayType=bondTypeFromString(value.value("display_type","single"));
            else if(bond.type==BondType::Aromatic)bond.displayType=(numericSuffix(bond.id,'B')%2)?BondType::Double:BondType::Single;
            bond.stereo = bondStereoFromString(value.value("stereo", "none")); bond.visible = value.value("visible", true);
            molecule.nextBondId = std::max(molecule.nextBondId, numericSuffix(bond.id, 'B') + 1); molecule.bonds.push_back(std::move(bond));
        }
        if (const auto poses = raw.find("poses"); poses != raw.end() && poses->is_object()) for (const auto& [id, value] : poses->items()) {
            Pose pose; pose.id = value.value("id", id);
            if (const auto positions = value.find("atoms"); positions != value.end()) for (const auto& [atomId, point] : positions->items()) pose.atomPositions[atomId] = pointFromJson(point);
            molecule.poses[id] = std::move(pose);
        }
        project.nextMoleculeId = std::max(project.nextMoleculeId, numericSuffix(molecule.id, "molecule") + 1);
        project.molecules.push_back(std::move(molecule));
    }
    if (const auto timeline = root.find("timeline"); timeline != root.end()) {
        for (const json& value : timeline->value("atom_tweens", json::array())) { const std::string id=value.value("id","T"+std::to_string(project.nextTimelineId++)); project.nextTimelineId=std::max(project.nextTimelineId,numericSuffix(id,'T')+1); project.atomTweens.push_back({
            id, value.value("molecule", ""), value.value("atom", ""), value.value("start", 0), value.value("frames", 30),
            {value.value("x", 0.0), value.value("y", 0.0)}, static_cast<Easing>(value.value("easing", 0))}); }
        for (const json& value : timeline->value("pose_tweens", json::array())) { const std::string id=value.value("id","T"+std::to_string(project.nextTimelineId++)); project.nextTimelineId=std::max(project.nextTimelineId,numericSuffix(id,'T')+1); project.poseTweens.push_back({
            id, value.value("molecule", ""), value.value("pose", ""), value.value("start", 0), value.value("frames", 30),
            static_cast<Easing>(value.value("easing", 0))}); }
    }
    if(version>=4){
        for(const json& value:root.value("nodes",json::array())){
            ScriptNode node{value.value("id",""),value.value("type",""),value.value("enabled",true),value.value("params",json::object()).dump()};
            project.nextNodeId=std::max(project.nextNodeId,numericSuffix(node.id,'N')+1);project.nodes.push_back(std::move(node));
        }
    } else {
        project.ensureDefaultNodes();
        struct LegacyCommand{int start;std::size_t order;std::string type;json params;};std::vector<LegacyCommand> commands;std::size_t order=0;
        for(const AtomTween& tween:project.atomTweens)commands.push_back({tween.startFrame,order++,"atom_lerp_xy",{{"target",tween.moleculeId},{"atom",tween.atomId},{"x",tween.target.x},{"y",tween.target.y},{"frames",tween.frames},{"easing","linear"}}});
        for(const PoseTween& tween:project.poseTweens)commands.push_back({tween.startFrame,order++,"atom_lerp_pose",{{"target",tween.moleculeId},{"pose",tween.poseId},{"frames",tween.frames},{"easing","linear"}}});
        std::stable_sort(commands.begin(),commands.end(),[](const LegacyCommand& a,const LegacyCommand& b){return a.start!=b.start?a.start<b.start:a.order<b.order;});
        int cursor=0;for(const LegacyCommand& command:commands){if(command.start>cursor){const std::string waitId=project.addNode("wait",json({{"frames",command.start-cursor}}).dump());(void)waitId;cursor=command.start;}const std::string migratedId=project.addNode(command.type,command.params.dump());(void)migratedId;}
        project.atomTweens.clear();project.poseTweens.clear();
    }
    project.ensureDefaultNodes();
    project.validateIds();
    return project;
}

Project loadProject(const std::filesystem::path& path) {
    std::ifstream stream(path, std::ios::binary);
    if (!stream) throw std::runtime_error("Unable to open project: " + path.string());
    return fromJson(std::string(std::istreambuf_iterator<char>(stream), {}));
}
void saveProject(const Project& project, const std::filesystem::path& path) {
    project.validateIds();
    std::filesystem::create_directories(path.parent_path());
    const auto temporary = path.string() + ".tmp";
    { std::ofstream stream(temporary, std::ios::binary | std::ios::trunc); if (!stream) throw std::runtime_error("Unable to write project"); stream << toJson(project) << '\n'; }
#ifdef _WIN32
    if (!MoveFileExW(std::filesystem::path(temporary).c_str(), path.c_str(),
                     MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH)) {
        const DWORD error = GetLastError();
        std::filesystem::remove(temporary);
        throw std::runtime_error("Unable to replace project file (Windows error " + std::to_string(error) + ")");
    }
#else
    std::filesystem::rename(temporary, path);
#endif
}

}  // namespace chem::core
