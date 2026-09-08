#!/usr/bin/env python3
"""テンプレートから Cabinet/Notes/ にノートを1件作る。

配置ルールは type によって異なる。

- `--type project`: `Cabinet/Notes/<date>_<title>/<title>.md` に作る。
  `<date>` はfrontmatterの `date`（`--set date=...` 指定が無ければ実行日）。
  `--project` は無視する。
- `--type task` / `--type meeting` かつ `--project` 指定あり:
  `Cabinet/Notes/<project>/<type>/<title>.md` に作る。案件フォルダが
  無ければ作る。`--project` は既存フォルダ名をそのまま使う文字列で、
  曖昧一致や自動検索は行わない。
- それ以外（`--project` 未指定、または `--type know-how`）:
  `Cabinet/Notes/<title>.md` 直下に作る。

終了コードは 0=成功、1=同名ノートが既にある、2=入力エラー。
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

NOTE_TYPES = ["task", "project", "meeting", "know-how"]
FORBIDDEN_TITLE_CHARS = set('\\/:*?"<>|')


def split_frontmatter(text: str) -> tuple[list[str], str]:
    """テンプレートをfrontmatterの行リストと残りの本文に分ける。"""
    lines = text.split("\n")
    if not lines or lines[0].strip() != "---":
        raise ValueError("テンプレートにfrontmatterがありません")
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index], "\n".join(lines[index + 1 :])
    raise ValueError("テンプレートのfrontmatterが閉じていません")


def apply_overrides(fm_lines: list[str], overrides: dict[str, str]) -> list[str]:
    """frontmatterの各行に上書き値を反映する。

    テンプレートに存在しないプロパティを指定された場合は例外を送出する。
    タイポによる無秩序なプロパティの増殖を防ぐため。
    """
    known = {line.partition(":")[0].strip() for line in fm_lines if ":" in line}
    unknown = sorted(set(overrides) - known)
    if unknown:
        raise ValueError(f"テンプレートに存在しないプロパティです: {', '.join(unknown)}")
    result = []
    for line in fm_lines:
        key = line.partition(":")[0].strip()
        if ":" in line and key in overrides:
            result.append(f"{key}: {overrides[key]}")
        else:
            result.append(line)
    return result


def parse_set(values: list[str]) -> dict[str, str]:
    """`key=value` 形式の指定を辞書にする。"""
    overrides: dict[str, str] = {}
    for item in values:
        key, separator, value = item.partition("=")
        if not separator:
            raise ValueError(f"--set は key=value 形式で指定してください: {item}")
        overrides[key.strip()] = value.strip()
    return overrides


def default_vault_root() -> Path:
    """このスクリプトの位置からvaultのルートを求める。"""
    return Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="テンプレートからノートを1件作る")
    parser.add_argument("--vault-root", type=Path, default=default_vault_root())
    parser.add_argument("--type", required=True, choices=NOTE_TYPES)
    parser.add_argument("--title", required=True)
    parser.add_argument("--set", action="append", default=[], dest="sets")
    parser.add_argument("--project", help="案件フォルダ名。指定するとその配下に作る")
    args = parser.parse_args(argv)

    title = args.title.strip()
    if not title or set(title) & FORBIDDEN_TITLE_CHARS:
        print(f"ノート名に使えない文字が含まれています: {args.title}", file=sys.stderr)
        return 2

    project = args.project.strip() if args.project is not None else ""
    project_parts = Path(project).parts
    if args.project is not None and (
        not project
        or set(project) & FORBIDDEN_TITLE_CHARS
        or len(project_parts) != 1
        or project_parts[0] in {".", ".."}
    ):
        print(f"案件名に使えない文字が含まれています: {args.project}", file=sys.stderr)
        return 2

    vault = args.vault_root.resolve()
    template = vault / "Cabinet" / "Templates" / f"{args.type}.md"
    if not template.is_file():
        print(f"テンプレートがありません: {template}", file=sys.stderr)
        return 2

    try:
        overrides = parse_set(args.sets)
        overrides.setdefault("date", dt.date.today().isoformat())
        fm_lines, body = split_frontmatter(template.read_text(encoding="utf-8"))
        fm_lines = apply_overrides(fm_lines, overrides)
    except ValueError as error:
        print(str(error), file=sys.stderr)
        return 2

    notes_dir = vault / "Cabinet" / "Notes"
    if args.type == "project":
        date_value = overrides["date"]
        target = notes_dir / f"{date_value}_{title}" / f"{title}.md"
    elif args.type in ("task", "meeting") and project:
        target = notes_dir / project / args.type / f"{title}.md"
    else:
        target = notes_dir / f"{title}.md"
    if target.exists():
        print(f"同名のノートが既にあります: {target.relative_to(vault).as_posix()}", file=sys.stderr)
        return 1

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("---\n" + "\n".join(fm_lines) + "\n---\n" + body, encoding="utf-8")
    print(target.relative_to(vault).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
