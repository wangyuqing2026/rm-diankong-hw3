/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    main.c
  * @brief   电控组第三次培训作业
  *          流水灯 + 按键(外部中断) + 串口数据包(HEX) + OLED 状态显示 + 串口反馈
  *
  * 数据包（6 字节）： AA  RUN  DIR  STEP_L  STEP_H  CHECK
  *   RUN   00=暂停 01=运行
  *   DIR   00=正向 01=反向
  *   STEP  100~2000ms，小端（低字节在前）
  *   CHECK (AA+RUN+DIR+STEP_L+STEP_H) % 256
  *
  * 反馈（文本）： STATE=RUN,DIR=FWD,STEP=300,LED=1\r\n
  ******************************************************************************
  */
/* USER CODE END Header */

/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "gpio.h"
#include "usart.h"
#include "OLED.h"

#include <stdio.h>
#include <string.h>

/* Private define ------------------------------------------------------------*/
#define LED_NUM           3u      /* 实际接了几颗就写几（1~4）：3 颗接 PA0~PA2 */
#define KEY_DEBOUNCE_MS   20u     /* 按键消抖时间 */
#define RX_RING_SIZE      64u     /* 串口接收环形缓冲区大小（2 的幂最好） */

#define PKT_HEADER        0xAAu   /* 帧头 */
#define PKT_SIZE          6u      /* 整包长度 */
#define STEP_MIN_MS       100u    /* 间隔下限 */
#define STEP_MAX_MS       2000u   /* 间隔上限 */

#define FB_BUF_SIZE       48u     /* 反馈字符串缓冲区 */

/* Private typedef -----------------------------------------------------------*/
/* 收到的数据包：用结构体描述"每个字节是什么"，加 packed 保证正好 6 字节 */
typedef struct __attribute__((packed))
{
    uint8_t  header;      /* 0xAA */
    uint8_t  run;         /* 0/1 */
    uint8_t  dir;         /* 0/1 */
    uint16_t step_ms;     /* 小端存放，STM32 上可直接使用 */
    uint8_t  check;       /* 校验和 */
} CmdPacket_t;

_Static_assert(sizeof(CmdPacket_t) == PKT_SIZE, "数据包结构体必须是 6 字节");

/* 流水灯的完整运行状态：效果、OLED、串口反馈都从这一份状态里读 */
typedef struct
{
    uint8_t  running;     /* 1 运行，0 暂停 */
    uint8_t  dir;         /* 0 正向(1->2->3->4)，1 反向 */
    uint16_t step_ms;     /* 相邻 LED 切换间隔 */
    uint8_t  led;         /* 当前点亮的 LED 下标 0~LED_NUM-1 */
    uint32_t tick;        /* 上一次切灯的时刻(HAL_GetTick) */
} LedState_t;

/* 一个按键的上下文：引脚、中断打下的标记、消抖用的时间戳 */
typedef struct
{
    GPIO_TypeDef      *port;
    uint16_t           pin;
    volatile uint8_t  *edge_flag;   /* 中断里置 1，主循环处理完清 0 */
    volatile uint32_t *edge_tick;   /* 中断发生的时刻 */
    uint8_t            locked;      /* 已处理这次按下，等待松开 */
} KeyCtx_t;

/* Private variables ---------------------------------------------------------*/
/* huart1 定义在 usart.c，这里通过 usart.h 的 extern 使用 */

/* ---- 流水灯状态（PV 区：必须是全局/静态，中断和主循环都要访问） ---- */
static LedState_t s_led = {
    .running = 1u,      /* 上电就运行 */
    .dir     = 0u,      /* 正向 */
    .step_ms = 300u,    /* 300ms 切换一次 */
    .led     = 0u,      /* 先点 LED1 */
    .tick    = 0u,
};

/* ---- 按键事件：由 EXTI 回调写，主循环读 ---- */
static volatile uint8_t  s_key1_edge = 0u;
static volatile uint32_t s_key1_tick = 0u;
static volatile uint8_t  s_key2_edge = 0u;
static volatile uint32_t s_key2_tick = 0u;

