"""close_day.sh のテスト。一時ディレクトリにgitリポジトリを作って検証する。"""
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "close_day.sh"


def git(repo: Path, *args: str) -> str:
    """テスト用リポジトリでgitコマンドを実行する。"""
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def make_repo(tmp_path: Path, today: str = "2026-09-07") -> Path:
    """main と daily ブランチを持ち、デイリーノートが置かれたリポジトリを作る。"""
    repo = tmp_path / "vault"
    (repo / "Cabinet" / "Diary").mkdir(parents=True)
    (repo / "Cabinet" / "Diary" / ".gitkeep").write_text("", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "test")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "初期コミット")
    git(repo, "checkout", "-q", "-b", f"daily/{today}")
    (repo / "Cabinet" / "Diary" / f"{today}.md").write_text(
        f"---\ndate: {today}\n---\n\n## メモ\n- 覚え書き\n", encoding="utf-8"
    )
    return repo


def run_close(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), str(repo)], capture_output=True, text=True
    )


def test_commits_diary_note_of_the_day(tmp_path):
    repo = make_repo(tmp_path)

    result = run_close(repo)

    assert result.returncode == 0, result.stderr
    assert (repo / "Cabinet" / "Diary" / "2026-09-07.md").is_file()
    # 締めのコミットにデイリーノートが含まれること。
    tracked = git(repo, "show", "--name-only", "--pretty=format:", "HEAD").split("\n")
    assert "Cabinet/Diary/2026-09-07.md" in tracked


def test_fast_forwards_main_and_ends_on_main(tmp_path):
    repo = make_repo(tmp_path)

    run_close(repo)

    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert git(repo, "rev-parse", "main") == git(repo, "rev-parse", "daily/2026-09-07")


def test_skips_push_when_origin_is_absent(tmp_path):
    repo = make_repo(tmp_path)

    result = run_close(repo)

    assert result.returncode == 0
    assert "push をスキップ" in result.stdout


def test_merges_to_main_when_there_is_nothing_to_commit(tmp_path):
    """当日分が既にコミット済みでも、締めはエラーにならず main へ ff マージする。"""
    repo = make_repo(tmp_path)
    # 人間または別経路が既にコミットしていて、作業ツリーがクリーンな状態。
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "先行コミット")
    daily_head = git(repo, "rev-parse", "daily/2026-09-07")

    result = run_close(repo)

    assert result.returncode == 0, result.stderr
    assert "スキップ" in result.stdout
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert git(repo, "rev-parse", "main") == daily_head
    # 空コミットを積まないこと。
    assert git(repo, "rev-parse", "daily/2026-09-07") == daily_head


@pytest.mark.parametrize(
    "frontmatter",
    [
        pytest.param(b"---\ndate: 2026-09-07 \n---\n", id="trailing_space"),
        pytest.param(b'---\ndate: "2026-09-07"\n---\n', id="double_quoted"),
        pytest.param(b"---\ndate: '2026-09-07'\n---\n", id="single_quoted"),
        pytest.param(b'---\ndate: "2026-09-07" \n---\n', id="quoted_with_space"),
        pytest.param(b"---\r\ndate: 2026-09-07\r\n---\r\n", id="crlf"),
    ],
)
def test_accepts_date_property_written_with_quotes_or_padding(tmp_path, frontmatter):
    """date の値に空白・引用符・CRLF が混じっていても締められる。"""
    repo = make_repo(tmp_path)
    note = repo / "Cabinet" / "Diary" / "2026-09-07.md"
    note.write_bytes(frontmatter)

    result = run_close(repo)

    assert result.returncode == 0, result.stderr
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "main"
    assert git(repo, "rev-parse", "main") == git(repo, "rev-parse", "daily/2026-09-07")


def test_fails_when_diary_note_is_missing(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "Cabinet" / "Diary" / "2026-09-07.md").unlink()

    result = run_close(repo)

    assert result.returncode == 1
    assert "Cabinet/Diary/2026-09-07.md" in result.stderr


