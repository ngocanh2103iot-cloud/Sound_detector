import os
import random
import shutil
import librosa
from pathlib import Path

random.seed(42)

DATASET_DIR  = Path("../dataset")
ABNORMAL_SRC = Path("../dataset_raw/abnormal")
TARGET_SR    = 16000
FRAME_LENGTH = 16000   # 1 giây
HOP_LENGTH   = 8000    # 50% overlap


def count_frames(folder):
    """Đếm tổng số frame 1s sẽ được tạo sau windowing."""
    total = 0
    for f in sorted(Path(folder).rglob("*.wav")):
        y, _ = librosa.load(f, sr=TARGET_SR, mono=True)
        if len(y) >= FRAME_LENGTH:
            total += 1 + (len(y) - FRAME_LENGTH) // HOP_LENGTH
    return total


def pick_files_by_frames(files, target_frames):
    """Chọn file cho đến khi tổng frame >= target_frames."""
    picked = []
    accumulated = 0
    for f in files:
        y, _ = librosa.load(f, sr=TARGET_SR, mono=True)
        n = len(y)
        if n < FRAME_LENGTH:
            continue
        frames = 1 + (n - FRAME_LENGTH) // HOP_LENGTH
        picked.append(f)
        accumulated += frames
        if accumulated >= target_frames:
            break
    return picked, accumulated


# --- Đếm frame normal ---
print("Counting val/normal frames...")
val_normal_frames = count_frames(DATASET_DIR / "val/normal")
print(f"  Val  normal: {val_normal_frames} frames")

print("Counting test/normal frames...")
test_normal_frames = count_frames(DATASET_DIR / "test/normal")
print(f"  Test normal: {test_normal_frames} frames")

# --- Shuffle abnormal ---
abnormal_files = sorted(ABNORMAL_SRC.rglob("*.wav"))
random.shuffle(abnormal_files)
print(f"\nTotal abnormal source files: {len(abnormal_files)}")

# --- Chọn file abnormal khớp số frame ---
print("\nPicking val abnormal...")
val_abnormal, val_abn_frames = pick_files_by_frames(abnormal_files, val_normal_frames)

# Bỏ các file đã dùng cho val, lấy tiếp cho test
remaining = [f for f in abnormal_files if f not in set(val_abnormal)]
print("Picking test abnormal...")
test_abnormal, test_abn_frames = pick_files_by_frames(remaining, test_normal_frames)


# --- Copy ---
def copy_files(files, target_folder):
    target = DATASET_DIR / target_folder
    target.mkdir(parents=True, exist_ok=True)
    for old in target.glob("*.wav"):
        old.unlink()
    for i, f in enumerate(files):
        dst = target / f"{i:04d}_{f.name}"
        shutil.copy(f, dst)


copy_files(val_abnormal,  "val/abnormal")
copy_files(test_abnormal, "test/abnormal")

# --- Thống kê ---
print("\n" + "=" * 55)
print(f"{'':15s} {'files':>8s}  {'frames':>8s}")
print("-" * 55)
print(f"{'Val  normal':15s} {'-':>8s}  {val_normal_frames:>8d}")
print(f"{'Val  abnormal':15s} {len(val_abnormal):>8d}  {val_abn_frames:>8d}")
print(f"{'Test normal':15s} {'-':>8s}  {test_normal_frames:>8d}")
print(f"{'Test abnormal':15s} {len(test_abnormal):>8d}  {test_abn_frames:>8d}")
print("=" * 55)
