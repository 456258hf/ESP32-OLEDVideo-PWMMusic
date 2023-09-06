ORIGINAL_VIDEO = "original.mp4"  # 视频源文件名

ORIGINAL_FRAME_FOLDER = "OrigFrames"  # 从视频中提取的帧所存放的文件夹名

REVERSED_COLOR = False  # 是否反色
SCREEN_WIDTH = 128  # 屏幕宽度
SCREEN_HEIGHT = 64  # 屏幕高度
FRAME_STRETCH = True  # True：拉伸图像至铺满屏幕 False：等比缩放，画面上下或左右留空
PADDING_COLOR = (255, 255, 255)  # 上个参数为False时，边缘所填颜色，(255, 255, 255)或(0, 0, 0)

OUTPUT_FPS = 60  # 输出视频的fps（仅命名视频文件以被esp32中代码读取并处理）
