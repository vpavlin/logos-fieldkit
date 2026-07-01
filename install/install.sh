#!/usr/bin/env bash
# Deploy logos-fieldkit on a fresh Raspberry Pi (Debian 13 / trixie).
# Idempotent-ish; review before running. Assumes you (the deploy user) have sudo.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
U="$(id -un)"

echo "==> Packages"
sudo apt-get update
sudo apt-get install -y python3 dnsmasq-base qrencode nftables gpsd gpsd-clients \
  cage chromium grim || echo "  (some pkgs may be named differently on your image — e.g. chromium-browser)"

echo "==> udev rules (stable /dev/heltec, /dev/gps — ttyACMx order isn't stable)"
sudo cp "$REPO/install/99-logos-fieldkit.rules" /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger --subsystem-match=tty

echo "==> Dashboard (LCD kiosk)"
mkdir -p "$HOME/mesh-dashboard"
cp "$REPO/dashboard/"*.py "$REPO/dashboard/index.html" "$HOME/mesh-dashboard/"
sudo install -m755 "$REPO/dashboard/mesh-kiosk.sh" /usr/local/bin/mesh-kiosk.sh

echo "==> HTTP serve dir (/srv/dweb-share)"
sudo mkdir -p /srv/dweb-share/{basecamp/modules,node,library,status,logoscore,tools}
sudo chown -R "$U":"$U" /srv/dweb-share
cp "$REPO/server/index.html" /srv/dweb-share/index.html
# The landing page reuses the dashboard's live feeds via symlinks:
for j in data node-data sys-data; do ln -sf "$HOME/mesh-dashboard/$j.json" "/srv/dweb-share/status/$j.json"; done
# The module repo (rewrite catalog URLs -> this node's hotspot IP):
python3 "$REPO/modules/gen-local-repo.py" "$REPO/modules/index.json" > /srv/dweb-share/basecamp/index.json

echo "==> Hotspot scripts"
cp "$REPO/hotspot/ap-up.sh" "$REPO/hotspot/ap-revert.sh" "$HOME/"
chmod +x "$HOME/ap-up.sh" "$HOME/ap-revert.sh"

echo "==> systemd units"
mkdir -p "$HOME/.config/systemd/user"
cp "$REPO/systemd/"*-dash-data.service "$HOME/.config/systemd/user/"
sudo cp "$REPO/systemd/dweb-http.service" "$REPO/systemd/mesh-kiosk.service" /etc/systemd/system/
systemctl --user daemon-reload; sudo systemctl daemon-reload
systemctl --user enable --now mesh-dash-data node-dash-data sys-dash-data
sudo systemctl enable --now dweb-http mesh-kiosk
sudo loginctl enable-linger "$U"   # keep user services up across logout/reboot

echo "==> WiFi join QR"
qrencode -o "$HOME/mesh-dashboard/wifi-qr.png" -s 8 -m 2 -l M 'WIFI:T:WPA;S:LogosFieldNode;P:logosdweb;;'

cat <<'EOF'

==> Done. Remaining manual steps:
  * Drop the large artifacts into /srv/dweb-share (Basecamp AppImages, node tarballs,
    logoscore/tools, modules/*.lgx, library/) — see docs/ for the fetch list.
  * Edit ~/ap-up.sh: set the AP channel to MATCH your wlan0 STA's channel
    (single brcmfmac radio = AP+STA must share a channel — `nmcli dev wifi | grep '\*'`).
  * Bring the hotspot up safely:  sudo ~/ap-up.sh   (see docs/hardware.md for the auto-revert pattern)
  * Verify:  http://<ip>/   and the LCD panel's tabs.
  * Optional Local AI chat (bottom of the landing page): see server/llm-setup.md
    — builds llama.cpp, pulls Qwen3-1.7B (~1 GB), installs the logos-llm user service on :8081.
EOF
