#!/usr/bin/env sh
set -eu

PACKAGE_SPEC="${MEMOS_CLI_PACKAGE_SPEC:-git+https://github.com/a574676848/memos-cli.git}"
PACKAGE_NAME="${MEMOS_CLI_PACKAGE_NAME:-memos-cli}"
COMMAND_NAME="${MEMOS_CLI_COMMAND_NAME:-memos}"
INSTALL_MANAGER="${MEMOS_CLI_INSTALL_MANAGER:-auto}"
PYTHON_BIN="${PYTHON:-python3}"
VENV_DIR="${MEMOS_CLI_VENV_DIR:-$HOME/.local/share/memos-cli/venv}"
BIN_DIR="${MEMOS_CLI_BIN_DIR:-$HOME/.local/bin}"

info() {
  printf '%s\n' "$*"
}

has_cmd() {
  command -v "$1" >/dev/null 2>&1
}

is_pipx_package_installed() {
  pipx list --short 2>/dev/null | awk '{print $1}' | grep -qx "$PACKAGE_NAME"
}

install_with_pipx() {
  if has_cmd "$COMMAND_NAME"; then
    if is_pipx_package_installed && [ "$PACKAGE_SPEC" = "$PACKAGE_NAME" ]; then
      info "memos-cli already exists, upgrading with pipx..."
      pipx upgrade "$PACKAGE_NAME"
    else
      info "memos-cli already exists, reinstalling package spec with pipx..."
      pipx install --force "$PACKAGE_SPEC"
    fi
  else
    info "Installing memos-cli with pipx..."
    pipx install "$PACKAGE_SPEC"
  fi
}

install_with_pip_user() {
  info "Installing or upgrading memos-cli with pip --user..."
  "$PYTHON_BIN" -m pip install --user --upgrade "$PACKAGE_SPEC"
}

install_with_venv() {
  info "Installing or upgrading memos-cli in isolated venv..."
  "$PYTHON_BIN" -m venv "$VENV_DIR"
  "$VENV_DIR/bin/python" -m pip install --upgrade pip >/dev/null
  "$VENV_DIR/bin/python" -m pip install --upgrade "$PACKAGE_SPEC"
  mkdir -p "$BIN_DIR"
  ln -sfn "$VENV_DIR/bin/$COMMAND_NAME" "$BIN_DIR/$COMMAND_NAME"
}

if [ "$INSTALL_MANAGER" = "pipx" ]; then
  if ! has_cmd pipx; then
    info "pipx is required but was not found."
    exit 1
  fi
  install_with_pipx
elif [ "$INSTALL_MANAGER" = "pip" ]; then
  install_with_pip_user
elif [ "$INSTALL_MANAGER" = "venv" ]; then
  install_with_venv
else
  if has_cmd pipx && { ! has_cmd "$COMMAND_NAME" || is_pipx_package_installed; }; then
    install_with_pipx
  else
    install_with_venv
  fi
fi

if has_cmd "$COMMAND_NAME"; then
  "$COMMAND_NAME" --version
elif [ -x "$BIN_DIR/$COMMAND_NAME" ]; then
  "$BIN_DIR/$COMMAND_NAME" --version
else
  info "Installed package, but '$COMMAND_NAME' is not on PATH yet."
  info "Add '$BIN_DIR' to PATH, then run: $COMMAND_NAME --version"
fi
