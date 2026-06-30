# Hardware notes & runbook

## Display — 3.5" ILI9486 SPI panel
- Overlay (in `/boot/firmware/config.txt`): `dtoverlay=mipi-dbi-spi,spi0-0,speed=16000000` + `dtparam=reset-gpio=25,dc-gpio=24`. 320×480 portrait, DRM card2.
- **Theme quirks (baked into `dashboard/index.html`):** only `#000` is true black (dark-grey fills wash/flicker); use `#ff5500` orange; **no `text-shadow`**; monospace; larger fonts.
- **Backlight is HARDWIRED — no software brightness or on/off.** Verified: no `/sys/class/backlight`, not in the overlay, and GPIO 18/12/13 don't drive it. Real control would need a MOSFET-on-GPIO hardware mod.
- **Kiosk:** `cage` + `chromium` rendering `file://…/index.html`, `WLR_RENDERER=pixman`, on card2. Chromium needs `--allow-file-access-from-files` (a `file://` page can't `fetch()` local JSON otherwise).
- **Screenshot:** `SOCK=$(sudo ls /run/kiosk | grep -E '^wayland-[0-9]+$' | head -1); sudo bash -c "XDG_RUNTIME_DIR=/run/kiosk WAYLAND_DISPLAY=$SOCK grim /tmp/x.png"`. A fresh kiosk restart shows pure black for a few seconds (chromium reloading) — re-grab after ~6 s.

## Stable device names (udev)
`/dev/ttyACMx` numbers are **not** stable across reboots/re-plugs — a GPS re-plug once swapped the Heltec and GPS, so the gateway opened the GPS (`Device or resource busy`) instead of the radio, and messages stopped flowing. `install/99-logos-fieldkit.rules` pins stable symlinks by USB vendor ID:
- `/dev/heltec` → LoRa radio (Espressif VID `303a`)
- `/dev/gps` → u-blox GPS (VID `1546`)

Everything references these: the gateway runs with `MESHCORE_DEV=/dev/heltec`; the dashboard feeder's `radio_up()` fusers `/dev/heltec`. Apply rule changes with `sudo udevadm control --reload-rules && sudo udevadm trigger --subsystem-match=tty`.

## GPS — u-blox 7 (USB)
- Available as `/dev/gps` (stable symlink — see above); `gpsd` watches its `by-id` path. `sys-feed.py` reads it via `gpspipe`.
- This gpsd reports **HDOP** in `SKY` but **not a satellite list**, so the dashboard shows HDOP (lower = better) instead of a sat count.

## Hotspot — concurrent AP+STA on one brcmfmac radio
- `wlan0` is the **only uplink** and carries SSH (over WireGuard `wg0`). The AP runs on a **virtual interface** `wlan0_ap` (`iw dev wlan0 interface add wlan0_ap type __ap`) so the STA is untouched.
- **The AP MUST use the STA's channel** (single radio). Find it: `nmcli dev wifi | grep '\*'`. Set `802-11-wireless.channel` in `ap-up.sh` to match.
- **Safety pattern (use for ANY wlan0 change):** schedule an auto-revert *before* the change, run the change detached, cancel only after confirming SSH survived:
  ```bash
  sudo systemd-run --on-active=240 --unit=ap-revert ~/ap-revert.sh   # restores in 4 min unless cancelled
  sudo systemd-run --unit=ap-bringup --collect /bin/bash ~/ap-up.sh  # detached
  # reconnect, verify Internety + LogosFieldNode-ap both active, then:
  sudo systemctl stop ap-revert.timer
  ```
  The AP profile is `autoconnect=no`, so a **power-cycle returns to STA-only** — the ultimate manual escape.

## Runbook

**Node wedges / crash-loops** (`Could not retrieve block parent … during recovery`): clear BOTH the block DB and the recovery state, then restart — the node re-syncs from genesis:
```bash
systemctl --user stop logos-node logos-node-watchdog
mv ~/state/recovery ~/state/recovery.corrupt-$(date +%Y%m%d); rm -rf ~/state/db
systemctl --user start logos-node logos-node-watchdog
```
(Logos node **0.2.0** has recovery/storage fixes that should prevent this.)

**Disk fills up:** the 0.1.x node's `tracing.logger.file` wrote *uncapped* hourly logs into `~` (filled the SD with ~99 GB). Fix: set `tracing.logger.file: null` in `user_config.yaml` (logs go to the journal, capped). 0.2.0 adds a max-files/compressed appender.

**Locked out (full disk took down WiFi/WireGuard):** since `wlan0` is the sole uplink, a crash there = no SSH. Recover by pulling the microSD and mounting it on a laptop — the ext4 rootfs auto-mounts (files are `uid 1000` = readable/writable without sudo); free space / fix config, then reboot.
