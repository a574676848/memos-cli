# Production Readiness

## Implemented

- Zero-third-party-dependency Python CLI package.
- Official Memos `v0.28.0` REST paths for memos, attachments, shares, users, PATs, webhooks, shortcuts, and raw API access.
- Config file permissions set to `0600`.
- Token redaction in config display.
- JSON, table, CSV, plain, and file output.
- Unit tests for config, client, renderer, and command routing.
- Live smoke validation against `http://192.168.5.251:5230`.

## Operational Guidance

- Prefer `MEMOS_TOKEN` in CI instead of writing a token to disk.
- Use `-j` for automation and AI agents.
- Use `--force` only in non-interactive scripts after selecting exact resource names.
- Keep `memos api` available in production runs for newly added upstream endpoints.

## Known Tradeoffs

- The original Go plan was replaced with Python because this environment does not have `go`.
- YAML support is intentionally minimal and tailored to this CLI's generated config format to avoid third-party dependencies.
- Some low-frequency Memos APIs are covered through `memos api` instead of polished high-level commands.

