#!/usr/bin/env python3
# -*- mode: python; coding: utf-8 -*-
# Copyright © 2018 Göran Weinholt <goran@weinholt.se>
# SPDX-License-Identifier: LGPL-3.0-or-later

# SteelSeries Siberia 350 control software.

import argparse
import contextlib
import re
import usb1                     # python-libusb1

# Equalizer
CMD_REG_EQL_80 = 0x40
CMD_REG_EQL_280 = 0x41
CMD_REG_EQL_1K = 0x42
CMD_REG_EQL_3_5K = 0x43
CMD_REG_EQL_13K = 0x44
CMD_EQL_SELECT = 0x46
CMD_EQL_DATA = 0x47
CMD_UNKNOWN_49 = 0x49
CMD_UNKNOWN_4A = 0x4A

EQL_BANDS = (
    '80 Hz', '280 Hz', '1 kHz', '3.5 kHz', '13 kHz'
)

EQL_REGISTERS = (
    CMD_REG_EQL_80,
    CMD_REG_EQL_280,
    CMD_REG_EQL_1K,
    CMD_REG_EQL_3_5K,
    CMD_REG_EQL_13K,
)

EQL_DATA = ( # Unknown magic. Some are repeated.
    ( # 80 Hz.
        (0x3f, 0xa4, 0x76, 0xd0, 0xe0, 0x5a, 0xa5, 0xd, 0x0, 0x2d, 0x52, 0x86),
        (0x30, 0x4d, 0xc8, 0x89, 0xe9, 0xb2, 0x7e, 0x76, 0x4, 0xd9, 0x3f, 0x3b),
        (0x3f, 0xcf, 0x1, 0x46, 0xe0, 0x30, 0x1d, 0x1, 0x0, 0x18, 0xe, 0x80),
    ),
    ( # 280 Hz
        (0x3e, 0x5d, 0xf4, 0xfa, 0xe1, 0x97, 0xe2, 0xcc, 0x0, 0xcb, 0xf1, 0x66),
        (0x30, 0x4d, 0xc8, 0x89, 0xe9, 0xb2, 0x7e, 0x76, 0x4, 0xd9, 0x3f, 0x3b),
        (0x3f, 0x2c, 0xbd, 0x6e, 0xe0, 0xc9, 0x40, 0x1f, 0x0, 0x64, 0xa0, 0xf),
    ),
    ( # 1K
        (0x3a, 0xcf, 0xbd, 0x1e, 0xe4, 0xab, 0x5e, 0xfb, 0x2, 0x55, 0xaf, 0x7d),
        (0x3f, 0xa4, 0x76, 0xd0, 0xe0, 0x5a, 0xa5, 0xd, 0x0, 0x2d, 0x52, 0x86),
        (0x3d, 0x4d, 0x31, 0x77, 0xe2, 0x25, 0x7e, 0x8f, 0x1, 0x12, 0xbf, 0x47),
    ),
    ( # 3.5K
        (0x2d, 0x41, 0x3c, 0xcc, 0xed, 0x86, 0x58, 0xba, 0x6, 0xc3, 0x2c, 0x5d),
        (0xf7, 0xb2, 0x5, 0x97, 0xfc, 0x36, 0x69, 0xb4, 0xe, 0x1b, 0x34, 0xda),
        (0x30, 0x4d, 0xc8, 0x89, 0xe9, 0xb2, 0x7e, 0x76, 0x4, 0xd9, 0x3f, 0x3b),
    ),
    ( # 13K
        (0xfd, 0x9f, 0xcc, 0xf6, 0xfd, 0x7b, 0x46, 0x8e, 0xe, 0xbd, 0xa3, 0x47),
        (0x3d, 0x4d, 0x31, 0x77, 0xe2, 0x25, 0x7e, 0x8f, 0x1, 0x12, 0xbf, 0x47),
        (0xf7, 0xb2, 0x5, 0x97, 0xfc, 0x36, 0x69, 0xb4, 0xe, 0x1b, 0x34, 0xda),
    )
)

# Color.
CMD_UNKNOWN_80 = 0x80
CMD_SET_COLOR = 0x83
CMD_UNKNOWN_93 = 0x93
CMD_UNKNOWN_95 = 0x95

# Microphone.
CMD_MICROPHONE = 0xf0
# MIC_BLOB_0 = '0100fe01005b00000000000000000000'
# MIC_BLOB_1 = '010000005b0027000000000000000000'
# CMD_MIC_0 = 0x5e
# CMD_MIC_1 = 0x5d
# MIC_MIN = 0x02
# MIC_MUTE = 0x40
# MIC_MAX = 0x1c

def headset_command(command, payload):
    """Format a payload for a USB control write to the headset."""
    cmd = [0x01, 0x00, command, len(payload)] + payload
    cmd += [0] * (16 - len(cmd))

    return bytearray(cmd)


