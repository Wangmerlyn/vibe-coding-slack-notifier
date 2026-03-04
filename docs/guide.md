# Vibe Coding Slack Notifier – Full Guide

This guide walks through setup, configuration, usage, debugging, and development for sending Codex task notifications to Slack DMs.

## What it does
- Opens a DM channel to a target Slack user.
- Posts a concise summary using fields from the Codex payload (`title`, `status`, `summary`, `duration`, `url`).
- Works with either stdin or a payload file (as Codex may provide).
- Optional debug capture of the payload used.

## Requirements
- Python 3.12+
- Slack app with bot token (`xoxb-...`) and scopes: `chat:write`, `im:write` (or `conversations:write`). `users:read` is handy if you need to look up IDs.
- Your Slack User ID (Profile → ⋯ → Copy member ID).

## Install
```bash
git clone git@github.com:Wangmerlyn/vibe-coding-slack-notifier.git
cd vibe-coding-slack-notifier
conda activate codex_slack_notifier  # or your preferred env
pip install -e '.[dev]'
# optional
pre-commit install
```

## Configure secrets
Pick one:
```bash
# Direct export
export SLACK_BOT_TOKEN=xoxb-your-token
export SLACK_USER_ID=U12345678

# Or .env file (recommended)
cp .env.example .env
edit .env   # fill SLACK_BOT_TOKEN and SLACK_USER_ID
# auto-loaded by the wrapper/notifier
```

## Wire Codex notify
Use the portable wrapper so payloads from stdin or file both work:
```toml
# ~/.codex/config.toml
notify = ["/path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh"]
```
Options:
- Override env file location: `ENV_FILE=/path/to/.env`.
- Capture the payload used: `DEBUG_CODEX_PAYLOAD=/path/to/codex_payload.json` (unset to disable).

## Manual send (smoke test)
```bash
echo '{"status":"success","title":"Test ping","summary":"Hello"}' \
  | python scripts/notifier/slack_notify.py --user-id "$SLACK_USER_ID"
```

## Wrapper behavior
- Accepts `$1` as a payload file path or falls back to stdin.
- Validates readability; if not readable, waits briefly then falls back to stdin (logs a warning).
- Loads env from `${ENV_FILE:-$REPO_ROOT/.env}`.
- Writes the selected payload to `DEBUG_CODEX_PAYLOAD` if set.
- Forwards payload to `slack_notify.py` with `--env-file`.

## Troubleshooting
- `missing_scope`: ensure Slack app has `chat:write` and `im:write`/`conversations:write`; reinstall the app and use the updated token.
- `Missing Slack token/user ID`: set env vars or ensure `.env` is loaded; wrapper’s `ENV_FILE` can point elsewhere.
- No DM received: set `DEBUG_CODEX_PAYLOAD` and inspect the payload; verify `SLACK_USER_ID` is correct.
- Rate limited: the notifier retries once on HTTP 429/5xx.
- Empty payload: notifier still sends a default “Codex task completed.” message.

## Development
- Format/lint: `pre-commit run --all-files` (uses ruff).
- Tests: `pytest` (mocks Slack API).
- CI: GitHub Actions runs pre-commit on push/PR.

## File map (docs)
- `README.md` – quick start and essential snippets.
- `docs/guide.md` – this detailed guide.
- `docs/notifier_slack.md` – focused setup notes for Slack + Codex.
- `scripts/notifier/codex_notify_wrapper.sh` – Codex-facing entrypoint.
- `scripts/notifier/slack_notify.py` – CLI entry to the notifier logic.
