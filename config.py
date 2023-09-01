ORIGINAL_VIDEO = "original.mp4"  # 视频源文件名

ORIGINAL_FRAME_FOLDER = "OrigFrames"  # 从视频中提取的帧所存放的文件夹名

REVERSED_COLOR = False  # 是否反色
RESIZE_HEIGHT = 64  # 输出视频在12864上显示的高度，若小于64则空缺的高度为空白
RESIZE_WIDTH = 128  # 输出视频在12864上显示的宽度，若小于128则空缺的宽度为空白
OUTPUT_FPS = 60  # 输出视频的fps（仅命名视频文件以被esp32中代码读取并处理）
