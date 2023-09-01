from ssd1306 import SSD1306_I2C
from machine import Pin, Timer
import machine
import os

machine.freq(240000000)

# 使用硬件I2C(1)，scl=25，sda=26
i2c = machine.I2C(1, freq=1200000)
oled = SSD1306_I2C(128, 64, i2c)

# 使用默认SD卡槽2，sck=18，miso=19，mosi=23，指定cs=4
sd = machine.SDCard(slot=2, cs=Pin(4))
os.mount(sd, "/sd")


def time1_irq(time1):
    global FrameCount, f, p
    f.seek(1024*FrameCount)  # 从当前帧指针位读取1kb图像数据
    data = f.read(1024)
    oled.buffer = data  # 直接写进帧缓存
    oled.show()
    FrameCount += 1  # 下一帧
    if (FrameCount == p):  # 如果所有帧播放完毕
        time1.deinit()


if __name__ == "__main__":
    FrameCount = 0  # 帧指针

    files = os.listdir("/sd")
    for file in files:
        if (file.startswith('video')):  # 匹配文件名
            fname = file
    try:
        p = int(fname.split('-')[1][:5])
    except:
        p = 1  # 未定义帧总数则仅播放一帧
    try:
        fps = int(fname.split('-')[2][:2])
    except:
        fps = 60  # 未定义fps则默认为60

    f = open(f'/sd/{fname}', 'rb')  # 打开文件

    time1 = Timer(1)  # 创建time1定时器对象：控制oled逐帧显示图像，形成视频
    time1.init(freq=fps, mode=Timer.PERIODIC, callback=time1_irq)
