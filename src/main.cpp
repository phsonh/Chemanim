#include "LuaRuntime.hpp"
#include "Renderer.hpp"
#include "VideoEncoder.hpp"

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#define CloseWindow CloseWindowWin32
#define ShowCursor ShowCursorWin32
#include <windows.h>
#include <shellapi.h>
#undef ShowCursor
#undef CloseWindow
#endif

#include <algorithm>
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

struct Options {
    std::optional<std::string> modName;
    bool openWhenFinished = true;
    bool still = false;
    int stillFrame = 0;
    bool profile = false;
};

void printHelp() {
    std::cout <<
        "Chemanim - render a Lua chemistry-animation mod directly to MP4\n\n"
        "Usage:\n"
        "  chemanim.exe aldol       Render mod/aldol/main.lua\n"
        "  chemanim.exe             Auto-select when mod/ contains exactly one mod\n"
        "  chemanim.exe native2d_demo --still --no-open\n"
        "  chemanim.exe atom_motion --frame 30 --no-open\n"
        "  chemanim.exe aldol --no-open\n\n"
        "Output:\n"
        "  media/aldol/aldol_YYYY-MM-DD_HH-MM-SS.mp4\n"
        "  media/native2d_demo/native2d_demo_preview.png (--still)\n";
}

Options parseOptions(int argc, char** argv) {
    Options options;
    for (int i = 1; i < argc; ++i) {
        const std::string argument = argv[i];
        if (argument == "--help" || argument == "-h") { printHelp(); std::exit(0); }
        if (argument == "--no-open") options.openWhenFinished = false;
        else if (argument == "--still") options.still = true;
        else if (argument == "--profile") options.profile = true;
        else if (argument == "--frame") {
            if (++i >= argc) throw std::runtime_error("--frame requires a non-negative frame number");
            options.stillFrame = std::max(0, std::stoi(argv[i])); options.still = true;
        }
        else if (argument.starts_with('-')) throw std::runtime_error("Unknown option: " + argument);
        else if (!options.modName) options.modName = argument;
        else throw std::runtime_error("Only one mod name may be specified");
    }
    return options;
}

std::filesystem::path executableDirectory() {
#ifdef _WIN32
    std::wstring buffer(32768, L'\0');
    const DWORD length = GetModuleFileNameW(nullptr, buffer.data(), static_cast<DWORD>(buffer.size()));
    if (length > 0 && length < buffer.size()) {
        buffer.resize(length);
        return std::filesystem::path(buffer).parent_path();
    }
#endif
    return std::filesystem::current_path();
}

std::optional<std::filesystem::path> findRootFrom(std::filesystem::path directory) {
    std::error_code error;
    directory = std::filesystem::weakly_canonical(directory, error);
    if (error) return std::nullopt;
    while (!directory.empty()) {
        if (std::filesystem::is_directory(directory / "mod")) return directory;
        const auto parent = directory.parent_path();
        if (parent == directory) break;
        directory = parent;
    }
    return std::nullopt;
}

std::filesystem::path findProjectRoot() {
    if (const auto root = findRootFrom(std::filesystem::current_path())) return *root;
    if (const auto root = findRootFrom(executableDirectory())) return *root;
    throw std::runtime_error("Cannot find a project root containing the 'mod' directory");
}

std::string selectMod(const std::filesystem::path& root, const Options& options) {
    const auto modRoot = root / "mod";
    if (options.modName) {
        const std::filesystem::path namePath(*options.modName);
        if (namePath.has_parent_path() || namePath.filename() != namePath || *options.modName == "." || *options.modName == "..") {
            throw std::runtime_error("Mod name must be one directory name, not a path");
        }
        if (!std::filesystem::is_regular_file(modRoot / namePath / "main.lua")) {
            throw std::runtime_error("Mod entry not found: " + (modRoot / namePath / "main.lua").string());
        }
        return *options.modName;
    }

    std::vector<std::string> candidates;
    for (const auto& entry : std::filesystem::directory_iterator(modRoot)) {
        if (entry.is_directory() && std::filesystem::is_regular_file(entry.path() / "main.lua")) {
            candidates.push_back(entry.path().filename().string());
        }
    }
    std::sort(candidates.begin(), candidates.end());
    if (candidates.empty()) throw std::runtime_error("No mod/*/main.lua entry was found");
    if (candidates.size() == 1) return candidates.front();

    std::ostringstream message;
    message << "More than one mod is available; specify one on the command line:";
    for (const auto& name : candidates) message << "\n  " << name;
    throw std::runtime_error(message.str());
}

