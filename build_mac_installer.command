#!/bin/bash
set -e

cd "$(dirname "$0")"

APP_NAME="Forge Studio"
APP_PATH="dist/${APP_NAME}.app"
PKG_ROOT="build/mac-pkg-root"
PKG_OUTPUT="dist/Forge Studio Installer v1.5.pkg"

echo "Forge Studio macOS installer builder"
echo "This creates ${PKG_OUTPUT}"
echo

if [ ! -d "$APP_PATH" ]; then
  echo "${APP_PATH} was not found."
  echo "Run ./build_mac_app.command first."
  exit 1
fi

if ! command -v pkgbuild >/dev/null 2>&1; then
  echo "pkgbuild was not found. Install Apple Command Line Tools:"
  echo "xcode-select --install"
  exit 1
fi

rm -rf "$PKG_ROOT"
mkdir -p "$PKG_ROOT/Applications"
cp -R "$APP_PATH" "$PKG_ROOT/Applications/"

pkgbuild \
  --root "$PKG_ROOT" \
  --install-location "/" \
  --identifier "com.forgestudio.app" \
  --version "1.5" \
  "$PKG_OUTPUT"

echo
echo "Done. Your Mac installer is here:"
echo "$(pwd)/${PKG_OUTPUT}"
echo
echo "Note: this installer is unsigned. For public release, sign and notarize it with an Apple Developer account."
