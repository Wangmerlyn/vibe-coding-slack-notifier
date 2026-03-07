#!/usr/bin/env bash
# Example: configure Codex to call the Slack notifier after tasks complete.
#
# Optional: load env vars if present (safe KEY=VALUE parsing, no shell eval)
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
ENV_FILE="$SCRIPT_DIR/../../.env"
if [ -f "$ENV_FILE" ]; then
  while IFS= read -r line || [ -n "$line" ]; do
    # Skip blank lines and comments
    case "$line" in \#*|"") continue ;; esac
    # Strip optional 'export ' prefix
    line="${line#export }"
    # Only process lines with '='
    case "$line" in *=*) ;; *) continue ;; esac
    key="${line%%=*}"
    value="${line#*=}"
    # Strip surrounding quotes from value
    case "$value" in
      \"*\") value="${value#\"}"; value="${value%\"}" ;;
      \'*\') value="${value#\'}"; value="${value%\'}" ;;
    esac
    # Only set if not already in environment
    if [ -z "${!key+x}" ]; then
      export "$key=$value"
    fi
  done < "$ENV_FILE"
fi

# Replace U12345678 with your Slack User ID and adjust the path to this repository.
# Then register the command with Codex:
#   codex config set notify "/home/you/vibe-coding-slack-notifier/scripts/notifier/slack_notify.py --user-id ${SLACK_USER_ID:-U12345678}"

python /home/you/vibe-coding-slack-notifier/scripts/notifier/slack_notify.py --user-id "${SLACK_USER_ID:-U12345678}" <<'JSON'
{
  "status": "success",
  "title": "Sample Codex run",
  "summary": "Replace this payload with the one Codex supplies."
}
JSON
