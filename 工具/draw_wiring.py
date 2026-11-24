# -*- coding: utf-8 -*-
"""生成「接线总表」一页图（重建用），A4 竖版 1240x1754。"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1240, 1754
NAVY = (31, 56, 100)
BLUE = (46, 92, 138)
LIGHT = (238, 243, 249)
LINE = (200, 210, 222)
RED = (176, 42, 42)
GREEN = (46, 110, 62)
GRAY = (90, 90, 90)
DARK = (30, 30, 30)

F = r"C:\Windows\Fonts\msyh.ttc"
FB = r"C:\Windows\Fonts\msyhbd.ttc"
_fc = {}


def font(size, bold=False):
    key = (size, bold)
    if key not in _fc:
        _fc[key] = ImageFont.truetype(FB if bold else F, size)
    return _fc[key]


img = Image.new("RGB", (W, H), "white")
d = ImageDraw.Draw(img)
M = 46  # 页边距


def txt(x, y, s, size=20, bold=False, color=DARK):
    d.text((x, y), s, font=font(size, bold), fill=color)


def tw(s, size=20, bold=False):
    return d.textlength(s, font=font(size, bold))


def section(y, title, note=None):
    d.rectangle([M, y, M + 6, y + 30], fill=BLUE)
    txt(M + 16, y + 1, title, 25, True, NAVY)
    if note:
        txt(M + 16 + tw(title, 25, True) + 16, y + 8, note, 18, False, GRAY)
    y += 34
    d.line([M, y, W - M, y], fill=LINE, width=1)
    return y + 8


def table(y, rows, cols=(3,), widths=None, x0=M, total=None, header=None, rowh=33):
    total = total or (W - 2 * M)
    if widths is None:
        widths = [1.0 / len(cols)] * len(cols)
    xs = [x0]
    for w in widths:
        xs.append(xs[-1] + total * w)
    yy = y
    if header:
        d.rectangle([xs[0], yy, xs[-1], yy + rowh], fill=(216, 228, 242))
        for i, h in enumerate(header):
            txt(xs[i] + 12, yy + 8, h, 19, True, NAVY)
        yy += rowh
    for r in rows:
        hh = rowh
        # 自动加高：任何一格超过列宽就换行（简单两行处理）
        over = False
        for i, c in enumerate(r):
            if tw(c, 19) > xs[i + 1] - xs[i] - 24:
                over = True
        if over:
            hh = rowh + 30
        d.rectangle([xs[0], yy, xs[-1], yy + hh], outline=LINE, width=1)
        for i, c in enumerate(r):
            col = DARK
            if i == 1:
                col = RED
            if str(c).startswith("说明"):
                col = GRAY
            txt(xs[i] + 12, yy + 8, c, 19, i == 0, col)
        yy += hh
    for x in xs[1:-1]:
        d.line([x, y, x, yy], fill=LINE, width=1)
    return yy + 14


# ── 标题 ───────────────────────────────────────────────
txt(M, 34, "电控组第三次作业 · 接线总表", 40, True, NAVY)
txt(M, 88, "3 颗 LED + 2 个按键 + 串口 + OLED（软件 I²C / 硬件 I²C 两版）· STM32F103C8T6", 21, False, GRAY)
d.line([M, 126, W - M, 126], fill=NAVY, width=3)
y = 142

# ── 一、板子引脚位置 ────────────────────────────────────
y = section(y, "一、先认清板子两侧的引脚（USB 朝上）", "红框＝本作业要用")
LEFT = ["VBAT", "C13", "C14", "C15", "A0", "A1", "A2", "A3", "A4", "A5",
        "A6", "A7", "B0", "B1", "B10", "B11", "R", "3.3", "GND", "GND"]
RIGHT = ["3.3", "GND", "5V", "B9", "B8", "B7", "B6", "B5", "B4", "B3",
         "A15", "A12", "A11", "A10", "A9", "A8", "B15", "B14", "B13", "B12"]
USE_L = {"A0", "A1", "A2", "B1", "B0", "3.3", "GND"}
USE_R = {"3.3", "GND", "B7", "B6", "A12", "A11", "A10", "A9"}

bw, bh, gap = 52, 30, 3


def strip(y, labels, used, tag):
    txt(M, y + 4, tag, 19, True, BLUE)
    x = M + 66
    for i, p in enumerate(labels):
        on = p in used
        d.rectangle([x, y, x + bw, y + bh], fill=(255, 235, 235) if on else (247, 249, 252),
                    outline=RED if on else LINE, width=2 if on else 1)
        col = RED if on else GRAY
        f = font(15, True) if on else font(15)
        wpx = d.textlength(p, font=f)
        d.text((x + (bw - wpx) / 2, y + 6), p, font=f, fill=col)
        x += bw + gap
    return y + bh + 8


y = strip(y, LEFT, USE_L, "左列")
txt(M + 66, y, "（从上往下：VBAT → C13 → … → GND）", 16, False, GRAY)
y += 22
y = strip(y, RIGHT, USE_R, "右列")
txt(M + 66, y, "（从上往下：3.3 → GND → 5V → … → B12）", 16, False, GRAY)
y += 34

# ── 二、电源与下载器 ───────────────────────────────────
y = section(y, "二、供电 + ST-Link（4 根线）")
y = table(y, [
    ("ST-Link 3.3", "板子 3.3", "给板子供电；也可以用 Micro-USB 供电，二选一"),
    ("ST-Link GND", "板子 GND", "必须接"),
    ("ST-Link SWDIO", "板子 DIO", "下载/调试数据"),
    ("ST-Link SWCLK", "板子 CLK", "下载/调试时钟"),
], widths=[0.30, 0.20, 0.50])
y = table(y, [
    ("板子 3.3", "面包板红色（+）轨", "所有模块的 3.3V 都从这条轨取"),
    ("板子 GND", "面包板蓝色（−）轨", "所有模块的 GND 都从这条轨取"),
], widths=[0.24, 0.26, 0.50])
txt(M, y - 6, "说明：ST-Link 的 3.3V 和板子的 Micro-USB 不要同时接，板子只从一个地方取电。", 18, False, RED)
y += 22

# ── 三、LED ────────────────────────────────────────────
y = section(y, "三、3 颗 LED（PA0 / PA1 / PA2，同一时刻只亮一颗）")
y = table(y, [
    ("PA0", "330Ω → LED1 长脚", "LED1 短脚 → GND 轨"),
    ("PA1", "330Ω → LED2 长脚", "LED2 短脚 → GND 轨"),
    ("PA2", "330Ω → LED3 长脚", "LED3 短脚 → GND 轨"),
], widths=[0.16, 0.42, 0.42], header=["引脚", "中间串电阻", "回到哪里"])
txt(M, y - 6, "说明：长脚（正极）朝 GPIO，短脚朝 GND；每颗灯独占一列（A~E 五个孔为一组），两颗插同一组就会一起亮。", 18, False, GRAY)
y += 22

# ── 四、按键 ───────────────────────────────────────────
y = section(y, "四、2 个按键（PA11 = 换向，PA12 = 暂停/继续）")
y = table(y, [
    ("PA11", "KEY1 一端", "KEY1 另一端 → GND 轨"),
    ("PA12", "KEY2 一端", "KEY2 另一端 → GND 轨"),
], widths=[0.16, 0.42, 0.42], header=["引脚", "接到", "另一端"])
txt(M, y - 6, "说明：芯片内部上拉，不用外加电阻；4 脚按键只用对角两只脚，同侧两脚内部常通，接错等于一直按住。", 18, False, GRAY)
y += 22

# ── 五、串口 ───────────────────────────────────────────
y = section(y, "五、USB 转 TTL（3 根线，模块要 3.3V 电平）")
y = table(y, [
    ("PA9（TX）", "模块 RX", "板子发 → 模块收"),
    ("PA10（RX）", "模块 TX", "模块发 → 板子收，TX/RX 必须交叉"),
    ("板子 GND", "模块 GND", "必须共地，否则乱码或收不到"),
], widths=[0.24, 0.26, 0.50], header=["引脚", "接到", "说明"])
txt(M, y - 6, "说明：模块 VCC 不用接（板子自己供电）；模块必须是 3.3V 电平，5V 会打坏 PA10。", 18, False, GRAY)
y += 22

# ── 六、OLED ───────────────────────────────────────────
y = section(y, "六、OLED（4 针，VCC 一定接 3.3V）", "两版选一，看你做不做选做")
half = (W - 2 * M - 20) // 2
txt(M, y, "基础版 · 软件 I²C", 20, True, BLUE)
txt(M + half + 20, y, "选做版 · 硬件 I²C", 20, True, BLUE)
y += 28
y1 = table(y, [
    ("VCC", "3.3V 轨", "别接 5V"),
    ("GND", "GND 轨", ""),
    ("SCL", "PB1", "左列丝印 B1"),
    ("SDA", "PB0", "左列丝印 B0"),
], widths=[0.28, 0.34, 0.38], x0=M, total=half, header=["针脚", "接到", "备注"])
y2 = table(y, [
    ("VCC", "3.3V 轨", "别接 5V"),
    ("GND", "GND 轨", ""),
    ("SCL", "PB6", "右列丝印 B6"),
    ("SDA", "PB7", "右列丝印 B7"),
], widths=[0.28, 0.34, 0.38], x0=M + half + 20, total=half, header=["针脚", "接到", "备注"])
y = max(y1, y2)
txt(M, y - 6, "说明：模块一般自带 4.7k 上拉，没有的话 SCL/SDA 各接一个 4.7k 到 3.3V；两版不能同时接。", 18, False, GRAY)
y += 22

# ── 七、上电前检查 ─────────────────────────────────────
y = section(y, "七、上电前 8 条（万用表通断档，断电测）")
checks = [
    ("1", "3.3V 与 GND 之间不短路", "2", "OLED 接 3.3V 不是 5V"),
    ("3", "LED 长脚朝 GPIO、短脚朝 GND", "4", "按键一端 GPIO、一端 GND"),
    ("5", "串口 TX/RX 已交叉", "6", "USB-TTL 与板子共地"),
    ("7", "PB0/PB1（或 PB6/PB7）没被占用", "8", "板子只从一个地方取电"),
]
cw = (W - 2 * M) // 2
for n1, t1, n2, t2 in checks:
    txt(M + 4, y, n1 + ".", 19, True, BLUE)
    txt(M + 34, y, t1, 19)
    txt(M + cw + 4, y, n2 + ".", 19, True, BLUE)
    txt(M + cw + 34, y, t2, 19)
    y += 32

y += 6
d.line([M, y, W - M, y], fill=LINE, width=1)
y += 12
txt(M, y, "接完先做三件事：万用表量 3.3V 与 GND 不短路 → 上电看板子电源灯 → 串口助手看有没有 COM 口。", 19, True, NAVY)
y += 34
txt(M, y, "编译烧录：工具\\build.ps1  再  工具\\flash.ps1（需先装好 ST-Link 驱动）", 18, False, GRAY)

img.save(r"C:\Users\Furina\Documents\deepseek-harness\default-workspace\diankong3\工具\接线总表.png", quality=95)
print("ok", img.size, "last y =", y)
