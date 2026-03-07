import json
import os
from pathlib import Path
from typing import Any, Dict, List

import pytest

from codex_slack_notifier import notifier
from codex_slack_notifier.notifier import (
    SlackNotificationError,
    SlackNotifier,
    build_message,
    load_payload,
)


class FakeResponse:
    def __init__(
        self,
        status_code: int = 200,
        json_data: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}

    def json(self) -> Dict[str, Any]:
        return self._json

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise Exception(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses: List[FakeResponse]) -> None:
        self.responses = responses
        self.posts: list[dict[str, Any]] = []

    def post(
        self,
        url: str,
        headers: dict[str, Any],
        json: dict[str, Any],
        timeout: int,
    ) -> FakeResponse:
        self.posts.append({"url": url, "headers": headers, "json": json, "timeout": timeout})
        return self.responses.pop(0)


def test_build_message_prefers_payload_fields() -> None:
    payload = {
        "title": "Run notebook",
        "status": "success",
        "duration": "3m 12s",
        "summary": "Notebook finished with no errors",
        "url": "https://example.com/logs/123",
        "repo": "/home/user/project",
    }
    message = build_message(payload)
    assert "Run notebook" in message
    assert "Status: success" in message
    assert "3m 12s" in message
    assert "Notebook finished with no errors" in message
    assert "https://example.com/logs/123" in message
    assert "project" in message


def test_build_message_repo_only_adds_default_headline() -> None:
    message = build_message({"repo": "/path/to/repo"})
    assert message == "Codex task completed at repo /path/to/repo"


def test_send_dm_sends_open_then_message(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        FakeResponse(json_data={"ok": True, "channel": {"id": "C123"}}),
        FakeResponse(json_data={"ok": True, "ts": "1.2"}),
    ]
    session = FakeSession(responses)
    notifier = SlackNotifier("xoxb-test-token", session=session)
    monkeypatch.setattr("time.sleep", lambda _: None)

    notifier.send_dm("U999", "hello world")

    assert len(session.posts) == 2
    assert session.posts[0]["json"]["users"] == "U999"
    assert session.posts[1]["json"]["text"] == "hello world"


def test_send_dm_retries_on_rate_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    responses = [
        FakeResponse(
            status_code=429,
            json_data={"ok": False, "error": "ratelimited"},
            headers={"Retry-After": "0"},
        ),
        FakeResponse(json_data={"ok": True, "channel": {"id": "C123"}}),
        FakeResponse(json_data={"ok": True, "ts": "1.2"}),
    ]
    session = FakeSession(responses)
    notifier = SlackNotifier("xoxb-test-token", session=session)
    monkeypatch.setattr("time.sleep", lambda _: None)

    notifier.send_dm("U999", "rate limited message")

    assert len(session.posts) == 3
    assert session.posts[0]["url"].endswith("conversations.open")
    assert session.posts[1]["url"].endswith("conversations.open")
    assert session.posts[2]["url"].endswith("chat.postMessage")


def test_retry_after_parses_float_and_clamps(monkeypatch: pytest.MonkeyPatch) -> None:
    sleep_calls: list[int] = []
    responses = [
        FakeResponse(
            status_code=429,
            json_data={"ok": False, "error": "ratelimited"},
            headers={"Retry-After": "1.6"},
        ),
        FakeResponse(json_data={"ok": True, "channel": {"id": "C123"}}),
        FakeResponse(json_data={"ok": True, "ts": "1.2"}),
    ]
    session = FakeSession(responses)
    notifier = SlackNotifier("xoxb-test-token", session=session)
    monkeypatch.setattr("time.sleep", lambda seconds: sleep_calls.append(seconds))

    notifier.send_dm("U999", "rate limited message")

    assert sleep_calls == [2]
    assert len(session.posts) == 3


def test_load_payload_supports_file(tmp_path: Path) -> None:
    payload_path = tmp_path / "payload.json"
    payload_data = {"status": "done"}
    payload_path.write_text(json.dumps(payload_data), encoding="utf-8")

    loaded = load_payload(None, str(payload_path))

    assert loaded == payload_data


def test_load_payload_rejects_invalid_json(tmp_path: Path) -> None:
    payload_path = tmp_path / "bad.json"
    payload_path.write_text("not-json", encoding="utf-8")

    with pytest.raises(SlackNotificationError):
        load_payload(None, str(payload_path))


def test_build_message_with_empty_payload_returns_default() -> None:
    """Ensure build_message returns the default message for an empty payload."""
    message = build_message({})
    assert message == "Codex task completed."


def test_env_file_loader_does_not_overwrite_existing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure _load_env_file does not overwrite existing environment variables."""
    env_file = tmp_path / ".env"
    env_file.write_text("SLACK_BOT_TOKEN=token-from-file\n", encoding="utf-8")
    monkeypatch.setenv("SLACK_BOT_TOKEN", "token-from-env")

    from codex_slack_notifier import notifier

    notifier._load_env_file(str(env_file))

    assert os.environ["SLACK_BOT_TOKEN"] == "token-from-env"


def test_env_file_loader_sets_vars(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("export SLACK_BOT_TOKEN=test-token\nSLACK_USER_ID=U1\n", encoding="utf-8")
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("SLACK_USER_ID", raising=False)

    notifier._load_env_file(str(env_file))

    assert os.environ["SLACK_BOT_TOKEN"] == "test-token"
    assert os.environ["SLACK_USER_ID"] == "U1"


def test_env_file_loader_strips_surrounding_quotes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ensure _load_env_file strips surrounding quotes from values."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        'SLACK_BOT_TOKEN="xoxb-quoted"\nSLACK_USER_ID=\'U_SINGLE\'\n',
        encoding="utf-8",
    )
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("SLACK_USER_ID", raising=False)

    notifier._load_env_file(str(env_file))

    assert os.environ["SLACK_BOT_TOKEN"] == "xoxb-quoted"
    assert os.environ["SLACK_USER_ID"] == "U_SINGLE"


def test_main_uses_user_id_from_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("SLACK_BOT_TOKEN=test-token\nSLACK_USER_ID=U123\n", encoding="utf-8")
    monkeypatch.delenv("SLACK_BOT_TOKEN", raising=False)
    monkeypatch.delenv("SLACK_USER_ID", raising=False)
    monkeypatch.setenv("REPO_ROOT", "/tmp/repo")

    sent: list[tuple[str, str]] = []

    def fake_send_dm(self: SlackNotifier, user_id: str, message: str) -> None:  # type: ignore[override]
        sent.append((user_id, message))

    monkeypatch.setattr(notifier.SlackNotifier, "send_dm", fake_send_dm)

    exit_code = notifier.main(
        ["--env-file", str(env_file), "--payload", '{"status":"ok","repo":"/tmp/repo"}']
    )

    assert exit_code == 0
    assert sent and sent[0][0] == "U123"
