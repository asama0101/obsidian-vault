"""new_note.py のテスト。vault本体は触らず tmp_path 上に一時vaultを作る。"""
import datetime as dt
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "new_note.py"

TASK_TEMPLATE = """---
type: task
date:
status: 1_todo
due:
done:
context:
---

## 完了条件

## 作業ログ
"""


def make_vault(tmp_path: Path) -> Path:
    """テンプレートとNotesディレクトリだけを持つ一時vaultを作る。"""
    templates = tmp_path / "Cabinet" / "Templates"
    templates.mkdir(parents=True)
    (templates / "task.md").write_text(TASK_TEMPLATE, encoding="utf-8")
    (tmp_path / "Cabinet" / "Notes").mkdir()
    return tmp_path


def run_new_note(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--vault-root", str(vault), *args],
        capture_output=True,
        text=True,
    )


def test_creates_note_from_template(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(vault, "--type", "task", "--title", "見積書の作成")

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Cabinet/Notes/見積書の作成.md"
    created = vault / "Cabinet" / "Notes" / "見積書の作成.md"
    assert created.is_file()
    assert "## 完了条件" in created.read_text(encoding="utf-8")


def test_fills_date_with_today(tmp_path):
    vault = make_vault(tmp_path)

    run_new_note(vault, "--type", "task", "--title", "見積書の作成")

    text = (vault / "Cabinet" / "Notes" / "見積書の作成.md").read_text(encoding="utf-8")
    assert f"date: {dt.date.today().isoformat()}" in text


def test_set_overrides_a_property(tmp_path):
    vault = make_vault(tmp_path)

    run_new_note(
        vault, "--type", "task", "--title", "見積書の作成",
        "--set", "due=2026-09-10", "--set", "context=A社",
    )

    text = (vault / "Cabinet" / "Notes" / "見積書の作成.md").read_text(encoding="utf-8")
    assert "due: 2026-09-10" in text
    assert "context: A社" in text


def test_duplicate_title_fails_without_touching_the_existing_note(tmp_path):
    vault = make_vault(tmp_path)
    existing = vault / "Cabinet" / "Notes" / "見積書の作成.md"
    existing.write_text("元の中身\n", encoding="utf-8")

    result = run_new_note(vault, "--type", "task", "--title", "見積書の作成")

    assert result.returncode == 1
    assert existing.read_text(encoding="utf-8") == "元の中身\n"


def test_unknown_property_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(
        vault, "--type", "task", "--title", "見積書の作成", "--set", "priority=high"
    )

    assert result.returncode == 2
    assert "priority" in result.stderr
    assert not (vault / "Cabinet" / "Notes" / "見積書の作成.md").exists()


def test_invalid_title_character_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(vault, "--type", "task", "--title", "A社/見積書")

    assert result.returncode == 2


def test_set_without_equals_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(
        vault, "--type", "task", "--title", "見積書の作成", "--set", "due"
    )

    assert result.returncode == 2


def test_missing_template_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(vault, "--type", "project", "--title", "新規案件")

    assert result.returncode == 2