std::string timestamp() {
    const auto now = std::chrono::system_clock::now();
    const std::time_t value = std::chrono::system_clock::to_time_t(now);
    std::tm local{};
#ifdef _WIN32
    localtime_s(&local, &value);
#else
    localtime_r(&value, &local);
#endif
    std::ostringstream result;
    result << std::put_time(&local, "%Y-%m-%d_%H-%M-%S");
    return result.str();
}

bool openWithDefaultApplication(const std::filesystem::path& path) {
#ifdef _WIN32
    const HINSTANCE result = ShellExecuteW(nullptr, L"open", path.c_str(), nullptr,
                                           path.parent_path().c_str(), SW_SHOWNORMAL);
    return reinterpret_cast<std::intptr_t>(result) > 32;
#else
    (void)path;
    return false;
#endif
}

} // namespace

int main(int argc, char** argv) {
    try {
        const Options options = parseOptions(argc, argv);
        const std::filesystem::path root = findProjectRoot();
        const std::string modName = selectMod(root, options);
        const std::filesystem::path script = root / "mod" / modName / "main.lua";
        const std::filesystem::path mediaDirectory = root / "media" / modName;
        std::filesystem::create_directories(mediaDirectory);
        const std::filesystem::path output = options.still
            ? mediaDirectory / (modName + "_frame_" + std::to_string(options.stillFrame) + ".png")
            : mediaDirectory / (modName + "_" + timestamp() + ".mp4");

        std::cout << "Mod:    " << modName << "\nEntry:  " << script.string()
                  << "\nOutput: " << output.string() << "\n";

        chem::LuaRuntime runtime;
        runtime.runScript(script);
        chem::Engine& engine = runtime.engine();
        chem::Renderer renderer(engine);
        renderer.initialize(true);
        if (options.still) {
            renderer.renderScene(options.stillFrame);
            renderer.savePng(output);
            std::cout << "Created: " << output.string() << "\n";
            if (options.openWhenFinished && !openWithDefaultApplication(output)) {
                std::cerr << "The PNG was created, but Windows could not open the default image viewer.\n";
            }
            return 0;
        }
        chem::VideoEncoder encoder(output, engine.scene.width, engine.scene.height, engine.scene.fps);
        const auto renderStart = std::chrono::steady_clock::now();
        for (int frame = 0; frame <= engine.scene.endFrame; ++frame) {
            renderer.renderScene(frame);
            encoder.writeFrame(renderer.captureRgba());
            if (frame % 30 == 0 || frame == engine.scene.endFrame) {
                std::cout << "Encoding frame " << frame << " / " << engine.scene.endFrame << "\r" << std::flush;
            }
        }
        encoder.finish();
        const double elapsed = std::chrono::duration<double>(std::chrono::steady_clock::now() - renderStart).count();
        std::cout << "\nCreated: " << output.string() << "\n";

        if (options.profile) {
            const auto& profile = renderer.profile(); const int frames = engine.scene.endFrame + 1;
            std::filesystem::path profilePath = output; profilePath.replace_extension(".profile.json");
            std::ofstream report(profilePath, std::ios::binary | std::ios::trunc);
            report << std::fixed << std::setprecision(3)
                   << "{\n  \"frames\": " << frames << ",\n  \"wall_seconds\": " << elapsed
                   << ",\n  \"frames_per_second\": " << (frames / std::max(.000001, elapsed))
                   << ",\n  \"svg_generation_ms\": " << profile.svgGenerationMs
                   << ",\n  \"svg_parsing_ms\": " << profile.svgParsingMs
                   << ",\n  \"svg_rasterization_ms\": " << profile.svgRasterizationMs
                   << ",\n  \"texture_upload_ms\": " << profile.textureUploadMs
                   << ",\n  \"molecule_cache_hits\": " << profile.moleculeCacheHits
                   << ",\n  \"molecule_cache_misses\": " << profile.moleculeCacheMisses << "\n}\n";
            std::cout << "Profile: " << profilePath.string() << "\n";
        }

        if (options.openWhenFinished && !openWithDefaultApplication(output)) {
            std::cerr << "The MP4 was created, but Windows could not open the default video player.\n";
        }
        return 0;
    } catch (const std::exception& error) {
        std::cerr << "Chemanim error:\n" << error.what() << "\n";
        return 1;
    }
}