/* ---- 两个按键的上下文（变量必须在 PV 区，初始化放在 main 之前的常量里） ---- */
static KeyCtx_t s_key1 = { KEY1_GPIO_Port, KEY1_Pin, &s_key1_edge, &s_key1_tick, 0u };
static KeyCtx_t s_key2 = { KEY2_GPIO_Port, KEY2_Pin, &s_key2_edge, &s_key2_tick, 0u };

/* ---- 串口接收：中断只往环形缓冲区塞字节 ---- */
static uint8_t           s_rx_byte = 0u;
static uint8_t           s_rx_ring[RX_RING_SIZE];
static volatile uint16_t s_rx_head = 0u;   /* 中断写 */
static volatile uint16_t s_rx_tail = 0u;   /* 主循环写 */
static volatile uint32_t s_rx_drop = 0u;   /* 缓冲区满丢掉的字节数（调试用） */

/* ---- 拆包状态机 ---- */
static uint8_t s_pkt_buf[PKT_SIZE];
static uint8_t s_pkt_len = 0u;

/* ---- 串口反馈 ---- */
static char              s_fb_buf[FB_BUF_SIZE];
static volatile uint8_t  s_tx_busy = 0u;
static uint8_t           s_tx_pending = 0u;

/* ---- OLED 行缓存：内容没变就不重画 ---- */
static char    s_oled_line[4][17];
static uint8_t s_oled_dirty = 1u;

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);

static void     Led_Apply(void);
static void     Led_Task(void);
static uint8_t  Key_Scan(KeyCtx_t *key);
static void     Uart_Poll(void);
static uint8_t  Ring_Pop(uint8_t *byte);
static void     Packet_Handle(const uint8_t *raw);
static void     App_StateChanged(void);
static void     Feedback_Send(void);
static void     Oled_Refresh(void);

/* USER CODE BEGIN 0 */

/* USER CODE END 0 */

/**
  * @brief  主循环跑一轮：五个任务各做一小步就返回，谁都不许阻塞
  * @note   单独抽成函数，方便在电脑上做离线仿真（见 sim/ 目录）
  */
static void App_LoopOnce(void)
{
  /* 1) 按键：消抖确认后改状态 */
  if (Key_Scan(&s_key1))
  {
    s_led.dir = (uint8_t)(1u - s_led.dir);   /* 切换方向 */
    App_StateChanged();
  }
  if (Key_Scan(&s_key2))
  {
    s_led.running = (uint8_t)(1u - s_led.running);   /* 暂停/继续 */
    if (s_led.running)
    {
      s_led.tick = HAL_GetTick();          /* 恢复后从现在重新计时 */
    }
    App_StateChanged();
  }

  /* 2) 串口：把缓冲区里的字节拆成数据包并处理 */
  Uart_Poll();

  /* 3) 流水灯：到点才换灯，不阻塞 */
  Led_Task();

  /* 4) OLED：只有内容变化才重画 */
  if (s_oled_dirty)
  {
    s_oled_dirty = 0u;
    Oled_Refresh();
  }

  /* 5) 反馈：上一次发完再补发待发的一条 */
  if (s_tx_pending && !s_tx_busy)
  {
    s_tx_pending = 0u;
    Feedback_Send();
  }
}

/**
  * @brief  程序入口
  */
int main(void)
{
  /* USER CODE BEGIN 1 */

  /* USER CODE END 1 */

  /* MCU 配置 -------------------------------------------------------------*/
  HAL_Init();
  SystemClock_Config();

  /* 外设初始化 -----------------------------------------------------------*/
  MX_GPIO_Init();
  MX_USART1_UART_Init();

  /* USER CODE BEGIN 2 */
  OLED_Init();                    /* 软件 I²C 驱动内部自己配置 PB0/PB1 */
  Led_Apply();                    /* 先按初始状态点亮 LED1 */
  Oled_Refresh();                 /* 首屏 */
  s_led.tick = HAL_GetTick();

  /* 启动串口中断接收：每次收 1 字节，收满进回调，回调里再续一次 */
  if (HAL_UART_Receive_IT(&huart1, &s_rx_byte, 1u) != HAL_OK)
  {
    Error_Handler();
  }

  Feedback_Send();                /* 上电先报一次状态，方便确认串口通了 */
  /* USER CODE END 2 */

  /* 主循环：一轮只做五件小事，全部是非阻塞的 */
  while (1)
  {
    /* USER CODE BEGIN 3 */
    App_LoopOnce();
    /* USER CODE END 3 */
  }
}

