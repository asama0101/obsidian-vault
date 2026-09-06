# CLAUDE.md — このvaultの取扱説明書

個人利用のObsidian vault。Obsidian（`Today.md`・Bases）を「見る場所」、
Claude Codeを「操作・秘書業務を回す場所」として役割分担する。

## 役割分担

秘書業務を7機能（捕捉・判断・構造化・追跡・準備・報告・締め）に分解し、
人間とClaude Codeの担当を次のように固定する。

- **人間がやること**: ①生の情報を`Inbox/`に書き留める、または`intake`
  スキルで直接渡す。②AIが確信を持てない判断（分類不明・新規プロジェクト
  起票の可否等）に答える。`Today.md`の`## メモ`欄への自由記述。`Today.md`
  と5本の`.base`を読むこと。Claude Codeを起動すること（`/today`を1日の
  最初に1回）。
- **Claude Codeがやること**: ③〜⑦（構造化・追跡・準備・報告・締め）の
  全て。`Inbox/`の仕分け、`Cabinet/Notes/`への構造化、期限・進捗の追跡、
  会議前の準備、`Today.md`への報告、クリアデスクの実行。

人間がObsidianのファイルエクスプローラーを操作して`Cabinet/`配下を直接
編集・整理することは想定しない。

## フォルダ構成

```
vault/
├── Inbox/            ← 人間の書き込みゾーン（1件1ノート、フォルダ一覧は見ない。Inbox.baseで一覧を見る）
├── Today.md           ← ピン留め。ブリーフィング（Claude Code管理）＋メモ（人間が自由記述）
├── Inbox.base／タスク.base／プロジェクト.base／議事録.base／ノウハウ.base
├── Cabinet/           ← Claude Code専管ゾーン（人間は直接編集しない）
│   ├── Diary/         ← 締め処理でリネーム移動された過去のTodayの記録
│   ├── Notes/         ← task/project/meeting/know-howを`type`で区別してフラット格納
│   ├── Documents/     ← 資料保管庫（都度の自然言語指示で手動投入、専用Skillなし）
│   ├── Assets/        ← 添付ファイル
│   └── Templates/     ← テンプレート
└── .claude/
```

## ノート種別とプロパティ

`type`プロパティで4種を判別する: `task` / `project` / `meeting` /
`know-how`。`Inbox/`配下のノートは分類前の一時状態のため`type`を持たない
（`date`のみ）。`Cabinet/Diary/`のノート（締め処理でリネームされた過去の
`Today.md`）も`type`を持たない（`date`のみ）。

| プロパティ | task | project | meeting | know-how | Inbox | Diary |
|---|---|---|---|---|---|---|
| type | ● | ● | ● | ● | | |
| status | ●(1_todo/2_doing/3_pending/4_done/5_cancelled) | ●(1_active/2_done) | | | | |
| due | ○ | ○ | | | | |
| check | ○ | | | | | |
| date | ● | | ● | ● | ● | ● |
| context | ○ | ○ | ○ | ○ | | |

## プロパティ更新はClaude Code経由を正とする

`status`/`check`をObsidianのプロパティパネルで直接書き換えることを
前提にしない。自然言語の指示を受けたら、該当ノートのfrontmatterを直接
編集する。ステータス値は上表の許容値のみを使う。

## `Today.md`の運用

`Today.md`はvault直下に常に1つだけ存在する単一ファイル。`## ブリーフィング`
（今日の予定・今日のタスク・一言コメント。`today`スキルの開始/更新モードが
自動更新する）と`## メモ`（人間が自由に書き込む欄）の2セクションを持つ。
「メモしておいて」等の指示は`## メモ`へ追記する形で反映する。締め処理で
`Today.md`は`Cabinet/Diary/{{date}}.md`へリネーム移動され、翌朝また新規に
作成される。日常的な予定・タスク確認は`Today.md`で完結させ、資料・過去
記録を横断的に探す時だけBasesをたどる。

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
  繰り返し呼ばれ、Inbox仕分け・カレンダー確認・期限確認を継続的に行う。
  人間は1日の最初に`/today`を1回起動すればよい。
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
