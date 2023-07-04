/* Main source file of Solari-Control ATmega CPU.
 */

#include <stdint.h>
#include <stdbool.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/wdt.h>

#include "io.h"

///////////////////////////////////////////////////////////////////////////////

int main();
static inline void init();

///////////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////////

int main() {
	init();

	while (true) {
		// wdt_reset();
	}
}

static inline void init() {
	ACSR |= ACD;  // analog comparator disable
	TIMSK0 = TIMSK1 = TIMSK2 = 0;

	io_init();
	io_led_green_on();
	io_led_yellow_on();
	io_led_red_on();

	// Timer 2 @ 1 kHz (1 ms)
	//TCCR2 = (1 << WGM21) | (1 << CS21) | (1 << CS20); // CTC; prescaler 32×
	//OCR2 = 248; // 1 ms
	//TIMSK |= (1 << OCIE2);

	for (uint8_t i = 0; i < 5; i++)
		_delay_ms(200);

	io_led_green_off();
	io_led_yellow_off();
	io_led_red_off();

	sei(); // enable interrupts globally
	// wdt_enable(WDTO_250MS);
}

///////////////////////////////////////////////////////////////////////////////

ISR(TIMER2_COMPA_vect) {
	// Timer 2 @ 1 kHz (1 ms)

	/*static volatile uint8_t counter_20ms = 0;
	counter_20ms++;
	if (counter_20ms >= 20) {
		counter_20ms = 0;
		switch_update();
	}*/
}

///////////////////////////////////////////////////////////////////////////////
