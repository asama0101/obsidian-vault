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
project:
tags:
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
        "--set", "due=2026-09-10", "--set", "project=[[A案件]]",
    )

    text = (vault / "Cabinet" / "Notes" / "見積書の作成.md").read_text(encoding="utf-8")
    assert "due: 2026-09-10" in text
    assert "project: [[A案件]]" in text


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


def test_project_option_creates_the_note_in_the_project_folder(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(
        vault, "--type", "task", "--title", "C9500 見積依頼",
        "--project", "大手町DC コアSW更改",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Cabinet/Notes/大手町DC コアSW更改/task/C9500 見積依頼.md"
    assert (
        vault / "Cabinet" / "Notes" / "大手町DC コアSW更改" / "task" / "C9500 見積依頼.md"
    ).is_file()


def test_meeting_with_project_creates_the_note_under_meeting_subfolder(tmp_path):
    vault = make_vault(tmp_path)
    meeting_templates = vault / "Cabinet" / "Templates"
    (meeting_templates / "meeting.md").write_text(TASK_TEMPLATE, encoding="utf-8")

    result = run_new_note(
        vault, "--type", "meeting", "--title", "定例会議",
        "--project", "大手町DC コアSW更改",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Cabinet/Notes/大手町DC コアSW更改/meeting/定例会議.md"
    assert (
        vault / "Cabinet" / "Notes" / "大手町DC コアSW更改" / "meeting" / "定例会議.md"
    ).is_file()


def test_project_type_creates_the_note_in_its_own_dated_folder(tmp_path):
    vault = make_vault(tmp_path)
    (vault / "Cabinet" / "Templates" / "project.md").write_text(TASK_TEMPLATE, encoding="utf-8")

    result = run_new_note(vault, "--type", "project", "--title", "新規案件")

    today = dt.date.today().isoformat()
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == f"Cabinet/Notes/{today}_新規案件/新規案件.md"
    assert (vault / "Cabinet" / "Notes" / f"{today}_新規案件" / "新規案件.md").is_file()


def test_project_type_uses_explicit_date_override_for_the_folder_name(tmp_path):
    vault = make_vault(tmp_path)
    (vault / "Cabinet" / "Templates" / "project.md").write_text(TASK_TEMPLATE, encoding="utf-8")

    result = run_new_note(
        vault, "--type", "project", "--title", "新規案件", "--set", "date=2020-01-01",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Cabinet/Notes/2020-01-01_新規案件/新規案件.md"
    assert (vault / "Cabinet" / "Notes" / "2020-01-01_新規案件" / "新規案件.md").is_file()


def test_project_folder_is_created_when_missing(tmp_path):
    vault = make_vault(tmp_path)
    assert not (vault / "Cabinet" / "Notes" / "新宿局 回線増設").exists()

    run_new_note(
        vault, "--type", "task", "--title", "構成図の修正", "--project", "新宿局 回線増設",
    )

    assert (vault / "Cabinet" / "Notes" / "新宿局 回線増設").is_dir()


def test_without_project_the_note_stays_directly_under_notes(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(vault, "--type", "task", "--title", "C9500後継機のEOSL確認")

    assert result.stdout.strip() == "Cabinet/Notes/C9500後継機のEOSL確認.md"


def test_know_how_with_project_still_stays_directly_under_notes(tmp_path):
    vault = make_vault(tmp_path)
    (vault / "Cabinet" / "Templates" / "know-how.md").write_text(TASK_TEMPLATE, encoding="utf-8")

    result = run_new_note(
        vault, "--type", "know-how", "--title", "BGPのルートリフレクタ設計", "--project", "A案件"
    )

    assert result.stdout.strip() == "Cabinet/Notes/BGPのルートリフレクタ設計.md"


def test_duplicate_title_in_the_same_project_returns_1(tmp_path):
    vault = make_vault(tmp_path)
    run_new_note(vault, "--type", "task", "--title", "見積依頼", "--project", "A案件")

    result = run_new_note(vault, "--type", "task", "--title", "見積依頼", "--project", "A案件")

    assert result.returncode == 1


def test_same_title_in_different_projects_is_allowed(tmp_path):
    vault = make_vault(tmp_path)
    run_new_note(vault, "--type", "task", "--title", "見積依頼", "--project", "A案件")

    result = run_new_note(vault, "--type", "task", "--title", "見積依頼", "--project", "B案件")

    assert result.returncode == 0, result.stderr
    assert (vault / "Cabinet" / "Notes" / "B案件" / "task" / "見積依頼.md").is_file()


def test_invalid_project_character_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(
        vault, "--type", "task", "--title", "見積依頼", "--project", "A社/案件",
    )

    assert result.returncode == 2
    assert not (vault / "Cabinet" / "Notes" / "A社").exists()


def test_project_parent_reference_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(
        vault, "--type", "task", "--title", "見積依頼", "--project", "..",
    )

    assert result.returncode == 2
    assert not (vault / "Cabinet" / "見積依頼.md").is_file()
    assert not any((vault / "Cabinet" / "Notes").rglob("見積依頼.md"))


def test_project_current_dir_reference_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(
        vault, "--type", "task", "--title", "見積依頼", "--project", ".",
    )

    assert result.returncode == 2
    assert not any((vault / "Cabinet" / "Notes").rglob("見積依頼.md"))


def test_blank_project_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(vault, "--type", "task", "--title", "見積依頼", "--project", "  ")

    assert result.returncode == 2
