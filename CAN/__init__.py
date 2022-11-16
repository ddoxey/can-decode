import re
from pprint import pprint


class CAN:
    """
    The CAN class parses a raw line from can-utils candump.
    """
    text, interface, code, byte_n, value = None, None, None, None, None

    def __init__(self, line):
        self.text = re.sub(r'\s+', ' ', line).strip()
        tokens = self.text.split(' ')
        self.interface = tokens[0]
        self.code = int(tokens[1], 16)
        self.byte_n = int(tokens[2].strip('[]'))
        self.bytes = tokens[3:]

    def get_hex_bytes(self, endian = 1):
        hex_bytes = self.bytes
        if endian == 0:
            hex_bytes = reversed(hex_bytes)
        return hex_bytes

    def get_hex_str(self, endian = 1):
        hex_bytes = self.get_hex_bytes(endian)
        self.hex_str = ' '.join(hex_bytes)

    def get_value(self, endian = 1):
        hex_bytes = self.get_hex_bytes(endian)
        return int('0x{}'.format(''.join(hex_bytes)), 16)

    def get_binary_str(self, endian = 1):
        return format(self.get_value(endian), f'0{self.byte_n*8}b')

    def decode(self, sg):
        """
        Given an int value and a collection of signal syntax (SG) tokens this
        decodes out the encoded value.
        """
        sign = 0
        value = int(self.get_value(sg))
        bitmask = (pow(2, int(sg.bit_len)) - 1) << int(sg.start_bit)
        value = (value & bitmask)
        value = value >> int(sg.start_bit)
        if sg.signed:
            first_bitmask = pow(2, int(sg.bit_len) - 1)
            sign = (value & first_bitmask) >> (int(sg.bit_len) - 1)
            value = first_bitmask ^ value
        value = sg.offset + sg.scale * value
        if sign == 1:
            value *= -1
        if sg.min_val < sg.max_val:
            value = max(value, sg.min_val)
        if sg.max_val > sg.min_val:
            value = min(sg.max_val, value)
        value = re.sub(r'[.]0$', "", str(value))
        if sg.units != "":
            return f'{value} {sg.units}'
        return value

    def __str__(self):
        return f'{self.interface} {self.code} [{self.byte_n}] {self.get_hex_str()}'
