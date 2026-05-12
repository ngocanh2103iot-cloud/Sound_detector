#include "audio_reader.h"

#include <Arduino.h>

#include "AudioTools.h"

using namespace audio_tools;

namespace {

constexpr int kPinI2sBck = 14;
constexpr int kPinI2sWs = 15;
constexpr int kPinI2sSd = 32;

const AudioInfo kMicInfo(16000, 2, 32);
const AudioInfo kMicMonoInfo(16000, 1, 32);
const AudioInfo kPcmInfo(16000, 1, 16);
constexpr float kAudioGain = 0.5f;

I2SStream mic;
ChannelFormatConverterStream channelConverter(mic);
NumberFormatConverterStream numberConverter(channelConverter);

bool audioStarted = false;

}  // namespace

namespace audio_reader {

bool begin() {
  if (audioStarted) {
    return true;
  }

  auto cfg = mic.defaultConfig(RX_MODE);
  cfg.sample_rate = kMicInfo.sample_rate;
  cfg.channels = kMicInfo.channels;
  cfg.bits_per_sample = 32;  // INMP441 outputs in 32-bit I2S slots
#if defined(I2S_CHANNEL_FMT_ONLY_LEFT)
  cfg.channel_format = I2S_CHANNEL_FMT_ONLY_LEFT;  // INMP441 L/R tied to GND -> left channel
#elif defined(I2S_CHANNEL_FMT_ALL_LEFT)
  cfg.channel_format = I2S_CHANNEL_FMT_ALL_LEFT;
#endif
  cfg.i2s_format = I2S_STD_FORMAT;
  cfg.is_master = true;
  cfg.pin_bck = kPinI2sBck;
  cfg.pin_ws = kPinI2sWs;
  cfg.pin_data = kPinI2sSd;
  cfg.buffer_count = 16;
  cfg.buffer_size = 1024;
  cfg.use_apll = false;

  if (!mic.begin(cfg)) {
    Serial.println("Failed to start I2S microphone");
    return false;
  }

  if (!channelConverter.begin(kMicInfo, kMicMonoInfo)) {
    Serial.println("Failed to start channel converter");
    return false;
  }

  if (!numberConverter.begin(kMicMonoInfo, kPcmInfo.bits_per_sample, kAudioGain)) {
    Serial.println("Failed to start number converter");
    return false;
  }

  audioStarted = true;
  return true;
}

size_t readPcm(uint8_t *buffer, size_t bufferSize) {
  if (!audioStarted && !begin()) {
    return 0;
  }

  return numberConverter.readBytes(buffer, bufferSize);
}

}  // namespace audio_reader
