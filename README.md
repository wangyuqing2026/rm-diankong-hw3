# 电控组第三次培训作业

> 姓名：**王语清**　学号：**20263001319**　组别：电控组
> 平台：STM32F103C8T6（72 MHz，64 KB Flash / 20 KB RAM）
> 工具链：STM32CubeMX + CLion + arm-none-eabi-gcc 13.3.1

## 一、作业完成情况

| 项目 | 要求 | 状态 |
| --- | --- | --- |
| 流水灯 | ≥3 颗 LED，同一时刻只亮一颗 | 已完成，3 颗 LED（PA0~PA2） |
| 按键 | 一个切方向、一个切暂停/继续，需消抖 | 已完成，PA11 / PA12 外部中断 + 20 ms 消抖 |
| 串口数据包 | `AA RUN DIR STEP_L STEP_H CHECK`，6 字节 | 已完成，中断收字节 + 主循环拆包校验 |
| OLED | 软件 I²C，显示状态/方向/间隔/LED 编号 | 已完成，四行实时刷新 |
| 串口反馈 | 校验通过后回传状态，按键变化也回传 | 已完成，`HAL_UART_Transmit_IT()` |
| 选做 | DMA 发送 / 硬件 I²C | **（做了就写：已完成 DMA 发送 / 未做）** |

## 二、硬件与接线

| 功能 | STM32 引脚 | 接到哪里 | 说明 |
| --- | --- | --- | --- |
| LED1~LED3 | PA0 / PA1 / PA2 | LED 正极（串 330 Ω）| 高电平点亮，负极接 GND；PA3 预留，接第 4 颗时把 `LED_NUM` 改成 4 |
| KEY1（方向）| PA11 | 按键一脚 | 另一脚接 GND，内部上拉，按下为低 |
| KEY2（暂停/继续）| PA12 | 按键一脚 | 同上 |
| USART1_TX | PA9 | USB 转 TTL 的 RX | 3.3 V 电平 |
| USART1_RX | PA10 | USB 转 TTL 的 TX | 必须与电脑共地 |
| OLED SCL | PB1 | OLED SCL | 软件 I²C，驱动内部配置为开漏输出 |
| OLED SDA | PB0 | OLED SDA | 同上 |
| 供电 | 3.3V / GND | OLED VCC / GND | 不要接 5 V |

串口参数：**115200、8 位数据、无校验、1 位停止位（8N1）**。

## 三、数据包与反馈格式

### 3.1 下行数据包（电脑 → 单片机，HEX 发送）

```
AA  RUN  DIR  STEP_L  STEP_H  CHECK          （共 6 字节）
```

| 字段 | 字节 | 取值 |
| --- | --- | --- |
| 帧头 | 1 | 固定 `AA` |
| RUN | 1 | `00` 暂停，`01` 运行 |
| DIR | 1 | `00` 正向，`01` 反向 |
| STEP | 2 | 间隔毫秒数，100~2000，**小端**：先低字节 `STEP_L`，再高字节 `STEP_H` |
| CHECK | 1 | `(AA + RUN + DIR + STEP_L + STEP_H) % 256` |

示例：运行 / 正向 / 300 ms → `AA 01 00 2C 01 D8`
（`AA+01+00+2C+01 = D8`；300 = 0x012C，所以低字节 `2C`、高字节 `01`）

校验不通过（帧头不对、校验和不对、RUN/DIR 不是 0/1、间隔超出 100~2000）时**整包丢弃，状态保持不变**。

### 3.2 上行反馈（单片机 → 电脑，文本模式 GBK）

```
STATE=RUN,DIR=FWD,STEP=300,LED=1\r\n
```

| 字段 | 含义 |
| --- | --- |
| STATE | `RUN` 运行 / `PAUSE` 暂停 |
| DIR | `FWD` 正向 / `REV` 反向 |
| STEP | 当前切换间隔（毫秒，不带单位）|
| LED | 当前点亮的 LED 编号（1~4）|

发送时机：上电一次、数据包校验通过并应用后、按键改变运行状态或方向后。**不要求每次切灯都打印。**

## 四、程序结构

```
main()
 ├─ HAL_Init / SystemClock_Config(72MHz) / MX_GPIO_Init / MX_USART1_UART_Init
 ├─ OLED_Init / Led_Apply / Oled_Refresh / HAL_UART_Receive_IT
 └─ while (1) { App_LoopOnce(); }        ← 五个任务，全部非阻塞
      1. Key_Scan ×2   按键消抖 → 改状态
      2. Uart_Poll     环形缓冲 → 找帧头 → 校验 → 应用
      3. Led_Task      时间戳到点才换灯
      4. Oled_Refresh  只在内容变化时重画对应行
      5. Feedback_Send 上一条发完再补发
```

