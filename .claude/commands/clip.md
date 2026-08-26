---
description: URLの内容を取り込みメモ化する
argument-hint: <URL>
---
引数のURL（`$ARGUMENTS`）の内容を取得し、要約してメモノート化する。

## 手順

1. `$ARGUMENTS`のURLをWebFetchで取得する。
2. タイトルと3〜5行程度の要約を作成する。
3. `92_Template/memo.md`の内容をベースに、`10_Inbox/`配下へ新規ノートを
   作成する。ファイル名はページタイトルを使う（Windowsで問題になる禁止文字
   `\ / : * ? " < > |`は`_`に置換する）。
4. frontmatterの`date`は今日の日付。本文に「元URL: `<URL>`」の行、続けて
   要約を書く。
5. 作成したファイルパスをユーザーに報告する。
