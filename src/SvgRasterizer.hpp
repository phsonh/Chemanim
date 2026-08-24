#pragma once

#include <string>

#include <raylib.h>

namespace chem {

Image rasterizeSvg(const std::string& svg, float scale);

} // namespace chem
