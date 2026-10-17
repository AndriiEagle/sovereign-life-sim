"""Serve the synthetic demo only; never expose audit, personal seed or .git."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse

ROOT = Path(__file__).resolve().parents[1]
ALLOWED = {
    '/engine-isometric-ui/index.html', '/engine-isometric-ui/styles.css',
    '/engine-isometric-ui/app.mjs', '/simulation-core/model.mjs',
    '/mcp-bridge/events.mjs',
}


def allowed_path(raw):
    path = unquote(urlsplit(raw).path)
    if path in {'/', '/engine-isometric-ui/'}:
        path = '/engine-isometric-ui/index.html'
    return path if path in ALLOWED else None


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        path = allowed_path(self.path)
        if path is None:
            self.send_error(404)
            return
        self.path = path
        super().do_GET()

    def do_HEAD(self):
        path = allowed_path(self.path)
        if path is None:
            self.send_error(404)
            return
        self.path = path
        super().do_HEAD()

    def end_headers(self):
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', "default-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        super().end_headers()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=4530)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'SYNTHETIC demo: http://127.0.0.1:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
