# Memos CLI — Gap Analysis and Production Scope

> Date: 2026-05-10
> Source baseline: `usememos/memos` `v0.28.0` release and local instance smoke checks

## 1. Findings Against Initial Docs

The first-pass docs correctly identified the main CLI shape, but several areas were either outdated or underspecified for a production CLI.

### 1.1 Resource API was renamed to Attachment API

Memos `v0.28.0` exposes attachments through:

- `GET /api/v1/attachments`
- `POST /api/v1/attachments`
- `GET /api/v1/{name=attachments/*}`
- `PATCH /api/v1/{attachment.name=attachments/*}`
- `DELETE /api/v1/{name=attachments/*}`
- `POST /api/v1/attachments:batchDelete`

The initial docs used `/api/v1/resources`. The CLI keeps `resource` as a user-facing alias for compatibility, but the implementation must call the official attachment endpoints.

### 1.2 Missing API surfaces

The original command matrix omitted these production-relevant surfaces:

- Auth: `GET /api/v1/auth/status`, `POST /api/v1/auth/signin`, `POST /api/v1/auth/signout`, `POST /api/v1/auth/refresh`
- Instance: profile and settings management
- Shortcut: saved filters under `users/{user}/shortcuts`
- PAT: list/create/delete personal access tokens
- User settings: list/get/update
- Linked identities and notifications
- Memo reactions: list/upsert/delete
- Attachment get/update/batch delete
- Low-level escape hatch for new official endpoints
- AI transcription and identity provider management endpoints

### 1.3 Completion strategy

Implementing every official endpoint as a polished high-level command is larger than a first production increment. To avoid blocking real usage, this project includes:

- High-level commands for daily workflows: auth, config, memo, resource/attachment, share, user, PAT, webhook, shortcut.
- A generic `memos api METHOD PATH` command for every official v0.28.0 endpoint, including instance, AI, identity provider, notification, linked identity, and future-compatible calls.

This makes the CLI complete from an operability standpoint while preserving a stable path for adding more first-class commands.

### 1.4 Toolchain adjustment

The initial docs proposed Go. The current build environment does not provide `go`, while Python 3.14 is available. The deliverable is therefore a zero-third-party-dependency Python CLI:

- Uses only the Python standard library.
- Installs as a normal console script through `pyproject.toml`.
- Works without generated protobuf bindings by using Memos' JSON REST gateway.
- Includes unit tests using `unittest` and local HTTP servers.

## 2. Production Scope

P0 production criteria:

- Token is never printed by default and config files are written with `0600`.
- `--json`, `--format table|plain|csv|json`, `--output-file`, `--timeout`, and env overrides are supported.
- All destructive high-level operations support `--force` or explicit confirmation.
- Standardized exit codes:
  - `0`: success
  - `1`: API/business error
  - `2`: network error
  - `3`: argument error
  - `4`: configuration error
- Automated unit tests cover config, HTTP client, rendering, memo operations, and command parsing.
- Live smoke commands are documented and can be run against the local instance.

## 3. Verified Local Instance Facts

- `GET /api/v1/users/root` with the provided PAT returns HTTP 200 and user `users/root`.
- `GET /api/v1/memos?pageSize=3` returns the expected v0.28 JSON shape.
- `POST /api/v1/memos` accepts a direct JSON body such as `{"content": "...", "visibility": "PRIVATE"}`.

## 4. Updated Command Coverage

High-level commands:

- `memos config init|show|set-context|contexts`
- `memos auth status`
- `memos memo create|list|get|update|delete|search|comment|comments|attach|attachments|relations|link|reactions|react|unreact`
- `memos share create|list|revoke|get`
- `memos attachment upload|list|get|update|delete|batch-delete`
- `memos resource ...` as an alias to `attachment`
- `memos user list|get|create|update|delete|stats|stats-all`
- `memos pat list|create|delete`
- `memos webhook list|create|update|delete`
- `memos shortcut list|get|create|update|delete`
- `memos new|ls|rm|edit`
- `memos api METHOD PATH`

The `api` command is the coverage guarantee for official endpoints that are intentionally not wrapped by a high-level command yet.
