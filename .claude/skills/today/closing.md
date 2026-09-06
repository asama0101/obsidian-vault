# 締めモード

1. `Inbox/`に項目が残っていれば、各項目を`Cabinet/Templates/task.md`を
   元に`type: task`のノートとして`Cabinet/Notes/`へ作成する。本文の
   `## メモ`に元のInboxノートの内容をそのまま転記し、タイトルは
   「要確認: <元の内容の先頭部分>」とする。作成後、元のInboxノートを
   削除する。これを`Inbox/`が空になるまで繰り返す。
2. `Today.md`の`## ブリーフィング`を、今日実際に処理した件数（Inboxから
   構造化した件数・完了したタスク件数等）を含む実績サマリーに書き換える。
   `## メモ`セクションの内容はそのまま変更しない。
3. `Today.md`のfrontmatterの`date`を読み取り、`git mv Today.md
   Cabinet/Diary/<date>.md`でリネーム移動する。
4. 今日の変更を1つのコミットにまとめる。
5. 日次ブランチを`main`へfast-forwardマージする。non-fast-forwardの場合は
   マージを中断し、日次ブランチに復帰した上で人間に通知する。
6. `main`をリモートへpushする。
7. `PushNotification`でクリアデスク完了を通知する。
