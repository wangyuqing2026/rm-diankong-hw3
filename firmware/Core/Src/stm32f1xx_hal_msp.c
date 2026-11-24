/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file    stm32f1xx_hal_msp.c
  * @brief   MSP：外设的底层引脚、时钟、中断使能
  ******************************************************************************
  */
/* USER CODE END Header */

#include "main.h"
#include "usart.h"          /* hdma_usart1_tx 的声明在这里 */

/**
  * @brief 全局 MSP 初始化
  */
void HAL_MspInit(void)
{
  __HAL_RCC_AFIO_CLK_ENABLE();
  __HAL_RCC_PWR_CLK_ENABLE();

  /* 关掉 JTAG 只留 SWD，释放 PB3/PB4/PA15（本工程没用到，保留默认也可以） */
  __HAL_AFIO_REMAP_SWJ_NOJTAG();
}

/**
  * @brief USART1 的底层配置：时钟、PA9/PA10 复用、NVIC
  */
void HAL_UART_MspInit(UART_HandleTypeDef *huart)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  if (huart->Instance == USART1)
  {
    __HAL_RCC_USART1_CLK_ENABLE();
    __HAL_RCC_GPIOA_CLK_ENABLE();

    /* PA9 = USART1_TX，复用推挽输出 */
    GPIO_InitStruct.Pin   = GPIO_PIN_9;
    GPIO_InitStruct.Mode  = GPIO_MODE_AF_PP;
    GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_HIGH;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    /* PA10 = USART1_RX，上拉输入 */
    GPIO_InitStruct.Pin  = GPIO_PIN_10;
    GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
    GPIO_InitStruct.Pull = GPIO_PULLUP;
    HAL_GPIO_Init(GPIOA, &GPIO_InitStruct);

    /* 串口中断优先级要高于按键，保证字节不丢 */
    HAL_NVIC_SetPriority(USART1_IRQn, 1, 0);
    HAL_NVIC_EnableIRQ(USART1_IRQn);

    /* ---- 选做：USART1_TX 走 DMA1_Channel4 ----
     * 搬运方向：内存 -> 外设（USART1->DR）；内存地址自增、外设地址不变；
     * 两边都是字节宽度；Normal 模式（一包搬完就停，不是循环缓冲）。
     * 链接到 huart1.hdmatx 之后，HAL_UART_Transmit_DMA() 才能找到这个通道。 */
    hdma_usart1_tx.Instance                 = DMA1_Channel4;
    hdma_usart1_tx.Init.Direction           = DMA_MEMORY_TO_PERIPH;
    hdma_usart1_tx.Init.PeriphInc           = DMA_PINC_DISABLE;
    hdma_usart1_tx.Init.MemInc              = DMA_MINC_ENABLE;
    hdma_usart1_tx.Init.PeriphDataAlignment = DMA_PDATAALIGN_BYTE;
    hdma_usart1_tx.Init.MemDataAlignment    = DMA_MDATAALIGN_BYTE;
    hdma_usart1_tx.Init.Mode                = DMA_NORMAL;
    hdma_usart1_tx.Init.Priority            = DMA_PRIORITY_LOW;
    if (HAL_DMA_Init(&hdma_usart1_tx) != HAL_OK)
    {
      Error_Handler();
    }
    __HAL_LINKDMA(huart, hdmatx, hdma_usart1_tx);

    /* DMA 传输完成要靠中断来收尾（清标志、回调），优先级低于串口接收 */
    HAL_NVIC_SetPriority(DMA1_Channel4_IRQn, 2, 0);
    HAL_NVIC_EnableIRQ(DMA1_Channel4_IRQn);
  }
}

void HAL_UART_MspDeInit(UART_HandleTypeDef *huart)
{
  if (huart->Instance == USART1)
  {
    __HAL_RCC_USART1_CLK_DISABLE();
    HAL_GPIO_DeInit(GPIOA, GPIO_PIN_9 | GPIO_PIN_10);
    HAL_NVIC_DisableIRQ(USART1_IRQn);

    /* 选做：DMA 通道也要一起关掉 */
    HAL_DMA_DeInit(huart->hdmatx);
    HAL_NVIC_DisableIRQ(DMA1_Channel4_IRQn);
  }
}
