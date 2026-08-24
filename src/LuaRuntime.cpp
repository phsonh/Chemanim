#include "LuaRuntime.hpp"

extern "C" {
#include <lauxlib.h>
#include <lualib.h>
}

#include <algorithm>
#include <cctype>
#include <stdexcept>

namespace chem {

namespace {
constexpr const char* kObjectMetatable = "chemanim.object";

void pushClosure(lua_State* state, LuaRuntime* runtime, lua_CFunction function) {
    lua_pushlightuserdata(state, runtime);
    lua_pushcclosure(state, function, 1);
}

void pushBoundClosure(lua_State* state, LuaRuntime* runtime, int objectId, lua_CFunction function) {
    lua_pushlightuserdata(state, runtime);
    lua_pushinteger(state, objectId);
    lua_pushcclosure(state, function, 2);
}

double numberField(lua_State* state, int table, const char* key, double fallback) {
    table = lua_absindex(state, table);
    lua_getfield(state, table, key);
    const double result = lua_isnumber(state, -1) ? lua_tonumber(state, -1) : fallback;
    lua_pop(state, 1);
    return result;
}

std::string stringField(lua_State* state, int table, const char* key, std::string fallback) {
    table = lua_absindex(state, table);
    lua_getfield(state, table, key);
    if (lua_isstring(state, -1)) fallback = lua_tostring(state, -1);
    lua_pop(state, 1);
    return fallback;
}

ColorValue parseColor(lua_State* state, int index, ColorValue fallback) {
    if (lua_isstring(state, index)) {
        std::string text = lua_tostring(state, index);
        if (!text.empty() && text.front() == '#') text.erase(text.begin());
        if (text.size() == 6 || text.size() == 8) {
            try {
                fallback.r = static_cast<unsigned char>(std::stoul(text.substr(0, 2), nullptr, 16));
                fallback.g = static_cast<unsigned char>(std::stoul(text.substr(2, 2), nullptr, 16));
                fallback.b = static_cast<unsigned char>(std::stoul(text.substr(4, 2), nullptr, 16));
                if (text.size() == 8) fallback.a = static_cast<unsigned char>(std::stoul(text.substr(6, 2), nullptr, 16));
            } catch (...) {}
        }
    } else if (lua_istable(state, index)) {
        fallback.r = static_cast<unsigned char>(std::clamp(numberField(state, index, "r", fallback.r), 0.0, 255.0));
        fallback.g = static_cast<unsigned char>(std::clamp(numberField(state, index, "g", fallback.g), 0.0, 255.0));
        fallback.b = static_cast<unsigned char>(std::clamp(numberField(state, index, "b", fallback.b), 0.0, 255.0));
        fallback.a = static_cast<unsigned char>(std::clamp(numberField(state, index, "a", fallback.a), 0.0, 255.0));
    }
    return fallback;
}
} // namespace

LuaRuntime::LuaRuntime() {
    state_ = luaL_newstate();
    if (!state_) throw std::runtime_error("Unable to create Lua state");
    luaL_openlibs(state_);
    engine_ = std::make_unique<Engine>(state_);
    installApi();
}

LuaRuntime::~LuaRuntime() {
    engine_.reset();
    if (state_) lua_close(state_);
}

LuaRuntime& LuaRuntime::self(lua_State* state) {
    return *static_cast<LuaRuntime*>(lua_touserdata(state, lua_upvalueindex(1)));
}

int LuaRuntime::traceback(lua_State* state) {
    const char* message = lua_tostring(state, 1);
    if (message) luaL_traceback(state, state, message, 1);
    else lua_pushliteral(state, "(error object is not a string)");
    return 1;
}

void LuaRuntime::runScript(const std::filesystem::path& scriptPath) {
    const auto absolute = std::filesystem::absolute(scriptPath);
    engine_->scriptDirectory = absolute.parent_path();
    lua_pushcfunction(state_, traceback);
    const int handler = lua_gettop(state_);
    if (luaL_loadfile(state_, absolute.string().c_str()) != LUA_OK || lua_pcall(state_, 0, 0, handler) != LUA_OK) {
        const std::string message = lua_tostring(state_, -1) ? lua_tostring(state_, -1) : "unknown Lua error";
        lua_settop(state_, 0);
        throw std::runtime_error(message);
    }
    lua_settop(state_, 0);
    engine_->scene.endFrame = std::max({engine_->scene.endFrame, cursor_, engine_->maxScheduledFrame()});
}

void LuaRuntime::setDefaultNumber(int tableIndex, const char* key, double value) {
    tableIndex = lua_absindex(state_, tableIndex);
    lua_pushnumber(state_, value);
    lua_setfield(state_, tableIndex, key);
}

void LuaRuntime::setDefaultString(int tableIndex, const char* key, const char* value) {
    tableIndex = lua_absindex(state_, tableIndex);
    lua_pushstring(state_, value);
    lua_setfield(state_, tableIndex, key);
}

void LuaRuntime::copyTable(int fromIndex, int toIndex) {
    fromIndex = lua_absindex(state_, fromIndex);
    toIndex = lua_absindex(state_, toIndex);
    lua_pushnil(state_);
    while (lua_next(state_, fromIndex) != 0) {
        lua_pushvalue(state_, -2);
        lua_insert(state_, -2);
        lua_settable(state_, toIndex);
    }
}

Object& LuaRuntime::createObjectTable(const std::string& kind, int propertiesIndex) {
    if (propertiesIndex != 0) propertiesIndex = lua_absindex(state_, propertiesIndex);
    lua_newtable(state_);
    const int table = lua_gettop(state_);

    setDefaultNumber(table, "x", 0); setDefaultNumber(table, "y", 0);
    setDefaultNumber(table, "scale_x", 1); setDefaultNumber(table, "scale_y", 1);
    setDefaultNumber(table, "rotation", 0);
    setDefaultNumber(table, "alpha", kind == "arrow" ? 1 : 0);
    setDefaultNumber(table, "anchor_x", -1); setDefaultNumber(table, "anchor_y", -1);
    setDefaultNumber(table, "layer", 0); setDefaultNumber(table, "visible", 1);
    setDefaultNumber(table, "reveal", 1); setDefaultString(table, "reveal_dir", "ltr");
    const double defaultInk = (kind == "arrow" || kind == "molecule") ? 25 : 255;
    setDefaultNumber(table, "r", defaultInk);
    setDefaultNumber(table, "g", defaultInk);
    setDefaultNumber(table, "b", defaultInk);

    if (kind == "sprite") {
        setDefaultString(table, "texture", "");
    } else if (kind == "arrow") {
        setDefaultNumber(table, "x1", 0); setDefaultNumber(table, "y1", 0);
        setDefaultNumber(table, "x2", 0); setDefaultNumber(table, "y2", 0);
        setDefaultNumber(table, "cx1", 0); setDefaultNumber(table, "cy1", 0);
        setDefaultNumber(table, "cx2", 0); setDefaultNumber(table, "cy2", 0);
        setDefaultNumber(table, "thickness", 3);
        setDefaultNumber(table, "progress", 0);
    }

    if (propertiesIndex != 0 && lua_istable(state_, propertiesIndex)) copyTable(propertiesIndex, table);
    luaL_getmetatable(state_, kObjectMetatable);
    lua_setmetatable(state_, table);
    Object& object = engine_->createObject(table, kind);
    object.bornFrame = cursor_;
    currentObjectId_ = object.id;
    bindObjectMethods(table, object);
    return object;
}

void LuaRuntime::readMolecule(Object& object, int tableIndex) {
    tableIndex = lua_absindex(state_, tableIndex);
    auto molecule = std::make_unique<core::Molecule>();
    molecule->sourceSmiles = stringField(state_, tableIndex, "source_smiles", "");
    molecule->referenceBondLength = numberField(state_, tableIndex, "reference_bond_length", 1.0);

    lua_getfield(state_, tableIndex, "atoms");
    if (!lua_istable(state_, -1)) {
        lua_pop(state_, 1);
        throw std::runtime_error("chem.NewMol: compiled molecule data requires an atoms table");
    }
    const int atomsTable = lua_gettop(state_);
    const std::size_t atomCount = lua_rawlen(state_, atomsTable);
    molecule->atoms.reserve(atomCount);
    for (std::size_t i = 1; i <= atomCount; ++i) {
        lua_rawgeti(state_, atomsTable, static_cast<lua_Integer>(i));
        if (!lua_istable(state_, -1)) {
            lua_pop(state_, 2);
            throw std::runtime_error("chem.NewMol: every atom must be a table");
        }
        core::Atom atom;
        atom.id = stringField(state_, -1, "id", "");
        atom.element = stringField(state_, -1, "element", "C");
        atom.alias = stringField(state_, -1, "alias", "");
        atom.isotope = static_cast<int>(numberField(state_, -1, "isotope", 0));
        atom.formalCharge = static_cast<int>(numberField(state_, -1, "formal_charge", 0));
        atom.radicalElectrons = static_cast<int>(numberField(state_, -1, "radical_electrons", 0));
        atom.implicitHydrogens = static_cast<int>(numberField(state_, -1, "implicit_hydrogens", 0));
        atom.aromatic = numberField(state_, -1, "aromatic", 0) != 0;
        atom.hidden = numberField(state_, -1, "hidden", 0) != 0;
        atom.position.x = numberField(state_, -1, "x", 0);
        atom.position.y = numberField(state_, -1, "y", 0);
        if (atom.id.empty()) {
            lua_pop(state_, 2);
            throw std::runtime_error("chem.NewMol: atom stable ID cannot be empty");
        }
        molecule->atoms.push_back(std::move(atom));
        lua_pop(state_, 1);
    }
    lua_pop(state_, 1);

    lua_getfield(state_, tableIndex, "bonds");
    if (!lua_istable(state_, -1)) {
        lua_pop(state_, 1);
        throw std::runtime_error("chem.NewMol: compiled molecule data requires a bonds table");
    }
    const int bondsTable = lua_gettop(state_);
    const std::size_t bondCount = lua_rawlen(state_, bondsTable);
    molecule->bonds.reserve(bondCount);
    for (std::size_t i = 1; i <= bondCount; ++i) {
        lua_rawgeti(state_, bondsTable, static_cast<lua_Integer>(i));
        if (!lua_istable(state_, -1)) {
            lua_pop(state_, 2);
            throw std::runtime_error("chem.NewMol: every bond must be a table");
        }
        core::Bond bond;
        bond.id = stringField(state_, -1, "id", "");
        bond.atomA = stringField(state_, -1, "a", "");
        bond.atomB = stringField(state_, -1, "b", "");
        const double order = numberField(state_, -1, "order", 1);
        bond.type = numberField(state_, -1, "aromatic", 0) != 0 ? core::BondType::Aromatic :
                    order > 2.5 ? core::BondType::Triple : order > 1.5 ? core::BondType::Double : core::BondType::Single;
        if(bond.type==core::BondType::Aromatic){const double display=numberField(state_,-1,"display_order",1);bond.displayType=display>1.5?core::BondType::Double:core::BondType::Single;}
        bond.stereo = core::bondStereoFromString(stringField(state_, -1, "stereo", "none"));
        bond.visible = numberField(state_, -1, "visible", 1) != 0;
        if (bond.id.empty() || bond.atomA.empty() || bond.atomB.empty()) {
            lua_pop(state_, 2);
            throw std::runtime_error("chem.NewMol: bond ID and atom references cannot be empty");
        }
        molecule->bonds.push_back(std::move(bond));
        lua_pop(state_, 1);
    }
    lua_pop(state_, 1);

    molecule->validateIds();
    object.molecule = std::move(molecule);
}

void LuaRuntime::bindObjectMethods(int tableIndex, Object& object) {
    tableIndex = lua_absindex(state_, tableIndex);
    const auto bind = [&](const char* name, lua_CFunction function) {
        pushBoundClosure(state_, this, object.id, function);
        lua_setfield(state_, tableIndex, name);
    };
    bind("SetPos", mSetPos); bind("SetPosX", mSetPosX); bind("SetPosY", mSetPosY);
    bind("SetAlpha", mSetAlpha); bind("SetColor", mSetColor);
    bind("SetLayer", mSetLayer); bind("SetVisible", mSetVisible); bind("SetAnchor", mSetAnchor);
    bind("Delete", mDelete);
    bind("LerpPos", mLerpPos); bind("LerpPosX", mLerpPosX); bind("LerpPosY", mLerpPosY);
    bind("LerpAlpha", mLerpAlpha); bind("LerpColor", mLerpColor);
    if (object.kind == "sprite" || object.kind == "molecule") {
        bind("SetScale", mSetScale); bind("SetScaleX", mSetScaleX); bind("SetScaleY", mSetScaleY);
        bind("SetRotation", mSetRotation); bind("SetRot", mSetRotation);
        bind("LerpScale", mLerpScale); bind("LerpScaleX", mLerpScaleX); bind("LerpScaleY", mLerpScaleY);
        bind("LerpRotation", mLerpRotation); bind("LerpRot", mLerpRotation);
    }
    if (object.kind == "sprite") {
        bind("SetImage", mSetImage); bind("ChangeImage", mChangeImage);
    } else if (object.kind == "molecule") {
        bind("SetAtomXY", mSetAtomXY); bind("LerpAtomXY", mLerpAtomXY);
        bind("LerpAtomsXY", mLerpAtomsXY);
        bind("SetAtomElement",mSetAtomElement);bind("SetAtomCharge",mSetAtomCharge);bind("SetAtomHidden",mSetAtomHidden);
        bind("FormBond",mFormBond);bind("DeleteBond",mDeleteBond);bind("SetBondOrder",mSetBondOrder);
        bind("SetBondStereo",mSetBondStereo);bind("SetBondVisible",mSetBondVisible);
    } else if (object.kind == "arrow") {
        bind("SetProgress", mSetProgress); bind("LerpProgress", mLerpProgress);
        bind("SetCurve", mSetCurve);
        bind("SetWidth", mSetWidth);
    }
}

Object* LuaRuntime::resolveObject(int index, int& nextArgument) {
    if (lua_istable(state_, index) && engine_->objectFromTable(index)) {
        nextArgument = index + 1;
        return engine_->objectFromTable(index);
    }
    nextArgument = index;
    return engine_->objectById(currentObjectId_);
}

void LuaRuntime::installApi() {
    luaL_newmetatable(state_, kObjectMetatable);
    lua_newtable(state_);
    const int methods = lua_gettop(state_);
    for (const auto& [name, fn] : std::initializer_list<std::pair<const char*, lua_CFunction>>{
             {"set", lSet}, {"to", lTo}, {"texture", lTexture}, {"remove", lRemove}, {"select", lSelect}}) {
        pushClosure(state_, this, fn); lua_setfield(state_, methods, name);
    }
    lua_setfield(state_, -2, "__index");
    lua_pop(state_, 1);

    lua_newtable(state_);
    const int api = lua_gettop(state_);
    for (const auto& [name, fn] : std::initializer_list<std::pair<const char*, lua_CFunction>>{
             {"scene", lScene}, {"load_texture", lLoadTexture},
             {"NewMol", lNewMol}, {"NewArrow", lNewArrow},
             {"Wait", lWait}, {"SetFrame", lAt}, {"GetFrame", lFrame}, {"Select", lSelect}, {"Current", lCurrent},
             {"set", lSet}, {"to", lTo}, {"texture", lTexture},
             {"select", lSelect}, {"current", lCurrent}, {"remove", lRemove},
             {"at", lAt}, {"wait", lWait}, {"frame", lFrame}, {"on_frame", lOnFrame}}) {
        pushClosure(state_, this, fn); lua_setfield(state_, api, name);
    }
    lua_pushvalue(state_, api); lua_setglobal(state_, "chem");
    lua_getglobal(state_, "package"); lua_getfield(state_, -1, "loaded");
    lua_pushvalue(state_, api); lua_setfield(state_, -2, "chem"); lua_pop(state_, 2);
    lua_pop(state_, 1);

    constexpr const char* conveniences = R"LUA(
function chem.fade_in(obj, frames, ease) return chem.to(obj, frames, { alpha = 1 }, ease or "linear") end
function chem.fade_out(obj, frames, ease) return chem.to(obj, frames, { alpha = 0 }, ease or "linear") end
function chem.wipe_in(obj, frames, direction, ease)
    chem.set(obj, { reveal = 0, reveal_dir = direction or "ltr" })
    return chem.to(obj, frames, { reveal = 1 }, ease or "linear")
end
function chem.move_to(obj, frames, x, y, ease) return chem.to(obj, frames, { x = x, y = y }, ease or "linear") end
)LUA";
    if (luaL_dostring(state_, conveniences) != LUA_OK) {
        throw std::runtime_error(lua_tostring(state_, -1));
    }
}

