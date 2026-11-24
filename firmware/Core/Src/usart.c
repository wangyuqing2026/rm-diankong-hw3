/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    usart.c
  * @brief   USART1：115200 8N1，异步收发，开启全局中断
  ******************************************************************************
  */
/* USER CODE END Header */

#include "usart.h"

UART_HandleTypeDef huart1;
DMA_HandleTypeDef  hdma_usart1_tx;   /* DMA1_Channel4 = USART1_TX（选做） */

/**
  * @brief 打开 DMA1 时钟
  * @note  必须在 MX_USART1_UART_Init() 之前调用：MspInit 里要配置 DMA 通道，
  *        通道寄存器没时钟就是"写进去没反应"，现象是 DMA 一直不启动。
  */
void MX_DMA_Init(void)
{
  __HAL_RCC_DMA1_CLK_ENABLE();
}

void MX_USART1_UART_Init(void)
{
  huart1.Instance          = USART1;
  huart1.Init.BaudRate     = 115200;
  huart1.Init.WordLength   = UART_WORDLENGTH_8B;
  huart1.Init.StopBits     = UART_STOPBITS_1;
  huart1.Init.Parity       = UART_PARITY_NONE;
  huart1.Init.Mode         = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl    = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;

  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
}
