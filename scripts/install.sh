#!/usr/bin/env sh
set -eu

PACKAGE_SPEC="${MEMOS_CLI_PACKAGE_SPEC:-memos-cli}"
PACKAGE_NAME="${MEMOS_CLI_PACKAGE_NAME:-memos-cli}"
COMMAND_NAME="${MEMOS_CLI_COMMAND_NAME:-memos}"
INSTALL_MANAGER="${MEMOS_CLI_INSTALL_MANAGER:-auto}"
PYTHON_BIN="${PYTHON:-python3}"

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

if [ "$INSTALL_MANAGER" = "pipx" ]; then
  if ! has_cmd pipx; then
    info "pipx is required but was not found."
    exit 1
  fi
  install_with_pipx
elif [ "$INSTALL_MANAGER" = "pip" ]; then
  install_with_pip_user
else
  if has_cmd pipx && { ! has_cmd "$COMMAND_NAME" || is_pipx_package_installed; }; then
    install_with_pipx
  else
    install_with_pip_user
  fi
fi

if has_cmd "$COMMAND_NAME"; then
  "$COMMAND_NAME" --version
else
  info "Installed package, but '$COMMAND_NAME' is not on PATH yet."
  info "Add your Python user scripts directory to PATH, then run: $COMMAND_NAME --version"
fi
