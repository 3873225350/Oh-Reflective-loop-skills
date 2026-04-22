#!/usr/bin/env bash
# Source this file: source scripts/gh-env-sai.sh
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_GH_CONFIG_DIR="$REPO_ROOT/.gh-config-sai"

if [ -z "${_GH_CONFIG_DIR_OLD+x}" ]; then
  export _GH_CONFIG_DIR_OLD="${GH_CONFIG_DIR-__UNSET__}"
fi

export GH_CONFIG_DIR="$TARGET_GH_CONFIG_DIR"
echo "GH_CONFIG_DIR -> $GH_CONFIG_DIR"
gh auth status || true
