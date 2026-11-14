#!/usr/bin/env python3
"""Convert a Flipper Zero .ir file (parsed Samsung32 / NEC signals) to Broadlink b64 codes.

Usage:
  python scripts/flipper2broadlink.py ir/ROBERTS_MP23.ir            # name<TAB>b64:code
  python scripts/flipper2broadlink.py ir/ROBERTS_MP23.ir --yaml     # YAML mapping for an HA script

Codes can be sent with remote.send_command (command: "b64:...") or scripts/send.py.
Only the standard library is needed.
"""
import argparse
import base64
import re
import struct
import sys

# Broadlink pulse unit is 2^-15 s (~30.5 us): units = us * 269 / 8192
BROADLINK_IR = 0x26


def bits_lsb(*byte_values: int) -> list[int]:
    return [(b >> i) & 1 for b in byte_values for i in range(8)]


def frame(header: tuple[int, int], bits: list[int], mark=560, one=1690, zero=560) -> list[int]:
    pulses = list(header)
    for b in bits:
        pulses += [mark, one if b else zero]
    return pulses + [mark]


def samsung32(addr: int, cmd: int) -> list[int]:
    return frame((4500, 4500), bits_lsb(addr, addr, cmd, cmd ^ 0xFF))


def nec(addr: int, cmd: int) -> list[int]:
    return frame((9000, 4500), bits_lsb(addr, addr ^ 0xFF, cmd, cmd ^ 0xFF))


PROTOCOLS = {"Samsung32": samsung32, "NEC": nec}


def to_broadlink(pulses: list[int], repeat: int = 0) -> str:
    body = bytearray()
    for us in pulses:
        u = int(us * 269 / 8192)
        body += struct.pack(">B", u) if u < 256 else b"\x00" + struct.pack(">H", u)
    pkt = bytearray([BROADLINK_IR, repeat]) + struct.pack("<H", len(body)) + body + bytearray([0x0D, 0x05])
    pad = (len(pkt) + 4) % 16
    if pad:
        pkt += bytearray(16 - pad)
    return "b64:" + base64.b64encode(pkt).decode()


def parse_ir(text: str):
    for block in re.split(r"^#.*$", text, flags=re.M):
        fields = dict(re.findall(r"^(\w+):\s*(.+?)\s*$", block, flags=re.M))
        if fields.get("type") != "parsed" or "name" not in fields:
            continue
        proto = fields.get("protocol")
        if proto not in PROTOCOLS:
            print(f"skipping {fields['name']!r}: protocol {proto} not supported", file=sys.stderr)
            continue
        addr = int(fields["address"].split()[0], 16)
        cmd = int(fields["command"].split()[0], 16)
        yield fields["name"], to_broadlink(PROTOCOLS[proto](addr, cmd))


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ir_file")
    ap.add_argument("--yaml", action="store_true", help="emit 'slug: b64:...' YAML lines")
    args = ap.parse_args()

    with open(args.ir_file, encoding="utf-8") as f:
        for name, code in parse_ir(f.read()):
            print(f"{slug(name)}: {code}" if args.yaml else f"{name}\t{code}")


if __name__ == "__main__":
    main()