/**
  * @brief 系统时钟：HSE 8MHz -> PLL x9 -> 72MHz
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState       = RCC_HSE_ON;
  RCC_OscInitStruct.HSEPredivValue = RCC_HSE_PREDIV_DIV1;
  RCC_OscInitStruct.HSIState       = RCC_HSI_ON;
  RCC_OscInitStruct.PLL.PLLState   = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource  = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLMUL     = RCC_PLL_MUL9;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }

  RCC_ClkInitStruct.ClockType      = RCC_CLOCKTYPE_HCLK | RCC_CLOCKTYPE_SYSCLK
                                   | RCC_CLOCKTYPE_PCLK1 | RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource   = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider  = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV2;   /* APB1 最高 36MHz */
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_2) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* ======================== 1. 流水灯 ======================================= */

/**
  * @brief 按 s_led.led 点亮唯一一颗 LED，其余熄灭
  */
static void Led_Apply(void)
{
  /* 数组固定 4 项，循环只走 LED_NUM 项：这样 LED_NUM 改 1~4 都不用在数组里增删 */
  static const uint16_t pins[4] = { LED1_Pin, LED2_Pin, LED3_Pin, LED4_Pin };
  uint8_t i;

  for (i = 0u; i < LED_NUM; i++)
  {
    HAL_GPIO_WritePin(LED1_GPIO_Port, pins[i],
                      (i == s_led.led) ? GPIO_PIN_SET : GPIO_PIN_RESET);
  }
}

/**
  * @brief 到点就换下一颗；暂停时什么都不做，保留当前灯
  */
static void Led_Task(void)
{
  uint32_t now;

  if (!s_led.running)
  {
    return;                                  /* 暂停：保持现状 */
  }

  now = HAL_GetTick();
  if ((uint32_t)(now - s_led.tick) < s_led.step_ms)
  {
    return;                                  /* 还没到点 */
  }

  /* 累加而不是直接赋值，长期运行不累积误差 */
  s_led.tick += s_led.step_ms;
  if ((uint32_t)(now - s_led.tick) >= s_led.step_ms)
  {
    s_led.tick = now;                        /* 主循环被拖慢过，别补跳一串 */
  }

  if (s_led.dir == 0u)
  {
    s_led.led = (uint8_t)((s_led.led + 1u) % LED_NUM);
  }
  else
  {
    s_led.led = (uint8_t)((s_led.led + LED_NUM - 1u) % LED_NUM);
  }

  Led_Apply();
  s_oled_dirty = 1u;                         /* LED 编号变了，屏幕要更新 */
}

/* ======================== 2. 按键（EXTI + 消抖）========================== */

/**
  * @brief 扫描一个按键：中断只打标记，这里做消抖和"松开确认"
  * @retval 1 = 确认了一次有效按下
  */
static uint8_t Key_Scan(KeyCtx_t *key)
{
  uint32_t now;

  if (key->locked)
  {
    /* 已经算过这次按下，等松手才允许下一次 */
    if (HAL_GPIO_ReadPin(key->port, key->pin) == GPIO_PIN_SET)
    {
      key->locked = 0u;
    }
    return 0u;
  }

  if (*(key->edge_flag) == 0u)
  {
    return 0u;
  }

  now = HAL_GetTick();
  if ((uint32_t)(now - *(key->edge_tick)) < KEY_DEBOUNCE_MS)
  {
    return 0u;                               /* 还在抖，等电平稳住 */
  }

  *(key->edge_flag) = 0u;
  if (HAL_GPIO_ReadPin(key->port, key->pin) == GPIO_PIN_RESET)
  {
    key->locked = 1u;                        /* 确认按下 */
    return 1u;
  }
  return 0u;                                 /* 抖动造成的假边沿 */
}

/* ======================== 3. 串口接收与拆包 ============================== */

/**
  * @brief 从环形缓冲区取一个字节
  * @retval 1 = 取到了
  */
