"""rename_context.py のテスト。vault本体は触らず tmp_path 上に一時vaultを作る。"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "rename_context.py"

NOTE_A = """---
type: task
date: 2026-09-01
status: 1_todo
due: 2026-09-10
done:
context: A社案件
---

## 完了条件

条件A

## 作業ログ

- 2026-09-01: 作成
"""

NOTE_B = """---
type: project
date: 2026-09-02
status: 1_active
context: A社案件
---

## 概要

案件Bの概要
"""

NOTE_OTHER = """---
type: task
date: 2026-09-03
status: 2_doing
due:
done:
context: B社
---

## 完了条件

条件C
"""


def make_vault(tmp_path: Path, notes: dict[str, str]) -> Path:
    """指定したノート内容で一時vaultを作る。"""
    notes_dir = tmp_path / "Cabinet" / "Notes"
    notes_dir.mkdir(parents=True)
    for title, text in notes.items():
        (notes_dir / f"{title}.md").write_text(text, encoding="utf-8")
    return tmp_path


def run_rename(vault: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--vault-root", str(vault), *args],
        capture_output=True,
        text=True,
    )


def test_all_matching_notes_are_rewritten(tmp_path):
    vault = make_vault(
        tmp_path,
        {"ノートA": NOTE_A, "ノートB": NOTE_B, "ノートC": NOTE_OTHER},
    )

    result = run_rename(vault, "--old", "A社案件", "--new", "A社")

    assert result.returncode == 0, result.stderr
    text_a = (vault / "Cabinet" / "Notes" / "ノートA.md").read_text(encoding="utf-8")
    text_b = (vault / "Cabinet" / "Notes" / "ノートB.md").read_text(encoding="utf-8")
    assert "context: A社\n" in text_a
    assert "context: A社\n" in text_b
    changed = set(result.stdout.strip().splitlines())
    assert changed == {"Cabinet/Notes/ノートA.md", "Cabinet/Notes/ノートB.md"}


def test_non_matching_note_is_byte_identical(tmp_path):
    vault = make_vault(
        tmp_path,
        {"ノートA": NOTE_A, "ノートC": NOTE_OTHER},
    )
    before = (vault / "Cabinet" / "Notes" / "ノートC.md").read_bytes()

    run_rename(vault, "--old", "A社案件", "--new", "A社")

    after = (vault / "Cabinet" / "Notes" / "ノートC.md").read_bytes()
    assert before == after


def test_no_match_returns_exit_code_1_and_writes_nothing(tmp_path):
    vault = make_vault(tmp_path, {"ノートC": NOTE_OTHER})
    before = (vault / "Cabinet" / "Notes" / "ノートC.md").read_bytes()

    result = run_rename(vault, "--old", "存在しない値", "--new", "何か")

    assert result.returncode == 1
    after = (vault / "Cabinet" / "Notes" / "ノートC.md").read_bytes()
    assert before == after


def test_dry_run_does_not_write(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})
    before = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()

    result = run_rename(vault, "--old", "A社案件", "--new", "A社", "--dry-run")

    assert result.returncode == 0, result.stderr
    after = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()
    assert before == after
    assert result.stdout.strip() == "Cabinet/Notes/ノートA.md"


def test_new_empty_string_clears_context(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})

    result = run_rename(vault, "--old", "A社案件", "--new", "")

    assert result.returncode == 0, result.stderr
    text = (vault / "Cabinet" / "Notes" / "ノートA.md").read_text(encoding="utf-8")
    assert "context:\n" in text


def test_old_empty_string_is_rejected(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})
    before = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()

    result = run_rename(vault, "--old", "", "--new", "何か")

    assert result.returncode == 2
    after = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()
    assert before == after


def test_other_lines_and_property_order_are_preserved(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})

    run_rename(vault, "--old", "A社案件", "--new", "A社")

    text = (vault / "Cabinet" / "Notes" / "ノートA.md").read_text(encoding="utf-8")
    lines = text.split("\n")
    expected = NOTE_A.split("\n")
    for original_line, new_line in zip(expected, lines):
        if original_line.startswith("context:"):
            assert new_line == "context: A社"
        else:
            assert new_line == original_line
    assert len(lines) == len(expected)
