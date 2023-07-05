/* Main source file of Solari-Control ATmega CPU.
 */

#include <stdint.h>
#include <stdbool.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/wdt.h>
#include "io.h"
#include "uart.h"
#include "spi.h"
#include "flap.h"

///////////////////////////////////////////////////////////////////////////////

int main();
static inline void init(void);
static void uart_process_received(void);
static void _uart_process_txreq(void);

///////////////////////////////////////////////////////////////////////////////

volatile bool _flap_update_rq;
volatile uint16_t _counter_flap_clap;

typedef union {
	uint8_t all;
	struct {
		bool sens : 1;
		bool pos : 1;
	} sep;
} UartRequests;

UartRequests uart_req;

///////////////////////////////////////////////////////////////////////////////

int main() {
	init();

	while (true) {
		if (uart_received)
			uart_process_received();
		_uart_process_txreq();
		if (_flap_update_rq) {
			flap_update_1ms();
			_flap_update_rq = false;
		}
		if (_counter_flap_clap >= FLAP_CLAP_PERIOD_MS) {
			// flap_single_clap(); // TODO uncomment after tests
			_counter_flap_clap = 0;
			uart_req.sep.pos = true;
		}

		// wdt_reset();
	}
}

static inline void init(void) {
	ACSR |= ACD;  // analog comparator disable
	TIMSK0 = TIMSK1 = TIMSK2 = 0;
	uart_req.all = 0;
	_counter_flap_clap = 0;

	io_init();
	io_led_green_on();
	io_led_yellow_on();
	io_led_red_on();

	uart_init();
	spi_init();
	flap_init();

	// Setup timer 0 @ 1 kHz (period 1 ms)
	TCCR0A = (1 << WGM01); // CTC mode
	TCCR0B = (1 << CS01) | (1 << CS00); // CTC mode, prescaler 64×
	TIMSK0 = (1 << OCIE0A); // enable compare match interrupt
	OCR0A = 229;

	for (uint8_t i = 0; i < 5; i++)
		_delay_ms(200);

	io_led_green_off();
	io_led_yellow_off();
	io_led_red_off();

	sei(); // enable interrupts globally
	// wdt_enable(WDTO_250MS);
}

///////////////////////////////////////////////////////////////////////////////

ISR(TIMER0_COMPA_vect) {
	// Timer 2 @ 1 kHz (1 ms)
	uart_update_1ms();
	_flap_update_rq = true;

	if (_counter_flap_clap < FLAP_CLAP_PERIOD_MS)
		_counter_flap_clap++;
}

///////////////////////////////////////////////////////////////////////////////

static void uart_process_received(void) {
	if (!uart_received)
		return;
	io_led_green_toggle();
	const uint8_t data_len = uart_input_buf[1];

	switch (uart_input_buf[2]) { // message type
	case UART_MSG_MS_GET_SENS:
		uart_req.sep.sens = true;
		break;
	case UART_MSG_MS_GET_POS:
		uart_req.sep.pos = true;
		break;
	case UART_MSG_MS_FLAP:
		if (data_len >= FLAP_BYTES) {
			flap_flap((uint8_t*)&uart_input_buf[3]);
		}
		break;
	case UART_MSG_MS_SET_SINGLE:
		if (data_len > 2) {
			flap_set_single(uart_input_buf[3], uart_input_buf[4]);
		}
		break;
	case UART_MSG_MS_SET_ALL:
		if (data_len >= FLAP_UNITS) {
			flap_set_all((uint8_t*)&uart_input_buf[3]);
		}
	}

	uart_received = false;
}

static void _uart_process_txreq(void) {
	if (!uart_can_fill_output_buf())
		return;

	if (uart_req.sep.sens) {
		uart_output_buf[1] = 2*FLAP_BYTES;
		uart_output_buf[2] = UART_MSG_SM_SENS;
		for (uint8_t i = 0; i < FLAP_BYTES; i++)
			uart_output_buf[3+i] = flap_sens_moved[i];
		for (uint8_t i = 0; i < FLAP_BYTES; i++)
			uart_output_buf[3+FLAP_BYTES+i] = flap_sens_reset[i];
		if (uart_send_buf() == 0)
			uart_req.sep.sens = false;
	} else if (uart_req.sep.pos) {
		uart_output_buf[1] = FLAP_UNITS;
		uart_output_buf[2] = UART_MSG_SM_POS;
		for (uint8_t i = 0; i < FLAP_UNITS; i++)
			uart_output_buf[3+i] = flap_pos[i];
		if (uart_send_buf() == 0)
			uart_req.sep.pos = false;
	}
}
