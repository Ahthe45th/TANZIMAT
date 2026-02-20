#!/usr/bin/env bash
set -euo pipefail

LOG=/var/log/browser-block.log
WRAP_DIR=/usr/bin   # wrappers shadow real binaries here
FIREFOX_WRAP="${WRAP_DIR}/firefox"
CHROMIUM_WRAP="${WRAP_DIR}/chromium"
CHROME_WRAP="${WRAP_DIR}/chrome"
GOOGLE_CHROME_WRAP="${WRAP_DIR}/google-chrome"

ts() { date +"%Y-%m-%d %H:%M:%S"; }

log() { echo "[$(ts)] $*" >>"$LOG"; }

# Desktop notification to any logged-in graphical user
notify_all() {
  local title="$1" body="$2"
  if ! command -v notify-send >/dev/null 2>&1; then
    log "notify-send not found; skipping notifications"
    return 0
  fi
  while read -r sid user seat; do
    uid=$(id -u "$user" 2>/dev/null || echo "")
    [ -n "$uid" ] || continue
    bus="unix:path=/run/user/${uid}/bus"
    su - "$user" -s /bin/sh -c \
      "DBUS_SESSION_BUS_ADDRESS='${bus}' notify-send '${title}' '${body}' -u normal" \
      >/dev/null 2>&1 || true
  done < <(loginctl list-sessions --no-legend | awk '{print $1" "$3" "$2}')
}

make_wrapper() {
  local target="$1"
  log "make_wrapper: ensuring WRAP_DIR=$WRAP_DIR"
  install -d -m 0755 "$WRAP_DIR"
  log "make_wrapper: writing temp file for $target"
  tmp="$(mktemp)"
  cat >"$tmp" <<'EOF'
#!/usr/bin/env bash
echo "This browser is temporarily disabled on this system." >&2
exit 1
EOF
  log "make_wrapper: installing wrapper to $target"
  install -m 0755 "$tmp" "$target"
  rm -f "$tmp"
  log "make_wrapper: done for $target"
}

block() {
  log "BLOCK start: killing + creating wrappers"
  /usr/bin/pkill firefox || true
  /usr/bin/pkill chromium || true
  /usr/bin/pkill chrome || true
  /usr/bin/pkill google-chrome || true

  make_wrapper "$FIREFOX_WRAP"
  make_wrapper "$CHROMIUM_WRAP"
  make_wrapper "$CHROME_WRAP"
  make_wrapper "$GOOGLE_CHROME_WRAP"

  log "PATH=$PATH"
  log "which firefox=$(command -v firefox || true)"
  log "which chromium=$(command -v chromium || true)"
  log "which chrome=$(command -v chrome || true)"
  log "which google-chrome=$(command -v google-chrome || true)"
  log "BLOCK done"
  notify_all "Browsers blocked" "Firefox & Chromium/Chrome disabled until next unblock."
}

unblock() {
  log "UNBLOCK start: removing wrappers"
  rm -f "$FIREFOX_WRAP" "$CHROMIUM_WRAP" "$CHROME_WRAP" "$GOOGLE_CHROME_WRAP"
  log "UNBLOCK done"
  notify_all "Browsers unblocked" "Firefox & Chromium/Chrome are enabled."
}

# Run 4× within the minute (≈0s, 15s, 30s, 45s)
sweep() {
  log "SWEEP start (4x within minute)"
  for i in 1 2 3 4; do
    /usr/bin/pkill firefox || true
    /usr/bin/pkill chromium || true
    /usr/bin/pkill chrome || true
    /usr/bin/pkill google-chrome || true
    [ $i -lt 4 ] && sleep 15
  done
  log "SWEEP end"
}

case "${1:-}" in
  block)   block ;;
  unblock) unblock ;;
  sweep)   sweep ;;
  *) echo "Usage: $0 {block|unblock|sweep}" >&2; exit 1 ;;
esac
