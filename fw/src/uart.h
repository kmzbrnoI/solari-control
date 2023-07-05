#ifndef __UART_H__
#define __UART_H__

/* UARRT communication interface
 * Protocol: 0xMAGIC 0xLEN 0xCMDTYPE 0xDATA1 ... 0xDATAN 0xXOR
 * MAGIC is different for both directions.
 * LEN is length of data (excluding xor, excluding CMDTYPE)
 * XOR is calculated out of all packets (including MAGIC)
 */

#include <stdbool.h>

#define UART_RECEIVE_MAGIC 0xCA
#define UART_SEND_MAGIC 0xB7

#define UART_OUTPUT_BUF_MAX_SIZE 64
#define UART_INPUT_BUF_MAX_SIZE 64

extern volatile uint8_t uart_output_buf[UART_OUTPUT_BUF_MAX_SIZE];
extern volatile uint8_t uart_input_buf[UART_INPUT_BUF_MAX_SIZE];
extern volatile bool uart_received;

void uart_init(void);
bool uart_can_fill_output_buf(void);
uint8_t uart_send_buf(void);
void uart_update_1ms(void);

#endif
