#pragma once

#include <cstdint>
#include <filesystem>
#include <map>
#include <optional>
#include <set>
#include <string>
#include <unordered_map>
#include <vector>

namespace chem::core {

struct Point {
    double x = 0.0;
    double y = 0.0;
};

struct Rect {
    double left = 0.0;
    double top = 0.0;
    double right = 0.0;
    double bottom = 0.0;

    [[nodiscard]] bool contains(Point point, double padding = 0.0) const;
};

enum class BondType { Single, Double, Triple, Aromatic };
enum class BondStereo { None, SolidWedge, DashedWedge, Wavy };

struct Atom {
    std::string id;
    std::string element = "C";
    std::string alias;
    int isotope = 0;
    int formalCharge = 0;
    int radicalElectrons = 0;
    int implicitHydrogens = 0;
    bool aromatic = false;
    bool hidden = false;
    Point position;
};

struct Bond {
    std::string id;
    std::string atomA;
    std::string atomB;
    BondType type = BondType::Single;
    BondStereo stereo = BondStereo::None;
    bool visible = true;
};

struct Pose {
    std::string id;
    std::map<std::string, Point> atomPositions;
};

struct Molecule {
    std::string id;
    std::string name;
    std::string sourceSmiles;
    double referenceBondLength = 1.5;
    std::uint64_t nextAtomId = 1;
    std::uint64_t nextBondId = 1;
    std::vector<Atom> atoms;
    std::vector<Bond> bonds;
    std::map<std::string, Pose> poses;
    Point scenePosition;
    double rotation = 0.0;
    double scale = 2.2;
    int alpha = 255;
    int layer = 0;

    [[nodiscard]] Atom* atom(const std::string& stableId);
    [[nodiscard]] const Atom* atom(const std::string& stableId) const;
    [[nodiscard]] Bond* bond(const std::string& stableId);
    [[nodiscard]] const Bond* bond(const std::string& stableId) const;
    [[nodiscard]] Bond* bondBetween(const std::string& first, const std::string& second);
    [[nodiscard]] std::string allocateAtomId();
    [[nodiscard]] std::string allocateBondId();
    [[nodiscard]] std::string addAtom(Point position, std::string element = "C");
    [[nodiscard]] std::string addBond(const std::string& first, const std::string& second,
                                      BondType type = BondType::Single,
                                      BondStereo stereo = BondStereo::None);
    bool removeAtom(const std::string& stableId);
    bool removeBond(const std::string& stableId);
    void validateIds() const;
};

struct Scene {
    int width = 1920;
    int height = 1080;
    int logicWidth = 960;
    int logicHeight = 540;
    int fps = 60;
    double viewZoom = 2.2;
    std::string background = "FFFFFFFF";
    std::string title = "native2d";
};

struct Style {
    std::string preset = "acs_document_1996";
    std::string fontFamily = "Arial";
    std::string fontFile = "C:/Windows/Fonts/arial.ttf";
    double fontPt = 10.0;
    double bondLengthPt = 14.4;
    double lineWidthPt = 0.6;
    double doubleBondSpacing = 0.18;
};

enum class Easing { Linear, InQuad, OutQuad, InOutQuad, SmoothStep, Step };

struct AtomTween {
    std::string id;
    std::string moleculeId;
    std::string atomId;
    int startFrame = 0;
    int frames = 30;
    Point target;
    Easing easing = Easing::Linear;
};

struct PoseTween {
    std::string id;
    std::string moleculeId;
    std::string poseId;
    int startFrame = 0;
    int frames = 30;
    Easing easing = Easing::Linear;
};

struct Project {
    std::string mod = "native2d_demo";
    Scene scene;
    Style style;
    std::uint64_t nextMoleculeId = 1;
    std::uint64_t nextTimelineId = 1;
    std::vector<Molecule> molecules;
    std::vector<AtomTween> atomTweens;
    std::vector<PoseTween> poseTweens;

    [[nodiscard]] Molecule* molecule(const std::string& stableId);
    [[nodiscard]] const Molecule* molecule(const std::string& stableId) const;
    [[nodiscard]] std::string addBlankMolecule(std::string name = {});
    [[nodiscard]] std::string addAtomTween(const std::string& moleculeId,
                                           const std::string& atomId,
                                           int startFrame, int frames,
                                           Point target, Easing easing = Easing::Linear);
    void validateIds() const;
};

[[nodiscard]] std::string toJson(const Project& project, int indent = 2);
[[nodiscard]] Project fromJson(const std::string& source);
[[nodiscard]] Project loadProject(const std::filesystem::path& path);
void saveProject(const Project& project, const std::filesystem::path& path);

[[nodiscard]] const char* toString(BondType value);
[[nodiscard]] const char* toString(BondStereo value);
[[nodiscard]] BondType bondTypeFromString(const std::string& value);
[[nodiscard]] BondStereo bondStereoFromString(const std::string& value);

}  // namespace chem::core
