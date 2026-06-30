#!/usr/bin/env python3
"""Rewrite the catalog's .lgx URLs to the field node's hotspot address, so
Basecamp installs modules over the local WiFi — fully offline.

Usage:  gen-local-repo.py index.json [base_url] > served-index.json
        (default base_url = http://10.42.0.1/basecamp/modules/)
"""
import sys, json

base = sys.argv[2] if len(sys.argv) > 2 else "http://10.42.0.1/basecamp/modules/"
src = json.load(open(sys.argv[1]))
for p in src.get("packages", []):
    for v in p.get("versions", []):
        v["url"] = base + v["url"].rsplit("/", 1)[-1]
print(json.dumps(src, indent=2))