int LuaRuntime::lScene(lua_State* state) {
    auto& runtime = self(state);
    luaL_checktype(state, 1, LUA_TTABLE);
    runtime.engine_->scene.width = static_cast<int>(numberField(state, 1, "width", runtime.engine_->scene.width));
    runtime.engine_->scene.height = static_cast<int>(numberField(state, 1, "height", runtime.engine_->scene.height));
    runtime.engine_->scene.logicWidth = static_cast<int>(numberField(state, 1, "logic_width", runtime.engine_->scene.width));
    runtime.engine_->scene.logicHeight = static_cast<int>(numberField(state, 1, "logic_height", runtime.engine_->scene.height));
    runtime.engine_->scene.fps = static_cast<int>(numberField(state, 1, "fps", runtime.engine_->scene.fps));
    runtime.engine_->scene.viewZoom = numberField(state, 1, "view_zoom", runtime.engine_->scene.viewZoom);
    runtime.engine_->scene.endFrame = static_cast<int>(numberField(state, 1, "end_frame", runtime.engine_->scene.endFrame));
    runtime.engine_->scene.title = stringField(state, 1, "title", runtime.engine_->scene.title);
    lua_getfield(state, 1, "background");
    if (!lua_isnil(state, -1)) runtime.engine_->scene.background = parseColor(state, -1, runtime.engine_->scene.background);
    lua_pop(state, 1);
    if (runtime.engine_->scene.width <= 0 || runtime.engine_->scene.height <= 0 ||
        runtime.engine_->scene.logicWidth <= 0 || runtime.engine_->scene.logicHeight <= 0 ||
        runtime.engine_->scene.fps <= 0 || runtime.engine_->scene.viewZoom <= 0) {
        return luaL_error(state, "scene width, height, logic_width, logic_height and fps must be positive");
    }
    return 0;
}

