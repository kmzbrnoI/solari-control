#include <avr/io.h>
#include <util/delay.h>
#include "spi.h"
#include "io.h"
#include "io.h"
#include "io.h"

/* CD4021 input shift registers: shifts on raising edge, max freq. = 12 MHz
 * CD4094 output shift registers: shifts on raising egde, max freq. = 5 MHz
 * -> rising edge = setup, falling edge = sample
 * -> SCK by default high (but CPOL=0 because of inverting in PCB design) -> CPHA=0
 */

///////////////////////////////////////////////////////////////////////////////

void spi_init(void) {
	DDRB |= (1 << PB3) | (1 << PB5) | (1 << PB2); // MOSI & SCK & SS out
	PORTB |= (1 << PB4); // pull-up on MISO just for sure
	SPCR = (1 << SPE) | (1 << MSTR) | (1 << SPR0); // enable SPI, SPI master, frequency=f_osc/16
}

void spi_write(uint8_t* data, uint8_t size) {
	io_strobe_off();
	_delay_us(1);

	for (uint8_t i = 0; i < size; i++) {
		SPDR = ~data[i];
		while (!(SPSR & (1<<SPIF)));
	}

	io_strobe_on();
}

void spi_read(uint8_t* data, uint8_t size) {
	io_parser_on();
	_delay_us(1);
	io_parser_off();
	_delay_us(1);

	for (uint8_t i = 0; i < size; i++) {
		SPDR = 0;
		while (!(SPSR & (1<<SPIF)));
		data[i] = SPDR;
	}
}
