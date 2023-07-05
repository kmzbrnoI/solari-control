#include <stddef.h>
#include <avr/io.h>
#include <avr/interrupt.h>
#include "uart.h"

#define UART_RECEIVE_TIMEOUT 10 // ms

volatile uint8_t uart_output_buf[UART_OUTPUT_BUF_MAX_SIZE];
volatile uint8_t uart_input_buf[UART_INPUT_BUF_MAX_SIZE];
volatile bool uart_received;

volatile uint8_t _next_byte_to_send;
volatile bool _sending;
volatile bool _receiving;
volatile uint8_t _receive_xor;
volatile uint8_t _next_byte_to_receive;
volatile uint8_t _receiving_timer; // in milliseconds

///////////////////////////////////////////////////////////////////////////////

static inline void _send_next_byte(void);

///////////////////////////////////////////////////////////////////////////////

void uart_init(void) {
	uart_received = false;
	uart_output_buf[0] = UART_SEND_MAGIC;
	_receiving = false;
	_sending = false;
	_next_byte_to_send = 0;

	UCSR0A = _BV(U2X0); // Double speed
	UCSR0B = _BV(RXCIE0) | _BV(TXCIE0) | _BV(RXEN0) | _BV(TXEN0);  // RX, TX enable; RX, TX interrupt enable
	UCSR0C = _BV(UCSZ01) | _BV(UCSZ00); // 8-bit data
	UBRR0L = 15; // 115 2000 baud/s
}

void uart_update_1ms() {
	if (_receiving_timer < 0xFF)
		_receiving_timer++;
}

///////////////////////////////////////////////////////////////////////////////
// Sending

bool uart_can_fill_output_buf(void) {
	return !_sending;
}

uint8_t uart_send_buf() {
	if (_sending)
		return 1;
	const uint8_t packet_size = uart_output_buf[1]+4;
	if (packet_size >= UART_OUTPUT_BUF_MAX_SIZE)
		return 2;

	uint8_t xor = 0;
	for (uint8_t i = 0; i < packet_size-1; i++)
		xor ^= uart_output_buf[i];
	uart_output_buf[packet_size-1] = xor;

	_sending = true;
	_next_byte_to_send = 0;
	_send_next_byte();
	return 0;
}

static inline void _send_next_byte(void) {
	while (!(UCSR0A & _BV(UDRE0)));
	UDR0 = uart_output_buf[_next_byte_to_send];
	_next_byte_to_send++;
}

ISR(USART_TX_vect) {
	uint8_t size = uart_output_buf[1]+4;
	if (_next_byte_to_send < size) {
		_send_next_byte();
	} else {
		_sending = false;
	}
}

///////////////////////////////////////////////////////////////////////////////
// Receiving

ISR(USART_RX_vect) {
	uint8_t status = UCSR0A;
	uint8_t data = UDR0;

	if (status & ((1<<FE0)|(1<<DOR0)|(1<<UPE0))) {
		_receiving = false;
		return; // return on error
	}

	if (_receiving_timer > UART_RECEIVE_TIMEOUT)
		_receiving = false;
	_receiving_timer = 0;

	if (_receiving) {
		uart_input_buf[_next_byte_to_receive] = data;
		_next_byte_to_receive++;
		_receive_xor ^= data;
		const uint8_t packet_length = uart_input_buf[1] + 4; // [1] is surely present
		if (packet_length >= UART_INPUT_BUF_MAX_SIZE) {
			_receiving = false;
			return;
		}
		if (_next_byte_to_receive == packet_length) {
			_receiving = false;
			if (_receive_xor == 0)
				uart_received = true;
		}
	} else {
		if ((!uart_received) && (data == UART_RECEIVE_MAGIC)) {
			_receiving = true;
			_receive_xor = data;
			uart_input_buf[0] = data;
			_next_byte_to_receive = 1;
		}
	}
}
