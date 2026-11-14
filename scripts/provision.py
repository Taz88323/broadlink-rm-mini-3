#!/usr/bin/env python3
"""Put a Broadlink RM mini 3 on your Wi-Fi without the Broadlink app.

1. Put the device in AP mode (LED blinking slowly) - see README.
2. Join the open "BroadlinkProv" Wi-Fi network on this computer.
3. Run:  python scripts/provision.py --ssid "My 2.4GHz SSID"
   You are prompted for the Wi-Fi password; it is never stored or logged.

The setup packet is sent directly to the device's AP address (x.x.x.1 on the
BroadlinkProv network) as well as to the broadcast addresses. On macOS the
broadcast alone often never arrives - the unicast is what makes it work.
"""
import argparse
import getpass
import subprocess
import sys
import time

import broadlink

SECURITY = {"none": 0, "wep": 1, "wpa": 2, "wpa2": 3, "wpa/wpa2": 4}


def sh(cmd: str) -> str:
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5).stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"<{e}>"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ssid", required=True, help="2.4 GHz network the device should join")
    ap.add_argument("--security", choices=SECURITY, default="wpa2", help="default: wpa2 (WPA2-PSK/AES)")
    ap.add_argument("--iface", default="en0", help="Wi-Fi interface (macOS default en0)")
    args = ap.parse_args()

    ip = sh(f"ipconfig getifaddr {args.iface}") or sh("hostname -I 2>/dev/null | awk '{print $1}'")
    if not ip:
        sys.exit("No IP on the Wi-Fi interface - join BroadlinkProv first and wait for an address.")
    prefix = ".".join(ip.split(".")[:3])
    device_ip = f"{prefix}.1"
    print(f"This computer: {ip}  ->  device (AP) expected at {device_ip}")

    ping = sh(f"ping -c 2 -t 3 {device_ip} 2>/dev/null | tail -2 | head -1") or "no reply"
    print(f"Ping {device_ip}: {ping}")

    password = getpass.getpass(f"Wi-Fi password for {args.ssid}: ")
    targets = [device_ip, "255.255.255.255", f"{prefix}.255"]

    for _ in range(3):
        for t in targets:
            try:
                broadlink.setup(args.ssid, password, SECURITY[args.security], ip_address=t)
                print(f"  sent to {t}")
            except OSError as e:
                print(f"  FAILED to {t}: {e}  (macOS: allow your terminal under "
                      "Privacy & Security > Local Network)")
        time.sleep(1)

    print("\nWithin ~30 s the LED should stop blinking and BroadlinkProv should disappear.")
    print("Rejoin your normal Wi-Fi, then run: python scripts/discover.py")


if __name__ == "__main__":
    main()