int LuaRuntime::lLoadTexture(lua_State* state) {
    auto& runtime = self(state);
    const double anchorX = lua_isnumber(state, 3) ? lua_tonumber(state, 3) : 0.5;
    const double anchorY = lua_isnumber(state, 4) ? lua_tonumber(state, 4) : 0.5;
    runtime.engine_->registerTexture(luaL_checkstring(state, 1), luaL_checkstring(state, 2), anchorX, anchorY);
    return 0;
}

int LuaRuntime::lNewMol(lua_State* state) {
    auto& runtime = self(state);
    // During the first native-2D slice an empty call remains capable of opening
    // old PNG examples. New v2 projects always pass embedded atom/bond data.
    if (!lua_istable(state, 1)) {
        runtime.createObjectTable("sprite", 0);
        return 1;
    }
    lua_getfield(state, 1, "atoms");
    const bool native = lua_istable(state, -1);
    lua_pop(state, 1);
    Object& object = runtime.createObjectTable(native ? "molecule" : "sprite", 1);
    if (native) {
        try {
            runtime.readMolecule(object, -1);
        } catch (const std::exception& error) {
            return luaL_error(state, "%s", error.what());
        }
    }
    return 1;
}

int LuaRuntime::lNewArrow(lua_State* state) {
    self(state).createObjectTable("arrow", lua_istable(state, 1) ? 1 : 0);
    return 1;
}

