from __future__ import annotations

import argparse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


_STATIC_PATH = "/architecture.svg"
_ANIMATED_PATH = "/architecture-animated.svg"


class _VisualizationHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    daemon_threads = True


def _as_bytes(value: str | bytes, label: str) -> bytes:
    data = value.encode("utf-8") if isinstance(value, str) else bytes(value)
    if not data:
        raise ValueError(f"{label} SVG content cannot be empty")
    return data


def _page(has_animated: bool) -> bytes:
    animated_link = (
        '<a href="/architecture-animated.svg">Open ANIMATED SVG</a>'
        if has_animated
        else '<span>ANIMATED SVG unavailable</span>'
    )
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Architecture visualization</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{{font-family:system-ui,sans-serif;margin:0;color:#1e293b;background:#f8fafc}}
header{{padding:1rem 1.5rem;background:#0f172a;color:white}}
nav{{display:flex;gap:1rem;padding:.75rem 1.5rem;background:white;border-bottom:1px solid #cbd5e1}}
nav a,nav span{{color:#1e40af}}
main{{padding:1rem 1.5rem}}
.object-frame{{width:100%;height:calc(100vh - 150px);min-height:520px;border:1px solid #cbd5e1;background:white}}
</style>
</head>
<body>
<header><h1>Architecture visualization</h1></header>
<nav aria-label="Visualization modes">
<a href="/architecture.svg">Open STATIC SVG</a>
{animated_link}
</nav>
<main>
<p>STATIC is the default presentation. ANIMATED is optional visual motion, not runtime execution.</p>
<object class="object-frame" id="architecture-view" data="/architecture.svg"
 type="image/svg+xml" title="Architecture visualization">
Architecture SVG is unavailable.
</object>
</main>
</body>
</html>
"""
    return document.encode("utf-8")


def create_visualization_server(
    static_svg: str | bytes,
    animated_svg: str | bytes | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 0,
) -> ThreadingHTTPServer:
    """Create a server for already-rendered SVG bytes.

    The HTTP layer exposes fixed routes only. It never receives a repository
    path, shell command or analysis request.
    """
    static_payload = _as_bytes(static_svg, "static")
    animated_payload = (
        _as_bytes(animated_svg, "animated") if animated_svg is not None else None
    )
    page_payload = _page(animated_payload is not None)

    routes: dict[str, tuple[bytes, str]] = {
        "/": (page_payload, "text/html; charset=utf-8"),
        _STATIC_PATH: (static_payload, "image/svg+xml; charset=utf-8"),
    }
    if animated_payload is not None:
        routes[_ANIMATED_PATH] = (
            animated_payload,
            "image/svg+xml; charset=utf-8",
        )

    class VisualizationRequestHandler(BaseHTTPRequestHandler):
        server_version = "ArchitectureVisualization/1.0"

        def _send(self, path: str, include_body: bool) -> None:
            response = routes.get(path)
            if response is None:
                body = b"Not Found\n"
                self.send_response(HTTPStatus.NOT_FOUND)
                self.send_header("Content-Type", "text/plain; charset=utf-8")
            else:
                body, content_type = response
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            if include_body:
                self.wfile.write(body)

        def do_GET(self) -> None:
            self._send(self.path, True)

        def do_HEAD(self) -> None:
            self._send(self.path, False)

        def log_message(self, format: str, *args) -> None:
            return

    return _VisualizationHTTPServer((host, port), VisualizationRequestHandler)


def serve_visualization(
    static_svg_path: str | Path,
    animated_svg_path: str | Path | None = None,
    *,
    host: str = "127.0.0.1",
    port: int = 8000,
) -> None:
    """Serve pre-generated SVG files until interrupted."""
    static_payload = Path(static_svg_path).read_bytes()
    animated_payload = (
        Path(animated_svg_path).read_bytes()
        if animated_svg_path is not None
        else None
    )
    server = create_visualization_server(
        static_payload,
        animated_payload,
        host=host,
        port=port,
    )
    address = server.server_address
    print(f"Architecture visualization: http://{address[0]}:{address[1]}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Serve pre-generated architecture SVG files"
    )
    parser.add_argument("--static-svg", required=True, type=Path)
    parser.add_argument("--animated-svg", type=Path)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", default=8000, type=int)
    args = parser.parse_args(argv)
    serve_visualization(
        args.static_svg,
        args.animated_svg,
        host=args.host,
        port=args.port,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
