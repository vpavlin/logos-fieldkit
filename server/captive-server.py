#!/usr/bin/env python3
"""Captive-portal HTTP server for the Logos field node.

Serves /srv/dweb-share exactly like `python -m http.server`, but any request
that isn't a real file (the OS captive-detection probes — /generate_204,
/hotspot-detect.html, /ncsi.txt, … — plus any unknown host/path the DNS
wildcard funnels here) gets a 302 to the landing page. That makes joining the
LogosFieldNode AP auto-pop the portal, while real downloads (Basecamp, .lgx,
docs, library) still serve normally. Stdlib only; runs as the dweb-http service.
"""
import http.server
import os

ROOT = "/srv/dweb-share"
PORTAL = "http://10.42.0.1/"


class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ROOT, **k)

    def _is_real(self):
        fs = self.translate_path(self.path.split("?", 1)[0])
        return os.path.isfile(fs) or (
            os.path.isdir(fs) and os.path.isfile(os.path.join(fs, "index.html"))
        )

    def _portal(self):
        self.send_response(302)
        self.send_header("Location", PORTAL)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        if self.path.split("?", 1)[0] == "/" or self._is_real():
            return super().do_GET()
        return self._portal()

    def do_HEAD(self):
        if self.path.split("?", 1)[0] == "/" or self._is_real():
            return super().do_HEAD()
        return self._portal()


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("", 80), Handler).serve_forever()
