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
void colorToJson(json& value, const Color& color) {
    value = json{{"r", color.red}, {"g", color.green}, {"b", color.blue}};
}
Color colorFromJson(const json& value, Color fallback = {}) {
    return {value.value("r", fallback.red), value.value("g", fallback.green),
            value.value("b", fallback.blue)};
}

void migrateProjectWideStableIds(Project& project) {
    std::uint64_t nextAtom=1,nextBond=1,nextAdornment=1;
    for(const Molecule& molecule:project.molecules){
        for(const Atom& value:molecule.atoms)nextAtom=std::max(nextAtom,numericSuffix(value.id,'A')+1);
        for(const Bond& value:molecule.bonds)nextBond=std::max(nextBond,numericSuffix(value.id,'B')+1);
        for(const AtomAdornment& value:molecule.adornments)nextAdornment=std::max(nextAdornment,numericSuffix(value.id,'D')+1);
    }
    std::set<std::string> atomIds,bondIds,adornmentIds;
    struct Remap { std::map<std::string,std::string> atoms,bonds,adornments; };
    std::map<std::string,Remap> remaps;
    for(Molecule& molecule:project.molecules){
        Remap& remap=remaps[molecule.id];
        for(Atom& value:molecule.atoms){const std::string old=value.id;if(!atomIds.insert(old).second){do value.id="A"+std::to_string(nextAtom++);while(!atomIds.insert(value.id).second);remap.atoms[old]=value.id;}}
        for(Bond& value:molecule.bonds){if(auto it=remap.atoms.find(value.atomA);it!=remap.atoms.end())value.atomA=it->second;if(auto it=remap.atoms.find(value.atomB);it!=remap.atoms.end())value.atomB=it->second;const std::string old=value.id;if(!bondIds.insert(old).second){do value.id="B"+std::to_string(nextBond++);while(!bondIds.insert(value.id).second);remap.bonds[old]=value.id;}}
        for(AtomAdornment& value:molecule.adornments){if(auto it=remap.atoms.find(value.atomId);it!=remap.atoms.end())value.atomId=it->second;const std::string old=value.id;if(!adornmentIds.insert(old).second){do value.id="D"+std::to_string(nextAdornment++);while(!adornmentIds.insert(value.id).second);remap.adornments[old]=value.id;}}
        for(auto& [_,pose]:molecule.poses){std::map<std::string,Point> positions;for(const auto& [id,point]:pose.atomPositions){const auto it=remap.atoms.find(id);positions[it==remap.atoms.end()?id:it->second]=point;}pose.atomPositions=std::move(positions);}
        molecule.nextAtomId=std::max(molecule.nextAtomId,nextAtom);molecule.nextBondId=std::max(molecule.nextBondId,nextBond);molecule.nextAdornmentId=std::max(molecule.nextAdornmentId,nextAdornment);
    }
    const auto rename=[&](json& params,const std::string& moleculeId,const char* key,const std::map<std::string,std::string> Remap::* member){
        const auto mapIt=remaps.find(moleculeId);if(mapIt==remaps.end())return;const auto& values=mapIt->second.*member;auto found=params.find(key);if(found==params.end())return;
        if(found->is_string()){if(auto it=values.find(found->get<std::string>());it!=values.end())*found=it->second;}
        else if(found->is_array())for(json& value:*found)if(value.is_string())if(auto it=values.find(value.get<std::string>());it!=values.end())value=it->second;
    };
    for(ScriptNode& node:project.nodes){json params=json::parse(node.paramsJson);const std::string target=params.value("target","");rename(params,target,"atom",&Remap::atoms);rename(params,target,"atoms",&Remap::atoms);rename(params,target,"bond",&Remap::bonds);rename(params,target,"bonds",&Remap::bonds);rename(params,target,"adornment",&Remap::adornments);rename(params,target,"adornments",&Remap::adornments);
        if(node.type=="bond_form"){rename(params,target,"a",&Remap::atoms);rename(params,target,"b",&Remap::atoms);}
        if(node.type=="merge_molecules"){rename(params,target,"a",&Remap::atoms);rename(params,params.value("source",""),"b",&Remap::atoms);}
        node.paramsJson=params.dump();
    }
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
AtomAdornment* Molecule::adornment(const std::string& stableId) {
    const auto found = std::find_if(adornments.begin(), adornments.end(), [&](const AtomAdornment& value) { return value.id == stableId; });
    return found == adornments.end() ? nullptr : &*found;
}
const AtomAdornment* Molecule::adornment(const std::string& stableId) const {
    const auto found = std::find_if(adornments.begin(), adornments.end(), [&](const AtomAdornment& value) { return value.id == stableId; });
    return found == adornments.end() ? nullptr : &*found;
}
Bond* Molecule::bondBetween(const std::string& first, const std::string& second) {
    const auto found = std::find_if(bonds.begin(), bonds.end(), [&](const Bond& value) {
        return value.alive && ((value.atomA == first && value.atomB == second) || (value.atomA == second && value.atomB == first));
    });
    return found == bonds.end() ? nullptr : &*found;
}
const Atom* Molecule::anchorAtom() const {
    const Atom* result = nullptr;
    for (const Atom& value : atoms) {
        if (!value.alive) continue;
        if (!result || value.creationSerial < result->creationSerial) result = &value;
    }
    return result;
}
std::optional<Point> Molecule::coordinate() const {
    return origin;
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
std::string Molecule::allocateAdornmentId() {
    for (;;) {
        const std::string result = "D" + std::to_string(nextAdornmentId++);
        if (!adornment(result)) return result;
    }
}
std::string Molecule::addAtom(Point position, std::string element, std::uint64_t creationSerial) {
    const std::string stableId = allocateAtomId();
    atoms.push_back(Atom{.id = stableId, .creationSerial = creationSerial,
                         .element = std::move(element), .position = position});
    return stableId;
}
std::string Molecule::addBond(const std::string& first, const std::string& second,
                              BondType type, BondStereo stereo) {
    if (first == second || !atom(first) || !atom(second)) return {};
    if (Bond* existing = bondBetween(first, second)) {
        existing->type = type;
        existing->stereo = stereo;
        existing->alive = true;
        return existing->id;
    }
    const std::string stableId = allocateBondId();
    bonds.push_back(Bond{.id = stableId, .atomA = first, .atomB = second, .type = type,
        .stereo = stereo});
    return stableId;
}
std::string Molecule::addAdornment(const std::string& atomId, std::string text,
                                    Point offset, std::uint64_t creationSerial) {
    const Atom* owner = atom(atomId);
    if (!owner || !owner->alive) return {};
    const std::string stableId = allocateAdornmentId();
    adornments.push_back(AtomAdornment{.id = stableId, .creationSerial = creationSerial,
        .atomId = atomId, .text = std::move(text), .offset = offset});
    return stableId;
}
bool Molecule::removeAtom(const std::string& stableId) {
    Atom* value = atom(stableId);
    if (!value || !value->alive) return false;
    value->alive = false;
    for (Bond& bondValue : bonds) {
        if (bondValue.atomA == stableId || bondValue.atomB == stableId) bondValue.alive = false;
    }
    for (AtomAdornment& adornmentValue : adornments) {
        if (adornmentValue.atomId == stableId) adornmentValue.alive = false;
    }
    return true;
}
bool Molecule::removeBond(const std::string& stableId) {
    Bond* value = bond(stableId);
    if (!value || !value->alive) return false;
    value->alive = false;
    return true;
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
    std::set<std::string> adornmentIds;
    for (const AtomAdornment& value : adornments) {
        if (value.id.empty() || !adornmentIds.insert(value.id).second) throw std::runtime_error("Duplicate or empty adornment ID: " + value.id);
        if (!atomIds.contains(value.atomId)) throw std::runtime_error("Adornment " + value.id + " has an invalid atom anchor");
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
std::string Project::addBlankMolecule(std::string name,
                                      std::optional<std::size_t> insertionIndex) {
    std::string id;
    do { id = "molecule" + std::to_string(nextMoleculeId++); } while (molecule(id));
    if (name.empty()) name = id;
    Molecule value;
    value.id = id;
    value.name = std::move(name);
    // Atom/bond/adornment IDs are referenced by ordered nodes and survive
    // ownership transfer.  Start every new molecule above the project-wide
    // high-water mark so DetachSubgraph/MergeMolecules can move records without
    // renaming them.
    for (const Molecule& existing : molecules) {
        value.nextAtomId = std::max(value.nextAtomId, existing.nextAtomId);
        value.nextBondId = std::max(value.nextBondId, existing.nextBondId);
        value.nextAdornmentId = std::max(value.nextAdornmentId, existing.nextAdornmentId);
        for (const Atom& atomValue : existing.atoms)
            value.nextAtomId = std::max(value.nextAtomId, numericSuffix(atomValue.id, 'A') + 1);
        for (const Bond& bondValue : existing.bonds)
            value.nextBondId = std::max(value.nextBondId, numericSuffix(bondValue.id, 'B') + 1);
        for (const AtomAdornment& adornmentValue : existing.adornments)
            value.nextAdornmentId = std::max(value.nextAdornmentId, numericSuffix(adornmentValue.id, 'D') + 1);
    }
    molecules.push_back(std::move(value));
    const std::string createNodeId=addNode("molecule_create", json({{"target", id}}).dump(), insertionIndex);
    (void)createNodeId;
    return id;
}

std::string Project::duplicateMolecule(const std::string& sourceId,
                                       std::optional<std::size_t> nodeIndex) {
    const Molecule* source = molecule(sourceId);
    if (!source) throw std::runtime_error("Cannot duplicate unknown molecule: " + sourceId);
    const Molecule sourceCopy = *source;
    std::string id;
    do { id = "molecule" + std::to_string(nextMoleculeId++); } while (molecule(id));

    std::uint64_t nextAtom = 1, nextBond = 1, nextAdornment = 1;
    for (const Molecule& existing : molecules) {
        for (const Atom& value : existing.atoms) nextAtom = std::max(nextAtom, numericSuffix(value.id, 'A') + 1);
        for (const Bond& value : existing.bonds) nextBond = std::max(nextBond, numericSuffix(value.id, 'B') + 1);
        for (const AtomAdornment& value : existing.adornments) nextAdornment = std::max(nextAdornment, numericSuffix(value.id, 'D') + 1);
    }
    Molecule copy = sourceCopy;
    copy.id = id;
    copy.name = sourceCopy.name.empty() ? id : sourceCopy.name + " 副本";
    std::map<std::string, std::string> atomIds, bondIds, adornmentIds;
    for (Atom& atom : copy.atoms) {
        const std::string old = atom.id;
        atom.id = "A" + std::to_string(nextAtom++);
        atom.creationSerial = allocateCreationSerial();
        atomIds.emplace(old, atom.id);
    }
    for (Bond& bond : copy.bonds) {
        const std::string old = bond.id;
        bond.id = "B" + std::to_string(nextBond++);
        bond.atomA = atomIds.at(bond.atomA);
        bond.atomB = atomIds.at(bond.atomB);
        bondIds.emplace(old, bond.id);
    }
    for (AtomAdornment& adornment : copy.adornments) {
        const std::string old = adornment.id;
        adornment.id = "D" + std::to_string(nextAdornment++);
        adornment.atomId = atomIds.at(adornment.atomId);
        adornment.creationSerial = allocateCreationSerial();
        adornmentIds.emplace(old, adornment.id);
    }
    std::map<std::string, Pose> remappedPoses;
    for (auto& [poseId, pose] : copy.poses) {
        std::map<std::string, Point> positions;
        for (const auto& [oldAtom, point] : pose.atomPositions)
            if (const auto found = atomIds.find(oldAtom); found != atomIds.end()) positions.emplace(found->second, point);
        pose.atomPositions = std::move(positions);
        remappedPoses.emplace(poseId, std::move(pose));
    }
    copy.poses = std::move(remappedPoses);
    copy.nextAtomId = nextAtom;
    copy.nextBondId = nextBond;
    copy.nextAdornmentId = nextAdornment;
    molecules.push_back(std::move(copy));
    const std::string createNodeId=addNode("molecule_create", json({{"target", id}}).dump(), nodeIndex);
    (void)createNodeId;
    return id;
}
std::uint64_t Project::allocateCreationSerial() { return nextCreationSerial++; }
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
    if(type=="molecule_create") {
        const std::string target=parsed.value("target","");
        if(target.empty() || !molecule(target)) throw std::runtime_error("New molecule node requires its own valid molecule");
        for(const ScriptNode& existing:nodes) if(existing.type=="molecule_create") {
            const json current=json::parse(existing.paramsJson);
            if(current.value("target","")==target)
                throw std::runtime_error("Molecule already has a creation node: "+target);
        }
    }
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
    std::set<std::uint64_t> creationSerials;
    std::set<std::string> atomIds,bondIds,adornmentIds;
    for (const Molecule& value : molecules) {
        if (value.id.empty() || !moleculeIds.insert(value.id).second) throw std::runtime_error("Duplicate or empty molecule ID: " + value.id);
        value.validateIds();
        for (const Atom& atomValue : value.atoms) {
            if(!atomIds.insert(atomValue.id).second)throw std::runtime_error("Atom stable ID is not project-wide unique: "+atomValue.id);
            if (!atomValue.creationSerial || !creationSerials.insert(atomValue.creationSerial).second)
                throw std::runtime_error("Duplicate or empty atom creation serial");
        }
        for (const AtomAdornment& adornmentValue : value.adornments) {
            if(!adornmentIds.insert(adornmentValue.id).second)throw std::runtime_error("Adornment stable ID is not project-wide unique: "+adornmentValue.id);
            if (!adornmentValue.creationSerial || !creationSerials.insert(adornmentValue.creationSerial).second)
                throw std::runtime_error("Duplicate or empty adornment creation serial");
        }
        for(const Bond& bondValue:value.bonds)if(!bondIds.insert(bondValue.id).second)throw std::runtime_error("Bond stable ID is not project-wide unique: "+bondValue.id);
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
    }
    return "single";
}
const char* toString(BondStereo value) {
    switch (value) {
        case BondStereo::None: return "none";
        case BondStereo::SolidWedge: return "wedge";
        case BondStereo::DashedWedge: return "dash";
        case BondStereo::SolidBar: return "solid_bar";
        case BondStereo::HashedBar: return "hashed_bar";
        case BondStereo::Wavy: return "wavy";
    }
    return "none";
}
BondType bondTypeFromString(const std::string& value) {
    if (value == "double") return BondType::Double;
    if (value == "triple") return BondType::Triple;
    return BondType::Single;
}
BondStereo bondStereoFromString(const std::string& value) {
    if (value == "wedge") return BondStereo::SolidWedge;
    if (value == "dash") return BondStereo::DashedWedge;
    if (value == "solid_bar" || value == "bold") return BondStereo::SolidBar;
    if (value == "hashed_bar" || value == "hashed") return BondStereo::HashedBar;
    if (value == "wavy" || value == "either") return BondStereo::Wavy;
    return BondStereo::None;
}
const char* toString(SecondaryLineSide value) {
    switch (value) {
        case SecondaryLineSide::Left: return "left";
        case SecondaryLineSide::Right: return "right";
        case SecondaryLineSide::Center: return "center";
    }
    return "center";
}
SecondaryLineSide secondaryLineSideFromString(const std::string& value) {
    if (value == "left") return SecondaryLineSide::Left;
    if (value == "right") return SecondaryLineSide::Right;
    return SecondaryLineSide::Center;
}
const char* toString(AtomLabelSide value) {
    return value == AtomLabelSide::Left ? "left" : "right";
}
AtomLabelSide atomLabelSideFromString(const std::string& value) {
    return value == "left" ? AtomLabelSide::Left : AtomLabelSide::Right;
}
const char* toString(AtomNumberStyle value) {
    switch (value) {
        case AtomNumberStyle::Normal: return "normal";
        case AtomNumberStyle::Superscript: return "superscript";
        case AtomNumberStyle::Subscript: return "subscript";
    }
    return "subscript";
}
AtomNumberStyle atomNumberStyleFromString(const std::string& value) {
    if (value == "normal") return AtomNumberStyle::Normal;
    if (value == "superscript") return AtomNumberStyle::Superscript;
    return AtomNumberStyle::Subscript;
}

std::string toJson(const Project& project, int indent) {
    json root{{"format", "chemanim-native-2d"}, {"version", 8}, {"mod", project.mod},
        {"next_molecule_id", project.nextMoleculeId}, {"next_timeline_id", project.nextTimelineId},
        {"next_node_id",project.nextNodeId}, {"next_creation_serial", project.nextCreationSerial}};
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
            {"anchor", {{"x", molecule.origin.x}, {"y", molecule.origin.y}}},
            {"reference_bond_length", molecule.referenceBondLength}, {"next_atom_id", molecule.nextAtomId},
            {"next_bond_id", molecule.nextBondId}, {"next_adornment_id", molecule.nextAdornmentId},
            {"rotation", molecule.rotation}, {"scale_x", molecule.scaleX}, {"scale_y", molecule.scaleY}, {"alpha", molecule.alpha},
            {"layer", molecule.layer}, {"visible",molecule.visible}, {"retired", molecule.retired}};
        colorToJson(item["color"], molecule.color);
        item["atoms"] = json::array();
        for (const Atom& atom : molecule.atoms) item["atoms"].push_back({{"id", atom.id}, {"element", atom.element},
            {"creation_serial", atom.creationSerial}, {"label", atom.alias},
            {"label_side", toString(atom.labelSide)}, {"number_style", toString(atom.numberStyle)},
            {"isotope", atom.isotope},
            {"radical_electrons", atom.radicalElectrons}, {"implicit_hydrogens", atom.implicitHydrogens},
            {"hidden", atom.hidden}, {"alive", atom.alive}, {"alpha", atom.alpha},
            {"color", {{"r", atom.color.red}, {"g", atom.color.green}, {"b", atom.color.blue}}},
            {"x", atom.position.x}, {"y", atom.position.y}});
        item["bonds"] = json::array();
        for (const Bond& bond : molecule.bonds) {
            json raw={{"id", bond.id}, {"a", bond.atomA}, {"b", bond.atomB}, {"type", toString(bond.type)},
                {"secondary_line_side", toString(bond.secondaryLineSide)}, {"stereo", toString(bond.stereo)},
                {"visible", bond.visible}, {"alive", bond.alive}, {"alpha", bond.alpha},
                {"color", {{"r", bond.color.red}, {"g", bond.color.green}, {"b", bond.color.blue}}}};
            item["bonds"].push_back(std::move(raw));
        }
        item["adornments"] = json::array();
        for (const AtomAdornment& adornment : molecule.adornments) {
            item["adornments"].push_back({{"id", adornment.id}, {"creation_serial", adornment.creationSerial},
                {"atom", adornment.atomId}, {"text", adornment.text}, {"x", adornment.offset.x},
                {"y", adornment.offset.y}, {"alpha", adornment.alpha}, {"alive", adornment.alive},
                {"color", {{"r", adornment.color.red}, {"g", adornment.color.green}, {"b", adornment.color.blue}}}});
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
    if (version < 2 || version > 8) throw std::runtime_error("Unsupported Chemanim native 2D project version");
    Project project;
    std::map<std::string,std::pair<Point,double>> legacyTransforms;
    project.mod = root.value("mod", project.mod);
    project.nextMoleculeId = root.value("next_molecule_id", std::uint64_t{1});
    project.nextTimelineId = root.value("next_timeline_id", std::uint64_t{1});
    project.nextNodeId = root.value("next_node_id", std::uint64_t{1});
    project.nextCreationSerial = root.value("next_creation_serial", std::uint64_t{1});
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
        if (version >= 8) molecule.origin = pointFromJson(raw.value("anchor", json::object()));
        molecule.referenceBondLength = raw.value("reference_bond_length", molecule.referenceBondLength);
        molecule.nextAtomId = raw.value("next_atom_id", std::uint64_t{1}); molecule.nextBondId = raw.value("next_bond_id", std::uint64_t{1});
        molecule.nextAdornmentId = raw.value("next_adornment_id", std::uint64_t{1});
        const Point legacyOrigin{raw.value("x", 0.0), raw.value("y", 0.0)};
        const double legacyScale = raw.value("scale", 2.2) * 14.4 / std::max(.01, molecule.referenceBondLength);
        if(version<5)legacyTransforms[molecule.id]={legacyOrigin,legacyScale};
        molecule.rotation = raw.value("rotation", 0.0);
        const double persistedScale = version >= 5 ? raw.value("scale", 1.0) : 1.0;
        molecule.scaleX = version >= 7 ? raw.value("scale_x", persistedScale) : persistedScale;
        molecule.scaleY = version >= 7 ? raw.value("scale_y", persistedScale) : persistedScale;
        molecule.alpha = raw.value("alpha", 255); molecule.layer = raw.value("layer", 0);
        molecule.visible=raw.value("visible",true); molecule.retired=raw.value("retired",false);
        if (const auto color = raw.find("color"); color != raw.end()) molecule.color = colorFromJson(*color, {255,255,255});
        for (const json& value : raw.value("atoms", json::array())) {
            Atom atom; atom.id = value.value("id", ""); atom.element = value.value("element", "C");
            atom.alias = value.value("label", value.value("alias", ""));
            atom.labelSide = atomLabelSideFromString(value.value("label_side", "right"));
            atom.numberStyle = atomNumberStyleFromString(value.value("number_style", "subscript"));
            atom.creationSerial = version >= 5 ? value.value("creation_serial", std::uint64_t{0}) : project.allocateCreationSerial();
            if (atom.creationSerial == 0) atom.creationSerial = project.allocateCreationSerial();
            project.nextCreationSerial = std::max(project.nextCreationSerial, atom.creationSerial + 1);
            atom.isotope = value.value("isotope", 0); atom.radicalElectrons = value.value("radical_electrons", 0);
            atom.implicitHydrogens = value.value("implicit_hydrogens", 0); atom.hidden = value.value("hidden", false);
            atom.alive = value.value("alive", true); atom.alpha = value.value("alpha", 255);
            if (const auto color = value.find("color"); color != value.end()) atom.color = colorFromJson(*color);
            Point stored{value.value("x", 0.0), value.value("y", 0.0)};
            atom.position = version >= 5 ? stored : Point{legacyOrigin.x + stored.x * legacyScale,
                                                          legacyOrigin.y + stored.y * legacyScale};
            molecule.nextAtomId = std::max(molecule.nextAtomId, numericSuffix(atom.id, 'A') + 1);
            const int legacyCharge = value.value("formal_charge", 0);
            molecule.atoms.push_back(std::move(atom));
            if (legacyCharge != 0) {
                const std::string text = std::abs(legacyCharge) == 1
                    ? (legacyCharge > 0 ? "⊕" : "⊖")
                    : std::to_string(std::abs(legacyCharge)) + (legacyCharge > 0 ? "⊕" : "⊖");
                const std::string adornmentId = "D" + std::to_string(molecule.nextAdornmentId++);
                molecule.adornments.push_back({adornmentId, project.allocateCreationSerial(), molecule.atoms.back().id,
                                                text, {18.0, 18.0}, {}, 255, true});
            }
        }
        for (const json& value : raw.value("bonds", json::array())) {
            Bond bond; bond.id = value.value("id", ""); bond.atomA = value.value("a", ""); bond.atomB = value.value("b", "");
            const std::string persistedType = value.value("type", "single");
            if (persistedType == "aromatic" || value.value("aromatic", false)) {
                bond.type = value.contains("display_type")
                    ? bondTypeFromString(value.value("display_type", "single"))
                    : ((numericSuffix(bond.id,'B') % 2) ? BondType::Double : BondType::Single);
            } else if (value.contains("type")) bond.type = bondTypeFromString(persistedType);
            else { const double order = value.value("order", 1.0); bond.type = order > 2.5 ? BondType::Triple : order > 1.5 ? BondType::Double : BondType::Single; }
            bond.secondaryLineSide = secondaryLineSideFromString(value.value("secondary_line_side", "center"));
            bond.stereo = bondStereoFromString(value.value("stereo", "none")); bond.visible = value.value("visible", true);
            bond.alive = value.value("alive", true); bond.alpha = value.value("alpha", 255);
            if (const auto color = value.find("color"); color != value.end()) bond.color = colorFromJson(*color);
            molecule.nextBondId = std::max(molecule.nextBondId, numericSuffix(bond.id, 'B') + 1); molecule.bonds.push_back(std::move(bond));
        }
        if (version >= 5) for (const json& value : raw.value("adornments", json::array())) {
            AtomAdornment adornment;
            adornment.id = value.value("id", ""); adornment.creationSerial = value.value("creation_serial", std::uint64_t{0});
            if (!adornment.creationSerial) adornment.creationSerial = project.allocateCreationSerial();
            project.nextCreationSerial = std::max(project.nextCreationSerial, adornment.creationSerial + 1);
            adornment.atomId = value.value("atom", ""); adornment.text = value.value("text", "⊕");
            adornment.offset = {value.value("x", 0.0), value.value("y", 0.0)};
            adornment.alpha = value.value("alpha", 255); adornment.alive = value.value("alive", true);
            if (const auto color = value.find("color"); color != value.end()) adornment.color = colorFromJson(*color);
            molecule.nextAdornmentId = std::max(molecule.nextAdornmentId, numericSuffix(adornment.id, 'D') + 1);
            molecule.adornments.push_back(std::move(adornment));
        }
        if (version < 5) molecule.referenceBondLength *= legacyScale;
        if (const auto poses = raw.find("poses"); poses != raw.end() && poses->is_object()) for (const auto& [id, value] : poses->items()) {
            Pose pose; pose.id = value.value("id", id);
            if (const auto positions = value.find("atoms"); positions != value.end()) for (const auto& [atomId, point] : positions->items()) {
                Point stored=pointFromJson(point);pose.atomPositions[atomId]=version>=5?stored:Point{legacyOrigin.x+stored.x*legacyScale,legacyOrigin.y+stored.y*legacyScale};
            }
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
        if(version<5)for(ScriptNode& node:project.nodes){
            if(node.type!="atom_set_xy"&&node.type!="atom_lerp_xy")continue;json params=json::parse(node.paramsJson);const auto transform=legacyTransforms.find(params.value("target",""));if(transform==legacyTransforms.end())continue;
            params["x"]=transform->second.first.x+params.value("x",0.0)*transform->second.second;
            params["y"]=transform->second.first.y+params.value("y",0.0)*transform->second.second;node.paramsJson=params.dump();
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
    // Resolve legacy project-wide member-ID collisions while the authoritative
    // v7 structures are still present on their owning molecules.  The v8
    // migration below moves those records into snapshots and clears the
    // identity objects, after which a structure-only scan would be too late.
    migrateProjectWideStableIds(project);
    if (version < 8) {
        // v7 and earlier stored a molecule's authoritative structure directly
        // on the object and used its earliest living atom as the transform
        // anchor.  v8 separates identity, local structure state and object
        // transform.  Convert once, preserving every stable member ID.
        for (Molecule& molecule : project.molecules) {
            Point anchor{};
            if (const Atom* atom = molecule.anchorAtom()) anchor = atom->position;
            molecule.origin = anchor;

            Molecule local = molecule;
            local.origin = {};
            local.rotation = 0.0;
            local.scaleX = local.scaleY = 1.0;
            local.alpha = 255;
            local.color = {255, 255, 255};
            local.layer = 0;
            local.visible = true;
            local.retired = false;
            for (Atom& atom : local.atoms) {
                atom.position.x -= anchor.x;
                atom.position.y -= anchor.y;
            }
            for (auto& [_, pose] : local.poses) for (auto& [__, point] : pose.atomPositions) {
                point.x -= anchor.x;
                point.y -= anchor.y;
            }

            const bool hasStructure = !local.atoms.empty() || !local.bonds.empty() ||
                                      !local.adornments.empty();
            if (hasStructure) {
                Project temporary;
                temporary.molecules = {local};
                temporary.nodes.clear();
                json snapshot = json::parse(toJson(temporary, 0))["molecules"][0];
                for (const char* key : {"source_smiles", "anchor", "rotation", "scale_x",
                                        "scale_y", "alpha", "color", "layer", "visible",
                                        "retired", "poses"}) snapshot.erase(key);
                const auto create = std::find_if(project.nodes.begin(), project.nodes.end(),
                    [&](const ScriptNode& node) {
                        if (node.type != "molecule_create") return false;
                        return json::parse(node.paramsJson).value("target", "") == molecule.id;
                    });
                const std::size_t index = create == project.nodes.end()
                    ? project.nodes.size()
                    : static_cast<std::size_t>(std::distance(project.nodes.begin(), create)) + 1;
                const std::string migrated = project.addNode(
                    "molecule_set_structure",
                    json({{"target", molecule.id}, {"coordinate_space", "molecule_local_v2"},
                          {"snapshot", std::move(snapshot)}, {"migrated_from_base", true}}).dump(),
                    index);
                (void)migrated;
            }

            // Existing structure-writing and member-coordinate nodes were
            // authored in the former world/anchor space.  Normalize their
            // stored coordinates to the same v8 local space.
            const auto localizeSnapshot = [&](json& snapshot) {
                if (!snapshot.is_object()) return;
                for (json& atom : snapshot.value("atoms", json::array())) {
                    atom["x"] = atom.value("x", 0.0) - anchor.x;
                    atom["y"] = atom.value("y", 0.0) - anchor.y;
                }
                snapshot.erase("anchor");
            };
            for (ScriptNode& node : project.nodes) {
                json params = json::parse(node.paramsJson);
                if (params.value("target", "") != molecule.id) continue;
                if (node.type == "molecule_set_structure") {
                    if (!params.value("migrated_from_base", false))
                        localizeSnapshot(params["snapshot"]);
                    params["coordinate_space"] = "molecule_local_v2";
                } else if (node.type == "molecule_gradient_structure") {
                    localizeSnapshot(params["start_snapshot"]);
                    localizeSnapshot(params["end_snapshot"]);
                    params["coordinate_space"] = "molecule_local_v2";
                } else if (node.type == "molecule_lerp_structure") {
                    if (auto atoms = params.find("atoms"); atoms != params.end() && atoms->is_object())
                        for (auto& [_, point] : atoms->items()) {
                            point["x"] = point.value("x", 0.0) - anchor.x;
                            point["y"] = point.value("y", 0.0) - anchor.y;
                        }
                } else if (node.type == "atom_set_xy" || node.type == "atom_lerp_xy") {
                    params["x"] = params.value("x", 0.0) - anchor.x;
                    params["y"] = params.value("y", 0.0) - anchor.y;
                }
                node.paramsJson = params.dump();
            }

            molecule.atoms.clear();
            molecule.bonds.clear();
            molecule.adornments.clear();
            molecule.poses.clear();
            molecule.sourceSmiles.clear();
        }
    }
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
