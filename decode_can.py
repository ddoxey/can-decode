#!/usr/bin/env python3
import os
import re
import sys
from pprint import pprint, pformat


class DBC:
    """
    The DBC class parses a .dbc file and uses the given data to identify,
    decode, and annotate CAN messages.
    """
    filename = None
    version = ""
    records = []

    def __init__(self, filename):
        self.filename = filename
        with open(self.filename, 'r') as dbc_fh:
            for line in dbc_fh:
                line = line.rstrip().rstrip(';').rstrip()
                if len(line) == 0:
                    continue
                if line.startswith('VERSION '):
                    self.version = line.split(' ', 1)[1].strip('"')
                    continue
                line = re.sub(r'\s+', ' ', line)
                if re.match(r'[A-Z_]+_([ ]*[:]|[ ].+)', line):
                    type_name, attributes = None, None
                    if ' ' in line:
                        type_name, attributes = line.strip().split(' ', 1)
                        if attributes == ':':
                            type_name += ':'
                            attributes = None
                    else:
                        type_name = line.strip()
                    if type_name == 'BO_':
                        self.add_record(type_name, attributes)
                    elif type_name == 'VAL_TABLE_':
                        attr_a, attr_b = attributes.split(' ', 1)
                        self.add_record(type_name, attr_a)
                        subrecords = attr_b.split(' ')
                        while len(subrecords) > 0:
                            self.add_subrecord(type=subrecords.pop(1),
                                               attr=subrecords.pop(0))
                    elif type_name == 'VAL_':
                        attr_a, attr_b, attr_c = attributes.split(' ', 2)
                        self.add_record(type_name, f'{attr_a} {attr_b}')
                        subrecords = attr_c.split(' ')
                        while len(subrecords) > 0:
                            self.add_subrecord(type=subrecords.pop(1),
                                               attr=subrecords.pop(0))
                    elif type_name == 'BA_':
                        attrs = attributes.split(' ', 4)
                        last_i = len(attrs) - 1
                        self.add_record(type_name, ' '.join(attrs[0:last_i]))
                        subrecords = attrs[last_i].strip('"').split(',')
                        for subrec in subrecords:
                            self.add_subrecord(type=subrec.strip())
                    elif type_name == 'CM_':
                        attrs = attributes.split(' ', 3)
                        self.add_record(type_name, ' '.join(attrs[0:3]))
                        self.add_subrecord(type=attrs[3])
                    else:
                        if type_name.endswith(':'):
                            self.add_record(type_name.rstrip(':'))
                            if attributes is not None:
                                for subrec in attributes.split(' '):
                                    self.add_subrecord(type=subrec)
                        else:
                            self.add_record(type_name, attributes)
                    continue
                if re.match(r'\s+[A-Z_]+', line):
                    line = line.strip()
                    if ' ' in line:
                        type_name, attributes = line.strip().split(' ', 1)
                        if type_name == 'SG_':
                            attr_a, attr_b = attributes.split(':', 1)
                            self.add_subrecord(
                                type=type_name,
                                attr=attr_a.strip(),
                                subrecords=attr_b.strip().split(' '))
                        else:
                            self.add_subrecord(type=type_name,
                                               attr=attributes)
                    else:
                        self.add_subrecord(type=line)
                    continue
                raise Exception(f'Failed to parse: >{line}<')

    def add_record(self, type_name, attributes=None):
        """
        Append a new record with the given name and attributes.
        """
        record = {
            'type': type_name.strip('"'),
            'subrecords': []
        }
        if attributes is not None:
            if re.match(r'[0-9A-F]+[ ]', attributes):
                record['id'], record['attr'] = attributes.split(' ', 1)
            elif re.match(r'[0-9A-F]+$', attributes):
                record['id'] = attributes
        self.records.append(record)

    def add_subrecord(self, **kwargs):
        """
        Add a subrecord to the most recently added record.
        """
        subrec = {}
        for param in ['type', 'attr', 'subrecords']:
            if param in kwargs:
                if isinstance(kwargs[param], str):
                    subrec[param] = kwargs[param].strip('"')
                else:
                    subrec[param] = [p.strip('"') for p in kwargs[param]]
        self.records[-1]['subrecords'].append(subrec)

    def query(self, type_name, id_where):
        """
        Search records and return the first one that matches the
        given type and id.
        """
        for record in [r for r in self.records if r['type'] == type_name]:
            if 'id' not in record:
                continue
            if record['id'] == id_where:
                return record
        return None

    def decode(self, value, sg_fields):
        """
        Given an int value and a collection of signal syntax (SG) tokens this
        decodes out the encoded value.
        """
        start_bit, bit_len, endian = re.split(r'[|@]', sg_fields[0])
        scale, offset = [float(n) for n in sg_fields[1].strip('()').split(',', 1)]
        min_val, max_val = [float(n) for n in sg_fields[2].strip('[]').split('|', 1)]
        unit = sg_fields[3]
        bitmask = (pow(2, int(bit_len)) - 1) << int(start_bit)
        value = int(value) & bitmask
        value = offset + scale * value
        if min_val < max_val:
            value = max(value, min_val)
        if max_val > min_val:
            value = min(max_val, value)
        value = re.sub(r'[.]0$', "", str(value))
        if unit != "":
            return f'{value} {unit}'
        return value

    def annotate(self, event):
        """
        Given a CAN event this will identify and
        return an annotated and decoded message.
        """
        msg = {
            'code': None,
            'name': None,
            'byte_n': None,
            'from': None,
            'fields': {}
        }
        ob = self.query('BO_', event.code)
        if ob is not None:
            msg['code'] = event.code
            msg['name'], msg['byte_n'], msg['from'] = ob['attr'].split(' ', 2)
            for sg in ob['subrecords']:
                msg['fields'][sg['attr']] = {
                    'value': self.decode(event.value, sg['subrecords']),
                    'to': sg['subrecords'][-1]
                }
        if msg['code'] is None:
            return None
        return msg

    def __str__(self):
        return 'FILE: {}\nVERSION: {}\n{}'.format(self.filename,
                                                  self.version,
                                                  pformat(self.records))


class CAN:
    """
    The CAN class parses a raw line from can-utils candump.
    """
    interface, code, byte_n, value = None, None, None, None

    def __init__(self, line):
        tokens = re.sub(r'\s+', ' ', line).strip().split(' ')
        self.interface = tokens[0]
        self.code = tokens[1]
        self.byte_n = tokens[2].strip('[]')
        self.hex_str = ' '.join(tokens[3:])
        self.value = int('0x{}'.format(''.join(tokens[3:])), 16)

    def __str__(self):
        return f'{self.interface} {self.code} [{self.byte_n}] {self.hex_str}'


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
