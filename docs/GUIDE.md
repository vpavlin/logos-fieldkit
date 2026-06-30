# Logos Field Node — Setup & Test Guide

Everything here is served from a Raspberry Pi over its own WiFi (`LogosFieldNode`) — **no internet required**. Connect, then work through the piece(s) you want. All downloads are local (`http://10.42.0.1/`).

> Conventions: `$` = a shell command on your laptop. Replace `<…>` placeholders.

---

## 0. Connect

1. Join WiFi **`LogosFieldNode`** (password `logosdweb`) — or scan the QR on the field node's screen.
2. Open **http://10.42.0.1/** — the landing page with all downloads.

---

## 1. Logos Basecamp (desktop app)

Private messaging + modular apps.

**Download** (from the landing page → *Basecamp*):
- **Linux x86_64** → `…-linux-x86_64.AppImage`
- **Linux arm64** → `…-linux-aarch64.AppImage`
- **macOS (Apple Silicon)** → `…-macos-arm64.dmg`

**Run (Linux):**
```bash
$ chmod +x LogosBasecamp-0.2.0-linux-x86_64.AppImage
$ ./LogosBasecamp-0.2.0-linux-x86_64.AppImage
```
**macOS:** open the `.dmg`, drag to Applications. If Gatekeeper blocks it (unsigned), right-click → Open, or `xattr -dr com.apple.quarantine /Applications/LogosBasecamp.app`.

**⚠ On upgrade**, clear the cache first: `rm -rf ~/.cache/Logos` (macOS: `~/Library/Caches/Logos`).

**Test:** Basecamp opens to the messaging UI. ✅

---

## 2. Mesh Gateway modules (LoRa ⇄ Logos Messaging)

Install the modules that bridge a LoRa mesh to Logos Messaging.

1. In Basecamp: **Settings → Package Repositories → Add**, paste the repo URL shown on the landing page (it auto-fills to this node, e.g. `http://10.42.0.1/basecamp/index.json`).
2. Install **`mesh_gateway`**, **`mesh_gateway_ui`**, and **`qr`**.
   *(Module install is fully supported on **Linux x86_64**. macOS gets the app only for now; raw arm64 `.lgx` are under `/basecamp/modules/`.)*
3. Open the **Mesh** tab.

**Connect a LoRa node:** plug in a node running Meshtastic or MeshCore companion firmware over USB. The badge shows the detected backend.

**Load a mesh config:** Mesh → Settings → *Load mesh config* → pick the **DWeb Camp** preset (or paste JSON). This tunes the radio + channels so you're on the same mesh as everyone else.

**Test:** send a message on a channel; it appears in the Mesh tab and relays to Logos Messaging. Messages from the mesh show up tagged by origin. ✅

---

## 3. Logos blockchain node

