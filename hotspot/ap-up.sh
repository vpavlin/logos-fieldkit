#!/bin/bash
# Bring up a concurrent AP on a virtual interface (wlan0_ap); the STA stays on wlan0.
#
# A single brcmfmac radio can only run AP+STA on the SAME channel, so the AP must follow
# whatever the uplink (home wifi at the bench / a phone hotspot in the field) is currently on.
# We read the STA's live channel/band and bring the AP up to match — no hardcoded 5 GHz/ch36.
#
#   ./ap-up.sh         bring the AP up on the STA's current channel
#   ./ap-up.sh --dry   just print the band/channel it WOULD use (no changes) — safe to run anytime
#
# Field flow: set the phone hotspot to 2.4 GHz, connect the Pi's STA to it, THEN run this.
IW=/usr/sbin/iw

# Derive the STA's channel + band (single-radio constraint => AP must match these).
FREQ=$("$IW" dev wlan0 link 2>/dev/null | awk '/freq:/{print int($2)}')
CH=$("$IW" dev wlan0 info 2>/dev/null | awk '/channel/{print $2; exit}')
if [ -n "$FREQ" ] && [ "$FREQ" -lt 3000 ]; then BAND=bg; else BAND=a; fi
if [ -z "$CH" ]; then BAND=bg; CH=6; NOTE=" (STA channel unknown — defaulting; connect the uplink first!)"; fi

if [ "$1" = "--dry" ]; then
  echo "STA freq=${FREQ:-?}MHz -> AP band=$BAND channel=$CH${NOTE}"
  exit 0
fi

exec >>/home/vpavlin/ap-up.log 2>&1
echo "=== ap-up $(date -u +%H:%M:%S) ==="
echo "STA freq=${FREQ:-?}MHz -> AP band=$BAND channel=$CH${NOTE}"

"$IW" dev wlan0 interface add wlan0_ap type __ap 2>&1 || echo "vif add note (may already exist)"
sleep 1
nmcli con delete LogosFieldNode-ap 2>/dev/null
nmcli con add type wifi ifname wlan0_ap con-name LogosFieldNode-ap autoconnect no \
  ssid LogosFieldNode 802-11-wireless.mode ap 802-11-wireless.band "$BAND" 802-11-wireless.channel "$CH" \
  ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk logosdweb 2>&1
nmcli con up LogosFieldNode-ap 2>&1
echo "ap-up exit=$?  active:"
nmcli -t -f NAME,DEVICE con show --active
