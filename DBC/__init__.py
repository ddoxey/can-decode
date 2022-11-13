import re
from pprint import pformat, pprint


class DBC:
    """
    The DBC class parses a .dbc file and uses the given data to identify,
    decode, and annotate CAN messages.
    """
    class LIST_:
        id = 0
        name = None
        items = []

        def __init__(self, raw_text):
            elements = raw_text.split(' ')
            self.name = elements.pop(0).rstrip(':')
            self.items = [item for item in [e.strip() for e in elements] if item != ""]

        def append(self, item):
            if not isinstance(item, str):
                raise Exception(f'Invalid object appended to {__class__}: {type(item)}')
            self.items.append(item)

    class BO_:
        id = 0
        name = None
        byte_n = None
        origin = None
        sgs = []

        def __init__(self, raw_text):
            elements = raw_text.split(' ')
            self.id = int(elements[0])
            self.name = elements[1].rstrip(':')
            self.byte_n = int(elements[2])
            self.origin = elements[3]

        def append(self, sg):
            if not isinstance(sg, DBC.SG_):
                raise Exception(f'Invalid object appended to {__class__}: {type(sg)}')
            self.sgs.append(sg)

    class SG_:
        id = 0
        name = None
        start_bit, bit_length, endian = None, None, None
        scale, offset = None, None
        min_val, max_val = None, None
        units, destination = None, None

        def __init__(self, raw_text):
            attr_a, attr_b = raw_text.split(':', 1)
            self.name = attr_a.strip()
            elements = attr_b.strip().split(' ')
            self.start_bit, self.bit_len, self.endian = re.split(r'[|@]', elements[0])
            self.scale, self.offset = [float(n) for n in elements[1].strip('()').split(',', 1)]
            self.min_val, self.max_val = [float(n) for n in elements[2].strip('[]').split('|', 1)]
            self.units = elements[3].strip('"')
            self.destination = elements[4].strip('"')

        def append(self, row):
            raise Exception(f'Cannot append to {__class__}')

    class BO_TX_BU_:
        id = 0
        modules = []

        def __init__(self, raw_text):
            attr_a, attr_b = raw_text.split(':', 1)
            self.id = int(attr_a.strip())
            self.modules = attr_b.strip().split(',')

        def append(self, module):
            if not isinstance(module, str):
                raise Exception(f'Invalid object appended to {__class__}: {type(module)}')
            self.modules.append(module)

    class BA_DEF_DEF_:
        id = 0
        name = None
        value = None

        def __init__(self, raw_text):
            attr_a, attr_b = raw_text.split(' ', 1)
            self.name = attr_a.strip('"')
            self.value = attr_b.strip('"')

        def append(self, _):
            raise Exception(f'Cannot append to {__class__}')

    class BA_DEF_:
        id = 0
        name = None
        data_type = None
        library = []

        def __init__(self, raw_text):
            elements = raw_text.split(' ')
            self.name = elements.pop(0).strip('"')
            self.data_type = elements.pop(0)
            if len(elements) > 0 and ',' in elements[0]:
                self.library = [e.strip('"') for e in elements.split(',')]
            else:
                self.library = elements

        def append(self, value):
            if not isinstance(value, str):
                raise Exception(f'Invalid object appended to {__class__}: {type(value)}')
            self.library.append(value.strip('"'))

    class VAL_TABLE_:
        id = 0
        name = None
        rows = []

        def __init__(self, raw_text):
            attr_a, attr_b = raw_text.split(' ', 1)
            self.name = attr_a.strip()
            elements = attr_b.split(' ')
            while len(elements) > 0:
                self.rows.append({'type': elements.pop(1),
                                  'index': elements.pop(0)})

        def append(self, row):
            if not isinstance(row, dict):
                raise Exception(f'Invalid object appended to {__class__}: {type(row)}')
            self.rows.append(row)

    class VAL_:
        id = 0
        name = None
        rows = []

        def __init__(self, raw_text):
            attr_a, attr_b, attr_c = raw_text.split(' ', 2)
            self.name = f'{attr_a} {attr_b}'
            elements = attr_c.split(' ')
            while len(elements) > 0:
                self.rows.append({'type': elements.pop(1),
                                  'name': elements.pop(0)})

        def append(self, row):
            if not isinstance(row, dict):
                raise Exception(f'Invalid object appended to {__class__}: {type(row)}')
            self.rows.append(row)

    class BA_:
        id = 0
        name = None
        rows = []

        def __init__(self, raw_text):
            attrs = raw_text.split(' ', 4)
            last_i = len(attrs) - 1
            self.name = ' '.join(attrs[0:last_i])
            elements = attrs[last_i].strip('"').split(',')
            for element in elements:
                self.rows.append({'type': element.strip()})

        def append(self, row):
            if not isinstance(row, dict):
                raise Exception(f'Invalid object appended to {__class__}: {type(row)}')
            self.rows.append(row)

    class CM_:
        id = 0
        bo_id = None
        text = None

        def __init__(self, raw_text):
            attrs = raw_text.split(' ', 3)
            self.bo_id = int(attrs[1])
            self.text = ' '.join(attrs[2:]).strip('"')

        def append(self, _):
            raise Exception(f'Cannot append to {__class__}')

    class SIG_GROUP_:
        id = 0
        bo_id = None
        name = None
        members = []

        def __init__(self, raw_text):
            attr_a, attr_b = raw_text.split(':', 1)
            self.bo_id = int(attr_a.split(' ', 1)[0])
            self.name = attr_a.split(' ', 1)[1].strip()
            self.members = attr_b.strip().split(' ')

        def append(self, _):
            raise Exception(f'Cannot append to {__class__}')

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
                        self.add_record(self.BO_(attributes))
                    elif type_name == 'BO_TX_BU_':
                        self.add_record(self.BO_TX_BU_(attributes))
                    elif type_name == 'BA_DEF_':
                        self.add_record(self.BA_DEF_(attributes))
                    elif type_name == 'BA_DEF_DEF_':
                        self.add_record(self.BA_DEF_DEF_(attributes))
                    elif type_name == 'VAL_TABLE_':
                        self.add_record(self.VAL_TABLE_(attributes))
                    elif type_name == 'VAL_':
                        self.add_record(self.VAL_(attributes))
                    elif type_name == 'BA_':
                        self.add_record(self.BA_(attributes))
                    elif type_name == 'CM_':
                        self.add_record(self.CM_(attributes))
                    elif type_name == 'SIG_GROUP_':
                        self.add_record(self.SIG_GROUP_(attributes))
                    else:
                        if type_name.endswith(':'):
                            self.add_record(self.LIST_(type_name.rstrip(':')))
                            if attributes is not None:
                                for subrec in attributes.split(' '):
                                    self.add_subrecord(subrec)
                        else:
                            raise Exception(f'Unrecognized entry: {type_name} {attributes}')
                    continue
                if re.match(r'\s+[A-Z_]+', line):
                    line = line.strip()
                    if ' ' in line:
                        type_name, attributes = line.strip().split(' ', 1)
                        if type_name == 'SG_':
                            self.add_subrecord(self.SG_(attributes))
                        else:
                            self.add_subrecord({'type': type_name,
                                                'attr': attributes})
                    else:
                        self.add_subrecord(line.strip())
                    continue
                raise Exception(f'Failed to parse: >{line}<')

    def add_record(self, dbc_object):
        """
        Append a new record with the given name and attributes.
        """
        self.records.append(dbc_object)

    def add_subrecord(self, dbc_object):
        """
        Add a subrecord to the most recently added record.
        """
        self.records[-1].append(dbc_object)

    def query(self, type_name, event):
        """
        Search records and return the first one that matches the
        given type and event.id.
        """
        for record in [r for r in self.records if isinstance(r, type_name)]:
            if record.id == event.code:
                return record
        return None

    def decode(self, value, sg):
        """
        Given an int value and a collection of signal syntax (SG) tokens this
        decodes out the encoded value.
        """
        # TODO account for sg.endian (0+ 0- 1+ 1-)
        bitmask = (pow(2, int(sg.bit_len)) - 1) << int(sg.start_bit)
        value = int(value) & bitmask
        value = sg.offset + sg.scale * value
        if sg.min_val < sg.max_val:
            value = max(value, sg.min_val)
        if sg.max_val > sg.min_val:
            value = min(sg.max_val, value)
        value = re.sub(r'[.]0$', "", str(value))
        if sg.units != "":
            return f'{value} {sg.units}'
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
        ob = self.query(self.BO_, event)
        if ob is not None:
            msg['code'] = event.code
            msg['name'], msg['byte_n'], msg['from'] = ob.name, ob.byte_n, ob.origin
            for sg in ob.sgs:
                msg['fields'][sg.name] = {
                    'value': self.decode(event.value, sg),
                    'to': sg.destination
                }
        if msg['code'] is None:
            return None
        return msg

    def __str__(self):
        return 'FILE: {}\nVERSION: {}\n{}'.format(self.filename,
                                                  self.version,
                                                  pformat(self.records))
