#include <avr/io.h>
#include <util/delay.h>
#include <string.h>
#include "flap.h"
#include "spi.h"
#include "io.h"
#include "common.h"

///////////////////////////////////////////////////////////////////////////////
// Variables

uint8_t flap_sens_reset[FLAP_SIDES][FLAP_BYTES];
uint8_t flap_sens_moved[FLAP_SIDES][FLAP_BYTES];
uint8_t flap_pos[FLAP_SIDES][FLAP_UNITS];
uint8_t flap_counts[FLAP_SIDES][FLAP_UNITS];
uint8_t flap_target_pos[FLAP_SIDES][FLAP_UNITS];

uint8_t _last_moved_sens[FLAP_SIDES][FLAP_BYTES];
bool _next_ip;
uint8_t _active_out_timer;
bool flap_moved_changed;
FlapSide flap_side;

///////////////////////////////////////////////////////////////////////////////
// Local functions prototypes

static void _flap_read(void);
static void _update_moved(void);
static inline bool _flap_in_progress(void);
static void _set_side(FlapSide side);
static void flap_flap(uint8_t which[FLAP_BYTES]);

///////////////////////////////////////////////////////////////////////////////

void flap_init(void) {
	_next_ip = true;
	_active_out_timer = ACTIVE_OUT_MS;
	flap_moved_changed = false;

	for (uint8_t i = 0; i < FLAP_SIDES; i++) {
		memset(flap_pos[i], 0xFF, FLAP_UNITS);
		memset(flap_counts[i], 0xFF, FLAP_UNITS);
		memset(flap_target_pos[i], 0, FLAP_UNITS);
	}

	for (uint8_t i = 0; i < FLAP_SIDES; i++) {
		_set_side(i);
		_delay_ms(500);
		_flap_read();
		memcpy(_last_moved_sens[i], flap_sens_moved[i], FLAP_BYTES);
		_update_moved();
	}

	_set_side(NoSide);
}

void flap_flap(uint8_t which[FLAP_BYTES]) {
	if (_flap_in_progress())
		return; // flapping in progress

	io_id_off();
	io_ip_off();
	_delay_us(10);
	spi_write(which, FLAP_BYTES);
	_delay_us(10);

	if (_next_ip) {
		io_id_off();
		io_ip_on();
	} else {
		io_id_on();
		io_ip_off();
	}

	_active_out_timer = 0;
	_next_ip = !_next_ip;
	io_led_red_on();
}

void flap_update_1ms(void) {
	if (_active_out_timer < ACTIVE_OUT_MS) {
		_active_out_timer++;
		if (_active_out_timer == ACTIVE_OUT_MS) {
			io_id_off();
			io_ip_off();
			_flap_read();
			_update_moved();
			flap_moved_changed = true;
			io_led_red_off();
		}
	}
}

static void _flap_read(void) {
	/* There must be a delay of minimum 50 us between 2 successive execution of this function
	 * to ensure proper state of 'Z' & 'P' signals.
	 */
	uint8_t received[FLAP_BYTES];

	if (flap_side >= FLAP_SIDES)
		fail();

	io_z_off();
	io_p_on();
	_delay_us(10);
	spi_read(received, FLAP_BYTES);

	// invert received bytes
	for (size_t i = 0; i < FLAP_BYTES; i++)
		flap_sens_moved[flap_side][FLAP_BYTES-i-1] = reverse_uint8_bits_order(received[i]);

	io_z_on();
	io_p_off();
	_delay_us(50); // wait for slow transistors & optocoupler
	spi_read(received, FLAP_BYTES);

	// invert received bytes
	for (size_t i = 0; i < FLAP_BYTES; i++)
		flap_sens_reset[flap_side][FLAP_BYTES-i-1] = reverse_uint8_bits_order(~received[i]);

	io_z_off();
	io_p_off();
}

static void _update_moved(void) {
	if (flap_side >= FLAP_SIDES)
		fail();

	for (uint8_t i = 0; i < FLAP_UNITS; i++) {
		const bool current_sens = ((flap_sens_moved[flap_side][i/8] >> (i%8)) & 1);
		const bool current_reset = ((flap_sens_reset[flap_side][i/8] >> (i%8)) & 1);
		const bool last_sens = ((_last_moved_sens[flap_side][i/8] >> (i%8)) & 1);

		if ((current_sens != last_sens) && (flap_pos[flap_side][i] != 0xFF))
			flap_pos[flap_side][i]++;
		if (current_reset) {
			if ((flap_pos[flap_side][i] != 0xFF) && (flap_pos[flap_side][i] != 0))
				flap_counts[flap_side][i] = flap_pos[flap_side][i];
			flap_pos[flap_side][i] = 0;
		}
		if (flap_target_pos[flap_side][i] >= flap_counts[flap_side][i])
			flap_target_pos[flap_side][i] = 0;
	}

	memcpy(_last_moved_sens[flap_side], flap_sens_moved[flap_side], FLAP_BYTES);
}

static inline bool _flap_in_progress(void) {
	return _active_out_timer < ACTIVE_OUT_MS;
}

void flap_set_all(FlapSide side, uint8_t pos[FLAP_UNITS]) {
	if (side >= FLAP_SIDES)
		fail();

	memcpy(flap_target_pos[side], pos, FLAP_UNITS);
	for (uint8_t i = 0; i < FLAP_UNITS; i++)
		if (flap_target_pos[side][i] >= flap_counts[side][i])
			flap_target_pos[side][i] = 0;
}

void flap_set_single(FlapSide side, uint8_t i, uint8_t pos) {
	if (i < FLAP_UNITS) {
		if (pos >= flap_counts[side][i])
			pos = 0;
		flap_target_pos[side][i] = pos;
	}
}

void flap_single_clap() {
	if (_flap_in_progress())
		return;

	if ((flap_target_reached(SideA)) && (flap_target_reached(SideB))) {
		if (flap_side != NoSide)
			_set_side(NoSide);
		return;
	}

	if ((flap_side == NoSide) || (flap_target_reached(flap_side))) {
		_set_side(flap_target_reached(SideA) ? SideB : SideA);
		return; // flap next cycle
	}

	uint8_t to_flap[FLAP_BYTES];
	memset(to_flap, 0, FLAP_BYTES);

	for (uint8_t i = 0; i < FLAP_UNITS; i++)
		if (flap_pos[flap_side][i] != flap_target_pos[flap_side][i])
			to_flap[i/8] |= (1 << (i%8));

	flap_flap(to_flap);
}

static void _set_side(FlapSide side) {
	flap_side = side;
	switch (side) {
	case SideA:
		io_rel1_on();
		io_rel2_off();
		break;
	case SideB:
		io_rel1_off();
		io_rel2_on();
		break;
	case NoSide:
		io_rel1_off();
		io_rel2_off();
		break;
	}
}

bool flap_target_reached(FlapSide side) {
	if (side >= FLAP_SIDES)
		fail();

	return (memcmp((char*)flap_pos[side], (char*)flap_target_pos[side], FLAP_UNITS) == 0);
}
