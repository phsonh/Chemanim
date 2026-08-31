#include "Editing.hpp"
#include "Depiction.hpp"
#include "Nodes.hpp"
#include "SketcherGeometry.hpp"
#include "Timeline.hpp"

#include <nlohmann/json.hpp>

#include <algorithm>
#include <array>
#include <cmath>
#include <numbers>
#include <stdexcept>

namespace chem::core {
namespace {
using json = nlohmann::json;
double distance(Point a, Point b) { return std::hypot(a.x - b.x, a.y - b.y); }
double pointSegmentDistance(Point point, Point first, Point second) {
    const double dx = second.x - first.x, dy = second.y - first.y;
    const double length2 = dx * dx + dy * dy;
    if (length2 < 1e-12) return distance(point, first);
    const double t = std::clamp(((point.x - first.x) * dx + (point.y - first.y) * dy) / length2, 0.0, 1.0);
    return distance(point, {first.x + t * dx, first.y + t * dy});
}
bool isBondTool(Tool tool) {
    return tool == Tool::SingleBond || tool == Tool::DoubleBond || tool == Tool::TripleBond ||
           tool == Tool::SolidWedge || tool == Tool::DashedWedge ||
           tool == Tool::SolidBar || tool == Tool::HashedBar || tool == Tool::WavyBond;
}
bool isRingTool(Tool tool) { return tool >= Tool::Ring3 && tool <= Tool::Benzene; }
bool isStructureWriteTool(Tool tool) {
    return isBondTool(tool) || isRingTool(tool) || tool == Tool::Eraser ||
           tool == Tool::AtomLabel || tool == Tool::AtomText ||
           tool == Tool::ChargePositive || tool == Tool::ChargeNegative;
}
int ringSize(Tool tool) { return tool == Tool::Benzene ? 6 : 3 + static_cast<int>(tool) - static_cast<int>(Tool::Ring3); }
std::pair<BondType, BondStereo> bondStyle(Tool tool) {
    switch (tool) {
        case Tool::DoubleBond: return {BondType::Double, BondStereo::None};
        case Tool::TripleBond: return {BondType::Triple, BondStereo::None};
        case Tool::SolidWedge: return {BondType::Single, BondStereo::SolidWedge};
        case Tool::DashedWedge: return {BondType::Single, BondStereo::DashedWedge};
        case Tool::SolidBar: return {BondType::Single, BondStereo::SolidBar};
        case Tool::HashedBar: return {BondType::Single, BondStereo::HashedBar};
        case Tool::WavyBond: return {BondType::Single, BondStereo::Wavy};
        default: return {BondType::Single, BondStereo::None};
    }
}
Point snappedDirection(Point start, Point raw, double length, bool disableAngle) {
    if (disableAngle) return raw;
    return sketcher_geometry::roundedDirection(start, raw, length, 24);
}
Point snappedDirectionFromBaseline(Point start, Point raw, double length,
                                   Point baseline, bool disableAngle) {
    const double rawLength = std::hypot(raw.x - start.x, raw.y - start.y);
    if (rawLength <= 1e-9) return {start.x + baseline.x, start.y + baseline.y};
    if (disableAngle) return {start.x + (raw.x - start.x) * length / rawLength,
                              start.y + (raw.y - start.y) * length / rawLength};
    constexpr double increment = 2.0 * std::numbers::pi / 24.0;
    const double baseAngle = std::atan2(baseline.y, baseline.x);
    const double rawAngle = std::atan2(raw.y - start.y, raw.x - start.x);
    const double angle = baseAngle + std::round((rawAngle - baseAngle) / increment) * increment;
    return {start.x + length * std::cos(angle), start.y + length * std::sin(angle)};
}
std::array<Point,4> arrowCurveFromEndpoints(Point start,Point end,double bendLevel) {
    const Point delta{end.x-start.x,end.y-start.y};
    const double length=std::max(1e-9,std::hypot(delta.x,delta.y));
    const Point normal{-delta.y/length,delta.x/length};
    const double bend=std::clamp(length*0.18,18.0,70.0)*bendLevel;
    return {start,
            Point{start.x+delta.x/3.0+normal.x*bend,start.y+delta.y/3.0+normal.y*bend},
            Point{start.x+delta.x*2.0/3.0+normal.x*bend,start.y+delta.y*2.0/3.0+normal.y*bend},
            end};
}
std::vector<Point> neighborOffsets(const Molecule& molecule, const Atom& atom) {
    std::vector<Point> result;
    for (const Bond& bond : molecule.bonds) {
        if (!bond.alive) continue;
        const std::string* otherId = nullptr;
        if (bond.atomA == atom.id) otherId = &bond.atomB;
        else if (bond.atomB == atom.id) otherId = &bond.atomA;
        if (otherId) if (const Atom* other = molecule.atom(*otherId); other && other->alive) {
            result.push_back({other->position.x - atom.position.x, other->position.y - atom.position.y});
        }
    }
    return result;
}
bool pointInPolygon(Point point, const std::vector<Point>& polygon) {
    bool inside = false;
    for (std::size_t i = 0, j = polygon.size() - 1; i < polygon.size(); j = i++) {
        const Point a = polygon[i], b = polygon[j];
        if (((a.y > point.y) != (b.y > point.y)) &&
            point.x < (b.x - a.x) * (point.y - a.y) / ((b.y - a.y) + 1e-15) + a.x) inside = !inside;
    }
    return inside;
}
json moleculeSnapshotJson(const Molecule& molecule) {
    Project temporary;temporary.molecules={molecule};temporary.nodes.clear();
    json snapshot=json::parse(toJson(temporary))["molecules"][0];
    // A structure snapshot is deliberately not a serialized render object.
    // Keep stable structure data and allocation counters only; object and
    // scene transforms are evaluated later by the normal animation layer.
    for(const char* key:{"source_smiles","anchor","rotation","scale_x","scale_y","alpha","color",
                         "layer","visible","retired","poses"})snapshot.erase(key);
    return snapshot;
}
std::optional<Molecule> moleculeFromSnapshotJson(const json& snapshot) {
    if(!snapshot.is_object()||!snapshot.contains("atoms"))return std::nullopt;
    try{json wrapper={{"format","chemanim-native-2d"},{"version",8},{"molecules",json::array({snapshot})},{"nodes",json::array()}};Project loaded=fromJson(wrapper.dump());if(!loaded.molecules.empty())return loaded.molecules.front();}catch(...){}
    return std::nullopt;
}
std::optional<Molecule> structureBeforeNode(const Project& project,std::size_t index,const std::string& target,int* startFrame=nullptr) {
    Project prefix=project;index=std::min(index,prefix.nodes.size());prefix.nodes.resize(index);int cursor=0;
    for(const ScriptNode& node:prefix.nodes)if(node.enabled&&node.type=="wait"){try{cursor+=std::max(0,json::parse(node.paramsJson).value("frames",30));}catch(...){}}
    if(startFrame)*startFrame=cursor;const EvaluatedScene scene=evaluateStructureNodes(prefix,cursor);const auto found=scene.molecules.find(target);
    if(found==scene.molecules.end()||found->second.retired||!found->second.visible)return std::nullopt;return found->second;
}
}  // namespace

Point Viewport::modelToCanvas(Point value) const {
    return {width * 0.5 + (value.x - center.x) * pixelsPerUnit,
            height * 0.5 - (value.y - center.y) * pixelsPerUnit};
}
Point Viewport::canvasToModel(Point value) const {
    return {center.x + (value.x - width * 0.5) / pixelsPerUnit,
            center.y - (value.y - height * 0.5) / pixelsPerUnit};
}

struct EditorSession::Impl {
    Project project;
    std::string activeMolecule;
    Tool tool = Tool::SelectRectangle;
    std::string element = "C";
    Viewport viewport;
    std::set<std::string> selectedAtoms;
    std::set<std::string> selectedBonds;
    EditTargetKind targetKind = EditTargetKind::TimelinePreview;
    std::string targetId;
    int previewFrame = 0;
    std::optional<Molecule> structureDraft;
    enum class SnapshotDomain { Structure, Authoring };
    struct Snapshot { Project before; Project after; SnapshotDomain domain; };
    std::vector<Snapshot> undo;
    std::vector<Snapshot> redo;
    struct Gesture {
        Project before;
        Point pressCanvas;
        Point pressModel;
        Point startCanvas;
        Point currentCanvas;
        Point startModel;
        Hit startHit;
        std::map<std::string, Point> original;
        std::vector<Point> lasso;
        std::map<std::string, Point> targetPositions;
        std::map<std::string, Point> targetAdornmentOffsets;
        std::map<std::string, Point> originalAdornments;
        std::set<std::string> erasedAtoms;
        std::set<std::string> erasedBonds;
        std::string previewText;
        GesturePreviewKind previewKind = GesturePreviewKind::None;
        double bendLevel = 1.0;
        bool changed = false;
    };
    std::optional<Gesture> gesture;

    void markGradientNodesForReview(std::size_t afterIndex=0,const std::string& moleculeId={}) {
        for(std::size_t index=afterIndex;index<project.nodes.size();++index){ScriptNode& node=project.nodes[index];if(node.type!="molecule_gradient_structure")continue;json params=json::parse(node.paramsJson);if(!moleculeId.empty()&&params.value("target","")!=moleculeId)continue;params["needs_review"]=true;node.paramsJson=params.dump();}
    }

    Molecule* molecule() { return project.molecule(activeMolecule); }
    const Molecule* molecule() const { return project.molecule(activeMolecule); }
    Molecule* editableMolecule() { return targetKind==EditTargetKind::StructureSnapshot&&structureDraft?&*structureDraft:molecule(); }
    const Molecule* editableMolecule() const { return targetKind==EditTargetKind::StructureSnapshot&&structureDraft?&*structureDraft:molecule(); }

    void flushStructureDraft() {
        if(targetKind==EditTargetKind::BaseStructure){markGradientNodesForReview(0,activeMolecule);return;}
        if(targetKind!=EditTargetKind::StructureSnapshot||!structureDraft)return;
        ScriptNode* node=project.node(targetId);if(!node)return;
        if(Molecule* identity=project.molecule(activeMolecule)){
            identity->nextAtomId=std::max(identity->nextAtomId,structureDraft->nextAtomId);
            identity->nextBondId=std::max(identity->nextBondId,structureDraft->nextBondId);
            identity->nextAdornmentId=std::max(identity->nextAdornmentId,structureDraft->nextAdornmentId);
        }
        json params=json::parse(node->paramsJson);params[node->type=="molecule_gradient_structure"?"end_snapshot":"snapshot"]=moleculeSnapshotJson(*structureDraft);node->paramsJson=params.dump();
    }

    void loadStructureDraft(const ScriptNode& node) {
        const json params=json::parse(node.paramsJson);const auto snapshot=params.find(node.type=="molecule_gradient_structure"?"end_snapshot":"snapshot");
        if(node.type=="molecule_gradient_structure"&&params.value("coordinate_space","")!="molecule_local_v2"){
            structureDraft.reset();return;
        }
        if(snapshot!=params.end()&&snapshot->is_object()&&snapshot->contains("id")&&snapshot->contains("atoms")){
            json wrapper={{"format","chemanim-native-2d"},{"version",8},{"molecules",json::array({*snapshot})},{"nodes",json::array()}};
            Project loaded=fromJson(wrapper.dump());if(!loaded.molecules.empty()){structureDraft=std::move(loaded.molecules.front());return;}
        }
        structureDraft=evaluateMolecule(project,activeMolecule,previewFrame);
    }

    bool validStructureContext() const {
        if ((targetKind != EditTargetKind::BaseStructure&&targetKind!=EditTargetKind::StructureSnapshot) || targetId.empty()) return false;
        const ScriptNode* node = project.node(targetId);
        if (!node || !node->enabled) return false;
        try {
            const json params = json::parse(node->paramsJson);
            const std::string target = params.value("target", "");
            const std::string capability=nodeMetadata(node->type).structureEditCapability;
            const bool kindMatches=(targetKind==EditTargetKind::BaseStructure&&capability=="base")||(targetKind==EditTargetKind::StructureSnapshot&&capability=="snapshot"&&structureDraft.has_value());
            return kindMatches&&target == activeMolecule && project.molecule(target) != nullptr;
        } catch (...) {
            return false;
        }
    }

