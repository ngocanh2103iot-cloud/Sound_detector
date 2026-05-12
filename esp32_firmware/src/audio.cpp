#include "audio.h"
#include "config.h"
#include "dummy_audio.h"
#include <Arduino.h>
#include <driver/i2s.h>


static int16_t audio_buffer[num_samples];

void audio_init() {
#if USE_DUMMY_AUDIO
  Serial.println("Audio Init (Dummy Mode)");
#else
  Serial.println("Audio Init (I2S Mode - INMP441)");

  i2s_config_t i2s_config = {
      .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX),
      .sample_rate = SAMPLE_RATE,
      .bits_per_sample =
          I2S_BITS_PER_SAMPLE_32BIT, // INMP441 is 24-bit, usually read as
                                     // 32-bit then shifted
      .channel_format = I2S_CHANNEL_FMT_ONLY_LEFT,
      .communication_format = I2S_COMM_FORMAT_STAND_I2S,
      .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
      .dma_buf_count = 8,
      .dma_buf_len = 1024,
      .use_apll = false,
      .tx_desc_auto_clear = false,
      .fixed_mclk = 0};

  i2s_pin_config_t pin_config = {.bck_io_num = I2S_SCK,
                                 .ws_io_num = I2S_WS,
                                 .data_out_num = I2S_PIN_NO_CHANGE,
                                 .data_in_num = I2S_SD};

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);
  i2s_zero_dma_buffer(I2S_NUM_0);
#endif
}

void record_audio() {
#if USE_DUMMY_AUDIO
  // Copy dữ liệu từ mảng dummy_audio sang audio_buffer để giả lập việc ghi âm
  for (int i = 0; i < num_samples; i++) {
    audio_buffer[i] = dummy_audio[i];
  }

  // Giả lập thời gian chờ ghi âm thực tế (1 giây)
  delay(1000);
#else
  size_t bytes_read;
  const int CHUNK_SIZE = 256; // Đọc 256 mẫu (1024 bytes) mỗi vòng lặp để tối ưu hiệu suất
  int32_t i2s_chunk[CHUNK_SIZE];
  
  int samples_read = 0;

  // Đọc liên tục theo từng block cho đến khi đủ 1 giây (16000 mẫu)
  while (samples_read < num_samples) {
    i2s_read(I2S_NUM_0, (void*)i2s_chunk, sizeof(i2s_chunk), &bytes_read, portMAX_DELAY);
    
    int samples_in_chunk = bytes_read / 4; // Mỗi mẫu 32-bit = 4 bytes
    for (int i = 0; i < samples_in_chunk; i++) {
      if (samples_read < num_samples) {
        // INMP441 trả về 24-bit dữ liệu ở các bit cao (MSB) của frame 32-bit.
        // Dịch phải 14 bit (thay vì 16 bit) để lấy int16_t đồng thời tăng Gain (khuếch đại) lên 4 lần.
        audio_buffer[samples_read++] = (int16_t)(i2s_chunk[i] >> 14);
      }
    }
  }
#endif
}

int16_t *get_audio() { return audio_buffer; }