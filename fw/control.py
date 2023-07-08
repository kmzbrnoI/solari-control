#!/usr/bin/env python3

"""
Usage:
    control.py <device> [<content.json>]

Content of content.json:
{
    "num": 12345,
    "type": "Os",
    "direction1": "Blansko",
    "direction2": "Blansko",
    "final": "Max. 14 znaků",
    "time": "14:30",
    "delay": "0:30"
}
"""

import serial
import sys
import datetime
from typing import List, Dict
import json

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

global sport
global send_positions


def xor(data: List[int]) -> int:
    result = 0
    for num in data:
        result ^= num
    return result


def send(msgtype: int, data: List[int]) -> None:
    _data = data[:]
    _data.insert(0, msgtype)
    _data.insert(0, len(data))
    _data.insert(0, UART_SEND_MAGIC)
    _data.append(xor(_data))

    print(f'Send: {_data}')
    sport.write(_data)


def parse(data: List[int]) -> None:
    global send_positions

    if xor(data) != 0:
        print(f'Invalid xor: {data}')
        return

    # print('>>>>>> Received:', data)

    if data[2] == UART_MSG_SM_POS:
        print(f'Positions: {data[3:-1]}')
        positions = data[3:-1]
        assert len(positions) == FLAP_UNITS
        if all([pos != 0xFF for pos in positions[8:]]):
            send_positions = True

    elif data[2] == UART_MSG_SM_TARGET:
        print(f'Target: {data[3:-1]}')

    elif data[2] == UART_MSG_SM_SENS:
        print('Sensors: ', end='')
        print(' '.join([f'{byte:#010b}' for byte in data[3:-1]]))


def flap_number(num: int, length: int) -> List[int]:  # always returns list of length `length`
    if num == 0:
        return [0]*length
    numstr = str(num).rjust(length, '~')[-length:]
    return [int(char)+1 if char != '~' else 0 for char in numstr]


def flap_final(final: str) -> List[int]:  # always returns list of length FLAP_FINAL_LEN
    return [FLAP_ALPHABET.index(char) for char in final.lower().ljust(FLAP_FINAL_LEN, ' ')]


def flap_all_positions(content: Dict) -> List[int]:  # always returns list of length FLAP_UNITS
    final = flap_final(content.get('final', ''))
    assert len(final) == FLAP_FINAL_LEN

    result = []
    result += [FLAP_TYPES.index(content['type'])+1] if 'type' in content else [0]
    result += flap_number(content.get('num', 0), FLAP_TRAINNUM_COUNT)
    assert len(result) == 6
    result += final[0:2]
    assert len(result) == 8
    result += final[10:14]
    assert len(result) == 12
    result += [FLAP_DIRECTIONS_1.index(content['direction1'])+1] if 'direction1' in content else [0]
    result += [FLAP_DIRECTIONS_2.index(content['direction2'])+1] if 'direction2' in content else [0]
    result += [0, 0] # time TODO
    result += final[2:11]  # 0x10-0x17

    """
    if 'time' in content:
        hours, minutes = content['time'].split(':')
        result += [int(hours)+1] + flap_number(minutes, 2)
    else:
        result += [0, 0, 0]
    """

    # TODO: delay

    while len(result) < FLAP_UNITS:
        result.append(0)
    return result


if __name__ == '__main__':
    global send_positions
    send_positions = False
    positions_sent = False

    if len(sys.argv) < 2:
        sys.stderr.write(__doc__.strip()+'\n')
        sys.exit(1)

    if len(sys.argv) >= 3:
        with open(sys.argv[2]) as f:
            positions = json.loads(f.read())
    else:
        positions = {}

    sport = serial.Serial(sys.argv[1], 115200)

    receive_buf = []
    last_receive_time = datetime.datetime.now()
    while True:
        received = sport.read(1)
        if not received:
            sys.stderr.write('Port interrupt!\n')
            sys.exit(1)
        if receive_buf and datetime.datetime.now()-last_receive_time > RECEIVE_TIMEOUT:
            print('Clearing data, timeout!')
            receive_buf.clear()
        last_receive_time = datetime.datetime.now()
        receive_buf += received
        while len(receive_buf) > 0 and receive_buf[0] != UART_RECEIVE_MAGIC:
            print(f'Popping packet: {receive_buf[0]}')
            receive_buf.pop(0)

        while len(receive_buf) >= 2 and len(receive_buf) >= receive_buf[1]+4:
            packet_length = receive_buf[1]+4
            parse(receive_buf[0:packet_length])
            receive_buf = receive_buf[packet_length:]
            while len(receive_buf) > 0 and receive_buf[0] != UART_RECEIVE_MAGIC:
                print(f'Popping packet: {receive_buf[0]}')
                receive_buf.pop(0)

        if send_positions and not positions_sent:
            print('Sending positions...')
            send_positions = False
            positions_sent = True
            send(UART_MSG_MS_SET_ALL, flap_all_positions(positions))
