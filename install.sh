#!/usr/bin/env bash
set -Eeuo pipefail
BASE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
if [[ $# -eq 0 ]]; then
  exec bash "$BASE/tools/oneclick.sh" install auto
fi
exec bash "$BASE/tools/font-actions.sh" install "$@"
