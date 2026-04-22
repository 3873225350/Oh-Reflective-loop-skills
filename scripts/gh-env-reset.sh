#!/usr/bin/env bash
# Source this file: source scripts/gh-env-reset.sh
if [ "${_GH_CONFIG_DIR_OLD-__MISSING__}" = "__MISSING__" ]; then
  echo "No saved GH_CONFIG_DIR state found in this shell."
  exit 0
fi

if [ "$_GH_CONFIG_DIR_OLD" = "__UNSET__" ]; then
  unset GH_CONFIG_DIR
else
  export GH_CONFIG_DIR="$_GH_CONFIG_DIR_OLD"
fi

unset _GH_CONFIG_DIR_OLD
echo "GH_CONFIG_DIR restored."
gh auth status || true
