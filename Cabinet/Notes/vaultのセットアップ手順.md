---
type: know-how
date: 2026-09-07
context: vault運用
---

## 状況

このvaultを新規に導入する際の環境構築手順。Obsidian 1.11以降とClaude Codeが必要。

## 手順

### 前提

- Obsidian **1.11 以降**を使う。Basesがコア機能として使えるため
- `secretary`スキルの締め手順（`.claude/skills/secretary/closing.md`）が日次ブランチを`main`へマージ後に`git push origin main`するため、リモートリポジトリ（`origin`）を設定しておく。設定しない場合は`git push`の手順だけ失敗する（マージ自体は成功する）

### 1. Gitリポジトリを初期化する

`secretary`スキルの締め手順が日次ブランチのマージ・pushを行うため、他の手順より先に済ませておく。

- vaultルートで`git init -b main`を実行する
- `.gitignore`を作成し、以下を除外する。
  ```
  .obsidian/workspace.json
  .obsidian/workspace-mobile.json
  .trash/
  desktop.ini
  __pycache__/
  .pytest_cache/
  ```
- 初回コミットを作成する（`git add .` → `git commit -m "Initial commit"`）
- （任意）リモートリポジトリ（GitHub等）を用意し、`git remote add origin <URL>`で紐付ける
- （任意）`git push -u origin main`で初回pushする

### 2. フォルダを作成する

vaultルート直下に`Cabinet/`を作り、`Cabinet/`配下に`Diary/`・`Notes/`・`Documents/`・`Assets/`・`Templates/`を作成する。

- `Cabinet/MEMORY.md`を作成する。初期内容は見出し`# MEMORY`のみでよい

### 3. `.base`ファイルをvaultルート直下に配置する

- `タスク.base`・`プロジェクト.base`・`議事録.base`・`ノウハウ.base`をルートディレクトリに配置する

### 4. `Cabinet/Templates`にテンプレートファイルを配置する

- `task.md` / `project.md` / `meeting.md` / `know-how.md` / `today.md`を`Cabinet/Templates/`にコピーする
- `設定 → コアプラグイン → テンプレート`を有効化し、テンプレートフォルダの場所を`Cabinet/Templates`に設定する
- `設定 → コアプラグイン → デイリーノート`を**無効化**する。`Today.md`（`secretary`スキルが管理）が同じ役割を担うため、コアプラグイン側が別途デイリーノートを作らないようにする
- `設定 → ファイルとリンク → 起動時に開くファイル`を`最後に開いたファイル`に設定する
- `設定 → ファイルとリンク → 新規添付ファイルの保存先`を`Cabinet/Assets`に設定する
- `Today.md`をブックマーク（ピン留め）し、いつでもすぐ開けるようにする

### 5. ショートカットキーを割り当てる

- `設定 → ホットキー`で「テンプレート: テンプレートを挿入」に任意のキー（例: `Ctrl+Shift+N`）を割り当てる
- `設定 → ホットキー`で「ペイン: 右に分割」に任意のキー（例: `Ctrl+R`）を割り当てる
- `設定 → ホットキー`で「右のサイドバーを開閉」に任意のキー（例: `Ctrl+,`）を割り当てる
- `設定 → ホットキー`で「左のサイドバーを開閉」に任意のキー（例: `Ctrl+.`）を割り当てる

### 6. Claude Codeコマンドを配置する

- `CLAUDE.md`を`.claude/`配下に配置する
- `.claude/commands/`に`today.md` / `intake.md` / `close.md`を配置する
- `.claude/skills/secretary/SKILL.md`を配置する
- （任意）Google CalendarまたはOutlookのMCP連携を設定する

### 7. 運用を開始する

- 1日の最初に`/today`を1回起動する。以後は更新モードが自動で繰り返され、締め処理まで人間の起動は不要

## 注意点

### OneDrive環境での注意点

このvaultをOneDrive配下に置く場合、以下に注意する。

- **OneDriveの「ファイルオンデマンド」を無効化し、vaultフォルダを「常にこのデバイスに保持する」に設定する**: クラウードのみでローカルに実体が無い状態だと、Obsidianの全文検索やClaude Codeからのファイル読み書きが失敗・遅延する
- **`.git`フォルダをOneDrive外へ逃がす**: OneDriveの「フォルダーの選択」機能はトップレベルフォルダ単位でしか同期除外できず、`.git`のような特定のサブフォルダだけを除外することはできない。2026年8月に管理者向けの除外機能が追加されたが、個人アカウントでは使えないことが多い。放置すると同期処理と`git`のファイルロックが競合しリポジトリが破損するリスクがあるため、`git`の`--separate-git-dir`機能で`.git`の実体をOneDrive外へ移す。
  - OneDrive外の場所（例: `C:\Users\<ユーザー名>\git-data\obsidian.git`）を用意する
  - vaultルートで`git init --separate-git-dir=C:\Users\<ユーザー名>\git-data\obsidian.git`を実行する。既存リポジトリに対しても安全に適用できる。実行すると`.git`の中身がそのパスへ移動する。vaultルートには移動先を指す`.git`ポインタファイル1つだけが残る
  - `git status`を実行し、リポジトリが正常に認識されることを確認する
- **複数端末で同時にvaultを開かない**: 同一vaultを別PC・別デバイスで同時に開くと、OneDriveの同期タイミングのズレでノートの重複ファイル（`ファイル名-PC名.md`等）や`.git`の競合が起きる。編集は1台に絞るか、片方を閉じてから他方を開く

### Obsidianの基本設定

**エディタ**
- デフォルトビューを`リーディングビュー`にする
- 読みやすい行の長さを`off`にする
- 行番号の表示を`on`にする
- ノートにMermaid図を表示を`on`にする
- インタインタイトルを`off`にする

**ファイルとリンク**
- 内部リンクを毎回更新するを`on`にする
- すべてのファイル拡張子を認識を`on`にする

**外観**
- 好みのテーマを設定する（`Typora-Vue`がすっきりしつつ色味がよい）
