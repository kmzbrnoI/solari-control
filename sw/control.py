#!/usr/bin/env python3

"""
Solari di Udine platform board control script

Usage:
    control.py set_positions [options] [--file=<filename.json>] [-w|--wait] <device> <side>
    control.py reset [options] [-w|--wait] <device> <side>
    control.py flap [options] <device> <flapid> <side>
    control.py loop [options] <device> [<side>]
    control.py (-h | --help)
    control.py --version

Options:
  -l <loglevel>     Specify loglevel (python logging package) [default: info]
  -p --pos          Print received positions
  -s --sens         Print received sensors
  -t --target       Print received target

Side: A/B

See content.json for set_positions example
"""

import serial
import sys
import datetime
from typing import List, Dict
import json
import docopt
import logging

APP_VERSION = '1.0'

UART_RECEIVE_MAGIC = 0xB7
UART_SEND_MAGIC = 0xCA

UART_MSG_MS_GET_SENS = 0x01
UART_MSG_MS_GET_POS = 0x02
UART_MSG_MS_GET_TARGET = 0x03
UART_MSG_MS_FLAP = 0x10
UART_MSG_MS_SET_SINGLE = 0x11
UART_MSG_MS_SET_ALL = 0x12

UART_MSG_SM_SENS = 0x01
UART_MSG_SM_POS = 0x02
UART_MSG_SM_TARGET = 0x03

RECEIVE_TIMEOUT = datetime.timedelta(milliseconds=200)

FLAP_UNITS = 26
FLAP_ALPHABET = " 0123456789aáäbcčdďeéěfghiíjklmnňoóöpqrřsštťuúůüvwxyýzž/.()"
FLAP_FINAL_LEN = 14
FLAP_TRAINNUM_COUNT = 5

FLAP_TYPES = [
    'Ec', 'Ic', 'Ex R', 'Ex lůžkový', 'Ex', 'R R', 'R lůžkový', 'R', 'Sp', 'Os',
    'Mim. Ex', 'Mim. R', 'Mim. Sp', 'Mim. Os', 'Zvláštní vlak', 'Special train',
    'Parní vlak', 'Steam train', 'IR', 'ICE', 'Sc', 'TGV', '', 'Ic bílá', 'Sp',
]

FLAP_DIRECTIONS_1 = [
    'Adamov', 'Adamov-Blansko', 'Bylnice', 'Blansko', 'Blažovice', 'Bohumín',
    'Břeclav', 'Břeclav-Kúty', 'Břeclav-Bratislava', 'Bučovice', 'Bzenec',
    'Česká Třebová', 'Č.Třebová-Pardubice', 'Havlíčkův Brod', 'Holubice',
    'Horní Cerekev', 'Hradec Králové', 'Jihlava', 'Jihlava-Horní Cerekev',
    'Kolín', 'Kojetín', 'Kroměříž', 'Křižanov', 'Kunovice', 'Kuřim', 'Kuřim-Tišnov',
    'Kyjov', 'Modřice', 'Moravské Bránice', 'Moravský Krumlov', 'Náměšť nad Oslavou',
    'Nezamyslice', 'Olomouc hl.n.', 'Olomouc-Uničov', 'Ostrava hl.n.',
    'Ostrava-Vítkovice', 'Pardubice hl.n.', 'Praha-Holešovice', 'Přerov',
    'Přerov-Bohumín', 'Prostějov hl.n.', 'Prostějov-Olomouc', 'Rajhrad',
    'Rousínov', 'Šakvice', 'Skalice nad Svitavou', 'Sokolnice-Teln.', 'Střelice',
    'Studenec', 'Studénka', 'Tišnov', 'Veselí nad Moravou', 'Vranovice',
    'Vyškov na Moravě', 'Zastávka u Brna', 'Žďár nad Sázavou', '?', 'Studenec',
    'Štúrovo', 'Svitavy', 'Tábor', 'Tišnov', 'Tišnov-Křižanov', 'Trenč. Teplá',
    'Turnov', 'Uherské Hradiště', '?'
]

