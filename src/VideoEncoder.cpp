#include "VideoEncoder.hpp"

#ifdef _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <mfapi.h>
#include <mferror.h>
#include <mfidl.h>
#include <mfreadwrite.h>
#endif

#include <algorithm>
#include <iomanip>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace chem {

#ifdef _WIN32
namespace {

template <typename T>
void release(T*& value) {
    if (value) { value->Release(); value = nullptr; }
}

void check(HRESULT result, const char* operation) {
    if (SUCCEEDED(result)) return;
    std::ostringstream message;
    message << operation << " failed (HRESULT 0x" << std::hex << std::uppercase
            << static_cast<unsigned long>(result) << ')';
    throw std::runtime_error(message.str());
}

std::uint8_t clampByte(int value) {
    return static_cast<std::uint8_t>(std::clamp(value, 0, 255));
}

} // namespace

struct VideoEncoder::Impl {
    IMFSinkWriter* writer = nullptr;
    DWORD streamIndex = 0;
    int width = 0;
    int height = 0;
    LONGLONG nextTime = 0;
    LONGLONG frameDuration = 0;
    bool finished = false;
    bool mfStarted = false;
    bool ownsCom = false;

    ~Impl() {
        if (writer && !finished) writer->Finalize();
        release(writer);
        if (mfStarted) MFShutdown();
        if (ownsCom) CoUninitialize();
    }
};

VideoEncoder::VideoEncoder(const std::filesystem::path& output, int width, int height,
                           int fps, int bitrate)
    : impl_(std::make_unique<Impl>()) {
    if (width <= 0 || height <= 0 || fps <= 0 || (width % 2) || (height % 2)) {
        throw std::runtime_error("MP4 dimensions must be positive even numbers and fps must be positive");
    }
    impl_->width = width;
    impl_->height = height;
    impl_->frameDuration = 10'000'000LL / fps;

    const HRESULT comResult = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    if (SUCCEEDED(comResult)) impl_->ownsCom = true;
    else if (comResult != RPC_E_CHANGED_MODE) check(comResult, "CoInitializeEx");

    check(MFStartup(MF_VERSION), "MFStartup");
    impl_->mfStarted = true;

    IMFAttributes* attributes = nullptr;
    IMFMediaType* outputType = nullptr;
    IMFMediaType* inputType = nullptr;
    try {
        check(MFCreateAttributes(&attributes, 3), "MFCreateAttributes");
        check(attributes->SetUINT32(MF_READWRITE_ENABLE_HARDWARE_TRANSFORMS, TRUE), "Enable hardware transforms");
        check(attributes->SetUINT32(MF_SINK_WRITER_DISABLE_THROTTLING, TRUE), "Disable sink throttling");
        check(MFCreateSinkWriterFromURL(output.c_str(), nullptr, attributes, &impl_->writer),
              "MFCreateSinkWriterFromURL");

        check(MFCreateMediaType(&outputType), "Create H.264 media type");
        check(outputType->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video), "Set output major type");
        check(outputType->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_H264), "Set H.264 subtype");
        check(outputType->SetUINT32(MF_MT_AVG_BITRATE, static_cast<UINT32>(bitrate)), "Set bitrate");
        check(outputType->SetUINT32(MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive), "Set progressive mode");
        check(MFSetAttributeSize(outputType, MF_MT_FRAME_SIZE, width, height), "Set output frame size");
        check(MFSetAttributeRatio(outputType, MF_MT_FRAME_RATE, fps, 1), "Set output frame rate");
        check(MFSetAttributeRatio(outputType, MF_MT_PIXEL_ASPECT_RATIO, 1, 1), "Set pixel aspect ratio");
        check(impl_->writer->AddStream(outputType, &impl_->streamIndex), "Add H.264 stream");

        check(MFCreateMediaType(&inputType), "Create NV12 media type");
        check(inputType->SetGUID(MF_MT_MAJOR_TYPE, MFMediaType_Video), "Set input major type");
        check(inputType->SetGUID(MF_MT_SUBTYPE, MFVideoFormat_NV12), "Set NV12 subtype");
        check(inputType->SetUINT32(MF_MT_INTERLACE_MODE, MFVideoInterlace_Progressive), "Set input progressive mode");
        check(MFSetAttributeSize(inputType, MF_MT_FRAME_SIZE, width, height), "Set input frame size");
        check(MFSetAttributeRatio(inputType, MF_MT_FRAME_RATE, fps, 1), "Set input frame rate");
        check(MFSetAttributeRatio(inputType, MF_MT_PIXEL_ASPECT_RATIO, 1, 1), "Set input pixel aspect ratio");
        check(impl_->writer->SetInputMediaType(impl_->streamIndex, inputType, nullptr), "Set NV12 input type");
        check(impl_->writer->BeginWriting(), "Begin MP4 writing");
    } catch (...) {
        release(inputType); release(outputType); release(attributes);
        throw;
    }
    release(inputType); release(outputType); release(attributes);
}

