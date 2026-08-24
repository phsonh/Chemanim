#pragma once

#include <filesystem>
#include <functional>
#include <limits>
#include <map>
#include <memory>
#include <optional>
#include <string>
#include <unordered_map>
#include <vector>

#include "core/Document.hpp"

struct lua_State;

namespace chem {

struct ColorValue {
    unsigned char r = 255;
    unsigned char g = 255;
    unsigned char b = 255;
    unsigned char a = 255;
};

struct SceneSettings {
    int width = 1920;
    int height = 1080;
    int logicWidth = 1920;
    int logicHeight = 1080;
    int fps = 60;
    double viewZoom = 2.2;
    int endFrame = 0;
    std::string title = "Chemanim Preview";
    ColorValue background{245, 245, 242, 255};
};

enum class Ease {
    Linear,
    InQuad,
    OutQuad,
    InOutQuad,
    InCubic,
    OutCubic,
    InOutCubic,
    SmoothStep,
    Step
};

struct Segment {
    int start = 0;
    int end = 0;
    double from = 0.0;
    double to = 0.0;
    Ease ease = Ease::Linear;
    unsigned long long order = 0;
    int cancelledAt = std::numeric_limits<int>::max();
    double cancelledValue = 0.0;
};

struct NumericTrack {
    double base = 0.0;
    std::vector<Segment> segments;

    [[nodiscard]] double valueAt(int frame) const;
};

struct StringEvent {
    int frame = 0;
    std::string value;
    unsigned long long order = 0;
};

struct StringTrack {
    std::string base;
    std::vector<StringEvent> events;

    [[nodiscard]] std::string valueAt(int frame) const;
};

struct ImageLayer {
    std::string texture;
    double x = 0.0;
    double y = 0.0;
    double alpha = 1.0;
};

struct ImageTransition {
    int start = 0;
    int end = 0;
    std::vector<ImageLayer> fromLayers;
    std::string toTexture;
    double toX = 0.0;
    double toY = 0.0;
    Ease ease = Ease::Linear;
    unsigned long long order = 0;
    unsigned long long textureCompletionOrder = 0;
    unsigned long long xCompletionOrder = 0;
    unsigned long long yCompletionOrder = 0;
    int cancelledAt = std::numeric_limits<int>::max();
};

struct ImageBlend {
    std::vector<ImageLayer> layers;
};

struct Object {
    int id = 0;
    int luaRef = -1;
    std::string kind = "sprite";
    std::string name;
    int bornFrame = 0;
    int deadFrame = std::numeric_limits<int>::max();
    std::unordered_map<std::string, NumericTrack> numericTracks;
    std::unordered_map<std::string, StringTrack> stringTracks;
    std::vector<ImageTransition> imageTransitions;
    std::unique_ptr<core::Molecule> molecule;
};

struct TextureAsset {
    std::string name;
    std::filesystem::path path;
    double anchorX = 0.5;
    double anchorY = 0.5;
};

class Engine {
public:
    explicit Engine(lua_State* state);
    ~Engine();

    Engine(const Engine&) = delete;
    Engine& operator=(const Engine&) = delete;

    SceneSettings scene;
    std::filesystem::path scriptDirectory;

    Object& createObject(int tableIndex, const std::string& kind);
    Object* objectFromTable(int tableIndex);
    Object* objectById(int id);
    void scheduleRemove(Object& object, int frame);
    unsigned long long addNumericTween(Object& object, const std::string& property, int start,
                                       int duration, double target, Ease ease);
    unsigned long long addStringKey(Object& object, const std::string& property, int frame,
                                    std::string value);
    void addImageTransition(Object& object, int start, int duration,
                            std::string targetTexture, Ease ease,
                            std::optional<double> targetX = std::nullopt,
                            std::optional<double> targetY = std::nullopt);
    void addAtomTween(Object& object, const std::string& atomId, int start, int duration,
                      double x, double y, Ease ease);
    void applyFrame(int frame);
    void registerTexture(std::string name, std::filesystem::path path,
                         double anchorX = 0.5, double anchorY = 0.5);
    void addFrameCallback(int luaRef);

    [[nodiscard]] int maxScheduledFrame() const;
    [[nodiscard]] std::optional<ImageBlend> imageBlendAt(const Object& object, int frame) const;
    [[nodiscard]] const std::vector<std::unique_ptr<Object>>& objects() const { return objects_; }
    [[nodiscard]] const std::map<std::string, TextureAsset>& textures() const { return textures_; }
    [[nodiscard]] lua_State* state() const { return state_; }

    static Ease parseEase(const std::string& name);

private:
    lua_State* state_ = nullptr;
    std::vector<std::unique_ptr<Object>> objects_;
    std::unordered_map<int, Object*> byId_;
    std::map<std::string, TextureAsset> textures_;
    std::vector<int> frameCallbacks_;
    int nextId_ = 1;
    unsigned long long nextOrder_ = 1;

    static double easeValue(Ease ease, double t);
    void writeNumber(Object& object, const std::string& key, double value);
    void writeString(Object& object, const std::string& key, const std::string& value);
};

} // namespace chem
