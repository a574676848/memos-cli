from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from . import __version__
from .client import MemosClient, api_resource_path, maybe_json, normalize_resource_name, parse_kv
from .config import Config, Context, active_context, load_config, safe_config_dict, save_config
from .errors import APIError, ArgumentError, ConfigError, MemosCLIError
from .render import render


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
        if result is not None:
            output(args, result)
        return 0
    except MemosCLIError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        if isinstance(exc, APIError):
            print(f"HTTP status: {exc.status}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("Interrupted", file=sys.stderr)
        return 130


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="memos", description="CLI for Memos v0.28 REST API")
    parser.add_argument("--version", action="version", version=f"memos-cli {__version__}")
    parser.add_argument("-c", "--config", help="config file path")
    parser.add_argument("--context", help="config context name")
    parser.add_argument("-f", "--format", choices=["table", "json", "plain", "csv"], default=os.environ.get("MEMOS_FORMAT", "table"))
    parser.add_argument("-j", "--json", action="store_true", help="shortcut for --format json")
    parser.add_argument("-o", "--output-file", help="write output to file")
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("MEMOS_TIMEOUT", "30")))
    parser.add_argument("-v", "--verbose", action="store_true")

    sub = parser.add_subparsers(dest="command", required=True)
    add_config(sub)
    add_auth(sub)
    add_memo(sub)
    add_shortcuts(sub)
    add_attachment(sub, "attachment")
    add_attachment(sub, "resource")
    add_share(sub)
    add_user(sub)
    add_pat(sub)
    add_webhook(sub)
    add_shortcut_resource(sub)
    add_upgrade(sub)
    add_api(sub)
    return parser


def add_common_list_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--limit", "--page-size", dest="page_size", type=int)
    parser.add_argument("--page-token")
    parser.add_argument("--filter")


def add_config(sub: argparse._SubParsersAction) -> None:
    config = sub.add_parser("config", help="manage CLI config")
    s = config.add_subparsers(dest="action", required=True)

    init = s.add_parser("init", help="create or update a context")
    init.add_argument("--server", required=True)
    init.add_argument("--token", required=True)
    init.add_argument("--username", default="root")
    init.add_argument("--name", default="default")
    init.add_argument("--set-default", action="store_true", default=True)
    init.set_defaults(func=cmd_config_init)

    show = s.add_parser("show", help="show config with token redacted")
    show.set_defaults(func=cmd_config_show)

    contexts = s.add_parser("contexts", help="list contexts")
    contexts.set_defaults(func=cmd_config_contexts)

    set_context = s.add_parser("set-context", help="set default context")
    set_context.add_argument("name")
    set_context.set_defaults(func=cmd_config_set_context)


def add_auth(sub: argparse._SubParsersAction) -> None:
    auth = sub.add_parser("auth", help="authentication commands")
    s = auth.add_subparsers(dest="action", required=True)
    status = s.add_parser("status", help="validate token and show current user")
    status.set_defaults(func=lambda args: client_from_args(args).request("GET", "/api/v1/auth/me"))


