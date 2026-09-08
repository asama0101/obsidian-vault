# vault再構成 実装計画

> **エージェント実行者へ**: このプランの実行には superpowers:subagent-driven-development（推奨）または superpowers:executing-plans を使うこと。ステップはチェックボックス（`- [ ]`）で進捗管理する。

**ゴール**: `context` を階層タグに置き換え、`Cabinet/Notes/` に案件フォルダを導入し、秘書ループの1サイクルあたり出力量を当日更新分まで削減する。

**アーキテクチャ**: project をハブに、task と meeting が `project: "[[案件名]]"` で親を指し、実体は `Cabinet/Notes/<案件名>/` に集約する。分類軸は第1階層を5つに固定した階層タグが担い、`index.py` は `rglob` で階層を走査して既定で完了物とカレンダーID列を落とす。Bases は `groupBy: context` をやめ、軸ごとの view と `file.hasTag()` フィルタで表現する。

**技術スタック**: Python 3（標準ライブラリのみ）、pytest、bash、Obsidian Bases（YAML）、Markdown

**設計書**: `.claude/specs/2026-09-07-vault-restructure-design.md`

## 全体制約

- タグ第1階層は5つに固定する（`メーカー` / `領域` / `種別` / `ベンダー` / `設備`）。増やさない。
- `Cabinet/Notes/` は案件フォルダ階層を持つ。`index.py` の走査は `rglob` を使う。
- テストは `python3 -m pytest .claude/scripts/tests/` で実行する。現在95件が green である。**各タスクの完了時点で全件 green を維持すること。**
- 日次ブランチ運用のため `main` 上では編集できない（branch-guard）。作業ブランチは `feat/vault-restructure-design` を使う。
- 移行は考慮しない（実データは `Cabinet/Notes/` に1件のみ）。
- コミットは各タスクの最後に1回だけ行う。
- 応答・docstring・コメントは日本語で書く。コード・変数・シンボルは英語で書く。
- Markdown文書は固定文字数でのハードラップを禁止する。1文または1箇条書き項目は1行で書く。
- 新規パッケージのインストールは行わない。Python は標準ライブラリのみを使う（`test_bases.py` の `yaml` はテスト専用で導入済み）。
- テストは vault 本体を書き換えず、必ず `tmp_path` 上に一時vaultを構築して行う。`test_templates.py` と `test_bases.py` だけは vault 本体を読み取り専用で検証する。
- スクリプトの終了コードは 0=成功、1=実行時エラー（既存ファイル等）、2=入力エラーに統一する。
- `status` の値域は task が `1_todo`/`2_doing`/`3_pending`/`4_done`/`5_cancelled`、project が `1_active`/`2_done`、meeting が `1_予定`/`2_実施済`/`3_中止`/`4_不参加`。

---

## 変更するファイル

| ファイル | 区分 | 責務 |
|---|---|---|
| `.claude/scripts/index.py` | 変更 | `rglob` 走査、`tags`/`project` 列、既定の完了物除外、`--due-before`、`--with-calendar-ids`、`--contexts` 削除 |
| `.claude/scripts/new_note.py` | 変更 | `--project` で案件フォルダへ配置する |
| `.claude/scripts/rename_context.py` | 削除 | `context` 廃止に伴い役割が消える（189行） |
| `.claude/scripts/close_day.sh` | 変更なし | 設計書6章の決定 |
| `.claude/scripts/tests/test_index.py` | 変更 | rglob走査・新しい列順・既定除外・`--due-before`・`--with-calendar-ids` をテストで固定する |
| `.claude/scripts/tests/test_new_note.py` | 変更 | `--project` の挙動をテストする |
| `.claude/scripts/tests/test_rename_context.py` | 削除 | 対象スクリプトの削除に伴う（369行） |
| `.claude/scripts/tests/test_templates.py` | 変更 | 新しいプロパティ構成を期待値にする |
| `.claude/scripts/tests/test_bases.py` | 変更 | view数上限を撤廃し `context` 不使用を検査する |
| `.claude/scripts/tests/test_close_day.py` | 変更なし | `close_day.sh` が変わらないため |
| `Cabinet/Templates/task.md` | 変更 | `context` 削除、`project`・`tags` 追加 |
| `Cabinet/Templates/project.md` | 変更 | `context` を `tags` に置換 |
| `Cabinet/Templates/meeting.md` | 変更 | `context` 削除、`project`・`tags` 追加 |
| `Cabinet/Templates/know-how.md` | 変更 | `context` を `tags` に置換 |
| `Cabinet/Templates/today.md` | 変更なし | 空セクションのみのため |
| `Cabinet/Bases/ノウハウ.base` | 変更 | `groupBy: context` を軸別 view + `file.hasTag()` に置換 |
| `Cabinet/Bases/議事録.base` | 変更 | 同上 |
| `Cabinet/Bases/タスク.base` | 変更 | `order` の `context` を `project` に置換 |
| `Cabinet/Bases/プロジェクト.base` | 変更 | `order` の `context` を `tags` に置換 |
| `Cabinet/Bases/_検証.base` | 作成→削除 | Task 1 の実機検証専用。検証完了後に削除する |
| `Cabinet/Reference/.gitkeep` | 作成 | 案件横断・長寿命の資料置き場 |
| `.claude/skills/secretary/SKILL.md` | 変更 | 出力量削減、予定チェックボックス、カレンダー絞り込み、タグ規則、ノート配置、Documents振り分け |
| `.claude/skills/secretary/references/close.md` | 作成 | 締めモードの詳細手順（9ステップ） |
| `.claude/CLAUDE.md` | 変更 | フォルダ構成・プロパティ表・フラット規約・チェックボックス規約 |
| `README.md` | 変更 | 人間向けの使い方を新構成に合わせる |
| `.claude/settings.local.json` | 変更 | `Cabinet/Reference/**`・`Documents/**` 許可追加、`rename_context.py` 許可削除 |

---

## Task 1: Obsidian Bases の実機検証（人間が実施・ブロッカー）

**Files:**
- Create: `Cabinet/Notes/_bases検証/_検証 project.md`, `Cabinet/Notes/_bases検証/_検証 task.md`, `Cabinet/Notes/_bases検証/_検証 knowhow.md`, `Cabinet/Bases/_検証.base`
- Delete（検証後）: 上記4ファイル

**Interfaces:**
- Consumes: なし
- Produces: 下の「結果記入欄」の4行。**Task 8 はこの記入欄が埋まるまで着手しない。**

**このタスクは自動化できない。**Obsidian のGUIでしか確認できない挙動を判定する。エージェントはステップ1〜2（検証用ファイルの作成）とステップ5（後片付け）を実行し、ステップ3〜4は人間に依頼して停止する。

Task 2〜7 および Task 9〜14 はこのタスクにブロックされない。並行して進めてよい。

- [ ] **Step 1: 検証用ノート3本を作る**

```bash
cd /home/asama/obsidian-vault
mkdir -p "Cabinet/Notes/_bases検証"
cat > "Cabinet/Notes/_bases検証/_検証 project.md" <<'EOF'
---
type: project
date: 2026-09-07
status: 1_active
tags: [種別/更改, メーカー/Cisco]
---

## 概要

Bases の挙動確認用。検証後に削除する。
EOF
cat > "Cabinet/Notes/_bases検証/_検証 task.md" <<'EOF'
---
type: task
date: 2026-09-07
status: 1_todo
project: "[[_検証 project]]"
tags:
---

## 完了条件

Bases の挙動確認用。検証後に削除する。
EOF
cat > "Cabinet/Notes/_bases検証/_検証 knowhow.md" <<'EOF'
---
type: know-how
date: 2026-09-07
tags:
  - 領域/ルーティング
  - メーカー/Cisco
---

## 状況

Bases の挙動確認用。ブロック形式の tags で作る。検証後に削除する。
EOF
```

`_検証 knowhow.md` だけ `tags` をブロック形式にするのは、Obsidianのプロパティパネルがリストをブロック形式で書き戻すため、インライン形式（`_検証 project.md`）との差が `file.hasTag()` の判定に影響しないことを同時に確認するため。

- [ ] **Step 2: 検証用 `.base` を作る**

```bash
cd /home/asama/obsidian-vault
cat > "Cabinet/Bases/_検証.base" <<'EOF'
formulas:
  tagtext: 'file.tags.join(" | ")'
views:
  - type: table
    name: V1 第1階層マッチ
    filters:
      and:
        - file.hasTag("メーカー")
    order:
      - file.name
      - type
      - tags
      - formula.tagtext
  - type: table
    name: V2 第2階層マッチ
    filters:
      and:
        - file.hasTag("メーカー/Cisco")
    order:
      - file.name
      - type
      - tags
      - formula.tagtext
  - type: table
    name: V3 ブロック形式マッチ
    filters:
      and:
        - file.hasTag("領域")
    order:
      - file.name
      - type
      - tags
      - formula.tagtext
  - type: table
    name: V4 リンク逆引き
    filters:
      and:
        - file.hasLink(this.file)
        - type != "project"
    order:
      - file.name
      - type
      - project
  - type: table
    name: V5 フォルダ代替
    filters:
      and:
        - file.inFolder(this.file.folder)
        - type != "project"
    order:
      - file.name
      - type
EOF
```

- [ ] **Step 3: 人間に検証を依頼する（エージェントはここで停止する）**

人間に次の5点を依頼する。

1. **バージョン確認**: Obsidian の 設定 → 一般 → 「現在のバージョン」の表示を読む（macOS/Windowsアプリでは ヘルプ → バージョン情報 でも同じ値が出る）。vault内のファイルにはバージョンが記録されていないため、GUIでしか取得できない。
2. **V1 を開く**: `Cabinet/Bases/_検証.base` をObsidianで開き、view `V1 第1階層マッチ` を選ぶ。`_検証 project` と `_検証 knowhow` の2件が出れば `file.hasTag("親")` は frontmatter の階層タグを拾う。0件なら拾わない。
3. **V2 と V3 を開く**: `V2 第2階層マッチ` は `_検証 project` と `_検証 knowhow` の2件、`V3 ブロック形式マッチ` は `_検証 knowhow` の1件が期待値。V1 が0件でも V2 が2件出るなら「第1階層だけが拾えない」と判定できる。V3 が0件ならブロック形式が拾えない。
4. **V4 と V5 を開く**: `_検証 project.md` をノートとして開き、`![[_検証.base#V4 リンク逆引き]]` を本文に一時的に貼って表示させる（`.base` を直接開くと `this.file` が定まらないため、埋め込みで確認する）。`_検証 task` の1件が出れば `file.hasLink(this.file)` は frontmatter の `project: "[[...]]"` を拾う。0件なら拾わない。同様に `![[_検証.base#V5 フォルダ代替]]` を貼り、`_検証 task` と `_検証 knowhow` の2件が出るかを見る（V4 の代替手段が使えるかの確認）。
5. **`file.tags` の表示を読む**: V1〜V3 のいずれかで `tagtext` 列の値を読む。`#メーカー/Cisco | #種別/更改` のように `#` が付くか、`メーカー/Cisco | 種別/更改` のように付かないかを記録する。

