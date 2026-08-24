cmake_minimum_required(VERSION 3.24)
project(Chemanim VERSION 0.1.0 LANGUAGES C CXX)

if(POLICY CMP0169)
    cmake_policy(SET CMP0169 OLD)
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)

set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(BUILD_GAMES OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    raylib
    URL https://codeload.github.com/raysan5/raylib/tar.gz/refs/tags/5.5
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(raylib)

FetchContent_Declare(
    lua_source
    URL https://www.lua.org/ftp/lua-5.4.7.tar.gz
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_GetProperties(lua_source)
if(NOT lua_source_POPULATED)
    FetchContent_Populate(lua_source)
endif()

set(LUA_DIR "${lua_source_SOURCE_DIR}/src")
add_library(lua STATIC
    ${LUA_DIR}/lapi.c ${LUA_DIR}/lauxlib.c ${LUA_DIR}/lbaselib.c
    ${LUA_DIR}/lcode.c ${LUA_DIR}/lcorolib.c ${LUA_DIR}/lctype.c
    ${LUA_DIR}/ldblib.c ${LUA_DIR}/ldebug.c ${LUA_DIR}/ldo.c
    ${LUA_DIR}/ldump.c ${LUA_DIR}/lfunc.c ${LUA_DIR}/lgc.c
    ${LUA_DIR}/linit.c ${LUA_DIR}/liolib.c ${LUA_DIR}/llex.c
    ${LUA_DIR}/lmathlib.c ${LUA_DIR}/lmem.c ${LUA_DIR}/loadlib.c
    ${LUA_DIR}/lobject.c ${LUA_DIR}/lopcodes.c ${LUA_DIR}/loslib.c
    ${LUA_DIR}/lparser.c ${LUA_DIR}/lstate.c ${LUA_DIR}/lstring.c
    ${LUA_DIR}/lstrlib.c ${LUA_DIR}/ltable.c ${LUA_DIR}/ltablib.c
    ${LUA_DIR}/ltm.c ${LUA_DIR}/lundump.c ${LUA_DIR}/lutf8lib.c
    ${LUA_DIR}/lvm.c ${LUA_DIR}/lzio.c
)
target_include_directories(lua PUBLIC ${LUA_DIR})

add_executable(chemanim
    src/main.cpp
    src/Engine.cpp
    src/LuaRuntime.cpp
    src/Renderer.cpp
    src/VideoEncoder.cpp
)
target_include_directories(chemanim PRIVATE src)
target_link_libraries(chemanim PRIVATE raylib lua)
if(WIN32)
    target_link_libraries(chemanim PRIVATE mfplat mfreadwrite mfuuid ole32 shell32)
endif()

if(MSVC)
    target_compile_options(chemanim PRIVATE /W4 /permissive- /utf-8)
else()
    target_compile_options(chemanim PRIVATE -Wall -Wextra -Wpedantic)
endif()

set_property(DIRECTORY PROPERTY VS_STARTUP_PROJECT chemanim)
