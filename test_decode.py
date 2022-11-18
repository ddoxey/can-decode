#!/usr/bin/env python3
from DBC import DBC
from CAN import CAN
import unittest


class TestANDecode(unittest.TestCase):

    def run_dbc_decode(self, dbc_text, can_text, expect):

        dbc = DBC(dbc_text)

        event = CAN(can_text)

        # print(f'event: {event}')

        self.assertEqual(event.interface, expect['event_interface'])
        self.assertEqual(event.code, expect['event_code'])
        self.assertEqual(event.byte_n, expect['event_byte_n'])

        bo = dbc.query(DBC.BO_, event)

        # print(f'bo: {bo}')

        self.assertEqual(bo.name, expect['bo_name'])
        self.assertEqual(bo.byte_n, expect['bo_byte_n'])
        self.assertEqual(bo.origin, expect['bo_origin'])

        sg = bo.sgs[-1]

        self.assertEqual(sg.name, expect['sg_name'])
        self.assertEqual(sg.start_bit, expect['sg_start_bit'])
        self.assertEqual(sg.bit_len, expect['sg_bit_len'])
        self.assertEqual(sg.min_val, expect['sg_min_val'])
        self.assertEqual(sg.max_val, expect['sg_max_val'])
        self.assertEqual(sg.scale, expect['sg_scale'])
        self.assertEqual(sg.offset, expect['sg_offset'])
        self.assertEqual(sg.units, expect['sg_units'])
        self.assertEqual(sg.destination, expect['sg_destination'])

        value = event.decode(sg)

        self.assertEqual(value, expect['decoded_value'])

    def test_decode_value(self):
        """
            HEX:    F    F    F    F    F    F    F    F    0    1    0    0
            BIN: 1111 1111 1111 1111 1111 1111 1111 1111 0000 0001 0000 0000
                                                         |                 |
                                                        16                 1
            0 + (256 * 1) => 256
        """
        dbc_text = 'BO_ 1000 XYZ_message: 6 ABC\n' \
                   '    SG_ XYZ_messageID A : 0|16@1+ (1,0) [255|257] "MPH" XYZ\n'

        can_text = " can0 3E8 [6] FF FF FF FF 01 00"

        expect = {
            'event_interface': "can0",
            'event_code': 1000,
            'event_byte_n': 6,
            'bo_name': "XYZ_message",
            'bo_byte_n': 6,
            'bo_origin': "ABC",
            'sg_name': 'XYZ_messageID A',
            'sg_start_bit': '0',
            'sg_bit_len': '16',
            'sg_min_val': 255.0,
            'sg_max_val': 257.0,
            'sg_scale': 1.0,
            'sg_offset': 0.0,
            'sg_units': "MPH",
            'sg_destination': "XYZ",
            'decoded_value': '256 MPH',
        }

        self.run_dbc_decode(dbc_text, can_text, expect)

    def test_unsigned_scaled_offset(self):
        """
            HEX:    F    F    F    F    F    F    F    E    0    4    0    3
            BIN: 1111 1111 1111 1111 1111 1111 1111 1110 0000 0100 0000 0011
                                                       |                 |
                                                      15                 1
            150 + (256 * 2.5) => 790
        """
        dbc_text = 'BO_ 1001 XYZ_message: 6 ABC\n' \
                   '    SG_ XYZ_messageID B : 2|15@1+ (2.5,150) [3|4000] "MPH" XYZ\n'

        can_text = " can0 3E9 [6] FF FF FF FE 04 03"

        expect = {
            'event_interface': "can0",
            'event_code': 1001,
            'event_byte_n': 6,
            'bo_name': "XYZ_message",
            'bo_byte_n': 6,
            'bo_origin': "ABC",
            'sg_name': 'XYZ_messageID B',
            'sg_start_bit': '2',
            'sg_bit_len': '15',
            'sg_min_val': 3.0,
            'sg_max_val': 4000.0,
            'sg_scale': 2.5,
            'sg_offset': 150.0,
            'sg_units': "MPH",
            'sg_destination': "XYZ",
            'decoded_value': '790 MPH',
        }

        self.run_dbc_decode(dbc_text, can_text, expect)

    def test_negative_scaled_offset(self):
        """
            HEX:    F    F    F    F    F    F    F    F    0    4    0    3
            BIN: 1111 1111 1111 1111 1111 1111 1111 1111 0000 0100 0000 0011
                                                       |                 |
                                                      15                 1
            150 + (-256 * 2.5) => -790
        """
        dbc_text = 'BO_ 1001 XYZ_message: 6 ABC\n' \
                   '    SG_ XYZ_messageID B : 2|15@1- (2.5,150) [-3000|4] "MPH" XYZ\n'

        can_text = " can0 3E9 [6] FF FF FF FF 04 03"

        expect = {
            'event_interface': "can0",
            'event_code': 1001,
            'event_byte_n': 6,
            'bo_name': "XYZ_message",
            'bo_byte_n': 6,
            'bo_origin': "ABC",
            'sg_name': 'XYZ_messageID B',
            'sg_start_bit': '2',
            'sg_bit_len': '15',
            'sg_min_val': -3000.0,
            'sg_max_val': 4.0,
            'sg_scale': 2.5,
            'sg_offset': 150.0,
            'sg_units': "MPH",
            'sg_destination': "XYZ",
            'decoded_value': '-790 MPH',
        }

        self.run_dbc_decode(dbc_text, can_text, expect)

    def test_negative_scaled_offset_big_endian(self):
        """
            HEX:    F    F    F    F    F    F    F    F    0    4    0    3
            BIN: 1111 1111 1111 1111 1111 1111 1111 1111 0000 0100 0000 0011
                                                       |                 |
                                                      15                 1
            150 + (-256 * 2.5) => -790
        """
        dbc_text = 'BO_ 1001 XYZ_message: 6 ABC\n' \
                   '    SG_ XYZ_messageID B : 2|15@0- (2.5,150) [-3000|4] "MPH" XYZ\n'

        can_text = " can0 3E9 [6] 03 04 FF FF FF FF"

        expect = {
            'event_interface': "can0",
            'event_code': 1001,
            'event_byte_n': 6,
            'bo_name': "XYZ_message",
            'bo_byte_n': 6,
            'bo_origin': "ABC",
            'sg_name': 'XYZ_messageID B',
            'sg_start_bit': '2',
            'sg_bit_len': '15',
            'sg_min_val': -3000.0,
            'sg_max_val': 4.0,
            'sg_scale': 2.5,
            'sg_offset': 150.0,
            'sg_units': "MPH",
            'sg_destination': "XYZ",
            'decoded_value': '-790 MPH',
        }

        self.run_dbc_decode(dbc_text, can_text, expect)


if __name__ == '__main__':
    unittest.main()
