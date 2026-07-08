#!/usr/bin/env python3
from __future__ import annotations

import argparse
import http.cookiejar
import json
import sys
import urllib.request
from pathlib import Path


def load_access(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = ("url", "user", "password")
    missing = [key for key in required if not payload.get(key)]
    if missing:
        raise SystemExit(f"Missing keys in access file: {', '.join(missing)}")
    return payload


def post(opener: urllib.request.OpenerDirector, url: str, data: dict) -> bytes:
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with opener.open(req, timeout=240) as response:
        return response.read()


def request_json(opener: urllib.request.OpenerDirector, url: str, data: dict) -> dict:
    raw = post(opener, url, data)
    return json.loads(raw.decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="Trigger an authenticated Evidentia Render backup.")
    parser.add_argument(
        "--access-file",
        default="/Users/piguin/.openclaw/workspace/.evidentia-render-access.json",
        help="JSON file with url, user and password.",
    )
    args = parser.parse_args()

    access = load_access(Path(args.access_file))
    base_url = str(access["url"]).rstrip("/")
    jar = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

    post(opener, f"{base_url}/api/login", {"username": access["user"], "password": access["password"]})
    result = request_json(opener, f"{base_url}/api/admin/backup", {})
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))

    if not result.get("ok"):
        return 2
    if int(result.get("records") or 0) < 1 or int(result.get("sqliteChunks") or 0) < 1:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
