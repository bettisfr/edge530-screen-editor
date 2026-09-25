#!/usr/bin/env python3
__version__ = "1.0.0"  # stable since initial creation; see git log once initialized
"""
FIT file CRC-16 -- Garmin's standard nibble-table algorithm (matches the
reference implementation in the public FIT SDK's C source). The trailing
2 bytes of every .fit file are this CRC computed over every preceding byte
(file header included, trailing CRC itself excluded).

Self-verified in __main__ against every real .fit file we have on hand --
if this doesn't reproduce the existing trailing CRC on an UNMODIFIED file,
something is wrong with the algorithm and nothing built on top of it
should be trusted.
"""

CRC_TABLE = [
    0x0000, 0xCC01, 0xD801, 0x1400, 0xF001, 0x3C00, 0x2800, 0xE401,
    0xA001, 0x6C00, 0x7800, 0xB401, 0x5000, 0x9C01, 0x8801, 0x4400,
]


def fit_crc_update(crc, byte):
    tmp = CRC_TABLE[crc & 0xF]
    crc = (crc >> 4) & 0x0FFF
    crc = crc ^ tmp ^ CRC_TABLE[byte & 0xF]

    tmp = CRC_TABLE[crc & 0xF]
    crc = (crc >> 4) & 0x0FFF
    crc = crc ^ tmp ^ CRC_TABLE[(byte >> 4) & 0xF]

    return crc & 0xFFFF


def fit_crc(data):
    """CRC-16 over an entire byte sequence."""
    crc = 0
    for b in data:
        crc = fit_crc_update(crc, b)
    return crc


if __name__ == '__main__':
    import sys
    import struct
    import glob

    paths = sys.argv[1:] if len(sys.argv) > 1 else sorted(glob.glob('/mnt/user-data/uploads/*.fit'))
    all_ok = True
    for path in paths:
        with open(path, 'rb') as f:
            data = f.read()
        body = data[:-2]
        expected = struct.unpack('<H', data[-2:])[0]
        computed = fit_crc(body)
        ok = (computed == expected)
        all_ok &= ok
        status = 'OK' if ok else '** MISMATCH **'
        print(f'{path}: file_trailing_crc={expected:#06x}  computed={computed:#06x}  {status}')

    print()
    print('ALL PASS' if all_ok else 'CRC IMPLEMENTATION IS WRONG -- DO NOT USE FOR WRITES')
