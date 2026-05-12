#pragma once

#include <stddef.h>
#include <stdint.h>

namespace audio_reader {

constexpr size_t kPcmPayloadBytes = 640;  // 16kHz * 1ch * 16bit * 20ms

bool begin();
size_t readPcm(uint8_t *buffer, size_t bufferSize);

}  // namespace audio_reader
