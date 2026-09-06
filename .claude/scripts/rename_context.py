#!/usr/bin/env python3
"""ノートの `context` プロパティの値を一括で付け替える。

AIがcontextの新しい値を自分で決めてノートを作ったあと、その値が誤っていた場合に
訂正する経路として使う。1件だけ直すならfrontmatterの直接編集でよいが、同じ値を
複数のノートに付けたあとで誤りに気づいた場合、1件ずつ直すと直し漏れが自己増殖する。
この処理は完全に機械的（値の一致や指定パスに基づく機械的な置換だけ）なので、判断
を伴わずスクリプト側に置く。

2つの指定方法を持つ。

- `--old`/`--new`: `--old` と完全一致する `context` を持つ全ノートを一括で付け替える。
- `--path`（複数回指定可）/`--new`: 指定したノートだけを付け替える。`context` が
  空のノートに後から値を付ける場合に使う（`--old ""` は事故防止のため拒否される
  ため、空のcontextには `--old`/`--new` の経路が使えない）。

両方は同時に指定できず、どちらも指定しない場合も拒否する。

行ベースの書き換えのみを行い、`context:` 行以外（本文・他のプロパティ・
プロパティの順序）には一切手を触れない。frontmatter全体を再構築する方式は
本文やプロパティ順を壊すため採らない。frontmatterの閉じ `---` が無い場合は
`index.py` と同様にfrontmatter無しとみなし、対象外とする（本文中に偶然
`context:` から始まる行があっても誤爆しないため）。

`--path` 指定時は、書き込み前に全パスを検証する。1件でも無効なパスがあれば
1件も書き換えない（部分適用を避けるため）。同じパスを複数回指定しても、
書き込み・出力とも1回だけになるよう重複を除去する。

終了コードは 0=成功、1=対象が1件も無い、2=入力エラー。
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

FORBIDDEN_NEW_CHARS = (":", "#")


def find_context_line_index(lines: list[str]) -> int | None:
    """frontmatter内の `context:` 行のインデックスを返す。無ければ None。

    閉じの `---` が見つかるまでの範囲だけを対象にする。閉じが無い場合は
    `index.py` の `parse_frontmatter` と同様にfrontmatter無しとみなし、
    本文側に `context:` から始まる行があってもそれを対象にしない。
    """
    if not lines or lines[0].strip() != "---":
        return None
    closing = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            closing = i
            break
    if closing is None:
        return None
    for index in range(1, closing):
        key, separator, _ = lines[index].partition(":")
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


def format_context_line(new: str) -> str:
    """`context:` 行を新しい値で組み立てる。空文字列なら値無しの行にする。"""
    return f"context: {new}" if new else "context:"


def rewrite_by_old_value(note: Path, old: str, new: str, dry_run: bool) -> bool:
    """1ノートの `context:` 行を、値が `old` と完全一致する場合だけ書き換える。"""
    text = note.read_text(encoding="utf-8")
    lines = text.split("\n")
    index = find_context_line_index(lines)
    if index is None or parse_value(lines[index]) != old:
        return False
    if not dry_run:
        lines[index] = format_context_line(new)
        note.write_text("\n".join(lines), encoding="utf-8")
    return True


def resolve_path_targets(
    paths: list[str], vault: Path, notes_dir: Path
) -> tuple[list[tuple[Path, list[str], int]], str | None]:
    """`--path` で指定された全ノートを検証する。

    1件でも問題があれば理由を返す。呼び出し側はこの時点で1件も書き換えない。
    有効な場合は各ノートのパス・行リスト・context行のインデックスを返し、
    書き込み側で再度読み直さずに済むようにする。
    """
    targets: list[tuple[Path, list[str], int]] = []
    seen: set[Path] = set()
    for rel in paths:
        candidate = (vault / rel).resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        try:
            candidate.relative_to(notes_dir)
        except ValueError:
            return [], f"Cabinet/Notes/ 配下のパスではありません: {rel}"
        if not candidate.is_file():
            return [], f"ノートが見つかりません: {rel}"
        lines = candidate.read_text(encoding="utf-8").split("\n")
        index = find_context_line_index(lines)
        if index is None:
            return [], f"frontmatterに context がありません: {rel}"
        targets.append((candidate, lines, index))
    return targets, None


def default_vault_root() -> Path:
    """このスクリプトの位置からvaultのルートを求める。"""
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="contextの値を一括で付け替える")
    parser.add_argument("--vault-root", type=Path, default=default_vault_root())
    parser.add_argument("--old", default=None, help="付け替え元の値（--pathとは排他）")
    parser.add_argument("--new", required=True, help="付け替え先の値（空文字列も可）")
    parser.add_argument(
        "--path", action="append", default=[], dest="paths",
        help="付け替え対象のノートをvault相対パスで指定する（複数回指定可、--oldとは排他）",
    )
    parser.add_argument("--dry-run", action="store_true", help="書き込まず対象だけ表示する")
    args = parser.parse_args(argv)

    if args.old is not None and args.paths:
        print("--old と --path は同時に指定できません", file=sys.stderr)
        return 2
    if args.old is None and not args.paths:
        print("--old か --path のいずれかを指定してください", file=sys.stderr)
        return 2
    if args.old is not None and args.old == "":
        print("--old は空文字列にできません", file=sys.stderr)
        return 2
    if any(char in args.new for char in FORBIDDEN_NEW_CHARS):
        print(f"--new に {' '.join(FORBIDDEN_NEW_CHARS)} を含めることはできません（YAMLが壊れるため）", file=sys.stderr)
        return 2

    vault = args.vault_root.resolve()
    notes_dir = vault / "Cabinet" / "Notes"

    if args.paths:
        targets, error = resolve_path_targets(args.paths, vault, notes_dir.resolve())
        if error:
            print(error, file=sys.stderr)
            return 2
        changed = []
        for note, lines, index in targets:
            if not args.dry_run:
                lines[index] = format_context_line(args.new)
                note.write_text("\n".join(lines), encoding="utf-8")
            changed.append(note.relative_to(vault).as_posix())
        for path in changed:
            print(path)
        return 0

    if not notes_dir.is_dir():
        print(f"Cabinet/Notes/ が見つかりません: {notes_dir}", file=sys.stderr)
        return 1

    changed = [
        note.relative_to(vault).as_posix()
        for note in sorted(notes_dir.glob("*.md"))
        if rewrite_by_old_value(note, args.old, args.new, args.dry_run)
    ]

    for path in changed:
        print(path)

    if not changed:
        print(f"--old の値 '{args.old}' に一致するノートがありません", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
