#include "Renderer.hpp"
#include "SvgRasterizer.hpp"

extern "C" {
#include <lua.h>
}

#include <raymath.h>

#include <algorithm>
#include <array>
#include <cmath>
#include <chrono>
#include <cstdio>
#include <filesystem>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace chem {

Renderer::Renderer(Engine& engine) : engine_(engine) {}

Renderer::~Renderer() {
    if (!initialized_) return;
    for (auto& [_, texture] : textures_) UnloadTexture(texture);
    for (auto& [_, entry] : moleculeSvgs_) {
        if (entry.texture.id != 0) UnloadTexture(entry.texture);
    }
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

Color Renderer::objectColor(int tableIndex,const char* scope) const {
    const auto channel = [&](const char* key, double fallback) {
        return static_cast<unsigned char>(std::clamp(number(tableIndex,key,fallback)*engine_.globalValue(scope,key,currentFrame_)/255.0,0.0,255.0));
    };
    const double alpha = std::clamp(number(tableIndex,"alpha",1.0)*engine_.globalValue(scope,"alpha",currentFrame_)/255.0,0.0,1.0);
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
    else if (object.kind == "molecule") drawAcsMolecule(table, object);
    else if (object.kind == "arrow") drawArrow(table);
    lua_pop(state, 1);
}

void Renderer::drawAcsMolecule(int table, const Object& object) {
    const auto evaluatedMolecule=engine_.moleculeAt(object.id,currentFrame_);if(!evaluatedMolecule||evaluatedMolecule->atoms.empty())return;
    const float renderWidth = static_cast<float>(engine_.scene.width * supersample_);
    const float renderHeight = static_cast<float>(engine_.scene.height * supersample_);
    const float canvasScaleX = renderWidth / engine_.scene.logicWidth;
    const float canvasScaleY = renderHeight / engine_.scene.logicHeight;
    const float scaleX = static_cast<float>(number(table,"scale_x",1)*engine_.globalValue("molecule","scale_x",currentFrame_));
    const float scaleY = static_cast<float>(number(table,"scale_y",1)*engine_.globalValue("molecule","scale_y",currentFrame_));
    const float rasterScale = static_cast<float>(engine_.scene.viewZoom * supersample_) *
                              std::max(std::abs(scaleX), std::abs(scaleY));
    SvgCacheEntry& cache = moleculeSvgs_[object.id];
    if (!cache.hasViewport) {
        core::Molecule extent=*evaluatedMolecule;if(const auto finalMolecule=engine_.moleculeAt(object.id,engine_.maxScheduledFrame());finalMolecule)extent.atoms.insert(extent.atoms.end(),finalMolecule->atoms.begin(),finalMolecule->atoms.end());
        double minX = extent.atoms.front().position.x, maxX = minX;
        double minY = extent.atoms.front().position.y, maxY = minY;
        for (const auto& atom : extent.atoms) {
            minX = std::min(minX, atom.position.x); maxX = std::max(maxX, atom.position.x);
            minY = std::min(minY, atom.position.y); maxY = std::max(maxY, atom.position.y);
        }
        const double reference = std::max(0.01, evaluatedMolecule->referenceBondLength);
        const double pixelsPerUnit = 14.4 / reference;
        cache.viewport.width = std::max(64, static_cast<int>(std::ceil((maxX - minX) * pixelsPerUnit + 64.0)));
        cache.viewport.height = std::max(64, static_cast<int>(std::ceil((maxY - minY) * pixelsPerUnit + 64.0)));
        cache.viewport.pixelsPerUnit = pixelsPerUnit;
        cache.viewport.center = {(minX + maxX) * .5, (minY + maxY) * .5};
        cache.hasViewport = true;
    }
    core::Molecule currentMolecule = *evaluatedMolecule;
    const Color moleculeTint=objectColor(table,"molecule");currentMolecule.color={moleculeTint.r,moleculeTint.g,moleculeTint.b};
    for (auto& atom : currentMolecule.atoms) {
        const auto x = object.numericTracks.find("atom:" + atom.id + ":x");
        const auto y = object.numericTracks.find("atom:" + atom.id + ":y");
        if (x != object.numericTracks.end()) atom.position.x = x->second.valueAt(currentFrame_);
        if (y != object.numericTracks.end()) atom.position.y = y->second.valueAt(currentFrame_);
        if(const auto value=object.stringTracks.find("atom:"+atom.id+":label");value!=object.stringTracks.end())atom.alias=value->second.valueAt(currentFrame_);
        if(const auto value=object.numericTracks.find("atom:"+atom.id+":hidden");value!=object.numericTracks.end())atom.hidden=value->second.valueAt(currentFrame_)>.5;
        if(const auto value=object.numericTracks.find("atom:"+atom.id+":alpha");value!=object.numericTracks.end())atom.alpha=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));
        if(const auto value=object.numericTracks.find("atom:"+atom.id+":color:r");value!=object.numericTracks.end())atom.color.red=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));
        if(const auto value=object.numericTracks.find("atom:"+atom.id+":color:g");value!=object.numericTracks.end())atom.color.green=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));
        if(const auto value=object.numericTracks.find("atom:"+atom.id+":color:b");value!=object.numericTracks.end())atom.color.blue=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));
    }
    for(auto& bond:currentMolecule.bonds){
        if(const auto value=object.stringTracks.find("bond:"+bond.id+":type");value!=object.stringTracks.end()){
            bond.type=core::bondTypeFromString(value->second.valueAt(currentFrame_));
        }
        if(const auto value=object.stringTracks.find("bond:"+bond.id+":secondary");value!=object.stringTracks.end())bond.secondaryLineSide=core::secondaryLineSideFromString(value->second.valueAt(currentFrame_));
        if(const auto value=object.stringTracks.find("bond:"+bond.id+":stereo");value!=object.stringTracks.end())bond.stereo=core::bondStereoFromString(value->second.valueAt(currentFrame_));
        if(const auto value=object.numericTracks.find("bond:"+bond.id+":visible");value!=object.numericTracks.end())bond.visible=value->second.valueAt(currentFrame_)>.5;
        if(const auto value=object.numericTracks.find("bond:"+bond.id+":alpha");value!=object.numericTracks.end())bond.alpha=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));
        if(const auto value=object.numericTracks.find("bond:"+bond.id+":color:r");value!=object.numericTracks.end())bond.color.red=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));
        if(const auto value=object.numericTracks.find("bond:"+bond.id+":color:g");value!=object.numericTracks.end())bond.color.green=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));
        if(const auto value=object.numericTracks.find("bond:"+bond.id+":color:b");value!=object.numericTracks.end())bond.color.blue=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));
    }
    for(auto& adornment:currentMolecule.adornments){const std::string prefix="adornment:"+adornment.id+":";if(const auto value=object.numericTracks.find(prefix+"x");value!=object.numericTracks.end())adornment.offset.x=value->second.valueAt(currentFrame_);if(const auto value=object.numericTracks.find(prefix+"y");value!=object.numericTracks.end())adornment.offset.y=value->second.valueAt(currentFrame_);if(const auto value=object.numericTracks.find(prefix+"alpha");value!=object.numericTracks.end())adornment.alpha=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));if(const auto value=object.stringTracks.find(prefix+"text");value!=object.stringTracks.end())adornment.text=value->second.valueAt(currentFrame_);if(const auto value=object.numericTracks.find(prefix+"color:r");value!=object.numericTracks.end())adornment.color.red=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));if(const auto value=object.numericTracks.find(prefix+"color:g");value!=object.numericTracks.end())adornment.color.green=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));if(const auto value=object.numericTracks.find(prefix+"color:b");value!=object.numericTracks.end())adornment.color.blue=static_cast<int>(std::round(value->second.valueAt(currentFrame_)));}
    std::ostringstream geometry; geometry << std::setprecision(12);
    for (const auto& atom : currentMolecule.atoms) geometry << atom.id << ':' << atom.element << ':' << atom.alias << ':'
        << static_cast<int>(atom.labelSide) << ':' << static_cast<int>(atom.numberStyle) << ':'
        << atom.position.x << ':' << atom.position.y << ':' << atom.alive << ':' << atom.alpha << ':'
        << atom.color.red << ':' << atom.color.green << ':' << atom.color.blue << ';';
    for (const auto& bond : currentMolecule.bonds) geometry << bond.id << ':' << bond.atomA << ':' << bond.atomB << ':' << static_cast<int>(bond.type) << ':' << static_cast<int>(bond.secondaryLineSide) << ':' << static_cast<int>(bond.stereo) << ':' << bond.alive << ':' << bond.alpha << ':' << bond.color.red << ':' << bond.color.green << ':' << bond.color.blue << ';';
    for(const auto& value:currentMolecule.adornments)geometry<<value.id<<':'<<value.atomId<<':'<<value.text<<':'<<value.offset.x<<':'<<value.offset.y<<':'<<value.alpha<<':'<<value.alive<<';';
    const std::string geometryKey = geometry.str();
    const bool geometryChanged = cache.geometryKey != geometryKey;
    if (geometryChanged) {
        const auto start = std::chrono::steady_clock::now(); const core::Style style;
        cache.svg = depictionCore_.depict(currentMolecule, style, cache.viewport).svg;
        profile_.svgGenerationMs += std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - start).count();
        cache.geometryKey = geometryKey; ++profile_.moleculeCacheMisses;
    } else ++profile_.moleculeCacheHits;
    if (cache.texture.id == 0 || geometryChanged ||
        std::abs(cache.rasterScale - rasterScale) > 0.001f) {
        if (cache.texture.id != 0) UnloadTexture(cache.texture);
        core::RasterProfile rasterProfile;
        Image image = rasterizeSvg(cache.svg, rasterScale, &rasterProfile);
        profile_.svgParsingMs += rasterProfile.parseMs;
        profile_.svgRasterizationMs += rasterProfile.rasterMs;
        const auto uploadStart = std::chrono::steady_clock::now();
        cache.texture = LoadTextureFromImage(image);
        profile_.textureUploadMs += std::chrono::duration<double, std::milli>(std::chrono::steady_clock::now() - uploadStart).count();
        UnloadImage(image);
        SetTextureFilter(cache.texture, TEXTURE_FILTER_BILINEAR);
        cache.rasterScale = rasterScale;
    }
    const double rotationDegrees=number(table,"rotation",0);const double radians=rotationDegrees*3.14159265358979323846/180.0;
    const double localX=cache.viewport.center.x*scaleX,localY=cache.viewport.center.y*scaleY;
    const double offsetX=localX*std::cos(radians)-localY*std::sin(radians),offsetY=localX*std::sin(radians)+localY*std::cos(radians);
    const float x = renderWidth * 0.5f + static_cast<float>(number(table, "x", 0)+offsetX) * canvasScaleX;
    const float y = renderHeight * 0.5f - static_cast<float>(number(table, "y", 0)+offsetY) * canvasScaleY;
    const float expectedX = static_cast<float>(engine_.scene.viewZoom * supersample_) * std::abs(scaleX);
    const float expectedY = static_cast<float>(engine_.scene.viewZoom * supersample_) * std::abs(scaleY);
    const float naturalWidth = cache.texture.width / rasterScale;
    const float naturalHeight = cache.texture.height / rasterScale;
    Rectangle source{0, 0, static_cast<float>(cache.texture.width), static_cast<float>(cache.texture.height)};
    if (scaleX < 0) source.width = -source.width;
    if (scaleY < 0) source.height = -source.height;
    Rectangle destination{x, y, naturalWidth * expectedX, naturalHeight * expectedY};
    const Vector2 origin{destination.width * 0.5f, destination.height * 0.5f};
    Color tint = WHITE;
    tint.a = objectColor(table,"molecule").a;
    DrawTexturePro(cache.texture, source, destination, origin,
                   static_cast<float>(rotationDegrees), tint);
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
    const Color baseColor = objectColor(table,"sprite");
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
    const float sx = static_cast<float>(number(table,"scale_x",1)*engine_.globalValue("arrow","scale_x",currentFrame_));
    const float sy = static_cast<float>(number(table,"scale_y",1)*engine_.globalValue("arrow","scale_y",currentFrame_));
    const float renderWidth = static_cast<float>(engine_.scene.width * supersample_);
    const float renderHeight = static_cast<float>(engine_.scene.height * supersample_);
    const float canvasScaleX = renderWidth / engine_.scene.logicWidth;
    const float canvasScaleY = renderHeight / engine_.scene.logicHeight;
    const float strokeScale = std::sqrt(canvasScaleX * canvasScaleY);
    const double anchorX=number(table,"x1",0),anchorY=number(table,"y1",0);
    const auto screenPoint = [&](const char* xKey, const char* yKey, double fallbackX, double fallbackY) {
        const float logicalX = ox + static_cast<float>(anchorX+(number(table,xKey,fallbackX)-anchorX)*sx);
        const float logicalY = oy + static_cast<float>(anchorY+(number(table,yKey,fallbackY)-anchorY)*sy);
        return Vector2{renderWidth * 0.5f + logicalX * canvasScaleX,
                       renderHeight * 0.5f - logicalY * canvasScaleY};
    };
    Vector2 p0 = screenPoint("x1", "y1", 0, 0);
    Vector2 p1 = screenPoint("cx1", "cy1", 100, 0);
    Vector2 p2 = screenPoint("cx2", "cy2", 200, 0);
    Vector2 p3 = screenPoint("x2", "y2", 300, 0);
    const float thickness = static_cast<float>(std::max(0.1,number(table,"thickness",3)*engine_.globalValue("arrow","width",currentFrame_))) * strokeScale;
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
    Color color = objectColor(table,"arrow");
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
