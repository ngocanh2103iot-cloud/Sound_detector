# ── verify_dummy.py: Cross-check ESP32 inference using Python ────────────────
# Loads the same dummy WAV, extracts MFCCs (matching ESP32 pipeline),
# then runs Nystroem + Linear OCSVM to compare scores.
#
# Usage: python verify_dummy.py "../dataset/test/abnormal/0000_dog_bark_54823-3-2-1.wav"

import sys
import os
import numpy as np
import librosa
import pickle

TARGET_SR = 16000
N_FFT = 512
HOP_LENGTH = 256
N_MELS = 40
N_MFCC = 13
NUM_SAMPLES = 16000

def extract_mfcc_esp32_style(wav_path):
    """Replicate the ESP32 MFCC pipeline in Python."""
    y, sr = librosa.load(wav_path, sr=TARGET_SR, mono=True)
    if len(y) < NUM_SAMPLES:
        y = np.pad(y, (0, NUM_SAMPLES - len(y)))
    else:
        y = y[:NUM_SAMPLES]

    # Pre-emphasis
    y_pre = np.append(y[0], y[1:] - 0.97 * y[:-1])

    # STFT with Hann window (librosa default), but ESP32 uses Hamming
    # For verification, use same params
    S = librosa.feature.melspectrogram(
        y=y_pre, sr=TARGET_SR, n_fft=N_FFT, hop_length=HOP_LENGTH,
        n_mels=N_MELS, window='hamming', power=2.0
    )
    S_db = librosa.power_to_db(S, ref=1.0)

    mfcc = librosa.feature.mfcc(S=S_db, n_mfcc=N_MFCC)

    # Stats: mean, std, max across frames → 39 dims
    mfcc_mean = mfcc.mean(axis=1)
    mfcc_std  = mfcc.std(axis=1)
    mfcc_max  = mfcc.max(axis=1)

    features = np.concatenate([mfcc_mean, mfcc_std, mfcc_max])
    return features

def main():
    if len(sys.argv) < 2:
        print("Usage: python verify_dummy.py <wav_path>")
        return

    wav_path = sys.argv[1]
    if not os.path.exists(wav_path):
        print(f"File not found: {wav_path}")
        return

    # Load saved model
    model_dir = "saved_models"
    import joblib
    nystroem = joblib.load(os.path.join(model_dir, "nystroem.pkl"))
    ocsvm = joblib.load(os.path.join(model_dir, "ocsvm_linear.pkl"))
    scaler = joblib.load(os.path.join(model_dir, "scaler.pkl"))

    features = extract_mfcc_esp32_style(wav_path)
    print(f"Features (first 5): {features[:5]}")

    # Scale
    features_scaled = scaler.transform(features.reshape(1, -1))

    # Nystroem transform
    features_nys = nystroem.transform(features_scaled)

    # OCSVM decision
    score = ocsvm.decision_function(features_nys)[0]

    print(f"\nPython OCSVM score: {score:.4f}")
    print(f"THRESHOLD_1 = -2.0, THRESHOLD_2 = 4.0911")
    if score >= 4.0911:
        print("-> NORMAL")
    elif score <= -2.0:
        print("-> ABNORMAL")
    else:
        print("-> UNCERTAIN")

if __name__ == "__main__":
    main()
