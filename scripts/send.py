#!/usr/bin/env python3
"""Send an IR code through a Broadlink device - handy for testing codes before HA.

Usage:
  python scripts/send.py --host 192.168.1.50 --cmd power
      (looks the code up in homeassistant/packages/roberts_mp23.yaml)
  python scripts/send.py --host 192.168.1.50 --code b64:JgBDAJOT...
"""
import argparse
import base64
import pathlib
import sys

import broadlink
import yaml

DEFAULT_PACKAGE = pathlib.Path(__file__).resolve().parent.parent / "homeassistant/packages/roberts_mp23.yaml"


def load_codes(path: pathlib.Path) -> dict:
    pkg = yaml.safe_load(path.read_text())
    for script in pkg.get("script", {}).values():
        codes = script.get("variables", {}).get("codes")
        if codes:
            return codes
    sys.exit(f"No codes found in {path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--host", help="Broadlink IP address")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--cmd", help="command name from the package (e.g. power, volume_up)")
    g.add_argument("--code", help="raw code, with or without the b64: prefix")
    ap.add_argument("--package", type=pathlib.Path, default=DEFAULT_PACKAGE)
    ap.add_argument("--list", action="store_true", help="list command names and exit")
    args = ap.parse_args()

    if args.cmd or args.list:
        codes = load_codes(args.package)
        if args.list:
            print("\n".join(codes))
            return
        if args.cmd not in codes:
            sys.exit(f"Unknown command {args.cmd!r}. Use --list.")
        code = codes[args.cmd]
    elif args.code:
        code = args.code
    else:
        ap.error("give --cmd, --code or --list")
    if not args.host:
        ap.error("--host is required to send")
    code = code.removeprefix("b64:")

    dev = broadlink.hello(args.host)
    dev.auth()
    dev.send_data(base64.b64decode(code))
    print(f"sent {args.cmd or 'code'} via {args.host}")


if __name__ == "__main__":
    main()
