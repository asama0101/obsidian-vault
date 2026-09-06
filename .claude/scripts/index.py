#!/usr/bin/env python3
"""Cabinet/Notes/ のノートを索引化してTSVで出力する。

秘書ループがvaultを読む唯一の経路。個別ノートの読み込みは、実際にそのノートを
編集するときだけ行う。出力はヘッダ行を持たず、1行が1ノートに対応する。
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

COLUMNS = [
    "path",
    "type",
    "status",
    "due",
    "check",
    "done",
    "context",
    "date",
    "title",
    "mtime",
]


def parse_frontmatter(text: str) -> dict[str, str]:
    """先頭の `---` で囲まれた `key: value` 行を辞書にして返す。

    閉じの `---` が無い場合はfrontmatter無しとみなして空の辞書を返す。
    値の前後を囲むクォートは取り除く。
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    props: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return props
        key, separator, value = line.partition(":")
        if not separator:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        props[key.strip()] = value
    return {}


def sanitize(value: str) -> str:
    """TSVの行と列を壊す制御文字を空白に潰す。"""
    return value.replace("\t", " ").replace("\n", " ").replace("\r", " ")


def build_row(note: Path, vault_root: Path) -> dict[str, str]:
    """ノート1件を索引の1行に変換する。"""
    props = parse_frontmatter(note.read_text(encoding="utf-8", errors="replace"))
    row = {column: sanitize(props.get(column, "")) for column in COLUMNS}
    row["path"] = note.relative_to(vault_root).as_posix()
    row["title"] = note.stem
    row["mtime"] = dt.datetime.fromtimestamp(note.stat().st_mtime).isoformat(
        timespec="seconds"
    )
    return row


def collect(vault_root: Path) -> list[dict[str, str]]:
    """Cabinet/Notes/ 直下の .md をファイル名順に索引化する。"""
    notes_dir = vault_root / "Cabinet" / "Notes"
    if not notes_dir.is_dir():
        return []
    return [build_row(note, vault_root) for note in sorted(notes_dir.glob("*.md"))]


def default_vault_root() -> Path:
    """このスクリプトの位置からvaultのルートを求める。"""
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ノートの索引をTSVで出力する")
    parser.add_argument("--vault-root", type=Path, default=default_vault_root())
    args = parser.parse_args(argv)

    for row in collect(args.vault_root.resolve()):
        print("\t".join(row[column] for column in COLUMNS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
