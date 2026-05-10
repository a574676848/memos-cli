from __future__ import annotations

import csv
import io
import json
from typing import Any


LIST_KEYS = (
    "memos",
    "attachments",
    "users",
    "memoShares",
    "memo_shares",
    "reactions",
    "relations",
    "webhooks",
    "shortcuts",
    "settings",
    "personalAccessTokens",
    "personal_access_tokens",
    "stats",
    "notifications",
)


def render(data: Any, fmt: str = "table") -> str:
    if fmt == "json":
        return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if fmt == "plain":
        return render_plain(data)
    if fmt == "csv":
        return render_csv(data)
    return render_table(data)


def pick_rows(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return [x if isinstance(x, dict) else {"value": x} for x in data]
    if isinstance(data, dict):
        for key in LIST_KEYS:
            if key in data and isinstance(data[key], list):
                return [x if isinstance(x, dict) else {"value": x} for x in data[key]]
        return [data]
    return [{"value": data}]


def flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float, str)):
        return str(value).replace("\n", " ")
    if isinstance(value, list):
        if all(isinstance(item, str) for item in value):
            return ",".join(value)
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    return str(value)


def select_columns(rows: list[dict[str, Any]]) -> list[str]:
    preferred = [
        "name",
        "shareUrl",
        "content",
        "snippet",
        "visibility",
        "state",
        "pinned",
        "username",
        "role",
        "displayName",
        "filename",
        "type",
        "size",
        "url",
        "title",
        "filter",
        "createTime",
        "updateTime",
        "expireTime",
    ]
    keys: list[str] = []
    for key in preferred:
        if any(key in row for row in rows):
            keys.append(key)
    for row in rows:
        for key in row:
            if key not in keys and not isinstance(row[key], (dict, list)):
                keys.append(key)
    return keys[:8] or ["value"]


def render_table(data: Any) -> str:
    rows = pick_rows(data)
    if not rows:
        return "\n"
    columns = select_columns(rows)
    rendered = [[truncate(flatten(row.get(col)), 72) for col in columns] for row in rows]
    widths = [max(len(col), *(len(row[i]) for row in rendered)) for i, col in enumerate(columns)]
    header = "  ".join(col.ljust(widths[i]) for i, col in enumerate(columns))
    sep = "  ".join("-" * widths[i] for i in range(len(columns)))
    body = ["  ".join(row[i].ljust(widths[i]) for i in range(len(columns))) for row in rendered]
    return "\n".join([header, sep, *body]) + "\n"


def render_plain(data: Any) -> str:
    rows = pick_rows(data)
    parts: list[str] = []
    for row in rows:
        if len(row) == 1 and "content" in row:
            parts.append(flatten(row["content"]))
        else:
            parts.extend(f"{key}: {flatten(value)}" for key, value in row.items())
        parts.append("")
    return "\n".join(parts).rstrip() + "\n"


def render_csv(data: Any) -> str:
    rows = pick_rows(data)
    columns = select_columns(rows)
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=columns, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: flatten(row.get(key)) for key in columns})
    return buf.getvalue()


def truncate(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)] + "…"

