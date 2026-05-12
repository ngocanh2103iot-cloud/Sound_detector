#include "audio.h"
#include "config.h"
#include "esp_dsp.h"
#include "fbank_matrix.h"
#include <Arduino.h>
#include <math.h>

static float current_frame[n_fft];
static float fft_buffer[n_fft * 2] __attribute__((aligned(16)));
static float pow_frame[n_fft / 2 + 1];
static float mel_energies[n_mels];
static float hamming_window[n_fft];
static float dct_matrix[n_mfcc][n_mels];

#ifndef M_PI
#define M_PI 3.14159265358979323846f
#endif

void features_init() {
  dsps_fft2r_init_fc32(NULL, n_fft);

  for (int k = 0; k < n_fft; k++)
    hamming_window[k] = 0.54f - 0.46f * cosf(2.0f * M_PI * k / (n_fft - 1));

  for (int k = 0; k < n_mfcc; k++) {
    float factor = (k == 0) ? sqrtf(1.0f / n_mels) : sqrtf(2.0f / n_mels);
    for (int m = 0; m < n_mels; m++) {
      dct_matrix[k][m] =
          factor * cosf(M_PI * k * (2.0f * m + 1.0f) / (2.0f * n_mels));
    }
  }
}

// Trích xuất MFCC từ audio int16 → vector 39 chiều (13 mean + 13 std + 13 max)
void extract_mfccs(const int16_t *audio, float *mfcc_out) {
  float mfcc_sum[n_mfcc] = {0};
  float mfcc_sq_sum[n_mfcc] = {0};
  float mfcc_max[n_mfcc];

  // Khởi tạo max = giá trị rất nhỏ
  for (int k = 0; k < n_mfcc; k++)
    mfcc_max[k] = -1e30f;

  for (int f = 0; f < num_frames; f++) {
    int start_sample = f * hop_length;

    // A. Cắt khung + Pre-emphasis + Hamming window
    for (int k = 0; k < n_fft; k++) {
      int idx = start_sample + k;
      if (idx < num_samples) {
        float current_val = (float)audio[idx] / 32768.0f;
        float prev_val =
            (idx > 0) ? (float)audio[idx - 1] / 32768.0f : current_val;
        current_frame[k] =
            (current_val - 0.97f * prev_val) * hamming_window[k];
      } else {
        current_frame[k] = 0.0f;
      }
    }

    // B. FFT dùng ESP-DSP
    for (int k = 0; k < n_fft; k++) {
      fft_buffer[k * 2] = current_frame[k];
      fft_buffer[k * 2 + 1] = 0.0f;
    }
    dsps_fft2r_fc32(fft_buffer, n_fft);
    dsps_bit_rev_fc32(fft_buffer, n_fft);

    // C. Power Spectrum
    for (int k = 0; k <= n_fft / 2; k++) {
      float re = fft_buffer[k * 2];
      float im = fft_buffer[k * 2 + 1];
      pow_frame[k] = (re * re + im * im) / n_fft;
    }

    // D. Mel filterbank
    int weight_idx = 0;
    for (int m = 0; m < n_mels; m++) {
      float sum = 0.0f;
      int start = mel_starts[m], length = mel_lengths[m];

      if (length > 0) {
        dsps_dotprod_f32(&pow_frame[start], &mel_weights[weight_idx], &sum,
                         length);
        weight_idx += length;
      }

      if (sum < 1e-12f)
        sum = 1e-12f;
      mel_energies[m] = 10.0f * log10f(sum);
    }

    // E. DCT → MFCC cho frame này, tích lũy sum/sq_sum/max
    for (int k = 0; k < n_mfcc; k++) {
      float val = 0.0f;
      for (int m = 0; m < n_mels; m++)
        val += mel_energies[m] * dct_matrix[k][m];

      mfcc_sum[k] += val;
      mfcc_sq_sum[k] += val * val;
      if (val > mfcc_max[k])
        mfcc_max[k] = val;
    }
  }

  // Output: 39 chiều = [13 mean, 13 std, 13 max]
  for (int k = 0; k < n_mfcc; k++) {
    float mean = mfcc_sum[k] / num_frames;
    float variance = (mfcc_sq_sum[k] / num_frames) - (mean * mean);
    if (variance < 0.0f)
      variance = 0.0f;

    mfcc_out[k] = mean;                   // [0..12]  mean
    mfcc_out[k + n_mfcc] = sqrtf(variance); // [13..25] std
    mfcc_out[k + 2 * n_mfcc] = mfcc_max[k]; // [26..38] max
  }
}

void extract_features(float *features) { extract_mfccs(get_audio(), features); }
