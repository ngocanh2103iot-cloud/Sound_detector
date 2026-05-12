import csv
import shutil
import librosa
import soundfile as sf
from pathlib import Path
from tqdm import tqdm

# --- Cấu hình ---
URBANSOUND_DIR = Path("../UrbanSound8K/UrbanSound8K")
CSV_PATH       = URBANSOUND_DIR / "metadata" / "UrbanSound8K.csv"
AUDIO_DIR      = URBANSOUND_DIR / "audio"
OUTPUT_DIR     = Path("../dataset_raw/abnormal")

TARGET_SR = 16000

# classID theo README: 3=dog_bark, 6=gun_shot, 7=jackhammer
TARGET_CLASSES = {3: "dog_bark", 6: "gun_shot", 7: "jackhammer"}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# --- Đọc CSV và lọc ---
rows = []
with open(CSV_PATH, "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        class_id = int(row["classID"])
        if class_id in TARGET_CLASSES:
            rows.append(row)

print(f"Tìm thấy {len(rows)} file thuộc {list(TARGET_CLASSES.values())}")

# --- Copy và convert sang 16kHz mono WAV ---
stats = {name: 0 for name in TARGET_CLASSES.values()}
errors = 0

for row in tqdm(rows, desc="Processing"):
    filename = row["slice_file_name"]
    fold     = f"fold{row['fold']}"
    class_id = int(row["classID"])
    class_name = TARGET_CLASSES[class_id]

    src = AUDIO_DIR / fold / filename
    if not src.exists():
        errors += 1
        continue

    # Tên output: classname_originalname.wav
    dst = OUTPUT_DIR / f"{class_name}_{filename}"

    try:
        y, sr = librosa.load(src, sr=TARGET_SR, mono=True)
        sf.write(str(dst), y, TARGET_SR, subtype="PCM_16")
        stats[class_name] += 1
    except Exception as e:
        print(f"Error: {filename} — {e}")
        errors += 1

# --- Thống kê ---
print("\n" + "=" * 50)
print("DONE")
print("=" * 50)
for name, count in stats.items():
    print(f"  {name:15s}: {count:4d} files")
print(f"  {'errors':15s}: {errors:4d}")
print(f"Output: {OUTPUT_DIR.resolve()}")
