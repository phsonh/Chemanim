cmake_policy(SET CMP0207 NEW)
if(NOT DEFINED CHEMANIM_EXECUTABLE OR NOT DEFINED CHEMANIM_DEPENDENCY_DIRECTORY)
    message(FATAL_ERROR "Runtime dependency copy arguments are missing")
endif()

file(GET_RUNTIME_DEPENDENCIES
    EXECUTABLES "${CHEMANIM_EXECUTABLE}"
    DIRECTORIES "${CHEMANIM_DEPENDENCY_DIRECTORY}"
    RESOLVED_DEPENDENCIES_VAR resolved
    UNRESOLVED_DEPENDENCIES_VAR unresolved
    PRE_EXCLUDE_REGEXES "api-ms-.*" "ext-ms-.*"
    POST_EXCLUDE_REGEXES ".*[Ww]indows[\\/].*"
)
get_filename_component(destination "${CHEMANIM_EXECUTABLE}" DIRECTORY)
foreach(dependency IN LISTS resolved)
    get_filename_component(name "${dependency}" NAME)
    file(COPY_FILE "${dependency}" "${destination}/${name}" ONLY_IF_DIFFERENT)
endforeach()
