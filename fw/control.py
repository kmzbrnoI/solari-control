#!/usr/bin/env python3

"""
Usage:
    control.py <device> <content.json>

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
import datetime
import json

UART_RECEIVE_MAGIC = 0xB7
UART_SEND_MAGIC = 0xCA

UART_MSG_MS_GET_SENS = 0x01
UART_MSG_MS_GET_POS = 0x02
UART_MSG_MS_FLAP = 0x10
UART_MSG_MS_SET_SINGLE = 0x11
UART_MSG_MS_SET_ALL = 0x12

UART_MSG_SM_SENS = 0x01
UART_MSG_SM_POS = 0x02

RECEIVE_TIMEOUT = datetime.timedelta(milliseconds=200)

FLAP_UNITS = 32
FLAP_ALPHABET = "~0123456789abc"
FLAP_FINAL_LEN = 14
FLAP_NUMBERS = "~0123456789"
FLAP_NUMBERS_COUNT = 5

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
    _data.insert(0, UART_RECEIVE_MAGIC)
    _data.append(xor(data))

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
        if all([pos == 0 for pos in positions]):
            send_positions = True

    elif data[2] == UART_MSG_SM_SENS:
        print(f'Sensors: {data[3]:#010b} {data[4]:#010b} {data[5]:#010b} {data[6]:#010b}')


def flap_number(num: int) -> List[int]: # always returns list of length FLAP_NUMBERS_COUNT
    numstr = str(num).rjust(FLAP_NUMBERS_COUNT, '~')[-FLAP_NUMBERS_COUNT:]
    return [FLAP_NUMBERS.index(char) for char in numstr]


def flap_final(final: str) -> List[int]: # always returns list of length FLAP_FINAL_LEN
    return [FLAP_ALPHABET.index(char) for char in final.lower().ljust(FLAP_FINAL_LEN, '~')]


def flap_all_positions(content: Dict) -> List[int]: # always returns list of length FLAP_UNITS
    result = [0]*FLAP_UNITS
    for i, pos in enumerate(flap_final(content["final"])):
        result[i] = pos
    return result


if __name__ == '__main__':
    global send_positions
    send_positions = False
    positions_sent = False

    if len(sys.argv) != 3:
        sys.stderr.write(__doc__.strip()+'\n')
        sys.exit(1)

    with open(sys.argv[2]) as f:
        positions = json.loads(f.read())
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
