cmake_minimum_required(VERSION 3.24)
project(Chemanim VERSION 0.1.0 LANGUAGES C CXX)

find_package(Git QUIET)
set(CHEMANIM_BUILD_COMMIT "unknown")
if(Git_FOUND)
    execute_process(COMMAND "${GIT_EXECUTABLE}" rev-parse HEAD
        WORKING_DIRECTORY "${CMAKE_SOURCE_DIR}"
        OUTPUT_VARIABLE CHEMANIM_BUILD_COMMIT OUTPUT_STRIP_TRAILING_WHITESPACE
        ERROR_QUIET)
endif()

if(POLICY CMP0169)
    cmake_policy(SET CMP0169 OLD)
endif()
if(POLICY CMP0167)
    cmake_policy(SET CMP0167 OLD)
endif()

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(FetchContent)

set(CHEMANIM_RDKIT_ROOT "${CMAKE_SOURCE_DIR}/.deps/rdkit" CACHE PATH "Conda prefix containing librdkit-dev")
if(NOT EXISTS "${CHEMANIM_RDKIT_ROOT}/Library/lib/cmake/rdkit/rdkit-config.cmake")
    message(FATAL_ERROR "RDKit C++ development files are missing. Run tools/bootstrap_native_deps.ps1 first.")
endif()
list(PREPEND CMAKE_PREFIX_PATH "${CHEMANIM_RDKIT_ROOT}/Library")
set(BOOST_ROOT "${CHEMANIM_RDKIT_ROOT}/Library")
set(Boost_ROOT "${CHEMANIM_RDKIT_ROOT}/Library")
foreach(_boost_component serialization iostreams random regex)
    if(EXISTS "${CHEMANIM_RDKIT_ROOT}/Library/bin/boost_${_boost_component}.dll" AND
       NOT EXISTS "${CHEMANIM_RDKIT_ROOT}/Library/lib/boost_${_boost_component}.dll")
        file(COPY_FILE
            "${CHEMANIM_RDKIT_ROOT}/Library/bin/boost_${_boost_component}.dll"
            "${CHEMANIM_RDKIT_ROOT}/Library/lib/boost_${_boost_component}.dll"
            ONLY_IF_DIFFERENT)
    endif()
endforeach()
if(NOT TARGET Cairo::Cairo)
    add_library(Cairo::Cairo SHARED IMPORTED)
    set_target_properties(Cairo::Cairo PROPERTIES
        IMPORTED_IMPLIB "${CHEMANIM_RDKIT_ROOT}/Library/lib/cairo.lib"
        IMPORTED_LOCATION "${CHEMANIM_RDKIT_ROOT}/Library/bin/cairo.dll"
        INTERFACE_INCLUDE_DIRECTORIES "${CHEMANIM_RDKIT_ROOT}/Library/include/cairo"
    )
endif()
find_package(RDKit CONFIG REQUIRED)

FetchContent_Declare(
    nlohmann_json
    URL https://codeload.github.com/nlohmann/json/tar.gz/refs/tags/v3.12.0
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(nlohmann_json)

FetchContent_Declare(
    pybind11
    URL https://codeload.github.com/pybind/pybind11/tar.gz/refs/tags/v3.0.1
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
set(PYBIND11_FINDPYTHON ON)
FetchContent_MakeAvailable(pybind11)

set(BUILD_EXAMPLES OFF CACHE BOOL "" FORCE)
set(BUILD_GAMES OFF CACHE BOOL "" FORCE)
FetchContent_Declare(
    raylib
    URL https://codeload.github.com/raysan5/raylib/tar.gz/refs/tags/5.5
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_MakeAvailable(raylib)

FetchContent_Declare(
    nanosvg
    URL https://codeload.github.com/memononen/nanosvg/tar.gz/refs/heads/master
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
)
FetchContent_GetProperties(nanosvg)
if(NOT nanosvg_POPULATED)
    FetchContent_Populate(nanosvg)
endif()

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

add_library(chemanim_core_lib STATIC
    src/core/Document.cpp
    src/core/Nodes.cpp
    src/core/Editing.cpp
    src/core/SketcherGeometry.cpp
    src/core/Depiction.cpp
    src/core/SvgRaster.cpp
    src/core/Timeline.cpp
    src/core/Codegen.cpp
)
set_target_properties(chemanim_core_lib PROPERTIES POSITION_INDEPENDENT_CODE ON)
target_include_directories(chemanim_core_lib PUBLIC src PRIVATE ${nanosvg_SOURCE_DIR}/src)
target_link_libraries(chemanim_core_lib
    PUBLIC RDKit::GraphMol RDKit::SmilesParse RDKit::Depictor RDKit::MolDraw2D
    PRIVATE nlohmann_json::nlohmann_json
)

pybind11_add_module(chemanim_core MODULE WITHOUT_SOABI src/core/Bindings.cpp)
target_link_libraries(chemanim_core PRIVATE chemanim_core_lib nlohmann_json::nlohmann_json)
target_compile_definitions(chemanim_core PRIVATE CHEMANIM_BUILD_COMMIT="${CHEMANIM_BUILD_COMMIT}")
set(CHEMANIM_PYTHON_OUTPUT_DIRECTORY "${CMAKE_SOURCE_DIR}/tools" CACHE PATH
    "Output directory for the chemanim_core Python module")
set_target_properties(chemanim_core PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY "${CHEMANIM_PYTHON_OUTPUT_DIRECTORY}"
    RUNTIME_OUTPUT_DIRECTORY "${CHEMANIM_PYTHON_OUTPUT_DIRECTORY}"
)

add_executable(chemanim
    src/main.cpp
    src/Engine.cpp
    src/LuaRuntime.cpp
    src/Renderer.cpp
    src/VideoEncoder.cpp
    src/SvgRasterizer.cpp
)
target_include_directories(chemanim PRIVATE src ${nanosvg_SOURCE_DIR}/src)
target_link_libraries(chemanim PRIVATE raylib lua chemanim_core_lib)
if(WIN32)
    target_link_libraries(chemanim PRIVATE mfplat mfreadwrite mfuuid ole32 shell32)
endif()

if(WIN32)
    add_custom_command(TARGET chemanim POST_BUILD
        COMMAND ${CMAKE_COMMAND} -E copy_if_different $<TARGET_RUNTIME_DLLS:chemanim> $<TARGET_FILE_DIR:chemanim>
        COMMAND ${CMAKE_COMMAND}
            -DCHEMANIM_EXECUTABLE=$<TARGET_FILE:chemanim>
            -DCHEMANIM_DEPENDENCY_DIRECTORY=${CHEMANIM_RDKIT_ROOT}/Library/bin
            -P ${CMAKE_SOURCE_DIR}/cmake/CopyRuntimeDependencies.cmake
        COMMAND_EXPAND_LISTS)
endif()

if(MSVC)
    target_compile_options(chemanim PRIVATE /W4 /permissive- /utf-8)
    target_compile_options(chemanim_core_lib PRIVATE /W4 /permissive- /utf-8)
    target_compile_options(chemanim_core PRIVATE /W4 /permissive- /utf-8)
else()
    target_compile_options(chemanim PRIVATE -Wall -Wextra -Wpedantic)
endif()

set_property(DIRECTORY PROPERTY VS_STARTUP_PROJECT chemanim)
