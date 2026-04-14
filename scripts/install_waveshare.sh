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
if [ ! -d "$EPAPER_LIB/waveshare_epd" ]; then
    echo "Error: waveshare_epd not found at $EPAPER_LIB/waveshare_epd" >&2
    echo "Set EPAPER_LIB to the directory containing the waveshare_epd package." >&2
    exit 1
fi

# Prefer uv, fall back to pip in the venv
if command -v uv &>/dev/null; then
    INSTALLER=(uv pip install)
elif [ -x "$PROJECT_DIR/.venv/bin/pip" ]; then
    INSTALLER=("$PROJECT_DIR/.venv/bin/pip" install)
else
    echo "Error: neither uv nor .venv/bin/pip found." >&2
    echo "Install uv (https://docs.astral.sh/uv/) or create a venv with pip." >&2
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
"${INSTALLER[@]}" -e "$EPAPER_LIB"

echo ""
echo "Done. Verify with:  .venv/bin/python -c 'import waveshare_epd; print(waveshare_epd)'"
