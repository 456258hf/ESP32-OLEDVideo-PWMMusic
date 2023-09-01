import cv2
import os
from config import *

if not os.path.exists(ORIGINAL_VIDEO):
    Exception(
        f'Original video {ORIGINAL_VIDEO} not found, please check the settings in config.py')

# 创建一个VideoCapture对象
cap = cv2.VideoCapture(ORIGINAL_VIDEO)

if cap.isOpened():
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if not os.path.exists(ORIGINAL_FRAME_FOLDER):
        os.mkdir(ORIGINAL_FRAME_FOLDER)
    for i in range(frame_count):
        print(f'Generating frame{i:05d}/{(frame_count-1):05d}...')
        ret, frame = cap.read()
        if ret:
            output_file = os.path.join(
                ORIGINAL_FRAME_FOLDER, f"frame{i:05d}.jpg")
            cv2.imwrite(output_file, frame)
        else:
            break
    print(f'Generated! Check the frames in folder \{ORIGINAL_FRAME_FOLDER}\ ')
else:
    print("Unable to open the video file.")

# 释放VideoCapture对象
cap.release()
