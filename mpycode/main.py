from ssd1306 import SSD1306_I2C
from machine import Pin, Timer
from musicscore import MUSIC
import machine
import os

machine.freq(240000000)

# 使用硬件I2C(1)，scl=25，sda=26
i2c = machine.I2C(1, freq=1200000)
oled = SSD1306_I2C(128, 64, i2c)

# 使用默认SD卡槽2，sck=18，miso=19，mosi=23，指定cs=4
sd = machine.SDCard(slot=2, cs=Pin(4))
os.mount(sd, "/sd")

BEEP_PIN = 33  # 设定蜂鸣器引脚
BPM = 138  # 设定播放BPM

SPEEDMS = (60000/BPM)/16-1.5  # 计算16音符时值，-1.5以避免音符间隔较短时产生的延迟


def time0_irq(time0):
    global MusicCount
    MusicFreq = MUSIC[MusicCount][0]  # 选择音符对应的频率
    beep = machine.PWM(Pin(BEEP_PIN))  # 每次初始化PWM，防止无法去初始化
    if (MusicFreq):
        beep.freq(int(440*2**((MusicFreq-10)/12)))  # 十二平均律计算频率，以A4=440Hz为基准
    else:
        beep.deinit()  # 休止符
    time0.init(period=int(  # 设定下一个音的延时
        (SPEEDMS * MUSIC[MusicCount][1])), mode=Timer.ONE_SHOT, callback=time0_irq)
    MusicCount += 1  # 下一个音
    if (MUSIC[MusicCount][0] == 255):  # 如果下一个音是终止标志位，关闭PWM与定时器
        time0.deinit()
        beep.deinit


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
    MusicCount = 0  # 音符指针
    FrameCount = 0  # 帧指针

    files = os.listdir("/sd")
    for file in files:
        if (file.startswith('video')):  # 匹配文件名
            fname = file
    try:
        p = int(fname.split('-')[1][:5])  # 读取文件名中帧总数
    except:
        p = 1  # 未定义帧总数则仅播放一帧
    try:
        fps = int(fname.split('-')[2][:2])  # 读取文件名中fps
    except:
        fps = 30  # 未定义fps则默认为30

    f = open(f'/sd/{fname}', 'rb')  # 打开文件

    time0 = Timer(0)  # 创建time0定时器对象：控制蜂鸣器发声
    time0.init(period=1, mode=Timer.ONE_SHOT, callback=time0_irq)
    time1 = Timer(1)  # 创建time1定时器对象：控制oled逐帧显示图像，形成视频
    time1.init(freq=fps, mode=Timer.PERIODIC, callback=time1_irq)
