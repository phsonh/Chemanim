#include "Renderer.hpp"

extern "C" {
#include <lua.h>
}

#include <raymath.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <cstdio>
#include <filesystem>
#include <sstream>
#include <stdexcept>
#include <unordered_map>
#include <vector>

namespace chem {

Renderer::Renderer(Engine& engine) : engine_(engine) {}

Renderer::~Renderer() {
    if (!initialized_) return;
    for (auto& [_, texture] : textures_) UnloadTexture(texture);
    if (ownsMoleculeFont_) UnloadFont(moleculeFont_);
    UnloadRenderTexture(supersampleTarget_);
    UnloadRenderTexture(target_);
    CloseWindow();
}

void Renderer::initialize(bool hidden) {
    unsigned int flags = FLAG_WINDOW_RESIZABLE | FLAG_VSYNC_HINT;
    if (hidden) flags |= FLAG_WINDOW_HIDDEN;
    SetConfigFlags(flags);
    SetTraceLogLevel(LOG_WARNING);
    const int windowWidth = hidden ? 64 : 1280;
    const int windowHeight = hidden ? 64 : 720;
    InitWindow(windowWidth, windowHeight, engine_.scene.title.c_str());
    if (!IsWindowReady()) throw std::runtime_error("Failed to initialize the graphics window");
    target_ = LoadRenderTexture(engine_.scene.width, engine_.scene.height);
    supersampleTarget_ = LoadRenderTexture(
        engine_.scene.width * supersample_, engine_.scene.height * supersample_);
    SetTextureFilter(target_.texture, TEXTURE_FILTER_BILINEAR);
    SetTextureFilter(supersampleTarget_.texture, TEXTURE_FILTER_BILINEAR);
    initialized_ = true;
    const std::filesystem::path arial = "C:/Windows/Fonts/arial.ttf";
    if (std::filesystem::is_regular_file(arial)) {
        moleculeFont_ = LoadFontEx(arial.string().c_str(), 48, nullptr, 0);
        ownsMoleculeFont_ = moleculeFont_.texture.id != 0;
    }
    if (!ownsMoleculeFont_) moleculeFont_ = GetFontDefault();
    loadAssets();
}

void Renderer::loadAssets() {
    for (const auto& [name, asset] : engine_.textures()) {
        const std::string path = asset.path.string();
        Texture2D texture = LoadTexture(path.c_str());
        if (texture.id == 0) throw std::runtime_error("Failed to load texture '" + name + "': " + path);
        SetTextureFilter(texture, TEXTURE_FILTER_BILINEAR);
        textures_[name] = texture;
    }
}

double Renderer::number(int tableIndex, const char* key, double fallback) const {
    lua_State* state = engine_.state();
    tableIndex = lua_absindex(state, tableIndex);
    lua_getfield(state, tableIndex, key);
    const double result = lua_isnumber(state, -1) ? lua_tonumber(state, -1) : fallback;
    lua_pop(state, 1);
    return result;
}

std::string Renderer::string(int tableIndex, const char* key, const char* fallback) const {
    lua_State* state = engine_.state();
    tableIndex = lua_absindex(state, tableIndex);
    lua_getfield(state, tableIndex, key);
    std::string result = fallback;
    if (lua_isstring(state, -1)) result = lua_tostring(state, -1);
    lua_pop(state, 1);
    return result;
}

Color Renderer::objectColor(int tableIndex) const {
    const auto channel = [&](const char* key, double fallback) {
        return static_cast<unsigned char>(std::clamp(number(tableIndex, key, fallback), 0.0, 255.0));
    };
    const double alpha = std::clamp(number(tableIndex, "alpha", 1.0), 0.0, 1.0);
    return Color{channel("r", 255), channel("g", 255), channel("b", 255),
                 static_cast<unsigned char>(std::round(alpha * 255.0))};
}

void Renderer::renderScene(int frame) {
    currentFrame_ = frame;
    engine_.applyFrame(frame);
    struct Entry { const Object* object; double layer; };
    std::vector<Entry> entries;
    lua_State* state = engine_.state();
    for (const auto& object : engine_.objects()) {
        if (frame < object->bornFrame || frame >= object->deadFrame) continue;
        lua_rawgeti(state, LUA_REGISTRYINDEX, object->luaRef);
        const bool visible = number(-1, "visible", 1) != 0 && number(-1, "alpha", 1) > 0;
        const double layer = number(-1, "layer", 0);
        lua_pop(state, 1);
        if (visible) entries.push_back({object.get(), layer});
    }
    std::stable_sort(entries.begin(), entries.end(), [](const Entry& a, const Entry& b) {
        if (a.layer != b.layer) return a.layer < b.layer;
        return a.object->id < b.object->id;
    });

    const ColorValue bg = engine_.scene.background;
    BeginTextureMode(supersampleTarget_);
    ClearBackground(Color{bg.r, bg.g, bg.b, bg.a});
    for (const Entry& entry : entries) drawObject(*entry.object);
    EndTextureMode();

    BeginTextureMode(target_);
    ClearBackground(BLANK);
    const Rectangle source{
        0, 0,
        static_cast<float>(supersampleTarget_.texture.width),
        -static_cast<float>(supersampleTarget_.texture.height)
    };
    const Rectangle destination{
        0, 0,
        static_cast<float>(engine_.scene.width),
        static_cast<float>(engine_.scene.height)
    };
    DrawTexturePro(supersampleTarget_.texture, source, destination, {0, 0}, 0, WHITE);
    EndTextureMode();
}

void Renderer::drawObject(const Object& object) {
    lua_State* state = engine_.state();
    lua_rawgeti(state, LUA_REGISTRYINDEX, object.luaRef);
    const int table = lua_gettop(state);
    if (object.kind == "sprite") drawSprite(table, object);
    else if (object.kind == "molecule") drawMolecule(table, object);
    else if (object.kind == "arrow") drawArrow(table);
    lua_pop(state, 1);
}

namespace {

std::string atomLabel(const Atom2D& atom) {
    if (atom.hidden) return {};
    if (!atom.alias.empty()) return atom.alias;
    const bool ordinaryCarbon = atom.element == "C" && atom.isotope == 0 &&
                                atom.formalCharge == 0 && atom.radicalElectrons == 0;
    if (ordinaryCarbon) return {};
    std::ostringstream label;
    if (atom.isotope > 0) label << atom.isotope;
    label << atom.element;
    if (atom.implicitHydrogens > 0) {
        label << 'H';
        if (atom.implicitHydrogens > 1) label << atom.implicitHydrogens;
    }
    if (atom.formalCharge != 0) {
        const int magnitude = std::abs(atom.formalCharge);
        if (magnitude > 1) label << magnitude;
        label << (atom.formalCharge > 0 ? '+' : '-');
    }
    if (atom.radicalElectrons > 0) label << '.';
    return label.str();
}

Vector2 shortenedToLabel(Vector2 from, Vector2 to, Rectangle label, float gap) {
    Vector2 direction = Vector2Subtract(to, from);
    const float length = Vector2Length(direction);
    if (length < 0.001f || label.width <= 0 || label.height <= 0) return to;
    direction = Vector2Scale(direction, 1.0f / length);
    const float halfW = label.width * 0.5f + gap;
    const float halfH = label.height * 0.5f + gap;
    const float tx = std::abs(direction.x) > 0.0001f ? halfW / std::abs(direction.x) : 1.0e9f;
    const float ty = std::abs(direction.y) > 0.0001f ? halfH / std::abs(direction.y) : 1.0e9f;
    return Vector2Subtract(to, Vector2Scale(direction, std::min(tx, ty)));
}

} // namespace

void Renderer::drawMolecule(int table, const Object& object) {
    if (!object.molecule || object.molecule->atoms.empty()) return;
    const Molecule2D& molecule = *object.molecule;
    const float renderWidth = static_cast<float>(engine_.scene.width * supersample_);
    const float renderHeight = static_cast<float>(engine_.scene.height * supersample_);
    const float canvasScaleX = renderWidth / engine_.scene.logicWidth;
    const float canvasScaleY = renderHeight / engine_.scene.logicHeight;
    const float objectX = static_cast<float>(number(table, "x", 0));
    const float objectY = static_cast<float>(number(table, "y", 0));
    const float scaleX = static_cast<float>(number(table, "scale_x", 1));
    const float scaleY = static_cast<float>(number(table, "scale_y", 1));
    const float rotation = static_cast<float>(number(table, "rotation", 0) * DEG2RAD);

    std::unordered_map<std::string, const Atom2D*> byId;
    for (const Atom2D& atom : molecule.atoms) byId[atom.stableId] = &atom;
    std::vector<double> lengths;
    for (const Bond2D& bond : molecule.bonds) {
        const auto a = byId.find(bond.atomA), b = byId.find(bond.atomB);
        if (a != byId.end() && b != byId.end()) {
            const double dx = a->second->position.x - b->second->position.x;
            const double dy = a->second->position.y - b->second->position.y;
            const double length = std::hypot(dx, dy);
            if (length > 0.001) lengths.push_back(length);
        }
    }
    double medianBond = 1.5;
    if (!lengths.empty()) {
        const auto middle = lengths.begin() + static_cast<std::ptrdiff_t>(lengths.size() / 2);
        std::nth_element(lengths.begin(), middle, lengths.end());
        medianBond = *middle;
    }
    // ACS Document 1996 reference bond length: 14.4 pt at 96-DPI equivalent.
    const float viewZoom = static_cast<float>(engine_.scene.viewZoom);
    const float referenceBond = 19.2f * supersample_ * viewZoom;
    const float unit = referenceBond / static_cast<float>(medianBond);
    const auto transform = [&](const Atom2D& atom) {
        float x = static_cast<float>(atom.position.x) * unit * scaleX;
        float y = static_cast<float>(atom.position.y) * unit * scaleY;
        const float rx = x * std::cos(rotation) - y * std::sin(rotation);
        const float ry = x * std::sin(rotation) + y * std::cos(rotation);
        return Vector2{renderWidth * 0.5f + objectX * canvasScaleX + rx,
                       renderHeight * 0.5f - objectY * canvasScaleY - ry};
    };

    const float fontSize = (10.0f * 96.0f / 72.0f) * supersample_ * viewZoom;
    const float spacing = 0.2f * fontSize;
    const float labelGap = 1.5f * supersample_ * viewZoom;
    const float lineWidth = 0.8f * supersample_ * viewZoom;
    const float doubleGap = referenceBond * 0.18f;
    const Color color = objectColor(table);
    std::unordered_map<std::string, Vector2> positions;
    std::unordered_map<std::string, Rectangle> labels;
    std::unordered_map<std::string, std::string> labelText;
    for (const Atom2D& atom : molecule.atoms) {
        const Vector2 p = transform(atom);
        positions[atom.stableId] = p;
        const std::string label = atomLabel(atom);
        labelText[atom.stableId] = label;
        if (label.empty()) {
            labels[atom.stableId] = Rectangle{p.x, p.y, 0, 0};
        } else {
            const Vector2 size = MeasureTextEx(moleculeFont_, label.c_str(), fontSize, spacing);
            labels[atom.stableId] = Rectangle{p.x - size.x * 0.5f, p.y - size.y * 0.5f, size.x, size.y};
        }
    }

    const auto line = [&](Vector2 a, Vector2 b, float width = -1.0f) {
        DrawLineEx(a, b, width < 0 ? lineWidth : width, color);
    };
    for (const Bond2D& bond : molecule.bonds) {
        if (!bond.visible) continue;
        const auto pa = positions.find(bond.atomA), pb = positions.find(bond.atomB);
        if (pa == positions.end() || pb == positions.end()) continue;
        Vector2 a = shortenedToLabel(pb->second, pa->second, labels[bond.atomA], labelGap);
        Vector2 b = shortenedToLabel(pa->second, pb->second, labels[bond.atomB], labelGap);
        Vector2 tangent = Vector2Normalize(Vector2Subtract(b, a));
        if (Vector2Length(tangent) < 0.001f) continue;
        const Vector2 normal{-tangent.y, tangent.x};
        if (bond.stereo == "wedge") {
            const float wedgeWidth = 5.0f * supersample_;
            DrawTriangle(a, Vector2Add(b, Vector2Scale(normal, wedgeWidth)),
                         Vector2Subtract(b, Vector2Scale(normal, wedgeWidth)), color);
        } else if (bond.stereo == "dash") {
            constexpr int marks = 7;
            for (int i = 0; i < marks; ++i) {
                const float t = static_cast<float>(i + 1) / (marks + 1);
                const Vector2 center = Vector2Lerp(a, b, t);
                const float half = t * 5.0f * supersample_;
                line(Vector2Subtract(center, Vector2Scale(normal, half)),
                     Vector2Add(center, Vector2Scale(normal, half)), lineWidth * 0.85f);
            }
        } else if (bond.order >= 2.8) {
            line(a, b);
            const Vector2 offset = Vector2Scale(normal, doubleGap * 0.55f);
            line(Vector2Add(a, offset), Vector2Add(b, offset));
            line(Vector2Subtract(a, offset), Vector2Subtract(b, offset));
        } else if (bond.order >= 1.8) {
            const Vector2 offset = Vector2Scale(normal, doubleGap * 0.35f);
            line(Vector2Add(a, offset), Vector2Add(b, offset));
            line(Vector2Subtract(a, offset), Vector2Subtract(b, offset));
        } else if (bond.aromatic || std::abs(bond.order - 1.5) < 0.1) {
            line(a, b);
        } else {
            line(a, b);
        }
    }
    for (const Atom2D& atom : molecule.atoms) {
        const std::string& label = labelText[atom.stableId];
        if (label.empty()) continue;
        const Rectangle box = labels[atom.stableId];
        DrawTextEx(moleculeFont_, label.c_str(), Vector2{box.x, box.y}, fontSize, spacing, color);
    }
}

void Renderer::drawSprite(int table, const Object& object) {
    const float renderWidth = static_cast<float>(engine_.scene.width * supersample_);
    const float renderHeight = static_cast<float>(engine_.scene.height * supersample_);
    const float canvasScaleX = renderWidth / engine_.scene.logicWidth;
    const float canvasScaleY = renderHeight / engine_.scene.logicHeight;
    const double objectX = number(table, "x", 0);
    const double objectY = number(table, "y", 0);
    const float scaleX = static_cast<float>(number(table, "scale_x", 1)) * canvasScaleX;
    const float scaleY = static_cast<float>(number(table, "scale_y", 1)) * canvasScaleY;
    const float rotation = static_cast<float>(number(table, "rotation", 0));
    const double objectAnchorX = number(table, "anchor_x", -1);
    const double objectAnchorY = number(table, "anchor_y", -1);
    const float reveal = static_cast<float>(std::clamp(number(table, "reveal", 1), 0.0, 1.0));
    if (reveal <= 0) return;
    const std::string direction = string(table, "reveal_dir", "ltr");
    const Color baseColor = objectColor(table);
    const auto drawTexture = [&](const std::string& textureName, double blendAlpha,
                                 double logicalX, double logicalY) {
        if (blendAlpha <= 0) return;
        const auto found = textures_.find(textureName);
        const auto assetFound = engine_.textures().find(textureName);
        if (found == textures_.end() || assetFound == engine_.textures().end()) return;
        const Texture2D texture = found->second;
        const TextureAsset& asset = assetFound->second;
        const float anchorX = static_cast<float>(objectAnchorX < 0 ? asset.anchorX : objectAnchorX);
        const float anchorY = static_cast<float>(objectAnchorY < 0 ? asset.anchorY : objectAnchorY);
        // DrawTexturePro treats a negative destination size as a positive size;
        // it does not mirror the texture.  Keep the destination rectangle
        // positive, flip through the source rectangle, and mirror the anchor so
        // negative scale has the same pivot semantics as the editor preview.
        const bool flipX = scaleX < 0.0f;
        const bool flipY = scaleY < 0.0f;
        const float fullW = texture.width * std::abs(scaleX);
        const float fullH = texture.height * std::abs(scaleY);
        Rectangle source{0, 0, static_cast<float>(texture.width), static_cast<float>(texture.height)};
        const float x = static_cast<float>(renderWidth * 0.5 + logicalX * canvasScaleX);
        const float y = static_cast<float>(renderHeight * 0.5 - logicalY * canvasScaleY);
        Rectangle destination{x, y, fullW, fullH};
        Vector2 origin{
            (flipX ? 1.0f - anchorX : anchorX) * fullW,
            (flipY ? anchorY : 1.0f - anchorY) * fullH
        };
        if (direction == "rtl") {
            source.x = texture.width * (1.0f - reveal); source.width *= reveal;
            destination.width *= reveal; origin.x -= fullW * (1.0f - reveal);
        } else if (direction == "ttb") {
            source.height *= reveal; destination.height *= reveal;
        } else if (direction == "btt") {
            source.y = texture.height * (1.0f - reveal); source.height *= reveal;
            destination.height *= reveal; origin.y -= fullH * (1.0f - reveal);
        } else {
            source.width *= reveal; destination.width *= reveal;
        }
        if (flipX) source.width = -source.width;
        if (flipY) source.height = -source.height;
        Color tint = baseColor;
        tint.a = static_cast<unsigned char>(std::round(
            static_cast<double>(baseColor.a) * std::clamp(blendAlpha, 0.0, 1.0)));
        DrawTexturePro(texture, source, destination, origin, rotation, tint);
    };

    if (const auto blend = engine_.imageBlendAt(object, currentFrame_)) {
        for (const auto& layer : blend->layers) {
            drawTexture(layer.texture, layer.alpha, layer.x, layer.y);
        }
    } else {
        drawTexture(string(table, "texture"), 1.0, objectX, objectY);
    }
}

void Renderer::drawArrow(int table) {
    const float ox = static_cast<float>(number(table, "x", 0));
    const float oy = static_cast<float>(number(table, "y", 0));
    const float sx = static_cast<float>(number(table, "scale_x", 1));
    const float sy = static_cast<float>(number(table, "scale_y", 1));
    const float renderWidth = static_cast<float>(engine_.scene.width * supersample_);
    const float renderHeight = static_cast<float>(engine_.scene.height * supersample_);
    const float canvasScaleX = renderWidth / engine_.scene.logicWidth;
    const float canvasScaleY = renderHeight / engine_.scene.logicHeight;
    const float strokeScale = std::sqrt(canvasScaleX * canvasScaleY);
    const auto screenPoint = [&](const char* xKey, const char* yKey, double fallbackX, double fallbackY) {
        const float logicalX = ox + static_cast<float>(number(table, xKey, fallbackX)) * sx;
        const float logicalY = oy + static_cast<float>(number(table, yKey, fallbackY)) * sy;
        return Vector2{renderWidth * 0.5f + logicalX * canvasScaleX,
                       renderHeight * 0.5f - logicalY * canvasScaleY};
    };
    Vector2 p0 = screenPoint("x1", "y1", 0, 0);
    Vector2 p1 = screenPoint("cx1", "cy1", 100, 0);
    Vector2 p2 = screenPoint("cx2", "cy2", 200, 0);
    Vector2 p3 = screenPoint("x2", "y2", 300, 0);
    const float thickness = static_cast<float>(std::max(0.1, number(table, "thickness", 3))) * strokeScale;
    const float headLength = thickness * (20.0f / 3.0f);
    const float headWidth = thickness * 5.0f;
    const float progress = static_cast<float>(std::clamp(number(table, "progress", 0), 0.0, 1.0));
    if (progress <= 0) return;

    constexpr int samples = 256;
    std::array<Vector2, samples + 1> points{};
    std::array<float, samples + 1> cumulative{};
    points[0] = p0;
    for (int i = 1; i <= samples; ++i) {
        const float t = static_cast<float>(i) / samples;
        const float u = 1.0f - t;
        points[i] = Vector2{
            u*u*u*p0.x + 3*u*u*t*p1.x + 3*u*t*t*p2.x + t*t*t*p3.x,
            u*u*u*p0.y + 3*u*u*t*p1.y + 3*u*t*t*p2.y + t*t*t*p3.y
        };
        cumulative[i] = cumulative[i - 1] + Vector2Distance(points[i - 1], points[i]);
    }
    const float targetLength = cumulative[samples] * progress;
    Color color = objectColor(table);
    const auto pointsThroughLength = [&](float length) {
        std::vector<Vector2> result;
        result.reserve(samples + 2);
        result.push_back(p0);
        for (int i = 1; i <= samples; ++i) {
            if (cumulative[i] <= length) {
                result.push_back(points[i]);
                continue;
            }
            const float segmentLength = cumulative[i] - cumulative[i - 1];
            if (length > cumulative[i - 1] && segmentLength > 0) {
                const float local = (length - cumulative[i - 1]) / segmentLength;
                result.push_back(Vector2Lerp(points[i - 1], points[i], local));
            }
            break;
        }
        return result;
    };

    const std::vector<Vector2> tipPoints = pointsThroughLength(targetLength);
    if (tipPoints.size() < 2) return;
    const Vector2 tip = tipPoints.back();

    // The shaft stops at the center of the triangular head's base.  It must
    // not continue underneath the triangle all the way to the arrow tip.
    const float shaftLength = std::max(0.0f, targetLength - headLength);
    const std::vector<Vector2> shaftPoints = pointsThroughLength(shaftLength);
    const Vector2 base = shaftPoints.back();

    // Build one continuous ribbon instead of drawing hundreds of independent
    // quads.  The averaged tangent gives smooth joins even on a tight curve;
    // the supersampled target supplies stable antialiasing after downsampling.
    std::vector<Vector2> ribbon;
    ribbon.reserve(shaftPoints.size() * 2);
    const float halfThickness = thickness * 0.5f;
    if (shaftPoints.size() >= 2) {
        for (std::size_t i = 0; i < shaftPoints.size(); ++i) {
            Vector2 tangent{};
            if (i == 0) {
                tangent = Vector2Subtract(shaftPoints[1], shaftPoints[0]);
            } else if (i + 1 == shaftPoints.size()) {
                tangent = Vector2Subtract(shaftPoints[i], shaftPoints[i - 1]);
            } else {
                tangent = Vector2Subtract(shaftPoints[i + 1], shaftPoints[i - 1]);
            }
            tangent = Vector2Normalize(tangent);
            if (Vector2Length(tangent) < 0.001f) tangent = {1, 0};
            const Vector2 normal{-tangent.y, tangent.x};
            // Right then left keeps raylib's generated strip triangles
            // counter-clockwise in its screen-space coordinate system.
            ribbon.push_back(Vector2Subtract(shaftPoints[i], Vector2Scale(normal, halfThickness)));
            ribbon.push_back(Vector2Add(shaftPoints[i], Vector2Scale(normal, halfThickness)));
        }
        DrawTriangleStrip(ribbon.data(), static_cast<int>(ribbon.size()), color);
        DrawCircleV(shaftPoints.front(), halfThickness, color);
    }

    Vector2 tangent = Vector2Normalize(Vector2Subtract(tip, base));
    if (Vector2Length(tangent) < 0.001f) tangent = {1, 0};
    const Vector2 normal{-tangent.y, tangent.x};
    const float headScale = std::min(1.0f, Vector2Distance(tip, base) / headLength);
    const Vector2 left = Vector2Add(base, Vector2Scale(normal, headWidth * headScale * 0.5f));
    const Vector2 right = Vector2Subtract(base, Vector2Scale(normal, headWidth * headScale * 0.5f));
    DrawTriangle(tip, right, left, color);
}

std::vector<unsigned char> Renderer::captureRgba() {
    Image image = LoadImageFromTexture(target_.texture);
    ImageFlipVertical(&image);
    ImageFormat(&image, PIXELFORMAT_UNCOMPRESSED_R8G8B8A8);
    const std::size_t size = static_cast<std::size_t>(image.width) * image.height * 4;
    const auto* pixels = static_cast<const unsigned char*>(image.data);
    std::vector<unsigned char> result(pixels, pixels + size);
    UnloadImage(image);
    return result;
}

void Renderer::savePng(const std::filesystem::path& path) {
    std::filesystem::create_directories(path.parent_path());
    Image image = LoadImageFromTexture(target_.texture);
    ImageFlipVertical(&image);
    if (!ExportImage(image, path.string().c_str())) {
        UnloadImage(image);
        throw std::runtime_error("Failed to write PNG: " + path.string());
    }
    UnloadImage(image);
}

} // namespace chem