def add_memo(sub: argparse._SubParsersAction) -> None:
    memo = sub.add_parser("memo", help="memo commands")
    s = memo.add_subparsers(dest="action", required=True)

    create = s.add_parser("create", help="create memo")
    create.add_argument("content", nargs="?")
    create.add_argument("--content", dest="content_flag")
    create.add_argument("--visibility", default="PRIVATE", choices=["PRIVATE", "PROTECTED", "PUBLIC"])
    create.add_argument("--pinned", action="store_true")
    create.add_argument("--memo-id")
    create.add_argument("--stdin", action="store_true")
    create.set_defaults(func=cmd_memo_create)

    list_cmd = s.add_parser("list", help="list memos")
    add_common_list_flags(list_cmd)
    list_cmd.add_argument("--state")
    list_cmd.add_argument("--order-by")
    list_cmd.add_argument("--show-deleted", action="store_true")
    list_cmd.set_defaults(func=cmd_memo_list)

    get = s.add_parser("get", help="get memo")
    get.add_argument("id")
    get.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.id, 'memos')}"))

    update = s.add_parser("update", help="update memo")
    update.add_argument("id")
    update.add_argument("--content")
    update.add_argument("--visibility", choices=["PRIVATE", "PROTECTED", "PUBLIC"])
    update.add_argument("--pinned", choices=["true", "false"])
    update.add_argument("--state", choices=["NORMAL", "ARCHIVED"])
    update.set_defaults(func=cmd_memo_update)

    delete = s.add_parser("delete", help="delete memo")
    delete.add_argument("id")
    delete.add_argument("--force", action="store_true")
    delete.set_defaults(func=cmd_memo_delete)

    search = s.add_parser("search", help="search memos with CEL contains filter")
    search.add_argument("query")
    search.add_argument("--limit", type=int)
    search.set_defaults(func=cmd_memo_search)

    comment = s.add_parser("comment", help="create memo comment")
    comment.add_argument("id")
    comment.add_argument("content", nargs="?")
    comment.add_argument("--stdin", action="store_true")
    comment.set_defaults(func=cmd_memo_comment)

    comments = s.add_parser("comments", help="list memo comments")
    comments.add_argument("id")
    add_common_list_flags(comments)
    comments.add_argument("--order-by")
    comments.set_defaults(func=cmd_memo_comments)

    attach = s.add_parser("attach", help="replace memo attachment list")
    attach.add_argument("id")
    attach.add_argument("attachments", nargs="+")
    attach.set_defaults(func=cmd_memo_attach)

    attachments = s.add_parser("attachments", help="list memo attachments")
    attachments.add_argument("id")
    add_common_list_flags(attachments)
    attachments.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.id, 'memos')}/attachments", params=list_params(args)))

    relations = s.add_parser("relations", help="list memo relations")
    relations.add_argument("id")
    add_common_list_flags(relations)
    relations.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.id, 'memos')}/relations", params=list_params(args)))

    link = s.add_parser("link", help="replace memo relations with one reference")
    link.add_argument("id")
    link.add_argument("related_id")
    link.add_argument("--type", default="REFERENCE", choices=["REFERENCE", "COMMENT"])
    link.set_defaults(func=cmd_memo_link)

    reactions = s.add_parser("reactions", help="list memo reactions")
    reactions.add_argument("id")
    add_common_list_flags(reactions)
    reactions.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.id, 'memos')}/reactions", params=list_params(args)))

    react = s.add_parser("react", help="upsert memo reaction")
    react.add_argument("id")
    react.add_argument("reaction_type")
    react.set_defaults(func=cmd_memo_react)

    unreact = s.add_parser("unreact", help="delete memo reaction")
    unreact.add_argument("reaction_name")
    unreact.set_defaults(func=lambda args: delete_with_confirm(args, api_resource_path(args.reaction_name, "memos"), force=True))


def add_shortcuts(sub: argparse._SubParsersAction) -> None:
    new = sub.add_parser("new", help="shortcut for memo create")
    new.add_argument("content", nargs="?")
    new.add_argument("--visibility", default="PRIVATE", choices=["PRIVATE", "PROTECTED", "PUBLIC"])
    new.add_argument("--pinned", action="store_true")
    new.add_argument("--stdin", action="store_true")
    new.set_defaults(func=cmd_memo_create)

    ls = sub.add_parser("ls", help="shortcut for memo list")
    add_common_list_flags(ls)
    ls.add_argument("--state")
    ls.add_argument("--order-by")
    ls.add_argument("--show-deleted", action="store_true")
    ls.set_defaults(func=cmd_memo_list)

    rm = sub.add_parser("rm", help="shortcut for memo delete")
    rm.add_argument("id")
    rm.add_argument("--force", action="store_true")
    rm.set_defaults(func=cmd_memo_delete)

    edit = sub.add_parser("edit", help="edit memo content with $EDITOR")
    edit.add_argument("id")
    edit.set_defaults(func=cmd_memo_edit)


