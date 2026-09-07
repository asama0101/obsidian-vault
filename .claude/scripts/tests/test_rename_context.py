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


# --path モード（B-1: 空のcontextに後から値を付ける経路）


def test_path_mode_rewrites_multiple_notes(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A, "ノートC": NOTE_OTHER})

    result = run_rename(
        vault,
        "--path", "Cabinet/Notes/ノートA.md",
        "--path", "Cabinet/Notes/ノートC.md",
        "--new", "統合先",
    )

    assert result.returncode == 0, result.stderr
    text_a = (vault / "Cabinet" / "Notes" / "ノートA.md").read_text(encoding="utf-8")
    text_c = (vault / "Cabinet" / "Notes" / "ノートC.md").read_text(encoding="utf-8")
    assert "context: 統合先\n" in text_a
    assert "context: 統合先\n" in text_c
    changed = set(result.stdout.strip().splitlines())
    assert changed == {"Cabinet/Notes/ノートA.md", "Cabinet/Notes/ノートC.md"}


def test_old_and_path_are_mutually_exclusive(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})
    before = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()

    result = run_rename(
        vault, "--old", "A社案件", "--path", "Cabinet/Notes/ノートA.md", "--new", "A社",
    )

    assert result.returncode == 2
    after = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()
    assert before == after


def test_neither_old_nor_path_is_rejected(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})

    result = run_rename(vault, "--new", "A社")

    assert result.returncode == 2


def test_path_mode_rejects_nonexistent_path_without_writing(tmp_path):
    """有効パスを先、無効パスを後に置く。逐次書き込み実装なら1件目が書かれてしまうため、
    この順序でないと「1件も書き換えない」という部分適用防止の主張をテストが固定できない。"""
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})
    before = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()

    result = run_rename(
        vault,
        "--path", "Cabinet/Notes/ノートA.md",
        "--path", "Cabinet/Notes/存在しない.md",
        "--new", "A社",
    )

    assert result.returncode == 2
    after = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()
    assert before == after, "有効パス（1件目）が部分的に書き換えられている"


def test_path_mode_rejects_path_outside_notes_dir(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})
    outside = vault / "Cabinet" / "MEMORY.md"
    outside.write_text("---\ncontext: X\n---\n", encoding="utf-8")

    result = run_rename(vault, "--path", "Cabinet/MEMORY.md", "--new", "A社")

    assert result.returncode == 2
    assert outside.read_text(encoding="utf-8") == "---\ncontext: X\n---\n"


def test_path_mode_dry_run_does_not_write(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})
    before = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()

    result = run_rename(
        vault, "--path", "Cabinet/Notes/ノートA.md", "--new", "A社", "--dry-run",
    )

    assert result.returncode == 0, result.stderr
    after = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()
    assert before == after
    assert result.stdout.strip() == "Cabinet/Notes/ノートA.md"


# C: 軽微な修正


def test_missing_notes_dir_reports_reason_on_stderr(tmp_path):
    result = run_rename(tmp_path, "--old", "A社案件", "--new", "A社")

    assert result.returncode == 1
    assert result.stderr.strip() != ""


def test_no_match_reports_reason_on_stderr(tmp_path):
    vault = make_vault(tmp_path, {"ノートC": NOTE_OTHER})

    result = run_rename(vault, "--old", "存在しない値", "--new", "何か")

    assert result.returncode == 1
    assert "存在しない値" in result.stderr


def test_new_value_with_colon_is_rejected(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})
    before = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()

    result = run_rename(vault, "--old", "A社案件", "--new", "A社: 本店")

    assert result.returncode == 2
    after = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()
    assert before == after


def test_new_value_with_hash_is_rejected(tmp_path):
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})
    before = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()

    result = run_rename(vault, "--old", "A社案件", "--new", "A社 #タグ")

    assert result.returncode == 2
    after = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()
    assert before == after


UNTERMINATED_NOTE = """---
type: task
date: 2026-09-04
status: 1_todo

## 完了条件

context: A社案件
"""


def test_unterminated_frontmatter_is_not_touched(tmp_path):
    """閉じの `---` が無い場合はfrontmatter無しとみなし、本文中のcontext:行に誤爆しない。"""
    vault = make_vault(tmp_path, {"ノートD": UNTERMINATED_NOTE})
    before = (vault / "Cabinet" / "Notes" / "ノートD.md").read_bytes()

    result = run_rename(vault, "--old", "A社案件", "--new", "A社")

    assert result.returncode == 1
    after = (vault / "Cabinet" / "Notes" / "ノートD.md").read_bytes()
    assert before == after


NOTE_WITH_BODY_CONTEXT_LINE = """---
type: task
date: 2026-09-05
status: 1_todo
context: A社案件
---

## 作業ログ

context: 本文中のこの行は書き換えない
"""


def test_body_context_line_is_not_rewritten(tmp_path):
    """frontmatterが正しく閉じていれば、本文中の `context:` 行には触れない。"""
    vault = make_vault(tmp_path, {"ノートE": NOTE_WITH_BODY_CONTEXT_LINE})

    result = run_rename(vault, "--old", "A社案件", "--new", "A社")

    assert result.returncode == 0, result.stderr
    text = (vault / "Cabinet" / "Notes" / "ノートE.md").read_text(encoding="utf-8")
    assert "context: A社\n" in text
    assert "context: 本文中のこの行は書き換えない" in text


def test_path_mode_deduplicates_same_path(tmp_path):
    """同じパスを2回指定しても、書き込み・出力とも1回だけになる。"""
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})

    result = run_rename(
        vault,
        "--path", "Cabinet/Notes/ノートA.md",
        "--path", "Cabinet/Notes/ノートA.md",
        "--new", "A社",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip().splitlines() == ["Cabinet/Notes/ノートA.md"]


def test_path_mode_rejects_note_without_context_field(tmp_path):
    """`--path` 先のfrontmatterに `context` 行が無ければ1件も書き換えない。"""
    vault = make_vault(tmp_path, {"ノートA": NOTE_A})
    no_context_note = vault / "Cabinet" / "Notes" / "contextなし.md"
    no_context_note.write_text("---\ntype: task\ndate: 2026-09-06\n---\n\n## 完了条件\n", encoding="utf-8")
    before_a = (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes()
    before_no_context = no_context_note.read_bytes()

    result = run_rename(
        vault,
        "--path", "Cabinet/Notes/ノートA.md",
        "--path", "Cabinet/Notes/contextなし.md",
        "--new", "A社",
    )

    assert result.returncode == 2
    assert (vault / "Cabinet" / "Notes" / "ノートA.md").read_bytes() == before_a
    assert no_context_note.read_bytes() == before_no_context
