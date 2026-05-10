from __future__ import annotations

import os
import stat
from dataclasses import dataclass, field
from pathlib import Path

from .errors import ConfigError


@dataclass
class Context:
    server: str
    token: str
    username: str = "root"


@dataclass
class Config:
    version: str = "1"
    default_context: str = "default"
    contexts: dict[str, Context] = field(default_factory=dict)


def preferred_config_path() -> Path:
    explicit = os.environ.get("MEMOSCLI_CONFIG")
    if explicit:
        return Path(explicit).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        return Path(xdg).expanduser() / "memos-cli" / "config.yaml"
    return Path.home() / ".config" / "memos-cli" / "config.yaml"


def candidate_config_paths() -> list[Path]:
    preferred = preferred_config_path()
    legacy = Path.home() / ".memos-cli.yaml"
    if preferred == legacy:
        return [preferred]
    return [preferred, legacy]


def resolve_config_path(path: str | None = None) -> Path:
    if path:
        return Path(path).expanduser()
    for candidate in candidate_config_paths():
        if candidate.exists():
            return candidate
    return preferred_config_path()


def _strip(value: str) -> str:
    value = value.strip()
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    return value


def parse_config(text: str) -> Config:
    cfg = Config()
    current_context: str | None = None
    in_contexts = False

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        if not raw_line.startswith(" "):
            current_context = None
            if line.startswith("version:"):
                cfg.version = _strip(line.split(":", 1)[1])
            elif line.startswith("default_context:"):
                cfg.default_context = _strip(line.split(":", 1)[1])
            elif line == "contexts:":
                in_contexts = True
            continue
        if in_contexts and raw_line.startswith("  ") and not raw_line.startswith("    "):
            name = line.strip().rstrip(":")
            if not name:
                raise ConfigError("invalid empty context name in config")
            current_context = name
            cfg.contexts[current_context] = Context(server="", token="", username="")
            continue
        if current_context and raw_line.startswith("    "):
            key, sep, value = line.strip().partition(":")
            if not sep:
                continue
            value = _strip(value)
            ctx = cfg.contexts[current_context]
            if key == "server":
                ctx.server = value.rstrip("/")
            elif key == "token":
                ctx.token = value
            elif key == "username":
                ctx.username = value

    return cfg


def dump_config(cfg: Config) -> str:
    lines = [
        'version: "1"',
        f"default_context: {cfg.default_context}",
        "contexts:",
    ]
    for name, ctx in cfg.contexts.items():
        lines.extend(
            [
                f"  {name}:",
                f'    server: "{ctx.server.rstrip("/")}"',
                f'    token: "{ctx.token}"',
                f'    username: "{ctx.username}"',
            ]
        )
    return "\n".join(lines) + "\n"


def load_config(path: str | None = None) -> tuple[Config, Path]:
    config_path = resolve_config_path(path)
    if not config_path.exists():
        raise ConfigError(f"config file not found: {config_path}")
    return parse_config(config_path.read_text(encoding="utf-8")), config_path


def save_config(cfg: Config, path: str | Path | None = None) -> Path:
    config_path = Path(path).expanduser() if path else resolve_config_path(None)
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(dump_config(cfg), encoding="utf-8")
    os.chmod(config_path, stat.S_IRUSR | stat.S_IWUSR)
    return config_path


def active_context(cfg: Config, name: str | None = None) -> Context:
    context_name = name or os.environ.get("MEMOS_CONTEXT") or cfg.default_context
    if context_name not in cfg.contexts:
        raise ConfigError(f"context not found: {context_name}")
    ctx = cfg.contexts[context_name]
    server = os.environ.get("MEMOS_SERVER", ctx.server).rstrip("/")
    token = os.environ.get("MEMOS_TOKEN", ctx.token)
    if not server:
        raise ConfigError("server is empty; run 'memos config init'")
    if not token:
        raise ConfigError("token is empty; run 'memos config init'")
    return Context(server=server, token=token, username=ctx.username or "root")


def redact_token(token: str) -> str:
    if not token:
        return ""
    if len(token) <= 10:
        return "***"
    return f"{token[:6]}...{token[-4:]}"


def safe_config_dict(cfg: Config) -> dict:
    return {
        "version": cfg.version,
        "default_context": cfg.default_context,
        "contexts": {
            name: {"server": ctx.server, "token": redact_token(ctx.token), "username": ctx.username}
            for name, ctx in cfg.contexts.items()
        },
    }

