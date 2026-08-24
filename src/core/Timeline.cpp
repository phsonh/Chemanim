#include "Timeline.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <vector>

namespace chem::core {
namespace {
struct Segment {
    int start = 0;
    int frames = 0;
    Point target;
    Easing easing = Easing::Linear;
    std::size_t order = 0;
    Point from;
};

Point interpolate(Point from, Point to, double t) {
    return {from.x + (to.x - from.x) * t, from.y + (to.y - from.y) * t};
}
Point evaluate(const std::vector<Segment>& segments, Point base, int frame) {
    Point value = base;
    for (const Segment& segment : segments) {
        if (frame < segment.start) break;
        const double t = segment.frames <= 0 ? 1.0 : static_cast<double>(frame - segment.start) / segment.frames;
        value = interpolate(segment.from, segment.target, easingValue(segment.easing, t));
    }
    return value;
}
}  // namespace

double easingValue(Easing easing, double t) {
    t = std::clamp(t, 0.0, 1.0);
    switch (easing) {
        case Easing::InQuad: return t * t;
        case Easing::OutQuad: return 1.0 - (1.0 - t) * (1.0 - t);
        case Easing::InOutQuad: return t < .5 ? 2*t*t : 1-std::pow(-2*t+2,2)/2;
        case Easing::SmoothStep: return t*t*(3-2*t);
        case Easing::Step: return t >= 1.0 ? 1.0 : 0.0;
        default: return t;
    }
}

Molecule evaluateMolecule(const Project& project, const std::string& moleculeId, int frame) {
    const Molecule* base = project.molecule(moleculeId);
    if (!base) throw std::runtime_error("Unknown molecule: " + moleculeId);
    Molecule result = *base;
    std::map<std::string, std::vector<Segment>> tracks;
    std::size_t order = 0;
    for (const AtomTween& tween : project.atomTweens) {
        if (tween.moleculeId == moleculeId && base->atom(tween.atomId)) tracks[tween.atomId].push_back({tween.startFrame,tween.frames,tween.target,tween.easing,order++});
    }
    for (const PoseTween& tween : project.poseTweens) {
        if (tween.moleculeId != moleculeId) { ++order; continue; }
        const auto pose = base->poses.find(tween.poseId);
        if (pose != base->poses.end()) for (const auto& [atomId, target] : pose->second.atomPositions) if (base->atom(atomId)) tracks[atomId].push_back({tween.startFrame,tween.frames,target,tween.easing,order});
        ++order;
    }
    for (auto& [atomId, segments] : tracks) {
        const Point initial = base->atom(atomId)->position;
        std::stable_sort(segments.begin(), segments.end(), [](const Segment& a, const Segment& b) { return a.start != b.start ? a.start < b.start : a.order < b.order; });
        std::vector<Segment> prepared; prepared.reserve(segments.size());
        for (Segment segment : segments) { segment.from = evaluate(prepared, initial, segment.start); prepared.push_back(segment); }
        if (Atom* atom = result.atom(atomId)) atom->position = evaluate(prepared, initial, frame);
    }
    return result;
}

std::map<std::string, Molecule> evaluateProject(const Project& project, int frame) {
    std::map<std::string, Molecule> result;
    for (const Molecule& molecule : project.molecules) result.emplace(molecule.id, evaluateMolecule(project,molecule.id,frame));
    return result;
}

}  // namespace chem::core
