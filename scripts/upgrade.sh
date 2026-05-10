#!/usr/bin/env sh
set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
MEMOS_CLI_INSTALL_MANAGER="${MEMOS_CLI_INSTALL_MANAGER:-auto}" \
  "$SCRIPT_DIR/install.sh" "$@"
