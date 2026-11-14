#!/usr/bin/env python3
"""Find Broadlink devices on the local network and check they accept auth.

Usage:  python scripts/discover.py [--local-ip 192.168.1.23] [--timeout 8]
"""
import argparse

import broadlink


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--local-ip", help="this computer's LAN IP (helps when you have several interfaces/VPNs)")
    ap.add_argument("--timeout", type=int, default=8)
    args = ap.parse_args()

    kwargs = {"timeout": args.timeout}
    if args.local_ip:
        kwargs["local_ip_address"] = args.local_ip
    devices = broadlink.discover(**kwargs)
    print(f"{len(devices)} device(s) found")
    for d in devices:
        try:
            authed = d.auth()
        except Exception as e:  # noqa: BLE001
            authed = f"auth failed: {e}"
        print(f"  {d.host[0]:15}  {d.mac.hex(':')}  {d.model or hex(d.devtype)}  "
              f"locked={d.is_locked}  auth={authed}")
    if not devices:
        print("Nothing found. Is the device's LED off (provisioned)? Is this computer on the same LAN?")


if __name__ == "__main__":
    main()
