#ifndef __FLAP_H__
#define __FLAP_H__

/* Flap units high-level control (getting state, setting state)
 * Wiring:
 * Letters: 3-10 ~ 0x10-0x17, 1: 0x06, 2: 0x07, 11-14: 0x08-0x0B
 * Train number: 0x01-0x05
 * Train type: 0x00
 * Direction1: 0x0C
 * Direction2: 0x0D
 * Hours: 0x0E, minutes: 0x0F
 */

#include <stdbool.h>
#include <stdint.h>

#define FLAP_SIDES 2
#define FLAP_BYTES 4
#define FLAP_UNITS 26
#define ACTIVE_OUT_MS 80 // max uint8_t
#define FLAP_CLAP_PERIOD_MS 150
#define FLAP_MAX_FLAPS_SINCE_INCR 5
#define FLAP_MAX_FLAPS_SINCE_RESET 85

typedef enum {
	SideA = 0,
	SideB = 1,
	NoSide = 0xFF,
} FlapSide;

extern uint8_t flap_sens_reset[FLAP_SIDES][FLAP_BYTES];
extern uint8_t flap_sens_moved[FLAP_SIDES][FLAP_BYTES];
extern uint8_t flap_pos[FLAP_SIDES][FLAP_UNITS]; // 0xFF = unknown
extern bool flap_moved_changed;
extern uint8_t flap_target_pos[FLAP_SIDES][FLAP_UNITS];
extern uint8_t flap_counts[FLAP_SIDES][FLAP_UNITS]; // initially 0xFF, set after first overflow
extern FlapSide flap_side;

void flap_init(void);
void flap_set_all(FlapSide side, uint8_t pos[FLAP_UNITS]);
void flap_set_single(FlapSide side, uint8_t i, uint8_t pos);
void flap_update_1ms(void);
void flap_single_clap();
bool flap_target_reached(FlapSide side);
bool flap_target_reached_ignore_errors(FlapSide side);

#endif
