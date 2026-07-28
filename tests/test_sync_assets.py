"""Tests for sync_assets_tree / rewrite_obsidian_embeds in tools/post_lib.sh.

The shell helpers are driven directly through bash. sync_assets_tree's `ask`
policy is interactive, so these tests cover the three non-interactive policies
plus the automatic paths (no collision, identical content); the prompt itself is
exercised by hand.
"""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


def _bash(script: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", "-c", f"source tools/post_lib.sh\n{script}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        stdin=subprocess.DEVNULL,
    )


def sync(src: Path, dest: Path, policy: str) -> subprocess.CompletedProcess:
    cmd = f"sync_assets_tree {shlex.quote(str(src))} {shlex.quote(str(dest))} {shlex.quote(policy)}"
    return _bash(cmd)


def rewrite(qmd: Path, post_root: Path) -> str:
    proc = _bash(
        f"rewrite_obsidian_embeds {shlex.quote(str(qmd))} "
        f"{shlex.quote(str(post_root / 'assets'))} {shlex.quote(str(post_root))}"
    )
    assert proc.returncode == 0, proc.stderr
    return qmd.read_text(encoding="utf-8")


def write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def tree(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


@pytest.fixture
def collision(tmp_path):
    """Issue #27's shape: repo has assets/imgs/foo.png, Obsidian ships it flat."""

    def _factory(incoming: str = "OBSIDIAN", existing: str = "REPO", stale: str | None = None):
        src = tmp_path / "project" / "assets"
        dest = tmp_path / "post" / "assets"
        write(src / "foo.png", incoming)
        write(dest / "imgs" / "foo.png", existing)
        if stale is not None:
            write(dest / "foo.png", stale)
        return src, dest

    return _factory


def test_copies_into_empty_tree(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    write(src / "imgs" / "a.png", "A")
    write(src / "diagrams" / "b.png", "B")
    dest.mkdir()

    proc = sync(src, dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/a.png", "diagrams/b.png"}


def test_same_relpath_is_an_update_not_a_collision(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    write(src / "imgs" / "a.png", "NEW")
    write(dest / "imgs" / "a.png", "OLD")

    proc = sync(src, dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert (dest / "imgs" / "a.png").read_text() == "NEW"
    assert "collision" not in proc.stdout


def test_identical_content_resolves_without_prompting(collision):
    src, dest = collision(incoming="SAME", existing="SAME")

    proc = sync(src, dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/foo.png"}
    assert "identical" in proc.stdout
    # `ask` with no tty warns only for collisions it actually has to punt on.
    assert "Not running interactively" not in proc.stdout


def test_identical_content_removes_a_stale_duplicate(collision):
    src, dest = collision(incoming="SAME", existing="SAME", stale="SAME")

    proc = sync(src, dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/foo.png"}
    assert "Removed the stale duplicate" in proc.stdout


def test_override_writes_into_the_existing_repo_path(collision):
    src, dest = collision(incoming="OBSIDIAN", existing="REPO", stale="REPO")

    proc = sync(src, dest, "override")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/foo.png"}
    assert (dest / "imgs" / "foo.png").read_text() == "OBSIDIAN"


def test_keep_existing_discards_the_incoming_copy(collision):
    src, dest = collision(incoming="OBSIDIAN", existing="REPO", stale="REPO")

    proc = sync(src, dest, "keep-existing")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/foo.png"}
    assert (dest / "imgs" / "foo.png").read_text() == "REPO"


def test_keep_both_reproduces_the_old_additive_behavior(collision):
    src, dest = collision(incoming="OBSIDIAN", existing="REPO")

    proc = sync(src, dest, "keep-both")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"foo.png", "imgs/foo.png"}
    assert (dest / "foo.png").read_text() == "OBSIDIAN"
    assert (dest / "imgs" / "foo.png").read_text() == "REPO"


def test_ask_without_a_tty_keeps_both_and_warns(collision):
    src, dest = collision(incoming="OBSIDIAN", existing="REPO")

    proc = sync(src, dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"foo.png", "imgs/foo.png"}
    assert "Not running interactively" in proc.stdout


def test_already_ambiguous_repo_tree_is_reported_not_guessed(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    write(src / "foo.png", "OBSIDIAN")
    write(dest / "imgs" / "foo.png", "ONE")
    write(dest / "diagrams" / "foo.png", "TWO")

    proc = sync(src, dest, "override")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"foo.png", "imgs/foo.png", "diagrams/foo.png"}
    assert "several paths" in proc.stdout
    assert (dest / "imgs" / "foo.png").read_text() == "ONE"
    assert (dest / "diagrams" / "foo.png").read_text() == "TWO"


def test_missing_source_dir_is_a_no_op(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()

    proc = sync(tmp_path / "nope", dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == set()


@pytest.mark.parametrize("policy", ["override", "keep-existing"])
def test_resolved_collision_lets_the_embed_rewrite_succeed(tmp_path, policy):
    """The E1 regression guard: a resolved collision must leave one path per basename."""
    post = tmp_path / "post"
    src = tmp_path / "project" / "assets"
    write(src / "foo.png", "OBSIDIAN")
    write(post / "assets" / "imgs" / "foo.png", "REPO")
    qmd = write(post / "index.qmd", "Body\n\n![[foo.png]]\n")

    assert sync(src, post / "assets", policy).returncode == 0

    assert rewrite(qmd, post) == "Body\n\n![](assets/imgs/foo.png)\n"


def test_keep_both_leaves_the_embed_ambiguous(tmp_path):
    post = tmp_path / "post"
    src = tmp_path / "project" / "assets"
    write(src / "foo.png", "OBSIDIAN")
    write(post / "assets" / "imgs" / "foo.png", "REPO")
    qmd = write(post / "index.qmd", "Body\n\n![[foo.png]]\n")

    assert sync(src, post / "assets", "keep-both").returncode == 0

    # Unchanged wikilink is what check_post.sh reports as E1.
    assert "![[foo.png]]" in rewrite(qmd, post)
