#!/usr/bin/env bash
set -euo pipefail

copilot "$@"
copilot_exit=$?
/path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh
exit "$copilot_exit"
