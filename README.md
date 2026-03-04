# Vibe Coding Slack Notifier

[![CodeRabbit Reviews](https://img.shields.io/coderabbit/prs/github/Wangmerlyn/vibe-coding-slack-notifier?utm_source=oss&utm_medium=github&utm_campaign=Wangmerlyn%2Fvibe-coding-slack-notifier&labelColor=171717&color=FF570A&link=https%3A%2F%2Fcoderabbit.ai&label=CodeRabbit+Reviews)](https://coderabbit.ai)
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/Wangmerlyn/vibe-coding-slack-notifier)

Send Codex task completion alerts straight to your Slack DMs using the Slack Web API (no webhooks).

For a detailed, step-by-step guide (setup, config, debugging, FAQs), see `docs/guide.md`.

For integrations with other coding agents (Codex CLI, Claude Code, Gemini CLI, OpenCode, Copilot CLI, Cursor), see `docs/integrations.md`.
Sample config snippets live under `docs/examples/` (Codex/Claude/Gemini/OpenCode/Copilot wrapper).

## Why This Slack Notifier
- Codex has a notify hook but the VS Code extension still lacks built-in completion alerts (sound/visual); community requests for audible notifications haven’t shipped, so you must watch the editor.
- CLI-based tricks (terminal bells, desktop notifications) often fail over Remote-SSH because the sound/notification doesn’t propagate, leaving remote users uninformed.
- This project fills the gap with Slack DMs: reliable, cross-platform, and independent of where Codex runs, so you get task-completion messages without keeping VS Code in focus or on your local machine.

## Quick start
1. **Clone & env**
   - `git clone git@github.com:Wangmerlyn/vibe-coding-slack-notifier.git`
   - `cd vibe-coding-slack-notifier`
   - `conda activate codex_slack_notifier` (or create it)
   - `pip install -e '.[dev]'`
   - Optional: `pre-commit install`

2. **Create a Slack app**
   - Go to [api.slack.com/apps](https://api.slack.com/apps) → "Create New App" → "From scratch".
   - Choose a workspace and create a Bot token.
   - Add Bot scopes: `chat:write`, `im:write`, and `users:read` if you need lookups.
   - Install the app to the workspace and copy the **Bot User OAuth Token** (`xoxb-...`).
   - Find your Slack User ID (Profile → ⋯ → Copy member ID).

3. **Set environment variables**
   ```bash
   # Option A: export directly
   export SLACK_BOT_TOKEN=xoxb-your-token-here
   export SLACK_USER_ID=U12345678   # or pass --user-id

   # Option B: copy and edit .env.example, then
   cp .env.example .env
   # edit .env, then load it
   set -a; source .env; set +a
   ```
   Tokens are read from the environment only. The notifier also auto-loads `.env` (or a file passed via `--env-file`) if present.

4. **Send a manual test DM**
   ```bash
   echo '{"status":"success","title":"Codex run","summary":"Finished"}' \
     | python scripts/notifier/slack_notify.py --user-id "$SLACK_USER_ID"
   ```
   - The script opens a DM via `conversations.open` and sends the message via `chat.postMessage`.

5. **Wire up Codex notify**
   ```bash
   codex config set notify "/abs/path/to/scripts/notifier/slack_notify.py --user-id $SLACK_USER_ID"
   ```
   Codex will pipe a JSON payload on completion; the notifier formats and sends it.

6. **Run tests (optional)**
   ```bash
   pytest
   # Lint: ruff check .
   ```

## Payload expectations
- The notifier builds a message from `title`, `status`, `summary`, `duration`, and `url` when present.
- Missing fields default to a simple “Codex task completed.” message.

## More details
- `docs/notifier_slack.md` contains expanded setup notes and troubleshooting.
- Example Codex wiring: `scripts/notifier/codex_notify_example.sh`.

### Debugging Codex notify (optional)
- Use the wrapper that can read payloads from a file argument (as Codex may supply) or stdin:
  ```
  notify = ["/path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh"]
  ```
- To capture the final payload for debugging, set an env var before running Codex:
  ```
  export DEBUG_CODEX_PAYLOAD=/path/to/your/codex_payload.json
  ```
  The wrapper will write only the most relevant JSON payload to that path; unset the variable to stop logging.
