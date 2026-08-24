#pragma once

#include "Document.hpp"

#include <map>
#include <string>

namespace chem::core {

[[nodiscard]] double easingValue(Easing easing, double t);
[[nodiscard]] Molecule evaluateMolecule(const Project& project,
                                        const std::string& moleculeId,
                                        int frame);
[[nodiscard]] std::map<std::string, Molecule> evaluateProject(const Project& project, int frame);

}  // namespace chem::core
