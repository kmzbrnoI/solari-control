#!/usr/bin/env python3

"""
Solari di Control platform table hJOP integration

Usage:
  solari.py [options] <track_id>
  solari.py --version

Options:
  -s <servername>    Specify hJOPserver address [default: 127.0.0.1]
  -p <port>          Specify hJOPserver port [default: 5896]
  -l <loglevel>      Specify loglevel (python logging package) [default: info]
  -h --help          Show this screen.
  --version          Show version.
"""

import sys
import logging
from docopt import docopt  # type: ignore
from typing import List, Dict
import subprocess
import json
import datetime

import ac.blocks
import ac.panel_client as panel_client
import ac.events as events
from ac import pt as pt
import utils.blocks

DEVICE = '/dev/ttyAMA0'
SIDE = 'B'

TYPES = {
    'Ec': 'Ec',
    'Ic': 'Ic',
    'Ex': 'Ex',
    'R': 'R',
    'Sp': 'Sp',
    'Os': 'Os',
    'MOs': 'Os',
    'Zvl': 'Zvláštní vlak',
}


def show_train(train: Dict) -> bool:
    global track_id
    logging.info(f'Showing train {train["name"]} ...')

    if train['type'] not in TYPES:
        return False

    content = {
        'num': train['name'],
        'type': TYPES[train['type']],
    }

    if 'areaTo' in train:
        content['final'] = pt.get(f'/areas/{train["areaTo"]}')['area']['name']

    podj_time = train.get('podj', {}).get(str(track_id), {}).get('absolute', None)
    if podj_time is not None:
        date, time = podj_time.split('T')
        hours, minutes, seconds = time.split(':')
        hours = str(int(hours)+1)
        content['time'] = f'{hours}:{minutes}'

    with open('content.json', 'w') as file:
        file.write(json.dumps(content, indent='\t'))

    _stdout = subprocess.run(['../sw/control.py', 'set_positions', '--file=content.json', DEVICE, SIDE])
    logging.info(_stdout)
    return True


def clear() -> None:
    logging.info('Resetting...')
    _stdout = subprocess.run(['../sw/control.py', 'reset', DEVICE, SIDE])
    logging.info(_stdout)


def on_track_change(block) -> None:
    trains = block['blockState'].get('trains', [])
    predict = block['blockState'].get('trainPredict', '')
    shown = False
    if trains:
        if not show_train(pt.get(f'/trains/{trains[0]}')['train']):
            clear()
    elif predict != '':
        if not show_train(pt.get(f'/trains/{predict}')['train']):
            clear()
    else:
        clear()


@events.on_connect
def on_connect():
    global track_id
    track_id = int(args['<track_id>'])
    ac.blocks.register_change(on_track_change, track_id)
    on_track_change(pt.get(f'/blocks/{track_id}?state=true')['block'])
    logging.info('Startup sequence finished')


if __name__ == '__main__':
    args = docopt(__doc__)

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

    panel_client.init(args['-s'], int(args['-p']))