int LuaRuntime::lSprite(lua_State* state) {
    auto& runtime = self(state);
    const char* texture = luaL_checkstring(state, 1);
    runtime.createObjectTable("sprite", lua_istable(state, 2) ? 2 : 0);
    lua_pushstring(state, texture); lua_setfield(state, -2, "texture");
    return 1;
}

int LuaRuntime::lArrow(lua_State* state) {
    self(state).createObjectTable("arrow", lua_istable(state, 1) ? 1 : 0);
    return 1;
}

int LuaRuntime::lSet(lua_State* state) {
    auto& runtime = self(state);
    int properties = 1;
    Object* object = runtime.resolveObject(1, properties);
    if (!object) return luaL_error(state, "chem.set: no current object");
    luaL_checktype(state, properties, LUA_TTABLE);
    const int table = lua_absindex(state, properties);
    lua_pushnil(state);
    while (lua_next(state, table) != 0) {
        if (lua_type(state, -2) == LUA_TSTRING) {
            const std::string key = lua_tostring(state, -2);
            if (lua_isnumber(state, -1)) runtime.engine_->addNumericTween(*object, key, runtime.cursor_, 0, lua_tonumber(state, -1), Ease::Step);
            else if (lua_isboolean(state, -1)) runtime.engine_->addNumericTween(*object, key, runtime.cursor_, 0, lua_toboolean(state, -1), Ease::Step);
            else if (lua_isstring(state, -1)) runtime.engine_->addStringKey(*object, key, runtime.cursor_, lua_tostring(state, -1));
        }
        lua_pop(state, 1);
    }
    lua_settop(state, 0);
    lua_rawgeti(state, LUA_REGISTRYINDEX, object->luaRef);
    return 1;
}

