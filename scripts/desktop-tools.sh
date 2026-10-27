#!/usr/bin/env bash
set -euo pipefail

# Source this file so the updated Node also runs the installer's subsequent npm/npx commands.
if [ "$(uname -s)" != Darwin ] || ! command -v brew >/dev/null 2>&1; then
  echo "Automatic Node.js/Obsidian setup requires macOS with Homebrew installed." >&2
  exit 1
fi

if pgrep -f '/Obsidian[.]app/Contents/MacOS/' >/dev/null; then
  echo "Close Obsidian before updating its desktop installer; the app will not be force-quit." >&2
  exit 1
fi

brew update
if brew list --formula node >/dev/null 2>&1; then
  brew upgrade --formula --yes node
else
  brew install --formula --yes node
fi

DESKTOP_NODE_PREFIX="$(brew --prefix node)"
export PATH="$DESKTOP_NODE_PREFIX/bin:$PATH"
hash -r
node -e '
  const [major, minor] = process.versions.node.split(".").map(Number);
  if (major < 22 || (major === 22 && minor < 20)) {
    console.error("Node.js 22.20 or newer is required after the Homebrew update.");
    process.exit(1);
  }
'

if brew list --cask obsidian >/dev/null 2>&1; then
  brew upgrade --cask --greedy --no-quit --yes obsidian
else
  # Replace an older manual .app install too; do not run cask zap or touch vault data.
  brew install --cask --force --yes obsidian
fi
echo "Node.js and Obsidian desktop tools are up to date."
