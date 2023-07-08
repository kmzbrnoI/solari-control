#ifndef __FLAP_H__
#define __FLAP_H__

/* Flap units high-level control (getting state, setting state) */

#include <stdbool.h>
#include <stdint.h>

#define FLAP_BYTES 3
#define FLAP_UNITS (8*FLAP_BYTES)
#define ACTIVE_OUT_MS 80 // max uint8_t
#define FLAP_CLAP_PERIOD_MS 200

extern uint8_t flap_sens_reset[FLAP_BYTES];
extern uint8_t flap_sens_moved[FLAP_BYTES];
extern uint8_t flap_pos[FLAP_UNITS]; // 0xFF = unknown

void flap_init(void);
void flap_set_all(uint8_t pos[FLAP_UNITS]);
void flap_set_single(uint8_t i, uint8_t pos);
void flap_flap(uint8_t which[FLAP_BYTES]);
void flap_update_1ms(void);
void flap_single_clap();

#endif
