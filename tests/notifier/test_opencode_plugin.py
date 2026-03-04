import json
from pathlib import Path


def test_package_json_exposes_opencode_plugin_entrypoint() -> None:
    package_json = Path("package.json")
    assert package_json.exists()

    data = json.loads(package_json.read_text(encoding="utf-8"))

    assert data["name"] == "opencode-vibe-coding-slack-notifier"
    assert data["main"] == "./opencode-plugin/index.js"
    assert data["types"] == "./opencode-plugin/index.d.ts"
    assert data["exports"]["."]["import"] == "./opencode-plugin/index.js"


def test_opencode_plugin_files_exist() -> None:
    plugin_js = Path("opencode-plugin/index.js")
    plugin_dts = Path("opencode-plugin/index.d.ts")

    assert plugin_js.exists()
    assert plugin_dts.exists()

    js_source = plugin_js.read_text(encoding="utf-8")
    assert "session.idle" in js_source
    assert "conversations.open" in js_source
    assert "chat.postMessage" in js_source
    assert "export default OpenCodeSlackNotifierPlugin" in js_source
    assert "OPENCODE_SLACK_ENV_FILE" in js_source
    assert '.config", "opencode", "slack-notifier.env' in js_source
