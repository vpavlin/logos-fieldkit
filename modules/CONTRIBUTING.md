# Contributing a module to the catalog

`index.json` is a [Logos Basecamp](https://github.com/logos-co/logos-basecamp) **package repository**. Field-node users add its URL in Basecamp → *Settings → Package Repositories* and install your module over the hotspot — **offline**.

## Add your module

1. **Publish a release** of your module with a `.lgx` asset (e.g. on your own GitHub repo). Build it with [logos-module-builder](https://github.com/logos-co/logos-module-builder) against the current Logos release line (**0.2.0**).
2. **Open a PR** adding an entry to `index.json` under `packages`:

```json
{
  "name": "your_module",
  "versions": [{
    "releasedAt": "2026-07-01T00:00:00Z",
    "publisherRef": "your_module-v1.0.0",
    "url": "https://github.com/you/your-repo/releases/download/v1.0.0/your_module.lgx",
    "size": 123456,
    "sha256": "<sha256 of the .lgx>",
    "rootHash": "<root hash from the manifest>",
    "manifest": { "...": "the module manifest (name, type, dependencies, main, hashes, ...)" }
  }]
}
```

Tip: if you already publish via your own repo's `index.json` (like `basecamp-meshtastic/repo/index.json`), just copy your package's object across.

3. CI / a maintainer regenerates the **served** `index.json` for the field node — its `.lgx` URLs are rewritten to the hotspot's address (`http://10.42.0.1/...`) so installs work fully offline. See `modules/gen-local-repo.py`.

## Arch notes

- Basecamp 0.2.0 ships **Linux x86_64 + arm64 AppImages** and a **macOS arm64** app.
- Module `.lgx` are per-arch. A single repo entry serves one arch unless you ship a **combined** `.lgx` (multiple variants in one package). For now, x86_64 is the fully-supported install path; arm64 `.lgx` are offered as direct downloads.

## Current catalog

- `mesh_gateway` + `mesh_gateway_ui` — LoRa ⇄ Logos Messaging bridge ([basecamp-meshtastic](https://github.com/vpavlin/basecamp-meshtastic))
- `qr` — QR generator service ([xAlisher/qr-basecamp](https://github.com/xAlisher/qr-basecamp))