def add_attachment(sub: argparse._SubParsersAction, name: str) -> None:
    res = sub.add_parser(name, help="attachment/resource commands")
    s = res.add_subparsers(dest="action", required=True)
    upload = s.add_parser("upload", help="upload attachment")
    upload.add_argument("file")
    upload.add_argument("--filename")
    upload.add_argument("--memo")
    upload.set_defaults(func=lambda args: client_from_args(args).upload_attachment(args.file, filename=args.filename, memo=args.memo))

    list_cmd = s.add_parser("list", help="list attachments")
    add_common_list_flags(list_cmd)
    list_cmd.add_argument("--order-by")
    list_cmd.set_defaults(func=lambda args: client_from_args(args).request("GET", "/api/v1/attachments", params=list_params(args, order=True)))

    get = s.add_parser("get", help="get attachment")
    get.add_argument("id")
    get.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.id, 'attachments')}"))

    update = s.add_parser("update", help="update attachment metadata")
    update.add_argument("id")
    update.add_argument("--filename")
    update.add_argument("--type")
    update.add_argument("--external-link")
    update.add_argument("--memo")
    update.set_defaults(func=cmd_attachment_update)

    delete = s.add_parser("delete", help="delete attachment")
    delete.add_argument("id")
    delete.add_argument("--force", action="store_true")
    delete.set_defaults(func=lambda args: delete_with_confirm(args, f"/api/v1/{normalize_resource_name(args.id, 'attachments')}", args.force))

    batch = s.add_parser("batch-delete", help="delete multiple attachments")
    batch.add_argument("ids", nargs="+")
    batch.add_argument("--force", action="store_true")
    batch.set_defaults(func=cmd_attachment_batch_delete)


def add_share(sub: argparse._SubParsersAction) -> None:
    share = sub.add_parser("share", help="share commands")
    s = share.add_subparsers(dest="action", required=True)
    create = s.add_parser("create", help="create memo share")
    create.add_argument("memo")
    create.add_argument("--expire-in-days", type=int)
    create.add_argument("--expire-at")
    create.set_defaults(func=cmd_share_create)

    list_cmd = s.add_parser("list", help="list memo shares")
    list_cmd.add_argument("memo")
    list_cmd.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.memo, 'memos')}/shares"))

    revoke = s.add_parser("revoke", help="delete share")
    revoke.add_argument("name")
    revoke.add_argument("--force", action="store_true")
    revoke.set_defaults(func=lambda args: delete_with_confirm(args, api_resource_path(args.name, "memos"), args.force))

    get = s.add_parser("get", help="get memo by share token")
    get.add_argument("share_id")
    get.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/shares/{args.share_id}"))


def add_user(sub: argparse._SubParsersAction) -> None:
    user = sub.add_parser("user", help="user commands")
    s = user.add_subparsers(dest="action", required=True)
    list_cmd = s.add_parser("list", help="list users")
    add_common_list_flags(list_cmd)
    list_cmd.add_argument("--show-deleted", action="store_true")
    list_cmd.set_defaults(func=lambda args: client_from_args(args).request("GET", "/api/v1/users", params=list_params(args, show_deleted=True)))

    get = s.add_parser("get", help="get user")
    get.add_argument("username")
    get.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.username, 'users')}"))

    create = s.add_parser("create", help="create user")
    create.add_argument("username")
    create.add_argument("--password", required=True)
    create.add_argument("--role", default="USER", choices=["USER", "ADMIN"])
    create.add_argument("--email")
    create.add_argument("--display-name")
    create.add_argument("--user-id")
    create.add_argument("--validate-only", action="store_true")
    create.set_defaults(func=cmd_user_create)

    update = s.add_parser("update", help="update user")
    update.add_argument("username")
    update.add_argument("--role", choices=["USER", "ADMIN"])
    update.add_argument("--email")
    update.add_argument("--display-name")
    update.add_argument("--avatar-url")
    update.add_argument("--description")
    update.add_argument("--state", choices=["NORMAL", "ARCHIVED"])
    update.set_defaults(func=cmd_user_update)

    delete = s.add_parser("delete", help="delete user")
    delete.add_argument("username")
    delete.add_argument("--force", action="store_true")
    delete.set_defaults(func=lambda args: delete_with_confirm(args, f"/api/v1/{normalize_resource_name(args.username, 'users')}", args.force, params={"force": args.force}))

    stats = s.add_parser("stats", help="get user stats")
    stats.add_argument("username", nargs="?", default="root")
    stats.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.username, 'users')}:getStats"))

    stats_all = s.add_parser("stats-all", help="list all user stats")
    stats_all.set_defaults(func=lambda args: client_from_args(args).request("GET", "/api/v1/users:stats"))


