#!/usr/bin/env python3
"""
This program processes a candump file and attempts to decode
each message with the given .dbc. It will print the raw CAN
message along with a binary representation and the decimal
value of the message.

The -k option filters to only those known in the .dbc.
The -u option filters to only those unknown in the .dbc.

This could be handy in "eye-balling" potential field boundaries
when reverse engineering, or maybe not.
"""
import os
import re
import sys
from CAN import CAN
from DBC import DBC


def print_bitfield(name, indent_n, sgs):
    """
    This prints a representation of the 64 bits with markers at the
    field boundaries.
    """
    tiks = {}
    for sg in reversed(sgs):
        end_bit = int(sg.start_bit) + int(sg.bit_len) - 1
        tiks[end_bit] = True
        tiks[int(sg.start_bit)] = True
    indent_n -= len(name)
    print(name, end="")
    print(''.join([' ' for n in range(indent_n + 2)]), end="[")
    for col in reversed(range(64)):
        if col in tiks:
            print('|', end="")
        else:
            print(' ', end="")
    print("]")


def run(dbc_filename, can_filename, known_option):

    dbc = DBC(dbc_filename)

    last_code = 0

    with open(can_filename, 'r') as can_fh:
        for line in can_fh:
            event = CAN(line)
            event_str = str(event)
            bo = dbc.query(dbc.BO_, event)
            if bo is None:
                if known_option == '-k':
                    continue
            else:
                if known_option == '-u':
                    continue
            if last_code != event.code:
                print(''.join(['=' for n in range(124)]))
            if bo is not None:
                print_bitfield(bo.name, len(event_str), bo.sgs)
            print(event_str, end=f' : {event.bin_str} = {event.value}\n')
            last_code = event.code

    return True


if __name__ == '__main__':
    if len(sys.argv) < 3:
        raise Exception(f'USAGE {sys.argv[0]} <filename>.dbc <candump-ouput> [-u|-k]')
    if not os.path.exists(sys.argv[1]):
        raise Exception(f'No such file: {sys.argv[1]}')
    if not os.path.exists(sys.argv[2]):
        raise Exception(f'No such file: {sys.argv[2]}')
    known_option = '-a'
    if len(sys.argv) > 3:
        if sys.argv[3] not in ['-u', '-k']:
            raise Exception(f'{sys.argv[3]} should be either -u (unknonw) or -k (known)')
        else:
            known_option = sys.argv[3]
    run(sys.argv[1], sys.argv[2], known_option)