- [ ] **Step 4: 結果を記入する**

人間の回答を受け取ったら、この計画ファイルの下表を編集して埋める。Task 8 の担当エージェントはこの表だけを読んで実装方針を決める。

| # | 検証項目 | 結果 |
|---|---|---|
| 1 | Obsidian のバージョン | （未記入） |
| 2 | `file.hasTag("メーカー")` が階層タグを拾うか（V1／V2／V3の件数） | （未記入） |
| 3 | `file.hasLink(this.file)` が frontmatter のリンクを拾うか（V4の件数／V5の件数） | （未記入） |
| 4 | `file.tags` の要素に `#` が付くか | （未記入） |

- [ ] **Step 5: 検証用ファイルを片付ける**

```bash
cd /home/asama/obsidian-vault
rm -f "Cabinet/Bases/_検証.base"
rm -rf "Cabinet/Notes/_bases検証"
ls Cabinet/Bases
```

Expected: `Cabinet/Bases` に `.base` が4本（`タスク.base` `ノウハウ.base` `プロジェクト.base` `議事録.base`）だけ残る。`_検証 project.md` に貼った埋め込み行も消えていること（ノートごと削除されるため自動的に消える）。

- [ ] **Step 6: コミットする**

検証用ファイルは作成と削除で相殺されるため、コミット対象は結果を記入したこの計画ファイルだけになる。

```bash
cd /home/asama/obsidian-vault
git add .claude/plans/2026-09-07-vault-restructure.md
git commit -m "docs: Bases の実機検証結果を計画に記録

file.hasTag() の階層対応・file.hasLink() のfrontmatter対応・file.tags の
接頭辞を Obsidian 上で確認し、Task 8 の実装方針を確定した。"
```

---

## Task 2: `index.py` — サブフォルダ走査（rglob化）

**Files:**
- Modify: `.claude/scripts/index.py`
- Test: `.claude/scripts/tests/test_index.py`

**Interfaces:**
- Consumes: 現行の `collect(vault_root: Path) -> list[dict[str, str]]`
- Produces: `collect()` が `Cabinet/Notes/` 配下を再帰的に走査する。`path` 列が `Cabinet/Notes/<案件名>/<title>.md` 形式を取りうる

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_index.py` の末尾に追記する。ヘルパ `write_note` は直下にしか置けないため、サブフォルダ用のヘルパを追加する。

```python
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
```

- [ ] **Step 2: 実行して失敗を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_index.py -q
```

Expected: 追加した3件が FAIL。`glob("*.md")` はサブフォルダを見ないため出力が空になり、`len(result) == 1` と `sorted(...) == [...]` と添字アクセスが落ちる。

- [ ] **Step 3: 最小実装を書く**

`.claude/scripts/index.py` の `collect()` を次に置き換える。

```python
def collect(vault_root: Path) -> list[dict[str, str]]:
    """Cabinet/Notes/ 配下（案件フォルダを含む）の .md をパス順に索引化する。"""
    notes_dir = vault_root / "Cabinet" / "Notes"
    if not notes_dir.is_dir():
        return []
    return [build_row(note, vault_root) for note in sorted(notes_dir.rglob("*.md"))]
```

- [ ] **Step 4: 実行して通過を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -q
```

Expected: `98 passed`（95件 + 追加3件）。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/scripts/index.py .claude/scripts/tests/test_index.py
git commit -m "feat(index): 案件フォルダを再帰的に走査する

collect() の glob を rglob に変え、Cabinet/Notes/<案件名>/ 配下のノートを
索引に含めるようにした。path 列は階層パスになる。"
```

---

## Task 3: `index.py` — 出力列の変更

**Files:**
- Modify: `.claude/scripts/index.py`
- Test: `.claude/scripts/tests/test_index.py`

**Interfaces:**
- Consumes: Task 2 の `collect()`
- Produces:
  - 定数: `COLUMNS: list[str]`（既定10列）、`CALENDAR_COLUMNS: list[str]`（2列）、`ALL_COLUMNS: list[str]`（12列）、`LIST_SEPARATOR: str`（`","`）
  - 関数: `strip_quotes(value: str) -> str`、`parse_inline_list(value: str) -> list[str]`、`parse_frontmatter(text: str) -> dict[str, str]`
  - CLI: `--with-calendar-ids`（`action="store_true"`）
  - 既定の列順: `path` `type` `status` `due` `done` `tags` `project` `date` `title` `mtime` の10列固定
  - `--with-calendar-ids` 指定時: 上記10列の末尾に `calendar_event_id` `calendar_series_id` を足した12列

**多値の区切り文字はカンマ（`,`）とする。** `sanitize()` はタブ・改行・復帰をすべて半角空白に潰すため、空白を区切りにすると値内の空白と区別できなくなる。カンマは `sanitize()` が触らず、YAMLのインラインリスト（`[a, b]`）が要素内にカンマを許さないため衝突しない。既存の `--type`/`--status` が使う `csv_list()` の区切りとも揃う。

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_index.py` を編集する。まず先頭の定数を差し替える。

```python
COLUMN_COUNT = 10
COLUMN_COUNT_WITH_CALENDAR_IDS = 12
```

`test_columns_are_in_fixed_order` を次に差し替える。

```python
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
```

`test_note_without_frontmatter_is_still_listed` の `result[0][7]` を `result[0][8]` に直す。`test_quoted_values_are_unquoted`・`test_tab_in_value_is_sanitized`・`test_invalid_utf8_note_does_not_break_the_index` から `context` を消して次に差し替える。

```python
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


def test_invalid_utf8_note_does_not_break_the_index(tmp_path):
    write_note(tmp_path, "正常なノート.md", "---\ntype: task\n---\n")
    notes = tmp_path / "Cabinet" / "Notes"
    (notes / "壊れたノート.md").write_bytes(b"---\ntype: task\ntags: [\xff\xfe]\n---\n")

    result = rows(run_index(tmp_path))

    assert len(result) == 2
    assert result[0][1] == "task"
```

`--type`/`--status`/`--date` 系の既存テストが使う `row[7]`（旧 `title`）はすべて `row[8]` に直す。対象は `test_filter_by_type`・`test_status_accepts_comma_separated_values_as_or`・`test_type_and_status_combine_as_and`・`test_date_matches_only_the_exact_date`・`test_date_combines_with_type_as_and`・`test_updated_on_matches_the_date_part_of_mtime` の6件。

末尾に新規テスト7件を追記する。

```python
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
```

- [ ] **Step 2: 実行して失敗を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_index.py -q
```

Expected: 列変更に触れるテストが FAIL。既定11列のままなので `len(row) == 10` が落ち、`--with-calendar-ids` は未知の引数で `argparse` が終了コード2を返し `run_index` の `assert result.returncode == 0` が落ちる。

- [ ] **Step 3: 最小実装を書く**

`.claude/scripts/index.py` の定数と `parse_frontmatter` を次に置き換える。

```python
LIST_SEPARATOR = ","

COLUMNS = [
    "path",
    "type",
    "status",
    "due",
    "done",
    "tags",
    "project",
    "date",
    "title",
    "mtime",
]
CALENDAR_COLUMNS = ["calendar_event_id", "calendar_series_id"]
ALL_COLUMNS = COLUMNS + CALENDAR_COLUMNS


def strip_quotes(value: str) -> str:
    """値の前後を囲むクォートを1組だけ取り除く。"""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_inline_list(value: str) -> list[str]:
    """`[a, b]` 形式のインラインリストを要素のリストにする。"""
    return [strip_quotes(item.strip()) for item in value[1:-1].split(",") if item.strip()]


def parse_frontmatter(text: str) -> dict[str, str]:
    """先頭の `---` で囲まれたfrontmatterを辞書にして返す。

    値がリストの場合（`[a, b]` のインライン形式と `- a` のブロック形式の両方）は、
    要素を LIST_SEPARATOR で連結した1つの文字列にする。`[[リンク]]` は
    ネストしたリストではなくObsidianのリンクなので、リストとして分解しない。
    閉じの `---` が無い場合はfrontmatter無しとみなして空の辞書を返す。
    値の前後を囲むクォートは取り除く。
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    props: dict[str, str] = {}
    pending_key: str | None = None
    pending_items: list[str] = []

    def flush() -> None:
        """直前の `key:` に続くブロックリストを確定させる。"""
        if pending_key is not None and pending_items:
            props[pending_key] = LIST_SEPARATOR.join(pending_items)

    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            flush()
            return props
        if pending_key is not None and stripped.startswith("- "):
            pending_items.append(strip_quotes(stripped[2:].strip()))
            continue
        flush()
        pending_key, pending_items = None, []
        key, separator, value = line.partition(":")
        if not separator:
            continue
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]") and not value.startswith("[["):
            props[key] = LIST_SEPARATOR.join(parse_inline_list(value))
            continue
        if not value:
            pending_key = key
            props[key] = ""
            continue
        props[key] = strip_quotes(value)
    return {}
```

`build_row()` の列生成を `ALL_COLUMNS` に変える。

```python
    row = {column: sanitize(props.get(column, "")) for column in ALL_COLUMNS}
```

`main()` に `--with-calendar-ids` を足し、出力列を切り替える。

```python
    parser.add_argument(
        "--with-calendar-ids",
        action="store_true",
        help="calendar_event_id と calendar_series_id を末尾に付ける",
    )
```

```python
    columns = ALL_COLUMNS if args.with_calendar_ids else COLUMNS
    for row in rows:
        if matches(row, args):
            print("\t".join(row[column] for column in columns))
    return 0
```

- [ ] **Step 4: 実行して通過を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -q
```

Expected: `105 passed`（98件 + 追加7件）。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/scripts/index.py .claude/scripts/tests/test_index.py
git commit -m "feat(index): context列をtags列に置き換えproject列を追加する

多値のtags/projectをカンマ連結で1セルに収め、インライン形式とブロック形式の
両方を解釈できるようにした。calendar_event_id と calendar_series_id は
--with-calendar-ids を付けたときだけ出力する。"
```