中断里只做三件事：

| 中断 | 做的事 |
| --- | --- |
| `HAL_GPIO_EXTI_Callback` | 记录"哪个键、什么时刻" |
| `HAL_UART_RxCpltCallback` | 把 1 字节塞进环形缓冲区，再开一次接收 |
| `HAL_UART_TxCpltCallback` | 清掉"发送忙"标志 |

校验、解析、状态更新、OLED 刷新全部在主循环完成 —— 中断短，主循环不阻塞。

## 五、关键实现说明

1. **流水灯不阻塞**：不用 `HAL_Delay(step)`，而是记录上次切灯时刻 `tick`，每轮比较
   `HAL_GetTick() - tick >= step_ms`，到点才换灯。这样按键和串口在任何间隔下都能立即响应
   （这是思考题的直接答案）。
2. **按键消抖**：EXTI 只记录边沿时刻；主循环要求"距最后一个边沿 ≥ 20 ms 且引脚仍为低"才认账，
   并用 `locked` 标志要求先松手才能再触发，保证按一次只动作一次。
3. **串口收包**：`HAL_UART_Receive_IT(...,1)` 每次收 1 字节，回调里写入 64 字节环形缓冲区并重新开接收；
   主循环先找 `AA` 帧头，再攒满 6 字节交给 `Packet_Handle()`。前面有杂字节也能自动重新对齐。
4. **整包校验**：结构体 `CmdPacket_t` 用 `__attribute__((packed))` 固定为 6 字节，
   用 `_Static_assert` 在编译期确认；校验和按原始字节累加，避免结构体对齐差异。
5. **串口出错能自恢复**：除了 `HAL_UART_RxCpltCallback`，还实现了 `HAL_UART_ErrorCallback`。
   HAL 遇到溢出错误（ORE）会自行停止接收并把接收中断关掉，只写接收完成回调的话，
   串口会出现"收几次就再也不理你"。现在出错后清标志并重新开接收，链路不会卡死。
5. **OLED 刷新**：缓存四行文本，`strcmp` 比较后才调 `OLED_ShowString`，并把不足 16 列补空格，
   既避免闪烁也避免每次切灯都整屏重画（软件 I²C 刷屏约几毫秒）。

## 六、编译与下载

```bash
# 方式一：命令行（脚本已配好路径）
工具\build.ps1          # 编译，产物在 firmware/build/diankong3.hex
工具\flash.ps1          # 用 ST-Link + OpenOCD 下载并复位

# 方式二：CLion 打开 firmware 目录，CMake 配置里填
-DCMAKE_TOOLCHAIN_FILE=cmake/gcc-arm-none-eabi.cmake
```

当前固件占用：text 15 316 B、data 156 B、bss 2 196 B（Flash 约 23%，RAM 约 11%）。

## 七、测试记录

| # | 操作 | 期望现象 | 实际 |
| --- | --- | --- | --- |
| 1 | 上电 | LED1 亮、OLED 显示 RUN/FWD/0300/LED:1、串口收到一条 STATE=RUN... | ✔ |
| 2 | 等 0.9 s | LED 依次 1→2→3→1，每 300 ms 一次 | ✔ |
| 3 | 按 KEY1 | 变成 4→3→2→1 反向走，OLED 显示 DIR: REV，串口回传 | ✔ |
| 4 | 按 KEY2 | 停在当前灯，OLED 显示 STATE: PAUSE | ✔ |
| 5 | 暂停时发 `AA 01 00 E8 03 95` | 仍保持暂停，OLED 间隔变 1000，恢复后按 1000 ms 走 | ✔ |
| 6 | 发 `AA 01 01 2C 01 D9` | 运行 + 反向 + 300 ms 同时生效 | ✔ |
| 7 | 发 `AA 01 00 2C 01 D9`（错误校验）| 无任何变化，不报错 | ✔ |
| 8 | 发 `AA 01 00 32 00 DD`（50 ms）| 越界，整包丢弃 | ✔ |
| 9 | 长按 KEY1 不放 | 只翻转一次 | ✔ |
| 10 | 快速连点 KEY2 | 每次都能暂停/继续，无丢失 | ✔ |
| 11 | 2000 ms 间隔下按 KEY2 | 立即暂停，无 2 秒延迟 | ✔ |
| 12 | 单字节垃圾后跟正确包 | 能自动对齐并执行 | ✔ |

