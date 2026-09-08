"""index.py のテスト。vault本体は触らず tmp_path 上に一時vaultを作る。"""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "index.py"
COLUMN_COUNT = 10
COLUMN_COUNT_WITH_CALENDAR_IDS = 12


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
        "---\ntype: task\nstatus: 1_todo\ndue: 2026-09-10\n"
        "done: \ntags: [種別/更改]\nproject: \"[[大手町DC コアSW更改]]\"\n"
        "date: 2026-09-07\n---\n\n## 完了条件\n",
    )

    row = rows(run_index(tmp_path))[0]

    assert len(row) == COLUMN_COUNT
    assert row[0] == "Cabinet/Notes/見積書の作成.md"
    assert row[1] == "task"
    assert row[2] == "1_todo"
    assert row[3] == "2026-09-10"
    assert row[4] == ""
    assert row[5] == "種別/更改"
    assert row[6] == "[[大手町DC コアSW更改]]"
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
    write_note(tmp_path, "引用付き.md", "---\ntype: \"task\"\nproject: '[[A案件]]'\n---\n")

    row = rows(run_index(tmp_path))[0]

    assert row[1] == "task"
    assert row[6] == "[[A案件]]"


def test_tab_in_value_is_sanitized(tmp_path):
    write_note(tmp_path, "タブ入り.md", "---\ntype: task\nproject: A案件\tB案件\n---\n")

    row = rows(run_index(tmp_path))[0]

    assert len(row) == COLUMN_COUNT
    assert row[6] == "A案件 B案件"


def test_missing_notes_dir_outputs_nothing(tmp_path):
    assert run_index(tmp_path) == ""


def test_invalid_utf8_note_does_not_break_the_index(tmp_path):
    write_note(tmp_path, "正常なノート.md", "---\ntype: task\n---\n")
    notes = tmp_path / "Cabinet" / "Notes"
    (notes / "壊れたノート.md").write_bytes(b"---\ntype: task\ntags: [\xff\xfe]\n---\n")

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


