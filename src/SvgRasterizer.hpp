#pragma once

#include <string>

#include <raylib.h>
#include "core/SvgRaster.hpp"

namespace chem {

Image rasterizeSvg(const std::string& svg, float scale, core::RasterProfile* profile = nullptr);

} // namespace chem
