#pragma once

#include "Document.hpp"
#include "Editing.hpp"

#include <cstdint>
#include <string>
#include <vector>

namespace chem::core {

struct AtomGeometry {
    std::string id;
    Point center;
    Rect labelBounds;
};

struct BondGeometry {
    std::string id;
    Point first;
    Point second;
    std::vector<Point> hitPolygon;
    BondType type = BondType::Single;
    SecondaryLineSide secondaryLineSide = SecondaryLineSide::Center;
    double lineSpacing = 0.0;
};

struct DepictionResult {
    int width = 0;
    int height = 0;
    std::string svg;
    Point modelOrigin;
    double modelScale = 1.0;
    Rect viewBox;
    std::vector<AtomGeometry> atoms;
    std::vector<BondGeometry> bonds;
};

struct RasterResult {
    int width = 0;
    int height = 0;
    std::vector<std::uint8_t> rgba;
};

class DepictionCore {
public:
    [[nodiscard]] DepictionResult depict(const Molecule& molecule, const Style& style,
                                         const Viewport& viewport) const;
    [[nodiscard]] RasterResult rasterize(const DepictionResult& depiction, double scale = 1.0) const;
};

[[nodiscard]] Molecule moleculeFromSmiles(const std::string& stableId,
                                          const std::string& name,
                                          const std::string& smiles);

}  // namespace chem::core
