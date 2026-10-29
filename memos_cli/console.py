from __future__ import annotations

import locale
import sys

# Piped input arrives as raw bytes. Modern producers emit UTF-8, while legacy
# shells and heredocs may still use the ANSI code page of the host.
_DECODE_ORDER = ("utf-8-sig", "utf-8")


def read_piped_text() -> str:
    """Read piped stdin, decoding UTF-8 first and falling back to the locale."""
    buffer = getattr(sys.stdin, "buffer", None)
    if buffer is None:
        return sys.stdin.read()
    raw = buffer.read()
    if not raw:
        return ""
    for encoding in _DECODE_ORDER:
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    try:
        return raw.decode(locale.getpreferredencoding(False))
    except (UnicodeDecodeError, LookupError):
        return raw.decode("utf-8", errors="replace")


def relax_stdio_errors() -> None:
    """Keep stdout/stderr from crashing on characters the console cannot encode."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            reconfigure(errors="replace")
        except (ValueError, OSError):
            continue
