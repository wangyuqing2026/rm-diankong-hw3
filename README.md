# 电控组第三次培训作业

姓名：王语清
学号：20263001319
组别：电控组

板子 STM32F103C8T6（72 MHz，64 KB Flash / 20 KB RAM），CubeMX 配引脚，CLion + arm-none-eabi-gcc 13.3.1 编译。

## 做了什么

基础要求四项都做完了，两个选做也做了。

- 流水灯：3 颗 LED（PA0~PA2），同一时刻只亮一颗，间隔 100~2000 ms 可调
- 按键：PA11 切方向、PA12 暂停/继续，外部中断 + 20 ms 消抖，按住只算一次
- 串口收包：6 字节数据包，中断收字节，主循环找帧头、校验、应用
- OLED：四行显示 STATE / DIR / STEP / LED，内容变了才重画
- 串口反馈：状态一变就回一行文本
- 选做：DMA 发送和硬件 I²C 都做了，OLED 走 I2C1（PB6/PB7，400 kHz）

## 接线

| 功能 | 引脚 | 接到 |
| --- | --- | --- |
| LED1~LED3 | PA0 / PA1 / PA2 | LED 正极（串 330 Ω），负极接 GND |
| KEY1 方向 | PA11 | 按键一脚，另一脚接 GND（内部上拉） |
| KEY2 暂停 | PA12 | 同上 |
| USART1 TX / RX | PA9 / PA10 | USB 转 TTL 的 RX / TX，要共地 |
| OLED SCL / SDA | PB6 / PB7 | 硬件 I²C1，复用开漏 |

串口 115200 8N1。LED 高电平点亮。PA3 空着，接第 4 颗时把 `LED_NUM` 改成 4。

## 数据包和反馈

下行 6 字节：

```
AA  RUN  DIR  STEP_L  STEP_H  CHECK
```

RUN 是 00 暂停 / 01 运行，DIR 是 00 正向 / 01 反向，STEP 是毫秒数、100~2000、小端（先低字节），CHECK = (AA+RUN+DIR+STEP_L+STEP_H) % 256。比如运行正向 300 ms 是 `AA 01 00 2C 01 D8`。

帧头不对、校验不对、RUN/DIR 不是 0/1、间隔超范围，都整包丢掉，状态不变。

上行是文本（GBK）：

```
STATE=RUN,DIR=FWD,STEP=300,LED=1
```

STATE 是 RUN/PAUSE，DIR 是 FWD/REV，STEP 是当前间隔，LED 是当前亮的编号。上电发一次，数据包生效后发一次，按键改状态或方向后发一次。

## 程序结构

主循环里五个任务，每个都只做一小步就返回：

```c
while (1) {
    App_LoopOnce();   // 按键、收包、换灯、刷屏、补发反馈
}
```

中断里只记录事件：EXTI 回调记"哪个键、什么时候"，串口接收回调把 1 个字节塞进 64 字节环形缓冲再开下一次接收，发送完成回调清忙标志。解析、校验、改状态、刷屏都在主循环里做。

## 几个实现上的点

**流水灯不用 HAL_Delay**。记下上次换灯的时刻，每轮比一次 `HAL_GetTick() - tick >= step_ms`，到点才换。这样不管间隔设成多少，按键和串口都能马上响应，这也是思考题问的东西。

**按键消抖**。EXTI 只记边沿时刻，主循环看到"距最后一个边沿超过 20 ms 且引脚还是低"才算按下，另外用一个 `locked` 标志要求先松手，所以按住不放只触发一次。

**收包用状态机**。回调每次收 1 字节，主循环先找 `AA`，再攒够 6 字节交给校验函数。前面混了杂字节也能自己重新对齐。

**结构体固定 6 字节**。`CmdPacket_t` 加了 `__attribute__((packed))`，再用 `_Static_assert(sizeof(CmdPacket_t) == 6)` 在编译期卡住，省得对齐填充把长度变成 7。

**串口断了能自己恢复**。HAL 遇到溢出（ORE）会停掉接收中断，只写接收回调的话，现象是"收几次就再也不理你"。所以补了 `HAL_UART_ErrorCallback`，清标志后重新 `HAL_UART_Receive_IT`。

**OLED 只在变化时重画**。四行文本各存一份，`strcmp` 不一样才写屏，写之前把不足 16 列的部分补上空格，既不会闪，也不会每次切灯都整屏刷一遍。

## 编译和下载

