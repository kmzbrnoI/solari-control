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

///////////////////////////////////////////////////////////////////////////////

int main();
static inline void init(void);
static void uart_process_received(void);
static void _uart_send_test(void);

///////////////////////////////////////////////////////////////////////////////

volatile uint16_t _counter_1s;

///////////////////////////////////////////////////////////////////////////////

int main() {
	init();

	while (true) {
		if (uart_received)
			uart_process_received();

		if (_counter_1s >= 1000) {
			_counter_1s = 0;
			_uart_send_test();
		}
		// wdt_reset();
	}
}

static inline void init(void) {
	ACSR |= ACD;  // analog comparator disable
	TIMSK0 = TIMSK1 = TIMSK2 = 0;

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

	if (_counter_1s < 1000)
		_counter_1s++;
}

///////////////////////////////////////////////////////////////////////////////

static void uart_process_received(void) {
	if (!uart_received)
		return;

	io_led_green_toggle();
	uart_received = false;
}

static void _uart_send_test(void) {
	if (!uart_can_fill_output_buf())
		return;

	uart_output_buf[1] = 1;
	uart_output_buf[2] = 0x42;
	uart_output_buf[3] = 0x11;
	uart_send_buf();
}
