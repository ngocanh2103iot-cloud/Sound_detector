import numpy as np

# --- Cấu hình tham số theo kế hoạch OCSVM ---
TARGET_SR = 16000
WINDOW_SIZE_SEC = 1.0
OVERLAP_PERCENT = 0.5  # 50% overlap → mỗi 500ms xuất 1 frame dự đoán

FRAME_LENGTH = int(TARGET_SR * WINDOW_SIZE_SEC)          # 16000 mẫu = 1 giây
HOP_LENGTH   = int(FRAME_LENGTH * (1.0 - OVERLAP_PERCENT))  # 8000 mẫu = 0.5 giây


def augment_audio(audio_frame, noise_level=0.005):
    """
    Áp dụng Random Gain [0.8, 1.2] và Gaussian Noise lên một khung âm thanh.
    Chỉ dùng cho tập TRAIN, không dùng cho val/test.
    """
    # 1. Random Gain
    gain = np.random.uniform(0.8, 1.2)
    audio_gained = audio_frame * gain

    # 2. Gaussian Noise (nhiễu trắng nhẹ)
    noise = np.random.randn(len(audio_gained))
    audio_noisy = audio_gained + (noise_level * noise)

    return audio_noisy


def process_audio(raw_audios, augment=False):
    """
    Windowing trên danh sách âm thanh đầu vào.

    Args:
        raw_audios (list[np.ndarray]): Danh sách các mảng audio float32.
        augment (bool): Nếu True, mỗi frame gốc sẽ được nhân đôi bằng 1
                        frame augmented. Chỉ đặt True cho tập TRAIN.

    Returns:
        np.ndarray: shape (N, FRAME_LENGTH) — N frame đã sẵn sàng cho MFCC.
    """
    frames = []

    for audio in raw_audios:
        # Bỏ qua file quá ngắn không đủ 1 frame
        if len(audio) < FRAME_LENGTH:
            continue

        for start in range(0, len(audio) - FRAME_LENGTH + 1, HOP_LENGTH):
            frame = audio[start : start + FRAME_LENGTH]
            frames.append(frame)

            if augment:
                frames.append(augment_audio(frame))

    # Trả về (0, FRAME_LENGTH) thay vì (0,) khi không có frame nào
    if not frames:
        return np.empty((0, FRAME_LENGTH), dtype=np.float32)

    return np.array(frames, dtype=np.float32)