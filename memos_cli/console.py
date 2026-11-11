from __future__ import annotations

import locale
import sys

# Piped input arrives as raw bytes. Modern producers emit UTF-8, while legacy
# shells and heredocs may still use the ANSI code page of the host.
_DECODE_ORDER = ("utf-8-sig", "utf-8")

# Pipes, files and agent runtimes read our bytes as UTF-8. Interactive consoles
# keep their own code page so glyphs stay readable in legacy Windows shells.
_OUTPUT_ENCODING = "utf-8"


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


def configure_stdio() -> None:
    """Pin machine-readable output to UTF-8 and keep consoles from crashing.

    Python wraps a redirected stdout/stderr with the ANSI code page of the host
    (cp936 on Chinese Windows), so piping JSON out of the CLI produced bytes no
    UTF-8 consumer could read. Interactive terminals are left untouched: the
    console already negotiates its own encoding and forcing UTF-8 there would
    print mojibake in legacy shells.
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is None:
            continue
        try:
            if _needs_utf8(stream):
                reconfigure(encoding=_OUTPUT_ENCODING, errors="replace")
            else:
                reconfigure(errors="replace")
        except (ValueError, OSError):
            continue


def _needs_utf8(stream: object) -> bool:
    encoding = (getattr(stream, "encoding", "") or "").lower()
    if encoding.startswith("utf-8"):
        return False
    return not _is_tty(stream)


def _is_tty(stream: object) -> bool:
    isatty = getattr(stream, "isatty", None)
    if isatty is None:
        return False
    try:
        return bool(isatty())
    except (ValueError, OSError):
        return False
