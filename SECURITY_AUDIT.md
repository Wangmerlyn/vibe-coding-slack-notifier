# Security Audit Report

**Date:** 2026-03-07
**Scope:** Full repository review of vibe-coding-slack-notifier
**Verdict:** No malicious code found. Minor improvements recommended.

## Summary

The codebase is clean and does exactly what it claims: sends Slack DM
notifications when coding agent tasks complete. There is no data exfiltration,
no backdoors, no obfuscated code, and no suspicious network calls beyond the
expected Slack API (`https://slack.com/api`).

## Findings

### 1. Shell sourcing of `.env` in example script (Medium-Low)

**File:** `scripts/notifier/codex_notify_example.sh:8`

The example script uses `. "$SCRIPT_DIR/../../.env"` (shell source) to load
environment variables. If the `.env` file contained shell commands beyond
`KEY=VALUE` pairs, they would execute. The Python `_load_env_file()` correctly
uses safe line-by-line parsing instead.

**Recommendation:** Replace shell sourcing with safe parsing, or add a comment
warning that the file is sourced as shell code.

### 2. Auto-loading `.env` from current working directory (Low)

**File:** `src/codex_slack_notifier/notifier.py:240`

If no `--env-file` is specified, the notifier auto-loads `.env` from the
current working directory. A malicious `.env` in an untrusted directory could
inject unexpected token/user values, redirecting notifications to an
attacker-controlled Slack account.

**Recommendation:** Consider only auto-loading from known paths (e.g. the
script's own directory or `$HOME/.config/`), or warn when loading from CWD.

### 3. Inconsistent env value parsing between Python and JS (Low)

**Files:** `opencode-plugin/index.js:53-62` vs `src/codex_slack_notifier/notifier.py:228-231`

The JS plugin strips surrounding quotes from env values (`"val"` or `'val'`),
but the Python `_load_env_file()` does not. A `.env` with
`SLACK_BOT_TOKEN="xoxb-..."` works in JS but passes quotes as part of the
token in Python, causing silent auth failures.

**Recommendation:** Add quote-stripping to the Python env loader to match JS
behavior.

### 4. `DEBUG_CODEX_PAYLOAD` writes to arbitrary path (Low)

**File:** `scripts/notifier/codex_notify_wrapper.sh:81-85`

If the `DEBUG_CODEX_PAYLOAD` environment variable is set, the wrapper writes
the payload to that path. An attacker with environment control could
potentially overwrite files, though this requires existing environment access.

**Recommendation:** Acceptable for a debug feature. Consider validating the
target path or documenting the risk.

### 5. No input validation on Slack IDs (Low)

User-supplied `user_id` and `channel_id` values are passed directly to the
Slack API without local validation. Slack rejects invalid values, so
exploitation potential is negligible.

**Recommendation:** No action needed; Slack is the authority on valid IDs.

## Positive Security Practices

- `SLACK_API_BASE` is hardcoded — cannot be redirected via environment variables
- TLS certificate verification uses secure defaults (not disabled)
- Tokens are never logged, even at DEBUG level
- Shell wrapper passes file paths as Python arguments, not interpolated into
  code — safe from injection
- `.env` is in `.gitignore` — secrets won't be accidentally committed
- Env loaders do not overwrite existing environment variables
- Retry logic is bounded (max 2 attempts) — no infinite loops
- Network timeouts are enforced (10 seconds default)