---

## Task 4: `index.py` — フィルタの追加

**Files:**
- Modify: `.claude/scripts/index.py`
- Test: `.claude/scripts/tests/test_index.py`

**Interfaces:**
- Consumes: Task 3 の `COLUMNS` と `matches(row: dict[str, str], args: argparse.Namespace) -> bool`
- Produces:
  - 定数: `COMPLETED_STATUSES: dict[str, set[str]]`
  - 関数: `is_completed(row: dict[str, str]) -> bool`
  - CLI: `--all`（`action="store_true"`）、`--due-before <YYYY-MM-DD>`
  - `--type` / `--status` / `--date` / `--updated-on` の挙動は変えない

**設計判断: `--status` を明示指定したときは既定除外を適用しない。** 既定除外は「フィルタ無しの呼び出しが完了物で膨らむ」ことを防ぐための保護であって、完了物を見せないための禁止ではない。`--status 4_done` は「完了したタスクを見たい」という明示要求であり、ここで既定除外が勝つと結果が常に空になり、オプション自体が壊れる。`--type task` のように `--status` を伴わない指定では既定除外を効かせる（`--type` は絞り込み軸が違うだけで、完了物を見たいという意思表示ではないため）。`--all` は `--status` 未指定時の既定除外を解除する明示スイッチとして残す。

**`--due-before` は指定日を含む。** 「期限が今日以前」という秘書ループの用途（`SKILL.md` の今日のタスク抽出）が境界日を含むため。`due` が空のノートは除外する。

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_index.py` の末尾に9件を追記する。

```python
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
```

- [ ] **Step 2: 実行して失敗を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_index.py -q
```

Expected: 追加9件が FAIL。完了物は既定で出力されたままなので `run_index(tmp_path) == ""` が落ち、`--all` と `--due-before` は未知の引数で `argparse` が終了コード2を返す。

- [ ] **Step 3: 最小実装を書く**

`.claude/scripts/index.py` に定数と判定関数を足す（`COLUMNS` 群の直後に置く）。

```python
COMPLETED_STATUSES = {
    "task": {"4_done", "5_cancelled"},
    "project": {"2_done"},
}
```

```python
def is_completed(row: dict[str, str]) -> bool:
    """既定の出力から外す完了物かを判定する。"""
    return row["status"] in COMPLETED_STATUSES.get(row["type"], set())
```

`matches()` を次に置き換える。

```python
def matches(row: dict[str, str], args: argparse.Namespace) -> bool:
    """索引の1行が絞り込み条件をすべて満たすかを判定する。

    完了物は既定で落とすが、`--all` と `--status` の明示指定はこの既定を解除する。
    `--status 4_done` のような明示要求を既定除外が握り潰すと結果が常に空になるため。
    """
    if not args.all and not args.status and is_completed(row):
        return False
    if args.type and row["type"] not in args.type:
        return False
    if args.status and row["status"] not in args.status:
        return False
    if args.date and row["date"] != args.date:
        return False
    if args.updated_on and not row["mtime"].startswith(args.updated_on):
        return False
    if args.due_before and (not row["due"] or row["due"] > args.due_before):
        return False
    return True
```

`main()` に2つのオプションを足す。

```python
    parser.add_argument("--all", action="store_true", help="完了物も含めて全件出す")
    parser.add_argument("--due-before", help="dueがこの日付以前のものに絞る（指定日を含む）")
```

- [ ] **Step 4: 実行して通過を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -q
```

Expected: `114 passed`（105件 + 追加9件）。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/scripts/index.py .claude/scripts/tests/test_index.py
git commit -m "feat(index): 完了物を既定除外し --due-before を新設する

task の 4_done/5_cancelled と project の 2_done を既定で落とし、--all で戻せる
ようにした。--status の明示指定はこの既定除外を解除する。"
```

---

## Task 5: `index.py` の `--contexts` 削除と `rename_context.py` の削除

**Files:**
- Modify: `.claude/scripts/index.py`
- Delete: `.claude/scripts/rename_context.py`, `.claude/scripts/tests/test_rename_context.py`
- Test: `.claude/scripts/tests/test_index.py`

**Interfaces:**
- Consumes: Task 4 の `main()`
- Produces: `--contexts` を持たない `index.py`。`rename_context.py` は存在しない

**削除するテストは22件。** 内訳は `test_rename_context.py` の全21件（`python3 -m pytest .claude/scripts/tests/test_rename_context.py --collect-only -q` で実測）と、`test_index.py` の `test_contexts_lists_unique_values_sorted` の1件。現在の95件から22件を引くと**73件**になる。ただし Task 2〜4 で19件を追加済みのため、**このタスク完了時点の実測値は 92 passed** となる。

- [ ] **Step 1: `--contexts` のテストを削除する**

`.claude/scripts/tests/test_index.py` の末尾にある `test_contexts_lists_unique_values_sorted`（現行219行目付近、関数定義から末尾まで）を削除する。

- [ ] **Step 2: 実行して失敗を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -q 2>&1 | tail -3
```

Expected: `113 passed`。テストを1件消しただけなので green のままだが、`--contexts` は実装に残っている。次のステップで実装とファイルを消してから、この件数が減ることを確認する。

- [ ] **Step 3: 実装とファイルを削除する**

`.claude/scripts/index.py` から次の2か所を削除する。

- `main()` の `parser.add_argument("--contexts", action="store_true", help="既存のcontext値を一覧する")` の行
- `rows = collect(...)` の直後にある `if args.contexts:` ブロック3行（`for context in sorted(...)` / `print(context)` / `return 0`）

```bash
cd /home/asama/obsidian-vault
git rm -q .claude/scripts/rename_context.py .claude/scripts/tests/test_rename_context.py
grep -rn "contexts\|rename_context" .claude/scripts/ || echo "残存なし"
```

Expected: `grep` が `残存なし` を出す。

- [ ] **Step 4: 実行して通過を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -q 2>&1 | tail -3
```

Expected: `92 passed`（113件 − `test_rename_context.py` の21件）。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add -A .claude/scripts
git commit -m "refactor: context の一括付け替え機構を削除する

context の廃止に伴い index.py の --contexts と rename_context.py（189行）、
test_rename_context.py（369行）を削除した。タグの一括改名は Obsidian の
タグ機能が持つため自前で抱える理由がない。"
```

---

## Task 6: `new_note.py` — 案件フォルダへの配置

**Files:**
- Modify: `.claude/scripts/new_note.py`
- Test: `.claude/scripts/tests/test_new_note.py`

**Interfaces:**
- Consumes: 現行の `main(argv: list[str] | None = None) -> int` と `FORBIDDEN_TITLE_CHARS: set[str]`
- Produces:
  - CLI: `--project "<案件名>"`（任意）
  - 出力: 作成したノートの vault 相対パス。`--project` 指定時は `Cabinet/Notes/<案件名>/<title>.md`、未指定時は `Cabinet/Notes/<title>.md`
  - 終了コード: 0=成功 / 1=同名あり / 2=入力エラー（案件名の検証失敗を含む）

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_new_note.py` の `TASK_TEMPLATE` を新しいプロパティ構成に差し替える。

```python
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
```

`test_set_overrides_a_property` の `--set context=A社` を `--set project=[[A案件]]` に差し替える。

```python
def test_set_overrides_a_property(tmp_path):
    vault = make_vault(tmp_path)

    run_new_note(
        vault, "--type", "task", "--title", "見積書の作成",
        "--set", "due=2026-09-10", "--set", "project=[[A案件]]",
    )

    text = (vault / "Cabinet" / "Notes" / "見積書の作成.md").read_text(encoding="utf-8")
    assert "due: 2026-09-10" in text
    assert "project: [[A案件]]" in text
```

末尾に7件を追記する。

```python
def test_project_option_creates_the_note_in_the_project_folder(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(
        vault, "--type", "task", "--title", "C9500 見積依頼",
        "--project", "大手町DC コアSW更改",
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "Cabinet/Notes/大手町DC コアSW更改/C9500 見積依頼.md"
    assert (vault / "Cabinet" / "Notes" / "大手町DC コアSW更改" / "C9500 見積依頼.md").is_file()


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
    assert (vault / "Cabinet" / "Notes" / "B案件" / "見積依頼.md").is_file()


def test_invalid_project_character_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(
        vault, "--type", "task", "--title", "見積依頼", "--project", "A社/案件",
    )

    assert result.returncode == 2
    assert not (vault / "Cabinet" / "Notes" / "A社").exists()


def test_blank_project_is_rejected(tmp_path):
    vault = make_vault(tmp_path)

    result = run_new_note(vault, "--type", "task", "--title", "見積依頼", "--project", "  ")

    assert result.returncode == 2
```

- [ ] **Step 2: 実行して失敗を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_new_note.py -q
```

Expected: 追加7件が FAIL。`--project` は未知の引数で `argparse` が終了コード2を返すため、`returncode == 0` を期待する4件が落ち、`returncode == 1` を期待する1件も落ちる。`--project` 検証系2件は偶然2が返るが、`A社` フォルダが作られないことの検査は通り、`test_blank_project_is_rejected` も通ってしまう。実装後に意味のある形で通ることを Step 4 で確認する。

- [ ] **Step 3: 最小実装を書く**

`.claude/scripts/new_note.py` の docstring を差し替える。

```python
"""テンプレートから Cabinet/Notes/ にノートを1件作る。

`--project` を指定すると Cabinet/Notes/<案件名>/ の下に作り、案件フォルダが
無ければ作る。未指定なら Cabinet/Notes/ 直下に作る。

終了コードは 0=成功、1=同名ノートが既にある、2=入力エラー。
"""
```

`main()` の引数定義に1行足す。

```python
    parser.add_argument("--project", help="案件フォルダ名。指定するとその配下に作る")
```

タイトル検証の直後に案件名の検証を足す。禁止文字はタイトルと同じ集合を使う（どちらもファイルシステムのパス要素になるため）。

```python
    project = args.project.strip() if args.project is not None else ""
    if args.project is not None and (not project or set(project) & FORBIDDEN_TITLE_CHARS):
        print(f"案件名に使えない文字が含まれています: {args.project}", file=sys.stderr)
        return 2
```

`target` の組み立てを次に置き換える。

```python
    notes_dir = vault / "Cabinet" / "Notes"
    target = notes_dir / project / f"{title}.md" if project else notes_dir / f"{title}.md"