def test_fails_when_date_property_is_malformed(tmp_path):
    repo = make_repo(tmp_path)
    note = repo / "Cabinet" / "Diary" / "2026-09-07.md"
    note.write_text("---\ndate: きょう\n---\n", encoding="utf-8")

    result = run_close(repo)

    assert result.returncode == 1
    # 日付として読めない値であることを、その値ごと知らせること。
    assert "食い違" in result.stderr
    assert "きょう" in result.stderr
    assert note.exists()


def test_fails_when_date_property_does_not_match_file_name(tmp_path):
    repo = make_repo(tmp_path)
    head_before = git(repo, "rev-parse", "HEAD")
    note = repo / "Cabinet" / "Diary" / "2026-09-07.md"
    note.write_text("---\ndate: 2026-09-06\n---\n", encoding="utf-8")

    result = run_close(repo)

    assert result.returncode == 1
    assert "食い違" in result.stderr
    assert note.exists()
    # 異常系では作業ツリーに手を付けず、コミットも作らない。
    assert git(repo, "rev-parse", "HEAD") == head_before
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "daily/2026-09-07"


def test_fails_when_not_on_a_daily_branch(tmp_path):
    """ブランチ検査はノート存在検査より先に行う。日付の出所がブランチ名だから。"""
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "-b", "feature/other")
    # ノートが無くてもブランチのエラーが出ることで、検査順序を固定する。
    (repo / "Cabinet" / "Diary" / "2026-09-07.md").unlink()

    result = run_close(repo)

    assert result.returncode == 1
    assert "日次ブランチ" in result.stderr
    assert "feature/other" in result.stderr


def test_fails_when_main_cannot_fast_forward(tmp_path):
    repo = make_repo(tmp_path)
    main_before = git(repo, "rev-parse", "main")
    daily_head_before = git(repo, "rev-parse", "daily/2026-09-07")
    git(repo, "stash", "-q", "-u")
    git(repo, "checkout", "-q", "main")
    (repo / "別の変更.md").write_text("main側の変更\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "main側の先行コミット")
    main_after = git(repo, "rev-parse", "main")
    git(repo, "checkout", "-q", "daily/2026-09-07")
    git(repo, "stash", "pop", "-q")

    result = run_close(repo)

    assert result.returncode == 1
    assert main_before != main_after
    assert git(repo, "rev-parse", "main") == main_after
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "daily/2026-09-07"
    # 締め失敗時は作業ツリーを締め前の状態に復元する（/loopの二重化を防ぐため）。
    assert (repo / "Cabinet" / "Diary" / "2026-09-07.md").exists()
    assert git(repo, "rev-parse", "daily/2026-09-07") == daily_head_before


def test_restores_worktree_when_checkout_main_fails(tmp_path):
    repo = make_repo(tmp_path)
    daily_head_before = git(repo, "rev-parse", "daily/2026-09-07")
    # main が消えていれば `git checkout main` が失敗する。
    git(repo, "branch", "-q", "-D", "main")

    result = run_close(repo)

    assert result.returncode == 1
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "daily/2026-09-07"
    # ff 失敗時と同じ復元経路を通り、コミットが取り消されデイリーノートが残ること。
    assert git(repo, "rev-parse", "daily/2026-09-07") == daily_head_before
    assert (repo / "Cabinet" / "Diary" / "2026-09-07.md").is_file()


def test_reports_recovery_steps_when_push_fails(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "remote", "add", "origin", str(tmp_path / "unreachable.git"))

    result = run_close(repo)

    assert result.returncode == 1
    assert "git pull --rebase origin main" in result.stderr
    # push 失敗では復元しない。main は進んだままでよい。
    assert (repo / "Cabinet" / "Diary" / "2026-09-07.md").is_file()
    assert git(repo, "rev-parse", "main") == git(repo, "rev-parse", "daily/2026-09-07")
