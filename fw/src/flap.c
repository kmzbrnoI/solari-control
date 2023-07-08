#include <avr/io.h>
#include <util/delay.h>
#include <string.h>
#include "flap.h"
#include "spi.h"
#include "io.h"
#include "common.h"

///////////////////////////////////////////////////////////////////////////////
// Variables

uint8_t flap_sens_reset[FLAP_BYTES];
uint8_t flap_sens_moved[FLAP_BYTES];
uint8_t flap_pos[FLAP_UNITS];

uint8_t _last_moved_sens[FLAP_BYTES];
bool _next_ip;
uint8_t _active_out_timer;
bool flap_moved_changed;
uint8_t flap_target_pos[FLAP_UNITS];

///////////////////////////////////////////////////////////////////////////////
// Local functions prototypes

static void _flap_read(void);
static void _update_moved(void);
static inline bool _flap_in_progress(void);

///////////////////////////////////////////////////////////////////////////////

void flap_init(void) {
	_next_ip = true;
	_active_out_timer = ACTIVE_OUT_MS;
	flap_moved_changed = false;
	memset(flap_pos, 0xFF, FLAP_UNITS);
	memset(flap_target_pos, 0, FLAP_UNITS);
	_flap_read();
	_update_moved();
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
		}
	}
}

static void _flap_read(void) {
	/* There must be a delay of minimum 50 us between 2 successive execution of this function
	 * to ensure proper state of 'Z' & 'P' signals.
	 */
	uint8_t received[FLAP_BYTES];

	io_z_off();
	io_p_on();
	_delay_us(10);
	spi_read(received, FLAP_BYTES);

	// invert received bytes
	for (size_t i = 0; i < FLAP_BYTES; i++)
		flap_sens_moved[FLAP_BYTES-i-1] = reverse_uint8_bits_order(received[i]);

	io_z_on();
	io_p_off();
	_delay_us(50); // wait for slow transistors & optocoupler
	spi_read(received, FLAP_BYTES);

	// invert received bytes
	for (size_t i = 0; i < FLAP_BYTES; i++)
		flap_sens_reset[FLAP_BYTES-i-1] = reverse_uint8_bits_order(~received[i]);

	io_z_off();
	io_p_off();
}

static void _update_moved(void) {
	for (uint8_t i = 0; i < FLAP_UNITS; i++) {
		const bool current_sens = ((flap_sens_moved[i/8] >> (i%8)) & 1);
		const bool current_reset = ((flap_sens_reset[i/8] >> (i%8)) & 1);
		const bool last_sens = ((_last_moved_sens[i/8] >> (i%8)) & 1);

		if ((current_sens != last_sens) && (flap_pos[i] != 0xFF))
			flap_pos[i]++;
		if (current_reset)
			flap_pos[i] = 0;
	}

	memcpy(_last_moved_sens, flap_sens_moved, FLAP_BYTES);
}

static inline bool _flap_in_progress(void) {
	return _active_out_timer < ACTIVE_OUT_MS;
}

void flap_set_all(uint8_t pos[FLAP_UNITS]) {
	memcpy(flap_target_pos, pos, FLAP_UNITS);
}

void flap_set_single(uint8_t i, uint8_t pos) {
	if (i < FLAP_UNITS)
		flap_target_pos[i] = pos;
}

void flap_single_clap() {
	if (memcmp((char*)flap_pos, (char*)flap_target_pos, FLAP_UNITS) == 0)
		return;
	if (_flap_in_progress())
		return;

	uint8_t to_flap[FLAP_BYTES];
	memset(to_flap, 0, FLAP_BYTES);

	for (uint8_t i = 0; i < FLAP_UNITS; i++)
		if (flap_pos[i] != flap_target_pos[i])
			to_flap[i/8] |= (1 << (i%8));

	flap_flap(to_flap);
}