```
工具\build.ps1     # 编译，产物 firmware/build/diankong3.hex
工具\flash.ps1     # ST-Link + OpenOCD 下载并复位
```

CLion 打开 `firmware` 目录，CMake 参数填 `-DCMAKE_TOOLCHAIN_FILE=cmake/gcc-arm-none-eabi.cmake`。

现在固件占用 text 19 532 B、data 156 B、bss 2 348 B（Flash 约 30%，RAM 约 12%）。

## 测试

| # | 操作 | 现象 |
| --- | --- | --- |
| 1 | 上电 | LED1 亮，OLED 显示 RUN/FWD/0300/LED:1，串口收到一行 STATE=RUN... |
| 2 | 等一会儿 | 灯按 300 ms 依次 1→2→3→1 |
| 3 | 按 KEY1 | 变成 3→2→1→3 反向走，OLED 和串口都跟着变 |
| 4 | 按 KEY2 | 停在当前那颗，OLED 显示 PAUSE |
| 5 | 暂停时发 `AA 01 00 E8 03 95` | 仍暂停，间隔变 1000，恢复后按 1000 ms 走 |
| 6 | 发 `AA 01 01 2C 01 D9` | 运行、反向、300 ms 同时生效 |
| 7 | 发 `AA 01 00 2C 01 D9`（校验错） | 没反应，也不报错 |
| 8 | 发 `AA 01 00 32 00 DD`（50 ms） | 越界，整包丢掉 |
| 9 | 长按 KEY1 | 只翻一次 |
| 10 | 连点 KEY2 | 次次生效，没丢 |
| 11 | 2000 ms 时按 KEY2 | 立刻暂停，没有两秒延迟 |
| 12 | 先发一个杂字节再发正确包 | 能重新对齐并执行 |

1~12 的行为先在 `sim/` 里用 PC 编译跑过（35 条断言全过），再上板复测。

改 `LED_NUM` 之后要跟着改测试里的假设：一轮的步数是 `LED_NUM`，不是写死的 4。

## 选做

### DMA 发送

反馈从 `HAL_UART_Transmit_IT` 换成 `HAL_UART_Transmit_DMA`，数据由 DMA1_Channel4 搬进 `USART1->DR`。

改了四个地方：`usart.c` 加 `hdma_usart1_tx` 和 `MX_DMA_Init()`（开 DMA1 时钟）；`stm32f1xx_hal_msp.c` 里配通道（Memory→Peripheral、MINC、Byte/Byte、Normal、低优先级）并 `__HAL_LINKDMA`；`stm32f1xx_it.c` 加 `DMA1_Channel4_IRQHandler`；`main.c` 把 `MX_DMA_Init()` 放到串口初始化前面，发送改调 DMA 版。

用 Normal 不用 Circular，因为一包反馈发完就该停，Circular 会自己从头再搬一遍，把旧数据重复发出去。DMA 传输完成中断也必须开，收尾（清忙标志、调回调）在中断里做，少了这个入口就是"第一包发出去了，之后再也不发"。

验证没上示波器：连发 5 个不同状态的包，收到 5 行且顺序对；再用 ST-Link 读 DMA1_Channel4，`CPAR=0x40013804`（就是 USART1->DR）、`CMAR=0x20000114`（`s_fb_buf` 的地址）、`CNDTR=0`（搬完了），说明字节确实是 DMA 搬的。一包 34 字节，中断方式 CPU 要进 34 次，DMA 只进 1 次。

### 硬件 I²C

OLED 不再用 GPIO 逐位翻转，改由 I2C1 产生时序，PB6 = SCL、PB7 = SDA，两脚复用开漏，400 kHz。

`i2c.c` 是新加的：`MX_I2C1_Init()` 配 400 kHz、7 位地址，`HAL_I2C_MspInit()` 把 PB6/PB7 设成 `GPIO_MODE_AF_OD`。`OLED.c` 里删掉了 `OLED_I2C_Start/Stop/SendByte` 三个位翻转函数，`OLED_WriteCommand/WriteData` 改成一条 `HAL_I2C_Master_Transmit(&hi2c1, 0x78, buf, 2, 100)`，`buf` 是 {控制字, 数据}。CMake 源文件列表加了 `Core/Src/i2c.c`。对外接口一个没动，`main.c` 只改了注释。

地址写 0x78 是因为 SSD1306 的 7 位地址是 0x3C，HAL 要的是左移一位后的 8 位地址。控制字 0x00 表示后面跟命令、0x40 表示跟显存数据。

