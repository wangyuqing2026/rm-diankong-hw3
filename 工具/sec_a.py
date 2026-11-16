# -*- coding: utf-8 -*-
"""手册第一部分：封面、目录、第 0~5 章"""


def build(h):
    # ================= 封面 =================
    h.title(
        '电控组第三次培训作业',
        '实 施 手 册 · STM32F103C8T6',
        [
            '流水灯 · 按键外部中断 · 串口数据包 · OLED 状态显示',
            '',
            '海南大学 RM 战队　电控组',
            '版本 1.0　2026-11-16',
        ],
    )

    # ================= 目录 =================
    h.pagebreak()
    p = h.doc.add_paragraph()
    run = p.add_run('目　录')
    from manual_kit import _set_run_font, ACCENT
    _set_run_font(run, size=16, bold=True, color=ACCENT)
    p.paragraph_format.space_after = 12

    toc = [
        ('第 0 章', '先看这里：这本手册怎么用'),
        ('第 1 章', '把作业翻译成代码'),
        ('第 2 章', '硬件与接线'),
        ('第 3 章', '环境、工程与编译下载'),
        ('第 4 章', '代码总览：五个任务与一份状态'),
        ('第 5 章', '逐模块实现与讲解'),
        ('第 6 章', '联调：分阶段点亮与测试用例'),
        ('第 7 章', '故障排查表'),
        ('第 8 章', '思考题：答案与延伸'),
        ('第 9 章', '选做：DMA 发送与硬件 I²C'),
        ('第 10 章', '提交：仓库、README、演示视频'),
        ('第 11 章', '实操考核模拟题库'),
        ('附录 A', '数据包速查表'),
        ('附录 B', '常用 HAL 函数速查'),
        ('附录 C', '术语表'),
    ]
    for no, name in toc:
        para = h.doc.add_paragraph()
        para.paragraph_format.space_after = 4
        r1 = para.add_run(no + '　')
        _set_run_font(r1, size=11, bold=True, color=ACCENT)
        r2 = para.add_run(name)
        _set_run_font(r2, size=11)

    h.spacer(10)
    h.note('本手册配套一份**可以直接编译下载的完整工程**（`firmware/`）和一份**离线仿真程序**（`sim/`）。'
           '建议第一次阅读时先照着第 0 章的里程碑走一遍，卡住了再翻对应的章节，不要从头到尾读完再动手。',
           label='怎么读')

    # ================= 第 0 章 =================
    h.h1('第 0 章　先看这里：这本手册怎么用')

    h.h2('0.1 你现在的位置')
    h.p('你已经完成了第二次作业的流水灯，知道 CubeMX 怎么配引脚、CLion 怎么编译下载，也知道 `HAL_GPIO_WritePin()` '
        '能控制 LED。这次要新增四样东西：**外部中断**、**串口中断收发**、**数据包**、**软件 I²C OLED**，'
        '外加一个选做的 **DMA 发送**。')
    h.p('难点不在"每个知识点都很难"，而在于**它们要共用同一份运行状态**：按键改它、串口改它、流水灯读它、'
        'OLED 显示它、串口反馈还要把它发出去。只要这份状态设计对了，剩下的都是体力活。')
    h.table(
        ['你已有的能力', '这次要补的', '补完的检验方式'],
        [
            ['GPIO 输出、CubeMX 配引脚、CLion 编译下载', '外部中断（EXTI）与回调', '按一下键，OLED 立刻变'],
            ['会写 while(1) + HAL_Delay 的流水灯', '不用 Delay 的定时（时间戳）', '2000 ms 间隔下按键也无延迟'],
            ['会用串口打印一句 HELLO', '中断收字节 + 拆包 + 校验', '发 6 个字节能改运行状态'],
            ['没用过 I²C', '软件 I²C 驱动 OLED', 'OLED 四行状态实时更新'],
            ['没做过中断发送', 'HAL_UART_Transmit_IT', '每次状态变化都收到一行文本'],
        ],
        widths=[5.6, 5.6, 4.6],
    )

    h.h2('0.2 时间安排：五天版 / 一天冲刺版')
    h.p('**如果只有一天**：看同目录的 `一天冲刺清单.docx` —— 里面是小时级时间表、硬件采买清单和"卡住 15 分钟就换招"的表。'
        '下面这张是按五天排的正常节奏，适合想边做边消化的走法。')
    h.table(
        ['第几天', '当天只做一件事', '做完的标准'],
        [
            ['11-16（今天）', '装好工程、点亮 4 颗流水灯、跑通离线仿真', 'LED 按 300 ms 轮转，`sim/test_app.exe` 全 PASS'],
            ['11-17', '接两个按键，做外部中断 + 消抖', '按 KEY1 反方向、按 KEY2 暂停，长按只触发一次'],
            ['11-18', '串口收字节 + 拆包 + 校验', '发 `AA 01 00 2C 01 D8` 能改状态，错包被丢弃'],
            ['11-19', 'OLED 四行显示 + 串口反馈', '屏幕和串口回传都跟着状态变'],
            ['11-20', '整体联调、按第 6 章测试表逐条过', '12 条测试全部打勾'],
            ['11-21', '录演示视频、写 README、提交 GitHub', '群作业链接交上去'],
        ],
        widths=[3.2, 7.4, 5.2],
    )
    h.p('如果某一天落后了，**优先保住"基础四项"（流水灯、按键、串口包、OLED）**，选做放到最后，做不完不影响基础分。')

    h.h2('0.3 六个里程碑')
    h.p('把作业拆成 6 个可以独立验收的小目标，每完成一个就停下来测一次。'
        '**千万不要六个一起写，然后一起调试** —— 那是新手最容易崩的方式。')
    h.table(
        ['里程碑', '目标', '完成标志（能自己验证）', '参考章节'],
        [
            ['M0', '工程能编译、能下载、串口能打印', '上电后串口助手收到一行 `STATE=RUN,...`', '第 3 章'],
            ['M1', '3 颗 LED 流水灯', 'LED 按 300 ms 依次点亮、循环', '5.2'],
            ['M2', '两个按键 + 消抖', 'KEY1 换向、KEY2 暂停/继续，长按不重复', '5.3'],
            ['M3', '串口收 6 字节数据包', '发包能改状态，错包不生效', '5.4 / 5.5'],
            ['M4', 'OLED 四行状态', '屏幕显示 STATE / DIR / STEP / LED', '5.8'],
            ['M5', '串口反馈', '每次状态变化收到 `STATE=...` 一行', '5.7'],
            ['M6', '联调 + 思考题', '第 6 章 12 条测试全过，能回答思考题', '第 6、8 章'],
        ],
        widths=[1.8, 4.4, 6.6, 3.0],
    )

    h.h2('0.4 每个模块的写法都一样')
    h.p('第 5 章每一节都按同一个顺序讲，你可以照着这个顺序自己推导别的功能：')
    h.num(1, '**先想清楚**：这个功能由谁触发？数据存在哪？什么时候更新？')
    h.num(2, '**再写代码**：只写这一个功能需要的最小代码，别急着合并。')
    h.num(3, '**然后解释**：逐行说清每个变量什么时候被谁改。')
    h.num(4, '**最后列易错点**：这类代码最常错在哪，错了会看到什么现象。')

    # ================= 第 1 章 =================
    h.h1('第 1 章　把作业翻译成代码')

    h.h2('1.1 需求 → 代码：一张表看完')
    h.p('作业文档的每一条要求，最后都会落到某个变量或某个函数上。先建立这张映射，写代码时就不会漏。')
    h.table(
        ['作业要求', '由谁实现', '关键变量 / 函数'],
        [
            ['≥3 颗 LED，同一时刻只亮一颗', '主循环 Led_Task', '`s_led.led` + `Led_Apply()`'],
            ['一个键切方向', 'EXTI + Key_Scan', '`s_key1` → `s_led.dir`'],
            ['一个键切暂停/继续', 'EXTI + Key_Scan', '`s_key2` → `s_led.running`'],
            ['暂停保留当前灯', 'Led_Task 直接 return', '不改 `s_led.led`'],
            ['按键消抖，一次只触发一次', '时间戳 + locked', '`s_key1_edge/tick`、`key->locked`'],
            ['串口收 6 字节包', '中断收字节 + 主循环拆包', '`s_rx_ring`、`s_pkt_buf`'],
            ['校验帧头与校验和', 'Packet_Handle', '`raw[0..4]` 累加'],
            ['一包同时更新三项', 'Packet_Handle', '`running/dir/step_ms` 一起写'],
            ['暂停期间的修改要能生效', '先写状态，暂不动灯', '`s_led.tick = HAL_GetTick()`'],
            ['OLED 显示四项状态', 'Oled_Refresh', '`s_oled_line[4][17]`'],
            ['按键/串口都同步显示', 'App_StateChanged', '`s_oled_dirty = 1`'],
            ['串口中断回传状态', 'Feedback_Send', '`HAL_UART_Transmit_IT()`'],
            ['中断只做必要的事', '三个回调', '只写标志/塞缓冲区'],
        ],
        widths=[6.0, 4.6, 5.4],
    )

    h.h2('1.2 一份状态，三种输出')
    h.p('整个程序只有**一份**流水灯状态，按键、串口只负责改它；流水灯、OLED、串口反馈只负责读它。'
        '这样三者永远不会"打架"——不会出现 LED 在跑但屏幕写暂停的情况。')
    h.code(r'''
                  ┌──────────────┐        ┌──────────────┐
   按键 EXTI ────►│              │        │  Led_Task    │───► 3 颗 LED
                  │   s_led      │───────►│              │
   串口数据包 ──►│  running     │        ├──────────────┤
                  │  dir         │───────►│  Oled_Refresh│───► OLED 四行
                  │  step_ms     │        ├──────────────┤
                  │  led / tick  │───────►│ Feedback_Send│───► 串口文本
                  └──────────────┘        └──────────────┘
                        ▲
                        └── 唯一的"真相来源"：谁想改状态，都改这里
''', caption='图 1-1　数据流：一份状态，三个消费者')

    h.h2('1.3 中断和主循环怎么分工')
    h.p('作业明确要求"中断回调只完成必要的数据接收或事件记录，解析、状态更新、OLED 刷新放在主循环"。'
        '这不是形式要求，而是有实际原因的：中断里做长事情，会拖慢其它中断，串口就会丢字节。')
    h.table(
        ['放在中断里（必须快）', '放在主循环（可以慢）'],
        [
            ['记录"哪个键、什么时刻"', '消抖判断、改方向/运行状态'],
            ['把 1 个字节塞进环形缓冲区', '找帧头、算校验和、解析字段'],
            ['清掉"发送完成"标志', '格式化反馈文本、刷 OLED'],
        ],
        widths=[7.0, 8.0],
    )
    h.note('三条硬规矩：① 回调里不许 `HAL_Delay()`；② 回调里不许刷 OLED；③ 回调里不许等串口发送完成。'
           '违反了程序不一定马上崩，但会出现"偶尔卡死""串口丢包"这类最难查的问题。')

    # ================= 第 2 章 =================
    h.h1('第 2 章　硬件与接线')

    h.h2('2.1 器材清单')
    h.table(
        ['器材', '数量', '备注'],
        [
            ['STM32F103C8T6 最小系统板', '1', '板载 8 MHz 晶振、3.3 V 稳压'],
            ['ST-Link V2 下载器', '1', '接 SWD：SWDIO / SWCLK / GND / 3.3V'],
            ['USB 转 TTL 模块（CH340 / CP2102）', '1', '3.3 V 电平，**不要**用 5 V 档'],
            ['4 针 I²C OLED（SSD1306，128×64）', '1', 'GND / VCC / SCL / SDA'],
            ['两脚轻触按键', '2', '常开型'],
            ['LED（3 mm 或 5 mm）', '4', '颜色随意，作业要求 ≥3'],
            ['电阻 330 Ω', '4', 'LED 限流，别省'],
            ['面包板 + 杜邦线', '1 套', '公对公 / 公对母按需'],
        ],
        widths=[7.4, 1.8, 5.8],
    )

    h.h2('2.2 引脚分配（照这张表接就不会错）')
    h.table(
        ['功能', '引脚', '模式（CubeMX 里的设置）', '接到哪里'],
        [
            ['LED1', 'PA0', 'GPIO_Output 推挽', 'LED 正极（串 330 Ω），负极 GND'],
            ['LED2', 'PA1', 'GPIO_Output 推挽', '同上'],
            ['LED3', 'PA2', 'GPIO_Output 推挽', '同上'],
            ['LED4（预留）', 'PA3', 'GPIO_Output 推挽', '同上'],
            ['KEY1（方向）', 'PA11', 'GPIO_EXTI11，下降沿，Pull-up', '按键一脚；另一脚 GND'],
            ['KEY2（暂停）', 'PA12', 'GPIO_EXTI12，下降沿，Pull-up', '按键一脚；另一脚 GND'],
            ['USART1_TX', 'PA9', 'USART1 Asynchronous', 'USB-TTL 的 **RX**'],
            ['USART1_RX', 'PA10', 'USART1 Asynchronous', 'USB-TTL 的 **TX**'],
            ['OLED SCL', 'PB1', '不用配（驱动里配成开漏输出）', 'OLED SCL'],
            ['OLED SDA', 'PB0', '不用配（驱动里配成开漏输出）', 'OLED SDA'],
        ],
        widths=[3.6, 2.2, 5.6, 5.6],
    )
    h.p('为什么这么选：**PA11/PA12 共用同一个中断入口 `EXTI15_10`**（外部中断线按引脚号 0~15 分组，'
        '10~15 号共用一个中断向量），所以两个按键只需要开一条 NVIC 中断，配置最简单；'
        'PB0/PB1 是群文件里那份 OLED 驱动写死的引脚，跟着驱动走最省事；'
        'PA9/PA10 是 USART1 的默认引脚，不用重映射。')

    h.h2('2.3 接线顺序（六步，每步都要能测）')
    h.num(1, '**只接下载线**：ST-Link 的 3.3V/GND/SWDIO/SWCLK 接板子对应引脚（板子上有 SWD 排针）。'
             '先烧一个最简单的程序，确认能下载、能复位。')
    h.num(2, '**接 3 颗 LED**：每颗 LED 串一个 330 Ω，正极接 PA0~PA2，负极接 GND（第 4 颗 PA3 预留）。'
             '烧 M1 的程序，确认 3 颗都能亮、都能灭（这一步能查出 LED 极性接反）。')
    h.num(3, '**接 2 个按键**：按键跨在 PA11 和 GND 之间、PA12 和 GND 之间。'
             '不用外接上拉电阻——PA11/PA12 开内部上拉。')
    h.num(4, '**接串口**：PA9 → 模块 RX，PA10 ← 模块 TX，模块 GND 接板子 GND（**必须共地**），模块 VCC 可不接。')
    h.num(5, '**接 OLED**：3.3V → VCC，GND → GND，PB1 → SCL，PB0 → SDA。'
             '注意有些模块丝印顺序是 GND/VCC/SCL/SDA，有些是 VCC/GND/SCL/SDA，**以丝印为准**。')
    h.num(6, '**整机复测**：上电，看 OLED 是否亮、串口是否收到上电反馈、LED 是否开始流水。')

    h.h2('2.4 上电前 8 条检查')
    h.table(
        ['#', '检查什么', '怎么查'],
        [
            ['1', '电源没有短路', '3.3V 与 GND 之间用万用表量，不能是 0 Ω'],
            ['2', 'OLED 接 3.3V 不是 5V', '看模块丝印'],
            ['3', 'LED 极性', '长脚（正极）朝 GPIO，短脚朝 GND'],
            ['4', '按键两端', '一端 PA11/PA12，一端 GND，别接成 VCC'],
            ['5', '串口 TX/RX 交叉', 'PA9→RX、PA10→TX，接错只收不发或不收不发'],
            ['6', '共地', 'USB-TTL 的 GND 和板子 GND 必须连'],
            ['7', 'PB0/PB1 没被别的东西占用', '比如 ADC 或别的模块'],
            ['8', 'ST-Link 的 3.3V 不要和板子外部供电打架', '板子只从一个地方取电'],
        ],
        widths=[1.0, 7.0, 7.0],
    )

    h.h2('2.5 四种常见接线错误的现象')
    h.table(
        ['现象', '最可能的原因'],
        [
            ['LED 一颗都不亮，但程序在跑', 'LED 极性接反，或限流电阻太大（>10 kΩ）'],
            ['按键不用按就一直在触发', '按键一端接成了 VCC，或没开内部上拉'],
            ['串口助手全是乱码', '波特率不是 115200，或模块是 5 V 电平'],
            ['OLED 全黑，但串口正常', 'VCC/GND 接反、SCL/SDA 接反、或 PB0/PB1 被占用'],
        ],
        widths=[7.0, 8.0],
    )

    # ================= 第 3 章 =================
    h.h1('第 3 章　环境、工程与编译下载')

    h.h2('3.1 这台电脑上已经装好了什么')
    h.p('你之前在另一台电脑上做第二次作业，这台电脑的环境我已经重新配好，全部是**免安装（便携版）**，'
        '不需要管理员权限，也不会写注册表：')
    h.table(
        ['工具', '位置', '版本', '用途'],
        [
            ['arm-none-eabi-gcc', r'D:\apps\diankong-tools\gcc\bin', '13.3.1', '交叉编译（生成 .elf/.hex）'],
            ['CMake', r'D:\apps\diankong-tools\cmake\bin', '4.5.0', '生成构建文件'],
            ['Ninja', r'D:\apps\diankong-tools\ninja', '1.13.2', '实际执行编译'],
            ['OpenOCD', r'D:\apps\diankong-tools\openocd\bin', '0.12.0', '通过 ST-Link 烧录/调试'],
            ['CLion', r'D:\apps\diankong-tools\clion', '2026.3', '写代码、编译、断点调试'],
        ],
        widths=[4.4, 7.0, 2.0, 3.6],
    )
    h.note('CLion 是商业软件，首次启动会让你登录 JetBrains 账号并选择许可方式（学生可申请免费的教育许可，'
           '或者用 30 天试用）。**即使不激活 CLion 也能做作业**：用 `工具\\build.ps1` 编译、`工具\\flash.ps1` 下载，'
           '用任意文本编辑器改代码即可。', label='关于 CLion 授权')

    h.h2('3.2 三种工作方式，选一种就行')
    h.table(
        ['方式', '怎么做', '适合什么时候'],
        [
            ['① 命令行脚本', '双击/运行 `工具\\build.ps1`，再 `工具\\flash.ps1`', '最快，不依赖 IDE；改一行编译一次'],
            ['② CLion', '打开 `firmware` 目录 → CMake 选项填 `-DCMAKE_TOOLCHAIN_FILE=cmake/gcc-arm-none-eabi.cmake` → 构建', '要断点调试、看变量、跳转定义'],
            ['③ CubeMX 新建', '按 3.3 的表重新配一遍，再把 `main.c` 里的 USER CODE 段落搬过去', '老师要求必须有 .ioc，或你要改外设配置'],
        ],
        widths=[2.6, 8.4, 5.0],
    )
    h.note('`工具\\flash.ps1` 用的是 OpenOCD + ST-Link。**第一次用之前要先装 ST-Link 驱动**'
           '（ST 官网的 ST-LINK_USB_Driver，或装了 STM32CubeProgrammer 自带）。'
           '如果 OpenOCD 报 `No ST-LINK detected`，先用 STM32CubeProgrammer 的图形界面烧一次 '
           '`firmware/build/diankong3.hex` 验证硬件通路，再回头查驱动。', label='烧录')

    h.h2('3.3 用 CubeMX 新建工程：逐项配置清单')
    h.p('如果你要在自己电脑上用 CubeMX 重新生成，照着这张表点，不要凭记忆：')
    h.table(
        ['页面', '项目', '设置'],
        [
            ['Pinout', 'PA0~PA3', 'GPIO_Output（推挽、无上下拉、Low 速度）'],
            ['Pinout', 'PA11 / PA12', 'GPIO_EXTI11 / GPIO_EXTI12；GPIO mode = External Interrupt Mode with Falling edge trigger；Pull-up'],
            ['Pinout', 'PA9 / PA10', 'USART1 → Asynchronous（自动分配）'],
            ['Pinout', 'PB0 / PB1', '**不要配**（OLED 驱动在 `OLED_I2C_Init()` 里自己配成开漏输出）'],
            ['Clock', 'RCC', 'HSE = Crystal/Ceramic Resonator'],
            ['Clock', 'Clock Configuration', 'HSE 8 MHz → PLLMul ×9 → SYSCLK 72 MHz；APB1 = 36 MHz（/2）、APB2 = 72 MHz'],
            ['NVIC', 'EXTI line[15:10]', '勾选 Enabled，Preemption Priority = 2'],
            ['NVIC', 'USART1 global interrupt', '勾选 Enabled，Preemption Priority = 1（比按键高）'],
            ['SYS', 'Debug', 'Serial Wire（不选的话下次可能连不上）'],
            ['Project', 'Toolchain/IDE', 'CMake（配合 CLion），或者 STM32CubeIDE'],
        ],
        widths=[2.6, 5.0, 8.0],
    )
    h.p('**为什么串口中断优先级要比按键高**：串口一个字节 115200 波特率下约 87 μs 就收完，'
        '如果按键中断（含消抖处理）占用太久，串口硬件寄存器会被覆盖，导致丢字节。'
        '把串口设成更高优先级（数字更小），它能打断按键中断。')

    h.h2('3.4 工程目录与 USER CODE 规矩')
    h.code(r'''
firmware/
├─ Core/Inc/          main.h  gpio.h  usart.h  stm32f1xx_it.h  stm32f1xx_hal_conf.h  OLED.h  OLED_Font.h
├─ Core/Src/          main.c  gpio.c  usart.c  stm32f1xx_it.c  stm32f1xx_hal_msp.c
│                     system_stm32f1xx.c  startup_stm32f103xb.s  OLED.c
├─ Drivers/           STM32F1xx_HAL_Driver/ + CMSIS/
├─ CMakeLists.txt
└─ STM32F103C8Tx_FLASH.ld
''', caption='图 3-1　工程结构（和 CubeMX 生成的完全一致）')
    h.p('自己写的代码一定放在 `USER CODE BEGIN x` 与 `USER CODE END x` 之间，否则 CubeMX 重新生成时会被删掉：')
    h.table(
        ['区号', '位置', '放什么'],
        [
            ['PV', '`USER CODE BEGIN PV`', '全局/静态变量（`s_led`、`s_rx_ring`、`s_pkt_buf` 等）'],
            ['0', '`USER CODE BEGIN 0`', '自己写的辅助函数原型、宏（本工程用不到）'],
            ['2', '`USER CODE BEGIN 2`', '初始化之后的启动代码（`OLED_Init()`、启动接收）'],
            ['3', '`USER CODE BEGIN 3`', '主循环里的代码（本工程只有 `App_LoopOnce();`）'],
            ['4', '`USER CODE BEGIN 4`', '所有函数实现 + 三个中断回调'],
        ],
        widths=[1.6, 5.4, 9.0],
    )

    h.h2('3.5 编译产物')
    h.p('编译成功后在 `firmware/build/` 下会有三个文件，用哪个取决于烧录工具：')
    h.table(
        ['文件', '用途'],
        [
            ['`diankong3.elf`', '带调试信息，OpenOCD / CLion 调试用（推荐）'],
            ['`diankong3.hex`', 'ST-Link Utility、STM32CubeProgrammer、FlyMcu 都能烧'],
            ['`diankong3.bin`', '纯二进制，某些串口 ISP 下载工具用'],
        ],
        widths=[4.4, 10.6],
    )
    h.p('当前固件占用：**text 15 316 B / data 156 B / bss 2 196 B**（Flash 约 23%、RAM 约 11%），留有很大余量。')

    # ================= 第 4 章 =================
    h.h1('第 4 章　代码总览：五个任务与一份状态')

    h.h2('4.1 主循环里的五个任务')
    h.p('主循环不是"流水账"，而是**五个互不阻塞的小任务**轮流跑一轮。每一轮都在微秒级完成，所以看起来是"同时"在响应。')
    h.table(
        ['顺序', '任务', '多久做一次', '做什么', '绝对不许做'],
        [
            ['1', '`Key_Scan()` ×2', '每轮', '消抖确认、改方向/运行', '`HAL_Delay()`、刷屏'],
            ['2', '`Uart_Poll()`', '每轮', '取字节、找帧头、校验、应用', '等发送完成'],
            ['3', '`Led_Task()`', '每轮（到点才动）', '换下一颗灯', '延时等待'],
            ['4', '`Oled_Refresh()`', '内容变了才做', '重画变化的那一行', '每轮无条件刷屏'],
            ['5', '`Feedback_Send()`', '有变化且空闲时', '格式化并启动中断发送', '忙等发送完成'],
        ],
        widths=[1.4, 4.4, 3.6, 4.0, 4.0],
    )

    h.h2('4.2 一轮主循环长什么样')
    h.code(r'''
static void App_LoopOnce(void)
{
  /* 1) 按键：消抖确认后改状态 */
  if (Key_Scan(&s_key1)) { s_led.dir ^= 1;      App_StateChanged(); }
  if (Key_Scan(&s_key2)) { s_led.running ^= 1;  if (运行) s_led.tick = HAL_GetTick();  App_StateChanged(); }

  /* 2) 串口：缓冲区里的字节 → 数据包 → 应用 */
  Uart_Poll();

  /* 3) 流水灯：到点才换灯 */
  Led_Task();

  /* 4) OLED：内容变了才重画 */
  if (s_oled_dirty) { s_oled_dirty = 0; Oled_Refresh(); }

  /* 5) 反馈：上一条发完再补发 */
  if (s_tx_pending && !s_tx_busy) { s_tx_pending = 0; Feedback_Send(); }
}
''', caption='代码 4-1　主循环一轮（`main.c` 里的 `App_LoopOnce`）')
    h.p('为什么要单独抽成函数而不是直接写在 `while (1)` 里？因为**抽出来才能在电脑上仿真**：'
        '`sim/test_app.c` 用假的 HAL 驱动这个函数跑 35 项断言，不用接板子就能验证逻辑。'
        '这也是第 11 章现场改代码时你能快速验证的原因。')

    h.h2('4.3 关键变量：谁写、谁读、为什么要 volatile')
    h.table(
        ['变量', '类型', '谁写', '谁读', '为什么'],
        [
            ['`s_led`', '`LedState_t`', '主循环', '主循环', '唯一状态源，不需要 volatile'],
            ['`s_key1_edge`', '`volatile uint8_t`', 'EXTI 回调', '主循环', '中断与主循环共享，必须 volatile'],
            ['`s_key1_tick`', '`volatile uint32_t`', 'EXTI 回调', '主循环', '同上（记录边沿时刻）'],
            ['`s_rx_ring/head/tail`', '`uint8_t[]` + `volatile uint16_t`', '回调写 head', '主循环写 tail', '经典单生产者/单消费者'],
            ['`s_pkt_len`', '`uint8_t`', '主循环', '主循环', '拆包状态机，只在主循环里动'],
            ['`s_tx_busy`', '`volatile uint8_t`', '主循环置 1、回调清 0', '两边都读', '中断与主循环共享'],
            ['`s_oled_line[4][17]`', '`char`', '主循环', '主循环', '行缓存，避免重复刷屏'],
        ],
        widths=[3.6, 4.6, 3.6, 3.0, 4.0],
    )
    h.note('`volatile` 只解决"编译器优化掉读写"的问题，**不解决并发安全**。'
           '本项目靠"单写者"来保证安全：head 只有中断写、tail 只有主循环写，所以不需要关中断。')

    # ================= 第 5 章 =================
    h.h1('第 5 章　逐模块实现与讲解')

    h.h2('5.1 常量与数据结构')
    h.p('先把"魔法数字"变成有名字的常量，再给数据包定义一个结构体。结构体是这次作业的硬要求，也是最有用的技巧：'
        '它让"第 3、4 个字节组成一个 16 位间隔"这种话，变成 `pkt.step_ms` 这样一眼就懂的代码。')
    h.code(r'''
#define LED_NUM           3u      /* 实际接了几颗就写几（本项目 3 颗） */
#define KEY_DEBOUNCE_MS   20u     /* 消抖时间 */
#define RX_RING_SIZE      64u     /* 接收环形缓冲区大小 */
#define PKT_HEADER        0xAAu
#define PKT_SIZE          6u
#define STEP_MIN_MS       100u
#define STEP_MAX_MS       2000u

/* 收到的数据包：每个字节是什么，一目了然 */
typedef struct __attribute__((packed))
{
    uint8_t  header;      /* 0xAA */
    uint8_t  run;         /* 0/1 */
    uint8_t  dir;         /* 0/1 */
    uint16_t step_ms;     /* 小端存放，STM32 上可直接用 */
    uint8_t  check;       /* 校验和 */
} CmdPacket_t;

_Static_assert(sizeof(CmdPacket_t) == PKT_SIZE, "数据包结构体必须是 6 字节");
''', caption='代码 5-1　常量与数据包结构体')
    h.p('三个要点：')
    h.bullet('`__attribute__((packed))` 让编译器**不插入对齐填充**。`uint16_t` 默认要求 2 字节对齐，'
             '如果没有 packed，编译器可能在 `dir` 后面塞一个空字节，结构体就变成 7 字节，接收长度全错。')
    h.bullet('`_Static_assert` 是编译期检查：一旦结构体大小不是 6，**编译直接报错**，而不是等到板子上才发现收不全。'
             '这种"把错误提前到编译期"的习惯非常值得学。')
    h.bullet('`uint16_t step_ms` 在 STM32（小端）上正好是"低字节在前"，和作业要求的发送顺序一致，'
             '所以收到后可以直接用，不需要手动 `lo | (hi << 8)`。')

    h.h2('5.2 流水灯：用时间戳代替 HAL_Delay')
    h.p('**先想清楚**：换灯的时机由"距上次换灯过了多久"决定，而不是"睡多久"。'
        '只要记住上次的时刻，每轮比较一次就够了——这样主循环永远不会停在那里等。')
    h.code(r'''
static void Led_Task(void)
{
  uint32_t now;

  if (!s_led.running) return;                 /* 暂停：保持现状，不动灯 */

  now = HAL_GetTick();
  if ((uint32_t)(now - s_led.tick) < s_led.step_ms) return;   /* 还没到点 */

  s_led.tick += s_led.step_ms;                /* 累加，长期运行不漂移 */
  if ((uint32_t)(now - s_led.tick) >= s_led.step_ms) {
    s_led.tick = now;                         /* 落后太多就别补跳一串 */
  }

  if (s_led.dir == 0u) s_led.led = (uint8_t)((s_led.led + 1u) % LED_NUM);
  else                 s_led.led = (uint8_t)((s_led.led + LED_NUM - 1u) % LED_NUM);

  Led_Apply();
  s_oled_dirty = 1u;                          /* 编号变了，屏幕要更新 */
}
''', caption='代码 5-2　流水灯（不阻塞）')
    h.p('三个细节值得注意：')
    h.bullet('**`(uint32_t)(now - tick)` 而不是 `now > tick + step`**：`HAL_GetTick()` 是 32 位、约 49.7 天回绕一次，'
             '直接相减（无符号）在回绕时结果依然正确。这是嵌入式的标准写法。')
    h.bullet('**反向用 `+ LED_NUM - 1` 再取模**：`(0 + 4 - 1) % 4 = 3`，从 LED1 退到 LED4，不会出现负数下标。')
    h.bullet('**`tick += step` 而不是 `tick = now`**：前者不累积误差；但如果主循环被卡住很久（比如调试时），'
             '差值会超过一个间隔，所以加了一句"落后太多就重置"，避免一下子连跳好几颗。')
    h.table(
        ['错误写法', '现象', '为什么错'],
        [
            ['`HAL_Delay(step_ms)` 放在循环里', '2000 ms 间隔时按键要等 2 秒才响应', 'CPU 卡在延时里，主循环不转'],
            ['`if (now > tick + step)`', '开机 49.7 天后流水灯停住', '32 位溢出后条件不再成立'],
            ['`tick = now` 且没有容错', '调试打断后一次跳好几颗', '落后量被一次性补上'],
            ['`LED_NUM` 写成 4 但只接了 3 颗', '每轮有 1/4 时间"全灭"，像卡了一拍', '那一步的高电平送到了空引脚'],
        ],
        widths=[6.0, 5.0, 4.6],
    )
    h.p('`LED_NUM` 一定要等于**实际接的灯数**（本项目接了 3 颗，所以写 `3u`）。'
        '如果写成 4，流水灯转到第 4 步时没有灯可点，屏幕上还会显示 `LED: 4`——现象是"灯停了一拍"，很容易被误判成程序卡死。')

    h.h2('5.3 按键：外部中断 + 20 ms 消抖 + 松开锁')
    h.p('**先想清楚**：一次"按下"在电气上其实是一串抖动（5~20 ms 内高低跳好几次）。'
        '如果每个下降沿都动作，按一次可能切三四次方向。所以需要判断"电平已经稳定"。')
    h.p('中断里只记录"某个键在什么时刻出现了下降沿"，这是最轻的工作：')
    h.code(r'''
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
  uint32_t now = HAL_GetTick();

  if (GPIO_Pin == KEY1_Pin) { s_key1_tick = now; s_key1_edge = 1u; }
  else if (GPIO_Pin == KEY2_Pin) { s_key2_tick = now; s_key2_edge = 1u; }
}
''', caption='代码 5-3　外部中断回调（`USER CODE 4` 区）')
    h.p('消抖放在主循环。关键技巧：**抖动会不停刷新 `edge_tick`**，所以只有"最后一次边沿之后又安静了 20 ms"'
        '才会被确认，天然把抖动过滤掉：')
    h.code(r'''
static uint8_t Key_Scan(KeyCtx_t *key)
{
  if (key->locked) {                        /* 已经算过这次按下，等松手 */
    if (HAL_GPIO_ReadPin(key->port, key->pin) == GPIO_PIN_SET) key->locked = 0u;
    return 0u;
  }
  if (*(key->edge_flag) == 0u) return 0u;

  if ((uint32_t)(HAL_GetTick() - *(key->edge_tick)) < KEY_DEBOUNCE_MS) return 0u;  /* 还在抖 */

  *(key->edge_flag) = 0u;
  if (HAL_GPIO_ReadPin(key->port, key->pin) == GPIO_PIN_RESET) {
    key->locked = 1u;                       /* 确认按下，锁住直到松手 */
    return 1u;
  }
  return 0u;                                /* 假边沿（例如松手时的抖动） */
}
''', caption='代码 5-4　按键扫描（消抖 + 松开确认）')
    h.p('时间轴看一遍就懂了：')
    h.code(r'''
按下瞬间（抖动 6 ms）        安静 20 ms            松手
  │▼▲▼▲▼│                    │                    │
  └─ 每次边沿都刷新 edge_tick；最后一次边沿 + 20 ms 才确认 ─┘
     ↓
  确认时 locked=1：按住不放再来边沿也不动作；松手后 locked=0，下次才能再触发
''')
    h.note('为什么不用"中断里 delay 10 ms 再读一次"？因为在中断里延时会让串口抢不到 CPU，'
           '115200 波特率下一个字节 87 μs，10 ms 足够丢十几个字节。')

    h.h2('5.4 串口收字节：环形缓冲区')
    h.p('**先想清楚**：串口是"一个字节一个字节"来的，而数据包是"6 个字节一起"才有意义。'
        '所以中间要有一个**能暂存、能先进先出**的地方，这就是环形缓冲区。')
    h.code(r'''
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance == USART1) {
    uint16_t next = (uint16_t)((s_rx_head + 1u) % RX_RING_SIZE);

    if (next != s_rx_tail) {                 /* 没满就存 */
      s_rx_ring[s_rx_head] = s_rx_byte;
      s_rx_head = next;
    } else {
      s_rx_drop++;                           /* 满了就丢（调试时可观察） */
    }

    (void)HAL_UART_Receive_IT(&huart1, &s_rx_byte, 1u);   /* 必须重新开！ */
  }
}
''', caption='代码 5-5　接收完成回调（`USER CODE 4` 区）')
    h.p('三个必须理解的点：')
    h.bullet('**必须重新 `HAL_UART_Receive_IT()`**。HAL 的 `Receive_IT` 是一次性的：收满指定长度就停。'
             '不重新开，你会发现"只能收到第一个字节"——这是新手第一大坑。')
    h.bullet('**为什么不用 `HAL_UART_Receive_IT(..., 6)` 一次收 6 字节**：那样只能"整包对齐"地收。'
             '如果电脑先发了一个杂字节，之后所有包都会错位。逐字节收 + 自己找帧头，才能自动重新对齐。')
    h.bullet('**为什么 head/tail 一个中断写一个主循环写**：单写者模型，两边互不加锁也不会坏。'
             '如果两边都写同一个变量，就要关中断保护了。')
    h.note('还有一个坑：HAL 在收到**溢出错误（ORE）**时会自动停止接收、把接收中断关掉。'
           '如果只实现 `HAL_UART_RxCpltCallback`，串口会出现"收几次就再也不理你、发什么都没反应"。'
           '解决办法是再实现一个 `HAL_UART_ErrorCallback`，清掉错误标志后重新 `HAL_UART_Receive_IT()`。'
           '本工程已加上这段，你调试时如果遇到"串口突然不收了"，先看是不是少了它。', label='进阶')

    h.h2('5.5 拆包：帧头状态机 + 校验和')
    h.p('主循环从缓冲区取字节，先找帧头 `AA`，再攒满 6 字节交给校验函数。'
        '这个"状态机"只有两个状态：**还没对齐**（丢字节直到看见 AA）和**正在攒包**。')
    h.code(r'''
static void Uart_Poll(void)
{
  uint8_t b;

  while (Ring_Pop(&b)) {
    if (s_pkt_len == 0u) {
      if (b == PKT_HEADER) s_pkt_buf[s_pkt_len++] = b;   /* 对齐到帧头 */
    } else {
      s_pkt_buf[s_pkt_len++] = b;
      if (s_pkt_len >= PKT_SIZE) { Packet_Handle(s_pkt_buf); s_pkt_len = 0u; }
    }
  }
}
''', caption='代码 5-6　拆包状态机')
    h.p('校验与应用的顺序很重要：**先全部检查，全部通过才改状态**。任何一项不合格就整包丢弃，'
        '这样"半个包生效"的情况永远不会发生：')
    h.code(r'''
static void Packet_Handle(const uint8_t *raw)
{
  CmdPacket_t pkt;
  uint8_t     sum;
  uint16_t    step;

  memcpy(&pkt, raw, PKT_SIZE);               /* 避免对未对齐地址取 uint16_t */

  if (pkt.header != PKT_HEADER) return;                       /* 1. 帧头 */
  sum = (uint8_t)(raw[0] + raw[1] + raw[2] + raw[3] + raw[4]);
  if (sum != pkt.check) return;                               /* 2. 校验和 */
  if ((pkt.run > 1u) || (pkt.dir > 1u)) return;               /* 3. 取值 */
  step = pkt.step_ms;
  if ((step < STEP_MIN_MS) || (step > STEP_MAX_MS)) return;   /* 4. 范围 */

  s_led.running = pkt.run;                    /* 5. 三项一起更新 */
  s_led.dir     = pkt.dir;
  s_led.step_ms = step;
  s_led.tick    = HAL_GetTick();              /* 从这一刻重新计时 */

  App_StateChanged();                         /* 6. 刷屏 + 回传 */
}
''', caption='代码 5-7　校验与应用')
    h.h3('校验和手算三遍就不会忘')
    h.p('规则：把 `AA` 和它后面 4 个字节当普通数字加起来，只留最低两位十六进制。')
    h.table(
        ['想要的设置', 'RUN DIR STEP', '相加', 'CHECK', '完整包'],
        [
            ['运行 / 正向 / 300 ms', '01 00 2C 01', 'AA+01+00+2C+01 = 0xD8', 'D8', '`AA 01 00 2C 01 D8`'],
            ['暂停 / 正向 / 300 ms', '00 00 2C 01', 'AA+00+00+2C+01 = 0xD7', 'D7', '`AA 00 00 2C 01 D7`'],
            ['运行 / 反向 / 1000 ms', '01 01 E8 03', 'AA+01+01+E8+03 = 0x197 → 97', '97', '`AA 01 01 E8 03 97`'],
            ['暂停 / 反向 / 1000 ms', '00 01 E8 03', 'AA+00+01+E8+03 = 0x196 → 96', '96', '`AA 00 01 E8 03 96`'],
        ],
        widths=[4.6, 3.4, 5.2, 1.8, 4.6],
    )
    h.note('1000 ms 的步进字节是 `E8 03`（0x03E8），不是 `03 E8`。**低字节在前**是这里最容易错的地方，'
           '发反了会变成 0x03E8→0xE803=59395 ms，被范围检查丢掉（表现为"发包没反应"）。')

    h.h2('5.6 应用设置：暂停期间的修改也要生效')
    h.p('作业验收第 4 条："在暂停期间做出的修改，在启动后可以被正常执行。"'
        '这一条不需要额外代码——只要**收到包就写状态，不管当前是否在运行**。'
        '因为暂停时 `Led_Task()` 直接 return，只读不改，恢复后自然按新设置走。')
    h.p('唯一的细节是 `s_led.tick = HAL_GetTick()`：收到包时把计时起点清零，'
        '否则如果上一个间隔已经"欠"了很久，恢复运行时可能立刻跳一颗灯。')

    h.h2('5.7 串口反馈：中断发送 + 忙/待发')
    h.p('反馈要求用 `HAL_UART_Transmit_IT()`。它启动后立刻返回，CPU 在中断里逐个字节喂给串口。'
        '**同一个缓冲区在发送完成前不能被改写**，所以要处理"上一次还没发完，又要发一条"的情况：')
    h.code(r'''
static void Feedback_Send(void)
{
  int n;

  if (s_tx_busy) { s_tx_pending = 1u; return; }   /* 忙就只记一笔，别动缓冲区 */

  n = snprintf(s_fb_buf, FB_BUF_SIZE, "STATE=%s,DIR=%s,STEP=%u,LED=%u\r\n",
               s_led.running ? "RUN" : "PAUSE",
               s_led.dir ? "REV" : "FWD",
               (unsigned int)s_led.step_ms,
               (unsigned int)(s_led.led + 1u));
  if (n <= 0) return;
  if (n >= (int)FB_BUF_SIZE) n = (int)FB_BUF_SIZE - 1;

  s_tx_busy = 1u;
  if (HAL_UART_Transmit_IT(&huart1, (uint8_t *)s_fb_buf, (uint16_t)n) != HAL_OK) {
    s_tx_busy = 0u;
    s_tx_pending = 1u;
  }
}

void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance == USART1) s_tx_busy = 0u;
}
''', caption='代码 5-8　反馈发送与完成回调')
    h.p('主循环里的第 5 步负责"补发"：`if (s_tx_pending && !s_tx_busy) { s_tx_pending = 0; Feedback_Send(); }`。'
        '这样即使连续按了三次键，也只会多发一条最新状态，不会覆盖正在发的内容。')
    h.note('常见错误：不判断 `s_tx_busy` 直接 `snprintf` 到同一个缓冲区。'
           '结果是串口上出现半条旧消息 + 半条新消息的"拼接怪"，很难看出是代码问题。')

    h.h2('5.8 OLED：行缓存，只重画变化的行')
    h.p('软件 I²C 是"用程序翻转 IO"模拟时序，一次刷整屏（1024 字节）约几毫秒。'
        '如果每轮主循环都刷，一是浪费 CPU，二是屏幕会闪。做法是**缓存四行文本，只有内容变了才重画那一行**：')
    h.code(r'''
static void Oled_Refresh(void)
{
  char    line[17];
  uint8_t i, c;
  size_t  len;

  for (i = 0u; i < 4u; i++) {
    switch (i) {
      case 0u: (void)snprintf(line, sizeof(line), "STATE: %s", s_led.running ? "RUN" : "PAUSE"); break;
      case 1u: (void)snprintf(line, sizeof(line), "DIR: %s",   s_led.dir ? "REV" : "FWD");       break;
      case 2u: (void)snprintf(line, sizeof(line), "STEP:%04ums", (unsigned int)s_led.step_ms);   break;
      default: (void)snprintf(line, sizeof(line), "LED: %u", (unsigned int)(s_led.led + 1u));    break;
    }

    len = strlen(line);
    for (c = (uint8_t)len; c < 16u; c++) line[c] = ' ';   /* 补空格，盖掉旧字符 */
    line[16] = '\0';

    if (strcmp(line, s_oled_line[i]) != 0) {              /* 变了才画 */
      OLED_ShowString((uint8_t)(i + 1u), 1u, line);
      (void)strncpy(s_oled_line[i], line, sizeof(s_oled_line[i]) - 1u);
      s_oled_line[i][sizeof(s_oled_line[i]) - 1u] = '\0';
    }
  }
}
''', caption='代码 5-9　OLED 刷新（含补空格）')
    h.p('为什么一定要补空格：`STATE: RUN`（10 字符）变成 `STATE: PAUSE`（12 字符）没问题，'
        '但反过来 PAUSE→RUN 时，如果只写 10 个字符，屏幕上会残留 "SE" 两个字，变成 `STATE: RUNSE`。'
        '**补空格到固定 16 列**是最省事的解决办法（另一种是刷之前先清这一行）。')
    h.p('`STEP:%04ums` 会显示成 `STEP:0300ms`（4 位、不足补 0），正好占满第 3 行。')

    h.h2('5.9 中断里到底做了什么（汇总）')
    h.table(
        ['中断源', '回调', '只做这几件事', '耗时'],
        [
            ['PA11/PA12 下降沿', '`HAL_GPIO_EXTI_Callback`', '记录边沿时刻、置标志', '几微秒'],
            ['USART1 收满 1 字节', '`HAL_UART_RxCpltCallback`', '存入环形缓冲区、重开接收', '几微秒'],
            ['USART1 发送完成', '`HAL_UART_TxCpltCallback`', '清 `s_tx_busy`', '几微秒'],
        ],
        widths=[4.2, 6.4, 6.0, 2.4],
    )
    h.p('这就是"中断只做必要的事"的具体样子：**三个回调加起来不到 20 行有效代码**，'
        '没有任何延时、没有刷屏、没有字符串格式化。')