```

既存の `target.parent.mkdir(parents=True, exist_ok=True)` がそのまま案件フォルダの作成を担うため、追加の `mkdir` は要らない。

- [ ] **Step 4: 実行して通過を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -q
```

Expected: `99 passed`（92件 + 追加7件）。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/scripts/new_note.py .claude/scripts/tests/test_new_note.py
git commit -m "feat(new_note): --project で案件フォルダへ配置する

案件名にもタイトルと同じ禁止文字検証を適用し、フォルダが無ければ作る。
未指定時の Cabinet/Notes/ 直下への配置と終了コード規約は変えない。"
```

---

## Task 7: `Cabinet/Templates/` の更新

**Files:**
- Modify: `Cabinet/Templates/task.md`, `Cabinet/Templates/project.md`, `Cabinet/Templates/meeting.md`, `Cabinet/Templates/know-how.md`
- Test: `.claude/scripts/tests/test_templates.py`

**Interfaces:**
- Consumes: Task 6 の `new_note.py`
- Produces: 4本のテンプレートのfrontmatterキー順。`today.md` は変更しない

`task` と `meeting` にも空の `tags:` を置く。設計書3章は task・meeting に原則タグを付けないと定めているが、「親案件と違う機器やベンダーが絡んだときだけ、その軸を付ける」という例外を認めている。キーが無いと例外時に `new_note.py --set` が「テンプレートに存在しないプロパティです」で終了コード2になるため、空欄のキーだけ用意しておく。

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_templates.py` の `EXPECTED_KEYS` を差し替える。

```python
EXPECTED_KEYS = {
    "task": ["type", "date", "status", "due", "done", "project", "tags"],
    "project": ["type", "date", "status", "due", "tags"],
    "meeting": [
        "type", "date", "status", "project", "tags",
        "calendar_event_id", "calendar_series_id",
    ],
    "know-how": ["type", "date", "tags"],
}
```

末尾に1件を追記する。

```python
@pytest.mark.parametrize("note_type", sorted(EXPECTED_KEYS))
def test_no_template_has_a_context_property(note_type):
    text = (VAULT / "Cabinet" / "Templates" / f"{note_type}.md").read_text(encoding="utf-8")

    assert "context" not in text
```

- [ ] **Step 2: 実行して失敗を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_templates.py -q
```

Expected: `test_frontmatter_keys_match_the_spec` の4件と `test_no_template_has_a_context_property` の4件、計8件が FAIL。テンプレートが `context` を持ったままのため。

- [ ] **Step 3: 最小実装を書く**

4本のテンプレートのfrontmatterを書き換える。本文のセクション見出しは変えない。

`Cabinet/Templates/task.md`:

```markdown
---
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
```

`Cabinet/Templates/project.md`:

```markdown
---
type: project
date:
status: 1_active
due:
tags:
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
project:
tags:
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
tags:
---

## 状況

## 手順

## 注意点
```

- [ ] **Step 4: 実行して通過を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -q 2>&1 | tail -3
grep -rn "context" Cabinet/Templates/ || echo "残存なし"
```

Expected: `103 passed`（99件 + 4件）。追加した関数は1本だが `@pytest.mark.parametrize("note_type", sorted(EXPECTED_KEYS))` で4値に展開されるため4件増える。`grep` は `残存なし` を出す。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add Cabinet/Templates .claude/scripts/tests/test_templates.py
git commit -m "feat(templates): context を tags に置き換え project を追加する

task と meeting に project を、4種すべてに tags を持たせた。task/meeting の
tags は例外的な付与のための空欄で、既定では値を入れない。"
```

---

## Task 8: `Cabinet/Bases/` の書き直し（Task 1 の結果に依存）

**Files:**
- Modify: `Cabinet/Bases/ノウハウ.base`, `Cabinet/Bases/議事録.base`, `Cabinet/Bases/タスク.base`, `Cabinet/Bases/プロジェクト.base`
- Test: `.claude/scripts/tests/test_bases.py`

**Interfaces:**
- Consumes: Task 1 の「結果記入欄」、Task 7 の `tags`/`project` プロパティ
- Produces: `groupBy: context` を持たない `.base` 4本。`ノウハウ.base` と `議事録.base` は `file.hasTag()` の view を1本以上持つ

**Task 1 の結果記入欄が空欄のままなら、このタスクに着手しないこと。** 下の分岐で実装が変わる。

| Task 1 の結果 | このタスクの書き方 |
|---|---|
| 検証2で V1 が2件（第1階層が拾える） | 下のコードをそのまま使う |
| 検証2で V1 が0件・V2 が2件（第2階層だけ拾える） | `file.hasTag("メーカー")` のような第1階層のみの指定を使わず、すべて `file.hasTag("メーカー/Cisco")` のように第2階層まで書く。本タスクのコードは元から第2階層で書いてあるため変更不要 |
| 検証2で V2 も0件（frontmatter のタグを拾わない） | `file.hasTag(...)` を `file.tags.contains(...)` に置き換える。引数は検証4の結果に従い、`#` が付くなら `"#メーカー/Cisco"`、付かないなら `"メーカー/Cisco"` |
| 検証3で V4 が1件 | `プロジェクト.base` の `関連ノート` ビューを現行のまま維持する |
| 検証3で V4 が0件・V5 が2件 | `関連ノート` の `file.hasLink(this.file)` を `file.inFolder(this.file.folder)` に置き換える。案件フォルダ導入により同等の結果が得られる |
| 検証3で V4 も V5 も0件 | 実装を止めて人間に報告する。関連ノートの逆引き手段が無くなるため、`プロジェクト.base` の設計をやり直す必要がある |

- [ ] **Step 1: 失敗するテストを書く**

`.claude/scripts/tests/test_bases.py` から `test_base_has_at_most_two_views` を削除する。view方式では軸の値が増えるたびに view が増えるため、上限2という規約自体が設計と矛盾する。代わりに末尾へ2件を追記する。

```python
TAG_VIEW_FILES = ["ノウハウ.base", "議事録.base"]


@pytest.mark.parametrize("name", EXPECTED_FILES)
def test_no_view_uses_context(name):
    text = (BASES_DIR / name).read_text(encoding="utf-8")

    assert "context" not in text


@pytest.mark.parametrize("name", TAG_VIEW_FILES)
def test_tag_views_filter_by_has_tag(name):
    text = (BASES_DIR / name).read_text(encoding="utf-8")

    assert "file.hasTag(" in text, f"{name} にタグ軸のビューがありません"
```

