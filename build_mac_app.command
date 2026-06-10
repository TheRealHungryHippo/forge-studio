#!/bin/bash
set -e

cd "$(dirname "$0")"

echo "Forge Studio macOS builder"
echo "This creates dist/Forge Studio.app"
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python 3 is required. Install it from https://www.python.org/downloads/macos/"
  exit 1
fi

python3 -m venv .venv-mac
source .venv-mac/bin/activate

python -m pip install --upgrade pip
python -m pip install pyinstaller

python -m PyInstaller \
  --noconfirm \
  --windowed \
  --name "Forge Studio" \
  --icon "forge_studio_icon.ico" \
  --add-data "forge_studio_icon.ico:." \
  forge_studio.py

echo
echo "Done. Your Mac app is here:"
echo "$(pwd)/dist/Forge Studio.app"
echo
echo "If macOS blocks it because it is unsigned, right-click the app, choose Open, then Open again."
