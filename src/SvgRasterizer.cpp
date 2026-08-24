#include "SvgRasterizer.hpp"

#define NANOSVG_IMPLEMENTATION
#include <nanosvg.h>
#define NANOSVGRAST_IMPLEMENTATION
#include <nanosvgrast.h>

#include <algorithm>
#include <cmath>
#include <cstring>
#include <stdexcept>
#include <vector>

namespace chem {

Image rasterizeSvg(const std::string& svg, float scale) {
    if (svg.empty()) throw std::runtime_error("Native molecule is missing its RDKit ACS1996 SVG");
    std::vector<char> source(svg.begin(), svg.end());
    source.push_back('\0');
    NSVGimage* parsed = nsvgParse(source.data(), "px", 96.0f);
    if (!parsed) throw std::runtime_error("Unable to parse RDKit ACS1996 SVG");
    scale = std::max(0.01f, scale);
    const int width = std::max(1, static_cast<int>(std::ceil(parsed->width * scale)));
    const int height = std::max(1, static_cast<int>(std::ceil(parsed->height * scale)));
    std::vector<unsigned char> pixels(static_cast<std::size_t>(width) * height * 4, 0);
    NSVGrasterizer* rasterizer = nsvgCreateRasterizer();
    if (!rasterizer) {
        nsvgDelete(parsed);
        throw std::runtime_error("Unable to create SVG rasterizer");
    }
    nsvgRasterize(rasterizer, parsed, 0, 0, scale, pixels.data(), width, height, width * 4);
    Image result = GenImageColor(width, height, BLANK);
    std::memcpy(result.data, pixels.data(), pixels.size());
    nsvgDeleteRasterizer(rasterizer);
    nsvgDelete(parsed);
    return result;
}

} // namespace chem
