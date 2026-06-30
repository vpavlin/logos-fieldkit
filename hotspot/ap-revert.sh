#!/bin/bash
# Safety revert: tear down the AP, restore normal STA networking.
exec >>/home/vpavlin/ap-revert.log 2>&1
echo "=== ap-revert $(date -u +%H:%M:%S) ==="
nmcli con down LogosFieldNode-ap 2>/dev/null
nmcli con delete LogosFieldNode-ap 2>/dev/null
iw dev wlan0_ap del 2>/dev/null
nmcli con up Internety 2>/dev/null
systemctl restart wg-quick@wg0 2>/dev/null
echo "revert done; active:"
nmcli -t -f NAME,DEVICE con show --active
