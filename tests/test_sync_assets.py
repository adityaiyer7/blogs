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
    """Issue #27's shape: repo already has the file, Obsidian ships it flat.

    `existing_dir` is where the repo copy lives. Under `imgs` the incoming flat
    file is routed straight onto it, so there is no collision left to resolve —
    use another folder to exercise the collision policies themselves.
    """

    def _factory(
        incoming: str = "OBSIDIAN",
        existing: str = "REPO",
        stale: str | None = None,
        existing_dir: str = "imgs",
    ):
        src = tmp_path / "project" / "assets"
        dest = tmp_path / "post" / "assets"
        write(src / "foo.png", incoming)
        write(dest / existing_dir / "foo.png", existing)
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


# --- routing top-level images into imgs/ (issue #28) ------------------------


def test_flat_images_are_routed_into_imgs(tmp_path):
    """The v-jepa shape: Obsidian keeps images flat, the repo wants assets/imgs/."""
    src, dest = tmp_path / "src", tmp_path / "dest"
    for name in ("video_frames.png", "tublet.png", "tube.png"):
        write(src / name, name)
    dest.mkdir()

    proc = sync(src, dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/video_frames.png", "imgs/tublet.png", "imgs/tube.png"}
    assert "3 routed into imgs/" in proc.stdout


@pytest.mark.parametrize("name", ["a.PNG", "b.JPEG", "c.Svg", "d.webp", "e.tiff"])
def test_routing_matches_image_extensions_case_insensitively(tmp_path, name):
    src, dest = tmp_path / "src", tmp_path / "dest"
    write(src / name, "IMG")
    dest.mkdir()

    assert sync(src, dest, "ask").returncode == 0
    assert tree(dest) == {f"imgs/{name}"}


def test_non_image_files_stay_flat(tmp_path):
    """attention-mechanism keeps .tex/.aux/.dvi/.log sources flat in assets/."""
    src, dest = tmp_path / "src", tmp_path / "dest"
    for name in ("fig.tex", "fig.aux", "fig.dvi", "fig.log", "notes.pdf", "Makefile"):
        write(src / name, name)
    dest.mkdir()

    assert sync(src, dest, "ask").returncode == 0
    assert tree(dest) == {"fig.tex", "fig.aux", "fig.dvi", "fig.log", "notes.pdf", "Makefile"}


def test_routing_is_skipped_when_the_source_ships_both_copies(tmp_path):
    """Routing must not collapse two distinct incoming files onto one path."""
    src, dest = tmp_path / "src", tmp_path / "dest"
    write(src / "foo.png", "FLAT")
    write(src / "imgs" / "foo.png", "NESTED")
    dest.mkdir()

    proc = sync(src, dest, "keep-both")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"foo.png", "imgs/foo.png"}
    assert (dest / "foo.png").read_text() == "FLAT"
    assert (dest / "imgs" / "foo.png").read_text() == "NESTED"


def test_routing_onto_the_existing_copy_is_an_update_not_a_prompt(collision):
    """Issue #27's case stops being a collision once the flat file is routed."""
    src, dest = collision(incoming="OBSIDIAN", existing="REPO")

    proc = sync(src, dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/foo.png"}
    assert (dest / "imgs" / "foo.png").read_text() == "OBSIDIAN"
    # stdin is /dev/null, so a prompt would have fallen back with this warning.
    assert "Not running interactively" not in proc.stdout
    assert "collision" not in proc.stdout


def test_routing_removes_the_flat_copy_left_by_an_earlier_sync(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    write(src / "foo.png", "NEW")
    write(dest / "foo.png", "OLD")

    proc = sync(src, dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/foo.png"}
    assert (dest / "imgs" / "foo.png").read_text() == "NEW"


def test_routed_flat_image_resolves_its_embed_under_imgs(tmp_path):
    """The D2 regression guard: no manual move plus path fixup after a sync."""
    post = tmp_path / "post"
    src = tmp_path / "project" / "assets"
    write(src / "tube.png", "OBSIDIAN")
    qmd = write(post / "index.qmd", "Body\n\n![[tube.png|A tube]]\n")

    assert sync(src, post / "assets", "ask").returncode == 0

    assert rewrite(qmd, post) == "Body\n\n![A tube](assets/imgs/tube.png)\n"


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
    src, dest = collision(incoming="OBSIDIAN", existing="REPO", existing_dir="diagrams")

    proc = sync(src, dest, "keep-existing")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"diagrams/foo.png"}
    assert (dest / "diagrams" / "foo.png").read_text() == "REPO"


def test_keep_both_reproduces_the_old_additive_behavior(collision):
    src, dest = collision(incoming="OBSIDIAN", existing="REPO", existing_dir="diagrams")

    proc = sync(src, dest, "keep-both")

    assert proc.returncode == 0, proc.stderr
    # The incoming copy is still routed into imgs/ — keep-both is about how many
    # copies survive, not about where a new one lands.
    assert tree(dest) == {"imgs/foo.png", "diagrams/foo.png"}
    assert (dest / "imgs" / "foo.png").read_text() == "OBSIDIAN"
    assert (dest / "diagrams" / "foo.png").read_text() == "REPO"


def test_ask_without_a_tty_keeps_both_and_warns(collision):
    src, dest = collision(incoming="OBSIDIAN", existing="REPO", existing_dir="diagrams")

    proc = sync(src, dest, "ask")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/foo.png", "diagrams/foo.png"}
    assert "Not running interactively" in proc.stdout


def test_already_ambiguous_repo_tree_is_reported_not_guessed(tmp_path):
    """Routing lands on the canonical copy; the stray elsewhere is reported, not guessed."""
    src, dest = tmp_path / "src", tmp_path / "dest"
    write(src / "foo.png", "OBSIDIAN")
    write(dest / "imgs" / "foo.png", "ONE")
    write(dest / "diagrams" / "foo.png", "TWO")

    proc = sync(src, dest, "override")

    assert proc.returncode == 0, proc.stderr
    assert tree(dest) == {"imgs/foo.png", "diagrams/foo.png"}
    assert "also exists elsewhere" in proc.stdout
    # Updated in place; the stray is left exactly as it was rather than overwritten.
    assert (dest / "imgs" / "foo.png").read_text() == "OBSIDIAN"
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
    write(post / "assets" / "diagrams" / "foo.png", "REPO")
    qmd = write(post / "index.qmd", "Body\n\n![[foo.png]]\n")

    assert sync(src, post / "assets", "keep-both").returncode == 0

    # Unchanged wikilink is what check_post.sh reports as E1.
    assert "![[foo.png]]" in rewrite(qmd, post)
