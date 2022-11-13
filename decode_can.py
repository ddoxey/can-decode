#!/usr/bin/env python3
"""
This decodes the given candump log with the given .dbc file.
The messages that can be decoded are printed with their ID
number, message name, field name, decoded value, units, and
the module from => to relationship.
"""
import os
import re
import sys
from pprint import pprint, pformat
from DBC import DBC
from CAN import CAN


def run(dbc_filename, can_filename):

    dbc = DBC(dbc_filename)

    with open(can_filename, 'r') as can_fh:
        for line in can_fh:
            event = CAN(line)
            message = dbc.annotate(event)
            if message is not None:
                code, name, from_node, fields = message['code'], \
                                                message['name'], \
                                                message['from'], \
                                                message['fields']
                for field_name in fields:
                    value, to_node = fields[field_name]['value'], \
                                     fields[field_name]['to']
                    print(f'[{code}] {name}:{field_name} = {value} ({from_node} => {to_node})')

    return True


if __name__ == '__main__':
    if len(sys.argv) != 3:
        raise Exception(f'USAGE {sys.argv[0]} <filename>.dbc <candump-ouput>')
    if not os.path.exists(sys.argv[1]):
        raise Exception(f'No such file: {sys.argv[1]}')
    if not os.path.exists(sys.argv[2]):
        raise Exception(f'No such file: {sys.argv[2]}')
    run(sys.argv[1], sys.argv[2])
