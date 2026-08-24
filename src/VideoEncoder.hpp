#pragma once

#include <cstdint>
#include <filesystem>
#include <memory>
#include <span>

namespace chem {

class VideoEncoder {
public:
    VideoEncoder(const std::filesystem::path& output, int width, int height,
                 int fps, int bitrate = 12'000'000);
    ~VideoEncoder();

    VideoEncoder(const VideoEncoder&) = delete;
    VideoEncoder& operator=(const VideoEncoder&) = delete;

    void writeFrame(std::span<const std::uint8_t> rgba);
    void finish();

private:
    struct Impl;
    std::unique_ptr<Impl> impl_;
};

} // namespace chem

