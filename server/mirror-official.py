#!/usr/bin/env python3
"""Mirror the official Logos module repo for offline install as a 2nd on-node repository.

Mirrors each package's latest .lgx from logos-co/logos-modules-release, rewriting the URLs to the
field node's hotspot and emitting a logos-repo-official.json descriptor, so Basecamp installs them
over the field node's WiFi — alongside our own mesh-module repo.

Version note: a module's `manifestVersion` is the MANIFEST SCHEMA version (0.2.x / 0.3.x). Per the
spec + logos-package `isVersionSupported()`, tooling accepts any 0.x — so it is NOT a Basecamp
compatibility gate. Whether a given plugin actually loads is an ABI question, confirmed by installing
it in the target Basecamp, not decidable from the manifest. So we mirror EVERYTHING by default; the
optional COMPAT arg can filter by manifestVersion if you ever need to.

blockchain_module/ui are skipped: the lgpd build is DEVNET (issue #3054) and won't chainsync on the
testnet this field node runs.

Usage: mirror-official.py [OUT_DIR] [BASE_URL] [COMPAT]
  OUT_DIR  default /srv/dweb-share/basecamp/official
  BASE_URL default http://10.42.0.1/basecamp/official   (the AP IP, matches our own repo)
  COMPAT   optional manifestVersion filter (e.g. 0.2.0); default: mirror all latest
"""
import json, os, sys, urllib.request

OFFICIAL_INDEX = "https://github.com/logos-co/logos-modules-release/releases/download/index/index.json"
OUT_DIR  = sys.argv[1] if len(sys.argv) > 1 else "/srv/dweb-share/basecamp/official"
BASE_URL = (sys.argv[2] if len(sys.argv) > 2 else "http://10.42.0.1/basecamp/official").rstrip("/")
COMPAT   = sys.argv[3] if len(sys.argv) > 3 else None
EXCLUDE  = {"blockchain_module", "blockchain_ui"}  # devnet build (#3054) — can't chainsync our testnet


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "logos-fieldkit-mirror"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def pick(p):
    vs = p.get("versions", [])
    if COMPAT:
        return next((v for v in vs if str((v.get("manifest") or {}).get("manifestVersion")) == COMPAT), None)
    return vs[0] if vs else None   # latest (index lists newest-first)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f"Fetching official index (filter = {COMPAT or 'none — all latest'}) ...")
    idx = json.loads(fetch(OFFICIAL_INDEX))
    kept = []
    for p in idx.get("packages", []):
        if p.get("name") in EXCLUDE:
            continue
        v = pick(p)
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

    # prune stale .lgx from older runs / version bumps (keep only what the index references)
    keep = {p["versions"][0]["url"].split("/")[-1] for p in kept}
    for f in os.listdir(OUT_DIR):
        if f.endswith(".lgx") and f not in keep:
            print("  - pruning stale", f)
            os.remove(os.path.join(OUT_DIR, f))

    idx["packages"] = kept
    idx["repositoryName"] = "logos-modules-official (field-node mirror)"
    with open(os.path.join(OUT_DIR, "index.json"), "w") as f:
        json.dump(idx, f, indent=2)

    descriptor = {
        "schemaVersion": idx.get("schemaVersion", 2),
        "name": "logos-modules-official-mirror",
        "displayName": "Logos Official (field-node mirror)",
        "description": "Offline mirror of the official Logos modules, served over the field node's WiFi.",
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
