#include <avr/io.h>
#include "io.h"

void io_init(void) {
	DDRC = 0x07;
}
