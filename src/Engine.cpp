#include "Engine.hpp"

extern "C" {
#include <lauxlib.h>
#include <lua.h>
}

#include <algorithm>
#include <array>
#include <cmath>
#include <set>
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

std::vector<std::string> propertyParts(const std::string& value) {
    std::vector<std::string> result;std::size_t start=0;
    while(start<=value.size()){const std::size_t end=value.find(':',start);result.push_back(value.substr(start,end==std::string::npos?value.size()-start:end-start));if(end==std::string::npos)break;start=end+1;}
    return result;
}

std::optional<double> moleculeNumericBase(const Object& object,const std::string& property) {
    if(!object.molecule)return std::nullopt;const auto parts=propertyParts(property);if(parts.size()<3)return std::nullopt;
    if(parts[0]=="atom"){const core::Atom* value=object.molecule->atom(parts[1]);if(!value)return std::nullopt;if(parts[2]=="x")return value->position.x;if(parts[2]=="y")return value->position.y;if(parts[2]=="alpha")return value->alpha;if(parts[2]=="hidden")return value->hidden?1.0:0.0;if(parts.size()==4&&parts[2]=="color"){if(parts[3]=="r")return value->color.red;if(parts[3]=="g")return value->color.green;if(parts[3]=="b")return value->color.blue;}}
    if(parts[0]=="bond"){const core::Bond* value=object.molecule->bond(parts[1]);if(!value)return std::nullopt;if(parts[2]=="alpha")return value->alpha;if(parts[2]=="visible")return value->visible?1.0:0.0;if(parts.size()==4&&parts[2]=="color"){if(parts[3]=="r")return value->color.red;if(parts[3]=="g")return value->color.green;if(parts[3]=="b")return value->color.blue;}}
    if(parts[0]=="adornment"){const core::AtomAdornment* value=object.molecule->adornment(parts[1]);if(!value)return std::nullopt;if(parts[2]=="x")return value->offset.x;if(parts[2]=="y")return value->offset.y;if(parts[2]=="alpha")return value->alpha;if(parts.size()==4&&parts[2]=="color"){if(parts[3]=="r")return value->color.red;if(parts[3]=="g")return value->color.green;if(parts[3]=="b")return value->color.blue;}}
    return std::nullopt;
}

