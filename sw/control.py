#!/usr/bin/env python3
# edulint: flake8=--max-line-length=100

"""
Solari di Udine platform board control script

Usage:
    control.py set_positions [options] [--file=<filename.json>] [-w|--wait] <device> <side>
    control.py reset [options] [-w|--wait] <device> <side>
    control.py flap [options] <device> <flapid> <side>
    control.py loop [options] <device> [<side>]
    control.py state [options] [--file=<filename.json>] <device> <side>
    control.py (-h | --help)
    control.py --version

Options:
  -l <loglevel>     Specify loglevel (python logging package) [default: info]
  -p --pos          Print received positions as bytes
  -s --sens         Print received sensor status as bits
  -t --target       Print received target as bytes

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
FLAP_ALPHABET = ' 0123456789aáäbcčdďeéěfghiíjklmnňoóöpqrřsštťuúůüvwxyýzž/.-()'
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
    '>480', 'VLAK NEJEDE', 'BUS'
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


def flap_str(lst: List[str], i: int) -> str:
    if i == 0xFF:
        return '?'
    return lst[i-1] if i > 0 and i <= len(lst) else ''


def side_str(_side: int) -> str:
    if (_side & 1) == 0:
        return 'A'
    if (_side & 1) == 1:
        return 'B'
    return '?'


def side_int(_side: str) -> int:
    _side = _side.lower()
    if _side == 'a':
        return 0
    if _side == 'b':
        return 1

    assert False, 'Invalid side'


def parse(data: List[int], program) -> None:
    if xor(data) != 0:
        logging.warning(f'Invalid xor: {data}')
        return

    logging.debug(f'> Received: {data}')

    if len(data) < 5:
        logging.warning('Data too short!')
        return

    if data[2] == UART_MSG_SM_POS:
        side = data[3] & 1
        target_reached = bool((data[3] >> 1) & 1)
        positions = data[4:-1]
        assert len(positions) == FLAP_UNITS, f'{len(positions)} != {FLAP_UNITS}'
        if args['<side>'] is None or side == args['<side>']:
            if args['--pos']:
                logging.info(f'Side: {side_str(side)} Positions: {positions}')
            if getattr(program, 'received_positions', None):
                program.received_positions(positions, side, target_reached)
        else:
            logging.debug('Side mismatch')

    elif data[2] == UART_MSG_SM_TARGET:
        side = data[3] & 1
        target = data[4:-1]
        assert len(target) == FLAP_UNITS, f'{len(target)} != {FLAP_UNITS}'
        if args['<side>'] is None or side == args['<side>']:
            if args['--target']:
                logging.info(f'Side: {side_str(side)} Target: {target}')
            if getattr(program, 'received_target', None):
                program.received_target(target, side)
        else:
            logging.debug('Side mismatch')

    elif data[2] == UART_MSG_SM_SENS:
        side = data[3] & 1
        sensors = data[4:-1]
        if args['<side>'] is None or side == args['<side>']:
            if args['--sens']:
                logging.info(f'Side: {side_str(side)} Sensors: ' +
                             (' '.join([f'{byte:#010b}' for byte in sensors])))
            if getattr(program, 'received_sensors', None):
                program.received_sensors(sensors, side)
        else:
            logging.debug('Side mismatch')


def flap_number(num: int, length: int) -> List[int]:  # always returns list of length `length`
    if num == 0:
        return [0]*length
    numstr = str(num).rjust(length, '~')[-length:]
    return [int(char)+1 if char != '~' else 0 for char in numstr]


def flap_final(final: str) -> List[int]:  # always returns list of length FLAP_FINAL_LEN
    for letter in final.lower():
        assert letter in FLAP_ALPHABET, f'Letter "{letter}" is not available!'
    return [FLAP_ALPHABET.index(char) for char in final.lower().ljust(FLAP_FINAL_LEN, ' ')]


def flap_delay(delay: str) -> int:
    if delay.upper() in FLAP_DELAYS_NEXT:
        return FLAP_DELAYS_NEXT.index(delay.upper()) + len(FLAP_DELAYS_MIN) + 1

    if ':' in delay:
        hours, minutes = map(int, delay.split(':'))
        minutes += hours*60
    elif delay.isdecimal():
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
    result += [(minutes % 10) + 1] if minutes != 0xFF else [0]
    result += [flap_delay(content['delay'])] if 'delay' in content else [0]

    assert len(result) == FLAP_UNITS
    return result


def explain_positions(data: List[int]) -> Dict:
    assert len(data) >= FLAP_UNITS
    if len(data) > FLAP_UNITS:
        logging.warning(f'{len(data)} bytes of positions received, however {FLAP_UNITS} expected!')
    result = {}
    result['raw'] = {}

    result['type'] = flap_str(FLAP_TYPES, data[0])
    result['raw']['type'] = data[0]

    num_data = data[1:6]
    trainnum = 0
    for i, numeral in enumerate(num_data):
        if numeral == 0:
            numeral = 1
        trainnum += (10**(len(num_data)-i-1)) * ((numeral-1) % 10)
    if any(num > 0 for num in num_data):
        result['num'] = trainnum
        result['num_red'] = any(num > 10 for num in num_data)

    result['raw']['num'] = num_data

    result['direction1'] = flap_str(FLAP_DIRECTIONS_1, data[12])
    result['raw']['direction1'] = data[12]
    result['direction2'] = flap_str(FLAP_DIRECTIONS_2, data[13])
    result['raw']['direction2'] = data[13]

    delay = data[25]
    if delay == 0xFF:
        result['delay'] = '?'
    elif delay > 0:
        delay_i = delay-1
        if delay_i < len(FLAP_DELAYS_MIN):
            minutes = FLAP_DELAYS_MIN[delay_i]
            result['delay'] = f'{minutes//60}:{str(minutes%60).zfill(2)}'
        elif delay_i < len(FLAP_DELAYS_MIN) + len(FLAP_DELAYS_NEXT):
            result['delay'] = FLAP_DELAYS_NEXT[delay_i-len(FLAP_DELAYS_MIN)]
        else:
            result['delay'] = ''
    else:
        result['delay'] = ''
    result['raw']['delay'] = delay

    hours, minutes_tenths, minutes_ones = data[14], data[15], data[24]
    if hours > 24 or minutes_tenths > 10 or minutes_ones > 10:
        result['time'] = '?'
    elif hours == 0 or minutes_tenths == 0 or minutes_ones == 0:
        result['time'] = ''
    else:
        minutes = (minutes_tenths-1)*10 + (minutes_ones-1)
        result['time'] = f'{hours-1}:{str(minutes).zfill(2)}'
    result['raw']['time'] = {}
    result['raw']['time']['minutes_ones'] = minutes_ones
    result['raw']['time']['minutes_tenths'] = minutes_tenths
    result['raw']['time']['hours'] = hours

    final = data[6:8] + data[16:24] + data[8:12]
    result['final'] = ''.join(flap_str(FLAP_ALPHABET, min(f+1, 0xFF)) for f in final)
    result['raw']['final'] = final

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

    def received_positions(self, positions: List[int], side: int, target_reached: bool) -> None:
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

    def received_positions(self, positions: List[int], side: int, target_reached: bool) -> None:
        if all([pos != 0xFF for pos in positions]) and not self.sent:
            logging.info('Sending flap...')
            send(self.sport, UART_MSG_MS_FLAP, [args['<side>'], int(args['<flapid>'])])
            self.sent = True

    def received_target(self, target: List[int], side: int) -> None:
        if self.sent:
            logging.info('Flap sent.')
            sys.exit(0)


class Loop:
    def __init__(self, sport):
        pass


class State:
    def __init__(self, sport):
        self.sport = sport
        self.received = {}
        logging.info('Waiting for positions...')

    def dump_and_exit(self) -> None:
        content = json.dumps(self.received, ensure_ascii=False, indent='    ')
        if args['--file']:
            with open(args['--file'], 'w') as f:
                f.write(content)
        else:
            print(content)

        sys.exit(0)

    def received_positions(self, positions: List[int], side: int, target_reached: bool) -> None:
        logging.info('Positions received.')
        if side == args['<side>']:
            self.received['current'] = explain_positions(positions)
            self.received['current']['side'] = side
            self.received['current']['target_reached'] = target_reached

            if 'target' in self.received:
                self.dump_and_exit()
            else:
                send(self.sport, UART_MSG_MS_GET_TARGET, [])

    def received_target(self, target: List[int], side: int) -> None:
        self.received['target'] = explain_positions(target)
        self.received['target']['side'] = side
        logging.info('Target received.')
        if 'current' in self.received:
            self.dump_and_exit()


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

    PROGRAMS = {
        'set_positions': SetPositions,
        'reset': SetPositions,
        'flap': Flap,
        'loop': Loop,
        'state': State,
    }

    program = None
    for name, inst in PROGRAMS.items():
        if args[name]:
            program = inst(sport)
            break
    assert program is not None, 'Unknown program'

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