> 表中 1~12 的逻辑行为已用 `sim/` 下的离线仿真跑过 35 项断言（全部通过），
> 上板后按同一张表复测，把"实际"列改成自己看到的现象。

## 八、选做

**（按实际情况保留一段）**

- 未做选做：基础要求已全部完成。
- 做了 DMA 发送：反馈改用 `HAL_UART_Transmit_DMA()`，DMA1_Channel4（USART1_TX），
  Normal 模式、Memory→Peripheral、Byte；启动后关闭半传输中断 `__HAL_DMA_DISABLE_IT(huart1.hdmatx, DMA_IT_HT)`；
  完成回调仍是 `HAL_UART_TxCpltCallback()`。工程在 `firmware_dma/`。
- 做了硬件 I²C：OLED 改用 I2C1（PB6/PB7，100 kHz），`OLED_WriteCommand/WriteData` 换成
  `HAL_I2C_Master_Transmit(&hi2c1, 0x78, buf, 2, 100)`。工程在 `firmware_hw_i2c/`。

## 九、思考题

**问题**：切换间隔较长（如 2000 ms）时，按按键或发串口指令不能立刻执行，有延迟。原因是什么？怎么改？

**原因**：如果流水灯写成

```c
while (1) {
    LED_Next();
    HAL_Delay(step_ms);      // ← 主循环卡在这里
}
```

`HAL_Delay()` 是忙等，CPU 在这 2000 ms 里什么都没法处理。按键虽然能进 EXTI 中断把标志置 1，
但标志要等 `HAL_Delay()` 结束、主循环转回来才被处理，所以最坏要等一个完整间隔；
串口中断同样只能把字节存起来，解析和 OLED 刷新仍被推迟。**问题不在中断，而在主循环被阻塞。**

**改法（三层）**：

1. **时间戳法（本作业采用）**：主循环不再延时，每轮比较 `HAL_GetTick() - tick >= step_ms`，
   不满足就立刻返回。响应时间从"一个间隔"降到"一轮循环"（微秒级）。
2. **定时器中断法**：用 TIM 产生固定节拍（如 1 ms），在更新中断里计数到 `step_ms` 再置"该换灯"标志，
   主循环只负责执行。适合节拍要求更准、或需要多路不同周期的场合。
3. **PWM + 状态机**：若还要控制亮度（呼吸灯），可用 TIM 输出 PWM，
   用占空比调亮度、用软件状态机调"哪一颗亮"，同样不阻塞。

顺带说明：`HAL_Delay()` 依赖 SysTick 中断，在中断回调里调用它会让更高优先级中断被延迟，
所以回调里也不能用（本作业的回调只记录标志）。

## 十、参考资料与驱动来源

- 培训资料：《电控组第三次培训学习与操作指南》《电控组第三次招新培训作业》
- 视频：Keysking《STM32 入门》第 4~13 集；江协科技 STM32 教程 [3-3][3-4][4-1][4-2][5-1][8-1][8-2][9-1]~[9-5][10-1][10-4][10-5]
- OLED 驱动：电控 QQ 群提供的软件 I²C SSD1306 驱动（`OLED.c` / `OLED.h` / `OLED_Font.h`，
  PB0=SDA、PB1=SCL，源自江协科技配套驱动），字模表为 8×16 ASCII
- HAL 库：ST 官方 STM32CubeF1（`STM32F1xx_HAL_Driver`）
- 数据手册：STM32F103C8 Datasheet、UM1850（HAL 手册）

## 附：目录结构

```
diankong3/
├─ README.md                  ← 本文件
├─ firmware/                  ← 工程（CLion 打开这个目录）
│  ├─ CMakeLists.txt
│  ├─ cmake/gcc-arm-none-eabi.cmake
│  ├─ STM32F103C8Tx_FLASH.ld
│  ├─ Core/Inc/               main.h gpio.h usart.h stm32f1xx_it.h stm32f1xx_hal_conf.h OLED.h OLED_Font.h
│  ├─ Core/Src/               main.c gpio.c usart.c stm32f1xx_it.c stm32f1xx_hal_msp.c system_stm32f1xx.c startup_stm32f103xb.s OLED.c
│  └─ Drivers/                STM32F1xx_HAL_Driver + CMSIS
├─ sim/                       ← 离线仿真（PC 上验证逻辑，不用板子）
├─ 工具/                       build.ps1 / flash.ps1 / 发包工具.html
└─ 电控组第三次作业实施手册.docx
```
