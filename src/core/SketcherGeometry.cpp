// Adapted from Schrödinger 2D Sketcher at fixed commit
// bbfa930e77c09545df165bc75e618bfe93396bbd:
//   molviewer/coord_utils.cpp::best_placing_around_origin()
//   molviewer/coord_utils.cpp::get_rounded_angle_radians()
// Copyright (c) 2024, Schrodinger, LLC. BSD-3-Clause.
// See THIRD_PARTY_NOTICES.md.

#include "SketcherGeometry.hpp"

#include <algorithm>
#include <cmath>
#include <numbers>
#include <ranges>

namespace chem::core::sketcher_geometry {
namespace {
constexpr double fullTurn = 2.0 * std::numbers::pi;

double normalizedAngle(double angle) {
    angle = std::fmod(angle, fullTurn);
    return angle < 0.0 ? angle + fullTurn : angle;
}

double horizontalDistance(double angle) {
    angle = normalizedAngle(angle);
    return std::min({angle, std::abs(angle - std::numbers::pi), fullTurn - angle});
}
}  // namespace

Point roundedDirection(Point start, Point cursor, double length, int fullTurnIncrements) {
    const double angle = std::atan2(cursor.y - start.y, cursor.x - start.x);
    const double increments = static_cast<double>(fullTurnIncrements);
    const double rounded = std::round(angle * increments / fullTurn) / increments * fullTurn;
    return {start.x + length * std::cos(rounded), start.y + length * std::sin(rounded)};
}

Point bestPlacementAroundOrigin(const std::vector<Point>& neighborOffsets, double length,
                                bool limitSingleNeighborTo120) {
    if (neighborOffsets.empty()) return {length, 0.0};

    std::vector<double> angles;
    angles.reserve(neighborOffsets.size() + 1);
    for (const Point point : neighborOffsets) angles.push_back(normalizedAngle(std::atan2(point.y, point.x)));
    std::ranges::sort(angles);
    angles.push_back(angles.front() + fullTurn);

    // Match the upstream tolerance and deterministic horizontal tie-break.
    constexpr double tolerance = 1.01;
    double bestHalfGap = 0.5 * (angles[1] - angles[0]);
    std::vector<std::size_t> tied{0};
    for (std::size_t index = 0; index + 1 < angles.size(); ++index) {
        const double halfGap = 0.5 * (angles[index + 1] - angles[index]);
        if (halfGap > bestHalfGap * tolerance) {
            bestHalfGap = halfGap;
            tied.assign(1, index);
        } else if (halfGap > bestHalfGap / tolerance) {
            tied.push_back(index);
        }
    }
    std::size_t best = tied.front();
    for (const std::size_t candidate : tied) {
        const double candidateMidpoint = angles[candidate] + 0.5 * (angles[candidate + 1] - angles[candidate]);
        const double bestMidpoint = angles[best] + 0.5 * (angles[best + 1] - angles[best]);
        if (horizontalDistance(candidateMidpoint) + 1e-12 < horizontalDistance(bestMidpoint)) best = candidate;
    }

    const bool limitTo120 = limitSingleNeighborTo120 && neighborOffsets.size() == 1;
    const double maximum = limitTo120 ? 2.0 * std::numbers::pi / 3.0 : std::numbers::pi;
    const double halfGap = 0.5 * (angles[best + 1] - angles[best]);
    const double resultAngle = angles[best] + std::min(maximum, halfGap);
    return {length * std::cos(resultAngle), length * std::sin(resultAngle)};
}

}  // namespace chem::core::sketcher_geometry
