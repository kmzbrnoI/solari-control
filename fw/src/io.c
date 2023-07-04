#include <avr/io.h>
#include "io.h"

void io_init(void) {
	DDRC = 0x1F;
	DDRD = 0xFC;
}
