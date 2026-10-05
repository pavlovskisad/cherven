#!/bin/bash
# Shared by the .command launchers beside it. Usage: launch.sh <page>
#
# Opens the page full screen in Google Chrome, starting by itself, from the
# files on this machine — no network needed.
#
#   --kiosk              full screen, no browser chrome, no way out but Cmd+Q
#   --autoplay-policy=…  sound without a click, so ?autostart=1 can skip the gate
#   --user-data-dir      a profile of its own, kept between launches, so the
#                        settings tuned in the room (press C) survive a restart.
#                        Never --incognito: it wipes them on every launch.
# caffeinate keeps the screen and the machine awake for as long as Chrome runs.

PAGE="$1"
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
PROFILE="$HOME/.cherven-chrome"

CHROME=""
for c in "/Applications/Google Chrome.app" "$HOME/Applications/Google Chrome.app" "/Applications/Chromium.app"; do
  bin="$c/Contents/MacOS/$(basename "$c" .app)"
  if [ -x "$bin" ]; then CHROME="$bin"; break; fi
done
if [ -z "$CHROME" ]; then
  osascript -e 'display alert "Cherven" message "Google Chrome is not installed. Install it from google.com/chrome, then double-click this again."'
  exit 1
fi
if [ ! -f "$ROOT/$PAGE" ] || [ ! -f "$ROOT/cherven.mp3" ]; then
  osascript -e "display alert \"Cherven\" message \"Missing $PAGE or cherven.mp3 in $ROOT\""
  exit 1
fi

# A kiosk already running on this profile would swallow the new launch (Chrome
# hands the URL to the running copy and ignores the flags), so close it first.
pkill -f -- "--user-data-dir=$PROFILE" 2>/dev/null && sleep 2

# file:// URL; escape what would otherwise end or break the path
path="$(printf '%s' "$ROOT/$PAGE" | sed -e 's/%/%25/g' -e 's/ /%20/g' -e 's/#/%23/g' -e 's/?/%3F/g')"
URL="file://$path?autostart=1"

echo "Cherven: $URL"
echo "Cmd+Q quits. C opens the settings panel."

exec caffeinate -dimsu "$CHROME" \
  --user-data-dir="$PROFILE" \
  --kiosk \
  --autoplay-policy=no-user-gesture-required \
  --no-first-run --no-default-browser-check \
  --disable-search-engine-choice-screen \
  --disable-features=Translate,TranslateUI \
  --noerrdialogs --hide-crash-restore-bubble --disable-session-crashed-bubble \
  --overscroll-history-navigation=0 --disable-pinch \
  --check-for-update-interval=31536000 \
  "$URL"
