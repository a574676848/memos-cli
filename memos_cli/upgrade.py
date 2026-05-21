from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tomllib
import urllib.error
import urllib.request
from typing import Any

from .errors import ArgumentError
from .version import PACKAGE_NAME, get_current_version


DEFAULT_PACKAGE_SPEC = "git+https://github.com/a574676848/memos-cli.git"
DEFAULT_VERSION_URL = "https://raw.githubusercontent.com/a574676848/memos-cli/main/pyproject.toml"
DEFAULT_TIMEOUT_SECONDS = 5
VERSION_PATTERN = re.compile(r"\d+|[A-Za-z]+")


def add_upgrade(sub: argparse._SubParsersAction) -> None:
    upgrade = sub.add_parser("upgrade", help="upgrade memos-cli")
    upgrade.add_argument(
        "--source",
        default=os.environ.get("MEMOS_CLI_PACKAGE_SPEC") or os.environ.get("MEMOS_CLI_UPGRADE_SOURCE") or DEFAULT_PACKAGE_SPEC,
        help=f"pip/pipx package spec, defaults to MEMOS_CLI_PACKAGE_SPEC or {DEFAULT_PACKAGE_SPEC}",
    )
    upgrade.add_argument(
        "--package-name",
        default=os.environ.get("MEMOS_CLI_PACKAGE_NAME", PACKAGE_NAME),
        help=f"installed package name used by pipx, defaults to {PACKAGE_NAME}",
    )
    upgrade.add_argument("--manager", choices=["auto", "pipx", "pip"], default=os.environ.get("MEMOS_CLI_UPGRADE_MANAGER", "auto"))
    upgrade.add_argument("--python", default=sys.executable, help="Python executable used for pip upgrades")
    upgrade.add_argument("--user", action="store_true", help="pass --user when upgrading with pip")
    upgrade.add_argument("--dry-run", action="store_true", help="print the upgrade command without running it")
    upgrade.add_argument("--check", action="store_true", help="check the latest GitHub source version without upgrading")
    upgrade.add_argument(
        "--version-url",
        default=os.environ.get("MEMOS_CLI_VERSION_URL", DEFAULT_VERSION_URL),
        help=f"pyproject.toml URL used by --check, defaults to {DEFAULT_VERSION_URL}",
    )
    upgrade.set_defaults(func=cmd_upgrade)


def cmd_upgrade(args: argparse.Namespace) -> dict[str, Any]:
    current_version = get_current_version()
    if args.check:
        return check_upgrade(args.version_url, current_version)

    manager, command = upgrade_command(args)
    result: dict[str, Any] = {
        "current_version": current_version,
        "manager": manager,
        "command": command,
        "dry_run": args.dry_run,
    }
    if args.dry_run:
        return result

    completed = subprocess.run(command, text=True, capture_output=True)
    result["returncode"] = completed.returncode
    if completed.stdout.strip():
        result["stdout"] = completed.stdout.strip()
    if completed.stderr.strip():
        result["stderr"] = completed.stderr.strip()
    if completed.returncode != 0:
        tail = completed.stderr.strip() or completed.stdout.strip() or "no output"
        raise ArgumentError(f"upgrade failed with exit code {completed.returncode}: {tail}")
    return result


def check_upgrade(version_url: str, current_version: str | None = None) -> dict[str, Any]:
    latest_version = fetch_latest_version(version_url)
    current = current_version or get_current_version()
    has_update = compare_versions(latest_version, current) > 0
    return {
        "current_version": current,
        "latest_version": latest_version,
        "has_update": has_update,
        "upgrade_command": "memos upgrade" if has_update else None,
        "version_url": version_url,
    }


def fetch_latest_version(version_url: str) -> str:
    try:
        with urllib.request.urlopen(version_url, timeout=DEFAULT_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8")
    except (OSError, urllib.error.URLError) as exc:
        raise ArgumentError(f"version check failed: {exc}") from exc

    try:
        latest_version = tomllib.loads(payload)["project"]["version"]
    except (KeyError, tomllib.TOMLDecodeError) as exc:
        raise ArgumentError("version check response does not contain project.version") from exc

    if not isinstance(latest_version, str) or not latest_version.strip():
        raise ArgumentError("version check response contains an invalid project.version")
    return latest_version.strip()


def compare_versions(left: str, right: str) -> int:
    left_parts = version_parts(left)
    right_parts = version_parts(right)
    return (left_parts > right_parts) - (left_parts < right_parts)


def version_parts(value: str) -> tuple[tuple[int, int | str], ...]:
    parts: list[tuple[int, int | str]] = []
    for item in VERSION_PATTERN.findall(value):
        if item.isdigit():
            parts.append((1, int(item)))
        else:
            parts.append((0, item.lower()))
    return tuple(parts)


def upgrade_command(args: argparse.Namespace) -> tuple[str, list[str]]:
    manager = args.manager
    pipx = shutil.which("pipx")
    if manager == "auto":
        manager = "pipx" if pipx and _running_from_pipx(args.package_name) else "pip"

    if manager == "pipx":
        if not pipx:
            raise ArgumentError("pipx is not available; use --manager pip or install pipx")
        if args.source == args.package_name:
            return "pipx", [pipx, "upgrade", args.package_name]
        return "pipx", [pipx, "install", "--force", args.source]

    command = [args.python, "-m", "pip", "install", "--upgrade"]
    if args.user:
        command.append("--user")
    command.append(args.source)
    return "pip", command


def _running_from_pipx(package_name: str) -> bool:
    executable = sys.executable
    return f"/pipx/venvs/{package_name}/" in executable.replace("\\", "/")