int LuaRuntime::lTo(lua_State* state) {
    auto& runtime = self(state);
    int durationIndex = 1;
    Object* object = runtime.resolveObject(1, durationIndex);
    if (!object) return luaL_error(state, "chem.to: no current object");
    const int duration = static_cast<int>(luaL_checkinteger(state, durationIndex));
    const int properties = durationIndex + 1;
    luaL_checktype(state, properties, LUA_TTABLE);
    const std::string easeName = lua_isstring(state, properties + 1) ? lua_tostring(state, properties + 1) : "linear";
    const Ease ease = Engine::parseEase(easeName);
    const int table = lua_absindex(state, properties);
    lua_pushnil(state);
    while (lua_next(state, table) != 0) {
        if (lua_type(state, -2) == LUA_TSTRING && lua_isnumber(state, -1)) {
            runtime.engine_->addNumericTween(*object, lua_tostring(state, -2), runtime.cursor_, duration, lua_tonumber(state, -1), ease);
        }
        lua_pop(state, 1);
    }
    runtime.cursor_ += std::max(0, duration);
    lua_settop(state, 0);
    lua_rawgeti(state, LUA_REGISTRYINDEX, object->luaRef);
    return 1;
}

int LuaRuntime::lTexture(lua_State* state) {
    auto& runtime = self(state);
    int nameIndex = 1;
    Object* object = runtime.resolveObject(1, nameIndex);
    if (!object) return luaL_error(state, "chem.texture: no current object");
    runtime.engine_->addStringKey(*object, "texture", runtime.cursor_, luaL_checkstring(state, nameIndex));
    lua_settop(state, 0); lua_rawgeti(state, LUA_REGISTRYINDEX, object->luaRef); return 1;
}

int LuaRuntime::lSelect(lua_State* state) {
    auto& runtime = self(state);
    Object* object = runtime.engine_->objectFromTable(1);
    if (!object) return luaL_error(state, "chem.select expects a Chemanim object table");
    runtime.currentObjectId_ = object->id;
    lua_settop(state, 1); return 1;
}

int LuaRuntime::lCurrent(lua_State* state) {
    auto& runtime = self(state);
    Object* object = runtime.engine_->objectById(runtime.currentObjectId_);
    if (!object) { lua_pushnil(state); return 1; }
    lua_rawgeti(state, LUA_REGISTRYINDEX, object->luaRef); return 1;
}

int LuaRuntime::lRemove(lua_State* state) {
    auto& runtime = self(state);
    int unused = 1;
    Object* object = runtime.resolveObject(1, unused);
    if (!object) return luaL_error(state, "chem.remove: no current object");
    runtime.engine_->scheduleRemove(*object, runtime.cursor_);
    return 0;
}

int LuaRuntime::lAt(lua_State* state) {
    auto& runtime = self(state);
    runtime.cursor_ = std::max(0, static_cast<int>(luaL_checkinteger(state, 1)));
    lua_pushinteger(state, runtime.cursor_); return 1;
}

int LuaRuntime::lWait(lua_State* state) {
    auto& runtime = self(state);
    runtime.cursor_ += std::max(0, static_cast<int>(luaL_checkinteger(state, 1)));
    lua_pushinteger(state, runtime.cursor_); return 1;
}

