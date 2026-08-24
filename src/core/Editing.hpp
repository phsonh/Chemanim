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
    ChargePositive,
    ChargeNegative,
    SingleBond,
    DoubleBond,
    TripleBond,
    AromaticBond,
    SolidWedge,
    DashedWedge,
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

enum class HitKind { None, Atom, Bond };
enum class EditTargetKind { BaseStructure, TimelinePreview, AtomTween, Pose };

struct Hit {
    HitKind kind = HitKind::None;
    std::string id;
    double distance = 0.0;
};

struct GesturePreview {
    bool active = false;
    Point start;
    Point current;
    std::vector<Point> polygon;
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
    void setViewport(Viewport viewport);
    [[nodiscard]] const Viewport& viewport() const;
    void editBaseStructure(int previewFrame = 0);
    void previewTimeline(int frame);
    void editAtomTween(const std::string& tweenId);
    void editPose(const std::string& moleculeId, const std::string& poseId, int previewFrame);
    [[nodiscard]] EditTargetKind editTargetKind() const;
    [[nodiscard]] Molecule displayMolecule() const;

    [[nodiscard]] Hit hitTest(Point canvasPoint) const;
    [[nodiscard]] EditResult pointerDown(Point canvasPoint, bool alt, bool control, bool shift);
    [[nodiscard]] EditResult pointerMove(Point canvasPoint, bool alt, bool control, bool shift);
    [[nodiscard]] EditResult pointerUp(Point canvasPoint, bool alt, bool control, bool shift);
    void cancelGesture();
    bool deleteSelection();
    bool setAtomPosition(const std::string& atomId, Point position);
    bool setAtomElement(const std::string& atomId, std::string element);
    bool changeAtomCharge(const std::string& atomId, int delta);

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
