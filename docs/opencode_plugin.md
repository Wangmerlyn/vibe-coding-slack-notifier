# OpenCode Plugin Install (Marketplace / npm)

This repository now exposes an installable OpenCode plugin package:

- npm package: `opencode-vibe-coding-slack-notifier`
- plugin export: `OpenCodeSlackNotifierPlugin` (default export included)

The plugin sends Slack DM notifications when OpenCode emits `session.idle`.

## 1) Configure Slack credentials (recommended: env file, no manual export)

Create `~/.config/opencode/slack-notifier.env`:

```bash
mkdir -p ~/.config/opencode
cat > ~/.config/opencode/slack-notifier.env <<'EOF'
SLACK_BOT_TOKEN=xoxb-your-token-here
SLACK_USER_ID=U12345678
EOF
```

The plugin auto-loads this file on first use.

If you want a custom path, set:

```bash
export OPENCODE_SLACK_ENV_FILE=/absolute/path/to/slack-notifier.env
```

You can still use direct environment variables if preferred:

```bash
export SLACK_BOT_TOKEN=xoxb-your-token-here
export SLACK_USER_ID=U12345678
```

Optional:

```bash
# Debug plugin logs
export OPENCODE_SLACK_DEBUG=1

# Debounce repeated session.idle notifications (milliseconds)
export OPENCODE_SLACK_DEBOUNCE_MS=5000

# Slack HTTP timeout (milliseconds)
export SLACK_NOTIFY_TIMEOUT_MS=10000
```

## 2) Install package

```bash
npm install -g opencode-vibe-coding-slack-notifier
# or
bun add -g opencode-vibe-coding-slack-notifier
```

## 3) Enable in OpenCode config (official plugin flow)

Edit `~/.config/opencode/opencode.json`:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "plugin": ["opencode-vibe-coding-slack-notifier"]
}
```

A full copy/paste example is available at `docs/examples/opencode/opencode.json`.

## 4) Verify

```bash
opencode debug config
```

You should see `opencode-vibe-coding-slack-notifier` in the resolved `plugin` list.

## 5) Trigger a test run

Start any OpenCode task and wait for the session to become idle; the plugin will send:

- `OpenCode task completed at repo <path>`
- and include session ID when available.

## Troubleshooting

- `missing_scope`: ensure Slack app includes `chat:write` and `im:write`/`conversations:write`, then reinstall app to workspace.
- No message received: verify `SLACK_BOT_TOKEN` and `SLACK_USER_ID` are exported in the same environment where OpenCode runs.
- No message received: confirm credentials exist in `~/.config/opencode/slack-notifier.env` or set `OPENCODE_SLACK_ENV_FILE`.
- Repeated messages: increase `OPENCODE_SLACK_DEBOUNCE_MS`.
