cmake_minimum_required(VERSION 3.24)
project(ChemanimSketcherProbe LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

if(NOT DEFINED SKETCHER_SOURCE OR NOT DEFINED SKETCHER_BUILD)
    message(FATAL_ERROR "Pass SKETCHER_SOURCE and SKETCHER_BUILD")
endif()

find_package(Python3 REQUIRED COMPONENTS Development.Module)
find_package(Qt6 REQUIRED COMPONENTS Widgets)
find_package(RDKit CONFIG REQUIRED)

add_library(schrodinger_sketcher SHARED IMPORTED)
set_target_properties(schrodinger_sketcher PROPERTIES
    IMPORTED_IMPLIB "${SKETCHER_BUILD}/schrodinger_sketcher.lib"
    IMPORTED_LOCATION "${SKETCHER_BUILD}/schrodinger_sketcher.dll")

Python3_add_library(sketcher_probe MODULE probe.cpp WITH_SOABI)
target_include_directories(sketcher_probe PRIVATE
    "${SKETCHER_SOURCE}/include"
    "${SKETCHER_SOURCE}/src"
    "${SKETCHER_BUILD}/include")
target_link_libraries(sketcher_probe PRIVATE
    schrodinger_sketcher Qt6::Widgets RDKit::GraphMol)
