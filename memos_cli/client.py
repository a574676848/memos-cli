from __future__ import annotations

import base64
import json
import mimetypes
import socket
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from .config import Context
from .errors import APIError, NetworkError


class MemosClient:
    def __init__(self, context: Context, timeout: float = 30.0, debug: bool = False):
        self.server = context.server.rstrip("/")
        self.token = context.token
        self.timeout = timeout
        self.debug = debug

    def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        body: Any | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        url = self._url(path, params)
        data = None
        request_headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {self.token}",
        }
        if headers:
            request_headers.update(headers)
        if body is not None:
            data = json.dumps(body, ensure_ascii=False).encode("utf-8")
            request_headers.setdefault("Content-Type", "application/json")

        req = urllib.request.Request(url, data=data, headers=request_headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return self._decode_response(resp.status, resp.read(), resp.headers.get("Content-Type", ""))
        except urllib.error.HTTPError as exc:
            payload = exc.read()
            message = self._error_message(exc.code, payload)
            raise APIError(exc.code, message, self._try_json(payload)) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise NetworkError(str(exc)) from exc

    def upload_attachment(self, file_path: str, *, filename: str | None = None, memo: str | None = None) -> Any:
        path = Path(file_path)
        raw = path.read_bytes()
        mime_type = mimetypes.guess_type(filename or path.name)[0] or "application/octet-stream"
        body = {
            "filename": filename or path.name,
            "content": base64.b64encode(raw).decode("ascii"),
            "type": mime_type,
        }
        if memo:
            body["memo"] = normalize_resource_name(memo, "memos")
        return self.request("POST", "/api/v1/attachments", body=body)

    def _url(self, path: str, params: dict[str, Any] | None = None) -> str:
        if path.startswith("http://") or path.startswith("https://"):
            base = path
        else:
            if not path.startswith("/"):
                path = "/" + path
            base = self.server + path
        if not params:
            return base
        cleaned: dict[str, str] = {}
        for key, value in params.items():
            if value is None or value == "":
                continue
            if isinstance(value, bool):
                cleaned[key] = "true" if value else "false"
            else:
                cleaned[key] = str(value)
        if not cleaned:
            return base
        separator = "&" if "?" in base else "?"
        return base + separator + urllib.parse.urlencode(cleaned)

    def _decode_response(self, status: int, raw: bytes, content_type: str) -> Any:
        if not raw:
            return {}
        if "application/json" in content_type or raw[:1] in (b"{", b"["):
            return json.loads(raw.decode("utf-8"))
        return raw.decode("utf-8", errors="replace")

    def _try_json(self, raw: bytes) -> Any:
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _error_message(self, status: int, raw: bytes) -> str:
        payload = self._try_json(raw)
        if isinstance(payload, dict):
            return str(payload.get("message") or payload.get("error") or payload.get("details") or f"HTTP {status}")
        text = raw.decode("utf-8", errors="replace").strip()
        return text or f"HTTP {status}"


def normalize_resource_name(value: str, prefix: str) -> str:
    value = value.strip()
    if value.startswith(prefix + "/"):
        return value
    return f"{prefix}/{value}"


def api_resource_path(value: str, default_prefix: str) -> str:
    value = value.strip().lstrip("/")
    if value.startswith("api/v1/"):
        return "/" + value
    if "/" in value:
        return "/api/v1/" + value
    return "/api/v1/" + normalize_resource_name(value, default_prefix)


def resource_id(value: str, prefix: str) -> str:
    return normalize_resource_name(value, prefix).split("/", 1)[1]


def parse_kv(values: list[str] | None) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in values or []:
        key, sep, value = item.partition("=")
        if not sep:
            raise ValueError(f"expected KEY=VALUE, got {item!r}")
        out[key] = value
    return out


def maybe_json(value: str | None) -> Any:
    if not value:
        return None
    return json.loads(value)


def new_request_id() -> str:
    return str(uuid.uuid4())
