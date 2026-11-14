# Broadlink RM mini 3 without a smartphone

Set up a Broadlink RM mini 3 IR blaster without the Broadlink app or a cloud
account, add it to Home Assistant, and use it to control a **Roberts MP-23
(MP-Sound 23)** micro system. You don't need the Roberts' original remote.

- `scripts/provision.py` puts the RM mini 3 on your Wi-Fi from a laptop.
- `scripts/discover.py` finds it on your network.
- `scripts/send.py` sends an IR code from the command line, for testing.
- `scripts/flipper2broadlink.py` converts Flipper Zero `.ir` files (Samsung32 or NEC) into Broadlink `b64:` codes.
- `homeassistant/packages/roberts_mp23.yaml` is a Home Assistant package with all 32 Roberts MP-23 buttons. It adds a media player, keeps track of power, mute and source, and switches source through an automation.
- `homeassistant/dashboards/roberts_mp23_remote.yaml` is a dashboard card laid out like the remote, using only built-in cards.

## Requirements

- Python 3.9+ on macOS or Linux
- A **2.4 GHz** Wi-Fi network using **WPA2-PSK (AES)**. The RM mini 3 can't join 5 GHz or WPA3 networks, including WPA2/WPA3 mixed mode, and some units don't work on channels 12–13.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Install the requirements **before** you start. Once your computer joins the device's setup network, it has no internet connection.

## 1. Put the device in AP mode

1. Plug it in. Press and hold the reset pinhole for about 5 seconds until the LED **blinks fast**. This is the app's pairing mode, and it isn't the one you want.
2. Press and hold the reset pinhole again for about 5 seconds until the LED **blinks slowly**, roughly once every 2 seconds. This is AP mode.
3. An open Wi-Fi network called **`BroadlinkProv`** appears.

## 2. Send it your Wi-Fi details

Join `BroadlinkProv` on your computer, then run:

```bash
.venv/bin/python scripts/provision.py --ssid "Your-2.4GHz-SSID"
```

The script asks for the Wi-Fi password, so it never appears on the command line, in your shell history or in a file. It sends the setup packet several ways: directly to the device at `x.x.x.1` on the setup network, to `255.255.255.255`, and to the subnet broadcast address.

> **Why the direct send matters:** the setup network has no default gateway. On macOS, broadcasting the packet (what `broadlink.setup()` does by default) "succeeded" without errors, but the device never received it and kept blinking slowly. Sending it straight to the device's AP address fixed it.

When it works, the LED stops blinking and `BroadlinkProv` disappears within about 30 seconds.

If the script prints `FAILED … No route to host`, allow your terminal app under **System Settings → Privacy & Security → Local Network**.

## 3. Find it

Rejoin your normal Wi-Fi, then run:

```bash
.venv/bin/python scripts/discover.py
```

Reserve the IP address it shows in your router's DHCP settings.

## 4. Add it to Home Assistant

1. Go to **Settings → Devices & services → Add integration → Broadlink** and enter the IP address. If the firmware is locked, the integration offers to unlock it.
2. Make sure the device's **`remote.*` entity is on**. If it's off, Home Assistant silently drops every command.

## 5. Control the Roberts MP-23

The codes come from the [Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB) file `CD_Players/Roberts/ROBERTS_MP23.ir`. That file uses the Samsung32 protocol with address `0xA4`. A copy is in `ir/`. The codes have been converted to Broadlink format and are built into the package, so no learning step is needed.

Test a code first:

```bash
.venv/bin/python scripts/send.py --host <device-ip> --cmd power
.venv/bin/python scripts/send.py --list
```

Then set up Home Assistant:

1. Make sure `configuration.yaml` includes:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```
2. Copy `homeassistant/packages/roberts_mp23.yaml` to `/config/packages/`. If your Broadlink entity isn't `remote.rm_mini_3`, change it in `roberts_mp23_send`. It appears only once.
3. Restart Home Assistant. You'll now have `media_player.roberts_mp_23`, `script.roberts_mp23_send` (takes a `cmd` field) and the helpers.
4. Add the remote card: **Edit dashboard → Add card → Manual**, then paste `homeassistant/dashboards/roberts_mp23_remote.yaml`.

**Things to know:**

- IR only sends commands, so Home Assistant has to assume the power, mute and source state. If someone uses the front panel, flip `input_boolean.roberts_mp23_power` directly to bring it back in step. This doesn't send anything to the radio.
- On the card, hold **Radio** to send a raw Radio press. That switches between DAB and FM when the radio is already on.
- `media_player.toggle` needs its own `toggle:` command on a universal media player that has no child players underneath it. The package includes one.

## Other devices

Convert any Flipper `.ir` file that uses Samsung32 or NEC:

```bash
python3 scripts/flipper2broadlink.py path/to/device.ir --yaml
```

## Optional: keep it offline

The device doesn't need the internet. Block it from reaching the internet on your router, while still allowing traffic from Home Assistant. Full isolation needs a separate network for your IoT devices, such as a separate SSID or VLAN.

## Credits

- [python-broadlink](https://github.com/mjg59/python-broadlink) (MIT)
- IR codes: [Flipper-IRDB](https://github.com/Lucaslhm/Flipper-IRDB) (CC0-1.0)

## Licence

MIT – see [LICENSE](LICENSE). The IR codes in `ir/` and the codes derived from
them are from Flipper-IRDB and are CC0 (public domain).
