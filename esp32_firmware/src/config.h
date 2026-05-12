#pragma once

#define USE_DUMMY_AUDIO 1  // Change to 0 to use real I2S microphone (INMP441)

#define SAMPLE_RATE 16000
#define FRAME_SIZE 512

#define I2S_WS 25
#define I2S_SD 33
#define I2S_SCK 32

#define n_fft 512
#define hop_length 256
#define n_mels 40
#define n_mfcc 13
#define num_samples 16000
#define num_frames 61

#define FEATURE_COUNT 39