"""core/files.py: what the TUI reads or lists from a repository, and the
paths a person gives it -- checked, bounded, and never a crash."""

import os
import subprocess

import pytest

from adrpy_tui.core import files


def _link_folder(link, target):
    """A folder link: a junction on Windows (no admin needed), else a symlink."""
    if os.name == "nt":
        subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)], check=True, capture_output=True)
    else:
        os.symlink(target, link, target_is_directory=True)


def test_a_folder_that_cannot_be_looked_at_is_not_inside(tmp_path, monkeypatch):
    """Every OSError from lstat read as "not there", so a folder denied to the
    person passed the check, and the listing that followed raised
    PermissionError and ended the app."""
    denied = tmp_path / "doc" / "decision-log"
    denied.mkdir(parents=True)
    real = os.lstat

    def lstat(path, *args, **kwargs):
        if os.path.normpath(str(path)) == os.path.normpath(str(denied)):
            raise PermissionError(13, "Access is denied", str(path))
        return real(path, *args, **kwargs)

    monkeypatch.setattr(files.os, "lstat", lstat)
    assert files.inside_repository(tmp_path, denied / "x.md") is False
    assert files.inside_repository(tmp_path, tmp_path / "doc" / "not-yet" / "x.md") is True  # missing: nothing to follow


def test_asking_about_a_path_that_cannot_be_looked_at_is_a_no(tmp_path, monkeypatch):
    """Path.is_dir raises PermissionError on a denied folder (Python 3.12):
    typed in Change repository, it ended the app."""
    class Denied(type(tmp_path)):
        def is_dir(self, **_):
            raise PermissionError(13, "Access is denied")

        is_file = is_dir

    monkeypatch.setattr(files, "Path", Denied)
    assert files.is_dir(tmp_path) is False
    assert files.is_file(tmp_path / "x.md") is False


def test_a_listing_never_follows_a_folder_link(tmp_path):
    """rglob followed a junction below the log folder: it listed files outside
    the repository, and a junction to a parent never ended."""
    log, outside = tmp_path / "log", tmp_path / "outside"
    (log / "2026").mkdir(parents=True)
    outside.mkdir()
    (log / "2026" / "inside.md").write_text("x", encoding="utf-8")
    (outside / "outside.md").write_text("x", encoding="utf-8")
    _link_folder(log / "out", outside)
    _link_folder(log / "2026" / "loop", log)
    assert [path.name for path in files.markdown_files(log)] == ["inside.md"]


def test_a_listing_of_a_folder_that_cannot_be_read_is_empty(tmp_path):
    assert files.markdown_files(tmp_path / "missing") == []


@pytest.mark.parametrize("lines, width", [(3000, 10), (10, 60_000), (3000, 400)])
def test_read_start_reads_only_what_is_shown_and_counts_the_whole_file(tmp_path, lines, width):
    """The preview read the whole file, then cut it: a 500 MB file would take
    a minute and gigabytes. Only the start is kept; the totals are the file's
    -- they were the cut content's when both limits were passed."""
    page = tmp_path / "big.md"
    text = "\n".join("x" * width for _ in range(lines))
    page.write_bytes(text.encode("utf-8"))  # as written, no line-ending translation
    start, total_lines, total_characters = files.read_start(page, 500, 100_000)
    assert (total_lines, total_characters) == (lines, len(text))
    assert len(start) <= 100_000 and len(start.splitlines()) <= 500
    assert text.startswith(start)
