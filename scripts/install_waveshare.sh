#!/usr/bin/env bash
# Install the waveshare_epd package from the local e-Paper repo
# into the bird-listener virtual environment.
#
# Usage:  ./scripts/install_waveshare.sh
#
# The e-Paper repo has no setup.py/pyproject.toml, so we create a
# temporary one and pip-install in editable mode (symlink).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
EPAPER_LIB="${EPAPER_LIB:-$(cd "$PROJECT_DIR/../e-Paper/RaspberryPi_JetsonNano/python/lib" && pwd)}"
VENV_PIP="$PROJECT_DIR/.venv/bin/pip"

if [ ! -d "$EPAPER_LIB/waveshare_epd" ]; then
    echo "Error: waveshare_epd not found at $EPAPER_LIB/waveshare_epd" >&2
    echo "Set EPAPER_LIB to the directory containing the waveshare_epd package." >&2
    exit 1
fi

if [ ! -x "$VENV_PIP" ]; then
    echo "Error: virtual environment pip not found at $VENV_PIP" >&2
    echo "Create the venv first:  python -m venv .venv" >&2
    exit 1
fi

# Create a minimal pyproject.toml if one doesn't already exist
if [ ! -f "$EPAPER_LIB/pyproject.toml" ]; then
    cat > "$EPAPER_LIB/pyproject.toml" <<'EOF'
[project]
name = "waveshare-epd"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = ["Pillow"]

[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"
EOF
    echo "Created temporary pyproject.toml in $EPAPER_LIB"
    CREATED_PYPROJECT=1
else
    CREATED_PYPROJECT=0
fi

echo "Installing waveshare_epd from $EPAPER_LIB ..."
"$VENV_PIP" install -e "$EPAPER_LIB"

echo ""
echo "Done. Verify with:  .venv/bin/python -c 'import waveshare_epd; print(waveshare_epd)'"
