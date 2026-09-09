# スクリプト

`index.py`・`new_note.py`・`close_day.sh` の呼び出し例をまとめたチートシートである。

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
# --project を付けると Cabinet/Notes/<案件名>/ の下に作り、フォルダが無ければ作る
python3 .claude/scripts/new_note.py --type task --title "C9500 見積依頼" \
    --project "大手町DC コアSW更改" --set due=2026-09-10 \
    --set 'project="[[大手町DC コアSW更改]]"'

# タグは YAML のインラインリスト形式で渡す
python3 .claude/scripts/new_note.py --type know-how --title "BGPのルートリフレクタ設計" \
    --set 'tags=[領域/ルーティング, メーカー/Cisco]'

# blocked_by は project 同様 "[[タスク名]]" のリンク形式で渡す
python3 .claude/scripts/new_note.py --type task --title "C9500 納品確認" \
    --project "2026-01-15_大手町DC コアSW更改" \
    --set 'blocked_by=["[[C9500 見積依頼]]"]'

# 締め（コミット・ffマージ・push）
bash .claude/scripts/close_day.sh
```

`--project` オプション（配置先フォルダ）と `--set project=...`（frontmatterのリンク）は別物である。両方渡すのが通常の使い方になる。`--set project=` の値は `"[[案件名]]"` のようにダブルクォートごと渡す。クォートが落ちると YAML が `[[案件名]]` をネストしたリストと解釈し、Obsidianのプロパティ表示が壊れるため。
