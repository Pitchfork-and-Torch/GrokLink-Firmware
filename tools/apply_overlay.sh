#!/usr/bin/env bash
# Copy GrokLink firmware overlay into a flipperzero-firmware tree.
set -euo pipefail
FIRMWARE_ROOT="${1:-}"
if [[ -z "$FIRMWARE_ROOT" ]]; then
  echo "Usage: $0 /path/to/flipperzero-firmware"
  exit 1
fi
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/firmware"

copy_tree() {
  local rel="$1"
  mkdir -p "$(dirname "$FIRMWARE_ROOT/$rel")"
  echo "Copy $rel"
  rm -rf "$FIRMWARE_ROOT/$rel"
  cp -a "$SRC/$rel" "$FIRMWARE_ROOT/$rel"
}

copy_tree "lib/groklink"
copy_tree "applications/services/grok_agent"
copy_tree "applications/system/grok_rpc"
copy_tree "applications/main/groklink_cli"
if [[ -d "$SRC/applications_user" ]]; then
  copy_tree "applications_user"
fi

cat > "$FIRMWARE_ROOT/GROKLINK_OVERLAY.md" <<'EOF'
# GrokLink overlay applied

See GrokLink-Firmware docs/BUILD_FLASH.md for link / fam / HAL wiring steps.
EOF

echo "Done."