Run a Logos (Cryptarchia) node. **Use the standalone binary** — it's `testnet-0.2.0`, matching the bootstrap peers. (The Logos Core *module* path via `lgpd download blockchain_module` is a **devnet** build and won't chainsync on the testnet — see [issue #3054](https://github.com/logos-blockchain/logos-blockchain/issues/3054).)

**Download** (landing page → *Logos Node*) the tarball for your platform and extract:
```bash
$ tar xzf logos-blockchain-node-linux-x86_64-0.2.0.tar.gz
$ chmod +x logos-blockchain-node
```

**Generate a config** (fresh keys + the devnet bootstrap peers):
```bash
$ ./logos-blockchain-node init-config -o user_config.yaml \
    -p /ip4/65.109.51.37/udp/3000/quic-v1/p2p/12D3KooWFrouXfmrR4nsLMtE7wu15DoMJ6VtoUtHinREZCvbWHar \
       /ip4/65.109.51.37/udp/3001/quic-v1/p2p/12D3KooWJRGau8M1rjT7R5e4YYsgdFhsMX35nRDtMwCDjxQkXAHz \
       /ip4/65.109.51.37/udp/3002/quic-v1/p2p/12D3KooWQXJavMDTRscjauFSgVAB1VLB6Rzpy2uY5SU9Tk7927tb \
       /ip4/65.109.51.37/udp/50001/quic-v1/p2p/12D3KooWSQc7CcGtvWDPF1yCbBthFnQjprfCVHmfmNDUrSmqQsU1
```
(This also writes `keystore.yaml`. To carry over a 0.1.2 node use `migrate-from-0.1.2` instead.)

**Proving circuits** — the 0.2.0 release ships none, so reuse **v0.4.2** (download from *Logos Node*; the `.zkey` keys are arch-agnostic, same tarball for x86_64/arm64):
```bash
$ mkdir -p ~/.logos-blockchain-circuits
$ tar xzf logos-blockchain-circuits-v0.4.2-linux-aarch64.tar.gz -C ~/.logos-blockchain-circuits
```

**Run** (point at the circuits):
```bash
$ LOGOS_BLOCKCHAIN_CIRCUITS=~/.logos-blockchain-circuits ./logos-blockchain-node --log-backend stderr user_config.yaml
```

**Verify** (in another terminal):
```bash
$ curl -s http://localhost:8080/cryptarchia/info | jq
# expect {"cryptarchia_info":{"height":N,...},"mode":{"Started":"Bootstrapping"}}
```
The node is in **Bootstrapping** for ~1 h with `height`/`slot` steadily increasing, then flips to **Online**. (`Skipping IBD as no peers configured` is harmless — it catches up via tip-poll.) ✅

**Get funds:** grab a key id from `user_config.yaml` (`grep -A3 known_keys user_config.yaml`), request from the [devnet faucet](https://devnet.blockchain.logos.co/web/faucet/), then check `curl http://localhost:8080/wallet/<key>/balance`.

**Keep logs from filling the disk:** the binary defaults to a capped rolling file logger (`MaxFiles: 10`). On a small disk, prefer `--log-backend stderr` (journald) and set `tracing.logger.file: null` in the config.

---

## 4. Headless (logoscore) — no GUI

Run modules (gateway, node, …) on a server/Pi via the Logos Core CLI.

**Download** (landing page → *Headless (logoscore)*) `logoscore` + the package tools (`/tools/`: `lgpm`, `lgpd`), extract, put on `PATH`:
```bash
$ tar xzf logoscore-x86_64-linux.tar.gz && install -m755 logoscore-x86_64.AppImage ~/.local/bin/logoscore
$ tar xzf lgpm-x86_64-linux.tar.gz       && install -m755 lgpm-x86_64.AppImage      ~/.local/bin/lgpm
# (FUSE error? prefix commands with APPIMAGE_EXTRACT_AND_RUN=1)
```

**Install a module + run:**
```bash
$ lgpm --modules-dir ./modules install --file <module>.lgx
$ logoscore -m ./modules -D &           # start the daemon
$ logoscore load-module <module>        # load it
$ logoscore call <module> <method> ...  # invoke
```

**Test:** `logoscore load-module …` returns success and the daemon logs `Module loaded: <module>`. ✅

---

## 5. Library

Offline reading, served on this node:
- **Holotropic Breathwork** (Stanislav & Christina Grof) — [EPUB](/library/Holotropic-Breathwork-Grof.epub) · [PDF](/library/Holotropic-Breathwork-Grof.pdf)
- **Farewell to Westphalia** (Jarrad Hope & Peter Ludlow) — [PDF](/library/Farewell-to-Westphalia.pdf)

(Also on the landing page under *Library*.)

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Basecamp UI blank/odd after upgrade | clear `~/.cache/Logos` and relaunch |
| Module won't install on macOS/arm64 | module `.lgx` are Linux-x86_64 for now; use a Linux x86_64 machine |
| Node stuck at height 0 | confirm peers in `user_config.yaml`; check `curl :8080/cryptarchia/info`; give bootstrap ~1 min |
| Gateway not seeing the radio | use a **stable device path** (`/dev/heltec`), not `/dev/ttyACMx` (USB order isn't stable) |
| Disk filling from node logs | `--log-backend stderr` + `tracing.logger.file: null` (or rely on the capped rolling logger) |
| `logoscore` FUSE error | run with `APPIMAGE_EXTRACT_AND_RUN=1` |

Questions / contributions: see the [logos-fieldkit repo](https://github.com/vpavlin/logos-fieldkit).
