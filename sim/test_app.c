// 离线仿真：把真实的 main.c 编到 PC 上，用假的 HAL 驱动它跑，
// 验证按键消抖、数据包解析、流水灯时序、OLED 内容与反馈格式。
// 编译（在 diankong3/sim 目录下）：
//   gcc -std=gnu11 -I stub -I ../firmware/Core/Inc -o test_app.exe test_app.c
// 运行：./test_app.exe
#define main firmware_main
#include "../firmware/Core/Src/main.c"
#undef main

#include <stdio.h>
#include <string.h>

/* ---------------- 桩件状态 ---------------- */
static uint32_t      g_tick = 0u;
static GPIO_PinState g_key1 = GPIO_PIN_SET;
static GPIO_PinState g_key2 = GPIO_PIN_SET;
static int           g_led[4] = {0, 0, 0, 0};
static char          g_oled[4][17];
static char          g_tx[64];
static int           g_tx_len = 0;

static int g_fail = 0;
static int g_pass = 0;

#define CHECK(cond, msg)                                                          \
    do {                                                                          \
        if (cond) { g_pass++; printf("  PASS  %s\n", msg); }                      \
        else      { g_fail++; printf("  FAIL  %s  (line %d)\n", msg, __LINE__); }  \
    } while (0)

/* ---------------- HAL 桩件 ---------------- */
HAL_StatusTypeDef HAL_Init(void) { return HAL_OK; }
uint32_t HAL_GetTick(void) { return g_tick; }

void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state)
{
    (void)port;
    static const uint16_t pins[4] = {GPIO_PIN_0, GPIO_PIN_1, GPIO_PIN_2, GPIO_PIN_3};
    for (int i = 0; i < 4; i++) {
        if (pin == pins[i]) { g_led[i] = (state == GPIO_PIN_SET) ? 1 : 0; }
    }
}

GPIO_PinState HAL_GPIO_ReadPin(GPIO_TypeDef *port, uint16_t pin)
{
    (void)port;
    if (pin == GPIO_PIN_11) { return g_key1; }
    if (pin == GPIO_PIN_12) { return g_key2; }
    return GPIO_PIN_SET;
}

HAL_StatusTypeDef HAL_UART_Receive_IT(UART_HandleTypeDef *h, uint8_t *p, uint16_t len)
{
    (void)h; (void)p; (void)len;
    return HAL_OK;
}

HAL_StatusTypeDef HAL_UART_Transmit_IT(UART_HandleTypeDef *h, uint8_t *p, uint16_t len)
{
    (void)h;
    if (g_tx_len != 0) { return HAL_BUSY; }   /* 上一次还没"发完" */
    memcpy(g_tx, p, len);
    g_tx[len] = '\0';
    g_tx_len = (int)len;
    return HAL_OK;
}

HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *s) { (void)s; return HAL_OK; }
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *s, uint32_t l) { (void)s; (void)l; return HAL_OK; }

void OLED_Init(void) {}
void OLED_Clear(void) { memset(g_oled, 0, sizeof(g_oled)); }
void OLED_ShowNum(uint8_t Line, uint8_t Column, uint32_t Number, uint8_t Length)
{
    (void)Line; (void)Column; (void)Number; (void)Length;
}
void OLED_ShowString(uint8_t Line, uint8_t Column, char *String)
{
    (void)Column;
    if (Line >= 1 && Line <= 4) {
        memset(g_oled[Line - 1], 0, 17);
        strncpy(g_oled[Line - 1], String, 16);
    }
}

/* 这两个原本由 gpio.c / usart.c 提供 */
UART_HandleTypeDef huart1;
void MX_GPIO_Init(void) {}
void MX_USART1_UART_Init(void) { huart1.Instance = USART1; }

/* ---------------- 仿真辅助 ---------------- */
static void tx_finish(void)      /* 模拟"发送完成中断" */
{
    g_tx_len = 0;
    HAL_UART_TxCpltCallback(&huart1);
}

static void loop_once(void)      /* 主循环跑一轮 */
{
    App_LoopOnce();
    if (s_tx_busy) { tx_finish(); }   /* 桩件不会自己发完，这里手动收尾 */
}

static void advance(uint32_t ms) /* 时间前进 ms 毫秒，每毫秒跑一轮 */
{
    for (uint32_t i = 0; i < ms; i++) {
        g_tick += 1u;
        loop_once();
    }
}

static void feed(const uint8_t *bytes, int n)
{
    for (int i = 0; i < n; i++) {
        s_rx_byte = bytes[i];
        HAL_UART_RxCpltCallback(&huart1);
    }
    loop_once();
}

