"""close_day.sh のテスト。一時ディレクトリにgitリポジトリを作って検証する。"""
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "close_day.sh"


def git(repo: Path, *args: str) -> str:
    """テスト用リポジトリでgitコマンドを実行する。"""
    result = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return result.stdout.strip()


def make_repo(tmp_path: Path, today: str = "2026-09-07") -> Path:
    """main と daily ブランチを持ち、Today.md が置かれたリポジトリを作る。"""
    repo = tmp_path / "vault"
    (repo / "Cabinet" / "Diary").mkdir(parents=True)
    (repo / "Cabinet" / "Diary" / ".gitkeep").write_text("", encoding="utf-8")
    subprocess.run(["git", "init", "-q", "-b", "main", str(repo)], check=True)
    git(repo, "config", "user.email", "test@example.com")
    git(repo, "config", "user.name", "test")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "初期コミット")
    git(repo, "checkout", "-q", "-b", f"daily/{today}")
    (repo / "Today.md").write_text(
        f"---\ndate: {today}\n---\n\n## メモ\n- 覚え書き\n", encoding="utf-8"
    )
    return repo


def run_close(repo: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), str(repo)], capture_output=True, text=True
    )


def test_moves_today_into_diary_and_commits(tmp_path):
    repo = make_repo(tmp_path)

    result = run_close(repo)

    assert result.returncode == 0, result.stderr
    assert not (repo / "Today.md").exists()
    assert (repo / "Cabinet" / "Diary" / "2026-09-07.md").is_file()


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


def test_fails_when_today_is_missing(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "Today.md").unlink()

    result = run_close(repo)

    assert result.returncode == 1


def test_fails_when_date_property_is_malformed(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "Today.md").write_text("---\ndate: きょう\n---\n", encoding="utf-8")

    result = run_close(repo)

    assert result.returncode == 1
    assert (repo / "Today.md").exists()


def test_fails_when_not_on_a_daily_branch(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "checkout", "-q", "-b", "feature/other")

    result = run_close(repo)

    assert result.returncode == 1
    assert (repo / "Today.md").exists()


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
    assert (repo / "Today.md").exists()
    assert not (repo / "Cabinet" / "Diary" / "2026-09-07.md").exists()
    assert git(repo, "rev-parse", "daily/2026-09-07") == daily_head_before


def test_restores_worktree_when_checkout_main_fails(tmp_path):
    repo = make_repo(tmp_path)
    daily_head_before = git(repo, "rev-parse", "daily/2026-09-07")
    # main が消えていれば `git checkout main` が失敗する。
    git(repo, "branch", "-q", "-D", "main")

    result = run_close(repo)

    assert result.returncode == 1
    assert git(repo, "rev-parse", "--abbrev-ref", "HEAD") == "daily/2026-09-07"
    # ff 失敗時と同じ復元経路を通り、Today.md が失われないこと。
    assert (repo / "Today.md").exists()
    assert not (repo / "Cabinet" / "Diary" / "2026-09-07.md").exists()
    assert git(repo, "rev-parse", "daily/2026-09-07") == daily_head_before


def test_reports_recovery_steps_when_push_fails(tmp_path):
    repo = make_repo(tmp_path)
    git(repo, "remote", "add", "origin", str(tmp_path / "unreachable.git"))

    result = run_close(repo)

    assert result.returncode == 1
    assert "git pull --rebase origin main" in result.stderr
    # push 失敗では復元しない。main は進んだままでよい。
    assert not (repo / "Today.md").exists()
    assert (repo / "Cabinet" / "Diary" / "2026-09-07.md").is_file()
    assert git(repo, "rev-parse", "main") == git(repo, "rev-parse", "daily/2026-09-07")


def test_fails_when_diary_file_already_exists(tmp_path):
    repo = make_repo(tmp_path)
    (repo / "Cabinet" / "Diary" / "2026-09-07.md").write_text("既存の記録\n", encoding="utf-8")

    result = run_close(repo)

    assert result.returncode == 1
    assert (repo / "Today.md").exists()
    assert (repo / "Cabinet" / "Diary" / "2026-09-07.md").read_text(encoding="utf-8") == "既存の記録\n"


