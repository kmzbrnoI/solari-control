#ifndef _IO_H_
#define _IO_H_

/* Basic low-level IO manipulation. */

#include <stdbool.h>

void io_init(void);

inline void io_led_green_on() { PORTC |= (1 << PC0); }
inline void io_led_green_off() { PORTC &= ~(1 << PC0); }
inline void io_led_yellow_on() { PORTC |= (1 << PC1); }
inline void io_led_yellow_off() { PORTC &= ~(1 << PC1); }
inline void io_led_red_on() { PORTC |= (1 << PC2); }
inline void io_led_red_off() { PORTC &= ~(1 << PC2); }

#endif
