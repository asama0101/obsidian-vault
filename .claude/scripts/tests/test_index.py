"""index.py のテスト。vault本体は触らず tmp_path 上に一時vaultを作る。"""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "index.py"
COLUMN_COUNT = 10


def write_note(vault: Path, name: str, body: str) -> Path:
    """一時vaultの Cabinet/Notes/ にノートを1件置く。"""
    notes = vault / "Cabinet" / "Notes"
    notes.mkdir(parents=True, exist_ok=True)
    path = notes / name
    path.write_text(body, encoding="utf-8")
    return path


def run_index(vault: Path, *args: str) -> str:
    """index.py を実行して標準出力を返す。"""
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--vault-root", str(vault), *args],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def rows(output: str) -> list[list[str]]:
    """TSV出力を列のリストに分解する。"""
    return [line.split("\t") for line in output.splitlines()]


def test_outputs_one_row_per_note(tmp_path):
    write_note(tmp_path, "見積書の作成.md", "---\ntype: task\nstatus: 1_todo\n---\n\n## 完了条件\n")
    write_note(tmp_path, "環境構築.md", "---\ntype: task\nstatus: 2_doing\n---\n\n## 完了条件\n")

    result = rows(run_index(tmp_path))

    assert len(result) == 2
    assert all(len(row) == COLUMN_COUNT for row in result)


def test_columns_are_in_fixed_order(tmp_path):
    write_note(
        tmp_path,
        "見積書の作成.md",
        "---\ntype: task\nstatus: 1_todo\ndue: 2026-09-10\ncheck: 2026-09-08\n"
        "done: \ncontext: A社\ndate: 2026-09-07\n---\n\n## 完了条件\n",
    )

    row = rows(run_index(tmp_path))[0]

    assert row[0] == "Cabinet/Notes/見積書の作成.md"
    assert row[1] == "task"
    assert row[2] == "1_todo"
    assert row[3] == "2026-09-10"
    assert row[4] == "2026-09-08"
    assert row[5] == ""
    assert row[6] == "A社"
    assert row[7] == "2026-09-07"
    assert row[8] == "見積書の作成"
    assert row[9].startswith("20")


def test_empty_property_becomes_empty_string(tmp_path):
    write_note(tmp_path, "環境構築.md", "---\ntype: task\ndue:\n---\n\n## 完了条件\n")

    row = rows(run_index(tmp_path))[0]

    assert row[3] == ""


def test_note_without_frontmatter_is_still_listed(tmp_path):
    write_note(tmp_path, "メモ書き.md", "## 見出しだけのノート\n")

    result = rows(run_index(tmp_path))

    assert len(result) == 1
    assert result[0][1] == ""
    assert result[0][8] == "メモ書き"


def test_unclosed_frontmatter_is_treated_as_absent(tmp_path):
    write_note(tmp_path, "壊れたノート.md", "---\ntype: task\nstatus: 1_todo\n")

    row = rows(run_index(tmp_path))[0]

    assert row[1] == ""


def test_quoted_values_are_unquoted(tmp_path):
    write_note(tmp_path, "引用付き.md", '---\ntype: "task"\ncontext: \'A社\'\n---\n')

    row = rows(run_index(tmp_path))[0]

    assert row[1] == "task"
    assert row[6] == "A社"


def test_tab_in_value_is_sanitized(tmp_path):
    write_note(tmp_path, "タブ入り.md", "---\ntype: task\ncontext: A社\tB社\n---\n")

    row = rows(run_index(tmp_path))[0]

    assert len(row) == COLUMN_COUNT
    assert row[6] == "A社 B社"


def test_missing_notes_dir_outputs_nothing(tmp_path):
    assert run_index(tmp_path) == ""


def test_invalid_utf8_note_does_not_break_the_index(tmp_path):
    write_note(tmp_path, "正常なノート.md", "---\ntype: task\n---\n")
    notes = tmp_path / "Cabinet" / "Notes"
    (notes / "壊れたノート.md").write_bytes(b"---\ntype: task\ncontext: \xff\xfe\n---\n")

    result = rows(run_index(tmp_path))

    assert len(result) == 2
    assert result[0][1] == "task"


def test_default_vault_root_points_at_the_vault():
    import importlib.util

    spec = importlib.util.spec_from_file_location("index", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert (module.default_vault_root() / "Cabinet" / "Templates").is_dir()


def test_filter_by_type(tmp_path):
    write_note(tmp_path, "見積書の作成.md", "---\ntype: task\n---\n")
    write_note(tmp_path, "定例.md", "---\ntype: meeting\n---\n")

    result = rows(run_index(tmp_path, "--type", "task"))

    assert len(result) == 1
    assert result[0][8] == "見積書の作成"


def test_status_accepts_comma_separated_values_as_or(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 1_todo\n---\n")
    write_note(tmp_path, "B.md", "---\ntype: task\nstatus: 2_doing\n---\n")
    write_note(tmp_path, "C.md", "---\ntype: task\nstatus: 4_done\n---\n")

    result = rows(run_index(tmp_path, "--status", "1_todo,2_doing"))

    assert sorted(row[8] for row in result) == ["A", "B"]


def test_type_and_status_combine_as_and(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 1_todo\n---\n")
    write_note(tmp_path, "B.md", "---\ntype: project\nstatus: 1_todo\n---\n")

    result = rows(run_index(tmp_path, "--type", "task", "--status", "1_todo"))

    assert [row[8] for row in result] == ["A"]


def test_due_before_includes_the_boundary_date(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\ndue: 2026-09-07\n---\n")
    write_note(tmp_path, "B.md", "---\ntype: task\ndue: 2026-09-08\n---\n")

    result = rows(run_index(tmp_path, "--due-before", "2026-09-07"))

    assert [row[8] for row in result] == ["A"]


def test_due_before_excludes_notes_without_due(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\ndue:\n---\n")

    assert run_index(tmp_path, "--due-before", "2026-12-31") == ""


def test_updated_on_matches_the_date_part_of_mtime(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\n---\n")
    today = __import__("datetime").date.today().isoformat()

    result = rows(run_index(tmp_path, "--updated-on", today))

    assert [row[8] for row in result] == ["A"]


def test_updated_on_excludes_other_dates(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\n---\n")

    assert run_index(tmp_path, "--updated-on", "1999-01-01") == ""


def test_contexts_lists_unique_values_sorted(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\ncontext: B社\n---\n")
    write_note(tmp_path, "B.md", "---\ntype: task\ncontext: A社\n---\n")
    write_note(tmp_path, "C.md", "---\ntype: task\ncontext: A社\n---\n")
    write_note(tmp_path, "D.md", "---\ntype: task\ncontext:\n---\n")

    output = run_index(tmp_path, "--contexts")

    assert output.splitlines() == ["A社", "B社"]
