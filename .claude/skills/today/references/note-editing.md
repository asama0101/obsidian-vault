# ノートの編集

- `status` や `due` の変更は frontmatter を直接編集する。値域は `.claude/CLAUDE.md` の表に従う。
- `task` を完了にするときは `status: 4_done` と `done: <今日の日付>` を両方書く。
- `tags` の変更は frontmatter を直接編集する。同じ値を持つ他のノートも直す必要がある場合は、`index.py` の `tags` 列で対象ノートを列挙し、frontmatterを1件ずつ直接編集する。
- `project` の変更は frontmatter を直接編集し、実体のフォルダも移す。プロパティとフォルダの同期はAIが担保する。
- `## 更新履歴` は作らない。`project` の `## 経緯` にだけ、方針・判断の変化を書く。`status` の変更では書かない。