class Headset(object):
    """Class for controlling the headset."""

    VENDOR_ID = 0x1038
    # PRODUCT_ID = 0x1229
    PRODUCT_ID = 0x12AA
    # INTERFACE_NUM = 3
    INTERFACE_NUM = 5

    def __init__(self):
        self.context = usb1.USBContext()
        self.context.setDebug(usb1.LOG_LEVEL_DEBUG)
        self.handle = self.context.openByVendorIDAndProductID(self.VENDOR_ID, self.PRODUCT_ID)
        self.handle.setAutoDetachKernelDriver(True)
        self.handle.claimInterface(self.INTERFACE_NUM)

    def close(self):
        """Release USB resources."""
        self.handle.releaseInterface(self.INTERFACE_NUM)
        self.context.close()

    def _send(self, cmd, value=0x0206):
        """Send a control command to the headset.

        The command should be generated by :py:func:`headset_command`.

        """
        self.handle.controlWrite(usb1.TYPE_CLASS | usb1.RECIPIENT_INTERFACE,
                                 request=9, value=value, index=self.INTERFACE_NUM,
                                 data=cmd)

    def set_color(self, red, green, blue):
        """Set the color of the headset to the given RGB value (0-255 values)."""
        print("\nProduct name: {}".format(self.handle.getProduct()))
        commands = (
            headset_command(CMD_UNKNOWN_95, [0x80, 0xbf]),
            headset_command(CMD_UNKNOWN_80, [0x52, 0x20]),
            headset_command(CMD_SET_COLOR, [red, green, blue]),
            headset_command(CMD_UNKNOWN_93, [0x03, 0x80])
        )

        commands = []
        # 1.
        commands.append(bytearray(b"\x06\x81\x43\x01\x22\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 2.
        commands.append(bytearray(b"\x06\x8a\x42\x00\x20\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 3.
        commands.append(bytearray(b"\x06\x81\x43\x01\x23\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 4. Color #deadff
        commands.append(bytearray(b"\x06\x8a\x42\x00\x20\x41\x00\xde\xea\xff\xff\x52\x00\xc8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 5.
        commands.append(bytearray(b"\x06\x81\x43\x01\x23\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 6.
        commands.append(bytearray(b"\x06\x8a\x42\x00\x20\x41\x08\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 7.
        commands.append(bytearray(b"\x06\x81\x43\x01\x23\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 8.
        commands.append(bytearray(b"\x06\x8a\x42\x00\x20\x60\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 9.
        commands.append(bytearray(b"\x06\x81\x43\x01\x23\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 10.
        commands.append(bytearray(b"\x06\x8a\x42\x00\x20\x40\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
        # 11.
        commands.append(bytearray(b"\x06\x81\x43\x01\x23\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))

        for cmd in commands:
            print(len(cmd))
            print(cmd)
            self._send(cmd)

        # Pre save
        command = bytearray(b"\x04\x40\x01\x11\x54\x9b\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00")
        print(len(command))
        print(command)
        self._send(command, value=0x0204)

        # Save
        command = bytearray(b"\x21\x01")
        print(len(command))
        print(command)
        self._send(command, value=0x0221)

    def set_microphone_optimization(self, enable):
        """Enable or disable microphone automatic optimization."""
        cmd = headset_command(CMD_MICROPHONE, [0xf1 if enable else 0x00])
        self._send(cmd)

    def set_equalizer(self, band, value):
        """Set the value for an equalizer band.

        Bands: {0: '80 Hz', 1: '280 Hz', 2: '1 kHz', 3: '3.5 kHz', 4: '13 kHz'}.
        Value is between 0x00 and 0x30 (-12 dB to +12 dB, 0x18 = 0 dB).

        """
        assert 0 <= band <= 5
        assert 0x00 <= value <= 0x30
        zero_db = 0x18

        prologue = [
            headset_command(EQL_REGISTERS[band], [zero_db]),
            headset_command(CMD_EQL_SELECT, [0x0d]),
            headset_command(CMD_EQL_SELECT, [band + 1])
        ]

        if value < 0x18:
            values = EQL_DATA[band][0]
        elif value > 0x18:
            values = EQL_DATA[band][2]
        else:
            values = EQL_DATA[band][1]

        value_cmds = [headset_command(CMD_EQL_DATA, [val]) for val in values]

        epilogue = [
            headset_command(CMD_UNKNOWN_4A, [0x00]),
            headset_command(CMD_UNKNOWN_49, [0x04]),
            headset_command(EQL_REGISTERS[band], [value]),
            headset_command(CMD_EQL_SELECT, [0x0d]),
        ]

        for cmd in prologue + value_cmds + epilogue:
            self._send(cmd)


def main():
    parser = argparse.ArgumentParser(description='Siberia 350 control')
    parser.add_argument('--color',
                        help='set the color of the headset LEDs (rrggbb)')
    parser.add_argument('--mic-auto', dest='mic_auto', action='store_true', default=None,
                        help='enable mic auto optimization')
    parser.add_argument('--no-mic-auto', dest='mic_auto', action='store_false', default=None,
                        help='disable mic auto optimization')
    parser.add_argument('--equalizer',
                        help='set the equalizer (e.g. 0,0,0,0,0)')
    args = parser.parse_args()
    if args.color is None and args.mic_auto is None and args.equalizer is None:
        parser.print_help()

    with contextlib.closing(Headset()) as headset:
        if args.color is not None:
            color = re.findall('[0-9A-Fa-f]{2}', args.color)
            if len(color) != 3:
                parser.error('invalid color: %r' % args.color)
            red, green, blue = (int(c, 16) for c in color)
            print("Setting color to %02x%02x%02x" % (red, green, blue))
            headset.set_color(red, green, blue)

        if args.mic_auto is not None:
            if args.mic_auto:
                print('Enabling mic auto optimization')
            else:
                print('Disabling mic auto optimization')
            headset.set_microphone_optimization(args.mic_auto)

        if args.equalizer is not None:
            values = [float(x) if x != '' else '' for x in args.equalizer.split(',')]
            if len(values) != 5 or not all(v == '' or -12 <= v <= 12 for v in values):
                parser.error('invalid equalizer setting: %r' % values)
            print('Setting equalizer:')
            for band, value in enumerate(values):
                if value != '':
                    print(" {:>7} - {:>5} dB".format(EQL_BANDS[band], value))
                    headset.set_equalizer(band, int(2 * (value + 12)))


if __name__ == '__main__':
    main()
