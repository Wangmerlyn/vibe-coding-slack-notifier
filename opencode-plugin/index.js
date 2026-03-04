const SLACK_API_BASE = "https://slack.com/api";
const DEFAULT_TIMEOUT_MS = 10_000;
const MAX_ATTEMPTS = 2;
const DEFAULT_DEBOUNCE_MS = 5_000;

const warned = {
  missingEnv: false,
};

const lastSessionNotifyAt = new Map();

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parsePositiveInt(value, fallback) {
  const parsed = Number.parseInt(String(value), 10);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return fallback;
  }
  return parsed;
}

function parseRetryAfterMs(retryAfterHeader) {
  if (!retryAfterHeader) {
    return 1_000;
  }
  const parsed = Number.parseFloat(retryAfterHeader);
  if (!Number.isFinite(parsed) || parsed <= 0) {
    return 1_000;
  }
  return Math.max(1_000, Math.ceil(parsed * 1_000));
}

function shouldNotify(event, debounceMs) {
  if (event?.type !== "session.idle") {
    return false;
  }

  const sessionId = event?.properties?.sessionID;
  if (!sessionId) {
    return true;
  }

  const now = Date.now();
  const last = lastSessionNotifyAt.get(sessionId) ?? 0;
  if (now - last < debounceMs) {
    return false;
  }

  lastSessionNotifyAt.set(sessionId, now);
  return true;
}

function buildMessage(repo, sessionId) {
  if (sessionId) {
    return `OpenCode task completed at repo ${repo}\nSession: ${sessionId}`;
  }
  return `OpenCode task completed at repo ${repo}`;
}

async function slackPost(token, endpoint, payload) {
  const timeoutMs = parsePositiveInt(process.env.SLACK_NOTIFY_TIMEOUT_MS, DEFAULT_TIMEOUT_MS);

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt += 1) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch(`${SLACK_API_BASE}/${endpoint}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json; charset=utf-8",
        },
        body: JSON.stringify(payload),
        signal: controller.signal,
      });

      if (response.status === 429 && attempt < MAX_ATTEMPTS) {
        const retryMs = parseRetryAfterMs(response.headers.get("retry-after"));
        await sleep(retryMs);
        continue;
      }

      if (response.status >= 500 && attempt < MAX_ATTEMPTS) {
        await sleep(1_000);
        continue;
      }

      if (!response.ok) {
        const body = await response.text();
        throw new Error(`Slack HTTP ${response.status}: ${body || "empty response"}`);
      }

      const data = await response.json();
      if (!data?.ok) {
        throw new Error(`Slack API error: ${data?.error || "unknown_error"}`);
      }

      return data;
    } finally {
      clearTimeout(timer);
    }
  }

  throw new Error(`Slack request failed for ${endpoint}`);
}

async function sendSlackDm(token, userId, text) {
  const dm = await slackPost(token, "conversations.open", { users: userId });
  const channelId = dm?.channel?.id;
  if (!channelId) {
    throw new Error("Slack did not return DM channel id");
  }
  await slackPost(token, "chat.postMessage", {
    channel: channelId,
    text,
  });
}

export const OpenCodeSlackNotifierPlugin = async ({ directory, worktree }) => {
  const debounceMs = parsePositiveInt(process.env.OPENCODE_SLACK_DEBOUNCE_MS, DEFAULT_DEBOUNCE_MS);

  return {
    event: async ({ event }) => {
      if (!shouldNotify(event, debounceMs)) {
        return;
      }

      const token = process.env.SLACK_BOT_TOKEN;
      const userId = process.env.SLACK_USER_ID;
      if (!token || !userId) {
        if (!warned.missingEnv) {
          warned.missingEnv = true;
          console.warn(
            "[opencode-vibe-coding-slack-notifier] Missing SLACK_BOT_TOKEN or SLACK_USER_ID; skipping notification.",
          );
        }
        return;
      }

      const repo = worktree || directory || process.cwd();
      const sessionId = event?.properties?.sessionID;
      const message = buildMessage(repo, sessionId);

      try {
        await sendSlackDm(token, userId, message);
        if (process.env.OPENCODE_SLACK_DEBUG === "1") {
          console.log("[opencode-vibe-coding-slack-notifier] Slack notification sent.");
        }
      } catch (error) {
        const detail = error instanceof Error ? error.message : String(error);
        console.error(`[opencode-vibe-coding-slack-notifier] Failed to send Slack notification: ${detail}`);
      }
    },
  };
};

export default OpenCodeSlackNotifierPlugin;
