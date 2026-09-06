#!/usr/bin/env python3
"""ノートの `context` プロパティの値を一括で付け替える。

AIがcontextの新しい値を自分で決めてノートを作ったあと、その値が誤っていた場合に
訂正する経路として使う。1件だけ直すならfrontmatterの直接編集でよいが、同じ値を
複数のノートに付けたあとで誤りに気づいた場合、1件ずつ直すと直し漏れが自己増殖する。
この処理は完全に機械的（`--old` と完全一致するcontextを持つノートを機械的に置換
するだけ）なので、判断を伴わずスクリプト側に置く。

行ベースの書き換えのみを行い、`context:` 行以外（本文・他のプロパティ・
プロパティの順序）には一切手を触れない。frontmatter全体を再構築する方式は
本文やプロパティ順を壊すため採らない。

終了コードは 0=成功、1=対象が1件も無い、2=入力エラー。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def find_context_line_index(lines: list[str]) -> int | None:
    """frontmatter内の `context:` 行のインデックスを返す。無ければ None。"""
    if not lines or lines[0].strip() != "---":
        return None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return None
        key, separator, _ = line.partition(":")
        if separator and key.strip() == "context":
            return index
    return None


def parse_value(line: str) -> str:
    """`key: value` 行から前後のクォートを除いた値を取り出す。"""
    _, _, value = line.partition(":")
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def rewrite_note(path: Path, old: str, new: str, dry_run: bool) -> bool:
    """1ノートの `context:` 行を書き換える。書き換え対象なら True を返す。"""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    index = find_context_line_index(lines)
    if index is None or parse_value(lines[index]) != old:
        return False
    if not dry_run:
        lines[index] = f"context: {new}" if new else "context:"
        path.write_text("\n".join(lines), encoding="utf-8")
    return True


def default_vault_root() -> Path:
    """このスクリプトの位置からvaultのルートを求める。"""
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="contextの値を一括で付け替える")
    parser.add_argument("--vault-root", type=Path, default=default_vault_root())
    parser.add_argument("--old", required=True, help="付け替え元の値")
    parser.add_argument("--new", required=True, help="付け替え先の値（空文字列も可）")
    parser.add_argument("--dry-run", action="store_true", help="書き込まず対象だけ表示する")
    args = parser.parse_args(argv)

    if not args.old:
        print("--old は空文字列にできません", file=sys.stderr)
        return 2

    vault = args.vault_root.resolve()
    notes_dir = vault / "Cabinet" / "Notes"
    if not notes_dir.is_dir():
        return 1

    changed = [
        note.relative_to(vault).as_posix()
        for note in sorted(notes_dir.glob("*.md"))
        if rewrite_note(note, args.old, args.new, args.dry_run)
    ]

    for path in changed:
        print(path)

    return 0 if changed else 1


if __name__ == "__main__":
    sys.exit(main())