- [ ] **Step 2: 実行して失敗を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/test_bases.py -q
```

Expected: `test_no_view_uses_context` の4件と `test_tag_views_filter_by_has_tag` の2件、計6件が FAIL。4本すべてが `context` を含み、`file.hasTag(` はどこにも無いため。

- [ ] **Step 3: 最小実装を書く**

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
      - tags
    sort:
      - property: date
        direction: DESC
    columnSize:
      note.date: 110
  - type: table
    name: 領域/ルーティング
    filters:
      and:
        - type == "know-how"
        - file.hasTag("領域/ルーティング")
    order:
      - file.name
      - tags
      - date
    columnSize:
      note.date: 110
  - type: table
    name: メーカー/Cisco
    filters:
      and:
        - type == "know-how"
        - file.hasTag("メーカー/Cisco")
    order:
      - file.name
      - tags
      - date
    columnSize:
      note.date: 110
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
      - project
    sort:
      - property: date
        direction: DESC
    columnSize:
      note.date: 110
  - type: table
    name: 未実施
    filters:
      and:
        - type == "meeting"
        - status == "1_予定"
    order:
      - file.name
      - date
      - project
    sort:
      - property: date
        direction: ASC
    columnSize:
      note.date: 110
  - type: table
    name: 種別/障害
    filters:
      and:
        - type == "meeting"
        - file.hasTag("種別/障害")
    order:
      - file.name
      - date
      - project
      - tags
    columnSize:
      note.date: 110
```

議事録の案件別閲覧は `プロジェクト.base` の `関連ノート` ビューが担うため、`議事録.base` には案件軸の view を置かない。meeting は原則タグを持たないので、タグ軸は例外的に付いたときの受け皿として `種別/障害` の1本だけを置く。

`Cabinet/Bases/タスク.base`: `order` の `context` を `project` に置き換える。他は変えない。

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
      - project
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
      - project
    summaries:
      file.name: Count
    columnSize:
      note.status: 130
```

`Cabinet/Bases/プロジェクト.base`: `order` の `context` を `tags` に置き換える。`関連ノート` ビューは Task 1 の検証3の結果に従う（V4 が1件なら現行のまま）。

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
      - tags
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

- [ ] **Step 4: 実行して通過を確認する**

```bash
cd /home/asama/obsidian-vault
python3 -m pytest .claude/scripts/tests/ -q 2>&1 | tail -3
grep -rn "context" Cabinet/Bases/ || echo "残存なし"
```

Expected: `105 passed`（103件 − 削除した `test_base_has_at_most_two_views` の4件 + 追加6件）。`grep` は `残存なし` を出す。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add Cabinet/Bases .claude/scripts/tests/test_bases.py
git commit -m "feat(bases): groupBy: context を軸別viewとhasTagフィルタに置き換える

多値タグの groupBy が1ノートを複数グループに出せないため、軸ごとに view を
定義する方式へ切り替えた。view数上限2の規約はこの方式と矛盾するため撤回した。"
```

---

## Task 9: `SKILL.md` — 出力量の削減

**Files:**
- Modify: `.claude/skills/secretary/SKILL.md`

**Interfaces:**
- Consumes: Task 3〜6 で確定した `index.py` / `new_note.py` のCLI
- Produces: `## スクリプト` 節の usage と、開始モード ステップ8・更新モード ステップ11 の抽出条件

- [ ] **Step 1: `## スクリプト` 節のコードブロックを差し替える**

`SKILL.md:72-90` のコードブロック全体を次に置き換える。`rename_context.py` の2つの例は対象スクリプトごと消えたので削除する。

````markdown
```bash
# 索引（列: path type status due done tags project date title mtime、ヘッダ行なし、10列）
# tags と project が多値のときはカンマ区切りで1セルに入る
python3 .claude/scripts/index.py [--type task,meeting] [--status 1_todo,2_doing] \
    [--date 2026-09-07] [--updated-on 2026-09-07] [--due-before 2026-09-07] \
    [--with-calendar-ids] [--all]

# --with-calendar-ids を付けると末尾に calendar_event_id calendar_series_id が増えて12列になる
# 既定では task の 4_done/5_cancelled と project の 2_done を落とす
# --all で全件に戻す。--status を明示指定した場合もこの既定除外は効かない
python3 .claude/scripts/index.py --type meeting --date 2026-09-07 --with-calendar-ids

# ノート生成（vault相対パスを標準出力に返す。既存なら終了コード1）
# --project を付けると Cabinet/Notes/<案件名>/ の下に作り、フォルダが無ければ作る
python3 .claude/scripts/new_note.py --type task --title "C9500 見積依頼" \
    --project "大手町DC コアSW更改" --set due=2026-09-10 \
    --set 'project="[[大手町DC コアSW更改]]"'

# タグは YAML のインラインリスト形式で渡す
python3 .claude/scripts/new_note.py --type know-how --title "BGPのルートリフレクタ設計" \
    --set 'tags=[領域/ルーティング, メーカー/Cisco]'

# 締め（コミット・ffマージ・push）
bash .claude/scripts/close_day.sh
```
````

`--project` オプション（配置先フォルダ）と `--set project=...`（frontmatterのリンク）は別物である。両方渡すのが通常の使い方になる。`--set project=` の値は `"[[案件名]]"` のようにダブルクォートごと渡す。クォートが落ちると YAML が `[[案件名]]` をネストしたリストと解釈し、Obsidianのプロパティ表示が壊れるため。

- [ ] **Step 2: 開始モードの今日のタスク抽出を2回に分ける**

`SKILL.md:101`（開始モード ステップ8）を次に置き換える。

```markdown
8. 今日のタスクを2回の呼び出しで取る。`index.py --type task --due-before <今日>` で期限が今日以前のもの、`index.py --type task --status 2_doing` で進行中のものを取り、パスで重複を除いて結合する。1回の全件取得より出力が小さくなるため2回に分ける。既定で `4_done`/`5_cancelled` は落ちるので、完了済みタスクの除外を自分で行う必要はない。
```

- [ ] **Step 3: 更新モードの全件呼び出しを廃止する**

`SKILL.md:120-132`（更新モード ステップ11「今日新規に作った `context` の棚卸し」）を丸ごと削除し、次のステップに置き換える。

```markdown
11. **今日作ったタグの棚卸しを行う。このステップは更新モードの最後に置く。**
    - 対象の判定: `index.py --updated-on <今日>` の出力だけを使う。`tags` 列に現れる値のうち、`Cabinet/Bases/` のどの `.base` にも view が無いものを「今日新しく生まれたタグ」とする。**フィルタ無しの全件呼び出しは行わない。**
    - 出力: 該当があれば `## メモ` の先頭に `- ⓘ 今日作ったタグ: <値1>, <値2>（違っていればObsidianのタグ機能で改名。締めで .base に view を足します）` の1行を追記する。該当が無ければ何もしない。
    - **値は昇順に並べる。** 並び順が揺れると毎サイクル「構成が変わった」と誤判定される。
    - **同じ内容の行が既に `## メモ` にあれば追加しない。値の構成が変わっていれば既存のⓘ行を書き換える。**
    - **更新モードの最後に置くのは**、ステップ9・10より前だと、それらが新しいタグを作った場合にそのサイクルで告知されないため。
    - **締めモードではなく更新モードに置くのは、締めモードで書くと人間の目に触れないためである。** 締めは人間がその日のデイリーノートを見終わったあとに走る。
```

- [ ] **Step 4: 変更後の整合を確認する**

```bash
cd /home/asama/obsidian-vault
grep -n "index.py" .claude/skills/secretary/SKILL.md
grep -n "rename_context\|--contexts" .claude/skills/secretary/SKILL.md || echo "残存なし"
python3 -m pytest .claude/scripts/tests/ -q 2>&1 | tail -3
```

Expected: `index.py` の呼び出しがすべてフィルタ付き（`--type`/`--status`/`--date`/`--updated-on`/`--due-before` のいずれかを伴う）になっている。`## ノートの編集` 節にはまだ `rename_context` が残るため、この時点では `grep` が2行ほどヒットする（Task 11 で消す）。テストは `105 passed`。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/skills/secretary/SKILL.md
git commit -m "perf(skill): index.py のフィルタ無し全件呼び出しを廃止する

更新モード最後の棚卸しを --updated-on ベースに変え、今日のタスク抽出を
--due-before と --status 2_doing の2回に分けた。usage も新オプションに更新した。"
```

---

## Task 10: `SKILL.md` — 予定のチェックボックスとカレンダー絞り込み

**Files:**
- Modify: `.claude/skills/secretary/SKILL.md`

**Interfaces:**
- Consumes: Task 9 で更新した SKILL.md
- Produces: `## 今日の予定` の行書式、更新モードのチェック処理、カレンダー節の絞り込み3条件

- [ ] **Step 1: 行書式の定義を差し替える**

`SKILL.md:54`（`## デイリーノートの行書式` の第1項）を次に置き換える。

```markdown
- `## 今日の予定`: `- [ ] HH:MM-HH:MM [[議事録ノート名]]`。この1種類だけで、チェックボックスの無い行は存在しない。セクション末尾に `（取得元: ...）` の1行を置く。チェックは出席の合図として扱い、更新モードが対応する議事録ノートの `status` を `2_実施済` にする。
```

- [ ] **Step 2: カレンダー節に絞り込みを足す**

`SKILL.md:188`（`## カレンダー` の第2項）を次に置き換え、第3項以降は番号を繰り下げる。

```markdown
2. 見つかったすべてのソースから当日 00:00–23:59（ローカルタイムゾーン）のイベントを取得してマージする。
3. **取得したイベントを次の3条件で機械的に絞り込む。3つすべてを満たすものだけが `## 今日の予定` に載り、議事録ノートも作られる。この2つの対象は完全に一致させる。**
   - 時刻指定がある（`start.dateTime` を持つ。`start.date` だけの終日イベントは対象外）
   - 自分の `responseStatus` が `declined` でない
   - `attendees` に自分以外の参加者が存在する（`attendees` が無い、または自分だけのイベントは対象外）
4. 除外されるのは、終日イベント（休暇・当番）、辞退した通知系イベント、作業ウィンドウのブロック予定や個人の予定である。**絞り込みにAIの推測を入れない。**上の3条件だけで判定する。
```

代償として、終日で登録される休暇・当番・全社作業日はデイリーノートに現れない。これらを載せたい場合は時刻指定のイベントとして登録してもらう。この旨も同じ節に1行で書く。

- [ ] **Step 3: 更新モードにチェック済み予定行の処理を足す**

`SKILL.md:110`（更新モード ステップ4）の直後に、新しいステップを挿入する（以降の番号は繰り下げる）。

```markdown
5. **`## 今日の予定` のチェック済み行（`- [x]`）を出席の合図として扱う。** 対応する議事録ノートの `status` を `2_実施済` にする。状態はノート側の frontmatter が持つため、次のステップの全置換でチェックは復元され、冪等性が保たれる。
```

- [ ] **Step 4: 出欠推測のステップを書き換える**

現行の更新モード ステップ10（`SKILL.md:119`、終了時刻を過ぎた会議の事後構造化）を次に置き換える。`status` をAIが推測する記述を消す。

```markdown
    **終了時刻を過ぎた会議の事後構造化を行う。** `## メモ` の生メモから `## 決定事項` と `## アクション` を抽出して議事録ノートに書き、アクションはタスクノートとして起票して議事録からリンクする。**`status` はこのステップで変更しない。**出席の確定はチェックボックスが担い、未チェックのまま終了時刻を過ぎた行は締めモードの出欠確認に回る（`references/close.md` 参照）。
```

- [ ] **Step 5: 変更後の整合を確認する**

```bash
cd /home/asama/obsidian-vault
grep -n "今日の予定" .claude/skills/secretary/SKILL.md
grep -n "4_不参加" .claude/skills/secretary/SKILL.md
```

Expected: `## 今日の予定` の行書式が `- [ ] HH:MM-HH:MM [[議事録ノート名]]` に統一されている。`4_不参加` は締めモードの参照だけに現れ、更新モードのステップからは消えている。

- [ ] **Step 6: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/skills/secretary/SKILL.md
git commit -m "feat(skill): 予定行をチェックボックス化しカレンダーを3条件で絞る

出席の確定を人間のチェックに委ね、AIによる出欠推測を廃止した。時刻指定あり・
辞退していない・自分以外の参加者がいる、の3条件を満たすイベントだけを載せる。"
```

---

## Task 11: `SKILL.md` — タグ規則とノート配置ルール

**Files:**
- Modify: `.claude/skills/secretary/SKILL.md`

**Interfaces:**
- Consumes: Task 10 で更新した SKILL.md
- Produces: `## 分類基準` 節のタグ規則、ノート初期配置ルール、`rename_context.py` 記述の消滅

- [ ] **Step 1: `context` の規則1/2をタグ規則に差し替える**

`SKILL.md:168-175` の `context` に関する段落と規則1・規則2を丸ごと削除し、次に置き換える。

```markdown
### タグ規則

タグの第1階層は次の5つに固定する。**この5つ以外を第1階層に作らない。**

| 第1階層 | 例 | 目的 |
|---|---|---|
| `メーカー/` | `メーカー/Cisco` | 同一機種の障害・手配履歴の横断 |
| `領域/` | `領域/ルーティング` | 設計ノウハウと検証結果の再利用 |
| `種別/` | `種別/障害`・`種別/更改` | 案件の性格の区別 |
| `ベンダー/` | `ベンダー/○○電気` | 販社・工事会社の対応履歴 |
| `設備/` | `設備/大手町-CoreSW` | 特定設備に紐づく作業の追跡 |

タグを付ける対象は type で絞る。

| type | 付けるタグ |
|---|---|
| project | `種別/` は必須。`メーカー/` `ベンダー/` `設備/` は該当すれば付ける |
| task・meeting | **原則なし。**親案件と違う機器やベンダーが絡んだときだけ、その軸だけを付ける |
| know-how | `領域/` が主分類軸。`メーカー/` も該当すれば付ける |

- メーカーで検索したいとき、project ノートに `メーカー/Cisco` が付いていればその案件がヒットし、配下の task と meeting は `プロジェクト.base` の関連ノートビューで全部見える。task・meeting に同じタグを重ねても辿り着ける先は変わらない。
- 第2階層の値は既存の値から選ぶ。`index.py --updated-on <今日>` の `tags` 列と `Cabinet/Bases/` の view 名が既存値の手がかりになる。
- 既存値に該当が無ければ新しい第2階層を作ってよい。第1階層が固定されているため、増えても統制が効く。作った値は更新モードのステップ11がⓘ行で告知し、締めが `.base` に view を足す。
- タグは `new_note.py --set 'tags=[種別/更改, メーカー/Cisco]'` の形で最初から付ける。既存ノートに後から付ける場合は frontmatter を直接編集する。値の一括改名はObsidianのタグ機能（タグペインの右クリック→名前の変更）で行う。
```

- [ ] **Step 2: ノート配置ルールを足す**

`### タグ規則` の直後に次の節を足す。

```markdown
### ノートの初期配置

ノート作成時、案件が確定していれば `new_note.py --project "<案件名>"` で `Cabinet/Notes/<案件名>/` に作り、確定していなければ `--project` を付けず `Cabinet/Notes/` 直下に作る。

| きっかけ | 案件の確定度 | 初期の置き場所 |
|---|---|---|
| カレンダーから議事録を作る | 会議名から判定できることが多い | 案件フォルダ |
| `## メモ` から起票したタスク | 不明なことが多い | 直下 |
| 障害の発生 | project がまだ存在しない | project を作ってからその配下 |
| know-how | そもそも案件を持たない | 常に直下 |

- 案件フォルダ名は project ノート名と完全に一致させる。
- 案件フォルダに置くノートには `--set 'project="[[案件名]]"'` も併せて渡す。フォルダは置き場所、`project` プロパティは正典であり、`プロジェクト.base` の関連ノートビューはプロパティ側を見て動く。
- 複数案件にまたがる会議は、実体を主たる案件のフォルダに置いたまま `--set 'project=["[[A案件]]", "[[B案件]]"]'` とリストで書く。
- **直下に置いた未確定ノートは締めで棚卸しし、案件が決まったものを案件フォルダへ移す**（`references/close.md` の追加9）。移動してもリンクはObsidianが追従する。
- 案件を改名したときフォルダ名は自動追従しない。改名に気づいた時点でフォルダ名も直す。
```

- [ ] **Step 3: `## ノートの編集` 節から `rename_context.py` を消す**

`SKILL.md:199` の `context` に関する項目（`- context を1件だけ直す場合は、…` の1項目）を削除し、代わりに次の1項目を置く。

```markdown
- `tags` の変更は frontmatter を直接編集する。同じ値を持つ他のノートも直す必要がある場合は、Obsidianのタグ機能で一括改名する。
- `project` の変更は frontmatter を直接編集し、実体のフォルダも移す。プロパティとフォルダの同期はAIが担保する。
```

- [ ] **Step 4: 変更後の整合を確認する**

```bash
cd /home/asama/obsidian-vault
grep -n "context" .claude/skills/secretary/SKILL.md || echo "残存なし"
grep -n "rename_context" .claude/skills/secretary/SKILL.md || echo "残存なし"
```

Expected: どちらも `残存なし`。ただし `## デイリーノートの行書式` と `### 処理済みマーカーの判定規約` に残る「`context` の新しい値を提案した場合は ` → [[ノート名]]（context: 提案値）` となる」の記述も同時に消すこと。タグは提案の告知をⓘ行で行うため、メモ行への `（context: 提案値）` 追記は不要になる。処理済み判定は `→ [[...]]` と `→ 実行済み` の2種で足りる。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/skills/secretary/SKILL.md
git commit -m "feat(skill): context の規則を階層タグ規則に差し替える

第1階層5軸の固定とtype別の付与対象、ノートの初期配置ルールを追加した。
rename_context.py への参照はスクリプト削除に合わせて消した。"
```

---

## Task 12: `SKILL.md` — 更新モードに `Documents/` 振り分けを追加

**Files:**
- Modify: `.claude/skills/secretary/SKILL.md`
- Create: `Cabinet/Reference/.gitkeep`

**Interfaces:**
- Consumes: Task 11 で更新した SKILL.md
- Produces: 更新モードの `Documents/` 振り分けステップ、`Cabinet/Reference/` の実体

- [ ] **Step 1: `Cabinet/Reference/` を作る**

```bash
cd /home/asama/obsidian-vault
mkdir -p Cabinet/Reference
touch Cabinet/Reference/.gitkeep
ls Cabinet
```

Expected: `Cabinet` 配下に `Assets` `Bases` `Diary` `MEMORY.md` `Notes` `Reference` `Templates` が並ぶ。

- [ ] **Step 2: 更新モードに振り分けステップを足す**

更新モードのステップ列（Task 10 でステップ5を挿入済み）の末尾、タグ棚卸しステップの直前に次を挿入する。番号は挿入位置に合わせて振り直す。

```markdown
- **`Documents/` 直下を振り分ける。** `ls Documents` で直下のファイルを確認し、行き先が判定できるものだけを移す。
  - 特定の案件の資料である（ファイル名か中身に案件名・案件フォルダにあるノートの固有名詞が現れる）→ `Cabinet/Notes/<案件名>/` へ移す。
  - 案件横断で長く使う資料である（メーカー資料・規格書・製品カタログ）→ `Cabinet/Reference/` へ移す。
  - **どちらとも判定できないものは動かさない。**`Documents/` 直下に残したまま、`## 確認したいこと` に `- Documents/<ファイル名> の行き先（案件名 または Reference）を教えてください（1回目） →` の1行を足す。
  - **推測で振り分けない。**間違った案件フォルダに入った資料は、その案件を見ている限り見つからない。判定できないことを質問に出す方が安い。
  - 移動には `git mv` ではなく `mv` を使う。日中はコミットせず、締めの `close_day.sh` が `git add -A` でまとめて拾うため。
  - 既に同名のファイルが移動先にある場合は移さず、`## 確認したいこと` に上書きしてよいかを聞く。
```

- [ ] **Step 3: 変更後の整合を確認する**

```bash
cd /home/asama/obsidian-vault
grep -n "Documents" .claude/skills/secretary/SKILL.md
```

Expected: 更新モードに振り分けステップが1つ現れる。設計書12章「`Documents/` 走査を非目標とする」は前回設計の制約であり、本設計書4章がこれを覆しているため、走査の記述が入って正しい。

- [ ] **Step 4: コミットする**

```bash
cd /home/asama/obsidian-vault
git add Cabinet/Reference .claude/skills/secretary/SKILL.md
git commit -m "feat(skill): 更新モードに Documents 直下の振り分けを追加する

判定できるものだけを案件フォルダか Cabinet/Reference へ移し、判定できない
ものは直下に残して確認事項に出す。推測での振り分けは禁止する。"
```

---

## Task 13: `references/close.md` への分割と締めモードの拡張

**Files:**
- Create: `.claude/skills/secretary/references/close.md`
- Modify: `.claude/skills/secretary/SKILL.md`

**Interfaces:**
- Consumes: Task 12 で更新した SKILL.md
- Produces: 9ステップの締め手順を持つ `references/close.md`。`SKILL.md` の締めモード節は概要と参照だけになる

- [ ] **Step 1: `references/close.md` を作る**

```bash
cd /home/asama/obsidian-vault
mkdir -p .claude/skills/secretary/references
```

`.claude/skills/secretary/references/close.md` を新規作成する。

````markdown
# 締めモード

1日を締めてクリアデスクする。`/close` から起動する。時刻では自動起動しない。人間が退勤したかを時刻から推定できないため。

ステップは9つある。うち3つ（1・5・8）はAIだけで完結し、残り6つ（2・3・4・6・7・9）は人間の判断を要する。**6項目を1つずつ順に聞くと締めが6往復になり、毎日実行するのは現実的でない。まとめて1回で聞く。**

## 手順

1. **当日更新分を取得する。** `index.py --updated-on <今日>` を1回叩き、以降のステップはこの出力を使い回す。加えて期限見直し用に `index.py --type task --due-before <今日>` と `index.py --type task --status 2_doing` を叩く。**フィルタ無しの全件呼び出しは行わない。**
2. **予定とタスクを実績サマリーに書き換える。** `## 今日の予定` と `## 今日のタスク` を当日の実績に書き換える。`## 確認したいこと` と `## メモ` は変えない。**未チェックのまま終了時刻を過ぎた会議行は、下の確認リストの「出欠」項目に回す。**
3. **未処理の棚卸しを行う。** 未処理のメモ行（SKILL.md の「処理済みマーカーの判定規約」に従い、AIの接頭辞（`⚠`/`ⓘ`/`前日の未処理:`）を持たず、かつ `→ [[...]]` や `→ 実行済み` を含まない行）または未回答の確認事項（`→` の右が空の行）が残っていれば、`## メモ` の先頭に `- ⚠ 未処理 N件（内訳: メモ X件 / 確認 Y件）` の1行を追記する。**同じ内容の行が既にあれば追加せず、件数が変わっていれば既存の⚠行を書き換える。**
4. **MEMORY.md への昇格を判断する。** 当日更新分とデイリーノートから、人・状況についての持続的文脈を `Cabinet/MEMORY.md` へ `- <内容>（YYYY-MM-DD 記録）` の形式で1行追記する。**同じ内容の行が既にあれば追記しない。**
5. **`bash .claude/scripts/close_day.sh` を実行する。** 日付はブランチ名から取られ、`Cabinet/Diary/<その日>.md` の存在と frontmatter の `date` の一致が検査される。
6. **期限を見直す。** 期限超過タスクと、長く `2_doing` のまま止まっているタスクを一覧し、各件に「翌日 / 今週内 / 保留に落とす（`3_pending`） / 中止（`5_cancelled`）」の提案を根拠付きで添える。人間は違うものだけ直す。これで `due` が実態を反映し続けるため、今日のタスクの件数上限という対症療法が要らなくなる。
7. **`Documents/` 直下を片付ける。** 更新モードで判定しきれなかったファイルの行き先を確認し、直下を空にする。行き先が決まらないものは `Documents/未分類/` へ落として直下を空にし、未分類の件数をサマリーで報告する。**`close_day.sh` にこの検査は入れない。**資料の未振り分けはデータ破壊ではなく、ここで締めを止めると急いでいる日に締め自体を放棄することになるため。
8. **`Cabinet/Bases/` に view を足す。** その日のⓘ行が告知したタグの第2階層に新しい値が生まれていれば、対応する軸の `.base` に view を1本足す。書式は既存の view に合わせる（`type` の一致と `file.hasTag("<第1階層>/<第2階層>")` を `filters.and` に並べる）。このステップは人間の判断を要さない。
9. **直下の未確定ノートを案件フォルダへ移す。** `index.py --updated-on <今日>` の `path` 列が `Cabinet/Notes/<ファイル名>.md`（フォルダを挟まない）で、かつ `type` が `task` か `meeting` のものを一覧する。案件が決まったものは移動先の案件フォルダを確認してから `mv` で移し、`project` プロパティも合わせて書く。案件がまだ決まらないものは直下に残す。know-how は project を持たないため対象外。

`close_day.sh` は締めが成功すると HEAD を `main` に残す。そのまま `/close` を再実行すると日次ブランチ検査に引っかかり `日次ブランチ (daily/*) 上で実行してください` で終了コード1になる。これは正常な挙動である。

締めの最後に **`/loop` を停止する。`ScheduleWakeup` ツールを `stop: true` で呼ぶ。** 成否にかかわらず停止する。失敗は人間の介入を要する状態であり、自動処理を続ける理由が無いため。

## 人間への確認は1回にまとめる

ステップ2・3・4・6・7・9 の判断を、次の1メッセージにまとめて提示する。人間が1回答えれば全部片付く。

```
今日の締めです。次の6点を確認してください。まとめて答えていただければ反映します。

【1. 出欠】終了時刻を過ぎても未チェックの会議が N 件あります。不参加でよいですか。
  - 13:00-14:00 [[2026-09-07 ○○電気 機器納期調整]]

【2. 未処理】メモ X 件・確認事項 Y 件が未処理のまま残ります。明日に繰り越します。
  - 新宿の増設、光ケーブルの敷設は工事会社待ち

【3. MEMORY昇格】次の1行を Cabinet/MEMORY.md に足そうと思います。
  - ○○電気の窓口は田中さん（2026-09-07 記録）

【4. 期限見直し】期限を過ぎた / 長く進行中のタスクが N 件あります。提案は次のとおりです。
  - [[C9500 見積依頼]] 期限 今日 → 翌日（先方回答待ちのため）
  - [[新宿局 増設 構成図の修正]] 進行中12日 → 3_pending（工事会社待ちのため）

【5. Documents】行き先が決まらない資料が N 件あります。
  - 構成図v3.pdf → 案件名を教えてください（不明なら Documents/未分類/ へ落とします）

【6. ノート移動】直下にあるノートのうち、案件が決まったものを移します。
  - [[C9500後継機のEOSL確認]] → Cabinet/Notes/大手町DC コアSW更改/ でよいですか

違うものだけ指摘してください。指摘が無ければこの内容で締めます。
```

- 該当が無い項目は見出しごと省く。6項目すべてが空なら確認を出さずそのまま締める。
- 人間の回答を反映してから、ステップ5の `close_day.sh` を実行する。**確認より先にコミットしない。**
- 回答が返らないまま放置された場合も締めを完了させる。**締めをしないと翌日が止まる。**モード判別表は前日の日次ブランチに居残ったまま `/today` を起動すると停止する設計であり、締めを飛ばすと翌朝の秘書ループが立ち上がらない。提案どおりに反映し、反映内容をデイリーノートの `## メモ` に `- ⚠ 締めの確認に回答が無かったため提案どおり反映しました` の1行で残す。
````

- [ ] **Step 2: `SKILL.md` の締めモード節を概要に置き換える**

`SKILL.md:138-146`（`## 締めモード` 節の全体）を次に置き換える。

```markdown
## 締めモード

1日を締めてクリアデスクする。9ステップからなり、うち6つが人間の判断を要する。**その6つは1つずつ聞かず、1回の確認にまとめて提示する。**

**詳細手順は `references/close.md` が正典。** 締めモードを起動したらまずそれを読む。締めは1日1回しか使わないため、開始・更新のたびに読み込まなくてよいよう分けている。

概要は次のとおり。

| | ステップ | 人間の判断 |
|---|---|---|
| 1 | 当日更新分の取得 | 不要 |
| 2 | 予定・タスクを実績サマリーへ書き換え | 要 |
| 3 | `## メモ` `## 確認したいこと` の未処理棚卸し | 要 |
| 4 | MEMORY.md への昇格判断 | 要（該当時のみ） |
| 5 | `close_day.sh` の実行 | 不要 |
| 6 | 期限の見直し | 要 |
| 7 | `Documents/` 直下の片付け | 要 |
| 8 | `Cabinet/Bases/` の view 追加 | 不要 |
| 9 | 直下の未確定ノートを案件フォルダへ移動 | 要 |

未処理のメモ行や未回答の確認事項は、`- ⚠ 未処理 N件` の行を足したうえでデイリーノートにそのまま残す。強制的なノート変換は行わない。翌朝の開始モードがこの行を見つけると、新しいデイリーノートの `## メモ` に繰越の1行を書く。
```

- [ ] **Step 3: `/close` コマンドの説明を合わせる**

`.claude/commands/close.md` の本文を次に置き換える。

```markdown
`secretary` スキルを締めモードで起動する。手順の正典は `.claude/skills/secretary/references/close.md`。9ステップのうち人間の判断を要する6項目は、1回の確認にまとめて提示される。
```

- [ ] **Step 4: 変更後の整合を確認する**

```bash
cd /home/asama/obsidian-vault
wc -l .claude/skills/secretary/SKILL.md .claude/skills/secretary/references/close.md
grep -n "references/close.md" .claude/skills/secretary/SKILL.md .claude/commands/close.md
python3 -m pytest .claude/scripts/tests/ -q 2>&1 | tail -3
```

Expected: `SKILL.md` から締めの詳細手順が消えて行数が減り、`references/close.md` が新規に存在する。両ファイルから `references/close.md` への参照が引ける。テストは `105 passed`。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/skills/secretary .claude/commands/close.md
git commit -m "feat(skill): 締めを9ステップに拡張し references/close.md へ分割する

期限見直し・Documents片付け・Bases view追加・未確定ノート移動の4ステップを
追加し、人間の判断を要する6項目を1回の確認にまとめる手順を定めた。"
```

---

## Task 14: `CLAUDE.md` / `README.md` / `settings.local.json` の更新

**Files:**
- Modify: `.claude/CLAUDE.md`, `README.md`, `.claude/settings.local.json`

**Interfaces:**
- Consumes: Task 2〜13 の全変更
- Produces: 新構成に一致した取扱説明書・人間向け案内・権限設定

**`.claude/settings.local.json` について**: 実測した現在のユーザー設定（`~/.claude/settings.json`）の `permissions.deny` に `Edit(**/.claude/settings.local.json)` は含まれていないため、通常は編集できる。**それでもブロックされた場合は、別の技術的手段で回避せず即座に停止し、BLOCKED として報告して人間に編集を依頼すること。**依頼する内容は Step 3 の差分そのものを提示する。

- [ ] **Step 1: `.claude/CLAUDE.md` を更新する**

次の6か所を書き換える。

1. **フォルダ構成のツリー**（`## フォルダ構成` のコードブロック）を次に置き換える。

```
vault/
├── Documents/          ← 人間がドラッグ&ドロップで投入する資料。締め完了時点で直下は空
├── Cabinet/            ← Claude Code専管ゾーン
│   ├── Notes/          ← 案件フォルダ <案件名>/ と、直下の know-how・案件未確定ノート
│   ├── Reference/      ← 案件横断・長寿命の資料（メーカー資料・規格書）
│   ├── Diary/          ← デイリーノート。当日分が人間との唯一の接点、それ以外は過去分
│   ├── Assets/         ← Obsidianの添付ファイル
│   ├── Templates/      ← 5本
│   ├── Bases/          ← .base 4本。締めがviewを追加する
│   └── MEMORY.md       ← 長期記憶
├── README.md           ← 人間向けの使い方
├── .obsidian/          ← Obsidianの設定。gitに追跡している
└── .claude/
```

2. **フラット規約の撤回**。`Cabinet/Notes/ はサブフォルダを作らずフラットに保つ。type はフォルダに依存せず判定されるため、フォルダによる分類は不安定な意思決定を強いるだけになる。` の1段落を次に置き換える。

```markdown
`Cabinet/Notes/` は案件フォルダ `<案件名>/` を持つ。project ノート・配下の task・meeting・案件資料をそこに集約し、案件単位の閲覧と資料紐付けを成立させる。know-how と案件未確定のノートは直下に置く。`type` の判定は引き続き frontmatter の `type` プロパティで行い、フォルダには依存させない。フォルダは置き場所の分類であって判定基準ではない。案件フォルダ名は project ノート名と一致させる。
```

3. **プロパティ表**を次に置き換える。

```markdown
| プロパティ | task | project | meeting | know-how |
|---|---|---|---|---|
| type | ● | ● | ● | ● |
| date | ● | ● | ● | ● |
| status | ● | ● | ● | |
| due | ○ | ○ | | |
| done | ○ | | | |
| project | ○ | | ○ | |
| tags | ○ | ● | ○ | ● |
| calendar_event_id | | | ● | |
| calendar_series_id | | | ○ | |

`tags` は階層タグで、第1階層を `メーカー` / `領域` / `種別` / `ベンダー` / `設備` の5つに固定する。付ける対象は type で絞る（project は `種別/` 必須、know-how は `領域/` が主軸、task・meeting は原則なし）。規則の正典は `.claude/skills/secretary/SKILL.md` の「タグ規則」節。`project` は `"[[案件名]]"` またはそのリストで親案件を指す。
```

4. **チェックボックス規約**。`## デイリーノートの運用` の表の `## 今日の予定` 行の書式を `- [ ] HH:MM-HH:MM [[議事録ノート名]]` に直し、人間側を「読む、出席した会議にチェックを入れる」に直す。続く段落 `チェックボックスを使うのは ## 今日のタスク だけ。…予定側は押しても意味を持たせる先が無いため素の箇条書きにする。` を次に置き換える。

```markdown
`## 今日の予定` と `## 今日のタスク` の両方でチェックボックスを使う。人間がチェックしたタスク行を更新モードが完了の合図として読み、対応するタスクノートを `status: 4_done` / `done: <今日>` にする。予定行のチェックは出席の合図で、対応する議事録ノートを `status: 2_実施済` にする。`## 今日の予定` に載るのは、時刻指定があり・辞退しておらず・自分以外の参加者がいるイベントだけで、議事録ノートを作る対象と完全に一致する。
```

5. **`## プロパティ更新はClaude Code経由を正とする` 節**から `context` と `rename_context.py` の記述を消す。`status` / `due` / `done` / `context` の列挙を `status` / `due` / `done` / `tags` / `project` に直し、末尾2文（`context の値を複数ノートにまたがって付け替える場合は…単発のものは空にする。`）を次に置き換える。

```markdown
`tags` の値を複数ノートにまたがって付け替える場合はObsidianのタグ機能で一括改名する。`project` の変更は frontmatter と実体のフォルダの両方を直す。
```

6. **`## スクリプト` 節**から `rename_context.py` の1行を削除し、`index.py` の説明に既定除外を1文足す。

```markdown
- `.claude/scripts/index.py`: ノートの索引をTSVで出力する。`Cabinet/Notes/` の一覧を読む唯一の経路。`rglob` で案件フォルダも走査する。既定で完了物（`task` の `4_done`/`5_cancelled`、`project` の `2_done`）とカレンダーID列を落とす。
- `.claude/scripts/new_note.py`: テンプレートからノートを1件作る。`--project` で案件フォルダへ配置する。
```

- [ ] **Step 2: `README.md` を更新する**

次の4か所を書き換える。

1. `## 使い方` の第4項の直前に1項を挿入し、以降を繰り下げる。

```markdown
4. 出席した会議は `## 今日の予定` の行にチェックを入れる。次の更新で議事録ノートが「実施済」になる。
```

2. `## どこに何があるか` の表に2行を足し、`Cabinet/Notes/` の説明を直す。

```markdown
| `Cabinet/Notes/<案件名>/` | 案件ごとのフォルダ。プロジェクト・タスク・議事録・資料がまとまっている |
| `Cabinet/Notes/` の直下 | ノウハウと、まだ案件が決まっていないノート |
| `Cabinet/Reference/` | 案件をまたいで使う資料。メーカー資料・規格書 |
```

3. `## ノートの4種類` の `type プロパティで区別する。フォルダでは分けない。` を次に置き換える。

```markdown
`type` プロパティで区別する。フォルダは案件で分ける（種類では分けない）。
```

4. `## 資料の紐付け` を次に置き換える。

```markdown
`Documents/` にドラッグ&ドロップした資料は、次の更新で案件フォルダか `Cabinet/Reference/` へ自動で振り分けられる。どちらか判定できないものは `## 確認したいこと` で行き先を聞かれる。1日の終わりには `Documents/` の直下は空になる。

会議の資料は議事録ノートの `## 資料` からリンクされる。カレンダーの添付とdescription内のURLは自動で貼られる。
```

あわせて末尾の `## 中身を知りたいとき` に1行足す。

```markdown
- 今回の再構成の設計: `.claude/specs/2026-09-07-vault-restructure-design.md`
```

- [ ] **Step 3: `.claude/settings.local.json` を更新する**

`permissions.allow` から `rename_context.py` の2行を削除し、`Cabinet/Reference/**` と `Documents/**` の4行を足す。結果は次になる。

```json
{
  "permissions": {
    "allow": [
      "Bash(git status *)",
      "Bash(git log *)",
      "Bash(git branch --show-current)",
      "Bash(git branch --list *)",
      "Bash(git checkout -b daily/*)",
      "Bash(git checkout daily/*)",
      "Bash(python3 .claude/scripts/index.py)",
      "Bash(python3 .claude/scripts/index.py *)",
      "Bash(python3 .claude/scripts/new_note.py)",
      "Bash(python3 .claude/scripts/new_note.py *)",
      "Bash(bash .claude/scripts/close_day.sh)",
      "Bash(bash .claude/scripts/close_day.sh *)",
      "Bash(python3 -m pytest *)",
      "Edit(Cabinet/Diary/**)",
      "Write(Cabinet/Diary/**)",
      "Edit(Cabinet/MEMORY.md)",
      "Edit(Cabinet/Notes/**)",
      "Write(Cabinet/Notes/**)",
      "Edit(Cabinet/Reference/**)",
      "Write(Cabinet/Reference/**)",
      "Edit(Documents/**)",
      "Write(Documents/**)",
      "mcp__claude_ai_Google_Calendar__list_events",
      "mcp__claude_ai_Google_Calendar__list_calendars",
      "mcp__claude_ai_Google_Calendar__search_events",
      "mcp__claude_ai_Google_Calendar__get_event"
    ]
  }
}
```

`Documents/**` への Write/Edit 許可が要るのは、更新モードと締めが直下のファイルを移動し、行き先未定のものを `Documents/未分類/` へ落とすため。ファイルの移動そのものは `mv`（Bash）で行うが、Bashコマンド経由の移動は workspace-guard の対象外であり、Write/Edit の許可は `Documents/未分類/` に案内ファイルを置くなどの編集経路に効く。

- [ ] **Step 4: 全体を検証する**

```bash
cd /home/asama/obsidian-vault
python3 -m json.tool .claude/settings.local.json > /dev/null && echo "JSON OK"
grep -rn "context\|rename_context" .claude/CLAUDE.md README.md .claude/settings.local.json || echo "残存なし"
grep -rn "フラットに保つ\|フラット格納" .claude/CLAUDE.md README.md || echo "フラット規約の残存なし"
python3 -m pytest .claude/scripts/tests/ -q 2>&1 | tail -3
```

Expected: `JSON OK`。`残存なし` と `フラット規約の残存なし`。テストは `105 passed`。

- [ ] **Step 5: コミットする**

```bash
cd /home/asama/obsidian-vault
git add .claude/CLAUDE.md README.md .claude/settings.local.json
git commit -m "docs: 取扱説明書とREADMEと権限を新構成に合わせる

案件フォルダとCabinet/Referenceを追記し、プロパティ表のcontextをtags/projectに
差し替えた。フラット規約とチェックボックス規約の撤回も反映した。"
```

---

## Self-Review 記録

**1. 設計書の網羅性** — 設計書の各章と実装タスクの対応。

| 設計書 | タスク |
|---|---|
| 1章 目的と背景 | 実装対象なし（背景の記述） |
| 2章 現状の問題 | Task 3（列削減）、Task 4（既定除外）、Task 9（全件呼び出し廃止） |
| 3章 データモデル（タグ第1階層5軸・付与対象） | Task 7（テンプレート）、Task 11（タグ規則）、Task 14（プロパティ表） |
| 4章 フォルダ構成（案件フォルダ・Reference・初期配置） | Task 2（rglob）、Task 6（`--project`）、Task 11（初期配置）、Task 12（Reference・Documents振り分け）、Task 13（追加9） |
| 5章 Bases | Task 1（実機検証）、Task 8（書き直し） |
| 6章 スクリプトの変更 | Task 2〜6。`close_day.sh` は変更なしの決定に従い触らない |
| 7章 スキルの変更 | Task 9（出力量削減）、Task 10（予定行）、Task 11（タグ規則）、Task 12（Documents振り分け）、Task 13（締め拡張・分割） |
| 8章 実機で検証すべきこと | Task 1 |
| 9章 スコープ外 | 実装しない。`.superpowers/sdd/` と `.pytest_cache/` の片付けは本計画の対象外 |
| 10章 覆す既存決定 | Task 14（CLAUDE.md:31 フラット規約・CLAUDE.md:73 チェックボックス規約）、Task 10（SKILL.md:186-189 カレンダー節） |
| 付録 運用実例 | Task 6・Task 7・Task 11 の期待値の根拠として使用 |

**未カバーだったため追加した項目（3件）**:

- **`Cabinet/Reference/` の実体作成**。設計書4章がフォルダ構成に含めているが、どのタスクで作るかが指示に無かった。最初に使う Task 12 で作ることにした。
- **案件改名時のフォルダ追従**。設計書4章が「改名時にフォルダも直す処理を締めか更新モードに入れる」と要求している。Task 11 の「ノートの初期配置」節に1行として入れた。締めのステップ9は「直下から案件フォルダへの移動」であって改名追従ではないため、別建てにしている。
- **`/close` コマンド説明の同期**。`.claude/commands/close.md` が締めの手順を要約しており、`references/close.md` への分割で参照先が変わる。Task 13 の Step 3 に入れた。

**意図的にカバーしない項目（2件）**: 設計書9章のスコープ外事項（`.superpowers/sdd/` と `.pytest_cache/` の片付け、設備台帳）は破壊的操作またはtypeの追加であり、設計書自身が「ユーザーの指示を待つ」「作らない」と決めているため、タスクを立てない。

**2. プレースホルダ走査** — 「TBD」「TODO」「適切な」「後述」「未定」「XXX」を全文検索し、いずれも該当なし（`Documents/未分類/` の説明にある「行き先未定」だけが「未定」に引っかかるが、これは運用上の状態を指す語であってプレースホルダではない）。「上記」は3か所あり、すべて直前の具体的な列挙（Task 1 の Create 4ファイル、Task 3 の既定10列、`## 変更するファイル` 表の行）を指す参照で、内容の先送りではない。

Task 1 の「結果記入欄」だけが空欄だが、これは人間が実機で埋める入力欄であり、設計書8章が「推測で実装を進めない箇所」と定めたものの受け皿である。埋まるまで Task 8 に着手しないことを Task 1 と Task 8 の両方に明記し、Task 8 には結果ごとの分岐表を先に書いてある。

**3. 型・名前の一貫性**:

- `index.py` の列名 `tags` / `project` は Task 3 で定義し、Task 4 の `matches()`（`row["due"]`）、Task 8 の `.base` の `order`、Task 9 の usage、Task 13 のステップ9（`path` 列の形）が同じ名前を使う。
- 列の添字は Task 3 で `path`=0 … `mtime`=9 に確定し、Task 4 のテストがすべて `row[8]`（`title`）を参照する。Task 3 で既存テストの `row[7]` を `row[8]` に直す作業を明示している。
- `--due-before` は Task 4 で「指定日を含む」と定義し、Task 9 の開始モード ステップ8 と Task 13 のステップ1が同じ意味で使う。
- `--with-calendar-ids` は Task 3 で定義し、Task 9 の usage が同じ綴りで参照する。
- `new_note.py` の `--project`（配置先フォルダ）と `--set project=`（frontmatterのリンク）は別物であり、Task 6 で両立させ、Task 9 と Task 11 が両方を渡す例を示している。
- `LIST_SEPARATOR = ","` は Task 3 で定義し、Task 3 の全テストの期待値（`"種別/更改,メーカー/Cisco"`）と一致する。
- 終了コード規約（0/1/2）は Task 6 で維持し、Task 9 の usage コメントが同じ意味で参照する。
- `references/close.md` の参照は Task 13 で作られ、Task 10（更新モード ステップ10）、Task 11（ノートの初期配置）、Task 13（SKILL.md 締めモード節）、`.claude/commands/close.md` の4か所から同じパスで引かれる。
- テスト件数は 95 →（+3）98 →（+7）105 →（+9）114 →（−22）92 →（+7）99 →（+4）103 →（−4+6）105 と推移し、各タスクの Step で期待値として明記している。
