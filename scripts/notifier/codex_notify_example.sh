#!/usr/bin/env bash
# Example: configure Codex to call the Slack notifier after tasks complete.
#
# Optional: load env vars if present
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)
if [ -f "$SCRIPT_DIR/../../.env" ]; then
  set -a
  . "$SCRIPT_DIR/../../.env"
  set +a
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