FLAP_DIRECTIONS_2 = [
    'Blansko', 'Bohumín', 'Bojkovice', 'Břeclav', 'Bratislava', 'Bylnice',
    'Bučovice', 'Bzenec', 'Čadca', 'České Budějovice', 'Český Těšín', 'Chornice',
    'Děčin', 'Frýdek-Místek', 'Havířov', 'Havlíčkův Brod', 'Holubice', 'Horní Cerekev',
    'Hradec Králové', 'Hranice na Moravě', 'Hrušovany nad Jevišovkou', 'Hulín',
    'Kolína', 'Komárno', 'Kyjov', 'Kyjov Bzenec', 'Křižanov', 'Kunovice', 'Kúty',
    'Moravské Bránice', 'Moravský Krumlov', 'Moravský Písek', 'Moravská Třebová',
    'Mosty u Jablunkova', 'Náměšť nad Oslavou', 'Nezamyslice', 'Nové Město na Moravě',
    'Okříšky', 'Ostrava hl.n.', 'Ostrava-Svinov', 'Ostrava-Vítkovice', 'Pardubice hl.n.',
    'Pardubice-Kolín', 'Praha-Holešovice', 'Přerov', 'S1', 'S2', 'S3', 'S4', 'S41',
    'S5', 'S6', 'S7', 'R1', 'R2', 'R3', 'R4', 'R41', 'R5', 'R6', 'R7', 'Uničov',
    'Ústí nad Labem', 'Valašské Meziřící', 'Veselí nad Lužnicí', 'Veseá nad Moravou',
    'Vyškov na Moravě', 'Zábřeh na Moravě', 'Zaječí', 'Žďár nad Sázavou', 'Žilina',
    'Kojetín', 'Vlárský Průsmyk', 'Tábor-Veselí nad Lužnicí', '', 'Praha hl.n.',
    '', 'ODKLON']

FLAP_DELAYS_MIN = [
    5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90, 100, 110,
    120, 130, 140, 150, 160, 170, 180, 200, 220, 240, 260, 280, 300, 330, 360,
    390, 420, 450, 480
]

FLAP_DELAYS_NEXT = [
    ">480", "VLAK NEJEDE", "BUS"
]


def xor(data: List[int]) -> int:
    result = 0
    for num in data:
        result ^= num
    return result


def send(sport, msgtype: int, data: List[int]) -> None:
    _data = data[:]
    _data.insert(0, msgtype)
    _data.insert(0, len(data))
    _data.insert(0, UART_SEND_MAGIC)
    _data.append(xor(_data))

    logging.debug(f'< Send: {_data}')
    sport.write(_data)


def side_str(_side: int) -> str:
    if (_side&1) == 0:
        return 'A'
    elif (_side&1) == 1:
        return 'B'
    else:
        return '?'


def side_int(_side: str) -> int:
    _side = _side.lower()
    if _side == 'a':
        return 0
    elif _side == 'b':
        return 1

    assert False, 'Invalid side'


def parse(data: List[int], program) -> None:
    if xor(data) != 0:
        logging.warning(f'Invalid xor: {data}')
        return

    logging.debug(f'> Received: {data}')

    if data[2] == UART_MSG_SM_POS:
        if args['<side>'] is None or (data[3]&1) == args['<side>']:
            if args['--pos']:
                logging.info(f'Side: {side_str(data[3])} Positions: {data[4:-1]}')
            positions = data[4:-1]
            assert len(positions) == FLAP_UNITS
            if getattr(program, 'received_positions', None):
                program.received_positions(positions)

    elif data[2] == UART_MSG_SM_TARGET:
        if args['<side>'] is None or (data[3]&1) == args['<side>']:
            if args['--target']:
                logging.info(f'Side: {side_str(data[3])} Target: {data[4:-1]}')
            if getattr(program, 'received_target', None):
                program.received_target(data[4:-1])

    elif data[2] == UART_MSG_SM_SENS:
        if args['<side>'] is None or (data[3]&1) == args['<side>']:
            if args['--sens']:
                logging.info(f'Side: {side_str(data[3])} Sensors: ' +
                             (' '.join([f'{byte:#010b}' for byte in data[4:-1]])))
            if getattr(program, 'received_sensors', None):
                program.received_sensors(data[4:-1])


def flap_number(num: int, length: int) -> List[int]:  # always returns list of length `length`
    if num == 0:
        return [0]*length
    numstr = str(num).rjust(length, '~')[-length:]
    return [int(char)+1 if char != '~' else 0 for char in numstr]


def flap_final(final: str) -> List[int]:  # always returns list of length FLAP_FINAL_LEN
    return [FLAP_ALPHABET.index(char) for char in final.lower().ljust(FLAP_FINAL_LEN, ' ')]


def flap_delay(delay: str) -> int:
    if delay.upper() in FLAP_DELAYS_NEXT:
        return FLAP_DELAYS_NEXT.index(delay.upper()) + len(FLAP_DELAYS_MIN) + 1

    if ':' in delay:
        hours, minutes = map(int, delay.split(':'))
        minutes += hours*60
    elif delay.isdigit():
        minutes = int(delay)
    else:
        assert False, 'Invalid delay'

    if minutes > 480:
        return len(FLAP_DELAYS_MIN) + 1

    # Pick nearest lower delay
    while minutes > 0 and minutes not in FLAP_DELAYS_MIN:
        minutes -= 1

    if minutes not in FLAP_DELAYS_MIN:
        return 0

    return FLAP_DELAYS_MIN.index(minutes) + 1


