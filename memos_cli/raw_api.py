from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

from .client import MemosClient, maybe_json, parse_kv


ClientFactory = Callable[[argparse.Namespace], MemosClient]


def add_api(sub: argparse._SubParsersAction, client_factory: ClientFactory) -> None:
    api = sub.add_parser("api", help="raw API escape hatch")
    api.add_argument("method", choices=["GET", "POST", "PATCH", "DELETE", "PUT", "get", "post", "patch", "delete", "put"])
    api.add_argument("path")
    api.add_argument("--data", help="JSON request body")
    api.add_argument("--data-file", help="read JSON body from file, '-' for stdin")
    api.add_argument("--param", action="append", help="query parameter KEY=VALUE")
    api.set_defaults(func=lambda args: cmd_api(args, client_factory))


def cmd_api(args: argparse.Namespace, client_factory: ClientFactory) -> Any:
    data = None
    if args.data_file:
        raw = sys.stdin.read() if args.data_file == "-" else Path(args.data_file).read_text(encoding="utf-8")
        data = json.loads(raw)
    elif args.data:
        data = maybe_json(args.data)
    return client_factory(args).request(args.method.upper(), args.path, params=parse_kv(args.param), body=data)