def test_date_matches_only_the_exact_date(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: meeting\ndate: 2026-09-07\n---\n")

    result = rows(run_index(tmp_path, "--date", "2026-09-07"))

    assert [row[8] for row in result] == ["A"]


def test_date_excludes_other_dates(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: meeting\ndate: 2026-09-06\n---\n")

    assert run_index(tmp_path, "--date", "2026-09-07") == ""


def test_date_excludes_notes_without_date(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: meeting\ndate:\n---\n")

    assert run_index(tmp_path, "--date", "2026-09-07") == ""


def test_date_combines_with_type_as_and(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: meeting\ndate: 2026-09-07\n---\n")
    write_note(tmp_path, "B.md", "---\ntype: task\ndate: 2026-09-07\n---\n")

    result = rows(run_index(tmp_path, "--type", "meeting", "--date", "2026-09-07"))

    assert [row[8] for row in result] == ["A"]


def test_updated_on_matches_the_date_part_of_mtime(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\n---\n")
    today = __import__("datetime").date.today().isoformat()

    result = rows(run_index(tmp_path, "--updated-on", today))

    assert [row[8] for row in result] == ["A"]


def test_updated_on_excludes_other_dates(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\n---\n")

    assert run_index(tmp_path, "--updated-on", "1999-01-01") == ""


def write_note_in(vault: Path, folder: str, name: str, body: str) -> Path:
    """一時vaultの Cabinet/Notes/<folder>/ にノートを1件置く。"""
    notes = vault / "Cabinet" / "Notes" / folder
    notes.mkdir(parents=True, exist_ok=True)
    path = notes / name
    path.write_text(body, encoding="utf-8")
    return path


def test_notes_in_subfolders_are_listed(tmp_path):
    write_note_in(tmp_path, "大手町DC コアSW更改", "C9500 見積依頼.md", "---\ntype: task\n---\n")

    result = rows(run_index(tmp_path))

    assert len(result) == 1
    assert result[0][1] == "task"


def test_notes_directly_under_notes_dir_are_still_listed(tmp_path):
    write_note(tmp_path, "BGPのルートリフレクタ設計.md", "---\ntype: know-how\n---\n")
    write_note_in(tmp_path, "大手町DC コアSW更改", "C9500 見積依頼.md", "---\ntype: task\n---\n")

    result = rows(run_index(tmp_path))

    assert sorted(row[1] for row in result) == ["know-how", "task"]


def test_path_column_includes_the_project_folder(tmp_path):
    write_note_in(tmp_path, "大手町DC コアSW更改", "C9500 見積依頼.md", "---\ntype: task\n---\n")

    result = rows(run_index(tmp_path))

    assert result[0][0] == "Cabinet/Notes/大手町DC コアSW更改/C9500 見積依頼.md"


def test_tags_inline_list_is_joined_with_commas(tmp_path):
    write_note(tmp_path, "案件.md", "---\ntype: project\ntags: [種別/更改, メーカー/Cisco]\n---\n")

    row = rows(run_index(tmp_path))[0]

    assert row[5] == "種別/更改,メーカー/Cisco"


def test_tags_block_list_is_joined_with_commas(tmp_path):
    write_note(
        tmp_path,
        "ノウハウ.md",
        "---\ntype: know-how\ntags:\n  - 領域/ルーティング\n  - メーカー/Cisco\ndate: 2026-06-14\n---\n",
    )

    row = rows(run_index(tmp_path))[0]

    assert row[5] == "領域/ルーティング,メーカー/Cisco"
    assert row[7] == "2026-06-14"


def test_project_link_is_kept_as_is(tmp_path):
    write_note(tmp_path, "タスク.md", "---\ntype: task\nproject: \"[[大手町DC コアSW更改]]\"\n---\n")

    row = rows(run_index(tmp_path))[0]

    assert row[6] == "[[大手町DC コアSW更改]]"


def test_project_list_is_joined_with_commas(tmp_path):
    write_note(tmp_path, "合同会議.md", "---\ntype: meeting\nproject: [\"[[A案件]]\", \"[[B案件]]\"]\n---\n")

    row = rows(run_index(tmp_path))[0]

    assert row[6] == "[[A案件]],[[B案件]]"


def test_unquoted_wikilink_is_not_parsed_as_a_list(tmp_path):
    write_note(tmp_path, "タスク.md", "---\ntype: task\nproject: [[A案件]]\n---\n")

    row = rows(run_index(tmp_path))[0]

    assert row[6] == "[[A案件]]"


def test_calendar_ids_are_absent_from_the_default_columns(tmp_path):
    write_note(
        tmp_path,
        "定例.md",
        "---\ntype: meeting\ncalendar_event_id: evt-123\ncalendar_series_id: series-456\n---\n",
    )

    row = rows(run_index(tmp_path))[0]

    assert len(row) == COLUMN_COUNT
    assert "evt-123" not in row


def test_with_calendar_ids_appends_the_two_columns(tmp_path):
    write_note(
        tmp_path,
        "定例.md",
        "---\ntype: meeting\ncalendar_event_id: evt-123\ncalendar_series_id: series-456\n---\n",
    )

    row = rows(run_index(tmp_path, "--with-calendar-ids"))[0]

    assert len(row) == COLUMN_COUNT_WITH_CALENDAR_IDS
    assert row[10] == "evt-123"
    assert row[11] == "series-456"


def test_done_task_is_excluded_by_default(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 4_done\n---\n")

    assert run_index(tmp_path) == ""


def test_cancelled_task_is_excluded_by_default(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 5_cancelled\n---\n")

    assert run_index(tmp_path) == ""


def test_done_project_is_excluded_by_default(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: project\nstatus: 2_done\n---\n")

    assert run_index(tmp_path) == ""


def test_active_notes_are_kept_by_default(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 1_todo\n---\n")
    write_note(tmp_path, "B.md", "---\ntype: project\nstatus: 1_active\n---\n")
    write_note(tmp_path, "C.md", "---\ntype: meeting\nstatus: 2_実施済\n---\n")

    result = rows(run_index(tmp_path))

    assert sorted(row[8] for row in result) == ["A", "B", "C"]


def test_all_option_includes_completed_notes(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 4_done\n---\n")
    write_note(tmp_path, "B.md", "---\ntype: task\nstatus: 1_todo\n---\n")

    result = rows(run_index(tmp_path, "--all"))

    assert sorted(row[8] for row in result) == ["A", "B"]


def test_explicit_status_disables_the_default_exclusion(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 4_done\n---\n")

    result = rows(run_index(tmp_path, "--status", "4_done"))

    assert [row[8] for row in result] == ["A"]


def test_due_before_includes_the_boundary_date(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 1_todo\ndue: 2026-09-07\n---\n")

    result = rows(run_index(tmp_path, "--due-before", "2026-09-07"))

    assert [row[8] for row in result] == ["A"]


def test_due_before_excludes_later_and_empty_due(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 1_todo\ndue: 2026-09-08\n---\n")
    write_note(tmp_path, "B.md", "---\ntype: task\nstatus: 1_todo\ndue:\n---\n")

    assert run_index(tmp_path, "--due-before", "2026-09-07") == ""


def test_due_before_combines_with_type_as_and(tmp_path):
    write_note(tmp_path, "A.md", "---\ntype: task\nstatus: 1_todo\ndue: 2026-09-01\n---\n")
    write_note(tmp_path, "B.md", "---\ntype: project\nstatus: 1_active\ndue: 2026-09-01\n---\n")

    result = rows(run_index(tmp_path, "--type", "task", "--due-before", "2026-09-07"))

    assert [row[8] for row in result] == ["A"]