static uint8_t Ring_Pop(uint8_t *byte)
{
  if (s_rx_tail == s_rx_head)
  {
    return 0u;
  }
  *byte = s_rx_ring[s_rx_tail];
  s_rx_tail = (uint16_t)((s_rx_tail + 1u) % RX_RING_SIZE);
  return 1u;
}

/**
  * @brief 逐字节喂给状态机：先找帧头 AA，再攒够 6 字节交给 Packet_Handle
  */
static void Uart_Poll(void)
{
  uint8_t b;

  while (Ring_Pop(&b))
  {
    if (s_pkt_len == 0u)
    {
      if (b == PKT_HEADER)                 /* 不是帧头就丢弃，重新对齐 */
      {
        s_pkt_buf[s_pkt_len++] = b;
      }
    }
    else
    {
      s_pkt_buf[s_pkt_len++] = b;
      if (s_pkt_len >= PKT_SIZE)
      {
        Packet_Handle(s_pkt_buf);
        s_pkt_len = 0u;
      }
    }
  }
}

/**
  * @brief 校验并应用一整包
  * @note  帧头、校验和、取值范围任何一项不通过，整包丢弃、状态不变
  */
static void Packet_Handle(const uint8_t *raw)
{
  CmdPacket_t pkt;
  uint8_t     sum;
  uint16_t    step;

  memcpy(&pkt, raw, PKT_SIZE);             /* 避免直接对未对齐地址取 uint16_t */

  if (pkt.header != PKT_HEADER)
  {
    return;
  }

  /* 校验和：把前 5 个字节按原样相加，取低 8 位 */
  sum = (uint8_t)(raw[0] + raw[1] + raw[2] + raw[3] + raw[4]);
  if (sum != pkt.check)
  {
    return;
  }

  if ((pkt.run > 1u) || (pkt.dir > 1u))
  {
    return;
  }

  step = pkt.step_ms;
  if ((step < STEP_MIN_MS) || (step > STEP_MAX_MS))
  {
    return;
  }

  /* 三项一起更新：暂停时也要生效，恢复后直接用新设置跑 */
  s_led.running = pkt.run;
  s_led.dir     = pkt.dir;
  s_led.step_ms = step;
  s_led.tick    = HAL_GetTick();

  App_StateChanged();
}

/**
  * @brief 状态变了：刷新 OLED 并回传一条反馈
  */
static void App_StateChanged(void)
{
  s_oled_dirty = 1u;
  Feedback_Send();
}

/* ======================== 4. 串口反馈（中断发送）========================= */

/**
  * @brief 把当前状态格式化成一行文本，用 HAL_UART_Transmit_IT 发出去
  * @note  上一包没发完就只记一个"待发"标记，等发完再发，避免改写正在发送的缓冲区
  */
static void Feedback_Send(void)
{
  int n;

  if (s_tx_busy)
  {
    s_tx_pending = 1u;
    return;
  }

  n = snprintf(s_fb_buf, FB_BUF_SIZE, "STATE=%s,DIR=%s,STEP=%u,LED=%u\r\n",
               (s_led.running != 0u) ? "RUN" : "PAUSE",
               (s_led.dir != 0u) ? "REV" : "FWD",
               (unsigned int)s_led.step_ms,
               (unsigned int)(s_led.led + 1u));
  if (n <= 0)
  {
    return;
  }
  if (n >= (int)FB_BUF_SIZE)
  {
    n = (int)FB_BUF_SIZE - 1;
  }

  s_tx_busy = 1u;
  if (HAL_UART_Transmit_IT(&huart1, (uint8_t *)s_fb_buf, (uint16_t)n) != HAL_OK)
  {
    s_tx_busy = 0u;
    s_tx_pending = 1u;
  }
}

/* ======================== 5. OLED 显示 =================================== */

/**
  * @brief 四行状态：只在内容变化时重画对应行（软件 I²C 刷屏比较慢）
  */
