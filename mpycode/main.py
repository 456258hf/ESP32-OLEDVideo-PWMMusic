from ssd1306 import SSD1306_I2C, SSD1306_SPI
from sh1106 import SH1106_I2C, SH1106_SPI
from machine import Pin, Timer, I2S
import machine
import os

machine.freq(240000000)

# SSD1306_I2C 使用硬件I2C(1)，scl=25，sda=26
i2c = machine.I2C(1, freq=1200000)
oled = SSD1306_I2C(128, 64, i2c)

# SSD1306_SPI 使用硬件SPI(1)，sck=16，mosi=17，dc=22，res=5，cs=21
# spi = machine.SPI(1, baudrate=40000000,  sck=Pin(16), mosi=Pin(17), miso=None)
# oled = SSD1306_SPI(128, 64, spi, dc=Pin(22), res=Pin(5), cs=Pin(21))

# SH1106_I2C 使用硬件I2C(1)，scl=25，sda=26
# i2c = machine.I2C(1, freq=1200000)
# oled = SH1106_I2C(128, 64, i2c)

# SH1106_SPI 使用硬件SPI(1)，sck=16，mosi=17，dc=22，res=5，cs=21
# spi = machine.SPI(1, baudrate=40000000,  sck=Pin(16), mosi=Pin(17), miso=None)
# oled = SH1106_SPI(128, 64, spi, dc=Pin(22), res=Pin(5), cs=Pin(21))

# 使用默认SD卡槽2，sck=18，miso=19，mosi=23，指定cs=4
sd = machine.SDCard(slot=2, cs=Pin(4))

# 定义I2S模块连接引脚，使用I2S(1), sck=32, sd=33, 指定ws=27
SCK_PIN = 32
WS_PIN = 27
SD_PIN = 33

WAV_FILE = "audio.wav"  # 音频文件名
CONJ = 3  # 每CONJ帧传输一次相应长度音频到I2S，避免频繁传输导致卡顿，默认为3

# 设定蜂鸣器播放参数
BEEP_PIN = 15  # 设定蜂鸣器引脚
BPM = 138  # 设定播放BPM

SPEEDMS = (60000/BPM)/16-1  # 计算16音符时值（ms），-1以避免音符间隔较短时产生的延迟


def time0_irq(time0):
    try:
        Note = next(Music)
    except StopIteration:
        print("end of audio file")
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


def tim1_irq(timer1):
    if MusicType == 2:
        global Flag
        Flag += 1
        if Flag == CONJ:
            i2s_play()
            Flag = 0

    try:
        if type(oled) == SSD1306_I2C or type(oled) == SSD1306_SPI:
            VideoRead = VideoFile.readinto(oled.buffer)  # 读取一帧数据到显存
        elif type(oled) == SH1106_I2C or type(oled) == SH1106_SPI:
            VideoRead = VideoFile.readinto(oled.renderbuf)  # 读取一帧数据到显存
    except OSError:  # VideoRead == 0 后，关闭定时器所需时间较长，可能导致此错误
        print("maybe end of video file")
        VideoFile.close()
        tim1.deinit()
        return
    if VideoRead == 0:
        print("end of video file")
        VideoFile.close()
        tim1.deinit()
    else:
        if type(oled) == SSD1306_I2C or type(oled) == SSD1306_SPI:
            oled.show()  # 显示图像
        elif type(oled) == SH1106_I2C or type(oled) == SH1106_SPI:
            oled.show(full_update=True)  # 显示图像


def i2s_play():  # 进行I2S传输
    AudioRead = AudioFile.readinto(AudioBufMV)  # 读取一定长度音频数据到内存
    if AudioRead == 0:
        print("end of audio file")
        AudioFile.close()
        audio_out.deinit()
    else:
        _ = audio_out.write(AudioBufMV)  # 推送音频


def i2s_callback(arg):  # I2S缓存清空时的回调函数
    pass


if __name__ == "__main__":
    Flag = CONJ - 1  # 标记

    try:
        os.mount(sd, "/sd")
        path = "/sd"
    except OSError:
        print("SD card is not inserted or is damaged, trying to find files from the internal file system")
        path = ""

    # 寻找视频文件
    files = os.listdir(path)
    for file in files:
        if file.startswith("video-"):
            VideoFileName = file
            print(f"Using video hexfile {VideoFileName} to play")
            break
    else:
        raise Exception(
            "Video hexfile video-xxxxxp-xxfps-xxxxxxxx.hex not found")

    # 打开视频文件
    VideoFile = open(f"{path}/{VideoFileName}", 'rb')  # 打开文件

    # 从视频文件名中获取视频信息
    VideoFileName = VideoFileName.split('-')
    try:
        Fps = int(VideoFileName[2][:2])  # 读取文件名中fps
    except:
        Fps = 30  # 未定义fps或获取失败则默认为30

    # 打开音频文件
    try:
        AudioFile = open(f"{path}/{WAV_FILE}", 'rb')
        MusicType = 2
    except OSError:
        try:
            from musicscore import MUSIC
            MusicType = 1
        except ImportError:
            MusicType = 0

    # 如果有音乐，则初始化相关内容
    if MusicType == 2:
        print(f"Using {WAV_FILE} to play music")
        # 从wav文件头读取音频信息
        AudioHeader = AudioFile.read(44)

        # I2S初始化
        audio_out = I2S(
            1,  # i2s通道
            sck=Pin(SCK_PIN),
            ws=Pin(WS_PIN),
            sd=Pin(SD_PIN),
            mode=I2S.TX,
            bits=int.from_bytes(AudioHeader[34:35], 'little'),  # 音频位深度
            format=int.from_bytes(
                AudioHeader[22:23], 'little') - 1,  # 0为单声道，1为双声道
            rate=int.from_bytes(AudioHeader[24:28], 'little'),  # 音频采样率
            ibuf=40000,  # i2s内部缓存大小
        )
        audio_out.irq(i2s_callback)  # 配置一个并没有什么用的回调函数

        # 划分音频缓存空间
        AudioFrameLen = int(int.from_bytes(
            AudioHeader[28:32], 'little') / Fps)  # 视频每帧时间内对应的音频的字节数
        AudioBuf = bytearray(AudioFrameLen * CONJ)
        AudioBufMV = memoryview(AudioBuf)
    # 如果有乐谱，则初始化相关内容
    elif MusicType == 1:
        print("Using musicscore.py to play music")
        Music = iter(MUSIC)  # 创建乐谱迭代器
        beep = machine.PWM(Pin(BEEP_PIN))  # 定义蜂鸣器对象
        time0 = Timer(0)  # 创建tim0定时器对象：控制蜂鸣器发声
        time0.init(period=100, mode=Timer.ONE_SHOT, callback=time0_irq)
    # 音乐和乐谱都不存在
    else:
        print(
            f"Neither {WAV_FILE} nor musicscore.py exists, no music will be played")

    # 主定时器初始化
    tim1 = Timer(1)  # 创建tim1定时器对象，播放视频
    tim1.init(freq=Fps, mode=Timer.PERIODIC, callback=tim1_irq)
