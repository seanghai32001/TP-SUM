"""Shared server-side reverse-proxy helpers for AutoSum's Vercel Python Functions."""
from __future__ import annotations

import json
import os
import re
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

ENV_NAME = "AUTOSUM_API_BASE_URL"
MAX_REQUEST_BODY = 2 * 1024 * 1024
TIMEOUT_SECONDS = 25

_ALLOWED_MEDIA_ROOTS = {
    "/image.png", "/images.png", "/welcome.mp3",
    "/icon-96.png", "/icon-128.png", "/icon-144.png", "/icon-152.png",
    "/icon-180.png", "/icon-192.png", "/icon-256.png", "/icon-384.png", "/icon-512.png",
    "/apple-touch-icon.png", "/apple-touch-icon-precomposed.png",
}
_GROUP_PHOTO_RE = re.compile(r"^/static/group_photos/[A-Za-z0-9_.-]+\.(?:jpg|jpeg|png|webp)$", re.IGNORECASE)
_REQUEST_HEADER_ALLOWLIST = {
    "accept", "content-type", "authorization", "range", "if-range",
    "if-none-match", "if-modified-since",
}
_RESPONSE_HEADER_ALLOWLIST = {
    "content-type", "content-length", "cache-control", "etag", "last-modified",
    "expires", "content-disposition", "accept-ranges", "content-range",
}


def backend_base_url() -> str:
    """Read the FastAPI URL only inside Python Function runtime."""
    raw = (os.getenv(ENV_NAME) or "").strip()
    if not raw:
        raise RuntimeError(f"Missing {ENV_NAME} environment variable in Vercel Project Settings.")
    parsed = urlsplit(raw)
    if parsed.scheme not in {"https", "http"} or not parsed.netloc:
        raise RuntimeError(f"{ENV_NAME} must be an absolute http(s) URL.")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise RuntimeError(f"{ENV_NAME} must not contain credentials, query parameters, or a fragment.")
    
    # ដំណោះស្រាយ: បាន Comment លក្ខខណ្ឌ HTTPS ចោល ដើម្បីអនុញ្ញាតឱ្យប្រើ HTTP ជាមួយ IP ធម្មតាបាន
    # if parsed.scheme != "https" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
    #     raise RuntimeError(f"{ENV_NAME} must use HTTPS in production.")
    
    return raw.rstrip("/")


def _json_error(handler, status: int, message: str) -> None:
    payload = json.dumps({"error": message}, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(payload)))
    handler.send_header("Cache-Control", "no-store")
    handler.end_headers()
    if getattr(handler, "command", "GET") != "HEAD":
        handler.wfile.write(payload)


def _read_body(handler) -> bytes:
    try:
        size = int(handler.headers.get("Content-Length", "0") or "0")
    except (TypeError, ValueError) as exc:
        raise ValueError("Invalid Content-Length header.") from exc
    if size < 0 or size > MAX_REQUEST_BODY:
        raise ValueError("Request body is too large.")
    return handler.rfile.read(size) if size else b""


def _forward_response(handler, upstream_request: Request) -> None:
    try:
        upstream = urlopen(upstream_request, timeout=TIMEOUT_SECONDS)
    except HTTPError as exc:
        upstream = exc
    with upstream:
        handler.send_response(upstream.status)
        for key, value in upstream.headers.items():
            if key.lower() in _RESPONSE_HEADER_ALLOWLIST:
                handler.send_header(key, value)
        handler.send_header("X-Content-Type-Options", "nosniff")
        handler.end_headers()
        if getattr(handler, "command", "GET") == "HEAD":
            return
        while True:
            chunk = upstream.read(64 * 1024)
            if not chunk:
                break
            handler.wfile.write(chunk)


def _request_headers(handler) -> dict[str, str]:
    return {
        key: value for key, value in handler.headers.items()
        if key.lower() in _REQUEST_HEADER_ALLOWLIST
    }


def proxy_fixed_path(handler, upstream_path: str, allowed_methods: Iterable[str]) -> None:
    allowed = set(allowed_methods)
    method = getattr(handler, "command", "GET").upper()
    if method not in allowed:
        handler.send_response(405)
        handler.send_header("Allow", ", ".join(sorted(allowed)))
        handler.send_header("Content-Length", "0")
        handler.end_headers()
        return
    try:
        body = _read_body(handler) if method in {"POST", "PUT", "PATCH"} else None
        query = urlsplit(handler.path).query
        target = backend_base_url() + upstream_path + (("?" + query) if query else "")
        req = Request(target, data=body, headers=_request_headers(handler), method=method)
        _forward_response(handler, req)
    except ValueError as exc:
        _json_error(handler, 400, str(exc))
    except RuntimeError as exc:
        _json_error(handler, 500, str(exc))
    except (URLError, TimeoutError, OSError) as exc:
        print(f"AutoSum proxy connection failed for {upstream_path}: {exc}")
        _json_error(handler, 502, "Cannot connect to the configured FastAPI backend.")


def proxy_media(handler) -> None:
    method = getattr(handler, "command", "GET").upper()
    if method not in {"GET", "HEAD"}:
        _json_error(handler, 405, "Media proxy only accepts GET or HEAD.")
        return
    params = parse_qs(urlsplit(handler.path).query, keep_blank_values=True)
    raw_target = params.get("path", [""])[0]
    parsed_target = urlsplit(raw_target)
    path = parsed_target.path
    allowed = path in _ALLOWED_MEDIA_ROOTS or bool(_GROUP_PHOTO_RE.fullmatch(path))
    if not allowed or ".." in path or "\\" in path or "\x00" in path:
        _json_error(handler, 400, "This media path is not allowed.")
        return
    try:
        target = backend_base_url() + path + (("?" + parsed_target.query) if parsed_target.query else "")
        req = Request(target, headers=_request_headers(handler), method=method)
        _forward_response(handler, req)
    except RuntimeError as exc:
        _json_error(handler, 500, str(exc))
    except (URLError, TimeoutError, OSError) as exc:
        print(f"AutoSum media proxy failed for {path}: {exc}")
        _json_error(handler, 502, "Cannot load media from the configured FastAPI backend.")
