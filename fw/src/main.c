/* Main source file of Solari-Control ATmega CPU.
 */

#include <stdint.h>
#include <stdbool.h>
#include <util/delay.h>
#include <avr/interrupt.h>
#include <avr/io.h>
#include <avr/wdt.h>

///////////////////////////////////////////////////////////////////////////////

int main();
static inline void init();

///////////////////////////////////////////////////////////////////////////////


///////////////////////////////////////////////////////////////////////////////

int main() {
	init();

	while (true) {
		wdt_reset();
	}
}

static inline void init() {
	ACSR |= ACD;  // analog comparator disable
	//TIMSK = 0;

	//io_init();
	//set_output(PIN_LED_RED, true);
	//set_output(PIN_LED_YELLOW, true);

	// Timer 2 @ 1 kHz (1 ms)
	//TCCR2 = (1 << WGM21) | (1 << CS21) | (1 << CS20); // CTC; prescaler 32×
	//OCR2 = 248; // 1 ms
	//TIMSK |= (1 << OCIE2);

	sei(); // enable interrupts globally
	wdt_enable(WDTO_250MS);
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
