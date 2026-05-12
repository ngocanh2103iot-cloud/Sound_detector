#pragma once
#include <stdint.h>

void audio_init();
void record_audio();
int16_t* get_audio();