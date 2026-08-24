#pragma once

#include "Document.hpp"

#include <filesystem>
#include <string>

namespace chem::core {

[[nodiscard]] std::string compileLua(const Project& project);
[[nodiscard]] std::filesystem::path writeMod(const Project& project,
                                             const std::filesystem::path& repositoryRoot);

}  // namespace chem::core
