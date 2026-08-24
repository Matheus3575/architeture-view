from __future__ import annotations

import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import urlopen

from architecture_recovery.pipeline import analyze_repository
from architecture_recovery.rendering import render_svg
from architecture_recovery.visualization import VisualizationReadModelBuilder
from architecture_recovery.web import create_visualization_server


ROOT = Path(__file__).parents[1]
FIXTURE = ROOT / "benchmarks" / "fixtures" / "visualization_read_model"


def _rendered_svgs():
    model = VisualizationReadModelBuilder().build(analyze_repository(FIXTURE))
    return (
        model,
        render_svg(model, mode="static").encode("utf-8"),
        render_svg(model, mode="animated").encode("utf-8"),
    )


def test_web_consumer_serves_static_default_animated_and_accessible_page():
    model, static_svg, animated_svg = _rendered_svgs()
    before = model.model_dump_json()
    server = create_visualization_server(static_svg, animated_svg, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://{server.server_address[0]}:{server.server_address[1]}"

    try:
        with urlopen(base + "/") as response:
            page = response.read()
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("text/html")
        with urlopen(base + "/architecture.svg") as response:
            served_static = response.read()
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("image/svg+xml")
        with urlopen(base + "/architecture-animated.svg") as response:
            served_animated = response.read()
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("image/svg+xml")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    assert b'lang="en"' in page
    assert b'aria-label="Visualization modes"' in page
    assert b"/architecture.svg" in page
    assert b"/architecture-animated.svg" in page
    assert b'data="/architecture.svg"' in page
    assert served_static == static_svg
    assert served_animated == animated_svg
    assert model.model_dump_json() == before


def test_web_consumer_has_fixed_routes_and_no_animated_route_when_unprovided():
    server = create_visualization_server(b"<svg/>", port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://{server.server_address[0]}:{server.server_address[1]}"

    try:
        with urlopen(base + "/architecture.svg") as response:
            assert response.read() == b"<svg/>"
        try:
            urlopen(base + "/architecture-animated.svg")
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("animated route unexpectedly available")
        try:
            urlopen(base + "/../secret")
        except HTTPError as error:
            assert error.code == 404
        else:
            raise AssertionError("unknown route unexpectedly available")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_web_consumer_rejects_empty_svg_content():
    try:
        create_visualization_server(b"", port=0)
    except ValueError as exc:
        assert "cannot be empty" in str(exc)
    else:
        raise AssertionError("empty SVG content was accepted")
