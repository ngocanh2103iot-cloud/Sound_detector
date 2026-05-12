#pragma once

#include <stdint.h>

void features_init();
void extract_mfccs(const int16_t *audio, float *mfcc_out);
void extract_features(float *features);