def flap_all_positions(content: Dict) -> List[int]:  # always returns list of length FLAP_UNITS
    final = flap_final(content.get('final', ''))
    assert len(final) == FLAP_FINAL_LEN

    hours, minutes = map(int, content['time'].split(':')) if 'time' in content else (0xFF, 0xFF)

    result = []
    result += [FLAP_TYPES.index(content['type'])+1] if 'type' in content else [0]
    trainnum = flap_number(content.get('num', 0), FLAP_TRAINNUM_COUNT)
    if content.get('num_red', False):
        trainnum = [v+10 if v != 0 else 0 for v in trainnum]
    result += trainnum
    result += final[0:2]
    result += final[10:14]
    result += [FLAP_DIRECTIONS_1.index(content['direction1'])+1] if 'direction1' in content else [0]
    result += [FLAP_DIRECTIONS_2.index(content['direction2'])+1] if 'direction2' in content else [0]
    result += [hours+1] if hours != 0xFF else [0]
    result += [(minutes//10)+1] if minutes != 0xFF else [0]
    result += final[2:10]  # 0x10-0x17
    result += [(minutes%10)+1] if minutes != 0xFF else [0]
    result += [flap_delay(content['delay'])] if 'delay' in content else [0]

    assert len(result) == FLAP_UNITS
    return result


###############################################################################
# Subprograms

class SetPositions:
    def __init__(self, sport):
        self.sport = sport
        self.positions_sent = False
        self.sent_positions = []

        self.content = {}
        if args['--file']:
            with open(args['--file']) as f:
                self.content = json.loads(f.read())
        elif args['set_positions']:
            self.content = json.loads(input())

    def received_positions(self, positions: List[int]) -> None:
        if not self.positions_sent and all([pos != 0xFF for pos in positions]):
            self.positions_sent = True
            self.sent_positions = flap_all_positions(self.content)
            logging.info(f'Sending positions: {self.sent_positions} ...')
            send(self.sport, UART_MSG_MS_SET_ALL, [args['<side>']] + self.sent_positions)
            if not args['-w']:
                logging.info('Finished')
                sys.exit(0)
            else:
                logging.info('Waiting for positions reached (-w present)...')

        if positions == self.sent_positions:
            logging.info('Finished')
            sys.exit(0)


class Flap:
    def __init__(self, sport):
        self.sport = sport
        self.sent = False
        logging.info('Waiting for device initialized...')

    def received_positions(self, positions: List[int]) -> None:
        if all([pos != 0xFF for pos in positions]) and not self.sent:
            logging.info('Sending flap...')
            send(self.sport, UART_MSG_MS_FLAP, [agrs['<side>'], int(args['<flapid>'])])
            self.sent = True

    def received_target(self, target: List[int]) -> None:
        if self.sent:
            logging.info('Flap sent.')
            sys.exit(0)


class Loop:
    def __init__(self, sport):
        pass


###############################################################################
# Main

if __name__ == '__main__':
    global args
    args = docopt.docopt(__doc__, version=APP_VERSION)
    args['<side>'] = side_int(args['<side>']) if args['<side>'] is not None else None

    loglevel = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL,
    }.get(args['-l'], logging.INFO)
    logging.basicConfig(
        stream=sys.stdout,
        level=loglevel,
        format='[%(asctime)s.%(msecs)03d] %(levelname)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    sport = serial.Serial(args['<device>'], 115200)
    logging.debug(f'Connected to {args["<device>"]}')

    if args['set_positions'] or args['reset']:
        program = SetPositions(sport)
    elif args['flap']:
        program = Flap(sport)
    elif args['loop']:
        program = Loop(sport)
    else:
        assert False, 'Unknown program'

    receive_buf = []
    last_receive_time = datetime.datetime.now()
    while True:
        received = sport.read(1)
        if not received:
            sys.stderr.write('Port interrupt!\n')
            sys.exit(1)
        if receive_buf and datetime.datetime.now()-last_receive_time > RECEIVE_TIMEOUT:
            logging.debug('Clearing data, timeout!')
            receive_buf.clear()
        last_receive_time = datetime.datetime.now()
        receive_buf += received
        while len(receive_buf) > 0 and receive_buf[0] != UART_RECEIVE_MAGIC:
            logging.debug(f'Popping packet: {receive_buf[0]}')
            receive_buf.pop(0)

        while len(receive_buf) >= 2 and len(receive_buf) >= receive_buf[1]+4:
            packet_length = receive_buf[1]+4
            parse(receive_buf[0:packet_length], program)
            receive_buf = receive_buf[packet_length:]
            while len(receive_buf) > 0 and receive_buf[0] != UART_RECEIVE_MAGIC:
                logging.debug(f'Popping packet: {receive_buf[0]}')
                receive_buf.pop(0)

        if getattr(program, 'iter', None):
            program.iter()
