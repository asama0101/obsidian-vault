"""テンプレート5本と new_note.py の結合テスト。

vault本体のテンプレートを一時vaultへコピーして検証するため、本体は書き換えない。
"""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

VAULT = Path(__file__).resolve().parents[3]
NEW_NOTE = VAULT / ".claude" / "scripts" / "new_note.py"

EXPECTED_KEYS = {
    "task": ["type", "date", "status", "due", "done", "project", "tags", "blocked_by"],
    "project": ["type", "date", "status", "due", "tags"],
    "meeting": [
        "type", "date", "status", "project",
        "calendar_event_id", "calendar_series_id",
    ],
    "know-how": ["type", "date", "tags"],
}

EXPECTED_HEADINGS = {
    "task": ["## 完了条件", "## 作業ログ"],
    "project": ["## 概要", "## ステークホルダ", "## マイルストーン", "## メモ", "## ドキュメント", "## 関連"],
    "meeting": ["## 会議情報", "## 議題", "## 資料", "## メモ", "## 決定事項", "## アクション"],
    "know-how": ["## 状況", "## 手順", "## 注意点"],
}


def frontmatter_keys(text: str) -> list[str]:
    """先頭のfrontmatterのキーを出現順に返す。"""
    lines = text.split("\n")
    assert lines[0].strip() == "---", "frontmatterで始まっていません"
    keys = []
    for line in lines[1:]:
        if line.strip() == "---":
            return keys
        if ":" in line:
            keys.append(line.partition(":")[0].strip())
    pytest.fail("frontmatterが閉じていません")


@pytest.fixture
def vault(tmp_path):
    """vault本体のテンプレートをコピーした一時vaultを作る。"""
    shutil.copytree(VAULT / "6_Cabinet" / "Templates", tmp_path / "6_Cabinet" / "Templates")
    return tmp_path


@pytest.mark.parametrize("note_type", sorted(EXPECTED_KEYS))
def test_frontmatter_keys_match_the_spec(note_type):
    text = (VAULT / "6_Cabinet" / "Templates" / f"{note_type}.md").read_text(encoding="utf-8")

    assert frontmatter_keys(text) == EXPECTED_KEYS[note_type]


@pytest.mark.parametrize("note_type", sorted(EXPECTED_HEADINGS))
def test_headings_match_the_spec(note_type):
    text = (VAULT / "6_Cabinet" / "Templates" / f"{note_type}.md").read_text(encoding="utf-8")

    assert [line for line in text.split("\n") if line.startswith("## ")] == EXPECTED_HEADINGS[note_type]


def test_today_template_has_the_four_sections():
    text = (VAULT / "6_Cabinet" / "Templates" / "today.md").read_text(encoding="utf-8")

    assert frontmatter_keys(text) == ["date"]
    assert [line for line in text.split("\n") if line.startswith("## ")] == [
        "## 今日の予定",
        "## 今日のタスク",
        "## Claudeからの連絡",
        "## メモ",
    ]


@pytest.mark.parametrize("note_type", sorted(EXPECTED_KEYS))
def test_new_note_can_generate_every_type(vault, note_type):
    result = subprocess.run(
        [
            sys.executable, str(NEW_NOTE),
            "--vault-root", str(vault),
            "--type", note_type,
            "--title", f"検証用{note_type}",
        ],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    title = f"検証用{note_type}"
    created_path = result.stdout.strip()
    if note_type == "project":
        assert created_path == f"{title}.md"
    elif note_type == "know-how":
        assert created_path == f"2_know-how/{title}.md"
    else:
        assert created_path == f"3_Inbox/{title}.md"
    created = vault / created_path
    assert f"type: {note_type}" in created.read_text(encoding="utf-8")


def test_task_status_defaults_to_todo():
    text = (VAULT / "6_Cabinet" / "Templates" / "task.md").read_text(encoding="utf-8")

    assert "status: 1_todo" in text


def test_meeting_status_defaults_to_scheduled():
    text = (VAULT / "6_Cabinet" / "Templates" / "meeting.md").read_text(encoding="utf-8")

    assert "status: 1_予定" in text


@pytest.mark.parametrize("note_type", sorted(EXPECTED_KEYS))
def test_no_template_has_a_context_property(note_type):
    text = (VAULT / "6_Cabinet" / "Templates" / f"{note_type}.md").read_text(encoding="utf-8")

    assert "context" not in text
