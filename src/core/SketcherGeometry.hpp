#pragma once

#include "Document.hpp"

#include <vector>

namespace chem::core::sketcher_geometry {

[[nodiscard]] Point roundedDirection(Point start, Point cursor, double length,
                                     int fullTurnIncrements = 24);
[[nodiscard]] Point bestPlacementAroundOrigin(const std::vector<Point>& neighborOffsets,
                                              double length,
                                              bool limitSingleNeighborTo120 = true);

}  // namespace chem::core::sketcher_geometry
