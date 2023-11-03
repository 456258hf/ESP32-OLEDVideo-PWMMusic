"""将视频拆分为每一帧的图像"""
import os
import cv2
from config import ORIGINAL_VIDEO

if __name__ == '__main__':
    # 寻找视频文件
    if not os.path.exists(ORIGINAL_VIDEO):
        raise FileNotFoundError(
            f"Original video {ORIGINAL_VIDEO} not found, please check the settings in config.py")

    # 创建一个VideoCapture对象
    cap = cv2.VideoCapture(ORIGINAL_VIDEO)

    if not cap.isOpened():
        print(f"Unable to open the video file {ORIGINAL_VIDEO}")
    else:
        print(f"Using video {ORIGINAL_VIDEO} to generate frames")
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        # 从视频中提取的帧所存放的文件夹名
        original_frame_folder = f"OrigFrames-{frame_count-1:05d}p-{fps:02d}fps"
        if not os.path.exists(original_frame_folder):
            os.mkdir(original_frame_folder)
        for i in range(frame_count):
            print(
                f"\rGenerating frame{i:05d}/{(frame_count-1):05d}...", end='')
            ret, frame = cap.read()
            if ret:
                output_file = os.path.join(
                    original_frame_folder, f"frame{i:05d}.jpg")
                cv2.imwrite(output_file, frame)
            else:
                break
        print(
            f"\nGenerated! Check the frames in folder \\{original_frame_folder}\\ ")
    # 释放VideoCapture对象
    cap.release()