用 400 kHz 不用 100 kHz：这里每个字节算一条完整事务（起始 + 地址 + 控制字 + 数据 + 停止，约 30 bit），100 kHz 一条要 300 µs 左右，整屏 1024 字节差不多 300 ms，主循环会被彻底卡住；400 kHz 一条约 75 µs，整屏约 77 ms。实际只在内容变化时重画一行（32 字节，约 2.6 ms），基本感觉不到。

验证也是读寄存器：`I2C1_CR2=0x24`（FREQ=36，PCLK1 36 MHz）、`I2C1_CCR=0x801E`（F/S=1，CCR=30，36 MHz/(30×3)=400 kHz）、`I2C1_TRISE=0x0B`、`GPIOB_CRL` 里 PB6/PB7 是 `0xF`（复用开漏）；`SR1`、`SR2` 都是 0，没有 AF（从机不应答）也没有 BERR，说明屏在正常应答。

## 踩过的坑

调试时卡住的三个问题，记一下。

1. 串口发出去的数据原样回来了。原因是 TX 和 RX 两个头子插在面包板同一排，那一排内部是通的。挪一排就好了。
2. OLED 不亮，供电、引脚、地址都查过没问题，最后是 SCL 和 SDA 接反了。模块丝印是 GND/VDD/SCK/SDA，和常见顺序不一样。
3. 串口收着收着就没反应。ORE 之后 HAL 会把接收中断关掉，就是上面 `HAL_UART_ErrorCallback` 那条。

## 思考题

问：切换间隔较长（比如 2000 ms）时，按按键或发串口指令不能立刻执行，为什么？怎么改？

原因是主循环被 `HAL_Delay()` 卡住了：

```c
while (1) {
    LED_Next();
    HAL_Delay(step_ms);   // 这两秒里 CPU 什么都干不了
}
```

`HAL_Delay()` 是忙等。按键能进 EXTI 中断把标志置上，但标志要等延时结束、主循环转回来才处理，所以最坏要等一整个间隔；串口同理，字节能存进缓冲，解析和刷屏照旧推迟。问题不在中断，在主循环被阻塞。

改法有三种：

1. 时间戳法（本作业用的）：主循环不延时，每轮比一次 `HAL_GetTick() - tick >= step_ms`，不到点立刻返回。响应时间从"一个间隔"降到"一轮循环"。
2. 定时器中断：用 TIM 产生 1 ms 节拍，中断里数到 `step_ms` 再置"该换灯"标志，主循环只负责执行。适合节拍要求更准、或者要好几种不同周期的场合。
3. PWM + 状态机：如果还要调亮度（呼吸灯），用 TIM 出 PWM 调占空比，用软件状态机决定哪颗亮，同样不阻塞。

另外 `HAL_Delay()` 靠 SysTick 中断，在中断回调里调用会拖慢其他中断，所以回调里也不能用。本作业的回调只记标志，不干活。

## 参考资料

- 培训资料：《电控组第三次培训学习与操作指南》《电控组第三次招新培训作业》
- 视频：Keysking《STM32 入门》第 4~13 集；江协科技 STM32 教程 [3-3][3-4][4-1][4-2][5-1][8-1][8-2][9-1]~[9-5][10-1][10-4][10-5]
- OLED 驱动：电控 QQ 群给的 SSD1306 驱动（`OLED.c`/`OLED.h`/`OLED_Font.h`，源自江协科技配套驱动，原版是软件 I²C、PB0=SDA/PB1=SCL，我把传输层换成了硬件 I2C1、PB6/PB7），字模是 8×16 ASCII
- HAL 库：ST 官方 STM32CubeF1
- 手册：STM32F103C8 Datasheet、UM1850

## 目录

```
diankong3/
├─ README.md
├─ firmware/              工程本体，CLion 打开这个目录
│  ├─ CMakeLists.txt
│  ├─ cmake/gcc-arm-none-eabi.cmake
│  ├─ STM32F103C8Tx_FLASH.ld
│  ├─ Core/Inc/  Core/Src/
│  └─ Drivers/            STM32F1xx_HAL_Driver + CMSIS
├─ sim/                   离线仿真，PC 上验证逻辑
├─ 工具/                  build.ps1 flash.ps1 build_sim.ps1 发包工具.html 接线总表.png
└─ 电控组第三次作业实施手册.docx
```
