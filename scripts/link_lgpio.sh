#!/usr/bin/env bash
# Symlink system-installed lgpio into the project's virtual environment.
#
# lgpio is a C extension installed via apt (sudo apt install python3-lgpio)
# and can't be pip-installed into a venv, so we symlink it.
#
# Usage:  ./scripts/link_lgpio.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
VENV_PYTHON="$PROJECT_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
    echo "Error: venv python not found at $VENV_PYTHON" >&2
    exit 1
fi

SITE=$("$VENV_PYTHON" -c "import site; print(site.getsitepackages()[0])")
SYS_DIST="/usr/lib/python3/dist-packages"

# Check that lgpio is installed system-wide
if ! compgen -G "$SYS_DIST/lgpio*" >/dev/null; then
    echo "lgpio not found in $SYS_DIST" >&2
    echo "Install it first:  sudo apt install python3-lgpio" >&2
    exit 1
fi

LINKED=0
for f in "$SYS_DIST"/lgpio* "$SYS_DIST"/_lgpio*; do
    [ -e "$f" ] || continue
    name="$(basename "$f")"
    if [ -e "$SITE/$name" ]; then
        echo "Already exists: $SITE/$name"
    else
        ln -s "$f" "$SITE/$name"
        echo "Linked: $f -> $SITE/$name"
    fi
    LINKED=1
done

if [ "$LINKED" -eq 0 ]; then
    echo "Error: no lgpio files found to link" >&2
    exit 1
fi

echo ""
echo "Done. Verify with:  $VENV_PYTHON -c 'import lgpio; print(lgpio)'"