std::optional<std::string> moleculeStringBase(const Object& object,const std::string& property) {
    if(!object.molecule)return std::nullopt;const auto parts=propertyParts(property);if(parts.size()!=3)return std::nullopt;
    if(parts[0]=="atom"){const core::Atom* value=object.molecule->atom(parts[1]);if(value&&parts[2]=="element")return value->element;}
    if(parts[0]=="bond"){const core::Bond* value=object.molecule->bond(parts[1]);if(!value)return std::nullopt;if(parts[2]=="type")return core::toString(value->type);if(parts[2]=="secondary")return core::toString(value->secondaryLineSide);if(parts[2]=="stereo")return core::toString(value->stereo);}
    if(parts[0]=="adornment"){const core::AtomAdornment* value=object.molecule->adornment(parts[1]);if(value&&parts[2]=="text")return value->text;}
    return std::nullopt;
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
        if(const auto base=moleculeNumericBase(object,property))track.base=*base;
        else {lua_rawgeti(state_, LUA_REGISTRYINDEX, object.luaRef);lua_getfield(state_, -1, property.c_str());track.base = lua_isnumber(state_, -1) ? lua_tonumber(state_, -1) : 0.0;lua_pop(state_, 2);}
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
        if(const auto base=moleculeStringBase(object,property))track.base=*base;
        else {lua_rawgeti(state_, LUA_REGISTRYINDEX, object.luaRef);lua_getfield(state_, -1, property.c_str());if (lua_isstring(state_, -1)) track.base = lua_tostring(state_, -1);lua_pop(state_, 2);}
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

void Engine::addAtomTween(Object& object, const std::string& atomId, int start, int duration,
                          double x, double y, Ease ease) {
    if (!object.molecule) throw std::runtime_error("Atom coordinates require a molecule object");
    const core::Atom* atom = object.molecule->atom(atomId);
    if (!atom) throw std::runtime_error("Unknown atom stable ID: " + atomId);
    const std::string xKey = "atom:" + atomId + ":x";
    const std::string yKey = "atom:" + atomId + ":y";
    object.numericTracks.try_emplace(xKey, NumericTrack{atom->position.x, {}});
    object.numericTracks.try_emplace(yKey, NumericTrack{atom->position.y, {}});
    addNumericTween(object, xKey, start, duration, x, ease);
    addNumericTween(object, yKey, start, duration, y, ease);
}

void Engine::addDetach(Object& source,Object& destination,int frame,std::vector<std::string> atoms,std::vector<std::string> bonds){topologyEvents_.push_back({TopologyEventKind::Detach,frame,source.id,destination.id,std::move(atoms),std::move(bonds),std::nullopt,nextOrder_++});}
void Engine::addMerge(Object& source,Object& destination,int frame,std::optional<core::Bond> newBond){topologyEvents_.push_back({TopologyEventKind::Merge,frame,source.id,destination.id,{},{},std::move(newBond),nextOrder_++});}

std::optional<core::Molecule> Engine::moleculeAt(int objectId,int frame) const {
    std::map<int,core::Molecule> values;for(const auto& object:objects_)if(object->molecule)values.emplace(object->id,*object->molecule);
    const auto objectFor=[&](int id)->const Object*{const auto found=byId_.find(id);return found==byId_.end()?nullptr:found->second;};
    const auto valueAt=[&](const Object* object,const std::string& key,int at,double fallback){if(!object)return fallback;if(auto it=object->numericTracks.find(key);it!=object->numericTracks.end())return it->second.valueAt(at);return fallback;};
    const auto toWorld=[&](const Object* object,core::Point point,int at){const double sx=valueAt(object,"scale_x",at,1),sy=valueAt(object,"scale_y",at,1),angle=valueAt(object,"rotation",at,0)*3.14159265358979323846/180.0,c=std::cos(angle),s=std::sin(angle);point={point.x*sx,point.y*sy};return core::Point{valueAt(object,"x",at,0)+point.x*c-point.y*s,valueAt(object,"y",at,0)+point.x*s+point.y*c};};
    const auto fromWorld=[&](const Object* object,core::Point point,int at){point.x-=valueAt(object,"x",at,0);point.y-=valueAt(object,"y",at,0);const double angle=-valueAt(object,"rotation",at,0)*3.14159265358979323846/180.0,c=std::cos(angle),s=std::sin(angle),x=point.x*c-point.y*s,y=point.x*s+point.y*c;double sx=valueAt(object,"scale_x",at,1),sy=valueAt(object,"scale_y",at,1);if(std::abs(sx)<1e-9)sx=sx<0?-1e-9:1e-9;if(std::abs(sy)<1e-9)sy=sy<0?-1e-9:1e-9;return core::Point{x/sx,y/sy};};
    std::vector<const TopologyEvent*> ordered;for(const TopologyEvent& event:topologyEvents_)if(event.frame<=frame)ordered.push_back(&event);std::stable_sort(ordered.begin(),ordered.end(),[](const auto* a,const auto* b){return a->frame!=b->frame?a->frame<b->frame:a->order<b->order;});
    for(const TopologyEvent* event:ordered){auto source=values.find(event->sourceObject),destination=values.find(event->destinationObject);if(source==values.end()||destination==values.end()||source==destination)continue;const Object* sourceObject=objectFor(event->sourceObject);const Object* destinationObject=objectFor(event->destinationObject);
        std::set<std::string> atoms(event->atoms.begin(),event->atoms.end()),bonds(event->bonds.begin(),event->bonds.end());if(event->kind==TopologyEventKind::Merge)for(const core::Atom& atom:source->second.atoms)atoms.insert(atom.id);
        for(auto it=source->second.atoms.begin();it!=source->second.atoms.end();)if(atoms.contains(it->id)){it->position.x=valueAt(sourceObject,"atom:"+it->id+":x",event->frame,it->position.x);it->position.y=valueAt(sourceObject,"atom:"+it->id+":y",event->frame,it->position.y);it->position=fromWorld(destinationObject,toWorld(sourceObject,it->position,event->frame),event->frame);destination->second.atoms.push_back(std::move(*it));it=source->second.atoms.erase(it);}else ++it;
        for(auto it=source->second.bonds.begin();it!=source->second.bonds.end();)if(event->kind==TopologyEventKind::Merge||bonds.contains(it->id)||(atoms.contains(it->atomA)&&atoms.contains(it->atomB))){destination->second.bonds.push_back(std::move(*it));it=source->second.bonds.erase(it);}else{if(atoms.contains(it->atomA)||atoms.contains(it->atomB))it->alive=false;++it;}
        for(auto it=source->second.adornments.begin();it!=source->second.adornments.end();)if(atoms.contains(it->atomId)){destination->second.adornments.push_back(std::move(*it));it=source->second.adornments.erase(it);}else ++it;
        if(event->kind==TopologyEventKind::Merge){source->second.retired=true;source->second.visible=false;if(event->newBond)destination->second.bonds.push_back(*event->newBond);}
    }
    const auto found=values.find(objectId);if(found==values.end())return std::nullopt;return found->second;
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