def add_pat(sub: argparse._SubParsersAction) -> None:
    pat = sub.add_parser("pat", help="personal access token commands")
    s = pat.add_subparsers(dest="action", required=True)
    list_cmd = s.add_parser("list")
    list_cmd.add_argument("--user", default="root")
    add_common_list_flags(list_cmd)
    list_cmd.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.user, 'users')}/personalAccessTokens", params=list_params(args)))

    create = s.add_parser("create")
    create.add_argument("--user", default="root")
    create.add_argument("--description", default="")
    create.add_argument("--expires-in-days", type=int, default=0)
    create.set_defaults(func=cmd_pat_create)

    delete = s.add_parser("delete")
    delete.add_argument("name")
    delete.add_argument("--force", action="store_true")
    delete.set_defaults(func=lambda args: delete_with_confirm(args, api_resource_path(args.name, "users"), args.force))


def add_webhook(sub: argparse._SubParsersAction) -> None:
    hook = sub.add_parser("webhook", help="user webhook commands")
    s = hook.add_subparsers(dest="action", required=True)
    list_cmd = s.add_parser("list")
    list_cmd.add_argument("--user", default="root")
    list_cmd.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.user, 'users')}/webhooks"))

    create = s.add_parser("create")
    create.add_argument("url")
    create.add_argument("--user", default="root")
    create.add_argument("--display-name", default="")
    create.set_defaults(func=cmd_webhook_create)

    update = s.add_parser("update")
    update.add_argument("name")
    update.add_argument("--url")
    update.add_argument("--display-name")
    update.set_defaults(func=cmd_webhook_update)

    delete = s.add_parser("delete")
    delete.add_argument("name")
    delete.add_argument("--force", action="store_true")
    delete.set_defaults(func=lambda args: delete_with_confirm(args, api_resource_path(args.name, "users"), args.force))


def add_shortcut_resource(sub: argparse._SubParsersAction) -> None:
    shortcut = sub.add_parser("shortcut", help="saved filter shortcut commands")
    s = shortcut.add_subparsers(dest="action", required=True)
    list_cmd = s.add_parser("list")
    list_cmd.add_argument("--user", default="root")
    list_cmd.set_defaults(func=lambda args: client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.user, 'users')}/shortcuts"))

    get = s.add_parser("get")
    get.add_argument("name")
    get.set_defaults(func=lambda args: client_from_args(args).request("GET", api_resource_path(args.name, "users")))

    create = s.add_parser("create")
    create.add_argument("title")
    create.add_argument("--filter", required=True)
    create.add_argument("--user", default="root")
    create.set_defaults(func=cmd_shortcut_create)

    update = s.add_parser("update")
    update.add_argument("name")
    update.add_argument("--title")
    update.add_argument("--filter")
    update.set_defaults(func=cmd_shortcut_update)

    delete = s.add_parser("delete")
    delete.add_argument("name")
    delete.add_argument("--force", action="store_true")
    delete.set_defaults(func=lambda args: delete_with_confirm(args, api_resource_path(args.name, "users"), args.force))


def add_api(sub: argparse._SubParsersAction) -> None:
    api = sub.add_parser("api", help="raw API escape hatch")
    api.add_argument("method", choices=["GET", "POST", "PATCH", "DELETE", "PUT", "get", "post", "patch", "delete", "put"])
    api.add_argument("path")
    api.add_argument("--data", help="JSON request body")
    api.add_argument("--data-file", help="read JSON body from file, '-' for stdin")
    api.add_argument("--param", action="append", help="query parameter KEY=VALUE")
    api.set_defaults(func=cmd_api)


