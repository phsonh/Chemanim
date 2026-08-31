#pragma once

#include "Document.hpp"

#include <string>
#include <vector>

namespace chem::core {

struct NodeTiming {
    std::string id;
    std::string type;
    std::string target;
    int startFrame = 0;
    int endFrame = 0;
    bool enabled = true;
};

struct ArrowState {
    std::string id;
    bool exists = false;
    bool visible = true;
    Point position;
    Point start;
    Point control1;
    Point control2;
    Point end;
    double progress = 0.0;
    double alpha = 255.0;
    double width = 3.0;
    double scaleX = 1.0;
    double scaleY = 1.0;
    double red = 25.0;
    double green = 25.0;
    double blue = 25.0;
};

struct GlobalNodeState {
    double moleculeAlpha = 255.0;
    double moleculeRed = 255.0;
    double moleculeGreen = 255.0;
    double moleculeBlue = 255.0;
    double moleculeScaleX = 1.0;
    double moleculeScaleY = 1.0;
    double arrowAlpha = 255.0;
    double arrowRed = 255.0;
    double arrowGreen = 255.0;
    double arrowBlue = 255.0;
    double arrowScaleX = 1.0;
    double arrowScaleY = 1.0;
    double arrowWidth = 1.0;
};

struct NodeDiagnostic {
    std::string nodeId;
    std::string severity;
    std::string message;
};

struct NodeMetadata {
    std::string category;
    std::string scope;
    std::string section;
    int order = 0;
    std::string exposure;
    std::string targetKind;
    std::string structureEditCapability;
    bool hasDuration = false;
    bool targetImmutable = false;
    bool showSection = true;
    std::string directManipulationCapability;
};

struct EvaluatedScene {
    std::map<std::string, Molecule> molecules;
    std::map<std::string, ArrowState> arrows;
    GlobalNodeState globals;
    std::vector<NodeDiagnostic> diagnostics;
};

[[nodiscard]] std::string nodeRegistryJson();
[[nodiscard]] std::string defaultNodeParamsJson(const std::string& type);
[[nodiscard]] const NodeMetadata& nodeMetadata(const std::string& type);
[[nodiscard]] std::vector<NodeTiming> compileNodeTimings(const Project& project);
[[nodiscard]] EvaluatedScene evaluateNodes(const Project& project, int frame);
// Evaluates local structure and object-local visual tracks without baking
// transforms into atom coordinates and without scene-global multipliers.
[[nodiscard]] EvaluatedScene evaluateLocalObjectNodes(const Project& project, int frame);
// Evaluates lifecycle, topology, stable-member structure and member-local
// tracks only. Object transforms and global visual tracks remain unapplied.
[[nodiscard]] EvaluatedScene evaluateStructureNodes(const Project& project, int frame);
[[nodiscard]] int nodeSequenceEndFrame(const Project& project);
// Stable IDs define correspondence. Transient ghost records produced here
// exist only for depiction and are never persisted into the project.
[[nodiscard]] Molecule blendMoleculeStructures(const Molecule& start,
                                                const Molecule& end,
                                                double progress);

}  // namespace chem::core
