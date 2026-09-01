#pragma once

#include "Document.hpp"

#include <memory>
#include <optional>
#include <string>
#include <vector>

namespace chem::core {

enum class Tool {
    SelectRectangle,
    SelectLasso,
    Move,
    Eraser,
    AtomLabel,
    AtomText,
    ChargePositive,
    ChargeNegative,
    SingleBond,
    DoubleBond,
    TripleBond,
    SolidWedge,
    DashedWedge,
    SolidBar,
    HashedBar,
    WavyBond,
    Ring3,
    Ring4,
    Ring5,
    Ring6,
    Ring7,
    Ring8,
    Benzene,
};

struct Viewport {
    int width = 960;
    int height = 540;
    double pixelsPerUnit = 48.0;
    Point center;

    [[nodiscard]] Point modelToCanvas(Point value) const;
    [[nodiscard]] Point canvasToModel(Point value) const;
};

enum class HitKind { None, Atom, Bond, Adornment, Molecule, Control };
enum class EditTargetKind { BaseStructure, StructureSnapshot, TimelinePreview, AtomTween, Pose, ScriptNode };
enum class GesturePreviewKind { None, Rectangle, Lasso, Bond, Ring, Adornment, Text, Move, Pan, ArrowCurve };

struct Hit {
    HitKind kind = HitKind::None;
    std::string id;
    double distance = 0.0;
};

struct GesturePreview {
    bool active = false;
    GesturePreviewKind kind = GesturePreviewKind::None;
    Point start;
    Point current;
    std::vector<Point> polygon;
    std::string text;
    std::optional<std::string> snapAtomId;
};

struct EditResult {
    bool changed = false;
    std::string message;
    Hit hover;
    GesturePreview preview;
    std::vector<std::string> selectedAtoms;
    std::vector<std::string> selectedBonds;
};

struct DirectControl {
    std::string id;
    std::string role;
    Point position;
};

class EditorSession {
public:
    explicit EditorSession(Project project = {});
    ~EditorSession();
    EditorSession(EditorSession&&) noexcept;
    EditorSession& operator=(EditorSession&&) noexcept;
    EditorSession(const EditorSession&) = delete;
    EditorSession& operator=(const EditorSession&) = delete;

    [[nodiscard]] Project& project();
    [[nodiscard]] const Project& project() const;
    void replaceProject(Project project);
    void setActiveMolecule(const std::string& stableId);
    [[nodiscard]] std::string activeMoleculeId() const;
    void setTool(Tool tool);
    [[nodiscard]] Tool tool() const;
    void setElement(std::string element);
    [[nodiscard]] std::string element() const;
    void setViewport(Viewport viewport);
    [[nodiscard]] const Viewport& viewport() const;
    void editBaseStructure(const std::string& nodeId, int previewFrame = 0);
    void previewTimeline(int frame);
    void editAtomTween(const std::string& tweenId);
    void editPose(const std::string& moleculeId, const std::string& poseId, int previewFrame);
    void editScriptNode(const std::string& nodeId);
    [[nodiscard]] EditTargetKind editTargetKind() const;
    [[nodiscard]] std::string editTargetId() const;
    [[nodiscard]] int previewFrame() const;
    [[nodiscard]] std::optional<int> comparisonFrame() const;
    [[nodiscard]] bool canEditStructure() const;
    [[nodiscard]] bool canDirectManipulate() const;
    [[nodiscard]] Molecule displayMolecule() const;
    [[nodiscard]] std::vector<DirectControl> directControls() const;

    [[nodiscard]] Hit hitTest(Point canvasPoint) const;
    [[nodiscard]] EditResult pointerDown(Point canvasPoint, bool alt, bool control, bool shift);
    [[nodiscard]] EditResult pointerMove(Point canvasPoint, bool alt, bool control, bool shift);
    [[nodiscard]] EditResult pointerUp(Point canvasPoint, bool alt, bool control, bool shift);
    bool adjustArrowCurveBend(int direction);
    void cancelGesture();
    [[nodiscard]] EditResult selectAll();
    bool deleteSelection();
    bool setAtomPosition(const std::string& atomId, Point position);
    bool setAtomElement(const std::string& atomId, std::string element);
    bool setAtomLabel(const std::string& atomId, std::string label,
                      AtomLabelSide side, AtomNumberStyle numberStyle);
    bool addChargeAdornment(const std::string& atomId, int delta);
    bool setAdornmentOffset(const std::string& adornmentId, Point offset);
    [[nodiscard]] std::string createBlankMolecule(
        std::string name = {},
        std::optional<std::size_t> insertionIndex = std::nullopt);
    [[nodiscard]] std::string importSmiles(
        std::string name,const std::string& smiles,
        std::optional<std::size_t> insertionIndex = std::nullopt);
    [[nodiscard]] std::string addScriptNode(const std::string& type, const std::string& paramsJson,
                                            std::optional<std::size_t> index = std::nullopt);
    [[nodiscard]] std::vector<std::string> livingMoleculeTargets(
        std::optional<std::size_t> insertionIndex = std::nullopt) const;
    [[nodiscard]] std::string createMergedGradientStructure(
        const std::string& target, const std::string& source, int frames,
        const std::string& easing,
        std::optional<std::size_t> insertionIndex = std::nullopt);
    bool updateScriptNode(const std::string& nodeId, const std::string& paramsJson);
    bool setScriptNodeEnabled(const std::string& nodeId, bool enabled);
    bool moveScriptNode(const std::string& nodeId, std::size_t index);
    [[nodiscard]] std::string duplicateScriptNode(
        const std::string& nodeId,
        std::optional<std::size_t> insertionIndex = std::nullopt);
    bool deleteScriptNode(const std::string& nodeId);
    [[nodiscard]] std::string gradientStructureSummary(const std::string& nodeId) const;
    bool rebuildGradientStructure(const std::string& nodeId);
    bool retargetGradientStructure(const std::string& nodeId,
                                   const std::string& moleculeId);
    bool repairMoleculeAnchor(const std::string& moleculeId);
    [[nodiscard]] EditResult selectConnectedComponent(const std::string& atomId,
                                                      bool additive = false);
    bool updateScene(const std::string& sceneJson);

    [[nodiscard]] bool canUndo() const;
    [[nodiscard]] bool canRedo() const;
    bool undo();
    bool redo();

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

[[nodiscard]] const char* toString(Tool value);
[[nodiscard]] Tool toolFromString(const std::string& value);

}  // namespace chem::core
