#!/usr/bin/env bash
set -euo pipefail

cleanup_tmp() { [[ "${TMP_PAYLOAD_CREATED:-0}" == "1" && -n "${TMP_PAYLOAD:-}" && -f "$TMP_PAYLOAD" ]] && rm -f "$TMP_PAYLOAD"; }
trap cleanup_tmp EXIT

# Accept payload via file path, inline JSON argument, or stdin.
if [[ -n "${1:-}" && "${1}" != "/dev/stdin" && "${1}" != "-" ]]; then
  candidate="${1}"
  # If the argument looks like inline JSON, materialize it to a temp file.
  if [[ "$candidate" =~ ^[\{\[] ]]; then
    TMP_PAYLOAD="$(mktemp)"
    TMP_PAYLOAD_CREATED="1"
    printf "%s\n" "$candidate" > "$TMP_PAYLOAD"
    src="$TMP_PAYLOAD"
  else
    if [[ ! -r "${candidate}" ]]; then
      # brief retry in case the file is being written
      sleep 0.2
    fi
    if [[ -f "${candidate}" && -r "${candidate}" ]]; then
      src="${candidate}"
    else
      echo "Payload file '${candidate}' not found or not readable, falling back to stdin" >&2
      src="/dev/stdin"
    fi
  fi
else
  src="/dev/stdin"
fi
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
ENV_FILE="${ENV_FILE:-"$REPO_ROOT/.env"}"

# If DEBUG_CODEX_PAYLOAD is set to a filepath, the selected payload will be written there.
filter_and_forward() {
  REPO_ROOT="$REPO_ROOT" python3 - "$src" <<'PY'
import json
import sys
import pathlib
import os

source = sys.argv[1]
debug_path = os.environ.get("DEBUG_CODEX_PAYLOAD")
repo_root = os.environ.get("REPO_ROOT")

def read_lines():
    if source != "/dev/stdin" and pathlib.Path(source).exists():
        return pathlib.Path(source).read_text(encoding="utf-8", errors="ignore").splitlines()
    return sys.stdin.read().splitlines()

def is_relevant(obj: dict) -> bool:
    keys = {"status", "state", "title", "event", "task", "summary", "message", "details"}
    return any(k in obj for k in keys)

last_valid = None
last_relevant = None

for line in read_lines():
    clean = line.replace("\x00", "").strip()
    if not clean:
        continue
    try:
        obj = json.loads(clean)
    except json.JSONDecodeError:
        continue
    last_valid = obj
    if isinstance(obj, dict) and is_relevant(obj):
        last_relevant = obj

chosen = last_relevant or last_valid or {}
if repo_root and isinstance(chosen, dict):
    chosen.setdefault("repo", repo_root)
out = json.dumps(chosen)
if debug_path:
    try:
        pathlib.Path(debug_path).write_text(out + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"DEBUG_CODEX_PAYLOAD write failed: {exc}", file=sys.stderr)
sys.stdout.write(out)
PY
}

if ! filter_and_forward | python3 "$SCRIPT_DIR/slack_notify.py" --env-file "$ENV_FILE"; then
  echo "Notifier failed to send message" >&2
  exit 1
fi
