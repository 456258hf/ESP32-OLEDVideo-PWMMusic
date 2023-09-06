import PIL.ImageQt
import os
import hashlib
from config import *
from PIL import Image


def ImageResizeNoStretch(image: Image) -> Image:
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


def Binarization2String(image: Image) -> str:  # 将图像二值化为字符串
    pixels = image.getdata()
    image_str = ""
    for pixel in pixels:
        light_or_dark = 1 if pixel > 127 else 0
        image_str += str(light_or_dark ^ REVERSED_COLOR)
    return image_str


def Transform(input_str: str) -> str:  # 对图像进行处理，使得可以直接写进ssd1306显存
    output_list = [None] * 8192
    for o in range(8):
        for m in range(128):
            for n in range(8):
                j = 1024*o + 8*m + n
                i = 1024*(o+1) - 128*(n+1) + m
                output_list[j] = input_str[i]
    output_str = "".join(output_list)
    return output_str


if __name__ == '__main__':
    if not os.path.exists(ORIGINAL_FRAME_FOLDER):
        Exception(
            f'Original frames folder \{ORIGINAL_FRAME_FOLDER}\ not found, please check the settings in config.py')
    else:
        # 统计原始图像数量：
        count = len(os.listdir(ORIGINAL_FRAME_FOLDER))
        # 生成临时文件名称，若临时文件已存在则删除
        hexname = f'video-{count:05d}p-{OUTPUT_FPS:02d}fps.hex'
        if os.path.exists(hexname):
            os.remove(hexname)
        # 创建空的临时文件：
        with open(hexname, "w") as f:
            pass
        # 帧处理：
        for frame in os.listdir(ORIGINAL_FRAME_FOLDER):
            print(f'Converting {frame[:10]}/{count:05d}...')
            # 打开图像：
            frame = PIL.Image.open(os.path.join(ORIGINAL_FRAME_FOLDER, frame))
            # 调整图像大小：
            if FRAME_STRETCH:
                frame_r = frame.resize(
                    (SCREEN_WIDTH, SCREEN_HEIGHT), Image.Resampling.LANCZOS)
            else:
                frame_r = ImageResizeNoStretch(frame)
            # 灰度化图像：
            frame_rc = frame_r.convert("L")
            # 将图像二值化为字符串：
            frame_str = Binarization2String(frame_rc)
            # 对图像进行处理，使得可以直接写进ssd1306缓存：
            frame_strt = Transform(frame_str)
            # 将字符串转换为bytes类型的对象：
            frame_bytes = int(frame_strt, 2).to_bytes(1024, byteorder='big')
            # 在文件最后写入当前帧数据：
            with open(hexname, 'ab') as f:
                f.write(frame_bytes)
        # 将SHA256校验和前八位附在文件名中：
        with open(hexname, "rb") as f:
            bytes = f.read()
            hash = hashlib.sha256(bytes).hexdigest()
        newhexname = f'video-{count:05d}p-{OUTPUT_FPS:02d}fps-{hash[:8]}.hex'
        try:
            os.rename(hexname, newhexname)
            print(f'Converted! Check the hexfile {newhexname}')
        except FileExistsError:
            print(
                f"Hexfile {newhexname} with same content has already been generated")
