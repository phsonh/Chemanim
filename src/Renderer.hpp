#pragma once

#include "Engine.hpp"

#include <string>
#include <filesystem>
#include <unordered_map>
#include <vector>

#include <raylib.h>

namespace chem {

class Renderer {
public:
    explicit Renderer(Engine& engine);
    ~Renderer();

    Renderer(const Renderer&) = delete;
    Renderer& operator=(const Renderer&) = delete;

    void initialize(bool hidden);
    void renderScene(int frame);
    void savePng(const std::filesystem::path& path);
    [[nodiscard]] std::vector<unsigned char> captureRgba();

private:
    Engine& engine_;
    RenderTexture2D target_{};
    RenderTexture2D supersampleTarget_{};
    std::unordered_map<std::string, Texture2D> textures_;
    struct SvgCacheEntry {
        Texture2D texture{};
        std::string svg;
        float rasterScale = 0.0f;
    };
    std::unordered_map<int, SvgCacheEntry> moleculeSvgs_;
    bool initialized_ = false;
    int currentFrame_ = 0;
    static constexpr int supersample_ = 2;

    void loadAssets();
    void drawObject(const Object& object);
    void drawSprite(int tableIndex, const Object& object);
    void drawAcsMolecule(int tableIndex, const Object& object);
    void drawArrow(int tableIndex);
    [[nodiscard]] double number(int tableIndex, const char* key, double fallback) const;
    [[nodiscard]] std::string string(int tableIndex, const char* key, const char* fallback = "") const;
    [[nodiscard]] Color objectColor(int tableIndex) const;
};

} // namespace chem
