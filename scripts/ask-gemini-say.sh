#!/usr/bin/env bash
set -euo pipefail

# ask-gemini-say.sh
# Runs `nvm use v23.11.0 && gemini "<prompt>"` and speaks the answer.
# - Defaults to running in the background so your shell returns immediately.
# - Uses the first working TTS: spd-say, espeak-ng, espeak, pico2wave (+ paplay/aplay).

usage() {
  cat <<'USAGE'
Usage: ask-gemini-say.sh [--fg] [--no-tts] <your question here>

Options:
  --fg        Run in foreground (do not daemonize).
  --no-tts    Do not speak; only print the response.

Examples:
  ./ask-gemini-say.sh "What is the capital of Peru?"
  ./ask-gemini-say.sh --fg "Summarize TCP vs UDP in one paragraph."
USAGE
}

if [[ ${1:-} == "-h" || ${1:-} == "--help" || $# -eq 0 ]]; then
  usage
  exit 0
fi

# Parse flags
RUN_FOREGROUND=false
NO_TTS=false
args=()
for arg in "$@"; do
  case "$arg" in
    --fg)
      RUN_FOREGROUND=true
      ;;
    --no-tts)
      NO_TTS=true
      ;;
    *)
      args+=("$arg")
      ;;
  esac
done

if [[ ${#args[@]} -eq 0 ]]; then
  echo "Error: Missing prompt." >&2
  usage
  exit 1
fi

PROMPT=${args[*]}

daemonize_if_needed() {
  if [[ "$RUN_FOREGROUND" == true ]]; then
    return 0
  fi
  # Relaunch self in background and exit parent.
  # Use nohup to detach from terminal cleanly.
  nohup "$0" --fg ${NO_TTS:+--no-tts} "$PROMPT" >/dev/null 2>&1 &
  bg_pid=$!
  echo "Started Gemini query in background (PID $bg_pid)."
  exit 0
}

load_nvm() {
  # Try common locations for nvm. If not found, we continue; gemini may still work.
  if command -v nvm >/dev/null 2>&1; then
    return 0
  fi
  local nvm_dir
  nvm_dir="${NVM_DIR:-$HOME/.nvm}"
  if [[ -s "$nvm_dir/nvm.sh" ]]; then
    # shellcheck source=/dev/null
    . "$nvm_dir/nvm.sh"
    return 0
  fi
  # Some installations use /usr/share/nvm or /usr/local/opt/nvm
  for candidate in /usr/share/nvm /usr/local/opt/nvm; do
    if [[ -s "$candidate/nvm.sh" ]]; then
      # shellcheck source=/dev/null
      . "$candidate/nvm.sh"
      return 0
    fi
  done
  return 1
}

ensure_node_version() {
  if load_nvm; then
    # Ignore errors if the exact version is unavailable; continue with current Node.
    nvm use v23.11.0 >/dev/null 2>&1 || true
  fi
}

ensure_gemini_available() {
  if ! command -v gemini >/dev/null 2>&1; then
    echo "Error: 'gemini' CLI not found in PATH." >&2
    echo "- Ensure the Gemini CLI is installed and configured." >&2
    echo "- If installed via npm, verify the correct Node version with nvm." >&2
    exit 127
  fi
}

filter_text() {
  # Strip a bit of Markdown punctuation to improve TTS clarity.
  sed -E 's/[`*_#>]+//g; s/^\s+//; s/\s+$//' | sed -E 's/\[([^\]]+)\]\([^)]*\)/\1/g'
}

say_text() {
  local text="$1"
  if [[ "$NO_TTS" == true ]]; then
    return 0
  fi

  # Prefer system speech-dispatcher if available (often better voices).
  if command -v spd-say >/dev/null 2>&1; then
    echo "Using system speech-dispatch"
    spd-say -w "$text" && return 0
  fi

  # espeak-ng (newer) or espeak fallback.
  if command -v espeak-ng >/dev/null 2>&1; then
    echo "Using espeak-ng speech-dispatch"
    espeak-ng -s 180 -p 30 -a 200 "$text" && return 0
  fi
  if command -v espeak >/dev/null 2>&1; then
    echo "Using espeak speech-dispatch"
    espeak -s 180 -p 30 -a 200 "$text" && return 0
  fi

  # pico2wave fallback (generates WAV); try paplay or aplay.
  if command -v pico2wave >/dev/null 2>&1; then
    echo "Using pico2wave speech-dispatch"
    local tmp
    tmp=$(mktemp --suffix=.wav)
    pico2wave -w "$tmp" "$text" >/dev/null 2>&1 || { rm -f "$tmp"; return 1; }
    if command -v paplay >/dev/null 2>&1; then
      paplay "$tmp" || true
    else
      aplay "$tmp" || true
    fi
    rm -f "$tmp"
    return 0
  fi

  echo "Warning: No TTS engine found (tried spd-say, espeak-ng, espeak, pico2wave)." >&2
  return 1
}

main() {
  daemonize_if_needed
  ensure_node_version
  ensure_gemini_available

  # Run Gemini with the prompt; capture full output.
  # If your gemini CLI supports streaming flags, you can add them here.
  local raw
  if ! raw=$(gemini --prompt "$PROMPT" 2>&1); then
    echo "$raw" >&2
    exit 1
  fi

  # Clean up text a little for TTS, but print original to stdout for fidelity.
  echo "$raw"
  local spoken
  spoken=$(printf "%s" "$raw" | filter_text)
  say_text "$spoken" || true
}

main "$@"
