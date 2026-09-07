#!/usr/bin/env bash
# 当日の Cabinet/Diary/<date>.md を含む変更を1コミットにまとめ、main へ ff マージし push する。
# 終了コード: 0=成功、1=実行時エラー。
set -euo pipefail

vault_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$vault_root"

# 日付はブランチ名を出所とするため、ブランチ検査を最初に行う
branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$branch" != daily/* ]]; then
  echo "日次ブランチ (daily/*) 上で実行してください。現在: ${branch}" >&2
  exit 1
fi

day="${branch#daily/}"
if [[ ! "$day" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "ブランチ名から日付を読めません: '${branch}'" >&2
  exit 1
fi

note="Cabinet/Diary/${day}.md"
if [[ ! -f "$note" ]]; then
  echo "${note} がありません" >&2
  exit 1
fi

# 前後の空白と復帰文字（CRLF 由来）を落とす
trim() {
  local s="${1//$'\r'/}"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

# frontmatter の date プロパティを1つだけ取り出す。CRLF 改行のファイルも受け付ける
note_date="$(awk '/^---\r?$/{fence++; next} fence==1 && /^date:/{sub(/^date:/, ""); print; exit}' "$note")"
# Obsidian のプロパティパネルは引用符付きで書きうるので、比較前に正規化する
note_date="$(trim "$note_date")"
note_date="${note_date#[\"\']}"
note_date="${note_date%[\"\']}"
note_date="$(trim "$note_date")"
if [[ "$note_date" != "$day" ]]; then
  echo "ファイル名と frontmatter の date が食い違います: ${note} の date は '${note_date}'" >&2
  exit 1
fi

head_before="$(git rev-parse HEAD)"

# 締めのコミットを取り消す。
# 作業ツリーを破棄する操作（git reset --hard 等）は使わない。
restore_worktree() {
  git checkout -q "$branch"
  git reset --soft "$head_before"
}

git add -A
# 当日分が既にコミット済みの場合はコミットを飛ばし、main へのマージだけ行う（締めを冪等にする）
if git diff --cached --quiet; then
  echo "コミットする変更が無いためコミットをスキップしました"
else
  git commit -q -m "chore: ${day} の記録"
fi

if ! git checkout -q main; then
  restore_worktree
  echo "main へ切り替えられませんでした。手動で解決してください。" >&2
  exit 1
fi

if ! git merge --ff-only -q "$branch"; then
  restore_worktree
  echo "main へ fast-forward マージできませんでした。手動で解決してください。" >&2
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "origin が無いため push をスキップしました"
  exit 0
fi

# push 失敗時は作業ツリーを復元しない。main へのマージは既に済んでおり、
# 巻き戻すとローカルの履歴だけが失われるため。人間がリモートと解決する。
if ! git push -q origin main; then
  echo "push に失敗した。git pull --rebase origin main で解決してから git push origin main を実行すること。" >&2
  exit 1
fi

echo "締め完了: Cabinet/Diary/${day}.md を push しました"
