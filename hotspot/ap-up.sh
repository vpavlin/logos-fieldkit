#!/bin/bash
# Bring up a concurrent AP on a virtual interface (wlan0_ap), STA stays on wlan0.
exec >>/home/vpavlin/ap-up.log 2>&1
echo "=== ap-up $(date -u +%H:%M:%S) ==="
iw dev wlan0 interface add wlan0_ap type __ap 2>&1 || echo "vif add note (may already exist)"
sleep 1
nmcli con delete LogosFieldNode-ap 2>/dev/null
nmcli con add type wifi ifname wlan0_ap con-name LogosFieldNode-ap autoconnect no \
  ssid LogosFieldNode 802-11-wireless.mode ap 802-11-wireless.band a 802-11-wireless.channel 36 \
  ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk logosdweb 2>&1
nmcli con up LogosFieldNode-ap 2>&1
echo "ap-up exit=$?  active:"
nmcli -t -f NAME,DEVICE con show --active
