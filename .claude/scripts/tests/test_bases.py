"""6_Cabinet/Bases/ の .base 4本を構文と規約の面から検証する。"""
from pathlib import Path

import pytest
import yaml

VAULT = Path(__file__).resolve().parents[3]
BASES_DIR = VAULT / "6_Cabinet" / "Bases"
EXPECTED_FILES = ["タスク.base", "ノウハウ.base", "プロジェクト.base", "議事録.base"]


def load(name: str) -> dict:
    return yaml.safe_load((BASES_DIR / name).read_text(encoding="utf-8"))


def test_exactly_four_base_files_exist():
    assert sorted(path.name for path in BASES_DIR.glob("*.base")) == EXPECTED_FILES


@pytest.mark.parametrize("name", EXPECTED_FILES)
def test_base_is_valid_yaml_with_views(name):
    data = load(name)

    assert isinstance(data, dict)
    assert isinstance(data.get("views"), list)
    assert data["views"], "ビューが1つもありません"


@pytest.mark.parametrize("name", EXPECTED_FILES)
def test_every_view_has_a_name_and_filters(name):
    for view in load(name)["views"]:
        assert view.get("name"), f"{name} に名前の無いビューがあります"
        assert view.get("type") == "table"
        assert "filters" in view


def test_task_base_exposes_the_today_view():
    names = [view["name"] for view in load("タスク.base")["views"]]

    assert "今日やること" in names


def test_task_base_exposes_the_project_view():
    names = [view["name"] for view in load("タスク.base")["views"]]

    assert "project別" in names


def test_meeting_base_exposes_the_project_view():
    names = [view["name"] for view in load("議事録.base")["views"]]

    assert "project別" in names


def test_project_template_embeds_the_task_project_view():
    template = (VAULT / "6_Cabinet" / "Templates" / "project.md").read_text(encoding="utf-8")
    names = [view["name"] for view in load("タスク.base")["views"]]

    embedded = [
        line for line in template.split("\n") if line.startswith("![[タスク.base#")
    ]
    assert len(embedded) == 1
    view_name = embedded[0].split("#", 1)[1].rstrip("]")
    assert view_name in names


def test_project_template_embeds_the_meeting_project_view():
    template = (VAULT / "6_Cabinet" / "Templates" / "project.md").read_text(encoding="utf-8")
    names = [view["name"] for view in load("議事録.base")["views"]]

    embedded = [
        line for line in template.split("\n") if line.startswith("![[議事録.base#")
    ]
    assert len(embedded) == 1
    view_name = embedded[0].split("#", 1)[1].rstrip("]")
    assert view_name in names


def test_today_template_embeds_the_task_view_for_reference():
    template = (VAULT / "6_Cabinet" / "Templates" / "today.md").read_text(encoding="utf-8")
    names = [view["name"] for view in load("タスク.base")["views"]]

    embedded = [line for line in template.split("\n") if line.startswith("![[タスク.base#")]
    assert len(embedded) == 1
    view_name = embedded[0].split("#", 1)[1].rstrip("]")
    assert view_name in names


def test_today_template_embeds_the_project_view():
    template = (VAULT / "6_Cabinet" / "Templates" / "today.md").read_text(encoding="utf-8")
    names = [view["name"] for view in load("プロジェクト.base")["views"]]

    embedded = [
        line for line in template.split("\n") if line.startswith("![[プロジェクト.base#")
    ]
    assert len(embedded) == 1
    view_name = embedded[0].split("#", 1)[1].rstrip("]")
    assert view_name in names
