#!/usr/bin/env bash
# Run actual Fontconfig operations inside a disposable account-local directory.
set -Eeuo pipefail
ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
[[ "$(uname -s)" == Linux && "$EUID" != 0 ]] || { printf 'Run tests as a non-root Linux user.\n'; exit 1; }
for cmd in python3 git fc-list fc-cache fc-scan desktop-file-validate flock; do command -v "$cmd" >/dev/null; done
for script in "$ROOT"/*.sh "$ROOT"/tools/*.sh "$ROOT"/tests/*.sh; do bash -n "$script"; done
while IFS= read -r -d '' entry; do desktop-file-validate "$entry"; done < <(find "$ROOT" -path "$ROOT/.git" -prune -o -name '*.desktop' -type f -print0)
export PYTHONDONTWRITEBYTECODE=1
python3 "$ROOT/tests/test_runtime.py"
python3 "$ROOT/tests/test_public.py"
python3 "$ROOT/tests/test_release.py"
