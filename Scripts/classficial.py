import os
import random
import shutil
from pathlib import Path

random.seed(42)

source_dir = "../dataset_raw"
outsource_dir = "../dataset"

# --- OCSVM layout ---
# train/normal    : 70% of Normal data (used for model training)
# val/normal      : 15% of Normal data (used for evaluation)
# val/abnormal    : 50% of Abnormal data (used for evaluation)
# test/normal     : 15% of Normal data (used for final test)
# test/abnormal   : 50% of Abnormal data (used for final test)
folders = [
    "train/normal",
    "val/normal",
    "val/abnormal",
    "test/normal",
    "test/abnormal",
]
for folder in folders:
    os.makedirs(os.path.join(outsource_dir, folder), exist_ok=True)


def get_files(folder):
    """Return sorted list of .wav files under folder (recursive)."""
    p = Path(folder)
    if not p.exists():
        return []
    return sorted(p.rglob("*.wav"))


def copy_files(files, target_folder):
    """Copy files into target_folder, prepending index to avoid name collisions."""
    for i, file_path in enumerate(files):
        unique_name = f"{i:04d}_{file_path.name}"
        dst = os.path.join(outsource_dir, target_folder, unique_name)
        shutil.copy(file_path, dst)


# --- Normal split: 70 / 15 / 15 ---
normal_files = get_files(os.path.join(source_dir, "normal"))
if not normal_files:
    raise FileNotFoundError(f"No .wav files found in '{source_dir}/normal'. Check source_dir.")

random.shuffle(normal_files)
n_total = len(normal_files)
n_train = int(0.70 * n_total)
n_val   = int(0.15 * n_total)

train_normal = normal_files[:n_train]
val_normal   = normal_files[n_train:n_train + n_val]
test_normal  = normal_files[n_train + n_val:]

copy_files(train_normal, "train/normal")
copy_files(val_normal,   "val/normal")
copy_files(test_normal,  "test/normal")

print(f"Normal  — train: {len(train_normal)}, val: {len(val_normal)}, test: {len(test_normal)}")

# --- Abnormal split: 50 / 50 (val / test only — NOT used for training) ---
abnormal_files = get_files(os.path.join(source_dir, "abnormal"))
if not abnormal_files:
    print("Warning: No abnormal data found. Skipping abnormal split.")
else:
    random.shuffle(abnormal_files)
    n_half = len(abnormal_files) // 2
    val_abnormal  = abnormal_files[:n_half]
    test_abnormal = abnormal_files[n_half:]

    copy_files(val_abnormal,  "val/abnormal")
    copy_files(test_abnormal, "test/abnormal")

    print(f"Abnormal — val: {len(val_abnormal)}, test: {len(test_abnormal)}")
