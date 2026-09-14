#include "LuaRuntime.hpp"
#include "Renderer.hpp"
#include "VideoEncoder.hpp"
#include "core/Codegen.hpp"
#include "core/Document.hpp"

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
#include <cctype>
#include <filesystem>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <optional>
#include <sstream>
#include <stdexcept>
#include <string>

namespace {

struct Options {
    std::optional<std::filesystem::path> document;
    bool openWhenFinished = true;
    bool still = false;
    int stillFrame = 0;
    bool profile = false;
};

void printHelp() {
    std::cout <<
        "Chemanim - render one saved .cmm document directly\n\n"
        "Usage:\n"
        "  chemanim.exe reaction.cmm\n"
        "  chemanim.exe reaction.cmm --no-open\n"
        "  chemanim.exe reaction.cmm --frame 30 --no-open\n\n"
        "Output (next to the .cmm document):\n"
        "  reaction_YYYY-MM-DD_HH-MM-SS.mp4\n"
        "  reaction_frame_30.png (--frame 30)\n";
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
            options.stillFrame = std::max(0, std::stoi(argv[i]));
            options.still = true;
        } else if (argument.starts_with('-')) {
            throw std::runtime_error("Unknown option: " + argument);
        } else if (!options.document) {
            options.document = std::filesystem::path(argument);
        } else {
            throw std::runtime_error("Only one .cmm document may be specified");
        }
    }
    if (!options.document) throw std::runtime_error("A saved .cmm document path is required");
    return options;
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

std::filesystem::path resolveDocument(const std::filesystem::path& requested) {
    const auto document = std::filesystem::absolute(requested).lexically_normal();
    if (!std::filesystem::is_regular_file(document)) {
        throw std::runtime_error("CMM document not found: " + document.string());
    }
    std::string extension = document.extension().string();
    std::transform(extension.begin(), extension.end(), extension.begin(),
                   [](unsigned char c) { return static_cast<char>(std::tolower(c)); });
    if (extension != ".cmm") throw std::runtime_error("Input must be a .cmm document");
    return document;
}

} // namespace

int main(int argc, char** argv) {
    try {
        const Options options = parseOptions(argc, argv);
        const std::filesystem::path document = resolveDocument(*options.document);
        const std::filesystem::path outputDirectory = document.parent_path();
        const std::string baseName = document.stem().string().empty() ? "chemanim" : document.stem().string();
        const std::filesystem::path output = options.still
            ? outputDirectory / (baseName + "_frame_" + std::to_string(options.stillFrame) + ".png")
            : outputDirectory / (baseName + "_" + timestamp() + ".mp4");

        std::cout << "Document: " << document.string() << "\nOutput:   " << output.string() << "\n";

        const chem::core::Project project = chem::core::loadProject(document);
        chem::LuaRuntime runtime;
        runtime.runSource(chem::core::compileLua(project), document.parent_path(), document.filename().string());
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
            const auto& profile = renderer.profile();
            const int frames = engine.scene.endFrame + 1;
            std::filesystem::path profilePath = output;
            profilePath.replace_extension(".profile.json");
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
