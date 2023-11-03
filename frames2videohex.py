"""将视频每一帧的图像处理并合并为用于 ESP32 上显示的 hex 视频文件"""
import os
import hashlib
import PIL.ImageQt
from PIL import Image
from config import REVERSED_COLOR, SCREEN_WIDTH, SCREEN_HEIGHT, FRAME_STRETCH, PADDING_COLOR


def image_resize_no_stretch(image: Image) -> Image:
    """进行无拉伸的图像缩放"""
    # 获取图像尺寸
    image_width, image_height = image.size

    # 计算比例
    width_ratio = SCREEN_WIDTH / image_width
    height_ratio = SCREEN_HEIGHT / image_height

    # 计算适应后的尺寸
    if width_ratio < height_ratio:
        new_width = SCREEN_WIDTH
        new_height = int(image_height * width_ratio)
    else:
        new_width = int(image_width * height_ratio)
        new_height = SCREEN_HEIGHT

    # 创建一个空白画布
    canvas = Image.new("RGB", (SCREEN_WIDTH, SCREEN_HEIGHT), PADDING_COLOR)

    # 计算图像居中位置
    x_offset = (SCREEN_WIDTH - new_width) // 2
    y_offset = (SCREEN_HEIGHT - new_height) // 2

    # 将图像粘贴到画布上
    canvas.paste(image.resize((new_width, new_height),
                 Image.Resampling.LANCZOS), (x_offset, y_offset))

    return canvas


def image_binarization(image: Image) -> str:
    """将图像二值化为字符串"""
    pixels = image.getdata()
    image_str = ""
    for pixel in pixels:
        light_or_dark = 1 if pixel > 127 else 0
        image_str += str(light_or_dark ^ REVERSED_COLOR)
    return image_str


def image_transform(input_str: str) -> str:
    """对图像进行处理，使得可以直接写进 oled 显存"""
    output_list = [None] * SCREEN_WIDTH * SCREEN_HEIGHT
    for page in range(SCREEN_HEIGHT // 8):
        for column in range(SCREEN_WIDTH):
            for row in range(8):
                oldpos = 8*SCREEN_WIDTH*page + 8*column + row
                newpos = 8*SCREEN_WIDTH * \
                    (page+1) - SCREEN_WIDTH*(row+1) + column
                output_list[oldpos] = input_str[newpos]
    output_str = "".join(output_list)
    return output_str


if __name__ == '__main__':
    # 寻找视频图像文件夹
    entries = os.listdir()
    for entry in entries:
        if os.path.isdir(entry) and entry.startswith("OrigFrames-"):
            original_frame_folder = entry
            print(
                f"Converting frame folder \\{original_frame_folder}\\ to video hexfile")
            break
    else:
        raise FileNotFoundError(
            "Original frames folder \\OrigFrames-xxxxxp-xxfps\\ not found")

    # 从文件夹名中获取总帧数与fps：
    original_frame_folder_name = original_frame_folder.split('-')
    frame_count = int(original_frame_folder_name[1][:5])
    video_fps = int(original_frame_folder_name[2][:2])

    # 生成临时文件名称，若临时文件已存在则删除
    hexname = f"video-{frame_count:05d}p-{video_fps:02d}fps.hex"
    if os.path.exists(hexname):
        os.remove(hexname)
    # 创建空的临时文件：
    with open(hexname, "wb") as f:
        pass
    # 帧处理：
    for frame in os.listdir(original_frame_folder):
        print(f"\rConverting {frame[:10]}/{frame_count:05d}...", end='')
        # 打开图像：
        frame = PIL.Image.open(os.path.join(original_frame_folder, frame))
        # 调整图像大小：
        if FRAME_STRETCH:
            frame = frame.resize(
                (SCREEN_WIDTH, SCREEN_HEIGHT), Image.Resampling.LANCZOS)
        else:
            frame = image_resize_no_stretch(frame)
        # 灰度化图像：
        frame = frame.convert('L')
        # 将图像二值化为字符串：
        frame = image_binarization(frame)
        # 对图像进行处理，使得可以直接写进ssd1306缓存：
        frame = image_transform(frame)
        # 将字符串转换为bytes类型的对象：
        frame_bytes = int(frame, 2).to_bytes(
            SCREEN_WIDTH * SCREEN_HEIGHT//8, byteorder='big')
        # 在文件最后写入当前帧数据：
        with open(hexname, 'ab') as f:
            f.write(frame_bytes)
    # 将SHA256校验和前八位附在文件名中：
    with open(hexname, "rb") as f:
        hexfile = f.read()
        SHA256 = hashlib.sha256(hexfile).hexdigest()
    newhexname = f"video-{frame_count:05d}p-{video_fps:02d}fps-{SHA256[:8]}.hex"
    try:
        os.rename(hexname, newhexname)
        print(f"\nConverted! Check the hexfile {newhexname}")
    except FileExistsError as e:
        raise FileExistsError(
            f"\nHexfile {newhexname} with same content has already been generated") from e
