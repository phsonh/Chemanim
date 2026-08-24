#pragma once

#include "Engine.hpp"

#include <filesystem>
#include <memory>
#include <string>

struct lua_State;

namespace chem {

class LuaRuntime {
public:
    LuaRuntime();
    ~LuaRuntime();

    LuaRuntime(const LuaRuntime&) = delete;
    LuaRuntime& operator=(const LuaRuntime&) = delete;

    void runScript(const std::filesystem::path& scriptPath);
    [[nodiscard]] Engine& engine() { return *engine_; }
    [[nodiscard]] const Engine& engine() const { return *engine_; }

private:
    lua_State* state_ = nullptr;
    std::unique_ptr<Engine> engine_;
    int cursor_ = 0;
    int currentObjectId_ = 0;

    void installApi();
    Object& createObjectTable(const std::string& kind, int propertiesIndex);
    void readMolecule(Object& object, int tableIndex);
    void bindObjectMethods(int tableIndex, Object& object);
    void copyTable(int fromIndex, int toIndex);
    Object* resolveObject(int index, int& nextArgument);
    void setDefaultNumber(int tableIndex, const char* key, double value);
    void setDefaultString(int tableIndex, const char* key, const char* value);

    static LuaRuntime& self(lua_State* state);
    static int traceback(lua_State* state);
    static int lScene(lua_State* state);
    static int lLoadTexture(lua_State* state);
    static int lNewMol(lua_State* state);
    static int lNewArrow(lua_State* state);
    static int lSprite(lua_State* state);
    static int lArrow(lua_State* state);
    static int lSet(lua_State* state);
    static int lTo(lua_State* state);
    static int lTexture(lua_State* state);
    static int lSelect(lua_State* state);
    static int lCurrent(lua_State* state);
    static int lRemove(lua_State* state);
    static int lAt(lua_State* state);
    static int lWait(lua_State* state);
    static int lFrame(lua_State* state);
    static int lOnFrame(lua_State* state);

    static LuaRuntime& boundRuntime(lua_State* state);
    static Object& boundObject(lua_State* state);
    static int returnBoundObject(lua_State* state, Object& object);
    static Ease boundEase(lua_State* state, int modeIndex);
    static int mSetPos(lua_State* state);
    static int mSetPosX(lua_State* state);
    static int mSetPosY(lua_State* state);
    static int mSetImage(lua_State* state);
    static int mChangeImage(lua_State* state);
    static int mSetAlpha(lua_State* state);
    static int mSetScale(lua_State* state);
    static int mSetScaleX(lua_State* state);
    static int mSetScaleY(lua_State* state);
    static int mSetRotation(lua_State* state);
    static int mSetLayer(lua_State* state);
    static int mSetVisible(lua_State* state);
    static int mSetAnchor(lua_State* state);
    static int mDelete(lua_State* state);
    static int mLerpPos(lua_State* state);
    static int mLerpPosX(lua_State* state);
    static int mLerpPosY(lua_State* state);
    static int mLerpAlpha(lua_State* state);
    static int mLerpScale(lua_State* state);
    static int mLerpScaleX(lua_State* state);
    static int mLerpScaleY(lua_State* state);
    static int mLerpRotation(lua_State* state);
    static int mSetProgress(lua_State* state);
    static int mLerpProgress(lua_State* state);
    static int mSetCurve(lua_State* state);
    static int mSetColor(lua_State* state);
    static int mLerpColor(lua_State* state);
    static int mSetWidth(lua_State* state);
    static int mSetAtomXY(lua_State* state);
    static int mLerpAtomXY(lua_State* state);
    static int mLerpAtomsXY(lua_State* state);
    static int mSetAtomElement(lua_State* state);
    static int mSetAtomHidden(lua_State* state);
    static int mSetAtomAlpha(lua_State* state);
    static int mLerpAtomAlpha(lua_State* state);
    static int mSetAtomColor(lua_State* state);
    static int mLerpAtomColor(lua_State* state);
    static int mFormBond(lua_State* state);
    static int mDeleteBond(lua_State* state);
    static int mBreakBond(lua_State* state);
    static int mSetBondOrder(lua_State* state);
    static int mSetBondSecondarySide(lua_State* state);
    static int mSetBondStereo(lua_State* state);
    static int mSetBondVisible(lua_State* state);
    static int mSetBondAlpha(lua_State* state);
    static int mLerpBondAlpha(lua_State* state);
    static int mSetBondColor(lua_State* state);
    static int mLerpBondColor(lua_State* state);
    static int mSetAdornmentOffset(lua_State* state);
    static int mLerpAdornmentOffset(lua_State* state);
    static int mSetAdornmentAlpha(lua_State* state);
    static int mLerpAdornmentAlpha(lua_State* state);
    static int mSetAdornmentColor(lua_State* state);
    static int mLerpAdornmentColor(lua_State* state);
    static int mSetAdornmentText(lua_State* state);
    static int mDetachSubgraph(lua_State* state);
    static int mMergeFrom(lua_State* state);
};

} // namespace chem
