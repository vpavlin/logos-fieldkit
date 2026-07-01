# logos-fieldkit

A self-contained **Logos field node** on a Raspberry Pi — a LoRa ⇄ Logos mesh gateway, a Logos blockchain node, a live LCD status dashboard, and an **offline WiFi download point** that serves Logos Basecamp, modules, the blockchain node, docs, and a reading library.

Built for **DWeb Camp**: it runs with no upstream internet, over its own WiFi access point + LoRa mesh. Walk up, scan a QR to join, and pull everything you need.

---

## What's in the box

| Component | What it does |
|---|---|
| **Mesh gateway** | Bridges a LoRa mesh (Meshtastic *or* MeshCore) ⇄ Logos Messaging. Lives in [basecamp-meshtastic](https://github.com/vpavlin/basecamp-meshtastic); cataloged here. |
| **Blockchain node** | A Logos (Cryptarchia) node — see [logos-blockchain](https://github.com/logos-blockchain/logos-blockchain). |
| **LCD dashboard** | A 3.5" SPI touch panel with **MESH · NODE · SYS · GPS · WIFI** tabs (live mesh activity, node sync, CPU/mem/disk/temp, GPS + cached offline map, and the join-QR). |
| **Download hotspot** | A WiFi AP (`LogosFieldNode`) + HTTP server offering Basecamp (Linux/macOS), `.lgx` modules + an in-app package repo, the node binary + circuits, docs, and an offline library. |
| **Local AI** | A small LLM (Qwen3-1.7B via llama.cpp) running **entirely on the Pi** — a Logos-aware chat at the bottom of the landing page, genuinely offline. Knowledge is injected via the system prompt in `server/index.html`; setup in [`server/llm-setup.md`](server/llm-setup.md). |

## Architecture

```
  LoRa radio (USB) ──┐
                     ├─► mesh_gateway (Basecamp module) ──► Logos Messaging (Waku)
  Logos node (:8080)─┘                    │
                                          ▼
  feeders (python, systemd)  feed.py / node-feed.py / sys-feed.py
        │  write *.json + map.png + wifi-qr.png
        ▼
  LCD kiosk (cage + chromium, file://)  ── dashboard/index.html  (5 touch tabs)

  HTTP server (dweb-http.service, :80)  ── /srv/dweb-share  (server/index.html landing + artifacts)
  Local LLM (logos-llm.service, :8081)  ── Qwen3-1.7B via llama.cpp, on-Pi chat in the landing page
        ▲
  WiFi AP "LogosFieldNode"  ── concurrent AP+STA on wlan0_ap (keeps the uplink) ── hotspot/ap-up.sh
```

The dashboard reuses the *same* feeder JSON via symlinks, so the landing page shows the same live status.

## Hardware

- Raspberry Pi 5 (Debian 13 / trixie)
- 3.5" ILI9486 SPI touch panel (`panel-mipi-dbi`, 320×480) — see `docs/hardware.md` for its quirks
- u-blox 7 USB GPS
- A LoRa node on USB (e.g. Heltec V4 running Meshtastic or MeshCore companion firmware)

## Repo layout

```
dashboard/   LCD kiosk: index.html + feeders (feed.py / node-feed.py / sys-feed.py) + mesh-kiosk.sh
server/      HTTP landing page (index.html, incl. the on-Pi Local AI chat + its system prompt) + llm-setup.md
hotspot/     ap-up.sh / ap-revert.sh — concurrent AP+STA + the timed auto-revert safety pattern
systemd/     the .service units (3 feeders, dweb-http, mesh-kiosk, logos-llm)
modules/     the module catalog (index.json) + CONTRIBUTING.md
install/      install.sh — bring the kit up on a fresh Pi
docs/         hardware notes, panel quirks, recovery runbook
```

## Deploy

```bash
git clone https://github.com/vpavlin/logos-fieldkit
cd logos-fieldkit
sudo ./install/install.sh
```

Then drop the large artifacts (Basecamp AppImages, node tarballs, library, …) into `/srv/dweb-share/` and bring up the hotspot with `hotspot/ap-up.sh`. See `install/install.sh` + `docs/` for details.

## Module catalog

`modules/index.json` is a **Logos Basecamp package repository** — add its URL in Basecamp → *Settings → Package Repositories* to install the cataloged modules over the hotspot, offline.

**Want to add a module?** See [`modules/CONTRIBUTING.md`](modules/CONTRIBUTING.md) — open a PR with your module's entry. (Alisher: this is where your `qr` and friends live. 👋)

## Status

Running live on a Pi 5 at DWeb Camp. Pinned to the Logos **0.2.0** release line. License: TBD.
