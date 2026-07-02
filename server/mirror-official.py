#!/usr/bin/env python3
"""Mirror the 0.2.0-compatible subset of the official Logos module repo for offline install.

The official repo (logos-co/logos-modules-release) has moved most modules to
manifestVersion 0.3.0, which will NOT load in the field node's Basecamp 0.2.0. This mirrors
only the packages whose latest version is manifestVersion 0.2.0 — chiefly `delivery_module`
(the mesh_gateway dependency, so the gateway is fully installable offline), plus whatever else
in the official repo still targets 0.2.0 (storage v1, openmetrics, lez_indexer, blockchain*).
Each .lgx is downloaded locally and its URL rewritten to the hotspot, so Basecamp installs it
over the field node's WiFi. Served as a SECOND package repository alongside our own.

NOTE: blockchain_module here is the lgpd/devnet build (issue #3054) — installs but won't
chainsync on testnet. When the field kit moves to Basecamp 0.3.0, re-run with COMPAT=0.3.0
to mirror the full current set.

Usage: mirror-official.py [OUT_DIR] [BASE_URL] [COMPAT]
  OUT_DIR  default /srv/dweb-share/basecamp/official
  BASE_URL default http://10.42.0.1/basecamp/official   (the AP IP, matches our own repo)
  COMPAT   default 0.2.0                                 (our served Basecamp's manifestVersion)
"""
import json, os, sys, urllib.request

OFFICIAL_INDEX = "https://github.com/logos-co/logos-modules-release/releases/download/index/index.json"
OUT_DIR  = sys.argv[1] if len(sys.argv) > 1 else "/srv/dweb-share/basecamp/official"
BASE_URL = (sys.argv[2] if len(sys.argv) > 2 else "http://10.42.0.1/basecamp/official").rstrip("/")
COMPAT   = sys.argv[3] if len(sys.argv) > 3 else "0.2.0"

# The lgpd blockchain_module/ui are DEVNET builds (issue #3054) — they won't chainsync on the
# testnet our field node runs (we run the standalone testnet node), so skip them rather than ship
# a module that can't work here. (135 MB saved, too.)
EXCLUDE = {"blockchain_module", "blockchain_ui"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "logos-fieldkit-mirror"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Fetching official index (compat manifestVersion == {COMPAT}) ...")
    idx = json.loads(fetch(OFFICIAL_INDEX))
    kept = []
    for p in idx.get("packages", []):
        if p.get("name") in EXCLUDE:
            continue
        # newest version whose manifestVersion matches our Basecamp
        v = next((x for x in p.get("versions", [])
                  if str((x.get("manifest") or {}).get("manifestVersion")) == COMPAT), None)
        if not v or not v.get("url"):
            continue
        fn = v["url"].split("/")[-1]
        dest = os.path.join(OUT_DIR, fn)
        if os.path.exists(dest) and os.path.getsize(dest) == v.get("size", -1):
            print(f"  = {p['name']:22} {fn}  (cached)")
        else:
            print(f"  v {p['name']:22} {fn}  ({v.get('size', 0)/1048576:.1f} MB)")
            data = fetch(v["url"])
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                f.write(data)
            os.replace(tmp, dest)
        v["url"] = f"{BASE_URL}/{fn}"
        p["versions"] = [v]
        kept.append(p)

    idx["packages"] = kept
    idx["repositoryName"] = f"logos-modules-official (field-node {COMPAT} mirror)"
    with open(os.path.join(OUT_DIR, "index.json"), "w") as f:
        json.dump(idx, f, indent=2)

    descriptor = {
        "schemaVersion": idx.get("schemaVersion", 2),
        "name": "logos-modules-official-mirror",
        "displayName": f"Logos Official (field-node mirror, {COMPAT})",
        "description": "Offline mirror of the compatible official Logos modules, served over the field node's WiFi.",
        "indexUrl": f"{BASE_URL}/index.json",
        "trustedSigners": [],
    }
    with open(os.path.join(OUT_DIR, "logos-repo-official.json"), "w") as f:
        json.dump(descriptor, f, indent=2)

    print(f"\nMirrored {len(kept)} packages -> {OUT_DIR}")
    for p in kept:
        m = p["versions"][0].get("manifest", {})
        print(f"  - {p['name']} @ {m.get('version')}  (manifest {m.get('manifestVersion')})")


if __name__ == "__main__":
    main()