    bool validScriptManipulationContext() const {
        if (targetKind == EditTargetKind::AtomTween || targetKind == EditTargetKind::Pose) return true;
        if (targetKind != EditTargetKind::ScriptNode) return false;
        const ScriptNode* node = project.node(targetId);
        if (!node || !node->enabled) return false;
        const std::string capability=nodeMetadata(node->type).directManipulationCapability;
        if(!capability.empty())return true;
        static const std::set<std::string> legacySupported{"atom_set_xy","atom_lerp_xy","adornment_set_offset","adornment_lerp_offset"};
        return legacySupported.contains(node->type);
    }

    void normalizeContext() {
        if (!project.molecule(activeMolecule))
            activeMolecule = project.molecules.empty() ? "" : project.molecules.front().id;
        bool valid = targetKind == EditTargetKind::TimelinePreview;
        if (targetKind == EditTargetKind::BaseStructure||targetKind==EditTargetKind::StructureSnapshot) valid = validStructureContext();
        else if (targetKind == EditTargetKind::ScriptNode)
            valid = project.node(targetId) != nullptr;
        else if (targetKind == EditTargetKind::AtomTween)
            valid = std::any_of(project.atomTweens.begin(),project.atomTweens.end(),
                [&](const AtomTween& value){return value.id==targetId;});
        else if (targetKind == EditTargetKind::Pose)
            valid = molecule() && molecule()->poses.contains(targetId);
        if (!valid) {
            if(!project.nodes.empty()){targetKind=EditTargetKind::ScriptNode;targetId=project.nodes.front().id;}
            else{targetKind=EditTargetKind::TimelinePreview;targetId.clear();}
            tool=Tool::SelectRectangle;structureDraft.reset();
            gesture.reset();selectedAtoms.clear();selectedBonds.clear();
        }
    }

    Molecule displayed() const {
        Molecule result = validStructureContext() ? *editableMolecule() : evaluateMolecule(project, activeMolecule, previewFrame);
        if (validStructureContext()) {
            const EvaluatedScene scene=evaluateNodes(project,previewFrame);
            if(const auto found=scene.molecules.find(activeMolecule);found!=scene.molecules.end()){
                const Molecule& visual=found->second;const double radians=visual.rotation*std::numbers::pi/180.0;
                const double c=std::cos(radians),s=std::sin(radians);
                for(Atom& atom:result.atoms){const double x=atom.position.x*visual.scaleX,y=atom.position.y*visual.scaleY;atom.position={visual.origin.x+x*c-y*s,visual.origin.y+x*s+y*c};}
                result.origin=visual.origin;result.scaleX=visual.scaleX;result.scaleY=visual.scaleY;result.rotation=visual.rotation;
                result.alpha=visual.alpha;result.color=visual.color;result.layer=visual.layer;
            }
        }
        if (gesture && targetKind != EditTargetKind::BaseStructure && targetKind != EditTargetKind::StructureSnapshot && targetKind != EditTargetKind::TimelinePreview) {
            const ScriptNode* node=targetKind==EditTargetKind::ScriptNode?project.node(targetId):nullptr;
            const bool objectPosition=node&&(node->type=="molecule_set_position"||node->type=="molecule_lerp_position"||node->type=="molecule_set_x"||node->type=="molecule_lerp_x"||node->type=="molecule_set_y"||node->type=="molecule_lerp_y");
            if(!objectPosition)for (const auto& [id, position] : gesture->targetPositions) if (Atom* atom = result.atom(id)) atom->position = position;
            for (const auto& [id, offset] : gesture->targetAdornmentOffsets) if (AtomAdornment* value=result.adornment(id)) value->offset=offset;
        }
        return result;
    }

    struct EditTransform { Point origin{}; double scaleX=1.0,scaleY=1.0,rotation=0.0; };
    EditTransform editTransform() const {
        if(!validStructureContext())return {};
        const EvaluatedScene scene=evaluateNodes(project,previewFrame);
        if(const auto found=scene.molecules.find(activeMolecule);found!=scene.molecules.end())
            return {found->second.origin,found->second.scaleX,found->second.scaleY,found->second.rotation};
        return {};
    }
    Point localToWorld(Point value) const {
        if(!validStructureContext())return value;const EditTransform transform=editTransform();
        const double radians=transform.rotation*std::numbers::pi/180.0,c=std::cos(radians),s=std::sin(radians);
        const double x=value.x*transform.scaleX,y=value.y*transform.scaleY;
        return {transform.origin.x+x*c-y*s,transform.origin.y+x*s+y*c};
    }
    Point worldToLocal(Point value) const {
        if(!validStructureContext())return value;const EditTransform transform=editTransform();
        const double radians=-transform.rotation*std::numbers::pi/180.0,c=std::cos(radians),s=std::sin(radians);
        const double dx=value.x-transform.origin.x,dy=value.y-transform.origin.y;
        const double x=dx*c-dy*s,y=dx*s+dy*c;
        return {std::abs(transform.scaleX)>1e-12?x/transform.scaleX:0.0,
                std::abs(transform.scaleY)>1e-12?y/transform.scaleY:0.0};
    }
    Point canvasToEdit(Point value) const {return worldToLocal(viewport.canvasToModel(value));}
    Point editToCanvas(Point value) const {return viewport.modelToCanvas(localToWorld(value));}

    std::optional<ArrowState> displayedArrow(const Project& source,const ScriptNode& node) const {
        const std::string target=json::parse(node.paramsJson).value("target","");
        const EvaluatedScene scene=evaluateNodes(source,previewFrame);
        const auto found=scene.arrows.find(target);if(found==scene.arrows.end())return std::nullopt;
        return found->second;
    }

    Hit hit(Point canvasPoint, std::optional<std::string> ignoreAtom = std::nullopt) const {
        if(targetKind==EditTargetKind::ScriptNode){const ScriptNode* node=project.node(targetId);if(node&&node->type=="arrow_set_curve"){
            const json params=json::parse(node->paramsJson);
            if(!params.value("initialized",true))return {};
            const auto shown=displayedArrow(project,*node);if(!shown)return {};
            const std::array<std::pair<const char*,Point>,4> controls{{
                {"p0",{shown->position.x+shown->start.x,shown->position.y+shown->start.y}},
                {"c1",{shown->position.x+shown->control1.x,shown->position.y+shown->control1.y}},
                {"c2",{shown->position.x+shown->control2.x,shown->position.y+shown->control2.y}},
                {"p3",{shown->position.x+shown->end.x,shown->position.y+shown->end.y}}}};
            Hit control;control.distance=1e9;for(const auto& [id,position]:controls){const double d=distance(canvasPoint,viewport.modelToCanvas(position));if(d<=12.0&&d<control.distance)control={HitKind::Control,id,d};}if(control.kind==HitKind::Control)return control;
        }}
        if (!molecule()) return {};
        const Molecule displayedMolecule = displayed(); const Molecule* value = &displayedMolecule;
        Hit best;
        best.distance = 1e9;
        for (const Atom& atom : value->atoms) {
            if (!atom.alive) continue;
            if (ignoreAtom && atom.id == *ignoreAtom) continue;
            const double d = distance(canvasPoint, viewport.modelToCanvas(atom.position));
            if (d <= 14.0 && d < best.distance) best = {HitKind::Atom, atom.id, d};
        }
        if (best.kind == HitKind::Atom) return best;
        for (const AtomAdornment& adornment : value->adornments) {
            const Atom* atom = value->atom(adornment.atomId);
            if (!adornment.alive || !atom || !atom->alive) continue;
            const Point point{atom->position.x + adornment.offset.x, atom->position.y + adornment.offset.y};
            const double d = distance(canvasPoint, viewport.modelToCanvas(point));
            if (d <= 14.0 && d < best.distance) best = {HitKind::Adornment, adornment.id, d};
        }
        if (best.kind == HitKind::Adornment) return best;
        for (const Bond& bond : value->bonds) {
            if (!bond.alive || !bond.visible) continue;
            const Atom* a = value->atom(bond.atomA); const Atom* b = value->atom(bond.atomB);
            if (!a || !b) continue;
            const Point first=viewport.modelToCanvas(a->position),second=viewport.modelToCanvas(b->position);
            const double dx=second.x-first.x,dy=second.y-first.y;
            const double magnitude=std::max(1e-9,std::hypot(dx,dy));
            const Point normal{-dy/magnitude,dx/magnitude};
            const double spacing=project.style.doubleBondSpacing*value->referenceBondLength*viewport.pixelsPerUnit;
            const auto strokeDistance=[&](double offset){
                const Point delta{normal.x*offset,normal.y*offset};
                return pointSegmentDistance(canvasPoint,{first.x+delta.x,first.y+delta.y},
                                             {second.x+delta.x,second.y+delta.y});
            };
            double d=strokeDistance(0.0);
            if(bond.type==BondType::Triple)d=std::min({d,strokeDistance(-spacing),strokeDistance(spacing)});
            else if(bond.type==BondType::Double){
                if(bond.secondaryLineSide==SecondaryLineSide::Center){
                    const Point tangent{dx/magnitude,dy/magnitude};
                    const auto extension=[&](const Atom* atom,bool firstEndpoint,double sign){
                        double bestExtension=0.0;
                        for(const Bond& candidate:value->bonds){
                            if(candidate.id==bond.id||!candidate.alive||!candidate.visible||
                               (candidate.atomA!=atom->id&&candidate.atomB!=atom->id))continue;
                            const Atom* neighbour=value->atom(candidate.atomA==atom->id?candidate.atomB:candidate.atomA);
                            if(!neighbour||!neighbour->alive)continue;
                            const Point neighbourPoint=viewport.modelToCanvas(neighbour->position);
                            const Point atomPoint=viewport.modelToCanvas(atom->position);
                            const double ux=neighbourPoint.x-atomPoint.x,uy=neighbourPoint.y-atomPoint.y;
                            const double neighbourLength=std::hypot(ux,uy);if(neighbourLength<1e-9)continue;
                            const double un=(ux*normal.x+uy*normal.y)/neighbourLength;
                            const double ut=(ux*tangent.x+uy*tangent.y)/neighbourLength;
                            if(std::abs(un)<1e-6)continue;
                            const double ray=sign*spacing*.5/un;
                            if(ray<=0.0||ray>magnitude*.35)continue;const double candidateExtension=ray*ut;
                            if((firstEndpoint&&candidateExtension>=-1e-6)||
                               (!firstEndpoint&&candidateExtension<=1e-6))continue;
                            if(bestExtension==0.0||std::abs(candidateExtension)<std::abs(bestExtension))
                                bestExtension=candidateExtension;
                        }
                        return std::clamp(bestExtension,-magnitude*.25,magnitude*.25);
                    };
                    for(double sign:{-1.0,1.0}){
                        const Point offset{normal.x*spacing*.5*sign,normal.y*spacing*.5*sign};
                        const double firstExtension=extension(a,true,sign);
                        const double secondExtension=extension(b,false,sign);
                        d=std::min(d,pointSegmentDistance(canvasPoint,
                            {first.x+offset.x+tangent.x*firstExtension,
                             first.y+offset.y+tangent.y*firstExtension},
                            {second.x+offset.x+tangent.x*secondExtension,
                             second.y+offset.y+tangent.y*secondExtension}));
                    }
                }else{
                    // Model-space Left becomes the negative normal after the
                    // canvas Y axis is inverted.
                    const double sign=bond.secondaryLineSide==SecondaryLineSide::Left?-1.0:1.0;
                    d=std::min(d,strokeDistance(spacing*sign));
                }
            }
            if (d <= 9.0 && d < best.distance) best = {HitKind::Bond, bond.id, d};
        }
        if (best.kind == HitKind::Bond) return best;
        if(targetKind==EditTargetKind::ScriptNode){const ScriptNode* node=project.node(targetId);if(node&&nodeMetadata(node->type).directManipulationCapability=="molecule_translate"){
            bool any=false;double left=1e100,right=-1e100,top=1e100,bottom=-1e100;for(const Atom& atom:value->atoms)if(atom.alive){const Point p=viewport.modelToCanvas(atom.position);any=true;left=std::min(left,p.x);right=std::max(right,p.x);top=std::min(top,p.y);bottom=std::max(bottom,p.y);}if(any&&canvasPoint.x>=left-14&&canvasPoint.x<=right+14&&canvasPoint.y>=top-14&&canvasPoint.y<=bottom+14)return {HitKind::Molecule,value->id,0.0};
        }}
        if (best.distance == 1e9) best.distance = 0.0;
        return best;
    }

