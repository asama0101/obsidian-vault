#!/usr/bin/env python3
"""Cabinet/Notes/ のノートを索引化してTSVで出力する。

秘書ループが Cabinet/Notes/ の一覧を読む唯一の経路。個別ノートの読み込みは、実際に
そのノートを編集するときだけ行う。出力はヘッダ行を持たず、1行が1ノートに対応する。
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

LIST_SEPARATOR = ","

COLUMNS = [
    "path",
    "type",
    "status",
    "due",
    "done",
    "tags",
    "project",
    "date",
    "title",
    "mtime",
    "blocked_by",
]
CALENDAR_COLUMNS = ["calendar_event_id", "calendar_series_id"]
ALL_COLUMNS = COLUMNS + CALENDAR_COLUMNS
COMPLETED_STATUSES = {
    "task": {"4_done", "5_cancelled"},
    "project": {"2_done"},
}


def strip_quotes(value: str) -> str:
    """値の前後を囲むクォートを1組だけ取り除く。"""
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_inline_list(value: str) -> list[str]:
    """`[a, b]` 形式のインラインリストを要素のリストにする。"""
    return [strip_quotes(item.strip()) for item in value[1:-1].split(",") if item.strip()]


def parse_frontmatter(text: str) -> dict[str, str]:
    """先頭の `---` で囲まれたfrontmatterを辞書にして返す。

    値がリストの場合（`[a, b]` のインライン形式と `- a` のブロック形式の両方）は、
    要素を LIST_SEPARATOR で連結した1つの文字列にする。`[[リンク]]` は
    ネストしたリストではなくObsidianのリンクなので、リストとして分解しない。
    閉じの `---` が無い場合はfrontmatter無しとみなして空の辞書を返す。
    値の前後を囲むクォートは取り除く。
    """
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        return {}
    props: dict[str, str] = {}
    pending_key: str | None = None
    pending_items: list[str] = []

    def flush() -> None:
        """直前の `key:` に続くブロックリストを確定させる。"""
        if pending_key is not None and pending_items:
            props[pending_key] = LIST_SEPARATOR.join(pending_items)

    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            flush()
            return props
        if pending_key is not None and stripped.startswith("- "):
            pending_items.append(strip_quotes(stripped[2:].strip()))
            continue
        flush()
        pending_key, pending_items = None, []
        key, separator, value = line.partition(":")
        if not separator:
            continue
        key = key.strip()
        value = value.strip()
        if value.startswith("[") and value.endswith("]") and not value.startswith("[["):
            props[key] = LIST_SEPARATOR.join(parse_inline_list(value))
            continue
        if not value:
            pending_key = key
            props[key] = ""
            continue
        props[key] = strip_quotes(value)
    return {}


def sanitize(value: str) -> str:
    """TSVの行と列を壊す制御文字を空白に潰す。"""
    return value.replace("\t", " ").replace("\n", " ").replace("\r", " ")


def build_row(note: Path, vault_root: Path) -> dict[str, str]:
    """ノート1件を索引の1行に変換する。"""
    props = parse_frontmatter(note.read_text(encoding="utf-8", errors="replace"))
    row = {column: sanitize(props.get(column, "")) for column in ALL_COLUMNS}
    row["path"] = note.relative_to(vault_root).as_posix()
    row["title"] = note.stem
    row["mtime"] = dt.datetime.fromtimestamp(note.stat().st_mtime).isoformat(
        timespec="seconds"
    )
    return row


def collect(vault_root: Path) -> list[dict[str, str]]:
    """Cabinet/Notes/ 配下（案件フォルダを含む）の .md をパス順に索引化する。"""
    notes_dir = vault_root / "Cabinet" / "Notes"
    if not notes_dir.is_dir():
        return []
    return [build_row(note, vault_root) for note in sorted(notes_dir.rglob("*.md"))]


def csv_list(value: str) -> list[str]:
    """カンマ区切りの文字列を空要素を除いたリストにする。"""
    return [item.strip() for item in value.split(",") if item.strip()]


def is_completed(row: dict[str, str]) -> bool:
    """既定の出力から外す完了物かを判定する。"""
    return row["status"] in COMPLETED_STATUSES.get(row["type"], set())


def matches(row: dict[str, str], args: argparse.Namespace) -> bool:
    """索引の1行が絞り込み条件をすべて満たすかを判定する。

    完了物は既定で落とすが、`--all` と `--status` の明示指定はこの既定を解除する。
    `--status 4_done` のような明示要求を既定除外が握り潰すと結果が常に空になるため。
    """
    if not args.all and not args.status and is_completed(row):
        return False
    if args.type and row["type"] not in args.type:
        return False
    if args.status and row["status"] not in args.status:
        return False
    if args.date and row["date"] != args.date:
        return False
    if args.updated_on and not row["mtime"].startswith(args.updated_on):
        return False
    if args.due_before and (not row["due"] or row["due"] > args.due_before):
        return False
    return True


def default_vault_root() -> Path:
    """このスクリプトの位置からvaultのルートを求める。"""
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="ノートの索引をTSVで出力する")
    parser.add_argument("--vault-root", type=Path, default=default_vault_root())
    parser.add_argument("--type", type=csv_list, default=[], help="typeで絞る（カンマ区切りでOR）")
    parser.add_argument("--status", type=csv_list, default=[], help="statusで絞る（カンマ区切りでOR）")
    parser.add_argument("--date", help="frontmatterのdateがこの日付と完全一致するものに絞る")
    parser.add_argument("--updated-on", help="この日付に更新されたものに絞る")
    parser.add_argument("--all", action="store_true", help="完了物も含めて全件出す")
    parser.add_argument("--due-before", help="dueがこの日付以前のものに絞る（指定日を含む）")
    parser.add_argument(
        "--with-calendar-ids",
        action="store_true",
        help="calendar_event_id と calendar_series_id を末尾に付ける",
    )
    args = parser.parse_args(argv)

    rows = collect(args.vault_root.resolve())

    columns = ALL_COLUMNS if args.with_calendar_ids else COLUMNS
    for row in rows:
        if matches(row, args):
            print("\t".join(row[column] for column in columns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
