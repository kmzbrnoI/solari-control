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
static void _uart_req_set_sens(FlapSide side, bool value);
static void _uart_req_set_pos(FlapSide side, bool value);
static void _uart_req_set_target(FlapSide side, bool value);

///////////////////////////////////////////////////////////////////////////////

volatile bool _flap_update_rq;
volatile uint16_t _counter_flap_clap;
volatile uint8_t _led_yel_counter;
volatile bool _flap_txreq;

#define LED_YEL_ON_MS 100

typedef union {
	uint8_t all;
	struct {
		bool sens_side1 : 1;
		bool sens_side2 : 1;
		bool pos_side1 : 1;
		bool pos_side2 : 1;
		bool target_side1 : 1;
		bool target_side2 : 1;
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
			flap_single_clap();
			_counter_flap_clap = 0;
			io_led_green_toggle();
			if (_flap_txreq) {
				uart_req.sep.sens_side1 = uart_req.sep.sens_side2 = true;
				uart_req.sep.pos_side1 = uart_req.sep.pos_side2 = true;
			}
			_flap_txreq = true;
		}

		if (flap_moved_changed) {
			flap_moved_changed = false;
			if (_flap_txreq) {
				uart_req.sep.sens_side1 = uart_req.sep.sens_side2 = true;
				uart_req.sep.pos_side1 = uart_req.sep.pos_side2 = true;
				_flap_txreq = false;
			}
		}

		// wdt_reset();
	}
}

static inline void init(void) {
	ACSR |= ACD;  // analog comparator disable
	TIMSK0 = TIMSK1 = TIMSK2 = 0;
	uart_req.all = 0;
	_counter_flap_clap = 0;
	_led_yel_counter = 2*LED_YEL_ON_MS;
	_flap_txreq = false;

	io_init();
	io_led_green_on();
	io_led_yellow_on();
	io_led_red_on();

	uart_init();
	spi_init();

	// Setup timer 0 @ 1 kHz (period 1 ms)
	TCCR0A = (1 << WGM01); // CTC mode
	TCCR0B = (1 << CS01) | (1 << CS00); // CTC mode, prescaler 64×
	TIMSK0 = (1 << OCIE0A); // enable compare match interrupt
	OCR0A = 229;

	flap_init(); // must be initialized after some time

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
	if (_led_yel_counter < 2*LED_YEL_ON_MS) {
		_led_yel_counter++;
		if (_led_yel_counter == LED_YEL_ON_MS)
			io_led_yellow_off();
	}
}

///////////////////////////////////////////////////////////////////////////////

static void uart_process_received(void) {
	if (!uart_received)
		return;
	if (_led_yel_counter == 2*LED_YEL_ON_MS) {
		_led_yel_counter = 0;
		io_led_yellow_on();
	}
	const uint8_t data_len = uart_input_buf[1];

	switch (uart_input_buf[2]) { // message type
	case UART_MSG_MS_GET_SENS:
		uart_req.sep.sens_side1 = uart_req.sep.sens_side2 = true;
		break;
	case UART_MSG_MS_GET_POS:
		uart_req.sep.pos_side1 = uart_req.sep.pos_side2 = true;
		break;
	case UART_MSG_MS_GET_TARGET:
		uart_req.sep.target_side1 = uart_req.sep.target_side2 = true;
		break;
	case UART_MSG_MS_FLAP:
		if (data_len >= 2) {
			const uint8_t side = uart_input_buf[3];
			const uint8_t unit = uart_input_buf[4];
			if ((side < FLAP_SIDES) && (flap_target_pos[side][unit] != 0xFF)) {
				flap_set_single(side, unit, flap_target_pos[side][unit]+1);
				_uart_req_set_target(side, true);
			}
		}
		break;
	case UART_MSG_MS_SET_SINGLE:
		if (data_len >= 3) {
			const uint8_t side = uart_input_buf[3];
			if (side < FLAP_SIDES) {
				flap_set_single(side, uart_input_buf[4], uart_input_buf[5]);
				_uart_req_set_target(side, true);
			}
		}
		break;
	case UART_MSG_MS_SET_ALL:
		if (data_len >= (FLAP_UNITS+1) && (uart_input_buf[3] < FLAP_SIDES)) {
			flap_set_all(uart_input_buf[3], (uint8_t*)&uart_input_buf[4]);
			_uart_req_set_target(uart_input_buf[3], true);
		}
		break;
	}

	uart_received = false;
}

static void _uart_process_txreq(void) {
	if (!uart_can_fill_output_buf())
		return;

	if ((uart_req.sep.sens_side1) || (uart_req.sep.sens_side2)) {
		const uint8_t side = (uart_req.sep.sens_side1) ? 0 : 1;
		uart_output_buf[1] = (2*FLAP_BYTES) + 1;
		uart_output_buf[2] = UART_MSG_SM_SENS;
		uart_output_buf[3] = side;
		for (uint8_t i = 0; i < FLAP_BYTES; i++)
			uart_output_buf[4+i] = flap_sens_moved[side][i];
		for (uint8_t i = 0; i < FLAP_BYTES; i++)
			uart_output_buf[4+FLAP_BYTES+i] = flap_sens_reset[side][i];
		if (uart_send_buf() == 0)
			_uart_req_set_sens(side, false);
	} else if ((uart_req.sep.pos_side1) || (uart_req.sep.pos_side2)) {
		const uint8_t side = (uart_req.sep.pos_side1) ? 0 : 1;
		uart_output_buf[1] = FLAP_UNITS + 1;
		uart_output_buf[2] = UART_MSG_SM_POS;
		uart_output_buf[3] = side | (flap_target_reached(side) << 1) |
			(flap_target_reached_ignore_errors(side) << 2);
		for (uint8_t i = 0; i < FLAP_UNITS; i++)
			uart_output_buf[4+i] = flap_pos[side][i];
		if (uart_send_buf() == 0)
			_uart_req_set_pos(side, false);
	} else if ((uart_req.sep.target_side1) || (uart_req.sep.target_side2)) {
		const uint8_t side = (uart_req.sep.target_side1) ? 0 : 1;
		uart_output_buf[1] = FLAP_UNITS + 1;
		uart_output_buf[2] = UART_MSG_SM_TARGET;
		uart_output_buf[3] = side;
		for (uint8_t i = 0; i < FLAP_UNITS; i++)
			uart_output_buf[4+i] = flap_target_pos[side][i];
		if (uart_send_buf() == 0)
			_uart_req_set_target(side, false);
	}
}

static void _uart_req_set_sens(FlapSide side, bool value) {
	switch (side) {
		case SideA: uart_req.sep.sens_side1 = value; break;
		case SideB: uart_req.sep.sens_side2 = value; break;
		default: break;
	}
}

static void _uart_req_set_pos(FlapSide side, bool value) {
	switch (side) {
		case SideA: uart_req.sep.pos_side1 = value; break;
		case SideB: uart_req.sep.pos_side2 = value; break;
		default: break;
	}
}

static void _uart_req_set_target(FlapSide side, bool value) {
	switch (side) {
		case SideA: uart_req.sep.target_side1 = value; break;
		case SideB: uart_req.sep.target_side2 = value; break;
		default: break;
	}
}
