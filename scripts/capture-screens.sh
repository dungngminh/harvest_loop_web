#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCREENS="$ROOT/public/screens"
DERIVED="/tmp/harvestloop-build"
PROJECT="/Users/dungngminh/Projects/komkat/harvest_loop/harvestloop/harvestloop.xcodeproj"
SIM_ID="${SIM_ID:-741943A6-8221-42C8-A62B-494FBD187F87}"
BUNDLE="me.komkatstudio.harvestloopgame"
APP="$DERIVED/Build/Products/Debug-iphonesimulator/harvestloop.app"

mkdir -p "$SCREENS"

if [[ ! -d "$APP" ]]; then
  xcodebuild -project "$PROJECT" -scheme harvestloop -configuration Debug \
    -destination "platform=iOS Simulator,id=$SIM_ID" \
    -derivedDataPath "$DERIVED" build >/dev/null
fi

xcrun simctl boot "$SIM_ID" 2>/dev/null || true
open -a Simulator --args -CurrentDeviceUDID "$SIM_ID" 2>/dev/null || true
sleep 2
xcrun simctl status_bar "$SIM_ID" override --orientation landscapeLeft 2>/dev/null || true
sleep 2
xcrun simctl install "$SIM_ID" "$APP"

capture() {
  local name="$1"
  local wait="$2"
  shift 2
  xcrun simctl terminate "$SIM_ID" "$BUNDLE" 2>/dev/null || true
  sleep 1
  xcrun simctl launch "$SIM_ID" "$BUNDLE" "$@" >/dev/null
  sleep "$wait"
  xcrun simctl io "$SIM_ID" screenshot "$SCREENS/$name"
  echo "captured $name"
}

capture "01-hero.png" 5 -captureProgram -captureSeed 42
capture "02-blocks.png" 5 -captureProgram -captureSeed 7 -level 2
capture "03-loops.png" 5 -captureProgram -captureSeed 99 -level 6
capture "04-fresh.png" 5 -autostart -captureSeed 2026
capture "05-harvest.png" 5 -captureProgram -captureSeed 55 -level 8
capture "06-stars.png" 10 -captureSuccess -captureSeed 1 -level 6

python3 "$ROOT/scripts/generate-assets.py"
python3 "$ROOT/scripts/generate-og.py"
