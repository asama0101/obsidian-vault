# CLAUDE.md — このvaultの取扱説明書

個人利用のObsidian vault。Obsidian（`Today.md`・Bases）を「見る場所」、
Claude Codeを「操作・秘書業務を回す場所」として役割分担する。

## 役割分担

秘書業務を7機能（捕捉・判断・構造化・追跡・準備・報告・締め）に分解し、
人間とClaude Codeの担当を次のように固定する。

- **人間がやること**: ①生の情報を`Inbox/`に書き留める、または`intake`
  スキルで直接渡す。②AIが確信を持てない判断（分類不明・新規プロジェクト
  起票の可否等）に答える。`Today.md`の`## メモ`欄への自由記述、または
  `Review/`配下のノートの`## 要判断`欄への記入。`Today.md`と6本の
  `.base`を読むこと。Claude Codeを起動すること（`/today`を1日の最初に
  1回）。
- **Claude Codeがやること**: ③〜⑦（構造化・追跡・準備・報告・締め）の
  全て。`Inbox/`の仕分け、`Cabinet/Notes/`への構造化、期限・進捗の追跡、
  会議前の準備、`Today.md`への報告、クリアデスクの実行。

人間がObsidianのファイルエクスプローラーを操作して`Cabinet/`配下を直接
編集・整理することは想定しない。

## フォルダ構成

```
vault/
├── Inbox/            ← 人間の書き込みゾーン（1件1ノート、フォルダ一覧は見ない。Inbox.baseで一覧を見る）
├── Review/           ← AIの確認待ちゾーン（1件1ノート、Review.baseで一覧を見る。`## 要判断`欄に人間が回答する）
├── Today.md           ← ピン留め。ブリーフィング（Claude Code管理）＋メモ（人間が自由記述）
├── Inbox.base／Review.base／タスク.base／プロジェクト.base／議事録.base／ノウハウ.base
├── Cabinet/           ← Claude Code専管ゾーン（人間は直接編集しない）
│   ├── Diary/         ← 締め処理でリネーム移動された過去のTodayの記録
│   ├── Notes/         ← task/project/meeting/know-howを`type`で区別してフラット格納
│   ├── Documents/     ← 資料保管庫（都度の自然言語指示で手動投入、専用Skillなし）
│   ├── Assets/        ← 添付ファイル
│   ├── Templates/     ← テンプレート
│   └── MEMORY.md      ← 長期記憶。人・状況についての持続的文脈（締め処理が昇格判断で追記）
└── .claude/
```

## ノート種別とプロパティ

`type`プロパティで4種を判別する: `task` / `project` / `meeting` /
`know-how`。`Inbox/`配下のノートは分類前の一時状態のため`type`を持たない
（`date`のみ）。`Review/`配下のノートも同様に確認待ちの一時状態のため
`type`を持たない（`date`と`source`のみ）。`Cabinet/Diary/`のノート
（締め処理でリネームされた過去の`Today.md`）も`type`を持たない
（`date`のみ）。

| プロパティ | task | project | meeting | know-how | Inbox | Review | Diary |
|---|---|---|---|---|---|---|---|
| type | ● | ● | ● | ● | | | |
| status | ●(1_todo/2_doing/3_pending/4_done/5_cancelled) | ●(1_active/2_done) | | | | | |
| due | ○ | ○ | | | | | |
| check | ○ | | | | | | |
| date | ● | | ● | ● | ● | ● | ● |
| context | ○ | ○ | ○ | ○ | | | |

`meeting`型のノートは追加で`calendar_event_id`／`calendar_series_id`
（カレンダー連携用）を持つ。`Review/`配下のノートは追加で`source`
（発生元の自由記述、例: `intake`／`closing`）を持つ。上の表には含めない。

## 更新履歴セクション

`task`・`project`・`know-how`の本文末尾は`## 更新履歴`セクションを持つ。
ノート作成時に`- {{date}}: 作成`で初期化され、Claude Codeがそのノートの
状態・内容を変更するたびに`- {{date}}: <変更内容>`を追記する。frontmatter
の`date`（作成日）だけでは事後の更新を日付でたどれないため、更新の記録は
本文側のこのセクションで管理する。`meeting`・`Inbox`・`Review`・
`Cabinet/Diary`のノートはこのセクションを持たない。

