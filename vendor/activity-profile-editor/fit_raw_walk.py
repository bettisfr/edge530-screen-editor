#!/usr/bin/env python3
__version__ = "1.0.0"  # stable since initial creation; see git log once initialized
"""
Generic, profile-agnostic FIT message walker.
Logs every definition and data message with file byte offsets, so we can
locate exactly which message instance covers a given diff range - no
semantic interpretation of mesg_num, just structural decode per the FIT
protocol spec (header + record loop).
"""
import struct
import sys

def parse_fit(path):
    with open(path, 'rb') as f:
        data = f.read()

    # --- File header ---
    hdr_size = data[0]
    proto_ver = data[1]
    profile_ver = struct.unpack_from('<H', data, 2)[0]
    data_size = struct.unpack_from('<I', data, 4)[0]
    data_type = data[8:12]
    header_crc_present = hdr_size >= 14

    pos = hdr_size
    end_of_data = hdr_size + data_size

    local_defs = {}  # local_msg_type -> dict(mesg_num, endian, fields=[(def_num,size,base_type)], dev_fields=[...])
    messages = []  # list of dicts: start, end, kind, local_type, mesg_num, raw_fields(list of (def_num,size,base_type,raw_bytes)), header_byte

    BASE_TYPE_SIZE = {
        0x00: 1, 0x01: 1, 0x02: 1, 0x83: 2, 0x84: 2, 0x85: 4, 0x86: 4,
        0x07: 1, 0x88: 4, 0x89: 4, 0x0A: 1, 0x8B: 2, 0x8C: 4, 0x0D: 1,
        0x8E: 4, 0x8F: 8, 0x90: 8, 0x91: 8, 0x92: 8, 0x93: 8,
    }

    while pos < end_of_data:
        start = pos
        header_byte = data[pos]
        pos += 1
        is_def = bool(header_byte & 0x40)
        is_compressed_ts = bool(header_byte & 0x80)

        if is_compressed_ts:
            local_type = (header_byte >> 5) & 0x03
        else:
            local_type = header_byte & 0x0F

        if is_def:
            reserved = data[pos]; pos += 1
            arch = data[pos]; pos += 1
            endian = '<' if arch == 0 else '>'
            mesg_num = struct.unpack_from(endian + 'H', data, pos)[0]; pos += 2
            num_fields = data[pos]; pos += 1
            fields = []
            for _ in range(num_fields):
                def_num = data[pos]; size = data[pos+1]; base_type = data[pos+2]
                fields.append((def_num, size, base_type))
                pos += 3
            dev_fields = []
            if header_byte & 0x20:
                num_dev = data[pos]; pos += 1
                for _ in range(num_dev):
                    def_num = data[pos]; size = data[pos+1]; dev_idx = data[pos+2]
                    dev_fields.append((def_num, size, dev_idx))
                    pos += 3
            local_defs[local_type] = {
                'mesg_num': mesg_num, 'endian': endian,
                'fields': fields, 'dev_fields': dev_fields
            }
            messages.append({
                'start': start, 'end': pos, 'kind': 'def',
                'local_type': local_type, 'mesg_num': mesg_num,
                'fields': fields, 'dev_fields': dev_fields,
                'header_byte': header_byte,
            })
        else:
            defn = local_defs.get(local_type)
            if defn is None:
                # can't proceed without a definition; bail
                messages.append({'start': start, 'end': pos, 'kind': 'data-UNKNOWN-LOCALTYPE',
                                  'local_type': local_type, 'header_byte': header_byte})
                break
            raw_fields = []
            if is_compressed_ts:
                pass  # time offset is in header_byte low 5 bits, no extra bytes
            for (def_num, size, base_type) in defn['fields']:
                raw = data[pos:pos+size]
                pos += size
                raw_fields.append((def_num, size, base_type, raw))
            dev_raw = []
            for (def_num, size, dev_idx) in defn['dev_fields']:
                raw = data[pos:pos+size]
                pos += size
                dev_raw.append((def_num, size, dev_idx, raw))
            messages.append({
                'start': start, 'end': pos, 'kind': 'data',
                'local_type': local_type, 'mesg_num': defn['mesg_num'],
                'fields': raw_fields, 'dev_fields': dev_raw,
                'header_byte': header_byte,
            })

    return messages, hdr_size, end_of_data, len(data)


def find_overlapping(messages, off_start, off_end):
    hits = []
    for i, m in enumerate(messages):
        if m['start'] <= off_end and m['end'] > off_start:
            hits.append((i, m))
    return hits


def fmt_msg(m):
    s = f"[{m['kind']}] off={m['start']:#06x}-{m['end']:#06x} local_type={m.get('local_type')} mesg_num={m.get('mesg_num')}"
    if m['kind'] == 'data':
        parts = []
        cursor = m['start'] + 1  # header byte
        for (def_num, size, base_type, raw) in m['fields']:
            parts.append(f"f{def_num}(sz{size},bt{base_type:#04x})={raw.hex()}@{cursor:#06x}")
            cursor += size
        s += "\n    " + " | ".join(parts)
    elif m['kind'] == 'def':
        parts = [f"f{d}(sz{sz},bt{bt:#04x})" for (d, sz, bt) in m['fields']]
        s += "\n    fields: " + ", ".join(parts)
    return s


if __name__ == '__main__':
    path = sys.argv[1]
    messages, hdr_size, end_of_data, total_len = parse_fit(path)
    print(f"{path}: header_size={hdr_size} data_size={end_of_data-hdr_size} total={total_len} num_messages={len(messages)}")
    if len(sys.argv) > 2:
        off = int(sys.argv[2], 0)
        off_end = int(sys.argv[3], 0) if len(sys.argv) > 3 else off
        hits = find_overlapping(messages, off, off_end)
        print(f"\n--- messages overlapping {off:#06x}-{off_end:#06x} ---")
        for i, m in hits:
            print(f"msg#{i}: {fmt_msg(m)}")
