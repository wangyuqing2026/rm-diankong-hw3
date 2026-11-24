#ifndef __USART_H
#define __USART_H

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"

extern UART_HandleTypeDef huart1;
extern DMA_HandleTypeDef  hdma_usart1_tx;   /* DMA1_Channel4 = USART1_TX（选做） */

void MX_DMA_Init(void);
void MX_USART1_UART_Init(void);

#ifdef __cplusplus
}
#endif

#endif /* __USART_H */
