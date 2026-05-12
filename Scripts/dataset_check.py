from librosa.core import audio
import os
import librosa
import numpy as np

Datapath = "D:\Education\Sound_detector\dataset"

target_sr = 16000
total = 0
error = 0

for root,dirs,files in os.walk(Datapath):
    for file in files:
        if file.endswith(('.wav')):
            total += 1
            path = os.path.join(root,file)
            try:
                audio, sr = librosa.load(path,sr=target_sr,mono=True)
                print("=" * 50)
                print(f"FILE: {path}")
                print(f"sample_rate: {sr}")
                print(f"shape: {audio.shape}")
                print(f"dtype: {audio.dtype}")
                print(f"duration: {len(audio)/sr:.2f} sec")
            except Exception as e:
                error += 1
                print(f"ERROR FILE: {path}")
                print(e)

print("\nDONE")
print(f"TOTAL FILES: {total}")
print(f"ERROR FILES: {error}")   
            
