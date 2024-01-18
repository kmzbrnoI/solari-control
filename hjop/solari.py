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
from typing import Dict
import subprocess
import json

import ac.blocks
import ac.panel_client as panel_client
import ac.events as events
import utils.blocks
from ac import pt as pt

DEVICE = '/dev/ttyAMA0'
SIDES = ['A', 'B']

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

ENABLE_BLOCK_ID = 5001


def show_train(train: Dict) -> bool:
    global track_id
    logging.info(f'Showing train {train} ...')

    if not train.get('announcement', False):
        return False
    if train['type'] not in TYPES:
        return False

    content = {
        'num': train['name'],
        'type': TYPES[train['type']],
        'num_red': train['type'] in ['Ec', 'Ic', 'Ex', 'R'],
        'direction2': 'S3',
    }

    if 'areaTo' in train:
        content['final'] = pt.get(f'/areas/{train["areaTo"]}')['area']['name']

    if content['final'] == 'Odbočka Čejč':
        content['final'] = 'Brno hlavní n.'
        content['direction1'] = 'Vranovice'

    podj_time = train.get('podj', {}).get(str(track_id), {}).get('absolute', None)
    if podj_time is not None:
        date, time = podj_time.split('T')
        hours, minutes, seconds = time.split(':')
        hours = str(int(hours)+1)
        content['time'] = f'{hours}:{minutes}'

    with open('content.json', 'w') as file:
        file.write(json.dumps(content, indent='\t', ensure_ascii=False))

    for side in SIDES:
        result = subprocess.run(
            ['../sw/control.py', 'set_positions', '--file=content.json', DEVICE, side]
        )
        if result.returncode != 0:
            logging.error('control.py returned nonzero status!')
            return False
    return True


def clear() -> None:
    logging.info('Resetting...')
    for side in SIDES:
        subprocess.run(['../sw/control.py', 'reset', DEVICE, side])


def on_enable_change(block) -> None:
    global track_id
    on_track_change(utils.blocks.state(track_id))


def on_track_change(block) -> None:
    if not utils.blocks.state(ENABLE_BLOCK_ID).get('activeOutput', False):
        logging.info('on_track_change: enable block disabled.')
        return

    if 'blockState' in block:
        block = block['blockState']
    trains = block.get('trains', [])
    predict = block.get('trainPredict', '')
    train = None

    if trains:
        train = pt.get(f'/trains/{trains[0]}')['train']
    elif predict != '':
        train = pt.get(f'/trains/{predict}')['train']

    if train is not None:
        ok = show_train(train)
        if ok:
            logging.info('Done')
        else:
            logging.info('show_train returned False!')
            clear()
    else:
        clear()


@events.on_connect
def on_connect():
    global track_id
    track_id = int(args['<track_id>'])
    ac.blocks.register_change(on_track_change, track_id)
    ac.blocks.register_change(on_enable_change, ENABLE_BLOCK_ID)
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
