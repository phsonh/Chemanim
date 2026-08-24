#include "Editing.hpp"
#include "Nodes.hpp"
#include "SketcherGeometry.hpp"
#include "Timeline.hpp"

#include <nlohmann/json.hpp>

#include <algorithm>
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
    return tool >= Tool::SingleBond && tool <= Tool::WavyBond;
}
bool isRingTool(Tool tool) { return tool >= Tool::Ring3 && tool <= Tool::Benzene; }
int ringSize(Tool tool) { return tool == Tool::Benzene ? 6 : 3 + static_cast<int>(tool) - static_cast<int>(Tool::Ring3); }
std::pair<BondType, BondStereo> bondStyle(Tool tool) {
    switch (tool) {
        case Tool::DoubleBond: return {BondType::Double, BondStereo::None};
        case Tool::TripleBond: return {BondType::Triple, BondStereo::None};
        case Tool::AromaticBond: return {BondType::Aromatic, BondStereo::None};
        case Tool::SolidWedge: return {BondType::Single, BondStereo::SolidWedge};
        case Tool::DashedWedge: return {BondType::Single, BondStereo::DashedWedge};
        case Tool::WavyBond: return {BondType::Single, BondStereo::Wavy};
        default: return {BondType::Single, BondStereo::None};
    }
}
Point snappedDirection(Point start, Point raw, double length, bool disableAngle) {
    if (disableAngle) return raw;
    return sketcher_geometry::roundedDirection(start, raw, length, 24);
}
std::vector<Point> neighborOffsets(const Molecule& molecule, const Atom& atom) {
    std::vector<Point> result;
    for (const Bond& bond : molecule.bonds) {
        const std::string* otherId = nullptr;
        if (bond.atomA == atom.id) otherId = &bond.atomB;
        else if (bond.atomB == atom.id) otherId = &bond.atomA;
        if (otherId) if (const Atom* other = molecule.atom(*otherId)) {
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
BondType stableAromaticDisplay(const std::string& id) {
    try { return (std::stoull(id.size()>1?id.substr(1):id)%2)?BondType::Double:BondType::Single; }
    catch (...) { return BondType::Single; }
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
    EditTargetKind targetKind = EditTargetKind::BaseStructure;
    std::string targetId;
    int previewFrame = 0;
    struct Snapshot { Project before; Project after; };
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
        GesturePreviewKind previewKind = GesturePreviewKind::None;
        bool changed = false;
    };
    std::optional<Gesture> gesture;

    Molecule* molecule() { return project.molecule(activeMolecule); }
    const Molecule* molecule() const { return project.molecule(activeMolecule); }

    Molecule displayed() const {
        Molecule result = targetKind == EditTargetKind::BaseStructure ? *molecule() : evaluateMolecule(project, activeMolecule, previewFrame);
        if (gesture && targetKind != EditTargetKind::BaseStructure && targetKind != EditTargetKind::TimelinePreview) for (const auto& [id, position] : gesture->targetPositions) if (Atom* atom = result.atom(id)) atom->position = position;
        return result;
    }

    Hit hit(Point canvasPoint, std::optional<std::string> ignoreAtom = std::nullopt) const {
        if (!molecule()) return {};
        const Molecule displayedMolecule = displayed(); const Molecule* value = &displayedMolecule;
        Hit best;
        best.distance = 1e9;
        for (const Atom& atom : value->atoms) {
            if (ignoreAtom && atom.id == *ignoreAtom) continue;
            const double d = distance(canvasPoint, viewport.modelToCanvas(atom.position));
            if (d <= 14.0 && d < best.distance) best = {HitKind::Atom, atom.id, d};
        }
        if (best.kind == HitKind::Atom) return best;
        for (const Bond& bond : value->bonds) {
            const Atom* a = value->atom(bond.atomA); const Atom* b = value->atom(bond.atomB);
            if (!a || !b) continue;
            const double d = pointSegmentDistance(canvasPoint, viewport.modelToCanvas(a->position), viewport.modelToCanvas(b->position));
            if (d <= 9.0 && d < best.distance) best = {HitKind::Bond, bond.id, d};
        }
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
            const Hit snap = hit(gesture->currentCanvas, gesture->startHit.kind == HitKind::Atom ? std::optional(gesture->startHit.id) : std::nullopt);
            if (snap.kind == HitKind::Atom) value.preview.snapAtomId = snap.id;
        }
        return value;
    }

    Point gestureEndpoint(bool alt) const {
        if (!gesture) return {};
        const Molecule* value = molecule();
        const Hit near = hit(gesture->currentCanvas, gesture->startHit.kind == HitKind::Atom ? std::optional(gesture->startHit.id) : std::nullopt);
        if (near.kind == HitKind::Atom && value) return value->atom(near.id)->position;
        const double length = value ? value->referenceBondLength : 1.5;
        if (value && gesture->startHit.kind == HitKind::Atom &&
            distance(gesture->pressCanvas, gesture->currentCanvas) <= 12.0) {
            if (const Atom* atom = value->atom(gesture->startHit.id)) {
                const Point offset = sketcher_geometry::bestPlacementAroundOrigin(
                    neighborOffsets(*value, *atom), length);
                return {atom->position.x + offset.x, atom->position.y + offset.y};
            }
        }
        const Point candidate = snappedDirection(
            gesture->startModel, viewport.canvasToModel(gesture->currentCanvas), length, alt);
        // Endpoint atom snapping wins over angular snapping, including when the
        // rounded endpoint (rather than the raw cursor) lands on an atom.
        const Hit snappedHit = hit(viewport.modelToCanvas(candidate),
                                   gesture->startHit.kind == HitKind::Atom
                                       ? std::optional(gesture->startHit.id)
                                       : std::nullopt);
        if (snappedHit.kind == HitKind::Atom && value) return value->atom(snappedHit.id)->position;
        return candidate;
    }

    std::vector<Point> ringPolygon(int count, Point cursor) const {
        const Molecule* value = molecule();
        if (!value || !gesture) return {};
        const double side = value->referenceBondLength;
        const double radius = side / (2.0 * std::sin(std::numbers::pi / count));
        std::vector<Point> result;
        if (gesture->startHit.kind == HitKind::Bond) {
            const Bond* bond = value->bond(gesture->startHit.id); const Atom* a = bond ? value->atom(bond->atomA) : nullptr; const Atom* b = bond ? value->atom(bond->atomB) : nullptr;
            if (!a || !b) return {};
            const Point mid{(a->position.x + b->position.x) * .5, (a->position.y + b->position.y) * .5};
            const Point delta{b->position.x - a->position.x, b->position.y - a->position.y};
            const double actual = std::max(1e-9, std::hypot(delta.x, delta.y));
            const Point normal{-delta.y / actual, delta.x / actual};
            const double apothem = actual * .5 / std::tan(std::numbers::pi / count);
            const Point modelCursor = viewport.canvasToModel(cursor);
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
            const double direction = sign > 0 ? -1.0 : 1.0;
            for (int i = 0; i < count; ++i) result.push_back({center.x + radius * std::cos(startAngle + direction * i * 2 * std::numbers::pi / count), center.y + radius * std::sin(startAngle + direction * i * 2 * std::numbers::pi / count)});
            result[0] = a->position; result[1] = b->position;
            return result;
        }
        Point vertex = gesture->startModel;
        if (gesture->startHit.kind == HitKind::Atom) vertex = value->atom(gesture->startHit.id)->position;
        Point direction;
        if (gesture->startHit.kind == HitKind::Atom && distance(gesture->pressCanvas, cursor) <= 12.0) {
            const Atom* atom = value->atom(gesture->startHit.id);
            const Point offset = sketcher_geometry::bestPlacementAroundOrigin(neighborOffsets(*value, *atom), side);
            direction = {vertex.x + offset.x, vertex.y + offset.y};
        } else {
            direction = snappedDirection(vertex, viewport.canvasToModel(cursor), side, false);
        }
        double firstAngle = std::atan2(direction.y - vertex.y, direction.x - vertex.x);
        Point center{vertex.x + radius * std::cos(firstAngle + std::numbers::pi * .5 - std::numbers::pi / count),
                     vertex.y + radius * std::sin(firstAngle + std::numbers::pi * .5 - std::numbers::pi / count)};
        const double startAngle = std::atan2(vertex.y - center.y, vertex.x - center.x);
        for (int i = 0; i < count; ++i) result.push_back({center.x + radius * std::cos(startAngle - i * 2 * std::numbers::pi / count), center.y + radius * std::sin(startAngle - i * 2 * std::numbers::pi / count)});
        result[0] = vertex;
        return result;
    }

    void commit() {
        if (!gesture || !gesture->changed) { gesture.reset(); return; }
        undo.push_back({std::move(gesture->before), project});
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
void EditorSession::setTool(Tool tool) { impl_->tool = tool; impl_->gesture.reset(); }
Tool EditorSession::tool() const { return impl_->tool; }
void EditorSession::setElement(std::string element) { impl_->element = std::move(element); }
void EditorSession::setViewport(Viewport viewport) { impl_->viewport = viewport; }
const Viewport& EditorSession::viewport() const { return impl_->viewport; }
void EditorSession::editBaseStructure(int previewFrame) { impl_->targetKind=EditTargetKind::BaseStructure; impl_->targetId.clear(); impl_->previewFrame=previewFrame; impl_->gesture.reset(); }
void EditorSession::previewTimeline(int frame) { impl_->targetKind=EditTargetKind::TimelinePreview; impl_->targetId.clear(); impl_->previewFrame=frame; impl_->tool=Tool::SelectRectangle; impl_->gesture.reset(); }
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
    impl_->previewFrame=found==timings.end()?0:found->endFrame; impl_->targetKind=EditTargetKind::ScriptNode; impl_->targetId=nodeId;
    impl_->tool=Tool::SelectRectangle; impl_->gesture.reset();
}
EditTargetKind EditorSession::editTargetKind() const { return impl_->targetKind; }
Molecule EditorSession::displayMolecule() const { if(!impl_->molecule()) throw std::runtime_error("No active molecule"); return impl_->displayed(); }
Hit EditorSession::hitTest(Point canvasPoint) const { return impl_->hit(canvasPoint); }

EditResult EditorSession::pointerDown(Point canvasPoint, bool, bool control, bool shift) {
    Molecule* molecule = impl_->molecule();
    if (!molecule) return impl_->result(canvasPoint);
    const Point pressModel = impl_->viewport.canvasToModel(canvasPoint);
    Impl::Gesture gesture{.before = impl_->project, .pressCanvas = canvasPoint, .pressModel = pressModel,
                          .startCanvas = canvasPoint, .currentCanvas = canvasPoint,
                          .startModel = pressModel, .startHit = impl_->hit(canvasPoint)};
    if (isBondTool(impl_->tool)) gesture.previewKind=GesturePreviewKind::Bond;
    else if (isRingTool(impl_->tool)) gesture.previewKind=GesturePreviewKind::Ring;
    else if (impl_->tool==Tool::SelectLasso) gesture.previewKind=gesture.startHit.kind==HitKind::Atom?GesturePreviewKind::Move:GesturePreviewKind::Lasso;
    else if (impl_->tool==Tool::SelectRectangle) gesture.previewKind=gesture.startHit.kind==HitKind::Atom?GesturePreviewKind::Move:GesturePreviewKind::Rectangle;
    else if (impl_->tool==Tool::Move) gesture.previewKind=GesturePreviewKind::Move;
    if (gesture.startHit.kind == HitKind::Atom) {
        const Molecule shown = impl_->displayed();
        if (const Atom* atom = shown.atom(gesture.startHit.id)) {
            gesture.startModel = atom->position;
            gesture.startCanvas = impl_->viewport.modelToCanvas(atom->position);
        }
    }
    if (impl_->tool == Tool::SelectLasso) gesture.lasso.push_back(canvasPoint);
    if (impl_->tool == Tool::Move || impl_->tool == Tool::SelectRectangle || impl_->tool == Tool::SelectLasso) {
        if (gesture.startHit.kind == HitKind::Atom) {
            if (control) {
                if (impl_->selectedAtoms.contains(gesture.startHit.id)) impl_->selectedAtoms.erase(gesture.startHit.id); else impl_->selectedAtoms.insert(gesture.startHit.id);
            } else if (shift) {
                impl_->selectedAtoms.insert(gesture.startHit.id);
            } else if (!impl_->selectedAtoms.contains(gesture.startHit.id)) {
                impl_->selectedAtoms = {gesture.startHit.id}; impl_->selectedBonds.clear();
            }
            if (impl_->targetKind != EditTargetKind::TimelinePreview) { const Molecule shown=impl_->displayed(); for (const std::string& id : impl_->selectedAtoms) if (const Atom* atom = shown.atom(id)) gesture.original[id] = atom->position; }
        } else if (!control && !shift) { impl_->selectedAtoms.clear(); impl_->selectedBonds.clear(); }
    }
    impl_->gesture = std::move(gesture);
    return impl_->result(canvasPoint);
}

EditResult EditorSession::pointerMove(Point canvasPoint, bool alt, bool, bool) {
    if (!impl_->gesture) return impl_->result(canvasPoint);
    impl_->gesture->currentCanvas = canvasPoint;
    Molecule* molecule = impl_->molecule();
    if (!molecule) return impl_->result(canvasPoint);
    if ((impl_->tool == Tool::Move || impl_->tool == Tool::SelectRectangle || impl_->tool == Tool::SelectLasso) && !impl_->gesture->original.empty()) {
        const Point current = impl_->viewport.canvasToModel(canvasPoint);
        const Point delta{current.x - impl_->gesture->pressModel.x, current.y - impl_->gesture->pressModel.y};
        for (const auto& [id, position] : impl_->gesture->original) {
            const Point target{position.x + delta.x, position.y + delta.y};
            if (impl_->targetKind == EditTargetKind::BaseStructure) { if (Atom* atom = molecule->atom(id)) atom->position = target; }
            else impl_->gesture->targetPositions[id] = target;
        }
        impl_->gesture->changed = std::hypot(delta.x, delta.y) > 1e-9;
    } else if (impl_->tool == Tool::SelectLasso) {
        if (impl_->gesture->lasso.empty() || distance(canvasPoint, impl_->gesture->lasso.back()) > 3.0) impl_->gesture->lasso.push_back(canvasPoint);
    } else if (isBondTool(impl_->tool)) {
        impl_->gesture->currentCanvas = impl_->viewport.modelToCanvas(impl_->gestureEndpoint(alt));
    } else if (isRingTool(impl_->tool)) {
        impl_->gesture->lasso.clear();
        for (Point point : impl_->ringPolygon(ringSize(impl_->tool), canvasPoint)) impl_->gesture->lasso.push_back(impl_->viewport.modelToCanvas(point));
    }
    return impl_->result(canvasPoint);
}

EditResult EditorSession::pointerUp(Point canvasPoint, bool alt, bool control, bool) {
    if (!impl_->gesture) return impl_->result(canvasPoint);
    impl_->gesture->currentCanvas = canvasPoint;
    Molecule* molecule = impl_->molecule();
    if (!molecule) { impl_->gesture.reset(); return impl_->result(canvasPoint); }
    if (impl_->targetKind != EditTargetKind::BaseStructure) {
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
            }
        }
    } else if (impl_->tool == Tool::SelectRectangle && impl_->gesture->original.empty()) {
        const double left = std::min(impl_->gesture->pressCanvas.x, canvasPoint.x), right = std::max(impl_->gesture->pressCanvas.x, canvasPoint.x);
        const double top = std::min(impl_->gesture->pressCanvas.y, canvasPoint.y), bottom = std::max(impl_->gesture->pressCanvas.y, canvasPoint.y);
        if (!control) impl_->selectedAtoms.clear();
        for (const Atom& atom : molecule->atoms) if (Rect{left, top, right, bottom}.contains(impl_->viewport.modelToCanvas(atom.position))) impl_->selectedAtoms.insert(atom.id);
    } else if (impl_->tool == Tool::SelectLasso && impl_->gesture->lasso.size() >= 3) {
        if (!control) impl_->selectedAtoms.clear();
        for (const Atom& atom : molecule->atoms) if (pointInPolygon(impl_->viewport.modelToCanvas(atom.position), impl_->gesture->lasso)) impl_->selectedAtoms.insert(atom.id);
    } else if (isBondTool(impl_->tool)) {
        const auto [type, stereo] = bondStyle(impl_->tool);
        if (impl_->gesture->startHit.kind == HitKind::Bond && distance(impl_->gesture->startCanvas, canvasPoint) < 5.0) {
            if (Bond* bond = molecule->bond(impl_->gesture->startHit.id)) {
                bond->type = type; bond->displayType = type==BondType::Aromatic ? std::optional<BondType>(stableAromaticDisplay(bond->id)) : std::nullopt;
                bond->stereo = stereo; impl_->gesture->changed = true;
            }
        } else {
            std::string first = impl_->gesture->startHit.kind == HitKind::Atom ? impl_->gesture->startHit.id : molecule->addAtom(impl_->gesture->startModel);
            const Point endpoint = impl_->gestureEndpoint(alt);
            const Hit endpointHit = impl_->hit(impl_->viewport.modelToCanvas(endpoint),
                                               impl_->gesture->startHit.kind == HitKind::Atom
                                                   ? std::optional(impl_->gesture->startHit.id)
                                                   : std::nullopt);
            std::string second = endpointHit.kind == HitKind::Atom ? endpointHit.id : molecule->addAtom(endpoint);
            if (first != second) {
                const std::string bondId = molecule->addBond(first, second, type, stereo);
                impl_->gesture->changed = !bondId.empty();
                impl_->selectedAtoms = {second};
            }
        }
    } else if (isRingTool(impl_->tool)) {
        const int count = ringSize(impl_->tool); const std::vector<Point> polygon = impl_->ringPolygon(count, canvasPoint);
        if (static_cast<int>(polygon.size()) == count) {
            std::vector<std::string> ids(count);
            if (impl_->gesture->startHit.kind == HitKind::Atom) ids[0] = impl_->gesture->startHit.id;
            if (impl_->gesture->startHit.kind == HitKind::Bond) { if (const Bond* bond = molecule->bond(impl_->gesture->startHit.id)) { ids[0] = bond->atomA; ids[1] = bond->atomB; } }
            for (int i = 0; i < count; ++i) if (ids[i].empty()) ids[i] = molecule->addAtom(polygon[i]);
            for (int i = 0; i < count; ++i) {
                if (impl_->gesture->startHit.kind == HitKind::Bond && i == 0) continue;
                const BondType type = impl_->tool == Tool::Benzene ? BondType::Aromatic : BondType::Single;
                const std::string bondId = molecule->addBond(ids[i], ids[(i + 1) % count], type);
                if(impl_->tool==Tool::Benzene)if(Bond* bond=molecule->bond(bondId)){bond->displayType=i%2?BondType::Double:BondType::Single;bond->visible=true;}
                (void)bondId;
            }
            if(impl_->tool==Tool::Benzene)for(const std::string& id:ids)if(Atom* atom=molecule->atom(id))atom->aromatic=true;
            impl_->selectedAtoms = std::set<std::string>(ids.begin(), ids.end()); impl_->gesture->changed = true;
        }
    } else if (impl_->tool == Tool::AtomLabel) {
        if (impl_->gesture->startHit.kind == HitKind::Atom) molecule->atom(impl_->gesture->startHit.id)->element = impl_->element;
        else {
            const std::string atomId = molecule->addAtom(impl_->gesture->startModel, impl_->element);
            (void)atomId;
        }
        impl_->gesture->changed = true;
    } else if (impl_->tool == Tool::ChargePositive || impl_->tool == Tool::ChargeNegative) {
        if (impl_->gesture->startHit.kind == HitKind::Atom) { molecule->atom(impl_->gesture->startHit.id)->formalCharge += impl_->tool == Tool::ChargePositive ? 1 : -1; impl_->gesture->changed = true; }
    } else if (impl_->tool == Tool::Eraser) {
        if (impl_->gesture->startHit.kind == HitKind::Atom) impl_->gesture->changed = molecule->removeAtom(impl_->gesture->startHit.id);
        else if (impl_->gesture->startHit.kind == HitKind::Bond) impl_->gesture->changed = molecule->removeBond(impl_->gesture->startHit.id);
    }
    const bool changed = impl_->gesture->changed;
    impl_->commit();
    EditResult result = impl_->result(canvasPoint); result.changed = changed; return result;
}

