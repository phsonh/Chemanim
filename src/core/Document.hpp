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

enum class BondType { Single, Double, Triple };
enum class BondStereo {
    None,
    SolidWedge,
    DashedWedge,
    SolidBar,
    HashedBar,
    Wavy,
};
enum class SecondaryLineSide { Left, Right, Center };
enum class AtomLabelSide { Left, Right };
enum class AtomNumberStyle { Normal, Subscript, Superscript };

struct Color {
    int red = 0;
    int green = 0;
    int blue = 0;
};

struct Atom {
    std::string id;
    std::uint64_t creationSerial = 0;
    std::string element = "C";
    std::string alias;
    AtomLabelSide labelSide = AtomLabelSide::Right;
    AtomNumberStyle numberStyle = AtomNumberStyle::Subscript;
    int isotope = 0;
    int radicalElectrons = 0;
    int implicitHydrogens = 0;
    bool hidden = false;
    bool alive = true;
    int alpha = 255;
    Color color;
    Point position;
};

struct Bond {
    std::string id;
    std::string atomA;
    std::string atomB;
    BondType type = BondType::Single;
    SecondaryLineSide secondaryLineSide = SecondaryLineSide::Center;
    BondStereo stereo = BondStereo::None;
    bool visible = true;
    bool alive = true;
    int alpha = 255;
    Color color;
};

struct AtomAdornment {
    std::string id;
    std::uint64_t creationSerial = 0;
    std::string atomId;
    std::string text = "⊕";
    Point offset;
    Color color;
    int alpha = 255;
    bool alive = true;
};

struct Pose {
    std::string id;
    std::map<std::string, Point> atomPositions;
};

struct Molecule {
    std::string id;
    std::string name;
    std::string sourceSmiles;
    // v8: stable object-space origin.  Structure atoms are persisted in
    // molecule-local coordinates and never act as the object's transform
    // anchor.
    Point origin;
    // New empty v8 objects have no meaningful transform centre until their
    // first non-empty structure state is committed.  Older v8 documents are
    // treated as initialized to preserve their authored animation exactly.
    bool anchorInitialized = false;
    double referenceBondLength = 32.0;
    std::uint64_t nextAtomId = 1;
    std::uint64_t nextBondId = 1;
    std::uint64_t nextAdornmentId = 1;
    std::vector<Atom> atoms;
    std::vector<Bond> bonds;
    std::vector<AtomAdornment> adornments;
    std::map<std::string, Pose> poses;
    double rotation = 0.0;
    // v7: X/Y are the only persisted scale components.  A separate uniform
    // value would be ambiguous because it could be multiplied twice.
    double scaleX = 1.0;
    double scaleY = 1.0;
    int alpha = 255;
    Color color{255, 255, 255};
    int layer = 0;
    bool visible = true;
    bool retired = false;

    [[nodiscard]] Atom* atom(const std::string& stableId);
    [[nodiscard]] const Atom* atom(const std::string& stableId) const;
    [[nodiscard]] Bond* bond(const std::string& stableId);
    [[nodiscard]] const Bond* bond(const std::string& stableId) const;
    [[nodiscard]] AtomAdornment* adornment(const std::string& stableId);
    [[nodiscard]] const AtomAdornment* adornment(const std::string& stableId) const;
    [[nodiscard]] Bond* bondBetween(const std::string& first, const std::string& second);
    [[nodiscard]] const Atom* anchorAtom() const;
    [[nodiscard]] std::optional<Point> coordinate() const;
    [[nodiscard]] std::string allocateAtomId();
    [[nodiscard]] std::string allocateBondId();
    [[nodiscard]] std::string allocateAdornmentId();
    [[nodiscard]] std::string addAtom(Point position, std::string element = "C",
                                      std::uint64_t creationSerial = 0);
    [[nodiscard]] std::string addBond(const std::string& first, const std::string& second,
                                      BondType type = BondType::Single,
                                      BondStereo stereo = BondStereo::None);
    [[nodiscard]] std::string addAdornment(const std::string& atomId, std::string text,
                                           Point offset, std::uint64_t creationSerial = 0);
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

struct ScriptNode {
    std::string id;
    std::string type;
    bool enabled = true;
    // Kept as JSON text so the C++ document remains the sole owner while the
    // node registry can evolve without a parallel Python dataclass hierarchy.
    std::string paramsJson = "{}";
};

struct Project {
    std::string mod = "native2d_demo";
    Scene scene;
    Style style;
    std::uint64_t nextMoleculeId = 1;
    std::uint64_t nextTimelineId = 1;
    std::uint64_t nextNodeId = 1;
    std::uint64_t nextCreationSerial = 1;
    std::vector<Molecule> molecules;
    std::vector<ScriptNode> nodes;
    // v2/v3 compatibility input only.  v4 serialization and authoring use
    // `nodes`; typed tracks are compiled from that ordered sequence.
    std::vector<AtomTween> atomTweens;
    std::vector<PoseTween> poseTweens;

    [[nodiscard]] Molecule* molecule(const std::string& stableId);
    [[nodiscard]] const Molecule* molecule(const std::string& stableId) const;
    [[nodiscard]] std::string addBlankMolecule(
        std::string name = {},
        std::optional<std::size_t> insertionIndex = std::nullopt);
    [[nodiscard]] std::string duplicateMolecule(const std::string& sourceId,
                                                std::optional<std::size_t> nodeIndex = std::nullopt);
    [[nodiscard]] std::uint64_t allocateCreationSerial();
    [[nodiscard]] std::string addAtomTween(const std::string& moleculeId,
                                           const std::string& atomId,
                                           int startFrame, int frames,
                                           Point target, Easing easing = Easing::Linear);
    [[nodiscard]] ScriptNode* node(const std::string& stableId);
    [[nodiscard]] const ScriptNode* node(const std::string& stableId) const;
    [[nodiscard]] std::string addNode(const std::string& type, std::string paramsJson = "{}",
                                      std::optional<std::size_t> index = std::nullopt);
    void ensureDefaultNodes();
    void validateIds() const;
};

[[nodiscard]] std::string toJson(const Project& project, int indent = 2);
[[nodiscard]] Project fromJson(const std::string& source);
[[nodiscard]] Project loadProject(const std::filesystem::path& path);
void saveProject(const Project& project, const std::filesystem::path& path);

[[nodiscard]] const char* toString(BondType value);
[[nodiscard]] const char* toString(BondStereo value);
[[nodiscard]] const char* toString(SecondaryLineSide value);
[[nodiscard]] const char* toString(AtomLabelSide value);
[[nodiscard]] const char* toString(AtomNumberStyle value);
[[nodiscard]] BondType bondTypeFromString(const std::string& value);
[[nodiscard]] BondStereo bondStereoFromString(const std::string& value);
[[nodiscard]] SecondaryLineSide secondaryLineSideFromString(const std::string& value);
[[nodiscard]] AtomLabelSide atomLabelSideFromString(const std::string& value);
[[nodiscard]] AtomNumberStyle atomNumberStyleFromString(const std::string& value);

}  // namespace chem::core
