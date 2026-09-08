# Obsidian秘書vault 再設計 実装計画

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 人間との接点を `Today.md` 1枚に、判断基準を `secretary` スキル1か所に、vaultの読み取りを索引スクリプト1本に集約した秘書システムを構築する。

**Architecture:** 機械的処理を `.claude/scripts/` の3スクリプトに落とし、判断を伴う処理だけを `secretary` スキルに残す。ループは `index.py` を1回叩いて `Today.md` を冪等に再生成する。ノートは `Cabinet/Notes/` にフラット格納し、`type` プロパティで4種を判別する。

**Tech Stack:** Python 3.12（標準ライブラリのみ）、bash、pytest 9.0.3（システム導入済み）、PyYAML 6.0.1（`.base` 検証にのみ使用）、Obsidian Bases、Claude Code Skills / Commands / MCP。

**Spec:** `.claude/specs/2026-09-07-vault-secretary-redesign-design.md`

## Global Constraints

- 応答・docstring・コメントは日本語で書く。コード・変数・シンボルは英語で書く。
- Markdown文書は固定文字数でのハードラップを禁止する。1文または1箇条書き項目は1行で書く。
- ノートを新規作成・編集する前に、日次ブランチ `daily/YYYY-MM-DD` にいることを確認する。ただし本計画の実装作業は `redesign/vault-secretary` ブランチ上で行う。
- 新規パッケージのインストールは行わない。Python は標準ライブラリのみを使う（PyYAML は `.base` の構文検証にのみ使い、スクリプト本体からは import しない）。
- `Cabinet/Notes/` はサブフォルダを作らずフラットに保つ。
- `status` の値域は task が `1_todo`/`2_doing`/`3_pending`/`4_done`/`5_cancelled`、project が `1_active`/`2_done`、meeting が `1_予定`/`2_実施済`/`3_中止`/`4_不参加`。
- スクリプトの終了コードは 0=成功、1=実行時エラー（既存ファイル・マージ失敗等）、2=入力エラー（不正な引数・不正なノート名等）に統一する。
- テストは `python3 -m pytest` で実行する。テストは vault 本体を書き換えず、必ず `tmp_path` 上に一時vaultを構築して行う。

---

## File Structure

| ファイル | 責務 |
|---|---|
| `.claude/scripts/index.py` | `Cabinet/Notes/` のfrontmatterをTSV索引化する。vaultを読む唯一の経路 |
| `.claude/scripts/new_note.py` | テンプレートからノートを1件作る |
| `.claude/scripts/close_day.sh` | 締めの機械的部分（Diary退避・コミット・ffマージ・push） |
| `.claude/scripts/tests/test_index.py` | `index.py` のテスト |
| `.claude/scripts/tests/test_new_note.py` | `new_note.py` のテスト |
| `.claude/scripts/tests/test_close_day.py` | `close_day.sh` のテスト |
| `.claude/scripts/tests/test_templates.py` | テンプレート5本と `new_note.py` の結合テスト |
| `.claude/scripts/tests/test_bases.py` | `.base` 4本の構文検証 |
| `Cabinet/Templates/{today,task,project,meeting,know-how}.md` | ノートの最小骨 |
| `Cabinet/Bases/{プロジェクト,タスク,議事録,ノウハウ}.base` | 人間の閲覧専用ビュー |
| `.claude/skills/secretary/SKILL.md` | 判断を伴う全処理。分類基準の唯一の定義箇所 |
| `.claude/commands/{today,intake,close}.md` | 薄い入口 |
| `.claude/settings.local.json` | MCPツールとスクリプトの事前許可 |
| `.claude/CLAUDE.md` | vaultの取扱説明書 |
| `README.md` | 人間向けの概要 |

---

## Task 1: 整地とフォルダ骨格

**Files:**
- Delete: `Inbox/`, `Review/`, `20_Diary/`, `Inbox.base`, `Review.base`, `Cabinet/Templates/inbox.md`, `Cabinet/Templates/review.md`, `.obsidian/daily-notes.json`
- Move: `Cabinet/Documents/` → `Documents/`, `{タスク,プロジェクト,議事録,ノウハウ}.base` → `Cabinet/Bases/`
- Create: `.claude/scripts/tests/`, `.claude/commands/`

**Interfaces:**
- Consumes: なし（最初のタスク）
- Produces: 後続タスクが書き込む先のディレクトリ構造

削除対象はすべてgit追跡下にあるため、誤って消しても `git show HEAD~1:<path>` で復元できる。`20_Diary/2026-09-02.md` はvault内で唯一の実ノートだが、内部リンク4本すべてが削除済みパスを指す旧構成の残骸であり、設計書10章で破棄対象と決定済み。

- [ ] **Step 1: 現状のツリーを記録する**

```bash
cd /home/asama/obsidian-vault
git status --short
find . -path ./.git -prune -o -type f -print | grep -v '^./.obsidian/' | sort > /tmp/tree-before.txt
wc -l /tmp/tree-before.txt
```

- [ ] **Step 2: 旧ゾーンとテンプレートを削除する**

```bash
cd /home/asama/obsidian-vault
git rm -r -q Inbox Review 20_Diary
git rm -q Inbox.base Review.base
git rm -q Cabinet/Templates/inbox.md Cabinet/Templates/review.md
rm -f .obsidian/daily-notes.json
```

`.obsidian/daily-notes.json` は削除済みの `20_Diary` と `92_Template/daily.md` を参照する壊れた設定。`.obsidian/` の大半はgit追跡外のため `git rm` ではなく `rm` を使う。

- [ ] **Step 3: `Documents/` をvault直下へ移動する**

```bash
cd /home/asama/obsidian-vault
mkdir -p Documents
git mv Cabinet/Documents/.gitkeep Documents/.gitkeep
rmdir Cabinet/Documents
```

- [ ] **Step 4: `.base` を `Cabinet/Bases/` へ移動する**

```bash
cd /home/asama/obsidian-vault
mkdir -p Cabinet/Bases
git mv タスク.base プロジェクト.base 議事録.base ノウハウ.base Cabinet/Bases/
```

- [ ] **Step 5: 新規ディレクトリを作る**

```bash
cd /home/asama/obsidian-vault
mkdir -p .claude/scripts/tests .claude/commands
touch .claude/scripts/tests/.gitkeep .claude/commands/.gitkeep
```

- [ ] **Step 6: 構造を検証する**

```bash
cd /home/asama/obsidian-vault
ls -a . | grep -vE '^(\.|\.\.|\.git|\.obsidian|\.gitignore|desktop\.ini)$'
ls Cabinet
```

Expected: vault直下は `Cabinet` `Documents` `README.md` `.claude` のみ（`Today.md` はまだ無い）。`Cabinet` 配下は `Assets` `Bases` `Diary` `MEMORY.md` `Notes` `Templates`。

- [ ] **Step 7: コミットする**

```bash
cd /home/asama/obsidian-vault
git add -A
git commit -m "refactor: 旧ゾーンを破棄しフォルダ骨格を再構成

Inbox/・Review/・孤児の20_Diary/・壊れたdaily-notes.jsonを削除し、
Documents/をvault直下へ、.baseをCabinet/Bases/へ移動した。"
```

---

## Task 2: `index.py` のコア（frontmatter解析とTSV出力）

**Files:**
- Create: `.claude/scripts/index.py`
- Test: `.claude/scripts/tests/test_index.py`

