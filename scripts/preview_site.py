#!/usr/bin/env python3
"""Serve site/ the way Netlify will, so the site can be checked before deploying.

`python -m http.server` gets three things wrong, and they are exactly the three
that break a printed address:

  - it does not resolve /setup to setup.html, so every clean URL 404s
  - it ignores _redirects, so none of the 25 chapter routes work
  - it serves its own 404 page instead of 404.html, so the page that explains
    why /ch01 and /ch19 do not exist is never seen

This does all three. Standard library only, deliberately: checking the site
should not require the docking environment, or Node.

    python scripts/preview_site.py            # serves site/ on port 8000
    python scripts/preview_site.py site 8080  # or say where and which port

Redirects are served with the status in _redirects, so a 301 that should have
been a 302 shows up here rather than in a reader's cache.
"""
import sys
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "site").resolve()
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8000


def load_redirects(root):
    """Parse _redirects. Netlify's format is richer than this; the site uses
    only `/from  https://to  STATUS`, and anything else is worth noticing."""
    redirects = {}
    path = root / "_redirects"
    if not path.exists():
        print(f"warning: no _redirects in {root}", file=sys.stderr)
        return redirects
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 3:
            print(f"warning: {path}:{n}: expected 3 fields, skipping", file=sys.stderr)
            continue
        route, target, status = parts
        redirects[route] = (target, int(status))
    return redirects


REDIRECTS = load_redirects(ROOT)


class Netlifyish(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0].rstrip("/") or "/"

        if path in REDIRECTS:
            target, status = REDIRECTS[path]
            self.send_response(status)
            self.send_header("Location", target)
            self.end_headers()
            return

        # Clean URLs: /setup is served from setup.html.
        if path != "/" and not Path(path).suffix:
            if (ROOT / (path.lstrip("/") + ".html")).is_file():
                self.path = path + ".html"

        served = ROOT / "index.html" if self.path == "/" else ROOT / self.path.lstrip("/")
        if not served.is_file():
            self.send_error_page()
            return

        return super().do_GET()

    def send_error_page(self):
        custom = ROOT / "404.html"
        body = custom.read_bytes() if custom.is_file() else b"Not found"
        self.send_response(404)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    if not ROOT.is_dir():
        sys.exit(f"{ROOT} is not a directory")
    handler = partial(Netlifyish, directory=str(ROOT))
    print(f"Serving {ROOT} at http://localhost:{PORT}/")
    print(f"{len(REDIRECTS)} redirect routes loaded. Ctrl-C to stop.")
    try:
        HTTPServer(("127.0.0.1", PORT), handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped")


if __name__ == "__main__":
    main()
