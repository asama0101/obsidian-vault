#!/usr/bin/env bash
# Today.md を Cabinet/Diary/ へ退避し、当日分を1コミットにまとめて main へ ff マージし push する。
# 終了コード: 0=成功、1=実行時エラー。
set -euo pipefail

vault_root="${1:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
cd "$vault_root"

if [[ ! -f Today.md ]]; then
  echo "Today.md がありません" >&2
  exit 1
fi

# frontmatter の date プロパティを1つだけ取り出す
day="$(awk '/^---$/{fence++; next} fence==1 && /^date:/{sub(/^date:[[:space:]]*/, ""); print; exit}' Today.md)"
if [[ ! "$day" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
  echo "Today.md の date プロパティを読めません: '${day}'" >&2
  exit 1
fi

branch="$(git rev-parse --abbrev-ref HEAD)"
if [[ "$branch" != daily/* ]]; then
  echo "日次ブランチ (daily/*) 上で実行してください。現在: ${branch}" >&2
  exit 1
fi

if [[ -e "Cabinet/Diary/${day}.md" ]]; then
  echo "Cabinet/Diary/${day}.md が既に存在します。上書きしません。" >&2
  exit 1
fi

head_before="$(git rev-parse HEAD)"

mkdir -p Cabinet/Diary
mv Today.md "Cabinet/Diary/${day}.md"

git add -A
git commit -q -m "chore: ${day} の記録"

git checkout -q main
if ! git merge --ff-only -q "$branch"; then
  git checkout -q "$branch"
  git reset --soft "$head_before"
  mv "Cabinet/Diary/${day}.md" Today.md
  echo "main へ fast-forward マージできませんでした。手動で解決してください。" >&2
  exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
  echo "origin が無いため push をスキップしました"
  exit 0
fi

git push -q origin main
echo "締め完了: Cabinet/Diary/${day}.md を push しました"
