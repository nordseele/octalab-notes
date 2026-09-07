#!/usr/bin/env python3
"""Extract the MAIN OS from your own copy of an official Octatrack .syx.

    python3 tools/extract_os.py OCTATRACK_OS1.40C.syx out/mainos.bin

No Elektron file is redistributed with this repository: you supply the .syx,
this reads it.  The chain is SysEx 7-bit unpack -> ELEK container -> aPLib
depack, ported to pure Python from the decoder in ems-octakit
(patcher/src/lib.rs, MIT) so that reading the OS needs no toolchain at all.

The result is verified against the published digest of OS 1.40C; an unexpected
hash is reported, not silently accepted.
"""
import hashlib, pathlib, sys

MANUF = bytes([0x00, 0x20, 0x3C]); PRODUCT, SUBPRODUCT = 0x05, 0x00
DATA_CMD, FINAL_CMD, HDR = 0x7E, 0x7F, 26


def nib(h, l):
    assert h <= 0xF and l <= 0xF, "non-nibble metadata"
    return (h << 4) | l


def unpack_7bit(payload, high_order):
    out = bytearray()
    for i in range(0, len(payload), 8):
        group = payload[i:i + 8]
        if not group:
            break
        flags = group[0]
        for index, byte in enumerate(group[1:]):
            bit = 6 - index if high_order else index
            out.append(byte | (((flags >> bit) & 1) << 7))
    return bytes(out)


def packet_checksum(offset, decoded):
    s = ((offset >> 16) & 0xFF) + ((offset >> 8) & 0xFF) + (offset & 0xFF)
    return (s + sum(decoded)) & 0xFF


def decode_firmware(raw):
    out, next_off, declared = bytearray(), None, None
    pos = 0
    while pos < len(raw):
        if raw[pos] != 0xF0:
            pos += 1
            continue
        end = raw.index(0xF7, pos + 1)
        msg, pos = raw[pos:end + 1], end + 1
        if len(msg) < 8 or msg[1:4] != MANUF or msg[4] != PRODUCT or msg[5] != SUBPRODUCT:
            continue
        cmd, body = msg[6], msg[7:-1]
        if cmd == DATA_CMD:
            if not body:
                continue
            checksum = nib(body[0], body[1])
            offset = (nib(body[2], body[3]) << 16) | (nib(body[4], body[5]) << 8) | nib(body[6], body[7])
            dec = unpack_7bit(body[8:], True)
            if packet_checksum(offset, dec) != checksum:
                dec = unpack_7bit(body[8:], False)
                assert packet_checksum(offset, dec) == checksum, f"checksum @{offset:#08x}"
            if next_off is None:
                next_off = offset
            assert offset == next_off, f"non-contiguous packet @{offset:#08x}"
            next_off = offset + len(dec)
            out += dec
        elif cmd == FINAL_CMD:
            declared = (nib(body[0], body[1]) << 16) | (nib(body[2], body[3]) << 8) | nib(body[4], body[5])
    assert declared == len(out), f"declared {declared}, got {len(out)}"
    return bytes(out)


def parse_container(d):
    assert d[:4] == b"ELEK", "ELEK magic differs"
    product, version = d[4:8].decode(), d[13:18].decode()
    packed_len = int.from_bytes(d[18:22], "big")
    declared_sum = int.from_bytes(d[22:26], "big")
    packed = d[HDR:HDR + packed_len]
    assert sum(packed) & 0xFFFFFFFF == declared_sum, "packed checksum differs"
    assert not any(d[HDR + packed_len:]), "trailer not zero-filled"
    return product, version, packed


class Bits:
    def __init__(self, src):
        self.src, self.pos, self.tag = src, 0, 0

    def byte(self):
        b = self.src[self.pos]
        self.pos += 1
        return b

    def bit(self):
        self.tag = (self.tag << 1) & 0xFFFFFFFF
        if self.tag & 0xFF == 0:
            b = self.byte()
            self.tag = ((b << 1) | 1) & 0xFFFFFFFF
            return (b >> 7) & 1
        return (self.tag >> 8) & 1

    def gamma(self):
        v = 1
        while True:
            v = v * 2 + self.bit()
            if self.bit() == 1:
                return v


MAX_OFFSET_FOR_LEN2 = 0x0D00


def depack(src):
    r, out, last = Bits(src), bytearray(), 1
    while True:
        if r.bit() == 1:
            out.append(r.byte())
            continue
        g = r.gamma()
        if g == 2:
            offset = last
        else:
            raw = (g * 256 + r.byte() - 0x300) & 0xFFFFFFFF
            if raw == 0xFFFFFFFF:
                assert r.pos == len(src), "bytes after end marker"
                return bytes(out)
            offset = last = raw + 1
        assert 0 < offset <= len(out), f"bad match offset {offset:#x}"
        length = (r.bit() << 1) | r.bit()
        if length == 0:
            length = r.gamma() + 2
        if offset > MAX_OFFSET_FOR_LEN2:
            length += 1
        for _ in range(length + 1):
            out.append(out[len(out) - offset])


EXPECTED = {
    "164f31224bf61181e3f50e7dec40df9afcae5b16dbf6e4c0d0cc5e986af0a84e": "OS 1.40C MAIN OS (1,112,560 B)",
}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    raw = open(sys.argv[1], "rb").read()
    container = decode_firmware(raw)
    product, version, packed = parse_container(container)
    os_img = depack(packed)
    out = pathlib.Path(sys.argv[2])
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(os_img)
    digest = hashlib.sha256(os_img).hexdigest()
    print(f"product={product} version={version}")
    print(f"container {len(container)} B  packed {len(packed)} B  MAIN OS {len(os_img)} B")
    print(f"sha256 {digest}")
    print(f"        {EXPECTED.get(digest, 'UNKNOWN BUILD - every address in docs/ was read off OS 1.40C')}")
    print(f"wrote   {out}  (load base 0x40000400)")
