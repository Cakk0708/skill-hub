#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$root_dir"

if [[ -x "$root_dir/.venv/bin/python" ]]; then
  python_bin="$root_dir/.venv/bin/python"
else
  python_bin="${PYTHON:-python3}"
fi

exec "$python_bin" "$root_dir/main.py" "$@"
