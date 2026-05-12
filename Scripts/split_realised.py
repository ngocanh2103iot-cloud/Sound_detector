import librosa
import soundfile as sf
from pathlib import Path
import shutil
import argparse
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_filename(filename: str):
    """Parse filename theo format ReaLISED: abc_123_45_67_8.flac"""
    parts = filename.replace('.flac', '').split('_')
    if len(parts) != 5:
        return None, None, None
    class_code = parts[0]          # ví dụ: 'obj'
    event_id = parts[1]
    action = parts[2]
    material = parts[3]
    intensity = int(parts[4]) if parts[4].isdigit() else 0
    return class_code, intensity, event_id

def main(input_dir: str, output_dir: str):
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    
    normal_dir = output_path / "normal"
    abnormal_dir = output_path / "abnormal"
    
    normal_dir.mkdir(parents=True, exist_ok=True)
    abnormal_dir.mkdir(parents=True, exist_ok=True)
    
    flac_files = list(input_path.glob("*.flac"))
    logging.info(f"Tìm thấy {len(flac_files)} file .flac")
    
    stats = {"normal": 0, "abnormal": 0, "skipped": 0}
    
    for file in tqdm(flac_files, desc="Đang xử lý"):
        class_code, intensity, event_id = parse_filename(file.name)
        if not class_code:
            stats["skipped"] += 1
            continue
            
        # Quy tắc phân loại
        is_normal = False
        
        if class_code in {'wal', 'wat', 'swi'} and intensity <= 2:          # walking, water tap, switch nhẹ
            is_normal = True
        elif class_code in {'spe'} and intensity <= 1:                      # thì thầm
            is_normal = True
        elif class_code in {'obj', 'doo', 'fur'} and intensity >= 2:       # object falling, door, furniture mạnh
            is_normal = False
        elif class_code in {'obj', 'doo', 'fur', 'win', 'cup', 'dra'}:
            is_normal = False  # các sự kiện va chạm
        else:
            # Mặc định: intensity thấp = normal
            is_normal = (intensity <= 1)
        
        target_dir = normal_dir if is_normal else abnormal_dir
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Load và convert sang 16kHz mono
            y, sr = librosa.load(file, sr=16000, mono=True)
            
            # Tạo tên file mới dễ quản lý
            new_filename = f"{class_code}_{event_id}_int{intensity}.wav"
            output_file = target_dir / new_filename
            
            sf.write(output_file, y, 16000, subtype='PCM_16')
            
            if is_normal:
                stats["normal"] += 1
            else:
                stats["abnormal"] += 1
                
        except Exception as e:
            logging.error(f"Lỗi xử lý {file.name}: {e}")
            stats["skipped"] += 1
    
    # Thống kê
    print("\n" + "="*50)
    print("HOÀN THÀNH TÁCH DATASET")
    print("="*50)
    print(f"Normal      : {stats['normal']:4d} files")
    print(f"Abnormal    : {stats['abnormal']:4d} files")
    print(f"Skipped     : {stats['skipped']:4d} files")
    print(f"Thư mục output: {output_path.resolve()}")
    print("="*50)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tách Normal/Abnormal từ ReaLISED dataset")
    parser.add_argument("--input", "-i", required=True, help="Thư mục chứa các file .flac")
    parser.add_argument("--output", "-o", default="dataset_realised", help="Thư mục output")
    args = parser.parse_args()
    
    main(args.input, args.output)