def add_upgrade(sub: argparse._SubParsersAction) -> None:
    upgrade = sub.add_parser("upgrade", help="upgrade memos-cli")
    upgrade.add_argument(
        "--source",
        default=os.environ.get("MEMOS_CLI_PACKAGE_SPEC") or os.environ.get("MEMOS_CLI_UPGRADE_SOURCE") or "memos-cli",
        help="pip/pipx package spec, defaults to MEMOS_CLI_PACKAGE_SPEC or memos-cli",
    )
    upgrade.add_argument(
        "--package-name",
        default=os.environ.get("MEMOS_CLI_PACKAGE_NAME", "memos-cli"),
        help="installed package name used by pipx, defaults to memos-cli",
    )
    upgrade.add_argument("--manager", choices=["auto", "pipx", "pip"], default=os.environ.get("MEMOS_CLI_UPGRADE_MANAGER", "auto"))
    upgrade.add_argument("--python", default=sys.executable, help="Python executable used for pip upgrades")
    upgrade.add_argument("--user", action="store_true", help="pass --user when upgrading with pip")
    upgrade.add_argument("--dry-run", action="store_true", help="print the upgrade command without running it")
    upgrade.set_defaults(func=cmd_upgrade)


def cmd_config_init(args) -> dict:
    try:
        cfg, path = load_config(args.config)
    except ConfigError:
        cfg, path = Config(), Path(args.config).expanduser() if args.config else None
    cfg.contexts[args.name] = Context(server=args.server.rstrip("/"), token=args.token, username=args.username)
    if args.set_default or not cfg.default_context:
        cfg.default_context = args.name
    config_path = save_config(cfg, path)
    return {"config": str(config_path), "context": args.name, "server": args.server.rstrip("/"), "username": args.username}


def cmd_config_show(args) -> dict:
    cfg, path = load_config(args.config)
    data = safe_config_dict(cfg)
    data["path"] = str(path)
    return data


def cmd_config_contexts(args) -> list[dict[str, Any]]:
    cfg, _ = load_config(args.config)
    return [
        {"name": name, "default": name == cfg.default_context, "server": ctx.server, "username": ctx.username}
        for name, ctx in cfg.contexts.items()
    ]


def cmd_config_set_context(args) -> dict:
    cfg, path = load_config(args.config)
    if args.name not in cfg.contexts:
        raise ConfigError(f"context not found: {args.name}")
    cfg.default_context = args.name
    save_config(cfg, path)
    return {"default_context": args.name}


def cmd_memo_create(args) -> Any:
    content = getattr(args, "content_flag", None) or args.content
    if args.stdin or not content:
        if not sys.stdin.isatty():
            stdin_content = sys.stdin.read().strip()
            content = "\n".join(part for part in [content, stdin_content] if part)
    if not content:
        raise ArgumentError("memo content is required")
    body = {"content": content, "visibility": args.visibility}
    if args.pinned:
        body["pinned"] = True
    return client_from_args(args).request("POST", "/api/v1/memos", params={"memoId": getattr(args, "memo_id", None)}, body=body)


def cmd_memo_list(args) -> Any:
    return client_from_args(args).request("GET", "/api/v1/memos", params=list_params(args, order=True, state=True, show_deleted=True))


def cmd_memo_update(args) -> Any:
    memo = {"name": normalize_resource_name(args.id, "memos")}
    mask: list[str] = []
    for attr, field in [("content", "content"), ("visibility", "visibility"), ("state", "state")]:
        value = getattr(args, attr)
        if value is not None:
            memo[field] = value
            mask.append(field)
    if args.pinned is not None:
        memo["pinned"] = args.pinned == "true"
        mask.append("pinned")
    if not mask:
        raise ArgumentError("no fields to update")
    return client_from_args(args).request("PATCH", f"/api/v1/{memo['name']}", params={"updateMask": ",".join(mask)}, body=memo)


def cmd_memo_delete(args) -> Any:
    return delete_with_confirm(args, f"/api/v1/{normalize_resource_name(args.id, 'memos')}", args.force, params={"force": args.force})


def cmd_memo_search(args) -> Any:
    query = args.query.replace('"', '\\"')
    return client_from_args(args).request("GET", "/api/v1/memos", params={"filter": f'content.contains("{query}")', "pageSize": args.limit})


def cmd_memo_comment(args) -> Any:
    content = args.content
    if args.stdin or not content:
        if not sys.stdin.isatty():
            content = sys.stdin.read().strip()
    if not content:
        raise ArgumentError("comment content is required")
    return client_from_args(args).request("POST", f"/api/v1/{normalize_resource_name(args.id, 'memos')}/comments", body={"content": content, "visibility": "PRIVATE"})


