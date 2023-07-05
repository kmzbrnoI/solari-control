#!/usr/bin/env python3
# run with unbuffered output: ‹python3 -u read.py /dev/ttyACM0›
# To send data run e.g. `echo -ne '\xCA\x01\x02\xAA\x63' > /dev/ttyUSB1`

import serial
import sys
import datetime


assert len(sys.argv) >= 2

ser = serial.Serial(sys.argv[1], 115200)

while True:
    chars = ser.read(1)
    if not chars:
        continue
    if chars[0] == 0xB7:
        print()
        print(f'[{datetime.datetime.now().time()}]', end=' ')
    print(hex(chars[0]), end=' ')
