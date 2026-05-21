from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


PACKAGE_NAME = "memos-cli"
UNKNOWN_VERSION = "0+unknown"


def get_current_version() -> str:
    try:
        return version(PACKAGE_NAME)
    except PackageNotFoundError:
        return UNKNOWN_VERSION
