#pragma once

#include "Document.hpp"

#include <string>

namespace chem::core {

[[nodiscard]] std::string compileLua(const Project& project);

}  // namespace chem::core
