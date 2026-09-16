#!/bin/sh
set -eu

"${PYTHON:-python3}" - "${1:-http://localhost}" <<'PY'
import json
import sys
from urllib.error import HTTPError
from urllib.request import urlopen

base_url = sys.argv[1].rstrip("/")


def fetch(path):
    with urlopen(base_url + path, timeout=5) as response:
        return response.status, response.headers, response.read(), response.url


status, headers, body, _ = fetch("/api/v1/health")
assert status == 200
assert headers.get_content_type() == "application/json"
assert json.loads(body) == {"status": "ok", "torrserver": "not_configured"}

for path in ("/", "/tv", "/tv/"):
    status, headers, body, url = fetch(path)
    assert status == 200 and url.endswith("/tv/"), path
    assert headers.get_content_type() == "text/html"
    assert b"My Media" in body

for path, content_type in (
    ("/tv/css/style.css", "text/css"),
    ("/tv/js/app.js", "application/javascript"),
):
    status, headers, body, _ = fetch(path)
    assert status == 200 and body, path
    assert headers.get_content_type() == content_type, path

for path, expected in (("/tv/missing.css", 404), ("/play/not-implemented", 501)):
    try:
        fetch(path)
    except HTTPError as error:
        assert error.code == expected, path
    else:
        raise AssertionError("Unexpected success: " + path)

print("Smoke checks passed: API, TV page, redirects, assets, and reserved playback route.")
PY
