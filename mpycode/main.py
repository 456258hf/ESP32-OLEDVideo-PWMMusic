from ssd1306 import SSD1306_I2C
from machine import Pin, Timer
import machine
import os

try:
    from musicscore import MUSIC
except ImportError:
    HasMusic = False
else:
    HasMusic = True

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
    try:
        Note = next(Music)
    except StopIteration:
        time0.deinit()
        beep.deinit()
        return
    if Note[0]:
        # 十二平均律计算频率，以A4=440Hz为基准
        beep.duty(512)
        beep.freq(int(440*2**((Note[0]-10)/12)))
    else:
        beep.duty(0)
    time0.init(period=int(  # 设定下一个音的延时
        (SPEEDMS * Note[1])), mode=Timer.ONE_SHOT, callback=time0_irq)


def time1_irq(time1):
    global FrameCount
    oled.buffer = f.read(1024)  # 读取1kb图像数据，直接写进帧缓存
    oled.show()
    FrameCount += 1  # 帧计数+1
    if (FrameCount == FrameNum):  # 如果所有帧播放完毕
        time1.deinit()
        f.close()


if __name__ == "__main__":
    MusicCount = 0  # 音符指针
    FrameCount = 0  # 帧指针

    files = os.listdir("/sd")
    for file in files:
        if (file.startswith('video')):  # 匹配文件名
            fname = file

    f = open(f'/sd/{fname}', 'rb')  # 打开文件

    # 从文件名中获取视频信息
    fname = fname.split('-')
    try:
        FrameNum = int(fname[1][:5])  # 读取文件名中帧总数
    except:
        FrameNum = 1  # 未定义帧总数则仅播放一帧
    try:
        Fps = int(fname[2][:2])  # 读取文件名中fps
    except:
        Fps = 30  # 未定义fps则默认为30

    # 如果有音乐，则初始化相关内容
    if HasMusic:
        Music = iter(MUSIC)  # 创建乐谱迭代器
        beep = machine.PWM(Pin(BEEP_PIN))  # 定义蜂鸣器对象
        time0 = Timer(0)  # 创建time0定时器对象：控制蜂鸣器发声
        time0.init(period=100, mode=Timer.ONE_SHOT, callback=time0_irq)

    # 视频定时器初始化
    time1 = Timer(1)  # 创建time1定时器对象：控制oled逐帧显示图像，形成视频
    time1.init(freq=Fps, mode=Timer.PERIODIC, callback=time1_irq)