static void boot(void)
{
    huart1.Instance = USART1;
    OLED_Init();
    Led_Apply();
    Oled_Refresh();
    s_led.tick = HAL_GetTick();
    HAL_UART_Receive_IT(&huart1, &s_rx_byte, 1u);
    Feedback_Send();
    tx_finish();
}

/* 按住 KEY1 / KEY2 一段时间再松开；中间不会重复触发 */
static void key1_press(uint32_t hold_ms)
{
    g_key1 = GPIO_PIN_RESET;
    s_key1_edge = 1u;
    s_key1_tick = g_tick;
    advance(hold_ms);
    g_key1 = GPIO_PIN_SET;
    advance(2u);
}

static void key2_press(uint32_t hold_ms)
{
    g_key2 = GPIO_PIN_RESET;
    s_key2_edge = 1u;
    s_key2_tick = g_tick;
    advance(hold_ms);
    g_key2 = GPIO_PIN_SET;
    advance(2u);
}

/* 作业文档里的 4 个标准包 */
static const uint8_t PKT_RUN_FWD_300[6]    = {0xAA, 0x01, 0x00, 0x2C, 0x01, 0xD8};
static const uint8_t PKT_PAUSE_FWD_300[6]  = {0xAA, 0x00, 0x00, 0x2C, 0x01, 0xD7};
static const uint8_t PKT_RUN_REV_300[6]    = {0xAA, 0x01, 0x01, 0x2C, 0x01, 0xD9};
static const uint8_t PKT_PAUSE_REV_1000[6] = {0xAA, 0x00, 0x01, 0xE8, 0x03, 0x96};