    EditResult result(Point canvasPoint) const {
        EditResult value;
        value.hover = hit(canvasPoint);
        value.selectedAtoms.assign(selectedAtoms.begin(), selectedAtoms.end());
        value.selectedBonds.assign(selectedBonds.begin(), selectedBonds.end());
        if (gesture) {
            value.preview.active = true;
            value.preview.kind = gesture->previewKind;
            value.preview.start = gesture->startCanvas;
            value.preview.current = gesture->currentCanvas;
            value.preview.polygon = gesture->lasso;
            value.preview.text = gesture->previewText;
            const Hit snap = hit(gesture->currentCanvas, gesture->startHit.kind == HitKind::Atom ? std::optional(gesture->startHit.id) : std::nullopt);
            if (snap.kind == HitKind::Atom) value.preview.snapAtomId = snap.id;
        }
        return value;
    }

    Point gestureEndpoint(bool alt) const {
        if (!gesture) return {};
        const Molecule* value = editableMolecule();
        const double length = value ? value->referenceBondLength : 1.5;
        const bool click=distance(gesture->pressCanvas,gesture->currentCanvas)<=12.0;
        if (gesture->startHit.kind==HitKind::None && click) {
            constexpr double defaultAngle=std::numbers::pi/6.0;
            return {gesture->startModel.x+length*std::cos(defaultAngle),
                    gesture->startModel.y+length*std::sin(defaultAngle)};
        }
        if (value && gesture->startHit.kind == HitKind::Atom && click) {
            if (const Atom* atom = value->atom(gesture->startHit.id)) {
                const std::vector<Point> neighbours=neighborOffsets(*value,*atom);
                const Point offset = neighbours.empty()
                    ? Point{length*std::cos(std::numbers::pi/6.0),length*std::sin(std::numbers::pi/6.0)}
                    : sketcher_geometry::bestPlacementAroundOrigin(neighbours, length);
                return {atom->position.x + offset.x, atom->position.y + offset.y};
            }
        }
        const Hit near = hit(gesture->currentCanvas, gesture->startHit.kind == HitKind::Atom ? std::optional(gesture->startHit.id) : std::nullopt);
        if (near.kind == HitKind::Atom && value) return value->atom(near.id)->position;
        const Point candidate = snappedDirection(
            gesture->startModel, canvasToEdit(gesture->currentCanvas), length, alt);
        // Endpoint atom snapping wins over angular snapping, including when the
        // rounded endpoint (rather than the raw cursor) lands on an atom.
        const Hit snappedHit = hit(editToCanvas(candidate),
                                   gesture->startHit.kind == HitKind::Atom
                                       ? std::optional(gesture->startHit.id)
                                       : std::nullopt);
        if (snappedHit.kind == HitKind::Atom && value) return value->atom(snappedHit.id)->position;
        return candidate;
    }

    Point adornmentEndpoint(bool alt) const {
        if (!gesture || gesture->startHit.kind != HitKind::Atom || !editableMolecule()) return {};
        const Atom* atom = editableMolecule()->atom(gesture->startHit.id);
        if (!atom) return {};
        // Formal-charge placement is a single, predictable document-space
        // radius.  At 100% editor zoom this is exactly 20 screen pixels.
        constexpr double length = 20.0;
        if (distance(gesture->pressCanvas, gesture->currentCanvas) <= 12.0) {
            const Point offset = sketcher_geometry::bestPlacementAroundOrigin(
                neighborOffsets(*editableMolecule(), *atom), length);
            return {atom->position.x + offset.x, atom->position.y + offset.y};
        }
        return snappedDirection(atom->position, canvasToEdit(gesture->currentCanvas),
                                length, alt);
    }

    AtomLabelSide textSide() const {
        if (!gesture || gesture->startHit.kind != HitKind::Atom || !editableMolecule())
            return AtomLabelSide::Right;
        const Atom* atom = editableMolecule()->atom(gesture->startHit.id);
        if (!atom) return AtomLabelSide::Right;
        if (distance(gesture->pressCanvas, gesture->currentCanvas) > 12.0) {
            return canvasToEdit(gesture->currentCanvas).x < atom->position.x
                ? AtomLabelSide::Left : AtomLabelSide::Right;
        }
        const std::vector<Point> neighbours = neighborOffsets(*editableMolecule(), *atom);
        if (neighbours.empty()) return AtomLabelSide::Right;
        // A label has only two legal layouts. Score both horizontal
        // directions against every adjacent bond and use the side with the
        // larger minimum angular clearance. This matters for degree-two and
        // higher vertices: reducing a general largest-sector direction to
        // its x sign can choose the crowded side. Exact ties deliberately
        // prefer the conventional right-hand layout.
        const auto angularClearance = [&](double candidateAngle) {
            double clearance = std::numbers::pi;
            for (const Point& neighbour : neighbours) {
                const double neighbourAngle = std::atan2(neighbour.y, neighbour.x);
                const double separation = std::remainder(
                    candidateAngle - neighbourAngle, 2.0 * std::numbers::pi);
                clearance = std::min(clearance, std::abs(separation));
            }
            return clearance;
        };
        const double right = angularClearance(0.0);
        const double left = angularClearance(std::numbers::pi);
        return left > right + 1e-9 ? AtomLabelSide::Left : AtomLabelSide::Right;
    }

    Point textEndpoint() const {
        if (!gesture || gesture->startHit.kind != HitKind::Atom || !editableMolecule()) return {};
        const Atom* atom = editableMolecule()->atom(gesture->startHit.id);
        if (!atom) return {};
        const double direction = textSide() == AtomLabelSide::Left ? -1.0 : 1.0;
        return {atom->position.x + direction * editableMolecule()->referenceBondLength * .55,
                atom->position.y};
    }

    std::vector<Point> ringPolygon(int count, Point cursor, bool disableAngle = false) const {
        const Molecule* value = editableMolecule();
        if (!value || !gesture) return {};
        const double side = value->referenceBondLength;
        double radius = side / (2.0 * std::sin(std::numbers::pi / count));
        std::vector<Point> result;
        if (gesture->startHit.kind == HitKind::Bond) {
            const Bond* bond = value->bond(gesture->startHit.id); const Atom* a = bond ? value->atom(bond->atomA) : nullptr; const Atom* b = bond ? value->atom(bond->atomB) : nullptr;
            if (!a || !b) return {};
            const Point mid{(a->position.x + b->position.x) * .5, (a->position.y + b->position.y) * .5};
            const Point delta{b->position.x - a->position.x, b->position.y - a->position.y};
            const double actual = std::max(1e-9, std::hypot(delta.x, delta.y));
            // The shared bond is one exact side of the new polygon.  Derive
            // both radius and apothem from its real length; using the template
            // bond length here creates a distorted ring when the existing
            // structure was freely edited.
            radius = actual / (2.0 * std::sin(std::numbers::pi / count));
            const Point normal{-delta.y / actual, delta.x / actual};
            const double apothem = actual * .5 / std::tan(std::numbers::pi / count);
            const Point modelCursor = canvasToEdit(cursor);
            double sign = ((modelCursor.x - mid.x) * normal.x + (modelCursor.y - mid.y) * normal.y) >= 0 ? 1.0 : -1.0;
            if (distance(gesture->pressCanvas, cursor) <= 12.0) {
                // Adapted from Sketcher's fragment ring-flip choice: for a
                // click, place the new fragment on the emptier side of the
                // shared bond. A real drag still selects the indicated side.
                const auto clearance = [&](double candidateSign) {
                    const Point candidateCenter{mid.x + normal.x * apothem * candidateSign,
                                                mid.y + normal.y * apothem * candidateSign};
                    double nearest = 1e100;
                    for (const Atom& atom : value->atoms) {
                        if (!atom.alive) continue;
                        if (atom.id == a->id || atom.id == b->id) continue;
                        nearest = std::min(nearest, distance(candidateCenter, atom.position));
                    }
                    return nearest;
                };
                const double positive = clearance(1.0), negative = clearance(-1.0);
                if (std::abs(positive - negative) > 1e-9) sign = positive > negative ? 1.0 : -1.0;
                else sign = normal.x >= 0.0 ? 1.0 : -1.0;
            }
            const Point center{mid.x + normal.x * apothem * sign, mid.y + normal.y * apothem * sign};
            double startAngle = std::atan2(a->position.y - center.y, a->position.x - center.x);
            // With the center on the positive normal side, B is the next
            // counter-clockwise vertex after A.  Reversing this sign and then
            // forcibly replacing vertex 1 with B produced the crossing,
            // collapsed fused rings seen in the editor.
            const double direction = sign > 0 ? 1.0 : -1.0;
            for (int i = 0; i < count; ++i) result.push_back({center.x + radius * std::cos(startAngle + direction * i * 2 * std::numbers::pi / count), center.y + radius * std::sin(startAngle + direction * i * 2 * std::numbers::pi / count)});
            result[0] = a->position; result[1] = b->position;
            return result;
        }
        Point vertex = gesture->startModel;
        if (gesture->startHit.kind == HitKind::Atom) vertex = value->atom(gesture->startHit.id)->position;
        Point centerDirection;
        // A free ring defaults to a vertex-up/down orientation rather than a
        // flat top.  Dragging still rotates the entire template with the
        // ring-specific 15-degree bisector snapping rule.
        Point baseline{0.0, radius};
        if (gesture->startHit.kind == HitKind::Atom) {
            const Atom* atom = value->atom(gesture->startHit.id);
            const std::vector<Point> neighbours=neighborOffsets(*value,*atom);
            if(!neighbours.empty())baseline=sketcher_geometry::bestPlacementAroundOrigin(
                neighbours, radius, false);
        }
        if (gesture->startHit.kind == HitKind::Atom && distance(gesture->pressCanvas, cursor) <= 12.0) {
            // A ring attached through one atom is a whole geometric template,
            // not one newly placed bond.  Its centre must lie on the bisector
            // of the largest empty sector so the two new bonds adjacent to
            // the shared atom are mirror images.  In particular, a terminal
            // atom's ring centre is exactly opposite its existing bond.  The
            // 120-degree single-neighbour limit is useful for the bond tool,
            // but applying it here visibly pushes a spiro ring to one side.
            centerDirection = baseline;
        } else {
            const Point raw = canvasToEdit(cursor);
            const Point center = snappedDirectionFromBaseline(
                vertex, raw, radius, baseline, disableAngle);
            centerDirection = {center.x - vertex.x, center.y - vertex.y};
        }
        Point center{vertex.x + centerDirection.x, vertex.y + centerDirection.y};
        const double startAngle = std::atan2(vertex.y - center.y, vertex.x - center.x);
        for (int i = 0; i < count; ++i) result.push_back({center.x + radius * std::cos(startAngle + i * 2 * std::numbers::pi / count), center.y + radius * std::sin(startAngle + i * 2 * std::numbers::pi / count)});
        result[0] = vertex;
        return result;
    }