static void Oled_Refresh(void)
{
  char    line[17];
  uint8_t i;
  uint8_t c;
  size_t  len;

  for (i = 0u; i < 4u; i++)
  {
    switch (i)
    {
      case 0u:
        (void)snprintf(line, sizeof(line), "STATE: %s",
                       (s_led.running != 0u) ? "RUN" : "PAUSE");
        break;
      case 1u:
        (void)snprintf(line, sizeof(line), "DIR: %s",
                       (s_led.dir != 0u) ? "REV" : "FWD");
        break;
      case 2u:
        (void)snprintf(line, sizeof(line), "STEP:%04ums", (unsigned int)s_led.step_ms);
        break;
      default:
        (void)snprintf(line, sizeof(line), "LED: %u", (unsigned int)(s_led.led + 1u));
        break;
    }

    /* 补空格到 16 列，把这一行上一次的旧字符盖掉 */
    len = strlen(line);
    for (c = (uint8_t)len; c < 16u; c++)
    {
      line[c] = ' ';
    }
    line[16] = '\0';

    if (strcmp(line, s_oled_line[i]) != 0)
    {
      OLED_ShowString((uint8_t)(i + 1u), 1u, line);
      (void)strncpy(s_oled_line[i], line, sizeof(s_oled_line[i]) - 1u);
      s_oled_line[i][sizeof(s_oled_line[i]) - 1u] = '\0';
    }
  }
}

/* ======================== 6. 中断回调（只记录，不处理）=================== */

/**
  * @brief 外部中断回调：记录"哪个键、什么时候"
  */
void HAL_GPIO_EXTI_Callback(uint16_t GPIO_Pin)
{
  uint32_t now = HAL_GetTick();

  if (GPIO_Pin == KEY1_Pin)
  {
    s_key1_tick = now;      /* 抖动会连续进这里，时间戳被不停刷新 */
    s_key1_edge = 1u;
  }
  else if (GPIO_Pin == KEY2_Pin)
  {
    s_key2_tick = now;
    s_key2_edge = 1u;
  }
}

/**
  * @brief 串口收满 1 字节：塞进环形缓冲区，再续一次接收
  */
void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance == USART1)
  {
    uint16_t next = (uint16_t)((s_rx_head + 1u) % RX_RING_SIZE);

    if (next != s_rx_tail)
    {
      s_rx_ring[s_rx_head] = s_rx_byte;
      s_rx_head = next;
    }
    else
    {
      s_rx_drop++;            /* 满了就丢，主循环跟不上时才会发生 */
    }

    (void)HAL_UART_Receive_IT(&huart1, &s_rx_byte, 1u);
  }
}

/**
  * @brief 串口发送完成：清忙标志，允许下一条反馈
  */
void HAL_UART_TxCpltCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance == USART1)
  {
    s_tx_busy = 0u;
  }
}

/**
  * @brief 串口出错（溢出 ORE / 帧错误 / 噪声）：清标志并重新开接收
  * @note  HAL 在出错时会自动停止接收（RXNEIE 被清掉），不重新开的话
  *        接收就永久停了——表现是"只能收一次"或"发什么都没反应"。
  */
void HAL_UART_ErrorCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance == USART1)
  {
    if (huart->ErrorCode & HAL_UART_ERROR_ORE)
    {
      __HAL_UART_CLEAR_OREFLAG(huart);      /* 先读 SR 再读 DR，清掉溢出标志 */
    }
    if (huart->ErrorCode & HAL_UART_ERROR_FE)
    {
      __HAL_UART_CLEAR_FEFLAG(huart);
    }
    if (huart->ErrorCode & HAL_UART_ERROR_NE)
    {
      __HAL_UART_CLEAR_NEFLAG(huart);
    }
    huart->ErrorCode = HAL_UART_ERROR_NONE;

    s_rx_drop++;                            /* 记一笔，方便以后观察 */
    (void)HAL_UART_Receive_IT(&huart1, &s_rx_byte, 1u);
  }
}

/**
  * @brief 错误处理：点亮全部 LED 并停在死循环，便于发现初始化失败
  */
void Error_Handler(void)
{
  __disable_irq();
  while (1)
  {
  }
}

#ifdef USE_FULL_ASSERT
void assert_failed(uint8_t *file, uint32_t line)
{
  (void)file;
  (void)line;
}
#endif

/* USER CODE END 4 */