void EditorSession::cancelGesture() { if (impl_->gesture) { impl_->project = std::move(impl_->gesture->before); impl_->gesture.reset(); } }
bool EditorSession::deleteSelection() {
    Molecule* molecule = impl_->molecule(); if (!molecule) return false;
    Project before = impl_->project; bool changed = false;
    for (const std::string& id : impl_->selectedBonds) changed |= molecule->removeBond(id);
    for (const std::string& id : impl_->selectedAtoms) changed |= molecule->removeAtom(id);
    if (changed) { impl_->undo.push_back({std::move(before), impl_->project}); impl_->redo.clear(); impl_->selectedAtoms.clear(); impl_->selectedBonds.clear(); }
    return changed;
}
bool EditorSession::setAtomPosition(const std::string& atomId, Point position) {
    Molecule* molecule = impl_->molecule(); Atom* atom = molecule ? molecule->atom(atomId) : nullptr;
    if (!atom || (atom->position.x == position.x && atom->position.y == position.y)) return false;
    Project before = impl_->project; atom->position = position; impl_->undo.push_back({std::move(before), impl_->project}); impl_->redo.clear(); return true;
}
bool EditorSession::setAtomElement(const std::string& atomId, std::string element) {
    Molecule* molecule = impl_->molecule(); Atom* atom = molecule ? molecule->atom(atomId) : nullptr;
    if (!atom || atom->element == element || element.empty()) return false;
    Project before = impl_->project; atom->element = std::move(element); impl_->undo.push_back({std::move(before), impl_->project}); impl_->redo.clear(); return true;
}
bool EditorSession::changeAtomCharge(const std::string& atomId, int delta) {
    Molecule* molecule = impl_->molecule(); Atom* atom = molecule ? molecule->atom(atomId) : nullptr;
    if (!atom || delta == 0) return false;
    Project before = impl_->project; atom->formalCharge += delta; impl_->undo.push_back({std::move(before), impl_->project}); impl_->redo.clear(); return true;
}
std::string EditorSession::addScriptNode(const std::string& type,const std::string& paramsJson,std::optional<std::size_t> index) {
    Project before=impl_->project; const std::string id=impl_->project.addNode(type,paramsJson,index);
    impl_->undo.push_back({std::move(before),impl_->project});impl_->redo.clear();return id;
}
bool EditorSession::updateScriptNode(const std::string& nodeId,const std::string& paramsJson) {
    ScriptNode* node=impl_->project.node(nodeId);if(!node)return false;const json value=json::parse(paramsJson);
    if(!value.is_object())throw std::runtime_error("Node params must be an object");const std::string normalized=value.dump();
    if(node->paramsJson==normalized)return false;Project before=impl_->project;node->paramsJson=normalized;
    impl_->undo.push_back({std::move(before),impl_->project});impl_->redo.clear();return true;
}
bool EditorSession::setScriptNodeEnabled(const std::string& nodeId,bool enabled) {
    ScriptNode* node=impl_->project.node(nodeId);if(!node||node->enabled==enabled)return false;Project before=impl_->project;node->enabled=enabled;
    impl_->undo.push_back({std::move(before),impl_->project});impl_->redo.clear();return true;
}
bool EditorSession::moveScriptNode(const std::string& nodeId,std::size_t index) {
    auto found=std::find_if(impl_->project.nodes.begin(),impl_->project.nodes.end(),[&](const ScriptNode& value){return value.id==nodeId;});
    if(found==impl_->project.nodes.end()||found->type=="scene")return false;const std::size_t old=static_cast<std::size_t>(std::distance(impl_->project.nodes.begin(),found));
    if(!impl_->project.nodes.empty()&&impl_->project.nodes.front().type=="scene")index=std::max<std::size_t>(1,index);
    index=std::min(index,impl_->project.nodes.size()-1);if(old==index)return false;Project before=impl_->project;ScriptNode value=std::move(*found);
    impl_->project.nodes.erase(impl_->project.nodes.begin()+static_cast<std::ptrdiff_t>(old));
    impl_->project.nodes.insert(impl_->project.nodes.begin()+static_cast<std::ptrdiff_t>(index),std::move(value));
    impl_->undo.push_back({std::move(before),impl_->project});impl_->redo.clear();return true;
}
std::string EditorSession::duplicateScriptNode(const std::string& nodeId) {
    const ScriptNode* node=impl_->project.node(nodeId);if(!node||node->type=="scene")return{};const auto found=std::find_if(impl_->project.nodes.begin(),impl_->project.nodes.end(),[&](const ScriptNode& value){return value.id==nodeId;});
    const std::size_t index=static_cast<std::size_t>(std::distance(impl_->project.nodes.begin(),found))+1;return addScriptNode(node->type,node->paramsJson,index);
}
bool EditorSession::deleteScriptNode(const std::string& nodeId) {
    const auto found=std::find_if(impl_->project.nodes.begin(),impl_->project.nodes.end(),[&](const ScriptNode& value){return value.id==nodeId;});
    if(found==impl_->project.nodes.end()||found->type=="scene")return false;Project before=impl_->project;impl_->project.nodes.erase(found);
    impl_->undo.push_back({std::move(before),impl_->project});impl_->redo.clear();return true;
}
bool EditorSession::updateScene(const std::string& sceneJson) {
    const json value=json::parse(sceneJson);if(!value.is_object())throw std::runtime_error("Scene must be an object");Scene next=impl_->project.scene;
    next.width=value.value("width",next.width);next.height=value.value("height",next.height);next.logicWidth=value.value("logic_width",next.logicWidth);
    next.logicHeight=value.value("logic_height",next.logicHeight);next.fps=value.value("fps",next.fps);next.background=value.value("background",next.background);
    next.title=value.value("title",next.title);next.viewZoom=value.value("view_zoom",next.viewZoom);
    const Scene& old=impl_->project.scene;if(old.width==next.width&&old.height==next.height&&old.logicWidth==next.logicWidth&&old.logicHeight==next.logicHeight&&old.fps==next.fps&&old.background==next.background&&old.title==next.title&&old.viewZoom==next.viewZoom)return false;
    Project before=impl_->project;impl_->project.scene=std::move(next);impl_->undo.push_back({std::move(before),impl_->project});impl_->redo.clear();return true;
}
bool EditorSession::canUndo() const { return !impl_->undo.empty(); }
bool EditorSession::canRedo() const { return !impl_->redo.empty(); }
bool EditorSession::undo() { if (impl_->undo.empty()) return false; auto snapshot = std::move(impl_->undo.back()); impl_->undo.pop_back(); impl_->project = snapshot.before; impl_->redo.push_back(std::move(snapshot)); return true; }
bool EditorSession::redo() { if (impl_->redo.empty()) return false; auto snapshot = std::move(impl_->redo.back()); impl_->redo.pop_back(); impl_->project = snapshot.after; impl_->undo.push_back(std::move(snapshot)); return true; }

const char* toString(Tool value) {
    static constexpr const char* names[] = {"select_rectangle","select_lasso","move","eraser","atom_label","charge_positive","charge_negative","single_bond","double_bond","triple_bond","aromatic_bond","solid_wedge","dashed_wedge","wavy_bond","ring3","ring4","ring5","ring6","ring7","ring8","benzene"};
    return names[static_cast<int>(value)];
}
Tool toolFromString(const std::string& value) {
    for (int i = 0; i <= static_cast<int>(Tool::Benzene); ++i) if (value == toString(static_cast<Tool>(i))) return static_cast<Tool>(i);
    throw std::runtime_error("Unknown tool: " + value);
}

}  // namespace chem::core