    void commit() {
        if (!gesture) return;
        if (!gesture->changed) {
            // A failed compound gesture must be atomic.  In particular, bond
            // creation used to leave its first atom behind when endpoint
            // resolution failed, while reporting no change and therefore
            // providing no way to undo back to an empty canvas.
            const auto high = project.nextCreationSerial;
            project = std::move(gesture->before);
            project.nextCreationSerial = std::max(project.nextCreationSerial, high);
            gesture.reset();
            return;
        }
        flushStructureDraft();
        undo.push_back({std::move(gesture->before), project,
                        (targetKind == EditTargetKind::BaseStructure||targetKind==EditTargetKind::StructureSnapshot)
                            ? SnapshotDomain::Structure : SnapshotDomain::Authoring});
        redo.clear();
        gesture.reset();
    }
};

EditorSession::EditorSession(Project project) : impl_(std::make_unique<Impl>()) { impl_->project = std::move(project); impl_->project.ensureDefaultNodes(); if (!impl_->project.molecules.empty()) impl_->activeMolecule = impl_->project.molecules.front().id; }
EditorSession::~EditorSession() = default;
EditorSession::EditorSession(EditorSession&&) noexcept = default;
EditorSession& EditorSession::operator=(EditorSession&&) noexcept = default;
Project& EditorSession::project() { return impl_->project; }
const Project& EditorSession::project() const { return impl_->project; }
void EditorSession::replaceProject(Project project) { impl_ = std::make_unique<Impl>(); impl_->project = std::move(project); impl_->project.ensureDefaultNodes(); if (!impl_->project.molecules.empty()) impl_->activeMolecule = impl_->project.molecules.front().id; }
void EditorSession::setActiveMolecule(const std::string& stableId) { if (!impl_->project.molecule(stableId)) throw std::runtime_error("Unknown molecule: " + stableId); impl_->activeMolecule = stableId; impl_->selectedAtoms.clear(); impl_->selectedBonds.clear(); }
std::string EditorSession::activeMoleculeId() const { return impl_->activeMolecule; }
void EditorSession::setTool(Tool tool) {
    impl_->tool = tool;
    impl_->gesture.reset();
    if (tool != Tool::SelectRectangle && tool != Tool::SelectLasso && tool != Tool::Move) {
        impl_->selectedAtoms.clear();
        impl_->selectedBonds.clear();
    }
}
Tool EditorSession::tool() const { return impl_->tool; }
void EditorSession::setElement(std::string element) { impl_->element = std::move(element); }
std::string EditorSession::element() const { return impl_->element; }
void EditorSession::setViewport(Viewport viewport) { impl_->viewport = viewport; }
const Viewport& EditorSession::viewport() const { return impl_->viewport; }
void EditorSession::editBaseStructure(const std::string& nodeId, int previewFrame) {
    const ScriptNode* node=impl_->project.node(nodeId);
    if(!node||!node->enabled||nodeMetadata(node->type).structureEditCapability!="base")
        throw std::runtime_error("Node does not authorize structure editing: "+nodeId);
    const json params=json::parse(node->paramsJson);const std::string moleculeId=params.value("target","");
    if(!impl_->project.molecule(moleculeId))
        throw std::runtime_error("Structure node has no valid molecule target: "+nodeId);
    impl_->activeMolecule=moleculeId;impl_->targetKind=EditTargetKind::BaseStructure;
    impl_->targetId=nodeId;impl_->previewFrame=previewFrame;impl_->structureDraft.reset();impl_->gesture.reset();
}
void EditorSession::previewTimeline(int frame) { impl_->targetKind=EditTargetKind::TimelinePreview; impl_->targetId.clear(); impl_->previewFrame=frame; impl_->structureDraft.reset(); impl_->tool=Tool::SelectRectangle; impl_->gesture.reset(); }
void EditorSession::editAtomTween(const std::string& tweenId) {
    const auto found=std::find_if(impl_->project.atomTweens.begin(),impl_->project.atomTweens.end(),[&](const AtomTween& value){return value.id==tweenId;});
    if(found==impl_->project.atomTweens.end()) throw std::runtime_error("Unknown atom tween: "+tweenId);
    impl_->activeMolecule=found->moleculeId; impl_->targetKind=EditTargetKind::AtomTween; impl_->targetId=tweenId; impl_->previewFrame=found->startFrame+found->frames; impl_->tool=Tool::Move; impl_->gesture.reset();
}
void EditorSession::editPose(const std::string& moleculeId,const std::string& poseId,int previewFrame) {
    Molecule* value=impl_->project.molecule(moleculeId); if(!value) throw std::runtime_error("Unknown molecule: "+moleculeId);
    if(!value->poses.contains(poseId)) value->poses.emplace(poseId,Pose{poseId,{}});
    impl_->activeMolecule=moleculeId; impl_->targetKind=EditTargetKind::Pose; impl_->targetId=poseId; impl_->previewFrame=previewFrame; impl_->tool=Tool::Move; impl_->gesture.reset();
}
void EditorSession::editScriptNode(const std::string& nodeId) {
    const ScriptNode* node=impl_->project.node(nodeId); if(!node) throw std::runtime_error("Unknown script node: "+nodeId);
    const json params=json::parse(node->paramsJson); const std::string moleculeId=params.value("target","");
    if(impl_->project.molecule(moleculeId)) impl_->activeMolecule=moleculeId;
    const auto timings=compileNodeTimings(impl_->project);
    const auto found=std::find_if(timings.begin(),timings.end(),[&](const NodeTiming& value){return value.id==nodeId;});
    impl_->previewFrame=found==timings.end()?0:found->endFrame;
    const std::string capability=nodeMetadata(node->type).structureEditCapability;
    EditTargetKind desired=capability=="base"?EditTargetKind::BaseStructure:capability=="snapshot"?EditTargetKind::StructureSnapshot:EditTargetKind::ScriptNode;
    if(node->type=="molecule_gradient_structure"&&params.value("coordinate_space","")!="molecule_local_v2")desired=EditTargetKind::ScriptNode;
    const bool sameContext=impl_->targetId==nodeId&&impl_->targetKind==desired&&
        (desired!=EditTargetKind::StructureSnapshot||impl_->structureDraft.has_value());
    if(sameContext){impl_->previewFrame=found==timings.end()?0:found->endFrame;return;}
    impl_->targetKind=desired;
    impl_->targetId=nodeId;
    if(impl_->targetKind==EditTargetKind::StructureSnapshot)impl_->loadStructureDraft(*node);else impl_->structureDraft.reset();
    impl_->tool=Tool::SelectRectangle; impl_->gesture.reset();
}
EditTargetKind EditorSession::editTargetKind() const { return impl_->targetKind; }
std::string EditorSession::editTargetId() const { return impl_->targetId; }
int EditorSession::previewFrame() const { return impl_->previewFrame; }
std::optional<int> EditorSession::comparisonFrame() const {
    const ScriptNode* node=impl_->project.node(impl_->targetId);if(!node)return std::nullopt;const NodeMetadata& meta=nodeMetadata(node->type);if(meta.scope!="transform"||meta.exposure!="primary")return std::nullopt;
    const auto timings=compileNodeTimings(impl_->project);const auto found=std::find_if(timings.begin(),timings.end(),[&](const NodeTiming& value){return value.id==node->id;});if(found==timings.end())return std::nullopt;return found->startFrame;
}
bool EditorSession::canEditStructure() const { return impl_->validStructureContext(); }
bool EditorSession::canDirectManipulate() const {
    return impl_->validStructureContext() || impl_->validScriptManipulationContext();
}
Molecule EditorSession::displayMolecule() const { if(!impl_->molecule()) throw std::runtime_error("No active molecule"); return impl_->displayed(); }
std::vector<DirectControl> EditorSession::directControls() const {
    std::vector<DirectControl> result;if(impl_->targetKind!=EditTargetKind::ScriptNode)return result;const ScriptNode* node=impl_->project.node(impl_->targetId);if(!node)return result;
    if(nodeMetadata(node->type).directManipulationCapability=="molecule_translate"){const Molecule shown=evaluateMolecule(impl_->project,impl_->activeMolecule,impl_->previewFrame);result.push_back({"anchor","对象锚点",shown.origin});return result;}
    if(node->type!="arrow_set_curve")return result;const json p=json::parse(node->paramsJson);if(!p.value("initialized",true))return result;
    const auto shown=impl_->displayedArrow(impl_->project,*node);if(!shown)return result;
    const auto world=[&](Point value){return Point{value.x+shown->position.x,value.y+shown->position.y};};
    result.push_back({"p0","起点",world(shown->start)});result.push_back({"c1","控制点 1",world(shown->control1)});result.push_back({"c2","控制点 2",world(shown->control2)});result.push_back({"p3","终点",world(shown->end)});return result;
}
Hit EditorSession::hitTest(Point canvasPoint) const { return impl_->hit(canvasPoint); }

EditResult EditorSession::pointerDown(Point canvasPoint, bool, bool control, bool shift) {
    Molecule* molecule = impl_->editableMolecule();
    if (isStructureWriteTool(impl_->tool) && !impl_->validStructureContext())
        return impl_->result(canvasPoint);
    const Point pressModel = impl_->canvasToEdit(canvasPoint);
    Impl::Gesture gesture{.before = impl_->project, .pressCanvas = canvasPoint, .pressModel = pressModel,
                          .startCanvas = canvasPoint, .currentCanvas = canvasPoint,
                          .startModel = pressModel, .startHit = impl_->hit(canvasPoint)};
    const ScriptNode* activeNode=impl_->targetKind==EditTargetKind::ScriptNode?impl_->project.node(impl_->targetId):nullptr;
    const bool drawingArrow=activeNode&&activeNode->type=="arrow_set_curve"&&!json::parse(activeNode->paramsJson).value("initialized",true);
    if(!molecule&&gesture.startHit.kind!=HitKind::Control&&!drawingArrow)return impl_->result(canvasPoint);
    if (control && gesture.startHit.kind == HitKind::None) {
        // Ctrl-drag is a tool-independent rectangular selection gesture.  It
        // keeps the current drawing tool active once the gesture ends.
        gesture.previewKind=GesturePreviewKind::Rectangle;
    }
    else if (isBondTool(impl_->tool)) gesture.previewKind=GesturePreviewKind::Bond;
    else if (isRingTool(impl_->tool)) gesture.previewKind=GesturePreviewKind::Ring;
    else if ((impl_->tool==Tool::ChargePositive||impl_->tool==Tool::ChargeNegative)&&gesture.startHit.kind==HitKind::Atom) {
        gesture.previewKind=GesturePreviewKind::Adornment;
        gesture.previewText=impl_->tool==Tool::ChargePositive?"⊕":"⊖";
    }
    else if (impl_->tool==Tool::AtomText && gesture.startHit.kind==HitKind::Atom) {
        gesture.previewKind=GesturePreviewKind::Text;
    }
    else if (impl_->tool==Tool::SelectLasso) gesture.previewKind=gesture.startHit.kind!=HitKind::None?GesturePreviewKind::Move:GesturePreviewKind::Lasso;
    else if (impl_->tool==Tool::SelectRectangle) gesture.previewKind=gesture.startHit.kind!=HitKind::None?GesturePreviewKind::Move:GesturePreviewKind::Rectangle;
    else if (impl_->tool==Tool::Move) gesture.previewKind=GesturePreviewKind::Move;
    if(drawingArrow){gesture.previewKind=GesturePreviewKind::ArrowCurve;gesture.startModel=impl_->viewport.canvasToModel(canvasPoint);gesture.pressModel=gesture.startModel;gesture.lasso.assign(4,canvasPoint);}
    if (gesture.startHit.kind == HitKind::Atom) {
        const Molecule* editable=impl_->editableMolecule();
        if (const Atom* atom = editable?editable->atom(gesture.startHit.id):nullptr) {
            gesture.startModel = atom->position;
            gesture.startCanvas = impl_->editToCanvas(atom->position);
        }
    }
    if (impl_->tool == Tool::SelectLasso) gesture.lasso.push_back(canvasPoint);
    if(gesture.startHit.kind==HitKind::Control){gesture.previewKind=GesturePreviewKind::Move;gesture.original[gesture.startHit.id]=impl_->viewport.canvasToModel(canvasPoint);}
    if(gesture.startHit.kind==HitKind::Adornment&&(impl_->tool==Tool::SelectRectangle||impl_->tool==Tool::SelectLasso||impl_->tool==Tool::Move)){
        const Molecule shown=impl_->displayed();if(const AtomAdornment* value=shown.adornment(gesture.startHit.id))gesture.originalAdornments[value->id]=value->offset;
    }
    if (impl_->tool == Tool::Move || impl_->tool == Tool::SelectRectangle || impl_->tool == Tool::SelectLasso) {
        if (gesture.startHit.kind == HitKind::Atom) {
            if (control) {
                if (impl_->selectedAtoms.contains(gesture.startHit.id)) impl_->selectedAtoms.erase(gesture.startHit.id); else impl_->selectedAtoms.insert(gesture.startHit.id);
            } else if (shift) {
                impl_->selectedAtoms.insert(gesture.startHit.id);
            } else if (!impl_->selectedAtoms.contains(gesture.startHit.id)) {
                impl_->selectedAtoms = {gesture.startHit.id}; impl_->selectedBonds.clear();
            }
            if (impl_->targetKind != EditTargetKind::TimelinePreview) { const Molecule shown=impl_->validStructureContext()?*impl_->editableMolecule():impl_->displayed(); for (const std::string& id : impl_->selectedAtoms) if (const Atom* atom = shown.atom(id)) gesture.original[id] = atom->position; }
        } else if(gesture.startHit.kind==HitKind::Bond){
            if(control){if(impl_->selectedBonds.contains(gesture.startHit.id))impl_->selectedBonds.erase(gesture.startHit.id);else impl_->selectedBonds.insert(gesture.startHit.id);}
            else if(shift)impl_->selectedBonds.insert(gesture.startHit.id);
            else if(!impl_->selectedBonds.contains(gesture.startHit.id)){impl_->selectedAtoms.clear();impl_->selectedBonds={gesture.startHit.id};}
            if(impl_->targetKind!=EditTargetKind::TimelinePreview){const Molecule shown=impl_->validStructureContext()?*impl_->editableMolecule():impl_->displayed();for(const std::string& id:impl_->selectedAtoms)if(const Atom* atom=shown.atom(id))gesture.original[id]=atom->position;for(const std::string& id:impl_->selectedBonds)if(const Bond* bond=shown.bond(id))for(const std::string* atomId:{&bond->atomA,&bond->atomB})if(const Atom* atom=shown.atom(*atomId))gesture.original[atom->id]=atom->position;}
        } else if (!control && !shift) { impl_->selectedAtoms.clear(); impl_->selectedBonds.clear(); }
    }
    if(impl_->targetKind==EditTargetKind::ScriptNode){
        gesture.original.clear();gesture.originalAdornments.clear();const ScriptNode* node=impl_->project.node(impl_->targetId);const json params=node?json::parse(node->paramsJson):json::object();
        if(node&&nodeMetadata(node->type).directManipulationCapability=="molecule_translate"&&(gesture.startHit.kind==HitKind::Atom||gesture.startHit.kind==HitKind::Bond||gesture.startHit.kind==HitKind::Molecule)){const Molecule shown=impl_->displayed();for(const Atom& atom:shown.atoms)if(atom.alive)gesture.original[atom.id]=atom.position;}
        else if(node&&(node->type=="atom_set_xy"||node->type=="atom_lerp_xy")&&gesture.startHit.kind==HitKind::Atom&&gesture.startHit.id==params.value("atom","")){const Molecule shown=impl_->displayed();if(const Atom* atom=shown.atom(gesture.startHit.id))gesture.original[atom->id]=atom->position;}
        else if(node&&(node->type=="adornment_set_offset"||node->type=="adornment_lerp_offset")&&gesture.startHit.kind==HitKind::Adornment&&gesture.startHit.id==params.value("adornment","")){const Molecule shown=impl_->displayed();if(const AtomAdornment* value=shown.adornment(gesture.startHit.id))gesture.originalAdornments[value->id]=value->offset;}
        else if(node&&node->type=="arrow_set_curve"&&gesture.startHit.kind==HitKind::Control){
            gesture.original["p0"]={params.value("x1",0.0),params.value("y1",0.0)};
            gesture.original["c1"]={params.value("cx1",80.0),params.value("cy1",80.0)};
            gesture.original["c2"]={params.value("cx2",-80.0),params.value("cy2",80.0)};
            gesture.original["p3"]={params.value("x2",160.0),params.value("y2",0.0)};
        }
    }
    impl_->gesture = std::move(gesture);
    if (impl_->gesture->previewKind==GesturePreviewKind::Adornment) {
        impl_->gesture->currentCanvas=impl_->editToCanvas(impl_->adornmentEndpoint(false));
    }
    if (impl_->gesture->previewKind==GesturePreviewKind::Text) {
        impl_->gesture->currentCanvas=impl_->editToCanvas(impl_->textEndpoint());
    }
    if (impl_->tool == Tool::Eraser && impl_->gesture) {
        const Hit hit = impl_->gesture->startHit;
        if (hit.kind == HitKind::Atom && impl_->gesture->erasedAtoms.insert(hit.id).second)
            impl_->gesture->changed |= molecule->removeAtom(hit.id);
        else if (hit.kind == HitKind::Bond && impl_->gesture->erasedBonds.insert(hit.id).second)
            impl_->gesture->changed |= molecule->removeBond(hit.id);
    }
    return impl_->result(canvasPoint);
}

EditResult EditorSession::pointerMove(Point canvasPoint, bool alt, bool, bool) {
    if (!impl_->gesture) return impl_->result(canvasPoint);
    impl_->gesture->currentCanvas = canvasPoint;
    Molecule* molecule = impl_->editableMolecule();
    if(impl_->gesture->previewKind==GesturePreviewKind::ArrowCurve&&impl_->targetKind==EditTargetKind::ScriptNode){
        ScriptNode* node=impl_->project.node(impl_->targetId);if(!node||node->type!="arrow_set_curve")return impl_->result(canvasPoint);
        const Point current=impl_->viewport.canvasToModel(canvasPoint);const auto world=arrowCurveFromEndpoints(impl_->gesture->pressModel,current,impl_->gesture->bendLevel);
        json params=json::parse(node->paramsJson);const auto beforeNode=impl_->gesture->before.node(impl_->targetId);const auto shown=beforeNode?impl_->displayedArrow(impl_->gesture->before,*beforeNode):std::nullopt;
        const Point offset=shown?shown->position:Point{};const double sx=shown&&std::abs(shown->scaleX)>1e-12?shown->scaleX:1.0,sy=shown&&std::abs(shown->scaleY)>1e-12?shown->scaleY:1.0;
        const Point rawP0{world[0].x-offset.x,world[0].y-offset.y};
        const auto raw=[&](Point value){return Point{rawP0.x+(value.x-offset.x-rawP0.x)/sx,rawP0.y+(value.y-offset.y-rawP0.y)/sy};};
        const Point c1=raw(world[1]),c2=raw(world[2]),p3=raw(world[3]);
        params["x1"]=rawP0.x;params["y1"]=rawP0.y;params["cx1"]=c1.x;params["cy1"]=c1.y;params["cx2"]=c2.x;params["cy2"]=c2.y;params["x2"]=p3.x;params["y2"]=p3.y;node->paramsJson=params.dump();
        impl_->gesture->lasso.clear();for(const Point value:world)impl_->gesture->lasso.push_back(impl_->viewport.modelToCanvas(value));
        impl_->gesture->changed=distance(impl_->gesture->pressCanvas,canvasPoint)>=4.0;return impl_->result(canvasPoint);
    }
    if(impl_->gesture->startHit.kind==HitKind::Control&&impl_->targetKind==EditTargetKind::ScriptNode){
        ScriptNode* node=impl_->project.node(impl_->targetId);if(node&&node->type=="arrow_set_curve"){const Point current=impl_->viewport.canvasToModel(canvasPoint);json params=json::parse(node->paramsJson);const std::string id=impl_->gesture->startHit.id;
            const ScriptNode* beforeNode=impl_->gesture->before.node(impl_->targetId);const auto shown=beforeNode?impl_->displayedArrow(impl_->gesture->before,*beforeNode):std::nullopt;
            const Point offset=shown?shown->position:Point{};const double sx=shown&&std::abs(shown->scaleX)>1e-12?shown->scaleX:1.0,sy=shown&&std::abs(shown->scaleY)>1e-12?shown->scaleY:1.0;
            const Point rawP0=impl_->gesture->original.at("p0");const auto raw=[&](Point value){return Point{rawP0.x+(value.x-offset.x-rawP0.x)/sx,rawP0.y+(value.y-offset.y-rawP0.y)/sy};};
            if(id=="p0"){const Point target{current.x-offset.x,current.y-offset.y};const Point delta{target.x-rawP0.x,target.y-rawP0.y};const Point c1=impl_->gesture->original.at("c1");params["x1"]=target.x;params["y1"]=target.y;params["cx1"]=c1.x+delta.x;params["cy1"]=c1.y+delta.y;}
            else if(id=="c1"){const Point target=raw(current);params["cx1"]=target.x;params["cy1"]=target.y;}
            else if(id=="c2"){const Point target=raw(current);params["cx2"]=target.x;params["cy2"]=target.y;}
            else if(id=="p3"){const Point target=raw(current);const Point old=impl_->gesture->original.at("p3"),c2=impl_->gesture->original.at("c2");params["x2"]=target.x;params["y2"]=target.y;params["cx2"]=c2.x+target.x-old.x;params["cy2"]=c2.y+target.y-old.y;}
            node->paramsJson=params.dump();impl_->gesture->changed=distance(impl_->gesture->pressModel,current)>1e-9;
        }return impl_->result(canvasPoint);
    }
    if (!molecule) return impl_->result(canvasPoint);
    if ((impl_->tool == Tool::Move || impl_->tool == Tool::SelectRectangle || impl_->tool == Tool::SelectLasso) && !impl_->gesture->original.empty()) {
        const Point current = impl_->canvasToEdit(canvasPoint);
        Point delta{current.x - impl_->gesture->pressModel.x, current.y - impl_->gesture->pressModel.y};
        ScriptNode* directNode=impl_->targetKind==EditTargetKind::ScriptNode?impl_->project.node(impl_->targetId):nullptr;
        if(directNode&&(directNode->type=="molecule_set_x"||directNode->type=="molecule_lerp_x"))delta.y=0.0;
        if(directNode&&(directNode->type=="molecule_set_y"||directNode->type=="molecule_lerp_y"))delta.x=0.0;
        for (const auto& [id, position] : impl_->gesture->original) {
            const Point target{position.x + delta.x, position.y + delta.y};
            if (impl_->targetKind == EditTargetKind::BaseStructure||impl_->targetKind==EditTargetKind::StructureSnapshot) { if (Atom* atom = molecule->atom(id)) atom->position = target; }
            else impl_->gesture->targetPositions[id] = target;
        }
        impl_->gesture->changed = std::hypot(delta.x, delta.y) > 1e-9;
        if(impl_->gesture->changed&&directNode&&(directNode->type=="molecule_set_position"||directNode->type=="molecule_lerp_position"||directNode->type=="molecule_set_x"||directNode->type=="molecule_lerp_x"||directNode->type=="molecule_set_y"||directNode->type=="molecule_lerp_y")){
            json params=json::parse(directNode->paramsJson);const Molecule beforeShown=evaluateMolecule(impl_->gesture->before,impl_->activeMolecule,impl_->previewFrame);const Point origin=beforeShown.origin;
            if(directNode->type=="molecule_set_x"||directNode->type=="molecule_lerp_x")params["value"]=origin.x+delta.x;
            else if(directNode->type=="molecule_set_y"||directNode->type=="molecule_lerp_y")params["value"]=origin.y+delta.y;
            else{params["x"]=origin.x+delta.x;params["y"]=origin.y+delta.y;}
            directNode->paramsJson=params.dump();
        }
    } else if((impl_->tool==Tool::Move||impl_->tool==Tool::SelectRectangle||impl_->tool==Tool::SelectLasso)&&!impl_->gesture->originalAdornments.empty()){
        const Point current=impl_->canvasToEdit(canvasPoint);const Point delta{current.x-impl_->gesture->pressModel.x,current.y-impl_->gesture->pressModel.y};
        for(const auto& [id,offset]:impl_->gesture->originalAdornments){const Point target{offset.x+delta.x,offset.y+delta.y};if(impl_->targetKind==EditTargetKind::BaseStructure||impl_->targetKind==EditTargetKind::StructureSnapshot){if(AtomAdornment* value=molecule->adornment(id))value->offset=target;}else impl_->gesture->targetAdornmentOffsets[id]=target;}
        impl_->gesture->changed=std::hypot(delta.x,delta.y)>1e-9;
    } else if (impl_->tool == Tool::SelectLasso) {
        if (impl_->gesture->lasso.empty() || distance(canvasPoint, impl_->gesture->lasso.back()) > 3.0) impl_->gesture->lasso.push_back(canvasPoint);
    } else if (impl_->gesture->previewKind==GesturePreviewKind::Rectangle) {
        // The rectangle is rendered by the editor overlay; no model mutation
        // occurs until pointerUp performs the selection.
    } else if (isBondTool(impl_->tool)) {
        impl_->gesture->currentCanvas = impl_->editToCanvas(impl_->gestureEndpoint(alt));
    } else if (isRingTool(impl_->tool)) {
        impl_->gesture->lasso.clear();
        for (Point point : impl_->ringPolygon(ringSize(impl_->tool), canvasPoint, alt)) impl_->gesture->lasso.push_back(impl_->editToCanvas(point));
    } else if (impl_->tool==Tool::ChargePositive||impl_->tool==Tool::ChargeNegative) {
        if (impl_->gesture->startHit.kind==HitKind::Atom)
            impl_->gesture->currentCanvas=impl_->editToCanvas(impl_->adornmentEndpoint(alt));
    } else if (impl_->tool==Tool::AtomText) {
        if (impl_->gesture->startHit.kind==HitKind::Atom)
            impl_->gesture->currentCanvas=impl_->editToCanvas(impl_->textEndpoint());
    } else if (impl_->tool == Tool::Eraser) {
        const Hit hit = impl_->hit(canvasPoint);
        if (hit.kind == HitKind::Atom && impl_->gesture->erasedAtoms.insert(hit.id).second)
            impl_->gesture->changed |= molecule->removeAtom(hit.id);
        else if (hit.kind == HitKind::Bond && impl_->gesture->erasedBonds.insert(hit.id).second)
            impl_->gesture->changed |= molecule->removeBond(hit.id);
    }
    return impl_->result(canvasPoint);
}

EditResult EditorSession::pointerUp(Point canvasPoint, bool alt, bool control, bool) {
    if (!impl_->gesture) return impl_->result(canvasPoint);
    impl_->gesture->currentCanvas = canvasPoint;
    Molecule* molecule = impl_->editableMolecule();
    if(impl_->gesture->previewKind==GesturePreviewKind::ArrowCurve){
        const bool changed=impl_->gesture->changed;
        if(changed)if(ScriptNode* node=impl_->project.node(impl_->targetId)){json params=json::parse(node->paramsJson);params["initialized"]=true;node->paramsJson=params.dump();}
        impl_->commit();EditResult result=impl_->result(canvasPoint);result.changed=changed;return result;
    }
    if (!molecule&&impl_->gesture->startHit.kind==HitKind::Control){const bool changed=impl_->gesture->changed;impl_->commit();EditResult result=impl_->result(canvasPoint);result.changed=changed;return result;}
    if (!molecule) { impl_->gesture.reset(); return impl_->result(canvasPoint); }
    if (impl_->targetKind != EditTargetKind::BaseStructure&&impl_->targetKind!=EditTargetKind::StructureSnapshot) {
        if (impl_->gesture->changed && impl_->targetKind == EditTargetKind::AtomTween) {
            auto found=std::find_if(impl_->project.atomTweens.begin(),impl_->project.atomTweens.end(),[&](const AtomTween& value){return value.id==impl_->targetId;});
            if(found!=impl_->project.atomTweens.end()) for(const auto& [atomId,target]:impl_->gesture->targetPositions) {
                if(atomId==found->atomId) found->target=target;
                else {
                    const std::string tweenId = impl_->project.addAtomTween(
                        found->moleculeId, atomId, found->startFrame, found->frames,
                        target, found->easing);
                    (void)tweenId;
                }
            }
        } else if (impl_->gesture->changed && impl_->targetKind == EditTargetKind::Pose) {
            Pose& pose=molecule->poses[impl_->targetId]; pose.id=impl_->targetId;
            for(const auto& [atomId,target]:impl_->gesture->targetPositions) pose.atomPositions[atomId]=target;
        } else if (impl_->gesture->changed && impl_->targetKind == EditTargetKind::ScriptNode) {
            if (ScriptNode* node=impl_->project.node(impl_->targetId)) {
                json params=json::parse(node->paramsJson); const std::string atomId=params.value("atom","");
                if(const auto found=impl_->gesture->targetPositions.find(atomId);found!=impl_->gesture->targetPositions.end()){
                    params["x"]=found->second.x;params["y"]=found->second.y;node->paramsJson=params.dump();
                }
                const std::string adornmentId=params.value("adornment","");
                if(const auto found=impl_->gesture->targetAdornmentOffsets.find(adornmentId);found!=impl_->gesture->targetAdornmentOffsets.end()){params["x"]=found->second.x;params["y"]=found->second.y;node->paramsJson=params.dump();}
                // Molecule position nodes are updated continuously in
                // pointerMove from the gesture's immutable before-state.
            }
        }
    } else if (impl_->gesture->previewKind == GesturePreviewKind::Rectangle && impl_->gesture->original.empty() && impl_->gesture->originalAdornments.empty()) {
        const double left = std::min(impl_->gesture->pressCanvas.x, canvasPoint.x), right = std::max(impl_->gesture->pressCanvas.x, canvasPoint.x);
        const double top = std::min(impl_->gesture->pressCanvas.y, canvasPoint.y), bottom = std::max(impl_->gesture->pressCanvas.y, canvasPoint.y);
        if (!control) impl_->selectedAtoms.clear();
        for (const Atom& atom : molecule->atoms) if (atom.alive && Rect{left, top, right, bottom}.contains(impl_->editToCanvas(atom.position))) impl_->selectedAtoms.insert(atom.id);
        if(!control)impl_->selectedBonds.clear();for(const Bond& bond:molecule->bonds)if(bond.alive&&impl_->selectedAtoms.contains(bond.atomA)&&impl_->selectedAtoms.contains(bond.atomB))impl_->selectedBonds.insert(bond.id);
    } else if (impl_->tool == Tool::SelectLasso && impl_->gesture->original.empty() && impl_->gesture->originalAdornments.empty() && impl_->gesture->lasso.size() >= 3) {
        if (!control) impl_->selectedAtoms.clear();
        for (const Atom& atom : molecule->atoms) if (atom.alive && pointInPolygon(impl_->editToCanvas(atom.position), impl_->gesture->lasso)) impl_->selectedAtoms.insert(atom.id);
        if(!control)impl_->selectedBonds.clear();for(const Bond& bond:molecule->bonds)if(bond.alive&&impl_->selectedAtoms.contains(bond.atomA)&&impl_->selectedAtoms.contains(bond.atomB))impl_->selectedBonds.insert(bond.id);
    } else if (isBondTool(impl_->tool)) {
        const auto [type, stereo] = bondStyle(impl_->tool);
        if (impl_->gesture->startHit.kind == HitKind::Bond && distance(impl_->gesture->startCanvas, canvasPoint) < 5.0) {
            if (Bond* bond = molecule->bond(impl_->gesture->startHit.id)) {
                if (impl_->tool==Tool::SingleBond) {
                    bond->type=bond->type==BondType::Single?BondType::Double:
                        bond->type==BondType::Double?BondType::Triple:BondType::Single;
                    bond->stereo=BondStereo::None;
                    if(bond->type==BondType::Double)bond->secondaryLineSide=SecondaryLineSide::Center;
                } else if (impl_->tool==Tool::DoubleBond && bond->type==BondType::Double &&
                           bond->stereo==BondStereo::None) {
                    // Match ChemDraw's double-bond tool: clicking an existing
                    // double bond changes only its persistent visual side.
                    // The atom order remains stable, so Left/Right also remain
                    // stable across save/reopen and timeline evaluation.
                    bond->secondaryLineSide =
                        bond->secondaryLineSide==SecondaryLineSide::Center ? SecondaryLineSide::Left :
                        bond->secondaryLineSide==SecondaryLineSide::Left ? SecondaryLineSide::Right :
                        SecondaryLineSide::Center;
                } else {
                    bond->type = type;
                    bond->stereo = stereo;
                    if (type==BondType::Double) bond->secondaryLineSide=SecondaryLineSide::Center;
                }
                impl_->gesture->changed = true;
            }
        } else {
            // Resolve both endpoints against the pre-gesture document.  If we
            // create the first carbon before resolving a click endpoint, that
            // new carbon is hit at the cursor and the gesture collapses into a
            // lone implicit-CH4 atom instead of the expected ethane skeleton.
            const Point endpoint = impl_->gestureEndpoint(alt);
            const bool click=distance(impl_->gesture->pressCanvas,canvasPoint)<=12.0;
            const Hit endpointHit = click ? Hit{} : impl_->hit(impl_->editToCanvas(endpoint),
                                               impl_->gesture->startHit.kind == HitKind::Atom
                                                   ? std::optional(impl_->gesture->startHit.id)
                                                   : std::nullopt);
            std::string first = impl_->gesture->startHit.kind == HitKind::Atom ? impl_->gesture->startHit.id : molecule->addAtom(impl_->gesture->startModel, "C", impl_->project.allocateCreationSerial());
            std::string second = endpointHit.kind == HitKind::Atom ? endpointHit.id : molecule->addAtom(endpoint, "C", impl_->project.allocateCreationSerial());
            if (first != second) {
                const std::string bondId = molecule->addBond(first, second, type, stereo);
                impl_->gesture->changed = !bondId.empty();
            }
        }
    } else if (isRingTool(impl_->tool)) {
        const int count = ringSize(impl_->tool); const std::vector<Point> polygon = impl_->ringPolygon(count, canvasPoint, alt);
        if (static_cast<int>(polygon.size()) == count) {
            std::vector<std::string> ids(count);
            if (impl_->gesture->startHit.kind == HitKind::Atom) ids[0] = impl_->gesture->startHit.id;
            if (impl_->gesture->startHit.kind == HitKind::Bond) { if (const Bond* bond = molecule->bond(impl_->gesture->startHit.id)) { ids[0] = bond->atomA; ids[1] = bond->atomB; } }
            for (int i = 0; i < count; ++i) if (ids[i].empty()) ids[i] = molecule->addAtom(polygon[i], "C", impl_->project.allocateCreationSerial());
            for (int i = 0; i < count; ++i) {
                if (impl_->gesture->startHit.kind == HitKind::Bond && i == 0) continue;
                const BondType type = impl_->tool == Tool::Benzene && i % 2 == 0 ? BondType::Double : BondType::Single;
                const std::string bondId = molecule->addBond(ids[i], ids[(i + 1) % count], type);
                if (type == BondType::Double) if (Bond* bond=molecule->bond(bondId)) {
                    const Point a=polygon[i], b=polygon[(i+1)%count];
                    Point center{}; for(const Point p:polygon){center.x+=p.x;center.y+=p.y;} center.x/=count;center.y/=count;
                    const Point normal{-(b.y-a.y),b.x-a.x};
                    const Point mid{(a.x+b.x)*.5,(a.y+b.y)*.5};
                    bond->secondaryLineSide=((center.x-mid.x)*normal.x+(center.y-mid.y)*normal.y)>=0
                        ? SecondaryLineSide::Left : SecondaryLineSide::Right;
                }
                (void)bondId;
            }
            impl_->gesture->changed = true;
        }
    } else if (impl_->tool == Tool::AtomText) {
        std::string request;
        if (impl_->gesture->startHit.kind == HitKind::Atom) {
            request = "atom_text|" + impl_->gesture->startHit.id + "|" +
                (impl_->textSide() == AtomLabelSide::Left ? "left" : "right");
        }
        impl_->commit();
        EditResult result = impl_->result(canvasPoint); result.message = std::move(request); return result;
    } else if (impl_->tool == Tool::AtomLabel) {
        if (impl_->gesture->startHit.kind == HitKind::Atom) {
            Atom* atom=molecule->atom(impl_->gesture->startHit.id);
            // Element buttons are presets for the same visual label edited by
            // AtomText; they do not switch to a second chemical data path.
            atom->alias=impl_->element=="C" ? "" : impl_->element;
            atom->labelSide=impl_->textSide();atom->numberStyle=AtomNumberStyle::Subscript;
        }
        else {
            const std::string atomId = molecule->addAtom(impl_->gesture->startModel, "C", impl_->project.allocateCreationSerial());
            if(Atom* atom=molecule->atom(atomId))atom->alias=impl_->element=="C" ? "" : impl_->element;
        }
        impl_->gesture->changed = true;
    } else if (impl_->tool == Tool::ChargePositive || impl_->tool == Tool::ChargeNegative) {
        if (impl_->gesture->startHit.kind == HitKind::Atom) {
            const Atom* owner=molecule->atom(impl_->gesture->startHit.id);
            const Point endpoint=impl_->adornmentEndpoint(alt);
            const std::string id=molecule->addAdornment(impl_->gesture->startHit.id,
                impl_->tool == Tool::ChargePositive ? "⊕" : "⊖",
                {endpoint.x-owner->position.x,endpoint.y-owner->position.y},
                impl_->project.allocateCreationSerial());
            impl_->gesture->changed = !id.empty();
        }
    }
    const bool changed = impl_->gesture->changed;
    impl_->commit();
    EditResult result = impl_->result(canvasPoint); result.changed = changed; return result;
}

bool EditorSession::adjustArrowCurveBend(int direction) {
    if(direction==0||impl_->targetKind!=EditTargetKind::ScriptNode)return false;
    ScriptNode* node=impl_->project.node(impl_->targetId);if(!node||node->type!="arrow_set_curve")return false;
    if(impl_->gesture&&impl_->gesture->previewKind==GesturePreviewKind::ArrowCurve){
        impl_->gesture->bendLevel=std::clamp(impl_->gesture->bendLevel+(direction>0?1.0:-1.0),-5.0,5.0);
        (void)pointerMove(impl_->gesture->currentCanvas,false,false,false);return true;
    }
    json params=json::parse(node->paramsJson);if(!params.value("initialized",true))return false;
    const Point p0{params.value("x1",0.0),params.value("y1",0.0)},p3{params.value("x2",160.0),params.value("y2",0.0)};
    const Point delta{p3.x-p0.x,p3.y-p0.y};const double length=std::hypot(delta.x,delta.y);if(length<=1e-9)return false;
    const double amount=std::clamp(length*0.18,18.0,70.0)*(direction>0?1.0:-1.0);const Point shift{-delta.y/length*amount,delta.x/length*amount};
    Project before=impl_->project;params["cx1"]=params.value("cx1",80.0)+shift.x;params["cy1"]=params.value("cy1",80.0)+shift.y;params["cx2"]=params.value("cx2",-80.0)+shift.x;params["cy2"]=params.value("cy2",80.0)+shift.y;node->paramsJson=params.dump();
    impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return true;
}

void EditorSession::cancelGesture() { if (impl_->gesture) { const auto high=impl_->project.nextCreationSerial;impl_->project = std::move(impl_->gesture->before);impl_->project.nextCreationSerial=std::max(impl_->project.nextCreationSerial,high);impl_->gesture.reset(); } }
EditResult EditorSession::selectAll() {
    impl_->selectedAtoms.clear();
    impl_->selectedBonds.clear();
    if (const Molecule* molecule=impl_->editableMolecule()) {
        for (const Atom& atom:molecule->atoms) if (atom.alive) impl_->selectedAtoms.insert(atom.id);
        for (const Bond& bond:molecule->bonds) if (bond.alive&&bond.visible)
            impl_->selectedBonds.insert(bond.id);
    }
    return impl_->result({-1e9,-1e9});
}
bool EditorSession::deleteSelection() {
    if (!impl_->validStructureContext()) return false;
    Molecule* molecule = impl_->editableMolecule(); if (!molecule) return false;
    Project before = impl_->project; bool changed = false;
    for (const std::string& id : impl_->selectedBonds) changed |= molecule->removeBond(id);
    for (const std::string& id : impl_->selectedAtoms) changed |= molecule->removeAtom(id);
    if (changed) { impl_->flushStructureDraft();impl_->undo.push_back({std::move(before), impl_->project, Impl::SnapshotDomain::Structure}); impl_->redo.clear(); impl_->selectedAtoms.clear(); impl_->selectedBonds.clear(); }
    return changed;
}
bool EditorSession::setAtomPosition(const std::string& atomId, Point position) {
    if (!impl_->validStructureContext()) return false;
    Molecule* molecule = impl_->editableMolecule(); Atom* atom = molecule ? molecule->atom(atomId) : nullptr;
    if (!atom || (atom->position.x == position.x && atom->position.y == position.y)) return false;
    Project before = impl_->project; atom->position = position;impl_->flushStructureDraft(); impl_->undo.push_back({std::move(before), impl_->project, Impl::SnapshotDomain::Structure}); impl_->redo.clear(); return true;
}
bool EditorSession::setAtomElement(const std::string& atomId, std::string element) {
    if (!impl_->validStructureContext()) return false;
    Molecule* molecule = impl_->editableMolecule(); Atom* atom = molecule ? molecule->atom(atomId) : nullptr;
    const std::string label=element=="C" ? "" : element;
    if (!atom || atom->alias == label || element.empty()) return false;
    Project before = impl_->project; atom->alias = label;impl_->flushStructureDraft(); impl_->undo.push_back({std::move(before), impl_->project, Impl::SnapshotDomain::Structure}); impl_->redo.clear(); return true;
}
bool EditorSession::setAtomLabel(const std::string& atomId, std::string label,
                                 AtomLabelSide side, AtomNumberStyle numberStyle) {
    if (!impl_->validStructureContext()) return false;
    Molecule* molecule = impl_->editableMolecule(); Atom* atom = molecule ? molecule->atom(atomId) : nullptr;
    if (!atom || label.empty() ||
        (atom->alias == label && atom->labelSide == side && atom->numberStyle == numberStyle)) return false;
    Project before = impl_->project; atom->alias = std::move(label); atom->labelSide = side;
    atom->numberStyle = numberStyle;impl_->flushStructureDraft(); impl_->undo.push_back({std::move(before), impl_->project, Impl::SnapshotDomain::Structure});
    impl_->redo.clear(); return true;
}
bool EditorSession::addChargeAdornment(const std::string& atomId, int delta) {
    if (!impl_->validStructureContext()) return false;
    Molecule* molecule = impl_->editableMolecule(); Atom* atom = molecule ? molecule->atom(atomId) : nullptr;
    if (!atom || delta == 0) return false;
    Project before = impl_->project;
    const std::string text = std::abs(delta) == 1 ? (delta > 0 ? "⊕" : "⊖")
        : std::to_string(std::abs(delta)) + (delta > 0 ? "⊕" : "⊖");
    const std::string id=molecule->addAdornment(atomId,text,{18.0,18.0},impl_->project.allocateCreationSerial());
    if(id.empty())return false;
    impl_->flushStructureDraft();impl_->undo.push_back({std::move(before), impl_->project, Impl::SnapshotDomain::Structure}); impl_->redo.clear(); return true;
}
bool EditorSession::setAdornmentOffset(const std::string& adornmentId, Point offset) {
    if (!impl_->validStructureContext()) return false;
    Molecule* molecule=impl_->editableMolecule(); AtomAdornment* value=molecule?molecule->adornment(adornmentId):nullptr;
    if(!value||(value->offset.x==offset.x&&value->offset.y==offset.y))return false;
    Project before=impl_->project;value->offset=offset;impl_->flushStructureDraft();impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Structure});impl_->redo.clear();return true;
}
std::string EditorSession::createBlankMolecule(std::string name,std::optional<std::size_t> insertionIndex) {
    Project before=impl_->project;const std::string id=impl_->project.addBlankMolecule(std::move(name),insertionIndex);
    impl_->activeMolecule=id;
    for(auto found=impl_->project.nodes.rbegin();found!=impl_->project.nodes.rend();++found)if(found->type=="molecule_create"&&json::parse(found->paramsJson).value("target","")==id){impl_->targetId=found->id;break;}
    impl_->targetKind=EditTargetKind::ScriptNode;impl_->previewFrame=0;impl_->structureDraft.reset();impl_->tool=Tool::SelectRectangle;
    impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return id;
}
std::string EditorSession::importSmiles(std::string name,const std::string& smiles,std::optional<std::size_t> insertionIndex) {
    Project before=impl_->project;const std::size_t createIndex=std::min(insertionIndex.value_or(impl_->project.nodes.size()),impl_->project.nodes.size());const std::string id=impl_->project.addBlankMolecule(name,createIndex);
    Molecule* destination=impl_->project.molecule(id);const std::uint64_t firstAtom=destination->nextAtomId,firstBond=destination->nextBondId,firstAdornment=destination->nextAdornmentId;
    Molecule imported=moleculeFromSmiles(id,name.empty()?id:name,smiles);std::map<std::string,std::string> atomIds;
    std::uint64_t atomNumber=firstAtom,bondNumber=firstBond,adornmentNumber=firstAdornment;
    for(Atom& atom:imported.atoms){const std::string old=atom.id;atom.id="A"+std::to_string(atomNumber++);atomIds[old]=atom.id;atom.creationSerial=impl_->project.allocateCreationSerial();}
    for(Bond& bond:imported.bonds){bond.id="B"+std::to_string(bondNumber++);bond.atomA=atomIds.at(bond.atomA);bond.atomB=atomIds.at(bond.atomB);}
    for(AtomAdornment& value:imported.adornments){value.id="D"+std::to_string(adornmentNumber++);value.atomId=atomIds.at(value.atomId);value.creationSerial=impl_->project.allocateCreationSerial();}
    imported.nextAtomId=atomNumber;imported.nextBondId=bondNumber;imported.nextAdornmentId=adornmentNumber;imported.origin=destination->origin;
    destination->nextAtomId=atomNumber;destination->nextBondId=bondNumber;destination->nextAdornmentId=adornmentNumber;
    const json params={{"target",id},{"coordinate_space","molecule_local_v2"},{"snapshot",moleculeSnapshotJson(imported)}};
    const std::string structureId=impl_->project.addNode("molecule_set_structure",params.dump(),createIndex+1);
    impl_->activeMolecule=id;impl_->targetId=structureId;impl_->targetKind=EditTargetKind::StructureSnapshot;impl_->previewFrame=0;impl_->structureDraft=std::move(imported);
    impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return id;
}
std::string EditorSession::addScriptNode(const std::string& type,const std::string& paramsJson,std::optional<std::size_t> index) {
    if(type=="molecule_create")throw std::runtime_error("Use the atomic new-molecule command");
    Project before=impl_->project;
    if(type=="molecule_set_structure"){
        if(impl_->activeMolecule.empty())throw std::runtime_error("设定分子结构需要当前活动分子");
        const std::size_t insertion=std::min(index.value_or(impl_->project.nodes.size()),impl_->project.nodes.size());int startFrame=0;
        const auto start=structureBeforeNode(impl_->project,insertion,impl_->activeMolecule,&startFrame);if(!start)throw std::runtime_error("当前节点位置没有仍然存活的活动分子");
        json params={{"target",impl_->activeMolecule},{"coordinate_space","molecule_local_v2"},{"snapshot",moleculeSnapshotJson(*start)}};
        const std::string id=impl_->project.addNode(type,params.dump(),insertion);impl_->targetKind=EditTargetKind::StructureSnapshot;impl_->targetId=id;impl_->previewFrame=startFrame;impl_->structureDraft=*start;
        impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return id;
    }
    if(type=="molecule_gradient_structure"){
        if(impl_->activeMolecule.empty())throw std::runtime_error("渐变结构需要当前活动分子");
        const std::size_t insertion=std::min(index.value_or(impl_->project.nodes.size()),impl_->project.nodes.size());int startFrame=0;
        const auto start=structureBeforeNode(impl_->project,insertion,impl_->activeMolecule,&startFrame);if(!start)throw std::runtime_error("当前节点位置没有仍然存活的活动分子");
        json requested=json::parse(paramsJson);json params={{"target",impl_->activeMolecule},{"frames",std::max(0,requested.value("frames",30))},{"easing",requested.value("easing","linear")},{"coordinate_space","molecule_local_v2"},{"start_snapshot",moleculeSnapshotJson(*start)},{"end_snapshot",moleculeSnapshotJson(*start)},{"needs_review",false}};
        const std::string id=impl_->project.addNode(type,params.dump(),insertion);impl_->targetKind=EditTargetKind::StructureSnapshot;impl_->targetId=id;impl_->previewFrame=startFrame+params["frames"].get<int>();impl_->structureDraft=*start;
        impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return id;
    }
    const std::string id=impl_->project.addNode(type,paramsJson,index);
    impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return id;
}
bool EditorSession::updateScriptNode(const std::string& nodeId,const std::string& paramsJson) {
    ScriptNode* node=impl_->project.node(nodeId);if(!node)return false;const json value=json::parse(paramsJson);
    if(!value.is_object())throw std::runtime_error("Node params must be an object");
    if(nodeMetadata(node->type).targetImmutable){const json old=json::parse(node->paramsJson);if(value.value("target","")!=old.value("target",""))throw std::runtime_error("The target of a new-molecule node is immutable");}
    const std::string normalized=value.dump();
    if(node->paramsJson==normalized)return false;Project before=impl_->project;node->paramsJson=normalized;
    const std::size_t index=static_cast<std::size_t>(std::distance(impl_->project.nodes.begin(),std::find_if(impl_->project.nodes.begin(),impl_->project.nodes.end(),[&](const ScriptNode& item){return item.id==nodeId;})));
    if(node->type!="molecule_gradient_structure")impl_->markGradientNodesForReview(index+1);
    impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return true;
}
bool EditorSession::setScriptNodeEnabled(const std::string& nodeId,bool enabled) {
    ScriptNode* node=impl_->project.node(nodeId);if(!node||node->enabled==enabled)return false;Project before=impl_->project;node->enabled=enabled;
    impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return true;
}
bool EditorSession::moveScriptNode(const std::string& nodeId,std::size_t index) {
    auto found=std::find_if(impl_->project.nodes.begin(),impl_->project.nodes.end(),[&](const ScriptNode& value){return value.id==nodeId;});
    if(found==impl_->project.nodes.end()||found->type=="scene")return false;const std::size_t old=static_cast<std::size_t>(std::distance(impl_->project.nodes.begin(),found));
    if(!impl_->project.nodes.empty()&&impl_->project.nodes.front().type=="scene")index=std::max<std::size_t>(1,index);
    index=std::min(index,impl_->project.nodes.size()-1);if(old==index)return false;Project before=impl_->project;ScriptNode value=std::move(*found);
    impl_->project.nodes.erase(impl_->project.nodes.begin()+static_cast<std::ptrdiff_t>(old));
    impl_->project.nodes.insert(impl_->project.nodes.begin()+static_cast<std::ptrdiff_t>(index),std::move(value));
    impl_->markGradientNodesForReview();
    impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return true;
}
std::string EditorSession::duplicateScriptNode(const std::string& nodeId) {
    const ScriptNode* node=impl_->project.node(nodeId);if(!node||node->type=="scene")return{};const auto found=std::find_if(impl_->project.nodes.begin(),impl_->project.nodes.end(),[&](const ScriptNode& value){return value.id==nodeId;});
    const std::size_t index=static_cast<std::size_t>(std::distance(impl_->project.nodes.begin(),found))+1;
    if(node->type=="molecule_create"){
        const json params=json::parse(node->paramsJson);Project before=impl_->project;const std::string moleculeId=impl_->project.duplicateMolecule(params.value("target",""),index);
        impl_->activeMolecule=moleculeId;std::string createdId;for(const ScriptNode& value:impl_->project.nodes)if(value.type=="molecule_create"&&json::parse(value.paramsJson).value("target","")==moleculeId){createdId=value.id;break;}
        impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return createdId;
    }
    if(node->type=="molecule_gradient_structure"){
        Project before=impl_->project;json params=json::parse(node->paramsJson);params["needs_review"]=true;const std::string created=impl_->project.addNode(node->type,params.dump(),index);
        impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return created;
    }
    return addScriptNode(node->type,node->paramsJson,index);
}
bool EditorSession::deleteScriptNode(const std::string& nodeId) {
    const auto found=std::find_if(impl_->project.nodes.begin(),impl_->project.nodes.end(),[&](const ScriptNode& value){return value.id==nodeId;});
    if(found==impl_->project.nodes.end()||found->type=="scene")return false;const std::size_t index=static_cast<std::size_t>(std::distance(impl_->project.nodes.begin(),found));Project before=impl_->project;impl_->project.nodes.erase(found);impl_->markGradientNodesForReview(index);
    impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return true;
}
std::string EditorSession::gradientStructureSummary(const std::string& nodeId) const {
    const ScriptNode* node=impl_->project.node(nodeId);if(!node||node->type!="molecule_gradient_structure")return "{}";const json params=json::parse(node->paramsJson);
    const auto start=moleculeFromSnapshotJson(params.value("start_snapshot",json::object())),end=moleculeFromSnapshotJson(params.value("end_snapshot",json::object()));if(!start||!end)return "{}";
    std::map<std::string,const Atom*> firstAtoms,secondAtoms;for(const Atom& value:start->atoms)if(value.alive)firstAtoms[value.id]=&value;for(const Atom& value:end->atoms)if(value.alive)secondAtoms[value.id]=&value;
    std::map<std::string,const Bond*> firstBonds,secondBonds;for(const Bond& value:start->bonds)if(value.alive)firstBonds[value.id]=&value;for(const Bond& value:end->bonds)if(value.alive)secondBonds[value.id]=&value;
    std::map<std::string,const AtomAdornment*> firstAdornments,secondAdornments;for(const AtomAdornment& value:start->adornments)if(value.alive)firstAdornments[value.id]=&value;for(const AtomAdornment& value:end->adornments)if(value.alive)secondAdornments[value.id]=&value;
    int addedAtoms=0,addedBonds=0,addedAdornments=0,deleted=0,moved=0,changed=0;
    for(const auto& [id,value]:secondAtoms)if(!firstAtoms.contains(id))++addedAtoms;else{const Atom& first=*firstAtoms.at(id);if(distance(first.position,value->position)>1e-6)++moved;if(first.element!=value->element||first.alias!=value->alias||first.hidden!=value->hidden)++changed;}
    for(const auto& [id,_]:firstAtoms)if(!secondAtoms.contains(id))++deleted;
    for(const auto& [id,value]:secondBonds)if(!firstBonds.contains(id))++addedBonds;else{const Bond& first=*firstBonds.at(id);if(first.type!=value->type||first.stereo!=value->stereo||first.secondaryLineSide!=value->secondaryLineSide||first.visible!=value->visible)++changed;}
    for(const auto& [id,_]:firstBonds)if(!secondBonds.contains(id))++deleted;
    for(const auto& [id,value]:secondAdornments)if(!firstAdornments.contains(id))++addedAdornments;else if(firstAdornments.at(id)->text!=value->text)++changed;
    for(const auto& [id,_]:firstAdornments)if(!secondAdornments.contains(id))++deleted;
    const bool legacySpace=params.value("coordinate_space","")!="molecule_local_v2";
    return json({{"added_atoms",addedAtoms},{"added_bonds",addedBonds},{"added_adornments",addedAdornments},{"deleted_objects",deleted},{"moved_atoms",moved},{"changed_objects",changed},{"needs_review",params.value("needs_review",false)||legacySpace},{"legacy_coordinate_space",legacySpace}}).dump();
}
bool EditorSession::rebuildGradientStructure(const std::string& nodeId) {
    auto found=std::find_if(impl_->project.nodes.begin(),impl_->project.nodes.end(),[&](const ScriptNode& value){return value.id==nodeId;});if(found==impl_->project.nodes.end()||found->type!="molecule_gradient_structure")return false;
    const std::size_t index=static_cast<std::size_t>(std::distance(impl_->project.nodes.begin(),found));json params=json::parse(found->paramsJson);int startFrame=0;const auto start=structureBeforeNode(impl_->project,index,params.value("target",""),&startFrame);if(!start)return false;
    Project before=impl_->project;params["coordinate_space"]="molecule_local_v2";params["start_snapshot"]=moleculeSnapshotJson(*start);params["end_snapshot"]=moleculeSnapshotJson(*start);params["needs_review"]=false;found->paramsJson=params.dump();impl_->structureDraft=*start;impl_->previewFrame=startFrame+params.value("frames",30);impl_->targetKind=EditTargetKind::StructureSnapshot;impl_->targetId=nodeId;
    impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return true;
}
bool EditorSession::updateScene(const std::string& sceneJson) {
    const json value=json::parse(sceneJson);if(!value.is_object())throw std::runtime_error("Scene must be an object");Scene next=impl_->project.scene;
    next.width=value.value("width",next.width);next.height=value.value("height",next.height);next.logicWidth=value.value("logic_width",next.logicWidth);
    next.logicHeight=value.value("logic_height",next.logicHeight);next.fps=value.value("fps",next.fps);next.background=value.value("background",next.background);
    next.title=value.value("title",next.title);next.viewZoom=value.value("view_zoom",next.viewZoom);
    const Scene& old=impl_->project.scene;if(old.width==next.width&&old.height==next.height&&old.logicWidth==next.logicWidth&&old.logicHeight==next.logicHeight&&old.fps==next.fps&&old.background==next.background&&old.title==next.title&&old.viewZoom==next.viewZoom)return false;
    Project before=impl_->project;impl_->project.scene=std::move(next);impl_->undo.push_back({std::move(before),impl_->project,Impl::SnapshotDomain::Authoring});impl_->redo.clear();return true;
}
bool EditorSession::canUndo() const {
    if (impl_->undo.empty() || impl_->targetKind == EditTargetKind::TimelinePreview) return false;
    return impl_->undo.back().domain != Impl::SnapshotDomain::Structure || impl_->validStructureContext();
}
bool EditorSession::canRedo() const {
    if (impl_->redo.empty() || impl_->targetKind == EditTargetKind::TimelinePreview) return false;
    return impl_->redo.back().domain != Impl::SnapshotDomain::Structure || impl_->validStructureContext();
}
bool EditorSession::undo() { if (!canUndo()) return false; const auto high=impl_->project.nextCreationSerial;auto snapshot = std::move(impl_->undo.back()); impl_->undo.pop_back(); impl_->project = snapshot.before;impl_->project.nextCreationSerial=std::max(impl_->project.nextCreationSerial,high);impl_->redo.push_back(std::move(snapshot));impl_->normalizeContext();if(impl_->targetKind==EditTargetKind::StructureSnapshot)if(const ScriptNode* node=impl_->project.node(impl_->targetId))impl_->loadStructureDraft(*node);return true; }
bool EditorSession::redo() { if (!canRedo()) return false; const auto high=impl_->project.nextCreationSerial;auto snapshot = std::move(impl_->redo.back()); impl_->redo.pop_back(); impl_->project = snapshot.after;impl_->project.nextCreationSerial=std::max(impl_->project.nextCreationSerial,high);impl_->undo.push_back(std::move(snapshot));impl_->normalizeContext();if(impl_->targetKind==EditTargetKind::StructureSnapshot)if(const ScriptNode* node=impl_->project.node(impl_->targetId))impl_->loadStructureDraft(*node);return true; }

const char* toString(Tool value) {
    static constexpr const char* names[] = {"select_rectangle","select_lasso","move","eraser","atom_label","atom_text","charge_positive","charge_negative","single_bond","double_bond","triple_bond","solid_wedge","dashed_wedge","solid_bar","hashed_bar","wavy_bond","ring3","ring4","ring5","ring6","ring7","ring8","benzene"};
    return names[static_cast<int>(value)];
}
Tool toolFromString(const std::string& value) {
    for (int i = 0; i <= static_cast<int>(Tool::Benzene); ++i) if (value == toString(static_cast<Tool>(i))) return static_cast<Tool>(i);
    throw std::runtime_error("Unknown tool: " + value);
}

}  // namespace chem::core
