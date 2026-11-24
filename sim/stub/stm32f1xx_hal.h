// 离线仿真用的 HAL 桩件：只保留 main.c 需要的类型与函数原型，
// 让同一份 main.c 能在 PC 上编译，从而验证逻辑而不必接板子。
#ifndef STUB_STM32F1XX_HAL_H
#define STUB_STM32F1XX_HAL_H

#include <stdint.h>
#include <stddef.h>

typedef enum { HAL_OK = 0, HAL_ERROR, HAL_BUSY, HAL_TIMEOUT } HAL_StatusTypeDef;
typedef enum { GPIO_PIN_RESET = 0, GPIO_PIN_SET } GPIO_PinState;

typedef struct { int dummy; } GPIO_TypeDef;
typedef struct { int dummy; } USART_TypeDef;
typedef struct { USART_TypeDef *Instance; uint32_t ErrorCode; } UART_HandleTypeDef;
typedef struct { int dummy; } DMA_HandleTypeDef;   /* 选做：仿真里只要有个类型就行 */

/* 串口错误码（仿真里只用得上这几个） */
#define HAL_UART_ERROR_NONE 0u
#define HAL_UART_ERROR_PE   1u
#define HAL_UART_ERROR_NE   2u
#define HAL_UART_ERROR_FE   4u
#define HAL_UART_ERROR_ORE  8u

/* 真实 HAL 里这几个宏要去读 SR/DR 清标志；仿真没有寄存器，空操作即可 */
#define __HAL_UART_CLEAR_OREFLAG(h) ((void)(h))
#define __HAL_UART_CLEAR_FEFLAG(h)  ((void)(h))
#define __HAL_UART_CLEAR_NEFLAG(h)  ((void)(h))

#define GPIOA ((GPIO_TypeDef *)0x40010800u)
#define GPIOB ((GPIO_TypeDef *)0x40010C00u)
#define USART1 ((USART_TypeDef *)0x40013800u)

#define GPIO_PIN_0  0x0001u
#define GPIO_PIN_1  0x0002u
#define GPIO_PIN_2  0x0004u
#define GPIO_PIN_3  0x0008u
#define GPIO_PIN_9  0x0200u
#define GPIO_PIN_10 0x0400u
#define GPIO_PIN_11 0x0800u
#define GPIO_PIN_12 0x1000u

typedef struct { uint32_t PLLState, PLLSource, PLLMUL; } RCC_PLLInitTypeDef;
typedef struct { uint32_t OscillatorType, HSEState, HSEPredivValue, HSIState; RCC_PLLInitTypeDef PLL; } RCC_OscInitTypeDef;
typedef struct { uint32_t ClockType, SYSCLKSource, AHBCLKDivider, APB1CLKDivider, APB2CLKDivider; } RCC_ClkInitTypeDef;

#define RCC_OSCILLATORTYPE_HSE 1u
#define RCC_HSE_ON 1u
#define RCC_HSE_PREDIV_DIV1 1u
#define RCC_HSI_ON 1u
#define RCC_PLL_ON 1u
#define RCC_PLLSOURCE_HSE 1u
#define RCC_PLL_MUL9 1u
#define RCC_CLOCKTYPE_HCLK 1u
#define RCC_CLOCKTYPE_SYSCLK 2u
#define RCC_CLOCKTYPE_PCLK1 4u
#define RCC_CLOCKTYPE_PCLK2 8u
#define RCC_SYSCLKSOURCE_PLLCLK 1u
#define RCC_SYSCLK_DIV1 1u
#define RCC_HCLK_DIV2 1u
#define RCC_HCLK_DIV1 1u
#define FLASH_LATENCY_2 2u

HAL_StatusTypeDef HAL_Init(void);
uint32_t HAL_GetTick(void);
void HAL_GPIO_WritePin(GPIO_TypeDef *port, uint16_t pin, GPIO_PinState state);
GPIO_PinState HAL_GPIO_ReadPin(GPIO_TypeDef *port, uint16_t pin);
HAL_StatusTypeDef HAL_UART_Receive_IT(UART_HandleTypeDef *h, uint8_t *p, uint16_t len);
HAL_StatusTypeDef HAL_UART_Transmit_IT(UART_HandleTypeDef *h, uint8_t *p, uint16_t len);
HAL_StatusTypeDef HAL_UART_Transmit_DMA(UART_HandleTypeDef *h, uint8_t *p, uint16_t len);
HAL_StatusTypeDef HAL_RCC_OscConfig(RCC_OscInitTypeDef *s);
HAL_StatusTypeDef HAL_RCC_ClockConfig(RCC_ClkInitTypeDef *s, uint32_t latency);

#define __disable_irq() ((void)0)

#endif
