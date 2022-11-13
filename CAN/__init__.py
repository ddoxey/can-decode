import re


class CAN:
    """
    The CAN class parses a raw line from can-utils candump.
    """
    text, interface, code, byte_n, value = None, None, None, None, None

    def __init__(self, line):
        self.text = re.sub(r'\s+', ' ', line).strip()
        tokens = self.text.split(' ')
        self.interface = tokens[0]
        self.code = str(int(tokens[1], 16))
        self.byte_n = int(tokens[2].strip('[]'))
        self.value = int('0x{}'.format(''.join(tokens[3:])), 16)
        self.bin_str = format(self.value, '064b')
        self.hex_str = ' '.join(tokens[3:])

    def __str__(self):
        return f'{self.interface} {self.code} [{self.byte_n}] {self.hex_str}'