VideoEncoder::~VideoEncoder() = default;

void VideoEncoder::writeFrame(std::span<const std::uint8_t> rgba) {
    if (!impl_ || impl_->finished) throw std::runtime_error("Cannot write to a finalized MP4");
    const std::size_t pixelCount = static_cast<std::size_t>(impl_->width) * impl_->height;
    if (rgba.size() != pixelCount * 4) throw std::runtime_error("Unexpected RGBA frame size");

    std::vector<std::uint8_t> nv12(pixelCount + pixelCount / 2);
    auto yPlane = nv12.data();
    auto uvPlane = nv12.data() + pixelCount;

    for (int y = 0; y < impl_->height; ++y) {
        for (int x = 0; x < impl_->width; ++x) {
            const std::size_t pixel = (static_cast<std::size_t>(y) * impl_->width + x) * 4;
            const int r = rgba[pixel]; const int g = rgba[pixel + 1]; const int b = rgba[pixel + 2];
            yPlane[static_cast<std::size_t>(y) * impl_->width + x] = clampByte(((66*r + 129*g + 25*b + 128) >> 8) + 16);
        }
    }
    for (int y = 0; y < impl_->height; y += 2) {
        for (int x = 0; x < impl_->width; x += 2) {
            int sumU = 0; int sumV = 0;
            for (int dy = 0; dy < 2; ++dy) {
                for (int dx = 0; dx < 2; ++dx) {
                    const std::size_t pixel = (static_cast<std::size_t>(y + dy) * impl_->width + x + dx) * 4;
                    const int r = rgba[pixel]; const int g = rgba[pixel + 1]; const int b = rgba[pixel + 2];
                    sumU += ((-38*r - 74*g + 112*b + 128) >> 8) + 128;
                    sumV += ((112*r - 94*g - 18*b + 128) >> 8) + 128;
                }
            }
            const std::size_t uv = static_cast<std::size_t>(y / 2) * impl_->width + x;
            uvPlane[uv] = clampByte(sumU / 4);
            uvPlane[uv + 1] = clampByte(sumV / 4);
        }
    }

    IMFMediaBuffer* buffer = nullptr;
    IMFSample* sample = nullptr;
    BYTE* destination = nullptr;
    try {
        check(MFCreateMemoryBuffer(static_cast<DWORD>(nv12.size()), &buffer), "Create video buffer");
        check(buffer->Lock(&destination, nullptr, nullptr), "Lock video buffer");
        std::copy(nv12.begin(), nv12.end(), destination);
        check(buffer->Unlock(), "Unlock video buffer"); destination = nullptr;
        check(buffer->SetCurrentLength(static_cast<DWORD>(nv12.size())), "Set video buffer length");
        check(MFCreateSample(&sample), "Create video sample");
        check(sample->AddBuffer(buffer), "Attach video buffer");
        check(sample->SetSampleTime(impl_->nextTime), "Set sample time");
        check(sample->SetSampleDuration(impl_->frameDuration), "Set sample duration");
        check(impl_->writer->WriteSample(impl_->streamIndex, sample), "Write video sample");
        impl_->nextTime += impl_->frameDuration;
    } catch (...) {
        if (destination && buffer) buffer->Unlock();
        release(sample); release(buffer);
        throw;
    }
    release(sample); release(buffer);
}

void VideoEncoder::finish() {
    if (!impl_ || impl_->finished) return;
    check(impl_->writer->Finalize(), "Finalize MP4");
    impl_->finished = true;
}

#else

struct VideoEncoder::Impl {};
VideoEncoder::VideoEncoder(const std::filesystem::path&, int, int, int, int) {
    throw std::runtime_error("Direct MP4 encoding is currently supported on Windows only");
}
VideoEncoder::~VideoEncoder() = default;
void VideoEncoder::writeFrame(std::span<const std::uint8_t>) {}
void VideoEncoder::finish() {}

#endif

} // namespace chem

