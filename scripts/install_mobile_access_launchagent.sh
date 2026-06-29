#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PLIST="/Users/piguin/Library/LaunchAgents/com.evidentia.mobile-access.plist"
LOG_DIR="${ROOT}/data/mobile-access"

mkdir -p "${LOG_DIR}"

cat >"${PLIST}" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>com.evidentia.mobile-access</string>
  <key>ProgramArguments</key>
  <array>
    <string>${ROOT}/scripts/start_mobile_access.sh</string>
  </array>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>300</integer>
  <key>StandardOutPath</key>
  <string>${LOG_DIR}/launchagent.out.log</string>
  <key>StandardErrorPath</key>
  <string>${LOG_DIR}/launchagent.err.log</string>
</dict>
</plist>
EOF

chmod 600 "${PLIST}"
launchctl bootout "gui/$(id -u)" "${PLIST}" >/dev/null 2>&1 || true
launchctl bootstrap "gui/$(id -u)" "${PLIST}"
launchctl kickstart -k "gui/$(id -u)/com.evidentia.mobile-access"
launchctl print "gui/$(id -u)/com.evidentia.mobile-access" | sed -n '1,80p'
