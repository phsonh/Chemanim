#include "Engine.hpp"

extern "C" {
#include <lauxlib.h>
#include <lua.h>
}

#include <algorithm>
#include <array>
#include <cmath>
#include <stdexcept>

namespace chem {

namespace {
double applyEase(Ease ease, double t) {
    t = std::clamp(t, 0.0, 1.0);
    switch (ease) {
        case Ease::Linear: return t;
        case Ease::InQuad: return t * t;
        case Ease::OutQuad: return 1.0 - (1.0 - t) * (1.0 - t);
        case Ease::InOutQuad:
            return t < 0.5 ? 2.0 * t * t : 1.0 - std::pow(-2.0 * t + 2.0, 2.0) / 2.0;
        case Ease::InCubic: return t * t * t;
        case Ease::OutCubic: return 1.0 - std::pow(1.0 - t, 3.0);
        case Ease::InOutCubic:
            return t < 0.5 ? 4.0 * t * t * t : 1.0 - std::pow(-2.0 * t + 2.0, 3.0) / 2.0;
        case Ease::SmoothStep: return t * t * (3.0 - 2.0 * t);
        case Ease::Step: return t >= 1.0 ? 1.0 : 0.0;
    }
    return t;
}
} // namespace

double NumericTrack::valueAt(int frame) const {
    double value = base;
    std::vector<const Segment*> ordered;
    ordered.reserve(segments.size());
    for (const auto& segment : segments) ordered.push_back(&segment);
    std::stable_sort(ordered.begin(), ordered.end(), [](const Segment* a, const Segment* b) {
        if (a->start != b->start) return a->start < b->start;
        return a->order < b->order;
    });
    for (const Segment* segment : ordered) {
        if (frame < segment->start) continue;
        if (frame >= segment->cancelledAt) {
            value = segment->cancelledValue;
            continue;
        }
        if (segment->end <= segment->start || frame >= segment->end) {
            value = segment->to;
        } else {
            const double t = static_cast<double>(frame - segment->start) /
                             static_cast<double>(segment->end - segment->start);
            value = segment->from + (segment->to - segment->from) * applyEase(segment->ease, t);
        }
    }
    return value;
}

std::string StringTrack::valueAt(int frame) const {
    std::string value = base;
    std::vector<const StringEvent*> ordered;
    ordered.reserve(events.size());
    for (const auto& event : events) ordered.push_back(&event);
    std::stable_sort(ordered.begin(), ordered.end(), [](const StringEvent* a, const StringEvent* b) {
        if (a->frame != b->frame) return a->frame < b->frame;
        return a->order < b->order;
    });
    for (const StringEvent* event : ordered) {
        if (frame >= event->frame) value = event->value;
    }
    return value;
}

Engine::Engine(lua_State* state) : state_(state) {}

Engine::~Engine() {
    if (!state_) return;
    for (const auto& object : objects_) {
        if (object->luaRef != LUA_NOREF) luaL_unref(state_, LUA_REGISTRYINDEX, object->luaRef);
    }
    for (const int ref : frameCallbacks_) luaL_unref(state_, LUA_REGISTRYINDEX, ref);
}

Object& Engine::createObject(int tableIndex, const std::string& kind) {
    tableIndex = lua_absindex(state_, tableIndex);
    auto object = std::make_unique<Object>();
    object->id = nextId_++;
    object->kind = kind;

    lua_pushvalue(state_, tableIndex);
    object->luaRef = luaL_ref(state_, LUA_REGISTRYINDEX);
    lua_pushinteger(state_, object->id);
    lua_setfield(state_, tableIndex, "__id");
    lua_pushstring(state_, kind.c_str());
    lua_setfield(state_, tableIndex, "kind");

    lua_getfield(state_, tableIndex, "name");
    if (lua_isstring(state_, -1)) object->name = lua_tostring(state_, -1);
    lua_pop(state_, 1);

    Object& result = *object;
    byId_[object->id] = object.get();
    objects_.push_back(std::move(object));
    return result;
}

Object* Engine::objectFromTable(int tableIndex) {
    tableIndex = lua_absindex(state_, tableIndex);
    if (!lua_istable(state_, tableIndex)) return nullptr;
    lua_getfield(state_, tableIndex, "__id");
    const int id = static_cast<int>(lua_tointeger(state_, -1));
    lua_pop(state_, 1);
    return objectById(id);
}

Object* Engine::objectById(int id) {
    const auto it = byId_.find(id);
    return it == byId_.end() ? nullptr : it->second;
}

void Engine::scheduleRemove(Object& object, int frame) {
    object.deadFrame = std::min(object.deadFrame, frame);
}

unsigned long long Engine::addNumericTween(Object& object, const std::string& property, int start,
                                           int duration, double target, Ease ease) {
    auto [it, inserted] = object.numericTracks.try_emplace(property);
    NumericTrack& track = it->second;
    if (inserted) {
        lua_rawgeti(state_, LUA_REGISTRYINDEX, object.luaRef);
        lua_getfield(state_, -1, property.c_str());
        track.base = lua_isnumber(state_, -1) ? lua_tonumber(state_, -1) : 0.0;
        lua_pop(state_, 2);
    }
    const double from = track.valueAt(start);
    // A later command for the same property owns the track from this frame
    // onward. Preserve the old curve before `start`, but prevent its pending
    // tail from extending the schedule or resurfacing after the new tween.
    for (auto& segment : track.segments) {
        const int effectiveEnd = std::min(segment.end, segment.cancelledAt);
        if (segment.start <= start && start < effectiveEnd) {
            segment.cancelledAt = start;
            segment.cancelledValue = from;
        }
    }
    const unsigned long long order = nextOrder_++;
    track.segments.push_back(Segment{
        start, start + std::max(0, duration), from, target, ease, order
    });
    return order;
}

unsigned long long Engine::addStringKey(Object& object, const std::string& property, int frame,
                                        std::string value) {
    auto [it, inserted] = object.stringTracks.try_emplace(property);
    StringTrack& track = it->second;
    if (inserted) {
        lua_rawgeti(state_, LUA_REGISTRYINDEX, object.luaRef);
        lua_getfield(state_, -1, property.c_str());
        if (lua_isstring(state_, -1)) track.base = lua_tostring(state_, -1);
        lua_pop(state_, 2);
    }
    const unsigned long long order = nextOrder_++;
    track.events.push_back(StringEvent{frame, std::move(value), order});
    return order;
}

void Engine::addImageTransition(Object& object, int start, int duration,
                                std::string targetTexture, Ease ease,
                                std::optional<double> targetX,
                                std::optional<double> targetY) {
    duration = std::max(0, duration);
    const auto numberAt = [&](const std::string& key) {
        const auto found = object.numericTracks.find(key);
        if (found != object.numericTracks.end()) return found->second.valueAt(start);
        lua_rawgeti(state_, LUA_REGISTRYINDEX, object.luaRef);
        lua_getfield(state_, -1, key.c_str());
        const double value = lua_isnumber(state_, -1) ? lua_tonumber(state_, -1) : 0.0;
        lua_pop(state_, 2);
        return value;
    };
    const double sourceX = numberAt("x");
    const double sourceY = numberAt("y");
    const double destinationX = targetX.value_or(sourceX);
    const double destinationY = targetY.value_or(sourceY);

    std::vector<ImageLayer> sourceLayers;
    if (const auto currentBlend = imageBlendAt(object, start)) {
        sourceLayers = currentBlend->layers;
    }
    auto trackIt = object.stringTracks.find("texture");
    std::string sourceTexture;
    if (trackIt != object.stringTracks.end()) {
        sourceTexture = trackIt->second.valueAt(start);
    } else {
        lua_rawgeti(state_, LUA_REGISTRYINDEX, object.luaRef);
        lua_getfield(state_, -1, "texture");
        if (lua_isstring(state_, -1)) sourceTexture = lua_tostring(state_, -1);
        lua_pop(state_, 2);
    }
    if (sourceLayers.empty() && !sourceTexture.empty()) {
        sourceLayers.push_back(ImageLayer{sourceTexture, sourceX, sourceY, 1.0});
    }

    // Cancel an in-flight image transition and remove its not-yet-fired
    // texture/position completion keys. The new transition starts from the
    // exact composite visible at this frame.
    for (auto& transition : object.imageTransitions) {
        const int effectiveEnd = std::min(transition.end, transition.cancelledAt);
        if (transition.start <= start && start < effectiveEnd) {
            transition.cancelledAt = start;
            if (auto textureTrack = object.stringTracks.find("texture");
                textureTrack != object.stringTracks.end()) {
                std::erase_if(textureTrack->second.events, [&](const StringEvent& event) {
                    return event.order == transition.textureCompletionOrder;
                });
            }
            for (const auto& [key, completionOrder] : std::array{
                     std::pair{"x", transition.xCompletionOrder},
                     std::pair{"y", transition.yCompletionOrder}}) {
                if (auto numericTrack = object.numericTracks.find(key);
                    numericTrack != object.numericTracks.end()) {
                    std::erase_if(numericTrack->second.segments, [&](const Segment& segment) {
                        return segment.order == completionOrder;
                    });
                }
            }
        }
    }

    if (duration == 0 || sourceLayers.empty()) {
        addStringKey(object, "texture", start, std::move(targetTexture));
        addNumericTween(object, "x", start, 0, destinationX, Ease::Step);
        addNumericTween(object, "y", start, 0, destinationY, Ease::Step);
        return;
    }
    ImageTransition transition;
    transition.start = start;
    transition.end = start + duration;
    transition.fromLayers = std::move(sourceLayers);
    transition.toTexture = targetTexture;
    transition.toX = destinationX;
    transition.toY = destinationY;
    transition.ease = ease;
    transition.order = nextOrder_++;
    transition.textureCompletionOrder = addStringKey(
        object, "texture", transition.end, targetTexture);
    transition.xCompletionOrder = addNumericTween(
        object, "x", transition.end, 0, destinationX, Ease::Step);
    transition.yCompletionOrder = addNumericTween(
        object, "y", transition.end, 0, destinationY, Ease::Step);
    object.imageTransitions.push_back(std::move(transition));
}

std::optional<ImageBlend> Engine::imageBlendAt(const Object& object, int frame) const {
    const ImageTransition* selected = nullptr;
    for (const auto& transition : object.imageTransitions) {
        if (frame < transition.start || frame >= std::min(transition.end, transition.cancelledAt)) continue;
        if (!selected || transition.start > selected->start ||
            (transition.start == selected->start && transition.order > selected->order)) {
            selected = &transition;
        }
    }
    if (!selected) return std::nullopt;
    const double duration = std::max(1, selected->end - selected->start);
    const double t = static_cast<double>(frame - selected->start) / duration;
    const double mix = applyEase(selected->ease, t);
    ImageBlend blend;
    blend.layers.reserve(selected->fromLayers.size() + 1);
    for (const auto& layer : selected->fromLayers) {
        ImageLayer faded = layer;
        faded.alpha *= 1.0 - mix;
        blend.layers.push_back(std::move(faded));
    }
    blend.layers.push_back(ImageLayer{
        selected->toTexture, selected->toX, selected->toY, mix
    });
    return blend;
}

void Engine::writeNumber(Object& object, const std::string& key, double value) {
    lua_rawgeti(state_, LUA_REGISTRYINDEX, object.luaRef);
    lua_pushnumber(state_, value);
    lua_setfield(state_, -2, key.c_str());
    lua_pop(state_, 1);
}

void Engine::writeString(Object& object, const std::string& key, const std::string& value) {
    lua_rawgeti(state_, LUA_REGISTRYINDEX, object.luaRef);
    lua_pushlstring(state_, value.data(), value.size());
    lua_setfield(state_, -2, key.c_str());
    lua_pop(state_, 1);
}

void Engine::applyFrame(int frame) {
    for (const auto& object : objects_) {
        for (const auto& [key, track] : object->numericTracks) writeNumber(*object, key, track.valueAt(frame));
        for (const auto& [key, track] : object->stringTracks) writeString(*object, key, track.valueAt(frame));
    }

    for (const int ref : frameCallbacks_) {
        lua_rawgeti(state_, LUA_REGISTRYINDEX, ref);
        lua_pushinteger(state_, frame);
        if (lua_pcall(state_, 1, 0, 0) != LUA_OK) {
            const std::string message = lua_tostring(state_, -1);
            lua_pop(state_, 1);
            throw std::runtime_error("on_frame callback failed: " + message);
        }
    }
}

void Engine::registerTexture(std::string name, std::filesystem::path path,
                             double anchorX, double anchorY) {
    if (path.is_relative()) path = scriptDirectory / path;
    TextureAsset asset{name, std::filesystem::weakly_canonical(path),
                       std::clamp(anchorX, 0.0, 1.0), std::clamp(anchorY, 0.0, 1.0)};
    textures_[name] = std::move(asset);
}

void Engine::addFrameCallback(int luaRef) { frameCallbacks_.push_back(luaRef); }

int Engine::maxScheduledFrame() const {
    int maximum = 0;
    for (const auto& object : objects_) {
        if (object->deadFrame != std::numeric_limits<int>::max()) maximum = std::max(maximum, object->deadFrame);
        for (const auto& [_, track] : object->numericTracks) {
            for (const auto& segment : track.segments) {
                maximum = std::max(maximum, std::min(segment.end, segment.cancelledAt));
            }
        }
        for (const auto& [_, track] : object->stringTracks) {
            for (const auto& event : track.events) maximum = std::max(maximum, event.frame);
        }
    }
    return maximum;
}

Ease Engine::parseEase(const std::string& name) {
    static const std::unordered_map<std::string, Ease> values{
        {"linear", Ease::Linear}, {"in_quad", Ease::InQuad}, {"out_quad", Ease::OutQuad},
        {"in_out_quad", Ease::InOutQuad}, {"in_cubic", Ease::InCubic},
        {"out_cubic", Ease::OutCubic}, {"in_out_cubic", Ease::InOutCubic},
        {"smooth", Ease::SmoothStep}, {"smoothstep", Ease::SmoothStep}, {"step", Ease::Step}
    };
    const auto it = values.find(name);
    return it == values.end() ? Ease::Linear : it->second;
}

double Engine::easeValue(Ease ease, double t) { return applyEase(ease, t); }

} // namespace chem
