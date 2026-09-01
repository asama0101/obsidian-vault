---
name: archive
description: Downloadsフォルダにある資料をこのObsidian vault内の91_Documentフォルダへコピーする。「Downloadsの資料をDocumentsにコピーして」「ダウンロードした〇〇をドキュメントに移して」「さっき落としたファイルをDocumentsに入れて」等の依頼で使う。コピー対象が具体的なファイル名・パターンで特定できていない場合は、必ずこのスキルの手順に従ってユーザーに確認してから実行する。
---

Downloadsフォルダの資料を、このObsidian vault内の`91_Document`フォルダへコピーする作業を担当する。
以下の手順に従うこと。

各手順のコードブロックに記載したコマンドは、`<...>`部分の置き換え以外を改変せずそのまま実行する。
確認・検証目的であっても、記載の無いコマンド（別のBash/PowerShellコマンドでの再確認等）を独自に追加実行しない。

## 1. パスの解決

- コピー元: `$env:USERPROFILE\Downloads`
- コピー先: このvaultリポジトリ直下の`91_Document`（フラット。サブフォルダは作らない）

## 2. 日次ブランチの確認

`91_Document`はこのvaultリポジトリの管理下にある。
コピーを実行する前に、vaultのCLAUDE.md運用ルールに従い、今日の日次ブランチ（`daily/YYYY-MM-DD`）にいることを確認する。
mainブランチにいる場合は`git checkout -b daily/<今日の日付>`で作成する（既に存在すればチェックアウトのみ）。

## 3. 対象ファイルの確定

ユーザーの依頼文にファイル名・拡張子・パターン（例: 「見積書.pdf」「今日ダウンロードした資料」「*.xlsx」）が含まれていれば、それを対象として扱う。
`Get-ChildItem`でDownloadsフォルダ内の該当ファイルを一覧化し、実際にマッチしたファイル名をユーザーに提示する。
0件の場合はその旨を伝えて終了する。

依頼文に具体的な指定が無い場合は、ユーザーに聞き返す前に、まずDownloadsフォルダ内で**更新日時が新しい順に上位4件**のファイル・フォルダを自動で探す。

```powershell
Get-ChildItem -Path "$env:USERPROFILE\Downloads" | Sort-Object LastWriteTime -Descending | Select-Object -First 4 | Format-List Name, PSIsContainer, LastWriteTime, Length
```

候補件数に応じて確認方法を分ける。

- 2件以上: 各項目の名前・種別（ファイル/フォルダ）・更新日時を選択肢とした`AskUserQuestion`（`multiSelect: true`）で複数選択させる。選ばれた項目すべてを対象とする（複数選択時は以降の手順4・5を選択項目ごとに実行する）。
- 1件のみ: その項目の名前・種別・更新日時を提示し、`AskUserQuestion`の単一選択（はい/いいえ）で「これでよいか」を確認する。

「その他」（自由記述）が選ばれた場合は、改めて何を対象にするか確認する。
勝手にDownloadsフォルダ全体を対象にしないこと。

## 4. 上書き確認

マッチしたファイルのうち`91_Document`に同名ファイルが既に存在するものが無いか、`Test-Path`で確認する。

```powershell
Test-Path -Path "<vaultルート>\91_Document\<対象ファイル1>", "<vaultルート>\91_Document\<対象ファイル2>"
```

存在するものがあれば、コピーを実行する前にその一覧を提示し、上書きしてよいかユーザーに確認する。
同名ファイルが無ければこの確認は不要。

## 5. コピーの実行

確認が取れたら`Copy-Item -Force`でDownloadsから`91_Document`直下へコピーする。
対象がフォルダの場合は`-Recurse`も付ける。

```powershell
Copy-Item -Path "$env:USERPROFILE\Downloads\<対象ファイル>" -Destination "<vaultルート>\91_Document\" -Force
Copy-Item -Path "$env:USERPROFILE\Downloads\<対象フォルダ>" -Destination "<vaultルート>\91_Document\" -Force -Recurse
```

複数ファイルの場合は対象ファイルごとに実行する。

## 6. 結果報告

コピーしたファイル名の一覧（何件コピーしたか、上書きしたものがあればその旨）をユーザーに報告する。
