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

| セクション | 行書式 | AI | 人間 |
|---|---|---|---|
| `## 今日の予定` | `- HH:MM-HH:MM [[議事録ノート名]]` | 全置換で再生成 | 読む |
| `## 今日のタスク` | `- [ ] [[タスクノート名]] <状態>` | 全置換で再生成、チェック済み行を完了として処理 | 読む、終わったタスクにチェックを入れる |
| `## 確認したいこと` | `- <質問>（N回目） →` | 質問行を追加、回答済み行を削除 | `→` の右に回答 |
| `## メモ` | 自由記述 | 行の後ろにリンクを追記 | 自由記述 |

チェックボックスを使うのは `## 今日のタスク` だけ。人間がチェックした行を更新モードが完了の合図として読み、対応するタスクノートを `status: 4_done` / `done: <今日>` にする。予定側は押しても意味を持たせる先が無いため素の箇条書きにする。

AIは人間が書いた文言を書き換えない。処理済みのメモ行は削除せず、` → [[ノート名]]` を追記する。`context` を新規に提案したときは ` → [[ノート名]]（context: 提案値）` になる。処理済みかどうかは行内に `→ [[...]]` を含むかで判定する（行末では判定しない）。判定規約は `.claude/skills/secretary/SKILL.md` が正典。

締めで `Today.md` は `Cabinet/Diary/<date>.md` へリネーム移動され、翌朝また新規に作られる。

## MEMORY.md の運用

`Cabinet/MEMORY.md` は人・状況についての持続的文脈を保存する長期記憶。「どうやるか」は `know-how`、「今何が前提として動いているか」はMEMORY.md。締めが昇格判断を行い、該当があれば1行追記する。開始処理はこのファイルを読んでブリーフィングの前提知識に使う。

## 読み取りは索引スクリプト経由を正とする

`Cabinet/Notes/` を1件ずつ読んではいけない。一覧が必要なときは必ず `.claude/scripts/index.py` を使う。個別のReadは、実際にそのノートを編集するときだけ行う。ノート件数に比例するコストを常時ループに持ち込まないため。

## プロパティ更新はClaude Code経由を正とする

`status` / `due` / `done` / `context` をObsidianのプロパティパネルで直接書き換えることを前提にしない。自然言語の指示を受けたら、該当ノートのfrontmatterを直接編集する。`context` の値を複数ノートにまたがって付け替える場合は `.claude/scripts/rename_context.py` を使う。`context` は繰り返し現れるまとまりに付ける値であり、単発のものは空にする。

## 通知は行わない

秘書ループは通知を送らない。伝えたいことは `Today.md` に書く。会議直前のリマインドはカレンダーアプリ本体に委ねる。

## Git運用: 日次ブランチ

ノートを新規作成・編集する前に、必ず今日の日次ブランチ `daily/YYYY-MM-DD` にいることを確認する。無ければ `main` から `git checkout -b daily/<今日の日付>` で作る。日中はコミットしない。締めが `close_day.sh` で1コミットにまとめ、`main` へ fast-forward マージして push する。

## コマンド

- `/today`: 秘書ループの開始または更新。`Today.md` の有無と、その `date` が今日かで判別する。`date` が今日でなければ前日分が締められていないので、報告して停止する。更新は `/loop` から30分間隔で自動的に呼ばれる。
- `/intake`: 会話に貼られたメール・チャット本文をノート化する。
- `/close`: 1日を締める。時刻では自動起動しない。

手順の詳細は `.claude/skills/secretary/SKILL.md` を参照する。設計の経緯は `.claude/specs/2026-09-07-vault-secretary-redesign-design.md` にある。

## スクリプト

- `.claude/scripts/index.py`: ノートの索引をTSVで出力する。`Cabinet/Notes/` の一覧を読む唯一の経路。
- `.claude/scripts/new_note.py`: テンプレートからノートを1件作る。
- `.claude/scripts/rename_context.py`: `context` の値を一括で付け替える。
- `.claude/scripts/close_day.sh`: 締めのgit操作。

テストは `python3 -m pytest .claude/scripts/tests/` で実行する。
