#include "audio.h"
#include "config.h"
#include "dummy_audio.h"
#include "audio_reader.h"

#include <Arduino.h>
#include <math.h>
#include <string.h>

static int16_t audio_buffer[num_samples];
static bool is_first_run = true;

static bool read_pcm_exact(int16_t *dst, size_t sample_count) {
  uint8_t *out = reinterpret_cast<uint8_t *>(dst);
  size_t bytes_remaining = sample_count * sizeof(int16_t);

  while (bytes_remaining > 0) {
    size_t chunk_bytes = bytes_remaining;
    if (chunk_bytes > audio_reader::kPcmPayloadBytes) {
      chunk_bytes = audio_reader::kPcmPayloadBytes;
    }

    size_t bytes_read = audio_reader::readPcm(out, chunk_bytes);
    if (bytes_read == 0) {
      memset(out, 0, bytes_remaining);
      return false;
    }

    out += bytes_read;
    bytes_remaining -= bytes_read;
  }

  return true;
}

void audio_init() {
#if USE_DUMMY_AUDIO
  Serial.println("Audio Init (Dummy Mode)");
#else
  Serial.println("Audio Init (AudioTools I2S Mode - INMP441)");
  if (!audio_reader::begin()) {
    Serial.println("Audio Init failed");
  }
#endif
}

void record_audio() {
#if USE_DUMMY_AUDIO
  for (int i = 0; i < num_samples; i++) {
    audio_buffer[i] = dummy_audio[i];
  }
  delay((SLIDING_STEP * 1000) / SAMPLE_RATE);
#else
  const size_t samples_to_read = is_first_run ? num_samples : SLIDING_STEP;
  const size_t start_idx = is_first_run ? 0 : (num_samples - SLIDING_STEP);

  if (!is_first_run) {
    memmove(audio_buffer,
            audio_buffer + SLIDING_STEP,
            (num_samples - SLIDING_STEP) * sizeof(audio_buffer[0]));
  }

  bool ok = read_pcm_exact(audio_buffer + start_idx, samples_to_read);
  is_first_run = false;

  int64_t sum_sq = 0;
  for (int i = 0; i < num_samples; i++) {
    sum_sq += (int64_t)audio_buffer[i] * audio_buffer[i];
  }

  float rms = sqrt((float)sum_sq / num_samples);
  Serial.printf("[MIC] RMS=%.1f%s\n", rms, ok ? "" : " read failed");
#endif
}

int16_t *get_audio() { return audio_buffer; }
