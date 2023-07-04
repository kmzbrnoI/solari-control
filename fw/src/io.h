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

inline void io_rel1_on() { PORTD |= (1 << PD6); }
inline void io_rel1_off() { PORTD &= ~(1 << PD6); }
inline void io_rel2_on() { PORTD |= (1 << PD7); }
inline void io_rel2_off() { PORTD &= ~(1 << PD7); }

inline void io_z_on() { PORTD |= (1 << PD3); }
inline void io_z_off() { PORTD &= ~(1 << PD3); }
inline void io_p_on() { PORTD |= (1 << PD4); }
inline void io_p_off() { PORTD &= ~(1 << PD4); }
inline void io_parser_on() { PORTD |= (1 << PD2); }
inline void io_parser_off() { PORTD &= ~(1 << PD2); }
inline void io_strobe_on() { PORTD |= (1 << PD5); }
inline void io_strobe_off() { PORTD &= ~(1 << PD5); }
inline void io_id_on() { PORTC |= (1 << PC3); }
inline void io_id_off() { PORTC &= ~(1 << PC3); }
inline void io_ip_on() { PORTC |= (1 << PC4); }
inline void io_ip_off() { PORTC &= ~(1 << PC4); }

#endif