int LuaRuntime::lFrame(lua_State* state) {
    lua_pushinteger(state, self(state).cursor_); return 1;
}

int LuaRuntime::lOnFrame(lua_State* state) {
    auto& runtime = self(state);
    luaL_checktype(state, 1, LUA_TFUNCTION);
    lua_pushvalue(state, 1);
    runtime.engine_->addFrameCallback(luaL_ref(state, LUA_REGISTRYINDEX));
    return 0;
}

LuaRuntime& LuaRuntime::boundRuntime(lua_State* state) {
    return *static_cast<LuaRuntime*>(lua_touserdata(state, lua_upvalueindex(1)));
}

Object& LuaRuntime::boundObject(lua_State* state) {
    auto& runtime = boundRuntime(state);
    const int id = static_cast<int>(lua_tointeger(state, lua_upvalueindex(2)));
    Object* object = runtime.engine_->objectById(id);
    if (!object) luaL_error(state, "object no longer exists");
    return *object;
}

int LuaRuntime::returnBoundObject(lua_State* state, Object& object) {
    lua_settop(state, 0);
    lua_rawgeti(state, LUA_REGISTRYINDEX, object.luaRef);
    return 1;
}

Ease LuaRuntime::boundEase(lua_State* state, int modeIndex) {
    if(lua_isstring(state,modeIndex)) return Engine::parseEase(lua_tostring(state,modeIndex));
    const int mode = lua_isnumber(state, modeIndex) ? static_cast<int>(lua_tointeger(state, modeIndex)) : 0;
    switch (mode) {
        case 1: return Ease::InQuad;
        case 2: return Ease::InCubic;
        case 3: return Ease::OutQuad;
        case 4: return Ease::OutCubic;
        case 5: return Ease::InOutQuad;
        case 6: return Ease::InOutCubic;
        default: return Ease::Linear;
    }
}

namespace {
int methodBase(lua_State* state) { return lua_istable(state, 1) ? 2 : 1; }
int durationValue(lua_State* state, int index) {
    return std::max(0, static_cast<int>(luaL_checkinteger(state, index)));
}
double alphaValue(lua_State* state, int index) {
    return std::clamp(luaL_checknumber(state, index), 0.0, 255.0) / 255.0;
}
} // namespace

