# ── dummy_gen.py: Generate dummy_audio.h from a WAV sample ──────────────────
# Reads a 1-second WAV file (16kHz, mono), converts to int16 C array.
# Usage:
#   python dummy_gen.py <path_to_wav> [--output <output_path>]
#
# Example:
#   python dummy_gen.py "../dataset/test/normal/0000_Window Curtains_023_0dB.wav"
#   python dummy_gen.py "../dataset/test/abnormal/0000_dog_bark_54823-3-2-1.wav"

import argparse
import os
import numpy as np
import librosa

TARGET_SR = 16000
TARGET_SAMPLES = 16000  # 1 second

def main():
    parser = argparse.ArgumentParser(description="Generate dummy_audio.h from WAV")
    parser.add_argument("wav_path", help="Path to input WAV file")
    parser.add_argument("--output", default="../esp32_firmware/src/dummy_audio.h",
                        help="Output header path (default: ../esp32_firmware/src/dummy_audio.h)")
    args = parser.parse_args()

    if not os.path.exists(args.wav_path):
        print(f"ERROR: File not found: {args.wav_path}")
        return

    # Load and resample to 16kHz mono
    y, sr = librosa.load(args.wav_path, sr=TARGET_SR, mono=True)
    print(f"Loaded: {args.wav_path}")
    print(f"  Original length: {len(y)} samples ({len(y)/TARGET_SR:.2f}s)")

    # Pad or truncate to exactly TARGET_SAMPLES
    if len(y) < TARGET_SAMPLES:
        y = np.pad(y, (0, TARGET_SAMPLES - len(y)), mode='constant')
    else:
        y = y[:TARGET_SAMPLES]

    # Convert float32 [-1, 1] to int16 [-32768, 32767]
    y_int16 = np.clip(y * 32768.0, -32768, 32767).astype(np.int16)

    # Stats
    print(f"  Output: {TARGET_SAMPLES} samples (int16)")
    print(f"  Range: [{y_int16.min()}, {y_int16.max()}]")
    print(f"  RMS: {np.sqrt(np.mean(y_int16.astype(float)**2)):.1f}")

    # Write C header
    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write('#pragma once\n')
        f.write('#include <stdint.h>\n\n')
        f.write(f'// Auto-generated from: {os.path.basename(args.wav_path)}\n')
        f.write(f'// Samples: {TARGET_SAMPLES}, Sample Rate: {TARGET_SR}Hz\n\n')
        f.write(f'const int16_t dummy_audio[{TARGET_SAMPLES}] = {{\n')

        # Write 16 values per line
        for i in range(0, TARGET_SAMPLES, 16):
            chunk = y_int16[i:i+16]
            line = ', '.join(str(v) for v in chunk)
            if i + 16 < TARGET_SAMPLES:
                f.write(f'    {line},\n')
            else:
                f.write(f'    {line}\n')

        f.write('};\n')

    file_size = os.path.getsize(args.output) / 1024
    print(f"\nExported: {args.output}")
    print(f"File size: {file_size:.1f} KB")

if __name__ == '__main__':
    main()