/* ---------------- 测试 ---------------- */
int main(void)
{
    printf("== 1. 上电初始状态 ==\n");
    boot();
    CHECK(s_led.running == 1u && s_led.dir == 0u && s_led.step_ms == 300u, "初始：运行/正向/300ms");
    CHECK(g_led[0] == 1 && g_led[1] == 0 && g_led[2] == 0 && g_led[3] == 0, "初始只点亮 LED1");
    CHECK(strcmp(g_oled[0], "STATE: RUN      ") == 0, "OLED 第1行 STATE: RUN");
    CHECK(strcmp(g_oled[1], "DIR: FWD        ") == 0, "OLED 第2行 DIR: FWD");
    CHECK(strcmp(g_oled[2], "STEP:0300ms     ") == 0, "OLED 第3行 STEP:0300ms");
    CHECK(strcmp(g_oled[3], "LED: 1          ") == 0, "OLED 第4行 LED: 1");
    CHECK(strcmp(g_tx, "STATE=RUN,DIR=FWD,STEP=300,LED=1\r\n") == 0, "上电反馈格式正确");

    printf("\n== 2. 流水灯按 300ms 切换、正向环绕 ==\n");
    advance(299u);
    CHECK(g_led[0] == 1, "299ms 还没到点，仍是 LED1");
    advance(1u);
    CHECK(g_led[1] == 1 && g_led[0] == 0, "300ms 切到 LED2");
    advance(900u);
    CHECK(g_led[0] == 1, "四颗一轮后回到 LED1");
    CHECK(strcmp(g_oled[3], "LED: 1          ") == 0, "OLED 的 LED 编号跟着变");

    printf("\n== 3. 作业给出的 4 个示例数据包 ==\n");
    feed(PKT_PAUSE_FWD_300, 6);
    CHECK(s_led.running == 0u && s_led.step_ms == 300u, "暂停包生效：停止、间隔 300");
    feed(PKT_RUN_REV_300, 6);
    CHECK(s_led.running == 1u && s_led.dir == 1u, "反向包生效：运行、反向");
    feed(PKT_PAUSE_REV_1000, 6);
    CHECK(s_led.running == 0u && s_led.dir == 1u && s_led.step_ms == 1000u, "1000ms 反向暂停包生效");
    feed(PKT_RUN_FWD_300, 6);
    CHECK(s_led.running == 1u && s_led.dir == 0u && s_led.step_ms == 300u, "恢复为运行/正向/300");

    printf("\n== 4. 校验和 / 帧头 / 取值范围不合法时整包丢弃 ==\n");
    LedState_t before = s_led;
    const uint8_t bad_check[6]  = {0xAA, 0x01, 0x00, 0x2C, 0x01, 0xD9};   /* 应为 D8 */
    const uint8_t bad_header[6] = {0x55, 0x01, 0x00, 0x2C, 0x01, 0x36};
    const uint8_t bad_step[6]   = {0xAA, 0x01, 0x00, 0x32, 0x00, 0xDD};   /* 50ms 越界 */
    const uint8_t bad_run[6]    = {0xAA, 0x02, 0x00, 0x2C, 0x01, 0xDA};   /* RUN=2 越界 */

    feed(bad_check, 6);
    CHECK(memcmp(&before, &s_led, sizeof(before)) == 0, "校验和错误：状态不变");
    feed(bad_header, 6);
    CHECK(memcmp(&before, &s_led, sizeof(before)) == 0, "帧头错误：状态不变");
    feed(bad_step, 6);
    CHECK(memcmp(&before, &s_led, sizeof(before)) == 0, "间隔 50ms 越界：状态不变");
    feed(bad_run, 6);
    CHECK(memcmp(&before, &s_led, sizeof(before)) == 0, "RUN=02 越界：状态不变");

    printf("\n== 5. 重同步：前面有垃圾字节也能收到正确包 ==\n");
    const uint8_t junk[4] = {0x11, 0x22, 0x33, 0xAA};
    feed(junk, 4);
    CHECK(s_pkt_len == 1u, "看到帧头后开始攒包");
    const uint8_t tail[5] = {0x00, 0x00, 0xE8, 0x03, 0x95};   /* 暂停/正向/1000ms */
    feed(tail, 5);
    CHECK(s_pkt_len == 0u, "收满 6 字节后清空状态机");
    CHECK(s_led.running == 0u && s_led.step_ms == 1000u, "垃圾字节后的合法包仍被应用");

    printf("\n== 6. 暂停时 LED 不动，但按键和串口仍有效 ==\n");
    feed(PKT_PAUSE_FWD_300, 6);
    uint8_t led_before = s_led.led;
    advance(5000u);
    CHECK(s_led.led == led_before && g_led[led_before] == 1, "暂停 5 秒：LED 保持不动");
    CHECK(strcmp(g_oled[0], "STATE: PAUSE    ") == 0, "暂停时 OLED 显示 PAUSE");
    key2_press(60u);
    CHECK(s_led.running == 1u, "暂停时按键能把流水灯继续起来");
    CHECK(strstr(g_tx, "STATE=RUN") != NULL, "按键后同步回传反馈");
    advance(300u);
    CHECK(s_led.led != led_before, "继续后按原方向接着走");

    printf("\n== 7. 按键消抖：抖动不算、一次按下只触发一次 ==\n");
    feed(PKT_RUN_FWD_300, 6);
    uint8_t dir0 = s_led.dir;
    for (int i = 0; i < 4; i++) {          /* 20ms 内连续 4 个下降沿 */
        s_key1_edge = 1u;
        s_key1_tick = g_tick;
        advance(5u);
    }
    CHECK(s_led.dir == dir0, "抖动期间不动作");
    g_key1 = GPIO_PIN_RESET;               /* 电平稳住，再等 20ms */
    advance(KEY_DEBOUNCE_MS + 1u);
    CHECK(s_led.dir == (uint8_t)(1u - dir0), "稳定 20ms 后确认一次按下，方向翻转");
    s_key1_edge = 1u;                      /* 按住不放又抖了一下 */
    s_key1_tick = g_tick;
    advance(KEY_DEBOUNCE_MS + 1u);
    CHECK(s_led.dir == (uint8_t)(1u - dir0), "按住不放不会重复触发");
    g_key1 = GPIO_PIN_SET;
    advance(2u);
    key1_press(60u);
    CHECK(s_led.dir == dir0, "松开后再按，能再次翻转");

    printf("\n== 8. 方向反转后从当前灯往回走 ==\n");
    feed(PKT_RUN_REV_300, 6);
    uint8_t cur = s_led.led;
    advance(300u);
    CHECK(s_led.led == (uint8_t)((cur + LED_NUM - 1u) % LED_NUM), "反向：下标 -1");

    printf("\n== 9. 反馈不覆盖正在发送的缓冲区 ==\n");
    feed(PKT_PAUSE_FWD_300, 6);
    g_tx_len = 3;                      /* 人为让发送保持"忙" */
    s_tx_busy = 1u;
    char snapshot[64];
    strcpy(snapshot, g_tx);

    /* 手动模拟一次按键确认：这里不调用 tx_finish，让"忙"一直保持 */
    g_key2 = GPIO_PIN_RESET;
    s_key2_edge = 1u;
    s_key2_tick = g_tick;
    g_tick += KEY_DEBOUNCE_MS + 1u;
    App_LoopOnce();

    CHECK(strcmp(snapshot, g_tx) == 0, "忙时不改写正在发送的内容");
    CHECK(s_tx_pending == 1u, "只记录待发标记");

    tx_finish();                       /* 发送完成 */
    loop_once();
    CHECK(strstr(g_tx, "STATE=RUN") != NULL, "发完后补发最新状态");

    printf("\n================ %d passed, %d failed ================\n", g_pass, g_fail);
    return g_fail == 0 ? 0 : 1;
}
