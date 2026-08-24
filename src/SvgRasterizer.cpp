#include "SvgRasterizer.hpp"
#include "core/SvgRaster.hpp"

#include <cstring>

namespace chem {

Image rasterizeSvg(const std::string& svg, float scale, core::RasterProfile* profile) {
    const core::RasterResult raster = core::rasterizeSvg(svg, scale, profile);
    Image result = GenImageColor(raster.width, raster.height, BLANK);
    std::memcpy(result.data, raster.rgba.data(), raster.rgba.size());
    return result;
}

} // namespace chem