**Interfaces:**
- Consumes: Task 1 のディレクトリ構造
- Produces:
  - CLI: `python3 .claude/scripts/index.py [--vault-root PATH]`
  - 出力: ヘッダ行なしのTSV。1行1ノート。列は `path`, `type`, `status`, `due`, `check`, `done`, `context`, `date`, `title`, `mtime` の10列固定
  - 関数: `parse_frontmatter(text: str) -> dict[str, str]`, `sanitize(value: str) -> str`, `build_row(note: Path, vault_root: Path) -> dict[str, str]`, `collect(vault_root: Path) -> list[dict[str, str]]`, `main(argv=None) -> int`
  - 定数: `COLUMNS: list[str]`

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_index.py` を新規作成する。

```python
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_index.py -v
```

Expected: 全テストが FAIL または ERROR。`index.py` が存在しないため `subprocess` が非ゼロ終了し、`assert result.returncode == 0` で落ちる。

- [ ] **Step 3: 最小の実装を書く**

`.claude/scripts/index.py` を新規作成する。

```python
#!/usr/bin/env python3
"""Cabinet/Notes/ のノートを索引化してTSVで出力する。

秘書ループがvaultを読む唯一の経路。個別ノートの読み込みは、実際にそのノートを
編集するときだけ行う。出力はヘッダ行を持たず、1行が1ノートに対応する。
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

COLUMNS = [
    "path",
    "type",
    "status",
    "due",
    "check",
    "done",
    "context",
    "date",
    "title",
    "mtime",
]


def parse_frontmatter(text: str) -> dict[str, str]:
    """先頭の `---` で囲まれた `key: value` 行を辞書にして返す。

    閉じの `---` が無い場合はfrontmatter無しとみなして空の辞書を返す。
    値の前後を囲むクォートは取り除く。
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    props: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return props
        key, separator, value = line.partition(":")
        if not separator:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        props[key.strip()] = value
    return {}


def sanitize(value: str) -> str:
    """TSVの行と列を壊す制御文字を空白に潰す。"""
    return value.replace("\t", " ").replace("\n", " ").replace("\r", " ")


def build_row(note: Path, vault_root: Path) -> dict[str, str]:
    """ノート1件を索引の1行に変換する。"""
    props = parse_frontmatter(note.read_text(encoding="utf-8"))
    row = {column: sanitize(props.get(column, "")) for column in COLUMNS}
    row["path"] = note.relative_to(vault_root).as_posix()
    row["title"] = note.stem
    row["mtime"] = dt.datetime.fromtimestamp(note.stat().st_mtime).isoformat(
        timespec="seconds"
    )
    return row


def collect(vault_root: Path) -> list[dict[str, str]]:
    """Cabinet/Notes/ 直下の .md をファイル名順に索引化する。"""
    notes_dir = vault_root / "Cabinet" / "Notes"
    if not notes_dir.is_dir():
        return []
    return [build_row(note, vault_root) for note in sorted(notes_dir.glob("*.md"))]