## プロパティ更新はClaude Code経由を正とする

`status`/`check`をObsidianのプロパティパネルで直接書き換えることを
前提にしない。自然言語の指示を受けたら、該当ノートのfrontmatterを直接
編集する。ステータス値は上表の許容値のみを使う。`task`/`project`/
`know-how`のノートを編集した場合は、`## 更新履歴`に変更内容を1行
追記する。

## `Today.md`の運用

`Today.md`はvault直下に常に1つだけ存在する単一ファイル。`## ブリーフィング`
（今日の予定・今日のタスク・一言コメント。`today`スキルの開始/更新モードが
自動更新する）と`## メモ`（人間が自由に書き込む欄）の2セクションを持つ。
「メモしておいて」等の指示は`## メモ`へ追記する形で反映する。締め処理で
`Today.md`は`Cabinet/Diary/{{date}}.md`へリネーム移動され、翌朝また新規に
作成される。日常的な予定・タスク確認は`Today.md`で完結させ、資料・過去
記録を横断的に探す時だけBasesをたどる。

## MEMORY.mdの運用

`Cabinet/MEMORY.md`は、人・状況についての持続的文脈（関係者の役割、
繰り返し発生する前提条件など）を保存する長期記憶ファイル。`know-how`型
（手順・ノウハウ）とは役割を分ける：「どうやるか」はknow-how、「今何が
前提として動いているか」はMEMORY.md。締め処理が1日の終わりに「昇格判断」
（今日の内容に持続的文脈と言えるものがあるか）を行い、該当があれば追記
する。開始処理はこのファイルを読み込み、ブリーフィング作成の前提知識に
使う。

## Reviewゾーンの運用

`Review/`は、AIが分類・判断に確信を持てない成果物を定型フォーマット
（`## サマリー`／`## 要判断`／`## 本文`／`## 秘書メモ`）で確認待ちに
置くゾーン。以下の2ケースでのみ使う。

- `/intake`でtype・contextの判定に確信が持てない場合
- 締め処理で`Inbox/`の未処理項目を強制変換する場合

人間は`## 要判断`欄の`- 回答: `行（コロンの右）に回答を書き込む。この行が
回答済みかどうかの判定マーカーになる。次回の`today`更新処理が回答済みの
Reviewノートを検出し、正式なノート（`Cabinet/Notes/`）に変換して
Reviewノートを削除する。通常の`update.md`によるInbox仕分けが「曖昧なため
保留」するケースは対象外で、従来通りInboxに残す。

## Git運用: 日次ブランチ

ノートを新規作成・編集するBash/Write/Edit操作を行う前に、必ず今日の日次
ブランチ（`daily/YYYY-MM-DD`）にいることを確認する。無ければ`main`から
`git checkout -b daily/<今日の日付>`で作成する。既に存在すればチェック
アウトするだけでよい。日中はコミットしない（`today`スキルの締め手順が
最後に今日の変更をひとつのコミットにまとめ、`main`へfast-forwardマージし、
`git push`する）。

## コマンド

- `/today`: 開始・更新・締めの3モードを持つ（`.claude/skills/today/
  SKILL.md`にスキル化済み）。更新モードは`/loop`から数十分間隔で自動的に
  繰り返し呼ばれ、Inbox仕分け・Reviewノートの回答確認・カレンダー確認・
  期限確認を継続的に行う。人間は1日の最初に`/today`を1回起動すればよい。
- `/intake`: 会話に貼り付けられたメール・チャット本文からタスク候補を
  抽出しノート化する（`.claude/skills/intake/SKILL.md`）。
- `/setup`: 新規プロジェクトを起票する（`.claude/skills/setup/SKILL.md`）。
  `Cabinet/Notes/`はフラット構成のため専用サブフォルダは作らない。

各コマンドの詳細手順は`.claude/skills/<name>/SKILL.md`を参照する。

## フォルダに関する補足

`type`はフォルダに依存せず判定されるため、`Cabinet/Notes/`はサブフォルダ
を作らずフラットに保つ。フォルダによる分類はAIにとって不安定な意思決定
（このメモは`task`か`know-how`か等ではなく、どのサブフォルダに置くか、
という点）を強いるため、意図的にこの一本化を採用している。
