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
    double red = 25.0;
    double green = 25.0;
    double blue = 25.0;
};

struct EvaluatedScene {
    std::map<std::string, Molecule> molecules;
    std::map<std::string, ArrowState> arrows;
};

[[nodiscard]] std::string nodeRegistryJson();
[[nodiscard]] std::string defaultNodeParamsJson(const std::string& type);
[[nodiscard]] std::vector<NodeTiming> compileNodeTimings(const Project& project);
[[nodiscard]] EvaluatedScene evaluateNodes(const Project& project, int frame);
[[nodiscard]] int nodeSequenceEndFrame(const Project& project);

}  // namespace chem::core
