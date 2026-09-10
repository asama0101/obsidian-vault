# スクリプト

`index.py`・`new_note.py`・`close_day.sh` の呼び出し例をまとめたチートシートである。

## 挙動の詳細

- `index.py`: ノートの索引をTSVで出力する。`1_Notes/`・`2_know-how/`・`3_Inbox/`・`4_Archive/`、およびvault直下のprojectノートの一覧を読む唯一の経路。`rglob` で案件フォルダも走査する。既定で完了物（`task` の `4_done`/`5_cancelled`、`project` の `2_done`）とカレンダーID列を落とす。
- `new_note.py`: テンプレートからノートを1件作る。`--type project` は `--project` を無視し、vault直下に `<title>.md` をフラット配置すると同時に `1_Notes/<title>/` フォルダを作る。`--type task`/`meeting` は `--project` を指定すると `1_Notes/<project>/task/` または `1_Notes/<project>/meeting/` に配置する（`project` は既存フォルダ名をそのまま使う文字列で、曖昧一致や自動検索は行わない）。`--project` を指定しない場合、`--type task`/`meeting` は `3_Inbox/` に、`--type know-how` は `2_know-how/` に作る。
- `close_day.sh`: 締めのgit操作。日付はブランチ名から取り、`6_Cabinet/Diary/<その日>.md` の存在と frontmatter の `date` の一致を検査してからコミットする。`date` は前後の空白・引用符・復帰文字を落として正規化してから比較するため、Obsidianのプロパティパネルが引用符付きで書いた値でも通る。`git add -A` の後にステージした差分が無ければ `コミットする変更が無いためコミットをスキップしました` と出力してコミットを飛ばし、`main` へのマージへ進む。これにより、同じ日次ブランチ上で締めを繰り返してもエラーにならない。ただし締めが成功すると HEAD は `main` に残るため、そのまま締め処理を再実行した場合は日次ブランチ検査に引っかかり `日次ブランチ (daily/*) 上で実行してください` で終了コード1になる。

```bash
# 索引（列: path type status due done tags project date title mtime blocked_by、ヘッダ行なし、11列）
# tags と project が多値のときはカンマ区切りで1セルに入る
python3 .claude/scripts/index.py [--type task,meeting] [--status 1_todo,2_doing] \
    [--date 2026-09-07] [--updated-on 2026-09-07] [--due-before 2026-09-07] \
    [--with-calendar-ids] [--all]

# --with-calendar-ids を付けると末尾に calendar_event_id calendar_series_id が増えて13列になる
# 既定では task の 4_done/5_cancelled と project の 2_done を落とす
# --all で全件に戻す。--status を明示指定した場合もこの既定除外は効かない
python3 .claude/scripts/index.py --type meeting --date 2026-09-07 --with-calendar-ids

# ノート生成（vault相対パスを標準出力に返す。既存なら終了コード1）
# --project を付けると 1_Notes/<案件名>/ の下に作り、フォルダが無ければ作る
python3 .claude/scripts/new_note.py --type task --title "C9500 見積依頼" \
    --project "大手町DC コアSW更改" --set due=2026-09-10 \
    --set 'project="[[大手町DC コアSW更改]]"'

# タグは YAML のインラインリスト形式で渡す（--project を付けなければ 2_know-how/ に作る）
python3 .claude/scripts/new_note.py --type know-how --title "BGPのルートリフレクタ設計" \
    --set 'tags=[領域/ルーティング, メーカー/Cisco]'

# blocked_by は project 同様 "[[タスク名]]" のリンク形式で渡す
python3 .claude/scripts/new_note.py --type task --title "C9500 納品確認" \
    --project "大手町DC コアSW更改" \
    --set 'blocked_by=["[[C9500 見積依頼]]"]'

# 締め（コミット・ffマージ・push）
bash .claude/scripts/close_day.sh
```

`--project` オプション（配置先フォルダ）と `--set project=...`（frontmatterのリンク）は別物である。両方渡すのが通常の使い方になる。`--set project=` の値は `"[[案件名]]"` のようにダブルクォートごと渡す。クォートが落ちると YAML が `[[案件名]]` をネストしたリストと解釈し、Obsidianのプロパティ表示が壊れるため。
