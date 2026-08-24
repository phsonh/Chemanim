#pragma once

#include "Depiction.hpp"

#include <string>

namespace chem::core {

struct RasterProfile {
    double parseMs = 0.0;
    double rasterMs = 0.0;
};

[[nodiscard]] RasterResult rasterizeSvg(const std::string& svg, double scale,
                                        RasterProfile* profile = nullptr);

}  // namespace chem::core
