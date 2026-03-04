# Integrating Other Coding Agents with the Slack Notifier

Many coding-agent CLIs expose hooks or plugin points that can run shell commands on lifecycle events. Point those hooks at `scripts/notifier/codex_notify_wrapper.sh` (or `slack_notify.py` directly) to deliver Slack DMs when long tasks finish.

## General pattern
- Ensure `SLACK_BOT_TOKEN` and `SLACK_USER_ID` are available (via `.env` or exported env vars).
- Use the wrapper for robustness across stdin/file/inline payloads:
  ```
  /path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh
  ```
- Optionally capture the payload for debugging:
  ```
  DEBUG_CODEX_PAYLOAD=/tmp/codex_payload.json
  ```
- If your tool provides a payload file path, pass it as the first argument; if it pipes JSON, no args are needed.

## Claude Code
- Supports a hook system; add a hook on events like `Stop` / `SessionEnd`.
- Example `.claude/settings.json` snippet:
  ```json
  {
    "hooks": {
      "Stop": [
        {
          "matcher": "*",
          "hooks": [
            { "type": "command", "command": "/path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh" }
          ]
        }
      ]
    }
  }
  ```
  See `docs/examples/claude/settings.json`.

## Gemini CLI
- Similar hook support; configure in `.gemini/settings.json`.
  ```json
  {
    "hooks": {
      "Stop": [
        {
          "type": "command",
          "command": "/path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh"
        }
      ]
    }
  }
  ```
  See `docs/examples/gemini/hooks.json` for a copy/paste starter that matches `.gemini/settings.json`.

## OpenCode
- Use its plugin/hook extensibility to invoke the notifier on relevant events (e.g., session complete).
- Skeleton plugin example (`.opencode/plugins/slackNotifier.js`):
  ```js
  import { exec } from "node:child_process";

  export const SlackNotifierPlugin = async () => ({
    event: async ({ event }) => {
      if (event?.type === "session.idle") {
        exec("/path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh");
      }
    },
  });
  ```
  See `docs/examples/opencode/slackNotifier.js`.

## Copilot CLI & Cursor
- No native hooks today. Workaround: wrap the CLI call and invoke the notifier afterward:
  ```bash
  copilot "$@"
  /path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh
  ```
  See `docs/examples/copilot_wrapper.sh` for a minimal wrapper.

## Codex CLI (reference)
- Example `~/.codex/config.toml` with the wrapper:
  ```toml
  model = "<YOUR_CODEX_MODEL_ID>"   # replace with your Codex model id
  model_reasoning_effort = "high"
  notify = ["/path/to/vibe-coding-slack-notifier/scripts/notifier/codex_notify_wrapper.sh"]
  ```
  See `docs/examples/codex/config.toml` for a full sample. Optional flags: `DEBUG_CODEX_PAYLOAD` (capture payload) and `ENV_FILE` (alternate env path).

## Tips
- Keep the notify command short and use absolute paths.
- The wrapper reads the payload from a file path passed as `$1`. If `$1` is an inline JSON string, it's also handled. If no argument is given, it reads from stdin.
- Set `LOGLEVEL=WARNING` (or use `--log-level WARNING`) when calling `slack_notify.py` directly to avoid chatty stdout/stderr in host tools.