def cmd_memo_comments(args) -> Any:
    params = list_params(args, order=True)
    return client_from_args(args).request("GET", f"/api/v1/{normalize_resource_name(args.id, 'memos')}/comments", params=params)


def cmd_memo_attach(args) -> Any:
    attachments = [{"name": normalize_resource_name(item, "attachments")} for item in args.attachments]
    return client_from_args(args).request("PATCH", f"/api/v1/{normalize_resource_name(args.id, 'memos')}/attachments", body={"attachments": attachments})


def cmd_memo_link(args) -> Any:
    memo = normalize_resource_name(args.id, "memos")
    related = normalize_resource_name(args.related_id, "memos")
    body = {"relations": [{"memo": {"name": memo}, "relatedMemo": {"name": related}, "type": args.type}]}
    return client_from_args(args).request("PATCH", f"/api/v1/{memo}/relations", body=body)


def cmd_memo_react(args) -> Any:
    memo = normalize_resource_name(args.id, "memos")
    body = {"reaction": {"contentId": memo, "reactionType": args.reaction_type}}
    return client_from_args(args).request("POST", f"/api/v1/{memo}/reactions", body=body)


def cmd_memo_edit(args) -> Any:
    client = client_from_args(args)
    memo_name = normalize_resource_name(args.id, "memos")
    current = client.request("GET", f"/api/v1/{memo_name}")
    content = current.get("content", "")
    editor = os.environ.get("EDITOR", "vi")
    with tempfile.NamedTemporaryFile("w+", suffix=".md", encoding="utf-8", delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        temp_name = tmp.name
    try:
        subprocess.run([editor, temp_name], check=True)
        new_content = Path(temp_name).read_text(encoding="utf-8")
    finally:
        Path(temp_name).unlink(missing_ok=True)
    if new_content == content:
        return {"changed": False, "name": memo_name}
    return client.request("PATCH", f"/api/v1/{memo_name}", params={"updateMask": "content"}, body={"name": memo_name, "content": new_content})


def cmd_attachment_update(args) -> Any:
    attachment = {"name": normalize_resource_name(args.id, "attachments")}
    mask: list[str] = []
    for attr, field in [("filename", "filename"), ("type", "type"), ("external_link", "externalLink")]:
        value = getattr(args, attr)
        if value:
            attachment[field] = value
            mask.append(field)
    if args.memo:
        attachment["memo"] = normalize_resource_name(args.memo, "memos")
        mask.append("memo")
    if not mask:
        raise ArgumentError("no fields to update")
    return client_from_args(args).request("PATCH", f"/api/v1/{attachment['name']}", params={"updateMask": ",".join(mask)}, body=attachment)


def cmd_attachment_batch_delete(args) -> Any:
    if not args.force and not confirm(f"Delete {len(args.ids)} attachments?"):
        return {"deleted": False}
    names = [normalize_resource_name(item, "attachments") for item in args.ids]
    return client_from_args(args).request("POST", "/api/v1/attachments:batchDelete", body={"names": names})


def cmd_share_create(args) -> Any:
    body: dict[str, Any] = {}
    if args.expire_at:
        body["expireTime"] = args.expire_at
    elif args.expire_in_days:
        body["expireTime"] = (datetime.now(timezone.utc) + timedelta(days=args.expire_in_days)).isoformat().replace("+00:00", "Z")
    return client_from_args(args).request("POST", f"/api/v1/{normalize_resource_name(args.memo, 'memos')}/shares", body=body)


def cmd_user_create(args) -> Any:
    user = {"username": args.username, "password": args.password, "role": args.role}
    if args.email:
        user["email"] = args.email
    if args.display_name:
        user["displayName"] = args.display_name
    return client_from_args(args).request(
        "POST",
        "/api/v1/users",
        params={"userId": args.user_id, "validateOnly": args.validate_only},
        body=user,
    )


def cmd_user_update(args) -> Any:
    user = {"name": normalize_resource_name(args.username, "users")}
    mask: list[str] = []
    for attr, field in [
        ("role", "role"),
        ("email", "email"),
        ("display_name", "displayName"),
        ("avatar_url", "avatarUrl"),
        ("description", "description"),
        ("state", "state"),
    ]:
        value = getattr(args, attr)
        if value is not None:
            user[field] = value
            mask.append(field)
    if not mask:
        raise ArgumentError("no fields to update")
    return client_from_args(args).request("PATCH", f"/api/v1/{user['name']}", params={"updateMask": ",".join(mask)}, body=user)


def cmd_pat_create(args) -> Any:
    parent = normalize_resource_name(args.user, "users")
    body = {"parent": parent, "description": args.description, "expiresInDays": args.expires_in_days}
    return client_from_args(args).request("POST", f"/api/v1/{parent}/personalAccessTokens", body=body)


def cmd_webhook_create(args) -> Any:
    parent = normalize_resource_name(args.user, "users")
    body = {"url": args.url}
    if args.display_name:
        body["displayName"] = args.display_name
    return client_from_args(args).request("POST", f"/api/v1/{parent}/webhooks", body=body)


def cmd_webhook_update(args) -> Any:
    webhook = {"name": args.name.strip().lstrip("/")}
    mask: list[str] = []
    if args.url:
        webhook["url"] = args.url
        mask.append("url")
    if args.display_name:
        webhook["displayName"] = args.display_name
        mask.append("displayName")
    if not mask:
        raise ArgumentError("no fields to update")
    return client_from_args(args).request("PATCH", api_resource_path(webhook["name"], "users"), params={"updateMask": ",".join(mask)}, body=webhook)


def cmd_shortcut_create(args) -> Any:
    parent = normalize_resource_name(args.user, "users")
    body = {"title": args.title, "filter": args.filter}
    return client_from_args(args).request("POST", f"/api/v1/{parent}/shortcuts", body=body)


def cmd_shortcut_update(args) -> Any:
    shortcut = {"name": args.name.strip().lstrip("/")}
    mask: list[str] = []
    if args.title:
        shortcut["title"] = args.title
        mask.append("title")
    if args.filter:
        shortcut["filter"] = args.filter
        mask.append("filter")
    if not mask:
        raise ArgumentError("no fields to update")
    return client_from_args(args).request("PATCH", api_resource_path(shortcut["name"], "users"), params={"updateMask": ",".join(mask)}, body=shortcut)


def cmd_api(args) -> Any:
    data = None
    if args.data_file:
        raw = sys.stdin.read() if args.data_file == "-" else Path(args.data_file).read_text(encoding="utf-8")
        data = json.loads(raw)
    elif args.data:
        data = maybe_json(args.data)
    return client_from_args(args).request(args.method.upper(), args.path, params=parse_kv(args.param), body=data)


def cmd_upgrade(args) -> dict[str, Any]:
    manager, command = upgrade_command(args)
    result: dict[str, Any] = {
        "current_version": __version__,
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


def upgrade_command(args) -> tuple[str, list[str]]:
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
    executable = Path(sys.executable).as_posix()
    return f"/pipx/venvs/{package_name}/" in executable or f"\\pipx\\venvs\\{package_name}\\" in str(Path(sys.executable))


def client_from_args(args) -> MemosClient:
    cfg, _ = load_config(args.config)
    return MemosClient(active_context(cfg, args.context), timeout=args.timeout, debug=args.verbose)


def list_params(args, *, order: bool = False, state: bool = False, show_deleted: bool = False) -> dict[str, Any]:
    params = {
        "pageSize": getattr(args, "page_size", None),
        "pageToken": getattr(args, "page_token", None),
        "filter": getattr(args, "filter", None),
    }
    if order:
        params["orderBy"] = getattr(args, "order_by", None)
    if state:
        params["state"] = getattr(args, "state", None)
    if show_deleted:
        params["showDeleted"] = getattr(args, "show_deleted", False)
    return params


def delete_with_confirm(args, path: str, force: bool, params: dict[str, Any] | None = None) -> Any:
    if not force and not confirm(f"Delete {path}?"):
        return {"deleted": False}
    return client_from_args(args).request("DELETE", path, params=params)


def confirm(prompt: str) -> bool:
    if not sys.stdin.isatty():
        return False
    answer = input(f"{prompt} [y/N] ").strip().lower()
    return answer in {"y", "yes"}


def output(args, result: Any) -> None:
    fmt = "json" if args.json else args.format
    text = render(result, fmt)
    if args.output_file:
        Path(args.output_file).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
