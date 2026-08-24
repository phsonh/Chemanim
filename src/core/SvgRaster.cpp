#include "SvgRaster.hpp"

#define NANOSVG_IMPLEMENTATION
#include <nanosvg.h>
#define NANOSVGRAST_IMPLEMENTATION
#include <nanosvgrast.h>

#include <algorithm>
#include <cmath>
#include <chrono>
#include <stdexcept>

namespace chem::core {

RasterResult rasterizeSvg(const std::string& svg, double scale, RasterProfile* profile) {
    if (svg.empty()) throw std::runtime_error("Cannot rasterize an empty SVG");
    std::vector<char> source(svg.begin(), svg.end()); source.push_back('\0');
    const auto parseStart = std::chrono::steady_clock::now();
    NSVGimage* parsed = nsvgParse(source.data(), "px", 96.0f);
    if (profile) profile->parseMs += std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now()-parseStart).count();
    if (!parsed) throw std::runtime_error("NanoSVG could not parse the RDKit drawing");
    scale = std::max(0.01, scale);
    RasterResult result;
    result.width = std::max(1, static_cast<int>(std::ceil(parsed->width * scale)));
    result.height = std::max(1, static_cast<int>(std::ceil(parsed->height * scale)));
    result.rgba.resize(static_cast<std::size_t>(result.width) * result.height * 4, 0);
    NSVGrasterizer* rasterizer = nsvgCreateRasterizer();
    if (!rasterizer) { nsvgDelete(parsed); throw std::runtime_error("NanoSVG rasterizer allocation failed"); }
    const auto rasterStart = std::chrono::steady_clock::now();
    nsvgRasterize(rasterizer, parsed, 0, 0, static_cast<float>(scale), result.rgba.data(), result.width, result.height, result.width * 4);
    if (profile) profile->rasterMs += std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now()-rasterStart).count();
    nsvgDeleteRasterizer(rasterizer); nsvgDelete(parsed);
    return result;
}

}  // namespace chem::core