def default_vault_root() -> Path:
    """このスクリプトの位置からvaultのルートを求める。"""
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ノートの索引をTSVで出力する")
    parser.add_argument("--vault-root", type=Path, default=default_vault_root())
    args = parser.parse_args(argv)

    for row in collect(args.vault_root.resolve()):
        print("\t".join(row[column] for column in COLUMNS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_index.py -v
```

Expected: 8 passed。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/scripts/index.py .claude/scripts/tests/test_index.py
git commit -m "feat: index.py のコアを実装（frontmatter解析とTSV出力）"
```

---

## Task 3: `index.py` の絞り込みオプション

**Files:**
- Modify: `.claude/scripts/index.py`
- Test: `.claude/scripts/tests/test_index.py`

**Interfaces:**
- Consumes: Task 2 の `COLUMNS`, `collect()`, `main()`
- Produces:
  - CLI: `--type`, `--status`（いずれもカンマ区切りでOR）、`--due-before DATE`、`--updated-on DATE`、`--contexts`
  - 複数オプションの併用はAND
  - 関数: `csv_list(value: str) -> list[str]`, `matches(row: dict[str, str], args) -> bool`
  - `--contexts` 指定時は空でない `context` 値を重複排除・昇順で1行1件出力する（TSVは出力しない）

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_index.py` の末尾に追記する。

```python
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_index.py -v
```

Expected: 新規8件が FAIL。`--type` 等は未定義オプションなので argparse が exit code 2 を返し、`assert result.returncode == 0` で落ちる。

- [ ] **Step 3: 絞り込みを実装する**

`.claude/scripts/index.py` の `default_vault_root()` の直前に2つの関数を追加する。

```python
def csv_list(value: str) -> list[str]:
    """カンマ区切りの文字列を空要素を除いたリストにする。"""
    return [item.strip() for item in value.split(",") if item.strip()]


def matches(row: dict[str, str], args: argparse.Namespace) -> bool:
    """索引の1行が絞り込み条件をすべて満たすかを判定する。"""
    if args.type and row["type"] not in args.type:
        return False
    if args.status and row["status"] not in args.status:
        return False
    if args.due_before and (not row["due"] or row["due"] > args.due_before):
        return False
    if args.updated_on and not row["mtime"].startswith(args.updated_on):
        return False
    return True
```

`main()` を次の内容に差し替える。

```python
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ノートの索引をTSVで出力する")
    parser.add_argument("--vault-root", type=Path, default=default_vault_root())
    parser.add_argument("--type", type=csv_list, default=[], help="typeで絞る（カンマ区切りでOR）")
    parser.add_argument("--status", type=csv_list, default=[], help="statusで絞る（カンマ区切りでOR）")
    parser.add_argument("--due-before", help="dueがこの日付以前のものに絞る")
    parser.add_argument("--updated-on", help="この日付に更新されたものに絞る")
    parser.add_argument("--contexts", action="store_true", help="既存のcontext値を一覧する")
    args = parser.parse_args(argv)

    rows = collect(args.vault_root.resolve())

    if args.contexts:
        for context in sorted({row["context"] for row in rows if row["context"]}):
            print(context)
        return 0

    for row in rows:
        if matches(row, args):
            print("\t".join(row[column] for column in COLUMNS))
    return 0
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_index.py -v
```

Expected: 16 passed。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/scripts/index.py .claude/scripts/tests/test_index.py
git commit -m "feat: index.py に絞り込みオプションを追加"
```

---

## Task 4: `new_note.py`

**Files:**
- Create: `.claude/scripts/new_note.py`
- Test: `.claude/scripts/tests/test_new_note.py`

**Interfaces:**
- Consumes: Task 1 のディレクトリ構造
- Produces:
  - CLI: `python3 .claude/scripts/new_note.py --type {task,project,meeting,know-how} --title TITLE [--vault-root PATH] [--set key=value ...]`
  - 成功時: `Cabinet/Notes/<title>.md` を作り、vault相対パスを標準出力に1行出して 0 を返す
  - 既存ファイルがある場合: 何も書かず 1 を返す
  - 不正な引数・テンプレートに無いプロパティ・不正なノート名: 2 を返す
  - `date` は `--set` で明示されなければ実行日で埋める
  - 関数: `split_frontmatter(text: str) -> tuple[list[str], str]`, `apply_overrides(fm_lines: list[str], overrides: dict[str, str]) -> list[str]`, `parse_set(values: list[str]) -> dict[str, str]`, `main(argv=None) -> int`

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_new_note.py` を新規作成する。

```python
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
check:
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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_new_note.py -v
```

Expected: 8件すべて FAIL。`new_note.py` が存在しないため。

- [ ] **Step 3: 実装を書く**

`.claude/scripts/new_note.py` を新規作成する。

```python
#!/usr/bin/env python3
"""テンプレートから Cabinet/Notes/ にノートを1件作る。

終了コードは 0=成功、1=同名ノートが既にある、2=入力エラー。
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

NOTE_TYPES = ["task", "project", "meeting", "know-how"]
FORBIDDEN_TITLE_CHARS = set('\\/:*?"<>|')


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """テンプレートをfrontmatterの行リストと残りの本文に分ける。"""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("テンプレートにfrontmatterがありません")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index], "\n".join(lines[index + 1 :])
    raise ValueError("テンプレートのfrontmatterが閉じていません")


def apply_overrides(fm_lines: list[str], overrides: dict[str, str]) -> list[str]:
    """frontmatterの各行に上書き値を反映する。

    テンプレートに存在しないプロパティを指定された場合は例外を送出する。
    タイポによる無秩序なプロパティの増殖を防ぐため。
    """
    known = {line.partition(":")[0].strip() for line in fm_lines if ":" in line}
    unknown = sorted(set(overrides) - known)
    if unknown:
        raise ValueError(f"テンプレートに存在しないプロパティです: {', '.join(unknown)}")
    result = []
    for line in fm_lines:
        key = line.partition(":")[0].strip()
        if ":" in line and key in overrides:
            result.append(f"{key}: {overrides[key]}")
        else:
            result.append(line)
    return result


def parse_set(values: list[str]) -> dict[str, str]:
    """`key=value` 形式の指定を辞書にする。"""
    overrides: dict[str, str] = {}
    for item in values:
        key, separator, value = item.partition("=")
        if not separator:
            raise ValueError(f"--set は key=value 形式で指定してください: {item}")
        overrides[key.strip()] = value.strip()
    return overrides


def default_vault_root() -> Path:
    """このスクリプトの位置からvaultのルートを求める。"""
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="テンプレートからノートを1件作る")
    parser.add_argument("--vault-root", type=Path, default=default_vault_root())
    parser.add_argument("--type", required=True, choices=NOTE_TYPES)
    parser.add_argument("--title", required=True)
    parser.add_argument("--set", action="append", default=[], dest="sets")
    args = parser.parse_args(argv)

    title = args.title.strip()
    if not title or set(title) & FORBIDDEN_TITLE_CHARS:
        print(f"ノート名に使えない文字が含まれています: {args.title}", file=sys.stderr)
        return 2

    vault = args.vault_root.resolve()
    template = vault / "Cabinet" / "Templates" / f"{args.type}.md"
    if not template.is_file():
        print(f"テンプレートがありません: {template}", file=sys.stderr)
        return 2

    target = vault / "Cabinet" / "Notes" / f"{title}.md"
    if target.exists():
        print(f"同名のノートが既にあります: {target.relative_to(vault).as_posix()}", file=sys.stderr)
        return 1

    try:
        overrides = parse_set(args.sets)
        overrides.setdefault("date", dt.date.today().isoformat())
        fm_lines, body = split_frontmatter(template.read_text(encoding="utf-8"))
        fm_lines = apply_overrides(fm_lines, overrides)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("---\n" + "\n".join(fm_lines) + "\n---\n" + body, encoding="utf-8")
    print(target.relative_to(vault).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_new_note.py -v
```

Expected: 8 passed。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/scripts/new_note.py .claude/scripts/tests/test_new_note.py
git commit -m "feat: new_note.py を実装（テンプレートからのノート生成）"
```

---

## Task 5: `close_day.sh`

**Files:**
- Create: `.claude/scripts/close_day.sh`
- Test: `.claude/scripts/tests/test_close_day.py`

**Interfaces:**
- Consumes: Task 1 のディレクトリ構造
- Produces:
  - CLI: `bash .claude/scripts/close_day.sh [VAULT_ROOT]`（省略時はスクリプト位置から算出）
  - 成功時: `Today.md` を `Cabinet/Diary/<date>.md` へ移動し、当日分を1コミットにまとめ、`main` へ fast-forward マージし、`origin` があれば push して 0 を返す
  - `Today.md` が無い / `date` が不正 / `daily/*` ブランチでない / コミットする変更が無い / fast-forward できない: 1 を返す
  - `origin` が無い場合は push をスキップして 0 を返す

このスクリプトは `git commit` と `main` へのマージを内部で行う。`branch-guard.sh` は Bash コマンド文字列を検査するため、`daily/*` ブランチ上で `bash .claude/scripts/close_day.sh` を起動する限りブロックされない。締めのマージはこのスクリプトの本来の目的であり、迂回ではない。

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_close_day.py` を新規作成する。

```python
"""close_day.sh のテスト。一時ディレクトリにgitリポジトリを作って検証する。"""
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "close_day.sh"


def git(repo: Path, *args: str) -> str:
    """テスト用リポジトリでgitコマンドを実行する。"""
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def make_repo(tmp_path: Path, today: str = "2026-09-07") -> Path:
    """main と daily ブランチを持ち、Today.md が置かれたリポジトリを作る。"""
    repo = tmp_path / "vault"
    (repo / "Cabinet" / "Diary").mkdir(parents=True)
    (repo / "Cabinet" / "Diary" / ".gitkeep").write_text("", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "test")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "初期コミット")
    git(repo, "checkout", "-q", "-b", f"daily/{today}")
    (repo / "Today.md").write_text(
        f"---\ndate: {today}\n---\n\n## メモ\n- 覚え書き\n", encoding="utf-8"
    )
    return repo


def run_close(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), str(repo)], capture_output=True, text=True
    )


def test_moves_today_into_diary_and_commits(tmp_path):
    repo = make_repo(tmp_path)

    result = run_close(repo)

    assert result.returncode == 0, result.stderr
    assert not (repo / "Today.md").exists()
    assert (repo / "Cabinet" / "Diary" / "2026-09-07.md").is_file()


def test_fast_forwards_main_and_ends_on_main(tmp_path):
    repo = make_repo(tmp_path)

    run_close(repo)

    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert git(repo, "rev-parse", "main") == git(repo, "rev-parse", "daily/2026-09-07")


def test_skips_push_when_origin_is_absent(tmp_path):
    repo = make_repo(tmp_path)

    result = run_close(repo)

    assert result.returncode == 0
    assert "push" in result.stdout


def test_fails_when_today_is_missing(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "Today.md").unlink()

    result = run_close(repo)

    assert result.returncode == 1


def test_fails_when_date_property_is_malformed(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "Today.md").write_text("---\ndate: きょう\n---\n", encoding="utf-8")

    result = run_close(repo)

    assert result.returncode == 1
    assert (repo / "Today.md").exists()


def test_fails_when_not_on_a_daily_branch(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "-b", "feature/other")

    result = run_close(repo)

    assert result.returncode == 1
    assert (repo / "Today.md").exists()


def test_fails_when_main_cannot_fast_forward(tmp_path):
    repo = make_repo(tmp_path)
    main_before = git(repo, "rev-parse", "main")
    git(repo, "stash", "-q", "-u")
    git(repo, "checkout", "-q", "main")
    (repo / "別の変更.md").write_text("main側の変更\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "main側の先行コミット")
    main_after = git(repo, "rev-parse", "main")
    git(repo, "checkout", "-q", "daily/2026-09-07")
    git(repo, "stash", "-q", "pop")

    result = run_close(repo)

    assert result.returncode == 1
    assert main_before != main_after
    assert git(repo, "rev-parse", "main") == main_after
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_close_day.py -v
```

Expected: 7件すべて FAIL。`close_day.sh` が存在しないため bash が exit 127 を返す。

- [ ] **Step 3: 実装を書く**

`.claude/scripts/close_day.sh` を新規作成する。

```bash
#!/usr/bin/env bash
# Today.md を Cabinet/Diary/ へ退避し、当日分を1コミットにまとめて main へ ff マージし push する。
# 終了コード: 0=成功、1=実行時エラー。
set -euo pipefail

vault_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$vault_root"

if [[ ! -f Today.md ]]; then
  echo "Today.md がありません" >&2
  exit 1
fi

# frontmatter の date プロパティを1つだけ取り出す
day="$(awk '/^---$/{fence++; next} fence==1 && /^date:/{sub(/^date:[[:space:]]*/, ""); print; exit}' Today.md)"
if [[ ! "$day" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Today.md の date プロパティを読めません: '${day}'" >&2
  exit 1
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$branch" != daily/* ]]; then
  echo "日次ブランチ (daily/*) 上で実行してください。現在: ${branch}" >&2
  exit 1
fi

mkdir -p Cabinet/Diary
mv Today.md "Cabinet/Diary/${day}.md"

git add -A
if git diff --cached --quiet; then
  echo "コミットする変更がありません" >&2
  exit 1
fi
git commit -q -m "chore: ${day} の記録"

git checkout -q main
if ! git merge --ff-only -q "$branch"; then
  git checkout -q "$branch"
  echo "main へ fast-forward マージできませんでした。手動で解決してください。" >&2
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "origin が無いため push をスキップしました"
  exit 0
fi

git push -q origin main
echo "締め完了: Cabinet/Diary/${day}.md を push しました"
```

- [ ] **Step 4: 実行権限を付けてテストが通ることを確認する**

```bash
cd /home/asama/obsidian-vault
chmod +x .claude/scripts/close_day.sh .claude/scripts/index.py .claude/scripts/new_note.py
python3 -m pytest .claude/scripts/tests/test_close_day.py -v
```

Expected: 7 passed。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/scripts/close_day.sh .claude/scripts/tests/test_close_day.py
git update-index --chmod=+x .claude/scripts/close_day.sh .claude/scripts/index.py .claude/scripts/new_note.py
git commit -m "feat: close_day.sh を実装（締めのgit操作）"
```

---

## Task 6: テンプレート5本

**Files:**
- Rewrite: `Cabinet/Templates/{today,task,project,meeting,know-how}.md`
- Test: `.claude/scripts/tests/test_templates.py`

**Interfaces:**
- Consumes: Task 4 の `new_note.py`
- Produces: 各typeのテンプレート。frontmatterのキー集合が設計書5章の表と一致し、`new_note.py` から生成できること

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_templates.py` を新規作成する。

```python
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
    "task": ["type", "date", "status", "due", "check", "done", "context"],
    "project": ["type", "date", "status", "due", "context"],
    "meeting": [
        "type", "date", "status", "context", "calendar_event_id", "calendar_series_id"
    ],
    "know-how": ["type", "date", "context"],
}

EXPECTED_HEADINGS = {
    "task": ["## 完了条件", "## 作業ログ"],
    "project": ["## 概要", "## 現状と次の一手", "## 経緯", "## 関連"],
    "meeting": ["## 議題", "## 資料", "## メモ", "## 決定事項", "## アクション"],
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
    shutil.copytree(VAULT / "Cabinet" / "Templates", tmp_path / "Cabinet" / "Templates")
    (tmp_path / "Cabinet" / "Notes").mkdir()
    return tmp_path


@pytest.mark.parametrize("note_type", sorted(EXPECTED_KEYS))
def test_frontmatter_keys_match_the_spec(note_type):
    text = (VAULT / "Cabinet" / "Templates" / f"{note_type}.md").read_text(encoding="utf-8")

    assert frontmatter_keys(text) == EXPECTED_KEYS[note_type]


@pytest.mark.parametrize("note_type", sorted(EXPECTED_HEADINGS))
def test_headings_match_the_spec(note_type):
    text = (VAULT / "Cabinet" / "Templates" / f"{note_type}.md").read_text(encoding="utf-8")

    assert [line for line in text.split("\n") if line.startswith("## ")] == EXPECTED_HEADINGS[note_type]


def test_today_template_has_the_four_sections():
    text = (VAULT / "Cabinet" / "Templates" / "today.md").read_text(encoding="utf-8")

    assert frontmatter_keys(text) == ["date"]
    assert [line for line in text.split("\n") if line.startswith("## ")] == [
        "## 今日の予定",
        "## 今日のタスク",
        "## 確認したいこと",
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
    created = vault / "Cabinet" / "Notes" / f"検証用{note_type}.md"
    assert f"type: {note_type}" in created.read_text(encoding="utf-8")


def test_task_status_defaults_to_todo():
    text = (VAULT / "Cabinet" / "Templates" / "task.md").read_text(encoding="utf-8")

    assert "status: 1_todo" in text


def test_meeting_status_defaults_to_scheduled():
    text = (VAULT / "Cabinet" / "Templates" / "meeting.md").read_text(encoding="utf-8")

    assert "status: 1_予定" in text
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_templates.py -v
```

Expected: 現行テンプレートは旧セクション構成のため、`test_headings_match_the_spec` と `test_frontmatter_keys_match_the_spec` が FAIL。

- [ ] **Step 3: テンプレートを書き直す**

`Cabinet/Templates/task.md`:

```markdown
---
type: task
date:
status: 1_todo
due:
check:
done:
context:
---

## 完了条件

## 作業ログ
```

`Cabinet/Templates/project.md`:

```markdown
---
type: project
date:
status: 1_active
due:
context:
---

## 概要

## 現状と次の一手

## 経緯

## 関連

![[プロジェクト.base#関連ノート]]
```

`Cabinet/Templates/meeting.md`:

```markdown
---
type: meeting
date:
status: 1_予定
context:
calendar_event_id:
calendar_series_id:
---

## 議題

## 資料

## メモ

## 決定事項

## アクション
```

`Cabinet/Templates/know-how.md`:

```markdown
---
type: know-how
date:
context:
---

## 状況

## 手順

## 注意点
```

`Cabinet/Templates/today.md`:

```markdown
---
date:
---

## 今日の予定

## 今日のタスク

## 確認したいこと

## メモ
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_templates.py -v
```

Expected: 15 passed。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add Cabinet/Templates .claude/scripts/tests/test_templates.py
git commit -m "refactor: テンプレート5本を最小骨に書き直す

project 14セクション・meeting 10セクションを廃し、空欄の見出しを量産しない
構成にした。task/meeting/know-how の更新履歴を廃止し、project のみ経緯を残す。"
```

---

## Task 7: `.base` 4本

**Files:**
- Rewrite: `Cabinet/Bases/{プロジェクト,タスク,議事録,ノウハウ}.base`
- Test: `.claude/scripts/tests/test_bases.py`

**Interfaces:**
- Consumes: Task 1 の `Cabinet/Bases/`、Task 6 の `project.md` が参照する `関連ノート` ビュー名
- Produces: 4本の `.base`。各ファイルのビューは2つ以内。`プロジェクト.base` は `関連ノート` という名前のビューを持つ

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_bases.py` を新規作成する。

```python
"""Cabinet/Bases/ の .base 4本を構文と規約の面から検証する。"""
from pathlib import Path

import pytest
import yaml

VAULT = Path(__file__).resolve().parents[3]
BASES_DIR = VAULT / "Cabinet" / "Bases"
EXPECTED_FILES = ["タスク.base", "ノウハウ.base", "プロジェクト.base", "議事録.base"]


def load(name: str) -> dict:
    return yaml.safe_load((BASES_DIR / name).read_text(encoding="utf-8"))


def test_exactly_four_base_files_exist():
    assert sorted(path.name for path in BASES_DIR.glob("*.base")) == EXPECTED_FILES


@pytest.mark.parametrize("name", EXPECTED_FILES)
def test_base_is_valid_yaml_with_views(name):
    data = load(name)

    assert isinstance(data, dict)
    assert isinstance(data.get("views"), list)
    assert data["views"], "ビューが1つもありません"


@pytest.mark.parametrize("name", EXPECTED_FILES)
def test_base_has_at_most_two_views(name):
    assert len(load(name)["views"]) <= 2


@pytest.mark.parametrize("name", EXPECTED_FILES)
def test_every_view_has_a_name_and_filters(name):
    for view in load(name)["views"]:
        assert view.get("name"), f"{name} に名前の無いビューがあります"
        assert view.get("type") == "table"
        assert "filters" in view


def test_project_base_exposes_the_embedded_view():
    names = [view["name"] for view in load("プロジェクト.base")["views"]]

    assert "関連ノート" in names


def test_project_template_embeds_an_existing_view():
    template = (VAULT / "Cabinet" / "Templates" / "project.md").read_text(encoding="utf-8")
    names = [view["name"] for view in load("プロジェクト.base")["views"]]

    embedded = [
        line for line in template.split("\n") if line.startswith("![[プロジェクト.base#")
    ]
    assert len(embedded) == 1
    view_name = embedded[0].split("#", 1)[1].rstrip("]")
    assert view_name in names
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_bases.py -v
```

Expected: `test_base_has_at_most_two_views` が `プロジェクト.base`（4ビュー）と `タスク.base`（7ビュー）で FAIL。`test_project_base_exposes_the_embedded_view` も FAIL。

- [ ] **Step 3: `.base` を書き直す**

`Cabinet/Bases/プロジェクト.base`:

```yaml
views:
  - type: table
    name: 進行中
    filters:
      and:
        - type == "project"
        - status == "1_active"
    order:
      - file.name
      - due
      - context
    sort:
      - property: due
        direction: ASC
    columnSize:
      note.due: 110
  - type: table
    name: 関連ノート
    filters:
      and:
        - file.hasLink(this.file)
        - type != "project"
    groupBy:
      property: type
      direction: ASC
    order:
      - file.name
      - type
      - status
      - due
      - date
    summaries:
      file.name: Count
```

`Cabinet/Bases/タスク.base`:

```yaml
views:
  - type: table
    name: 期限超過
    filters:
      and:
        - type == "task"
        - status != "4_done"
        - status != "5_cancelled"
        - due < today()
    order:
      - file.name
      - due
      - status
      - context
    sort:
      - property: due
        direction: ASC
    columnSize:
      note.due: 110
  - type: table
    name: 全件棚卸し
    filters:
      and:
        - type == "task"
    groupBy:
      property: status
      direction: ASC
    order:
      - file.name
      - status
      - due
      - done
      - context
    summaries:
      file.name: Count
    columnSize:
      note.status: 130
```

`Cabinet/Bases/議事録.base`:

```yaml
views:
  - type: table
    name: 日付降順
    filters:
      and:
        - type == "meeting"
    order:
      - file.name
      - date
      - status
      - context
    sort:
      - property: date
        direction: DESC
    columnSize:
      note.date: 110
  - type: table
    name: コンテキスト別
    filters:
      and:
        - type == "meeting"
    groupBy:
      property: context
      direction: ASC
    order:
      - file.name
      - context
      - date
      - status
    columnSize:
      note.date: 110
```

`Cabinet/Bases/ノウハウ.base`:

```yaml
views:
  - type: table
    name: 全ノウハウ一覧
    filters:
      and:
        - type == "know-how"
    order:
      - file.name
      - date
      - context
    sort:
      - property: date
        direction: DESC
    columnSize:
      note.date: 110
  - type: table
    name: コンテキスト別
    filters:
      and:
        - type == "know-how"
    groupBy:
      property: context
      direction: ASC
    order:
      - file.name
      - context
      - date
    columnSize:
      note.date: 110
```

- [ ] **Step 4: テストが通ることを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_bases.py -v
```

Expected: 15 passed。

- [ ] **Step 5: 全テストを通す**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -v
```

Expected: 全件 passed。

- [ ] **Step 6: コミットする**

```bash
cd /home/asama/obsidian-vault
git add Cabinet/Bases .claude/scripts/tests/test_bases.py
git commit -m "refactor: .base を4本・各2ビュー以内に削減

タスク.base の7ビューを2本に、プロジェクト.base の4ビューを2本にまとめた。
関連タスクと関連議事録は type でグループ化した単一の関連ノートビューに統合した。"
```

---

## Task 8: `secretary` スキル

**Files:**
- Create: `.claude/skills/secretary/SKILL.md`
- Delete: `.claude/skills/today/`, `.claude/skills/intake/`, `.claude/skills/setup/`

**Interfaces:**
- Consumes: Task 2〜7 のスクリプト・テンプレート・`.base`
- Produces: 開始／更新／締めの3モードと取り込み入口を持つ単一スキル。分類基準の唯一の定義箇所

- [ ] **Step 1: 旧スキルを削除する**

```bash
cd /home/asama/obsidian-vault
git rm -r -q .claude/skills/today .claude/skills/intake .claude/skills/setup
```

- [ ] **Step 2: `secretary` スキルを書く**

`.claude/skills/secretary/SKILL.md` を新規作成する。

````markdown
---
name: secretary
description: 秘書ループの本体。開始・更新・締めの3モードと、貼り付けられた本文の取り込みを行う。「今日のノート開いて」等は開始または更新、「締めて」「クリアデスクして」は締め、メール・チャット本文が貼られた場合は取り込みとして扱う。
---

# secretary

Obsidian vaultで秘書業務を回す。人間との接点は `Today.md` 1枚だけ、vaultの読み取りは `index.py` だけ、分類基準はこのファイルだけ。

## モードの判別

- `Today.md` が無い → **開始モード**
- `Today.md` がある → **更新モード**
- 「締めて」「クリアデスク」等の明示指示 → **締めモード**
- 会話にメール・チャット等の本文が貼られている → **取り込み**

締めは時刻では起動しない。人間が退勤したかを時刻から推定できないため。

## 共通の前提

- ノートを作成・編集する前に、日次ブランチ `daily/<今日の日付>` にいることを確認する。無ければ `main` から `git checkout -b daily/<今日の日付>` で作る。
- 日中はコミットしない。締めが1コミットにまとめる。
- `Cabinet/Notes/` を1件ずつ読んではいけない。一覧が要るときは必ず `index.py` を使う。個別のReadは、実際にそのノートを編集するときだけ行う。
- 通知は一切行わない。伝えたいことは `Today.md` に書く。

## スクリプト

```bash
# 索引（列: path type status due check done context date title mtime、ヘッダ行なし）
python3 .claude/scripts/index.py [--type task,meeting] [--status 1_todo,2_doing] \
    [--due-before 2026-09-07] [--updated-on 2026-09-07] [--contexts]

# ノート生成（vault相対パスを標準出力に返す。既存なら終了コード1）
python3 .claude/scripts/new_note.py --type task --title "見積書の作成" \
    --set due=2026-09-10 --set context=A社

# 締め（Diary退避・コミット・ffマージ・push）
bash .claude/scripts/close_day.sh
```

## 開始モード

1. 日次ブランチを確認・作成する。
2. `Cabinet/Templates/today.md` から `Today.md` を作り、`date` を今日にする。
3. `Cabinet/MEMORY.md` を読む。
4. カレンダーを取得する（下の「カレンダー」参照）。
5. 各イベントを `index.py --type meeting` の出力と `calendar_event_id` で照合し、無ければ `new_note.py --type meeting` で作る。`## 資料` をイベントから埋める。
6. 定例（`calendar_series_id` が一致）は前回の同シリーズ議事録から `## アクション` の未完分と `## 議題` を転記する。当日の会議が3件以上なら、各会議の過去議事録探索を Explore サブエージェントへ並列委任する。探索範囲は `Cabinet/Notes/` のみ。書き込みは自分が行う。
7. `index.py --type task --status 1_todo,2_doing` を叩き、`due` が今日以前のもの、または `status` が `2_doing` のものを今日のタスクとする。
8. `## 今日の予定` と `## 今日のタスク` を書く。
9. `/loop` を30分間隔で起動し、更新モードを自走させる。

## 更新モード

1. `index.py` を1回だけ叩く。
2. カレンダーを1回だけ引く。
3. `## 今日の予定` と `## 今日のタスク` を**全置換で再生成**する。開始モードと同じ抽出条件を使う。
4. `## メモ` の未処理行（行末に `→ [[...]]` が無い行）を分類し、`new_note.py` でノート化し、行末に ` → [[ノート名]]` を追記する。
5. `## 確認したいこと` の回答済み行（`→` の右に文字がある行）を処理し、ノート化してその行を削除する。
6. カレンダーから消えたイベントに対応する meeting ノートは `status` を `3_中止` にする。

このモードは冪等である。前回の状態を保存する必要はない。

`## メモ` と `## 確認したいこと` に対しては追記と処理済み行の削除だけを行い、人間が書いた文言を書き換えない。

## 締めモード

1. `index.py --updated-on <今日>` と `Today.md` の内容から、`Cabinet/MEMORY.md` へ昇格すべき持続的文脈があるか判断する。あれば1行追記する。
2. `## 今日の予定` と `## 今日のタスク` を当日の実績サマリーに書き換える。`## 確認したいこと` と `## メモ` は変えない。
3. `bash .claude/scripts/close_day.sh` を実行する。非ゼロで終了したら `/loop` を止めず、失敗内容を報告して停止する。
4. `/loop` を停止する。

未処理のメモ行や未回答の確認事項は、`Today.md` ごと `Cabinet/Diary/` へ退避されるだけでよい。強制的な変換は行わない。

## 取り込み

会話に貼られた本文からノートを作る。

1. 依頼内容・締切・関連する案件を読み取る。
2. 下の分類基準で `type` と `context` を決める。
3. `new_note.py` でノートを作り、原文全体を `task` なら `## 作業ログ`、`know-how` なら `## 状況` に残す。
4. 作ったノートのパスを人間に伝える。

## 分類基準

判定順に評価し、最初に該当したものを採る。

1. **meeting** — カレンダーイベントに対応する、または会議・打合せの記録である。
2. **project** — 複数のタスクを束ね、数週間以上続き、固有名詞で呼ばれる案件である。
3. **task** — 期限または完了条件があり、自分が行う具体的な行動である。
4. **know-how** — 再利用可能な手順・知識であり、行動ではなく参照対象である。

`context` は `index.py --contexts` が返す既存値から選ぶ。該当が無ければ新規に作らず、確認事項に回す。

### 確信が持てないとき

`## 確認したいこと` に1行足す。書式は `- <質問> →` とし、`→` の右は空けておく。

**往復の上限は2回とする。** 2回目でも確定しなければ、最も確からしい分類でノートを作り、その旨をノート本文に1行記す。人間とAIの往復を無限化させないため。

## カレンダー

1. 実行時に利用可能なカレンダーMCPツールを列挙する。
2. 見つかったすべてのソースから当日 00:00–23:59（ローカルタイムゾーン）のイベントを取得してマージする。
3. イベントの `id` を `calendar_event_id`、`recurringEventId` を `calendar_series_id` に対応させる。
4. **取得できたソースと、失敗・未接続のソースを `## 今日の予定` の直下に必ず書く。** 書式は `（取得元: Google ✓ / Outlook 未接続）`。
5. イベントの `attachments`（`title` と `fileUrl`）と `description` 内のURLを `## 資料` に `[表示名](URL)` 形式で書く。Google Drive のファイルは Drive MCP で表示名を解決する。解決できなければURLをそのまま書く。

第4項は必須である。取得できていない事実が毎日 `Today.md` に現れることで、連携の欠落が放置されるのを防ぐ。

## ノートの編集

- `status` や `due` の変更は frontmatter を直接編集する。値域は `.claude/CLAUDE.md` の表に従う。
- `task` を完了にするときは `status: 4_done` と `done: <今日の日付>` を両方書く。
- `## 更新履歴` は作らない。`project` の `## 経緯` にだけ、方針・判断の変化を書く。`status` の変更では書かない。
````

- [ ] **Step 3: スキルが参照するパスが実在することを確認する**

```bash
cd /home/asama/obsidian-vault
grep -oE '\.claude/scripts/[a-z_]+\.(py|sh)|Cabinet/Templates/[a-z-]+\.md|Cabinet/MEMORY\.md' .claude/skills/secretary/SKILL.md | sort -u | while read -r p; do
  [ -e "$p" ] && echo "OK   $p" || echo "MISS $p"
done
```

Expected: すべて `OK`。`MISS` が1件でもあれば実装を止めて報告する。

- [ ] **Step 4: 旧スキルへの参照が残っていないことを確認する**

```bash
cd /home/asama/obsidian-vault
grep -rn 'skills/today\|skills/intake\|skills/setup\|opening\.md\|update\.md\|closing\.md' .claude/skills .claude/commands README.md || echo "参照なし"
```

Expected: `参照なし`。`.claude/specs/` と `.claude/plans/` は旧構成を引用として記述するため検査対象から外す。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add -A .claude/skills
git commit -m "feat: secretary スキルに統合

today(3ファイル154行)・intake・setup の3スキルを1本に統合し、
分類基準の唯一の定義箇所を作った。往復の上限を2回に定めた。"
```

---

## Task 9: カスタムコマンドと権限設定

**Files:**
- Create: `.claude/commands/today.md`, `.claude/commands/intake.md`, `.claude/commands/close.md`
- Modify: `.claude/settings.local.json`
- Delete: `.claude/commands/.gitkeep`

**Interfaces:**
- Consumes: Task 8 の `secretary` スキル
- Produces: `/today`, `/intake`, `/close` の3コマンドと、無人ループが止まらない権限設定

- [ ] **Step 1: コマンドを3本書く**

`.claude/commands/today.md`:

```markdown
---
description: 秘書ループを開始または更新する
---

`secretary` スキルを起動する。`Today.md` が無ければ開始モード、あれば更新モードとして扱う。
```

`.claude/commands/intake.md`:

```markdown
---
description: 貼り付けられた本文をノート化する
---

`secretary` スキルを取り込みモードで起動する。会話に貼られた本文から依頼・締切・関連案件を読み取り、分類基準に従ってノートを作る。
```

`.claude/commands/close.md`:

```markdown
---
description: 1日を締めてクリアデスクする
---

`secretary` スキルを締めモードで起動する。MEMORY昇格判断、実績サマリーの記入、`close_day.sh` の実行、`/loop` の停止までを行う。
```

- [ ] **Step 2: 権限設定を書き換える**

`.claude/settings.local.json` を次の内容に差し替える。

```json
{
  "permissions": {
    "allow": [
      "Bash(git status *)",
      "Bash(git log *)",
      "Bash(git branch --show-current)",
      "Bash(git checkout -b daily/*)",
      "Bash(python3 .claude/scripts/index.py *)",
      "Bash(python3 .claude/scripts/new_note.py *)",
      "Bash(bash .claude/scripts/close_day.sh *)",
      "Bash(python3 -m pytest *)",
      "mcp__claude_ai_Google_Calendar__list_events",
      "mcp__claude_ai_Google_Calendar__list_calendars",
      "mcp__claude_ai_Google_Calendar__search_events",
      "mcp__claude_ai_Google_Calendar__get_event",
      "mcp__claude_ai_Google_Drive__authenticate"
    ]
  }
}
```

カレンダーの読み取り系のみを許可し、`create_event` / `update_event` / `delete_event` は許可しない。秘書ループは予定を読むだけで、書き換えは人間の指示がある場合に限るため。

- [ ] **Step 3: 設定がJSONとして妥当であることを確認する**

```bash
cd /home/asama/obsidian-vault
python3 -c "import json; d=json.load(open('.claude/settings.local.json')); print(len(d['permissions']['allow']), 'entries')"
rm -f .claude/commands/.gitkeep
ls .claude/commands
```

Expected: `13 entries` と `close.md intake.md today.md`。

- [ ] **Step 4: コミットする**

```bash
cd /home/asama/obsidian-vault
git add -A .claude/commands .claude/settings.local.json
git commit -m "feat: /today /intake /close を追加し、MCPとスクリプトを事前許可

無人ループがカレンダー取得のパーミッションプロンプトで停止しないようにした。
カレンダーは読み取り系のみ許可する。"
```

---

## Task 10: `.claude/CLAUDE.md` の全面改訂

**Files:**
- Rewrite: `.claude/CLAUDE.md`

**Interfaces:**
- Consumes: Task 1〜9 の全成果物
- Produces: 実体と一致するvaultの取扱説明書

- [ ] **Step 1: 現行の記述が実体と矛盾している箇所を洗い出す**

```bash
cd /home/asama/obsidian-vault
grep -n 'Inbox\|Review\|更新履歴\|Documents\|intake\|setup\|/today\|\.base' .claude/CLAUDE.md
```

Expected: 旧構成への言及が多数ヒットする。すべて書き換え対象。

- [ ] **Step 2: `.claude/CLAUDE.md` を書き直す**

```markdown
# CLAUDE.md — このvaultの取扱説明書

個人利用のObsidian vault。Obsidianを「見る場所」、Claude Codeを「操作・秘書業務を回す場所」として役割分担する。

## 役割分担

- **人間がやること**: `Today.md` の `## メモ` に思いついたことや受けた依頼を書く。`## 確認したいこと` の `→` の右に回答を書く。1日の最初に `/today` を1回起動する。
- **Claude Codeがやること**: それ以外すべて。メモの構造化、期限・進捗の追跡、会議の事前準備と議事録、`Today.md` の更新、締め処理。

人間がObsidianのファイルエクスプローラーで `Cabinet/` 配下を直接編集・整理することは想定しない。

## フォルダ構成

```
vault/
├── Today.md            ← 人間との唯一の接点
├── Documents/          ← 人間がドラッグ&ドロップで投入する資料
├── Cabinet/            ← Claude Code専管ゾーン
│   ├── Notes/          ← task/project/meeting/know-how をフラット格納
│   ├── Diary/          ← 締めでリネーム移動された過去のToday
│   ├── Assets/         ← Obsidianの添付ファイル
│   ├── Templates/      ← 5本
│   ├── Bases/          ← .base 4本（人間の閲覧専用）
│   └── MEMORY.md       ← 長期記憶
└── .claude/
```

`Cabinet/Notes/` はサブフォルダを作らずフラットに保つ。`type` はフォルダに依存せず判定されるため、フォルダによる分類は不安定な意思決定を強いるだけになる。

## ノート種別とプロパティ

| プロパティ | task | project | meeting | know-how |
|---|---|---|---|---|
| type | ● | ● | ● | ● |
| date | ● | ● | ● | ● |
| status | ● | ● | ● | |
| due | ○ | ○ | | |
| check | ○ | | | |
| done | ○ | | | |
| context | ○ | ○ | ○ | ○ |
| calendar_event_id | | | ○ | |
| calendar_series_id | | | ○ | |

`Cabinet/Diary/` のノートは `date` のみを持つ。

### status の値域

- `task`: `1_todo` / `2_doing` / `3_pending` / `4_done` / `5_cancelled`
- `project`: `1_active` / `2_done`
- `meeting`: `1_予定` / `2_実施済` / `3_中止` / `4_不参加`

`3_中止` は会議そのものが取り消された場合、`4_不参加` は開催されたが自分が出席しなかった場合。

## 更新履歴を持たない

`## 更新履歴` セクションは作らない。`task` の完了日は `done` プロパティで持つ。`project` のみ `## 経緯` を持ち、方針・判断の変化だけを記録する。`status` の変更では書かない。

## `Today.md` の運用

vault直下に常に1つだけ存在する単一ファイル。4セクションを持つ。

| セクション | AI | 人間 |
|---|---|---|
| `## 今日の予定` | 全置換で再生成 | 読む |
| `## 今日のタスク` | 全置換で再生成 | 読む |
| `## 確認したいこと` | 質問行を追加、回答済み行を削除 | `→` の右に回答 |
| `## メモ` | 行末にリンクを追記 | 自由記述 |

AIは人間が書いた文言を書き換えない。処理済みのメモ行は削除せず、` → [[ノート名]]` を追記する。

締めで `Today.md` は `Cabinet/Diary/<date>.md` へリネーム移動され、翌朝また新規に作られる。

## MEMORY.md の運用

`Cabinet/MEMORY.md` は人・状況についての持続的文脈を保存する長期記憶。「どうやるか」は `know-how`、「今何が前提として動いているか」はMEMORY.md。締めが昇格判断を行い、該当があれば1行追記する。開始処理はこのファイルを読んでブリーフィングの前提知識に使う。

## 読み取りは索引スクリプト経由を正とする

`Cabinet/Notes/` を1件ずつ読んではいけない。一覧が必要なときは必ず `.claude/scripts/index.py` を使う。個別のReadは、実際にそのノートを編集するときだけ行う。ノート件数に比例するコストを常時ループに持ち込まないため。

## プロパティ更新はClaude Code経由を正とする

`status` / `due` / `done` をObsidianのプロパティパネルで直接書き換えることを前提にしない。自然言語の指示を受けたら、該当ノートのfrontmatterを直接編集する。

## 通知は行わない

秘書ループは通知を送らない。伝えたいことは `Today.md` に書く。会議直前のリマインドはカレンダーアプリ本体に委ねる。

## Git運用: 日次ブランチ

ノートを新規作成・編集する前に、必ず今日の日次ブランチ `daily/YYYY-MM-DD` にいることを確認する。無ければ `main` から `git checkout -b daily/<今日の日付>` で作る。日中はコミットしない。締めが `close_day.sh` で1コミットにまとめ、`main` へ fast-forward マージして push する。

## コマンド

- `/today`: 秘書ループの開始または更新。`Today.md` の有無で判別する。更新は `/loop` から30分間隔で自動的に呼ばれる。
- `/intake`: 会話に貼られたメール・チャット本文をノート化する。
- `/close`: 1日を締める。時刻では自動起動しない。

手順の詳細は `.claude/skills/secretary/SKILL.md` を参照する。設計の経緯は `.claude/specs/2026-09-07-vault-secretary-redesign-design.md` にある。

## スクリプト

- `.claude/scripts/index.py`: ノートの索引をTSVで出力する。vaultを読む唯一の経路。
- `.claude/scripts/new_note.py`: テンプレートからノートを1件作る。
- `.claude/scripts/close_day.sh`: 締めのgit操作。

テストは `python3 -m pytest .claude/scripts/tests/` で実行する。
```

- [ ] **Step 3: 記述と実体の整合を確認する**

```bash
cd /home/asama/obsidian-vault
grep -oE '\.claude/(scripts|skills|specs|commands)/[A-Za-z0-9_./-]+|Cabinet/[A-Za-z]+(\.md)?' .claude/CLAUDE.md | sort -u | while read -r p; do
  [ -e "$p" ] && echo "OK   $p" || echo "MISS $p"
done
echo "旧ゾーン名: $(grep -c 'Inbox\|Review/' .claude/CLAUDE.md || true)"
echo "更新履歴の言及: $(grep -c '更新履歴' .claude/CLAUDE.md || true)"
```

Expected: パスはすべて `OK`。`旧ゾーン名: 0`。`更新履歴の言及: 2`（「更新履歴を持たない」の見出しと本文の2行のみ。この2行は仕様を否定文で述べるものであり、旧構成の残存ではない）。

- [ ] **Step 4: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/CLAUDE.md
git commit -m "docs: CLAUDE.md を新構成に全面改訂"
```

---

## Task 11: `README.md` の全面改訂

**Files:**
- Rewrite: `README.md`

**Interfaces:**
- Consumes: Task 1〜10 の全成果物
- Produces: 人間向けの短い概要

- [ ] **Step 1: `README.md` を書き直す**

現行288行を次の内容に置き換える。CLAUDE.mdと重複する詳細は書かず、人間が最初に読む案内に絞る。

```markdown
# 秘書vault

Obsidianを「見る場所」、Claude Codeを「秘書業務を回す場所」として使う個人用vault。

## 使い方

1. 1日の最初に Claude Code で `/today` を実行する。`Today.md` が作られ、予定とタスクが埋まる。
2. あとは `Today.md` を開いておくだけでよい。30分ごとに内容が最新化される。
3. 思いついたこと・受けた依頼は `Today.md` の `## メモ` に1行で書く。次の更新でノートになり、行末にリンクが付く。
4. `## 確認したいこと` に質問が現れたら、`→` の右に答えを書く。次の更新で処理される。
5. 1日の終わりに `/close` を実行する。`Today.md` が `Cabinet/Diary/` に片付き、その日の変更がコミットされる。

通知は飛ばない。見に行けば常に最新になっている。

## どこに何があるか

| 場所 | 用途 |
|---|---|
| `Today.md` | 唯一の接点。予定・タスク・確認事項・メモ |
| `Documents/` | 資料置き場。ドラッグ&ドロップで投入する |
| `Cabinet/Notes/` | タスク・プロジェクト・議事録・ノウハウの本体 |
| `Cabinet/Bases/` | 一覧ビュー4本。日常では見ず、棚卸しや検索のときだけ開く |
| `Cabinet/Diary/` | 過去の `Today.md` |
| `Cabinet/MEMORY.md` | 人・状況についての長期記憶 |

`Cabinet/` の中身は Claude Code が管理する。手で整理する必要はない。

## ノートの4種類

`type` プロパティで区別する。フォルダでは分けない。

- `task` — 期限や完了条件がある、自分が行う具体的な行動
- `project` — 複数のタスクを束ねる、数週間以上続く案件
- `meeting` — 会議。カレンダーから自動で作られる
- `know-how` — 再利用できる手順・知識

## 資料の紐付け

会議ノートの `## 資料` からリンクする。カレンダーの添付とdescription内のURLは自動で貼られる。`Documents/` にドラッグ&ドロップした資料は自動では紐付かないので、`## メモ` に書くか自分でリンクを貼る。

## 中身を知りたいとき

- 運用ルール: `.claude/CLAUDE.md`
- 秘書の手順: `.claude/skills/secretary/SKILL.md`
- 設計の経緯と判断の記録: `.claude/specs/2026-09-07-vault-secretary-redesign-design.md`
```

- [ ] **Step 2: 全テストと構造を最終確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -q
echo "--- vault直下 ---"
ls -a . | grep -vE '^(\.|\.\.|\.git|\.obsidian|\.gitignore|desktop\.ini)$'
echo "--- Cabinet ---"
ls Cabinet
echo "--- .claude ---"
ls .claude .claude/scripts .claude/commands .claude/skills
```

Expected: 全テスト passed。vault直下は `Cabinet` `Documents` `README.md` `.claude`。`.claude` 配下に `scripts` `commands` `skills` `specs` `plans` `CLAUDE.md` `settings.local.json`。

- [ ] **Step 3: コミットする**

```bash
cd /home/asama/obsidian-vault
git add README.md
git commit -m "docs: README を新構成に全面改訂

288行を人間向けの案内に絞って書き直した。"
```

---

## Self-Review 記録

**1. Spec coverage** — 設計書の各章と実装タスクの対応。

| 設計書 | タスク |
|---|---|
| 3章 フォルダ構成 | Task 1 |
| 4章 Today.md 仕様 | Task 6（テンプレート）、Task 8（更新規則） |
| 5章 ノートスキーマ・資料紐付け | Task 6、Task 8 |
| 6章 実行機構の割り当て | Task 2〜5（スクリプト）、Task 8（スキル）、Task 9（コマンド）、Task 8 手順6（サブエージェント） |
| 7章 3モードの手順 | Task 8 |
| 8章 カレンダー連携の契約 | Task 8、Task 9（権限） |
| 9章 分類基準 | Task 8 |
| 10章 破棄するもの | Task 1、Task 6、Task 7、Task 8 |
| 11章 閲覧面 | Task 7 |
| 12章 非目標 | 実装しないことの確認。Task 8 に `Documents/` 走査の手順を書かないことで担保 |

**2. 設計書からの逸脱（1件）** — `project` テンプレートに `## 関連` セクションを追加し、`![[プロジェクト.base#関連ノート]]` を埋め込んだ。設計書5章の project は3セクションだが、設計書11章が「プロジェクトノート埋め込み用の関連タスク・関連議事録」ビューを要求しているのに、埋め込む先のセクションが定義されていなかった。ビュー数を2以内に保つため、関連タスクと関連議事録を `type` でグループ化した単一の `関連ノート` ビューに統合した。

**3. 型と名前の一貫性** — `index.py` の `COLUMNS` 10列は Task 2 で定義し、Task 3 の `matches()` と Task 8 のスキル文書が同じ列名を使う。`new_note.py` の終了コード（0/1/2）は Task 4 で定義し、Task 6 の結合テストと Task 8 のスキル文書が同じ意味で参照する。`プロジェクト.base` のビュー名 `関連ノート` は Task 6 のテンプレートと Task 7 の `.base` とテストの3か所で一致させている。