int LuaRuntime::mSetPos(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "x", runtime.cursor_, 0, luaL_checknumber(state, a), Ease::Step);
    runtime.engine_->addNumericTween(object, "y", runtime.cursor_, 0, luaL_checknumber(state, a + 1), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetPosX(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "x", runtime.cursor_, 0, luaL_checknumber(state, a), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetPosY(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "y", runtime.cursor_, 0, luaL_checknumber(state, a), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetImage(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addStringKey(object, "texture", runtime.cursor_, luaL_checkstring(state, a));
    return returnBoundObject(state, object);
}

int LuaRuntime::mChangeImage(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    if (object.kind != "sprite") return luaL_error(state, "ChangeImage is only available on texture objects");
    const int argumentCount = lua_gettop(state) - a + 1;
    if (argumentCount >= 5) {
        runtime.engine_->addImageTransition(
            object, runtime.cursor_, durationValue(state, a + 3),
            luaL_checkstring(state, a), boundEase(state, a + 4),
            luaL_checknumber(state, a + 1), luaL_checknumber(state, a + 2));
    } else {
        // Old scripts remain valid: without an explicit target coordinate the
        // incoming image uses the object's position at transition start.
        runtime.engine_->addImageTransition(
            object, runtime.cursor_, durationValue(state, a + 1),
            luaL_checkstring(state, a), boundEase(state, a + 2));
    }
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetAlpha(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "alpha", runtime.cursor_, 0, alphaValue(state, a), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetScale(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    const double x = luaL_checknumber(state, a);
    const double y = lua_isnumber(state, a + 1) ? lua_tonumber(state, a + 1) : x;
    runtime.engine_->addNumericTween(object, "scale_x", runtime.cursor_, 0, x, Ease::Step);
    runtime.engine_->addNumericTween(object, "scale_y", runtime.cursor_, 0, y, Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetScaleX(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "scale_x", runtime.cursor_, 0, luaL_checknumber(state, a), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetScaleY(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "scale_y", runtime.cursor_, 0, luaL_checknumber(state, a), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetRotation(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "rotation", runtime.cursor_, 0, luaL_checknumber(state, a), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetLayer(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "layer", runtime.cursor_, 0, luaL_checknumber(state, a), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetVisible(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    const double value = lua_toboolean(state, a) ? 1.0 : 0.0;
    runtime.engine_->addNumericTween(object, "visible", runtime.cursor_, 0, value, Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetAnchor(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "anchor_x", runtime.cursor_, 0, std::clamp(luaL_checknumber(state, a), 0.0, 1.0), Ease::Step);
    runtime.engine_->addNumericTween(object, "anchor_y", runtime.cursor_, 0, std::clamp(luaL_checknumber(state, a + 1), 0.0, 1.0), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mDelete(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state);
    runtime.engine_->scheduleRemove(object, runtime.cursor_);
    return 0;
}

int LuaRuntime::mLerpPos(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    const int duration = durationValue(state, a + 2); const Ease ease = boundEase(state, a + 3);
    runtime.engine_->addNumericTween(object, "x", runtime.cursor_, duration, luaL_checknumber(state, a), ease);
    runtime.engine_->addNumericTween(object, "y", runtime.cursor_, duration, luaL_checknumber(state, a + 1), ease);
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpPosX(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "x", runtime.cursor_, durationValue(state, a + 1), luaL_checknumber(state, a), boundEase(state, a + 2));
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpPosY(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "y", runtime.cursor_, durationValue(state, a + 1), luaL_checknumber(state, a), boundEase(state, a + 2));
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpAlpha(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "alpha", runtime.cursor_, durationValue(state, a + 1), alphaValue(state, a), boundEase(state, a + 2));
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpScale(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    const int argumentCount = lua_gettop(state) - a + 1;
    const double x = luaL_checknumber(state, a);
    const bool separateAxes = argumentCount >= 4;
    const double y = separateAxes ? luaL_checknumber(state, a + 1) : x;
    const int durationIndex = separateAxes ? a + 2 : a + 1;
    const int duration = durationValue(state, durationIndex);
    const Ease ease = boundEase(state, durationIndex + 1);
    runtime.engine_->addNumericTween(object, "scale_x", runtime.cursor_, duration, x, ease);
    runtime.engine_->addNumericTween(object, "scale_y", runtime.cursor_, duration, y, ease);
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpScaleX(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "scale_x", runtime.cursor_, durationValue(state, a + 1), luaL_checknumber(state, a), boundEase(state, a + 2));
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpScaleY(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "scale_y", runtime.cursor_, durationValue(state, a + 1), luaL_checknumber(state, a), boundEase(state, a + 2));
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpRotation(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "rotation", runtime.cursor_, durationValue(state, a + 1), luaL_checknumber(state, a), boundEase(state, a + 2));
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetProgress(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "progress", runtime.cursor_, 0, std::clamp(luaL_checknumber(state, a), 0.0, 1.0), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpProgress(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "progress", runtime.cursor_, durationValue(state, a + 1),
                                     std::clamp(luaL_checknumber(state, a), 0.0, 1.0), boundEase(state, a + 2));
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetCurve(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    static constexpr const char* keys[] = {"x1", "y1", "cx1", "cy1", "cx2", "cy2", "x2", "y2"};
    for (int i = 0; i < 8; ++i) runtime.engine_->addNumericTween(object, keys[i], runtime.cursor_, 0, luaL_checknumber(state, a + i), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetColor(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "r", runtime.cursor_, 0, std::clamp(luaL_checknumber(state, a), 0.0, 255.0), Ease::Step);
    runtime.engine_->addNumericTween(object, "g", runtime.cursor_, 0, std::clamp(luaL_checknumber(state, a + 1), 0.0, 255.0), Ease::Step);
    runtime.engine_->addNumericTween(object, "b", runtime.cursor_, 0, std::clamp(luaL_checknumber(state, a + 2), 0.0, 255.0), Ease::Step);
    if (lua_isnumber(state, a + 3)) runtime.engine_->addNumericTween(object, "alpha", runtime.cursor_, 0, alphaValue(state, a + 3), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpColor(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    const int duration = durationValue(state, a + 3);
    const Ease ease = boundEase(state, a + 4);
    runtime.engine_->addNumericTween(object, "r", runtime.cursor_, duration,
        std::clamp(luaL_checknumber(state, a), 0.0, 255.0), ease);
    runtime.engine_->addNumericTween(object, "g", runtime.cursor_, duration,
        std::clamp(luaL_checknumber(state, a + 1), 0.0, 255.0), ease);
    runtime.engine_->addNumericTween(object, "b", runtime.cursor_, duration,
        std::clamp(luaL_checknumber(state, a + 2), 0.0, 255.0), ease);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetWidth(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addNumericTween(object, "thickness", runtime.cursor_, 0, luaL_checknumber(state, a), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetAtomXY(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addAtomTween(object, luaL_checkstring(state, a), runtime.cursor_, 0,
                                  luaL_checknumber(state, a + 1), luaL_checknumber(state, a + 2), Ease::Step);
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpAtomXY(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    runtime.engine_->addAtomTween(object, luaL_checkstring(state, a), runtime.cursor_, durationValue(state, a + 3),
                                  luaL_checknumber(state, a + 1), luaL_checknumber(state, a + 2), boundEase(state, a + 4));
    return returnBoundObject(state, object);
}

int LuaRuntime::mLerpAtomsXY(lua_State* state) {
    auto& runtime = boundRuntime(state); auto& object = boundObject(state); const int a = methodBase(state);
    luaL_checktype(state, a, LUA_TTABLE);
    const int duration = durationValue(state, a + 1); const Ease ease = boundEase(state, a + 2);
    lua_pushnil(state);
    while (lua_next(state, a) != 0) {
        const char* atomId = luaL_checkstring(state, -2); luaL_checktype(state, -1, LUA_TTABLE);
        lua_rawgeti(state, -1, 1); const double x = luaL_checknumber(state, -1); lua_pop(state, 1);
        lua_rawgeti(state, -1, 2); const double y = luaL_checknumber(state, -1); lua_pop(state, 1);
        runtime.engine_->addAtomTween(object, atomId, runtime.cursor_, duration, x, y, ease);
        lua_pop(state, 1);
    }
    return returnBoundObject(state, object);
}

int LuaRuntime::mSetAtomElement(lua_State* state) {
    auto& runtime=boundRuntime(state);auto& object=boundObject(state);const int a=methodBase(state);
    if(!object.molecule)return luaL_error(state,"SetAtomElement requires a molecule");const std::string id=luaL_checkstring(state,a);
    if(!object.molecule->atom(id))return luaL_error(state,"Unknown atom ID");runtime.engine_->addStringKey(object,"atom:"+id+":element",runtime.cursor_,luaL_checkstring(state,a+1));return returnBoundObject(state,object);
}
int LuaRuntime::mSetAtomCharge(lua_State* state) {
    auto& runtime=boundRuntime(state);auto& object=boundObject(state);const int a=methodBase(state);
    if(!object.molecule)return luaL_error(state,"SetAtomCharge requires a molecule");const std::string id=luaL_checkstring(state,a);
    if(!object.molecule->atom(id))return luaL_error(state,"Unknown atom ID");runtime.engine_->addNumericTween(object,"atom:"+id+":charge",runtime.cursor_,0,luaL_checknumber(state,a+1),Ease::Step);return returnBoundObject(state,object);
}
int LuaRuntime::mSetAtomHidden(lua_State* state) {
    auto& runtime=boundRuntime(state);auto& object=boundObject(state);const int a=methodBase(state);
    if(!object.molecule)return luaL_error(state,"SetAtomHidden requires a molecule");const std::string id=luaL_checkstring(state,a);
    if(!object.molecule->atom(id))return luaL_error(state,"Unknown atom ID");runtime.engine_->addNumericTween(object,"atom:"+id+":hidden",runtime.cursor_,0,lua_toboolean(state,a+1)?1:0,Ease::Step);return returnBoundObject(state,object);
}
int LuaRuntime::mFormBond(lua_State* state) {
    auto& runtime=boundRuntime(state);auto& object=boundObject(state);const int a=methodBase(state);
    if(!object.molecule)return luaL_error(state,"FormBond requires a molecule");const std::string id=luaL_checkstring(state,a),first=luaL_checkstring(state,a+1),second=luaL_checkstring(state,a+2);
    if(!object.molecule->atom(first)||!object.molecule->atom(second))return luaL_error(state,"Unknown bond atom ID");
    if(!object.molecule->bond(id)){object.molecule->bonds.push_back(core::Bond{.id=id,.atomA=first,.atomB=second,.visible=false});}
    runtime.engine_->addStringKey(object,"bond:"+id+":type",runtime.cursor_,luaL_checkstring(state,a+3));runtime.engine_->addStringKey(object,"bond:"+id+":stereo",runtime.cursor_,luaL_checkstring(state,a+4));runtime.engine_->addNumericTween(object,"bond:"+id+":visible",runtime.cursor_,0,1,Ease::Step);return returnBoundObject(state,object);
}
int LuaRuntime::mDeleteBond(lua_State* state) {auto& runtime=boundRuntime(state);auto& object=boundObject(state);const int a=methodBase(state);const std::string id=luaL_checkstring(state,a);runtime.engine_->addNumericTween(object,"bond:"+id+":visible",runtime.cursor_,0,0,Ease::Step);return returnBoundObject(state,object);}
int LuaRuntime::mSetBondOrder(lua_State* state) {auto& runtime=boundRuntime(state);auto& object=boundObject(state);const int a=methodBase(state);const std::string id=luaL_checkstring(state,a);runtime.engine_->addStringKey(object,"bond:"+id+":type",runtime.cursor_,luaL_checkstring(state,a+1));return returnBoundObject(state,object);}
int LuaRuntime::mSetBondStereo(lua_State* state) {auto& runtime=boundRuntime(state);auto& object=boundObject(state);const int a=methodBase(state);const std::string id=luaL_checkstring(state,a);runtime.engine_->addStringKey(object,"bond:"+id+":stereo",runtime.cursor_,luaL_checkstring(state,a+1));return returnBoundObject(state,object);}
int LuaRuntime::mSetBondVisible(lua_State* state) {auto& runtime=boundRuntime(state);auto& object=boundObject(state);const int a=methodBase(state);const std::string id=luaL_checkstring(state,a);runtime.engine_->addNumericTween(object,"bond:"+id+":visible",runtime.cursor_,0,lua_toboolean(state,a+1)?1:0,Ease::Step);return returnBoundObject(state,object);}

} // namespace chem
