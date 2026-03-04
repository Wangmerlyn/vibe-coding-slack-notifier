# Slack DM notifier for Codex

Send Codex completion events as Slack direct messages using the Slack Web API (no webhooks required).

## Slack app setup
- Create a Slack app (from a manifest or <https://api.slack.com/apps>). Choose a Bot token.
- Add bot scopes: `chat:write`, `im:write`, and `users:read` if you need to look up IDs.
- Install the app to your workspace and grab the **Bot User OAuth Token** (starts with `xoxb-`).
- Find your Slack User ID (profile → ⋯ → Copy member ID) for the DM recipient.

## Environment variables
```
# Option A: export directly
export SLACK_BOT_TOKEN=xoxb-123...             # required
export SLACK_USER_ID=U12345678                 # optional if passed via --user-id

# Option B: use a .env file (see .env.example)
cp .env.example .env
set -a; source .env; set +a
```
Tokens are read from the environment only; nothing is hard-coded. The notifier also auto-loads `.env` (or a file passed via `--env-file`) if present.

## Script usage
The notifier lives at `scripts/notifier/slack_notify.py` and accepts JSON payloads on stdin or via flags.
```
# Send a quick manual notification
echo '{"status":"success","title":"Codex run","summary":"Finished"}' \
  | python scripts/notifier/slack_notify.py --user-id U12345678
```
Flags:
- `--user-id`: Slack User ID (fallback: `SLACK_USER_ID`).
- `--token-env`: Name of the env var holding the bot token (default `SLACK_BOT_TOKEN`).
- `--payload` / `--payload-file`: Provide JSON directly or from a file.
- `--title`: Optional override for the message title.

## Codex notify integration
Register the script so Codex calls it after tasks finish:
```
codex config set notify "/abs/path/to/scripts/notifier/slack_notify.py --user-id U12345678"
```
Codex will pipe a JSON payload to the script; the notifier formats a concise DM (title, status, duration, summary, link when present).
A concrete example is in `scripts/notifier/codex_notify_example.sh`.

### Optional debugging
- If Codex supplies a payload file instead of stdin, use the wrapper:
  ```
  notify = ["/path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh"]
  ```
- To capture the selected payload for inspection, set:
  ```
  export DEBUG_CODEX_PAYLOAD=/path/to/your/codex_payload.json
  ```
  Unset this variable to stop logging.

> The wrapper defaults to loading `.env` from the repo root; override with `ENV_FILE=/custom/path/.env` if you store credentials elsewhere.

## Installing & testing
```
conda activate codex_slack_notifier
pip install -e .[dev]
pytest
```
Ruff linting: `ruff check .`

## Troubleshooting
- Missing token/user ID: set `SLACK_BOT_TOKEN` and `SLACK_USER_ID` or pass `--user-id`.
- Rate limits/HTTP 5xx: the script retries once; errors are logged to stderr and exit with code 1.
- Message content looks sparse: ensure the payload includes keys like `title`, `status`, `summary`, `duration`, `url`.
